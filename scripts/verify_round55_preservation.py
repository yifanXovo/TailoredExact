#!/usr/bin/env python3
"""Verify every path in the pre-Round-55 unrelated-untracked snapshot."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "build" / "round55_preexisting_untracked_snapshot.csv"
OUTPUT = ROOT / "results" / "gf_k1_am_sf_station_state_chain_round55" / "preexisting_untracked_final_verification.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    missing: list[str] = []
    size_mismatch: list[str] = []
    hash_mismatch: list[str] = []
    checked = 0
    checked_bytes = 0
    with SNAPSHOT.open(newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            relative = row["path"]
            path = ROOT / relative
            if not path.is_file():
                missing.append(relative)
                continue
            expected_size = int(row["bytes"])
            actual_size = path.stat().st_size
            if actual_size != expected_size:
                size_mismatch.append(relative)
                continue
            if sha256(path) != row["sha256"]:
                hash_mismatch.append(relative)
                continue
            checked += 1
            checked_bytes += actual_size
    result = {
        "schema": "round55-preexisting-untracked-final-verification-v1",
        "snapshot_path": SNAPSHOT.relative_to(ROOT).as_posix(),
        "snapshot_sha256": sha256(SNAPSHOT),
        "verified_file_count": checked,
        "verified_bytes": checked_bytes,
        "missing_paths": missing,
        "size_mismatch_paths": size_mismatch,
        "sha256_mismatch_paths": hash_mismatch,
        "all_preserved": not missing and not size_mismatch and not hash_mismatch,
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_preserved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
