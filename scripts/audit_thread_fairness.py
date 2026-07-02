#!/usr/bin/env python3
"""Audit controlled one-thread fairness for compact-BC and CPLEX rows."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


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


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def as_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/gf_compact_bc_strengthening_round2")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    results = Path(args.results)
    raw_dir = results / "raw"
    rows: List[Dict[str, Any]] = []
    failures = 0

    for path, data in iter_json(raw_dir):
        method = str(data.get("method", ""))
        preset = str(data.get("algorithm_preset", ""))
        fairness = str(data.get("thread_fairness_class", ""))
        policy = str(data.get("solver_thread_policy", ""))
        cplex_threads = as_int(data.get("cplex_threads"))
        compact_threads = as_int(data.get("compact_bc_solver_threads"))
        paper_compact = preset == "paper-gf-compact-bc" and method == "gcap-frontier"
        cplex_benchmark = method == "cplex"
        diagnostic = fairness == "multithread_diagnostic" or "diagnostic" in str(data.get("classification", "")).lower()
        failure_reasons: List[str] = []

        if cplex_benchmark and not diagnostic and cplex_threads != 1:
            failure_reasons.append("controlled_cplex_not_one_thread")
        if paper_compact and not diagnostic and compact_threads != 1:
            failure_reasons.append("controlled_compact_bc_not_one_thread")
        if (paper_compact or cplex_benchmark) and not diagnostic:
            if fairness != "one_thread_fair":
                failure_reasons.append("missing_one_thread_fair_class")
            if not policy or policy == "unknown":
                failure_reasons.append("missing_solver_thread_policy")
        if as_bool(data.get("certified_original_problem")) and fairness == "unknown_not_paper":
            failure_reasons.append("certified_row_unknown_thread_policy")

        if failure_reasons:
            failures += 1
        rows.append(
            {
                "file": str(path),
                "method": method,
                "algorithm_preset": preset,
                "status": data.get("status", ""),
                "cplex_threads": cplex_threads,
                "mip_threads": as_int(data.get("mip_threads")),
                "compact_bc_solver_threads": compact_threads,
                "solver_thread_policy": policy,
                "thread_fairness_class": fairness,
                "audit_passed": not failure_reasons,
                "failures": "|".join(failure_reasons),
            }
        )

    out = Path(args.out) if args.out else results / "thread_fairness_audit.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "file",
            "method",
            "algorithm_preset",
            "status",
            "cplex_threads",
            "mip_threads",
            "compact_bc_solver_threads",
            "solver_thread_policy",
            "thread_fairness_class",
            "audit_passed",
            "failures",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"audited_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
