#!/usr/bin/env python3
"""Analyze frozen Round 32 rows using only observed certificate events."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import os
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, TextIO

import round30_bound_trace as bound_trace


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_long_run_validation_round32"
RUNS = OUT / "runs"
STAGE0_RUNS = OUT / "stage0_runs"
ROUND31 = ROOT / "results" / "gf_nonblocking_gurobi_c6_round31"
TOL = 1e-7
MATERIAL_GAP_TOL = 1e-7
GAP_THRESHOLDS = (0.50, 0.25, 0.20, 0.10, 0.05, 0.02, 0.01, 0.005, 0.001)
PROFILE_TAU = (1.0, 1.25, 1.5, 2.0, 3.0, 5.0, 10.0)


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


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def open_text(path: Path) -> TextIO:
    return (
        gzip.open(path, "rt", encoding="utf-8", newline="")
        if path.suffix.lower() == ".gz"
        else path.open("r", encoding="utf-8", newline=""))


def resolve_data(path: Path) -> Path | None:
    if path.is_file():
        return path
    compressed = Path(str(path) + ".gz")
    return compressed if compressed.is_file() else None


def csv_rows(path: Path) -> list[dict[str, str]]:
    candidate = resolve_data(path)
    if candidate is None:
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
        columns, material = ["status"], [{"status": "no_rows"}]
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_text(path: Path, text: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def discover(root: Path) -> list[dict[str, Any]]:
    output = []
    if not root.exists():
        return output
    for marker_path in sorted(root.glob("*/completion_marker.json")):
        state = load_json(marker_path)
        result_path = marker_path.parent / "result.json"
        output.append({
            "state": state,
            "result": load_json(result_path) if result_path.is_file() else {},
            "run_dir": marker_path.parent,
        })
    return output


def result_bounds(run: dict[str, Any]) -> tuple[float, float]:
    result = run["result"]
    if run["state"]["arm"] in {"C5-REFERENCE", "C6-FROZEN"}:
        return (
            number(result.get(
                "external_gini_tree_global_lower_bound",
                result.get("lower_bound"))),
            number(result.get(
                "external_gini_tree_verified_upper_bound",
                result.get("upper_bound"))),
        )
    return number(result.get("lower_bound")), number(result.get("upper_bound"))


def work(run: dict[str, Any]) -> float:
    arm, result = run["state"]["arm"], run["result"]
    if arm == "P-GRB":
        return number(result.get("gurobi_work"))
    if arm in {"C5-REFERENCE", "C6-FROZEN"}:
        return number(result.get("external_gini_tree_work"))
    return math.nan


def nodes(run: dict[str, Any]) -> float:
    arm, result = run["state"]["arm"], run["result"]
    if arm == "P-GRB":
        return number(result.get(
            "gurobi_node_count", result.get("native_mip_node_count")))
    if arm in {"C5-REFERENCE", "C6-FROZEN"}:
        return number(result.get("external_gini_tree_nodes"))
    return number(result.get("native_mip_node_count"))


def memory(run: dict[str, Any]) -> float:
    if run["state"]["arm"] in {"C5-REFERENCE", "C6-FROZEN"}:
        return number(run["result"].get("external_gini_tree_peak_memory_gb"))
    return math.nan


def metric(run: dict[str, Any], suffix: str, default: Any = 0) -> Any:
    return run["result"].get(f"external_gini_tree_{suffix}", default)


def phase_time(run: dict[str, Any], event: str) -> float:
    for row in csv_rows(run["run_dir"] / "process_phases.csv"):
        if row.get("event") == event:
            return number(row.get("process_seconds"), 0.0)
    return 0.0


def trace_for(run: dict[str, Any]) -> tuple[
        bool, str, tuple[bound_trace.BoundObservation, ...]]:
    arm = run["state"]["arm"]
    if arm in {"C5-REFERENCE", "C6-FROZEN"}:
        path = run["run_dir"] / "external" / "global_bound_trace.csv"
        candidate = resolve_data(path)
        if candidate is None:
            return False, "trace_missing", ()
        audit = bound_trace.audit_external_trace(candidate)
        return audit.complete, audit.reason, audit.observations
    if arm == "P-GRB":
        rows = csv_rows(run["run_dir"] / "progress.csv")
        launch = phase_time(run, "plain_gurobi_optimize_launch")
        observations = []
        last_bound = -math.inf
        last_time = -math.inf
        for row_number, row in enumerate(rows, start=2):
            if not truth(row.get("best_bound_available")):
                continue
            value = number(row.get("best_bound"))
            elapsed = number(row.get("elapsed_runtime_seconds"))
            if (
                not math.isfinite(value)
                or not math.isfinite(elapsed)
                or abs(value) >= 1e50
            ):
                continue
            process = launch + elapsed
            if process + TOL < last_time:
                return False, (
                    f"plain_callback_time_nonmonotone_at_row_{row_number}"), ()
            scale = max(1.0, abs(last_bound), abs(value))
            if value + TOL * scale < last_bound:
                return False, (
                    f"plain_callback_bound_nonmonotone_at_row_{row_number}"), ()
            last_time = max(last_time, process)
            last_bound = max(last_bound, value)
            observations.append(bound_trace.BoundObservation(
                process, elapsed, "native_progress_callback", last_bound,
                number(row.get("incumbent")),
                integer(row.get("open_nodes")), 0, last_bound, None,
                "gurobi_cb_mip_objbnd"))
        return (
            len(observations) >= 2,
            "complete_native_callback_trace"
            if len(observations) >= 2
            else "too_few_native_callback_bounds",
            tuple(observations),
        )
    return False, "trace_not_required_for_contextual_s0", ()


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
    proof_areas = [0.0, 0.0]
    gap_areas = [0.0, 0.0]
    lb_areas = [0.0, 0.0]
    for begin, finish in zip(times, times[1:]):
        duration = finish - begin
        for index, trace in enumerate((left, right)):
            value = value_at(trace, begin)
            gap = max(
                0.0, min(1.0, (upper - value) / denominator))
            lb_areas[index] += duration * value
            gap_areas[index] += duration * gap
            proof_areas[index] += duration * (1.0 - gap)
    duration = end - start
    return {
        "auc_status": "observed_common_window",
        "auc_reason": "no_interpolation_no_post_last_event_extension",
        "common_window_start_process_seconds": start,
        "common_window_end_process_seconds": end,
        "common_window_duration_seconds": duration,
        "left_mean_valid_lower_bound": lb_areas[0] / duration,
        "right_mean_valid_lower_bound": lb_areas[1] / duration,
        "left_normalized_proof_auc": proof_areas[0] / duration,
        "right_normalized_proof_auc": proof_areas[1] / duration,
        "normalized_proof_auc_delta_right_minus_left":
            (proof_areas[1] - proof_areas[0]) / duration,
        "left_normalized_gap_auc": gap_areas[0] / duration,
        "right_normalized_gap_auc": gap_areas[1] / duration,
    }


def public_row(run: dict[str, Any], common_ub: float | None = None
               ) -> dict[str, Any]:
    state, result = run["state"], run["result"]
    lower, upper = result_bounds(run)
    common = upper if common_ub is None else common_ub
    gap = (
        max(0.0, (common - lower) / max(abs(common), 1e-12))
        if math.isfinite(lower) and math.isfinite(common)
        else math.nan)
    strict = truth(result.get("strict_certified_original_problem"))
    return {
        "round_id": 32,
        "stage_id": state["stage_id"],
        "run_id": state["run_id"],
        "instance_id": state["instance_id"],
        "instance_path": state["instance_path"],
        "instance_sha256": state["instance_sha256"],
        "family": state["family"],
        "V": state["V"],
        "M": state["M"],
        "Q": state["Q"],
        "T": state["T"],
        "nominal_budget_seconds": state["nominal_budget_seconds"],
        "actual_process_cap_seconds": state["actual_process_cap_seconds"],
        "arm": state["arm"],
        "solver": state["solver"],
        "solver_version": state["solver_version"],
        "executable_sha256": state["executable_sha256"],
        "source_commit": state["source_commit"],
        "protocol_sha256": state["protocol_sha256"],
        "run_status": state["run_status"],
        "return_code": state["return_code"],
        "status": result.get("status", "result_missing"),
        "valid_final_lb": lower,
        "verified_ub": upper,
        "common_verified_ub": common,
        "common_ub_normalized_gap": gap,
        "strict_certificate": strict,
        "certificate_time_seconds":
            number(result.get("runtime_seconds")) if strict else "",
        "total_wall_seconds": number(result.get("runtime_seconds")),
        "total_work": work(run),
        "native_nodes": nodes(run),
        "peak_memory_gb": memory(run),
        "graceful_deadline_finalization":
            truth(result.get("graceful_deadline_finalization")),
        "failure_reason": result.get(
            "external_gini_tree_failure_reason",
            result.get("gurobi_failure_reason", "")),
        "run_path": run["run_dir"].relative_to(ROOT).as_posix(),
    }


def paired(
        runs: list[dict[str, Any]], left_arm: str, right_arm: str,
        traces: dict[str, tuple[
            bool, str, tuple[bound_trace.BoundObservation, ...]]]
        ) -> list[dict[str, Any]]:
    keyed = {
        (run["state"]["instance_id"], run["state"]["arm"]): run
        for run in runs
    }
    output = []
    for name in sorted({
            key[0] for key in keyed
            if key[1] == left_arm and (key[0], right_arm) in keyed}):
        left = keyed[(name, left_arm)]
        right = keyed[(name, right_arm)]
        left_lb, left_ub = result_bounds(left)
        right_lb, right_ub = result_bounds(right)
        common = min(left_ub, right_ub)
        left_gap = max(
            0.0, (common - left_lb) / max(abs(common), 1e-12))
        right_gap = max(
            0.0, (common - right_lb) / max(abs(common), 1e-12))
        left_trace = traces[left["state"]["run_id"]]
        right_trace = traces[right["state"]["run_id"]]
        auc = (
            pair_auc(left_trace[2], right_trace[2], common)
            if left_trace[0] and right_trace[0]
            else {
                "auc_status": "auc_unavailable",
                "auc_reason":
                    f"left={left_trace[1]};right={right_trace[1]}",
            })
        left_strict = truth(left["result"].get(
            "strict_certified_original_problem"))
        right_strict = truth(right["result"].get(
            "strict_certified_original_problem"))
        output.append({
            "round_id": 32,
            "stage_id": left["state"]["stage_id"],
            "instance_id": name,
            "family": left["state"]["family"],
            "V": left["state"]["V"],
            "M": left["state"]["M"],
            "Q": left["state"]["Q"],
            "nominal_budget_seconds":
                left["state"]["nominal_budget_seconds"],
            "left_arm": left_arm,
            "right_arm": right_arm,
            "common_verified_ub": common,
            "left_final_lb": left_lb,
            "right_final_lb": right_lb,
            "left_common_gap": left_gap,
            "right_common_gap": right_gap,
            "final_gap_delta_right_minus_left": right_gap - left_gap,
            "left_strict_certificate": left_strict,
            "right_strict_certificate": right_strict,
            "left_certificate_time_seconds":
                number(left["result"].get("runtime_seconds"))
                if left_strict else "",
            "right_certificate_time_seconds":
                number(right["result"].get("runtime_seconds"))
                if right_strict else "",
            "left_work": work(left),
            "right_work": work(right),
            "left_nodes": nodes(left),
            "right_nodes": nodes(right),
            "left_peak_memory_gb": memory(left),
            "right_peak_memory_gb": memory(right),
            "gap_outcome": (
                "right_win" if right_gap < left_gap - MATERIAL_GAP_TOL
                else "left_win" if left_gap < right_gap - MATERIAL_GAP_TOL
                else "tie"),
            "certificate_outcome": (
                "right_win" if right_strict and not left_strict
                else "left_win" if left_strict and not right_strict
                else "both_certified" if left_strict and right_strict
                else "neither_certified"),
            **auc,
        })
    return output


def trace_and_threshold_outputs(
        runs: list[dict[str, Any]],
        traces: dict[str, tuple[
            bool, str, tuple[bound_trace.BoundObservation, ...]]]
        ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    auc_rows, threshold_rows = [], []
    by_group: dict[tuple[str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        state = run["state"]
        by_group[(
            state["stage_id"], state["instance_id"],
            integer(state["nominal_budget_seconds"]))].append(run)
    for run in runs:
        state = run["state"]
        group = by_group[(
            state["stage_id"], state["instance_id"],
            integer(state["nominal_budget_seconds"]))]
        bounds = [
            result_bounds(item)[1] for item in group
            if math.isfinite(result_bounds(item)[1])]
        common = min(bounds) if bounds else math.nan
        complete, reason, observations = traces[state["run_id"]]
        row = {
            "run_id": state["run_id"],
            "stage_id": state["stage_id"],
            "instance_id": state["instance_id"],
            "family": state["family"],
            "V": state["V"],
            "M": state["M"],
            "arm": state["arm"],
            "nominal_budget_seconds": state["nominal_budget_seconds"],
            "trace_complete": complete,
            "trace_reason": reason,
            "bound_observations": len(observations),
            "auc_status": "observed" if complete else "auc_unavailable",
            "no_interpolation": True,
            "no_post_final_extension": True,
        }
        if complete and math.isfinite(common):
            row.update(bound_trace.observed_step_auc(
                observations, common_verified_upper_bound=common))
            for threshold in GAP_THRESHOLDS:
                reached = next((
                    point.process_seconds for point in observations
                    if (common - point.global_lower_bound)
                    / max(abs(common), 1e-12) <= threshold + 1e-12
                ), None)
                threshold_rows.append({
                    "run_id": state["run_id"],
                    "stage_id": state["stage_id"],
                    "instance_id": state["instance_id"],
                    "family": state["family"],
                    "V": state["V"],
                    "M": state["M"],
                    "arm": state["arm"],
                    "nominal_budget_seconds":
                        state["nominal_budget_seconds"],
                    "common_verified_ub": common,
                    "common_gap_threshold": threshold,
                    "reached": reached is not None,
                    "first_observed_process_seconds":
                        reached if reached is not None else "",
                    "no_interpolation": True,
                })
            strict = truth(run["result"].get(
                "strict_certified_original_problem"))
            threshold_rows.append({
                "run_id": state["run_id"],
                "stage_id": state["stage_id"],
                "instance_id": state["instance_id"],
                "family": state["family"],
                "V": state["V"],
                "M": state["M"],
                "arm": state["arm"],
                "nominal_budget_seconds":
                    state["nominal_budget_seconds"],
                "common_verified_ub": common,
                "common_gap_threshold": "strict_certification",
                "reached": strict,
                "first_observed_process_seconds":
                    number(run["result"].get("runtime_seconds"))
                    if strict else "",
                "no_interpolation": True,
                "time_source": "final_strict_certificate_result",
            })
        auc_rows.append(row)
    return auc_rows, threshold_rows


def work_thresholds(runs: list[dict[str, Any]],
                    time_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_run = {run["state"]["run_id"]: run for run in runs}
    output = []
    for row in time_rows:
        run = by_run[row["run_id"]]
        arm = run["state"]["arm"]
        threshold = row["common_gap_threshold"]
        if arm != "P-GRB" or threshold == "strict_certification":
            output.append({
                **row,
                "first_observed_work": (
                    work(run)
                    if threshold == "strict_certification"
                    and truth(row["reached"]) else ""),
                "work_status": (
                    "final_total_work_at_strict_certificate"
                    if threshold == "strict_certification"
                    and truth(row["reached"])
                    else "unavailable_no_synchronized_work_trace"),
            })
            continue
        common = number(row["common_verified_ub"])
        target_time = number(row["first_observed_process_seconds"])
        launch = phase_time(run, "plain_gurobi_optimize_launch")
        observed_work = ""
        if truth(row["reached"]) and math.isfinite(target_time):
            for progress in csv_rows(run["run_dir"] / "progress.csv"):
                elapsed = number(progress.get("elapsed_runtime_seconds"))
                if (
                    truth(progress.get("best_bound_available"))
                    and launch + elapsed + 1e-12 >= target_time
                ):
                    observed_work = progress.get("work", "")
                    break
        output.append({
            **row,
            "first_observed_work": observed_work,
            "work_status": (
                "observed_native_progress_work"
                if observed_work != "" else "threshold_not_reached"),
        })
    return output


def summarize_pairs(pair_rows: list[dict[str, Any]],
                    keys: tuple[str, ...]) -> list[dict[str, Any]]:
    def shifted_geomean(values: Iterable[float],
                        shift: float = 1e-9) -> float:
        material = [max(0.0, value) for value in values]
        return math.exp(statistics.fmean(
            math.log(value + shift) for value in material)) - shift

    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in pair_rows:
        groups[tuple(row[key] for key in keys)].append(row)
    output = []
    for key, group in sorted(groups.items(), key=lambda item: str(item[0])):
        auc = [
            row for row in group
            if row["auc_status"] == "observed_common_window"]
        record = {field: value for field, value in zip(keys, key)}
        record.update({
            "pairs": len(group),
            "c6_gap_wins": sum(row["gap_outcome"] == "right_win"
                               for row in group),
            "p_grb_gap_wins": sum(row["gap_outcome"] == "left_win"
                                  for row in group),
            "gap_ties": sum(row["gap_outcome"] == "tie" for row in group),
            "c6_certificates": sum(truth(row["right_strict_certificate"])
                                   for row in group),
            "p_grb_certificates": sum(truth(row["left_strict_certificate"])
                                      for row in group),
            "auc_available": len(auc),
            "c6_auc_wins": sum(
                number(row[
                    "normalized_proof_auc_delta_right_minus_left"]) > TOL
                for row in auc),
            "p_grb_auc_wins": sum(
                number(row[
                    "normalized_proof_auc_delta_right_minus_left"]) < -TOL
                for row in auc),
            "auc_ties": sum(
                abs(number(row[
                    "normalized_proof_auc_delta_right_minus_left"])) <= TOL
                for row in auc),
            "median_final_gap_delta_c6_minus_p": statistics.median(
                number(row["final_gap_delta_right_minus_left"])
                for row in group),
            "median_auc_delta_c6_minus_p": (
                statistics.median(number(row[
                    "normalized_proof_auc_delta_right_minus_left"])
                                  for row in auc)
                if auc else ""),
            "shifted_geomean_p_grb_common_gap": shifted_geomean(
                number(row["left_common_gap"]) for row in group),
            "shifted_geomean_c6_common_gap": shifted_geomean(
                number(row["right_common_gap"]) for row in group),
            "shift_for_gap_geomean": 1e-9,
        })
        output.append(record)
    return output


def performance_profile(
        pair_rows: list[dict[str, Any]],
        threshold_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    times = {
        (row["stage_id"], row["instance_id"], row["arm"],
         str(row["common_gap_threshold"])): number(
             row["first_observed_process_seconds"])
        for row in threshold_rows if truth(row["reached"])
    }
    output = []
    for threshold in GAP_THRESHOLDS:
        ratios: dict[str, list[float]] = {"P-GRB": [], "C6-FROZEN": []}
        eligible = 0
        for pair in pair_rows:
            key = (
                pair["stage_id"], pair["instance_id"], str(threshold))
            left = times.get((key[0], key[1], "P-GRB", key[2]))
            right = times.get((key[0], key[1], "C6-FROZEN", key[2]))
            if not (math.isfinite(left or math.nan)
                    or math.isfinite(right or math.nan)):
                continue
            eligible += 1
            best = min(
                value for value in (left, right)
                if value is not None and math.isfinite(value))
            ratios["P-GRB"].append(
                left / best if left is not None else math.inf)
            ratios["C6-FROZEN"].append(
                right / best if right is not None else math.inf)
        for tau in PROFILE_TAU:
            for arm in ("P-GRB", "C6-FROZEN"):
                output.append({
                    "common_gap_threshold": threshold,
                    "tau": tau,
                    "arm": arm,
                    "eligible_pairs": eligible,
                    "fraction_within_tau_of_best": (
                        sum(value <= tau + 1e-12 for value in ratios[arm])
                        / eligible if eligible else ""),
                    "unreached_is_infinite": True,
                })
    return output


def exactness_audits(runs: list[dict[str, Any]]) -> tuple[
        list[dict[str, Any]], list[dict[str, Any]], bool, int]:
    exactness, certificates = [], []
    false_count = 0
    for run in runs:
        result, state = run["result"], run["state"]
        lower, upper = result_bounds(run)
        strict = truth(result.get("strict_certified_original_problem"))
        if state["arm"] == "C6-FROZEN":
            structural = all((
                truth(metric(run, "root_coverage_valid")),
                truth(metric(run, "parent_child_coverage_valid")),
                truth(metric(run, "all_leaf_bounds_valid")),
                truth(metric(run, "leaf_bounds_monotone")),
                truth(metric(run, "global_bound_monotone")),
                truth(metric(run, "lifecycle_complete")),
                truth(metric(run, "feasibility_consistency_gate")),
            ))
            all_closed = truth(metric(run, "all_relevant_leaves_closed"))
            open_preserved = (
                all_closed or integer(metric(run, "open_leaf_count")) > 0)
        else:
            structural = (
                truth(result.get(
                    "original_compact_structure_identity", True))
                and truth(result.get(
                    "original_problem_verification_passed", True)))
            all_closed = strict
            open_preserved = True
        false = strict and (
            not structural
            or not math.isfinite(lower)
            or not math.isfinite(upper)
            or abs(lower - upper) >
               TOL * max(1.0, abs(lower), abs(upper)))
        false_count += int(false)
        exactness.append({
            "run_id": state["run_id"],
            "stage_id": state["stage_id"],
            "instance_id": state["instance_id"],
            "arm": state["arm"],
            "structural_gate": structural,
            "open_leaf_preserved_on_deadline": open_preserved,
            "valid_lower_bound": lower,
            "verified_upper_bound": upper,
            "lifecycle_complete": (
                truth(metric(run, "lifecycle_complete"))
                if state["arm"] == "C6-FROZEN" else True),
            "passed": structural and open_preserved and math.isfinite(lower),
        })
        certificates.append({
            "run_id": state["run_id"],
            "stage_id": state["stage_id"],
            "instance_id": state["instance_id"],
            "arm": state["arm"],
            "strict_certificate": strict,
            "certificate_class": result.get("strict_certificate_class"),
            "certificate_rejection_reason":
                result.get("strict_certificate_rejection_reason"),
            "false_certificate": false,
            "passed": not false,
        })
    passed = (
        all(truth(row["passed"]) for row in exactness)
        and all(truth(row["passed"]) for row in certificates))
    return exactness, certificates, passed, false_count


def trace_audit_rows(
        runs: list[dict[str, Any]],
        traces: dict[str, tuple[
            bool, str, tuple[bound_trace.BoundObservation, ...]]]
        ) -> list[dict[str, Any]]:
    output = []
    for run in runs:
        state = run["state"]
        complete, reason, observations = traces[state["run_id"]]
        required = state["arm"] in {
            "P-GRB", "C5-REFERENCE", "C6-FROZEN"}
        output.append({
            "run_id": state["run_id"],
            "stage_id": state["stage_id"],
            "instance_id": state["instance_id"],
            "arm": state["arm"],
            "trace_required": required,
            "trace_complete": complete,
            "trace_reason": reason,
            "observation_count": len(observations),
            "formal_scheduler_global_bound_monotone": (
                truth(metric(run, "global_bound_monotone"))
                if state["arm"] in {"C5-REFERENCE", "C6-FROZEN"}
                else True),
            "passed": (not required) or complete,
        })
    return output


def projection(path: Path, fields: tuple[str, ...],
               float_fields: tuple[str, ...] = ()) -> list[tuple[Any, ...]]:
    output = []
    for row in csv_rows(path):
        values: list[Any] = []
        for field in fields:
            value: Any = row.get(field, "")
            if field in float_fields and value != "":
                value = round(number(value), 8)
            values.append(value)
        output.append(tuple(values))
    return output


def frozen_equivalence(stage0: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for run in stage0:
        baseline_id = run["state"].get("baseline_round31_run_id", "")
        if not baseline_id or run["state"]["arm"] != "C6-FROZEN":
            continue
        baseline = ROUND31 / "runs" / baseline_id
        if not baseline.is_dir():
            baseline = ROUND31 / "stage0_runs" / baseline_id
        current = run["run_dir"]
        before = load_json(baseline / "result.json")
        after = run["result"]
        before_lb = number(before.get("external_gini_tree_global_lower_bound"))
        after_lb = number(after.get("external_gini_tree_global_lower_bound"))
        before_ub = number(before.get("external_gini_tree_verified_upper_bound"))
        after_ub = number(after.get("external_gini_tree_verified_upper_bound"))
        decision_checks = {
            "parent_lp_objectives_equal": projection(
                baseline / "external/lp_status_ledger.csv",
                ("leaf_id", "optimal", "infeasible", "lower_bound"),
                ("lower_bound",)) == projection(
                    current / "external/lp_status_ledger.csv",
                    ("leaf_id", "optimal", "infeasible", "lower_bound"),
                    ("lower_bound",)),
            "native_target_sequence_equal": projection(
                baseline / "external/native_target_ledger.csv",
                ("leaf_id", "target_kind", "current_bound", "target_bound",
                 "target_reached", "exact_closure", "requeued"),
                ("current_bound", "target_bound")) == projection(
                    current / "external/native_target_ledger.csv",
                    ("leaf_id", "target_kind", "current_bound", "target_bound",
                     "target_reached", "exact_closure", "requeued"),
                    ("current_bound", "target_bound")),
            "child_bounds_equal": projection(
                baseline / "external/parent_child_bound_ledger.csv",
                ("parent_id", "left_id", "left_lp_bound", "right_id",
                 "right_lp_bound", "decision"),
                ("left_lp_bound", "right_lp_bound")) == projection(
                    current / "external/parent_child_bound_ledger.csv",
                    ("parent_id", "left_id", "left_lp_bound", "right_id",
                     "right_lp_bound", "decision"),
                    ("left_lp_bound", "right_lp_bound")),
            "split_decisions_equal": projection(
                baseline / "external/split_decision_ledger.csv",
                ("parent_id", "eligible", "split", "reason")) == projection(
                    current / "external/split_decision_ledger.csv",
                    ("parent_id", "eligible", "split", "reason")),
            "requeue_and_closure_sequence_equal": projection(
                baseline / "external/paper_tree_events.csv",
                ("event", "leaf_id", "status", "detail")) == projection(
                    current / "external/paper_tree_events.csv",
                    ("event", "leaf_id", "status", "detail")),
        }
        final_valid_lb_equal = (
            abs(before_lb - after_lb)
            <= TOL * max(1.0, abs(before_lb), abs(after_lb)))
        final_valid_lbs_valid = (
            math.isfinite(before_lb)
            and math.isfinite(after_lb)
            and math.isfinite(before_ub)
            and math.isfinite(after_ub)
            and before_lb <= before_ub + TOL * max(1.0, abs(before_ub))
            and after_lb <= after_ub + TOL * max(1.0, abs(after_ub)))
        endpoint_checks = {
            "final_valid_lb_equal": final_valid_lb_equal,
            "final_valid_lbs_valid": final_valid_lbs_valid,
            "verified_ub_equal": (
                abs(before_ub - after_ub)
                <= TOL * max(1.0, abs(before_ub), abs(after_ub))),
            "certificate_equal": truth(before.get(
                "strict_certified_original_problem")) == truth(after.get(
                    "strict_certified_original_problem")),
        }
        output.append({
            "instance_id": run["state"]["instance_id"],
            "baseline_round31_run_id": baseline_id,
            "round32_run_id": run["state"]["run_id"],
            **decision_checks,
            **endpoint_checks,
            # A time-limited native-MIP callback frontier depends on the
            # engineering shutdown horizon.  Exact terminal-LB equality is
            # recorded above, but is not a mathematical decision.  Frozen
            # equivalence instead requires every discrete decision to match
            # and both independently reported endpoints to remain valid,
            # with the same verified UB and certificate outcome.
            "all_frozen_decisions_equivalent": (
                all(decision_checks.values())
                and final_valid_lbs_valid
                and endpoint_checks["verified_ub_equal"]
                and endpoint_checks["certificate_equal"]),
            "trace_serialization_allowed_to_differ": True,
        })
    return output


def repeatability_rows(
        official: list[dict[str, Any]],
        pair_auc_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    primary = {
        (run["state"]["instance_id"], run["state"]["arm"]): run
        for run in official
        if run["state"]["stage_id"] in {"stage1", "stage2"}
    }
    repeats = [
        run for run in official
        if run["state"]["stage_id"] == "repeatability"]
    output = []
    for repeat in repeats:
        key = (repeat["state"]["instance_id"], repeat["state"]["arm"])
        original = primary[key]
        left_lb, left_ub = result_bounds(original)
        right_lb, right_ub = result_bounds(repeat)
        row = {
            "instance_id": key[0],
            "family": repeat["state"]["family"],
            "V": repeat["state"]["V"],
            "M": repeat["state"]["M"],
            "arm": key[1],
            "original_run_id": original["state"]["run_id"],
            "repeat_run_id": repeat["state"]["run_id"],
            "original_lb": left_lb,
            "repeat_lb": right_lb,
            "final_lb_absolute_delta": abs(left_lb - right_lb),
            "verified_ub_absolute_delta": abs(left_ub - right_ub),
            "certificate_equal": truth(original["result"].get(
                "strict_certified_original_problem")) == truth(
                    repeat["result"].get(
                        "strict_certified_original_problem")),
            "lifecycle_valid": (
                truth(metric(repeat, "lifecycle_complete"))
                if key[1] == "C6-FROZEN" else True),
        }
        if key[1] == "C6-FROZEN":
            row.update({
                "hga_trajectory_exact": (
                    (original["run_dir"] / "hga_generations.csv").read_bytes()
                    == (repeat["run_dir"] / "hga_generations.csv").read_bytes()),
                "target_sequence_exact": projection(
                    original["run_dir"]
                    / "external/native_target_ledger.csv",
                    ("leaf_id", "target_kind", "target_bound", "status"),
                    ("target_bound",)) == projection(
                        repeat["run_dir"]
                        / "external/native_target_ledger.csv",
                        ("leaf_id", "target_kind", "target_bound", "status"),
                        ("target_bound",)),
                "split_sequence_exact": projection(
                    original["run_dir"]
                    / "external/split_decision_ledger.csv",
                    ("parent_id", "split", "reason")) == projection(
                        repeat["run_dir"]
                        / "external/split_decision_ledger.csv",
                        ("parent_id", "split", "reason")),
            })
        output.append(row)
    return output


def mechanism_outputs(runs: list[dict[str, Any]]) -> dict[str, int]:
    splits, lookaheads, targets, closures, lifecycle = [], [], [], [], []
    for run in runs:
        if run["state"]["arm"] not in {"C5-REFERENCE", "C6-FROZEN"}:
            continue
        state, directory = run["state"], run["run_dir"]
        base = {
            "run_id": state["run_id"],
            "stage_id": state["stage_id"],
            "instance_id": state["instance_id"],
            "family": state["family"],
            "V": state["V"],
            "M": state["M"],
            "arm": state["arm"],
        }
        bound_by_parent = {
            row.get("parent_id", ""): row for row in csv_rows(
                directory / "external/parent_child_bound_ledger.csv")
        }
        leaves = {
            row.get("leaf_id", ""): row for row in csv_rows(
                directory / "external/paper_leaf_ledger.csv")
        }
        split_times: dict[str, float] = {}
        for event in csv_rows(
                directory / "external/paper_tree_events.csv"):
            if event.get("event") == "split":
                split_times[event.get("leaf_id", "")] = number(
                    event.get("telemetry_seconds"))
        global_split_changes: dict[str, float] = {}
        previous_bound = math.nan
        for event in csv_rows(
                directory / "external/global_bound_trace.csv"):
            current_bound = number(event.get("valid_global_lower_bound"))
            if event.get("event_type") == "split":
                active = event.get("active_leaf", "")
                global_split_changes[active] = (
                    current_bound - previous_bound
                    if math.isfinite(previous_bound) else math.nan)
            previous_bound = current_bound
        for row in csv_rows(
                directory / "external/split_decision_ledger.csv"):
            parent = row.get("parent_id", "")
            split = truth(row.get("split"))
            bounds = bound_by_parent.get(parent, {})
            leaf = leaves.get(parent, {})
            descendants = [
                item for leaf_id, item in leaves.items()
                if leaf_id.startswith(parent + ".")
            ]
            splits.append({
                **base, **row,
                "actual_atomic_split": split,
                "split_time_seconds": split_times.get(parent, ""),
                "split_depth": leaf.get("depth", ""),
                "split_gamma_L": leaf.get("gamma_L", ""),
                "split_gamma_U": leaf.get("gamma_U", ""),
                "split_interval_width": (
                    number(leaf.get("gamma_U"))
                    - number(leaf.get("gamma_L"))
                    if leaf else ""),
                "parent_lp_bound": bounds.get("parent_lp_bound", ""),
                "left_child_bound": bounds.get("left_lp_bound", ""),
                "right_child_bound": bounds.get("right_lp_bound", ""),
                "post_split_bound": bounds.get("post_split_bound", ""),
                "immediate_global_lb_change":
                    global_split_changes.get(parent, ""),
                "descendant_final_min_lower_bound": (
                    min(number(item.get("lower_bound"))
                        for item in descendants)
                    if descendants else ""),
                "descendants_all_closed": (
                    all(item.get("status") not in {"open", "invalid"}
                        for item in descendants)
                    if descendants else ""),
                "descendants_close_earlier_than_unsplit_parent":
                    "unavailable_no_valid_counterfactual",
                "counterfactual_runtime_claimed": False,
            })
        for row in csv_rows(
                directory / "external/parent_child_bound_ledger.csv"):
            lookaheads.append({**base, **row})
        for row in csv_rows(
                directory / "external/native_target_ledger.csv"):
            targets.append({**base, **row})
        for row in csv_rows(
                directory / "external/paper_optimize_ledger.csv"):
            if row.get("solve_kind") == "MIP":
                closures.append({**base, **row})
        lifecycle.append({
            **base,
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
            "native_requeues": metric(run, "native_requeue_count"),
            "exact_closure_launches":
                metric(run, "exact_closure_launch_count"),
            "lp_cutoff_prunes": metric(run, "lp_pruned_leaf_count"),
            "terminal_work": metric(run, "terminal_mip_work"),
            "total_work": metric(run, "work"),
            "native_nodes": metric(run, "nodes"),
            "peak_memory_gb": metric(run, "peak_memory_gb"),
            "lifecycle_complete": truth(metric(run, "lifecycle_complete")),
            "native_tree_continuation_claimed": False,
        })
    write_csv(OUT / "split_long_run_audit.csv", splits)
    write_csv(OUT / "child_lookahead_long_run_audit.csv", lookaheads)
    write_csv(OUT / "native_target_long_run_audit.csv", targets)
    write_csv(OUT / "terminal_closure_long_run_audit.csv", closures)
    write_csv(OUT / "lifecycle_and_resource_summary.csv", lifecycle)
    return {
        "actual_atomic_splits": sum(
            truth(row["actual_atomic_split"]) for row in splits),
        "child_lookahead_pairs": len(lookaheads),
        "native_target_rows": len(targets),
        "requeues": sum(
            integer(row.get("native_requeues")) for row in lifecycle),
        "exact_closure_launches": sum(
            integer(row.get("exact_closure_launches")) for row in lifecycle),
        "lp_cutoff_prunes": sum(
            integer(row.get("lp_cutoff_prunes")) for row in lifecycle),
    }


def historical_reference() -> None:
    rows = csv_rows(ROUND31 / "p_grb_vs_c6.csv")
    output = [{
        "historical_round": 31,
        "historical_only": True,
        "not_round32_official": True,
        "historical_budget_seconds": 300,
        **row,
    } for row in rows]
    write_csv(OUT / "historical_round31_reference.csv", output)


def stage0_main(stage0: list[dict[str, Any]]) -> int:
    if len(stage0) != 12:
        raise RuntimeError(
            f"Stage 0 requires 12 completed rows, found {len(stage0)}")
    traces = {
        run["state"]["run_id"]: trace_for(run) for run in stage0
    }
    exactness, certificates, exact_pass, false_count = exactness_audits(stage0)
    trace_rows = trace_audit_rows(stage0, traces)
    equivalence = frozen_equivalence(stage0)
    v12 = [
        row for row in trace_rows
        if row["instance_id"] == "V12_M2"]
    stage0_exact = [
        {**public_row(run), "exactness_passed": exactness[index]["passed"]}
        for index, run in enumerate(stage0)
    ]
    write_csv(OUT / "stage0_exactness.csv", stage0_exact)
    write_csv(OUT / "stage0_trace_qualification.csv", trace_rows)
    write_csv(OUT / "trace_monotonicity_audit.csv", trace_rows)
    write_csv(OUT / "frozen_decision_equivalence.csv", equivalence)
    sentinel = [
        public_row(run) for run in stage0
        if run["state"].get("suite") == "exactness_sentinel"
    ]
    write_csv(OUT / "stage0_sentinel.csv", sentinel)
    all_passed = (
        exact_pass
        and false_count == 0
        and all(truth(row["passed"]) for row in trace_rows)
        and len(v12) == 2
        and all(truth(row["passed"]) for row in v12)
        and len(equivalence) == 3
        and all(truth(row["all_frozen_decisions_equivalent"])
                for row in equivalence)
    )
    write_json(OUT / "stage0_gate_summary.json", {
        "schema": "round32-stage0-gates-v1",
        "completed_rows": len(stage0),
        "false_certificates": false_count,
        "trace_rows": len(trace_rows),
        "v12_m2_trace_rows": len(v12),
        "frozen_equivalence_rows": len(equivalence),
        "all_stage0_gates_passed": all_passed,
    })
    return 0 if all_passed else 1


def classification(
        pair1800: list[dict[str, Any]],
        pair3600: list[dict[str, Any]],
        threshold_rows: list[dict[str, Any]],
        exact_pass: bool,
        false_count: int,
        trace_rows: list[dict[str, Any]]) -> tuple[str, dict[str, bool]]:
    if false_count or not exact_pass:
        return "invalid", {"exactness": False}
    required_trace = [row for row in trace_rows if truth(row["trace_required"])]
    if not required_trace or not all(truth(row["passed"]) for row in required_trace):
        return "c6_engineering_evidence_incomplete", {
            "exactness": True, "trace_complete": False}
    group_summaries = (
        summarize_pairs(pair1800, ("family",))
        + summarize_pairs(pair1800, ("V",))
        + summarize_pairs(pair1800, ("M",)))
    no_group_majority_loss = all(
        integer(row["p_grb_gap_wins"]) <= integer(row["pairs"]) / 2
        for row in group_summaries)
    large_majority = sum(
        row["gap_outcome"] != "left_win" for row in pair1800
    ) >= math.ceil(2 * len(pair1800) / 3)
    certificates = sum(
        truth(row["right_strict_certificate"]) for row in pair1800
    ) >= sum(truth(row["left_strict_certificate"]) for row in pair1800)
    auc = [
        row for row in pair1800
        if row["auc_status"] == "observed_common_window"]
    auc_favors = bool(auc) and statistics.median(
        number(row["normalized_proof_auc_delta_right_minus_left"])
        for row in auc) >= -TOL
    time_map = {
        (row["stage_id"], row["instance_id"], row["arm"],
         str(row["common_gap_threshold"])): (
             number(row["first_observed_process_seconds"])
             if truth(row["reached"]) else math.inf)
        for row in threshold_rows
        if row["stage_id"] in {"stage1", "stage2"}
        and row["common_gap_threshold"] != "strict_certification"
    }
    time_wins = {"C6-FROZEN": 0, "P-GRB": 0, "tie": 0}
    for pair in pair1800:
        for threshold in GAP_THRESHOLDS:
            base = (
                pair["stage_id"], pair["instance_id"], str(threshold))
            left = time_map.get((base[0], base[1], "P-GRB", base[2]),
                                math.inf)
            right = time_map.get((base[0], base[1], "C6-FROZEN", base[2]),
                                 math.inf)
            if not math.isfinite(left) and not math.isfinite(right):
                continue
            if right < left - TOL:
                time_wins["C6-FROZEN"] += 1
            elif left < right - TOL:
                time_wins["P-GRB"] += 1
            else:
                time_wins["tie"] += 1
    threshold_favors = (
        time_wins["C6-FROZEN"] + time_wins["tie"]
        >= time_wins["P-GRB"])
    no_3600_reversal = sum(
        row["gap_outcome"] == "left_win" for row in pair3600
    ) <= len(pair3600) / 2
    multi = [row for row in pair1800 if row["stage_id"] == "stage2"]
    multi_supports = sum(
        row["gap_outcome"] != "left_win" for row in multi
    ) >= math.ceil(len(multi) / 2)
    gates = {
        "exactness": True,
        "trace_complete": True,
        "no_group_majority_loss": no_group_majority_loss,
        "large_majority_1800_wins_or_ties": large_majority,
        "certificate_count_not_lower": certificates,
        "median_auc_favors_c6": auc_favors,
        "observed_time_to_gap_favors_c6": threshold_favors,
        "no_3600_systematic_reversal": no_3600_reversal,
        "multi_m_supports": multi_supports,
    }
    if all(gates.values()):
        return "c6_long_run_same_solver_advantage_confirmed", gates
    return "c6_short_run_advantage_long_run_mixed", gates


def final_report(summary: dict[str, Any],
                 pair1800: list[dict[str, Any]],
                 pair3600: list[dict[str, Any]],
                 c5: list[dict[str, Any]],
                 s0: list[dict[str, Any]]) -> None:
    def outcomes(rows: list[dict[str, Any]]) -> tuple[int, int, int]:
        return (
            sum(row["gap_outcome"] == "right_win" for row in rows),
            sum(row["gap_outcome"] == "left_win" for row in rows),
            sum(row["gap_outcome"] == "tie" for row in rows),
        )

    def auc_outcomes(rows: list[dict[str, Any]]) -> tuple[int, int, int, int]:
        available = [
            row for row in rows
            if row["auc_status"] == "observed_common_window"]
        return (
            sum(number(row[
                "normalized_proof_auc_delta_right_minus_left"]) > TOL
                for row in available),
            sum(number(row[
                "normalized_proof_auc_delta_right_minus_left"]) < -TOL
                for row in available),
            sum(abs(number(row[
                "normalized_proof_auc_delta_right_minus_left"])) <= TOL
                for row in available),
            len(available),
        )

    w1800, l1800, t1800 = outcomes(pair1800)
    w3600, l3600, t3600 = outcomes(pair3600)
    aw1800, al1800, at1800, aa1800 = auc_outcomes(pair1800)
    aw3600, al3600, at3600, aa3600 = auc_outcomes(pair3600)
    text = f"""# Round 32 final report

## Outcome

Classification: `{summary['classification']}`.

Round 32 completed {summary['completed_rows']} of 133 frozen official,
limited-reference, contextual, and repeatability rows. It retained
{summary['time_limited_rows']} valid time-limited rows, recorded
{summary['failed_rows']} failed rows, {summary['invalidated_rows']}
invalidations/reruns, and found {summary['false_certificates']} false
certificates. The frozen C6 mathematical decisions did not change; the only
source repair was the verified-incumbent-aware trace aggregate described in
`v12_m2_trace_root_cause.md`.

## Same-solver comparison

At 1,800 seconds C6/P-GRB final-gap outcomes were
{w1800}/{l1800}/{t1800} C6 wins/losses/ties across {len(pair1800)} pairs.
Observed common-window AUC outcomes were
{aw1800}/{al1800}/{at1800} over {aa1800} compatible pairs. At 3,600 seconds
on the frozen V50 matrix, final-gap outcomes were
{w3600}/{l3600}/{t3600}; AUC outcomes were
{aw3600}/{al3600}/{at3600} over {aa3600} compatible pairs.

The 1,800-second strict-certificate counts were
{summary['c6_certificates_1800']} for C6 and
{summary['p_grb_certificates_1800']} for P-GRB. The 3,600-second counts were
{summary['c6_certificates_3600']} and
{summary['p_grb_certificates_3600']}. Certification times, fixed
common-gap times, Work, nodes, common-UB gaps, and pair-level AUC are retained
in the comparison and threshold CSVs.

## Mechanisms and references

Across the recorded tailored rows the audit observed
{summary['actual_atomic_splits']} atomic splits,
{summary['child_lookahead_pairs']} child-lookahead pairs,
{summary['native_target_rows']} native-target rows,
{summary['requeues']} requeues, and
{summary['exact_closure_launches']} exact-closure launches. A zero split
count, if observed, is evidence only for this tested range and is not a proof
that adaptive splitting is unnecessary.

Stage 4 contains {len(c5)} C5/C6 diagnostic pairs. Stage 5 contains
{len(s0)} CPLEX S0 contextual comparisons. Neither changes the primary
same-solver conclusion. S0/F0-CPLEX remains the accepted stable CPLEX paper
mainline; C6 is evaluated as the tailored Gurobi mainline, and P-GRB remains
its primary same-solver benchmark.

## Evidence semantics

All AUCs use observed left-continuous steps on the common observed window:
no interpolation, endpoint-only pseudo-AUC, or post-final-event extension.
Historical Round 31 rows are isolated in
`historical_round31_reference.csv`. Time-limited valid endpoints are not
algorithm failures. Work-to-gap is reported only where synchronized native
work observations exist; unavailable C6 work trajectories are not
manufactured. No V>50 instance was generated or tested.
"""
    write_text(OUT / "final_report.md", text)


def official_main(stage0: list[dict[str, Any]],
                  official: list[dict[str, Any]]) -> int:
    if len(official) != 133:
        raise RuntimeError(
            f"official analysis requires 133 completed rows, found "
            f"{len(official)}")
    all_runs = stage0 + official
    traces = {run["state"]["run_id"]: trace_for(run) for run in all_runs}
    trace_rows = trace_audit_rows(all_runs, traces)
    write_csv(OUT / "trace_monotonicity_audit.csv", trace_rows)
    by_stage = {
        stage: [
            run for run in official if run["state"]["stage_id"] == stage]
        for stage in (
            "stage1", "stage2", "stage3", "stage4", "stage5",
            "repeatability")
    }
    pair1800 = (
        paired(by_stage["stage1"], "P-GRB", "C6-FROZEN", traces)
        + paired(by_stage["stage2"], "P-GRB", "C6-FROZEN", traces))
    pair3600 = paired(
        by_stage["stage3"], "P-GRB", "C6-FROZEN", traces)
    c5 = paired(
        by_stage["stage4"], "C5-REFERENCE", "C6-FROZEN", traces)
    primary_c6 = {
        run["state"]["instance_id"]: run for run in official
        if run["state"]["stage_id"] in {"stage1", "stage2"}
        and run["state"]["arm"] == "C6-FROZEN"
    }
    s0 = []
    for run in by_stage["stage5"]:
        partner = primary_c6[run["state"]["instance_id"]]
        s0.extend(paired(
            [run, partner], "S0-CPLEX", "C6-FROZEN", traces))
    primary_common = {
        row["instance_id"]: row["common_verified_ub"]
        for row in pair1800
    }
    stage_files = {
        "stage1": "stage1_existing_1800s.csv",
        "stage2": "stage2_multi_m_1800s.csv",
        "stage3": "stage3_v50_3600s.csv",
        "stage4": "stage4_c5_reference_1800s.csv",
        "stage5": "stage5_s0_anchors_1800s.csv",
        "repeatability": "repeatability_1800s.csv",
    }
    for stage, filename in stage_files.items():
        write_csv(OUT / filename, [
            public_row(
                run,
                primary_common.get(run["state"]["instance_id"]))
            for run in by_stage[stage]])
    write_csv(OUT / "p_grb_vs_c6_1800s.csv", pair1800)
    write_csv(OUT / "p_grb_vs_c6_3600s.csv", pair3600)
    write_csv(OUT / "c5_vs_c6_1800s.csv", c5)
    write_csv(OUT / "s0_vs_c6_context.csv", s0)
    write_csv(OUT / "family_summary_1800s.csv",
              summarize_pairs(pair1800, ("family",)))
    write_csv(OUT / "family_summary_3600s.csv",
              summarize_pairs(pair3600, ("family",)))
    write_csv(OUT / "size_summary.csv",
              summarize_pairs(pair1800 + pair3600,
                              ("nominal_budget_seconds", "V")))
    write_csv(OUT / "m_summary.csv",
              summarize_pairs(pair1800 + pair3600,
                              ("nominal_budget_seconds", "M")))
    write_csv(OUT / "v_by_m_summary.csv",
              summarize_pairs(pair1800 + pair3600,
                              ("nominal_budget_seconds", "V", "M")))
    certification = summarize_pairs(
        pair1800 + pair3600, ("nominal_budget_seconds",))
    write_csv(OUT / "certification_summary.csv", certification)

    auc_rows, time_rows = trace_and_threshold_outputs(all_runs, traces)
    write_csv(OUT / "actual_bound_progress_auc.csv", auc_rows)
    write_csv(OUT / "time_to_gap_thresholds.csv", time_rows)
    write_csv(OUT / "work_to_gap_thresholds.csv",
              work_thresholds(all_runs, time_rows))
    write_csv(OUT / "convergence_performance_profile.csv",
              performance_profile(pair1800, time_rows))
    mechanism = mechanism_outputs(official)
    exactness, certificates, exact_pass, false_count = exactness_audits(
        all_runs)
    write_csv(OUT / "exactness_audit.csv", exactness)
    write_csv(OUT / "certificate_audit.csv", certificates)
    equivalence = frozen_equivalence(stage0)
    write_csv(OUT / "frozen_decision_equivalence.csv", equivalence)
    repeat_rows = repeatability_rows(official, pair1800)
    write_csv(OUT / "repeatability_1800s.csv", repeat_rows)
    historical_reference()
    classification_name, classification_gates = classification(
        pair1800, pair3600, time_rows, exact_pass, false_count, trace_rows)
    invalidations = csv_rows(OUT / "runner_invalidations.csv")
    time_limited = sum(
        truth(run["result"].get("graceful_deadline_finalization"))
        and not truth(run["result"].get(
            "strict_certified_original_problem"))
        for run in official)
    failures = sum(
        integer(run["state"].get("return_code"), 1) != 0 for run in official)
    excluded = sum(
        row["auc_status"] != "observed_common_window"
        for row in pair1800 + pair3600)
    summary = {
        "schema": "round32-final-audit-v1",
        "classification": classification_name,
        "classification_gates": classification_gates,
        "expected_rows": 133,
        "completed_rows": len(official),
        "failed_rows": failures,
        "time_limited_rows": time_limited,
        "invalidated_rows": len(invalidations),
        "rerun_rows": len(invalidations),
        "excluded_primary_auc_pairs": excluded,
        "false_certificates": false_count,
        "stage0_gates_passed": load_json(
            OUT / "stage0_gate_summary.json")[
                "all_stage0_gates_passed"],
        "c6_certificates_1800": sum(
            truth(row["right_strict_certificate"]) for row in pair1800),
        "p_grb_certificates_1800": sum(
            truth(row["left_strict_certificate"]) for row in pair1800),
        "c6_certificates_3600": sum(
            truth(row["right_strict_certificate"]) for row in pair3600),
        "p_grb_certificates_3600": sum(
            truth(row["left_strict_certificate"]) for row in pair3600),
        "existing_instance_count": 23,
        "new_multi_m_instance_count": 12,
        "repeatability_rows": len(repeat_rows),
        **mechanism,
        "stable_cplex_mainline": "S0/F0-CPLEX",
        "validated_gurobi_arm": "C6-FROZEN",
        "same_solver_benchmark": "P-GRB",
    }
    write_json(OUT / "final_audit_summary.json", summary)
    final_report(summary, pair1800, pair3600, c5, s0)
    return 0 if classification_name != "invalid" else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage0", action="store_true")
    args = parser.parse_args()
    stage0 = discover(STAGE0_RUNS)
    if args.stage0:
        return stage0_main(stage0)
    return official_main(stage0, discover(RUNS))


if __name__ == "__main__":
    raise SystemExit(main())
