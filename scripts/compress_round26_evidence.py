#!/usr/bin/env python3
"""Deterministically gzip every retained Round 26 LP and verify round trips."""

from __future__ import annotations

import csv
import gzip
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_external_gurobi_production_validation_round26"
FIELDS = (
    "original_path", "compressed_path", "original_bytes", "compressed_bytes",
    "original_sha256", "compressed_sha256", "compression",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def main() -> None:
    grouped: dict[Path, list[dict[str, object]]] = {}
    paths = sorted(OUT.rglob("*.lp"))
    for path in paths:
        target = Path(str(path) + ".gz")
        original_hash = sha256(path)
        original_bytes = path.stat().st_size
        with path.open("rb") as source, target.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw,
                               compresslevel=9, mtime=0) as sink:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    sink.write(block)
        restored = hashlib.sha256()
        restored_bytes = 0
        with gzip.open(target, "rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                restored.update(block)
                restored_bytes += len(block)
        if restored.hexdigest() != original_hash or restored_bytes != original_bytes:
            target.unlink(missing_ok=True)
            raise RuntimeError(f"round-trip mismatch: {path}")
        path.unlink()
        run_dir = next(
            (parent for parent in path.parents
             if parent.parent.name == "runs"),
            path.parent,
        )
        grouped.setdefault(run_dir, []).append({
            "original_path": relative(path),
            "compressed_path": relative(target),
            "original_bytes": original_bytes,
            "compressed_bytes": target.stat().st_size,
            "original_sha256": original_hash,
            "compressed_sha256": sha256(target),
            "compression": "gzip_level9_mtime0_filename_omitted",
        })

    for run_dir, new_rows in grouped.items():
        manifest = run_dir / "compression_manifest.csv"
        rows: list[dict[str, object]] = []
        if manifest.is_file():
            with manifest.open(newline="", encoding="utf-8") as stream:
                rows.extend(csv.DictReader(stream))
        rows.extend(new_rows)
        rows.sort(key=lambda item: str(item["original_path"]))
        with manifest.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
    print(f"compressed_and_verified_lp_files={len(paths)}")


if __name__ == "__main__":
    main()
