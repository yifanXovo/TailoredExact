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
    src = root / "compact_bc_effectiveness_summary.csv"
    rows = list(csv.DictReader(src.open(newline="", encoding="utf-8"))) if src.exists() else []
    failures = 0
    out_rows = []
    for row in rows:
        reasons = []
        called = str(row.get("compact_bc_called", "")).lower() in {"true", "1", "yes"}
        cls = row.get("closure_source_class", "")
        if cls.startswith("compact_bc") and not called:
            reasons.append("compact_bc_class_without_call")
        if called and row.get("final_MIP_bound", "") == "":
            reasons.append("called_leaf_missing_final_bound")
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
