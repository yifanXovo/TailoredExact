#!/usr/bin/env python3
"""Serial pre-freeze Round 30 development runner.

The authorized Gurobi license path is placed only in each solver child
environment.  This script never opens, reads, hashes, prints, copies, or
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
OUT = ROOT / "results/gf_c0_mechanism_transfer_c5_round30/development"
EXE = ROOT / "build_round30/dev_gurobi/ExactEBRP.exe"
LICENSE = r"E:\gurobi\gurobi.lic"
DEVELOPMENT_INSTANCES = (
    "V12_M1",
    "V12_M2",
    "high_imbalance_seed3202",
    "moderate_seed3302",
    "tight_T_seed3101",
    "tight_T_seed5102",
    "moderate_seed6301",
)


def replace_option(command: list[str], option: str, value: object) -> None:
    index = command.index(option)
    command[index + 1] = (
        str(value).lower() if isinstance(value, bool) else str(value))


def command_for(instance: str, arm: str, budget: int,
                run_dir: Path) -> list[str]:
    saved = r29.GUROBI_EXE
    r29.GUROBI_EXE = EXE
    try:
        if arm == "P-GRB":
            return r29.plain_command(instance, budget, run_dir)
        base_arm = "C3-REPLICA" if arm == "C3-REPLICA" else "C4-CANDIDATE"
        command = r29.external_command(instance, base_arm, budget, run_dir)
    finally:
        r29.GUROBI_EXE = saved
    if arm == "C0-DIAG":
        replace_option(command, "--external-gini-scheduling", "legacy-quanta")
        replace_option(command, "--external-gini-lifecycle", "retained-per-leaf")
        command.extend(("--external-gini-split-after-attempts", "2"))
    elif arm == "C5-CANDIDATE":
        replace_option(
            command, "--external-gini-scheduling",
            "round30-dual-bound-target")
        replace_option(
            command, "--external-gini-lifecycle",
            "round30-same-leaf-bound-target")
    elif arm not in {"C3-REPLICA", "C4-CANDIDATE"}:
        raise ValueError(arm)
    return command


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    os.replace(temporary, path)


def run_one(instance: str, arm: str, budget: int) -> dict[str, Any]:
    slug = arm.lower().replace("-", "_")
    run_id = f"{instance}__{slug}__{budget}s"
    run_dir = OUT / run_id
    state_path = run_dir / "run_state.json"
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("completed"):
            print(f"SKIP {run_id}", flush=True)
            return state
        raise RuntimeError(f"incomplete development run requires audit: {run_id}")
    run_dir.mkdir(parents=True, exist_ok=False)
    command = command_for(instance, arm, budget, run_dir)
    record: dict[str, Any] = {
        "schema": "round30-development-command-v1",
        "official": False,
        "run_id": run_id,
        "instance": instance,
        "arm": arm,
        "budget_seconds": budget,
        "executable_sha256": r29.sha256(EXE),
        "instance_sha256": r29.sha256(r29.instance_path(instance)),
        "command": command,
        "license_environment": "child-only-authorized-path-not-serialized",
        "completed": False,
    }
    write_json(run_dir / "command.json", record)
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
    record.update({
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code,
        "emergency_timeout": emergency_timeout,
        "result_exists": (run_dir / "result.json").is_file(),
        "phase_ledger_exists": (run_dir / "process_phases.csv").is_file(),
        "global_bound_trace_exists":
            (run_dir / "external/global_bound_trace.csv").is_file()
            if arm != "P-GRB" else
            (run_dir / "progress.csv").is_file(),
        "completed": True,
    })
    write_json(state_path, record)
    print(
        f"DONE {run_id} rc={return_code} "
        f"wall={record['runner_wall_seconds']:.3f}", flush=True)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", choices=tuple(r29.INSTANCES))
    parser.add_argument(
        "--arm",
        choices=("P-GRB", "C0-DIAG", "C3-REPLICA",
                 "C4-CANDIDATE", "C5-CANDIDATE"))
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--budget", type=int, default=70)
    args = parser.parse_args()
    if not EXE.is_file():
        raise SystemExit(f"development executable missing: {EXE}")
    if args.matrix:
        jobs = tuple(
            (instance, arm)
            for instance in DEVELOPMENT_INSTANCES
            for arm in ("C4-CANDIDATE", "C5-CANDIDATE"))
    elif args.instance and args.arm:
        jobs = ((args.instance, args.arm),)
    else:
        parser.error("use --matrix or both --instance and --arm")
    failures = 0
    for instance, arm in jobs:
        state = run_one(instance, arm, args.budget)
        failures += int(
            state["return_code"] != 0 or state["emergency_timeout"] or
            not state["result_exists"] or
            not state["phase_ledger_exists"] or
            not state["global_bound_trace_exists"])
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
