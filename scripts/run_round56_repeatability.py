#!/usr/bin/env python3
"""Rerun and compare the three frozen Round 56 repeatability sentinels."""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import round56_common as r56
import run_round56_official as official


REPETITION_ID = "repeat-1"
RAW = r56.EVIDENCE / "local_raw" / "repeatability"
SENTINELS = ((8, 1, 30, 1800), (20, 3, 30, 10800), (50, 5, 30, 18000))
PATH_OPTIONS = {
    "--progress-log", "--process-phase-ledger", "--external-gini-artifact-dir",
    "--primal-heuristic-generation-log", "--heuristic-candidates-csv", "--log", "--out",
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        if len(value) != 1:
            raise RuntimeError(f"expected one result in {path}")
        value = value[0]
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object in {path}")
    return value


def descriptors() -> list[dict[str, Any]]:
    selected = []
    for descriptor in official.descriptors():
        key = (int(descriptor["V"]), int(descriptor["M"]), int(descriptor["Q"]), int(descriptor["route_time_limit_seconds"]))
        if key in SENTINELS:
            selected.append(descriptor)
    if {(
        int(row["V"]), int(row["M"]), int(row["Q"]), int(row["route_time_limit_seconds"])
    ) for row in selected} != set(SENTINELS):
        raise RuntimeError("frozen repeatability sentinel lookup failed")
    return selected


def normalize_command(command: list[str]) -> list[str]:
    normalized: list[str] = []
    index = 0
    while index < len(command):
        token = command[index]
        if token in PATH_OPTIONS:
            normalized.extend((token, "<RUN_PATH>"))
            index += 2
        elif token == "--round56-run-identity-sha256":
            normalized.extend((token, "<RUN_IDENTITY>"))
            index += 2
        else:
            normalized.append(token)
            index += 1
    return normalized


def same_number(left: Any, right: Any, tolerance: float = 1e-9) -> bool:
    if left is None or right is None:
        return left is right
    return math.isclose(float(left), float(right), rel_tol=tolerance, abs_tol=tolerance)


def canonical_routes(result: dict[str, Any]) -> str:
    return r56.canonical_json(result.get("routes", []))


def compare(descriptor: dict[str, Any], repeated: dict[str, Any], repeated_command: list[str]) -> dict[str, Any]:
    scenario_id = descriptor["scenario_id"]
    original_dir = official.RAW / scenario_id
    original = load_json(original_dir / "result.json")
    original_command = load_json(original_dir / "command.json")["command"]
    original_class = official.classify(original)
    repeated_class = official.classify(repeated)
    original_verification = original.get("verification") or {}
    repeated_verification = repeated.get("verification") or {}
    objective_agrees = same_number(original.get("objective"), repeated.get("objective"))
    certificate_agrees = original_class == repeated_class and bool(original.get("strict_certified_original_problem")) == bool(repeated.get("strict_certified_original_problem"))
    verifier_agrees = bool(original_verification.get("original_solution_feasible")) == bool(repeated_verification.get("original_solution_feasible"))
    mathematical_identity_agrees = original.get("mathematical_instance_sha256") == repeated.get("mathematical_instance_sha256") == descriptor["mathematical_instance_sha256"]
    run_identity_differs = original.get("run_identity_sha256") != repeated.get("run_identity_sha256")
    parameter_contract_agrees = normalize_command(original_command) == normalize_command(repeated_command)
    final_inventory_agrees = original_verification.get("final_inventories") == repeated_verification.get("final_inventories")
    native_route_agrees = canonical_routes(original) == canonical_routes(repeated)
    multiple_optimum_variation_allowed = objective_agrees and certificate_agrees and verifier_agrees and (not final_inventory_agrees or not native_route_agrees)
    passed = all((objective_agrees, certificate_agrees, verifier_agrees, mathematical_identity_agrees, run_identity_differs, parameter_contract_agrees))
    return {
        "scenario_id": scenario_id, "V": descriptor["V"], "M": descriptor["M"], "Q": descriptor["Q"],
        "T": descriptor["route_time_limit_seconds"], "solver_process_cap_seconds": descriptor["solver_process_cap_seconds"],
        "original_solution_class": original_class, "repeat_solution_class": repeated_class,
        "original_objective": original.get("objective"), "repeat_objective": repeated.get("objective"),
        "objective_agrees": objective_agrees, "certificate_class_agrees": certificate_agrees,
        "verifier_outcome_agrees": verifier_agrees, "mathematical_instance_identity_agrees": mathematical_identity_agrees,
        "run_identity_differs_only_by_repetition_context": run_identity_differs and parameter_contract_agrees,
        "solver_parameter_contract_agrees": parameter_contract_agrees,
        "original_work": original.get("external_gini_tree_work"), "repeat_work": repeated.get("external_gini_tree_work"),
        "original_nodes": original.get("external_gini_tree_nodes"), "repeat_nodes": repeated.get("external_gini_tree_nodes"),
        "original_split_count": original.get("external_gini_tree_split_count"), "repeat_split_count": repeated.get("external_gini_tree_split_count"),
        "final_inventory_agrees": final_inventory_agrees, "native_route_witness_agrees": native_route_agrees,
        "objective_equivalent_witness_variation_allowed": multiple_optimum_variation_allowed,
        "passed": passed,
    }


def write_audit(rows: list[dict[str, Any]]) -> None:
    r56.write_csv(r56.EVIDENCE / "repeatability_results.csv", rows)
    lines = [
        "# Round 56 repeatability audit", "",
        f"All three frozen sentinels passed: **{str(all(row['passed'] for row in rows)).lower()}**.", "",
        "The repeat used the same source, executable, mathematical scenario, K1-AM-SF preset, solver parameter contract, route horizon, and process cap. The run identity changed only because the frozen repetition identifier was `repeat-1` and output paths were repetition-specific.", "",
        "A different route or final inventory is not treated as a correctness failure when the certified objective, certificate class, and independent verifier outcome agree; such variation can represent an objective-equivalent optimum.", "",
        "| Scenario | Objective agrees | Certificate agrees | Verifier agrees | Native route identical | Pass |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario_id']} | {row['objective_agrees']} | {row['certificate_class_agrees']} | "
            f"{row['verifier_outcome_agrees']} | {row['native_route_witness_agrees']} | {row['passed']} |"
        )
    (r56.EVIDENCE / "repeatability_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run() -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    comparisons: list[dict[str, Any]] = []
    for ordinal, descriptor in enumerate(descriptors(), start=1):
        scenario_id = descriptor["scenario_id"]
        run_dir = RAW / scenario_id
        run_dir.mkdir(parents=True, exist_ok=True)
        command, identity = official.command_for(descriptor, run_dir, REPETITION_ID)
        result_path = run_dir / "result.json"
        marker_path = run_dir / "completion_marker.json"
        result = None
        if result_path.is_file() and marker_path.is_file():
            marker = load_json(marker_path)
            candidate = load_json(result_path)
            if marker.get("complete") and marker.get("run_identity_sha256") == identity and candidate.get("run_identity_sha256") == identity:
                result = candidate
                print(f"[{ordinal}/3] {scenario_id} resumed", flush=True)
        if result is None:
            r56.write_json(run_dir / "command.json", {
                "schema": "round56-repeatability-command-v1", "scenario_id": scenario_id,
                "repetition_id": REPETITION_ID, "run_identity_sha256": identity, "command": command,
            })
            cap = int(descriptor["solver_process_cap_seconds"])
            print(f"[{ordinal}/3] START {scenario_id} cap={cap}s", flush=True)
            started = time.monotonic()
            with (run_dir / "stdout.log").open("wb") as stdout, (run_dir / "stderr.log").open("wb") as stderr:
                completed = subprocess.run(command, cwd=r56.ROOT, env=env, stdout=stdout, stderr=stderr, timeout=cap + 180, check=False)
            if completed.returncode != 0 or not result_path.is_file():
                raise RuntimeError(f"repeatability execution failed: {scenario_id}")
            result = load_json(result_path)
            r56.write_json(marker_path, {
                "schema": "round56-repeatability-completion-v1", "complete": True, "scenario_id": scenario_id,
                "run_identity_sha256": identity, "result_sha256": r56.sha256_file(result_path),
                "runner_wall_seconds": time.monotonic() - started,
            })
        row = compare(descriptor, result, command)
        comparisons.append(row)
        if not row["passed"]:
            raise RuntimeError(f"repeatability comparison failed: {scenario_id}")
        print(f"[{ordinal}/3] DONE {scenario_id}", flush=True)
    write_audit(comparisons)
    print(json.dumps({"repeatability_rows": len(comparisons), "all_passed": all(row["passed"] for row in comparisons)}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if not args.run:
        raise RuntimeError("pass --run")
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
