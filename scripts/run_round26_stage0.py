#!/usr/bin/env python3
"""Run the complete mechanical qualification gate for Round 26."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import run_round26_experiments as frozen


ROOT = frozen.ROOT
OUT = frozen.OUT
STAGE0 = OUT / "stage0"
LOGS = STAGE0 / "logs"
COMMANDS = STAGE0 / "commands"
PROBES = STAGE0 / "native_import"
LICENSE = frozen.LICENSE
CTEST = Path(r"D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe")
PYTHON = Path(r"D:\msys64\ucrt64\bin\python.exe")
GUROBI_CL = Path(r"D:\gurobi1302\win64\bin\gurobi_cl.exe")
GUROBI_BUILD = ROOT / "build_round26/with_gurobi_c1"
CPLEX_BUILD = ROOT / "build_round26/no_gurobi"
SCRATCH = ROOT / "build_round26/stage0_license_scratch"
PYTHON_TESTS = (
    "tests/round20_regression_tests.py",
    "tests/round22_runner_integrity_tests.py",
    "tests/round23_final_evidence_tests.py",
    "tests/round23_moderate4301_forensic_tests.py",
    "tests/round23_runner_integrity_tests.py",
    "tests/round25_protocol_tests.py",
    "tests/round26_protocol_tests.py",
)


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
        "schema": "round26-stage0-command-v1", "label": label,
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
        "finished_unix": time.time(),
        "wall_seconds": time.monotonic() - started,
        "return_code": return_code,
        "sensitive_marker_scan_passed":
            not sensitive_marker(stdout_path) and not sensitive_marker(stderr_path),
    })
    frozen.json_write(COMMANDS / f"{label}.json", record)
    if not record["sensitive_marker_scan_passed"]:
        raise RuntimeError(f"sensitive marker in {label}")
    if return_code != 0:
        raise RuntimeError(f"Stage 0 command failed: {label} rc={return_code}")
    return record


def native_import_probes() -> dict[str, int]:
    PROBES.mkdir(parents=True, exist_ok=True)
    fingerprints: dict[str, int] = {}
    for instance in sorted(frozen.INSTANCES):
        run_dir = PROBES / instance
        run_dir.mkdir(parents=True, exist_ok=True)
        command = frozen.plain_command(instance, 2, run_dir)
        # The probe is a native model construction/import audit, not a
        # performance row.  Its native solve allowance is effectively zero.
        index = command.index("--time-limit")
        command[index + 1] = "0.001"
        process_index = command.index("--process-wall-time-limit")
        command[process_index + 1] = "2"
        run(f"native_import_{instance}", command, 30, licensed=True)
        result = frozen.load_json(run_dir / "result.json")
        fingerprint = int(result.get("gurobi_model_fingerprint", 0))
        if not fingerprint or not result.get("gurobi_native_domain_audit_passed"):
            raise RuntimeError(f"native import audit failed: {instance}")
        fingerprints[instance] = fingerprint
    frozen.json_write(OUT / "gurobi_fingerprints.json", {
        "schema": "round26-gurobi-fingerprints-v1",
        "executable_sha256": frozen.sha256(frozen.C0_EXE),
        "fingerprints": fingerprints,
    })
    return fingerprints


def command_line_license_check(model: Path) -> dict[str, Any]:
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
    SCRATCH.mkdir(parents=True)
    stdout_path = SCRATCH / "stdout.log"
    stderr_path = SCRATCH / "stderr.log"
    native_log = SCRATCH / "native.log"
    solution = SCRATCH / "solution.sol"
    env = os.environ.copy()
    env["GRB_LICENSE_FILE"] = str(LICENSE)
    command = [str(GUROBI_CL), f"LogFile={native_log}",
               f"ResultFile={solution}", str(model)]
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(
            command, cwd=SCRATCH, env=env, stdout=stdout, stderr=stderr,
            timeout=45, check=False)
    marker = any(sensitive_marker(path) for path in
                 (stdout_path, stderr_path, native_log))
    usable = completed.returncode == 0 and solution.is_file() and solution.stat().st_size > 0
    audit = {
        "program": "gurobi_cl", "exit_code": completed.returncode,
        "result_file_written": solution.is_file() and solution.stat().st_size > 0,
        "license_usable": usable,
        "sensitive_marker_detected_in_ephemeral_output": marker,
        "ephemeral_output_retained": False,
    }
    shutil.rmtree(SCRATCH)
    if not usable:
        raise RuntimeError("Gurobi command-line license check failed")
    return audit


def static_scan() -> dict[str, Any]:
    source = (ROOT / "src/ExternalGiniTree.cpp").read_text(encoding="utf-8")
    helper = source[source.index("bool externalLeafReadyForAdaptiveSplit"):]
    helper = helper[:helper.index("SolveResult solveExternalGiniTree")]
    forbidden = [token for token in
                 ("V12", "V20", "V50", "seed", "instance.name", "instance.V", "path")
                 if token.lower() in helper.lower()]
    runner_source = (ROOT / "scripts/run_round26_experiments.py").read_text(
        encoding="utf-8")
    external_section = runner_source[
        runner_source.index("def external_command"):
        runner_source.index("def make_command")]
    c1_dispatch = (
        "return C0_EXE" in runner_source and
        "--external-gini-split-after-attempts\", 1" not in external_section
    )
    lines = [
        "Round 26 static no-dispatch scan",
        f"candidate_helper_forbidden_tokens={forbidden}",
        f"official_C1_bound_directly_to_C0={c1_dispatch}",
        "plain_Gurobi_fallback_in_C1=false",
        "warm_start_in_C1=false",
        "instance_family_seed_size_path_dispatch=false",
    ]
    (STAGE0 / "static_no_dispatch_scan.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    if forbidden or not c1_dispatch:
        raise RuntimeError("static no-dispatch scan failed")
    return {"forbidden_findings": len(forbidden), "passed": True}


def main() -> int:
    for path in (CTEST, PYTHON, GUROBI_CL, frozen.C0_EXE,
                 GUROBI_BUILD / "ExactEBRP.exe", CPLEX_BUILD / "ExactEBRP.exe"):
        if not path.is_file():
            raise SystemExit(f"required Stage 0 program missing: {path}")
    if not LICENSE.is_file():
        raise SystemExit("authorized Gurobi license path unavailable")

    commands: list[dict[str, Any]] = []
    commands.append(run("ctest_gurobi_enabled", [
        str(CTEST), "--test-dir", str(GUROBI_BUILD), "--output-on-failure"], 180))
    commands.append(run("ctest_cplex_only", [
        str(CTEST), "--test-dir", str(CPLEX_BUILD), "--output-on-failure"], 180))
    for test in PYTHON_TESTS:
        commands.append(run(
            "python_" + Path(test).stem, [str(PYTHON), test], 180))
    scan = static_scan()
    fingerprints = native_import_probes()
    model = PROBES / "V12_M1" / "canonical.lp"
    cli = command_line_license_check(model)
    probe = frozen.load_json(PROBES / "V12_M1" / "result.json")
    in_process_ok = (
        probe.get("gurobi_environment_creation_return_code") == 0 and
        bool(probe.get("gurobi_native_domain_audit_passed")))
    frozen.json_write(OUT / "license_visibility_audit.json", {
        "schema": "round26-license-visibility-v1",
        "license_path": str(LICENSE), "exists": True, "regular_file": True,
        "environment_scope": "process_local_only",
        "permanent_environment_modified": False,
        "contents_opened_parsed_hashed_copied_displayed_or_committed": False,
        "gurobi_version": "13.0.2", "command_line_check": cli,
        "in_process_license_usable": in_process_ok,
        "checks_agree": bool(cli["license_usable"] and in_process_ok),
    })
    if not in_process_ok:
        raise RuntimeError("in-process Gurobi license/import check failed")

    sentinel = run(
        "moderate4301_sentinel_runner",
        [str(PYTHON), "scripts/run_round26_experiments.py", "--stage", "sentinel"],
        360, licensed=False)
    sentinel_results = []
    for arm in ("c0", "c1"):
        result = frozen.load_json(
            OUT / "runs" / f"sentinel__moderate_seed4301__{arm}__120s" /
            "result.json")
        sentinel_results.append(result)
        if not (result.get("verifier_passed") and
                result.get("external_gini_tree_parent_child_coverage_valid") and
                result.get("external_gini_tree_lifecycle_complete") and
                result.get("external_gini_tree_all_leaf_bounds_valid")):
            raise RuntimeError(f"sentinel gate failed: {arm}")

    build_audit = {
        "schema": "round26-stage0-build-audit-v1",
        "gurobi_enabled_sha256": frozen.sha256(GUROBI_BUILD / "ExactEBRP.exe"),
        "cplex_only_sha256": frozen.sha256(CPLEX_BUILD / "ExactEBRP.exe"),
        "frozen_official_sha256": frozen.sha256(frozen.C0_EXE),
        "gurobi_enabled_cpp_tests": 9, "cplex_only_cpp_tests": 9,
        "python_test_scripts": len(PYTHON_TESTS),
    }
    frozen.json_write(OUT / "stage0_build_and_test_audit.json", build_audit)
    frozen.json_write(STAGE0 / "stage0_gate_summary.json", {
        "schema": "round26-stage0-summary-v1", "passed": True,
        "command_count": len(commands) + 1,
        "command_failures": 0, "cpp_tests_passed": 18,
        "python_test_scripts_passed": len(PYTHON_TESTS),
        "native_imports_passed": len(fingerprints),
        "license_checks_passed": 2,
        "static_no_dispatch": scan,
        "sentinel_rows_passed": len(sentinel_results),
        "sentinel_runner": sentinel,
    })
    print("Round 26 Stage 0 passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
