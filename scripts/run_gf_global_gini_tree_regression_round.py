#!/usr/bin/env python3
"""Round 20 serial experiments, forensic extraction, and fail-closed audits."""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple


ROOT = Path(__file__).resolve().parents[1]
ROUND = "gf_global_gini_tree_regression_round"
RESULTS = ROOT / "results" / ROUND
RAW = RESULTS / "raw"
LOGS = RESULTS / "logs"
COMMANDS = RESULTS / "commands"
RUNS = RESULTS / "runs"
AUDITS = RESULTS / "audits"
DIAGNOSTICS = RESULTS / "diagnostic_models"
INTERRUPTED = RESULTS / "interrupted"
EXE = ROOT / "build_round20" / "ExactEBRP.exe"
UNIT = ROOT / "build_round20" / "GlobalGiniTreeTests.exe"
PROCESS_TOLERANCE = 30

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
FORENSIC = (
    "tight_T_seed3101", "high_imbalance_seed3202", "V12_M2",
    "moderate_seed3302", "V12_M1", "tight_T_seed3102",
)
STAGE1 = ("tight_T_seed3101", "high_imbalance_seed3202", "V12_M2", "moderate_seed3302")
STAGE3 = ("tight_T_seed3101", "high_imbalance_seed3202", "moderate_seed3302", "tight_T_seed3102")

ARMS: Dict[str, Dict[str, str]] = {
    "baseline": {"estimate": "parent-copy", "rows": "full-inherited-pack", "timing": "deferred", "mip": "false"},
    "factory_full": {"estimate": "factory-domain", "rows": "full-inherited-pack", "timing": "deferred", "mip": "false"},
    "parent_delta": {"estimate": "parent-copy", "rows": "exact-incremental-delta", "timing": "deferred", "mip": "false"},
    "factory_delta": {"estimate": "factory-domain", "rows": "exact-incremental-delta", "timing": "deferred", "mip": "false"},
    "eager_only": {"estimate": "parent-copy", "rows": "full-inherited-pack", "timing": "eager", "mip": "false"},
    "mip_start_only": {"estimate": "parent-copy", "rows": "full-inherited-pack", "timing": "deferred", "mip": "true"},
    "delta_eager": {"estimate": "parent-copy", "rows": "exact-incremental-delta", "timing": "eager", "mip": "false"},
    "delta_eager_mip": {"estimate": "parent-copy", "rows": "exact-incremental-delta", "timing": "eager", "mip": "true"},
    "root_flow_only": {"estimate": "parent-copy", "rows": "full-inherited-pack", "timing": "deferred", "mip": "false", "root_flow": "true"},
}
STAGE1_ARMS = ("baseline", "factory_full", "parent_delta", "factory_delta")
THRESHOLDS = (0.20, 0.10, 0.05, 0.01, 0.0)
CPLEX = Path(r"C:\Program Files\IBM\ILOG\CPLEX_Studio2211\cplex\bin\x64_win64\cplex.exe")
DIAGNOSTIC_INTERVALS: Dict[str, Tuple[int, float, float]] = {
    "tight_T_seed3101": (0, 0.0, 0.026813183533485361),
    "high_imbalance_seed3202": (0, 0.0, 0.23749999999999999),
    "V12_M2": (4, 0.35925203537748546, 0.44906504422185678),
    "moderate_seed3302": (4, 0.0, 0.024454525818626546),
}


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dirs() -> None:
    for path in (RESULTS, RAW, LOGS, COMMANDS, RUNS, AUDITS, DIAGNOSTICS, INTERRUPTED):
        path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if isinstance(value, dict) and isinstance(value.get("results"), list):
        return value["results"][0] if value["results"] else {}
    return value if isinstance(value, dict) else {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: Sequence[str] = ()) -> None:
    material = list(rows)
    names = list(fields)
    for row in material:
        for key in row:
            if key not in names:
                names.append(key)
    if not names:
        names = ["status", "reason"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=names, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)


def number(value: Any, default: float = math.nan) -> float:
    try:
        result = float(value)
        return result
    except (TypeError, ValueError):
        return default


def truth(value: Any) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes"}


def paths(run_id: str) -> Dict[str, Path]:
    run = RUNS / run_id
    return {
        "run": run, "json": RAW / f"{run_id}.json", "log": LOGS / f"{run_id}.log",
        "command": COMMANDS / f"{run_id}.json", "progress": run / "progress.csv",
        "node": run / "global_node_trace.csv", "bound": run / "global_bound_trajectory.csv",
        "root": run / "global_root.lp", "manifest": run / "model_lifecycle_manifest.csv",
        "post": run / "post_local_row_trace.csv", "topology": run / "gini_topology.csv",
        "sibling": run / "sibling_delay.csv", "delta": run / "row_delta.csv",
        "memory": run / "tree_memory.csv", "mip": run / "mip_start_audit.csv",
    }


def callback_off_flags() -> List[str]:
    return [
        "--tailored-bc-branching-priority", "off", "--tailored-bc-gini-branching", "off",
        "--tailored-bc-gini-subset-envelope", "false", "--tailored-bc-low-gini-l1-centering", "false",
        "--tailored-bc-local-centering", "false", "--tailored-bc-subset-cross-h-centering", "false",
        "--tailored-bc-local-q-centering", "false", "--tailored-bc-subset-inventory-imbalance", "false",
        "--tailored-bc-transfer-cutset", "false", "--tailored-bc-gs-product-coupling", "false",
        "--tailored-bc-disaggregated-sp-estimator", "false", "--tailored-bc-bucket-ratio-domain-tightening", "false",
        "--tailored-bc-bucket-subset-ratio-domain", "false", "--tailored-bc-bucket-integer-inventory-domain", "false",
        "--tailored-bc-bucket-required-movement", "false", "--tailored-bc-bucket-required-visit", "false",
        "--tailored-bc-s-bucket-ledger", "off",
    ]


def frozen_static_flags() -> List[str]:
    return [
        "--tailored-bc-enabled", "true", "--tailored-bc-mode", "static",
        "--tailored-bc-callback-cut-profile", "off", "--compact-bc-root-cut-rounds", "0",
        "--compact-bc-dynamic-cut-families", "none", "--compact-bc-cut-profile", "balanced",
        "--compact-bc-low-gini-strengthening", "safe", "--compact-bc-denominator-bound-mode", "tight",
        "--compact-bc-objective-estimator-mode", "adaptive", "--compact-bc-domain-propagation-mode", "iterative",
        "--compact-bc-domain-propagation-rounds", "2", "--compact-bc-variable-s-centering", "true",
        "--compact-bc-sp-product-estimator", "paper-safe", "--compact-bc-sp-product-bounds", "tight",
        "--compact-bc-s-range-refinement", "off",
    ] + callback_off_flags()


def base_tailored(instance: str, budget: int, p: Dict[str, Path]) -> List[str]:
    return [
        str(EXE), "--method", "gcap-frontier", "--algorithm-preset", "paper-gf-tailored-bc",
        "--paper-run-sealed", "true", "--input", str(ROOT / INSTANCES[instance]["path"]),
        "--lambda", "0.15", "--T", "3600", "--time-limit", str(budget),
        "--process-wall-time-limit", str(budget), "--threads", "1", "--mip-threads", "1",
        "--compact-bc-threads", "1", "--cplex-threads", "1", "--primal-heuristic", "hga-tgbc",
        "--progress-log", str(p["progress"]), "--progress-interval-seconds", "30",
        "--log", str(p["log"]), "--out", str(p["json"]),
    ] + frozen_static_flags()


def global_command(instance: str, arm: str, budget: int, p: Dict[str, Path], presolve: str = "on") -> List[str]:
    spec = ARMS[arm]
    return base_tailored(instance, budget, p) + [
        "--frontier-execution-mode", "global-gini-tree", "--global-gini-tree-presolve", presolve,
        "--global-gini-tree-search", "traditional", "--global-gini-tree-child-estimate", spec["estimate"],
        "--global-gini-tree-row-attachment", spec["rows"], "--global-gini-tree-row-timing", spec["timing"],
        "--global-gini-tree-native-mip-start", spec["mip"], "--global-gini-tree-node-trace", str(p["node"]),
        "--global-gini-tree-root-connectivity-flow", spec.get("root_flow", "false"),
        "--global-gini-tree-bound-trace", str(p["bound"]), "--global-gini-tree-manifest", str(p["manifest"]),
        "--global-gini-tree-root-export", str(p["root"]), "--global-gini-tree-post-row-trace", str(p["post"]),
        "--global-gini-tree-topology-trace", str(p["topology"]), "--global-gini-tree-sibling-trace", str(p["sibling"]),
        "--global-gini-tree-row-delta-trace", str(p["delta"]), "--global-gini-tree-memory-trace", str(p["memory"]),
        "--global-gini-tree-mip-start-audit", str(p["mip"]),
    ]


def plain_command(instance: str, budget: int, p: Dict[str, Path]) -> List[str]:
    return [
        str(EXE), "--method", "cplex", "--plain-baseline", "--input", str(ROOT / INSTANCES[instance]["path"]),
        "--lambda", "0.15", "--T", "3600", "--time-limit", str(budget), "--threads", "1",
        "--cplex-threads", "1", "--mip-threads", "1", "--progress-log", str(p["progress"]),
        "--progress-interval-seconds", "30", "--log", str(p["log"]), "--out", str(p["json"]),
    ]


def legacy_command(instance: str, budget: int, p: Dict[str, Path]) -> List[str]:
    return base_tailored(instance, budget, p) + [
        "--frontier-scheduling-mode", "legacy", "--auto-interval-oracle-leaf-budget-policy", "total",
        "--auto-interval-oracle-total-budget", str(budget),
    ]


def command_for(instance: str, arm: str, budget: int, p: Dict[str, Path], presolve: str = "on") -> List[str]:
    if arm == "plain":
        return plain_command(instance, budget, p)
    if arm == "legacy":
        return legacy_command(instance, budget, p)
    return global_command(instance, arm, budget, p, presolve)


def process_snapshot() -> Dict[str, Any]:
    answer = {"exactebrp_count": 0, "cplex_count": 0, "source": "tasklist"}
    try:
        text = subprocess.check_output(["tasklist", "/FO", "CSV", "/NH"], text=True, errors="replace")
        names = [line.split(",", 1)[0].strip('"').lower() for line in text.splitlines()]
        answer["exactebrp_count"] = sum(name.startswith("exactebrp") for name in names)
        answer["cplex_count"] = sum(name == "cplex.exe" for name in names)
    except Exception as exc:
        answer["source"] = f"snapshot_failed:{exc}"
    return answer


def stamp_result(path: Path, run_id: str, instance: str, arm: str, budget: int) -> None:
    data = read_json(path)
    if not data:
        return
    data.update({
        "source_round": ROUND, "fresh_run": True, "result_package": rel(RESULTS),
        "round20_run_id": run_id, "round20_instance": instance, "round20_arm": arm,
        "round20_budget_seconds": budget,
    })
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def archive_attempt(run_id: str, p: Dict[str, Path], reason: str) -> Path:
    root = INTERRUPTED / run_id
    index = 1
    while (root / f"attempt_{index}").exists():
        index += 1
    target = root / f"attempt_{index}"
    target.mkdir(parents=True, exist_ok=True)
    for key in ("command", "log", "json"):
        source = p[key]
        if source.exists():
            shutil.copy2(source, target / source.name)
    if p["run"].exists():
        shutil.copytree(p["run"], target / "run_artifacts", dirs_exist_ok=True)
    (target / "archive_reason.txt").write_text(reason + "\n", encoding="utf-8")
    return target


def clear_active_attempt(p: Dict[str, Path]) -> None:
    """Clear only an already archived Round 20 attempt before a fresh run."""
    for key in ("command", "log", "json"):
        try:
            p[key].unlink()
        except FileNotFoundError:
            pass
    if p["run"].exists():
        shutil.rmtree(p["run"])


def usable_completed_result(data: Dict[str, Any], arm: str) -> bool:
    if not data or not truth(data.get("fresh_run")):
        return False
    status = str(data.get("status", "")).lower()
    if "error" in status or truth(data.get("global_gini_tree_callback_abort_used")):
        return False
    if arm in ARMS:
        return (truth(data.get("global_gini_tree_solver_finalization_reached")) and
                truth(data.get("global_gini_tree_lifecycle_valid")) and
                truth(data.get("global_gini_tree_native_best_bound_available")) and
                number(data.get("global_gini_tree_mipopt_count"), 0) == 1 and
                not str(data.get("global_gini_tree_fail_reason", "")))
    return True


def run_one(run_id: str, instance: str, arm: str, budget: int, presolve: str = "on", skip: bool = True) -> Dict[str, Any]:
    p = paths(run_id)
    executable_hash = sha256(EXE)
    existing = read_json(p["json"])
    previous = read_json(p["command"])
    same_binary = previous.get("executable_sha256") == executable_hash
    if skip and same_binary and usable_completed_result(existing, arm):
        return {"run_id": run_id, "skipped": True, "return_code": 0}
    reasons: List[str] = []
    if existing and not usable_completed_result(existing, arm):
        reasons.append("retained JSON was not solver-final usable evidence")
    if existing and not same_binary:
        reasons.append("retained evidence was produced by a different executable hash")
    if previous and (truth(previous.get("runner_timeout")) or
                     number(previous.get("return_code"), 0) != 0):
        reasons.append("previous runner attempt did not finish cleanly")
    if existing or previous or p["run"].exists() or p["log"].exists():
        archive_attempt(run_id, p, "archived automatically before retry: " +
                        "; ".join(reasons or ["explicit fresh rerun"]))
        clear_active_attempt(p)
    p["run"].mkdir(parents=True, exist_ok=True)
    cmd = command_for(instance, arm, budget, p, presolve)
    before = process_snapshot()
    record: Dict[str, Any] = {
        "run_id": run_id, "instance": instance, "instance_class": INSTANCES[instance]["class"],
        "arm": arm, "budget_seconds": budget, "presolve": presolve, "start_time": now(),
        "command": cmd, "command_line": subprocess.list2cmdline(cmd), "executable": rel(EXE),
        "executable_sha256": executable_hash, "pre_process_snapshot": before,
        "stale_process_detected": bool(before["exactebrp_count"] or before["cplex_count"]),
    }
    p["command"].write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if record["stale_process_detected"]:
        record.update({"return_code": -99, "engineering_blocker": "stale_solver_process"})
        p["command"].write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return record
    print(f"[{now()}] START {run_id}", flush=True)
    started = time.perf_counter()
    timed_out = False
    try:
        completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=budget + PROCESS_TOLERANCE)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        completed = subprocess.CompletedProcess(cmd, -98, exc.stdout or "", exc.stderr or "")
    wall = time.perf_counter() - started
    with p["log"].open("a", encoding="utf-8") as stream:
        stream.write("\n--- ROUND20 RUNNER STDOUT ---\n" + completed.stdout)
        stream.write("\n--- ROUND20 RUNNER STDERR ---\n" + completed.stderr)
    record.update({
        "end_time": now(), "actual_process_wall_seconds": wall, "return_code": completed.returncode,
        "runner_timeout": timed_out, "post_process_snapshot": process_snapshot(),
        "engineering_blocker": "runner_emergency_timeout" if timed_out else "",
    })
    p["command"].write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    stamp_result(p["json"], run_id, instance, arm, budget)
    if timed_out:
        archive_attempt(run_id, p, "runner emergency timeout after solver budget plus cleanup tolerance")
    print(f"[{now()}] END {run_id} rc={completed.returncode} wall={wall:.3f}s", flush=True)
    return record


def selected_arm() -> str:
    data = read_json(RESULTS / "selection.json")
    arm = str(data.get("selected_arm", ""))
    if arm not in ARMS:
        raise RuntimeError("No evidence-gated selected arm. Run select --arm <arm> after Stage 1.")
    return arm


def phase_tests() -> None:
    ensure_dirs()
    rows: List[Dict[str, Any]] = []
    completed = subprocess.run([str(UNIT)], cwd=ROOT, capture_output=True, text=True, errors="replace")
    (AUDITS / "cpp_unit_tests.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    rows.append({"test": "cpp_global_gini_tree_tests", "status": "passed" if completed.returncode == 0 else "failed",
                 "detail": completed.stdout.strip()})
    python_test = subprocess.run(
        [sys.executable, str(ROOT / "tests/round20_regression_tests.py")],
        cwd=ROOT, capture_output=True, text=True, errors="replace")
    (AUDITS / "python_round20_regression_tests.log").write_text(
        python_test.stdout + python_test.stderr, encoding="utf-8")
    rows.append({"test": "python_round20_regression_tests",
                 "status": "passed" if python_test.returncode == 0 else "failed",
                 "detail": (python_test.stdout + python_test.stderr).strip()})
    invalid = subprocess.run([str(EXE), "--method", "option-consistency-test", "--input",
                              str(ROOT / INSTANCES["V12_M1"]["path"]), "--lambda", "-0.1", "--T", "3600"],
                             cwd=ROOT, capture_output=True, text=True, errors="replace")
    rows.append({"test": "negative_lambda_rejected", "status": "passed" if invalid.returncode != 0 else "failed",
                 "detail": (invalid.stderr + invalid.stdout)[-500:]})
    source = (ROOT / "src/TailoredBCCplexApi.cpp").read_text(encoding="utf-8")
    forbidden = ["tight_T_seed", "high_imbalance_seed", "moderate_seed", "regen_candidate", "known_objective"]
    hits = [token for token in forbidden if token in source]
    rows.append({"test": "no_instance_or_known_objective_logic", "status": "passed" if not hits else "failed",
                 "detail": "|".join(hits)})
    write_csv(AUDITS / "mechanical_tests.csv", rows)
    if any(row["status"] != "passed" for row in rows):
        raise RuntimeError("mechanical tests failed")


def phase_gates() -> None:
    for instance in FORENSIC:
        for presolve in ("on", "off"):
            run_one(f"gate__{instance}__baseline__presolve_{presolve}__30s", instance, "baseline", 30, presolve)
    summarize()


def phase_forensic() -> None:
    for instance in FORENSIC:
        run_one(f"forensic__{instance}__baseline__300s", instance, "baseline", 300)
    for instance in ("tight_T_seed3101", "high_imbalance_seed3202", "V12_M2", "moderate_seed3302"):
        run_one(f"legacy_forensic__{instance}__legacy__300s", instance, "legacy", 300)
    collect_legacy_models()
    summarize()


def phase_stage1(instances: Sequence[str]) -> None:
    for instance in instances:
        for arm in STAGE1_ARMS:
            run_one(f"stage1__{instance}__{arm}__300s", instance, arm, 300)
    summarize()


def phase_optional(arms: Sequence[str], instances: Sequence[str]) -> None:
    for arm in arms:
        if arm not in ARMS or arm in STAGE1_ARMS:
            raise ValueError(f"invalid optional arm: {arm}")
        for instance in instances:
            run_one(f"optional__{instance}__{arm}__300s", instance, arm, 300)
    summarize()


def verified_cutoff(instance: str) -> float:
    candidates = [
        RAW / f"forensic__{instance}__baseline__300s.json",
        RAW / f"mechanism_gate__{instance}__parent_delta__30s.json",
    ]
    for path in candidates:
        data = read_json(path)
        value = number(data.get("objective"))
        if math.isfinite(value) and value > 0.0:
            return value
    raise RuntimeError(f"no independently verified cutoff is available for {instance}")


def diagnostic_compact_command(instance: str, lower: float, upper: float,
                               budget: int, directory: Path) -> List[str]:
    return [
        str(EXE), "--method", "interval-cutoff-oracle",
        "--algorithm-preset", "paper-gf-tailored-bc", "--paper-run-sealed", "true",
        "--input", str(ROOT / INSTANCES[instance]["path"]), "--lambda", "0.15",
        "--T", "3600", "--time-limit", str(budget),
        "--process-wall-time-limit", str(budget), "--threads", "1",
        "--mip-threads", "1", "--compact-bc-threads", "1", "--cplex-threads", "1",
        "--primal-heuristic", "hga-tgbc", "--interval-exact-cutoff-oracle", "compact-mip",
        "--interval-exact-oracle-mode", "objective-bound",
        "--interval-oracle-objective-cutoff-row", "true",
        "--interval-exact-cutoff-gamma-L", format(lower, ".17g"),
        "--interval-exact-cutoff-gamma-U", format(upper, ".17g"),
        "--interval-exact-cutoff-UB", format(verified_cutoff(instance), ".17g"),
        "--interval-exact-cutoff-time-limit", str(budget),
        "--compact-bc-time-limit", str(budget),
        "--interval-exact-cutoff-export-lp", str(directory / "fixed_interval_factory.lp"),
        "--interval-exact-cutoff-result", str(directory / "fixed_interval_factory.sol"),
        "--log", str(directory / "fixed_interval_factory.log"),
        "--out", str(directory / "fixed_interval_factory.json"),
    ] + frozen_static_flags()


def run_diagnostic_process(run_id: str, cmd: Sequence[str], budget: int,
                           directory: Path) -> Dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    command_path = directory / "command.json"
    stdout_path = directory / "runner_output.log"
    current_hash = sha256(EXE)
    previous = read_json(command_path)
    result_path = directory / "fixed_interval_factory.json"
    if (previous.get("executable_sha256") == current_hash and
            previous.get("return_code") == 0 and result_path.exists()):
        return previous
    before = process_snapshot()
    record: Dict[str, Any] = {
        "run_id": run_id, "start_time": now(), "command": list(cmd),
        "command_line": subprocess.list2cmdline(list(cmd)),
        "executable_sha256": current_hash, "budget_seconds": budget,
        "pre_process_snapshot": before,
        "stale_process_detected": bool(before["exactebrp_count"] or before["cplex_count"]),
    }
    command_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if record["stale_process_detected"]:
        record.update({"return_code": -99, "engineering_blocker": "stale_solver_process"})
        command_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return record
    started = time.perf_counter()
    try:
        completed = subprocess.run(list(cmd), cwd=ROOT, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=budget + PROCESS_TOLERANCE)
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        completed = subprocess.CompletedProcess(cmd, -98, exc.stdout or "", exc.stderr or "")
        timed_out = True
    captured = completed.stdout + "\n--- STDERR ---\n" + completed.stderr
    stdout_path.write_text(captured, encoding="utf-8")
    # The fixed-interval native C API reports directly on stdout.  Preserve a
    # deterministic formulation-local CPLEX log alongside the model, matching
    # the result JSON's declared log path.
    (directory / "fixed_interval_factory.log").write_text(captured, encoding="utf-8")
    record.update({"end_time": now(), "actual_process_wall_seconds": time.perf_counter() - started,
                   "return_code": completed.returncode, "runner_timeout": timed_out,
                   "post_process_snapshot": process_snapshot(),
                   "engineering_blocker": "runner_emergency_timeout" if timed_out else ""})
    command_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def run_legacy_lp_diagnostic(instance: str, interval_id: int, budget: int,
                             directory: Path) -> Dict[str, Any]:
    source = (DIAGNOSTICS / "inventory_route_gini_relaxation" / instance /
              f"interval_{interval_id}" / "inventory_gini_bound.lp")
    directory.mkdir(parents=True, exist_ok=True)
    command_file = directory / "run.cplex"
    log_path = directory / "legacy_relaxation.log"
    record_path = directory / "command.json"
    if not source.exists() or not CPLEX.exists():
        record = {"run_id": f"diagnostic_legacy__{instance}__interval_{interval_id}",
                  "return_code": -97, "engineering_blocker":
                  "missing_source_lp" if not source.exists() else "missing_cplex_executable"}
        record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return record
    source_hash = sha256(source)
    previous = read_json(record_path)
    if (previous.get("source_lp_sha256") == source_hash and
            previous.get("return_code") == 0 and log_path.exists()):
        return previous
    command_file.write_text(
        "set threads 1\nset timelimit " + str(budget) +
        "\nset mip tolerances mipgap 0\nset mip strategy search 1\n"
        "set mip strategy nodeselect 1\nread \"" + str(source.resolve()) +
        "\"\noptimize\nquit\n", encoding="utf-8")
    before = process_snapshot()
    record: Dict[str, Any] = {
        "run_id": f"diagnostic_legacy__{instance}__interval_{interval_id}",
        "start_time": now(), "source_lp": rel(source), "source_lp_sha256": source_hash,
        "cplex": str(CPLEX), "budget_seconds": budget,
        "command": [str(CPLEX), "-f", str(command_file)],
        "pre_process_snapshot": before,
        "stale_process_detected": bool(before["exactebrp_count"] or before["cplex_count"]),
    }
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if record["stale_process_detected"]:
        record.update({"return_code": -99, "engineering_blocker": "stale_solver_process"})
        record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return record
    started = time.perf_counter()
    try:
        completed = subprocess.run(record["command"], cwd=ROOT, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=budget + PROCESS_TOLERANCE)
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        completed = subprocess.CompletedProcess(record["command"], -98,
                                                exc.stdout or "", exc.stderr or "")
        timed_out = True
    log_path.write_text(completed.stdout + "\n--- STDERR ---\n" + completed.stderr,
                        encoding="utf-8")
    record.update({"end_time": now(), "actual_process_wall_seconds": time.perf_counter() - started,
                   "return_code": completed.returncode, "runner_timeout": timed_out,
                   "post_process_snapshot": process_snapshot(),
                   "engineering_blocker": "runner_emergency_timeout" if timed_out else ""})
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def phase_interval_diagnostics() -> None:
    budget = 60
    for instance, (interval_id, lower, upper) in DIAGNOSTIC_INTERVALS.items():
        root = DIAGNOSTICS / "matched_interval" / instance / f"interval_{interval_id}"
        run_legacy_lp_diagnostic(instance, interval_id, budget, root / "A_legacy_relaxation")
        compact = root / "B_factory_preloaded"
        run_diagnostic_process(
            f"diagnostic_factory__{instance}__interval_{interval_id}__{budget}s",
            diagnostic_compact_command(instance, lower, upper, budget, compact),
            budget, compact)
        run_one(f"diagnostic_eager__{instance}__eager_only__{budget}s",
                instance, "eager_only", budget)
    build_forensic_tables()
    summarize()


def phase_stage2(instances: Sequence[str]) -> None:
    chosen = selected_arm()
    for instance in instances:
        run_one(f"stage2__{instance}__baseline__900s", instance, "baseline", 900)
        run_one(f"stage2__{instance}__{chosen}__900s", instance, chosen, 900)
        run_one(f"stage2__{instance}__plain__900s", instance, "plain", 900)
    summarize()


def phase_stage3(instances: Sequence[str]) -> None:
    chosen = selected_arm()
    for instance in instances:
        run_one(f"stage3__{instance}__{chosen}__1800s", instance, chosen, 1800)
        run_one(f"stage3__{instance}__plain__1800s", instance, "plain", 1800)
    summarize()


INTERVAL_NOTE = re.compile(
    r"(?:interval|child interval)\s+(?P<id>\d+).*?interval=\[(?P<L>[-+0-9.eE]+),(?P<U>[-+0-9.eE]+)\].*?"
    r"objective_lb=(?P<lb>[-+0-9.eE]+),\s*lp=(?P<lp>[^,]+)", re.DOTALL)


def resolve_note_path(raw: str) -> Path:
    value = raw.strip().replace("\\", os.sep)
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def collect_legacy_models() -> None:
    records: List[Dict[str, Any]] = []
    for instance in ("tight_T_seed3101", "high_imbalance_seed3202", "V12_M2", "moderate_seed3302"):
        run_id = f"legacy_forensic__{instance}__legacy__300s"
        data = read_json(paths(run_id)["json"])
        for note in data.get("notes", []):
            match = INTERVAL_NOTE.search(str(note))
            if not match:
                continue
            lp = resolve_note_path(match.group("lp"))
            target = DIAGNOSTICS / "inventory_route_gini_relaxation" / instance / f"interval_{match.group('id')}"
            target.mkdir(parents=True, exist_ok=True)
            if lp.exists():
                for source in lp.parent.iterdir():
                    if source.is_file():
                        shutil.copy2(source, target / source.name)
            records.append({
                "instance": instance, "interval_id": int(match.group("id")),
                "gamma_L": match.group("L"), "gamma_U": match.group("U"),
                "objective_lb": match.group("lb"), "source_lp": rel(lp),
                "copied_directory": rel(target), "lp_sha256": sha256(lp) if lp.exists() else "",
                "status": "copied" if lp.exists() else "missing",
            })
    write_csv(AUDITS / "legacy_interval_model_index.csv", records)


LP_TOKEN = re.compile(r"(?<![0-9.])[A-Za-z][A-Za-z0-9_]*")
LP_SECTION_WORDS = {
    "Minimize", "Maximize", "Subject", "To", "Bounds", "Binaries", "Binary",
    "Generals", "General", "End", "obj", "inf",
}


def variable_family(name: str) -> str:
    return re.sub(r"(?:_[0-9]+)+$", "", name)


def lp_inventory(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"model_status": "missing", "model_path": rel(path)}
    text = path.read_text(encoding="utf-8", errors="replace")
    section = ""
    objective: List[str] = []
    rows: List[str] = []
    current_row = ""
    bounds: List[str] = []
    binary: set[str] = set()
    general: set[str] = set()
    variables: set[str] = set()

    def tokens(line: str) -> List[str]:
        found = LP_TOKEN.findall(line)
        return [value for value in found if value not in LP_SECTION_WORDS and
                not re.fullmatch(r"c[0-9]+", value)]

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("\\"):
            continue
        lower = line.lower()
        if lower in {"minimize", "maximize"}:
            if current_row:
                rows.append(current_row)
                current_row = ""
            section = "objective"
            continue
        if lower in {"subject to", "such that", "st"}:
            section = "rows"
            continue
        if lower == "bounds":
            if current_row:
                rows.append(current_row)
                current_row = ""
            section = "bounds"
            continue
        if lower in {"binaries", "binary"}:
            section = "binary"
            continue
        if lower in {"generals", "general", "integers"}:
            section = "general"
            continue
        if lower == "end":
            if current_row:
                rows.append(current_row)
            break
        if section == "objective":
            objective.append(line)
            variables.update(tokens(line))
        elif section == "rows":
            if re.match(r"^[A-Za-z][A-Za-z0-9_]*\s*:", line):
                if current_row:
                    rows.append(current_row)
                current_row = line
            else:
                current_row += " " + line
            row_body = line.split(":", 1)[-1]
            variables.update(tokens(row_body))
        elif section == "bounds":
            bounds.append(line)
            variables.update(tokens(line))
        elif section == "binary":
            values = tokens(line)
            binary.update(values)
            variables.update(values)
        elif section == "general":
            values = tokens(line)
            general.update(values)
            variables.update(values)

    type_counts: collections.Counter[Tuple[str, str]] = collections.Counter()
    family_counts: collections.Counter[str] = collections.Counter()
    for name in variables:
        family = variable_family(name)
        kind = "binary" if name in binary else ("integer" if name in general else "continuous")
        type_counts[(family, kind)] += 1
        family_counts[family] += 1
    bound_counts: collections.Counter[str] = collections.Counter()
    for line in bounds:
        for name in set(tokens(line)):
            if name in variables:
                bound_counts[variable_family(name)] += 1
    nonzeros = 0
    normalized_rows: List[str] = []
    for row in rows:
        body = row.split(":", 1)[-1]
        row_vars = [name for name in tokens(body) if name in variables]
        nonzeros += len(row_vars)
        normalized_rows.append(" ".join(body.split()))
    objective_text = " ".join(" ".join(line.split()) for line in objective)
    family_text = "|".join(f"{family}:{kind}:{count}"
                           for (family, kind), count in sorted(type_counts.items()))
    return {
        "model_status": "present", "model_path": rel(path),
        "model_sha256": sha256(path), "model_bytes": path.stat().st_size,
        "variables": len(variables), "rows": len(rows), "nonzeros": nonzeros,
        "continuous_variables": sum(1 for name in variables if name not in binary and name not in general),
        "integer_variables": len(general), "binary_variables": len(binary),
        "variables_by_family_integrality": family_text,
        "bounds_by_family": "|".join(f"{key}:{value}" for key, value in sorted(bound_counts.items())),
        "objective_fingerprint": hashlib.sha256(objective_text.encode()).hexdigest(),
        "row_signature": hashlib.sha256("\n".join(normalized_rows).encode()).hexdigest(),
        "family_signature": hashlib.sha256(family_text.encode()).hexdigest(),
    }


def cplex_log_metrics(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"log_status": "missing", "log_path": rel(path)}
    text = path.read_text(encoding="utf-8", errors="replace")
    removed = re.findall(
        r"(?:Presolve removed|MIP Presolve eliminated)\s+(\d+)\s+rows and\s+(\d+)\s+columns",
        text)
    substitutions = [int(value) for value in re.findall(r"Aggregator did\s+(\d+)\s+substitutions", text)]
    coefficient_changes = [int(value) for value in re.findall(
        r"MIP Presolve modified\s+(\d+)\s+coefficients", text)]
    node_zero = []
    for line in text.splitlines():
        match = re.match(r"^\s*0\s+0\s+([-+0-9.eE]+)", line)
        if match:
            try:
                node_zero.append(float(match.group(1)))
            except ValueError:
                pass
    best_bounds = [number(value) for value in re.findall(
        r"Best bound\s*=\s*([-+0-9.eE]+)", text, re.IGNORECASE)]
    cut_pairs = re.findall(r"^\s*([A-Za-z][A-Za-z -]+ cuts) applied:\s+(\d+)",
                           text, re.MULTILINE)
    reduced = re.findall(
        r"Reduced MIP has\s+(\d+)\s+rows,\s+(\d+)\s+columns, and\s+(\d+)\s+nonzeros", text)
    tree_memory = [number(value) for value in re.findall(r"tree\s*=\s*([0-9.]+)\s*MB", text)]
    return {
        "log_status": "present", "log_path": rel(path), "log_sha256": sha256(path),
        "presolve_eliminated_rows": sum(int(pair[0]) for pair in removed),
        "presolve_eliminated_columns": sum(int(pair[1]) for pair in removed),
        "presolve_substitutions": sum(substitutions),
        "presolve_coefficient_changes": sum(coefficient_changes),
        "presolved_rows": int(reduced[-1][0]) if reduced else "",
        "presolved_columns": int(reduced[-1][1]) if reduced else "",
        "presolved_nonzeros": int(reduced[-1][2]) if reduced else "",
        "root_uncut_relaxation": node_zero[0] if node_zero else "",
        "post_root_cut_relaxation": node_zero[-1] if node_zero else "",
        "time_limited_best_bound": best_bounds[-1] if best_bounds else "",
        "native_cuts_by_type": "|".join(f"{name.strip()}={count}" for name, count in cut_pairs),
        "max_native_tree_memory_mb": max(tree_memory, default=""),
    }


def current_global_result(instance: str, timing: str) -> Tuple[Dict[str, Any], str]:
    current_hash = sha256(EXE)
    matches: List[Tuple[int, float, Dict[str, Any], str]] = []
    for path in RAW.glob("*.json"):
        data = read_json(path)
        if data.get("round20_instance") != instance or not truth(data.get("global_gini_tree_attempted")):
            continue
        if data.get("global_gini_tree_row_timing_mode") != timing:
            continue
        run_id = str(data.get("round20_run_id", path.stem))
        command = read_json(paths(run_id)["command"])
        if command.get("executable_sha256") != current_hash or not usable_completed_result(
                data, str(data.get("round20_arm", ""))):
            continue
        preferred = 1 if data.get("round20_arm") in {"baseline", "eager_only"} else 0
        matches.append((preferred, path.stat().st_mtime, data, run_id))
    if not matches:
        return {}, ""
    _, _, data, run_id = max(matches, key=lambda item: (item[0], item[1]))
    return data, run_id


def matched_child_trace(run_id: str, lower: float, upper: float) -> Dict[str, Any]:
    tolerance = 1e-9
    for row in read_csv(paths(run_id)["topology"]):
        for side in ("lower", "upper"):
            if (abs(number(row.get(f"{side}_gamma_L")) - lower) <= tolerance and
                    abs(number(row.get(f"{side}_gamma_U")) - upper) <= tolerance):
                uid = int(number(row.get(f"{side}_uid"), -1))
                post = [item for item in read_csv(paths(run_id)["post"])
                        if int(number(item.get("node_uid"), -2)) == uid]
                passed = next((item for item in post
                               if item.get("status", "").startswith("passed")), {})
                attached = next((item for item in post if item.get("status") in
                                 {"awaiting_reoptimization", "not_required_empty_delta"}), {})
                delta = next((item for item in read_csv(paths(run_id)["delta"])
                              if int(number(item.get("node_uid"), -2)) == uid and
                              "attach" in item.get("event", "")), {})
                return {
                    "child_uid": uid, "parent_uid": row.get("parent_uid", ""),
                    "parent_relaxation": row.get("parent_relaxation", ""),
                    "child_estimate": row.get(f"{side}_estimate", ""),
                    "domain_estimate": row.get(f"{side}_domain_estimate", ""),
                    "estimate_lift": row.get(f"{side}_lift", ""),
                    "estimate_mode": row.get("estimate_mode", ""),
                    "pre_local_row_relaxation": passed.get("pre_local_row_relaxation", ""),
                    "post_local_row_relaxation": passed.get("post_local_row_relaxation", ""),
                    "post_row_status": passed.get("status", "not_observed"),
                    "theoretical_full_rows": delta.get("theoretical_full_rows", ""),
                    "theoretical_full_bounds": delta.get("theoretical_full_bounds", ""),
                    "inherited_rows": delta.get("inherited_rows", ""),
                    "inherited_bounds": delta.get("inherited_bounds", ""),
                    "exact_duplicate_rows_omitted": delta.get(
                        "exact_duplicate_rows_omitted", attached.get("duplicates_omitted", "")),
                    "delta_rows_attached": delta.get(
                        "delta_rows_attached", attached.get("delta_rows_attached", "")),
                    "delta_bounds_attached": delta.get("delta_bounds_attached", ""),
                    "row_families": delta.get("families", ""),
                    "row_family_signature": delta.get("aggregate_signature", ""),
                }
    return {"post_row_status": "matching_child_not_observed"}


def build_forensic_tables() -> None:
    model_rows: List[Dict[str, Any]] = []
    comparison: List[Dict[str, Any]] = []
    legacy_index = read_csv(AUDITS / "legacy_interval_model_index.csv")
    for index in legacy_index:
        instance = index.get("instance", "")
        interval_id = int(number(index.get("interval_id"), -1))
        source = (DIAGNOSTICS / "inventory_route_gini_relaxation" / instance /
                  f"interval_{interval_id}" / "inventory_gini_bound.lp")
        row = {"instance": instance, "interval_id": interval_id,
               "gamma_L": index.get("gamma_L", ""), "gamma_U": index.get("gamma_U", ""),
               "formulation": "A_inventory_route_gini_relaxation",
               "scope": "diagnostic_only; route-mask families excluded from migration"}
        row.update(lp_inventory(source))
        model_rows.append(row)

    for instance, (interval_id, lower, upper) in DIAGNOSTIC_INTERVALS.items():
        root = DIAGNOSTICS / "matched_interval" / instance / f"interval_{interval_id}"
        legacy_lp = (DIAGNOSTICS / "inventory_route_gini_relaxation" / instance /
                     f"interval_{interval_id}" / "inventory_gini_bound.lp")
        legacy_log = root / "A_legacy_relaxation" / "legacy_relaxation.log"
        factory_dir = root / "B_factory_preloaded"
        factory_lp = factory_dir / "fixed_interval_factory.lp"
        factory_log = factory_dir / "fixed_interval_factory.log"
        factory_json = read_json(factory_dir / "fixed_interval_factory.json")

        for formulation, lp, log in (
                ("A_inventory_route_gini_relaxation", legacy_lp, legacy_log),
                ("B_factory_preloaded_fixed_interval", factory_lp, factory_log)):
            inventory = {"instance": instance, "interval_id": interval_id,
                         "gamma_L": lower, "gamma_U": upper, "formulation": formulation,
                         "incumbent_cutoff": verified_cutoff(instance),
                         "native_mip_start_present": False}
            inventory.update(lp_inventory(lp))
            inventory.update(cplex_log_metrics(log))
            if formulation.startswith("B_"):
                inventory["time_limited_best_bound"] = factory_json.get(
                    "interval_exact_cutoff_best_bound",
                    factory_json.get("interval_oracle_solver_best_bound", ""))
                inventory["verified_incumbent_cutoff_present"] = factory_json.get(
                    "interval_oracle_has_objective_cutoff_row", "")
                inventory["row_families"] = factory_json.get(
                    "compact_interval_bc_cut_families_enabled", "")
            model_rows.append(inventory)
            compare = {"instance": instance, "interval_id": interval_id,
                       "gamma_L": lower, "gamma_U": upper, "formulation": formulation}
            compare.update(cplex_log_metrics(log))
            compare["solver_best_bound"] = inventory.get("time_limited_best_bound", "")
            compare["validity_status"] = "passed" if inventory.get("model_status") == "present" else "failed"
            comparison.append(compare)

        deferred_data, deferred_run = current_global_result(instance, "deferred")
        if deferred_run:
            child = matched_child_trace(deferred_run, lower, upper)
            root_inventory = lp_inventory(paths(deferred_run)["root"])
            model = {"instance": instance, "interval_id": interval_id,
                     "gamma_L": lower, "gamma_U": upper,
                     "formulation": "C_global_root_deferred_child",
                     "run_id": deferred_run,
                     "row_families": deferred_data.get("compact_bc_cut_families_enabled", ""),
                     "native_mip_start_present": deferred_data.get(
                         "global_gini_tree_native_mip_start_stored", False)}
            model.update(root_inventory)
            model.update(child)
            model_rows.append(model)
            compare = {"instance": instance, "interval_id": interval_id,
                       "gamma_L": lower, "gamma_U": upper,
                       "formulation": "C_global_root_deferred_child", "run_id": deferred_run,
                       **child, "validity_status": "passed" if child.get("child_uid", -1) >= 0 else "failed"}
            comparison.append(compare)

        eager_data, eager_run = current_global_result(instance, "eager")
        if eager_run:
            child = matched_child_trace(eager_run, lower, upper)
            model = {"instance": instance, "interval_id": interval_id,
                     "gamma_L": lower, "gamma_U": upper,
                     "formulation": "D_eager_branch_child", "run_id": eager_run,
                     "native_mip_start_present": eager_data.get(
                         "global_gini_tree_native_mip_start_stored", False), **child}
            model.update(lp_inventory(paths(eager_run)["root"]))
            model_rows.append(model)
            comparison.append({"instance": instance, "interval_id": interval_id,
                               "gamma_L": lower, "gamma_U": upper,
                               "formulation": "D_eager_branch_child", "run_id": eager_run,
                               **child, "validity_status": "passed" if child.get("child_uid", -1) >= 0 else "failed"})

        factory_metrics = cplex_log_metrics(factory_log)
        if deferred_run and math.isfinite(number(factory_metrics.get("root_uncut_relaxation"))):
            child = matched_child_trace(deferred_run, lower, upper)
            domain_estimate = number(child.get("domain_estimate"))
            standalone_relaxation = number(factory_metrics.get("root_uncut_relaxation"))
            final_estimate = number(child.get("child_estimate"))
            reoptimized_child = number(child.get("post_local_row_relaxation"))
            domain_valid = (math.isfinite(domain_estimate) and
                            domain_estimate <= standalone_relaxation +
                            1e-8 * max(1.0, abs(standalone_relaxation)))
            inherited_valid = (math.isfinite(final_estimate) and
                               math.isfinite(reoptimized_child) and
                               final_estimate <= reoptimized_child +
                               1e-8 * max(1.0, abs(reoptimized_child)))
            comparison.append({
                "instance": instance, "interval_id": interval_id,
                "gamma_L": lower, "gamma_U": upper,
                "formulation": "global_child_estimate", "run_id": deferred_run,
                "child_estimate": child.get("child_estimate", ""),
                "domain_estimate": child.get("domain_estimate", ""),
                "matched_standalone_uncut_relaxation":
                    factory_metrics.get("root_uncut_relaxation", ""),
                "matched_child_relaxation":
                    child.get("post_local_row_relaxation", ""),
                "domain_component_below_standalone_relaxation": domain_valid,
                "inherited_estimate_below_reoptimized_child": inherited_valid,
                "standalone_comparability_note": (
                    "final inherited estimate is not compared with an uncut "
                    "standalone LP that omits the parent's native cuts"),
                "validity_status": "passed" if domain_valid and inherited_valid else "failed",
            })

    model_rows.append({
        "instance": "all", "interval_id": "root",
        "formulation": "candidate_family_classification",
        "row_families": "legacy_fcb_single_commodity_connectivity",
        "scope": "root-global", "present_in_legacy_A": True,
        "present_in_factory_B_and_global_C": False,
        "scaling": "O(M*V^2) continuous variables and rows",
        "projection_proof": (
            "send the number of downstream visited stations on each used "
            "depot-closed route arc; one unit is consumed at every visit"),
        "route_mask_enumeration": False, "restricted_route_pool": False,
        "migration_status": "implemented_as_optional_root_flow_only_arm",
    })
    current_hash = sha256(EXE)
    for result_path in RAW.glob("*.json"):
        data = read_json(result_path)
        if data.get("round20_arm") != "root_flow_only":
            continue
        run_id = str(data.get("round20_run_id", result_path.stem))
        if read_json(paths(run_id)["command"]).get("executable_sha256") != current_hash:
            continue
        row = {
            "instance": data.get("round20_instance", ""),
            "interval_id": "root",
            "formulation": "E_optional_root_connectivity_flow",
            "run_id": run_id,
            "scope": "root-global; exact scalable extended formulation",
            "row_families": "single_commodity_route_connectivity",
        }
        row.update(lp_inventory(paths(run_id)["root"]))
        model_rows.append(row)
    write_csv(RESULTS / "forensic_model_diff.csv", model_rows)
    write_csv(RESULTS / "forensic_interval_bound_comparison.csv", comparison)


def parse_run_identity(path: Path) -> Tuple[str, str, int, str]:
    data = read_json(path)
    return (str(data.get("round20_instance", "")), str(data.get("round20_arm", "")),
            int(number(data.get("round20_budget_seconds", 0), 0)), str(data.get("round20_run_id", path.stem)))


def objective_audit(data: Dict[str, Any]) -> Tuple[bool, str]:
    objective, gini, penalty = number(data.get("objective")), number(data.get("gini", data.get("G"))), number(data.get("penalty", data.get("P")))
    if not all(math.isfinite(x) for x in (objective, gini, penalty)):
        return False, "missing_nonfinite_objective_parts"
    residual = objective - (gini + 0.15 * penalty)
    ok = abs(residual) <= 1e-7 * max(1.0, abs(objective), abs(gini + 0.15 * penalty))
    return ok, f"residual={residual:.17g}"


def result_summary(path: Path) -> Dict[str, Any]:
    data = read_json(path)
    instance, arm, budget, run_id = parse_run_identity(path)
    global_arm = truth(data.get("global_gini_tree_attempted"))
    lb, ub = number(data.get("lower_bound")), number(data.get("upper_bound", data.get("objective")))
    gap = number(data.get("gap"))
    if not math.isfinite(gap) and math.isfinite(lb) and math.isfinite(ub) and ub > 0:
        gap = max(0.0, (ub - lb) / ub)
    command = read_json(paths(run_id)["command"])
    root_flow = "--global-gini-tree-root-connectivity-flow true" in str(
        command.get("command_line", "")).lower()
    return {
        "run_id": run_id, "instance": instance, "instance_class": INSTANCES.get(instance, {}).get("class", ""),
        "arm": arm, "budget_seconds": budget, "status": data.get("status", "missing"),
        "objective": data.get("objective", ""), "LB": data.get("lower_bound", ""), "UB": data.get("upper_bound", ""),
        "gap": gap, "certified": truth(data.get("certified_original_problem")) or truth(data.get("global_gini_tree_optimality_accepted")),
        "verifier_passed": truth(data.get("verifier_passed", data.get("global_gini_tree_incumbent_verified"))),
        "nodes": data.get("nodes", data.get("global_gini_tree_native_open_nodes", "")),
        "open_nodes": (data.get("global_gini_tree_native_open_nodes", "")
                       if global_arm else data.get("open_nodes", "")),
        "simplex_iterations": data.get("global_gini_tree_native_simplex_iterations", ""),
        "gini_branches": data.get("global_gini_tree_gini_branch_nodes", ""),
        "ordinary_branches": data.get("global_gini_tree_ordinary_branch_fallbacks", ""),
        "rows_attached": data.get("global_gini_tree_local_rows_attached", ""),
        "rows_avoided": number(data.get("global_gini_tree_theoretical_full_rows", 0), 0) - number(data.get("global_gini_tree_delta_rows_attached", 0), 0),
        "equal_siblings": data.get("global_gini_tree_sibling_equal_estimate_pairs", ""),
        "discriminated_siblings": data.get("global_gini_tree_sibling_discriminated_pairs", ""),
        "row_factory_seconds": data.get("global_gini_tree_row_factory_seconds", ""),
        "callback_packing_seconds": data.get("global_gini_tree_callback_packing_seconds", ""),
        "row_api_seconds": data.get("global_gini_tree_local_row_api_seconds", ""),
        "native_solution_count": data.get("global_gini_tree_native_solution_pool_count", ""),
        "native_cut_counts": data.get("global_gini_tree_native_cut_counts", ""),
        "mip_start_accepted": data.get("global_gini_tree_native_mip_start_accepted", ""),
        "root_connectivity_flow": root_flow,
        "first_gini_branch_time": data.get("global_gini_tree_first_gini_branch_time", ""),
        "callback_abort": data.get("global_gini_tree_callback_abort_used", ""),
        "lifecycle_valid": data.get("global_gini_tree_lifecycle_valid", "") if global_arm else "benchmark",
        "fresh_run": data.get("fresh_run", False),
    }


def trace_points(run_id: str, data: Dict[str, Any]) -> List[Tuple[float, float, float, float]]:
    rows = read_csv(paths(run_id)["bound"])
    points: List[Tuple[float, float, float, float]] = []
    offset = max(0.0, number(data.get("round20_budget_seconds", 0), 0) - number(data.get("global_gini_tree_native_time_limit_seconds", data.get("round20_budget_seconds", 0)), 0))
    for row in rows:
        t = number(row.get("elapsed_time")) + offset
        lb = number(row.get("native_global_LB"))
        incumbent = number(row.get("native_incumbent"))
        cutoff = number(row.get("verified_cutoff"))
        ub = incumbent if math.isfinite(incumbent) and incumbent < 1e50 else cutoff
        if math.isfinite(t) and math.isfinite(lb) and math.isfinite(ub) and ub > 0:
            points.append((t, lb, ub, max(0.0, (ub - lb) / ub)))
    if not points:
        for row in read_csv(paths(run_id)["progress"]):
            t, lb, ub, gap = (number(row.get("elapsed_seconds")), number(row.get("global_LB")),
                              number(row.get("incumbent_UB")), number(row.get("gap")))
            if all(math.isfinite(x) for x in (t, lb, ub)):
                points.append((t, lb, ub, gap if math.isfinite(gap) else max(0.0, (ub - lb) / max(ub, 1e-12))))
    points.sort()
    return points


def threshold_rows() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for path in RAW.glob("*.json"):
        data = read_json(path)
        if not data.get("fresh_run"):
            continue
        instance, arm, budget, run_id = parse_run_identity(path)
        points = trace_points(run_id, data)
        row: Dict[str, Any] = {"run_id": run_id, "instance": instance, "arm": arm, "budget_seconds": budget}
        for threshold in THRESHOLDS:
            label = "gap_0" if threshold == 0 else f"gap_{int(threshold*100)}pct"
            hit = next((p[0] for p in points if p[3] <= threshold + 1e-10), math.nan)
            row[f"time_to_{label}"] = hit
        out.append(row)
    return out


def forensic_trace_audits() -> None:
    post_rows: List[Dict[str, Any]] = []
    sibling_rows: List[Dict[str, Any]] = []
    memory_rows: List[Dict[str, Any]] = []
    for path in RAW.glob("*.json"):
        data = read_json(path)
        run_id = str(data.get("round20_run_id", ""))
        if not run_id or not truth(data.get("global_gini_tree_attempted")):
            continue
        instance, arm, budget, _ = parse_run_identity(path)
        post = read_csv(paths(run_id)["post"])
        pending = sum(row.get("status") == "awaiting_reoptimization" for row in post)
        passed = sum(row.get("status", "").startswith("passed") for row in post)
        post_rows.append({
            "run_id": run_id, "instance": instance, "arm": arm, "budget_seconds": budget,
            "pending_attachments": pending, "post_relaxations_observed": passed,
            "passed_in_relaxation_context": sum(row.get("status") == "passed" for row in post),
            "passed_in_branching_context": sum(row.get("status") == "passed_at_branching_context" for row in post),
            "still_open_unprocessed": max(0, pending - passed),
            "failures": data.get("global_gini_tree_post_row_reoptimization_failures", ""),
            "mean_lift": (sum(max(0.0, number(row.get("post_local_row_relaxation"), 0) - number(row.get("pre_local_row_relaxation"), 0))
                              for row in post if row.get("status", "").startswith("passed")) / max(1, passed)),
        })
        siblings = read_csv(paths(run_id)["sibling"])
        delays = [number(row.get("delay_seconds")) for row in siblings if math.isfinite(number(row.get("delay_seconds")))]
        sibling_rows.append({
            "run_id": run_id, "instance": instance, "arm": arm, "pairs_created": data.get("global_gini_tree_gini_branch_nodes", ""),
            "children_first_processed": len(siblings), "equal_estimate_pairs": data.get("global_gini_tree_sibling_equal_estimate_pairs", ""),
            "discriminated_pairs": data.get("global_gini_tree_sibling_discriminated_pairs", ""),
            "mean_child_delay_seconds": sum(delays) / max(1, len(delays)), "max_child_delay_seconds": max(delays, default=0.0),
        })
        log_text = paths(run_id)["log"].read_text(encoding="utf-8", errors="replace") if paths(run_id)["log"].exists() else ""
        samples = [(number(a), number(b)) for a, b in re.findall(r"Elapsed time\s*=\s*([0-9.]+).*?tree\s*=\s*([0-9.]+)\s*MB", log_text)]
        for elapsed, mb in samples:
            memory_rows.append({"run_id": run_id, "instance": instance, "arm": arm, "elapsed_seconds": elapsed,
                                "native_tree_memory_mb": mb, "rows_attached_final": data.get("global_gini_tree_local_rows_attached", ""),
                                "rows_avoided_final": number(data.get("global_gini_tree_theoretical_full_rows", 0), 0) - number(data.get("global_gini_tree_delta_rows_attached", 0), 0)})
    write_csv(RESULTS / "post_local_row_reoptimization_audit.csv", post_rows)
    write_csv(RESULTS / "gini_sibling_delay_audit.csv", sibling_rows)
    write_csv(RESULTS / "tree_memory_and_row_growth.csv", memory_rows)


def exactness_audits(summaries: List[Dict[str, Any]]) -> None:
    current_hash = sha256(EXE) if EXE.exists() else ""
    fresh: List[Dict[str, Any]] = []
    stale_hash_runs: List[str] = []
    for path in RAW.glob("*.json"):
        data = read_json(path)
        if not truth(data.get("fresh_run")):
            continue
        run_id = str(data.get("round20_run_id", path.stem))
        command = read_json(paths(run_id)["command"])
        if command.get("executable_sha256") != current_hash:
            stale_hash_runs.append(run_id)
            continue
        fresh.append(data)
    global_data = [data for data in fresh if truth(data.get("global_gini_tree_attempted"))]
    obj = [objective_audit(data)[0] for data in fresh]
    mechanical = {row.get("test", ""): row.get("status", "")
                  for row in read_csv(AUDITS / "mechanical_tests.csv")}
    unit_passed = (mechanical.get("cpp_global_gini_tree_tests") == "passed" and
                   mechanical.get("python_round20_regression_tests") == "passed")

    def all_global(field: str, predicate=lambda x: truth(x)) -> bool:
        return bool(global_data) and all(predicate(data.get(field)) for data in global_data)

    topology: List[Dict[str, str]] = []
    post_rows: List[Dict[str, str]] = []
    for data in global_data:
        run_id = str(data.get("round20_run_id", ""))
        topology.extend(read_csv(paths(run_id)["topology"]))
        post_rows.extend(read_csv(paths(run_id)["post"]))

    def finite_row(row: Dict[str, str], *fields: str) -> bool:
        return all(math.isfinite(number(row.get(field))) for field in fields)

    estimate_valid = bool(topology)
    sibling_valid = bool(topology)
    metadata_valid = bool(topology)
    for row in topology:
        required = ("parent_gamma_L", "parent_gamma_U", "split",
                    "parent_relaxation", "lower_estimate", "upper_estimate",
                    "lower_domain_estimate", "upper_domain_estimate")
        if not finite_row(row, *required) or row.get("validity_status") != "passed":
            estimate_valid = sibling_valid = metadata_valid = False
            continue
        parent = number(row["parent_relaxation"])
        low = number(row["lower_estimate"])
        high = number(row["upper_estimate"])
        low_domain = number(row["lower_domain_estimate"])
        high_domain = number(row["upper_domain_estimate"])
        mode = row.get("estimate_mode", "")
        tolerance = 1e-8 * max(1.0, abs(parent), abs(low), abs(high))
        if low + tolerance < parent or high + tolerance < parent:
            estimate_valid = False
        if mode == "parent-copy" and (abs(low - parent) > tolerance or
                                      abs(high - parent) > tolerance):
            estimate_valid = False
        if mode == "factory-domain" and (
                abs(low - max(parent, low_domain)) > tolerance or
                abs(high - max(parent, high_domain)) > tolerance):
            estimate_valid = False
        parent_l, parent_u, split = (number(row["parent_gamma_L"]),
                                     number(row["parent_gamma_U"]),
                                     number(row["split"]))
        if not (abs(number(row.get("lower_gamma_L")) - parent_l) <= 1e-9 and
                abs(number(row.get("lower_gamma_U")) - split) <= 1e-9 and
                abs(number(row.get("upper_gamma_L")) - split) <= 1e-9 and
                abs(number(row.get("upper_gamma_U")) - parent_u) <= 1e-9 and
                int(number(row.get("lower_uid"), -1)) >= 0 and
                int(number(row.get("upper_uid"), -1)) >= 0 and
                row.get("lower_uid") != row.get("upper_uid")):
            sibling_valid = False
        if not (int(number(row.get("parent_uid"), -1)) >= 0 and
                int(number(row.get("child_gini_generation"), -1)) ==
                int(number(row.get("parent_gini_generation"), -2)) + 1):
            metadata_valid = False

    diagnostic = read_csv(RESULTS / "forensic_interval_bound_comparison.csv")
    diagnostic_estimates = [row for row in diagnostic
                            if row.get("formulation") == "global_child_estimate"]
    diagnostic_estimate_valid = bool(diagnostic_estimates) and all(
        row.get("validity_status") == "passed" and
        finite_row(row, "child_estimate", "matched_child_relaxation") and
        number(row["child_estimate"]) <=
        number(row["matched_child_relaxation"]) +
        1e-8 * max(1.0, abs(number(row["matched_child_relaxation"])))
        for row in diagnostic_estimates)

    delta_data = [data for data in global_data
                  if data.get("global_gini_tree_row_attachment_mode") ==
                  "exact-incremental-delta"]
    eager_data = [data for data in global_data
                  if data.get("global_gini_tree_row_timing_mode") == "eager"]
    eager_modes = {read_json(paths(str(data.get("round20_run_id", "")))["command"])
                   .get("presolve") for data in eager_data}
    mip_data = [data for data in global_data
                if truth(data.get("global_gini_tree_native_mip_start_attempted"))]
    flow_data = [data for data in global_data
                 if data.get("round20_arm") == "root_flow_only"]
    flow_projection_valid = bool(flow_data)
    for data in flow_data:
        run_id = str(data.get("round20_run_id", ""))
        families = str(lp_inventory(paths(run_id)["root"]).get(
            "variables_by_family_integrality", ""))
        match_x = re.search(r"(?:^|\|)x:binary:(\d+)(?:\||$)", families)
        match_flow = re.search(
            r"(?:^|\|)conn:continuous:(\d+)(?:\||$)", families)
        if (not match_x or not match_flow or
                int(match_x.group(1)) != int(match_flow.group(1))):
            flow_projection_valid = False
    all_current_global_usable = bool(global_data) and all(
        usable_completed_result(data, str(data.get("round20_arm", "")))
        for data in global_data)
    tests = [
        (1, "objective_identity_and_serialization", bool(fresh) and all(obj), "current-executable fresh JSON rows"),
        (2, "exhaustive_station_domain_e_lb", unit_passed, "executed C++ exhaustive group"),
        (3, "child_estimate_below_exact_toy_optimum", unit_passed, "executed C++ exhaustive toy group"),
        (4, "child_estimate_below_diagnostic_relaxation", diagnostic_estimate_valid, "matched standalone child-relaxation rows"),
        (5, "parent_relaxation_inheritance", estimate_valid and all_global("global_gini_tree_child_estimate_failures", lambda x: number(x, 0) == 0), "topology arithmetic and native callback counters"),
        (6, "sibling_specific_estimates", sibling_valid and all_global("global_gini_tree_coverage_failures", lambda x: number(x, 0) == 0), "exact sibling intervals and distinct UIDs"),
        (7, "domain_infeasible_fails_closed", unit_passed, "executed C++ domain-infeasible group"),
        (8, "parent_uid_and_generation_metadata", metadata_valid and all_global("global_gini_tree_node_info_api_failures", lambda x: number(x, 0) == 0), "topology UID and generation arithmetic"),
        (9, "post_local_row_detection", bool(post_rows) and all_global("global_gini_tree_post_row_reoptimization_failures", lambda x: number(x, 0) == 0), "explicit pre/await/post phase trace"),
        (10, "exact_duplicate_detection", unit_passed, "executed C++ canonical duplicate group"),
        (11, "endpoint_dependent_changes", unit_passed, "executed C++ endpoint group"),
        (12, "incremental_delta_equivalence", unit_passed and bool(delta_data) and all(usable_completed_result(d, str(d.get("round20_arm", ""))) for d in delta_data), "executed unit proof plus solver-final delta runs"),
        (13, "no_sibling_leakage", all_global("global_gini_tree_sibling_isolation_by_construction"), "child-local rows"),
        (14, "eager_presolve_compatibility", bool(eager_data) and {"on", "off"}.issubset(eager_modes) and all(usable_completed_result(d, str(d.get("round20_arm", ""))) for d in eager_data), "fresh eager presolve-on/off gates"),
        (15, "native_mip_start_mapping_and_gate", bool(mip_data) and all(truth(d.get("global_gini_tree_native_mip_start_mapping_complete")) and truth(d.get("global_gini_tree_native_mip_start_stored")) and truth(d.get("global_gini_tree_incumbent_verified")) for d in mip_data), "fresh complete verified native starts"),
        (16, "round19_coverage_lifecycle_finalization_verifier", not stale_hash_runs and all_current_global_usable and all(all(truth(d.get(k)) for k in ("global_gini_tree_root_coverage_valid", "global_gini_tree_branch_coverage_valid", "global_gini_tree_lifecycle_valid", "global_gini_tree_solver_finalization_reached", "global_gini_tree_incumbent_verified")) for d in global_data), "current executable only; stale=" + "|".join(stale_hash_runs)),
        (17, "no_instance_seed_scale_known_objective_logic", not any(token in (ROOT / "src/TailoredBCCplexApi.cpp").read_text(encoding="utf-8") for token in ("tight_T_seed", "high_imbalance_seed", "moderate_seed", "known_objective")), "source scan"),
        (18, "no_auxiliary_production_solve", all(number(d.get("global_gini_tree_interval_oracle_count"), 0) == 0 and number(d.get("global_gini_tree_mipopt_count"), 0) == 1 for d in global_data), "lifecycle counters"),
        (19, "no_plain_cplex_information_in_tailored", all(d.get("method") == "gcap-frontier" for d in global_data), "command/result separation"),
        (20, "no_false_optimality_positive_gap", all(not truth(d.get("global_gini_tree_optimality_accepted")) or number(d.get("gap"), 1) <= 1e-8 for d in global_data), "certificate guard"),
        (21, "scalable_root_connectivity_flow_projection", unit_passed and flow_projection_valid, "C++ route projection plus root LP x/conn cardinality equality"),
    ]
    write_csv(AUDITS / "exactness_audit.csv", [
        {"test_id": i, "test": name, "status": "passed" if ok else "failed", "evidence": evidence}
        for i, name, ok, evidence in tests
    ])


def summarize() -> None:
    ensure_dirs()
    summaries = [result_summary(path) for path in sorted(RAW.glob("*.json")) if read_json(path).get("fresh_run")]
    write_csv(AUDITS / "all_fresh_run_summary.csv", summaries)
    write_csv(RESULTS / "causal_ablation_summary.csv", [row for row in summaries if row["run_id"].startswith(("stage1__", "optional__"))])
    write_csv(RESULTS / "matched_900s_comparison.csv", [row for row in summaries if row["run_id"].startswith("stage2__")])
    write_csv(RESULTS / "selected_1800s_convergence.csv", [row for row in summaries if row["run_id"].startswith("stage3__")])
    write_csv(RESULTS / "time_to_gap_thresholds.csv", threshold_rows())
    forensic_trace_audits()
    exactness_audits(summaries)
    objective_rows = []
    for path in sorted(RAW.glob("*.json")):
        data = read_json(path)
        if not data.get("fresh_run"):
            continue
        ok, detail = objective_audit(data)
        objective_rows.append({"run_id": data.get("round20_run_id", path.stem), "status": "passed" if ok else "failed", "detail": detail})
    write_csv(AUDITS / "objective_identity.csv", objective_rows)
    build = {
        "generated_at": now(), "hostname": socket.gethostname(), "platform": platform.platform(),
        "python": sys.version, "logical_cpus": os.cpu_count(), "executable": rel(EXE),
        "executable_sha256": sha256(EXE) if EXE.exists() else "", "unit_test_executable": rel(UNIT),
        "unit_test_sha256": sha256(UNIT) if UNIT.exists() else "",
    }
    (AUDITS / "build_and_machine.json").write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")


def select(arm: str, rationale: str) -> None:
    if arm not in ARMS:
        raise ValueError(arm)
    current_hash = sha256(EXE)
    missing: List[str] = []
    for instance in STAGE1:
        for candidate in STAGE1_ARMS:
            run_id = f"stage1__{instance}__{candidate}__300s"
            data = read_json(paths(run_id)["json"])
            command = read_json(paths(run_id)["command"])
            if (command.get("executable_sha256") != current_hash or
                    not usable_completed_result(data, candidate)):
                missing.append(run_id)
    if missing:
        raise RuntimeError(
            "Stage 1 selection is fail-closed until all current-binary causal rows "
            "are solver-final and usable: " + "|".join(missing))
    exactness = read_csv(AUDITS / "exactness_audit.csv")
    failed = [row.get("test", "") for row in exactness
              if row.get("status") != "passed"]
    if not exactness or failed:
        raise RuntimeError(
            "Stage 1 selection is fail-closed until every exactness audit passes: " +
            "|".join(failed or ["missing_exactness_audit"]))
    data = {"selected_arm": arm, "selected_at": now(), "rationale": rationale,
            "selection_scope": "Stage 1 plus isolated optional mechanism evidence; no Stage 2/3 result used"}
    (RESULTS / "selection.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def parse_list(value: str, allowed: Iterable[str]) -> List[str]:
    choices = list(allowed) if value == "all" else [part.strip() for part in value.split(",") if part.strip()]
    invalid = [item for item in choices if item not in allowed]
    if invalid:
        raise ValueError(f"invalid choices: {invalid}")
    return choices


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="phase", required=True)
    for name in ("tests", "gates", "forensic", "interval-diagnostics",
                 "build-forensic-tables", "summarize"):
        sub.add_parser(name)
    stage1 = sub.add_parser("stage1")
    stage1.add_argument("--instances", default=",".join(STAGE1))
    stage2 = sub.add_parser("stage2")
    stage2.add_argument("--instances", default="all")
    stage3 = sub.add_parser("stage3")
    stage3.add_argument("--instances", default=",".join(STAGE3))
    optional = sub.add_parser("optional")
    optional.add_argument("--arms", required=True)
    optional.add_argument("--instances", default=",".join(STAGE1))
    selection = sub.add_parser("select")
    selection.add_argument("--arm", required=True)
    selection.add_argument("--rationale", required=True)
    args = parser.parse_args()
    ensure_dirs()
    if args.phase == "tests": phase_tests()
    elif args.phase == "gates": phase_gates()
    elif args.phase == "forensic": phase_forensic()
    elif args.phase == "interval-diagnostics": phase_interval_diagnostics()
    elif args.phase == "build-forensic-tables": build_forensic_tables()
    elif args.phase == "stage1": phase_stage1(parse_list(args.instances, STAGE1))
    elif args.phase == "optional": phase_optional(parse_list(args.arms, ARMS), parse_list(args.instances, INSTANCES))
    elif args.phase == "select": select(args.arm, args.rationale)
    elif args.phase == "stage2": phase_stage2(parse_list(args.instances, INSTANCES))
    elif args.phase == "stage3": phase_stage3(parse_list(args.instances, STAGE3))
    elif args.phase == "summarize": summarize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
