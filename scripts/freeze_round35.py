#!/usr/bin/env python3
"""Freeze the complete Round 35 matrix, commands, and executable identity."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import round35_common as common


R32 = common.ROOT / "results" / "gf_c6_long_run_validation_round32"
R34 = common.ROOT / "results" / "gf_c6_documentation_hga_round34"


def option(command: list[str], name: str) -> str:
    index = command.index(name)
    return command[index + 1]


def simple_start_preflight() -> None:
    matrix = common.csv_rows(R34 / "round34_official_matrix.csv")
    selected = [row for row in matrix
                if row["stage"] in {"v10", "transfer"}
                and row["arm"] == common.ARM]
    if len(selected) != 22:
        raise RuntimeError(f"expected 22 Round 34 SIMPLE preflight rows, got {len(selected)}")
    output = []
    for row in selected:
        run_dir = R34 / "runs" / row["run_id"]
        result = common.load_json(run_dir / "result.json")
        candidates = common.csv_rows(run_dir / "heuristic_candidates.csv")
        passed = (
            result.get("external_gini_tree_startup_variant") == "simple-start"
            and int(result.get("incumbent_candidates_verified", 0)) == 3
            and len(candidates) == 3
            and all(str(item.get("verifier_passed", "")).lower() == "true"
                    for item in candidates))
        output.append({
            "round_id": 35,
            "evidence_source_round": 34,
            "historical_run_id": row["run_id"],
            "instance_id": row["instance_id"],
            "candidate_count": len(candidates),
            "independently_verified_candidates": sum(
                str(item.get("verifier_passed", "")).lower() == "true"
                for item in candidates),
            "reported_startup_variant": result.get(
                "external_gini_tree_startup_variant"),
            "verified_upper_bound": result.get(
                "external_gini_tree_verified_upper_bound"),
            "preflight_passed": passed,
            "historical_evidence_read_only": True,
        })
    if not all(row["preflight_passed"] for row in output):
        raise RuntimeError("SIMPLE independent-verifier preflight failed")
    common.write_csv(
        common.OUT / "simple_start_independent_verification_preflight.csv",
        output)


def main() -> int:
    if common.FROZEN_MANIFEST.exists():
        raise SystemExit("Round 35 is already frozen")
    if common.RUNS.exists() and any(common.RUNS.iterdir()):
        raise RuntimeError("official results exist before freeze")
    if subprocess.check_output(
            ("git", "branch", "--show-current"), cwd=common.ROOT,
            text=True).strip() != "codex/round35-simple-start-full-qualification":
        raise RuntimeError("unexpected branch")
    build = common.load_json(common.OUT / "stage0_build_and_tests.json")
    if not build.get("passed") or not common.EXE.is_file():
        raise RuntimeError("clean build/test gate did not pass")
    if not all(row["identical"] == "True" for row in common.csv_rows(
            common.OUT / "frozen_c6_equivalence.csv")):
        raise RuntimeError("frozen C6 equivalence failed")
    simple_start_preflight()
    items = common.inventory()
    rows = common.csv_rows(common.OFFICIAL_MATRIX)
    commands: dict[str, Any] = {}
    audit = []
    for row in rows:
        item = items[row["instance_id"]]
        run_dir = common.RUNS / row["run_id"]
        command = common.command_for(row, item, run_dir)
        commands[row["run_id"]] = {
            "round_id": 35,
            "stage": row["stage"],
            "instance_id": row["instance_id"],
            "instance_sha256": item["instance_sha256"],
            "arm": row["arm"],
            "command": command,
        }
        one_thread = all(option(command, name) == "1" for name in (
            "--threads", "--mip-threads", "--cplex-threads",
            "--compact-bc-threads"))
        audit.append({
            "round_id": 35,
            "run_id": row["run_id"],
            "stage": row["stage"],
            "arm": row["arm"],
            "process_cap_seconds": row["process_cap_seconds"],
            "simple_start": option(command, "--primal-heuristic") == "greedy",
            "reported_variant_contract": option(
                command, "--round34-c6-startup-variant") == "simple-start",
            "gurobi_seed_zero": option(command, "--gurobi-seed") == "0",
            "one_thread": one_thread,
            "frozen_c6_scheduler": option(
                command, "--external-gini-scheduling")
                == "round31-nonblocking-native-bound",
            "frozen_c6_lifecycle": option(
                command, "--external-gini-lifecycle")
                == "round31-open-native-bounded",
            "historical_comparator_command": False,
            "command_audit_passed": one_thread,
        })
    if len(commands) != 52 or not all(row["command_audit_passed"] for row in audit):
        raise RuntimeError("command freeze audit failed")
    common.write_json(common.COMMAND_FREEZE, {
        "schema": "round35-command-freeze-v1",
        "round_id": 35,
        "commands": commands,
        "frozen_before_official_results": True,
    })
    common.write_csv(common.OUT / "round35_command_audit.csv", audit)

    artifacts = {
        "protocol": common.OUT / "round35_protocol.md",
        "source_of_truth": common.OUT / "source_of_truth.md",
        "instance_manifest": common.INSTANCE_MANIFEST,
        "matrix_1800": common.MATRIX_1800,
        "matrix_3600": common.MATRIX_3600,
        "repeat_freeze": common.REPEAT_FREEZE,
        "historical_compatibility":
            common.OUT / "historical_comparator_compatibility.csv",
        "fingerprints": common.FINGERPRINTS,
        "frozen_c6_equivalence": common.OUT / "frozen_c6_equivalence.csv",
        "official_matrix": common.OFFICIAL_MATRIX,
        "command_freeze": common.COMMAND_FREEZE,
        "stage0_build_and_tests": common.OUT / "stage0_build_and_tests.json",
    }
    source_files = (
        "CMakeLists.txt", "include/Instance.hpp", "include/Result.hpp",
        "include/PaperExternalGiniTree.hpp", "include/hga_tgbc/HybridGA.h",
        "src/HgaTgbcRunner.cpp", "src/main.cpp",
        "src/Result.cpp", "src/PaperExternalGiniTree.cpp",
        "src/ControllingLeafScheduler.cpp", "src/IntervalRowFactory.cpp",
        "src/GurobiBaseline.cpp", "scripts/round35_common.py",
        "scripts/prepare_round35.py", "scripts/freeze_round35.py",
        "scripts/run_round35_experiments.py",
        "scripts/run_round35_build_and_tests.py",
        "tests/round35_protocol_tests.py",
    )
    manifest: dict[str, Any] = {
        "schema": "round35-frozen-manifest-v1",
        "round_id": 35,
        "branch": "codex/round35-simple-start-full-qualification",
        "starting_head": "b1225b9e723516f736df69b5d79f367551ad78ff",
        "observed_live_main_at_preparation":
            "722b9b50cbd2155c43af1b2b511f55d579efb59d",
        "solver_source_commit": build["source_commit"],
        "gurobi_version": "13.0.2",
        "gurobi_executable_path": common.relative(common.EXE),
        "gurobi_executable_sha256": common.sha256(common.EXE),
        "new_primary_solver_arm": common.ARM,
        "historical_comparator_processes_launched": 0,
        "matrix_1800_rows": 35,
        "matrix_3600_v50_rows": 12,
        "repeat_rows": 5,
        "total_new_solver_rows": 52,
        "initial_intervals": 4,
        "normalized_split_threshold_rho": 0.01,
        "maximum_adaptive_depth": 8,
        "minimum_adaptive_width": 0.0001,
        "gurobi_seed": 0,
        "threads": 1,
        "shutdown_margin_seconds": common.SHUTDOWN_MARGIN,
        "watchdog_separation_seconds": common.WATCHDOG_SEPARATION,
        "source_file_sha256": {
            path: common.sha256(common.ROOT / path) for path in source_files
        },
        "historical_read_only_source_sha256": {
            common.relative(path): common.sha256(path) for path in (
                R32 / "round32_frozen_manifest.json",
                R32 / "round32_official_matrix.csv",
                R32 / "runner_row_summary.csv",
                R32 / "round32_stage3_freeze.csv",
                R34 / "final_audit_summary.json",
                R34 / "hga_v10_official_ablation.csv",
                R34 / "hga_transfer_anchor_results.csv",
            )
        },
        "official_results_started_when_written": False,
        "frozen_before_official_results": True,
    }
    for name, path in artifacts.items():
        manifest[f"{name}_path"] = common.relative(path)
        manifest[f"{name}_sha256"] = common.sha256(path)
    common.write_json(common.FROZEN_MANIFEST, manifest)
    print(json.dumps({
        "frozen": True,
        "rows": len(rows),
        "solver_source_commit": manifest["solver_source_commit"],
        "executable_sha256": manifest["gurobi_executable_sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
