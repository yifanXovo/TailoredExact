#!/usr/bin/env python3
"""Protocol tests for the frozen, bounded Round 48 K1-AMF study."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import round48_common as common  # noqa: E402


class Round48ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.exe = Path(os.environ.get("EXACTEBRP_ROUND48_EXE", common.EXE))
        if not cls.exe.is_file():
            raise RuntimeError(f"official Round 48 executable missing: {cls.exe}")
        cls.items = common.frozen_instances()

    def command(self, instance: str | None = None) -> list[str]:
        with tempfile.TemporaryDirectory(dir=ROOT / "build") as temporary:
            run_dir = Path(temporary) / "row"
            return common.candidate_command(
                self.items[instance or common.MECHANISM[0]], run_dir,
                300.0, self.exe)

    def test_01_stage0_precedes_runtime_and_hashes_verify(self) -> None:
        manifest_path = common.OUT / "stage0_freeze_manifest.json"
        manifest = common.load_json(manifest_path)
        self.assertTrue(manifest["frozen_before_candidate_runtime"])
        self.assertFalse(manifest["candidate_runtime_started"])
        self.assertEqual(len(manifest["files"]), 11)
        for row in manifest["files"]:
            path = common.OUT / row["path"]
            self.assertTrue(path.is_file())
            self.assertEqual(common.sha256(path), row["sha256"])
        for command_path in common.RUNS.glob("*/command.json"):
            self.assertGreaterEqual(command_path.stat().st_mtime_ns,
                                    manifest_path.stat().st_mtime_ns)

    def test_02_only_one_new_candidate_k1_amf(self) -> None:
        identity = common.identity()
        self.assertEqual(identity["algorithm"], "K1-AMF")
        self.assertEqual(identity["K0"], 1)
        self.assertEqual(identity["tau"], common.TAU)
        self.assertEqual(identity["point_rule"], "midpoint")
        runner = (ROOT / "scripts" / "run_round48.py").read_text(
            encoding="utf-8")
        self.assertNotIn("K4-AMF", runner)
        self.assertNotIn("P-GRB", runner)

    def test_03_candidate_command_is_exact_frozen_mode(self) -> None:
        command = self.command()
        self.assertEqual(command[command.index("--round48-k1-amf") + 1],
                         "k1-amf")
        self.assertEqual(command[command.index(
            "--round47-c6-adaptive-mass") + 1], "adaptive-mass")
        self.assertEqual(float(command[command.index(
            "--round47-c6-adaptive-mass-tau") + 1]), common.TAU)
        self.assertEqual(command[command.index(
            "--round40-c6-coarse-start") + 1], "k1-adaptive")
        self.assertEqual(command[command.index(
            "--round45-point-rule") + 1], "midpoint")

    def test_04_no_rho_cap_or_contraction(self) -> None:
        command = self.command()
        self.assertNotIn("--c6-normalized-split-threshold", command)
        self.assertFalse(common.identity()["rho_cap"])
        self.assertFalse(common.identity()["contraction"])
        self.assertNotIn("adaptive-mass-contraction", command)

    def test_05_forbidden_research_mechanisms_are_off(self) -> None:
        command = self.command()
        for option in (
                "--round43-envelope-refinement", "--round43-lifted-cuts",
                "--round43-frontier-consolidation",
                "--round44-envelope-tail-repair", "--round44-rank1-cuts",
                "--round44-mip-starts", "--round44-frontier-consolidation",
                "--round45-adaptive-parametric-partition"):
            self.assertEqual(command[command.index(option) + 1], "off")
        lowered = " ".join(command).lower()
        for forbidden in ("gamma-veto", "fpmm", "pmm", "rho-cap"):
            self.assertNotIn(forbidden, lowered)

    def test_06_equal_variable_weighting_no_family_weights(self) -> None:
        registry = common.load_json(
            common.OUT / "eligible_variable_registry.json")
        self.assertTrue(registry["equal_variable_weights"])
        self.assertFalse(registry["equal_family_weights"])
        self.assertFalse(registry["post_outcome_family_selection_allowed"])
        formula = common.load_json(common.OUT / "amf_formula_freeze.json")
        self.assertEqual(formula["adjustable_parameters_introduced"], 0)

    def test_07_score_implementation_has_no_solve_call(self) -> None:
        source = (ROOT / "src" / "Round48K1AMF.cpp").read_text(
            encoding="utf-8")
        start = source.index("AMFFormulationProfile buildRound48")
        body = source[start:]
        self.assertNotIn("optimize(", body.lower())
        self.assertNotIn("solvemodel", body.lower())
        identity = common.identity()
        self.assertEqual(identity["extra_lp_queries"], 0)
        self.assertEqual(identity["extra_mip_queries"], 0)

    def test_08_no_v50_and_caps_are_bounded(self) -> None:
        freeze = common.load_json(common.OUT / "dataset_freeze.json")
        self.assertFalse(freeze["V50_allowed"])
        self.assertEqual(len(common.MECHANISM), 8)
        self.assertEqual(len(common.STAGE5), 15)
        self.assertFalse(any("v50" in row["path"].lower()
                             for row in freeze["instances"]))
        command = self.command()
        self.assertLessEqual(float(command[command.index(
            "--process-wall-time-limit") + 1]), common.MAX_PROCESS_CAP)

    def test_09_historical_comparator_hashes_are_real(self) -> None:
        manifest = common.csv_rows(
            common.OUT / "historical_baseline_reference_manifest.csv")
        self.assertGreater(len(manifest), 0)
        for row in manifest:
            artifact = ROOT / row["source_path"].split("#", 1)[0]
            self.assertTrue(artifact.is_file(), artifact)
            self.assertEqual(common.sha256(artifact), row["artifact_sha256"])
            item = self.items[row["instance"]]
            self.assertEqual(item["sha256"], row["input_sha256"])

    def test_10_completed_candidate_rows_are_sealed_one_executable(self) -> None:
        required = set(__import__("round48_experiment").REQUIRED)
        hashes = set()
        for marker_path in common.RUNS.glob("*/completion_marker.json"):
            marker = common.load_json(marker_path)
            self.assertTrue(marker["complete"])
            hashes.add(marker["executable_sha256"])
            names = {path.name for path in marker_path.parent.iterdir()
                     if path.is_file()}
            self.assertTrue(required <= names)
        self.assertLessEqual(len(hashes), 1)

    def test_11_offline_gate_result_closes_later_stages(self) -> None:
        audit = common.load_json(common.OUT / "amf_separation_audit.json")
        self.assertFalse(audit["primary_offline_gate_passed"])
        self.assertEqual(audit["structural_classification"],
                         "amf_partial_structural_separation")
        runner = (ROOT / "scripts" / "run_round48.py").read_text(
            encoding="utf-8")
        self.assertNotIn('"stage4"', runner)
        self.assertNotIn('"stage5"', runner)

    def test_12_counterfactuals_are_diagnostic_and_one_step(self) -> None:
        for arm in ("retain", "midpoint"):
            command = common.counterfactual_command(
                self.items[common.MECHANISM[4]], Path("diagnostic"),
                1200.0, "L0", arm, self.exe)
            self.assertEqual(command[command.index(
                "--round48-counterfactual-mode") + 1], arm)
            self.assertEqual(command[command.index(
                "--round48-counterfactual-interval") + 1], "L0")
            self.assertEqual(command[command.index("--round48-k1-amf") + 1],
                             "off")

    def test_13_official_command_uses_one_nondevelopment_hash(self) -> None:
        command = self.command()
        expected = common.sha256(self.exe)
        self.assertEqual(command[command.index(
            "--round24-executable-sha256") + 1], expected)
        self.assertNotIn("dev-gurobi-release", self.exe.as_posix().lower())

    def test_14_final_classifications_are_evidence_derived_when_present(self) -> None:
        path = common.OUT / "final_decision.json"
        if not path.is_file():
            self.skipTest("final decision is generated after Stage 3")
        value = common.load_json(path)
        self.assertTrue(value["derived_from_completed_evidence"])
        self.assertEqual(value["tau"], common.TAU)
        self.assertEqual(value["stage_rows"],
                         {"stage3": 8, "stage4": 0, "stage5": 0})
        self.assertTrue(value["offline_gate_failed"])
        self.assertGreater(len(value["evidence_sha256"]), 0)


if __name__ == "__main__":
    unittest.main()
