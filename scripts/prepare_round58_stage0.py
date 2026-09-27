#!/usr/bin/env python3
"""Audit Round 57 and freeze the complete Round 58 panel before performance."""

from __future__ import annotations

import csv
import json
import platform
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import round58_common as r58


TRACKED_USER_FILES = (
    "results/gf_compact_bc_round/handling_convention_test/handling_convention.json",
    "results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv",
    "results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json",
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=r58.ROOT, text=True).strip()


def first_line(command: list[str], fallback: str) -> str:
    try:
        return subprocess.check_output(
            command, text=True, stderr=subprocess.STDOUT).splitlines()[0]
    except (OSError, subprocess.CalledProcessError, IndexError):
        return fallback


def file_entry(path: Path) -> dict[str, Any]:
    return {"path": r58.repo_path(path), "bytes": path.stat().st_size,
            "sha256": r58.sha256_file(path)}


def verify_round57_inventory() -> dict[str, Any]:
    inventory_path = r58.ROUND57 / "final_data_inventory.csv"
    inventory = r58.read_csv(inventory_path)
    checks: list[dict[str, Any]] = []
    for row in inventory:
        path = r58.ROOT / row["path"]
        present = path.is_file()
        actual = r58.sha256_file(path) if present else ""
        checks.append({
            "path": row["path"], "category": row["category"],
            "present": present, "expected_sha256": row["sha256"],
            "actual_sha256": actual, "match": present and actual == row["sha256"],
        })
    dataset_files = [p for p in r58.REFERENCE.rglob("*") if p.is_file()]
    counts = r58.read_json(r58.REFERENCE / "manifests" / "dataset_counts.json")
    regen = r58.read_csv(r58.ROUND57 / "deterministic_regeneration_audit.csv")
    parser = r58.read_csv(r58.ROUND57 / "parser_compatibility.csv")
    validation = r58.read_csv(r58.ROUND57 / "generated_instance_validation.csv")
    source = r58.read_json(r58.REFERENCE / "source_provenance.json")
    generator_contract = r58.read_json(r58.REFERENCE / "generator_contract.json")
    frozen_contract = r58.read_json(r58.ROUND57 / "frozen_generator_contract.json")
    final_decision = r58.read_json(r58.ROUND57 / "final_decision.json")
    source_checks = []
    for label, record in generator_contract["source_files"].items():
        path = Path(record["path"])
        actual = r58.sha256_file(path) if path.is_file() else ""
        source_checks.append({
            "source": label, "path": str(path), "present": path.is_file(),
            "expected_sha256": record["sha256"], "actual_sha256": actual,
            "match": actual == record["sha256"],
        })
    inventory_pass = all(row["match"] for row in checks)
    regen_pass = len(regen) == 349 and all(
        r58.truth(row["byte_equal"]) and row["validation_status"] == "PASS"
        for row in regen)
    parser_pass = len(parser) == 240 and all(
        row.get("validation_status", row.get("parser_status", "PASS")) == "PASS"
        or r58.truth(row.get("cpp_parser_accepted", row.get("accepted", False)))
        for row in parser)
    validation_pass = len(validation) == 240 and all(
        row["validation_status"] == "PASS" for row in validation)
    contract_match = r58.canonical_json(generator_contract) == r58.canonical_json(frozen_contract)
    acceptable = all((inventory_pass, regen_pass, parser_pass, validation_pass,
                      contract_match, all(row["match"] for row in source_checks),
                      len(dataset_files) == 349,
                      counts.get("instances") == 240,
                      counts.get("landscapes") == 60,
                      counts.get("mapping_rows") == 500,
                      counts.get("scenarios") == 960,
                      counts.get("selections") == 20))
    return {
        "schema": "round58-local-round57-dataset-audit-v1",
        "dataset_family": r58.DATASET_FAMILY,
        "classification_before_round58": final_decision["generation_classification"],
        "source_classification": final_decision["source_classification"],
        "optimizer_results_used_to_generate_or_select": False,
        "dataset_file_count": len(dataset_files),
        "manifest_counts": counts,
        "final_inventory_row_count": len(inventory),
        "final_inventory_all_present_and_hash_matched": inventory_pass,
        "final_inventory_mismatch_count": sum(not row["match"] for row in checks),
        "deterministic_regeneration_rows": len(regen),
        "deterministic_regeneration_pass": regen_pass,
        "cpp_parser_rows": len(parser), "cpp_parser_pass": parser_pass,
        "generated_validation_rows": len(validation),
        "generated_validation_pass": validation_pass,
        "generator_contract_matches_round57_freeze": contract_match,
        "generator_source_sha256": r58.sha256_file(
            r58.ROOT / "scripts" / "generate_citibike443_regional_v1.py"),
        "source_hash_checks": source_checks,
        "source_provenance_schema": source.get("schema"),
        "historical_preservation_classification": final_decision["preservation_classification"],
        "round57_family_acceptable_for_frozen_round58_panel": acceptable,
        "audit_rows_retained_locally": checks,
    }


def current_status() -> tuple[list[str], list[str]]:
    lines = subprocess.check_output(
        ["git", "status", "--porcelain=v1", "-uall"], cwd=r58.ROOT,
        text=True, encoding="utf-8", errors="surrogateescape").splitlines()
    return ([line for line in lines if not line.startswith("??")],
            [line[3:] for line in lines if line.startswith("??")])


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    tree = git("show", "-s", "--format=%T", "HEAD")
    if branch != r58.BRANCH or head != r58.BASE_COMMIT or tree != r58.BASE_TREE:
        raise RuntimeError(
            f"Round 58 must start from {r58.BRANCH} at the exact Round 56 base")
    r58.EVIDENCE.mkdir(parents=True, exist_ok=True)
    tracked_status, untracked_paths = current_status()
    if len(tracked_status) != 3:
        raise RuntimeError(f"unexpected tracked working-tree changes: {tracked_status}")
    tracked = []
    for path_text in TRACKED_USER_FILES:
        path = r58.ROOT / path_text
        tracked.append({**file_entry(path), "git_status": "modified",
                        "git_blob": git("hash-object", path_text)})

    round57_audit = verify_round57_inventory()
    if not round57_audit["round57_family_acceptable_for_frozen_round58_panel"]:
        raise RuntimeError("Round 57 family failed local qualification")
    r58.write_json(r58.EVIDENCE / "local_round57_dataset_audit.json", round57_audit)

    pr = json.loads(subprocess.check_output([
        "gh", "pr", "view", str(r58.BASE_PR), "--json",
        "number,state,isDraft,baseRefName,headRefName,headRefOid,url,mergeStateStatus"
    ], cwd=r58.ROOT, text=True))
    remote_match = (pr["headRefName"] == r58.BASE_BRANCH and
                    pr["headRefOid"] == r58.BASE_COMMIT and
                    pr["state"] == "OPEN")
    if not remote_match:
        raise RuntimeError("PR #115 no longer matches the authorized Round 56 base")

    round57_owned = {
        row["path"] for row in round57_audit["audit_rows_retained_locally"]
        if row["match"]
    }
    round57_status_paths = {
        path for path in untracked_paths
        if path.startswith("reference/citibike443-regional-v1/")
        or path.startswith("results/data_generation_citibike_round57/")
        or path in {"scripts/generate_citibike443_regional_v1.py",
                    "scripts/round57_parser_probe.cpp"}
    }
    round58_status_paths = {
        path for path in untracked_paths
        if path.startswith("results/gf_citibike443_k1_vs_pgrb_round58/")
        or path in {"scripts/round58_common.py", "scripts/prepare_round58_stage0.py"}
        or path.startswith("scripts/__pycache__/round58_common.")
        or path.startswith("scripts/__pycache__/prepare_round58_stage0.")
    }
    pre_round57_count = (
        len(untracked_paths) - len(round57_status_paths) - len(round58_status_paths))
    preservation = {
        "schema": "round58-preexisting-file-preservation-audit-v1",
        "recorded_at_utc": now,
        "baseline_recorded_before_round58_artifact_generation": True,
        "tracked_modified_files": tracked,
        "tracked_modified_file_count": len(tracked),
        "untracked_file_count_before_round58": len(untracked_paths),
        "round57_status_owned_untracked_file_count": len(round57_status_paths),
        "round58_in_progress_paths_excluded_from_baseline_count": len(round58_status_paths),
        "pre_round57_untracked_file_count": pre_round57_count,
        "round57_final_inventory_owned_paths": len(round57_owned),
        "round57_inventory_hashes_all_match": round57_audit[
            "final_inventory_all_present_and_hash_matched"],
        "pre_round57_baseline_source": (
            "results/data_generation_citibike_round57/repository_start_audit.json"),
        "pre_round57_baseline_fingerprint": (
            "9f5ac5fb127e3fd1e3ab73c4342bebae0ac621e2753e4f08368964213f56d17e"),
        "pre_round57_expected_untracked_count": 58453,
        "pre_round57_count_matches": pre_round57_count == 58453,
        "preservation_rule": (
            "No reset, clean, stash, relocation, overwrite, or deletion; verify the "
            "three tracked hashes, the Round 57 inventory, and the inherited Round 57 "
            "historical preservation baseline at finalization."),
        "round58_outputs_excluded_from_baseline": True,
        "final_reverification_pending": True,
    }
    if not preservation["pre_round57_count_matches"]:
        raise RuntimeError("pre-Round57 untracked baseline count changed")
    r58.write_json(r58.EVIDENCE / "preexisting_file_preservation_audit.json", preservation)

    r58.write_json(r58.EVIDENCE / "repository_start_audit.json", {
        "schema": "round58-repository-start-audit-v1",
        "recorded_at_utc": now,
        "repository": str(r58.ROOT), "starting_branch": r58.BASE_BRANCH,
        "created_branch": r58.BRANCH, "local_head": head, "local_tree": tree,
        "expected_head": r58.BASE_COMMIT, "expected_tree": r58.BASE_TREE,
        "base_pr": pr, "local_remote_head_equal": remote_match,
        "local_remote_tree_equal": True,
        "tracked_preexisting_modification_count": len(tracked),
        "untracked_preexisting_file_count": len(untracked_paths),
        "round57_dataset_present_before_round58": True,
        "round57_dataset_committed_at_start": False,
        "repository_recloned_reset_cleaned_stashed_or_relocated": False,
        "round58_performance_result_opened": False,
        "pr_115_modified": False,
    })
    r58.write_json(r58.EVIDENCE / "environment_audit.json", {
        "schema": "round58-environment-audit-v1", "recorded_at_utc": now,
        "machine": platform.node(), "operating_system": platform.platform(),
        "os_detail": "Microsoft Windows 10 Professional 10.0.19045",
        "cpu": "12th Gen Intel(R) Core(TM) i7-12700KF",
        "logical_processors": 20, "memory_bytes": 34163961856,
        "compiler": first_line(["D:/msys64/ucrt64/bin/g++.exe", "--version"], "unavailable"),
        "cmake": first_line([
            "D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/"
            "CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe", "--version"], "unavailable"),
        "python": first_line(["D:/msys64/ucrt64/bin/python.exe", "--version"], "unavailable"),
        "gurobi": first_line(["D:/gurobi1302/win64/bin/gurobi_cl.exe", "--version"], "unavailable"),
        "gurobi_home": "D:/gurobi1302/win64", "gurobi_license_probe_pending": True,
        "development_build": "build/dev-round58-gurobi",
        "official_build_rule": "one clean source-SHA-named build after source freeze",
    })

    primary, matched, reserve = r58.build_panel()
    complete = primary + matched
    fields = r58.panel_csv_fields()
    r58.write_csv(r58.EVIDENCE / "round58_primary_panel.csv",
                  r58.normalized_panel_rows(primary), fields)
    r58.write_csv(r58.EVIDENCE / "round58_matched_T_panel.csv",
                  r58.normalized_panel_rows(matched), fields)
    r58.write_csv(r58.EVIDENCE / "round58_complete_panel.csv",
                  r58.normalized_panel_rows(complete), fields)
    r58.write_csv(r58.EVIDENCE / "round58_reserve_inventory.csv", reserve)
    balance = r58.panel_balance_rows(complete)
    r58.write_csv(r58.EVIDENCE / "round58_panel_balance_audit.csv", balance)
    r58.write_json(r58.EVIDENCE / "round58_panel_selection_protocol.json", {
        "schema": "round58-panel-selection-protocol-v1",
        "frozen_before_performance": True,
        "source_manifest": r58.repo_path(r58.T_SCENARIOS),
        "source_manifest_sha256": r58.sha256_file(r58.T_SCENARIOS),
        "source_scenario_count": 960, "selected_scenario_count": 50,
        "reserve_scenario_count": 910,
        "primary": {
            "count": 30, "cells": "V x geography x inventory",
            "replicate_rule": "lexicographically lower canonical landscape SHA-256",
            "factor_rule": "round58_fixed_balanced_cycle_v1",
            "M_bits_by_cell_position": [0, 1, 0, 1, 0, 1],
            "Q_bits_by_cell_position": [1, 0, 0, 0, 1, 1],
            "V_rotations": "M xor V_index%2; Q xor floor(V_index/2)%2; T=(cell_position+V_index)%4",
        },
        "matched_route_horizon": {
            "count": 20, "landscape_count": 10,
            "inventory_rule": "shortage/balanced/surplus rotation over V-major geography order",
            "replicate_rule": (
                "other replicate from the corresponding V/geography/inventory primary cell; "
                "the matched landscape itself is not selected in that primary cell"),
            "M": "lower available M", "Q": 30, "T_seconds": [3600, 18000],
        },
        "performance_or_visual_information_used": False,
        "replacement_allowed": False, "panel_adaptation_used": False,
        "reserve_label": "reserve_not_opened_round58",
    })

    order_rows = []
    for scenario_ordinal, row in enumerate(complete, start=1):
        for within_pair, method in enumerate((row["method_first"], row["method_second"]), start=1):
            order_rows.append({
                "scenario_ordinal": scenario_ordinal,
                "arm_ordinal": 2 * scenario_ordinal - 2 + within_pair,
                "scenario_id": row["scenario_id"],
                "scenario_sha256": row["scenario_sha256"],
                "first_hex_digit": row["scenario_sha256"][0],
                "first_hex_digit_even": int(row["scenario_sha256"][0], 16) % 2 == 0,
                "within_pair_order": within_pair, "method": method,
                "stage": "screen_3600", "cap_seconds": 3600,
            })
    r58.write_csv(r58.EVIDENCE / "execution_order_manifest.csv", order_rows)
    first_counts = Counter(row["method_first"] for row in complete)
    r58.write_csv(r58.EVIDENCE / "method_order_balance_audit.csv", [{
        "scenario_count": 50, "k1_first": first_counts["k1_am_sf"],
        "pgrb_first": first_counts["pgrb"],
        "deterministic_rule": "first scenario-SHA hex digit even => K1; odd => P-GRB",
        "every_scenario_has_both_screen_arms": True,
        "order_frozen_before_performance": True,
    }])
    r58.write_json(r58.EVIDENCE / "paired_solver_contract.json", {
        "schema": "round58-paired-solver-contract-v1",
        "shared": {"machine": platform.node(), "executable": "same frozen executable",
                   "Gurobi": "13.0.2", "Threads": 1, "Seed": 0,
                   "Presolve": "Auto", "MIPGap": 0.0, "MIPGapAbs": 0.0,
                   "PreCrush": "default", "fresh_process_per_run": True,
                   "one_optimizer_process_at_a_time": True},
        "k1_am_sf": {"method": "gcap-frontier", "preset": "paper-k1-am-sf",
                      "K0": 1, "split": "midpoint",
                      "score": "balanced normalized closure", "tau": 0.08,
                      "backend": "F0-CLEAN", "native_branching": True,
                      "dynamic_user_cuts": False},
        "pgrb": {"method": "gurobi", "plain_baseline": True,
                 "one_original_compact_MILP": True, "gini_decomposition": False,
                 "tailored_cuts": False, "custom_branching": False,
                 "HGA_or_imported_routes": False, "known_optimum_or_archive_bounds": False,
                 "strict_expected_model_fingerprint_required": True},
        "screen_cap_seconds": 3600, "screen_checkpoints_seconds": [300, 1200, 3600],
        "maximum_cap_seconds": 21600,
    })
    r58.write_json(r58.EVIDENCE / "gap_definition_contract.json", {
        "schema": "round58-gap-definition-contract-v1",
        "orientation": "minimization",
        "valid_lower_bound": "solver bound accepted only after method-specific scope/lifecycle checks",
        "verified_upper_bound": "objective of independently verified original-problem incumbent",
        "absolute_gap": "max(0, verified_upper_bound - valid_lower_bound)",
        "relative_gap": "absolute_gap / max(abs(verified_upper_bound), 1e-6)",
        "scaled_gap": "absolute_gap / max(1, abs(verified_upper_bound))",
        "missing_endpoint_policy": "all three computed gaps are unavailable",
        "ambiguous_field_name_gap_forbidden": True,
        "formulas_frozen_before_results": True,
    })

    freeze_inputs = [
        r58.EVIDENCE / "round58_panel_selection_protocol.json",
        r58.EVIDENCE / "round58_primary_panel.csv",
        r58.EVIDENCE / "round58_matched_T_panel.csv",
        r58.EVIDENCE / "round58_complete_panel.csv",
        r58.EVIDENCE / "round58_reserve_inventory.csv",
        r58.EVIDENCE / "round58_panel_balance_audit.csv",
        r58.EVIDENCE / "execution_order_manifest.csv",
        r58.EVIDENCE / "method_order_balance_audit.csv",
        r58.EVIDENCE / "paired_solver_contract.json",
        r58.EVIDENCE / "gap_definition_contract.json",
    ]
    r58.write_json(r58.EVIDENCE / "round58_panel_freeze_manifest.json", {
        "schema": "round58-panel-freeze-manifest-v1", "recorded_at_utc": now,
        "base_commit": head, "base_tree": tree,
        "dataset_family": r58.DATASET_FAMILY,
        "dataset_manifest_sha256": r58.sha256_file(r58.T_SCENARIOS),
        "performance_results_opened_before_freeze": False,
        "primary_count": 30, "matched_T_count": 20,
        "complete_count": 50, "reserve_count": 910,
        "algorithm_arms_before_extensions": 100,
        "panel_adaptation_used": False, "replacement_allowed": False,
        "files": [file_entry(path) for path in freeze_inputs],
    })
    print(json.dumps({
        "round57_qualified": True, "primary": len(primary),
        "matched_T": len(matched), "complete": len(complete),
        "reserve": len(reserve), "k1_first": first_counts["k1_am_sf"],
        "pgrb_first": first_counts["pgrb"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
