"""Archive only the four completed Round90 C2 seed-repeat raw arms.

Modes are plan, check, build, each once and in that order. Raw remains in
place. The frozen Round88 kernel hashes every source member and verifies the
uncompressed archive stream member-by-member after each package is written.
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
CAMPAIGN = RESULTS / "runner_lp_g_c2_repeat"
PREREG = RESULTS / "preregistration_c2_repeat.json"
PLAN = RESULTS / "runner_lp_g_c2_repeat_raw_plan.json"
CHECK = RESULTS / "runner_lp_g_c2_repeat_raw_inventory_check.json"
INDEX = RESULTS / "runner_lp_g_c2_repeat_raw_index.json"
FAILURE = RESULTS / "runner_lp_g_c2_repeat_raw_archive_failure.json"
OUTPUT = RESULTS / "runner_lp_g_c2_repeat_raw_archives"
ARMS = ((1, 1, "ENS-C"), (1, 2, "LP-G"),
        (2, 1, "LP-G"), (2, 2, "ENS-C"))
archive.RESULTS = RESULTS  # Private import in this process; frozen source unchanged.


def read(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def raw_dir(seed: int, within_seed: int, method: str) -> Path:
    return CAMPAIGN / f"seed_{seed}" / "raw" / f"{within_seed:02d}_C2_{method}"


def require_stopped() -> None:
    if (CAMPAIGN / "active_run.lock").exists():
        raise RuntimeError("C2 repeat runner lock is still active")
    expression = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "($_.Name -match '^(ExactEBRP|Round[0-9]+.*Experiment|gurobi_cl|"
        "cmake|ninja|g\\+\\+|cc1plus|cl|link|ld|MSBuild)\\.exe$') "
        "-or ($_.Name -match '^python(w)?\\.exe$' -and "
        "$_.CommandLine -match 'round90_lp_g_c2_repeat\\.py|"
        "round90_lp_g_g3\\.py|round88[_-]ot|round90[_-]ot') } "
        "| Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    )
    output = subprocess.check_output(
        ["powershell.exe", "-NoProfile", "-Command", expression],
        text=True, timeout=15).strip()
    if output and json.loads(output):
        raise RuntimeError("solver/build/repeat runner process still active")


def completed_campaign() -> dict:
    prereg = read(PREREG)
    if (prereg.get("schema") != "round90-lp-g-c2-repeat-preregistration-v1"
            or prereg.get("planned_runs") != 4 or
            prereg.get("runtime_root") !=
            "results/unified_exact_round90/runner_lp_g_c2_repeat" or
            prereg.get("repeat_order") != [
                {"seed": 1, "method_order": ["ENS-C", "LP-G"]},
                {"seed": 2, "method_order": ["LP-G", "ENS-C"]}]):
        raise RuntimeError("C2 repeat preregistration mismatch")
    identity = read(CAMPAIGN / "identity.json")
    launches = identity.get("launches")
    if (identity.get("schema") != "round90-lp-g-c2-repeat-identity-v1"
            or identity.get("prereg_sha256") != archive.digest(PREREG)
            or identity.get("wrapper_sha256") != archive.digest(
                ROOT / "scripts/round90_lp_g_c2_repeat.py")
            or not isinstance(launches, list) or len(launches) != 4):
        raise RuntimeError("C2 repeat identity invalid")
    completion = read(CAMPAIGN / "run_completion.json")
    if (completion.get("schema") != "round90-lp-g-c2-repeat-run-completion-v1"
            or completion.get("planned") != 4 or completion.get("completed") != 4
            or completion.get("error") is not None
            or completion.get("failed_attempt_costs") != []):
        raise RuntimeError("C2 repeat whole run unfinished")
    if list(CAMPAIGN.glob("runner_failure_*.json")):
        raise RuntimeError("unexpected failed attempt in completed campaign")
    postflight = read(CAMPAIGN / "repeat_postflight.json")
    if (postflight.get("schema") != "round90-lp-g-c2-repeat-postflight-v1"
            or not postflight.get("matches_prepared_identity")
            or postflight.get("active_heavy_process_count") != 0
            or postflight.get("active_lock")
            or postflight.get("identity_sha256") != archive.digest(CAMPAIGN / "identity.json")
            or len(postflight.get("source_hashes", [])) != 7
            or any(not row.get("matches_identity") for row in postflight["source_hashes"])):
        raise RuntimeError("C2 repeat postflight identity/finish invalid")
    top = jsonl(CAMPAIGN / "summary.jsonl")
    if len(top) != 4:
        raise RuntimeError("C2 repeat top-level summary not exactly four")
    if {path.name for path in CAMPAIGN.iterdir() if path.is_dir()} != {
            "seed_1", "seed_2"}:
        raise RuntimeError("unexpected seed root")
    for seed in (1, 2):
        parent = CAMPAIGN / f"seed_{seed}"
        raw = parent / "raw"
        if (parent.is_symlink() or parent.is_junction() or
                not raw.is_dir() or raw.is_symlink() or raw.is_junction()):
            raise RuntimeError("missing/linked seed raw root")
        wanted = {f"{index:02d}_C2_{method}" for s, index, method in ARMS
                  if s == seed}
        if {path.name for path in raw.iterdir()} != wanted:
            raise RuntimeError("orphan/missing seed raw arm")
        own = jsonl(parent / "summary.jsonl")
        if len(own) != 2:
            raise RuntimeError("per-seed summary not exactly two")
        cross = read(parent / "runner_cross_arm_C2.json")
        if cross.get("passed") is not True:
            raise RuntimeError("per-seed cross-arm audit did not pass")
    source_groups = []
    for number, (seed, within_seed, method) in enumerate(ARMS, 1):
        source = raw_dir(seed, within_seed, method)
        launch = launches[number - 1]
        top_row = top[number - 1]
        own = jsonl(CAMPAIGN / f"seed_{seed}" / "summary.jsonl")[within_seed - 1]
        record = top_row.get("record")
        receipt = read(source / "launch.json")
        complete = read(source / "completion.json")
        audit = read(source / "audit.json")
        native = read(source / "native_parameter_evidence.json")
        if (not source.is_dir() or source.is_symlink() or source.is_junction()
                or launch.get("number") != number or launch.get("seed") != seed
                or launch.get("id") != "C2" or launch.get("arm") != method
                or Path(launch.get("destination", "")).resolve() != source.resolve()
                or not isinstance(record, dict) or record.get("number") != number
                or record.get("id") != "C2" or record.get("arm") != method
                or record.get("seed") != seed
                or Path(record.get("destination", "")).resolve() != source.resolve()
                or own.get("number") != number or own.get("arm") != method
                or own.get("destination") != str(source)
                or receipt.get("number") != number or receipt.get("seed") != seed
                or receipt.get("arm") != method
                or receipt.get("prereg_sha256") != identity["prereg_sha256"]
                or receipt.get("runner_sha256") != identity["runner_sha256"]
                or complete != record.get("completion")
                or complete != own.get("completion")
                or complete.get("returncode") != 0
                or complete.get("stop_reason") != "normal_return"
                or not complete.get("within_cap")
                or audit.get("passed") is not True
                or record.get("audit_passed") is not True
                or own.get("audit_passed") is not True
                or record.get("endpoint") != audit.get("endpoint")
                or own.get("endpoint") != audit.get("endpoint")
                or record["endpoint"].get("certificate") is not True
                or top_row.get("native_parameter_evidence") != native
                or native.get("status") != "native_result_readback_verified"
                or native.get("seed") != seed
                or native.get("gurobi_seed_effective") != seed
                or native.get("gurobi_threads_effective") != 1
                or native.get("gurobi_presolve_effective") != -1):
            raise RuntimeError("completed C2 arm identity/audit mismatch: " + str(source))
        entries = archive.file_entries(source)
        source_groups.append((f"seed_{seed}_{within_seed:02d}_C2_{method}", entries))
    return dict(
        campaign_identity_sha256=archive.digest(CAMPAIGN / "identity.json"),
        preregistration_sha256=archive.digest(PREREG),
        summary_sha256=archive.digest(CAMPAIGN / "summary.jsonl"),
        completion_sha256=archive.digest(CAMPAIGN / "run_completion.json"),
        postflight_sha256=archive.digest(CAMPAIGN / "repeat_postflight.json"),
        source_groups=source_groups)


def inventory() -> dict:
    started = time.perf_counter()
    require_stopped()
    completed = completed_campaign()
    groups = []
    seen: set[str] = set()
    for name, entries in completed["source_groups"]:
        chunks = archive.partition(entries)
        for part, chunk in enumerate(chunks, 1):
            suffix = "" if len(chunks) == 1 else f".part{part:02d}-of-{len(chunks):02d}"
            for entry in chunk:
                if entry["path"] in seen:
                    raise RuntimeError("duplicate source member")
                seen.add(entry["path"])
            groups.append(dict(
                source_group=name, part_number=part, part_count=len(chunks),
                archive=archive.relative(OUTPUT / (name + suffix + ".tar.gz")),
                source_file_count=len(chunk),
                source_bytes=sum(item["size"] for item in chunk), files=chunk))
    return dict(kind="round90_lp_g_c2_repeat_raw",
                member_root="results/unified_exact_round90",
                campaign_identity_sha256=completed["campaign_identity_sha256"],
                preregistration_sha256=completed["preregistration_sha256"],
                summary_sha256=completed["summary_sha256"],
                completion_sha256=completed["completion_sha256"],
                postflight_sha256=completed["postflight_sha256"],
                raw_part_limit_bytes=archive.RAW_PART_LIMIT,
                archive_limit_bytes=archive.ARCHIVE_LIMIT,
                source_group_count=4, source_file_count=len(seen),
                source_bytes=sum(group["source_bytes"] for group in groups),
                archive_count=len(groups),
                inventory_wall_seconds=time.perf_counter() - started,
                groups=groups)


def stable(plan: dict, current: dict) -> None:
    for key in ("kind", "member_root", "campaign_identity_sha256",
                "preregistration_sha256", "summary_sha256", "completion_sha256",
                "postflight_sha256", "raw_part_limit_bytes", "archive_limit_bytes",
                "source_group_count", "source_file_count", "source_bytes",
                "archive_count", "groups"):
        if plan[key] != current[key]:
            raise RuntimeError("source identity/inventory drift: " + key)


def make_plan() -> None:
    if PLAN.exists() or CHECK.exists() or INDEX.exists() or OUTPUT.exists():
        raise RuntimeError("C2 repeat raw archive output already exists")
    plan = inventory()
    archive.write_exclusive(PLAN, plan)
    print("planned C2 repeat", plan["source_file_count"], "files",
          plan["source_bytes"], "bytes", plan["archive_count"], "packages", flush=True)


def check_plan() -> None:
    if CHECK.exists() or INDEX.exists() or OUTPUT.exists():
        raise RuntimeError("C2 repeat raw inventory check already exists")
    plan = read(PLAN)
    started = time.perf_counter()
    fresh = inventory()
    stable(plan, fresh)
    archive.write_exclusive(CHECK, dict(
        schema="round90-lp-g-c2-repeat-raw-inventory-check-v1",
        plan_sha256=archive.digest(PLAN), identity_and_inventory_unchanged=True,
        source_file_count=fresh["source_file_count"],
        source_bytes=fresh["source_bytes"], archive_count=fresh["archive_count"],
        check_wall_seconds=time.perf_counter() - started))
    print("checked C2 repeat inventory", fresh["source_file_count"], flush=True)


def build() -> None:
    if INDEX.exists() or OUTPUT.exists():
        raise RuntimeError("C2 repeat raw archive output already exists")
    plan = read(PLAN)
    checked = read(CHECK)
    if (checked.get("schema") != "round90-lp-g-c2-repeat-raw-inventory-check-v1"
            or not checked.get("identity_and_inventory_unchanged")
            or checked.get("plan_sha256") != archive.digest(PLAN)):
        raise RuntimeError("missing or drifted inventory check")
    fresh = inventory()
    stable(plan, fresh)
    if shutil.disk_usage(RESULTS).free < plan["source_bytes"]:
        raise RuntimeError("insufficient disk for bounded archive build")
    started = time.perf_counter()
    completed = []
    try:
        for number, group in enumerate(plan["groups"], 1):
            records, hash_seconds = archive.source_hashes(group)
            target = RESULTS / group["archive"]
            if target.exists():
                raise RuntimeError("archive target already exists")
            compression_seconds = archive.create_archive(target, records)
            size = target.stat().st_size
            if size >= archive.ARCHIVE_LIMIT:
                raise RuntimeError("archive exceeds 45 MiB")
            hash_started = time.perf_counter()
            archive_sha = archive.digest(target)
            archive_hash_seconds = time.perf_counter() - hash_started
            verify_seconds, verified_bytes = archive.verify_archive(target, records)
            if verified_bytes != group["source_bytes"]:
                raise RuntimeError("stream-verified bytes differ")
            completed.append(dict(
                source_group=group["source_group"],
                part_number=group["part_number"], part_count=group["part_count"],
                archive=group["archive"], archive_size=size,
                archive_sha256=archive_sha, source_file_count=len(records),
                source_bytes=group["source_bytes"], verified_file_count=len(records),
                verified_bytes=verified_bytes,
                stream_verification="all_member_sha256_size_equal_source",
                source_hash_wall_seconds=hash_seconds,
                compression_wall_seconds=compression_seconds,
                archive_hash_wall_seconds=archive_hash_seconds,
                archive_verify_wall_seconds=verify_seconds,
                files=records))
            print("verified C2 repeat", number, "/", len(plan["groups"]),
                  group["archive"], len(records), "files", verified_bytes,
                  "raw bytes", size, "archive bytes", flush=True)
        archive.write_exclusive(INDEX, dict(
            kind=plan["kind"], member_root=plan["member_root"],
            plan_sha256=archive.digest(PLAN), check_sha256=archive.digest(CHECK),
            campaign_identity_sha256=plan["campaign_identity_sha256"],
            source_group_count=plan["source_group_count"],
            source_file_count=plan["source_file_count"],
            source_bytes=plan["source_bytes"], archive_count=len(completed),
            archive_bytes=sum(item["archive_size"] for item in completed),
            raw_part_limit_bytes=archive.RAW_PART_LIMIT,
            archive_limit_bytes=archive.ARCHIVE_LIMIT,
            build_wall_seconds_before_index_write=time.perf_counter() - started,
            groups=completed))
        print("complete C2 repeat archive", len(completed), "packages", flush=True)
    except Exception as error:
        if not FAILURE.exists():
            archive.write_exclusive(FAILURE, dict(
                error=repr(error), completed_archives=len(completed),
                elapsed_seconds=time.perf_counter() - started))
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "check", "build"))
    args = parser.parse_args()
    if args.mode == "plan":
        make_plan()
    elif args.mode == "check":
        check_plan()
    else:
        build()


if __name__ == "__main__":
    main()
