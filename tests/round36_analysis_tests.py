#!/usr/bin/env python3
"""Integrity checks for derived Round 36 causal-analysis outputs."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_incumbent_decomposition_causal_round36"
PREFIX = "" if (OUT / "per_arm_results.csv").is_file() else "interim_"
sys.path.insert(0, str(ROOT / "scripts"))
import analyze_round36 as analysis  # noqa: E402


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / f"{PREFIX}{name}").open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def yes(value: object) -> bool:
    return str(value).strip().lower() == "true"


class Round36AnalysisTests(unittest.TestCase):
    def test_required_metric_schema_contract(self) -> None:
        valid, problems = analysis.metric_schema_valid(
            OUT, PREFIX, expected_runs=len(rows("per_arm_results.csv")))
        self.assertTrue(valid, problems)

    def test_artifact_inventory_contract_is_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / "run"
            directory.mkdir()
            required = [path.relative_to(directory).as_posix() for path in
                        analysis.common.required_artifacts(directory)]
            artifacts = [{"path": path} for path in required]
            marker = {"artifact_count": len(artifacts)}
            self.assertEqual((True, "artifact_inventory_contract_valid"),
                             analysis.artifact_inventory_contract(
                                 directory, artifacts, marker))
            cases = (
                (artifacts + [artifacts[0]],
                 {"artifact_count": len(artifacts) + 1},
                 "artifact_manifest_duplicate_path"),
                (artifacts[:-1], {"artifact_count": len(artifacts) - 1},
                 "required_artifact_unlisted"),
                (artifacts + [{"path": "../escape.txt"}],
                 {"artifact_count": len(artifacts) + 1},
                 "artifact_path_outside_run"),
                (artifacts, {"artifact_count": len(artifacts) + 1},
                 "artifact_count_mismatch"),
            )
            for rows, state, reason in cases:
                with self.subTest(reason=reason):
                    valid, actual = analysis.artifact_inventory_contract(
                        directory, rows, state)
                    self.assertFalse(valid)
                    self.assertTrue(actual.startswith(reason))

    def test_deadline_noncertificate_gate_is_fail_closed(self) -> None:
        good = {
            "strict_certified_original_problem": False,
            "status": "round31_c6_external_gini_tree_time_limit",
            "graceful_deadline_finalization": True,
            "exact_phase_started": True,
            "external_gini_tree_failure_reason": "overall_global_deadline",
            "external_gini_tree_global_deadline_interruption_count": 1,
            "external_gini_tree_open_leaf_count": 3,
            "external_gini_tree_all_relevant_leaves_closed": False,
            "strict_certificate_rejection_reason": "relevant_leaf_open",
        }
        self.assertTrue(analysis.graceful_deadline_noncertificate(good))
        corruptions = {
            "strict_certified_original_problem": True,
            "status": "stopped_early",
            "graceful_deadline_finalization": False,
            "exact_phase_started": False,
            "external_gini_tree_failure_reason": "none",
            "external_gini_tree_global_deadline_interruption_count": 0,
            "external_gini_tree_open_leaf_count": 0,
            "external_gini_tree_all_relevant_leaves_closed": True,
            "strict_certificate_rejection_reason": "unsupported_status",
        }
        for field, value in corruptions.items():
            with self.subTest(field=field):
                self.assertFalse(analysis.graceful_deadline_noncertificate(
                    {**good, field: value}))

    def test_runner_lifecycle_gate_is_fail_closed(self) -> None:
        good = {
            "return_code": 0,
            "emergency_timeout": False,
            "result_json_parse_verified_after_process_exit": True,
            "missing_required_artifacts": [],
            "completed": True,
            "completion_marker_atomic": True,
            "algorithmic_solve_state_resumed": False,
        }
        self.assertTrue(analysis.runner_lifecycle_valid(good))
        corruptions = {
            "return_code": 1,
            "emergency_timeout": True,
            "result_json_parse_verified_after_process_exit": False,
            "missing_required_artifacts": ["result.json"],
            "completed": False,
            "completion_marker_atomic": False,
            "algorithmic_solve_state_resumed": True,
        }
        for field, value in corruptions.items():
            with self.subTest(field=field):
                state = {**good, field: value}
                self.assertFalse(analysis.runner_lifecycle_valid(state))

    def test_complete_panels_have_four_arms(self) -> None:
        per_arm = rows("per_arm_results.csv")
        grouped: dict[str, set[str]] = {}
        for row in per_arm:
            grouped.setdefault(row["panel_row_id"], set()).add(row["arm"])
        self.assertTrue(grouped)
        self.assertTrue(all(arms == {"HH", "SS", "BW-P", "BW-A"}
                            for arms in grouped.values()))

    def test_exactness_audits_are_green(self) -> None:
        audits = rows("exactness_certificate_audit.csv")
        self.assertTrue(audits)
        self.assertTrue(all(yes(row["exactness_certificate_audit_passed"])
                            for row in audits))
        self.assertFalse(any(yes(row["false_certificate"])
                             for row in audits))
        lifecycle_fields = (
            "runner_normal_exit", "runner_no_emergency_timeout",
            "result_json_verified_after_process_exit",
            "runner_required_artifacts_complete",
            "atomic_completion_marker_valid",
            "algorithmic_solve_state_not_resumed", "runner_lifecycle_valid",
        )
        self.assertTrue(all(yes(row[field]) for row in audits
                            for field in lifecycle_fields))
        self.assertTrue(all(yes(row[
            "certificate_or_graceful_deadline_endpoint_valid"])
            for row in audits))
        self.assertTrue(all(yes(row["finite_bounds"]) for row in audits))

    def test_geometry_and_normalization_controls(self) -> None:
        geometry = rows("causal_geometry_comparison.csv")
        normalization = rows("causal_normalization_comparison.csv")
        self.assertEqual(len(geometry), len(normalization))
        self.assertTrue(all(yes(row["same_proof_incumbent"])
                            for row in geometry if yes(row["geometry_exposure"])))
        self.assertTrue(all(yes(row["same_proof_incumbent"])
                            and yes(row["same_anchor"])
                            for row in normalization))

    def test_auc_handling_convention(self) -> None:
        comparisons = (rows("causal_geometry_comparison.csv")
                       + rows("causal_normalization_comparison.csv"))
        observed = [row for row in comparisons
                    if row.get("auc_status") == "observed_common_window"]
        self.assertTrue(observed)
        self.assertTrue(all(row["auc_convention"] ==
            "left_continuous_no_interpolation_no_post_last_extension"
            for row in observed))

    def test_expanded_mechanism_ledgers_are_joinable(self) -> None:
        lookahead = rows("child_lookahead_split_audit.csv")
        targets = rows("native_target_audit.csv")
        closures = rows("terminal_closure_audit.csv")
        self.assertTrue(lookahead)
        self.assertTrue(targets)
        self.assertTrue(closures)
        self.assertTrue(all("b_plus" in row and "eta_proof" in row
                            and "eta_anchor" in row for row in lookahead))
        self.assertTrue(all(row["run_id"] and row["panel_row_id"]
                            for row in lookahead + targets + closures))

    def test_machine_decision_matches_completion_state(self) -> None:
        decision = json.loads((OUT / f"{PREFIX}final_audit_decision.json").read_text(
            encoding="utf-8"))
        self.assertFalse(decision["automatic_promotion_performed"])
        self.assertEqual(decision["validated_gurobi_mainline"], "C6-HGA-FULL")
        self.assertEqual(decision["false_certificate_count"], 0)
        if PREFIX:
            self.assertEqual(decision["classification"], "incomplete_stage_b")
        else:
            self.assertEqual(decision["completed_official_rows"], 56)


if __name__ == "__main__":
    unittest.main()
