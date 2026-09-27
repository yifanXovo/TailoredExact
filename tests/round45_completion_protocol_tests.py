#!/usr/bin/env python3
"""Protocol tests for the sealed Round 45 completion evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45"
OUT = ROUND / "completion"
MATRIX = OUT / "required_run_matrix.csv"
sys.path.insert(0, str(ROOT / "scripts"))


def load(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def truth(value) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes"}


class Round45CompletionProtocol(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = rows(MATRIX)
        cls.by_id = {row["row_id"]: row for row in cls.matrix}
        cls.directories = {row["row_id"]: ROUND / row["run_directory"]
                           for row in cls.matrix}
        cls.markers = {key: load(directory / "completion_marker.json")
                       for key, directory in cls.directories.items()}
        cls.commands = {key: load(directory / "command.json")
                        for key, directory in cls.directories.items()}
        cls.results = {key: load(directory / "result.json")
                       for key, directory in cls.directories.items()}
        cls.decision = load(OUT / "final_decision.json")

    def test_01_matrix_is_amended_and_complete(self):
        self.assertEqual(232, len(self.matrix))
        self.assertEqual(232, len(self.by_id))
        self.assertTrue(all(truth(marker["complete"]) for marker in self.markers.values()))
        self.assertEqual("complete", self.decision["round45_completion_status"])

    def test_02_all_markers_use_one_actual_executable_hash(self):
        hashes = {marker["executable_sha256"] for marker in self.markers.values()}
        self.assertEqual(1, len(hashes))
        executable = ROOT / "build_round45_completion" / "ExactEBRP.exe"
        self.assertEqual(next(iter(hashes)), digest(executable))

    def test_03_artifact_manifests_are_hash_valid(self):
        for row_id, directory in self.directories.items():
            manifest = directory / "artifact_manifest.csv"
            self.assertEqual(digest(manifest),
                             self.markers[row_id]["artifact_manifest_sha256"])
            for entry in rows(manifest):
                path = directory / entry["path"]
                self.assertTrue(path.is_file(), f"{row_id}: {entry['path']}")
                self.assertEqual(int(entry["size_bytes"]), path.stat().st_size)
                self.assertEqual(entry["sha256"], digest(path))

    def test_04_official_commands_use_actual_3600_caps_and_one_thread(self):
        for row_id, command in self.commands.items():
            args = command["command"]
            option = lambda name: args[args.index(name) + 1]
            self.assertEqual(3600.0, float(option("--time-limit")), row_id)
            self.assertEqual(3600.0, float(option("--process-wall-time-limit")), row_id)
            self.assertEqual(1, int(option("--threads")), row_id)
            self.assertEqual(1, int(option("--mip-threads")), row_id)
            self.assertTrue(truth(command["sequential_official_execution"]), row_id)

    def test_05_every_terminal_is_exact_or_honestly_capped(self):
        for row_id, marker in self.markers.items():
            terminal = (truth(marker["strict_certificate"]) or
                        truth(marker["local_parent_exact"]) or
                        truth(marker["honest_required_cap"]))
            self.assertTrue(terminal, row_id)
            if truth(marker["honest_required_cap"]):
                self.assertGreaterEqual(float(marker["process_seconds"]), 3570.0, row_id)

    def test_06_capped_rows_have_all_common_horizon_checkpoints(self):
        for row_id, marker in self.markers.items():
            checkpoints = rows(self.directories[row_id] / "common_horizon_trace.csv")
            self.assertEqual({300, 1200, 3600},
                             {int(float(row["horizon_seconds"])) for row in checkpoints})
            if truth(marker["honest_required_cap"]):
                for point in checkpoints:
                    self.assertNotEqual("", point["lower_bound"], row_id)
                    self.assertNotEqual("", point["verified_upper_bound"], row_id)
                    self.assertNotEqual("", point["normalized_gap_integral"], row_id)

    def test_07_counterfactual_retain_and_split_geometry_is_real(self):
        for row in self.matrix:
            if "counterfactual" not in row["stage"]:
                continue
            audit = load(self.directories[row["row_id"]] /
                         "counterfactual_validity.json")
            self.assertTrue(truth(audit["counterfactual_valid"]), row["row_id"])
            if row["arm"] == "retain":
                self.assertTrue(truth(audit["retain_zero_split_valid"]), row["row_id"])
            else:
                self.assertTrue(truth(audit["one_split_event_valid"]), row["row_id"])
                self.assertEqual(2, int(audit["child_count"]), row["row_id"])
                self.assertTrue(truth(audit["exact_two_child_union"]), row["row_id"])

    def test_08_matched_counterfactual_parent_identity(self):
        grouped = defaultdict(set)
        for row in self.matrix:
            if "counterfactual" not in row["stage"]:
                continue
            state = load(self.directories[row["row_id"]] / "parent_state.json")
            key = (row["stage"], row["instance"], row["K0"], row["parent_id"])
            grouped[key].add(state["parent_canonical_model_sha256"])
        self.assertEqual(32, len(grouped))
        self.assertTrue(all(len(values) == 1 for values in grouped.values()))

    def test_09_every_gamma_split_parent_has_midpoint_pmm_fpmm(self):
        parents = rows(OUT / "true_counterfactual_parent_manifest.csv")
        pairs = rows(OUT / "true_counterfactual_pair_summary.csv")
        pair_keys = {(row["stage"], row["instance"], row["K0"], row["parent_id"])
                     for row in pairs}
        for parent in parents:
            split = (parent["old_c6_action"].lower() == "split" and
                     float(parent["Gamma_sum"]) >= 0.012)
            if split:
                key = (parent["stage"], parent["instance"], parent["K0"],
                       parent["parent_id"])
                self.assertIn(key, pair_keys)
                self.assertTrue(truth(parent["all_four_arms_present"]))

    def test_10_parametric_split_points_are_certified(self):
        validity = rows(OUT / "counterfactual_validity_audit.csv")
        for row in validity:
            if row["arm"] in {"pmm-split", "fpmm-split"}:
                self.assertTrue(truth(row["point_certified"]), row["row_id"])
                self.assertEqual(1, int(row["split_count"]), row["row_id"])

    def test_11_validation_and_holdout_are_not_used_for_selection(self):
        for row in self.matrix:
            if row["stage"] in {"post_selection_counterfactual",
                                "small_panel_rerun_validation",
                                "small_panel_rerun_holdout"}:
                self.assertFalse(truth(row["selection_use"]), row["row_id"])
        source = (ROOT / "scripts" / "finalize_round45.py").read_text(encoding="utf-8")
        self.assertIn("0.012", source)
        self.assertIn("0.10", source)

    def test_12_no_false_beneficial_labels(self):
        pairs = rows(OUT / "true_counterfactual_pair_summary.csv")
        for row in pairs:
            if row["label"] == "beneficial":
                self.assertTrue(truth(row["retain_exact"]))
                self.assertTrue(truth(row["midpoint_exact"]))
                self.assertLessEqual(float(row["midpoint_work"]),
                                     0.85 * float(row["retain_work"]))

    def test_13_classification_is_evidence_gated(self):
        audit = load(OUT / "classification_gate_audit.json")
        self.assertEqual(self.decision, audit)
        self.assertTrue(truth(self.decision["matrix_gate"]["pass"]))
        self.assertTrue(truth(self.decision["counterfactual_gate"]["pass"]))
        self.assertTrue(truth(self.decision["complex_gate"]["pass"]))
        self.assertTrue(truth(self.decision["small_panel_rerun_gate"]))

    def test_14_complex_matrix_and_secondary_rows_are_complete(self):
        complex_gate = load(OUT / "complex_gate_audit.json")
        self.assertEqual(48, int(complex_gate["mandatory_completed"]))
        self.assertEqual(6, int(complex_gate["secondary_completed"]))
        self.assertTrue(truth(complex_gate["pass"]))

    def test_15_default_off_and_deterministic_equivalence_pass(self):
        audit = rows(OUT / "default_off_equivalence.csv")
        self.assertGreaterEqual(len(audit), 2)
        self.assertTrue(all(truth(row["pass"]) for row in audit))

    def test_16_paper_facing_adaptive_preset_remains_experimental(self):
        source = (ROOT / "src" / "main.cpp").read_text(encoding="utf-8")
        self.assertIn('research-gf-adaptive-gamma-veto', source)
        self.assertIn('preset == "paper-gf-adaptive-gamma-veto"', source)
        self.assertNotIn('"paper-gf-adaptive-gamma-veto",\n',
                         source[source.find("paper_trace_presets"):])


if __name__ == "__main__":
    unittest.main(verbosity=2)
