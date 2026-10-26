#!/usr/bin/env python3
"""End-to-end protocol tests for the bounded Round 50 study."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
FIXED_RUNS = OUT / "official_confirmation" / "v0"
COUNTERFACTUAL_RUNS = OUT / "counterfactual_runs"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def truth(value: object) -> bool:
    return str(value).lower() in {"1", "true", "yes"}


class Round50ProtocolTests(unittest.TestCase):
    def test_01_stage0_was_frozen_and_hashes_still_verify(self) -> None:
        freeze = load_json(OUT / "stage0_freeze_manifest.json")
        self.assertTrue(freeze["frozen_before_new_optimization_runtime_or_result_inspection"])
        self.assertFalse(freeze["candidate_runtime_started"])
        self.assertEqual(freeze["maximum_iterations"], 4)
        self.assertEqual(freeze["maximum_process_cap_seconds"], 1800)
        self.assertTrue(freeze["V50_forbidden"])
        for item in freeze["required_files"]:
            path = OUT / item["path"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(sha256(path), item["sha256"], path)

    def test_02_all_frozen_state_identities_reconstruct(self) -> None:
        manifest = rows(OUT / "fixed_interval_state_manifest.csv")
        audit = rows(OUT / "fixed_interval_state_reconstruction_audit.csv")
        self.assertEqual(len(manifest), 23)
        self.assertEqual(len(audit), 23)
        self.assertEqual({row["state_id"] for row in manifest},
                         {f"D{i}" for i in range(1, 15)} |
                         {f"C{i}" for i in range(1, 10)})
        for row in audit:
            self.assertEqual(row["reconstruction_status"], "complete", row)
            self.assertTrue(truth(row["cutoff_reconstruction_verified"]), row)
            self.assertEqual(row["objective_sense"], "minimize", row)
            self.assertEqual(row["canonical_model_fingerprint"],
                             row["row_bound_signature"], row)
            self.assertEqual(int(row["mapped_variable_count"]),
                             int(row["original_columns"]), row)
            self.assertTrue(row["original_variable_mapping_sha256"], row)

    def test_03_fixed_driver_has_complete_required_logging(self) -> None:
        required = {
            "command.json", "state_identity.json", "model_fingerprint.json",
            "result.json", "mip_progress.csv", "root_processing_ledger.csv",
            "presolve_ledger.csv", "branching_policy_ledger.csv",
            "cut_family_ledger.csv", "formulation_size_ledger.csv",
            "numerical_quality_ledger.csv", "model_reuse_ledger.csv",
            "certificate_ledger.csv", "artifact_manifest.csv",
            "completion_marker.json",
        }
        self.assertEqual(len(list(FIXED_RUNS.glob("*/completion_marker.json"))), 23)
        for marker_path in FIXED_RUNS.glob("*/completion_marker.json"):
            self.assertTrue(required <= {p.name for p in marker_path.parent.iterdir()
                                         if p.is_file()}, marker_path.parent)

    def test_04_objective_cutoff_and_mapping_contract_is_preserved(self) -> None:
        protocol = load_json(OUT / "fixed_interval_state_protocol.json")
        solver = load_json(OUT / "solver_contract.json")
        self.assertIn("complete_objective", protocol["identity_fields"])
        self.assertEqual(solver["objective_sense"], "minimize")
        self.assertEqual(float(solver["certificate_tolerance"]), 1e-7)
        self.assertFalse(solver["known_optimum_injection"])
        self.assertFalse(solver["archive_winner_injection"])
        for row in rows(OUT / "fixed_interval_confirmation_results.csv"):
            self.assertTrue(truth(row["model_identity_match"]), row["state_id"])
            self.assertEqual(row["lower_bound"], row["lower_bound"].strip())
            self.assertEqual(row["verified_upper_bound"],
                             row["verified_upper_bound"].strip())

    def test_05_branching_registry_priorities_and_default_are_deterministic(self) -> None:
        decision = load_json(OUT / "branching_iteration_decision.json")
        self.assertEqual(decision["classification"], "default_branching_retained")
        self.assertEqual(len(decision["candidate_decisions"]), 3)
        self.assertEqual(decision["priority_assignment_failures"], 0)
        registry = rows(OUT / "fixed_interval_semantic_registry_audit.csv")
        self.assertGreater(len(registry), 0)
        self.assertTrue(all(truth(row["semantic_registry_complete"])
                            for row in registry))
        source = (ROOT / "src" / "Round50IntervalMip.cpp").read_text(
            encoding="utf-8")
        self.assertIn("Round50BranchingPolicy::Default) return 0", source)

    def test_06_row_registry_is_complete_and_core_rows_are_protected(self) -> None:
        registry = rows(OUT / "cut_and_row_family_registry.csv")
        families = {row["family"] for row in registry}
        for expected in (
            "inventory_conservation", "movement_reachability",
            "visit_inventory_linking", "handling_capacity",
            "support_duration", "transfer_compatibility", "direct_gini_cap_floor",
            "interval_tight_mccormick", "objective_estimator_cutoff",
            "penalty_lower_bound_closure", "gini_spread", "required_movement",
            "low_gini_centering", "variable_s_centering", "sp_product_estimator",
        ):
            self.assertIn(expected, families)
        protected = {"core feasibility/model-definition", "exact reformulation"}
        self.assertTrue(all(truth(row["core_row_protected"])
                            for row in registry
                            if row["classification"] in protected))

    def test_07_duplicate_cut_and_tightening_correctness_is_honest(self) -> None:
        decision = load_json(OUT / "cut_formulation_iteration_decision.json")
        self.assertEqual(decision["classification"], "original_cut_pack_retained")
        self.assertEqual(decision["candidate_count"], 1)
        self.assertEqual(decision["false_certificates"], 0)
        self.assertEqual(decision["correctness_failures"], 1)
        audit = rows(OUT / "c1_model_correctness_audit.csv")
        self.assertTrue(all(row["status"] == "pass" and
                            truth(row["feasible_set_and_objective_invariant"])
                            for row in audit))
        numerical = rows(OUT / "numerical_candidate_results.csv")[0]
        self.assertFalse(truth(numerical["entered"]))
        self.assertEqual(numerical["decision"], "no_exact_candidate")

    def test_08_exact_symmetry_preserves_a_representative_but_was_rejected(self) -> None:
        decision = load_json(OUT / "symmetry_numerical_iteration_decision.json")
        self.assertEqual(decision["symmetry_candidates"], 2)
        self.assertEqual(decision["model_delta_audit_failures"], 0)
        self.assertEqual(decision["classification"],
                         "original_symmetry_policy_retained")
        report = (OUT / "symmetry_validity_report.md").read_text(encoding="utf-8")
        self.assertIn("representative from every orbit", report.lower())
        self.assertIn("identical", report.lower())

    def test_09_lp_to_mip_reuse_was_not_opened_without_a_solved_lp_object(self) -> None:
        decision = load_json(OUT / "model_reuse_iteration_decision.json")
        self.assertEqual(decision["classification"], "model_reuse_not_opened")
        self.assertFalse(decision["candidate_entered"])
        self.assertEqual(decision["screen_rows"], 0)
        audit = rows(OUT / "model_reuse_correctness_audit.csv")
        changed = next(row for row in audit
                       if row["audit_item"] == "mathematical_model_changed")
        leakage = next(row for row in audit
                       if row["audit_item"] == "interval_local_cut_leakage")
        self.assertFalse(truth(changed["observed"]))
        self.assertFalse(truth(leakage["observed"]))

    def test_10_fixed_certificates_coverage_and_zero_gap_are_audited(self) -> None:
        certificate = rows(OUT / "certificate_audit.csv")
        fixed = [row for row in certificate if row["scope"] == "fixed_state"]
        self.assertEqual(len(fixed), 23)
        self.assertEqual(sum(truth(row["strict_certificate"]) for row in fixed), 17)
        self.assertFalse(any(truth(row["false_certificate"]) for row in fixed))
        self.assertTrue(all(truth(row["evidence_complete"]) for row in fixed))

    def test_11_vnext_default_off_is_exactly_v0_for_all_fixed_states(self) -> None:
        equivalence = rows(OUT / "default_off_equivalence.csv")
        self.assertEqual(len(equivalence), 23)
        self.assertTrue(all(truth(row["critical_fields_equal"])
                            for row in equivalence))
        self.assertTrue(all(truth(row["physical_run_shared"])
                            for row in equivalence))
        definition = load_json(OUT / "interval_mip_vnext_definition.json")
        self.assertEqual(definition["definition_equivalence"], "Interval-MIP-v0")
        self.assertEqual(definition["accepted_modification_count"], 0)

    def test_12_k1_controller_equivalence_and_ordered_gate(self) -> None:
        audit = load_json(OUT / "k1_backend_promotion_audit.json")
        self.assertEqual(audit["classification"], "historical_k1_am_retained")
        self.assertFalse(audit["integration_eligible"])
        self.assertEqual(audit["physical_rows"], {"300s": 0, "1200s": 0,
                                                  "1800s": 0})
        self.assertFalse(audit["research_mode_added"])
        report = (OUT / "split_tail_repair_report.md").read_text(encoding="utf-8")
        self.assertIn("Gate 2 fails", report)

    def test_13_no_forbidden_runtime_or_process_metric_dispatch(self) -> None:
        audit = (OUT / "no_instance_dispatch_audit.md").read_text(
            encoding="utf-8")
        self.assertIn("PASS", audit)
        source = "\n".join((ROOT / path).read_text(encoding="utf-8")
                            for path in ("include/Round50IntervalMip.hpp",
                                         "src/Round50IntervalMip.cpp"))
        for forbidden in ("seed1343324363", "tight_T_seed", "V20_M3",
                          "machine_identity", "historical_winner"):
            self.assertNotIn(forbidden, source)
        self.assertNotIn("elapsed", source.lower())
        self.assertNotIn("node", source.lower())
        self.assertNotIn("memory", source.lower())

    def test_14_iteration_count_candidates_families_and_tuning_are_bounded(self) -> None:
        policy = load_json(OUT / "bounded_iteration_policy.json")
        self.assertEqual(policy["maximum_iterations"], 4)
        plans = [load_json(OUT / f"iteration_{i}_plan.json") for i in range(1, 5)]
        self.assertEqual(len(plans), 4)
        families = [plans[i].get("principal_family", plans[i].get("mechanism"))
                    for i in range(4)]
        self.assertEqual(len(set(families)), 4)
        candidate_counts = (
            plans[0]["candidate_count"], plans[1]["maximum_candidates"],
            plans[2]["maximum_candidates"], plans[3]["candidate_cap"])
        self.assertTrue(all(count <= 3 for count in candidate_counts))
        for name in ("branching_iteration_decision.json",
                     "cut_formulation_iteration_decision.json",
                     "symmetry_numerical_iteration_decision.json",
                     "model_reuse_iteration_decision.json"):
            self.assertFalse(load_json(OUT / name).get("confirmation_opened", False))

    def test_15_official_rows_share_one_policy_specific_executable(self) -> None:
        fixed = rows(OUT / "fixed_interval_confirmation_results.csv")
        self.assertEqual({row["executable_sha256"] for row in fixed},
                         {"85a6404acb015ea71e1b56a656f85665cda46b1f72a29a7174e6f48d96f8e81a"})
        counter = rows(OUT / "vnext_retain_results.csv") + rows(
            OUT / "vnext_midpoint_results.csv")
        self.assertEqual({row["executable_sha256"] for row in counter},
                         {"7cc8ecb324c69526b38f21a8d66cdc4ca6ab6de0cd03639f916f25340d097a2e"})

    def test_16_no_broad_rerun_v50_or_cap_violation(self) -> None:
        fixed = rows(OUT / "fixed_interval_confirmation_results.csv")
        self.assertFalse(any("v50" in row["instance"].lower() for row in fixed))
        self.assertTrue(all(float(row["process_cap_seconds"]) <= 1800
                            for row in fixed))
        for marker_path in COUNTERFACTUAL_RUNS.glob("*/completion_marker.json"):
            self.assertLessEqual(float(load_json(marker_path)["process_cap_seconds"]),
                                 1800)
        historical = rows(OUT / "historical_baseline_reference_manifest.csv")
        self.assertTrue(all(row["comparison_status"].startswith("historical")
                            for row in historical))

    def test_17_counterfactual_labels_and_tail_gate_derive_from_complete_rows(self) -> None:
        pairs = rows(OUT / "vnext_counterfactual_pair_summary.csv")
        self.assertEqual(len(pairs), 7)
        self.assertTrue(all(truth(row["evidence_complete"]) for row in pairs))
        self.assertTrue(all(truth(row["parent_identity_match"]) for row in pairs))
        self.assertEqual(sum(truth(row["severe_error"]) for row in pairs), 4)
        decision = load_json(OUT / "split_stage_decision.json")
        self.assertEqual(decision["counterfactual_rows"], 14)
        self.assertEqual(decision["classification"], "severe_split_error_remains")
        self.assertFalse(decision["lp_tail_stage_opened"])
        self.assertEqual(decision["rules_tested"], 0)

    def test_18_final_classifications_are_derived_from_completed_evidence(self) -> None:
        decision = load_json(OUT / "final_decision.json")
        if decision["github_delivery"] == "draft_pr_pending":
            self.skipTest("draft PR publication gate is completed after the first push")
        self.assertEqual(decision["completion_status"], "round50_complete")
        self.assertTrue(decision["derived_from_completed_evidence"])
        self.assertEqual(decision["entered_stage_missing_rows"], [])
        self.assertEqual(decision["fixed_interval_classification"],
                         "interval_mip_v0_retained")
        self.assertEqual(decision["split_classification"],
                         "severe_split_error_remains")

    def test_19_compact_evidence_policy_excludes_raw_run_trees(self) -> None:
        compact = rows(OUT / "compact_evidence_inventory.csv")
        local = rows(OUT / "local_raw_evidence_inventory.csv")
        self.assertGreater(len(compact), 80)
        self.assertGreater(len(local), 0)
        for row in compact:
            self.assertNotIn("counterfactual_runs/", row["path"])
            self.assertNotIn("official_confirmation/", row["path"])
            self.assertNotIn("development_runs/", row["path"])
            self.assertNotIn("state_reconstruction/", row["path"])
        self.assertTrue(all(row["aggregate_sha256"] for row in local))

    def test_20_every_required_report_is_present_and_inventoried(self) -> None:
        inventory = rows(OUT / "final_evidence_inventory.csv")
        self.assertTrue(all(truth(row["present"]) for row in inventory))
        self.assertTrue(all(row["status"] in {"verified", "self_excluded"}
                            for row in inventory))
        self.assertGreaterEqual(len(inventory), 56)

    def test_21_every_physical_run_marker_and_manifest_is_complete(self) -> None:
        fixed_markers = list(FIXED_RUNS.glob("*/completion_marker.json"))
        counter_markers = list(COUNTERFACTUAL_RUNS.glob("*/completion_marker.json"))
        self.assertEqual((len(fixed_markers), len(counter_markers)), (23, 14))
        for marker_path in fixed_markers + counter_markers:
            marker = load_json(marker_path)
            self.assertTrue(marker.get("complete", marker.get("evidence_complete")))
            manifest = marker_path.parent / "artifact_manifest.csv"
            self.assertTrue(manifest.is_file())
            for item in rows(manifest):
                artifact = marker_path.parent / item["path"]
                self.assertTrue(artifact.is_file(), artifact)
                self.assertEqual(sha256(artifact), item["sha256"], artifact)

    def test_22_entered_row_counts_and_missing_rows_are_exact(self) -> None:
        decision = load_json(OUT / "final_decision.json")
        self.assertEqual(decision["row_counts"]["fixed_stage1_baseline"], 14)
        self.assertEqual(decision["row_counts"]["fixed_confirmation_physical"], 23)
        self.assertEqual(decision["row_counts"]["fixed_confirmation_logical"], 46)
        self.assertEqual(decision["row_counts"]["k1_integration_physical"], 0)
        self.assertEqual(decision["row_counts"]["counterfactual_physical"], 14)
        self.assertEqual(decision["row_counts"]["counterfactual_pairs"], 7)
        self.assertEqual(decision["entered_stage_missing_rows"], [])


if __name__ == "__main__":
    unittest.main()
