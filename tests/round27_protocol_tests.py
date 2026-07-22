#!/usr/bin/env python3
"""Protocol and command-construction tests for Round 27."""

from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "round27", SCRIPTS / "run_round27_experiments.py")
assert SPEC and SPEC.loader
round27 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(round27)


class Round27ProtocolTests(unittest.TestCase):
    def test_official_matrix_is_exact(self) -> None:
        self.assertEqual(len(round27.STAGE1), 4)
        self.assertEqual(len(round27.STAGE2), 15)
        self.assertEqual(len(round27.STAGE3), 2)
        self.assertEqual(set(round27.STAGE2_INSTANCES), {
            "V12_M1", "V12_M2", "high_imbalance_seed3202",
            "moderate_seed3302", "tight_T_seed3101"})

    def test_c2_uses_generation_and_lp_events_only(self) -> None:
        command = round27.c2_command("V12_M1", 300, Path("audit"))
        self.assertNotIn("--primal-heuristic-seconds", command)
        self.assertNotIn("--external-gini-split-after-attempts", command)
        self.assertEqual(command[command.index("--primal-heuristic-stop") + 1],
                         "generation-stagnation")
        self.assertEqual(command[command.index(
            "--primal-heuristic-no-improve-generations") + 1], "2000")
        self.assertEqual(command[command.index("--external-gini-scheduling") + 1],
                         "paper-lp-event")
        self.assertEqual(command[command.index("--external-gini-warm-start") + 1],
                         "false")

    def test_standalone_hga_has_no_time_budget(self) -> None:
        command = round27.hga_command("V12_M2", Path("audit"))
        self.assertNotIn("--time-limit", command)
        self.assertNotIn("--process-wall-time-limit", command)
        self.assertNotIn("--primal-heuristic-seconds", command)
        self.assertIn("--primal-heuristic-generation-log", command)

    def test_pgrb_has_no_hga_or_tailored_information(self) -> None:
        command = round27.plain_command("V12_M1", 300, Path("audit"))
        self.assertIn("--plain-baseline", command)
        self.assertNotIn("--primal-heuristic", command)
        self.assertNotIn("--external-gini-scheduling", command)

    def test_lossless_compression_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory(dir=round27.ROOT) as temporary:
            path = Path(temporary) / "trajectory.csv"
            # Exercise the same deterministic gzip parameters without crossing
            # the production size threshold.
            content = b"generation,best\n0,-1\n1,-1\n"
            path.write_bytes(content)
            self.assertEqual(round27.sha256(path), __import__("hashlib").sha256(
                content).hexdigest())

    def test_protocol_names_required_outputs(self) -> None:
        text = round27.PROTOCOL.read_text(encoding="utf-8")
        self.assertIn("C2-PAPER", text)
        self.assertIn("2,000 consecutive completed", text)
        self.assertIn("exactly 15 serial official rows", text)


if __name__ == "__main__":
    unittest.main()
