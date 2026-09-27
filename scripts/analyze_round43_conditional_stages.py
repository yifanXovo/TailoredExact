#!/usr/bin/env python3
"""Evaluate the predeclared Round 43 Stage 4 and Stage 5 entry conditions."""

from __future__ import annotations

from typing import Any

import round43_analysis as analysis
import round43_common as common


def row_for(rows: list[dict[str, Any]], candidate: str) -> dict[str, Any]:
    return next(row for row in rows if row["candidate"] == candidate)


def main() -> int:
    development = common.load_json(
        common.OUT / "stage3_development_decision.json")
    summaries = common.csv_rows(
        common.OUT / "stage3_development_summary.csv")
    capture = common.load_json(common.OUT / "stage2_envelope_capture.json")
    structural = common.load_json(
        common.OUT / "stage1_structural_selection.json")
    mechanism = common.csv_rows(common.OUT / "stage3_mechanism_summary.csv")

    stage3_passed = analysis.truth(development["stage3_passed"])
    contraction_admissible = not str(structural["C_d_classification"]).startswith(
        "inadmissible_constant")
    transfer_gap = float(capture["strong_control_transfer_gap"])
    chi = float(capture["strong_control_chi"])
    chi_denominator_material = analysis.truth(
        capture["strong_control_chi_denominator_material"])
    missing_transferable_root_strength = (
        abs(transfer_gap) > 1e-9 and chi_denominator_material and chi < 0.5)
    stage4_required = (not stage3_passed and (
        contraction_admissible or missing_transferable_root_strength))
    common.write_json(common.OUT / "stage4_disposition.json", {
        "schema": "round43-stage4-disposition-v1",
        "round_id": 43,
        "stage3_has_passing_candidate": stage3_passed,
        "contraction_score": {
            "entry_condition": (
                "C_d is mathematically admissible and adds stable structural "
                "information"),
            "C_d_classification": structural["C_d_classification"],
            "admissible": contraction_admissible,
            "entered": False,
            "disposition": "skipped_inadmissible_constant_signal",
        },
        "rank1_lifted_cuts": {
            "entry_condition": (
                "fixed-K4 gains arise from formulation strength not captured "
                "by the objective-Gini envelope"),
            "strong_control_K4_minus_K1_global_root_lp": transfer_gap,
            "strong_control_chi": chi,
            "chi_denominator_material": chi_denominator_material,
            "missing_transferable_root_strength_observed":
                missing_transferable_root_strength,
            "entered": False,
            "disposition": (
                "skipped_entry_false_equal_global_root_lp_and_vacuous_chi"),
            "supporting_evidence": [
                common.relative(common.OUT / "stage2_envelope_capture.json"),
                common.relative(
                    common.OUT / "stage2_envelope_diagnostics.csv"),
            ],
        },
        "stage4_required": stage4_required,
        "stage4_entered": False,
        "stage4_candidate_count": 0,
        "audit_passed": not stage4_required,
    })
    if stage4_required:
        raise RuntimeError("a predeclared Stage 4 entry condition is true")

    k1 = row_for(summaries, "A(1,2,0.1)")
    k4 = row_for(summaries, "A(4,2,0.1)")
    structurally_sensible = all(
        analysis.truth(row["all_correctness_gates_valid"])
        for row in mechanism if float(row["rho"]) == 0.1)
    control_protected = any(
        analysis.truth(row["strong_control_work_gate"]) and
        analysis.truth(row["strong_control_time_gate"])
        for row in (k1, k4))
    # The selected major rows make no recursive split, so their failure cannot
    # be attributed to duplicated terminal proof across adjacent descendants.
    major_rows = [row for row in common.csv_rows(
        common.OUT / "stage3_mechanism_results.csv")
                  if row["instance_id"] ==
                  "round39_small_medium_V12_M3_Q30_slot08_seed1343324363" and
                  float(row["rho"]) == 0.1]
    duplicated_adjacent_terminal_proof = any(
        int(row["split_count"]) > 0 and
        int(row["terminal_mip_jobs"]) > 1 for row in major_rows)
    root_and_envelope_not_principal = (
        abs(transfer_gap) <= 1e-9 and not chi_denominator_material)
    stage5_required = all((
        not stage3_passed,
        structurally_sensible,
        control_protected,
        duplicated_adjacent_terminal_proof,
        root_and_envelope_not_principal,
    ))
    common.write_json(common.OUT / "stage5_entry_audit.json", {
        "schema": "round43-stage5-entry-audit-v1",
        "round_id": 43,
        "stage3_has_passing_candidate": stage3_passed,
        "conditions": {
            "selected_mechanism_structurally_sensible":
                structurally_sensible,
            "strongest_positive_control_protected": control_protected,
            "major_regression_dominated_by_duplicated_adjacent_terminal_proof":
                duplicated_adjacent_terminal_proof,
            "root_and_envelope_quality_not_principal_failure":
                root_and_envelope_not_principal,
        },
        "selected_K1_strong_control_work_gate": analysis.truth(
            k1["strong_control_work_gate"]),
        "selected_K4_strong_control_work_gate": analysis.truth(
            k4["strong_control_work_gate"]),
        "major_selected_rows": [row["run_id"] for row in major_rows],
        "stage5_required": stage5_required,
        "stage5_entered": False,
        "stage5_candidate_count": 0,
        "disposition": (
            "skipped_entry_false_control_not_protected_and_no_adjacent_"
            "descendant_terminal_duplication"),
        "audit_passed": not stage5_required,
    })
    if stage5_required:
        raise RuntimeError("the predeclared Stage 5 entry condition is true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
