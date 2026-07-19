#!/usr/bin/env python3
"""Deterministically compress Round 24 model streams and hash the package."""

from __future__ import annotations

import csv
import gzip
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "results" / "gf_solver_backend_migration_round24"
MANIFEST = PACKAGE / "evidence_package_manifest.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def compress_model_streams() -> None:
    for source in sorted((PACKAGE / "stage0").glob("**/models/*.lp")):
        target = source.with_suffix(source.suffix + ".gz")
        with source.open("rb") as incoming, target.open("wb") as raw:
            with gzip.GzipFile(
                filename="", mode="wb", fileobj=raw, compresslevel=9, mtime=0
            ) as outgoing:
                for block in iter(lambda: incoming.read(1024 * 1024), b""):
                    outgoing.write(block)
        source.unlink()


def write_manifest() -> None:
    files = [
        path
        for path in sorted(PACKAGE.rglob("*"))
        if path.is_file() and path != MANIFEST
    ]
    with MANIFEST.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["relative_path", "bytes", "sha256", "role"])
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            if "/stage0/" in relative:
                role = "stage0_evidence"
            elif path.suffix in {".json", ".csv"}:
                role = "audit_or_result"
            else:
                role = "design_or_report"
            writer.writerow([relative, path.stat().st_size, sha256(path), role])


if __name__ == "__main__":
    PACKAGE.resolve().relative_to(ROOT.resolve())
    compress_model_streams()
    write_manifest()
