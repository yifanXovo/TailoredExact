"""Offline Round 87 convergence analysis. This script never starts an optimizer."""
import csv
import hashlib
import json
import math
from pathlib import Path
import time

import round86_native_evidence as evidence


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "results/unified_exact_round87"
OUT = STAGE / "campaign"
TOLERANCE = 1e-7


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_csv(path, rows):
    rows = list(rows)
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with Path(path).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def checkpoint_times(cap):
    return [300, 600, 1200, 1800, 3600, 7200, *range(10800, cap + 1, 3600)]


def gap_fields(upper, lower):
    gap = upper - lower if upper is not None else None
    relative = gap / abs(upper) if upper not in (None, 0) else None
    return gap, relative


def checkpoint(observations, done, seconds):
    endpoint = done["audit"]["endpoint"]
    if done["stop_reason"] == "normal_return" and done["wall_seconds"] <= seconds:
        gap, relative = gap_fields(endpoint["U"], endpoint["L"])
        return dict(U=endpoint["U"], L=endpoint["L"], gap=gap, relative_gap=relative,
                    certificate=endpoint["certificate"], source="normal_endpoint_carry_forward")
    visible = [row["payload"] for row in observations if row["effective_available_seconds"] <= seconds]
    upper_values = [row["objective"] for row in visible if row["kind"] == "witness"]
    lower_values = [row["global_bound"] for row in visible
                    if row["kind"] == "bound" and row["global_available"]]
    upper = min(upper_values) if upper_values else None
    lower = max([0.0, *lower_values])
    gap, relative = gap_fields(upper, lower)
    if upper is not None:
        assert lower <= upper + TOLERANCE
    return dict(U=upper, L=lower, gap=gap, relative_gap=relative, certificate=False,
                source="committed_same_run_evidence" if upper is not None else "no_verified_UB")


def target_time(done, target, optimum_known):
    if target is None:
        return dict(target_objective=None, time_seconds=None, precision="unavailable", label="unavailable")
    candidates = [w["available"] for w in done["audit"].get("witnesses", [])
                  if abs(w["F"] - target) <= TOLERANCE]
    label = "t_find_star" if optimum_known else "first_final_UB"
    if candidates:
        return dict(target_objective=target, time_seconds=min(candidates), precision="observed_committed_witness", label=label)
    final = done["audit"].get("final_physical_verification")
    if final is not None and abs(final["F"] - target) <= TOLERANCE:
        return dict(target_objective=target, time_seconds=done["wall_seconds"], precision="exit_time_upper_bound", label=label)
    return dict(target_objective=target, time_seconds=None, precision="not_observed", label=label)


def main():
    started = time.perf_counter()
    assert not (OUT / "analysis.json").exists(), "Never replace the closed Round 87 analysis"
    completion = read(OUT / "driver_completion.json")
    summary = read(OUT / "summary.json")
    identity = read(OUT / "identity.json")
    protocol = read(STAGE / "protocol.json")
    assert completion["all_valid"] and completion["completed"] == completion["planned"] == 18
    assert summary["completed"] == summary["planned"] == 18
    assert sha(STAGE / "protocol.json") == identity["protocol_sha256"]
    assert sha(STAGE / "plan.md") == identity["plan_sha256"]
    assert sha(ROOT / "scripts/round87_research.py") == identity["driver_sha256"]
    assert sha(evidence.__file__) == identity["reader_sha256"]
    assert sha(identity["binary_path"]) == identity["binary_sha256"]
    launches = identity["launches"]
    assert len(launches) == len(summary["records"]) == 18
    endpoints = []
    trajectories = []
    witnesses = []
    observations_by_number = {}
    for launch, done in zip(launches, summary["records"]):
        assert (launch["number"], launch["panel"]["id"], launch["arm"]) == (done["number"], done["id"], done["arm"])
        assert done["audit"]["passed"]
        destination = Path(launch["destination"])
        observations = read(destination / "observations.json")
        observations_by_number[launch["number"]] = observations
        assert read(destination / "launch.json") == launch
        for row in observations:
            checked = evidence.receipt(destination / "journal" / f'event_{row["sequence"]}.commit',
                                       row["first_observed_seconds"], launch["cap"])
            assert checked == row
        replay = evidence.audit(ROOT, launch["panel"], observations, identity["binary_sha256"])
        for key in ["UB", "LB", "native_calls_started", "native_calls_returned", "physical_witnesses"]:
            assert replay[key] == done["audit"][key]
        endpoint = done["audit"]["endpoint"]
        gap, relative = gap_fields(endpoint["U"], endpoint["L"])
        endpoints.append(dict(number=launch["number"], id=done["id"], arm=done["arm"], V=launch["panel"]["V"],
                              M=launch["panel"]["M"], Q=launch["panel"]["Q"], T_seconds=launch["panel"]["T_seconds"],
                              process_exit_seconds=done["wall_seconds"], stop_reason=done["stop_reason"],
                              U=endpoint["U"], L=endpoint["L"], gap=gap, relative_gap=relative,
                              certificate=endpoint["certificate"], t_cert=done["wall_seconds"] if endpoint["certificate"] else None,
                              censored=not endpoint["certificate"], status=endpoint["status"], source=endpoint["source"]))
        for seconds in checkpoint_times(launch["cap"]):
            trajectories.append(dict(number=launch["number"], id=done["id"], arm=done["arm"],
                                     seconds=seconds, **checkpoint(observations, done, seconds)))
        for witness in done["audit"].get("witnesses", []):
            witnesses.append(dict(number=launch["number"], id=done["id"], arm=done["arm"],
                                  sequence=witness["sequence"], available_seconds=witness["available"],
                                  objective=witness["F"], G=witness["G"], P=witness["P"],
                                  source=witness["source"], call=witness["call"]))
    certified_objectives = {}
    for identity_name in [panel["id"] for panel in protocol["panel"]]:
        values = [row["U"] for row in endpoints if row["id"] == identity_name and row["certificate"]]
        if values:
            assert max(values) - min(values) <= TOLERANCE, (identity_name, values)
            certified_objectives[identity_name] = min(values)
    discovery = []
    for done in summary["records"]:
        optimum = certified_objectives.get(done["id"])
        target = optimum if optimum is not None else done["audit"]["endpoint"]["U"]
        observed = target_time(done, target, optimum is not None)
        t_cert = done["wall_seconds"] if done["audit"]["endpoint"]["certificate"] else None
        exact_find = observed["time_seconds"] if observed["precision"] == "observed_committed_witness" else None
        discovery.append(dict(number=done["number"], id=done["id"], arm=done["arm"], optimum_known=optimum is not None,
                              **observed, t_cert=t_cert,
                              t_tail=t_cert - exact_find if t_cert is not None and exact_find is not None else None,
                              tail_note="exact_from_observed_witness" if t_cert is not None and exact_find is not None
                              else "unknown_or_only_bounded"))
    pairs = []
    for panel in protocol["panel"]:
        rows = {row["arm"]: row for row in endpoints if row["id"] == panel["id"]}
        p, ens = rows["P-GRB"], rows["ENS-C"]
        if p["certificate"] and ens["certificate"]:
            classification = "both_certified"
            ratio = p["t_cert"] / ens["t_cert"]
            difference = p["t_cert"] - ens["t_cert"]
            winner = "ENS-C" if difference > 0 else "P-GRB" if difference < 0 else "tie"
        elif p["certificate"] or ens["certificate"]:
            classification = "ens_certified_p_censored" if ens["certificate"] else "p_certified_ens_censored"
            ratio = None
            difference = None
            winner = "ENS-C_budget_advantage" if ens["certificate"] else "P-GRB_budget_advantage"
        else:
            classification = "both_censored"
            ratio = None
            difference = None
            winner = "ordering_not_established"
        pairs.append(dict(id=panel["id"], V=panel["V"], M=panel["M"], Q=panel["Q"],
                          T_seconds=panel["T_seconds"], classification=classification, winner=winner,
                          p_t_cert=p["t_cert"], ens_t_cert=ens["t_cert"], p_over_ens_t_cert=ratio,
                          p_minus_ens_seconds=difference, p_U=p["U"], p_L=p["L"], p_gap=p["gap"],
                          ens_U=ens["U"], ens_L=ens["L"], ens_gap=ens["gap"]))
    cross_checks = []
    for panel in protocol["panel"]:
        rows = [row for row in endpoints if row["id"] == panel["id"]]
        uppers = [row["U"] for row in rows if row["U"] is not None]
        lowers = [row["L"] for row in rows if row["L"] is not None]
        strongest = max(lowers)
        best = min(uppers) if uppers else None
        if best is not None:
            assert strongest <= best + TOLERANCE
        cross_checks.append(dict(id=panel["id"], maximum_same_run_global_L=strongest,
                                 minimum_independent_physical_U=best, passed=best is None or strongest <= best + TOLERANCE,
                                 scope="offline contradiction check only; never a combined algorithm endpoint"))
    raw_index = []
    for launch in launches:
        destination = Path(launch["destination"])
        for name in ["launch.json", "completion.json", "observations.json", "audit.json", "result.json",
                     "native.log", "progress.csv", "phases.csv", "compact.lp"]:
            path = destination / name
            if path.is_file():
                raw_index.append(dict(number=launch["number"], id=launch["panel"]["id"], arm=launch["arm"],
                                      path=str(path), bytes=path.stat().st_size, sha256=sha(path)))
    write_csv(STAGE / "endpoints.csv", endpoints)
    write_csv(STAGE / "paired_comparison.csv", pairs)
    write_csv(STAGE / "checkpoint_trajectories.csv", trajectories)
    write_csv(STAGE / "discovery_and_tail.csv", discovery)
    write_csv(STAGE / "witness_index.csv", witnesses)
    write_csv(STAGE / "raw_artifact_index.csv", raw_index)
    write(STAGE / "independent_validation.json", dict(
        all_runs_replayed=True, runs=len(endpoints), all_run_audits_passed=True,
        cross_arm_checks=cross_checks, certified_roles=sorted(certified_objectives),
        certified_objectives=certified_objectives,
        witness_rows=len(witnesses), raw_index_rows=len(raw_index), optimizer_calls=0,
        numerical_certificate_only=True, strict_rational_proof=False,
    ))
    analysis = dict(schema="round87-analysis-v1", completed_pairs=len(pairs),
                    both_certified=sum(row["classification"] == "both_certified" for row in pairs),
                    one_certified=sum("censored" in row["classification"] and row["classification"] != "both_censored" for row in pairs),
                    both_censored=sum(row["classification"] == "both_censored" for row in pairs),
                    ens_faster=sum(row["winner"] == "ENS-C" for row in pairs),
                    p_faster=sum(row["winner"] == "P-GRB" for row in pairs),
                    optimizer_calls=0, wall_seconds=time.perf_counter() - started,
                    endpoint_rows=len(endpoints), checkpoint_rows=len(trajectories),
                    discovery_rows=len(discovery), script_sha256=sha(__file__))
    write(OUT / "analysis.json", analysis)
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
