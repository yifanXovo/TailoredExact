#!/usr/bin/env python3
"""Verify omitted Round 40 flags preserve the explicit-off C6 path."""

from __future__ import annotations

import json
import os
import subprocess
import time
from typing import Any

import round40_common as common


PANEL = (
    "round39_small_easy_V10_M1_Q30_slot04_seed1099392856",
    "round39_small_medium_V8_M3_Q30_slot03_seed1177285734",
    "round39_small_easy_V12_M3_Q30_slot08_seed1167625600",
)
ARMS = ("C6-IMPLICIT-DEFAULT", "C6-EXPLICIT-OFF")
PROCESS_CAP = 10800.0


def manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    inventory = common.inventory()
    serial = 0
    for instance_id in PANEL:
        item = inventory[instance_id]
        for arm in ARMS:
            serial += 1
            rows.append({
                "round_id": 40,
                "audit": "default_c6_equivalence",
                "serial_order": serial,
                "run_id": (f"default_equivalence__{instance_id}__" +
                           ("implicit" if arm == ARMS[0] else "explicit_off")),
                "instance_id": instance_id,
                "instance_sha256": item["sha256"],
                "difficulty_stratum": item["difficulty_stratum"],
                "V": item["V"],
                "M": item["M"],
                "Q": item["Q"],
                "arm": arm,
                "round40_flags": "omitted" if arm == ARMS[0] else "off",
                "gurobi_presolve": -1,
                "process_cap_seconds": PROCESS_CAP,
                "watchdog_seconds": PROCESS_CAP + 180.0,
            })
    return rows


def run_one(row: dict[str, Any]) -> None:
    run_dir = common.RUNS / str(row["run_id"])
    result_path = run_dir / "result.json"
    if result_path.is_file():
        print(f"resume: {row['run_id']}", flush=True)
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    item = common.inventory()[str(row["instance_id"])]
    command = common.fair_command(
        item, "C6-HGA-FULL-K4", run_dir, -1, PROCESS_CAP)
    if row["round40_flags"] == "off":
        command.extend((
            "--round40-c6-coarse-start", "off",
            "--round40-c6-ub-geometry", "off"))
    record = {
        "schema": "round40-default-equivalence-run-v1",
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
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(
            command, cwd=common.ROOT, env=environment,
            stdout=stdout, stderr=stderr, check=False,
            timeout=float(row["watchdog_seconds"]))
    record.update({
        "completed": result_path.is_file(),
        "return_code": completed.returncode,
        "watchdog_timeout": False,
        "runner_wall_seconds": time.monotonic() - started,
        "stdout_path": common.relative(stdout_path),
        "stderr_path": common.relative(stderr_path),
    })
    common.write_json(run_dir / "command.json", record)
    print(json.dumps({
        "run_id": row["run_id"],
        "return_code": completed.returncode,
        "completed": record["completed"],
        "runner_wall_seconds": record["runner_wall_seconds"],
    }, sort_keys=True), flush=True)
    if completed.returncode != 0 or not result_path.is_file():
        raise RuntimeError(f"default-equivalence row failed: {row['run_id']}")


def main() -> int:
    rows = manifest()
    common.write_csv(common.OUT / "default_c6_equivalence_manifest.csv", rows)
    start_path = common.OUT / "default_c6_equivalence_start.json"
    if not start_path.exists():
        common.write_json(start_path, {
            "schema": "round40-default-equivalence-start-v1",
            "frozen_before_results": True,
            "panel": list(PANEL),
            "arms": list(ARMS),
            "row_count": len(rows),
            "executable_sha256": common.sha256(common.EXE),
        })
    for row in rows:
        run_one(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
