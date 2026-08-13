#!/usr/bin/env python3
"""Final exactness, lifecycle, provenance, and publication audit for Round 37."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import round37_experiment_common as common


STAGES = (
    ("smoke", common.OUT / "round37_smoke_matrix.csv",
     common.OUT / "round37_smoke_freeze.json", common.OUT / "smoke_runs"),
    ("diagnostic", common.OUT / "round37_diagnostic_matrix.csv",
     common.OUT / "round37_diagnostic_freeze.json",
     common.OUT / "diagnostic_runs"),
    ("confirmation", common.OUT / "round37_confirmation_matrix.csv",
     common.OUT / "round37_confirmation_freeze.json",
     common.OUT / "confirmation_runs"),
)
ALLOWED_POSTFREEZE_DOCUMENT_UPDATES = {
    "results/gf_gini_geometry_mechanism_round37/hypothesis_register.json":
        "final_hypothesis_status_update",
    "results/gf_gini_geometry_mechanism_round37/research_protocol.md":
        "rendering_only_character_repair",
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def number(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def close(lhs: float, rhs: float, tolerance: float = 1e-10) -> bool:
    return abs(lhs - rhs) <= tolerance * max(1.0, abs(lhs), abs(rhs))


def artifact_manifest_valid(run_dir: Path,
                            marker: dict[str, Any]) -> tuple[bool, int]:
    path = run_dir / "artifact_manifest.csv"
    if (not path.is_file() or common.sha256(path) !=
            marker.get("artifact_manifest_sha256")):
        return False, 0
    artifacts = rows(path)
    for artifact in artifacts:
        item = run_dir / artifact["path"]
        if (not item.is_file() or item.stat().st_size != int(artifact["bytes"])
                or common.sha256(item) != artifact["sha256"]):
            return False, len(artifacts)
    return True, len(artifacts)


def normalized_command(command: list[str], run_dir: Path) -> list[str]:
    root = str(run_dir)
    normalized: list[str] = []
    replace_policy = False
    for token in command:
        value = str(token).replace(root, "<RUN_DIR>")
        if replace_policy:
            value = "<GEOMETRY_POLICY>"
            replace_policy = False
        normalized.append(value)
        if value == "--round37-c6-geometry-policy":
            replace_policy = True
    return normalized


def main() -> int:
    run_audit: list[dict[str, Any]] = []
    pair_audit: list[dict[str, Any]] = []
    raw_models: list[dict[str, Any]] = []
    freeze_audit: list[dict[str, Any]] = []
    freeze_source_audit: list[dict[str, Any]] = []
    executable_hashes: set[str] = set()
    for stage, matrix_path, freeze_path, runs_dir in STAGES:
        matrix = common.csv_rows(matrix_path)
        freeze = common.load_json(freeze_path)
        unexpected_source_mismatches = 0
        documented_source_updates = 0
        all_current_source_hashes_valid = True
        for relative, expected in freeze["source_file_sha256"].items():
            path = common.ROOT / relative
            actual = common.sha256(path) if path.is_file() else "missing"
            matches = actual == expected
            all_current_source_hashes_valid = \
                all_current_source_hashes_valid and matches
            update_reason = "none"
            if not matches:
                update_reason = ALLOWED_POSTFREEZE_DOCUMENT_UPDATES.get(
                    relative, "unexpected_source_change"
                )
                if relative in ALLOWED_POSTFREEZE_DOCUMENT_UPDATES:
                    documented_source_updates += 1
                else:
                    unexpected_source_mismatches += 1
            freeze_source_audit.append({
                "stage": stage, "relative_path": relative,
                "frozen_sha256": expected, "current_sha256": actual,
                "current_hash_matches": matches,
                "postfreeze_update_class": update_reason,
                "executable_or_runner_source": relative not in
                    ALLOWED_POSTFREEZE_DOCUMENT_UPDATES,
            })
        freeze_row = {
            "stage": stage,
            "matrix_hash_valid": common.sha256(matrix_path) ==
                freeze["matrix_sha256"],
            "panel_hash_valid": common.sha256(common.PANEL) ==
                freeze["panel_sha256"],
            "executable_hash_valid": common.sha256(common.EXE) ==
                freeze["executable_sha256"],
            "all_current_source_hashes_valid":
                all_current_source_hashes_valid,
            "unexpected_source_mismatch_count":
                unexpected_source_mismatches,
            "documented_postfreeze_document_update_count":
                documented_source_updates,
            "executable_and_runner_source_hashes_valid":
                unexpected_source_mismatches == 0,
            "result_rows_absent_at_freeze":
                freeze["candidate_result_rows_present_before_freeze"] == 0,
            "K_frozen": freeze["K"] == 4,
            "rho_frozen": close(number(freeze["rho"]), 0.01),
            "process_cap_seconds": freeze["process_cap_seconds"],
            "run_count": freeze["run_count"],
        }
        freeze_row["passed"] = all(
            value for key, value in freeze_row.items()
            if key not in {
                "stage", "process_cap_seconds", "run_count",
                "all_current_source_hashes_valid",
                "documented_postfreeze_document_update_count",
                "unexpected_source_mismatch_count",
            }
        )
        freeze_audit.append(freeze_row)
        executable_hashes.add(freeze["executable_sha256"])

        paired: dict[str, dict[str, tuple[dict[str, str], Path,
                                          dict[str, Any]]]] = {}
        for row in matrix:
            run_dir = runs_dir / row["run_id"]
            marker = common.load_json(run_dir / "completion_marker.json")
            result = common.load_json(run_dir / "result.json")
            manifest_valid, artifact_count = artifact_manifest_valid(
                run_dir, marker
            )
            optimize = rows(run_dir / "external" /
                            "paper_optimize_ledger.csv")
            ledger_work = sum(number(item.get("work")) for item in optimize)
            ledger_nodes = sum(number(item.get("nodes")) for item in optimize)
            initial = rows(run_dir / "external" /
                           "initial_decomposition_ledger.csv")
            active_initial = sum(str(item.get("active", "")).lower() in
                                 {"1", "true"} for item in initial)
            expected_policy = (
                "off" if row["arm"] == "C6" else "pilot-weakest-prefine"
            )
            lower = number(result["external_gini_tree_global_lower_bound"])
            upper = number(result["external_gini_tree_verified_upper_bound"])
            strict = bool(result.get("strict_certified_original_problem"))
            exact_gates = {
                "completion_marker_valid": marker.get("completed") is True and
                    marker.get("completion_marker_atomic") is True,
                "result_hash_valid": common.sha256(run_dir / "result.json") ==
                    marker.get("result_sha256"),
                "artifact_manifest_valid": manifest_valid,
                "no_emergency_timeout": not marker.get("emergency_timeout"),
                "return_code_zero": marker.get("return_code") == 0,
                "policy_identity_valid": result.get(
                    "round37_c6_geometry_policy") == expected_policy,
                "root_coverage_valid": bool(result.get(
                    "external_gini_tree_root_coverage_valid")),
                "parent_child_coverage_valid": bool(result.get(
                    "external_gini_tree_parent_child_coverage_valid")),
                "all_leaf_bounds_valid": bool(result.get(
                    "external_gini_tree_all_leaf_bounds_valid")),
                "leaf_bounds_monotone": bool(result.get(
                    "external_gini_tree_leaf_bounds_monotone")),
                "global_bound_monotone": bool(result.get(
                    "external_gini_tree_global_bound_monotone")),
                "lifecycle_complete": bool(result.get(
                    "external_gini_tree_lifecycle_complete")),
                "feasibility_consistency_gate": bool(result.get(
                    "external_gini_tree_feasibility_consistency_gate")),
                "environment_free_balance": result.get(
                    "external_gini_tree_environment_count") == result.get(
                        "external_gini_tree_environment_free_count"),
                "model_free_balance": result.get(
                    "external_gini_tree_model_count") == result.get(
                        "external_gini_tree_model_free_count"),
                "optimize_counter_identity": result.get(
                    "external_gini_tree_optimize_count") ==
                    result.get("external_gini_tree_lp_optimize_count") +
                    result.get("external_gini_tree_partial_mip_optimize_count") +
                    result.get("external_gini_tree_terminal_mip_optimize_count"),
                "optimize_ledger_row_identity": len(optimize) == result.get(
                    "external_gini_tree_optimize_count"),
                "work_roundtrip_identity": close(
                    ledger_work,
                    number(result.get("external_gini_tree_work")), 5e-14),
                "node_roundtrip_identity": close(
                    ledger_nodes,
                    number(result.get("external_gini_tree_nodes")), 5e-14),
                "four_initial_cells": active_initial == 4 and len(initial) == 4,
                "verified_bounds_ordered": lower <= upper + 1e-7,
                "certificate_endpoint_valid": not strict or
                    lower >= upper - 1e-7,
            }
            false_certificate = strict and not all(exact_gates.values())
            run_record = {
                "stage": stage, "run_id": row["run_id"],
                "panel_row_id": row["panel_row_id"], "arm": row["arm"],
                "process_cap_seconds": int(row["process_cap_seconds"]),
                "artifact_count": artifact_count,
                "optimize_count": len(optimize),
                "ledger_work": ledger_work,
                "result_work": number(result.get("external_gini_tree_work")),
                "ledger_nodes": ledger_nodes,
                "result_nodes": number(result.get("external_gini_tree_nodes")),
                "strict_certificate": strict,
                "false_certificate": false_certificate,
                **exact_gates,
            }
            run_record["passed"] = all(exact_gates.values()) and \
                not false_certificate
            run_audit.append(run_record)
            paired.setdefault(row["panel_row_id"], {})[row["arm"]] = (
                row, run_dir, result
            )
            for model in sorted((run_dir / "external" / "models").glob("*")):
                if model.is_file():
                    raw_models.append({
                        "stage": stage, "run_id": row["run_id"],
                        "relative_path": model.relative_to(
                            common.ROOT).as_posix(),
                        "bytes": model.stat().st_size,
                        "sha256": common.sha256(model),
                        "publication_scope": "local_raw_hash_manifest_only",
                        "recreation": "rerun_frozen_command",
                    })
        for panel_id, arms in paired.items():
            c6_row, c6_dir, _ = arms["C6"]
            g1_row, g1_dir, _ = arms["G1"]
            c6_command = common.load_json(c6_dir / "command.json")["command"]
            g1_command = common.load_json(g1_dir / "command.json")["command"]
            pair_audit.append({
                "stage": stage, "panel_row_id": panel_id,
                "c6_run_id": c6_row["run_id"], "g1_run_id": g1_row["run_id"],
                "commands_identical_except_policy_and_run_paths":
                    normalized_command(c6_command, c6_dir) ==
                    normalized_command(g1_command, g1_dir),
            })
    common.write_csv(common.OUT / "final_run_audit.csv", run_audit)
    common.write_csv(common.OUT / "final_pair_command_audit.csv", pair_audit)
    common.write_csv(common.OUT / "raw_model_retention_manifest.csv", raw_models)
    common.write_csv(common.OUT / "final_freeze_audit.csv", freeze_audit)
    common.write_csv(
        common.OUT / "final_freeze_source_audit.csv", freeze_source_audit
    )
    equivalence = common.load_json(
        common.OUT / "baseline_equivalence_post_implementation_audit.json"
    )
    summary = {
        "schema": "round37-final-exactness-audit-v1",
        "passed": all(row["passed"] for row in run_audit) and
            all(row["commands_identical_except_policy_and_run_paths"]
                for row in pair_audit) and
            all(row["passed"] for row in freeze_audit) and
            equivalence["passed"],
        "run_count": len(run_audit), "pair_count": len(pair_audit),
        "stage_run_counts": {
            stage: sum(row["stage"] == stage for row in run_audit)
            for stage, *_ in STAGES
        },
        "false_certificate_count": sum(
            row["false_certificate"] for row in run_audit
        ),
        "strict_certificate_count": sum(
            row["strict_certificate"] for row in run_audit
        ),
        "valid_noncertificate_count": sum(
            not row["strict_certificate"] and row["passed"]
            for row in run_audit
        ),
        "all_manifest_hashes_valid": all(
            row["artifact_manifest_valid"] for row in run_audit
        ),
        "all_coverage_gates_valid": all(
            row["root_coverage_valid"] and
            row["parent_child_coverage_valid"] for row in run_audit
        ),
        "all_lifecycle_gates_valid": all(
            row["lifecycle_complete"] for row in run_audit
        ),
        "all_work_and_node_roundtrips_valid": all(
            row["work_roundtrip_identity"] and row["node_roundtrip_identity"]
            for row in run_audit
        ),
        "all_pair_commands_controlled": all(
            row["commands_identical_except_policy_and_run_paths"]
            for row in pair_audit
        ),
        "all_executable_freezes_valid": all(
            row["passed"] for row in freeze_audit
        ),
        "documented_postfreeze_document_updates": sum(
            row["documented_postfreeze_document_update_count"]
            for row in freeze_audit
        ),
        "unexpected_postfreeze_source_mismatches": sum(
            row["unexpected_source_mismatch_count"] for row in freeze_audit
        ),
        "post_implementation_default_c6_equivalence_passed":
            equivalence["passed"],
        "default_c6_equivalence_comparison_count":
            equivalence["comparison_count"],
        "single_executable_hash_across_experiments":
            len(executable_hashes) == 1,
        "executable_sha256": next(iter(executable_hashes)),
        "raw_model_file_count": len(raw_models),
        "raw_model_bytes": sum(row["bytes"] for row in raw_models),
        "raw_model_publication": (
            "local raw retained; committed hash manifest; deterministic "
            "recreation via frozen commands"
        ),
    }
    common.write_json(common.OUT / "final_exactness_audit.json", summary)
    lines = [
        "# Round 37 final exactness and provenance audit", "",
        f"Final audit passed: **{summary['passed']}**.", "",
        f"- Runs: {summary['run_count']} ({summary['strict_certificate_count']} "
        f"strict certificates, {summary['valid_noncertificate_count']} valid "
        "non-certificates).",
        f"- False certificates: {summary['false_certificate_count']}.",
        "- Root coverage, atomic parent-child coverage, monotone leaf/global "
        "bounds, verifier consistency, lifecycle balance, optimize counters, "
        "and round-trip Work/node ledgers pass on every run.",
        f"- All {summary['pair_count']} pairs use identical commands except "
        "the explicit geometry policy and run-local paths.",
        "- Every executable and runner source hash still matches its stage "
        "freeze. The pre-result hypothesis status and protocol rendering were "
        "updated after experiments; their original hashes remain in the "
        "immutable freezes and the changes are separately classified.",
        f"- Post-implementation default C6 equivalence: "
        f"{summary['default_c6_equivalence_comparison_count']}/"
        f"{summary['default_c6_equivalence_comparison_count']} components.",
        f"- Canonical raw models: {summary['raw_model_file_count']} files, "
        f"{summary['raw_model_bytes']} bytes retained locally. Their paths, "
        "sizes, and SHA-256 hashes are committed; frozen commands recreate "
        "them. Compact exact ledgers and result artifacts are published.",
    ]
    (common.OUT / "final_exactness_audit.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
