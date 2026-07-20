#!/usr/bin/env python3
"""Licensed native-import and tiny-exact Stage 0 checks for Round 25."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

import run_round25_experiments as frozen


ROOT = frozen.ROOT
OUT = frozen.OUT
RAW = OUT / "stage0" / "raw"
MODELS = OUT / "stage0" / "models"
LOGS = OUT / "stage0" / "native_logs"
COMMANDS = OUT / "stage0" / "commands"
SCRATCH = ROOT / "build_round25" / "license_check_scratch"
EXE = frozen.DEFAULT_EXE
GUROBI_CL = Path(r"D:\gurobi1302\win64\bin\gurobi_cl.exe")


def add(args: list[str], name: str, value: object) -> None:
    frozen.add(args, name, value)


def probe_command(label: str, instance: str, seconds: float) -> list[str]:
    result = RAW / f"{label}.json"
    model = MODELS / f"{label}.lp"
    log = LOGS / f"{label}.log"
    args = [str(EXE), "--input", str(frozen.INSTANCES[instance][0])]
    for name, value in (
        ("--method", "gurobi"), ("--lambda", 0.15), ("--T", 3600),
        ("--time-limit", seconds), ("--process-wall-time-limit", seconds + 2),
        ("--threads", 1), ("--mip-threads", 1),
        ("--cplex-threads", 1), ("--compact-bc-threads", 1),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0), ("--gurobi-presolve", -1),
        ("--gurobi-model-export", model),
        ("--gurobi-progress", RAW / f"{label}.progress.csv"),
        ("--log", log), ("--out", result),
    ):
        add(args, name, value)
    args.append("--plain-baseline")
    return args


def sensitive_marker(path: Path) -> bool:
    if not path.exists():
        return False
    data = path.read_bytes()
    return any(marker in data for marker in (
        b"LicenseID", b"WLSAccessID", b"WLSSecret", b"TokenServer",
        b"Set parameter Username", b"Computer ID", b"HOSTID"))


def run(label: str, command: list[str], timeout: float,
        result_path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema": "round25-stage0-command-v1", "label": label,
        "command": command, "executable_sha256": frozen.sha256(EXE),
        "started_unix": time.time(),
        "gurobi_license_environment": "process_local_authorized_path",
    }
    frozen.json_write(COMMANDS / f"{label}.json", record)
    env = os.environ.copy()
    env["GRB_LICENSE_FILE"] = str(frozen.LICENSE)
    stdout_path = LOGS / f"{label}.console.stdout.log"
    stderr_path = LOGS / f"{label}.console.stderr.log"
    began = time.monotonic()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                timeout=timeout, check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
    record.update({
        "return_code": return_code,
        "runner_wall_seconds": time.monotonic() - began,
        "finished_unix": time.time(),
        "result_exists": result_path.is_file(),
    })
    frozen.json_write(COMMANDS / f"{label}.json", record)
    if any(sensitive_marker(path) for path in
           (stdout_path, stderr_path, LOGS / f"{label}.log")):
        raise RuntimeError(f"sensitive marker detected in Stage 0 {label}")
    if return_code != 0 or not result_path.is_file():
        raise RuntimeError(f"Stage 0 {label} failed rc={return_code}")
    return json.loads(result_path.read_text(encoding="utf-8"))


def command_line_license_check(model: Path) -> dict[str, Any]:
    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
    SCRATCH.mkdir(parents=True)
    stdout_path = SCRATCH / "stdout.log"
    stderr_path = SCRATCH / "stderr.log"
    native_log = SCRATCH / "native.log"
    solution = SCRATCH / "solution.sol"
    env = os.environ.copy()
    env["GRB_LICENSE_FILE"] = str(frozen.LICENSE)
    command = [str(GUROBI_CL), f"LogFile={native_log}",
               f"ResultFile={solution}", str(model)]
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(
            command, cwd=SCRATCH, env=env, stdout=stdout, stderr=stderr,
            timeout=45, check=False)
    marker = any(sensitive_marker(path) for path in
                 (stdout_path, stderr_path, native_log))
    native_text = native_log.read_text(encoding="utf-8", errors="replace") \
        if native_log.exists() and not marker else ""
    optimal = "Optimal solution found" in native_text
    audit = {
        "program": "gurobi_cl", "exit_code": completed.returncode,
        "minimal_solve_status": "OPTIMAL" if optimal else "not_optimal",
        "license_usable": completed.returncode == 0 and optimal,
        "sensitive_marker_detected_in_ephemeral_output": marker,
        "ephemeral_output_retained": False,
        "sanitized_failure_class": "none" if completed.returncode == 0 and optimal
        else "command_line_license_or_solve_failure",
    }
    shutil.rmtree(SCRATCH)
    return audit


def main() -> int:
    for directory in (RAW, MODELS, LOGS, COMMANDS):
        directory.mkdir(parents=True, exist_ok=True)
    if not EXE.is_file() or not frozen.LICENSE.is_file() or not GUROBI_CL.is_file():
        raise SystemExit("Stage 0 executable, Gurobi CLI, or authorized license path missing")

    fingerprints: dict[str, int] = {}
    probe_instances = (*frozen.STAGE1_INSTANCES, "moderate_seed4301", "toy")
    probe_results: dict[str, dict[str, Any]] = {}
    for instance in probe_instances:
        label = f"native_import_probe_{instance.lower()}"
        result_path = RAW / f"{label}.json"
        result = run(label, probe_command(label, instance, 0.001), 30, result_path)
        fingerprint = int(result.get("gurobi_model_fingerprint", 0))
        if not fingerprint or not result.get("gurobi_native_domain_audit_passed"):
            raise RuntimeError(f"native import audit failed for {instance}")
        fingerprints[instance] = fingerprint
        probe_results[instance] = result
    frozen.json_write(OUT / "gurobi_fingerprints.json", {
        "schema": "round25-gurobi-fingerprints-v1",
        "executable_sha256": frozen.sha256(EXE),
        "fingerprints": fingerprints,
    })

    exact_results: dict[str, dict[str, Any]] = {}
    for instance in ("toy", "V12_M1"):
        for arm in ("P-CPX", "P-GRB"):
            label = f"{instance.lower()}_{arm.lower().replace('-', '_')}"
            run_dir = OUT / "stage0" / "qualification_runs" / label
            run_dir.mkdir(parents=True, exist_ok=True)
            manifest = frozen.validate_frozen(EXE, arm, instance)
            command = frozen.make_command(
                EXE, instance, arm, 30, run_dir, manifest)
            result = run(label, command, 45, run_dir / "result.json")
            exact_results[label] = result

    cli = command_line_license_check(
        OUT / "stage0" / "qualification_runs" / "toy_p_grb" / "canonical.lp")
    in_process = exact_results["toy_p_grb"]
    in_process_ok = (
        in_process.get("gurobi_environment_creation_return_code") == 0 and
        str(in_process.get("gurobi_status_text", "")).upper() == "OPTIMAL")
    frozen.json_write(OUT / "license_visibility_audit.json", {
        "schema": "round25-license-visibility-v1",
        "license_path": str(frozen.LICENSE),
        "exists": frozen.LICENSE.exists(), "regular_file": frozen.LICENSE.is_file(),
        "environment_scope": "process_local_only",
        "permanent_environment_modified": False,
        "contents_opened_parsed_hashed_copied_or_committed": False,
        "gurobi_version": "13.0.2",
        "command_line_check": cli,
        "in_process_cpp_check": {
            "environment_creation_return_code":
                in_process.get("gurobi_environment_creation_return_code", -1),
            "minimal_solve_status": in_process.get("gurobi_status_text", ""),
            "exit_code": 0,
            "license_usable": in_process_ok,
            "sanitized_failure_class": "none" if in_process_ok
                else "in_process_license_or_solve_failure",
        },
        "checks_agree": bool(cli["license_usable"] and in_process_ok),
        "evidence_redaction":
            "No license contents or machine-bound identifiers are retained.",
    })
    if not cli["license_usable"] or not in_process_ok:
        raise RuntimeError("independent license checks failed")
    print("Round25 Stage 0 native solver checks passed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
