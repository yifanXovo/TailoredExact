#!/usr/bin/env python3
"""Freeze the Round 41 panel, caps, and decision gates."""

from __future__ import annotations

import subprocess

import round41_common as common


ROLES = {
    "round39_small_easy_V10_M1_Q30_slot04_seed1099392856":
        "easy_p_grb_win",
    "round39_small_easy_V12_M3_Q30_slot08_seed1167625600":
        "largest_easy_p_grb_win",
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363":
        "major_fragmentation_regression",
    "round39_small_medium_V8_M3_Q30_slot03_seed1177285734":
        "additional_medium_c6_win",
    "round39_small_medium_V10_M2_Q20_slot05_seed968549317":
        "additional_medium_c6_win",
    "round39_small_hard_V10_M1_Q30_slot02_seed1721447042":
        "hard_p_grb_win",
    "round39_small_hard_V10_M1_Q20_slot01_seed561355351":
        "hard_p_grb_win",
    "round39_small_hard_V12_M3_Q20_slot07_seed621538683":
        "numerical_fail_closed_endpoint",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114":
        "strongest_k4_positive_control",
    "round39_small_hard_V10_M3_Q20_slot04_seed1145042375":
        "additional_hard_c6_win",
}


def main() -> int:
    inventory = common.inventory()
    rows = []
    for serial, (instance_id, role) in enumerate(ROLES.items(), start=1):
        item = inventory[instance_id]
        cap = 1800 if role in {
            "major_fragmentation_regression",
            "strongest_k4_positive_control",
        } else (300 if item["difficulty_stratum"] == "small-easy" else 900)
        rows.append({
            "round_id": 41,
            "serial_order": serial,
            "instance_id": instance_id,
            "instance_sha256": item["sha256"],
            "diagnostic_role": role,
            "difficulty_stratum": item["difficulty_stratum"],
            "V": item["V"],
            "M": item["M"],
            "Q": item["Q"],
            "root_lp_cap_seconds": 300,
            "exact_cap_seconds": cap,
            "one_thread": True,
            "gurobi_seed": 0,
            "gurobi_presolve": -1,
            "relative_gap": 0.0,
            "absolute_gap": 0.0,
            "selection_basis": "unchanged_round40_predeclared_diagnostic_panel",
        })
    common.write_csv(common.OUT / "diagnostic_panel_manifest.csv", rows)
    common.write_json(common.OUT / "decision_gates_frozen.json", {
        "schema": "round41-decision-gates-v1",
        "frozen_before_confirmation_runs": True,
        "source_head": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), cwd=common.ROOT,
            text=True).strip(),
        "default": "C6-HGA-FULL K=4 rho=0.01 remains unchanged",
        "gate_a": {
            "requirements": [
                "one static model and one native integer optimize",
                "strict original-problem certificate on solved sentinels",
                "independent verifier passes",
                "zero false certificates",
                "all post default-off equivalence pairs pass",
            ],
        },
        "gate_b": {
            "core_model_variable_ratio_max_vs_i": 2.5,
            "meaningful_root_bound_absolute_gain": 1e-6,
            "core_minimum_external_k2_strength_capture": 0.10,
            "extended_minimum_external_k2_strength_capture": 0.25,
        },
        "gate_c": {
            "fragmentation_instance":
                "round39_small_medium_V12_M3_Q30_slot08_seed1343324363",
            "fragmentation_requirements": {
                "integer_proof_jobs": 1,
                "maximum_time_ratio_vs_external_k4": 0.80,
                "maximum_work_ratio_vs_external_k4": 0.80,
                "comparison_requires_matching_strict_certificates": True,
            },
            "coarse_weakness_instance":
                "round39_small_hard_V12_M3_Q30_slot08_seed1288546114",
            "coarse_weakness_requirements": {
                "maximum_time_ratio_vs_external_k4": 1.25,
                "maximum_work_ratio_vs_external_k4": 1.25,
                "maximum_time_ratio_vs_external_k1": 0.70,
                "maximum_work_ratio_vs_external_k1": 0.70,
                "comparison_requires_matching_strict_certificates": True,
            },
            "both_witnesses_required": True,
            "capped_noncertificates_never_count_as_gate_passes": True,
        },
        "gate_d": {
            "st_k4_requires_gates_a_b_c": True,
            "st_k4_implemented_if_gate_c_fails": False,
        },
        "gate_e": {
            "held_out_requires_gates_a_b_c": True,
        },
        "official_process_cap_upper_bound_seconds": 1800,
        "forbidden_dispatch_inputs": [
            "instance name", "seed", "V/M/Q", "scenario label",
            "elapsed time", "Work", "node count", "hardware",
        ],
    })
    print({"panel_rows": len(rows), "frozen": True})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
