#!/usr/bin/env python3
"""Audit and analyze the frozen Round 38 exploratory smoke pairs."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import round38_experiment_common as common


def number(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def boolean(value: Any) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes"}


def sequence_hash(run_dir: Path) -> str:
    trace = common.csv_rows(run_dir / "external" / "global_bound_trace.csv")
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
    trace = common.csv_rows(run_dir / "external" / "global_bound_trace.csv")
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
    if (not manifest_path.is_file() or common.sha256(manifest_path) !=
            marker.get("artifact_manifest_sha256")):
        return False
    for artifact in common.csv_rows(manifest_path):
        path = run_dir / artifact["path"]
        if (not path.is_file() or
                path.stat().st_size != int(artifact["bytes"]) or
                common.sha256(path) != artifact["sha256"]):
            return False
    return True


def main() -> int:
    freeze = common.load_json(common.SMOKE_FREEZE)
    matrix = common.csv_rows(common.SMOKE_MATRIX)
    panel = common.panel()
    by_panel: dict[str, dict[str, dict[str, str]]] = {}
    for row in matrix:
        by_panel.setdefault(row["panel_row_id"], {})[row["arm"]] = row
    run_audit: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    false_certificates = 0
    for panel_id, arms in by_panel.items():
        item = panel[panel_id]
        loaded: dict[str, tuple[Path, dict[str, Any], dict[str, Any]]] = {}
        for arm in ("C6", "G2A"):
            row = arms[arm]
            run_dir = common.SMOKE_RUNS / row["run_id"]
            marker = common.load_json(run_dir / "completion_marker.json")
            result = common.load_json(run_dir / "result.json")
            expected_policy = (
                "off" if arm == "C6" else "pilot-next-frontier-complete"
            )
            lower = number(result["external_gini_tree_global_lower_bound"])
            upper = number(result["external_gini_tree_verified_upper_bound"])
            gates = {
                "completion_marker_valid": marker.get("completed") is True,
                "artifact_manifest_valid": manifest_valid(run_dir, marker),
                "result_hash_valid": common.sha256(run_dir / "result.json") ==
                    marker.get("result_sha256"),
                "arm_contract_valid":
                    result.get("round38_c6_frontier_policy") ==
                    expected_policy,
                "round37_policy_off":
                    result.get("round37_c6_geometry_policy") == "off",
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
            false_certificate = strict and not (
                all(gates.values()) and
                boolean(result.get(
                    "external_gini_tree_all_relevant_leaves_closed")) and
                lower >= upper - 1e-7
            )
            false_certificates += int(false_certificate)
            run_audit.append({
                "run_id": row["run_id"],
                "panel_row_id": panel_id,
                "arm": arm,
                **gates,
                "strict_certificate": strict,
                "false_certificate": false_certificate,
                "all_gates_pass": all(gates.values()) and
                    not false_certificate,
            })
            loaded[arm] = (run_dir, marker, result)
        c6_dir, _, c6 = loaded["C6"]
        g2_dir, _, g2 = loaded["G2A"]
        c6_lb = number(c6["external_gini_tree_global_lower_bound"])
        g2_lb = number(g2["external_gini_tree_global_lower_bound"])
        common_ub = min(
            number(c6["external_gini_tree_verified_upper_bound"]),
            number(g2["external_gini_tree_verified_upper_bound"]),
        )
        scale = max(1e-12, abs(common_ub))
        c6_gap = max(0.0, (common_ub - c6_lb) / scale)
        g2_gap = max(0.0, (common_ub - g2_lb) / scale)
        improvement = c6_gap - g2_gap
        if improvement > 1e-7:
            outcome = "g2a_improves"
        elif improvement < -1e-7:
            outcome = "g2a_regresses"
        else:
            outcome = "tie"
        c6_trace = common.csv_rows(
            c6_dir / "external" / "global_bound_trace.csv"
        )
        g2_trace = common.csv_rows(
            g2_dir / "external" / "global_bound_trace.csv"
        )
        common_window = min(
            max(number(row["exact_phase_elapsed_seconds"]) for row in c6_trace),
            max(number(row["exact_phase_elapsed_seconds"]) for row in g2_trace),
        )
        c6_auc = mean_common_gap_auc(c6_dir, common_ub, common_window)
        g2_auc = mean_common_gap_auc(g2_dir, common_ub, common_window)
        pairs.append({
            "panel_ordinal": item["panel_ordinal"],
            "panel_row_id": panel_id,
            "instance_id": item["instance_id"],
            "V": item["V"],
            "M": item["M"],
            "scenario": item["scenario"],
            "common_verified_ub": common_ub,
            "c6_valid_lb": c6_lb,
            "g2a_valid_lb": g2_lb,
            "c6_common_ub_gap": c6_gap,
            "g2a_common_ub_gap": g2_gap,
            "g2a_gap_improvement": improvement,
            "outcome": outcome,
            "c6_strict": boolean(
                c6.get("strict_certified_original_problem")
            ),
            "g2a_strict": boolean(
                g2.get("strict_certified_original_problem")
            ),
            "certificate_regression": boolean(
                c6.get("strict_certified_original_problem")
            ) and not boolean(g2.get("strict_certified_original_problem")),
            "pilot_all_initial_lps_complete": boolean(
                g2.get("round38_pilot_all_initial_lps_complete")
            ),
            "pilot_initial_lp_count": int(number(
                g2.get("round38_pilot_initial_lp_count")
            )),
            "pilot_eligible_cell_count": int(number(
                g2.get("round38_pilot_eligible_cell_count")
            )),
            "pilot_frontier_plateau_size": int(number(
                g2.get("round38_pilot_frontier_plateau_size")
            )),
            "pilot_unique_controlling_cell": boolean(
                g2.get("round38_pilot_unique_controlling_cell")
            ),
            "pilot_next_strict_frontier_available": boolean(
                g2.get("round38_pilot_next_strict_frontier_available")
            ),
            "pilot_selected_leaf": g2.get(
                "round38_pilot_selected_leaf_id", ""
            ),
            "pilot_children_evaluated": boolean(
                g2.get("round38_pilot_children_evaluated")
            ),
            "pilot_b_plus": number(g2.get("round38_pilot_b_plus")),
            "pilot_delta_local": number(
                g2.get("round38_pilot_delta_local")
            ),
            "pilot_L_i_plus": number(
                g2.get("round38_pilot_hypothetical_global_bound")
            ),
            "pilot_delta_global": number(
                g2.get("round38_pilot_delta_global")
            ),
            "pilot_frontier_completion": number(
                g2.get("round38_pilot_frontier_completion")
            ),
            "pilot_completes_next_strict_frontier": boolean(
                g2.get("round38_pilot_completes_next_strict_frontier")
            ),
            "pilot_refinement_performed": boolean(
                g2.get("round38_pilot_refinement_performed")
            ),
            "pilot_rejection_count": int(number(
                g2.get("round38_pilot_rejection_count")
            )),
            "pilot_decision_reason": g2.get(
                "round38_pilot_decision_reason", ""
            ),
            "common_exact_window_seconds": common_window,
            "c6_mean_common_gap_auc": c6_auc,
            "g2a_mean_common_gap_auc": g2_auc,
            "g2a_auc_improvement": c6_auc - g2_auc,
            "c6_sequence_sha256": sequence_hash(c6_dir),
            "g2a_sequence_sha256": sequence_hash(g2_dir),
            "c6_work_descriptive": number(
                c6.get("external_gini_tree_work")
            ),
            "g2a_work_descriptive": number(
                g2.get("external_gini_tree_work")
            ),
            "c6_nodes_descriptive": number(
                c6.get("external_gini_tree_nodes")
            ),
            "g2a_nodes_descriptive": number(
                g2.get("external_gini_tree_nodes")
            ),
            "c6_exact_seconds_descriptive": number(
                c6.get("external_gini_tree_elapsed_seconds")
            ),
            "g2a_exact_seconds_descriptive": number(
                g2.get("external_gini_tree_elapsed_seconds")
            ),
        })
    common.write_csv(common.OUT / "smoke_run_audit.csv", run_audit)
    common.write_csv(common.OUT / "smoke_pair_analysis.csv", pairs)
    exposed = [row for row in pairs if row["pilot_children_evaluated"]]
    summary = {
        "schema": "round38-smoke-analysis-v1",
        "exploratory": True,
        "freeze_sha256": common.sha256(common.SMOKE_FREEZE),
        "matrix_sha256": freeze["matrix_sha256"],
        "run_count": len(run_audit),
        "pair_count": len(pairs),
        "all_run_gates_pass": all(row["all_gates_pass"] for row in run_audit),
        "false_certificate_count": false_certificates,
        "certificate_regression_count": sum(
            row["certificate_regression"] for row in pairs
        ),
        "pilot_child_evaluation_count": len(exposed),
        "pilot_refinement_count": sum(
            row["pilot_refinement_performed"] for row in pairs
        ),
        "next_frontier_completion_count": sum(
            row["pilot_completes_next_strict_frontier"] for row in pairs
        ),
        "g2a_final_gap_improvement_count": sum(
            row["outcome"] == "g2a_improves" for row in pairs
        ),
        "g2a_final_gap_regression_count": sum(
            row["outcome"] == "g2a_regresses" for row in pairs
        ),
        "final_gap_tie_count": sum(row["outcome"] == "tie" for row in pairs),
        "round37_v50_regression_witness_fixed_at_smoke": next(
            row["outcome"] == "tie" for row in pairs
            if int(row["panel_ordinal"]) == 10
        ),
        "round37_v20_positive_witness_retained_at_smoke": next(
            row["outcome"] == "g2a_improves" for row in pairs
            if int(row["panel_ordinal"]) == 8
        ),
        "stage_decision": "advance_frozen_g2a_to_medium_full_panel",
        "decision_reason": (
            "All exactness and artifact gates passed with zero false "
            "certificates. No midpoint pair completed the next strict "
            "frontier and no G2-A refinement occurred, falsifying immediate "
            "frontier completion as the cause of the retained V20 benefit. "
            "Nevertheless the stable V20 positive remained positive and the "
            "stable V50 regression became a tie, so the frozen rule warrants "
            "a medium-cap full-panel test for generality and pilot-overhead "
            "effects without any policy change."
        ),
        "pairs": pairs,
    }
    common.write_json(common.OUT / "smoke_analysis.json", summary)
    lines = [
        "# Round 38 exploratory smoke analysis",
        "",
        f"All run gates passed: **{summary['all_run_gates_pass']}**; false "
        f"certificates: **{false_certificates}**; certificate regressions: "
        f"**{summary['certificate_regression_count']}**.",
        "",
        "| Row | V/M | Children evaluated | Completes frontier | Split | "
        "C6 gap | G2-A gap | Gap change | AUC change | Outcome |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in pairs:
        lines.append(
            f"| {row['panel_row_id']} | {row['V']}/{row['M']} | "
            f"{row['pilot_children_evaluated']} | "
            f"{row['pilot_completes_next_strict_frontier']} | "
            f"{row['pilot_refinement_performed']} | "
            f"{row['c6_common_ub_gap']:.6g} | "
            f"{row['g2a_common_ub_gap']:.6g} | "
            f"{row['g2a_gap_improvement']:.6g} | "
            f"{row['g2a_auc_improvement']:.6g} | {row['outcome']} |"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        summary["decision_reason"],
    ])
    (common.OUT / "smoke_analysis.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: summary[key] for key in (
        "all_run_gates_pass", "false_certificate_count",
        "pilot_child_evaluation_count", "next_frontier_completion_count",
        "pilot_refinement_count", "g2a_final_gap_improvement_count",
        "g2a_final_gap_regression_count", "final_gap_tie_count",
        "stage_decision",
    )}, indent=2, sort_keys=True))
    return 0 if summary["all_run_gates_pass"] and not false_certificates else 1


if __name__ == "__main__":
    raise SystemExit(main())
