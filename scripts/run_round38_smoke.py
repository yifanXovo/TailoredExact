#!/usr/bin/env python3
"""Checksum-resumable serial runner for frozen Round 38 smoke pairs."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import round38_experiment_common as common
import run_round25_experiments as licensed


LOCK = common.OUT / ".round38_smoke_runner.lock"
SENSITIVE_MARKERS = (
    b"GRB_LICENSE_FILE", b"gurobi.lic", b"LicenseID",
    b"WLSAccessID", b"WLSSecret", b"TokenServer",
)


def artifact_inventory(directory: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(
            (item for item in directory.rglob("*") if item.is_file()),
            key=lambda item: item.as_posix()):
        if path.name in {
            "artifact_manifest.csv", "completion_marker.json", "run_state.json"
        }:
            continue
        records.append({
            "path": path.relative_to(directory).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": common.sha256(path),
        })
    return records


def completion_valid(directory: Path, row: dict[str, str],
                     item: dict[str, Any], freeze: dict[str, Any]
                     ) -> tuple[bool, str]:
    marker_path = directory / "completion_marker.json"
    manifest_path = directory / "artifact_manifest.csv"
    if not marker_path.is_file() or not manifest_path.is_file():
        return False, "completion_or_artifact_manifest_missing"
    try:
        marker = common.load_json(marker_path)
        artifacts = common.csv_rows(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError, csv.Error):
        return False, "completion_metadata_unparseable"
    expected = {
        "round_id": 38,
        "run_id": row["run_id"],
        "instance_sha256": item["instance_sha256"],
        "executable_sha256": freeze["executable_sha256"],
        "matrix_sha256": freeze["matrix_sha256"],
    }
    for key, value in expected.items():
        if marker.get(key) != value:
            return False, f"completion_identity_mismatch:{key}"
    if common.sha256(manifest_path) != marker.get(
            "artifact_manifest_sha256"):
        return False, "artifact_manifest_checksum_mismatch"
    for artifact in artifacts:
        path = directory / artifact["path"]
        if (not path.is_file() or
                path.stat().st_size != int(artifact["bytes"]) or
                common.sha256(path) != artifact["sha256"]):
            return False, f"artifact_checksum_mismatch:{artifact['path']}"
    return True, "checksum_valid_complete_row"


def validate_frozen(row: dict[str, str], item: dict[str, Any],
                    freeze: dict[str, Any]) -> None:
    if common.sha256(common.PANEL) != freeze["panel_sha256"]:
        raise RuntimeError("frozen panel changed")
    if common.sha256(common.SMOKE_MATRIX) != freeze["matrix_sha256"]:
        raise RuntimeError("smoke matrix changed")
    if (not common.EXE.is_file() or
            common.sha256(common.EXE) != freeze["executable_sha256"]):
        raise RuntimeError("official executable changed")
    for relative, expected in freeze["source_file_sha256"].items():
        path = common.ROOT / relative
        if not path.is_file() or common.sha256(path) != expected:
            raise RuntimeError(f"frozen source changed: {relative}")
    instance_path = common.ROOT / item["path"]
    if (not instance_path.is_file() or
            common.sha256(instance_path) != item["instance_sha256"]):
        raise RuntimeError(f"instance changed: {item['instance_id']}")
    expected = freeze["commands"][row["run_id"]]["command"]
    actual = common.command_for(
        row, item, common.SMOKE_RUNS / row["run_id"]
    )
    if actual != expected:
        raise RuntimeError(f"command changed: {row['run_id']}")
    if not licensed.LICENSE.is_file():
        raise RuntimeError("licensed child environment unavailable")


def scan_sensitive(directory: Path) -> None:
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes().lower()
        if any(marker.lower() in data for marker in SENSITIVE_MARKERS):
            raise RuntimeError(f"sensitive license marker in {path.name}")


def boolean(value: Any) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes"}


def run_one(row: dict[str, str], item: dict[str, Any],
            freeze: dict[str, Any]) -> dict[str, Any]:
    directory = common.SMOKE_RUNS / row["run_id"]
    if directory.exists():
        valid, reason = completion_valid(directory, row, item, freeze)
        if valid:
            print(f"SKIP {row['serial_order']} {row['run_id']}", flush=True)
            return common.load_json(directory / "completion_marker.json")
        raise RuntimeError(
            "existing incomplete/invalid run requires preservation: "
            f"{row['run_id']}:{reason}"
        )
    validate_frozen(row, item, freeze)
    directory.mkdir(parents=True, exist_ok=False)
    command = freeze["commands"][row["run_id"]]["command"]
    record: dict[str, Any] = {
        "schema": "round38-smoke-run-v1",
        "round_id": 38,
        "run_id": row["run_id"],
        "serial_order": int(row["serial_order"]),
        "stage": row["stage"],
        "panel_row_id": row["panel_row_id"],
        "instance_id": item["instance_id"],
        "instance_path": item["path"],
        "instance_sha256": item["instance_sha256"],
        "V": int(row["V"]),
        "M": int(row["M"]),
        "scenario": row["scenario"],
        "arm": row["arm"],
        "process_cap_seconds": int(row["process_cap_seconds"]),
        "watchdog_seconds": int(row["watchdog_seconds"]),
        "solver": "Gurobi",
        "solver_version": "13.0.2",
        "gurobi_seed": 0,
        "threads": 1,
        "K": 4,
        "rho": 0.01,
        "executable_sha256": freeze["executable_sha256"],
        "matrix_sha256": freeze["matrix_sha256"],
        "source_tree_fingerprint": freeze["source_tree_fingerprint"],
        "command": command,
        "license_environment": "child_only_not_serialized",
        "algorithmic_solve_state_resumed": False,
        "completed": False,
    }
    common.write_json(directory / "command.json", record)
    common.write_json(directory / "run_state.json", {
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
                command, cwd=common.ROOT, env=environment,
                stdout=stdout, stderr=stderr,
                timeout=int(row["watchdog_seconds"]), check=False,
            )
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
            emergency = True
    result_path = directory / "result.json"
    result = common.load_json(result_path) if result_path.is_file() else None
    missing = [
        path.relative_to(common.ROOT).as_posix()
        for path in common.required_artifacts(directory) if not path.is_file()
    ]
    record.update({
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code,
        "emergency_timeout": emergency,
        "result_json_parse_verified_after_process_exit": result is not None,
        "missing_required_artifacts": missing,
    })
    if result is not None:
        lower = float(result["external_gini_tree_global_lower_bound"])
        upper = float(result["external_gini_tree_verified_upper_bound"])
        expected_policy = (
            "off" if row["arm"] == "C6"
            else "pilot-next-frontier-complete"
        )
        gates = {
            "arm_contract_matches":
                result.get("round38_c6_frontier_policy") == expected_policy,
            "round37_policy_off":
                result.get("round37_c6_geometry_policy") == "off",
            "root_coverage_valid": boolean(
                result.get("external_gini_tree_root_coverage_valid")
            ),
            "parent_child_coverage_valid": boolean(
                result.get("external_gini_tree_parent_child_coverage_valid")
            ),
            "lifecycle_complete": boolean(
                result.get("external_gini_tree_lifecycle_complete")
            ),
            "global_bound_monotone": boolean(
                result.get("external_gini_tree_global_bound_monotone")
            ),
            "leaf_bounds_monotone": boolean(
                result.get("external_gini_tree_leaf_bounds_monotone")
            ),
            "feasibility_gate": boolean(
                result.get("external_gini_tree_feasibility_consistency_gate")
            ),
        }
        strict = boolean(result.get("strict_certified_original_problem"))
        all_closed = boolean(
            result.get("external_gini_tree_all_relevant_leaves_closed")
        )
        false_certificate = strict and not (
            all(gates.values()) and all_closed and lower >= upper - 1e-7
        )
        record.update({
            "status": result.get("status"),
            "valid_lower_bound": lower,
            "verified_upper_bound": upper,
            "final_gap": max(
                0.0, (upper - lower) / max(1e-12, abs(upper))
            ),
            "strict_certified_original_problem": strict,
            "strict_certificate_class": result.get(
                "strict_certificate_class", ""
            ),
            "strict_certificate_rejection_reason": result.get(
                "strict_certificate_rejection_reason", ""
            ),
            **gates,
            "all_relevant_leaves_closed": all_closed,
            "false_certificate": false_certificate,
            "pilot_all_initial_lps_complete": result.get(
                "round38_pilot_all_initial_lps_complete"
            ),
            "pilot_initial_lp_count": result.get(
                "round38_pilot_initial_lp_count"
            ),
            "pilot_selected_leaf_id": result.get(
                "round38_pilot_selected_leaf_id"
            ),
            "pilot_children_evaluated": result.get(
                "round38_pilot_children_evaluated"
            ),
            "pilot_completes_next_strict_frontier": result.get(
                "round38_pilot_completes_next_strict_frontier"
            ),
            "pilot_refinement_performed": result.get(
                "round38_pilot_refinement_performed"
            ),
            "pilot_decision_reason": result.get(
                "round38_pilot_decision_reason"
            ),
        })
    required_gates = (
        "arm_contract_matches", "round37_policy_off",
        "root_coverage_valid", "parent_child_coverage_valid",
        "lifecycle_complete", "global_bound_monotone",
        "leaf_bounds_monotone", "feasibility_gate",
    )
    finalized = (
        not emergency and return_code == 0 and result is not None and
        not missing and all(record.get(key) for key in required_gates) and
        not record.get("false_certificate")
    )
    if not finalized:
        common.write_json(directory / "run_state.json", {
            **record, "runner_state": "incomplete_preserved_requires_audit"
        })
        raise RuntimeError(
            f"invalid smoke row: {row['run_id']} rc={return_code} "
            f"emergency={emergency} missing={len(missing)}"
        )
    scan_sensitive(directory)
    artifacts = artifact_inventory(directory)
    manifest_path = directory / "artifact_manifest.csv"
    common.write_csv(manifest_path, artifacts, ["path", "bytes", "sha256"])
    marker = {
        **record,
        "artifact_count": len(artifacts),
        "artifact_manifest_sha256": common.sha256(manifest_path),
        "result_sha256": common.sha256(result_path),
        "completed": True,
        "completion_marker_atomic": True,
        "completed_at_unix_seconds": time.time(),
    }
    common.write_json(directory / "completion_marker.json", marker)
    common.write_json(directory / "run_state.json", {
        **marker, "runner_state": "checksum_valid_complete"
    })
    print(
        f"DONE {row['serial_order']}/12 {row['run_id']} "
        f"strict={marker.get('strict_certified_original_problem')} "
        f"gap={marker.get('final_gap')} "
        f"decision={marker.get('pilot_decision_reason')}", flush=True,
    )
    return marker


def main() -> int:
    if not common.SMOKE_FREEZE.is_file() or not common.SMOKE_MATRIX.is_file():
        raise SystemExit("freeze_round38_smoke.py must run first")
    freeze = common.load_json(common.SMOKE_FREEZE)
    matrix = common.csv_rows(common.SMOKE_MATRIX)
    panel = common.panel()
    common.SMOKE_RUNS.mkdir(parents=True, exist_ok=True)
    try:
        with LOCK.open("x", encoding="utf-8") as stream:
            stream.write(str(os.getpid()))
    except FileExistsError as error:
        raise SystemExit("another Round 38 smoke runner may be active") from error
    markers = []
    try:
        for row in matrix:
            markers.append(run_one(row, panel[row["panel_row_id"]], freeze))
        common.write_csv(common.SMOKE_SUMMARY, markers)
    finally:
        if LOCK.is_file():
            LOCK.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
