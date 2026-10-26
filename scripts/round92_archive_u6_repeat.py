"""Archive the four paid Round92 U6 seed-1/2 repeat arms.

Plan, check and build require separate root admission and an idle compute slot.
The frozen Round88 kernel supplies hashing, tar creation and stream verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

import round88_archive_evidence as archive


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/unified_exact_round92"
CAMPAIGN = RESULTS / "runner_u6_repeat"
PREREG = RESULTS / "preregistration_u6_repeat.json"
PLAN = RESULTS / "runner_u6_repeat_raw_plan.json"
CHECK = RESULTS / "runner_u6_repeat_raw_check.json"
INDEX = RESULTS / "runner_u6_repeat_raw_index.json"
FAILURE = RESULTS / "runner_u6_repeat_raw_failure.json"
OUTPUT = RESULTS / "runner_u6_repeat_raw_archives"
KERNEL_SHA256 = "d357b232ceb8e14e94cbf9629d57d9f18bc2f60b1b682865042c4cdd622319f0"
archive.RESULTS = RESULTS


def read(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def require_stopped() -> None:
    if (CAMPAIGN / "active_run.lock").exists():
        raise RuntimeError("Round92 U6 repeat runner lock still active")
    expression = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "($_.Name -match '^(ExactEBRP|gurobi_cl|cmake|ninja|g\\+\\+|cc1plus|cl|link|ld|MSBuild)\\.exe$') "
        "-or ($_.Name -match '^python(w)?\\.exe$' -and $_.CommandLine -match "
        "'round92_handling_u6_repeat\\.py|round92_handling_g3\\.py|round92_.*diagnostic|round90_lp_g_.*\\.py|round88[_-]ot') } "
        "| Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    )
    output = subprocess.check_output(
        ["powershell.exe", "-NoProfile", "-Command", expression],
        text=True, timeout=15).strip()
    if output and json.loads(output):
        raise RuntimeError("solver, build or diagnostic process still active")


def finalized_attempts() -> tuple[list[dict], dict]:
    prereg = read(PREREG)
    order = prereg.get("repeat_order")
    if (prereg.get("schema") != "round92-handling-u6-repeat-preregistration-v1" or
            prereg.get("runtime_root") != CAMPAIGN.relative_to(ROOT).as_posix() or
            prereg.get("planned_arms") != 4 or
            order != [{"seed": 1, "method_order": ["ENS-C", "H-ACT"]},
                      {"seed": 2, "method_order": ["H-ACT", "ENS-C"]}]):
        raise RuntimeError("U6 repeat preregistration/order changed")
    for path_key, sha_key in (
            ("frozen_g3_runner", "frozen_g3_runner_sha256"),
            ("frozen_g3_preregistration", "frozen_g3_preregistration_sha256"),
            ("frozen_g3_qualification_gate", "frozen_g3_qualification_gate_sha256")):
        if archive.digest(ROOT / prereg[path_key]) != prereg[sha_key]:
            raise RuntimeError("frozen G3 prerequisite changed: " + path_key)
    identity_path = CAMPAIGN / "identity.json"
    identity = read(identity_path)
    launches = identity.get("launches")
    if (identity.get("schema") != "round92-handling-u6-repeat-identity-v1" or
            identity.get("prereg_sha256") != archive.digest(PREREG) or
            identity.get("wrapper_sha256") != archive.digest(
                ROOT / "scripts/round92_handling_u6_repeat.py") or
            identity.get("runner_sha256") != archive.digest(
                ROOT / "scripts/round92_handling_g3.py") or
            identity.get("gate_sha256") != archive.digest(
                RESULTS / "u6_repeat_prepare_gate.json") or
            identity.get("candidate_binary_sha256") !=
            prereg.get("candidate_binary_sha256") or
            identity.get("candidate_core_sha256") !=
            prereg.get("candidate_core_sha256") or
            identity.get("source_commit") != prereg.get("source_commit") or
            not isinstance(identity.get("source_hashes"), list) or
            not isinstance(identity.get("harness_hashes"), dict) or
            not isinstance(launches, list) or len(launches) != 4):
        raise RuntimeError("prepared U6 repeat identity changed")
    lease = read(CAMPAIGN / "runner_u6_repeat_lease.json")
    if lease != dict(schema="round92-handling-u6-repeat-run-lease-v1",
                     identity_sha256=archive.digest(identity_path),
                     authorized_by="root", allow_optimize=True, planned_arms=4):
        raise RuntimeError("U6 repeat lease changed")
    completion = read(CAMPAIGN / "run_completion.json")
    postflight = read(CAMPAIGN / "postflight.json")
    if (completion.get("schema") != "round92-handling-u6-repeat-run-completion-v1" or
            completion.get("planned") != 4 or completion.get("completed") != 4 or
            completion.get("error") is not None or
            completion.get("failed_attempt_costs") != [] or
            completion.get("postflight_passed") is not True or
            postflight.get("schema") != "round92-handling-u6-repeat-postflight-v1" or
            postflight.get("passed") is not True or
            postflight.get("source_hashes_match") is not True or
            postflight.get("main_matches") is not True or
            postflight.get("core_matches") is not True or
            postflight.get("no_residual_heavy_processes") is not True or
            postflight.get("main_sha256") != identity["candidate_binary_sha256"] or
            postflight.get("core_sha256") != identity["candidate_core_sha256"]):
        raise RuntimeError("four-arm completion/postflight invalid")
    outer = read(RESULTS / "u6_repeat_run_outer_001.receipt.json")
    if (outer.get("schema") != "round92-u6-repeat-run-outer-receipt-v1" or
            outer.get("child_exit_code") != 0 or outer.get("failure") is not None or
            outer.get("argv") != ["D:/msys64/ucrt64/bin/python.exe", "-B",
                                  "scripts/round92_handling_u6_repeat.py", "run"]):
        raise RuntimeError("repeat outer command receipt invalid")
    summary_path = CAMPAIGN / "summary.jsonl"
    with summary_path.open("r", encoding="utf-8") as stream:
        summary = [json.loads(line) for line in stream if line.strip()]
    if len(summary) != 4:
        raise RuntimeError("four paid top records absent")
    # The runner signs the raw global summary prefix after each completed pair,
    # preserving its original line endings; local seed summaries have no top
    # seed/native-readback wrapper and are deliberately not the hash target.
    global_lines = summary_path.read_bytes().splitlines(keepends=True)
    if len(global_lines) != 4 or any(not line.endswith(b"\n") for line in global_lines):
        raise RuntimeError("four complete raw global summary lines absent")
    three = read(CAMPAIGN / "three_seed_summary.json")
    if (three.get("schema") != "round92-handling-u6-repeat-three-seed-summary-v1" or
            set(three.get("pairs_by_seed", {})) != {"0", "1", "2"}):
        raise RuntimeError("seed-0 reference or three-seed verdict absent")
    if {p.name for p in CAMPAIGN.iterdir() if p.is_dir()} != {"seed_1", "seed_2"}:
        raise RuntimeError("unexpected seed directory")
    sources = []
    receipt_paths = [PREREG, identity_path, summary_path,
        CAMPAIGN / "runner_u6_repeat_lease.json", CAMPAIGN / "run_completion.json",
        CAMPAIGN / "postflight.json", CAMPAIGN / "three_seed_summary.json",
        RESULTS / "u6_repeat_run_outer_001.receipt.json",
        RESULTS / "u6_repeat_prepare_gate.json"]
    for seed in (1, 2):
        seed_dir = CAMPAIGN / f"seed_{seed}"
        raw_root = seed_dir / "raw"
        if (not raw_root.is_dir() or raw_root.is_symlink() or raw_root.is_junction()):
            raise RuntimeError("seed raw root missing or linked")
        arm_order = order[seed - 1]["method_order"]
        expected_names = {f"{local:02d}_U6_{arm}"
                          for local, arm in enumerate(arm_order, 1)}
        if {x.name for x in raw_root.iterdir()} != expected_names:
            raise RuntimeError("missing/orphan seed raw directory")
        seed_path = seed_dir / "summary.jsonl"
        with seed_path.open("r", encoding="utf-8") as stream:
            seed_rows = [json.loads(line) for line in stream if line.strip()]
        if len(seed_rows) != 2:
            raise RuntimeError("seed-local summary is not a pair")
        risk = read(seed_dir / "runner_repeat_risk_signal.json")
        if (risk.get("seed") != seed or risk.get("research_signal_only") is not True or
                risk.get("summary_sha256") != hashlib.sha256(
                    b"".join(global_lines[:2 * seed])).hexdigest()):
            raise RuntimeError("seed-local risk receipt invalid")
        cross = read(seed_dir / "runner_cross_arm_U6.json")
        if (cross.get("id") != "U6" or cross.get("passed") is not True or
                {x.get("arm") for x in cross.get("arms", [])} != {"ENS-C", "H-ACT"}):
            raise RuntimeError("seed-local original-problem cross-arm check failed")
        receipt_paths += [seed_path, seed_dir / "runner_repeat_risk_signal.json",
                          seed_dir / "runner_cross_arm_U6.json",
                          seed_dir / "processes.jsonl", seed_dir / "runtime_status.json"]
        for local, arm in enumerate(arm_order, 1):
            number = (seed - 1) * 2 + local
            launch, top, seed_item = launches[number - 1], summary[number - 1], seed_rows[local - 1]
            source = raw_root / f"{local:02d}_U6_{arm}"
            if (not source.is_dir() or source.is_symlink() or source.is_junction() or
                    launch.get("number") != number or launch.get("seed") != seed or
                    launch.get("id") != "U6" or launch.get("arm") != arm or
                    Path(launch.get("destination", "")).resolve() != source.resolve() or
                    top.get("record") != dict(seed_item, seed=seed) or
                    top.get("seed") != seed):
                raise RuntimeError("seed/global launch or summary identity mismatch")
            record = top.get("record")
            native = top.get("native_parameter_evidence")
            if (not isinstance(record, dict) or not isinstance(native, dict) or
                    record.get("number") != number or record.get("seed") != seed or
                    record.get("id") != "U6" or record.get("arm") != arm or
                    Path(record.get("destination", "")).resolve() != source.resolve() or
                    record.get("audit_passed") is not True or
                    native.get("status") != "native_result_seed_readback_verified" or
                    native.get("seed") != seed or
                    native.get("gurobi_seed_effective") != seed):
                raise RuntimeError("nested record/seed native identity mismatch")
            completion_row = read(source / "completion.json")
            audit = read(source / "audit.json")
            result = read(source / "result.json")
            handling = record.get("handling_evidence")
            if (record.get("completion") != completion_row or
                    completion_row.get("number") != number or
                    completion_row.get("stop_reason") != "normal_return" or
                    completion_row.get("within_cap") is not True or
                    audit.get("passed") is not True or
                    record.get("endpoint") != audit.get("endpoint") or
                    handling != audit.get("handling_row_evidence") or
                    audit.get("binary_sha256") != identity["candidate_binary_sha256"] or
                    native.get("result_sha256") != archive.digest(source / "result.json") or
                    result.get("algorithm_preset") !=
                    ("research-round92-ensc-rounded-handling-activation" if arm == "H-ACT"
                     else "research-round83-vds-equal-net-exchange")):
                raise RuntimeError("raw completion/audit/native result mismatch")
            if arm == "ENS-C":
                if handling != {"status": "not_applicable_default_off", "model_generations": 0}:
                    raise RuntimeError("default-off row evidence mismatch")
            else:
                ledger = Path(handling.get("ledger_path", ""))
                latest = handling.get("latest_canonical_models", [])
                if (handling.get("status") != "complete_model_generation_evidence" or
                        handling.get("model_generations", 0) < 1 or
                        handling.get("rows_total_across_generations", 0) < 1 or
                        len(handling.get("historical_model_rows", [])) !=
                        handling.get("model_generations") or
                        not all(x.get("proof_version") == 2 and x.get("rows", 0) > 0 and
                                x.get("model_scope", "").endswith(
                                    "round92_static_rounded_handling_activation")
                                for x in handling.get("historical_model_rows", [])) or
                        not latest or
                        not all(x.get("current_bytes_verified") is True and
                                Path(x.get("canonical_path", "")).is_relative_to(source)
                                for x in latest) or
                        not ledger.is_relative_to(source) or
                        archive.digest(ledger) != handling.get("ledger_sha256")):
                    raise RuntimeError("v2 row identity incomplete")
            sources.append(dict(number=number, seed=seed, role="U6", arm=arm,
                                name=f"seed_{seed}_{local:02d}_U6_{arm}",
                                directory=source, certificate=record["endpoint"]["certificate"],
                                status=record["endpoint"]["status"]))
    return sources, dict(attempted=[f"seed{s['seed']}/{s['role']}/{s['arm']}" for s in sources],
        not_run=[], seed0_reference="runner_handling_g3/raw/11_U6_H-ACT and 12_U6_ENS-C (not duplicated)",
        certifications={f"seed{s['seed']}/{s['arm']}": s["certificate"] for s in sources},
        source_receipt_sha256={archive.relative(p): archive.digest(p) for p in receipt_paths})


def inventory() -> dict:
    started = time.perf_counter()
    require_stopped()
    if archive.digest(ROOT / "scripts/round88_archive_evidence.py") != KERNEL_SHA256:
        raise RuntimeError("frozen Round88 archive kernel changed")
    sources, attempts = finalized_attempts()
    groups = []
    seen = set()
    for source in sources:
        entries = archive.file_entries(source["directory"])
        # A single large source may compress below 45 MiB; verification remains
        # strict and fails closed if its actual package exceeds that bound.
        chunks, current, used = [], [], 0
        for entry in entries:
            if current and used + entry["size"] > archive.RAW_PART_LIMIT:
                chunks.append(current)
                current, used = [], 0
            current.append(entry)
            used += entry["size"]
        if current:
            chunks.append(current)
        name = source["name"]
        for part, chunk in enumerate(chunks, 1):
            suffix = "" if len(chunks) == 1 else f".part{part:02d}-of-{len(chunks):02d}"
            for entry in chunk:
                if entry["path"] in seen:
                    raise RuntimeError("duplicate source member")
                seen.add(entry["path"])
            groups.append(dict(source_group=name, part_number=part,
                               part_count=len(chunks),
                               archive=archive.relative(OUTPUT / (name + suffix + ".tar.gz")),
                               source_file_count=len(chunk),
                               source_bytes=sum(e["size"] for e in chunk),
                               files=chunk))
    return dict(kind="round92_u6_seed_repeat_raw",
                member_root="results/unified_exact_round92",
                adapter_sha256=archive.digest(Path(__file__)),
                frozen_kernel_sha256=KERNEL_SHA256,
                preregistration_sha256=archive.digest(PREREG),
                attempt_evidence=attempts,
                raw_part_limit_bytes=archive.RAW_PART_LIMIT,
                archive_limit_bytes=archive.ARCHIVE_LIMIT,
                source_group_count=len(sources), source_file_count=len(seen),
                source_bytes=sum(g["source_bytes"] for g in groups),
                archive_count=len(groups), inventory_wall_seconds=time.perf_counter()-started,
                groups=groups)


def same_plan(a: dict, b: dict) -> None:
    for key in ("kind", "member_root", "adapter_sha256", "frozen_kernel_sha256",
                "preregistration_sha256", "attempt_evidence", "raw_part_limit_bytes",
                "archive_limit_bytes", "source_group_count", "source_file_count",
                "source_bytes", "archive_count", "groups"):
        if a[key] != b[key]:
            raise RuntimeError("raw archive inventory drift: " + key)


def plan() -> None:
    if any(x.exists() for x in (PLAN, CHECK, INDEX, OUTPUT)):
        raise RuntimeError("archive output already exists")
    data = inventory()
    archive.write_exclusive(PLAN, data)
    print("planned", data["source_file_count"], "files", data["archive_count"], "parts")


def check() -> None:
    if any(x.exists() for x in (CHECK, INDEX, OUTPUT)):
        raise RuntimeError("archive check or build already exists")
    old, new = read(PLAN), inventory()
    same_plan(old, new)
    archive.write_exclusive(CHECK, dict(schema="round92-u6-repeat-raw-check-v1",
        passed=True, plan_sha256=archive.digest(PLAN),
        adapter_sha256=new["adapter_sha256"], frozen_kernel_sha256=KERNEL_SHA256,
        source_group_count=new["source_group_count"],
        source_file_count=new["source_file_count"], source_bytes=new["source_bytes"],
        archive_count=new["archive_count"],
        reinspection_wall_seconds=new["inventory_wall_seconds"],
        attempted=new["attempt_evidence"]["attempted"],
        not_run=new["attempt_evidence"]["not_run"]))
    print("checked", new["source_file_count"], "files")


def build() -> None:
    if INDEX.exists() or OUTPUT.exists():
        raise RuntimeError("archive output already exists")
    old, checked = read(PLAN), read(CHECK)
    if (checked.get("schema") != "round92-u6-repeat-raw-check-v1" or
            checked.get("passed") is not True or
            checked.get("plan_sha256") != archive.digest(PLAN) or
            checked.get("adapter_sha256") != archive.digest(Path(__file__)) or
            checked.get("frozen_kernel_sha256") != KERNEL_SHA256):
        raise RuntimeError("matching check receipt absent")
    fresh = inventory()
    same_plan(old, fresh)
    if shutil.disk_usage(RESULTS).free < old["source_bytes"]:
        raise RuntimeError("insufficient free disk")
    started = time.perf_counter()
    completed = []
    for group in old["groups"]:
        records, hash_seconds = archive.source_hashes(group)
        target = RESULTS / group["archive"]
        if target.exists():
            raise RuntimeError("archive target already exists")
        compress_seconds = archive.create_archive(target, records)
        size = target.stat().st_size
        if size >= archive.ARCHIVE_LIMIT:
            raise RuntimeError("archive exceeds strict 45 MiB limit")
        hash_start = time.perf_counter()
        package_sha = archive.digest(target)
        package_hash_seconds = time.perf_counter() - hash_start
        verify_seconds, verified_bytes = archive.verify_archive(target, records)
        if verified_bytes != group["source_bytes"]:
            raise RuntimeError("stream-verified size differs")
        completed.append(dict(source_group=group["source_group"],
            part_number=group["part_number"], part_count=group["part_count"],
            archive=group["archive"], archive_size=size, archive_sha256=package_sha,
            source_file_count=len(records), source_bytes=verified_bytes,
            verified_file_count=len(records), verified_bytes=verified_bytes,
            stream_verification="all_member_sha256_size_equal_source",
            source_hash_wall_seconds=hash_seconds, compression_wall_seconds=compress_seconds,
            archive_hash_wall_seconds=package_hash_seconds,
            archive_verify_wall_seconds=verify_seconds, files=records))
    archive.write_exclusive(INDEX, dict(kind=old["kind"], member_root=old["member_root"],
        adapter_sha256=old["adapter_sha256"], frozen_kernel_sha256=KERNEL_SHA256,
        preregistration_sha256=old["preregistration_sha256"],
        plan_sha256=archive.digest(PLAN), check_sha256=archive.digest(CHECK),
        attempt_evidence=old["attempt_evidence"],
        source_group_count=old["source_group_count"],
        source_file_count=old["source_file_count"], source_bytes=old["source_bytes"],
        archive_count=len(completed), archive_bytes=sum(x["archive_size"] for x in completed),
        archive_limit_bytes=archive.ARCHIVE_LIMIT,
        build_wall_seconds_before_index_write=time.perf_counter()-started,
        groups=completed))
    print("verified", len(completed), "packages", old["source_file_count"], "files")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "check", "build"))
    mode = parser.parse_args().mode
    started = time.perf_counter()
    try:
        {"plan": plan, "check": check, "build": build}[mode]()
    except Exception as exc:
        if not FAILURE.exists():
            archive.write_exclusive(FAILURE, dict(
                schema="round92-u6-repeat-raw-failure-v1", mode=mode,
                error=repr(exc), elapsed_seconds=time.perf_counter()-started,
                plan_exists=PLAN.exists(), check_exists=CHECK.exists(),
                index_exists=INDEX.exists(), output_exists=OUTPUT.exists()))
        raise


if __name__ == "__main__":
    main()
