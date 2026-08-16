#!/usr/bin/env python3
"""Run implicit-default versus explicit Round 44-off C6 sentinels."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from typing import Any

import round42_common as round42
import round44_common as common


SENTINELS = (
    "round39_small_easy_V10_M1_Q30_slot04_seed1099392856",
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114",
)


def command_for(item: dict[str, Any], run_dir, cap: float,
                explicit: bool) -> list[str]:
    command = round42.fair_c6_command(item, run_dir, cap)
    command[0] = str(common.EXE)
    executable_hash = common.sha256(common.EXE)
    for option in ("--round24-executable-sha256",
                   "--round24-manifest-executable-sha256"):
        common.replace_option(command, option, executable_hash)
    if explicit:
        common.replace_option(
            command, "--round44-envelope-tail-repair", "off")
    return command


def run_one(instance_id: str, mode: str, cap: float, force: bool) -> None:
    run_id = f"default-off__{instance_id}__{mode}"
    run_dir = common.RUNS / run_id
    result_path = run_dir / "result.json"
    if result_path.is_file() and not force:
        print(f"resume: {run_id}", flush=True)
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    item = common.inventory()[instance_id]
    command = command_for(item, run_dir, cap, mode == "explicit")
    record = {
        "schema": "round44-default-off-run-v1",
        "round_id": 44,
        "run_id": run_id,
        "instance_id": instance_id,
        "instance_sha256": item["sha256"],
        "mode": mode,
        "process_cap_seconds": cap,
        "watchdog_seconds": cap + 45.0,
        "command": command,
        "executable_sha256": common.sha256(common.EXE),
        "completed": False,
        "invalidated": False,
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
                command, cwd=common.ROOT, env=environment, stdout=stdout,
                stderr=stderr, check=False, timeout=cap + 45.0)
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
    if return_code != 0 or timed_out or not result_path.is_file():
        raise RuntimeError(f"default-off sentinel failed: {run_id}")
    result = common.load_json(result_path)
    print(json.dumps({
        "run_id": run_id,
        "certified": result.get("strict_certified_original_problem"),
        "work": result.get("external_gini_tree_work"),
        "seconds": result.get("final_process_wall_time_seconds"),
    }, sort_keys=True), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--process-cap", type=float, default=3600.0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    for instance_id in SENTINELS:
        for mode in ("implicit", "explicit"):
            run_one(instance_id, mode, args.process_cap, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
