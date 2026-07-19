#!/usr/bin/env python3
"""Reproducible isolated MinGW release builds for both Round 24 configurations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build_round24"
CXX = Path(r"D:\msys64\ucrt64\bin\g++.exe")
CPLEX_INCLUDE = Path(r"C:\Program Files\IBM\ILOG\CPLEX_Studio2211\cplex\include")
CORE = [
    "Parser", "Evaluator", "Result", "StrictCertificate", "ModelCorrectness",
    "FileSha256", "DenseProgress", "GurobiCertificate", "GurobiProgress",
    "MipStartMapping", "ExternalGiniTree", "ConnectivityFlow", "Bounds",
    "ColumnPool", "TailoredExact", "Pricing", "Cuts", "Branching", "Master",
    "ColumnGeneration", "CplexBaseline", "TailoredBC", "TailoredBCCuts",
    "TailoredBCCallbacks", "TailoredBCCplexApi", "ControllingLeafScheduler",
    "GiniBranching", "GiniFrontierGeometry", "IntervalRowFactory",
    "hga_tgbc/HgaTgbcGreedy", "HgaTgbcRunner", "Logger",
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
    "Round24BackendTests": "tests/round24_backend_tests.cpp",
}


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def discover_gurobi() -> Path:
    candidates: list[Path] = []
    if os.environ.get("GUROBI_HOME"):
        candidates.append(Path(os.environ["GUROBI_HOME"]))
    for drive in "CDEF":
        root = Path(f"{drive}:/")
        if not root.exists():
            continue
        candidates.extend(sorted(root.glob("gurobi*/win64"), reverse=True))
    for candidate in candidates:
        if (candidate / "include" / "gurobi_c.h").exists():
            return candidate.resolve()
    raise SystemExit(
        "Gurobi-enabled build requested but no version-neutral "
        "gurobi*/win64/include/gurobi_c.h installation was found")


def build(configuration: str, clean: bool) -> dict[str, object]:
    enabled = configuration == "gurobi"
    release = BUILD / f"release_{configuration}"
    if clean and release.exists():
        shutil.rmtree(release)
    obj = release / "obj"
    tests = release / "tests"
    obj.mkdir(parents=True, exist_ok=True)
    tests.mkdir(parents=True, exist_ok=True)
    gurobi_root = discover_gurobi() if enabled else None
    flags = [
        str(CXX), "-std=c++17", "-O3", "-DNDEBUG", "-Wall", "-Wextra",
        "-Wpedantic", f"-I{ROOT / 'include'}", f"-I{CPLEX_INCLUDE}",
        f"-DEXACT_EBRP_ENABLE_GUROBI={1 if enabled else 0}",
    ]
    if gurobi_root:
        flags.append(f"-I{gurobi_root / 'include'}")
        flags.append(
            '-DEXACT_EBRP_GUROBI_ROOT="' +
            gurobi_root.as_posix().replace('"', '\\"') + '"')
    sources = CORE + ["GurobiBaseline" if enabled else "GurobiBaselineStub"]
    objects: list[Path] = []
    for stem in sources:
        source = ROOT / "src" / f"{stem}.cpp"
        target = obj / (stem.replace("/", "_") + ".o")
        run(flags + ["-c", str(source), "-o", str(target)])
        objects.append(target)
    main_obj = obj / "main.o"
    run(flags + ["-c", str(ROOT / "src" / "main.cpp"), "-o", str(main_obj)])
    executable = release / "ExactEBRP.exe"
    run([str(CXX), "-O3", "-o", str(executable), str(main_obj)] +
        [str(path) for path in objects])
    for name, relative in TESTS.items():
        test_obj = obj / f"{name}.o"
        run(flags + ["-c", str(ROOT / relative), "-o", str(test_obj)])
        run([str(CXX), "-O3", "-o", str(tests / f"{name}.exe"),
             str(test_obj)] + [str(path) for path in objects])
    frozen = BUILD / (
        "ExactEBRP-round24-gurobi.exe" if enabled
        else "ExactEBRP-round24-cplex.exe")
    shutil.copy2(executable, frozen)
    return {
        "configuration": configuration,
        "gurobi_enabled": enabled,
        "gurobi_root": str(gurobi_root) if gurobi_root else "not_applicable",
        "executable": frozen.relative_to(ROOT).as_posix(),
        "executable_sha256": sha(frozen),
        "core_source_count": len(sources),
        "test_executable_count": len(TESTS),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true")
    parser.add_argument(
        "--configuration", choices=("default", "gurobi", "both"),
        default="both")
    args = parser.parse_args()
    if not CXX.exists():
        raise SystemExit(f"compiler missing: {CXX}")
    if not CPLEX_INCLUDE.exists():
        raise SystemExit(f"CPLEX include missing: {CPLEX_INCLUDE}")
    selected = ("default", "gurobi") if args.configuration == "both" else (
        args.configuration,)
    records = [build(item, args.clean) for item in selected]
    provenance = {
        "schema": "round24-dual-configuration-frozen-executables-v1",
        "source_commit_at_build": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "compiler": str(CXX),
        "compiler_version": subprocess.check_output(
            [str(CXX), "--version"], text=True).splitlines()[0],
        "optimization": "-O3 -DNDEBUG -std=c++17",
        "clean_build": bool(args.clean),
        "builds": records,
    }
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "round24_frozen_executables.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(provenance, indent=2))


if __name__ == "__main__":
    main()
