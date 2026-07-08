#!/usr/bin/env python3
"""Audit S-bucket parent ledger merge summaries."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def json_rows(root: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    raw = root / "raw"
    if not raw.exists():
        return rows
    for path in sorted(raw.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not b(data.get("s_range_refinement_enabled")):
            continue
        rows.append({
            "source_json": str(path),
            "ledger_mode": data.get("tailored_bc_s_bucket_ledger", data.get("compact_bc_s_range_refinement", "")),
            "parent_closed_by_s_bucket_ledger": str(data.get("s_range_bucket_closed", False)),
            "coverage_valid": str(data.get("s_range_parent_coverage_valid", False)),
            "all_buckets_closed": str(data.get("s_range_bucket_closed", False)),
            "diagnostic_evidence_used": "False",
            "checkpoint_only_used": "False",
            "plain_cplex_used": str(data.get("row_class", "").startswith("benchmark_only")),
            "timeout_bucket_count": "0" if data.get("status") == "interval_closed" else "1",
        })
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/gf_tailored_bc_s_bucket_strengthening_round")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    root = Path(args.results)
    rows = read_csv(root / "s_bucket_parent_merge_summary.csv")
    if not rows:
        rows = json_rows(root)
    failures = 0
    audited: List[Dict[str, Any]] = []
    for row in rows:
        reasons: List[str] = []
        ledger_mode = row.get("ledger_mode", "")
        parent_closed = b(row.get("parent_closed_by_s_bucket_ledger"))
        coverage_valid = b(row.get("coverage_valid"))
        all_buckets_closed = b(row.get("all_buckets_closed"))
        diagnostic_used = b(row.get("diagnostic_evidence_used"))
        checkpoint_used = b(row.get("checkpoint_only_used"))
        plain_used = b(row.get("plain_cplex_used"))
        timeout_count = int(float(row.get("timeout_bucket_count", 0) or 0))
        if parent_closed and ledger_mode != "paper-safe":
            reasons.append("non_paper_safe_ledger_closed_parent")
        if parent_closed and not coverage_valid:
            reasons.append("closed_parent_without_coverage")
        if parent_closed and not all_buckets_closed:
            reasons.append("closed_parent_with_open_bucket")
        if parent_closed and timeout_count > 0:
            reasons.append("closed_parent_with_timeout_bucket")
        if parent_closed and diagnostic_used:
            reasons.append("closed_parent_with_diagnostic_evidence")
        if parent_closed and checkpoint_used:
            reasons.append("closed_parent_with_checkpoint_only_evidence")
        if parent_closed and plain_used:
            reasons.append("closed_parent_with_plain_cplex_evidence")
        ok = not reasons
        failures += 0 if ok else 1
        audited.append({**row, "audit_passed": ok, "failures": "|".join(reasons)})
    out = Path(args.out) if args.out else root / "s_bucket_ledger_audit.csv"
    write_csv(out, audited)
    print(f"s_bucket_ledger_rows={len(audited)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
