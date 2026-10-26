"""Lossless G4-priority raw archive adapter over the frozen Round88 kernel.

Run plan, check, build exactly once each after the solver slot is released.
Raw directories stay in place. Top-level receipts are staged separately.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import time

import round88_archive_evidence as archive


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/unified_exact_round90"
CAMPAIGN = RESULTS / "runner_lp_g_g4_priority"
PREREG = RESULTS / "preregistration_g4_priority.json"
PLAN = RESULTS / "runner_lp_g_g4_priority_raw_plan.json"
CHECK = RESULTS / "runner_lp_g_g4_priority_raw_check.json"
INDEX = RESULTS / "runner_lp_g_g4_priority_raw_index.json"
FAILURE = RESULTS / "runner_lp_g_g4_priority_raw_failure.json"
OUTPUT = RESULTS / "runner_lp_g_g4_priority_raw_archives"
KERNEL_SHA256 = "d357b232ceb8e14e94cbf9629d57d9f18bc2f60b1b682865042c4cdd622319f0"
archive.RESULTS = RESULTS


def read(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def require_stopped() -> None:
    if (CAMPAIGN / "active_run.lock").exists():
        raise RuntimeError("G4 priority runner lock still active")
    expression = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "($_.Name -match '^(ExactEBRP|Round[0-9]+.*Experiment|"
        "gurobi_cl|cmake|ninja|g\\+\\+|cc1plus|cl|link|ld|MSBuild)\\.exe$') "
        "-or ($_.Name -match '^python(w)?\\.exe$' -and $_.CommandLine -match "
        "'round90_lp_g_g4_priority\\.py|round90_lp_g_g3\\.py|"
        "round91_|round88[_-]ot|round89[_-]ot|ot[_-]diagnostic|ot[_-]closure') } "
        "| Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    )
    output = subprocess.check_output(
        ["powershell.exe", "-NoProfile", "-Command", expression],
        text=True, timeout=15).strip()
    if output and json.loads(output):
        raise RuntimeError("solver, build, diagnostic, or runner process still active")


def finalized_attempts() -> tuple[list[dict], dict]:
    prereg = read(PREREG)
    if (prereg.get("schema") != "round90-lp-g-g4-priority-preregistration-v1" or
            prereg.get("planned_runs") != 4 or
            prereg.get("execution_order") !=
            ["F2/ENS-C", "F2/LP-G", "D6/LP-G", "D6/ENS-C"] or
            prereg.get("runtime_root") != CAMPAIGN.relative_to(ROOT).as_posix()):
        raise RuntimeError("G4 priority preregistration identity invalid")
    identity_path = CAMPAIGN / "identity.json"
    identity = read(identity_path)
    launches = identity.get("launches")
    if (identity.get("schema") != "round90-lp-g-g4-priority-identity-v1" or
            identity.get("prereg_sha256") != archive.digest(PREREG) or
            identity.get("wrapper_sha256") != archive.digest(
                ROOT / "scripts/round90_lp_g_g4_priority.py") or
            identity.get("candidate_binary_sha256") !=
            prereg.get("candidate_binary_sha256") or
            not isinstance(launches, list) or len(launches) != 4):
        raise RuntimeError("G4 priority prepared identity invalid")
    lease_path = CAMPAIGN / prereg["run_lease_name"]
    lease = read(lease_path)
    if lease != dict(schema="round90-lp-g-g4-priority-run-lease-v1",
                     authorized_by="root", allow_optimize=True,
                     identity_sha256=archive.digest(identity_path), planned_runs=4,
                     execution_order=prereg["execution_order"]):
        raise RuntimeError("G4 priority root lease invalid")
    completed_path = CAMPAIGN / "run_completion.json"
    completed = read(completed_path)
    if (completed.get("schema") != "round90-lp-g-g4-priority-run-completion-v1" or
            completed.get("planned") != 4 or completed.get("completed") != 4 or
            completed.get("attempted") != [1, 2, 3, 4] or
            completed.get("not_run") != [] or completed.get("error") is not None or
            completed.get("failed_attempt_costs") != [] or
            completed.get("completed_process_receipts") != 4):
        raise RuntimeError("G4 priority batch not finalized as four paid arms")
    outer_path = CAMPAIGN / "priority_outer_001.receipt.json"
    outer = read(outer_path)
    if (outer.get("schema") != "round90-g4-priority-outer-receipt-v1" or
            outer.get("exit_code") != 0 or outer.get("exception") is not None or
            outer.get("command") !=
            "D:/msys64/ucrt64/bin/python.exe scripts/round90_lp_g_g4_priority.py run"):
        raise RuntimeError("G4 priority outer command receipt invalid")
    summary_path = CAMPAIGN / "summary.jsonl"
    with summary_path.open("r", encoding="utf-8") as stream:
        summary = [json.loads(line) for line in stream if line.strip()]
    if len(summary) != 4:
        raise RuntimeError("G4 priority summary lacks four arms")
    if list(CAMPAIGN.glob("runner_failure_*.json")) or list(
            CAMPAIGN.rglob("*risk_stop.json")):
        raise RuntimeError("unexpected G4 failure or severe-stop receipt")

    actual_roles = {path.name for path in CAMPAIGN.iterdir() if path.is_dir()}
    if actual_roles != {"F2", "D6"}:
        raise RuntimeError("unexpected role directory under G4 campaign")
    sources = []
    expected_by_role: dict[str, set[str]] = {"F2": set(), "D6": set()}
    for number, (launch, item) in enumerate(zip(launches, summary), 1):
        role, arm = prereg["execution_order"][number - 1].split("/")
        if (not isinstance(launch, dict) or launch.get("number") != number or
                launch.get("id") != role or launch.get("arm") != arm or
                launch.get("seed") != 0 or launch.get("cap_seconds") !=
                (600 if role == "F2" else 3600)):
            raise RuntimeError("global launch identity/order/cap mismatch")
        source = Path(launch.get("destination", ""))
        raw_root = CAMPAIGN / role / "raw"
        if (source.parent.resolve() != raw_root.resolve() or
                re.fullmatch(r"[0-9]{2}_" + re.escape(role) + "_" +
                             re.escape(arm), source.name) is None or
                not source.is_dir() or source.is_symlink() or source.is_junction()):
            raise RuntimeError("G4 destination is missing, linked, or outside role raw root")
        if source.name in expected_by_role[role]:
            raise RuntimeError("duplicate role raw directory")
        expected_by_role[role].add(source.name)
        record = item.get("record") if isinstance(item, dict) else None
        if (item.get("seed") != 0 or item.get("role") != role or
                not isinstance(record, dict) or record.get("number") != number or
                record.get("id") != role or record.get("arm") != arm or
                record.get("seed") != 0 or
                Path(record.get("destination", "")).resolve() != source.resolve() or
                item.get("native_parameter_evidence", {}).get("status") !=
                "native_result_readback_verified" or
                record.get("audit_passed") is not True):
            raise RuntimeError("G4 top summary/launch/readback mismatch")
        arm_completion = read(source / "completion.json")
        arm_audit = read(source / "audit.json")
        arm_result = read(source / "result.json")
        if (record.get("completion") != arm_completion or
                arm_completion.get("stop_reason") != "normal_return" or
                arm_completion.get("within_cap") is not True or
                arm_audit.get("passed") is not True or
                record.get("endpoint") != arm_audit.get("endpoint") or
                record.get("split_evidence") != arm_audit.get("lp_g_split_evidence") or
                arm_result.get("algorithm_preset") !=
                ("research-round90-ensc-lp-g-split" if arm == "LP-G"
                 else "research-round83-vds-equal-net-exchange")):
            raise RuntimeError("G4 completed raw/audit/algorithm identity mismatch")
        # A normal, audited graceful deadline is a valid paid observation.
        # It is not forced to be certified for archival.
        if not record["endpoint"].get("certificate") and not (
                arm_result.get("graceful_deadline_finalization") is True and
                "time_limit" in arm_result.get("status", "")):
            raise RuntimeError("uncertified arm lacks recognized deadline evidence")
        per_role_path = CAMPAIGN / role / "summary.jsonl"
        with per_role_path.open("r", encoding="utf-8") as stream:
            per_role = [json.loads(line) for line in stream if line.strip()]
        if not any(row.get("number") == number and row.get("id") == role and
                   row.get("arm") == arm and row.get("completion") == arm_completion and
                   row.get("endpoint") == arm_audit["endpoint"] for row in per_role):
            raise RuntimeError("G4 role summary/raw mismatch")
        sources.append(dict(number=number, role=role, arm=arm, directory=source,
                            certificate=record["endpoint"]["certificate"],
                            status=record["endpoint"]["status"]))
    for role, names in expected_by_role.items():
        raw_root = CAMPAIGN / role / "raw"
        if (not raw_root.is_dir() or raw_root.is_symlink() or raw_root.is_junction() or
                {path.name for path in raw_root.iterdir()} != names):
            raise RuntimeError("orphan or missing G4 raw directory: " + role)
    receipt_paths = {"identity": identity_path, "lease": lease_path,
                     "summary": summary_path, "run_completion": completed_path,
                     "outer_command": outer_path}
    for role in ("F2", "D6"):
        receipt_paths[role + "_summary"] = CAMPAIGN / role / "summary.jsonl"
        receipt_paths[role + "_cross_arm"] = CAMPAIGN / role / (
            "runner_cross_arm_" + role + ".json")
        if read(receipt_paths[role + "_cross_arm"]).get("passed") is not True:
            raise RuntimeError("G4 cross-arm contradiction receipt failed")
    return sources, dict(
        attempted=[f'{row["number"]}/{row["role"]}/{row["arm"]}' for row in sources],
        not_run=[], certifications={f'{row["role"]}/{row["arm"]}': row["certificate"]
                                for row in sources},
        source_receipt_sha256={key: archive.digest(path)
                               for key, path in receipt_paths.items()})


def partition(entries: list[dict]) -> list[list[dict]]:
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
    if archive.digest(ROOT / "scripts/round88_archive_evidence.py") != KERNEL_SHA256:
        raise RuntimeError("frozen Round88 archive kernel changed")
    sources, attempts = finalized_attempts()
    seen: set[str] = set()
    groups = []
    for source in sources:
        entries = archive.file_entries(source["directory"])
        chunks = partition(entries)
        name = f'{source["number"]:02d}_{source["role"]}_{source["arm"]}'
        for part, chunk in enumerate(chunks, 1):
            suffix = "" if len(chunks) == 1 else ".part%02d-of-%02d" % (
                part, len(chunks))
            for entry in chunk:
                if entry["path"] in seen:
                    raise RuntimeError("duplicate G4 source member")
                seen.add(entry["path"])
            groups.append(dict(source_group=name, part_number=part,
                               part_count=len(chunks),
                               archive=archive.relative(OUTPUT / (name + suffix + ".tar.gz")),
                               source_file_count=len(chunk),
                               source_bytes=sum(entry["size"] for entry in chunk),
                               files=chunk))
    return dict(kind="round90_lp_g_g4_priority_raw",
                member_root="results/unified_exact_round90",
                adapter_sha256=archive.digest(Path(__file__)),
                frozen_kernel_sha256=KERNEL_SHA256,
                preregistration_sha256=archive.digest(PREREG),
                attempt_evidence=attempts,
                raw_part_limit_bytes=archive.RAW_PART_LIMIT,
                archive_limit_bytes=archive.ARCHIVE_LIMIT,
                source_group_count=len(sources), source_file_count=len(seen),
                source_bytes=sum(group["source_bytes"] for group in groups),
                archive_count=len(groups),
                inventory_wall_seconds=time.perf_counter() - started,
                groups=groups)


def same_plan(planned: dict, fresh: dict) -> None:
    for key in ("kind", "member_root", "adapter_sha256", "frozen_kernel_sha256",
                "preregistration_sha256", "attempt_evidence", "raw_part_limit_bytes",
                "archive_limit_bytes", "source_group_count", "source_file_count",
                "source_bytes", "archive_count", "groups"):
        if planned[key] != fresh[key]:
            raise RuntimeError("G4 archive identity/inventory drift: " + key)


def make_plan() -> None:
    if PLAN.exists() or CHECK.exists() or INDEX.exists() or OUTPUT.exists():
        raise RuntimeError("G4 raw archive output already exists")
    planned = inventory()
    archive.write_exclusive(PLAN, planned)
    print("planned G4 raw", planned["source_file_count"], "files",
          planned["source_bytes"], "bytes", planned["archive_count"],
          "archives", flush=True)


def check_plan() -> None:
    if CHECK.exists() or INDEX.exists() or OUTPUT.exists():
        raise RuntimeError("G4 raw archive check/output already exists")
    planned = read(PLAN)
    fresh = inventory()
    same_plan(planned, fresh)
    archive.write_exclusive(CHECK, dict(
        schema="round90-g4-priority-raw-check-v1", passed=True,
        plan_sha256=archive.digest(PLAN),
        adapter_sha256=fresh["adapter_sha256"],
        frozen_kernel_sha256=KERNEL_SHA256,
        source_group_count=fresh["source_group_count"],
        source_file_count=fresh["source_file_count"],
        source_bytes=fresh["source_bytes"],
        archive_count=fresh["archive_count"],
        reinspection_wall_seconds=fresh["inventory_wall_seconds"],
        attempted=fresh["attempt_evidence"]["attempted"],
        not_run=fresh["attempt_evidence"]["not_run"]))
    print("checked G4 raw plan", fresh["source_file_count"], "files",
          fresh["archive_count"], "archives", flush=True)


def build() -> None:
    if INDEX.exists() or OUTPUT.exists():
        raise RuntimeError("G4 raw archive output already exists")
    planned = read(PLAN)
    checked = read(CHECK)
    if (checked.get("schema") != "round90-g4-priority-raw-check-v1" or
            checked.get("passed") is not True or
            checked.get("plan_sha256") != archive.digest(PLAN) or
            checked.get("adapter_sha256") != archive.digest(Path(__file__)) or
            checked.get("frozen_kernel_sha256") != KERNEL_SHA256):
        raise RuntimeError("G4 raw plan lacks matching check receipt")
    fresh = inventory()
    same_plan(planned, fresh)
    if shutil.disk_usage(RESULTS).free < planned["source_bytes"]:
        raise RuntimeError("insufficient free disk for bounded G4 archive build")
    started = time.perf_counter()
    completed = []
    for number, group in enumerate(planned["groups"], 1):
        records, hash_seconds = archive.source_hashes(group)
        target = RESULTS / group["archive"]
        if target.exists():
            raise RuntimeError("G4 archive target already exists")
        compress_seconds = archive.create_archive(target, records)
        size = target.stat().st_size
        if size >= archive.ARCHIVE_LIMIT:
            raise RuntimeError("G4 archive exceeds 45 MiB target")
        hash_started = time.perf_counter()
        package_sha = archive.digest(target)
        package_hash_seconds = time.perf_counter() - hash_started
        verify_seconds, verified_bytes = archive.verify_archive(target, records)
        if verified_bytes != group["source_bytes"]:
            raise RuntimeError("G4 streamed verified byte count differs")
        completed.append(dict(
            source_group=group["source_group"], part_number=group["part_number"],
            part_count=group["part_count"], archive=group["archive"],
            archive_size=size, archive_sha256=package_sha,
            source_file_count=len(records), source_bytes=verified_bytes,
            verified_file_count=len(records), verified_bytes=verified_bytes,
            stream_verification="all_member_sha256_size_equal_source",
            source_hash_wall_seconds=hash_seconds,
            compression_wall_seconds=compress_seconds,
            archive_hash_wall_seconds=package_hash_seconds,
            archive_verify_wall_seconds=verify_seconds, files=records))
        print("verified G4 raw", number, "/", len(planned["groups"]),
              group["archive"], "files", len(records),
              "raw_bytes", verified_bytes, "archive_bytes", size, flush=True)
    archive.write_exclusive(INDEX, dict(
        kind=planned["kind"], member_root=planned["member_root"],
        adapter_sha256=planned["adapter_sha256"],
        frozen_kernel_sha256=KERNEL_SHA256,
        preregistration_sha256=planned["preregistration_sha256"],
        plan_sha256=archive.digest(PLAN), check_sha256=archive.digest(CHECK),
        attempt_evidence=planned["attempt_evidence"],
        source_group_count=planned["source_group_count"],
        source_file_count=planned["source_file_count"],
        source_bytes=planned["source_bytes"], archive_count=len(completed),
        archive_bytes=sum(row["archive_size"] for row in completed),
        archive_limit_bytes=archive.ARCHIVE_LIMIT,
        build_wall_seconds_before_index_write=time.perf_counter() - started,
        groups=completed))
    print("complete G4 raw", planned["source_file_count"], "files",
          len(completed), "archives", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "check", "build"))
    mode = parser.parse_args().mode
    started = time.perf_counter()
    try:
        if mode == "plan":
            make_plan()
        elif mode == "check":
            check_plan()
        else:
            build()
    except Exception as exc:
        if not FAILURE.exists():
            archive.write_exclusive(FAILURE, dict(
                schema="round90-g4-priority-raw-failure-v1", mode=mode,
                error=repr(exc), elapsed_seconds=time.perf_counter() - started,
                plan_exists=PLAN.exists(), check_exists=CHECK.exists(),
                index_exists=INDEX.exists(), output_exists=OUTPUT.exists()))
        raise


if __name__ == "__main__":
    main()
