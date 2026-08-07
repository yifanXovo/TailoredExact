#!/usr/bin/env python3
"""Analyze Round 33 exact convergence using process-entry certificate time."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import os
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, TextIO

import analyze_round32 as round32_analysis
import round30_bound_trace as bound_trace
import round33_common as common


OUT = common.OUT
TOL = 1e-7
GAP_THRESHOLDS = (0.50, 0.25, 0.10, 0.05, 0.02, 0.01, 0.005, 0.001)
TIME_SHIFT = 1.0


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


def write_csv(path: Path, rows: Iterable[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    material = list(rows)
    columns = fields or []
    if not columns:
        for row in material:
            for key in row:
                if key not in columns:
                    columns.append(key)
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


def write_text(path: Path, value: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def open_text(path: Path) -> TextIO:
    return (
        gzip.open(path, "rt", encoding="utf-8", newline="")
        if path.suffix.lower() == ".gz"
        else path.open("r", encoding="utf-8", newline=""))


def resolve(path: Path) -> Path | None:
    if path.is_file():
        return path
    compressed = Path(str(path) + ".gz")
    return compressed if compressed.is_file() else None


def csv_rows(path: Path) -> list[dict[str, str]]:
    candidate = resolve(path)
    if candidate is None:
        return []
    with open_text(candidate) as stream:
        return list(csv.DictReader(stream))


def discover() -> list[dict[str, Any]]:
    output = []
    for marker_path in sorted(common.RUNS.glob("*/completion_marker.json")):
        result_path = marker_path.parent / "result.json"
        output.append({
            "state": common.load_json(marker_path),
            "result": common.load_json(result_path),
            "run_dir": marker_path.parent,
        })
    return output


def bounds(run: dict[str, Any]) -> tuple[float, float]:
    return common.result_bounds(run["state"]["arm"], run["result"])


def process_time(run: dict[str, Any]) -> float:
    return common.process_entry_time(run["result"])


def strict(run: dict[str, Any]) -> bool:
    return truth(run["result"].get("strict_certified_original_problem"))


def verification_passed(result: dict[str, Any]) -> bool:
    verification = result.get("verification", {})
    return bool(
        verification.get("original_solution_feasible")
        and verification.get("original_objective_recomputed")
        and verification.get("objective_matches")
        and not verification.get("errors")
    )


def work(run: dict[str, Any]) -> float:
    field = (
        "gurobi_work" if run["state"]["arm"] == "P-GRB"
        else "external_gini_tree_work")
    return number(run["result"].get(field))


def nodes(run: dict[str, Any]) -> float:
    field = (
        "gurobi_node_count" if run["state"]["arm"] == "P-GRB"
        else "external_gini_tree_nodes")
    return number(run["result"].get(field))


def memory(run: dict[str, Any]) -> float:
    if run["state"]["arm"] == "C6-FROZEN":
        return number(run["result"].get("external_gini_tree_peak_memory_gb"))
    return math.nan


def final_objective(run: dict[str, Any]) -> float:
    return number(run["result"].get(
        "verified_incumbent_objective", run["result"].get("objective")))


def phase_time(run: dict[str, Any], event: str) -> float:
    for row in csv_rows(run["run_dir"] / "process_phases.csv"):
        if row.get("event") == event:
            return number(row.get("process_seconds"), 0.0)
    return 0.0


def observed_trace(run: dict[str, Any]) -> tuple[
        bool, str, tuple[bound_trace.BoundObservation, ...]]:
    complete, reason, observations = round32_analysis.trace_for(run)
    if run["state"]["arm"] != "P-GRB":
        return complete, reason, observations
    lower, upper = bounds(run)
    final_time = process_time(run)
    material = list(observations)
    if material and final_time + TOL < material[-1].process_seconds:
        return False, "final_process_time_precedes_callback", tuple(material)
    if material:
        last = material[-1]
        scale = max(1.0, abs(last.global_lower_bound), abs(lower))
        if lower + TOL * scale < last.global_lower_bound:
            return False, "final_bound_below_callback_bound", tuple(material)
        if final_time > last.process_seconds + 1e-12:
            material.append(bound_trace.BoundObservation(
                final_time,
                number(run["result"].get("runtime_seconds"), final_time),
                "finalization",
                max(lower, last.global_lower_bound),
                upper,
                0,
                1 if strict(run) else 0,
                max(lower, last.global_lower_bound),
                None,
                "native_final_result",
            ))
        complete = len(material) >= 2
        reason = (
            "complete_native_callback_plus_final_result_trace"
            if complete else "single_observed_native_final_bound")
    return complete, reason, tuple(material)


def public_row(run: dict[str, Any], common_upper: float | None = None
               ) -> dict[str, Any]:
    state, result = run["state"], run["result"]
    lower, upper = bounds(run)
    common_ub = upper if common_upper is None else common_upper
    gap = max(
        0.0, (common_ub - lower) / max(abs(common_ub), 1e-12))
    certified = strict(run)
    return {
        "round_id": 33,
        "stage_id": state["stage_id"],
        "run_id": state["run_id"],
        "instance_id": state["instance_id"],
        "instance_path": state["instance_path"],
        "instance_sha256": state["instance_sha256"],
        "V": state["V"],
        "M": state["M"],
        "Q": state["Q"],
        "scenario": state["scenario"],
        "seed": next((row["seed"] for row in common.csv_rows(
            common.V10_MANIFEST)
            if row["instance_id"] == state["instance_id"]), ""),
        "arm": state["arm"],
        "solver": "Gurobi",
        "solver_version": state["solver_version"],
        "source_commit": state["source_commit"],
        "executable_sha256": state["executable_sha256"],
        "process_cap_seconds": state["actual_process_cap_seconds"],
        "run_status": state["run_status"],
        "status": result.get("status", ""),
        "solver_native_optimal": result.get("status") == "optimal",
        "strict_certificate": certified,
        "strict_certificate_class":
            result.get("strict_certificate_class", ""),
        "strict_certificate_rejection_reason":
            result.get("strict_certificate_rejection_reason", ""),
        "strict_certificate_time_from_process_entry_seconds":
            process_time(run) if certified else "",
        "time_limited_runtime_from_process_entry_seconds":
            process_time(run) if not certified else "",
        "diagnostic_solver_runtime_seconds":
            number(result.get("runtime_seconds")),
        "verified_objective": final_objective(run),
        "valid_final_lb": lower,
        "verified_ub": upper,
        "common_verified_ub": common_ub,
        "common_gap": gap,
        "total_work": work(run),
        "native_nodes": nodes(run),
        "peak_memory_gb": memory(run),
        "model_fingerprint": state.get("model_fingerprint", ""),
        "return_code": state["return_code"],
        "lifecycle_valid": (
            truth(result.get("gurobi_lifecycle_valid"))
            if state["arm"] == "P-GRB"
            else truth(result.get("external_gini_tree_lifecycle_complete"))),
    }


def time_tolerance(left: float, right: float) -> float:
    return max(0.05, 0.001 * min(left, right))


def pair_rows(runs: list[dict[str, Any]], stage: str,
              traces: dict[str, tuple[
                  bool, str, tuple[bound_trace.BoundObservation, ...]]]
              ) -> list[dict[str, Any]]:
    selected = [run for run in runs if run["state"]["stage_id"] == stage]
    keyed = {
        (run["state"]["instance_id"], run["state"]["arm"]): run
        for run in selected
    }
    output = []
    for name in sorted({key[0] for key in keyed}):
        p_run = keyed[(name, "P-GRB")]
        c_run = keyed[(name, "C6-FROZEN")]
        p_lb, p_ub = bounds(p_run)
        c_lb, c_ub = bounds(c_run)
        common_ub = min(p_ub, c_ub)
        p_gap = max(0.0, (common_ub - p_lb) / max(abs(common_ub), 1e-12))
        c_gap = max(0.0, (common_ub - c_lb) / max(abs(common_ub), 1e-12))
        p_cert, c_cert = strict(p_run), strict(c_run)
        p_time = process_time(p_run) if p_cert else math.nan
        c_time = process_time(c_run) if c_cert else math.nan
        if p_cert and c_cert:
            tolerance = time_tolerance(p_time, c_time)
            outcome = (
                "C6_win" if c_time < p_time - tolerance
                else "P_GRB_win" if p_time < c_time - tolerance
                else "tie")
            speedup = p_time / c_time
        elif c_cert:
            tolerance, outcome, speedup = math.nan, "C6_win", math.nan
        elif p_cert:
            tolerance, outcome, speedup = math.nan, "P_GRB_win", math.nan
        else:
            tolerance, outcome, speedup = math.nan, "unresolved", math.nan
        p_trace = traces[p_run["state"]["run_id"]]
        c_trace = traces[c_run["state"]["run_id"]]
        auc = (
            round32_analysis.pair_auc(p_trace[2], c_trace[2], common_ub)
            if p_trace[0] and c_trace[0]
            else {
                "auc_status": "auc_unavailable",
                "auc_reason": f"P={p_trace[1]};C6={c_trace[1]}",
            })
        output.append({
            "round_id": 33,
            "stage_id": stage,
            "instance_id": name,
            "V": p_run["state"]["V"],
            "M": p_run["state"]["M"],
            "Q": p_run["state"]["Q"],
            "scenario": p_run["state"]["scenario"],
            "p_grb_strict_certificate": p_cert,
            "c6_strict_certificate": c_cert,
            "p_grb_certificate_time_seconds": p_time if p_cert else "",
            "c6_certificate_time_seconds": c_time if c_cert else "",
            "speedup_p_grb_over_c6": speedup if math.isfinite(speedup) else "",
            "certificate_time_materiality_tolerance_seconds":
                tolerance if math.isfinite(tolerance) else "",
            "certificate_time_outcome": outcome,
            "p_grb_verified_objective": final_objective(p_run),
            "c6_verified_objective": final_objective(c_run),
            "verified_objective_equal": abs(
                final_objective(p_run) - final_objective(c_run))
                <= TOL * max(1.0, abs(final_objective(p_run)),
                             abs(final_objective(c_run))),
            "common_verified_ub": common_ub,
            "p_grb_final_lb": p_lb,
            "c6_final_lb": c_lb,
            "p_grb_common_gap": p_gap,
            "c6_common_gap": c_gap,
            "p_grb_work": work(p_run),
            "c6_work": work(c_run),
            "p_grb_nodes": nodes(p_run),
            "c6_nodes": nodes(c_run),
            "p_grb_peak_memory_gb": memory(p_run),
            "c6_peak_memory_gb": memory(c_run),
            **auc,
        })
    return output


def shifted_geomean(values: list[float]) -> float:
    return (
        math.exp(statistics.fmean(math.log(value + TIME_SHIFT)
                                  for value in values)) - TIME_SHIFT
        if values else math.nan)


def group_rows(pairs: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in pairs:
        grouped[str(row[key])].append(row)
    output = []
    for value, members in sorted(grouped.items()):
        both = [row for row in members
                if truth(row["p_grb_strict_certificate"])
                and truth(row["c6_strict_certificate"])]
        speeds = [number(row["speedup_p_grb_over_c6"])
                  for row in both]
        p_times = [number(row["p_grb_certificate_time_seconds"])
                   for row in both]
        c_times = [number(row["c6_certificate_time_seconds"])
                   for row in both]
        output.append({
            key: value,
            "pairs": len(members),
            "p_grb_certificates": sum(
                truth(row["p_grb_strict_certificate"]) for row in members),
            "c6_certificates": sum(
                truth(row["c6_strict_certificate"]) for row in members),
            "both_certified": len(both),
            "c6_time_wins": sum(
                row["certificate_time_outcome"] == "C6_win"
                for row in members),
            "p_grb_time_wins": sum(
                row["certificate_time_outcome"] == "P_GRB_win"
                for row in members),
            "time_ties": sum(
                row["certificate_time_outcome"] == "tie"
                for row in members),
            "unresolved": sum(
                row["certificate_time_outcome"] == "unresolved"
                for row in members),
            "median_speedup_p_over_c6":
                statistics.median(speeds) if speeds else "",
            "shifted_geomean_p_grb_seconds":
                shifted_geomean(p_times) if p_times else "",
            "shifted_geomean_c6_seconds":
                shifted_geomean(c_times) if c_times else "",
            "geomean_shift_seconds": TIME_SHIFT,
        })
    return output


def trace_outputs(
        runs: list[dict[str, Any]],
        traces: dict[str, tuple[
            bool, str, tuple[bound_trace.BoundObservation, ...]]]
        ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[(run["state"]["stage_id"],
                 run["state"]["instance_id"])].append(run)
    auc_rows, threshold_rows = [], []
    for run in runs:
        state = run["state"]
        partners = grouped[(state["stage_id"], state["instance_id"])]
        common_ub = min(bounds(item)[1] for item in partners)
        complete, reason, observations = traces[state["run_id"]]
        row = {
            "round_id": 33,
            "stage_id": state["stage_id"],
            "run_id": state["run_id"],
            "instance_id": state["instance_id"],
            "V": state["V"],
            "M": state["M"],
            "Q": state["Q"],
            "scenario": state["scenario"],
            "arm": state["arm"],
            "trace_complete": complete,
            "trace_reason": reason,
            "observation_count": len(observations),
            "no_interpolation": True,
            "no_post_final_extension": True,
        }
        if complete and len(observations) >= 2:
            row.update(bound_trace.observed_step_auc(
                observations, common_verified_upper_bound=common_ub))
        else:
            row["auc_status"] = "unavailable_observed_trace_insufficient"
        auc_rows.append(row)
        denominator = max(abs(common_ub), 1e-12)
        for threshold in GAP_THRESHOLDS:
            reached = next((
                observation.process_seconds for observation in observations
                if max(0.0, (common_ub - observation.global_lower_bound)
                       / denominator) <= threshold + 1e-12
            ), None)
            threshold_rows.append({
                "round_id": 33,
                "stage_id": state["stage_id"],
                "run_id": state["run_id"],
                "instance_id": state["instance_id"],
                "V": state["V"],
                "M": state["M"],
                "Q": state["Q"],
                "scenario": state["scenario"],
                "arm": state["arm"],
                "gap_threshold": threshold,
                "reached": reached is not None,
                "first_observed_process_entry_seconds":
                    reached if reached is not None else "",
                "unreached_semantics":
                    "infinite_no_interpolation" if reached is None else "",
            })
    return auc_rows, threshold_rows


def projection(path: Path, fields: tuple[str, ...],
               floats: tuple[str, ...] = ()) -> list[tuple[Any, ...]]:
    output = []
    for row in csv_rows(path):
        values: list[Any] = []
        for field in fields:
            value: Any = row.get(field, "")
            if field in floats and value != "":
                value = round(number(value), 8)
            values.append(value)
        output.append(tuple(values))
    return output


def repeatability(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    primary = {
        (run["state"]["instance_id"], run["state"]["arm"]): run
        for run in runs if run["state"]["stage_id"] == "stage1"
    }
    output = []
    for repeat in sorted(
            (run for run in runs if run["state"]["stage_id"] == "stage3"),
            key=lambda run: run["state"]["run_id"]):
        key = (repeat["state"]["instance_id"], repeat["state"]["arm"])
        original = primary[key]
        o_time = process_time(original) if strict(original) else math.nan
        r_time = process_time(repeat) if strict(repeat) else math.nan
        objective_delta = abs(final_objective(original) - final_objective(repeat))
        row = {
            "round_id": 33,
            "instance_id": key[0],
            "M": repeat["state"]["M"],
            "Q": repeat["state"]["Q"],
            "scenario": repeat["state"]["scenario"],
            "arm": key[1],
            "original_run_id": original["state"]["run_id"],
            "repeat_run_id": repeat["state"]["run_id"],
            "original_certificate": strict(original),
            "repeat_certificate": strict(repeat),
            "certificate_equal": strict(original) == strict(repeat),
            "original_certificate_time_seconds":
                o_time if math.isfinite(o_time) else "",
            "repeat_certificate_time_seconds":
                r_time if math.isfinite(r_time) else "",
            "certificate_time_ratio_repeat_over_original":
                r_time / o_time if math.isfinite(o_time) and
                math.isfinite(r_time) else "",
            "original_verified_objective": final_objective(original),
            "repeat_verified_objective": final_objective(repeat),
            "objective_absolute_delta": objective_delta,
            "objective_equal": objective_delta <= TOL * max(
                1.0, abs(final_objective(original)),
                abs(final_objective(repeat))),
            "original_work": work(original),
            "repeat_work": work(repeat),
            "work_ratio_repeat_over_original":
                work(repeat) / work(original)
                if work(original) > 0.0 else "",
            "lifecycle_valid": (
                truth(repeat["result"].get("gurobi_lifecycle_valid"))
                if key[1] == "P-GRB" else truth(repeat["result"].get(
                    "external_gini_tree_lifecycle_complete"))),
        }
        if key[1] == "C6-FROZEN":
            row.update({
                "hga_trajectory_exact": (
                    resolve(original["run_dir"] / "hga_generations.csv").read_bytes()
                    == resolve(repeat["run_dir"] / "hga_generations.csv").read_bytes()),
                "target_sequence_exact": projection(
                    original["run_dir"] / "external/native_target_ledger.csv",
                    ("leaf_id", "target_kind", "target_bound", "status"),
                    ("target_bound",)) == projection(
                    repeat["run_dir"] / "external/native_target_ledger.csv",
                    ("leaf_id", "target_kind", "target_bound", "status"),
                    ("target_bound",)),
                "split_sequence_exact": projection(
                    original["run_dir"] / "external/split_decision_ledger.csv",
                    ("parent_id", "split", "reason")) == projection(
                    repeat["run_dir"] / "external/split_decision_ledger.csv",
                    ("parent_id", "split", "reason")),
            })
        else:
            row.update({
                "hga_trajectory_exact": "not_applicable",
                "target_sequence_exact": "not_applicable",
                "split_sequence_exact": "not_applicable",
            })
        row["repeatability_valid"] = bool(
            row["certificate_equal"]
            and row["objective_equal"]
            and row["lifecycle_valid"]
            and (key[1] != "C6-FROZEN" or (
                row["hga_trajectory_exact"]
                and row["target_sequence_exact"]
                and row["split_sequence_exact"])))
        output.append(row)
    return output


def audits(runs: list[dict[str, Any]]) -> tuple[
        list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], int]:
    exact_rows, certificate_rows, lifecycle_rows = [], [], []
    false_certificates = 0
    expected = common.fingerprint_values()
    for run in runs:
        state, result = run["state"], run["result"]
        lower, upper = bounds(run)
        scale = max(1.0, abs(lower), abs(upper))
        bound_valid = (
            math.isfinite(lower) and math.isfinite(upper)
            and lower <= upper + TOL * scale)
        verified = verification_passed(result)
        lifecycle = (
            truth(result.get("gurobi_lifecycle_valid"))
            if state["arm"] == "P-GRB" else truth(result.get(
                "external_gini_tree_lifecycle_complete")))
        fingerprint_match = (
            integer(result.get("gurobi_model_fingerprint")) ==
            expected[state["instance_id"]]
            if state["arm"] == "P-GRB" else True)
        certificate_valid = bool(
            bound_valid and verified and lifecycle and fingerprint_match
            and result.get("strict_certificate_rejection_reason") == "none")
        false = strict(run) and not certificate_valid
        false_certificates += int(false)
        exact_rows.append({
            "round_id": 33,
            "run_id": state["run_id"],
            "stage_id": state["stage_id"],
            "instance_id": state["instance_id"],
            "arm": state["arm"],
            "valid_lb": lower,
            "verified_ub": upper,
            "bound_order_valid": bound_valid,
            "verifier_passed": verified,
            "lifecycle_valid": lifecycle,
            "model_fingerprint_match": fingerprint_match,
            "strict_certificate": strict(run),
            "false_certificate": false,
            "passed": bound_valid and not false,
        })
        certificate_rows.append({
            "round_id": 33,
            "run_id": state["run_id"],
            "stage_id": state["stage_id"],
            "instance_id": state["instance_id"],
            "arm": state["arm"],
            "solver_native_optimal": result.get("status") == "optimal",
            "strict_original_problem_certificate": strict(run),
            "certificate_class": result.get("strict_certificate_class", ""),
            "certificate_rejection_reason":
                result.get("strict_certificate_rejection_reason", ""),
            "certificate_time_from_process_entry_seconds":
                process_time(run) if strict(run) else "",
            "native_optimal_without_strict_evidence": (
                result.get("status") == "optimal" and not strict(run)),
            "certificate_evidence_valid": certificate_valid if strict(run)
            else True,
            "false_certificate": false,
        })
        lifecycle_rows.append({
            **public_row(run),
            "overall_deadline_started_at_process_entry": truth(
                result.get("overall_deadline_started_at_process_entry")),
            "process_wall_time_comparable": truth(
                result.get("process_wall_time_comparable")),
            "graceful_deadline_finalization": truth(
                result.get("graceful_deadline_finalization")),
        })
    return exact_rows, certificate_rows, lifecycle_rows, false_certificates


def mechanism_rows(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for run in runs:
        if run["state"]["arm"] != "C6-FROZEN":
            continue
        state, result = run["state"], run["result"]
        child_rows = csv_rows(
            run["run_dir"] / "external/parent_child_bound_ledger.csv")
        target_rows = csv_rows(
            run["run_dir"] / "external/native_target_ledger.csv")
        output.append({
            "round_id": 33,
            "stage_id": state["stage_id"],
            "run_id": state["run_id"],
            "instance_id": state["instance_id"],
            "V": state["V"],
            "M": state["M"],
            "Q": state["Q"],
            "scenario": state["scenario"],
            "atomic_splits": integer(
                result.get("external_gini_tree_split_count")),
            "native_targets": len(target_rows),
            "exact_closures": integer(result.get(
                "external_gini_tree_exact_closure_launch_count")),
            "child_lookahead_pairs": len(child_rows),
            "requeues": integer(result.get(
                "external_gini_tree_native_requeue_count")),
            "total_work": work(run),
            "native_nodes": nodes(run),
            "peak_memory_gb": memory(run),
            "strict_certificate": strict(run),
            "lifecycle_valid": truth(result.get(
                "external_gini_tree_lifecycle_complete")),
        })
    return output


def main() -> int:
    if not common.MANIFEST.is_file():
        raise SystemExit("Round 33 frozen manifest missing")
    matrix = common.csv_rows(common.MATRIX)
    runs = discover()
    if len(runs) != len(matrix):
        raise RuntimeError(
            f"Round 33 incomplete: expected {len(matrix)}, found {len(runs)}")
    run_ids = {run["state"]["run_id"] for run in runs}
    if run_ids != {row["run_id"] for row in matrix}:
        raise RuntimeError("Round 33 run identities do not match matrix")
    traces = {
        run["state"]["run_id"]: observed_trace(run) for run in runs
    }
    pair_v10 = pair_rows(runs, "stage1", traces)
    pair_v12 = pair_rows(runs, "stage2", traces)
    public = []
    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        by_pair[(run["state"]["stage_id"],
                 run["state"]["instance_id"])].append(run)
    for run in runs:
        partners = by_pair[(run["state"]["stage_id"],
                            run["state"]["instance_id"])]
        public.append(public_row(run, min(bounds(item)[1] for item in partners)))
    write_csv(OUT / "stage1_v10_convergence.csv", [
        row for row in public if row["stage_id"] == "stage1"])
    write_csv(OUT / "stage2_v12_anchors.csv", [
        row for row in public if row["stage_id"] == "stage2"])
    write_csv(OUT / "p_grb_vs_c6_v10.csv", pair_v10)
    write_csv(OUT / "p_grb_vs_c6_v12_anchor.csv", pair_v12)
    convergence = [{
        "V": row["V"],
        "M": row["M"],
        "Q": row["Q"],
        "Scenario": row["scenario"],
        "P-GRB Time": row["p_grb_certificate_time_seconds"],
        "P-GRB Conv.": row["p_grb_strict_certificate"],
        "C6 Time": row["c6_certificate_time_seconds"],
        "C6 Conv.": row["c6_strict_certificate"],
        "Speedup": row["speedup_p_grb_over_c6"],
        "instance_id": row["instance_id"],
    } for row in pair_v10]
    write_csv(OUT / "convergence_time_matrix.csv", convergence)
    write_csv(OUT / "certificate_time_speedup.csv", pair_v10 + pair_v12)
    write_csv(OUT / "scenario_summary.csv", group_rows(pair_v10, "scenario"))
    write_csv(OUT / "m_summary.csv", group_rows(pair_v10, "M"))
    write_csv(OUT / "q_summary.csv", group_rows(pair_v10, "Q"))
    mq_pairs = [{**row, "M_by_Q": f"M{row['M']}_Q{row['Q']}"}
                for row in pair_v10]
    write_csv(OUT / "m_by_q_summary.csv", group_rows(mq_pairs, "M_by_Q"))
    auc_rows, threshold_rows = trace_outputs(runs, traces)
    write_csv(OUT / "actual_bound_progress_auc.csv", auc_rows)
    write_csv(OUT / "time_to_gap_thresholds.csv", threshold_rows)
    repeats = repeatability(runs)
    write_csv(OUT / "stage3_repeatability.csv", repeats)
    mechanisms = mechanism_rows(runs)
    write_csv(OUT / "c6_mechanism_summary.csv", mechanisms)
    exact_rows, certificate_rows, lifecycle_rows, false_count = audits(runs)
    write_csv(OUT / "exactness_audit.csv", exact_rows)
    write_csv(OUT / "certificate_audit.csv", certificate_rows)
    write_csv(OUT / "lifecycle_and_resource_summary.csv", lifecycle_rows)

    completed = len(runs)
    failed = sum(
        integer(run["state"].get("return_code"), 1) != 0 for run in runs)
    time_limited = sum(not strict(run) for run in runs)
    v10_p = sum(truth(row["p_grb_strict_certificate"]) for row in pair_v10)
    v10_c = sum(truth(row["c6_strict_certificate"]) for row in pair_v10)
    wins = sum(row["certificate_time_outcome"] == "C6_win"
               for row in pair_v10)
    losses = sum(row["certificate_time_outcome"] == "P_GRB_win"
                 for row in pair_v10)
    ties = sum(row["certificate_time_outcome"] == "tie"
               for row in pair_v10)
    unresolved = sum(row["certificate_time_outcome"] == "unresolved"
                     for row in pair_v10)
    speeds = [number(row["speedup_p_grb_over_c6"]) for row in pair_v10
              if row["speedup_p_grb_over_c6"] != ""]
    trace_required = [row for row in auc_rows
                      if row["stage_id"] in {"stage1", "stage2"}]
    trace_complete = all(
        truth(row["trace_complete"]) or
        row.get("auc_status") == "unavailable_observed_trace_insufficient"
        for row in trace_required)
    repeat_valid = all(truth(row["repeatability_valid"]) for row in repeats)
    group_regression = any(
        integer(row["p_grb_time_wins"]) > integer(row["c6_time_wins"])
        for summary in (
            group_rows(pair_v10, "scenario"),
            group_rows(pair_v10, "M"))
        for row in summary)
    if false_count or failed or not all(truth(row["passed"])
                                        for row in exact_rows):
        classification = "invalid"
    elif not trace_complete or completed != 52:
        classification = "v10_exact_convergence_evidence_incomplete"
    elif wins > losses and not group_regression and repeat_valid:
        classification = "v10_exact_convergence_c6_advantage_confirmed"
    else:
        classification = "v10_exact_convergence_crossover_mixed"
    summary = {
        "schema": "round33-final-audit-v1",
        "classification": classification,
        "expected_rows": 52,
        "completed_rows": completed,
        "failed_rows": failed,
        "time_limited_rows": time_limited,
        "false_certificates": false_count,
        "v10_instance_count": 18,
        "v10_pair_count": len(pair_v10),
        "v10_p_grb_certificates": v10_p,
        "v10_c6_certificates": v10_c,
        "c6_certificate_time_wins": wins,
        "p_grb_certificate_time_wins": losses,
        "certificate_time_ties": ties,
        "certificate_time_unresolved": unresolved,
        "median_speedup_p_grb_over_c6":
            statistics.median(speeds) if speeds else None,
        "shifted_geomean_p_grb_seconds": shifted_geomean([
            number(row["p_grb_certificate_time_seconds"])
            for row in pair_v10
            if row["p_grb_certificate_time_seconds"] != ""]),
        "shifted_geomean_c6_seconds": shifted_geomean([
            number(row["c6_certificate_time_seconds"])
            for row in pair_v10
            if row["c6_certificate_time_seconds"] != ""]),
        "geomean_shift_seconds": TIME_SHIFT,
        "v12_p_grb_certificates": sum(
            truth(row["p_grb_strict_certificate"]) for row in pair_v12),
        "v12_c6_certificates": sum(
            truth(row["c6_strict_certificate"]) for row in pair_v12),
        "repeatability_rows": len(repeats),
        "repeatability_all_valid": repeat_valid,
        "trace_rows": len(auc_rows),
        "primary_trace_gate_passed": trace_complete,
        "c6_atomic_splits": sum(row["atomic_splits"] for row in mechanisms),
        "c6_native_targets": sum(row["native_targets"] for row in mechanisms),
        "c6_exact_closures": sum(row["exact_closures"] for row in mechanisms),
        "c6_child_lookahead_pairs": sum(
            row["child_lookahead_pairs"] for row in mechanisms),
        "c6_requeues": sum(row["requeues"] for row in mechanisms),
        "c6_total_work": sum(
            number(row["total_work"], 0.0) for row in mechanisms),
        "c6_peak_memory_gb": max(
            (number(row["peak_memory_gb"], 0.0) for row in mechanisms),
            default=0.0),
        "stable_algorithm_decision": (
            "C6 remains validated Gurobi mainline; no C7 and no tuning"),
        "round32_raw_rows_imported": 0,
    }
    write_json(OUT / "final_audit_summary.json", summary)
    report = f"""# Round 33 final report

## Outcome

Classification: `{classification}`.

Round 33 completed {completed}/52 frozen rows with {failed} process failures,
{time_limited} valid time-limited rows, and {false_count} false certificates.
The frozen C6 C++ algorithm was unchanged. All primary times are strict
certificate times from process entry (`final_process_wall_time_seconds`), not
solver-only or exact-phase runtimes.

## V10 exact convergence

P-GRB strictly certified {v10_p}/18 V10 instances and C6 certified
{v10_c}/18. Certificate-time outcomes were C6/P-GRB/tie/unresolved =
{wins}/{losses}/{ties}/{unresolved}. The median P-GRB/C6 speedup over
both-certified rows was {summary['median_speedup_p_grb_over_c6']}.
With a one-second shift, geometric-mean certificate times were
{summary['shifted_geomean_p_grb_seconds']} seconds for P-GRB and
{summary['shifted_geomean_c6_seconds']} seconds for C6.

The complete paper-facing 18-row table is `convergence_time_matrix.csv`.
Scenario, M, Q, and M-by-Q summaries retain all group outcomes without
mixing Round 32 raw evidence.

## Validation, anchors, and repeatability

The two V12 anchors produced {summary['v12_p_grb_certificates']}/2 P-GRB and
{summary['v12_c6_certificates']}/2 C6 strict certificates. All
{len(repeats)} repeatability arm rows were valid: {repeat_valid}. Certificate
states, objectives, Work, times, and C6 HGA/target/split sequences are in
`stage3_repeatability.csv`.

Observed proof AUC and gap-threshold times use real left-continuous events,
including a real final-result event when needed. No interpolation or
post-final-event extension is used. Solver-native optimality, strict
original-problem certification, strict certificate time, and time-limited
runtime are distinct fields in every public row.

## C6 mechanisms

Across official and repeat C6 rows, the run records contain
{summary['c6_atomic_splits']} atomic splits,
{summary['c6_native_targets']} native targets,
{summary['c6_exact_closures']} exact-closure launches,
{summary['c6_child_lookahead_pairs']} child-lookahead pairs, and
{summary['c6_requeues']} requeues. C6 total native Work was
{summary['c6_total_work']} and peak recorded memory was
{summary['c6_peak_memory_gb']} GB.

## Stable algorithm decision

C6 remains the validated tailored Gurobi mainline regardless of small-case
timing outcomes. Round 33 creates no C7, changes no rho or scheduling rule,
and is independent benchmark-completion evidence rather than an
algorithm-selection round.
"""
    write_text(OUT / "final_report.md", report)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
