#!/usr/bin/env python3
"""Run diagnostic BPC closure attempts on unresolved frontier leaves."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List


def as_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def read_targets(interval_csv: Path, max_leaves: int) -> List[Dict[str, str]]:
    with interval_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    targets: List[Dict[str, str]] = []
    for row in rows:
        status = (row.get("interval_status") or "").lower()
        if status not in {"unresolved", "unprocessed_relevant", "invalid"}:
            continue
        targets.append(row)
        if max_leaves > 0 and len(targets) >= max_leaves:
            break
    return targets


def load_result(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        return data["results"][0]
    if isinstance(data, dict):
        return data
    return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", default="build/ExactEBRP.exe")
    parser.add_argument("--instance", required=True)
    parser.add_argument("--interval-csv", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--lambda-value", default="0.15")
    parser.add_argument("--T", default="3600")
    parser.add_argument("--time-limit", default="120")
    parser.add_argument("--max-leaves", type=int, default=2)
    parser.add_argument("--max-nodes", default="63")
    args = parser.parse_args()

    exe = Path(args.exe)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = read_targets(Path(args.interval_csv), args.max_leaves)
    summary_path = out_dir / "bpc_leaf_validation_summary.csv"
    pricing_path = out_dir / "bpc_pricing_profile.csv"
    state_audit_path = out_dir / "pricing_state_audit.csv"
    depth_path = out_dir / "pricing_depth_profile.csv"
    op_path = out_dir / "operation_dp_profile.csv"

    summary_fields = [
        "interval_id", "gamma_L", "gamma_U", "return_code", "status",
        "lower_bound", "upper_bound", "gap", "nodes", "open_nodes",
        "pricing_calls", "pricing_time_seconds", "master_time_seconds",
        "columns", "cuts_added", "pricing_closure_status",
        "pricing_completed_exactly", "pricing_closure_certified_exact",
        "pricing_best_reduced_cost_any", "pricing_remaining_negative_rc",
        "exact_pricing_closed", "stop_reason", "result_file",
    ]
    pricing_fields = [
        "interval_id", "pricing_calls", "pricing_time_seconds",
        "pricing_engine", "final_pricing_engine", "labels_generated",
        "labels_kept", "labels_expanded", "labels_pruned_duration",
        "labels_pruned_load", "labels_pruned_station", "labels_pruned_support",
        "labels_pruned_reduced_cost", "dominance_prunes",
        "operation_dp_prunes", "negative_columns_found", "columns_inserted",
        "best_reduced_cost", "remaining_negative_rc", "closure_status",
    ]
    state_fields = [
        "interval_id", "call_index", "vehicle", "event", "pricing_engine_used",
        "time_seconds", "exact_completed", "early_negative_stop",
        "generated_columns", "returned_negative_columns", "route_states",
        "operation_states", "pricing_state_stop_reason",
        "pricing_label_dominance_mode", "pricing_label_dominance_exact_safe",
        "pricing_completion_bound_mode", "pricing_route_skeleton_mode",
        "pricing_operation_dp_dominance_enabled", "best_reduced_cost",
    ]
    depth_fields = [
        "interval_id", "call_index", "vehicle", "depth",
        "labels_generated", "labels_kept", "labels_expanded",
        "pruned_duration", "pruned_load", "pruned_station",
        "pruned_support", "pruned_reduced_cost", "pruned_dominance",
        "duplicate_states", "operation_states_generated",
        "operation_states_pruned", "columns_generated",
        "negative_columns_found", "best_reduced_cost",
    ]
    op_fields = [
        "interval_id", "call_index", "vehicle", "depth",
        "operation_states_generated", "operation_states_pruned",
    ]

    def load_trace_calls(result_file: Path) -> List[Dict[str, Any]]:
        trace_file = result_file.with_suffix(".trace.json")
        if not trace_file.exists():
            return []
        try:
            data = json.loads(trace_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        calls = data.get("pricing_calls", [])
        return calls if isinstance(calls, list) else []

    def aggregate_result_call(result: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not result or int(result.get("pricing_calls") or 0) <= 0:
            return []
        return [{
            "vehicle": "aggregate",
            "event": "aggregate_result_json",
            "pricing_engine_used": result.get("final_pricing_engine", ""),
            "time_seconds": result.get("pricing_time_seconds", ""),
            "exact_completed": result.get("pricing_completed_exactly", ""),
            "early_negative_stop": False,
            "generated_columns": result.get("pricing_negative_columns_found", ""),
            "returned_negative_columns": result.get("pricing_negative_columns_found", ""),
            "route_states": result.get("pricing_labels_expanded", result.get("labels_processed", "")),
            "operation_states": result.get("operation_dp_dominance_pruned_states", ""),
            "pricing_state_stop_reason": result.get("pricing_state_stop_reason", ""),
            "pricing_label_dominance_mode": result.get("pricing_label_dominance_mode", ""),
            "pricing_label_dominance_exact_safe": result.get("pricing_label_dominance_exact_safe", ""),
            "pricing_completion_bound_mode": result.get("pricing_completion_bound_mode", ""),
            "pricing_route_skeleton_mode": result.get("pricing_route_skeleton_mode", ""),
            "pricing_operation_dp_dominance_enabled": result.get("pricing_operation_dp_dominance_enabled", ""),
            "best_reduced_cost": result.get("pricing_best_reduced_cost_any", ""),
            "pricing_depth_profile": result.get("pricing_depth_profile", []),
            "operation_dp_profile": result.get("operation_dp_profile", []),
        }]

    with summary_path.open("w", newline="", encoding="utf-8") as s_handle, \
            pricing_path.open("w", newline="", encoding="utf-8") as p_handle, \
            state_audit_path.open("w", newline="", encoding="utf-8") as st_handle, \
            depth_path.open("w", newline="", encoding="utf-8") as d_handle, \
            op_path.open("w", newline="", encoding="utf-8") as o_handle:
        summary_writer = csv.DictWriter(s_handle, fieldnames=summary_fields)
        pricing_writer = csv.DictWriter(p_handle, fieldnames=pricing_fields)
        state_writer = csv.DictWriter(st_handle, fieldnames=state_fields)
        depth_writer = csv.DictWriter(d_handle, fieldnames=depth_fields)
        op_writer = csv.DictWriter(o_handle, fieldnames=op_fields)
        summary_writer.writeheader()
        pricing_writer.writeheader()
        state_writer.writeheader()
        depth_writer.writeheader()
        op_writer.writeheader()
        for pos, row in enumerate(targets):
            interval_id = row.get("interval_id") or str(pos)
            lo = row.get("gamma_L") or "0"
            hi = row.get("gamma_U") or "0"
            result_file = out_dir / f"leaf_{interval_id}.json"
            log_file = out_dir / f"leaf_{interval_id}.log"
            cmd = [
                str(exe),
                "--method", "gcap-tree",
                "--algorithm-preset", "paper-gf-bpc-core",
                "--paper-run-sealed", "true",
                "--input", args.instance,
                "--lambda", args.lambda_value,
                "--T", args.T,
                "--gini-floor", lo,
                "--gini-cap", hi,
                "--time-limit", args.time_limit,
                "--max-nodes", args.max_nodes,
                "--out", str(result_file),
                "--log", str(log_file),
            ]
            completed = subprocess.run(cmd, text=True, capture_output=True)
            if completed.stdout or completed.stderr:
                log_file.write_text(completed.stdout + completed.stderr, encoding="utf-8")
            result: Dict[str, Any] = {}
            if result_file.exists():
                result = load_result(result_file)
            trace_calls = load_trace_calls(result_file)
            if not trace_calls:
                trace_calls = aggregate_result_call(result)
            summary_writer.writerow({
                "interval_id": interval_id,
                "gamma_L": lo,
                "gamma_U": hi,
                "return_code": completed.returncode,
                "status": result.get("status", "no_json"),
                "lower_bound": result.get("lower_bound", ""),
                "upper_bound": result.get("upper_bound", ""),
                "gap": result.get("gap", ""),
                "nodes": result.get("nodes", ""),
                "open_nodes": result.get("open_nodes", ""),
                "pricing_calls": result.get("pricing_calls", ""),
                "pricing_time_seconds": result.get("pricing_time_seconds", ""),
                "master_time_seconds": result.get("master_time_seconds", ""),
                "columns": result.get("columns", ""),
                "cuts_added": result.get("cuts_added", ""),
                "pricing_closure_status": result.get("pricing_closure_status", ""),
                "pricing_completed_exactly": result.get("pricing_completed_exactly", ""),
                "pricing_closure_certified_exact": result.get("pricing_closure_certified_exact", ""),
                "pricing_best_reduced_cost_any": result.get("pricing_best_reduced_cost_any", ""),
                "pricing_remaining_negative_rc": result.get("pricing_remaining_negative_rc", ""),
                "exact_pricing_closed": result.get("pricing_closure_certified_exact", ""),
                "stop_reason": result.get("full_certificate_rejection_reason", ""),
                "result_file": str(result_file),
            })
            pricing_writer.writerow({
                "interval_id": interval_id,
                "pricing_calls": result.get("pricing_calls", ""),
                "pricing_time_seconds": result.get("pricing_time_seconds", ""),
                "pricing_engine": result.get("pricing_engine", ""),
                "final_pricing_engine": result.get("final_pricing_engine", ""),
                "labels_generated": result.get("pricing_labels_generated", result.get("pricing_columns_enumerated", "")),
                "labels_kept": result.get("pricing_labels_kept", ""),
                "labels_expanded": result.get("pricing_labels_expanded", ""),
                "labels_pruned_duration": result.get("pricing_labels_pruned_duration", ""),
                "labels_pruned_load": result.get("pricing_labels_pruned_load", ""),
                "labels_pruned_station": result.get("pricing_labels_pruned_station", ""),
                "labels_pruned_support": result.get("pricing_labels_pruned_support", ""),
                "labels_pruned_reduced_cost": result.get("pricing_labels_pruned_reduced_cost", ""),
                "dominance_prunes": result.get("pricing_labels_pruned_dominance", result.get("dominance_removed_columns", "")),
                "operation_dp_prunes": result.get("operation_dp_dominance_pruned_states", ""),
                "negative_columns_found": result.get("pricing_negative_columns_found", ""),
                "columns_inserted": result.get("pricing_negative_columns_inserted", ""),
                "best_reduced_cost": result.get("pricing_best_reduced_cost_any", ""),
                "remaining_negative_rc": result.get("pricing_remaining_negative_rc", ""),
                "closure_status": result.get("pricing_closure_status", ""),
            })
            for call_index, call in enumerate(trace_calls):
                state_writer.writerow({
                    "interval_id": interval_id,
                    "call_index": call_index,
                    "vehicle": call.get("vehicle", ""),
                    "event": call.get("event", ""),
                    "pricing_engine_used": call.get("pricing_engine_used", ""),
                    "time_seconds": call.get("time_seconds", ""),
                    "exact_completed": call.get("exact_completed", ""),
                    "early_negative_stop": call.get("early_negative_stop", ""),
                    "generated_columns": call.get("generated_columns", ""),
                    "returned_negative_columns": call.get("returned_negative_columns", ""),
                    "route_states": call.get("route_states", ""),
                    "operation_states": call.get("operation_states", ""),
                    "pricing_state_stop_reason": call.get("pricing_state_stop_reason", ""),
                    "pricing_label_dominance_mode": call.get("pricing_label_dominance_mode", ""),
                    "pricing_label_dominance_exact_safe": call.get("pricing_label_dominance_exact_safe", ""),
                    "pricing_completion_bound_mode": call.get("pricing_completion_bound_mode", ""),
                    "pricing_route_skeleton_mode": call.get("pricing_route_skeleton_mode", ""),
                    "pricing_operation_dp_dominance_enabled": call.get("pricing_operation_dp_dominance_enabled", ""),
                    "best_reduced_cost": call.get("best_reduced_cost", ""),
                })
                for depth in call.get("pricing_depth_profile", []) or []:
                    if not isinstance(depth, dict):
                        continue
                    row = {name: depth.get(name, "") for name in depth_fields}
                    row.update({
                        "interval_id": interval_id,
                        "call_index": call_index,
                        "vehicle": call.get("vehicle", ""),
                    })
                    depth_writer.writerow(row)
                for depth in call.get("operation_dp_profile", []) or []:
                    if not isinstance(depth, dict):
                        continue
                    op_writer.writerow({
                        "interval_id": interval_id,
                        "call_index": call_index,
                        "vehicle": call.get("vehicle", ""),
                        "depth": depth.get("depth", ""),
                        "operation_states_generated": depth.get("operation_states_generated", ""),
                        "operation_states_pruned": depth.get("operation_states_pruned", ""),
                    })
    print(
        "targets={targets} summary={summary} pricing={pricing} "
        "state={state} depth={depth} operation={operation}".format(
            targets=len(targets),
            summary=summary_path,
            pricing=pricing_path,
            state=state_audit_path,
            depth=depth_path,
            operation=op_path,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
