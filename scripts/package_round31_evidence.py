#!/usr/bin/env python3
"""Losslessly compress, verify, and inventory Round 31 evidence."""

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
OUT = ROOT / "results/gf_nonblocking_gurobi_c6_round31"
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


def compress() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if COMPRESSION_MANIFEST.is_file():
        with COMPRESSION_MANIFEST.open(
                newline="", encoding="utf-8") as stream:
            records = list(csv.DictReader(stream))
        for record in records:
            verify_compressed_record(record)
    known_originals = {record["original_path"] for record in records}
    roots = (OUT / "runs", OUT / "development", OUT / "stage0_runs")
    paths = sorted({
        path for root in roots if root.is_dir() for path in root.rglob("*")
    })
    for path in paths:
        if (not path.is_file() or path.stat().st_size < THRESHOLD or
                path.suffix.lower() not in {".csv", ".log", ".lp"}):
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
        restored = hashlib.sha256()
        restored_bytes = 0
        with gzip.open(target, "rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                restored.update(block)
                restored_bytes += len(block)
        if (restored.hexdigest() != original_hash or
                restored_bytes != original_bytes):
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
    write_csv(
        COMPRESSION_MANIFEST, records,
        [
            "original_path", "compressed_path", "original_bytes",
            "compressed_bytes", "original_sha256", "compressed_sha256",
            "restoration_sha256", "restoration_bytes", "compression",
        ])
    return records


def retained_compression_records() -> list[dict[str, Any]]:
    if not COMPRESSION_MANIFEST.is_file():
        raise RuntimeError("compression manifest is missing")
    with COMPRESSION_MANIFEST.open(
            newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    for record in records:
        target = ROOT / record["compressed_path"]
        if not target.is_file():
            raise RuntimeError(f"compressed artifact is missing: {target}")
        if (
            record["original_sha256"] != record["restoration_sha256"]
            or int(record["original_bytes"]) !=
                int(record["restoration_bytes"])
            or sha256(target) != record["compressed_sha256"]
        ):
            raise RuntimeError(
                f"retained compression record is inconsistent: {target}")
    roots = (OUT / "runs", OUT / "development", OUT / "stage0_runs")
    remaining = [
        path for root in roots if root.is_dir() for path in root.rglob("*")
        if path.is_file() and path.stat().st_size >= THRESHOLD and
        path.suffix.lower() in {".csv", ".log", ".lp"}
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
                "official_run_artifact" if "runs" in path.parts
                else "development_artifact"
                if "development" in path.parts
                else "stage0_artifact"
                if "stage0_runs" in path.parts
                else "derived_or_protocol_evidence"),
        })
    return rows


def update_summary(compressed: list[dict[str, Any]]) -> tuple[
        dict[str, Any], list[dict[str, Any]]]:
    summary_path = OUT / "final_audit_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary.update({
        "losslessly_compressed_files": len(compressed),
        "compression_restoration_hashes_verified": True,
        "evidence_package_manifest_path": relative(MANIFEST),
    })
    temporary = summary_path.with_suffix(".json.tmp")
    for _ in range(20):
        temporary.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        os.replace(temporary, summary_path)
        rows = collect_rows()
        largest = max(rows, key=lambda row: int(row["bytes"]))
        package_fields = {
            "evidence_package_file_count_excluding_self": len(rows),
            "evidence_package_bytes_excluding_self": sum(
                int(row["bytes"]) for row in rows),
            "largest_artifact_path": largest["path"],
            "largest_artifact_bytes": largest["bytes"],
        }
        if all(summary.get(key) == value
               for key, value in package_fields.items()):
            return summary, rows
        summary.update(package_fields)
    raise RuntimeError("evidence-package summary size did not converge")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-only", action="store_true")
    arguments = parser.parse_args()
    compressed = (
        retained_compression_records()
        if arguments.inventory_only else compress())
    summary, rows = update_summary(compressed)
    write_csv(
        MANIFEST, rows,
        ["path", "bytes", "sha256", "compressed", "role"])
    largest = max(rows, key=lambda row: int(row["bytes"]))
    total = sum(int(row["bytes"]) for row in rows)
    print(json.dumps({
        "files": len(rows),
        "bytes": total,
        "largest": largest,
        "compressed_files": len(compressed),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
