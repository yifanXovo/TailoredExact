#!/usr/bin/env python3
"""Static and frozen-evidence guards for Round 40 research."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_regression_adaptive_round40"
sys.path.insert(0, str(ROOT / "scripts"))

import round40_common as common  # noqa: E402


csv.field_size_limit(1024 * 1024 * 1024)


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def load_json(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


class Round40ProtocolTests(unittest.TestCase):
    def test_validated_default_remains_unchanged_and_experiments_off(self) -> None:
        instance = text("include/Instance.hpp")
        self.assertIn('round34_c6_startup_variant = "hga-full"', instance)
        self.assertIn('round40_c6_coarse_start = "off"', instance)
        self.assertIn('round40_c6_ub_geometry = "off"', instance)
        tree = text("src/PaperExternalGiniTree.cpp")
        self.assertIn("options.frontier_intervals != 4", tree)
        self.assertIn("options.frontier_adaptive_split_factor != 2", tree)
        self.assertIn("options.gurobi_presolve != -1", tree)

    def test_presolve_policy_is_uniform_auto(self) -> None:
        decision = load_json("frozen_presolve_decision.json")
        self.assertTrue(decision["round39_contract_was_solver_level_fair"])
        self.assertTrue(decision["round39_labeling_was_ambiguous"])
        self.assertEqual(decision["frozen_policy"], "gurobi-auto")
        self.assertEqual(decision["gurobi_presolve_value"], -1)
        self.assertFalse(decision["instance_dispatch"])
        self.assertTrue(decision["all_rows_exact"])

    def test_part1_manifests_and_fail_closed_analyzer_are_complete(self) -> None:
        self.assertEqual(len(common.csv_rows(OUT / "k1_diagnostic_manifest.csv")),
                         40)
        self.assertEqual(len(common.csv_rows(OUT / "k1_iterative_manifest.csv")),
                         10)
        self.assertEqual(len(common.csv_rows(OUT / "k1_per_run_trajectory.csv")),
                         50)
        analyzer = text("scripts/analyze_round40_k1.py")
        self.assertIn("expected_unresolved_endpoint", analyzer)
        self.assertIn("backend_parameter_roundtrip_valid", analyzer)
        self.assertIn("--require-full", analyzer)

    def test_nested_geometry_is_structural_and_default_off(self) -> None:
        source = text("src/GiniFrontierGeometry.cpp")
        start = source.index(
            "Round40NestedDyadicGeometry makeRound40NestedDyadicGeometry(")
        end = source.index("AnchorGridDecomposition makeProofRelevantAnchorGrid(",
                           start)
        mechanism = source[start:end].lower()
        for forbidden in (
            "instance_id", "scenario", "seed", "elapsed", "runtime",
            "node_count", "work_units", "historical", "hardware",
        ):
            self.assertNotIn(forbidden, mechanism)
        self.assertIn("stable_root_upper", mechanism)
        self.assertIn("global_cell_count * 2", mechanism)
        self.assertIn("round40nestedboundarypreservation", mechanism)

    def test_part2_full_panel_and_stability_gates_are_complete(self) -> None:
        manifest = common.csv_rows(OUT / "ub_geometry_manifest.csv")
        self.assertEqual(len(manifest), 48)
        self.assertEqual(len({row["instance_id"] for row in manifest}), 24)
        self.assertEqual(Counter(row["arm"] for row in manifest), {
            "C6-HGA-FULL-K4": 24, "C6-NESTED-DYADIC-K4": 24})
        trajectories = common.csv_rows(
            OUT / "ub_geometry_per_run_trajectory.csv")
        self.assertEqual(len(trajectories), 48)
        candidate = [row for row in trajectories
                     if row["arm"] == "C6-NESTED-DYADIC-K4"]
        self.assertEqual(len(candidate), 24)
        self.assertTrue(all(row["exactness_passed"] == "True"
                            for row in candidate))
        projection = common.csv_rows(
            OUT / "ub_geometry_round36_stability_projection.csv")
        differing = [row for row in projection
                     if row["ub_values_differ"] == "True"]
        self.assertEqual(len(differing), 10)
        self.assertTrue(all(
            row["legacy_relevant_boundaries_preserved"] == "False" and
            row["nested_relevant_boundaries_preserved"] == "True"
            for row in differing))

    def test_default_equivalence_and_final_exactness_pass(self) -> None:
        default = common.csv_rows(OUT / "default_c6_equivalence.csv")
        self.assertEqual(len(default), 3)
        self.assertTrue(all(row["mismatch_count"] == "0" and
                            row["default_equivalence_passed"] == "True"
                            for row in default))
        exactness = common.csv_rows(OUT / "exactness_audit.csv")
        self.assertEqual(len(exactness), 112)
        self.assertTrue(all(row["accepted_outcome"] == "True"
                            for row in exactness))
        self.assertEqual(sum(row["expected_unresolved"] == "True"
                             for row in exactness), 5)

    def test_final_decision_protects_mainline(self) -> None:
        decision = load_json("final_decision.json")
        self.assertFalse(decision["part1"]["promotion"])
        self.assertFalse(decision["part2"]["promotion"])
        self.assertFalse(decision["part3"]["implemented"])
        self.assertEqual(decision["exactness"]["false_certificates"], 0)
        self.assertEqual(
            decision["promotion_recommendation"],
            "retain_frozen_c6_hga_full_k4_rho_0_01")
        self.assertFalse(decision["automatic_mainline_change"])


if __name__ == "__main__":
    unittest.main()
