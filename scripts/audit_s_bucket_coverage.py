#!/usr/bin/env python3
"""Audit S-domain bucket coverage rows for Tailored-BC rounds."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, List, Tuple


TOL = 1e-7


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


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


def group_key(row: Dict[str, str]) -> Tuple[str, str, str, str, str, str, str]:
    return (
        row.get("parent_leaf", row.get("leaf", "")),
        row.get("gamma_L", ""),
        row.get("gamma_U", ""),
        row.get("ledger_mode", row.get("tailored_bc_s_bucket_ledger", "")),
        row.get("bucket_count", row.get("s_range_bucket_count", "")),
        row.get("bucket_policy_effective", row.get("tailored_bc_s_bucket_policy", "")),
        row.get("budget_seconds", row.get("budget_seconds_per_bucket", "")),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/gf_tailored_bc_s_bucket_strengthening_round")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    root = Path(args.results)
    source = root / "s_bucket_bucket_status.csv"
    rows = read_csv(source)
    if not rows:
        source = root / "s_bucket_coverage_audit.csv"
        rows = read_csv(source)

    failures = 0
    audited: List[Dict[str, Any]] = []
    by_group: Dict[Tuple[str, str, str, str, str, str, str], List[Dict[str, str]]] = {}
    for row in rows:
        by_group.setdefault(group_key(row), []).append(row)

    for key, group in by_group.items():
        group = sorted(group, key=lambda r: (f(r.get("s_bucket_L", r.get("s_range_bucket_L"))), f(r.get("s_bucket_U", r.get("s_range_bucket_U")))))
        parent_L = min(f(r.get("parent_S_L", r.get("s_range_global_L"))) for r in group)
        parent_U = max(f(r.get("parent_S_U", r.get("s_range_global_U"))) for r in group)
        if parent_U < parent_L:
            parent_L, parent_U = parent_U, parent_L
        cursor = parent_L
        uncovered = 0.0
        outside = False
        overlap_bad = False
        for row in group:
            lo = f(row.get("s_bucket_L", row.get("s_range_bucket_L")))
            hi = f(row.get("s_bucket_U", row.get("s_range_bucket_U")))
            if lo < parent_L - TOL or hi > parent_U + TOL or hi < lo - TOL:
                outside = True
            if lo > cursor + TOL:
                uncovered += lo - cursor
            if lo < cursor - TOL:
                overlap_bad = True
            cursor = max(cursor, hi)
        if cursor < parent_U - TOL:
            uncovered += parent_U - cursor
        exact_cover = uncovered <= TOL and not outside and not overlap_bad

        for row in group:
            reasons: List[str] = []
            if f(row.get("parent_S_U", row.get("s_range_global_U"))) < f(row.get("parent_S_L", row.get("s_range_global_L"))) - TOL:
                reasons.append("invalid_parent_s_domain")
            if not exact_cover:
                reasons.append("bucket_union_not_exact_cover")
            if outside:
                reasons.append("bucket_outside_parent_domain")
            if overlap_bad:
                reasons.append("bucket_overlap_beyond_boundary")
            if b(row.get("coverage_used_for_paper_certificate")) and row.get("ledger_mode") != "paper-safe":
                reasons.append("diagnostic_bucket_used_for_certificate")
            if b(row.get("s_range_certificate_valid")) and row.get("ledger_mode") == "diagnostic":
                reasons.append("diagnostic_bucket_marked_certificate_valid")
            ok = not reasons
            failures += 0 if ok else 1
            audited.append({
                **row,
                "coverage_tolerance": TOL,
                "group_exact_cover": exact_cover,
                "uncovered_s_gap": uncovered,
                "bucket_outside_parent_domain": outside,
                "bucket_overlap_beyond_boundary": overlap_bad,
                "audit_passed": ok,
                "failures": "|".join(reasons),
            })

    out = Path(args.out) if args.out else root / "s_bucket_coverage_audit.csv"
    write_csv(out, audited)
    print(f"s_bucket_coverage_groups={len(by_group)} rows={len(audited)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
