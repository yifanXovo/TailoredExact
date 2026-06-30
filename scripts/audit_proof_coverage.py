#!/usr/bin/env python3
"""Summarize lower-bound proof coverage for ExactEBRP result directories."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on"}
    return False


def as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def iter_json(path: Path) -> Iterable[Path]:
    if path.is_dir():
        yield from sorted(path.rglob("*.json"))
    elif path.exists():
        yield path


def iter_results(path: Path) -> Iterable[Dict[str, Any]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        for item in data["results"]:
            if isinstance(item, dict):
                yield item
    elif isinstance(data, dict) and "trace_schema" not in data:
        yield data


def classify(row: Dict[str, Any]) -> str:
    preset = str(row.get("algorithm_preset", "custom"))
    method = str(row.get("method", ""))
    if method == "cplex":
        return "CPLEX benchmark"
    if method == "interval-cutoff-oracle":
        return "interval-oracle diagnostic"
    if preset == "paper-gf-bpc-core":
        return "paper-gf-bpc-core"
    if preset in {"paper-exact-portfolio", "paper-exact-v20-certificate"}:
        return "paper-exact-portfolio"
    if "bpc" in preset or method in {"gcap-tree", "pricing", "gcap-frontier"}:
        return "BPC diagnostic"
    return "diagnostic"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(args.results)
    rows: List[Dict[str, Any]] = []
    for path in iter_json(root):
        for result in iter_results(path):
            rows.append({
                "source": str(path),
                "instance": result.get("instance_name", ""),
                "method": result.get("method", ""),
                "algorithm_preset": result.get("algorithm_preset", ""),
                "classification": classify(result),
                "status": result.get("status", ""),
                "certified_original_problem": as_bool(result.get("certified_original_problem", False)),
                "lower_bound": result.get("lower_bound", ""),
                "upper_bound": result.get("upper_bound", ""),
                "gap": result.get("gap", ""),
                "intervals_closed_by_relaxation_count": as_int(result.get("intervals_closed_by_relaxation_count", 0)),
                "intervals_closed_by_bpc_count": as_int(result.get("intervals_closed_by_bpc_count", 0)),
                "intervals_closed_by_oracle_count": as_int(result.get("intervals_closed_by_oracle_count", 0)),
                "intervals_unresolved_count": as_int(result.get("intervals_unresolved_count", result.get("unresolved_intervals", 0))),
                "certificate_uses_interval_oracle": as_bool(result.get("certificate_uses_interval_oracle", False)),
                "certificate_uses_bpc_tree": as_bool(result.get("certificate_uses_bpc_tree", False)),
                "certificate_uses_relaxation_only": as_bool(result.get("certificate_uses_relaxation_only", False)),
                "bpc_core_certificate_valid": as_bool(result.get("bpc_core_certificate_valid", False)),
                "exact_portfolio_certificate_valid": as_bool(result.get("exact_portfolio_certificate_valid", False)),
                "frontier_lower_bound_source": result.get("frontier_lower_bound_source", ""),
                "full_certificate_basis": result.get("full_certificate_basis", ""),
                "full_certificate_rejection_reason": result.get("full_certificate_rejection_reason", ""),
            })
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source", "instance", "method", "algorithm_preset", "classification",
        "status", "certified_original_problem", "lower_bound", "upper_bound",
        "gap", "intervals_closed_by_relaxation_count",
        "intervals_closed_by_bpc_count", "intervals_closed_by_oracle_count",
        "intervals_unresolved_count", "certificate_uses_interval_oracle",
        "certificate_uses_bpc_tree", "certificate_uses_relaxation_only",
        "bpc_core_certificate_valid", "exact_portfolio_certificate_valid",
        "frontier_lower_bound_source", "full_certificate_basis",
        "full_certificate_rejection_reason",
    ]
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
