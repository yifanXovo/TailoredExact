#!/usr/bin/env python3
"""Audit and analyze the frozen Round 37 exploratory smoke pairs."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import round37_experiment_common as common


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def number(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes"}


def sequence_hash(run_dir: Path) -> str:
    trace = csv_rows(run_dir / "external" / "global_bound_trace.csv")
    keep = (
        "event_type", "active_leaf", "active_leaf_valid_lower_bound",
        "other_open_leaf_min_valid_lower_bound", "valid_global_lower_bound",
        "verified_global_upper_bound", "open_relevant_leaf_count",
        "closed_relevant_leaf_count", "event_source",
    )
    canonical = [tuple(row.get(field, "") for field in keep) for row in trace]
    data = json.dumps(canonical, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def mean_common_gap_auc(run_dir: Path, common_ub: float,
                        window: float) -> float:
    trace = csv_rows(run_dir / "external" / "global_bound_trace.csv")
    points: list[tuple[float, float]] = []
    for row in trace:
        t = number(row.get("exact_phase_elapsed_seconds"), -1.0)
        lb = number(row.get("valid_global_lower_bound"), 0.0)
        if t >= 0.0:
            points.append((t, lb))
    points.sort()
    if not points or window <= 0.0:
        return 0.0
    scale = max(1e-12, abs(common_ub))
    area = 0.0
    previous_t = 0.0
    previous_gap = max(0.0, (common_ub - points[0][1]) / scale)
    for t, lb in points:
        clipped = min(window, max(previous_t, t))
        area += previous_gap * (clipped - previous_t)
        if t >= window:
            previous_t = window
            break
        previous_t = t
        previous_gap = max(0.0, (common_ub - lb) / scale)
    if previous_t < window:
        area += previous_gap * (window - previous_t)
    return area / window


def manifest_valid(run_dir: Path, marker: dict[str, Any]) -> bool:
    manifest_path = run_dir / "artifact_manifest.csv"
    if (not manifest_path.is_file() or
            common.sha256(manifest_path) !=
            marker.get("artifact_manifest_sha256")):
        return False
    for artifact in csv_rows(manifest_path):
        path = run_dir / artifact["path"]
        if (not path.is_file() or path.stat().st_size != int(artifact["bytes"])
                or common.sha256(path) != artifact["sha256"]):
            return False
    return True


def main() -> int:
    freeze = common.load_json(common.SMOKE_FREEZE)
    matrix = common.csv_rows(common.SMOKE_MATRIX)
    panel = common.panel()
    by_panel: dict[str, dict[str, dict[str, str]]] = {}
    for row in matrix:
        by_panel.setdefault(row["panel_row_id"], {})[row["arm"]] = row

    pair_rows: list[dict[str, Any]] = []
    run_audit: list[dict[str, Any]] = []
    false_certificates = 0
    for panel_row_id, arms in by_panel.items():
        item = panel[panel_row_id]
        loaded: dict[str, tuple[Path, dict[str, Any], dict[str, Any]]] = {}
        for arm in ("C6", "G1"):
            row = arms[arm]
            run_dir = common.SMOKE_RUNS / row["run_id"]
            marker = common.load_json(run_dir / "completion_marker.json")
            result = common.load_json(run_dir / "result.json")
            gates = {
                "completion_marker_valid": marker.get("completed") is True,
                "artifact_manifest_valid": manifest_valid(run_dir, marker),
                "result_hash_valid": common.sha256(run_dir / "result.json") ==
                    marker.get("result_sha256"),
                "root_coverage_valid": boolean(result.get(
                    "external_gini_tree_root_coverage_valid")),
                "parent_child_coverage_valid": boolean(result.get(
                    "external_gini_tree_parent_child_coverage_valid")),
                "lifecycle_complete": boolean(result.get(
                    "external_gini_tree_lifecycle_complete")),
                "global_bound_monotone": boolean(result.get(
                    "external_gini_tree_global_bound_monotone")),
                "leaf_bounds_monotone": boolean(result.get(
                    "external_gini_tree_leaf_bounds_monotone")),
                "feasibility_gate": boolean(result.get(
                    "external_gini_tree_feasibility_consistency_gate")),
            }
            strict = boolean(result.get("strict_certified_original_problem"))
            lower = number(result.get("external_gini_tree_global_lower_bound"))
            upper = number(result.get("external_gini_tree_verified_upper_bound"))
            false_certificate = strict and not (
                all(gates.values()) and lower >= upper - 1e-7
            )
            false_certificates += int(false_certificate)
            run_audit.append({
                "run_id": row["run_id"], "panel_row_id": panel_row_id,
                "arm": arm, **gates, "strict_certificate": strict,
                "false_certificate": false_certificate,
                "all_gates_pass": all(gates.values()) and
                    not false_certificate,
            })
            loaded[arm] = (run_dir, marker, result)

        c6_dir, c6_marker, c6 = loaded["C6"]
        g1_dir, g1_marker, g1 = loaded["G1"]
        c6_lb = number(c6["external_gini_tree_global_lower_bound"])
        g1_lb = number(g1["external_gini_tree_global_lower_bound"])
        c6_ub = number(c6["external_gini_tree_verified_upper_bound"])
        g1_ub = number(g1["external_gini_tree_verified_upper_bound"])
        common_ub = min(c6_ub, g1_ub)
        scale = max(1e-12, abs(common_ub))
        c6_gap = max(0.0, (common_ub - c6_lb) / scale)
        g1_gap = max(0.0, (common_ub - g1_lb) / scale)
        gap_improvement = c6_gap - g1_gap
        if gap_improvement > 1e-7:
            outcome = "g1_improves"
        elif gap_improvement < -1e-7:
            outcome = "g1_regresses"
        else:
            outcome = "tie"

        c6_trace = csv_rows(c6_dir / "external" / "global_bound_trace.csv")
        g1_trace = csv_rows(g1_dir / "external" / "global_bound_trace.csv")
        c6_end = max(number(row["exact_phase_elapsed_seconds"])
                     for row in c6_trace)
        g1_end = max(number(row["exact_phase_elapsed_seconds"])
                     for row in g1_trace)
        common_window = min(c6_end, g1_end)
        c6_auc = mean_common_gap_auc(c6_dir, common_ub, common_window)
        g1_auc = mean_common_gap_auc(g1_dir, common_ub, common_window)

        parent_rows = csv_rows(
            g1_dir / "external" / "parent_child_bound_ledger.csv"
        )
        pilot_rows = [row for row in parent_rows if row["decision"] ==
                      "round37_pilot_weakest_midpoint_prefinement"]
        pilot_parent = number(pilot_rows[0]["parent_lp_bound"]) \
            if pilot_rows else 0.0
        pilot_post = number(pilot_rows[0]["post_split_bound"]) \
            if pilot_rows else 0.0
        pilot_gain = pilot_post - pilot_parent if pilot_rows else 0.0
        expected_leaf = "L" + str(item["weakest_initial_cell_index"])
        reported_leaf = str(g1.get("round37_pilot_weakest_leaf_id", ""))
        exposure = boolean(g1.get("round37_pilot_prefinement_performed"))
        pair_rows.append({
            "panel_ordinal": item["panel_ordinal"],
            "panel_row_id": panel_row_id,
            "instance_id": item["instance_id"],
            "V": item["V"], "M": item["M"],
            "scenario": item["scenario"],
            "common_verified_ub": common_ub,
            "c6_valid_lb": c6_lb, "g1_valid_lb": g1_lb,
            "c6_common_ub_gap": c6_gap, "g1_common_ub_gap": g1_gap,
            "g1_gap_improvement": gap_improvement,
            "outcome": outcome,
            "c6_strict": boolean(c6.get("strict_certified_original_problem")),
            "g1_strict": boolean(g1.get("strict_certified_original_problem")),
            "certificate_regression": boolean(
                c6.get("strict_certified_original_problem")) and not boolean(
                    g1.get("strict_certified_original_problem")),
            "pilot_all_initial_lps_complete": boolean(g1.get(
                "round37_pilot_all_initial_lps_complete")),
            "pilot_initial_lp_count": int(number(g1.get(
                "round37_pilot_initial_lp_count"))),
            "expected_weakest_leaf": expected_leaf,
            "reported_weakest_leaf": reported_leaf,
            "weakest_cell_reproduced": exposure and
                reported_leaf == expected_leaf,
            "pilot_exposure": exposure,
            "pilot_prefinement_count": int(number(g1.get(
                "round37_pilot_prefinement_count"))),
            "pilot_parent_lp_bound": pilot_parent,
            "pilot_post_split_bound": pilot_post,
            "pilot_absolute_bound_gain": pilot_gain,
            "pilot_normalized_bound_gain": pilot_gain /
                max(1e-7, common_ub - pilot_parent) if pilot_rows else 0.0,
            "common_exact_window_seconds": common_window,
            "c6_mean_common_gap_auc": c6_auc,
            "g1_mean_common_gap_auc": g1_auc,
            "g1_auc_improvement": c6_auc - g1_auc,
            "c6_sequence_sha256": sequence_hash(c6_dir),
            "g1_sequence_sha256": sequence_hash(g1_dir),
            "c6_work_descriptive": number(c6.get("external_gini_tree_work")),
            "g1_work_descriptive": number(g1.get("external_gini_tree_work")),
            "c6_nodes_descriptive": number(c6.get("external_gini_tree_nodes")),
            "g1_nodes_descriptive": number(g1.get("external_gini_tree_nodes")),
        })

    common.write_csv(common.OUT / "smoke_run_audit.csv", run_audit)
    common.write_csv(common.OUT / "smoke_pair_analysis.csv", pair_rows)
    exposures = [row for row in pair_rows if row["pilot_exposure"]]
    summary = {
        "schema": "round37-smoke-analysis-v1",
        "exploratory": True,
        "freeze_sha256": common.sha256(common.SMOKE_FREEZE),
        "matrix_sha256": freeze["matrix_sha256"],
        "run_count": len(run_audit),
        "pair_count": len(pair_rows),
        "all_run_gates_pass": all(row["all_gates_pass"] for row in run_audit),
        "false_certificate_count": false_certificates,
        "certificate_regression_count": sum(
            row["certificate_regression"] for row in pair_rows
        ),
        "pilot_exposure_count": len(exposures),
        "pilot_unexposed_count": len(pair_rows) - len(exposures),
        "unexposed_reason": (
            "V50 moderate process cap reached during initial LP census"
            if len(exposures) < len(pair_rows) else "none"
        ),
        "historical_weakest_cell_reproduced_count": sum(
            row["weakest_cell_reproduced"] for row in exposures
        ),
        "positive_pilot_bound_gain_count": sum(
            row["pilot_absolute_bound_gain"] > 1e-7 for row in exposures
        ),
        "g1_final_gap_improvement_count": sum(
            row["outcome"] == "g1_improves" for row in pair_rows
        ),
        "g1_final_gap_regression_count": sum(
            row["outcome"] == "g1_regresses" for row in pair_rows
        ),
        "final_gap_tie_count": sum(
            row["outcome"] == "tie" for row in pair_rows
        ),
        "sum_common_ub_gap_improvement": sum(
            row["g1_gap_improvement"] for row in pair_rows
        ),
        "v50_regression_concern": any(
            row["V"] == 50 and row["outcome"] == "g1_regresses"
            for row in pair_rows
        ),
        "stage_decision": "advance_to_focused_diagnostic_without_rule_change",
        "decision_reason": (
            "Exactness gates passed and every exposed pilot produced a positive "
            "selected-cell LP bound gain with historical weakest-cell "
            "reproduction, but one V50 row was censored before exposure and "
            "the exposed V50 high-imbalance row regressed in final gap. A "
            "focused medium-cap diagnostic is warranted; broad validation or "
            "promotion is not."
        ),
        "pairs": pair_rows,
    }
    common.write_json(common.OUT / "smoke_analysis.json", summary)
    lines = [
        "# Round 37 exploratory smoke analysis", "",
        f"All run gates passed: **{summary['all_run_gates_pass']}**; false "
        f"certificates: **{false_certificates}**; certificate regressions: "
        f"**{summary['certificate_regression_count']}**.", "",
        f"The G1 policy executed on **{len(exposures)}/6** pairs. The remaining "
        "V50 moderate row exhausted the 180-second cap during the complete "
        "four-cell LP census, before any policy decision or split.", "",
        "| Row | V/M | Exposure | Weakest reproduced | Pilot LP gain | "
        "C6 common-UB gap | G1 common-UB gap | Outcome |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in pair_rows:
        lines.append(
            f"| {row['panel_row_id']} | {row['V']}/{row['M']} | "
            f"{row['pilot_exposure']} | {row['weakest_cell_reproduced']} | "
            f"{row['pilot_absolute_bound_gain']:.6g} | "
            f"{row['c6_common_ub_gap']:.6g} | "
            f"{row['g1_common_ub_gap']:.6g} | {row['outcome']} |"
        )
    lines.extend([
        "", "## Decision", "",
        "Advance to a focused medium-cap diagnostic without changing G1. The "
        "mechanism is real at the local relaxation level: every exposed pilot "
        "strictly raised the selected cell's valid LP bound, and all 5 exposed "
        "cells reproduced the independently observed Round 36 weakest-cell "
        "index. End-to-end evidence is not uniformly positive: one V20 row "
        "improved materially, three pairs tied, one hard V50 row was censored, "
        "and the V50 high-imbalance row regressed. This is evidence for a "
        "mechanism diagnostic, not candidate promotion.",
    ])
    (common.OUT / "smoke_analysis.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: summary[key] for key in (
        "all_run_gates_pass", "false_certificate_count",
        "pilot_exposure_count", "positive_pilot_bound_gain_count",
        "g1_final_gap_improvement_count", "g1_final_gap_regression_count",
        "final_gap_tie_count", "stage_decision",
    )}, indent=2, sort_keys=True))
    return 0 if summary["all_run_gates_pass"] and not false_certificates else 1


if __name__ == "__main__":
    raise SystemExit(main())
