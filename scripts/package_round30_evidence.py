#!/usr/bin/env python3
"""Losslessly compress and inventory the isolated Round 30 evidence tree."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import run_round30_experiments as runner


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_c0_mechanism_transfer_c5_round30"
MANIFEST = OUT / "evidence_package_manifest.csv"


def main() -> int:
    compressed = runner.compress_large_files()
    rows = []
    for path in sorted(OUT.rglob("*")):
        if not path.is_file() or path == MANIFEST:
            continue
        rows.append({
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": runner.sha256(path),
            "compressed": path.suffix.lower() == ".gz",
            "role": (
                "official_run_artifact" if "runs" in path.parts
                else "derived_or_protocol_evidence"),
        })
    with MANIFEST.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    largest = max(rows, key=lambda row: int(row["bytes"]))
    total_bytes = sum(int(row["bytes"]) for row in rows)
    summary_path = OUT / "final_audit_summary.json"
    summary = (
        json.loads(summary_path.read_text(encoding="utf-8"))
        if summary_path.is_file() else {})
    summary.update({
        "evidence_package_file_count_excluding_self": len(rows),
        "evidence_package_bytes_excluding_self": total_bytes,
        "largest_artifact_path": largest["path"],
        "largest_artifact_bytes": largest["bytes"],
        "losslessly_compressed_files": len(compressed),
        "compression_restoration_hashes_verified": all(
            row["original_sha256"] == row["restoration_sha256"]
            and row["original_bytes"] == row["restoration_bytes"]
            for row in compressed),
        "evidence_package_manifest_path":
            MANIFEST.relative_to(ROOT).as_posix(),
    })
    runner.json_write(summary_path, summary)
    print(json.dumps({
        "files": len(rows),
        "bytes": total_bytes,
        "largest": largest,
        "compressed_files": len(compressed),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
