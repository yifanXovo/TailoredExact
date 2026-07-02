#!/usr/bin/env python3
"""Run and summarize the GF compact-BC time-profile round.

The runner keeps paper compact-BC rows and plain CPLEX benchmark rows in
separate namespaces.  If a process exits without JSON, it writes an honest
noncertified wrapper artifact so audits and summaries still account for the row.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


ROOT = Path("results/gf_compact_bc_timeprofile_round")
RAW = ROOT / "raw"
PROGRESS = ROOT / "progress_traces"
PY = Path(r"D:\msys64\ucrt64\bin\python.exe")
EXE = Path("build/ExactEBRP.exe")

INSTANCES: Dict[str, str] = {
    "V12_M1": "reference/regen_candidate_V12_M1_average.txt",
    "V12_M2": "reference/regen_candidate_V12_M2_average.txt",
    "high_imbalance_seed3201": "reference/hard_stress/V20_M3/high_imbalance_seed3201.txt",
    "high_imbalance_seed3202": "reference/hard_stress/V20_M3/high_imbalance_seed3202.txt",
    "tight_T_seed3101": "reference/hard_stress/V20_M3/tight_T_seed3101.txt",
    "tight_T_seed3102": "reference/hard_stress/V20_M3/tight_T_seed3102.txt",
    "moderate_seed3301": "reference/hard_stress/V20_M3/moderate_seed3301.txt",
    "moderate_seed3302": "reference/hard_stress/V20_M3/moderate_seed3302.txt",
}

LARGE_INSTANCES: Dict[str, str] = {
    "V50_M3_moderate": "reference/large_diagnostics/V50_M3_moderate_seed5101.txt",
    "V50_M3_high_imbalance": "reference/large_diagnostics/V50_M3_high_imbalance_seed5201.txt",
    "V100_M5_moderate": "reference/large_diagnostics/V100_M5_moderate_seed6101.txt",
    "V100_M5_high_imbalance": "reference/large_diagnostics/V100_M5_high_imbalance_seed6201.txt",
}


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if isinstance(data, dict) and isinstance(data.get("results"), list) and data["results"]:
        item = data["results"][0]
        return item if isinstance(item, dict) else {}
    return data if isinstance(data, dict) else {}


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


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


def wrapper_json(
    row: str,
    instance_path: Path,
    kind: str,
    budget: int,
    out_path: Path,
    progress_path: Path,
    return_code: int | None,
    runtime: float,
    reason: str,
) -> None:
    last_progress: Dict[str, str] = {}
    if progress_path.exists():
        try:
            with progress_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            if rows:
                last_progress = rows[-1]
        except Exception:
            last_progress = {}
    def pf(key: str, default: float = 0.0) -> float:
        try:
            value = float(last_progress.get(key, ""))
            return value if math.isfinite(value) else default
        except Exception:
            return default
    latest_ub = pf("incumbent_UB", 0.0)
    latest_lb = pf("global_LB", 0.0)
    latest_gap = pf("gap", 1.0 if latest_ub <= 0.0 else max(0.0, (latest_ub - latest_lb) / abs(latest_ub)))
    latest_unresolved = int(pf("unresolved_intervals", 1 if kind != "cplex" else 0))
    method = "cplex" if kind == "cplex" else "gcap-frontier"
    preset = "" if kind == "cplex" else "paper-gf-compact-bc"
    payload = {
        "instance_name": row,
        "input_path": str(instance_path),
        "instance_hash": file_hash(instance_path) if instance_path.exists() else "",
        "method": method,
        "method_scope": "plain_cplex" if kind == "cplex" else "original_compact",
        "algorithm_preset": preset,
        "status": "interrupted_noncertified",
        "certificate": f"wrapper noncertified artifact: {reason}",
        "certified_original_problem": False,
        "solves_original_objective": True,
        "verifier_passed": False,
        "objective": latest_ub if latest_ub > 0.0 else 0.0,
        "lower_bound": latest_lb,
        "upper_bound": latest_ub,
        "gap": latest_gap,
        "runtime_seconds": runtime,
        "wall_time_seconds": runtime,
        "time_budget_seconds": budget,
        "actual_runtime_seconds": runtime,
        "unresolved_intervals": latest_unresolved,
        "invalid_bound_intervals": 0,
        "open_nodes": 0,
        "sealed_run": kind != "cplex",
        "no_archive_scanning": True,
        "no_external_known_ub": True,
        "no_focus_only_certificate": True,
        "finalization_source": "interrupted_checkpoint",
        "solver_finalization_reached": False,
        "wrapper_synthesized_final_json": True,
        "process_return_code": return_code if return_code is not None else -1,
        "abnormal_exit_detected": True,
        "abnormal_exit_reason": reason,
        "last_progress_event": last_progress.get("event", "wrapper_interrupted"),
        "plateau_reason": reason,
        "compact_interval_bc_enabled": kind != "cplex",
        "compact_bc_bound_valid": False,
        "compact_bc_bound_scope": "none",
        "compact_bc_rejection_reason": reason,
        "certificate_uses_bpc_tree": False,
        "route_mask_all_subset_enumeration_certifying": False,
        "cplex_threads": 1 if kind == "cplex" else 0,
        "mip_threads": 1,
        "compact_bc_solver_threads": 0 if kind == "cplex" else 1,
        "solver_thread_policy": "plain_cplex_single_thread" if kind == "cplex" else "compact_bc_single_thread",
        "thread_fairness_class": "one_thread_fair",
        "progress_log": str(progress_path) if kind != "cplex" else "",
        "progress_checkpoints_written": 1 if progress_path.exists() else 0,
        "gap_trajectory_available": progress_path.exists(),
        "notes": ["wrapper synthesized noncertified result; no optimality claim"],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_cmd(name: str, cmd: List[str], out_path: Path, progress_path: Path, timeout: int, instance: Path, kind: str, budget: int) -> None:
    if out_path.exists():
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    (ROOT / "logs").mkdir(parents=True, exist_ok=True)
    stdout_path = ROOT / "logs" / f"{name}.stdout.log"
    stderr_path = ROOT / "logs" / f"{name}.stderr.log"
    start = time.monotonic()
    rc: int | None = None
    reason = "process_exit_without_json"
    try:
        with stdout_path.open("w", encoding="utf-8") as out, stderr_path.open("w", encoding="utf-8") as err:
            proc = subprocess.run(cmd, stdout=out, stderr=err, timeout=timeout)
            rc = proc.returncode
            reason = f"return_code_{rc}"
    except subprocess.TimeoutExpired:
        reason = f"external_timeout_after_{timeout}s"
    runtime = time.monotonic() - start
    if not out_path.exists():
        wrapper_json(Path(name).stem, instance, kind, budget, out_path, progress_path, rc, runtime, reason)


def exact_command(row: str, instance: Path, budget: int, leaf_budget: int, large: bool = False) -> Tuple[List[str], Path, Path]:
    out_path = RAW / f"exact_{row}_{budget}s.json"
    progress_path = PROGRESS / f"exact_{row}_{budget}s.progress.csv"
    cmd = [
        str(EXE), "--method", "gcap-frontier",
        "--algorithm-preset", "paper-gf-compact-bc",
        "--paper-run-sealed", "true",
        "--input", str(instance),
        "--lambda", "0.15",
        "--T", "3600",
        "--time-limit", str(budget),
        "--threads", "1",
        "--mip-threads", "1",
        "--compact-bc-threads", "1",
        "--compact-bc-time-limit", str(leaf_budget),
        "--compact-bc-cut-profile", "balanced",
        "--compact-bc-root-cut-rounds", "2",
        "--compact-bc-root-cut-time-limit", "10",
        "--compact-bc-dynamic-cut-families", "support,transfer,visit,objective,receiver",
        "--compact-bc-domain-propagation-mode", "iterative",
        "--compact-bc-domain-propagation-rounds", "3",
        "--compact-bc-model-size-policy", "resource-adaptive",
        "--compact-bc-max-memory-mb", "2048",
        "--compact-bc-expensive-static-families", "auto",
        "--compact-bc-progress-interval", "30",
        "--progress-log", str(progress_path),
        "--out", str(out_path),
    ]
    if large:
        cmd.extend(["--compact-bc-use-dynamic-instead-of-static", "true"])
    return cmd, out_path, progress_path


def cplex_command(row: str, instance: Path, budget: int) -> Tuple[List[str], Path, Path]:
    out_path = RAW / f"cplex_{row}_{budget}s.json"
    cmd = [
        str(EXE), "--method", "cplex", "--plain-baseline",
        "--input", str(instance),
        "--lambda", "0.15",
        "--T", "3600",
        "--time-limit", str(budget),
        "--threads", "1",
        "--mip-threads", "1",
        "--cplex-threads", "1",
        "--out", str(out_path),
    ]
    return cmd, out_path, Path("")


def summarize() -> None:
    subprocess.run([str(PY), "scripts/summarize_gf_compact_bc_round.py", "--raw-dir", str(RAW), "--out-dir", str(ROOT)], check=False)
    summary_path = ROOT / "gf_compact_bc_summary.csv"
    if not summary_path.exists():
        return
    with summary_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    exact = [r for r in rows if r.get("method") == "gcap-frontier"]
    cplex = [r for r in rows if r.get("method") == "cplex"]
    write_csv(ROOT / "timeprofile_exact_summary.csv", exact)
    write_csv(ROOT / "timeprofile_cplex_summary.csv", cplex)
    key = lambda r: (r.get("instance_name", ""), str(int(float(r.get("time_budget_seconds") or 0))))
    cplex_by_key = {key(r): r for r in cplex}
    compare: List[Dict[str, Any]] = []
    for e in exact:
        c = cplex_by_key.get(key(e), {})
        compare.append({
            "instance_name": e.get("instance_name", ""),
            "time_budget_seconds": e.get("time_budget_seconds", ""),
            "exact_status": e.get("status", ""),
            "exact_certified": e.get("certified_original_problem", ""),
            "exact_LB": e.get("lower_bound", ""),
            "exact_UB": e.get("upper_bound", ""),
            "exact_gap": e.get("gap", ""),
            "exact_runtime": e.get("runtime_seconds", ""),
            "cplex_status": c.get("status", ""),
            "cplex_LB": c.get("lower_bound", ""),
            "cplex_UB": c.get("upper_bound", ""),
            "cplex_gap": c.get("gap", ""),
            "cplex_runtime": c.get("runtime_seconds", ""),
            "thread_fairness_class": e.get("thread_fairness_class", ""),
            "cplex_thread_fairness_class": c.get("thread_fairness_class", ""),
        })
    write_csv(ROOT / "exact_vs_cplex_timeprofile.csv", compare)
    write_csv(ROOT / "exact_vs_cplex_timeprofile_bound_quality.csv", compare)
    write_csv(ROOT / "plain_cplex_single_thread_timeprofile.csv", cplex)
    write_csv(ROOT / "dynamic_root_cut_hard_leaf_summary.csv", [
        r for r in exact if any(name in r.get("instance_name", "") for name in ["moderate_seed3301", "high_imbalance_seed3201", "tight_T_seed3102", "moderate_seed3302"])
    ])
    write_csv(ROOT / "domain_propagation_summary.csv", exact)
    write_csv(ROOT / "model_size_audit.csv", exact)
    write_csv(ROOT / "large_v_diagnostic_summary.csv", [
        r for r in exact if r.get("instance_name", "").startswith("V50") or r.get("instance_name", "").startswith("V100")
    ])
    interval_path = ROOT / "interval_leaf_status.csv"
    if interval_path.exists():
        with interval_path.open(newline="", encoding="utf-8") as handle:
            intervals = list(csv.DictReader(handle))
        write_csv(ROOT / "large_v_leaf_status.csv", [
            r for r in intervals if "V50" in r.get("source_csv", "") or "V100" in r.get("source_csv", "")
        ])
        write_csv(ROOT / "moderate_seed3301_leaf_status.csv", [
            r for r in intervals if "moderate_seed3301" in r.get("source_csv", "")
        ])
    progress_rows: List[Dict[str, Any]] = []
    for p in sorted(PROGRESS.glob("*.progress.csv")):
        try:
            with p.open(newline="", encoding="utf-8") as handle:
                trace = list(csv.DictReader(handle))
        except Exception:
            trace = []
        if not trace:
            continue
        gaps = []
        for tr in trace:
            try:
                gaps.append(float(tr.get("gap", "")))
            except Exception:
                pass
        progress_rows.append({
            "progress_log": str(p),
            "checkpoints": len(trace),
            "first_gap": gaps[0] if gaps else "",
            "best_gap": min(gaps) if gaps else "",
            "final_gap": gaps[-1] if gaps else "",
            "final_time_seconds": trace[-1].get("elapsed_seconds", ""),
        })
    write_csv(ROOT / "gap_trajectory_summary.csv", progress_rows)
    write_csv(ROOT / "moderate_seed3301_leaf_bound_progress.csv", [
        r for r in progress_rows if "moderate_seed3301" in r.get("progress_log", "")
    ])
    write_csv(ROOT / "moderate_seed3301_timeprofile.csv", [
        r for r in exact if "moderate_seed3301" in r.get("instance_name", "")
    ])
    write_csv(ROOT / "dynamic_root_cut_ablation.csv", [
        r for r in exact if str(r.get("compact_bc_total_root_cut_rounds", "0")) not in {"", "0"}
    ])
    write_csv(ROOT / "cut_ablation_timeprofile.csv", [
        r for r in exact if "ablation" in Path(r.get("file", "")).name
    ])
    write_csv(ROOT / "receiver_source_cover_pair_audit.csv", [
        {"mode": "singleton-paper-safe", "paper_safe": True, "pair_set_status": "diagnostic_only", "reason": "pair/set net cover not enabled in controlled paper rows"}
    ])
    manifest: List[Dict[str, Any]] = []
    for name, raw in {**INSTANCES, **LARGE_INSTANCES}.items():
        path = Path(raw)
        manifest.append({"row": name, "path": raw, "exists": path.exists(), "sha256": file_hash(path) if path.exists() else ""})
    write_csv(ROOT / "instance_manifest.csv", manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["priority", "full", "summarize"], default="priority")
    parser.add_argument("--include-cplex", action="store_true")
    parser.add_argument("--include-large", action="store_true")
    parser.add_argument("--external-slack", type=int, default=240)
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    PROGRESS.mkdir(parents=True, exist_ok=True)
    if args.mode != "summarize":
        exact_plan: List[Tuple[str, str, int, int, bool]] = [
            ("V12_M1", INSTANCES["V12_M1"], 300, 60, False),
            ("V12_M2", INSTANCES["V12_M2"], 300, 120, False),
            ("high_imbalance_seed3202", INSTANCES["high_imbalance_seed3202"], 300, 120, False),
            ("tight_T_seed3101", INSTANCES["tight_T_seed3101"], 300, 120, False),
            ("high_imbalance_seed3201", INSTANCES["high_imbalance_seed3201"], 300, 120, False),
            ("tight_T_seed3102", INSTANCES["tight_T_seed3102"], 300, 120, False),
            ("moderate_seed3301", INSTANCES["moderate_seed3301"], 300, 120, False),
            ("moderate_seed3302", INSTANCES["moderate_seed3302"], 300, 120, False),
            ("moderate_seed3301", INSTANCES["moderate_seed3301"], 1200, 600, False),
        ]
        if args.mode == "full":
            for row in ["high_imbalance_seed3201", "high_imbalance_seed3202", "tight_T_seed3101", "tight_T_seed3102", "moderate_seed3301", "moderate_seed3302"]:
                exact_plan.append((row, INSTANCES[row], 1200, 300, False))
        if args.include_large:
            for row, path in LARGE_INSTANCES.items():
                exact_plan.append((row, path, 300, 60, True))
        for row, raw, budget, leaf_budget, large in exact_plan:
            instance = Path(raw)
            cmd, out_path, progress_path = exact_command(row, instance, budget, leaf_budget, large)
            run_cmd(out_path.stem, cmd, out_path, progress_path, budget + args.external_slack, instance, "exact", budget)

        if args.include_cplex:
            cplex_plan: List[Tuple[str, str, int]] = [
                *( (row, path, 300) for row, path in INSTANCES.items() ),
                ("moderate_seed3301", INSTANCES["moderate_seed3301"], 1200),
                ("high_imbalance_seed3201", INSTANCES["high_imbalance_seed3201"], 1200),
            ]
            if args.include_large:
                cplex_plan.extend((row, path, 300) for row, path in LARGE_INSTANCES.items())
            for row, raw, budget in cplex_plan:
                instance = Path(raw)
                cmd, out_path, progress_path = cplex_command(row, instance, budget)
                run_cmd(out_path.stem, cmd, out_path, progress_path, budget + args.external_slack, instance, "cplex", budget)

    summarize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
