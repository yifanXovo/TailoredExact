#!/usr/bin/env python3
"""Select exactly one Round 43 envelope from development-10 evidence."""

from __future__ import annotations

import csv
import math
from statistics import mean
from typing import Any

import round43_common as common


MODES = ("constant", "single")


def gmean(values: list[float]) -> float:
    if not values or any(not math.isfinite(value) or value <= 0.0
                         for value in values):
        return math.inf
    return math.exp(sum(math.log(value) for value in values) / len(values))


def run_id(instance_id: str, mode: str) -> tuple[str, bool]:
    if instance_id in common.MECHANISM_ROLES:
        return (
            f"stage2-envelope__{instance_id}__algorithm__K1__d2__"
            f"rho0.01__no-adaptive__{mode}", True)
    return (
        f"stage2-development__{instance_id}__algorithm__K1__d2__"
        f"rho0.01__no-adaptive__{mode}", False)


def root_bound(run_dir: Any) -> float:
    trace = common.csv_rows(run_dir / "external" / "global_bound_trace.csv")
    values = [float(row["active_leaf_valid_lower_bound"])
              for row in trace
              if row["event_type"] == "native_root_processing_bound" and
              row["active_leaf_valid_lower_bound"]]
    return max(values) if values else math.nan


def main() -> int:
    rows: list[dict[str, Any]] = []
    e0_roots: dict[str, float] = {}
    for instance_id in common.MECHANISM_ROLES:
        identity = (
            f"stage2-envelope__{instance_id}__algorithm__K1__d2__"
            "rho0.01__no-adaptive__none")
        e0_roots[instance_id] = root_bound(common.RUNS / identity)
    for mode in MODES:
        for instance_id in common.DEVELOPMENT_IDS:
            identity, reused = run_id(instance_id, mode)
            run_dir = common.RUNS / identity
            result = common.load_json(run_dir / "result.json")
            command = common.load_json(run_dir / "command.json")
            certified = bool(result.get(
                "strict_certified_original_problem", False))
            failure = result.get("external_gini_tree_failure_reason", "")
            hard_failure = failure not in {"none", "overall_global_deadline"}
            lower = float(result["external_gini_tree_global_lower_bound"])
            upper = float(result["external_gini_tree_verified_upper_bound"])
            root = (root_bound(run_dir) if (run_dir / "external" /
                    "global_bound_trace.csv").is_file() else upper)
            rows.append({
                "instance_id": instance_id,
                "mode": mode,
                "run_id": identity,
                "reused_mechanism_row": reused,
                "executable_sha256": command["executable_sha256"],
                "certified": certified,
                "right_censored": not certified and not hard_failure,
                "hard_failure": hard_failure,
                "lifecycle_complete": bool(result.get(
                    "external_gini_tree_lifecycle_complete", True)),
                "valid_final_lower": lower,
                "verified_upper": upper,
                "relative_gap": max(0.0, upper - lower) /
                    max(abs(upper), 1e-12),
                "root_native_bound": root,
                "root_improvement_over_E0": (
                    root - e0_roots[instance_id]
                    if instance_id in e0_roots and math.isfinite(root)
                    else math.nan),
                "total_work": float(result.get(
                    "external_gini_tree_work", 0.0)),
                "solver_seconds": float(result.get(
                    "external_gini_tree_solver_seconds", 0.0)),
                "process_seconds": float(result.get(
                    "final_process_wall_time_seconds",
                    result.get("runtime_seconds", 0.0))),
                "peak_memory_gb": float(result.get(
                    "external_gini_tree_peak_memory_gb", 0.0)),
                "run_dir": common.relative(run_dir),
            })
    common.write_csv(common.OUT / "stage2_development_envelope_rows.csv", rows)
    summaries = []
    for mode in MODES:
        group = [row for row in rows if row["mode"] == mode]
        major = next(row for row in group
                     if row["instance_id"] ==
                     "round39_small_medium_V12_M3_Q30_slot08_seed1343324363")
        control = next(row for row in group
                       if row["instance_id"] ==
                       "round39_small_hard_V12_M3_Q30_slot08_seed1288546114")
        summaries.append({
            "mode": mode,
            "row_count": len(group),
            "reused_mechanism_rows": sum(
                row["reused_mechanism_row"] for row in group),
            "new_rows": sum(
                not row["reused_mechanism_row"] for row in group),
            "certified_count": sum(row["certified"] for row in group),
            "right_censored_count": sum(
                row["right_censored"] for row in group),
            "hard_failure_count": sum(row["hard_failure"] for row in group),
            "geomean_total_work": gmean([
                max(row["total_work"], 1e-12) for row in group]),
            "geomean_process_seconds": gmean([
                max(row["process_seconds"], 1e-12) for row in group]),
            "mean_relative_gap": mean(
                0.0 if row["certified"] else row["relative_gap"]
                for row in group),
            "major_regression_work": major["total_work"],
            "strong_control_work": control["total_work"],
            "max_peak_memory_gb": max(
                row["peak_memory_gb"] for row in group),
            "mean_mechanism_root_improvement_over_E0": mean([
                row["root_improvement_over_E0"] for row in group
                if math.isfinite(row["root_improvement_over_E0"])]),
        })
    summaries.sort(key=lambda row: (
        -row["certified_count"], row["mean_relative_gap"],
        row["major_regression_work"], row["strong_control_work"],
        row["geomean_total_work"], MODES.index(row["mode"])))
    common.write_csv(common.OUT / "stage2_development_envelope_summary.csv",
                     summaries)
    selected = summaries[0]["mode"]
    common.write_json(common.OUT / "stage2_final_envelope_selection.json", {
        "schema": "round43-stage2-final-envelope-selection-v1",
        "round_id": 43,
        "development_instances": 10,
        "evidence_rows": 20,
        "new_exact_rows": 8,
        "reused_exact_mechanism_rows": 12,
        "selected_envelope_mode": selected,
        "stage3_envelope_mode": selected,
        "selection_order": [
            "hard correctness", "certificate count", "final gap",
            "major severe-regression Work", "strong-control Work",
            "geometric mean Work", "time", "simplicity"],
        "selected_exactly_one": True,
        "all_rows_same_frozen_executable": len({
            row["executable_sha256"] for row in rows}) == 1,
        "executable_sha256": rows[0]["executable_sha256"],
        "reason": (
            "Single complete affine generation is selected over the constant "
            "cut by the frozen certificate/gap/Work order on development-10."
            if selected == "single" else
            "The constant descendant cut is selected by the frozen order."),
    })
    report = [
        "# Round 43 envelope ablation", "",
        "Stage 2 screened E0/E1/E2/E3 on six mechanisms, retained E1/E2, "
        "then completed development-10 using 12 exact reused mechanism rows "
        "and eight new rows.", "",
        "| mode | certificates | censored | gmean Work | gmean process s | "
        "major Work | control Work | mean mechanism root improvement vs E0 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in sorted(summaries, key=lambda item: MODES.index(item["mode"])):
        report.append(
            f"| {row['mode']} | {row['certified_count']}/10 | "
            f"{row['right_censored_count']} | "
            f"{row['geomean_total_work']:.6g} | "
            f"{row['geomean_process_seconds']:.6g} | "
            f"{row['major_regression_work']:.6g} | "
            f"{row['strong_control_work']:.6g} | "
            f"{row['mean_mechanism_root_improvement_over_E0']:.6g} |")
    report.extend(["", f"Frozen Stage 3 envelope: `{selected}`.", ""])
    common.write_text(common.OUT / "envelope_ablation.md",
                      "\n".join(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
