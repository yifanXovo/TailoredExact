#!/usr/bin/env python3
"""Freeze the two M1 symmetry candidates that qualify from the core screen."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"
CORE = ["D1", "D2", "D3", "D4", "D5", "D6", "D9", "D10", "D11"]
CANDIDATES = {
    "m1-s1-route-start-order": "symmetry_core_s1_raw.csv",
    "m1-s1r-used-first-route-start-order": "symmetry_core_s1r_raw.csv",
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
        (EVIDENCE / "m1_core_m1_raw.csv").open(
            newline="", encoding="utf-8-sig"))}
    model_rows = list(csv.DictReader(
        (EVIDENCE / "symmetry_m1_model_correctness.csv").open(
            newline="", encoding="utf-8-sig")))
    model_ok = {(row["candidate_policy"], row["state_id"]):
                row["status"] == "pass" for row in model_rows}
    output: list[dict[str, object]] = []
    decisions: dict[str, object] = {}
    for policy, filename in CANDIDATES.items():
        candidate = {row["state_id"]: row for row in csv.DictReader(
            (EVIDENCE / filename).open(newline="", encoding="utf-8-sig"))}
        if set(candidate) != set(CORE):
            raise RuntimeError(f"incomplete core panel for {policy}")
        lost = severe_count = correctness = false_cert = 0
        improved_states: list[str] = []
        for state in CORE:
            old, new = baseline[state], candidate[state]
            is_severe, reason = severe(old, new)
            old_cert, new_cert = truth(old["certificate"]), truth(new["certificate"])
            lost += int(old_cert and not new_cert)
            severe_count += int(is_severe)
            false_cert += int(truth(new["false_certificate"]))
            valid = (truth(new["evidence_complete"])
                     and truth(new["cap_respected"])
                     and truth(new["model_identity_match"])
                     and model_ok[(policy, state)]
                     and not truth(new["false_certificate"]))
            correctness += int(not valid)
            improved = (
                (old_cert and new_cert and
                 float(new["work"]) < float(old["work"]) - 1e-9)
                or (not old_cert and not new_cert and
                    (float(new["gap"]) < float(old["gap"]) - 1e-9
                     or float(new["gi_common_horizon"]) <
                        float(old["gi_common_horizon"]) - 1e-9)))
            if improved:
                improved_states.append(state)
            output.append({
                "candidate_policy": policy, "state_id": state,
                "baseline_certificate": str(old_cert).lower(),
                "candidate_certificate": str(new_cert).lower(),
                "baseline_work": old["work"], "candidate_work": new["work"],
                "baseline_gap": old["gap"], "candidate_gap": new["gap"],
                "baseline_gi": old["gi_common_horizon"],
                "candidate_gi": new["gi_common_horizon"],
                "improved": str(improved).lower(),
                "severe_regression": str(is_severe).lower(),
                "severe_regression_reason": reason,
                "engineering_evidence_complete": str(valid).lower(),
            })
        base_work = sum(float(baseline[state]["work"]) for state in CORE)
        cand_work = sum(float(candidate[state]["work"]) for state in CORE)
        qualifies = (lost == severe_count == correctness == false_cert == 0
                     and cand_work <= base_work + 1e-9
                     and len(improved_states) >= 2)
        decisions[policy] = {
            "aggregate_candidate_work": cand_work,
            "aggregate_m1_v0_work": base_work,
            "aggregate_work_ratio": cand_work / base_work,
            "core_qualified": qualifies,
            "correctness_failures": correctness,
            "false_certificates": false_cert,
            "full_development_opened": qualifies,
            "improved_states": improved_states,
            "lost_baseline_certificates": lost,
            "severe_regressions": severe_count,
        }
    with (EVIDENCE / "symmetry_m1_core_screen_results.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    document = {
        "baseline": "m1-tight-big-m-v0",
        "candidates": decisions,
        "core_cap_seconds": 120,
        "core_states": CORE,
        "frozen_before_full_development_results": True,
        "schema": "round51-symmetry-core-screen-decision-v1",
    }
    (EVIDENCE / "symmetry_m1_core_screen_decision.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not all(value["core_qualified"] for value in decisions.values()):
        raise RuntimeError("one or more symmetry candidates failed core")
    print(json.dumps(document, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
