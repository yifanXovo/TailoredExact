#!/usr/bin/env python3
"""Audit plateau-round progress traces and final best-bound preservation."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, List


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/gf_tailored_bc_plateau_diagnosis_round")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    root = Path(args.results)
    source = root / "bound_trace_audit.csv"
    rows = read_csv(source)
    audited: List[Dict[str, Any]] = []
    failures = 0
    for row in rows:
        reasons: List[str] = []
        if not b(row.get("audit_passed")):
            reasons.append(row.get("failures", "bound_trace_failed") or "bound_trace_failed")
        if (
            str(row.get("progress_path", "")) and
            "plain_fixed_interval_mip" not in str(row.get("variant", "")) and
            int(float(row.get("valid_checkpoint_rows", 0) or 0)) <= 0
        ):
            reasons.append("progress_trace_has_no_valid_cplex_bound")
        ok = not reasons
        failures += 0 if ok else 1
        audited.append({**row, "audit_passed": ok, "failures": "|".join(reasons)})
    out = Path(args.out) if args.out else source
    write_csv(out, audited)
    print(f"plateau_bound_trace_rows={len(audited)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
