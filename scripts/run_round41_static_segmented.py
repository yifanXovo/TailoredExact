#!/usr/bin/env python3
"""Run explicitly selected Round 41 static segmented-Gini rows."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from typing import Any

import round41_common as common


ARMS = ("st-k2-i", "st-k2-p-core", "st-k2-p-extended")


def run_one(instance_id: str, arm: str, solve: str,
            process_cap: float, force: bool) -> dict[str, Any]:
    run_id = f"static__{instance_id}__{arm}__{solve}"
    run_dir = common.RUNS / run_id
    result_path = run_dir / "result.json"
    if result_path.is_file() and not force:
        print(f"resume: {run_id}", flush=True)
        return common.load_json(result_path)
    run_dir.mkdir(parents=True, exist_ok=True)
    item = common.inventory()[instance_id]
    command = common.fair_c6_command(item, run_dir, process_cap)
    command.extend((
        "--round41-static-segmented-gini", arm,
        "--round41-static-segmented-solve", solve,
    ))
    record: dict[str, Any] = {
        "schema": "round41-static-segmented-run-v1",
        "round_id": 41,
        "run_id": run_id,
        "instance_id": instance_id,
        "instance_sha256": item["sha256"],
        "arm": arm,
        "solve": solve,
        "process_cap_seconds": process_cap,
        "watchdog_seconds": process_cap + 30.0,
        "command": command,
        "executable_sha256": common.sha256(common.EXE),
        "completed": False,
    }
    common.write_json(run_dir / "command.json", record)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    started = time.monotonic()
    timed_out = False
    return_code = -1
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=common.ROOT, env=environment,
                stdout=stdout, stderr=stderr, check=False,
                timeout=record["watchdog_seconds"])
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
    record.update({
        "completed": result_path.is_file(),
        "return_code": return_code,
        "watchdog_timeout": timed_out,
        "runner_wall_seconds": time.monotonic() - started,
        "stdout_path": common.relative(stdout_path),
        "stderr_path": common.relative(stderr_path),
    })
    common.write_json(run_dir / "command.json", record)
    print(json.dumps({
        "run_id": run_id,
        "return_code": return_code,
        "completed": record["completed"],
        "runner_wall_seconds": record["runner_wall_seconds"],
    }, sort_keys=True), flush=True)
    if return_code != 0 or timed_out or not result_path.is_file():
        raise RuntimeError(f"Round 41 row failed: {run_id}")
    return common.load_json(result_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", action="append", required=True)
    parser.add_argument("--arm", action="append", choices=ARMS,
                        required=True)
    parser.add_argument("--solve", choices=("root-lp", "mip"),
                        default="root-lp")
    parser.add_argument("--process-cap", type=float, default=300.0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not common.EXE.is_file():
        raise SystemExit(f"Round 41 executable missing: {common.EXE}")
    known = common.inventory()
    unknown = set(args.instance) - set(known)
    if unknown:
        raise SystemExit(f"instances are not frozen: {sorted(unknown)}")
    for instance_id in args.instance:
        for arm in args.arm:
            run_one(instance_id, arm, args.solve, args.process_cap, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
