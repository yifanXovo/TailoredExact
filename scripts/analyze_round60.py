"""Create the compact, auditable Round 60 evidence package.

The large solver artifacts remain under ``local_raw``.  This script extracts
the predeclared comparisons, root-relaxation diagnostics, candidate events,
and process-budget audit into small files suitable for source control.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_verified_candidate_native_round60"
RAW = OUT / "local_raw"
PANEL = {row["id"]: row for row in json.loads(
    (OUT / "protocol.json").read_text(encoding="utf-8"))["panel"]}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, records: list[dict]):
    if not records:
        raise RuntimeError(f"refusing to create empty table: {path}")
    fields: list[str] = []
    for record in records:
        for key in record:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def number(value, default=math.nan):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def finite(value):
    return math.isfinite(number(value))


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_instance(identity: str):
    path = ROOT / PANEL[identity]["instance_path"]
    text = path.read_text(encoding="utf-8")

    def vector(name):
        match = re.search(rf"(?m)^\s*{name}\s*=\s*(\[[^\n]+\])", text)
        if not match:
            return []
        return list(ast.literal_eval(match.group(1)))

    initial = vector("initial")
    target = vector("target")
    weights = [float(value) for value in vector("weights")]
    if not weights:
        weights = [0.0] + [1.0] * int(PANEL[identity]["V"])
    if abs(max(weights[1:]) - 10.0) <= 1e-6:
        weights = [value / 10.0 for value in weights]
    return {"initial": initial, "target": target, "weights": weights}


def objective_parts(identity: str, inventory: list[float]):
    instance = read_instance(identity)
    target = instance["target"]
    ratios = [0.0] + [inventory[i] / target[i]
                      for i in range(1, len(inventory))]
    s_value = sum(ratios[1:])
    h_value = sum(abs(ratios[i] - ratios[j])
                  for i in range(1, len(ratios))
                  for j in range(i + 1, len(ratios)))
    g_value = h_value / ((len(inventory) - 1) * s_value) \
        if s_value > 0 else 0.0
    p_value = sum(instance["weights"][i] * abs(ratios[i] - 1.0)
                  for i in range(1, len(inventory)))
    return {"S": s_value, "H": h_value, "G": g_value,
            "P": p_value, "objective": g_value + 0.15 * p_value}


def decision(result):
    """Apply the thresholds frozen before the formal performance runs."""
    off, inject = result
    off_gap = max(0.0, number(off["verified_upper_bound"]) -
                  number(off["lower_bound"]))
    inject_gap = max(0.0, number(inject["verified_upper_bound"]) -
                     number(inject["lower_bound"]))
    delta = off_gap - inject_gap
    relative = delta / off_gap if off_gap > 0 else 0.0
    off_cert = bool(off["certificate"])
    inject_cert = bool(inject["certificate"])
    time_delta = number(off["process_time_seconds"]) - \
        number(inject["process_time_seconds"])
    if off_cert and not inject_cert:
        label = "certificate_loss"
    elif not off_cert and inject_cert:
        label = "certificate_gain"
    elif delta >= 0.001 and relative >= 0.05:
        label = "meaningful_gap_improvement"
    elif delta <= -0.001 and relative <= -0.05:
        label = "obvious_gap_regression"
    elif off_cert and inject_cert and time_delta >= 10.0:
        label = "meaningful_certificate_speedup"
    elif off_cert and inject_cert and time_delta <= -10.0:
        label = "obvious_certificate_slowdown"
    elif off_cert and inject_cert and abs(time_delta) < 1.0:
        label = "neutral_subsecond_timing"
    else:
        label = "neutral_below_predeclared_threshold"
    return off_gap, inject_gap, delta, relative, time_delta, label


def fixed_tables():
    records = []
    pairs = []
    for stage in ["fixed_120", "long_600"]:
        stage_path = RAW / stage
        if not stage_path.exists():
            continue
        cap = int(stage.rsplit("_", 1)[1])
        for identity_path in sorted(stage_path.iterdir()):
            if not identity_path.is_dir():
                continue
            identity = identity_path.name
            by_mode = {}
            for mode_path in sorted(identity_path.iterdir()):
                result_path = mode_path / "result.json"
                if not result_path.exists():
                    continue
                result = load(result_path)
                mode = mode_path.name.lower()
                by_mode[mode] = result
                records.append({
                    "stage": stage, "cap_seconds": cap, "id": identity,
                    "mode": mode.upper(), "status": result["status"],
                    "native_status": result["native_status"],
                    "certificate": result["certificate"],
                    "lower_bound": result["lower_bound"],
                    "verified_upper_bound": result["verified_upper_bound"],
                    "absolute_gap": max(0.0,
                        number(result["verified_upper_bound"]) -
                        number(result["lower_bound"])),
                    "relative_gap": result["gap"],
                    "work": result["work"], "nodes": result["nodes"],
                    "simplex_iterations": result["simplex_iterations"],
                    "root_time_seconds": result["root_time_seconds"],
                    "root_callback_count": load(
                        mode_path / "node_samples.csv.audit.json").get(
                            "root_callback_count", "")
                        if (mode_path / "node_samples.csv.audit.json").exists()
                        else "",
                    "root_completion_status": load(
                        mode_path / "node_samples.csv.audit.json").get(
                            "root_completion_status", "")
                        if (mode_path / "node_samples.csv.audit.json").exists()
                        else "",
                    "process_seconds": result["process_time_seconds"],
                    "candidate_triggers": result["round60_candidate_triggers"],
                    "candidates_generated": result["round60_candidates_generated"],
                    "candidates_verified": result["round60_candidates_verified"],
                    "candidates_mapped": result["round60_candidates_mapped"],
                    "candidates_submitted": result["round60_candidates_submitted"],
                    "candidates_confirmed":
                        result["round60_candidates_confirmed_accepted"],
                    "candidate_acceptance_unknown":
                        result["round60_candidates_acceptance_unknown"],
                    "candidate_objective": result[
                        "round60_best_generated_objective"]
                        if result["round60_best_generated_objective_available"]
                        else "",
                    "candidate_overhead_seconds":
                        result["round60_candidate_overhead_seconds"],
                    "model_sha256": result["model_sha256"],
                })
            if "off" in by_mode and "inject" in by_mode:
                off = by_mode["off"]
                inject = by_mode["inject"]
                off_gap, inject_gap, delta, relative, time_delta, label = \
                    decision((off, inject))
                pairs.append({
                    "stage": stage, "cap_seconds": cap, "id": identity,
                    "same_model_sha256": off["model_sha256"] ==
                        inject["model_sha256"],
                    "off_certificate": off["certificate"],
                    "inject_certificate": inject["certificate"],
                    "off_LB": off["lower_bound"],
                    "inject_LB": inject["lower_bound"],
                    "off_UB": off["verified_upper_bound"],
                    "inject_UB": inject["verified_upper_bound"],
                    "off_absolute_gap": off_gap,
                    "inject_absolute_gap": inject_gap,
                    "absolute_gap_reduction": delta,
                    "relative_absolute_gap_reduction": relative,
                    "off_process_seconds": off["process_time_seconds"],
                    "inject_process_seconds": inject["process_time_seconds"],
                    "off_minus_inject_seconds": time_delta,
                    "inject_work_minus_off": number(inject["work"]) -
                        number(off["work"]),
                    "inject_nodes_minus_off": int(inject["nodes"]) -
                        int(off["nodes"]),
                    "candidate_submitted": inject[
                        "round60_candidates_submitted"],
                    "candidate_confirmed": inject[
                        "round60_candidates_confirmed_accepted"],
                    "candidate_acceptance_unknown": inject[
                        "round60_candidates_acceptance_unknown"],
                    "candidate_overhead_seconds": inject[
                        "round60_candidate_overhead_seconds"],
                    "predeclared_decision": label,
                })
    write_csv(OUT / "fixed_candidate_results.csv", records)
    write_csv(OUT / "fixed_candidate_pairs.csv", pairs)
    return records, pairs


def candidate_events():
    output = []
    for path in sorted(RAW.rglob("*candidate_events.csv")):
        relative = path.relative_to(RAW)
        stage = relative.parts[0]
        if stage == "native_micro":
            identity = "micro"
            arm = relative.parts[1]
        else:
            identity = relative.parts[1]
            arm = relative.parts[2]
        for row in rows(path):
            output.append({"stage": stage, "id": identity, "arm": arm,
                           **row})
    write_csv(OUT / "candidate_event_evidence.csv", output)


def native_micro():
    output = []
    directory = RAW / "native_micro"
    for run in sorted(directory.iterdir()):
        event_path = run / "round60_candidate_events.csv"
        completion = load(run / "completion.json") if (
            run / "completion.json").exists() else {}
        events = rows(event_path) if event_path.exists() else []
        output.append({
            "run": run.name, "returncode": completion.get("returncode", ""),
            "events": len(events),
            "generated": sum(int(row["generated"]) for row in events),
            "mapped": sum(int(row["mapping_complete"]) for row in events),
            "submitted": sum(int(row["submitted"]) for row in events),
            "last_acceptance": events[-1]["acceptance"] if events else "",
            "last_status": events[-1]["status"] if events else "",
            "all_checked_linear_rows_valid": all(
                row["linear_valid"] == "1" for row in events
                if row["linear_checked"] == "1"),
            "maximum_linear_violation": max(
                [number(row["max_violation"], 0.0) for row in events] or [0.0]),
        })
    write_csv(OUT / "native_injection_micro.csv", output)


def root_diagnostics():
    details = []
    trajectories = []
    for identity in ["D3", "D4", "D6", "D7"]:
        directory = RAW / "fixed_120" / identity / "OFF"
        sample_path = directory / "node_samples.csv"
        if not sample_path.exists():
            # Directory names are lower-case in older local runs.
            directory = RAW / "fixed_120" / identity / "off"
            sample_path = directory / "node_samples.csv"
        sample_rows = rows(sample_path)
        audit = load(Path(str(sample_path) + ".audit.json"))
        by_kind = {}
        for row in sample_rows:
            by_kind.setdefault(row["sample_kind"], {})[row["variable"]] = \
                number(row["value"])
        for kind in ["first_root_relaxation", "latest_root_relaxation"]:
            values = by_kind[kind]
            inventory = [0.0] + [values[f"Y_{i}"]
                                  for i in range(1, int(PANEL[identity]["V"]) + 1)]
            parts = objective_parts(identity, inventory)
            model_g = values["G"]
            z_residuals = [abs(values[f"zprod_{i}"] - model_g * inventory[i])
                           for i in range(1, len(inventory))]
            family_stats = {}
            families = {
                "Y": re.compile(r"^Y_"), "bit": re.compile(r"^bit_"),
                "visit_z": re.compile(r"^z_"),
                "mode": re.compile(r"^mode_"), "arc_x": re.compile(r"^x_"),
            }
            for family, pattern in families.items():
                selected = [value for name, value in values.items()
                            if pattern.match(name)]
                distances = [abs(value - round(value)) for value in selected]
                family_stats[family + "_count"] = len(selected)
                family_stats[family + "_fractional_count"] = sum(
                    distance > 1e-7 for distance in distances)
                family_stats[family + "_max_fractionality"] = max(
                    distances or [0.0])
            details.append({
                "id": identity, "sample_kind": kind,
                "root_callback_sequence": next(
                    row["root_callback_sequence"] for row in sample_rows
                    if row["sample_kind"] == kind),
                "root_completion_status": audit["root_completion_status"],
                "sampling_seconds": audit["sampling_seconds"],
                "eligible_callback_checks": audit["eligible_callback_checks"],
                "successful_samples": audit["successful_samples"],
                "nonoptimal_or_failed_sample_checks": audit["sampling_failures"],
                "root_callback_count": audit["root_callback_count"],
                "model_G": model_g, "inventory_exact_G": parts["G"],
                "delta_G_exact_minus_model": parts["G"] - model_g,
                "absolute_delta_G": abs(parts["G"] - model_g),
                "max_abs_zprod_minus_G_times_Y": max(z_residuals),
                "inventory_exact_P": parts["P"],
                "inventory_exact_objective": parts["objective"],
                **family_stats,
            })
        scalar_path = Path(str(sample_path) + ".root_scalars.csv")
        for row in rows(scalar_path):
            trajectories.append({
                "id": identity,
                "root_completion_status": audit["root_completion_status"],
                **row,
            })
    write_csv(OUT / "root_relaxation_diagnostic.csv", details)
    write_csv(OUT / "root_scalar_trajectory.csv", trajectories)
    return details


def product_route():
    selections = {item["id"]: item for item in load(
        OUT / "fixed_inventory_selection.json")}
    output = []
    for identity in ["D3", "D4", "D6"]:
        selection = selections[identity]
        inventory = selection["fixed_inventory"]
        parts = objective_parts(identity, inventory)
        initial = read_instance(identity)["initial"]
        pickup = sum(max(0, initial[i] - inventory[i])
                     for i in range(1, len(inventory)))
        drop = sum(max(0, inventory[i] - initial[i])
                   for i in range(1, len(inventory)))
        depot_return = pickup - drop
        lp_dir = RAW / "product_route" / identity / "FIXED-Y-LP"
        lp = load(lp_dir / "lp_result.json")
        evidence = {row["variable_name"]: number(row["primal_value"])
                    for row in rows(lp_dir / "lp_variable_evidence.csv")}
        lp_g = evidence["G"]
        lp_product_residual = max(abs(evidence[f"zprod_{i}"] -
                                      lp_g * evidence[f"Y_{i}"])
                                  for i in range(1, len(inventory)))
        mip = load(RAW / "product_route" / identity /
                   "FIXED-Y-MIP" / "result.json")
        relaxed_path = (RAW / "product_route" / identity /
                        "FIXED-Y-MIP-T-RELAXED" / "result.json")
        relaxed = load(relaxed_path) if relaxed_path.exists() else None
        if mip["native_status"] == "OPTIMAL":
            obstruction = "none_fixed_inventory_is_route_feasible_at_original_T"
        elif relaxed and relaxed["native_status"] == "OPTIMAL":
            obstruction = (
                "original_route_duration_horizon; same inventory, capacities, "
                "vehicle loads, and routing/order model feasible when only T is relaxed")
        else:
            obstruction = "unresolved_fixed_inventory_route_infeasibility"
        output.append({
            "id": identity, "inventory_source": selection["source"],
            "root_inventory_integral": selection["root_inventory_integral"],
            "rounding": selection["rounding"],
            "fixed_inventory": ";".join(map(str, inventory)),
            "changed_stations": sum(initial[i] != inventory[i]
                                    for i in range(1, len(inventory))),
            "total_pickup": pickup, "total_station_drop": drop,
            "depot_return": depot_return,
            "aggregate_handling_seconds":
                number(PANEL[identity]["pickup_seconds"]) * pickup +
                number(PANEL[identity]["drop_seconds"]) *
                    (drop + depot_return),
            "exact_G": parts["G"], "exact_P": parts["P"],
            "exact_objective": parts["objective"],
            "fixed_LP_status": lp["native_status"],
            "fixed_LP_objective": lp["objective"],
            "fixed_LP_minus_exact_objective":
                number(lp["objective"]) - parts["objective"],
            "fixed_LP_product_residual": lp_product_residual,
            "fixed_MIP_status": mip["native_status"],
            "fixed_MIP_certificate": mip["certificate"],
            "fixed_MIP_objective": mip["verified_upper_bound"]
                if mip["native_status"] == "OPTIMAL" else "",
            "fixed_MIP_process_seconds": mip["process_time_seconds"],
            "time_relaxed_T": 1000000 if relaxed else "",
            "time_relaxed_status": relaxed["native_status"] if relaxed else "",
            "time_relaxed_objective": relaxed["verified_upper_bound"]
                if relaxed and relaxed["native_status"] == "OPTIMAL" else "",
            "diagnosed_obstruction": obstruction,
        })
    write_csv(OUT / "product_route_diagnostic.csv", output)
    return output


def hga_table():
    output = []
    evidence = []
    for identity in ["D6", "D7"]:
        directory = RAW / "hga_publish_120" / identity
        original = load(directory / "HGA-ORIGINAL" / "result.json")
        publish = load(directory / "HGA-PUBLISH" / "result.json")
        a = rows(directory / "HGA-ORIGINAL" / "hga_generations.csv")
        b = rows(directory / "HGA-PUBLISH" / "hga_generations.csv")
        common = min(len(a), len(b))
        exact_prefix = all(
            left["generation"] == right["generation"] and
            abs(number(left["best_fitness"]) -
                number(right["best_fitness"])) <= 1e-12 and
            left["strict_improvement"] == right["strict_improvement"]
            for left, right in zip(a[:common], b[:common]))
        output.append({
            "id": identity, "original_UB": original["upper_bound"],
            "publish_UB": publish["upper_bound"],
            "absolute_UB_improvement": number(original["upper_bound"]) -
                number(publish["upper_bound"]),
            "relative_UB_improvement": 1.0 -
                number(publish["upper_bound"]) /
                number(original["upper_bound"]),
            "original_hga_seconds": original["hga_wall_time_seconds"],
            "publish_hga_seconds": publish["hga_wall_time_seconds"],
            "original_generations": original["hga_total_generations"],
            "publish_generations": publish["hga_total_generations"],
            "common_generation_prefix_rows": common,
            "common_logical_prefix_exact": exact_prefix,
            "retained_verified_event_candidate": publish[
                "hga_retained_verified_event_candidate"],
            "candidate_observer_failed": publish[
                "hga_candidate_observer_failed"],
            "candidate_observations": publish["hga_candidate_observations"],
            "candidates_verified": publish["hga_verified_candidate_count"],
            "candidates_published": publish["hga_published_candidate_count"],
            "verification_seconds": publish[
                "hga_candidate_verification_seconds"],
            "retained_sha256": publish["hga_retained_candidate_sha256"],
        })
        for row in rows(directory / "HGA-PUBLISH" / "hga_candidates.csv"):
            evidence.append({"id": identity, **row})
    write_csv(OUT / "hga_publish_results.csv", output)
    write_csv(OUT / "hga_candidate_evidence.csv", evidence)
    return output


def split_table():
    output = []
    for identity in ["D2", "C2"]:
        loaded = {}
        for arm in ["K1-H", "Single-H"]:
            directory = RAW / "split_120" / identity / arm
            result = load(directory / "result.json")
            candidate = rows(directory / "heuristic_candidates.csv")[-1]
            route_state = "|".join(candidate.get(key, "") for key in [
                "objective", "G", "P", "route_count", "served_station_count",
                "total_pickup", "total_drop", "depot_unload", "route_durations"])
            loaded[arm] = (result, hashlib.sha256(
                route_state.encode("utf-8")).hexdigest())
        same = loaded["K1-H"][1] == loaded["Single-H"][1]
        for arm in ["K1-H", "Single-H"]:
            result, route_hash = loaded[arm]
            output.append({
                "id": identity, "protocol_stage": PANEL[identity]["stage"],
                "arm": arm, "same_initial_verified_route_state": same,
                "initial_route_state_sha256": route_hash,
                "hga_seconds": result["hga_wall_time_seconds"],
                "splits": result["external_gini_tree_split_count"],
                "declined_splits": result[
                    "external_gini_tree_declined_split_count"],
                "LP_calls": result["external_gini_tree_lp_optimize_count"],
                "partial_MIP_calls": result[
                    "external_gini_tree_partial_mip_optimize_count"],
                "partial_target_events": result[
                    "external_gini_tree_partial_mip_target_reached_count"],
                "terminal_MIP_calls": result[
                    "external_gini_tree_terminal_mip_optimize_count"],
                "lower_bound": result["lower_bound"],
                "upper_bound": result["upper_bound"],
                "absolute_gap": number(result["upper_bound"]) -
                    number(result["lower_bound"]),
                "relative_gap": result["gap"],
                "strict_certificate": result[
                    "external_gini_tree_strict_certified"],
                "solver_seconds": result[
                    "external_gini_tree_solver_seconds"],
                "work": result["external_gini_tree_work"],
                "process_seconds": result["final_process_wall_time_seconds"],
            })
    write_csv(OUT / "split_attribution.csv", output)
    return output


def integration_and_references():
    output = []
    for stage, identities, arms in [
        ("integration_120", ["D1", "C1"],
         ["Single-S", "Single-S+INJECT"]),
        ("partial_integration_120", ["C2"],
         ["K1-H", "K1-H+INJECT"]),
        ("same_build_reference_120", ["D1", "C1"], ["P-GRB", "K1-H"]),
    ]:
        for identity in identities:
            for arm in arms:
                path = RAW / stage / identity / arm / "result.json"
                if not path.exists():
                    successful = []
                    for candidate in sorted((RAW / stage / identity).glob(
                            arm + "-retry*/result.json")):
                        completion = candidate.parent / "completion.json"
                        if completion.exists() and load(completion).get(
                                "returncode") == 0:
                            successful.append(candidate)
                    if successful:
                        path = successful[-1]
                if not path.exists():
                    continue
                result = load(path)
                output.append({
                    "stage": stage, "id": identity, "arm": arm,
                    "algorithm_preset": result.get("algorithm_preset", "plain"),
                    "status": result["status"],
                    "lower_bound": result["lower_bound"],
                    "upper_bound": result["upper_bound"],
                    "absolute_gap": max(0.0, number(result["upper_bound"]) -
                                        number(result["lower_bound"])),
                    "relative_gap": result["gap"],
                    "strict_certificate": (
                        result.get("strict_certified_original_problem", False)
                        if result.get("method") == "gurobi" else
                        result.get("external_gini_tree_strict_certified", False)),
                    "process_seconds": result["final_process_wall_time_seconds"],
                    "splits": result.get("external_gini_tree_split_count", 0),
                    "LP_calls": result.get(
                        "external_gini_tree_lp_optimize_count", 0),
                    "MIP_calls": result.get(
                        "external_gini_tree_partial_mip_optimize_count", 0) +
                        result.get("external_gini_tree_terminal_mip_optimize_count", 0),
                    "candidate_mode": result.get("round60_candidate_mode", "off"),
                    "candidates_generated": result.get(
                        "round60_candidates_generated", 0),
                    "candidates_submitted": result.get(
                        "round60_candidates_submitted", 0),
                    "candidates_confirmed": result.get(
                        "round60_candidates_confirmed_accepted", 0),
                    "candidate_acceptance_unknown": result.get(
                        "round60_candidates_acceptance_unknown", 0),
                    "candidate_overhead_seconds": result.get(
                        "round60_candidate_overhead_seconds", 0),
                    "model_correctness_verified": result.get(
                        "model_correctness_verified", ""),
                    "model_fingerprint": result.get(
                        "gurobi_model_fingerprint", ""),
                    "executable_sha256": load(path.parent / "launch.json").get(
                        "executable_sha256", ""),
                })
    write_csv(OUT / "full_integration_results.csv", output)
    paired = []
    for stage, identity, off_arm, inject_arm in [
        ("integration_120", "D1", "Single-S", "Single-S+INJECT"),
        ("integration_120", "C1", "Single-S", "Single-S+INJECT"),
        ("partial_integration_120", "C2", "K1-H", "K1-H+INJECT"),
    ]:
        selected = {(row["id"], row["arm"]): row for row in output
                    if row["stage"] == stage}
        if (identity, off_arm) not in selected or \
                (identity, inject_arm) not in selected:
            continue
        off = selected[(identity, off_arm)]
        inject = selected[(identity, inject_arm)]
        off_gap = number(off["absolute_gap"])
        inject_gap = number(inject["absolute_gap"])
        delta = off_gap - inject_gap
        relative = delta / off_gap if off_gap > 0 else 0.0
        time_delta = number(off["process_seconds"]) - \
            number(inject["process_seconds"])
        if off["strict_certificate"] and not inject["strict_certificate"]:
            label = "certificate_loss"
        elif not off["strict_certificate"] and inject["strict_certificate"]:
            label = "certificate_gain"
        elif delta >= 0.001 and relative >= 0.05:
            label = "meaningful_gap_improvement"
        elif delta <= -0.001 and relative <= -0.05:
            label = "obvious_gap_regression"
        elif (off["strict_certificate"] and inject["strict_certificate"] and
              time_delta >= 10.0):
            label = "meaningful_certificate_speedup"
        elif (off["strict_certificate"] and inject["strict_certificate"] and
              time_delta <= -10.0):
            label = "obvious_certificate_slowdown"
        elif (off["strict_certificate"] and inject["strict_certificate"] and
              abs(time_delta) < 1.0):
            label = "neutral_subsecond_timing"
        else:
            label = "neutral_below_predeclared_threshold"
        paired.append({
            "stage": stage, "id": identity,
            "off_arm": off_arm, "inject_arm": inject_arm,
            "same_executable_sha256": off["executable_sha256"] ==
                inject["executable_sha256"],
            "off_LB": off["lower_bound"], "inject_LB": inject["lower_bound"],
            "off_UB": off["upper_bound"], "inject_UB": inject["upper_bound"],
            "off_absolute_gap": off_gap,
            "inject_absolute_gap": inject_gap,
            "absolute_gap_reduction": delta,
            "relative_absolute_gap_reduction": relative,
            "off_minus_inject_seconds": time_delta,
            "candidate_submitted": inject["candidates_submitted"],
            "candidate_confirmed": inject["candidates_confirmed"],
            "candidate_acceptance_unknown": inject[
                "candidate_acceptance_unknown"],
            "predeclared_decision": label,
        })
    write_csv(OUT / "full_integration_pairs.csv", paired)
    return output


def budget_audit():
    entries = [json.loads(line) for line in (OUT / "processes.jsonl").read_text(
        encoding="utf-8").splitlines() if line.strip()]
    launches = []
    for path in RAW.rglob("launch.json"):
        launch = load(path)
        completion_path = path.parent / "completion.json"
        if not completion_path.exists():
            continue
        completion = load(completion_path)
        start = number(launch["started_unix"])
        launches.append((start, start + number(completion["wall_seconds"]),
                         bool(launch.get("optimization", True))))
    events = []
    for start, end, optimization in launches:
        if optimization:
            # Launches use wall-clock epoch while durations use a monotonic
            # clock.  Allow 0.1 s for cross-clock/readout skew; the driver
            # itself blocks in process.wait before launching the next run.
            events.extend([(start, 1), (end - 0.1, -1)])
    # End events sort before start events at identical timestamps.
    active = maximum = 0
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        active += delta
        maximum = max(maximum, active)
    failures = []
    for path in RAW.rglob("completion.json"):
        completion = load(path)
        if completion.get("returncode") != 0:
            failures.append(str(path.parent.relative_to(RAW)))
    native_micro_count = len([
        path for path in (RAW / "native_micro").iterdir()
        if path.is_dir()])
    audit = {
        "schema": "round60-process-budget-audit-v1",
        "maximum_allowed_processes": 72,
        "manual_native_micro_processes": 5,
        "script_optimization_processes": sum(
            bool(item.get("optimization", True)) for item in entries),
        "script_nonoptimization_processes": sum(
            not bool(item.get("optimization", True)) for item in entries),
        "total_charged_processes": 5 + sum(
            bool(item.get("optimization", True)) for item in entries),
        "remaining_processes": 72 - 5 - sum(
            bool(item.get("optimization", True)) for item in entries),
        "native_micro_processes": native_micro_count,
        "maximum_native_micro_processes": 6,
        "maximum_observed_concurrent_optimization_processes": maximum,
        "interval_overlap_tolerance_seconds": 0.1,
        "structurally_serial_driver": True,
        "failed_processes_retained_and_charged": failures,
        "all_watchdogs_clear": all(not load(path).get("watchdog", False)
            for path in RAW.rglob("completion.json")),
    }
    write_json(OUT / "budget_audit.json", audit)
    return audit


def build_ledger():
    grouped = {}
    seen_directories = set()
    for path in RAW.rglob("launch.json"):
        launch = load(path)
        seen_directories.add(path.parent.resolve())
        digest = launch.get("executable_sha256", "")
        if not digest:
            continue
        record = grouped.setdefault(digest, {
            "executable_sha256": digest, "processes": 0,
            "stages": set(), "executables": set(),
        })
        record["processes"] += 1
        record["stages"].add(launch.get("stage", "manual_native_micro"))
        command = launch.get("command", [])
        if command:
            record["executables"].add(Path(command[0]).name)
    for path in (RAW / "native_micro").rglob("command.json"):
        if path.parent.resolve() in seen_directories:
            continue
        command = load(path)
        digest = command.get("executable_sha256", "")
        if not digest:
            continue
        record = grouped.setdefault(digest, {
            "executable_sha256": digest, "processes": 0,
            "stages": set(), "executables": set(),
        })
        record["processes"] += 1
        record["stages"].add("manual_native_micro")
        record["executables"].add(
            Path(command.get("executable_path", "unknown")).name)
    entries = []
    for record in grouped.values():
        entries.append({
            "executable_sha256": record["executable_sha256"],
            "processes": record["processes"],
            "stages": sorted(record["stages"]),
            "executables": sorted(record["executables"]),
        })
    current = {}
    for name in ["ExactEBRP.exe", "Round50IntervalMipExperiment.exe"]:
        path = ROOT / "build/round60-dev" / name
        if path.exists():
            current[name] = sha256(path)
    write_json(OUT / "build_ledger.json", {
        "schema": "round60-build-ledger-v1",
        "launched_builds": sorted(entries,
            key=lambda item: item["executable_sha256"]),
        "current_deliverable_executables": current,
        "note": ("Each matched performance pair used one executable hash. "
                 "A final code-audit patch only added missing partial-target "
                 "wiring; final-build validation and targeted matched runs are "
                 "listed separately."),
    })


def manifest():
    excluded = {"artifact_manifest.json"}
    records = []
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name not in excluded:
            records.append({"path": path.name, "bytes": path.stat().st_size,
                            "sha256": sha256(path)})
    write_json(OUT / "artifact_manifest.json", {
        "schema": "round60-compact-artifact-manifest-v1",
        "local_raw_committed": False,
        "artifacts": records,
    })


def main():
    fixed, pairs = fixed_tables()
    candidate_events()
    native_micro()
    roots = root_diagnostics()
    product = product_route()
    hga = hga_table()
    split = split_table()
    integration = integration_and_references()
    audit = budget_audit()
    build_ledger()
    summary = {
        "fixed_rows": len(fixed), "fixed_pairs": len(pairs),
        "root_rows": len(roots), "product_rows": len(product),
        "hga_pairs": len(hga), "split_rows": len(split),
        "integration_reference_rows": len(integration),
        "budget": audit,
    }
    write_json(OUT / "analysis_summary.json", summary)
    manifest()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
