#!/usr/bin/env python3
"""Analyze frozen Round 31 results from observed bound events only."""

from __future__ import annotations

import csv
import gzip
import json
import math
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, TextIO

import round30_bound_trace as bound_trace


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_nonblocking_gurobi_c6_round31"
RUNS = OUT / "runs"
TOL = 1e-7


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


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
    return str(value).strip().lower() in {"true", "1", "yes"}


def open_text(path: Path) -> TextIO:
    return (
        gzip.open(path, "rt", encoding="utf-8", newline="")
        if path.suffix.lower() == ".gz"
        else path.open("r", encoding="utf-8", newline=""))


def csv_rows(path: Path) -> list[dict[str, str]]:
    candidate = path
    if not candidate.is_file() and Path(str(path) + ".gz").is_file():
        candidate = Path(str(path) + ".gz")
    if not candidate.is_file():
        return []
    with open_text(candidate) as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: Iterable[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    material = list(rows)
    columns = fields or []
    if not columns:
        for row in material:
            for field in row:
                if field not in columns:
                    columns.append(field)
    if not columns:
        columns = ["status"]
        material = [{"status": "no_rows"}]
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    os.replace(temporary, path)


def raw_runs() -> list[dict[str, Any]]:
    output = []
    for state_path in sorted(RUNS.glob("*/run_state.json")):
        state = load_json(state_path)
        result_path = state_path.parent / "result.json"
        output.append({
            "state": state,
            "result": load_json(result_path) if result_path.is_file() else {},
            "run_dir": state_path.parent,
        })
    return output


def result_bounds(run: dict[str, Any]) -> tuple[float, float]:
    result = run["result"]
    if run["state"]["arm"] in {"C5-CANDIDATE", "C6-CANDIDATE"}:
        return (
            number(result.get(
                "external_gini_tree_global_lower_bound",
                result.get("lower_bound"))),
            number(result.get(
                "external_gini_tree_verified_upper_bound",
                result.get("upper_bound"))),
        )
    return number(result.get("lower_bound")), number(result.get("upper_bound"))


def phase_time(run: dict[str, Any], event: str) -> float:
    for row in csv_rows(run["run_dir"] / "process_phases.csv"):
        if row.get("event") == event:
            return number(row.get("process_seconds"), 0.0)
    return 0.0


def trace_for(run: dict[str, Any]) -> tuple[
        bool, str, tuple[bound_trace.BoundObservation, ...]]:
    arm = run["state"]["arm"]
    if arm in {"C5-CANDIDATE", "C6-CANDIDATE"}:
        audit = bound_trace.audit_external_trace(
            run["run_dir"] / "external/global_bound_trace.csv")
        return audit.complete, audit.reason, audit.observations
    if arm in {"P-GRB", "P-GRB-HGA"}:
        rows = csv_rows(run["run_dir"] / "progress.csv")
        launch = phase_time(run, "plain_gurobi_optimize_launch")
        observations = []
        last = -math.inf
        for row in rows:
            if not truth(row.get("best_bound_available")):
                continue
            value = number(row.get("best_bound"))
            elapsed = number(row.get("elapsed_runtime_seconds"))
            if not math.isfinite(value) or not math.isfinite(elapsed) or (
                    abs(value) >= 1e50):
                continue
            if value + TOL < last:
                return False, "plain_callback_bound_nonmonotone", ()
            last = max(last, value)
            observations.append(bound_trace.BoundObservation(
                launch + elapsed, elapsed, "native_progress_callback",
                last, number(row.get("incumbent")),
                integer(row.get("open_nodes")), 0, last, None,
                "gurobi_cb_mip_objbnd"))
        return (
            len(observations) >= 2,
            "complete_native_callback_trace"
            if len(observations) >= 2 else
            "too_few_native_callback_bounds",
            tuple(observations),
        )
    return False, "auc_not_required_for_s0_anchor", ()


def value_at(observations: tuple[bound_trace.BoundObservation, ...],
             when: float) -> float:
    value = observations[0].global_lower_bound
    for row in observations:
        if row.process_seconds > when + 1e-12:
            break
        value = row.global_lower_bound
    return value


def pair_auc(
        left: tuple[bound_trace.BoundObservation, ...],
        right: tuple[bound_trace.BoundObservation, ...],
        upper: float) -> dict[str, Any]:
    start = max(left[0].process_seconds, right[0].process_seconds)
    end = min(left[-1].process_seconds, right[-1].process_seconds)
    if end <= start:
        return {
            "auc_status": "auc_unavailable",
            "auc_reason": "no_positive_common_observed_window",
        }
    times = sorted({
        start, end,
        *(row.process_seconds for row in left
          if start < row.process_seconds < end),
        *(row.process_seconds for row in right
          if start < row.process_seconds < end),
    })
    denominator = max(abs(upper), 1e-12)
    areas = [0.0, 0.0]
    lb_areas = [0.0, 0.0]
    for begin, finish in zip(times, times[1:]):
        duration = finish - begin
        for index, trace in enumerate((left, right)):
            value = value_at(trace, begin)
            lb_areas[index] += duration * value
            areas[index] += duration * max(
                0.0, min(1.0, 1.0 - (upper - value) / denominator))
    duration = end - start
    return {
        "auc_status": "observed_common_window",
        "auc_reason": "no_interpolation_no_post_last_event_extension",
        "common_window_start_process_seconds": start,
        "common_window_end_process_seconds": end,
        "common_window_duration_seconds": duration,
        "left_mean_valid_lower_bound": lb_areas[0] / duration,
        "right_mean_valid_lower_bound": lb_areas[1] / duration,
        "left_normalized_proof_auc": areas[0] / duration,
        "right_normalized_proof_auc": areas[1] / duration,
        "normalized_proof_auc_delta_right_minus_left":
            (areas[1] - areas[0]) / duration,
    }


def common_upper_bounds(runs: list[dict[str, Any]]) -> dict[str, float]:
    values: dict[str, list[float]] = defaultdict(list)
    for run in runs:
        _, upper = result_bounds(run)
        if math.isfinite(upper):
            values[run["state"]["instance"]].append(upper)
    return {name: min(found) for name, found in values.items()}


def public_row(run: dict[str, Any], upper: float) -> dict[str, Any]:
    state, result = run["state"], run["result"]
    lower, verified_upper = result_bounds(run)
    gap = (
        max(0.0, (upper - lower) / max(abs(upper), 1e-12))
        if math.isfinite(lower) and math.isfinite(upper) else math.nan)
    return {
        "stage": state["stage"],
        "instance": state["instance"],
        "family": state["family"],
        "V": state["V"],
        "M": state["M"],
        "sealed_heldout": state["sealed_heldout"],
        "arm": state["arm"],
        "repetition": state["repetition"],
        "budget_seconds": state["budget_seconds"],
        "return_code": state["return_code"],
        "emergency_timeout": state["emergency_timeout"],
        "status": result.get("status", "result_missing"),
        "valid_final_lb": lower,
        "verified_ub": verified_upper,
        "common_verified_ub": upper,
        "common_ub_gap": gap,
        "strict_certificate":
            truth(result.get("strict_certified_original_problem")),
        "runtime_seconds": number(result.get("runtime_seconds")),
        "graceful_deadline_finalization":
            truth(result.get("graceful_deadline_finalization")),
        "failure_reason": result.get(
            "external_gini_tree_failure_reason",
            result.get("gurobi_failure_reason", "none")),
        "run_id": state["run_id"],
        "run_path": run["run_dir"].relative_to(ROOT).as_posix(),
    }


def stage_runs(runs: list[dict[str, Any]], stage: int) -> list[dict[str, Any]]:
    return [run for run in runs if integer(run["state"]["stage"]) == stage]


def pairs(stage: list[dict[str, Any]], left_arm: str, right_arm: str,
          upper: dict[str, float],
          traces: dict[str, tuple[
              bool, str, tuple[bound_trace.BoundObservation, ...]]]
          ) -> list[dict[str, Any]]:
    keyed = {
        (run["state"]["instance"], run["state"]["arm"],
         integer(run["state"]["repetition"])): run
        for run in stage
    }
    output = []
    instances = sorted({
        name for name, arm, repetition in keyed
        if arm == left_arm and repetition == 0 and
        (name, right_arm, 0) in keyed
    })
    for name in instances:
        left = keyed[(name, left_arm, 0)]
        right = keyed[(name, right_arm, 0)]
        left_lb, _ = result_bounds(left)
        right_lb, _ = result_bounds(right)
        left_trace = traces[left["state"]["run_id"]]
        right_trace = traces[right["state"]["run_id"]]
        auc = (
            pair_auc(left_trace[2], right_trace[2], upper[name])
            if left_trace[0] and right_trace[0] else {
                "auc_status": "auc_unavailable",
                "auc_reason":
                    f"left={left_trace[1]};right={right_trace[1]}",
            })
        output.append({
            "instance": name,
            "family": left["state"]["family"],
            "V": left["state"]["V"],
            "left_arm": left_arm,
            "right_arm": right_arm,
            "common_verified_ub": upper[name],
            "left_final_lb": left_lb,
            "right_final_lb": right_lb,
            "final_lb_delta_right_minus_left": right_lb - left_lb,
            "left_common_gap":
                max(0.0, (upper[name] - left_lb) /
                    max(abs(upper[name]), 1e-12)),
            "right_common_gap":
                max(0.0, (upper[name] - right_lb) /
                    max(abs(upper[name]), 1e-12)),
            "normalized_gap_delta_right_minus_left":
                (left_lb - right_lb) / max(abs(upper[name]), 1e-12),
            "left_strict_certificate": truth(left["result"].get(
                "strict_certified_original_problem")),
            "right_strict_certificate": truth(right["result"].get(
                "strict_certified_original_problem")),
            **auc,
        })
    return output


def family_summary(pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in pair_rows:
        grouped[(row["family"], integer(row["V"]))].append(row)
    output = []
    for (family, size), rows in sorted(grouped.items()):
        auc = [
            row for row in rows
            if row["auc_status"] == "observed_common_window"]
        output.append({
            "family": family,
            "V": size,
            "instances": len(rows),
            "right_final_lb_wins": sum(
                row["final_lb_delta_right_minus_left"] > TOL
                for row in rows),
            "left_final_lb_wins": sum(
                row["final_lb_delta_right_minus_left"] < -TOL
                for row in rows),
            "final_lb_ties": sum(
                abs(row["final_lb_delta_right_minus_left"]) <= TOL
                for row in rows),
            "auc_available": len(auc),
            "right_auc_wins": sum(
                row["normalized_proof_auc_delta_right_minus_left"] > TOL
                for row in auc),
            "left_auc_wins": sum(
                row["normalized_proof_auc_delta_right_minus_left"] < -TOL
                for row in auc),
            "auc_ties": sum(
                abs(row["normalized_proof_auc_delta_right_minus_left"]) <= TOL
                for row in auc),
        })
    return output


def metric(run: dict[str, Any], suffix: str, default: Any = 0) -> Any:
    return run["result"].get(f"external_gini_tree_{suffix}", default)


def mechanism_outputs(runs: list[dict[str, Any]]) -> None:
    targets = []
    next_targets = []
    terminal_rows = []
    avoidance = []
    blocking = []
    lifecycle = []
    for run in runs:
        if run["state"]["arm"] not in {
                "C5-CANDIDATE", "C6-CANDIDATE"}:
            continue
        state, result, directory = (
            run["state"], run["result"], run["run_dir"])
        for row in csv_rows(
                directory / "external/native_target_ledger.csv"):
            record = {
                "run_id": state["run_id"],
                "instance": state["instance"],
                "arm": state["arm"],
                **row,
            }
            targets.append(record)
            if row.get("target_kind") == "next_leaf":
                next_targets.append(record)
        terminal_work = 0.0
        partial_work = 0.0
        terminal_calls = 0
        for row in csv_rows(
                directory / "external/paper_optimize_ledger.csv"):
            if row.get("solve_kind") == "MIP":
                terminal_calls += 1
                terminal_work += number(row.get("work"), 0.0)
                terminal_rows.append({
                    "run_id": state["run_id"],
                    "instance": state["instance"],
                    "arm": state["arm"],
                    **row,
                })
            elif "TARGET_MIP" in str(row.get("solve_kind")):
                partial_work += number(row.get("work"), 0.0)
        avoidance.append({
            "run_id": state["run_id"],
            "instance": state["instance"],
            "arm": state["arm"],
            "parent_lp_requeues": metric(run, "parent_lp_requeue_count"),
            "child_lookaheads_avoided":
                metric(run, "child_lookahead_avoided_count"),
            "child_lookahead_reuses":
                metric(run, "child_lookahead_reuse_count"),
            "forced_splits_avoided":
                metric(run, "forced_split_avoided_count"),
            "next_leaf_target_phases":
                metric(run, "next_leaf_target_phase_count"),
            "next_leaf_targets_reached":
                metric(run, "next_leaf_target_reached_count"),
            "child_bound_target_phases":
                metric(run, "child_bound_target_phase_count"),
            "native_requeues": metric(run, "native_requeue_count"),
        })
        total_work = number(metric(run, "work"), 0.0)
        blocking.append({
            "run_id": state["run_id"],
            "instance": state["instance"],
            "family": state["family"],
            "V": state["V"],
            "arm": state["arm"],
            "terminal_mip_calls": terminal_calls,
            "terminal_mip_work_ledger": terminal_work,
            "terminal_mip_work_result":
                number(metric(run, "terminal_mip_work"), 0.0),
            "partial_target_work_ledger": partial_work,
            "total_external_work": total_work,
            "terminal_work_share": (
                terminal_work / total_work if total_work > 0 else 0.0),
            "final_stagnation_seconds":
                metric(run, "final_stagnation_seconds"),
            "lp_cutoff_prunes": metric(run, "lp_pruned_leaf_count"),
        })
        lifecycle.append({
            "run_id": state["run_id"],
            "instance": state["instance"],
            "arm": state["arm"],
            "models": metric(run, "model_count"),
            "model_frees": metric(run, "model_free_count"),
            "environments": metric(run, "environment_count"),
            "environment_frees": metric(run, "environment_free_count"),
            "optimize_calls": metric(run, "optimize_count"),
            "lp_calls": metric(run, "lp_optimize_count"),
            "partial_target_calls": metric(
                run, "partial_mip_optimize_count"),
            "terminal_calls": metric(run, "terminal_mip_optimize_count"),
            "model_reuses": metric(run, "in_memory_model_reuse_count"),
            "integer_domain_restores":
                metric(run, "integer_domain_restore_count"),
            "fresh_restarts": metric(run, "fresh_restart_count"),
            "child_restarts": metric(run, "child_restart_count"),
            "reset_calls": metric(run, "reset_call_count"),
            "lifecycle_complete": truth(metric(run, "lifecycle_complete")),
            "basis_reuse_claimed": False,
            "native_tree_continuation_claimed": False,
        })
    write_csv(OUT / "native_target_value.csv", targets)
    write_csv(OUT / "next_leaf_target_value.csv", next_targets)
    write_csv(OUT / "child_lookahead_avoidance.csv", avoidance)
    write_csv(OUT / "terminal_mip_value_audit.csv", terminal_rows)
    write_csv(OUT / "terminal_blocking_summary.csv", blocking)
    write_csv(OUT / "lifecycle_and_resource_summary.csv", lifecycle)


def repeatability(
        stage5: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keyed = {
        (run["state"]["instance"], integer(run["state"]["repetition"])): run
        for run in stage5
    }
    output = []
    for name in sorted({item[0] for item in keyed}):
        left, right = keyed[(name, 1)], keyed[(name, 2)]
        left_lb, _ = result_bounds(left)
        right_lb, _ = result_bounds(right)

        def projection(run: dict[str, Any], file: str,
                       fields: tuple[str, ...]) -> list[tuple[str, ...]]:
            return [
                tuple(row.get(field, "") for field in fields)
                for row in csv_rows(run["run_dir"] / "external" / file)
            ]

        output.append({
            "instance": name,
            "family": left["state"]["family"],
            "V": left["state"]["V"],
            "hga_trajectory_exact":
                (left["run_dir"] / "hga_generations.csv").read_bytes() ==
                (right["run_dir"] / "hga_generations.csv").read_bytes(),
            "leaf_order_exact": projection(
                left, "paper_tree_events.csv", ("event", "leaf_id")) ==
                projection(
                    right, "paper_tree_events.csv", ("event", "leaf_id")),
            "target_sequence_exact": projection(
                left, "native_target_ledger.csv",
                ("leaf_id", "target_kind", "target_bound", "status")) ==
                projection(
                    right, "native_target_ledger.csv",
                    ("leaf_id", "target_kind", "target_bound", "status")),
            "split_sequence_exact": projection(
                left, "split_decision_ledger.csv",
                ("parent_id", "split", "reason")) ==
                projection(
                    right, "split_decision_ledger.csv",
                    ("parent_id", "split", "reason")),
            "rep1_final_lb": left_lb,
            "rep2_final_lb": right_lb,
            "final_lb_absolute_delta": abs(left_lb - right_lb),
            "rep1_strict_certificate": truth(left["result"].get(
                "strict_certified_original_problem")),
            "rep2_strict_certificate": truth(right["result"].get(
                "strict_certified_original_problem")),
            "rep1_lifecycle": truth(metric(left, "lifecycle_complete")),
            "rep2_lifecycle": truth(metric(right, "lifecycle_complete")),
            "rep1_graceful_finalization": truth(
                left["result"].get("graceful_deadline_finalization")),
            "rep2_graceful_finalization": truth(
                right["result"].get("graceful_deadline_finalization")),
        })
    return output


def exactness_outputs(runs: list[dict[str, Any]]) -> tuple[bool, int]:
    exactness = []
    certificates = []
    false_count = 0
    for run in runs:
        if run["state"]["arm"] != "C6-CANDIDATE":
            continue
        result = run["result"]
        structural = all((
            truth(metric(run, "root_coverage_valid")),
            truth(metric(run, "parent_child_coverage_valid")),
            truth(metric(run, "all_leaf_bounds_valid")),
            truth(metric(run, "leaf_bounds_monotone")),
            truth(metric(run, "global_bound_monotone")),
            truth(metric(run, "lifecycle_complete")),
            truth(metric(run, "feasibility_consistency_gate")),
        ))
        lower, upper = result_bounds(run)
        strict = truth(result.get("strict_certified_original_problem"))
        all_closed = truth(metric(run, "all_relevant_leaves_closed"))
        false = strict and (
            not structural or not all_closed or
            abs(lower - upper) >
            TOL * max(1.0, abs(lower), abs(upper)))
        false_count += int(false)
        exactness.append({
            "run_id": run["state"]["run_id"],
            "instance": run["state"]["instance"],
            "stage": run["state"]["stage"],
            "structural_gate": structural,
            "open_leaf_preserved_on_deadline": (
                all_closed or integer(metric(run, "open_leaf_count")) > 0),
            "partial_status_closure_count": 0,
            "passed": structural,
        })
        certificates.append({
            "run_id": run["state"]["run_id"],
            "instance": run["state"]["instance"],
            "strict_certificate": strict,
            "all_relevant_leaves_closed": all_closed,
            "false_certificate": false,
            "certificate_class":
                result.get("strict_certificate_class"),
            "rejection_reason":
                result.get("strict_certificate_rejection_reason"),
            "passed": not false,
        })
    write_csv(OUT / "exactness_audit.csv", exactness)
    write_csv(OUT / "certificate_audit.csv", certificates)
    return (
        all(row["passed"] for row in exactness) and
        all(row["passed"] for row in certificates),
        false_count,
    )


def main() -> int:
    runs = raw_runs()
    if not runs:
        raise SystemExit("no Round 31 official runs")
    upper = common_upper_bounds(runs)
    traces = {
        run["state"]["run_id"]: trace_for(run) for run in runs
    }
    by_stage = {stage: stage_runs(runs, stage) for stage in range(1, 7)}
    stage_names = {
        1: "stage1_mechanism_anchors.csv",
        2: "stage2_existing_primary.csv",
        3: "stage3_sealed_heldout.csv",
        4: "stage4_mainline_and_incumbent_ablation.csv",
        5: "stage5_repeatability.csv",
        6: "stage6_medium_run.csv",
    }
    for stage, name in stage_names.items():
        rows = [
            public_row(run, upper[run["state"]["instance"]])
            for run in by_stage[stage]]
        if stage == 6 and not rows:
            rows = [{
                "status": "excluded_pending_or_failed_short_run_gate",
                "conditional": True,
            }]
        write_csv(OUT / name, rows)

    auc_rows = []
    threshold_rows = []
    for run in runs:
        complete, reason, observations = traces[run["state"]["run_id"]]
        row = {
            "run_id": run["state"]["run_id"],
            "stage": run["state"]["stage"],
            "instance": run["state"]["instance"],
            "family": run["state"]["family"],
            "V": run["state"]["V"],
            "arm": run["state"]["arm"],
            "trace_complete": complete,
            "trace_reason": reason,
            "bound_observations": len(observations),
            "auc_status": "observed" if complete else "auc_unavailable",
        }
        if complete:
            row.update(bound_trace.observed_step_auc(
                observations, upper[run["state"]["instance"]]))
            for threshold in (0.50, 0.25, 0.10, 0.05, 0.02, 0.01):
                reached = next((
                    point.process_seconds for point in observations
                    if (upper[run["state"]["instance"]] -
                        point.global_lower_bound) /
                       max(abs(upper[run["state"]["instance"]]), 1e-12)
                       <= threshold + 1e-12), None)
                threshold_rows.append({
                    "run_id": run["state"]["run_id"],
                    "instance": run["state"]["instance"],
                    "arm": run["state"]["arm"],
                    "common_gap_threshold": threshold,
                    "reached": reached is not None,
                    "first_observed_process_seconds":
                        reached if reached is not None else "",
                    "no_interpolation": True,
                })
        auc_rows.append(row)
    write_csv(OUT / "actual_bound_progress_auc.csv", auc_rows)
    write_csv(OUT / "time_to_gap_thresholds.csv", threshold_rows)

    p_vs_c6 = pairs(
        by_stage[2], "P-GRB", "C6-CANDIDATE", upper, traces)
    sealed_p_vs_c6 = pairs(
        by_stage[3], "P-GRB", "C6-CANDIDATE", upper, traces)
    c5_vs_c6 = (
        pairs(by_stage[1], "C5-CANDIDATE", "C6-CANDIDATE",
              upper, traces) +
        pairs(by_stage[3], "C5-CANDIDATE", "C6-CANDIDATE",
              upper, traces))
    p_hga = pairs(
        by_stage[4], "P-GRB", "P-GRB-HGA", upper, traces)
    s0 = pairs(
        by_stage[4], "S0-CPLEX", "C6-CANDIDATE", upper, traces)
    write_csv(OUT / "p_grb_vs_c6.csv", p_vs_c6)
    write_csv(OUT / "c5_vs_c6.csv", c5_vs_c6)
    write_csv(OUT / "p_grb_hga_ablation.csv", p_hga)
    write_csv(OUT / "s0_vs_c6_anchor.csv", s0)
    write_csv(OUT / "existing_family_summary.csv",
              family_summary(p_vs_c6))
    write_csv(OUT / "sealed_family_summary.csv",
              family_summary(sealed_p_vs_c6))
    mechanism_outputs(runs)
    write_csv(OUT / "stage5_repeatability_audit.csv",
              repeatability(by_stage[5]))
    exact, false_certificates = exactness_outputs(runs)

    lb_wins = sum(
        row["final_lb_delta_right_minus_left"] > TOL for row in p_vs_c6)
    lb_ties = sum(
        abs(row["final_lb_delta_right_minus_left"]) <= TOL
        for row in p_vs_c6)
    auc_available = [
        row for row in p_vs_c6
        if row["auc_status"] == "observed_common_window"]
    auc_wins = sum(
        row["normalized_proof_auc_delta_right_minus_left"] > TOL
        for row in auc_available)
    auc_ties = sum(
        abs(row["normalized_proof_auc_delta_right_minus_left"]) <= TOL
        for row in auc_available)
    sealed_lb_wins_ties = sum(
        row["final_lb_delta_right_minus_left"] >= -TOL
        for row in sealed_p_vs_c6)
    sealed_auc = [
        row for row in sealed_p_vs_c6
        if row["auc_status"] == "observed_common_window"]
    sealed_auc_wins_ties = sum(
        row["normalized_proof_auc_delta_right_minus_left"] >= -TOL
        for row in sealed_auc)
    maximum_gap_loss = max(
        (row["right_common_gap"] - row["left_common_gap"]
         for row in p_vs_c6), default=0.0)
    family = family_summary(p_vs_c6)
    no_family_p_majority = all(
        row["left_final_lb_wins"] <=
        row["right_final_lb_wins"] + row["final_lb_ties"]
        for row in family)
    v12 = [
        run for run in by_stage[2]
        if run["state"]["arm"] == "C6-CANDIDATE" and
        integer(run["state"]["V"]) == 12]
    v50_auc = [
        row for row in auc_available if integer(row["V"]) == 50]
    v50_auc_wins_ties = sum(
        row["normalized_proof_auc_delta_right_minus_left"] >= -TOL
        for row in v50_auc)
    short_gate = all((
        exact,
        false_certificates == 0,
        lb_wins + lb_ties >= 15,
        maximum_gap_loss <= 0.02 + TOL,
        no_family_p_majority,
        auc_wins + auc_ties >= 12,
        v50_auc_wins_ties > 0,
        len(v12) == 2 and all(truth(run["result"].get(
            "strict_certified_original_problem")) for run in v12),
        sealed_lb_wins_ties >= 5,
        sealed_auc_wins_ties >= 4,
    ))
    write_json(OUT / "short_run_gate.json", {
        "schema": "round31-short-run-gate-v1",
        "passed": short_gate,
        "exactness": exact,
        "false_certificates": false_certificates,
        "existing_final_lb_wins": lb_wins,
        "existing_final_lb_ties": lb_ties,
        "existing_final_lb_wins_ties": lb_wins + lb_ties,
        "maximum_normalized_gap_loss": maximum_gap_loss,
        "no_family_p_grb_majority": no_family_p_majority,
        "existing_auc_available": len(auc_available),
        "existing_auc_wins": auc_wins,
        "existing_auc_ties": auc_ties,
        "existing_auc_wins_ties": auc_wins + auc_ties,
        "v50_auc_available": len(v50_auc),
        "v50_auc_wins_ties": v50_auc_wins_ties,
        "both_v12_certified": len(v12) == 2 and all(
            truth(run["result"].get("strict_certified_original_problem"))
            for run in v12),
        "sealed_final_lb_wins_ties": sealed_lb_wins_ties,
        "sealed_auc_available": len(sealed_auc),
        "sealed_auc_wins_ties": sealed_auc_wins_ties,
    })

    process_failures = sum(
        run["state"]["return_code"] != 0 or
        not run["state"]["result_exists"] for run in runs)
    c5_pairs = [
        row for row in c5_vs_c6
        if row["instance"] in {
            item["instance"] for item in p_vs_c6}]
    c6_over_c5 = sum(
        row["final_lb_delta_right_minus_left"] > TOL
        for row in c5_pairs)
    if not exact or false_certificates:
        classification = "invalid"
    elif short_gate:
        classification = "paper_exact_and_broadly_dominant"
    elif c6_over_c5 > len(c5_pairs) / 2:
        classification = "paper_exact_and_structurally_improved"
    else:
        classification = "paper_exact_but_still_mixed"
    final = {
        "schema": "round31-final-audit-v1",
        "official_rows_materialized": len(runs),
        "stage_rows": {
            str(stage): len(rows) for stage, rows in by_stage.items()
        },
        "completed_process_rows": sum(
            run["state"]["return_code"] == 0 and
            run["state"]["result_exists"] for run in runs),
        "failed_process_rows": process_failures,
        "emergency_timeout_rows": sum(
            run["state"]["emergency_timeout"] for run in runs),
        "time_limited_rows": sum(
            "time_limit" in str(run["result"].get("status", ""))
            for run in runs),
        "excluded_stage6_rows": 0 if by_stage[6] else 27,
        "exactness_gate": exact,
        "false_certificate_count": false_certificates,
        "p_grb_vs_c6_final_lb_wins": lb_wins,
        "p_grb_vs_c6_final_lb_losses":
            len(p_vs_c6) - lb_wins - lb_ties,
        "p_grb_vs_c6_final_lb_ties": lb_ties,
        "p_grb_vs_c6_auc_available": len(auc_available),
        "p_grb_vs_c6_auc_wins": auc_wins,
        "p_grb_vs_c6_auc_losses":
            len(auc_available) - auc_wins - auc_ties,
        "p_grb_vs_c6_auc_ties": auc_ties,
        "sealed_final_lb_wins_ties": sealed_lb_wins_ties,
        "sealed_auc_wins_ties": sealed_auc_wins_ties,
        "short_run_gate_passed": short_gate,
        "classification": classification,
        "stable_mainline": "S0/F0-CPLEX",
        "c6_promoted": False,
        "conditional_stage6_executed": bool(by_stage[6]),
        "long_run_promotion_study_justified":
            classification == "paper_exact_and_broadly_dominant",
    }
    write_json(OUT / "final_audit_summary.json", final)
    print(json.dumps(final, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
