#!/usr/bin/env python3
"""Bind Round 32 protocol, sources, instances, matrices, and executables."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_long_run_validation_round32"
BUILD = ROOT / "build_round32" / "official"
CPLEX_EXE = BUILD / "cplex" / "ExactEBRP.exe"
GUROBI_EXE = BUILD / "gurobi" / "ExactEBRP.exe"
STARTING_HEAD = "919fd688a29a730d897db612213982ba8792a53f"
OBSERVED_LIVE_MAIN = "2acc29c5556ddd3b229d65fd2b3fb8982ce6b8d2"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def main() -> int:
    build = json.loads(
        (OUT / "stage0_build_and_tests.json").read_text(encoding="utf-8"))
    if not build.get("passed"):
        raise RuntimeError("clean build and regression gate did not pass")
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    if build["source_commit"] != head:
        raise RuntimeError("official executables were not built from HEAD")
    source_files = (
        "CMakeLists.txt",
        "include/Instance.hpp",
        "include/PaperExternalGiniTree.hpp",
        "include/Result.hpp",
        "src/GurobiBaseline.cpp",
        "src/PaperExternalGiniTree.cpp",
        "src/Result.cpp",
        "src/main.cpp",
        "scripts/generate_hard_exact_stress_instances.py",
        "scripts/generate_round32_multi_m.py",
        "scripts/analyze_round32.py",
        "scripts/package_round32_evidence.py",
        "scripts/prepare_round32.py",
        "scripts/run_round32_build_and_tests.py",
        "scripts/run_round32_experiments.py",
        "scripts/freeze_round32.py",
        "tests/round31_c6_tests.cpp",
        "tests/round31_protocol_tests.py",
        "tests/round32_protocol_tests.py",
        "tests/round32_runner_trace_tests.py",
    )
    for path_text in source_files:
        if not (ROOT / path_text).is_file():
            raise RuntimeError(f"frozen source is missing: {path_text}")
    artifacts = {
        "protocol": OUT / "round32_protocol.md",
        "existing_instance_manifest":
            OUT / "round32_existing_instance_manifest.csv",
        "multi_m_manifest": OUT / "round32_multi_m_manifest.csv",
        "stage3_freeze": OUT / "round32_stage3_freeze.csv",
        "official_matrix": OUT / "round32_official_matrix.csv",
        "stage0_matrix": OUT / "round32_stage0_matrix.csv",
    }
    manifest: dict[str, Any] = {
        "schema": "round32-frozen-manifest-v1",
        "branch": subprocess.check_output(
            ("git", "branch", "--show-current"), cwd=ROOT,
            text=True).strip(),
        "starting_head": STARTING_HEAD,
        "observed_live_main": OBSERVED_LIVE_MAIN,
        "source_commit": head,
        "engineering_fix_commits": [head],
        "frozen_before_official_results": True,
        "official_results_started_when_written": False,
        "cplex_executable_path": relative(CPLEX_EXE),
        "cplex_executable_sha256": sha256(CPLEX_EXE),
        "gurobi_executable_path": relative(GUROBI_EXE),
        "gurobi_executable_sha256": sha256(GUROBI_EXE),
        "compiler": build["compiler"],
        "cmake": build["cmake"],
        "cplex_version": build["cplex_version"],
        "gurobi_version": build["gurobi_version"],
        "source_file_sha256": {
            path_text: sha256(ROOT / path_text)
            for path_text in source_files
        },
        "c6_algorithm_selector": "round31-nonblocking-native-bound",
        "c6_lifecycle": "round31-open-native-bounded",
        "initial_intervals": 4,
        "maximum_adaptive_depth": 8,
        "minimum_adaptive_width": 1e-4,
        "normalized_split_threshold_rho": 0.01,
        "global_strengthening_family_count": 6,
        "interval_local_strengthening_family_count": 9,
        "new_strategy_parameter_count": 0,
        "shutdown_margin_seconds": 15,
        "emergency_watchdog_separation_seconds": 90,
        "experiment_row_resume": True,
        "algorithmic_solve_state_resume": False,
    }
    for key, path in artifacts.items():
        manifest[f"{key}_path"] = relative(path)
        manifest[f"{key}_sha256"] = sha256(path)
    if manifest["cplex_executable_sha256"] != build[
            "cplex_executable_sha256"]:
        raise RuntimeError("CPLEX executable hash changed after clean build")
    if manifest["gurobi_executable_sha256"] != build[
            "gurobi_executable_sha256"]:
        raise RuntimeError("Gurobi executable hash changed after clean build")
    write_json(OUT / "round32_frozen_manifest.json", manifest)

    source_path = OUT / "source_of_truth.md"
    current = source_path.read_text(encoding="utf-8")
    current = current.replace(
        "- Frozen C6 source commit: recorded after the intended pre-run commit in\n"
        "  `round32_frozen_manifest.json`",
        f"- Frozen C6 source commit: `{head}`")
    temporary = source_path.with_suffix(".md.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(current)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, source_path)
    print(json.dumps({
        "source_commit": head,
        "protocol_sha256": manifest["protocol_sha256"],
        "cplex_executable_sha256": manifest["cplex_executable_sha256"],
        "gurobi_executable_sha256": manifest["gurobi_executable_sha256"],
        "frozen_source_file_count": len(source_files),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
