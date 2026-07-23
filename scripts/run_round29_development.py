#!/usr/bin/env python3
"""Run the retained, pre-freeze Round 29 development experiments.

The authorized license path is assigned only to each solver child environment.
This script never opens, reads, hashes, copies, prints, or serializes that file.
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
OUT = ROOT / "results/gf_gurobi_performance_recovery_round29/development"
EXE = ROOT / "build_round29/dev_gurobi/ExactEBRP.exe"
LICENSE = r"E:\gurobi\gurobi.lic"
INSTANCES = (
    "V12_M1",
    "V12_M2",
    "high_imbalance_seed3202",
    "moderate_seed3302",
    "tight_T_seed3101",
    "moderate_seed6301",
)


def replace_option(command: list[str], option: str, value: object) -> None:
    index = command.index(option)
    command[index + 1] = str(value).lower() if isinstance(value, bool) \
        else str(value)


def command_for(instance: str, arm: str, budget: int,
                run_dir: Path) -> list[str]:
    saved = r29.GUROBI_EXE
    r29.GUROBI_EXE = EXE
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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    os.replace(temporary, path)


def run_one(instance: str, arm: str, budget: int) -> dict[str, Any]:
    run_id = f"{instance}__{arm.lower().replace('-', '_')}__{budget}s"
    run_dir = OUT / run_id
    state_path = run_dir / "run_state.json"
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("completed"):
            print(f"SKIP {run_id}", flush=True)
            return state
        raise RuntimeError(f"incomplete retained development run: {run_id}")
    run_dir.mkdir(parents=True, exist_ok=False)
    command = command_for(instance, arm, budget, run_dir)
    command_record = {
        "schema": "round29-development-command-v1",
        "official": False,
        "run_id": run_id,
        "instance": instance,
        "arm": arm,
        "budget_seconds": budget,
        "executable_sha256": r29.sha256(EXE),
        "instance_sha256": r29.sha256(r29.instance_path(instance)),
        "command": command,
        "license_environment": "process-local-authorized-path-not-serialized",
    }
    write_json(run_dir / "command.json", command_record)
    environment = os.environ.copy()
    environment["GRB_LICENSE_FILE"] = LICENSE
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
    state = {
        **command_record,
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code,
        "emergency_timeout": emergency_timeout,
        "result_exists": (run_dir / "result.json").is_file(),
        "phase_ledger_exists": (run_dir / "process_phases.csv").is_file(),
        "completed": True,
    }
    write_json(state_path, state)
    print(
        f"DONE {run_id} rc={return_code} "
        f"wall={state['runner_wall_seconds']:.3f}",
        flush=True)
    return state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--matrix", choices=("candidate", "microbench"), required=True)
    parser.add_argument("--budget", type=int, default=60)
    args = parser.parse_args()
    if not EXE.is_file():
        raise SystemExit(f"development executable missing: {EXE}")
    matrix = (
        tuple((instance, arm) for instance in INSTANCES
              for arm in ("C3-REPLICA", "C4-CANDIDATE"))
        if args.matrix == "candidate"
        else (("moderate_seed4301", "C2-COLD"),
              ("moderate_seed4301", "C4-CANDIDATE"))
    )
    failures = 0
    for instance, arm in matrix:
        state = run_one(instance, arm, args.budget)
        failures += int(
            state["return_code"] != 0 or state["emergency_timeout"] or
            not state["result_exists"] or not state["phase_ledger_exists"])
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
