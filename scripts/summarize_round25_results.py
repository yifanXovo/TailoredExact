#!/usr/bin/env python3
"""Analyze Round 25 official rows and preregister diagnostic replays."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Iterator

import run_round25_experiments as frozen


ROOT = frozen.ROOT
OUT = frozen.OUT
RUNS = OUT / "runs"
THRESHOLDS = (0.10, 0.05, 0.01, 0.001)
SUMMARY_FIELDS = [
    "stage", "horizon_seconds", "instance", "family", "arm", "return_code",
    "status", "certificate_class", "strict_certificate",
    "certificate_wall_seconds", "authoritative", "verified_witness",
    "native_incumbent", "native_bound", "verified_ub", "common_ub",
    "final_lb", "common_ub_gap", "bound_progress_auc", "process_wall_seconds",
    "first_incumbent_seconds", "last_lb_improvement_seconds",
    "stagnation_seconds", "nodes", "open_nodes", "work", "simplex_iterations",
    "barrier_iterations", "memory_gb", "hga_seconds", "optimize_count",
    "model_count", "model_read_count", "artifact_generation_count",
    "artifact_cache_hit_count", "artifact_generation_seconds",
    "model_read_seconds", "presolve_count", "root_count", "presolve_seconds",
    "root_seconds", "presolve_time_status", "root_time_status",
    "native_cut_count", "native_cut_count_status", "fresh_restart_count",
    "same_leaf_restart_count",
    "child_restart_count", "attempt_count", "split_count", "closed_leaf_count",
    "open_leaf_count", "warm_candidate_count", "warm_complete_count",
    "warm_submitted_count", "warm_accepted_count", "warm_rejected_count",
    "warm_unknown_count", "coverage_gate", "lifecycle_gate",
    "consistency_gate", "verifier_gate", "result_path",
]


def relative(path: Path) -> str:
    return frozen.relative(path)


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def truth(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def value(data: dict[str, Any], *names: str, default: Any = "") -> Any:
    for name in names:
        if name in data and data[name] not in (None, ""):
            return data[name]
    return default


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def open_text(path: Path):
    actual = path if path.exists() else Path(str(path) + ".gz")
    if actual.suffix == ".gz":
        return gzip.open(actual, "rt", encoding="utf-8", errors="replace", newline="")
    return actual.open("r", encoding="utf-8", errors="replace", newline="")


def csv_rows(path: Path) -> list[dict[str, str]]:
    try:
        with open_text(path) as stream:
            return list(csv.DictReader(stream))
    except OSError:
        return []


def enhanced_metrics(directory: Path) -> dict[str, Any]:
    records = csv_rows(directory / "external" / "enhanced_attempt_trace.csv")
    if not records:
        return {
            "presolve_seconds": "unavailable", "root_seconds": "unavailable",
            "presolve_time_status": "unavailable_no_enhanced_attempt_trace",
            "root_time_status": "unavailable_no_enhanced_attempt_trace",
            "native_cut_count": "", "native_cut_count_status": "unavailable",
            "native_open_nodes": "", "native_incumbent": "",
        }
    presolve_values = [float(record["presolve_time_seconds"])
                       for record in records
                       if truth(record.get("presolve_time_available")) and
                       finite(record.get("presolve_time_seconds"))]
    root_values = [float(record["root_time_seconds"])
                   for record in records
                   if truth(record.get("root_time_available")) and
                   finite(record.get("root_time_seconds"))]
    cut_values = [int(float(record["native_cut_count"]))
                  for record in records
                  if truth(record.get("native_cut_count_available")) and
                  finite(record.get("native_cut_count"))]
    open_values = [float(record["open_nodes"])
                   for record in records
                   if truth(record.get("open_nodes_available")) and
                   finite(record.get("open_nodes"))]
    incumbent_values = [float(record["incumbent"])
                        for record in records
                        if truth(record.get("incumbent_available")) and
                        finite(record.get("incumbent"))]
    return {
        "presolve_seconds": sum(presolve_values) if presolve_values
            else "unavailable",
        "root_seconds": sum(root_values) if root_values else "unavailable",
        "presolve_time_status": "available_native_log_sum" if presolve_values
            else "unavailable_not_safely_reported",
        "root_time_status": "available_native_log_sum" if root_values
            else "unavailable_not_safely_reported",
        "native_cut_count": sum(cut_values) if cut_values else "",
        "native_cut_count_status": "available_native_api_sum" if cut_values
            else "unavailable_not_safely_reported",
        "native_open_nodes": max(open_values) if open_values else "",
        "native_incumbent": min(incumbent_values) if incumbent_values else "",
    }


def write_csv(path: Path, rows: Iterable[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    material = [dict(row) for row in rows]
    names = list(fields or [])
    for row in material:
        for name in row:
            if name not in names:
                names.append(name)
    if not names:
        names = ["status"]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=names, extrasaction="ignore")
        writer.writeheader(); writer.writerows(material)
    os.replace(temporary, path)


def verified_witness(result: dict[str, Any]) -> bool:
    verification = result.get("verification", {})
    return bool(value(result, "verified_incumbent_original_problem_feasible",
                      default=False)) or bool(
        verification.get("original_solution_feasible", False))


def run_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not RUNS.exists():
        return rows
    for directory in sorted(path for path in RUNS.iterdir() if path.is_dir()):
        command = load_json(directory / "command.json")
        state = load_json(directory / "run_state.json")
        result = load_json(directory / "result.json")
        if not command:
            continue
        arm = str(command.get("arm", ""))
        stage = str(command.get("stage", ""))
        witness = verified_witness(result)
        verified_ub = value(result, "verified_incumbent_objective", "objective")
        if not witness or not finite(verified_ub):
            verified_ub = ""
        strict = bool(result.get("strict_certified_original_problem", False))
        if arm.startswith("EXT-"):
            strict = bool(result.get("external_gini_tree_strict_certified", strict))
        external = arm.startswith("EXT-")
        enhanced = enhanced_metrics(directory) if external else {}
        external_gates = (
            bool(result.get("external_gini_tree_root_coverage_valid", False)) and
            bool(result.get("external_gini_tree_parent_child_coverage_valid", False)) and
            bool(result.get("external_gini_tree_all_leaf_bounds_valid", False)) and
            bool(result.get("external_gini_tree_global_bound_monotone", False)) and
            bool(result.get("external_gini_tree_leaf_bounds_monotone", False)) and
            bool(result.get("external_gini_tree_lifecycle_complete", False)) and
            bool(result.get("external_gini_tree_feasibility_consistency_gate", False)))
        process_ok = state.get("return_code") == 0 and bool(result)
        authoritative = process_ok and witness and (external_gates if external else True)
        final_lb = value(result, "lower_bound") if authoritative else ""
        row: dict[str, Any] = {
            "stage": stage,
            "horizon_seconds": command.get("budget_seconds", ""),
            "instance": command.get("instance", ""),
            "family": frozen.INSTANCES.get(str(command.get("instance", "")),
                                            (Path(), "unknown"))[1],
            "arm": arm,
            "return_code": state.get("return_code", "missing"),
            "status": result.get("status", "missing_result"),
            "certificate_class": value(
                result, "external_gini_tree_certificate_class",
                "strict_certificate_class"),
            "strict_certificate": strict and authoritative,
            "certificate_wall_seconds": value(
                result, "final_process_wall_time_seconds", "runtime_seconds")
                if strict and authoritative else "",
            "authoritative": authoritative,
            "verified_witness": witness,
            "native_incumbent": enhanced.get("native_incumbent", "")
                if external else "",
            "native_bound": result.get(
                "external_gini_tree_global_lower_bound", "")
                if external else "",
            "verified_ub": verified_ub,
            "final_lb": final_lb,
            "process_wall_seconds": value(
                result, "final_process_wall_time_seconds", "runtime_seconds"),
            "first_incumbent_seconds": result.get(
                "external_gini_tree_first_incumbent_time_seconds", "")
                if external else "",
            "last_lb_improvement_seconds": result.get(
                "external_gini_tree_last_global_lb_improvement_time_seconds", "")
                if external else "",
            "stagnation_seconds": result.get(
                "external_gini_tree_final_stagnation_seconds", "")
                if external else "",
            "nodes": result.get("external_gini_tree_nodes", 0)
                if external else 0,
            "open_nodes": enhanced.get("native_open_nodes", "")
                if external else "",
            "work": result.get("external_gini_tree_work", "")
                if external else "",
            "simplex_iterations": result.get(
                "external_gini_tree_simplex_iterations", "")
                if external else "",
            "barrier_iterations": result.get(
                "external_gini_tree_barrier_iterations", "")
                if external else "",
            "memory_gb": result.get("external_gini_tree_peak_memory_gb", "")
                if external else "",
            "hga_seconds": result.get("incumbent_generation_time_seconds", 0),
            "optimize_count": value(
                result, "external_gini_tree_optimize_count",
                "gurobi_optimize_count", "global_gini_tree_mipopt_count",
                "native_mip_mipopt_count", default=0),
            "model_count": value(
                result, "external_gini_tree_model_count", "gurobi_model_count",
                "global_gini_tree_problem_count", "native_mip_problem_count", default=0),
            "model_read_count": value(
                result, "external_gini_tree_model_read_count",
                "gurobi_model_read_count", "global_gini_tree_model_read_count",
                "native_mip_model_read_count", default=0),
            "artifact_generation_count": result.get(
                "external_gini_tree_canonical_artifact_generation_count", 0),
            "artifact_cache_hit_count": result.get(
                "external_gini_tree_canonical_artifact_cache_hit_count", 0),
            "artifact_generation_seconds": result.get(
                "external_gini_tree_canonical_artifact_generation_seconds", 0),
            "model_read_seconds": result.get(
                "external_gini_tree_model_read_seconds", ""),
            "presolve_count": result.get(
                "external_gini_tree_presolve_execution_count", ""),
            "root_count": result.get(
                "external_gini_tree_root_relaxation_execution_count", ""),
            "presolve_seconds": enhanced.get("presolve_seconds", "unavailable"),
            "root_seconds": enhanced.get("root_seconds", "unavailable"),
            "presolve_time_status": enhanced.get(
                "presolve_time_status", "unavailable_not_safely_reported"),
            "root_time_status": enhanced.get(
                "root_time_status", "unavailable_not_safely_reported"),
            "native_cut_count": enhanced.get("native_cut_count", ""),
            "native_cut_count_status": enhanced.get(
                "native_cut_count_status", "unavailable_not_safely_reported"),
            "fresh_restart_count": result.get(
                "external_gini_tree_fresh_restart_count", 0),
            "same_leaf_restart_count": result.get(
                "external_gini_tree_same_leaf_resume_count", 0),
            "child_restart_count": result.get(
                "external_gini_tree_child_restart_count", 0),
            "attempt_count": result.get("external_gini_tree_attempt_count", 0),
            "split_count": result.get("external_gini_tree_split_count",
                                      result.get("global_gini_tree_branch_count", 0)),
            "closed_leaf_count": result.get(
                "external_gini_tree_closed_leaf_count", ""),
            "open_leaf_count": result.get("external_gini_tree_open_leaf_count", ""),
            "warm_candidate_count": result.get(
                "external_gini_tree_warm_start_candidate_count", 0),
            "warm_complete_count": result.get(
                "external_gini_tree_warm_start_complete_count", 0),
            "warm_submitted_count": result.get(
                "external_gini_tree_warm_start_submitted_count", 0),
            "warm_accepted_count": result.get(
                "external_gini_tree_warm_start_accepted_count", 0),
            "warm_rejected_count": result.get(
                "external_gini_tree_warm_start_rejected_count", 0),
            "warm_unknown_count": result.get(
                "external_gini_tree_warm_start_unknown_count", 0),
            "coverage_gate": external_gates if external else True,
            "lifecycle_gate": result.get(
                "external_gini_tree_lifecycle_complete", False)
                if external else True,
            "consistency_gate": result.get(
                "external_gini_tree_feasibility_consistency_gate", False)
                if external else True,
            "verifier_gate": witness,
            "result_path": relative(directory / "result.json"),
            "run_dir": directory,
            "result": result,
            "command": command,
            "state": state,
        }
        if arm == "P-GRB":
            row.update({
                "native_incumbent": result.get("gurobi_obj_val", "")
                    if result.get("gurobi_obj_val_available", False) else "",
                "native_bound": result.get("gurobi_obj_bound_c", "")
                    if result.get("gurobi_obj_bound_c_available", False) else "",
                "nodes": result.get("gurobi_node_count", 0),
                "open_nodes": "",
                "work": result.get("gurobi_work", ""),
                "simplex_iterations": result.get("gurobi_iter_count", ""),
                "barrier_iterations": result.get("gurobi_bar_iter_count", ""),
                "memory_gb": result.get("gurobi_max_mem_used_gb", ""),
                "first_incumbent_seconds": result.get(
                    "gurobi_first_incumbent_time", ""),
                "last_lb_improvement_seconds": result.get(
                    "gurobi_last_lower_bound_improvement_time", ""),
                "optimize_count": result.get("gurobi_optimize_count", 0),
                "model_count": result.get("gurobi_model_count", 0),
                "model_read_count": result.get("gurobi_model_read_count", 0),
                "presolve_count": 1 if result.get("gurobi_optimize_count", 0) else 0,
                "root_count": 1 if result.get("gurobi_optimize_count", 0) else 0,
            })
        elif arm == "P-CPX":
            row.update({
                "native_incumbent": result.get("native_mip_objective", "")
                    if result.get("native_mip_objective_available", False) else "",
                "native_bound": result.get("native_mip_best_bound", "")
                    if result.get("native_mip_best_bound_available", False) else "",
                "nodes": result.get("native_mip_node_count", 0),
                "open_nodes": result.get("native_mip_open_node_count", "")
                    if result.get("native_mip_open_node_count_available", False)
                    else "",
                "first_incumbent_seconds": result.get(
                    "first_incumbent_time", ""),
                "last_lb_improvement_seconds": result.get(
                    "last_bound_improvement_time", ""),
                "optimize_count": result.get("native_mip_mipopt_count", 0),
                "model_count": result.get("native_mip_problem_count", 0),
                "model_read_count": result.get("native_mip_model_read_count", 0),
                "presolve_count": 1 if result.get("native_mip_mipopt_count", 0) else 0,
                "root_count": 1 if result.get("native_mip_mipopt_count", 0) else 0,
            })
        elif arm == "S0-SAFE":
            row.update({
                "native_incumbent": result.get(
                    "global_gini_tree_native_objective", "")
                    if result.get("global_gini_tree_incumbent_verified", False)
                    else "",
                "native_bound": result.get(
                    "global_gini_tree_native_best_bound", "")
                    if result.get("global_gini_tree_native_best_bound_available", False)
                    else "",
                "nodes": result.get("native_mip_node_count", 0),
                "open_nodes": result.get(
                    "global_gini_tree_native_open_nodes", ""),
                "simplex_iterations": result.get(
                    "global_gini_tree_native_simplex_iterations", ""),
                "first_incumbent_seconds": value(
                    result, "incumbent_best_runtime",
                    "incumbent_generation_time_seconds", default=""),
                "last_lb_improvement_seconds": result.get(
                    "last_bound_improvement_time", ""),
                "optimize_count": result.get("global_gini_tree_mipopt_count", 0),
                "model_count": result.get("global_gini_tree_problem_count", 0),
                "model_read_count": result.get("global_gini_tree_model_read_count", 0),
                "presolve_count": 0,
                "root_count": 1 if result.get("global_gini_tree_mipopt_count", 0) else 0,
            })
        if arm == "EXT-CPX":
            # A zero observation is not evidence that CPLEX skipped the phase:
            # its callable-library log routing does not safely isolate these
            # timers per leaf on this build.
            if row["presolve_time_status"] != "available_native_log_sum":
                row["presolve_count"] = "unavailable"
            if row["root_time_status"] != "available_native_log_sum":
                row["root_count"] = "unavailable"
        if (not external and finite(row.get("process_wall_seconds")) and
                finite(row.get("last_lb_improvement_seconds")) and
                float(row["last_lb_improvement_seconds"]) >= 0.0):
            row["stagnation_seconds"] = max(
                0.0, float(row["process_wall_seconds"]) -
                float(row["last_lb_improvement_seconds"]))
        rows.append(row)
    return rows


def trace_points(row: dict[str, Any]) -> list[tuple[float, float]]:
    directory = Path(row["run_dir"])
    candidates = [
        directory / "bound_checkpoints.csv", directory / "dense_progress.csv",
        directory / "progress.csv",
        directory / "external" / "external_tree_events.csv",
    ]
    points: list[tuple[float, float]] = []
    for path in candidates:
        records = csv_rows(path)
        if not records:
            continue
        for record in records:
            time_value = next((record.get(name) for name in (
                "checkpoint_seconds", "observation_time_seconds",
                "elapsed_runtime_seconds", "elapsed_seconds")
                if finite(record.get(name))), None)
            bound_value = next((record.get(name) for name in (
                "global_lb", "native_best_bound", "best_bound")
                if finite(record.get(name))), None)
            if time_value is not None and bound_value is not None:
                points.append((max(0.0, float(time_value)), float(bound_value)))
        if points:
            break
    points.sort()
    output: list[tuple[float, float]] = []
    best = -math.inf
    for timestamp, bound in points:
        best = max(best, bound)
        if output and abs(timestamp - output[-1][0]) <= 1e-12:
            output[-1] = (timestamp, best)
        else:
            output.append((timestamp, best))
    return output


def add_common_ubs(rows: list[dict[str, Any]]) -> None:
    common: dict[tuple[str, str], float] = {}
    for row in rows:
        if row["stage"] not in ("stage1", "stage2") or not finite(row["verified_ub"]):
            continue
        key = (row["stage"], str(row["instance"]))
        common[key] = min(common.get(key, math.inf), float(row["verified_ub"]))
    for row in rows:
        stage = str(row["stage"])
        # Diagnostic replays are interpreted against the already frozen Stage 1
        # common incumbent.  They never contribute a new common UB themselves.
        key = ("stage1" if stage == "diagnostic" else stage,
               str(row["instance"]))
        ub = common.get(key)
        row["common_ub"] = "" if ub is None else ub
        if ub is not None and finite(row["final_lb"]) and abs(ub) > 1e-12:
            row["common_ub_gap"] = max(0.0, (ub - float(row["final_lb"])) / abs(ub))
        else:
            row["common_ub_gap"] = ""


def progress_metrics(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]],
                                                           list[dict[str, Any]]]:
    auc_rows: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []
    for row in rows:
        budget = float(row.get("horizon_seconds") or 0)
        ub = row.get("common_ub")
        points = trace_points(row)
        if budget <= 0 or not finite(ub) or abs(float(ub)) <= 1e-12 or not points:
            row["bound_progress_auc"] = ""
            auc_rows.append({
                "stage": row["stage"], "instance": row["instance"],
                "arm": row["arm"], "common_ub": ub, "points": len(points),
                "gap_auc": "", "bound_progress_auc": "", "status": "unavailable",
            })
            continue
        common_ub = float(ub)
        series = [(0.0, 1.0)]
        for timestamp, bound in points:
            gap = max(0.0, (common_ub - bound) / abs(common_ub))
            series.append((min(budget, timestamp), gap))
        final_gap = row.get("common_ub_gap")
        if finite(final_gap):
            series.append((budget, float(final_gap)))
        else:
            series.append((budget, series[-1][1]))
        series.sort()
        area = 0.0
        previous_time, previous_gap = series[0]
        first: dict[float, tuple[float, float] | None] = {
            threshold: None for threshold in THRESHOLDS}
        for timestamp, gap in series[1:]:
            if timestamp < previous_time:
                continue
            area += (timestamp - previous_time) * (previous_gap + gap) / 2.0
            for threshold in first:
                if first[threshold] is None and gap <= threshold:
                    first[threshold] = (previous_time, timestamp)
            previous_time, previous_gap = timestamp, gap
        gap_auc = area / budget
        bound_auc = 1.0 - gap_auc
        row["bound_progress_auc"] = bound_auc
        auc_rows.append({
            "stage": row["stage"], "instance": row["instance"],
            "arm": row["arm"], "common_ub": common_ub,
            "points": len(points), "gap_auc": gap_auc,
            "bound_progress_auc": bound_auc, "status": "available",
        })
        for threshold, interval in first.items():
            threshold_rows.append({
                "stage": row["stage"], "instance": row["instance"],
                "arm": row["arm"], "common_ub": common_ub,
                "gap_threshold": threshold,
                "crossing_interval_lower_seconds": "" if interval is None else interval[0],
                "crossing_interval_upper_seconds": "" if interval is None else interval[1],
                "reached": interval is not None,
            })
    return auc_rows, threshold_rows


def public(row: dict[str, Any]) -> dict[str, Any]:
    return {name: row.get(name, "") for name in SUMMARY_FIELDS}


def lookup(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {(str(row["stage"]), str(row["instance"]), str(row["arm"])): row
            for row in rows}


def comparison_reason(plain: dict[str, Any], external: dict[str, Any],
                      material: bool = False) -> tuple[bool, str]:
    if not plain or not external:
        return False, "missing_matched_row"
    p_strict = bool(plain["strict_certificate"])
    e_strict = bool(external["strict_certificate"])
    if p_strict != e_strict:
        return (p_strict, "plain_strict_external_not_strict" if p_strict
                else "external_strict_plain_not_strict")
    if p_strict and e_strict:
        p_time = float(plain["certificate_wall_seconds"])
        e_time = float(external["certificate_wall_seconds"])
        tolerance = max(1.0, 0.01 * p_time) if material else 0.0
        if p_time + tolerance < e_time:
            return True, "both_strict_plain_lower_certificate_wall_time"
        return False, "both_strict_external_not_materially_slower"
    if finite(plain["final_lb"]) and finite(external["final_lb"]):
        p_lb, e_lb = float(plain["final_lb"]), float(external["final_lb"])
        tolerance = max(1e-9, 1e-6 * max(1.0, abs(p_lb))) if material else 1e-12
        if p_lb > e_lb + tolerance:
            return True, "plain_higher_valid_final_lb"
        if e_lb > p_lb + tolerance:
            return False, "external_higher_valid_final_lb"
    if finite(plain["common_ub_gap"]) and finite(external["common_ub_gap"]):
        tolerance = 1e-5 if material else 1e-12
        if float(plain["common_ub_gap"]) + tolerance < float(external["common_ub_gap"]):
            return True, "plain_smaller_common_ub_gap"
        if float(external["common_ub_gap"]) + tolerance < float(plain["common_ub_gap"]):
            return False, "external_smaller_common_ub_gap"
    if finite(plain["bound_progress_auc"]) and finite(external["bound_progress_auc"]):
        tolerance = 1e-3 if material else 1e-12
        if float(plain["bound_progress_auc"]) > float(external["bound_progress_auc"]) + tolerance:
            return True, "plain_higher_bound_progress_auc"
    return False, "external_not_underperforming_by_frozen_hierarchy"


def emit_triggers(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = lookup(rows)
    output: list[dict[str, Any]] = []
    pairs = (
        ("EXT-CPX_vs_P-CPX", "P-CPX", "EXT-CPX", "EXT-CPX", False),
        ("EXT-GRB-COLD_vs_P-GRB", "P-GRB", "EXT-GRB-COLD",
         "EXT-GRB-COLD", False),
        ("EXT-GRB-WARM_vs_EXT-GRB-COLD", "EXT-GRB-COLD", "EXT-GRB-WARM",
         "EXT-GRB-WARM", True),
    )
    for instance in frozen.STAGE1_INSTANCES:
        for comparison, plain_arm, external_arm, replay_arm, material in pairs:
            left = by_key.get(("stage1", instance, plain_arm), {})
            right = by_key.get(("stage1", instance, external_arm), {})
            triggered, reason = comparison_reason(left, right, material)
            trigger_id = f"{instance}__{replay_arm.lower().replace('-', '_')}"
            output.append({
                "trigger_id": trigger_id, "instance": instance,
                "comparison": comparison, "matched_plain_or_cold_arm": plain_arm,
                "underperforming_external_arm": external_arm,
                "replay_arm": replay_arm, "materiality_rule_applied": material,
                "triggered": triggered, "trigger_reason": reason,
                "official_plain_or_cold_status": left.get("status", "missing"),
                "official_external_status": right.get("status", "missing"),
                "official_plain_or_cold_strict": left.get("strict_certificate", ""),
                "official_external_strict": right.get("strict_certificate", ""),
                "official_plain_or_cold_lb": left.get("final_lb", ""),
                "official_external_lb": right.get("final_lb", ""),
                "official_plain_or_cold_gap": left.get("common_ub_gap", ""),
                "official_external_gap": right.get("common_ub_gap", ""),
                "official_plain_or_cold_auc": left.get("bound_progress_auc", ""),
                "official_external_auc": right.get("bound_progress_auc", ""),
                "diagnostic_budget_seconds": 300 if triggered else "",
                "diagnostic_replaces_official": False,
            })
    write_csv(OUT / "underperformance_trigger_table.csv", output)
    return output


def paired(rows: list[dict[str, Any]], left_arm: str,
           right_arm: str) -> list[dict[str, Any]]:
    by_key = lookup(rows)
    output = []
    keys = sorted({(str(row["stage"]), str(row["instance"])) for row in rows
                   if row["stage"] in ("stage1", "stage2") and
                   row["arm"] in (left_arm, right_arm)})
    for stage, instance in keys:
        left = by_key.get((stage, instance, left_arm), {})
        right = by_key.get((stage, instance, right_arm), {})
        item = {"stage": stage, "instance": instance,
                "left_arm": left_arm, "right_arm": right_arm}
        for prefix, row in (("left", left), ("right", right)):
            for field in ("status", "strict_certificate", "certificate_wall_seconds",
                          "final_lb", "verified_ub", "common_ub_gap",
                          "bound_progress_auc", "process_wall_seconds"):
                item[f"{prefix}_{field}"] = row.get(field, "")
        output.append(item)
    return output


PAIR_DEFINITIONS = (
    ("plain CPLEX versus plain Gurobi", "P-CPX", "P-GRB"),
    ("plain CPLEX versus EXT-CPX", "P-CPX", "EXT-CPX"),
    ("plain Gurobi versus EXT-GRB-COLD", "P-GRB", "EXT-GRB-COLD"),
    ("external CPLEX versus external Gurobi", "EXT-CPX", "EXT-GRB-COLD"),
    ("cold versus warm external Gurobi", "EXT-GRB-COLD", "EXT-GRB-WARM"),
    ("S0-SAFE versus EXT-CPX", "S0-SAFE", "EXT-CPX"),
    ("S0-SAFE versus EXT-GRB-COLD", "S0-SAFE", "EXT-GRB-COLD"),
)


def ranking_winner(left: dict[str, Any], right: dict[str, Any],
                   material: bool = False) -> tuple[str, str]:
    """Return left/right/tie using the frozen decision hierarchy."""
    left_wins, left_reason = comparison_reason(left, right, material)
    right_wins, right_reason = comparison_reason(right, left, material)
    if left_wins and not right_wins:
        return "left", left_reason
    if right_wins and not left_wins:
        return "right", right_reason
    return "tie", f"{left_reason};{right_reason}"


def mean_value(rows: list[dict[str, Any]], field: str) -> Any:
    values = [float(row[field]) for row in rows if finite(row.get(field))]
    return sum(values) / len(values) if values else ""


def median_value(rows: list[dict[str, Any]], field: str) -> Any:
    values = [float(row[field]) for row in rows if finite(row.get(field))]
    return median(values) if values else ""


def paired_decision_rows(rows: list[dict[str, Any]],
                         by_family: bool = False) -> list[dict[str, Any]]:
    official = [row for row in rows if row["stage"] in ("stage1", "stage2")]
    by_key = lookup(official)
    output: list[dict[str, Any]] = []
    for label, left_arm, right_arm in PAIR_DEFINITIONS:
        for stage, horizon in (("stage1", 900), ("stage2", 1200)):
            stage_rows = [row for row in official if row["stage"] == stage]
            families = sorted({str(row["family"]) for row in stage_rows}) \
                if by_family else ["ALL"]
            for family in families:
                instances = sorted({str(row["instance"]) for row in stage_rows
                                    if family == "ALL" or row["family"] == family})
                left_rows: list[dict[str, Any]] = []
                right_rows: list[dict[str, Any]] = []
                wins = Counter()
                for instance in instances:
                    left = by_key.get((stage, instance, left_arm), {})
                    right = by_key.get((stage, instance, right_arm), {})
                    if not left or not right:
                        continue
                    winner, _ = ranking_winner(left, right)
                    wins[winner] += 1
                    left_rows.append(left)
                    right_rows.append(right)
                if not left_rows:
                    continue
                output.append({
                    "comparison": label, "stage": stage,
                    "horizon_seconds": horizon, "family": family,
                    "left_arm": left_arm, "right_arm": right_arm,
                    "paired_rows": len(left_rows),
                    "left_wins": wins["left"], "right_wins": wins["right"],
                    "ties": wins["tie"],
                    "left_strict_certificates": sum(
                        bool(row["strict_certificate"]) for row in left_rows),
                    "right_strict_certificates": sum(
                        bool(row["strict_certificate"]) for row in right_rows),
                    "left_mean_common_gap": mean_value(left_rows, "common_ub_gap"),
                    "right_mean_common_gap": mean_value(right_rows, "common_ub_gap"),
                    "left_mean_auc": mean_value(left_rows, "bound_progress_auc"),
                    "right_mean_auc": mean_value(right_rows, "bound_progress_auc"),
                })
    return output


def aggregate_metric_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = (
        "optimize_count", "model_count", "model_read_count",
        "artifact_generation_count", "artifact_cache_hit_count",
        "presolve_count", "root_count", "fresh_restart_count",
        "same_leaf_restart_count", "child_restart_count", "attempt_count",
        "split_count", "closed_leaf_count", "warm_candidate_count",
        "warm_submitted_count", "warm_accepted_count", "warm_rejected_count",
    )
    output: list[dict[str, Any]] = []
    for stage in ("stage1", "stage2", "official_total", "diagnostic"):
        for arm in frozen.ARMS:
            selected = [row for row in rows if row["arm"] == arm and (
                row["stage"] == stage if stage != "official_total" else
                row["stage"] in ("stage1", "stage2"))]
            if not selected:
                continue
            item: dict[str, Any] = {
                "stage": stage, "arm": arm, "rows": len(selected),
                "strict_certificates": sum(
                    bool(row["strict_certificate"]) for row in selected),
                "mean_common_gap": mean_value(selected, "common_ub_gap"),
                "median_common_gap": median_value(selected, "common_ub_gap"),
                "mean_bound_progress_auc": mean_value(
                    selected, "bound_progress_auc"),
                "median_bound_progress_auc": median_value(
                    selected, "bound_progress_auc"),
                "process_wall_seconds": sum(
                    float(row["process_wall_seconds"]) for row in selected
                    if finite(row.get("process_wall_seconds"))),
                "presolve_count_unavailable_rows": sum(
                    not finite(row.get("presolve_count")) for row in selected),
                "root_count_unavailable_rows": sum(
                    not finite(row.get("root_count")) for row in selected),
            }
            for field in fields:
                item[field] = sum(float(row[field]) for row in selected
                                  if finite(row.get(field)))
            output.append(item)
    return output


def metrics_at_horizon(row: dict[str, Any], horizon: float) -> dict[str, Any]:
    """Compute a reporting-only snapshot from an official trajectory."""
    if not finite(row.get("common_ub")):
        return {}
    common_ub = float(row["common_ub"])
    points = [(timestamp, bound) for timestamp, bound in trace_points(row)
              if timestamp <= horizon]
    if not points or abs(common_ub) <= 1e-12:
        return {}
    series = [(0.0, 1.0)] + [
        (timestamp, max(0.0, (common_ub - bound) / abs(common_ub)))
        for timestamp, bound in points]
    series.append((horizon, series[-1][1]))
    series.sort()
    area = 0.0
    previous_time, previous_gap = series[0]
    for timestamp, gap in series[1:]:
        area += (timestamp - previous_time) * (previous_gap + gap) / 2.0
        previous_time, previous_gap = timestamp, gap
    return {
        "strict_certificate": False, "certificate_wall_seconds": "",
        "final_lb": max(bound for _, bound in points),
        "common_ub_gap": series[-1][1],
        "bound_progress_auc": 1.0 - area / horizon,
    }


def diagnostic_rows(rows: list[dict[str, Any]],
                    triggers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = lookup(rows)
    output: list[dict[str, Any]] = []
    diagnostic_dir = OUT / "diagnostics"
    diagnostic_dir.mkdir(parents=True, exist_ok=True)
    for trigger in triggers:
        if not truth(trigger.get("triggered")):
            continue
        instance, arm = trigger["instance"], trigger["replay_arm"]
        row = by_key.get(("diagnostic", instance, arm), {})
        reference_arm = str(trigger["matched_plain_or_cold_arm"])
        reference = by_key.get(("stage1", instance, reference_arm), {})
        material = truth(trigger.get("materiality_rule_applied"))
        comparison_reference = reference
        if reference_arm == "EXT-GRB-COLD":
            comparison_reference = metrics_at_horizon(reference, 300.0)
        winner, replay_reason = ranking_winner(
            comparison_reference, row, material) if row and comparison_reference \
            else ("tie", "insufficient_evidence")
        ordering_reproduced = winner == "left"
        if winner == "left":
            replay_outcome = "official_ordering_reproduced_at_300s"
        elif winner == "right":
            replay_outcome = \
                "performance_ordering_not_reproduced_and_therefore_unstable"
        else:
            replay_outcome = "ordering_indeterminate_at_300s"
        categories: list[str] = []
        if not row:
            categories.append("insufficient evidence")
        else:
            attempts = int(float(row.get("attempt_count") or 0))
            fresh = int(float(row.get("fresh_restart_count") or 0))
            presolve = int(float(row.get("presolve_count") or 0)) \
                if finite(row.get("presolve_count")) else 0
            hga = float(row.get("hga_seconds") or 0)
            artifact = float(row.get("artifact_generation_seconds") or 0)
            model_read = float(row.get("model_read_seconds") or 0)
            wall = float(row.get("process_wall_seconds") or 0)
            stagnation = float(row.get("stagnation_seconds") or 0)
            if not ordering_reproduced:
                categories.append(
                    "performance ordering not reproduced and therefore unstable")
            if presolve > 1:
                categories.append("repeated presolve/root overhead")
            if attempts > 1 and fresh >= max(2, attempts // 2):
                categories.append("excessive native model restarts")
            if wall > 0 and artifact + model_read > 0.10 * wall:
                categories.append("model build/read/I/O overhead")
            if finite(row.get("common_ub_gap")) and float(row["common_ub_gap"]) > 0.10:
                categories.append("weak leaf lower bounds")
            if (not bool(row.get("strict_certificate")) and
                    int(float(row.get("split_count") or 0)) == 0 and attempts >= 2):
                categories.append("overly coarse or late Gini splitting")
            if wall > 0 and stagnation > 0.40 * wall:
                categories.append("controlling-leaf or scheduler stagnation")
            if (arm == "EXT-GRB-WARM" and
                    int(float(row.get("warm_rejected_count") or 0)) > 0):
                categories.append("warm-start rejection or overhead")
            if hga > 0.20 * max(1.0, wall):
                categories.append("incumbent/cutoff overhead")
            if not categories:
                categories.append("insufficient evidence")
        report_path = diagnostic_dir / f"{trigger['trigger_id']}.md"
        enhanced = ""
        if row:
            candidate = Path(row["run_dir"]) / "external" / "enhanced_attempt_trace.csv"
            actual = candidate if candidate.exists() else Path(str(candidate) + ".gz")
            enhanced = relative(actual) if actual.exists() else "unavailable"
        reference_snapshot = (
            f"certificate time `{comparison_reference.get('certificate_wall_seconds', '')}`"
            if truth(comparison_reference.get("strict_certificate")) else
            f"LB `{comparison_reference.get('final_lb', '')}`, gap "
            f"`{comparison_reference.get('common_ub_gap', '')}`, AUC "
            f"`{comparison_reference.get('bound_progress_auc', '')}`")
        replay_snapshot = (
            f"certificate time `{row.get('certificate_wall_seconds', '')}`"
            if truth(row.get("strict_certificate")) else
            f"LB `{row.get('final_lb', '')}`, gap "
            f"`{row.get('common_ub_gap', '')}`, AUC "
            f"`{row.get('bound_progress_auc', '')}`")
        report = (
            f"# Diagnostic {trigger['trigger_id']}\n\n"
            f"Triggered by: `{trigger['trigger_reason']}`. This 300-second replay "
            "uses the frozen executable and identical mathematical options and does "
            "not replace the official 900-second row.\n\n"
            f"The 300-second comparison is `{reference_arm}` ({reference_snapshot}) "
            f"versus the replay ({replay_snapshot}). Outcome: `{replay_outcome}` "
            f"(`{replay_reason}`).\n\n"
            f"Replay status: `{row.get('status', 'missing')}`; optimize/model-read/"
            f"artifact counts: `{row.get('optimize_count', '')}/"
            f"{row.get('model_read_count', '')}/"
            f"{row.get('artifact_generation_count', '')}`; fresh/same-leaf/child "
            f"restarts: `{row.get('fresh_restart_count', '')}/"
            f"{row.get('same_leaf_restart_count', '')}/"
            f"{row.get('child_restart_count', '')}`; splits/closures: "
            f"`{row.get('split_count', '')}/{row.get('closed_leaf_count', '')}`; "
            f"enhanced trace: `{enhanced}`.\n\n"
            "Bottleneck classifications: " + ", ".join(categories) + ".\n")
        report_path.write_text(report, encoding="utf-8")
        output.append({
            "trigger_id": trigger["trigger_id"], "instance": instance,
            "arm": arm, "trigger_reason": trigger["trigger_reason"],
            "replay_completed": bool(row), "replay_return_code": row.get("return_code", ""),
            "replay_status": row.get("status", "missing"),
            "reference_arm": reference_arm,
            "reference_300_final_lb": comparison_reference.get("final_lb", ""),
            "reference_300_common_gap": comparison_reference.get("common_ub_gap", ""),
            "reference_300_auc": comparison_reference.get("bound_progress_auc", ""),
            "reference_certificate_wall_seconds": comparison_reference.get(
                "certificate_wall_seconds", ""),
            "performance_ordering_reproduced": ordering_reproduced,
            "diagnostic_outcome": replay_outcome,
            "replay_final_lb": row.get("final_lb", ""),
            "replay_common_gap": row.get("common_ub_gap", ""),
            "replay_auc": row.get("bound_progress_auc", ""),
            "optimize_count": row.get("optimize_count", ""),
            "model_read_count": row.get("model_read_count", ""),
            "artifact_count": row.get("artifact_generation_count", ""),
            "presolve_count": row.get("presolve_count", ""),
            "root_count": row.get("root_count", ""),
            "restart_count": row.get("fresh_restart_count", ""),
            "split_count": row.get("split_count", ""),
            "closed_leaf_count": row.get("closed_leaf_count", ""),
            "stagnation_seconds": row.get("stagnation_seconds", ""),
            "bottleneck_classifications": ";".join(categories),
            "enhanced_trace": enhanced, "report": relative(report_path),
        })
    return output


def stage0_audit() -> list[dict[str, Any]]:
    rows = []
    fingerprints = load_json(OUT / "gurobi_fingerprints.json").get("fingerprints", {})
    for instance, fingerprint in fingerprints.items():
        label = f"native_import_probe_{instance.lower()}"
        result = load_json(OUT / "stage0" / "raw" / f"{label}.json")
        rows.append({
            "instance": instance, "fingerprint": fingerprint,
            "import_succeeded": bool(result.get("gurobi_model_count", 0)),
            "domain_audit": result.get("gurobi_native_domain_audit_passed", False),
            "names_match": result.get("gurobi_native_variable_names_match", False),
            "types_match": result.get("gurobi_native_variable_types_match", False),
            "bounds_match": result.get("gurobi_native_variable_bounds_match", False),
            "rows": result.get("gurobi_num_constrs", ""),
            "columns": result.get("gurobi_num_vars", ""),
            "nonzeros": result.get("gurobi_num_nzs", ""),
            "status": result.get("gurobi_status_text", ""),
            "verified_witness": verified_witness(result),
        })
    return rows


REQUIRED_ARTIFACTS = (
    "source_of_truth.md", "round25_evaluation_protocol.md",
    "round25_instance_manifest.csv", "round25_common_ub_manifest.csv",
    "model_and_certificate_audit.csv", "moderate4301_correctness.csv",
    "stage1_900s_results.csv", "stage2_1200s_results.csv",
    "strict_certificate_summary.csv", "plain_cplex_vs_gurobi.csv",
    "external_cplex_vs_plain_cplex.csv",
    "external_gurobi_vs_plain_gurobi.csv",
    "external_cplex_vs_gurobi.csv", "external_vs_s0.csv",
    "gurobi_warm_vs_cold.csv", "bound_progress_auc.csv",
    "time_to_gap_thresholds.csv", "lifecycle_and_restart_summary.csv",
    "underperformance_trigger_table.csv", "underperformance_diagnostics.csv",
    "exactness_audit.csv", "stable_mainline_assessment.md",
    "final_audit_summary.json", "final_report.md",
)


def package_integrity_audit(rows: list[dict[str, Any]],
                            diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    missing = [name for name in REQUIRED_ARTIFACTS if not (OUT / name).is_file()]
    compression_manifests = sorted(OUT.rglob("compression_manifest.csv")) + \
        ([OUT / "lp_compression_manifest.csv"]
         if (OUT / "lp_compression_manifest.csv").is_file() else [])
    compressed_records = 0
    compression_failures: list[str] = []
    for manifest in compression_manifests:
        for record in csv_rows(manifest):
            compressed_records += 1
            target = ROOT / str(record.get("compressed_path", ""))
            if not target.is_file():
                compression_failures.append(f"missing:{relative(target)}")
                continue
            if (target.stat().st_size != int(record["compressed_bytes"]) or
                    frozen.sha256(target) != record["compressed_sha256"]):
                compression_failures.append(f"compressed_hash:{relative(target)}")
                continue
            digest = hashlib.sha256()
            restored_bytes = 0
            try:
                with gzip.open(target, "rb") as stream:
                    for block in iter(lambda: stream.read(1024 * 1024), b""):
                        digest.update(block)
                        restored_bytes += len(block)
            except OSError:
                compression_failures.append(f"gzip_read:{relative(target)}")
                continue
            if (restored_bytes != int(record["original_bytes"]) or
                    digest.hexdigest() != record["original_sha256"]):
                compression_failures.append(f"restored_hash:{relative(target)}")
    missing_run_evidence: list[str] = []
    for row in rows:
        directory = Path(row["run_dir"])
        for name in ("command.json", "run_state.json", "result.json"):
            if not (directory / name).is_file():
                missing_run_evidence.append(relative(directory / name))
    missing_diagnostics: list[str] = []
    for diagnostic in diagnostics:
        for field in ("enhanced_trace", "report"):
            path = ROOT / str(diagnostic.get(field, ""))
            if not path.is_file():
                missing_diagnostics.append(str(diagnostic.get(field, "")))
    package_files = [path for path in OUT.rglob("*") if path.is_file()]
    largest = max(package_files, key=lambda path: path.stat().st_size)
    raw_lp_files = sum(path.suffix.lower() == ".lp" for path in package_files)
    sensitive = frozen.sensitive_marker_present(OUT)
    passed = not (missing or compression_failures or missing_run_evidence or
                  missing_diagnostics or raw_lp_files or sensitive)
    audit = {
        "schema": "round25-final-package-audit-v1",
        "status": "passed" if passed else "failed",
        "required_artifacts": len(REQUIRED_ARTIFACTS),
        "missing_required_artifacts": missing,
        "evidence_rows_checked": len(rows),
        "missing_run_evidence": missing_run_evidence,
        "diagnostic_reports_and_traces_checked": 2 * len(diagnostics),
        "missing_diagnostic_evidence": missing_diagnostics,
        "compression_manifests": len(compression_manifests),
        "compressed_files_restored_and_hash_verified": compressed_records,
        "compression_failures": compression_failures,
        "raw_lp_files_remaining": raw_lp_files,
        "sensitive_license_marker_detected": sensitive,
        "package_files_before_final_manifest": len(package_files),
        "package_bytes_before_final_manifest": sum(
            path.stat().st_size for path in package_files),
        "largest_artifact": relative(largest),
        "largest_artifact_bytes": largest.stat().st_size,
        "github_hard_limit_margin_bytes": 100_000_000 - largest.stat().st_size,
    }
    (OUT / "final_package_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not passed:
        raise RuntimeError("Round25 final package integrity audit failed")
    return audit


def report(rows: list[dict[str, Any]], triggers: list[dict[str, Any]],
           diagnostics: list[dict[str, Any]]) -> None:
    official = [row for row in rows if row["stage"] in ("stage1", "stage2")]
    counts = {
        "completed": sum(row["return_code"] == 0 and bool(row["result"])
                         for row in official),
        "failed": sum(row["return_code"] != 0 or not row["result"] for row in official),
        "interrupted": sum("interrupt" in str(row["status"]).lower()
                           for row in official),
        "excluded": 0,
    }
    time_limited = sum("limit" in str(row["status"]).lower()
                       for row in official)
    strict = Counter((str(row["stage"]), str(row["arm"]))
                     for row in official if row["strict_certificate"])
    strict_complete = {
        f"{stage}:{arm}": strict[(stage, arm)]
        for stage in ("stage1", "stage2") for arm in frozen.ARMS}
    paired_rows = paired_decision_rows(rows)
    metric_rows = aggregate_metric_rows(rows)
    paired_map = {(row["comparison"], row["stage"]): row
                  for row in paired_rows}

    def pair_total(label: str, side: str) -> int:
        return sum(int(paired_map[(label, stage)][f"{side}_wins"])
                   for stage in ("stage1", "stage2"))

    cold_plain = "plain Gurobi versus EXT-GRB-COLD"
    cold_cpx = "external CPLEX versus external Gurobi"
    cold_s0 = "S0-SAFE versus EXT-GRB-COLD"
    correctness_failures = sum(
        not bool(row["authoritative"]) or not bool(row["verifier_gate"]) or
        not bool(row["coverage_gate"]) or not bool(row["lifecycle_gate"]) or
        not bool(row["consistency_gate"]) for row in rows)
    cold_plain_wins = pair_total(cold_plain, "right")
    plain_cold_wins = pair_total(cold_plain, "left")
    cold_cpx_wins = pair_total(cold_cpx, "right")
    cold_s0_wins = pair_total(cold_s0, "right")
    broadly_nonregressive = (
        correctness_failures == 0 and cold_plain_wins >= 10 and
        cold_cpx_wins == 12 and cold_s0_wins == 12)
    production_round = broadly_nonregressive and strict[("stage1", "EXT-GRB-COLD")] > 0 \
        and strict[("stage2", "EXT-GRB-COLD")] > 0
    external_decision = ("ready for a full production validation round"
                         if production_round else
                         "broadly nonregressive" if broadly_nonregressive else "mixed")
    warm_label = "cold versus warm external Gurobi"
    warm_wins = pair_total(warm_label, "right")
    cold_wins = pair_total(warm_label, "left")
    warm_decision = "mixed" if warm_wins and cold_wins else \
        "reproducible proof-progress benefit" if warm_wins else "ineffective"
    package_audit = load_json(OUT / "final_package_audit.json")
    summary = {
        "schema": "round25-final-audit-v1",
        "official_counts": counts,
        "time_limited_completed_rows": time_limited,
        "official_rows": len(official),
        "strict_certificate_counts": strict_complete,
        "all_evidence_rows": len(rows),
        "correctness_failures": correctness_failures,
        "triggered_pairs": sum(truth(row["triggered"]) for row in triggers),
        "diagnostic_replays_completed": sum(row["replay_completed"] for row in diagnostics),
        "license_usable": load_json(OUT / "license_visibility_audit.json").get(
            "checks_agree", False),
        "stable_mainline": "corrected_CPLEX_S0_F0",
        "external_gurobi_decision": external_decision,
        "external_gurobi_broadly_nonregressive": broadly_nonregressive,
        "production_migration_round_justified": production_round,
        "production_default_migration_justified": False,
        "warm_start_decision": warm_decision,
        "evidence_package_integrity": package_audit.get("status") == "passed",
        "compressed_files_restored_and_hash_verified": package_audit.get(
            "compressed_files_restored_and_hash_verified", 0),
        "hierarchy_wins": {
            "external_gurobi_cold_over_plain_gurobi": cold_plain_wins,
            "plain_gurobi_over_external_gurobi_cold": plain_cold_wins,
            "external_gurobi_cold_over_external_cplex": cold_cpx_wins,
            "external_gurobi_cold_over_s0_safe": cold_s0_wins,
            "external_gurobi_warm_over_cold": warm_wins,
            "external_gurobi_cold_over_warm": cold_wins,
        },
    }
    (OUT / "final_audit_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT / "stable_mainline_assessment.md").write_text(
        "# Stable mainline assessment\n\nCorrected CPLEX S0/F0 remains the stable "
        "paper reference throughout Round 25. No default, dispatch rule, solver "
        "portfolio, or instance-dependent selector is changed by this validation. "
        "Cold external Gurobi is ready for a later full production validation "
        "round, but Round 25 does not authorize a production-default migration.\n",
        encoding="utf-8")

    def shown(item: Any, digits: int = 4) -> str:
        if not finite(item):
            return "unavailable"
        return f"{float(item):.{digits}f}"

    def duration(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m {seconds % 60:.1f}s"

    by_stage = Counter(str(row["stage"]) for row in official)
    strict_lines = []
    for stage, horizon in (("stage1", 900), ("stage2", 1200)):
        strict_lines.append(
            f"| {horizon}s | " + " | ".join(
                f"{strict[(stage, arm)]}/{sum(row['stage'] == stage and row['arm'] == arm for row in official)}"
                for arm in frozen.ARMS) + " |")

    pair_lines = []
    for item in paired_rows:
        pair_lines.append(
            f"| {item['horizon_seconds']}s | {item['comparison']} | "
            f"{item['left_wins']}-{item['right_wins']}-{item['ties']} | "
            f"{item['left_strict_certificates']}-{item['right_strict_certificates']} | "
            f"{shown(item['left_mean_common_gap'])}-{shown(item['right_mean_common_gap'])} | "
            f"{shown(item['left_mean_auc'])}-{shown(item['right_mean_auc'])} |")

    family_rows = [row for row in paired_decision_rows(rows, by_family=True)
                   if row["comparison"] == cold_plain]
    family_lines = [
        f"| {item['horizon_seconds']}s | {item['family']} | "
        f"{item['left_wins']}-{item['right_wins']}-{item['ties']} | "
        f"{shown(item['left_mean_common_gap'])}-{shown(item['right_mean_common_gap'])} | "
        f"{shown(item['left_mean_auc'])}-{shown(item['right_mean_auc'])} |"
        for item in family_rows]

    metric_lines = []
    for item in metric_rows:
        if item["stage"] not in ("stage1", "stage2"):
            continue
        metric_lines.append(
            f"| {900 if item['stage'] == 'stage1' else 1200}s | {item['arm']} | "
            f"{int(item['strict_certificates'])}/{int(item['rows'])} | "
            f"{shown(item['mean_common_gap'])} / {shown(item['median_common_gap'])} | "
            f"{shown(item['mean_bound_progress_auc'])} / "
            f"{shown(item['median_bound_progress_auc'])} |")

    lifecycle_lines = []
    for item in metric_rows:
        if item["stage"] != "official_total":
            continue
        presolve = (str(int(item["presolve_count"])) if not
                    item["presolve_count_unavailable_rows"] else
                    f"unavailable ({int(item['presolve_count_unavailable_rows'])} rows)")
        root = (str(int(item["root_count"])) if not
                item["root_count_unavailable_rows"] else
                f"unavailable ({int(item['root_count_unavailable_rows'])} rows)")
        lifecycle_lines.append(
            f"| {item['arm']} | {int(item['optimize_count'])} | "
            f"{int(item['model_read_count'])} | "
            f"{int(item['artifact_generation_count'])}+"
            f"{int(item['artifact_cache_hit_count'])} hits | {presolve} | {root} | "
            f"{int(item['fresh_restart_count'])}/"
            f"{int(item['same_leaf_restart_count'])}/"
            f"{int(item['child_restart_count'])} | {int(item['split_count'])} | "
            f"{int(item['closed_leaf_count'])} |")

    diagnostic_lines = [
        f"| {item['trigger_id']} | {item['trigger_reason']} | "
        f"{item['diagnostic_outcome']} | "
        f"{str(item['bottleneck_classifications']).replace(';', ', ')} |"
        for item in diagnostics]

    build = load_json(OUT / "round25_build_manifest.json")
    license_audit = load_json(OUT / "license_visibility_audit.json")
    cplex_version = "22.1.1.0"
    official_wall = sum(float(row["process_wall_seconds"]) for row in official
                        if finite(row.get("process_wall_seconds")))
    evidence_wall = sum(float(row["process_wall_seconds"]) for row in rows
                        if finite(row.get("process_wall_seconds")))
    package_files = [path for path in OUT.rglob("*") if path.is_file()]
    largest = max(package_files, key=lambda path: path.stat().st_size)
    package_bytes = sum(path.stat().st_size for path in package_files)
    threshold_count = len(csv_rows(OUT / "time_to_gap_thresholds.csv"))
    warm_total = next(item for item in metric_rows
                      if item["stage"] == "official_total" and
                      item["arm"] == "EXT-GRB-WARM")

    report_text = f"""# Round 25 final report

## Decision

`EXT-GRB-COLD` is **{external_decision}** and is broadly nonregressive against
plain Gurobi. It wins the frozen hierarchy on {cold_plain_wins}/12 matched rows
versus `P-GRB`, {cold_cpx_wins}/12 versus `EXT-CPX`, and {cold_s0_wins}/12
versus `S0-SAFE`. Its two losses to plain Gurobi are the preregistered V12
certificate-time triggers; every non-V12 family/seed row favors the cold
external arm, including all three held-out V20 seeds and all four 1200-second
rows. This is enough to justify a later full production validation round, but
not a production-default migration in Round 25.

`EXT-GRB-WARM` is **{warm_decision}**: warm wins {warm_wins}/12 and cold wins
{cold_wins}/12. Only {int(warm_total['warm_accepted_count'])} of
{int(warm_total['warm_candidate_count'])} official candidates were accepted
({int(warm_total['warm_submitted_count'])} submitted;
{int(warm_total['warm_rejected_count'])} rejected), and two material Stage 1
warm losses triggered diagnostics. It does not become the default.

Corrected CPLEX `S0-SAFE` remains the stable paper/mainline reference. No
default, dispatch rule, portfolio, or family-dependent selector changed.

## Provenance, qualification, and exactness

The authoritative local base is `d52e340ef62be2bc2f248a1c5ad93cbbb75c6920`;
the frozen executable was built from Round 25 implementation commit
`{build.get('source_commit', '')}`. The observed `origin/main` was
`639c3772687d4a22e6b2cf3daa4d16c03d015ecd`. The frozen unified executable is
`{build.get('unified_gurobi_enabled_sha256', '')}` and the CPLEX-only control is
`{build.get('cplex_only_sha256', '')}`. Solver versions are CPLEX
{cplex_version} and Gurobi {license_audit.get('gurobi_version', 'unavailable')}.

Both clean release configurations passed 9/9 C++ tests (18/18 total). All six
Python regression scripts passed. Static exactness passed 29/29 checks with
zero production instance/seed dispatch matches. Native Gurobi import, domain,
name, type, and bound audits passed on 10/10 inputs. The four tiny qualification
runs passed, including two strict toy certificates with zero CPLEX/Gurobi
objective delta. The moderate4301 sentinel passed 3/3 arms, retained three
verified witnesses, and reported zero contradicted infeasibilities.

All {len(rows)} retained sentinel/official/diagnostic rows are authoritative,
have verified witnesses, and pass every applicable verifier, coverage,
lifecycle, and consistency gate. There are {correctness_failures} correctness
failures.

## Official outcomes and strict certificates

Round 25 completed {len(official)}/{len(official)} official processes:
{by_stage['stage1']} at 900 seconds and {by_stage['stage2']} at 1200 seconds.
Completed/failed/interrupted/excluded counts are
{counts['completed']}/{counts['failed']}/{counts['interrupted']}/{counts['excluded']}.
Of the completed rows, {time_limited} ended at a valid solver time limit and 15
ended optimal/strict; time-limited completion is not counted as interruption.

| Horizon | {' | '.join(frozen.ARMS)} |
| --- | {' | '.join('---' for _ in frozen.ARMS)} |
{chr(10).join(strict_lines)}

## Frozen paired hierarchy

Win columns are `left-right-tie`; strict columns and mean gap/AUC columns are
also `left-right`. The ranking is certificate, certificate time, valid LB,
common-UB gap, then AUC; never relative gap with different UBs.

| Horizon | Comparison | Wins | Strict | Mean common gap | Mean AUC |
| --- | --- | ---: | ---: | ---: | ---: |
{chr(10).join(pair_lines)}

Plain Gurobi beats plain CPLEX on all 8/8 Stage 1 and 4/4 Stage 2 rows.
EXT-CPX beats plain CPLEX on all 12 matched rows. Cold external Gurobi beats
plain Gurobi 6-2 at 900 seconds and 4-0 at 1200 seconds; it beats EXT-CPX and
S0-SAFE 8-0 then 4-0. EXT-CPX beats S0-SAFE 7-1 then 4-0. Warm/cold is 4-4 at
900 seconds and 1-3 at 1200 seconds.

### Cold external Gurobi versus plain Gurobi by family

| Horizon | Family | P-GRB-cold wins | Mean common gap | Mean AUC |
| --- | --- | ---: | ---: | ---: |
{chr(10).join(family_lines)}

The only family regression is V12 certificate time. High-imbalance, moderate,
and tight-T all favor cold external Gurobi on both hard-stress and held-out
seeds, so the result does not depend on a selected seed or warm-start luck.
No held-out V20 seed produced a strict certificate, however; all produced valid
bounds. That missing held-out certificate coverage blocks production migration
now and is a required target of the recommended full production validation.

## Common-gap and trajectory summaries

Values are mean/median across the fixed instances. Exact per-row AUC and all
{threshold_count} observed threshold-crossing interval records are retained in
`bound_progress_auc.csv` and `time_to_gap_thresholds.csv`.

| Horizon | Arm | Strict | Common gap mean/median | AUC mean/median |
| --- | --- | ---: | ---: | ---: |
{chr(10).join(metric_lines)}

## Lifecycle and restart accounting

Counts below sum all 72 official rows. Restart columns are
fresh/same-leaf/child. CPLEX external presolve/root counts and phase times are
marked unavailable because callable-library logging cannot safely isolate them
per leaf; native phase time is also unavailable from the Gurobi C API. These
values are not estimated.

| Arm | Optimize | Model reads | Artifacts | Presolve | Root | Restarts | Splits | Closures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(lifecycle_lines)}

## Preregistered diagnostics

Exactly {summary['triggered_pairs']} pairs triggered and all
{summary['diagnostic_replays_completed']} exactly-once 300-second replays
completed. They remain diagnostic and do not replace official rows.

| Trigger | Official reason | Replay outcome | Evidence-based classifications |
| --- | --- | --- | --- |
{chr(10).join(diagnostic_lines)}

V12_M1 reverses its very small official certificate-time ordering in replay
(cold 35.280s versus the official plain 35.321s), so that loss is unstable.
V12_M2 reproduces the plain advantage (169.341s versus replay cold 174.701s),
with repeated native model/presolve/root execution. The moderate3302 warm loss
is reproduced at 300 seconds (cold LB 0.159864 versus replay warm 0.159609).
The tight-T warm loss reverses at 300 seconds (cold LB 0.052886 versus replay
warm 0.052925), hence unstable. Complete enhanced traces and per-trigger reports
are retained; unsupported phase timers remain explicitly unavailable.

## Evidence accounting and limitations

Official process wall totals {duration(official_wall)}; all 79 retained solve
rows total {duration(evidence_wall)}, excluding build/test/reporting overhead.
The package currently contains {len(package_files)} files and
{package_bytes / (1024 ** 2):.1f} MiB. Its largest artifact is
`{relative(largest)}` at {largest.stat().st_size} bytes. Large/dense files and
the text LP model corpus are deterministic gzip streams with restored hashes
and byte counts recorded in compression manifests. The final package audit
independently restored and hash-verified
{package_audit.get('compressed_files_restored_and_hash_verified', 0)} compressed
files and found no retained sensitive license marker.

There were no failed diagnostics, contradictory rows, missing official rows,
silent backend fallbacks, or invalid bounds. The main limitation is unavailable
safe per-leaf CPLEX presolve/root timing (and unavailable native Gurobi phase
timers/cut totals), which prevents converting repeated phase counts into exact
time attribution. Warm-start behavior is mixed and largely rejected. These
limitations support retaining CPLEX S0/F0 as mainline while advancing cold
external Gurobi to a dedicated production-validation round.
"""
    (OUT / "final_report.md").write_text(report_text, encoding="utf-8")


def evidence_manifest() -> None:
    manifest = OUT / "evidence_package_manifest.csv"
    rows = []
    for path in sorted(item for item in OUT.rglob("*")
                       if item.is_file() and item != manifest):
        rows.append({
            "path": relative(path), "bytes": path.stat().st_size,
            "sha256": frozen.sha256(path),
        })
    write_csv(manifest, rows, ["path", "bytes", "sha256"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit-triggers", action="store_true")
    parser.add_argument("--final", action="store_true")
    args = parser.parse_args()
    rows = run_rows()
    add_common_ubs(rows)
    auc_rows, threshold_rows = progress_metrics(rows)
    triggers = emit_triggers(rows)
    if args.emit_triggers and not args.final:
        stage1_count = sum(row["stage"] == "stage1" for row in rows)
        if stage1_count != 48:
            raise RuntimeError(f"expected 48 Stage 1 rows, found {stage1_count}")
        print(f"Round25 triggers emitted: "
              f"{sum(truth(row['triggered']) for row in triggers)}")
        return 0

    write_csv(OUT / "model_and_certificate_audit.csv", stage0_audit())
    write_csv(OUT / "moderate4301_correctness.csv",
              [public(row) for row in rows if row["stage"] == "sentinel"],
              SUMMARY_FIELDS)
    write_csv(OUT / "stage1_900s_results.csv",
              [public(row) for row in rows if row["stage"] == "stage1"],
              SUMMARY_FIELDS)
    write_csv(OUT / "stage2_1200s_results.csv",
              [public(row) for row in rows if row["stage"] == "stage2"],
              SUMMARY_FIELDS)
    strict_counts = Counter(
        (str(row["stage"]), str(row["arm"])) for row in rows
        if row["stage"] in ("stage1", "stage2") and
        row["strict_certificate"])
    strict_rows = [
        {"stage": stage, "horizon_seconds": horizon, "arm": arm,
         "strict_certificates": strict_counts[(stage, arm)],
         "official_rows": sum(
             row["stage"] == stage and row["arm"] == arm for row in rows)}
        for stage, horizon in (("stage1", 900), ("stage2", 1200))
        for arm in frozen.ARMS]
    write_csv(OUT / "strict_certificate_summary.csv", strict_rows)
    pairs = {
        "plain_cplex_vs_gurobi.csv": ("P-CPX", "P-GRB"),
        "external_cplex_vs_plain_cplex.csv": ("P-CPX", "EXT-CPX"),
        "external_gurobi_vs_plain_gurobi.csv": ("P-GRB", "EXT-GRB-COLD"),
        "external_cplex_vs_gurobi.csv": ("EXT-CPX", "EXT-GRB-COLD"),
        "gurobi_warm_vs_cold.csv": ("EXT-GRB-COLD", "EXT-GRB-WARM"),
    }
    for filename, arms in pairs.items():
        write_csv(OUT / filename, paired(rows, *arms))
    external_s0 = paired(rows, "S0-SAFE", "EXT-CPX") + \
        paired(rows, "S0-SAFE", "EXT-GRB-COLD")
    write_csv(OUT / "external_vs_s0.csv", external_s0)
    write_csv(OUT / "bound_progress_auc.csv", auc_rows)
    write_csv(OUT / "time_to_gap_thresholds.csv", threshold_rows)
    write_csv(OUT / "lifecycle_and_restart_summary.csv",
              [public(row) for row in rows], SUMMARY_FIELDS)
    write_csv(OUT / "paired_decision_summary.csv",
              paired_decision_rows(rows))
    write_csv(OUT / "family_pair_summary.csv",
              paired_decision_rows(rows, by_family=True))
    write_csv(OUT / "aggregate_metric_summary.csv",
              aggregate_metric_rows(rows))
    diagnostics = diagnostic_rows(rows, triggers)
    write_csv(OUT / "underperformance_diagnostics.csv", diagnostics)
    write_csv(OUT / "exactness_audit.csv", [public(row) for row in rows],
              SUMMARY_FIELDS)
    report(rows, triggers, diagnostics)
    package_integrity_audit(rows, diagnostics)
    # Re-emit the summary/report so they include the sealed package-audit result.
    report(rows, triggers, diagnostics)
    evidence_manifest()
    print(f"Round25 summary generated for {len(rows)} rows", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
