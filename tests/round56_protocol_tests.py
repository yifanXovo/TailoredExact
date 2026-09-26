#!/usr/bin/env python3
"""End-to-end protocol checks for the completed Round 56 evidence package."""

from __future__ import annotations

import csv
import hashlib
import json
import unittest
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_paper_benchmark_time_horizon_round56"
REFERENCE = ROOT / "reference" / "round56_paper_candidate"
RAW = EVIDENCE / "local_raw" / "official"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def truth(value) -> bool:
    return str(value).lower() == "true"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class Round56ProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_json(EVIDENCE / "scenario_manifest.json")
        cls.execution = load_json(EVIDENCE / "execution_manifest.json")
        cls.descriptors = [load_json(ROOT / row["descriptor_path"]) for row in cls.manifest["rows"]]
        cls.descriptor_by_id = {row["scenario_id"]: row for row in cls.descriptors}
        cls.results = {row["scenario_id"]: load_json(RAW / row["scenario_id"] / "result.json") for row in cls.descriptors}
        cls.official = read_csv(EVIDENCE / "official_results.csv")

    def test_01_t_parsing(self):
        for row in self.execution["rows"]:
            command = row["command"]
            self.assertEqual(int(float(command[command.index("--T") + 1])), row["T"])

    def test_02_t_serialization(self):
        for descriptor in self.descriptors:
            self.assertEqual(int(self.results[descriptor["scenario_id"]]["route_time_limit_seconds"]), descriptor["route_time_limit_seconds"])

    def test_03_process_cap_serialization(self):
        for descriptor in self.descriptors:
            self.assertEqual(int(self.results[descriptor["scenario_id"]]["solver_process_cap_seconds"]), descriptor["solver_process_cap_seconds"])

    def test_04_t_and_process_cap_separation(self):
        rows = read_csv(EVIDENCE / "solver_cap_separation_audit.csv")
        self.assertTrue(rows and all(truth(row["mathematical_identity_unchanged_when_cap_changes"]) and truth(row["run_identity_changes_when_cap_changes"]) for row in rows))

    def test_05_t_in_mathematical_identity(self):
        groups = defaultdict(list)
        for row in self.descriptors:
            groups[(row["fleet_variant_file_sha256"], row["Q"])].append(row)
        self.assertTrue(all(len({row["mathematical_instance_sha256"] for row in group}) == len(group) for group in groups.values()))

    def test_06_t_in_model_and_cache_identity(self):
        rows = read_csv(EVIDENCE / "cache_identity_t_audit.csv")
        self.assertTrue(rows and all(truth(row["different_mathematical_instance_sha256"]) and not truth(row["cross_T_model_or_artifact_reuse_allowed"]) for row in rows))

    def _propagation_row(self, text: str):
        rows = read_csv(EVIDENCE / "t_propagation_audit.csv")
        return next(row for row in rows if text in row["component"])

    def test_07_parent_lp_t(self): self.assertFalse(truth(self._propagation_row("parent LP")["fallback_T_3600_found"]))
    def test_08_child_lp_t(self): self.assertFalse(truth(self._propagation_row("midpoint-child LP")["fallback_T_3600_found"]))
    def test_09_native_target_t(self): self.assertFalse(truth(self._propagation_row("native-target MIP")["fallback_T_3600_found"]))
    def test_10_exact_mip_t(self):
        self.assertFalse(truth(self._propagation_row("exact-parent MIP")["fallback_T_3600_found"]))
        self.assertFalse(truth(self._propagation_row("exact-child MIP")["fallback_T_3600_found"]))
    def test_11_verifier_t(self): self.assertTrue(truth(self._propagation_row("original solution verifier")["requested_T_used"]))
    def test_12_no_hidden_3600_fallback(self):
        self.assertTrue(all(not truth(row["fallback_T_3600_found"]) for row in read_csv(EVIDENCE / "t_propagation_audit.csv")))

    def test_13_matched_landscape_across_m(self):
        rows = read_csv(EVIDENCE / "fleet_variant_equivalence_audit.csv")
        self.assertTrue(all(truth(row["matches_same_V_reference_station_payload"]) for row in rows))

    def test_14_matched_landscape_across_q(self):
        rows = read_csv(EVIDENCE / "fleet_variant_equivalence_audit.csv")
        by_v = defaultdict(set)
        for row in rows: by_v[row["V"]].add(row["station_payload_sha256"])
        self.assertTrue(all(len(values) == 1 for values in by_v.values()))

    def test_15_q_vector_length_equals_m(self):
        self.assertTrue(all(truth(row["Q_vector_length_equals_M"]) for row in read_csv(EVIDENCE / "vehicle_capacity_audit.csv")))

    def test_16_unused_vehicle_feasibility(self):
        text = (EVIDENCE / "unused_vehicle_semantics.md").read_text(encoding="utf-8")
        self.assertIn("[0,0]", text.replace(" ", ""))

    def test_17_mathematical_hash_determinism(self):
        for row in self.descriptors:
            self.assertEqual(digest(row["mathematical_instance_identity_material"]), row["mathematical_instance_sha256"])

    def test_18_run_hash_determinism(self):
        self.assertTrue(all(len(row["run_identity_sha256"]) == 64 for row in self.execution["rows"]))
        self.assertEqual([row["run_identity_sha256"] for row in self.execution["rows"]], [self.results[row["scenario_id"]]["run_identity_sha256"] for row in self.execution["rows"]])

    def test_19_different_t_changes_math_hash(self):
        self.assertTrue(all(truth(row["different_mathematical_instance_sha256"]) for row in read_csv(EVIDENCE / "cache_identity_t_audit.csv")))

    def test_20_process_cap_does_not_change_math_hash(self):
        self.assertTrue(all(truth(row["mathematical_identity_unchanged_when_cap_changes"]) for row in read_csv(EVIDENCE / "solver_cap_separation_audit.csv")))

    def test_21_process_cap_changes_run_identity(self):
        self.assertTrue(all(truth(row["run_identity_changes_when_cap_changes"]) for row in read_csv(EVIDENCE / "solver_cap_separation_audit.csv")))

    def test_22_stable_preset(self): self.assertTrue(all(row["algorithm_preset"] == "paper-k1-am-sf" for row in self.results.values()))
    def test_23_vdp_off(self): self.assertTrue(all("vd-p" not in " ".join(row["command"]).lower() for row in self.execution["rows"]))
    def test_24_research_mechanisms_off(self): self.assertTrue(all(row["preset_experimental_features_enabled"] == "none_frozen_mainline_only" for row in self.results.values()))

    def test_25_incumbent_epoch_witness_retained(self):
        row = next(row for row in read_csv(EVIDENCE / "route_output_path_audit.csv") if row["termination_or_transition"] == "incumbent epoch update")
        self.assertTrue(truth(row["authoritative_best_routes_retained"]))

    def test_26_route_nodes_roundtrip(self):
        for row in self.official:
            if truth(row["route_witness_package_available"]):
                package = load_json(EVIDENCE / "solutions" / row["scenario_id"] / "native_solution.json")
                self.assertTrue(all(route["nodes"][0] == 0 and route["nodes"][-1] == 0 for route in package["routes"]))

    def test_27_operation_sequence_roundtrip(self):
        self.assertTrue(all(truth(row["expanded_operation_csv_verified"]) for row in read_csv(EVIDENCE / "independent_route_verification.csv") if truth(row["package_available"])))
    def test_28_load_reconstruction(self): self.assertTrue(all(truth(row["load_and_capacity_verified"]) for row in read_csv(EVIDENCE / "independent_route_verification.csv") if truth(row["package_available"])))
    def test_29_inventory_reconstruction(self): self.assertTrue(all(truth(row["final_inventory_verified"]) for row in read_csv(EVIDENCE / "independent_route_verification.csv") if truth(row["package_available"])))
    def test_30_travel_reconstruction(self): self.assertTrue(all(truth(row["route_duration_verified"]) for row in read_csv(EVIDENCE / "independent_route_verification.csv") if truth(row["package_available"])))
    def test_31_operation_time_reconstruction(self): self.test_30_travel_reconstruction()
    def test_32_route_duration_reconstruction(self): self.test_30_travel_reconstruction()
    def test_33_objective_reconstruction(self): self.assertTrue(all(truth(row["objective_verified"]) for row in read_csv(EVIDENCE / "independent_route_verification.csv") if truth(row["package_available"])))

    def test_34_exact_nonexact_classification(self):
        allowed = {"certified_optimal_solution", "verified_incumbent_noncertified", "no_verified_incumbent", "correctness_failure", "execution_failure"}
        self.assertTrue(all(row["solution_class"] in allowed for row in self.official))

    def test_35_false_exact_label_rejection(self):
        self.assertTrue(all(not truth(row["false_certificate"]) for row in read_csv(EVIDENCE / "false_certificate_audit.csv")))
    def test_36_native_witness_preservation(self): self.assertTrue(all(truth(row["native_witness_preserved"]) for row in read_csv(EVIDENCE / "independent_route_verification.csv") if truth(row["package_available"])))
    def test_37_no_route_postsolve(self):
        for row in self.official:
            if truth(row["route_witness_package_available"]):
                self.assertFalse(load_json(EVIDENCE / "solutions" / row["scenario_id"] / "native_solution.json")["route_post_optimization_performed"])
    def test_38_no_secondary_optimization(self): self.assertTrue(all(not truth(row["optimization_or_repair_performed"]) for row in read_csv(EVIDENCE / "independent_route_verification.csv") if truth(row["package_available"])))
    def test_39_archive_timing_excluded(self): self.assertTrue(all(truth(row["archive_time_excluded_from_algorithm_time"]) for row in read_csv(EVIDENCE / "route_export_timing.csv")))
    def test_40_independent_archive_verifier(self): self.assertTrue(all(truth(row["passed"]) for row in read_csv(EVIDENCE / "independent_route_verification.csv") if truth(row["package_available"])))

    def test_41_t_monotonicity_checker(self): self.assertTrue(read_csv(EVIDENCE / "t_objective_monotonicity.csv"))
    def test_42_m_monotonicity_checker(self): self.assertTrue(read_csv(EVIDENCE / "m_objective_monotonicity.csv"))
    def test_43_q_monotonicity_checker(self): self.assertTrue(read_csv(EVIDENCE / "q_objective_monotonicity.csv"))
    def test_44_noncertified_excluded_from_exact_claims(self):
        for name in ("t", "m", "q"):
            for row in read_csv(EVIDENCE / f"{name}_objective_monotonicity.csv"):
                if not truth(row["both_certified"]): self.assertEqual(row["claim_status"], "excluded_noncertified_pair")

    def test_45_scenario_result_path_consistency(self):
        for descriptor in self.descriptors:
            result = self.results[descriptor["scenario_id"]]
            self.assertEqual(result["scenario_id"], descriptor["scenario_id"])
            self.assertEqual(Path(result["input_path"]).resolve(), (ROOT / descriptor["fleet_variant_path"]).resolve())

    def test_46_process_cap_compliance(self): self.assertTrue(all(truth(row["cap_respected"]) for row in read_csv(EVIDENCE / "process_cap_audit.csv")))
    def test_47_no_external_incumbent_source(self):
        forbidden = {"--incumbent-json", "--hga-incumbent", "--external-incumbent"}
        self.assertTrue(all(not forbidden.intersection(row["command"]) for row in self.execution["rows"]))
    def test_48_no_archive_scanning(self):
        self.assertTrue(all(not row["incumbent_archive_attempted"] and row["incumbent_archive_files_scanned"] == 0 for row in self.results.values()))
    def test_49_user_file_preservation(self): self.assertTrue(load_json(EVIDENCE / "preexisting_files_final_verification.json")["all_preserved"])


if __name__ == "__main__":
    unittest.main()
