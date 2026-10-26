"""Archive the completed Round91 D3/C2 diagnostic exactly once.

This is evidence packaging only: no model import or Optimize. The signed raw
index is checked against fresh source hashes, including all primal/residual
files, before any archive is opened. Original files remain in place.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile
import time


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/unified_exact_round91"
RAW = RESULTS / "handling_real_diagnostic_001"
RAW_INDEX = RAW / "raw_index.json"
REPORT = RAW / "report.md"
PACKAGE = RESULTS / "handling_real_raw_archive.tar.gz"
INDEX = RESULTS / "handling_real_raw_archive_index.json"
RECEIPT = RESULTS / "handling_real_raw_archive_receipt.json"
FAILURE = RESULTS / "handling_real_raw_archive_failure.json"
LIMIT = 45 * 1024 * 1024  # Strictly less than 45 MiB.
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def digest(path: Path) -> tuple[str, int]:
    sha = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for piece in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(piece)
            size += len(piece)
    return sha.hexdigest(), size


def write_new(path: Path, value: dict) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def source_path(name: str) -> Path:
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or "//" in name):
        raise RuntimeError("invalid raw-index path: " + repr(name))
    parts = PurePosixPath(name).parts
    if (not parts or any(part in ("", ".", "..") for part in parts)
            or PurePosixPath(name).is_absolute()
            or PurePosixPath(name).as_posix() != name):
        raise RuntimeError("unsafe raw-index path: " + name)
    path = RAW.joinpath(*parts)
    current = RESULTS
    for part in (RAW.name, *parts):
        current = current / part
        if current.is_symlink() or current.is_junction():
            raise RuntimeError("linked source refused: " + str(current))
    if not path.is_file() or not path.resolve().is_relative_to(RAW.resolve()):
        raise RuntimeError("missing or escaping source: " + name)
    return path


def metadata_path(path: Path) -> Path:
    current = RESULTS
    for part in path.relative_to(RESULTS).parts:
        current = current / part
        if current.is_symlink() or current.is_junction():
            raise RuntimeError("linked metadata refused: " + str(current))
    if not path.is_file() or not path.resolve().is_relative_to(RESULTS.resolve()):
        raise RuntimeError("missing or escaping metadata: " + str(path))
    return path


def records_from_raw_index() -> tuple[list[dict], str]:
    metadata_path(RAW_INDEX)
    raw_index_bytes = RAW_INDEX.read_bytes()
    raw_index_sha = hashlib.sha256(raw_index_bytes).hexdigest()
    old = json.loads(raw_index_bytes)
    if (old.get("schema") != "round91-real-handling-raw-index-v1"
            or old.get("raw_file_count") != 47
            or not isinstance(old.get("files"), list)
            or len(old["files"]) != 47):
        raise RuntimeError("raw index schema/count differs from completed run")
    if RAW.is_symlink() or RAW.is_junction() or not RAW.is_dir():
        raise RuntimeError("missing or linked raw root")
    names: set[str] = set()
    records = []
    for item in old["files"]:
        name = item.get("path")
        path = source_path(name)
        if name in names or name in ("report.md", "raw_index.json"):
            raise RuntimeError("duplicate or reserved raw member: " + repr(name))
        names.add(name)
        if (type(item.get("size_bytes")) is not int or item["size_bytes"] < 0
                or not isinstance(item.get("sha256"), str)
                or HEX64.fullmatch(item["sha256"]) is None):
            raise RuntimeError("invalid raw-index size/hash: " + name)
        actual_sha, actual_size = digest(path)
        if actual_sha != item["sha256"] or actual_size != item["size_bytes"]:
            raise RuntimeError("source differs from raw index: " + name)
        records.append(dict(path="handling_real_diagnostic_001/" + name,
                            size=actual_size, sha256=actual_sha,
                            source="independently_rehashed_against_raw_index"))
    if sum(record["size"] for record in records) != old.get("raw_total_bytes"):
        raise RuntimeError("raw byte total differs from raw index")
    actual_names: set[str] = set()
    for path in RAW.rglob("*"):
        if path.is_symlink() or path.is_junction():
            raise RuntimeError("linked raw tree member refused: " + str(path))
        if path.is_file():
            actual_names.add(path.relative_to(RAW).as_posix())
    if actual_names != names | {"report.md", "raw_index.json"}:
        raise RuntimeError("raw tree has missing or unindexed files")
    for path in (REPORT, RAW_INDEX):
        metadata_path(path)
        sha, size = digest(path)
        if path == RAW_INDEX and sha != raw_index_sha:
            raise RuntimeError("raw index changed during inventory")
        records.append(dict(path=path.relative_to(RESULTS).as_posix(),
                            size=size, sha256=sha,
                            source="fresh_metadata_hash"))
    if len(records) != 49 or len({row["path"] for row in records}) != 49:
        raise RuntimeError("archive requires exactly 49 distinct members")
    return sorted(records, key=lambda row: row["path"]), raw_index_sha


def create_archive(records: list[dict]) -> None:
    # Exclusive create preserves a failed partial package for diagnosis.
    with PACKAGE.open("xb") as output:
        with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|") as tar:
                for row in records:
                    source = RESULTS / row["path"]
                    metadata_path(source)
                    if source.stat().st_size != row["size"]:
                        raise RuntimeError("source size changed during compression")
                    info = tarfile.TarInfo(row["path"])
                    info.size = row["size"]
                    info.mtime = 0
                    info.mode = 0o644
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    with source.open("rb") as stream:
                        tar.addfile(info, stream)


def verify_archive(records: list[dict]) -> int:
    wanted = {row["path"]: row for row in records}
    seen: set[str] = set()
    bytes_read = 0
    with PACKAGE.open("rb") as archive:
        with tarfile.open(fileobj=archive, mode="r|gz") as tar:
            for member in tar:
                name = member.name
                if (not member.isfile() or name not in wanted or name in seen
                        or name.startswith("/") or ".." in PurePosixPath(name).parts):
                    raise RuntimeError("unexpected or duplicate archive member: " + name)
                row = wanted[name]
                if member.size != row["size"]:
                    raise RuntimeError("archive member size mismatch: " + name)
                stream = tar.extractfile(member)
                if stream is None:
                    raise RuntimeError("archive member unreadable: " + name)
                sha = hashlib.sha256()
                size = 0
                for piece in iter(lambda: stream.read(1024 * 1024), b""):
                    sha.update(piece)
                    size += len(piece)
                if size != row["size"] or sha.hexdigest() != row["sha256"]:
                    raise RuntimeError("archive member hash/size mismatch: " + name)
                seen.add(name)
                bytes_read += size
    if seen != set(wanted):
        raise RuntimeError("archive has missing members")
    return bytes_read


def stage_paths() -> list[str]:
    # Large primal/residual JSONL files are only in the package.
    names = [
        "scripts/round91_archive_handling_real.py",
        "results/unified_exact_round91/handling_real_diagnostic_001/report.md",
        "results/unified_exact_round91/handling_real_diagnostic_001/raw_index.json",
        "results/unified_exact_round91/handling_real_diagnostic_001/outer_watchdog.py",
        "results/unified_exact_round91/handling_real_diagnostic_001/outer_D3/outer_receipt.json",
        "results/unified_exact_round91/handling_real_diagnostic_001/outer_C2/outer_receipt.json",
        "results/unified_exact_round91/handling_real_postrun_process_check.json",
        PACKAGE.relative_to(ROOT).as_posix(),
        INDEX.relative_to(ROOT).as_posix(),
        RECEIPT.relative_to(ROOT).as_posix(),
    ]
    return names


def main() -> None:
    started = time.perf_counter()
    if any(path.exists() or path.is_symlink()
           for path in (PACKAGE, INDEX, RECEIPT, FAILURE)):
        raise RuntimeError("archive output/receipt already exists; refusing overwrite or retry")
    phases: dict[str, float] = {}
    stage = "source_hash_and_inventory"
    try:
        tick = time.perf_counter()
        records, raw_index_sha = records_from_raw_index()
        phases[stage] = time.perf_counter() - tick
        source_bytes = sum(row["size"] for row in records)
        stage = "compression"
        tick = time.perf_counter()
        create_archive(records)
        phases[stage] = time.perf_counter() - tick
        package_size = PACKAGE.stat().st_size
        if package_size >= LIMIT:
            raise RuntimeError("package is not below 45 MiB")
        stage = "archive_sha256"
        tick = time.perf_counter()
        package_sha, measured_package_size = digest(PACKAGE)
        phases[stage] = time.perf_counter() - tick
        if measured_package_size != package_size:
            raise RuntimeError("package size drift")
        stage = "archive_stream_verification"
        tick = time.perf_counter()
        verified_bytes = verify_archive(records)
        phases[stage] = time.perf_counter() - tick
        if verified_bytes != source_bytes:
            raise RuntimeError("verified byte total mismatch")
        stage = "source_postflight"
        tick = time.perf_counter()
        for row in records:
            sha, size = digest(metadata_path(RESULTS / row["path"]))
            if sha != row["sha256"] or size != row["size"]:
                raise RuntimeError("source changed after archive: " + row["path"])
        phases[stage] = time.perf_counter() - tick
        stage = "write_index"
        write_new(INDEX, dict(
            schema="round91-handling-real-archive-index-v1",
            member_root="results/unified_exact_round91",
            raw_index_sha256=raw_index_sha, raw_file_count=47,
            metadata_file_count=2, source_file_count=49,
            source_bytes=source_bytes, verified_bytes=verified_bytes,
            package=PACKAGE.relative_to(ROOT).as_posix(),
            package_bytes=package_size, package_sha256=package_sha,
            package_limit_exclusive_bytes=LIMIT,
            verification="fresh_raw_index_sha_and_full_member_stream_sha_size",
            files=records))
        stage = "write_receipt"
        write_new(RECEIPT, dict(
            schema="round91-handling-real-archive-receipt-v1",
            status="complete", index_sha256=digest(INDEX)[0],
            archive_sha256=package_sha, source_file_count=49,
            source_bytes=source_bytes, archive_bytes=package_size,
            phase_wall_seconds=phases,
            wall_seconds_before_receipt_write=time.perf_counter() - started,
            staging_paths=stage_paths(),
            originals_preserved=True, optimize_calls=0, build_calls=0))
        print("archived 49 files; bytes", source_bytes,
              "package bytes", package_size,
              "wall seconds", time.perf_counter() - started, flush=True)
    except Exception as error:
        if not FAILURE.exists():
            write_new(FAILURE, dict(
                schema="round91-handling-real-archive-failure-v1",
                stage=stage, error=repr(error), phase_wall_seconds=phases,
                elapsed_seconds=time.perf_counter() - started,
                partial_package_preserved=PACKAGE.exists(),
                originals_preserved=True))
        raise


if __name__ == "__main__":
    main()
