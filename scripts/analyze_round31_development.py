#!/usr/bin/env python3
"""Summarize the prescribed pre-freeze C6 development runs."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_nonblocking_gurobi_c6_round31"
RUNS = OUT / "development"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def main() -> int:
    rows = []
    hashes = set()
    for state_path in sorted(RUNS.glob("*__c6_candidate__71s/run_state.json")):
        state = load(state_path)
        result = load(state_path.parent / "result.json")
        hashes.add(state["executable_sha256"])
        rows.append({
            "instance": state["instance"],
            "budget_seconds": state["budget_seconds"],
            "executable_sha256": state["executable_sha256"],
            "return_code": state["return_code"],
            "emergency_timeout": state["emergency_timeout"],
            "status": result.get("status"),
            "exact_phase_started": result.get("exact_phase_started"),
            "excluded_pre_exact_hga_deadline": (
                not result.get("exact_phase_started") and
                result.get("status") == "paper_hga_global_deadline"),
            "valid_final_lb": result.get(
                "external_gini_tree_global_lower_bound"),
            "verified_ub": result.get(
                "external_gini_tree_verified_upper_bound"),
            "strict_certificate":
                result.get("strict_certified_original_problem"),
            "coverage_valid": (
                result.get("external_gini_tree_root_coverage_valid")
                and result.get(
                    "external_gini_tree_parent_child_coverage_valid")),
            "bounds_monotone": (
                result.get("external_gini_tree_global_bound_monotone")
                and result.get(
                    "external_gini_tree_leaf_bounds_monotone")),
            "lifecycle_complete":
                result.get("external_gini_tree_lifecycle_complete"),
            "parent_lp_requeues":
                result.get("external_gini_tree_parent_lp_requeue_count"),
            "next_leaf_target_phases":
                result.get(
                    "external_gini_tree_next_leaf_target_phase_count"),
            "next_leaf_targets_reached":
                result.get(
                    "external_gini_tree_next_leaf_target_reached_count"),
            "child_target_phases":
                result.get(
                    "external_gini_tree_child_bound_target_phase_count"),
            "native_requeues":
                result.get("external_gini_tree_native_requeue_count"),
            "child_lookaheads_avoided":
                result.get(
                    "external_gini_tree_child_lookahead_avoided_count"),
            "forced_splits_avoided":
                result.get(
                    "external_gini_tree_forced_split_avoided_count"),
            "splits": result.get("external_gini_tree_split_count"),
            "terminal_mip_calls":
                result.get(
                    "external_gini_tree_terminal_mip_optimize_count"),
            "terminal_mip_work":
                result.get("external_gini_tree_terminal_mip_work"),
            "lp_cutoff_prunes":
                result.get("external_gini_tree_lp_pruned_leaf_count"),
            "failure_reason":
                result.get("external_gini_tree_failure_reason"),
        })
    if len(rows) != 11:
        raise RuntimeError(
            f"expected 11 final development runs, found {len(rows)}")
    if len(hashes) != 1:
        raise RuntimeError("development executable identity changed")
    correctness = all(
        row["return_code"] == 0 and not row["emergency_timeout"] and
        ((row["coverage_valid"] and row["bounds_monotone"] and
          row["lifecycle_complete"])
         if row["exact_phase_started"]
         else row["excluded_pre_exact_hga_deadline"])
        for row in rows)
    write_csv(OUT / "c6_development_summary.csv", rows)
    summary = {
        "schema": "round31-c6-development-selection-v1",
        "runs": len(rows),
        "single_executable_identity": True,
        "executable_sha256": next(iter(hashes)),
        "correctness_passed": correctness,
        "c6_exact_phase_runs": sum(
            bool(row["exact_phase_started"]) for row in rows),
        "excluded_pre_exact_hga_deadline_runs": sum(
            bool(row["excluded_pre_exact_hga_deadline"]) for row in rows),
        "strict_certificates": sum(
            bool(row["strict_certificate"]) for row in rows),
        "parent_lp_requeues": sum(
            int(row["parent_lp_requeues"]) for row in rows),
        "next_leaf_target_phases": sum(
            int(row["next_leaf_target_phases"]) for row in rows),
        "next_leaf_targets_reached": sum(
            int(row["next_leaf_targets_reached"]) for row in rows),
        "child_target_phases": sum(
            int(row["child_target_phases"]) for row in rows),
        "native_requeues": sum(
            int(row["native_requeues"]) for row in rows),
        "child_lookaheads_avoided": sum(
            int(row["child_lookaheads_avoided"]) for row in rows),
        "forced_splits_avoided": sum(
            int(row["forced_splits_avoided"]) for row in rows),
        "splits": sum(int(row["splits"]) for row in rows),
        "terminal_mip_calls": sum(
            int(row["terminal_mip_calls"]) for row in rows),
        "terminal_mip_work": sum(
            float(row["terminal_mip_work"]) for row in rows),
        "lp_cutoff_prunes": sum(
            int(row["lp_cutoff_prunes"]) for row in rows),
        "selected_candidate": "C6-CANDIDATE",
        "fallback_prototype_used": False,
        "selection_basis":
            "Phase A mechanism evidence plus uniform 11-instance "
            "correctness/mechanism development matrix",
    }
    (OUT / "c6_development_selection.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not correctness:
        raise RuntimeError("development correctness gate failed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
