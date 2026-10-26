#!/usr/bin/env python3
"""Close the sole A1-R1 core and assemble the complete adaptive evidence."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

from analyze_round51_a1_core import read_rows, severe, truth, write_rows


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"
RUN_ROOT = EVIDENCE / "a1r_core_runs"
CORE = ["D1", "D2", "D3", "D4", "D5", "D6", "D9", "D10", "D11"]
CANDIDATE = "a1r-root-sparse-top1"


def main() -> None:
    baseline = {row["state_id"]: row for row in read_rows(
        EVIDENCE / "a1r_core_m1_raw.csv")}
    candidate = {row["state_id"]: row for row in read_rows(
        EVIDENCE / "a1r_core_a1r_raw.csv")}
    if set(baseline) != set(CORE) or set(candidate) != set(CORE):
        raise RuntimeError("A1-R1 core summaries do not match the frozen panel")
    hashes = {row["executable_sha256"] for row in baseline.values()} | {
        row["executable_sha256"] for row in candidate.values()}
    if len(hashes) != 1:
        raise RuntimeError("paired A1-R1 core did not use one executable hash")
    model = {row["state_id"]: row for row in read_rows(
        EVIDENCE / "adaptive_branching_revision_model_correctness.csv")}

    probe_rows: list[dict[str, object]] = []
    priority_rows: list[dict[str, object]] = []
    overhead_rows: list[dict[str, object]] = []
    audits: dict[str, dict[str, object]] = {}
    for state in CORE:
        run = RUN_ROOT / f"{state}__{CANDIDATE}"
        probes = read_rows(run / "adaptive_branching_probe_evidence.csv")
        priorities = read_rows(
            run / "adaptive_branching_priority_assignment_audit.csv")
        overhead = read_rows(run / "adaptive_branching_overhead_ledger.csv")
        reuse = read_rows(run / "model_reuse_ledger.csv")
        if len(overhead) != 1 or len(reuse) != 1:
            raise RuntimeError(f"invalid A1-R1 lifecycle ledger: {state}")
        o, r = overhead[0], reuse[0]
        active = [row for row in priorities
                  if int(row["requested_priority"]) > 0]
        expected_models = 2 + int(o["probe_count"])
        total = (float(o["root_lp_work"]) +
                 float(o["child_probe_work"]) +
                 float(o["terminal_mip_work"]))
        active_vector_valid = (
            len(active) == int(o["priority_count"]) <= 1
            and all(int(row["requested_priority"]) == 1 and
                    int(row["observed_priority"]) == 1 and
                    truth(row["exact_readback"]) and
                    truth(row["terminal_model_fresh"])
                    for row in active)
            and (not active or int(active[0]["zero_priority_readback_count"])
                 == int(candidate[state]["original_columns"]) - 1))
        run_valid = (
            int(o["candidate_count"]) <= 4
            and int(o["probe_count"]) <= 8
            and len(probes) == int(o["probe_count"])
            and active_vector_valid
            and all(truth(row["model_fingerprint_match"]) and
                    truth(row["bound_override_readback_valid"]) and
                    truth(row["fresh_disposable_model"]) for row in probes)
            and truth(o["lifecycle_valid"])
            and not truth(r["in_memory_model_reused"])
            and int(r["model_count"]) == int(r["model_read_count"])
                == int(r["optimize_count"]) == expected_models
            and math.isclose(total, float(o["total_work"]),
                             rel_tol=0.0, abs_tol=1e-12)
            and math.isclose(total, float(candidate[state]["work"]),
                             rel_tol=0.0, abs_tol=1e-12))
        audits[state] = {"overhead": o, "run_valid": run_valid}
        for row in probes:
            probe_rows.append({"stage": "revision_core_120s", **row})
        for row in priorities:
            priority_rows.append({"stage": "revision_core_120s", **row})
        overhead_rows.append({
            "stage": "revision_core_120s", **o,
            "model_count": r["model_count"],
            "model_read_count": r["model_read_count"],
            "optimize_count": r["optimize_count"],
            "in_memory_model_reused": r["in_memory_model_reused"],
            "end_to_end_work_reconciled": str(math.isclose(
                total, float(candidate[state]["work"]),
                rel_tol=0.0, abs_tol=1e-12)).lower(),
            "run_audit_pass": str(run_valid).lower(),
        })

    results: list[dict[str, object]] = []
    severe_rows: list[dict[str, object]] = []
    lost = false_certificates = correctness_failures = severe_count = 0
    for state in CORE:
        old, new = baseline[state], candidate[state]
        old_cert, new_cert = truth(old["certificate"]), truth(new["certificate"])
        is_severe, reason = severe(old, new)
        old_work, new_work = float(old["work"]), float(new["work"])
        old_gap, new_gap = float(old["gap"]), float(new["gap"])
        old_gi, new_gi = (float(old["gi_common_horizon"]),
                          float(new["gi_common_horizon"]))
        lost_now = old_cert and not new_cert
        false_now = truth(new["false_certificate"])
        correct = (truth(new["evidence_complete"])
                   and truth(new["cap_respected"])
                   and truth(new["model_identity_match"])
                   and model[state]["status"] == "pass"
                   and audits[state]["run_valid"]
                   and not false_now)
        regressed = (new_work > old_work + 1e-9 or
                     (not old_cert and not new_cert and
                      (new_gap > old_gap + 1e-9 or new_gi > old_gi + 1e-9)))
        lost += int(lost_now)
        false_certificates += int(false_now)
        correctness_failures += int(not correct)
        severe_count += int(is_severe)
        o = audits[state]["overhead"]
        results.append({
            "state_id": state,
            "baseline_policy": old["policy"],
            "candidate_policy": new["policy"],
            "process_cap_seconds": new["process_cap_seconds"],
            "executable_sha256": new["executable_sha256"],
            "model_sha256": new["model_sha256"],
            "canonical_model_byte_identical":
                model[state]["three_way_canonical_lp_byte_identical"],
            "baseline_status": old["status"],
            "candidate_status": new["status"],
            "baseline_certificate": str(old_cert).lower(),
            "candidate_certificate": str(new_cert).lower(),
            "lost_baseline_certificate": str(lost_now).lower(),
            "false_certificate": str(false_now).lower(),
            "baseline_work": old["work"],
            "candidate_total_work": new["work"],
            "candidate_terminal_mip_work": o["terminal_mip_work"],
            "candidate_root_plus_probe_work":
                float(o["root_lp_work"]) + float(o["child_probe_work"]),
            "total_work_delta": new_work - old_work,
            "total_work_ratio": new_work / old_work,
            "baseline_process_time_seconds": old["process_time_seconds"],
            "candidate_total_process_time_seconds": new["process_time_seconds"],
            "baseline_gap": old["gap"], "candidate_gap": new["gap"],
            "baseline_gi": old["gi_common_horizon"],
            "candidate_gi": new["gi_common_horizon"],
            "candidate_count": o["candidate_count"],
            "probe_count": o["probe_count"],
            "priority_count": o["priority_count"],
            "fallback_reason": o["fallback_reason"],
            "regressed": str(regressed).lower(),
            "severe_regression": str(is_severe).lower(),
            "severe_regression_reason": reason,
            "engineering_evidence_complete": str(correct).lower(),
        })
        severe_rows.append({
            "mechanism": "A1-R1", "candidate_policy": new["policy"],
            "state_id": state,
            "baseline_certificate": str(old_cert).lower(),
            "candidate_certificate": str(new_cert).lower(),
            "work_ratio": new_work / old_work,
            "work_absolute_increase": new_work - old_work,
            "gi_ratio": new_gi / old_gi if old_gi > 0 else 0.0,
            "gi_absolute_increase": new_gi - old_gi,
            "gap_ratio": new_gap / old_gap if old_gap > 0 else 0.0,
            "gap_absolute_increase": new_gap - old_gap,
            "severe_regression": str(is_severe).lower(),
            "reason": reason,
        })

    base_work = sum(float(baseline[state]["work"]) for state in CORE)
    cand_work = sum(float(candidate[state]["work"]) for state in CORE)
    aggregate_nonworse = cand_work <= base_work + 1e-9
    core_pass = (correctness_failures == false_certificates == lost
                 == severe_count == 0 and aggregate_nonworse)
    decision = {
        "aggregate_a1r_total_work": cand_work,
        "aggregate_m1_v0_work": base_work,
        "aggregate_paired_total_work_nonworse": aggregate_nonworse,
        "aggregate_work_delta": cand_work - base_work,
        "aggregate_work_ratio": cand_work / base_work,
        "candidate": CANDIDATE,
        "confirmation_opened": False,
        "core_cap_seconds": 120,
        "core_gate_passed": core_pass,
        "core_states": CORE,
        "correctness_failures": correctness_failures,
        "decision": "reject_a1r_as_production_backend",
        "development_300s_opened": False,
        "false_certificates": false_certificates,
        "lost_baseline_certificates": lost,
        "reason": "aggregate_end_to_end_work_regression",
        "remaining_adaptive_revisions": 0,
        "schema": "round51-adaptive-branching-revision-decision-v1",
        "severe_regressions": severe_count,
    }
    write_rows(EVIDENCE / "adaptive_branching_revision_probe_evidence.csv",
               probe_rows)
    write_rows(EVIDENCE /
               "adaptive_branching_revision_priority_assignment_audit.csv",
               priority_rows)
    write_rows(EVIDENCE / "adaptive_branching_revision_overhead_audit.csv",
               overhead_rows)
    write_rows(EVIDENCE / "adaptive_branching_revision_candidate_results.csv",
               results)
    write_rows(EVIDENCE /
               "adaptive_branching_revision_severe_regression_audit.csv",
               severe_rows)
    (EVIDENCE / "adaptive_branching_revision_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    # Preserve the already-frozen A1 decision, then regenerate each required
    # paper-facing adaptive table with both bounded candidates exactly once.
    initial_decision = json.loads(
        (EVIDENCE / "adaptive_branching_decision.json").read_text(
            encoding="utf-8"))
    (EVIDENCE / "adaptive_branching_initial_decision.json").write_text(
        json.dumps(initial_decision, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    merges = [
        ("adaptive_branching_probe_evidence.csv", probe_rows, "policy"),
        ("adaptive_branching_priority_assignment_audit.csv", priority_rows,
         "policy"),
        ("adaptive_branching_overhead_audit.csv", overhead_rows, "policy"),
        ("adaptive_branching_candidate_results.csv", results,
         "candidate_policy"),
        ("adaptive_branching_severe_regression_audit.csv", severe_rows,
         "candidate_policy"),
    ]
    for filename, revision_rows, policy_key in merges:
        old_rows = [row for row in read_rows(EVIDENCE / filename)
                    if row[policy_key] != CANDIDATE]
        write_rows(EVIDENCE / filename, old_rows + revision_rows)
    final = {
        "candidates": {
            "a1-root-sparse-2x2": initial_decision,
            CANDIDATE: decision,
        },
        "confirmation_opened": False,
        "decision": "reject_all_round51_adaptive_branching_candidates",
        "development_300s_opened": False,
        "initial_revision_opening_was_contract_authorized": True,
        "reason": "A1_failed_aggregate_and_severe_gates;_A1R_failed_aggregate_gate",
        "remaining_adaptive_revisions": 0,
        "schema": "round51-adaptive-branching-final-decision-v1",
    }
    (EVIDENCE / "adaptive_branching_decision.json").write_text(
        json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if core_pass:
        raise RuntimeError("unexpected A1-R1 core pass requires development")
    print(json.dumps(final, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
