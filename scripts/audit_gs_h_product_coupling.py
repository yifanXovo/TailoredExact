#!/usr/bin/env python3
"""Audit G-S-H product-coupling rows."""

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
        enabled = as_bool(data.get("tailored_bc_gs_product_coupling_enabled"))
        if enabled:
            enabled_count += 1
        rows_added = (int(float(data.get("gs_mccormick_rows_added", 0) or 0)) +
                      int(float(data.get("gs_h_upper_rows_added", 0) or 0)) +
                      int(float(data.get("gs_product_callback_rows_added", 0) or 0)))
        lower_mode = str(data.get("tailored_bc_gs_product_lower_row", "off"))
        certified = as_bool(data.get("certified_original_problem")) or data.get("status") == "interval_closed"
        reasons: List[str] = []
        if enabled and rows_added <= 0 and str(data.get("tailored_bc_gs_product_coupling_mode", "")) in {"static", "both"}:
            reasons.append("enabled_without_rows")
        diagnostic_row = as_bool(data.get("diagnostic_row"))
        if certified and lower_mode == "diagnostic" and not diagnostic_row:
            reasons.append("diagnostic_lower_row_in_certified_row")
        if lower_mode == "paper-safe" and "paper_safe" not in str(data.get("gs_product_coupling_proof_status", "")):
            reasons.append("paper_safe_lower_without_proof_status")
        if reasons:
            failures += 1
        rows.append({
            "file": str(path),
            "enabled": enabled,
            "rows_added": rows_added,
            "lower_row_mode": lower_mode,
            "proof_status": data.get("gs_product_coupling_proof_status", ""),
            "audit_passed": not reasons,
            "failures": "|".join(reasons),
        })
    if enabled_count == 0:
        failures += 1
        rows.append({"file": "", "enabled": False, "rows_added": 0,
                     "lower_row_mode": "", "proof_status": "",
                     "audit_passed": False, "failures": "no_gs_rows_exercised"})
    out = Path(args.out) if args.out else root / "gs_h_product_coupling_audit.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"audited_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
