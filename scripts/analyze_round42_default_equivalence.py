#!/usr/bin/env python3
"""Fail-closed Round 42 default C6 equivalence and Round 41 cross-check."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any

import analyze_round40_k1 as k1
import round42_common as common


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
    summary = {
        **row,
        "return_code": command["return_code"],
        "objective": result["objective"],
        "valid_lower_bound": float(result[
            "external_gini_tree_global_lower_bound"]),
        "verified_upper_bound": float(result[
            "external_gini_tree_verified_upper_bound"]),
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
        "reported_round42_static": result["round42_static_architecture"],
        "reported_round42_siblings": result[
            "round42_terminal_sibling_coalescing"],
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
    manifest = common.csv_rows(
        common.OUT / "default_c6_equivalence_manifest.csv")
    rows = [summarize(row) for row in manifest]
    common.write_csv(common.OUT / "default_c6_equivalence_per_run.csv", rows)
    grouped: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        grouped[row["instance_id"]][row["arm"]] = row
    round41_path = common.ROOT / "results" / \
        "gf_decomposition_single_tree_round41" / "default_c6_equivalence.csv"
    round41 = {row["instance_id"]: row
               for row in common.csv_rows(round41_path)}
    comparisons: list[dict[str, Any]] = []
    for instance_id, arms in grouped.items():
        implicit = arms["C6-IMPLICIT-DEFAULT"]
        explicit = arms["C6-EXPLICIT-ROUND42-OFF"]
        mismatches = [field for field in DETERMINISTIC_FIELDS
                      if str(implicit[field]) != str(explicit[field])]
        common_gate = all(
            k1.truth(item["strict_certificate"]) and
            k1.truth(item["original_problem_verifier_passed"]) and
            k1.truth(item["parameter_roundtrip_valid"]) and
            int(item["gurobi_presolve_effective"]) == -1 and
            item["reported_coarse_start"] == "off" and
            item["reported_ub_geometry"] == "off" and
            item["reported_round42_static"] == "off" and
            item["reported_round42_siblings"] == "off"
            for item in (implicit, explicit))
        prior = round41[instance_id]
        cross = implicit["deterministic_trajectory_sha256"] == \
            prior["post_trajectory_sha256"]
        comparisons.append({
            "instance_id": instance_id,
            "round41_head": "75fe23e591a39b54f7940eb0012a245e3a92d955",
            "deterministic_field_count": len(DETERMINISTIC_FIELDS),
            "mismatch_count": len(mismatches),
            "mismatched_fields": ";".join(mismatches),
            "round41_pre_trajectory_sha256": prior[
                "post_trajectory_sha256"],
            "round42_implicit_trajectory_sha256": implicit[
                "deterministic_trajectory_sha256"],
            "round42_explicit_trajectory_sha256": explicit[
                "deterministic_trajectory_sha256"],
            "implicit_explicit_hash_match": implicit[
                "deterministic_trajectory_sha256"] == explicit[
                    "deterministic_trajectory_sha256"],
            "round41_round42_hash_match": cross,
            "common_exactness_gate": common_gate,
            "default_c6_equivalence_passed": (
                common_gate and not mismatches and cross),
        })
    common.write_csv(common.OUT / "default_c6_equivalence.csv", comparisons)
    if not all(k1.truth(row["default_c6_equivalence_passed"])
               for row in comparisons):
        raise RuntimeError("Round 42 default C6 equivalence gate failed")
    print({"pairs": len(comparisons), "all_equivalent": True})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
