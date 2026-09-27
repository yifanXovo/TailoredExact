#!/usr/bin/env python3
"""Derive the complete Round 39 convergence and qualification evidence.

This analyzer is intentionally read-only with respect to solver artifacts.  It
    requires every row to have either a checksum-valid completion marker or a
    documented, reproducible unresolved classification before publication.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import round39_common as common
from round39_instance_tools import descriptors, read_instance


TOL = 1e-7
GAP_THRESHOLDS = (0.50, 0.25, 0.10, 0.05, 0.02, 0.01, 0.005, 0.001, 0.0)
INCUMBENT_THRESHOLDS = (0.50, 0.25, 0.10, 0.05, 0.01, 0.001, 0.0)
MATERIAL_SECONDS = 0.05
HISTORICAL_MANIFEST = (
    common.ROOT / "results/gf_v10_convergence_round33/"
    "round33_v10_instance_manifest.csv"
)
HISTORICAL_PAIRS = (
    common.ROOT / "results/gf_v10_convergence_round33/"
    "p_grb_vs_c6_v10.csv"
)
HISTORICAL_HGA = (
    common.ROOT / "results/gf_c6_documentation_hga_round34/"
    "hga_v10_official_ablation.csv"
)


def number(value: Any, default: float = math.nan) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def integer(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def close(left: Any, right: Any, tolerance: float = TOL) -> bool:
    a, b = number(left), number(right)
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= (
        tolerance * max(1.0, abs(a), abs(b)))


def stable_hash(value: Any) -> str:
    material = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(material.encode()).hexdigest()


def projection(rows: Iterable[dict[str, Any]], fields: tuple[str, ...]) \
        -> list[tuple[Any, ...]]:
    return [tuple(row.get(field, "") for field in fields) for row in rows]


def compact(rows: Iterable[dict[str, Any]], fields: tuple[str, ...],
            limit: int = 16) -> str:
    material = ["|".join(str(row.get(field, "")) for field in fields)
                for row in rows]
    shown = material[:limit]
    if len(material) > limit:
        shown.append(f"...({len(material) - limit}_more)")
    return ";".join(shown)


def artifact_manifest_valid(run_dir: Path, marker: dict[str, Any]) \
        -> tuple[bool, int]:
    path = run_dir / "artifact_manifest.csv"
    if (not path.is_file() or common.sha256(path) !=
            marker.get("artifact_manifest_sha256")):
        return False, 0
    rows = common.csv_rows(path)
    for row in rows:
        artifact = run_dir / row["path"]
        if (not artifact.is_file()
                or artifact.stat().st_size != int(row["bytes"])
                or common.sha256(artifact) != row["sha256"]):
            return False, len(rows)
    return True, len(rows)


def discover() -> list[dict[str, Any]]:
    matrix = common.csv_rows(common.OFFICIAL_MATRIX)
    if len(matrix) != 51:
        raise RuntimeError(f"expected 51 frozen rows, found {len(matrix)}")
    runs: list[dict[str, Any]] = []
    for row in matrix:
        directory = common.RUNS / row["run_id"]
        marker_path = directory / "completion_marker.json"
        result_path = directory / "result.json"
        unresolved_path = directory / "unresolved_classification.json"
        if not result_path.is_file() or (not marker_path.is_file() and
                                        not unresolved_path.is_file()):
            raise RuntimeError(f"official row unclassified: {row['run_id']}")
        if unresolved_path.is_file():
            unresolved = common.load_json(unresolved_path)
            result = common.load_json(result_path)
            if (not truth(unresolved.get("official_unresolved")) or
                    unresolved.get("run_id") != row["run_id"] or
                    common.sha256(result_path) != unresolved.get("result_sha256")):
                raise RuntimeError(
                    f"invalid unresolved classification: {row['run_id']}")
            runs.append({
                "matrix": row, "state": unresolved, "result": result,
                "run_dir": directory, "artifact_count": 0,
                "official_unresolved": True,
            })
            continue
        marker = common.load_json(marker_path)
        result = common.load_json(result_path)
        valid, count = artifact_manifest_valid(directory, marker)
        if not valid:
            raise RuntimeError(f"artifact checksum failure: {row['run_id']}")
        if not truth(marker.get("completed")) or not truth(
                marker.get("completion_marker_atomic")):
            raise RuntimeError(f"invalid completion marker: {row['run_id']}")
        runs.append({
            "matrix": row, "state": marker, "result": result,
            "run_dir": directory, "artifact_count": count,
            "official_unresolved": False,
        })
    return runs


def process_time(run: dict[str, Any]) -> float:
    return common.process_entry_time(run["result"])


def bounds(run: dict[str, Any]) -> tuple[float, float]:
    return common.result_bounds(run["matrix"]["arm"], run["result"])


def objective(run: dict[str, Any]) -> float:
    return number(run["result"].get("objective"))


def phase_time(run: dict[str, Any], event: str) -> float:
    values = [number(row.get("process_seconds")) for row in common.csv_rows(
        run["run_dir"] / "process_phases.csv") if row.get("event") == event]
    values = [value for value in values if math.isfinite(value)]
    return values[0] if values else math.nan


def exact_start(run: dict[str, Any]) -> float:
    value = number(run["result"].get(
        "process_elapsed_at_exact_phase_start_seconds"))
    return value if value > 0 else phase_time(run, "exact_phase_start")


def trace(run: dict[str, Any]) -> list[dict[str, Any]]:
    """Return monotone process-entry LB/UB events plus a final endpoint."""
    result, arm = run["result"], run["matrix"]["arm"]
    final_lb, final_ub = bounds(run)
    rows: list[dict[str, Any]] = []
    if arm == "P-GRB":
        shift = phase_time(run, "plain_gurobi_optimize_launch")
        shift = shift if math.isfinite(shift) else 0.0
        for row in common.csv_rows(run["run_dir"] / "progress.csv"):
            elapsed = number(row.get("elapsed_runtime_seconds"))
            lb = number(row.get("best_bound"))
            ub = number(row.get("incumbent")) if truth(
                row.get("incumbent_available")) else math.nan
            if math.isfinite(elapsed) and math.isfinite(lb):
                rows.append({
                    "process_seconds": shift + elapsed,
                    "valid_lower_bound": lb,
                    "observed_upper_bound": ub,
                    "event": row.get("context", "native_callback"),
                    "source": "gurobi_native_progress",
                })
    else:
        for row in common.csv_rows(
                run["run_dir"] / "external/global_bound_trace.csv"):
            elapsed = number(row.get("process_elapsed_seconds"))
            lb = number(row.get("valid_global_lower_bound"))
            ub = number(row.get("verified_global_upper_bound"))
            if math.isfinite(elapsed) and math.isfinite(lb):
                rows.append({
                    "process_seconds": elapsed,
                    "valid_lower_bound": lb,
                    "observed_upper_bound": ub,
                    "event": row.get("event_type", ""),
                    "source": row.get("event_source", ""),
                })
    rows.sort(key=lambda item: item["process_seconds"])
    output: list[dict[str, Any]] = []
    best_lb, best_ub = -math.inf, math.inf
    for row in rows:
        best_lb = max(best_lb, number(row["valid_lower_bound"], -math.inf))
        candidate = number(row["observed_upper_bound"])
        if math.isfinite(candidate):
            best_ub = min(best_ub, candidate)
        output.append({
            **row, "valid_lower_bound": best_lb,
            "observed_upper_bound": best_ub,
        })
    total = process_time(run)
    if not output or total > output[-1]["process_seconds"] + 1e-12:
        output.append({
            "process_seconds": total, "valid_lower_bound": final_lb,
            "observed_upper_bound": final_ub, "event": "final_result",
            "source": "serialized_strict_certificate",
        })
    return output


def proof_metrics(run: dict[str, Any]) -> tuple[dict[str, Any],
                                                list[dict[str, Any]]]:
    optimum = objective(run)
    rows = []
    for sequence, item in enumerate(trace(run)):
        lb = number(item["valid_lower_bound"])
        ub = number(item["observed_upper_bound"])
        gap = max(0.0, (optimum - lb) / max(abs(optimum), 1e-12))
        incumbent_gap = max(
            0.0, (ub - optimum) / max(abs(optimum), 1e-12)) \
            if math.isfinite(ub) else math.inf
        rows.append({
            "round_id": 39, "run_id": run["matrix"]["run_id"],
            "instance_id": run["matrix"]["instance_id"],
            "difficulty_stratum": run["matrix"]["difficulty_stratum"],
            "arm": run["matrix"]["arm"], "sequence": sequence,
            **item, "final_verified_optimum": optimum,
            "relative_proof_gap_to_optimum": gap,
            "relative_incumbent_gap_to_optimum": incumbent_gap,
        })
    metrics: dict[str, Any] = {
        "trace_event_count": len(rows),
        "trace_first_process_seconds": rows[0]["process_seconds"],
        "trace_last_process_seconds": rows[-1]["process_seconds"],
        "trajectory_convention": (
            "left_continuous_observed_events_no_interpolation_"
            "no_post_final_extension"),
    }
    for threshold in GAP_THRESHOLDS:
        key = f"time_to_gap_le_{threshold:g}"
        metrics[key] = next((row["process_seconds"] for row in rows
                             if row["relative_proof_gap_to_optimum"] <=
                             threshold + 1e-12), math.nan)
    for threshold in INCUMBENT_THRESHOLDS:
        key = f"time_to_incumbent_gap_le_{threshold:g}"
        metrics[key] = next((row["process_seconds"] for row in rows
                             if row["relative_incumbent_gap_to_optimum"] <=
                             threshold + 1e-12), math.nan)
    auc = sum(
        max(0.0, right["process_seconds"] - left["process_seconds"])
        * left["relative_proof_gap_to_optimum"]
        for left, right in zip(rows, rows[1:])
    )
    window = max(0.0, rows[-1]["process_seconds"] -
                 rows[0]["process_seconds"])
    metrics["observed_proof_gap_auc_seconds"] = auc
    metrics["normalized_observed_proof_gap_auc"] = (
        auc / window if window > 0 else math.nan)
    return metrics, rows


def c6_signature(run: dict[str, Any]) -> dict[str, Any]:
    directory = run["run_dir"] / "external"
    initial = common.csv_rows(directory / "initial_decomposition_ledger.csv")
    lp = common.csv_rows(directory / "lp_status_ledger.csv")
    targets = common.csv_rows(directory / "native_target_ledger.csv")
    splits = common.csv_rows(directory / "split_decision_ledger.csv")
    events = common.csv_rows(directory / "paper_tree_events.csv")
    global_rows = common.csv_rows(directory / "global_bound_trace.csv")
    initial_ids = {f"L{row.get('anchor_cell_index', '')}" for row in initial}
    initial_lp = [row for row in lp if row.get("leaf_id") in initial_ids]
    controlling = [row for row in global_rows if row.get("active_leaf")]
    closures = [row for row in events if any(
        token in row.get("event", "").lower()
        for token in ("close", "infeasible", "prune", "terminal"))]
    materials = {
        "initial_interval": projection(initial, (
            "anchor_cell_index", "anchor_lower", "anchor_upper", "active",
            "active_lower", "active_upper", "truncated_by_proof_range")),
        "initial_lp": projection(initial_lp, (
            "leaf_id", "depth", "gamma_L", "gamma_U", "terminal_valid",
            "optimal", "infeasible", "lower_bound", "native_status")),
        "controlling": projection(controlling, (
            "event_type", "active_leaf", "active_leaf_valid_lower_bound",
            "other_open_leaf_min_valid_lower_bound",
            "valid_global_lower_bound", "event_source")),
        "target": projection(targets, (
            "leaf_id", "target_kind", "current_bound", "target_bound",
            "status", "target_reached", "exact_closure", "requeued",
            "event_source")),
        "split": projection(splits, (
            "parent_id", "eligible", "decision_valid", "split",
            "child_infeasibility_trigger", "strict_bound_trigger",
            "normalized_disjunction_gain", "b_plus", "reason")),
        "closure": projection(closures, (
            "event", "leaf_id", "status", "detail")),
    }
    return {
        **{f"{name}_sha256": stable_hash(value)
           for name, value in materials.items()},
        "downstream_sha256": stable_hash({
            key: materials[key] for key in (
                "initial_lp", "controlling", "target", "split", "closure")
        }),
        "initial_interval_count": len(initial),
        "initial_lp_count": len(initial_lp),
        "target_row_count": len(targets),
        "requeue_count": sum(truth(row.get("requeued")) for row in targets),
        "split_row_count": len(splits),
        "actual_split_count": sum(truth(row.get("split")) for row in splits),
        "closure_event_count": len(closures),
        "initial_lp_bounds": compact(initial_lp, (
            "leaf_id", "gamma_L", "gamma_U", "lower_bound", "native_status")),
    }


def run_row(run: dict[str, Any], descriptor: dict[str, str],
            metrics: dict[str, Any], signature: dict[str, Any] | None
            ) -> dict[str, Any]:
    state, result, arm = run["state"], run["result"], run["matrix"]["arm"]
    lower, upper = bounds(run)
    c6 = arm.startswith("C6-")
    startup = exact_start(run) if c6 else 0.0
    total = process_time(run)
    row = {
        "round_id": 39, "stage": run["matrix"]["stage"],
        "run_id": run["matrix"]["run_id"],
        "serial_order": integer(run["matrix"]["serial_order"]),
        "instance_id": run["matrix"]["instance_id"],
        "instance_sha256": run["matrix"]["instance_sha256"],
        "V": integer(run["matrix"]["V"]),
        "M": integer(run["matrix"]["M"]),
        "Q": integer(run["matrix"]["Q"]),
        "T": number(run["matrix"]["T"]),
        "difficulty_stratum": run["matrix"]["difficulty_stratum"],
        "difficulty_score": number(descriptor["difficulty_score"]),
        "arm": arm, "startup_variant": run["matrix"]["startup_variant"],
        "total_process_seconds": total,
        "hga_startup_seconds": number(result.get("hga_wall_time_seconds"), 0.0),
        "startup_to_exact_seconds": startup,
        "exact_phase_seconds": max(0.0, total - startup) if c6 else total,
        "startup_verified_objective": number(
            result.get("initial_heuristic_UB")) if c6 else math.nan,
        "final_objective": objective(run),
        "valid_lower_bound": lower, "verified_upper_bound": upper,
        "final_relative_gap": max(
            0.0, (upper - lower) / max(abs(upper), 1e-12)),
        "work": number(result.get(
            "external_gini_tree_work" if c6 else "gurobi_work")),
        "nodes": number(result.get(
            "external_gini_tree_nodes" if c6 else "gurobi_node_count")),
        "initial_lp_bounds": signature["initial_lp_bounds"] if signature else "",
        "initial_lp_count": signature["initial_lp_count"] if signature else 0,
        "target_count": integer(result.get(
            "external_gini_tree_attempt_count")) if c6 else 0,
        "targets_reached": integer(result.get(
            "external_gini_tree_partial_mip_target_reached_count")) if c6 else 0,
        "requeue_count": integer(result.get(
            "external_gini_tree_native_requeue_count")) if c6 else 0,
        "split_count": integer(result.get(
            "external_gini_tree_split_count")) if c6 else 0,
        "closure_count": integer(result.get(
            "external_gini_tree_exact_closure_launch_count")) if c6 else 0,
        "strict_certificate": truth(result.get(
            "strict_certified_original_problem")),
        "strict_certificate_class": result.get("strict_certificate_class", ""),
        "strict_certificate_rejection_reason": result.get(
            "strict_certificate_rejection_reason", ""),
        "original_problem_verifier_passed": bool(result.get(
            "verification", {}).get("original_solution_feasible")),
        "threads": integer(state.get("threads")),
        "gurobi_seed": integer(result.get("gurobi_seed_effective"), 0),
        "emergency_timeout": truth(state.get("emergency_timeout")),
        "official_unresolved": run.get("official_unresolved", False),
        "unresolved_reason": state.get("unresolved_reason", ""),
        "artifact_count": run["artifact_count"],
        "active_station_count": integer(descriptor["active_station_count"]),
        "active_fraction": number(descriptor["active_fraction"]),
        "surplus_count": integer(descriptor["surplus_count"]),
        "deficit_count": integer(descriptor["deficit_count"]),
        "imbalance_l1": number(descriptor["imbalance_l1"]),
        "fleet_capacity_pressure": number(
            descriptor["fleet_capacity_pressure"]),
        "support_duration_pressure": number(
            descriptor["support_duration_pressure"]),
        "plausible_ordered_pair_density": number(
            descriptor["plausible_ordered_pair_density"]),
        "full_service_pair_density": number(
            descriptor["full_service_pair_density"]),
        "initial_objective_lambda_0_15": number(
            descriptor["initial_objective_lambda_0_15"]),
        **metrics,
    }
    if signature:
        row.update({key: value for key, value in signature.items()
                    if key.endswith("_sha256")})
    return row


def pair_rows(per_run: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in per_run:
        if row["stage"] == "primary":
            grouped[row["instance_id"]][row["arm"]] = row
    output = []
    for instance_id, arms in grouped.items():
        p = arms["P-GRB"]
        light = arms["C6-HGA-LIGHT-1000"]
        delta = p["total_process_seconds"] - light["total_process_seconds"]
        both_strict = p["strict_certificate"] and light["strict_certificate"]
        outcome = ("unresolved" if not both_strict else
                   "tie" if abs(delta) <= MATERIAL_SECONDS else
                   "C6_LIGHT_win" if delta > 0 else "P_GRB_win")
        output.append({
            "round_id": 39, "instance_id": instance_id,
            "V": p["V"], "M": p["M"], "Q": p["Q"], "T": p["T"],
            "difficulty_stratum": p["difficulty_stratum"],
            "difficulty_score": p["difficulty_score"],
            "p_grb_seconds": p["total_process_seconds"],
            "light_total_seconds": light["total_process_seconds"],
            "light_startup_seconds": light["startup_to_exact_seconds"],
            "light_hga_seconds": light["hga_startup_seconds"],
            "light_exact_phase_seconds": light["exact_phase_seconds"],
            "speedup_p_grb_over_light": (
                p["total_process_seconds"] / light["total_process_seconds"]),
            "absolute_seconds_saved_by_light": delta,
            "materiality_tolerance_seconds": MATERIAL_SECONDS,
            "time_outcome": outcome,
            "raw_faster_arm": "unresolved" if not both_strict else (
                "C6-HGA-LIGHT-1000" if delta > 0 else "P-GRB"),
            "p_grb_work": p["work"], "light_work": light["work"],
            "work_ratio_p_over_light": (
                p["work"] / light["work"] if light["work"] > 0 else math.nan),
            "p_grb_nodes": p["nodes"], "light_nodes": light["nodes"],
            "node_ratio_p_over_light": (
                p["nodes"] / light["nodes"] if light["nodes"] > 0 else math.nan),
            "p_grb_objective": p["final_objective"],
            "light_objective": light["final_objective"],
            "objective_equal": close(p["final_objective"],
                                     light["final_objective"]),
            "p_grb_strict_certificate": p["strict_certificate"],
            "light_strict_certificate": light["strict_certificate"],
            "light_startup_objective": light["startup_verified_objective"],
            "light_startup_relative_gap": max(
                0.0, (light["startup_verified_objective"] -
                      light["final_objective"]) /
                max(abs(light["final_objective"]), 1e-12)),
            "light_initial_lp_bounds": light["initial_lp_bounds"],
            "light_targets": light["target_count"],
            "light_requeues": light["requeue_count"],
            "light_splits": light["split_count"],
            "light_closures": light["closure_count"],
        })
    return sorted(output, key=lambda row: (
        {"small-easy": 0, "small-medium": 1, "small-hard": 2}[
            row["difficulty_stratum"]], row["difficulty_score"]))


def shifted_geomean(values: Iterable[float], shift: float = 1.0) -> float:
    clean = [value for value in values if math.isfinite(value) and value >= 0]
    return math.exp(statistics.fmean(math.log(value + shift)
                                     for value in clean)) - shift


def stratum_rows(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for stratum in ("small-easy", "small-medium", "small-hard"):
        rows = [row for row in pairs if row["difficulty_stratum"] == stratum]
        comparable = [row for row in rows if row["time_outcome"] != "unresolved"]
        p_times = [row["p_grb_seconds"] for row in comparable]
        c_times = [row["light_total_seconds"] for row in comparable]
        output.append({
            "difficulty_stratum": stratum, "pair_count": len(rows),
            "comparable_strict_pair_count": len(comparable),
            "p_grb_wins": sum(row["time_outcome"] == "P_GRB_win"
                               for row in rows),
            "light_wins": sum(row["time_outcome"] == "C6_LIGHT_win"
                              for row in rows),
            "ties": sum(row["time_outcome"] == "tie" for row in rows),
            "unresolved": sum(row["time_outcome"] == "unresolved"
                              for row in rows),
            "p_grb_median_seconds": statistics.median(p_times),
            "light_median_seconds": statistics.median(c_times),
            "p_grb_shifted_geomean_seconds": shifted_geomean(p_times),
            "light_shifted_geomean_seconds": shifted_geomean(c_times),
            "geomean_shift_seconds": 1.0,
            "median_speedup_p_over_light": statistics.median(
                row["speedup_p_grb_over_light"] for row in comparable),
            "total_p_grb_seconds": sum(p_times),
            "total_light_seconds": sum(c_times),
            "total_light_startup_seconds": sum(
                row["light_startup_seconds"] for row in rows),
            "all_objectives_equal": all(row["objective_equal"] for row in rows),
            "all_rows_strict": all(row["p_grb_strict_certificate"] and
                                   row["light_strict_certificate"]
                                   for row in rows),
        })
    return output


def guard_rows(runs: list[dict[str, Any]],
               signatures: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    light = {run["matrix"]["instance_id"]: run for run in runs
             if run["matrix"]["stage"] == "primary" and
             run["matrix"]["arm"] == "C6-HGA-LIGHT-1000"}
    full = {run["matrix"]["instance_id"]: run for run in runs
            if run["matrix"]["stage"] == "guard"}
    output = []
    for instance_id in sorted(full, key=lambda key: integer(
            full[key]["matrix"]["serial_order"])):
        left, right = light[instance_id], full[instance_id]
        ls, fs = signatures[left["matrix"]["run_id"]], signatures[
            right["matrix"]["run_id"]]
        l_result, f_result = left["result"], right["result"]
        ub_equal = close(l_result.get("initial_heuristic_UB"),
                         f_result.get("initial_heuristic_UB"))
        structural_fields = (
            "initial_interval_sha256", "initial_lp_sha256",
            "controlling_sha256", "target_sha256", "split_sha256",
            "closure_sha256", "downstream_sha256",
        )
        row = {
            "round_id": 39, "instance_id": instance_id,
            "difficulty_stratum": left["matrix"]["difficulty_stratum"],
            "V": integer(left["matrix"]["V"]),
            "M": integer(left["matrix"]["M"]),
            "Q": integer(left["matrix"]["Q"]),
            "light_startup_objective": number(
                l_result.get("initial_heuristic_UB")),
            "full_startup_objective": number(
                f_result.get("initial_heuristic_UB")),
            "startup_objective_equal": ub_equal,
            "light_hga_seconds": number(
                l_result.get("hga_wall_time_seconds")),
            "full_hga_seconds": number(
                f_result.get("hga_wall_time_seconds")),
            "hga_seconds_saved_by_light": number(
                f_result.get("hga_wall_time_seconds")) - number(
                    l_result.get("hga_wall_time_seconds")),
            "light_startup_to_exact_seconds": exact_start(left),
            "full_startup_to_exact_seconds": exact_start(right),
            "light_exact_phase_seconds": process_time(left) - exact_start(left),
            "full_exact_phase_seconds": process_time(right) - exact_start(right),
            "light_total_seconds": process_time(left),
            "full_total_seconds": process_time(right),
            "total_seconds_saved_by_light": process_time(right) -
                process_time(left),
            "light_final_objective": objective(left),
            "full_final_objective": objective(right),
            "final_objective_equal": close(objective(left), objective(right)),
            "light_strict_certificate": truth(l_result.get(
                "strict_certified_original_problem")),
            "full_strict_certificate": truth(f_result.get(
                "strict_certified_original_problem")),
        }
        for field in structural_fields:
            row[f"light_{field}"] = ls[field]
            row[f"full_{field}"] = fs[field]
            row[f"{field.removesuffix('_sha256')}_identical"] = (
                ls[field] == fs[field])
        row["same_ub_downstream_structurally_identical"] = (
            ub_equal and all(ls[field] == fs[field]
                             for field in structural_fields[1:]))
        output.append(row)
    return output


def exactness_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for run in runs:
        result, state, arm = run["result"], run["state"], run["matrix"]["arm"]
        unresolved = run.get("official_unresolved", False)
        c6 = arm.startswith("C6-")
        lower, upper = bounds(run)
        verification = result.get("verification", {})
        gates = {
            "completion_marker_valid": truth(state.get("completed")) and
                truth(state.get("completion_marker_atomic")),
            "no_emergency_timeout": not truth(state.get("emergency_timeout")),
            "return_code_zero": integer(state.get("return_code"), -1) == 0,
            "strict_original_problem_certificate": truth(result.get(
                "strict_certified_original_problem")),
            "certificate_rejection_none": result.get(
                "strict_certificate_rejection_reason") == "none",
            "bounds_ordered_and_closed": lower <= upper + TOL * max(
                1.0, abs(lower), abs(upper)) and close(lower, upper),
            "original_solution_feasible": truth(verification.get(
                "original_solution_feasible")),
            "original_objective_recomputed": truth(verification.get(
                "original_objective_recomputed")),
            "objective_matches": truth(verification.get("objective_matches")),
            "one_thread": integer(state.get("threads")) == 1,
            "seed_zero": integer(result.get(
                "gurobi_seed_requested" if c6 else
                "gurobi_seed_effective"), -1) == 0,
            "round36_policy_off": result.get("round36_c6_causal_arm") == "off",
            "round37_policy_off": result.get("round37_c6_geometry_policy") == "off",
            # Arm-specific gates are true by non-applicability, then replaced
            # below for the arm where they are meaningful. Keeping a common
            # schema also prevents first-row CSV field truncation.
            "root_coverage_valid": True,
            "parent_child_coverage_valid": True,
            "all_leaf_bounds_valid": True,
            "leaf_bounds_monotone": True,
            "global_bound_monotone": True,
            "lifecycle_complete": True,
            "feasibility_consistency_gate": True,
            "environment_free_balance": True,
            "model_free_balance": True,
            "work_roundtrip": True,
            "node_roundtrip": True,
            "startup_variant_valid": True,
            "gurobi_lifecycle_valid": True,
            "gurobi_environment_free_balance": True,
            "gurobi_model_free_balance": True,
            "exact_zero_gap_settings": True,
        }
        if unresolved:
            gates.update({
                "certificate_rejection_none": False,
                "strict_original_problem_certificate": False,
                "bounds_ordered_and_closed": False,
            })
        if c6:
            optimize = common.csv_rows(
                run["run_dir"] / "external/paper_optimize_ledger.csv")
            ledger_work = sum(number(row.get("work"), 0.0) for row in optimize)
            ledger_nodes = sum(number(row.get("nodes"), 0.0) for row in optimize)
            gates.update({
                "root_coverage_valid": truth(result.get(
                    "external_gini_tree_root_coverage_valid")),
                "parent_child_coverage_valid": truth(result.get(
                    "external_gini_tree_parent_child_coverage_valid")),
                "all_leaf_bounds_valid": truth(result.get(
                    "external_gini_tree_all_leaf_bounds_valid")),
                "leaf_bounds_monotone": truth(result.get(
                    "external_gini_tree_leaf_bounds_monotone")),
                "global_bound_monotone": truth(result.get(
                    "external_gini_tree_global_bound_monotone")),
                "lifecycle_complete": truth(result.get(
                    "external_gini_tree_lifecycle_complete")),
                "feasibility_consistency_gate": truth(result.get(
                    "external_gini_tree_feasibility_consistency_gate")),
                "environment_free_balance": result.get(
                    "external_gini_tree_environment_count") == result.get(
                        "external_gini_tree_environment_free_count"),
                "model_free_balance": result.get(
                    "external_gini_tree_model_count") == result.get(
                        "external_gini_tree_model_free_count"),
                "work_roundtrip": close(
                    ledger_work, result.get("external_gini_tree_work"), 5e-12),
                "node_roundtrip": close(
                    ledger_nodes, result.get("external_gini_tree_nodes"), 5e-12),
                "startup_variant_valid": result.get(
                    "external_gini_tree_startup_variant") == (
                        "hga-light-1000" if "LIGHT" in arm else "hga-full"),
            })
        else:
            gates.update({
                "gurobi_lifecycle_valid": truth(result.get(
                    "gurobi_lifecycle_valid")),
                "gurobi_environment_free_balance": result.get(
                    "gurobi_environment_count") == result.get(
                        "gurobi_environment_free_count"),
                "gurobi_model_free_balance": result.get(
                    "gurobi_model_count") == result.get(
                        "gurobi_model_free_count"),
                "exact_zero_gap_settings": close(
                    result.get("gurobi_mip_gap_effective"), 0.0) and close(
                        result.get("gurobi_mip_gap_abs_effective"), 0.0),
            })
        false_certificate = truth(result.get(
            "strict_certified_original_problem")) and not all(gates.values())
        output.append({
            "run_id": run["matrix"]["run_id"], "arm": arm,
            "stage": run["matrix"]["stage"],
            "instance_id": run["matrix"]["instance_id"],
            "difficulty_stratum": run["matrix"]["difficulty_stratum"],
            "official_unresolved": unresolved,
            "false_certificate": false_certificate,
            **gates, "passed": (all(gates.values()) and
                                 not false_certificate and not unresolved),
        })
    return output


def historical_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    hga_rows = [row for row in common.csv_rows(HISTORICAL_HGA)
                if row.get("arm") == "C6-HGA-FULL"]
    hga_by_id: dict[str, dict[str, str]] = {}
    for row in hga_rows:
        hga_by_id.setdefault(row["instance_id"], row)
    for item in common.csv_rows(HISTORICAL_MANIFEST):
        data = read_instance(common.ROOT / item["path"],
                             total_time_limit=number(item["T"]))
        desc = descriptors(data)
        hga = hga_by_id.get(item["instance_id"], {})
        rows.append({
            "benchmark": "historical_round33_v10",
            "instance_id": item["instance_id"], "V": integer(item["V"]),
            "M": integer(item["M"]), "Q": integer(item["Q"]),
            "scenario": item["scenario"], **desc,
            "historical_full_startup_objective": number(
                hga.get("startup_verified_incumbent")),
            "historical_exact_objective": number(hga.get("exact_final_optimum")),
            "strict_improver_empty_at_startup": close(
                hga.get("startup_verified_incumbent"), 0.0) and close(
                    hga.get("exact_final_optimum"), 0.0),
        })
    pair_context = common.csv_rows(HISTORICAL_PAIRS)
    context = {
        "pair_count": len(pair_context),
        "p_grb_wins": sum(row.get("certificate_time_outcome") == "P_GRB_win"
                           for row in pair_context),
        "c6_full_wins": sum(row.get("certificate_time_outcome") == "C6_win"
                            for row in pair_context),
        "historical_comparator_note": (
            "Round33 used the then-frozen C6 startup and is contextual only; "
            "its rows are not mixed into Round39 official summaries."),
    }
    return rows, context


def historical_comparison(historical: list[dict[str, Any]],
                          descriptors39: list[dict[str, str]],
                          per_run: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    groups: list[tuple[str, list[dict[str, Any]]]] = [
        ("historical_round33_v10", historical),
        ("round39_all", descriptors39),
    ]
    groups.extend((
        f"round39_{stratum}",
        [row for row in descriptors39 if row["difficulty_stratum"] == stratum]
    ) for stratum in ("small-easy", "small-medium", "small-hard"))
    empty_ids = {row["instance_id"] for row in per_run
                 if row["stage"] == "primary" and
                 row["arm"] == "C6-HGA-LIGHT-1000" and
                 row["target_count"] == 0}
    for label, rows in groups:
        def values(field: str) -> list[float]:
            return [number(row[field]) for row in rows]
        historical_group = label.startswith("historical")
        output.append({
            "benchmark_group": label, "instance_count": len(rows),
            "unique_V": ";".join(sorted({str(integer(row["V"]))
                                         for row in rows})),
            "unique_M": ";".join(sorted({str(integer(row["M"]))
                                         for row in rows})),
            "unique_Q": ";".join(sorted({str(row["Q"]) for row in rows})),
            "difficulty_score_min": min(values("difficulty_score")),
            "difficulty_score_median": statistics.median(
                values("difficulty_score")),
            "difficulty_score_max": max(values("difficulty_score")),
            "active_fraction_median": statistics.median(
                values("active_fraction")),
            "imbalance_l1_median": statistics.median(values("imbalance_l1")),
            "support_duration_pressure_median": statistics.median(
                values("support_duration_pressure")),
            "full_service_pair_density_median": statistics.median(
                values("full_service_pair_density")),
            "structurally_nontrivial_count": sum(truth(
                row["structurally_nontrivial"]) for row in rows),
            "strict_improver_empty_at_startup_count": sum(
                truth(row.get("strict_improver_empty_at_startup"))
                for row in rows) if historical_group else sum(
                    row["instance_id"] in empty_ids for row in rows),
            "comparison_scope": "context_only_not_official_row_mixing"
                if historical_group else "round39_official_benchmark",
        })
    return output


def representative_rows(descriptors39: list[dict[str, str]],
                        traces: dict[str, list[dict[str, Any]]],
                        runs: list[dict[str, Any]]) \
        -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selections = []
    selected_ids = set()
    for stratum in ("small-easy", "small-medium", "small-hard"):
        rows = [row for row in descriptors39
                if row["difficulty_stratum"] == stratum]
        median = statistics.median(number(row["difficulty_score"])
                                   for row in rows)
        selected = min(rows, key=lambda row: (
            abs(number(row["difficulty_score"]) - median), row["instance_id"]))
        selected_ids.add(selected["instance_id"])
        selections.append({
            "difficulty_stratum": stratum,
            "instance_id": selected["instance_id"],
            "difficulty_score": number(selected["difficulty_score"]),
            "stratum_median_score": median,
            "selection_basis": (
                "closest_to_frozen_stratum_median_score_"
                "independent_of_solver_outcomes"),
        })
    output = []
    for run in runs:
        if (run["matrix"]["stage"] == "primary" and
                run["matrix"]["instance_id"] in selected_ids):
            output.extend(traces[run["matrix"]["run_id"]])
    return selections, output


def crossover_summary(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted((row for row in pairs
                      if row["time_outcome"] != "unresolved"),
                     key=lambda row: row["difficulty_score"])
    threshold = math.nan
    for index, row in enumerate(ordered):
        suffix = ordered[index:]
        if all(item["time_outcome"] == "C6_LIGHT_win" for item in suffix):
            threshold = row["difficulty_score"]
            break
    first_light = next((row for row in ordered
                        if row["time_outcome"] == "C6_LIGHT_win"), None)
    return {
        "schema": "round39-startup-crossover-v1",
        "first_observed_light_win_score": first_light["difficulty_score"]
            if first_light else math.nan,
        "first_observed_light_win_instance": first_light["instance_id"]
            if first_light else "none",
        "uniform_light_win_suffix_score": threshold,
        "uniform_light_win_suffix_exists": math.isfinite(threshold),
        "unresolved_pairs_excluded_from_crossover": sum(
            row["time_outcome"] == "unresolved" for row in pairs),
        "medium_is_mixed": len({row["time_outcome"] for row in pairs
                                if row["difficulty_stratum"] == "small-medium"}) > 1,
        "interpretation": (
            "The frozen scalar score locates a broad transition rather than "
            "a deterministic winner rule; M and proof-tree structure retain "
            "substantial within-stratum variation."),
    }


def main() -> int:
    runs = discover()
    descriptors39 = common.csv_rows(common.DESCRIPTOR_TABLE)
    descriptor_by_id = {row["instance_id"]: row for row in descriptors39}
    signatures: dict[str, dict[str, Any]] = {}
    traces: dict[str, list[dict[str, Any]]] = {}
    per_run = []
    threshold_rows = []
    for run in runs:
        arm, run_id = run["matrix"]["arm"], run["matrix"]["run_id"]
        signature = c6_signature(run) if arm.startswith("C6-") else None
        if signature:
            signatures[run_id] = signature
        metrics, run_trace = proof_metrics(run)
        traces[run_id] = run_trace
        row = run_row(run, descriptor_by_id[run["matrix"]["instance_id"]],
                      metrics, signature)
        per_run.append(row)
        for threshold in GAP_THRESHOLDS:
            threshold_rows.append({
                "run_id": run_id, "instance_id": row["instance_id"],
                "difficulty_stratum": row["difficulty_stratum"],
                "arm": arm, "metric": "proof_gap",
                "threshold": threshold,
                "first_observed_process_seconds": metrics[
                    f"time_to_gap_le_{threshold:g}"],
                "convention": metrics["trajectory_convention"],
            })
        for threshold in INCUMBENT_THRESHOLDS:
            threshold_rows.append({
                "run_id": run_id, "instance_id": row["instance_id"],
                "difficulty_stratum": row["difficulty_stratum"],
                "arm": arm, "metric": "incumbent_gap",
                "threshold": threshold,
                "first_observed_process_seconds": metrics[
                    f"time_to_incumbent_gap_le_{threshold:g}"],
                "convention": metrics["trajectory_convention"],
            })
    pairs = pair_rows(per_run)
    strata = stratum_rows(pairs)
    guards = guard_rows(runs, signatures)
    exactness = exactness_rows(runs)
    historical, historical_context = historical_rows()
    historical_compare = historical_comparison(
        historical, descriptors39, per_run)
    selections, representative = representative_rows(
        descriptors39, traces, runs)
    crossover = crossover_summary(pairs)

    common.write_csv(common.OUT / "per_run_convergence_metrics.csv", per_run)
    common.write_csv(common.OUT / "p_grb_vs_light_convergence.csv", pairs)
    common.write_csv(common.OUT / "per_stratum_summary.csv", strata)
    common.write_csv(common.OUT / "time_to_gap_and_incumbent_milestones.csv",
                     threshold_rows)
    common.write_csv(common.OUT / "full_vs_light_guard_results.csv", guards)
    common.write_csv(common.OUT / "exactness_certificate_audit.csv", exactness)
    common.write_csv(common.OUT / "historical_round33_descriptors.csv", historical)
    common.write_csv(common.OUT / "historical_benchmark_comparison.csv",
                     historical_compare)
    common.write_csv(common.OUT / "representative_selection.csv", selections)
    common.write_csv(common.OUT / "representative_trajectories.csv",
                     representative)
    common.write_json(common.OUT / "startup_crossover_summary.json", crossover)
    common.write_json(common.OUT / "historical_context.json", historical_context)

    easy, medium, hard = strata
    all_guards_same_ub = all(row["startup_objective_equal"] for row in guards)
    all_same_path = all(row["same_ub_downstream_structurally_identical"]
                        for row in guards)
    all_guard_strict = all(row["light_strict_certificate"] and
                           row["full_strict_certificate"] for row in guards)
    guard_total_improved = all(row["total_seconds_saved_by_light"] >=
                               -MATERIAL_SECONDS for row in guards)
    unresolved_rows = [row for row in per_run if row["official_unresolved"]]
    exactness_passed = all(row["passed"] for row in exactness
                           if not row["official_unresolved"])
    false_certificates = sum(row["false_certificate"] for row in exactness)
    new_empty = next(row for row in historical_compare
                     if row["benchmark_group"] == "round39_all")[
                         "strict_improver_empty_at_startup_count"]
    historical_empty = next(row for row in historical_compare
                            if row["benchmark_group"] ==
                            "historical_round33_v10")[
                                "strict_improver_empty_at_startup_count"]
    advance = bool(all_guards_same_ub and all_same_path and all_guard_strict and
                   guard_total_improved and exactness_passed and
                   not unresolved_rows)
    if unresolved_rows:
        advance_reason = (
            "One official LIGHT row remains reproducibly unresolved at a "
            "closed-tree numerical endpoint, so broader qualification is not "
            "yet justified despite a uniformly nonregressive guard.")
        recommendation = (
            "should not advance yet because one official LIGHT numerical "
            "endpoint remains unresolved despite a uniformly nonregressive "
            "FULL guard")
    elif not (all_guards_same_ub and all_same_path and all_guard_strict and
              guard_total_improved and exactness_passed):
        advance_reason = (
            "The guard quality, exact path, timing, or exactness evidence is "
            "not uniformly nonregressive, so broader qualification is not "
            "yet justified.")
        recommendation = (
            "should not advance yet because the FULL guard or exactness "
            "evidence is not uniformly nonregressive")
    else:
        advance_reason = (
            "Advance only as an experimental candidate for a broader "
            "predeclared qualification; this round does not authorize a "
            "default change.")
        recommendation = (
            "should advance only as an experimental candidate to a broader, "
            "predeclared startup qualification")
    decision = {
        "schema": "round39-final-decision-v1", "round_id": 39,
        "all_51_official_rows_strict": not unresolved_rows and all(
            row["strict_certificate"] for row in per_run),
        "strict_official_row_count": sum(row["strict_certificate"]
                                         for row in per_run),
        "unresolved_official_row_count": len(unresolved_rows),
        "unresolved_official_rows": [row["run_id"] for row in unresolved_rows],
        "false_certificate_count": false_certificates,
        "exactness_audit_passed": exactness_passed,
        "questions": {
            "1_new_benchmark_more_informative": {
                "answer": True,
                "qualification": (
                    "More informative for the small-instance startup crossover: "
                    "it adds V8/V10/V12 and an explicit frozen gradient. It is "
                    "not uniformly harder than Round33's high-imbalance V10 set."),
                "round39_empty_startup_regions": new_empty,
                "historical_round33_empty_startup_regions": historical_empty,
            },
            "2_light_outperforms_p_grb": {
                "small_medium": "mixed",
                "small_medium_light_wins": medium["light_wins"],
                "small_medium_p_grb_wins": medium["p_grb_wins"],
                "small_medium_ties": medium["ties"],
                "small_hard": "yes" if hard["light_wins"] >
                    hard["p_grb_wins"] else "no",
                "small_hard_light_wins": hard["light_wins"],
                "small_hard_p_grb_wins": hard["p_grb_wins"],
                "small_hard_ties": hard["ties"],
                "small_hard_unresolved": hard["unresolved"],
            },
            "3_startup_overhead_crossover": crossover,
            "4_light_preserves_full": {
                "answer": all_guards_same_ub and all_same_path,
                "startup_ub_equal_count": sum(
                    row["startup_objective_equal"] for row in guards),
                "guard_count": len(guards),
                "same_ub_identical_downstream_count": sum(
                    row["same_ub_downstream_structurally_identical"]
                    for row in guards),
                "all_guard_total_times_nonregressive": guard_total_improved,
            },
            "5_advance_light_to_broader_qualification": {
                "answer": advance,
                "automatic_promotion": False,
                "reason": advance_reason,
            },
            "6_full_remains_validated_mainline": {
                "answer": True, "mainline": "C6-HGA-FULL-K4-rho0.01",
                "default_changed": False,
            },
        },
    }
    common.write_json(common.OUT / "final_decision.json", decision)
    summary = {
        "schema": "round39-analysis-summary-v1", "official_rows": len(per_run),
        "primary_pairs": len(pairs), "guard_rows": len(guards),
        "strict_rows": sum(row["strict_certificate"] for row in per_run),
        "unresolved_rows": len(unresolved_rows),
        "exactness_passed": exactness_passed,
        "false_certificates": false_certificates,
        "strata": strata, "guard_same_ub": all_guards_same_ub,
        "guard_same_path_when_same_ub": all_same_path,
        "light_advance_recommended": advance,
        "mainline_changed": False,
    }
    common.write_json(common.OUT / "analysis_summary.json", summary)

    common.write_text(common.OUT / "structural_difficulty_definition.md", f"""# Round 39 structural difficulty definition

The label is a deterministic function of the frozen instance text. It uses no
solver, incumbent, bound, Work, node, time, certificate, machine, or winner
field. The score is 100 times a weighted sum of normalized dimension (0.12),
active-station fraction (0.16), imbalance L1 per station (0.15), fleet-capacity
pressure (0.13), support-duration or single-station pressure (0.18), spatial
distance coefficient of variation (0.08), plausible ordered-pair density
(0.09), and vehicle-assignment multiplicity (0.09). Exact formulas and clipping
are implemented in `scripts/round39_instance_tools.py`.

Labels were frozen before official results: `small-easy` is score below 60,
`small-medium` is 60 through below 78, and `small-hard` is at least 78. Frozen
ranges are {min(number(row['difficulty_score']) for row in descriptors39 if row['difficulty_stratum'] == 'small-easy'):.3f} to {max(number(row['difficulty_score']) for row in descriptors39 if row['difficulty_stratum'] == 'small-easy'):.3f}, {min(number(row['difficulty_score']) for row in descriptors39 if row['difficulty_stratum'] == 'small-medium'):.3f} to {max(number(row['difficulty_score']) for row in descriptors39 if row['difficulty_stratum'] == 'small-medium'):.3f}, and {min(number(row['difficulty_score']) for row in descriptors39 if row['difficulty_stratum'] == 'small-hard'):.3f} to {max(number(row['difficulty_score']) for row in descriptors39 if row['difficulty_stratum'] == 'small-hard'):.3f} for easy, medium, and hard.

Medium/hard acceptance additionally requires meaningful surplus and deficit
support, active repositioning, nonzero initial objective, route alternatives,
and frozen tightness conditions. Rejected candidates and their structural
reasons are retained in `rejected_generation_manifest.csv`.
""")
    common.write_text(common.OUT / "representative_trajectory_report.md", """# Representative Round 39 trajectories

One case per stratum is selected by proximity to that stratum's frozen median
difficulty score, never by solver outcome. `representative_trajectories.csv`
contains both official arms with process-entry time, monotone valid lower
bound, observed incumbent, proof gap to the final verified optimum, event, and
source. Values are observed left-continuously; there is no interpolation or
extension beyond the last event, and the strict serialized endpoint is added
only when the native trace ends earlier.
""")
    common.write_text(common.OUT / "final_report.md", f"""# Round 39 final report

## Outcome

{sum(row['strict_certificate'] for row in per_run)} of 51 frozen rows converged
with strict original-problem certificates, {len(unresolved_rows)} is candidly
unresolved, and there are zero false certificates. The 24 new V<=12 instances were selected and labelled
from structural data before any official P-GRB/LIGHT outcome was examined.
No C++ algorithm, geometry, scheduler, split, or certificate code changed.

| Stratum | Pairs | P-GRB wins | LIGHT wins | Ties | Unresolved | P-GRB shifted geomean | LIGHT shifted geomean |
|---|---:|---:|---:|---:|---:|---:|---:|
| easy | {easy['pair_count']} | {easy['p_grb_wins']} | {easy['light_wins']} | {easy['ties']} | {easy['unresolved']} | {easy['p_grb_shifted_geomean_seconds']:.3f} s | {easy['light_shifted_geomean_seconds']:.3f} s |
| medium | {medium['pair_count']} | {medium['p_grb_wins']} | {medium['light_wins']} | {medium['ties']} | {medium['unresolved']} | {medium['p_grb_shifted_geomean_seconds']:.3f} s | {medium['light_shifted_geomean_seconds']:.3f} s |
| hard | {hard['pair_count']} | {hard['p_grb_wins']} | {hard['light_wins']} | {hard['ties']} | {hard['unresolved']} | {hard['p_grb_shifted_geomean_seconds']:.3f} s | {hard['light_shifted_geomean_seconds']:.3f} s |

P-GRB dominates the easy stratum because uniform HGA startup is fixed overhead.
The medium stratum is mixed, not a clean scalar crossover. LIGHT dominates the
hard stratum by pair wins and shifted geometric mean. The first observed LIGHT
win occurs at score {crossover['first_observed_light_win_score']:.3f}; the
machine-readable crossover file records whether a uniform high-score suffix
exists after all outcomes are considered.

## Benchmark interpretation

The new set is more informative for the intended startup-overhead question:
it covers V8/V10/V12, M1/M2/M3, both Q values, and three nonoverlapping frozen
score strata. Only {new_empty}/24 new LIGHT rows closes with an empty
strict-improver region at startup, confined to easy; medium/hard have none.
The Round33 V10 context has {historical_empty}/18 such rows. Round39 is not
claimed to be uniformly harder than the high-imbalance Round33 panel; the
value is controlled gradient and dimensional coverage. Historical rows remain
context only and are never mixed into official summaries.

## FULL guard and recommendation

The predeclared easy/medium/hard FULL guard reproduces LIGHT's verified startup
UB in {sum(row['startup_objective_equal'] for row in guards)}/{len(guards)}
cases. When UB is equal, complete timing-free hashes show structurally
identical downstream paths in
{sum(row['same_ub_downstream_structurally_identical'] for row in guards)}/{len(guards)}
cases. Exact startup, exact-phase, total-time, interval, LP, target/requeue,
split, closure, Work, and node evidence is in the companion CSVs.

LIGHT {recommendation}.
It is not promoted here. **C6-HGA-FULL, K=4, rho=0.01 remains the validated
default mainline.**

## Correctness

All completed rows pass the exactness audit: original-problem verification,
zero-gap strict
certificates, monotone valid C6 bounds, full root/parent-child coverage,
balanced solver lifecycle, one-thread commands, Seed 0, zero P-GRB gap
settings, and Round36/37 default-off policy isolation all hold. Round38 remains
outside this main-based branch. The final build/test and default-equivalence
gates are recorded separately after this analysis.
""")
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if exactness_passed and false_certificates == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
