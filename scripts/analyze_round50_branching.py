#!/usr/bin/env python3
"""Finalize the bounded Round 50 semantic-branching iteration."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def truth(value: object) -> bool:
    return str(value).lower() in {"1", "true", "yes"}


def rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def severe_regression(baseline: dict[str, str], candidate: dict[str, str]) -> tuple[bool, str]:
    bcert = truth(baseline["certificate"])
    ccert = truth(candidate["certificate"])
    if bcert and not ccert:
        return True, "baseline_certifies_candidate_does_not"
    if bcert and ccert:
        bw = float(baseline["work"])
        cw = float(candidate["work"])
        bt = float(baseline["process_time_seconds"])
        ct = float(candidate["process_time_seconds"])
        if cw / max(1e-12, bw) > 1.50 and cw - bw > 50.0:
            return True, "exact_Work_ratio_gt_1.50_and_delta_gt_50"
        if ct / max(1e-12, bt) > 1.50 and ct - bt > 60.0:
            return True, "exact_time_ratio_gt_1.50_and_delta_gt_60"
        return False, "none"
    bgi = float(baseline["gi_common_horizon"])
    cgi = float(candidate["gi_common_horizon"])
    bgap = float(baseline["gap"])
    cgap = float(candidate["gap"])
    if cgi >= 1.50 * bgi and cgi - bgi >= 0.05:
        return True, "capped_GI_ratio_ge_1.50_and_delta_ge_0.05"
    if cgap >= 1.50 * bgap and cgap - bgap >= 0.05:
        return True, "capped_gap_ratio_ge_1.50_and_delta_ge_0.05"
    return False, "none"


def add_phase(output: list[dict[str, object]], phase: str,
              policy: str, current_rows: list[dict[str, str]],
              baseline_rows: dict[str, dict[str, str]]) -> None:
    for row in current_rows:
        baseline = baseline_rows[row["state_id"]]
        severe, reason = (False, "baseline") if policy == "interval-mip-v0" \
            else severe_regression(baseline, row)
        output.append({
            "phase": phase, "state_id": row["state_id"],
            "instance": row["instance"], "policy": policy,
            "process_cap_seconds": row["process_cap_seconds"],
            "executable_sha256": row["executable_sha256"],
            "model_identity_match": row["model_identity_match"],
            "branch_priority_assignment_status": row["branch_priority_assignment_status"],
            "branch_priority_tiers": row.get(
                "branch_priority_tiers", "all:all:p0=0"),
            "status": row["status"], "certificate": row["certificate"],
            "false_certificate": row["false_certificate"],
            "work": row["work"], "process_time_seconds": row["process_time_seconds"],
            "nodes": row["nodes"], "root_work": row["root_work"],
            "root_relaxation_bound": row["root_relaxation_bound"],
            "final_root_cut_bound": row["final_root_cut_bound"],
            "lower_bound": row["lower_bound"],
            "verified_upper_bound": row["verified_upper_bound"],
            "gap": row["gap"], "gi_common_horizon": row["gi_common_horizon"],
            "baseline_certificate": baseline["certificate"],
            "baseline_work": baseline["work"],
            "work_ratio": format(float(row["work"]) /
                                 max(1e-12, float(baseline["work"])), ".17g"),
            "work_delta": format(float(row["work"]) - float(baseline["work"]), ".17g"),
            "baseline_gi": baseline["gi_common_horizon"],
            "gi_delta": format(float(row["gi_common_horizon"]) -
                               float(baseline["gi_common_horizon"]), ".17g"),
            "baseline_gap": baseline["gap"],
            "gap_delta": format(float(row["gap"]) - float(baseline["gap"]), ".17g"),
            "severe_regression": str(severe).lower(),
            "severe_regression_reason": reason,
            "evidence_complete": row["evidence_complete"],
            "cap_respected": row["cap_respected"],
            "artifact_dir": row["artifact_dir"],
        })


def main() -> None:
    core_paths = {
        "interval-mip-v0": EVIDENCE / "iteration1_core_v0_120s.csv",
        "b1-primitive-first": EVIDENCE / "iteration1_core_b1_120s.csv",
        "b2-route-first": EVIDENCE / "iteration1_core_b2_120s.csv",
        "b3-operation-first": EVIDENCE / "iteration1_core_b3_120s.csv",
    }
    qualification_paths = {
        "interval-mip-v0": EVIDENCE / "iteration1_qualification_v0_300s.csv",
        "b1-primitive-first": EVIDENCE / "iteration1_qualification_b1_300s.csv",
    }
    core = {policy: rows(path) for policy, path in core_paths.items()}
    qualification = {policy: rows(path) for policy, path in qualification_paths.items()}
    if any(len(value) != 9 for value in core.values()):
        raise RuntimeError("incomplete branching core panel")
    if any(len(value) != 14 for value in qualification.values()):
        raise RuntimeError("incomplete branching qualification panel")
    all_rows = [row for value in core.values() for row in value] + [
        row for value in qualification.values() for row in value]
    if len({row["executable_sha256"] for row in all_rows}) != 1:
        raise RuntimeError("branching executable mismatch")
    if any(not truth(row["model_identity_match"]) or
           not truth(row["evidence_complete"]) or
           not truth(row["cap_respected"]) or truth(row["false_certificate"])
           for row in all_rows):
        raise RuntimeError("branching evidence gate failed")
    for policy, policy_rows in core.items():
        expected = "default_no_assignment" if policy == "interval-mip-v0" else "applied"
        if any(row["branch_priority_assignment_status"] != expected
               for row in policy_rows):
            raise RuntimeError(f"priority assignment failed for {policy}")

    output: list[dict[str, object]] = []
    core_baseline = {row["state_id"]: row for row in core["interval-mip-v0"]}
    for policy, policy_rows in core.items():
        add_phase(output, "core_120s", policy, policy_rows, core_baseline)
    qualification_baseline = {
        row["state_id"]: row for row in qualification["interval-mip-v0"]}
    for policy, policy_rows in qualification.items():
        add_phase(output, "qualification_300s", policy, policy_rows,
                  qualification_baseline)

    result_path = EVIDENCE / "branching_candidate_results.csv"
    fields = list(output[0].keys())
    with result_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)

    qualified_base = qualification["interval-mip-v0"]
    qualified_b1 = qualification["b1-primitive-first"]
    total_ratio = sum(float(row["work"]) for row in qualified_b1) / sum(
        float(row["work"]) for row in qualified_base)
    exact_base = sum(truth(row["certificate"]) for row in qualified_base)
    exact_b1 = sum(truth(row["certificate"]) for row in qualified_b1)
    severe_rows = [row for row in output if row["phase"] == "qualification_300s"
                   and row["policy"] == "b1-primitive-first"
                   and truth(row["severe_regression"])]

    # Priority values must depend only on semantic family and policy.
    tier_maps: dict[str, dict[str, set[str]]] = {}
    for policy in ("b1-primitive-first", "b2-route-first", "b3-operation-first"):
        mapping: dict[str, set[str]] = {}
        for row in core[policy]:
            for token in row["branch_priority_tiers"].split(";"):
                family_type, right = token.split(":p", 1)
                family = family_type.split(":", 1)[0]
                priority = right.split("=", 1)[0]
                mapping.setdefault(family, set()).add(priority)
        if any(len(values) != 1 for values in mapping.values()):
            raise RuntimeError(f"nondeterministic tiers for {policy}")
        tier_maps[policy] = mapping

    audit = f"""# Round 50 tailored branching policy audit

All four core policies used one executable (`{all_rows[0]['executable_sha256']}`), identical canonical model fingerprints, and nine frozen states at 120 seconds. B1, B2, and B3 assigned priorities to every integer variable through the semantic registry; assignment status was `applied` on every candidate row. Priority tiers were deterministic by semantic family and ordinal only. Default v0 assigned no priorities.

B2 was rejected in the core screen after losing D4 and D10 certificates. B3 was rejected because D4 Work rose from 129.528 to 195.896 (ratio 1.512, delta 66.368), a frozen severe regression. B1 alone qualified, but on the full 300-second D1-D14 panel it lost D3's v0 certificate ({exact_base} versus {exact_b1} total certificates) and severely worsened D14 capped proof progress. Its aggregate Work ratio was {total_ratio:.6f}. B1 did materially improve D10 and D12, demonstrating a local semantic effect, but it failed the no-lost-certificate and no-severe-regression gates.

No tailored branching policy is accepted. `interval-mip-v0` default Gurobi branching is restored as the cumulative backend. Candidate modes remain default-off solely to reproduce the rejected ablations; they are not selected by any preset or instance/time/size dispatch.
"""
    (EVIDENCE / "branching_policy_audit.md").write_text(audit, encoding="utf-8")

    decision = {
        "schema": "round50-branching-iteration-decision-v1",
        "iteration": 1,
        "status": "complete",
        "classification": "default_branching_retained",
        "active_policy_after_iteration": "interval-mip-v0",
        "accepted_changes": [],
        "candidate_decisions": [
            {"policy": "b1-primitive-first", "decision": "reject",
             "reason": "lost D3 qualification certificate and severe D14 capped regression"},
            {"policy": "b2-route-first", "decision": "reject",
             "reason": "lost D4 and D10 core certificates"},
            {"policy": "b3-operation-first", "decision": "reject",
             "reason": "severe D4 exact-row Work regression"},
        ],
        "core_row_count": 36,
        "qualification_row_count": 28,
        "qualification_baseline_certificate_count": exact_base,
        "qualification_b1_certificate_count": exact_b1,
        "qualification_b1_aggregate_work_ratio": total_ratio,
        "qualification_b1_severe_states": [row["state_id"] for row in severe_rows],
        "correctness_failures": 0,
        "false_certificates": 0,
        "model_identity_failures": 0,
        "priority_assignment_failures": 0,
        "confirmation_opened": False,
        "post_screen_tuning": False,
        "candidate_modes_default_off_for_reproduction": True,
        "runtime_dispatch": False,
        "results_path": result_path.relative_to(ROOT).as_posix(),
        "results_sha256": sha256(result_path),
        "input_summary_hashes": {
            path.relative_to(ROOT).as_posix(): sha256(path)
            for path in [*core_paths.values(), *qualification_paths.values()]
        },
    }
    (EVIDENCE / "branching_iteration_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
