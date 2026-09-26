"""Round88 retained raw evidence archiver with independent stream verification.

Run plan first, inspect it, then build once. Original files are never moved.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import time


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/unified_exact_round88"
RAW_PART_LIMIT = 36 * 1024 * 1024
ARCHIVE_LIMIT = 45 * 1024 * 1024
REST_ARMS = (
    "07_D3_ENS-C", "08_D3_P-GRB", "09_D3_A1",
    "10_C2_A1", "11_C2_P-GRB", "12_C2_ENS-C",
    "13_D7_P-GRB", "14_D7_A1", "15_D7_ENS-C",
    "16_U6_ENS-C", "17_U6_A1", "18_U6_P-GRB",
    "19_F5_A1", "20_F5_ENS-C", "21_F5_P-GRB",
    "22_F6_ENS-C", "23_F6_P-GRB", "24_F6_A1")
REST_LEDGER = (
    "runner_a1_g3/identity.json", "runner_a1_g3/preflight.json",
    "runner_a1_g3/processes.jsonl", "runner_a1_g3/summary.jsonl",
    "runner_a1_g3/runtime_status.json",
    "runner_a1_g3/runner_rest_completion.json",
    "runner_a1_g3/runner_rest_lease.json",
    *("runner_a1_g3/runner_cross_arm_" + name + ".json"
      for name in ("D3", "C2", "D7", "U6", "F5", "F6")))
CROSS_DIRS = (
    "ot_b1_cross_preparation", "ot_b1_cross_preparation_v2",
    "ot_b1_cross_preparation_v3", "ot_b1_cross_preparation_v4")
CROSS_LEDGER = (
    "ot_b1_cross_contract.md", "ot_qualification_b1_cross.md",
    "ot_b1_cross_independent_review.md",
    "ot_b1_cross_admission.json")


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for piece in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(piece)
    return value.hexdigest()


def relative(path: Path) -> str:
    return path.relative_to(RESULTS).as_posix()


def file_entries(directory: Path) -> list[dict]:
    if (not directory.is_dir() or directory.is_symlink() or
            directory.is_junction()):
        raise RuntimeError("missing or linked source directory: " + str(directory))
    entries = []
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise RuntimeError("linked source refused: " + str(path))
        if path.is_file():
            entries.append(dict(path=relative(path), size=path.stat().st_size))
    if not entries:
        raise RuntimeError("empty source directory: " + str(directory))
    return entries


def named_entries(names: tuple[str, ...]) -> list[dict]:
    entries = []
    for name in names:
        path = RESULTS / name
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("missing or linked source file: " + name)
        entries.append(dict(path=relative(path), size=path.stat().st_size))
    return sorted(entries, key=lambda item: item["path"])


def partition(entries: list[dict]) -> list[list[dict]]:
    chunks: list[list[dict]] = []
    current: list[dict] = []
    used = 0
    for entry in entries:
        if entry["size"] > RAW_PART_LIMIT:
            raise RuntimeError("single source exceeds part cap: " + entry["path"])
        if current and used + entry["size"] > RAW_PART_LIMIT:
            chunks.append(current)
            current, used = [], 0
        current.append(entry)
        used += entry["size"]
    if current:
        chunks.append(current)
    return chunks


def plan(kind: str) -> dict:
    if kind == "runner_rest":
        source_groups = [
            (arm, file_entries(RESULTS / "runner_a1_g3/raw" / arm))
            for arm in REST_ARMS]
        source_groups.append(("rest_ledgers", named_entries(REST_LEDGER)))
        archive_directory = "runner_rest_raw_archives"
    else:
        source_groups = [
            (name, file_entries(RESULTS / name)) for name in CROSS_DIRS]
        source_groups.append(("preparation_ledgers", named_entries(CROSS_LEDGER)))
        archive_directory = "cross_prep_archives"
    groups = []
    seen: set[str] = set()
    for source_name, entries in source_groups:
        for entry in entries:
            if entry["path"] in seen:
                raise RuntimeError("duplicate source path: " + entry["path"])
            seen.add(entry["path"])
        chunks = partition(entries)
        for part_number, chunk in enumerate(chunks, 1):
            suffix = ("" if len(chunks) == 1 else
                      ".part%02d-of-%02d" % (part_number, len(chunks)))
            name = source_name + suffix
            groups.append(dict(
                source_group=source_name,
                part_number=part_number, part_count=len(chunks),
                archive=f"{archive_directory}/{name}.tar.gz",
                file_count=len(chunk),
                source_bytes=sum(x["size"] for x in chunk),
                files=chunk))
    return dict(kind=kind, member_root="results/unified_exact_round88",
                raw_part_limit_bytes=RAW_PART_LIMIT,
                archive_limit_bytes=ARCHIVE_LIMIT,
                source_group_count=len(source_groups),
                source_file_count=len(seen),
                source_bytes=sum(group["source_bytes"] for group in groups),
                archive_count=len(groups), groups=groups)


def write_exclusive(path: Path, data: dict) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def source_hashes(group: dict) -> tuple[list[dict], float]:
    started = time.perf_counter()
    records = []
    for entry in group["files"]:
        path = RESULTS / entry["path"]
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("source disappeared or became link: " + entry["path"])
        if path.stat().st_size != entry["size"]:
            raise RuntimeError("source size drift: " + entry["path"])
        records.append(dict(path=entry["path"], size=entry["size"],
                            sha256=digest(path)))
    return records, time.perf_counter() - started


def create_archive(path: Path, records: list[dict]) -> float:
    started = time.perf_counter()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as output:
        with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w|") as tar:
                for entry in records:
                    source = RESULTS / entry["path"]
                    info = tarfile.TarInfo(entry["path"])
                    info.size = entry["size"]
                    info.mtime = 0
                    info.mode = 0o644
                    info.uid = info.gid = 0
                    info.uname = info.gname = ""
                    with source.open("rb") as stream:
                        tar.addfile(info, stream)
    return time.perf_counter() - started


def verify_archive(path: Path, records: list[dict]) -> tuple[float, int]:
    started = time.perf_counter()
    expected = {item["path"]: item for item in records}
    seen: set[str] = set()
    total = 0
    with path.open("rb") as archive:
        with tarfile.open(fileobj=archive, mode="r|gz") as tar:
            for member in tar:
                name = member.name
                if (not member.isfile() or name not in expected or
                        name in seen or name.startswith("/") or
                        ".." in Path(name).parts):
                    raise RuntimeError("unexpected archive member: " + name)
                target = expected[name]
                if member.size != target["size"]:
                    raise RuntimeError("archived size differs: " + name)
                stream = tar.extractfile(member)
                if stream is None:
                    raise RuntimeError("member could not be read: " + name)
                value = hashlib.sha256()
                measured = 0
                while True:
                    piece = stream.read(1024 * 1024)
                    if not piece:
                        break
                    measured += len(piece)
                    value.update(piece)
                if measured != target["size"] or value.hexdigest() != target["sha256"]:
                    raise RuntimeError("archived hash/length differs: " + name)
                total += measured
                seen.add(name)
    if seen != set(expected):
        raise RuntimeError("archive missing expected files")
    return time.perf_counter() - started, total


def build(kind: str) -> None:
    plan_path = RESULTS / ("runner_rest_raw_plan.json" if kind == "runner_rest"
                           else "cross_prep_plan.json")
    index_path = RESULTS / ("runner_rest_raw_index.json" if kind == "runner_rest"
                            else "cross_prep_index.json")
    if index_path.exists():
        raise RuntimeError("index already exists; refusing duplicate build")
    with plan_path.open("r", encoding="utf-8") as stream:
        planned = json.load(stream)
    if planned != plan(kind):
        raise RuntimeError("source inventory differs from precompression plan")
    started = time.perf_counter()
    built = []
    try:
        for number, group in enumerate(planned["groups"], 1):
            archive = RESULTS / group["archive"]
            if archive.exists():
                raise RuntimeError("archive already exists: " + str(archive))
            records, hash_seconds = source_hashes(group)
            compress_seconds = create_archive(archive, records)
            size = archive.stat().st_size
            if size >= ARCHIVE_LIMIT:
                raise RuntimeError("archive exceeds 45 MiB target: " + str(archive))
            sha_started = time.perf_counter()
            archive_sha = digest(archive)
            archive_hash_seconds = time.perf_counter() - sha_started
            verify_seconds, verified_bytes = verify_archive(archive, records)
            item = dict(
                source_group=group["source_group"],
                part_number=group["part_number"], part_count=group["part_count"],
                archive=group["archive"], archive_size=size,
                archive_sha256=archive_sha,
                source_file_count=len(records), source_bytes=group["source_bytes"],
                verified_file_count=len(records), verified_bytes=verified_bytes,
                stream_verification="all_member_sha256_size_equal_source",
                source_hash_wall_seconds=hash_seconds,
                compression_wall_seconds=compress_seconds,
                archive_hash_wall_seconds=archive_hash_seconds,
                archive_verify_wall_seconds=verify_seconds,
                files=records)
            built.append(item)
            print("verified", kind, number, "/", len(planned["groups"]),
                  group["archive"], "files", len(records),
                  "raw_bytes", group["source_bytes"],
                  "archive_bytes", size, flush=True)
        index = dict(
            kind=kind, member_root=planned["member_root"],
            source_file_count=planned["source_file_count"],
            source_bytes=planned["source_bytes"],
            archive_count=len(built),
            archive_bytes=sum(item["archive_size"] for item in built),
            raw_part_limit_bytes=RAW_PART_LIMIT,
            archive_limit_bytes=ARCHIVE_LIMIT,
            total_build_wall_seconds_before_index_write=time.perf_counter() - started,
            groups=built)
        write_exclusive(index_path, index)
        print("complete", kind, "files", index["source_file_count"],
              "archives", index["archive_count"],
              "archive_bytes", index["archive_bytes"], flush=True)
    except Exception as error:
        failure = RESULTS / (kind + "_archive_failure.json")
        if not failure.exists():
            write_exclusive(failure, dict(kind=kind, error=repr(error),
                                          completed_archives=len(built),
                                          elapsed_seconds=time.perf_counter() - started))
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("plan", "build"))
    parser.add_argument("kind", choices=("runner_rest", "cross_prep"))
    args = parser.parse_args()
    if args.mode == "plan":
        path = RESULTS / ("runner_rest_raw_plan.json" if args.kind == "runner_rest"
                          else "cross_prep_plan.json")
        planned = plan(args.kind)
        write_exclusive(path, planned)
        print("planned", args.kind, "files", planned["source_file_count"],
              "raw_bytes", planned["source_bytes"],
              "archives", planned["archive_count"])
    else:
        build(args.kind)


if __name__ == "__main__":
    main()
