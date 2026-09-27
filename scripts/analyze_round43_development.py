#!/usr/bin/env python3
"""Audit references and evaluate the frozen Round 43 development gates."""

from __future__ import annotations

import math
from typing import Any

import round43_analysis as analysis
import round43_common as common


MAJOR = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
CONTROL = "round39_small_hard_V12_M3_Q30_slot08_seed1288546114"
REFERENCE_ARMS = ("C6", "K1-old", "K1-single",
                  "K1-adaptive-decisive", "P-GRB")


def materiality() -> dict[str, str]:
    freeze = common.load_json(common.OUT / "dataset_freeze.json")
    return {row["instance_id"]: row["classification"]
            for row in freeze["development"]}


def load_references() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    mandatory = set(common.CONTEMPORARY_REFERENCE_IDS)
    references = []
    audit = []
    inventory = common.inventory()
    manifest = analysis.historical_manifest()
    default_audit = common.csv_rows(common.OUT / "default_off_equivalence.csv")
    default_off_valid = len(default_audit) == 3 and all(
        analysis.truth(row["default_off_equivalence_passed"])
        for row in default_audit)
    for instance_id in common.DEVELOPMENT_IDS:
        for arm in REFERENCE_ARMS:
            entry = manifest[(instance_id, arm)]
            use_current = arm == "P-GRB" or (
                arm == "C6" and instance_id in mandatory)
            row = (analysis.current_reference(instance_id, arm)
                   if use_current else
                   analysis.historical_reference(instance_id, arm))
            row["instance_id"] = instance_id
            references.append(row)
            input_match = (entry["input_sha256"] ==
                           inventory[instance_id]["sha256"])
            zero_range_no_model = (
                entry["canonical_model_hash_available"].lower() == "false" and
                instance_id == common.DEVELOPMENT_IDS[0])
            model_identity_available = (
                entry["canonical_model_hash_available"].lower() == "true" or
                zero_range_no_model)
            historical_contract = analysis.truth(
                entry["historical_solver_contract_valid"])
            historical_certificate = analysis.truth(
                entry["historical_strict_certificate"])
            historical_outcome_honest = (
                not row["false_certificate"] and
                row["parameter_roundtrip_valid"] and
                (not row["certified"] or row["verified_incumbent"]))
            eligible_reuse = (
                not use_current and arm != "P-GRB" and input_match and
                model_identity_available and historical_contract and
                historical_outcome_honest and default_off_valid)
            audit.append({
                "instance_id": instance_id,
                "arm": arm,
                "provenance": row["provenance"],
                "input_sha256_match": input_match,
                "canonical_model_identity_available": model_identity_available,
                "zero_range_no_model_expected": zero_range_no_model,
                "historical_solver_contract_valid": historical_contract,
                "historical_strict_certificate": historical_certificate,
                "historical_outcome_honest": historical_outcome_honest,
                "same_machine": entry["machine_identifier"] ==
                    "WIN-3NO58RVQ4VC",
                "round43_default_off_equivalence_valid": default_off_valid,
                "hga_start_contract_valid": row[
                    "hga_start_contract_valid"],
                "hga_start_requested": row["hga_start_requested"],
                "hga_start_incumbent_found": row[
                    "hga_start_incumbent_found"],
                "hga_start_mapping_complete": row[
                    "hga_start_mapping_complete"],
                "hga_start_submitted": row["hga_start_submitted"],
                "hga_start_status": row["hga_start_status"],
                "hga_start_verified_objective": row[
                    "hga_start_verified_objective"],
                "hga_start_safe_mapping_rejection": row[
                    "hga_start_safe_mapping_rejection"],
                "historical_reuse_eligible": eligible_reuse,
                "disposition": (
                    "contemporaneous_fair_hga_start"
                    if arm == "P-GRB" else
                    ("mandatory_contemporaneous_c6"
                     if use_current else "audited_historical_reuse")),
            })
    if not all(row["historical_reuse_eligible"]
               for row in audit if row["disposition"] ==
               "audited_historical_reuse"):
        raise RuntimeError("historical reference equivalence audit failed")
    if not all(row["hga_start_contract_valid"]
               for row in audit if row["arm"] == "P-GRB"):
        raise RuntimeError("Round 43 P-GRB HGA-start contract failed")
    return references, audit


def main() -> int:
    selection = common.load_json(common.OUT / "stage3_candidate_selection.json")
    references, audit = load_references()
    common.write_csv(common.OUT / "baseline_reuse_audit.csv", audit)
    ref_map = {(row["instance_id"], row["arm"]): row for row in references}
    candidates = []
    for key in ("selected_K1", "selected_K4"):
        setting = selection[key]
        for instance_id in common.DEVELOPMENT_IDS:
            row = analysis.candidate_metrics(
                instance_id, int(setting["K0"]), float(setting["rho"]))
            row["instance_id"] = instance_id
            candidates.append(row)
    all_runs = references + candidates
    common.write_csv(common.OUT / "per_run_results.csv", all_runs)

    classifications = materiality()
    comparisons = []
    for candidate in candidates:
        instance_id = candidate["instance_id"]
        c6 = ref_map[(instance_id, "C6")]
        pgrb = ref_map[(instance_id, "P-GRB")]
        work_p = analysis.ratio(candidate["work"], pgrb["work"])
        work_c6 = analysis.ratio(candidate["work"], c6["work"])
        shifted_exact_c6 = analysis.ratio(
            candidate["exact_phase_seconds"] + 1.0,
            c6["exact_phase_seconds"] + 1.0)
        shifted_total_p = analysis.ratio(
            candidate["process_seconds"] + 1.0,
            pgrb["process_seconds"] + 1.0)
        material_result = ("win" if work_p <= 0.95 else
                           ("loss" if work_p >= 1.05 else "tie"))
        comparisons.append({
            "instance_id": instance_id,
            "classification": classifications[instance_id],
            "candidate": candidate["arm"],
            "candidate_certified": candidate["certified"],
            "candidate_false_certificate": candidate["false_certificate"],
            "candidate_verifier_passed": candidate["verified_incumbent"],
            "candidate_parameter_contract_valid": candidate[
                "parameter_roundtrip_valid"],
            "c6_certified": c6["certified"],
            "pgrb_certified": pgrb["certified"],
            "certificate_regression_vs_c6": (
                c6["certified"] and not candidate["certified"]),
            "candidate_work": candidate["work"],
            "c6_work": c6["work"],
            "pgrb_work": pgrb["work"],
            "candidate_over_c6_work": work_c6,
            "candidate_over_pgrb_work": work_p,
            "candidate_exact_seconds": candidate["exact_phase_seconds"],
            "c6_exact_seconds": c6["exact_phase_seconds"],
            "shifted_exact_time_vs_c6": shifted_exact_c6,
            "candidate_process_seconds": candidate["process_seconds"],
            "pgrb_process_seconds": pgrb["process_seconds"],
            "shifted_total_time_vs_pgrb": shifted_total_p,
            "joint_work_time_ratio_vs_pgrb": max(work_p, shifted_total_p),
            "material_result_vs_pgrb": material_result,
            "severe_material_regression": (
                classifications[instance_id] == "material_proof" and
                work_p > 1.35),
            "split_count": candidate["split_count"],
            "final_intervals": candidate["final_intervals"],
            "lp_jobs": candidate["lp_jobs"],
            "terminal_mip_jobs": candidate["terminal_mip_jobs"],
        })
    common.write_csv(common.OUT / "development_comparison.csv", comparisons)

    summaries = []
    for arm in sorted({row["candidate"] for row in comparisons}):
        group = [row for row in comparisons if row["candidate"] == arm]
        major = next(row for row in group if row["instance_id"] == MAJOR)
        control = next(row for row in group if row["instance_id"] == CONTROL)
        material = [row for row in group
                    if row["classification"] == "material_proof"]
        wins = sum(row["material_result_vs_pgrb"] == "win"
                   for row in material)
        losses = sum(row["material_result_vs_pgrb"] == "loss"
                     for row in material)
        summary = {
            "candidate": arm,
            "row_count": len(group),
            "all_correctness_gates": all(
                row["candidate_certified"] and
                not row["candidate_false_certificate"] and
                row["candidate_verifier_passed"] and
                row["candidate_parameter_contract_valid"] and
                not row["certificate_regression_vs_c6"] for row in group),
            "major_candidate_over_pgrb_work": major[
                "candidate_over_pgrb_work"],
            "major_gate": major["candidate_over_pgrb_work"] <= 1.25,
            "strong_control_candidate_over_c6_work": control[
                "candidate_over_c6_work"],
            "strong_control_work_gate": control[
                "candidate_over_c6_work"] <= 1.20,
            "strong_control_shifted_exact_time": control[
                "shifted_exact_time_vs_c6"],
            "strong_control_time_gate": control[
                "shifted_exact_time_vs_c6"] <= 1.25,
            "worst_material_candidate_over_pgrb_work": max(
                row["candidate_over_pgrb_work"] for row in material),
            "material_tail_gate": all(
                row["candidate_over_pgrb_work"] <= 1.35
                for row in material),
            "geomean_candidate_over_pgrb_work": analysis.gmean([
                row["candidate_over_pgrb_work"] for row in group]),
            "geomean_candidate_over_c6_work": analysis.gmean([
                row["candidate_over_c6_work"] for row in group]),
            "material_wins": wins,
            "material_losses": losses,
            "material_ties": len(material) - wins - losses,
            "material_win_loss_gate": wins >= losses,
            "worst_joint_work_time_ratio": max(
                row["joint_work_time_ratio_vs_pgrb"] for row in group),
            "joint_work_time_gate": all(
                row["joint_work_time_ratio_vs_pgrb"] <= 1.50
                for row in group),
        }
        summary["pgrb_aggregate_gate"] = (
            summary["geomean_candidate_over_pgrb_work"] <= 0.90)
        summary["c6_aggregate_gate"] = (
            summary["geomean_candidate_over_c6_work"] <= 1.05)
        summary["development_passed"] = all(summary[key] for key in (
            "all_correctness_gates", "major_gate",
            "strong_control_work_gate", "strong_control_time_gate",
            "material_tail_gate", "pgrb_aggregate_gate",
            "c6_aggregate_gate", "material_win_loss_gate",
            "joint_work_time_gate"))
        summaries.append(summary)
    summaries.sort(key=lambda row: (
        not row["development_passed"],
        not row["all_correctness_gates"],
        row["major_candidate_over_pgrb_work"],
        row["strong_control_candidate_over_c6_work"],
        row["worst_material_candidate_over_pgrb_work"],
        row["geomean_candidate_over_pgrb_work"],
        0 if row["candidate"].startswith("A(1,") else 1))
    common.write_csv(common.OUT / "stage3_development_summary.csv", summaries)
    passing = [row["candidate"] for row in summaries
               if row["development_passed"]]
    common.write_json(common.OUT / "stage3_development_decision.json", {
        "schema": "round43-stage3-development-decision-v1",
        "round_id": 43,
        "candidate_count": len(summaries),
        "development_rows": len(comparisons),
        "passing_candidates": passing,
        "selected_for_validation": passing[0] if passing else None,
        "stage3_passed": bool(passing),
        "validation_may_open": bool(passing),
        "holdout_opened": False,
        "tail_first_selection_order": [
            "correctness", "major severe-regression protection",
            "strongest C6 control protection", "worst material ratio",
            "aggregate Work", "aggregate time", "prefer K0=1 on tie"],
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
