#!/usr/bin/env python3
"""Apply the frozen Round 51 gates to A1 and audit its bounded lifecycle."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"
RUN_ROOT = EVIDENCE / "a1_core_runs"
CORE = ["D1", "D2", "D3", "D4", "D5", "D6", "D9", "D10", "D11"]
BASELINE = "m1-tight-big-m-v0"
CANDIDATE = "a1-root-sparse-2x2"


def truth(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def read_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise RuntimeError(f"refusing to write empty audit: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def severe(old: dict[str, str], new: dict[str, str]) -> tuple[bool, str]:
    old_cert, new_cert = truth(old["certificate"]), truth(new["certificate"])
    reasons: list[str] = []
    if old_cert and not new_cert:
        reasons.append("baseline_certifies_candidate_does_not")
    old_work, new_work = float(old["work"]), float(new["work"])
    old_time, new_time = (float(old["process_time_seconds"]),
                          float(new["process_time_seconds"]))
    if old_cert and new_cert:
        if new_work > 1.5 * old_work and new_work - old_work > 50.0:
            reasons.append("exact_work_ratio_and_absolute")
        if new_time > 1.5 * old_time and new_time - old_time > 60.0:
            reasons.append("exact_time_ratio_and_absolute")
    if not old_cert and not new_cert:
        old_gi, new_gi = (float(old["gi_common_horizon"]),
                          float(new["gi_common_horizon"]))
        old_gap, new_gap = float(old["gap"]), float(new["gap"])
        if new_gi >= 1.5 * old_gi and new_gi - old_gi >= 0.05:
            reasons.append("capped_gi_ratio_and_absolute")
        if new_gap >= 1.5 * old_gap and new_gap - old_gap >= 0.05:
            reasons.append("capped_gap_ratio_and_absolute")
    return bool(reasons), "|".join(reasons) if reasons else "none"


def main() -> None:
    baseline = {row["state_id"]: row for row in read_rows(
        EVIDENCE / "a1_core_m1_raw.csv")}
    candidate = {row["state_id"]: row for row in read_rows(
        EVIDENCE / "a1_core_a1_raw.csv")}
    if set(baseline) != set(CORE) or set(candidate) != set(CORE):
        raise RuntimeError("A1 core summaries do not match the frozen panel")
    if {row["executable_sha256"] for row in baseline.values()} != {
            row["executable_sha256"] for row in candidate.values()}:
        raise RuntimeError("paired A1 core did not use one executable hash")

    model = {row["state_id"]: row for row in read_rows(
        EVIDENCE / "adaptive_branching_model_correctness.csv")}
    probe_rows: list[dict[str, object]] = []
    priority_rows: list[dict[str, object]] = []
    overhead_rows: list[dict[str, object]] = []
    run_audits: dict[str, dict[str, object]] = {}
    for state in CORE:
        run = RUN_ROOT / f"{state}__{CANDIDATE}"
        probes = read_rows(run / "adaptive_branching_probe_evidence.csv")
        priorities = read_rows(
            run / "adaptive_branching_priority_assignment_audit.csv")
        overhead = read_rows(run / "adaptive_branching_overhead_ledger.csv")
        reuse = read_rows(run / "model_reuse_ledger.csv")
        if len(overhead) != 1 or len(reuse) != 1:
            raise RuntimeError(f"invalid lifecycle ledger cardinality: {state}")
        o, r = overhead[0], reuse[0]
        expected_models = 2 + int(o["probe_count"])
        accounting = (float(o["root_lp_work"]) +
                      float(o["child_probe_work"]) +
                      float(o["terminal_mip_work"]))
        active_priorities = [row for row in priorities
                             if int(row["requested_priority"]) > 0]
        run_valid = (
            int(o["candidate_count"]) <= 4
            and int(o["probe_count"]) <= 8
            and int(o["priority_count"]) <= 2
            and len(probes) == int(o["probe_count"])
            and len(active_priorities) == int(o["priority_count"])
            and all(truth(row["model_fingerprint_match"]) and
                    truth(row["bound_override_readback_valid"]) and
                    truth(row["fresh_disposable_model"]) for row in probes)
            and all(truth(row["exact_readback"]) and
                    truth(row["terminal_model_fresh"])
                    for row in priorities)
            and truth(o["lifecycle_valid"])
            and not truth(r["in_memory_model_reused"])
            and int(r["model_count"]) == int(r["model_read_count"])
                == int(r["optimize_count"]) == expected_models
            and math.isclose(accounting, float(o["total_work"]),
                             rel_tol=0.0, abs_tol=1e-12)
            and math.isclose(accounting, float(candidate[state]["work"]),
                             rel_tol=0.0, abs_tol=1e-12))
        run_audits[state] = {
            "active_priorities": active_priorities,
            "overhead": o,
            "run_valid": run_valid,
        }
        for row in probes:
            probe_rows.append({"stage": "core_120s", **row})
        for row in priorities:
            priority_rows.append({"stage": "core_120s", **row})
        overhead_rows.append({
            "stage": "core_120s", **o,
            "model_count": r["model_count"],
            "model_read_count": r["model_read_count"],
            "optimize_count": r["optimize_count"],
            "in_memory_model_reused": r["in_memory_model_reused"],
            "end_to_end_work_reconciled": str(math.isclose(
                accounting, float(candidate[state]["work"]),
                rel_tol=0.0, abs_tol=1e-12)).lower(),
            "run_audit_pass": str(run_valid).lower(),
        })

    results: list[dict[str, object]] = []
    severe_rows: list[dict[str, object]] = []
    lost = false_certificates = correctness_failures = severe_count = 0
    regression_states: list[str] = []
    total_work_regression_states: list[str] = []
    for state in CORE:
        old, new = baseline[state], candidate[state]
        old_cert, new_cert = truth(old["certificate"]), truth(new["certificate"])
        is_severe, reason = severe(old, new)
        old_work, new_work = float(old["work"]), float(new["work"])
        old_gap, new_gap = float(old["gap"]), float(new["gap"])
        old_gi = float(old["gi_common_horizon"])
        new_gi = float(new["gi_common_horizon"])
        lost_now = old_cert and not new_cert
        false_now = truth(new["false_certificate"])
        correct = (truth(new["evidence_complete"])
                   and truth(new["cap_respected"])
                   and truth(new["model_identity_match"])
                   and model[state]["status"] == "pass"
                   and run_audits[state]["run_valid"]
                   and not false_now)
        regressed = (new_work > old_work + 1e-9 or
                     (not old_cert and not new_cert and
                      (new_gap > old_gap + 1e-9 or new_gi > old_gi + 1e-9)))
        if regressed:
            regression_states.append(state)
        if new_work > old_work + 1e-9:
            total_work_regression_states.append(state)
        lost += int(lost_now)
        false_certificates += int(false_now)
        correctness_failures += int(not correct)
        severe_count += int(is_severe)
        o = run_audits[state]["overhead"]
        results.append({
            "state_id": state,
            "baseline_policy": old["policy"],
            "candidate_policy": new["policy"],
            "process_cap_seconds": new["process_cap_seconds"],
            "executable_sha256": new["executable_sha256"],
            "model_sha256": new["model_sha256"],
            "canonical_model_byte_identical":
                model[state]["canonical_lp_byte_identical"],
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
            "mechanism": "A1", "candidate_policy": new["policy"],
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

    # The revision gate is evidence-based and fixed: on every regressed state
    # with priorities, the best probe improves a child bound, while the second
    # score is at most 40% of the first. D4 is also a frozen severe regression.
    priority_regressions = [state for state in total_work_regression_states
                            if len(run_audits[state]["active_priorities"]) == 2]
    best_locally_beneficial = all(
        max(float(run_audits[state]["active_priorities"][0]["delta_down"]),
            float(run_audits[state]["active_priorities"][0]["delta_up"])) > 0.0
        for state in priority_regressions)
    second_ratios = [
        float(run_audits[state]["active_priorities"][1]["score"]) /
        float(run_audits[state]["active_priorities"][0]["score"])
        for state in priority_regressions]
    clear_overreach = (
        not core_pass and severe_count > 0
        and priority_regressions
        and set(priority_regressions) == set(total_work_regression_states)
        and all(len(run_audits[row["state_id"]]["active_priorities"]) == 2
                for row in severe_rows if row["severe_regression"] == "true")
        and best_locally_beneficial
        and max(second_ratios) <= 0.40)
    revision_opened = bool(clear_overreach)

    write_rows(EVIDENCE / "adaptive_branching_probe_evidence.csv", probe_rows)
    write_rows(EVIDENCE / "adaptive_branching_priority_assignment_audit.csv",
               priority_rows)
    write_rows(EVIDENCE / "adaptive_branching_overhead_audit.csv", overhead_rows)
    write_rows(EVIDENCE / "adaptive_branching_candidate_results.csv", results)
    write_rows(EVIDENCE / "adaptive_branching_severe_regression_audit.csv",
               severe_rows)
    revision = {
        "a1_core_failed": not core_pass,
        "a1r_root_sparse_top1_opened": revision_opened,
        "best_probe_locally_beneficial_on_every_priority_regression":
            best_locally_beneficial,
        "clear_two_priority_overreach": clear_overreach,
        "maximum_second_to_best_score_ratio_on_regressed_states":
            max(second_ratios),
        "permitted_change_only":
            "best candidate BranchPriority=1; every other variable=0",
        "priority_regression_states": priority_regressions,
        "all_work_or_capped_progress_regression_states": regression_states,
        "total_work_regression_states": total_work_regression_states,
        "revision_count_after_opening": 1 if revision_opened else 0,
        "schema": "round51-a1-revision-opening-audit-v1",
        "severe_regression_states": [
            row["state_id"] for row in severe_rows
            if row["severe_regression"] == "true"],
    }
    (EVIDENCE / "adaptive_branching_revision_opening_audit.json").write_text(
        json.dumps(revision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    decision = {
        "aggregate_a1_total_work": cand_work,
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
        "decision": "reject_a1_as_defined",
        "development_300s_opened": False,
        "false_certificates": false_certificates,
        "lost_baseline_certificates": lost,
        "reason": "aggregate_work_regression_and_D4_severe_capped_gap_regression",
        "revision_candidate": "a1r-root-sparse-top1" if revision_opened else None,
        "revision_opened": revision_opened,
        "schema": "round51-adaptive-branching-decision-v1",
        "severe_regressions": severe_count,
    }
    (EVIDENCE / "adaptive_branching_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not revision_opened:
        raise RuntimeError("A1 failed but the frozen top-1 revision gate did not open")
    print(json.dumps({"decision": decision, "revision": revision},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
