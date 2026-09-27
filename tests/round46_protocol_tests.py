#!/usr/bin/env python3
"""Pre-run protocol tests for the frozen Round 46 screen."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import round46_common as common  # noqa: E402


class Round46ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.exe = Path(os.environ.get("EXACTEBRP_ROUND46_EXE", common.EXE))
        if not cls.exe.is_file():
            raise RuntimeError(f"official Round 46 executable missing: {cls.exe}")
        cls.items = common.frozen_instances()
        cls.dev = [row for row in cls.items.values()
                   if row["panel"] == "development"]

    def commands(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "build") as temporary:
            run_dir = Path(temporary) / "row"
            for k0 in common.K_GRID:
                for rho in common.RHO_GRID:
                    yield k0, rho, common.c6_command(
                        self.dev[0], run_dir, 300.0, k0, rho, self.exe)

    def test_frozen_grid_and_stage3_cardinality(self) -> None:
        arms = json.loads((common.OUT / "arm_definition.json").read_text(
            encoding="utf-8"))["arms"]
        self.assertEqual(len(arms), 10)
        self.assertEqual(len(self.dev), 10)
        self.assertEqual(len(arms) * len(self.dev), 100)
        self.assertEqual({row["rho"] for row in arms}, set(common.RHO_GRID))
        self.assertEqual({row["K0"] for row in arms}, {1, 4})

    def test_one_official_executable_and_no_per_rho_build(self) -> None:
        hashes, paths = set(), set()
        for _, _, command in self.commands():
            paths.add(command[0])
            hashes.add(command[command.index("--round24-executable-sha256") + 1])
        self.assertEqual(paths, {str(self.exe.resolve())})
        self.assertEqual(hashes, {common.sha256(self.exe)})
        self.assertNotIn("dev-gurobi-release",
                         self.exe.as_posix().lower())
        self.assertFalse(any("rho" in part.lower()
                             for part in self.exe.parts[-2:]))

    def test_pure_c6_midpoint_contract(self) -> None:
        forbidden_values = {"gamma-veto", "pmm", "fpmm"}
        for k0, rho, command in self.commands():
            lowered = [token.lower() for token in command]
            self.assertTrue(forbidden_values.isdisjoint(lowered))
            for option in (
                    "--round43-envelope-refinement",
                    "--round43-lifted-cuts",
                    "--round43-frontier-consolidation",
                    "--round44-envelope-tail-repair",
                    "--round44-rank1-cuts", "--round44-mip-starts",
                    "--round44-frontier-consolidation",
                    "--round45-adaptive-parametric-partition"):
                self.assertEqual(command[command.index(option) + 1], "off")
            self.assertEqual(
                command[command.index("--round45-point-rule") + 1],
                "midpoint")
            self.assertEqual(
                command[command.index("--frontier-adaptive-split-factor") + 1],
                "2")
            self.assertEqual(
                command[command.index("--round40-c6-coarse-start") + 1],
                "off" if k0 == 4 else "k1-adaptive")
            self.assertEqual(float(command[
                command.index("--c6-normalized-split-threshold") + 1]), rho)

    def test_solver_and_cap_contract(self) -> None:
        for _, _, command in self.commands():
            self.assertEqual(command[command.index("--threads") + 1], "1")
            self.assertEqual(command[command.index("--mip-threads") + 1], "1")
            self.assertEqual(command[command.index("--gurobi-seed") + 1], "0")
            self.assertEqual(command[command.index("--gurobi-presolve") + 1], "-1")
            self.assertLessEqual(float(command[
                command.index("--process-wall-time-limit") + 1]), 1800.0)

    def test_no_v50_and_no_candidate_before_stage0(self) -> None:
        freeze = json.loads((common.OUT / "dataset_freeze.json").read_text(
            encoding="utf-8"))
        self.assertTrue(freeze["no_v50"])
        self.assertFalse(any("v50" in row["path"].lower()
                             for row in freeze["instances"]))
        manifest = common.OUT / "stage0_freeze_manifest.json"
        self.assertTrue(manifest.is_file())
        for command_path in common.RUNS.glob("*/command.json"):
            self.assertGreaterEqual(command_path.stat().st_mtime_ns,
                                    manifest.stat().st_mtime_ns)

    def test_rho_identity_is_serialized_everywhere(self) -> None:
        value = common.identity("K4-r015", 4, 0.15)
        self.assertEqual(value["rho"], 0.15)
        self.assertTrue(value["rho_explicit"])
        self.assertEqual(value["rho_source"], "explicit")
        runner = (ROOT / "scripts" / "round46_experiment.py").read_text(
            encoding="utf-8")
        for token in ("command.json", "process_manifest.json",
                      "c6_split_decision_ledger.csv", "run_id"):
            self.assertIn(token, runner)

    def test_historical_old_c6_is_still_frozen(self) -> None:
        source = (ROOT / "src" / "PaperExternalGiniTree.cpp").read_text(
            encoding="utf-8")
        self.assertGreaterEqual(
            source.count("kRound31C6NormalizedSplitThreshold"), 2)
        self.assertIn("options.c6_normalized_split_threshold", source)


if __name__ == "__main__":
    unittest.main()
