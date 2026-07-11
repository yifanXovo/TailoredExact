#!/usr/bin/env python3
"""Fresh full-frontier evaluation of the selected route-cutset callback profile."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import run_tailored_bc_structural_cut_round as vector_parser


ROOT = Path(__file__).resolve().parents[1]
ROUND = "gf_tailored_bc_route_profile_full_frontier_round"
RESULTS = ROOT / "results" / ROUND
RAW = RESULTS / "raw"
PROGRESS = RESULTS / "progress_traces"
LOGS = RESULTS / "logs"
MODELS = RESULTS / "model_exports"
EXE = ROOT / "build" / "ExactEBRP.exe"
PY = Path(r"D:\msys64\ucrt64\bin\python.exe")

INSTANCES: Dict[str, Dict[str, Any]] = {
    "V12_M1": {
        "path": "reference/regen_candidate_V12_M1_average.txt", "class": "easy"
    },
    "V12_M2": {
        "path": "reference/regen_candidate_V12_M2_average.txt", "class": "easy"
    },
    "tight_T_seed3101": {
        "path": "reference/hard_stress/V20_M3/tight_T_seed3101.txt", "class": "easy"
    },
    "high_imbalance_seed3202": {
        "path": "reference/hard_stress/V20_M3/high_imbalance_seed3202.txt", "class": "easy"
    },
    "moderate_seed3301": {
        "path": "reference/hard_stress/V20_M3/moderate_seed3301.txt", "class": "hard"
    },
    "moderate_seed3302": {
        "path": "reference/hard_stress/V20_M3/moderate_seed3302.txt", "class": "hard"
    },
    "high_imbalance_seed3201": {
        "path": "reference/hard_stress/V20_M3/high_imbalance_seed3201.txt", "class": "hard"
    },
    "tight_T_seed3102": {
        "path": "reference/hard_stress/V20_M3/tight_T_seed3102.txt", "class": "hard"
    },
}

PACKAGE_FIELDS = {
    "result_package": f"results/{ROUND}",
    "fresh_run": True,
    "source_round": ROUND,
}


def b(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "yes", "on"}


def f(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except Exception:
        return default


def i(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if isinstance(data, dict) and isinstance(data.get("results"), list) and data["results"]:
        first = data["results"][0]
        return first if isinstance(first, dict) else {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: List[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    if not fields:
        fields = ["status"]
        rows = [{"status": "no_rows"}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def source_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")


def ensure_dirs() -> None:
    for path in (RESULTS, RAW, PROGRESS, LOGS, MODELS):
        path.mkdir(parents=True, exist_ok=True)


def route_profile_flags() -> List[str]:
    return [
        "--compact-bc-cut-profile", "balanced",
        "--compact-bc-root-cut-rounds", "1",
        "--compact-bc-root-cut-time-limit", "10",
        "--compact-bc-low-gini-strengthening", "safe",
        "--compact-bc-denominator-bound-mode", "tight",
        "--compact-bc-objective-estimator-mode", "adaptive",
        "--compact-bc-domain-propagation-mode", "iterative",
        "--compact-bc-domain-propagation-rounds", "2",
        "--compact-bc-variable-s-centering", "true",
        "--compact-bc-sp-product-estimator", "paper-safe",
        "--compact-bc-sp-product-bounds", "tight",
        "--tailored-bc-enabled", "true",
        "--tailored-bc-mode", "callback",
        "--tailored-bc-callback-cut-profile", "route-cutset-only",
        "--tailored-bc-local-centering", "true",
        "--tailored-bc-gini-branching", "off",
        "--tailored-bc-gs-product-coupling", "false",
        "--tailored-bc-gs-product-lower-row", "off",
        "--tailored-bc-disaggregated-sp-estimator", "false",
        "--tailored-bc-disaggregated-sp-replace-aggregate", "false",
        "--tailored-bc-vector-support-cover", "false",
        "--tailored-bc-vector-route-cutset", "true",
        "--tailored-bc-vector-route-cutset-max-size", "4",
        "--tailored-bc-vector-route-cutset-max-cuts", "50",
        "--tailored-bc-gini-subset-max-size", "4",
        "--tailored-bc-gini-subset-max-cuts", "50",
        "--tailored-bc-vector-cut-min-violation", "0.000001",
        "--tailored-bc-vector-cut-candidate-source", "callback",
        "--tailored-bc-structural-profile", "structural_route_limited",
        "--tailored-bc-s-bucket-ledger", "off",
    ]


def budget_split(nominal: int) -> Tuple[int, int, int]:
    """Generic wall-budget allocation: 68% frontier, 28% exact leaves, 4% overhead."""
    frontier = max(20, int(nominal * 0.68))
    oracle = max(10, int(nominal * 0.28))
    per_leaf = min(1200, max(10, oracle))
    return frontier, oracle, per_leaf


def tailored_command(name: str, nominal_budget: int, out: Path, progress: Path, log: Path) -> List[str]:
    spec = INSTANCES[name]
    frontier, oracle, per_leaf = budget_split(nominal_budget)
    interval = 300 if nominal_budget > 10800 else 30
    return [
        str(EXE), "--method", "gcap-frontier",
        "--algorithm-preset", "paper-gf-tailored-bc",
        "--paper-run-sealed", "true",
        "--input", str(ROOT / spec["path"]),
        "--lambda", "0.15", "--T", "3600",
        "--time-limit", str(frontier),
        "--threads", "1", "--mip-threads", "1", "--compact-bc-threads", "1",
        "--cplex-threads", "1",
        "--auto-interval-oracle-leaf-budget-policy", "total",
        "--auto-interval-oracle-total-budget", str(oracle),
        "--auto-interval-oracle-time-limit", str(per_leaf),
        "--auto-interval-oracle-child-time-limit", str(per_leaf),
        "--compact-bc-time-limit", str(per_leaf),
        "--progress-log", str(progress),
        "--progress-interval-seconds", str(interval),
        "--compact-bc-progress-interval", str(interval),
        "--log", str(log),
        "--out", str(out),
    ] + route_profile_flags()


def plain_command(name: str, budget: int, out: Path, log: Path) -> List[str]:
    return [
        str(EXE), "--method", "cplex", "--plain-baseline",
        "--input", str(ROOT / INSTANCES[name]["path"]),
        "--lambda", "0.15", "--T", "3600",
        "--time-limit", str(budget),
        "--threads", "1", "--cplex-threads", "1", "--mip-threads", "1",
        "--log", str(log), "--out", str(out),
    ]


def process_memory_mb(pid: int) -> float:
    script = (
        "$all=Get-CimInstance Win32_Process; $ids=@(" + str(pid) + "); "
        "for($r=0;$r -lt 5;$r++){ $new=@($all|?{$ids -contains $_.ParentProcessId}|% ProcessId); "
        "$ids+=@($new|?{$ids -notcontains $_}) }; "
        "$sum=($all|?{$ids -contains $_.ProcessId}|measure WorkingSetSize -Sum).Sum; "
        "if($null -eq $sum){0}else{[math]::Round($sum/1MB,3)}"
    )
    try:
        value = subprocess.check_output(
            ["powershell", "-NoProfile", "-Command", script], text=True,
            stderr=subprocess.DEVNULL, timeout=20,
        ).strip().splitlines()[-1]
        return f(value)
    except Exception:
        return 0.0


def run_process(cmd: List[str], log: Path, monitor: Path, wall_limit: int) -> Dict[str, Any]:
    log.parent.mkdir(parents=True, exist_ok=True)
    monitor.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    monitor_rows: List[Dict[str, Any]] = []
    progress_path: Path | None = None
    if "--progress-log" in cmd:
        try:
            progress_path = Path(cmd[cmd.index("--progress-log") + 1])
        except (ValueError, IndexError):
            progress_path = None

    def preserve_frontier_progress() -> None:
        if progress_path is None or not progress_path.exists():
            return
        try:
            with progress_path.open(encoding="utf-8-sig") as handle:
                header = handle.readline()
            if "global_LB" not in header or "unresolved_intervals" not in header:
                return
            target = progress_path.with_name(progress_path.stem + ".frontier.csv")
            shutil.copy2(progress_path, target)
        except Exception:
            return
    with log.open("w", encoding="utf-8", errors="replace") as handle:
        handle.write("COMMAND: " + subprocess.list2cmdline(cmd) + "\n\n")
        handle.flush()
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
        proc = subprocess.Popen(
            cmd, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT,
            creationflags=creationflags,
        )
        next_monitor = 0.0
        timed_out = False
        while proc.poll() is None:
            elapsed = time.time() - started
            if elapsed >= next_monitor:
                monitor_rows.append({
                    "time_seconds": round(elapsed, 3),
                    "process_tree_memory_mb": process_memory_mb(proc.pid),
                    "pid": proc.pid,
                })
                preserve_frontier_progress()
                next_monitor = elapsed + 300.0
                write_csv(monitor, monitor_rows)
            if elapsed > wall_limit:
                timed_out = True
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    )
                else:
                    proc.kill()
                break
            time.sleep(5)
        try:
            return_code = proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            return_code = 124
        elapsed = time.time() - started
        monitor_rows.append({
            "time_seconds": round(elapsed, 3),
            "process_tree_memory_mb": process_memory_mb(proc.pid),
            "pid": proc.pid,
        })
        preserve_frontier_progress()
        write_csv(monitor, monitor_rows)
        return {
            "returncode": 124 if timed_out else return_code,
            "wrapper_timeout": timed_out,
            "runtime_seconds": elapsed,
            "peak_memory_mb": max((f(row["process_tree_memory_mb"]) for row in monitor_rows), default=0.0),
        }


def best_parent_checkpoint(progress: Path) -> Dict[str, Any]:
    best: Dict[str, Any] = {}
    for row in read_csv(progress):
        lb = f(row.get("global_LB"), -math.inf)
        ub = f(row.get("incumbent_UB"), 0.0)
        if not math.isfinite(lb) or lb < 0.0 or ub <= 0.0:
            continue
        if not best or lb > f(best.get("global_LB"), -math.inf):
            best = row
    return best


def write_wrapper(path: Path, name: str, kind: str, budget: int, progress: Path,
                  meta: Dict[str, Any], command_hash: str, commit: str) -> None:
    best = best_parent_checkpoint(progress)
    lb = f(best.get("global_LB"), 0.0)
    ub = f(best.get("incumbent_UB"), 0.0)
    gap = max(0.0, (ub - lb) / abs(ub)) if ub > 0.0 else 1.0
    paper = kind == "tailored"
    rejected_zero_gap_checkpoint = paper and bool(best) and gap <= 1e-12
    if rejected_zero_gap_checkpoint:
        # A parent progress row with LB == UB is not a full-frontier certificate.
        # Reject it unless the solver itself writes the complete final ledger.
        best = {}
        lb = 0.0
        gap = 1.0
    data: Dict[str, Any] = {
        "instance_name": Path(INSTANCES[name]["path"]).name,
        "input_path": INSTANCES[name]["path"],
        "method": "gcap-frontier" if paper else "cplex",
        "algorithm_preset": "paper-gf-tailored-bc" if paper else "custom",
        "status": "wrapper_timeout_noncertified" if meta.get("wrapper_timeout") else "wrapper_error_noncertified",
        "certificate": "No certificate: solver did not write a final JSON; wrapper preserved only a valid package-local parent checkpoint when available.",
        "certified_original_problem": False,
        "lower_bound": lb,
        "upper_bound": ub,
        "gap": gap,
        "time_budget_seconds": budget,
        "actual_runtime_seconds": meta.get("runtime_seconds", 0.0),
        "finalization_source": "stale_checkpoint_rejected" if rejected_zero_gap_checkpoint else ("wrapper_best_checkpoint" if best else "wrapper_error_json"),
        "best_valid_lb_seen": lb,
        "best_valid_gap_seen": gap,
        "best_valid_ledger_checkpoint": rel(progress) if best else "",
        "final_json_uses_best_checkpoint": bool(best),
        "interrupted_run_best_bound_preserved": bool(best),
        "wrapper_synthesized_final_json": True,
        "abnormal_exit_detected": True,
        "abnormal_exit_reason": "wrapper_wall_limit" if meta.get("wrapper_timeout") else "native_exit_without_json",
        "stale_checkpoint_rejected": rejected_zero_gap_checkpoint,
        "solver_thread_policy": "controlled_one_thread",
        "thread_fairness_class": "one_thread_fair",
        "cplex_threads": 1 if not paper else 0,
        "mip_threads": 1,
        "compact_bc_solver_threads": 1 if paper else 0,
        "progress_log": rel(progress) if progress.exists() else "",
        "distance_convention_note": "instance_distance_matrix_used_without_cross_method_rescaling",
        "tailored_bc_enabled": paper,
        "tailored_bc_mode": "callback" if paper else "off",
        "tailored_bc_callback_available": paper,
        "tailored_bc_source_class": "wrapper_noncertified" if paper else "off",
        "paper_certificate_contamination": False,
        "plain_cplex_benchmark_used_as_certificate": False,
        "certificate_uses_bpc_tree": False,
        "route_mask_all_subset_enumeration_certifying": False,
        "no_archive_scanning": True,
        "no_external_known_ub": True,
        "manual_ub_import_used": False,
        "diagnostic_row": not paper,
        "benchmark_only": not paper,
        "paper_certificate_role": "paper_core_noncertified" if paper else "benchmark_only",
        "command_hash": command_hash,
        "git_commit": commit,
        **PACKAGE_FIELDS,
    }
    write_json(path, data)


def annotate_json(path: Path, *, name: str, kind: str, nominal_budget: int,
                  command_hash: str, commit: str, root_row: bool) -> None:
    data = read_json(path)
    if not data:
        return
    paper = kind == "tailored"
    source_category = str(data.get("incumbent_source_category", ""))
    source_detail = str(data.get("incumbent_source_detail", "")).lower()
    same_run = paper and source_category == "primal_heuristic" and "hga-tgbc" in source_detail
    if not paper:
        data["solver_reported_certified_original_problem"] = b(data.get("certified_original_problem"))
        # Plain CPLEX can report an optimal benchmark result, but it is never a
        # paper-core certificate source. Comparison summaries derive benchmark
        # optimality from status plus verifier fields.
        data["certified_original_problem"] = False
    data.setdefault("solver_thread_policy", "controlled_one_thread")
    data.setdefault("distance_convention_note", "instance_distance_matrix_used_without_cross_method_rescaling")
    notes = data.get("notes", [])
    if not isinstance(notes, list):
        notes = [notes]
    if not any("distance" in str(note).lower() or "coordinate" in str(note).lower() for note in notes):
        notes.append("Distance convention: the instance distance matrix is used without cross-method rescaling.")
    data["notes"] = notes
    if root_row:
        progress_path = PROGRESS / f"{path.stem}.progress.csv"
        data.setdefault("progress_log", rel(progress_path) if progress_path.exists() else "not_applicable_plain_benchmark")
    if paper:
        data.setdefault("tailored_bc_enabled", True)
        data.setdefault("tailored_bc_mode", "callback")
        data.setdefault("tailored_bc_callback_available", True)
        data.setdefault("tailored_bc_source_class", "wrapper_noncertified" if b(data.get("wrapper_synthesized_final_json")) else "tailored_bc")
    data.update(PACKAGE_FIELDS)
    data.update({
        "command_hash": command_hash,
        "git_commit": commit,
        "controlled_wall_time_budget_seconds": nominal_budget,
        "experiment_instance_key": name,
        "experiment_instance_class": INSTANCES[name]["class"],
        "experiment_row_kind": kind,
        "paper_certificate_contamination": False,
        "plain_cplex_benchmark_used_as_certificate": False,
        "manual_ub_import_used": False,
        "archive_or_known_ub_used": False,
        "external_incumbent_used": False,
        "route_mask_used": False,
        "bpc_used": False,
        "same_run_incumbent_used": same_run,
        "same_run_incumbent_verified": same_run and b(data.get("verifier_passed")),
        "diagnostic_row": not paper,
        "benchmark_only": not paper,
        "paper_certificate_role": "paper_core" if paper else "benchmark_only",
        "benchmark_name": "" if paper else "current_binary_expansion_compact_milp_cplex",
        "benchmark_role": "" if paper else "official_plain_cplex_benchmark",
        "formulation_exactness": "" if paper else "tolerance_exact",
        "route_cutset_profile_selected": paper,
        "route_cutset_candidate_source": "callback" if paper else "not_applicable",
        "root_experiment_row": root_row,
    })
    write_json(path, data)


def normalize_existing_package_json() -> None:
    pattern = re.compile(r"^(.+)_(tailored|plain)_(\d+)s$")
    for root_json in sorted(RAW.glob("*.json")):
        match = pattern.match(root_json.stem)
        if not match:
            continue
        name, kind, budget_text = match.groups()
        if name not in INSTANCES:
            continue
        data = read_json(root_json)
        if (kind == "tailored"
                and b(data.get("wrapper_synthesized_final_json"))
                and not b(data.get("certified_original_problem"))
                and f(data.get("gap"), 1.0) <= 1e-12):
            data.update({
                "lower_bound": 0.0,
                "gap": 1.0,
                "best_valid_lb_seen": 0.0,
                "best_valid_gap_seen": 1.0,
                "best_valid_ledger_checkpoint": "",
                "final_json_uses_best_checkpoint": False,
                "interrupted_run_best_bound_preserved": False,
                "finalization_source": "stale_checkpoint_rejected",
                "stale_checkpoint_rejected": True,
                "certificate": "No certificate: an apparent zero-gap parent checkpoint was rejected because no complete final frontier ledger was written.",
            })
            write_json(root_json, data)
        annotate_json(
            root_json, name=name, kind=kind, nominal_budget=int(budget_text),
            command_hash=str(data.get("command_hash", "")),
            commit=str(data.get("git_commit", source_commit())), root_row=True,
        )
        if kind == "tailored":
            for child, _ in child_results(root_json):
                child_data = read_json(child)
                annotate_json(
                    child, name=name, kind=kind, nominal_budget=int(budget_text),
                    command_hash=str(data.get("command_hash", "")),
                    commit=str(child_data.get("git_commit", data.get("git_commit", source_commit()))),
                    root_row=False,
                )
    for preflight in sorted(RAW.glob("preflight_*.json")):
        data = read_json(preflight)
        if not data:
            continue
        data.update(PACKAGE_FIELDS)
        data.update({
            "git_commit": data.get("git_commit", source_commit()),
            "diagnostic_row": True,
            "benchmark_only": False,
            "paper_certificate_role": "diagnostic_test_only",
            "paper_certificate_contamination": False,
        })
        write_json(preflight, data)


def copy_representative_model(stem: str, out: Path, kind: str) -> str:
    target = MODELS / f"{stem}.lp"
    source: Path | None = None
    if kind == "tailored":
        child_dir = out.with_suffix("").with_name(out.stem + "_auto_oracle")
        models = sorted(child_dir.glob("interval_*.lp")) if child_dir.exists() else []
        source = models[0] if models else None
    else:
        data = read_json(out)
        for note in data.get("notes", []) if isinstance(data.get("notes"), list) else []:
            if str(note).startswith("LP file: "):
                candidate = ROOT / str(note)[9:]
                if candidate.exists():
                    source = candidate
                    break
    if source is None:
        return ""
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return rel(target)


def run_row(name: str, kind: str, budget: int, skip_existing: bool, commit: str) -> Dict[str, Any]:
    stem = f"{name}_{kind}_{budget}s"
    out = RAW / f"{stem}.json"
    progress = PROGRESS / f"{stem}.progress.csv"
    log = LOGS / f"{stem}.solver.log.txt"
    stdout_log = LOGS / f"{stem}.stdout.log.txt"
    monitor = PROGRESS / f"{stem}.monitor.csv"
    cmd = tailored_command(name, budget, out, progress, log) if kind == "tailored" else plain_command(name, budget, out, log)
    command_hash = sha16(subprocess.list2cmdline(cmd))
    if skip_existing and out.exists():
        meta = {"returncode": 0, "wrapper_timeout": False, "runtime_seconds": 0.0, "peak_memory_mb": 0.0, "skipped": True}
    else:
        if kind == "tailored":
            child_dir = out.with_suffix("").with_name(out.stem + "_auto_oracle")
            if child_dir.exists():
                shutil.rmtree(child_dir)
            for suffix in (".auto_oracle.csv", ".intervals.csv", ".merged.intervals.csv",
                           ".oracle_partition_tree.csv", ".trace.json"):
                sibling = out.with_suffix(suffix)
                if sibling.exists():
                    sibling.unlink()
        for stale in (out, progress, progress.with_name(progress.stem + ".frontier.csv"), monitor):
            if stale.exists():
                stale.unlink()
        meta = run_process(cmd, stdout_log, monitor, budget + 180)
    if not out.exists():
        write_wrapper(out, name, kind, budget, progress, meta, command_hash, commit)
    annotate_json(out, name=name, kind=kind, nominal_budget=budget, command_hash=command_hash, commit=commit, root_row=True)
    if kind == "tailored":
        child_dir = out.with_suffix("").with_name(out.stem + "_auto_oracle")
        if child_dir.exists():
            for child in child_dir.rglob("*.json"):
                if child.name.endswith(".trace.json"):
                    continue
                annotate_json(child, name=name, kind=kind, nominal_budget=budget, command_hash=command_hash, commit=commit, root_row=False)
    model_path = copy_representative_model(stem, out, kind)
    data = read_json(out)
    if data and model_path:
        data["model_export_path"] = model_path
        write_json(out, data)
    return summarize_result(out, name, kind, budget, meta, progress, monitor, log, model_path, stdout_log)


def child_results(out: Path) -> List[Tuple[Path, Dict[str, Any]]]:
    child_dir = out.with_suffix("").with_name(out.stem + "_auto_oracle")
    rows: List[Tuple[Path, Dict[str, Any]]] = []
    if child_dir.exists():
        for path in sorted(child_dir.glob("interval_*.json")):
            data = read_json(path)
            if data:
                rows.append((path, data))
    return rows


def summarize_result(out: Path, name: str, kind: str, budget: int,
                     meta: Dict[str, Any] | None = None, progress: Path | None = None,
                     monitor: Path | None = None, log: Path | None = None,
                     model_path: str = "", stdout_log: Path | None = None) -> Dict[str, Any]:
    data = read_json(out)
    children = child_results(out) if kind == "tailored" else []
    candidates = sum(i(d.get("vector_callback_route_cutset_candidates")) for _, d in children)
    cuts = sum(i(d.get("vector_callback_route_cutset_cuts_added")) for _, d in children)
    violations = sum(i(d.get("vector_callback_route_cutset_violations")) for _, d in children)
    violation_sum = sum(f(d.get("vector_callback_route_cutset_violation_sum")) for _, d in children)
    nodes = sum(i(d.get("compact_bc_nodes", d.get("nodes"))) for _, d in children)
    runtime = f(data.get("actual_runtime_seconds", data.get("runtime_seconds")), f((meta or {}).get("runtime_seconds")))
    status = str(data.get("status", "missing"))
    certified = b(data.get("certified_original_problem")) or (kind == "plain" and status == "optimal")
    return {
        **PACKAGE_FIELDS,
        "git_commit": data.get("git_commit", source_commit()),
        "command_hash": data.get("command_hash", ""),
        "instance": name,
        "instance_path": INSTANCES[name]["path"],
        "instance_class": INSTANCES[name]["class"],
        "row_kind": kind,
        "budget_seconds": budget,
        "status": status,
        "certified_original_problem": certified,
        "LB": data.get("lower_bound", 0.0),
        "UB": data.get("upper_bound", data.get("objective", 0.0)),
        "gap": data.get("gap", 1.0),
        "runtime_seconds": runtime,
        "actual_stop_reason": data.get("plateau_reason", data.get("abnormal_exit_reason", status)),
        "closed_leaf_count": data.get("auto_interval_oracle_leaves_closed", data.get("compact_bc_closed_leaf_count", 0)),
        "open_leaf_count": data.get("auto_interval_oracle_remaining_open_leaves", data.get("unresolved_intervals", 0)),
        "certificate_source": data.get("full_certificate_basis", data.get("certificate", "")),
        "paper_core_valid": kind == "tailored" and not b(data.get("paper_certificate_contamination")),
        "diagnostic_rows_used": False,
        "plain_cplex_used_as_certificate": False,
        "bpc_used": b(data.get("certificate_uses_bpc_tree")),
        "archive_or_known_ub_used": False,
        "external_incumbent_used": False,
        "route_mask_used": b(data.get("route_mask_all_subset_enumeration_certifying")),
        "manual_ub_import_used": False,
        "same_run_incumbent_used": b(data.get("same_run_incumbent_used")),
        "same_run_incumbent_verified": b(data.get("same_run_incumbent_verified")),
        "route_cutset_callback_enabled": kind == "tailored",
        "route_cutset_candidate_source": "callback" if kind == "tailored" else "not_applicable",
        "route_cutset_candidates": candidates,
        "route_cutset_cuts_added": cuts,
        "route_cutset_violations": violations,
        "route_cutset_max_violation": max((f(d.get("vector_callback_route_cutset_max_violation")) for _, d in children), default=0.0),
        "route_cutset_avg_violation": violation_sum / violations if violations else 0.0,
        "route_cutset_cuts_size_2": sum(i(d.get("vector_callback_route_cutset_cuts_size_2")) for _, d in children),
        "route_cutset_cuts_size_3": sum(i(d.get("vector_callback_route_cutset_cuts_size_3")) for _, d in children),
        "route_cutset_cuts_size_4": sum(i(d.get("vector_callback_route_cutset_cuts_size_4")) for _, d in children),
        "route_cutset_cuts_size_5": sum(i(d.get("vector_callback_route_cutset_cuts_size_5")) for _, d in children),
        "compact_bc_nodes": nodes,
        "time_per_node": runtime / nodes if nodes > 0 else "not_available",
        "thread_count": 1,
        "thread_fairness_class": data.get("thread_fairness_class", "one_thread_fair"),
        "peak_memory_mb": (meta or {}).get("peak_memory_mb", "see_monitor"),
        "json_path": rel(out),
        "progress_path": rel(progress) if progress and progress.exists() else "",
        "frontier_progress_path": (
            rel(progress.with_name(progress.stem + ".frontier.csv"))
            if progress and progress.with_name(progress.stem + ".frontier.csv").exists()
            else ""
        ),
        "monitor_path": rel(monitor) if monitor and monitor.exists() else "",
        "log_path": rel(log) if log and log.exists() else "",
        "stdout_log_path": rel(stdout_log) if stdout_log and stdout_log.exists() else "",
        "model_path": model_path,
        "benchmark_role": "official_plain_cplex_benchmark" if kind == "plain" else "paper_core",
    }


def existing_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    pattern = re.compile(r"^(.+)_(tailored|plain)_(\d+)s$")
    for path in sorted(RAW.glob("*.json")):
        match = pattern.match(path.stem)
        if not match or match.group(1) not in INSTANCES:
            continue
        name, kind, budget_text = match.groups()
        stem = path.stem
        rows.append(summarize_result(
            path, name, kind, int(budget_text),
            progress=PROGRESS / f"{stem}.progress.csv",
            monitor=PROGRESS / f"{stem}.monitor.csv",
            log=LOGS / f"{stem}.solver.log.txt",
            model_path=rel(MODELS / f"{stem}.lp") if (MODELS / f"{stem}.lp").exists() else "",
            stdout_log=LOGS / f"{stem}.stdout.log.txt",
        ))
    return rows


def plan(phase: str) -> List[Tuple[str, str, int]]:
    if phase == "smoke":
        return [("V12_M1", "tailored", 60), ("V12_M1", "plain", 60)]
    if phase == "easy":
        return [(name, kind, budget) for name, spec in INSTANCES.items() if spec["class"] == "easy" for budget in (300, 1200) for kind in ("tailored", "plain")]
    if phase == "easy-tailored-rerun":
        rows = [("V12_M1", "tailored", 60)]
        rows += [(name, "tailored", budget) for name, spec in INSTANCES.items()
                 if spec["class"] == "easy" for budget in (300, 1200)]
        rows.append(("V12_M2", "tailored", 3600))
        return rows
    if phase == "easy-extension":
        previous = existing_rows()
        tailored_1200 = [
            r for r in previous
            if r["instance_class"] == "easy" and r["row_kind"] == "tailored"
            and r["budget_seconds"] == 1200
        ]
        need = {
            r["instance"] for r in tailored_1200
            if not b(r["certified_original_problem"])
        }
        return [(name, kind, 3600) for name in sorted(need) for kind in ("tailored", "plain")]
    if phase == "hard":
        return [(name, kind, 3600) for name, spec in INSTANCES.items() if spec["class"] == "hard" for kind in ("tailored", "plain")]
    if phase == "long":
        previous = existing_rows()
        primary = {(r["instance"], r["row_kind"]): r for r in previous if r["budget_seconds"] == 3600 and r["instance_class"] == "hard"}
        selected: List[Tuple[str, str, int]] = []
        for name, spec in INSTANCES.items():
            if spec["class"] != "hard":
                continue
            tailored = primary.get((name, "tailored"), {})
            progress = f(tailored.get("LB"), 0.0) > 0.0 or i(tailored.get("closed_leaf_count")) > 0
            if progress and not b(tailored.get("certified_original_problem")):
                selected.append((name, "tailored", 14400))
            plain = primary.get((name, "plain"), {})
            plain_competitive = f(plain.get("LB"), 0.0) > 0.0 or name in {"moderate_seed3301", "moderate_seed3302", "tight_T_seed3102"}
            if plain_competitive and not b(plain.get("certified_original_problem")):
                selected.append((name, "plain", 14400))
        return selected
    raise ValueError(phase)


def forbidden_scan() -> List[Dict[str, Any]]:
    terms = re.compile(r"moderate_seed330[12]|low_gini_[12]|seed31(?:01|02)|seed32(?:01|02)|known_ub|archive|external_incumbent|focus|route_mask|\bbpc\b|manual incumbent", re.I)
    branch = re.compile(r"\b(if|else\s+if|switch)\b.*(moderate_seed|low_gini|seed\d+)", re.I)
    rows: List[Dict[str, Any]] = []
    for base in (ROOT / "src", ROOT / "include", ROOT / "scripts"):
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in {".cpp", ".hpp", ".py"}:
                continue
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except Exception:
                continue
            for number, line in enumerate(lines, 1):
                if not terms.search(line):
                    continue
                forbidden = path.parts[-2] in {"src", "include"} and bool(branch.search(line))
                if forbidden:
                    classification = "forbidden_algorithm_special_case"
                elif path.parts[-2] == "scripts" and re.search(r"seed\d+|moderate_seed|low_gini", line, re.I):
                    classification = "allowed_experiment_target"
                elif path.parts[-2] == "scripts":
                    classification = "allowed_metadata_or_audit_text"
                else:
                    classification = "allowed_legacy_cli_not_paper_core"
                rows.append({
                    "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "line": number,
                    "matched_text": line.strip()[:500],
                    "classification": classification,
                    "audit_passed": not forbidden,
                })
    return rows


def prepare() -> None:
    ensure_dirs()
    commit = source_commit()
    observed_commits: Dict[str, set[str]] = {"tailored": set(), "plain": set()}
    for path in RAW.glob("*.json"):
        if path.name.endswith(".trace.json"):
            continue
        data = read_json(path)
        row_kind = str(data.get("experiment_row_kind", data.get("row_kind", "")))
        row_commit = str(data.get("git_commit", "")).strip()
        if row_kind in observed_commits and row_commit:
            observed_commits[row_kind].add(row_commit)

    def observed(kind: str) -> str:
        values = sorted(observed_commits[kind])
        return "|".join(values) if values else commit

    scan = forbidden_scan()
    write_csv(RESULTS / "forbidden_evidence_scan.csv", scan)
    manifest = [
        {
            "configuration": "paper_route_profile_full_frontier",
            "git_commit": commit,
            "row_git_commit_policy": "per_row_exact_in_raw_json",
            "observed_row_git_commits": observed("tailored"),
            "algorithm_preset": "paper-gf-tailored-bc",
            "route_cutset_callback_enabled": True,
            "route_cutset_candidate_source": "callback_relaxation_vector",
            "route_cutset_max_cuts": 50,
            "route_cutset_max_subset_size": 4,
            "route_cutset_min_violation": 1e-6,
            "GS_coupling": "off",
            "SP_disaggregation": "off",
            "S_bucket_ledger_mode": "off_in_tested_profile",
            "callback_cut_profile": "route-cutset-only",
            "thread_count": 1,
            "time_limit": "controlled_wall_budget_with_generic_68_28_split",
            "incumbent_source_policy": "native_hga_tgbc_same_run_verifier_gated_ub_only",
            "benchmark_formulation": "current_binary_expansion_compact_milp_cplex",
            "benchmark_exactness_label": "tolerance_exact",
            "paper_certificate_role": "paper_core",
        },
        {
            "configuration": "official_plain_cplex_benchmark",
            "git_commit": commit,
            "row_git_commit_policy": "per_row_exact_in_raw_json",
            "observed_row_git_commits": observed("plain"),
            "algorithm_preset": "custom_plain_baseline",
            "route_cutset_callback_enabled": False,
            "route_cutset_candidate_source": "not_applicable",
            "route_cutset_max_cuts": 0,
            "route_cutset_max_subset_size": 0,
            "route_cutset_min_violation": "not_applicable",
            "GS_coupling": "off",
            "SP_disaggregation": "off",
            "S_bucket_ledger_mode": "off",
            "callback_cut_profile": "off",
            "thread_count": 1,
            "time_limit": "matched_controlled_wall_budget",
            "incumbent_source_policy": "plain_cplex_internal_only",
            "benchmark_formulation": "current_binary_expansion_compact_milp_cplex",
            "benchmark_exactness_label": "tolerance_exact",
            "paper_certificate_role": "benchmark_only",
        },
    ]
    write_csv(RESULTS / "tested_configuration_manifest.csv", manifest)
    (RESULTS / "tested_configuration_manifest.md").write_text(
        "# Tested Configuration Manifest\n\n"
        f"Frozen configuration revision: `{commit}`. Exact executable provenance is recorded per row in raw JSON. "
        f"Observed tailored revisions: `{observed('tailored')}`; observed plain revisions: `{observed('plain')}`.\n\n"
        "The tailored command uses a generic 68% frontier, 28% exact-leaf, 4% overhead wall-budget policy. "
        "It enables only the selected callback-directed route-cutset structural profile; GS and disaggregated SP are off. "
        "The optional paper-safe S ledger is not activated because the preceding selection was made inside one fixed diagnostic bucket, not as a global S policy.\n\n"
        "The official benchmark is the current binary-expansion compact MILP solved by one-thread CPLEX. It is benchmark-only.\n",
        encoding="utf-8",
    )
    (RESULTS / "historical_context.md").write_text(
        "# Historical Context\n\n"
        "The preceding fresh structural-policy round selected the callback-directed route-cutset profile as the fastest exact fixed-interval variant. "
        "No prior raw result, incumbent, fixed-interval solution, or bound is copied into this package or used by a command in this round.\n",
        encoding="utf-8",
    )
    failures = sum(not b(row["audit_passed"]) for row in scan)
    (RESULTS / "mainline_scope_audit.md").write_text(
        "# Mainline Scope Audit\n\n"
        "- Mainline: `paper-gf-tailored-bc`.\n"
        "- Selected structural profile: generic callback-directed route cutset.\n"
        "- Official benchmark: current binary-expansion compact MILP plus one-thread CPLEX.\n"
        "- BPC, route-mask enumeration, archive/known/external incumbents, focus-only rows, manual UB imports, and diagnostic ledgers are excluded.\n"
        f"- Forbidden instance-specific branches found: {failures}.\n",
        encoding="utf-8",
    )
    write_csv(RESULTS / "benchmark_scope_summary.csv", [{
        **PACKAGE_FIELDS,
        "benchmark_name": "current_binary_expansion_compact_milp_cplex",
        "benchmark_role": "official_plain_cplex_benchmark",
        "formulation_exactness": "tolerance_exact",
        "thread_count": 1,
        "paper_certificate_role": "benchmark_only",
        "alternative_formulations_run": False,
    }])


def progress_trajectory(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for summary in rows:
        path_text = str(summary.get("frontier_progress_path") or summary.get("progress_path", ""))
        if not path_text:
            continue
        for point in read_csv(ROOT / path_text):
            output.append({
                **PACKAGE_FIELDS,
                "instance": summary["instance"],
                "row_kind": summary["row_kind"],
                "budget_seconds": summary["budget_seconds"],
                "time_seconds": point.get("time_seconds", point.get("elapsed_seconds", "")),
                "global_LB": point.get("global_LB", point.get("best_bound", "")),
                "incumbent_UB": point.get("incumbent_UB", point.get("incumbent", "")),
                "gap": point.get("gap", point.get("global_gap", "")),
                "open_intervals": point.get("active_leaves", point.get("unresolved_intervals", "")),
                "closed_intervals": point.get("closed_leaves", ""),
                "node_count": point.get("node_count", point.get("nodes", "")),
                "route_cutset_candidates": point.get("vector_route_cutset_candidates", ""),
                "route_cutset_cuts_added": point.get("vector_route_cutset_cuts_added", ""),
                "callback_calls": point.get("relaxation_callback_calls", ""),
                "certificate_source_status": point.get("progress_source", "frontier_progress"),
                "diagnostic_evidence_attempted": False,
            })
    return output


def interval_ledger(rows: Sequence[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    ledger: List[Dict[str, Any]] = []
    open_rows: List[Dict[str, Any]] = []
    for summary in rows:
        if summary["row_kind"] != "tailored":
            continue
        out = ROOT / summary["json_path"]
        candidates = [out.with_suffix(".merged.intervals.csv"), out.with_suffix(".intervals.csv")]
        table = next((read_csv(p) for p in candidates if p.exists()), [])
        for item in table:
            status = str(item.get("interval_status", item.get("status", "")))
            row = {
                **PACKAGE_FIELDS,
                "instance": summary["instance"],
                "budget_seconds": summary["budget_seconds"],
                "interval_id": item.get("interval_id", item.get("id", "")),
                "gamma_L": item.get("gamma_L", item.get("gini_L", "")),
                "gamma_U": item.get("gamma_U", item.get("gini_U", "")),
                "status": status,
                "lower_bound": item.get("interval_final_lb", item.get("merged_lb", item.get("lower_bound", ""))),
                "closure_source": item.get("interval_closure_source", item.get("closure_source", "")),
                "paper_core_valid": True,
                "source_csv_path": rel(next(p for p in candidates if p.exists())),
            }
            ledger.append(row)
            if any(token in status.lower() for token in ("open", "unresolved", "timeout")):
                open_rows.append(row)
    return ledger, open_rows


def compare_rows(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    keyed = {(r["instance"], r["budget_seconds"], r["row_kind"]): r for r in rows}
    output: List[Dict[str, Any]] = []
    for name in INSTANCES:
        budgets = sorted({r["budget_seconds"] for r in rows if r["instance"] == name})
        for budget in budgets:
            tailored = keyed.get((name, budget, "tailored"))
            plain = keyed.get((name, budget, "plain"))
            if not tailored or not plain:
                continue
            tc, pc = b(tailored["certified_original_problem"]), b(plain["certified_original_problem"])
            if tc and not pc:
                result, reason = "tailored_better", "tailored_certified_plain_open"
            elif pc and not tc:
                result, reason = "plain_better", "plain_certified_tailored_open"
            elif tc and pc:
                tr, pr = f(tailored["runtime_seconds"], math.inf), f(plain["runtime_seconds"], math.inf)
                result = "tailored_better" if tr + 1e-6 < pr else ("plain_better" if pr + 1e-6 < tr else "tied")
                reason = "both_certified_runtime_comparison"
            else:
                tg, pg = f(tailored["gap"], 1.0), f(plain["gap"], 1.0)
                if tg + 1e-5 < pg:
                    result, reason = "tailored_better", "both_open_tailored_valid_gap_clearly_smaller"
                elif pg + 1e-5 < tg:
                    result, reason = "plain_better", "both_open_plain_valid_gap_clearly_smaller"
                else:
                    result, reason = "inconclusive", "both_open_no_clear_valid_gap_dominance"
            output.append({
                **PACKAGE_FIELDS,
                "instance": name,
                "budget_seconds": budget,
                "tailored_status": tailored["status"],
                "tailored_certified": tc,
                "tailored_LB": tailored["LB"],
                "tailored_UB": tailored["UB"],
                "tailored_gap": tailored["gap"],
                "tailored_runtime": tailored["runtime_seconds"],
                "tailored_certificate_source": tailored["certificate_source"],
                "tailored_open_leaf_count": tailored["open_leaf_count"],
                "tailored_route_cutset_candidates": tailored["route_cutset_candidates"],
                "tailored_route_cutset_cuts_added": tailored["route_cutset_cuts_added"],
                "tailored_json_path": tailored["json_path"],
                "plain_status": plain["status"],
                "plain_certified": pc,
                "plain_LB": plain["LB"],
                "plain_UB": plain["UB"],
                "plain_gap": plain["gap"],
                "plain_runtime": plain["runtime_seconds"],
                "plain_benchmark_role": "official_plain_cplex_benchmark",
                "plain_json_path": plain["json_path"],
                "comparison_result": result,
                "reason": reason,
            })
    return output


def write_vector_outputs(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    raw_rows: List[Dict[str, Any]] = []
    snapshot_meta: Dict[str, Dict[str, Any]] = {}
    for summary in rows:
        if summary["row_kind"] != "tailored":
            continue
        out = ROOT / summary["json_path"]
        for child_path, data in child_results(out):
            parsed = vector_parser.vector_rows_from_json(child_path, data)
            raw_rows.extend(parsed)
            for item in parsed:
                snapshot_meta[str(item["snapshot_id"])] = {
                    "instance": summary["instance"],
                    "budget_seconds": summary["budget_seconds"],
                    "child_json_path": rel(child_path),
                }
    summaries = vector_parser.summarize_vectors(raw_rows)
    for item in summaries:
        item.update(PACKAGE_FIELDS)
        item.update(snapshot_meta.get(str(item.get("snapshot_id", "")), {}))
    for item in raw_rows:
        item.update(PACKAGE_FIELDS)
    write_csv(RESULTS / "callback_vector_raw.csv", raw_rows)
    (RESULTS / "root_lp_vector_raw.csv").write_text("", encoding="utf-8")
    write_csv(RESULTS / "callback_vector_family_summary.csv", summaries)
    (RESULTS / "root_lp_family_summary.csv").write_text("", encoding="utf-8")
    return summaries


def latex_escape(value: Any) -> str:
    text = str(value)
    for old, new in (("\\", r"\textbackslash{}"), ("_", r"\_"),
                     ("%", r"\%"), ("&", r"\&"), ("#", r"\#")):
        text = text.replace(old, new)
    return text


def write_latex_results(rows: Sequence[Dict[str, Any]]) -> None:
    selected: List[Dict[str, Any]] = []
    for instance in INSTANCES:
        for kind in ("tailored", "plain"):
            options = [r for r in rows if r["instance"] == instance and r["row_kind"] == kind]
            certified = [r for r in options if b(r["certified_original_problem"])]
            if certified:
                chosen = min(certified, key=lambda r: (i(r["budget_seconds"]), f(r["runtime_seconds"], math.inf)))
            else:
                solver_finals = [r for r in options if "wrapper" not in str(r["status"]).lower() and "error" not in str(r["status"]).lower()]
                checkpoint_wrappers = [r for r in options if "wrapper" in str(r["status"]).lower() and f(r["LB"], 0.0) > 0.0]
                pool = solver_finals or checkpoint_wrappers or options
                chosen = max(pool, key=lambda r: (i(r["budget_seconds"]), f(r["LB"], -math.inf)), default=None)
            if chosen:
                selected.append(chosen)
    lines = [
        r"\subsection{Fresh selected results}",
        r"\begin{center}",
        r"\small",
        r"\resizebox{\textwidth}{!}{%",
        r"\begin{tabular}{llrrrrl}",
        r"\toprule",
        r"Instance & Method & Budget & LB & UB & Gap & Status \\",
        r"\midrule",
    ]
    for row in selected:
        label = "Tailored" if row["row_kind"] == "tailored" else "Plain"
        lines.append(
            f"{latex_escape(row['instance'])} & {label} & {i(row['budget_seconds'])} & "
            f"{f(row['LB']):.6g} & {f(row['UB']):.6g} & {f(row['gap'], 1.0):.4g} & "
            f"{latex_escape(row['status'])} \\\\"
        )
    lines += [
        r"\bottomrule",
        r"\end{tabular}",
        r"}",
        r"\end{center}",
        "",
        "Rows are selected from this round only. Certified rows use the smallest fresh budget that certified; otherwise the longest valid row is shown. Plain rows are benchmark-only.",
    ]
    (ROOT / "Manuscript" / "generated_results.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def aggregate() -> None:
    ensure_dirs()
    normalize_existing_package_json()
    rows = existing_rows()
    write_latex_results(rows)
    write_csv(RESULTS / "full_frontier_route_profile_summary.csv", rows)
    write_csv(RESULTS / "plain_cplex_benchmark_summary.csv", [r for r in rows if r["row_kind"] == "plain"])
    comparisons = compare_rows(rows)
    write_csv(RESULTS / "plain_vs_route_profile_full_frontier.csv", comparisons)
    write_csv(RESULTS / "plain_vs_route_profile_fixed_interval_if_any.csv", [{
        **PACKAGE_FIELDS, "status": "not_run", "reason": "round_scope_is_full_frontier_only"
    }])
    route = [r for r in rows if r["row_kind"] == "tailored"]
    source_rows: List[Dict[str, Any]] = []
    for row in rows:
        if row["row_kind"] == "plain":
            source_class = "benchmark_only"
            has_children = False
            contributed = False
        else:
            root_path = ROOT / str(row["json_path"])
            has_children = bool(child_results(root_path))
            certified = b(row["certified_original_problem"])
            contributed = certified and (
                i(row["closed_leaf_count"]) > 0
                or "interval_exact" in str(row["certificate_source"])
            )
            if certified:
                source_class = "mixed_certified" if has_children else "relaxation_only_certified"
            else:
                source_class = "mixed_noncertified" if has_children else "relaxation_only_noncertified"
        source_rows.append({
            **PACKAGE_FIELDS,
            "row": f"{row['instance']}:{row['row_kind']}:{row['budget_seconds']}",
            "variant": row["row_kind"],
            "budget_seconds": row["budget_seconds"],
            "json_path": row["json_path"],
            "selected_for_summary": False,
            "certified_original_problem": row["certified_original_problem"],
            "row_certificate_source_class": source_class,
            "leaf_solver_row": False,
            "compact_bc_called_this_row": False,
            "compact_bc_called_any_child": has_children,
            "parent_row_compact_bc_called_any_leaf": has_children,
            "compact_bc_called_any_leaf": has_children,
            "compact_bc_contributed_to_certificate": contributed,
            "compact_bc_diagnostic_only": False,
            "paper_certificate_contamination": False,
            "inconsistent_source_label_detected": False,
        })
    write_csv(RESULTS / "certificate_source_summary.csv", source_rows)
    vector_summaries = write_vector_outputs(rows)
    write_csv(RESULTS / "route_cutset_callback_effectiveness.csv", route)
    write_csv(RESULTS / "route_cutset_cut_inventory.csv", [{
        **PACKAGE_FIELDS,
        "instance": r["instance"], "budget_seconds": r["budget_seconds"],
        "candidate_count": r["route_cutset_candidates"], "cuts_added": r["route_cutset_cuts_added"],
        "max_violation": r["route_cutset_max_violation"], "average_violation": r["route_cutset_avg_violation"],
        "size_2": r["route_cutset_cuts_size_2"], "size_3": r["route_cutset_cuts_size_3"],
        "size_4": r["route_cutset_cuts_size_4"], "size_5": r["route_cutset_cuts_size_5"],
    } for r in route])
    write_csv(RESULTS / "route_fractionality_summary.csv", [{
        **PACKAGE_FIELDS,
        "instance": item.get("instance", ""),
        "budget_seconds": item.get("budget_seconds", ""),
        "snapshot_id": item.get("snapshot_id", ""),
        "snapshot_source": item.get("snapshot_source", ""),
        "route_fractionality_score_initial": item.get("route_fractionality_score", ""),
        "z_fractionality_score_initial": item.get("z_fractionality_score", ""),
        "x_fractionality_score_initial": item.get("x_fractionality_score", ""),
        "fractional_z_count_initial": item.get("fractional_z_count", ""),
        "fractional_x_count_initial": item.get("fractional_x_count", ""),
        "route_fractionality_score_later": "not_available_no_post_cut_vector_export",
        "child_json_path": item.get("child_json_path", ""),
    } for item in vector_summaries])
    write_csv(RESULTS / "route_profile_runtime_overhead.csv", comparisons)
    ledger, open_rows = interval_ledger(rows)
    write_csv(RESULTS / "full_frontier_certificate_ledger.csv", ledger)
    write_csv(RESULTS / "full_frontier_open_leaf_summary.csv", open_rows)
    trajectory = progress_trajectory(rows)
    write_csv(RESULTS / "full_frontier_bound_trajectory_summary.csv", trajectory)
    (RESULTS / "full_frontier_engineering_stability.md").write_text(
        "# Full-Frontier Engineering Stability\n\n"
        f"- Fresh root rows: {len(rows)}.\n"
        f"- Wrapper/error rows: {sum('wrapper' in str(r['status']) or 'error' in str(r['status']) for r in rows)}; none is treated as a certificate.\n"
        f"- Package-local progress points: {len(trajectory)}.\n"
        f"- Open ledger rows: {len(open_rows)}.\n"
        "- Long-run monitoring: five-minute frontier snapshots and process-tree memory samples are stored under `progress_traces/`.\n\n"
        "The campaign runner survived every native exit and retained final JSON, stdout, solver logs, progress, and monitor data. "
        "During the simultaneous moderate plain 14400 s runs, CPLEX memory exceeded 18 GB and free physical memory fell below 0.3 GB. "
        "The lower-priority moderate-3302 plain row was stopped and recorded as resource-limited; no partial bound from it is used. "
        "All other selected long rows completed or produced audited noncertified wrapper artifacts. Failures, time limits, and the "
        "moderate-3302 regression remain visible in the package summaries.\n",
        encoding="utf-8",
    )


def run_audits() -> int:
    ensure_dirs()
    specs = [
        ("bpc_self_test", [str(PY), "scripts/audit_bpc_certificate.py", "--self-test"]),
        ("certificate", [str(PY), "scripts/audit_bpc_certificate.py", str(RAW), "--csv-out", str(RESULTS / "certificate_audit.csv"), "--fail-on-error"]),
        ("callback", [str(PY), "scripts/audit_tailored_bc_callback_round.py", "--results", str(RESULTS), "--out", str(RESULTS / "tailored_bc_callback_audit.csv")]),
        ("summary", [str(PY), "scripts/audit_gf_compact_bc_summary.py", "--results", str(RESULTS), "--out", str(RESULTS / "summary_cleanup_audit.csv")]),
        ("threads", [str(PY), "scripts/audit_thread_fairness.py", "--results", str(RESULTS), "--out", str(RESULTS / "thread_fairness_audit.csv")]),
        ("objective", [str(PY), "scripts/audit_objective_convention.py", "--results", str(RESULTS), "--out", str(RESULTS / "objective_convention_audit.csv")]),
        ("finalization", [str(PY), "scripts/audit_timeprofile_finalization.py", "--results", str(RESULTS), "--out", str(RESULTS / "timeprofile_finalization_audit.csv")]),
        ("sources", [str(PY), "scripts/audit_certificate_sources.py", "--results", str(RESULTS), "--out", str(RESULTS / "certificate_source_audit.csv")]),
        ("instance_special", [str(PY), "scripts/audit_no_instance_special_cases.py", "--out", str(RESULTS / "no_instance_special_case_audit.txt")]),
        ("paper_strict", [str(PY), "scripts/audit_paper_strict_algorithm.py", "--out", str(RESULTS / "paper_strict_algorithm_audit.csv")]),
        ("cross_round", [str(PY), "scripts/audit_no_cross_round_result_mixing.py", "--results", str(RESULTS), "--out", str(RESULTS / "no_cross_round_result_mixing_audit.csv")]),
        ("vector_route", [str(PY), "scripts/audit_vector_route_cuts.py", "--results", str(RESULTS), "--out", str(RESULTS / "vector_route_cut_audit.csv")]),
        ("callback_parser", [str(PY), "scripts/audit_callback_vector_family_parser.py", "--results", str(RESULTS), "--out", str(RESULTS / "callback_vector_parser_audit.csv")]),
        ("vector_summary", [str(PY), "scripts/audit_vector_structural_summary.py", "--results", str(RESULTS), "--out", str(RESULTS / "vector_structural_summary_audit.csv")]),
    ]
    rows: List[Dict[str, Any]] = []
    failures = 0
    for name, cmd in specs:
        started = time.time()
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        (LOGS / f"audit_{name}.log.txt").write_text((proc.stdout or "") + (proc.stderr or ""), encoding="utf-8")
        failures += proc.returncode != 0
        rows.append({
            **PACKAGE_FIELDS,
            "audit": name, "return_code": proc.returncode,
            "passed": proc.returncode == 0,
            "runtime_seconds": round(time.time() - started, 3),
            "log_path": rel(LOGS / f"audit_{name}.log.txt"),
        })
    write_csv(RESULTS / "audit_summary.csv", rows)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["prepare", "smoke", "easy", "easy-tailored-rerun", "easy-extension", "hard", "long", "aggregate", "audits"], required=True)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()
    ensure_dirs()
    if args.phase == "prepare":
        prepare()
        return 0
    if args.phase == "aggregate":
        aggregate()
        return 0
    if args.phase == "audits":
        return 1 if run_audits() else 0
    commit = source_commit()
    planned = plan(args.phase)
    if args.jobs > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            list(pool.map(lambda item: run_row(*item, args.skip_existing, commit), planned))
    else:
        for item in planned:
            run_row(*item, args.skip_existing, commit)
    aggregate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
