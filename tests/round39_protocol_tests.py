#!/usr/bin/env python3
"""Static and frozen-data guards for the Round 39 qualification."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import round39_common as common  # noqa: E402


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Round39ProtocolTests(unittest.TestCase):
    def test_default_remains_full(self) -> None:
        self.assertIn(
            'round34_c6_startup_variant = "hga-full"',
            text("include/Instance.hpp"))

    def test_light_changes_only_uniform_stagnation_contract(self) -> None:
        source = text("src/PaperExternalGiniTree.cpp")
        self.assertIn('round34_c6_startup_variant == "hga-full"', source)
        self.assertIn('round34_c6_startup_variant == "hga-light-1000"', source)
        self.assertIn("options.primal_heuristic_no_improve_generations == 2000",
                      source)
        self.assertIn("options.primal_heuristic_no_improve_generations == 1000",
                      source)
        command = text("scripts/round39_common.py")
        self.assertIn('1000 if light else 2000', command)
        self.assertNotIn("item[\"V\"]", command)
        self.assertNotIn("item[\"M\"]", command)

    def test_frozen_panel_has_balanced_gradient(self) -> None:
        rows = common.csv_rows(common.INSTANCE_MANIFEST)
        self.assertEqual(len(rows), 24)
        self.assertEqual(Counter(row["difficulty_stratum"] for row in rows), {
            "small-easy": 8, "small-medium": 8, "small-hard": 8})
        self.assertEqual({int(row["V"]) for row in rows}, {8, 10, 12})
        self.assertEqual({int(row["M"]) for row in rows}, {1, 2, 3})
        self.assertEqual({int(row["Q"]) for row in rows}, {20, 30})
        self.assertTrue(all(row["frozen_before_official_comparison"] == "True"
                            for row in rows))
        self.assertTrue(all(row["solver_outcomes_used_for_selection"] == "False"
                            for row in rows))

    def test_instance_and_descriptor_hashes_are_frozen(self) -> None:
        manifest = common.load_json(common.FROZEN_MANIFEST)
        self.assertEqual(sha256(common.INSTANCE_MANIFEST),
                         manifest["instance_manifest_sha256"])
        self.assertEqual(sha256(common.DESCRIPTOR_TABLE),
                         manifest["descriptor_table_sha256"])
        self.assertEqual(sha256(common.OFFICIAL_MATRIX),
                         manifest["official_matrix_sha256"])
        for row in common.csv_rows(common.INSTANCE_MANIFEST):
            self.assertEqual(sha256(ROOT / row["path"]), row["sha256"])

    def test_medium_hard_nontrivial_filters(self) -> None:
        for row in common.csv_rows(common.DESCRIPTOR_TABLE):
            if row["difficulty_stratum"] not in {"small-medium", "small-hard"}:
                continue
            self.assertGreaterEqual(int(row["surplus_count"]), 2)
            self.assertGreaterEqual(int(row["deficit_count"]), 2)
            self.assertGreaterEqual(float(row["active_fraction"]), 0.60)
            self.assertGreater(float(row["initial_objective_lambda_0_15"]), 0.10)
            self.assertGreater(float(row["plausible_ordered_pair_density"]), 0.10)

    def test_official_matrix_and_guard_are_predeclared(self) -> None:
        rows = common.csv_rows(common.OFFICIAL_MATRIX)
        self.assertEqual(len(rows), 51)
        self.assertEqual(Counter(row["stage"] for row in rows), {
            "primary": 48, "guard": 3})
        self.assertTrue(all(row["run_to_convergence"] == "True" for row in rows))
        self.assertTrue(all(row["frozen_before_official_results"] == "True"
                            for row in rows))
        guards = common.csv_rows(common.GUARD_MANIFEST)
        self.assertEqual(len(guards), 3)
        self.assertEqual({row["difficulty_stratum"] for row in guards}, {
            "small-easy", "small-medium", "small-hard"})

    def test_runner_requires_strict_convergence(self) -> None:
        runner = text("scripts/run_round39_experiments.py")
        for token in (
            "strict_converged", "strict_certified_original_problem",
            "verification_passed", "completion_marker_atomic",
            "artifact_manifest_sha256", "incomplete_preserved_requires_extension",
            "GRB_LICENSE_FILE", "algorithmic_solve_state_resumed",
        ):
            self.assertIn(token, runner)

    def test_analysis_is_complete_and_historical_rows_stay_separate(self) -> None:
        analyzer = text("scripts/analyze_round39.py")
        for token in (
            "p_grb_vs_light_convergence.csv", "per_stratum_summary.csv",
            "full_vs_light_guard_results.csv", "exactness_certificate_audit.csv",
            "representative_trajectories.csv", "historical_benchmark_comparison.csv",
            "final_decision.json", "expected 51 frozen rows",
        ):
            self.assertIn(token, analyzer)
        self.assertNotIn("HISTORICAL_PAIRS +", analyzer)


if __name__ == "__main__":
    unittest.main()
