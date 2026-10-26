#!/usr/bin/env python3
"""Build the frozen Round 42 development evidence and performance gates."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Callable

import analyze_round41 as r41
import round42_common as common


MAJOR = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
STRONG = "round39_small_hard_V12_M3_Q30_slot08_seed1288546114"


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "yes"}


def number(value: Any, default: float = math.nan) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def gmean(values: list[float]) -> float:
    if not values or any(math.isnan(value) or value <= 0.0
                         for value in values):
        return math.nan
    if any(math.isinf(value) for value in values):
        return math.inf
    return math.exp(sum(math.log(value) for value in values) / len(values))


def ratio(candidate: float, baseline: float) -> float:
    if baseline > 0.0:
        return candidate / baseline
    return 1.0 if candidate == 0.0 else math.inf


def exact_start(run_dir: Path) -> float:
    return r41.exact_start(run_dir)


def command_result(run_dir: Path) -> tuple[dict[str, Any], dict[str, Any]] | None:
    command_path = run_dir / "command.json"
    result_path = run_dir / "result.json"
    if not command_path.is_file() or not result_path.is_file():
        return None
    return common.load_json(command_path), common.load_json(result_path)


def c6_row(instance_id: str, arm: str, tag: str) -> dict[str, Any] | None:
    run_dir = common.RUNS / f"c6__{instance_id}__{arm}__{tag}"
    pair = command_result(run_dir)
    if not pair:
        return None
    command, result = pair
    total = number(result.get("final_process_wall_time_seconds"),
                   number(result.get("runtime_seconds"), 0.0))
    exact = max(0.0, total - exact_start(run_dir))
    trajectory = r41.r40.c6_trajectory(run_dir, result)
    coverage_path = result.get("round42_sibling_coverage_ledger_path", "")
    block_rows: list[dict[str, str]] = []
    if coverage_path and Path(coverage_path).is_file():
        block_rows = [row for row in common.csv_rows(Path(coverage_path))
                      if row.get("block_id")]
    model_hashes = [row["model_sha256"] for row in block_rows
                    if row.get("model_sha256")]
    return {
        "instance_id": instance_id,
        "arm": {
            "c6-reference": "C6-HGA-FULL-K4",
            "k1-single-reference": "C6-K1-SINGLE",
            "sibling-core": "C6-SIBLING-CORE",
            "sibling-core-factored": "C6-SIBLING-CORE-FACTORED",
        }[arm],
        "run_id": run_dir.name,
        "kind": "external-c6",
        "executable_sha256": command.get("executable_sha256", ""),
        "process_cap_seconds": command.get("process_cap_seconds", ""),
        "status": result.get("status", ""),
        "objective": result.get("objective", ""),
        "valid_lower_bound": result.get(
            "external_gini_tree_global_lower_bound", ""),
        "verified_upper_bound": result.get(
            "external_gini_tree_verified_upper_bound", ""),
        "strict_certificate": truth(result.get(
            "strict_certified_original_problem")),
        "original_problem_verifier_passed": truth(
            result.get("verification", {}).get(
                "original_solution_feasible")),
        "parameter_roundtrip_valid": truth(result.get(
            "external_gini_tree_backend_parameter_roundtrip_valid")),
        "false_certificate": truth(result.get(
            "strict_certified_original_problem")) and not truth(
                result.get("verification", {}).get(
                    "original_solution_feasible")),
        "exact_phase_seconds": exact,
        "total_process_seconds": total,
        "solver_work": number(result.get("external_gini_tree_work"), 0.0),
        "solver_nodes": number(result.get("external_gini_tree_nodes"), 0.0),
        "independent_integer_proof_jobs": int(number(trajectory.get(
            "independent_integer_proof_jobs"), 0.0)),
        "native_optimize_calls": int(number(result.get(
            "external_gini_tree_optimize_count"), 0.0)),
        "model_sha256": ";".join(model_hashes),
        "model_variables": sum(int(row.get("model_columns") or 0)
                               for row in block_rows),
        "model_binary_variables": "",
        "model_integer_variables": "",
        "model_continuous_variables": "",
        "model_linear_constraints": sum(int(row.get("model_rows") or 0)
                                         for row in block_rows),
        "model_nonzeros": sum(int(row.get("model_nonzeros") or 0)
                              for row in block_rows),
        "model_general_constraints": sum(int(row.get("indicator_rows") or 0)
                                         for row in block_rows),
        "model_build_seconds": result.get(
            "external_gini_tree_model_build_seconds", ""),
        "model_read_seconds": result.get(
            "external_gini_tree_model_read_seconds", ""),
        "selector_variables": sum(int(row.get("selectors") or 0)
                                  for row in block_rows),
        "perspective_variables": sum(int(row.get(
            "perspective_variables") or 0) for row in block_rows),
        "root_lp_bound": "",
        "presolved_rows": "",
        "presolved_columns": "",
        "presolved_nonzeros": "",
        "sibling_pairs_considered": result.get(
            "round42_sibling_pairs_considered", 0),
        "sibling_pairs_coalesced": result.get(
            "round42_sibling_pairs_coalesced", 0),
        "sibling_replaced_leaf_count": result.get(
            "round42_sibling_replaced_leaf_count", 0),
        "sibling_atomic_coverage_events": result.get(
            "round42_sibling_atomic_coverage_events", 0),
        "sibling_fallback_events": result.get(
            "round42_sibling_fallback_events", 0),
        "sibling_unresolved_union_count": result.get(
            "round42_sibling_unresolved_union_count", 0),
        "coverage_valid": truth(result.get(
            "external_gini_tree_parent_child_coverage_valid")),
        "lifecycle_complete": truth(result.get(
            "external_gini_tree_lifecycle_complete")),
    }


def static_row(instance_id: str, arm: str, tag: str,
               report_arm: str) -> dict[str, Any] | None:
    run_dir = common.RUNS / f"static__{instance_id}__{arm}__mip__{tag}"
    pair = command_result(run_dir)
    if not pair:
        return None
    command, result = pair
    verifier = truth(result.get("round41_static_original_verifier_passed"))
    strict = truth(result.get("strict_certified_original_problem"))
    total = number(result.get("final_process_wall_time_seconds"),
                   number(result.get("runtime_seconds"), 0.0))
    return {
        "instance_id": instance_id,
        "arm": report_arm,
        "run_id": run_dir.name,
        "kind": "static-single-tree",
        "executable_sha256": command.get("executable_sha256", ""),
        "process_cap_seconds": command.get("process_cap_seconds", ""),
        "status": result.get("status", ""),
        "objective": result.get("objective", ""),
        "valid_lower_bound": result.get("round41_static_native_bound", ""),
        "verified_upper_bound": result.get("upper_bound", ""),
        "strict_certificate": strict,
        "original_problem_verifier_passed": verifier,
        "parameter_roundtrip_valid": truth(result.get(
            "round41_static_parameter_roundtrip_valid")),
        "false_certificate": strict and not verifier,
        "exact_phase_seconds": max(0.0, total - exact_start(run_dir)),
        "total_process_seconds": total,
        "solver_work": number(result.get("round41_static_solver_work"), 0.0),
        "solver_nodes": number(result.get("round41_static_solver_nodes"), 0.0),
        "independent_integer_proof_jobs": int(number(result.get(
            "round41_static_integer_proof_job_count"), 0.0)),
        "native_optimize_calls": int(number(result.get(
            "round41_static_optimize_count"), 0.0)),
        "model_sha256": result.get(
            "round41_static_segmented_model_sha256", ""),
        "model_variables": result.get("round41_static_model_variables", ""),
        "model_binary_variables": result.get(
            "round41_static_model_binary_variables", ""),
        "model_integer_variables": result.get(
            "round41_static_model_integer_variables", ""),
        "model_continuous_variables": result.get(
            "round41_static_model_continuous_variables", ""),
        "model_linear_constraints": result.get(
            "round41_static_model_linear_constraints", ""),
        "model_nonzeros": result.get("round41_static_model_nonzeros", ""),
        "model_general_constraints": result.get(
            "round41_static_model_general_constraints", ""),
        "model_build_seconds": result.get(
            "round41_static_model_build_seconds", ""),
        "model_read_seconds": result.get(
            "round41_static_model_read_seconds", ""),
        "selector_variables": result.get(
            "round41_static_selector_variables", ""),
        "perspective_variables": result.get(
            "round41_static_perspective_variables", ""),
        "root_lp_bound": result.get("round41_static_root_lp_bound", ""),
        "presolved_rows": result.get("round41_static_presolved_rows", ""),
        "presolved_columns": result.get(
            "round41_static_presolved_columns", ""),
        "presolved_nonzeros": result.get(
            "round41_static_presolved_nonzeros", ""),
        "sibling_pairs_considered": 0,
        "sibling_pairs_coalesced": 0,
        "sibling_replaced_leaf_count": 0,
        "sibling_atomic_coverage_events": 0,
        "sibling_fallback_events": 0,
        "sibling_unresolved_union_count": 0,
        "coverage_valid": truth(result.get(
            "round41_static_segmented_coverage_valid")),
        "lifecycle_complete": truth(result.get(
            "round41_static_one_native_mip_job")),
    }


def composite_row(instance_id: str, arm: str, tag: str,
                  report_arm: str) -> dict[str, Any] | None:
    run_dir = common.RUNS / f"composite__{instance_id}__{arm}__mip__{tag}"
    path = run_dir / "composite_summary.json"
    if not path.is_file():
        return None
    result = common.load_json(path)
    strict = truth(result.get("strict_global_union_certificate"))
    verifier = truth(result.get("original_problem_verifier_passed"))
    return {
        "instance_id": instance_id,
        "arm": report_arm,
        "run_id": run_dir.name,
        "kind": "fixed-external-block-cover",
        "executable_sha256": result.get("executable_sha256", ""),
        "process_cap_seconds": "per-component",
        "status": "optimal" if strict else "incomplete_or_rejected",
        "objective": result.get("objective", ""),
        "valid_lower_bound": result.get("valid_lower_bound", ""),
        "verified_upper_bound": result.get("objective", ""),
        "strict_certificate": strict,
        "original_problem_verifier_passed": verifier,
        "parameter_roundtrip_valid": truth(result.get("accepted_outcome")),
        "false_certificate": strict and not verifier,
        "exact_phase_seconds": number(result.get("exact_phase_seconds"), 0.0),
        "total_process_seconds": number(result.get(
            "total_process_seconds"), 0.0),
        "solver_work": number(result.get("solver_work"), 0.0),
        "solver_nodes": number(result.get("solver_nodes"), 0.0),
        "independent_integer_proof_jobs": result.get(
            "independent_integer_proof_jobs", 0),
        "native_optimize_calls": result.get("native_optimize_calls", 0),
        "model_sha256": ";".join(result.get(
            "component_model_sha256", [])),
        "model_variables": result.get("model_variables", ""),
        "model_binary_variables": result.get(
            "model_binary_variables", ""),
        "model_integer_variables": result.get(
            "model_integer_variables", ""),
        "model_continuous_variables": result.get(
            "model_continuous_variables", ""),
        "model_linear_constraints": result.get(
            "model_linear_constraints", ""),
        "model_nonzeros": result.get("model_nonzeros", ""),
        "model_general_constraints": result.get(
            "model_general_constraints", ""),
        "model_build_seconds": result.get("model_build_seconds", ""),
        "model_read_seconds": result.get("model_read_seconds", ""),
        "selector_variables": "",
        "perspective_variables": "",
        "root_lp_bound": "",
        "presolved_rows": "",
        "presolved_columns": "",
        "presolved_nonzeros": "",
        "sibling_pairs_considered": 0,
        "sibling_pairs_coalesced": 0,
        "sibling_replaced_leaf_count": 0,
        "sibling_atomic_coverage_events": 0,
        "sibling_fallback_events": 0,
        "sibling_unresolved_union_count": 0,
        "coverage_valid": truth(result.get("complete_gap_free_cover")),
        "lifecycle_complete": result.get("native_optimize_calls", 0) ==
            result.get("independent_integer_proof_jobs", 0),
    }


ARM_LOADERS: list[tuple[str, Callable[[str], dict[str, Any] | None]]] = [
    ("C6-HGA-FULL-K4", lambda i: c6_row(
        i, "c6-reference", "development_reference")),
    ("C6-K1-SINGLE", lambda i: c6_row(
        i, "k1-single-reference", "development_k1_reference")),
    ("EXTERNAL-K2-FIXED", lambda i: composite_row(
        i, "external-k2-fixed", "development_same_k", "EXTERNAL-K2-FIXED")),
    ("ST-K2-P-CORE", lambda i: static_row(
        i, "st-k2-p-core-reference", "development_same_k", "ST-K2-P-CORE")),
    ("ST-K4-P-CORE", lambda i: static_row(
        i, "st-k4-p-core", "development_family_a_base", "ST-K4-P-CORE")),
    ("ST-K4-P-CORE-HIERARCHICAL", lambda i: static_row(
        i, "st-k4-p-core-hierarchical",
        "development_family_a_hierarchical",
        "ST-K4-P-CORE-HIERARCHICAL")),
    ("PAIRED-K4", lambda i: composite_row(
        i, "paired-k4", "development_family_b_base", "PAIRED-K4")),
    ("PAIRED-K4-FACTORED", lambda i: composite_row(
        i, "paired-k4-factored", "development_family_b_factored",
        "PAIRED-K4-FACTORED")),
    ("C6-SIBLING-CORE", lambda i: c6_row(
        i, "sibling-core", "development_family_c_base")),
    ("C6-SIBLING-CORE-FACTORED", lambda i: c6_row(
        i, "sibling-core-factored", "development_family_c_factored")),
]

REFERENCE_ARMS = {"C6-K1-SINGLE", "EXTERNAL-K2-FIXED", "ST-K2-P-CORE"}


def main() -> int:
    manifests = sorted(common.csv_rows(common.OUT / "development_manifest.csv"),
                       key=lambda row: int(row["serial_order"]))
    rows: list[dict[str, Any]] = []
    for item in manifests:
        for _, loader in ARM_LOADERS:
            row = loader(item["instance_id"])
            if row:
                rows.append({
                    "round_id": 42,
                    "experiment_group": "development",
                    "serial_order": item["serial_order"],
                    "diagnostic_role": item["diagnostic_role"],
                    **row,
                })
    if not rows:
        raise RuntimeError("no Round 42 development results found")
    common.write_csv(common.OUT / "per_run_results.csv", rows)

    by_key = {(row["instance_id"], row["arm"]): row for row in rows}
    comparisons: list[dict[str, Any]] = []
    candidates = [name for name, _ in ARM_LOADERS
                  if name not in {"C6-HGA-FULL-K4"}]
    for item in manifests:
        baseline = by_key.get((item["instance_id"], "C6-HGA-FULL-K4"))
        if not baseline:
            continue
        for candidate_name in candidates:
            candidate = by_key.get((item["instance_id"], candidate_name))
            if not candidate:
                continue
            work_ratio = ratio(number(candidate["solver_work"]),
                               number(baseline["solver_work"]))
            shifted_time_ratio = ratio(
                number(candidate["exact_phase_seconds"]) + 1.0,
                number(baseline["exact_phase_seconds"]) + 1.0)
            comparisons.append({
                "instance_id": item["instance_id"],
                "diagnostic_role": item["diagnostic_role"],
                "candidate": candidate_name,
                "baseline": "C6-HGA-FULL-K4",
                "candidate_work": candidate["solver_work"],
                "baseline_work": baseline["solver_work"],
                "work_ratio": work_ratio,
                "candidate_exact_phase_seconds": candidate[
                    "exact_phase_seconds"],
                "baseline_exact_phase_seconds": baseline[
                    "exact_phase_seconds"],
                "shifted_time_ratio": shifted_time_ratio,
                "materiality": "win" if work_ratio <= 0.95 else (
                    "loss" if work_ratio >= 1.05 else "tie"),
                "catastrophic_both_above_1_25": (
                    work_ratio > 1.25 and shifted_time_ratio > 1.25),
                "baseline_strict_certificate": baseline[
                    "strict_certificate"],
                "candidate_strict_certificate": candidate[
                    "strict_certificate"],
                "certificate_regression": (
                    truth(baseline["strict_certificate"]) and
                    not truth(candidate["strict_certificate"])),
                "false_certificate": candidate["false_certificate"],
            })
    common.write_csv(common.OUT / "development_comparison.csv", comparisons)

    ranking: list[dict[str, Any]] = []
    for candidate_name in candidates:
        if candidate_name in REFERENCE_ARMS:
            continue
        selected = [row for row in comparisons
                    if row["candidate"] == candidate_name]
        if not selected:
            continue
        major = next((row for row in selected
                      if row["instance_id"] == MAJOR), None)
        strong = next((row for row in selected
                       if row["instance_id"] == STRONG), None)
        complete = len(selected) == len(manifests)
        false_certificates = sum(truth(row["false_certificate"])
                                 for row in selected)
        certificate_regressions = sum(truth(row["certificate_regression"])
                                      for row in selected)
        catastrophic = sum(truth(row["catastrophic_both_above_1_25"])
                           for row in selected)
        work_gmean = gmean([number(row["work_ratio"]) for row in selected])
        time_gmean = gmean([number(row["shifted_time_ratio"])
                            for row in selected])
        gate = bool(
            complete and false_certificates == 0 and
            certificate_regressions == 0 and major and strong and
            number(major["work_ratio"]) <= 0.80 and
            number(major["shifted_time_ratio"]) <= 0.80 and
            number(strong["work_ratio"]) <= 1.10 and
            number(strong["shifted_time_ratio"]) <= 1.10 and
            work_gmean <= 0.90 and time_gmean <= 0.95 and
            catastrophic == 0)
        model_sizes = [number(row["model_nonzeros"])
                       for row in rows if row["arm"] == candidate_name and
                       str(row["model_nonzeros"]) != ""]
        ranking.append({
            "candidate": candidate_name,
            "development_rows": len(selected),
            "complete_development_panel": complete,
            "false_certificates": false_certificates,
            "certificate_regressions": certificate_regressions,
            "catastrophic_regressions": catastrophic,
            "geometric_mean_work_ratio": work_gmean,
            "geometric_mean_shifted_time_ratio": time_gmean,
            "major_fragmentation_work_ratio": major["work_ratio"] if major else "",
            "major_fragmentation_shifted_time_ratio": (
                major["shifted_time_ratio"] if major else ""),
            "strong_positive_work_ratio": strong["work_ratio"] if strong else "",
            "strong_positive_shifted_time_ratio": (
                strong["shifted_time_ratio"] if strong else ""),
            "mean_model_nonzeros": (
                sum(model_sizes) / len(model_sizes) if model_sizes else ""),
            "development_gate_passed": gate,
        })
    ranking.sort(key=lambda row: (
        int(row["false_certificates"]),
        int(row["certificate_regressions"]),
        int(row["catastrophic_regressions"]),
        number(row["geometric_mean_work_ratio"]),
        number(row["geometric_mean_shifted_time_ratio"]),
        number(row["mean_model_nonzeros"], math.inf),
    ))
    for index, row in enumerate(ranking, 1):
        row["lexicographic_rank"] = index
    common.write_csv(common.OUT / "candidate_ranking.csv", ranking)

    common.write_csv(common.OUT / "certificate_audit.csv", [{
        "instance_id": row["instance_id"], "arm": row["arm"],
        "strict_certificate": row["strict_certificate"],
        "original_problem_verifier_passed": row[
            "original_problem_verifier_passed"],
        "parameter_roundtrip_valid": row["parameter_roundtrip_valid"],
        "false_certificate": row["false_certificate"],
        "coverage_valid": row["coverage_valid"],
        "lifecycle_complete": row["lifecycle_complete"],
        "status": row["status"],
    } for row in rows])
    common.write_csv(common.OUT / "model_size_comparison.csv", [{
        key: row[key] for key in (
            "instance_id", "arm", "model_sha256", "model_variables",
            "model_binary_variables", "model_integer_variables",
            "model_continuous_variables", "model_build_seconds",
            "model_read_seconds",
            "model_linear_constraints", "model_nonzeros",
            "model_general_constraints", "selector_variables",
            "perspective_variables", "presolved_rows", "presolved_columns",
            "presolved_nonzeros")
    } for row in rows])
    common.write_csv(common.OUT / "coverage_lifecycle_audit.csv", [{
        key: row[key] for key in (
            "instance_id", "arm", "coverage_valid", "lifecycle_complete",
            "sibling_pairs_considered", "sibling_pairs_coalesced",
            "sibling_replaced_leaf_count", "sibling_atomic_coverage_events",
            "sibling_fallback_events", "sibling_unresolved_union_count")
    } for row in rows])
    print({"per_run_rows": len(rows), "comparisons": len(comparisons),
           "ranked_candidates": len(ranking)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
