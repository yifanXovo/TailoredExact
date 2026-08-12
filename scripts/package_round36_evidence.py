#!/usr/bin/env python3
"""Create the compact, auditable Round 36 final evidence bundle.

All 56 Stage B and 47 Stage C raw run directories remain local and
checksum-addressed by their completion markers. This script packages all four
Stage B arms for one deterministic representative per frozen Round-35 pattern,
plus compact all-row Stage C identities and comparisons, retaining the ledgers
needed to audit the claims without committing model dumps or redundant logs.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
import os
import shutil
from pathlib import Path
from typing import Any, Iterable

import analyze_round36 as analysis
import round36_common as common
import round36_stage_c_common as stage_c
import run_round36_stage_c as stage_c_runner


RAW_FILES = (
    "result.json",
    "completion_marker.json",
    "artifact_manifest.csv",
    "heuristic_candidates.csv",
    "process_phases.csv",
    "external/initial_decomposition_ledger.csv",
    "external/global_bound_trace.csv",
    "external/lp_status_ledger.csv",
    "external/native_target_ledger.csv",
    "external/paper_leaf_ledger.csv",
    "external/paper_optimize_ledger.csv",
    "external/paper_tree_events.csv",
    "external/parent_child_bound_ledger.csv",
    "external/split_decision_ledger.csv",
)
SENSITIVE = (
    b"grb_license_file", b"gurobi.lic", b"licenseid",
    b"wlsaccessid", b"wlssecret", b"tokenserver",
)
FINAL_DERIVED = (
    "round36_protocol.md",
    "frozen_causal_panel.csv",
    "frozen_causal_panel.json",
    "source_of_truth.md",
    "theory_and_mechanism_note.md",
    "analysis_gate_definition.md",
    "round36_official_matrix.csv",
    "round36_command_freeze.json",
    "round36_frozen_manifest.json",
    "official_start_record.json",
    "stage_a_build_and_tests.csv",
    "stage_a_build_and_tests.json",
    "stage_a_build_and_tests.md",
    "baseline_equivalence_audit.csv",
    "baseline_equivalence_audit.json",
    "baseline_equivalence_audit.md",
    "github_pr_record.json",
    "semantic_separation_audit.csv",
    "semantic_separation_audit.json",
    "semantic_separation_audit.md",
    "verified_ub_assignment_audit.csv",
    "anchor_consumer_occurrence_audit.csv",
    "per_arm_results.csv",
    "initial_decomposition_audit.csv",
    "exactness_certificate_audit.csv",
    "interaction_sequence_hashes.csv",
    "trajectory_events.csv",
    "child_lookahead_split_audit.csv",
    "native_target_audit.csv",
    "terminal_closure_audit.csv",
    "causal_geometry_comparison.csv",
    "causal_normalization_comparison.csv",
    "fixed_anchor_proof_comparison.csv",
    "causal_group_summaries.csv",
    "representative_trajectory_report.md",
    "final_audit_decision.json",
    "final_report.md",
    "runner_row_summary.csv",
    "stage_c_candidate_definition.json",
    "stage_c_contract_fix_audit.csv",
    "stage_c_contract_fix_audit.json",
    "stage_c_contract_fix_audit.md",
    "stage_c_invalidated_attempt_1_contract_bug.json",
    "stage_c_invalidated_attempt_1_contract_bug.md",
    "stage_c_validation_matrix.csv",
    "stage_c_command_freeze.json",
    "stage_c_frozen_manifest.json",
    "stage_c_start_record.json",
    "stage_c_runner_row_summary.csv",
    "stage_c_per_run_results.csv",
    "stage_c_comparisons.csv",
    "stage_c_group_summaries.csv",
    "stage_c_final_audit.json",
    "stage_c_final_report.md",
)
COMPRESSED_DERIVED = {
    "trajectory_events.csv": "trajectory_events.csv.gz",
}
MAX_REPOSITORY_ARTIFACT_BYTES = 95 * 1024 * 1024


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    material = list(rows)
    if not material:
        raise RuntimeError(f"refusing empty evidence table: {path}")
    fields: list[str] = []
    for row in material:
        for field in row:
            if field not in fields:
                fields.append(field)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def write_text(path: Path, value: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def number(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def final_exactness_valid(path: Path) -> bool:
    if not path.is_file():
        return False
    rows = csv_rows(path)
    lifecycle_fields = (
        "runner_normal_exit", "runner_no_emergency_timeout",
        "result_json_verified_after_process_exit",
        "runner_required_artifacts_complete",
        "atomic_completion_marker_valid",
        "algorithmic_solve_state_not_resumed", "runner_lifecycle_valid",
        "certificate_or_graceful_deadline_endpoint_valid", "finite_bounds",
    )
    return (
        len(rows) == 56
        and len({row.get("run_id") for row in rows}) == 56
        and all(truth(row.get("exactness_certificate_audit_passed"))
                and not truth(row.get("false_certificate"))
                and all(truth(row.get(field)) for field in lifecycle_fields)
                for row in rows)
    )


def validate_official_rows(matrix: list[dict[str, str]],
                           manifest: dict[str, Any],
                           items: dict[str, dict[str, Any]]) -> None:
    for row in matrix:
        directory = common.RUNS / row["run_id"]
        valid, reason = analysis.artifact_complete(
            directory, row, items[row["instance_id"]], manifest)
        if not valid:
            raise RuntimeError(
                f"official row failed checksum revalidation: "
                f"{row['run_id']}:{reason}")


def sensitive(path: Path) -> str:
    data = path.read_bytes().lower()
    return next((marker.decode() for marker in SENSITIVE if marker in data), "")


def gzip_deterministic(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    with source.open("rb") as input_stream, temporary.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw,
                           compresslevel=9, mtime=0) as output_stream:
            shutil.copyfileobj(input_stream, output_stream,
                               length=1024 * 1024)
        raw.flush()
        os.fsync(raw.fileno())
    temporary.replace(target)


def require_repository_artifact_size(path: Path) -> None:
    size = path.stat().st_size
    if size > MAX_REPOSITORY_ARTIFACT_BYTES:
        raise RuntimeError(
            f"repository artifact exceeds 95 MiB preflight: {path}:{size}")


def representatives() -> list[dict[str, str]]:
    rows = csv_rows(common.OUT / "causal_geometry_comparison.csv")
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(row["round35_pattern"], []).append(row)
    selected = []
    for pattern, candidates in sorted(groups.items()):
        chosen = max(candidates, key=lambda row: (
            abs(number(row.get("right_minus_left_proof_auc"))),
            -int(row["V"]), row["instance_id"]))
        selected.append({
            "round35_pattern": pattern,
            "panel_row_id": chosen["panel_row_id"],
            "instance_id": chosen["instance_id"],
            "selection_rule":
                "largest_absolute_HH_vs_BW-P_common_window_proof_AUC_delta",
            "absolute_geometry_proof_auc_delta": abs(number(
                chosen.get("right_minus_left_proof_auc"))),
        })
    if not selected:
        raise RuntimeError("no representative causal rows")
    return selected


def validate_final() -> dict[str, Any]:
    decision_path = common.OUT / "final_audit_decision.json"
    if not decision_path.is_file():
        raise RuntimeError("final analysis is missing")
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    if decision.get("completed_official_rows") != 56:
        raise RuntimeError("Round 36 is not 56/56 complete")
    if decision.get("false_certificate_count") != 0 or not decision.get(
            "all_exactness_certificate_audits_passed"):
        raise RuntimeError("final correctness gate is not green")
    allowed = {
        "decomposition_geometry_dominant",
        "split_normalization_coupling_dominant", "both_effects_matter",
        "neither_isolated_effect_sufficient",
    }
    if (decision.get("classification") not in allowed
            or decision.get("automatic_promotion_performed") is not False
            or decision.get("validated_gurobi_mainline") != "C6-HGA-FULL"):
        raise RuntimeError("final classification or mainline contract is invalid")
    for name in FINAL_DERIVED:
        if not (common.OUT / name).is_file():
            raise RuntimeError(f"required final artifact missing: {name}")
    if not final_exactness_valid(common.OUT / "exactness_certificate_audit.csv"):
        raise RuntimeError("final lifecycle/exactness table is not 56-row green")
    matrix = common.csv_rows(common.OFFICIAL_MATRIX)
    if len(matrix) != 56:
        raise RuntimeError("official matrix is not 56 rows")
    validate_official_rows(matrix, common.load_json(common.FROZEN_MANIFEST),
                           common.inventory())
    stage_c_decision = common.load_json(stage_c.FINAL_AUDIT)
    stage_c_manifest = common.load_json(stage_c.FROZEN_MANIFEST)
    stage_c_candidate = common.load_json(stage_c.CANDIDATE)
    contract_fix = common.load_json(stage_c.CONTRACT_FIX_AUDIT)
    invalidated_attempt = common.load_json(
        stage_c.INVALIDATED_ATTEMPT_RECORD)
    stage_b_manifest = common.load_json(common.FROZEN_MANIFEST)
    frozen_stage_c_artifacts = (
        (stage_c.CANDIDATE, "candidate_definition_sha256"),
        (stage_c.MATRIX, "validation_matrix_sha256"),
        (stage_c.COMMAND_FREEZE, "command_freeze_sha256"),
    )
    if any(not path.is_file() or sha256(path) != stage_c_manifest[key]
           for path, key in frozen_stage_c_artifacts):
        raise RuntimeError("Stage C frozen artifact identity changed")
    if any(not (common.ROOT / relative).is_file() or
               sha256(common.ROOT / relative) != expected
               for relative, expected in
               stage_c_manifest["source_file_sha256"].items()):
        raise RuntimeError("Stage C frozen source identity changed")
    if not (
            contract_fix.get("passed") is True
            and contract_fix.get("stage_b_executable_unchanged") is True
            and contract_fix.get("executables_are_distinct") is True
            and contract_fix.get("baseline_equivalence", {}).get(
                "all_identical") is True
            and invalidated_attempt.get("invalidated") is True
            and invalidated_attempt.get("completed_valid_rows") == 18
            and invalidated_attempt.get("failed_serial_order") == 19
            and invalidated_attempt.get("row_reuse_permitted") is False
            and sha256(stage_c.CONTRACT_FIX_AUDIT) ==
                stage_c_manifest["contract_fix_audit_sha256"]
            and sha256(stage_c.INVALIDATED_ATTEMPT_RECORD) ==
                stage_c_manifest["invalidated_attempt_record_sha256"]
            and stage_c_candidate.get("stage_b_executable_sha256") ==
                stage_b_manifest["gurobi_executable_sha256"]
            and stage_c_candidate.get("stage_c_executable_sha256") ==
                stage_c_manifest["gurobi_executable_sha256"]
            and sha256(stage_c.STAGE_B_EXE) ==
                stage_c_manifest["stage_b_executable_sha256"]
            and sha256(stage_c.EXE) ==
                stage_c_manifest["gurobi_executable_sha256"]):
        raise RuntimeError(
            "Stage C contract-fix or invalidated-attempt provenance failed")
    if not (
            stage_c_decision.get("completed") is True
            and stage_c_decision.get("expected_rows") == stage_c.EXPECTED_ROWS
            and stage_c_decision.get("completed_rows") == stage_c.EXPECTED_ROWS
            and stage_c_decision.get("valid_rows") == stage_c.EXPECTED_ROWS
            and stage_c_decision.get("false_certificate_count") == 0
            and stage_c_decision.get("separately_frozen_validation") is True
            and stage_c_decision.get(
                "historical_comparator_compatibility_valid") is True
            and stage_c_decision.get("automatic_promotion_performed") is False
            and stage_c_decision.get("rho_sensitivity_performed") is False
            and stage_c_decision.get(
                "instance_dependent_dispatch_introduced") is False
            and stage_c_decision.get(
                "validated_gurobi_mainline") == "C6-HGA-FULL"):
        raise RuntimeError(
            "Stage C final validity or no-promotion gate is not green")
    stage_c_matrix = stage_c.csv_rows(stage_c.MATRIX)
    stage_c_summary = stage_c.csv_rows(stage_c.SUMMARY)
    if (len(stage_c_matrix) != stage_c.EXPECTED_ROWS
            or len(stage_c_summary) != stage_c.EXPECTED_ROWS
            or len({row["run_id"] for row in stage_c_summary}) !=
            stage_c.EXPECTED_ROWS
            or sum(row["validation_stage"] == "qualification_1800"
                   for row in stage_c_matrix) != 35
            or sum(row["validation_stage"] == "independent_v50_3600"
                   for row in stage_c_matrix) != 12):
        raise RuntimeError("Stage C matrix or runner summary is not 47-row complete")
    return {"stage_b": decision, "stage_c": stage_c_decision}


def stage_c_completion_manifest() -> list[dict[str, Any]]:
    """Revalidate every Stage C row and retain compact raw-artifact identities."""
    matrix = stage_c.csv_rows(stage_c.MATRIX)
    items = stage_c.inventory()
    manifest = stage_c.load_json(stage_c.FROZEN_MANIFEST)
    output = []
    for row in matrix:
        directory = stage_c.RUNS / row["run_id"]
        valid, reason = stage_c_runner.completion_valid(
            directory, row, items[row["instance_id"]], manifest)
        if not valid:
            raise RuntimeError(
                f"Stage C row failed checksum revalidation: "
                f"{row['run_id']}:{reason}")
        marker_path = directory / "completion_marker.json"
        artifact_path = directory / "artifact_manifest.csv"
        marker = stage_c.load_json(marker_path)
        output.append({
            "serial_order": int(row["serial_order"]),
            "validation_stage": row["validation_stage"],
            "run_id": row["run_id"],
            "instance_id": row["instance_id"],
            "completion_valid": True,
            "completion_reason": reason,
            "completion_marker_path": stage_c.relative(marker_path),
            "completion_marker_bytes": marker_path.stat().st_size,
            "completion_marker_sha256": sha256(marker_path),
            "artifact_manifest_path": stage_c.relative(artifact_path),
            "artifact_manifest_bytes": artifact_path.stat().st_size,
            "artifact_manifest_sha256": sha256(artifact_path),
            "artifact_count": int(marker["artifact_count"]),
            "result_sha256": marker["result_sha256"],
            "strict_certificate": marker[
                "strict_certified_original_problem"],
            "emergency_timeout": marker["emergency_timeout"],
            "algorithmic_solve_state_resumed": marker[
                "algorithmic_solve_state_resumed"],
            "anchor_safety_valid": marker["anchor_safety_valid"],
            "arm_contract_matches": marker["arm_contract_matches"],
            "root_coverage_valid": marker["root_coverage_valid"],
            "parent_child_coverage_valid": marker[
                "parent_child_coverage_valid"],
        })
    return output


def main() -> int:
    decisions = validate_final()
    decision = decisions["stage_b"]
    stage_c_decision = decisions["stage_c"]
    stage_c_completion_csv = common.OUT / "stage_c_completion_manifest.csv"
    write_csv(stage_c_completion_csv, stage_c_completion_manifest())
    compressed_derived = []
    for source_name, target_name in COMPRESSED_DERIVED.items():
        source, target = common.OUT / source_name, common.OUT / target_name
        marker = sensitive(source)
        if marker:
            raise RuntimeError(
                f"license-sensitive marker {marker} in {source}")
        gzip_deterministic(source, target)
        require_repository_artifact_size(target)
        compressed_derived.append({
            "source_path": common.relative(source),
            "source_bytes": source.stat().st_size,
            "source_sha256": sha256(source),
            "compressed_path": common.relative(target),
            "compressed_bytes": target.stat().st_size,
            "compressed_sha256": sha256(target),
            "compression": "gzip_level9_mtime0",
        })
    selected = representatives()
    matrix = common.csv_rows(common.OFFICIAL_MATRIX)
    by_panel_arm = {(row["panel_row_id"], row["arm"]): row for row in matrix}
    bundle = common.OUT / "representative_raw"
    manifest_rows = []
    expected_targets: set[Path] = set()
    for representative in selected:
        for arm in common.ARMS:
            matrix_row = by_panel_arm[(representative["panel_row_id"], arm)]
            run_dir = common.RUNS / matrix_row["run_id"]
            for relative in RAW_FILES:
                source = run_dir / relative
                if not source.is_file():
                    raise RuntimeError(f"representative raw artifact missing: {source}")
                marker = sensitive(source)
                if marker:
                    raise RuntimeError(
                        f"license-sensitive marker {marker} in {source}")
                target = bundle / representative["panel_row_id"] / arm.lower(
                    ).replace("-", "_") / f"{relative}.gz"
                gzip_deterministic(source, target)
                require_repository_artifact_size(target)
                expected_targets.add(target.resolve())
                manifest_rows.append({
                    **representative, "arm": arm,
                    "run_id": matrix_row["run_id"],
                    "source_path": common.relative(source),
                    "source_bytes": source.stat().st_size,
                    "source_sha256": sha256(source),
                    "compressed_path": common.relative(target),
                    "compressed_bytes": target.stat().st_size,
                    "compressed_sha256": sha256(target),
                    "compression": "gzip_level9_mtime0",
                    "license_sensitive_scan_passed": True,
                })
    # Fail closed on stale packaged files instead of silently retaining a
    # representative selected by an earlier analysis.
    stale = [path for path in bundle.rglob("*.gz")
             if path.resolve() not in expected_targets]
    if stale:
        raise RuntimeError(
            "stale representative files require manual audit: "
            + ", ".join(common.relative(path) for path in stale[:5]))
    manifest_csv = common.OUT / "representative_raw_manifest.csv"
    write_csv(manifest_csv, manifest_rows)
    selection_csv = common.OUT / "representative_selection.csv"
    write_csv(selection_csv, selected)
    final_inventory = []
    inventory_names = [COMPRESSED_DERIVED.get(name, name)
                       for name in FINAL_DERIVED] + [
        "representative_selection.csv", "representative_raw_manifest.csv",
        "stage_c_completion_manifest.csv"]
    for name in inventory_names:
        path = common.OUT / name
        marker = sensitive(path)
        if marker:
            raise RuntimeError(
                f"license-sensitive marker {marker} in {path}")
        require_repository_artifact_size(path)
        final_inventory.append({
            "path": common.relative(path), "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    inventory_csv = common.OUT / "final_evidence_inventory.csv"
    write_csv(inventory_csv, final_inventory)
    summary = {
        "schema": "round36-evidence-package-v2",
        "round_id": 36,
        "classification": decision["classification"],
        "completed_official_rows": 56,
        "completed_stage_c_rows": stage_c.EXPECTED_ROWS,
        "stage_c_candidate": stage_c_decision["candidate"],
        "stage_c_predeclared_performance_gate_passed": stage_c_decision[
            "predeclared_performance_gate_passed"],
        "stage_c_automatic_promotion_performed": False,
        "stage_c_recommendation": stage_c_decision["recommendation"],
        "representative_patterns": len(selected),
        "representative_instances": selected,
        "representative_arm_rows": len(selected) * len(common.ARMS),
        "compressed_raw_artifacts": len(manifest_rows),
        "uncompressed_raw_bytes": sum(int(row["source_bytes"])
                                      for row in manifest_rows),
        "compressed_raw_bytes": sum(int(row["compressed_bytes"])
                                    for row in manifest_rows),
        "compressed_derived_artifacts": compressed_derived,
        "representative_manifest_sha256": sha256(manifest_csv),
        "stage_c_completion_manifest_sha256": sha256(
            stage_c_completion_csv),
        "final_evidence_inventory_sha256": sha256(inventory_csv),
        "all_raw_runs_retained_locally": True,
        "all_raw_runs_checksum_addressed": True,
        "model_dumps_packaged": False,
        "license_sensitive_material_packaged": False,
        "repository_artifact_size_limit_bytes":
            MAX_REPOSITORY_ARTIFACT_BYTES,
        "all_repository_artifacts_below_size_limit": True,
    }
    write_json(common.OUT / "evidence_package_summary.json", summary)
    report = f"""# Round 36 evidence package

- Final classification: `{decision['classification']}`.
- Official rows: 56 checksum-complete.
- Separately frozen Stage C rows: {stage_c.EXPECTED_ROWS} checksum-complete.
- Stage C historical-comparator gate:
  `{stage_c_decision['predeclared_performance_gate_passed']}`; no automatic
  promotion was performed.
- Representative patterns: {len(selected)}.
- Representative four-arm rows: {len(selected) * len(common.ARMS)}.
- Compressed raw artifacts: {len(manifest_rows)}.
- Raw bytes before/after lossless gzip: {summary['uncompressed_raw_bytes']} /
  {summary['compressed_raw_bytes']}.
- The all-row trajectory CSV is retained locally and packaged as deterministic
  `trajectory_events.csv.gz` for repository synchronization.
- License-sensitive material: none.
- Model dumps: excluded.

Representatives are selected deterministically within each frozen Round-35
pattern by the largest absolute HH-versus-BW-P common-window proof-AUC delta.
All four arms are packaged for each selected instance. Original raw paths,
uncompressed hashes, compressed paths, and compressed hashes are recorded in
`representative_raw_manifest.csv`. All 56 complete raw directories remain
local and are independently checksum-addressed by their completion markers.
All 47 Stage C completion markers and artifact manifests are independently
revalidated and checksum-indexed by `stage_c_completion_manifest.csv`; the
full Stage C raw directories also remain local.
"""
    write_text(common.OUT / "evidence_package_report.md", report)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
