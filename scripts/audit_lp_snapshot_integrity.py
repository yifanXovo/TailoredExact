#!/usr/bin/env python3
"""Audit LP/fractional snapshot diagnostics.

The current CPLEX callback path can expose native bound/node telemetry, but
not all best-bound-node relaxation variable values in every run.  This audit
therefore accepts explicitly labelled unavailable fields and rejects silent
zero-filled or certificate-bearing diagnostic snapshots.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, Iterable, List


MISSING_LABELS = {
    "",
    "not_exposed",
    "not_exposed_by_current_cplex_callback",
    "not_exposed_by_current_cplex_callback_api",
    "unavailable",
    "not_available",
}


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.is_dir():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def candidate_files(results: Path) -> Iterable[Path]:
    for name in (
        "plateau_snapshot_values.csv",
        "plateau_snapshot_summary.csv",
        "plain_vs_tailored_snapshot_comparison.csv",
    ):
        path = results / name
        if path.exists():
            yield path
    snap_dir = results / "lp_snapshots"
    if snap_dir.exists():
        yield from sorted(snap_dir.glob("*.csv"))
    plateau_dir = results / "plateau_snapshots"
    if plateau_dir.exists():
        yield from sorted(plateau_dir.glob("*.csv"))


def audit_file(path: Path, row: Dict[str, str]) -> Dict[str, Any]:
    failures: List[str] = []
    source = row.get("snapshot_source", row.get("snapshot_scope", ""))
    role = row.get("paper_certificate_role", row.get("row_class", "diagnostic_only"))
    if not source:
        failures.append("missing_snapshot_source")
    if "certificate" in str(role).lower() and "diagnostic" not in str(role).lower():
        failures.append("snapshot_marked_as_certificate_evidence")

    for key in ("S", "P", "H", "G", "G_variable", "W_SP", "S_times_P"):
        if key in row:
            value = str(row.get(key, "")).strip()
            if value == "0" and "not_exposed" in source.lower():
                failures.append(f"{key}_silently_zero_filled")
            if value and value.lower() not in MISSING_LABELS:
                try:
                    float(value)
                except ValueError:
                    failures.append(f"{key}_non_numeric_unlabelled:{value[:40]}")

    return {
        "file": str(path),
        "snapshot_source": source,
        "snapshot_scope": row.get("snapshot_scope", ""),
        "paper_certificate_role": role,
        "audit_passed": not failures,
        "failures": "|".join(failures),
    }


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
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    results = Path(args.results)
    rows: List[Dict[str, Any]] = []
    for path in candidate_files(results):
        records = read_csv(path)
        for record in records:
            rows.append(audit_file(path, record))
    if not rows:
        rows = [{"file": "", "audit_passed": False, "failures": "no_snapshot_csv"}]
    write_csv(Path(args.out), rows)
    failures = sum(1 for row in rows if not as_bool(row.get("audit_passed")))
    print(f"lp_snapshot_integrity_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
