#!/usr/bin/env python3
"""Freeze the post-Stage-0 Round 29 C4 candidate and official protocol."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import run_round29_experiments as runner


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_gurobi_performance_recovery_round29"
SOURCE_FILES = (
    "CMakeLists.txt",
    "include/FixedIntervalMipBackend.hpp",
    "include/HgaTgbcRunner.hpp",
    "include/Instance.hpp",
    "include/ProcessPhaseLedger.hpp",
    "include/Result.hpp",
    "include/hga_tgbc/HybridGA.h",
    "src/GurobiBaseline.cpp",
    "src/HgaTgbcRunner.cpp",
    "src/PaperExternalGiniTree.cpp",
    "src/ProcessPhaseLedger.cpp",
    "src/ReplicaExternalGiniTree.cpp",
    "src/Result.cpp",
    "src/main.cpp",
    "scripts/analyze_round29_results.py",
    "scripts/freeze_round29.py",
    "scripts/run_round29_build_and_tests.py",
    "scripts/run_round28_experiments.py",
    "scripts/run_round29_experiments.py",
    "scripts/run_round29_stage0.py",
    "tests/round29_performance_recovery_tests.cpp",
    "tests/round29_protocol_tests.py",
)


def git(*args: str) -> str:
    return subprocess.check_output(
        ("git", *args), cwd=ROOT, text=True).strip()


def digest_text(value: Any) -> str:
    material = json.dumps(
        value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    temporary.replace(path)


def source_hashes() -> dict[str, str]:
    return {
        path: runner.sha256(ROOT / path)
        for path in SOURCE_FILES
    }


def scan_forbidden_logic() -> list[dict[str, Any]]:
    sources = {
        path: (ROOT / path).read_text(encoding="utf-8")
        for path in SOURCE_FILES
    }
    paper = sources["src/PaperExternalGiniTree.cpp"]
    main = sources["src/main.cpp"]
    checks = (
        (
            "no_instance_name_or_path_decision",
            paper,
            r"(?:if|switch)\s*\([^\)]*instance\.(?:name|path)",
        ),
        (
            "no_size_dispatch_in_c4_decision",
            paper,
            r"(?:if|switch)\s*\([^\)]*instance\.(?:V|M)",
        ),
        (
            "no_wall_clock_split_decision",
            paper[paper.index("evaluatePaperLpSplitDecision"):
                  paper.index("evaluatePaperTerminalMipDecision")],
            r"(?:elapsed|runtime|wall|deadline|Work|nodes)",
        ),
        (
            "no_attempt_retry_split_decision",
            paper[paper.index("evaluatePaperLpSplitDecision"):
                  paper.index("evaluatePaperTerminalMipDecision")],
            r"(?:attempt|retry|solution_count)",
        ),
        (
            "no_known_objective_dispatch",
            paper + main,
            r"(?:known_optimum|known_objective|historical_benchmark)",
        ),
        (
            "explicit_distinct_c4_selector",
            main,
            r"round29-bound-gain-incremental",
        ),
    )
    records = []
    for name, text, pattern in checks:
        found = re.search(pattern, text, flags=re.IGNORECASE)
        positive = name == "explicit_distinct_c4_selector"
        passed = bool(found) if positive else not bool(found)
        records.append({
            "check": name,
            "passed": passed,
            "pattern": pattern,
            "match_count": len(re.findall(
                pattern, text, flags=re.IGNORECASE)),
            "interpretation": (
                "required selector present" if positive
                else "forbidden decision dependency absent"),
        })
    return records


def command_fingerprint() -> tuple[str, int]:
    commands = []
    for stage in ("stage1", "stage2", "stage4"):
        for instance, arm, repetition in runner.stage_matrix(stage):
            run_dir = Path("<ROUND29_RUN>") / (
                f"{stage}__{instance}__{arm}__{repetition}")
            commands.append({
                "stage": stage,
                "instance": instance,
                "arm": arm,
                "repetition": repetition,
                "command": runner.command_for(
                    instance, arm, runner.OFFICIAL_BUDGET, run_dir),
            })
    return digest_text(commands), len(commands)


def main() -> int:
    frozen_inputs = (
        *SOURCE_FILES,
        "CMakeLists.txt",
        "scripts/run_round29_experiments.py",
        "scripts/run_round29_stage0.py",
        "tests/round29_performance_recovery_tests.cpp",
        "tests/round29_protocol_tests.py",
        "results/gf_gurobi_performance_recovery_round29/round29_protocol.md",
    )
    if subprocess.run(
            ("git", "diff", "--quiet", "HEAD", "--", *frozen_inputs),
            cwd=ROOT, check=False).returncode != 0:
        raise SystemExit(
            "Round 29 frozen source/protocol inputs must be committed first")
    if not runner.GUROBI_EXE.is_file():
        raise SystemExit("official Gurobi executable missing")
    cplex_exe = ROOT / "build_round29/cplex_only/ExactEBRP.exe"
    if not cplex_exe.is_file():
        raise SystemExit("official CPLEX-only executable missing")
    if not runner.INSTANCE_MANIFEST.is_file():
        runner.prepare_instance_manifest()
    scans = scan_forbidden_logic()
    with (OUT / "c4_forbidden_logic_scan.csv").open(
            "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(scans[0]))
        writer.writeheader()
        writer.writerows(scans)
    if not all(record["passed"] for record in scans):
        raise SystemExit("C4 forbidden-logic scan failed")

    parameters = {
        "schema": "round29-c4-parameter-freeze-v1",
        "arm": "C4-CANDIDATE",
        "algorithm_selector": "round29-bound-gain-incremental",
        "mathematical_split_rule": {
            "requires_complete_parent_lp": True,
            "requires_both_complete_child_lps": True,
            "split_if_child_lp_infeasible": True,
            "split_if_min_feasible_child_bound_strictly_exceeds_parent": True,
            "certificate_tolerance": 1e-7,
            "declined_split_action": "exact_unsplit_parent_mip",
            "cutoff_fathom": "complete_lp_bound_ge_verified_ub_minus_1e-7",
        },
        "geometry": {
            "initial_intervals": 4,
            "adaptive": True,
            "maximum_depth": 8,
            "minimum_width": 1e-4,
            "split_factor": 2,
            "selector_variables": 0,
        },
        "execution": {
            "same_leaf_model_object_retention": True,
            "integer_domain_restored_before_parent_mip": True,
            "basis_submission": False,
            "native_tree_reuse_claim": False,
            "mip_start": False,
            "local_redecode_repair": False,
            "threads": 1,
            "gurobi_seed": 0,
            "gurobi_presolve": -1,
            "relative_mip_gap": 0.0,
            "absolute_mip_gap": 0.0,
        },
        "primal_heuristic": {
            "method": "hga-tgbc",
            "seed": 20260626,
            "stop": "generation-stagnation",
            "no_improve_generations": 2000,
            "configured_runs": 12,
            "local_redecode_repair": False,
            "verified_incumbent_use": "upper_bound_and_cutoff_only",
        },
        "deadline": {
            "origin": "process_entry",
            "official_nominal_seconds": 300,
            "engineering_shutdown_margin_seconds": 5,
            "margin_may_affect_split_decision": False,
        },
        "static_formulation": {
            "global_row_families": 6,
            "interval_local_row_families": 9,
            "connectivity_flow_variant": "round20-current",
            "presolve_contract": "off",
            "search_contract": "traditional",
            "row_attachment": "full-inherited-pack",
            "row_timing": "deferred",
            "child_estimate": "parent-copy",
        },
    }
    write_json(OUT / "c4_parameter_freeze.json", parameters)

    command_sha, command_count = command_fingerprint()
    manifest = {
        "schema": "round29-c4-frozen-manifest-v1",
        "arm": "C4-CANDIDATE",
        "source_commit": git("rev-parse", "HEAD"),
        "branch": git("branch", "--show-current"),
        "protocol_path": runner.relative(runner.PROTOCOL),
        "protocol_sha256": runner.sha256(runner.PROTOCOL),
        "instance_manifest_path": runner.relative(runner.INSTANCE_MANIFEST),
        "instance_manifest_sha256": runner.sha256(
            runner.INSTANCE_MANIFEST),
        "parameter_freeze_path": runner.relative(
            OUT / "c4_parameter_freeze.json"),
        "parameter_freeze_sha256": runner.sha256(
            OUT / "c4_parameter_freeze.json"),
        "forbidden_logic_scan_path": runner.relative(
            OUT / "c4_forbidden_logic_scan.csv"),
        "forbidden_logic_scan_sha256": runner.sha256(
            OUT / "c4_forbidden_logic_scan.csv"),
        "gurobi_executable_path": runner.relative(runner.GUROBI_EXE),
        "gurobi_executable_sha256": runner.sha256(runner.GUROBI_EXE),
        "cplex_executable_path": runner.relative(cplex_exe),
        "cplex_executable_sha256": runner.sha256(cplex_exe),
        "source_file_sha256": source_hashes(),
        "official_command_matrix_sha256": command_sha,
        "official_runner_row_count": command_count,
        "stage1_rows": len(runner.stage_matrix("stage1")),
        "stage2_new_rows": len(runner.stage_matrix("stage2")),
        "stage2_materialized_rows": 51,
        "stage4_rows": len(runner.stage_matrix("stage4")),
        "compiler": "GNU g++ 14.2.0 (MinGW-w64 UCRT64)",
        "cplex_version": "22.1.1",
        "gurobi_version": "13.0.2",
        "official_results_observed_before_freeze": False,
        "stable_mainline": "corrected CPLEX S0/F0 unchanged",
    }
    write_json(runner.MANIFEST, manifest)
    print(json.dumps({
        "source_commit": manifest["source_commit"],
        "gurobi_executable_sha256":
            manifest["gurobi_executable_sha256"],
        "cplex_executable_sha256": manifest["cplex_executable_sha256"],
        "protocol_sha256": manifest["protocol_sha256"],
        "official_runner_row_count": command_count,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
