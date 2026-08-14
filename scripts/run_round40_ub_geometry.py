#!/usr/bin/env python3
"""Run the frozen full-panel Round 40 incumbent-stable geometry study."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from typing import Any

import round40_common as common


ARMS = ("C6-HGA-FULL-K4", "C6-NESTED-DYADIC-K4")
SMOKE = {
    "round39_small_easy_V10_M1_Q30_slot04_seed1099392856",
    "round39_small_easy_V12_M3_Q30_slot08_seed1167625600",
    "round39_small_medium_V8_M3_Q30_slot03_seed1177285734",
    "round39_small_medium_V10_M2_Q20_slot05_seed968549317",
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363",
    "round39_small_hard_V12_M3_Q20_slot07_seed621538683",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114",
}
PROCESS_CAP = 10800.0
WATCHDOG_MARGIN = 180.0


def slug(value: str) -> str:
    return value.lower().replace("-", "_")


def manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    serial = 0
    for item in common.inventory().values():
        for arm in ARMS:
            serial += 1
            instance_id = str(item["instance_id"])
            rows.append({
                "round_id": 40,
                "part": 2,
                "serial_order": serial,
                "run_id": f"ub_geometry__{instance_id}__{slug(arm)}",
                "instance_id": instance_id,
                "instance_sha256": item["sha256"],
                "smoke_subset": instance_id in SMOKE,
                "difficulty_stratum": item["difficulty_stratum"],
                "V": item["V"],
                "M": item["M"],
                "Q": item["Q"],
                "arm": arm,
                "ub_geometry_policy": (
                    "off" if arm == "C6-HGA-FULL-K4"
                    else "nested-dyadic-k4"),
                "gurobi_presolve": -1,
                "process_cap_seconds": PROCESS_CAP,
                "shutdown_margin_seconds": common.SHUTDOWN_MARGIN,
                "watchdog_seconds": PROCESS_CAP + WATCHDOG_MARGIN,
                "one_thread": True,
                "gurobi_seed": 0,
                "relative_gap": 0.0,
                "absolute_gap": 0.0,
                "selection_basis": "full_frozen_round39_24_instance_panel",
                "mechanism_uses_historical_outcome": False,
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
    command = common.c6_ub_geometry_command(
        item, str(row["arm"]), run_dir,
        float(row["process_cap_seconds"]))
    record = {
        "schema": "round40-ub-geometry-run-v1",
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
        "run_id": row["run_id"],
        "return_code": return_code,
        "completed": record["completed"],
        "runner_wall_seconds": record["runner_wall_seconds"],
    }, sort_keys=True), flush=True)
    if return_code != 0 or timed_out or not result_path.is_file():
        raise RuntimeError(f"UB-geometry row failed: {row['run_id']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "full"),
                        default="smoke")
    parser.add_argument("--instance", action="append", default=[])
    parser.add_argument("--arm", action="append", choices=ARMS, default=[])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not common.EXE.is_file():
        raise SystemExit(f"Round 40 executable missing: {common.EXE}")
    rows = manifest()
    common.OUT.mkdir(parents=True, exist_ok=True)
    common.write_csv(common.OUT / "ub_geometry_manifest.csv", rows)
    start_path = common.OUT / "ub_geometry_official_start.json"
    if not start_path.exists():
        common.write_json(start_path, {
            "schema": "round40-ub-geometry-start-v1",
            "round_id": 40,
            "part": 2,
            "frozen_before_results": True,
            "panel_source": (
                "results/gf_small_hard_light_round39/"
                "frozen_instance_manifest.csv"),
            "instance_count": 24,
            "arms": list(ARMS),
            "row_count": len(rows),
            "smoke_instances": sorted(SMOKE),
            "presolve_policy": "gurobi-auto",
            "executable_sha256": common.sha256(common.EXE),
            "source_head": subprocess.check_output(
                ("git", "rev-parse", "HEAD"), cwd=common.ROOT,
                text=True).strip(),
        })
    selected = rows if args.stage == "full" else [
        row for row in rows if row["smoke_subset"]]
    if args.instance:
        requested = set(args.instance)
        known = {str(row["instance_id"]) for row in rows}
        if requested - known:
            raise SystemExit(
                f"instances are not frozen: {sorted(requested - known)}")
        selected = [row for row in rows if row["instance_id"] in requested]
    if args.arm:
        selected = [row for row in selected if row["arm"] in args.arm]
    for row in selected:
        run_one(row, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
