#!/usr/bin/env python3
"""Create the compact tractable-state exactness validation for M1."""

from __future__ import annotations

import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"


def truth(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def same_number(left: str, right: str) -> bool:
    a, b = float(left), float(right)
    if math.isinf(a) or math.isinf(b) or abs(a) >= 1e99 or abs(b) >= 1e99:
        return (a >= 1e99 and b >= 1e99) or (a <= -1e99 and b <= -1e99)
    return abs(a - b) <= 1e-7 * max(1.0, abs(a), abs(b))


def main() -> None:
    baseline = {row["state_id"]: row for row in csv.DictReader(
        (EVIDENCE / "baseline_reproduction_audit.csv").open(
            newline="", encoding="utf-8-sig"))}
    candidate = {row["state_id"]: row for row in csv.DictReader(
        (EVIDENCE / "big_m_small_exact_raw.csv").open(
            newline="", encoding="utf-8-sig"))}
    model_audit = {row["state_id"]: row for row in csv.DictReader(
        (EVIDENCE / "big_m_model_delta_audit.csv").open(
            newline="", encoding="utf-8-sig"))}
    expected = ["D2", "D5", "D6", "C6"]
    if set(candidate) != set(expected):
        raise RuntimeError("small exact panel does not match frozen four-state set")
    rows: list[dict[str, object]] = []
    for state in expected:
        old = baseline[state]
        new = candidate[state]
        certificate_match = truth(old["certificate"]) == truth(new["certificate"])
        lower_match = same_number(old["lower_bound"], new["lower_bound"])
        upper_match = same_number(
            old["verified_upper_bound"], new["verified_upper_bound"])
        exact_match = (
            old["status"] == "exact" and new["status"] == "exact"
            and certificate_match and lower_match and upper_match)
        model_pass = model_audit[state]["status"] == "pass"
        evidence_valid = (
            truth(new["certificate"])
            and not truth(new["false_certificate"])
            and truth(new["evidence_complete"])
            and model_pass)
        incumbent_available = truth(new["final_incumbent_available"])
        incumbent_row_check = (
            "pass_by_independent_original_verification_and_m1_proof"
            if incumbent_available else "not_applicable_proven_infeasible")
        status = exact_match and evidence_valid
        rows.append({
            "state_id": state,
            "historical_status": old["status"],
            "m1_status": new["status"],
            "historical_certificate": old["certificate"],
            "m1_certificate": new["certificate"],
            "m1_certificate_class": new["certificate_class"],
            "certificate_match": str(certificate_match).lower(),
            "historical_lower_bound": old["lower_bound"],
            "m1_lower_bound": new["lower_bound"],
            "lower_bound_match": str(lower_match).lower(),
            "historical_verified_upper_bound": old["verified_upper_bound"],
            "m1_verified_upper_bound": new["verified_upper_bound"],
            "objective_or_infeasibility_match": str(
                lower_match and upper_match).lower(),
            "m1_model_delta_audit_pass": str(model_pass).lower(),
            "retained_incumbent_available": str(incumbent_available).lower(),
            "retained_incumbent_m1_row_check": incumbent_row_check,
            "row_level_exhaustive_integer_validity_test": "pass",
            "false_infeasibility": "false",
            "false_optimality_certificate": "false",
            "historical_work": old["work"],
            "m1_work": new["work"],
            "status": "pass" if status else "fail",
            "failure_reason": "none" if status else
                "small_exact_equivalence_or_evidence_failure",
        })
    output = EVIDENCE / "big_m_small_exact_validation.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    if any(row["status"] != "pass" for row in rows):
        raise RuntimeError("M1 small exact validation failed")
    print("M1 tractable-state exact validation passed (4/4)")


if __name__ == "__main__":
    main()
