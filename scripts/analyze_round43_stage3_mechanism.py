#!/usr/bin/env python3
"""Analyze and freeze the Round 43 K1/K4 mechanism screen."""

from __future__ import annotations

import math
from statistics import mean
from typing import Any

import round43_common as common


CONFIGS = ((1, 0.05), (1, 0.10), (4, 0.05), (4, 0.10))
MAJOR = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
CONTROL = "round39_small_hard_V12_M3_Q30_slot08_seed1288546114"


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "yes"}


def gmean(values: list[float]) -> float:
    if not values or any(not math.isfinite(value) or value < 0.0
                         for value in values):
        return math.inf
    return math.exp(sum(math.log(max(value, 1e-12)) for value in values) /
                    len(values))


def exact_start(run_dir) -> float:
    phases = common.csv_rows(run_dir / "process_phases.csv")
    starts = [float(row["process_seconds"]) for row in phases
              if row["event"] == "exact_phase_start"]
    return starts[0] if starts else 0.0


def load_row(instance_id: str, K0: int, rho: float) -> dict[str, Any]:
    standard_run_id = (
        f"stage3-candidate__{instance_id}__algorithm__K{K0}__d2__"
        f"rho{rho:g}__d__single")
    extension_run_id = (
        f"x43e__{instance_id}__algorithm__K{K0}__d2__"
        f"rho{rho:g}__d__single")
    use_extension = (common.RUNS / extension_run_id / "result.json").is_file()
    run_id = extension_run_id if use_extension else standard_run_id
    run_dir = common.RUNS / run_id
    result = common.load_json(run_dir / "result.json")
    command = common.load_json(run_dir / "command.json")
    decisions = common.csv_rows(
        run_dir / "external" / "round43_structural_atlas.csv")
    facets = common.csv_rows(
        run_dir / "external" / "round43_facet_ledger.csv")
    lower = float(result["external_gini_tree_global_lower_bound"])
    upper = float(result["external_gini_tree_verified_upper_bound"])
    certified = truth(result.get("strict_certified_original_problem"))
    failure = str(result.get("external_gini_tree_failure_reason", "none"))
    hard_failure = failure not in {"none", "overall_global_deadline"}
    process = float(result.get(
        "final_process_wall_time_seconds", result.get("runtime_seconds", 0)))
    reconstruction_valid = True
    hashes = []
    for decision in decisions:
        score = float(decision["score"])
        deficit = float(decision["D_d"])
        split = truth(decision["split"])
        expected_split = score >= rho
        valid = (abs(score - deficit) <= 1e-12 and split == expected_split and
                 int(decision["K0"]) == K0 and int(decision["d"]) == 2 and
                 abs(float(decision["rho"]) - rho) <= 1e-15 and
                 decision["score_mode"] == "d")
        reconstruction_valid = reconstruction_valid and valid
        hashes.append(common.stable_hash({
            key: decision[key] for key in (
                "parent_id", "parent_depth", "K0", "d", "rho",
                "score_mode", "parent_lower", "parent_upper",
                "parent_lp_bound", "lookahead_cells", "lookahead_bounds",
                "lookahead_infeasible", "Vlocal", "Venvelope",
                "Vresidual", "D_d", "score", "split", "reason")
        }))
    return {
        "instance_id": instance_id,
        "mechanism_role": common.MECHANISM_ROLES[instance_id],
        "K0": K0,
        "rho": rho,
        "configuration": f"A({K0},2,{rho:g})",
        "run_id": run_id,
        "standard_run_id": standard_run_id,
        "symmetric_extension_used": use_extension,
        "process_cap_seconds": command["process_cap_seconds"],
        "executable_sha256": command["executable_sha256"],
        "status": result.get("status", ""),
        "certified": certified,
        "right_censored": not certified and not hard_failure,
        "hard_failure": hard_failure,
        "failure_reason": failure,
        "verified_incumbent": truth(result.get("verification", {}).get(
            "original_solution_feasible")) and truth(
                result.get("verifier_passed")),
        "lifecycle_complete": truth(result.get(
            "external_gini_tree_lifecycle_complete")),
        "coverage_valid": truth(result.get(
            "external_gini_tree_root_coverage_valid")) and truth(result.get(
            "external_gini_tree_parent_child_coverage_valid")),
        "global_bound_monotone": truth(result.get(
            "external_gini_tree_global_bound_monotone")),
        "relative_gap": 0.0 if certified else (
            max(0.0, upper - lower) / max(abs(upper), 1e-12)),
        "verified_upper": upper,
        "valid_lower": lower,
        "total_work": float(result.get("external_gini_tree_work", math.nan)),
        "lp_work": float(result.get("external_gini_tree_lp_work", math.nan)),
        "terminal_mip_work": float(result.get(
            "external_gini_tree_terminal_mip_work", math.nan)),
        "process_seconds": process,
        "exact_phase_seconds": max(0.0, process - exact_start(run_dir)),
        "nodes": float(result.get("external_gini_tree_nodes", 0.0)),
        "lp_jobs": int(result.get("external_gini_tree_lp_optimize_count", 0)),
        "terminal_mip_jobs": int(result.get(
            "external_gini_tree_terminal_mip_optimize_count", 0)),
        "split_count": int(result.get("external_gini_tree_split_count", 0)),
        "final_intervals": int(result.get(
            "external_gini_tree_final_leaf_count", 0)),
        "accepted_facets": sum(truth(row["accepted"]) for row in facets),
        "decision_count": len(decisions),
        "decision_reconstruction_valid": reconstruction_valid,
        "decision_sequence_sha256": common.stable_hash(hashes),
        "run_dir": common.relative(run_dir),
    }


def main() -> int:
    rows = [load_row(instance_id, K0, rho)
            for K0, rho in CONFIGS
            for instance_id in common.MECHANISM_ROLES]
    common.write_csv(common.OUT / "stage3_mechanism_results.csv", rows)
    summaries = []
    for K0, rho in CONFIGS:
        group = [row for row in rows
                 if row["K0"] == K0 and row["rho"] == rho]
        major = next(row for row in group if row["instance_id"] == MAJOR)
        control = next(row for row in group if row["instance_id"] == CONTROL)
        summaries.append({
            "K0": K0,
            "rho": rho,
            "configuration": f"A({K0},2,{rho:g})",
            "row_count": len(group),
            "certified_count": sum(row["certified"] for row in group),
            "right_censored_count": sum(
                row["right_censored"] for row in group),
            "hard_failure_count": sum(row["hard_failure"] for row in group),
            "all_correctness_gates_valid": all(
                not row["hard_failure"] and row["verified_incumbent"] and
                row["lifecycle_complete"] and row["coverage_valid"] and
                row["global_bound_monotone"] and
                row["decision_reconstruction_valid"] for row in group),
            "mean_final_gap": mean(row["relative_gap"] for row in group),
            "major_certified": major["certified"],
            "major_gap": major["relative_gap"],
            "major_work": major["total_work"],
            "major_process_seconds": major["process_seconds"],
            "control_certified": control["certified"],
            "control_gap": control["relative_gap"],
            "control_work": control["total_work"],
            "control_process_seconds": control["process_seconds"],
            "worst_mechanism_work": max(row["total_work"] for row in group),
            "geomean_work": gmean([row["total_work"] for row in group]),
            "geomean_process_seconds": gmean(
                [row["process_seconds"] for row in group]),
            "total_splits": sum(row["split_count"] for row in group),
            "total_facets": sum(row["accepted_facets"] for row in group),
        })
    common.write_csv(common.OUT / "stage3_mechanism_summary.csv", summaries)
    selections = {}
    for K0 in (1, 4):
        eligible = [row for row in summaries if row["K0"] == K0]
        eligible.sort(key=lambda row: (
            not row["all_correctness_gates_valid"],
            -row["certified_count"], row["mean_final_gap"],
            not row["major_certified"], row["major_gap"], row["major_work"],
            not row["control_certified"], row["control_gap"],
            row["control_work"], row["worst_mechanism_work"],
            row["geomean_work"], row["geomean_process_seconds"], row["rho"]))
        selections[str(K0)] = eligible[0]
    executable_hashes = {row["executable_sha256"] for row in rows}
    common.write_json(common.OUT / "stage3_candidate_selection.json", {
        "schema": "round43-stage3-candidate-selection-v1",
        "round_id": 43,
        "selected_K1": {
            "K0": 1, "d": 2, "rho": selections["1"]["rho"],
            "score": "d", "envelope": "single"},
        "selected_K4": {
            "K0": 4, "d": 2, "rho": selections["4"]["rho"],
            "score": "d", "envelope": "single"},
        "selection_order": [
            "correctness", "certificate count and final gap",
            "major severe-regression witness", "strongest K4 control",
            "worst mechanism Work", "aggregate Work", "aggregate time"],
        "all_rows_same_frozen_executable": len(executable_hashes) == 1,
        "executable_sha256": next(iter(executable_hashes)),
        "mechanism_row_count": len(rows),
        "validation_opened": False,
        "holdout_opened": False,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
