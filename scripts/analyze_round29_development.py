#!/usr/bin/env python3
"""Summarize retained pre-freeze C4 development and incremental equivalence."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_gurobi_performance_recovery_round29"
RUNS = OUT / "development"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write(path: Path, material: list[dict[str, Any]]) -> None:
    fields = list(material[0]) if material else ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(material)


def value(result: dict[str, Any], key: str,
          default: Any = 0) -> Any:
    current = result.get(key, default)
    return default if current is None else current


def development_summary() -> list[dict[str, Any]]:
    output = []
    for state_path in sorted(RUNS.glob("*__60s/run_state.json")):
        state = load(state_path)
        result_path = state_path.parent / "result.json"
        if not result_path.is_file():
            continue
        result = load(result_path)
        output.append({
            "instance": state["instance"],
            "arm": state["arm"],
            "budget_seconds": state["budget_seconds"],
            "return_code": state["return_code"],
            "emergency_timeout": state["emergency_timeout"],
            "status": result.get("status", ""),
            "exact_phase_started": result.get("exact_phase_started", False),
            "verified_ub": value(result, "upper_bound"),
            "valid_lb": value(result, "lower_bound"),
            "gap": value(result, "gap"),
            "optimize_count": value(
                result, "external_gini_tree_optimize_count"),
            "lp_count": value(
                result, "external_gini_tree_lp_optimize_count"),
            "terminal_mip_count": value(
                result, "external_gini_tree_terminal_mip_optimize_count"),
            "split_count": value(
                result, "external_gini_tree_split_count"),
            "declined_split_count": value(
                result, "external_gini_tree_declined_split_count"),
            "model_read_count": value(
                result, "external_gini_tree_model_read_count"),
            "same_leaf_model_reuse_count": value(
                result,
                "external_gini_tree_in_memory_model_reuse_count"),
            "integer_domain_restore_count": value(
                result,
                "external_gini_tree_integer_domain_restore_count"),
            "lp_pruned_leaf_count": value(
                result, "external_gini_tree_lp_pruned_leaf_count"),
            "open_leaf_count": value(
                result, "external_gini_tree_open_leaf_count"),
            "work": value(result, "external_gini_tree_work"),
            "lp_work": value(result, "external_gini_tree_lp_work"),
            "terminal_mip_work": value(
                result, "external_gini_tree_terminal_mip_work"),
            "peak_memory_gb": value(
                result, "external_gini_tree_peak_memory_gb"),
            "lifecycle_complete": result.get(
                "external_gini_tree_lifecycle_complete", False),
            "strict_certificate": result.get(
                "strict_certified_original_problem", False),
            "result_path": result_path.relative_to(ROOT).as_posix(),
        })
    return output


def equivalence() -> list[dict[str, Any]]:
    cold_dir = RUNS / "moderate_seed4301__c2_cold__60s"
    warm_dir = RUNS / "moderate_seed4301__c4_candidate__60s"
    output: list[dict[str, Any]] = []
    if not cold_dir.is_dir() or not warm_dir.is_dir():
        return output
    cold_lp = {
        row["leaf_id"]: row
        for row in rows(cold_dir / "external/lp_status_ledger.csv")
    }
    warm_lp = {
        row["leaf_id"]: row
        for row in rows(warm_dir / "external/lp_status_ledger.csv")
    }
    for leaf in sorted(set(cold_lp) & set(warm_lp)):
        left, right = cold_lp[leaf], warm_lp[leaf]
        left_bound = float(left["lower_bound"])
        right_bound = float(right["lower_bound"])
        terminal_identity = all(
            left[key] == right[key]
            for key in ("terminal_valid", "optimal", "infeasible",
                        "bound_available", "native_status"))
        bound_identity = (
            not (left["bound_available"] == right["bound_available"] == "1")
            or math.isclose(
                left_bound, right_bound, rel_tol=1e-9, abs_tol=1e-7))
        output.append({
            "comparison": "cold_lp_vs_incremental_lp",
            "leaf_id": leaf,
            "cold_native_status": left["native_status"],
            "incremental_native_status": right["native_status"],
            "cold_bound": left_bound,
            "incremental_bound": right_bound,
            "absolute_bound_difference": abs(left_bound - right_bound),
            "terminal_status_identity": terminal_identity,
            "objective_identity_within_1e_7": bound_identity,
            "passed": terminal_identity and bound_identity,
        })
    cold_splits = {
        row["parent_id"]: row
        for row in rows(cold_dir / "external/split_decision_ledger.csv")
    }
    warm_splits = {
        row["parent_id"]: row
        for row in rows(warm_dir / "external/split_decision_ledger.csv")
    }
    for leaf in sorted(set(cold_splits) & set(warm_splits)):
        left, right = cold_splits[leaf], warm_splits[leaf]
        same = all(
            left[key] == right[key]
            for key in ("decision_valid", "split",
                        "child_infeasibility_trigger",
                        "strict_bound_trigger", "reason"))
        output.append({
            "comparison": "cold_vs_incremental_split_decision",
            "leaf_id": leaf,
            "cold_native_status": "",
            "incremental_native_status": "",
            "cold_bound": "",
            "incremental_bound": "",
            "absolute_bound_difference": "",
            "terminal_status_identity": "",
            "objective_identity_within_1e_7": "",
            "passed": same,
        })
    cold_mips = {
        row["leaf_id"]: row
        for row in rows(cold_dir / "external/paper_optimize_ledger.csv")
        if row.get("solve_kind") == "MIP"
    }
    warm_mips = {
        row["leaf_id"]: row
        for row in rows(warm_dir / "external/paper_optimize_ledger.csv")
        if row.get("solve_kind") == "MIP"
    }
    for leaf in sorted(set(cold_mips) & set(warm_mips)):
        left, right = cold_mips[leaf], warm_mips[leaf]
        same = all(
            left.get(key) == right.get(key)
            for key in (
                "native_status", "optimize_return_code", "model_sha256"))
        output.append({
            "comparison": "cold_vs_incremental_terminal_mip",
            "leaf_id": leaf,
            "cold_native_status": left.get("native_status", ""),
            "incremental_native_status": right.get("native_status", ""),
            "cold_bound": "",
            "incremental_bound": "",
            "absolute_bound_difference": "",
            "terminal_status_identity": same,
            "objective_identity_within_1e_7": "",
            "passed": same,
        })
    return output


def main() -> int:
    summary = development_summary()
    write(OUT / "development_candidate_summary.csv", summary)
    audit = equivalence()
    write(OUT / "development_incremental_equivalence.csv", audit)
    failures = sum(not bool(row["passed"]) for row in audit)
    print(
        f"development_rows={len(summary)} "
        f"equivalence_checks={len(audit)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
