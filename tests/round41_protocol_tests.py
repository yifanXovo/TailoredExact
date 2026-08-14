#!/usr/bin/env python3
"""Static and native-smoke guards for Round 41."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_decomposition_single_tree_round41"


def source(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def result(run_id: str) -> dict:
    value = json.loads((OUT / "runs" / run_id / "result.json").read_text(
        encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


class Round41ProtocolTests(unittest.TestCase):
    def test_default_and_frozen_c6_contract_are_unchanged(self) -> None:
        instance = source("include/Instance.hpp")
        self.assertIn('round41_static_segmented_gini = "off"', instance)
        self.assertIn('round41_static_segmented_solve = "mip"', instance)
        tree = source("src/PaperExternalGiniTree.cpp")
        self.assertIn("options.frontier_intervals != 4", tree)
        self.assertIn("options.frontier_adaptive_split_factor != 2", tree)
        self.assertIn("options.gurobi_presolve != -1", tree)

    def test_static_path_is_prebuilt_and_one_optimize(self) -> None:
        tree = source("src/PaperExternalGiniTree.cpp")
        start = tree.index("SolveResult solveRound41StaticSegmentedGini(")
        end = tree.index("SolveResult solvePaperExternalGiniTree(", start)
        mechanism = tree[start:end]
        self.assertEqual(mechanism.count("backend->solve(request)"), 1)
        self.assertIn("writeCanonicalCompactModel", mechanism)
        self.assertIn("retain_model_after_solve = false", mechanism)
        self.assertIn("warm_start_enabled = false", mechanism)
        for forbidden in (
            "instance.name", "scenario", "work_units", "node_count",
            "BranchPriority", "GRBcbcut", "GRBcblazy",
        ):
            self.assertNotIn(forbidden, mechanism)

    def test_formulation_contains_required_exact_aggregations(self) -> None:
        writer = source("src/CplexBaseline.cpp")
        self.assertIn("segmentSelectorName", writer)
        self.assertIn("segmentGName", writer)
        self.assertIn("segmentActivationName", writer)
        self.assertIn("segmentProductName", writer)
        self.assertIn("addStaticLinear(selector_sum, \"=\", 1.0)", writer)
        self.assertIn("addStaticLinear(g_sum, \"=\", 0.0)", writer)
        self.assertIn("addStaticLinear(activation_sum, \"=\", 0.0)", writer)
        self.assertIn("addStaticLinear(product_sum, \"=\", 0.0)", writer)
        self.assertIn(
            "addStaticLinear(s_lower_aggregation, \">=\", 0.0)", writer)
        self.assertIn(
            "addStaticLinear(p_lower_aggregation, \">=\", 0.0)", writer)
        self.assertIn("infeasible ? 0.0 : 1.0, \"B\"", writer)

    def test_panel_and_gates_were_frozen(self) -> None:
        with (OUT / "diagnostic_panel_manifest.csv").open(
                newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 10)
        ids = {row["instance_id"] for row in rows}
        self.assertIn(
            "round39_small_medium_V12_M3_Q30_slot08_seed1343324363", ids)
        self.assertIn(
            "round39_small_hard_V12_M3_Q30_slot08_seed1288546114", ids)
        gates = json.loads((OUT / "decision_gates_frozen.json").read_text(
            encoding="utf-8"))
        self.assertTrue(gates["frozen_before_confirmation_runs"])
        self.assertTrue(gates["gate_c"]["both_witnesses_required"])
        self.assertLess(gates["official_process_cap_upper_bound_seconds"],
                        3600)

    def test_native_smoke_and_exactness(self) -> None:
        prefix = (
            "static__round39_small_medium_V8_M3_Q30_slot03_seed1177285734")
        objectives = set()
        for arm in ("st-k2-i", "st-k2-p-core", "st-k2-p-extended"):
            lp = result(f"{prefix}__{arm}__root-lp")
            self.assertEqual(
                lp["status"], "round41_static_segmented_root_lp_complete")
            self.assertTrue(lp["round41_static_segmented_technical_feasible"])
            self.assertGreater(lp["round41_static_model_general_constraints"],
                               0)
            self.assertFalse(lp["strict_certified_original_problem"])
            mip = result(f"{prefix}__{arm}__mip")
            self.assertTrue(mip["round41_static_one_native_mip_job"])
            self.assertTrue(mip["round41_static_original_verifier_passed"])
            self.assertTrue(mip["round41_static_strict_certificate"])
            objectives.add(round(float(mip["objective"]), 12))
        self.assertEqual(len(objectives), 1)

    def test_post_default_equivalence(self) -> None:
        with (OUT / "post_default_c6_equivalence.csv").open(
                newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(
            row["mismatch_count"] == "0" and
            row["default_equivalence_passed"] == "True"
            for row in rows))


if __name__ == "__main__":
    unittest.main()
