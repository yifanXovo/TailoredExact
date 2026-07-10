#!/usr/bin/env python3
"""Audit disaggregated S-e_i product estimator rows."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "on"}


def iter_json(raw: Path) -> Iterable[tuple[Path, Dict[str, Any]]]:
    for path in sorted(raw.rglob("*.json")):
        if path.name.endswith(".trace.json"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict):
            yield path, data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", default="results/gf_tailored_bc_structural_cut_round")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    root = Path(args.results)
    rows: List[Dict[str, Any]] = []
    failures = 0
    enabled_count = 0
    for path, data in iter_json(root / "raw"):
        enabled = as_bool(data.get("tailored_bc_disaggregated_sp_estimator_enabled"))
        if enabled:
            enabled_count += 1
        vars_added = int(float(data.get("disagg_sp_variables_added", 0) or 0))
        rows_added = int(float(data.get("disagg_sp_mccormick_rows_added", 0) or 0)) + int(float(data.get("disagg_sp_estimator_rows_added", 0) or 0))
        reasons: List[str] = []
        if enabled and str(data.get("tailored_bc_disaggregated_sp_mode", "")) in {"static", "both"}:
            if vars_added <= 0:
                reasons.append("enabled_without_T_variables")
            if rows_added <= 0:
                reasons.append("enabled_without_rows")
        if enabled and "paper_safe" not in str(data.get("disagg_sp_proof_status", "")) and rows_added > 0:
            reasons.append("rows_without_paper_safe_proof_status")
        if reasons:
            failures += 1
        rows.append({
            "file": str(path),
            "enabled": enabled,
            "variables_added": vars_added,
            "rows_added": rows_added,
            "replace_aggregate": data.get("tailored_bc_disaggregated_sp_replace_aggregate", ""),
            "proof_status": data.get("disagg_sp_proof_status", ""),
            "audit_passed": not reasons,
            "failures": "|".join(reasons),
        })
    if enabled_count == 0:
        failures += 1
        rows.append({"file": "", "enabled": False, "variables_added": 0,
                     "rows_added": 0, "replace_aggregate": "",
                     "proof_status": "", "audit_passed": False,
                     "failures": "no_disaggregated_sp_rows_exercised"})
    out = Path(args.out) if args.out else root / "disaggregated_sp_estimator_audit.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"audited_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
