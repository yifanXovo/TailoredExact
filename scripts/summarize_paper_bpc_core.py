#!/usr/bin/env python3
"""Build paper-core BPC summary CSV files from raw JSON results.

The solver writes raw JSON plus optional interval ledgers. This script keeps the
paper-core summary reproducible and derives the controlling interval directly
from the active interval ledger instead of relying on hand-edited notes.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


SUMMARY_COLUMNS = [
    "instance",
    "method",
    "algorithm_preset",
    "status",
    "objective",
    "lower_bound",
    "upper_bound",
    "gap",
    "runtime_seconds",
    "wall_time_seconds",
    "verifier_passed",
    "certified_original_problem",
    "unresolved_intervals",
    "invalid_bound_intervals",
    "open_nodes",
    "pricing_calls",
    "pricing_closed_nodes",
    "columns_generated",
    "cuts_generated",
    "completion_lb_pruned_labels",
    "required_closure_pruned_labels",
    "label_dominance_comparisons",
    "label_dominance_pruned_labels",
    "label_dominance_cross_pickup_pruned_labels",
    "label_dominance_inactive_entries_skipped",
    "label_dominance_bucket_compactions",
    "label_dominance_compacted_entries",
    "operation_dp_dominance_pruned_states",
    "controlling_interval",
    "frontier_min_interval_lower_bound",
    "frontier_lower_bound_source",
    "node_trace_count",
    "pricing_trace_count",
    "bpc_trace_json",
    "bpc_interval_trace_csv",
    "result_file",
    "progress_log",
    "log_file",
    "plateau_reason",
]


ADAPTIVE_DEPTH_RUNS = {
    "v12_m1_average_core_1200s": "default",
    "v12_m1_average_core_1200s_depth5_default": "5",
    "v12_m1_average_core_1200s_depth6_default": "6",
    "v12_m1_average_core_300s_depth5_default": "5",
    "v12_m1_average_core_300s_depth6_default": "6",
    "v12_m1_average_core_300s_depth7_default": "7",
    "v12_m1_average_core_300s_depth8_default": "8",
    "v12_m1_average_core_300s_depth9": "9",
    "v12_m1_average_core_300s_label_dominance_trace": "default",
    "v12_m1_average_core_300s_split_before_tree": "3",
    "v12_m1_average_core_300s_split_completion_lb": "3",
    "v12_m1_average_core_300s_split_depth5": "5",
    "v12_m2_average_core_1200s": "default",
    "v12_m2_average_core_1200s_depth5_default": "5",
    "v12_m2_average_core_1200s_split_before_tree": "3",
    "v12_m2_average_core_300s_depth5_default": "5",
    "v12_m2_average_core_300s_depth6_default": "6",
    "v12_m2_average_core_300s_depth7_default": "7",
    "v12_m2_average_core_300s_depth8_default": "8",
    "v12_m2_average_core_300s_depth9": "9",
    "v12_m2_average_core_300s_split_before_tree": "3",
    "v12_m2_average_core_300s_split_completion_lb": "3",
    "v12_m2_average_core_300s_split_depth4": "4",
}

ADAPTIVE_COLUMNS = [
    "run",
    "instance",
    "requested_depth",
    "lower_bound",
    "upper_bound",
    "gap",
    "runtime_seconds",
    "unresolved_intervals",
    "open_nodes",
    "pricing_calls",
    "pricing_closed_nodes",
    "bound_time_seconds",
    "master_time_seconds",
    "pricing_time_seconds",
    "frontier_lower_bound_source",
    "controlling_interval",
    "result_file",
]


def scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if value is None:
        return ""
    return str(value)


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def result_paths(raw_dir: Path) -> Iterable[Path]:
    for path in sorted(raw_dir.glob("*.json")):
        if path.name.endswith(".trace.json"):
            continue
        yield path


def plateau_reason(result: Dict[str, Any]) -> str:
    if result.get("certified_original_problem"):
        return "certified"
    if int(result.get("invalid_bound_intervals") or 0) > 0:
        return "invalid_bound_intervals"
    if int(result.get("unresolved_intervals") or 0) > 0:
        return "unresolved_intervals"
    status = str(result.get("status", ""))
    if "diagnostic" in status:
        return "not_certified"
    if status and status != "optimal":
        return status
    return "not_certified"


def log_path_for(result_file: str, result: Dict[str, Any], logs_dir: Path) -> str:
    if result.get("log_file"):
        return str(result.get("log_file"))
    stem = Path(result_file).stem
    candidate = logs_dir / f"{stem}.log"
    return str(candidate) if candidate.exists() else ""


def parse_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def controlling_interval(interval_csv: str) -> str:
    if not interval_csv:
        return ""
    path = Path(interval_csv)
    if not path.exists():
        return ""
    candidates: List[Dict[str, str]] = []
    with path.open(newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("interval_status") != "unresolved":
                continue
            if row.get("interval_bound_valid", "").lower() == "false":
                continue
            lb = parse_float(row.get("interval_lower_bound"))
            if lb is None:
                continue
            candidates.append(row)
    if not candidates:
        return ""
    best = min(
        candidates,
        key=lambda r: (
            parse_float(r.get("interval_lower_bound")) or float("inf"),
            parse_float(r.get("gamma_L")) or 0.0,
        ),
    )
    return (
        f"{best.get('interval_id')}:[{best.get('gamma_L')},"
        f"{best.get('gamma_U')}]:lb={best.get('interval_lower_bound')}"
    )


def summary_row(path: Path, result: Dict[str, Any], logs_dir: Path) -> Dict[str, Any]:
    result_file = result.get("result_file") or str(path)
    interval_csv = result.get("bpc_interval_trace_csv", "")
    row: Dict[str, Any] = {
        "instance": result.get("instance_name") or Path(result.get("input_path", "")).name,
        "method": result.get("method", ""),
        "algorithm_preset": result.get("algorithm_preset", ""),
        "status": result.get("status", ""),
        "objective": result.get("objective", ""),
        "lower_bound": result.get("lower_bound", ""),
        "upper_bound": result.get("upper_bound", ""),
        "gap": result.get("gap", ""),
        "runtime_seconds": result.get("runtime_seconds", ""),
        "wall_time_seconds": result.get("wall_time_seconds", result.get("runtime_seconds", "")),
        "verifier_passed": result.get("verifier_passed", ""),
        "certified_original_problem": result.get("certified_original_problem", ""),
        "unresolved_intervals": result.get("unresolved_intervals", ""),
        "invalid_bound_intervals": result.get("invalid_bound_intervals", ""),
        "open_nodes": result.get("open_nodes", ""),
        "pricing_calls": result.get("pricing_calls", ""),
        "pricing_closed_nodes": result.get("pricing_closed_nodes", ""),
        "columns_generated": result.get("columns", ""),
        "cuts_generated": result.get("cuts_added", ""),
        "controlling_interval": controlling_interval(interval_csv),
        "frontier_min_interval_lower_bound": result.get("frontier_min_interval_lower_bound", ""),
        "frontier_lower_bound_source": result.get("frontier_lower_bound_source", ""),
        "node_trace_count": result.get("node_trace_count", ""),
        "pricing_trace_count": result.get("pricing_trace_count", ""),
        "bpc_trace_json": result.get("bpc_trace_json", ""),
        "bpc_interval_trace_csv": interval_csv,
        "result_file": result_file,
        "progress_log": result.get("progress_log", ""),
        "log_file": log_path_for(result_file, result, logs_dir),
        "plateau_reason": plateau_reason(result),
    }
    for column in SUMMARY_COLUMNS:
        row.setdefault(column, result.get(column, ""))
    return row


def write_csv(path: Path, columns: List[str], rows: Iterable[Dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=columns, quoting=csv.QUOTE_ALL, lineterminator="\n"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({column: scalar(row.get(column, "")) for column in columns})
            count += 1
    return count


def build_summary(raw_dir: Path, logs_dir: Path, output: Path) -> int:
    rows = []
    for path in result_paths(raw_dir):
        result = load_json(path)
        if result is not None:
            rows.append(summary_row(path, result, logs_dir))
    return write_csv(output, SUMMARY_COLUMNS, rows)


def build_adaptive(raw_dir: Path, output: Path) -> int:
    rows: List[Dict[str, Any]] = []
    for run, depth in ADAPTIVE_DEPTH_RUNS.items():
        path = raw_dir / f"{run}.json"
        result = load_json(path)
        if result is None:
            continue
        interval_csv = result.get("bpc_interval_trace_csv", "")
        rows.append(
            {
                "run": run,
                "instance": result.get("instance_name")
                or Path(result.get("input_path", "")).name,
                "requested_depth": depth,
                "lower_bound": result.get("lower_bound", ""),
                "upper_bound": result.get("upper_bound", ""),
                "gap": result.get("gap", ""),
                "runtime_seconds": result.get("runtime_seconds", ""),
                "unresolved_intervals": result.get("unresolved_intervals", ""),
                "open_nodes": result.get("open_nodes", ""),
                "pricing_calls": result.get("pricing_calls", ""),
                "pricing_closed_nodes": result.get("pricing_closed_nodes", ""),
                "bound_time_seconds": result.get("bound_time_seconds", ""),
                "master_time_seconds": result.get("master_time_seconds", ""),
                "pricing_time_seconds": result.get("pricing_time_seconds", ""),
                "frontier_lower_bound_source": result.get("frontier_lower_bound_source", ""),
                "controlling_interval": controlling_interval(interval_csv),
                "result_file": str(path),
            }
        )
    return write_csv(output, ADAPTIVE_COLUMNS, rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", default="results/paper_bpc_core/raw")
    parser.add_argument("--logs-dir", default="results/paper_bpc_core/logs")
    parser.add_argument("--summary-out", default="results/paper_bpc_core/summary.csv")
    parser.add_argument(
        "--adaptive-out", default="results/paper_bpc_core/adaptive_depth_diagnostic.csv"
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    logs_dir = Path(args.logs_dir)
    summary_count = build_summary(raw_dir, logs_dir, Path(args.summary_out))
    adaptive_count = build_adaptive(raw_dir, Path(args.adaptive_out))
    print(f"summary_rows={summary_count} adaptive_rows={adaptive_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
