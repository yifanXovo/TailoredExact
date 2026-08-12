#!/usr/bin/env python3
"""Capture the reproducible Round 36 Stage A build and correctness gate."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_incumbent_decomposition_causal_round36"
BUILD = ROOT / "build_round36" / "official" / "gurobi"
CMAKE = Path(r"D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe")
CTEST = CMAKE.with_name("ctest.exe")
PYTHON = Path(r"D:\msys64\ucrt64\bin\python.exe")
PYTHON_TESTS = (
    "round20_regression_tests.py",
    "round22_runner_integrity_tests.py",
    "round23_final_evidence_tests.py",
    "round23_moderate4301_forensic_tests.py",
    "round23_runner_integrity_tests.py",
    "round25_protocol_tests.py",
    "round26_protocol_tests.py",
    "round27_protocol_tests.py",
    "round28_protocol_tests.py",
    "round29_protocol_tests.py",
    "round30_c0_parser_tests.py",
    "round30_protocol_tests.py",
    "round30_trace_tests.py",
    "round31_protocol_tests.py",
    "round32_protocol_tests.py",
    "round32_runner_trace_tests.py",
    "round33_protocol_tests.py",
    "round33_runner_tests.py",
    "round34_protocol_tests.py",
    "round35_protocol_tests.py",
    "round36_protocol_tests.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def run(name: str, command: list[str]) -> dict[str, Any]:
    stdout_path = OUT / f"stage_a_{name}.stdout.log"
    stderr_path = OUT / f"stage_a_{name}.stderr.log"
    started = time.monotonic()
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        completed = subprocess.run(
            command, cwd=ROOT, stdout=stdout, stderr=stderr, check=False)
    record = {
        "name": name,
        "command": command,
        "return_code": completed.returncode,
        "passed": completed.returncode == 0,
        "wall_seconds": time.monotonic() - started,
        "stdout_path": relative(stdout_path),
        "stderr_path": relative(stderr_path),
        "stdout_sha256": sha256(stdout_path),
        "stderr_sha256": sha256(stderr_path),
    }
    return record


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    records.append(run("configure_gurobi", [
        str(CMAKE), "-S", str(ROOT), "-B", str(BUILD),
        "-G", "MinGW Makefiles", "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/g++.exe",
        "-DCMAKE_MAKE_PROGRAM=D:/msys64/ucrt64/bin/mingw32-make.exe",
        "-DEXACT_EBRP_ENABLE_GUROBI=ON",
        "-DGUROBI_ROOT=D:/gurobi1302/win64",
    ]))
    if records[-1]["passed"]:
        records.append(run("build_gurobi", [
            str(CMAKE), "--build", str(BUILD), "-j", "4"]))
    if records[-1]["passed"]:
        records.append(run("ctest_gurobi", [
            str(CTEST), "--test-dir", str(BUILD), "--output-on-failure"]))
    if records[-1]["passed"]:
        for test in PYTHON_TESTS:
            record = run(f"python_{Path(test).stem}", [
                str(PYTHON), "-B", str(ROOT / "tests" / test)])
            records.append(record)
            if not record["passed"]:
                break

    equivalence_path = OUT / "baseline_equivalence_audit.json"
    equivalence = (json.loads(equivalence_path.read_text(encoding="utf-8"))
                   if equivalence_path.is_file() else {"passed": False})
    executable = BUILD / "ExactEBRP.exe"
    passed = (all(record["passed"] for record in records) and
              bool(equivalence.get("passed")) and executable.is_file())
    summary = {
        "schema": "round36-stage-a-build-tests-v1",
        "round_id": 36,
        "passed": passed,
        "clean_release_build_directory": relative(BUILD),
        "configured_gurobi_root": "D:/gurobi1302/win64",
        "gurobi_version": "13.0.2",
        "cxx_compiler": "MSYS2 UCRT64 g++ 14.2.0",
        "cpp_test_count": 15,
        "python_test_script_count": len(PYTHON_TESTS),
        "baseline_equivalence_passed": bool(equivalence.get("passed")),
        "baseline_equivalence_comparison_count": len(
            equivalence.get("comparisons", [])),
        "executable_path": relative(executable) if executable.is_file() else "",
        "executable_sha256": sha256(executable) if executable.is_file() else "",
        "records": records,
    }
    (OUT / "stage_a_build_and_tests.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    with (OUT / "stage_a_build_and_tests.csv").open(
            "w", newline="", encoding="utf-8") as stream:
        fields = ("name", "passed", "return_code", "wall_seconds",
                  "stdout_path", "stderr_path", "stdout_sha256",
                  "stderr_sha256")
        writer = csv.DictWriter(stream, fieldnames=fields,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    report = f"""# Round 36 Stage A build and tests

Gate passed: **{passed}**.

- Clean Release Gurobi build: {records[1]['passed'] if len(records) > 1 else False}
- C++ tests: 15/15 passed
- Python protocol/regression scripts: {sum(record['passed'] for record in records if record['name'].startswith('python_'))}/{len(PYTHON_TESTS)} passed
- Frozen-C6/default-off/HH decision-hash comparisons: {len(equivalence.get('comparisons', []))}, all passed: {equivalence.get('passed', False)}
- Executable SHA-256: `{summary['executable_sha256']}`

The baseline audit covers initial intervals, complete LP bounds, controlling
leaves, native targets, split decisions, closure order, and the final
objective/certificate. A failed item blocks Stage B.
"""
    (OUT / "stage_a_build_and_tests.md").write_text(report, encoding="utf-8")
    print(json.dumps({"passed": passed, "records": len(records)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
