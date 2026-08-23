#!/usr/bin/env python3
"""Run contemporaneous frozen C6 and P-GRB Round 43 references."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from typing import Any

import round43_common as common
import round42_common as round42


def default_c6_command(item: dict[str, Any], run_dir,
                       process_cap: float) -> list[str]:
    """Build the implicit-default C6 sentinel without any Round 43 option."""
    command = round42.fair_c6_command(item, run_dir, process_cap)
    command[0] = str(common.EXE)
    executable_hash = common.sha256(common.EXE)
    for option in ("--round24-executable-sha256",
                   "--round24-manifest-executable-sha256"):
        common.replace_option(command, option, executable_hash)
    return command


def run_one(instance_id: str, arm: str, process_cap: float,
            force: bool) -> dict[str, Any]:
    run_id = f"reference__{instance_id}__{arm}"
    run_dir = common.RUNS / run_id
    result_path = run_dir / "result.json"
    if result_path.is_file() and not force:
        print(f"resume: {run_id}", flush=True)
        return common.load_json(result_path)
    run_dir.mkdir(parents=True, exist_ok=True)
    item = common.inventory()[instance_id]
    command = (default_c6_command(item, run_dir, process_cap)
        if arm == "c6-implicit" else
        (common.fair_c6_command(
            item, run_dir, process_cap, execution="algorithm",
            K0=4, depth=2, rho=0.05, score="d", envelope="single")
         if arm == "c6" else
         common.fair_pgrb_command(item, run_dir, process_cap)))
    if arm == "c6":
        index = command.index("--round43-envelope-refinement")
        command[index + 1] = "off"
    record: dict[str, Any] = {
        "schema": "round43-contemporary-reference-run-v1",
        "round_id": 43,
        "run_id": run_id,
        "instance_id": instance_id,
        "instance_sha256": item["sha256"],
        "arm": arm,
        "process_cap_seconds": process_cap,
        "watchdog_seconds": process_cap + 30.0,
        "command": command,
        "executable_sha256": common.sha256(common.EXE),
        "completed": False,
    }
    common.write_json(run_dir / "command.json", record)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    timed_out = False
    return_code = -1
    with (run_dir / "stdout.log").open("wb") as stdout, \
            (run_dir / "stderr.log").open("wb") as stderr:
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
    })
    common.write_json(run_dir / "command.json", record)
    print(json.dumps({
        "run_id": run_id, "return_code": return_code,
        "completed": record["completed"],
        "runner_wall_seconds": record["runner_wall_seconds"],
    }, sort_keys=True), flush=True)
    if return_code != 0 or timed_out or not result_path.is_file():
        raise RuntimeError(f"reference row failed: {run_id}")
    return common.load_json(result_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", action="append", required=True)
    parser.add_argument("--arm", action="append",
                        choices=("c6", "c6-implicit", "pgrb"),
                        required=True)
    parser.add_argument("--process-cap", type=float, default=3600.0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    for instance_id in args.instance:
        if instance_id not in common.inventory():
            raise SystemExit(f"instance is not frozen: {instance_id}")
        for arm in args.arm:
            run_one(instance_id, arm, args.process_cap, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
