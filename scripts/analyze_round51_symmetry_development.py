#!/usr/bin/env python3
"""Apply frozen gates to the complete M1 symmetry development panel."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"
STATES = [f"D{i}" for i in range(1, 15)]
CANDIDATES = {
    "m1-s1-route-start-order": "symmetry_development_s1_raw.csv",
    "m1-s1r-used-first-route-start-order": "symmetry_development_s1r_raw.csv",
}


def truth(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def severe(old: dict[str, str], new: dict[str, str]) -> tuple[bool, str]:
    old_cert, new_cert = truth(old["certificate"]), truth(new["certificate"])
    reasons: list[str] = []
    if old_cert and not new_cert:
        reasons.append("baseline_certifies_candidate_does_not")
    old_work, new_work = float(old["work"]), float(new["work"])
    old_time, new_time = (
        float(old["process_time_seconds"]), float(new["process_time_seconds"]))
    if old_cert and new_cert:
        if new_work > 1.5 * old_work and new_work - old_work > 50.0:
            reasons.append("exact_work_ratio_and_absolute")
        if new_time > 1.5 * old_time and new_time - old_time > 60.0:
            reasons.append("exact_time_ratio_and_absolute")
    if not old_cert and not new_cert:
        old_gi, new_gi = (
            float(old["gi_common_horizon"]), float(new["gi_common_horizon"]))
        old_gap, new_gap = float(old["gap"]), float(new["gap"])
        if new_gi >= 1.5 * old_gi and new_gi - old_gi >= 0.05:
            reasons.append("capped_gi_ratio_and_absolute")
        if new_gap >= 1.5 * old_gap and new_gap - old_gap >= 0.05:
            reasons.append("capped_gap_ratio_and_absolute")
    return bool(reasons), "|".join(reasons) if reasons else "none"


def main() -> None:
    baseline = {row["state_id"]: row for row in csv.DictReader(
        (EVIDENCE / "symmetry_development_m1_raw.csv").open(
            newline="", encoding="utf-8-sig"))}
    big_m = {row["state_id"]: row["big_m_affected"] for row in csv.DictReader(
        (EVIDENCE / "big_m_model_delta_audit.csv").open(
            newline="", encoding="utf-8-sig"))}
    model_rows = list(csv.DictReader(
        (EVIDENCE / "symmetry_m1_model_correctness.csv").open(
            newline="", encoding="utf-8-sig")))
    model_ok = {(row["candidate_policy"], row["state_id"]):
                row["status"] == "pass" for row in model_rows}
    results: list[dict[str, object]] = []
    severe_rows: list[dict[str, object]] = []
    decisions: dict[str, object] = {}
    for policy, filename in CANDIDATES.items():
        candidate = {row["state_id"]: row for row in csv.DictReader(
            (EVIDENCE / filename).open(newline="", encoding="utf-8-sig"))}
        if set(candidate) != set(STATES) or set(baseline) != set(STATES):
            raise RuntimeError(f"incomplete D1-D14 qualification for {policy}")
        lost_states: list[str] = []
        severe_states: list[str] = []
        improved_states: list[str] = []
        correctness = false_certificates = 0
        for state in STATES:
            old, new = baseline[state], candidate[state]
            old_cert, new_cert = truth(old["certificate"]), truth(new["certificate"])
            lost = old_cert and not new_cert
            if lost:
                lost_states.append(state)
            is_severe, reason = severe(old, new)
            if is_severe:
                severe_states.append(state)
            false_certificate = truth(new["false_certificate"])
            false_certificates += int(false_certificate)
            valid = (truth(new["evidence_complete"])
                     and truth(new["cap_respected"])
                     and truth(new["model_identity_match"])
                     and model_ok[(policy, state)]
                     and not false_certificate)
            correctness += int(not valid)
            old_work, new_work = float(old["work"]), float(new["work"])
            old_gap, new_gap = float(old["gap"]), float(new["gap"])
            old_gi, new_gi = (
                float(old["gi_common_horizon"]),
                float(new["gi_common_horizon"]))
            improved = (
                (not old_cert and new_cert)
                or (old_cert and new_cert and new_work < old_work - 1e-9)
                or (not old_cert and not new_cert and
                    (new_gap < old_gap - 1e-9 or new_gi < old_gi - 1e-9)))
            if improved:
                improved_states.append(state)
            results.append({
                "state_id": state, "candidate_policy": policy,
                "big_m_affected": big_m[state],
                "d13_mandatory_negative_control": str(state == "D13").lower(),
                "process_cap_seconds": new["process_cap_seconds"],
                "executable_sha256": new["executable_sha256"],
                "baseline_model_sha256": old["model_sha256"],
                "candidate_model_sha256": new["model_sha256"],
                "model_correctness_audit": "pass" if model_ok[(policy, state)] else "fail",
                "baseline_status": old["status"],
                "candidate_status": new["status"],
                "baseline_certificate": old["certificate"],
                "candidate_certificate": new["certificate"],
                "candidate_certificate_class": new["certificate_class"],
                "lost_baseline_certificate": str(lost).lower(),
                "false_certificate": str(false_certificate).lower(),
                "baseline_native_status": old["native_status"],
                "candidate_native_status": new["native_status"],
                "baseline_work": old["work"], "candidate_work": new["work"],
                "work_delta": new_work - old_work,
                "work_ratio": new_work / old_work if old_work > 0.0 else 0.0,
                "baseline_process_time_seconds": old["process_time_seconds"],
                "candidate_process_time_seconds": new["process_time_seconds"],
                "baseline_gap": old["gap"], "candidate_gap": new["gap"],
                "baseline_gi": old["gi_common_horizon"],
                "candidate_gi": new["gi_common_horizon"],
                "baseline_nodes": old["nodes"], "candidate_nodes": new["nodes"],
                "baseline_simplex_iterations": old["simplex_iterations"],
                "candidate_simplex_iterations": new["simplex_iterations"],
                "baseline_root_relaxation_bound": old["root_relaxation_bound"],
                "candidate_root_relaxation_bound": new["root_relaxation_bound"],
                "baseline_final_root_cut_bound": old["final_root_cut_bound"],
                "candidate_final_root_cut_bound": new["final_root_cut_bound"],
                "baseline_presolved_rows": old["presolved_rows"],
                "candidate_presolved_rows": new["presolved_rows"],
                "baseline_presolved_columns": old["presolved_columns"],
                "candidate_presolved_columns": new["presolved_columns"],
                "baseline_peak_memory_gb": old["peak_memory_gb"],
                "candidate_peak_memory_gb": new["peak_memory_gb"],
                "baseline_max_matrix": old["max_matrix"],
                "candidate_max_matrix": new["max_matrix"],
                "improved": str(improved).lower(),
                "severe_regression": str(is_severe).lower(),
                "severe_regression_reason": reason,
                "engineering_evidence_complete": str(valid).lower(),
            })
            severe_rows.append({
                "candidate_policy": policy, "state_id": state,
                "big_m_affected": big_m[state],
                "d13_negative_control": str(state == "D13").lower(),
                "baseline_certificate": str(old_cert).lower(),
                "candidate_certificate": str(new_cert).lower(),
                "work_ratio": new_work / old_work if old_work > 0.0 else 0.0,
                "work_absolute_increase": new_work - old_work,
                "gi_ratio": new_gi / old_gi if old_gi > 0.0 else 0.0,
                "gi_absolute_increase": new_gi - old_gi,
                "gap_ratio": new_gap / old_gap if old_gap > 0.0 else 0.0,
                "gap_absolute_increase": new_gap - old_gap,
                "severe_regression": str(is_severe).lower(),
                "reason": reason,
            })
        base_work = sum(float(baseline[state]["work"]) for state in STATES)
        cand_work = sum(float(candidate[state]["work"]) for state in STATES)
        passed = (not lost_states and not severe_states and correctness == 0
                  and false_certificates == 0 and cand_work <= base_work + 1e-9
                  and len(improved_states) >= 2)
        d13_lost = "D13" in lost_states
        decisions[policy] = {
            "aggregate_candidate_work": cand_work,
            "aggregate_m1_v0_work": base_work,
            "aggregate_work_ratio": cand_work / base_work,
            "confirmation_opened": passed,
            "correctness_failures": correctness,
            "d13_baseline_certificate": truth(baseline["D13"]["certificate"]),
            "d13_candidate_certificate": truth(candidate["D13"]["certificate"]),
            "d13_round50_symmetry_regression_reproduced": d13_lost,
            "decision": "qualify_for_confirmation" if passed else "reject",
            "development_gate_passed": passed,
            "false_certificates": false_certificates,
            "improved_states": improved_states,
            "lost_baseline_certificate_states": lost_states,
            "severe_regression_states": severe_states,
        }
    with (EVIDENCE / "symmetry_m1_candidate_results.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)
    with (EVIDENCE / "symmetry_m1_severe_regression_audit.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(severe_rows[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(severe_rows)
    document = {
        "baseline": "m1-tight-big-m-v0",
        "candidates": decisions,
        "confirmation_opened": False,
        "development_cap_seconds": 300,
        "development_states": STATES,
        "final_symmetry_policy": "v0-cardinality",
        "reason": "both_candidates_lost_mandatory_D13_certificate",
        "schema": "round51-symmetry-m1-decision-v1",
    }
    (EVIDENCE / "symmetry_m1_decision.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(document, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
