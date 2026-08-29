#!/usr/bin/env python3
"""Run one explicit Round 42 static block or a fixed two-block cover."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time
from typing import Any

import round42_common as common


STATIC_ARMS = (
    "st-k2-p-core-reference",
    "st-k4-p-core",
    "st-k4-p-core-hierarchical",
    "st-k4-p-core-factored",
    "external-k2-left",
    "external-k2-right",
    "paired-k4-lower",
    "paired-k4-upper",
    "paired-k4-lower-factored",
    "paired-k4-upper-factored",
)

COMPOSITES = {
    "external-k2-fixed": ("external-k2-left", "external-k2-right"),
    "paired-k4": ("paired-k4-lower", "paired-k4-upper"),
    "paired-k4-factored": (
        "paired-k4-lower-factored", "paired-k4-upper-factored"),
}


def exact_start(run_dir: Path) -> float:
    """Return the process-entry timestamp of the exact phase."""
    path = run_dir / "process_phases.csv"
    if not path.is_file():
        return 0.0
    matches = []
    for row in common.csv_rows(path):
        if row.get("event") == "exact_phase_start":
            try:
                matches.append(float(row.get("process_seconds", 0.0)))
            except (TypeError, ValueError):
                pass
    return matches[-1] if matches else 0.0


def run_one(instance_id: str, arm: str, solve: str,
            process_cap: float, force: bool,
            tag: str = "") -> dict[str, Any]:
    suffix = f"__{tag}" if tag else ""
    run_id = f"static__{instance_id}__{arm}__{solve}{suffix}"
    run_dir = common.RUNS / run_id
    result_path = run_dir / "result.json"
    if result_path.is_file() and not force:
        print(f"resume: {run_id}", flush=True)
        return common.load_json(result_path)
    run_dir.mkdir(parents=True, exist_ok=True)
    item = common.inventory()[instance_id]
    command = common.fair_c6_command(item, run_dir, process_cap)
    if arm == "st-k2-p-core-reference":
        command.extend((
            "--round41-static-segmented-gini", "st-k2-p-core",
            "--round41-static-segmented-solve", solve,
        ))
    else:
        command.extend((
            "--round42-static-architecture", arm,
            "--round42-static-solve", solve,
        ))
    record: dict[str, Any] = {
        "schema": "round42-static-run-v1",
        "round_id": 42,
        "run_id": run_id,
        "instance_id": instance_id,
        "instance_sha256": item["sha256"],
        "arm": arm,
        "solve": solve,
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
        "run_id": run_id,
        "return_code": return_code,
        "completed": record["completed"],
        "runner_wall_seconds": record["runner_wall_seconds"],
    }, sort_keys=True), flush=True)
    if return_code != 0 or timed_out or not result_path.is_file():
        raise RuntimeError(f"Round 42 row failed: {run_id}")
    return common.load_json(result_path)


def run_composite(instance_id: str, composite: str, solve: str,
                  process_cap: float, force: bool,
                  tag: str = "") -> dict[str, Any]:
    component_results = [
        run_one(instance_id, arm, solve, process_cap, force, tag)
        for arm in COMPOSITES[composite]
    ]
    suffix = f"__{tag}" if tag else ""
    component_run_dirs = [
        common.RUNS /
        f"static__{instance_id}__{arm}__{solve}{suffix}"
        for arm in COMPOSITES[composite]
    ]
    summary_dir = common.RUNS / (
        f"composite__{instance_id}__{composite}__{solve}{suffix}")
    summary_dir.mkdir(parents=True, exist_ok=True)
    strict_components = all(bool(row.get(
        "round42_block_strict_certificate", False))
        for row in component_results)
    native_exact_components = all(
        bool(row.get("round41_static_segmented_technical_feasible", False))
        and bool(row.get("round41_static_one_native_mip_job", False))
        and bool(row.get("round41_static_parameter_roundtrip_valid", False))
        and str(row.get("round41_static_native_status", "")) in {
            "OPTIMAL", "INFEASIBLE"}
        and (str(row.get("round41_static_native_status", "")) == "INFEASIBLE"
             or bool(row.get("round41_static_native_bound_available", False)))
        for row in component_results)
    verifier_components = all(bool(row.get(
        "round41_static_original_verifier_passed", False))
        for row in component_results)
    objectives = [float(row["objective"]) for row in component_results]
    bounds = [float(row.get(
        "round41_static_native_bound", row.get("lower_bound", 0.0)))
        for row in component_results]
    union_objective = min(objectives)
    union_bound = min(bounds)
    union_bound_matches_verified_objective = (
        abs(union_bound - union_objective) <=
        1e-7 * max(1.0, abs(union_objective)))
    summary = {
        "schema": "round42-static-composite-v1",
        "round_id": 42,
        "instance_id": instance_id,
        "instance_sha256": common.inventory()[instance_id]["sha256"],
        "arm": composite,
        "solve": solve,
        "component_arms": list(COMPOSITES[composite]),
        "component_model_sha256": [row.get(
            "round41_static_segmented_model_sha256", "")
            for row in component_results],
        "complete_gap_free_cover": True,
        "independent_integer_proof_jobs": sum(int(row.get(
            "round41_static_integer_proof_job_count", 0))
            for row in component_results),
        "native_optimize_calls": sum(int(row.get(
            "round41_static_optimize_count", 0))
            for row in component_results),
        "strict_component_certificates": strict_components,
        "native_exact_component_certificates": native_exact_components,
        "original_problem_verifier_passed": verifier_components,
        "strict_global_union_certificate": (
            solve == "mip" and native_exact_components and
            verifier_components and union_bound_matches_verified_objective),
        "union_bound_matches_verified_objective":
            union_bound_matches_verified_objective,
        "objective": union_objective,
        "valid_lower_bound": union_bound,
        "exact_phase_seconds": sum(max(
            0.0,
            float(row.get("final_process_wall_time_seconds",
                          row.get("runtime_seconds", 0.0))) -
            exact_start(run_dir))
            for row, run_dir in zip(component_results, component_run_dirs)),
        "total_process_seconds": sum(float(row.get(
            "final_process_wall_time_seconds",
            row.get("runtime_seconds", 0.0)))
            for row in component_results),
        "hga_startup_seconds": sum(float(row.get(
            "round36_hga_start_seconds", 0.0))
            for row in component_results),
        "solver_work": sum(float(row.get(
            "round41_static_solver_work", 0.0))
            for row in component_results),
        "solver_nodes": sum(float(row.get(
            "round41_static_solver_nodes", 0.0))
            for row in component_results),
        "model_variables": sum(int(row.get(
            "round41_static_model_variables", 0))
            for row in component_results),
        "model_binary_variables": sum(int(row.get(
            "round41_static_model_binary_variables", 0))
            for row in component_results),
        "model_integer_variables": sum(int(row.get(
            "round41_static_model_integer_variables", 0))
            for row in component_results),
        "model_continuous_variables": sum(int(row.get(
            "round41_static_model_continuous_variables", 0))
            for row in component_results),
        "model_linear_constraints": sum(int(row.get(
            "round41_static_model_linear_constraints", 0))
            for row in component_results),
        "model_nonzeros": sum(int(row.get(
            "round41_static_model_nonzeros", 0))
            for row in component_results),
        "model_general_constraints": sum(int(row.get(
            "round41_static_model_general_constraints", 0))
            for row in component_results),
        "model_build_seconds": sum(float(row.get(
            "round41_static_model_build_seconds", 0.0))
            for row in component_results),
        "model_read_seconds": sum(float(row.get(
            "round41_static_model_read_seconds", 0.0))
            for row in component_results),
        "accepted_outcome": solve == "root-lp" or (
            native_exact_components and verifier_components and
            union_bound_matches_verified_objective),
        "false_certificate": bool(
            solve == "mip" and native_exact_components and
            union_bound_matches_verified_objective and
            not verifier_components),
        "executable_sha256": common.sha256(common.EXE),
    }
    common.write_json(summary_dir / "composite_summary.json", summary)
    print(json.dumps({
        "composite": composite,
        "instance_id": instance_id,
        "strict": summary["strict_global_union_certificate"],
        "time": summary["exact_phase_seconds"],
        "work": summary["solver_work"],
    }, sort_keys=True), flush=True)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", action="append", required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--arm", action="append", choices=STATIC_ARMS)
    group.add_argument("--composite", action="append",
                       choices=tuple(COMPOSITES))
    parser.add_argument("--solve", choices=("root-lp", "mip"),
                        default="root-lp")
    parser.add_argument("--process-cap", type=float, default=300.0)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    if not common.EXE.is_file():
        raise SystemExit(f"Round 42 executable missing: {common.EXE}")
    known = common.inventory()
    unknown = set(args.instance) - set(known)
    if unknown:
        raise SystemExit(f"instances are not frozen: {sorted(unknown)}")
    for instance_id in args.instance:
        for arm in args.arm or []:
            run_one(instance_id, arm, args.solve,
                    args.process_cap, args.force, args.tag)
        for composite in args.composite or []:
            run_composite(instance_id, composite, args.solve,
                          args.process_cap, args.force, args.tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
