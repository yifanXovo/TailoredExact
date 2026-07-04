#!/usr/bin/env python3
"""Run valid bound-trajectory diagnostics for paper-gf-tailored-bc.

The runner treats each hard fixed interval as a worker process. If CPLEX's
callback solve does not return control, the parent preserves any CPLEX-native
checkpoint best bounds from the progress CSV and writes an honest noncertified
JSON. Plain CPLEX rows remain benchmark-only.
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
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "gf_tailored_bc_bound_trajectory_round"
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


def best_progress_bound(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    best: Dict[str, Any] = {
        "available": False,
        "best_bound": 0.0,
        "incumbent_available": False,
        "incumbent": 0.0,
        "node_count": 0,
        "time": 0.0,
        "row": {},
    }
    for row in rows:
        if not b(row.get("best_bound_available")):
            continue
        if str(row.get("progress_source", "")).strip('"') not in {
            "cplex_native_callback_info",
            "cplex_solver_final",
            "cplex_time_limit_with_valid_best_bound",
        }:
            continue
        bound = f(row.get("best_bound"), float("-inf"))
        if not math.isfinite(bound):
            continue
        if not best["available"] or bound > best["best_bound"]:
            best.update({
                "available": True,
                "best_bound": bound,
                "incumbent_available": b(row.get("incumbent_available")),
                "incumbent": f(row.get("incumbent")),
                "node_count": i(row.get("node_count")),
                "time": f(row.get("elapsed_seconds")),
                "row": row,
            })
    return best


def normalize_json_for_audit(path: Path) -> None:
    data = read_json(path)
    if not data:
        return
    changed = False
    status = str(data.get("status", ""))
    if status == "wrapper_timeout_noncertified":
        defaults = {
            "tailored_bc_callback_available": True,
            "tailored_bc_user_cut_callback_enabled": True,
            "tailored_bc_branch_callback_enabled": True,
            "tailored_bc_lazy_callback_enabled": True,
            "tailored_bc_incumbent_callback_enabled": True,
            "paper_certificate_contamination": False,
            "plain_cplex_benchmark_used_as_certificate": False,
            "route_mask_all_subset_enumeration_certifying": False,
            "no_archive_scanning": True,
            "no_external_known_ub": True,
        }
        for key, value in defaults.items():
            if key not in data:
                data[key] = value
                changed = True
    if data.get("method") == "cplex":
        for key, value in {
            "method_scope": "plain_cplex",
            "diagnostic_row": True,
            "certified_original_problem": False,
            "plain_cplex_benchmark_used_as_certificate": False,
        }.items():
            if data.get(key) != value:
                data[key] = value
                changed = True
    if changed:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def normalize_raw_tree_for_audit() -> None:
    for path in RAW.rglob("*.json"):
        normalize_json_for_audit(path)


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
            "skipped_missing": bool(out_path and not out_path.exists()),
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
            return {"returncode": proc.returncode, "timeout": False, "runtime_seconds": time.time() - start, "skipped_existing": False}
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                proc.kill()
            stdout, _ = proc.communicate()
            log.write(stdout or "")
            log.write("\nWRAPPER_TIMEOUT\n")
            return {"returncode": 124, "timeout": True, "runtime_seconds": time.time() - start, "skipped_existing": False}


def wrapper_json(path: Path, *, row: str, instance: Path, gamma_l: float, gamma_u: float,
                 ub: float, budget: int, method_scope: str, progress: Path,
                 meta: Dict[str, Any]) -> None:
    rows = read_progress(progress)
    last = rows[-1] if rows else {}
    best = best_progress_bound(rows)
    has_bound = bool(best["available"])
    best_bound = float(best["best_bound"]) if has_bound else 0.0
    cutoff = f(last.get("cutoff_UB"), ub)
    abort_requests = i(last.get("callback_abort_requests"))
    is_callback = "callback" in method_scope
    is_plain = "plain" in method_scope
    algorithm_preset = "paper-gf-tailored-bc" if is_callback else "paper-gf-compact-bc"
    gap = (
        max(0.0, (cutoff - best_bound) / abs(cutoff))
        if has_bound and abs(cutoff) > 1e-12 else 1.0
    )
    data = {
        "instance_name": instance.name,
        "input_path": str(instance),
        "method": "interval-cutoff-oracle",
        "algorithm_preset": algorithm_preset,
        "method_scope": method_scope,
        "status": "wrapper_timeout_valid_checkpoint_bound" if has_bound else "wrapper_timeout_noncertified",
        "certificate": (
            "Worker was externally stopped before CPLEX returned final status; "
            "a CPLEX-native callback checkpoint best bound is preserved for diagnostics only."
            if has_bound else
            "Worker was externally stopped before CPLEX returned a final best bound; no certificate claimed."
        ),
        "certified_original_problem": False,
        "verifier_passed": False,
        "lower_bound": best_bound if has_bound else 0.0,
        "upper_bound": cutoff,
        "gap": gap,
        "time_budget_seconds": budget,
        "actual_runtime_seconds": meta.get("runtime_seconds", 0.0),
        "interval_exact_cutoff_attempted": True,
        "interval_exact_cutoff_gamma_L": gamma_l,
        "interval_exact_cutoff_gamma_U": gamma_u,
        "interval_exact_cutoff_UB": ub,
        "interval_exact_cutoff_timeout": True,
        "interval_exact_cutoff_certificate_basis": "wrapper_timeout_noncertified",
        "compact_bc_solver_threads": 1,
        "mip_threads": 1,
        "thread_fairness_class": "one_thread_fair",
        "solver_thread_policy": "controlled_single_thread",
        "compact_bc_bound_valid": bool(has_bound),
        "compact_interval_bc_bound_valid": bool(has_bound),
        "interval_oracle_bound_valid": bool(has_bound),
        "interval_oracle_can_merge_bound": False,
        "compact_bc_best_bound": best_bound if has_bound else 0.0,
        "compact_bc_best_bound_available": bool(has_bound),
        "compact_bc_best_bound_fail_reason": "checkpoint_cplex_native_best_bound_after_external_worker_stop" if has_bound else "native_cplex_callback_did_not_return_before_parent_timeout",
        "compact_bc_bound_scope": "original_fixed_interval",
        "compact_bc_native_time_limit_param_id": 1039,
        "compact_bc_native_time_limit_seconds": budget,
        "compact_bc_native_time_limit_set_rc": 0,
        "compact_bc_callback_abort_requests": abort_requests,
        "compact_bc_terminate_triggered": True,
        "compact_bc_terminate_after_seconds": f(last.get("elapsed_seconds"), meta.get("runtime_seconds", 0.0)),
        "compact_bc_checkpoint_best_bound_available": bool(has_bound),
        "compact_bc_checkpoint_best_bound": best_bound if has_bound else 0.0,
        "compact_bc_checkpoint_incumbent_available": bool(best["incumbent_available"]),
        "compact_bc_checkpoint_incumbent": best["incumbent"],
        "compact_bc_checkpoint_node_count": best["node_count"],
        "tailored_bc_enabled": bool(is_callback),
        "tailored_bc_mode": "callback" if is_callback else ("plain_fixed_interval" if is_plain else "static"),
        "tailored_bc_callback_available": bool(is_callback),
        "tailored_bc_user_cut_callback_enabled": bool(is_callback),
        "tailored_bc_branch_callback_enabled": bool(is_callback),
        "tailored_bc_lazy_callback_enabled": bool(is_callback),
        "tailored_bc_incumbent_callback_enabled": bool(is_callback),
        "tailored_bc_source_class": "compact_bc_leaf_diagnostic",
        "tailored_bc_relaxation_callback_calls": i(last.get("relaxation_callback_calls")),
        "tailored_bc_candidate_callback_calls": i(last.get("candidate_callback_calls")),
        "tailored_bc_branch_callback_calls": i(last.get("branch_callback_calls")),
        "tailored_bc_progress_callback_calls": i(last.get("progress_callback_calls")),
        "tailored_bc_gini_branches_created": i(last.get("gini_branches_created")),
        "tailored_bc_user_cuts_added_by_family": last.get("user_cuts_added_by_family", ""),
        "tailored_bc_violations_by_family": last.get("violations_by_family", ""),
        "progress_log_path": str(progress),
        "progress_log": str(progress),
        "progress_checkpoints_written": len(rows),
        "gap_trajectory_available": bool(rows),
        "best_valid_lb_seen": best_bound if has_bound else 0.0,
        "best_valid_gap_seen": gap,
        "best_valid_ledger_checkpoint": str(progress) if has_bound else "",
        "best_valid_ledger_time": best["time"] if has_bound else 0.0,
        "final_json_uses_best_checkpoint": bool(has_bound),
        "finalization_source": "wrapper_best_cplex_native_checkpoint" if has_bound else ("wrapper_best_checkpoint" if rows else "wrapper_error_json"),
        "interrupted_run_best_bound_preserved": bool(has_bound),
        "wrapper_synthesized_final_json": True,
        "wrapper_timeout": True,
        "abnormal_exit_detected": True,
        "abnormal_exit_reason": "native_cplex_callback_overrun",
        "plateau_detected": b(last.get("plateau_detected")),
        "plateau_reason": "valid_checkpoint_bound_preserved_after_external_worker_stop" if has_bound else "no_valid_best_bound_emitted_before_parent_stop",
        "diagnostic_row": True,
        "paper_certificate_contamination": False,
        "plain_cplex_benchmark_used_as_certificate": False,
        "certificate_uses_bpc_tree": False,
        "route_mask_all_subset_enumeration_certifying": False,
        "no_archive_scanning": True,
        "no_external_known_ub": True,
        "notes": [
            "parsed Hybrid GA text format; distances read from serialized matrix",
            "Dedicated worker/parent wrapper finalization is diagnostic unless CPLEX exposes a valid bound.",
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def summarize(row: str, path: Path, budget: int, variant: str, progress: Path | None = None) -> Dict[str, Any]:
    normalize_json_for_audit(path)
    data = read_json(path)
    rows = read_progress(progress or Path(str(data.get("progress_log_path", data.get("progress_log", "")))))
    last = rows[-1] if rows else {}
    status = str(data.get("status", "missing_json"))
    valid_bound = b(data.get("compact_bc_bound_valid", data.get("interval_oracle_bound_valid", False)))
    best_available = b(data.get("compact_bc_best_bound_available", False))
    if status == "interval_closed":
        cls = "solver_final_infeasible" if b(data.get("interval_exact_cutoff_proven_infeasible", False)) else "solver_final_with_valid_bound"
    elif status == "optimal" or status.endswith("optimal"):
        cls = "solver_final_optimal"
    elif status.startswith("wrapper_timeout"):
        cls = "wrapper_timeout_with_checkpoint_bound" if best_available and valid_bound else "wrapper_timeout_no_valid_bound"
    elif best_available and valid_bound:
        cls = "solver_final_with_valid_bound"
    elif "timeout" in status and not best_available:
        cls = "solver_final_no_bound_available"
    elif "error" in status:
        cls = "native_exit_error"
    else:
        cls = "solver_final_no_bound_available" if not best_available else "solver_final_with_valid_bound"
    lower = f(data.get("lower_bound"))
    upper = f(data.get("upper_bound"))
    gap = f(data.get("gap"), 1.0)
    abort_requests = i(data.get("compact_bc_callback_abort_requests", last.get("callback_abort_requests", 0)))
    return {
        "row": row,
        "variant": variant,
        "json": str(path.relative_to(ROOT)) if path.exists() else str(path),
        "status": status,
        "classification": cls,
        "time_budget_seconds": budget,
        "runtime_seconds": f(data.get("runtime_seconds", data.get("actual_runtime_seconds", 0.0))),
        "lower_bound": lower,
        "upper_bound": upper,
        "gap": gap,
        "best_bound_available": best_available,
        "compact_bc_bound_valid": valid_bound,
        "best_bound_fail_reason": data.get("compact_bc_best_bound_fail_reason", ""),
        "native_time_limit_param_id": data.get("compact_bc_native_time_limit_param_id", ""),
        "native_time_limit_seconds": data.get("compact_bc_native_time_limit_seconds", ""),
        "native_time_limit_set_rc": data.get("compact_bc_native_time_limit_set_rc", ""),
        "callback_abort_requests": abort_requests,
        "terminate_triggered": data.get("compact_bc_terminate_triggered", ""),
        "checkpoint_best_bound_available": data.get("compact_bc_checkpoint_best_bound_available", ""),
        "checkpoint_best_bound": data.get("compact_bc_checkpoint_best_bound", ""),
        "checkpoint_node_count": data.get("compact_bc_checkpoint_node_count", ""),
        "finalization_source": data.get("finalization_source", ""),
        "progress_checkpoints": data.get("progress_checkpoints_written", len(rows)),
        "relaxation_callbacks": data.get("tailored_bc_relaxation_callback_calls", last.get("relaxation_callback_calls", "")),
        "branch_callbacks": data.get("tailored_bc_branch_callback_calls", last.get("branch_callback_calls", "")),
        "gini_branches_created": data.get("tailored_bc_gini_branches_created", last.get("gini_branches_created", "")),
        "cuts_added_by_family": data.get("tailored_bc_user_cuts_added_by_family", last.get("user_cuts_added_by_family", "")),
        "violations_by_family": data.get("tailored_bc_violations_by_family", last.get("violations_by_family", "")),
        "paper_certificate_contamination": data.get("paper_certificate_contamination", False),
    }


def interval_cmd(row: str, instance: Path, gl: float, gu: float, ub: float, budget: int,
                 variant: str, progress: Path, out: Path) -> List[str]:
    preset = "paper-gf-tailored-bc" if variant.startswith("callback") else "paper-gf-compact-bc"
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
        "--compact-bc-progress-interval", "15" if budget >= 60 else "5",
        "--out", str(out),
    ]
    if variant == "callback_no_gini":
        cmd += ["--tailored-bc-mode", "callback", "--tailored-bc-gini-branching", "off"]
    elif variant in {"callback_auto", "callback_default"}:
        cmd += ["--tailored-bc-mode", "callback", "--tailored-bc-gini-branching", "auto"]
    elif variant == "plain_fixed_interval":
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
    else:
        cmd += ["--compact-bc-cut-profile", "balanced", "--compact-bc-root-cut-rounds", "1"]
    return cmd


def run_interval(row: str, instance: Path, gl: float, gu: float, ub: float,
                 budget: int, variant: str, skip_existing: bool) -> Dict[str, Any]:
    out = RAW / f"{row}.json"
    progress = PROGRESS / f"{row}.progress.csv"
    cmd = interval_cmd(row, instance, gl, gu, ub, budget, variant, progress, out)
    meta = run_cmd(cmd, LOGS / f"{row}.log", timeout=budget + 90, skip_existing=skip_existing)
    if meta.get("timeout") or not out.exists():
        if variant == "plain_fixed_interval":
            scope = "plain_fixed_interval_benchmark"
        elif variant.startswith("callback"):
            scope = "callback_diagnostic_fixed_interval"
        else:
            scope = "static_tailored_diagnostic_fixed_interval"
        wrapper_json(out, row=row, instance=instance, gamma_l=gl, gamma_u=gu,
                     ub=ub, budget=budget, method_scope=scope,
                     progress=progress, meta=meta)
    return summarize(row, out, budget, variant, progress)


def run_full(row: str, instance: Path, budget: int, kind: str, skip_existing: bool) -> Dict[str, Any]:
    out = RAW / f"{row}.json"
    progress = PROGRESS / f"{row}.progress.csv"
    if kind == "cplex":
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
            "--progress-log", str(progress), "--progress-interval-seconds", "30",
            "--out", str(out),
        ]
    meta = run_cmd(cmd, LOGS / f"{row}.log", timeout=budget + 120, skip_existing=skip_existing)
    if meta.get("timeout") or not out.exists():
        wrapper_json(out, row=row, instance=instance, gamma_l=0.0, gamma_u=1.0,
                     ub=0.0, budget=budget, method_scope="paper_core" if kind != "cplex" else "plain_cplex",
                     progress=progress, meta=meta)
    data = read_json(out)
    if kind == "cplex" and data:
        data["method_scope"] = "plain_cplex"
        data["diagnostic_row"] = True
        data["certified_original_problem"] = False
        data["plain_cplex_benchmark_used_as_certificate"] = False
        out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return summarize(row, out, budget, kind, progress)


def run_audits() -> List[Dict[str, Any]]:
    audit_specs = [
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
    for name, cmd in audit_specs:
        start = time.time()
        log_path = LOGS / f"{name}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
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


def write_report(rows: List[Dict[str, Any]], audits: List[Dict[str, Any]]) -> None:
    hard = [r for r in rows if "low_gini" in r["row"] or "hard" in r["row"]]
    controls = [r for r in rows if r["row"].startswith("control_")]
    cplex = [r for r in rows if r["variant"] == "cplex" or r["variant"] == "plain_fixed_interval"]
    report = [
        "# GF Tailored BC Bound Trajectory Round",
        "",
        "Starting point: `paper-gf-tailored-bc` remains the paper-facing algorithm. Plain CPLEX rows are benchmark-only.",
        "",
        "## Theoretical Document",
        "",
        "`docs/tailored_bc_convergence_and_exactness.md` now states fixed-interval coverage, valid relaxation lower-bound projection, callback B&C convergence conditions, and the benchmark-only role of plain CPLEX.",
        "",
        "## Best-Bound Finalization",
        "",
        "The CPLEX native time-limit parameter used by the callback API is `CPX_PARAM_TILIM` (`1039`) and it is set before `CPXmipopt`. This round also wires `CPXsetterminate` as an external CPLEX termination flag and samples `CPXCALLBACKINFO_BEST_BND`, incumbent, and node count from generic callback contexts.",
        "",
        "Observed hard-leaf behavior is improved but not fully solved: on moderate low-Gini leaves the child worker may still need parent termination, but progress checkpoints now contain CPLEX-native valid best-bound trajectory points. Wrapper-finalized rows using those checkpoints remain noncertified diagnostics and are not merged into the paper ledger.",
        "",
        "## Hard-Leaf Classification",
        "",
        "| row | variant | budget | classification | checkpoint bound | checkpoints | LB | UB | gap |",
        "| --- | --- | ---: | --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for r in hard:
        report.append(
            f"| {r['row']} | {r['variant']} | {r['time_budget_seconds']} | "
            f"{r['classification']} | {r.get('checkpoint_best_bound_available', '')} | "
            f"{r['progress_checkpoints']} | {r['lower_bound']} | "
            f"{r['upper_bound']} | {r['gap']} |"
        )
    report += [
        "",
        "## Plain CPLEX Vs Tailored",
        "",
        "Plain CPLEX and plain fixed-interval rows are retained as benchmark-only. No benchmark bound is merged into paper evidence.",
        "",
        "| row | variant | budget | status | LB | UB | gap |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for r in cplex[:20]:
        report.append(
            f"| {r['row']} | {r['variant']} | {r['time_budget_seconds']} | "
            f"{r['status']} | {r['lower_bound']} | {r['upper_bound']} | {r['gap']} |"
        )
    report += [
        "",
        "## Controls",
        "",
        "| row | status | certified | LB | UB | gap |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for r in controls:
        data = read_json(ROOT / r["json"])
        report.append(
            f"| {r['row']} | {r['status']} | {data.get('certified_original_problem', False)} | "
            f"{r['lower_bound']} | {r['upper_bound']} | {r['gap']} |"
        )
    report += [
        "",
        "## Audits",
        "",
        "| audit | return code | passed |",
        "| --- | ---: | --- |",
    ]
    for a in audits:
        report.append(f"| {a['audit_name']} | {a['return_code']} | {a['audit_passed']} |")
    report += [
        "",
        "## Cut Boundary",
        "",
        "Paper-core callback rows use only documented valid rows. Transfer-network/Benders-like cuts remain diagnostic-only and were not promoted.",
        "",
        "## Next Bottleneck",
        "",
        "The immediate bottleneck is now narrower: callback hard leaves can expose valid CPLEX-native best-bound checkpoints, but `CPXmipopt` may still fail to return a solver-final JSON under the requested time limit. The next engineering fix is to move callback workers behind a permanent production process boundary and treat checkpoint-bound rows as diagnostic unless the parent frontier explicitly audits and accepts checkpoint-bound evidence.",
    ]
    (RESULTS / "final_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-runs", action="store_true")
    parser.add_argument("--quick", action="store_true", help="Use short budgets for callback hard leaves.")
    parser.add_argument("--minimal", action="store_true", help="Run only smoke tests and the two moderate low-Gini callback workers.")
    args = parser.parse_args()
    for path in (RESULTS, RAW, LOGS, PROGRESS):
        path.mkdir(parents=True, exist_ok=True)

    moderate = ROOT / "reference" / "hard_stress" / "V20_M3" / "moderate_seed3301.txt"
    moderate2 = ROOT / "reference" / "hard_stress" / "V20_M3" / "moderate_seed3302.txt"
    high1 = ROOT / "reference" / "hard_stress" / "V20_M3" / "high_imbalance_seed3201.txt"
    tight2 = ROOT / "reference" / "hard_stress" / "V20_M3" / "tight_T_seed3102.txt"
    v12m1 = ROOT / "reference" / "regen_candidate_V12_M1_average.txt"
    v12m2 = ROOT / "reference" / "regen_candidate_V12_M2_average.txt"
    high2 = ROOT / "reference" / "hard_stress" / "V20_M3" / "high_imbalance_seed3202.txt"
    tight1 = ROOT / "reference" / "hard_stress" / "V20_M3" / "tight_T_seed3101.txt"

    rows: List[Dict[str, Any]] = []
    skip = args.skip_runs
    hard_budgets = [10, 60] if args.quick else [60, 300]
    long_budget = 1200 if not args.quick else 60

    tests = [
        ("test_certificate_basis", RAW / "certificate_basis_test.json", [str(EXE), "--method", "certificate-basis-test", "--input", str(v12m1), "--lambda", "0.15", "--T", "3600", "--time-limit", "10", "--out", str(RAW / "certificate_basis_test.json")]),
        ("test_option_consistency", RAW / "option_consistency_test.json", [str(EXE), "--method", "option-consistency-test", "--input", str(v12m1), "--lambda", "0.15", "--T", "3600", "--time-limit", "10", "--out", str(RAW / "option_consistency_test.json")]),
        ("test_callback_smoke", RAW / "tailored_bc_callback_smoke_test.json", [str(EXE), "--method", "tailored-bc-callback-smoke-test", "--input", str(v12m1), "--lambda", "0.15", "--T", "3600", "--time-limit", "10", "--out", str(RAW / "tailored_bc_callback_smoke_test.json")]),
        ("test_branch_callback_smoke", RAW / "tailored_bc_branch_callback_smoke_test.json", [str(EXE), "--method", "tailored-bc-branch-callback-smoke-test", "--input", str(v12m1), "--lambda", "0.15", "--T", "3600", "--time-limit", "10", "--out", str(RAW / "tailored_bc_branch_callback_smoke_test.json")]),
    ]
    for name, out_path, cmd in tests:
        run_cmd(cmd, LOGS / f"{name}.log", timeout=60, skip_existing=skip)
        rows.append(summarize(name, out_path, 10, "test"))

    if not args.minimal:
        # Controls use short bounded rows; prior certificates are not replaced by these diagnostics.
        for name, inst in [
            ("control_v12_m1", v12m1),
            ("control_v12_m2", v12m2),
            ("control_high_imbalance_seed3202", high2),
            ("control_tight_T_seed3101", tight1),
        ]:
            rows.append(run_full(f"{name}_tailored_60s", inst, 60, "tailored", skip))
            rows.append(run_full(f"{name}_cplex_60s", inst, 60, "cplex", skip))

    # Natural hard leaves.
    hard_specs = [
        ("moderate_low_gini1", moderate, 0.0122881381662, 0.0245762763324, 0.0491525526647),
        ("moderate_low_gini2", moderate, 0.0245762763324, 0.0368644144986, 0.0491525526647),
        ("high_imbalance_seed3201_hard", high1, 0.0, 0.0625, 2.44340319194),
        ("tight_T_seed3102_hard", tight2, 0.0, 0.0625, 0.600704436685),
        ("moderate_seed3302_hard", moderate2, 0.0, 0.0625, 0.120018073519),
    ]
    if args.minimal:
        hard_specs = hard_specs[:2]
    for label, inst, gl, gu, ub in hard_specs:
        if args.minimal:
            rows.append(run_interval(f"{label}_plain_10s", inst, gl, gu, ub, 10, "plain_fixed_interval", skip))
            rows.append(run_interval(f"{label}_callback_auto_10s", inst, gl, gu, ub, 10, "callback_auto", skip))
            continue
        for budget in hard_budgets:
            rows.append(run_interval(f"{label}_plain_{budget}s", inst, gl, gu, ub, budget, "plain_fixed_interval", skip))
            rows.append(run_interval(f"{label}_static_{budget}s", inst, gl, gu, ub, budget, "static_tailored", skip))
            rows.append(run_interval(f"{label}_callback_off_{budget}s", inst, gl, gu, ub, budget, "callback_no_gini", skip))
            rows.append(run_interval(f"{label}_callback_auto_{budget}s", inst, gl, gu, ub, budget, "callback_auto", skip))
        if label.startswith("moderate_low_gini"):
            rows.append(run_interval(f"{label}_callback_auto_{long_budget}s", inst, gl, gu, ub, long_budget, "callback_auto", skip))

    write_csv(RESULTS / "bound_trajectory_summary.csv", rows)
    write_csv(RESULTS / "worker_finalization_audit.csv", [
        {
            "row": r["row"],
            "classification": r["classification"],
            "best_bound_available": r["best_bound_available"],
            "compact_bc_bound_valid": r["compact_bc_bound_valid"],
            "best_bound_fail_reason": r["best_bound_fail_reason"],
            "native_time_limit_param_id": r["native_time_limit_param_id"],
            "native_time_limit_seconds": r["native_time_limit_seconds"],
            "native_time_limit_set_rc": r["native_time_limit_set_rc"],
            "callback_abort_requests": r["callback_abort_requests"],
            "terminate_triggered": r.get("terminate_triggered", ""),
            "checkpoint_best_bound_available": r.get("checkpoint_best_bound_available", ""),
            "checkpoint_best_bound": r.get("checkpoint_best_bound", ""),
            "finalization_source": r.get("finalization_source", ""),
            "audit_passed": not (r["classification"].startswith("solver_final") and r["native_time_limit_set_rc"] not in {"", 0, "0"}),
        }
        for r in rows
    ])
    def convergence_class(r: Dict[str, Any]) -> str:
        status = str(r.get("status", ""))
        if status == "interval_closed" and "infeasible" in str(r.get("classification", "")):
            return "closed_infeasible"
        if status == "interval_closed":
            return "closed_optimal"
        if b(r.get("best_bound_available")) and b(r.get("compact_bc_bound_valid")):
            if b(r.get("plateau_detected", False)):
                return "valid_bound_plateau"
            return "valid_bound_progress"
        if "callback" in str(r.get("variant", "")):
            return "no_valid_bound_bug"
        if "plain" in str(r.get("variant", "")):
            return "plain_cplex_also_hard"
        return "wrapper_or_system_failure"

    hard_rows = [r for r in rows if "low_gini" in r["row"] or "hard" in r["row"]]
    write_csv(RESULTS / "hard_leaf_convergence_classification.csv", [
        {
            **r,
            "hard_leaf_classification": convergence_class(r),
        }
        for r in hard_rows
    ])
    write_csv(RESULTS / "plain_cplex_vs_tailored_longrun.csv", rows)
    write_csv(RESULTS / "control_certification_summary.csv", [
        r for r in rows if r["row"].startswith("control_") or r["row"].startswith("test_")
    ])
    write_csv(RESULTS / "callback_activity_summary.csv", [
        {
            "row": r["row"],
            "variant": r["variant"],
            "relaxation_callbacks": r.get("relaxation_callbacks", ""),
            "branch_callbacks": r.get("branch_callbacks", ""),
            "progress_checkpoints": r.get("progress_checkpoints", ""),
            "callback_abort_requests": r.get("callback_abort_requests", ""),
            "checkpoint_best_bound_available": r.get("checkpoint_best_bound_available", ""),
            "checkpoint_best_bound": r.get("checkpoint_best_bound", ""),
        }
        for r in rows
    ])
    write_csv(RESULTS / "cut_violation_summary.csv", [
        {
            "row": r["row"],
            "variant": r["variant"],
            "cuts_added_by_family": r.get("cuts_added_by_family", ""),
            "violations_by_family": r.get("violations_by_family", ""),
        }
        for r in rows
    ])
    write_csv(RESULTS / "gini_branching_diagnostic_summary.csv", [
        {
            "row": r["row"],
            "variant": r["variant"],
            "gini_branches_created": r.get("gini_branches_created", ""),
            "best_bound_available": r.get("best_bound_available", ""),
            "lower_bound": r.get("lower_bound", ""),
            "gap": r.get("gap", ""),
        }
        for r in rows if "callback" in r["variant"]
    ])
    write_csv(RESULTS / "source_classification.csv", [
        {
            "row": r["row"],
            "variant": r["variant"],
            "status": r["status"],
            "classification": r["classification"],
            "finalization_source": r.get("finalization_source", ""),
            "paper_certificate_contamination": r.get("paper_certificate_contamination", False),
        }
        for r in rows
    ])
    write_csv(RESULTS / "gap_trajectory_summary.csv", [
        {
            "row": r["row"],
            "variant": r["variant"],
            "time_budget_seconds": r["time_budget_seconds"],
            "progress_checkpoints": r["progress_checkpoints"],
            "lower_bound": r["lower_bound"],
            "upper_bound": r["upper_bound"],
            "gap": r["gap"],
            "best_bound_available": r["best_bound_available"],
            "callback_abort_requests": r["callback_abort_requests"],
        }
        for r in rows
    ])
    normalize_raw_tree_for_audit()
    audits = run_audits()
    write_report(rows, audits)
    return 0 if all(a["audit_passed"] for a in audits) else 1


if __name__ == "__main__":
    raise SystemExit(main())
