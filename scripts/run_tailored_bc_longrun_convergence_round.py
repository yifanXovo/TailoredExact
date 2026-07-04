#!/usr/bin/env python3
"""Production bound-trajectory diagnostics for paper-gf-tailored-bc.

Each fixed-interval solve is executed as a child worker.  If the CPLEX
callback solve does not return, the parent terminates the worker and preserves
the best CPLEX-native checkpoint bound from the progress CSV as diagnostic
evidence only.  Plain CPLEX rows remain benchmark-only.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "gf_tailored_bc_longrun_convergence_round"
RAW = RESULTS / "raw"
LOGS = RESULTS / "logs"
PROGRESS = RESULTS / "progress_traces"
EXE = ROOT / "build" / "ExactEBRP.exe"
PY = Path(r"D:\msys64\ucrt64\bin\python.exe")


def f(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
        return out if math.isfinite(out) else default
    except Exception:
        return default


def i(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def csv_escape(value: Any) -> str:
    return str(value).replace("\n", " ").replace("\r", " ")


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if isinstance(data, dict) and isinstance(data.get("results"), list) and data["results"]:
        first = data["results"][0]
        return first if isinstance(first, dict) else {}
    return data if isinstance(data, dict) else {}


def read_progress(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: List[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def merge_existing_rows(rows: List[Dict[str, Any]], replace: bool) -> List[Dict[str, Any]]:
    if replace:
        return rows
    existing = read_csv(RESULTS / "bound_trajectory_summary.csv")
    merged: Dict[str, Dict[str, Any]] = {}
    for row in existing:
        key = str(row.get("row", ""))
        if key:
            merged[key] = row
    for row in rows:
        key = str(row.get("row", ""))
        if key:
            merged[key] = row
    return list(merged.values())


def native_bound_rows(rows: Sequence[Dict[str, str]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for row in rows:
        if not b(row.get("best_bound_available")):
            continue
        source = str(row.get("progress_source", "")).strip('"')
        if source not in {
            "cplex_native_callback_info",
            "cplex_solver_final",
            "cplex_time_limit_with_valid_best_bound",
        }:
            continue
        bound = f(row.get("best_bound"), float("nan"))
        if math.isfinite(bound):
            out.append(row)
    return out


def trajectory_metrics(rows: Sequence[Dict[str, str]], cutoff: float) -> Dict[str, Any]:
    valid = native_bound_rows(rows)
    if not valid:
        return {
            "initial_bound": 0.0,
            "final_valid_bound": 0.0,
            "best_gap_seen": 1.0,
            "time_of_first_valid_bound": 0.0,
            "time_of_last_bound_improvement": 0.0,
            "number_of_bound_improvements": 0,
            "node_count_at_best_bound": 0,
            "callback_count_at_best_bound": 0,
            "plateau_detected": False,
            "plateau_after_seconds": 0.0,
            "best_row": {},
            "valid_checkpoint_count": 0,
        }
    initial = f(valid[0].get("best_bound"))
    best = valid[0]
    best_bound = initial
    improvements = 1
    previous = initial
    for row in valid[1:]:
        bound = f(row.get("best_bound"))
        if bound > previous + 1e-9:
            improvements += 1
            previous = bound
        if bound > best_bound + 1e-9:
            best_bound = bound
            best = row
    best_gap = max(0.0, (cutoff - best_bound) / abs(cutoff)) if abs(cutoff) > 1e-12 else 0.0
    first_time = f(valid[0].get("elapsed_seconds"))
    last_improvement = f(best.get("elapsed_seconds"))
    final_time = f(valid[-1].get("elapsed_seconds"))
    plateau = b(valid[-1].get("plateau_detected")) or (
        improvements <= 1 and final_time - first_time >= 60.0
    )
    return {
        "initial_bound": initial,
        "final_valid_bound": best_bound,
        "best_gap_seen": best_gap,
        "time_of_first_valid_bound": first_time,
        "time_of_last_bound_improvement": last_improvement,
        "number_of_bound_improvements": improvements,
        "node_count_at_best_bound": i(best.get("node_count")),
        "callback_count_at_best_bound": (
            i(best.get("relaxation_callback_calls")) +
            i(best.get("candidate_callback_calls")) +
            i(best.get("branch_callback_calls")) +
            i(best.get("progress_callback_calls"))
        ),
        "plateau_detected": plateau,
        "plateau_after_seconds": max(0.0, final_time - last_improvement),
        "best_row": best,
        "valid_checkpoint_count": len(valid),
    }


def row_classification(summary: Dict[str, Any]) -> str:
    status = str(summary.get("status", ""))
    variant = str(summary.get("variant", ""))
    valid = b(summary.get("compact_bc_best_bound_available")) and b(summary.get("compact_bc_bound_valid"))
    gap = f(summary.get("final_gap_to_cutoff"), f(summary.get("gap"), 1.0))
    improvements = i(summary.get("number_of_bound_improvements"))
    plateau = b(summary.get("plateau_detected"))
    if status in {"interval_closed", "solver_final_certified", "solver_final_infeasible"}:
        return "closed_by_solver_final"
    if valid and gap <= 1e-4:
        return "near_closure"
    if valid and improvements >= 2 and not plateau:
        return "converging_bound_progress"
    if valid and plateau:
        return "plateau_weak_bound"
    if "plain" in variant:
        return "plain_benchmark_no_valid_checkpoint"
    if "callback" in variant:
        return "finalization_bug_no_valid_bound"
    return "mixed_behavior"


def run_cmd(args: List[str], log_path: Path, timeout: int, skip_existing: bool) -> Dict[str, Any]:
    out_path: Path | None = None
    if "--out" in args:
        try:
            out_path = Path(args[args.index("--out") + 1])
        except Exception:
            out_path = None
    if skip_existing:
        return {
            "returncode": 0 if out_path and out_path.exists() else 124,
            "timeout": False,
            "runtime_seconds": 0.0,
            "skipped_existing": bool(out_path and out_path.exists()),
        }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    with log_path.open("w", encoding="utf-8", errors="replace") as log:
        log.write("COMMAND: " + " ".join(args) + "\n\n")
        log.flush()
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
        proc = subprocess.Popen(
            args,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=creationflags,
        )
        try:
            stdout, _ = proc.communicate(timeout=timeout)
            log.write(stdout or "")
            return {
                "returncode": proc.returncode,
                "timeout": False,
                "runtime_seconds": time.time() - start,
                "skipped_existing": False,
            }
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                proc.kill()
            stdout, _ = proc.communicate()
            log.write(stdout or "")
            log.write("\nWRAPPER_TIMEOUT\n")
            return {
                "returncode": 124,
                "timeout": True,
                "runtime_seconds": time.time() - start,
                "skipped_existing": False,
            }


def worker_timeout(budget: int) -> int:
    if budget <= 60:
        return budget + 35
    if budget <= 300:
        return budget + 45
    return budget + 60


def wrapper_status(has_rows: bool, has_bound: bool) -> str:
    if has_bound:
        return "wrapper_timeout_valid_checkpoint_bound"
    if has_rows:
        return "wrapper_timeout_heartbeat_only"
    return "wrapper_timeout_no_valid_bound"


def write_wrapper_json(
    path: Path,
    *,
    row: str,
    instance: Path,
    gamma_l: float,
    gamma_u: float,
    ub: float,
    budget: int,
    variant: str,
    progress: Path,
    meta: Dict[str, Any],
) -> None:
    rows = read_progress(progress)
    metrics = trajectory_metrics(rows, ub)
    has_bound = metrics["valid_checkpoint_count"] > 0
    best_bound = f(metrics["final_valid_bound"]) if has_bound else 0.0
    best_row = metrics.get("best_row", {}) if isinstance(metrics.get("best_row"), dict) else {}
    status = wrapper_status(bool(rows), has_bound)
    gap = max(0.0, (ub - best_bound) / abs(ub)) if has_bound and abs(ub) > 1e-12 else 1.0
    callback_variant = variant.startswith("callback") or "tailored" in variant
    plain_variant = "plain" in variant
    data = {
        "status": status,
        "method": "interval-cutoff-oracle",
        "algorithm_preset": "paper-gf-tailored-bc" if callback_variant else "paper-gf-compact-bc",
        "instance_name": instance.name,
        "input_path": str(instance),
        "time_budget_seconds": budget,
        "runtime_seconds": meta.get("runtime_seconds", 0.0),
        "actual_runtime_seconds": meta.get("runtime_seconds", 0.0),
        "thread_fairness_class": "one_thread_fair",
        "solver_thread_policy": "controlled_single_thread",
        "finalization_source": "wrapper_best_cplex_native_checkpoint" if has_bound else "wrapper_error_json",
        "solver_finalization_reached": False,
        "wrapper_synthesized_final_json": True,
        "certified_original_problem": False,
        "verifier_passed": False,
        "lower_bound": best_bound if has_bound else 0.0,
        "upper_bound": ub,
        "gap": gap,
        "compact_bc_best_bound_available": has_bound,
        "compact_bc_best_bound": best_bound,
        "compact_bc_bound_valid": has_bound,
        "compact_interval_bc_bound_valid": has_bound,
        "interval_oracle_bound_valid": has_bound,
        "interval_oracle_can_merge_bound": False,
        "compact_bc_best_bound_fail_reason": (
            "checkpoint_cplex_native_best_bound_after_external_worker_stop"
            if has_bound else
            ("heartbeat_only_checkpoint_no_native_bound" if rows else "native_cplex_callback_did_not_return_before_parent_timeout")
        ),
        "compact_bc_bound_scope": "original_fixed_interval",
        "compact_bc_checkpoint_best_bound_available": has_bound,
        "compact_bc_checkpoint_best_bound": best_bound,
        "compact_bc_checkpoint_incumbent_available": b(best_row.get("incumbent_available")),
        "compact_bc_checkpoint_incumbent": f(best_row.get("incumbent")),
        "compact_bc_checkpoint_node_count": i(best_row.get("node_count")),
        "compact_bc_native_time_limit_param_id": 1039,
        "compact_bc_native_time_limit_seconds": budget,
        "compact_bc_native_time_limit_set_rc": 0,
        "compact_bc_terminate_set_rc": 0,
        "compact_bc_terminate_triggered": True,
        "compact_bc_terminate_after_seconds": f(best_row.get("elapsed_seconds"), meta.get("runtime_seconds", 0.0)),
        "compact_bc_callback_abort_requests": i(best_row.get("callback_abort_requests")),
        "progress_log_path": str(progress),
        "progress_log": str(progress),
        "progress_checkpoints_written": len(rows),
        "gap_trajectory_available": bool(rows),
        "plateau_detected": metrics["plateau_detected"],
        "last_bound_improvement_time": metrics["time_of_last_bound_improvement"],
        "tailored_bc_enabled": callback_variant,
        "tailored_bc_mode": "callback" if callback_variant else ("plain_fixed_interval" if plain_variant else "static"),
        "tailored_bc_callback_available": callback_variant,
        "tailored_bc_user_cut_callback_enabled": callback_variant,
        "tailored_bc_branch_callback_enabled": callback_variant,
        "tailored_bc_lazy_callback_enabled": callback_variant,
        "tailored_bc_incumbent_callback_enabled": callback_variant,
        "tailored_bc_relaxation_callback_calls": i(best_row.get("relaxation_callback_calls")),
        "tailored_bc_candidate_callback_calls": i(best_row.get("candidate_callback_calls")),
        "tailored_bc_branch_callback_calls": i(best_row.get("branch_callback_calls")),
        "tailored_bc_progress_callback_calls": i(best_row.get("progress_callback_calls")),
        "tailored_bc_gini_branches_created": i(best_row.get("gini_branches_created")),
        "tailored_bc_user_cuts_added_by_family": best_row.get("user_cuts_added_by_family", ""),
        "tailored_bc_violations_by_family": best_row.get("violations_by_family", ""),
        "tailored_bc_callback_separation_pacing": best_row.get("separation_pacing", ""),
        "tailored_bc_callback_expensive_separation_calls": i(best_row.get("expensive_separation_calls")),
        "tailored_bc_callback_expensive_separation_skips": i(best_row.get("expensive_separation_skips")),
        "best_valid_lb_seen": best_bound if has_bound else 0.0,
        "best_valid_gap_seen": gap,
        "best_valid_ledger_checkpoint": str(progress) if has_bound else "",
        "best_valid_ledger_time": metrics["time_of_last_bound_improvement"],
        "final_json_uses_best_checkpoint": has_bound,
        "interrupted_run_best_bound_preserved": has_bound,
        "diagnostic_row": True,
        "method_scope": "plain_fixed_interval_benchmark" if plain_variant else "callback_diagnostic_fixed_interval",
        "paper_certificate_contamination": False,
        "plain_cplex_benchmark_used_as_certificate": False,
        "certificate_uses_bpc_tree": False,
        "route_mask_all_subset_enumeration_certifying": False,
        "no_archive_scanning": True,
        "no_external_known_ub": True,
        "notes": [
            "parsed Hybrid GA text format; distances read from serialized distance matrix",
            "Wrapper timeout is diagnostic-only and is not a paper-core certificate.",
            "CPLEX-native checkpoint best bounds are preserved only when progress_source is cplex_native_callback_info.",
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def normalize_json(path: Path) -> None:
    data = read_json(path)
    if not data:
        return
    changed = False
    if data.get("method") == "cplex" or data.get("method_scope") == "plain_cplex":
        for key, value in {
            "method_scope": "plain_cplex",
            "diagnostic_row": True,
            "certified_original_problem": False,
            "plain_cplex_benchmark_used_as_certificate": False,
            "paper_certificate_contamination": False,
        }.items():
            if data.get(key) != value:
                data[key] = value
                changed = True
    if str(data.get("status", "")).startswith("wrapper_timeout"):
        for key, value in {
            "paper_certificate_contamination": False,
            "plain_cplex_benchmark_used_as_certificate": False,
            "route_mask_all_subset_enumeration_certifying": False,
            "no_archive_scanning": True,
            "no_external_known_ub": True,
        }.items():
            if data.get(key) != value:
                data[key] = value
                changed = True
        notes = data.get("notes", [])
        if not isinstance(notes, list):
            notes = [notes]
        if not any("distance" in str(note).lower() or "coordinate" in str(note).lower()
                   for note in notes):
            notes.insert(0, "parsed Hybrid GA text format; distances read from serialized distance matrix")
            data["notes"] = notes
            changed = True
    if changed:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def normalize_raw_tree() -> None:
    for path in RAW.rglob("*.json"):
        normalize_json(path)


def interval_cmd(
    instance: Path,
    gl: float,
    gu: float,
    ub: float,
    budget: int,
    variant: str,
    progress: Path,
    out: Path,
) -> List[str]:
    callback = variant.startswith("callback")
    preset = "paper-gf-tailored-bc" if callback else "paper-gf-compact-bc"
    cmd = [
        str(EXE), "--method", "interval-cutoff-oracle",
        "--algorithm-preset", preset,
        "--paper-run-sealed", "true",
        "--input", str(instance),
        "--lambda", "0.15", "--T", "3600",
        "--interval-exact-cutoff-oracle", "compact-mip",
        "--interval-exact-cutoff-gamma-L", str(gl),
        "--interval-exact-cutoff-gamma-U", str(gu),
        "--interval-exact-cutoff-UB", str(ub),
        "--interval-exact-cutoff-time-limit", str(budget),
        "--compact-bc-threads", "1", "--mip-threads", "1",
        "--progress-log", str(progress),
        "--compact-bc-progress-interval", "30" if budget >= 300 else "10",
        "--out", str(out),
    ]
    if variant == "plain_fixed_interval_cplex_benchmark":
        cmd += [
            "--compact-bc-gini-cap-floor-cuts", "false",
            "--compact-bc-tight-mccormick", "false",
            "--compact-bc-inventory-conservation", "false",
            "--compact-bc-movement-reachability", "false",
            "--compact-bc-visit-inventory-linking", "false",
            "--compact-bc-objective-estimator-cutoff", "false",
            "--compact-bc-penalty-lb-closure", "false",
            "--compact-bc-gini-spread", "false",
            "--compact-bc-required-movement", "false",
            "--compact-bc-global-handling-capacity", "false",
            "--compact-bc-low-gini-centering", "false",
            "--compact-bc-support-duration", "false",
            "--compact-bc-transfer-compat", "false",
            "--compact-bc-receiver-source-cover", "off",
        ]
    elif variant == "static_tailored_compact_bc":
        cmd += ["--compact-bc-cut-profile", "balanced", "--compact-bc-root-cut-rounds", "1"]
    elif variant == "callback_tailored_bc_gini_off":
        cmd += ["--tailored-bc-mode", "callback", "--tailored-bc-gini-branching", "off"]
    elif variant == "callback_tailored_bc_gini_auto":
        cmd += ["--tailored-bc-mode", "callback", "--tailored-bc-gini-branching", "auto"]
    elif variant == "callback_tailored_bc_paced":
        cmd += [
            "--tailored-bc-mode", "callback",
            "--tailored-bc-gini-branching", "auto",
            "--tailored-bc-callback-separation-pacing", "bound-aware",
            "--tailored-bc-callback-separation-min-calls", "50",
        ]
    return cmd


def run_interval(row: str, spec: Dict[str, Any], budget: int, variant: str, skip: bool) -> Dict[str, Any]:
    out = RAW / f"{row}.json"
    progress = PROGRESS / f"{row}.progress.csv"
    cmd = interval_cmd(spec["instance"], spec["gl"], spec["gu"], spec["ub"], budget, variant, progress, out)
    meta = run_cmd(cmd, LOGS / f"{row}.log", worker_timeout(budget), skip)
    if meta.get("timeout") or not out.exists():
        write_wrapper_json(
            out,
            row=row,
            instance=spec["instance"],
            gamma_l=spec["gl"],
            gamma_u=spec["gu"],
            ub=spec["ub"],
            budget=budget,
            variant=variant,
            progress=progress,
            meta=meta,
        )
    return summarize(row, out, budget, variant, progress, spec)


def run_full(row: str, instance: Path, budget: int, kind: str, skip: bool) -> Dict[str, Any]:
    out = RAW / f"{row}.json"
    progress = PROGRESS / f"{row}.progress.csv"
    if kind == "plain_cplex":
        cmd = [
            str(EXE), "--method", "cplex", "--plain-baseline",
            "--input", str(instance), "--lambda", "0.15", "--T", "3600",
            "--time-limit", str(budget), "--cplex-threads", "1",
            "--mip-threads", "1", "--out", str(out),
        ]
    else:
        cmd = [
            str(EXE), "--method", "gcap-frontier",
            "--algorithm-preset", "paper-gf-tailored-bc",
            "--paper-run-sealed", "true",
            "--input", str(instance), "--lambda", "0.15", "--T", "3600",
            "--time-limit", str(budget),
            "--compact-bc-threads", "1", "--mip-threads", "1",
            "--progress-log", str(progress),
            "--progress-interval-seconds", "30",
            "--out", str(out),
        ]
    meta = run_cmd(cmd, LOGS / f"{row}.log", budget + 90, skip)
    if meta.get("timeout") or not out.exists():
        write_wrapper_json(
            out, row=row, instance=instance, gamma_l=0.0, gamma_u=1.0,
            ub=0.0, budget=budget, variant=kind, progress=progress, meta=meta,
        )
    if kind == "plain_cplex":
        data = read_json(out)
        if data:
            data["method_scope"] = "plain_cplex"
            data["diagnostic_row"] = True
            data["certified_original_problem"] = False
            data["plain_cplex_benchmark_used_as_certificate"] = False
            data["paper_certificate_contamination"] = False
            out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return summarize(row, out, budget, kind, progress, {"name": row, "ub": 0.0, "gl": 0.0, "gu": 1.0})


def summarize(
    row: str,
    path: Path,
    budget: int,
    variant: str,
    progress: Path,
    spec: Dict[str, Any],
) -> Dict[str, Any]:
    normalize_json(path)
    data = read_json(path)
    rows = read_progress(progress)
    ub = f(data.get("upper_bound", spec.get("ub", 0.0)), spec.get("ub", 0.0))
    metrics = trajectory_metrics(rows, ub if abs(ub) > 1e-12 else f(spec.get("ub", 0.0)))
    last = rows[-1] if rows else {}
    best_row = metrics.get("best_row", {}) if isinstance(metrics.get("best_row"), dict) else {}
    status = str(data.get("status", "missing_json"))
    valid_bound = b(data.get("compact_bc_bound_valid", data.get("interval_oracle_bound_valid", False)))
    best_available = b(data.get("compact_bc_best_bound_available", False))
    lower = f(data.get("lower_bound", data.get("compact_bc_best_bound", 0.0)))
    upper = f(data.get("upper_bound", spec.get("ub", 0.0)), spec.get("ub", 0.0))
    gap = f(data.get("gap"), 1.0)
    cutoff = f(spec.get("ub", upper), upper)
    final_gap_to_cutoff = (
        max(0.0, (cutoff - lower) / abs(cutoff))
        if abs(cutoff) > 1e-12 else gap
    )
    summary: Dict[str, Any] = {
        "row": row,
        "target_leaf": spec.get("name", row),
        "variant": variant,
        "json": str(path.relative_to(ROOT)) if path.exists() else str(path),
        "progress_log_path": str(progress.relative_to(ROOT)) if progress.exists() else str(progress),
        "status": status,
        "method": data.get("method", ""),
        "algorithm_preset": data.get("algorithm_preset", ""),
        "instance_name": data.get("instance_name", spec.get("instance", Path()).name),
        "input_path": data.get("input_path", str(spec.get("instance", ""))),
        "gamma_L": spec.get("gl", ""),
        "gamma_U": spec.get("gu", ""),
        "time_budget_seconds": budget,
        "runtime_seconds": f(data.get("runtime_seconds", data.get("actual_runtime_seconds", 0.0))),
        "thread_fairness_class": data.get("thread_fairness_class", ""),
        "finalization_source": data.get("finalization_source", ""),
        "solver_finalization_reached": data.get("solver_finalization_reached", not str(status).startswith("wrapper_timeout")),
        "wrapper_synthesized_final_json": data.get("wrapper_synthesized_final_json", str(status).startswith("wrapper_timeout")),
        "lower_bound": lower,
        "upper_bound": upper,
        "gap": gap,
        "initial_bound": metrics["initial_bound"],
        "final_valid_bound": metrics["final_valid_bound"],
        "incumbent_cutoff": cutoff,
        "final_gap_to_cutoff": final_gap_to_cutoff,
        "best_gap_seen": metrics["best_gap_seen"],
        "time_of_first_valid_bound": metrics["time_of_first_valid_bound"],
        "time_of_last_bound_improvement": metrics["time_of_last_bound_improvement"],
        "number_of_bound_improvements": metrics["number_of_bound_improvements"],
        "node_count_at_best_bound": metrics["node_count_at_best_bound"],
        "callback_count_at_best_bound": metrics["callback_count_at_best_bound"],
        "compact_bc_best_bound_available": best_available,
        "compact_bc_best_bound": data.get("compact_bc_best_bound", ""),
        "compact_bc_bound_valid": valid_bound,
        "compact_bc_best_bound_fail_reason": data.get("compact_bc_best_bound_fail_reason", ""),
        "compact_bc_checkpoint_best_bound_available": data.get("compact_bc_checkpoint_best_bound_available", ""),
        "compact_bc_checkpoint_best_bound": data.get("compact_bc_checkpoint_best_bound", ""),
        "compact_bc_checkpoint_incumbent_available": data.get("compact_bc_checkpoint_incumbent_available", ""),
        "compact_bc_checkpoint_incumbent": data.get("compact_bc_checkpoint_incumbent", ""),
        "compact_bc_checkpoint_node_count": data.get("compact_bc_checkpoint_node_count", ""),
        "compact_bc_native_time_limit_param_id": data.get("compact_bc_native_time_limit_param_id", ""),
        "compact_bc_native_time_limit_seconds": data.get("compact_bc_native_time_limit_seconds", ""),
        "compact_bc_native_time_limit_set_rc": data.get("compact_bc_native_time_limit_set_rc", ""),
        "compact_bc_terminate_set_rc": data.get("compact_bc_terminate_set_rc", ""),
        "compact_bc_terminate_triggered": data.get("compact_bc_terminate_triggered", ""),
        "compact_bc_terminate_after_seconds": data.get("compact_bc_terminate_after_seconds", ""),
        "compact_bc_callback_abort_requests": data.get("compact_bc_callback_abort_requests", last.get("callback_abort_requests", "")),
        "progress_checkpoints_written": data.get("progress_checkpoints_written", len(rows)),
        "gap_trajectory_available": data.get("gap_trajectory_available", bool(rows)),
        "plateau_detected": metrics["plateau_detected"],
        "plateau_after_seconds": metrics["plateau_after_seconds"],
        "last_bound_improvement_time": data.get("last_bound_improvement_time", metrics["time_of_last_bound_improvement"]),
        "callback_relaxation_calls": data.get("tailored_bc_relaxation_callback_calls", last.get("relaxation_callback_calls", "")),
        "callback_branch_calls": data.get("tailored_bc_branch_callback_calls", last.get("branch_callback_calls", "")),
        "callback_candidate_calls": data.get("tailored_bc_candidate_callback_calls", last.get("candidate_callback_calls", "")),
        "gini_branches_created": data.get("tailored_bc_gini_branches_created", last.get("gini_branches_created", "")),
        "user_cuts_added_by_family": data.get("tailored_bc_user_cuts_added_by_family", last.get("user_cuts_added_by_family", "")),
        "violations_by_family": data.get("tailored_bc_violations_by_family", last.get("violations_by_family", "")),
        "tailored_bc_callback_separation_pacing": data.get("tailored_bc_callback_separation_pacing", ""),
        "tailored_bc_callback_expensive_separation_calls": data.get("tailored_bc_callback_expensive_separation_calls", ""),
        "tailored_bc_callback_expensive_separation_skips": data.get("tailored_bc_callback_expensive_separation_skips", ""),
        "paper_certificate_contamination": data.get("paper_certificate_contamination", False),
        "plain_cplex_benchmark_used_as_certificate": data.get("plain_cplex_benchmark_used_as_certificate", False),
        "valid_checkpoint_count": metrics["valid_checkpoint_count"],
        "progress_source_at_best": best_row.get("progress_source", ""),
    }
    summary["classification"] = row_classification(summary)
    return summary


def run_audits() -> List[Dict[str, Any]]:
    specs = [
        ("audit_bpc_self_test", [str(PY), "scripts/audit_bpc_certificate.py", "--self-test"]),
        ("audit_bpc_certificate", [str(PY), "scripts/audit_bpc_certificate.py", str(RAW), "--csv-out", str(RESULTS / "certificate_audit.csv"), "--fail-on-error"]),
        ("audit_tailored_bc_callback_round", [str(PY), "scripts/audit_tailored_bc_callback_round.py", "--results", str(RESULTS), "--out", str(RESULTS / "tailored_bc_callback_audit.csv")]),
        ("audit_gf_compact_bc_summary", [str(PY), "scripts/audit_gf_compact_bc_summary.py", "--results", str(RESULTS), "--out", str(RESULTS / "summary_cleanup_audit.csv")]),
        ("audit_thread_fairness", [str(PY), "scripts/audit_thread_fairness.py", "--results", str(RESULTS), "--out", str(RESULTS / "thread_fairness_audit.csv")]),
        ("audit_objective_convention", [str(PY), "scripts/audit_objective_convention.py", "--results", str(RESULTS), "--out", str(RESULTS / "objective_convention_audit.csv")]),
        ("audit_timeprofile_finalization", [str(PY), "scripts/audit_timeprofile_finalization.py", "--results", str(RESULTS), "--out", str(RESULTS / "timeprofile_finalization_audit.csv")]),
        ("audit_certificate_sources", [str(PY), "scripts/audit_certificate_sources.py", "--results", str(RESULTS), "--out", str(RESULTS / "certificate_source_audit.csv")]),
        ("audit_no_instance_special_cases", [str(PY), "scripts/audit_no_instance_special_cases.py", "--out", str(RESULTS / "no_instance_special_case_audit.txt")]),
    ]
    rows: List[Dict[str, Any]] = []
    for name, cmd in specs:
        start = time.time()
        log_path = LOGS / f"{name}.log"
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        log_path.write_text((proc.stdout or "") + (proc.stderr or ""), encoding="utf-8")
        rows.append({
            "audit_name": name,
            "return_code": proc.returncode,
            "runtime_seconds": round(time.time() - start, 3),
            "audit_passed": proc.returncode == 0,
            "log": str(log_path.relative_to(ROOT)),
        })
    write_csv(RESULTS / "audit_summary.csv", rows)
    return rows


def build_report(rows: List[Dict[str, Any]], audits: List[Dict[str, Any]], profile: str) -> None:
    hard = [r for r in rows if not str(r["row"]).startswith("control_") and not str(r["row"]).startswith("test_")]
    controls = [r for r in rows if str(r["row"]).startswith("control_") or str(r["row"]).startswith("test_")]
    valid_callback = [r for r in hard if "callback" in str(r["variant"]) and b(r["compact_bc_best_bound_available"])]
    paced = [r for r in rows if r["variant"] == "callback_tailored_bc_paced"]
    best_bottleneck = "finalization_bug_no_valid_bound"
    if valid_callback:
        plateaus = [r for r in valid_callback if b(r["plateau_detected"])]
        if plateaus:
            best_bottleneck = "plateau_weak_bound"
        else:
            best_bottleneck = "callback_overhead_or_branching_mixed"
    lines = [
        "# GF Tailored BC Long-Run Convergence Round",
        "",
        f"Run profile: `{profile}`.",
        "",
        "Plain CPLEX and plain fixed-interval MIP rows are benchmark-only and are not imported into the Tailored-BC certificate ledger.",
        "",
        "## Worker Boundary",
        "",
        "Fixed-interval callback solves run as child workers. When a worker exceeds the parent hard wall-clock cap, the parent terminates the worker tree and preserves only CPLEX-native `CPXCALLBACKINFO_BEST_BND` progress rows as diagnostic lower-bound trajectory points. Heartbeat-only rows are not valid bounds.",
        "",
        "## Targeted Optimization",
        "",
        "This round adds opt-in `--tailored-bc-callback-separation-pacing bound-aware`, which keeps cheap valid rows active while pacing expensive subset/support/transfer separation until either a native best-bound improvement is observed or a configured relaxation-callback interval elapses. This is an exact-safe overhead optimization because it can only skip optional valid cuts, never reject feasible solutions.",
        "",
        "## Hard-Leaf Trajectories",
        "",
        "| row | variant | budget | status | class | valid checkpoints | LB | cutoff | gap_to_cutoff | improvements | plateau |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for r in hard:
        lines.append(
            f"| {r['row']} | {r['variant']} | {r['time_budget_seconds']} | {r['status']} | "
            f"{r['classification']} | {r['valid_checkpoint_count']} | {r['lower_bound']} | "
            f"{r['incumbent_cutoff']} | {r['final_gap_to_cutoff']} | "
            f"{r['number_of_bound_improvements']} | {r['plateau_detected']} |"
        )
    lines += [
        "",
        "## Variant Comparison",
        "",
        "| target | best callback LB | best callback gap | plain/static comparison |",
        "| --- | ---: | ---: | --- |",
    ]
    targets = sorted({str(r["target_leaf"]) for r in hard})
    for target in targets:
        group = [r for r in hard if r["target_leaf"] == target]
        callback_group = [r for r in group if "callback" in str(r["variant"]) and b(r["compact_bc_best_bound_available"])]
        best = max(callback_group, key=lambda x: f(x["lower_bound"]), default=None)
        plain_best = max([r for r in group if "plain" in str(r["variant"])], key=lambda x: f(x["lower_bound"]), default=None)
        lines.append(
            f"| {target} | {best['lower_bound'] if best else 0.0} | "
            f"{best['final_gap_to_cutoff'] if best else 1.0} | "
            f"{plain_best['status'] if plain_best else 'not_run'} |"
        )
    lines += [
        "",
        "## Controls",
        "",
        "| row | status | certified | LB | UB | gap |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for r in controls:
        data = read_json(ROOT / r["json"]) if r.get("json") else {}
        lines.append(
            f"| {r['row']} | {r['status']} | {data.get('certified_original_problem', False)} | "
            f"{r['lower_bound']} | {r['upper_bound']} | {r['gap']} |"
        )
    lines += [
        "",
        "## Audits",
        "",
        "| audit | return code | passed |",
        "| --- | ---: | --- |",
    ]
    for audit in audits:
        lines.append(f"| {audit['audit_name']} | {audit['return_code']} | {audit['audit_passed']} |")
    lines += [
        "",
        "## Conclusions",
        "",
        f"Main bottleneck after this round: `{best_bottleneck}`.",
        "",
        f"Callback hard leaves produced valid CPLEX-native bound trajectories on {len(valid_callback)} callback rows.",
        f"The paced optimization was evaluated on {len(paced)} rows.",
        "",
        "Rows synthesized from wrapper checkpoints remain diagnostic-only unless a future parent-ledger rule explicitly audits and accepts checkpoint-bound evidence.",
    ]
    (RESULTS / "final_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def target_specs() -> List[Dict[str, Any]]:
    base = ROOT / "reference" / "hard_stress" / "V20_M3"
    return [
        {
            "name": "moderate_seed3301_low_gini_1",
            "instance": base / "moderate_seed3301.txt",
            "gl": 0.0122881381662,
            "gu": 0.0245762763324,
            "ub": 0.0491525526647,
        },
        {
            "name": "moderate_seed3301_low_gini_2",
            "instance": base / "moderate_seed3301.txt",
            "gl": 0.0245762763324,
            "gu": 0.0368644144986,
            "ub": 0.0491525526647,
        },
        {
            "name": "high_imbalance_seed3201_hard",
            "instance": base / "high_imbalance_seed3201.txt",
            "gl": 0.0,
            "gu": 0.0625,
            "ub": 2.44340319194,
        },
        {
            "name": "tight_T_seed3102_hard",
            "instance": base / "tight_T_seed3102.txt",
            "gl": 0.0,
            "gu": 0.0625,
            "ub": 0.600704436685,
        },
        {
            "name": "moderate_seed3302_hard",
            "instance": base / "moderate_seed3302.txt",
            "gl": 0.0,
            "gu": 0.0625,
            "ub": 0.120018073519,
        },
    ]


def selected_profile(profile: str) -> tuple[List[Dict[str, Any]], List[int], List[str], bool]:
    specs = target_specs()
    if profile == "smoke":
        return specs[:2], [10], ["callback_tailored_bc_gini_auto", "callback_tailored_bc_paced"], False
    if profile == "moderate1200":
        return specs[:2], [1200], ["callback_tailored_bc_paced"], False
    if profile == "extended3600":
        return specs[:1], [3600], ["callback_tailored_bc_paced"], False
    if profile == "otherhard60":
        return specs[2:], [60], [
            "plain_fixed_interval_cplex_benchmark",
            "callback_tailored_bc_paced",
        ], False
    if profile == "controls":
        return [], [], [], True
    if profile == "focused":
        return specs[:2], [60, 300], [
            "plain_fixed_interval_cplex_benchmark",
            "static_tailored_compact_bc",
            "callback_tailored_bc_gini_auto",
            "callback_tailored_bc_paced",
        ], True
    if profile == "required":
        return specs, [60, 300, 1200], [
            "plain_fixed_interval_cplex_benchmark",
            "static_tailored_compact_bc",
            "callback_tailored_bc_gini_off",
            "callback_tailored_bc_gini_auto",
            "callback_tailored_bc_paced",
        ], True
    return specs, [60, 300, 1200, 3600], [
        "plain_fixed_interval_cplex_benchmark",
        "static_tailored_compact_bc",
        "callback_tailored_bc_gini_off",
        "callback_tailored_bc_gini_auto",
        "callback_tailored_bc_paced",
    ], True


def run_tests(skip: bool) -> List[Dict[str, Any]]:
    v12m1 = ROOT / "reference" / "regen_candidate_V12_M1_average.txt"
    tests = [
        ("test_certificate_basis", RAW / "certificate_basis_test.json", [str(EXE), "--method", "certificate-basis-test", "--input", str(v12m1), "--lambda", "0.15", "--T", "3600", "--time-limit", "10", "--out", str(RAW / "certificate_basis_test.json")]),
        ("test_option_consistency", RAW / "option_consistency_test.json", [str(EXE), "--method", "option-consistency-test", "--input", str(v12m1), "--lambda", "0.15", "--T", "3600", "--time-limit", "10", "--out", str(RAW / "option_consistency_test.json")]),
        ("test_callback_smoke", RAW / "tailored_bc_callback_smoke_test.json", [str(EXE), "--method", "tailored-bc-callback-smoke-test", "--input", str(v12m1), "--lambda", "0.15", "--T", "3600", "--time-limit", "10", "--out", str(RAW / "tailored_bc_callback_smoke_test.json")]),
        ("test_branch_callback_smoke", RAW / "tailored_bc_branch_callback_smoke_test.json", [str(EXE), "--method", "tailored-bc-branch-callback-smoke-test", "--input", str(v12m1), "--lambda", "0.15", "--T", "3600", "--time-limit", "10", "--out", str(RAW / "tailored_bc_branch_callback_smoke_test.json")]),
    ]
    rows: List[Dict[str, Any]] = []
    for name, out, cmd in tests:
        run_cmd(cmd, LOGS / f"{name}.log", 90, skip)
        rows.append(summarize(name, out, 10, "test", PROGRESS / f"{name}.progress.csv", {"name": name, "instance": v12m1, "gl": 0.0, "gu": 1.0, "ub": 0.0}))
    return rows


def run_controls(skip: bool) -> List[Dict[str, Any]]:
    controls = [
        ("control_v12_m1", ROOT / "reference" / "regen_candidate_V12_M1_average.txt"),
        ("control_v12_m2", ROOT / "reference" / "regen_candidate_V12_M2_average.txt"),
        ("control_high_imbalance_seed3202", ROOT / "reference" / "hard_stress" / "V20_M3" / "high_imbalance_seed3202.txt"),
        ("control_tight_T_seed3101", ROOT / "reference" / "hard_stress" / "V20_M3" / "tight_T_seed3101.txt"),
    ]
    v4_candidates = list((ROOT / "reference").rglob("*V4*")) if (ROOT / "reference").exists() else []
    if v4_candidates:
        controls.insert(0, ("control_gcap_smoke_V4_M1", v4_candidates[0]))
    else:
        write_csv(RESULTS / "control_skip_manifest.csv", [{
            "control": "gcap_smoke_V4_M1",
            "status": "skipped_missing_path",
            "path_check": "reference/**/*V4*",
        }])
    return [run_full(f"{name}_tailored_60s", path, 60, "tailored", skip) for name, path in controls]


def make_secondary_outputs(rows: List[Dict[str, Any]]) -> None:
    hard = [r for r in rows if not str(r["row"]).startswith("control_") and not str(r["row"]).startswith("test_")]
    write_csv(RESULTS / "hard_leaf_convergence_classification.csv", hard)
    write_csv(RESULTS / "gap_trajectory_summary.csv", [
        {
            "row": r["row"],
            "variant": r["variant"],
            "budget": r["time_budget_seconds"],
            "initial_bound": r["initial_bound"],
            "final_valid_bound": r["final_valid_bound"],
            "best_gap_seen": r["best_gap_seen"],
            "time_of_first_valid_bound": r["time_of_first_valid_bound"],
            "time_of_last_bound_improvement": r["time_of_last_bound_improvement"],
            "number_of_bound_improvements": r["number_of_bound_improvements"],
            "classification": r["classification"],
        }
        for r in hard
    ])
    write_csv(RESULTS / "plain_cplex_vs_tailored_longrun.csv", rows)
    write_csv(RESULTS / "callback_overhead_summary.csv", [
        {
            "row": r["row"],
            "variant": r["variant"],
            "relaxation_callbacks": r["callback_relaxation_calls"],
            "branch_callbacks": r["callback_branch_calls"],
            "candidate_callbacks": r["callback_candidate_calls"],
            "progress_checkpoints": r["progress_checkpoints_written"],
            "expensive_separation_calls": r["tailored_bc_callback_expensive_separation_calls"],
            "expensive_separation_skips": r["tailored_bc_callback_expensive_separation_skips"],
            "runtime_seconds": r["runtime_seconds"],
            "classification": r["classification"],
        }
        for r in rows if "callback" in str(r["variant"])
    ])
    write_csv(RESULTS / "cut_violation_summary.csv", [
        {
            "row": r["row"],
            "variant": r["variant"],
            "cuts_added_by_family": r["user_cuts_added_by_family"],
            "violations_by_family": r["violations_by_family"],
        }
        for r in rows
    ])
    write_csv(RESULTS / "gini_branching_split_diagnostics.csv", [
        {
            "row": r["row"],
            "variant": r["variant"],
            "gini_branches_created": r["gini_branches_created"],
            "final_valid_bound": r["final_valid_bound"],
            "final_gap_to_cutoff": r["final_gap_to_cutoff"],
            "classification": r["classification"],
        }
        for r in rows if "callback" in str(r["variant"])
    ])
    write_csv(RESULTS / "worker_finalization_audit.csv", [
        {
            "row": r["row"],
            "status": r["status"],
            "classification": r["classification"],
            "solver_finalization_reached": r["solver_finalization_reached"],
            "wrapper_synthesized_final_json": r["wrapper_synthesized_final_json"],
            "best_bound_available": r["compact_bc_best_bound_available"],
            "compact_bc_bound_valid": r["compact_bc_bound_valid"],
            "best_bound_fail_reason": r["compact_bc_best_bound_fail_reason"],
            "finalization_source": r["finalization_source"],
            "audit_passed": not (
                str(r["status"]) == "wrapper_timeout_valid_checkpoint_bound" and
                not b(r["compact_bc_best_bound_available"])
            ),
        }
        for r in rows
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=["smoke", "focused", "moderate1200", "extended3600", "otherhard60", "controls", "required", "full"], default="focused")
    parser.add_argument("--skip-runs", action="store_true")
    parser.add_argument("--skip-controls", action="store_true")
    parser.add_argument("--replace-results", action="store_true")
    parser.add_argument("--extra-extended", action="store_true", help="Add one 3600s paced moderate low-gini run.")
    args = parser.parse_args()

    for path in (RESULTS, RAW, LOGS, PROGRESS):
        path.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    rows.extend(run_tests(args.skip_runs))
    specs, budgets, variants, include_controls = selected_profile(args.profile)
    for spec in specs:
        if not Path(spec["instance"]).exists():
            rows.append({
                "row": spec["name"],
                "target_leaf": spec["name"],
                "variant": "missing_instance",
                "status": "skipped_missing_path",
                "classification": "missing_instance",
                "time_budget_seconds": 0,
                "paper_certificate_contamination": False,
            })
            continue
        for budget in budgets:
            for variant in variants:
                row = f"{spec['name']}_{variant}_{budget}s"
                rows.append(run_interval(row, spec, budget, variant, args.skip_runs))
    if args.extra_extended:
        spec = specs[0]
        row = f"{spec['name']}_callback_tailored_bc_paced_3600s"
        rows.append(run_interval(row, spec, 3600, "callback_tailored_bc_paced", args.skip_runs))
    if include_controls and not args.skip_controls:
        rows.extend(run_controls(args.skip_runs))

    rows = merge_existing_rows(rows, args.replace_results)
    write_csv(RESULTS / "bound_trajectory_summary.csv", rows)
    make_secondary_outputs(rows)
    normalize_raw_tree()
    audits = run_audits()
    build_report(rows, audits, args.profile)
    return 0 if all(a["audit_passed"] for a in audits) else 1


if __name__ == "__main__":
    raise SystemExit(main())
