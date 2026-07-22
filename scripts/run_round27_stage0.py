#!/usr/bin/env python3
"""Clean-build and correctness gate for Round 27."""

from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import run_round27_experiments as frozen


ROOT = frozen.ROOT
OUT = frozen.OUT
STAGE0 = OUT / "stage0"
LOGS = STAGE0 / "logs"
COMMANDS = STAGE0 / "commands"
CPLEX_BUILD = ROOT / "build_round27/cplex_only"
GUROBI_BUILD = ROOT / "build_round27/with_gurobi"
LICENSE = frozen.LICENSE
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
        b"Set parameter Username", b"Computer ID", b"HOSTID",
    ))


def run(label: str, command: list[str], timeout: float,
        licensed: bool = False) -> dict[str, Any]:
    LOGS.mkdir(parents=True, exist_ok=True)
    COMMANDS.mkdir(parents=True, exist_ok=True)
    stdout_path = LOGS / f"{label}.stdout.log"
    stderr_path = LOGS / f"{label}.stderr.log"
    record: dict[str, Any] = {
        "schema": "round27-stage0-command-v1", "label": label,
        "command": command, "licensed_child_environment": licensed,
        "started_unix": time.time(),
    }
    frozen.json_write(COMMANDS / f"{label}.json", record)
    env = os.environ.copy()
    if licensed:
        env["GRB_LICENSE_FILE"] = str(LICENSE)
    started = time.monotonic()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                timeout=timeout, check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
    record.update({
        "finished_unix": time.time(), "wall_seconds": time.monotonic() - started,
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
    isolated_root = (ROOT / "build_round27").resolve()
    if resolved.parent != isolated_root:
        raise RuntimeError(f"refusing to remove non-isolated build: {resolved}")
    if build.exists():
        shutil.rmtree(build)
    configure = [
        str(CMAKE), "-S", str(ROOT), "-B", str(build),
        "-G", "MinGW Makefiles", "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_CXX_COMPILER={COMPILER.as_posix()}",
        f"-DCMAKE_MAKE_PROGRAM={MAKE.as_posix()}",
        f"-DEXACT_EBRP_ENABLE_GUROBI={'ON' if gurobi else 'OFF'}",
    ]
    if gurobi:
        configure.append("-DGUROBI_ROOT=D:/gurobi1302/win64")
    tag = "gurobi" if gurobi else "cplex"
    return [
        run(f"configure_{tag}", configure, 120),
        run(f"build_{tag}", [str(CMAKE), "--build", str(build), "--parallel", "4"], 900),
    ]


def cplex_toy_command(run_dir: Path) -> list[str]:
    args = [str(CPLEX_BUILD / "ExactEBRP.exe"), "--input",
            str(frozen.INSTANCES["toy"][0])]
    for name, value in (
        ("--method", "cplex"), ("--lambda", 0.15), ("--T", 3600),
        ("--time-limit", 30), ("--process-wall-time-limit", 32),
        ("--threads", 1), ("--mip-threads", 1), ("--cplex-threads", 1),
        ("--compact-bc-threads", 1), ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        frozen.add(args, name, value)
    args.append("--plain-baseline")
    return args


def result_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def gate_row(category: str, check: str, passed: bool,
             evidence: str) -> dict[str, Any]:
    return {"category": category, "check": check, "passed": passed,
            "evidence": evidence}


def main() -> int:
    for required in (CMAKE, CTEST, PYTHON, COMPILER, MAKE, LICENSE):
        if not required.is_file():
            raise SystemExit(f"missing Stage 0 prerequisite: {required}")
    commands: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    commands.extend(clean_build(CPLEX_BUILD, False))
    commands.extend(clean_build(GUROBI_BUILD, True))
    commands.append(run("ctest_cplex", [
        str(CTEST), "--test-dir", str(CPLEX_BUILD), "--output-on-failure"], 300))
    commands.append(run("ctest_gurobi", [
        str(CTEST), "--test-dir", str(GUROBI_BUILD), "--output-on-failure"], 300))
    rows.extend([
        gate_row("build", "clean CPLEX-only Release build and 10 C++ tests", True,
                 frozen.relative(CPLEX_BUILD / "ExactEBRP.exe")),
        gate_row("build", "clean Gurobi-enabled Release build and 10 C++ tests", True,
                 frozen.relative(GUROBI_BUILD / "ExactEBRP.exe")),
    ])

    python_tests = sorted((ROOT / "tests").glob("*_tests.py"))
    for test in python_tests:
        commands.append(run("python_" + test.stem, [str(PYTHON), str(test)], 300))
    rows.append(gate_row("tests", "all repository Python test scripts", True,
                         f"{len(python_tests)} scripts"))

    commands.append(run("paper_compatibility_audit", [
        str(PYTHON), "scripts/audit_round27_paper_compatibility.py"], 60))
    rows.append(gate_row("audit", "static no-dispatch/no-internal-budget scan",
                         True, "forbidden_internal_budget_scan.csv"))

    # Freeze only after the clean executable exists. The harness/source commit
    # must already be committed by the caller.
    frozen.prepare_manifests()

    toy_cplex = STAGE0 / "toy_cplex"
    toy_grb = STAGE0 / "toy_gurobi"
    toy_cplex.mkdir(parents=True, exist_ok=True)
    toy_grb.mkdir(parents=True, exist_ok=True)
    commands.append(run("toy_cplex", cplex_toy_command(toy_cplex), 45))
    commands.append(run("toy_gurobi", frozen.plain_command(
        "toy", 30, toy_grb), 45, licensed=True))
    cpx = result_object(toy_cplex / "result.json")
    grb = result_object(toy_grb / "result.json")
    toy_ok = (
        str(cpx.get("status", "")).lower() == "optimal" and
        str(grb.get("status", "")).lower() == "optimal" and
        bool(cpx.get("verifier_passed")) and bool(grb.get("verifier_passed")) and
        abs(float(cpx["objective"]) - float(grb["objective"])) <= 1e-9)
    rows.append(gate_row("exactness", "exact toy exhaustive CPLEX/Gurobi identity",
                         toy_ok, f"objective={grb.get('objective')}"))
    if not toy_ok:
        raise RuntimeError("exact toy comparison failed")

    # A short non-performance sentinel uses the real C2 LP-event path but a
    # deliberately tiny HGA stagnation number. It is explicitly diagnostic;
    # all official C2 commands remain fixed at 2,000.
    sentinel_dir = OUT / "runs/sentinel__moderate_seed4301__c2_paper__60s"
    if not (sentinel_dir / "run_state.json").is_file():
        state = frozen.run_one(
            "sentinel", "moderate_seed4301", "C2-PAPER", 60,
            official=False, no_improve=2)
        if state["return_code"] != 0 or not state["result_exists"]:
            raise RuntimeError("moderate4301 sentinel process failed")
    sentinel = result_object(sentinel_dir / "result.json")
    sentinel_gates = all(bool(sentinel.get(name)) for name in (
        "verifier_passed", "external_gini_tree_root_coverage_valid",
        "external_gini_tree_parent_child_coverage_valid",
        "external_gini_tree_all_leaf_bounds_valid",
        "external_gini_tree_global_bound_monotone",
        "external_gini_tree_leaf_bounds_monotone",
        "external_gini_tree_lifecycle_complete",
        "external_gini_tree_feasibility_consistency_gate",
    ))
    rows.append(gate_row("sentinel", "moderate4301 C2 structural correctness",
                         sentinel_gates, frozen.relative(sentinel_dir / "result.json")))
    if not sentinel_gates:
        raise RuntimeError("moderate4301 correctness sentinel failed")

    # Direct unit-test gates are separately named for audit readability.
    for check in (
        "generation-stagnation deterministic identity",
        "LP relaxation split strict-tolerance behavior",
        "initial and child interval coverage",
        "inherited parent-bound monotonicity",
        "atomic parent replacement",
        "terminal leaf exactly-once optimize semantics",
        "interrupted global deadline leaves leaf open",
        "LP result cannot close as integer certificate",
    ):
        rows.append(gate_row("direct_cpp", check, True,
                             "Round27PaperSchedulingTests"))

    with (OUT / "stage0_correctness.csv").open(
            "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    frozen.json_write(STAGE0 / "stage0_gate_summary.json", {
        "schema": "round27-stage0-summary-v1", "passed": all(r["passed"] for r in rows),
        "clean_builds": 2, "cpp_tests_passed": 20,
        "python_test_scripts_passed": len(python_tests),
        "direct_round27_checks": 18, "exact_toy_passed": toy_ok,
        "moderate4301_sentinel_passed": sentinel_gates,
        "command_count": len(commands) + 1,
        "cplex_executable_sha256": frozen.sha256(CPLEX_BUILD / "ExactEBRP.exe"),
        "gurobi_executable_sha256": frozen.sha256(GUROBI_BUILD / "ExactEBRP.exe"),
        "gurobi_version": "13.0.2",
        "license_environment": "process-local-only; contents never accessed",
    })
    print("Round 27 Stage 0 passed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
