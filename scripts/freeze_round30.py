#!/usr/bin/env python3
"""Freeze Round 30 source, commands, parameters, and official executables."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import run_round30_experiments as runner


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_c0_mechanism_transfer_c5_round30"
PARAMETERS = OUT / "c5_parameter_freeze.json"
FORBIDDEN = OUT / "c5_forbidden_logic_scan.csv"
MANIFEST = OUT / "c5_manifest.json"

SOURCE_FILES = (
    "CMakeLists.txt",
    "include/FixedIntervalMipBackend.hpp",
    "include/PaperExternalGiniTree.hpp",
    "include/Result.hpp",
    "src/ExternalGiniTree.cpp",
    "src/GurobiBaseline.cpp",
    "src/PaperExternalGiniTree.cpp",
    "src/Result.cpp",
    "src/main.cpp",
    "scripts/analyze_round30_c0_forensics.py",
    "scripts/analyze_round30_development.py",
    "scripts/analyze_round30_results.py",
    "scripts/freeze_round30.py",
    "scripts/package_round30_evidence.py",
    "scripts/round30_bound_trace.py",
    "scripts/run_round30_build_and_tests.py",
    "scripts/run_round30_development.py",
    "scripts/run_round30_experiments.py",
    "scripts/run_round30_stage0.py",
    "tests/round30_c0_parser_tests.py",
    "tests/round30_c5_tests.cpp",
    "tests/round30_protocol_tests.py",
    "tests/round30_trace_tests.py",
    "results/gf_c0_mechanism_transfer_c5_round30/round30_protocol.md",
    "results/gf_c0_mechanism_transfer_c5_round30/c5_design_decision.md",
    "results/gf_c0_mechanism_transfer_c5_round30/c5_exactness_argument.md",
    "results/gf_c0_mechanism_transfer_c5_round30/c5_solver_event_contract.md",
    "results/gf_c0_mechanism_transfer_c5_round30/c5_split_strategy.md",
    "results/gf_c0_mechanism_transfer_c5_round30/c5_incremental_reoptimization.md",
    "results/gf_c0_mechanism_transfer_c5_round30/stage0_incident.md",
)


def write_json(path: Path, value: Any) -> None:
    runner.json_write(path, value)


def git(*args: str) -> str:
    return subprocess.check_output(
        ("git", *args), cwd=ROOT, text=True).strip()


def c5_decision_source() -> str:
    source = (ROOT / "src/PaperExternalGiniTree.cpp").read_text(
        encoding="utf-8")
    return source[
        source.index("C5BoundTargetSplitDecision "
                     "evaluateC5BoundTargetSplitDecision"):
        source.index("PaperTerminalMipDecision "
                     "evaluatePaperTerminalMipDecision")]


def forbidden_scan() -> list[dict[str, Any]]:
    decision = c5_decision_source()
    command_samples = "\n".join(
        "\0".join(runner.command_for(
            instance, "C5-CANDIDATE", 300,
            OUT / "command_freeze_samples" / instance))
        for instance in runner.PRIMARY)
    rules = (
        ("fixed_time_quantum", r"\b(?:time_limit_seconds|quantum)\b", decision),
        ("work_limit", r"\bWorkLimit\b", decision + command_samples),
        ("arbitrary_node_limit", r"\bNodeLimit\b", decision + command_samples),
        ("solution_limit", r"\bSolutionLimit\b", decision + command_samples),
        ("attempt_count", r"\battempt(?:s|_number|_count)?\b", decision),
        ("retry_count", r"\bretr(?:y|ies)\b", decision),
        ("family_dispatch", r"\bfamily\b", decision),
        ("size_dispatch", r"\binstance\.(?:V|M)\b", decision),
        ("seed_dispatch", r"\bseed\b", decision),
        ("instance_name_or_path", r"\binstance\.(?:name|path)\b", decision),
        ("historical_optimum", r"\b(?:known|historical)_optimum\b", decision),
        ("plain_gurobi_fallback", r"\bplain(?:_gurobi|-GRB)?\b", decision),
        ("portfolio_dispatch", r"\bportfolio\b", decision),
    )
    records = []
    for name, pattern, body in rules:
        matches = re.findall(pattern, body, flags=re.I)
        records.append({
            "rule": name,
            "pattern": pattern,
            "match_count": len(matches),
            "passed": len(matches) == 0,
            "scope": "c5_decision_and_frozen_command_where_applicable",
            "reason": (
                "no_forbidden_occurrence"
                if not matches else "forbidden_occurrence_detected"),
        })
    if not all(row["passed"] for row in records):
        raise RuntimeError("C5 forbidden-logic scan failed")
    with FORBIDDEN.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    return records


def main() -> int:
    runner.prepare_instance_manifest()
    if not runner.GUROBI_EXE.is_file() or not runner.CPLEX_EXE.is_file():
        raise SystemExit("clean official executables must exist before freeze")
    for path_text in SOURCE_FILES:
        if not (ROOT / path_text).is_file():
            raise RuntimeError(f"freeze source missing: {path_text}")
    parameters = {
        "schema": "round30-c5-parameter-freeze-v1",
        "algorithm_arm": "C5-CANDIDATE",
        "algorithm_selector": "round30-dual-bound-target",
        "lifecycle": "round30-same-leaf-bound-target",
        "algorithmically_distinct": True,
        "fallback_prototype_used": False,
        "normalized_split_threshold_rho": 0.01,
        "certificate_tolerance": 1e-7,
        "native_target": "minimum_complete_feasible_child_lp_bound",
        "native_target_callback_attribute": "GRB_CB_MIP_OBJBND",
        "native_target_stop": "GRBterminate_after_valid_bound_reaches_target",
        "initial_intervals": 4,
        "split_geometry": "binary_midpoint_exact_atomic_cover",
        "maximum_depth": 8,
        "minimum_width": 0.0001,
        "split_factor": 2,
        "process_cap_seconds": 300,
        "shutdown_margin_seconds": 5,
        "solver_threads": 1,
        "gurobi_seed": 0,
        "internal_time_work_node_solution_attempt_retry_controls": 0,
        "family_size_seed_instance_dispatch": 0,
        "lp_basis_transfer": False,
        "native_tree_continuation_claim": False,
        "stable_mainline": "S0/F0-CPLEX",
        "c0_role": "exact_non_paper_compatible_diagnostic_only",
        "frozen_before_official_stage1": True,
    }
    write_json(PARAMETERS, parameters)
    rules = forbidden_scan()
    head = git("rev-parse", "HEAD")
    manifest = {
        "schema": "round30-c5-frozen-manifest-v1",
        "source_commit": head,
        "branch": git("branch", "--show-current"),
        "protocol_path": runner.relative(runner.PROTOCOL),
        "protocol_sha256": runner.sha256(runner.PROTOCOL),
        "instance_manifest_path": runner.relative(runner.INSTANCE_MANIFEST),
        "instance_manifest_sha256": runner.sha256(runner.INSTANCE_MANIFEST),
        "parameter_freeze_path": runner.relative(PARAMETERS),
        "parameter_freeze_sha256": runner.sha256(PARAMETERS),
        "forbidden_logic_scan_path": runner.relative(FORBIDDEN),
        "forbidden_logic_scan_sha256": runner.sha256(FORBIDDEN),
        "source_file_sha256": {
            path_text: runner.sha256(ROOT / path_text)
            for path_text in SOURCE_FILES
        },
        "gurobi_executable_path": runner.relative(runner.GUROBI_EXE),
        "gurobi_executable_sha256": runner.sha256(runner.GUROBI_EXE),
        "cplex_executable_path": runner.relative(runner.CPLEX_EXE),
        "cplex_executable_sha256": runner.sha256(runner.CPLEX_EXE),
        "official_budget_seconds": runner.OFFICIAL_BUDGET,
        "shutdown_margin_seconds": runner.SHUTDOWN_MARGIN,
        "stage1_launched_rows": len(runner.stage_matrix("stage1")),
        "stage2_launched_rows": len(runner.stage_matrix("stage2")),
        "stage2_materialized_rows": 51,
        "stage3_launched_rows": len(runner.stage_matrix("stage3")),
        "stage3_materialized_rows": 25,
        "stage4_rows": len(runner.stage_matrix("stage4")),
        "primary_instance_count": len(runner.PRIMARY),
        "forbidden_scan_rules": len(rules),
        "forbidden_scan_failures": sum(not row["passed"] for row in rules),
        "license_file_accessed_by_freeze": False,
        "official_results_started": False,
    }
    write_json(MANIFEST, manifest)
    print(json.dumps({
        "source_commit": head,
        "gurobi_executable_sha256":
            manifest["gurobi_executable_sha256"],
        "cplex_executable_sha256":
            manifest["cplex_executable_sha256"],
        "protocol_sha256": manifest["protocol_sha256"],
        "forbidden_scan_rules": len(rules),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
