#!/usr/bin/env python3
"""Create the paired Round 50 Iteration 2 decision evidence."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"


def rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def truth(value: str) -> bool:
    return value.lower() in {"1", "true"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    baseline = {row["state_id"]: row for row in rows(
        EVIDENCE / "iteration2_qualification_v0_300s.csv")}
    candidate = {row["state_id"]: row for row in rows(
        EVIDENCE / "iteration2_qualification_c1_300s.csv")}
    correctness = {row["state_id"]: row for row in rows(
        EVIDENCE / "c1_model_correctness_audit.csv")}
    if baseline.keys() != candidate.keys() or baseline.keys() != correctness.keys():
        raise RuntimeError("Iteration 2 paired state sets differ")

    fields = [
        "candidate_id", "state_id", "baseline_policy", "candidate_policy",
        "same_executable", "model_delta_valid", "duplicates_omitted",
        "baseline_status", "candidate_status", "baseline_certificate",
        "candidate_certificate", "false_certificate", "baseline_work",
        "candidate_work", "work_ratio", "work_delta", "baseline_gi",
        "candidate_gi", "gi_delta", "baseline_gap", "candidate_gap",
        "baseline_lb", "candidate_lb", "baseline_nodes", "candidate_nodes",
        "baseline_presolved_rows", "candidate_presolved_rows",
        "severe_regression", "correctness_failure", "paired_decision",
    ]
    output = []
    severe_count = 0
    correctness_failures = 0
    false_certificates = 0
    for state in sorted(baseline, key=lambda value: int(value[1:])):
        base = baseline[state]
        cand = candidate[state]
        base_work = float(base["work"])
        cand_work = float(cand["work"])
        base_cert = truth(base["certificate"])
        cand_cert = truth(cand["certificate"])
        correctness_failure = cand["status"] == "failed"
        severe = base_cert and not cand_cert
        if base_cert and cand_cert:
            severe = severe or (
                cand_work / max(1e-12, base_work) > 1.5 and
                cand_work - base_work > 50.0)
            severe = severe or (
                float(cand["process_time_seconds"]) /
                    max(1e-12, float(base["process_time_seconds"])) > 1.5 and
                float(cand["process_time_seconds"]) -
                    float(base["process_time_seconds"]) > 60.0)
        elif not base_cert and not cand_cert and not correctness_failure:
            severe = severe or (
                float(cand["gi_common_horizon"]) >=
                    1.5 * float(base["gi_common_horizon"]) and
                float(cand["gi_common_horizon"]) -
                    float(base["gi_common_horizon"]) >= 0.05)
            severe = severe or (
                float(cand["gap"]) >= 1.5 * float(base["gap"]) and
                float(cand["gap"]) - float(base["gap"]) >= 0.05)
        false_certificate = truth(cand["false_certificate"])
        severe_count += int(severe)
        correctness_failures += int(correctness_failure)
        false_certificates += int(false_certificate)
        if correctness_failure:
            paired_decision = "reject_correctness_terminal_contract"
        elif severe:
            paired_decision = "reject_severe_regression"
        elif base_cert == cand_cert and abs(cand_work / max(base_work, 1e-12) - 1.0) < 0.05:
            paired_decision = "neutral"
        elif cand_work < base_work:
            paired_decision = "candidate_better"
        else:
            paired_decision = "baseline_better"
        output.append({
            "candidate_id": "C1", "state_id": state,
            "baseline_policy": base["policy"],
            "candidate_policy": cand["policy"],
            "same_executable": str(base["executable_sha256"] ==
                                   cand["executable_sha256"]).lower(),
            "model_delta_valid": correctness[state]["feasible_set_and_objective_invariant"],
            "duplicates_omitted": cand["exact_duplicate_rows_omitted"],
            "baseline_status": base["status"], "candidate_status": cand["status"],
            "baseline_certificate": base["certificate"],
            "candidate_certificate": cand["certificate"],
            "false_certificate": cand["false_certificate"],
            "baseline_work": base["work"], "candidate_work": cand["work"],
            "work_ratio": cand_work / max(base_work, 1e-12),
            "work_delta": cand_work - base_work,
            "baseline_gi": base["gi_common_horizon"],
            "candidate_gi": cand["gi_common_horizon"],
            "gi_delta": float(cand["gi_common_horizon"]) - float(base["gi_common_horizon"]),
            "baseline_gap": base["gap"], "candidate_gap": cand["gap"],
            "baseline_lb": base["lower_bound"], "candidate_lb": cand["lower_bound"],
            "baseline_nodes": base["nodes"], "candidate_nodes": cand["nodes"],
            "baseline_presolved_rows": base["presolved_rows"],
            "candidate_presolved_rows": cand["presolved_rows"],
            "severe_regression": str(severe).lower(),
            "correctness_failure": str(correctness_failure).lower(),
            "paired_decision": paired_decision,
        })

    candidate_path = EVIDENCE / "cut_formulation_candidate_results.csv"
    with candidate_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)

    valid_rows = [row for row in output if row["correctness_failure"] == "false"]
    aggregate_base_work = sum(float(row["baseline_work"]) for row in valid_rows)
    aggregate_candidate_work = sum(float(row["candidate_work"]) for row in valid_rows)
    decision = {
        "schema": "round50-cut-formulation-iteration-decision-v1",
        "iteration": 2, "status": "complete",
        "classification": "original_cut_pack_retained",
        "candidate_count": 1, "candidate_policy": "c1-exact-duplicate-elimination",
        "candidate_accepted": False, "accepted_changes": [],
        "active_policy_after_iteration": "interval-mip-v0 original cut/formulation pack",
        "qualification_rows": len(output),
        "baseline_certificates": sum(truth(baseline[s]["certificate"]) for s in baseline),
        "candidate_certificates": sum(truth(candidate[s]["certificate"]) for s in candidate),
        "candidate_capped_rows": sum(candidate[s]["status"] == "capped" for s in candidate),
        "candidate_failed_rows": sum(candidate[s]["status"] == "failed" for s in candidate),
        "correctness_failures": correctness_failures,
        "false_certificates": false_certificates,
        "severe_regressions": severe_count,
        "severe_regression_states": [row["state_id"] for row in output
                                      if row["severe_regression"] == "true"],
        "model_delta_audit_failures": sum(
            row["feasible_set_and_objective_invariant"] != "true"
            for row in correctness.values()),
        "duplicates_omitted_development": sum(
            int(candidate[s]["exact_duplicate_rows_omitted"]) for s in candidate),
        "valid_row_aggregate_work_ratio": (
            aggregate_candidate_work / aggregate_base_work),
        "material_hard_state_improvements": 0,
        "generic_gurobi_cut_parameter_changed": False,
        "confirmation_opened": False, "runtime_dispatch": False,
        "rejection_reason": (
            "D12 baseline certified but C1's native-optimal solution failed the "
            "independent original-objective certificate tolerance; remaining "
            "hard-state Work changes were immaterial"),
        "candidate_results_sha256": sha256(candidate_path),
        "model_correctness_audit_sha256": sha256(
            EVIDENCE / "c1_model_correctness_audit.csv"),
        "executable_sha256": next(iter(baseline.values()))["executable_sha256"],
    }
    (EVIDENCE / "cut_formulation_iteration_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
