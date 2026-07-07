#!/usr/bin/env python3
"""Audit bucket-local ratio domain cuts for Tailored-BC result packages."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 0) -> int:
    try:
        if value in ("", None):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def iter_json(results: Path) -> Iterable[Path]:
    raw = results / "raw"
    if raw.exists():
        yield from sorted(raw.glob("*.json"))


def audit_row(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive audit output
        return {
            "file": str(path),
            "audit_passed": False,
            "failures": f"json_read_error:{exc}",
        }

    ratio_rows = as_int(data.get("tailored_bc_bucket_ratio_domain_rows_added"))
    ratio_tightened = as_int(data.get("tailored_bc_bucket_ratio_domain_bounds_tightened"))
    subset_rows = as_int(data.get("tailored_bc_bucket_subset_ratio_domain_cuts_added"))
    h_cap_rows = as_int(data.get("tailored_bc_bucket_h_cap_rows_added"))
    active = ratio_rows > 0 or ratio_tightened > 0 or subset_rows > 0 or h_cap_rows > 0

    s_l = as_float(data.get("s_range_bucket_L"))
    s_u = as_float(data.get("s_range_bucket_U"))
    gamma_u = as_float(data.get("interval_exact_cutoff_gamma_U"), -1.0)
    failures: List[str] = []
    if active:
        if not as_bool(data.get("s_range_refinement_enabled")):
            failures.append("bucket_ratio_active_without_s_range")
        if str(data.get("compact_bc_s_range_refinement", "")).lower() != "paper-safe":
            failures.append("bucket_ratio_not_paper_safe_s_range")
        if not as_bool(data.get("s_range_certificate_valid")):
            failures.append("bucket_ratio_without_valid_bucket_certificate_scope")
        if as_int(data.get("compact_bc_s_range_rows_added")) < 2:
            failures.append("bucket_ratio_without_enforced_s_rows")
        if s_u < s_l - 1e-9:
            failures.append("reversed_s_bucket")
        if gamma_u < -1e-12:
            failures.append("missing_gamma_u")
        if as_int(data.get("tailored_bc_bucket_subset_ratio_domain_max_size")) > 4:
            failures.append("subset_ratio_max_size_exceeds_4")
        proof = str(data.get("tailored_bc_bucket_ratio_domain_proof_status", ""))
        if ratio_rows > 0 and "paper_safe" not in proof:
            failures.append("ratio_domain_proof_status_not_paper_safe")

    return {
        "file": str(path),
        "row_class": data.get("row_class", ""),
        "active": active,
        "gamma_U": gamma_u,
        "s_bucket_L": s_l,
        "s_bucket_U": s_u,
        "s_range_refinement_enabled": data.get("s_range_refinement_enabled", ""),
        "compact_bc_s_range_refinement": data.get("compact_bc_s_range_refinement", ""),
        "s_range_certificate_valid": data.get("s_range_certificate_valid", ""),
        "compact_bc_s_range_rows_added": data.get("compact_bc_s_range_rows_added", ""),
        "bucket_ratio_domain_rows_added": ratio_rows,
        "bucket_ratio_domain_bounds_tightened": ratio_tightened,
        "bucket_subset_ratio_domain_cuts_added": subset_rows,
        "bucket_subset_ratio_domain_max_size": data.get("tailored_bc_bucket_subset_ratio_domain_max_size", ""),
        "bucket_h_cap_rows_added": h_cap_rows,
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    results = Path(args.results)
    rows = [audit_row(path) for path in iter_json(results)]
    if not rows:
        rows = [{"file": "", "audit_passed": False, "failures": "no_raw_json"}]
    write_csv(Path(args.out), rows)
    failures = sum(1 for row in rows if not as_bool(row.get("audit_passed")))
    active = sum(1 for row in rows if as_bool(row.get("active")))
    print(f"bucket_ratio_domain_rows={len(rows)} active={active} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
