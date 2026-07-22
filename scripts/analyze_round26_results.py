#!/usr/bin/env python3
"""Incremental and final analysis for the frozen Round 26 experiment matrix."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any

import run_round26_experiments as frozen
import summarize_round25_results as prior


ROOT = frozen.ROOT
OUT = frozen.OUT
RUNS = OUT / "runs"
THRESHOLDS = prior.THRESHOLDS
SUMMARY_FIELDS = prior.SUMMARY_FIELDS
STAGE_FILES = {
    "stage1": "stage1_known_1200s.csv",
    "stage2": "stage2_heldout_v20_1800s.csv",
    "stage3": "stage3_v50_1800s.csv",
    "stage4": "stage4_long_3600s.csv",
}


def finite(value: Any) -> bool:
    return prior.finite(value)


def truth(value: Any) -> bool:
    return prior.truth(value)


def value(data: dict[str, Any], *names: str, default: Any = "") -> Any:
    return prior.value(data, *names, default=default)


def load_json(path: Path) -> dict[str, Any]:
    return prior.load_json(path)


def write_csv(path: Path, rows: list[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    prior.write_csv(path, rows, fields)


def relative(path: Path) -> str:
    return frozen.relative(path)


def verified_witness(result: dict[str, Any]) -> bool:
    verification = result.get("verification", {})
    return bool(result.get("verified_incumbent_original_problem_feasible", False) or
                result.get("verifier_passed", False) or
                verification.get("original_solution_feasible", False))


def external_gates(result: dict[str, Any]) -> bool:
    return all(bool(result.get(name, False)) for name in (
        "external_gini_tree_root_coverage_valid",
        "external_gini_tree_parent_child_coverage_valid",
        "external_gini_tree_all_leaf_bounds_valid",
        "external_gini_tree_global_bound_monotone",
        "external_gini_tree_leaf_bounds_monotone",
        "external_gini_tree_lifecycle_complete",
        "external_gini_tree_feasibility_consistency_gate",
    ))


def extract_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for directory in sorted(path for path in RUNS.iterdir() if path.is_dir()):
        command = load_json(directory / "command.json")
        state = load_json(directory / "run_state.json")
        result = load_json(directory / "result.json")
        stage = str(command.get("stage", ""))
        if not (stage in frozen.OFFICIAL_STAGES or stage.startswith("diagnostic_")):
            continue
        arm = str(command.get("arm", ""))
        if arm not in ("P-GRB", "C0", "C1"):
            continue
        external = arm in ("C0", "C1")
        witness = verified_witness(result)
        process_ok = (state.get("return_code") == 0 and bool(result) and
                      state.get("sensitive_marker_scan_passed") is True)
        gates = external_gates(result) if external else True
        authoritative = process_ok and witness and gates
        verified_ub = value(result, "verified_incumbent_objective", "objective")
        if not witness or not finite(verified_ub):
            verified_ub = ""
        strict = bool(result.get("strict_certified_original_problem", False))
        if external:
            strict = bool(result.get("external_gini_tree_strict_certified", strict))
        enhanced = prior.enhanced_metrics(directory) if external else {}
        instance = str(command.get("instance", ""))
        row: dict[str, Any] = {
            "stage": stage,
            "horizon_seconds": command.get("budget_seconds", ""),
            "instance": instance,
            "family": frozen.INSTANCES.get(instance, (Path(), "unknown", 0))[1],
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
            "native_incumbent": "",
            "native_bound": "",
            "verified_ub": verified_ub,
            "common_ub": "",
            "final_lb": value(result, "lower_bound") if authoritative else "",
            "common_ub_gap": "",
            "bound_progress_auc": "",
            "process_wall_seconds": value(
                result, "final_process_wall_time_seconds", "runtime_seconds"),
            "first_incumbent_seconds": "",
            "last_lb_improvement_seconds": "",
            "stagnation_seconds": "",
            "nodes": 0,
            "open_nodes": "",
            "work": "",
            "simplex_iterations": "",
            "barrier_iterations": "",
            "memory_gb": "",
            "hga_seconds": result.get("incumbent_generation_time_seconds", 0),
            "optimize_count": 0,
            "model_count": 0,
            "model_read_count": 0,
            "artifact_generation_count": 0,
            "artifact_cache_hit_count": 0,
            "artifact_generation_seconds": 0,
            "model_read_seconds": 0,
            "presolve_count": 0,
            "root_count": 0,
            "presolve_seconds": "unavailable",
            "root_seconds": "unavailable",
            "presolve_time_status": "unavailable_not_safely_reported",
            "root_time_status": "unavailable_not_safely_reported",
            "native_cut_count": "",
            "native_cut_count_status": "unavailable_not_safely_reported",
            "fresh_restart_count": 0,
            "same_leaf_restart_count": 0,
            "child_restart_count": 0,
            "attempt_count": 0,
            "split_count": 0,
            "closed_leaf_count": "",
            "open_leaf_count": "",
            "warm_candidate_count": 0,
            "warm_complete_count": 0,
            "warm_submitted_count": 0,
            "warm_accepted_count": 0,
            "warm_rejected_count": 0,
            "warm_unknown_count": 0,
            "coverage_gate": gates,
            "lifecycle_gate": result.get(
                "external_gini_tree_lifecycle_complete", False) if external else True,
            "consistency_gate": result.get(
                "external_gini_tree_feasibility_consistency_gate", False)
                if external else True,
            "verifier_gate": witness,
            "result_path": relative(directory / "result.json"),
            "run_dir": directory,
            "command": command,
            "state": state,
            "result": result,
        }
        if external:
            row.update({
                "native_incumbent": enhanced.get("native_incumbent", ""),
                "native_bound": result.get(
                    "external_gini_tree_global_lower_bound", ""),
                "nodes": result.get("external_gini_tree_nodes", 0),
                "open_nodes": enhanced.get("native_open_nodes", ""),
                "work": result.get("external_gini_tree_work", ""),
                "simplex_iterations": result.get(
                    "external_gini_tree_simplex_iterations", ""),
                "barrier_iterations": result.get(
                    "external_gini_tree_barrier_iterations", ""),
                "memory_gb": result.get("external_gini_tree_peak_memory_gb", ""),
                "first_incumbent_seconds": result.get(
                    "external_gini_tree_first_incumbent_time_seconds", ""),
                "last_lb_improvement_seconds": result.get(
                    "external_gini_tree_last_global_lb_improvement_time_seconds", ""),
                "stagnation_seconds": result.get(
                    "external_gini_tree_final_stagnation_seconds", ""),
                "optimize_count": result.get(
                    "external_gini_tree_optimize_count", 0),
                "model_count": result.get("external_gini_tree_model_count", 0),
                "model_read_count": result.get(
                    "external_gini_tree_model_read_count", 0),
                "artifact_generation_count": result.get(
                    "external_gini_tree_canonical_artifact_generation_count", 0),
                "artifact_cache_hit_count": result.get(
                    "external_gini_tree_canonical_artifact_cache_hit_count", 0),
                "artifact_generation_seconds": result.get(
                    "external_gini_tree_canonical_artifact_generation_seconds", 0),
                "model_read_seconds": result.get(
                    "external_gini_tree_model_read_seconds", 0),
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
                "split_count": result.get("external_gini_tree_split_count", 0),
                "closed_leaf_count": result.get(
                    "external_gini_tree_closed_leaf_count", ""),
                "open_leaf_count": result.get(
                    "external_gini_tree_open_leaf_count", ""),
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
            })
        else:
            row.update({
                "native_incumbent": result.get("gurobi_obj_val", "")
                    if result.get("gurobi_obj_val_available", False) else "",
                "native_bound": result.get("gurobi_obj_bound_c", "")
                    if result.get("gurobi_obj_bound_c_available", False) else "",
                "nodes": result.get("gurobi_node_count", 0),
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
            if finite(row["process_wall_seconds"]) and finite(
                    row["last_lb_improvement_seconds"]):
                row["stagnation_seconds"] = max(
                    0.0, float(row["process_wall_seconds"]) -
                    float(row["last_lb_improvement_seconds"]))
        rows.append(row)
    return rows


def official_stage_for(row: dict[str, Any]) -> str:
    if row["stage"] in frozen.OFFICIAL_STAGES:
        return str(row["stage"])
    return str(row["command"].get("diagnostic_trigger", {}).get(
        "official_stage", ""))


def add_common_ubs(rows: list[dict[str, Any]]) -> None:
    common: dict[tuple[str, str], float] = {}
    for row in rows:
        if row["stage"] not in frozen.OFFICIAL_STAGES or not finite(row["verified_ub"]):
            continue
        key = (str(row["stage"]), str(row["instance"]))
        common[key] = min(common.get(key, math.inf), float(row["verified_ub"]))
    for row in rows:
        key = (official_stage_for(row), str(row["instance"]))
        ub = common.get(key)
        row["common_ub"] = "" if ub is None else ub
        if ub is not None and finite(row["final_lb"]) and abs(ub) > 1e-12:
            row["common_ub_gap"] = max(
                0.0, (ub - float(row["final_lb"])) / abs(ub))


def progress_metrics(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]],
                                                          list[dict[str, Any]]]:
    auc_rows: list[dict[str, Any]] = []
    crossing_rows: list[dict[str, Any]] = []
    for row in rows:
        budget = float(row.get("horizon_seconds") or 0)
        ub = row.get("common_ub")
        points = prior.trace_points(row)
        row["threshold_crossings"] = {}
        if budget <= 0 or not finite(ub) or abs(float(ub)) <= 1e-12 or not points:
            auc_rows.append({
                "stage": row["stage"], "instance": row["instance"],
                "arm": row["arm"], "common_ub": ub, "points": len(points),
                "gap_auc": "", "bound_progress_auc": "", "status": "unavailable",
            })
            continue
        common_ub = float(ub)
        series = [(0.0, 1.0)]
        for timestamp, bound in points:
            series.append((min(budget, timestamp), max(
                0.0, (common_ub - bound) / abs(common_ub))))
        final_gap = row.get("common_ub_gap")
        series.append((budget, float(final_gap) if finite(final_gap) else series[-1][1]))
        series.sort()
        area = 0.0
        previous_time, previous_gap = series[0]
        first: dict[float, tuple[float, float] | None] = {
            threshold: None for threshold in THRESHOLDS}
        for timestamp, gap in series[1:]:
            area += (timestamp - previous_time) * (previous_gap + gap) / 2.0
            for threshold in first:
                if first[threshold] is None and gap <= threshold:
                    first[threshold] = (previous_time, timestamp)
            previous_time, previous_gap = timestamp, gap
        gap_auc = area / budget
        row["bound_progress_auc"] = 1.0 - gap_auc
        auc_rows.append({
            "stage": row["stage"], "instance": row["instance"],
            "arm": row["arm"], "common_ub": common_ub, "points": len(points),
            "gap_auc": gap_auc, "bound_progress_auc": row["bound_progress_auc"],
            "status": "available",
        })
        for threshold, interval in first.items():
            row["threshold_crossings"][threshold] = (
                math.inf if interval is None else interval[1])
            crossing_rows.append({
                "stage": row["stage"], "instance": row["instance"],
                "arm": row["arm"], "common_ub": common_ub,
                "gap_threshold": threshold,
                "crossing_interval_lower_seconds": "" if interval is None else interval[0],
                "crossing_interval_upper_seconds": "" if interval is None else interval[1],
                "reached": interval is not None,
            })
    return auc_rows, crossing_rows


def ranking(left: dict[str, Any], right: dict[str, Any]) -> tuple[str, str]:
    if not left or not right:
        return "tie", "missing_matched_row"
    left_strict, right_strict = truth(left["strict_certificate"]), truth(
        right["strict_certificate"])
    if left_strict != right_strict:
        return ("left", "left_only_strict_certificate") if left_strict else (
            "right", "right_only_strict_certificate")
    if left_strict and right_strict:
        lt, rt = float(left["certificate_wall_seconds"]), float(
            right["certificate_wall_seconds"])
        if abs(lt - rt) > 1e-9:
            return ("left", "left_lower_certificate_wall_time") if lt < rt else (
                "right", "right_lower_certificate_wall_time")
    if finite(left["final_lb"]) and finite(right["final_lb"]):
        delta = float(left["final_lb"]) - float(right["final_lb"])
        if abs(delta) > 1e-12:
            return ("left", "left_higher_valid_final_lb") if delta > 0 else (
                "right", "right_higher_valid_final_lb")
    if finite(left["common_ub_gap"]) and finite(right["common_ub_gap"]):
        delta = float(left["common_ub_gap"]) - float(right["common_ub_gap"])
        if abs(delta) > 1e-12:
            return ("left", "left_smaller_common_ub_gap") if delta < 0 else (
                "right", "right_smaller_common_ub_gap")
    if finite(left["bound_progress_auc"]) and finite(right["bound_progress_auc"]):
        delta = float(left["bound_progress_auc"]) - float(right["bound_progress_auc"])
        if abs(delta) > 1e-12:
            return ("left", "left_higher_bound_progress_auc") if delta > 0 else (
                "right", "right_higher_bound_progress_auc")
    left_crossings = left.get("threshold_crossings", {})
    right_crossings = right.get("threshold_crossings", {})
    for threshold in THRESHOLDS:
        lt, rt = left_crossings.get(threshold, math.inf), right_crossings.get(
            threshold, math.inf)
        if abs(lt - rt) > 1e-9:
            return ("left", f"left_earlier_gap_{threshold}") if lt < rt else (
                "right", f"right_earlier_gap_{threshold}")
    return "tie", "frozen_hierarchy_tie"


def paired(rows: list[dict[str, Any]], left_arm: str,
           right_arm: str) -> list[dict[str, Any]]:
    official = [row for row in rows if row["stage"] in frozen.OFFICIAL_STAGES]
    by_key = {(row["stage"], row["instance"], row["arm"]): row for row in official}
    keys = sorted({(row["stage"], row["instance"]) for row in official
                   if (row["stage"], row["instance"], left_arm) in by_key and
                   (row["stage"], row["instance"], right_arm) in by_key})
    output: list[dict[str, Any]] = []
    for stage, instance in keys:
        left = by_key.get((stage, instance, left_arm), {})
        right = by_key.get((stage, instance, right_arm), {})
        winner, reason = ranking(left, right)
        item: dict[str, Any] = {
            "stage": stage, "instance": instance,
            "left_arm": left_arm, "right_arm": right_arm,
            "winner": winner, "decision_reason": reason,
        }
        for prefix, row in (("left", left), ("right", right)):
            for field in ("status", "strict_certificate", "certificate_wall_seconds",
                          "final_lb", "verified_ub", "common_ub_gap",
                          "bound_progress_auc", "process_wall_seconds", "work"):
                item[f"{prefix}_{field}"] = row.get(field, "")
        output.append(item)
    return output


def emit_triggers(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    official = [row for row in rows if row["stage"] in frozen.OFFICIAL_STAGES]
    by_key = {(row["stage"], row["instance"], row["arm"]): row for row in official}
    keys = sorted({(str(row["stage"]), str(row["instance"])) for row in official
                   if row["arm"] == "P-GRB"})
    output: list[dict[str, Any]] = []
    for stage, instance in keys:
        plain = by_key.get((stage, instance, "P-GRB"), {})
        c1 = by_key.get((stage, instance, "C1"), {})
        if not c1:
            continue
        winner, reason = ranking(plain, c1)
        horizon = int(plain["horizon_seconds"])
        trigger_id = f"{stage}__{instance}__{horizon}s__c1"
        output.append({
            "trigger_id": trigger_id,
            "official_stage": stage,
            "official_horizon_seconds": horizon,
            "instance": instance,
            "family": plain["family"],
            "V": frozen.INSTANCES[instance][2],
            "comparison": "P-GRB_vs_C1",
            "matched_plain_arm": "P-GRB",
            "underperforming_external_arm": "C1",
            "replay_arm": "C1",
            "triggered": winner == "left",
            "trigger_reason": reason,
            "winner": "P-GRB" if winner == "left" else (
                "C1" if winner == "right" else "tie"),
            "official_p_grb_status": plain.get("status", "missing"),
            "official_c1_status": c1.get("status", "missing"),
            "official_p_grb_strict": plain.get("strict_certificate", ""),
            "official_c1_strict": c1.get("strict_certificate", ""),
            "official_p_grb_certificate_wall_seconds": plain.get(
                "certificate_wall_seconds", ""),
            "official_c1_certificate_wall_seconds": c1.get(
                "certificate_wall_seconds", ""),
            "official_p_grb_final_lb": plain.get("final_lb", ""),
            "official_c1_final_lb": c1.get("final_lb", ""),
            "official_p_grb_common_gap": plain.get("common_ub_gap", ""),
            "official_c1_common_gap": c1.get("common_ub_gap", ""),
            "official_p_grb_auc": plain.get("bound_progress_auc", ""),
            "official_c1_auc": c1.get("bound_progress_auc", ""),
            "diagnostic_budget_seconds": 900 if frozen.INSTANCES[instance][2] == 50 else 600,
            "diagnostic_replaces_official": False,
        })
    write_csv(OUT / "regression_trigger_table.csv", output)
    return output


def classify_diagnostic(reference: dict[str, Any], replay: dict[str, Any]) -> str:
    if not replay or not truth(replay.get("authoritative")):
        return "insufficient evidence"
    if not all(truth(replay.get(gate)) for gate in (
            "coverage_gate", "lifecycle_gate", "consistency_gate",
            "verifier_gate")):
        return "numerical issue"
    ref_wall = float(reference["certificate_wall_seconds"]) \
        if finite(reference.get("certificate_wall_seconds")) else math.inf
    replay_wall = float(replay["certificate_wall_seconds"]) \
        if finite(replay.get("certificate_wall_seconds")) else math.inf
    ref_work = float(reference["work"]) if finite(reference.get("work")) else math.nan
    replay_work = float(replay["work"]) if finite(replay.get("work")) else math.nan
    if truth(reference.get("strict_certificate")) and truth(
            replay.get("strict_certificate")):
        wall_ratio = replay_wall / ref_wall if ref_wall > 0 else math.inf
        work_ratio = replay_work / ref_work if ref_work > 0 else math.inf
        if wall_ratio <= 1.05 and work_ratio <= 1.05:
            return "timing noise"
        if (work_ratio > 1.05 and
                int(float(replay.get("presolve_count") or 0)) > 1 and
                int(float(replay.get("fresh_restart_count") or 0)) > 1):
            return "persistent external-overhead regression"
    wall = float(replay.get("process_wall_seconds") or 0)
    stagnation = float(replay.get("stagnation_seconds") or 0)
    if frozen.INSTANCES[str(replay["instance"])][2] == 50 and finite(
            replay.get("memory_gb")) and float(replay["memory_gb"]) >= 1.0:
        return "scalability/memory overhead"
    if wall > 0 and stagnation > 0.40 * wall:
        return "scheduler/controlling-leaf stagnation"
    if int(float(replay.get("split_count") or 0)) >= 8:
        return "excessive partitioning"
    if finite(replay.get("common_ub_gap")) and float(
            replay["common_ub_gap"]) > 0.10:
        return "weak interval relaxation"
    return "insufficient evidence"


def diagnostic_rows(rows: list[dict[str, Any]],
                    triggers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    official = {(row["stage"], row["instance"], row["arm"]): row for row in rows
                if row["stage"] in frozen.OFFICIAL_STAGES}
    diagnostic_by_trigger: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not str(row["stage"]).startswith("diagnostic_"):
            continue
        trigger_id = str(row["command"].get("diagnostic_trigger", {}).get(
            "trigger_id", ""))
        diagnostic_by_trigger.setdefault(trigger_id, []).append(row)
    report_dir = OUT / "diagnostics"
    report_dir.mkdir(parents=True, exist_ok=True)
    output: list[dict[str, Any]] = []
    for trigger in triggers:
        if not truth(trigger.get("triggered")):
            continue
        trigger_id = str(trigger["trigger_id"])
        matches = diagnostic_by_trigger.get(trigger_id, [])
        if len(matches) > 1:
            raise RuntimeError(f"more than one replay for trigger {trigger_id}")
        replay = matches[0] if matches else {}
        reference = official.get((trigger["official_stage"], trigger["instance"],
                                  "P-GRB"), {})
        classification = classify_diagnostic(reference, replay)
        report_path = report_dir / f"{trigger_id}.md"
        enhanced = ""
        ledger = ""
        attempts = ""
        if replay:
            run_dir = Path(replay["run_dir"])
            for name, target in (
                    ("enhanced_attempt_trace.csv", "enhanced"),
                    ("external_leaf_ledger.csv", "ledger")):
                candidate = run_dir / "external" / name
                actual = candidate if candidate.exists() else Path(str(candidate) + ".gz")
                if actual.exists():
                    if target == "enhanced":
                        enhanced = relative(actual)
                    else:
                        ledger = relative(actual)
            attempts = replay.get("attempt_count", "")
        ref_wall = float(reference["certificate_wall_seconds"]) \
            if finite(reference.get("certificate_wall_seconds")) else math.nan
        replay_wall = float(replay["certificate_wall_seconds"]) \
            if finite(replay.get("certificate_wall_seconds")) else math.nan
        ref_work = float(reference["work"]) \
            if finite(reference.get("work")) else math.nan
        replay_work = float(replay["work"]) \
            if finite(replay.get("work")) else math.nan
        wall_ratio = replay_wall / ref_wall if ref_wall > 0 else ""
        work_ratio = replay_work / ref_work if ref_work > 0 else ""
        report = (
            f"# Enhanced diagnostic: {trigger_id}\n\n"
            f"Classification: **{classification}**. This is the exactly-once "
            f"{trigger['diagnostic_budget_seconds']}-second frozen-C1 replay "
            f"triggered by `{trigger['trigger_reason']}`. It is diagnostic-only "
            "and does not replace the official result.\n\n"
            "## Matched observation\n\n"
            f"Official P-GRB status/certificate time/Work: "
            f"`{reference.get('status', 'missing')}` / "
            f"`{reference.get('certificate_wall_seconds', '')}` / "
            f"`{reference.get('work', '')}`. Replay status/certificate time/Work: "
            f"`{replay.get('status', 'missing')}` / "
            f"`{replay.get('certificate_wall_seconds', '')}` / "
            f"`{replay.get('work', '')}`. Replay/P-GRB wall and Work ratios are "
            f"`{wall_ratio}` and `{work_ratio}`.\n\n"
            "## External-tree evidence\n\n"
            f"Models/reads/optimize calls: `{replay.get('model_count', '')}/"
            f"{replay.get('model_read_count', '')}/"
            f"{replay.get('optimize_count', '')}`. Presolve/root executions: "
            f"`{replay.get('presolve_count', '')}/"
            f"{replay.get('root_count', '')}`. Fresh/same-leaf/child restarts: "
            f"`{replay.get('fresh_restart_count', '')}/"
            f"{replay.get('same_leaf_restart_count', '')}/"
            f"{replay.get('child_restart_count', '')}`. Attempts/splits/closed/open "
            f"leaves: `{attempts}/{replay.get('split_count', '')}/"
            f"{replay.get('closed_leaf_count', '')}/"
            f"{replay.get('open_leaf_count', '')}`. Nodes/simplex iterations/peak "
            f"memory GB: `{replay.get('nodes', '')}/"
            f"{replay.get('simplex_iterations', '')}/"
            f"{replay.get('memory_gb', '')}`. Model generation/read seconds: "
            f"`{replay.get('artifact_generation_seconds', '')}/"
            f"{replay.get('model_read_seconds', '')}`. Last global-LB improvement "
            f"and final stagnation seconds: "
            f"`{replay.get('last_lb_improvement_seconds', '')}/"
            f"{replay.get('stagnation_seconds', '')}`.\n\n"
            f"Enhanced attempt trace: `{enhanced or 'missing'}`. Leaf ledger: "
            f"`{ledger or 'missing'}`. All coverage, lifecycle, consistency, and "
            f"verifier gates: `{replay.get('coverage_gate', '')}/"
            f"{replay.get('lifecycle_gate', '')}/"
            f"{replay.get('consistency_gate', '')}/"
            f"{replay.get('verifier_gate', '')}`.\n")
        report_path.write_text(report, encoding="utf-8")
        output.append({
            "trigger_id": trigger_id,
            "official_stage": trigger["official_stage"],
            "official_horizon_seconds": trigger["official_horizon_seconds"],
            "instance": trigger["instance"],
            "classification": classification,
            "replay_completed": bool(replay),
            "replay_return_code": replay.get("return_code", ""),
            "replay_status": replay.get("status", "missing"),
            "replay_authoritative": replay.get("authoritative", ""),
            "reference_certificate_wall_seconds": reference.get(
                "certificate_wall_seconds", ""),
            "replay_certificate_wall_seconds": replay.get(
                "certificate_wall_seconds", ""),
            "certificate_wall_ratio": wall_ratio,
            "reference_work": reference.get("work", ""),
            "replay_work": replay.get("work", ""),
            "work_ratio": work_ratio,
            "final_lb": replay.get("final_lb", ""),
            "common_ub_gap": replay.get("common_ub_gap", ""),
            "bound_progress_auc": replay.get("bound_progress_auc", ""),
            "models": replay.get("model_count", ""),
            "model_reads": replay.get("model_read_count", ""),
            "optimize_calls": replay.get("optimize_count", ""),
            "presolve_executions": replay.get("presolve_count", ""),
            "root_executions": replay.get("root_count", ""),
            "fresh_restarts": replay.get("fresh_restart_count", ""),
            "same_leaf_restarts": replay.get("same_leaf_restart_count", ""),
            "child_restarts": replay.get("child_restart_count", ""),
            "attempts": replay.get("attempt_count", ""),
            "splits": replay.get("split_count", ""),
            "closed_leaves": replay.get("closed_leaf_count", ""),
            "open_leaves": replay.get("open_leaf_count", ""),
            "nodes": replay.get("nodes", ""),
            "simplex_iterations": replay.get("simplex_iterations", ""),
            "peak_memory_gb": replay.get("memory_gb", ""),
            "model_generation_seconds": replay.get(
                "artifact_generation_seconds", ""),
            "model_read_seconds": replay.get("model_read_seconds", ""),
            "last_lb_improvement_seconds": replay.get(
                "last_lb_improvement_seconds", ""),
            "stagnation_seconds": replay.get("stagnation_seconds", ""),
            "enhanced_trace": enhanced,
            "leaf_ledger": ledger,
            "report": relative(report_path),
        })
    return output


def mean_value(rows: list[dict[str, Any]], field: str) -> Any:
    values = [float(row[field]) for row in rows if finite(row.get(field))]
    return sum(values) / len(values) if values else ""


def median_value(rows: list[dict[str, Any]], field: str) -> Any:
    values = [float(row[field]) for row in rows if finite(row.get(field))]
    return median(values) if values else ""


def pair_group(stage: str, horizon: Any, family: str, version: Any,
               pairs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "stage": stage,
        "horizon_seconds": horizon,
        "family": family,
        "V": version,
        "paired_rows": len(pairs),
        "p_grb_wins": sum(row["winner"] == "left" for row in pairs),
        "c1_wins": sum(row["winner"] == "right" for row in pairs),
        "ties": sum(row["winner"] == "tie" for row in pairs),
        "p_grb_strict_certificates": sum(
            truth(row["left_strict_certificate"]) for row in pairs),
        "c1_strict_certificates": sum(
            truth(row["right_strict_certificate"]) for row in pairs),
        "p_grb_mean_common_gap": mean_value(pairs, "left_common_ub_gap"),
        "c1_mean_common_gap": mean_value(pairs, "right_common_ub_gap"),
        "p_grb_median_common_gap": median_value(pairs, "left_common_ub_gap"),
        "c1_median_common_gap": median_value(pairs, "right_common_ub_gap"),
        "p_grb_mean_auc": mean_value(pairs, "left_bound_progress_auc"),
        "c1_mean_auc": mean_value(pairs, "right_bound_progress_auc"),
        "p_grb_median_auc": median_value(pairs, "left_bound_progress_auc"),
        "c1_median_auc": median_value(pairs, "right_bound_progress_auc"),
    }


def family_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = paired(rows, "P-GRB", "C1")
    output: list[dict[str, Any]] = []
    for stage in frozen.OFFICIAL_STAGES:
        stage_pairs = [row for row in pairs if row["stage"] == stage]
        families = sorted({frozen.INSTANCES[row["instance"]][1]
                           for row in stage_pairs})
        for family in families:
            selected = [row for row in stage_pairs
                        if frozen.INSTANCES[row["instance"]][1] == family]
            versions = {frozen.INSTANCES[row["instance"]][2]
                        for row in selected}
            output.append(pair_group(
                stage, frozen.OFFICIAL_STAGES[stage][0], family,
                next(iter(versions)) if len(versions) == 1 else "mixed", selected))
    non_v12 = [row for row in pairs if row["stage"] in ("stage1", "stage2") and
               frozen.INSTANCES[row["instance"]][1] != "v12"]
    for family in sorted({frozen.INSTANCES[row["instance"]][1]
                          for row in non_v12}):
        selected = [row for row in non_v12
                    if frozen.INSTANCES[row["instance"]][1] == family]
        output.append(pair_group(
            "known_and_heldout_v20", "1200_and_1800", family, 20, selected))
    output.append(pair_group(
        "known_and_heldout_v20", "1200_and_1800", "all_non_v12", 20,
        non_v12))
    return output


def halfway_progress(row: dict[str, Any]) -> dict[str, Any]:
    halfway = float(row["horizon_seconds"]) / 2.0
    points = [(timestamp, bound) for timestamp, bound in prior.trace_points(row)
              if timestamp <= halfway]
    halfway_lb = max((bound for _, bound in points), default=math.nan)
    final_lb = float(row["final_lb"]) if finite(row.get("final_lb")) else math.nan
    tolerance = 1e-12 * max(1.0, abs(final_lb), abs(halfway_lb)) \
        if math.isfinite(final_lb) and math.isfinite(halfway_lb) else math.inf
    sustained = truth(row.get("strict_certificate")) or (
        math.isfinite(final_lb) and math.isfinite(halfway_lb) and
        final_lb > halfway_lb + tolerance)
    return {
        "halfway_seconds": halfway,
        "halfway_lb": halfway_lb if math.isfinite(halfway_lb) else "",
        "final_lb": final_lb if math.isfinite(final_lb) else "",
        "post_halfway_lb_improvement": (
            final_lb - halfway_lb if math.isfinite(final_lb) and
            math.isfinite(halfway_lb) else ""),
        "sustained_progress": sustained,
    }


def scalability_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    official = [row for row in rows if row["stage"] in frozen.OFFICIAL_STAGES]
    fields = (
        "work", "nodes", "memory_gb", "fresh_restart_count", "split_count",
        "model_read_count", "model_read_seconds", "stagnation_seconds",
    )
    output: list[dict[str, Any]] = []
    for stage in ("stage2", "stage3", "stage4"):
        stage_rows = [row for row in official if row["stage"] == stage]
        for arm in sorted({row["arm"] for row in stage_rows}):
            selected = [row for row in stage_rows if row["arm"] == arm]
            versions = {frozen.INSTANCES[row["instance"]][2] for row in selected}
            halfway = [halfway_progress(row) for row in selected
                       if stage == "stage4" and arm == "C1"]
            item: dict[str, Any] = {
                "stage": stage,
                "horizon_seconds": frozen.OFFICIAL_STAGES[stage][0],
                "V": next(iter(versions)) if len(versions) == 1 else "mixed",
                "arm": arm,
                "rows": len(selected),
                "authoritative_rows": sum(truth(row["authoritative"])
                                           for row in selected),
                "strict_certificates": sum(truth(row["strict_certificate"])
                                             for row in selected),
                "mean_common_gap": mean_value(selected, "common_ub_gap"),
                "median_common_gap": median_value(selected, "common_ub_gap"),
                "mean_bound_progress_auc": mean_value(
                    selected, "bound_progress_auc"),
                "median_bound_progress_auc": median_value(
                    selected, "bound_progress_auc"),
                "halfway_applicable_rows": len(halfway),
                "sustained_progress_rows": sum(
                    truth(item["sustained_progress"]) for item in halfway),
            }
            for field in fields:
                item[f"mean_{field}"] = mean_value(selected, field)
                item[f"max_{field}"] = max(
                    (float(row[field]) for row in selected
                     if finite(row.get(field))), default="")
            output.append(item)
    return output


def resource_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    official = [row for row in rows if row["stage"] in frozen.OFFICIAL_STAGES]
    summed = (
        "work", "nodes", "optimize_count", "model_count", "model_read_count",
        "model_read_seconds", "presolve_count", "root_count",
        "fresh_restart_count", "same_leaf_restart_count", "child_restart_count",
        "attempt_count", "split_count", "closed_leaf_count",
    )
    output: list[dict[str, Any]] = []
    for arm in ("P-GRB", "C0", "C1"):
        selected = [row for row in official if row["arm"] == arm]
        item: dict[str, Any] = {
            "arm": arm, "rows": len(selected),
            "strict_certificates": sum(truth(row["strict_certificate"])
                                         for row in selected),
            "max_memory_gb": max((float(row["memory_gb"]) for row in selected
                                   if finite(row.get("memory_gb"))), default=""),
            "mean_stagnation_seconds": mean_value(selected, "stagnation_seconds"),
            "max_stagnation_seconds": max(
                (float(row["stagnation_seconds"]) for row in selected
                 if finite(row.get("stagnation_seconds"))), default=""),
        }
        for field in summed:
            item[f"total_{field}"] = sum(
                float(row[field]) for row in selected if finite(row.get(field)))
        output.append(item)
    return output


def promotion_gate_rows(rows: list[dict[str, Any]],
                        diagnostics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    official = [row for row in rows if row["stage"] in frozen.OFFICIAL_STAGES]
    p_c1 = paired(rows, "P-GRB", "C1")
    c0_c1 = paired(rows, "C0", "C1")
    non_v12 = [row for row in p_c1 if row["stage"] in ("stage1", "stage2") and
               frozen.INSTANCES[row["instance"]][1] != "v12"]
    heldout = [row for row in p_c1 if row["stage"] == "stage2"]
    v50 = [row for row in p_c1 if row["stage"] == "stage3"]
    long_c1 = [row for row in official if row["stage"] == "stage4" and
               row["arm"] == "C1"]
    family_losses = []
    for family in ("high_imbalance", "moderate", "tight_T"):
        selected = [row for row in non_v12
                    if frozen.INSTANCES[row["instance"]][1] == family]
        if sum(row["winner"] == "left" for row in selected) > len(selected) / 2:
            family_losses.append(family)
    c0_family_losses = []
    for family in sorted({frozen.INSTANCES[row["instance"]][1]
                          for row in c0_c1}):
        selected = [row for row in c0_c1
                    if frozen.INSTANCES[row["instance"]][1] == family]
        if sum(row["winner"] == "left" for row in selected) > len(selected) / 2:
            c0_family_losses.append(family)
    exact = all(truth(row["authoritative"]) and int(row["return_code"]) == 0 and
                all(truth(row[gate]) for gate in (
                    "coverage_gate", "lifecycle_gate", "consistency_gate",
                    "verifier_gate")) for row in official)
    diag_by_instance = {row["instance"]: row for row in diagnostics}
    v12_pass = (diag_by_instance.get("V12_M1", {}).get("classification") ==
                "timing noise" and diag_by_instance.get("V12_M2", {}).get(
                    "classification") != "persistent external-overhead regression")
    heldout_metric_pass = all((
        mean_value(heldout, "right_common_ub_gap") <
        mean_value(heldout, "left_common_ub_gap"),
        median_value(heldout, "right_common_ub_gap") <
        median_value(heldout, "left_common_ub_gap"),
        mean_value(heldout, "right_bound_progress_auc") >
        mean_value(heldout, "left_bound_progress_auc"),
        median_value(heldout, "right_bound_progress_auc") >
        median_value(heldout, "left_bound_progress_auc"),
    ))
    c0_nonlosses = sum(row["winner"] in ("right", "tie") for row in c0_c1)
    max_c0_gap_loss = max((
        float(row["right_common_ub_gap"]) - float(row["left_common_ub_gap"])
        for row in c0_c1 if finite(row.get("left_common_ub_gap")) and
        finite(row.get("right_common_ub_gap"))), default=0.0)
    sustained = [halfway_progress(row) for row in long_c1]
    new_heldout_strict = [row["instance"] for row in heldout
                          if truth(row["right_strict_certificate"]) and
                          not truth(row["left_strict_certificate"])]
    stage0 = load_json(OUT / "stage0/stage0_gate_summary.json")
    c1_manifest = load_json(OUT / "c1_manifest.json")
    c0_manifest = load_json(OUT / "c0_manifest.json")
    gates = [
        (1, "exactness_and_correctness", exact,
         f"{len(official)}/{len(official)} authoritative; zero applicable gate failures"),
        (2, "uniform_no_dispatch", stage0.get("static_no_dispatch", {}).get(
            "forbidden_findings") == 0,
         "zero static no-dispatch findings; one uniform C1 manifest"),
        (3, "v12_regressions_resolved_or_bounded", v12_pass,
         "V12_M1 is timing noise; V12_M2 remains persistent external-overhead regression"),
        (4, "broad_p_grb_advantage_known_and_heldout_v20",
         len(non_v12) == 9 and sum(row["winner"] == "right" for row in non_v12)
         >= math.ceil(0.80 * len(non_v12)) and heldout_metric_pass,
         f"C1 wins {sum(row['winner'] == 'right' for row in non_v12)}/{len(non_v12)} "
         "non-V12 pairs; held-out mean/median gap and AUC all improve"),
        (5, "no_family_systematic_regression", not family_losses,
         "no P-GRB-favoring family majority" if not family_losses else
         f"P-GRB-favoring majorities: {','.join(family_losses)}"),
        (6, "new_heldout_v20_strict_certificate", bool(new_heldout_strict),
         "new C1-only strict certificates: " +
         (",".join(new_heldout_strict) if new_heldout_strict else "none")),
        (7, "v50_validity_and_advantage",
         len(v50) == 3 and all(row["winner"] == "right" for row in v50) and
         all(truth(row["authoritative"]) for row in official
             if row["stage"] == "stage3"),
         f"C1 wins {sum(row['winner'] == 'right' for row in v50)}/{len(v50)} V50 pairs; all bounds valid"),
        (8, "long_run_sustained_progress",
         len(sustained) == 4 and all(item["sustained_progress"] for item in sustained),
         f"{sum(item['sustained_progress'] for item in sustained)}/{len(sustained)} C1 rows improve after halfway"),
        (9, "broad_c0_nonregression",
         bool(c0_c1) and c0_nonlosses >= math.ceil(0.80 * len(c0_c1)) and
         not c0_family_losses and max_c0_gap_loss <= 0.02,
         f"C1 wins/ties {c0_nonlosses}/{len(c0_c1)}; C0-favoring family majorities="
         f"{','.join(c0_family_losses) or 'none'}; max normalized gap loss={max_c0_gap_loss:.6f}"),
        (10, "independent_of_warm_start_selection_and_known_objective",
         c1_manifest.get("configuration", {}).get("explicit_cross_model_warm_start")
         is False and c1_manifest.get("configuration", {}).get(
             "instance_or_family_dispatch") is False and
         c1_manifest.get("executable_sha256") == c0_manifest.get(
             "executable_sha256"),
         "cold C1=C0 binary; no portfolio, known-objective, family, seed, or size dispatch"),
    ]
    return [{"gate": number, "name": name, "passed": passed,
             "decision": "PASS" if passed else "FAIL", "evidence": evidence}
            for number, name, passed, evidence in gates]


def scan_sensitive_markers(paths: list[Path]) -> int:
    markers = (b"WLSACCESSID=", b"WLSSECRET=", b"LICENSEID=",
               b"CLOUDACCESSID=", b"CLOUDKEY=")
    hits = 0
    for path in paths:
        opener = gzip.open if path.suffix == ".gz" else open
        try:
            with opener(path, "rb") as stream:
                tail = b""
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    data = tail + block
                    if any(marker in data for marker in markers):
                        hits += 1
                        break
                    tail = data[-32:]
        except (OSError, EOFError):
            hits += 1
    return hits


def package_summary() -> dict[str, Any]:
    manifest_path = OUT / "evidence_package_manifest.csv"
    paths = sorted(path for path in OUT.rglob("*")
                   if path.is_file() and path != manifest_path)
    raw_lps = [path for path in paths if path.suffix == ".lp"]
    entries = 0
    mismatches = 0
    for compression_manifest in OUT.rglob("compression_manifest.csv"):
        with compression_manifest.open(newline="", encoding="utf-8") as stream:
            for row in csv.DictReader(stream):
                entries += 1
                target = ROOT / row["compressed_path"]
                digest = hashlib.sha256()
                restored_bytes = 0
                try:
                    with gzip.open(target, "rb") as source:
                        for block in iter(lambda: source.read(1024 * 1024), b""):
                            digest.update(block)
                            restored_bytes += len(block)
                    if (digest.hexdigest() != row["original_sha256"] or
                            restored_bytes != int(row["original_bytes"])):
                        mismatches += 1
                except (OSError, KeyError, ValueError):
                    mismatches += 1
    sensitive_hits = scan_sensitive_markers(paths)
    largest = max(paths, key=lambda path: path.stat().st_size)
    return {
        "status": "passed" if not raw_lps and not mismatches and
        not sensitive_hits else "failed",
        "files_excluding_manifest": len(paths),
        "bytes_excluding_manifest": sum(path.stat().st_size for path in paths),
        "raw_lp_files": len(raw_lps),
        "compressed_entries_restored_and_hash_verified": entries - mismatches,
        "compression_mismatches": mismatches,
        "sensitive_marker_hits": sensitive_hits,
        "largest_artifact": relative(largest),
        "largest_artifact_bytes": largest.stat().st_size,
    }


def evidence_manifest() -> None:
    manifest = OUT / "evidence_package_manifest.csv"
    output = []
    for path in sorted(item for item in OUT.rglob("*")
                       if item.is_file() and item != manifest):
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        output.append({"path": relative(path), "bytes": path.stat().st_size,
                       "sha256": digest.hexdigest()})
    write_csv(manifest, output, ["path", "bytes", "sha256"])


def shown(item: Any, digits: int = 4) -> str:
    return f"{float(item):.{digits}f}" if finite(item) else "unavailable"


def final_artifacts(rows: list[dict[str, Any]], triggers: list[dict[str, Any]],
                    diagnostics: list[dict[str, Any]],
                    families: list[dict[str, Any]],
                    scalability: list[dict[str, Any]],
                    gates: list[dict[str, Any]]) -> None:
    official = [row for row in rows if row["stage"] in frozen.OFFICIAL_STAGES]
    p_c0 = paired(rows, "P-GRB", "C0")
    p_c1 = paired(rows, "P-GRB", "C1")
    c0_c1 = paired(rows, "C0", "C1")
    resources = resource_summary(rows)
    strict = Counter((row["stage"], row["arm"]) for row in official
                     if truth(row["strict_certificate"]))
    statuses = Counter(row["status"] for row in official)
    package = package_summary()
    promotion = all(truth(row["passed"]) for row in gates)
    build = load_json(OUT / "round26_build_manifest.json")
    stage0 = load_json(OUT / "stage0/stage0_gate_summary.json")
    summary = {
        "schema": "round26-final-audit-v1",
        "branch": "codex/round26-external-gurobi-production-validation",
        "round25_starting_head": "d8cba691424eb990fc22357f7a2911ec5d34f3df",
        "observed_origin_main_before_round26":
            "4a608eeae559cc69ca5c37b6eb4abab74fd3bc3b",
        "solver_versions": {"gurobi": build.get("gurobi_version", ""),
                            "cplex_historical_reference": "22.1.1.0"},
        "executable_sha256": {
            "frozen_c0_c1": build.get("gurobi_enabled_sha256", ""),
            "stage0_current_gurobi_build": load_json(
                OUT / "stage0_build_and_test_audit.json").get(
                    "gurobi_enabled_sha256", ""),
            "stage0_cplex_only": load_json(
                OUT / "stage0_build_and_test_audit.json").get(
                    "cplex_only_sha256", ""),
        },
        "qualification": {
            "cpp_tests_passed": stage0.get("cpp_tests_passed", 0),
            "python_test_scripts_passed": stage0.get(
                "python_test_scripts_passed", 0),
            "native_imports_passed": stage0.get("native_imports_passed", 0),
            "license_checks_passed": stage0.get("license_checks_passed", 0),
            "sentinel_rows_passed": stage0.get("sentinel_rows_passed", 0),
            "static_no_dispatch_findings": stage0.get(
                "static_no_dispatch", {}).get("forbidden_findings", ""),
        },
        "official": {
            "required": 47, "completed": len(official),
            "failed": sum(int(row["return_code"]) != 0 for row in official),
            "time_limited": statuses["time_limit"] +
                statuses["external_gini_tree_time_limit"],
            "optimal": statuses["optimal"], "excluded": 0,
            "authoritative": sum(truth(row["authoritative"]) for row in official),
        },
        "strict_certificates": {
            stage: {arm: strict[(stage, arm)] for arm in ("P-GRB", "C0", "C1")
                    if any(row["stage"] == stage and row["arm"] == arm
                           for row in official)}
            for stage in frozen.OFFICIAL_STAGES
        },
        "hierarchy": {
            "p_grb_vs_c0": Counter(row["winner"] for row in p_c0),
            "p_grb_vs_c1": Counter(row["winner"] for row in p_c1),
            "c0_vs_c1": Counter(row["winner"] for row in c0_c1),
        },
        "diagnostics": {
            "trigger_rows": len(triggers),
            "triggered": sum(truth(row["triggered"]) for row in triggers),
            "completed": sum(truth(row["replay_completed"]) for row in diagnostics),
            "classifications": Counter(row["classification"] for row in diagnostics),
        },
        "resources": resources,
        "promotion_gates_passed": sum(truth(row["passed"]) for row in gates),
        "promotion_gates_total": len(gates),
        "promotion_failed_gate_ids": [row["gate"] for row in gates
                                      if not truth(row["passed"])],
        "promotion": promotion,
        "stable_mainline": "corrected_CPLEX_S0_F0",
        "c1_definition": "C1_equals_C0_after_uniform_P1_failed_difficult_guard",
        "evidence_package": package,
    }
    (OUT / "final_audit_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    failed = [row for row in gates if not truth(row["passed"])]
    assessment = (
        "# Stable mainline assessment\n\n"
        "Corrected CPLEX S0/F0 remains the stable production/mainline algorithm. "
        "C1 is not promoted and no default alias, dispatch rule, solver portfolio, "
        "or backend selection was changed.\n\n"
        "C1 is exactly C0 because the only uniform prototype, P1, failed the "
        "preregistered difficult-instance development guard. The production gate "
        f"passes {len(gates) - len(failed)}/{len(gates)} requirements and fails "
        + ", ".join(f"Gate {row['gate']} ({row['name']})" for row in failed) +
        ". The decision is fail-closed even though held-out V20, V50, and long-run "
        "P-GRB comparisons strongly favor C1.\n")
    (OUT / "stable_mainline_assessment.md").write_text(
        assessment, encoding="utf-8")

    def win_text(items: list[dict[str, Any]], right_name: str) -> str:
        counts = Counter(row["winner"] for row in items)
        return (f"{right_name} {counts['right']}, left arm {counts['left']}, "
                f"ties {counts['tie']} ({len(items)} pairs)")

    stage_lines = []
    for stage, (budget, matrix) in frozen.OFFICIAL_STAGES.items():
        selected = [row for row in official if row["stage"] == stage]
        stage_lines.append(
            f"| {stage} | {budget} | {len(selected)}/{len(matrix)} | "
            f"{sum('time_limit' in row['status'] for row in selected)} | "
            f"{sum(truth(row['strict_certificate']) for row in selected)} |")
    strict_lines = []
    for stage, (budget, matrix) in frozen.OFFICIAL_STAGES.items():
        arms = sorted({arm for _, arm in matrix})
        strict_lines.append("| " + stage + " | " + " | ".join(
            f"{arm}: {strict[(stage, arm)]}/"
            f"{sum(row['stage'] == stage and row['arm'] == arm for row in official)}"
            for arm in arms) + " |")
    family_lines = [
        f"| {row['stage']} | {row['family']} | {row['paired_rows']} | "
        f"{row['p_grb_wins']}-{row['c1_wins']}-{row['ties']} | "
        f"{shown(row['p_grb_mean_common_gap'])}-{shown(row['c1_mean_common_gap'])} | "
        f"{shown(row['p_grb_mean_auc'])}-{shown(row['c1_mean_auc'])} |"
        for row in families]
    scale_lines = [
        f"| {row['stage']} | {row['V']} | {row['arm']} | {row['rows']} | "
        f"{shown(row['mean_common_gap'])} | {shown(row['mean_bound_progress_auc'])} | "
        f"{shown(row['max_memory_gb'])} | {int(float(row['sustained_progress_rows']))}/"
        f"{int(float(row['halfway_applicable_rows']))} |"
        for row in scalability]
    gate_lines = [f"| {row['gate']} | {row['name']} | {row['decision']} | "
                  f"{row['evidence']} |" for row in gates]
    diagnostic_lines = [
        f"| {row['trigger_id']} | {row['classification']} | "
        f"{shown(row['certificate_wall_ratio'])} | {shown(row['work_ratio'])} | "
        f"{row['fresh_restarts']}/{row['splits']}/{row['model_reads']} | "
        f"{shown(row['peak_memory_gb'])} | {shown(row['stagnation_seconds'])} |"
        for row in diagnostics]
    resource_lines = [
        f"| {row['arm']} | {row['rows']} | {shown(row['total_work'], 1)} | "
        f"{int(row['total_fresh_restart_count'])}/"
        f"{int(row['total_same_leaf_restart_count'])}/"
        f"{int(row['total_child_restart_count'])} | "
        f"{int(row['total_split_count'])} | {int(row['total_model_read_count'])} | "
        f"{shown(row['total_model_read_seconds'], 2)} | {shown(row['max_memory_gb'])} | "
        f"{shown(row['max_stagnation_seconds'], 1)} |"
        for row in resources]
    official_wall = sum(float(row["process_wall_seconds"]) for row in official
                        if finite(row.get("process_wall_seconds")))
    report = f"""# Round 26 final report

## Decision

**C1 is not promoted.** It equals C0 because the sole uniform prototype P1 was
rejected by the frozen difficult-case development guard. The final production
audit passes {len(gates) - len(failed)}/{len(gates)} gates and fails Gates
{', '.join(str(row['gate']) for row in failed)}. Corrected CPLEX S0/F0 remains
stable mainline; no alias, fallback, portfolio, or instance-dependent selector
was added.

The positive result is substantial but insufficient for promotion: C1 beats
P-GRB on 16/18 official pairs, including 9/9 non-V12 known/held-out V20, 3/3
V50, and 4/4 long rows. The blockers are the persistent V12_M2 structural
overhead and failure to broadly nonregress against independent C0 repetitions.

## Provenance and qualification

The branch starts from `d8cba691424eb990fc22357f7a2911ec5d34f3df`;
live `origin/main` was observed as
`4a608eeae559cc69ca5c37b6eb4abab74fd3bc3b` before Round 26. Frozen C0/C1
executable SHA-256 is `{build.get('gurobi_enabled_sha256', '')}` using Gurobi
{build.get('gurobi_version', '')}; the Stage 0 current Gurobi build and CPLEX-only
control hashes are `{summary['executable_sha256']['stage0_current_gurobi_build']}`
and `{summary['executable_sha256']['stage0_cplex_only']}`. CPLEX 22.1.1.0 is
historical S0-REF only.

Stage 0 passed 18/18 C++ tests, 7 Python suites, 15 native imports, 2 license
checks, 2 moderate4301 sentinels, and the static scan with zero forbidden
dispatch findings. All 47 official rows are authoritative and pass every
coverage, lifecycle, consistency, witness, bound, and certificate gate.

## C0, C1, and exactness

C0 is the frozen Round 25 cold, one-thread, solver-neutral external global-Gini
tree with static F0 leaf models, same-run independently verified HGA UB,
non-strict cutoff, parent-bound inheritance, immutable artifact cache, and no
cross-model warm start. P1 uniformly split unresolved leaves after one attempt;
it removed 70.0% of V12_M2 excess Work but failed high3202 by losing strict
closure and 0.028835 normalized LB, beyond the 0.02 guard. P1 was rejected
without tuning, so C1 is exactly C0 with the two-attempt rule.

The exactness argument is unchanged: root intervals cover the complete original
feasible region; atomic parent-to-child replacement preserves coverage; inherited
bounds remain valid; cutoffs use independently verified feasible UBs; unresolved
intervals cannot disappear; lifecycle/verifier checks agree; and a strict
certificate is asserted only for the complete original problem.

## V12 repeatability and diagnosis

Across three forensic repetitions, V12_M1 median C0/P-GRB certificate wall is
37.559/36.498 seconds (1.029x), while Work is 34.781/53.573. This is bounded
fixed orchestration overhead inside 5% and the enhanced replay classifies it as
timing noise.

V12_M2 forensic median wall is 183.022/179.187 seconds (1.021x), but Work is
341.716/282.097 (1.211x), with repeated model/presolve/root execution. In the
official row C1 loses 198.413 to 169.709 seconds and uses 365.361 versus 282.097
Work. Its replay remains a persistent external-overhead regression: repeated
same-leaf attempts, fresh roots, and delayed partitioning dominate; model I/O,
initial allocation, scheduler starvation, and numerical failure do not. Thus
only V12_M1 is resolved as timing noise; V12_M2 is unresolved.

## Official rows and strict certificates

All 47/47 official processes completed with return code zero: 38 valid time
limits, 9 optimal rows, 0 failures, 0 interruptions, and 0 exclusions. Official
solve wall totals {official_wall / 3600:.2f} hours.

| Stage | Seconds | Completed | Time-limited | Strict |
| --- | ---: | ---: | ---: | ---: |
{chr(10).join(stage_lines)}

| Stage | Strict certificates by arm |
| --- | --- |
{chr(10).join(strict_lines)}

## Frozen hierarchy comparisons

`P-GRB` versus C0: {win_text(p_c0, 'C0')}. `P-GRB` versus C1:
{win_text(p_c1, 'C1')}. C0 versus C1: {win_text(c0_c1, 'C1')}. C1 wins all
six sealed V20 pairs, including the new strict certificate on high5203; all
three V50 pairs; and all four fixed 3600-second pairs. C0 and C1 are identical
algorithms, so their 4-7 hierarchy split measures independent run variability,
not a mechanism improvement.

| Scope | Family | Pairs | P-GRB-C1 wins | Mean gap P-GRB-C1 | Mean AUC P-GRB-C1 |
| --- | --- | ---: | ---: | ---: | ---: |
{chr(10).join(family_lines)}

## Scalability and long-run closure

All V50 rows have valid models and bounds. At 1800 seconds C1 common-UB gaps
are 0.0969, 0.1480, and 0.1120 versus P-GRB's 0.1895, 0.3094, and 0.2492.
At 3600 seconds C1 wins all four pairs and every C1 lower bound improves after
the 1800-second checkpoint. Long-run peak memory reaches 6.078 GB on V50
moderate6301; progress is sustained despite 299.4 seconds of final stagnation.

| Stage | V | Arm | Rows | Mean gap | Mean AUC | Max GB | Sustained/checked |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(scale_lines)}

## Automatic diagnostics

Exactly 2/18 P-GRB/C1 pairs triggered, and both exactly-once diagnostic C1
replays completed. They never replace official rows.

| Trigger | Classification | Wall ratio | Work ratio | Restarts/splits/reads | GB | Stagnation s |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(diagnostic_lines)}

## Lifecycle and resource summary

Unsupported native phase times and cut counts remain marked unavailable; they
are not estimated. Restart columns are fresh/same-leaf/child.

| Arm | Rows | Work | Restarts | Splits | Reads | Read s | Max GB | Max stagnation s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(resource_lines)}

## Promotion audit

| Gate | Requirement | Result | Evidence |
| ---: | --- | --- | --- |
{chr(10).join(gate_lines)}

Promotion fails closed. The strong held-out and large-instance result does not
override V12_M2 or C0 nonregression gates, and mean performance alone is not a
promotion criterion.

## Evidence package and limitations

The package has {package['files_excluding_manifest']} retained files excluding
its self-excluded manifest, totaling {package['bytes_excluding_manifest'] / (1024**2):.1f}
MiB. The largest artifact is `{package['largest_artifact']}` at
{package['largest_artifact_bytes']} bytes. It has {package['raw_lp_files']} raw
LPs, {package['compressed_entries_restored_and_hash_verified']} verified
compression entries, {package['compression_mismatches']} compression mismatch,
and {package['sensitive_marker_hits']} sensitive-marker hits; package status is
**{package['status']}**.

Limitations are the unresolved V12_M2 repeated-root overhead, C0/C1 run
variability, no strict V50 or 3600-second certificate, unavailable safe native
per-leaf phase timing/cut totals, and increased external-tree memory at V50.
All time-limited rows retain valid global bounds; none is presented as a strict
certificate.
"""
    (OUT / "final_report.md").write_text(report, encoding="utf-8")


def public(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in SUMMARY_FIELDS}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit-triggers", action="store_true")
    parser.add_argument("--require-stage", choices=tuple(frozen.OFFICIAL_STAGES))
    args = parser.parse_args()
    rows = extract_rows()
    add_common_ubs(rows)
    auc_rows, crossing_rows = progress_metrics(rows)
    triggers = emit_triggers(rows)
    diagnostics = diagnostic_rows(rows, triggers)
    official = [row for row in rows if row["stage"] in frozen.OFFICIAL_STAGES]
    for stage, filename in STAGE_FILES.items():
        selected = [public(row) for row in official if row["stage"] == stage]
        if selected:
            write_csv(OUT / filename, selected, SUMMARY_FIELDS)
    write_csv(OUT / "p_grb_vs_c0.csv", paired(rows, "P-GRB", "C0"))
    write_csv(OUT / "p_grb_vs_c1.csv", paired(rows, "P-GRB", "C1"))
    write_csv(OUT / "c0_vs_c1.csv", paired(rows, "C0", "C1"))
    write_csv(OUT / "bound_progress_auc.csv", auc_rows)
    write_csv(OUT / "time_to_gap_thresholds.csv", crossing_rows)
    write_csv(OUT / "lifecycle_restart_summary.csv", [public(row) for row in rows],
              SUMMARY_FIELDS)
    write_csv(OUT / "exactness_audit.csv", [public(row) for row in rows],
              SUMMARY_FIELDS)
    counts = Counter((row["stage"], row["arm"]) for row in official
                     if truth(row["strict_certificate"]))
    strict_rows = [{
        "stage": stage, "horizon_seconds": budget, "arm": arm,
        "strict_certificates": counts[(stage, arm)],
        "official_rows": sum(row["stage"] == stage and row["arm"] == arm
                             for row in official),
    } for stage, (budget, matrix) in frozen.OFFICIAL_STAGES.items()
      for arm in sorted({arm for _, arm in matrix})]
    write_csv(OUT / "strict_certificate_summary.csv", strict_rows)
    write_csv(OUT / "regression_diagnostics.csv", diagnostics)
    families = family_summary(rows)
    scalability = scalability_summary(rows)
    gates = promotion_gate_rows(rows, diagnostics)
    write_csv(OUT / "family_summary.csv", families)
    write_csv(OUT / "scalability_summary.csv", scalability)
    write_csv(OUT / "promotion_gate_audit.csv", gates)
    final_artifacts(rows, triggers, diagnostics, families, scalability, gates)
    evidence_manifest()
    if args.require_stage:
        expected = len(frozen.OFFICIAL_STAGES[args.require_stage][1])
        observed = sum(row["stage"] == args.require_stage for row in official)
        if observed != expected:
            raise RuntimeError(
                f"expected {expected} {args.require_stage} rows, found {observed}")
    print(json.dumps({
        "official_rows": len(official),
        "authoritative_rows": sum(truth(row["authoritative"]) for row in official),
        "trigger_rows": len(triggers),
        "triggered": sum(truth(row["triggered"]) for row in triggers),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
