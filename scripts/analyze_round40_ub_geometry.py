#!/usr/bin/env python3
"""Analyze Round 40 nested-dyadic geometry and proof trajectories."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import analyze_round40_k1 as k1
import round40_common as common


ENDPOINT_ID = "round39_small_hard_V12_M3_Q20_slot07_seed621538683"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compact(rows: list[dict[str, str]], fields: tuple[str, ...]) -> str:
    return ";".join("|".join(row.get(field, "") for field in fields)
                    for row in rows)


def expected_unresolved(row: dict[str, Any]) -> bool:
    lower = k1.number(row.get("valid_lower_bound"), math.nan)
    upper = k1.number(row.get("verified_upper_bound"), math.nan)
    return (
        row.get("instance_id") == ENDPOINT_ID and
        row.get("return_code") == 0 and
        not k1.truth(row.get("watchdog_timeout")) and
        not k1.truth(row.get("strict_certificate")) and
        row.get("certificate_class") == "certificate_rejected" and
        row.get("status") == "round31_c6_external_gini_tree_not_certified" and
        k1.truth(row.get("original_problem_verifier_passed")) and
        k1.truth(row.get("backend_parameter_roundtrip_valid")) and
        k1.integer(row.get("gurobi_presolve_effective"), -99) == -1 and
        math.isfinite(lower) and math.isfinite(upper) and
        lower <= upper and upper - lower > 1e-7)


def summarize(frozen: dict[str, str]) -> dict[str, Any] | None:
    run_dir = common.RUNS / frozen["run_id"]
    result_path = run_dir / "result.json"
    if not result_path.is_file():
        return None
    command = common.load_json(run_dir / "command.json")
    result = common.load_json(result_path)
    lower, upper = common.result_bounds(frozen["arm"], result)
    total = k1.number(result.get(
        "final_process_wall_time_seconds", result.get("runtime_seconds")))
    trajectory = k1.c6_trajectory(run_dir, result)
    global_trace = k1.rows_if_present(
        run_dir / "external" / "global_bound_trace.csv")
    controlling = compact(
        global_trace,
        ("event_type", "active_leaf", "valid_global_lower_bound",
         "verified_global_upper_bound", "event_source"))
    geometry_canonical = "|".join((
        str(result.get("round40_c6_ub_geometry", "")),
        format(k1.number(result.get("external_gini_tree_root_gamma_L")),
               ".17g"),
        format(k1.number(result.get("external_gini_tree_root_gamma_U")),
               ".17g"),
        format(k1.number(result.get(
            "external_gini_tree_anchor_grid_gamma_upper")), ".17g"),
        str(result.get("round40_c6_nested_dyadic_level", "")),
        str(result.get(
            "round40_c6_nested_dyadic_global_cell_count", "")),
        str(result.get("external_gini_tree_anchor_grid_cell_indices", "")),
        str(result.get("external_gini_tree_anchor_grid_endpoints", "")),
        str(result.get("external_gini_tree_active_initial_intervals", "")),
    ))
    row: dict[str, Any] = {
        **frozen,
        "return_code": command.get("return_code"),
        "watchdog_timeout": command.get("watchdog_timeout"),
        "total_process_seconds": total,
        "hga_startup_seconds": k1.number(
            result.get("hga_wall_time_seconds")),
        "exact_phase_seconds": max(0.0, total - k1.exact_start(run_dir)),
        "startup_verified_ub": result.get(
            "round36_proof_incumbent_launch"),
        "objective": result.get("objective"),
        "valid_lower_bound": lower,
        "verified_upper_bound": upper,
        "solver_work": k1.number(result.get("external_gini_tree_work")),
        "solver_nodes": k1.number(result.get("external_gini_tree_nodes")),
        "strict_certificate": k1.truth(result.get(
            "strict_certified_original_problem")),
        "certificate_class": result.get(
            "external_gini_tree_certificate_class"),
        "original_problem_verifier_passed": k1.truth(
            result.get("verification", {}).get("original_solution_feasible")),
        "backend_parameter_roundtrip_valid": k1.truth(result.get(
            "external_gini_tree_backend_parameter_roundtrip_valid")),
        "gurobi_presolve_effective": result.get(
            "gurobi_presolve_effective"),
        "status": result.get("status"),
        "reported_ub_geometry_policy": result.get(
            "round40_c6_ub_geometry"),
        "stable_root_upper": result.get(
            "external_gini_tree_anchor_grid_gamma_upper"),
        "nested_dyadic_level": result.get(
            "round40_c6_nested_dyadic_level"),
        "nested_dyadic_global_cell_count": result.get(
            "round40_c6_nested_dyadic_global_cell_count"),
        "nested_dyadic_reason": result.get(
            "round40_c6_nested_dyadic_reason"),
        "anchor_cell_indices": result.get(
            "external_gini_tree_anchor_grid_cell_indices"),
        "anchor_endpoints": result.get(
            "external_gini_tree_anchor_grid_endpoints"),
        "active_initial_intervals": result.get(
            "external_gini_tree_active_initial_intervals"),
        "truncated_initial_interval_count": result.get(
            "external_gini_tree_truncated_initial_interval_count"),
        "root_coverage_valid": result.get(
            "external_gini_tree_root_coverage_valid"),
        "geometry_sha256": digest(geometry_canonical),
        "initial_lp_model_sequence_sha256": digest(
            trajectory["initial_model_sha256"]),
        "controlling_leaf_sequence": controlling,
        "controlling_leaf_sequence_sha256": digest(controlling),
        **trajectory,
    }
    expected_policy = frozen["ub_geometry_policy"]
    candidate = expected_policy == "nested-dyadic-k4"
    stable_root_expected = (int(frozen["V"]) - 1.0) / int(frozen["V"])
    row["geometry_contract_passed"] = (
        row["reported_ub_geometry_policy"] == expected_policy and
        k1.truth(row["root_coverage_valid"]) and
        (not candidate or (
            1 <= k1.integer(row["initial_interval_count"]) <= 4 and
            math.isclose(k1.number(row["stable_root_upper"]),
                         stable_root_expected, rel_tol=0.0, abs_tol=1e-12) and
            k1.integer(row["nested_dyadic_global_cell_count"], 0) >= 1 and
            str(row["nested_dyadic_reason"]) in {
                "stable_root_finest_dyadic_prefix_with_at_most_target_cells",
                "empty_proof_range_single_degenerate_cell",
            })))
    row["exactness_passed"] = (
        row["return_code"] == 0 and
        not k1.truth(row["watchdog_timeout"]) and
        row["strict_certificate"] and
        row["original_problem_verifier_passed"] and
        row["backend_parameter_roundtrip_valid"] and
        k1.integer(row["gurobi_presolve_effective"], -99) == -1 and
        row["geometry_contract_passed"] and
        math.isfinite(lower) and math.isfinite(upper) and
        lower <= upper + 1e-7)
    return row


def comparisons(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[row["instance_id"]][row["arm"]] = row
    output: list[dict[str, Any]] = []
    for instance_id, arms in grouped.items():
        baseline = arms.get("C6-HGA-FULL-K4")
        candidate = arms.get("C6-NESTED-DYADIC-K4")
        if not baseline or not candidate:
            continue
        baseline_work = baseline["solver_work"]
        candidate_work = candidate["solver_work"]
        work_ratio = (1.0 if abs(baseline_work) <= 1e-12 and
                      abs(candidate_work) <= 1e-12 else
                      candidate_work / max(baseline_work, 1e-12))
        output.append({
            "instance_id": instance_id,
            "difficulty_stratum": candidate["difficulty_stratum"],
            "baseline_seconds": baseline["total_process_seconds"],
            "candidate_seconds": candidate["total_process_seconds"],
            "candidate_over_baseline_time_ratio": (
                candidate["total_process_seconds"] /
                baseline["total_process_seconds"]),
            "baseline_work": baseline_work,
            "candidate_work": candidate_work,
            "candidate_over_baseline_work_ratio": work_ratio,
            "baseline_nodes": baseline["solver_nodes"],
            "candidate_nodes": candidate["solver_nodes"],
            "baseline_initial_intervals": baseline["initial_interval_count"],
            "candidate_initial_intervals": candidate["initial_interval_count"],
            "baseline_integer_jobs":
                baseline["independent_integer_proof_jobs"],
            "candidate_integer_jobs":
                candidate["independent_integer_proof_jobs"],
            "baseline_geometry_sha256": baseline["geometry_sha256"],
            "candidate_geometry_sha256": candidate["geometry_sha256"],
            "geometry_changed": (
                baseline["geometry_sha256"] != candidate["geometry_sha256"]),
            "same_objective": math.isclose(
                k1.number(candidate["objective"]),
                k1.number(baseline["objective"]),
                rel_tol=0.0, abs_tol=1e-7),
            "both_exact": (k1.truth(baseline["exactness_passed"]) and
                           k1.truth(candidate["exactness_passed"])),
            "expected_unresolved": (
                expected_unresolved(baseline) and
                expected_unresolved(candidate)),
            "baseline_outcome_accepted": (
                k1.truth(baseline["exactness_passed"]) or
                expected_unresolved(baseline)),
            "candidate_outcome_accepted": (
                k1.truth(candidate["exactness_passed"]) or
                expected_unresolved(candidate)),
            "candidate_improved_endpoint_certificate": (
                expected_unresolved(baseline) and
                k1.truth(candidate["exactness_passed"])),
        })
    return output


def nested_geometry(upper: float, root: float,
                    target: int = 4) -> tuple[int, list[float]]:
    tolerance = 1e-7
    if upper <= tolerance:
        return 0, [0.0, upper]
    level = 0
    global_count = 1

    def active_count(count: int) -> int:
        width = root / count
        active = max(1, min(count, math.ceil(upper / width)))
        while active > 1 and (active - 1) * width >= upper - tolerance:
            active -= 1
        while active < count and active * width < upper - tolerance:
            active += 1
        return active

    while level < 52 and active_count(global_count * 2) <= target:
        global_count *= 2
        level += 1
    width = root / global_count
    count = active_count(global_count)
    endpoints = [0.0]
    endpoints.extend(min(upper, (index + 1) * width)
                     for index in range(count))
    return level, endpoints


def boundaries_preserved(weaker: list[float], stronger: list[float],
                         tolerance: float = 1e-7) -> bool:
    cutoff = stronger[-1]
    return all(
        boundary > cutoff + tolerance or
        any(abs(boundary - endpoint) <= tolerance for endpoint in stronger)
        for boundary in weaker[1:-1])


def stability_projection(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current = {row["instance_id"]: row for row in rows
               if row["arm"] == "C6-NESTED-DYADIC-K4"}
    historical_path = (common.ROOT / "results" /
                       "gf_small_hard_light_round39" /
                       "per_run_convergence_metrics.csv")
    historical = {}
    with historical_path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["arm"] == "C6-HGA-LIGHT-1000":
                historical[row["instance_id"]] = row
    output: list[dict[str, Any]] = []
    for instance_id, candidate in current.items():
        if instance_id not in historical:
            continue
        root = (int(candidate["V"]) - 1.0) / int(candidate["V"])
        full_ub = min(k1.number(candidate["startup_verified_ub"]), root)
        light_ub = min(k1.number(
            historical[instance_id]["startup_verified_objective"]), root)
        weaker = max(full_ub, light_ub)
        stronger = min(full_ub, light_ub)
        legacy_weak = [weaker * index / 4 for index in range(5)]
        legacy_strong = [stronger * index / 4 for index in range(5)]
        weak_level, nested_weak = nested_geometry(weaker, root)
        strong_level, nested_strong = nested_geometry(stronger, root)
        output.append({
            "instance_id": instance_id,
            "hga_full_proof_upper": full_ub,
            "hga_light_proof_upper": light_ub,
            "ub_values_differ": not math.isclose(
                full_ub, light_ub, rel_tol=0.0, abs_tol=1e-12),
            "weaker_proof_upper": weaker,
            "stronger_proof_upper": stronger,
            "legacy_weaker_endpoints": ";".join(
                format(value, ".17g") for value in legacy_weak),
            "legacy_stronger_endpoints": ";".join(
                format(value, ".17g") for value in legacy_strong),
            "legacy_relevant_boundaries_preserved": boundaries_preserved(
                legacy_weak, legacy_strong),
            "nested_weaker_level": weak_level,
            "nested_stronger_level": strong_level,
            "nested_weaker_endpoints": ";".join(
                format(value, ".17g") for value in nested_weak),
            "nested_stronger_endpoints": ";".join(
                format(value, ".17g") for value in nested_strong),
            "nested_relevant_boundaries_preserved": boundaries_preserved(
                nested_weak, nested_strong),
            "interpretation": (
                "geometry_projection_only_no_runtime_monotonicity_claim"),
        })
    return output


def round36_stability_projection() -> list[dict[str, Any]]:
    path = (common.ROOT / "results" /
            "gf_incumbent_decomposition_causal_round36" /
            "frozen_causal_panel.csv")
    output: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        root = (int(row["V"]) - 1.0) / int(row["V"])
        hga_upper = min(float(row["round35_full_startup_ub"]), root)
        simple_upper = min(float(row["round35_simple_startup_ub"]), root)
        weaker = max(hga_upper, simple_upper)
        stronger = min(hga_upper, simple_upper)
        legacy_weak = [weaker * index / 4 for index in range(5)]
        legacy_strong = [stronger * index / 4 for index in range(5)]
        weak_level, nested_weak = nested_geometry(weaker, root)
        strong_level, nested_strong = nested_geometry(stronger, root)
        output.append({
            "panel_row_id": row["panel_row_id"],
            "instance_id": row["instance_id"],
            "V": row["V"],
            "M": row["M"],
            "scenario": row["scenario"],
            "hga_verified_proof_upper": hga_upper,
            "simple_verified_proof_upper": simple_upper,
            "ub_values_differ": not math.isclose(
                hga_upper, simple_upper, rel_tol=0.0, abs_tol=1e-12),
            "weaker_proof_upper": weaker,
            "stronger_proof_upper": stronger,
            "legacy_weaker_endpoints": ";".join(
                format(value, ".17g") for value in legacy_weak),
            "legacy_stronger_endpoints": ";".join(
                format(value, ".17g") for value in legacy_strong),
            "legacy_relevant_boundaries_preserved": boundaries_preserved(
                legacy_weak, legacy_strong),
            "nested_weaker_level": weak_level,
            "nested_stronger_level": strong_level,
            "nested_weaker_endpoints": ";".join(
                format(value, ".17g") for value in nested_weak),
            "nested_stronger_endpoints": ";".join(
                format(value, ".17g") for value in nested_strong),
            "nested_relevant_boundaries_preserved": boundaries_preserved(
                nested_weak, nested_strong),
            "interpretation": (
                "geometry_projection_on_preexisting_verified_ub_pairs_"
                "no_runtime_monotonicity_claim"),
        })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    manifest = common.csv_rows(common.OUT / "ub_geometry_manifest.csv")
    rows = [row for frozen in manifest if (row := summarize(frozen))]
    if args.require_full and len(rows) != len(manifest):
        raise RuntimeError(
            f"UB-geometry panel incomplete: {len(rows)}/{len(manifest)}")
    if not rows:
        raise RuntimeError("UB-geometry panel has no completed rows")
    common.write_csv(common.OUT / "ub_geometry_per_run_trajectory.csv", rows)
    paired = comparisons(rows)
    if paired:
        common.write_csv(common.OUT / "ub_geometry_comparison.csv", paired)
    projection = stability_projection(rows)
    if projection:
        common.write_csv(
            common.OUT / "ub_geometry_stability_projection.csv", projection)
    round36_projection = round36_stability_projection()
    common.write_csv(
        common.OUT / "ub_geometry_round36_stability_projection.csv",
        round36_projection)
    if not all(k1.truth(row["exactness_passed"]) or expected_unresolved(row)
               for row in rows):
        raise RuntimeError(
            "UB-geometry row failed exactness/unresolved fail-closed gate")
    if not all(k1.truth(row["same_objective"]) and
               k1.truth(row["baseline_outcome_accepted"]) and
               k1.truth(row["candidate_outcome_accepted"])
               for row in paired):
        raise RuntimeError("UB-geometry equivalence gate failed")
    if projection and not all(k1.truth(
            row["nested_relevant_boundaries_preserved"])
            for row in projection):
        raise RuntimeError("nested-dyadic boundary-preservation gate failed")
    if not all(k1.truth(row["nested_relevant_boundaries_preserved"])
               for row in round36_projection):
        raise RuntimeError(
            "Round 36 nested-dyadic boundary-preservation gate failed")
    print({"completed_rows": len(rows), "frozen_rows": len(manifest),
           "comparisons": len(paired), "stability_rows": len(projection),
           "round36_stability_rows": len(round36_projection)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
