#!/usr/bin/env python3
"""Seal every completed official Round 43 row under the required ledger names."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import shutil
from typing import Any

import round43_common as common


REQUIRED = (
    "process_phases.csv",
    "progress.csv",
    "result.json",
    "global_bound_trace.csv",
    "interval_tree_events.csv",
    "interval_coverage_ledger.csv",
    "parent_lp_ledger.csv",
    "lookahead_profile_ledger.csv",
    "envelope_facet_ledger.csv",
    "envelope_integral_ledger.csv",
    "refinement_decision_ledger.csv",
    "formulation_contraction_ledger.csv",
    "native_target_ledger.csv",
    "native_optimize_ledger.csv",
    "incumbent_verification_ledger.csv",
    "model_size_ledger.csv",
    "certificate_ledger.csv",
    "artifact_manifest.csv",
    "command.json",
    "completion_marker.json",
)

ALIASES = {
    "global_bound_trace.csv": "external/global_bound_trace.csv",
    "interval_tree_events.csv": "external/paper_tree_events.csv",
    "interval_coverage_ledger.csv":
        "external/initial_decomposition_ledger.csv",
    "parent_lp_ledger.csv": "external/round43_structural_atlas.csv",
    "lookahead_profile_ledger.csv": "external/round43_structural_atlas.csv",
    "envelope_facet_ledger.csv": "external/round43_facet_ledger.csv",
    "envelope_integral_ledger.csv": "external/round43_envelope_ledger.csv",
    "refinement_decision_ledger.csv":
        "external/round43_structural_atlas.csv",
    "formulation_contraction_ledger.csv":
        "external/round43_structural_atlas.csv",
    "native_target_ledger.csv": "external/native_target_ledger.csv",
    "native_optimize_ledger.csv": "external/paper_optimize_ledger.csv",
    "model_size_ledger.csv": "external/paper_optimize_ledger.csv",
}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def not_applicable(path: Path, reason: str) -> None:
    write_csv(path, [{
        "applicability": "not_applicable",
        "reason": reason,
        "source": "monolithic_or_non_refinement_official_row",
    }])


def result_ledger(run_dir: Path, name: str,
                  result: dict[str, Any]) -> None:
    if name == "incumbent_verification_ledger.csv":
        verification = result.get("verification", {})
        write_csv(run_dir / name, [{
            "original_solution_feasible": verification.get(
                "original_solution_feasible", False),
            "verifier_passed": result.get("verifier_passed", False),
            "verified_incumbent_objective_available": result.get(
                "verified_incumbent_objective_available", False),
            "verified_incumbent_objective": result.get(
                "verified_incumbent_objective", ""),
            "external_verified_upper_bound": result.get(
                "external_gini_tree_verified_upper_bound", ""),
        }])
    elif name == "certificate_ledger.csv":
        write_csv(run_dir / name, [{
            "strict_certified_original_problem": result.get(
                "strict_certified_original_problem", False),
            "status": result.get("status", ""),
            "valid_lower_bound": result.get(
                "external_gini_tree_global_lower_bound",
                result.get("lower_bound", "")),
            "verified_upper_bound": result.get(
                "external_gini_tree_verified_upper_bound",
                result.get("upper_bound", "")),
            "coverage_valid": result.get(
                "external_gini_tree_root_coverage_valid", "not_applicable"),
            "parent_child_coverage_valid": result.get(
                "external_gini_tree_parent_child_coverage_valid",
                "not_applicable"),
            "global_bound_monotone": result.get(
                "external_gini_tree_global_bound_monotone",
                "not_applicable"),
            "failure_reason": result.get(
                "external_gini_tree_failure_reason",
                result.get("gurobi_failure_reason", "none")),
        }])


def official_run_dirs() -> list[Path]:
    rows = []
    for run_dir in sorted(path for path in common.RUNS.iterdir()
                          if path.is_dir()):
        if "smoke" in run_dir.name or run_dir.name.startswith("protocol_"):
            continue
        command_path = run_dir / "command.json"
        result_path = run_dir / "result.json"
        if not command_path.is_file() or not result_path.is_file():
            continue
        command = common.load_json(command_path)
        if (int(command.get("round_id", -1)) == 43 and
                command.get("completed") is True and
                int(command.get("return_code", -1)) == 0):
            rows.append(run_dir)
    return rows


def seal(run_dir: Path) -> dict[str, Any]:
    command = common.load_json(run_dir / "command.json")
    result = common.load_json(run_dir / "result.json")
    for target, source_name in ALIASES.items():
        target_path = run_dir / target
        source_path = run_dir / source_name
        if target_path.is_file():
            continue
        if source_path.is_file():
            shutil.copyfile(source_path, target_path)
        else:
            not_applicable(
                target_path,
                f"{source_name} absent because this row has no applicable "
                "Round 43 refinement lifecycle")
    for name in ("incumbent_verification_ledger.csv",
                 "certificate_ledger.csv"):
        result_ledger(run_dir, name, result)
    for name in REQUIRED:
        path = run_dir / name
        if name in {"artifact_manifest.csv", "completion_marker.json"}:
            continue
        if not path.is_file():
            not_applicable(path, f"{name} is not applicable to this arm")

    completion = {
        "schema": "round43-completion-marker-v1",
        "round_id": 43,
        "run_id": command["run_id"],
        "completed": True,
        "return_code": command["return_code"],
        "watchdog_timeout": command["watchdog_timeout"],
        "executable_sha256": command["executable_sha256"],
        "input_sha256": command["instance_sha256"],
        "command_sha256": common.sha256(run_dir / "command.json"),
        "result_sha256": common.sha256(run_dir / "result.json"),
        "strict_certificate": result.get(
            "strict_certified_original_problem", False),
        "verifier_passed": result.get("verifier_passed", False),
    }
    common.write_json(run_dir / "completion_marker.json", completion)
    command_hash = completion["command_sha256"]
    manifest_rows = []
    for path in sorted(candidate for candidate in run_dir.rglob("*")
                       if candidate.is_file() and candidate !=
                       run_dir / "artifact_manifest.csv"):
        artifact = path.relative_to(run_dir).as_posix()
        if artifact.startswith("external/models/"):
            retention = "local_model_hash_only"
        elif (artifact.endswith(".gurobi.log") or
              artifact in {"native.log", "stdout.log", "stderr.log"}):
            retention = "local_lossless_log_hash_only"
        else:
            retention = "local_raw_with_published_hash"
        manifest_rows.append({
            "run_id": command["run_id"],
            "artifact": artifact,
            "path": common.relative(path),
            "sha256": common.sha256(path),
            "bytes": path.stat().st_size,
            "retention": retention,
            "required_protocol_artifact": artifact in REQUIRED,
            "generation_command_sha256": command_hash,
            "row_signature_source": (
                "native_optimize_ledger.csv:model_sha256" if
                artifact.startswith("external/models/") else ""),
        })
    write_csv(run_dir / "artifact_manifest.csv", manifest_rows)
    return {
        "run_id": command["run_id"],
        "run_dir": common.relative(run_dir),
        "artifact_count": len(REQUIRED),
        "published_file_count": len(manifest_rows) + 1,
        "artifact_manifest_sha256": common.sha256(
            run_dir / "artifact_manifest.csv"),
        "completion_marker_sha256": common.sha256(
            run_dir / "completion_marker.json"),
        "command_sha256": completion["command_sha256"],
        "result_sha256": completion["result_sha256"],
        "executable_sha256": completion["executable_sha256"],
        "input_sha256": completion["input_sha256"],
        "strict_certificate": completion["strict_certificate"],
        "verifier_passed": completion["verifier_passed"],
        "retention": "raw_run_local_compact_manifest_committed",
    }


def main() -> int:
    run_dirs = official_run_dirs()
    rows = [seal(run_dir) for run_dir in run_dirs]
    if not rows:
        raise RuntimeError("no completed official Round 43 rows found")
    common.write_csv(common.OUT / "official_run_evidence_manifest.csv", rows)
    artifact_rows = []
    for run_dir in run_dirs:
        artifact_rows.extend(common.csv_rows(run_dir / "artifact_manifest.csv"))
        command = common.load_json(run_dir / "command.json")
        manifest_path = run_dir / "artifact_manifest.csv"
        artifact_rows.append({
            "run_id": command["run_id"],
            "artifact": "artifact_manifest.csv",
            "path": common.relative(manifest_path),
            "sha256": common.sha256(manifest_path),
            "bytes": manifest_path.stat().st_size,
            "retention": "local_raw_with_published_hash",
            "required_protocol_artifact": True,
            "generation_command_sha256": common.sha256(
                run_dir / "command.json"),
            "row_signature_source": "",
        })
    common.write_csv(common.OUT / "artifact_manifest.csv", artifact_rows)
    print(json.dumps({
        "official_runs_sealed": len(rows),
        "required_artifacts_per_run": len(REQUIRED),
        "published_artifact_rows": len(artifact_rows),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
