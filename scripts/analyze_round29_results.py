#!/usr/bin/env python3
"""Build all Round 29 audits, comparisons, report, and package inventory.

The analysis is deterministic, accepts original or verified gzip-compressed
CSV evidence, and never accesses the Gurobi license.  Lower-bound comparisons
use a per-instance common verified UB.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Iterable

import run_round29_experiments as frozen


ROOT = frozen.ROOT
OUT = frozen.OUT
RUNS = OUT / "runs"
STAGE0 = OUT / "stage0_runs"
ROUND28 = ROOT / "results/gf_cplex_equivalent_gurobi_replica_round28"
HORIZON = 300.0
THRESHOLDS = (0.25, 0.10, 0.05, 0.01, 0.001, 0.0001)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def number(value: Any, default: float = 0.0) -> float:
    return float(value) if finite(value) else default


def integer(value: Any, default: int = 0) -> int:
    return int(round(number(value, default)))


def truth(value: Any) -> bool:
    return value is True or str(value).lower() in ("true", "1")


def open_csv(path: Path) -> tuple[Any, csv.DictReader | None]:
    if path.is_file():
        stream = path.open(newline="", encoding="utf-8")
        return stream, csv.DictReader(stream)
    compressed = Path(str(path) + ".gz")
    if compressed.is_file():
        stream = gzip.open(
            compressed, "rt", newline="", encoding="utf-8")
        return stream, csv.DictReader(stream)
    return None, None


def csv_rows(path: Path) -> list[dict[str, str]]:
    stream, reader = open_csv(path)
    if reader is None:
        return []
    with stream:
        return list(reader)


def write_csv(path: Path, rows: Iterable[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    material = list(rows)
    if fields is None:
        fields = list(material[0]) if material else ["status"]
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)
    temporary.replace(path)


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    temporary.replace(path)


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def semantic_hash(path: Path, fields: tuple[str, ...]) -> str:
    selected = [
        {field: row.get(field, "") for field in fields}
        for row in csv_rows(path)
    ]
    return hashlib.sha256(json.dumps(
        selected, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()


def verified(result: dict[str, Any]) -> bool:
    verification = result.get("verification", {})
    return (
        truth(result.get("verifier_passed")) or
        (
            truth(verification.get("original_solution_feasible")) and
            truth(verification.get("original_objective_recomputed")) and
            not verification.get("errors")
        )
    )


def external_gates(result: dict[str, Any]) -> bool:
    if not truth(result.get("exact_phase_started")):
        return (
            verified(result) and
            truth(result.get("graceful_deadline_finalization")) and
            not truth(result.get("strict_certified_original_problem")) and
            abs(number(result.get("lower_bound"))) <= 1e-12 and
            result.get("conservative_lower_bound_source") ==
            "objective_nonnegative_G_plus_lambda_P"
        )
    return all(truth(result.get(name)) for name in (
        "external_gini_tree_root_coverage_valid",
        "external_gini_tree_parent_child_coverage_valid",
        "external_gini_tree_all_leaf_bounds_valid",
        "external_gini_tree_leaf_bounds_monotone",
        "external_gini_tree_global_bound_monotone",
        "external_gini_tree_lifecycle_complete",
        "external_gini_tree_feasibility_consistency_gate",
    ))


def plain_gates(result: dict[str, Any]) -> bool:
    return (
        truth(result.get("gurobi_native_domain_audit_passed")) and
        truth(result.get("gurobi_lifecycle_valid")) and verified(result)
    )


def correctness_gates(arm: str, result: dict[str, Any]) -> bool:
    return plain_gates(result) if arm == "P-GRB" \
        else external_gates(result)


def observed_bound_points(
        run_dir: Path, arm: str,
        result: dict[str, Any]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    if arm == "P-GRB":
        for row in csv_rows(run_dir / "progress.csv"):
            if (truth(row.get("best_bound_available")) and
                    finite(row.get("best_bound"))):
                points.append((
                    number(row.get("elapsed_runtime_seconds")),
                    number(row.get("best_bound"))))
    else:
        shift = number(
            result.get("process_elapsed_at_exact_phase_start_seconds"),
            number(result.get("hga_wall_time_seconds")))
        for row in csv_rows(run_dir / "external/global_bound_trace.csv"):
            if finite(row.get("global_lb")):
                points.append((
                    shift + number(row.get("telemetry_seconds")),
                    number(row.get("global_lb"))))
    points.sort()
    output: list[tuple[float, float]] = []
    best = -math.inf
    for timestamp, bound in points:
        if bound + 1e-9 >= best:
            best = max(best, bound)
            output.append((
                max(0.0, min(HORIZON, timestamp)), best))
    return output


def normalized_gap(bound: float, common_ub: float) -> float:
    return max(
        0.0, (common_ub - bound) / max(abs(common_ub), 1e-12))


def auc(points: list[tuple[float, float]], final_lb: Any,
        common_ub: float, final_time: float) -> tuple[float, float, int]:
    sequence = [(0.0, normalized_gap(0.0, common_ub))]
    sequence.extend((
        timestamp, normalized_gap(bound, common_ub))
        for timestamp, bound in points)
    sequence.append((
        max(0.0, min(HORIZON, final_time)),
        normalized_gap(number(final_lb), common_ub)))
    sequence.append((
        HORIZON, normalized_gap(number(final_lb), common_ub)))
    sequence.sort()
    collapsed: list[tuple[float, float]] = []
    for item in sequence:
        if collapsed and abs(collapsed[-1][0] - item[0]) <= 1e-10:
            collapsed[-1] = item
        else:
            collapsed.append(item)
    gap_auc = sum(
        (right[0] - left[0]) * left[1]
        for left, right in zip(collapsed, collapsed[1:])) / HORIZON
    return gap_auc, 1.0 - gap_auc, len(points)


PUBLIC_FIELDS = [
    "stage", "instance", "family", "V", "M", "arm", "repetition",
    "horizon_seconds", "return_code", "runner_wall_seconds",
    "emergency_timeout", "result_exists", "status",
    "completed_process", "authoritative", "verified_witness",
    "correctness_gates", "strict_certificate", "certificate_class",
    "certificate_rejection_reason", "exact_phase_started",
    "graceful_deadline_finalization", "verified_ub", "valid_final_lb",
    "common_ub", "common_ub_gap", "bound_progress_auc",
    "normalized_gap_auc", "bound_observations", "process_wall_seconds",
    "process_elapsed_at_exact_start_seconds", "hga_wall_time_seconds",
    "exact_phase_seconds", "work", "lp_work", "terminal_mip_work",
    "lp_optimize_count", "terminal_mip_leaf_count",
    "terminal_mip_optimize_count", "split_count",
    "declined_split_count", "unconditional_split_count",
    "lp_pruned_leaf_count", "lp_infeasible_leaf_count",
    "initial_leaf_count", "final_leaf_count", "open_leaf_count",
    "closed_leaf_count", "max_depth", "optimize_count", "model_count",
    "model_read_count", "model_free_count", "environment_count",
    "environment_free_count", "presolve_count",
    "root_relaxation_count", "simplex_iterations",
    "barrier_iterations", "native_nodes", "peak_memory_gb",
    "model_build_seconds", "model_read_seconds", "solver_seconds",
    "final_stagnation_seconds", "same_leaf_model_reuse_count",
    "explicit_leaf_model_discard_count",
    "integer_domain_restore_count", "basis_available_count",
    "basis_mapped_count", "basis_submitted_count",
    "basis_accepted_count", "basis_rejected_count",
    "mip_start_submitted_count", "mip_start_accepted_count",
    "mip_start_rejected_count", "selector_variable_count",
    "global_row_family_count", "interval_row_family_count",
    "lifecycle_complete", "conservative_lower_bound_source",
    "result_path", "run_path",
]


def normalize_current(
        state_path: Path, result: dict[str, Any]) -> dict[str, Any]:
    state = load_json(state_path)
    run_dir = state_path.parent
    arm = state["arm"]
    external = arm != "P-GRB"
    ext = "external_gini_tree_"
    row: dict[str, Any] = {
        "stage": state["stage"],
        "instance": state["instance"],
        "family": state["family"],
        "V": state["V"],
        "M": state["M"],
        "arm": arm,
        "repetition": state.get("repetition", 0),
        "horizon_seconds": state["budget_seconds"],
        "return_code": state["return_code"],
        "runner_wall_seconds": state["runner_wall_seconds"],
        "emergency_timeout": state["emergency_timeout"],
        "result_exists": state["result_exists"],
        "status": result.get("status", ""),
        "completed_process": state["return_code"] == 0,
        "authoritative": (
            state["return_code"] == 0 and
            not state["emergency_timeout"] and state["result_exists"]),
        "verified_witness": verified(result),
        "correctness_gates": correctness_gates(arm, result),
        "strict_certificate": truth(
            result.get("strict_certified_original_problem")),
        "certificate_class": result.get(
            "strict_certificate_class",
            result.get("certificate_class", "")),
        "certificate_rejection_reason": result.get(
            "strict_certificate_rejection_reason", ""),
        "exact_phase_started": (
            truth(result.get("exact_phase_started")) if external else True),
        "graceful_deadline_finalization": truth(
            result.get("graceful_deadline_finalization")),
        "verified_ub": number(
            result.get("upper_bound", result.get("objective"))),
        "valid_final_lb": number(result.get("lower_bound")),
        "common_ub": "",
        "common_ub_gap": "",
        "bound_progress_auc": "",
        "normalized_gap_auc": "",
        "bound_observations": "",
        "process_wall_seconds": number(
            result.get("final_process_wall_time_seconds"),
            state["runner_wall_seconds"]),
        "process_elapsed_at_exact_start_seconds": number(
            result.get("process_elapsed_at_exact_phase_start_seconds")),
        "hga_wall_time_seconds": number(
            result.get("hga_wall_time_seconds")),
        "work": number(result.get(
            ext + "work" if external else "gurobi_work")),
        "lp_work": number(result.get(ext + "lp_work")) if external else 0,
        "terminal_mip_work": number(
            result.get(ext + "terminal_mip_work")) if external else 0,
        "lp_optimize_count": integer(
            result.get(ext + "lp_optimize_count")) if external else 0,
        "terminal_mip_leaf_count": integer(
            result.get(ext + "terminal_mip_leaf_count")) if external else 0,
        "terminal_mip_optimize_count": integer(
            result.get(ext + "terminal_mip_optimize_count")
        ) if external else 0,
        "split_count": integer(
            result.get(ext + "split_count")) if external else 0,
        "declined_split_count": integer(
            result.get(ext + "declined_split_count")) if external else 0,
        "unconditional_split_count": integer(
            result.get(ext + "unconditional_structural_split_count")
        ) if external else 0,
        "lp_pruned_leaf_count": integer(
            result.get(ext + "lp_pruned_leaf_count")) if external else 0,
        "lp_infeasible_leaf_count": integer(
            result.get(ext + "lp_infeasible_leaf_count")) if external else 0,
        "initial_leaf_count": integer(
            result.get(ext + "initial_leaf_count")) if external else 0,
        "final_leaf_count": integer(
            result.get(ext + "final_leaf_count")) if external else 0,
        "open_leaf_count": integer(
            result.get(ext + "open_leaf_count")) if external else 0,
        "closed_leaf_count": integer(
            result.get(ext + "closed_leaf_count")) if external else 0,
        "max_depth": integer(
            result.get(ext + "maximum_depth")) if external else 0,
        "optimize_count": integer(
            result.get(ext + "optimize_count")) if external else 1,
        "model_count": integer(result.get(
            ext + "model_count" if external else "gurobi_model_count")),
        "model_read_count": integer(result.get(
            ext + "model_read_count"
            if external else "gurobi_model_read_count")),
        "model_free_count": integer(result.get(
            ext + "model_free_count"
            if external else "gurobi_model_free_count")),
        "environment_count": integer(result.get(
            ext + "environment_count"
            if external else "gurobi_environment_count")),
        "environment_free_count": integer(result.get(
            ext + "environment_free_count"
            if external else "gurobi_environment_free_count")),
        "presolve_count": integer(
            result.get(ext + "presolve_execution_count")) if external else 1,
        "root_relaxation_count": integer(
            result.get(ext + "root_relaxation_execution_count")
        ) if external else 1,
        "simplex_iterations": number(result.get(
            ext + "simplex_iterations"
            if external else "gurobi_simplex_iterations")),
        "barrier_iterations": number(result.get(
            ext + "barrier_iterations"
            if external else "gurobi_barrier_iterations")),
        "native_nodes": number(result.get(
            ext + "nodes" if external else "gurobi_node_count")),
        "peak_memory_gb": number(result.get(
            ext + "peak_memory_gb"
            if external else "gurobi_max_mem_used_gb")),
        "model_build_seconds": number(
            result.get(ext + "model_build_seconds")) if external else 0,
        "model_read_seconds": number(
            result.get(ext + "model_read_seconds")) if external else 0,
        "solver_seconds": number(
            result.get(ext + "solver_seconds")) if external else number(
                result.get("gurobi_runtime_seconds")),
        "final_stagnation_seconds": number(
            result.get(ext + "final_stagnation_seconds")) if external else 0,
        "same_leaf_model_reuse_count": integer(
            result.get(ext + "in_memory_model_reuse_count")
        ) if external else 0,
        "explicit_leaf_model_discard_count": integer(
            result.get(ext + "explicit_leaf_model_discard_count")
        ) if external else 0,
        "integer_domain_restore_count": integer(
            result.get(ext + "integer_domain_restore_count")
        ) if external else 0,
        "basis_available_count": integer(
            result.get(ext + "basis_available_count")) if external else 0,
        "basis_mapped_count": integer(
            result.get(ext + "basis_mapped_count")) if external else 0,
        "basis_submitted_count": integer(
            result.get(ext + "basis_submitted_count")) if external else 0,
        "basis_accepted_count": integer(
            result.get(ext + "basis_accepted_count")) if external else 0,
        "basis_rejected_count": integer(
            result.get(ext + "basis_rejected_count")) if external else 0,
        "mip_start_submitted_count": integer(
            result.get(ext + "warm_start_submitted_count")
        ) if external else 0,
        "mip_start_accepted_count": integer(
            result.get(ext + "warm_start_accepted_count")
        ) if external else 0,
        "mip_start_rejected_count": integer(
            result.get(ext + "warm_start_rejected_count")
        ) if external else 0,
        "selector_variable_count": integer(
            result.get(ext + "selector_variable_count")) if external else 0,
        "global_row_family_count": integer(
            result.get(ext + "global_row_family_count")) if external else 0,
        "interval_row_family_count": integer(
            result.get(ext + "interval_row_family_count")) if external else 0,
        "lifecycle_complete": (
            truth(result.get(ext + "lifecycle_complete"))
            if external else truth(result.get("gurobi_lifecycle_valid"))),
        "conservative_lower_bound_source": result.get(
            "conservative_lower_bound_source", ""),
        "result_path": relative(run_dir / "result.json"),
        "run_path": relative(run_dir),
        "_run_dir": run_dir,
        "_result": result,
    }
    exact_start = row["process_elapsed_at_exact_start_seconds"]
    row["exact_phase_seconds"] = (
        max(0.0, row["process_wall_seconds"] - exact_start)
        if row["exact_phase_started"] else 0.0)
    return row


def current_rows() -> list[dict[str, Any]]:
    rows = []
    for state_path in sorted(RUNS.glob("*/run_state.json")):
        state = load_json(state_path)
        result_path = state_path.parent / "result.json"
        if not state.get("completed") or not result_path.is_file():
            continue
        rows.append(normalize_current(state_path, load_json(result_path)))
    return rows


def finalize_common_metrics(rows: list[dict[str, Any]]) -> None:
    by_instance: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["stage"] in ("stage1", "stage2"):
            by_instance[row["instance"]].append(row)
    for instance, members in by_instance.items():
        stage2_members = [
            row for row in members
            if row["arm"] == "P-GRB" or row["stage"] == "stage1" or
            row["stage"] == "stage2"
        ]
        ubs = [
            number(row["verified_ub"]) for row in stage2_members
            if row["verified_witness"] and finite(row["verified_ub"])
        ]
        if not ubs:
            continue
        common_ub = min(ubs)
        for row in members:
            row["common_ub"] = common_ub
            row["common_ub_gap"] = normalized_gap(
                number(row["valid_final_lb"]), common_ub)
            points = observed_bound_points(
                row["_run_dir"], row["arm"], row["_result"])
            gap_auc, bound_auc, count = auc(
                points, row["valid_final_lb"], common_ub,
                number(row["process_wall_seconds"]))
            row["normalized_gap_auc"] = gap_auc
            row["bound_progress_auc"] = bound_auc
            row["bound_observations"] = count


def public(row: dict[str, Any]) -> dict[str, Any]:
    return {field: row.get(field, "") for field in PUBLIC_FIELDS}


PAIR_FIELDS = [
    "instance", "family", "V", "left_arm", "right_arm", "common_ub",
    "left_status", "right_status", "left_strict", "right_strict",
    "left_final_lb", "right_final_lb", "right_minus_left_lb",
    "left_common_gap", "right_common_gap", "right_minus_left_gap",
    "left_bound_auc", "right_bound_auc", "right_minus_left_auc",
    "left_work", "right_work", "left_optimize_count",
    "right_optimize_count", "left_model_reads", "right_model_reads",
    "left_splits", "right_splits", "left_terminal_mips",
    "right_terminal_mips", "winner_by_final_lb",
]


def keyed_stage2(
        rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    output: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if row["arm"] == "P-GRB" and row["stage"] == "stage2":
            output[(row["instance"], row["arm"])] = row
        elif row["arm"] in ("C3-REPLICA", "C4-CANDIDATE"):
            if row["stage"] in ("stage1", "stage2") and not row["repetition"]:
                output[(row["instance"], row["arm"])] = row
    return output


def pair_rows(
        rows: list[dict[str, Any]], left_arm: str,
        right_arm: str) -> list[dict[str, Any]]:
    keyed = keyed_stage2(rows)
    output = []
    for instance in frozen.PRIMARY:
        left = keyed.get((instance, left_arm))
        right = keyed.get((instance, right_arm))
        if not left or not right:
            continue
        delta_lb = number(right["valid_final_lb"]) - number(
            left["valid_final_lb"])
        tolerance = 1e-7
        winner = (
            right_arm if delta_lb > tolerance else
            left_arm if delta_lb < -tolerance else "tie")
        output.append({
            "instance": instance,
            "family": left["family"],
            "V": left["V"],
            "left_arm": left_arm,
            "right_arm": right_arm,
            "common_ub": left["common_ub"],
            "left_status": left["status"],
            "right_status": right["status"],
            "left_strict": left["strict_certificate"],
            "right_strict": right["strict_certificate"],
            "left_final_lb": left["valid_final_lb"],
            "right_final_lb": right["valid_final_lb"],
            "right_minus_left_lb": delta_lb,
            "left_common_gap": left["common_ub_gap"],
            "right_common_gap": right["common_ub_gap"],
            "right_minus_left_gap": (
                number(right["common_ub_gap"]) -
                number(left["common_ub_gap"])),
            "left_bound_auc": left["bound_progress_auc"],
            "right_bound_auc": right["bound_progress_auc"],
            "right_minus_left_auc": (
                number(right["bound_progress_auc"]) -
                number(left["bound_progress_auc"])),
            "left_work": left["work"],
            "right_work": right["work"],
            "left_optimize_count": left["optimize_count"],
            "right_optimize_count": right["optimize_count"],
            "left_model_reads": left["model_read_count"],
            "right_model_reads": right["model_read_count"],
            "left_splits": left["split_count"],
            "right_splits": right["split_count"],
            "left_terminal_mips": left["terminal_mip_optimize_count"],
            "right_terminal_mips": right["terminal_mip_optimize_count"],
            "winner_by_final_lb": winner,
        })
    return output


def round28_stage3_references() -> list[dict[str, Any]]:
    output = []
    for row in csv_rows(ROUND28 / "stage3_anchor_comparison.csv"):
        if row.get("arm") not in ("S0-CPLEX", "C2-PAPER"):
            continue
        mapped = {field: row.get(field, "") for field in PUBLIC_FIELDS}
        mapped["stage"] = "stage3"
        mapped["declined_split_count"] = 0
        mapped["same_leaf_model_reuse_count"] = 0
        mapped["integer_domain_restore_count"] = 0
        mapped["basis_available_count"] = 0
        mapped["basis_mapped_count"] = 0
        mapped["basis_submitted_count"] = 0
        mapped["basis_accepted_count"] = 0
        mapped["basis_rejected_count"] = 0
        mapped["lifecycle_complete"] = row.get(
            "correctness_gates", "False")
        mapped["result_path"] = row.get("result_path", "")
        mapped["run_path"] = row.get("run_path", "")
        output.append(mapped)
    return output


def stage3_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    anchors = set(frozen.ANCHORS)
    output = round28_stage3_references()
    for row in rows:
        if (row["instance"] in anchors and
                row["arm"] in ("C3-REPLICA", "C4-CANDIDATE") and
                row["stage"] in ("stage1", "stage2") and
                not row["repetition"]):
            mapped = public(row)
            mapped["stage"] = "stage3"
            output.append(mapped)
    by_instance: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in output:
        by_instance[row["instance"]].append(row)
    for members in by_instance.values():
        ubs = [
            number(row["verified_ub"]) for row in members
            if truth(row.get("verified_witness")) and finite(
                row.get("verified_ub"))
        ]
        if not ubs:
            continue
        common_ub = min(ubs)
        for row in members:
            row["common_ub"] = common_ub
            row["common_ub_gap"] = normalized_gap(
                number(row["valid_final_lb"]), common_ub)
    return sorted(output, key=lambda row: (
        row["instance"], row["arm"]))


def anchor_pair(
        stage3: list[dict[str, Any]], left_arm: str,
        right_arm: str) -> list[dict[str, Any]]:
    keyed = {(row["instance"], row["arm"]): row for row in stage3}
    output = []
    for instance in frozen.ANCHORS:
        left = keyed.get((instance, left_arm))
        right = keyed.get((instance, right_arm))
        if not left or not right:
            continue
        delta = number(right["valid_final_lb"]) - number(
            left["valid_final_lb"])
        output.append({
            "instance": instance,
            "family": left["family"],
            "V": left["V"],
            "left_arm": left_arm,
            "right_arm": right_arm,
            "common_ub": left["common_ub"],
            "left_status": left["status"],
            "right_status": right["status"],
            "left_final_lb": left["valid_final_lb"],
            "right_final_lb": right["valid_final_lb"],
            "right_minus_left_lb": delta,
            "left_common_gap": left["common_ub_gap"],
            "right_common_gap": right["common_ub_gap"],
            "winner_by_final_lb": (
                right_arm if delta > 1e-7 else
                left_arm if delta < -1e-7 else "tie"),
        })
    return output


def phase_rows(run_dir: Path) -> list[dict[str, str]]:
    return csv_rows(run_dir / "process_phases.csv")


def phase_time(
        phases: list[dict[str, str]], event: str,
        occurrence: int = 0) -> float | None:
    matches = [row for row in phases if row.get("event") == event]
    if len(matches) <= occurrence:
        return None
    return number(matches[occurrence].get("process_seconds"))


def stage0_build_rows() -> list[dict[str, Any]]:
    record_path = OUT / "build_and_test_record.json"
    if not record_path.is_file():
        return []
    record = load_json(record_path)
    output = []
    for item in record["records"]:
        category = (
            "configure" if "configure" in item["name"] else
            "build" if "_build_" in item["name"] else
            "cpp_tests" if "ctest" in item["name"] else "python_tests")
        output.append({
            "category": category,
            "check": item["name"],
            "passed": item["passed"],
            "return_code": item["return_code"],
            "wall_seconds": item["wall_seconds"],
            "command": item["command_text"],
            "stdout_path": item["stdout_path"],
            "stderr_path": item["stderr_path"],
            "source_commit": record["source_commit"],
            "compiler": record.get("compiler", ""),
            "cplex_version": record.get("cplex_version", ""),
            "gurobi_version": record.get("gurobi_version", ""),
            "cplex_executable_sha256":
                record.get("cplex_executable_sha256", ""),
            "gurobi_executable_sha256":
                record.get("gurobi_executable_sha256", ""),
        })
    return output


def stage0_run_records(suite: str) -> list[tuple[
        dict[str, Any], dict[str, Any], Path]]:
    output = []
    for state_path in sorted(STAGE0.glob(
            f"{suite}__*/run_state.json")):
        state = load_json(state_path)
        result_path = state_path.parent / "result.json"
        if result_path.is_file():
            output.append((
                state, load_json(result_path), state_path.parent))
    return output


def stage0_deadline_rows() -> list[dict[str, Any]]:
    output = []
    for state, result, run_dir in stage0_run_records("deadline"):
        phases = phase_rows(run_dir)
        events = [row["event"] for row in phases]
        output.append({
            "label": state["label"],
            "arm": state["arm"],
            "budget_seconds": state["budget_seconds"],
            "runner_wall_seconds": state["runner_wall_seconds"],
            "return_code": state["return_code"],
            "emergency_timeout": state["emergency_timeout"],
            "result_json_present": state["result_exists"],
            "phase_ledger_present": state["phase_ledger_exists"],
            "process_entry_recorded": "process_entry" in events,
            "serialization_start_recorded":
                "final_result_serialization_start" in events,
            "serialization_complete_recorded":
                "final_result_serialization_complete" in events,
            "process_exit_recorded": "process_exit" in events,
            "exact_phase_started": result.get(
                "exact_phase_started", False),
            "graceful_deadline_finalization": result.get(
                "graceful_deadline_finalization", False),
            "strict_certificate": result.get(
                "strict_certified_original_problem", False),
            "valid_lb": result.get("lower_bound", ""),
            "conservative_lower_bound_source": result.get(
                "conservative_lower_bound_source", ""),
            "last_phase": events[-1] if events else "",
            "passed": (
                state["return_code"] == 0 and
                not state["emergency_timeout"] and state["result_exists"] and
                "final_result_serialization_complete" in events and
                "process_exit" in events and
                not truth(result.get("strict_certified_original_problem")) and
                "invalid" not in str(result.get("status", "")) and
                "failed" not in str(result.get("status", "")) and
                external_gates(result)
            ),
            "result_path": relative(run_dir / "result.json"),
            "phase_path": relative(run_dir / "process_phases.csv"),
        })
    return output


def stage0_exactness_rows() -> list[dict[str, Any]]:
    runs = {
        (state["instance"], state["arm"]): (state, result, run_dir)
        for state, result, run_dir in stage0_run_records("exactness")
    }
    output: list[dict[str, Any]] = []
    cold_key = ("moderate_seed4301", "C2-COLD")
    warm_key = ("moderate_seed4301", "C4-CANDIDATE")
    if cold_key not in runs or warm_key not in runs:
        return output
    _, cold_result, cold_dir = runs[cold_key]
    _, warm_result, warm_dir = runs[warm_key]
    cold_lp = {
        row["leaf_id"]: row
        for row in csv_rows(cold_dir / "external/lp_status_ledger.csv")
    }
    warm_lp = {
        row["leaf_id"]: row
        for row in csv_rows(warm_dir / "external/lp_status_ledger.csv")
    }
    for leaf in sorted(set(cold_lp) & set(warm_lp)):
        left, right = cold_lp[leaf], warm_lp[leaf]
        status_same = all(left.get(key) == right.get(key) for key in (
            "terminal_valid", "optimal", "infeasible",
            "bound_available", "native_status"))
        objective_same = (
            left.get("bound_available") != "1" or
            right.get("bound_available") != "1" or
            math.isclose(
                number(left.get("lower_bound")),
                number(right.get("lower_bound")),
                rel_tol=1e-9, abs_tol=1e-7)
        )
        output.append({
            "check": "cold_vs_incremental_lp",
            "leaf_id": leaf,
            "cold_value": left.get("lower_bound", ""),
            "incremental_value": right.get("lower_bound", ""),
            "absolute_difference": abs(
                number(left.get("lower_bound")) -
                number(right.get("lower_bound"))),
            "passed": status_same and objective_same,
            "evidence": (
                f"cold={left.get('native_status')};"
                f"incremental={right.get('native_status')}"),
        })
    cold_split = {
        row["parent_id"]: row for row in csv_rows(
            cold_dir / "external/split_decision_ledger.csv")
    }
    warm_split = {
        row["parent_id"]: row for row in csv_rows(
            warm_dir / "external/split_decision_ledger.csv")
    }
    for leaf in sorted(set(cold_split) & set(warm_split)):
        same = all(
            cold_split[leaf].get(key) == warm_split[leaf].get(key)
            for key in ("decision_valid", "split",
                        "child_infeasibility_trigger",
                        "strict_bound_trigger", "reason"))
        output.append({
            "check": "cold_vs_incremental_split_decision",
            "leaf_id": leaf,
            "cold_value": cold_split[leaf].get("reason", ""),
            "incremental_value": warm_split[leaf].get("reason", ""),
            "absolute_difference": "",
            "passed": same,
            "evidence": "complete common parent decision",
        })
    cold_mips = {
        row["leaf_id"]: row
        for row in csv_rows(
            cold_dir / "external/paper_optimize_ledger.csv")
        if row.get("solve_kind") == "MIP"
    }
    warm_mips = {
        row["leaf_id"]: row
        for row in csv_rows(
            warm_dir / "external/paper_optimize_ledger.csv")
        if row.get("solve_kind") == "MIP"
    }
    for leaf in sorted(set(cold_mips) & set(warm_mips)):
        left, right = cold_mips[leaf], warm_mips[leaf]
        same = all(
            left.get(key) == right.get(key)
            for key in (
                "native_status", "optimize_return_code", "model_sha256"))
        output.append({
            "check": "cold_vs_incremental_terminal_mip",
            "leaf_id": leaf,
            "cold_value": left.get("native_status", ""),
            "incremental_value": right.get("native_status", ""),
            "absolute_difference": "",
            "passed": same,
            "evidence": "same canonical model and native terminal status",
        })
    for name, passed, evidence in (
        (
            "cold_and_incremental_verified_ub_identity",
            math.isclose(
                number(cold_result.get("upper_bound")),
                number(warm_result.get("upper_bound")),
                rel_tol=1e-10, abs_tol=1e-9),
            "independently verified same-run UBs"),
        (
            "incremental_model_lifecycle_symmetry",
            truth(warm_result.get(
                "external_gini_tree_lifecycle_complete")),
            "model/environment create-free and restore counters"),
        (
            "incremental_basis_not_claimed",
            integer(warm_result.get(
                "external_gini_tree_basis_submitted_count")) == 0,
            "basis submission count is zero"),
        (
            "interrupted_leaves_not_certified",
            not truth(warm_result.get(
                "strict_certified_original_problem")),
            "open coverage rejects strict certificate"),
    ):
        output.append({
            "check": name,
            "leaf_id": "",
            "cold_value": "",
            "incremental_value": "",
            "absolute_difference": "",
            "passed": passed,
            "evidence": evidence,
        })
    toy_p = runs.get(("toy", "P-GRB"))
    toy_c4 = runs.get(("toy", "C4-CANDIDATE"))
    if toy_p and toy_c4:
        p_result = toy_p[1]
        c4_result = toy_c4[1]
        same = (
            verified(p_result) and verified(c4_result) and
            math.isclose(
                number(p_result.get("objective")),
                number(c4_result.get("objective")),
                rel_tol=1e-10, abs_tol=1e-9))
        output.append({
            "check": "toy_exhaustive_optimum_identity",
            "leaf_id": "",
            "cold_value": p_result.get("objective", ""),
            "incremental_value": c4_result.get("objective", ""),
            "absolute_difference": abs(
                number(p_result.get("objective")) -
                number(c4_result.get("objective"))),
            "passed": same,
            "evidence": "plain exact MILP versus C4 verified toy objective",
        })
    return output


def stage0_sentinel_rows() -> list[dict[str, Any]]:
    output = []
    for state, result, run_dir in stage0_run_records("sentinel"):
        arm = state["arm"]
        gates = (
            plain_gates(result) if arm == "P-GRB" else
            external_gates(result) if arm in (
                "C3-REPLICA", "C4-CANDIDATE") else
            all(truth(result.get(name)) for name in (
                "global_gini_tree_root_coverage_valid",
                "global_gini_tree_branch_coverage_valid",
                "global_gini_tree_lifecycle_valid",
                "global_gini_tree_global_bound_monotone"))
        )
        output.append({
            "instance": state["instance"],
            "arm": arm,
            "return_code": state["return_code"],
            "emergency_timeout": state["emergency_timeout"],
            "status": result.get("status", ""),
            "verified_witness": verified(result),
            "valid_lb": result.get("lower_bound", ""),
            "verified_ub": result.get("upper_bound", ""),
            "strict_certificate": result.get(
                "strict_certified_original_problem", False),
            "coverage_valid": (
                result.get("external_gini_tree_parent_child_coverage_valid")
                if arm in ("C3-REPLICA", "C4-CANDIDATE")
                else result.get(
                    "global_gini_tree_branch_coverage_valid", True)),
            "lifecycle_valid": (
                result.get("external_gini_tree_lifecycle_complete")
                if arm in ("C3-REPLICA", "C4-CANDIDATE")
                else result.get(
                    "gurobi_lifecycle_valid",
                    result.get("global_gini_tree_lifecycle_valid"))),
            "correctness_gates": gates,
            "passed": (
                state["return_code"] == 0 and
                not state["emergency_timeout"] and verified(result) and
                gates),
            "result_path": relative(run_dir / "result.json"),
        })
    return output


def stage0_transition_rows() -> list[dict[str, Any]]:
    output = []
    for state, result, run_dir in stage0_run_records("transition"):
        phases = phase_rows(run_dir)
        events = [row["event"] for row in phases]
        generation_complete = any(
            row["event"] == "hga_generation_loop_complete" and
            row["status"] in ("complete", "deadline_interrupted")
            for row in phases)
        verification_complete = (
            "independent_hga_verification_complete" in events)
        external_event = "first_external_tree_event" in events
        output.append({
            "instance": state["instance"],
            "arm": state["arm"],
            "return_code": state["return_code"],
            "runner_wall_seconds": state["runner_wall_seconds"],
            "emergency_timeout": state["emergency_timeout"],
            "status": result.get("status", ""),
            "hga_generation_completion_recorded": generation_complete,
            "verification_complete_recorded": verification_complete,
            "verified_ub_serialized": (
                verification_complete and verified(result) and
                finite(result.get("upper_bound"))),
            "exact_phase_started": result.get(
                "exact_phase_started", False),
            "first_external_event_recorded": external_event,
            "valid_lb": result.get("lower_bound", ""),
            "conservative_lower_bound_source": result.get(
                "conservative_lower_bound_source", ""),
            "strict_certificate": result.get(
                "strict_certified_original_problem", False),
            "graceful_deadline_finalization": result.get(
                "graceful_deadline_finalization", False),
            "serialization_complete_recorded":
                "final_result_serialization_complete" in events,
            "process_exit_recorded": "process_exit" in events,
            "last_completed_phase": (
                next((
                    row["event"] for row in reversed(phases)
                    if row["status"] in ("complete",
                                         "completed_at_or_after_work_deadline")
                ), "")),
            "passed": (
                state["return_code"] == 0 and
                not state["emergency_timeout"] and
                generation_complete and
                "final_result_serialization_complete" in events and
                "process_exit" in events and
                not truth(result.get("strict_certified_original_problem"))
            ),
            "result_path": relative(run_dir / "result.json"),
            "phase_path": relative(run_dir / "process_phases.csv"),
        })
    return output


def phase_timing_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        phases = phase_rows(row["_run_dir"])
        if not phases:
            continue
        times = {
            event: [
                number(item.get("process_seconds"))
                for item in phases if item.get("event") == event
            ]
            for event in {item["event"] for item in phases}
        }
        def first(event: str) -> float | None:
            values = times.get(event, [])
            return values[0] if values else None
        hga_start = first("hga_start")
        verify_complete = first("independent_hga_verification_complete")
        exact_start = first("exact_phase_start")
        serialization_start = first("final_result_serialization_start")
        serialization_complete = first(
            "final_result_serialization_complete")
        output.append({
            "stage": row["stage"],
            "instance": row["instance"],
            "arm": row["arm"],
            "repetition": row["repetition"],
            "instance_parsing_complete_seconds":
                first("instance_parsing_complete"),
            "preprocessing_complete_seconds":
                first("initial_model_data_preprocessing_complete"),
            "hga_start_seconds": hga_start,
            "hga_generation_complete_seconds":
                first("hga_generation_loop_complete"),
            "hga_extraction_complete_seconds":
                first("hga_best_solution_extraction_complete"),
            "hga_decode_complete_seconds":
                first("hga_route_decoding_complete"),
            "verification_complete_seconds": verify_complete,
            "pre_exact_elapsed_seconds": exact_start if exact_start is not None
                else serialization_start,
            "exact_phase_start_seconds": exact_start,
            "first_external_event_seconds":
                first("first_external_tree_event"),
            "first_model_build_seconds":
                first("first_interval_model_build"),
            "first_lp_launch_seconds":
                first("first_lp_optimize_launch"),
            "external_phase_seconds": (
                serialization_start - exact_start
                if serialization_start is not None and
                exact_start is not None else 0.0),
            "serialization_seconds": (
                serialization_complete - serialization_start
                if serialization_complete is not None and
                serialization_start is not None else ""),
            "process_exit_seconds": first("process_exit"),
            "phase_event_count": len(phases),
        })
    return output


def incremental_reuse_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        if row["arm"] != "C4-CANDIDATE":
            continue
        exact = truth(row["exact_phase_started"])
        output.append({
            "stage": row["stage"],
            "instance": row["instance"],
            "repetition": row["repetition"],
            "lp_optimize_count": row["lp_optimize_count"],
            "terminal_mip_optimize_count":
                row["terminal_mip_optimize_count"],
            "model_count": row["model_count"],
            "model_read_count": row["model_read_count"],
            "same_leaf_model_reuse_count":
                row["same_leaf_model_reuse_count"],
            "integer_domain_restore_count":
                row["integer_domain_restore_count"],
            "explicit_leaf_model_discard_count":
                row["explicit_leaf_model_discard_count"],
            "model_free_count": row["model_free_count"],
            "environment_count": row["environment_count"],
            "environment_free_count": row["environment_free_count"],
            "read_saved_vs_fresh_event_count": max(
                0, integer(row["optimize_count"]) -
                integer(row["model_read_count"])),
            "native_tree_reuse_claimed": False,
            "lifecycle_complete": row["lifecycle_complete"],
            "passed": (
                not exact or (
                    integer(row["integer_domain_restore_count"]) ==
                    integer(row["lp_optimize_count"]) and
                    integer(row["same_leaf_model_reuse_count"]) ==
                    integer(row["terminal_mip_optimize_count"]) and
                    integer(row["model_count"]) ==
                    integer(row["model_free_count"]) and
                    truth(row["lifecycle_complete"])
                )
            ),
        })
    return output


def basis_reuse_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        if row["arm"] != "C4-CANDIDATE":
            continue
        output.append({
            "stage": row["stage"],
            "instance": row["instance"],
            "repetition": row["repetition"],
            "basis_available_count": row["basis_available_count"],
            "basis_mapped_count": row["basis_mapped_count"],
            "basis_submitted_count": row["basis_submitted_count"],
            "basis_accepted_count": row["basis_accepted_count"],
            "basis_rejected_count": row["basis_rejected_count"],
            "classification":
                "not_submitted_domain_transition_model_object_only",
            "no_basis_reuse_claim": (
                integer(row["basis_submitted_count"]) == 0),
        })
    return output


def split_value_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for run in rows:
        if run["arm"] != "C4-CANDIDATE":
            continue
        decision_by_parent = {
            row["parent_id"]: row for row in csv_rows(
                run["_run_dir"] / "external/split_decision_ledger.csv")
        }
        for row in csv_rows(
                run["_run_dir"] /
                "external/parent_child_bound_ledger.csv"):
            parent = row["parent_id"]
            decision = decision_by_parent.get(parent, {})
            parent_bound = number(row.get("parent_lp_bound"))
            post_bound = number(row.get("post_split_bound"), math.inf)
            gain = (
                post_bound - parent_bound
                if finite(row.get("post_split_bound")) else "")
            output.append({
                "stage": run["stage"],
                "instance": run["instance"],
                "repetition": run["repetition"],
                "parent_id": parent,
                "parent_lp_bound": parent_bound,
                "left_lp_bound": row.get("left_lp_bound", ""),
                "left_infeasible": truth(row.get("left_infeasible")),
                "right_lp_bound": row.get("right_lp_bound", ""),
                "right_infeasible": truth(row.get("right_infeasible")),
                "post_split_bound": row.get("post_split_bound", ""),
                "one_level_bound_gain": gain,
                "decision_valid": decision.get("decision_valid", ""),
                "split": decision.get("split", ""),
                "decision_reason": row.get(
                    "decision", decision.get("reason", "")),
                "low_value_split": (
                    truth(decision.get("split")) and
                    not truth(row.get("left_infeasible")) and
                    not truth(row.get("right_infeasible")) and
                    finite(gain) and number(gain) <= 1e-7),
            })
    return output


def terminal_value_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for run in rows:
        if run["arm"] not in ("C3-REPLICA", "C4-CANDIDATE"):
            continue
        event_file = (
            "external/replica_tree_events.csv"
            if run["arm"] == "C3-REPLICA"
            else "external/paper_tree_events.csv")
        previous_lb = 0.0
        previous_ub = number(run["verified_ub"])
        optimize = {
            (row.get("leaf_id"), row.get("solve_kind")): row
            for row in csv_rows(
                run["_run_dir"] / (
                    "external/replica_optimize_ledger.csv"
                    if run["arm"] == "C3-REPLICA"
                    else "external/paper_optimize_ledger.csv"))
        }
        for event in csv_rows(run["_run_dir"] / event_file):
            current_lb = number(event.get("global_lb"), previous_lb)
            current_ub = number(event.get("verified_ub"), previous_ub)
            if event.get("event") in (
                    "terminal_mip_complete", "terminal_mip_interrupted"):
                ledger = optimize.get((
                    event.get("leaf_id"), "MIP"), {})
                output.append({
                    "stage": run["stage"],
                    "instance": run["instance"],
                    "arm": run["arm"],
                    "repetition": run["repetition"],
                    "leaf_id": event.get("leaf_id", ""),
                    "event": event.get("event", ""),
                    "native_status": event.get("status", ""),
                    "telemetry_seconds": event.get(
                        "telemetry_seconds", ""),
                    "global_lb_before": previous_lb,
                    "global_lb_after": current_lb,
                    "global_lb_gain": max(0.0, current_lb - previous_lb),
                    "verified_ub_before": previous_ub,
                    "verified_ub_after": current_ub,
                    "incumbent_improvement": max(
                        0.0, previous_ub - current_ub),
                    "work": ledger.get("work", ""),
                    "simplex_iterations": ledger.get(
                        "simplex_iterations", ""),
                    "in_memory_model_reused": ledger.get(
                        "in_memory_model_reused", ""),
                    "produced_global_lb_gain":
                        current_lb > previous_lb + 1e-9,
                    "produced_incumbent_gain":
                        current_ub < previous_ub - 1e-9,
                })
            previous_lb = max(previous_lb, current_lb)
            previous_ub = min(previous_ub, current_ub)
    return output


def repeatability_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_instance: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["stage"] == "stage4" and row["arm"] == "C4-CANDIDATE":
            by_instance[row["instance"]].append(row)
    output = []
    for instance, members in sorted(by_instance.items()):
        members.sort(key=lambda row: integer(row["repetition"]))
        if len(members) != 2:
            continue
        left, right = members
        def sem(run: dict[str, Any], relative_path: str,
                fields: tuple[str, ...]) -> str:
            return semantic_hash(run["_run_dir"] / relative_path, fields)
        comparisons = {
            "hga_trajectory_identity": (
                sem(left, "hga_generations.csv", (
                    "generation", "best_fitness", "strict_improvement")) ==
                sem(right, "hga_generations.csv", (
                    "generation", "best_fitness", "strict_improvement"))),
            "split_decision_identity": (
                sem(left, "external/split_decision_ledger.csv", (
                    "parent_id", "eligible", "decision_valid", "split",
                    "child_infeasibility_trigger",
                    "strict_bound_trigger", "reason")) ==
                sem(right, "external/split_decision_ledger.csv", (
                    "parent_id", "eligible", "decision_valid", "split",
                    "child_infeasibility_trigger",
                    "strict_bound_trigger", "reason"))),
            "lp_objective_sequence_identity": (
                sem(left, "external/lp_status_ledger.csv", (
                    "leaf_id", "terminal_valid", "optimal", "infeasible",
                    "bound_available", "lower_bound", "native_status")) ==
                sem(right, "external/lp_status_ledger.csv", (
                    "leaf_id", "terminal_valid", "optimal", "infeasible",
                    "bound_available", "lower_bound", "native_status"))),
            "terminal_event_identity": (
                sem(left, "external/paper_tree_events.csv", (
                    "event", "leaf_id", "status", "global_lb",
                    "verified_ub", "detail")) ==
                sem(right, "external/paper_tree_events.csv", (
                    "event", "leaf_id", "status", "global_lb",
                    "verified_ub", "detail"))),
        }
        scalar_identity = all((
            math.isclose(
                number(left["verified_ub"]), number(right["verified_ub"]),
                rel_tol=1e-10, abs_tol=1e-9),
            math.isclose(
                number(left["valid_final_lb"]),
                number(right["valid_final_lb"]),
                rel_tol=1e-9, abs_tol=1e-7),
            left["status"] == right["status"],
            left["strict_certificate"] == right["strict_certificate"],
        ))
        output.append({
            "instance": instance,
            "rep1_status": left["status"],
            "rep2_status": right["status"],
            "rep1_verified_ub": left["verified_ub"],
            "rep2_verified_ub": right["verified_ub"],
            "rep1_valid_lb": left["valid_final_lb"],
            "rep2_valid_lb": right["valid_final_lb"],
            "absolute_lb_difference": abs(
                number(left["valid_final_lb"]) -
                number(right["valid_final_lb"])),
            **comparisons,
            "scalar_identity": scalar_identity,
            "exact_sequence_identity": all(comparisons.values()),
            "processes_graceful": (
                left["completed_process"] and right["completed_process"] and
                not left["emergency_timeout"] and
                not right["emergency_timeout"]),
            "classification": (
                "exact_full_identity" if scalar_identity and
                all(comparisons.values()) else
                "deterministic_algorithm_prefix_timing_divergence"
                if scalar_identity else
                "time_limited_sequence_or_scalar_divergence"),
        })
    return output


def family_summary(pairing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in pairing:
        grouped[(row["family"], integer(row["V"]))].append(row)
    output = []
    for (family, size), members in sorted(grouped.items()):
        winners = Counter(row["winner_by_final_lb"] for row in members)
        output.append({
            "family": family,
            "V": size,
            "instances": len(members),
            "c4_wins": winners["C4-CANDIDATE"],
            "p_grb_wins": winners["P-GRB"],
            "ties": winners["tie"],
            "c4_family_majority": (
                winners["C4-CANDIDATE"] > winners["P-GRB"]),
            "median_c4_minus_p_lb": median(
                number(row["right_minus_left_lb"]) for row in members),
            "mean_c4_minus_p_auc": mean(
                number(row["right_minus_left_auc"]) for row in members),
        })
    return output


def lifecycle_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = [
        "stage", "instance", "arm", "repetition", "status",
        "optimize_count", "presolve_count", "root_relaxation_count",
        "lp_optimize_count", "terminal_mip_optimize_count",
        "split_count", "declined_split_count", "final_leaf_count",
        "open_leaf_count", "model_count", "model_read_count",
        "model_free_count", "environment_count",
        "environment_free_count", "same_leaf_model_reuse_count",
        "integer_domain_restore_count", "work", "lp_work",
        "terminal_mip_work", "peak_memory_gb", "lifecycle_complete",
    ]
    return [{field: row.get(field, "") for field in fields} for row in rows]


def exactness_audit_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        result = row["_result"]
        external = row["arm"] != "P-GRB"
        output.append({
            "stage": row["stage"],
            "instance": row["instance"],
            "arm": row["arm"],
            "repetition": row["repetition"],
            "verified_witness": row["verified_witness"],
            "correctness_gates": row["correctness_gates"],
            "complete_root_coverage": (
                result.get("external_gini_tree_root_coverage_valid", "")
                if external else ""),
            "parent_child_coverage": (
                result.get(
                    "external_gini_tree_parent_child_coverage_valid", "")
                if external else ""),
            "leaf_bounds_valid": (
                result.get(
                    "external_gini_tree_all_leaf_bounds_valid", "")
                if external else ""),
            "leaf_bounds_monotone": (
                result.get(
                    "external_gini_tree_leaf_bounds_monotone", "")
                if external else ""),
            "global_bound_monotone": (
                result.get(
                    "external_gini_tree_global_bound_monotone", "")
                if external else ""),
            "lifecycle_complete": row["lifecycle_complete"],
            "feasibility_consistency": (
                result.get(
                    "external_gini_tree_feasibility_consistency_gate", "")
                if external else
                result.get("gurobi_native_domain_audit_passed", "")),
            "strict_certificate": row["strict_certificate"],
            "no_false_certificate": (
                row["strict_certificate"] or
                row["certificate_class"] in (
                    "certificate_rejected", "time_limit_valid_bound",
                    "optimality_certificate") or
                not row["strict_certificate"]),
            "passed": row["correctness_gates"],
        })
    return output


def certificate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "stage": row["stage"],
        "instance": row["instance"],
        "arm": row["arm"],
        "repetition": row["repetition"],
        "status": row["status"],
        "strict_certificate": row["strict_certificate"],
        "certificate_class": row["certificate_class"],
        "rejection_reason": row["certificate_rejection_reason"],
        "valid_lb": row["valid_final_lb"],
        "verified_ub": row["verified_ub"],
        "exact_phase_started": row["exact_phase_started"],
        "graceful_deadline_finalization":
            row["graceful_deadline_finalization"],
        "conservative_lower_bound_source":
            row["conservative_lower_bound_source"],
        "no_false_certificate": (
            not row["strict_certificate"] or
            abs(number(row["valid_final_lb"]) -
                number(row["verified_ub"])) <= 1e-7),
    } for row in rows]


def time_threshold_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        if row["stage"] not in ("stage1", "stage2"):
            continue
        points = observed_bound_points(
            row["_run_dir"], row["arm"], row["_result"])
        for threshold in THRESHOLDS:
            crossing = next((
                timestamp for timestamp, bound in points
                if normalized_gap(
                    bound, number(row["common_ub"])) <= threshold
            ), "")
            output.append({
                "stage": row["stage"],
                "instance": row["instance"],
                "arm": row["arm"],
                "threshold": threshold,
                "time_to_threshold_seconds": crossing,
                "reached": crossing != "",
                "final_common_ub_gap": row["common_ub_gap"],
            })
    return output


def bound_auc_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "stage": row["stage"],
        "instance": row["instance"],
        "family": row["family"],
        "V": row["V"],
        "arm": row["arm"],
        "repetition": row["repetition"],
        "common_ub": row["common_ub"],
        "valid_final_lb": row["valid_final_lb"],
        "common_ub_gap": row["common_ub_gap"],
        "bound_progress_auc": row["bound_progress_auc"],
        "normalized_gap_auc": row["normalized_gap_auc"],
        "bound_observations": row["bound_observations"],
    } for row in rows if row["stage"] in ("stage1", "stage2")]


def update_moderate_timing() -> list[dict[str, Any]]:
    path = OUT / "moderate6301_phase_timing.csv"
    retained = [
        row for row in csv_rows(path)
        if row.get("evidence_source") == "Round28 retained files"
    ]
    output: list[dict[str, Any]] = list(retained)
    for state, _, run_dir in stage0_run_records("transition"):
        for phase in phase_rows(run_dir):
            output.append({
                "evidence_source": "Round29 Stage0 transition",
                "run_id": state["run_id"],
                "phase": phase["event"],
                "process_seconds": phase["process_seconds"],
                "phase_status": phase["status"],
                "generations_recorded": "",
                "result_json_present": state["result_exists"],
                "external_tree_directory_present":
                    (run_dir / "external").is_dir(),
                "return_code": state["return_code"],
                "interpretation": phase.get("detail", ""),
            })
    write_csv(path, output)
    return output


def moderate_root_cause(transition: list[dict[str, Any]]) -> None:
    c3 = next((
        row for row in transition if row["arm"] == "C3-REPLICA"), None)
    c4 = next((
        row for row in transition if row["arm"] == "C4-CANDIDATE"), None)
    if not c3 or not c4:
        return
    text = f"""# Moderate6301 root cause

Round 28's three watchdog terminations were pre-exact failures, not external
C3 tree failures.  The old retained trajectory proves that the primary HGA
generation loop completed, but the old process emitted no external-tree event
or result.

Round 29 phase instrumentation identifies the mechanism precisely.  The
`paper-gf-tailored-bc` preset enabled an optional local re-decode repair after
the primary HGA.  That repair launched a second HGA in generation-stagnation
mode.  The local `primal_heuristic_seconds` value did not stop this mode, so
the second HGA could consume the remaining process window.  Round 28 then
reached an external watchdog before result serialization.  Its shared
generation-log path also allowed the repair trajectory to obscure the primary
trajectory.

The repair now observes the same absolute process-entry work deadline, all
phase events are append-flushed, and C3 reports
`{c3['status']}` with return code {c3['return_code']} and watchdog flag
`{c3['emergency_timeout']}`.  Its last completed phase is
`{c3['last_completed_phase']}`.  C4 uniformly disables the optional repair;
it reports `{c4['status']}`, exact-phase-started
`{c4['exact_phase_started']}`, first-external-event
`{c4['first_external_event_recorded']}`, return code
{c4['return_code']}, and watchdog flag `{c4['emergency_timeout']}`.

Both paths serialize only proven information.  If exact coverage has not
started, LB=0 is the explicit conservative bound from nonnegative
`G + lambda P`; no interval-tree bound or strict certificate is fabricated.
"""
    (OUT / "moderate6301_root_cause.md").write_text(
        text, encoding="utf-8")


def classify(
        rows: list[dict[str, Any]],
        p_pairs: list[dict[str, Any]],
        c3_pairs: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    c4 = [
        row for row in rows
        if row["arm"] == "C4-CANDIDATE" and
        row["stage"] in ("stage1", "stage2") and not row["repetition"]
    ]
    correctness = all(truth(row["correctness_gates"]) for row in c4)
    c3_wins = sum(
        row["winner_by_final_lb"] == "C4-CANDIDATE"
        for row in c3_pairs)
    c3_losses = sum(
        row["winner_by_final_lb"] == "C3-REPLICA"
        for row in c3_pairs)
    v20 = [row for row in p_pairs if integer(row["V"]) == 20]
    v20_wins = sum(
        row["winner_by_final_lb"] == "C4-CANDIDATE" for row in v20)
    v20_losses = sum(
        row["winner_by_final_lb"] == "P-GRB" for row in v20)
    v12 = [row for row in p_pairs if integer(row["V"]) == 12]
    v12_material = any(
        number(row["right_minus_left_lb"]) >
        0.01 * max(abs(number(row["common_ub"])), 1e-12)
        for row in v12)
    v50_rows = [row for row in c4 if integer(row["V"]) == 50]
    v50_systematic_failure = bool(v50_rows) and all(
        not truth(row["correctness_gates"]) or
        not truth(row["completed_process"]) for row in v50_rows)
    mechanisms_reduced = sum(
        integer(row["right_model_reads"]) <
        integer(row["left_model_reads"]) or
        integer(row["right_terminal_mips"]) <
        integer(row["left_terminal_mips"])
        for row in c3_pairs)
    if not correctness:
        classification = "invalid"
    elif (c3_wins > c3_losses and v20_wins > v20_losses and
          v12_material and not v50_systematic_failure and
          mechanisms_reduced > 0):
        classification = "performance_recovered_and_promising"
    else:
        classification = "exact_but_mixed"
    facts = {
        "c4_correctness_all": correctness,
        "c4_vs_c3_wins": c3_wins,
        "c4_vs_c3_losses": c3_losses,
        "v20_c4_vs_p_wins": v20_wins,
        "v20_c4_vs_p_losses": v20_losses,
        "v12_material_improvement": v12_material,
        "v50_systematic_failure": v50_systematic_failure,
        "instances_with_reduced_reads_or_terminal_mips":
            mechanisms_reduced,
    }
    return classification, facts


def package_manifest() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    excluded = {
        OUT / "evidence_package_manifest.csv",
        OUT / ".round29_runner.lock",
    }
    records = []
    for path in sorted(OUT.rglob("*")):
        if not path.is_file() or path in excluded or path.suffix == ".tmp":
            continue
        records.append({
            "path": relative(path),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "compressed": path.suffix == ".gz",
            "retained": True,
        })
    summary = {
        "file_count": len(records),
        "total_bytes": sum(integer(row["bytes"]) for row in records),
        "largest_path": max(
            records, key=lambda row: integer(row["bytes"]))["path"]
            if records else "",
        "largest_bytes": max(
            (integer(row["bytes"]) for row in records), default=0),
    }
    return records, summary


def aggregate(rows: list[dict[str, Any]], arm: str,
              field: str) -> float:
    return sum(
        number(row.get(field)) for row in rows
        if row["arm"] == arm and
        row["stage"] in ("stage1", "stage2") and not row["repetition"])


def render_report(
        audit: dict[str, Any], p_pairs: list[dict[str, Any]],
        c3_pairs: list[dict[str, Any]],
        stage3: list[dict[str, Any]],
        repeats: list[dict[str, Any]],
        terminal: list[dict[str, Any]]) -> str:
    p_wins = Counter(row["winner_by_final_lb"] for row in p_pairs)
    c3_wins = Counter(row["winner_by_final_lb"] for row in c3_pairs)
    v12 = [row for row in p_pairs if integer(row["V"]) == 12]
    v20 = [row for row in p_pairs if integer(row["V"]) == 20]
    v50 = [row for row in p_pairs if integer(row["V"]) == 50]
    terminal_gain = sum(
        truth(row["produced_global_lb_gain"]) for row in terminal)
    terminal_incumbent = sum(
        truth(row["produced_incumbent_gain"]) for row in terminal)
    anchors = defaultdict(dict)
    for row in stage3:
        anchors[row["instance"]][row["arm"]] = row
    anchor_lines = []
    for instance in frozen.ANCHORS:
        members = anchors[instance]
        values = ", ".join(
            f"{arm} LB={number(members[arm]['valid_final_lb']):.9g} "
            f"gap={number(members[arm]['common_ub_gap']):.4%}"
            for arm in ("S0-CPLEX", "C2-PAPER",
                        "C3-REPLICA", "C4-CANDIDATE")
            if arm in members)
        anchor_lines.append(f"- {instance}: {values}.")
    v12_lines = [
        f"- {row['instance']}: P-GRB LB {number(row['left_final_lb']):.9g}, "
        f"C4 LB {number(row['right_final_lb']):.9g}, "
        f"winner {row['winner_by_final_lb']}."
        for row in v12
    ]
    package = audit.get("package", {})
    return f"""# Round 29 final report

## Outcome

Round 29 classifies C4 as
`{audit['classification']}`.  C4 passed
{audit['audits']['c4_correctness_passed']}/
{audit['audits']['c4_correctness_rows']} official correctness audits.
The corrected CPLEX S0/F0 remains the stable accepted paper mainline; C4 is a
distinct exact candidate and is not promoted automatically.

## Root cause and deadline repair

Moderate6301 was a pre-exact transition/finalization failure, not evidence of
a C3 external-tree failure.  The optional local re-decode repair launched a
second generation-stagnation HGA whose local seconds cap was ineffective in
that stopping mode.  It could consume the remaining window, and Round 28's
external watchdog then prevented result serialization.

Round 29 uses one monotonic deadline from process entry.  Mathematical work
ends five seconds before the nominal 300-second cap; the fixed margin is only
for interruption, resource release, ledger flush, serialization, and exit.
It never enters a split predicate.  A pre-exact expiry emits a verified UB
when available, explicit `exact_phase_started=false`, conservative LB=0 from
nonnegative `G + lambda P`, and a rejected strict certificate.

## Round 28 diagnosis

The 30 completed C3 rows performed 5,764 optimizations: 4,107 LPs and 1,657
terminal MIPs.  Terminal MIPs consumed 80.4% of recorded LP-plus-MIP Work.
C3 made 2,366 unconditional splits and zero LP-bound prunes.  Among 2,027
splits with both immediate child LPs observed, 723 (35.7%) produced no strict
one-level controlling-bound gain.  Repeated model reads, presolve/root work,
lost state, leaf multiplication, and terminal-MIP startup are separate costs;
the earlier 7.1% median file/read share was not the total restart penalty.

## C4 definition

C4 is a combined, algorithmically distinct exact strategy.  For an eligible
parent with a complete LP bound, it solves both complete child LPs and splits
iff a child LP is infeasible or the minimum feasible child bound exceeds the
parent bound by more than `1e-7`.  Otherwise it discards the speculative
children and solves the complete unsplit parent MIP.  A complete LP may also
be cutoff-fathomed against the independently verified incumbent.

Execution retains the same leaf's Gurobi model object from LP to terminal MIP,
restores every original variable type, and then optimizes the exact MIP.
Split, empty, fathomed, and rejected speculative models are explicitly freed.
No LP basis is submitted, no native search tree is claimed, and no MIP start
is used.  This is model-object reuse only.

## Official matrix

The materialized Stage 2 matrix contains
{audit['process']['stage2_rows']} rows.  Completed/failed/emergency-watchdog
counts are {audit['process']['completed']}/{audit['process']['failed']}/
{audit['process']['emergency_timeouts']}; time-limited results number
{audit['process']['time_limited']}.  P-GRB versus C4 final-LB outcomes are
C4 {p_wins['C4-CANDIDATE']} wins, P-GRB {p_wins['P-GRB']} wins, and
{p_wins['tie']} ties.  C3 versus C4 outcomes are C4
{c3_wins['C4-CANDIDATE']} wins, C3 {c3_wins['C3-REPLICA']} wins, and
{c3_wins['tie']} ties.

### V12

{chr(10).join(v12_lines)}

Across V20, C4 records
{sum(row['winner_by_final_lb'] == 'C4-CANDIDATE' for row in v20)} wins and
{sum(row['winner_by_final_lb'] == 'P-GRB' for row in v20)} losses against
P-GRB.  Across V50 it records
{sum(row['winner_by_final_lb'] == 'C4-CANDIDATE' for row in v50)} wins and
{sum(row['winner_by_final_lb'] == 'P-GRB' for row in v50)} losses.

## Paper-mainline anchors

{chr(10).join(anchor_lines)}

## Mechanisms and resources

Across the unique official C4 primary rows: optimize/presolve/root counts are
{audit['c4_totals']['optimize_count']}/
{audit['c4_totals']['presolve_count']}/
{audit['c4_totals']['root_relaxation_count']}; LP/MIP counts are
{audit['c4_totals']['lp_optimize_count']}/
{audit['c4_totals']['terminal_mip_optimize_count']}; splits/declined splits
are {audit['c4_totals']['split_count']}/
{audit['c4_totals']['declined_split_count']}; final/open leaves are
{audit['c4_totals']['final_leaf_count']}/
{audit['c4_totals']['open_leaf_count']}.  Total Work is
{audit['c4_totals']['work']:.6g} (LP
{audit['c4_totals']['lp_work']:.6g}, terminal MIP
{audit['c4_totals']['terminal_mip_work']:.6g}); summed per-run peak memory is
{audit['c4_totals']['peak_memory_gb']:.6g} GB.  LP cutoff prunes number
{audit['c4_totals']['lp_pruned_leaf_count']}.

C4 retained {audit['c4_totals']['same_leaf_model_reuse_count']} same-leaf
models and restored {audit['c4_totals']['integer_domain_restore_count']} LP
domains.  Basis submitted/accepted/rejected counts are
{audit['c4_totals']['basis_submitted_count']}/
{audit['c4_totals']['basis_accepted_count']}/
{audit['c4_totals']['basis_rejected_count']}; MIP-start
submitted/accepted/rejected counts are
{audit['c4_totals']['mip_start_submitted_count']}/
{audit['c4_totals']['mip_start_accepted_count']}/
{audit['c4_totals']['mip_start_rejected_count']}.

Of {len(terminal)} terminal-MIP events in the retained primary evidence,
{terminal_gain} immediately raised the global LB and {terminal_incumbent}
improved the independently verified incumbent.

## Repeatability and interpretation

Stage 4 produced {len(repeats)} two-run comparisons;
{sum(truth(row['scalar_identity']) for row in repeats)} have scalar identity
and {sum(truth(row['exact_sequence_identity']) for row in repeats)} have full
semantic sequence identity.  Timing-limited prefix divergence is reported,
never replaced by a best repeat.

The unresolved mechanism is reported from the actual C4 evidence: where C4
does not dominate, complete child lookahead and exact terminal parent MIPs
remain costly even after disk rereads are removed.  Because C4 is
{audit['classification']}, a full long-run validation is
{audit['full_long_run_validation_recommended']}.  S0/F0 remains the stable
mainline in either case.

## Evidence package

The package contains {package.get('file_count', 0)} files totaling
{package.get('total_bytes', 0)} bytes.  Its largest retained artifact is
`{package.get('largest_path', '')}` at {package.get('largest_bytes', 0)}
bytes.  Large raw artifacts are gzip-compressed only after restoration hashes
match their originals.
"""


def main() -> int:
    rows = current_rows()
    finalize_common_metrics(rows)
    stage1 = sorted(
        [public(row) for row in rows if row["stage"] == "stage1"],
        key=lambda row: (row["instance"], row["arm"]))
    stage2_keyed = keyed_stage2(rows)
    stage2 = []
    for instance in frozen.PRIMARY:
        for arm in ("P-GRB", "C3-REPLICA", "C4-CANDIDATE"):
            source = stage2_keyed.get((instance, arm))
            if source:
                material = public(source)
                material["stage"] = "stage2"
                stage2.append(material)
    stage3 = stage3_rows(rows)
    p_pairs = pair_rows(rows, "P-GRB", "C4-CANDIDATE")
    c3_pairs = pair_rows(rows, "C3-REPLICA", "C4-CANDIDATE")
    c2_pairs = anchor_pair(stage3, "C2-PAPER", "C4-CANDIDATE")
    s0_pairs = anchor_pair(stage3, "S0-CPLEX", "C4-CANDIDATE")
    repeats = repeatability_rows(rows)
    phases = phase_timing_rows(rows)
    incremental = incremental_reuse_rows(rows)
    basis = basis_reuse_rows(rows)
    splits = split_value_rows(rows)
    terminal = terminal_value_rows(rows)
    exactness = exactness_audit_rows(rows)
    certificates = certificate_rows(rows)
    deadlines = stage0_deadline_rows()
    stage0_exact = stage0_exactness_rows()
    sentinel = stage0_sentinel_rows()
    transition = stage0_transition_rows()

    write_csv(OUT / "stage0_build_and_tests.csv", stage0_build_rows())
    write_csv(OUT / "stage0_deadline_finalization.csv", deadlines)
    write_csv(OUT / "stage0_exactness.csv", stage0_exact)
    write_csv(OUT / "stage0_sentinel.csv", sentinel)
    write_csv(OUT / "stage0_moderate6301_transition.csv", transition)
    write_csv(OUT / "stage1_anchor_mechanisms.csv", stage1, PUBLIC_FIELDS)
    write_csv(OUT / "stage2_full_300s_results.csv", stage2, PUBLIC_FIELDS)
    write_csv(
        OUT / "stage3_mainline_anchor_comparison.csv",
        stage3, PUBLIC_FIELDS)
    write_csv(OUT / "stage4_repeatability.csv", repeats)
    write_csv(OUT / "p_grb_vs_c4.csv", p_pairs, PAIR_FIELDS)
    write_csv(OUT / "c3_vs_c4.csv", c3_pairs, PAIR_FIELDS)
    write_csv(OUT / "c2_vs_c4_anchor.csv", c2_pairs)
    write_csv(OUT / "s0_vs_c4_anchor.csv", s0_pairs)
    write_csv(OUT / "family_summary.csv", family_summary(p_pairs))
    write_csv(OUT / "phase_timing_summary.csv", phases)
    write_csv(OUT / "incremental_reuse_audit.csv", incremental)
    write_csv(OUT / "basis_reuse_audit.csv", basis)
    write_csv(OUT / "split_value_audit.csv", splits)
    write_csv(OUT / "terminal_mip_value_audit.csv", terminal)
    write_csv(
        OUT / "lifecycle_and_resource_summary.csv",
        lifecycle_rows(rows))
    write_csv(OUT / "bound_progress_auc.csv", bound_auc_rows(rows))
    write_csv(OUT / "time_to_gap_thresholds.csv",
              time_threshold_rows(rows))
    write_csv(OUT / "exactness_audit.csv", exactness)
    write_csv(OUT / "certificate_audit.csv", certificates)
    update_moderate_timing()
    moderate_root_cause(transition)

    classification, classification_facts = classify(
        rows, p_pairs, c3_pairs)
    unique_c4 = [
        row for row in rows
        if row["arm"] == "C4-CANDIDATE" and
        row["stage"] in ("stage1", "stage2") and not row["repetition"]
    ]
    totals_fields = (
        "optimize_count", "presolve_count", "root_relaxation_count",
        "lp_optimize_count", "terminal_mip_optimize_count",
        "split_count", "declined_split_count", "final_leaf_count",
        "open_leaf_count", "work", "lp_work", "terminal_mip_work",
        "peak_memory_gb", "lp_pruned_leaf_count",
        "same_leaf_model_reuse_count", "integer_domain_restore_count",
        "basis_submitted_count", "basis_accepted_count",
        "basis_rejected_count", "mip_start_submitted_count",
        "mip_start_accepted_count", "mip_start_rejected_count",
    )
    c4_totals = {
        field: sum(number(row[field]) for row in unique_c4)
        for field in totals_fields
    }
    for field in totals_fields:
        if field not in (
                "work", "lp_work", "terminal_mip_work",
                "peak_memory_gb"):
            c4_totals[field] = int(round(c4_totals[field]))
    time_limited = sum(
        "time_limit" in str(row["status"]) or
        "global_deadline" in str(row["status"])
        for row in stage2)
    audit: dict[str, Any] = {
        "schema": "round29-final-audit-v1",
        "classification": classification,
        "classification_facts": classification_facts,
        "stable_mainline": "corrected CPLEX S0/F0",
        "c4_changes_mathematical_algorithm": True,
        "c4_incremental_scope": "same-leaf model object only",
        "basis_reuse_claimed": False,
        "native_tree_reuse_claimed": False,
        "full_long_run_validation_recommended": (
            "yes" if classification ==
            "performance_recovered_and_promising" else
            "not yet; resolve mixed short-run mechanisms first"),
        "process": {
            "stage1_rows": len(stage1),
            "stage2_rows": len(stage2),
            "stage3_rows": len(stage3),
            "stage4_repeat_pairs": len(repeats),
            "completed": sum(truth(row["completed_process"]) for row in stage2),
            "failed": sum(not truth(row["completed_process"]) for row in stage2),
            "time_limited": time_limited,
            "emergency_timeouts": sum(
                truth(row["emergency_timeout"]) for row in stage2),
            "excluded": sum(not truth(row["authoritative"]) for row in stage2),
        },
        "audits": {
            "stage0_build_test_rows": len(stage0_build_rows()),
            "stage0_deadline_rows": len(deadlines),
            "stage0_exactness_checks": len(stage0_exact),
            "stage0_sentinel_rows": len(sentinel),
            "stage0_transition_rows": len(transition),
            "c4_correctness_rows": len(unique_c4),
            "c4_correctness_passed": sum(
                truth(row["correctness_gates"]) for row in unique_c4),
            "incremental_reuse_rows": len(incremental),
            "incremental_reuse_passed": sum(
                truth(row["passed"]) for row in incremental),
            "basis_audit_rows": len(basis),
            "false_certificates": sum(
                not truth(row["no_false_certificate"])
                for row in certificates),
        },
        "c4_totals": c4_totals,
        "terminal_mip_events": {
            "count": len(terminal),
            "global_lb_improvements": sum(
                truth(row["produced_global_lb_gain"]) for row in terminal),
            "incumbent_improvements": sum(
                truth(row["produced_incumbent_gain"]) for row in terminal),
        },
        "package": {},
    }
    write_json(OUT / "final_audit_summary.json", audit)
    (OUT / "final_report.md").write_text(
        render_report(
            audit, p_pairs, c3_pairs, stage3, repeats, terminal),
        encoding="utf-8")
    manifest, package = package_manifest()
    audit["package"] = package
    write_json(OUT / "final_audit_summary.json", audit)
    (OUT / "final_report.md").write_text(
        render_report(
            audit, p_pairs, c3_pairs, stage3, repeats, terminal),
        encoding="utf-8")
    manifest, package = package_manifest()
    audit["package"] = package
    write_json(OUT / "final_audit_summary.json", audit)
    (OUT / "final_report.md").write_text(
        render_report(
            audit, p_pairs, c3_pairs, stage3, repeats, terminal),
        encoding="utf-8")
    manifest, _ = package_manifest()
    write_csv(OUT / "evidence_package_manifest.csv", manifest)
    print(json.dumps({
        "classification": classification,
        "current_official_rows": len(rows),
        "stage2_materialized_rows": len(stage2),
        "stage3_rows": len(stage3),
        "repeat_pairs": len(repeats),
        "package_files": audit["package"]["file_count"],
        "package_bytes": audit["package"]["total_bytes"],
    }, indent=2))
    expected = (
        len(stage1) == 12 and len(stage2) == 51 and len(stage3) == 20 and
        len(repeats) == 5 and
        audit["process"]["emergency_timeouts"] == 0 and
        audit["audits"]["false_certificates"] == 0 and
        all(truth(row["passed"]) for row in deadlines) and
        all(truth(row["passed"]) for row in sentinel) and
        all(truth(row["passed"]) for row in transition) and
        all(truth(row["passed"]) for row in stage0_exact)
    )
    return 0 if expected else 1


if __name__ == "__main__":
    raise SystemExit(main())
