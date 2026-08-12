#!/usr/bin/env python3
"""Run the separately frozen Round 36 Stage C candidate validation."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import round36_stage_c_common as common


SENSITIVE_MARKERS = (b"grb_license_file", b"wlsaccessid",
                     b"wlssecret", b"licenseid")


def artifact_inventory(directory: Path) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.name in {
                "artifact_manifest.csv", "completion_marker.json",
                "run_state.json"}:
            continue
        output.append({
            "path": path.relative_to(directory).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": common.sha256(path),
        })
    return output


def completion_valid(directory: Path, row: dict[str, str],
                     item: dict[str, Any], manifest: dict[str, Any]
                     ) -> tuple[bool, str]:
    marker_path = directory / "completion_marker.json"
    artifact_path = directory / "artifact_manifest.csv"
    if not marker_path.is_file() or not artifact_path.is_file():
        return False, "completion_or_artifact_manifest_missing"
    try:
        marker = common.load_json(marker_path)
        artifacts = common.csv_rows(artifact_path)
    except (OSError, ValueError, json.JSONDecodeError, csv.Error):
        return False, "completion_metadata_unparseable"
    expected = {
        "round_id": 36,
        "stage": "C",
        "run_id": row["run_id"],
        "instance_sha256": item["instance_sha256"],
        "executable_sha256": manifest["gurobi_executable_sha256"],
        "validation_matrix_sha256": manifest[
            "validation_matrix_sha256"],
        "candidate_definition_sha256": manifest[
            "candidate_definition_sha256"],
    }
    for key, value in expected.items():
        if marker.get(key) != value:
            return False, f"completion_identity_mismatch:{key}"
    if common.sha256(artifact_path) != marker.get(
            "artifact_manifest_sha256"):
        return False, "artifact_manifest_checksum_mismatch"
    for artifact in artifacts:
        path = directory / artifact["path"]
        if (not path.is_file() or path.stat().st_size != int(
                artifact["bytes"]) or
                common.sha256(path) != artifact["sha256"]):
            return False, f"artifact_checksum_mismatch:{artifact['path']}"
    return True, "checksum_valid_complete_row"


def validate_frozen(item: dict[str, Any], manifest: dict[str, Any]) -> None:
    identities = (
        (common.CANDIDATE, "candidate_definition_sha256"),
        (common.MATRIX, "validation_matrix_sha256"),
        (common.COMMAND_FREEZE, "command_freeze_sha256"),
    )
    for path, key in identities:
        if not path.is_file() or common.sha256(path) != manifest[key]:
            raise RuntimeError(f"frozen Stage C artifact changed: {path.name}")
    for path_text, expected in manifest["source_file_sha256"].items():
        path = common.ROOT / path_text
        if not path.is_file() or common.sha256(path) != expected:
            raise RuntimeError(f"frozen source changed: {path_text}")
    if (not common.EXE.is_file() or common.sha256(common.EXE) !=
            manifest["gurobi_executable_sha256"]):
        raise RuntimeError("official executable changed")
    path = common.item_path(item)
    if not path.is_file() or common.sha256(path) != item["instance_sha256"]:
        raise RuntimeError(f"instance changed: {item['instance_id']}")
    if "GRB_LICENSE_FILE" not in os.environ:
        raise RuntimeError("licensed child environment is unavailable")


def scan_sensitive(directory: Path) -> None:
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes().lower()
        if any(marker in data for marker in SENSITIVE_MARKERS):
            raise RuntimeError(f"sensitive license marker detected: {path}")


def acquire_lock() -> None:
    if common.LOCK.exists():
        try:
            state = common.load_json(common.LOCK)
            pid = int(state.get("pid", 0))
            if pid > 0:
                os.kill(pid, 0)
                raise RuntimeError("another Round 36 Stage C runner is active")
        except OSError:
            pass
    common.LOCK.unlink(missing_ok=True)
    common.write_json(common.LOCK, {"pid": os.getpid(),
                                   "created": time.time()})


def result_record(row: dict[str, str], item: dict[str, Any],
                  manifest: dict[str, Any], command: list[str]
                  ) -> dict[str, Any]:
    return {
        "schema": "round36-stage-c-run-v1",
        "round_id": 36,
        "stage": "C",
        "run_id": row["run_id"],
        "serial_order": int(row["serial_order"]),
        "stage_row_id": row["stage_row_id"],
        "validation_stage": row["validation_stage"],
        "instance_id": item["instance_id"],
        "instance_path": item["path"],
        "instance_sha256": item["instance_sha256"],
        "V": item["V"], "M": item["M"], "Q": item["Q"],
        "scenario": item["scenario"], "arm": common.ARM,
        "process_cap_seconds": int(row["process_cap_seconds"]),
        "watchdog_seconds": int(row["watchdog_seconds"]),
        "solver": "Gurobi", "solver_version": "13.0.2",
        "gurobi_seed": 0, "threads": 1, "rho": 0.01,
        "initial_interval_count": 4,
        "executable_sha256": manifest["gurobi_executable_sha256"],
        "validation_matrix_sha256": manifest[
            "validation_matrix_sha256"],
        "candidate_definition_sha256": manifest[
            "candidate_definition_sha256"],
        "source_tree_fingerprint": manifest["source_tree_fingerprint"],
        "command": command,
        "license_environment": "child_only_not_serialized",
        "algorithmic_solve_state_resumed": False,
        "completed": False,
    }


def run_one(row: dict[str, str], items: dict[str, dict[str, Any]],
            manifest: dict[str, Any]) -> dict[str, Any]:
    item = items[row["instance_id"]]
    directory = common.RUNS / row["run_id"]
    if directory.exists():
        valid, reason = completion_valid(directory, row, item, manifest)
        if valid:
            print(f"SKIP {row['serial_order']} {row['run_id']}", flush=True)
            return common.load_json(directory / "completion_marker.json")
        target = common.INVALIDATED / (
            f"{row['run_id']}__invalidated__{int(time.time() * 1000)}")
        common.INVALIDATED.mkdir(parents=True, exist_ok=True)
        if common.OUT.resolve() not in target.resolve().parents:
            raise RuntimeError(f"unsafe invalidation target: {target}")
        os.replace(directory, target)
        common.write_json(target / "invalidation_record.json", {
            "round_id": 36, "stage": "C", "run_id": row["run_id"],
            "reason": reason, "algorithmic_solve_state_resumed": False,
        })
    validate_frozen(item, manifest)
    directory.mkdir(parents=True, exist_ok=False)
    command = common.command_for(row, item, directory)
    frozen = common.load_json(common.COMMAND_FREEZE)["commands"][
        row["run_id"]]["command"]
    if command != frozen:
        raise RuntimeError(f"command changed after freeze: {row['run_id']}")
    record = result_record(row, item, manifest, command)
    common.write_json(directory / "command.json", record)
    common.write_json(directory / "run_state.json", {
        **record, "runner_state": "child_launch_pending"})
    started = time.monotonic()
    emergency = False
    with (directory / "console.stdout.log").open("wb") as stdout, \
         (directory / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=common.ROOT, env=os.environ.copy(),
                stdout=stdout, stderr=stderr,
                timeout=int(row["watchdog_seconds"]), check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
            emergency = True
    result_path = directory / "result.json"
    result = common.load_json(result_path) if result_path.is_file() else None
    missing = [common.relative(path) for path in common.required_artifacts(
        directory) if not path.is_file()]
    record.update({
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code,
        "emergency_timeout": emergency,
        "result_json_parse_verified_after_process_exit": result is not None,
        "missing_required_artifacts": missing,
    })
    if result is not None:
        lower, upper = common.result_bounds(result)
        proof = float(result.get("round36_proof_incumbent_launch", upper))
        anchor = float(result.get("round36_decomposition_anchor_launch",
                                  proof))
        record.update({
            "status": result.get("status"),
            "valid_lower_bound": lower,
            "verified_upper_bound": upper,
            "final_gap": max(0.0, (upper - lower) /
                             max(1e-12, abs(upper))),
            "strict_certified_original_problem": result.get(
                "strict_certified_original_problem"),
            "strict_certificate_class": result.get(
                "strict_certificate_class", ""),
            "strict_certificate_rejection_reason": result.get(
                "strict_certificate_rejection_reason", ""),
            "process_entry_time_seconds": common.process_entry_time(result),
            "reported_causal_arm": result.get("round36_c6_causal_arm"),
            "reported_split_normalization": result.get(
                "round36_c6_split_normalization"),
            "arm_contract_matches": (
                result.get("round36_c6_causal_arm") == common.CAUSAL_ARM and
                result.get("round36_c6_split_normalization") ==
                common.NORMALIZATION),
            "proof_incumbent_launch": proof,
            "decomposition_anchor_launch": anchor,
            "anchor_safety_valid": (
                result.get("round36_anchor_safety_valid") is True and
                anchor + 1e-9 >= proof),
            "root_coverage_valid": result.get(
                "external_gini_tree_root_coverage_valid"),
            "parent_child_coverage_valid": result.get(
                "external_gini_tree_parent_child_coverage_valid"),
        })
    finalized = (not emergency and result is not None and not missing and
                 record.get("arm_contract_matches") and
                 record.get("anchor_safety_valid") and
                 record.get("root_coverage_valid") and
                 record.get("parent_child_coverage_valid"))
    if not finalized:
        common.write_json(directory / "run_state.json", {
            **record, "runner_state": "incomplete_preserved_requires_audit"})
        raise RuntimeError(
            f"invalid Stage C row: {row['run_id']} rc={return_code} "
            f"emergency={emergency} missing={len(missing)}")
    scan_sensitive(directory)
    artifacts = artifact_inventory(directory)
    artifact_path = directory / "artifact_manifest.csv"
    common.write_csv(artifact_path, artifacts, ["path", "bytes", "sha256"])
    marker = {
        **record,
        "artifact_count": len(artifacts),
        "artifact_manifest_sha256": common.sha256(artifact_path),
        "result_sha256": common.sha256(result_path),
        "completed": True,
        "completion_marker_atomic": True,
        "completed_at_unix_seconds": time.time(),
    }
    common.write_json(directory / "completion_marker.json", marker)
    common.write_json(directory / "run_state.json", {
        **marker, "runner_state": "checksum_valid_complete"})
    print(f"DONE {row['serial_order']}/{common.EXPECTED_ROWS} "
          f"{row['run_id']} strict="
          f"{marker.get('strict_certified_original_problem')} "
          f"gap={marker.get('final_gap')}", flush=True)
    return marker


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", action="append")
    parser.add_argument("--validation-stage", action="append")
    parser.add_argument("--max-rows", type=int)
    args = parser.parse_args()
    if "GRB_LICENSE_FILE" not in os.environ:
        raise SystemExit("licensed child environment is unavailable")
    manifest = common.load_json(common.FROZEN_MANIFEST)
    items = common.inventory()
    rows = common.csv_rows(common.MATRIX)
    if args.run_id:
        rows = [row for row in rows if row["run_id"] in set(args.run_id)]
    if args.validation_stage:
        rows = [row for row in rows if row["validation_stage"] in
                set(args.validation_stage)]
    rows.sort(key=lambda row: int(row["serial_order"]))
    if args.max_rows is not None:
        rows = rows[:max(0, args.max_rows)]
    acquire_lock()
    common.RUNS.mkdir(parents=True, exist_ok=True)
    if not common.START_RECORD.is_file():
        common.write_json(common.START_RECORD, {
            "schema": "round36-stage-c-start-v1",
            "round_id": 36, "stage": "C",
            "started_at_unix_seconds": time.time(),
            "source_tree_fingerprint": manifest["source_tree_fingerprint"],
            "executable_sha256": manifest["gurobi_executable_sha256"],
            "validation_matrix_sha256": manifest[
                "validation_matrix_sha256"],
            "candidate_definition_sha256": manifest[
                "candidate_definition_sha256"],
            "frozen_before_stage_c_results": True,
        })
    existing = (common.csv_rows(common.SUMMARY)
                if common.SUMMARY.is_file() else [])
    keyed = {row["run_id"]: row for row in existing}
    try:
        for row in rows:
            marker = run_one(row, items, manifest)
            keyed[row["run_id"]] = marker
            common.write_csv(
                common.SUMMARY,
                sorted(keyed.values(), key=lambda value:
                       int(value["serial_order"])))
    finally:
        common.LOCK.unlink(missing_ok=True)
    print(json.dumps({
        "selected_rows": len(rows),
        "completed_rows": len(keyed),
        "strict_rows": sum(str(row.get(
            "strict_certified_original_problem")).lower() == "true"
            for row in keyed.values()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
