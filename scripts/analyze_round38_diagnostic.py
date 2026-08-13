#!/usr/bin/env python3
"""Audit the Round 38 full-panel diagnostic and frontier persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import analyze_round38_smoke as metrics
import round38_experiment_common as common


MATRIX = common.OUT / "round38_diagnostic_matrix.csv"
FREEZE = common.OUT / "round38_diagnostic_freeze.json"
RUNS = common.OUT / "diagnostic_runs"
OUTPUT_PREFIX = "diagnostic"
ANALYSIS_SCHEMA = "round38-diagnostic-analysis-v1"


def count_rows(path: Path, field: str, value: str = "1") -> int:
    return sum(row.get(field, "") == value for row in common.csv_rows(path))


def main() -> int:
    freeze = common.load_json(FREEZE)
    matrix = common.csv_rows(MATRIX)
    panel = common.panel()
    by_panel: dict[str, dict[str, dict[str, str]]] = {}
    for row in matrix:
        by_panel.setdefault(row["panel_row_id"], {})[row["arm"]] = row
    run_audit: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    frontier: list[dict[str, Any]] = []
    downstream: list[dict[str, Any]] = []
    false_certificates = 0
    for panel_id, arms in by_panel.items():
        item = panel[panel_id]
        loaded: dict[str, tuple[Path, dict[str, Any]]] = {}
        for arm in ("C6", "G2A"):
            row = arms[arm]
            run_dir = RUNS / row["run_id"]
            marker = common.load_json(run_dir / "completion_marker.json")
            result = common.load_json(run_dir / "result.json")
            expected_policy = (
                "off" if arm == "C6" else "pilot-next-frontier-complete"
            )
            lower = metrics.number(
                result["external_gini_tree_global_lower_bound"]
            )
            upper = metrics.number(
                result["external_gini_tree_verified_upper_bound"]
            )
            gates = {
                "completion_marker_valid": marker.get("completed") is True,
                "artifact_manifest_valid": metrics.manifest_valid(
                    run_dir, marker
                ),
                "result_hash_valid": common.sha256(run_dir / "result.json") ==
                    marker.get("result_sha256"),
                "arm_contract_valid":
                    result.get("round38_c6_frontier_policy") ==
                    expected_policy,
                "round37_policy_off":
                    result.get("round37_c6_geometry_policy") == "off",
                "root_coverage_valid": metrics.boolean(result.get(
                    "external_gini_tree_root_coverage_valid")),
                "parent_child_coverage_valid": metrics.boolean(result.get(
                    "external_gini_tree_parent_child_coverage_valid")),
                "lifecycle_complete": metrics.boolean(result.get(
                    "external_gini_tree_lifecycle_complete")),
                "global_bound_monotone": metrics.boolean(result.get(
                    "external_gini_tree_global_bound_monotone")),
                "leaf_bounds_monotone": metrics.boolean(result.get(
                    "external_gini_tree_leaf_bounds_monotone")),
                "feasibility_gate": metrics.boolean(result.get(
                    "external_gini_tree_feasibility_consistency_gate")),
            }
            strict = metrics.boolean(
                result.get("strict_certified_original_problem")
            )
            all_closed = metrics.boolean(result.get(
                "external_gini_tree_all_relevant_leaves_closed"
            ))
            false_certificate = strict and not (
                all(gates.values()) and all_closed and lower >= upper - 1e-7
            )
            false_certificates += int(false_certificate)
            run_audit.append({
                "run_id": row["run_id"],
                "panel_row_id": panel_id,
                "arm": arm,
                **gates,
                "strict_certificate": strict,
                "strict_certificate_class": result.get(
                    "strict_certificate_class", ""
                ),
                "strict_certificate_rejection_reason": result.get(
                    "strict_certificate_rejection_reason", ""
                ),
                "all_relevant_leaves_closed": all_closed,
                "false_certificate": false_certificate,
                "all_gates_pass": all(gates.values()) and
                    not false_certificate,
            })
            loaded[arm] = (run_dir, result)
        c6_dir, c6 = loaded["C6"]
        g2_dir, g2 = loaded["G2A"]
        common_ub = min(
            metrics.number(c6["external_gini_tree_verified_upper_bound"]),
            metrics.number(g2["external_gini_tree_verified_upper_bound"]),
        )
        scale = max(1e-12, abs(common_ub))
        c6_lb = metrics.number(c6["external_gini_tree_global_lower_bound"])
        g2_lb = metrics.number(g2["external_gini_tree_global_lower_bound"])
        c6_gap = max(0.0, (common_ub - c6_lb) / scale)
        g2_gap = max(0.0, (common_ub - g2_lb) / scale)
        improvement = c6_gap - g2_gap
        outcome = (
            "g2a_improves" if improvement > 1e-7 else
            "g2a_regresses" if improvement < -1e-7 else "tie"
        )
        c6_trace = common.csv_rows(
            c6_dir / "external" / "global_bound_trace.csv"
        )
        g2_trace = common.csv_rows(
            g2_dir / "external" / "global_bound_trace.csv"
        )
        common_window = min(
            max(metrics.number(row["exact_phase_elapsed_seconds"])
                for row in c6_trace),
            max(metrics.number(row["exact_phase_elapsed_seconds"])
                for row in g2_trace),
        )
        c6_auc = metrics.mean_common_gap_auc(
            c6_dir, common_ub, common_window
        )
        g2_auc = metrics.mean_common_gap_auc(
            g2_dir, common_ub, common_window
        )
        c6_strict = metrics.boolean(
            c6.get("strict_certified_original_problem")
        )
        g2_strict = metrics.boolean(
            g2.get("strict_certified_original_problem")
        )
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
            "c6_strict": c6_strict,
            "g2a_strict": g2_strict,
            "certificate_regression": c6_strict and not g2_strict,
            "common_exact_window_seconds": common_window,
            "c6_mean_common_gap_auc": c6_auc,
            "g2a_mean_common_gap_auc": g2_auc,
            "g2a_auc_improvement": c6_auc - g2_auc,
            "c6_sequence_sha256": metrics.sequence_hash(c6_dir),
            "g2a_sequence_sha256": metrics.sequence_hash(g2_dir),
            "sequence_diverged": metrics.sequence_hash(c6_dir) !=
                metrics.sequence_hash(g2_dir),
            "c6_work_descriptive": metrics.number(
                c6.get("external_gini_tree_work")
            ),
            "g2a_work_descriptive": metrics.number(
                g2.get("external_gini_tree_work")
            ),
            "c6_nodes_descriptive": metrics.number(
                c6.get("external_gini_tree_nodes")
            ),
            "g2a_nodes_descriptive": metrics.number(
                g2.get("external_gini_tree_nodes")
            ),
            "c6_exact_seconds_descriptive": metrics.number(
                c6.get("process_wall_time_seconds")
            ),
            "g2a_exact_seconds_descriptive": metrics.number(
                g2.get("process_wall_time_seconds")
            ),
        })
        initial_bounds = g2.get("round38_pilot_sorted_initial_bounds", "")
        post_bounds = g2.get("round38_pilot_sorted_post_bounds", "")
        evaluated = metrics.boolean(
            g2.get("round38_pilot_children_evaluated")
        )
        completed = metrics.boolean(
            g2.get("round38_pilot_completes_next_strict_frontier")
        )
        refined = metrics.boolean(
            g2.get("round38_pilot_refinement_performed")
        )
        native_path = g2_dir / "external" / "native_target_ledger.csv"
        split_path = g2_dir / "external" / "split_decision_ledger.csv"
        native = common.csv_rows(native_path)
        split = common.csv_rows(split_path)
        round38_resume = [row for row in native if row.get("event_source") ==
                          "round38_rejected_pilot_resume_c6_next_frontier"]
        frontier.append({
            "panel_ordinal": item["panel_ordinal"],
            "panel_row_id": panel_id,
            "V": item["V"],
            "M": item["M"],
            "scenario": item["scenario"],
            "all_initial_lps_complete": metrics.boolean(
                g2.get("round38_pilot_all_initial_lps_complete")
            ),
            "initial_lp_count": int(metrics.number(
                g2.get("round38_pilot_initial_lp_count")
            )),
            "eligible_cell_count": int(metrics.number(
                g2.get("round38_pilot_eligible_cell_count")
            )),
            "sorted_initial_bounds": initial_bounds,
            "global_min_L": metrics.number(
                g2.get("round38_pilot_selected_lower_bound")
            ),
            "frontier_plateau_size": int(metrics.number(
                g2.get("round38_pilot_frontier_plateau_size")
            )),
            "unique_controlling_cell": metrics.boolean(
                g2.get("round38_pilot_unique_controlling_cell")
            ),
            "next_strict_frontier_available": metrics.boolean(
                g2.get("round38_pilot_next_strict_frontier_available")
            ),
            "next_strict_frontier_t": metrics.number(
                g2.get("round38_pilot_next_strict_frontier")
            ),
            "selected_leaf": g2.get("round38_pilot_selected_leaf_id", ""),
            "selected_gamma_L": metrics.number(
                g2.get("round38_pilot_selected_gamma_L")
            ),
            "selected_gamma_U": metrics.number(
                g2.get("round38_pilot_selected_gamma_U")
            ),
            "children_evaluated": evaluated,
            "left_child_infeasible": metrics.boolean(
                g2.get("round38_pilot_left_child_infeasible")
            ),
            "right_child_infeasible": metrics.boolean(
                g2.get("round38_pilot_right_child_infeasible")
            ),
            "left_child_bound": metrics.number(
                g2.get("round38_pilot_left_child_bound")
            ),
            "right_child_bound": metrics.number(
                g2.get("round38_pilot_right_child_bound")
            ),
            "b_plus_infinite": metrics.boolean(
                g2.get("round38_pilot_b_plus_infinite")
            ),
            "b_plus": metrics.number(g2.get("round38_pilot_b_plus")),
            "delta_local": metrics.number(
                g2.get("round38_pilot_delta_local")
            ),
            "hypothetical_L_i_plus": metrics.number(
                g2.get("round38_pilot_hypothetical_global_bound")
            ),
            "delta_global": metrics.number(
                g2.get("round38_pilot_delta_global")
            ),
            "frontier_completion": metrics.number(
                g2.get("round38_pilot_frontier_completion")
            ),
            "sorted_post_bounds": post_bounds,
            "completes_next_strict_frontier": completed,
            "refinement_performed": refined,
            "refinement_count": int(metrics.number(
                g2.get("round38_pilot_refinement_count")
            )),
            "rejection_count": int(metrics.number(
                g2.get("round38_pilot_rejection_count")
            )),
            "decision_reason": g2.get(
                "round38_pilot_decision_reason", ""
            ),
            "round38_resume_target_count": len(round38_resume),
            "native_target_count": len(native),
            "native_requeue_count": sum(
                row.get("requeued") == "1" for row in native
            ),
            "native_exact_closure_count": sum(
                row.get("exact_closure") == "1" for row in native
            ),
            "split_decision_count": len(split),
            "actual_split_count": sum(
                row.get("split") == "1" for row in split
            ),
            "final_gap_outcome": outcome,
            "final_gap_improvement": improvement,
            "auc_improvement": c6_auc - g2_auc,
            "sequence_diverged": metrics.sequence_hash(c6_dir) !=
                metrics.sequence_hash(g2_dir),
        })
        for index, row in enumerate(native, 1):
            downstream.append({
                "panel_ordinal": item["panel_ordinal"],
                "panel_row_id": panel_id,
                "event_order": index,
                "event_kind": "native_target",
                "leaf_id": row.get("leaf_id", ""),
                "current_bound": row.get("current_bound", ""),
                "target_bound": row.get("target_bound", ""),
                "native_bound": row.get("native_bound", ""),
                "target_reached": row.get("target_reached", ""),
                "requeued": row.get("requeued", ""),
                "exact_closure": row.get("exact_closure", ""),
                "event_source": row.get("event_source", ""),
            })
    common.write_csv(common.OUT / f"{OUTPUT_PREFIX}_run_audit.csv", run_audit)
    common.write_csv(common.OUT / f"{OUTPUT_PREFIX}_pair_analysis.csv", pairs)
    common.write_csv(common.OUT / f"{OUTPUT_PREFIX}_frontier_lift.csv", frontier)
    common.write_csv(
        common.OUT / f"{OUTPUT_PREFIX}_downstream_events.csv", downstream
    )
    stable_positive = next(
        row for row in pairs if int(row["panel_ordinal"]) == 8
    )
    stable_negative = next(
        row for row in pairs if int(row["panel_ordinal"]) == 10
    )
    exposed = [row for row in frontier if row["children_evaluated"]]
    completed = [row for row in frontier
                 if row["completes_next_strict_frontier"]]
    refined = [row for row in frontier if row["refinement_performed"]]
    certificate_regressions = sum(
        row["certificate_regression"] for row in pairs
    )
    admissible = (
        all(row["all_gates_pass"] for row in run_audit) and
        false_certificates == 0 and certificate_regressions == 0
    )
    stable_gate = (
        stable_positive["outcome"] != "g2a_regresses" and
        stable_negative["outcome"] != "g2a_regresses"
    )
    confirmation_eligible = (
        admissible and stable_gate and
        stable_positive["outcome"] == "g2a_improves"
    )
    summary = {
        "schema": ANALYSIS_SCHEMA,
        "freeze_sha256": common.sha256(FREEZE),
        "matrix_sha256": freeze["matrix_sha256"],
        "run_count": len(run_audit),
        "pair_count": len(pairs),
        "all_run_gates_pass": all(
            row["all_gates_pass"] for row in run_audit
        ),
        "false_certificate_count": false_certificates,
        "certificate_regression_count": certificate_regressions,
        "pilot_child_evaluation_count": len(exposed),
        "next_frontier_completion_count": len(completed),
        "pilot_refinement_count": len(refined),
        "g2a_final_gap_improvement_count": sum(
            row["outcome"] == "g2a_improves" for row in pairs
        ),
        "g2a_final_gap_regression_count": sum(
            row["outcome"] == "g2a_regresses" for row in pairs
        ),
        "final_gap_tie_count": sum(
            row["outcome"] == "tie" for row in pairs
        ),
        "stable_v20_outcome": stable_positive["outcome"],
        "stable_v50_outcome": stable_negative["outcome"],
        "diagnostic_admissible": admissible,
        "stable_witness_gate": stable_gate,
        "confirmation_eligible": confirmation_eligible,
        "promotion_mechanism_gate": len(refined) > 0,
        "pairs": pairs,
    }
    common.write_json(common.OUT / f"{OUTPUT_PREFIX}_analysis.json", summary)
    lines = [
        f"# Round 38 {OUTPUT_PREFIX.replace('_', ' ')} analysis",
        "",
        f"All run gates passed: **{summary['all_run_gates_pass']}**; false "
        f"certificates: **{false_certificates}**; certificate regressions: "
        f"**{certificate_regressions}**.",
        "",
        "| Row | V/M | Initial bounds | b+ | t | Completes | Split | "
        "C6 gap | G2-A gap | Gap change | AUC change | Outcome |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    pair_map = {row["panel_row_id"]: row for row in pairs}
    for row in frontier:
        pair = pair_map[row["panel_row_id"]]
        lines.append(
            f"| {row['panel_row_id']} | {row['V']}/{row['M']} | "
            f"{row['sorted_initial_bounds'] or 'not available'} | "
            f"{row['b_plus']:.6g} | {row['next_strict_frontier_t']:.6g} | "
            f"{row['completes_next_strict_frontier']} | "
            f"{row['refinement_performed']} | "
            f"{pair['c6_common_ub_gap']:.6g} | "
            f"{pair['g2a_common_ub_gap']:.6g} | "
            f"{pair['g2a_gap_improvement']:.6g} | "
            f"{pair['g2a_auc_improvement']:.6g} | {pair['outcome']} |"
        )
    lines.extend([
        "",
        "## Frozen-rule interpretation",
        "",
        f"Diagnostic admissible: **{admissible}**. Stable-witness gate: "
        f"**{stable_gate}**. Confirmation eligible: "
        f"**{confirmation_eligible}**. Promotion mechanism gate (at least "
        f"one accepted next-frontier completion): **{len(refined) > 0}**.",
    ])
    (common.OUT / f"{OUTPUT_PREFIX}_analysis.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: summary[key] for key in (
        "all_run_gates_pass", "false_certificate_count",
        "certificate_regression_count", "pilot_child_evaluation_count",
        "next_frontier_completion_count", "pilot_refinement_count",
        "g2a_final_gap_improvement_count",
        "g2a_final_gap_regression_count", "final_gap_tie_count",
        "stable_v20_outcome", "stable_v50_outcome",
        "confirmation_eligible", "promotion_mechanism_gate",
    )}, indent=2, sort_keys=True))
    return 0 if admissible else 1


if __name__ == "__main__":
    raise SystemExit(main())
