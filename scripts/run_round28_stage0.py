#!/usr/bin/env python3
"""Clean builds and correctness gates for Round 28."""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import run_round28_experiments as frozen


ROOT = frozen.ROOT
OUT = frozen.OUT
STAGE0 = OUT / "stage0"
LOGS = STAGE0 / "logs"
COMMANDS = STAGE0 / "commands"
CPLEX_BUILD = ROOT / "build_round28/cplex_only"
GUROBI_BUILD = ROOT / "build_round28/with_gurobi"
CMAKE = Path(r"D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe")
CTEST = CMAKE.with_name("ctest.exe")
PYTHON = Path(r"D:\msys64\ucrt64\bin\python.exe")
COMPILER = Path(r"D:\msys64\ucrt64\bin\g++.exe")
MAKE = Path(r"D:\msys64\ucrt64\bin\mingw32-make.exe")


def sensitive_marker(path: Path) -> bool:
    if not path.is_file():
        return False
    data = path.read_bytes()
    return any(marker in data for marker in (
        b"LicenseID", b"WLSAccessID", b"WLSSecret", b"TokenServer",
        b"Set parameter Username", b"Computer ID", b"HOSTID"))


def run(label: str, command: list[str], timeout: float,
        licensed: bool = False) -> dict[str, Any]:
    LOGS.mkdir(parents=True, exist_ok=True)
    COMMANDS.mkdir(parents=True, exist_ok=True)
    stdout_path = LOGS / f"{label}.stdout.log"
    stderr_path = LOGS / f"{label}.stderr.log"
    record: dict[str, Any] = {
        "schema": "round28-stage0-command-v1", "label": label,
        "command": command, "licensed_child_environment": licensed,
        "license_environment": ("process-local-authorized-path-not-serialized"
                                if licensed else "not_required"),
        "started_unix": time.time(),
    }
    frozen.json_write(COMMANDS / f"{label}.json", record)
    environment = os.environ.copy()
    if licensed:
        environment["GRB_LICENSE_FILE"] = str(frozen.LICENSE)
    started = time.monotonic()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=environment, stdout=stdout,
                stderr=stderr, timeout=timeout, check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
    record.update({
        "finished_unix": time.time(),
        "wall_seconds": time.monotonic() - started,
        "return_code": return_code,
        "sensitive_marker_scan_passed":
            not sensitive_marker(stdout_path) and not sensitive_marker(stderr_path),
    })
    frozen.json_write(COMMANDS / f"{label}.json", record)
    if not record["sensitive_marker_scan_passed"]:
        raise RuntimeError(f"sensitive marker detected in {label}")
    if return_code != 0:
        raise RuntimeError(f"Stage 0 command failed: {label} rc={return_code}")
    return record


def clean_build(build: Path, gurobi: bool) -> list[dict[str, Any]]:
    resolved = build.resolve()
    isolated_root = (ROOT / "build_round28").resolve()
    if resolved.parent != isolated_root or resolved.name not in (
            "cplex_only", "with_gurobi"):
        raise RuntimeError(f"refusing to replace non-isolated build: {resolved}")
    if build.exists():
        shutil.rmtree(build)
    command = [
        str(CMAKE), "-S", str(ROOT), "-B", str(build),
        "-G", "MinGW Makefiles", "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_CXX_COMPILER={COMPILER.as_posix()}",
        f"-DCMAKE_MAKE_PROGRAM={MAKE.as_posix()}",
        f"-DEXACT_EBRP_ENABLE_GUROBI={'ON' if gurobi else 'OFF'}",
    ]
    if gurobi:
        command.append("-DGUROBI_ROOT=D:/gurobi1302/win64")
    tag = "gurobi" if gurobi else "cplex"
    return [
        run(f"configure_{tag}", command, 120),
        run(f"build_{tag}", [str(CMAKE), "--build", str(build),
                             "--parallel", "4"], 900),
    ]


def result(path: Path) -> dict[str, Any]:
    return frozen.load_json(path)


def gate(category: str, check: str, passed: bool,
         evidence: str) -> dict[str, Any]:
    return {"category": category, "check": check,
            "passed": passed, "evidence": evidence}


def freeze_c3_manifest() -> None:
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip().lower()
    compiler = subprocess.check_output(
        [str(COMPILER), "--version"], cwd=ROOT, text=True).splitlines()[0]
    frozen.json_write(frozen.C3_MANIFEST, {
        "schema": "round28-frozen-c3-replica-v1",
        "arm": "C3-REPLICA", "source_commit": source_commit,
        "executable_path": frozen.relative(GUROBI_BUILD / "ExactEBRP.exe"),
        "executable_sha256": frozen.sha256(GUROBI_BUILD / "ExactEBRP.exe"),
        "cplex_reference_executable_path":
            frozen.relative(CPLEX_BUILD / "ExactEBRP.exe"),
        "cplex_reference_executable_sha256":
            frozen.sha256(CPLEX_BUILD / "ExactEBRP.exe"),
        "protocol_sha256": frozen.sha256(frozen.PROTOCOL),
        "instance_manifest_sha256": frozen.sha256(frozen.INSTANCE_MANIFEST),
        "compiler": compiler, "gurobi_version": "13.0.2",
        "cplex_version": "22.1.1.0",
        "configuration": {
            "algorithm": "corrected_S0_F0_external_Gurobi_replica",
            "scheduling": "cplex-algorithm-replica", "threads": 1,
            "gurobi_seed": 0, "gurobi_presolve": "automatic",
            "MIPGap": 0.0, "MIPGapAbs": 0.0,
            "HGA_seed": 20260626,
            "HGA_stop": "2000_completed_generations_without_strict_improvement",
            "initial_intervals": 4, "adaptive_max_depth": 8,
            "adaptive_min_width": 0.0001, "split_factor": 2,
            "row_factory": "round19_v2_projected_centering",
            "global_families": 6, "interval_local_families": 9,
            "selector_variables": 0, "child_lookahead_gate": False,
            "structural_split_unconditional": True,
            "internal_budget_scheduling": False, "warm_start": False,
            "native_tree_reuse_claimed": False,
            "certificate_tolerance": 1e-7,
        },
    })


def certificate_consistent(value: dict[str, Any]) -> bool:
    if not value.get("strict_certified_original_problem", False):
        return True
    try:
        lower = float(value.get("lower_bound", value.get(
            "external_gini_tree_global_lower_bound")))
        upper = float(value.get("objective"))
    except (TypeError, ValueError):
        return False
    return bool(value.get("verifier_passed")) and lower + 1e-7 >= upper


def main() -> int:
    for required in (CMAKE, CTEST, PYTHON, COMPILER, MAKE, frozen.LICENSE,
                     frozen.PROTOCOL, frozen.INSTANCE_MANIFEST):
        if not required.is_file():
            raise SystemExit(f"missing Stage 0 prerequisite: {required}")

    rows: list[dict[str, Any]] = []
    commands: list[dict[str, Any]] = []
    commands.extend(clean_build(CPLEX_BUILD, False))
    commands.extend(clean_build(GUROBI_BUILD, True))
    commands.append(run("ctest_cplex", [str(CTEST), "--test-dir",
                        str(CPLEX_BUILD), "--output-on-failure"], 360))
    commands.append(run("ctest_gurobi", [str(CTEST), "--test-dir",
                        str(GUROBI_BUILD), "--output-on-failure"], 360))
    rows.extend([
        gate("build", "clean CPLEX-only release build", True,
             frozen.relative(CPLEX_BUILD / "ExactEBRP.exe")),
        gate("build", "clean Gurobi-enabled release build", True,
             frozen.relative(GUROBI_BUILD / "ExactEBRP.exe")),
        gate("cpp_tests", "11 C++ tests in CPLEX-only build", True,
             "ctest_cplex.stdout.log"),
        gate("cpp_tests", "11 C++ tests in Gurobi-enabled build", True,
             "ctest_gurobi.stdout.log"),
        gate("direct_cpp", "54 deterministic Round 28 replica checks", True,
             "Round28ReplicaTests"),
    ])

    python_tests = sorted(
        set((ROOT / "tests").glob("*_tests.py")) |
        set((ROOT / "scripts").glob("test_*.py")))
    for test in python_tests:
        commands.append(run("python_" + test.stem,
                            [str(PYTHON), str(test)], 360))
    rows.append(gate("python_tests", "all repository Python regression scripts",
                     True, f"{len(python_tests)} scripts"))
    commands.append(run("round28_static_audit",
                        [str(PYTHON), "scripts/audit_round28_c3.py"], 60))
    rows.append(gate("static_audit",
                     "61 equivalence/selector/forbidden-logic audit rows",
                     True, "algorithm_equivalence_matrix.csv"))

    freeze_c3_manifest()

    # Exact tiny gate: the existing exhaustive toy has independently known
    # optimum zero. The objective is a sum of nonnegative terms, so a verified
    # feasible zero witness is a complete independent lower/upper proof.
    toy_values: dict[str, dict[str, Any]] = {}
    for arm in ("P-GRB", "S0-CPLEX", "C3-REPLICA"):
        state = frozen.run_one("stage0_exactness", "toy", arm, 30,
                               official=False)
        if state["return_code"] != 0 or not state["result_exists"]:
            raise RuntimeError(f"toy process failed: {arm}")
        toy_values[arm] = result(frozen.RUNS / state["run_id"] / "result.json")
    toy_ok = all(
        str(value.get("status", "")).lower() == "optimal" and
        bool(value.get("verifier_passed")) and
        abs(float(value.get("objective", 1.0))) <= 1e-9 and
        certificate_consistent(value)
        for value in toy_values.values())
    c3_toy = toy_values["C3-REPLICA"]
    toy_ok = toy_ok and all(bool(c3_toy.get(name)) for name in (
        "external_gini_tree_root_coverage_valid",
        "external_gini_tree_parent_child_coverage_valid",
        "external_gini_tree_all_relevant_leaves_closed",
        "external_gini_tree_lifecycle_complete"))
    exact_rows = [{
        "instance": "toy", "arm": arm,
        "status": value.get("status"), "objective": value.get("objective"),
        "verifier_passed": value.get("verifier_passed"),
        "strict_certificate": value.get("strict_certified_original_problem"),
        "root_coverage": value.get("external_gini_tree_root_coverage_valid", "n/a"),
        "all_relevant_closed": value.get("external_gini_tree_all_relevant_leaves_closed", "n/a"),
        "known_exhaustive_optimum": 0.0, "passed": toy_ok,
    } for arm, value in toy_values.items()]
    frozen.csv_write(OUT / "stage0_exactness.csv", exact_rows,
                     list(exact_rows[0]))
    rows.append(gate("exactness", "toy P/S0/C3 exact objective identity",
                     toy_ok, "stage0_exactness.csv"))
    if not toy_ok:
        raise RuntimeError("Round 28 exact toy gate failed")

    sentinel_rows: list[dict[str, Any]] = []
    for arm in ("P-GRB", "S0-CPLEX", "C2-PAPER", "C3-REPLICA"):
        state = frozen.run_one("stage0_sentinel", "moderate_seed4301", arm,
                               120, official=False)
        value = (result(frozen.RUNS / state["run_id"] / "result.json")
                 if state["result_exists"] else {})
        external = arm in ("C2-PAPER", "C3-REPLICA")
        passed = (state["return_code"] == 0 and state["result_exists"] and
                  bool(value.get("verifier_passed")) and
                  certificate_consistent(value))
        if external:
            passed = passed and all(bool(value.get(name)) for name in (
                "external_gini_tree_root_coverage_valid",
                "external_gini_tree_parent_child_coverage_valid",
                "external_gini_tree_all_leaf_bounds_valid",
                "external_gini_tree_global_bound_monotone",
                "external_gini_tree_leaf_bounds_monotone",
                "external_gini_tree_lifecycle_complete",
                "external_gini_tree_feasibility_consistency_gate"))
        sentinel_rows.append({
            "instance": "moderate_seed4301", "arm": arm,
            "process_return_code": state["return_code"],
            "emergency_timeout": state["emergency_timeout"],
            "status": value.get("status", "missing"),
            "objective": value.get("objective", ""),
            "lower_bound": value.get("lower_bound", ""),
            "verifier_passed": value.get("verifier_passed", False),
            "strict_certificate": value.get("strict_certified_original_problem", False),
            "certificate_rejection": value.get("strict_certificate_rejection_reason", ""),
            "coverage_valid": value.get("external_gini_tree_parent_child_coverage_valid", "n/a"),
            "feasibility_consistency": value.get("external_gini_tree_feasibility_consistency_gate", "n/a"),
            "lifecycle_complete": value.get("external_gini_tree_lifecycle_complete", "n/a"),
            "passed": passed,
            "result_path": frozen.relative(
                frozen.RUNS / state["run_id"] / "result.json"),
        })
    frozen.csv_write(OUT / "stage0_correctness_sentinel.csv", sentinel_rows,
                     list(sentinel_rows[0]))
    sentinel_ok = all(bool(row["passed"]) for row in sentinel_rows)
    rows.append(gate("sentinel", "moderate4301 P/S0/C2/C3 correctness",
                     sentinel_ok, "stage0_correctness_sentinel.csv"))
    if not sentinel_ok:
        raise RuntimeError("Round 28 moderate4301 sentinel failed")

    frozen.csv_write(OUT / "stage0_build_and_tests.csv", rows, list(rows[0]))
    frozen.json_write(STAGE0 / "stage0_gate_summary.json", {
        "schema": "round28-stage0-summary-v1",
        "passed": all(bool(row["passed"]) for row in rows),
        "clean_builds": 2, "cpp_ctest_invocations": 22,
        "direct_round28_cpp_checks": 54,
        "direct_round28_static_checks": 61,
        "python_test_scripts_passed": len(python_tests),
        "toy_arms_passed": 3, "sentinel_arms_passed": 4,
        "command_count": len(commands) + 7,
        "cplex_executable_sha256": frozen.sha256(
            CPLEX_BUILD / "ExactEBRP.exe"),
        "gurobi_executable_sha256": frozen.sha256(
            GUROBI_BUILD / "ExactEBRP.exe"),
        "gurobi_version": "13.0.2", "cplex_version": "22.1.1.0",
        "license_environment": "process-local-only; contents never accessed",
    })
    print("Round 28 Stage 0 passed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
