#!/usr/bin/env python3
"""Bind Round 33 protocol, instances, fingerprints, source, and executable."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import round33_common as common


STARTING_HEAD = "2db8fe5b5c33145e1a8cd6dca86f8459885fa2bf"
OBSERVED_LIVE_MAIN = "e352055138c4ea00f308bed94523ee161dad1a6d"


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def main() -> int:
    if any(common.RUNS.glob("*/completion_marker.json")):
        raise RuntimeError("official results started before Round 33 freeze")
    build = common.load_json(common.OUT / "stage0_build_and_tests.json")
    preflight = common.load_json(common.OUT / "round33_preflight_summary.json")
    if not build.get("passed") or not preflight.get("passed"):
        raise RuntimeError("Round 33 build/preflight gate did not pass")
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=common.ROOT,
        text=True).strip()
    branch = subprocess.check_output(
        ("git", "branch", "--show-current"), cwd=common.ROOT,
        text=True).strip()
    if build["source_commit"] != head:
        raise RuntimeError("official executable was not built from HEAD")
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
        "scripts/generate_round33_v10.py",
        "scripts/prepare_round33.py",
        "scripts/round33_common.py",
        "scripts/run_round33_build_and_tests.py",
        "scripts/run_round33_preflight.py",
        "scripts/freeze_round33.py",
        "scripts/run_round33_experiments.py",
        "scripts/analyze_round33.py",
        "scripts/package_round33_evidence.py",
        "scripts/round30_bound_trace.py",
        "tests/round31_c6_tests.cpp",
        "tests/round33_protocol_tests.py",
        "tests/round33_runner_tests.py",
    )
    for path_text in source_files:
        if not (common.ROOT / path_text).is_file():
            raise RuntimeError(f"frozen source missing: {path_text}")
    artifacts = {
        "protocol": common.OUT / "round33_protocol.md",
        "v10_instance_manifest": common.V10_MANIFEST,
        "v12_anchor_manifest": common.V12_MANIFEST,
        "fingerprints": common.FINGERPRINTS,
        "certificate_preflight":
            common.OUT / "round33_certificate_preflight.csv",
        "official_matrix": common.MATRIX,
        "repeatability_freeze":
            common.OUT / "round33_repeatability_freeze.csv",
        "stage0_matrix": common.OUT / "round33_stage0_matrix.csv",
    }
    manifest: dict[str, Any] = {
        "schema": "round33-frozen-manifest-v1",
        "round_id": 33,
        "branch": branch,
        "starting_head": STARTING_HEAD,
        "observed_live_main": OBSERVED_LIVE_MAIN,
        "source_commit": head,
        "frozen_before_official_results": True,
        "official_results_started_when_written": False,
        "gurobi_executable_path": common.relative(common.EXE),
        "gurobi_executable_sha256": common.sha256(common.EXE),
        "compiler": build["compiler"],
        "cmake": build["cmake"],
        "gurobi_version": build["gurobi_version"],
        "source_file_sha256": {
            path_text: common.sha256(common.ROOT / path_text)
            for path_text in source_files
        },
        "frozen_cpp_source_changed_since_round32": False,
        "c6_algorithm_selector": "round31-nonblocking-native-bound",
        "c6_lifecycle": "round31-open-native-bounded",
        "initial_intervals": 4,
        "maximum_adaptive_depth": 8,
        "minimum_adaptive_width": 1e-4,
        "normalized_split_threshold_rho": 0.01,
        "new_strategy_parameter_count": 0,
        "process_cap_seconds": 3600,
        "shutdown_margin_seconds": common.SHUTDOWN_MARGIN,
        "emergency_watchdog_seconds": common.WATCHDOG,
        "primary_timing_field": "final_process_wall_time_seconds",
        "experiment_row_resume": True,
        "algorithmic_solve_state_resume": False,
    }
    for key, path in artifacts.items():
        manifest[f"{key}_path"] = common.relative(path)
        manifest[f"{key}_sha256"] = common.sha256(path)
    if manifest["gurobi_executable_sha256"] != build[
            "gurobi_executable_sha256"]:
        raise RuntimeError("Gurobi executable hash changed after build")
    write_json(common.MANIFEST, manifest)
    source_path = common.OUT / "source_of_truth.md"
    current = source_path.read_text(encoding="utf-8")
    current += (
        f"- Frozen source commit: `{head}`\n"
        f"- Frozen executable SHA-256: "
        f"`{manifest['gurobi_executable_sha256']}`\n"
        f"- Protocol SHA-256: `{manifest['protocol_sha256']}`\n"
    )
    temporary = source_path.with_suffix(".md.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(current)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, source_path)
    print(json.dumps({
        "source_commit": head,
        "protocol_sha256": manifest["protocol_sha256"],
        "gurobi_executable_sha256":
            manifest["gurobi_executable_sha256"],
        "frozen_source_file_count": len(source_files),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
