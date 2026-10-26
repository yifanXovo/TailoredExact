"""Conditional Round92 handling-activation G3 runner. Importing this module never starts work.

The Round92 qualification gate and a distinct root-issued lease for each stage
are mandatory. No command in this file is authorized by its mere existence.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import round70_affinity as affinity
import round86_native_evidence as evidence
import round88_a1_g3 as audited_runner_utilities
import round92_handling_row_evidence as row_evidence
from round75_startup import normalize, route_hash
from round83_audit_v2 import audit as replay_exchange


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "results/unified_exact_round92"
PREREG = STAGE / "preregistration_g3.json"
CAMPAIGN = STAGE / "runner_handling_g3"
R88_PREREG = ROOT / "results/unified_exact_round88/preregistration_a1_g3.json"
INPUT_AUDIT = ROOT / "results/unified_exact_round88/input_identity_audit.json"
read = audited_runner_utilities.read
sha = audited_runner_utilities.sha
write_new = audited_runner_utilities.write_new
append_jsonl = audited_runner_utilities.append_jsonl
atomic_status = audited_runner_utilities.atomic_status
memory_available = audited_runner_utilities.memory_available
bound_preview = audited_runner_utilities.bound_preview


def harness_hashes() -> dict[str, str]:
    files = {
        "runner": Path(__file__),
        "candidate_row_evidence": Path(row_evidence.__file__),
        "native_evidence_reader": Path(evidence.__file__),
        "physical_reader": Path(evidence.physical_module.__file__),
        "exchange_reader": ROOT / "scripts/round83_audit_v2.py",
        "affinity": ROOT / "scripts/round70_affinity.py",
        "normalizer": ROOT / "scripts/round75_startup.py",
        "audited_runner_utilities": ROOT / "scripts/round88_a1_g3.py",
        "input_identity_audit": INPUT_AUDIT,
    }
    return {name: sha(path) for name, path in files.items()}


def panel_and_identity(prereg: dict) -> dict:
    assert os.name == "nt", "Windows-only study"
    assert prereg["schema"] == "round92-handling-g3-preregistration-v1"
    assert prereg["status"] == "conditional_source_only_no_execution"
    assert prereg["planned_runs"] == 16 and len(prereg["panel"]) == 8
    assert prereg["maximum_process_wall_seconds"] == 12480
    assert prereg["no_component_time_or_work_slices"] is True
    assert prereg["performance_data_only_after_qualification_gate_and_stage_lease"] is True
    assert [row["id"] for row in prereg["panel"]] == [
        "E8", "S12", "D3", "C2", "D7", "U6", "F5", "F6"]
    assert [row["cap_seconds"] for row in prereg["panel"]] == [
        120, 120, 600, 600, 1200, 1200, 1200, 1200]
    assert [row["method_order"] for row in prereg["panel"]] == [
        ["ENS-C", "H-ACT"], ["H-ACT", "ENS-C"],
        ["ENS-C", "H-ACT"], ["H-ACT", "ENS-C"],
        ["ENS-C", "H-ACT"], ["H-ACT", "ENS-C"],
        ["ENS-C", "H-ACT"], ["H-ACT", "ENS-C"]]
    assert prereg["execution_order"] == [
        f'{row["id"]}/{arm}' for row in prereg["panel"] for arm in row["method_order"]]
    assert prereg["stages"] == [
        dict(name="smoke", ids=["E8", "S12"], planned_arms=4,
             requires_explicit_lease=True),
        dict(name="rest", ids=["D3", "C2", "D7", "U6", "F5", "F6"],
             planned_arms=12, requires_smoke_audit_and_new_lease=True)]
    common = prereg["common"]
    for key, value in dict(threads=1, mip_threads=1, gurobi_seed=0,
                           gurobi_presolve=-1, affinity_mask=4,
                           requested_mip_gap=0, requested_mip_gap_abs=0,
                           shutdown_margin_seconds=3, native_limit_offset_seconds=6,
                           hard_stop_offset_seconds=2).items():
        assert common[key] == value, key
    assert common["gurobi_version"] == "13.0.2"
    assert prereg["runtime_root"] == "results/unified_exact_round92/runner_handling_g3"
    assert prereg["qualification_gate_path"] == "results/unified_exact_round92/g3_qualification_gate.json"
    assert prereg["candidate_binary"] == "build/research/round92-handling-activation/ExactEBRP.exe"
    assert prereg["candidate_binary_sha256_provisional"] == (
        "767d2cbfa50f332a8b9cd6fa3f01888509509b11c2444100d7cafd63bc204b9b")
    assert prereg["candidate_core_sha256_provisional"] == (
        "29cb167a388e1a76bd544131bf59684be3950f92f13ecdb755525644f596de12")
    assert prereg["source_commit_provisional"] == "a0e35a221c770f71ef19c405edf9af73e43d93d7"
    assert prereg["g1_v2_admission_sha256"] == (
        "e6434dbb6dd18645b9626a954291ec9ed917341369b990a9d0c81133c841c624")
    r88 = read(R88_PREREG)
    old = {row["id"]: row for row in r88["panel"]}
    historical_p = prereg["historical_round88_p_timing"]
    assert historical_p["comparison_status"] == "historical_unpaired_not_a_round92_timed_arm"
    assert historical_p["round88_preregistration"] == str(R88_PREREG.relative_to(ROOT)).replace("\\", "/")
    assert historical_p["round88_binary_sha256"] == r88["candidate_binary_sha256"]
    assert set(historical_p["raw_receipts_by_role"]) == {row["id"] for row in prereg["panel"]}
    input_audit = read(INPUT_AUDIT)
    assert input_audit["all_hashes_match"] and input_audit["role_count"] == 19
    audited = {row["id"]: row for row in input_audit["roles"]}
    for row in prereg["panel"]:
        predecessor = old[row["id"]]
        for key in ("scenario_id", "input_path", "input_sha256", "T_seconds",
                    "pickup_seconds", "drop_seconds", "lambda", "cap_seconds"):
            assert row[key] == predecessor[key], (row["id"], key)
        assert row["historical_p_canonical_ancestry"]["source_round"] == predecessor["reference"]["source_round"]
        assert row["historical_p_canonical_ancestry"]["canonical_sha256"] == predecessor["reference"]["canonical_sha256"]
        p_number = r88["execution_order"].index(f'{row["id"]}/P-GRB') + 1
        receipt = historical_p["raw_receipts_by_role"][row["id"]]
        assert receipt["path"] == (
            f'results/unified_exact_round88/runner_a1_g3/raw/'
            f'{p_number:02d}_{row["id"]}_P-GRB')
        assert sha(ROOT / receipt["path"] / "launch.json") == receipt["launch_sha256"]
        assert sha(ROOT / receipt["path"] / "audit.json") == receipt["audit_sha256"]
        assert audited[row["id"]]["passed"]
        assert audited[row["id"]]["actual_sha256"] == row["input_sha256"]
        assert sha(ROOT / row["input_path"]) == row["input_sha256"]
    return input_audit


def qualification_gate(prereg: dict) -> dict:
    """This external gate is created only by root after qualification review."""
    gate = read(ROOT / prereg["qualification_gate_path"])
    assert gate["schema"] == "round92-handling-g3-qualification-gate-v1"
    assert gate["authorized_by"] == "root" and gate["qualified"] is True
    assert gate["allow_prepare"] is True and gate["allow_optimize"] is True
    assert gate["prereg_sha256"] == sha(PREREG)
    assert gate["runner_sha256"] == sha(Path(__file__))
    assert gate["source_commit"] == prereg["source_commit_provisional"]
    assert gate["candidate_binary_sha256"] == prereg["candidate_binary_sha256_provisional"]
    assert sha(ROOT / prereg["candidate_binary"]) == gate["candidate_binary_sha256"]
    assert gate["candidate_core_sha256"] == prereg["candidate_core_sha256_provisional"]
    assert sha(ROOT / "build/research/round92-handling-activation/libexact_ebrp_core.a") == gate["candidate_core_sha256"]
    assert sha(ROOT / prereg["g1_v2_admission_path"]) == prereg["g1_v2_admission_sha256"]
    assert gate["qualification_receipt_sha256"] == sha(ROOT / gate["qualification_receipt_path"])
    assert gate["independent_review_sha256"] == sha(ROOT / gate["independent_review_path"])
    assert gate["independent_review_path"] == (
        "results/unified_exact_round92/g1_v2_independent_evidence_review.md")
    assert len(gate["source_hashes"]) == 15
    assert len({row["path"] for row in gate["source_hashes"]}) == 15
    admitted = read(ROOT / prereg["g1_v2_admission_path"])
    assert gate["source_hashes"] == admitted["source_hashes"]
    for row in gate["source_hashes"]:
        assert sha(ROOT / row["path"]) == row["sha256"], row["path"]
    assert gate["harness_hashes"] == harness_hashes()
    return gate


def command_for(prereg: dict, item: dict, arm: str, destination: Path) -> list[str]:
    cap, common = item["cap_seconds"], prereg["common"]
    command = [
        str((ROOT / prereg["candidate_binary"]).resolve()),
        "--input", item["input_path"], "--lambda", str(item["lambda"]),
        "--T", str(item["T_seconds"]), "--pickup-time", str(item["pickup_seconds"]),
        "--drop-time", str(item["drop_seconds"]),
        "--time-limit", str(cap - common["native_limit_offset_seconds"]),
        "--process-wall-time-limit", str(cap),
        "--process-shutdown-margin", str(common["shutdown_margin_seconds"]),
        "--threads", "1", "--mip-threads", "1", "--gurobi-seed", "0",
        "--gurobi-presolve", "-1", "--method", "gcap-frontier",
        "--algorithm-preset", "research-round83-vds-equal-net-exchange",
        "--round92-handling-activation", "true" if arm == "H-ACT" else "false",
        "--round60-candidate-mode", "off", "--round61-candidate-mode", "off",
        "--round62-threshold-mode", "off", "--round65-witness-audit", "true",
        "--round65-hga-zero-stop", "true",
        "--out", str(destination / "result.json"),
        "--log", str(destination / "native.log"),
        "--process-phase-ledger", str(destination / "phases.csv"),
        "--external-gini-artifact-dir", str(destination / "external"),
        "--primal-heuristic-generation-log", str(destination / "hga.csv"),
        "--progress-log", str(destination / "progress.csv"),
        "--native-evidence-dir", str(destination / "journal"),
    ]
    assert "--round88-constructive-only-descent" not in command
    assert "--round89-native-ot-b1" not in command
    assert "--round90-lp-g-split" not in command
    return command


def launches_for(prereg: dict) -> list[dict]:
    launches = []
    for item in prereg["panel"]:
        for arm in item["method_order"]:
            number = len(launches) + 1
            destination = CAMPAIGN / "raw" / f'{number:02d}_{item["id"]}_{arm}'
            launches.append(dict(
                number=number, id=item["id"], arm=arm,
                stage="smoke" if number <= 4 else "rest",
                panel=dict(item, instance_path=item["input_path"]),
                destination=str(destination), cap_seconds=item["cap_seconds"],
                hard_stop_seconds=item["cap_seconds"] - prereg["common"]["hard_stop_offset_seconds"],
                command=command_for(prereg, item, arm, destination)))
    assert len(launches) == 16
    assert sum(row["cap_seconds"] for row in launches) == 12480
    return launches


def prepare() -> None:
    prereg = read(PREREG)
    panel_and_identity(prereg)
    gate = qualification_gate(prereg)
    assert not CAMPAIGN.exists(), "No overwrite, restart or splicing"
    launches = launches_for(prereg)
    CAMPAIGN.mkdir(parents=True)
    identity = dict(
        schema="round92-handling-g3-identity-v1", prereg_sha256=sha(PREREG),
        runner_sha256=sha(Path(__file__)), gate_sha256=sha(ROOT / prereg["qualification_gate_path"]),
        candidate_binary_sha256=gate["candidate_binary_sha256"],
        source_commit=gate["source_commit"], source_hashes=gate["source_hashes"],
        harness_hashes=gate["harness_hashes"], launches=launches,
        prepared_unix=time.time(), optimizer_calls=0)
    write_new(CAMPAIGN / "identity.json", identity)
    write_new(CAMPAIGN / "preflight.json", dict(
        schema="round92-handling-g3-preflight-v1", optimizer_calls=0,
        planned_runs=16, smoke_runs=4, process_cap_sum_seconds=12480,
        binary_hash_verified=True, source_hashes_verified=True,
        inputs_verified=8, harness_hashes_verified=True,
        memory_available_bytes=memory_available(), disk_free_bytes=shutil.disk_usage(CAMPAIGN).free,
        note="No model export or Optimize. Stage-specific leases still required."))
    print(json.dumps(dict(prepared=True, campaign=str(CAMPAIGN), optimizer_calls=0)), flush=True)


def foreign_heavy_processes() -> list[dict]:
    expression = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "($_.Name -match '^(ExactEBRP|Round[0-9]+.*Experiment|"
        "gurobi_cl|cmake|ninja|g\\+\\+|cc1plus|cl|link|ld|MSBuild)\\.exe$') "
        "-or ($_.Name -match '^python(w)?\\.exe$' -and $_.CommandLine -match "
        "'round88[_-]ot|round89[_-]ot|ot[_-]diagnostic|ot[_-]closure') } "
        "| Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    )
    raw = subprocess.check_output(
        ["powershell.exe", "-NoProfile", "-Command", expression],
        text=True, timeout=30).strip()
    if not raw:
        return []
    payload = json.loads(raw)
    return payload if isinstance(payload, list) else [payload]


def require_stage_lease(stage: str, identity: dict) -> None:
    lease = read(CAMPAIGN / f"runner_{stage}_lease.json")
    assert lease == dict(schema="round92-handling-g3-stage-lease-v1", stage=stage,
                         identity_sha256=sha(CAMPAIGN / "identity.json"),
                         authorized_by="root", allow_optimize=True)


def handling_row_evidence(launch: dict, result: dict | None, reason: str) -> dict:
    try:
        return row_evidence.audit(Path(launch["destination"]), launch["arm"],
                                  result, reason, sha, read)
    except Exception as exc:
        if reason == "normal_return":
            raise
        path = Path(launch["destination"]) / "external" / "round92_handling_activation_rows.csv"
        return dict(status="partial_unknown_after_interruption", issue=repr(exc),
                    raw_ledger=str(path), raw_ledger_sha256=sha(path) if path.is_file() else None,
                    model_generations=None, rows_total_across_generations=None)


def audit_launch(launch: dict, observations: list[dict], completion: dict,
                 identity: dict) -> dict:
    destination = Path(launch["destination"])
    reason = completion["stop_reason"]
    result_path = destination / "result.json"
    result = read(result_path) if reason == "normal_return" and result_path.is_file() else None
    if reason == "normal_return":
        assert result is not None, "normal exit without result.json"
        expected = ("research-round92-ensc-rounded-handling-activation" if launch["arm"] == "H-ACT"
                    else "research-round83-vds-equal-net-exchange")
        assert result["algorithm_preset"] == expected
    audited = evidence.audit(ROOT, launch["panel"], observations,
                             identity["candidate_binary_sha256"])
    evidence.finalize_endpoint(ROOT, launch["panel"], launch["arm"], audited,
                               observations, result, reason, {})
    audited["handling_row_evidence"] = handling_row_evidence(launch, result, reason)
    if result is not None:
        folder = destination / "hga.csv.exchange"
        if folder.is_dir():
            initial = normalize(read(folder / "initial.json"))
            audited["neutral_exchange"] = replay_exchange(launch["panel"], folder, initial)
            assert not read(folder / "result.json")["verification_failed"]
            final = normalize(read(folder / "final.json"))
            startup = [row["payload"] for row in observations
                       if row["payload"]["kind"] == "witness" and row["payload"]["call"] == 0]
            assert len(startup) == 1
            handed = normalize(startup[0])
            assert route_hash(handed) in {route_hash(initial), route_hash(final)}
            audited["outer_handoff"] = dict(
                initial_match=route_hash(handed) == route_hash(initial),
                final_match=route_hash(handed) == route_hash(final))
        else:
            assert not result.get("external_gini_tree_root_coverage_valid")
    audited["passed"] = True
    return audited


def severe_risk_signal(records: list[dict], role: str) -> list[dict]:
    pair = {row["arm"]: row for row in records if row["id"] == role}
    assert set(pair) == {"ENS-C", "H-ACT"}
    reference, candidate = pair["ENS-C"], pair["H-ACT"]
    ref_end, cand_end = reference["endpoint"], candidate["endpoint"]
    assert ref_end is not None and cand_end is not None
    ref_time = reference["completion"]["process_wall_seconds"]
    cand_time = candidate["completion"]["process_wall_seconds"]
    small = role in {"E8", "S12"} and cand_end["certificate"] and ref_end["certificate"] and max(cand_time, ref_time) < 60
    excess_ratio, excess_seconds = (0.5, 5) if small else (0.5, 30)
    found = []
    if (cand_end["certificate"] and ref_end["certificate"] and
            cand_time > ref_time * (1 + excess_ratio) and
            cand_time - ref_time > excess_seconds):
        found.append(dict(kind="severe_certification_time_signal", role=role,
                          candidate_seconds=cand_time, reference_seconds=ref_time))
    elif (ref_end["certificate"] and not cand_end["certificate"] and
          cand_time > ref_time * (1 + excess_ratio) and
          cand_time - ref_time > excess_seconds):
        found.append(dict(kind="certificate_loss_with_severe_censoring_lower_bound", role=role,
                          candidate_observed_seconds=cand_time, reference_certified_seconds=ref_time))
    elif not cand_end["certificate"] and not ref_end["certificate"]:
        cand_gap, ref_gap = cand_end["gap"], ref_end["gap"]
        if (cand_gap is not None and ref_gap is not None and cand_gap > ref_gap * 1.5
                and cand_gap - ref_gap > 0.01):
            found.append(dict(kind="severe_open_gap_signal", role=role,
                              candidate_gap=cand_gap, reference_gap=ref_gap,
                              candidate_U=cand_end["U"], candidate_L=cand_end["L"],
                              reference_U=ref_end["U"], reference_L=ref_end["L"]))
    return found


def cross_arm_contradiction(records: list[dict], role: str) -> None:
    pair = {row["arm"]: row for row in records if row["id"] == role}
    assert set(pair) == {"ENS-C", "H-ACT"}
    arms, lowers, uppers = [], [], []
    for arm in ("ENS-C", "H-ACT"):
        row = pair[arm]
        audit = read(Path(row["destination"]) / "audit.json")
        assert audit["passed"]
        bound = max(audit["LB"], row["endpoint"]["L"])
        physical = [w["F"] for w in audit["witnesses"]]
        final = audit.get("final_physical_verification")
        if final is not None:
            physical.append(final["F"])
        upper = min(physical) if physical else None
        lowers.append(bound)
        if upper is not None:
            uppers.append(upper)
        arms.append(dict(arm=arm, strongest_same_arm_global_L=bound,
                         minimum_same_arm_physical_U=upper,
                         physically_verified_witness_rows=len(audit["witnesses"])))
    strongest = max(lowers)
    weakest_upper = min(uppers) if uppers else None
    passed = weakest_upper is None or strongest <= weakest_upper + 1e-7
    write_new(CAMPAIGN / f"runner_cross_arm_{role}.json", dict(
        schema="round92-handling-g3-cross-arm-v1", id=role, arms=arms,
        strongest_global_L=strongest, minimum_physical_U=weakest_upper,
        tolerance=1e-7, passed=passed,
        scope="Offline original-problem contradiction only, not a merged endpoint"))
    assert passed, f"Original-problem cross-arm contradiction on {role}"


def run_one(launch: dict, prereg: dict, identity: dict) -> dict:
    admission_started = time.monotonic()
    competing = foreign_heavy_processes()
    assert not competing, f"Other solver/build/heavy process active: {competing}"
    free = shutil.disk_usage(CAMPAIGN).free
    available = memory_available()
    assert free >= 10 * 1024**3 and available >= 2 * 1024**3, "Resource admission failed"
    destination = Path(launch["destination"])
    destination.mkdir(parents=True, exist_ok=False)
    prelaunch_seconds = time.monotonic() - admission_started
    write_new(destination / "launch.json", dict(
        launch, prelaunch_seconds=prelaunch_seconds,
        prereg_sha256=identity["prereg_sha256"], runner_sha256=identity["runner_sha256"]))
    append_jsonl(CAMPAIGN / "processes.jsonl", dict(
        number=launch["number"], id=launch["id"], arm=launch["arm"],
        destination=str(destination), started_unix=time.time()))
    environment = dict(os.environ)
    environment["PATH"] = "D:/msys64/ucrt64/bin;D:/gurobi1302/win64/bin;" + environment.get("PATH", "")
    observations: list[dict] = []
    next_event = 1
    reason = "normal_return"
    child = None
    last_sample = -60.0
    low_memory_checks = 0
    started = time.monotonic()
    write_new(destination / "process_start_marker.json", dict(
        monotonic_seconds=started, unix_seconds=time.time(),
        scope="Wrapper before affinity and child creation; not certificate time"))
    with affinity.inherited_core(prereg["common"]["affinity_mask"]) as binding:
        try:
            with (destination / "stdout.log").open("x") as stdout, (destination / "stderr.log").open("x") as stderr:
                child = subprocess.Popen(launch["command"], cwd=ROOT, env=environment,
                                         stdout=stdout, stderr=stderr)
                mask = affinity.read_masks(child.pid)
                assert mask["process_mask"] == prereg["common"]["affinity_mask"]
                write_new(destination / "affinity.json", dict(parent=binding, child=mask, pid=child.pid))
                while True:
                    for _ in range(256):
                        path = destination / "journal" / f"event_{next_event}.commit"
                        if not path.exists():
                            break
                        try:
                            row = evidence.receipt(path, 0, launch["cap_seconds"])
                        except (AssertionError, FileNotFoundError, UnicodeError, ValueError):
                            break
                        observed = time.monotonic() - started
                        if observed > launch["cap_seconds"]:
                            break
                        row["first_observed_seconds"] = observed
                        row["effective_available_seconds"] = max(observed, row["data_close_seconds"])
                        observations.append(row)
                        next_event += 1
                    elapsed = time.monotonic() - started
                    if child.poll() is not None:
                        break
                    if elapsed >= launch["hard_stop_seconds"]:
                        reason = "whole_run_hard_stop"
                        child.kill()
                        break
                    if elapsed - last_sample >= 60:
                        upper, lower = bound_preview(observations)
                        available = memory_available()
                        free = shutil.disk_usage(CAMPAIGN).free
                        low_memory_checks = low_memory_checks + 1 if available < 2 * 1024**3 else 0
                        sample = dict(number=launch["number"], id=launch["id"], arm=launch["arm"],
                                      process_seconds=elapsed, observed_events=len(observations),
                                      provisional_U=upper, provisional_L=lower,
                                      provisional_gap=upper - lower if upper is not None else None,
                                      available_memory_bytes=available, free_disk_bytes=free,
                                      sampled_unix=time.time(), formal_endpoint=False)
                        append_jsonl(destination / "samples.jsonl", sample)
                        atomic_status(CAMPAIGN / "runtime_status.json", sample)
                        last_sample = elapsed
                        if free < 5 * 1024**3:
                            reason = "host_disk_safety_stop"
                            child.kill()
                            break
                        if low_memory_checks >= 2:
                            reason = "host_memory_safety_stop"
                            child.kill()
                            break
                    time.sleep(0.05)
                child.wait(timeout=max(2.0, launch["cap_seconds"] - (time.monotonic() - started)))
                exit_observed_seconds = time.monotonic() - started
                while True:
                    path = destination / "journal" / f"event_{next_event}.commit"
                    if not path.exists():
                        break
                    row = evidence.receipt(path, 0, launch["cap_seconds"])
                    observed = time.monotonic() - started
                    if observed > launch["cap_seconds"]:
                        break
                    row["first_observed_seconds"] = observed
                    row["effective_available_seconds"] = max(observed, row["data_close_seconds"])
                    observations.append(row)
                    next_event += 1
        finally:
            if child is not None and child.poll() is None:
                child.kill()
                child.wait(timeout=5)
    wrapper_wall = time.monotonic() - started
    if reason == "normal_return" and child.returncode != 0:
        reason = "abnormal_process_exit"
    completion = dict(schema="round92-handling-g3-completion-v1",
                      number=launch["number"], id=launch["id"], arm=launch["arm"],
                      returncode=child.returncode, process_wall_seconds=exit_observed_seconds,
                      prelaunch_seconds=prelaunch_seconds,
                      end_to_end_seconds=prelaunch_seconds + exit_observed_seconds,
                      wrapper_wall_seconds=wrapper_wall,
                      fully_observed_end_to_end_seconds=prelaunch_seconds + wrapper_wall,
                      postexit_drain_and_restore_seconds=wrapper_wall - exit_observed_seconds,
                      process_cap_seconds=launch["cap_seconds"],
                      within_cap=exit_observed_seconds <= launch["cap_seconds"],
                      stop_reason=reason, committed_events=len(observations), ended_unix=time.time())
    write_new(destination / "completion.json", completion)
    write_new(destination / "observations.json", observations)
    audit_started = time.perf_counter()
    try:
        assert completion["within_cap"]
        assert affinity.read_masks() == binding["before"]
        assert reason in {"normal_return", "whole_run_hard_stop",
                          "host_disk_safety_stop", "host_memory_safety_stop"}
        audited = audit_launch(launch, observations, completion, identity)
    except Exception as exc:
        audited = dict(passed=False, error=repr(exc), status="requires_independent_review",
                       certificate=False, endpoint=None)
    audited["offline_audit_seconds"] = time.perf_counter() - audit_started
    write_new(destination / "audit.json", audited)
    record = dict(number=launch["number"], id=launch["id"], arm=launch["arm"],
                  destination=str(destination), completion=completion,
                  full_attempt_wall_seconds=time.monotonic() - admission_started,
                  offline_audit_seconds=audited["offline_audit_seconds"],
                  audit_passed=audited["passed"], endpoint=audited.get("endpoint"),
                  handling_evidence=audited.get("handling_row_evidence"),
                  audit_error=audited.get("error"))
    append_jsonl(CAMPAIGN / "summary.jsonl", record)
    print(json.dumps(dict(completed=record), ensure_ascii=False), flush=True)
    if not audited["passed"]:
        raise RuntimeError("Audit failed; retain evidence and stop before next arm")
    if reason in {"host_disk_safety_stop", "host_memory_safety_stop"}:
        raise RuntimeError("Resource safety stop; no next arm")
    return record


def run_stage(stage: str) -> None:
    stage_started = time.monotonic()
    prereg = read(PREREG)
    panel_and_identity(prereg)
    gate = qualification_gate(prereg)
    identity = read(CAMPAIGN / "identity.json")
    assert identity["schema"] == "round92-handling-g3-identity-v1"
    assert identity["prereg_sha256"] == sha(PREREG)
    assert identity["runner_sha256"] == sha(Path(__file__))
    assert identity["gate_sha256"] == sha(ROOT / prereg["qualification_gate_path"])
    assert identity["candidate_binary_sha256"] == gate["candidate_binary_sha256"]
    assert identity["source_hashes"] == gate["source_hashes"]
    assert identity["harness_hashes"] == harness_hashes()
    assert identity["launches"] == launches_for(prereg)
    require_stage_lease(stage, identity)
    assert not (CAMPAIGN / "active_run.lock").exists()
    summary_path = CAMPAIGN / "summary.jsonl"
    existing = [json.loads(line) for line in summary_path.read_text(encoding="utf-8").splitlines()] \
        if summary_path.exists() else []
    before = 0 if stage == "smoke" else 4
    assert len(existing) == before, "Never rerun, skip or splice"
    assert all(row["number"] == index and row["audit_passed"]
               for index, row in enumerate(existing, 1))
    if stage == "rest":
        assert read(CAMPAIGN / "runner_smoke_gate.json") == dict(
            schema="round92-handling-g3-smoke-gate-v1", smoke_runs=4,
            summary_sha256=sha(summary_path), authorized_by="root", accepted=True)
    launches = [row for row in identity["launches"] if row["stage"] == stage]
    assert len(launches) == (4 if stage == "smoke" else 12)
    with (CAMPAIGN / "active_run.lock").open("x", encoding="utf-8") as lock:
        lock.write(json.dumps(dict(stage=stage, pid=os.getpid(), started_unix=time.time())) + "\n")
    stage_records, stage_error = [], None
    try:
        for launch in launches:
            attempt_started = time.monotonic()
            try:
                stage_records.append(run_one(launch, prereg, identity))
            except Exception as exc:
                recorded = [json.loads(line) for line in summary_path.read_text(encoding="utf-8").splitlines()] \
                    if summary_path.exists() else []
                if not recorded or recorded[-1]["number"] != launch["number"]:
                    destination = Path(launch["destination"])
                    marker = destination / "process_start_marker.json"
                    elapsed = time.monotonic() - attempt_started
                    process_lower = (time.monotonic() - read(marker)["monotonic_seconds"]) \
                        if marker.exists() else None
                    failure = dict(schema="round92-handling-g3-failure-v1",
                                   number=launch["number"], id=launch["id"], arm=launch["arm"],
                                   error=repr(exc), destination=str(destination),
                                   destination_exists=destination.exists(),
                                   total_attempt_elapsed_seconds=elapsed,
                                   process_wrapper_elapsed_lower_bound_seconds=process_lower,
                                   endpoint=None, certificate=False,
                                   needs_independent_review=True, recorded_unix=time.time())
                    path = CAMPAIGN / f'runner_failure_{launch["number"]:02d}.json'
                    write_new(path, failure)
                    append_jsonl(summary_path, dict(number=launch["number"], id=launch["id"],
                                                    arm=launch["arm"], destination=str(destination),
                                                    completion=None, audit_passed=False,
                                                    endpoint=None, audit_error=repr(exc),
                                                    failure_record=str(path)))
                raise
            if launch["arm"] == launch["panel"]["method_order"][-1]:
                all_records = existing + stage_records
                cross_arm_contradiction(all_records, launch["id"])
                signals = severe_risk_signal(all_records, launch["id"])
                if signals:
                    write_new(CAMPAIGN / f"runner_{stage}_risk_stop.json", dict(
                        role=launch["id"], signals=signals, research_signal_only=True,
                        requires_paired_review=True, summary_sha256=sha(summary_path)))
                    raise RuntimeError("Severe paired signal; pause next role for root review")
        if stage == "smoke":
            candidate = [row for row in stage_records if row["arm"] == "H-ACT"]
            assert len(candidate) == 2
            total_rows = sum(row["handling_evidence"]["rows_total_across_generations"]
                             for row in candidate if row["handling_evidence"]["status"] ==
                             "complete_model_generation_evidence")
            assert total_rows > 0, "R92 added-row construction unexposed in smoke; do not admit rest"
    except Exception as exc:
        stage_error = repr(exc)
        raise
    finally:
        (CAMPAIGN / "active_run.lock").unlink(missing_ok=True)
        stage_summary = [json.loads(line) for line in summary_path.read_text(encoding="utf-8").splitlines()][before:] \
            if summary_path.exists() else []
        observed = sum(row["completion"]["process_wall_seconds"]
                       for row in stage_summary if row["completion"] is not None)
        failures = sum(read(path)["total_attempt_elapsed_seconds"]
                       for path in CAMPAIGN.glob("runner_failure_*.json"))
        write_new(CAMPAIGN / f"runner_{stage}_completion.json", dict(
            stage=stage, completed=len(stage_summary), planned=len(launches),
            full_runner_stage_wall_seconds=time.monotonic() - stage_started,
            all_audits_passed=len(stage_summary) == len(launches) and
                all(row["audit_passed"] for row in stage_summary),
            stop_reason=stage_error, process_wall_seconds=observed,
            failed_attempt_elapsed_lower_bound_seconds=failures,
            process_wall_total_if_any_failed="unknown" if failures else observed,
            ended_unix=time.time()))


def main() -> None:
    assert len(sys.argv) == 2 and sys.argv[1] in {"prepare", "run-smoke", "run-rest"}, \
        "Usage: round92_handling_g3.py prepare|run-smoke|run-rest"
    if sys.argv[1] == "prepare":
        prepare()
    else:
        run_stage(sys.argv[1].removeprefix("run-"))


if __name__ == "__main__":
    main()
