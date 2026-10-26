"""Read-only optimizer-free analysis of the user-closed first five R87 pairs.

The original 18-run protocol and its analyzer remain frozen. This entry point
independently replays the ten completed arms and labels the interrupted eighth
arm's reconstructed observation times as bounds rather than exact times.
"""
import json
from pathlib import Path
import time

import round86_native_evidence as evidence
import round87_analyze as base


ROOT, STAGE, OUT = base.ROOT, base.STAGE, base.OUT
PAIR_IDS = ("D6", "D7", "U6", "F2", "F5")
FORMAL_RUNS = 10


def interrupted_target_time(done, target, optimum_known, receipt_closes, recovery):
    label = "t_find_star" if optimum_known else "first_final_UB"
    if target is None:
        return dict(target_objective=None, time_seconds=None, lower_bound_seconds=None,
                    upper_bound_seconds=None, precision="unavailable", label="unavailable")
    candidates = [w for w in done["audit"].get("witnesses", [])
                  if abs(w["F"] - target) <= base.TOLERANCE]
    if not candidates:
        return dict(target_objective=target, time_seconds=None, lower_bound_seconds=None,
                    upper_bound_seconds=None, precision="not_observed", label=label)
    lower = min(receipt_closes[w["sequence"]] for w in candidates)
    upper = min(recovery["last_original_driver_status_seconds"]
                if w["sequence"] <= recovery["original_driver_observed_commits"]
                else recovery["last_commit_close_seconds"] for w in candidates)
    assert lower <= upper <= done["wall_seconds"]
    return dict(target_objective=target, time_seconds=None, lower_bound_seconds=lower,
                upper_bound_seconds=upper, precision="committed_receipt_to_observation_upper_bound",
                label=label)


def main():
    started = time.perf_counter()
    assert not (OUT / "analysis.json").exists(), "Do not overwrite a completed analysis"
    assert not (OUT / "driver_completion.json").exists(), "This is an early-closed partial campaign"
    summary = base.read(OUT / "summary.json")
    identity = base.read(OUT / "identity.json")
    protocol = base.read(STAGE / "protocol.json")
    raw_campaign = Path(identity["runtime_root"]) / "campaign"
    recovery = base.read(raw_campaign / "quota_interruption_recovery" / "manifest.json")
    assert base.read(raw_campaign / "summary.json") == summary
    assert summary["completed"] == len(summary["records"]) == FORMAL_RUNS
    assert summary["planned"] == len(identity["launches"]) == protocol["limits"]["planned_runs"] == 18
    assert summary["completed_pairs"] == len(PAIR_IDS)
    assert tuple(p["id"] for p in protocol["panel"][:5]) == PAIR_IDS
    assert all(row["audit"]["passed"] for row in summary["records"])
    assert summary["records"][7]["stop_reason"] == "quota_interrupted"
    assert recovery["run_number"] == 8 and recovery["optimality_certificate"] is False
    assert base.sha(STAGE / "protocol.json") == identity["protocol_sha256"]
    assert base.sha(STAGE / "plan.md") == identity["plan_sha256"]
    assert base.sha(ROOT / "scripts/round87_research.py") == identity["driver_sha256"]
    assert base.sha(evidence.__file__) == identity["reader_sha256"]
    assert base.sha(identity["binary_path"]) == identity["binary_sha256"]
    launches = identity["launches"][:FORMAL_RUNS]
    endpoints, trajectories, witnesses, receipt_closes, raw_index = [], [], [], {}, []
    for launch, done in zip(launches, summary["records"]):
        assert (launch["number"], launch["panel"]["id"], launch["arm"]) == (
            done["number"], done["id"], done["arm"])
        destination = Path(launch["destination"])
        assert base.read(destination / "launch.json") == launch
        assert base.read(destination / "completion.json")["stop_reason"] == done["stop_reason"]
        observations = base.read(destination / "observations.json")
        assert len(observations) == done["observed_commits"]
        for expected, row in enumerate(observations, 1):
            assert row["sequence"] == expected
            checked = evidence.receipt(destination / "journal" / f"event_{expected}.commit",
                                       row["first_observed_seconds"], launch["cap"])
            assert checked == row
        replay = evidence.audit(ROOT, launch["panel"], observations, identity["binary_sha256"])
        for key in ("UB", "LB", "native_calls_started", "native_calls_returned", "physical_witnesses"):
            assert replay[key] == done["audit"][key], (done["number"], key)
        result = base.read(destination / "result.json") if done["stop_reason"] == "normal_return" else None
        evidence.finalize_endpoint(ROOT, launch["panel"], launch["arm"], replay, observations,
                                   result, done["stop_reason"], identity["references"][done["id"]])
        assert replay["endpoint"] == done["audit"]["endpoint"]
        endpoint = replay["endpoint"]
        gap, relative = base.gap_fields(endpoint["U"], endpoint["L"])
        recovered = done["number"] == 8
        endpoints.append(dict(number=done["number"], id=done["id"], arm=done["arm"],
                              V=launch["panel"]["V"], M=launch["panel"]["M"],
                              Q=launch["panel"]["Q"], T_seconds=launch["panel"]["T_seconds"],
                              process_exit_seconds=None if recovered else done["wall_seconds"],
                              process_exit_lower_bound_seconds=done["wall_seconds"] if recovered else None,
                              stop_reason=done["stop_reason"], U=endpoint["U"], L=endpoint["L"],
                              gap=gap, relative_gap=relative, certificate=endpoint["certificate"],
                              t_cert=done["wall_seconds"] if endpoint["certificate"] else None,
                              censored=not endpoint["certificate"], status=endpoint["status"],
                              source=endpoint["source"],
                              time_precision="last_commit_lower_bound_on_exit" if recovered else "observed_process_exit"))
        if recovered:
            receipt_closes = {row["sequence"]: row["data_close_seconds"] for row in observations
                              if row["payload"]["kind"] == "witness"}
            for seconds in base.checkpoint_times(launch["cap"]):
                if seconds < recovery["last_original_driver_status_seconds"]:
                    trajectories.append(dict(number=8, id=done["id"], arm=done["arm"],
                        seconds=seconds, U=None, L=None, gap=None, relative_gap=None,
                        certificate=False, source="observation_timing_unavailable_after_quota_interruption"))
            last = base.read(raw_campaign / "quota_interruption_recovery" / "last_original_runtime_status.json")
            assert last["committed_events"] == recovery["original_driver_observed_commits"]
            trajectories.append(dict(number=8, id=done["id"], arm=done["arm"],
                seconds=last["process_seconds"], U=last["latest_verified_UB"],
                L=last["latest_global_LB"], gap=last["gap"],
                relative_gap=last["gap"] / abs(last["latest_verified_UB"]),
                certificate=False, source="original_driver_observed_status"))
            trajectories.append(dict(number=8, id=done["id"], arm=done["arm"],
                seconds=recovery["last_commit_close_seconds"], U=endpoint["U"], L=endpoint["L"],
                gap=gap, relative_gap=relative, certificate=False,
                source="replayed_final_committed_evidence_exit_time_unknown"))
        else:
            for seconds in base.checkpoint_times(launch["cap"]):
                trajectories.append(dict(number=done["number"], id=done["id"], arm=done["arm"],
                                         seconds=seconds, **base.checkpoint(observations, done, seconds)))
        for witness in replay["witnesses"]:
            witnesses.append(dict(number=done["number"], id=done["id"], arm=done["arm"],
                sequence=witness["sequence"], available_seconds=None if recovered else witness["available"],
                earliest_possible_seconds=receipt_closes[witness["sequence"]] if recovered else None,
                latest_known_seconds=witness["available"] if recovered else None,
                objective=witness["F"], G=witness["G"], P=witness["P"],
                source=witness["source"], call=witness["call"],
                time_precision="interval" if recovered else "observed_committed_witness"))
        for name in ("launch.json", "completion.json", "observations.json", "audit.json", "result.json",
                     "native.log", "progress.csv", "phases.csv", "compact.lp"):
            path = destination / name
            if path.is_file():
                raw_index.append(dict(number=done["number"], id=done["id"], arm=done["arm"],
                                      path=str(path), bytes=path.stat().st_size, sha256=base.sha(path)))
        print(json.dumps(dict(independently_replayed=done["number"], id=done["id"],
                              arm=done["arm"], certificate=endpoint["certificate"])), flush=True)
    certified_objectives = {}
    for panel_id in PAIR_IDS:
        values = [row["U"] for row in endpoints if row["id"] == panel_id and row["certificate"]]
        if values:
            assert max(values) - min(values) <= base.TOLERANCE
            certified_objectives[panel_id] = min(values)
    discovery = []
    for done in summary["records"]:
        optimum = certified_objectives.get(done["id"])
        target = optimum if optimum is not None else done["audit"]["endpoint"]["U"]
        if done["number"] == 8:
            observed = interrupted_target_time(done, target, optimum is not None, receipt_closes, recovery)
        else:
            observed = base.target_time(done, target, optimum is not None)
            observed["lower_bound_seconds"] = None
            observed["upper_bound_seconds"] = None
        t_cert = done["wall_seconds"] if done["audit"]["endpoint"]["certificate"] else None
        exact_find = observed["time_seconds"] if observed["precision"] == "observed_committed_witness" else None
        discovery.append(dict(number=done["number"], id=done["id"], arm=done["arm"],
            optimum_known=optimum is not None, **observed, t_cert=t_cert,
            t_tail=t_cert - exact_find if t_cert is not None and exact_find is not None else None,
            tail_note="exact_from_observed_witness" if t_cert is not None and exact_find is not None
                      else "unknown_or_only_bounded"))
    pairs, cross_checks = [], []
    for panel in protocol["panel"][:5]:
        p, ens = ({row["arm"]: row for row in endpoints if row["id"] == panel["id"]}[arm]
                  for arm in ("P-GRB", "ENS-C"))
        if p["certificate"] and ens["certificate"]:
            classification, winner = "both_certified", "ENS-C" if ens["t_cert"] < p["t_cert"] else "P-GRB" if p["t_cert"] < ens["t_cert"] else "tie"
            ratio, difference = p["t_cert"] / ens["t_cert"], p["t_cert"] - ens["t_cert"]
        elif p["certificate"] or ens["certificate"]:
            classification = ("ens_certified_p_administratively_censored" if panel["id"] == "F2" else
                              "ens_certified_p_censored" if ens["certificate"] else "p_certified_ens_censored")
            winner = "ENS-C_observed_advantage_before_P_interruption" if panel["id"] == "F2" else \
                     "ENS-C_budget_advantage" if ens["certificate"] else "P-GRB_budget_advantage"
            ratio = difference = None
        else:
            classification, winner, ratio, difference = "both_censored", "ordering_not_established", None, None
        pairs.append(dict(id=panel["id"], V=panel["V"], M=panel["M"], Q=panel["Q"],
            T_seconds=panel["T_seconds"], classification=classification, winner=winner,
            p_t_cert=p["t_cert"], ens_t_cert=ens["t_cert"], p_over_ens_t_cert=ratio,
            p_minus_ens_seconds=difference, p_U=p["U"], p_L=p["L"], p_gap=p["gap"],
            ens_U=ens["U"], ens_L=ens["L"], ens_gap=ens["gap"]))
        strongest = max(p["L"], ens["L"])
        best = min(row["U"] for row in (p, ens) if row["U"] is not None)
        assert strongest <= best + base.TOLERANCE
        cross_checks.append(dict(id=panel["id"], maximum_same_run_global_L=strongest,
            minimum_independent_physical_U=best, passed=True,
            scope="offline contradiction check only; never a combined algorithm endpoint"))
    excluded = Path(identity["launches"][10]["destination"])
    assert excluded.is_dir() and not (excluded / "completion.json").exists()
    excluded_index = [dict(path=str(path), bytes=path.stat().st_size, sha256=base.sha(path))
                      for path in sorted(excluded.rglob("*")) if path.is_file()]
    base.write_csv(STAGE / "endpoints.csv", endpoints)
    base.write_csv(STAGE / "paired_comparison.csv", pairs)
    base.write_csv(STAGE / "checkpoint_trajectories.csv", trajectories)
    base.write_csv(STAGE / "discovery_and_tail.csv", discovery)
    base.write_csv(STAGE / "witness_index.csv", witnesses)
    base.write_csv(STAGE / "raw_artifact_index.csv", raw_index)
    base.write_csv(STAGE / "excluded_run11_raw_index.csv", excluded_index)
    base.write(STAGE / "independent_validation.json", dict(
        all_formal_runs_replayed=True, runs=FORMAL_RUNS, completed_pairs=len(PAIR_IDS),
        all_formal_run_audits_passed=True, cross_arm_checks=cross_checks,
        certified_roles=sorted(certified_objectives), certified_objectives=certified_objectives,
        witness_rows=len(witnesses), raw_index_rows=len(raw_index),
        excluded_run11_raw_index_rows=len(excluded_index), optimizer_calls=0,
        numerical_certificate_only=True, strict_rational_proof=False,
        original_planned_runs=18, user_closed_after_run=10))
    base.write(OUT / "partial_completion.json", dict(
        schema="round87-user-closed-partial-completion-v1", original_planned_runs=18,
        completed_formal_runs=FORMAL_RUNS, completed_pairs=len(PAIR_IDS),
        all_formal_runs_valid=True, incomplete_original_protocol=True,
        user_scope_change="stop_after_tenth_completed_run_due_to_time_budget",
        excluded_started_run=11, runs_12_through_18_started=False,
        original_driver_completion_exists=False,
        summary_sha256=base.sha(OUT / "summary.json"),
        scope_amendment_sha256=base.sha(STAGE / "scope_amendment_2026-09-26.md")))
    analysis = dict(schema="round87-partial-analysis-v1", completed_pairs=len(pairs),
        original_planned_pairs=9, both_certified=sum(p["classification"] == "both_certified" for p in pairs),
        one_certified=sum("certified" in p["classification"] and p["classification"] != "both_certified" for p in pairs),
        both_censored=sum(p["classification"] == "both_censored" for p in pairs),
        optimizer_calls=0, wall_seconds=time.perf_counter() - started,
        endpoint_rows=len(endpoints), checkpoint_rows=len(trajectories),
        discovery_rows=len(discovery), script_sha256=base.sha(__file__))
    base.write(OUT / "analysis.json", analysis)
    print(json.dumps(analysis, indent=2), flush=True)


if __name__ == "__main__":
    main()
