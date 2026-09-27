"""Finite F2/D6 G4 priority wrapper over the frozen Round90 G3 audit runner.

Import starts no work. ``prepare`` needs a root source gate and makes zero
Optimize calls. ``run`` needs a distinct root lease; it runs exactly four
complete seed-zero processes, without resume, retry, or component slicing.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "results/unified_exact_round90/preregistration_g4_priority.json"
CAMPAIGN = ROOT / "results/unified_exact_round90/runner_lp_g_g4_priority"


def frozen_runner():
    path = ROOT / "scripts/round90_lp_g_g3.py"
    spec = importlib.util.spec_from_file_location("round90_lp_g_g3_g4_priority_frozen", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.CAMPAIGN == ROOT / "results/unified_exact_round90/runner_lp_g_g3"
    return module


def pinned_file(r90, path: str, digest: str) -> None:
    assert r90.sha(ROOT / path) == digest, path


def validate(r90, prereg: dict) -> dict:
    assert os.name == "nt", "Windows-only study"
    assert prereg["schema"] == "round90-lp-g-g4-priority-preregistration-v1"
    assert prereg["status"] == "source_only_pending_independent_review_and_root_gates"
    assert prereg["runtime_root"] == CAMPAIGN.relative_to(ROOT).as_posix()
    assert prereg["planned_runs"] == 4 and prereg["sum_process_caps_seconds"] == 8400
    assert prereg["no_component_time_or_work_slices"] is True
    assert prereg["prepare_does_not_authorize_optimize"] is True
    assert prereg["run_requires_separate_root_lease"] is True
    assert prereg["execution_order"] == ["F2/ENS-C", "F2/LP-G", "D6/LP-G", "D6/ENS-C"]
    assert prereg["historical_p_timing"].startswith("R87 P-GRB observations")
    pinned_file(r90, prereg["frozen_g3_runner"], prereg["frozen_g3_runner_sha256"])
    pinned_file(r90, prereg["frozen_g3_preregistration"],
                prereg["frozen_g3_preregistration_sha256"])
    pinned_file(r90, prereg["frozen_g3_qualification_gate"],
                prereg["frozen_g3_qualification_gate_sha256"])
    g3 = r90.read(ROOT / prereg["frozen_g3_preregistration"])
    old_gate = r90.read(ROOT / prereg["frozen_g3_qualification_gate"])
    assert old_gate["qualified"] is True and old_gate["authorized_by"] == "root"
    assert old_gate["source_commit"] == prereg["source_commit"]
    assert old_gate["candidate_binary_sha256"] == prereg["candidate_binary_sha256"]
    assert old_gate["source_hashes"] == prereg["source_hashes"]
    assert old_gate["harness_hashes"] == prereg["harness_hashes"] == r90.harness_hashes()
    assert len(prereg["source_hashes"]) == 7
    assert len({row["path"] for row in prereg["source_hashes"]}) == 7
    for row in prereg["source_hashes"]:
        pinned_file(r90, row["path"], row["sha256"])
    assert prereg["candidate_binary"] == g3["candidate_binary"]
    pinned_file(r90, prereg["candidate_binary"], prereg["candidate_binary_sha256"])
    assert prereg["common"] == {key: g3["common"][key] for key in prereg["common"]}
    assert prereg["common"] == dict(
        threads=1, mip_threads=1, gurobi_seed=0, gurobi_presolve=-1,
        affinity_mask=4, native_limit_offset_seconds=6,
        hard_stop_offset_seconds=2, shutdown_margin_seconds=3,
        requested_mip_gap=0, requested_mip_gap_abs=0)

    # The 19-role protocol and independent input audit, not a filename alone,
    # bind each scenario, handling parameter, and canonical local input byte.
    manifest = r90.read(ROOT / prereg["planning_manifest"])
    input_audit = r90.read(ROOT / prereg["input_identity_audit"])
    assert manifest["canonical_development_root"].replace("\\", "/") == str(ROOT).replace("\\", "/")
    assert input_audit["role_count"] == 19 and input_audit["all_hashes_match"] is True
    assert input_audit["all_scenarios_match"] is True
    assert r90.sha(ROOT / prereg["input_identity_audit"]) == prereg["harness_hashes"]["input_identity_audit"]
    planned = {row["id"]: row for row in manifest["roles"]}
    audited = {row["id"]: row for row in input_audit["roles"]}
    assert len(planned) == len(audited) == 19
    roles = prereg["roles"]
    assert [row["id"] for row in roles] == ["F2", "D6"]
    assert [row["method_order"] for row in roles] == [
        ["ENS-C", "LP-G"], ["LP-G", "ENS-C"]]
    assert [row["cap_seconds"] for row in roles] == [600, 3600]
    assert sum(2 * row["cap_seconds"] for row in roles) == 8400
    for role in roles:
        source, audit = planned[role["id"]], audited[role["id"]]
        relative = source["input_path"].replace("\\", "/").split("/reference/", 1)
        assert len(relative) == 2
        assert role["input_path"] == "reference/" + relative[1]
        assert source["source_protocol"].replace("\\", "/").endswith("/protocol.json")
        assert audit["historical_source_path"].replace("\\", "/") == source["input_path"].replace("\\", "/")
        assert Path(audit["execution_path"]).resolve() == (ROOT / role["input_path"]).resolve()
        assert audit["passed"] is True and audit["hash_matches_planning_and_protocol"] is True
        assert audit["scenario_matches_protocol"] is True
        for name in ("scenario_id", "T_seconds", "pickup_seconds", "drop_seconds", "lambda"):
            assert role[name] == source[name] == audit[name], (role["id"], name)
        assert role["input_sha256"] == source["input_sha256_from_protocol"]
        assert role["input_sha256"] == audit["actual_sha256"] == audit["planning_sha256"]
        assert role["cap_seconds"] == source["development_full_run_cap_seconds"]
        pinned_file(r90, role["input_path"], role["input_sha256"])
    return g3


def four_launches(r90, prereg: dict, g3: dict) -> list[dict]:
    launches = []
    exemplar = g3["panel"][0]
    variable_options = {"--input", "--lambda", "--T", "--pickup-time", "--drop-time",
                        "--time-limit", "--process-wall-time-limit"}

    def masked(command: list[str]) -> list[str]:
        result = command.copy()
        for option in variable_options:
            assert result.count(option) == 1
            result[result.index(option) + 1] = "<role-scenario-or-cap>"
        return result

    for role in prereg["roles"]:
        for arm in role["method_order"]:
            number = len(launches) + 1
            within_role = 1 + (number - 1) % 2
            destination = CAMPAIGN / role["id"] / "raw" / f'{within_role:02d}_{role["id"]}_{arm}'
            command = r90.command_for(g3, role, arm, destination)
            assert masked(command) == masked(r90.command_for(g3, exemplar, arm, destination))
            assert command[command.index("--round90-lp-g-split") + 1] == (
                "true" if arm == "LP-G" else "false")
            assert command[command.index("--gurobi-seed") + 1] == "0"
            assert command[command.index("--time-limit") + 1] == str(role["cap_seconds"] - 6)
            assert command[command.index("--process-wall-time-limit") + 1] == str(role["cap_seconds"])
            assert "--round88-constructive-only-descent" not in command
            assert "--round89-native-ot-b1" not in command
            launches.append(dict(number=number, id=role["id"], arm=arm, seed=0,
                                 stage="g4_priority", panel=dict(role, instance_path=role["input_path"]),
                                 destination=str(destination), cap_seconds=role["cap_seconds"],
                                 hard_stop_seconds=role["cap_seconds"] - 2, command=command))
    assert [f'{row["id"]}/{row["arm"]}' for row in launches] == prereg["execution_order"]
    assert len(launches) == 4 and sum(row["cap_seconds"] for row in launches) == 8400
    assert len({row["destination"] for row in launches}) == 4
    return launches


def root_prepare_gate(r90, prereg: dict) -> tuple[dict, str]:
    gate_path = ROOT / prereg["prepare_gate_path"]
    gate = r90.read(gate_path)  # Created by root only after final C2 evidence review.
    assert gate["schema"] == "round90-lp-g-g4-priority-prepare-gate-v1"
    assert gate["authorized_by"] == "root" and gate["allow_prepare"] is True
    assert gate["allow_optimize"] is False and gate["c2_priority_criterion_accepted"] is True
    assert gate["prereg_sha256"] == r90.sha(PREREG)
    assert gate["wrapper_sha256"] == r90.sha(Path(__file__))
    assert gate["frozen_runner_sha256"] == prereg["frozen_g3_runner_sha256"]
    assert gate["candidate_binary_sha256"] == prereg["candidate_binary_sha256"]
    review_path = gate["c2_final_review_path"]
    assert review_path.startswith("results/unified_exact_round90/")
    pinned_file(r90, review_path, gate["c2_final_review_sha256"])
    return gate, r90.sha(gate_path)


def prepare(r90) -> None:
    prereg = r90.read(PREREG)
    g3 = validate(r90, prereg)
    launches = four_launches(r90, prereg, g3)
    gate, gate_sha = root_prepare_gate(r90, prereg)
    assert not CAMPAIGN.exists(), "Never overwrite, resume, or splice a campaign"
    assert not r90.foreign_heavy_processes(), "Foreign solver/build process present"
    CAMPAIGN.mkdir(parents=True, exist_ok=False)
    r90.write_new(CAMPAIGN / "identity.json", dict(
        schema="round90-lp-g-g4-priority-identity-v1", optimizer_calls=0,
        prereg_sha256=r90.sha(PREREG), wrapper_sha256=r90.sha(Path(__file__)),
        runner_sha256=prereg["frozen_g3_runner_sha256"], gate_sha256=gate_sha,
        c2_final_review_sha256=gate["c2_final_review_sha256"],
        candidate_binary_sha256=prereg["candidate_binary_sha256"],
        source_commit=prereg["source_commit"], source_hashes=prereg["source_hashes"],
        harness_hashes=prereg["harness_hashes"], launches=launches,
        prepared_unix=time.time()))
    r90.write_new(CAMPAIGN / "preflight.json", dict(
        schema="round90-lp-g-g4-priority-preflight-v1", optimizer_calls=0,
        planned_runs=4, process_cap_sum_seconds=8400, canonical_inputs_verified=2,
        source_binary_harness_verified=True, final_c2_review_pinned=True,
        disk_free_bytes=shutil.disk_usage(CAMPAIGN).free,
        memory_available_bytes=r90.memory_available(),
        note="Preparation does not authorize Optimize; separate root run lease required."))
    print(json.dumps(dict(prepared=True, optimizer_calls=0, campaign=str(CAMPAIGN))), flush=True)


def native_parameters(r90, launch: dict, record: dict) -> dict:
    destination = Path(launch["destination"])
    reason = record["completion"]["stop_reason"]
    result_path = destination / "result.json"
    if reason != "normal_return" or not result_path.is_file():
        return dict(status="unknown_censored_or_missing_result", seed=0,
                    command_sha256=r90.sha(destination / "launch.json"))
    result = r90.read(result_path)
    for key, expected in dict(
        gurobi_seed_requested=0, gurobi_seed_effective=0,
        gurobi_threads_requested=1, gurobi_threads_effective=1,
        gurobi_presolve_requested=-1, gurobi_presolve_effective=-1).items():
        assert result[key] == expected, (launch["number"], key, result[key])
    for key in ("gurobi_seed_set_return_code", "gurobi_seed_get_return_code",
                "gurobi_threads_set_return_code", "gurobi_threads_get_return_code",
                "gurobi_presolve_set_return_code", "gurobi_presolve_get_return_code"):
        assert result[key] == 0, (launch["number"], key)
    expected_identity = ("research-round90-ensc-lp-g-split" if launch["arm"] == "LP-G"
                         else "research-round83-vds-equal-net-exchange")
    assert result["algorithm_preset"] == expected_identity
    return dict(status="native_result_readback_verified", seed=0,
                result_sha256=r90.sha(result_path), algorithm_preset=expected_identity,
                gurobi_seed_effective=result["gurobi_seed_effective"],
                gurobi_threads_effective=result["gurobi_threads_effective"],
                gurobi_presolve_effective=result["gurobi_presolve_effective"])


def run(r90) -> None:
    prereg = r90.read(PREREG)
    g3 = validate(r90, prereg)
    gate, gate_sha = root_prepare_gate(r90, prereg)
    identity_path = CAMPAIGN / "identity.json"
    identity = r90.read(identity_path)
    assert identity["schema"] == "round90-lp-g-g4-priority-identity-v1"
    assert identity["prereg_sha256"] == r90.sha(PREREG)
    assert identity["wrapper_sha256"] == r90.sha(Path(__file__))
    assert identity["runner_sha256"] == prereg["frozen_g3_runner_sha256"]
    assert identity["gate_sha256"] == gate_sha
    assert identity["c2_final_review_sha256"] == gate["c2_final_review_sha256"]
    assert identity["candidate_binary_sha256"] == prereg["candidate_binary_sha256"]
    assert identity["source_hashes"] == prereg["source_hashes"]
    assert identity["harness_hashes"] == prereg["harness_hashes"]
    assert identity["launches"] == four_launches(r90, prereg, g3)
    lease_path = CAMPAIGN / prereg["run_lease_name"]
    lease = r90.read(lease_path)
    assert lease == dict(schema="round90-lp-g-g4-priority-run-lease-v1",
                         authorized_by="root", allow_optimize=True,
                         identity_sha256=r90.sha(identity_path), planned_runs=4,
                         execution_order=prereg["execution_order"])
    assert not (CAMPAIGN / "run_started.json").exists(), "Never rerun or resume"
    assert not (CAMPAIGN / "active_run.lock").exists()
    assert not (CAMPAIGN / "summary.jsonl").exists()
    assert all(not Path(row["destination"]).exists() for row in identity["launches"])
    assert not r90.foreign_heavy_processes(), "Foreign solver/build process present"
    started = time.perf_counter()
    r90.write_new(CAMPAIGN / "run_started.json", dict(
        identity_sha256=r90.sha(identity_path), lease_sha256=r90.sha(lease_path),
        started_unix=time.time(), complete_process_runs_planned=4,
        internal_optimize_calls_unbounded_by_arm_count=True))
    records: list[dict] = []
    run_error = None
    with (CAMPAIGN / "active_run.lock").open("x", encoding="utf-8") as lock:
        lock.write(json.dumps(dict(pid=os.getpid(), started_unix=time.time())) + "\n")
    try:
        for launch in identity["launches"]:
            role = launch["id"]
            role_dir = CAMPAIGN / role
            attempt_started = time.perf_counter()
            try:
                if launch["number"] in (1, 3):
                    role_dir.mkdir(exist_ok=False)
                r90.CAMPAIGN = role_dir  # Only the separately loaded G3 module object.
                record = r90.run_one(launch, g3, identity)
                params = native_parameters(r90, launch, record)
                r90.write_new(Path(launch["destination"]) / "native_parameter_evidence.json", params)
                assert params["status"] == "native_result_readback_verified" or (
                    record["completion"]["stop_reason"] != "normal_return")
                record["seed"] = 0
                records.append(record)
                r90.append_jsonl(CAMPAIGN / "summary.jsonl", dict(
                    seed=0, role=role, record=record, native_parameter_evidence=params))
            except Exception as exc:
                r90.write_new(CAMPAIGN / f'runner_failure_{launch["number"]:02d}.json', dict(
                    schema="round90-lp-g-g4-priority-failure-v1", number=launch["number"],
                    role=role, arm=launch["arm"], error=repr(exc),
                    attempt_elapsed_seconds=time.perf_counter() - attempt_started,
                    destination=launch["destination"],
                    destination_exists=Path(launch["destination"]).exists(),
                    completion_exists=(Path(launch["destination"]) / "completion.json").is_file(),
                    requires_independent_review=True, recorded_unix=time.time()))
                raise
            if launch["number"] in (2, 4):
                pair = [row for row in records if row["id"] == role]
                assert {row["arm"] for row in pair} == {"ENS-C", "LP-G"}
                r90.cross_arm_contradiction(pair, role)
                signals = r90.severe_risk_signal(pair, role)
                if signals:
                    r90.write_new(role_dir / "runner_priority_risk_stop.json", dict(
                        role=role, signals=signals, research_signal_only=True,
                        requires_paired_review=True,
                        summary_sha256=r90.sha(CAMPAIGN / "summary.jsonl")))
                    raise RuntimeError("Severe paired signal; stop before next role")
    except Exception as exc:
        run_error = repr(exc)
        raise
    finally:
        (CAMPAIGN / "active_run.lock").unlink(missing_ok=True)
        failures = [r90.read(path) for path in sorted(CAMPAIGN.glob("runner_failure_*.json"))]
        attempted = {row["number"] for row in records} | {row["number"] for row in failures}
        paid_completions = [r90.read(Path(row["destination"]) / "completion.json")
                            for row in identity["launches"]
                            if (Path(row["destination"]) / "completion.json").is_file()]
        r90.write_new(CAMPAIGN / "run_completion.json", dict(
            schema="round90-lp-g-g4-priority-run-completion-v1", planned=4,
            completed=len(records), attempted=sorted(attempted), error=run_error,
            not_run=[f'{row["id"]}/{row["arm"]}' for row in identity["launches"]
                     if row["number"] not in attempted],
            paid_process_wall_seconds_with_completion=sum(
                row["process_wall_seconds"] for row in paid_completions),
            completed_process_receipts=len(paid_completions),
            precompletion_failed_attempt_elapsed_seconds=sum(
                row["attempt_elapsed_seconds"] for row in failures
                if not row["completion_exists"]),
            full_outer_wall_seconds=time.perf_counter() - started,
            outer_wall_excludes_preflight_validation=True,
            failed_attempt_costs=failures,
            ended_unix=time.time()))


def main() -> None:
    assert len(sys.argv) == 2 and sys.argv[1] in {"prepare", "run"}, \
        "Usage: round90_lp_g_g4_priority.py prepare|run"
    r90 = frozen_runner()
    if sys.argv[1] == "prepare":
        prepare(r90)
    else:
        run(r90)


if __name__ == "__main__":
    main()
