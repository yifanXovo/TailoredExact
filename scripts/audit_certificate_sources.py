#!/usr/bin/env python3
"""Audit compact-BC certificate-source attribution tables."""

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
    src = root / "certificate_source_summary.csv"
    rows = list(csv.DictReader(src.open(newline="", encoding="utf-8"))) if src.exists() else []
    failures = 0
    out_rows = []
    allowed = {
        "relaxation_only", "relaxation_plus_compact_bc",
        "relaxation_plus_compact_bc_noncertified", "unresolved",
        "wrapper_checkpoint_only", "benchmark_only",
        "compact_bc_leaf_diagnostic", "invalid_or_unknown",
    }
    for row in rows:
        reasons = []
        cls = row.get("row_certificate_source_class", "")
        certified = str(row.get("certified_original_problem", "")).lower() == "true"
        if cls not in allowed:
            reasons.append("unknown_row_source_class")
        if certified and cls in {"unresolved", "wrapper_checkpoint_only", "invalid_or_unknown"}:
            reasons.append("certified_row_has_invalid_source_class")
        if reasons:
            failures += 1
        out_rows.append({**row, "audit_passed": not reasons, "failures": "|".join(reasons)})
    out = Path(args.out) if args.out else root / "certificate_source_audit.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out_rows:
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(out_rows[0]))
            writer.writeheader()
            writer.writerows(out_rows)
    else:
        out.write_text("", encoding="utf-8")
    print(f"audited_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
