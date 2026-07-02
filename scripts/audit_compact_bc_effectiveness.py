#!/usr/bin/env python3
"""Audit Compact-BC hard-leaf effectiveness output."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/gf_compact_bc_effectiveness_round")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    root = Path(args.results)
    src = root / "natural_hard_leaf_timeprofile.csv"
    if not src.exists():
        src = root / "natural_hard_leaf_progress.csv"
    if not src.exists():
        src = root / "interval_tailored_vs_plain_mip_long.csv"
    if not src.exists():
        src = root / "compact_bc_effectiveness_summary.csv"
    rows = list(csv.DictReader(src.open(newline="", encoding="utf-8"))) if src.exists() else []
    failures = 0
    out_rows = []
    for row in rows:
        reasons = []
        called = str(row.get("compact_bc_called", "")).lower() in {"true", "1", "yes"}
        if row.get("variant", "") in {"tailored", "plain"}:
            called = True
        cls = row.get("closure_source_class", "")
        if cls.startswith("compact_bc") and not called:
            reasons.append("compact_bc_class_without_call")
        final_bound = row.get("final_MIP_bound", "") or row.get("LB", "") or row.get("best_bound", "")
        if called and final_bound == "":
            reasons.append("called_leaf_missing_final_bound")
        runtime = row.get("compact_bc_runtime", "") or row.get("runtime_seconds", "")
        if called and runtime == "":
            reasons.append("called_leaf_missing_runtime")
        if str(row.get("diagnostic_only", "")).lower() == "true" and str(row.get("selected_for_summary", "")).lower() == "true":
            reasons.append("diagnostic_leaf_selected_as_paper_summary")
        failures += bool(reasons)
        out_rows.append({**row, "audit_passed": not reasons, "failures": "|".join(reasons)})
    if not rows:
        failures = 1
        out_rows.append({"audit_passed": False, "failures": "no_hard_leaf_rows"})
    out = Path(args.out) if args.out else root / "compact_bc_effectiveness_audit.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(out_rows[0]))
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"audited_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
