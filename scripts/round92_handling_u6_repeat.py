"""Conditional four-arm U6 risk repeat around the frozen Round92 G3 runner.

Import is inert. ``prepare`` is zero-Optimize and requires a separate root gate;
``run`` requires a root lease bound to the prepared identity. The original G3
module, campaign, raw evidence, and seed-0 pair are never modified.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import statistics
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "results/unified_exact_round92/preregistration_u6_repeat.json"
CAMPAIGN = ROOT / "results/unified_exact_round92/runner_u6_repeat"


class SeedAwareEvidence:
    """Explicit adapter for R86's frozen Seed=0 reader, on this module object only.

Every original call setting is first checked against the *actual* requested
seed and all other frozen settings. Only then an in-memory shallow copy with
Seed=0 is given to the original independent physical/scope/bound audit. Raw
journal events, observations.json, and receipt SHA values remain untouched.
    """

    def __init__(self, frozen, seed: int):
        self.frozen = frozen
        self.seed = seed
        self.physical_module = frozen.physical_module

    def receipt(self, *args, **kwargs):
        return self.frozen.receipt(*args, **kwargs)

    def audit(self, root, panel, records, binary_hash):
        expected = dict(read_return_code=0, Threads=1, Seed=self.seed, Presolve=-1,
                        MIPGap=0, MIPGapAbs=0, FeasibilityTol=1e-6,
                        IntFeasTol=1e-5, OptimalityTol=1e-6)
        projected = []
        original_calls = []
        for record in records:
            event = record["payload"]
            if event["kind"] != "call":
                projected.append(record)
                continue
            assert event["settings"] == expected, ("native_call_settings_mismatch",
                                                   self.seed, event["call"], event["settings"])
            original_calls.append(event["call"])
            projected_event = dict(event, settings=dict(event["settings"], Seed=0))
            projected.append(dict(record, payload=projected_event))
        audited = self.frozen.audit(root, panel, projected, binary_hash)
        audited["seed_aware_evidence_adapter"] = dict(
            status="original_call_settings_exactly_verified_before_projection",
            original_seed=self.seed, original_call_numbers=original_calls,
            original_call_count=len(original_calls), projected_in_memory_only=True,
            frozen_reader_expected_seed=0, raw_receipts_modified=False,
            all_nonseed_native_settings_compared=True)
        return audited

    def finalize_endpoint(self, *args, **kwargs):
        return self.frozen.finalize_endpoint(*args, **kwargs)


def frozen_runner():
    """Use a distinct module object so per-seed CAMPAIGN never alters G3."""
    path = ROOT / "scripts/round92_handling_g3.py"
    spec = importlib.util.spec_from_file_location("round92_handling_g3_u6_repeat_frozen", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.CAMPAIGN == ROOT / "results/unified_exact_round92/runner_handling_g3"
    return module


def pin(r92, relative: str, digest: str) -> None:
    assert r92.sha(ROOT / relative) == digest, relative


def seed0_reference(r92, prereg: dict) -> dict[str, dict]:
    old = prereg["seed0_reference"]
    assert old["status"] == "completed_same_round92_binary_open_gap_risk_not_rerun"
    for stem in ("g3_summary", "g3_rest_report", "g3_independent_review",
                 "g3_cross_arm", "g3_risk_stop"):
        pin(r92, old[stem + "_path"], old[stem + "_sha256"])
    assert r92.read(ROOT / old["g3_cross_arm_path"])["passed"] is True
    risk = r92.read(ROOT / old["g3_risk_stop_path"])
    assert risk["role"] == "U6" and risk["summary_sha256"] == old["g3_summary_sha256"]
    assert [row["kind"] for row in risk["signals"]] == ["severe_open_gap_signal"]
    summary = [json.loads(line) for line in
               (ROOT / old["g3_summary_path"]).read_text(encoding="utf-8").splitlines()]
    assert len(summary) == 12 and [row["number"] for row in summary] == list(range(1, 13))
    pair = {row["arm"]: row for row in summary if row["id"] == "U6"}
    assert set(pair) == {"ENS-C", "H-ACT"}
    for arm, receipt in old["arms"].items():
        raw = ROOT / receipt["raw"]
        for name in ("launch", "audit", "completion", "result"):
            assert r92.sha(raw / (name + ".json")) == receipt[name + "_sha256"]
        record = pair[arm]
        assert Path(record["destination"]) == raw.resolve()
        assert record["audit_passed"] and record["completion"]["stop_reason"] == "normal_return"
        assert record["completion"]["process_cap_seconds"] == 1200
        assert record["endpoint"] is not None and not record["endpoint"]["certificate"]
        result = r92.read(raw / "result.json")
        assert result["gurobi_seed_requested"] == result["gurobi_seed_effective"] == 0
        assert result["decoded_descent_seeds_completed"] == 25
        assert result["algorithm_preset"] == (
            "research-round92-ensc-rounded-handling-activation" if arm == "H-ACT"
            else "research-round83-vds-equal-net-exchange")
        assert r92.read(raw / "audit.json")["passed"] is True
    return pair


def validate(r92, prereg: dict) -> tuple[dict, dict, dict[str, dict]]:
    assert os.name == "nt", "Windows-only study"
    assert prereg["schema"] == "round92-handling-u6-repeat-preregistration-v1"
    assert prereg["status"] == "conditional_source_only_no_execution"
    assert prereg["runtime_root"] == str(CAMPAIGN.relative_to(ROOT)).replace("\\", "/")
    assert prereg["planned_arms"] == 4 and prereg["sum_process_caps_seconds"] == 4800
    assert prereg["prepare_does_not_authorize_optimize"] is True
    assert prereg["run_requires_separate_root_lease"] is True
    assert prereg["no_component_time_or_work_slices"] is True
    assert prereg["stop_on_correctness_identity_numeric_process_or_resource_fault"] is True
    assert prereg["no_retry_no_overwrite_no_extra_seed_or_cap"] is True
    assert prereg["repeat_order"] == [
        {"seed": 1, "method_order": ["ENS-C", "H-ACT"]},
        {"seed": 2, "method_order": ["H-ACT", "ENS-C"]}]
    rule = prereg["risk_rule"]
    assert rule["ratio_threshold"] == 1.5 and rule["absolute_gap_threshold"] == 0.01
    assert rule["required_same_direction_seeds"] == 2
    assert rule["required_original_severe_line_seeds"] == 2
    assert rule["require_all_three_open_for_median"] is True
    assert rule["performance_signals_do_not_stop_seed_2"] is True
    assert rule["all_four_planned_arms_even_after_seed_1_risk"] is True
    for name in ("frozen_g3_runner", "frozen_g3_preregistration",
                 "frozen_g3_qualification_gate"):
        pin(r92, prereg[name], prereg[name + "_sha256"])
    g3 = r92.read(ROOT / prereg["frozen_g3_preregistration"])
    gate = r92.read(ROOT / prereg["frozen_g3_qualification_gate"])
    r92.panel_and_identity(g3)
    assert r92.qualification_gate(g3) == gate
    assert gate["source_commit"] == prereg["source_commit"]
    assert gate["candidate_binary_sha256"] == prereg["candidate_binary_sha256"]
    assert gate["candidate_core_sha256"] == prereg["candidate_core_sha256"]
    assert gate["harness_hashes"] == r92.harness_hashes()
    assert len(gate["source_hashes"]) == 15
    assert prereg["candidate_binary"] == g3["candidate_binary"]
    u6 = next(row for row in g3["panel"] if row["id"] == "U6")
    assert sum(row["id"] == "U6" for row in g3["panel"]) == 1
    assert prereg["u6"] == {key: u6[key] for key in prereg["u6"]}
    assert prereg["u6"]["cap_seconds"] == 1200
    assert prereg["common"] == {key: g3["common"][key] for key in prereg["common"]}
    pin(r92, u6["input_path"], u6["input_sha256"])
    return g3, u6, seed0_reference(r92, prereg)


def four_launches(r92, prereg: dict, g3: dict, u6: dict) -> list[dict]:
    launches = []
    for planned in prereg["repeat_order"]:
        seed = planned["seed"]
        for arm in planned["method_order"]:
            number = len(launches) + 1
            ordinal = 1 + (number - 1) % 2
            destination = CAMPAIGN / f"seed_{seed}" / "raw" / f"{ordinal:02d}_U6_{arm}"
            original = r92.command_for(g3, u6, arm, destination)
            assert original.count("--gurobi-seed") == 1
            index = original.index("--gurobi-seed") + 1
            assert original[index] == "0"
            command = original.copy()
            command[index] = str(seed)
            assert command[:index] + ["0"] + command[index + 1:] == original
            assert command[command.index("--round92-handling-activation") + 1] == (
                "true" if arm == "H-ACT" else "false")
            assert command[command.index("--time-limit") + 1] == "1194"
            assert command[command.index("--process-wall-time-limit") + 1] == "1200"
            assert command[command.index("--threads") + 1] == "1"
            assert command[command.index("--mip-threads") + 1] == "1"
            assert command[command.index("--gurobi-presolve") + 1] == "-1"
            assert "--round88-constructive-only-descent" not in command
            assert "--round89-native-ot-b1" not in command
            assert "--round90-lp-g-split" not in command
            launches.append(dict(number=number, id="U6", arm=arm, seed=seed,
                                 stage="repeat", panel=dict(u6, instance_path=u6["input_path"]),
                                 destination=str(destination), cap_seconds=1200,
                                 hard_stop_seconds=1198, command=command))
    assert [(row["seed"], row["arm"]) for row in launches] == [
        (1, "ENS-C"), (1, "H-ACT"), (2, "H-ACT"), (2, "ENS-C")]
    assert len({row["destination"] for row in launches}) == 4
    assert sum(row["cap_seconds"] for row in launches) == 4800
    return launches


def prepare(r92) -> None:
    prereg = r92.read(PREREG)
    g3, u6, _ = validate(r92, prereg)
    launches = four_launches(r92, prereg, g3, u6)
    gate_path = ROOT / prereg["prepare_gate_path"]
    gate = r92.read(gate_path)  # To be created separately by root.
    assert gate == dict(
        schema="round92-handling-u6-repeat-prepare-gate-v1", authorized_by="root",
        allow_prepare=True, allow_optimize=False,
        prereg_sha256=r92.sha(PREREG), wrapper_sha256=r92.sha(Path(__file__)),
        frozen_runner_sha256=prereg["frozen_g3_runner_sha256"],
        g3_qualification_gate_sha256=prereg["frozen_g3_qualification_gate_sha256"],
        g3_summary_sha256=prereg["seed0_reference"]["g3_summary_sha256"],
        g3_independent_review_sha256=prereg["seed0_reference"]["g3_independent_review_sha256"],
        candidate_binary_sha256=prereg["candidate_binary_sha256"])
    assert not CAMPAIGN.exists(), "Never overwrite, resume, or splice"
    assert not r92.foreign_heavy_processes(), "Foreign solver/build process present"
    CAMPAIGN.mkdir(parents=True, exist_ok=False)
    old_gate = r92.read(ROOT / prereg["frozen_g3_qualification_gate"])
    identity = dict(schema="round92-handling-u6-repeat-identity-v1", optimizer_calls=0,
                    prereg_sha256=r92.sha(PREREG), wrapper_sha256=r92.sha(Path(__file__)),
                    runner_sha256=prereg["frozen_g3_runner_sha256"],
                    gate_sha256=r92.sha(gate_path),
                    candidate_binary_sha256=prereg["candidate_binary_sha256"],
                    candidate_core_sha256=prereg["candidate_core_sha256"],
                    source_commit=prereg["source_commit"], source_hashes=old_gate["source_hashes"],
                    harness_hashes=old_gate["harness_hashes"], launches=launches,
                    prepared_unix=time.time())
    r92.write_new(CAMPAIGN / "identity.json", identity)
    r92.write_new(CAMPAIGN / "preflight.json", dict(
        schema="round92-handling-u6-repeat-preflight-v1", optimizer_calls=0,
        planned_arms=4, process_cap_sum_seconds=4800,
        seed0_reference_open_pair=True, source_binary_harness_verified=True,
        input_hash_verified=True, native_seed_new_arms_not_yet_tested=True,
        disk_free_bytes=shutil.disk_usage(CAMPAIGN).free,
        memory_available_bytes=r92.memory_available(),
        note="Separate identity-bound root run lease is required."))
    print(json.dumps(dict(prepared=True, optimizer_calls=0, campaign=str(CAMPAIGN))), flush=True)


def native_parameters(r92, launch: dict, record: dict) -> dict:
    destination = Path(launch["destination"])
    reason = record["completion"]["stop_reason"]
    result_path = destination / "result.json"
    assert reason == "normal_return" and result_path.is_file(), (
        "Native Seed readback unavailable; keep unknown and stop", launch["number"], reason)
    result = r92.read(result_path)
    for key, expected in dict(
        gurobi_seed_requested=launch["seed"], gurobi_seed_effective=launch["seed"],
        gurobi_threads_requested=1, gurobi_threads_effective=1,
        gurobi_presolve_requested=-1, gurobi_presolve_effective=-1).items():
        assert result[key] == expected, (launch["number"], key, result[key])
    for key in ("gurobi_seed_set_return_code", "gurobi_seed_get_return_code",
                "gurobi_threads_set_return_code", "gurobi_threads_get_return_code",
                "gurobi_presolve_set_return_code", "gurobi_presolve_get_return_code"):
        assert result[key] == 0, (launch["number"], key, result[key])
    assert result["external_gini_tree_backend_parameter_roundtrip_valid"] is True
    assert result["decoded_descent_seeds_completed"] == 25
    expected_identity = ("research-round92-ensc-rounded-handling-activation"
                         if launch["arm"] == "H-ACT" else
                         "research-round83-vds-equal-net-exchange")
    assert result["algorithm_preset"] == expected_identity
    return dict(status="native_result_seed_readback_verified", seed=launch["seed"],
                result_sha256=r92.sha(result_path), algorithm_preset=expected_identity,
                gurobi_seed_requested=result["gurobi_seed_requested"],
                gurobi_seed_effective=result["gurobi_seed_effective"],
                gurobi_threads_effective=result["gurobi_threads_effective"],
                gurobi_presolve_effective=result["gurobi_presolve_effective"],
                startup_decoded_descent_seeds_completed=25)


def pair_status(pair: dict[str, dict]) -> dict:
    if set(pair) != {"ENS-C", "H-ACT"}:
        return dict(status="unknown_incomplete_pair")
    if not all(row["audit_passed"] and row["endpoint"] is not None and
               row["completion"]["stop_reason"] == "normal_return"
               for row in pair.values()):
        return dict(status="unknown_failed_or_censored")
    reference, candidate = pair["ENS-C"], pair["H-ACT"]
    for row in (reference, candidate):
        endpoint = row["endpoint"]
        assert all(isinstance(endpoint[key], (int, float)) and math.isfinite(endpoint[key])
                   for key in ("U", "L", "gap"))
        assert endpoint["U"] >= endpoint["L"] - 1e-7
        assert abs(endpoint["gap"] - (endpoint["U"] - endpoint["L"])) <= 1e-7
    if reference["endpoint"]["certificate"] and candidate["endpoint"]["certificate"]:
        ref_time = reference["completion"]["process_wall_seconds"]
        cand_time = candidate["completion"]["process_wall_seconds"]
        return dict(status="both_certified", reference_seconds=ref_time,
                    candidate_seconds=cand_time, candidate_over_reference_time_ratio=cand_time / ref_time)
    if reference["endpoint"]["certificate"] or candidate["endpoint"]["certificate"]:
        return dict(status="mixed_certification_no_open_gap_median")
    ref_gap = reference["endpoint"]["gap"]
    cand_gap = candidate["endpoint"]["gap"]
    assert ref_gap >= 0 and cand_gap >= 0, "Open numerical gap must be nonnegative"
    return dict(status="both_open", reference_U=reference["endpoint"]["U"],
                reference_L=reference["endpoint"]["L"], reference_gap=ref_gap,
                candidate_U=candidate["endpoint"]["U"],
                candidate_L=candidate["endpoint"]["L"], candidate_gap=cand_gap,
                gap_difference=cand_gap - ref_gap,
                ratio_margin=cand_gap - 1.5 * ref_gap,
                exceeds_original_severe_line=(cand_gap > 1.5 * ref_gap and
                                              cand_gap - ref_gap > 0.01))


def three_seed_summary(r92, seed0: dict, records: list[dict]) -> dict:
    pairs = {0: pair_status(seed0)}
    for seed in (1, 2):
        pairs[seed] = pair_status({row["arm"]: row for row in records if row["seed"] == seed})
    if all(pairs[seed]["status"] == "both_open" for seed in (0, 1, 2)):
        gaps = [pairs[seed] for seed in (0, 1, 2)]
        direction_count = sum(row["gap_difference"] > 0 for row in gaps)
        original_severe_count = sum(row["exceeds_original_severe_line"] for row in gaps)
        median_ratio_margin = statistics.median(row["ratio_margin"] for row in gaps)
        median_gap_difference = statistics.median(row["gap_difference"] for row in gaps)
        reproduced = (direction_count >= 2 and original_severe_count >= 2 and
                      median_ratio_margin > 0 and
                      median_gap_difference > 0.01)
        verdict = "risk_reproduced" if reproduced else "risk_not_reproduced"
    else:
        direction_count = original_severe_count = median_ratio_margin = median_gap_difference = None
        verdict = "mixed_or_censored_no_three_open_gap_median"
    return dict(schema="round92-handling-u6-repeat-three-seed-summary-v1",
                verdict=verdict, pairs_by_seed=pairs,
                upward_gap_direction_seeds=direction_count,
                original_severe_line_seeds=original_severe_count,
                median_candidate_gap_minus_1p5_reference_gap=median_ratio_margin,
                median_candidate_gap_minus_reference_gap=median_gap_difference,
                interpretation="Fixed development risk replication, not algorithm selection or statistical significance."
                               " Do not combine certified times with open gaps; F5/F6 stay unrun.")


def run(r92) -> None:
    prereg = r92.read(PREREG)
    g3, u6, seed0 = validate(r92, prereg)
    identity_path = CAMPAIGN / "identity.json"
    identity = r92.read(identity_path)
    assert identity["schema"] == "round92-handling-u6-repeat-identity-v1"
    assert identity["prereg_sha256"] == r92.sha(PREREG)
    assert identity["wrapper_sha256"] == r92.sha(Path(__file__))
    assert identity["runner_sha256"] == prereg["frozen_g3_runner_sha256"]
    assert identity["gate_sha256"] == r92.sha(ROOT / prereg["prepare_gate_path"])
    assert identity["candidate_binary_sha256"] == prereg["candidate_binary_sha256"]
    assert identity["candidate_core_sha256"] == prereg["candidate_core_sha256"]
    old_gate = r92.read(ROOT / prereg["frozen_g3_qualification_gate"])
    assert identity["source_hashes"] == old_gate["source_hashes"]
    assert identity["harness_hashes"] == r92.harness_hashes()
    assert identity["launches"] == four_launches(r92, prereg, g3, u6)
    lease_path = CAMPAIGN / prereg["run_lease_name"]
    assert r92.read(lease_path) == dict(
        schema="round92-handling-u6-repeat-run-lease-v1",
        identity_sha256=r92.sha(identity_path), authorized_by="root",
        allow_optimize=True, planned_arms=4)
    assert not (CAMPAIGN / "run_started.json").exists(), "Never rerun or resume"
    assert not (CAMPAIGN / "active_run.lock").exists()
    assert not (CAMPAIGN / "summary.jsonl").exists()
    assert all(not Path(row["destination"]).exists() for row in identity["launches"])
    assert not r92.foreign_heavy_processes(), "Foreign solver/build process present"
    started = time.perf_counter()
    r92.write_new(CAMPAIGN / "run_started.json", dict(
        identity_sha256=r92.sha(identity_path), lease_sha256=r92.sha(lease_path),
        started_unix=time.time(), complete_process_runs_planned=4,
        internal_optimize_calls_unbounded_by_arm_count=True))
    records: list[dict] = []
    run_error = None
    postflight = None
    frozen_evidence = r92.evidence
    with (CAMPAIGN / "active_run.lock").open("x", encoding="utf-8") as lock:
        lock.write(json.dumps(dict(pid=os.getpid(), started_unix=time.time())) + "\n")
    try:
        for launch in identity["launches"]:
            seed = launch["seed"]
            seed_dir = CAMPAIGN / f"seed_{seed}"
            if launch["number"] % 2 == 1:
                seed_dir.mkdir(exist_ok=False)
            r92.CAMPAIGN = seed_dir  # Only the independent module object is changed.
            r92.evidence = SeedAwareEvidence(frozen_evidence, seed)
            per_seed = dict(g3, common=dict(g3["common"], gurobi_seed=seed))
            attempt_started = time.perf_counter()
            try:
                record = r92.run_one(launch, per_seed, identity)
                params = native_parameters(r92, launch, record)
                r92.write_new(Path(launch["destination"]) / "native_parameter_evidence.json", params)
                record["seed"] = seed
                records.append(record)
                r92.append_jsonl(CAMPAIGN / "summary.jsonl", dict(
                    seed=seed, record=record, native_parameter_evidence=params))
            except Exception as exc:
                r92.write_new(CAMPAIGN / f'runner_failure_{launch["number"]:02d}.json', dict(
                    schema="round92-handling-u6-repeat-failure-v1", number=launch["number"],
                    seed=seed, arm=launch["arm"], error=repr(exc),
                    attempt_elapsed_seconds=time.perf_counter() - attempt_started,
                    destination=launch["destination"],
                    destination_exists=Path(launch["destination"]).exists(),
                    requires_independent_review=True, recorded_unix=time.time()))
                raise
            if launch["number"] % 2 == 0:
                pair = {row["arm"]: row for row in records if row["seed"] == seed}
                assert set(pair) == {"ENS-C", "H-ACT"}
                r92.cross_arm_contradiction(list(pair.values()), "U6")
                signals = r92.severe_risk_signal(list(pair.values()), "U6")
                r92.write_new(seed_dir / "runner_repeat_risk_signal.json", dict(
                    seed=seed, signals=signals, research_signal_only=True,
                    performance_signals_do_not_stop_seed_2=True,
                    summary_sha256=r92.sha(CAMPAIGN / "summary.jsonl")))
        r92.write_new(CAMPAIGN / "three_seed_summary.json", three_seed_summary(r92, seed0, records))
    except Exception as exc:
        run_error = repr(exc)
        raise
    finally:
        (CAMPAIGN / "active_run.lock").unlink(missing_ok=True)
        postflight_started = time.perf_counter()
        try:
            source_checks = [dict(path=row["path"], expected_sha256=row["sha256"],
                                  actual_sha256=r92.sha(ROOT / row["path"]))
                             for row in identity["source_hashes"]]
            main_sha = r92.sha(ROOT / prereg["candidate_binary"])
            core_sha = r92.sha(ROOT / "build/research/round92-handling-activation/libexact_ebrp_core.a")
            residual = r92.foreign_heavy_processes()
            postflight = dict(
                schema="round92-handling-u6-repeat-postflight-v1",
                source_checks=source_checks, source_hashes_match=all(
                    row["actual_sha256"] == row["expected_sha256"] for row in source_checks),
                main_sha256=main_sha, main_matches=main_sha == prereg["candidate_binary_sha256"],
                core_sha256=core_sha, core_matches=core_sha == prereg["candidate_core_sha256"],
                residual_heavy_processes=residual, no_residual_heavy_processes=not residual,
                captured_unix=time.time())
            postflight["passed"] = (postflight["source_hashes_match"] and
                                    postflight["main_matches"] and postflight["core_matches"] and
                                    postflight["no_residual_heavy_processes"])
        except Exception as exc:
            postflight = dict(schema="round92-handling-u6-repeat-postflight-v1",
                              passed=False, error=repr(exc), captured_unix=time.time())
        postflight["wall_seconds"] = time.perf_counter() - postflight_started
        r92.write_new(CAMPAIGN / "postflight.json", postflight)
        r92.write_new(CAMPAIGN / "run_completion.json", dict(
            schema="round92-handling-u6-repeat-run-completion-v1", planned=4,
            completed=len(records), error=run_error,
            process_wall_seconds=sum(row["completion"]["process_wall_seconds"] for row in records),
            runner_wall_seconds=time.perf_counter() - started,
            postflight_passed=postflight["passed"],
            failed_attempt_costs=[r92.read(path) for path in sorted(CAMPAIGN.glob("runner_failure_*.json"))],
            ended_unix=time.time()))
    if not postflight["passed"]:
        raise RuntimeError("Postflight source/binary/process identity failed; retain all evidence")


def main() -> None:
    assert len(sys.argv) == 2 and sys.argv[1] in {"prepare", "run"}, \
        "Usage: round92_handling_u6_repeat.py prepare|run"
    r92 = frozen_runner()
    if sys.argv[1] == "prepare":
        prepare(r92)
    else:
        run(r92)


if __name__ == "__main__":
    main()
