#!/usr/bin/env python3
"""Create clean Round 32 Release builds and run all regression suites."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_long_run_validation_round32"
BUILD_ROOT = ROOT / "build_round32" / "official"
CPLEX_BUILD = BUILD_ROOT / "cplex"
GUROBI_BUILD = BUILD_ROOT / "gurobi"
CMAKE = Path(
    r"D:\Program Files\Microsoft Visual Studio\2022\Professional"
    r"\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe")
CTEST = CMAKE.with_name("ctest.exe")
COMPILER = Path(r"D:\msys64\ucrt64\bin\g++.exe")
MAKE = Path(r"D:\msys64\ucrt64\bin\mingw32-make.exe")
PYTHON = Path(r"D:\msys64\ucrt64\bin\python.exe")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def execute(name: str, command: list[str],
            records: list[dict[str, Any]]) -> None:
    stdout_path = OUT / f"{name}.stdout.log"
    stderr_path = OUT / f"{name}.stderr.log"
    started = time.monotonic()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(
            command, cwd=ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            stdout=stdout, stderr=stderr, check=False)
        stdout.flush()
        os.fsync(stdout.fileno())
        stderr.flush()
        os.fsync(stderr.fileno())
    record = {
        "name": name,
        "return_code": completed.returncode,
        "wall_seconds": time.monotonic() - started,
        "command": subprocess.list2cmdline(command),
        "stdout_path": stdout_path.relative_to(ROOT).as_posix(),
        "stderr_path": stderr_path.relative_to(ROOT).as_posix(),
        "passed": completed.returncode == 0,
    }
    records.append(record)
    write_json(OUT / "stage0_build_and_tests.partial.json", records)
    write_csv(OUT / "stage0_build_and_tests.csv", records)
    print(
        f"{name}: rc={completed.returncode} "
        f"wall={record['wall_seconds']:.3f}", flush=True)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed: {name}")


def configure(build: Path, gurobi: bool) -> list[str]:
    command = [
        str(CMAKE), "-S", str(ROOT), "-B", str(build),
        "-G", "MinGW Makefiles",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_CXX_COMPILER={COMPILER.as_posix()}",
        f"-DCMAKE_MAKE_PROGRAM={MAKE.as_posix()}",
        f"-DEXACT_EBRP_ENABLE_GUROBI={'ON' if gurobi else 'OFF'}",
    ]
    if gurobi:
        command.append("-DGUROBI_ROOT=D:/gurobi1302/win64")
    return command


def main() -> int:
    if CPLEX_BUILD.exists() or GUROBI_BUILD.exists():
        raise SystemExit(
            "clean Round 32 build destinations already exist; audit them")
    OUT.mkdir(parents=True, exist_ok=True)
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    try:
        execute("stage0_configure_cplex", configure(CPLEX_BUILD, False),
                records)
        execute(
            "stage0_build_cplex",
            [str(CMAKE), "--build", str(CPLEX_BUILD), "-j", "2"],
            records)
        execute(
            "stage0_ctest_cplex",
            [str(CTEST), "--test-dir", str(CPLEX_BUILD),
             "--output-on-failure"], records)
        execute("stage0_configure_gurobi", configure(GUROBI_BUILD, True),
                records)
        execute(
            "stage0_build_gurobi",
            [str(CMAKE), "--build", str(GUROBI_BUILD), "-j", "2"],
            records)
        execute(
            "stage0_ctest_gurobi",
            [str(CTEST), "--test-dir", str(GUROBI_BUILD),
             "--output-on-failure"], records)
        python_tests = sorted((ROOT / "tests").glob("*.py"))
        for test in python_tests:
            execute(
                f"stage0_python_{test.stem}",
                [str(PYTHON), str(test)], records)
    except Exception as error:
        write_json(OUT / "stage0_build_and_tests.json", {
            "schema": "round32-build-tests-v1",
            "source_commit": head,
            "records": records,
            "passed": False,
            "failure": str(error),
        })
        raise
    cplex_exe = CPLEX_BUILD / "ExactEBRP.exe"
    gurobi_exe = GUROBI_BUILD / "ExactEBRP.exe"
    ctest_records = [
        record for record in records if record["name"].startswith(
            "stage0_ctest_")]
    python_records = [
        record for record in records if record["name"].startswith(
            "stage0_python_")]
    summary = {
        "schema": "round32-build-tests-v1",
        "source_commit": head,
        "compiler": subprocess.check_output(
            (str(COMPILER), "--version"), text=True).splitlines()[0],
        "cmake": subprocess.check_output(
            (str(CMAKE), "--version"), text=True).splitlines()[0],
        "cplex_version": "22.1.1",
        "gurobi_version": "13.0.2",
        "cplex_executable": cplex_exe.relative_to(ROOT).as_posix(),
        "cplex_executable_sha256": sha256(cplex_exe),
        "gurobi_executable": gurobi_exe.relative_to(ROOT).as_posix(),
        "gurobi_executable_sha256": sha256(gurobi_exe),
        "clean_release_build_count": 2,
        "ctest_invocation_count": len(ctest_records),
        "python_test_script_count": len(python_records),
        "command_count": len(records),
        "records": records,
        "passed": all(record["passed"] for record in records),
    }
    write_json(OUT / "stage0_build_and_tests.json", summary)
    (OUT / "stage0_build_and_tests.partial.json").unlink(missing_ok=True)
    print(json.dumps({
        "passed": summary["passed"],
        "cplex_executable_sha256": summary["cplex_executable_sha256"],
        "gurobi_executable_sha256": summary["gurobi_executable_sha256"],
        "commands": len(records),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
