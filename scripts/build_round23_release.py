#!/usr/bin/env python3
"""Reproducible isolated MinGW release build for Round 23."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build_round23"
RELEASE = BUILD / "release"
CXX = Path(r"D:\msys64\ucrt64\bin\g++.exe")
CPLEX_INCLUDE = Path(r"C:\Program Files\IBM\ILOG\CPLEX_Studio2211\cplex\include")
CORE = [
    "Parser", "Evaluator", "Result", "StrictCertificate", "ModelCorrectness",
    "DenseProgress", "ConnectivityFlow", "Bounds", "ColumnPool", "TailoredExact",
    "Pricing", "Cuts", "Branching", "Master", "ColumnGeneration", "CplexBaseline",
    "TailoredBC", "TailoredBCCuts", "TailoredBCCallbacks", "TailoredBCCplexApi",
    "ControllingLeafScheduler", "GiniBranching", "GiniFrontierGeometry",
    "IntervalRowFactory", "hga_tgbc/HgaTgbcGreedy", "HgaTgbcRunner", "Logger",
    "DispersionChildBound",
]
TESTS = {
    "ControllingLeafSchedulerTests": "tests/controlling_leaf_scheduler_tests.cpp",
    "GlobalGiniTreeTests": "tests/global_gini_tree_tests.cpp",
    "StrictCertificateTests": "tests/strict_certificate_tests.cpp",
    "ConnectivityFlowTests": "tests/connectivity_flow_tests.cpp",
    "StrictSerializationTests": "tests/strict_serialization_tests.cpp",
    "ModelCorrectnessTests": "tests/model_correctness_tests.cpp",
    "DenseProgressTests": "tests/dense_progress_tests.cpp",
    "DispersionChildBoundTests": "tests/dispersion_child_bound_tests.cpp",
}


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    if not CXX.exists():
        raise SystemExit(f"compiler missing: {CXX}")
    if not CPLEX_INCLUDE.exists():
        raise SystemExit(f"CPLEX include missing: {CPLEX_INCLUDE}")
    if args.clean and RELEASE.exists():
        shutil.rmtree(RELEASE)
    obj = RELEASE / "obj"
    test_dir = RELEASE / "tests"
    obj.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)
    flags = [
        str(CXX), "-std=c++17", "-O3", "-DNDEBUG", "-Wall", "-Wextra",
        "-Wpedantic", f"-I{ROOT / 'include'}", f"-I{CPLEX_INCLUDE}",
    ]
    core_objects: list[Path] = []
    for stem in CORE:
        source = ROOT / "src" / f"{stem}.cpp"
        target = obj / (stem.replace("/", "_") + ".o")
        run(flags + ["-c", str(source), "-o", str(target)])
        core_objects.append(target)
    main_obj = obj / "main.o"
    run(flags + ["-c", str(ROOT / "src" / "main.cpp"), "-o", str(main_obj)])
    executable = RELEASE / "ExactEBRP.exe"
    run([str(CXX), "-O3", "-o", str(executable), str(main_obj)] +
        [str(path) for path in core_objects])
    for name, relative in TESTS.items():
        test_obj = obj / f"{name}.o"
        run(flags + ["-c", str(ROOT / relative), "-o", str(test_obj)])
        run([str(CXX), "-O3", "-o", str(test_dir / f"{name}.exe"),
             str(test_obj)] + [str(path) for path in core_objects])
    frozen = BUILD / "ExactEBRP-frozen.exe"
    shutil.copy2(executable, frozen)
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    provenance = {
        "schema": "round23-frozen-executable-v1",
        "source_commit_at_build": source_commit,
        "executable": frozen.relative_to(ROOT).as_posix(),
        "executable_sha256": sha(frozen),
        "compiler": str(CXX),
        "compiler_version": subprocess.check_output(
            [str(CXX), "--version"], text=True).splitlines()[0],
        "optimization": "-O3 -DNDEBUG -std=c++17",
        "clean_build": bool(args.clean),
        "core_source_count": len(CORE),
        "test_executable_count": len(TESTS),
    }
    (BUILD / "frozen_executable.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
