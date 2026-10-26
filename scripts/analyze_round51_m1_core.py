#!/usr/bin/env python3
"""Apply the frozen Round 51 gates to the M1 120-second core screen."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"
CORE = ["D1", "D2", "D3", "D4", "D5", "D6", "D9", "D10", "D11"]


def truth(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def main() -> None:
    baseline = {row["state_id"]: row for row in csv.DictReader(
        (EVIDENCE / "m1_core_v0_raw.csv").open(
            newline="", encoding="utf-8-sig"))}
    candidate = {row["state_id"]: row for row in csv.DictReader(
        (EVIDENCE / "m1_core_m1_raw.csv").open(
            newline="", encoding="utf-8-sig"))}
    model = {row["state_id"]: row for row in csv.DictReader(
        (EVIDENCE / "big_m_model_delta_audit.csv").open(
            newline="", encoding="utf-8-sig"))}
    if set(baseline) != set(CORE) or set(candidate) != set(CORE):
        raise RuntimeError("M1 core summaries do not match the frozen panel")
    results: list[dict[str, object]] = []
    severe_rows: list[dict[str, object]] = []
    lost_certificates = 0
    correctness_failures = 0
    false_certificates = 0
    severe_count = 0
    for state in CORE:
        old, new = baseline[state], candidate[state]
        old_cert, new_cert = truth(old["certificate"]), truth(new["certificate"])
        lost = old_cert and not new_cert
        lost_certificates += int(lost)
        false_certificate = truth(new["false_certificate"])
        false_certificates += int(false_certificate)
        correct = (
            truth(new["evidence_complete"])
            and truth(new["cap_respected"])
            and truth(new["model_identity_match"])
            and model[state]["status"] == "pass"
            and not false_certificate)
        correctness_failures += int(not correct)
        old_work, new_work = float(old["work"]), float(new["work"])
        old_time, new_time = (
            float(old["process_time_seconds"]),
            float(new["process_time_seconds"]),
        )
        old_gap, new_gap = float(old["gap"]), float(new["gap"])
        old_gi, new_gi = (
            float(old["gi_common_horizon"]),
            float(new["gi_common_horizon"]),
        )
        reasons: list[str] = []
        if lost:
            reasons.append("baseline_certifies_candidate_does_not")
        if old_cert and new_cert:
            if (new_work > 1.5 * old_work and
                    new_work - old_work > 50.0):
                reasons.append("exact_work_ratio_and_absolute")
            if (new_time > 1.5 * old_time and
                    new_time - old_time > 60.0):
                reasons.append("exact_time_ratio_and_absolute")
        if not old_cert and not new_cert:
            if new_gi >= 1.5 * old_gi and new_gi - old_gi >= 0.05:
                reasons.append("capped_gi_ratio_and_absolute")
            if new_gap >= 1.5 * old_gap and new_gap - old_gap >= 0.05:
                reasons.append("capped_gap_ratio_and_absolute")
        severe = bool(reasons)
        severe_count += int(severe)
        results.append({
            "state_id": state, "panel_role": old["panel"],
            "big_m_affected": model[state]["big_m_affected"],
            "baseline_policy": old["policy"],
            "candidate_policy": new["policy"],
            "process_cap_seconds": new["process_cap_seconds"],
            "executable_sha256": new["executable_sha256"],
            "baseline_model_sha256": old["model_sha256"],
            "candidate_model_sha256": new["model_sha256"],
            "model_delta_audit": model[state]["status"],
            "baseline_status": old["status"],
            "candidate_status": new["status"],
            "baseline_certificate": old["certificate"],
            "candidate_certificate": new["certificate"],
            "candidate_certificate_class": new["certificate_class"],
            "lost_baseline_certificate": str(lost).lower(),
            "false_certificate": str(false_certificate).lower(),
            "baseline_work": old["work"], "candidate_work": new["work"],
            "work_delta": new_work - old_work,
            "work_ratio": new_work / old_work if old_work > 0.0 else 0.0,
            "baseline_process_time_seconds": old["process_time_seconds"],
            "candidate_process_time_seconds": new["process_time_seconds"],
            "baseline_gap": old["gap"], "candidate_gap": new["gap"],
            "baseline_gi": old["gi_common_horizon"],
            "candidate_gi": new["gi_common_horizon"],
            "baseline_root_relaxation_bound": old["root_relaxation_bound"],
            "candidate_root_relaxation_bound": new["root_relaxation_bound"],
            "baseline_final_root_cut_bound": old["final_root_cut_bound"],
            "candidate_final_root_cut_bound": new["final_root_cut_bound"],
            "baseline_nodes": old["nodes"], "candidate_nodes": new["nodes"],
            "baseline_simplex_iterations": old["simplex_iterations"],
            "candidate_simplex_iterations": new["simplex_iterations"],
            "severe_regression": str(severe).lower(),
            "severe_regression_reason": "|".join(reasons) if reasons else "none",
            "engineering_evidence_complete": str(correct).lower(),
        })
        severe_rows.append({
            "mechanism": "M1", "candidate_policy": new["policy"],
            "state_id": state, "baseline_certificate": str(old_cert).lower(),
            "candidate_certificate": str(new_cert).lower(),
            "work_ratio": new_work / old_work if old_work > 0.0 else 0.0,
            "work_absolute_increase": new_work - old_work,
            "gi_ratio": new_gi / old_gi if old_gi > 0.0 else 0.0,
            "gi_absolute_increase": new_gi - old_gi,
            "gap_ratio": new_gap / old_gap if old_gap > 0.0 else 0.0,
            "gap_absolute_increase": new_gap - old_gap,
            "severe_regression": str(severe).lower(),
            "reason": "|".join(reasons) if reasons else "none",
        })
    total_old = sum(float(row["baseline_work"]) for row in results)
    total_new = sum(float(row["candidate_work"]) for row in results)
    aggregate_nonworse = total_new <= total_old + 1e-9
    pass_core = (
        correctness_failures == 0 and false_certificates == 0
        and lost_certificates == 0 and severe_count == 0
        and aggregate_nonworse)
    with (EVIDENCE / "big_m_candidate_results.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(results)
    with (EVIDENCE / "big_m_severe_regression_audit.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(severe_rows[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(severe_rows)
    decision = {
        "aggregate_candidate_work": total_new,
        "aggregate_paired_work_nonworse": aggregate_nonworse,
        "aggregate_work_delta": total_new - total_old,
        "aggregate_work_ratio": total_new / total_old,
        "aggregate_v0_work": total_old,
        "candidate": "m1-tight-big-m-v0",
        "confirmation_opened": False,
        "core_cap_seconds": 120,
        "core_gate_passed": pass_core,
        "core_states": CORE,
        "correctness_failures": correctness_failures,
        "decision": "reject_as_production_backend",
        "development_300s_opened": False,
        "false_certificates": false_certificates,
        "lost_baseline_certificates": lost_certificates,
        "m1_retained_as_audited_experimental_baseline_for_stages_2_and_3": True,
        "reason": (
            "bounded_core_rejection:lost_D4_certificate_and_aggregate_work_regression"
            if not pass_core else "core_gate_passed"),
        "schema": "round51-big-m-decision-v1",
        "severe_regressions": severe_count,
    }
    (EVIDENCE / "big_m_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
