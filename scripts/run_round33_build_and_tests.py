#!/usr/bin/env python3
"""Create a clean Round 33 Gurobi Release build and run regressions."""

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
OUT = ROOT / "results" / "gf_v10_convergence_round33"
BUILD = ROOT / "build_round33" / "official" / "gurobi"
CMAKE = Path(
    r"D:\Program Files\Microsoft Visual Studio\2022\Professional"
    r"\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe")
CTEST = CMAKE.with_name("ctest.exe")
COMPILER = Path(r"D:\msys64\ucrt64\bin\g++.exe")
MAKE = Path(r"D:\msys64\ucrt64\bin\mingw32-make.exe")
PYTHON = Path(r"D:\msys64\ucrt64\bin\python.exe")
ROUND32_SOURCE = "0927d055710f43836053ecca055c0780b955a845"


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


def main() -> int:
    if BUILD.exists():
        raise SystemExit("clean Round 33 build destination already exists")
    OUT.mkdir(parents=True, exist_ok=True)
    BUILD.parent.mkdir(parents=True, exist_ok=True)
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    cpp_diff = subprocess.check_output(
        ("git", "diff", "--name-only", f"{ROUND32_SOURCE}..{head}",
         "--", "CMakeLists.txt", "include", "src", "tests/*.cpp"),
        cwd=ROOT, text=True).splitlines()
    if cpp_diff:
        raise RuntimeError(
            "Round 33 unexpectedly changes frozen C++ sources: "
            + ";".join(cpp_diff))
    records: list[dict[str, Any]] = []
    configure = [
        str(CMAKE), "-S", str(ROOT), "-B", str(BUILD),
        "-G", "MinGW Makefiles",
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_CXX_COMPILER={COMPILER.as_posix()}",
        f"-DCMAKE_MAKE_PROGRAM={MAKE.as_posix()}",
        "-DEXACT_EBRP_ENABLE_GUROBI=ON",
        "-DGUROBI_ROOT=D:/gurobi1302/win64",
    ]
    try:
        execute("stage0_configure_gurobi", configure, records)
        execute(
            "stage0_build_gurobi",
            [str(CMAKE), "--build", str(BUILD), "-j", "2"], records)
        execute(
            "stage0_ctest_gurobi",
            [str(CTEST), "--test-dir", str(BUILD),
             "--output-on-failure"], records)
        for test in sorted((ROOT / "tests").glob("*.py")):
            execute(
                f"stage0_python_{test.stem}",
                [str(PYTHON), str(test)], records)
    except Exception as error:
        write_json(OUT / "stage0_build_and_tests.json", {
            "schema": "round33-build-tests-v1",
            "source_commit": head,
            "records": records,
            "passed": False,
            "failure": str(error),
        })
        raise
    exe = BUILD / "ExactEBRP.exe"
    summary = {
        "schema": "round33-build-tests-v1",
        "source_commit": head,
        "round32_frozen_cpp_source_commit": ROUND32_SOURCE,
        "frozen_cpp_source_changed": False,
        "compiler": subprocess.check_output(
            (str(COMPILER), "--version"), text=True).splitlines()[0],
        "cmake": subprocess.check_output(
            (str(CMAKE), "--version"), text=True).splitlines()[0],
        "gurobi_version": "13.0.2",
        "gurobi_executable": exe.relative_to(ROOT).as_posix(),
        "gurobi_executable_sha256": sha256(exe),
        "clean_release_build_count": 1,
        "ctest_invocation_count": 1,
        "python_test_script_count": sum(
            row["name"].startswith("stage0_python_") for row in records),
        "command_count": len(records),
        "records": records,
        "passed": all(row["passed"] for row in records),
    }
    write_json(OUT / "stage0_build_and_tests.json", summary)
    (OUT / "stage0_build_and_tests.partial.json").unlink(missing_ok=True)
    print(json.dumps({
        "passed": summary["passed"],
        "gurobi_executable_sha256": summary["gurobi_executable_sha256"],
        "commands": len(records),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
