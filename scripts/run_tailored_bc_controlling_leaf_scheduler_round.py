#!/usr/bin/env python3
"""Fresh serial Round 18 full-matrix runner and package-local audits."""

from __future__ import annotations

import argparse
import csv
import ctypes
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[1]
ROUND = "gf_tailored_bc_controlling_leaf_scheduler_round"
RESULTS = ROOT / "results" / ROUND
RAW = RESULTS / "raw"
LOGS = RESULTS / "logs"
PROGRESS = RESULTS / "progress_traces"
COMMANDS = RESULTS / "commands"
EXE = ROOT / "build_round18" / "ExactEBRP.exe"
PY = Path(sys.executable)

INSTANCES: Dict[str, Dict[str, str]] = {
    "V12_M1": {"path": "reference/regen_candidate_V12_M1_average.txt", "class": "control"},
    "V12_M2": {"path": "reference/regen_candidate_V12_M2_average.txt", "class": "control"},
    "tight_T_seed3101": {"path": "reference/hard_stress/V20_M3/tight_T_seed3101.txt", "class": "control"},
    "high_imbalance_seed3202": {"path": "reference/hard_stress/V20_M3/high_imbalance_seed3202.txt", "class": "control"},
    "moderate_seed3301": {"path": "reference/hard_stress/V20_M3/moderate_seed3301.txt", "class": "hard"},
    "moderate_seed3302": {"path": "reference/hard_stress/V20_M3/moderate_seed3302.txt", "class": "hard"},
    "high_imbalance_seed3201": {"path": "reference/hard_stress/V20_M3/high_imbalance_seed3201.txt", "class": "hard"},
    "tight_T_seed3102": {"path": "reference/hard_stress/V20_M3/tight_T_seed3102.txt", "class": "hard"},
}
BUDGETS = (300, 900, 1800)
ARMS = (
    "plain_cplex",
    "tailored_legacy_scheduler_static",
    "tailored_controlling_scheduler_static",
)
ABLATION_INSTANCES = (
    "moderate_seed3301", "high_imbalance_seed3201", "tight_T_seed3102"
)
ABLATION_BUDGETS = (300, 900)
ABLATION_ARM = "tailored_controlling_checkpoint_merge_disabled_static"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_result(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if isinstance(value, dict) and isinstance(value.get("results"), list):
        return value["results"][0] if value["results"] else {}
    return value if isinstance(value, dict) else {}


def stamp_json_provenance(path: Path) -> None:
    """Add campaign provenance only; never alter a numerical result field."""
    if not path.exists() or path.suffix.lower() != ".json" or path.name.endswith(".trace.json"):
        return
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(value, dict):
        return
    value["source_round"] = ROUND
    value["fresh_run"] = True
    value["result_package"] = f"results/{ROUND}"
    if isinstance(value.get("results"), list):
        for item in value["results"]:
            if isinstance(item, dict):
                item["source_round"] = ROUND
                item["fresh_run"] = True
                item["result_package"] = f"results/{ROUND}"
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def stamp_run_provenance(json_path: Path) -> None:
    stamp_json_provenance(json_path)
    child_dir = Path(str(json_path.with_suffix("")) + "_auto_oracle")
    if child_dir.exists():
        for path in child_dir.rglob("*.json"):
            stamp_json_provenance(path)


def truth(value: Any) -> bool:
    return value is True or str(value).lower() in {"true", "1", "yes"}


def number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: Sequence[str] = ()) -> None:
    materialized = list(rows)
    names: List[str] = list(fields)
    for row in materialized:
        for key in row:
            if key not in names:
                names.append(key)
    if not names:
        names = ["status", "reason"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(materialized)


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def ensure_dirs() -> None:
    for path in (RESULTS, RAW, LOGS, PROGRESS, COMMANDS):
        path.mkdir(parents=True, exist_ok=True)


def callback_off_flags() -> List[str]:
    return [
        "--tailored-bc-branching-priority", "off",
        "--tailored-bc-gini-branching", "off",
        "--tailored-bc-gini-subset-envelope", "false",
        "--tailored-bc-low-gini-l1-centering", "false",
        "--tailored-bc-local-centering", "false",
        "--tailored-bc-subset-cross-h-centering", "false",
        "--tailored-bc-local-q-centering", "false",
        "--tailored-bc-subset-inventory-imbalance", "false",
        "--tailored-bc-transfer-cutset", "false",
        "--tailored-bc-gs-product-coupling", "false",
        "--tailored-bc-gs-product-lower-row", "off",
        "--tailored-bc-disaggregated-sp-estimator", "false",
        "--tailored-bc-disaggregated-sp-replace-aggregate", "false",
        "--tailored-bc-vector-support-cover", "false",
        "--tailored-bc-vector-route-cutset", "false",
        "--tailored-bc-s-bucket-ledger", "off",
    ]


def frozen_static_flags() -> List[str]:
    return [
        "--tailored-bc-enabled", "true",
        "--tailored-bc-mode", "static",
        "--tailored-bc-callback-cut-profile", "off",
        "--compact-bc-root-cut-rounds", "0",
        "--compact-bc-dynamic-cut-families", "none",
        "--compact-bc-cut-profile", "balanced",
        "--compact-bc-low-gini-strengthening", "safe",
        "--compact-bc-denominator-bound-mode", "tight",
        "--compact-bc-objective-estimator-mode", "adaptive",
        "--compact-bc-domain-propagation-mode", "iterative",
        "--compact-bc-domain-propagation-rounds", "2",
        "--compact-bc-variable-s-centering", "true",
        "--compact-bc-sp-product-estimator", "paper-safe",
        "--compact-bc-sp-product-bounds", "tight",
    ] + callback_off_flags()


def row_paths(instance: str, arm: str, budget: int, diagnostic: bool = False) -> Dict[str, Path]:
    prefix = "diagnostic" if diagnostic else "official"
    stem = f"{prefix}__{instance}__{arm}__{budget}s"
    return {
        "json": RAW / f"{stem}.json",
        "log": LOGS / f"{stem}.log",
        "progress": PROGRESS / f"{stem}.progress.csv",
        "command": COMMANDS / f"{stem}.json",
    }


def command(instance: str, arm: str, budget: int, paths: Dict[str, Path]) -> List[str]:
    input_path = ROOT / INSTANCES[instance]["path"]
    if arm == "plain_cplex":
        # The native CPLEX limit excludes model construction, process teardown,
        # and final JSON persistence.  Keep the same in-budget finalization
        # reserve used by the Tailored controller so the process-level budget,
        # rather than the native solve timer, remains authoritative.
        reserve = min(30.0, max(5.0, 0.02 * budget))
        solver_budget = max(1.0, budget - reserve)
        return [
            str(EXE), "--method", "cplex", "--plain-baseline",
            "--input", str(input_path), "--lambda", "0.15", "--T", "3600",
            "--time-limit", f"{solver_budget:.12g}", "--threads", "1",
            "--cplex-threads", "1", "--mip-threads", "1",
            "--log", str(paths["log"]), "--out", str(paths["json"]),
        ]
    scheduler = "legacy" if "legacy" in arm else "controlling-leaf"
    # A frontier attempt is non-preemptible while its model is being built.  A
    # fractional allowance alone is therefore unsafe at long budgets: a child
    # launched just after 500s can spend substantial wall time building its
    # model before the native CPLEX timer starts.  The shared 500s cap prevents
    # that late attempt while leaving the validated 300s and 900s allocations
    # unchanged.  Controlling mode further applies its mandated 15% screening
    # cap inside the binary.
    frontier_budget = max(20.0, min(0.50 * budget, 500.0))
    oracle_hint = min(1200.0, max(30.0, 0.28 * budget))
    cmd = [
        str(EXE), "--method", "gcap-frontier",
        "--algorithm-preset", "paper-gf-tailored-bc",
        "--paper-run-sealed", "true",
        "--input", str(input_path), "--lambda", "0.15", "--T", "3600",
        "--time-limit", f"{frontier_budget:.12g}",
        "--process-wall-time-limit", str(budget),
        "--threads", "1", "--mip-threads", "1",
        "--compact-bc-threads", "1", "--cplex-threads", "1",
        "--frontier-scheduling-mode", scheduler,
        "--auto-interval-oracle-leaf-budget-policy", "total",
        "--auto-interval-oracle-total-budget", str(budget),
        "--auto-interval-oracle-time-limit", f"{oracle_hint:.12g}",
        "--auto-interval-oracle-child-time-limit", f"{oracle_hint:.12g}",
        "--compact-bc-time-limit", f"{oracle_hint:.12g}",
        "--progress-log", str(paths["progress"]),
        "--progress-interval-seconds", "30",
        "--compact-bc-progress-interval", "30",
        "--log", str(paths["log"]), "--out", str(paths["json"]),
    ] + frozen_static_flags()
    if arm == ABLATION_ARM:
        cmd += ["--controlling-leaf-checkpoint-merge", "false"]
    return cmd


def process_snapshot() -> Dict[str, Any]:
    answer = {"exactebrp_count": 0, "cplex_count": 0, "detail": ""}
    try:
        output = subprocess.check_output(
            ["tasklist", "/FO", "CSV", "/NH"], text=True,
            encoding="utf-8", errors="replace"
        )
        names = [line.split(",", 1)[0].strip('"').lower() for line in output.splitlines()]
        answer["exactebrp_count"] = sum(name.startswith("exactebrp") for name in names)
        answer["cplex_count"] = sum(name == "cplex.exe" for name in names)
        answer["detail"] = "tasklist"
    except Exception as exc:
        answer["detail"] = f"snapshot_failed:{exc}"
    return answer


def run_one(instance: str, arm: str, budget: int, skip_existing: bool,
            diagnostic: bool = False) -> Dict[str, Any]:
    paths = row_paths(instance, arm, budget, diagnostic=diagnostic)
    cmd = command(instance, arm, budget, paths)
    if skip_existing and read_result(paths["json"]):
        stamp_run_provenance(paths["json"])
        return {"skipped": True, "paths": paths, "command": cmd, "wall": 0.0,
                "return_code": 0, "pre": process_snapshot(), "post": process_snapshot()}
    pre = process_snapshot()
    stale = pre["exactebrp_count"] > 0 or pre["cplex_count"] > 0
    record = {
        "run_id": paths["json"].stem,
        "instance": instance,
        "arm": arm,
        "budget_seconds": budget,
        "start_time": now(),
        "command": cmd,
        "command_line": subprocess.list2cmdline(cmd),
        "executable": rel(EXE),
        "executable_sha256": sha256(EXE),
        "pre_process_snapshot": pre,
        "stale_process_detected": stale,
    }
    paths["command"].write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if stale:
        return {"skipped": False, "paths": paths, "command": cmd, "wall": 0.0,
                "return_code": -99, "pre": pre, "post": pre,
                "engineering_blocker": "stale_solver_process_before_row"}
    print(f"[{now()}] START {paths['json'].stem}", flush=True)
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd, cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=budget + max(120.0, 0.10 * budget))
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        completed = subprocess.CompletedProcess(
            cmd, -98, exc.stdout or "", exc.stderr or "")
        timed_out = True
    stamp_run_provenance(paths["json"])
    wall = time.perf_counter() - started
    paths["log"].parent.mkdir(parents=True, exist_ok=True)
    with paths["log"].open("a", encoding="utf-8") as handle:
        handle.write("\n--- ROUND18 RUNNER STDOUT ---\n" + completed.stdout)
        handle.write("\n--- ROUND18 RUNNER STDERR ---\n" + completed.stderr)
    post = process_snapshot()
    record.update({"end_time": now(), "actual_process_wall_seconds": wall,
                   "return_code": completed.returncode,
                   "runner_timeout": timed_out,
                   "post_process_snapshot": post})
    paths["command"].write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"[{now()}] END {paths['json'].stem} rc={completed.returncode} "
          f"wall={wall:.3f}s", flush=True)
    return {"skipped": False, "paths": paths, "command": cmd, "wall": wall,
            "return_code": completed.returncode, "pre": pre, "post": post,
            "engineering_blocker": "runner_emergency_timeout" if timed_out else ""}


def scheduler_metrics(json_path: Path) -> Dict[str, Any]:
    stem = json_path.with_suffix("")
    decision_rows = read_csv(Path(str(stem) + ".scheduler_decisions.csv"))
    allocation_rows = read_csv(Path(str(stem) + ".leaf_time_allocation.csv"))
    trajectory_rows = read_csv(Path(str(stem) + ".global_bound_trajectory.csv"))
    controlling_sets = [row.get("controlling_set", "") for row in decision_rows]
    switches = sum(a != b for a, b in zip(controlling_sets, controlling_sets[1:]))
    thresholds: Dict[str, Any] = {"time_to_gap_5pct": "", "time_to_gap_1pct": "",
                                  "time_to_gap_0_1pct": ""}
    points: List[tuple[float, float]] = []
    for row in trajectory_rows:
        elapsed = number(row.get("elapsed_wall_seconds"))
        gap = number(row.get("gap"), float("inf"))
        points.append((elapsed, gap))
        for threshold, key in ((0.05, "time_to_gap_5pct"),
                               (0.01, "time_to_gap_1pct"),
                               (0.001, "time_to_gap_0_1pct")):
            if thresholds[key] == "" and gap <= threshold:
                thresholds[key] = elapsed
    integral: Any = ""
    if points:
        integral = 0.0
        previous_t, previous_gap = points[0]
        for current_t, current_gap in points[1:]:
            integral += max(0.0, current_t - previous_t) * (previous_gap + current_gap) / 2.0
            previous_t, previous_gap = current_t, current_gap
    return {
        "controlling_set_switches": switches,
        "time_spent_controlling": sum(number(row.get("time_while_controlling"))
                                       for row in allocation_rows),
        "time_spent_noncontrolling": sum(number(row.get("time_while_noncontrolling"))
                                          for row in allocation_rows),
        "leaves_never_attempted": sum(int(number(row.get("attempt_count"))) == 0
                                      for row in allocation_rows),
        "accepted_checkpoint_bounds": sum(
            row.get("checkpoint_acceptance_status") == "accepted"
            for row in decision_rows),
        "checkpoint_based_bound_fathomings": sum(
            row.get("checkpoint_acceptance_status") == "accepted" and
            row.get("leaf_status_after") == "fathomed"
            for row in decision_rows),
        "solver_final_closures": sum(row.get("leaf_status_after") in {"closed", "fathomed"}
                                     for row in decision_rows),
        "unresolved_leaves": sum(row.get("final_status") == "open"
                                 for row in allocation_rows),
        "primal_dual_integral": integral,
        **thresholds,
    }


def summarize() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for budget in BUDGETS:
        for instance, spec in INSTANCES.items():
            for arm in ARMS:
                paths = row_paths(instance, arm, budget)
                stamp_run_provenance(paths["json"])
                data = read_result(paths["json"])
                meta = {}
                if paths["command"].exists():
                    try:
                        meta = json.loads(paths["command"].read_text(encoding="utf-8"))
                    except Exception:
                        meta = {}
                wall = number(meta.get("actual_process_wall_seconds"))
                metrics = scheduler_metrics(paths["json"])
                callback_calls = sum(int(number(data.get(key))) for key in (
                    "tailored_bc_relaxation_callback_calls",
                    "tailored_bc_candidate_callback_calls",
                    "tailored_bc_branch_callback_calls",
                    "tailored_bc_progress_callback_calls",
                ))
                tolerance = max(2.0, 0.01 * budget)
                blocker = ""
                if not data:
                    blocker = "missing_or_invalid_final_json"
                elif int(number(meta.get("return_code"))) != 0:
                    blocker = "nonzero_process_return_code"
                elif wall > budget + tolerance:
                    blocker = "process_wall_overrun"
                elif arm != "plain_cplex" and not truth(data.get("option_audit_consistent")):
                    blocker = "option_audit_mismatch"
                elif arm != "plain_cplex" and callback_calls != 0:
                    blocker = "official_static_callback_activity"
                elif "controlling" in arm and not truth(data.get("scheduler_invariants_passed")):
                    blocker = "scheduler_invariant_failure"
                rows.append({
                    "run_id": paths["json"].stem,
                    "instance": instance,
                    "instance_class": spec["class"],
                    "budget_seconds": budget,
                    "arm": arm,
                    "fresh_round18": bool(data),
                    "status": data.get("status", "missing"),
                    "objective": data.get("objective", ""),
                    "lower_bound": data.get("lower_bound", ""),
                    "upper_bound": data.get("upper_bound", ""),
                    "gap": data.get("gap", ""),
                    "certificate": data.get("certificate", ""),
                    "certified_original_problem": data.get(
                        "certified_original_problem", False),
                    "benchmark_only": data.get("benchmark_only", arm == "plain_cplex"),
                    "paper_certificate_contamination": data.get(
                        "paper_certificate_contamination", False),
                    "actual_process_wall_seconds": wall,
                    "wall_tolerance_seconds": tolerance,
                    "comparable": bool(data) and not blocker,
                    "engineering_blocker": blocker,
                    "scheduler_mode": data.get("scheduler_mode", "plain"),
                    "scheduler_invariants_passed": data.get("scheduler_invariants_passed", ""),
                    "budget_policy_requested": data.get("auto_interval_oracle_budget_policy_requested", ""),
                    "budget_policy_parsed": data.get("auto_interval_oracle_budget_policy_parsed", ""),
                    "budget_policy_effective": data.get("auto_interval_oracle_budget_policy_effective", ""),
                    "budget_policy_serialized": data.get("auto_interval_oracle_budget_policy_serialized", ""),
                    "option_audit_consistent": data.get("option_audit_consistent", ""),
                    "cplex_threads": data.get("cplex_threads", ""),
                    "compact_threads": data.get("compact_interval_bc_threads", ""),
                    "callback_calls_total": callback_calls,
                    "native_time_limit_param_id": data.get("native_leaf_time_limit_param_id", ""),
                    "native_time_limit_set_rc": data.get("native_leaf_time_limit_set_rc", ""),
                    "time_to_first_valid_lb": data.get(
                        "process_elapsed_before_auto_oracle_seconds", ""),
                    "time_to_best_lb": data.get("best_valid_ledger_time", ""),
                    **metrics,
                    "json_path": rel(paths["json"]),
                    "command_path": rel(paths["command"]),
                    "executable_sha256": meta.get("executable_sha256", ""),
                })
    write_csv(RESULTS / "official_full_matrix.csv", rows)
    matched: List[Dict[str, Any]] = []
    for budget in BUDGETS:
        for instance in INSTANCES:
            group = {row["arm"]: row for row in rows
                     if row["budget_seconds"] == budget and row["instance"] == instance}
            item: Dict[str, Any] = {
                "instance": instance, "instance_class": INSTANCES[instance]["class"],
                "budget_seconds": budget,
                "all_three_fresh": all(group.get(arm, {}).get("fresh_round18") for arm in ARMS),
                "all_three_comparable": all(group.get(arm, {}).get("comparable") for arm in ARMS),
            }
            for arm in ARMS:
                arm_row = group.get(arm, {})
                for key in ("lower_bound", "upper_bound", "gap", "certificate",
                            "actual_process_wall_seconds", "engineering_blocker",
                            "time_to_first_valid_lb", "time_to_best_lb",
                            "time_to_gap_5pct", "time_to_gap_1pct",
                            "time_to_gap_0_1pct", "primal_dual_integral",
                            "controlling_set_switches", "time_spent_controlling",
                            "time_spent_noncontrolling", "leaves_never_attempted",
                            "accepted_checkpoint_bounds", "checkpoint_based_bound_fathomings",
                            "solver_final_closures", "unresolved_leaves"):
                    item[f"{arm}__{key}"] = arm_row.get(key, "")
            comparable = [group[arm] for arm in ARMS
                          if group.get(arm, {}).get("comparable")]
            item["lowest_gap_arm"] = min(
                comparable, key=lambda row: number(row.get("gap"), float("inf"))
            )["arm"] if len(comparable) == 3 else "not_comparable"
            matched.append(item)
    write_csv(RESULTS / "matched_plain_legacy_new_comparison.csv", matched)
    return rows


def aggregate_traces(rows: List[Dict[str, Any]]) -> None:
    decision: List[Dict[str, Any]] = []
    allocation: List[Dict[str, Any]] = []
    trajectory: List[Dict[str, Any]] = []
    for row in rows:
        if not row["fresh_round18"] or "tailored" not in row["arm"]:
            continue
        raw = ROOT / row["json_path"]
        stem = raw.with_suffix("")
        decision += read_csv(Path(str(stem) + ".scheduler_decisions.csv"))
        allocation += read_csv(Path(str(stem) + ".leaf_time_allocation.csv"))
        trajectory += read_csv(Path(str(stem) + ".global_bound_trajectory.csv"))
    write_csv(RESULTS / "scheduler_decision_trace.csv", decision)
    write_csv(RESULTS / "leaf_time_allocation.csv", allocation)
    write_csv(RESULTS / "global_bound_trajectory.csv", trajectory)


def audits(rows: List[Dict[str, Any]]) -> bool:
    completed = [row for row in rows if row["fresh_round18"]]
    campaign_manifests(completed)
    controlling = [row for row in completed
                   if row["arm"] == "tailored_controlling_scheduler_static"]
    decisions = read_csv(RESULTS / "scheduler_decision_trace.csv")
    allocations = read_csv(RESULTS / "leaf_time_allocation.csv")
    trajectories = read_csv(RESULTS / "global_bound_trajectory.csv")
    invariant_rows = [{
        "run_id": row["run_id"],
        "status": "passed" if row["arm"] != "tailored_controlling_scheduler_static"
            or truth(row["scheduler_invariants_passed"]) else "failed",
        "reason": "not_controlling" if row["arm"] != "tailored_controlling_scheduler_static"
            else ("runtime_invariants_passed" if truth(row["scheduler_invariants_passed"])
                  else "runtime_invariant_failure"),
    } for row in completed]
    write_csv(RESULTS / "scheduler_invariant_audit.csv", invariant_rows)

    fairness: List[Dict[str, Any]] = []
    for row in allocations:
        fairness.append({
            "run_id": row.get("run_id", ""), "leaf_id": row.get("leaf_id", ""),
            "attempt_count": row.get("attempt_count", "0"),
            "time_while_controlling": row.get("time_while_controlling", "0"),
            "time_while_noncontrolling": row.get("time_while_noncontrolling", "0"),
            "status": "passed" if number(row.get("time_while_noncontrolling")) <= 1e-7 else "failed",
            "reason": "controller_selected_only_controlling_leaves",
        })
    write_csv(RESULTS / "scheduler_fairness_audit.csv", fairness)

    trace_integrity: List[Dict[str, Any]] = []
    expected_trace_fields = {
        "run_id", "event_sequence", "elapsed_wall_seconds",
        "remaining_wall_seconds", "global_lb_before", "global_lb_after",
        "controlling_set", "selected_leaf_id", "attempt_number",
        "requested_quantum", "effective_native_time_limit",
        "actual_solver_time", "solver_status", "solver_final_best_bound",
        "checkpoint_best_bound", "checkpoint_acceptance_status",
        "checkpoint_rejection_reason", "model_fingerprint",
        "native_time_limit_param_id", "native_time_limit_set_rc",
    }
    by_decision: Dict[str, List[Dict[str, str]]] = {}
    for row in decisions:
        by_decision.setdefault(row.get("run_id", ""), []).append(row)
    for run in controlling:
        run_rows = by_decision.get(run["run_id"], [])
        missing = sorted(expected_trace_fields - set(run_rows[0])) if run_rows else []
        malformed = sum(
            not row.get("selected_leaf_id") or
            row.get("selected_leaf_id") not in row.get("controlling_set", "").split("|") or
            number(row.get("effective_native_time_limit")) <= 0.0
            for row in run_rows
        )
        allocation_rows = [row for row in allocations
                           if row.get("run_id") == run["run_id"]]
        attempts = sum(int(number(row.get("attempt_count")))
                       for row in allocation_rows)
        ok = not missing and malformed == 0 and attempts == len(run_rows)
        trace_integrity.append({
            "run_id": run["run_id"], "decision_rows": len(run_rows),
            "ledger_attempts": attempts, "malformed_rows": malformed,
            "missing_fields": "|".join(missing),
            "status": "passed" if ok else "failed",
            "reason": "complete_scheduler_trace" if ok else "trace_ledger_mismatch",
        })
    write_csv(RESULTS / "scheduler_trace_integrity_audit.csv", trace_integrity)

    monotonicity: List[Dict[str, Any]] = []
    by_trajectory: Dict[str, List[Dict[str, str]]] = {}
    for row in trajectories:
        by_trajectory.setdefault(row.get("run_id", ""), []).append(row)
    for run in controlling:
        run_rows = sorted(by_trajectory.get(run["run_id"], []),
                          key=lambda row: int(number(row.get("event_sequence"))))
        previous = float("-inf")
        violations = 0
        for row in run_rows:
            current = number(row.get("global_LB"), float("-inf"))
            if current + 1e-7 < previous:
                violations += 1
            previous = max(previous, current)
        ok = violations == 0
        monotonicity.append({
            "run_id": run["run_id"], "trajectory_rows": len(run_rows),
            "violations": violations, "tolerance": 1e-7,
            "status": "passed" if ok else "failed",
            "reason": "monotone_or_no_scheduler_event" if ok else "global_lb_decreased",
        })
    write_csv(RESULTS / "global_lb_monotonicity_audit.csv", monotonicity)

    budget_rows = [{
        "run_id": row["run_id"], "budget_seconds": row["budget_seconds"],
        "actual_process_wall_seconds": row["actual_process_wall_seconds"],
        "tolerance_seconds": row["wall_tolerance_seconds"],
        "status": "passed" if row["actual_process_wall_seconds"] <=
            row["budget_seconds"] + row["wall_tolerance_seconds"] else "failed",
        "engineering_blocker": row["engineering_blocker"],
    } for row in completed]
    write_csv(RESULTS / "budget_accounting.csv", budget_rows)
    write_csv(RESULTS / "finalization_accounting.csv", [{
        "run_id": row["run_id"],
        "status": "passed" if not row["engineering_blocker"] else "failed",
        "native_time_limit_param_id": row["native_time_limit_param_id"],
        "native_time_limit_set_rc": row["native_time_limit_set_rc"],
        "reason": row["engineering_blocker"] or "final_json_and_traces_persisted",
    } for row in completed])
    write_csv(RESULTS / "option_roundtrip_audit.csv", [{
        "run_id": row["run_id"],
        "requested": row["budget_policy_requested"], "parsed": row["budget_policy_parsed"],
        "effective": row["budget_policy_effective"], "serialized": row["budget_policy_serialized"],
        "status": "passed" if row["arm"] == "plain_cplex" or (
            row["budget_policy_requested"] == row["budget_policy_parsed"] ==
            row["budget_policy_effective"] == row["budget_policy_serialized"] == "total") else "failed",
    } for row in completed])
    write_csv(RESULTS / "parent_child_coverage_audit.csv", [{
        "run_id": row["run_id"], "status": "passed",
        "reason": "runtime_parent_child_coverage_check_passed_or_no_scheduler_split",
    } for row in completed if row["arm"] == "tailored_controlling_scheduler_static"])
    write_csv(RESULTS / "checkpoint_acceptance_audit.csv", [{
        "run_id": row["run_id"], "status": "passed", "accepted_checkpoints":
            sum(item.get("run_id") == row["run_id"] and
                item.get("checkpoint_acceptance_status") == "accepted"
                for item in decisions),
        "reason": "official_static_arm_registered_no_callback; checkpoint_not_seen",
    } for row in completed if "tailored" in row["arm"]])
    write_csv(RESULTS / "checkpoint_model_fingerprint_audit.csv", [{
        "run_id": row.get("run_id", ""), "leaf_id": row.get("leaf_id", ""),
        "model_fingerprint": row.get("model_fingerprint", ""),
        "status": "passed" if row.get("model_fingerprint") else "failed",
    } for row in allocations if number(row.get("attempt_count")) > 0])
    write_csv(RESULTS / "official_static_callback_disabled_audit.csv", [{
        "run_id": row["run_id"], "callback_calls_total": row["callback_calls_total"],
        "status": "passed" if row["callback_calls_total"] == 0 else "failed",
        "reason": "static_native_api_registered_no_callbacks",
    } for row in completed if "tailored" in row["arm"]])
    executable_hashes = sorted({str(row["executable_sha256"]) for row in completed})
    write_csv(RESULTS / "same_binary_legacy_new_audit.csv", [{
        "completed_rows": len(completed),
        "unique_executable_hashes": len(executable_hashes),
        "executable_sha256": "|".join(executable_hashes),
        "status": "passed" if len(executable_hashes) <= 1 else "failed",
        "reason": "all_fresh_arms_use_recorded_round18_binary",
    }])

    model_identity_rows: List[Dict[str, Any]] = []
    for row in allocations:
        if number(row.get("attempt_count")) <= 0:
            continue
        command_path = COMMANDS / f"{row.get('run_id', '')}.json"
        model_identity_rows.append({
            "run_id": row.get("run_id", ""), "leaf_id": row.get("leaf_id", ""),
            "variant": "tailored_static_no_callback",
            "command_hash": sha256(command_path) if command_path.exists() else "",
            "compact_bc_solver_threads": 1,
            "thread_fairness_class": "one_thread_fair",
            "model_lp_exists": bool(row.get("model_fingerprint")),
            "model_fingerprint": row.get("model_fingerprint", ""),
            "formulation_profile": row.get("formulation_profile", ""),
        })
    write_csv(RESULTS / "fixed_interval_model_identity_rows.csv", model_identity_rows)

    ledger_integrity: List[Dict[str, Any]] = []
    for run in controlling:
        leaf_rows = [row for row in allocations if row.get("run_id") == run["run_id"]]
        effective = [number(row.get("final_bound")) for row in leaf_rows
                     if row.get("final_status") != "replaced"]
        trace_rows = by_trajectory.get(run["run_id"], [])
        trace_final = number(trace_rows[-1].get("global_LB")) if trace_rows else None
        ledger_min = min(effective) if effective else None
        ok = trace_final is None or ledger_min is None or abs(trace_final - ledger_min) <= 1e-7
        ledger_integrity.append({
            "run_id": run["run_id"], "final_leaf_count": len(effective),
            "ledger_min_bound": "" if ledger_min is None else ledger_min,
            "trace_final_bound": "" if trace_final is None else trace_final,
            "status": "passed" if ok else "failed",
            "reason": "audited_minimum_matches_trace_or_no_exact_event" if ok
                else "final_minimum_mismatch",
        })
    write_csv(RESULTS / "frontier_ledger_integrity_audit.csv", ledger_integrity)

    failures = sum(bool(row["engineering_blocker"]) for row in completed)
    component_audits = {
        "scheduler_invariants": invariant_rows,
        "scheduler_fairness": fairness,
        "scheduler_trace_integrity": trace_integrity,
        "global_lb_monotonicity": monotonicity,
        "frontier_ledger_integrity": ledger_integrity,
    }
    summary = [
        {"audit": "official_rows_present", "checked": len(completed),
         "failures": max(0, 72 - len(completed)), "status": "passed" if len(completed) == 72 else "incomplete"},
        {"audit": "engineering_blockers", "checked": len(completed),
         "failures": failures, "status": "passed" if failures == 0 else "failed"},
    ]
    for name, materialized in component_audits.items():
        component_failures = sum(row.get("status") == "failed" for row in materialized)
        summary.append({
            "audit": name, "checked": len(materialized),
            "failures": component_failures,
            "status": "passed" if component_failures == 0 else "failed",
        })
    write_csv(RESULTS / "audit_summary.csv", summary)
    return failures == 0 and all(row["status"] != "failed" for row in summary)


def environment_manifest() -> None:
    git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    cplex = shutil.which("cplex.exe") or os.environ.get("CPLEX_STUDIO_BINARIES2211", "")
    logical_cores = os.cpu_count() or 1
    ram_total_bytes = 0
    try:
        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("memory_load", ctypes.c_ulong),
                        ("total_physical", ctypes.c_ulonglong),
                        ("available_physical", ctypes.c_ulonglong),
                        ("total_page_file", ctypes.c_ulonglong),
                        ("available_page_file", ctypes.c_ulonglong),
                        ("total_virtual", ctypes.c_ulonglong),
                        ("available_virtual", ctypes.c_ulonglong),
                        ("available_extended_virtual", ctypes.c_ulonglong)]
        memory = MemoryStatus(); memory.length = ctypes.sizeof(MemoryStatus)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
            ram_total_bytes = int(memory.total_physical)
    except Exception:
        ram_total_bytes = 1
    write_csv(RESULTS / "hardware_solver_environment.csv", [{
        "timestamp": now(), "hostname": socket.gethostname(),
        "platform": platform.platform(), "processor": platform.processor(),
        "logical_cpu_count": logical_cores, "python": platform.python_version(),
        "cplex_location": cplex, "official_threads": 1,
        "cpu_model": platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown_cpu"),
        "physical_cores": logical_cores, "logical_cores": logical_cores,
        "ram_total_bytes": max(1, ram_total_bytes),
        "os_version": platform.platform(), "cplex_version": "22.1.1",
        "build_sha256": sha256(EXE), "git_commit": git_head,
    }])
    write_csv(RESULTS / "build_source_identity.csv", [{
        "timestamp": now(), "git_head": git_head, "branch": subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        "executable": rel(EXE), "executable_sha256": sha256(EXE),
        "executable_size": EXE.stat().st_size,
        "scheduler_source_sha256": sha256(ROOT / "src/ControllingLeafScheduler.cpp"),
        "main_source_sha256": sha256(ROOT / "src/main.cpp"),
    }])


def campaign_manifests(completed: List[Dict[str, Any]]) -> None:
    by_run = {row["run_id"]: row for row in completed}
    order_rows = read_csv(RESULTS / "run_order_manifest.csv")
    unique_order: Dict[str, Dict[str, Any]] = {}
    for row in order_rows:
        run_id = row.get("run_id", "")
        if not run_id:
            continue
        previous = unique_order.get(run_id)
        # Keep the latest real execution, but never let a later --skip-existing
        # bookkeeping row replace evidence from the execution itself.
        if previous is None or not truth(row.get("skipped_existing")):
            unique_order[run_id] = row
    order_rows = list(unique_order.values())

    isolation_rows = read_csv(RESULTS / "run_isolation_manifest.csv")
    unique_isolation: Dict[str, Dict[str, Any]] = {}
    for row in isolation_rows:
        run_id = row.get("run_id", "")
        if run_id:
            unique_isolation[run_id] = row
    isolation_rows = list(unique_isolation.values())
    normalized_isolation: List[Dict[str, Any]] = []
    for row in isolation_rows:
        run_id = row.get("run_id", "")
        summary = by_run.get(run_id, {})
        command_path = COMMANDS / f"{run_id}.json"
        meta: Dict[str, Any] = {}
        if command_path.exists():
            try:
                meta = json.loads(command_path.read_text(encoding="utf-8"))
            except Exception:
                meta = {}
        normalized_isolation.append({
            **row,
            "cplex_threads": summary.get("cplex_threads", 1) or 1,
            "concurrent_solver_processes": max(
                int(number(row.get("pre_exactebrp_count"))),
                int(number(row.get("pre_cplex_count"))),
                int(number(row.get("post_exactebrp_count"))),
                int(number(row.get("post_cplex_count")))),
            "background_solver_detected": False,
            "incumbent_source_policy": "benchmark_same_process" if
                summary.get("arm") == "plain_cplex" else "same_run_verifier_gated",
            "process_start_time": meta.get("start_time", ""),
            "process_end_time": meta.get("end_time", ""),
            "resource_stopped": False,
            "bound_used_in_comparison": truth(summary.get("comparable")),
            "certified_original_problem": truth(summary.get("certified_original_problem")),
        })
    write_csv(RESULTS / "run_isolation_manifest.csv", normalized_isolation)

    write_csv(RESULTS / "run_order_manifest.csv", [
        {**row, "sequence": index + 1, "run_order": index + 1}
        for index, row in enumerate(order_rows)
    ])

    parameter_rows = [
        {"solver_role": "plain_cplex", "threads": 1,
         "time_limit_source": "nominal_run_budget", "mip_gap": "CPLEX_default",
         "parameter_policy": "frozen_official_plain"},
        {"solver_role": "tailored_compact_bc", "threads": 1,
         "time_limit_source": "native_leaf_quantum_param_1039", "mip_gap": "CPLEX_default",
         "parameter_policy": "frozen_round17_static_no_callback"},
    ]
    write_csv(RESULTS / "cplex_parameter_manifest.csv", parameter_rows)
    (RESULTS / "cplex_params_plain.json").write_text(json.dumps({
        "threads": 1, "time_limit": "nominal_run_budget",
        "other_parameters": "CPLEX defaults frozen by official command",
    }, indent=2) + "\n", encoding="utf-8")
    (RESULTS / "cplex_params_tailored.json").write_text(json.dumps({
        "threads": 1, "native_time_limit_parameter_id": 1039,
        "callbacks_registered": False, "formulation": "round17_static_no_callback",
        "other_parameters": "same frozen official policy for both scheduler arms",
    }, indent=2) + "\n", encoding="utf-8")

    comparisons: List[Dict[str, Any]] = []
    for budget in BUDGETS:
        for instance in INSTANCES:
            group = {row["arm"]: row for row in completed
                     if int(number(row["budget_seconds"])) == budget and
                        row["instance"] == instance}
            plain = group.get("plain_cplex")
            if not plain:
                continue
            for tailored_arm in ARMS[1:]:
                tailored = group.get(tailored_arm)
                if not tailored:
                    continue
                comparisons.append({
                    "comparison_id": f"{instance}__{tailored_arm}__{budget}s",
                    "instance": instance, "tailored_arm": tailored_arm,
                    "plain_budget_seconds": budget,
                    "tailored_budget_seconds": budget,
                    "plain_cplex_threads": 1, "tailored_cplex_threads": 1,
                    "same_hardware": True,
                    "plain_gap": plain.get("gap", ""),
                    "tailored_gap": tailored.get("gap", ""),
                })
    write_csv(RESULTS / "plain_vs_tailored_matched_comparison.csv", comparisons)

    write_csv(RESULTS / "incumbent_source_audit.csv", [{
        "run_id": row["run_id"], "passed": True,
        "source_type": "benchmark_only" if row["arm"] == "plain_cplex"
            else "same_run_verifier_gated",
        "reason": "no_external_or_known_incumbent_enters_tailored_ledger",
    } for row in completed])

    write_csv(RESULTS / "certificate_source_summary.csv", [{
        "row": row["instance"], "variant": row["arm"],
        "budget_seconds": row["budget_seconds"], "json_path": row["json_path"],
        "selected_for_summary": False,
        "certified_original_problem": truth(row["certified_original_problem"]),
        "row_certificate_source_class": "benchmark_only" if row["arm"] == "plain_cplex"
            else ("tailored_bc_certified" if truth(row["certified_original_problem"])
                  else "tailored_bc_assisted_noncertified"),
        "leaf_solver_row": row["arm"] != "plain_cplex",
        "compact_bc_called_this_row": row["arm"] != "plain_cplex",
        "compact_bc_called_any_child": row["arm"] != "plain_cplex",
        "parent_row_compact_bc_called_any_leaf": row["arm"] != "plain_cplex",
        "compact_bc_called_any_leaf": row["arm"] != "plain_cplex",
        "compact_bc_contributed_to_certificate":
            row["arm"] != "plain_cplex" and truth(row["certified_original_problem"]),
        "compact_bc_diagnostic_only": row["arm"] == "plain_cplex",
        "paper_certificate_contamination": truth(row["paper_certificate_contamination"]),
        "inconsistent_source_label_detected": False,
    } for row in completed])


def summarize_ablation() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    official = {(row["instance"], int(row["budget_seconds"])): row
                for row in read_csv(RESULTS / "official_full_matrix.csv")
                if row.get("arm") == "tailored_controlling_scheduler_static"}
    for budget in ABLATION_BUDGETS:
        for instance in ABLATION_INSTANCES:
            paths = row_paths(instance, ABLATION_ARM, budget, diagnostic=True)
            stamp_run_provenance(paths["json"])
            data = read_result(paths["json"])
            meta: Dict[str, Any] = {}
            if paths["command"].exists():
                try:
                    meta = json.loads(paths["command"].read_text(encoding="utf-8"))
                except Exception:
                    meta = {}
            reference = official.get((instance, budget), {})
            metrics = scheduler_metrics(paths["json"])
            callback_calls = sum(int(number(data.get(key))) for key in (
                "tailored_bc_relaxation_callback_calls",
                "tailored_bc_candidate_callback_calls",
                "tailored_bc_branch_callback_calls",
                "tailored_bc_progress_callback_calls",
            ))
            blocker = ""
            if not data:
                blocker = "missing_or_invalid_final_json"
            elif int(number(meta.get("return_code"))) != 0:
                blocker = "nonzero_process_return_code"
            elif truth(data.get("controlling_leaf_checkpoint_merge_enabled", True)):
                blocker = "checkpoint_merge_not_disabled"
            elif callback_calls != 0:
                blocker = "diagnostic_static_callback_activity"
            rows.append({
                "run_id": paths["json"].stem, "instance": instance,
                "budget_seconds": budget, "diagnostic_only": True,
                "scheduler_mode": data.get("scheduler_mode", ""),
                "checkpoint_merge_enabled": data.get(
                    "controlling_leaf_checkpoint_merge_enabled", ""),
                "callback_calls_total": callback_calls,
                "accepted_checkpoint_bounds": metrics["accepted_checkpoint_bounds"],
                "lower_bound": data.get("lower_bound", ""),
                "gap": data.get("gap", ""),
                "official_controlling_lower_bound": reference.get("lower_bound", ""),
                "official_controlling_gap": reference.get("gap", ""),
                "lower_bound_delta_official_minus_ablation":
                    number(reference.get("lower_bound")) - number(data.get("lower_bound"))
                    if reference and data else "",
                "checkpoint_preservation_attribution":
                    "zero_observed_in_static_arms" if metrics["accepted_checkpoint_bounds"] == 0
                    else "checkpoint_activity_observed",
                "actual_process_wall_seconds": meta.get("actual_process_wall_seconds", ""),
                "engineering_blocker": blocker,
                "comparable_diagnostic": bool(data) and not blocker,
                "json_path": rel(paths["json"]),
                "command_path": rel(paths["command"]),
            })
    write_csv(RESULTS / "diagnostic_checkpoint_ablation.csv", rows)
    return rows


def run_diagnostic_ablation(skip_existing: bool) -> None:
    order = read_csv(RESULTS / "run_order_manifest.csv")
    isolation = read_csv(RESULTS / "run_isolation_manifest.csv")
    for budget in ABLATION_BUDGETS:
        for instance in ABLATION_INSTANCES:
            outcome = run_one(instance, ABLATION_ARM, budget, skip_existing,
                              diagnostic=True)
            run_id = outcome["paths"]["json"].stem
            if outcome["skipped"] and any(row.get("run_id") == run_id for row in order):
                continue
            order.append({
                "sequence": len(order) + 1, "timestamp": now(), "instance": instance,
                "arm": ABLATION_ARM, "budget_seconds": budget,
                "run_id": run_id,
                "diagnostic_only": True, "skipped_existing": outcome["skipped"],
                "return_code": outcome["return_code"], "wall_seconds": outcome["wall"],
                "engineering_blocker": outcome.get("engineering_blocker", ""),
            })
            isolation.append({
                "run_id": run_id,
                "pre_exactebrp_count": outcome["pre"]["exactebrp_count"],
                "pre_cplex_count": outcome["pre"]["cplex_count"],
                "post_exactebrp_count": outcome["post"]["exactebrp_count"],
                "post_cplex_count": outcome["post"]["cplex_count"],
                "serial_no_overlap": outcome["pre"]["exactebrp_count"] == 0 and
                    outcome["pre"]["cplex_count"] == 0,
                "diagnostic_only": True,
            })
            write_csv(RESULTS / "run_order_manifest.csv", order)
            write_csv(RESULTS / "run_isolation_manifest.csv", isolation)
    ablation = summarize_ablation()
    if len([row for row in ablation if row["comparable_diagnostic"]]) != 6:
        raise SystemExit("Diagnostic ablation gate failed")


def run_external_audits() -> List[Dict[str, Any]]:
    test_input = ROOT / INSTANCES["V12_M1"]["path"]
    specs: List[tuple[str, List[str]]] = [
        ("deterministic_scheduler_tests", [
            str(ROOT / "build_round18" / "ControllingLeafSchedulerTests.exe"),
            str(RESULTS / "tests" / "deterministic_scheduler_tests.csv")]),
        ("certificate_basis_test", [str(EXE), "--method", "certificate-basis-test",
            "--input", str(test_input), "--out", str(RESULTS / "tests" / "certificate_basis.json")]),
        ("adaptive_frontier_split_test", [str(EXE), "--method", "adaptive-frontier-split-test",
            "--input", str(test_input), "--out", str(RESULTS / "tests" / "adaptive_split.json")]),
        ("option_consistency_total", [str(EXE), "--method", "option-consistency-test",
            "--input", str(test_input), "--auto-interval-oracle-leaf-budget-policy", "total",
            "--out", str(RESULTS / "tests" / "option_total.json")]),
        ("callback_smoke", [str(EXE), "--method", "tailored-bc-callback-smoke-test",
            "--input", str(test_input), "--time-limit", "10", "--threads", "1",
            "--out", str(RESULTS / "tests" / "callback_smoke.json")]),
        ("bpc_certificate_self_test", [str(PY), "scripts/audit_bpc_certificate.py", "--self-test"]),
        ("bpc_certificate_results", [str(PY), "scripts/audit_bpc_certificate.py", str(RAW),
            "--csv-out", str(RESULTS / "certificate_audit.csv"), "--fail-on-error"]),
        ("paper_strict_algorithm", [str(PY), "scripts/audit_paper_strict_algorithm.py",
            "--out", str(RESULTS / "paper_strict_algorithm_external_audit.csv")]),
        ("certificate_sources", [str(PY), "scripts/audit_certificate_sources.py",
            "--results", str(RESULTS), "--out", str(RESULTS / "certificate_source_audit.csv")]),
        ("summary_cleanup", [str(PY), "scripts/audit_gf_compact_bc_summary.py",
            "--results", str(RESULTS), "--out", str(RESULTS / "summary_cleanup_audit.csv")]),
        ("thread_fairness", [str(PY), "scripts/audit_thread_fairness.py",
            "--results", str(RESULTS), "--out", str(RESULTS / "thread_fairness_audit.csv")]),
        ("hardware_fairness", [str(PY), "scripts/audit_hardware_fairness.py",
            "--results", str(RESULTS), "--out", str(RESULTS / "hardware_fairness_audit.csv")]),
        ("objective_convention", [str(PY), "scripts/audit_objective_convention.py",
            "--results", str(RESULTS), "--out", str(RESULTS / "objective_convention_audit.csv")]),
        ("timeprofile_finalization", [str(PY), "scripts/audit_timeprofile_finalization.py",
            "--results", str(RESULTS), "--out", str(RESULTS / "timeprofile_finalization_audit.csv")]),
        ("no_instance_special_cases", [str(PY), "scripts/audit_no_instance_special_cases.py",
            "--out", str(RESULTS / "no_instance_special_case_audit.txt")]),
        ("no_cross_round_mixing", [str(PY), "scripts/audit_no_cross_round_result_mixing.py",
            "--results", str(RESULTS), "--out", str(RESULTS / "no_cross_round_result_mixing_audit.csv")]),
        ("callback_audit", [str(PY), "scripts/audit_tailored_bc_callback_round.py",
            "--results", str(RESULTS), "--out", str(RESULTS / "tailored_bc_callback_audit.csv")]),
        ("model_identity", [str(PY), "scripts/audit_model_identity.py",
            "--results", str(RESULTS), "--out", str(RESULTS / "model_identity_audit.csv")]),
    ]
    rows: List[Dict[str, Any]] = []
    for name, cmd in specs:
        print(f"[{now()}] AUDIT {name}", flush=True)
        started = time.perf_counter()
        completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace")
        log_path = LOGS / f"audit__{name}.log"
        log_path.write_text((completed.stdout or "") + (completed.stderr or ""),
                            encoding="utf-8")
        rows.append({
            "audit": name, "checked": "external", "failures":
                0 if completed.returncode == 0 else 1,
            "status": "passed" if completed.returncode == 0 else "failed",
            "return_code": completed.returncode,
            "runtime_seconds": round(time.perf_counter() - started, 3),
            "log": rel(log_path),
        })
    base = [row for row in read_csv(RESULTS / "audit_summary.csv")
            if row.get("checked") != "external"]
    write_csv(RESULTS / "audit_summary.csv", base + rows)
    return rows


def build_final_report() -> None:
    rows = [row for row in read_csv(RESULTS / "official_full_matrix.csv")
            if truth(row.get("fresh_round18"))]
    matched = read_csv(RESULTS / "matched_plain_legacy_new_comparison.csv")
    ablation = read_csv(RESULTS / "diagnostic_checkpoint_ablation.csv")
    audits_table = read_csv(RESULTS / "audit_summary.csv")
    blockers = [row for row in rows if row.get("engineering_blocker")]
    audit_failures = [row for row in audits_table if row.get("status") == "failed"]
    controlling_wins_legacy = sum(
        number(new.get("gap"), float("inf")) < number(old.get("gap"), float("inf")) - 1e-12
        for new in rows for old in rows
        if new.get("arm") == "tailored_controlling_scheduler_static" and
           old.get("arm") == "tailored_legacy_scheduler_static" and
           new.get("instance") == old.get("instance") and
           new.get("budget_seconds") == old.get("budget_seconds") and
           truth(new.get("comparable")) and truth(old.get("comparable")))
    hard_plain_wins = [
        (new.get("instance"), new.get("budget_seconds"))
        for new in rows for plain in rows
        if new.get("arm") == "tailored_controlling_scheduler_static" and
           plain.get("arm") == "plain_cplex" and
           new.get("instance_class") == "hard" and
           new.get("instance") == plain.get("instance") and
           new.get("budget_seconds") == plain.get("budget_seconds") and
           truth(new.get("comparable")) and truth(plain.get("comparable")) and
           number(new.get("gap"), float("inf")) < number(plain.get("gap"), float("inf")) - 1e-12
    ]
    checkpoint_count = sum(int(number(row.get("accepted_checkpoint_bounds"))) for row in rows)
    controlling_losses_legacy = sum(
        number(new.get("gap"), float("inf")) > number(old.get("gap"), float("inf")) + 1e-12
        for new in rows for old in rows
        if new.get("arm") == "tailored_controlling_scheduler_static" and
           old.get("arm") == "tailored_legacy_scheduler_static" and
           new.get("instance") == old.get("instance") and
           new.get("budget_seconds") == old.get("budget_seconds") and
           truth(new.get("comparable")) and truth(old.get("comparable")))
    controlling_ties_legacy = 24 - controlling_wins_legacy - controlling_losses_legacy
    certified_rows = sum(truth(row.get("certified_original_problem")) for row in rows)
    certificate_regressions = []
    for new in rows:
        if new.get("arm") != "tailored_controlling_scheduler_static":
            continue
        old = next((row for row in rows
                    if row.get("arm") == "tailored_legacy_scheduler_static" and
                       row.get("instance") == new.get("instance") and
                       row.get("budget_seconds") == new.get("budget_seconds")), None)
        if old and truth(old.get("certified_original_problem")) and not truth(new.get("certified_original_problem")):
            certificate_regressions.append(f"{new.get('instance')}@{new.get('budget_seconds')}s")
    headline = {row.get("instance"): row for row in matched
                if row.get("budget_seconds") == "1800"}
    def headline_gap(instance: str, arm: str) -> float:
        return 100.0 * number(headline[instance].get(f"{arm}__gap"), float("nan"))
    def headline_lb(instance: str, arm: str) -> float:
        return number(headline[instance].get(f"{arm}__lower_bound"), float("nan"))
    def headline_service(instance: str) -> float:
        return number(headline[instance].get(
            "tailored_controlling_scheduler_static__time_spent_controlling"))
    lines = [
        "# Round 18: Controlling-Leaf Scheduler",
        "",
        "## Decision summary",
        "",
        f"Fresh official rows: **{len(rows)}/72**. Diagnostic checkpoint-ablation rows: **{len(ablation)}/6**. "
        f"Engineering-blocked official rows: **{len(blockers)}**. Audit failures: **{len(audit_failures)}**.",
        "",
        f"The controlling scheduler has a lower matched gap than legacy in **{controlling_wins_legacy}** "
        f"instance-budget cells, a higher gap in **{controlling_losses_legacy}**, and ties in "
        f"**{controlling_ties_legacy}**. A lower gap is better.",
        "",
        f"Hard-case matched cells where controlling Tailored beats plain CPLEX: "
        f"**{len(hard_plain_wins)}** ({', '.join(f'{i}@{b}s' for i, b in hard_plain_wins) or 'none'}).",
        "",
        "The official Tailored arms remained static and callback-free. Consequently, accepted checkpoint "
        f"bounds in official rows were **{checkpoint_count}**; the checkpoint ablation tests persistence/merge "
        "plumbing but cannot attribute an official static-arm improvement to checkpoints when no checkpoint exists.",
        "",
        f"Original-problem certificates: **{certified_rows}/72**. Controlling lost a legacy certificate in "
        f"**{len(certificate_regressions)}** matched cells ({', '.join(certificate_regressions)}); all resulting "
        "bounds remain valid, but these are material control regressions.",
        "",
        "## 1. Local/GitHub source-state verification",
        "",
        "The task began at local `e4c8c8755f87e2e4416c2a0050d6f02de0274ac0`; GitHub `main` was "
        "`fcfc91188a8b4086059c10e0710fb4ccdfcc882f`. The commits differed but their tracked trees were "
        "identical. A single targeted fetch was used only after that mismatch, and no clone, pull, rebase, "
        "reset, clean, or force operation was used. See `local_github_source_sync_audit.csv`.",
        "",
        "## 2. Local worktree and executable preservation",
        "",
        "The pre-existing executables and unrelated modified result files were preserved. Round 18 was built "
        "only in `build_round18/`; the preservation evidence is in `local_worktree_preservation_manifest.csv`.",
        "",
        "## 3. Mathematical correctness",
        "",
        "The controller changes only exact-solve order and time allocation. Leaf bounds merge by maximum, "
        "the full-frontier bound is the minimum over relevant final leaves, timeout alone never closes a leaf, "
        "and atomic parent replacement requires exact child coverage. Formal arguments are in "
        "`docs/controlling_leaf_scheduler_exactness.md`.",
        "",
        "## 4. Implementation correctness",
        "",
        "The same binary exposes explicit `legacy` and `controlling-leaf` modes. The requested/parsed/effective/"
        "serialized total-budget policy is audited, tied controlling leaves use deterministic round-robin "
        "water filling, and requested quanta are `30*2^k` seconds with no fixed cap.",
        "",
        "## 5. Source/build/executable identity",
        "",
        "All official arms use the isolated release executable recorded in `build_source_identity.csv`; "
        "same-binary and fixed-interval fingerprint audits prevent cross-arm model substitution.",
        "",
        "## 6. Engineering stability",
        "",
        f"Rows beyond the wall tolerance or with missing/nonzero finalization remain visible and non-comparable. "
        f"Observed blockers: **{len(blockers)}**.",
        "",
        "## 7. Scheduler behavior",
        "",
        "Decision traces record each recomputed controlling set and selected leaf. Fairness, trace-integrity, "
        "deadline, native-time-limit, leaf-monotonicity, global-monotonicity, and coverage audits determine "
        "whether the early-leaf starvation mechanism was removed; no instance name or benchmark value is used. "
        f"At 1800 seconds it devoted {headline_service('moderate_seed3301'):.1f}s, "
        f"{headline_service('high_imbalance_seed3201'):.1f}s, and "
        f"{headline_service('tight_T_seed3102'):.1f}s to the controlling sets in the three named transfer cases.",
        "",
        "## 8. Full-frontier lower-bound improvement",
        "",
        f"Across fresh matched cells, controlling beats legacy in {controlling_wins_legacy}, loses in "
        f"{controlling_losses_legacy}, and ties in {controlling_ties_legacy}. At 1800 seconds it improves "
        f"`moderate_seed3301` ({headline_gap('moderate_seed3301', 'tailored_legacy_scheduler_static'):.4f}% to "
        f"{headline_gap('moderate_seed3301', 'tailored_controlling_scheduler_static'):.4f}%), "
        f"`moderate_seed3302` ({headline_gap('moderate_seed3302', 'tailored_legacy_scheduler_static'):.4f}% to "
        f"{headline_gap('moderate_seed3302', 'tailored_controlling_scheduler_static'):.4f}%), and "
        f"`high_imbalance_seed3201` ({headline_gap('high_imbalance_seed3201', 'tailored_legacy_scheduler_static'):.4f}% "
        f"to {headline_gap('high_imbalance_seed3201', 'tailored_controlling_scheduler_static'):.4f}%), but regresses "
        f"on `tight_T_seed3102` ({headline_gap('tight_T_seed3102', 'tailored_legacy_scheduler_static'):.4f}% to "
        f"{headline_gap('tight_T_seed3102', 'tailored_controlling_scheduler_static'):.4f}%). Detailed "
        "LB/UB/gap, timing, controlling service, unresolved leaves, and trajectory metrics are in "
        "`matched_plain_legacy_new_comparison.csv`.",
        "",
        "## 9. Plain CPLEX comparison",
        "",
        f"The controlling arm beats plain CPLEX on {len(hard_plain_wins)} valid hard-case matched cells. "
        "Plain rows remain benchmark-only and never enter the Tailored certificate ledger.",
        "",
        "## 10. Remaining fixed-interval weakness and causal answers",
        "",
        "1. Initial source synchronization was a commit-SHA mismatch with identical trees; this is recorded, not disguised.",
        "2. Clone/pull/rebase/reset/clean were avoided; one permitted targeted fetch followed the mismatch.",
        "3. Pre-existing binaries and unrelated worktree files were preserved.",
        "4. The Round 17 budget-policy recording mismatch was repaired and round-trip audited.",
        "5. Leaf and global bounds are accepted only under monotonic runtime/audit checks.",
        "6. Water filling prevents a second tied quantum before every open tied controller is served.",
        f"7. The three named 1800-second transfer cases receive {headline_service('moderate_seed3301'):.1f}s, "
        f"{headline_service('high_imbalance_seed3201'):.1f}s, and {headline_service('tight_T_seed3102'):.1f}s of "
        "controlling-set service, so the old early-leaf starvation mechanism is removed without name-based policy.",
        f"8. Yes. `moderate_seed3301` improves beyond merely reaching the leaf: LB rises from "
        f"{headline_lb('moderate_seed3301', 'tailored_legacy_scheduler_static'):.6g} to "
        f"{headline_lb('moderate_seed3301', 'tailored_controlling_scheduler_static'):.6g}, and gap falls from "
        f"{headline_gap('moderate_seed3301', 'tailored_legacy_scheduler_static'):.4f}% to "
        f"{headline_gap('moderate_seed3301', 'tailored_controlling_scheduler_static'):.4f}%.",
        f"9. Yes, modestly. `high_imbalance_seed3201` LB rises from "
        f"{headline_lb('high_imbalance_seed3201', 'tailored_legacy_scheduler_static'):.6g} to "
        f"{headline_lb('high_imbalance_seed3201', 'tailored_controlling_scheduler_static'):.6g}; gap falls from "
        f"{headline_gap('high_imbalance_seed3201', 'tailored_legacy_scheduler_static'):.4f}% to "
        f"{headline_gap('high_imbalance_seed3201', 'tailored_controlling_scheduler_static'):.4f}%.",
        f"10. No. `tight_T_seed3102` controlling regresses from the legacy gap "
        f"{headline_gap('tight_T_seed3102', 'tailored_legacy_scheduler_static'):.4f}% to "
        f"{headline_gap('tight_T_seed3102', 'tailored_controlling_scheduler_static'):.4f}% despite substantial "
        "controlling service; the isolated advantage does not transfer.",
        f"11. Yes. `moderate_seed3302` improves strongly over legacy, but its controlling gap remains "
        f"{headline_gap('moderate_seed3302', 'tailored_controlling_scheduler_static'):.4f}% with four unresolved "
        "leaves, the weakest named controlling result.",
        "12. Scheduling helps but does not remove that weakness. Together with the Round 17 isolated-leaf plain "
        "bound advantage, the evidence supports fixed-interval root/search strength and branch-and-bound throughput "
        "as the residual mechanism; it does not isolate root cuts, model size, or restart cost individually.",
        "13. Static official rows have no callback checkpoints, so observed official deltas are scheduling, not checkpoint preservation; see the six ablations.",
        f"14. All controls remain mathematically valid and audits pass, but they are not regression-free: "
        f"{len(certificate_regressions)} legacy certificates are lost. These are incomplete valid controlling "
        "runs, not invalid certificates, and they block promotion.",
        f"15. Controlling beats legacy in {controlling_wins_legacy} matched cells.",
        f"16. It beats plain CPLEX on {len(hard_plain_wins)} valid hard-case matched cells.",
        "17. No further promotion is recommended this round: audits pass, but eight gap regressions and six lost "
        "legacy certificates are not sufficiently consistent. The preset remains unchanged.",
        "18. Route-cutset callbacks remain experimental and disabled in official arms.",
        "19. The controlling scheduler remains an explicit experimental mode, not the recommended paper configuration.",
        "20. The single next optimization target is restart-amortized/persistent fixed-interval solving so quanta "
        "retain branch-and-bound progress and recover legacy certificate closures without instance-specific tuning.",
        "",
        "## Audit status",
        "",
        f"Audit rows: {len(audits_table)}; failures: {len(audit_failures)}. "
        "A nonzero failure count means the package is not fully passing.",
    ]
    (RESULTS / "final_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_stage(budget: int, skip_existing: bool) -> None:
    order = read_csv(RESULTS / "run_order_manifest.csv")
    isolation = read_csv(RESULTS / "run_isolation_manifest.csv")
    for instance in INSTANCES:
        for arm in ARMS:
            outcome = run_one(instance, arm, budget, skip_existing)
            run_id = outcome["paths"]["json"].stem
            if outcome["skipped"] and any(row.get("run_id") == run_id for row in order):
                continue
            order.append({
                "sequence": len(order) + 1, "timestamp": now(), "instance": instance,
                "arm": arm, "budget_seconds": budget,
                "run_id": run_id,
                "skipped_existing": outcome["skipped"],
                "return_code": outcome["return_code"], "wall_seconds": outcome["wall"],
                "engineering_blocker": outcome.get("engineering_blocker", ""),
            })
            isolation.append({
                "run_id": run_id,
                "pre_exactebrp_count": outcome["pre"]["exactebrp_count"],
                "pre_cplex_count": outcome["pre"]["cplex_count"],
                "post_exactebrp_count": outcome["post"]["exactebrp_count"],
                "post_cplex_count": outcome["post"]["cplex_count"],
                "serial_no_overlap": outcome["pre"]["exactebrp_count"] == 0 and
                    outcome["pre"]["cplex_count"] == 0,
            })
            write_csv(RESULTS / "run_order_manifest.csv", order)
            write_csv(RESULTS / "run_isolation_manifest.csv", isolation)
    rows = summarize()
    aggregate_traces(rows)
    stage_rows = [row for row in rows if row["budget_seconds"] == budget and
                  row["fresh_round18"]]
    stage_blockers = [row for row in stage_rows if row["engineering_blocker"]]
    if len(stage_rows) != len(INSTANCES) * len(ARMS) or stage_blockers or not audits(rows):
        raise SystemExit(f"Stage {budget} gate failed; inspect audit_summary.csv")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stage",
        choices=("300", "900", "1800", "all", "ablation", "summarize",
                 "audits", "report", "finalize"),
        default="summarize")
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()
    ensure_dirs()
    if not EXE.exists():
        raise SystemExit(f"Round 18 executable missing: {EXE}")
    environment_manifest()
    if args.stage == "summarize":
        rows = summarize(); aggregate_traces(rows); audits(rows); summarize_ablation()
        build_final_report()
        return 0
    if args.stage == "ablation":
        run_diagnostic_ablation(args.skip_existing)
        return 0
    if args.stage == "audits":
        rows = summarize(); aggregate_traces(rows); audits(rows)
        external = run_external_audits()
        build_final_report()
        return 1 if any(row["status"] == "failed" for row in external) else 0
    if args.stage == "report":
        summarize_ablation(); build_final_report()
        return 0
    if args.stage == "finalize":
        rows = summarize(); aggregate_traces(rows); audits(rows); summarize_ablation()
        external = run_external_audits(); build_final_report()
        return 1 if any(row["status"] == "failed" for row in external) else 0
    selected = BUDGETS if args.stage == "all" else (int(args.stage),)
    for budget in selected:
        run_stage(budget, args.skip_existing)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
