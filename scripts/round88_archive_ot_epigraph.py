"""Archive every six-arm epigraph raw file with the frozen tar/hash kernel.

The source tree is read-only. Plan and build are distinct exclusive commands;
every finished tar member is streamed back and checked against its source SHA.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import time

import round88_archive_evidence as archive


RESULTS = archive.RESULTS
SOURCE = RESULTS / "ot_epigraph_diagnostic_001"
OUTPUT = RESULTS / "ot_epigraph_raw_archives"
PLAN = RESULTS / "ot_epigraph_raw_plan.json"
INDEX = RESULTS / "ot_epigraph_raw_index.json"
FAILURE = RESULTS / "ot_epigraph_archive_failure.json"
ARMS = ("01_F2-root_B1", "02_F2-root_B2", "03_D7-root_B1",
        "04_D7-root_B2", "05_D7-child_B1", "06_D7-child_B2")
TOP_LEDGER = ("batch_summary.json", "outside_batch_command_receipt.json",
              "raw_file_index.json")


def partition(entries: list[dict]) -> list[list[dict]]:
    """Single raw items >36 MiB get a dedicated, still <45 MiB compressed part."""
    chunks: list[list[dict]] = []
    current: list[dict] = []
    used = 0
    for entry in entries:
        size = entry["size"]
        if size > archive.RAW_PART_LIMIT:
            if current:
                chunks.append(current)
                current, used = [], 0
            chunks.append([entry])
            continue
        if current and used+size > archive.RAW_PART_LIMIT:
            chunks.append(current)
            current, used = [], 0
        current.append(entry)
        used += size
    if current:
        chunks.append(current)
    return chunks


def inventory() -> dict:
    started = time.perf_counter()
    if SOURCE.is_symlink() or SOURCE.is_junction() or not SOURCE.is_dir():
        raise RuntimeError("missing or linked epigraph diagnostic source")
    actual_dirs = {path.name for path in SOURCE.iterdir() if path.is_dir()}
    if actual_dirs != set(ARMS):
        raise RuntimeError("unexpected or missing epigraph arm directory")
    actual_top = {path.name for path in SOURCE.iterdir() if path.is_file()}
    if actual_top != set(TOP_LEDGER):
        raise RuntimeError("unexpected or missing epigraph top ledger")
    source_groups = [(name, archive.file_entries(SOURCE / name)) for name in ARMS]
    source_groups.append(("batch_ledger", [dict(path=archive.relative(SOURCE / name),
                                                size=(SOURCE / name).stat().st_size)
                                           for name in TOP_LEDGER]))
    groups = []
    seen: set[str] = set()
    for name, entries in source_groups:
        chunks = partition(entries)
        for part, chunk in enumerate(chunks, 1):
            suffix = "" if len(chunks) == 1 else ".part%02d-of-%02d" % (part, len(chunks))
            path = archive.relative(OUTPUT / (name + suffix + ".tar.gz"))
            for entry in chunk:
                if entry["path"] in seen:
                    raise RuntimeError("duplicate source member")
                seen.add(entry["path"])
            groups.append(dict(source_group=name, part_number=part,
                               part_count=len(chunks), archive=path,
                               source_file_count=len(chunk),
                               source_bytes=sum(item["size"] for item in chunk),
                               oversize_single_source=(len(chunk) == 1 and
                                                       chunk[0]["size"] > archive.RAW_PART_LIMIT),
                               files=chunk))
    all_source = {item["path"] for item in archive.file_entries(SOURCE)}
    if seen != all_source:
        raise RuntimeError("plan does not cover every source file exactly once")
    return dict(kind="ot_epigraph", member_root="results/unified_exact_round88",
                raw_part_limit_bytes=archive.RAW_PART_LIMIT,
                archive_limit_bytes=archive.ARCHIVE_LIMIT,
                source_group_count=len(source_groups), source_file_count=len(seen),
                source_bytes=sum(group["source_bytes"] for group in groups),
                archive_count=len(groups),
                initial_free_disk_bytes=shutil.disk_usage(RESULTS).free,
                inventory_wall_seconds=time.perf_counter()-started, groups=groups)


def make_plan() -> None:
    if PLAN.exists() or INDEX.exists() or OUTPUT.exists():
        raise RuntimeError("epigraph archive output already exists")
    planned = inventory()
    started = time.perf_counter()
    for group in planned["groups"]:
        group["files"], _ = archive.source_hashes(group)
    planned["plan_source_hash_seconds"] = time.perf_counter()-started
    archive.write_exclusive(PLAN, planned)
    print("planned epigraph", planned["source_file_count"], "files",
          planned["source_bytes"], "bytes", planned["archive_count"], "archives",
          flush=True)


def build() -> None:
    if INDEX.exists() or OUTPUT.exists():
        raise RuntimeError("epigraph archive output already exists")
    with PLAN.open("r", encoding="utf-8") as stream:
        planned = json.load(stream)
    fresh = inventory()
    if (fresh["source_file_count"] != planned["source_file_count"] or
            fresh["source_bytes"] != planned["source_bytes"] or
            [(g["archive"], g["files"]) for g in fresh["groups"]] !=
            [(g["archive"], [{"path": item["path"], "size": item["size"]}
                             for item in g["files"]]) for g in planned["groups"]]):
        raise RuntimeError("source inventory changed after plan")
    if shutil.disk_usage(RESULTS).free < planned["source_bytes"]:
        raise RuntimeError("free disk below source bytes")
    started = time.perf_counter()
    completed = []
    try:
        for number, group in enumerate(planned["groups"], 1):
            records, hash_seconds = archive.source_hashes(group)
            if records != group["files"]:
                raise RuntimeError("source SHA/size changed after plan")
            target = RESULTS / group["archive"]
            if target.exists():
                raise RuntimeError("archive target already exists")
            compress_seconds = archive.create_archive(target, records)
            size = target.stat().st_size
            if size >= archive.ARCHIVE_LIMIT:
                raise RuntimeError("compressed archive >=45 MiB: " + group["archive"])
            t = time.perf_counter()
            archive_sha = archive.digest(target)
            archive_hash_seconds = time.perf_counter()-t
            verify_seconds, verified_bytes = archive.verify_archive(target, records)
            if verified_bytes != group["source_bytes"]:
                raise RuntimeError("stream verified byte count differs")
            completed.append(dict(source_group=group["source_group"],
                                  part_number=group["part_number"],
                                  part_count=group["part_count"], archive=group["archive"],
                                  archive_size=size, archive_sha256=archive_sha,
                                  source_file_count=len(records), source_bytes=verified_bytes,
                                  verified_file_count=len(records), verified_bytes=verified_bytes,
                                  stream_verification="all_member_sha256_size_equal_source",
                                  source_hash_wall_seconds=hash_seconds,
                                  compression_wall_seconds=compress_seconds,
                                  archive_hash_wall_seconds=archive_hash_seconds,
                                  archive_verify_wall_seconds=verify_seconds,
                                  free_disk_after_bytes=shutil.disk_usage(RESULTS).free,
                                  files=records))
            print("verified epigraph", number, "/", len(planned["groups"]),
                  group["archive"], "files", len(records),
                  "raw_bytes", verified_bytes, "archive_bytes", size, flush=True)
        result = dict(kind="ot_epigraph", member_root=planned["member_root"],
                      source_file_count=planned["source_file_count"],
                      source_bytes=planned["source_bytes"],
                      archive_count=len(completed),
                      archive_bytes=sum(item["archive_size"] for item in completed),
                      archive_limit_bytes=archive.ARCHIVE_LIMIT,
                      initial_free_disk_bytes=planned["initial_free_disk_bytes"],
                      final_free_disk_bytes=shutil.disk_usage(RESULTS).free,
                      build_wall_seconds_before_index_write=time.perf_counter()-started,
                      groups=completed)
        archive.write_exclusive(INDEX, result)
        print("complete epigraph", result["source_file_count"], "files",
              result["archive_count"], "archives", result["archive_bytes"], "bytes",
              flush=True)
    except Exception as exc:
        if not FAILURE.exists():
            archive.write_exclusive(FAILURE, {"error": repr(exc),
                                             "completed_archives": len(completed),
                                             "elapsed_seconds": time.perf_counter()-started})
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "build"))
    args = parser.parse_args()
    make_plan() if args.mode == "plan" else build()


if __name__ == "__main__":
    main()
