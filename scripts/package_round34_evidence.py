#!/usr/bin/env python3
"""Losslessly compress, scan, inventory, and verify Round 34 evidence."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
from typing import Any, BinaryIO

import round34_common as common


OUT = common.OUT
MANIFEST = OUT / "evidence_package_manifest.csv"
COMPRESSION = OUT / "compression_manifest.csv"
MINIMUM_COMPRESSION_BYTES = 1024 * 1024
COMPRESSIBLE = {".lp", ".csv", ".log"}
NEVER_COMPRESS = {
    "artifact_manifest.csv", "completion_marker.json", "command.json",
    "result.json", "run_state.json",
}
SENSITIVE_MARKERS = (
    b"GRB_LICENSE_FILE", b"gurobi.lic", b"LicenseID",
    b"WLSAccessID", b"WLSSecret",
)


def hash_stream(stream: BinaryIO) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(block)
        size += len(block)
    return size, digest.hexdigest()


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hash_stream(stream)[1]


def write_text(path: Path, value: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]],
              fields: list[str]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def candidates() -> list[Path]:
    roots = (
        common.RUNS, common.STAGE0_RUNS, common.DEVELOPMENT_RUNS,
        common.INVALIDATED,
    )
    output = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if (path.is_file() and path.name not in NEVER_COMPRESS
                    and path.suffix.lower() in COMPRESSIBLE
                    and path.stat().st_size >= MINIMUM_COMPRESSION_BYTES
                    and not path.name.endswith(".gz")):
                output.append(path)
    return sorted(output, key=lambda path: path.as_posix())


def compress(path: Path) -> dict[str, Any]:
    original_bytes = path.stat().st_size
    original_sha = sha256(path)
    target = Path(str(path) + ".gz")
    temporary = Path(str(target) + ".tmp")
    with path.open("rb") as source, temporary.open("wb") as raw:
        with gzip.GzipFile(
                filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                zipped.write(block)
        raw.flush()
        os.fsync(raw.fileno())
    with gzip.open(temporary, "rb") as restored:
        restored_bytes, restored_sha = hash_stream(restored)
    if restored_bytes != original_bytes or restored_sha != original_sha:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"compression restoration mismatch: {path}")
    os.replace(temporary, target)
    path.unlink()
    return {
        "original_path": common.relative(path),
        "compressed_path": common.relative(target),
        "original_bytes": original_bytes,
        "compressed_bytes": target.stat().st_size,
        "original_sha256": original_sha,
        "compressed_sha256": sha256(target),
        "restored_bytes": restored_bytes,
        "restored_sha256": restored_sha,
        "restoration_verified": True,
        "lossless": True,
    }


def scan_file(path: Path) -> bool:
    stream: BinaryIO = gzip.open(path, "rb") \
        if path.suffix.lower() == ".gz" else path.open("rb")
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
    excluded = {MANIFEST.resolve()}
    return sorted(
        (path for path in OUT.rglob("*")
         if path.is_file() and path.resolve() not in excluded),
        key=lambda path: path.as_posix())


def main() -> int:
    audit_path = OUT / "final_audit_summary.json"
    report_path = OUT / "final_report.md"
    if not audit_path.is_file() or not report_path.is_file():
        raise RuntimeError("Round 34 final analysis must run before packaging")
    if len(list(common.RUNS.glob("*/completion_marker.json"))) != 82:
        raise RuntimeError("all 82 official completion markers are required")
    write_text(OUT / ".gitattributes", "* -text\n** -text\n")
    compressed_rows = [compress(path) for path in candidates()]
    write_csv(COMPRESSION, compressed_rows, [
        "original_path", "compressed_path", "original_bytes",
        "compressed_bytes", "original_sha256", "compressed_sha256",
        "restored_bytes", "restored_sha256", "restoration_verified",
        "lossless",
    ])
    files = package_files()
    unsafe = [common.relative(path) for path in files if not scan_file(path)]
    if unsafe:
        raise RuntimeError(
            f"sensitive license marker found in {len(unsafe)} evidence files")
    largest = max(files, key=lambda path: path.stat().st_size)
    audit = common.load_json(audit_path)
    audit.update({
        "losslessly_compressed_files": len(compressed_rows),
        "compression_restoration_hashes_verified": all(
            row["restoration_verified"] for row in compressed_rows),
        "license_marker_scan_files": len(files),
        "license_marker_scan_hits": 0,
        "largest_artifact_path": common.relative(largest),
        "largest_artifact_bytes": largest.stat().st_size,
        "largest_artifact_sha256": sha256(largest),
        "post_package_completion_markers_are_provenance_only": True,
        "post_package_integrity_authority":
            "evidence_package_manifest_and_compression_restoration_hashes",
    })
    base_report = report_path.read_text(encoding="utf-8").split(
        "\n## Evidence package\n", 1)[0].rstrip() + "\n"
    for _ in range(8):
        files = package_files()
        total_bytes = sum(path.stat().st_size for path in files)
        audit.update({
            "evidence_package_file_count_excluding_self": len(files),
            "evidence_package_bytes_excluding_self": total_bytes,
        })
        write_json(audit_path, audit)
        report = base_report + f"""

## Evidence package

The package contains {len(files)} files excluding its self-manifest and totals
{total_bytes} bytes.  {len(compressed_rows)} large raw artifacts were compressed
losslessly and independently restored to the original byte count and SHA-256.
The largest retained artifact is `{common.relative(largest)}`
({largest.stat().st_size} bytes).  A package-wide sensitive-license-marker scan
found zero hits.  After compression, the package manifest and restoration
hashes supersede per-run pre-compression artifact manifests for integrity.
"""
        write_text(report_path, report)
        updated = package_files()
        if (len(updated) == len(files)
                and sum(path.stat().st_size for path in updated) == total_bytes):
            break
    else:
        raise RuntimeError("package byte count did not stabilize")
    files = package_files()
    rows = [{
        "path": common.relative(path), "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "compressed": path.suffix.lower() == ".gz",
        "role": "official_or_preflight_raw_evidence"
            if any(part in {"runs", "stage0_runs", "development_runs",
                            "invalidated_rows"} for part in path.parts)
            else "derived_or_protocol_evidence",
    } for path in files]
    write_csv(MANIFEST, rows, [
        "path", "bytes", "sha256", "compressed", "role"])
    for row in rows:
        path = common.ROOT / row["path"]
        if (not path.is_file() or path.stat().st_size != int(row["bytes"])
                or sha256(path) != row["sha256"]):
            raise RuntimeError(f"package manifest verification failed: {path}")
    print(json.dumps({
        "files_excluding_manifest": len(rows),
        "bytes_excluding_manifest": sum(int(row["bytes"]) for row in rows),
        "compressed_files": len(compressed_rows),
        "license_marker_hits": 0,
        "largest_artifact": common.relative(largest),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
