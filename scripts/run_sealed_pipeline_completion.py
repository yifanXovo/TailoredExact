#!/usr/bin/env python3
"""Run and finalize sealed paper-pipeline rows.

The C++ solver writes authoritative JSON when it returns normally.  This
wrapper only fills the gap when a sealed subprocess is interrupted, crashes, or
exits without JSON after writing progress.  Synthetic artifacts are always
noncertified and carry `finalization_source=interrupted_checkpoint` or
`wrapper_checkpoint`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]


DEFAULT_ROWS = [
    ("v4_smoke", "testdata/examples/gcap_smoke_V4_M1.txt", "smoke", 4, 1, 30, 90),
    (
        "v12_m2_300s",
        "reference/regen_candidate_V12_M2_average.txt",
        "regenerated_engineering",
        12,
        2,
        300,
        420,
    ),
    (
        "v12_m1_600s",
        "reference/regen_candidate_V12_M1_average.txt",
        "regenerated_engineering",
        12,
        1,
        600,
        780,
    ),
    (
        "high_imbalance_seed3201",
        "reference/hard_stress/V20_M3/high_imbalance_seed3201.txt",
        "hard_generated_v20_m3",
        20,
        3,
        1200,
        1500,
    ),
    (
        "high_imbalance_seed3202",
        "reference/hard_stress/V20_M3/high_imbalance_seed3202.txt",
        "hard_generated_v20_m3",
        20,
        3,
        1200,
        1500,
    ),
    (
        "tight_T_seed3101",
        "reference/hard_stress/V20_M3/tight_T_seed3101.txt",
        "hard_generated_v20_m3",
        20,
        3,
        1200,
        1500,
    ),
    (
        "tight_T_seed3102",
        "reference/hard_stress/V20_M3/tight_T_seed3102.txt",
        "hard_generated_v20_m3",
        20,
        3,
        1200,
        1500,
    ),
    (
        "moderate_seed3301",
        "reference/hard_stress/V20_M3/moderate_seed3301.txt",
        "hard_generated_v20_m3",
        20,
        3,
        1800,
        2100,
    ),
    (
        "moderate_seed3302",
        "reference/hard_stress/V20_M3/moderate_seed3302.txt",
        "hard_generated_v20_m3",
        20,
        3,
        1200,
        1500,
    ),
]


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: List[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    if not fields:
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def parse_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value: Any, default: int = 0) -> int:
    try:
        if value in ("", None):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def latest_progress(progress_path: Path) -> Dict[str, str]:
    rows = read_csv_rows(progress_path)
    return rows[-1] if rows else {}


def latest_verified_incumbent(ub_path: Path) -> Dict[str, str]:
    rows = read_csv_rows(ub_path)
    accepted = [r for r in rows if str(r.get("accepted", "")).lower() == "true"]
    return accepted[-1] if accepted else (rows[-1] if rows else {})


def sha256(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def synthesize_interval_ledger(
    out_path: Path,
    row_name: str,
    last: Dict[str, str],
) -> Path:
    ledger = out_path.with_suffix(".intervals.csv")
    interval_id = last.get("global_min_lb_interval_id", "0") or "0"
    interval_range = last.get("global_min_lb_interval_range", "")
    lo = ""
    hi = ""
    if interval_range.startswith("[") and interval_range.endswith("]"):
        parts = interval_range.strip("[]").split(",")
        if len(parts) == 2:
            lo, hi = parts[0], parts[1]
    rows = [{
        "interval_id": interval_id,
        "gamma_L": lo,
        "gamma_U": hi,
        "interval_status": "unresolved",
        "interval_lower_bound": last.get("global_LB", "0"),
        "lower_bound_source": last.get("global_min_lb_source", "checkpoint"),
        "open_nodes": last.get("open_nodes", "0"),
        "certificate_basis": "none",
        "reason": "wrapper synthesized unresolved controlling interval from latest progress checkpoint",
        "row": row_name,
    }]
    write_csv(ledger, rows)
    return ledger


def synthesize_json(
    *,
    row_name: str,
    input_path: Path,
    out_path: Path,
    progress_path: Path,
    ub_path: Path,
    stdout_path: Path,
    stderr_path: Path,
    scope: str,
    v: int,
    m: int,
    command: List[str],
    finalization_source: str,
    stop_reason: str,
    process_returncode: Optional[int],
) -> Dict[str, Any]:
    last = latest_progress(progress_path)
    incumbent = latest_verified_incumbent(ub_path)
    upper = parse_float(last.get("incumbent_UB"), parse_float(incumbent.get("objective"), 0.0))
    lower = parse_float(last.get("global_LB"), 0.0)
    gap = parse_float(last.get("gap"), 1.0 if upper > 0.0 else 0.0)
    ledger = synthesize_interval_ledger(out_path, row_name, last)
    verifier = str(incumbent.get("verifier_passed", "")).lower() == "true"
    progress_event = last.get("event", "")
    unresolved = parse_int(last.get("unresolved_intervals"), 1 if gap > 1e-9 else 0)
    open_nodes = parse_int(last.get("open_nodes"), unresolved)
    payload: Dict[str, Any] = {
        "instance_name": input_path.name,
        "instance_scope": scope,
        "instance_path": str(input_path),
        "instance_sha256": sha256(input_path),
        "V": v,
        "M": m,
        "method": "gcap-frontier",
        "algorithm_preset": "paper-exact-v20-certificate",
        "method_scope": "original_bpc",
        "solves_original_objective": True,
        "is_bpc": True,
        "status": "interrupted_noncertified",
        "certificate": "none",
        "objective": upper,
        "G": parse_float(incumbent.get("G"), 0.0),
        "P": parse_float(incumbent.get("P"), 0.0),
        "lower_bound": lower,
        "upper_bound": upper,
        "gap": gap,
        "runtime_seconds": parse_float(last.get("elapsed_seconds"), 0.0),
        "wall_time_seconds": parse_float(last.get("elapsed_seconds"), 0.0),
        "stop_reason": stop_reason,
        "finalization_source": finalization_source,
        "solver_finalization_reached": False,
        "wrapper_synthesized_final_json": True,
        "process_return_code": process_returncode if process_returncode is not None else 0,
        "abnormal_exit_detected": process_returncode not in (None, 0),
        "abnormal_exit_reason": (
            "none" if process_returncode in (None, 0)
            else f"process_return_code_{process_returncode}"
        ),
        "last_progress_event": progress_event,
        "plateau_reason": "interrupted_before_solver_final_json",
        "verifier_passed": verifier,
        "unresolved_intervals": unresolved,
        "invalid_bound_intervals": 0,
        "pricing_closed_nodes": 0,
        "open_nodes": open_nodes,
        "certified_original_problem": False,
        "nodes": 0,
        "columns": 0,
        "pricing_calls": 0,
        "pricing_time_seconds": parse_float(last.get("pricing_time_seconds"), 0.0),
        "master_time_seconds": parse_float(last.get("master_time_seconds"), 0.0),
        "bound_time_seconds": parse_float(last.get("bound_time_seconds"), 0.0),
        "frontier_covers_all_improving_gini_values": False,
        "frontier_range_certificate_scope": "original_full_improving_range",
        "full_certificate_all_intervals_accounted": False,
        "full_certificate_rejection_reason": "interrupted_checkpoint",
        "full_certificate_basis": "none",
        "full_certificate_requires_pricing_closure": False,
        "full_certificate_pricing_closure_satisfied": False,
        "pricing_completed_exactly": False,
        "pricing_closure_certified_exact": False,
        "pricing_closure_status": "not_used",
        "option_audit_consistent": True,
        "incumbent_source_category": "primal_heuristic" if incumbent else "empty",
        "incumbent_source_is_paper_reproducible": True,
        "incumbent_source_contributes_lower_bound": False,
        "incumbent_source_detail": "same-run native HGA-TGBC UB from UB event log"
        if incumbent else "no accepted incumbent event available",
        "sealed_run": True,
        "sealed_run_id": f"sealed_wrapper_{row_name}",
        "sealed_run_start_time": "",
        "incumbent_provenance": "same-run native HGA-TGBC UB, verifier-gated where available",
        "same_run_generated_incumbent": bool(incumbent),
        "no_archive_scanning": True,
        "no_external_known_ub": True,
        "no_focus_only_certificate": True,
        "sealed_run_forbidden_source_used": False,
        "sealed_run_rejection_reason": "none",
        "auto_interval_oracle_called": False,
        "auto_interval_oracle_total_final_leaves": unresolved,
        "auto_interval_oracle_leaves_attempted": 0,
        "auto_interval_oracle_leaves_closed": 0,
        "auto_interval_oracle_leaves_timed_out": 0,
        "auto_interval_oracle_leaves_split": 0,
        "auto_interval_oracle_time_seconds": 0.0,
        "auto_interval_oracle_remaining_open_leaves": unresolved,
        "auto_interval_oracle_status_by_leaf": "",
        "auto_interval_oracle_coverage_complete": False,
        "full_ledger_merge_status": "not_reached_before_interruption",
        "full_ledger_merge_audit_passed": False,
        "bpc_fallback_auto_called": False,
        "bpc_fallback_leaves_attempted": 0,
        "exact_pricing_closed_leaves": 0,
        "bpc_fallback_pricing_time": 0.0,
        "bpc_fallback_nodes": 0,
        "bpc_fallback_best_reduced_cost": 0.0,
        "bpc_interval_certificate_basis": "none",
        "progress_log": str(progress_path),
        "ub_event_log": str(ub_path),
        "bpc_interval_trace_csv": str(ledger),
        "result_file": str(out_path),
        "log_file": str(stdout_path),
        "command_line": " ".join(command),
        "wrapper_process_returncode": process_returncode,
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "notes": [
            "Wrapper synthesized a noncertified final artifact from latest progress checkpoint.",
            "This row is not a certificate and is included so audits cover the failed sealed run.",
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def run_checkpoint_oracle_for_payload(
    *,
    payload: Dict[str, Any],
    row_name: str,
    result_dir: Path,
    exe: Path,
    oracle_time_limit: int,
) -> Dict[str, Any]:
    """Run a diagnostic oracle on the synthesized controlling interval.

    This is not a full-ledger merge.  It records whether the latest checkpoint's
    controlling interval can be closed, but interrupted rows remain
    noncertified because the full final ledger is incomplete.
    """
    raw = result_dir / "raw"
    ledger = Path(str(payload.get("bpc_interval_trace_csv", "")))
    if not ledger.is_absolute():
        ledger = ROOT / ledger
    rows = read_csv_rows(ledger)
    if not rows:
        return payload
    leaf = rows[0]
    lo = leaf.get("gamma_L", "")
    hi = leaf.get("gamma_U", "")
    if not lo or not hi:
        return payload
    oracle_dir = raw / f"{row_name}_checkpoint_oracle"
    oracle_dir.mkdir(parents=True, exist_ok=True)
    oracle_json = oracle_dir / f"interval_{leaf.get('interval_id', '0')}.json"
    oracle_lp = oracle_dir / f"interval_{leaf.get('interval_id', '0')}.lp"
    oracle_sol = oracle_dir / f"interval_{leaf.get('interval_id', '0')}.sol"
    command = [
        str(exe),
        "--method", "interval-cutoff-oracle",
        "--input", str(payload.get("instance_path", "")),
        "--lambda", "0.15",
        "--T", "3600",
        "--interval-exact-cutoff-oracle", "compact-mip",
        "--interval-exact-cutoff-gamma-L", str(lo),
        "--interval-exact-cutoff-gamma-U", str(hi),
        "--interval-exact-cutoff-UB", str(payload.get("upper_bound", 0.0)),
        "--interval-exact-cutoff-time-limit", str(oracle_time_limit),
        "--interval-exact-cutoff-export-lp", str(oracle_lp),
        "--interval-exact-cutoff-result", str(oracle_sol),
        "--out", str(oracle_json),
    ]
    stdout_path = result_dir / "logs" / f"{row_name}.checkpoint_oracle.stdout.log"
    stderr_path = result_dir / "logs" / f"{row_name}.checkpoint_oracle.stderr.log"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            proc = subprocess.run(
                command,
                cwd=ROOT,
                stdout=stdout,
                stderr=stderr,
                timeout=max(oracle_time_limit + 60, 90),
                check=False,
            )
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            returncode = -999
    oracle_payload: Dict[str, Any] = {}
    if oracle_json.exists():
        try:
            oracle_payload = json.loads(oracle_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            oracle_payload = {}
    status = str(oracle_payload.get("status", "oracle_missing_output"))
    basis = str(oracle_payload.get("interval_exact_cutoff_certificate_basis", ""))
    solver_status = str(oracle_payload.get("interval_exact_cutoff_solver_status", ""))
    proven_infeasible = bool(oracle_payload.get("interval_exact_cutoff_proven_infeasible", False))
    timeout = bool(oracle_payload.get("interval_exact_cutoff_timeout", False)) or returncode == -999
    oracle_csv = raw / f"{row_name}.auto_oracle.csv"
    write_csv(oracle_csv, [{
        "interval_id": leaf.get("interval_id", "0"),
        "gamma_L": lo,
        "gamma_U": hi,
        "status": status,
        "certificate_basis": basis,
        "solver_status": solver_status,
        "proven_infeasible": proven_infeasible,
        "feasible_improving": bool(oracle_payload.get("interval_exact_cutoff_feasible_improving", False)),
        "timeout": timeout,
        "best_bound": oracle_payload.get("interval_exact_cutoff_best_bound", ""),
        "objective": oracle_payload.get("interval_exact_cutoff_objective", ""),
        "runtime_seconds": oracle_payload.get("interval_exact_cutoff_runtime_seconds", ""),
        "json_path": str(oracle_json),
        "lp_path": str(oracle_lp),
        "log_path": oracle_payload.get("interval_exact_cutoff_log_path", ""),
    }])
    payload["auto_interval_oracle_called"] = True
    payload["auto_interval_oracle_total_final_leaves"] = max(
        parse_int(payload.get("auto_interval_oracle_total_final_leaves"), 0), 1
    )
    payload["auto_interval_oracle_leaves_attempted"] = 1
    payload["auto_interval_oracle_leaves_closed"] = 1 if proven_infeasible else 0
    payload["auto_interval_oracle_leaves_timed_out"] = 1 if timeout else 0
    payload["auto_interval_oracle_leaves_split"] = 0
    payload["auto_interval_oracle_time_seconds"] = parse_float(
        oracle_payload.get("interval_exact_cutoff_runtime_seconds"), 0.0
    )
    payload["auto_interval_oracle_remaining_open_leaves"] = max(
        0,
        parse_int(payload.get("unresolved_intervals"), 0) - (1 if proven_infeasible else 0),
    )
    payload["auto_interval_oracle_status_by_leaf"] = (
        f"{leaf.get('interval_id', '0')}:{status}:{basis}:{solver_status}"
    )
    payload["auto_interval_oracle_coverage_complete"] = (
        payload["auto_interval_oracle_remaining_open_leaves"] == 0
    )
    payload["full_ledger_merge_status"] = (
        "checkpoint_oracle_closed_controlling_leaf_but_full_ledger_incomplete"
        if proven_infeasible else "checkpoint_oracle_diagnostic_unresolved"
    )
    payload["full_ledger_merge_audit_passed"] = False
    payload["plateau_reason"] = (
        "checkpoint_oracle_timeout" if timeout else "checkpoint_oracle_diagnostic_unresolved"
    )
    payload.setdefault("notes", [])
    payload["notes"].append(
        "Wrapper ran diagnostic interval oracle on checkpoint controlling leaf; "
        "interrupted row remains noncertified because full final ledger is incomplete."
    )
    Path(str(payload["result_file"])).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_command(
    exe: Path,
    row_name: str,
    input_path: Path,
    out_path: Path,
    progress_path: Path,
    ub_path: Path,
    time_limit: int,
    oracle_time: int,
    oracle_max_leaves: str,
    oracle_order: str,
    oracle_continue_after_timeout: bool,
    oracle_split_on_timeout: bool,
    oracle_child_split_count: int,
    oracle_max_depth: int,
    auto_bpc: bool,
    bpc_time: int,
    bpc_max_leaves: int,
) -> List[str]:
    return [
        str(exe),
        "--method", "gcap-frontier",
        "--algorithm-preset", "paper-exact-v20-certificate",
        "--paper-run-sealed", "true",
        "--auto-interval-oracle", "true",
        "--auto-interval-oracle-time-limit", str(oracle_time),
        "--auto-interval-oracle-max-leaves", str(oracle_max_leaves),
        "--auto-interval-oracle-order", str(oracle_order),
        "--auto-interval-oracle-continue-after-timeout",
        "true" if oracle_continue_after_timeout else "false",
        "--auto-interval-oracle-split-on-timeout",
        "true" if oracle_split_on_timeout else "false",
        "--auto-interval-oracle-child-split-count", str(oracle_child_split_count),
        "--auto-interval-oracle-max-depth", str(oracle_max_depth),
        "--auto-interval-oracle-restart-on-improved-ub", "true",
        "--auto-interval-bpc-fallback", "true" if auto_bpc else "false",
        "--auto-interval-bpc-time-limit", str(bpc_time),
        "--auto-interval-bpc-max-leaves", str(bpc_max_leaves),
        "--input", str(input_path),
        "--lambda", "0.15",
        "--T", "3600",
        "--time-limit", str(time_limit),
        "--progress-log", str(progress_path),
        "--ub-event-log", str(ub_path),
        "--out", str(out_path),
    ]


def run_row(args: argparse.Namespace) -> Dict[str, Any]:
    row_name = args.row_name
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    result_dir = Path(args.result_dir)
    raw_dir = result_dir / "raw"
    log_dir = result_dir / "logs"
    raw_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / f"{row_name}.json"
    progress_path = raw_dir / f"{row_name}.progress.csv"
    ub_path = raw_dir / f"{row_name}.ub_events.csv"
    stdout_path = log_dir / f"{row_name}.stdout.log"
    stderr_path = log_dir / f"{row_name}.stderr.log"
    for stale in [out_path, progress_path, ub_path, stdout_path, stderr_path]:
        if stale.exists():
            stale.unlink()
    exe = Path(args.exe)
    if not exe.is_absolute():
        exe = ROOT / exe
    command = build_command(
        exe,
        row_name,
        input_path,
        out_path,
        progress_path,
        ub_path,
        args.time_limit,
        args.oracle_time_limit,
        args.oracle_max_leaves,
        args.oracle_order,
        args.oracle_continue_after_timeout,
        args.oracle_split_on_timeout,
        args.oracle_child_split_count,
        args.oracle_max_depth,
        args.auto_bpc_fallback,
        args.bpc_time_limit,
        args.bpc_max_leaves,
    )
    start = time.monotonic()
    returncode: Optional[int] = None
    timed_out = False
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        proc = subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr)
        try:
            returncode = proc.wait(timeout=args.wall_timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            returncode = proc.wait()
    elapsed = time.monotonic() - start
    if out_path.exists():
        try:
            payload = json.loads(out_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        if isinstance(payload, dict):
            payload.setdefault("finalization_source", "solver_final_json")
            payload["solver_finalization_reached"] = True
            payload["wrapper_synthesized_final_json"] = False
            payload["process_return_code"] = returncode if returncode is not None else 0
            payload["abnormal_exit_detected"] = returncode not in (None, 0)
            payload["abnormal_exit_reason"] = (
                "none" if returncode in (None, 0)
                else f"process_return_code_{returncode}"
            )
            payload.setdefault("last_progress_event", "solver_final_json")
            payload.setdefault(
                "plateau_reason",
                "certified" if payload.get("status") == "optimal" else "not_certified",
            )
            out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        payload = synthesize_json(
            row_name=row_name,
            input_path=input_path,
            out_path=out_path,
            progress_path=progress_path,
            ub_path=ub_path,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            scope=args.instance_scope,
            v=args.V,
            m=args.M,
            command=command,
            finalization_source="interrupted_checkpoint" if timed_out else "wrapper_checkpoint",
            stop_reason="wrapper_wall_timeout" if timed_out else "process_exit_without_json",
            process_returncode=returncode,
        )
        if args.oracle_time_limit > 0:
            synth_path = json.loads(out_path.read_text(encoding="utf-8"))
            run_checkpoint_oracle_for_payload(
                payload=synth_path,
                row_name=row_name,
                result_dir=result_dir,
                exe=exe,
                oracle_time_limit=args.oracle_time_limit,
            )
    status = ""
    certified = False
    gap = ""
    if out_path.exists():
        data = json.loads(out_path.read_text(encoding="utf-8"))
        status = str(data.get("status", ""))
        certified = bool(data.get("certified_original_problem", False))
        gap = str(data.get("gap", ""))
    return {
        "row": row_name,
        "input": str(input_path),
        "status": status,
        "certified_original_problem": certified,
        "gap": gap,
        "returncode": returncode,
        "timed_out": timed_out,
        "wall_seconds": elapsed,
        "result_json": str(out_path),
        "progress_log": str(progress_path),
        "ub_event_log": str(ub_path),
        "stdout_log": str(stdout_path),
        "stderr_log": str(stderr_path),
        "command": " ".join(command),
    }


def summarize_round(result_dir: Path, rows: Iterable[tuple]) -> None:
    raw = result_dir / "raw"
    summary: List[Dict[str, Any]] = []
    intervals: List[Dict[str, Any]] = []
    oracle: List[Dict[str, Any]] = []
    bpc: List[Dict[str, Any]] = []
    run_exit: List[Dict[str, Any]] = []
    commands: List[Dict[str, Any]] = []
    instances: List[Dict[str, Any]] = []
    for name, input_path_text, scope, v, m, time_limit, wall_timeout in rows:
        out_path = raw / f"{name}.json"
        progress_path = raw / f"{name}.progress.csv"
        ub_path = raw / f"{name}.ub_events.csv"
        data: Dict[str, Any] = {}
        if out_path.exists():
            data = json.loads(out_path.read_text(encoding="utf-8"))
        status = data.get("status", "missing_final_json")
        result_json = str(out_path) if out_path.exists() else ""
        summary.append({
            "row": name,
            "input": input_path_text,
            "instance_scope": scope,
            "V": v,
            "M": m,
            "time_limit_seconds": time_limit,
            "wall_timeout_seconds": wall_timeout,
            "status": status,
            "objective": data.get("objective", ""),
            "lower_bound": data.get("lower_bound", ""),
            "upper_bound": data.get("upper_bound", ""),
            "gap": data.get("gap", ""),
            "runtime_seconds": data.get("runtime_seconds", ""),
            "certified_original_problem": data.get("certified_original_problem", False),
            "verifier_passed": data.get("verifier_passed", ""),
            "sealed_run": data.get("sealed_run", ""),
            "finalization_source": data.get("finalization_source", ""),
            "solver_finalization_reached": data.get("solver_finalization_reached", ""),
            "wrapper_synthesized_final_json": data.get("wrapper_synthesized_final_json", ""),
            "process_return_code": data.get("process_return_code", data.get("wrapper_process_returncode", "")),
            "abnormal_exit_detected": data.get("abnormal_exit_detected", ""),
            "abnormal_exit_reason": data.get("abnormal_exit_reason", ""),
            "last_progress_event": data.get("last_progress_event", ""),
            "plateau_reason": data.get("plateau_reason", ""),
            "unresolved_intervals": data.get("unresolved_intervals", ""),
            "open_nodes": data.get("open_nodes", ""),
            "auto_interval_oracle_called": data.get("auto_interval_oracle_called", ""),
            "auto_interval_oracle_total_final_leaves": data.get("auto_interval_oracle_total_final_leaves", ""),
            "auto_interval_oracle_leaves_attempted": data.get("auto_interval_oracle_leaves_attempted", ""),
            "auto_interval_oracle_leaves_closed": data.get("auto_interval_oracle_leaves_closed", ""),
            "auto_interval_oracle_leaves_timed_out": data.get("auto_interval_oracle_leaves_timed_out", ""),
            "auto_interval_oracle_leaves_split": data.get("auto_interval_oracle_leaves_split", ""),
            "auto_interval_oracle_remaining_open_leaves": data.get("auto_interval_oracle_remaining_open_leaves", ""),
            "auto_interval_oracle_coverage_complete": data.get("auto_interval_oracle_coverage_complete", ""),
            "full_ledger_merge_status": data.get("full_ledger_merge_status", ""),
            "bpc_fallback_auto_called": data.get("bpc_fallback_auto_called", ""),
            "progress_log": str(progress_path) if progress_path.exists() else "",
            "ub_event_log": str(ub_path) if ub_path.exists() else "",
            "result_json": result_json,
        })
        if status in {"interrupted_noncertified", "missing_final_json"}:
            run_exit.append(summary[-1])
        interval_path_text = data.get("bpc_interval_trace_csv", "") or data.get("bpc_interval_trace_csv_path", "")
        interval_path = Path(interval_path_text) if interval_path_text else raw / f"{name}.intervals.csv"
        if interval_path.exists():
            for rec in read_csv_rows(interval_path):
                intervals.append({"row": name, **rec})
        oracle_path = raw / f"{name}.auto_oracle.csv"
        if oracle_path.exists():
            for rec in read_csv_rows(oracle_path):
                oracle.append({"row": name, **rec})
        commands.append({
            "row": name,
            "input": input_path_text,
            "time_limit_seconds": time_limit,
            "wall_timeout_seconds": wall_timeout,
            "result_json": result_json,
        })
        input_path = ROOT / input_path_text
        instances.append({
            "row": name,
            "input": input_path_text,
            "instance_scope": scope,
            "V": v,
            "M": m,
            "sha256": sha256(input_path),
        })
    write_csv(result_dir / "sealed_minisuite_summary.csv", summary)
    write_csv(result_dir / "sealed_minisuite_interval_status.csv", intervals)
    write_csv(result_dir / "sealed_minisuite_oracle_summary.csv", oracle)
    write_csv(result_dir / "sealed_minisuite_bpc_summary.csv", bpc)
    write_csv(result_dir / "run_exit_summary.csv", run_exit)
    write_csv(result_dir / "command_manifest.csv", commands)
    write_csv(result_dir / "instance_manifest.csv", instances)


def run_self_test(args: argparse.Namespace) -> int:
    result_dir = Path(args.result_dir)
    raw = result_dir / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    progress = raw / "missing_final.progress.csv"
    ub = raw / "missing_final.ub_events.csv"
    progress.write_text(
        "elapsed_seconds,event,incumbent_UB,global_LB,gap,unresolved_intervals,"
        "global_min_lb_interval_id,global_min_lb_interval_range,global_min_lb_source,"
        "open_nodes,pricing_time_seconds,master_time_seconds,bound_time_seconds\n"
        "12.5,adaptive_split_child_1,1.5,1.0,0.333333,2,1,\"[0.1,0.2]\",gamma_floor,2,0,0,12\n",
        encoding="utf-8",
    )
    ub.write_text(
        "time_seconds,source,objective,G,P,improvement_over_previous,verifier_passed,accepted\n"
        "1,native_hga_tgbc_initial,1.5,0.2,8.6,0,true,true\n",
        encoding="utf-8",
    )
    payload = synthesize_json(
        row_name="missing_final",
        input_path=ROOT / "testdata/examples/gcap_smoke_V4_M1.txt",
        out_path=raw / "missing_final.json",
        progress_path=progress,
        ub_path=ub,
        stdout_path=result_dir / "logs/missing_final.stdout.log",
        stderr_path=result_dir / "logs/missing_final.stderr.log",
        scope="smoke",
        v=4,
        m=1,
        command=["synthetic"],
        finalization_source="interrupted_checkpoint",
        stop_reason="self_test_missing_final_json",
        process_returncode=None,
    )
    rows = [{
        "test": "missing_final_json_synthesized",
        "status": payload["status"],
        "finalization_source": payload["finalization_source"],
        "certified_original_problem": payload["certified_original_problem"],
        "result_json": str(raw / "missing_final.json"),
    }]
    write_csv(result_dir / "finalization_test_summary.csv", rows)
    return 0


def postprocess_oracles(args: argparse.Namespace) -> int:
    result_dir = Path(args.result_dir)
    exe = Path(args.exe)
    if not exe.is_absolute():
        exe = ROOT / exe
    count = 0
    for path in sorted((result_dir / "raw").glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if payload.get("status") != "interrupted_noncertified":
            continue
        if payload.get("auto_interval_oracle_called"):
            continue
        run_checkpoint_oracle_for_payload(
            payload=payload,
            row_name=path.stem,
            result_dir=result_dir,
            exe=exe,
            oracle_time_limit=args.oracle_time_limit,
        )
        count += 1
    print(f"checkpoint_oracles_run={count}")
    return 0


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run-row")
    run.add_argument("--row-name", required=True)
    run.add_argument("--input", required=True)
    run.add_argument("--instance-scope", required=True)
    run.add_argument("--V", type=int, required=True)
    run.add_argument("--M", type=int, required=True)
    run.add_argument("--time-limit", type=int, required=True)
    run.add_argument("--wall-timeout", type=int, required=True)
    run.add_argument("--oracle-time-limit", type=int, default=300)
    run.add_argument("--oracle-max-leaves", default="all")
    run.add_argument("--oracle-order", default="all")
    run.add_argument("--oracle-continue-after-timeout", action=argparse.BooleanOptionalAction, default=True)
    run.add_argument("--oracle-split-on-timeout", action=argparse.BooleanOptionalAction, default=False)
    run.add_argument("--oracle-child-split-count", type=int, default=2)
    run.add_argument("--oracle-max-depth", type=int, default=0)
    run.add_argument("--auto-bpc-fallback", action="store_true")
    run.add_argument("--bpc-time-limit", type=int, default=120)
    run.add_argument("--bpc-max-leaves", type=int, default=1)
    run.add_argument("--result-dir", default="results/sealed_pipeline_completion_round")
    run.add_argument("--exe", default="build/ExactEBRP.exe")

    suite = sub.add_parser("summarize")
    suite.add_argument("--result-dir", default="results/sealed_pipeline_completion_round")

    self_test = sub.add_parser("self-test")
    self_test.add_argument("--result-dir", default="results/sealed_pipeline_completion_round/finalization_tests")

    post = sub.add_parser("postprocess-oracles")
    post.add_argument("--result-dir", default="results/sealed_pipeline_completion_round")
    post.add_argument("--exe", default="build/ExactEBRP.exe")
    post.add_argument("--oracle-time-limit", type=int, default=60)

    args = parser.parse_args(argv)
    if args.cmd == "run-row":
        row = run_row(args)
        print(json.dumps(row, indent=2))
        return 0
    if args.cmd == "summarize":
        summarize_round(Path(args.result_dir), DEFAULT_ROWS)
        return 0
    if args.cmd == "self-test":
        return run_self_test(args)
    if args.cmd == "postprocess-oracles":
        return postprocess_oracles(args)
    raise AssertionError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
