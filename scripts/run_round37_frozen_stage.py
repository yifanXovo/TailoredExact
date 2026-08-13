#!/usr/bin/env python3
"""Serial checksum runner shared by post-smoke Round 37 frozen stages."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import round37_experiment_common as base
import run_round25_experiments as licensed


SENSITIVE_MARKERS = (
    b"GRB_LICENSE_FILE", b"gurobi.lic", b"LicenseID",
    b"WLSAccessID", b"WLSSecret", b"TokenServer",
)


def artifact_inventory(directory: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(
            (item for item in directory.rglob("*") if item.is_file()),
            key=lambda item: item.as_posix()):
        if path.name in {"artifact_manifest.csv", "completion_marker.json",
                         "run_state.json"}:
            continue
        records.append({
            "path": path.relative_to(directory).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": base.sha256(path),
        })
    return records


def scan_sensitive(directory: Path) -> None:
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes().lower()
        if any(marker.lower() in data for marker in SENSITIVE_MARKERS):
            raise RuntimeError(f"sensitive license marker in {path.name}")


def completion_valid(directory: Path, row: dict[str, str],
                     item: dict[str, Any], freeze: dict[str, Any]
                     ) -> tuple[bool, str]:
    marker_path = directory / "completion_marker.json"
    artifact_path = directory / "artifact_manifest.csv"
    if not marker_path.is_file() or not artifact_path.is_file():
        return False, "completion_or_artifact_manifest_missing"
    try:
        marker = base.load_json(marker_path)
        artifacts = base.csv_rows(artifact_path)
    except (OSError, ValueError, json.JSONDecodeError, csv.Error):
        return False, "completion_metadata_unparseable"
    expected = {
        "round_id": 37, "run_id": row["run_id"],
        "instance_sha256": item["instance_sha256"],
        "executable_sha256": freeze["executable_sha256"],
        "matrix_sha256": freeze["matrix_sha256"],
    }
    for key, value in expected.items():
        if marker.get(key) != value:
            return False, f"completion_identity_mismatch:{key}"
    if base.sha256(artifact_path) != marker.get("artifact_manifest_sha256"):
        return False, "artifact_manifest_checksum_mismatch"
    for artifact in artifacts:
        path = directory / artifact["path"]
        if (not path.is_file() or path.stat().st_size != int(artifact["bytes"])
                or base.sha256(path) != artifact["sha256"]):
            return False, f"artifact_checksum_mismatch:{artifact['path']}"
    return True, "checksum_valid_complete_row"


def validate_frozen(row: dict[str, str], item: dict[str, Any],
                    freeze: dict[str, Any], matrix: Path,
                    command_for: Any, run_dir: Path) -> None:
    if base.sha256(base.PANEL) != freeze["panel_sha256"]:
        raise RuntimeError("frozen panel changed")
    if base.sha256(matrix) != freeze["matrix_sha256"]:
        raise RuntimeError("stage matrix changed")
    if (not base.EXE.is_file() or
            base.sha256(base.EXE) != freeze["executable_sha256"]):
        raise RuntimeError("official executable changed")
    for relative, expected in freeze["source_file_sha256"].items():
        path = base.ROOT / relative
        if not path.is_file() or base.sha256(path) != expected:
            raise RuntimeError(f"frozen source changed: {relative}")
    instance_path = base.ROOT / item["path"]
    if (not instance_path.is_file() or
            base.sha256(instance_path) != item["instance_sha256"]):
        raise RuntimeError(f"instance changed: {item['instance_id']}")
    if command_for(row, item, run_dir) != \
            freeze["commands"][row["run_id"]]["command"]:
        raise RuntimeError(f"command changed: {row['run_id']}")
    if not licensed.LICENSE.is_file():
        raise RuntimeError("licensed child environment is unavailable")


def run_one(row: dict[str, str], item: dict[str, Any],
            freeze: dict[str, Any], matrix: Path, runs: Path,
            command_for: Any, total_rows: int) -> dict[str, Any]:
    directory = runs / row["run_id"]
    if directory.exists():
        valid, reason = completion_valid(directory, row, item, freeze)
        if valid:
            print(f"SKIP {row['serial_order']} {row['run_id']}", flush=True)
            return base.load_json(directory / "completion_marker.json")
        raise RuntimeError(
            f"existing invalid run requires preservation: "
            f"{row['run_id']}:{reason}"
        )
    validate_frozen(row, item, freeze, matrix, command_for, directory)
    directory.mkdir(parents=True, exist_ok=False)
    command = freeze["commands"][row["run_id"]]["command"]
    record: dict[str, Any] = {
        "schema": "round37-frozen-stage-run-v1", "round_id": 37,
        "run_id": row["run_id"],
        "serial_order": int(row["serial_order"]),
        "stage": row["stage"], "panel_row_id": row["panel_row_id"],
        "instance_id": item["instance_id"],
        "instance_path": item["path"],
        "instance_sha256": item["instance_sha256"],
        "V": int(row["V"]), "M": int(row["M"]),
        "scenario": row["scenario"], "arm": row["arm"],
        "process_cap_seconds": int(row["process_cap_seconds"]),
        "watchdog_seconds": int(row["watchdog_seconds"]),
        "solver": "Gurobi", "solver_version": "13.0.2",
        "gurobi_seed": 0, "threads": 1, "K": 4, "rho": 0.01,
        "executable_sha256": freeze["executable_sha256"],
        "matrix_sha256": freeze["matrix_sha256"],
        "source_tree_fingerprint": freeze["source_tree_fingerprint"],
        "command": command,
        "license_environment": "child_only_not_serialized",
        "algorithmic_solve_state_resumed": False, "completed": False,
    }
    base.write_json(directory / "command.json", record)
    base.write_json(directory / "run_state.json", {
        **record, "runner_state": "child_launch_pending"
    })
    environment = os.environ.copy()
    environment["GRB_LICENSE_FILE"] = str(licensed.LICENSE)
    started = time.monotonic()
    emergency = False
    with (directory / "console.stdout.log").open("wb") as stdout, \
         (directory / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=base.ROOT, env=environment,
                stdout=stdout, stderr=stderr,
                timeout=int(row["watchdog_seconds"]), check=False,
            )
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
            emergency = True
    result_path = directory / "result.json"
    result = base.load_json(result_path) if result_path.is_file() else None
    missing = [
        path.relative_to(base.ROOT).as_posix()
        for path in base.required_artifacts(directory) if not path.is_file()
    ]
    record.update({
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code, "emergency_timeout": emergency,
        "result_json_parse_verified_after_process_exit": result is not None,
        "missing_required_artifacts": missing,
    })
    if result is not None:
        lower = float(result["external_gini_tree_global_lower_bound"])
        upper = float(result["external_gini_tree_verified_upper_bound"])
        expected_policy = (
            "off" if row["arm"] == "C6" else "pilot-weakest-prefine"
        )
        root = bool(result.get("external_gini_tree_root_coverage_valid"))
        child = bool(result.get(
            "external_gini_tree_parent_child_coverage_valid"))
        lifecycle = bool(result.get("external_gini_tree_lifecycle_complete"))
        closed = bool(result.get(
            "external_gini_tree_all_relevant_leaves_closed"))
        strict = bool(result.get("strict_certified_original_problem"))
        false_certificate = strict and not (
            root and child and lifecycle and closed and lower >= upper - 1e-7
        )
        record.update({
            "status": result.get("status"), "valid_lower_bound": lower,
            "verified_upper_bound": upper,
            "final_gap": max(0.0, (upper - lower) /
                             max(1e-12, abs(upper))),
            "strict_certified_original_problem": strict,
            "strict_certificate_class": result.get(
                "strict_certificate_class", ""),
            "strict_certificate_rejection_reason": result.get(
                "strict_certificate_rejection_reason", ""),
            "reported_geometry_policy": result.get(
                "round37_c6_geometry_policy"),
            "arm_contract_matches": result.get(
                "round37_c6_geometry_policy") == expected_policy,
            "root_coverage_valid": root,
            "parent_child_coverage_valid": child,
            "lifecycle_complete": lifecycle,
            "all_relevant_leaves_closed": closed,
            "false_certificate": false_certificate,
            "pilot_all_initial_lps_complete": result.get(
                "round37_pilot_all_initial_lps_complete"),
            "pilot_initial_lp_count": result.get(
                "round37_pilot_initial_lp_count"),
            "pilot_weakest_leaf_id": result.get(
                "round37_pilot_weakest_leaf_id"),
            "pilot_prefinement_performed": result.get(
                "round37_pilot_prefinement_performed"),
            "pilot_prefinement_count": result.get(
                "round37_pilot_prefinement_count"),
        })
    finalized = (
        not emergency and return_code == 0 and result is not None and
        not missing and record.get("arm_contract_matches") and
        record.get("root_coverage_valid") and
        record.get("parent_child_coverage_valid") and
        record.get("lifecycle_complete") and
        not record.get("false_certificate")
    )
    if not finalized:
        base.write_json(directory / "run_state.json", {
            **record, "runner_state": "incomplete_preserved_requires_audit"
        })
        raise RuntimeError(
            f"invalid stage row: {row['run_id']} rc={return_code} "
            f"emergency={emergency} missing={len(missing)}"
        )
    scan_sensitive(directory)
    artifacts = artifact_inventory(directory)
    artifact_path = directory / "artifact_manifest.csv"
    base.write_csv(artifact_path, artifacts, ["path", "bytes", "sha256"])
    marker = {
        **record, "artifact_count": len(artifacts),
        "artifact_manifest_sha256": base.sha256(artifact_path),
        "result_sha256": base.sha256(result_path), "completed": True,
        "completion_marker_atomic": True,
        "completed_at_unix_seconds": time.time(),
    }
    base.write_json(directory / "completion_marker.json", marker)
    base.write_json(directory / "run_state.json", {
        **marker, "runner_state": "checksum_valid_complete"
    })
    print(
        f"DONE {row['serial_order']}/{total_rows} {row['run_id']} "
        f"strict={marker.get('strict_certified_original_problem')} "
        f"gap={marker.get('final_gap')}", flush=True,
    )
    return marker


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", required=True, type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--runs", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()
    matrix_path = args.matrix.resolve()
    freeze_path = args.freeze.resolve()
    runs = args.runs.resolve()
    summary = args.summary.resolve()
    for path in (matrix_path, freeze_path):
        if base.OUT.resolve() not in path.parents:
            raise SystemExit(f"stage evidence path outside Round 37: {path}")
    if base.OUT.resolve() not in runs.parents or \
            base.OUT.resolve() not in summary.parents:
        raise SystemExit("run/summary path outside Round 37")
    matrix = base.csv_rows(matrix_path)
    freeze = base.load_json(freeze_path)
    panel = base.panel()
    runs.mkdir(parents=True, exist_ok=True)
    lock = base.OUT / f".{runs.name}.lock"
    try:
        with lock.open("x", encoding="utf-8") as stream:
            stream.write(str(os.getpid()))
    except FileExistsError as error:
        raise SystemExit(f"another {runs.name} runner may be active") from error
    markers = []
    try:
        for row in matrix:
            markers.append(run_one(
                row, panel[row["panel_row_id"]], freeze, matrix_path, runs,
                base.command_for, len(matrix),
            ))
        base.write_csv(summary, markers)
    finally:
        if lock.is_file():
            lock.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
