"""Archive finalized Round90 G3 raw arms with the frozen Round88 kernel.

Neither mode should run while the campaign runner is active. Run `plan`,
inspect its exact file inventory, then run `build` under an exclusive archive
slot. Original raw files remain in place. Top-level runner ledgers stay out of
these tarballs so they can be submitted separately with the small metadata.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time

import round88_archive_evidence as archive


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/unified_exact_round90"
CAMPAIGN = RESULTS / "runner_lp_g_g3"
RAW = CAMPAIGN / "raw"
PREREG = RESULTS / "preregistration_g3.json"
PLAN = RESULTS / "runner_lp_g_raw_plan.json"
INDEX = RESULTS / "runner_lp_g_raw_index.json"
FAILURE = RESULTS / "runner_lp_g_archive_failure.json"
OUTPUT = RESULTS / "runner_lp_g_raw_archives"
# The imported, independently used archive kernel resolves every member path
# relative to its RESULTS global. Rebind that root only in this new driver.
archive.RESULTS = RESULTS


def expected_arms() -> tuple[str, ...]:
    with PREREG.open("r", encoding="utf-8") as stream:
        prereg = json.load(stream)
    if (prereg.get("schema") != "round90-lp-g-g3-preregistration-v1" or
            prereg.get("planned_runs") != 16 or
            prereg.get("runtime_root") !=
            "results/unified_exact_round90/runner_lp_g_g3"):
        raise RuntimeError("Round90 preregistration identity invalid")
    execution = prereg.get("execution_order")
    if not isinstance(execution, list) or len(execution) != 16:
        raise RuntimeError("Round90 execution order invalid")
    names = []
    for number, item in enumerate(execution, 1):
        if not isinstance(item, str) or item.count("/") != 1:
            raise RuntimeError("invalid Round90 arm identity")
        role, method = item.split("/")
        if not role or method not in ("ENS-C", "LP-G"):
            raise RuntimeError("invalid Round90 arm method")
        names.append(f"{number:02d}_{role}_{method}")
    if len(set(names)) != 16:
        raise RuntimeError("duplicate Round90 arm name")
    return tuple(names)


def require_stopped() -> None:
    if (CAMPAIGN / "active_run.lock").exists():
        raise RuntimeError("Round90 runner lock still active")
    expression = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "($_.Name -match '^(ExactEBRP|Round[0-9]+.*Experiment|"
        "Round89NativeOtB1Micro|Round90LpGSplitTests|gurobi_cl|"
        "cmake|ninja|g\\+\\+|cc1plus|cl|link|ld|MSBuild)\\.exe$') "
        "-or ($_.Name -match '^python(w)?\\.exe$' -and "
        "$_.CommandLine -match 'round90_lp_g_g3\\.py|"
        "round88[_-]ot|round90[_-]ot|ot[_-]diagnostic|ot[_-]closure') } "
        "| Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    )
    output = subprocess.check_output(
        ["powershell.exe", "-NoProfile", "-Command", expression],
        text=True, timeout=15).strip()
    if output and json.loads(output):
        raise RuntimeError("solver, build or Round90 runner process still active")


def finalized_attempts(arms: tuple[str, ...]) -> dict:
    with (CAMPAIGN / "identity.json").open("r", encoding="utf-8") as stream:
        identity = json.load(stream)
    launches = identity.get("launches")
    if (identity.get("schema") != "round90-lp-g-g3-identity-v1" or
            not isinstance(launches, list) or len(launches) != 16 or
            identity.get("prereg_sha256") != archive.digest(PREREG)):
        raise RuntimeError("Round90 campaign identity invalid")
    for number, (launch, arm) in enumerate(zip(launches, arms), 1):
        if (not isinstance(launch, dict) or launch.get("number") != number or
                f'{number:02d}_{launch.get("id")}_{launch.get("arm")}' != arm or
                Path(launch.get("destination", "")).resolve() !=
                (RAW / arm).resolve()):
            raise RuntimeError("Round90 launch/directory identity mismatch")
    summary_path = CAMPAIGN / "summary.jsonl"
    with summary_path.open("r", encoding="utf-8") as stream:
        summary = [json.loads(line) for line in stream if line.strip()]
    if not 4 <= len(summary) <= 16 or any(
            not isinstance(row, dict) for row in summary):
        raise RuntimeError("Round90 summary is not a finished prefix")
    if any(row.get("audit_passed") is not True for row in summary[:4]):
        raise RuntimeError("Round90 smoke prefix is not fully audited")
    hashes = {"identity": archive.digest(CAMPAIGN / "identity.json"),
              "summary": archive.digest(summary_path)}
    stage_status = {}
    for stage, planned, count in (("smoke", 4, 4),
                                  ("rest", 12, len(summary)-4)):
        path = CAMPAIGN / f"runner_{stage}_completion.json"
        with path.open("r", encoding="utf-8") as stream:
            completed = json.load(stream)
        if (not isinstance(completed, dict) or
                completed.get("stage") != stage or
                completed.get("planned") != planned or
                completed.get("completed") != count or
                (stage == "smoke" and
                 (completed.get("all_audits_passed") is not True or
                  completed.get("stop_reason") is not None)) or
                (stage == "rest" and
                 (count < 12 or completed.get("all_audits_passed") is not True)
                 and not completed.get("stop_reason"))):
            raise RuntimeError("Round90 stage completion/prefix invalid: " + stage)
        if stage == "rest" and completed.get("all_audits_passed") != (
                count == 12 and all(row.get("audit_passed") is True
                                    for row in summary[4:])):
            raise RuntimeError("Round90 rest completion/audit mismatch")
        hashes[stage] = archive.digest(path)
        stage_status[stage] = dict(completed=count, planned=planned,
                                   all_audits_passed=completed["all_audits_passed"],
                                   stop_reason=completed.get("stop_reason"))
    failures = {}
    absent_raw = []
    empty_raw = []
    for number, row in enumerate(summary, 1):
        launch = launches[number-1]
        arm = arms[number-1]
        source = RAW / arm
        if source.is_symlink() or source.is_junction():
            raise RuntimeError("linked attempted raw directory refused")
        if (row.get("number") != number or row.get("id") != launch["id"] or
                row.get("arm") != launch["arm"] or
                Path(row.get("destination", "")).resolve() != source.resolve()):
            raise RuntimeError("Round90 summary/launch prefix mismatch")
        if row.get("completion") is not None:
            if not source.is_dir() or not (source / "completion.json").is_file():
                raise RuntimeError("completed Round90 arm lacks raw receipt")
            if (row.get("failure_record") or
                    row["completion"] != json.loads(
                        (source / "completion.json").read_text(encoding="utf-8"))):
                raise RuntimeError("completed arm/raw receipt mismatch")
            audit = json.loads((source / "audit.json").read_text(encoding="utf-8"))
            if (not isinstance(audit, dict) or
                    row.get("audit_passed") is not audit.get("passed") or
                    row.get("endpoint") != audit.get("endpoint")):
                raise RuntimeError("completed arm/audit receipt mismatch")
        else:
            expected_failure = CAMPAIGN / f"runner_failure_{number:02d}.json"
            if (row.get("audit_passed") is not False or
                    row.get("failure_record") != str(expected_failure) or
                    not expected_failure.is_file()):
                raise RuntimeError("prelaunch failure receipt missing/ambiguous")
            with expected_failure.open("r", encoding="utf-8") as stream:
                failure = json.load(stream)
            if (not isinstance(failure, dict) or
                    failure.get("number") != number or
                    failure.get("id") != launch["id"] or
                    failure.get("arm") != launch["arm"] or
                    Path(failure.get("destination", "")).resolve() !=
                    source.resolve() or
                    failure.get("destination_exists") != source.exists()):
                raise RuntimeError("prelaunch failure/raw identity mismatch")
            failures[arm] = archive.digest(expected_failure)
            if not source.exists():
                absent_raw.append(arm)
            elif source.is_dir() and not any(source.iterdir()):
                empty_raw.append(arm)
            elif not source.is_dir():
                raise RuntimeError("failed arm raw path is not a directory")
        if number < len(summary) and row.get("audit_passed") is not True:
            raise RuntimeError("Round90 summary continues after failed arm")
    actual_failures = {path.name for path in CAMPAIGN.glob("runner_failure_*.json")}
    expected_failures = {f"runner_failure_{row['number']:02d}.json"
                         for row in summary if row.get("completion") is None}
    if actual_failures != expected_failures:
        raise RuntimeError("orphan Round90 failure receipt")
    return dict(attempted_arms=list(arms[:len(summary)]),
                not_run_arms=list(arms[len(summary):]),
                absent_raw_attempts=absent_raw,
                empty_raw_attempts=empty_raw,
                stage_status=stage_status,
                source_receipt_sha256=hashes,
                failure_receipt_sha256=failures)


def partition(entries: list[dict]) -> list[list[dict]]:
    """Use the R88 36 MiB raw cap; isolate a larger single source file."""
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
        if current and used + size > archive.RAW_PART_LIMIT:
            chunks.append(current)
            current, used = [], 0
        current.append(entry)
        used += size
    if current:
        chunks.append(current)
    return chunks


def inventory() -> dict:
    started = time.perf_counter()
    require_stopped()
    if not RAW.is_dir() or RAW.is_symlink() or RAW.is_junction():
        raise RuntimeError("missing or linked Round90 raw root")
    arms = expected_arms()
    attempts = finalized_attempts(arms)
    actual = {path.name for path in RAW.iterdir()}
    present = set(attempts["attempted_arms"]) - set(
        attempts["absent_raw_attempts"])
    if actual != present:
        raise RuntimeError("Round90 raw root has orphan or missing attempted arm")
    groups = []
    seen: set[str] = set()
    for arm in attempts["attempted_arms"]:
        if arm in attempts["absent_raw_attempts"] or arm in attempts["empty_raw_attempts"]:
            continue
        entries = archive.file_entries(RAW / arm)
        chunks = partition(entries)
        for part, chunk in enumerate(chunks, 1):
            suffix = "" if len(chunks) == 1 else ".part%02d-of-%02d" % (
                part, len(chunks))
            for entry in chunk:
                if entry["path"] in seen:
                    raise RuntimeError("duplicate source member")
                seen.add(entry["path"])
            groups.append(dict(
                source_group=arm, part_number=part,
                part_count=len(chunks),
                archive=archive.relative(
                    OUTPUT / (arm + suffix + ".tar.gz")),
                source_file_count=len(chunk),
                source_bytes=sum(item["size"] for item in chunk),
                files=chunk))
    return dict(
        kind="round90_lp_g_runner_raw",
        member_root="results/unified_exact_round90",
        preregistration_sha256=archive.digest(PREREG),
        attempt_evidence=attempts,
        raw_part_limit_bytes=archive.RAW_PART_LIMIT,
        archive_limit_bytes=archive.ARCHIVE_LIMIT,
        source_group_count=len(present) - len(attempts["empty_raw_attempts"]),
        source_file_count=len(seen),
        source_bytes=sum(group["source_bytes"] for group in groups),
        archive_count=len(groups),
        inventory_wall_seconds=time.perf_counter() - started,
        groups=groups)


def make_plan() -> None:
    if PLAN.exists() or INDEX.exists() or OUTPUT.exists():
        raise RuntimeError("Round90 raw archive output already exists")
    planned = inventory()
    archive.write_exclusive(PLAN, planned)
    print("planned Round90 raw", planned["source_file_count"], "files",
          planned["source_bytes"], "bytes", planned["archive_count"],
          "archives", flush=True)


def build() -> None:
    if INDEX.exists() or OUTPUT.exists():
        raise RuntimeError("Round90 raw archive output already exists")
    with PLAN.open("r", encoding="utf-8") as stream:
        planned = json.load(stream)
    fresh = inventory()
    for key in ("kind", "member_root", "preregistration_sha256",
                "attempt_evidence", "source_group_count",
                "source_file_count", "source_bytes", "archive_count"):
        if fresh[key] != planned[key]:
            raise RuntimeError("Round90 archive identity/inventory drift: " + key)
    if fresh["groups"] != planned["groups"]:
        raise RuntimeError("Round90 raw source path/size inventory drift")
    if shutil.disk_usage(RESULTS).free < planned["source_bytes"]:
        raise RuntimeError("insufficient free disk for bounded archive build")
    started = time.perf_counter()
    completed = []
    try:
        for number, group in enumerate(planned["groups"], 1):
            records, hash_seconds = archive.source_hashes(group)
            target = RESULTS / group["archive"]
            if target.exists():
                raise RuntimeError("archive target already exists")
            compress_seconds = archive.create_archive(target, records)
            size = target.stat().st_size
            if size >= archive.ARCHIVE_LIMIT:
                raise RuntimeError("archive exceeds 45 MiB target")
            digest_started = time.perf_counter()
            archive_sha = archive.digest(target)
            archive_hash_seconds = time.perf_counter() - digest_started
            verify_seconds, verified_bytes = archive.verify_archive(
                target, records)
            if verified_bytes != group["source_bytes"]:
                raise RuntimeError("stream verified byte count differs")
            completed.append(dict(
                source_group=group["source_group"],
                part_number=group["part_number"],
                part_count=group["part_count"],
                archive=group["archive"],
                archive_size=size, archive_sha256=archive_sha,
                source_file_count=len(records),
                source_bytes=verified_bytes,
                verified_file_count=len(records),
                verified_bytes=verified_bytes,
                stream_verification="all_member_sha256_size_equal_source",
                source_hash_wall_seconds=hash_seconds,
                compression_wall_seconds=compress_seconds,
                archive_hash_wall_seconds=archive_hash_seconds,
                archive_verify_wall_seconds=verify_seconds,
                files=records))
            print("verified Round90 raw", number, "/",
                  len(planned["groups"]), group["archive"],
                  "files", len(records), "raw_bytes", verified_bytes,
                  "archive_bytes", size, flush=True)
        result = dict(
            kind=planned["kind"], member_root=planned["member_root"],
            preregistration_sha256=planned["preregistration_sha256"],
            attempt_evidence=planned["attempt_evidence"],
            source_group_count=planned["source_group_count"],
            source_file_count=planned["source_file_count"],
            source_bytes=planned["source_bytes"],
            archive_count=len(completed),
            archive_bytes=sum(item["archive_size"] for item in completed),
            archive_limit_bytes=archive.ARCHIVE_LIMIT,
            build_wall_seconds_before_index_write=time.perf_counter()-started,
            groups=completed)
        archive.write_exclusive(INDEX, result)
        print("complete Round90 raw", result["source_file_count"],
              "files", result["archive_count"], "archives", flush=True)
    except Exception as error:
        if not FAILURE.exists():
            archive.write_exclusive(FAILURE, dict(
                error=repr(error), completed_archives=len(completed),
                elapsed_seconds=time.perf_counter()-started))
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "build"))
    args = parser.parse_args()
    if args.mode == "plan":
        make_plan()
    else:
        build()


if __name__ == "__main__":
    main()
