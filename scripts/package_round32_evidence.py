#!/usr/bin/env python3
"""Losslessly compress, restore-verify, and inventory Round 32 evidence."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_long_run_validation_round32"
MANIFEST = OUT / "evidence_package_manifest.csv"
COMPRESSION_MANIFEST = OUT / "compression_manifest.csv"
THRESHOLD = 512 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_csv(path: Path, rows: list[dict[str, Any]],
              fields: list[str]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def verify_compressed_record(record: dict[str, Any]) -> None:
    target = ROOT / record["compressed_path"]
    if not target.is_file():
        raise RuntimeError(f"compressed artifact is missing: {target}")
    restored = hashlib.sha256()
    restored_bytes = 0
    with gzip.open(target, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            restored.update(block)
            restored_bytes += len(block)
    if (
        sha256(target) != record["compressed_sha256"]
        or restored.hexdigest() != record["original_sha256"]
        or restored.hexdigest() != record["restoration_sha256"]
        or restored_bytes != int(record["original_bytes"])
        or restored_bytes != int(record["restoration_bytes"])
    ):
        raise RuntimeError(
            f"existing compression record failed verification: {target}")


def compression_roots() -> tuple[Path, ...]:
    return (
        OUT / "runs",
        OUT / "stage0_runs",
        OUT / "invalidated_rows",
    )


def compress() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if COMPRESSION_MANIFEST.is_file():
        with COMPRESSION_MANIFEST.open(
                newline="", encoding="utf-8") as stream:
            records = list(csv.DictReader(stream))
        for record in records:
            verify_compressed_record(record)
    known_originals = {record["original_path"] for record in records}
    paths = sorted({
        path for root in compression_roots() if root.is_dir()
        for path in root.rglob("*")
    })
    for path in paths:
        if (
            not path.is_file()
            or path.stat().st_size < THRESHOLD
            or path.suffix.lower() not in {".csv", ".log", ".lp"}
        ):
            continue
        if relative(path) in known_originals:
            raise RuntimeError(
                f"both raw and recorded compressed artifacts exist: {path}")
        target = Path(str(path) + ".gz")
        if target.exists():
            raise RuntimeError(f"compression target exists: {target}")
        original_hash = sha256(path)
        original_bytes = path.stat().st_size
        with path.open("rb") as source, target.open("wb") as raw:
            with gzip.GzipFile(
                    filename="", mode="wb", fileobj=raw,
                    compresslevel=9, mtime=0) as sink:
                for block in iter(
                        lambda: source.read(1024 * 1024), b""):
                    sink.write(block)
            raw.flush()
            os.fsync(raw.fileno())
        restored = hashlib.sha256()
        restored_bytes = 0
        with gzip.open(target, "rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                restored.update(block)
                restored_bytes += len(block)
        if (
            restored.hexdigest() != original_hash
            or restored_bytes != original_bytes
        ):
            target.unlink(missing_ok=True)
            raise RuntimeError(f"compression verification failed: {path}")
        path.unlink()
        records.append({
            "original_path": relative(path),
            "compressed_path": relative(target),
            "original_bytes": original_bytes,
            "compressed_bytes": target.stat().st_size,
            "original_sha256": original_hash,
            "compressed_sha256": sha256(target),
            "restoration_sha256": restored.hexdigest(),
            "restoration_bytes": restored_bytes,
            "compression": "gzip_level9_mtime0_filename_omitted",
        })
    records.sort(key=lambda record: record["original_path"])
    write_csv(COMPRESSION_MANIFEST, records, [
        "original_path", "compressed_path", "original_bytes",
        "compressed_bytes", "original_sha256", "compressed_sha256",
        "restoration_sha256", "restoration_bytes", "compression",
    ])
    return records


def retained_records() -> list[dict[str, Any]]:
    if not COMPRESSION_MANIFEST.is_file():
        raise RuntimeError("compression manifest is missing")
    with COMPRESSION_MANIFEST.open(
            newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    for record in records:
        verify_compressed_record(record)
    remaining = [
        path for root in compression_roots() if root.is_dir()
        for path in root.rglob("*")
        if path.is_file() and path.stat().st_size >= THRESHOLD
        and path.suffix.lower() in {".csv", ".log", ".lp"}
    ]
    if remaining:
        raise RuntimeError(
            f"inventory-only pass found {len(remaining)} uncompressed "
            "large artifacts")
    return records


def collect_rows() -> list[dict[str, Any]]:
    rows = []
    for path in sorted(OUT.rglob("*")):
        if not path.is_file() or path == MANIFEST:
            continue
        rows.append({
            "path": relative(path),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "compressed": path.suffix.lower() == ".gz",
            "role": (
                "official_run_artifact"
                if (OUT / "runs") in path.parents
                else "stage0_artifact"
                if (OUT / "stage0_runs") in path.parents
                else "invalidated_row_artifact"
                if (OUT / "invalidated_rows") in path.parents
                else "derived_or_protocol_evidence"),
        })
    return rows


def update_report(summary: dict[str, Any]) -> None:
    report_path = OUT / "final_report.md"
    report = report_path.read_text(encoding="utf-8")
    marker = "\n## Evidence package\n"
    report = report.split(marker)[0]
    report += (
        marker
        + "\nThe package contains "
        + str(summary["evidence_package_file_count_excluding_self"])
        + " files excluding its self-manifest, totaling "
        + str(summary["evidence_package_bytes_excluding_self"])
        + " bytes. The largest retained artifact is `"
        + str(summary["largest_artifact_path"])
        + "` ("
        + str(summary["largest_artifact_bytes"])
        + " bytes). "
        + str(summary["losslessly_compressed_files"])
        + " large artifacts were compressed losslessly and every restoration "
          "hash was verified.\n"
    )
    temporary = report_path.with_suffix(".md.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(report)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, report_path)


def update_summary(compressed: list[dict[str, Any]]) -> tuple[
        dict[str, Any], list[dict[str, Any]]]:
    summary_path = OUT / "final_audit_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary.update({
        "losslessly_compressed_files": len(compressed),
        "compression_restoration_hashes_verified": True,
        "evidence_package_manifest_path": relative(MANIFEST),
    })
    for _ in range(30):
        write_json(summary_path, summary)
        if (OUT / "final_report.md").is_file() and all(
                key in summary for key in (
                    "evidence_package_file_count_excluding_self",
                    "evidence_package_bytes_excluding_self",
                    "largest_artifact_path",
                    "largest_artifact_bytes")):
            update_report(summary)
        rows = collect_rows()
        largest = max(rows, key=lambda row: int(row["bytes"]))
        fields = {
            "evidence_package_file_count_excluding_self": len(rows),
            "evidence_package_bytes_excluding_self": sum(
                int(row["bytes"]) for row in rows),
            "largest_artifact_path": largest["path"],
            "largest_artifact_bytes": largest["bytes"],
        }
        if all(summary.get(key) == value for key, value in fields.items()):
            return summary, rows
        summary.update(fields)
    raise RuntimeError("Round 32 package summary did not converge")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()
    compressed = retained_records() if args.inventory_only else compress()
    summary, rows = update_summary(compressed)
    write_csv(
        MANIFEST, rows,
        ["path", "bytes", "sha256", "compressed", "role"])
    largest = max(rows, key=lambda row: int(row["bytes"]))
    print(json.dumps({
        "files": len(rows),
        "bytes": sum(int(row["bytes"]) for row in rows),
        "largest": largest,
        "compressed_files": len(compressed),
        "restoration_hashes_verified": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
