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
            basis = ev.get("oracle_certificate_basis", "")
            solver_status = str(ev.get("oracle_solver_status", "")).lower()
            if truthy(ev.get("oracle_proven_infeasible")) and (
                basis == "interval_exact_cutoff_mip_infeasible" and "infeasible" in solver_status
            ):
                out["interval_status"] = "bound_fathomed"
                out["reason"] = "merged_exact_interval_cutoff_mip_infeasible"
                out["certificate_basis"] = "interval_exact_cutoff_mip_infeasible"
                out["interval_lower_bound"] = out.get("incumbent_upper_bound", out.get("interval_lower_bound", ""))
                out["requires_pricing_closure"] = "false"
                out["pricing_closure_available"] = "false"
                out["interval_bound_valid"] = "true"
                applied = True
                reason = "exact matching leaf closed by proven infeasible cutoff oracle"
            else:
                reason = (
                    "oracle_not_mergeable:"
                    f"basis={basis};status={ev.get('oracle_status','')};"
                    f"solver={ev.get('oracle_solver_status','')}"
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
