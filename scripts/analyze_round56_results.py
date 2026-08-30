#!/usr/bin/env python3
"""Build the compact Round 56 result, checkpoint, route, and audit tables."""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import round56_common as r56
from round56_route_archive import EXECUTABLE_SHA256, SOURCE_FREEZE, classify


RAW = r56.EVIDENCE / "local_raw" / "official"
SOLUTIONS = r56.EVIDENCE / "solutions"
TOL = 1e-7


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        if len(value) != 1:
            raise RuntimeError(f"expected one JSON result in {path}")
        value = value[0]
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object in {path}")
    return value


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def gap(lower: float | None, upper: float | None) -> float | None:
    if lower is None or upper is None:
        return None
    return max(0.0, upper - lower) / max(1.0, abs(upper))


def close(left: Any, right: Any) -> bool:
    a, b = as_float(left), as_float(right)
    return a is not None and b is not None and abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def descriptors() -> list[dict[str, Any]]:
    manifest = load_json(r56.EVIDENCE / "scenario_manifest.json")
    return [load_json(r56.ROOT / row["descriptor_path"]) for row in manifest["rows"]]


def result_bundle(descriptor: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    run_dir = RAW / descriptor["scenario_id"]
    result_path, marker_path = run_dir / "result.json", run_dir / "completion_marker.json"
    if not result_path.is_file() or not marker_path.is_file():
        raise RuntimeError(f"missing official completion: {descriptor['scenario_id']}")
    result, marker = load_json(result_path), load_json(marker_path)
    if not marker.get("complete") or marker.get("result_sha256") != r56.sha256_file(result_path):
        raise RuntimeError(f"invalid official completion marker: {descriptor['scenario_id']}")
    return result, marker


def certificate_conditions(result: dict[str, Any]) -> dict[str, bool]:
    verification = result.get("verification") or {}
    lower, upper = as_float(result.get("lower_bound")), as_float(result.get("upper_bound"))
    return {
        "strict_original_certificate": bool(result.get("strict_certified_original_problem")),
        "external_tree_strict_certificate": bool(result.get("external_gini_tree_strict_certified")),
        "root_coverage_valid": bool(result.get("external_gini_tree_root_coverage_valid")),
        "parent_child_coverage_valid": bool(result.get("external_gini_tree_parent_child_coverage_valid")),
        "all_relevant_leaves_closed": bool(result.get("external_gini_tree_all_relevant_leaves_closed")),
        "all_leaf_bounds_valid": bool(result.get("external_gini_tree_all_leaf_bounds_valid")),
        "global_bound_monotone": bool(result.get("external_gini_tree_global_bound_monotone")),
        "original_solution_feasible": bool(verification.get("original_solution_feasible")),
        "original_objective_recomputed": bool(verification.get("original_objective_recomputed")),
        "verification_error_free": not bool(verification.get("errors")),
        "bound_closed_within_tolerance": lower is not None and upper is not None and close(lower, upper),
        "no_restricted_result_in_certificate": result.get("method_scope") == "original_compact" and result.get("strict_native_model_scope") == "original_problem",
    }


def route_stats(scenario_id: str) -> dict[str, Any]:
    package_path = SOLUTIONS / scenario_id / "native_solution.json"
    if not package_path.is_file():
        return {
            "route_witness_package_available": False, "archive_verification_passed": False,
            "vehicles_available": None, "vehicles_used": None, "total_visited_stations": None,
            "total_pickup": None, "total_station_drop": None, "total_depot_unload": None,
            "total_bikes_moved": None, "total_handling_operations": None,
            "maximum_route_travel_time": None, "maximum_route_operation_time": None,
            "maximum_route_duration": None, "total_route_duration": None,
            "maximum_route_utilization": None, "mean_used_vehicle_utilization": None,
            "route_duration_standard_deviation": None, "minimum_route_slack": None,
            "travel_time_share": None, "operation_time_share": None,
        }
    package = load_json(package_path)
    verification = load_json(SOLUTIONS / scenario_id / "solution_verification.json")
    routes = package["routes"]
    used = [route for route in routes if route["used"]]
    durations = [float(route["route_duration"]) for route in used]
    travel = sum(float(route["travel_time"]) for route in used)
    operation = sum(float(route["operation_time"]) for route in used)
    total_duration = travel + operation
    pickup = sum(int(route["total_pickup"]) for route in used)
    station_drop = sum(int(route["total_station_drop"]) for route in used)
    depot_unload = sum(int(route["final_depot_unload"]) for route in used)
    return {
        "route_witness_package_available": True,
        "archive_verification_passed": bool(verification.get("passed")),
        "vehicles_available": package["M"], "vehicles_used": len(used),
        "total_visited_stations": sum(len(route["operations"]) for route in used),
        "total_pickup": pickup, "total_station_drop": station_drop,
        "total_depot_unload": depot_unload, "total_bikes_moved": pickup + station_drop,
        "total_handling_operations": pickup + station_drop + depot_unload,
        "maximum_route_travel_time": max((float(route["travel_time"]) for route in used), default=0.0),
        "maximum_route_operation_time": max((float(route["operation_time"]) for route in used), default=0.0),
        "maximum_route_duration": max(durations, default=0.0), "total_route_duration": sum(durations),
        "maximum_route_utilization": max((float(route["utilization"]) for route in used), default=0.0),
        "mean_used_vehicle_utilization": statistics.mean(float(route["utilization"]) for route in used) if used else 0.0,
        "route_duration_standard_deviation": statistics.pstdev(durations) if durations else 0.0,
        "minimum_route_slack": min((float(route["route_slack"]) for route in used), default=float(package["route_time_limit_seconds"])),
        "travel_time_share": travel / total_duration if total_duration else 0.0,
        "operation_time_share": operation / total_duration if total_duration else 0.0,
    }


def checkpoint_snapshot(descriptor: dict[str, Any], result: dict[str, Any], checkpoint: int) -> dict[str, Any]:
    final_wall = float(result.get("final_process_wall_time_seconds", result.get("wall_time_seconds", 0.0)))
    final_certified = bool(result.get("strict_certified_original_problem"))
    if final_wall <= checkpoint + TOL:
        lower, upper = as_float(result.get("lower_bound")), as_float(result.get("upper_bound"))
        return {
            "snapshot_source": "certified_final_state" if final_certified else "completed_final_state",
            "snapshot_process_seconds": final_wall, "certificate_at_checkpoint": final_certified,
            "lower_bound": lower, "verified_upper_bound": upper, "gap": gap(lower, upper),
            "open_relevant_leaf_count": result.get("external_gini_tree_open_leaf_count"),
            "algorithm_work": result.get("external_gini_tree_work"), "nodes": result.get("external_gini_tree_nodes"),
            "simplex_iterations": result.get("external_gini_tree_simplex_iterations"),
            "split_count": result.get("external_gini_tree_split_count"),
            "event_type": "strict_completion" if final_certified else "finalization",
        }
    trace = read_csv(RAW / descriptor["scenario_id"] / "external" / "global_bound_trace.csv")
    eligible = [row for row in trace if as_float(row.get("process_elapsed_seconds")) is not None and float(row["process_elapsed_seconds"]) <= checkpoint + TOL]
    if eligible:
        selected = max(eligible, key=lambda row: float(row["process_elapsed_seconds"]))
        lower, upper = as_float(selected.get("valid_global_lower_bound")), as_float(selected.get("verified_global_upper_bound"))
        return {
            "snapshot_source": "global_bound_trace", "snapshot_process_seconds": as_float(selected.get("process_elapsed_seconds")),
            "certificate_at_checkpoint": False, "lower_bound": lower, "verified_upper_bound": upper,
            "gap": gap(lower, upper), "open_relevant_leaf_count": selected.get("open_relevant_leaf_count"),
            "algorithm_work": None, "nodes": None, "simplex_iterations": None, "split_count": None,
            "event_type": selected.get("event_type"),
        }
    progress = read_csv(RAW / descriptor["scenario_id"] / "progress.csv")
    eligible = [row for row in progress if as_float(row.get("elapsed_seconds")) is not None and float(row["elapsed_seconds"]) <= checkpoint + TOL]
    if eligible:
        selected = max(eligible, key=lambda row: float(row["elapsed_seconds"]))
        lower, upper = as_float(selected.get("global_LB")), as_float(selected.get("incumbent_UB"))
        return {
            "snapshot_source": "algorithm_progress", "snapshot_process_seconds": as_float(selected.get("elapsed_seconds")),
            "certificate_at_checkpoint": False, "lower_bound": lower, "verified_upper_bound": upper,
            "gap": gap(lower, upper), "open_relevant_leaf_count": selected.get("unresolved_intervals"),
            "algorithm_work": None, "nodes": as_float(selected.get("nodes")), "simplex_iterations": None,
            "split_count": None, "event_type": selected.get("event"),
        }
    raise RuntimeError(f"no checkpoint evidence for {descriptor['scenario_id']} at {checkpoint}")


def main_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    checkpoints: list[dict[str, Any]] = []
    packages: dict[str, dict[str, Any]] = {}
    for descriptor in descriptors():
        result, marker = result_bundle(descriptor)
        solution_class = classify(result)
        conditions = certificate_conditions(result)
        certificate_valid = all(conditions.values()) if solution_class == "certified_optimal_solution" else False
        false_certificate = bool(result.get("strict_certified_original_problem")) and not all(conditions.values())
        verification = result.get("verification") or {}
        stats = route_stats(descriptor["scenario_id"])
        final_wall = float(result.get("final_process_wall_time_seconds", result.get("wall_time_seconds", 0.0)))
        cap = int(descriptor["solver_process_cap_seconds"])
        cap_tolerance = max(2.0, 0.01 * cap)
        cap_respected = final_wall <= cap + cap_tolerance
        reached_cap = not bool(result.get("strict_certified_original_problem")) and final_wall >= cap - max(10.0, 0.01 * cap)
        row = {
            "scenario_id": descriptor["scenario_id"], "panel_class": descriptor["panel_class"],
            "V": descriptor["V"], "M": descriptor["M"], "Q": descriptor["Q"],
            "T": descriptor["route_time_limit_seconds"], "common_comparison_horizon_seconds": 3600,
            "solver_process_cap_seconds": cap, "source_commit": SOURCE_FREEZE,
            "executable_sha256": EXECUTABLE_SHA256,
            "mathematical_instance_sha256": descriptor["mathematical_instance_sha256"],
            "run_identity_sha256": result.get("run_identity_sha256"), "solution_class": solution_class,
            "strict_certificate": bool(result.get("strict_certified_original_problem")),
            "certificate_valid": certificate_valid, "false_certificate": false_certificate,
            "objective": result.get("objective"), "G": result.get("G"), "P": result.get("P"),
            "lower_bound": result.get("lower_bound"), "verified_upper_bound": result.get("upper_bound"),
            "final_gap": result.get("gap"), "algorithm_work": result.get("external_gini_tree_work"),
            "algorithm_wall_time_seconds": final_wall, "nodes": result.get("external_gini_tree_nodes"),
            "simplex_iterations": result.get("external_gini_tree_simplex_iterations"),
            "split_count": result.get("external_gini_tree_split_count"),
            "interval_count": result.get("external_gini_tree_final_leaf_count"),
            "fixed_interval_model_count": result.get("external_gini_tree_model_count"),
            "peak_memory_gb": result.get("external_gini_tree_peak_memory_gb"),
            "verified_incumbent_available": bool(verification.get("original_solution_feasible") and verification.get("original_objective_recomputed")),
            "route_witness_package_available": stats["route_witness_package_available"],
            "archive_verification_passed": stats["archive_verification_passed"],
            "process_cap_respected": cap_respected, "reached_prescribed_cap": reached_cap,
            "strict_rejection_reason": result.get("strict_certificate_rejection_reason"),
            "result_sha256": marker["result_sha256"],
        }
        results.append(row)
        if stats["route_witness_package_available"]:
            packages[descriptor["scenario_id"]] = load_json(SOLUTIONS / descriptor["scenario_id"] / "native_solution.json")
        for checkpoint in descriptor["checkpoint_seconds"]:
            snapshot = checkpoint_snapshot(descriptor, result, int(checkpoint))
            checkpoints.append({
                "scenario_id": descriptor["scenario_id"], "V": descriptor["V"], "M": descriptor["M"],
                "Q": descriptor["Q"], "T": descriptor["route_time_limit_seconds"],
                "checkpoint_seconds": checkpoint, **snapshot,
            })
    if len(results) != 50:
        raise RuntimeError(f"expected 50 completed official rows, found {len(results)}")
    return results, checkpoints, packages


def monotonic_rows(results: list[dict[str, Any]], dimension: str) -> list[dict[str, Any]]:
    if dimension == "T":
        keys, order = ("V", "M", "Q"), "T"
    elif dimension == "M":
        keys, order = ("V", "Q", "T"), "M"
    elif dimension == "Q":
        keys, order = ("V", "M", "T"), "Q"
    else:
        raise ValueError(dimension)
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        grouped[tuple(row[key] for key in keys)].append(row)
    output: list[dict[str, Any]] = []
    for group_key, group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda row: row[order])
        for lower, higher in zip(ordered, ordered[1:]):
            exact_pair = bool(lower["certificate_valid"] and higher["certificate_valid"])
            delta = float(higher["objective"]) - float(lower["objective"]) if exact_pair else None
            violation = exact_pair and delta > TOL
            output.append({
                **{key: value for key, value in zip(keys, group_key)},
                f"lower_{order}": lower[order], f"higher_{order}": higher[order],
                "lower_scenario_id": lower["scenario_id"], "higher_scenario_id": higher["scenario_id"],
                "lower_solution_class": lower["solution_class"], "higher_solution_class": higher["solution_class"],
                "both_certified": exact_pair, "lower_objective": lower["objective"] if exact_pair else None,
                "higher_objective": higher["objective"] if exact_pair else None,
                "higher_minus_lower_objective": delta, "monotonicity_expected": "nonincreasing",
                "violation": violation, "claim_status": "exact_pair_audited" if exact_pair else "excluded_noncertified_pair",
            })
    return output


def plateau_rows(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, int, int], list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        if row["panel_class"] == "primary_q30":
            grouped[(int(row["V"]), int(row["M"]), int(row["Q"]))].append(row)
    output = []
    for key, group in sorted(grouped.items()):
        ordered = sorted(group, key=lambda row: row["T"])
        fully_certified = len(ordered) == 4 and all(row["certificate_valid"] for row in ordered)
        first_plateau = None
        if fully_certified:
            for index, row in enumerate(ordered):
                suffix = ordered[index:]
                if all(close(candidate["objective"], row["objective"]) for candidate in suffix):
                    first_plateau = row["T"]
                    break
        output.append({
            "V": key[0], "M": key[1], "Q": key[2], "fully_certified_series": fully_certified,
            "first_tested_plateau_T": first_plateau, "plateau_claim_available": first_plateau is not None,
            "T1800_objective": ordered[0]["objective"] if fully_certified else None,
            "T3600_objective": ordered[1]["objective"] if fully_certified else None,
            "T10800_objective": ordered[2]["objective"] if fully_certified else None,
            "T18000_objective": ordered[3]["objective"] if fully_certified else None,
            "status": "fully_certified_exact_plateau_audit" if fully_certified else "insufficient_exact_t_evidence",
        })
    return output


def transition_rows(results: list[dict[str, Any]], packages: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[int, int, int], dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in results:
        grouped[(int(row["V"]), int(row["M"]), int(row["Q"]))][int(row["T"])] = row
    output = []
    for key, by_t in sorted(grouped.items()):
        if 3600 not in by_t:
            continue
        for target_t in (10800, 18000):
            if target_t not in by_t:
                continue
            lower, higher = by_t[3600], by_t[target_t]
            left_package, right_package = packages.get(lower["scenario_id"]), packages.get(higher["scenario_id"])
            exact_pair = bool(lower["certificate_valid"] and higher["certificate_valid"])
            left_inventory = left_package.get("final_inventory") if left_package else None
            right_inventory = right_package.get("final_inventory") if right_package else None
            output.append({
                "V": key[0], "M": key[1], "Q": key[2], "baseline_T": 3600, "comparison_T": target_t,
                "baseline_scenario_id": lower["scenario_id"], "comparison_scenario_id": higher["scenario_id"],
                "both_certified": exact_pair,
                "objective_change_comparison_minus_baseline": float(higher["objective"]) - float(lower["objective"]) if exact_pair else None,
                "baseline_final_inventory": r56.canonical_json(left_inventory) if left_inventory is not None else None,
                "comparison_final_inventory": r56.canonical_json(right_inventory) if right_inventory is not None else None,
                "final_inventory_changed": left_inventory != right_inventory if left_inventory is not None and right_inventory is not None else None,
                "claim_status": "exact_pair_audited" if exact_pair else "descriptive_witness_only_or_noncertified",
            })
    return output


def route_tables(results: list[dict[str, Any]], packages: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    result_by_id = {row["scenario_id"]: row for row in results}
    route_summary, verification_rows, timing_rows, inventory_rows, descriptive_rows = [], [], [], [], []
    for descriptor in descriptors():
        scenario_id = descriptor["scenario_id"]
        result = result_by_id[scenario_id]
        stats = route_stats(scenario_id)
        package = packages.get(scenario_id)
        route_summary.append({
            "scenario_id": scenario_id, "solution_class": result["solution_class"],
            "verified_incumbent_available": result["verified_incumbent_available"], **stats,
        })
        if package is None:
            verification_rows.append({"scenario_id": scenario_id, "package_available": False, "passed": None, "failures": "no_verified_witness"})
            timing_rows.append({
                "scenario_id": scenario_id, "algorithm_wall_time_seconds": result["algorithm_wall_time_seconds"],
                "algorithm_work": result["algorithm_work"], "mandatory_in_memory_verification_seconds": None,
                "route_archive_materialization_seconds": None, "route_archive_serialization_seconds": None,
                "independent_archive_verification_seconds": None, "total_process_time_seconds": result["algorithm_wall_time_seconds"],
                "archive_time_excluded_from_algorithm_time": True,
            })
            continue
        verification = load_json(SOLUTIONS / scenario_id / "solution_verification.json")
        verification_rows.append({
            "scenario_id": scenario_id, "package_available": True, "passed": verification.get("passed"),
            "failures": ";".join(verification.get("failures", [])),
            **{key: value for key, value in verification.items() if key.endswith("_verified")},
            "optimization_or_repair_performed": verification.get("optimization_or_repair_performed"),
        })
        materialization = as_float(verification.get("route_archive_materialization_seconds")) or 0.0
        serialization = as_float(verification.get("route_archive_serialization_seconds")) or 0.0
        independent = as_float(verification.get("independent_archive_verification_seconds")) or 0.0
        timing_rows.append({
            "scenario_id": scenario_id, "algorithm_wall_time_seconds": package.get("algorithm_wall_time_seconds"),
            "algorithm_work": package.get("algorithm_work"), "mandatory_in_memory_verification_seconds": package.get("mandatory_in_memory_verification_seconds"),
            "mandatory_in_memory_verification_accounting": package.get("mandatory_in_memory_verification_accounting"),
            "route_archive_materialization_seconds": materialization, "route_archive_serialization_seconds": serialization,
            "independent_archive_verification_seconds": independent,
            "total_process_time_seconds": float(package.get("algorithm_wall_time_seconds") or 0.0) + materialization + serialization + independent,
            "archive_time_excluded_from_algorithm_time": True,
        })
        inventory_rows.append({
            "scenario_id": scenario_id, "solution_class": package["solution_class"], "certificate_status": package["certificate_status"],
            "objective": package["objective"], "final_inventory": r56.canonical_json(package["final_inventory"]),
            "native_solution_path": r56.repo_path(SOLUTIONS / scenario_id / "native_solution.json"),
            "native_solution_sha256": r56.sha256_file(SOLUTIONS / scenario_id / "native_solution.json"),
            "route_post_optimization_performed": package["route_post_optimization_performed"],
        })
        descriptive_rows.append({
            "scenario_id": scenario_id, "V": descriptor["V"], "M": descriptor["M"], "Q": descriptor["Q"],
            "T": descriptor["route_time_limit_seconds"], "solution_class": package["solution_class"], **stats,
            "witness_interpretation": "single_native_final_witness_not_post_optimized",
        })
    return route_summary, verification_rows, timing_rows, inventory_rows, descriptive_rows


def write_all() -> None:
    results, checkpoints, packages = main_rows()
    r56.write_csv(r56.EVIDENCE / "official_results.csv", results)
    r56.write_csv(r56.EVIDENCE / "official_checkpoints.csv", checkpoints)
    r56.write_csv(r56.EVIDENCE / "common_3600s_comparison.csv", [row for row in checkpoints if int(row["checkpoint_seconds"]) == 3600])
    extended_ids = {row["scenario_id"] for row in results if int(row["solver_process_cap_seconds"]) == 7200}
    r56.write_csv(r56.EVIDENCE / "extended_7200s_results.csv", [
        {**row, "certified_by_3600": bool(row["certificate_valid"] and float(row["algorithm_wall_time_seconds"]) <= 3600 + TOL),
         "additional_certificate_after_3600": bool(row["certificate_valid"] and float(row["algorithm_wall_time_seconds"]) > 3600 + TOL)}
        for row in results if row["scenario_id"] in extended_ids
    ])
    r56.write_csv(r56.EVIDENCE / "process_cap_audit.csv", [{
        "scenario_id": row["scenario_id"], "solver_process_cap_seconds": row["solver_process_cap_seconds"],
        "algorithm_wall_time_seconds": row["algorithm_wall_time_seconds"], "cap_respected": row["process_cap_respected"],
        "reached_prescribed_cap": row["reached_prescribed_cap"], "solution_class": row["solution_class"],
    } for row in results])
    r56.write_csv(r56.EVIDENCE / "solution_classification.csv", [{
        "scenario_id": row["scenario_id"], "solution_class": row["solution_class"],
        "strict_certificate": row["strict_certificate"], "verified_incumbent_available": row["verified_incumbent_available"],
        "correctness_failure": row["solution_class"] == "correctness_failure", "execution_failure": row["solution_class"] == "execution_failure",
    } for row in results])
    certificate_rows, false_rows = [], []
    for descriptor in descriptors():
        result, _ = result_bundle(descriptor)
        conditions = certificate_conditions(result)
        row = {"scenario_id": descriptor["scenario_id"], **conditions, "all_certificate_conditions_pass": all(conditions.values())}
        certificate_rows.append(row)
        false_rows.append({
            "scenario_id": descriptor["scenario_id"], "strict_label_present": conditions["strict_original_certificate"],
            "all_certificate_conditions_pass": all(conditions.values()),
            "false_certificate": conditions["strict_original_certificate"] and not all(conditions.values()),
            "classification": classify(result),
        })
    r56.write_csv(r56.EVIDENCE / "certificate_audit.csv", certificate_rows)
    r56.write_csv(r56.EVIDENCE / "false_certificate_audit.csv", false_rows)
    route_summary, verification_rows, timing_rows, inventory_rows, descriptive_rows = route_tables(results, packages)
    r56.write_csv(r56.EVIDENCE / "route_export_summary.csv", route_summary)
    r56.write_csv(r56.EVIDENCE / "independent_route_verification.csv", verification_rows)
    r56.write_csv(r56.EVIDENCE / "route_export_timing.csv", timing_rows)
    r56.write_csv(r56.EVIDENCE / "route_witness_inventory.csv", inventory_rows)
    r56.write_csv(r56.EVIDENCE / "native_route_descriptive_statistics.csv", descriptive_rows)
    r56.write_csv(r56.EVIDENCE / "route_feasibility_audit.csv", [{
        "scenario_id": row["scenario_id"], "package_available": row["package_available"], "independent_verification_passed": row["passed"],
        "optimization_or_repair_performed": row.get("optimization_or_repair_performed"), "failures": row["failures"],
    } for row in verification_rows])
    t_rows, m_rows, q_rows = monotonic_rows(results, "T"), monotonic_rows(results, "M"), monotonic_rows(results, "Q")
    r56.write_csv(r56.EVIDENCE / "t_objective_monotonicity.csv", t_rows)
    r56.write_csv(r56.EVIDENCE / "m_objective_monotonicity.csv", m_rows)
    r56.write_csv(r56.EVIDENCE / "q_objective_monotonicity.csv", q_rows)
    r56.write_csv(r56.EVIDENCE / "objective_plateau_analysis.csv", plateau_rows(results))
    r56.write_csv(r56.EVIDENCE / "final_inventory_transition.csv", transition_rows(results, packages))
    base_by_v = {int(row["V"]): row for row in load_json(r56.EVIDENCE / "base_landscape_manifest.json")["rows"]}
    instance_rows = []
    for descriptor in descriptors():
        base = base_by_v[int(descriptor["V"])]
        instance_rows.append({
            "scenario_id": descriptor["scenario_id"], "panel_class": descriptor["panel_class"],
            "V": descriptor["V"], "M": descriptor["M"], "Q": descriptor["Q"], "T": descriptor["route_time_limit_seconds"],
            "fleet_density_V_per_M": float(descriptor["V"]) / float(descriptor["M"]),
            "base_seed": base["seed"], "base_landscape_sha256": descriptor["base_landscape_sha256"],
            "fleet_variant_file_sha256": descriptor["fleet_variant_file_sha256"],
            "mathematical_instance_sha256": descriptor["mathematical_instance_sha256"],
            "capacity_mean": base["capacity_mean"], "total_initial_inventory": base["total_initial_inventory"],
            "total_target_inventory": base["total_target_inventory"], "surplus_count": base["surplus_count"],
            "deficit_count": base["deficit_count"], "distance_mean": base["distance_mean"], "distance_max": base["distance_max"],
        })
    r56.write_csv(r56.EVIDENCE / "paper_candidate_instance_table.csv", instance_rows)
    r56.write_csv(r56.EVIDENCE / "paper_candidate_result_table.csv", results)
    r56.write_csv(r56.EVIDENCE / "paper_candidate_route_table.csv", descriptive_rows)
    r56.write_csv(r56.EVIDENCE / "exact_solution_inventory.csv", [row for row in inventory_rows if row["certificate_status"]])
    r56.write_csv(r56.EVIDENCE / "noncertified_result_inventory.csv", [row for row in results if not row["certificate_valid"]])
    summary = {
        "rows": len(results), "certified_final": sum(bool(row["certificate_valid"]) for row in results),
        "certified_by_3600": sum(bool(row["certificate_valid"] and float(row["algorithm_wall_time_seconds"]) <= 3600 + TOL) for row in results),
        "additional_7200_certificates": sum(bool(row["certificate_valid"] and float(row["algorithm_wall_time_seconds"]) > 3600 + TOL) for row in results),
        "capped_noncertified": sum(bool(row["reached_prescribed_cap"]) for row in results),
        "verified_incumbents": sum(bool(row["verified_incumbent_available"]) for row in results),
        "exact_route_packages": sum(bool(row["certificate_valid"] and row["route_witness_package_available"]) for row in results),
        "nonexact_route_packages": sum(bool(not row["certificate_valid"] and row["route_witness_package_available"]) for row in results),
        "route_verification_failures": sum(bool(row["package_available"] and not row["passed"]) for row in verification_rows),
        "false_certificates": sum(bool(row["false_certificate"]) for row in false_rows),
        "correctness_failures": sum(row["solution_class"] == "correctness_failure" for row in results),
        "t_monotonicity_violations": sum(bool(row["violation"]) for row in t_rows),
        "m_monotonicity_violations": sum(bool(row["violation"]) for row in m_rows),
        "q_monotonicity_violations": sum(bool(row["violation"]) for row in q_rows),
    }
    r56.write_json(r56.EVIDENCE / "analysis_summary.json", summary)
    if not all(row["process_cap_respected"] for row in results):
        raise RuntimeError("process-cap audit failure")
    if summary["false_certificates"] or summary["correctness_failures"] or summary["route_verification_failures"]:
        raise RuntimeError("correctness or route archive audit failure")
    print(json.dumps(summary, indent=2, sort_keys=True))


def main() -> int:
    write_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
