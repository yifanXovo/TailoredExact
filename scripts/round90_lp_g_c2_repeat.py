"""Conditional C2 seed-repeat wrapper around the frozen Round90 G3 runner.

Importing this file starts no work.  `prepare` requires a new root gate and
performs zero Optimize calls; `run` additionally requires a separate lease.
The four commands are the frozen C2 command with only Seed and output changed.
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
PREREG = ROOT / "results/unified_exact_round90/preregistration_c2_repeat.json"
CAMPAIGN = ROOT / "results/unified_exact_round90/runner_lp_g_c2_repeat"


def frozen_runner():
    """Load a distinct module object; never mutate the historical module/file."""
    path = ROOT / "scripts/round90_lp_g_g3.py"
    spec = importlib.util.spec_from_file_location("round90_lp_g_g3_c2_repeat_frozen", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.CAMPAIGN == ROOT / "results/unified_exact_round90/runner_lp_g_g3"
    return module


def pinned_file(r90, path: str, digest: str) -> None:
    assert r90.sha(ROOT / path) == digest, path


def seed0_reference(r90, prereg: dict) -> dict:
    old = prereg["seed0_reference"]
    assert old["status"] == "completed_certified_same_new_binary_not_rerun"
    for name in ("g3_summary", "g3_independent_review", "g3_cross_arm"):
        pinned_file(r90, old[name + "_path"], old[name + "_sha256"])
    assert r90.read(ROOT / old["g3_cross_arm_path"])["passed"] is True
    summary = [json.loads(line) for line in
               (ROOT / old["g3_summary_path"]).read_text(encoding="utf-8").splitlines()]
    assert len(summary) == 16
    pair = {row["arm"]: row for row in summary if row["id"] == "C2"}
    assert set(pair) == {"ENS-C", "LP-G"}
    for arm, receipt in old["arms"].items():
        folder = ROOT / receipt["raw"]
        for name in ("launch", "audit", "completion", "result"):
            assert r90.sha(folder / (name + ".json")) == receipt[name + "_sha256"]
        row = pair[arm]
        assert Path(row["destination"]) == folder.resolve()
        assert row["audit_passed"] and row["endpoint"]["certificate"]
        assert row["completion"]["stop_reason"] == "normal_return"
        assert row["completion"]["process_cap_seconds"] == 600
        assert r90.read(folder / "audit.json")["passed"] is True
        assert r90.read(folder / "result.json")["gurobi_seed_effective"] == 0
    return pair


def validate(r90, prereg: dict) -> tuple[dict, dict, dict]:
    assert os.name == "nt", "Windows-only study"
    assert prereg["schema"] == "round90-lp-g-c2-repeat-preregistration-v1"
    assert prereg["status"] == "conditional_source_only_no_execution"
    assert prereg["runtime_root"] == str(CAMPAIGN.relative_to(ROOT)).replace("\\", "/")
    assert prereg["planned_runs"] == 4 and prereg["sum_process_caps_seconds"] == 2400
    assert prereg["no_component_time_or_work_slices"] is True
    assert prereg["prepare_does_not_authorize_optimize"] is True
    assert prereg["run_requires_separate_root_lease"] is True
    assert prereg["repeat_order"] == [
        {"seed": 1, "method_order": ["ENS-C", "LP-G"]},
        {"seed": 2, "method_order": ["LP-G", "ENS-C"]}]
    pinned_file(r90, prereg["frozen_g3_runner"], prereg["frozen_g3_runner_sha256"])
    pinned_file(r90, prereg["frozen_g3_preregistration"],
                prereg["frozen_g3_preregistration_sha256"])
    pinned_file(r90, prereg["frozen_g3_qualification_gate"],
                prereg["frozen_g3_qualification_gate_sha256"])
    g3 = r90.read(ROOT / prereg["frozen_g3_preregistration"])
    old_gate = r90.read(ROOT / prereg["frozen_g3_qualification_gate"])
    assert old_gate["qualified"] and old_gate["authorized_by"] == "root"
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
        threads=1, mip_threads=1, gurobi_presolve=-1, affinity_mask=4,
        native_limit_offset_seconds=6, hard_stop_offset_seconds=2,
        shutdown_margin_seconds=3, requested_mip_gap=0, requested_mip_gap_abs=0)
    c2 = next(row for row in g3["panel"] if row["id"] == "C2")
    assert sum(row["id"] == "C2" for row in g3["panel"]) == 1
    assert prereg["c2"] == {key: c2[key] for key in prereg["c2"]}
    assert prereg["c2"]["cap_seconds"] == 600
    pinned_file(r90, c2["input_path"], c2["input_sha256"])
    seed0 = seed0_reference(r90, prereg)
    return g3, c2, seed0


def four_launches(r90, prereg: dict, g3: dict, c2: dict) -> list[dict]:
    launches: list[dict] = []
    for planned in prereg["repeat_order"]:
        seed = planned["seed"]
        for arm in planned["method_order"]:
            number = len(launches) + 1
            within_seed = 1 + (number - 1) % 2
            destination = CAMPAIGN / f"seed_{seed}" / "raw" / f"{within_seed:02d}_C2_{arm}"
            baseline = r90.command_for(g3, c2, arm, destination)
            positions = [index for index, value in enumerate(baseline) if value == "--gurobi-seed"]
            assert positions == [baseline.index("--gurobi-seed")]
            index = positions[0] + 1
            assert baseline[index] == "0"
            command = baseline.copy()
            command[index] = str(seed)
            assert command[:index] + ["0"] + command[index + 1:] == baseline
            assert command.count("--gurobi-seed") == 1
            assert command[command.index("--round90-lp-g-split") + 1] == (
                "true" if arm == "LP-G" else "false")
            assert "--round88-constructive-only-descent" not in command
            assert "--round89-native-ot-b1" not in command
            assert command[command.index("--threads") + 1] == "1"
            assert command[command.index("--mip-threads") + 1] == "1"
            assert command[command.index("--gurobi-presolve") + 1] == "-1"
            assert command[command.index("--time-limit") + 1] == "594"
            assert command[command.index("--process-wall-time-limit") + 1] == "600"
            launches.append(dict(
                number=number, id="C2", arm=arm, seed=seed, stage="repeat",
                panel=dict(c2, instance_path=c2["input_path"]),
                destination=str(destination), cap_seconds=600,
                hard_stop_seconds=598, command=command))
    assert [(row["seed"], row["arm"]) for row in launches] == [
        (1, "ENS-C"), (1, "LP-G"), (2, "LP-G"), (2, "ENS-C")]
    assert sum(row["cap_seconds"] for row in launches) == 2400
    assert len({row["destination"] for row in launches}) == 4
    return launches


def prepare(r90) -> None:
    prereg = r90.read(PREREG)
    g3, c2, _ = validate(r90, prereg)
    launches = four_launches(r90, prereg, g3, c2)
    gate_path = ROOT / prereg["prepare_gate_path"]
    gate = r90.read(gate_path)  # Root creates this after static review.
    assert gate == dict(
        schema="round90-lp-g-c2-repeat-prepare-gate-v1", authorized_by="root",
        allow_prepare=True, allow_optimize=False,
        prereg_sha256=r90.sha(PREREG), wrapper_sha256=r90.sha(Path(__file__)),
        frozen_runner_sha256=prereg["frozen_g3_runner_sha256"],
        g3_summary_sha256=prereg["seed0_reference"]["g3_summary_sha256"],
        g3_independent_review_sha256=prereg["seed0_reference"]["g3_independent_review_sha256"],
        candidate_binary_sha256=prereg["candidate_binary_sha256"])
    assert not CAMPAIGN.exists(), "Never overwrite, resume, or splice a campaign"
    assert not r90.foreign_heavy_processes(), "Foreign solver/build process present"
    CAMPAIGN.mkdir(parents=True, exist_ok=False)
    identity = dict(
        schema="round90-lp-g-c2-repeat-identity-v1", optimizer_calls=0,
        prereg_sha256=r90.sha(PREREG), wrapper_sha256=r90.sha(Path(__file__)),
        runner_sha256=prereg["frozen_g3_runner_sha256"], gate_sha256=r90.sha(gate_path),
        candidate_binary_sha256=prereg["candidate_binary_sha256"],
        source_commit=prereg["source_commit"], source_hashes=prereg["source_hashes"],
        harness_hashes=prereg["harness_hashes"], launches=launches,
        prepared_unix=time.time())
    r90.write_new(CAMPAIGN / "identity.json", identity)
    r90.write_new(CAMPAIGN / "preflight.json", dict(
        optimizer_calls=0, prepared_without_solver=True, planned_runs=4,
        process_cap_sum_seconds=2400, input_hash_verified=True,
        seed0_reference_certified=True, source_binary_harness_verified=True,
        disk_free_bytes=shutil.disk_usage(CAMPAIGN).free,
        memory_available_bytes=r90.memory_available(),
        note="A distinct root run lease is still required."))
    print(json.dumps(dict(prepared=True, optimizer_calls=0, campaign=str(CAMPAIGN))), flush=True)


def native_parameters(r90, launch: dict, record: dict) -> dict:
    destination = Path(launch["destination"])
    reason = record["completion"]["stop_reason"]
    result_path = destination / "result.json"
    if reason != "normal_return" or not result_path.is_file():
        return dict(status="unknown_censored_or_missing_result", seed=launch["seed"],
                    command_sha256=r90.sha(destination / "launch.json"))
    result = r90.read(result_path)
    for key, expected in dict(
        gurobi_seed_requested=launch["seed"], gurobi_seed_effective=launch["seed"],
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
    return dict(status="native_result_readback_verified", seed=launch["seed"],
                result_sha256=r90.sha(result_path), algorithm_preset=expected_identity,
                gurobi_seed_effective=result["gurobi_seed_effective"],
                gurobi_threads_effective=result["gurobi_threads_effective"],
                gurobi_presolve_effective=result["gurobi_presolve_effective"])


def certified_pair(pair: dict) -> dict:
    if set(pair) != {"ENS-C", "LP-G"}:
        return dict(status="incomplete_or_censored", reason="missing_arm")
    if not all(row["audit_passed"] and row["endpoint"] is not None and
               row["endpoint"]["certificate"] and
               row["completion"]["stop_reason"] == "normal_return"
               for row in pair.values()):
        return dict(status="incomplete_or_censored",
                    reason="uncertified_failed_audit_or_non_normal_completion")
    ref = pair["ENS-C"]["completion"]["process_wall_seconds"]
    cand = pair["LP-G"]["completion"]["process_wall_seconds"]
    assert ref > 0 and cand > 0 and math.isfinite(ref) and math.isfinite(cand)
    return dict(status="both_certified", ens_c_seconds=ref, lp_g_seconds=cand,
                lp_g_over_ens_c_ratio=cand / ref,
                direction="LP-G faster" if cand < ref else "ENS-C faster" if cand > ref else "tie")


def run(r90) -> None:
    prereg = r90.read(PREREG)
    g3, c2, seed0 = validate(r90, prereg)
    identity_path = CAMPAIGN / "identity.json"
    identity = r90.read(identity_path)
    assert identity["schema"] == "round90-lp-g-c2-repeat-identity-v1"
    assert identity["prereg_sha256"] == r90.sha(PREREG)
    assert identity["wrapper_sha256"] == r90.sha(Path(__file__))
    assert identity["runner_sha256"] == prereg["frozen_g3_runner_sha256"]
    assert identity["gate_sha256"] == r90.sha(ROOT / prereg["prepare_gate_path"])
    assert identity["candidate_binary_sha256"] == prereg["candidate_binary_sha256"]
    assert identity["source_hashes"] == prereg["source_hashes"]
    assert identity["harness_hashes"] == prereg["harness_hashes"]
    assert identity["launches"] == four_launches(r90, prereg, g3, c2)
    lease = r90.read(CAMPAIGN / prereg["run_lease_name"])
    assert lease == dict(schema="round90-lp-g-c2-repeat-run-lease-v1",
                         identity_sha256=r90.sha(identity_path),
                         authorized_by="root", allow_optimize=True, planned_runs=4)
    assert not (CAMPAIGN / "run_started.json").exists(), "Never rerun or resume"
    assert not (CAMPAIGN / "active_run.lock").exists()
    assert not (CAMPAIGN / "summary.jsonl").exists()
    assert all(not Path(row["destination"]).exists() for row in identity["launches"])
    assert not r90.foreign_heavy_processes(), "Foreign solver/build process present"
    started = time.perf_counter()
    r90.write_new(CAMPAIGN / "run_started.json", dict(
        identity_sha256=r90.sha(identity_path), lease_sha256=r90.sha(CAMPAIGN / prereg["run_lease_name"]),
        started_unix=time.time(), complete_process_runs_planned=4,
        internal_optimize_calls_unbounded_by_arm_count=True))
    records: list[dict] = []
    run_error = None
    with (CAMPAIGN / "active_run.lock").open("x", encoding="utf-8") as lock:
        lock.write(json.dumps(dict(pid=os.getpid(), started_unix=time.time())) + "\n")
    try:
        for launch in identity["launches"]:
            seed = launch["seed"]
            seed_dir = CAMPAIGN / f"seed_{seed}"
            if launch["number"] % 2 == 1:
                seed_dir.mkdir(exist_ok=False)
            r90.CAMPAIGN = seed_dir  # Only this independently loaded module object.
            per_seed = dict(g3, common=dict(g3["common"], gurobi_seed=seed))
            attempt_started = time.perf_counter()
            try:
                record = r90.run_one(launch, per_seed, identity)
                params = native_parameters(r90, launch, record)
                r90.write_new(Path(launch["destination"]) / "native_parameter_evidence.json", params)
                assert params["status"] == "native_result_readback_verified" or (
                    record["completion"]["stop_reason"] != "normal_return")
                record["seed"] = seed
                records.append(record)
                r90.append_jsonl(CAMPAIGN / "summary.jsonl", dict(seed=seed, record=record,
                                                                     native_parameter_evidence=params))
            except Exception as exc:
                r90.write_new(CAMPAIGN / f'runner_failure_{launch["number"]:02d}.json', dict(
                    schema="round90-lp-g-c2-repeat-failure-v1", number=launch["number"],
                    seed=seed, arm=launch["arm"], error=repr(exc),
                    attempt_elapsed_seconds=time.perf_counter() - attempt_started,
                    destination=launch["destination"],
                    destination_exists=Path(launch["destination"]).exists(),
                    requires_independent_review=True, recorded_unix=time.time()))
                raise
            if launch["number"] % 2 == 0:
                pair = {row["arm"]: row for row in records if row["seed"] == seed}
                assert set(pair) == {"ENS-C", "LP-G"}
                r90.cross_arm_contradiction(list(pair.values()), "C2")
                signal = r90.severe_risk_signal(list(pair.values()), "C2")
                if signal:
                    r90.write_new(seed_dir / "runner_repeat_risk_stop.json", dict(
                        seed=seed, signals=signal, research_signal_only=True,
                        requires_paired_review=True,
                        summary_sha256=r90.sha(CAMPAIGN / "summary.jsonl")))
                    raise RuntimeError("Severe paired signal; stop before next seed")
        pairs = {0: certified_pair(seed0)}
        for seed in (1, 2):
            pairs[seed] = certified_pair({row["arm"]: row for row in records
                                          if row["seed"] == seed})
        ratios = [pairs[seed]["lp_g_over_ens_c_ratio"] for seed in (0, 1, 2)
                  if pairs[seed]["status"] == "both_certified"]
        r90.write_new(CAMPAIGN / "three_pair_summary.json", dict(
            schema="round90-lp-g-c2-repeat-three-pair-summary-v1",
            pairs_by_seed=pairs, certified_pairs=len(ratios),
            median_certified_lp_g_over_ens_c_ratio=(statistics.median(ratios)
                                                       if ratios else None),
            censored_seeds=[seed for seed in (0, 1, 2)
                            if pairs[seed]["status"] != "both_certified"],
            interpretation="Development fluctuation check only; no significance or promotion."
                           " D6/F2/other protection remains open."))
    except Exception as exc:
        run_error = repr(exc)
        raise
    finally:
        (CAMPAIGN / "active_run.lock").unlink(missing_ok=True)
        r90.write_new(CAMPAIGN / "run_completion.json", dict(
            schema="round90-lp-g-c2-repeat-run-completion-v1", planned=4,
            completed=len(records), error=run_error,
            process_wall_seconds=sum(row["completion"]["process_wall_seconds"] for row in records),
            full_outer_wall_seconds=time.perf_counter() - started,
            failed_attempt_costs=[r90.read(path) for path in sorted(CAMPAIGN.glob("runner_failure_*.json"))],
            ended_unix=time.time()))


def main() -> None:
    assert len(sys.argv) == 2 and sys.argv[1] in {"prepare", "run"}, \
        "Usage: round90_lp_g_c2_repeat.py prepare|run"
    r90 = frozen_runner()
    if sys.argv[1] == "prepare":
        prepare(r90)
    else:
        run(r90)


if __name__ == "__main__":
    main()
