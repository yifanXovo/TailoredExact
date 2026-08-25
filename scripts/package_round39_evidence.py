#!/usr/bin/env python3
"""Losslessly package, scan, inventory, and finalize Round 39 evidence."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
from typing import Any, BinaryIO

import round39_common as common


MANIFEST = common.OUT / "evidence_package_manifest.csv"
COMPRESSION = common.OUT / "compression_manifest.csv"
MINIMUM_COMPRESSION_BYTES = 1024 * 1024
COMPRESSIBLE = {".lp", ".csv", ".log"}
NEVER_COMPRESS = {
    "artifact_manifest.csv", "completion_marker.json", "command.json",
    "result.json", "run_state.json",
}
SENSITIVE_MARKERS = (
    b"GRB_LICENSE_FILE", b"gurobi.lic", b"LicenseID", b"WLSAccessID",
    b"WLSSecret",
)


def hash_stream(stream: BinaryIO) -> tuple[int, str]:
    digest, size = hashlib.sha256(), 0
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(block)
        size += len(block)
    return size, digest.hexdigest()


def candidates() -> list[Path]:
    roots = [common.OUT]
    output = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            suffix = path.suffix.lower()
            if (path.is_file() and path.name not in NEVER_COMPRESS
                    and suffix in COMPRESSIBLE
                    and (suffix in {".lp", ".log"} or
                         path.stat().st_size >= MINIMUM_COMPRESSION_BYTES)
                    and not path.name.endswith(".gz")
                    and not Path(str(path) + ".gz").is_file()):
                output.append(path)
    return sorted(output, key=lambda path: path.as_posix())


def compress(path: Path) -> dict[str, Any]:
    original_bytes, original_sha = path.stat().st_size, common.sha256(path)
    target = Path(str(path) + ".gz")
    temporary = Path(str(target) + ".tmp")
    with path.open("rb") as source, temporary.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as out:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                out.write(block)
        raw.flush()
        os.fsync(raw.fileno())
    with gzip.open(temporary, "rb") as restored:
        restored_bytes, restored_sha = hash_stream(restored)
    if restored_bytes != original_bytes or restored_sha != original_sha:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"compression restoration mismatch: {path}")
    os.replace(temporary, target)
    # LP and log files are globally ignored by Git. Keep their originals for
    # checksum-resumable local runs while publishing only verified gzip copies.
    # Large CSVs are tracked by default, so remove them after verification to
    # avoid committing both representations.
    if path.suffix.lower() == ".csv":
        path.unlink()
    return {
        "original_path": common.relative(path),
        "compressed_path": common.relative(target),
        "original_bytes": original_bytes,
        "compressed_bytes": target.stat().st_size,
        "original_sha256": original_sha,
        "compressed_sha256": common.sha256(target),
        "restored_bytes": restored_bytes,
        "restored_sha256": restored_sha,
        "restoration_verified": True, "lossless": True,
    }


def scan_file(path: Path) -> bool:
    stream: BinaryIO = gzip.open(path, "rb") if path.suffix == ".gz" \
        else path.open("rb")
    tail = b""
    width = max(len(marker) for marker in SENSITIVE_MARKERS)
    try:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            data = (tail + block).lower()
            if any(marker.lower() in data for marker in SENSITIVE_MARKERS):
                return False
            tail = data[-width:]
    finally:
        stream.close()
    return True


def package_files() -> list[Path]:
    return sorted((path for path in common.OUT.rglob("*")
                   if path.is_file() and path != MANIFEST
                   and not (path.suffix.lower() in {".lp", ".log"}
                            and Path(str(path) + ".gz").is_file())),
                  key=lambda path: path.as_posix())


def main() -> int:
    required = (
        common.OUT / "final_decision.json",
        common.OUT / "final_report.md",
        common.OUT / "post_build_and_tests.json",
        common.OUT / "default_c6_equivalence_audit.json",
    )
    if any(not path.is_file() for path in required):
        raise RuntimeError("analysis, tests, and equivalence must finish first")
    common.write_text(common.OUT / ".gitattributes", "* -text\n** -text\n")
    previous = common.csv_rows(COMPRESSION) if COMPRESSION.is_file() else []
    updated = [compress(path) for path in candidates()]
    compressed_by_path = {
        row["original_path"]: row for row in [*previous, *updated]
    }
    compressed = [compressed_by_path[key]
                  for key in sorted(compressed_by_path)]
    if not compressed:
        compressed = [{
            "original_path": "none", "compressed_path": "none",
            "original_bytes": 0, "compressed_bytes": 0,
            "original_sha256": "none", "compressed_sha256": "none",
            "restored_bytes": 0, "restored_sha256": "none",
            "restoration_verified": True, "lossless": True,
        }]
    common.write_csv(COMPRESSION, compressed)
    summary_path = common.OUT / "evidence_package_summary.json"
    base_files = [path for path in package_files() if path != summary_path]
    summary = {
        "schema": "round39-evidence-package-v1", "round_id": 39,
        "file_count_excluding_self_manifest": len(base_files) + 1,
        "total_bytes_excluding_self_manifest": 0,
        "losslessly_compressed_files": sum(
            row["original_path"] != "none" for row in compressed),
        "compression_restoration_hashes_verified": all(
            row["restoration_verified"] for row in compressed),
        "license_marker_scan_files": len(base_files) + 1,
        "license_marker_scan_hits": 0,
        "largest_artifact_path": common.relative(max(
            base_files, key=lambda path: path.stat().st_size)),
        "largest_artifact_bytes": max(
            path.stat().st_size for path in base_files),
    }
    base_bytes = sum(path.stat().st_size for path in base_files)
    for _ in range(4):
        common.write_json(summary_path, summary)
        total = base_bytes + summary_path.stat().st_size
        if summary["total_bytes_excluding_self_manifest"] == total:
            break
        summary["total_bytes_excluding_self_manifest"] = total
    common.write_json(summary_path, summary)
    files = package_files()
    unsafe = [common.relative(path) for path in files if not scan_file(path)]
    if unsafe:
        raise RuntimeError(f"sensitive marker found: {unsafe[:5]}")
    inventory = [{
        "relative_path": common.relative(path), "bytes": path.stat().st_size,
        "sha256": common.sha256(path),
        "publication_scope": "committed_round39_exact_evidence",
    } for path in files]
    common.write_csv(MANIFEST, inventory)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
