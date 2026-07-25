#!/usr/bin/env python3
"""Frozen serial Round 31 official experiment runner.

The license location must be inherited in the process environment. This
module never opens, prints, copies, hashes, or serializes the license or its
location. All official solver jobs run sequentially.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import run_round29_experiments as r29


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_nonblocking_gurobi_c6_round31"
RUNS = OUT / "runs"
MANIFEST = OUT / "c6_manifest.json"
MATRIX = OUT / "round31_official_matrix.csv"
INSTANCE_MANIFEST = OUT / "round31_instance_manifest.csv"
GUROBI_EXE = ROOT / "build_round31/official/gurobi_r1/ExactEBRP.exe"
CPLEX_EXE = ROOT / "build_round31/official/cplex_r1/ExactEBRP.exe"
LOCK = OUT / ".round31_runner.lock"
SHUTDOWN_MARGIN = 5


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    os.replace(temporary, path)


def add(args: list[str], name: str, value: object) -> None:
    args.extend((
        name, str(value).lower() if isinstance(value, bool) else str(value)))


def instances() -> dict[str, dict[str, Any]]:
    return {
        row["instance"]: {
            "path": row["path"],
            "family": row["family"],
            "V": int(row["V"]),
            "M": int(row["M"]),
            "sha256": row["sha256"],
            "sealed": row["sealed_heldout"].lower() == "true",
        }
        for row in csv.DictReader(INSTANCE_MANIFEST.open(
            newline="", encoding="utf-8"))
    }


def instance_path(name: str, inventory: dict[str, dict[str, Any]]) -> Path:
    return ROOT / inventory[name]["path"]


def tailored_options(run_dir: Path, budget: int) -> list[str]:
    return r29.tailored_options(
        run_dir, budget, local_redecode=False)


def plain_command(name: str, budget: int, run_dir: Path,
                  inventory: dict[str, dict[str, Any]],
                  with_hga: bool) -> list[str]:
    args = [
        str(GUROBI_EXE), "--input", str(instance_path(name, inventory))]
    for option, value in (
        ("--method", "gurobi"),
        ("--lambda", 0.15),
        ("--T", 3600),
        ("--time-limit", budget),
        ("--process-wall-time-limit", budget),
        ("--process-shutdown-margin", SHUTDOWN_MARGIN),
        ("--process-phase-ledger", run_dir / "process_phases.csv"),
        ("--threads", 1),
        ("--mip-threads", 1),
        ("--cplex-threads", 1),
        ("--compact-bc-threads", 1),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0),
        ("--gurobi-presolve", -1),
        ("--gurobi-model-export", run_dir / "canonical.lp"),
        ("--gurobi-progress", run_dir / "progress.csv"),
        ("--round24-executable-sha256", sha256(GUROBI_EXE)),
        ("--round24-manifest-executable-sha256", sha256(GUROBI_EXE)),
        ("--round24-expected-gurobi-model-fingerprint",
         r29.r28.merged_fingerprints().get(name, 0)),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, option, value)
    if with_hga:
        for option, value in (
            ("--gurobi-hga-start", True),
            ("--primal-heuristic", "hga-tgbc"),
            ("--primal-heuristic-seed", 20260626),
            ("--primal-heuristic-stop", "generation-stagnation"),
            ("--primal-heuristic-no-improve-generations", 2000),
            ("--primal-heuristic-generation-log",
             run_dir / "hga_generations.csv"),
        ):
            add(args, option, value)
    args.append("--plain-baseline")
    return args


def external_command(name: str, arm: str, budget: int, run_dir: Path,
                     inventory: dict[str, dict[str, Any]]) -> list[str]:
    args = [
        str(GUROBI_EXE), "--input", str(instance_path(name, inventory))]
    args.extend(tailored_options(run_dir, budget))
    scheduling = {
        "C5-CANDIDATE": "round30-dual-bound-target",
        "C6-CANDIDATE": "round31-nonblocking-native-bound",
    }[arm]
    lifecycle = {
        "C5-CANDIDATE": "round30-same-leaf-bound-target",
        "C6-CANDIDATE": "round31-open-native-bounded",
    }[arm]
    for option, value in (
        ("--frontier-execution-mode", "external-gini-tree"),
        ("--external-gini-scheduling", scheduling),
        ("--external-gini-artifact-dir", run_dir / "external"),
        ("--external-gini-backend", "gurobi"),
        ("--external-gini-lifecycle", lifecycle),
        ("--external-gini-warm-start", False),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0),
        ("--gurobi-presolve", -1),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, option, value)
    return args


def s0_command(name: str, budget: int, run_dir: Path,
               inventory: dict[str, dict[str, Any]]) -> list[str]:
    args = [
        str(CPLEX_EXE), "--input", str(instance_path(name, inventory))]
    # S0's accepted local-redecode option remains unchanged.
    args.extend(r29.tailored_options(
        run_dir, budget, local_redecode=True))
    add(args, "--paper-run-sealed", True)
    for option, value in (
        ("--frontier-execution-mode", "global-gini-tree"),
        ("--global-gini-tree-node-trace",
         run_dir / "global_node_trace.csv"),
        ("--global-gini-tree-bound-trace",
         run_dir / "global_bound_trajectory.csv"),
        ("--global-gini-tree-manifest",
         run_dir / "model_lifecycle_manifest.csv"),
        ("--global-gini-tree-root-export", run_dir / "global_root.lp"),
        ("--global-gini-tree-post-row-trace", run_dir / "post_rows.csv"),
        ("--global-gini-tree-topology-trace",
         run_dir / "gini_topology.csv"),
        ("--global-gini-tree-sibling-trace",
         run_dir / "sibling_delay.csv"),
        ("--global-gini-tree-row-delta-trace",
         run_dir / "row_delta.csv"),
        ("--global-gini-tree-memory-trace",
         run_dir / "tree_memory.csv"),
        ("--global-gini-tree-mip-start-audit",
         run_dir / "mip_start_audit.csv"),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, option, value)
    return args


def command_for(name: str, arm: str, budget: int, run_dir: Path,
                inventory: dict[str, dict[str, Any]]) -> list[str]:
    if arm == "P-GRB":
        return plain_command(name, budget, run_dir, inventory, False)
    if arm == "P-GRB-HGA":
        return plain_command(name, budget, run_dir, inventory, True)
    if arm in {"C5-CANDIDATE", "C6-CANDIDATE"}:
        return external_command(name, arm, budget, run_dir, inventory)
    if arm == "S0-CPLEX":
        return s0_command(name, budget, run_dir, inventory)
    raise ValueError(arm)


def executable_for(arm: str) -> Path:
    return CPLEX_EXE if arm == "S0-CPLEX" else GUROBI_EXE


def validate_frozen(inventory: dict[str, dict[str, Any]],
                    name: str, arm: str) -> dict[str, Any]:
    manifest = load_json(MANIFEST)
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    if head != manifest["source_commit"]:
        raise RuntimeError("source HEAD changed after C6 freeze")
    for key in (
        "protocol", "parameter_freeze", "forbidden_logic_scan",
        "instance_manifest", "official_matrix",
    ):
        path = ROOT / manifest[f"{key}_path"]
        if sha256(path) != manifest[f"{key}_sha256"]:
            raise RuntimeError(f"frozen artifact changed: {key}")
    for path_text, expected in manifest["source_file_sha256"].items():
        if sha256(ROOT / path_text) != expected:
            raise RuntimeError(f"frozen source changed: {path_text}")
    executable = executable_for(arm)
    executable_key = (
        "cplex_executable_sha256"
        if arm == "S0-CPLEX" else "gurobi_executable_sha256")
    if sha256(executable) != manifest[executable_key]:
        raise RuntimeError(f"official executable changed: {arm}")
    if sha256(instance_path(name, inventory)) != inventory[name]["sha256"]:
        raise RuntimeError(f"instance changed: {name}")
    if "GRB_LICENSE_FILE" not in os.environ and arm != "S0-CPLEX":
        raise RuntimeError("licensed child environment is unavailable")
    return manifest


def run_one(row: dict[str, str],
            inventory: dict[str, dict[str, Any]]) -> dict[str, Any]:
    stage = int(row["stage"])
    name = row["instance"]
    arm = row["arm"]
    budget = int(row["budget_seconds"])
    repetition = int(row["repetition"])
    suffix = f"__rep{repetition}" if repetition else ""
    slug = arm.lower().replace("-", "_")
    run_id = f"stage{stage}__{name}__{slug}{suffix}__{budget}s"
    run_dir = RUNS / run_id
    state_path = run_dir / "run_state.json"
    if state_path.is_file():
        state = load_json(state_path)
        if state.get("completed"):
            print(f"SKIP {run_id}", flush=True)
            return state
        raise RuntimeError(f"incomplete official run: {run_id}")
    validate_frozen(inventory, name, arm)
    run_dir.mkdir(parents=True, exist_ok=False)
    command = command_for(name, arm, budget, run_dir, inventory)
    record: dict[str, Any] = {
        "schema": "round31-official-run-v1",
        "official": True,
        "run_id": run_id,
        "stage": stage,
        "instance": name,
        "family": inventory[name]["family"],
        "V": inventory[name]["V"],
        "M": inventory[name]["M"],
        "sealed_heldout": inventory[name]["sealed"],
        "arm": arm,
        "budget_seconds": budget,
        "repetition": repetition,
        "source_commit": load_json(MANIFEST)["source_commit"],
        "executable_sha256": sha256(executable_for(arm)),
        "instance_sha256": inventory[name]["sha256"],
        "command": command,
        "license_environment":
            "inherited-by-licensed-solver-child-not-serialized"
            if arm != "S0-CPLEX" else "not_required",
        "completed": False,
    }
    write_json(run_dir / "command.json", record)
    started = time.monotonic()
    emergency_timeout = False
    environment = os.environ.copy()
    if arm == "S0-CPLEX":
        environment.pop("GRB_LICENSE_FILE", None)
    with (run_dir / "console.stdout.log").open("wb") as stdout, \
         (run_dir / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=environment, stdout=stdout,
                stderr=stderr, timeout=budget + 30, check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
            emergency_timeout = True
    result_path = run_dir / "result.json"
    trace_path = (
        run_dir / "global_bound_trajectory.csv"
        if arm == "S0-CPLEX" else
        run_dir / "progress.csv"
        if arm in {"P-GRB", "P-GRB-HGA"} else
        run_dir / "external/global_bound_trace.csv")
    record.update({
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code,
        "emergency_timeout": emergency_timeout,
        "result_exists": result_path.is_file(),
        "phase_ledger_exists": (run_dir / "process_phases.csv").is_file(),
        "bound_trace_exists": trace_path.is_file(),
        "completed": True,
    })
    if result_path.is_file():
        result = load_json(result_path)
        record.update({
            "status": result.get("status"),
            "lower_bound": result.get("lower_bound"),
            "upper_bound": result.get("upper_bound"),
            "objective": result.get("objective"),
            "strict_certified":
                result.get("strict_certified_original_problem"),
            "failure_reason":
                result.get("external_gini_tree_failure_reason",
                           result.get("gurobi_failure_reason", "none")),
        })
    write_json(state_path, record)
    print(
        f"DONE {run_id} rc={return_code} "
        f"status={record.get('status')} "
        f"wall={record['runner_wall_seconds']:.3f}",
        flush=True)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stages", default="1,2,3,4,5")
    parser.add_argument("--stage6", action="store_true")
    args = parser.parse_args()
    requested = {int(value) for value in args.stages.split(",") if value}
    if args.stage6:
        gate = load_json(OUT / "short_run_gate.json")
        if not gate.get("passed"):
            raise SystemExit("frozen short-run gate failed; Stage 6 forbidden")
        requested.add(6)
    elif 6 in requested:
        raise SystemExit("Stage 6 requires --stage6 and a passing gate")
    inventory = instances()
    rows = list(csv.DictReader(MATRIX.open(newline="", encoding="utf-8")))
    selected = [row for row in rows if int(row["stage"]) in requested]
    if LOCK.exists():
        raise SystemExit("Round 31 serial-runner lock already exists")
    LOCK.write_text(
        json.dumps({"pid": os.getpid(), "stages": sorted(requested)}) + "\n",
        encoding="utf-8")
    failures = 0
    try:
        for row in selected:
            state = run_one(row, inventory)
            failures += int(
                state["return_code"] != 0 or
                state["emergency_timeout"] or
                not state["result_exists"] or
                not state["phase_ledger_exists"] or
                not state["bound_trace_exists"])
    finally:
        LOCK.unlink(missing_ok=True)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
