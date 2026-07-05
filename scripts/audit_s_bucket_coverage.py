#!/usr/bin/env python3
"""Audit that S-bucket diagnostics are not used as parent certificate evidence."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, List


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/gf_tailored_bc_plateau_diagnosis_round")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    root = Path(args.results)
    path = root / "s_bucket_coverage_audit.csv"
    rows: List[Dict[str, Any]] = []
    if path.exists():
        with path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
    failures = 0
    out_rows: List[Dict[str, Any]] = []
    for row in rows:
        reasons: List[str] = []
        if b(row.get("coverage_used_for_paper_certificate")):
            reasons.append("diagnostic_s_bucket_used_for_certificate")
        if b(row.get("s_range_certificate_valid")) and row.get("variant") == "s_bucket_diagnostic":
            reasons.append("diagnostic_bucket_marked_certificate_valid")
        ok = not reasons
        failures += 0 if ok else 1
        out_rows.append({**row, "audit_passed": ok, "failures": "|".join(reasons)})
    out = Path(args.out) if args.out else path
    out.parent.mkdir(parents=True, exist_ok=True)
    if out_rows:
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(out_rows[0]))
            writer.writeheader()
            writer.writerows(out_rows)
    else:
        out.write_text("", encoding="utf-8")
    print(f"s_bucket_rows={len(out_rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
