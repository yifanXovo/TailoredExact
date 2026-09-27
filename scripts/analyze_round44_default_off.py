#!/usr/bin/env python3
"""Fail closed on implicit/default versus explicit Round 44-off drift."""

from __future__ import annotations

import hashlib
import json

import round43_analysis as historical
import round44_common as common
from run_round44_default_off import SENTINELS


FIELDS = (
    "objective", "lower", "upper", "work", "nodes", "algorithm_arm",
    "active_initial_intervals", "initial_leaf_count", "lp_count",
    "terminal_count", "split_count", "final_leaf_count", "model_hashes",
)


def deterministic(run_dir) -> dict:
    result = common.load_json(run_dir / "result.json")
    ledger = common.csv_rows(run_dir / "external" /
                             "paper_optimize_ledger.csv")
    values = {
        "objective": result["objective"],
        "lower": result["external_gini_tree_global_lower_bound"],
        "upper": result["external_gini_tree_verified_upper_bound"],
        "work": result["external_gini_tree_work"],
        "nodes": result["external_gini_tree_nodes"],
        "algorithm_arm": result["external_gini_tree_algorithm_arm"],
        "active_initial_intervals": result[
            "external_gini_tree_active_initial_intervals"],
        "initial_leaf_count": result[
            "external_gini_tree_initial_leaf_count"],
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
    values["certified"] = common.truth(
        result["strict_certified_original_problem"])
    values["verified"] = common.truth(
        result["verification"]["original_solution_feasible"])
    values["parameters"] = common.truth(result[
        "external_gini_tree_backend_parameter_roundtrip_valid"])
    return values


def main() -> int:
    rows = []
    for instance_id in SENTINELS:
        implicit_dir = common.RUNS / (
            f"default-off__{instance_id}__implicit")
        explicit_dir = common.RUNS / (
            f"default-off__{instance_id}__explicit")
        implicit = deterministic(implicit_dir)
        explicit = deterministic(explicit_dir)
        implicit_command = common.load_json(
            implicit_dir / "command.json")["command"]
        explicit_command = common.load_json(
            explicit_dir / "command.json")["command"]
        mismatches = [field for field in FIELDS
                      if implicit[field] != explicit[field]]
        implicit_absent = "--round44-envelope-tail-repair" not in (
            implicit_command)
        explicit_off = False
        if "--round44-envelope-tail-repair" in explicit_command:
            index = explicit_command.index("--round44-envelope-tail-repair")
            explicit_off = explicit_command[index + 1] == "off"
        same_executable = (
            common.load_json(implicit_dir / "command.json")[
                "executable_sha256"] ==
            common.load_json(explicit_dir / "command.json")[
                "executable_sha256"] == common.sha256(common.EXE))
        passed = (
            implicit_absent and explicit_off and same_executable and
            not mismatches and implicit["certified"] and
            explicit["certified"] and implicit["verified"] and
            explicit["verified"] and implicit["parameters"] and
            explicit["parameters"])
        rows.append({
            "instance_id": instance_id,
            "deterministic_field_count": len(FIELDS),
            "mismatch_count": len(mismatches),
            "mismatched_fields": ";".join(mismatches),
            "implicit_round44_flag_absent": implicit_absent,
            "explicit_round44_mode_off": explicit_off,
            "same_final_executable": same_executable,
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
        raise RuntimeError("Round 44 default-off equivalence failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
