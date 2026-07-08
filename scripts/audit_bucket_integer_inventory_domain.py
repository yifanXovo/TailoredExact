#!/usr/bin/env python3
"""Audit paper-safe bucket-local integer inventory domain tightening."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def as_int(value: Any, default: int = 0) -> int:
    try:
        if value in ("", None):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def iter_json(results: Path) -> Iterable[Path]:
    raw = results / "raw"
    if raw.exists():
        yield from sorted(raw.glob("*.json"))


def audit(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"file": str(path), "audit_passed": False, "failures": f"json_error:{exc}"}

    tightened = as_int(data.get("bucket_integer_inventory_bounds_tightened"))
    rows_added = as_int(data.get("bucket_integer_inventory_rows_added"))
    active = tightened > 0 or rows_added > 0
    failures: List[str] = []
    if active:
        if not as_bool(data.get("s_range_refinement_enabled")):
            failures.append("active_without_s_range")
        if str(data.get("compact_bc_s_range_refinement", "")).lower() != "paper-safe":
            failures.append("active_without_paper_safe_s_range")
        if not as_bool(data.get("s_range_certificate_valid")):
            failures.append("active_without_valid_s_bucket_certificate_scope")
        if as_float(data.get("s_range_bucket_U")) < as_float(data.get("s_range_bucket_L")) - 1e-9:
            failures.append("reversed_s_bucket")
        mode = str(data.get("bucket_integer_inventory_domain_mode", "")).lower()
        if mode not in {"static", "both"}:
            failures.append(f"unexpected_mode:{mode}")
        proof = str(data.get("bucket_integer_inventory_domain_proof_status", ""))
        if "paper_safe" not in proof:
            failures.append("proof_status_not_paper_safe")
        if as_int(data.get("bucket_integer_inventory_lower_bounds_tightened")) < 0:
            failures.append("negative_lower_tighten_count")
        if as_int(data.get("bucket_integer_inventory_upper_bounds_tightened")) < 0:
            failures.append("negative_upper_tighten_count")

    return {
        "file": str(path),
        "active": active,
        "rows_added": rows_added,
        "bounds_tightened": tightened,
        "lower_bounds_tightened": data.get("bucket_integer_inventory_lower_bounds_tightened", ""),
        "upper_bounds_tightened": data.get("bucket_integer_inventory_upper_bounds_tightened", ""),
        "mode": data.get("bucket_integer_inventory_domain_mode", ""),
        "proof_status": data.get("bucket_integer_inventory_domain_proof_status", ""),
        "s_range_refinement_enabled": data.get("s_range_refinement_enabled", ""),
        "compact_bc_s_range_refinement": data.get("compact_bc_s_range_refinement", ""),
        "s_range_certificate_valid": data.get("s_range_certificate_valid", ""),
        "s_range_bucket_L": data.get("s_range_bucket_L", ""),
        "s_range_bucket_U": data.get("s_range_bucket_U", ""),
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
    rows = [audit(path) for path in iter_json(Path(args.results))]
    if not rows:
        rows = [{"file": "", "audit_passed": False, "failures": "no_raw_json"}]
    write_csv(Path(args.out), rows)
    failures = sum(1 for row in rows if not as_bool(row.get("audit_passed")))
    active = sum(1 for row in rows if as_bool(row.get("active")))
    print(f"bucket_integer_inventory_domain_rows={len(rows)} active={active} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
