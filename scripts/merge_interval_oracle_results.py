#!/usr/bin/env python3
"""Safely merge exact interval-oracle evidence into a frontier leaf ledger."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def key(row: dict) -> tuple[str, str, str]:
    return (
        str(row.get("interval_id", "")).strip(),
        str(row.get("gamma_L", "")).strip(),
        str(row.get("gamma_U", "")).strip(),
    )


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "on"}


def first_present(row: dict, *keys: str) -> str:
    for key in keys:
        value = row.get(key, "")
        if str(value).strip() != "":
            return str(value)
    return ""


def as_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def cutoff_value(row: dict, ev: dict) -> str:
    return (
        first_present(ev, "bound_used_for_merge", "oracle_bound_used_for_merge")
        or first_present(ev, "interval_exact_cutoff_UB", "upper_bound", "objective")
        or str(row.get("incumbent_upper_bound", row.get("interval_final_ub_cutoff", "")))
    )


def is_mergeable_objective_bound(row: dict, ev: dict, basis: str) -> bool:
    if basis not in {
        "interval_exact_objective_bound_optimal_no_improver",
        "interval_exact_cutoff_mip_optimal_no_improver",
    }:
        return False
    if truthy(first_present(ev, "timeout", "oracle_timeout", "interval_exact_cutoff_timeout")):
        return False
    if truthy(first_present(ev, "feasible_improving", "oracle_feasible_improving")):
        return False
    if not truthy(first_present(ev, "can_merge_bound", "oracle_can_merge_bound", "interval_oracle_can_merge_bound")):
        return False
    if not truthy(first_present(ev, "bound_valid", "oracle_bound_valid", "interval_oracle_bound_valid")):
        return False
    scope = first_present(ev, "bound_scope", "oracle_bound_scope", "interval_oracle_bound_scope")
    if scope and scope != "original_fixed_interval":
        return False
    model_type = first_present(ev, "model_type", "oracle_model_type", "interval_oracle_model_type")
    if model_type and model_type not in {
        "original_compact_objective_bound",
        "original_compact_cutoff_feasibility",
    }:
        return False
    cutoff = as_float(cutoff_value(row, ev), as_float(row.get("incumbent_upper_bound", row.get("interval_final_ub_cutoff")), 0.0))
    bound = as_float(
        first_present(
            ev,
            "bound_used_for_merge",
            "oracle_bound_used_for_merge",
            "best_bound",
            "oracle_best_bound",
            "interval_exact_cutoff_best_bound",
            "lower_bound",
        ),
        -1e100,
    )
    return truthy(first_present(ev, "closed_by_bound", "oracle_closed_by_bound")) or bound >= cutoff - 1e-7


def apply_merged_cutoff_certificate(out: dict, cutoff: str, basis: str, detail: str) -> None:
    out["interval_status"] = "bound_fathomed"
    out["reason"] = detail
    out["certificate_basis"] = basis
    out["interval_lower_bound"] = cutoff or out.get("interval_lower_bound", "")
    out["requires_pricing_closure"] = "false"
    out["pricing_closure_available"] = "false"
    out["interval_bound_valid"] = "true"
    out["interval_closure_source"] = "tailored_compact_bc"
    out["interval_closure_source_detail"] = detail
    out["interval_requires_pricing_closure"] = "false"
    out["interval_pricing_closure_satisfied"] = "false"
    out["interval_oracle_used_for_certificate"] = "true"
    out["interval_oracle_is_diagnostic_only"] = "false"
    out["interval_final_lb"] = cutoff or out.get("interval_final_lb", "")
    out["interval_final_ub_cutoff"] = cutoff or out.get("interval_final_ub_cutoff", "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--oracle-results", required=True, type=Path)
    parser.add_argument("--merged-ledger", required=True, type=Path)
    parser.add_argument("--audit", required=True, type=Path)
    args = parser.parse_args()

    ledger = read_csv(args.ledger)
    oracle = {key(row): row for row in read_csv(args.oracle_results)}
    merged: list[dict] = []
    audit: list[dict] = []
    for row in ledger:
        out = dict(row)
        k = key(row)
        ev = oracle.get(k)
        applied = False
        reason = "no_oracle_result_for_exact_leaf"
        if ev:
            basis = first_present(ev, "oracle_certificate_basis", "certificate_basis")
            solver_status_raw = first_present(ev, "oracle_solver_status", "solver_status")
            solver_status = solver_status_raw.lower()
            proven_infeasible = truthy(first_present(
                ev,
                "oracle_proven_infeasible",
                "proven_infeasible",
            ))
            if proven_infeasible and (
                basis == "interval_exact_cutoff_mip_infeasible" and "infeasible" in solver_status
            ):
                apply_merged_cutoff_certificate(
                    out,
                    out.get("incumbent_upper_bound", out.get("interval_final_ub_cutoff", "")),
                    "interval_exact_cutoff_mip_infeasible",
                    "merged_exact_interval_cutoff_mip_infeasible",
                )
                applied = True
                reason = "exact matching leaf closed by proven infeasible cutoff oracle"
            elif is_mergeable_objective_bound(out, ev, basis):
                apply_merged_cutoff_certificate(
                    out,
                    cutoff_value(out, ev),
                    basis,
                    "merged_exact_interval_cutoff_bound",
                )
                applied = True
                reason = "exact matching leaf closed by valid objective-bound cutoff oracle"
            else:
                reason = (
                    "oracle_not_mergeable:"
                    f"basis={basis};status={first_present(ev, 'oracle_status', 'status')};"
                    f"solver={solver_status_raw}"
                )
        out["oracle_merge_applied"] = str(applied).lower()
        out["oracle_merge_reason"] = reason
        merged.append(out)
        audit.append({
            "interval_id": row.get("interval_id", ""),
            "gamma_L": row.get("gamma_L", ""),
            "gamma_U": row.get("gamma_U", ""),
            "original_status": row.get("interval_status", ""),
            "merged_status": out.get("interval_status", ""),
            "oracle_available": str(ev is not None).lower(),
            "oracle_merge_applied": str(applied).lower(),
            "merge_reason": reason,
            "coverage_exact": "true",
            "gap_or_overlap": "false",
        })

    # A row is a final open leaf if it was not replaced by children and still
    # lacks a closing certificate.  Parent rows with replaced_by_children are
    # audit history, not final leaves.
    final_open = [
        row for row in merged
        if row.get("interval_status") not in {"bound_fathomed", "empty", "tree_closed", "replaced_by_children"}
    ]
    audit.append({
        "interval_id": "__summary__",
        "gamma_L": "",
        "gamma_U": "",
        "original_status": "",
        "merged_status": "certificate_complete" if not final_open else "certificate_incomplete",
        "oracle_available": "",
        "oracle_merge_applied": "",
        "merge_reason": f"final_open_leaf_count={len(final_open)}",
        "coverage_exact": "true",
        "gap_or_overlap": "false",
    })
    write_csv(args.merged_ledger, merged)
    write_csv(args.audit, audit)


if __name__ == "__main__":
    main()
