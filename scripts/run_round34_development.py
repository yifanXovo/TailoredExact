#!/usr/bin/env python3
"""Run the predeclared heuristic-only Round 34 development subset."""

from __future__ import annotations

import json
import math
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import round34_common as common


def verification_passed(result: dict[str, Any]) -> bool:
    verification = result.get("verification", {})
    return bool(
        verification.get("original_solution_feasible")
        and verification.get("original_objective_recomputed")
        and verification.get("objective_matches")
        and not verification.get("errors"))


def main() -> int:
    build = common.load_json(common.OUT / "stage0_build_and_tests.json")
    if not build.get("passed") or common.sha256(common.EXE) != build[
            "gurobi_executable_sha256"]:
        raise RuntimeError("Round 34 build identity is unavailable")
    items = common.inventory()
    selected = common.csv_rows(common.DEVELOPMENT_MANIFEST)
    if len(selected) != 7:
        raise RuntimeError("development manifest must contain seven identities")
    common.DEVELOPMENT_RUNS.mkdir(parents=True, exist_ok=False)
    rows: list[dict[str, Any]] = []
    order = 0
    for selected_item in selected:
        item = items[selected_item["instance_id"]]
        for arm in common.STARTUP_ARMS:
            order += 1
            run_id = f"development__{item['instance_id']}__{arm.lower().replace('-', '_')}"
            directory = common.DEVELOPMENT_RUNS / run_id
            directory.mkdir(parents=True)
            command = common.development_command(item, arm, directory)
            common.write_json(directory / "command.json", {
                "schema": "round34-development-command-v1",
                "round_id": 34,
                "stage": "development",
                "run_id": run_id,
                "instance_id": item["instance_id"],
                "instance_sha256": item["sha256"],
                "arm": arm,
                "startup_variant": common.startup_definition(arm)[
                    "startup_variant"],
                "serial_order": order,
                "source_commit": build["source_commit"],
                "executable_sha256": common.sha256(common.EXE),
                "command": command,
                "licensed_solver_used": False,
            })
            started = time.monotonic()
            with (directory / "console.stdout.log").open("wb") as stdout, \
                 (directory / "console.stderr.log").open("wb") as stderr:
                completed = subprocess.run(
                    command, cwd=common.ROOT, env={
                        **os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                    stdout=stdout, stderr=stderr, timeout=300, check=False)
            result_path = directory / "result.json"
            if completed.returncode != 0 or not result_path.is_file():
                raise RuntimeError(
                    f"development row failed: {run_id}: {completed.returncode}")
            result = common.load_json(result_path)
            passed = verification_passed(result)
            row = {
                "round_id": 34,
                "stage": "development",
                "run_id": run_id,
                "serial_order": order,
                "instance_id": item["instance_id"],
                "instance_sha256": item["sha256"],
                "V": item["V"],
                "M": item["M"],
                "Q": item["Q"],
                "scenario": item["scenario"],
                "arm": arm,
                "startup_variant": common.startup_definition(arm)[
                    "startup_variant"],
                "process_wall_seconds": time.monotonic() - started,
                "reported_runtime_seconds": float(result.get(
                    "runtime_seconds", 0.0)),
                "verified_incumbent_objective": float(result.get(
                    "objective", result.get("upper_bound", math.nan))),
                "verifier_passed": passed,
                "hga_wall_time_seconds": float(result.get(
                    "hga_wall_time_seconds", 0.0)),
                "hga_total_generations": int(result.get(
                    "hga_total_generations", 0)),
                "hga_generations_since_improvement": int(result.get(
                    "hga_generations_since_improvement", 0)),
                "hga_objective_improvement_count": int(result.get(
                    "hga_objective_improvement_count", 0)),
                "hga_final_fitness": float(result.get(
                    "hga_final_fitness", 0.0)),
                "return_code": completed.returncode,
                "passed": passed,
            }
            rows.append(row)
            common.write_json(directory / "completion_marker.json", row)
            print(f"{order}/21 {arm} {item['instance_id']} passed={passed}",
                  flush=True)
            if not passed:
                raise RuntimeError(f"development verifier failed: {run_id}")
            common.write_csv(
                common.OUT / "hga_development_results.partial.csv", rows)
    common.write_csv(common.OUT / "hga_development_results.csv", rows)
    (common.OUT / "hga_development_results.partial.csv").unlink(
        missing_ok=True)
    full = {row["instance_id"]: row for row in rows
            if row["arm"] == "C6-HGA-FULL"}
    light = {row["instance_id"]: row for row in rows
             if row["arm"] == "C6-HGA-LIGHT"}
    summary = {
        "schema": "round34-development-summary-v1",
        "round_id": 34,
        "source_commit": build["source_commit"],
        "executable_sha256": common.sha256(common.EXE),
        "rows": len(rows),
        "all_verifier_passed": all(row["passed"] for row in rows),
        "light_matches_full_fitness": sum(
            abs(light[name]["hga_final_fitness"] -
                full[name]["hga_final_fitness"]) <= 1e-12 for name in full),
        "light_matches_full_verified_objective": sum(
            abs(light[name]["verified_incumbent_objective"] -
                full[name]["verified_incumbent_objective"]) <= 1e-10
            for name in full),
        "simple_verifier_passed": sum(
            row["passed"] for row in rows
            if row["arm"] == "C6-SIMPLE-START"),
        "hga_light_selected": True,
        "hga_light_no_improve_generations": 1000,
        "completed_at_unix_seconds": time.time(),
    }
    common.write_json(common.OUT / "round34_development_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
