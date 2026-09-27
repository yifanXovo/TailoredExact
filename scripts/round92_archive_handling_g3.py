"""Archive the paid Round92 G3 prefix; never infer unrun arms from missing raw.

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
CAMPAIGN = RESULTS / "runner_handling_g3"
PREREG = RESULTS / "preregistration_g3.json"
PLAN = RESULTS / "runner_handling_g3_raw_plan.json"
CHECK = RESULTS / "runner_handling_g3_raw_check.json"
INDEX = RESULTS / "runner_handling_g3_raw_index.json"
FAILURE = RESULTS / "runner_handling_g3_raw_failure.json"
OUTPUT = RESULTS / "runner_handling_g3_raw_archives"
KERNEL_SHA256 = "d357b232ceb8e14e94cbf9629d57d9f18bc2f60b1b682865042c4cdd622319f0"
archive.RESULTS = RESULTS


def read(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def require_stopped() -> None:
    if (CAMPAIGN / "active_run.lock").exists():
        raise RuntimeError("Round92 G3 runner lock still active")
    expression = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "($_.Name -match '^(ExactEBRP|gurobi_cl|cmake|ninja|g\\+\\+|cc1plus|cl|link|ld|MSBuild)\\.exe$') "
        "-or ($_.Name -match '^python(w)?\\.exe$' -and $_.CommandLine -match "
        "'round92_handling_g3\\.py|round92_.*diagnostic|round90_lp_g_.*\\.py|round88[_-]ot') } "
        "| Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    )
    output = subprocess.check_output(
        ["powershell.exe", "-NoProfile", "-Command", expression],
        text=True, timeout=15).strip()
    if output and json.loads(output):
        raise RuntimeError("solver, build or diagnostic process still active")


def finalized_attempts() -> tuple[list[dict], dict]:
    prereg = read(PREREG)
    order = prereg.get("execution_order")
    expected = ["E8/ENS-C", "E8/H-ACT", "S12/H-ACT", "S12/ENS-C",
                "D3/ENS-C", "D3/H-ACT", "C2/H-ACT", "C2/ENS-C",
                "D7/ENS-C", "D7/H-ACT", "U6/H-ACT", "U6/ENS-C",
                "F5/ENS-C", "F5/H-ACT", "F6/H-ACT", "F6/ENS-C"]
    if (prereg.get("schema") != "round92-handling-g3-preregistration-v1" or
            prereg.get("planned_runs") != 16 or order != expected or
            prereg.get("runtime_root") != CAMPAIGN.relative_to(ROOT).as_posix() or
            [(s.get("name"), s.get("planned_arms")) for s in prereg.get("stages", [])]
            != [("smoke", 4), ("rest", 12)]):
        raise RuntimeError("Round92 preregistration/order changed")
    identity_path = CAMPAIGN / "identity.json"
    identity = read(identity_path)
    launches = identity.get("launches")
    if (identity.get("schema") != "round92-handling-g3-identity-v1" or
            identity.get("prereg_sha256") != archive.digest(PREREG) or
            identity.get("gate_sha256") != archive.digest(
                RESULTS / "g3_qualification_gate.json") or
            identity.get("runner_sha256") != archive.digest(
                ROOT / "scripts/round92_handling_g3.py") or
            identity.get("candidate_binary_sha256") !=
            prereg.get("candidate_binary_sha256_provisional") or
            not isinstance(identity.get("source_hashes"), list) or
            not isinstance(identity.get("harness_hashes"), dict) or
            not isinstance(launches, list) or len(launches) != 16):
        raise RuntimeError("prepared identity changed")
    for stage in ("smoke", "rest"):
        lease = read(CAMPAIGN / f"runner_{stage}_lease.json")
        if lease != dict(schema="round92-handling-g3-stage-lease-v1",
                         stage=stage, identity_sha256=archive.digest(identity_path),
                         authorized_by="root", allow_optimize=True):
            raise RuntimeError(stage + " stage lease changed")
    smoke = read(CAMPAIGN / "runner_smoke_completion.json")
    rest = read(CAMPAIGN / "runner_rest_completion.json")
    if (smoke.get("stage") != "smoke" or smoke.get("completed") != 4 or
            smoke.get("planned") != 4 or smoke.get("all_audits_passed") is not True or
            smoke.get("stop_reason") is not None or
            rest.get("stage") != "rest" or rest.get("completed") != 8 or
            rest.get("planned") != 12 or rest.get("failed_attempt_elapsed_lower_bound_seconds") != 0 or
            "Severe paired signal" not in str(rest.get("stop_reason"))):
        raise RuntimeError("paid prefix or legal research stop changed")
    gate = read(CAMPAIGN / "runner_smoke_gate.json")
    if (gate.get("schema") != "round92-handling-g3-smoke-gate-v1" or
            gate.get("smoke_runs") != 4 or gate.get("accepted") is not True or
            gate.get("authorized_by") != "root"):
        raise RuntimeError("smoke gate invalid")
    risk_path = CAMPAIGN / "runner_rest_risk_stop.json"
    risk = read(risk_path)
    if (risk.get("role") != "U6" or risk.get("research_signal_only") is not True or
            risk.get("requires_paired_review") is not True or
            len(risk.get("signals", [])) != 1 or
            risk["signals"][0].get("kind") != "severe_open_gap_signal"):
        raise RuntimeError("rest stop is not the admitted U6 research signal")
    for stage, exit_code in (("smoke", 0), ("rest", 1)):
        outer = read(RESULTS / f"g3_{stage}_outer_001.receipt.json")
        if (outer.get("schema") != f"round92-g3-{stage}-outer-receipt-v1" or
                outer.get("child_exit_code") != exit_code or
                outer.get("failure") is not None or
                outer.get("argv") != ["-B", "scripts/round92_handling_g3.py",
                                      "run-" + stage]):
            raise RuntimeError(stage + " external receipt invalid")
    summary_path = CAMPAIGN / "summary.jsonl"
    with summary_path.open("r", encoding="utf-8") as stream:
        summary = [json.loads(line) for line in stream if line.strip()]
    if (len(summary) != 12 or
            risk.get("summary_sha256") != archive.digest(summary_path)):
        raise RuntimeError("paid summary or risk-stop binding changed")
    # The gate binds the first four completed lines, already committed in 21273f691.
    with summary_path.open("rb") as stream:
        first_four = b"".join(stream.readline() for _ in range(4))
    if hashlib.sha256(first_four).hexdigest() != gate.get("summary_sha256"):
        raise RuntimeError("committed smoke prefix changed")
    if list(CAMPAIGN.glob("runner_failure_*.json")):
        raise RuntimeError("runner failure receipt exists")
    raw_root = CAMPAIGN / "raw"
    if (not raw_root.is_dir() or raw_root.is_symlink() or raw_root.is_junction()):
        raise RuntimeError("raw root missing or linked")
    actual = {p.name for p in raw_root.iterdir()}
    expected_raw = {f"{n:02d}_{order[n-1].replace('/', '_')}" for n in range(1, 13)}
    if actual != expected_raw:
        raise RuntimeError("missing, orphan, or unrun raw directory")
    sources = []
    for number in range(1, 13):
        role, arm = order[number - 1].split("/")
        launch, row = launches[number - 1], summary[number - 1]
        source = raw_root / f"{number:02d}_{role}_{arm}"
        if (not source.is_dir() or source.is_symlink() or source.is_junction()):
            raise RuntimeError("paid raw directory missing or linked")
        if (launch.get("number") != number or launch.get("id") != role or
                launch.get("arm") != arm or
                Path(launch.get("destination", "")).resolve() != source.resolve() or
                row.get("number") != number or row.get("id") != role or
                row.get("arm") != arm or
                Path(row.get("destination", "")).resolve() != source.resolve() or
                row.get("audit_passed") is not True):
            raise RuntimeError("launch/summary/raw identity mismatch")
        completion = read(source / "completion.json")
        audit = read(source / "audit.json")
        result = read(source / "result.json")
        handling = row.get("handling_evidence")
        if (row.get("completion") != completion or
                completion.get("number") != number or
                completion.get("stop_reason") != "normal_return" or
                completion.get("within_cap") is not True or
                audit.get("passed") is not True or
                row.get("endpoint") != audit.get("endpoint") or
                handling != audit.get("handling_row_evidence") or
                audit.get("binary_sha256") != identity["candidate_binary_sha256"] or
                not isinstance(result, dict) or
                result.get("algorithm_preset") !=
                ("research-round92-ensc-rounded-handling-activation"
                 if arm == "H-ACT" else "research-round83-vds-equal-net-exchange")):
            raise RuntimeError("completed raw or audit mismatch")
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
                    not all(x.get("model_scope", "").endswith(
                        "round92_static_rounded_handling_activation") and
                        x.get("rows", 0) > 0 and x.get("B", 0) >= 0 and
                        x.get("model_sha256") for x in
                        handling.get("historical_model_rows", [])) or
                    not all(x.get("proof_version") == 2 for x in
                            handling.get("historical_model_rows", [])) or
                    not all(x.get("current_bytes_verified") is True for x in
                            latest) or not latest or
                    not ledger.is_relative_to(source) or
                    not all(Path(x.get("canonical_path", "")).is_relative_to(source)
                            for x in latest) or
                    archive.digest(ledger) !=
                    handling.get("ledger_sha256")):
                raise RuntimeError("candidate v2 row identity is incomplete")
        sources.append(dict(number=number, role=role, arm=arm,
                            directory=source, certificate=row["endpoint"]["certificate"],
                            status=row["endpoint"]["status"]))
    for role in ("E8", "S12", "D3", "C2", "D7", "U6"):
        cross = read(CAMPAIGN / f"runner_cross_arm_{role}.json")
        if (cross.get("schema") != "round92-handling-g3-cross-arm-v1" or
                cross.get("id") != role or cross.get("passed") is not True or
                {x.get("arm") for x in cross.get("arms", [])} != {"ENS-C", "H-ACT"}):
            raise RuntimeError("physical cross-arm receipt invalid: " + role)
    receipt_paths = [PREREG, identity_path, summary_path, risk_path,
                     CAMPAIGN / "runner_smoke_completion.json",
                     CAMPAIGN / "runner_rest_completion.json",
                     CAMPAIGN / "runner_smoke_gate.json",
                     CAMPAIGN / "runner_smoke_lease.json",
                     CAMPAIGN / "runner_rest_lease.json"]
    receipt_paths += [CAMPAIGN / f"runner_cross_arm_{role}.json"
                      for role in ("E8", "S12", "D3", "C2", "D7", "U6")]
    receipt_paths += [RESULTS / f"g3_{stage}_outer_001.receipt.json"
                      for stage in ("smoke", "rest")]
    receipt_paths += [RESULTS / "g3_qualification_gate.json",
                      RESULTS / "g3_smoke_postflight_observation.json",
                      RESULTS / "g3_rest_postflight_receipt.json"]
    return sources, dict(
        attempted=order[:12], not_run=order[12:],
        stop="U6 severe_open_gap_signal; valid research stop; rest exit 1",
        certifications={f"{s['role']}/{s['arm']}": s["certificate"] for s in sources},
        source_receipt_sha256={archive.relative(p): archive.digest(p)
                               for p in receipt_paths})


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
        name = f'{source["number"]:02d}_{source["role"]}_{source["arm"]}'
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
    return dict(kind="round92_handling_g3_paid_prefix_raw",
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
    archive.write_exclusive(CHECK, dict(schema="round92-handling-g3-raw-check-v1",
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
    if (checked.get("schema") != "round92-handling-g3-raw-check-v1" or
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
                schema="round92-handling-g3-raw-failure-v1", mode=mode,
                error=repr(exc), elapsed_seconds=time.perf_counter()-started,
                plan_exists=PLAN.exists(), check_exists=CHECK.exists(),
                index_exists=INDEX.exists(), output_exists=OUTPUT.exists()))
        raise


if __name__ == "__main__":
    main()
