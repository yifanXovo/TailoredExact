#!/usr/bin/env python3
"""Analyze a frozen post-smoke Round 37 paired stage."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import round37_experiment_common as common


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def number(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def sequence_hash(run_dir: Path) -> str:
    trace = rows(run_dir / "external" / "global_bound_trace.csv")
    fields = (
        "event_type", "active_leaf", "active_leaf_valid_lower_bound",
        "other_open_leaf_min_valid_lower_bound", "valid_global_lower_bound",
        "verified_global_upper_bound", "open_relevant_leaf_count",
        "closed_relevant_leaf_count", "event_source",
    )
    canonical = [tuple(row.get(field, "") for field in fields)
                 for row in trace]
    return hashlib.sha256(json.dumps(
        canonical, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def gap_auc(run_dir: Path, common_ub: float, window: float) -> float:
    trace = rows(run_dir / "external" / "global_bound_trace.csv")
    points = sorted((number(row["exact_phase_elapsed_seconds"]),
                     number(row["valid_global_lower_bound"])) for row in trace)
    if not points or window <= 0.0:
        return 0.0
    scale = max(1e-12, abs(common_ub))
    area, prior_t = 0.0, 0.0
    prior_gap = max(0.0, (common_ub - points[0][1]) / scale)
    for t, lb in points:
        clipped = min(window, max(prior_t, t))
        area += prior_gap * (clipped - prior_t)
        if t >= window:
            prior_t = window
            break
        prior_t = t
        prior_gap = max(0.0, (common_ub - lb) / scale)
    area += prior_gap * max(0.0, window - prior_t)
    return area / window


def manifest_valid(run_dir: Path, marker: dict[str, Any]) -> bool:
    path = run_dir / "artifact_manifest.csv"
    if (not path.is_file() or common.sha256(path) !=
            marker.get("artifact_manifest_sha256")):
        return False
    for artifact in rows(path):
        item = run_dir / artifact["path"]
        if (not item.is_file() or item.stat().st_size != int(artifact["bytes"])
                or common.sha256(item) != artifact["sha256"]):
            return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--matrix", required=True, type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--output-prefix", required=True)
    args = parser.parse_args()
    matrix = common.csv_rows(args.matrix)
    freeze = common.load_json(args.freeze)
    panel = common.panel()
    by_panel: dict[str, dict[str, dict[str, str]]] = {}
    for row in matrix:
        by_panel.setdefault(row["panel_row_id"], {})[row["arm"]] = row
    audits: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    for panel_id, arms in by_panel.items():
        item = panel[panel_id]
        loaded: dict[str, tuple[Path, dict[str, Any]]] = {}
        for arm in ("C6", "G1"):
            run_dir = args.runs / arms[arm]["run_id"]
            marker = common.load_json(run_dir / "completion_marker.json")
            result = common.load_json(run_dir / "result.json")
            strict = bool(result.get("strict_certified_original_problem"))
            lower = number(result["external_gini_tree_global_lower_bound"])
            upper = number(result["external_gini_tree_verified_upper_bound"])
            gates = {
                "completion_marker_valid": marker.get("completed") is True,
                "artifact_manifest_valid": manifest_valid(run_dir, marker),
                "result_hash_valid": common.sha256(run_dir / "result.json") ==
                    marker.get("result_sha256"),
                "root_coverage_valid": bool(result.get(
                    "external_gini_tree_root_coverage_valid")),
                "parent_child_coverage_valid": bool(result.get(
                    "external_gini_tree_parent_child_coverage_valid")),
                "lifecycle_complete": bool(result.get(
                    "external_gini_tree_lifecycle_complete")),
                "global_bound_monotone": bool(result.get(
                    "external_gini_tree_global_bound_monotone")),
                "leaf_bounds_monotone": bool(result.get(
                    "external_gini_tree_leaf_bounds_monotone")),
                "feasibility_gate": bool(result.get(
                    "external_gini_tree_feasibility_consistency_gate")),
            }
            false_certificate = strict and not (
                all(gates.values()) and lower >= upper - 1e-7
            )
            audits.append({
                "run_id": arms[arm]["run_id"], "panel_row_id": panel_id,
                "arm": arm, **gates, "strict_certificate": strict,
                "false_certificate": false_certificate,
                "all_gates_pass": all(gates.values()) and
                    not false_certificate,
            })
            loaded[arm] = (run_dir, result)
        c6_dir, c6 = loaded["C6"]
        g1_dir, g1 = loaded["G1"]
        common_ub = min(number(c6["external_gini_tree_verified_upper_bound"]),
                        number(g1["external_gini_tree_verified_upper_bound"]))
        scale = max(1e-12, abs(common_ub))
        c6_gap = max(0.0, (common_ub - number(
            c6["external_gini_tree_global_lower_bound"])) / scale)
        g1_gap = max(0.0, (common_ub - number(
            g1["external_gini_tree_global_lower_bound"])) / scale)
        improvement = c6_gap - g1_gap
        outcome = ("g1_improves" if improvement > 1e-7 else
                   "g1_regresses" if improvement < -1e-7 else "tie")
        c6_trace = rows(c6_dir / "external" / "global_bound_trace.csv")
        g1_trace = rows(g1_dir / "external" / "global_bound_trace.csv")
        window = min(max(number(row["exact_phase_elapsed_seconds"])
                         for row in c6_trace),
                     max(number(row["exact_phase_elapsed_seconds"])
                         for row in g1_trace))
        pilot = [row for row in rows(
            g1_dir / "external" / "parent_child_bound_ledger.csv"
        ) if row["decision"] ==
            "round37_pilot_weakest_midpoint_prefinement"]
        parent_bound = number(pilot[0]["parent_lp_bound"]) if pilot else 0.0
        post_bound = number(pilot[0]["post_split_bound"]) if pilot else 0.0
        exposure = bool(g1.get("round37_pilot_prefinement_performed"))
        reported_leaf = str(g1.get("round37_pilot_weakest_leaf_id", ""))
        pairs.append({
            "panel_ordinal": item["panel_ordinal"],
            "panel_row_id": panel_id, "instance_id": item["instance_id"],
            "V": item["V"], "M": item["M"],
            "scenario": item["scenario"], "common_verified_ub": common_ub,
            "c6_valid_lb": number(c6["external_gini_tree_global_lower_bound"]),
            "g1_valid_lb": number(g1["external_gini_tree_global_lower_bound"]),
            "c6_common_ub_gap": c6_gap, "g1_common_ub_gap": g1_gap,
            "g1_gap_improvement": improvement, "outcome": outcome,
            "c6_strict": bool(c6.get("strict_certified_original_problem")),
            "g1_strict": bool(g1.get("strict_certified_original_problem")),
            "certificate_regression": bool(c6.get(
                "strict_certified_original_problem")) and not bool(g1.get(
                    "strict_certified_original_problem")),
            "pilot_all_initial_lps_complete": bool(g1.get(
                "round37_pilot_all_initial_lps_complete")),
            "pilot_initial_lp_count": int(number(g1.get(
                "round37_pilot_initial_lp_count"))),
            "expected_weakest_leaf": "L" +
                str(item["weakest_initial_cell_index"]),
            "reported_weakest_leaf": reported_leaf,
            "weakest_cell_reproduced": exposure and reported_leaf ==
                "L" + str(item["weakest_initial_cell_index"]),
            "pilot_exposure": exposure,
            "pilot_prefinement_count": int(number(g1.get(
                "round37_pilot_prefinement_count"))),
            "pilot_parent_lp_bound": parent_bound,
            "pilot_post_split_bound": post_bound,
            "pilot_absolute_bound_gain": post_bound - parent_bound
                if pilot else 0.0,
            "pilot_normalized_bound_gain": (post_bound - parent_bound) /
                max(1e-7, common_ub - parent_bound) if pilot else 0.0,
            "common_exact_window_seconds": window,
            "c6_mean_common_gap_auc": gap_auc(c6_dir, common_ub, window),
            "g1_mean_common_gap_auc": gap_auc(g1_dir, common_ub, window),
            "g1_auc_improvement": gap_auc(c6_dir, common_ub, window) -
                gap_auc(g1_dir, common_ub, window),
            "c6_sequence_sha256": sequence_hash(c6_dir),
            "g1_sequence_sha256": sequence_hash(g1_dir),
            "c6_work_descriptive": number(c6.get("external_gini_tree_work")),
            "g1_work_descriptive": number(g1.get("external_gini_tree_work")),
        })
    prefix = common.OUT / args.output_prefix
    common.write_csv(prefix.with_name(prefix.name + "_run_audit.csv"), audits)
    common.write_csv(prefix.with_name(prefix.name + "_pair_analysis.csv"), pairs)
    exposures = [row for row in pairs if row["pilot_exposure"]]
    summary = {
        "schema": f"round37-{args.stage}-analysis-v1",
        "stage": args.stage, "exploratory": True,
        "freeze_sha256": common.sha256(args.freeze),
        "matrix_sha256": freeze["matrix_sha256"],
        "run_count": len(audits), "pair_count": len(pairs),
        "all_run_gates_pass": all(row["all_gates_pass"] for row in audits),
        "false_certificate_count": sum(row["false_certificate"]
                                       for row in audits),
        "certificate_regression_count": sum(row["certificate_regression"]
                                            for row in pairs),
        "pilot_exposure_count": len(exposures),
        "weakest_cell_reproduced_count": sum(
            row["weakest_cell_reproduced"] for row in exposures),
        "positive_pilot_bound_gain_count": sum(
            row["pilot_absolute_bound_gain"] > 1e-7 for row in exposures),
        "g1_final_gap_improvement_count": sum(
            row["outcome"] == "g1_improves" for row in pairs),
        "g1_final_gap_regression_count": sum(
            row["outcome"] == "g1_regresses" for row in pairs),
        "final_gap_tie_count": sum(row["outcome"] == "tie" for row in pairs),
        "sum_common_ub_gap_improvement": sum(
            row["g1_gap_improvement"] for row in pairs),
        "pairs": pairs,
    }
    common.write_json(prefix.with_name(prefix.name + "_analysis.json"), summary)
    lines = [
        f"# Round 37 {args.stage.replace('_', ' ')} analysis", "",
        f"All run gates passed: **{summary['all_run_gates_pass']}**; false "
        f"certificates: **{summary['false_certificate_count']}**; certificate "
        f"regressions: **{summary['certificate_regression_count']}**.", "",
        "| Row | V/M | Exposure | Pilot LP gain | C6 common-UB gap | "
        "G1 common-UB gap | AUC improvement | Outcome |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in pairs:
        lines.append(
            f"| {row['panel_row_id']} | {row['V']}/{row['M']} | "
            f"{row['pilot_exposure']} | "
            f"{row['pilot_absolute_bound_gain']:.6g} | "
            f"{row['c6_common_ub_gap']:.6g} | "
            f"{row['g1_common_ub_gap']:.6g} | "
            f"{row['g1_auc_improvement']:.6g} | {row['outcome']} |"
        )
    prefix.with_name(prefix.name + "_analysis.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: summary[key] for key in (
        "all_run_gates_pass", "false_certificate_count",
        "pilot_exposure_count", "positive_pilot_bound_gain_count",
        "g1_final_gap_improvement_count", "g1_final_gap_regression_count",
        "final_gap_tie_count", "sum_common_ub_gap_improvement",
    )}, indent=2, sort_keys=True))
    return 0 if summary["all_run_gates_pass"] and not summary[
        "false_certificate_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
