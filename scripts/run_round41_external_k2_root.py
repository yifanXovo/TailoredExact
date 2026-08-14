#!/usr/bin/env python3
"""Run bounded external-K2 jobs to capture both complete initial LPs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time

import round41_common as common


def run_one(instance_id: str, process_cap: float, force: bool) -> None:
    run_id = f"root_reference__{instance_id}__external-k2"
    run_dir = common.RUNS / run_id
    result_path = run_dir / "result.json"
    if result_path.is_file() and not force:
        print(f"resume: {run_id}", flush=True)
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    item = common.inventory()[instance_id]
    command = common.fair_c6_command(item, run_dir, process_cap)
    common.round40.replace_all(command, "--frontier-intervals", 2)
    common.round40.replace_all(command, "--frontier-adaptive-split", False)
    common.round40.replace_all(
        command, "--external-gini-scheduling", "paper-lp-event")
    common.round40.replace_all(
        command, "--external-gini-lifecycle", "fresh-per-paper-event")
    record = {
        "schema": "round41-external-k2-root-run-v1",
        "round_id": 41,
        "run_id": run_id,
        "instance_id": instance_id,
        "instance_sha256": item["sha256"],
        "arm": "external-k2-root-diagnostic",
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
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(
            command, cwd=common.ROOT, env=environment,
            stdout=stdout, stderr=stderr, check=False,
            timeout=record["watchdog_seconds"])
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
        "run_id": run_id,
        "return_code": completed.returncode,
        "completed": record["completed"],
        "runner_wall_seconds": record["runner_wall_seconds"],
    }, sort_keys=True), flush=True)
    if completed.returncode != 0 or not result_path.is_file():
        raise RuntimeError(f"external-K2 root row failed: {run_id}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", action="append", default=[])
    parser.add_argument("--panel", action="store_true")
    parser.add_argument("--process-cap", type=float, default=60.0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not 0.0 < args.process_cap < 3600.0:
        raise SystemExit("process cap must be in (0,3600)")
    instances = list(args.instance)
    if args.panel:
        instances.extend(row["instance_id"] for row in common.csv_rows(
            common.OUT / "diagnostic_panel_manifest.csv"))
    instances = list(dict.fromkeys(instances))
    if not instances:
        raise SystemExit("select --panel and/or at least one --instance")
    unknown = set(instances) - set(common.inventory())
    if unknown:
        raise SystemExit(f"instances are not frozen: {sorted(unknown)}")
    for instance_id in instances:
        run_one(instance_id, args.process_cap, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
