#!/usr/bin/env python3
"""Audit serial, one-thread, package-local CPLEX comparison campaigns."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


def as_bool(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {
        "1", "true", "yes", "on"
    }


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def parse_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def write_csv(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    materialized = list(rows)
    fields: List[str] = []
    for row in materialized:
        for key in row:
            if key not in fields:
                fields.append(key)
    if not fields:
        fields = ["check", "passed", "reason"]
        materialized = [{"check": "no_checks", "passed": False,
                         "reason": "audit produced no checks"}]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(materialized)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True)
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    root = Path(args.results).resolve()
    out = Path(args.out) if args.out else root / "hardware_fairness_audit.csv"
    isolation = read_csv(root / "run_isolation_manifest.csv")
    order = read_csv(root / "run_order_manifest.csv")
    parameters = read_csv(root / "cplex_parameter_manifest.csv")
    hardware = read_csv(root / "hardware_solver_environment.csv")
    comparisons = read_csv(root / "plain_vs_tailored_matched_comparison.csv")
    incumbent = read_csv(root / "incumbent_source_audit.csv")

    rows: List[Dict[str, Any]] = []
    failures = 0

    def add(check: str, passed: bool, reason: str, run_id: str = "") -> None:
        nonlocal failures
        if not passed:
            failures += 1
        rows.append({"check": check, "run_id": run_id, "passed": passed,
                     "reason": reason})

    add("hardware_metadata_present", bool(hardware),
        f"rows={len(hardware)}")
    if hardware:
        required = {
            "hostname", "cpu_model", "physical_cores", "logical_cores",
            "ram_total_bytes", "os_version", "cplex_version",
            "build_sha256", "git_commit",
        }
        missing = sorted(key for key in required if not hardware[0].get(key))
        add("hardware_metadata_complete", not missing,
            "none" if not missing else "missing=" + ";".join(missing))

    add("parameter_manifest_present", bool(parameters),
        f"rows={len(parameters)}")
    parameter_roles = {row.get("solver_role", "") for row in parameters}
    add("plain_and_tailored_parameter_roles",
        {"plain_cplex", "tailored_compact_bc"}.issubset(parameter_roles),
        "roles=" + ";".join(sorted(parameter_roles)))
    for name in ("cplex_params_plain.json", "cplex_params_tailored.json"):
        path = root / name
        valid = False
        reason = "missing"
        if path.exists():
            try:
                valid = isinstance(json.loads(path.read_text(encoding="utf-8")), dict)
                reason = "valid_json" if valid else "not_object"
            except Exception as exc:  # noqa: BLE001 - report malformed artifact
                reason = f"json_error:{exc}"
        add(f"parameter_snapshot:{name}", valid, reason)

    add("run_isolation_manifest_present", bool(isolation),
        f"rows={len(isolation)}")
    ids = set()
    intervals = []
    for row in isolation:
        run_id = row.get("run_id", "")
        add("unique_run_id", bool(run_id) and run_id not in ids,
            "unique" if run_id and run_id not in ids else "missing_or_duplicate",
            run_id)
        ids.add(run_id)
        threads = int(as_float(row.get("cplex_threads"), 0))
        add("one_thread_cplex", threads == 1,
            f"cplex_threads={threads}", run_id)
        concurrent = int(as_float(row.get("concurrent_solver_processes"), 0))
        background = as_bool(row.get("background_solver_detected"))
        add("single_solver_process", concurrent <= 1 and not background,
            f"max_concurrent={concurrent};background={background}", run_id)
        add("incumbent_source_policy_present",
            bool(row.get("incumbent_source_policy")),
            row.get("incumbent_source_policy", "missing"), run_id)
        start = parse_time(row.get("process_start_time", ""))
        end = parse_time(row.get("process_end_time", ""))
        add("run_timestamps_valid", bool(start and end and end >= start),
            f"start={row.get('process_start_time')};end={row.get('process_end_time')}",
            run_id)
        if start and end:
            intervals.append((start, end, run_id))
        resource_stop = as_bool(row.get("resource_stopped"))
        used_bound = as_bool(row.get("bound_used_in_comparison"))
        certified = as_bool(row.get("certified_original_problem"))
        add("resource_stop_not_used",
            not resource_stop or (not used_bound and not certified),
            f"resource_stopped={resource_stop};bound_used={used_bound};certified={certified}",
            run_id)

    intervals.sort()
    for index, (start, end, run_id) in enumerate(intervals):
        if index == 0:
            continue
        previous_start, previous_end, previous_id = intervals[index - 1]
        del previous_start
        add("no_run_overlap", start >= previous_end,
            f"previous={previous_id};previous_end={previous_end.isoformat()};start={start.isoformat()}",
            run_id)

    add("run_order_manifest_present", bool(order), f"rows={len(order)}")
    sequence = [int(as_float(row.get("run_order"), 0)) for row in order]
    add("run_order_strictly_increasing",
        sequence == sorted(set(sequence)) and all(value > 0 for value in sequence),
        "sequence=" + ";".join(map(str, sequence[:30])))

    for row in comparisons:
        comparison_id = row.get("comparison_id", "")
        plain_budget = as_float(row.get("plain_budget_seconds"), -1.0)
        tailored_budget = as_float(row.get("tailored_budget_seconds"), -2.0)
        add("matched_budget", abs(plain_budget - tailored_budget) <= 1e-9,
            f"plain={plain_budget};tailored={tailored_budget}", comparison_id)
        plain_threads = int(as_float(row.get("plain_cplex_threads"), 0))
        tailored_threads = int(as_float(row.get("tailored_cplex_threads"), 0))
        add("matched_threads", plain_threads == tailored_threads == 1,
            f"plain={plain_threads};tailored={tailored_threads}", comparison_id)
        add("matched_hardware",
            bool(row.get("same_hardware")) and as_bool(row.get("same_hardware")),
            f"same_hardware={row.get('same_hardware')}", comparison_id)

    add("incumbent_source_audit_present", bool(incumbent),
        f"rows={len(incumbent)}")
    for row in incumbent:
        add("incumbent_source_safe",
            as_bool(row.get("passed", row.get("paper_core_safe", False))),
            row.get("reason", row.get("source_type", "")),
            row.get("run_id", ""))

    write_csv(out, rows)
    print(f"hardware fairness checks={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
