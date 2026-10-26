#!/usr/bin/env python3
"""Run the frozen Round 40 Off/Off and Auto/Auto presolve ablation."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import round40_common as common


WITNESSES = (
    ("round39_small_hard_V10_M1_Q30_slot02_seed1721447042",
     "short_round39_p_grb_regression"),
    ("round39_small_hard_V10_M3_Q20_slot04_seed1145042375",
     "round39_c6_positive_control"),
)
POLICIES = (("off", 0), ("auto", -1))
ARMS = ("P-GRB", "C6-HGA-FULL-K4")
PROCESS_CAP = 900.0
WATCHDOG_MARGIN = 90.0


def slug(value: str) -> str:
    return value.lower().replace("-", "_")


def manifest() -> list[dict[str, Any]]:
    inventory = common.inventory()
    rows: list[dict[str, Any]] = []
    serial = 0
    for instance_id, role in WITNESSES:
        item = inventory[instance_id]
        for policy, presolve in POLICIES:
            for arm in ARMS:
                serial += 1
                run_id = (f"presolve__{instance_id}__{policy}__"
                          f"{slug(arm)}")
                rows.append({
                    "round_id": 40,
                    "part": 0,
                    "serial_order": serial,
                    "run_id": run_id,
                    "instance_id": instance_id,
                    "instance_sha256": item["sha256"],
                    "diagnostic_role": role,
                    "V": item["V"],
                    "M": item["M"],
                    "Q": item["Q"],
                    "arm": arm,
                    "presolve_policy": policy,
                    "gurobi_presolve_value": presolve,
                    "process_cap_seconds": PROCESS_CAP,
                    "shutdown_margin_seconds": common.SHUTDOWN_MARGIN,
                    "watchdog_seconds": PROCESS_CAP + WATCHDOG_MARGIN,
                    "one_thread": True,
                    "gurobi_seed": 0,
                    "relative_gap": 0.0,
                    "absolute_gap": 0.0,
                })
    return rows


def run_one(row: dict[str, Any], force: bool) -> None:
    run_dir = common.RUNS / str(row["run_id"])
    result_path = run_dir / "result.json"
    if result_path.is_file() and not force:
        print(f"resume: {row['run_id']}", flush=True)
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    item = common.inventory()[str(row["instance_id"])]
    command = common.fair_command(
        item, str(row["arm"]), run_dir,
        int(row["gurobi_presolve_value"]),
        float(row["process_cap_seconds"]))
    record = {
        "schema": "round40-presolve-run-v1",
        **row,
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
                timeout=float(row["watchdog_seconds"]))
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
        "run_id": row["run_id"], "return_code": return_code,
        "completed": record["completed"],
        "runner_wall_seconds": record["runner_wall_seconds"],
    }, sort_keys=True), flush=True)
    if return_code != 0 or timed_out or not result_path.is_file():
        raise RuntimeError(f"presolve row failed: {row['run_id']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not common.EXE.is_file():
        raise SystemExit(f"Round 40 executable missing: {common.EXE}")
    rows = manifest()
    common.OUT.mkdir(parents=True, exist_ok=True)
    common.write_csv(common.PRESOLVE_MANIFEST, rows)
    common.write_json(common.OUT / "presolve_official_start.json", {
        "schema": "round40-presolve-start-v1",
        "round_id": 40,
        "part": 0,
        "frozen_before_results": True,
        "witnesses": [row[0] for row in WITNESSES],
        "policies": {name: value for name, value in POLICIES},
        "arms": list(ARMS),
        "row_count": len(rows),
        "executable_sha256": common.sha256(common.EXE),
        "source_head": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), cwd=common.ROOT,
            text=True).strip(),
    })
    for row in rows:
        run_one(row, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
