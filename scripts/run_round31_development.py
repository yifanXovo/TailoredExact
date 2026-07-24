#!/usr/bin/env python3
"""Serial pre-freeze Round 31 C6 development runner.

The authorized license location must already be present in the runner
environment. It is inherited only by solver children and is never opened,
printed, copied, hashed, or serialized by this module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import run_round29_experiments as r29


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_nonblocking_gurobi_c6_round31/development"
EXE = ROOT / "build_round31/dev_gurobi/ExactEBRP.exe"
DEVELOPMENT_INSTANCES = (
    "V12_M1",
    "V12_M2",
    "high_imbalance_seed3202",
    "moderate_seed3302",
    "tight_T_seed3101",
    "tight_T_seed4101",
    "tight_T_seed5102",
    "tight_T_seed5103",
    "high_imbalance_seed6202",
    "moderate_seed6301",
    "tight_T_seed6102",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def replace_option(command: list[str], option: str, value: object) -> None:
    index = command.index(option)
    command[index + 1] = (
        str(value).lower() if isinstance(value, bool) else str(value))


def command_for(instance: str, arm: str, budget: int,
                run_dir: Path) -> list[str]:
    saved = r29.GUROBI_EXE
    r29.GUROBI_EXE = EXE
    try:
        command = r29.external_command(
            instance, "C4-CANDIDATE", budget, run_dir)
    finally:
        r29.GUROBI_EXE = saved
    if arm == "C5-CANDIDATE":
        replace_option(
            command, "--external-gini-scheduling",
            "round30-dual-bound-target")
        replace_option(
            command, "--external-gini-lifecycle",
            "round30-same-leaf-bound-target")
    elif arm == "C6-CANDIDATE":
        replace_option(
            command, "--external-gini-scheduling",
            "round31-nonblocking-native-bound")
        replace_option(
            command, "--external-gini-lifecycle",
            "round31-open-native-bounded")
    else:
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
        raise RuntimeError(f"incomplete development run: {run_id}")
    if "GRB_LICENSE_FILE" not in os.environ:
        raise RuntimeError("licensed child environment is unavailable")
    run_dir.mkdir(parents=True, exist_ok=False)
    command = command_for(instance, arm, budget, run_dir)
    record: dict[str, Any] = {
        "schema": "round31-development-command-v1",
        "official": False,
        "run_id": run_id,
        "instance": instance,
        "arm": arm,
        "budget_seconds": budget,
        "executable_sha256": sha256(EXE),
        "instance_sha256": sha256(r29.instance_path(instance)),
        "command": command,
        "license_environment":
            "inherited-by-solver-child-not-opened-or-serialized",
        "completed": False,
    }
    write_json(run_dir / "command.json", record)
    started = time.monotonic()
    emergency_timeout = False
    with (run_dir / "console.stdout.log").open("wb") as stdout, \
         (run_dir / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=os.environ.copy(),
                stdout=stdout, stderr=stderr, timeout=budget + 20,
                check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
            emergency_timeout = True
    result_path = run_dir / "result.json"
    record.update({
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code,
        "emergency_timeout": emergency_timeout,
        "result_exists": result_path.is_file(),
        "phase_ledger_exists": (run_dir / "process_phases.csv").is_file(),
        "global_bound_trace_exists":
            (run_dir / "external/global_bound_trace.csv").is_file(),
        "native_target_ledger_exists":
            (run_dir / "external/native_target_ledger.csv").is_file(),
        "completed": True,
    })
    if result_path.is_file():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        record.update({
            "status": result.get("status"),
            "lower_bound": result.get("lower_bound"),
            "upper_bound": result.get("upper_bound"),
            "strict_certified":
                result.get("strict_certified_original_problem"),
            "failure_reason":
                result.get("external_gini_tree_failure_reason"),
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
    parser.add_argument("--instance", choices=tuple(r29.INSTANCES))
    parser.add_argument(
        "--arm", choices=("C5-CANDIDATE", "C6-CANDIDATE"),
        default="C6-CANDIDATE")
    parser.add_argument("--matrix", action="store_true")
    parser.add_argument("--budget", type=int, default=70)
    args = parser.parse_args()
    if not EXE.is_file():
        raise SystemExit(f"development executable missing: {EXE}")
    jobs = (
        tuple((instance, args.arm) for instance in DEVELOPMENT_INSTANCES)
        if args.matrix else
        ((args.instance, args.arm),) if args.instance else ())
    if not jobs:
        parser.error("use --matrix or --instance")
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
