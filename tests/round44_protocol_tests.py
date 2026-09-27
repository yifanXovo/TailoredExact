#!/usr/bin/env python3
"""Protocol invariants for the Round 44 C6-compatible tail-repair round."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_envelope_tail_repair_round44"
RUNS = OUT / "runs"
sys.path.insert(0, str(ROOT / "scripts"))
import round44_common as common  # noqa: E402


def load(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def repository_text_sha256(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class Round44ProtocolTests(unittest.TestCase):
    def test_stage0_is_frozen_before_candidate_runs(self) -> None:
        freeze = load("stage0_freeze_manifest.json")
        self.assertTrue(freeze["frozen_before_candidate_exact_runs"])
        self.assertFalse(freeze["candidate_results_observed"])
        self.assertEqual(freeze["base_sha"], common.BASE_SHA)
        self.assertEqual(freeze["base_tree_sha"], common.BASE_TREE_SHA)
        for row in freeze["artifacts"]:
            path = ROOT / row["path"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(repository_text_sha256(path), row["sha256"], path)
        if RUNS.exists():
            run_dirs = [path for path in RUNS.iterdir() if path.is_dir()]
            freeze_mtime = (OUT / "stage0_freeze_manifest.json").stat().st_mtime
            for run_dir in run_dirs:
                command = run_dir / "command.json"
                self.assertTrue(command.is_file(), run_dir)
                self.assertGreaterEqual(command.stat().st_mtime, freeze_mtime)
                self.assertNotEqual(
                    json.loads(command.read_text(encoding="utf-8")).get(
                        "stage"), "stage0")

    def test_round43_erratum_is_precise_and_nonhistorical(self) -> None:
        erratum = (OUT / "round43_formula_erratum.md").read_text(
            encoding="utf-8")
        self.assertIn("D_R43(I) = V_residual(I) /", erratum)
        self.assertIn("P_profile(I) = V_residual(I)", erratum)
        self.assertIn("require\nno rerun", erratum)
        self.assertIn("lifted cuts were not tested", erratum)
        self.assertIn("Historical raw result and decision", erratum)

    def test_dataset_split_is_complete_and_sealed(self) -> None:
        freeze = load("dataset_freeze.json")
        datasets = freeze["datasets"]
        by_split: dict[str, list[dict]] = {}
        for row in datasets:
            by_split.setdefault(row["split"], []).append(row)
            self.assertFalse(row["candidate_results_observed"])
            path = ROOT / row["path"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(common.sha256(path), row["sha256"])
        self.assertEqual(len(by_split["development"]), 10)
        self.assertEqual(len(by_split["validation"]), 7)
        self.assertEqual(len(by_split["sealed_holdout"]), 7)
        self.assertEqual(len(by_split["additional_v12"]), 2)
        self.assertEqual(len(by_split["v20_development_profile"]), 3)
        self.assertEqual(len(by_split["v20_confirmation"]), 3)
        self.assertEqual(freeze["validation_state"], "sealed")
        self.assertEqual(freeze["holdout_state"], "sealed")

    def test_solver_contract_is_fair_and_exact(self) -> None:
        contract = load("solver_contract.json")
        self.assertEqual(contract["threads"], 1)
        self.assertEqual(contract["seed"], 0)
        self.assertEqual(contract["presolve_value"], -1)
        self.assertEqual(contract["relative_mip_gap"], 0.0)
        self.assertEqual(contract["absolute_mip_gap"], 0.0)
        self.assertEqual(contract["gurobi_version"], "13.0.2")

    def test_performance_metrics_are_frozen_from_baselines(self) -> None:
        freeze = load("performance_metric_freeze.json")
        self.assertTrue(freeze["frozen_before_candidate_exact_runs"])
        self.assertFalse(freeze["candidate_results_observed"])
        self.assertEqual(freeze["startup_time_shift_seconds"], 1.0)
        self.assertEqual(freeze["startup_work_shift"], 1.0)
        self.assertEqual(len(freeze["startup_audit"]), 24)
        self.assertTrue(all(
            "plain_gurobi_optimize_launch" not in row["source"]
            for row in freeze["startup_audit"]))

    def test_promotion_gates_are_pgrb_oriented(self) -> None:
        gates = load("promotion_gates.json")
        self.assertEqual(gates["major_candidate_over_pgrb_work_max"], 1.05)
        self.assertEqual(gates["major_candidate_over_pgrb_time_max"], 1.05)
        self.assertEqual(gates["development_shifted_work_gmean_max"], 0.90)
        self.assertEqual(gates["development_shifted_time_gmean_max"], 0.95)
        self.assertEqual(
            gates["candidate_retained_advantage_pgrb_over_candidate_work_min"],
            2.0)
        self.assertNotIn("candidate_over_c6_universal_max", gates)

    def test_forbidden_inputs_and_telemetry_hash_exclusion(self) -> None:
        audit = load("forbidden_decision_inputs.json")
        forbidden = set(audit["forbidden"])
        self.assertTrue({
            "instance_name", "random_seed", "elapsed_time", "gurobi_work",
            "node_count", "memory", "dataset_membership",
        }.issubset(forbidden))
        self.assertTrue(audit["telemetry_excluded_from_decision_hash"])

    def test_baseline_default_off_sentinels_are_preserved(self) -> None:
        audit = rows("baseline_equivalence_manifest.csv")
        sentinels = [row for row in audit
                     if row["kind"] == "round43_default_off_sentinel"]
        self.assertEqual(len(sentinels), 3)
        self.assertTrue(all(common.truth(row["equivalence_passed"])
                            for row in sentinels))

    def test_failed_candidates_are_not_promoted_to_a_paper_preset(self) -> None:
        source = (ROOT / "src" / "main.cpp").read_text(encoding="utf-8")
        self.assertNotIn("paper-gf-c6-envelope-tail-repair", source)

    def test_both_pre_frozen_validation_candidates_failed(self) -> None:
        primary = load("validation_disposition.json")
        fallback = load("validation_fallback_disposition.json")
        self.assertFalse(primary["passes_all_gates"])
        self.assertFalse(fallback["passes_all_gates"])
        self.assertEqual(primary["candidate"], "noadaptive")
        self.assertEqual(fallback["candidate"], "veto-f05")
        frozen = load("final_candidate_freeze.json")
        activated = load("fallback_candidate_activation_freeze.json")
        expected = next(row for row in frozen["pre_frozen_validation_fallbacks"]
                        if row["tag"] == "veto-f05")
        self.assertEqual(expected["decision_identity_sha256"],
                         activated["configuration"]["decision_identity_sha256"])
        self.assertTrue(activated["frozen_before_fallback_validation"])

    def test_negative_terminal_keeps_downstream_panels_sealed(self) -> None:
        gate = load("qualification_terminal_gate.json")
        self.assertEqual(gate["terminal_classification"],
                         "bounded_systematic_negative_result")
        self.assertEqual(gate["scale_qualification"], "small_panel_only")
        self.assertEqual(gate["promotion"], "none")
        self.assertFalse(gate["holdout_opened"])
        self.assertFalse(gate["additional_v12_opened"])
        self.assertFalse(gate["v20_opened"])

    def test_final_decision_and_build_record_are_consistent(self) -> None:
        decision = load("final_decision.json")
        build = load("final_test_record.json")
        self.assertEqual(decision["terminal_classification"],
                         "bounded_systematic_negative_result")
        self.assertIsNone(decision["selected_candidate"])
        self.assertIsNone(decision["paper_preset"])
        self.assertEqual(build["executable_sha256"], common.sha256(common.EXE))
        self.assertEqual(build["ctest_passed"], build["ctest_total"])


if __name__ == "__main__":
    unittest.main()
