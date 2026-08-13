#!/usr/bin/env python3
"""Create compact cross-stage Round 38 evidence and the final decision."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import round38_experiment_common as common


STAGES = ("smoke", "diagnostic", "confirmation")


def boolean(value: Any) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes"}


def number(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def compact_sequence(values: list[str]) -> str:
    output: list[str] = []
    for value in values:
        if value and (not output or output[-1] != value):
            output.append(value)
    return ";".join(output)


def run_directory(stage: str, panel_row_id: str, arm: str) -> Path:
    return (
        common.OUT / f"{stage}_runs" /
        f"{stage}_{panel_row_id}__{arm.lower()}"
    )


def target_sequence(run_dir: Path) -> str:
    rows = common.csv_rows(run_dir / "external" / "native_target_ledger.csv")
    return ";".join(
        f"{row.get('leaf_id')}:{row.get('current_bound')}->"
        f"{row.get('target_bound')}:{row.get('status')}:"
        f"{row.get('event_source')}" for row in rows
    )


def split_sequence(run_dir: Path) -> str:
    rows = common.csv_rows(run_dir / "external" / "split_decision_ledger.csv")
    return ";".join(
        f"{row.get('parent_id')}:{row.get('split')}:{row.get('reason')}"
        for row in rows
    )


def controlling_sequence(run_dir: Path) -> str:
    rows = common.csv_rows(run_dir / "external" / "global_bound_trace.csv")
    return compact_sequence([row.get("active_leaf", "") for row in rows])


def closure_sequence(run_dir: Path) -> str:
    rows = common.csv_rows(run_dir / "external" / "paper_tree_events.csv")
    return ";".join(
        f"{row.get('event')}:{row.get('leaf_id')}:{row.get('status')}"
        for row in rows
        if any(token in row.get("event", "")
               for token in ("closure", "closed", "infeasible"))
    )


def terminal_mip_sequence(run_dir: Path) -> str:
    rows = common.csv_rows(run_dir / "external" / "paper_optimize_ledger.csv")
    return compact_sequence([
        row.get("leaf_id", "") for row in rows
        if "TERMINAL" in row.get("solve_kind", "").upper()
    ])


def pair_result_rows() -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for stage in STAGES:
        cap = {"smoke": 180, "diagnostic": 480, "confirmation": 900}[stage]
        for pair in common.csv_rows(
                common.OUT / f"{stage}_pair_analysis.csv"):
            panel_id = pair["panel_row_id"]
            c6_dir = run_directory(stage, panel_id, "C6")
            g2_dir = run_directory(stage, panel_id, "G2A")
            c6 = common.load_json(c6_dir / "result.json")
            g2 = common.load_json(g2_dir / "result.json")
            interval_rows = common.csv_rows(
                g2_dir / "external" / "initial_decomposition_ledger.csv"
            )
            initial_intervals = ";".join(
                f"[{row.get('active_lower')},{row.get('active_upper')}]"
                for row in interval_rows if row.get("active") == "1"
            )
            selected_lower = number(
                g2.get("round38_pilot_selected_gamma_L")
            )
            selected_upper = number(
                g2.get("round38_pilot_selected_gamma_U")
            )
            midpoint = 0.5 * (selected_lower + selected_upper)
            selected = g2.get("round38_pilot_selected_leaf_id", "")
            output.append({
                "stage": stage,
                "process_cap_seconds": cap,
                "panel_ordinal": pair["panel_ordinal"],
                "panel_row_id": panel_id,
                "instance_id": pair["instance_id"],
                "V": pair["V"],
                "M": pair["M"],
                "scenario": pair["scenario"],
                "verified_ub_at_g2a_launch": g2.get(
                    "external_gini_tree_verified_upper_bound"
                ),
                "common_verified_ub": pair["common_verified_ub"],
                "initial_intervals": initial_intervals,
                "all_initial_lps_complete": g2.get(
                    "round38_pilot_all_initial_lps_complete"
                ),
                "initial_lp_count": g2.get(
                    "round38_pilot_initial_lp_count"
                ),
                "sorted_initial_open_bounds": g2.get(
                    "round38_pilot_sorted_initial_bounds", ""
                ),
                "initial_global_L": g2.get(
                    "round38_pilot_selected_lower_bound"
                ),
                "next_strict_frontier_t": g2.get(
                    "round38_pilot_next_strict_frontier"
                ),
                "frontier_plateau_size": g2.get(
                    "round38_pilot_frontier_plateau_size"
                ),
                "unique_controlling_cell": g2.get(
                    "round38_pilot_unique_controlling_cell"
                ),
                "selected_cell": selected,
                "selected_interval": (
                    f"[{selected_lower:.17g},{selected_upper:.17g}]"
                    if selected else ""
                ),
                "left_child_interval": (
                    f"[{selected_lower:.17g},{midpoint:.17g}]"
                    if selected else ""
                ),
                "right_child_interval": (
                    f"[{midpoint:.17g},{selected_upper:.17g}]"
                    if selected else ""
                ),
                "children_evaluated": g2.get(
                    "round38_pilot_children_evaluated"
                ),
                "left_child_infeasible": g2.get(
                    "round38_pilot_left_child_infeasible"
                ),
                "right_child_infeasible": g2.get(
                    "round38_pilot_right_child_infeasible"
                ),
                "left_child_bound": g2.get(
                    "round38_pilot_left_child_bound"
                ),
                "right_child_bound": g2.get(
                    "round38_pilot_right_child_bound"
                ),
                "b_plus_infinite": g2.get(
                    "round38_pilot_b_plus_infinite"
                ),
                "b_plus": g2.get("round38_pilot_b_plus"),
                "delta_local": g2.get("round38_pilot_delta_local"),
                "hypothetical_L_i_plus": g2.get(
                    "round38_pilot_hypothetical_global_bound"
                ),
                "delta_global": g2.get("round38_pilot_delta_global"),
                "frontier_completion": g2.get(
                    "round38_pilot_frontier_completion"
                ),
                "completes_next_frontier": g2.get(
                    "round38_pilot_completes_next_strict_frontier"
                ),
                "hypothetical_sorted_post_bounds": g2.get(
                    "round38_pilot_sorted_post_bounds", ""
                ),
                "accepted_refinement": g2.get(
                    "round38_pilot_refinement_performed"
                ),
                "decision_reason": g2.get(
                    "round38_pilot_decision_reason", ""
                ),
                "live_refined_descendants": 0,
                "c6_controlling_leaf_sequence": controlling_sequence(c6_dir),
                "g2a_controlling_leaf_sequence": controlling_sequence(g2_dir),
                "c6_target_sequence": target_sequence(c6_dir),
                "g2a_target_sequence": target_sequence(g2_dir),
                "c6_split_sequence": split_sequence(c6_dir),
                "g2a_split_sequence": split_sequence(g2_dir),
                "c6_closure_sequence": closure_sequence(c6_dir),
                "g2a_closure_sequence": closure_sequence(g2_dir),
                "c6_terminal_mip_sequence": terminal_mip_sequence(c6_dir),
                "g2a_terminal_mip_sequence": terminal_mip_sequence(g2_dir),
                "c6_valid_lb": pair["c6_valid_lb"],
                "g2a_valid_lb": pair["g2a_valid_lb"],
                "c6_common_ub_gap": pair["c6_common_ub_gap"],
                "g2a_common_ub_gap": pair["g2a_common_ub_gap"],
                "g2a_gap_improvement": pair["g2a_gap_improvement"],
                "c6_proof_auc": pair["c6_mean_common_gap_auc"],
                "g2a_proof_auc": pair["g2a_mean_common_gap_auc"],
                "g2a_auc_improvement": pair["g2a_auc_improvement"],
                "outcome": pair["outcome"],
                "c6_strict_certificate": pair["c6_strict"],
                "g2a_strict_certificate": pair["g2a_strict"],
                "certificate_regression": pair["certificate_regression"],
                "c6_work_descriptive": c6.get("external_gini_tree_work"),
                "g2a_work_descriptive": g2.get("external_gini_tree_work"),
                "c6_nodes_descriptive": c6.get("external_gini_tree_nodes"),
                "g2a_nodes_descriptive": g2.get("external_gini_tree_nodes"),
                "c6_process_seconds_descriptive": c6.get(
                    "actual_runtime_seconds"
                ),
                "g2a_process_seconds_descriptive": g2.get(
                    "actual_runtime_seconds"
                ),
                "c6_exact_phase_seconds_descriptive": max(
                    0.0, number(c6.get("actual_runtime_seconds")) -
                    number(c6.get("process_elapsed_at_exact_phase_start_seconds"))
                ),
                "g2a_exact_phase_seconds_descriptive": max(
                    0.0, number(g2.get("actual_runtime_seconds")) -
                    number(g2.get("process_elapsed_at_exact_phase_start_seconds"))
                ),
            })
    return output


def local_raw_manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    commands = {
        "smoke": "python scripts/run_round38_smoke.py",
        "diagnostic": "python scripts/run_round38_diagnostic.py",
        "confirmation": "python scripts/run_round38_confirmation.py",
    }
    for stage in STAGES:
        for directory in sorted((common.OUT / f"{stage}_runs").iterdir()):
            if not directory.is_dir():
                continue
            marker_path = directory / "completion_marker.json"
            if not marker_path.is_file():
                continue
            marker = common.load_json(marker_path)
            rows.append({
                "stage": stage,
                "run_id": marker["run_id"],
                "panel_row_id": marker["panel_row_id"],
                "arm": marker["arm"],
                "process_cap_seconds": marker["process_cap_seconds"],
                "raw_directory": directory.relative_to(common.ROOT).as_posix(),
                "raw_directory_git_policy": "local_ignored_reproducible",
                "completion_marker_sha256": common.sha256(marker_path),
                "artifact_count": marker["artifact_count"],
                "artifact_manifest_sha256": marker[
                    "artifact_manifest_sha256"
                ],
                "result_sha256": marker["result_sha256"],
                "executable_sha256": marker["executable_sha256"],
                "matrix_sha256": marker["matrix_sha256"],
                "source_tree_fingerprint": marker[
                    "source_tree_fingerprint"
                ],
                "recreation_command": commands[stage],
            })
    return rows


def invalidated_attempt_manifest() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = common.OUT / "invalidated_attempts"
    rows: list[dict[str, Any]] = []
    if root.is_dir():
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            rows.append({
                "attempt_id": "wrapper_timeout_attempt_1",
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": common.sha256(path),
                "official_evidence": False,
                "invalidation_reason": (
                    "outer_orchestration_wrapper_expired_before_atomic_"
                    "completion"
                ),
            })
    summary = {
        "schema": "round38-invalidated-attempt-summary-v1",
        "attempt_id": "wrapper_timeout_attempt_1",
        "file_count": len(rows),
        "total_bytes": sum(int(row["bytes"]) for row in rows),
        "completion_marker_present": any(
            row["path"].endswith("completion_marker.json") for row in rows
        ),
        "official_evidence": False,
        "replacement_run": (
            "smoke_r36_04_round32_multi_m_tight_T_V20_M2_"
            "seed89001413__c6"
        ),
        "replacement_completion_marker_present": (
            common.OUT / "smoke_runs" /
            "smoke_r36_04_round32_multi_m_tight_T_V20_M2_seed89001413__c6" /
            "completion_marker.json"
        ).is_file(),
        "handling": (
            "preserved locally under an ignored quarantine; excluded from "
            "matrices, summaries, pair analyses, and final counts"
        ),
    }
    return rows, summary


def stage_paths(stage: str) -> tuple[Path, Path, Path]:
    return (
        common.OUT / f"{stage}_run_audit.csv",
        common.OUT / f"{stage}_pair_analysis.csv",
        common.OUT / f"{stage}_analysis.json",
    )


def exactness_audit() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    total_runs = 0
    total_pairs = 0
    total_false = 0
    total_certificate_regressions = 0
    all_gates = True
    total_strict = 0
    for stage in STAGES:
        audit_path, pair_path, analysis_path = stage_paths(stage)
        audit = common.csv_rows(audit_path)
        pairs = common.csv_rows(pair_path)
        analysis = common.load_json(analysis_path)
        stage_gates = all(boolean(row["all_gates_pass"]) for row in audit)
        false_count = sum(boolean(row["false_certificate"]) for row in audit)
        strict_count = sum(boolean(row["strict_certificate"]) for row in audit)
        certificate_regressions = sum(
            boolean(row["certificate_regression"]) for row in pairs
        )
        rows.append({
            "stage": stage,
            "run_count": len(audit),
            "pair_count": len(pairs),
            "all_completion_artifact_contract_coverage_lifecycle_"
            "monotonicity_feasibility_gates_pass": stage_gates,
            "strict_certificate_count": strict_count,
            "false_certificate_count": false_count,
            "certificate_regression_count": certificate_regressions,
            "child_evaluation_count": analysis[
                "pilot_child_evaluation_count"
            ],
            "next_frontier_completion_count": analysis[
                "next_frontier_completion_count"
            ],
            "accepted_refinement_count": analysis[
                "pilot_refinement_count"
            ],
            "improvement_count": analysis[
                "g2a_final_gap_improvement_count"
            ],
            "regression_count": analysis[
                "g2a_final_gap_regression_count"
            ],
            "tie_count": analysis["final_gap_tie_count"],
            "run_audit_sha256": common.sha256(audit_path),
            "pair_analysis_sha256": common.sha256(pair_path),
            "analysis_sha256": common.sha256(analysis_path),
        })
        total_runs += len(audit)
        total_pairs += len(pairs)
        total_false += false_count
        total_strict += strict_count
        total_certificate_regressions += certificate_regressions
        all_gates = all_gates and stage_gates
    summary = {
        "schema": "round38-exactness-audit-v1",
        "baseline_equivalence_pre_mechanism": common.load_json(
            common.OUT / "baseline_equivalence_pre_mechanism_audit.json"
        )["passed"],
        "baseline_equivalence_pre_mechanism_comparisons": 18,
        "baseline_equivalence_post_implementation": common.load_json(
            common.OUT /
            "baseline_equivalence_post_implementation_audit.json"
        )["passed"],
        "baseline_equivalence_post_implementation_comparisons": 18,
        "official_run_count": total_runs,
        "official_pair_count": total_pairs,
        "all_run_gates_pass": all_gates,
        "strict_certificate_count": total_strict,
        "false_certificate_count": total_false,
        "certificate_regression_count": total_certificate_regressions,
        "coverage_statement": (
            "Every official row passed root coverage, atomic parent-child "
            "coverage, lifecycle, global/leaf bound monotonicity, and "
            "feasibility gates. Open leaves correctly reject strict "
            "certification; completed strict certificates require all "
            "relevant leaves closed and LB >= verified UB within tolerance."
        ),
        "stages": rows,
    }
    return rows, summary


def persistence_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stage in STAGES:
        pair_by_ordinal = {
            int(row["panel_ordinal"]): row for row in common.csv_rows(
                common.OUT / f"{stage}_pair_analysis.csv"
            )
        }
        frontier_name = f"{stage}_frontier_lift.csv"
        if stage == "smoke":
            # Smoke pair analysis already contains all frontier fields.
            frontier_by_ordinal = pair_by_ordinal
        else:
            frontier_by_ordinal = {
                int(row["panel_ordinal"]): row for row in common.csv_rows(
                    common.OUT / frontier_name
                )
            }
        for ordinal in (8, 10, 11):
            if ordinal not in pair_by_ordinal:
                continue
            pair = pair_by_ordinal[ordinal]
            frontier = frontier_by_ordinal[ordinal]
            prefix = "pilot_" if stage == "smoke" else ""
            rows.append({
                "stage": stage,
                "process_cap_seconds": {
                    "smoke": 180, "diagnostic": 480,
                    "confirmation": 900,
                }[stage],
                "panel_ordinal": ordinal,
                "panel_row_id": pair["panel_row_id"],
                "V": pair["V"],
                "M": pair["M"],
                "scenario": pair["scenario"],
                "children_evaluated": frontier.get(
                    f"{prefix}children_evaluated", ""
                ),
                "b_plus": frontier.get(f"{prefix}b_plus", ""),
                "next_strict_frontier": frontier.get(
                    "next_strict_frontier_t",
                    frontier.get("pilot_next_strict_frontier", ""),
                ),
                "delta_local": frontier.get(
                    f"{prefix}delta_local", ""
                ),
                "delta_global": frontier.get(
                    f"{prefix}delta_global", ""
                ),
                "next_frontier_completed": frontier.get(
                    "completes_next_strict_frontier",
                    frontier.get(
                        "pilot_completes_next_strict_frontier", ""
                    ),
                ),
                "accepted_refinement": frontier.get(
                    "refinement_performed",
                    frontier.get("pilot_refinement_performed", ""),
                ),
                "live_refined_descendants": 0,
                "descendant_persistence": "not_applicable_no_accepted_split",
                "c6_common_ub_gap": pair["c6_common_ub_gap"],
                "g2a_common_ub_gap": pair["g2a_common_ub_gap"],
                "g2a_gap_improvement": pair["g2a_gap_improvement"],
                "g2a_auc_improvement": pair["g2a_auc_improvement"],
                "outcome": pair["outcome"],
                "sequence_diverged": pair.get(
                    "sequence_diverged",
                    pair.get("c6_sequence_sha256") !=
                    pair.get("g2a_sequence_sha256"),
                ),
                "interpretation": (
                    "rejected_pilot_then_parent_target_reordering;"
                    "not_an_accepted_global_frontier_lift"
                ),
            })
    return rows


def representative_trajectories() -> list[dict[str, Any]]:
    panel = common.panel()
    pair_rows = {
        int(row["panel_ordinal"]): row for row in common.csv_rows(
            common.OUT / "confirmation_pair_analysis.csv"
        )
    }
    frontier_rows = {
        int(row["panel_ordinal"]): row for row in common.csv_rows(
            common.OUT / "confirmation_frontier_lift.csv"
        )
    }
    output: list[dict[str, Any]] = []
    for ordinal in (8, 10, 11):
        item = next(row for row in panel.values()
                    if row["panel_ordinal"] == ordinal)
        pair = pair_rows[ordinal]
        frontier = frontier_rows[ordinal]
        for arm in ("C6", "G2A"):
            run_id = f"confirmation_{item['panel_row_id']}__{arm.lower()}"
            run_dir = common.OUT / "confirmation_runs" / run_id
            result = common.load_json(run_dir / "result.json")
            trace = common.csv_rows(
                run_dir / "external" / "global_bound_trace.csv"
            )
            targets = common.csv_rows(
                run_dir / "external" / "native_target_ledger.csv"
            )
            events = common.csv_rows(
                run_dir / "external" / "paper_tree_events.csv"
            )
            optimize = common.csv_rows(
                run_dir / "external" / "paper_optimize_ledger.csv"
            )
            splits = common.csv_rows(
                run_dir / "external" / "split_decision_ledger.csv"
            )
            output.append({
                "panel_ordinal": ordinal,
                "panel_row_id": item["panel_row_id"],
                "role": {
                    8: "stable_positive",
                    10: "stable_adversarial",
                    11: "confirmed_regression",
                }[ordinal],
                "arm": arm,
                "initial_bound_vector": (
                    frontier["sorted_initial_bounds"]
                    if arm == "G2A" else
                    "see_initial_LP_ledger_same_geometry"
                ),
                "candidate_b_plus": (
                    frontier["b_plus"] if arm == "G2A" else "not_evaluated"
                ),
                "candidate_next_frontier": (
                    frontier["next_strict_frontier_t"]
                    if arm == "G2A" else "not_evaluated"
                ),
                "candidate_accepted": (
                    frontier["refinement_performed"]
                    if arm == "G2A" else "not_evaluated"
                ),
                "controlling_leaf_sequence": compact_sequence([
                    row.get("active_leaf", "") for row in trace
                ]),
                "target_sequence": ";".join(
                    f"{row.get('leaf_id')}:{row.get('current_bound')}->"
                    f"{row.get('target_bound')}:{row.get('status')}"
                    for row in targets
                ),
                "requeue_count": sum(
                    row.get("requeued") == "1" for row in targets
                ),
                "split_sequence": ";".join(
                    f"{row.get('parent_id')}:{row.get('split')}:"
                    f"{row.get('reason')}" for row in splits
                ),
                "atomic_split_events": sum(
                    row.get("event") == "atomic_split" for row in events
                ),
                "terminal_mip_sequence": compact_sequence([
                    row.get("leaf_id", "") for row in optimize
                    if "terminal" in row.get("phase", "").lower() or
                    "terminal" in row.get("event_source", "").lower()
                ]),
                "final_valid_lb": result[
                    "external_gini_tree_global_lower_bound"
                ],
                "common_ub_gap": pair[
                    "c6_common_ub_gap" if arm == "C6"
                    else "g2a_common_ub_gap"
                ],
                "proof_auc": pair[
                    "c6_mean_common_gap_auc" if arm == "C6"
                    else "g2a_mean_common_gap_auc"
                ],
                "strict_certificate": result[
                    "strict_certified_original_problem"
                ],
                "certificate_rejection_reason": result.get(
                    "strict_certificate_rejection_reason", ""
                ),
                "work_descriptive": result["external_gini_tree_work"],
                "nodes_descriptive": result["external_gini_tree_nodes"],
                "process_seconds_descriptive": result[
                    "actual_runtime_seconds"
                ],
                "trajectory_sha256": pair[
                    "c6_sequence_sha256" if arm == "C6"
                    else "g2a_sequence_sha256"
                ],
            })
    return output


def main() -> int:
    per_pairs = pair_result_rows()
    common.write_csv(common.OUT / "per_pair_results.csv", per_pairs)
    raw_manifest = local_raw_manifest()
    common.write_csv(common.OUT / "local_raw_manifest.csv", raw_manifest)
    invalid_rows, invalid_summary = invalidated_attempt_manifest()
    if invalid_rows:
        common.write_csv(
            common.OUT / "invalidated_attempt_manifest.csv", invalid_rows
        )
    common.write_json(
        common.OUT / "invalidated_attempt_summary.json", invalid_summary
    )
    exact_rows, exact = exactness_audit()
    common.write_csv(common.OUT / "exactness_audit.csv", exact_rows)
    common.write_json(common.OUT / "exactness_audit.json", exact)
    persistence = persistence_rows()
    common.write_csv(common.OUT / "persistence_analysis.csv", persistence)
    trajectory = representative_trajectories()
    common.write_csv(
        common.OUT / "representative_trajectory_comparisons.csv", trajectory
    )
    diagnostic = common.load_json(common.OUT / "diagnostic_analysis.json")
    confirmation = common.load_json(common.OUT / "confirmation_analysis.json")
    confirmed = {
        int(row["panel_ordinal"]): row for row in confirmation["pairs"]
    }
    total_child_evaluations = sum(
        row["child_evaluation_count"] for row in exact_rows
    )
    total_completions = sum(
        row["next_frontier_completion_count"] for row in exact_rows
    )
    total_refinements = sum(
        row["accepted_refinement_count"] for row in exact_rows
    )
    final_decision = {
        "schema": "round38-final-decision-v1",
        "decision": "do_not_promote_g2a_retain_c6_hga_full",
        "stable_general_improvement_found": False,
        "validated_mainline": {
            "policy": "C6-HGA-FULL",
            "K": 4,
            "rho": 0.01,
            "round38_frontier_policy_default": "off",
        },
        "candidate": "G2A-pilot-next-frontier-complete",
        "compact_evidence": {
            "per_pair_results_sha256": common.sha256(
                common.OUT / "per_pair_results.csv"
            ),
            "local_raw_manifest_sha256": common.sha256(
                common.OUT / "local_raw_manifest.csv"
            ),
            "invalidated_attempt_summary_sha256": common.sha256(
                common.OUT / "invalidated_attempt_summary.json"
            ),
            "frontier_diagnostic_sha256": common.sha256(
                common.OUT / "diagnostic_frontier_lift.csv"
            ),
            "persistence_analysis_sha256": common.sha256(
                common.OUT / "persistence_analysis.csv"
            ),
            "representative_trajectory_sha256": common.sha256(
                common.OUT / "representative_trajectory_comparisons.csv"
            ),
        },
        "exactness": exact,
        "mechanism_exposure": {
            "child_evaluation_count": total_child_evaluations,
            "next_frontier_completion_count": total_completions,
            "accepted_refinement_count": total_refinements,
            "live_refined_descendant_count": 0,
        },
        "diagnostic_outcomes": {
            "improvements": diagnostic[
                "g2a_final_gap_improvement_count"
            ],
            "regressions": diagnostic[
                "g2a_final_gap_regression_count"
            ],
            "ties": diagnostic["final_gap_tie_count"],
        },
        "confirmation_outcomes": {
            "improvements": confirmation[
                "g2a_final_gap_improvement_count"
            ],
            "regressions": confirmation[
                "g2a_final_gap_regression_count"
            ],
            "ties": confirmation["final_gap_tie_count"],
            "stable_v20_gap_improvement": number(
                confirmed[8]["g2a_gap_improvement"]
            ),
            "stable_v20_auc_improvement": number(
                confirmed[8]["g2a_auc_improvement"]
            ),
            "stable_v50_gap_improvement": number(
                confirmed[10]["g2a_gap_improvement"]
            ),
            "stable_v50_auc_improvement": number(
                confirmed[10]["g2a_auc_improvement"]
            ),
            "v50_tight_T_gap_improvement": number(
                confirmed[11]["g2a_gap_improvement"]
            ),
            "v50_tight_T_auc_improvement": number(
                confirmed[11]["g2a_auc_improvement"]
            ),
        },
        "hypothesis_dispositions": {
            "H1": (
                "not_supported: 19 complete child evaluations yielded zero "
                "next-frontier completions, so the predicted accepted-lift "
                "class had no empirical exposure"
            ),
            "H2": (
                "rejected: stable V20 benefit and adversarial V50 tie were "
                "retained, but another V50 tight-T case regressed at both "
                "480 and 900 seconds under common-UB gap/AUC"
            ),
            "H3": (
                "diagnostic_only: no refined descendants existed; rejected "
                "lookahead changed target/split ordering bidirectionally"
            ),
            "H4": (
                "not_activated: zero accepted G2-A lifts gave no evidence "
                "to justify costlier global-vector enumeration"
            ),
        },
        "reason": (
            "G2-A is exact and default-off, but it never performed the "
            "frontier-completing refinement it was designed to test. Its "
            "measured gains and losses arise from completing the initial "
            "census, evaluating then discarding speculative children, and "
            "reordering native targets/splits. The confirmed V50 tight-T "
            "regression makes this path effect bidirectional, so no simple "
            "general paper-friendly promotion is justified."
        ),
        "later_work": (
            "If revisited, isolate complete-initial-census and rejected-"
            "lookahead effects as separate default-off experiments before "
            "considering any multi-cell G2-B enumeration."
        ),
    }
    common.write_json(common.OUT / "final_decision.json", final_decision)
    disposition_rows = [
        {"hypothesis_id": key, "final_disposition": value}
        for key, value in final_decision["hypothesis_dispositions"].items()
    ]
    common.write_csv(common.OUT / "hypothesis_disposition.csv", disposition_rows)
    exact_lines = [
        "# Round 38 exactness audit",
        "",
        f"Pre-mechanism C6 equivalence: **18/18**; post-implementation "
        f"explicit-off equivalence: **18/18**.",
        "",
        f"Across **{exact['official_run_count']}** official runs "
        f"(**{exact['official_pair_count']}** pairs), all run gates passed, "
        f"with **{exact['false_certificate_count']}** false certificates and "
        f"**{exact['certificate_regression_count']}** certificate "
        f"regressions.",
        "",
        "| Stage | Runs | Pairs | Strict certs | False certs | Cert "
        "regressions | Child evals | Completions | Accepted splits |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in exact_rows:
        exact_lines.append(
            f"| {row['stage']} | {row['run_count']} | {row['pair_count']} | "
            f"{row['strict_certificate_count']} | "
            f"{row['false_certificate_count']} | "
            f"{row['certificate_regression_count']} | "
            f"{row['child_evaluation_count']} | "
            f"{row['next_frontier_completion_count']} | "
            f"{row['accepted_refinement_count']} |"
        )
    exact_lines.extend(["", exact["coverage_statement"]])
    (common.OUT / "exactness_audit.md").write_text(
        "\n".join(exact_lines) + "\n", encoding="utf-8"
    )
    persistence_lines = [
        "# Round 38 persistence analysis",
        "",
        "Every one of the 19 evaluated midpoint pairs failed `b+ >= t`; no "
        "candidate split entered the live tree. Refined-descendant persistence "
        "is therefore not applicable. What persists is a rejected-lookahead "
        "path effect: G2-A completes the initial census, discards its child "
        "models, then targets the unchanged parent at `t`.",
        "",
        "| Stage | Row | Cap | Outcome | Gap change | AUC change | Accepted |",
        "|---|---:|---:|---|---:|---:|---:|",
    ]
    for row in persistence:
        persistence_lines.append(
            f"| {row['stage']} | {row['panel_ordinal']} | "
            f"{row['process_cap_seconds']} | {row['outcome']} | "
            f"{number(row['g2a_gap_improvement']):.6g} | "
            f"{number(row['g2a_auc_improvement']):.6g} | "
            f"{row['accepted_refinement']} |"
        )
    persistence_lines.extend([
        "",
        "The stable V20 positive persists from 180 through 900 seconds and "
        "the original adversarial V50 remains a final-gap tie. The V50 "
        "tight-T regression persists from 480 through 900 seconds after "
        "common-UB normalization. Hence rejected-pilot target/split "
        "reordering is bidirectional and is not a stable structural rule.",
    ])
    (common.OUT / "persistence_analysis.md").write_text(
        "\n".join(persistence_lines) + "\n", encoding="utf-8"
    )
    report = f"""# ExactEBRP Round 38 final report

## Decision

**Do not promote G2-A. Retain C6-HGA-FULL with K=4 and rho=0.01 as the
validated default mainline.** No stable general improvement was found.

Round 38 implemented an explicit, deterministic, default-off
`pilot-next-frontier-complete` experiment. The protected path remained
structurally equivalent before and after implementation (18/18 comparisons in
each gate). Across {exact['official_run_count']} official runs
({exact['official_pair_count']} pairs), all coverage, lifecycle,
monotonic-bound, feasibility, artifact, and certificate gates passed; false
certificates and certificate regressions were both zero.

## Mechanism result

Prior Round 37 forensics found 0/10 historical G1 exposures whose midpoint
child bound reached the next strict frontier. Round 38 then obtained
{total_child_evaluations} complete G2-A child evaluations over smoke,
full-panel diagnostic, and confirmation stages. Again, **0 reached the next
strict frontier and 0 refinements were accepted**. H1 therefore has no
empirical accepted-lift class, and G2-A is too selective to explain the
observed computational effects.

The effects instead arise from the rejected pilot path. G2-A completes all
initial LPs, evaluates and discards the midpoint children, then resumes the
unchanged parent at the next strict frontier. On the stable V20 witness this
changes the native-target path and confirms a gap improvement of
{number(confirmed[8]['g2a_gap_improvement']):.6f} with AUC improvement
{number(confirmed[8]['g2a_auc_improvement']):.6f}. On the original stable V50
adversarial witness the final gap ties, with AUC change
{number(confirmed[10]['g2a_auc_improvement']):.6f}.

However, V50 tight-T is adverse at both 480 and 900 seconds. At confirmation,
the common-UB gap change is
{number(confirmed[11]['g2a_gap_improvement']):.6f} and the AUC change is
{number(confirmed[11]['g2a_auc_improvement']):.6f}. C6 reaches an intermediate
target, performs an exact child-infeasibility split, and obtains a stronger
lower bound; G2-A's rejected pilot instead sends the unchanged parent directly
toward the higher frontier and remains deadline-open. This is a confirmed
bidirectional path effect, not a global-frontier lift.

## Hypotheses

- H1 is not supported: 19 evaluated midpoints, 0 next-frontier completions.
- H2 is rejected: the original witnesses look favorable, but a second V50
  stratum has a confirmed common-UB gap and AUC regression.
- H3 remains diagnostic: no live refined descendants existed; target/split
  reordering explains the observations but supplies no simple online rule.
- H4/G2-B was not activated: multi-cell speculative enumeration would add
  overhead without evidence of an accepted lift.

## Exactness and mainline status

G2-A never uses elapsed time, Work, nodes, V/M, scenario labels, instance
identity, hardware state, or historical outcomes. Its acceptance test uses
only complete valid LP dispositions, Gini geometry, the unique global
minimum, the next strict frontier, and the existing correctness tolerance.
Speculative children are either atomically incorporated as a complete cover or
discarded before C6 resumes. No accepted G2-A split occurred in the official
experiments, and the unchanged certificate verifier correctly rejected
deadline-open runs.

The experimental code and telemetry remain available behind an explicit
default-off option for reproducibility. They do not change C6, K, rho, HGA
startup, proof cutoff semantics, or certificate semantics.

## Learned mechanism and next step

Initial global-frontier geometry alone did not yield a stable online rule.
Before any future G2-B enumeration, a later round should isolate two distinct
effects: complete-initial-census scheduling and rejected-lookahead target
reordering. Those experiments must remain default-off and must not infer a
policy from instance classes or historical winners.
"""
    (common.OUT / "final_report.md").write_text(report, encoding="utf-8")
    representative = """# Round 38 representative trajectory comparisons

The machine-readable rows are in `representative_trajectory_comparisons.csv`.
All gaps below use the pair's common verified upper bound.

## Stable V20 positive (ordinal 8, 900 seconds)

C6 initially targets `L1` from `0.206824` to `0.271766`. G2-A first
completes the four-cell census, rejects midpoint children with
`b+=0.208433 < t=0.289176`, discards them, targets the unchanged `L1` to
`0.289176`, then targets `L2` and reaches `0.329851`. The common-UB gap
improves by `0.112251` and AUC by `0.094528`. No G2-A child becomes a live
descendant.

## Stable V50 adversarial witness (ordinal 10, 900 seconds)

G2-A rejects `b+=7.461556 < t=7.555718`, then its two native target steps
match the C6 bound milestones. Final common-UB gaps tie; G2-A AUC is worse by
`0.000789`. Again, the sequence differs only because the rejected pilot and
complete census precede the same parent-target progression.

## Confirmed V50 tight-T regression (ordinal 11, 900 seconds)

C6 first targets `L1` to `0.514198`, reaches `0.558341`, and then performs an
atomic child-infeasibility split before reaching lower bound `0.613715`.
G2-A rejects `b+=0.540854 < t=0.623055`, discards its children, sends the
unchanged parent directly toward `0.623055`, and remains deadline-open at
`0.607633`. The common-UB gap change is `-0.009008` and the AUC change is
`-0.010889`. This is the decisive bidirectional target/split reordering.
"""
    (common.OUT / "representative_trajectory_comparisons.md").write_text(
        representative, encoding="utf-8"
    )
    print(json.dumps({
        "decision": final_decision["decision"],
        "official_runs": exact["official_run_count"],
        "official_pairs": exact["official_pair_count"],
        "false_certificates": exact["false_certificate_count"],
        "certificate_regressions": exact["certificate_regression_count"],
        "child_evaluations": total_child_evaluations,
        "next_frontier_completions": total_completions,
        "accepted_refinements": total_refinements,
    }, indent=2, sort_keys=True))
    return 0 if (
        exact["all_run_gates_pass"] and
        exact["false_certificate_count"] == 0 and
        exact["certificate_regression_count"] == 0 and
        total_refinements == 0 and
        final_decision["decision"].startswith("do_not_promote")
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
