#!/usr/bin/env python3
"""Collect Round 42 root/block relaxation and fractionality diagnostics."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import round42_common as common


STATIC = (
    ("ST-K2-P-CORE", "st-k2-p-core-reference", "diagnostic_st_k2"),
    ("ST-K4-P-CORE", "st-k4-p-core", "diagnostic_st_k4"),
    ("ST-K4-P-CORE-HIERARCHICAL", "st-k4-p-core-hierarchical",
     "diagnostic_st_k4_hier"),
)
COMPOSITES = (
    ("EXTERNAL-K2-FIXED", ("external-k2-left", "external-k2-right"),
     "diagnostic_external_k2"),
    ("PAIRED-K4", ("paired-k4-lower", "paired-k4-upper"),
     "diagnostic_paired_k4"),
    ("PAIRED-K4-FACTORED",
     ("paired-k4-lower-factored", "paired-k4-upper-factored"),
     "diagnostic_paired_k4_factored"),
)


def load(path: Path) -> dict[str, Any] | None:
    return common.load_json(path) if path.is_file() else None


def static_fields(instance: str, report_arm: str, arm: str,
                  tag: str) -> dict[str, Any] | None:
    result = load(common.RUNS /
                  f"static__{instance}__{arm}__root-lp__{tag}" /
                  "result.json")
    if not result:
        return None
    return {
        "instance_id": instance,
        "arm": report_arm,
        "component_count": 1,
        "root_lp_bound": result.get("round41_static_root_lp_bound", ""),
        "root_lp_work": result.get("round41_static_solver_work", ""),
        "root_lp_seconds": result.get(
            "round41_static_solver_runtime_seconds", ""),
        "route_binary_fractionality": result.get(
            "round41_static_route_binary_fractionality", ""),
        "visit_binary_fractionality": result.get(
            "round41_static_visit_binary_fractionality", ""),
        "inventory_bit_fractionality": result.get(
            "round41_static_inventory_bit_fractionality", ""),
        "selector_binary_fractionality": result.get(
            "round41_static_selector_binary_fractionality", ""),
        "gbit_product_ambiguity": result.get(
            "round41_static_segmented_mccormick_ambiguity", ""),
        "simplex_iterations": result.get(
            "external_gini_tree_simplex_iterations", ""),
        "barrier_iterations": result.get(
            "external_gini_tree_barrier_iterations", ""),
        "model_variables": result.get("round41_static_model_variables", ""),
        "model_rows": result.get(
            "round41_static_model_linear_constraints", ""),
        "model_nonzeros": result.get("round41_static_model_nonzeros", ""),
        "presolved_rows": result.get("round41_static_presolved_rows", ""),
        "presolved_columns": result.get(
            "round41_static_presolved_columns", ""),
        "presolved_nonzeros": result.get(
            "round41_static_presolved_nonzeros", ""),
        "diagnostic_valid": result.get(
            "round41_static_lp_diagnostics_available", False),
        "model_sha256": result.get(
            "round41_static_segmented_model_sha256", ""),
    }


def composite_fields(instance: str, report_arm: str,
                     arms: tuple[str, str], tag: str) -> dict[str, Any] | None:
    parts = [load(common.RUNS /
                  f"static__{instance}__{arm}__root-lp__{tag}" /
                  "result.json") for arm in arms]
    if not all(parts):
        return None
    complete = [part for part in parts if part]
    return {
        "instance_id": instance,
        "arm": report_arm,
        "component_count": len(complete),
        "root_lp_bound": min(float(part[
            "round41_static_root_lp_bound"]) for part in complete),
        "root_lp_work": sum(float(part[
            "round41_static_solver_work"]) for part in complete),
        "root_lp_seconds": sum(float(part[
            "round41_static_solver_runtime_seconds"]) for part in complete),
        "route_binary_fractionality": max(float(part.get(
            "round41_static_route_binary_fractionality", 0.0))
            for part in complete),
        "visit_binary_fractionality": max(float(part.get(
            "round41_static_visit_binary_fractionality", 0.0))
            for part in complete),
        "inventory_bit_fractionality": max(float(part.get(
            "round41_static_inventory_bit_fractionality", 0.0))
            for part in complete),
        "selector_binary_fractionality": max(float(part.get(
            "round41_static_selector_binary_fractionality", 0.0))
            for part in complete),
        "gbit_product_ambiguity": max(float(part.get(
            "round41_static_segmented_mccormick_ambiguity", 0.0))
            for part in complete),
        "simplex_iterations": "",
        "barrier_iterations": "",
        "model_variables": sum(int(part.get(
            "round41_static_model_variables", 0)) for part in complete),
        "model_rows": sum(int(part.get(
            "round41_static_model_linear_constraints", 0))
            for part in complete),
        "model_nonzeros": sum(int(part.get(
            "round41_static_model_nonzeros", 0)) for part in complete),
        "presolved_rows": sum(int(part.get(
            "round41_static_presolved_rows", 0)) for part in complete),
        "presolved_columns": sum(int(part.get(
            "round41_static_presolved_columns", 0)) for part in complete),
        "presolved_nonzeros": sum(int(part.get(
            "round41_static_presolved_nonzeros", 0)) for part in complete),
        "diagnostic_valid": all(bool(part.get(
            "round41_static_lp_diagnostics_available")) for part in complete),
        "model_sha256": ";".join(str(part.get(
            "round41_static_segmented_model_sha256", ""))
            for part in complete),
    }


def c6_initial_fields(instance: str, arm: str, tag: str,
                      report_arm: str) -> dict[str, Any] | None:
    run_dir = common.RUNS / f"c6__{instance}__{arm}__{tag}"
    result = load(run_dir / "result.json")
    ledger = run_dir / "external" / "lp_status_ledger.csv"
    if not result or not ledger.is_file():
        return None
    initial = [row for row in common.csv_rows(ledger)
               if re.fullmatch(r"L[0-3]", row.get("leaf_id", "")) and
               row.get("depth", "0") == "0"]
    bounds = [float(row["lower_bound"]) for row in initial
              if row.get("bound_available", "").lower() in {"1", "true"}]
    return {
        "instance_id": instance,
        "arm": report_arm,
        "component_count": len(initial),
        "root_lp_bound": min(bounds) if bounds else "",
        "root_lp_work": sum(float(row.get("work") or 0.0)
                            for row in initial),
        "root_lp_seconds": "",
        "route_binary_fractionality": "",
        "visit_binary_fractionality": "",
        "inventory_bit_fractionality": "",
        "selector_binary_fractionality": "",
        "gbit_product_ambiguity": "",
        "simplex_iterations": "",
        "barrier_iterations": "",
        "model_variables": "",
        "model_rows": "",
        "model_nonzeros": "",
        "presolved_rows": "",
        "presolved_columns": "",
        "presolved_nonzeros": "",
        "diagnostic_valid": len(bounds) == len(initial) == 4,
        "model_sha256": "",
    }


def main() -> int:
    manifests = common.csv_rows(common.OUT / "development_manifest.csv")
    rows: list[dict[str, Any]] = []
    for item in manifests:
        instance = item["instance_id"]
        for report, arm, tag in STATIC:
            row = static_fields(instance, report, arm, tag)
            if row:
                rows.append(row)
        for report, arms, tag in COMPOSITES:
            row = composite_fields(instance, report, arms, tag)
            if row:
                rows.append(row)
        for report, arm, tag in (
            ("C6-HGA-FULL-K4", "c6-reference", "development_reference"),
            ("C6-SIBLING-CORE", "sibling-core",
             "development_family_c_base"),
            ("C6-SIBLING-CORE-FACTORED", "sibling-core-factored",
             "development_family_c_factored"),
        ):
            row = c6_initial_fields(instance, arm, tag, report)
            if row:
                rows.append(row)
    if not rows:
        raise RuntimeError("no root-relaxation evidence found")
    common.write_csv(common.OUT / "root_relaxation_comparison.csv", rows)
    print({"rows": len(rows), "valid": sum(bool(row["diagnostic_valid"])
                                             for row in rows)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
