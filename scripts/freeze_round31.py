#!/usr/bin/env python3
"""Freeze the selected C6 source, parameters, commands, and official matrix."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Iterable

import run_round29_experiments as r29


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_nonblocking_gurobi_c6_round31"
BUILD = ROOT / "build_round31/official"
CPLEX_EXE = BUILD / "cplex_r1/ExactEBRP.exe"
GUROBI_EXE = BUILD / "gurobi_r1/ExactEBRP.exe"
STARTING_HEAD = "893656f85fa6394dac787fee78baad2a52cdd2d2"
PRIMARY = tuple(r29.PRIMARY)
STAGE1 = (
    "V12_M1", "V12_M2", "high_imbalance_seed3202",
    "moderate_seed3302", "tight_T_seed3101", "tight_T_seed4101",
    "tight_T_seed5102", "high_imbalance_seed6202",
    "moderate_seed6301",
)
STAGE4 = (
    "V12_M1", "V12_M2", "high_imbalance_seed3202",
    "moderate_seed3302", "tight_T_seed3101",
    "high_imbalance_seed6202", "moderate_seed6301",
)
STAGE5_EXISTING = (
    "V12_M2", "high_imbalance_seed3202", "tight_T_seed4101",
    "tight_T_seed5102", "high_imbalance_seed6202",
    "moderate_seed6301",
)
STAGE6_EXISTING = (
    "V12_M2", "high_imbalance_seed3202", "moderate_seed3302",
    "tight_T_seed3101", "tight_T_seed5102",
    "high_imbalance_seed6202", "moderate_seed6301",
)


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
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    temporary.replace(path)


def write_csv(path: Path, rows: Iterable[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    material = list(rows)
    if not material:
        raise ValueError(f"empty CSV: {path}")
    columns = fields or list(material[0])
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(material)
    temporary.replace(path)


def sealed_instances() -> dict[str, dict[str, Any]]:
    rows = list(csv.DictReader(
        (OUT / "round31_sealed_heldout_manifest.csv").open(
            newline="", encoding="utf-8")))
    return {
        row["instance_id"]: {
            "path": row["path"],
            "family": row["stress_type"],
            "V": int(row["V"]),
            "M": int(row["M"]),
            "sha256": row["sha256"],
        }
        for row in rows
    }


def prepare_instance_manifest(
        sealed: dict[str, dict[str, Any]]) -> Path:
    rows: list[dict[str, Any]] = []
    for name in PRIMARY:
        path_text, family, vehicles, crews, expected = r29.INSTANCES[name]
        path = ROOT / path_text
        if sha256(path) != expected:
            raise RuntimeError(f"authoritative instance mismatch: {name}")
        rows.append({
            "instance": name,
            "family": family,
            "V": vehicles,
            "M": crews,
            "path": path_text,
            "sha256": expected,
            "sealed_heldout": False,
            "stage2_primary": True,
        })
    for name, item in sealed.items():
        path = ROOT / item["path"]
        if sha256(path) != item["sha256"]:
            raise RuntimeError(f"sealed instance mismatch: {name}")
        rows.append({
            "instance": name,
            "family": item["family"],
            "V": item["V"],
            "M": item["M"],
            "path": item["path"],
            "sha256": item["sha256"],
            "sealed_heldout": True,
            "stage2_primary": False,
        })
    path = OUT / "round31_instance_manifest.csv"
    write_csv(path, rows)
    return path


def scan_forbidden_logic() -> Path:
    source = (ROOT / "src/PaperExternalGiniTree.cpp").read_text(
        encoding="utf-8")
    start = source.index(
        "C6FrontierDecision evaluateC6FrontierDecision(")
    finish = source.index(
        "PaperTerminalMipDecision evaluatePaperTerminalMipDecision(",
        start)
    predicates = source[start:finish].lower()
    rules = [
        ("predicate_elapsed_time", predicates, r"\belapsed\b"),
        ("predicate_work", predicates, r"\bwork\b"),
        ("predicate_node", predicates, r"\bnode"),
        ("predicate_solution_limit", predicates, r"solutionlimit"),
        ("predicate_attempt", predicates, r"\battempt"),
        ("predicate_retry", predicates, r"\bretry"),
        ("predicate_family", predicates, r"\bfamily\b"),
        ("predicate_instance", predicates, r"\binstance\b"),
        ("predicate_seed", predicates, r"\bseed\b"),
        ("predicate_path", predicates, r"\bpath\b"),
        ("source_work_limit", source.lower(), r"grb_dbl_par_worklimit"),
        ("source_node_limit", source.lower(), r"grb_dbl_par_nodelimit"),
        ("source_solution_limit", source.lower(), r"grb_int_par_solutionlimit"),
        ("c6_attempt_selector", source.lower(),
         r"c6[^\n]{0,80}split_after_attempt"),
        ("c6_family_dispatch", source.lower(),
         r"c6[^\n]{0,80}(family|instance\.name)"),
    ]
    rows = []
    for name, text, pattern in rules:
        matches = re.findall(pattern, text)
        rows.append({
            "rule": name,
            "pattern": pattern,
            "match_count": len(matches),
            "passed": len(matches) == 0,
            "scope": "C6 mathematical predicate"
                if text is predicates else "C6 implementation source",
        })
    path = OUT / "c6_forbidden_logic_scan.csv"
    write_csv(path, rows)
    if any(not row["passed"] for row in rows):
        raise RuntimeError("C6 forbidden-logic scan failed")
    return path


def official_matrix(
        sealed: dict[str, dict[str, Any]]) -> Path:
    sealed_names = tuple(sealed)
    sealed_v20 = next(
        name for name in sealed_names if sealed[name]["V"] == 20)
    sealed_v50 = next(
        name for name in sealed_names if sealed[name]["V"] == 50)
    rows: list[dict[str, Any]] = []

    def add(stage: int, instances: Iterable[str], arms: Iterable[str],
            budget: int, repetition: int = 0,
            conditional: bool = False) -> None:
        for instance in instances:
            for arm in arms:
                rows.append({
                    "stage": stage,
                    "instance": instance,
                    "arm": arm,
                    "budget_seconds": budget,
                    "repetition": repetition,
                    "conditional": conditional,
                    "serial_order": len(rows) + 1,
                    "frozen_before_official_results": True,
                })

    add(1, STAGE1, ("C5-CANDIDATE", "C6-CANDIDATE"), 300)
    add(2, PRIMARY, ("P-GRB", "C6-CANDIDATE"), 300)
    add(3, sealed_names,
        ("P-GRB", "C5-CANDIDATE", "C6-CANDIDATE"), 300)
    add(4, STAGE4,
        ("S0-CPLEX", "P-GRB", "P-GRB-HGA",
         "C5-CANDIDATE", "C6-CANDIDATE"), 300)
    repeat_instances = STAGE5_EXISTING + (sealed_v20, sealed_v50)
    add(5, repeat_instances, ("C6-CANDIDATE",), 300, repetition=1)
    add(5, repeat_instances, ("C6-CANDIDATE",), 300, repetition=2)
    medium_instances = STAGE6_EXISTING + (sealed_v20, sealed_v50)
    add(6, medium_instances,
        ("P-GRB", "C5-CANDIDATE", "C6-CANDIDATE"),
        1200, conditional=True)
    path = OUT / "round31_official_matrix.csv"
    write_csv(path, rows)
    return path


def main() -> int:
    if not CPLEX_EXE.is_file() or not GUROBI_EXE.is_file():
        raise SystemExit("official clean executables are unavailable")
    build_record = json.loads(
        (OUT / "stage0_build_and_tests.json").read_text(encoding="utf-8"))
    if not build_record.get("passed"):
        raise RuntimeError("clean build/regression record did not pass")
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    sealed = sealed_instances()
    instance_manifest = prepare_instance_manifest(sealed)
    forbidden_scan = scan_forbidden_logic()
    matrix = official_matrix(sealed)
    parameter_freeze = {
        "schema": "round31-c6-parameter-freeze-v1",
        "algorithm_arm": "C6-CANDIDATE",
        "algorithm_selector": "round31-nonblocking-native-bound",
        "lifecycle": "round31-open-native-bounded",
        "parent_first_rule":
            "one_minimum_strictly_higher_other_leaf_bound_then_lazy_children",
        "frontier_target_repeats_per_leaf": 0,
        "child_target":
            "minimum_complete_feasible_child_lp_bound_when_current_gain_below_rho",
        "forced_split_after_child_target": False,
        "no_gain_rule": "exact_closure_after_unused_frontier_milestone_absent",
        "certificate_tolerance": 1e-7,
        "initial_intervals": 4,
        "maximum_depth": 8,
        "minimum_width": 1e-4,
        "split_factor": 2,
        "normalized_split_threshold_rho": 0.01,
        "total_policy_threshold_count": 1,
        "new_strategy_parameter_count": 0,
        "gurobi_seed": 0,
        "solver_threads": 1,
        "process_cap_seconds": 300,
        "shutdown_margin_seconds": 5,
        "internal_time_work_node_solution_attempt_retry_controls": 0,
        "family_size_seed_path_dispatch": 0,
        "lp_basis_transfer": False,
        "native_tree_continuation_claim": False,
        "same_model_object_retention": True,
        "fallback_prototype_used": False,
        "stable_mainline": "S0/F0-CPLEX",
        "frozen_before_official_stage1": True,
    }
    parameter_path = OUT / "c6_parameter_freeze.json"
    write_json(parameter_path, parameter_freeze)
    source_files = (
        "CMakeLists.txt",
        "include/Instance.hpp",
        "include/PaperExternalGiniTree.hpp",
        "include/Result.hpp",
        "src/GurobiBaseline.cpp",
        "src/PaperExternalGiniTree.cpp",
        "src/Result.cpp",
        "src/main.cpp",
        "tests/round31_c6_tests.cpp",
        "tests/round31_protocol_tests.py",
        "scripts/run_round31_development.py",
        "scripts/analyze_round31_development.py",
        "scripts/run_round31_build_and_tests.py",
        "scripts/run_round31_stage0.py",
        "scripts/run_round31_experiments.py",
        "scripts/analyze_round31_results.py",
        "scripts/freeze_round31.py",
        "results/gf_nonblocking_gurobi_c6_round31/c6_design_decision.md",
        "results/gf_nonblocking_gurobi_c6_round31/c6_exactness_argument.md",
        "results/gf_nonblocking_gurobi_c6_round31/c6_state_machine.md",
        "results/gf_nonblocking_gurobi_c6_round31/"
        "c6_native_bound_target_contract.md",
        "results/gf_nonblocking_gurobi_c6_round31/c6_split_strategy.md",
        "results/gf_nonblocking_gurobi_c6_round31/c6_exact_closure_rule.md",
        "results/gf_nonblocking_gurobi_c6_round31/"
        "c6_incremental_reoptimization.md",
    )
    manifest = {
        "schema": "round31-c6-frozen-manifest-v1",
        "branch": subprocess.check_output(
            ("git", "branch", "--show-current"), cwd=ROOT,
            text=True).strip(),
        "starting_head": STARTING_HEAD,
        "source_commit": head,
        "official_results_started": False,
        "cplex_executable_path": relative(CPLEX_EXE),
        "cplex_executable_sha256": sha256(CPLEX_EXE),
        "gurobi_executable_path": relative(GUROBI_EXE),
        "gurobi_executable_sha256": sha256(GUROBI_EXE),
        "protocol_path": relative(OUT / "round31_protocol.md"),
        "protocol_sha256": sha256(OUT / "round31_protocol.md"),
        "parameter_freeze_path": relative(parameter_path),
        "parameter_freeze_sha256": sha256(parameter_path),
        "forbidden_logic_scan_path": relative(forbidden_scan),
        "forbidden_logic_scan_sha256": sha256(forbidden_scan),
        "forbidden_scan_failures": 0,
        "instance_manifest_path": relative(instance_manifest),
        "instance_manifest_sha256": sha256(instance_manifest),
        "official_matrix_path": relative(matrix),
        "official_matrix_sha256": sha256(matrix),
        "primary_instance_count": len(PRIMARY),
        "sealed_instance_count": len(sealed),
        "official_short_run_row_count":
            sum(1 for row in csv.DictReader(
                matrix.open(newline="", encoding="utf-8"))
                if row["stage"] != "6"),
        "conditional_medium_row_count": 27,
        "license_file_accessed_by_freeze": False,
        "source_file_sha256": {
            path: sha256(ROOT / path) for path in source_files
        },
    }
    write_json(OUT / "c6_manifest.json", manifest)
    print(json.dumps({
        "source_commit": head,
        "short_rows": manifest["official_short_run_row_count"],
        "conditional_rows": manifest["conditional_medium_row_count"],
        "forbidden_failures": 0,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
