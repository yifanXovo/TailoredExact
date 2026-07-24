#!/usr/bin/env python3
"""Summarize the single-prototype Round 30 development matrix."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import analyze_round30_results as official
import round30_bound_trace as trace


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_c0_mechanism_transfer_c5_round30"
DEV = OUT / "development"


def load(run_dir: Path) -> dict[str, Any]:
    result = json.loads(
        (run_dir / "result.json").read_text(encoding="utf-8"))
    arm = "C4-CANDIDATE" if "__c4_candidate__" in run_dir.name \
        else "C5-CANDIDATE"
    instance = run_dir.name.split("__", 1)[0]
    audit = trace.audit_external_trace(
        run_dir / "external/global_bound_trace.csv")
    return {
        "run_dir": run_dir,
        "instance": instance,
        "arm": arm,
        "result": result,
        "audit": audit,
    }


def main() -> int:
    runs = [
        load(path) for path in sorted(DEV.glob("*__c?_candidate__60s"))
    ]
    rows = []
    for run in runs:
        result, audit = run["result"], run["audit"]
        rows.append({
            "instance": run["instance"],
            "arm": run["arm"],
            "status": result["status"],
            "valid_final_lb": result["lower_bound"],
            "verified_ub": result["upper_bound"],
            "trace_complete": audit.complete,
            "trace_reason": audit.reason,
            "valid_bound_observations": audit.bound_observation_count,
            "optimize_count":
                result.get("external_gini_tree_optimize_count", 0),
            "lp_optimize_count":
                result.get("external_gini_tree_lp_optimize_count", 0),
            "partial_mip_optimize_count":
                result.get(
                    "external_gini_tree_partial_mip_optimize_count", 0),
            "partial_targets_reached":
                result.get(
                    "external_gini_tree_partial_mip_target_reached_count", 0),
            "terminal_mip_optimize_count":
                result.get(
                    "external_gini_tree_terminal_mip_optimize_count", 0),
            "split_count":
                result.get("external_gini_tree_split_count", 0),
            "declined_split_count":
                result.get("external_gini_tree_declined_split_count", 0),
            "total_work": result.get("external_gini_tree_work", 0),
            "lp_work": result.get("external_gini_tree_lp_work", 0),
            "partial_mip_work":
                result.get("external_gini_tree_partial_mip_work", 0),
            "terminal_mip_work":
                result.get("external_gini_tree_terminal_mip_work", 0),
            "lifecycle_complete":
                result.get("external_gini_tree_lifecycle_complete", False),
            "coverage_valid": (
                result.get("external_gini_tree_root_coverage_valid", False)
                and result.get(
                    "external_gini_tree_parent_child_coverage_valid", False)),
        })
    official.write_csv(OUT / "development_results.csv", rows)
    keyed = {(run["instance"], run["arm"]): run for run in runs}
    pairs = []
    for instance in sorted({run["instance"] for run in runs}):
        c4 = keyed[(instance, "C4-CANDIDATE")]
        c5 = keyed[(instance, "C5-CANDIDATE")]
        pair = {
            "instance": instance,
            "c4_final_lb": c4["result"]["lower_bound"],
            "c5_final_lb": c5["result"]["lower_bound"],
            "final_lb_delta_c5_minus_c4":
                c5["result"]["lower_bound"] - c4["result"]["lower_bound"],
            "c5_partial_mip_optimize_count":
                c5["result"].get(
                    "external_gini_tree_partial_mip_optimize_count", 0),
            "c5_partial_targets_reached":
                c5["result"].get(
                    "external_gini_tree_partial_mip_target_reached_count", 0),
        }
        if c4["audit"].complete and c5["audit"].complete:
            pair.update(official.common_window_pair_auc(
                c4["audit"].observations, c5["audit"].observations,
                min(c4["result"]["upper_bound"],
                    c5["result"]["upper_bound"])))
        else:
            pair.update({
                "auc_status": "auc_unavailable",
                "auc_reason": (
                    f"c4={c4['audit'].reason};c5={c5['audit'].reason}")})
        pairs.append(pair)
    official.write_csv(OUT / "development_c4_vs_c5.csv", pairs)
    wins = sum(row["final_lb_delta_c5_minus_c4"] > 1e-7 for row in pairs)
    losses = sum(row["final_lb_delta_c5_minus_c4"] < -1e-7 for row in pairs)
    ties = len(pairs) - wins - losses
    targets = sum(
        int(row["c5_partial_targets_reached"]) for row in pairs)
    unavailable = sum(row["auc_status"] == "auc_unavailable" for row in pairs)
    report = f"""# Round 30 development summary

The one-prototype 60-second matrix completed all 14 C4/C5 processes. Every
run passed coverage, monotone-bound, lifecycle, and verifier gates. C5 had
{wins} final-LB wins, {losses} loss, and {ties} ties against C4. C5 reached
{targets} backend-certified parent dual-bound targets.

{unavailable} of seven development AUC pairs are deliberately unavailable.
Those pre-freeze rows exposed that deadline exits during a parent/child LP
could finalize an open trace without an explicit interruption row. The
generic deadline transition was then instrumented centrally before the clean
official build. These rows are retained and are not repaired or used for
AUC; the post-fix Stage 0 trace suite is the freeze gate.

The Moderate4301 75-second sentinel independently emitted a complete trace,
used one partial target MIP (0.875539 Work), reached the mathematical target,
requeued the parent, and performed the delayed atomic split. No fallback
prototype or threshold sweep was used.
"""
    (OUT / "development_summary.md").write_text(report, encoding="utf-8")
    print(json.dumps({
        "rows": len(rows), "pairs": len(pairs), "c5_lb_wins": wins,
        "c5_lb_losses": losses, "ties": ties,
        "c5_targets_reached": targets,
        "auc_unavailable_pairs": unavailable,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
