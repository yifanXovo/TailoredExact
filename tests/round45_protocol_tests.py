"""Protocol and evidence invariants for Round 45."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class Round45ProtocolTests(unittest.TestCase):
    def test_stage0_is_frozen_before_candidate_runs(self):
        manifest = load(OUT / "stage0_freeze_manifest.json")
        self.assertTrue(manifest["frozen_before_candidate_runs"])
        self.assertFalse(manifest["candidate_results_observed"])
        paths = {Path(row["path"]).name for row in manifest["artifacts"]}
        self.assertIn("material_classification.csv", paths)
        self.assertIn("complex_panel_freeze.json", paths)

    def test_material_classification_is_historical_only(self):
        with (OUT / "material_classification.csv").open(
                newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(24, len(rows))
        for row in rows:
            seconds = float(row["historical_pgrb_total_seconds"])
            expected = "material" if seconds >= 10 else "startup"
            actual = row["classification"]
            if actual == "startup_pathology":
                actual = "startup"
            self.assertEqual(expected, actual)
            self.assertEqual("True", row["frozen_before_candidate_runs"])

    def test_no_forbidden_decision_inputs(self):
        forbidden = load(OUT / "forbidden_decision_inputs.json")["forbidden"]
        score_path = (OUT / "runs" /
            "implementation_smoke__round39_small_easy_V10_M1_Q30_slot04_seed1099392856__k4_gamma_mid" /
            "timing_score_ledger.csv")
        with score_path.open(encoding="utf-8") as stream:
            header = next(csv.reader(stream))
        decision_fields = {field.lower() for field in header}
        disallowed_exact = {
            "instance name": "instance_name", "path": "path", "seed": "seed",
            "V": "v", "M": "m", "Q": "q", "panel membership": "panel",
            "historical winner": "historical_winner", "time": "time",
            "Work": "work", "nodes": "nodes", "iterations": "iterations",
            "memory": "memory", "hardware": "hardware",
            "learned policy": "learned_policy",
            "per-instance dispatch": "per_instance_dispatch",
        }
        for token in forbidden:
            self.assertNotIn(disallowed_exact[token], decision_fields)
        source = (ROOT / "src" / "GiniAdaptiveParametric.cpp").read_text(
            encoding="utf-8")
        self.assertNotIn("instance_id", source)
        self.assertNotIn("elapsed", source)

    def test_no_mixed_point_candidate_pool(self):
        source = (ROOT / "src" / "GiniAdaptiveParametric.cpp").read_text(
            encoding="utf-8")
        main = (ROOT / "src" / "PaperExternalGiniTree.cpp").read_text(
            encoding="utf-8")
        self.assertIn("selectParametricMaxMinPoint", source)
        self.assertIn("auditParametricRootSamples", source)
        self.assertNotIn("empirical_candidate", source.lower() + main.lower())
        contract = (OUT / "candidate_family_definition.md").read_text(
            encoding="utf-8").lower()
        self.assertIn("midpoint", contract)
        self.assertIn("pmm", contract)
        self.assertIn("fpmm", contract)

    def test_solver_contract_and_cap(self):
        contract = load(OUT / "solver_contract.json")
        self.assertEqual("Auto", contract["presolve"])
        self.assertEqual(0, contract["seed"])
        self.assertEqual(1, contract["threads"])
        self.assertEqual(0, contract["mip_gap"])
        self.assertEqual(0, contract["mip_gap_abs"])
        runner = (ROOT / "scripts" / "round45_experiment.py").read_text(
            encoding="utf-8")
        self.assertIn('default=3600.0', runner)
        self.assertIn('"--process-wall-time-limit"', runner)

    def test_validation_and_holdout_sealing(self):
        freeze = load(OUT / "small_dataset_freeze.json")
        self.assertEqual("sealed", freeze["validation_state"])
        self.assertEqual("sealed", freeze["holdout_state"])
        self.assertTrue(all(not row["candidate_results_observed"]
                            for row in freeze["datasets"] if row["sealed"]))

    def test_complex_panel_was_frozen(self):
        freeze = load(OUT / "complex_panel_freeze.json")
        self.assertTrue(freeze["frozen_before_candidate_runs"])
        self.assertFalse(freeze["candidate_results_observed"])
        self.assertGreaterEqual(len(freeze["v20_development"]), 3)
        self.assertGreaterEqual(len(freeze["v20_confirmation"]), 3)
        self.assertGreaterEqual(len(freeze["v50_development"]), 2)
        self.assertGreaterEqual(len(freeze["v50_confirmation"]), 2)

    def test_official_manifests_are_complete_and_invalidated_excluded(self):
        runs = OUT / "runs"
        for marker_path in runs.glob("*/completion_marker.json"):
            marker = load(marker_path)
            self.assertTrue(marker["complete"])
            run = marker_path.parent
            command = load(run / "command.json")
            self.assertFalse(command["invalidated"])
            with (run / "artifact_manifest.csv").open(
                    newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(marker["artifact_count"], len(rows))
            for row in rows:
                path = run / row["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(row["sha256"],
                    hashlib.sha256(path.read_bytes()).hexdigest())

    def test_terminal_classification_consistency(self):
        decision = OUT / "final_decision.json"
        if not decision.is_file():
            self.skipTest("final decision is created only after experiments")
        value = load(decision)
        self.assertIn(value["timing_classification"], {
            "validated_adaptive_timing", "adaptive_timing_small_only",
            "no_beneficial_recursive_split_evidence",
            "bounded_negative_timing_mechanism"})
        self.assertIn(value["point_classification"], {
            "validated_parametric_split_point", "parametric_point_small_only",
            "midpoint_not_improved", "bounded_negative_parametric_point"})
        if not value["validation"]["passed"]:
            self.assertEqual("not_opened", value["holdout"]["disposition"])

    def test_round45_default_off(self):
        instance = (ROOT / "include" / "Instance.hpp").read_text(
            encoding="utf-8")
        main = (ROOT / "src" / "main.cpp").read_text(encoding="utf-8")
        self.assertIn('round45_adaptive_parametric_partition = "off"', instance)
        self.assertIn('!= "off"', main)
        self.assertIn("round43_active || round44_active", main)

    def test_paper_preset_is_explicit_and_preserves_c6(self):
        main = (ROOT / "src" / "main.cpp").read_text(encoding="utf-8")
        self.assertIn('paper-gf-adaptive-gamma-veto', main)
        self.assertIn('opt.round45_timing_rule = "gamma-veto"', main)
        self.assertIn('opt.round45_rho_gamma = 0.012', main)
        self.assertIn('opt.round45_point_rule = "midpoint"', main)
        self.assertIn('opt.round45_initial_k0 = 4', main)
        self.assertIn('opt.algorithm_preset = "paper-gf-tailored-bc"', main)


if __name__ == "__main__":
    unittest.main()
