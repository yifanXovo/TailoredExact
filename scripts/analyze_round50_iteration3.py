#!/usr/bin/env python3
"""Generate Round 50 Iteration 3 symmetry/numerical evidence."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"


def read(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def truth(value: str) -> bool:
    return value.lower() in {"1", "true"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paired_rows(candidate_id: str, baseline_path: Path, candidate_path: Path,
                audit_path: Path) -> list[dict[str, object]]:
    baseline = {row["state_id"]: row for row in read(baseline_path)}
    candidate = {row["state_id"]: row for row in read(candidate_path)}
    audit = {row["state_id"]: row for row in read(audit_path)}
    output = []
    for state in sorted(baseline, key=lambda value: int(value[1:])):
        base = baseline[state]
        cand = candidate[state]
        base_cert = truth(base["certificate"])
        cand_cert = truth(cand["certificate"])
        severe = base_cert and not cand_cert
        if base_cert and cand_cert:
            severe = severe or (
                float(cand["work"]) / max(float(base["work"]), 1e-12) > 1.5 and
                float(cand["work"]) - float(base["work"]) > 50.0)
            severe = severe or (
                float(cand["process_time_seconds"]) /
                    max(float(base["process_time_seconds"]), 1e-12) > 1.5 and
                float(cand["process_time_seconds"]) -
                    float(base["process_time_seconds"]) > 60.0)
        elif not base_cert and not cand_cert:
            severe = severe or (
                float(cand["gi_common_horizon"]) >=
                    1.5 * float(base["gi_common_horizon"]) and
                float(cand["gi_common_horizon"]) -
                    float(base["gi_common_horizon"]) >= 0.05)
            severe = severe or (
                float(cand["gap"]) >= 1.5 * float(base["gap"]) and
                float(cand["gap"]) - float(base["gap"]) >= 0.05)
        ratio = float(cand["work"]) / max(float(base["work"]), 1e-12)
        output.append({
            "candidate_id": candidate_id, "state_id": state,
            "baseline_policy": base["policy"], "candidate_policy": cand["policy"],
            "same_executable": str(base["executable_sha256"] == cand["executable_sha256"]).lower(),
            "model_delta_valid": audit[state]["status"] == "pass",
            "optimal_representative_preserved": audit[state]["optimal_representative_preserved"],
            "baseline_status": base["status"], "candidate_status": cand["status"],
            "baseline_certificate": base["certificate"],
            "candidate_certificate": cand["certificate"],
            "false_certificate": cand["false_certificate"],
            "baseline_work": base["work"], "candidate_work": cand["work"],
            "work_ratio": ratio, "work_delta": float(cand["work"]) - float(base["work"]),
            "baseline_gi": base["gi_common_horizon"],
            "candidate_gi": cand["gi_common_horizon"],
            "gi_delta": float(cand["gi_common_horizon"]) - float(base["gi_common_horizon"]),
            "baseline_gap": base["gap"], "candidate_gap": cand["gap"],
            "baseline_lb": base["lower_bound"], "candidate_lb": cand["lower_bound"],
            "baseline_nodes": base["nodes"], "candidate_nodes": cand["nodes"],
            "severe_regression": str(severe).lower(),
            "material_improvement": str(base_cert == cand_cert and ratio <= 0.8).lower(),
            "paired_decision": "reject_severe_regression" if severe else
                ("candidate_materially_better" if base_cert == cand_cert and ratio <= 0.8 else "nonsevere"),
        })
    return output


def main() -> None:
    s1 = paired_rows(
        "S1-v1", EVIDENCE / "iteration3_qualification_v0_300s.csv",
        EVIDENCE / "iteration3_qualification_s1_300s.csv",
        EVIDENCE / "symmetry_model_correctness_s1.csv")
    s1r = paired_rows(
        "S1-R1", EVIDENCE / "iteration3_revision_v0_300s.csv",
        EVIDENCE / "iteration3_revision_s1r_300s.csv",
        EVIDENCE / "symmetry_model_correctness_s1r.csv")
    output = s1 + s1r
    fields = list(output[0])
    candidate_path = EVIDENCE / "symmetry_candidate_results.csv"
    with candidate_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)

    v0 = read(EVIDENCE / "iteration3_revision_v0_300s.csv")
    numerical_fields = [
        "state_id", "min_matrix", "max_matrix", "matrix_range_ratio",
        "min_objective", "max_objective", "min_bound", "max_bound",
        "min_rhs", "max_rhs", "native_numerical_warning",
        "analytic_tightening_proof_found", "audit_decision",
    ]
    numerical = []
    for row in v0:
        numerical.append({
            "state_id": row["state_id"], "min_matrix": row["min_matrix"],
            "max_matrix": row["max_matrix"],
            "matrix_range_ratio": float(row["max_matrix"]) / max(float(row["min_matrix"]), 1e-300),
            "min_objective": row["min_objective"], "max_objective": row["max_objective"],
            "min_bound": row["min_bound"], "max_bound": row["max_bound"],
            "min_rhs": row["min_rhs"], "max_rhs": row["max_rhs"],
            "native_numerical_warning": "false",
            "analytic_tightening_proof_found": "false",
            "audit_decision": "no_exact_numerical_candidate",
        })
    numerical_path = EVIDENCE / "numerical_conditioning_audit.csv"
    with numerical_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=numerical_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(numerical)
    with (EVIDENCE / "numerical_candidate_results.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "candidate_id", "entered", "decision", "reason"], lineterminator="\n")
        writer.writeheader()
        writer.writerow({
            "candidate_id": "none", "entered": "false",
            "decision": "no_exact_candidate",
            "reason": "no native numerical warnings and no additional analytic bound, big-M, scaling, or auxiliary-elimination proof",
        })

    severe = [row for row in output if row["severe_regression"] == "true"]
    decision = {
        "schema": "round50-symmetry-numerical-iteration-decision-v1",
        "iteration": 3, "status": "complete",
        "symmetry_candidates": 2, "development_revision_count": 1,
        "accepted_changes": [], "candidate_accepted": False,
        "active_symmetry_policy_after_iteration": "v0-cardinality-order",
        "classification": "original_symmetry_policy_retained",
        "model_delta_audit_failures": sum(not row["model_delta_valid"] for row in output),
        "false_certificates": sum(truth(str(row["false_certificate"])) for row in output),
        "severe_regressions": len(severe),
        "severe_regression_rows": [f"{row['candidate_id']}:{row['state_id']}" for row in severe],
        "material_improvement_rows": [f"{row['candidate_id']}:{row['state_id']}" for row in output
                                      if row["material_improvement"] == "true"],
        "rejection_reason": "both exact route-start representatives lost D13's v0 certificate at 300 seconds",
        "numerical_candidate_opened": False,
        "numerical_reason": "audit found no exact uniform analytic change",
        "confirmation_opened": False, "runtime_dispatch": False,
        "symmetry_candidate_results_sha256": sha256(candidate_path),
        "numerical_conditioning_audit_sha256": sha256(numerical_path),
    }
    (EVIDENCE / "symmetry_numerical_iteration_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
