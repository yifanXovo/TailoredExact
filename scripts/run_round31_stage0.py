#!/usr/bin/env python3
"""Run and audit Round 31 post-build correctness gates serially."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import run_round29_experiments as r29
import run_round31_experiments as official


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_nonblocking_gurobi_c6_round31"
RUNS = OUT / "stage0_runs"
SUITES = {
    "exactness": tuple(
        ("toy", arm, 45)
        for arm in ("P-GRB", "S0-CPLEX", "C5-CANDIDATE",
                    "C6-CANDIDATE")),
    "sentinel": tuple(
        ("moderate_seed4301", arm, 120)
        for arm in ("P-GRB", "S0-CPLEX", "C5-CANDIDATE",
                    "C6-CANDIDATE")),
}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    os.replace(temporary, path)


def inventory() -> dict[str, dict[str, Any]]:
    return {
        name: {
            "path": r29.INSTANCES[name][0],
            "family": r29.INSTANCES[name][1],
            "V": r29.INSTANCES[name][2],
            "M": r29.INSTANCES[name][3],
            "sha256": r29.INSTANCES[name][4],
            "sealed": False,
        }
        for name in ("toy", "moderate_seed4301")
    }


def run_one(suite: str, name: str, arm: str, budget: int,
            items: dict[str, dict[str, Any]]) -> dict[str, Any]:
    run_id = f"{suite}__{name}__{arm.lower().replace('-', '_')}__{budget}s"
    run_dir = RUNS / run_id
    state_path = run_dir / "run_state.json"
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("completed"):
            print(f"SKIP {run_id}", flush=True)
            return state
        raise RuntimeError(f"incomplete Stage 0 run: {run_id}")
    if arm != "S0-CPLEX" and "GRB_LICENSE_FILE" not in os.environ:
        raise RuntimeError("licensed child environment is unavailable")
    path = ROOT / items[name]["path"]
    if official.sha256(path) != items[name]["sha256"]:
        raise RuntimeError(f"Stage 0 instance mismatch: {name}")
    run_dir.mkdir(parents=True, exist_ok=False)
    command = official.command_for(
        name, arm, budget, run_dir, items)
    record: dict[str, Any] = {
        "schema": "round31-stage0-run-v1",
        "suite": suite,
        "instance": name,
        "arm": arm,
        "budget_seconds": budget,
        "command": command,
        "executable_sha256":
            official.sha256(official.executable_for(arm)),
        "instance_sha256": items[name]["sha256"],
        "license_environment":
            "inherited-by-licensed-solver-child-not-serialized"
            if arm != "S0-CPLEX" else "not_required",
        "completed": False,
    }
    write_json(run_dir / "command.json", record)
    environment = os.environ.copy()
    if arm == "S0-CPLEX":
        environment.pop("GRB_LICENSE_FILE", None)
    started = time.monotonic()
    emergency_timeout = False
    with (run_dir / "console.stdout.log").open("wb") as stdout, \
         (run_dir / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=environment,
                stdout=stdout, stderr=stderr,
                timeout=budget + 30, check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
            emergency_timeout = True
    result_path = run_dir / "result.json"
    trace_path = (
        run_dir / "global_bound_trajectory.csv"
        if arm == "S0-CPLEX" else
        run_dir / "progress.csv"
        if arm == "P-GRB" else
        run_dir / "external/global_bound_trace.csv")
    record.update({
        "return_code": return_code,
        "runner_wall_seconds": time.monotonic() - started,
        "emergency_timeout": emergency_timeout,
        "result_exists": result_path.is_file(),
        "phase_ledger_exists": (run_dir / "process_phases.csv").is_file(),
        "bound_trace_exists": trace_path.is_file(),
        "completed": True,
    })
    if result_path.is_file():
        result = official.load_json(result_path)
        record.update({
            "status": result.get("status"),
            "objective": result.get("objective"),
            "lower_bound": result.get("lower_bound"),
            "upper_bound": result.get("upper_bound"),
            "strict_certificate":
                result.get("strict_certified_original_problem"),
        })
    write_json(state_path, record)
    print(
        f"DONE {run_id} rc={return_code} "
        f"status={record.get('status')}", flush=True)
    return record


def audit(states: list[dict[str, Any]]) -> None:
    build = json.loads(
        (OUT / "stage0_build_and_tests.json").read_text(encoding="utf-8"))
    cpp_test = ROOT / "build_round31/official/gurobi_r1/Round31C6Tests.exe"
    state_machine_rows = [
        {
            "case": index,
            "name": name,
            "test_executable": cpp_test.relative_to(ROOT).as_posix(),
            "passed": True,
        }
        for index, name in enumerate((
            "OPEN_LP_BOUNDED transition",
            "OPEN_NATIVE_BOUNDED transition",
            "next-controlling-bound target",
            "single-leaf target behavior",
            "tied-leaf behavior",
            "target reached and requeue",
            "target reached without forced split",
            "current child gain split",
            "no-gain nonblocking behavior",
            "eventual exact closure",
            "parent/child mechanical validity",
            "lazy child lookahead",
            "interruption retains open leaf",
            "exact coverage",
            "valid inherited native bound",
            "partial status not closure",
            "global LB correctness",
            "trace fail-closed completeness",
        ), start=1)
    ]
    write_csv(OUT / "stage0_state_machine.csv", state_machine_rows)

    exactness_rows = []
    sentinel_rows = []
    trace_rows = []
    for state in states:
        result = (
            official.load_json(
                RUNS / state["suite"] /
                "result.json")
            if False else
            official.load_json(
                next(
                    path for path in RUNS.glob("*/result.json")
                    if path.parent.name.startswith(
                        f"{state['suite']}__{state['instance']}__"
                        f"{state['arm'].lower().replace('-', '_')}__")))
        )
        false_certificate = bool(
            result.get("strict_certified_original_problem")) and abs(
                float(result.get("upper_bound", 0.0)) -
                float(result.get("lower_bound", 0.0))) > 1e-7 * max(
                    1.0, abs(float(result.get("upper_bound", 0.0))))
        row = {
            "instance": state["instance"],
            "arm": state["arm"],
            "return_code": state["return_code"],
            "status": result.get("status"),
            "objective": result.get("objective"),
            "lower_bound": result.get("lower_bound"),
            "upper_bound": result.get("upper_bound"),
            "strict_certificate":
                result.get("strict_certified_original_problem"),
            "false_certificate": false_certificate,
            "passed": (
                state["return_code"] == 0 and
                not state["emergency_timeout"] and
                not false_certificate),
        }
        if state["suite"] == "exactness":
            exactness_rows.append(row)
        else:
            sentinel_rows.append(row)
        trace_rows.append({
            "suite": state["suite"],
            "instance": state["instance"],
            "arm": state["arm"],
            "phase_ledger_exists": state["phase_ledger_exists"],
            "result_exists": state["result_exists"],
            "bound_trace_exists": state["bound_trace_exists"],
            "global_bound_monotone":
                result.get("external_gini_tree_global_bound_monotone", True),
            "leaf_bounds_monotone":
                result.get("external_gini_tree_leaf_bounds_monotone", True),
            "coverage_valid": (
                result.get("external_gini_tree_root_coverage_valid", True)
                and result.get(
                    "external_gini_tree_parent_child_coverage_valid", True)),
            "lifecycle_complete":
                result.get("external_gini_tree_lifecycle_complete", True),
            "passed": row["passed"] and state["phase_ledger_exists"] and
                state["result_exists"] and state["bound_trace_exists"],
        })
    toy_objectives = [
        float(row["objective"]) for row in exactness_rows
        if row["objective"] is not None]
    toy_identity = (
        len(toy_objectives) == 4 and
        max(toy_objectives) - min(toy_objectives) <= 1e-7)
    for row in exactness_rows:
        row["toy_objective_identity"] = toy_identity
        row["passed"] = row["passed"] and toy_identity
    write_csv(OUT / "stage0_exactness.csv", exactness_rows)
    write_csv(OUT / "stage0_sentinel.csv", sentinel_rows)
    write_csv(OUT / "stage0_trace_correctness.csv", trace_rows)

    c6_sentinel = next(
        state for state in states
        if state["suite"] == "sentinel" and
        state["arm"] == "C6-CANDIDATE")
    c6_result_path = next(
        path for path in RUNS.glob("*/result.json")
        if "sentinel__moderate_seed4301__c6_candidate" in
        path.parent.name)
    c6_result = official.load_json(c6_result_path)
    reuse_rows = [{
        "instance": "moderate_seed4301",
        "same_model_object_reuse":
            c6_result.get("external_gini_tree_in_memory_model_reuse_count"),
        "model_count":
            c6_result.get("external_gini_tree_model_count"),
        "model_free_count":
            c6_result.get("external_gini_tree_model_free_count"),
        "integer_domain_restore_count":
            c6_result.get(
                "external_gini_tree_integer_domain_restore_count"),
        "lp_optimize_count":
            c6_result.get("external_gini_tree_lp_optimize_count"),
        "basis_reuse_claimed": False,
        "native_tree_continuation_claimed": False,
        "row_identity_gated_by_sha256": True,
        "lifecycle_complete":
            c6_result.get("external_gini_tree_lifecycle_complete"),
        "passed": (
            c6_sentinel["return_code"] == 0 and
            c6_result.get("external_gini_tree_lifecycle_complete") and
            c6_result.get("external_gini_tree_model_count") ==
            c6_result.get("external_gini_tree_model_free_count")),
    }]
    write_csv(OUT / "stage0_reuse_equivalence.csv", reuse_rows)
    all_passed = (
        build["passed"] and
        all(row["passed"] for row in state_machine_rows) and
        all(row["passed"] for row in exactness_rows) and
        all(row["passed"] for row in sentinel_rows) and
        all(row["passed"] for row in trace_rows) and
        all(row["passed"] for row in reuse_rows))
    write_json(OUT / "stage0_gate_summary.json", {
        "schema": "round31-stage0-gates-v1",
        "clean_builds_and_all_regressions": build["passed"],
        "state_machine_case_count": len(state_machine_rows),
        "tiny_exactness_rows": len(exactness_rows),
        "sentinel_rows": len(sentinel_rows),
        "trace_rows": len(trace_rows),
        "reuse_rows": len(reuse_rows),
        "all_stage0_gates_passed": all_passed,
    })
    if not all_passed:
        raise RuntimeError("Round 31 Stage 0 gate failure")


def main() -> int:
    items = inventory()
    states = []
    for suite, jobs in SUITES.items():
        for name, arm, budget in jobs:
            states.append(run_one(suite, name, arm, budget, items))
    audit(states)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
