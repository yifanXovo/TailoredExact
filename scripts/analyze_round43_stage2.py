#!/usr/bin/env python3
"""Consolidate and rank the frozen 24-row Round 43 envelope screen."""

from __future__ import annotations

import csv
import json
import math
from statistics import mean
from typing import Any

import round43_common as common


MODES = ("none", "constant", "single", "iterated")


def gmean(values: list[float]) -> float:
    if not values or any(not math.isfinite(value) or value < 0.0
                         for value in values):
        return math.inf
    return math.exp(sum(math.log(max(value, 1e-12)) for value in values) /
                    len(values))


def load_row(instance_id: str, mode: str) -> dict[str, Any]:
    run_id = (
        f"stage2-envelope__{instance_id}__algorithm__K1__d2__"
        f"rho0.01__no-adaptive__{mode}")
    run_dir = common.RUNS / run_id
    result = common.load_json(run_dir / "result.json")
    command = common.load_json(run_dir / "command.json")
    envelope_rows = common.csv_rows(
        run_dir / "external" / "round43_envelope_ledger.csv")
    facets = common.csv_rows(
        run_dir / "external" / "round43_facet_ledger.csv")
    certified = bool(result.get("strict_certified_original_problem", False))
    hard_failure = result.get("external_gini_tree_failure_reason") not in {
        "none", "overall_global_deadline"}
    lower = float(result["external_gini_tree_global_lower_bound"])
    upper = float(result["external_gini_tree_verified_upper_bound"])
    relative_gap = max(0.0, upper - lower) / max(abs(upper), 1e-12)
    return {
        "instance_id": instance_id,
        "mechanism_role": common.MECHANISM_ROLES[instance_id],
        "mode": mode,
        "run_id": run_id,
        "executable_sha256": command["executable_sha256"],
        "status": result["status"],
        "certified": certified,
        "right_censored": not certified and not hard_failure,
        "hard_failure": hard_failure,
        "lifecycle_complete": bool(result.get(
            "external_gini_tree_lifecycle_complete", False)),
        "root_coverage_valid": bool(result.get(
            "external_gini_tree_root_coverage_valid", False)),
        "parent_child_coverage_valid": bool(result.get(
            "external_gini_tree_parent_child_coverage_valid", False)),
        "global_bound_monotone": bool(result.get(
            "external_gini_tree_global_bound_monotone", False)),
        "verified_upper": upper,
        "valid_final_lower": lower,
        "relative_gap": relative_gap,
        "total_work": float(result.get("external_gini_tree_work", math.nan)),
        "lp_work": float(result.get("external_gini_tree_lp_work", math.nan)),
        "terminal_mip_work": float(result.get(
            "external_gini_tree_terminal_mip_work", math.nan)),
        "solver_seconds": float(result.get(
            "external_gini_tree_solver_seconds", math.nan)),
        "process_seconds": float(result.get(
            "final_process_wall_time_seconds",
            result.get("runtime_seconds", math.nan))),
        "peak_memory_gb": float(result.get(
            "external_gini_tree_peak_memory_gb", math.nan)),
        "optimize_count": int(result.get(
            "external_gini_tree_optimize_count", 0)),
        "lp_optimize_count": int(result.get(
            "external_gini_tree_lp_optimize_count", 0)),
        "terminal_mip_optimize_count": int(result.get(
            "external_gini_tree_terminal_mip_optimize_count", 0)),
        "envelope_iterations": max(
            (int(row["iteration"]) for row in envelope_rows), default=0),
        "accepted_facet_rows": sum(
            row["accepted"].lower() in {"1", "true"} for row in facets),
        "run_dir": common.relative(run_dir),
    }


def main() -> int:
    rows = [load_row(instance_id, mode)
            for instance_id in common.MECHANISM_ROLES for mode in MODES]
    common.write_csv(common.OUT / "stage2_envelope_screen.csv", rows)
    summaries: list[dict[str, Any]] = []
    for mode in MODES:
        group = [row for row in rows if row["mode"] == mode]
        summaries.append({
            "mode": mode,
            "row_count": len(group),
            "certified_count": sum(row["certified"] for row in group),
            "right_censored_count": sum(
                row["right_censored"] for row in group),
            "hard_failure_count": sum(row["hard_failure"] for row in group),
            "all_engineering_gates_valid": all(
                row["lifecycle_complete"] and row["root_coverage_valid"] and
                row["parent_child_coverage_valid"] and
                row["global_bound_monotone"] and not row["hard_failure"]
                for row in group),
            "mean_final_relative_gap": mean(
                row["relative_gap"] for row in group),
            "geomean_total_work": gmean(
                [row["total_work"] for row in group]),
            "geomean_process_seconds": gmean(
                [row["process_seconds"] for row in group]),
            "max_peak_memory_gb": max(
                row["peak_memory_gb"] for row in group),
            "accepted_facet_rows": sum(
                row["accepted_facet_rows"] for row in group),
            "max_envelope_iterations": max(
                row["envelope_iterations"] for row in group),
        })
    reference = next(row for row in summaries if row["mode"] == "none")
    for row in summaries:
        row["work_ratio_vs_none"] = (
            row["geomean_total_work"] /
            reference["geomean_total_work"])
        row["gap_delta_vs_none"] = (
            row["mean_final_relative_gap"] -
            reference["mean_final_relative_gap"])
    eligible = [row for row in summaries
                if row["all_engineering_gates_valid"]]
    eligible.sort(key=lambda row: (
        -row["certified_count"], row["mean_final_relative_gap"],
        row["geomean_total_work"], MODES.index(row["mode"])))
    selected = [row["mode"] for row in eligible[:2]]
    common.write_csv(common.OUT / "stage2_envelope_summary.csv", summaries)
    common.write_json(common.OUT / "stage2_envelope_selection.json", {
        "schema": "round43-stage2-envelope-selection-v1",
        "round_id": 43,
        "row_count": len(rows),
        "depth": 2,
        "K0": 1,
        "adaptive_split": False,
        "selection_order": [
            "engineering correctness", "certified row count",
            "mean final relative gap for right-censored rows",
            "geometric mean total Work", "simpler mode on exact ties"],
        "selected_modes": selected,
        "primary_mode": selected[0] if selected else None,
        "maximum_modes_allowed": 2,
        "all_rows_same_frozen_executable": len({
            row["executable_sha256"] for row in rows}) == 1,
        "executable_sha256": rows[0]["executable_sha256"],
        "note": (
            "Right-censored rows are never treated as exact solves. Their "
            "valid final gaps rank modes only after correctness and exact "
            "certificate count; Work is the next criterion."),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
