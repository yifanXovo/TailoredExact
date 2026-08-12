#!/usr/bin/env python3
"""Protocol and command tests for the conditional Round 36 Stage C layer."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import analyze_round36_stage_c as analysis  # noqa: E402
import audit_round36_completion as completion_audit  # noqa: E402
import freeze_round36_stage_c as freeze  # noqa: E402
import package_round36_evidence as evidence_package  # noqa: E402
import round36_stage_c_common as common  # noqa: E402


class StageCProtocolTests(unittest.TestCase):
    def test_final_package_and_completion_audit_require_stage_c(self) -> None:
        required = {
            "stage_c_candidate_definition.json",
            "stage_c_contract_fix_audit.csv",
            "stage_c_contract_fix_audit.json",
            "stage_c_contract_fix_audit.md",
            "stage_c_invalidated_attempt_1_contract_bug.json",
            "stage_c_invalidated_attempt_1_contract_bug.md",
            "stage_c_validation_matrix.csv",
            "stage_c_command_freeze.json",
            "stage_c_frozen_manifest.json",
            "stage_c_runner_row_summary.csv",
            "stage_c_per_run_results.csv",
            "stage_c_comparisons.csv",
            "stage_c_group_summaries.csv",
            "stage_c_final_audit.json",
            "stage_c_final_report.md",
        }
        self.assertTrue(required.issubset(set(evidence_package.FINAL_DERIVED)))
        self.assertTrue(required.issubset(set(completion_audit.FINAL_FILES)))
        self.assertIn("stage_c_completion_manifest.csv",
                      completion_audit.FINAL_FILES)

    def test_source_matrix_is_exactly_35_plus_12(self) -> None:
        rows = freeze.source_rows()
        self.assertEqual(47, len(rows))
        self.assertEqual(35, sum(row["validation_stage"] ==
                                 "qualification_1800" for row in rows))
        self.assertEqual(12, sum(row["validation_stage"] ==
                                 "independent_v50_3600" for row in rows))

    def test_candidate_command_is_bw_p_proof_normalized(self) -> None:
        row = freeze.source_rows()[0]
        item = common.inventory()[row["instance_id"]]
        command = common.command_for(row, item,
                                     common.RUNS / row["run_id"])
        mapping = dict(zip(command[1::2], command[2::2]))
        self.assertEqual("bw-p", mapping["--round36-c6-causal-arm"])
        self.assertEqual("proof",
                         mapping["--round36-c6-split-normalization"])
        self.assertEqual("hga-full",
                         mapping["--round34-c6-startup-variant"])
        self.assertEqual("hga-tgbc", mapping["--primal-heuristic"])

    def test_frozen_knobs_and_reproducibility(self) -> None:
        row = freeze.source_rows()[0]
        item = common.inventory()[row["instance_id"]]
        command = common.command_for(row, item,
                                     common.RUNS / row["run_id"])
        mapping = dict(zip(command[1::2], command[2::2]))
        self.assertEqual("4", mapping["--frontier-intervals"])
        self.assertEqual("0", mapping["--gurobi-seed"])
        self.assertEqual("1", mapping["--threads"])
        self.assertEqual("false", mapping["--external-gini-warm-start"])
        self.assertNotIn("--rho", command)

    def test_stage_c_does_not_modify_default_mode(self) -> None:
        self.assertEqual("BW-P", common.ARM)
        self.assertEqual("bw-p", common.CAUSAL_ARM)
        self.assertEqual("proof", common.NORMALIZATION)

    def test_stage_c_uses_an_isolated_executable(self) -> None:
        self.assertNotEqual(common.STAGE_B_EXE, common.EXE)
        self.assertIn("build_round36_stage_c_contract_fix",
                      common.EXE.as_posix())

    def test_comparison_outcome_prioritizes_certificate(self) -> None:
        self.assertEqual("candidate_win", analysis.comparison_outcome(
            True, False, 0.2, 0.1))
        self.assertEqual("comparator_win", analysis.comparison_outcome(
            False, True, 0.1, 0.2))

    def test_comparison_outcome_uses_common_ub_gap(self) -> None:
        self.assertEqual("candidate_win", analysis.comparison_outcome(
            False, False, 0.1, 0.2))
        self.assertEqual("comparator_win", analysis.comparison_outcome(
            False, False, 0.2, 0.1))
        self.assertEqual("tie", analysis.comparison_outcome(
            False, False, 0.1, 0.1 + 1e-12))

    def test_safe_gap_is_nonnegative(self) -> None:
        self.assertEqual(0.0, analysis.safe_gap(1.0, 1.0 + 1e-12))

    def test_historical_comparator_sources_cover_every_stage_c_row(self) -> None:
        for stage in analysis.HGA_FILES:
            hga = analysis.keyed(analysis.HGA_FILES[stage])
            simple = analysis.keyed(analysis.SIMPLE_FILES[stage])
            pgrb = analysis.keyed(analysis.PGRB_FILES[stage])
            expected = {row["instance_id"] for row in freeze.source_rows()
                        if row["validation_stage"] == stage}
            self.assertEqual(expected, set(hga))
            self.assertEqual(expected, set(simple))
            self.assertEqual(expected, set(pgrb))


if __name__ == "__main__":
    unittest.main()
