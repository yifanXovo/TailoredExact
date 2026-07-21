#!/usr/bin/env python3
"""Incremental and final analysis for the frozen Round 26 experiment matrix."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from pathlib import Path
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
                   if row["arm"] in (left_arm, right_arm)})
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
