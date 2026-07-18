#!/usr/bin/env python3
"""Compress and audit the complete Round 22 evidence package."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import shutil
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO / "results" / "gf_global_gini_tree_unified_validation_round"
MANIFEST_NAME = "evidence_package_manifest.csv"
GITHUB_HARD_LIMIT = 100_000_000


def hash_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            digest.update(block)
    return size, digest.hexdigest()


def hash_gzip_payload(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with gzip.open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            digest.update(block)
    return size, digest.hexdigest()


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO.resolve()).as_posix()


def evidence_scope(path: Path, root: Path) -> str:
    relative = path.relative_to(root).as_posix()
    if relative == "ExactEBRP-frozen.exe.gz":
        return "frozen_production_executable"
    if relative.startswith("attempts/"):
        pieces = relative.split("/")
        return f"attempt_archive:{pieces[1]}"
    if relative.startswith("mechanical/"):
        return "mechanical_gate_evidence"
    if relative.startswith(("runs/", "raw/", "logs/", "commands/")):
        return "run_evidence"
    return "protocol_or_analysis"


def load_previous_manifest(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as stream:
        return {row["stored_path"]: row for row in csv.DictReader(stream)}


def compress_file(path: Path) -> dict[str, object]:
    original_bytes, original_sha = hash_file(path)
    target = Path(f"{path}.gz")
    temporary = Path(f"{target}.tmp")
    with path.open("rb") as source, temporary.open("wb") as sink:
        with gzip.GzipFile(filename="", mode="wb", fileobj=sink, compresslevel=6, mtime=0) as archive:
            shutil.copyfileobj(source, archive, length=1024 * 1024)
    payload_bytes, payload_sha = hash_gzip_payload(temporary)
    if payload_bytes != original_bytes or payload_sha != original_sha:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"gzip round-trip verification failed: {path}")
    temporary.replace(target)
    path.unlink()
    return {
        "original_path": repo_path(path),
        "original_bytes": original_bytes,
        "original_sha256": original_sha,
        "stored_path": repo_path(target),
        "compression": "gzip",
        "round_trip_verified": "true",
    }


def package(root: Path, threshold: int) -> None:
    root = root.resolve()
    manifest_path = root / MANIFEST_NAME
    previous = load_previous_manifest(manifest_path)
    compressed: dict[str, dict[str, object]] = {}

    # A killed compressor can leave only its temporary output because originals
    # are removed strictly after verification and atomic replacement. Discard
    # those restart-safe temporaries before taking the candidate snapshot.
    for temporary in root.rglob("*.gz.tmp"):
        original = Path(str(temporary)[: -len(".gz.tmp")])
        target = Path(str(temporary)[: -len(".tmp")])
        if not original.exists() and not target.exists():
            raise RuntimeError(f"orphan gzip temporary without source or target: {temporary}")
        temporary.unlink()

    frozen = REPO / "build_round22" / "ExactEBRP-frozen.exe"
    packaged_frozen = root / "ExactEBRP-frozen.exe.gz"
    if not packaged_frozen.exists():
        if not frozen.exists():
            raise RuntimeError(f"missing frozen executable: {frozen}")
        row = compress_external(frozen, packaged_frozen)
        compressed[row["stored_path"]] = row

    candidates = sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.name != MANIFEST_NAME
        and path.suffix != ".gz"
        and not path.name.endswith(".gz.tmp")
        and path.stat().st_size >= threshold
    )
    for index, path in enumerate(candidates, 1):
        if not path.exists():
            continue
        row = compress_file(path)
        compressed[row["stored_path"]] = row
        print(f"compressed {index}/{len(candidates)} {row['original_path']}")

    rows: list[dict[str, object]] = []
    stored_files = sorted(
        path for path in root.rglob("*") if path.is_file() and path.name != MANIFEST_NAME
    )
    for path in stored_files:
        stored_path = repo_path(path)
        stored_bytes, stored_sha = hash_file(path)
        if stored_bytes >= GITHUB_HARD_LIMIT:
            raise RuntimeError(f"stored artifact exceeds GitHub hard limit: {stored_path} ({stored_bytes})")
        prior = compressed.get(stored_path) or previous.get(stored_path)
        if path.suffix == ".gz":
            payload_bytes, payload_sha = hash_gzip_payload(path)
            if prior:
                original_path = str(prior["original_path"])
                original_bytes = int(prior["original_bytes"])
                original_sha = str(prior["original_sha256"])
            else:
                original_path = stored_path[:-3]
                original_bytes = payload_bytes
                original_sha = payload_sha
            verified = payload_bytes == original_bytes and payload_sha == original_sha
            if not verified:
                raise RuntimeError(f"stored gzip does not match original metadata: {stored_path}")
            compression = "gzip"
        else:
            original_path = stored_path
            original_bytes = stored_bytes
            original_sha = stored_sha
            compression = "none"
            verified = True
        rows.append(
            {
                "scope": evidence_scope(path, root),
                "original_path": original_path,
                "original_bytes": original_bytes,
                "original_sha256": original_sha,
                "stored_path": stored_path,
                "stored_bytes": stored_bytes,
                "stored_sha256": stored_sha,
                "compression": compression,
                "round_trip_verified": str(verified).lower(),
            }
        )

    original_index = {str(row["original_path"]): row for row in rows}
    commands_root = root / "commands"
    official_ids: list[str] = []
    for command_path in sorted(commands_root.glob("*.json")):
        import json

        command = json.loads(command_path.read_text(encoding="utf-8"))
        if command.get("official"):
            official_ids.append(str(command["run_id"]))
    if len(official_ids) != 81:
        raise RuntimeError(f"expected 81 official command records, found {len(official_ids)}")
    required_templates = (
        "commands/{run_id}.json",
        "raw/{run_id}.json",
        "logs/{run_id}.console.log",
        "logs/{run_id}.native.log",
        "runs/{run_id}/artifact_manifest.csv",
        "runs/{run_id}/canonical_checkpoints.csv",
        "runs/{run_id}/raw_progress.csv",
    )
    missing: list[str] = []
    root_prefix = repo_path(root)
    for run_id in official_ids:
        for template in required_templates:
            logical = f"{root_prefix}/{template.format(run_id=run_id)}"
            if logical not in original_index:
                missing.append(logical)
    if missing:
        raise RuntimeError(f"missing {len(missing)} required official artifacts; first={missing[0]}")
    expected_attempts = {
        "excluded",
        "pre_freshness_erratum_21087954",
        "pre_integrity_erratum_cf12a925",
        "pre_monotonicity_erratum_90947929",
        "pre_refreeze_753275454e066ff7",
    }
    retained_attempts = {path.name for path in (root / "attempts").iterdir() if path.is_dir()}
    if retained_attempts != expected_attempts:
        raise RuntimeError(f"attempt archive mismatch: {sorted(retained_attempts)}")

    with manifest_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "scope",
                "original_path",
                "original_bytes",
                "original_sha256",
                "stored_path",
                "stored_bytes",
                "stored_sha256",
                "compression",
                "round_trip_verified",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    largest = max(rows, key=lambda row: int(row["stored_bytes"]))
    total = sum(int(row["stored_bytes"]) for row in rows)
    compressed_count = sum(row["compression"] == "gzip" for row in rows)
    print(
        f"packaged {len(rows)} artifacts ({compressed_count} gzip), "
        f"stored_bytes={total}, official_coverage={len(official_ids)}/81, "
        f"largest={largest['stored_bytes']} {largest['stored_path']}"
    )


def compress_external(source: Path, target: Path) -> dict[str, object]:
    original_bytes, original_sha = hash_file(source)
    temporary = Path(f"{target}.tmp")
    with source.open("rb") as input_stream, temporary.open("wb") as output_stream:
        with gzip.GzipFile(filename="", mode="wb", fileobj=output_stream, compresslevel=6, mtime=0) as archive:
            shutil.copyfileobj(input_stream, archive, length=1024 * 1024)
    payload_bytes, payload_sha = hash_gzip_payload(temporary)
    if payload_bytes != original_bytes or payload_sha != original_sha:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("frozen executable gzip verification failed")
    temporary.replace(target)
    return {
        "original_path": repo_path(source),
        "original_bytes": original_bytes,
        "original_sha256": original_sha,
        "stored_path": repo_path(target),
        "compression": "gzip",
        "round_trip_verified": "true",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--threshold-bytes", type=int, default=1_000_000)
    args = parser.parse_args()
    package(args.root, args.threshold_bytes)


if __name__ == "__main__":
    main()
