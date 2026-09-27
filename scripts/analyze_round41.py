#!/usr/bin/env python3
"""Build compact Round 41 evidence tables from local run artifacts."""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import analyze_round40_k1 as r40
import round41_common as common


STATIC_ARMS = ("st-k2-i", "st-k2-p-core", "st-k2-p-extended")
WITNESSES = {
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114",
}


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"true", "1", "yes"}


def number(value: Any, default: float = math.nan) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def exact_start(run_dir: Path) -> float:
    path = run_dir / "process_phases.csv"
    if not path.is_file():
        return 0.0
    matches = [number(row.get("process_seconds"), 0.0)
               for row in common.csv_rows(path)
               if row.get("event") == "exact_phase_start"]
    return matches[-1] if matches else 0.0


def result_if_present(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / "result.json"
    return common.load_json(path) if path.is_file() else None


def summarize_run(run_dir: Path, roles: dict[str, str]) -> dict[str, Any] | None:
    command_path = run_dir / "command.json"
    result = result_if_present(run_dir)
    if not command_path.is_file() or result is None:
        return None
    command = common.load_json(command_path)
    instance_id = str(command.get("instance_id", ""))
    arm = str(command.get("arm", result.get(
        "round41_static_segmented_gini", "")))
    solve = str(command.get("solve", "mip"))
    total = number(result.get("final_process_wall_time_seconds"), 0.0)
    hga = number(result.get("hga_wall_time_seconds"), 0.0)
    is_static = arm in STATIC_ARMS
    is_root_reference = arm.startswith("root-reference-")
    is_c6_reference = arm in {
        "external-k4", "external-k1", "external-k2-root-diagnostic"}
    if is_static or is_root_reference:
        lower = number(result.get("round41_static_native_bound"), 0.0)
        upper = number(result.get("upper_bound"), 0.0)
        work = number(result.get("round41_static_solver_work"), 0.0)
        nodes = number(result.get("round41_static_solver_nodes"), 0.0)
        jobs = 0 if is_root_reference else int(number(result.get(
            "round41_static_integer_proof_job_count"), 0.0))
        parameter_valid = truth(result.get(
            "round41_static_parameter_roundtrip_valid"))
        verifier = truth(result.get(
            "round41_static_original_verifier_passed"))
    elif is_c6_reference:
        lower = number(result.get(
            "external_gini_tree_global_lower_bound"), 0.0)
        upper = number(result.get(
            "external_gini_tree_verified_upper_bound"), 0.0)
        work = number(result.get("external_gini_tree_work"), 0.0)
        nodes = number(result.get("external_gini_tree_nodes"), 0.0)
        jobs = int(r40.c6_trajectory(
            run_dir, result)["independent_integer_proof_jobs"])
        parameter_valid = truth(result.get(
            "external_gini_tree_backend_parameter_roundtrip_valid"))
        verifier = truth(result.get("verification", {}).get(
            "original_solution_feasible"))
    else:
        lower = number(result.get("lower_bound"), 0.0)
        upper = number(result.get("upper_bound"), 0.0)
        work = number(result.get("gurobi_work"), 0.0)
        nodes = number(result.get("gurobi_node_count"), 0.0)
        jobs = 1
        parameter_valid = (
            int(number(result.get("gurobi_threads_effective"), -99)) == 1 and
            int(number(result.get("gurobi_seed_effective"), -99)) == 0 and
            int(number(result.get("gurobi_presolve_effective"), -99)) == -1 and
            abs(number(result.get("gurobi_mip_gap_effective"), 1.0)) < 1e-15 and
            abs(number(result.get(
                "gurobi_mip_gap_abs_effective"), 1.0)) < 1e-15)
        verifier = truth(result.get("verification", {}).get(
            "original_solution_feasible"))
    exact_seconds = max(0.0, total - exact_start(run_dir))
    gap = max(0.0, (upper - lower) / max(abs(upper), 1e-12))
    return {
        "run_id": command.get("run_id", run_dir.name),
        "instance_id": instance_id,
        "diagnostic_role": roles.get(instance_id, "engineering_sentinel"),
        "arm": arm,
        "solve": solve,
        "process_cap_seconds": command.get("process_cap_seconds", ""),
        "executable_sha256": command.get("executable_sha256", ""),
        "return_code": command.get("return_code", ""),
        "watchdog_timeout": command.get("watchdog_timeout", False),
        "status": result.get("status", ""),
        "objective": result.get("objective", ""),
        "valid_lower_bound": lower,
        "verified_upper_bound": upper,
        "relative_gap": gap,
        "strict_certificate": truth(result.get(
            "strict_certified_original_problem")),
        "original_problem_verifier_passed": verifier,
        "parameter_roundtrip_valid": parameter_valid,
        "hga_startup_seconds": hga,
        "exact_phase_seconds": exact_seconds,
        "total_process_seconds": total,
        "solver_work": work,
        "solver_nodes": nodes,
        "independent_integer_proof_jobs": jobs,
        "one_native_mip_job": truth(result.get(
            "round41_static_one_native_mip_job")) if is_static else jobs == 1,
        "model_sha256": result.get(
            "round41_static_segmented_model_sha256", ""),
        "model_variables": result.get("round41_static_model_variables", ""),
        "model_linear_constraints": result.get(
            "round41_static_model_linear_constraints", ""),
        "model_nonzeros": result.get("round41_static_model_nonzeros", ""),
        "model_general_constraints": result.get(
            "round41_static_model_general_constraints", ""),
        "accepted_outcome": (
            command.get("return_code") == 0 and
            not truth(command.get("watchdog_timeout")) and verifier and
            parameter_valid and math.isfinite(lower) and
            math.isfinite(upper) and lower <= upper + 1e-7),
        "false_certificate": truth(result.get(
            "strict_certified_original_problem")) and not verifier,
    }


def initial_lp_rows(run_dir: Path) -> list[dict[str, str]]:
    path = run_dir / "external" / "lp_status_ledger.csv"
    if not path.is_file():
        return []
    rows = common.csv_rows(path)
    return sorted(
        [row for row in rows
         if row.get("parent_id", "") == "" and
         row.get("leaf_id", "").startswith("L")],
        key=lambda row: row.get("leaf_id", ""))


def bound_from_initial(run_dir: Path, expected: int) -> float:
    rows = initial_lp_rows(run_dir)
    distinct = {row["leaf_id"]: row for row in rows}
    required = [distinct.get(f"L{index}") for index in range(expected)]
    if any(row is None or not truth(row.get("terminal_valid")) or
           not truth(row.get("bound_available")) for row in required):
        return math.nan
    return min(number(row["lower_bound"]) for row in required)


def historical_k1_bounds() -> dict[str, float]:
    path = common.ROOT / "results" / "gf_regression_adaptive_round40" / \
        "k1_per_run_trajectory.csv"
    output: dict[str, float] = {}
    if not path.is_file():
        return output
    for row in common.csv_rows(path):
        if row.get("arm") != "C6-K1-SINGLE":
            continue
        sequence = row.get("initial_lp_bounds", "")
        try:
            output[row["instance_id"]] = float(sequence.split("|")[3])
        except (IndexError, ValueError):
            if (truth(row.get("strict_certificate")) and
                    abs(number(row.get("valid_lower_bound"), math.nan)) <=
                    1e-12):
                output[row["instance_id"]] = 0.0
    return output


def write_default_equivalence() -> None:
    pre = {row["instance_id"]: row for row in common.csv_rows(
        common.OUT / "pre_default_c6_equivalence.csv")}
    post = {row["instance_id"]: row for row in common.csv_rows(
        common.OUT / "post_default_c6_equivalence.csv")}
    rows = []
    for instance_id in sorted(set(pre) & set(post)):
        a, b = pre[instance_id], post[instance_id]
        cross = (a["implicit_trajectory_sha256"] ==
                 b["implicit_trajectory_sha256"])
        rows.append({
            "instance_id": instance_id,
            "pre_pair_equivalent": a["default_equivalence_passed"],
            "post_pair_equivalent": b["default_equivalence_passed"],
            "pre_trajectory_sha256": a["implicit_trajectory_sha256"],
            "post_trajectory_sha256": b["implicit_trajectory_sha256"],
            "pre_post_trajectory_match": cross,
            "default_c6_equivalence_passed": (
                truth(a["default_equivalence_passed"]) and
                truth(b["default_equivalence_passed"]) and cross),
        })
    common.write_csv(common.OUT / "default_c6_equivalence.csv", rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-final", action="store_true")
    args = parser.parse_args()
    manifest = common.csv_rows(common.OUT / "diagnostic_panel_manifest.csv")
    roles = {row["instance_id"]: row["diagnostic_role"] for row in manifest}
    summaries = []
    for path in sorted(common.RUNS.glob("*")):
        if not path.is_dir() or not (
                path.name.startswith("static__") or
                path.name.startswith("reference__") or
                path.name.startswith("direct_root_reference__") or
                path.name.startswith("root_reference__")):
            continue
        row = summarize_run(path, roles)
        if row:
            summaries.append(row)
    if not summaries:
        raise RuntimeError("no Round 41 result rows found")
    common.write_csv(common.OUT / "per_run_results.csv", summaries)

    root_rows = [row for row in summaries
                 if row["arm"] in STATIC_ARMS and row["solve"] == "root-lp"]
    model_rows = [{
        "instance_id": row["instance_id"],
        "diagnostic_role": row["diagnostic_role"],
        "arm": row["arm"],
        "variables": row["model_variables"],
        "linear_constraints": row["model_linear_constraints"],
        "nonzeros": row["model_nonzeros"],
        "general_constraints": row["model_general_constraints"],
        "model_sha256": row["model_sha256"],
        **{key.removeprefix("round41_static_"): value
           for key, value in common.load_json(
               common.RUNS / row["run_id"] / "result.json").items()
           if key in {
               "round41_static_model_binary_variables",
               "round41_static_model_integer_variables",
               "round41_static_model_continuous_variables",
               "round41_static_selector_variables",
               "round41_static_perspective_variables",
               "round41_static_extended_variables",
               "round41_static_indicator_rows",
               "round41_static_linear_rows",
               "round41_static_model_build_seconds",
               "round41_static_model_read_seconds",
               "round41_static_presolved_rows",
               "round41_static_presolved_columns",
               "round41_static_presolved_nonzeros",
           }},
    } for row in root_rows]
    common.write_csv(common.OUT / "model_size_comparison.csv", model_rows)

    frac_rows = []
    for row in root_rows:
        value = common.load_json(common.RUNS / row["run_id"] / "result.json")
        frac_rows.append({
            "instance_id": row["instance_id"],
            "diagnostic_role": row["diagnostic_role"],
            "arm": row["arm"],
            "root_lp_bound": value["round41_static_root_lp_bound"],
            "route_phi": value["round41_static_route_binary_fractionality"],
            "visit_phi": value["round41_static_visit_binary_fractionality"],
            "inventory_bit_phi": value[
                "round41_static_inventory_bit_fractionality"],
            "selector_phi": value[
                "round41_static_selector_binary_fractionality"],
            "original_mccormick_ambiguity": value[
                "round41_static_mccormick_ambiguity"],
            "segmented_mccormick_ambiguity": value[
                "round41_static_segmented_mccormick_ambiguity"],
        })
    common.write_csv(
        common.OUT / "fractionality_and_mccormick_ambiguity.csv", frac_rows)

    historical = historical_k1_bounds()
    grouped_root: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in root_rows:
        grouped_root[row["instance_id"]][row["arm"]] = row
    comparison_rows = []
    capture_rows = []
    for instance_id, arms in sorted(grouped_root.items()):
        direct_k1 = result_if_present(
            common.RUNS / f"direct_root_reference__{instance_id}__k1")
        k1 = number(direct_k1.get("round41_static_root_lp_bound")) \
            if direct_k1 else math.nan
        k1_source = "round41_direct_fixed_interval_k1"
        if not math.isfinite(k1):
            k1_dir = common.RUNS / f"reference__{instance_id}__external-k1"
            k1 = bound_from_initial(k1_dir, 1)
            k1_source = "round41_contemporary_external_k1"
        if not math.isfinite(k1):
            k1 = historical.get(instance_id, math.nan)
            k1_source = "round40_same_contract_preserved_by_default_equivalence"
        direct_left = result_if_present(
            common.RUNS / f"direct_root_reference__{instance_id}__left")
        direct_right = result_if_present(
            common.RUNS / f"direct_root_reference__{instance_id}__right")
        left = number(direct_left.get("round41_static_root_lp_bound")) \
            if direct_left else math.nan
        right = number(direct_right.get("round41_static_root_lp_bound")) \
            if direct_right else math.nan
        k2 = min(left, right) if all(
            math.isfinite(value) for value in (left, right)) else math.nan
        if not math.isfinite(k2):
            k2_dir = common.RUNS / f"root_reference__{instance_id}__external-k2"
            k2 = bound_from_initial(k2_dir, 2)
            left_right = initial_lp_rows(k2_dir)
            left = number(left_right[0].get("lower_bound")) \
                if len(left_right) >= 1 else left
            right = number(left_right[1].get("lower_bound")) \
                if len(left_right) >= 2 else right
        row = {
            "instance_id": instance_id,
            "diagnostic_role": roles.get(instance_id, ""),
            "k1_root_lp_bound": k1,
            "k1_provenance": k1_source,
            "external_left_interval_lp_bound": left,
            "external_right_interval_lp_bound": right,
            "external_k2_disjunctive_bound": k2,
        }
        for arm in STATIC_ARMS:
            row[f"{arm.replace('-', '_')}_root_lp_bound"] = (
                arms.get(arm, {}).get("valid_lower_bound", math.nan))
        comparison_rows.append(row)
        for arm in STATIC_ARMS:
            candidate = number(arms.get(arm, {}).get(
                "valid_lower_bound"), math.nan)
            denominator = k2 - k1
            capture_rows.append({
                "instance_id": instance_id,
                "diagnostic_role": roles.get(instance_id, ""),
                "arm": arm,
                "k1_root_lp_bound": k1,
                "external_k2_disjunctive_bound": k2,
                "candidate_root_lp_bound": candidate,
                "positive_denominator": math.isfinite(denominator) and
                    denominator > 1e-12,
                "strength_capture": ((candidate - k1) / denominator)
                    if math.isfinite(candidate) and
                       math.isfinite(denominator) and denominator > 1e-12
                    else "",
            })
    common.write_csv(
        common.OUT / "root_relaxation_comparison.csv", comparison_rows)
    common.write_csv(
        common.OUT / "perspective_strength_capture.csv", capture_rows)

    exact_rows = [row for row in summaries
                  if row["solve"] == "mip" and row["arm"] in STATIC_ARMS]
    # A capped run may have a valid incumbent that is not the optimum.  It must
    # not make the certified arms on that instance look mutually inconsistent.
    # Compare objectives only across strict certificates; for noncertificates
    # the cross-arm optimum comparison is intentionally not applicable.
    objective_groups: dict[str, list[float]] = defaultdict(list)
    for row in exact_rows:
        value = number(row["objective"])
        if row["strict_certificate"] and math.isfinite(value):
            objective_groups[row["instance_id"]].append(value)
    exactness = [{
        "run_id": row["run_id"],
        "instance_id": row["instance_id"],
        "arm": row["arm"],
        "objective": row["objective"],
        "native_bound": row["valid_lower_bound"],
        "native_objective_residual": abs(
            number(row["objective"], 0.0) -
            number(row["valid_lower_bound"], 0.0)),
        "cross_static_objective_match": (all(math.isclose(
            number(row["objective"]), value, rel_tol=0.0, abs_tol=1e-7)
            for value in objective_groups[row["instance_id"]])
            if row["strict_certificate"] else ""),
        "return_code_zero": row["return_code"] == 0,
        "coverage_valid": common.load_json(
            common.RUNS / row["run_id"] / "result.json").get(
                "round41_static_segmented_coverage_valid"),
        "one_native_mip_job": row["one_native_mip_job"],
        "parameter_roundtrip_valid": row["parameter_roundtrip_valid"],
        "original_problem_verifier_passed": row[
            "original_problem_verifier_passed"],
        "strict_certificate": row["strict_certificate"],
        "false_certificate": row["false_certificate"],
        "accepted_outcome": row["accepted_outcome"],
    } for row in exact_rows]
    common.write_csv(common.OUT / "exactness_audit.csv", exactness)

    representative = [row for row in summaries
                      if row["instance_id"] in WITNESSES and
                      (row["solve"] in {"mip", "root-lp"} or
                       row["arm"] == "external-k2-root-diagnostic")]
    common.write_csv(
        common.OUT / "representative_trajectory_analysis.csv",
        representative)
    write_default_equivalence()

    if args.require_final:
        expected_static = len(manifest) * len(STATIC_ARMS) * 2
        if len(root_rows) + len(exact_rows) != expected_static:
            raise RuntimeError(
                f"incomplete static panel: {len(root_rows) + len(exact_rows)}"
                f"/{expected_static}")
        if any(row["false_certificate"] for row in exactness):
            raise RuntimeError("false Round 41 certificate")
    print({"per_run": len(summaries), "root": len(root_rows),
           "exact": len(exact_rows)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
