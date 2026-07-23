#!/usr/bin/env python3
"""Run Round 29 post-freeze mechanical, deadline, and sentinel gates.

The authorized Gurobi license path is assigned only to licensed solver child
environments.  The script never opens, reads, hashes, copies, prints, or
serializes the license file or its contents.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import run_round29_experiments as r29


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_gurobi_performance_recovery_round29/stage0_runs"
GUROBI_EXE = ROOT / "build_round29/with_gurobi/ExactEBRP.exe"
CPLEX_EXE = ROOT / "build_round29/cplex_only/ExactEBRP.exe"
LICENSE = r"E:\gurobi\gurobi.lic"


def replace_option(command: list[str], option: str, value: object) -> None:
    index = command.index(option)
    command[index + 1] = str(value).lower() if isinstance(value, bool) \
        else str(value)


def external_command(instance: str, arm: str, budget: float,
                     run_dir: Path) -> list[str]:
    saved = r29.GUROBI_EXE
    r29.GUROBI_EXE = GUROBI_EXE
    try:
        if arm in {"C3-REPLICA", "C4-CANDIDATE"}:
            return r29.external_command(instance, arm, budget, run_dir)
        if arm == "C2-COLD":
            command = r29.external_command(
                instance, "C4-CANDIDATE", budget, run_dir)
            replace_option(
                command, "--external-gini-scheduling", "paper-lp-event")
            replace_option(
                command, "--external-gini-lifecycle",
                "fresh-per-paper-event")
            return command
        raise ValueError(arm)
    finally:
        r29.GUROBI_EXE = saved


def plain_command(instance: str, budget: float,
                  run_dir: Path) -> list[str]:
    saved = r29.GUROBI_EXE
    r29.GUROBI_EXE = GUROBI_EXE
    try:
        return r29.plain_command(instance, budget, run_dir)
    finally:
        r29.GUROBI_EXE = saved


def s0_command(instance: str, budget: float,
               run_dir: Path) -> list[str]:
    args = [str(CPLEX_EXE), "--input", str(r29.instance_path(instance))]
    args.extend(r29.tailored_options(run_dir, budget, local_redecode=True))
    r29.add(args, "--paper-run-sealed", True)
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
        ("--global-gini-tree-topology-trace", run_dir / "gini_topology.csv"),
        ("--global-gini-tree-sibling-trace", run_dir / "sibling_delay.csv"),
        ("--global-gini-tree-row-delta-trace", run_dir / "row_delta.csv"),
        ("--global-gini-tree-memory-trace", run_dir / "tree_memory.csv"),
        ("--global-gini-tree-mip-start-audit",
         run_dir / "mip_start_audit.csv"),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        r29.add(args, option, value)
    return args


def command_for(instance: str, arm: str, budget: float,
                run_dir: Path) -> list[str]:
    if arm == "P-GRB":
        return plain_command(instance, budget, run_dir)
    if arm == "S0-CPLEX":
        return s0_command(instance, budget, run_dir)
    return external_command(instance, arm, budget, run_dir)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    os.replace(temporary, path)


def run_one(suite: str, label: str, instance: str, arm: str,
            budget: float) -> dict[str, Any]:
    run_id = (
        f"{suite}__{label}__{instance}__"
        f"{arm.lower().replace('-', '_')}__{budget:g}s")
    run_dir = OUT / run_id
    state_path = run_dir / "run_state.json"
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("completed"):
            print(f"SKIP {run_id}", flush=True)
            return state
        raise RuntimeError(f"incomplete retained Stage 0 run: {run_id}")
    run_dir.mkdir(parents=True, exist_ok=False)
    command = command_for(instance, arm, budget, run_dir)
    licensed = arm != "S0-CPLEX"
    executable = GUROBI_EXE if licensed else CPLEX_EXE
    record: dict[str, Any] = {
        "schema": "round29-stage0-command-v1",
        "official_performance_row": False,
        "suite": suite,
        "label": label,
        "run_id": run_id,
        "instance": instance,
        "arm": arm,
        "budget_seconds": budget,
        "shutdown_margin_seconds": r29.SHUTDOWN_MARGIN,
        "executable_sha256": r29.sha256(executable),
        "instance_sha256": r29.sha256(r29.instance_path(instance)),
        "command": command,
        "license_environment": (
            "process-local-authorized-path-not-serialized"
            if licensed else "not_applicable"),
        "completed": False,
    }
    write_json(run_dir / "command.json", record)
    environment = os.environ.copy()
    if licensed:
        environment["GRB_LICENSE_FILE"] = LICENSE
    else:
        environment.pop("GRB_LICENSE_FILE", None)
    started = time.monotonic()
    emergency_timeout = False
    with (run_dir / "console.stdout.log").open("wb") as stdout, \
         (run_dir / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=environment, stdout=stdout,
                stderr=stderr, timeout=budget + 15, check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
            emergency_timeout = True
    record.update({
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code,
        "emergency_timeout": emergency_timeout,
        "result_exists": (run_dir / "result.json").is_file(),
        "phase_ledger_exists": (run_dir / "process_phases.csv").is_file(),
        "completed": True,
    })
    write_json(state_path, record)
    print(
        f"DONE {run_id} rc={return_code} "
        f"wall={record['runner_wall_seconds']:.3f}",
        flush=True)
    return record


def matrix(suite: str) -> tuple[tuple[str, str, str, float], ...]:
    if suite == "deadline":
        return (
            ("pre_exact_hga", "moderate_seed4301", "C4-CANDIDATE", 8),
            ("hga_boundary", "moderate_seed4301", "C4-CANDIDATE", 25),
            ("first_external_events", "moderate_seed4301",
             "C4-CANDIDATE", 28),
            ("lp_or_terminal_mip", "moderate_seed4301",
             "C4-CANDIDATE", 45),
            ("local_redecode_transition", "moderate_seed4301",
             "C3-REPLICA", 30),
        )
    if suite == "exactness":
        return (
            ("toy_exhaustive_reference", "toy", "P-GRB", 30),
            ("toy_exact_candidate", "toy", "C4-CANDIDATE", 30),
            ("cold_parent_reference", "moderate_seed4301", "C2-COLD", 75),
            ("incremental_parent_candidate", "moderate_seed4301",
             "C4-CANDIDATE", 75),
        )
    if suite == "sentinel":
        return tuple(
            ("correctness_sentinel", "moderate_seed4301", arm, 120)
            for arm in (
                "P-GRB", "S0-CPLEX", "C3-REPLICA", "C4-CANDIDATE"))
    if suite == "transition":
        return tuple(
            ("moderate6301_transition", "moderate_seed6301", arm, 300)
            for arm in ("C3-REPLICA", "C4-CANDIDATE"))
    raise ValueError(suite)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--suite",
        choices=("deadline", "exactness", "sentinel", "transition"),
        required=True)
    args = parser.parse_args()
    if not GUROBI_EXE.is_file() or not CPLEX_EXE.is_file():
        raise SystemExit("Round 29 clean-build executables are missing")
    failures = 0
    for label, instance, arm, budget in matrix(args.suite):
        state = run_one(args.suite, label, instance, arm, budget)
        failures += int(
            state["return_code"] != 0 or state["emergency_timeout"] or
            not state["result_exists"] or not state["phase_ledger_exists"])
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
