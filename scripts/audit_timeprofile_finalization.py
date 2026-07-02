#!/usr/bin/env python3
"""Audit repaired time-profile finalization."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if isinstance(data, dict) and isinstance(data.get("results"), list) and data["results"]:
        return data["results"][0] if isinstance(data["results"][0], dict) else {}
    return data if isinstance(data, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/gf_compact_bc_effectiveness_round")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    root = Path(args.results)
    rows = []
    failures = 0
    for path in sorted((root / "raw").rglob("*.json")):
        if path.name.endswith(".trace.json"):
            continue
        data = read_json(path)
        if not data or str(data.get("method", "")) not in {"gcap-frontier", "cplex"}:
            continue
        reasons = []
        lb = f(data.get("lower_bound"))
        best_lb = f(data.get("best_valid_lb_seen"), lb)
        gap = f(data.get("gap"))
        best_gap = f(data.get("best_valid_gap_seen"), gap)
        if lb + 1e-8 < best_lb:
            reasons.append("final_lb_worse_than_best_valid_lb_seen")
        if gap > best_gap + 1e-8:
            reasons.append("final_gap_worse_than_best_valid_gap_seen")
        if gap == 0.0 and not b(data.get("certified_original_problem")):
            reasons.append("zero_gap_without_certificate")
        if str(data.get("finalization_source", "")).startswith("wrapper") and not b(data.get("final_json_uses_best_checkpoint")):
            reasons.append("wrapper_not_using_best_checkpoint")
        failures += bool(reasons)
        rows.append({
            "file": str(path),
            "method": data.get("method", ""),
            "instance_name": data.get("instance_name", ""),
            "finalization_source": data.get("finalization_source", ""),
            "lower_bound": lb,
            "best_valid_lb_seen": best_lb,
            "gap": gap,
            "best_valid_gap_seen": best_gap,
            "audit_passed": not reasons,
            "failures": "|".join(reasons),
        })
    out = Path(args.out) if args.out else root / "timeprofile_finalization_audit.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    else:
        out.write_text("", encoding="utf-8")
    print(f"audited_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
