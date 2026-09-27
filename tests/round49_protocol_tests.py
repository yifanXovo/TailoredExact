#!/usr/bin/env python3
"""Protocol tests for the frozen, bounded Round 49 K1-AM-RC study."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import round49_common as common  # noqa: E402


class Round49ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.exe = Path(os.environ.get("EXACTEBRP_ROUND49_EXE", common.EXE))
        if not cls.exe.is_file():
            raise RuntimeError(f"official Round 49 executable missing: {cls.exe}")
        cls.items = common.frozen_instances()

    def command(self, instance: str | None = None) -> list[str]:
        with tempfile.TemporaryDirectory(dir=ROOT / "build") as temporary:
            run_dir = Path(temporary) / "row"
            return common.candidate_command(
                self.items[instance or common.MECHANISM[0]], run_dir,
                300.0, self.exe, "d-rcd")

    def test_01_stage0_precedes_diagnostics_and_hashes_verify(self) -> None:
        manifest_path = common.OUT / "stage0_freeze_manifest.json"
        manifest = common.load_json(manifest_path)
        self.assertTrue(
            manifest["frozen_before_new_diagnostic_or_candidate_runtime"])
        self.assertFalse(manifest["candidate_runtime_started"])
        self.assertEqual(len(manifest["required_files"]), 12)
        for row in manifest["required_files"]:
            path = common.OUT / row["path"]
            self.assertTrue(path.is_file())
            self.assertEqual(common.sha256(path), row["sha256"])
        registry = manifest["additional_pre_census_registry"]
        self.assertEqual(common.sha256(common.OUT / registry["path"]),
                         registry["sha256"])

    def test_02_design_iterations_and_rule_menu_are_bounded(self) -> None:
        policy = common.load_json(common.OUT / "bounded_iteration_policy.json")
        freeze = common.load_json(common.OUT / "candidate_rule_freeze.json")
        self.assertEqual(policy["max_offline_design_iterations"], 2)
        self.assertEqual(policy["max_stage3_rule_revisions"], 1)
        self.assertLessEqual(freeze["offline_iterations_used"], 2)
        self.assertLessEqual(len(freeze["candidates"]), 2)
        self.assertTrue(freeze["no_post_freeze_formula_invention"])
        self.assertFalse(freeze["stage3_revision_used"])

    def test_03_only_frozen_k1_d_rcd_candidate(self) -> None:
        identity = common.identity()
        self.assertEqual(identity["algorithm"], "K1-AM-RC-A")
        self.assertEqual(identity["K0"], 1)
        self.assertEqual(identity["rule"], "d-rcd")
        self.assertEqual(identity["tau"], common.TAU)
        self.assertEqual(identity["point_rule"], "midpoint")
        runner = (ROOT / "scripts" / "run_round49.py").read_text(
            encoding="utf-8")
        self.assertNotIn("K4-AM-RC", runner)
        self.assertNotIn('"stage4"', runner)
        self.assertNotIn('"stage5"', runner)

    def test_04_candidate_command_is_exact_frozen_mode(self) -> None:
        command = self.command()
        self.assertEqual(command[command.index("--round49-k1-am-rc") + 1],
                         "d-rcd")
        self.assertEqual(command[command.index("--round48-k1-amf") + 1],
                         "off")
        self.assertEqual(command[command.index(
            "--round47-c6-adaptive-mass") + 1], "adaptive-mass")
        self.assertEqual(float(command[command.index(
            "--round47-c6-adaptive-mass-tau") + 1]), common.TAU)
        self.assertEqual(command[command.index(
            "--round40-c6-coarse-start") + 1], "k1-adaptive")
        self.assertEqual(command[command.index(
            "--round45-point-rule") + 1], "midpoint")

    def test_05_forbidden_mechanisms_are_off(self) -> None:
        command = self.command()
        for option in (
                "--round43-envelope-refinement", "--round43-lifted-cuts",
                "--round43-frontier-consolidation",
                "--round44-envelope-tail-repair", "--round44-rank1-cuts",
                "--round44-mip-starts", "--round44-frontier-consolidation",
                "--round45-adaptive-parametric-partition"):
            self.assertEqual(command[command.index(option) + 1], "off")
        self.assertNotIn("--c6-normalized-split-threshold", command)
        lowered = " ".join(command).lower()
        for forbidden in ("gamma-veto", "fpmm", "pmm", "rho-cap",
                          "root-processing"):
            self.assertNotIn(forbidden, lowered)

    def test_06_registry_is_semantic_and_excludes_auxiliaries(self) -> None:
        registry = common.load_json(
            common.OUT / "primitive_integer_variable_registry.json")
        families = {
            row["family"] for row in registry["included_family_rules"]}
        self.assertEqual(families, {row[0] for row in common.PRIMITIVE_FAMILIES})
        excluded = " ".join(
            pattern for row in registry["always_excluded"]
            for pattern in row["patterns"])
        for pattern in ("bit_*", "prod_*", "G"):
            self.assertIn(pattern, excluded)
        self.assertNotIn("W_GS", {
            row["prefix"] for row in registry["included_family_rules"]})
        self.assertFalse(registry["post_outcome_selection_allowed"])

    def test_07_no_new_parameter_or_family_weight(self) -> None:
        identity = common.identity()
        self.assertFalse(identity["new_continuous_rescue_threshold"])
        self.assertFalse(identity["family_weights"])
        self.assertFalse(identity["learned_coefficients"])
        self.assertFalse(identity["size_depth_width_rule"])
        self.assertEqual(identity["tau"], 0.07915)
        source = (ROOT / "src" / "Round49K1RC.cpp").read_text(
            encoding="utf-8").lower()
        self.assertNotIn("optimize(", source)
        self.assertNotIn("backend->solve", source)
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
            self.assertEqual(self.items[row["instance"]]["sha256"],
                             row["input_sha256"])

    def test_10_offline_failure_closes_stage4_and_stage5(self) -> None:
        audit = common.load_json(common.OUT / "rc_rule_separation_audit.json")
        self.assertFalse(audit["primary_offline_gate_passed"])
        self.assertEqual(audit["structural_classification"],
                         "rc_domain_partial_separation")
        freeze = common.load_json(common.OUT / "candidate_rule_freeze.json")
        self.assertTrue(freeze["candidates"][0]["bounded_diagnostic_only"])

    def test_11_completed_rows_are_sealed_one_executable(self) -> None:
        required = set(__import__("round49_experiment").REQUIRED)
        hashes = set()
        for marker_path in common.RUNS.glob("*/completion_marker.json"):
            marker = common.load_json(marker_path)
            self.assertTrue(marker["complete"])
            hashes.add(marker["executable_sha256"])
            names = {path.name for path in marker_path.parent.iterdir()
                     if path.is_file()}
            self.assertTrue(required <= names)
            self.assertEqual(marker["extra_lp_count"], 0)
            self.assertEqual(marker["extra_mip_count"], 0)
        self.assertLessEqual(len(hashes), 1)

    def test_12_official_command_uses_one_nondevelopment_hash(self) -> None:
        command = self.command()
        expected = common.sha256(self.exe)
        self.assertEqual(command[command.index(
            "--round24-executable-sha256") + 1], expected)
        self.assertNotIn("dev-gurobi-release", self.exe.as_posix().lower())

    def test_13_final_classifications_are_evidence_derived_when_present(self) -> None:
        path = common.OUT / "final_decision.json"
        if not path.is_file():
            self.skipTest("final decision is generated after Stage 3")
        value = common.load_json(path)
        self.assertTrue(value["derived_from_completed_evidence"])
        self.assertEqual(value["tau"], common.TAU)
        self.assertEqual(value["stage_rows"],
                         {"stage3": 8, "stage4": 0, "stage5": 0})
        self.assertTrue(value["offline_gate_failed"])
        self.assertEqual(value["stage3_revision_used"], False)
        self.assertGreater(len(value["evidence_sha256"]), 0)


if __name__ == "__main__":
    unittest.main()
