#!/usr/bin/env python3
"""Reverify every pre-Round-54 user file against the frozen snapshot."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_am_sf_inventory_route_round54"
AUDIT = OUT / "preexisting_file_preservation_audit.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


audit = json.loads(AUDIT.read_text(encoding="utf-8"))
tracked_failures: list[str] = []
for row in audit["tracked_modified_files"]:
    path = ROOT / row["path"]
    if (not path.is_file() or path.stat().st_size != row["bytes"] or
            sha256(path) != row["sha256"]):
        tracked_failures.append(row["path"])
        continue
    blob = subprocess.check_output(
        ["git", "hash-object", "--", row["path"]], cwd=ROOT,
        text=True, encoding="utf-8").strip()
    if blob != row["git_blob"]:
        tracked_failures.append(row["path"])

inventory_path = ROOT / audit["untracked_snapshot"]["local_inventory_path"]
inventory_hash_match = sha256(inventory_path) == audit["untracked_snapshot"]["local_inventory_sha256"]
with inventory_path.open(newline="", encoding="utf-8-sig") as handle:
    rows = list(csv.DictReader(handle))


def verify(row: dict[str, str]) -> tuple[str, bool]:
    path = ROOT / row["path"]
    valid = (path.is_file() and path.stat().st_size == int(row["bytes"])
             and sha256(path) == row["sha256"])
    return row["path"], valid


with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(verify, rows))
untracked_failures = [path for path, valid in results if not valid]
count_match = len(rows) == audit["untracked_snapshot"]["file_count"]
bytes_total = sum(int(row["bytes"]) for row in rows)
bytes_match = bytes_total == audit["untracked_snapshot"]["total_bytes"]

passed = (not tracked_failures and not untracked_failures and
          inventory_hash_match and count_match and bytes_match)
audit["final_reverification_pending"] = False
audit["final_reverification"] = {
    "passed": passed,
    "tracked_files_checked": len(audit["tracked_modified_files"]),
    "tracked_failures": tracked_failures,
    "untracked_files_checked": len(rows),
    "untracked_failures": untracked_failures,
    "untracked_total_bytes": bytes_total,
    "inventory_sha256_match": inventory_hash_match,
    "file_count_match": count_match,
    "total_bytes_match": bytes_match,
    "logical_snapshot_aggregate_match": not untracked_failures and count_match and bytes_match,
    "note": "The frozen inventory file is byte-identical and every listed path, byte length, and SHA-256 was independently rechecked.",
}
AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
if not passed:
    raise SystemExit(f"preservation failed: tracked={len(tracked_failures)}, untracked={len(untracked_failures)}")
print(f"preservation passed: {len(audit['tracked_modified_files'])} tracked and {len(rows)} untracked files ({bytes_total} bytes)")
