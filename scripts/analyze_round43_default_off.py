#!/usr/bin/env python3
"""Compare implicit C6 defaults with explicit Round 43-off sentinels."""

from __future__ import annotations

import hashlib
import json

import round43_analysis as analysis
import round43_common as common


FIELDS = (
    "objective", "lower", "upper", "work", "nodes", "algorithm_arm",
    "active_initial_intervals", "initial_leaf_count", "lp_count",
    "terminal_count", "split_count", "final_leaf_count", "model_hashes",
)


def deterministic(run_dir) -> dict:
    result = common.load_json(run_dir / "result.json")
    ledger = common.csv_rows(run_dir / "external" / "paper_optimize_ledger.csv")
    values = {
        "objective": result["objective"],
        "lower": result["external_gini_tree_global_lower_bound"],
        "upper": result["external_gini_tree_verified_upper_bound"],
        "work": result["external_gini_tree_work"],
        "nodes": result["external_gini_tree_nodes"],
        "algorithm_arm": result["external_gini_tree_algorithm_arm"],
        "active_initial_intervals": result[
            "external_gini_tree_active_initial_intervals"],
        "initial_leaf_count": result["external_gini_tree_initial_leaf_count"],
        "lp_count": result["external_gini_tree_lp_optimize_count"],
        "terminal_count": result[
            "external_gini_tree_terminal_mip_optimize_count"],
        "split_count": result["external_gini_tree_split_count"],
        "final_leaf_count": result["external_gini_tree_final_leaf_count"],
        "model_hashes": ";".join(row["model_sha256"] for row in ledger),
    }
    material = json.dumps(values, sort_keys=True, separators=(",", ":"))
    values["deterministic_sha256"] = hashlib.sha256(
        material.encode("utf-8")).hexdigest()
    values["certified"] = analysis.truth(
        result["strict_certified_original_problem"])
    values["verified"] = analysis.truth(
        result["verification"]["original_solution_feasible"])
    values["parameters"] = analysis.truth(
        result["external_gini_tree_backend_parameter_roundtrip_valid"])
    return values


def main() -> int:
    rows = []
    for instance_id in common.CONTEMPORARY_REFERENCE_IDS:
        implicit_dir = common.RUNS / f"reference__{instance_id}__c6-implicit"
        explicit_dir = common.RUNS / f"reference__{instance_id}__c6"
        implicit = deterministic(implicit_dir)
        explicit = deterministic(explicit_dir)
        implicit_command = common.load_json(implicit_dir / "command.json")[
            "command"]
        explicit_command = common.load_json(explicit_dir / "command.json")[
            "command"]
        mismatches = [field for field in FIELDS
                      if implicit[field] != explicit[field]]
        flags_absent = "--round43-envelope-refinement" not in implicit_command
        explicit_off = False
        if "--round43-envelope-refinement" in explicit_command:
            index = explicit_command.index("--round43-envelope-refinement")
            explicit_off = explicit_command[index + 1] == "off"
        passed = (
            flags_absent and explicit_off and not mismatches and
            implicit["certified"] and explicit["certified"] and
            implicit["verified"] and explicit["verified"] and
            implicit["parameters"] and explicit["parameters"])
        rows.append({
            "instance_id": instance_id,
            "deterministic_field_count": len(FIELDS),
            "mismatch_count": len(mismatches),
            "mismatched_fields": ";".join(mismatches),
            "implicit_round43_flags_absent": flags_absent,
            "explicit_round43_mode_off": explicit_off,
            "implicit_sha256": implicit["deterministic_sha256"],
            "explicit_sha256": explicit["deterministic_sha256"],
            "both_strict_certificates": (
                implicit["certified"] and explicit["certified"]),
            "both_original_verifiers": (
                implicit["verified"] and explicit["verified"]),
            "both_parameter_roundtrips": (
                implicit["parameters"] and explicit["parameters"]),
            "default_off_equivalence_passed": passed,
        })
    common.write_csv(common.OUT / "default_off_equivalence.csv", rows)
    if not all(row["default_off_equivalence_passed"] for row in rows):
        raise RuntimeError("Round 43 default-off equivalence failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
