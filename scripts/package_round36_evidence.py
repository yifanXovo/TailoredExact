#!/usr/bin/env python3
"""Create the compact, auditable Round 36 final evidence bundle.

All 56 raw run directories remain local and checksum-addressed by their
completion markers.  This script packages all four arms for one deterministic
representative per frozen Round-35 pattern, retaining the ledgers needed to
audit the causal claims without committing model dumps or redundant logs.
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

import round36_common as common


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
)


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
    for name in FINAL_DERIVED:
        if not (common.OUT / name).is_file():
            raise RuntimeError(f"required final artifact missing: {name}")
    matrix = common.csv_rows(common.OFFICIAL_MATRIX)
    if len(matrix) != 56:
        raise RuntimeError("official matrix is not 56 rows")
    for row in matrix:
        directory = common.RUNS / row["run_id"]
        marker = directory / "completion_marker.json"
        inventory = directory / "artifact_manifest.csv"
        if not marker.is_file() or not inventory.is_file():
            raise RuntimeError(f"official row incomplete: {row['run_id']}")
        state = json.loads(marker.read_text(encoding="utf-8"))
        if sha256(inventory) != state.get("artifact_manifest_sha256"):
            raise RuntimeError(f"artifact manifest drift: {row['run_id']}")
    return decision


def main() -> int:
    decision = validate_final()
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
    inventory_names = list(FINAL_DERIVED) + [
        "representative_selection.csv", "representative_raw_manifest.csv"]
    for name in inventory_names:
        path = common.OUT / name
        final_inventory.append({
            "path": common.relative(path), "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    inventory_csv = common.OUT / "final_evidence_inventory.csv"
    write_csv(inventory_csv, final_inventory)
    summary = {
        "schema": "round36-evidence-package-v1",
        "round_id": 36,
        "classification": decision["classification"],
        "completed_official_rows": 56,
        "representative_patterns": len(selected),
        "representative_instances": selected,
        "representative_arm_rows": len(selected) * len(common.ARMS),
        "compressed_raw_artifacts": len(manifest_rows),
        "uncompressed_raw_bytes": sum(int(row["source_bytes"])
                                      for row in manifest_rows),
        "compressed_raw_bytes": sum(int(row["compressed_bytes"])
                                    for row in manifest_rows),
        "representative_manifest_sha256": sha256(manifest_csv),
        "final_evidence_inventory_sha256": sha256(inventory_csv),
        "all_raw_runs_retained_locally": True,
        "all_raw_runs_checksum_addressed": True,
        "model_dumps_packaged": False,
        "license_sensitive_material_packaged": False,
    }
    write_json(common.OUT / "evidence_package_summary.json", summary)
    report = f"""# Round 36 evidence package

- Final classification: `{decision['classification']}`.
- Official rows: 56 checksum-complete.
- Representative patterns: {len(selected)}.
- Representative four-arm rows: {len(selected) * len(common.ARMS)}.
- Compressed raw artifacts: {len(manifest_rows)}.
- Raw bytes before/after lossless gzip: {summary['uncompressed_raw_bytes']} /
  {summary['compressed_raw_bytes']}.
- License-sensitive material: none.
- Model dumps: excluded.

Representatives are selected deterministically within each frozen Round-35
pattern by the largest absolute HH-versus-BW-P common-window proof-AUC delta.
All four arms are packaged for each selected instance. Original raw paths,
uncompressed hashes, compressed paths, and compressed hashes are recorded in
`representative_raw_manifest.csv`. All 56 complete raw directories remain
local and are independently checksum-addressed by their completion markers.
"""
    write_text(common.OUT / "evidence_package_report.md", report)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
