#!/usr/bin/env python3
"""Verify the pre-Round-56 untracked snapshot and tracked user modifications."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "build" / "round56_preexisting_untracked_snapshot.csv"
OUTPUT = ROOT / "results" / "gf_paper_benchmark_time_horizon_round56" / "preexisting_files_final_verification.json"
TRACKED_USER_FILES = {
    "results/gf_compact_bc_round/handling_convention_test/handling_convention.json": "9a5cd06f8a4163cfcbb57147a0b21c0a5e4aec91973ab93faa921baa0553f35b",
    "results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv": "4af39fe81263cd8c15ca457f4d4f6473a959630b6ab68a9280bc0a0e0a6b8acb",
    "results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json": "b11e84e2442c0c7b5ac5aa638b44945de28426fe31753083bff13ad401644202",
}


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
    tracked_rows = []
    for relative, expected_hash in TRACKED_USER_FILES.items():
        path = ROOT / relative
        actual_hash = sha256(path) if path.is_file() else None
        tracked_rows.append({
            "path": relative, "expected_sha256": expected_hash, "actual_sha256": actual_hash,
            "preserved": actual_hash == expected_hash,
        })
    result = {
        "schema": "round56-preexisting-files-final-verification-v1",
        "snapshot_path": SNAPSHOT.relative_to(ROOT).as_posix(), "snapshot_sha256": sha256(SNAPSHOT),
        "verified_untracked_file_count": checked, "verified_untracked_bytes": checked_bytes,
        "missing_untracked_paths": missing, "size_mismatch_untracked_paths": size_mismatch,
        "sha256_mismatch_untracked_paths": hash_mismatch, "tracked_user_modifications": tracked_rows,
        "all_preserved": not missing and not size_mismatch and not hash_mismatch and all(row["preserved"] for row in tracked_rows),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["all_preserved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
