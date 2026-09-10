#!/usr/bin/env python3
"""Run the final Round 39 C++ and repository Python regression gates."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import round39_common as common


CTEST = Path(
    r"D:\Program Files\Microsoft Visual Studio\2022\Professional"
    r"\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe")
PYTHON = Path(r"D:\msys64\ucrt64\bin\python.exe")


def run(name: str, command: list[str]) -> dict[str, Any]:
    stdout_path = common.OUT / f"{name}.stdout.log"
    stderr_path = common.OUT / f"{name}.stderr.log"
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(
            command, cwd=common.ROOT, env=environment,
            stdout=stdout, stderr=stderr, check=False)
    return {
        "round_id": 39, "name": name,
        "command": subprocess.list2cmdline(command),
        "return_code": completed.returncode,
        "wall_seconds": time.monotonic() - started,
        "stdout_path": common.relative(stdout_path),
        "stderr_path": common.relative(stderr_path),
        "passed": completed.returncode == 0,
    }


def main() -> int:
    records = [run("post_ctest_gurobi", [
        str(CTEST), "--test-dir", str(common.BUILD), "--output-on-failure",
    ])]
    if not records[-1]["passed"]:
        common.write_json(common.OUT / "post_build_and_tests.json", {
            "schema": "round39-post-tests-v1", "passed": False,
            "records": records,
        })
        return 1
    for test in sorted((common.ROOT / "tests").glob("*.py")):
        record = run(f"post_python_{test.stem}", [str(PYTHON), str(test)])
        records.append(record)
        if not record["passed"]:
            break
    common.write_csv(common.OUT / "post_build_and_tests.csv", records)
    summary = {
        "schema": "round39-post-tests-v1", "round_id": 39,
        "passed": all(row["passed"] for row in records),
        "cpp_ctest_invocations": 1,
        "python_test_script_count": sum(
            row["name"].startswith("post_python_") for row in records),
        "official_executable_sha256": common.sha256(common.EXE),
        "records": records,
    }
    common.write_json(common.OUT / "post_build_and_tests.json", summary)
    print(json.dumps({
        "passed": summary["passed"],
        "commands": len(records),
        "python_test_scripts": summary["python_test_script_count"],
    }, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
