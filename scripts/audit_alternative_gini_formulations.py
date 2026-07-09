#!/usr/bin/env python3
"""Audit alternative exact Gini formulation benchmark metadata."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, List


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.is_dir():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: List[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = Path(args.results)
    rows: List[Dict[str, Any]] = []
    failures = 0

    comparison = read_csv(root / "alternative_formulation_comparison.csv")
    audit_rows = read_csv(root / "alternative_formulation_metadata.csv")
    if not audit_rows:
        audit_rows = read_csv(root / "alternative_formulation_audit_source.csv")
    if not audit_rows:
        audit_rows = read_csv(root / "alternative_formulation_audit.csv")
    equivalence = read_csv(root / "alternative_formulation_equivalence_test.csv")
    rejection = read_csv(root / "alternative_formulation_rejection_notes.csv")

    if not comparison:
        rows.append({"table": "alternative_formulation_comparison.csv", "audit_passed": False, "failures": "missing_or_empty"})
        failures += 1

    for row in comparison:
        reasons: List[str] = []
        formulation = row.get("formulation_name", "")
        exactness = row.get("exactness_status", row.get("formulation_exactness", ""))
        role = row.get("formulation_role", "")
        status = row.get("formulation_status", row.get("status", ""))
        if not formulation:
            reasons.append("missing_formulation_name")
        if exactness not in {"exact", "tolerance_exact", "exact_but_too_large", "approximate_diagnostic_only", "rejected_not_exact"}:
            reasons.append("unknown_exactness_status")
        if role != "benchmark_only":
            reasons.append("alternative_formulation_not_benchmark_only")
        if exactness == "exact" and status == "exact_but_too_large":
            reasons.append("exact_row_marked_too_large")
        if "approx" in formulation.lower() and exactness == "exact":
            reasons.append("approximate_formulation_labelled_exact")
        ok = not reasons
        failures += 0 if ok else 1
        rows.append({**row, "table": "alternative_formulation_comparison.csv", "audit_passed": ok, "failures": "|".join(reasons)})

    if not audit_rows:
        rows.append({"table": "alternative_formulation_metadata.csv", "audit_passed": False, "failures": "missing_or_empty"})
        failures += 1
    for row in audit_rows:
        reasons = []
        formulation = row.get("formulation_name", "")
        exactness = row.get("exactness_status", "")
        coverage = row.get("coverage_valid", "")
        if exactness == "exact" and coverage not in {"true", "True", "1"}:
            reasons.append("exact_formulation_without_coverage")
        if formulation == "exact_s_selector" and truthy(row.get("selector_values_included", "")) is False and exactness == "exact":
            reasons.append("selector_missing_values")
        if formulation == "exact_s_parametric_cutoff" and row.get("parametric_cutoff_equivalence", "") not in {"true", "True", "1", "not_run_too_large"}:
            reasons.append("parametric_cutoff_equivalence_missing")
        ok = not reasons
        failures += 0 if ok else 1
        rows.append({**row, "table": "alternative_formulation_metadata.csv", "audit_passed": ok, "failures": "|".join(reasons)})

    if not equivalence:
        rows.append({"table": "alternative_formulation_equivalence_test.csv", "audit_passed": False, "failures": "missing_or_empty"})
        failures += 1
    for row in equivalence:
        reasons = []
        if row.get("equivalence_passed", "") not in {"true", "True", "1"}:
            reasons.append("toy_equivalence_failed")
        ok = not reasons
        failures += 0 if ok else 1
        rows.append({**row, "table": "alternative_formulation_equivalence_test.csv", "audit_passed": ok, "failures": "|".join(reasons)})

    for row in rejection:
        reasons = []
        if row.get("could_be_diagnostic", "") == "":
            reasons.append("missing_diagnostic_flag")
        if not row.get("exactness_obstacle"):
            reasons.append("missing_exactness_obstacle")
        ok = not reasons
        failures += 0 if ok else 1
        rows.append({**row, "table": "alternative_formulation_rejection_notes.csv", "audit_passed": ok, "failures": "|".join(reasons)})

    write_csv(Path(args.out), rows)
    print(f"alternative_formulation_audit_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
