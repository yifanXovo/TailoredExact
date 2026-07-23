#!/usr/bin/env python3
"""Analyze frozen Round 30 results using observed-bound trajectories only."""

from __future__ import annotations

import csv
import gzip
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, TextIO

import round30_bound_trace as bound_trace
import run_round30_experiments as frozen


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_c0_mechanism_transfer_c5_round30"
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
    if fields is None:
        fields = list(material[0]) if material else ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)


def phase_time(run_dir: Path, event: str, default: float = 0.0) -> float:
    for row in csv_rows(run_dir / "process_phases.csv"):
        if row.get("event") == event:
            return number(row.get("process_seconds"), default)
    return default


def raw_runs() -> dict[tuple[str, str, str, int], dict[str, Any]]:
    runs: dict[tuple[str, str, str, int], dict[str, Any]] = {}
    for state_path in sorted(RUNS.glob("*/run_state.json")):
        state = load_json(state_path)
        run_dir = state_path.parent
        result_path = run_dir / "result.json"
        result = load_json(result_path) if result_path.is_file() else {}
        key = (
            str(state["stage"]), str(state["instance"]), str(state["arm"]),
            integer(state.get("repetition")))
        runs[key] = {"state": state, "result": result, "run_dir": run_dir}
    return runs


def require_run(runs: dict[tuple[str, str, str, int], dict[str, Any]],
                stage: str, instance: str, arm: str,
                repetition: int = 0) -> dict[str, Any]:
    key = (stage, instance, arm, repetition)
    if key not in runs:
        raise RuntimeError(f"missing official run: {key}")
    return runs[key]


def materialized_stages(
        runs: dict[tuple[str, str, str, int], dict[str, Any]]
        ) -> dict[str, list[dict[str, Any]]]:
    stage1 = [
        require_run(runs, "stage1", instance, arm)
        for instance in frozen.STAGE1_INSTANCES
        for arm in ("C0-DIAG", "C4-CANDIDATE", "C5-CANDIDATE")
    ]
    stage2 = [
        require_run(
            runs,
            "stage1" if (
                arm != "P-GRB" and
                instance in frozen.STAGE1_INSTANCES) else "stage2",
            instance, arm)
        for instance in frozen.PRIMARY
        for arm in ("P-GRB", "C4-CANDIDATE", "C5-CANDIDATE")
    ]
    stage3 = [
        require_run(
            runs,
            "stage3" if arm in {"S0-CPLEX", "C3-REPLICA"} else "stage1",
            instance, arm)
        for instance in frozen.ANCHORS
        for arm in ("S0-CPLEX", "C0-DIAG", "C3-REPLICA",
                    "C4-CANDIDATE", "C5-CANDIDATE")
    ]
    stage4 = [
        require_run(runs, "stage4", instance, "C5-CANDIDATE", repetition)
        for instance in frozen.STAGE4_INSTANCES
        for repetition in (1, 2)
    ]
    return {
        "stage1": stage1, "stage2": stage2,
        "stage3": stage3, "stage4": stage4,
    }


def common_upper_bounds(
        stages: dict[str, list[dict[str, Any]]]) -> dict[str, float]:
    values: dict[str, list[float]] = defaultdict(list)
    for run in stages["stage1"] + stages["stage2"] + stages["stage3"]:
        result = run["result"]
        ub = number(result.get(
            "external_gini_tree_verified_upper_bound",
            result.get("upper_bound")))
        if math.isfinite(ub):
            values[run["state"]["instance"]].append(ub)
    return {instance: min(found) for instance, found in values.items()}


def public_row(run: dict[str, Any], common_ub: float) -> dict[str, Any]:
    state, result = run["state"], run["result"]
    lb = number(result.get(
        "external_gini_tree_global_lower_bound",
        result.get("lower_bound")))
    ub = number(result.get(
        "external_gini_tree_verified_upper_bound",
        result.get("upper_bound")))
    gap = (
        max(0.0, (common_ub - lb) / max(abs(common_ub), 1e-12))
        if math.isfinite(lb) and math.isfinite(common_ub) else math.nan)
    return {
        "source_stage": state["stage"],
        "instance": state["instance"],
        "family": state["family"],
        "V": state["V"],
        "M": state["M"],
        "arm": state["arm"],
        "repetition": state.get("repetition", 0),
        "budget_seconds": state["budget_seconds"],
        "return_code": state["return_code"],
        "emergency_timeout": state["emergency_timeout"],
        "status": result.get("status", "result_missing"),
        "verified_ub": ub,
        "common_verified_ub": common_ub,
        "valid_final_lb": lb,
        "common_ub_gap": gap,
        "strict_certificate":
            truth(result.get("strict_certified_original_problem")),
        "runtime_seconds": number(result.get("runtime_seconds")),
        "root_coverage_valid":
            truth(result.get("external_gini_tree_root_coverage_valid")),
        "parent_child_coverage_valid":
            truth(result.get(
                "external_gini_tree_parent_child_coverage_valid")),
        "all_relevant_leaves_closed":
            truth(result.get(
                "external_gini_tree_all_relevant_leaves_closed")),
        "all_leaf_bounds_valid":
            truth(result.get("external_gini_tree_all_leaf_bounds_valid")),
        "global_bound_monotone":
            truth(result.get("external_gini_tree_global_bound_monotone")),
        "leaf_bounds_monotone":
            truth(result.get("external_gini_tree_leaf_bounds_monotone")),
        "lifecycle_complete":
            truth(result.get("external_gini_tree_lifecycle_complete")),
        "failure_reason":
            result.get("external_gini_tree_failure_reason", "none"),
        "run_id": state["run_id"],
        "run_path": run["run_dir"].relative_to(ROOT).as_posix(),
    }


def legacy_observed_trace(run: dict[str, Any]) -> tuple[
        bool, str, tuple[bound_trace.BoundObservation, ...]]:
    state, result, run_dir = run["state"], run["result"], run["run_dir"]
    arm = state["arm"]
    if arm == "P-GRB":
        rows = csv_rows(run_dir / "progress.csv")
        launch = phase_time(run_dir, "plain_gurobi_optimize_launch")
        observations = []
        last = -math.inf
        for row in rows:
            if not truth(row.get("best_bound_available")):
                continue
            value = number(row.get("best_bound"))
            elapsed = number(row.get("elapsed_runtime_seconds"))
            if not math.isfinite(value) or abs(value) >= 1e50:
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
            if len(observations) >= 2 else "too_few_native_callback_bounds",
            tuple(observations))
    if arm == "C3-REPLICA":
        rows = csv_rows(run_dir / "external/global_bound_trace.csv")
        offset = phase_time(run_dir, "first_external_tree_event")
        observations = []
        last = -math.inf
        for row in rows:
            value = number(row.get("global_lb"))
            elapsed = number(row.get("telemetry_seconds"))
            upper = number(row.get("verified_ub"))
            if not math.isfinite(value) or not math.isfinite(elapsed):
                continue
            if value + TOL < last:
                return False, "c3_global_bound_nonmonotone", ()
            last = max(last, value)
            observations.append(bound_trace.BoundObservation(
                offset + elapsed, elapsed, str(row.get("event")),
                last, upper, 0, 0, last, None,
                "c3_existing_observed_global_trace"))
        return (
            len(observations) >= 2,
            "compatible_existing_c3_trace"
            if len(observations) >= 2 else "too_few_c3_observations",
            tuple(observations))
    return False, "unsupported_legacy_trace_arm", ()


def trace_for(run: dict[str, Any]) -> tuple[
        bool, str, tuple[bound_trace.BoundObservation, ...], int]:
    arm = run["state"]["arm"]
    if arm in {"C0-DIAG", "C4-CANDIDATE", "C5-CANDIDATE"}:
        audit = bound_trace.audit_external_trace(
            run["run_dir"] / "external/global_bound_trace.csv")
        return (
            audit.complete, audit.reason, audit.observations,
            audit.bound_observation_count)
    if arm in {"P-GRB", "C3-REPLICA"}:
        complete, reason, observations = legacy_observed_trace(run)
        return complete, reason, observations, len(observations)
    return False, "auc_not_required_for_arm", (), 0


def value_at(
        observations: tuple[bound_trace.BoundObservation, ...],
        time_value: float) -> float:
    value = observations[0].global_lower_bound
    for item in observations:
        if item.process_seconds > time_value + 1e-12:
            break
        value = item.global_lower_bound
    return value


def common_window_pair_auc(
        left: tuple[bound_trace.BoundObservation, ...],
        right: tuple[bound_trace.BoundObservation, ...],
        common_ub: float) -> dict[str, Any]:
    start = max(left[0].process_seconds, right[0].process_seconds)
    end = min(left[-1].process_seconds, right[-1].process_seconds)
    if end <= start:
        return {"auc_status": "auc_unavailable",
                "auc_reason": "no_positive_common_observed_window"}
    times = sorted({
        start, end,
        *(row.process_seconds for row in left
          if start < row.process_seconds < end),
        *(row.process_seconds for row in right
          if start < row.process_seconds < end),
    })
    left_area = right_area = 0.0
    left_lb_area = right_lb_area = 0.0
    denominator = max(abs(common_ub), 1e-12)
    for begin, finish in zip(times, times[1:]):
        duration = finish - begin
        left_value = value_at(left, begin)
        right_value = value_at(right, begin)
        left_lb_area += duration * left_value
        right_lb_area += duration * right_value
        left_area += duration * max(
            0.0, min(1.0, 1.0 - (common_ub - left_value) / denominator))
        right_area += duration * max(
            0.0, min(1.0, 1.0 - (common_ub - right_value) / denominator))
    duration = end - start
    return {
        "auc_status": "observed_common_window",
        "auc_reason": "no_interpolation_no_post_last_event_extension",
        "common_window_start_process_seconds": start,
        "common_window_end_process_seconds": end,
        "common_window_duration_seconds": duration,
        "left_mean_valid_lower_bound": left_lb_area / duration,
        "right_mean_valid_lower_bound": right_lb_area / duration,
        "left_normalized_proof_auc": left_area / duration,
        "right_normalized_proof_auc": right_area / duration,
        "normalized_proof_auc_delta_right_minus_left":
            (right_area - left_area) / duration,
    }


def pair_rows(
        stage_rows: list[dict[str, Any]], left_arm: str, right_arm: str,
        common_ubs: dict[str, float],
        traces: dict[str, tuple[bool, str, tuple[
            bound_trace.BoundObservation, ...], int]]) -> list[dict[str, Any]]:
    keyed = {
        (run["state"]["instance"], run["state"]["arm"]): run
        for run in stage_rows
    }
    output = []
    for instance in sorted({
            item for item, arm in keyed
            if arm == left_arm and (item, right_arm) in keyed}):
        left, right = keyed[(instance, left_arm)], keyed[(instance, right_arm)]
        left_public = public_row(left, common_ubs[instance])
        right_public = public_row(right, common_ubs[instance])
        left_trace = traces[left["state"]["run_id"]]
        right_trace = traces[right["state"]["run_id"]]
        auc = (
            common_window_pair_auc(
                left_trace[2], right_trace[2], common_ubs[instance])
            if left_trace[0] and right_trace[0]
            else {
                "auc_status": "auc_unavailable",
                "auc_reason":
                    f"left={left_trace[1]};right={right_trace[1]}"})
        output.append({
            "instance": instance,
            "family": left["state"]["family"],
            "left_arm": left_arm,
            "right_arm": right_arm,
            "common_verified_ub": common_ubs[instance],
            "left_final_lb": left_public["valid_final_lb"],
            "right_final_lb": right_public["valid_final_lb"],
            "final_lb_delta_right_minus_left":
                right_public["valid_final_lb"] - left_public["valid_final_lb"],
            "left_common_gap": left_public["common_ub_gap"],
            "right_common_gap": right_public["common_ub_gap"],
            "left_strict_certificate": left_public["strict_certificate"],
            "right_strict_certificate": right_public["strict_certificate"],
            **auc,
        })
    return output


def threshold_rows(
        run: dict[str, Any], observations: tuple[
            bound_trace.BoundObservation, ...],
        common_ub: float) -> list[dict[str, Any]]:
    output = []
    for threshold in (0.90, 0.75, 0.50, 0.25, 0.10, 0.05, 0.01):
        reached = next((
            item.process_seconds for item in observations
            if (common_ub - item.global_lower_bound) /
               max(abs(common_ub), 1e-12) <= threshold + 1e-12), None)
        output.append({
            "run_id": run["state"]["run_id"],
            "instance": run["state"]["instance"],
            "arm": run["state"]["arm"],
            "common_gap_threshold": threshold,
            "reached": reached is not None,
            "first_observed_process_seconds": (
                reached if reached is not None else ""),
            "no_interpolation": True,
        })
    return output


def result_metric(run: dict[str, Any], name: str,
                  default: Any = 0) -> Any:
    return run["result"].get(f"external_gini_tree_{name}", default)


def mechanism_rows(
        official: list[dict[str, Any]],
        traces: dict[str, tuple[bool, str, tuple[
            bound_trace.BoundObservation, ...], int]]
        ) -> dict[str, list[dict[str, Any]]]:
    roots, partials, splits, terminals, reuse, lifecycle = [], [], [], [], [], []
    for run in official:
        state, result, run_dir = run["state"], run["result"], run["run_dir"]
        trace = traces.get(state["run_id"], (False, "", (), 0))[2]
        previous = None
        for observation in trace:
            gain = (
                observation.global_lower_bound -
                previous.global_lower_bound if previous else 0.0)
            base = {
                "run_id": state["run_id"],
                "instance": state["instance"],
                "arm": state["arm"],
                "process_seconds": observation.process_seconds,
                "event_type": observation.event_type,
                "valid_global_lb": observation.global_lower_bound,
                "immediate_global_lb_gain": max(0.0, gain),
                "event_source": observation.event_source,
            }
            if observation.event_type == "native_root_processing_bound":
                roots.append(base)
            if observation.event_type in {
                    "partial_native_mip_bound_improvement",
                    "partial_native_bound_target"}:
                partials.append(base)
            previous = observation
        for row in csv_rows(run_dir / "external/split_decision_ledger.csv"):
            splits.append({
                "run_id": state["run_id"], "instance": state["instance"],
                "arm": state["arm"], **row})
        for row in csv_rows(run_dir / "external/paper_optimize_ledger.csv"):
            if row.get("solve_kind") in {"MIP", "PARTIAL_MIP_TARGET"}:
                terminals.append({
                    "run_id": state["run_id"],
                    "instance": state["instance"],
                    "arm": state["arm"], **row})
        reuse.append({
            "run_id": state["run_id"], "instance": state["instance"],
            "arm": state["arm"],
            "model_reads": result_metric(run, "model_read_count"),
            "model_count": result_metric(run, "model_count"),
            "in_memory_model_reuse":
                result_metric(run, "in_memory_model_reuse_count"),
            "basis_available": result_metric(run, "basis_available_count"),
            "basis_mapped": result_metric(run, "basis_mapped_count"),
            "basis_submitted": result_metric(run, "basis_submitted_count"),
            "basis_accepted": result_metric(run, "basis_accepted_count"),
            "confirmed_native_continuation":
                result_metric(run, "confirmed_continuation_count"),
            "ambiguous_retained_state":
                result_metric(run, "ambiguous_retained_state_count"),
            "claim": (
                "same_leaf_model_object_only_no_basis_or_native_tree_claim"
                if state["arm"] in {"C4-CANDIDATE", "C5-CANDIDATE"}
                else "arm_specific_reference"),
        })
        lifecycle.append({
            "run_id": state["run_id"], "instance": state["instance"],
            "arm": state["arm"],
            "optimize_count": result_metric(run, "optimize_count"),
            "lp_optimize_count": result_metric(run, "lp_optimize_count"),
            "partial_mip_optimize_count":
                result_metric(run, "partial_mip_optimize_count"),
            "terminal_mip_optimize_count":
                result_metric(run, "terminal_mip_optimize_count"),
            "presolve_executions":
                result_metric(run, "presolve_execution_count"),
            "root_executions":
                result_metric(run, "root_relaxation_execution_count"),
            "splits": result_metric(run, "split_count"),
            "declined_splits": result_metric(run, "declined_split_count"),
            "lp_cutoff_prunes": result_metric(run, "lp_pruned_leaf_count"),
            "partial_bound_events":
                result_metric(run, "partial_mip_bound_event_count"),
            "partial_targets_reached":
                result_metric(run, "partial_mip_target_reached_count"),
            "open_leaves": result_metric(run, "open_leaf_count"),
            "closed_leaves": result_metric(run, "closed_leaf_count"),
            "total_work": result_metric(run, "work"),
            "lp_work": result_metric(run, "lp_work"),
            "partial_mip_work": result_metric(run, "partial_mip_work"),
            "terminal_mip_work": result_metric(run, "terminal_mip_work"),
            "lifecycle_complete":
                truth(result_metric(run, "lifecycle_complete")),
        })
    return {
        "roots": roots, "partials": partials, "splits": splits,
        "terminals": terminals, "reuse": reuse, "lifecycle": lifecycle,
    }


def main() -> int:
    runs = raw_runs()
    stages = materialized_stages(runs)
    common_ubs = common_upper_bounds(stages)
    public = {
        stage: [public_row(run, common_ubs[run["state"]["instance"]])
                for run in rows]
        for stage, rows in stages.items()
    }
    write_csv(OUT / "stage1_c0_mechanism_anchors.csv", public["stage1"])
    write_csv(OUT / "stage2_full_300s_results.csv", public["stage2"])
    write_csv(OUT / "stage3_mainline_anchors.csv", public["stage3"])
    write_csv(OUT / "stage4_repeatability.csv", public["stage4"])

    unique_official = {
        run["state"]["run_id"]: run
        for rows in stages.values() for run in rows
    }
    traces = {
        run_id: trace_for(run)
        for run_id, run in unique_official.items()
    }
    auc_rows = []
    time_rows = []
    for run_id, run in unique_official.items():
        complete, reason, observations, count = traces[run_id]
        record: dict[str, Any] = {
            "run_id": run_id,
            "instance": run["state"]["instance"],
            "family": run["state"]["family"],
            "arm": run["state"]["arm"],
            "trace_complete": complete,
            "trace_reason": reason,
            "valid_bound_observation_count": count,
            "auc_status": "observed" if complete else "auc_unavailable",
        }
        if complete:
            record.update(bound_trace.observed_step_auc(
                observations,
                common_verified_upper_bound=
                    common_ubs[run["state"]["instance"]]))
            time_rows.extend(threshold_rows(
                run, observations, common_ubs[run["state"]["instance"]]))
        auc_rows.append(record)
    write_csv(OUT / "actual_bound_progress_auc.csv", auc_rows)
    write_csv(OUT / "time_to_gap_thresholds.csv", time_rows)

    p_vs_c5 = pair_rows(
        stages["stage2"], "P-GRB", "C5-CANDIDATE", common_ubs, traces)
    c4_vs_c5 = pair_rows(
        stages["stage2"], "C4-CANDIDATE", "C5-CANDIDATE",
        common_ubs, traces)
    c0_vs_c5 = pair_rows(
        stages["stage1"], "C0-DIAG", "C5-CANDIDATE", common_ubs, traces)
    s0_vs_c5 = pair_rows(
        stages["stage3"], "S0-CPLEX", "C5-CANDIDATE",
        common_ubs, traces)
    write_csv(OUT / "p_grb_vs_c5.csv", p_vs_c5)
    write_csv(OUT / "c4_vs_c5.csv", c4_vs_c5)
    write_csv(OUT / "c0_vs_c5_diagnostic.csv", c0_vs_c5)
    write_csv(OUT / "s0_vs_c5_anchor.csv", s0_vs_c5)

    family = []
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in c4_vs_c5:
        by_family[row["family"]].append(row)
    for name, rows in sorted(by_family.items()):
        available = [row for row in rows
                     if row["auc_status"] == "observed_common_window"]
        family.append({
            "family": name,
            "instances": len(rows),
            "c5_final_lb_wins": sum(
                row["final_lb_delta_right_minus_left"] > TOL
                for row in rows),
            "c4_final_lb_wins": sum(
                row["final_lb_delta_right_minus_left"] < -TOL
                for row in rows),
            "final_lb_ties": sum(
                abs(row["final_lb_delta_right_minus_left"]) <= TOL
                for row in rows),
            "auc_available": len(available),
            "c5_auc_wins": sum(
                row["normalized_proof_auc_delta_right_minus_left"] > TOL
                for row in available),
            "c4_auc_wins": sum(
                row["normalized_proof_auc_delta_right_minus_left"] < -TOL
                for row in available),
        })
    write_csv(OUT / "family_summary.csv", family)

    mechanisms = mechanism_rows(list(unique_official.values()), traces)
    write_csv(OUT / "root_event_value.csv", mechanisms["roots"])
    write_csv(OUT / "partial_mip_bound_value.csv", mechanisms["partials"])
    write_csv(OUT / "split_value_audit.csv", mechanisms["splits"])
    write_csv(OUT / "terminal_mip_value_audit.csv", mechanisms["terminals"])
    write_csv(
        OUT / "model_and_state_reuse_audit.csv", mechanisms["reuse"])
    write_csv(
        OUT / "lifecycle_and_resource_summary.csv",
        mechanisms["lifecycle"])

    c5_runs = [
        run for run in unique_official.values()
        if run["state"]["arm"] == "C5-CANDIDATE"]
    exactness = []
    certificates = []
    for run in c5_runs:
        result = run["result"]
        trace = traces[run["state"]["run_id"]]
        structural = all((
            truth(result_metric(run, "root_coverage_valid")),
            truth(result_metric(run, "parent_child_coverage_valid")),
            truth(result_metric(run, "all_leaf_bounds_valid")),
            truth(result_metric(run, "leaf_bounds_monotone")),
            truth(result_metric(run, "global_bound_monotone")),
            truth(result_metric(run, "lifecycle_complete")),
            truth(result_metric(run, "feasibility_consistency_gate")),
        ))
        exactness.append({
            "run_id": run["state"]["run_id"],
            "instance": run["state"]["instance"],
            "structural_exactness_gate": structural,
            "trace_complete": trace[0],
            "trace_reason": trace[1],
            "open_leaf_preserved_on_interruption":
                (not truth(result_metric(run, "all_relevant_leaves_closed"))
                 and integer(result_metric(run, "open_leaf_count")) > 0)
                or truth(result_metric(run, "all_relevant_leaves_closed")),
            "passed": structural and trace[0],
        })
        strict = truth(result.get("strict_certified_original_problem"))
        all_closed = truth(result_metric(run, "all_relevant_leaves_closed"))
        lb = number(result.get("lower_bound"))
        ub = number(result.get("upper_bound"))
        false_certificate = strict and (
            not structural or not all_closed or
            not math.isfinite(lb) or not math.isfinite(ub) or
            abs(lb - ub) > TOL * max(1.0, abs(lb), abs(ub)))
        certificates.append({
            "run_id": run["state"]["run_id"],
            "instance": run["state"]["instance"],
            "strict_certificate": strict,
            "all_relevant_leaves_closed": all_closed,
            "false_certificate": false_certificate,
            "passed": not false_certificate,
        })
    write_csv(OUT / "exactness_audit.csv", exactness)
    write_csv(OUT / "certificate_audit.csv", certificates)

    available_pairs = [
        row for row in c4_vs_c5
        if row["auc_status"] == "observed_common_window"]
    lb_wins = sum(
        row["final_lb_delta_right_minus_left"] > TOL for row in c4_vs_c5)
    auc_wins = sum(
        row["normalized_proof_auc_delta_right_minus_left"] > TOL
        for row in available_pairs)
    exact_pass = all(row["passed"] for row in exactness)
    certificate_pass = all(row["passed"] for row in certificates)
    trace_pass = all(row["trace_complete"] for row in exactness)
    if not (exact_pass and certificate_pass and trace_pass):
        classification = "invalid"
    elif (lb_wins > len(c4_vs_c5) / 2 and
          auc_wins > len(available_pairs) / 2):
        classification = "paper_exact_and_performance_promising"
    elif lb_wins or auc_wins:
        classification = "exact_c0_mechanism_transfer_partial"
    else:
        classification = "exact_but_no_transfer_gain"
    audit = {
        "schema": "round30-final-audit-v1",
        "official_unique_runs": len(unique_official),
        "stage1_rows": len(stages["stage1"]),
        "stage2_rows": len(stages["stage2"]),
        "stage3_rows": len(stages["stage3"]),
        "stage4_rows": len(stages["stage4"]),
        "completed_process_rows": sum(
            run["state"]["return_code"] == 0
            and run["state"]["result_exists"]
            for run in unique_official.values()),
        "failed_process_rows": sum(
            run["state"]["return_code"] != 0
            or not run["state"]["result_exists"]
            for run in unique_official.values()),
        "emergency_timeout_rows": sum(
            run["state"]["emergency_timeout"]
            for run in unique_official.values()),
        "c5_exactness_gate": exact_pass,
        "c5_certificate_gate": certificate_pass,
        "c5_trace_gate": trace_pass,
        "c4_vs_c5_final_lb_wins": lb_wins,
        "c4_vs_c5_auc_available": len(available_pairs),
        "c4_vs_c5_auc_wins": auc_wins,
        "classification": classification,
        "stable_mainline": "S0/F0-CPLEX",
        "c5_promoted": False,
        "long_run_validation_justified":
            classification == "paper_exact_and_performance_promising",
    }
    frozen.json_write(OUT / "final_audit_summary.json", audit)
    report = f"""# Round 30 final report

Round 30 completed {audit['official_unique_runs']} unique official processes
and materialized Stage 1/2/3/4 as
{audit['stage1_rows']}/{audit['stage2_rows']}/
{audit['stage3_rows']}/{audit['stage4_rows']} rows.

The corrected Round 29 audit marks every C4 row lacking a compatible observed
global trace `auc_unavailable`; no endpoint pseudo-trajectory is used.

C0 forensics identify validity-gated partial native bounds, exact inherited
coverage, and best-bound interleaving as transferable. Fixed time quanta,
attempt counts, retry counts, and Work/node/solution controls remain
forbidden. The selected C5 uses `rho=0.01` and a
`GRB_CB_MIP_OBJBND` target equal to the complete child-disjunction bound.

All C5 structural exactness gates: **{exact_pass}**. All C5 trace gates:
**{trace_pass}**. False-certificate gate: **{certificate_pass}**.

Against C4 on the 17-row primary matrix, C5 has {lb_wins} strict final-LB
wins and {auc_wins} observed common-window normalized proof-AUC wins among
{len(available_pairs)} AUC-eligible pairs.

Final classification: **{classification}**.

S0/F0-CPLEX remains the stable accepted paper mainline. C0 remains an exact
but non-paper-compatible diagnostic teacher. C5 is not promoted automatically.
"""
    (OUT / "final_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
