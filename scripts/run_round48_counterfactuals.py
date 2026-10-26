#!/usr/bin/env python3
"""Run the two frozen matched RETAIN/MIDPOINT diagnostic pairs."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

import round48_common as common


CASES = (
    {
        "case": "U1_root",
        "instance": common.MECHANISM[4],
        "interval": "L0",
        "purpose": "suspected_under_refinement_root",
    },
    {
        "case": "tight3102_L0_0",
        "instance": "tight_T_seed3102",
        "interval": "L0.0",
        "purpose": "first_exact_historical_divergence",
    },
)


def normalized(path: Path) -> dict:
    value = common.load_json(path)
    return value[0] if isinstance(value, list) else value


def run_case(case: dict, arm: str, executable: Path,
             process_cap: float, force: bool) -> dict:
    run_id = f"{case['case']}__{arm}"
    run_dir = common.OUT / "counterfactual_runs" / run_id
    marker_path = run_dir / "completion_marker.json"
    if marker_path.is_file() and not force:
        return common.load_json(marker_path)
    run_dir.mkdir(parents=True, exist_ok=True)
    marker_path.unlink(missing_ok=True)
    item = common.frozen_instances()[case["instance"]]
    command = common.counterfactual_command(
        item, run_dir, process_cap, case["interval"], arm, executable)
    record = {
        "schema": "round48-counterfactual-command-v1",
        "run_id": run_id, **case, "arm": arm,
        "diagnostic_not_original_problem_certificate": True,
        "further_recursive_splits_forbidden": arm == "midpoint",
        "process_cap_seconds": process_cap,
        "executable_path": str(executable),
        "executable_sha256": common.sha256(executable),
        "input_sha256": item["sha256"], "command": command,
    }
    common.write_json(run_dir / "command.json", record)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    with (run_dir / "stdout.log").open("wb") as stdout, \
            (run_dir / "stderr.log").open("wb") as stderr:
        try:
            process = subprocess.run(
                command, cwd=common.ROOT, env=env, stdout=stdout,
                stderr=stderr, timeout=process_cap + 45.0, check=False)
            return_code, watchdog = process.returncode, False
        except subprocess.TimeoutExpired:
            return_code, watchdog = -1, True
    result_path = run_dir / "result.json"
    if return_code or watchdog or not result_path.is_file():
        raise RuntimeError(
            f"counterfactual failed: {run_id}, rc={return_code}, "
            f"watchdog={watchdog}")
    result = normalized(result_path)
    if not result.get("round48_counterfactual_performed"):
        raise RuntimeError(f"counterfactual target was not performed: {run_id}")
    marker = {
        "schema": "round48-counterfactual-completion-v1", "complete": True,
        "run_id": run_id, **case, "arm": arm,
        "diagnostic_not_original_problem_certificate": True,
        "process_cap_seconds": process_cap,
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code, "watchdog_timeout": watchdog,
        "executable_sha256": common.sha256(executable),
        "command_sha256": common.sha256(run_dir / "command.json"),
        "result_sha256": common.sha256(result_path),
        "counterfactual_performed": True,
        "descendant_split_suppression_count": result.get(
            "round48_counterfactual_descendant_split_suppression_count", 0),
        "local_exact": result.get("status") == "round48_counterfactual_exact",
        "status": result.get("status"),
    }
    common.write_json(marker_path, marker)
    print(json.dumps(marker, sort_keys=True), flush=True)
    return marker


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--process-cap", type=float, default=1200.0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.process_cap <= 0 or args.process_cap > 1200:
        raise SystemExit("counterfactual cap must satisfy 0 < cap <= 1200")
    executable = args.executable.resolve()
    if not executable.is_file():
        raise SystemExit(f"official executable missing: {executable}")
    if "dev-gurobi-release" in executable.as_posix().lower():
        raise SystemExit("counterfactual diagnostics must use the official executable")
    markers = [run_case(case, arm, executable, args.process_cap, args.force)
               for case in CASES for arm in ("retain", "midpoint")]
    hashes = {marker["executable_sha256"] for marker in markers}
    if len(hashes) != 1 or not all(marker["complete"] for marker in markers):
        raise RuntimeError("counterfactual pair completion/hash invariant failed")
    common.write_json(common.OUT / "counterfactual_completion.json", {
        "schema": "round48-counterfactual-pairs-completion-v1",
        "complete": True, "row_count": len(markers),
        "executable_sha256": next(iter(hashes)),
        "rows": [marker["run_id"] for marker in markers],
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
