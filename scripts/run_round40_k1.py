#!/usr/bin/env python3
"""Run the predeclared Round 40 K=1 diagnostic panel."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from typing import Any

import round40_common as common


# Historical outcomes define diagnostic roles only; they are never inputs to
# the mechanism or a run-time policy. The complete panel is frozen before the
# first K=1 result.
PANEL = (
    ("round39_small_easy_V10_M1_Q30_slot04_seed1099392856",
     "round39_easy_p_grb_win", False),
    ("round39_small_easy_V12_M3_Q30_slot08_seed1167625600",
     "round39_easy_p_grb_win_largest_easy", True),
    ("round39_small_medium_V12_M3_Q30_slot08_seed1343324363",
     "major_round39_medium_regression", False),
    ("round39_small_medium_V8_M3_Q30_slot03_seed1177285734",
     "additional_medium_c6_win", True),
    ("round39_small_medium_V10_M2_Q20_slot05_seed968549317",
     "additional_medium_c6_win", False),
    ("round39_small_hard_V10_M1_Q30_slot02_seed1721447042",
     "round39_hard_p_grb_win", True),
    ("round39_small_hard_V10_M1_Q20_slot01_seed561355351",
     "round39_hard_p_grb_win", True),
    ("round39_small_hard_V12_M3_Q20_slot07_seed621538683",
     "round39_unresolved_endpoint_witness", False),
    ("round39_small_hard_V12_M3_Q30_slot08_seed1288546114",
     "strong_round39_c6_positive_control", False),
    ("round39_small_hard_V10_M3_Q20_slot04_seed1145042375",
     "additional_hard_c6_win", True),
)
ARMS = (
    "P-GRB",
    "C6-HGA-FULL-K4",
    "C6-K1-SINGLE",
    "C6-K1-ADAPTIVE",
)
PROCESS_CAP = 10800.0
WATCHDOG_MARGIN = 180.0


def slug(value: str) -> str:
    return value.lower().replace("-", "_")


def manifest() -> list[dict[str, Any]]:
    inventory = common.inventory()
    rows: list[dict[str, Any]] = []
    serial = 0
    for instance_id, role, smoke in PANEL:
        item = inventory[instance_id]
        for arm in ARMS:
            serial += 1
            run_id = f"k1__{instance_id}__{slug(arm)}"
            rows.append({
                "round_id": 40,
                "part": 1,
                "serial_order": serial,
                "run_id": run_id,
                "instance_id": instance_id,
                "instance_sha256": item["sha256"],
                "diagnostic_role": role,
                "smoke_subset": smoke,
                "difficulty_stratum": item["difficulty_stratum"],
                "V": item["V"],
                "M": item["M"],
                "Q": item["Q"],
                "arm": arm,
                "coarse_start_policy": {
                    "P-GRB": "not_applicable",
                    "C6-HGA-FULL-K4": "off",
                    "C6-K1-SINGLE": "k1-single",
                    "C6-K1-ADAPTIVE": "k1-adaptive",
                }[arm],
                "gurobi_presolve": -1,
                "process_cap_seconds": PROCESS_CAP,
                "shutdown_margin_seconds": common.SHUTDOWN_MARGIN,
                "watchdog_seconds": PROCESS_CAP + WATCHDOG_MARGIN,
                "one_thread": True,
                "gurobi_seed": 0,
                "relative_gap": 0.0,
                "absolute_gap": 0.0,
                "selection_basis": "predeclared_round39_diagnostic_roles",
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
    if row["arm"] == "P-GRB":
        command = common.fair_command(
            item, "P-GRB", run_dir, -1,
            float(row["process_cap_seconds"]))
    else:
        command = common.c6_policy_command(
            item, str(row["arm"]), run_dir,
            float(row["process_cap_seconds"]))
    record = {
        "schema": "round40-k1-run-v1", **row,
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
        raise RuntimeError(f"K=1 row failed: {row['run_id']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "full"),
                        default="smoke")
    parser.add_argument("--instance", action="append", default=[],
                        help="run only a predeclared instance (repeatable)")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not common.EXE.is_file():
        raise SystemExit(f"Round 40 executable missing: {common.EXE}")
    rows = manifest()
    common.OUT.mkdir(parents=True, exist_ok=True)
    manifest_path = common.OUT / "k1_diagnostic_manifest.csv"
    common.write_csv(manifest_path, rows)
    start_path = common.OUT / "k1_official_start.json"
    if not start_path.exists():
        common.write_json(start_path, {
            "schema": "round40-k1-start-v1",
            "round_id": 40,
            "part": 1,
            "frozen_before_results": True,
            "panel": [item[0] for item in PANEL],
            "arms": list(ARMS),
            "row_count": len(rows),
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
        known = {row["instance_id"] for row in rows}
        unknown = requested - known
        if unknown:
            raise SystemExit(
                f"instances are not in the frozen K=1 panel: {sorted(unknown)}")
        selected = [row for row in rows if row["instance_id"] in requested]
    for row in selected:
        run_one(row, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
