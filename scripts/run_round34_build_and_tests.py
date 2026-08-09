#!/usr/bin/env python3
"""Create the isolated Round 34 Release build and run all regressions."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import round34_common as common


CMAKE = Path(
    r"D:\Program Files\Microsoft Visual Studio\2022\Professional"
    r"\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe")
CTEST = CMAKE.with_name("ctest.exe")
COMPILER = Path(r"D:\msys64\ucrt64\bin\g++.exe")
MAKE = Path(r"D:\msys64\ucrt64\bin\mingw32-make.exe")
PYTHON = Path(r"D:\msys64\ucrt64\bin\python.exe")


def write_records(records: list[dict[str, Any]]) -> None:
    common.write_json(common.OUT / "stage0_build_and_tests.partial.json",
                      records)
    common.write_csv(common.OUT / "stage0_build_and_tests.csv", records)


def execute(name: str, command: list[str],
            records: list[dict[str, Any]]) -> None:
    stdout_path = common.OUT / f"{name}.stdout.log"
    stderr_path = common.OUT / f"{name}.stderr.log"
    started = time.monotonic()
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(
            command, cwd=common.ROOT, env=env, stdout=stdout,
            stderr=stderr, check=False)
    record = {
        "round_id": 34,
        "name": name,
        "return_code": completed.returncode,
        "wall_seconds": time.monotonic() - started,
        "command": subprocess.list2cmdline(command),
        "stdout_path": common.relative(stdout_path),
        "stderr_path": common.relative(stderr_path),
        "passed": completed.returncode == 0,
    }
    records.append(record)
    write_records(records)
    print(f"{name}: rc={completed.returncode} wall={record['wall_seconds']:.3f}",
          flush=True)
    if completed.returncode != 0:
        raise RuntimeError(f"Round 34 stage-0 command failed: {name}")


def main() -> int:
    common.OUT.mkdir(parents=True, exist_ok=True)
    common.BUILD.parent.mkdir(parents=True, exist_ok=True)
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=common.ROOT, text=True).strip()
    failure_path = common.OUT / "stage0_build_and_tests.json"
    resumed_test_fix = common.BUILD.exists()
    records: list[dict[str, Any]] = []
    executable_source_commit = head
    if resumed_test_fix:
        if not failure_path.is_file():
            raise SystemExit(
                "Round 34 build exists without a recorded failed test gate")
        previous = common.load_json(failure_path)
        if previous.get("passed") is not False:
            raise SystemExit("Round 34 successful build already exists")
        records = list(previous.get("records", []))
        executable_source_commit = str(previous["source_commit"])
    configure = [
        str(CMAKE), "-S", str(common.ROOT), "-B", str(common.BUILD),
        "-G", "MinGW Makefiles",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_CXX_COMPILER={COMPILER.as_posix()}",
        f"-DCMAKE_MAKE_PROGRAM={MAKE.as_posix()}",
        "-DEXACT_EBRP_ENABLE_GUROBI=ON",
        "-DGUROBI_ROOT=D:/gurobi1302/win64",
    ]
    try:
        if not resumed_test_fix:
            execute("stage0_configure_gurobi", configure, records)
            execute("stage0_build_gurobi",
                    [str(CMAKE), "--build", str(common.BUILD), "-j", "2"],
                    records)
        else:
            execute("stage0_rebuild_elapsed_test_fix",
                    [str(CMAKE), "--build", str(common.BUILD), "-j", "2"],
                    records)
        execute("stage0_ctest_gurobi" +
                ("_after_elapsed_test_fix" if resumed_test_fix else ""),
                [str(CTEST), "--test-dir", str(common.BUILD),
                 "--output-on-failure"], records)
        for test in sorted((common.ROOT / "tests").glob("*.py")):
            execute(f"stage0_python_{test.stem}",
                    [str(PYTHON), str(test)], records)
    except Exception as error:
        common.write_json(common.OUT / "stage0_build_and_tests.json", {
            "schema": "round34-build-tests-v1",
            "source_commit": executable_source_commit,
            "validation_commit": head,
            "records": records,
            "passed": False,
            "failure": str(error),
        })
        raise
    summary = {
        "schema": "round34-build-tests-v1",
        "round_id": 34,
        "source_commit": executable_source_commit,
        "validation_commit": head,
        "compiler": subprocess.check_output(
            (str(COMPILER), "--version"), text=True).splitlines()[0],
        "cmake": subprocess.check_output(
            (str(CMAKE), "--version"), text=True).splitlines()[0],
        "gurobi_version": "13.0.2",
        "gurobi_executable": common.relative(common.EXE),
        "gurobi_executable_sha256": common.sha256(common.EXE),
        "clean_release_build_count": 1,
        "resumed_after_observational_elapsed_test_fix": resumed_test_fix,
        "ctest_invocation_count": 1,
        "python_test_script_count": sum(
            row["name"].startswith("stage0_python_") for row in records),
        "command_count": len(records),
        "records": records,
        "historical_failed_test_gate_count": sum(
            not row["passed"] for row in records[:-1]
            if row["name"].startswith("stage0_ctest_gurobi")),
        "passed": records[-1]["passed"] and all(
            row["passed"] for row in records
            if row["name"].startswith("stage0_python_")) and any(
                row["passed"] and row["name"].startswith("stage0_build_")
                for row in records),
    }
    common.write_json(common.OUT / "stage0_build_and_tests.json", summary)
    (common.OUT / "stage0_build_and_tests.partial.json").unlink(
        missing_ok=True)
    print(json.dumps({
        "passed": summary["passed"],
        "executable_sha256": summary["gurobi_executable_sha256"],
        "commands": len(records),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
