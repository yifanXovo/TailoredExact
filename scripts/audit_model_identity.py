#!/usr/bin/env python3
"""Audit fixed-interval model identity records for the plateau round."""

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


def fallback_rows(root: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for name in ("dominant_bucket_longrun.csv", "adaptive_child_longrun.csv", "secondary_regression_summary.csv"):
        for row in read_csv(root / name):
            rows.append(row)
    return rows


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
    rows = read_csv(root / "model_identity_audit.csv")
    if not rows:
        rows = fallback_rows(root)
    out_rows: List[Dict[str, Any]] = []
    failures = 0
    for row in rows:
        reasons: List[str] = []
        if not row.get("command_hash"):
            reasons.append("missing_command_hash")
        if (
            str(row.get("compact_bc_solver_threads", "")) not in {"1", "1.0"} and
            row.get("thread_fairness_class") != "one_thread_fair"
        ):
            reasons.append("not_single_thread")
        if row.get("variant") not in {"callback_no_cuts"} and not b(row.get("model_lp_exists")):
            reasons.append("missing_exported_lp")
        ok = not reasons
        failures += 0 if ok else 1
        out_rows.append({**row, "audit_passed": ok, "failures": "|".join(reasons)})
    out = Path(args.out) if args.out else root / "model_identity_audit.csv"
    write_csv(out, out_rows)
    print(f"model_identity_rows={len(out_rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
