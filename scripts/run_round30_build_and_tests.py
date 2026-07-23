#!/usr/bin/env python3
"""Create clean Round 30 release builds and run all C++/Python tests."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_c0_mechanism_transfer_c5_round30"
BUILD_ROOT = ROOT / "build_round30"
CPLEX_BUILD = BUILD_ROOT / "cplex_only"
GUROBI_BUILD = BUILD_ROOT / "with_gurobi"
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
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    temporary.replace(path)


def execute(name: str, command: list[str],
            records: list[dict[str, Any]]) -> None:
    stdout_path = OUT / f"{name}.stdout.log"
    stderr_path = OUT / f"{name}.stderr.log"
    started = time.monotonic()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(
            command, cwd=ROOT, stdout=stdout, stderr=stderr, check=False)
    record = {
        "name": name,
        "command": command,
        "command_text": subprocess.list2cmdline(command),
        "return_code": completed.returncode,
        "wall_seconds": time.monotonic() - started,
        "stdout_path": stdout_path.relative_to(ROOT).as_posix(),
        "stderr_path": stderr_path.relative_to(ROOT).as_posix(),
        "passed": completed.returncode == 0,
    }
    records.append(record)
    write_json(OUT / "build_and_test_record.partial.json", {
        "schema": "round30-build-tests-v1",
        "records": records,
    })
    print(
        f"{name}: rc={completed.returncode} "
        f"wall={record['wall_seconds']:.3f}", flush=True)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed: {name}")


def configure_command(build: Path, gurobi: bool) -> list[str]:
    command = [
        str(CMAKE),
        "-S", str(ROOT),
        "-B", str(build),
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
            "clean-build destinations already exist; retain and audit them")
    OUT.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []
    python_tests = sorted((ROOT / "tests").glob("*.py"))
    try:
        execute(
            "stage0_configure_cplex",
            configure_command(CPLEX_BUILD, False), records)
        execute(
            "stage0_build_cplex",
            [str(CMAKE), "--build", str(CPLEX_BUILD), "-j", "2"], records)
        execute(
            "stage0_ctest_cplex",
            [str(CTEST), "--test-dir", str(CPLEX_BUILD),
             "--output-on-failure"], records)
        execute(
            "stage0_configure_gurobi",
            configure_command(GUROBI_BUILD, True), records)
        execute(
            "stage0_build_gurobi",
            [str(CMAKE), "--build", str(GUROBI_BUILD), "-j", "2"], records)
        execute(
            "stage0_ctest_gurobi",
            [str(CTEST), "--test-dir", str(GUROBI_BUILD),
             "--output-on-failure"], records)
        for test in python_tests:
            execute(
                f"stage0_python_{test.stem}",
                [str(PYTHON), str(test)], records)
    except Exception as error:
        write_json(OUT / "build_and_test_record.json", {
            "schema": "round30-build-tests-v1",
            "source_commit": subprocess.check_output(
                ("git", "rev-parse", "HEAD"), cwd=ROOT,
                text=True).strip(),
            "records": records,
            "passed": False,
            "failure": str(error),
        })
        raise
    cplex_exe = CPLEX_BUILD / "ExactEBRP.exe"
    gurobi_exe = GUROBI_BUILD / "ExactEBRP.exe"
    result = {
        "schema": "round30-build-tests-v1",
        "source_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), cwd=ROOT,
            text=True).strip(),
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
        "cpp_test_count_per_build": 13,
        "python_test_script_count": len(python_tests),
        "records": records,
        "passed": all(record["passed"] for record in records),
    }
    write_json(OUT / "build_and_test_record.json", result)
    (OUT / "build_and_test_record.partial.json").unlink(missing_ok=True)
    print(json.dumps({
        "passed": result["passed"],
        "cplex_executable_sha256":
            result["cplex_executable_sha256"],
        "gurobi_executable_sha256":
            result["gurobi_executable_sha256"],
        "commands": len(records),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
