#!/usr/bin/env python3
"""Run the trajectory-motivated decisive K=1 revision."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from typing import Any

import round40_common as common
import run_round40_k1 as original


ARM = "C6-K1-ADAPTIVE-DECISIVE"


def manifest() -> list[dict[str, Any]]:
    inventory = common.inventory()
    rows: list[dict[str, Any]] = []
    for serial, (instance_id, role, smoke) in enumerate(
            original.PANEL, start=1):
        item = inventory[instance_id]
        rows.append({
            "round_id": 40,
            "part": 1,
            "iteration": 2,
            "serial_order": serial,
            "run_id": f"k1_iterative__{instance_id}__c6_k1_adaptive_decisive",
            "instance_id": instance_id,
            "instance_sha256": item["sha256"],
            "diagnostic_role": role,
            "smoke_subset": smoke,
            "difficulty_stratum": item["difficulty_stratum"],
            "V": item["V"],
            "M": item["M"],
            "Q": item["Q"],
            "arm": ARM,
            "coarse_start_policy": "k1-adaptive-decisive",
            "gurobi_presolve": -1,
            "process_cap_seconds": original.PROCESS_CAP,
            "shutdown_margin_seconds": common.SHUTDOWN_MARGIN,
            "watchdog_seconds": (original.PROCESS_CAP +
                                 original.WATCHDOG_MARGIN),
            "one_thread": True,
            "gurobi_seed": 0,
            "relative_gap": 0.0,
            "absolute_gap": 0.0,
            "selection_basis": "frozen_round40_k1_panel_iteration_2",
            "revision_basis": (
                "major witness showed rho split recreates fragmented jobs; "
                "refine only on child infeasibility or cutoff proof"),
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
    command = common.c6_policy_command(
        item, ARM, run_dir, float(row["process_cap_seconds"]))
    record = {
        "schema": "round40-k1-iteration2-run-v1", **row,
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
        raise RuntimeError(f"decisive K=1 row failed: {row['run_id']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("smoke", "full"),
                        default="smoke")
    parser.add_argument("--instance", action="append", default=[])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    rows = manifest()
    manifest_path = common.OUT / "k1_iterative_manifest.csv"
    common.write_csv(manifest_path, rows)
    start_path = common.OUT / "k1_iterative_official_start.json"
    if not start_path.exists():
        common.write_json(start_path, {
            "schema": "round40-k1-iteration2-start-v1",
            "round_id": 40,
            "part": 1,
            "iteration": 2,
            "frozen_before_results": True,
            "panel": [item[0] for item in original.PANEL],
            "arm": ARM,
            "row_count": len(rows),
            "presolve_policy": "gurobi-auto",
            "executable_sha256": common.sha256(common.EXE),
        })
    selected = rows if args.stage == "full" else [
        row for row in rows if row["smoke_subset"]]
    if args.instance:
        requested = set(args.instance)
        known = {row["instance_id"] for row in rows}
        if requested - known:
            raise SystemExit(
                f"instances are not predeclared: {sorted(requested - known)}")
        selected = [row for row in rows if row["instance_id"] in requested]
    for row in selected:
        run_one(row, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
