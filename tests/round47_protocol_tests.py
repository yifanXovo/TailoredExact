#!/usr/bin/env python3
"""Protocol tests for the frozen Round 47 AM/AMC study."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import round47_common as common  # noqa: E402


class Round47ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.exe = Path(os.environ.get("EXACTEBRP_ROUND47_EXE", common.EXE))
        if not cls.exe.is_file():
            raise RuntimeError(f"official Round 47 executable missing: {cls.exe}")
        cls.items = common.frozen_instances()

    def commands(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "build") as temporary:
            run_dir = Path(temporary) / "row"
            for arm in common.ARMS:
                yield arm, common.candidate_command(
                    self.items[common.DEVELOPMENT[0]], run_dir, 300.0,
                    arm, self.exe)

    def test_stage0_precedes_candidate_runtime_and_is_hash_frozen(self) -> None:
        manifest_path = common.OUT / "stage0_freeze_manifest.json"
        manifest = common.load_json(manifest_path)
        self.assertFalse(manifest["candidate_run_files_present"])
        self.assertEqual(len(manifest["files"]), 11)
        for row in manifest["files"]:
            path = common.OUT / row["path"]
            self.assertTrue(path.is_file())
            self.assertEqual(common.sha256(path), row["sha256"])
        for command_path in common.RUNS.glob("*/command.json"):
            self.assertGreaterEqual(command_path.stat().st_mtime_ns,
                                    manifest_path.stat().st_mtime_ns)

    def test_exactly_four_arms_one_tau_midpoint_only(self) -> None:
        definition = common.load_json(
            common.OUT / "algorithm_arm_definition.json")
        self.assertEqual(tuple(row["arm"] for row in definition["arms"]),
                         common.ARMS)
        self.assertEqual({row["identity"]["tau"]
                          for row in definition["arms"]},
                         {common.TAU})
        self.assertEqual({row["K0"] for row in definition["arms"]}, {1, 4})
        self.assertEqual({row["mode"] for row in definition["arms"]},
                         {"adaptive-mass", "adaptive-mass-contraction"})
        freeze = common.load_json(common.OUT / "tau_freeze.json")
        self.assertEqual(freeze["tau"], common.TAU)
        self.assertTrue(freeze["frozen_before_candidate_runtime"])

    def test_commands_are_pure_lightweight_c6(self) -> None:
        hashes = set()
        for arm, command in self.commands():
            hashes.add(command[command.index(
                "--round24-executable-sha256") + 1])
            self.assertEqual(command[command.index(
                "--round47-c6-adaptive-mass") + 1],
                common.ARM_DEFINITIONS[arm]["mode"])
            self.assertEqual(float(command[command.index(
                "--round47-c6-adaptive-mass-tau") + 1]), common.TAU)
            self.assertEqual(command[command.index(
                "--round45-point-rule") + 1], "midpoint")
            self.assertEqual(command[command.index(
                "--round40-c6-coarse-start") + 1],
                "off" if arm.startswith("K4") else "k1-adaptive")
            for option in (
                    "--round43-envelope-refinement",
                    "--round43-lifted-cuts",
                    "--round43-frontier-consolidation",
                    "--round44-envelope-tail-repair",
                    "--round44-rank1-cuts", "--round44-mip-starts",
                    "--round44-frontier-consolidation",
                    "--round45-adaptive-parametric-partition"):
                self.assertEqual(command[command.index(option) + 1], "off")
            self.assertNotIn("gamma-veto", [token.lower() for token in command])
            self.assertLessEqual(float(command[command.index(
                "--process-wall-time-limit") + 1]), 1800.0)
        self.assertEqual(hashes, {common.sha256(self.exe)})
        self.assertNotIn("dev-gurobi-release", self.exe.as_posix().lower())

    def test_no_extra_score_query_in_source_or_identity(self) -> None:
        for arm in common.ARMS:
            identity = common.identity(arm)
            self.assertEqual(identity["extra_lp_queries"], 0)
            self.assertEqual(identity["extra_mip_queries"], 0)
        source = (ROOT / "src" / "PaperExternalGiniTree.cpp").read_text(
            encoding="utf-8")
        start = source.index("evaluateC6AdaptiveMassSplitDecision(")
        end = source.index(
            "PaperTerminalMipDecision evaluatePaperTerminalMipDecision", start)
        body = source[start:end]
        self.assertNotIn("optimize", body.lower())
        self.assertNotIn("solve", body.lower())

    def test_no_baseline_matrix_no_v50_and_frozen_panels(self) -> None:
        freeze = common.load_json(common.OUT / "dataset_freeze.json")
        self.assertFalse(freeze["V50_allowed"])
        self.assertEqual(len(common.DEVELOPMENT), 10)
        self.assertEqual(len(common.STAGE5), 14)
        self.assertFalse(any("v50" in row["path"].lower()
                             for row in freeze["instances"]))
        runner = (ROOT / "scripts" / "run_round47.py").read_text(
            encoding="utf-8")
        for forbidden in ("P-GRB", "K4-r001", "gamma-veto", "no-adaptive"):
            self.assertNotIn(forbidden, runner)

    def test_historical_reference_hashes_are_real(self) -> None:
        rows = common.csv_rows(
            common.OUT / "historical_baseline_reference_manifest.csv")
        self.assertGreater(len(rows), 0)
        for row in rows:
            artifact = ROOT / row["source_path"].split("#", 1)[0]
            self.assertTrue(artifact.is_file(), artifact)
            self.assertEqual(common.sha256(artifact), row["artifact_sha256"])
            instance = next((item for item in self.items.values()
                             if item["sha256"] == row["input_sha256"]), None)
            self.assertIsNotNone(instance, row["instance"])

    def test_completed_rows_have_complete_logs_and_one_executable(self) -> None:
        hashes = set()
        required = set(__import__("round47_experiment").REQUIRED)
        for marker_path in common.RUNS.glob("*/completion_marker.json"):
            marker = common.load_json(marker_path)
            self.assertTrue(marker["complete"])
            hashes.add(marker["executable_sha256"])
            names = {path.name for path in marker_path.parent.iterdir()
                     if path.is_file()}
            self.assertTrue(required <= names)
        self.assertLessEqual(len(hashes), 1)

    def test_final_classification_is_evidence_derived_when_present(self) -> None:
        path = common.OUT / "final_decision.json"
        if not path.is_file():
            self.skipTest("final decision is produced only after Stage 5")
        value = common.load_json(path)
        self.assertTrue(value["derived_from_completed_evidence"])
        self.assertEqual(value["tau"], common.TAU)
        self.assertEqual(value["stage_rows"],
                         {"stage3": 40, "stage4": 40, "stage5": 28})


if __name__ == "__main__":
    unittest.main()
