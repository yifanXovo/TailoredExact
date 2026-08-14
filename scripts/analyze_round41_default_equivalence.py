#!/usr/bin/env python3
"""Fail-closed audit for Round 41 pre/post default-off pairs."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from typing import Any

import analyze_round40_k1 as k1
import round41_common as common


DETERMINISTIC_FIELDS = (
    "objective", "valid_lower_bound", "verified_upper_bound",
    "solver_work", "solver_nodes", "algorithm_arm",
    "reported_coarse_start", "reported_ub_geometry",
    "active_initial_intervals", "initial_interval_count",
    "initial_interval_widths", "initial_lp_bounds",
    "initial_model_sha256", "native_target_sequence",
    "split_lookahead_sequence", "lp_optimize_count",
    "partial_mip_optimize_count", "terminal_mip_optimize_count",
    "independent_integer_proof_jobs", "lp_work", "partial_mip_work",
    "terminal_mip_work", "split_count", "requeue_count",
    "final_leaf_count",
)


def summarize(row: dict[str, str]) -> dict[str, Any]:
    run_dir = common.RUNS / row["run_id"]
    command = common.load_json(run_dir / "command.json")
    result = common.load_json(run_dir / "result.json")
    trajectory = k1.c6_trajectory(run_dir, result)
    lower = float(result["external_gini_tree_global_lower_bound"])
    upper = float(result["external_gini_tree_verified_upper_bound"])
    summary = {
        **row,
        "return_code": command["return_code"],
        "objective": result["objective"],
        "valid_lower_bound": lower,
        "verified_upper_bound": upper,
        "strict_certificate": result["strict_certified_original_problem"],
        "original_problem_verifier_passed": result["verification"][
            "original_solution_feasible"],
        "parameter_roundtrip_valid": result[
            "external_gini_tree_backend_parameter_roundtrip_valid"],
        "gurobi_presolve_effective": result["gurobi_presolve_effective"],
        "solver_work": result["external_gini_tree_work"],
        "solver_nodes": result["external_gini_tree_nodes"],
        "algorithm_arm": result["external_gini_tree_algorithm_arm"],
        "reported_coarse_start": result["round40_c6_coarse_start"],
        "reported_ub_geometry": result["round40_c6_ub_geometry"],
        "active_initial_intervals": result[
            "external_gini_tree_active_initial_intervals"],
        **trajectory,
    }
    canonical = json.dumps(
        {field: summary[field] for field in DETERMINISTIC_FIELDS},
        sort_keys=True, separators=(",", ":"))
    summary["deterministic_trajectory_sha256"] = hashlib.sha256(
        canonical.encode("utf-8")).hexdigest()
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("pre", "post"), required=True)
    args = parser.parse_args()
    manifest = common.csv_rows(
        common.OUT / f"{args.phase}_default_c6_equivalence_manifest.csv")
    rows = [summarize(row) for row in manifest]
    common.write_csv(
        common.OUT / f"{args.phase}_default_c6_equivalence_per_run.csv",
        rows)
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[row["instance_id"]][row["arm"]] = row
    comparisons: list[dict[str, Any]] = []
    for instance_id, arms in grouped.items():
        implicit = arms["C6-IMPLICIT-DEFAULT"]
        explicit = arms["C6-EXPLICIT-OFF"]
        mismatches = [field for field in DETERMINISTIC_FIELDS
                      if str(implicit[field]) != str(explicit[field])]
        common_gate = all(
            k1.truth(item["strict_certificate"]) and
            k1.truth(item["original_problem_verifier_passed"]) and
            k1.truth(item["parameter_roundtrip_valid"]) and
            int(item["gurobi_presolve_effective"]) == -1 and
            item["reported_coarse_start"] == "off" and
            item["reported_ub_geometry"] == "off"
            for item in (implicit, explicit))
        comparisons.append({
            "phase": args.phase,
            "instance_id": instance_id,
            "deterministic_field_count": len(DETERMINISTIC_FIELDS),
            "mismatch_count": len(mismatches),
            "mismatched_fields": ";".join(mismatches),
            "implicit_trajectory_sha256": implicit[
                "deterministic_trajectory_sha256"],
            "explicit_trajectory_sha256": explicit[
                "deterministic_trajectory_sha256"],
            "trajectory_hash_match": implicit[
                "deterministic_trajectory_sha256"] == explicit[
                    "deterministic_trajectory_sha256"],
            "common_exactness_gate": common_gate,
            "default_equivalence_passed": common_gate and not mismatches,
        })
    common.write_csv(
        common.OUT / f"{args.phase}_default_c6_equivalence.csv",
        comparisons)
    if not all(k1.truth(row["default_equivalence_passed"])
               for row in comparisons):
        raise RuntimeError("default C6 equivalence gate failed")
    print({"phase": args.phase, "rows": len(rows),
           "pairs": len(comparisons), "all_equivalent": True})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
