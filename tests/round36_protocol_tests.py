#!/usr/bin/env python3
"""Protocol gates for the predeclared Round 36 causal study."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_incumbent_decomposition_causal_round36"


class Round36ProtocolTests(unittest.TestCase):
    def test_panel_is_frozen_before_new_results(self) -> None:
        payload = json.loads((OUT / "frozen_causal_panel.json").read_text())
        self.assertEqual("exactebrp-round36-frozen-causal-panel-v1",
                         payload["schema"])
        self.assertFalse(payload["selection_observes_round36_results"])
        self.assertEqual(14, payload["row_count"])
        self.assertEqual(["HH", "SS", "BW-P", "BW-A"], payload["arms"])
        self.assertEqual(0.01, payload["rho"])
        self.assertEqual(4, payload["initial_interval_count"])
        self.assertTrue(all(row["frozen_before_round36_causal_results"]
                            for row in payload["rows"]))

    def test_panel_representation(self) -> None:
        with (OUT / "frozen_causal_panel.csv").open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(14, len(rows))
        self.assertEqual(14, len({row["panel_row_id"] for row in rows}))
        self.assertTrue({"V12_M1", "V12_M2"}.issubset(
            {row["instance_id"] for row in rows}))
        self.assertEqual({"1", "2", "3", "4"}, {row["M"] for row in rows})
        self.assertTrue({"moderate", "high_imbalance", "tight_T"}.issubset(
            {row["scenario"] for row in rows}))
        self.assertGreaterEqual(sum(row["V"] == "50" for row in rows), 4)
        self.assertEqual(3, sum(
            row["round35_pattern"] ==
            "4_simple_ub_weaker_exact_phase_slower" for row in rows))
        self.assertGreaterEqual(sum(
            row["round35_pattern"] ==
            "3_simple_ub_weaker_exact_phase_faster" for row in rows), 5)

    def test_protocol_forbids_confounded_tuning_and_dispatch(self) -> None:
        protocol = (OUT / "round36_protocol.md").read_text(encoding="utf-8")
        self.assertIn("`K=4`", protocol)
        self.assertIn("`rho=0.01`", protocol)
        self.assertIn("no instance-dependent dispatch", protocol)
        self.assertIn("No candidate is promoted automatically", protocol)

    def test_frozen_stage_b_matrix_is_balanced(self) -> None:
        matrix_path = OUT / "round36_official_matrix.csv"
        if not matrix_path.is_file():
            self.skipTest("Stage B matrix is frozen after Stage A")
        with matrix_path.open(newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(56, len(rows))
        self.assertEqual({"HH", "SS", "BW-P", "BW-A"},
                         {row["arm"] for row in rows})
        for arm in ("HH", "SS", "BW-P", "BW-A"):
            self.assertEqual(14, sum(row["arm"] == arm for row in rows))
        self.assertEqual({"0.01"}, {row["rho"] for row in rows})
        self.assertEqual({"4"}, {row["initial_interval_count"] for row in rows})
        self.assertEqual({"anchor"}, {
            row["split_normalization"] for row in rows
            if row["arm"] == "BW-A"})
        self.assertEqual({"proof"}, {
            row["split_normalization"] for row in rows
            if row["arm"] != "BW-A"})

    def test_command_freeze_has_only_explicit_uniform_arms(self) -> None:
        path = OUT / "round36_command_freeze.json"
        if not path.is_file():
            self.skipTest("commands are frozen after Stage A")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(payload["frozen_before_causal_results"])
        self.assertEqual(56, payload["row_count"])
        for record in payload["commands"].values():
            command = record["command"]
            self.assertIn("--round36-c6-causal-arm", command)
            self.assertIn("--round36-c6-split-normalization", command)
            self.assertEqual("1", command[command.index("--threads") + 1])
            self.assertEqual("0", command[command.index("--gurobi-seed") + 1])


if __name__ == "__main__":
    unittest.main()
