#!/usr/bin/env python3
"""Analyze the frozen Round 36 incumbent/decomposition causal matrix.

The program is read-only with respect to solver evidence.  It validates every
completion marker and artifact checksum before deriving compact causal tables.
With ``--allow-partial`` it writes explicitly prefixed pilot/interim outputs;
the publication outputs require all 56 frozen rows.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import round36_common as common


TOL = 1e-7
MATERIAL_AUC = 1e-4
ARMS = ("HH", "SS", "BW-P", "BW-A")


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


def runner_lifecycle_valid(state: dict[str, Any]) -> bool:
    return all((
        integer(state.get("return_code"), -1) == 0,
        not truth(state.get("emergency_timeout")),
        truth(state.get("result_json_parse_verified_after_process_exit")),
        not state.get("missing_required_artifacts", []),
        truth(state.get("completed")),
        truth(state.get("completion_marker_atomic")),
        not truth(state.get("algorithmic_solve_state_resumed")),
    ))


def graceful_deadline_noncertificate(result: dict[str, Any]) -> bool:
    return all((
        not truth(result.get("strict_certified_original_problem")),
        "time_limit" in str(result.get("status", "")).lower(),
        truth(result.get("graceful_deadline_finalization")),
        truth(result.get("exact_phase_started")),
        result.get("external_gini_tree_failure_reason") ==
            "overall_global_deadline",
        integer(result.get(
            "external_gini_tree_global_deadline_interruption_count")) >= 1,
        integer(result.get("external_gini_tree_open_leaf_count")) > 0,
        not truth(result.get(
            "external_gini_tree_all_relevant_leaves_closed")),
        result.get("strict_certificate_rejection_reason") ==
            "relevant_leaf_open",
    ))


def close(left: Any, right: Any, tolerance: float = TOL) -> bool:
    a, b = number(left), number(right)
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= \
        tolerance * max(1.0, abs(a), abs(b))


def relative_gap(lower: Any, upper: Any) -> float:
    lb, ub = number(lower), number(upper)
    if not (math.isfinite(lb) and math.isfinite(ub)):
        return math.nan
    return max(0.0, (ub - lb) / max(1e-12, abs(ub)))


def ratio(left: Any, right: Any) -> float:
    a, b = number(left), number(right)
    return a / b if math.isfinite(a) and math.isfinite(b) and b != 0 \
        else math.nan


def stable_hash(value: Any) -> str:
    material = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(material.encode()).hexdigest()


def projection(rows: Iterable[dict[str, Any]], fields: tuple[str, ...]) \
        -> list[tuple[Any, ...]]:
    return [tuple(row.get(field, "") for field in fields) for row in rows]


def compact(rows: Iterable[dict[str, Any]], fields: tuple[str, ...],
            limit: int = 12) -> str:
    material = ["|".join(str(row.get(field, "")) for field in fields)
                for row in rows]
    shown = material[:limit]
    if len(material) > limit:
        shown.append(f"...({len(material) - limit}_more)")
    return ";".join(shown)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8", newline="\n")
    temporary.replace(path)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    material = list(rows)
    if not material:
        material = [{"status": "no_rows"}]
    fields: list[str] = []
    for row in material:
        for field in row:
            if field not in fields:
                fields.append(field)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)
    temporary.replace(path)


def artifact_inventory_contract(directory: Path,
                                artifacts: list[dict[str, str]],
                                marker: dict[str, Any]) -> tuple[bool, str]:
    paths = [artifact.get("path", "") for artifact in artifacts]
    if len(paths) != len(set(paths)):
        return False, "artifact_manifest_duplicate_path"
    if integer(marker.get("artifact_count"), -1) != len(artifacts):
        return False, "artifact_count_mismatch"
    root = directory.resolve()
    for relative in paths:
        if not relative:
            return False, "artifact_manifest_empty_path"
        resolved = (directory / relative).resolve()
        if root not in resolved.parents:
            return False, f"artifact_path_outside_run:{relative}"
    required = {path.relative_to(directory).as_posix()
                for path in common.required_artifacts(directory)}
    missing = sorted(required - set(paths))
    if missing:
        return False, f"required_artifact_unlisted:{missing[0]}"
    return True, "artifact_inventory_contract_valid"


def artifact_complete(directory: Path, matrix: dict[str, str],
                      item: dict[str, Any], manifest: dict[str, Any]) \
        -> tuple[bool, str]:
    marker_path = directory / "completion_marker.json"
    inventory_path = directory / "artifact_manifest.csv"
    if not marker_path.is_file() or not inventory_path.is_file():
        return False, "completion_metadata_missing"
    try:
        marker = common.load_json(marker_path)
        artifacts = common.csv_rows(inventory_path)
    except (OSError, ValueError, json.JSONDecodeError, csv.Error):
        return False, "completion_metadata_unparseable"
    expected = {
        "round_id": 36,
        "run_id": matrix["run_id"],
        "instance_sha256": item["instance_sha256"],
        "executable_sha256": manifest["gurobi_executable_sha256"],
        "official_matrix_sha256": manifest["official_matrix_sha256"],
        "source_tree_fingerprint": manifest["source_tree_fingerprint"],
    }
    for key, value in expected.items():
        if marker.get(key) != value:
            return False, f"identity_mismatch:{key}"
    if marker.get("artifact_manifest_sha256") != common.sha256(inventory_path):
        return False, "artifact_manifest_checksum_mismatch"
    inventory_valid, reason = artifact_inventory_contract(
        directory, artifacts, marker)
    if not inventory_valid:
        return False, reason
    for artifact in artifacts:
        path = directory / artifact["path"]
        if not path.is_file() or path.stat().st_size != integer(
                artifact.get("bytes")) or common.sha256(path) != artifact.get(
                    "sha256"):
            return False, f"artifact_checksum_mismatch:{artifact['path']}"
    return True, "checksum_valid_complete"


def discover(allow_partial: bool) -> tuple[list[dict[str, Any]],
                                            list[dict[str, Any]]]:
    manifest = common.load_json(common.FROZEN_MANIFEST)
    matrix = common.csv_rows(common.OFFICIAL_MATRIX)
    panel = {row["panel_row_id"]: row
             for row in common.csv_rows(common.PANEL)}
    items = common.inventory()
    runs, missing = [], []
    for row in matrix:
        item = items[row["instance_id"]]
        directory = common.RUNS / row["run_id"]
        valid, reason = artifact_complete(directory, row, item, manifest)
        if not valid:
            missing.append({"run_id": row["run_id"], "reason": reason})
            continue
        marker = common.load_json(directory / "completion_marker.json")
        result = common.load_json(directory / "result.json")
        runs.append({
            "matrix": row, "panel": panel[row["panel_row_id"]],
            "item": item, "state": marker, "result": result,
            "run_dir": directory,
        })
    if missing and not allow_partial:
        sample = ", ".join(row["run_id"] for row in missing[:4])
        raise RuntimeError(
            f"Round 36 requires 56 complete rows; {len(missing)} missing: "
            f"{sample}")
    if not runs:
        raise RuntimeError("no checksum-complete Round 36 rows")
    by_panel: dict[str, set[str]] = defaultdict(set)
    for run in runs:
        by_panel[run["matrix"]["panel_row_id"]].add(run["matrix"]["arm"])
    incomplete_panels = [key for key, arms in by_panel.items()
                         if arms != set(ARMS)]
    if incomplete_panels and not allow_partial:
        raise RuntimeError(f"incomplete four-arm panels: {incomplete_panels}")
    # Partial reports use only complete four-arm panels so causal pairs cannot
    # silently mix observations from different completion states.
    if allow_partial:
        runs = [run for run in runs if run["matrix"]["panel_row_id"]
                not in incomplete_panels]
    return runs, missing


def bounds(run: dict[str, Any]) -> tuple[float, float]:
    return common.result_bounds(run["result"])


def strict(run: dict[str, Any]) -> bool:
    return truth(run["result"].get("strict_certified_original_problem"))


def process_time(run: dict[str, Any]) -> float:
    return common.process_entry_time(run["result"])


def exact_start(run: dict[str, Any]) -> float:
    return number(run["result"].get(
        "process_elapsed_at_exact_phase_start_seconds"), 0.0)


def exact_phase_time(run: dict[str, Any]) -> float:
    return max(0.0, process_time(run) - exact_start(run))


def ledger(run: dict[str, Any], name: str) -> list[dict[str, str]]:
    return common.csv_rows(run["run_dir"] / "external" / name)


def trace(run: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    best_lb = -math.inf
    best_ub = math.inf
    for source in ledger(run, "global_bound_trace.csv"):
        when = number(source.get("process_elapsed_seconds"))
        lower = number(source.get("valid_global_lower_bound"))
        upper = number(source.get("verified_global_upper_bound"))
        if not (math.isfinite(when) and math.isfinite(lower)):
            continue
        best_lb = max(best_lb, lower)
        if math.isfinite(upper):
            best_ub = min(best_ub, upper)
        output.append({
            "process_seconds": when,
            "exact_phase_seconds": number(source.get(
                "exact_phase_elapsed_seconds")),
            "lower_bound": best_lb, "upper_bound": best_ub,
            "event": source.get("event_type", ""),
            "active_leaf": source.get("active_leaf", ""),
            "source": source.get("event_source", ""),
        })
    output.sort(key=lambda row: row["process_seconds"])
    return output


def value_at(rows: list[dict[str, Any]], when: float) -> float:
    value = number(rows[0]["lower_bound"])
    for row in rows:
        if number(row["process_seconds"]) > when + 1e-12:
            break
        value = number(row["lower_bound"], value)
    return value


def pair_auc(left: dict[str, Any], right: dict[str, Any],
             common_ub: float) -> dict[str, Any]:
    left_trace, right_trace = trace(left), trace(right)
    if not left_trace or not right_trace:
        return {"auc_status": "unavailable_missing_trace"}
    start = max(left_trace[0]["process_seconds"],
                right_trace[0]["process_seconds"])
    end = min(left_trace[-1]["process_seconds"],
              right_trace[-1]["process_seconds"])
    if end <= start:
        return {"auc_status": "unavailable_no_common_observed_window"}
    times = sorted({
        start, end,
        *(row["process_seconds"] for row in left_trace
          if start < row["process_seconds"] < end),
        *(row["process_seconds"] for row in right_trace
          if start < row["process_seconds"] < end),
    })
    proof, gaps = [0.0, 0.0], [0.0, 0.0]
    denominator = max(1e-12, abs(common_ub))
    for begin, finish in zip(times, times[1:]):
        duration = finish - begin
        for index, rows in enumerate((left_trace, right_trace)):
            current = max(0.0, min(
                1.0, (common_ub - value_at(rows, begin)) / denominator))
            gaps[index] += duration * current
            proof[index] += duration * (1.0 - current)
    duration = end - start
    return {
        "auc_status": "observed_common_window",
        "auc_convention":
            "left_continuous_no_interpolation_no_post_last_extension",
        "common_window_start_seconds": start,
        "common_window_end_seconds": end,
        "common_window_seconds": duration,
        "left_normalized_proof_auc": proof[0] / duration,
        "right_normalized_proof_auc": proof[1] / duration,
        "right_minus_left_proof_auc": (proof[1] - proof[0]) / duration,
        "left_normalized_gap_auc": gaps[0] / duration,
        "right_normalized_gap_auc": gaps[1] / duration,
    }


def observed_auc(run: dict[str, Any], common_ub: float) -> dict[str, Any]:
    """Integrate one trace only over its actually recorded event window."""
    rows = trace(run)
    if len(rows) < 2:
        return {
            "observed_auc_status": "unavailable_insufficient_trace",
            "observed_trace_event_count": len(rows),
        }
    start, end = rows[0]["process_seconds"], rows[-1]["process_seconds"]
    duration = end - start
    if duration <= 0:
        return {
            "observed_auc_status": "unavailable_zero_window",
            "observed_trace_event_count": len(rows),
        }
    denominator = max(1e-12, abs(common_ub))
    gap_area = 0.0
    for left, right in zip(rows, rows[1:]):
        width = max(0.0, right["process_seconds"] - left["process_seconds"])
        current = max(0.0, min(
            1.0, (common_ub - left["lower_bound"]) / denominator))
        gap_area += width * current
    normalized_gap = gap_area / duration
    return {
        "observed_auc_status": "observed_event_window",
        "observed_auc_convention":
            "left_continuous_no_interpolation_no_post_last_extension",
        "observed_trace_event_count": len(rows),
        "observed_trace_start_seconds": start,
        "observed_trace_end_seconds": end,
        "observed_trace_window_seconds": duration,
        "normalized_observed_gap_auc": normalized_gap,
        "normalized_observed_proof_auc": 1.0 - normalized_gap,
    }


def mechanism(run: dict[str, Any]) -> dict[str, Any]:
    result = run["result"]
    initial = ledger(run, "initial_decomposition_ledger.csv")
    leaves = ledger(run, "paper_leaf_ledger.csv")
    lp = ledger(run, "lp_status_ledger.csv")
    targets = ledger(run, "native_target_ledger.csv")
    splits = ledger(run, "split_decision_ledger.csv")
    optimize = ledger(run, "paper_optimize_ledger.csv")
    events = ledger(run, "paper_tree_events.csv")
    global_rows = ledger(run, "global_bound_trace.csv")
    parent = ledger(run, "parent_child_bound_ledger.csv")
    initial_ids = {f"L{row.get('anchor_cell_index', '')}" for row in initial}
    initial_lp = [row for row in lp if row.get("leaf_id") in initial_ids]
    controlling = [row for row in global_rows if row.get("active_leaf")]
    actual_splits = [row for row in splits if truth(row.get("split"))]
    terminal = [row for row in optimize if row.get("solve_kind") == "MIP"]
    closures = [row for row in events if any(token in row.get(
        "event", "").lower() for token in (
            "close", "infeasible", "prune", "terminal"))]
    native_improvements = [row for row in global_rows if "incumbent" in
                           row.get("event_type", "").lower()]
    pre_split = []
    for row in global_rows:
        if row.get("event_type") == "split":
            break
        pre_split.append(row)
    first_split_exact = min((number(row.get("telemetry_seconds")) for row in
                             events if row.get("event") == "atomic_split"),
                            default=math.nan)
    initial_geometry_material = projection(initial, (
        "anchor_cell_index", "anchor_lower", "anchor_upper", "active",
        "active_lower", "active_upper", "truncated_by_proof_range"))
    initial_lp_material = projection(initial_lp, (
        "leaf_id", "depth", "gamma_L", "gamma_U", "terminal_valid",
        "optimal", "infeasible", "lower_bound", "native_status"))
    control_material = projection(controlling, (
        "event_type", "active_leaf", "active_leaf_valid_lower_bound",
        "other_open_leaf_min_valid_lower_bound", "valid_global_lower_bound",
        "event_source"))
    target_material = projection(targets, (
        "leaf_id", "target_kind", "current_bound", "target_bound", "status",
        "target_reached", "exact_closure", "requeued", "event_source"))
    split_material = projection(splits, (
        "parent_id", "eligible", "decision_valid", "split",
        "child_infeasibility_trigger", "strict_bound_trigger",
        "normalized_disjunction_gain", "b_plus", "reason"))
    split_decision_material = projection(splits, (
        "parent_id", "eligible", "decision_valid", "split",
        "child_infeasibility_trigger", "strict_bound_trigger", "reason"))
    closure_material = projection(closures, (
        "event", "leaf_id", "status", "detail"))
    pre_split_material = projection(pre_split, (
        "event_type", "active_leaf", "active_leaf_valid_lower_bound",
        "other_open_leaf_min_valid_lower_bound", "valid_global_lower_bound",
        "open_relevant_leaf_count", "closed_relevant_leaf_count",
        "event_source"))
    downstream = {
        "initial_lp": initial_lp_material, "control": control_material,
        "targets": target_material, "splits": split_material,
        "closure": closure_material,
    }
    return {
        "proof_range_lower": number(result.get(
            "external_gini_tree_root_gamma_L")),
        "proof_range_upper": number(result.get(
            "external_gini_tree_proof_relevant_gamma_upper")),
        "anchor_grid_upper": number(result.get(
            "external_gini_tree_anchor_grid_gamma_upper")),
        "anchor_grid_endpoints": result.get(
            "external_gini_tree_anchor_grid_endpoints", ""),
        "active_initial_intervals": result.get(
            "external_gini_tree_active_initial_intervals", ""),
        "truncated_initial_intervals": integer(result.get(
            "external_gini_tree_truncated_initial_interval_count")),
        "local_domain_ranges": compact(initial_lp, (
            "leaf_id", "gamma_L", "gamma_U", "lower_bound")),
        "interval_row_families": result.get(
            "external_gini_tree_interval_row_families", ""),
        "interval_row_family_count": integer(result.get(
            "external_gini_tree_interval_row_family_count")),
        "cutoff_derived_rows": integer(result.get(
            "compact_bc_objective_estimator_cutoff_rows_added")),
        "parent_lp_bound_count": len(parent),
        "parent_lp_bounds": compact(parent, (
            "parent_id", "parent_lp_bound", "left_lp_bound",
            "left_infeasible", "right_lp_bound", "right_infeasible",
            "post_split_bound")),
        "child_lp_bound_rows": len(parent),
        "child_lp_bounds": compact(parent, (
            "parent_id", "left_id", "left_lp_bound", "left_infeasible",
            "right_id", "right_lp_bound", "right_infeasible", "decision")),
        "initial_global_lower_bound": number(global_rows[0].get(
            "valid_global_lower_bound")) if global_rows else math.nan,
        "first_controlling_leaf": controlling[0].get(
            "active_leaf", "") if controlling else "",
        "controlling_leaf_sequence": compact(controlling, (
            "event_type", "active_leaf", "valid_global_lower_bound")),
        "native_target_sequence": compact(targets, (
            "leaf_id", "target_kind", "target_bound", "status")),
        "target_rows": len(targets),
        "targets_attained": sum(truth(row.get("target_reached"))
                                for row in targets),
        "requeues": sum(truth(row.get("requeued")) for row in targets),
        "child_lookahead_rows": len(splits),
        "b_plus_sequence": compact(splits, (
            "parent_id", "b_plus", "eta_proof", "eta_anchor")),
        "selected_eta_sequence": compact(splits, (
            "parent_id", "normalized_disjunction_gain",
            "normalization_source", "reason")),
        "actual_split_sequence": compact(actual_splits, (
            "parent_id", "normalized_disjunction_gain", "reason")),
        "actual_splits": len(actual_splits),
        "max_depth": max((integer(row.get("depth")) for row in leaves),
                         default=0),
        "first_split_exact_phase_seconds": first_split_exact,
        "first_split_process_seconds": exact_start(run) + first_split_exact
            if math.isfinite(first_split_exact) else math.nan,
        "terminal_mip_calls": len(terminal),
        "terminal_work": sum(number(row.get("work"), 0.0)
                             for row in terminal),
        "terminal_nodes": sum(number(row.get("nodes"), 0.0)
                              for row in terminal),
        "terminal_status_sequence": compact(terminal, (
            "leaf_id", "native_status", "work", "nodes")),
        "closure_sequence": compact(closures, (
            "event", "leaf_id", "status")),
        "native_incumbents_during_exact": len(native_improvements),
        "first_native_incumbent_process_seconds": number(result.get(
            "external_gini_tree_first_incumbent_time_seconds")),
        "work": number(result.get("external_gini_tree_work")),
        "nodes": number(result.get("external_gini_tree_nodes")),
        "initial_geometry_sha256": stable_hash(initial_geometry_material),
        "initial_lp_sha256": stable_hash(initial_lp_material),
        "controlling_sequence_sha256": stable_hash(control_material),
        "target_sequence_sha256": stable_hash(target_material),
        "split_sequence_sha256": stable_hash(split_material),
        "split_decision_sha256": stable_hash(split_decision_material),
        "closure_sequence_sha256": stable_hash(closure_material),
        "pre_first_split_sequence_sha256": stable_hash(pre_split_material),
        "downstream_sequence_sha256": stable_hash(downstream),
    }


def canonical_startups(runs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[run["matrix"]["panel_row_id"]].append(run)
    output = {}
    for panel_id, group in grouped.items():
        preferred = next((run for run in group
                          if run["matrix"]["arm"] == "BW-P"), group[0])
        result = preferred["result"]
        h_values = [number(run["result"].get(
            "round36_hga_start_objective")) for run in group
                    if truth(run["result"].get(
                        "round36_hga_start_verified"))]
        s_values = [number(run["result"].get(
            "round36_simple_start_objective")) for run in group
                    if truth(run["result"].get(
                        "round36_simple_start_verified"))]
        if not h_values or not s_values:
            raise RuntimeError(f"startup pair missing for {panel_id}")
        if not all(close(value, h_values[0]) for value in h_values) or not all(
                close(value, s_values[0]) for value in s_values):
            raise RuntimeError(f"startup objective drift for {panel_id}")
        output[panel_id] = {
            "U_H": number(result.get("round36_hga_start_objective"),
                          h_values[0]),
            "U_S": number(result.get("round36_simple_start_objective"),
                          s_values[0]),
            "HGA_start_seconds_canonical": number(result.get(
                "round36_hga_start_seconds")),
            "SIMPLE_start_seconds_canonical": number(result.get(
                "round36_simple_start_seconds")),
        }
    return output


def command_value(command: list[Any], option: str) -> str:
    values = [str(value) for value in command]
    try:
        return values[values.index(option) + 1]
    except (ValueError, IndexError):
        return ""


def active_cover_valid(run: dict[str, Any]) -> bool:
    rows = [row for row in ledger(run, "initial_decomposition_ledger.csv")
            if truth(row.get("active"))]
    if not rows:
        return False
    proof_lower = number(rows[0].get("proof_range_lower"))
    proof_upper = number(rows[0].get("proof_range_upper"))
    cursor = proof_lower
    for row in rows:
        lower, upper = number(row.get("active_lower")), number(
            row.get("active_upper"))
        if not close(lower, cursor) or upper < lower - TOL:
            return False
        cursor = upper
    return close(cursor, proof_upper)


def run_rows(runs: list[dict[str, Any]]) -> tuple[
        list[dict[str, Any]], list[dict[str, Any]],
        dict[str, dict[str, Any]], list[dict[str, Any]]]:
    startups = canonical_startups(runs)
    mechanisms, per_arm, audits, decomposition = {}, [], [], []
    final_ubs: dict[str, float] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        grouped[run["matrix"]["panel_row_id"]].append(run)
    for panel_id, group in grouped.items():
        final_ubs[panel_id] = min(bounds(run)[1] for run in group)
    for run in runs:
        matrix, panel, result, state = (
            run["matrix"], run["panel"], run["result"], run["state"])
        panel_id, arm = matrix["panel_row_id"], matrix["arm"]
        info = startups[panel_id]
        metric = mechanism(run)
        mechanisms[state["run_id"]] = metric
        lower, upper = bounds(run)
        common_ub = final_ubs[panel_id]
        proof = number(result.get("round36_proof_incumbent_launch"))
        anchor = number(result.get("round36_decomposition_anchor_launch"))
        strict_certificate = strict(run)
        deadline_noncertificate = graceful_deadline_noncertificate(result)
        base = {
            "round_id": 36, "panel_ordinal": panel["panel_ordinal"],
            "panel_row_id": panel_id, "run_id": state["run_id"],
            "instance_id": matrix["instance_id"], "V": panel["V"],
            "M": panel["M"], "scenario": panel["scenario"],
            "round35_pattern": panel["round35_pattern"],
            "selection_basis": panel["selection_basis"], "arm": arm,
            "process_cap_seconds": matrix["process_cap_seconds"],
            "U_H": info["U_H"], "U_S": info["U_S"],
            "HGA_start_seconds_canonical":
                info["HGA_start_seconds_canonical"],
            "SIMPLE_start_seconds_canonical":
                info["SIMPLE_start_seconds_canonical"],
            "arm_hga_attempted": result.get("round36_hga_start_attempted"),
            "arm_hga_verified": result.get("round36_hga_start_verified"),
            "arm_hga_objective": result.get("round36_hga_start_objective"),
            "arm_hga_seconds": result.get("round36_hga_start_seconds"),
            "arm_simple_attempted": result.get(
                "round36_simple_start_attempted"),
            "arm_simple_verified": result.get(
                "round36_simple_start_verified"),
            "arm_simple_objective": result.get(
                "round36_simple_start_objective"),
            "arm_simple_seconds": result.get("round36_simple_start_seconds"),
            "U_proof_launch": proof, "U_anchor_launch": anchor,
            "relative_incumbent_difference": result.get(
                "round36_relative_startup_incumbent_difference"),
            "normalization_source": result.get(
                "round36_c6_split_normalization"),
            "status": result.get("status"),
            "valid_final_lower_bound": lower,
            "verified_final_upper_bound": upper,
            "common_verified_upper_bound": common_ub,
            "final_common_ub_gap": relative_gap(lower, common_ub),
            "strict_certificate": strict_certificate,
            "valid_time_limited_noncertificate": deadline_noncertificate,
            "certificate_class": result.get("strict_certificate_class"),
            "certificate_rejection_reason": result.get(
                "strict_certificate_rejection_reason"),
            "process_seconds": process_time(run),
            "startup_to_exact_seconds": exact_start(run),
            "exact_phase_seconds": exact_phase_time(run),
            "source_tree_fingerprint": state.get("source_tree_fingerprint"),
            "executable_sha256": state.get("executable_sha256"),
            **metric,
            **observed_auc(run, common_ub),
        }
        per_arm.append(base)
        expected_proof = (info["U_H"] if arm == "HH" else info["U_S"]
                          if arm == "SS" else min(info["U_H"], info["U_S"]))
        expected_anchor = (info["U_H"] if arm == "HH" else info["U_S"]
                           if arm == "SS" else max(info["U_H"], info["U_S"]))
        expected_norm = "anchor" if arm == "BW-A" else "proof"
        command = state.get("command", [])
        one_thread = all(command_value(command, option) == "1" for option in (
            "--threads", "--mip-threads", "--cplex-threads",
            "--compact-bc-threads"))
        structural = all(truth(result.get(field)) for field in (
            "external_gini_tree_root_coverage_valid",
            "external_gini_tree_parent_child_coverage_valid",
            "external_gini_tree_all_leaf_bounds_valid",
            "external_gini_tree_leaf_bounds_monotone",
            "external_gini_tree_global_bound_monotone",
            "external_gini_tree_lifecycle_complete",
            "external_gini_tree_feasibility_consistency_gate"))
        open_preserved = truth(result.get(
            "external_gini_tree_all_relevant_leaves_closed")) or integer(
                result.get("external_gini_tree_open_leaf_count")) > 0
        inversion = lower > upper + TOL * max(1.0, abs(upper))
        finite_bounds = math.isfinite(lower) and math.isfinite(upper)
        false_certificate = strict(run) and not close(lower, upper)
        startup_contract = (
            (arm == "HH" and truth(result.get(
                "round36_hga_start_verified")) and not truth(result.get(
                    "round36_simple_start_attempted")))
            or (arm == "SS" and truth(result.get(
                "round36_simple_start_verified")) and not truth(result.get(
                    "round36_hga_start_attempted")))
            or (arm.startswith("BW-") and truth(result.get(
                "round36_hga_start_verified")) and truth(result.get(
                    "round36_simple_start_verified"))))
        proof_anchor_contract = close(proof, expected_proof) and close(
            anchor, expected_anchor) and anchor + TOL * max(
                1.0, abs(anchor), abs(proof)) >= proof
        arm_contract = result.get("round36_c6_causal_arm") == arm.lower() \
            and result.get("round36_c6_split_normalization") == expected_norm
        runner_lifecycle = runner_lifecycle_valid(state)
        certificate_endpoint_valid = strict_certificate or deadline_noncertificate
        audit_passed = all((
            structural, open_preserved, finite_bounds, not inversion,
            not false_certificate, startup_contract, proof_anchor_contract,
            arm_contract, truth(result.get("round36_anchor_safety_valid")),
            active_cover_valid(run), one_thread, runner_lifecycle,
            certificate_endpoint_valid,
            command_value(command, "--gurobi-seed") == "0",
            command_value(command, "--frontier-intervals") == "4",
            upper <= proof + TOL * max(1.0, abs(proof), abs(upper)),
        ))
        audits.append({
            **{key: base[key] for key in (
                "panel_row_id", "run_id", "instance_id", "V", "M",
                "scenario", "round35_pattern", "arm")},
            "completion_checksum_valid": True,
            "structural_exactness_gates": structural,
            "open_leaf_state_preserved_on_deadline": open_preserved,
            "active_proof_range_coverage_valid": active_cover_valid(run),
            "startup_verification_contract_valid": startup_contract,
            "proof_anchor_contract_valid": proof_anchor_contract,
            "reported_arm_normalization_contract_valid": arm_contract,
            "runner_normal_exit": integer(
                state.get("return_code"), -1) == 0,
            "runner_no_emergency_timeout": not truth(
                state.get("emergency_timeout")),
            "result_json_verified_after_process_exit": truth(state.get(
                "result_json_parse_verified_after_process_exit")),
            "runner_required_artifacts_complete": not state.get(
                "missing_required_artifacts", []),
            "atomic_completion_marker_valid": truth(
                state.get("completed")) and truth(
                    state.get("completion_marker_atomic")),
            "algorithmic_solve_state_not_resumed": not truth(
                state.get("algorithmic_solve_state_resumed")),
            "runner_lifecycle_valid": runner_lifecycle,
            "valid_time_limited_noncertificate": deadline_noncertificate,
            "certificate_or_graceful_deadline_endpoint_valid":
                certificate_endpoint_valid,
            "anchor_safety_valid": result.get(
                "round36_anchor_safety_valid"),
            "single_thread_command_valid": one_thread,
            "gurobi_seed_zero": command_value(command, "--gurobi-seed") == "0",
            "K_equals_four": command_value(
                command, "--frontier-intervals") == "4",
            "rho_frozen_source_contract": 0.01,
            "finite_bounds": finite_bounds,
            "bound_inversion": inversion,
            "strict_certificate": strict_certificate,
            "strict_bound_equality_within_tolerance":
                close(lower, upper) if strict_certificate else "not_applicable",
            "false_certificate": false_certificate,
            "final_verified_ub_no_worse_than_launch_proof":
                upper <= proof + TOL * max(1.0, abs(proof), abs(upper)),
            "exactness_certificate_audit_passed": audit_passed,
        })
        initial_rows = ledger(run, "initial_decomposition_ledger.csv")
        initial_lp_by_id = {row.get("leaf_id"): row for row in ledger(
            run, "lp_status_ledger.csv")}
        for cell in initial_rows:
            leaf = initial_lp_by_id.get(
                f"L{cell.get('anchor_cell_index', '')}", {})
            decomposition.append({
                **{key: base[key] for key in (
                    "panel_row_id", "run_id", "instance_id", "V", "M",
                    "scenario", "round35_pattern", "arm", "U_proof_launch",
                    "U_anchor_launch", "normalization_source")},
                **cell,
                "anchor_width": number(cell.get("anchor_upper")) - number(
                    cell.get("anchor_lower")),
                "active_width": number(cell.get("active_upper")) - number(
                    cell.get("active_lower")) if truth(cell.get("active"))
                    else 0.0,
                "local_leaf_id": leaf.get("leaf_id", ""),
                "local_lp_status": leaf.get("native_status", ""),
                "local_lp_lower_bound": leaf.get("lower_bound", ""),
                "interval_row_families": metric["interval_row_families"],
                "interval_row_family_count": metric[
                    "interval_row_family_count"],
                "cutoff_derived_rows": metric["cutoff_derived_rows"],
            })
    per_arm.sort(key=lambda row: (integer(row["panel_ordinal"]),
                                  ARMS.index(row["arm"])))
    audits.sort(key=lambda row: (row["panel_row_id"], ARMS.index(row["arm"])))
    return per_arm, audits, mechanisms, decomposition


def outcome(left: dict[str, Any], right: dict[str, Any],
            auc: dict[str, Any]) -> tuple[str, str]:
    if truth(right["strict_certificate"]) != truth(left["strict_certificate"]):
        return ("right_win", "strict_certificate") if truth(
            right["strict_certificate"]) else ("left_win", "strict_certificate")
    gap_delta = number(right["final_common_ub_gap"]) - number(
        left["final_common_ub_gap"])
    if gap_delta < -TOL:
        return "right_win", "final_common_ub_gap"
    if gap_delta > TOL:
        return "left_win", "final_common_ub_gap"
    auc_delta = number(auc.get("right_minus_left_proof_auc"))
    if auc_delta > MATERIAL_AUC:
        return "right_win", "common_window_proof_auc"
    if auc_delta < -MATERIAL_AUC:
        return "left_win", "common_window_proof_auc"
    if truth(left["strict_certificate"]) and truth(right["strict_certificate"]):
        time_ratio = ratio(right["exact_phase_seconds"],
                           left["exact_phase_seconds"])
        if math.isfinite(time_ratio) and time_ratio < 0.95:
            return "right_win", "certified_exact_phase_time_descriptive"
        if math.isfinite(time_ratio) and time_ratio > 1.05:
            return "left_win", "certified_exact_phase_time_descriptive"
    return "tie", "no_material_difference"


def causal_pair(left_run: dict[str, Any], right_run: dict[str, Any],
                left: dict[str, Any], right: dict[str, Any],
                comparison: str, mechanisms: dict[str, dict[str, Any]]) \
        -> dict[str, Any]:
    left_m = mechanisms[left["run_id"]]
    right_m = mechanisms[right["run_id"]]
    common_ub = min(number(left["verified_final_upper_bound"]),
                    number(right["verified_final_upper_bound"]))
    auc = pair_auc(left_run, right_run, common_ub)
    result, basis = outcome(left, right, auc)
    pre_split_changed = left_m["pre_first_split_sequence_sha256"] != \
        right_m["pre_first_split_sequence_sha256"] or left_m[
            "initial_lp_sha256"] != right_m["initial_lp_sha256"]
    split_decisions_changed = left_m["split_decision_sha256"] != \
        right_m["split_decision_sha256"]
    downstream_changed = any(left_m[field] != right_m[field] for field in (
        "initial_lp_sha256", "controlling_sequence_sha256",
        "target_sequence_sha256", "split_sequence_sha256",
        "closure_sequence_sha256"))
    both_zero = left_m["actual_splits"] == right_m["actual_splits"] == 0
    pattern = left["round35_pattern"]
    expected = ("right_win" if pattern.startswith("3_") else "left_win"
                if pattern.startswith("4_") or pattern.startswith("5_")
                else "not_directionally_assessed")
    return {
        "round_id": 36, "comparison": comparison,
        "panel_row_id": left["panel_row_id"],
        "instance_id": left["instance_id"], "V": left["V"], "M": left["M"],
        "scenario": left["scenario"], "round35_pattern": pattern,
        "left_arm": left["arm"], "right_arm": right["arm"],
        "left_U_proof": left["U_proof_launch"],
        "right_U_proof": right["U_proof_launch"],
        "same_proof_incumbent": close(left["U_proof_launch"],
                                      right["U_proof_launch"]),
        "left_U_anchor": left["U_anchor_launch"],
        "right_U_anchor": right["U_anchor_launch"],
        "same_anchor": close(left["U_anchor_launch"], right["U_anchor_launch"]),
        "left_normalization_source": left["normalization_source"],
        "right_normalization_source": right["normalization_source"],
        "left_strict_certificate": left["strict_certificate"],
        "right_strict_certificate": right["strict_certificate"],
        "left_final_common_ub_gap": relative_gap(
            left["valid_final_lower_bound"], common_ub),
        "right_final_common_ub_gap": relative_gap(
            right["valid_final_lower_bound"], common_ub),
        "right_minus_left_final_gap": relative_gap(
            right["valid_final_lower_bound"], common_ub) - relative_gap(
                left["valid_final_lower_bound"], common_ub),
        "left_process_seconds": left["process_seconds"],
        "right_process_seconds": right["process_seconds"],
        "left_exact_phase_seconds": left["exact_phase_seconds"],
        "right_exact_phase_seconds": right["exact_phase_seconds"],
        "right_over_left_exact_phase_ratio": ratio(
            right["exact_phase_seconds"], left["exact_phase_seconds"]),
        "left_work": left_m["work"], "right_work": right_m["work"],
        "left_nodes": left_m["nodes"], "right_nodes": right_m["nodes"],
        "left_actual_splits": left_m["actual_splits"],
        "right_actual_splits": right_m["actual_splits"],
        "left_max_depth": left_m["max_depth"],
        "right_max_depth": right_m["max_depth"],
        "left_terminal_mip_calls": left_m["terminal_mip_calls"],
        "right_terminal_mip_calls": right_m["terminal_mip_calls"],
        "initial_geometry_changed": left_m["initial_geometry_sha256"] !=
            right_m["initial_geometry_sha256"],
        "initial_lp_sequence_changed": left_m["initial_lp_sha256"] !=
            right_m["initial_lp_sha256"],
        "controlling_sequence_changed": left_m[
            "controlling_sequence_sha256"] != right_m[
                "controlling_sequence_sha256"],
        "target_sequence_changed": left_m["target_sequence_sha256"] !=
            right_m["target_sequence_sha256"],
        "split_sequence_changed": left_m["split_sequence_sha256"] !=
            right_m["split_sequence_sha256"],
        "actual_split_decisions_changed": split_decisions_changed,
        "closure_sequence_changed": left_m["closure_sequence_sha256"] !=
            right_m["closure_sequence_sha256"],
        "downstream_sequence_changed": downstream_changed,
        "pre_first_split_sequence_changed": pre_split_changed,
        "both_arms_zero_actual_splits": both_zero,
        "trajectory_diff_despite_zero_splits": both_zero and downstream_changed,
        "first_divergence_before_split": pre_split_changed,
        "left_first_split_process_seconds": left_m[
            "first_split_process_seconds"],
        "right_first_split_process_seconds": right_m[
            "first_split_process_seconds"],
        "causal_outcome": result, "outcome_basis": basis,
        "round35_expected_direction": expected,
        "round35_direction_match": result == expected
            if expected != "not_directionally_assessed" else "not_assessed",
        **auc,
    }


def comparisons(runs: list[dict[str, Any]], per_arm: list[dict[str, Any]],
                mechanisms: dict[str, dict[str, Any]]) -> tuple[
                    list[dict[str, Any]], list[dict[str, Any]],
                    list[dict[str, Any]]]:
    run_map = {(run["matrix"]["panel_row_id"], run["matrix"]["arm"]): run
               for run in runs}
    row_map = {(row["panel_row_id"], row["arm"]): row for row in per_arm}
    panel_ids = sorted({row["panel_row_id"] for row in per_arm})
    geometry, normalization, fixed_proof = [], [], []
    for panel_id in panel_ids:
        hh, ss, bwp, bwa = (row_map[(panel_id, arm)] for arm in ARMS)
        geometry_row = causal_pair(
            run_map[(panel_id, "HH")], run_map[(panel_id, "BW-P")], hh, bwp,
            "HH_vs_BW-P_geometry", mechanisms)
        geometry_row["geometry_exposure"] = (
            truth(geometry_row["same_proof_incumbent"])
            and not close(hh["U_anchor_launch"], bwp["U_anchor_launch"]))
        geometry.append(geometry_row)
        normalization_row = causal_pair(
            run_map[(panel_id, "BW-P")], run_map[(panel_id, "BW-A")],
            bwp, bwa, "BW-P_vs_BW-A_normalization", mechanisms)
        normalization_row["normalization_exposure"] = (
            close(bwp["U_proof_launch"], bwa["U_proof_launch"])
            and close(bwp["U_anchor_launch"], bwa["U_anchor_launch"])
            and not close(bwp["U_proof_launch"], bwp["U_anchor_launch"]))
        normalization_row["rho_explanation_possible"] = (
            normalization_row["normalization_exposure"]
            and normalization_row["actual_split_decisions_changed"]
            and not normalization_row["first_divergence_before_split"]
            and not normalization_row["both_arms_zero_actual_splits"])
        normalization.append(normalization_row)
        wide_arm = "SS" if number(bwp["U_S"]) >= number(bwp["U_H"]) else "HH"
        wide = ss if wide_arm == "SS" else hh
        proof_row = causal_pair(
            run_map[(panel_id, wide_arm)], run_map[(panel_id, "BW-A")],
            wide, bwa, "wide-proof_vs_best-proof_fixed-anchor", mechanisms)
        proof_row.update({
            "wide_self_arm": wide_arm,
            "fixed_anchor_proof_exposure": close(
                wide["U_anchor_launch"], bwa["U_anchor_launch"])
                and not close(wide["U_proof_launch"], bwa["U_proof_launch"]),
            "stronger_proof_cutoff_used_on_right": number(
                bwa["U_proof_launch"]) < number(wide["U_proof_launch"])
                - TOL * max(1.0, abs(number(wide["U_proof_launch"]))),
            "right_open_leaf_count": integer(run_map[(
                panel_id, "BW-A")]["result"].get(
                    "external_gini_tree_open_leaf_count")),
            "left_open_leaf_count": integer(run_map[(
                panel_id, wide_arm)]["result"].get(
                    "external_gini_tree_open_leaf_count")),
        })
        fixed_proof.append(proof_row)
    return geometry, normalization, fixed_proof


def sequence_rows(per_arm: list[dict[str, Any]],
                  mechanisms: dict[str, dict[str, Any]]) \
        -> list[dict[str, Any]]:
    output = []
    for row in per_arm:
        metric = mechanisms[row["run_id"]]
        output.append({
            **{key: row[key] for key in (
                "panel_row_id", "run_id", "instance_id", "V", "M",
                "scenario", "round35_pattern", "arm", "U_proof_launch",
                "U_anchor_launch", "normalization_source")},
            **{key: metric[key] for key in (
                "initial_geometry_sha256", "initial_lp_sha256",
                "controlling_sequence_sha256", "target_sequence_sha256",
                "split_sequence_sha256", "split_decision_sha256",
                "closure_sequence_sha256", "pre_first_split_sequence_sha256",
                "downstream_sequence_sha256", "actual_splits", "max_depth")},
            "hashes_exclude_timing_work_nodes": True,
        })
    return output


def trajectory_rows(runs: list[dict[str, Any]],
                    per_arm: list[dict[str, Any]]) -> list[dict[str, Any]]:
    row_map = {row["run_id"]: row for row in per_arm}
    output = []
    for run in runs:
        base = row_map[run["state"]["run_id"]]
        common_ub = base["common_verified_upper_bound"]
        for sequence, event in enumerate(trace(run)):
            output.append({
                "panel_row_id": base["panel_row_id"],
                "run_id": base["run_id"], "instance_id": base["instance_id"],
                "V": base["V"], "M": base["M"],
                "scenario": base["scenario"], "arm": base["arm"],
                "sequence": sequence,
                "process_seconds": event["process_seconds"],
                "exact_phase_seconds": event["exact_phase_seconds"],
                "valid_lower_bound": event["lower_bound"],
                "observed_verified_upper_bound": event["upper_bound"],
                "common_verified_upper_bound": common_ub,
                "relative_gap_to_common_ub": relative_gap(
                    event["lower_bound"], common_ub),
                "normalized_proof_fraction": 1.0 - min(1.0, relative_gap(
                    event["lower_bound"], common_ub)),
                "event": event["event"], "active_leaf": event["active_leaf"],
                "source": event["source"],
                "observed_event_no_post_last_extension": True,
            })
    return output


def expanded_ledger_rows(runs: list[dict[str, Any]],
                         per_arm: list[dict[str, Any]]) -> tuple[
        list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Materialize compact, joinable views of the key raw exact ledgers."""
    by_run = {row["run_id"]: row for row in per_arm}
    lookahead, targets, closures = [], [], []
    for run in runs:
        base = by_run[run["state"]["run_id"]]
        identity = {key: base[key] for key in (
            "panel_row_id", "run_id", "instance_id", "V", "M",
            "scenario", "round35_pattern", "arm", "U_proof_launch",
            "U_anchor_launch", "normalization_source")}
        parent = {row.get("parent_id"): row for row in ledger(
            run, "parent_child_bound_ledger.csv")}
        for sequence, split in enumerate(ledger(
                run, "split_decision_ledger.csv")):
            bounds_row = parent.get(split.get("parent_id"), {})
            lookahead.append({
                **identity, "sequence": sequence,
                "parent_id": split.get("parent_id", ""),
                "parent_lp_bound": bounds_row.get("parent_lp_bound", ""),
                "left_id": bounds_row.get("left_id", ""),
                "left_lp_bound": bounds_row.get("left_lp_bound", ""),
                "left_infeasible": bounds_row.get("left_infeasible", ""),
                "right_id": bounds_row.get("right_id", ""),
                "right_lp_bound": bounds_row.get("right_lp_bound", ""),
                "right_infeasible": bounds_row.get("right_infeasible", ""),
                "post_split_bound": bounds_row.get("post_split_bound", ""),
                **split,
                "decision_inputs_hardware_independent": True,
            })
        for sequence, target in enumerate(ledger(
                run, "native_target_ledger.csv")):
            targets.append({**identity, "sequence": sequence, **target})
        terminal_order = 0
        for optimize_sequence, row in enumerate(ledger(
                run, "paper_optimize_ledger.csv")):
            if row.get("solve_kind") != "MIP":
                continue
            closures.append({
                **identity, "terminal_order": terminal_order,
                "optimize_ledger_sequence": optimize_sequence,
                "leaf_id": row.get("leaf_id", ""),
                "native_status": row.get("native_status", ""),
                "solver_runtime": row.get("solver_runtime", ""),
                "work": row.get("work", ""), "nodes": row.get("nodes", ""),
                "simplex_iterations": row.get("simplex_iterations", ""),
                "barrier_iterations": row.get("barrier_iterations", ""),
                "in_memory_model_reused": row.get(
                    "in_memory_model_reused", ""),
            })
            terminal_order += 1
    return lookahead, targets, closures


def median(values: Iterable[Any]) -> Any:
    finite = [number(value) for value in values
              if math.isfinite(number(value))]
    return statistics.median(finite) if finite else ""


def group_summaries(comparisons_by_name: dict[str, list[dict[str, Any]]]) \
        -> list[dict[str, Any]]:
    output = []
    for name, rows in comparisons_by_name.items():
        for grouping in ("all", "scenario", "V", "M", "round35_pattern"):
            groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in rows:
                key = "all" if grouping == "all" else str(row[grouping])
                groups[key].append(row)
            for value, group in sorted(groups.items()):
                output.append({
                    "comparison": name, "grouping": grouping,
                    "group_value": value, "rows": len(group),
                    "right_wins": sum(row["causal_outcome"] == "right_win"
                                      for row in group),
                    "left_wins": sum(row["causal_outcome"] == "left_win"
                                     for row in group),
                    "ties": sum(row["causal_outcome"] == "tie"
                                for row in group),
                    "left_certificates": sum(truth(row[
                        "left_strict_certificate"]) for row in group),
                    "right_certificates": sum(truth(row[
                        "right_strict_certificate"]) for row in group),
                    "downstream_sequence_changes": sum(truth(row[
                        "downstream_sequence_changed"]) for row in group),
                    "actual_split_decision_changes": sum(truth(row[
                        "actual_split_decisions_changed"]) for row in group),
                    "pre_split_divergences": sum(truth(row[
                        "first_divergence_before_split"]) for row in group),
                    "zero_split_trajectory_divergences": sum(truth(row[
                        "trajectory_diff_despite_zero_splits"]) for row in group),
                    "median_right_minus_left_proof_auc": median(row.get(
                        "right_minus_left_proof_auc") for row in group),
                    "median_right_over_left_exact_phase_ratio": median(row.get(
                        "right_over_left_exact_phase_ratio") for row in group),
                })
    return output


def gates(audits: list[dict[str, Any]], geometry: list[dict[str, Any]],
          normalization: list[dict[str, Any]], complete: bool) \
        -> tuple[str, dict[str, Any]]:
    valid = all(truth(row["exactness_certificate_audit_passed"])
                for row in audits)
    exposed_g = [row for row in geometry if truth(row["geometry_exposure"])]
    downstream_g = [row for row in exposed_g
                    if truth(row["downstream_sequence_changed"])]
    assessed = [row for row in exposed_g if row[
        "round35_expected_direction"] != "not_directionally_assessed"]
    direction_matches = [row for row in assessed
                         if truth(row["round35_direction_match"])]
    g_patterns = {row["round35_pattern"] for row in exposed_g}
    downstream_patterns = {row["round35_pattern"] for row in downstream_g}
    faster_evidence = any(row["round35_pattern"].startswith("3_")
                          for row in downstream_g)
    v50_regression_evidence = any(
        integer(row["V"]) == 50 and row["round35_pattern"].startswith("5_")
        for row in downstream_g)
    geometry_supported = all((
        valid, complete, len(exposed_g) >= 4, len(g_patterns) >= 2,
        len(downstream_g) >= 3,
        len(downstream_g) >= math.ceil(0.60 * len(exposed_g)),
        len(direction_matches) >= 4,
        bool(assessed) and len(direction_matches) >= math.ceil(
            0.60 * len(assessed)),
        faster_evidence, v50_regression_evidence,
        len(downstream_patterns) >= 2,
    ))
    exposed_n = [row for row in normalization
                 if truth(row["normalization_exposure"])]
    changed_n = [row for row in exposed_n
                 if truth(row["actual_split_decisions_changed"])]
    supporting_n = [row for row in changed_n
                    if not truth(row["first_divergence_before_split"])]
    consequence_n = [row for row in supporting_n
                     if row["causal_outcome"] != "tie"]
    normalization_supported = all((
        valid, complete, len(supporting_n) >= 3,
        len({row["round35_pattern"] for row in supporting_n}) >= 2,
        len(consequence_n) >= 2,
    ))
    values = {
        "validity_gate_passed": valid,
        "complete_56_row_stage_b": complete,
        "geometry_exposed_rows": len(exposed_g),
        "geometry_exposed_pattern_count": len(g_patterns),
        "geometry_downstream_changed_rows": len(downstream_g),
        "geometry_downstream_changed_fraction": ratio(
            len(downstream_g), len(exposed_g)),
        "geometry_directionally_assessable_rows": len(assessed),
        "geometry_direction_match_rows": len(direction_matches),
        "geometry_direction_match_fraction": ratio(
            len(direction_matches), len(assessed)),
        "geometry_weaker_simple_faster_evidence": faster_evidence,
        "geometry_v50_regression_evidence": v50_regression_evidence,
        "geometry_mechanism_supported": geometry_supported,
        "normalization_exposed_rows": len(exposed_n),
        "normalization_split_decision_changed_rows": len(changed_n),
        "normalization_supporting_rows_no_pre_split_divergence":
            len(supporting_n),
        "normalization_supporting_pattern_count": len({
            row["round35_pattern"] for row in supporting_n}),
        "normalization_material_consequence_rows": len(consequence_n),
        "split_normalization_mechanism_supported": normalization_supported,
    }
    if not complete:
        classification = "incomplete_stage_b"
    elif not valid:
        classification = "invalid"
    elif geometry_supported and normalization_supported:
        classification = "both_effects_matter"
    elif geometry_supported:
        classification = "decomposition_geometry_dominant"
    elif normalization_supported:
        classification = "split_normalization_coupling_dominant"
    else:
        classification = "neither_isolated_effect_sufficient"
    return classification, values


def markdown_table(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(fields) + " |"
    rule = "|" + "|".join("---" for _ in fields) + "|"
    body = []
    for row in rows:
        values = []
        for field in fields:
            value = row.get(field, "")
            values.append(f"{value:.4g}" if isinstance(value, float) else str(value))
        body.append("| " + " | ".join(values) + " |")
    return "\n".join((header, rule, *body))


def reports(prefix: str, per_arm: list[dict[str, Any]],
            geometry: list[dict[str, Any]], normalization: list[dict[str, Any]],
            fixed_proof: list[dict[str, Any]], audits: list[dict[str, Any]],
            classification: str, gate_values: dict[str, Any],
            missing: list[dict[str, Any]]) -> dict[str, Any]:
    complete = len(per_arm) == 56 and not missing
    representatives = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in geometry:
        grouped[row["round35_pattern"]].append(row)
    for pattern, rows in sorted(grouped.items()):
        representatives.append(max(rows, key=lambda row: abs(number(
            row.get("right_minus_left_proof_auc"), 0.0))))
    representative_doc = f"""# Round 36 representative trajectory report

This report selects one HH-versus-BW-P row per populated frozen Round-35
pattern by the largest absolute common-window proof-AUC difference.  It is a
derived view; the full event table and deterministic hashes are retained in
the companion CSV files.

{markdown_table(representatives, ('round35_pattern', 'instance_id', 'V', 'M',
    'left_actual_splits', 'right_actual_splits',
    'pre_first_split_sequence_changed', 'causal_outcome',
    'right_minus_left_proof_auc'))}

There are {sum(truth(row['trajectory_diff_despite_zero_splits']) for row in geometry)}
geometry comparisons whose downstream trajectory differs while both arms make
zero actual splits, and {sum(truth(row['first_divergence_before_split']) for row in geometry)}
whose first structural difference is already present before a split.  Such
rows cannot be attributed to rho.

All AUC values use the common observed window, left-continuous bound values,
no interpolation, and no post-last-event extension.
"""
    write_text(common.OUT / f"{prefix}representative_trajectory_report.md",
               representative_doc)
    conclusion_map = {
        "decomposition_geometry_dominant":
            "Decomposition geometry is the dominant identified interaction.",
        "split_normalization_coupling_dominant":
            "Split-normalization coupling is the dominant identified interaction.",
        "both_effects_matter": "Both isolated effects matter.",
        "neither_isolated_effect_sufficient":
            "Neither isolated effect explains the Round-35 behavior sufficiently.",
        "invalid": "The causal evidence is invalid because a correctness gate failed.",
        "incomplete_stage_b": "Stage B is incomplete; no mechanism conclusion is drawn.",
    }
    positive = classification in {
        "decomposition_geometry_dominant",
        "split_normalization_coupling_dominant", "both_effects_matter"}
    if classification == "decomposition_geometry_dominant":
        recommendation = (
            "Keep C6-HGA-FULL unchanged and freeze best-proof + wide-anchor + "
            "proof-normalization as a candidate for broader Stage C validation.")
    elif classification == "split_normalization_coupling_dominant":
        recommendation = (
            "Keep C6-HGA-FULL unchanged; validate anchor normalization broadly "
            "before any later rho sensitivity study.")
    elif classification == "both_effects_matter":
        recommendation = (
            "Keep C6-HGA-FULL unchanged and validate the combined, precisely "
            "frozen mechanism in Stage C before any rho study.")
    else:
        recommendation = (
            "Keep C6-HGA-FULL unchanged; do not run Stage C or tune rho from "
            "this evidence.")
    aggregate = group_summaries({
        "HH_vs_BW-P_geometry": geometry,
        "BW-P_vs_BW-A_normalization": normalization,
        "wide-proof_vs_best-proof_fixed-anchor": fixed_proof,
    })
    overall = [row for row in aggregate if row["grouping"] == "all"]
    proof_exposures = [row for row in fixed_proof
                       if truth(row.get("fixed_anchor_proof_exposure"))]
    proof_gap_preserved = sum(number(row[
        "right_final_common_ub_gap"]) <= number(row[
            "left_final_common_ub_gap"]) + TOL for row in proof_exposures)
    proof_auc_preserved = sum(number(row.get(
        "right_minus_left_proof_auc"), -math.inf) >= -MATERIAL_AUC
                              for row in proof_exposures)
    unresolved_preserved = sum(integer(row.get("right_open_leaf_count")) <=
                               integer(row.get("left_open_leaf_count"))
                               for row in proof_exposures)
    question_answers = {
        "question_A_geometry": {
            "supported": truth(gate_values[
                "geometry_mechanism_supported"]),
            "exposed_rows": gate_values["geometry_exposed_rows"],
            "downstream_changed_rows": gate_values[
                "geometry_downstream_changed_rows"],
            "direction_match_rows": gate_values[
                "geometry_direction_match_rows"],
            "answer": (
                "The predeclared geometry gate passes."
                if truth(gate_values["geometry_mechanism_supported"])
                else "The predeclared geometry gate does not pass."),
        },
        "question_B_normalization": {
            "supported": truth(gate_values[
                "split_normalization_mechanism_supported"]),
            "exposed_rows": gate_values["normalization_exposed_rows"],
            "split_decision_changed_rows": gate_values[
                "normalization_split_decision_changed_rows"],
            "answer": (
                "The predeclared split-normalization gate passes."
                if truth(gate_values[
                    "split_normalization_mechanism_supported"])
                else "The predeclared split-normalization gate does not pass."),
        },
        "question_C_splitting_timing": {
            "geometry_zero_split_trajectory_divergences": sum(truth(row[
                "trajectory_diff_despite_zero_splits"]) for row in geometry),
            "geometry_pre_split_divergences": sum(truth(row[
                "first_divergence_before_split"]) for row in geometry),
            "normalization_zero_split_trajectory_divergences": sum(truth(row[
                "trajectory_diff_despite_zero_splits"]) for row in normalization),
            "normalization_pre_split_divergences": sum(truth(row[
                "first_divergence_before_split"]) for row in normalization),
            "answer": "Rows diverging before any split, or with zero splits "
                      "in both arms, are explicitly excluded from rho claims.",
        },
        "question_D_fixed_anchor_stronger_proof": {
            "exposed_rows": len(proof_exposures),
            "final_common_ub_gap_improved_or_preserved_rows":
                proof_gap_preserved,
            "common_window_proof_auc_improved_or_preserved_rows":
                proof_auc_preserved,
            "unresolved_open_leaf_count_reduced_or_preserved_rows":
                unresolved_preserved,
            "wall_clock_monotonicity_claimed": False,
            "answer": "The fixed-anchor table reports cutoff/proof progress "
                      "without claiming universal wall-clock monotonicity.",
        },
    }
    summary = {
        "schema": "round36-final-audit-decision-v1",
        "classification": classification,
        "conclusion": conclusion_map[classification],
        "recommendation": recommendation,
        "completed_official_rows": len(per_arm),
        "expected_official_rows": 56,
        "missing_or_incomplete_rows": missing,
        "strict_certificates": sum(truth(row["strict_certificate"])
                                   for row in per_arm),
        "time_limited_valid_nocertificates": sum(
            truth(row["valid_time_limited_noncertificate"])
            for row in per_arm),
        "false_certificate_count": sum(truth(row["false_certificate"])
                                       for row in audits),
        "all_exactness_certificate_audits_passed": all(truth(row[
            "exactness_certificate_audit_passed"]) for row in audits),
        "classification_gates": gate_values,
        "causal_question_answers": question_answers,
        "stage_c_authorized_by_positive_signal": positive and complete,
        "rho_sensitivity_recommended": truth(gate_values.get(
            "split_normalization_mechanism_supported")),
        "automatic_promotion_performed": False,
        "validated_gurobi_mainline": "C6-HGA-FULL",
        "K": 4, "rho": 0.01, "threads": 1, "gurobi_seed": 0,
        "comparison_summaries": overall,
    }
    write_json(common.OUT / f"{prefix}final_audit_decision.json", summary)
    report = f"""# Round 36 final report

## Outcome

Classification: `{classification}`.

{conclusion_map[classification]}

Round 36 has {len(per_arm)}/56 checksum-complete official rows, with
{summary['strict_certificates']} strict certificates,
{summary['time_limited_valid_nocertificates']} valid noncertificates, and
{summary['false_certificate_count']} false certificates.

## Causal comparisons

{markdown_table(overall, ('comparison', 'rows', 'right_wins', 'left_wins',
    'ties', 'downstream_sequence_changes',
    'actual_split_decision_changes', 'pre_split_divergences'))}

HH versus BW-P is treated as a clean geometry intervention only where HGA is
the best proof incumbent.  BW-P versus BW-A holds proof and geometry fixed and
changes only the selected split-normalization denominator.  The fixed-anchor
proof table compares the wide self-arm with BW-A, so geometry and the effective
anchor normalization remain fixed while the verified proof cutoff strengthens.

## Decision gates

{markdown_table([gate_values], tuple(gate_values))}

The numeric gate definition was recorded in `analysis_gate_definition.md`
after the V12_M1 integration pilot and before the remaining matrix completed.

## Explicit causal questions

### A. Decomposition geometry

{question_answers['question_A_geometry']['answer']} There are
{question_answers['question_A_geometry']['exposed_rows']} clean geometry
exposures, with
{question_answers['question_A_geometry']['downstream_changed_rows']} downstream
sequence changes and
{question_answers['question_A_geometry']['direction_match_rows']} frozen-pattern
direction matches.

### B. Split normalization

{question_answers['question_B_normalization']['answer']} The comparison has
{question_answers['question_B_normalization']['exposed_rows']} denominator
exposures and
{question_answers['question_B_normalization']['split_decision_changed_rows']}
actual split-decision changes.

### C. Whether splitting can cause the observed effect

The geometry comparison contains
{question_answers['question_C_splitting_timing']['geometry_zero_split_trajectory_divergences']}
zero-split trajectory divergences and
{question_answers['question_C_splitting_timing']['geometry_pre_split_divergences']}
pre-split divergences. The normalization comparison contains
{question_answers['question_C_splitting_timing']['normalization_zero_split_trajectory_divergences']}
and
{question_answers['question_C_splitting_timing']['normalization_pre_split_divergences']},
respectively. Such observations are not attributed to rho.

### D. Stronger proof incumbent with geometry fixed

Across {question_answers['question_D_fixed_anchor_stronger_proof']['exposed_rows']}
fixed-anchor proof exposures, the stronger proof arm improves or preserves the
final common-UB gap in
{question_answers['question_D_fixed_anchor_stronger_proof']['final_common_ub_gap_improved_or_preserved_rows']}
rows, common-window proof AUC in
{question_answers['question_D_fixed_anchor_stronger_proof']['common_window_proof_auc_improved_or_preserved_rows']}
rows, and unresolved open-leaf count in
{question_answers['question_D_fixed_anchor_stronger_proof']['unresolved_open_leaf_count_reduced_or_preserved_rows']}
rows. Universal wall-clock monotonicity is not claimed.

## Correctness and interpretation boundary

- All-row exactness/certificate audit: {summary['all_exactness_certificate_audits_passed']}.
- False certificates: {summary['false_certificate_count']}.
- K remains 4, rho remains 0.01, and all commands use Seed 0 and one thread.
- Proof cutoffs and certificates use verified `U_proof`; `U_anchor` is confined
  to launch-frozen decomposition geometry and the explicit diagnostic
  normalization selector.
- Timing, Work, and nodes are reported as outcomes and are excluded from all
  deterministic sequence hashes.
- AUC uses common observed windows with left-continuous values, no
  interpolation, and no post-last-event extension.

## Recommendation

{recommendation}

No new mainline is promoted automatically.
"""
    write_text(common.OUT / f"{prefix}final_report.md", report)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    runs, missing = discover(args.allow_partial)
    prefix = "interim_" if args.allow_partial else ""
    per_arm, audits, mechanisms, decomposition = run_rows(runs)
    geometry, normalization, fixed_proof = comparisons(
        runs, per_arm, mechanisms)
    sequences = sequence_rows(per_arm, mechanisms)
    trajectories = trajectory_rows(runs, per_arm)
    lookahead, targets, closures = expanded_ledger_rows(runs, per_arm)
    grouped = group_summaries({
        "HH_vs_BW-P_geometry": geometry,
        "BW-P_vs_BW-A_normalization": normalization,
        "wide-proof_vs_best-proof_fixed-anchor": fixed_proof,
    })
    complete = len(per_arm) == 56 and not missing
    classification, gate_values = gates(
        audits, geometry, normalization, complete)
    for name, rows in (
        ("per_arm_results.csv", per_arm),
        ("initial_decomposition_audit.csv", decomposition),
        ("exactness_certificate_audit.csv", audits),
        ("interaction_sequence_hashes.csv", sequences),
        ("trajectory_events.csv", trajectories),
        ("child_lookahead_split_audit.csv", lookahead),
        ("native_target_audit.csv", targets),
        ("terminal_closure_audit.csv", closures),
        ("causal_geometry_comparison.csv", geometry),
        ("causal_normalization_comparison.csv", normalization),
        ("fixed_anchor_proof_comparison.csv", fixed_proof),
        ("causal_group_summaries.csv", grouped),
    ):
        write_csv(common.OUT / f"{prefix}{name}", rows)
    summary = reports(prefix, per_arm, geometry, normalization, fixed_proof,
                      audits, classification, gate_values, missing)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if classification not in {"invalid"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
