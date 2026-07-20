#!/usr/bin/env python3
"""Execute the licensed, non-performance Round 24R Stage 0 solver checks."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_solver_backend_migration_round24r"
RAW = OUT / "raw" / "stage0"
MODELS = OUT / "models" / "stage0"
LOGS = OUT / "native_logs" / "stage0"
COMMANDS = OUT / "commands" / "stage0"
LICENSE = Path(r"E:\gurobi\gurobi.lic")
EXE = ROOT / "build_round24r" / "with_gurobi_clean" / "ExactEBRP.exe"
INSTANCES = {
    "toy": ROOT / "tests" / "data" / "round24_toy_V2_M1.txt",
    "V12_M1": ROOT / "reference" / "regen_candidate_V12_M1_average.txt",
    "V12_M2": ROOT / "reference" / "regen_candidate_V12_M2_average.txt",
    "moderate4301": ROOT / "reference" / "heldout_round22" / "V20_M3" / "moderate_seed4301.txt",
    "high_imbalance_seed3202": ROOT / "reference" / "hard_stress" / "V20_M3" / "high_imbalance_seed3202.txt",
    "tight_T_seed3101": ROOT / "reference" / "hard_stress" / "V20_M3" / "tight_T_seed3101.txt",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def append(args: list[str], name: str, item: object) -> None:
    args.extend((name, str(item).lower() if isinstance(item, bool) else str(item)))


def run(label: str, args: list[str], timeout: float, gurobi: bool) -> dict:
    command = [str(EXE), *args]
    record = {"schema": "round24r-stage0-command-v1", "label": label,
              "command": command, "executable_sha256": sha256(EXE),
              "started_unix": time.time(),
              "gurobi_license_environment": "process_local_authorized_path"}
    COMMANDS.mkdir(parents=True, exist_ok=True)
    (COMMANDS / f"{label}.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8")
    env = os.environ.copy()
    env["GRB_LICENSE_FILE"] = str(LICENSE)
    stdout_path = LOGS / f"{label}.console.stdout.log"
    stderr_path = LOGS / f"{label}.console.stderr.log"
    started = time.monotonic()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            completed = subprocess.run(command, cwd=ROOT, env=env,
                                       stdout=stdout, stderr=stderr,
                                       timeout=timeout, check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
    record.update({"return_code": return_code,
                   "runner_wall_seconds": time.monotonic() - started,
                   "finished_unix": time.time()})
    (COMMANDS / f"{label}.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8")
    if gurobi:
        sensitive = (b"LicenseID", b"Username", b"WLS", b"Token")
        for path in (stdout_path, stderr_path, LOGS / f"{label}.log"):
            if path.exists() and any(marker in path.read_bytes() for marker in sensitive):
                path.unlink(missing_ok=True)
                raise RuntimeError(
                    f"sensitive license marker detected and removed: {path.name}")
    if return_code != 0:
        raise RuntimeError(f"{label} returned {return_code}")
    result = RAW / f"{label}.json"
    if not result.exists():
        raise RuntimeError(f"{label} did not write a result")
    return json.loads(result.read_text(encoding="utf-8"))


def common(label: str, instance: str, seconds: float) -> list[str]:
    args: list[str] = []
    for name, item in (
        ("--input", INSTANCES[instance]), ("--lambda", 0.15), ("--T", 3600),
        ("--time-limit", seconds), ("--process-wall-time-limit", seconds + 2),
        ("--threads", 1), ("--mip-threads", 1), ("--cplex-threads", 1),
        ("--compact-bc-threads", 1),
        ("--log", LOGS / f"{label}.log"), ("--out", RAW / f"{label}.json"),
    ):
        append(args, name, item)
    args.append("--plain-baseline")
    return args


def cplex_args(label: str, instance: str, seconds: float) -> list[str]:
    args = common(label, instance, seconds)
    args[0:0] = ["--method", "cplex"]
    source = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip().lower()
    for name, item in (
        ("--cplex-model-export", MODELS / f"{label}.lp"),
        ("--progress-log", RAW / f"{label}.progress.csv"),
        ("--round22-production-mode", True),
        ("--round22-source-commit", source),
        ("--round22-executable-sha256", sha256(EXE)),
        ("--round22-production-manifest-sha256",
         sha256(OUT / "corrected_evaluation_protocol.md")),
        ("--dense-progress", True), ("--dense-progress-run-id", label),
        ("--dense-progress-algorithm-arm", "P-CPX"),
        ("--dense-progress-raw", RAW / f"{label}.dense.csv"),
        ("--dense-progress-checkpoints", RAW / f"{label}.checkpoints.csv"),
    ):
        append(args, name, item)
    return args


def gurobi_args(label: str, instance: str, seconds: float,
                fingerprint: int) -> list[str]:
    args = common(label, instance, seconds)
    args[0:0] = ["--method", "gurobi"]
    executable_sha = sha256(EXE)
    for name, item in (
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0), ("--gurobi-presolve", -1),
        ("--gurobi-model-export", MODELS / f"{label}.lp"),
        ("--gurobi-progress", RAW / f"{label}.progress.csv"),
        ("--round24-executable-sha256", executable_sha),
        ("--round24-manifest-executable-sha256", executable_sha),
        ("--round24-expected-gurobi-model-fingerprint", fingerprint),
    ):
        append(args, name, item)
    return args


def main() -> int:
    for directory in (RAW, MODELS, LOGS, COMMANDS):
        directory.mkdir(parents=True, exist_ok=True)
    if not EXE.is_file() or not LICENSE.is_file():
        raise SystemExit("Stage 0 executable or authorized license path is missing")

    fingerprints: dict[str, int] = {}
    for instance in INSTANCES:
        label = f"native_import_probe_{instance.lower()}"
        result = run(label, gurobi_args(label, instance, 0.001, 0), 30, True)
        fingerprint = int(result.get("gurobi_model_fingerprint", 0))
        if not fingerprint or not result.get("gurobi_native_domain_audit_passed"):
            raise RuntimeError(f"native import audit failed for {instance}")
        fingerprints[instance] = fingerprint
    (OUT / "gurobi_fingerprints.json").write_text(json.dumps({
        "schema": "round24r-gurobi-fingerprints-v1",
        "executable_sha256": sha256(EXE), "fingerprints": fingerprints,
    }, indent=2) + "\n", encoding="utf-8")

    run("toy_p_cpx", cplex_args("toy_p_cpx", "toy", 30), 45, False)
    run("toy_p_grb", gurobi_args("toy_p_grb", "toy", 30,
                                  fingerprints["toy"]), 45, True)
    run("v12_m1_p_cpx", cplex_args("v12_m1_p_cpx", "V12_M1", 30), 45, False)
    run("v12_m1_p_grb", gurobi_args("v12_m1_p_grb", "V12_M1", 30,
                                     fingerprints["V12_M1"]), 45, True)
    print("Round24R Stage 0 native solver checks passed")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Round24R Stage 0 failed: {exc}", file=sys.stderr)
        raise
