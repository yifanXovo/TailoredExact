#!/usr/bin/env python3
"""Audit vector-selected route support and cutset rows."""

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
        support_enabled = as_bool(data.get("tailored_bc_vector_support_cover_enabled"))
        cutset_enabled = as_bool(data.get("tailored_bc_vector_route_cutset_enabled"))
        if support_enabled or cutset_enabled:
            enabled_count += 1
        support_candidates = (int(float(data.get("vector_support_cover_candidates", 0) or 0)) +
                              int(float(data.get("vector_callback_support_cover_candidates", 0) or 0)))
        support_cuts = (int(float(data.get("vector_support_cover_cuts_added", 0) or 0)) +
                        int(float(data.get("vector_callback_support_cover_cuts_added", 0) or 0)))
        cutset_candidates = (int(float(data.get("vector_route_cutset_candidates", 0) or 0)) +
                             int(float(data.get("vector_callback_route_cutset_candidates", 0) or 0)))
        cutset_cuts = (int(float(data.get("vector_route_cutset_cuts_added", 0) or 0)) +
                       int(float(data.get("vector_callback_route_cutset_cuts_added", 0) or 0)))
        reasons: List[str] = []
        source = str(data.get("tailored_bc_vector_cut_candidate_source", ""))
        dynamic_summary = str(data.get("compact_bc_dynamic_cuts_added_by_family", ""))
        if support_enabled and support_candidates <= 0 and "support_duration=" not in dynamic_summary:
            reasons.append("support_cover_enabled_without_candidates")
        if cutset_enabled and cutset_candidates <= 0 and "route_cutset=" not in dynamic_summary:
            reasons.append("route_cutset_enabled_without_candidates")
        if (support_cuts > 0 or cutset_cuts > 0) and "paper_safe" not in str(data.get("vector_route_cuts_proof_status", "")):
            reasons.append("route_rows_without_paper_safe_status")
        if reasons:
            failures += 1
        rows.append({
            "file": str(path),
            "support_enabled": support_enabled,
            "cutset_enabled": cutset_enabled,
            "candidate_source": data.get("tailored_bc_vector_cut_candidate_source", ""),
            "support_candidates": support_candidates,
            "support_cuts": support_cuts,
            "cutset_candidates": cutset_candidates,
            "cutset_cuts": cutset_cuts,
            "proof_status": data.get("vector_route_cuts_proof_status", ""),
            "audit_passed": not reasons,
            "failures": "|".join(reasons),
        })
    if enabled_count == 0:
        failures += 1
        rows.append({"file": "", "support_enabled": False, "cutset_enabled": False,
                     "candidate_source": "", "support_candidates": 0,
                     "support_cuts": 0, "cutset_candidates": 0,
                     "cutset_cuts": 0, "proof_status": "",
                     "audit_passed": False, "failures": "no_vector_route_rows_exercised"})
    out = Path(args.out) if args.out else root / "vector_route_cuts_audit.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"audited_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
