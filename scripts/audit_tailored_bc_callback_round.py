#!/usr/bin/env python3
"""Audit the tailored-BC callback round output.

This audit is deliberately strict about callback attribution: static/root
separation fallback rows may be useful diagnostics, but they cannot be reported
as true CPLEX-managed tailored branch-and-cut callback evidence.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def iter_json(raw_dir: Path) -> Iterable[tuple[Path, Dict[str, Any]]]:
    for path in sorted(raw_dir.rglob("*.json")):
        if path.name.endswith(".trace.json"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and "trace_schema" not in data:
            yield path, data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/gf_tailored_bc_callback_round")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    root = Path(args.results)
    raw_dir = root / "raw"
    rows: List[Dict[str, Any]] = []
    failures = 0

    for path, data in iter_json(raw_dir):
        preset = str(data.get("algorithm_preset", ""))
        method = str(data.get("method", ""))
        status = str(data.get("status", ""))
        certified = as_bool(data.get("certified_original_problem"))
        tailored_enabled = as_bool(data.get("tailored_bc_enabled"))
        callback_available = as_bool(data.get("tailored_bc_callback_available"))
        callback_claim = (
            str(data.get("tailored_bc_mode", "")) == "callback" or
            as_bool(data.get("tailored_bc_user_cut_callback_enabled")) or
            as_bool(data.get("tailored_bc_lazy_callback_enabled")) or
            as_bool(data.get("tailored_bc_incumbent_callback_enabled")) or
            as_bool(data.get("tailored_bc_branch_callback_enabled")) or
            str(data.get("tailored_bc_source_class", "")) == "tailored_bc_certified"
        )
        reasons: List[str] = []

        if preset == "paper-gf-tailored-bc" and not tailored_enabled:
            reasons.append("paper_tailored_preset_without_tailored_fields")
        if callback_claim and not callback_available:
            reasons.append("callback_claim_without_callback_api")
        if certified and str(data.get("tailored_bc_source_class", "")) == "static_fallback":
            reasons.append("static_fallback_certified_as_tailored")
        if certified and as_bool(data.get("certificate_uses_bpc_tree")):
            reasons.append("bpc_contaminates_tailored_certificate")
        if certified and as_bool(data.get("route_mask_all_subset_enumeration_certifying")):
            reasons.append("route_mask_contaminates_tailored_certificate")
        if method == "tailored-bc-callback-smoke-test" and callback_available and status != "diagnostic_passed":
            reasons.append("callback_available_but_smoke_not_passed")

        if reasons:
            failures += 1
        rows.append({
            "file": str(path),
            "method": method,
            "algorithm_preset": preset,
            "status": status,
            "certified_original_problem": certified,
            "tailored_bc_enabled": tailored_enabled,
            "tailored_bc_mode": data.get("tailored_bc_mode", ""),
            "tailored_bc_callback_available": callback_available,
            "tailored_bc_source_class": data.get("tailored_bc_source_class", ""),
            "audit_passed": not reasons,
            "failures": "|".join(reasons),
        })

    if not rows:
        rows.append({
            "file": "",
            "method": "",
            "algorithm_preset": "",
            "status": "",
            "certified_original_problem": False,
            "tailored_bc_enabled": False,
            "tailored_bc_mode": "",
            "tailored_bc_callback_available": False,
            "tailored_bc_source_class": "",
            "audit_passed": False,
            "failures": "no_json_rows",
        })
        failures = 1

    out = Path(args.out) if args.out else root / "tailored_bc_callback_audit.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"audited_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
