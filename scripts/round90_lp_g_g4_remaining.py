"""Conditional serial G4 wrapper for the nine preselected remaining roles.

No work occurs on import. ``prepare`` requires one root source gate and makes
zero Optimize calls. ``run`` requires one further root batch lease; it may
start at most 18 complete processes and never resumes or retries a prefix.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "results/unified_exact_round90/preregistration_g4_remaining.json"
CAMPAIGN = ROOT / "results/unified_exact_round90/runner_lp_g_g4_remaining"
ROLE_IDS = ("N12", "D4", "E7", "C6", "C8", "F1", "C20", "B50", "S50")
CAPS = (120, 600, 120, 1200, 1200, 120, 1200, 3600, 3600)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def frozen_priority():
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    path = ROOT / prereg["frozen_priority_wrapper"]
    assert sha(path) == prereg["frozen_priority_wrapper_sha256"]
    spec = importlib.util.spec_from_file_location("round90_g4_priority_readonly_for_remaining", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.CAMPAIGN == ROOT / prereg["priority_runtime_root"]
    return module


def validate(priority, r90, prereg: dict) -> tuple[dict, dict]:
    assert os.name == "nt", "Windows-only historical binary"
    assert prereg["schema"] == "round90-lp-g-g4-remaining-preregistration-v1"
    assert prereg["status"] == "conditional_source_only_no_execution"
    assert prereg["runtime_root"] == CAMPAIGN.relative_to(ROOT).as_posix()
    assert prereg["planned_runs"] == 18 and prereg["sum_process_caps_seconds"] == 23520
    assert prereg["seed"] == 0 and prereg["no_component_time_or_work_slices"] is True
    assert prereg["prepare_does_not_authorize_optimize"] is True
    assert prereg["run_requires_separate_root_lease"] is True
    assert [row["id"] for row in prereg["roles"]] == list(ROLE_IDS)
    assert [row["cap_seconds"] for row in prereg["roles"]] == list(CAPS)
    assert [row["method_order"] for row in prereg["roles"]] == [
        ["ENS-C", "LP-G"] if i % 2 == 0 else ["LP-G", "ENS-C"]
        for i in range(len(ROLE_IDS))]
    assert sum(2 * row["cap_seconds"] for row in prereg["roles"]) == 23520
    assert [f'{row["id"]}/{arm}' for row in prereg["roles"]
            for arm in row["method_order"]] == prereg["execution_order"]
    assert priority.ROOT == ROOT
    assert sha(ROOT / prereg["frozen_priority_preregistration"]) == \
        prereg["frozen_priority_preregistration_sha256"]
    assert sha(ROOT / prereg["frozen_g3_runner"]) == prereg["frozen_g3_runner_sha256"]
    priority_prereg = r90.read(ROOT / prereg["frozen_priority_preregistration"])
    g3 = priority.validate(r90, priority_prereg)
    assert priority_prereg["planning_manifest"] == prereg["planning_manifest"]
    assert priority_prereg["input_identity_audit"] == prereg["input_identity_audit"]
    assert priority_prereg["frozen_g3_runner_sha256"] == prereg["frozen_g3_runner_sha256"]
    manifest = r90.read(ROOT / prereg["planning_manifest"])
    input_audit = r90.read(ROOT / prereg["input_identity_audit"])
    assert manifest["canonical_development_root"].replace("\\", "/") == str(ROOT).replace("\\", "/")
    assert input_audit["role_count"] == 19 and input_audit["all_hashes_match"] is True
    assert input_audit["all_scenarios_match"] is True
    assert r90.sha(ROOT / prereg["input_identity_audit"]) == \
        priority_prereg["harness_hashes"]["input_identity_audit"]
    planned = {row["id"]: row for row in manifest["roles"]}
    audited = {row["id"]: row for row in input_audit["roles"]}
    assert len(planned) == len(audited) == 19
    for role in prereg["roles"]:
        source, audit = planned[role["id"]], audited[role["id"]]
        pieces = source["input_path"].replace("\\", "/").split("/reference/", 1)
        assert len(pieces) == 2 and role["input_path"] == "reference/" + pieces[1]
        assert source["source_protocol"].replace("\\", "/").endswith("/protocol.json")
        assert audit["historical_source_path"].replace("\\", "/") == \
            source["input_path"].replace("\\", "/")
        assert Path(audit["execution_path"]).resolve() == (ROOT / role["input_path"]).resolve()
        assert audit["passed"] is True and audit["hash_matches_planning_and_protocol"] is True
        assert audit["scenario_matches_protocol"] is True
        for name in ("scenario_id", "T_seconds", "pickup_seconds", "drop_seconds", "lambda"):
            assert role[name] == source[name] == audit[name], (role["id"], name)
        assert role["input_sha256"] == source["input_sha256_from_protocol"]
        assert role["input_sha256"] == audit["actual_sha256"] == audit["planning_sha256"]
        assert role["cap_seconds"] == source["development_full_run_cap_seconds"]
        priority.pinned_file(r90, role["input_path"], role["input_sha256"])
    return priority_prereg, g3


def launches_for(r90, prereg: dict, g3: dict) -> list[dict]:
    launches = []
    exemplar = g3["panel"][0]
    variable_options = ("--input", "--lambda", "--T", "--pickup-time", "--drop-time",
                        "--time-limit", "--process-wall-time-limit")

    def masked(command: list[str]) -> list[str]:
        result = command.copy()
        for option in variable_options:
            assert result.count(option) == 1
            result[result.index(option) + 1] = "<registered-role-value>"
        return result

    for role in prereg["roles"]:
        for offset, arm in enumerate(role["method_order"], 1):
            number = len(launches) + 1
            destination = CAMPAIGN / role["id"] / "raw" / f'{offset:02d}_{role["id"]}_{arm}'
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
                                 stage="g4_remaining", panel=dict(role, instance_path=role["input_path"]),
                                 destination=str(destination), cap_seconds=role["cap_seconds"],
                                 hard_stop_seconds=role["cap_seconds"] - 2, command=command))
    assert len(launches) == 18 and sum(row["cap_seconds"] for row in launches) == 23520
    assert [f'{row["id"]}/{row["arm"]}' for row in launches] == prereg["execution_order"]
    assert len({row["destination"] for row in launches}) == 18
    return launches


def root_prepare_gate(priority, r90, prereg: dict) -> tuple[dict, str]:
    priority_root = ROOT / prereg["priority_runtime_root"]
    completion_path = priority_root / "run_completion.json"
    summary_path = priority_root / "summary.jsonl"
    completion = r90.read(completion_path)
    assert completion["planned"] == completion["completed"] == 4
    assert completion["error"] is None and completion["not_run"] == []
    with summary_path.open(encoding="utf-8") as stream:
        summary = [json.loads(line) for line in stream if line.strip()]
    assert len(summary) == 4
    assert [f'{row["role"]}/{row["record"]["arm"]}' for row in summary] == [
        "F2/ENS-C", "F2/LP-G", "D6/LP-G", "D6/ENS-C"]
    gate_path = ROOT / prereg["prepare_gate_path"]
    gate = r90.read(gate_path)
    assert gate["schema"] == "round90-lp-g-g4-remaining-prepare-gate-v1"
    assert gate["authorized_by"] == "root" and gate["allow_prepare"] is True
    assert gate["allow_optimize"] is False and gate["priority_stage_accepted"] is True
    assert gate["prereg_sha256"] == r90.sha(PREREG)
    assert gate["wrapper_sha256"] == r90.sha(Path(__file__))
    assert gate["frozen_priority_wrapper_sha256"] == prereg["frozen_priority_wrapper_sha256"]
    assert gate["priority_completion_sha256"] == r90.sha(completion_path)
    assert gate["priority_summary_sha256"] == r90.sha(summary_path)
    review = gate["priority_independent_review_path"]
    assert review.startswith("results/unified_exact_round90/")
    priority.pinned_file(r90, review, gate["priority_independent_review_sha256"])
    return gate, r90.sha(gate_path)


def prepare(priority, r90) -> None:
    prereg = r90.read(PREREG)
    priority_prereg, g3 = validate(priority, r90, prereg)
    launches = launches_for(r90, prereg, g3)
    gate, gate_sha = root_prepare_gate(priority, r90, prereg)
    assert not CAMPAIGN.exists(), "Never overwrite, resume or splice a campaign"
    assert not r90.foreign_heavy_processes(), "Foreign solver/build process present"
    CAMPAIGN.mkdir(parents=True, exist_ok=False)
    r90.write_new(CAMPAIGN / "identity.json", dict(
        schema="round90-lp-g-g4-remaining-identity-v1", optimizer_calls=0,
        prereg_sha256=r90.sha(PREREG), wrapper_sha256=r90.sha(Path(__file__)),
        frozen_priority_wrapper_sha256=prereg["frozen_priority_wrapper_sha256"],
        runner_sha256=prereg["frozen_g3_runner_sha256"], gate_sha256=gate_sha,
        priority_completion_sha256=gate["priority_completion_sha256"],
        priority_summary_sha256=gate["priority_summary_sha256"],
        priority_independent_review_sha256=gate["priority_independent_review_sha256"],
        candidate_binary_sha256=priority_prereg["candidate_binary_sha256"],
        source_commit=priority_prereg["source_commit"],
        source_hashes=priority_prereg["source_hashes"],
        harness_hashes=priority_prereg["harness_hashes"],
        launches=launches, prepared_unix=time.time()))
    r90.write_new(CAMPAIGN / "preflight.json", dict(
        schema="round90-lp-g-g4-remaining-preflight-v1", optimizer_calls=0,
        planned_runs=18, process_cap_sum_seconds=23520, canonical_inputs_verified=9,
        source_binary_harness_verified=True, priority_stage_accepted=True,
        disk_free_bytes=shutil.disk_usage(CAMPAIGN).free,
        memory_available_bytes=r90.memory_available(),
        note="Prepare does not authorize Optimize; one root batch lease is required."))
    print(json.dumps(dict(prepared=True, optimizer_calls=0, campaign=str(CAMPAIGN))), flush=True)


def run(priority, r90) -> None:
    prereg = r90.read(PREREG)
    priority_prereg, g3 = validate(priority, r90, prereg)
    gate, gate_sha = root_prepare_gate(priority, r90, prereg)
    identity_path = CAMPAIGN / "identity.json"
    identity = r90.read(identity_path)
    assert identity["schema"] == "round90-lp-g-g4-remaining-identity-v1"
    assert identity["prereg_sha256"] == r90.sha(PREREG)
    assert identity["wrapper_sha256"] == r90.sha(Path(__file__))
    assert identity["runner_sha256"] == prereg["frozen_g3_runner_sha256"]
    assert identity["gate_sha256"] == gate_sha
    assert identity["priority_completion_sha256"] == gate["priority_completion_sha256"]
    assert identity["priority_summary_sha256"] == gate["priority_summary_sha256"]
    assert identity["priority_independent_review_sha256"] == gate["priority_independent_review_sha256"]
    assert identity["candidate_binary_sha256"] == priority_prereg["candidate_binary_sha256"]
    assert identity["source_hashes"] == priority_prereg["source_hashes"]
    assert identity["harness_hashes"] == priority_prereg["harness_hashes"]
    assert identity["launches"] == launches_for(r90, prereg, g3)
    lease_path = CAMPAIGN / prereg["run_lease_name"]
    lease = r90.read(lease_path)
    assert lease == dict(schema="round90-lp-g-g4-remaining-run-lease-v1",
                         authorized_by="root", allow_optimize=True,
                         identity_sha256=r90.sha(identity_path), planned_runs=18,
                         execution_order=prereg["execution_order"])
    assert not (CAMPAIGN / "run_started.json").exists(), "Never rerun or resume"
    assert not (CAMPAIGN / "active_run.lock").exists()
    assert not (CAMPAIGN / "summary.jsonl").exists()
    assert all(not Path(row["destination"]).exists() for row in identity["launches"])
    assert not r90.foreign_heavy_processes(), "Foreign solver/build process present"
    started = time.perf_counter()
    r90.write_new(CAMPAIGN / "run_started.json", dict(
        identity_sha256=r90.sha(identity_path), lease_sha256=r90.sha(lease_path),
        started_unix=time.time(), complete_process_runs_planned=18,
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
                if launch["number"] % 2 == 1:
                    role_dir.mkdir(exist_ok=False)
                r90.CAMPAIGN = role_dir  # The independently loaded G3 module object only.
                record = r90.run_one(launch, g3, identity)
                params = priority.native_parameters(r90, launch, record)
                r90.write_new(Path(launch["destination"]) / "native_parameter_evidence.json", params)
                assert params["status"] == "native_result_readback_verified" or (
                    record["completion"]["stop_reason"] != "normal_return")
                record["seed"] = 0
                records.append(record)
                r90.append_jsonl(CAMPAIGN / "summary.jsonl", dict(
                    seed=0, role=role, record=record, native_parameter_evidence=params))
            except Exception as exc:
                r90.write_new(CAMPAIGN / f'runner_failure_{launch["number"]:02d}.json', dict(
                    schema="round90-lp-g-g4-remaining-failure-v1", number=launch["number"],
                    role=role, arm=launch["arm"], error=repr(exc),
                    attempt_elapsed_seconds=time.perf_counter() - attempt_started,
                    destination=launch["destination"],
                    destination_exists=Path(launch["destination"]).exists(),
                    completion_exists=(Path(launch["destination"]) / "completion.json").is_file(),
                    requires_independent_review=True, recorded_unix=time.time()))
                raise
            if launch["number"] % 2 == 0:
                pair = [row for row in records if row["id"] == role]
                assert {row["arm"] for row in pair} == {"ENS-C", "LP-G"}
                r90.cross_arm_contradiction(pair, role)
                signals = r90.severe_risk_signal(pair, role)
                if signals:
                    r90.write_new(role_dir / "runner_remaining_risk_stop.json", dict(
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
            schema="round90-lp-g-g4-remaining-run-completion-v1", planned=18,
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
            failed_attempt_costs=failures, ended_unix=time.time()))


def main() -> None:
    assert len(sys.argv) == 2 and sys.argv[1] in {"prepare", "run"}, \
        "Usage: round90_lp_g_g4_remaining.py prepare|run"
    priority = frozen_priority()
    r90 = priority.frozen_runner()
    if sys.argv[1] == "prepare":
        prepare(priority, r90)
    else:
        run(priority, r90)


if __name__ == "__main__":
    main()
