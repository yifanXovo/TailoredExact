#!/usr/bin/env python3
"""Apply the frozen Round 41 gates without changing their thresholds."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from typing import Any

import round41_common as common


STATIC_ARMS = ("st-k2-i", "st-k2-p-core", "st-k2-p-extended")
FRAGMENTATION = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
COARSE = "round39_small_hard_V12_M3_Q30_slot08_seed1288546114"


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"true", "1", "yes"}


def number(value: Any, default: float = math.nan) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def ratio(lhs: Any, rhs: Any) -> float:
    a, b = number(lhs), number(rhs)
    return a / b if math.isfinite(a) and math.isfinite(b) and b > 0 else math.nan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-complete-witnesses", action="store_true")
    args = parser.parse_args()
    rows = common.csv_rows(common.OUT / "per_run_results.csv")
    by_key = {(row["instance_id"], row["arm"], row["solve"]): row
              for row in rows}
    defaults = common.csv_rows(common.OUT / "default_c6_equivalence.csv")
    exactness = common.csv_rows(common.OUT / "exactness_audit.csv")
    model = common.csv_rows(common.OUT / "model_size_comparison.csv")
    strength = common.csv_rows(
        common.OUT / "perspective_strength_capture.csv")
    model_by_key = {(row["instance_id"], row["arm"]): row for row in model}

    i_rows = [row for row in exactness if row["arm"] == "st-k2-i"]
    gate_a = bool(i_rows) and all(
        truth(row["accepted_outcome"]) and
        truth(row["one_native_mip_job"]) and
        (not truth(row["strict_certificate"]) or
         truth(row["cross_static_objective_match"])) and
        truth(row["original_problem_verifier_passed"]) and
        not truth(row["false_certificate"])
        for row in i_rows) and all(
            truth(row["default_c6_equivalence_passed"]) for row in defaults)
    gate_a = gate_a and any(truth(row["strict_certificate"])
                            for row in i_rows)

    growth = []
    for instance_id in {row["instance_id"] for row in model}:
        base = model_by_key.get((instance_id, "st-k2-i"))
        core = model_by_key.get((instance_id, "st-k2-p-core"))
        if base and core:
            growth.append(ratio(core["variables"], base["variables"]))
    core_exact = [row for row in exactness
                  if row["arm"] == "st-k2-p-core"]
    gate_b = bool(core_exact) and all(
        truth(row["accepted_outcome"]) and
        truth(row["one_native_mip_job"]) and
        (not truth(row["strict_certificate"]) or
         truth(row["cross_static_objective_match"])) and
        not truth(row["false_certificate"])
        for row in core_exact) and bool(growth) and max(growth) <= 2.5
    gate_b = gate_b and any(truth(row["strict_certificate"])
                            for row in core_exact)
    core_capture = [number(row["strength_capture"])
                    for row in strength
                    if row["arm"] == "st-k2-p-core" and
                    truth(row["positive_denominator"])]
    gate_b = gate_b and bool(core_capture) and all(
        math.isfinite(value) and value >= 0.10 for value in core_capture)

    arm_evidence: dict[str, dict[str, Any]] = {}
    for arm in STATIC_ARMS:
        f = by_key.get((FRAGMENTATION, arm, "mip"))
        c = by_key.get((COARSE, arm, "mip"))
        fk4 = by_key.get((FRAGMENTATION, "external-k4", "mip"))
        ck4 = by_key.get((COARSE, "external-k4", "mip"))
        ck1 = by_key.get((COARSE, "external-k1", "mip"))
        complete = all(item is not None for item in (f, c, fk4, ck4, ck1))
        strict_comparable = complete and all(truth(item["strict_certificate"])
            for item in (f, c, fk4, ck4, ck1))
        values = {
            "complete": complete,
            "strict_comparable": strict_comparable,
            "fragmentation_time_ratio_vs_k4": ratio(
                f["exact_phase_seconds"], fk4["exact_phase_seconds"])
                if f and fk4 else math.nan,
            "fragmentation_work_ratio_vs_k4": ratio(
                f["solver_work"], fk4["solver_work"])
                if f and fk4 else math.nan,
            "coarse_time_ratio_vs_k4": ratio(
                c["exact_phase_seconds"], ck4["exact_phase_seconds"])
                if c and ck4 else math.nan,
            "coarse_work_ratio_vs_k4": ratio(
                c["solver_work"], ck4["solver_work"])
                if c and ck4 else math.nan,
            "coarse_time_ratio_vs_k1": ratio(
                c["exact_phase_seconds"], ck1["exact_phase_seconds"])
                if c and ck1 else math.nan,
            "coarse_work_ratio_vs_k1": ratio(
                c["solver_work"], ck1["solver_work"])
                if c and ck1 else math.nan,
            "fragmentation_integer_jobs": int(number(
                f["independent_integer_proof_jobs"], 0)) if f else 0,
        }
        values["fragmentation_pass"] = strict_comparable and (
            values["fragmentation_integer_jobs"] == 1 and
            values["fragmentation_time_ratio_vs_k4"] <= 0.80 and
            values["fragmentation_work_ratio_vs_k4"] <= 0.80)
        values["coarse_weakness_pass"] = strict_comparable and (
            values["coarse_time_ratio_vs_k4"] <= 1.25 and
            values["coarse_work_ratio_vs_k4"] <= 1.25 and
            values["coarse_time_ratio_vs_k1"] <= 0.70 and
            values["coarse_work_ratio_vs_k1"] <= 0.70)
        values["both_mechanisms_pass"] = (
            values["fragmentation_pass"] and
            values["coarse_weakness_pass"])
        arm_evidence[arm] = values

    witnesses_complete = all(value["complete"]
                             for value in arm_evidence.values())
    gate_c = any(value["both_mechanisms_pass"]
                 for value in arm_evidence.values())
    gate_d = gate_a and gate_b and gate_c
    gate_e = gate_d
    false_certificates = sum(truth(row["false_certificate"])
                             for row in exactness)
    decision = {
        "schema": "round41-final-decision-v1",
        "frozen_gate_source": "decision_gates_frozen.json",
        "witnesses_complete": witnesses_complete,
        "gate_a_technical_feasibility_passed": gate_a,
        "gate_b_perspective_engineering_passed": gate_b,
        "gate_b_max_core_variable_ratio_vs_i": max(growth) if growth else None,
        "gate_b_min_core_external_k2_strength_capture": (
            min(core_capture) if core_capture else None),
        "gate_c_both_opposing_mechanisms_passed": gate_c,
        "gate_c_arm_evidence": arm_evidence,
        "gate_d_k4_extension_justified": gate_d,
        "st_k4_p_implemented": False,
        "gate_e_held_out_validation_justified": gate_e,
        "held_out_validation_run": False,
        "st_k2_h_implemented": False,
        "exactness": {
            "audited_static_mip_rows": len(exactness),
            "strict_certificates": sum(truth(row["strict_certificate"])
                                       for row in exactness),
            "false_certificates": false_certificates,
        },
        "promotion_recommendation": (
            "candidate_requires_separate_promotion_round" if gate_e else
            "retain_frozen_c6_hga_full_k4_rho_0_01"),
        "validated_default": "C6-HGA-FULL K=4 rho=0.01",
        "automatic_mainline_change": False,
    }
    common.write_json(common.OUT / "final_decision.json", decision)
    if false_certificates:
        raise RuntimeError("false Round 41 certificate")
    if args.require_complete_witnesses and not witnesses_complete:
        raise RuntimeError("Round 41 opposing-witness matrix is incomplete")
    print(json.dumps({
        "gate_a": gate_a, "gate_b": gate_b, "gate_c": gate_c,
        "witnesses_complete": witnesses_complete,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
