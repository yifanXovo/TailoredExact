#!/usr/bin/env python3
"""Extract K=4/K=1 proof trajectories and comparisons for Round 40."""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import round40_common as common


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() == "true"


def number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def integer(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def expected_unresolved_endpoint(row: dict[str, Any]) -> bool:
    """Accept only the predeclared, fail-closed numerical endpoint outcome."""
    lower = number(row.get("valid_lower_bound"), math.nan)
    upper = number(row.get("verified_upper_bound"), math.nan)
    return (
        row.get("diagnostic_role") ==
        "round39_unresolved_endpoint_witness" and
        str(row.get("arm", "")).startswith("C6-") and
        row.get("return_code") == 0 and
        not truth(row.get("watchdog_timeout")) and
        not truth(row.get("strict_certificate")) and
        row.get("certificate_class") == "certificate_rejected" and
        row.get("status") == "round31_c6_external_gini_tree_not_certified" and
        truth(row.get("original_problem_verifier_passed")) and
        truth(row.get("backend_parameter_roundtrip_valid")) and
        integer(row.get("gurobi_presolve_effective"), -99) == -1 and
        math.isfinite(lower) and math.isfinite(upper) and
        lower <= upper and upper - lower > 1e-7)


def rows_if_present(path: Path) -> list[dict[str, str]]:
    return common.csv_rows(path) if path.is_file() else []


def exact_start(run_dir: Path) -> float:
    rows = rows_if_present(run_dir / "process_phases.csv")
    matches = [number(row.get("process_seconds")) for row in rows
               if row.get("event") == "exact_phase_start"]
    return matches[-1] if matches else 0.0


def compact_sequence(rows: list[dict[str, str]], fields: tuple[str, ...]) -> str:
    return ";".join("|".join(row.get(field, "") for field in fields)
                    for row in rows)


def c6_trajectory(run_dir: Path, result: dict[str, Any]) -> dict[str, Any]:
    external = run_dir / "external"
    lp = rows_if_present(external / "lp_status_ledger.csv")
    optimize = rows_if_present(external / "paper_optimize_ledger.csv")
    targets = rows_if_present(external / "native_target_ledger.csv")
    splits = rows_if_present(external / "split_decision_ledger.csv")
    initial = rows_if_present(external / "initial_decomposition_ledger.csv")
    events = rows_if_present(external / "paper_tree_events.csv")
    initial_count = integer(result.get("external_gini_tree_initial_leaf_count"))
    initial_ids = {f"L{index}" for index in range(initial_count)}
    initial_lp = [row for row in lp if row.get("leaf_id") in initial_ids]
    terminal = [row for row in optimize
                if row.get("solve_kind") in {"MIP", "TERMINAL_MIP"}]
    partial = [row for row in optimize if "TARGET" in row.get("solve_kind", "")]
    widths = [number(row.get("active_upper")) -
              number(row.get("active_lower"))
              for row in initial if truth(row.get("active"))]
    all_lp_widths = [number(row.get("gamma_U")) -
                     number(row.get("gamma_L")) for row in lp]
    return {
        "initial_interval_count": initial_count,
        "initial_interval_widths": "|".join(f"{value:.17g}" for value in widths),
        "initial_lp_bounds": compact_sequence(
            initial_lp,
            ("leaf_id", "gamma_L", "gamma_U", "lower_bound",
             "native_status", "work")),
        "all_lp_widths": "|".join(
            f"{value:.17g}" for value in all_lp_widths),
        "initial_model_sha256": compact_sequence(
            [row for row in optimize
             if row.get("leaf_id") in initial_ids and
             row.get("solve_kind") == "LP"],
            ("leaf_id", "model_sha256")),
        "native_target_sequence": compact_sequence(
            targets, ("phase_index", "leaf_id", "target_kind",
                      "current_bound", "target_bound", "status",
                      "work", "nodes")),
        "split_lookahead_sequence": compact_sequence(
            splits, ("parent_id", "split", "reason", "b_plus",
                     "eta_proof", "parent_native_bound_target")),
        "terminal_mip_sequence": compact_sequence(
            terminal, ("leaf_id", "native_status", "solver_runtime",
                       "work", "nodes", "model_sha256")),
        "closure_sequence": compact_sequence(
            [row for row in events if any(token in row.get("event", "")
             for token in ("closure", "prune", "infeasible"))],
            ("event", "leaf_id", "gamma_L", "gamma_U", "detail")),
        "lp_optimize_count": integer(result.get(
            "external_gini_tree_lp_optimize_count")),
        "partial_mip_optimize_count": len(partial),
        "terminal_mip_optimize_count": len(terminal),
        "independent_integer_proof_jobs": len(partial) + len(terminal),
        "lp_work": number(result.get("external_gini_tree_lp_work")),
        "partial_mip_work": number(result.get(
            "external_gini_tree_partial_mip_work")),
        "terminal_mip_work": number(result.get(
            "external_gini_tree_terminal_mip_work")),
        "split_count": integer(result.get("external_gini_tree_split_count")),
        "requeue_count": integer(result.get(
            "external_gini_tree_native_requeue_count")),
        "final_leaf_count": integer(result.get(
            "external_gini_tree_final_leaf_count")),
    }


def summarize(frozen: dict[str, str]) -> dict[str, Any] | None:
    run_dir = common.RUNS / frozen["run_id"]
    result_path = run_dir / "result.json"
    if not result_path.is_file():
        return None
    command = common.load_json(run_dir / "command.json")
    result = common.load_json(result_path)
    c6 = frozen["arm"].startswith("C6-")
    lower, upper = common.result_bounds(frozen["arm"], result)
    total = number(result.get(
        "final_process_wall_time_seconds", result.get("runtime_seconds")))
    row: dict[str, Any] = {
        **frozen,
        "return_code": command.get("return_code"),
        "watchdog_timeout": command.get("watchdog_timeout"),
        "total_process_seconds": total,
        "hga_startup_seconds": number(result.get("hga_wall_time_seconds"))
            if c6 else 0.0,
        "exact_phase_seconds": max(0.0, total - exact_start(run_dir))
            if c6 else total,
        "objective": result.get("objective"),
        "valid_lower_bound": lower,
        "verified_upper_bound": upper,
        "relative_gap": max(0.0, (upper - lower) /
                            max(abs(upper), 1e-12)),
        "solver_work": number(result.get(
            "external_gini_tree_work" if c6 else "gurobi_work")),
        "solver_nodes": number(result.get(
            "external_gini_tree_nodes" if c6 else "gurobi_node_count")),
        "strict_certificate": truth(result.get(
            "strict_certified_original_problem")),
        "certificate_class": result.get(
            "external_gini_tree_certificate_class" if c6 else
            "strict_certificate_class"),
        "original_problem_verifier_passed": truth(
            result.get("verification", {}).get("original_solution_feasible")),
        "gurobi_presolve_effective": result.get("gurobi_presolve_effective"),
        "status": result.get("status"),
    }
    row["backend_parameter_roundtrip_valid"] = (
        truth(result.get(
            "external_gini_tree_backend_parameter_roundtrip_valid"))
        if c6 else (
            integer(result.get("gurobi_threads_effective"), -99) == 1 and
            integer(result.get("gurobi_presolve_effective"), -99) == -1 and
            integer(result.get("gurobi_seed_effective"), -99) == 0 and
            abs(number(result.get("gurobi_mip_gap_effective"))) <= 1e-15 and
            abs(number(result.get("gurobi_mip_gap_abs_effective"))) <= 1e-15))
    if c6:
        row.update(c6_trajectory(run_dir, result))
        row["reported_coarse_start_policy"] = result.get(
            "round40_c6_coarse_start")
    else:
        row.update({
            "initial_interval_count": 0,
            "initial_interval_widths": "",
            "initial_lp_bounds": "",
            "all_lp_widths": "",
            "initial_model_sha256": "",
            "native_target_sequence": "",
            "split_lookahead_sequence": "",
            "terminal_mip_sequence": "",
            "closure_sequence": "",
            "lp_optimize_count": 0,
            "partial_mip_optimize_count": 0,
            "terminal_mip_optimize_count": 1,
            "independent_integer_proof_jobs": 1,
            "lp_work": 0.0,
            "partial_mip_work": 0.0,
            "terminal_mip_work": row["solver_work"],
            "split_count": 0,
            "requeue_count": 0,
            "final_leaf_count": 0,
            "reported_coarse_start_policy": "not_applicable",
        })
    row["exactness_passed"] = (
        row["return_code"] == 0 and not truth(row["watchdog_timeout"]) and
        row["strict_certificate"] and row["original_problem_verifier_passed"]
        and row["backend_parameter_roundtrip_valid"]
        and integer(row["gurobi_presolve_effective"], -99) == -1 and
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
        if not baseline:
            continue
        for candidate_name in (
                "C6-K1-SINGLE", "C6-K1-ADAPTIVE",
                "C6-K1-ADAPTIVE-DECISIVE"):
            candidate = arms.get(candidate_name)
            if not candidate:
                continue
            k4_work = baseline["solver_work"]
            candidate_work = candidate["solver_work"]
            work_ratio = (1.0 if abs(k4_work) <= 1e-12 and
                          abs(candidate_work) <= 1e-12 else
                          candidate_work / max(k4_work, 1e-12))
            output.append({
                "instance_id": instance_id,
                "diagnostic_role": candidate["diagnostic_role"],
                "candidate": candidate_name,
                "k4_seconds": baseline["total_process_seconds"],
                "candidate_seconds": candidate["total_process_seconds"],
                "candidate_over_k4_time_ratio":
                    candidate["total_process_seconds"] /
                    baseline["total_process_seconds"],
                "k4_work": k4_work,
                "candidate_work": candidate_work,
                "candidate_over_k4_work_ratio": work_ratio,
                "k4_integer_jobs": baseline["independent_integer_proof_jobs"],
                "candidate_integer_jobs":
                    candidate["independent_integer_proof_jobs"],
                "k4_terminal_work": baseline["terminal_mip_work"],
                "candidate_terminal_work": candidate["terminal_mip_work"],
                "k4_split_count": baseline["split_count"],
                "candidate_split_count": candidate["split_count"],
                "same_objective": math.isclose(
                    number(candidate["objective"]), number(baseline["objective"]),
                    rel_tol=0.0, abs_tol=1e-7),
                "both_exact": (truth(candidate["exactness_passed"]) and
                               truth(baseline["exactness_passed"])),
                "expected_unresolved": (
                    expected_unresolved_endpoint(baseline) and
                    expected_unresolved_endpoint(candidate)),
            })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    manifest = common.csv_rows(common.OUT / "k1_diagnostic_manifest.csv")
    iterative_manifest = common.OUT / "k1_iterative_manifest.csv"
    if iterative_manifest.is_file():
        manifest += common.csv_rows(iterative_manifest)
    rows = [row for frozen in manifest if (row := summarize(frozen))]
    if args.require_full and len(rows) != len(manifest):
        raise RuntimeError(
            f"K=1 panel incomplete: {len(rows)}/{len(manifest)} rows")
    common.write_csv(common.OUT / "k1_per_run_trajectory.csv", rows)
    paired = comparisons(rows)
    common.write_csv(common.OUT / "k1_vs_k4_comparison.csv", paired)
    if not all(truth(row["exactness_passed"]) or
               expected_unresolved_endpoint(row) for row in rows):
        raise RuntimeError(
            "completed K=1 row failed exactness/unresolved fail-closed gate")
    if not all(truth(row["same_objective"]) and
               (truth(row["both_exact"]) or
                truth(row["expected_unresolved"])) for row in paired):
        raise RuntimeError("K=1/K=4 equivalence gate failed")
    print({"completed_rows": len(rows), "frozen_rows": len(manifest),
           "comparisons": len(paired)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
