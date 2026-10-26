#!/usr/bin/env python3
"""Run one or more frozen Round 43 diagnostic or exact rows."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any

import round43_common as common


def run_one(args: argparse.Namespace, instance_id: str) -> dict[str, Any]:
    identity = (
        f"{args.stage}__{instance_id}__{args.execution}__K{args.K0}__"
        f"d{args.depth}__rho{args.rho:g}__{args.score}__{args.envelope}")
    if args.tag:
        identity += f"__{args.tag}"
    run_dir = common.RUNS / identity
    result_path = run_dir / "result.json"
    if result_path.is_file() and not args.force:
        print(f"resume: {identity}", flush=True)
        return common.load_json(result_path)
    run_dir.mkdir(parents=True, exist_ok=True)
    item = common.inventory()[instance_id]
    command = common.fair_c6_command(
        item, run_dir, args.process_cap, execution=args.execution,
        K0=args.K0, depth=args.depth, rho=args.rho,
        score=args.score, envelope=args.envelope)
    record: dict[str, Any] = {
        "schema": "round43-run-v1",
        "round_id": 43,
        "stage": args.stage,
        "run_id": identity,
        "instance_id": instance_id,
        "instance_sha256": item["sha256"],
        "candidate_identity": {
            "family": "A(K0,d,rho)",
            "execution": args.execution,
            "K0": args.K0,
            "d": args.depth,
            "rho": args.rho,
            "score": args.score,
            "envelope": args.envelope,
            "width_measure": "g-mccormick-unit",
            "lifted_cuts": "off",
            "frontier_consolidation": "off",
        },
        "process_cap_seconds": args.process_cap,
        "watchdog_seconds": args.process_cap + 30.0,
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
        "run_id": identity,
        "return_code": return_code,
        "completed": record["completed"],
        "runner_wall_seconds": record["runner_wall_seconds"],
    }, sort_keys=True), flush=True)
    if return_code != 0 or timed_out or not result_path.is_file():
        raise RuntimeError(f"Round 43 row failed: {identity}")
    return common.load_json(result_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--instance", action="append", required=True)
    parser.add_argument("--execution", choices=("atlas", "algorithm"),
                        required=True)
    parser.add_argument("--K0", type=int, choices=(1, 4), required=True)
    parser.add_argument("--depth", type=int, choices=(1, 2), required=True)
    parser.add_argument("--rho", type=float, required=True)
    parser.add_argument("--score", choices=(
        "d", "max-d-c", "old", "no-adaptive"), default="d")
    parser.add_argument("--envelope", choices=(
        "none", "constant", "single", "iterated"), default="single")
    parser.add_argument("--process-cap", type=float, default=3600.0)
    parser.add_argument("--tag", default="")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not common.EXE.is_file():
        raise SystemExit(f"Round 43 executable missing: {common.EXE}")
    frozen = common.inventory()
    unknown = set(args.instance) - set(frozen)
    if unknown:
        raise SystemExit(f"instances are not frozen: {sorted(unknown)}")
    for instance_id in args.instance:
        run_one(args, instance_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
