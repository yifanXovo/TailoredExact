#!/usr/bin/env python3
"""Cross-check Round 27 commands, ledgers, lifecycle, and package hashes."""

from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path
from typing import Any

import run_round27_experiments as frozen


OUT = frozen.OUT
RUNS = OUT / "runs"


def truth(value: Any) -> bool:
    return value is True or str(value).lower() in ("true", "1")


def result_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def rows(path: Path) -> list[dict[str, str]]:
    if path.is_file():
        with path.open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))
    compressed = Path(str(path) + ".gz")
    if compressed.is_file():
        with gzip.open(compressed, "rt", newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))
    return []


def main() -> int:
    findings: list[dict[str, Any]] = []
    failures = 0
    c2_dirs = sorted(RUNS.glob("stage[23]*__c2_paper__300s"))
    for run_dir in c2_dirs:
        command = frozen.load_json(run_dir / "command.json")
        state = frozen.load_json(run_dir / "run_state.json")
        command_line = command["command"]
        command_ok = (
            "--primal-heuristic-seconds" not in command_line and
            "--external-gini-split-after-attempts" not in command_line and
            command_line[command_line.index("--primal-heuristic-stop") + 1] ==
                "generation-stagnation" and
            command_line[command_line.index(
                "--primal-heuristic-no-improve-generations") + 1] == "2000" and
            command_line[command_line.index("--external-gini-scheduling") + 1] ==
                "paper-lp-event")
        checks: dict[str, Any] = {
            "command_uniform_and_paper_safe": command_ok,
            "sensitive_marker_scan_passed": state["sensitive_marker_scan_passed"],
        }
        result_path = run_dir / "result.json"
        if result_path.is_file():
            result = result_object(result_path)
            optimize = rows(run_dir / "external/paper_optimize_ledger.csv")
            lp_status = rows(run_dir / "external/lp_status_ledger.csv")
            split = rows(run_dir / "external/split_decision_ledger.csv")
            bounds = rows(run_dir / "external/parent_child_bound_ledger.csv")
            leaf = rows(run_dir / "external/paper_leaf_ledger.csv")
            lp_opt = [row for row in optimize if row["solve_kind"] == "LP"]
            mip_opt = [row for row in optimize if row["solve_kind"] == "MIP"]
            terminal_lp_status = all(
                truth(row["terminal_valid"]) and
                (truth(row["optimal"]) or truth(row["infeasible"]))
                for row in lp_status)
            checks.update({
                "optimize_ledger_matches_result": len(optimize) == int(
                    result["external_gini_tree_optimize_count"]),
                "LP_optimize_ledger_matches_result": len(lp_opt) == int(
                    result["external_gini_tree_lp_optimize_count"]),
                "MIP_optimize_ledger_matches_result": len(mip_opt) == int(
                    result["external_gini_tree_terminal_mip_optimize_count"]),
                "terminal_MIP_leaf_count_matches": len(mip_opt) == int(
                    result["external_gini_tree_terminal_mip_leaf_count"]),
                "terminal_MIP_leaf_ids_unique": len({row["leaf_id"] for row in mip_opt}) ==
                    len(mip_opt),
                "completed_LP_statuses_terminal_valid": terminal_lp_status,
                "LP_status_count_consistent": len(lp_status) <= len(lp_opt) and
                    len(lp_opt) - len(lp_status) <= int(
                        result["external_gini_tree_global_deadline_interruption_count"]),
                "split_bound_ledgers_consistent": len(bounds) == sum(
                    truth(row["eligible"]) for row in split),
                "coverage_valid": result["external_gini_tree_root_coverage_valid"] and
                    result["external_gini_tree_parent_child_coverage_valid"],
                "bounds_valid_and_monotone": result[
                    "external_gini_tree_all_leaf_bounds_valid"] and result[
                    "external_gini_tree_global_bound_monotone"] and result[
                    "external_gini_tree_leaf_bounds_monotone"],
                "lifecycle_complete": result["external_gini_tree_lifecycle_complete"],
                "model_release_symmetric": result["external_gini_tree_model_count"] ==
                    result["external_gini_tree_model_free_count"],
                "environment_release_symmetric": result[
                    "external_gini_tree_environment_count"] == result[
                    "external_gini_tree_environment_free_count"],
                "no_restart_or_attempt_scheduling": all(int(result[name]) == 0 for name in (
                    "external_gini_tree_same_leaf_resume_count",
                    "external_gini_tree_fresh_restart_count",
                    "external_gini_tree_child_restart_count",
                    "external_gini_tree_attempt_count")),
                "leaf_ledger_present": bool(leaf),
            })
        else:
            checks.update({
                "failed_row_retained": state["return_code"] == 124 and
                    state["emergency_timeout"] and not state["result_exists"],
                "HGA_trajectory_retained": (run_dir / "hga_generations.csv").is_file() or
                    Path(str(run_dir / "hga_generations.csv") + ".gz").is_file(),
                "no_partial_result_claim": not result_path.exists(),
            })
        passed = all(bool(value) for value in checks.values())
        failures += not passed
        findings.append({
            "run_id": run_dir.name, "result_exists": result_path.is_file(),
            "check_count": len(checks), "passed": passed,
            "failed_checks": "|".join(key for key, value in checks.items() if not value),
        })

    compression = rows(OUT / "compression_manifest.csv")
    compression_ok = all(
        row["original_sha256"] == row["restoration_sha256"] and
        row["original_bytes"] == row["restoration_bytes"] and
        (frozen.ROOT / row["compressed_path"]).is_file()
        for row in compression)
    failures += not compression_ok
    with (OUT / "ledger_consistency_audit.csv").open(
            "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(findings[0]))
        writer.writeheader()
        writer.writerows(findings)
    frozen.json_write(OUT / "evidence_integrity_audit.json", {
        "schema": "round27-evidence-integrity-v1", "passed": failures == 0,
        "C2_rows_checked": len(findings), "C2_row_failures": failures,
        "compression_records": len(compression),
        "compression_restoration_metadata_and_targets_valid": compression_ok,
        "all_official_run_states_sensitive_marker_clean": all(
            frozen.load_json(path)["sensitive_marker_scan_passed"]
            for path in RUNS.glob("stage[123]*/run_state.json")),
        "failed_V50_row_retained_without_retry": len(
            list(RUNS.glob("stage3__moderate_seed6301__c2_paper__300s"))) == 1,
    })
    print(f"Round27 evidence audit rows={len(findings)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
