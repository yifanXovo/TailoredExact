#!/usr/bin/env python3
"""Checksum-resumable serial runner for frozen Round 39 convergence rows."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import round39_common as common


LOCK = common.OUT / ".round39_runner.lock"
SUMMARY = common.OUT / "runner_row_summary.csv"
START_RECORD = common.OUT / "official_start_record.json"
SENSITIVE_MARKERS = (
    b"GRB_LICENSE_FILE", b"gurobi.lic", b"LicenseID", b"WLSAccessID",
    b"WLSSecret",
)


def artifact_inventory(directory: Path) -> list[dict[str, Any]]:
    output = []
    for path in sorted((item for item in directory.rglob("*") if item.is_file()),
                       key=lambda item: item.as_posix()):
        if path.name in {"artifact_manifest.csv", "completion_marker.json",
                          "run_state.json"}:
            continue
        output.append({
            "path": path.relative_to(directory).as_posix(),
            "bytes": path.stat().st_size, "sha256": common.sha256(path),
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
        "round_id": 39, "run_id": row["run_id"],
        "solver_source_commit": manifest["solver_source_commit"],
        "instance_sha256": item["sha256"],
        "executable_sha256": manifest["gurobi_executable_sha256"],
        "official_matrix_sha256": manifest["official_matrix_sha256"],
    }
    for key, value in expected.items():
        if marker.get(key) != value:
            return False, f"completion_identity_mismatch:{key}"
    if common.sha256(artifact_path) != marker.get("artifact_manifest_sha256"):
        return False, "artifact_manifest_checksum_mismatch"
    for artifact in artifacts:
        path = directory / artifact["path"]
        if (not path.is_file() or path.stat().st_size != int(artifact["bytes"])
                or common.sha256(path) != artifact["sha256"]):
            return False, f"artifact_checksum_mismatch:{artifact['path']}"
    return True, "checksum_valid_complete_row"


def scan_sensitive(directory: Path) -> None:
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        if any(marker.lower() in data.lower() for marker in SENSITIVE_MARKERS):
            raise RuntimeError(f"sensitive license marker detected in {path.name}")


def verification_passed(result: dict[str, Any]) -> bool:
    verification = result.get("verification", {})
    return bool(
        verification.get("original_solution_feasible")
        and verification.get("original_objective_recomputed")
        and verification.get("objective_matches")
        and not verification.get("errors")
    )


def strict_converged(arm: str, result: dict[str, Any]) -> bool:
    try:
        lower, upper = common.result_bounds(arm, result)
    except (KeyError, TypeError, ValueError):
        return False
    scale = max(1.0, abs(lower), abs(upper))
    lifecycle = bool(result.get(
        "external_gini_tree_lifecycle_complete" if arm.startswith("C6-")
        else "gurobi_lifecycle_valid"))
    return bool(
        math.isfinite(lower) and math.isfinite(upper)
        and lower <= upper + 1e-7 * scale
        and abs(upper - lower) <= 1e-7 * scale
        and result.get("strict_certified_original_problem") is True
        and result.get("strict_certificate_rejection_reason") == "none"
        and verification_passed(result) and lifecycle
    )


def validate_frozen(item: dict[str, Any], manifest: dict[str, Any]) -> None:
    artifact_keys = (
        "protocol", "generator_config", "instance_manifest",
        "descriptor_table", "rejected_manifest", "seed_manifest",
        "guard_manifest", "fingerprints", "official_matrix", "command_freeze",
    )
    for key in artifact_keys:
        path = common.ROOT / manifest[f"{key}_path"]
        if not path.is_file() or common.sha256(path) != manifest[f"{key}_sha256"]:
            raise RuntimeError(f"frozen artifact changed: {key}")
    for path_text, expected in manifest["source_file_sha256"].items():
        path = common.ROOT / path_text
        if not path.is_file() or common.sha256(path) != expected:
            raise RuntimeError(f"frozen source changed: {path_text}")
    if not common.EXE.is_file() or common.sha256(common.EXE) != manifest[
            "gurobi_executable_sha256"]:
        raise RuntimeError("official executable changed")
    path = common.item_path(item)
    if not path.is_file() or common.sha256(path) != item["sha256"]:
        raise RuntimeError(f"instance changed: {item['instance_id']}")
    if "GRB_LICENSE_FILE" not in os.environ:
        raise RuntimeError("licensed child environment is unavailable")


def run_record(row: dict[str, str], item: dict[str, Any],
               manifest: dict[str, Any], command: list[str]) -> dict[str, Any]:
    return {
        "schema": "round39-run-v1", "round_id": 39,
        "stage": row["stage"], "run_id": row["run_id"],
        "serial_order": int(row["serial_order"]),
        "instance_id": item["instance_id"], "instance_path": item["path"],
        "instance_sha256": item["sha256"], "V": item["V"],
        "M": item["M"], "Q": item["Q"], "T": item["T"],
        "difficulty_stratum": item["difficulty_stratum"],
        "arm": row["arm"], "startup_variant": row["startup_variant"],
        "solver": "Gurobi", "solver_version": "13.0.2", "threads": 1,
        "process_cap_seconds": int(row["process_cap_seconds"]),
        "watchdog_seconds": int(row["watchdog_seconds"]),
        "solver_source_commit": manifest["solver_source_commit"],
        "executable_sha256": manifest["gurobi_executable_sha256"],
        "official_matrix_sha256": manifest["official_matrix_sha256"],
        "instance_model_fingerprint": common.fingerprint_values()[
            item["instance_id"]],
        "primary_timing_field": "final_process_wall_time_seconds",
        "command": command,
        "license_environment": "inherited_by_solver_child_not_serialized",
        "algorithmic_solve_state_resumed": False, "completed": False,
    }


def invalidate(directory: Path, row: dict[str, str], reason: str) -> None:
    target = common.INVALIDATED / (
        f"{row['run_id']}__invalidated__{int(time.time() * 1000)}")
    common.INVALIDATED.mkdir(parents=True, exist_ok=True)
    if common.OUT.resolve() not in target.resolve().parents:
        raise RuntimeError(f"unsafe invalidation target: {target}")
    common.write_json(directory / "invalidation_record.json", {
        "round_id": 39, "run_id": row["run_id"], "reason": reason,
        "preserved_path": common.relative(target),
        "algorithmic_solve_state_resumed": False,
    })
    os.replace(directory, target)


def run_one(row: dict[str, str], items: dict[str, dict[str, Any]],
            manifest: dict[str, Any]) -> dict[str, Any]:
    item = items[row["instance_id"]]
    directory = common.RUNS / row["run_id"]
    if directory.exists():
        valid, reason = completion_valid(directory, row, item, manifest)
        if valid:
            marker = common.load_json(directory / "completion_marker.json")
            print(f"SKIP {row['serial_order']}/51 {row['run_id']}", flush=True)
            return marker
        invalidate(directory, row, reason)
    validate_frozen(item, manifest)
    directory.mkdir(parents=True, exist_ok=False)
    command = common.command_for(row, item, directory)
    frozen = common.load_json(common.COMMAND_FREEZE)["commands"][
        row["run_id"]]["command"]
    if command != frozen:
        raise RuntimeError(f"command changed after freeze: {row['run_id']}")
    record = run_record(row, item, manifest, command)
    common.write_json(directory / "command.json", record)
    common.write_json(directory / "run_state.json", {
        **record, "runner_state": "child_launch_pending"})
    started_wall, started = time.time(), time.monotonic()
    emergency_timeout = False
    with (directory / "console.stdout.log").open("wb") as stdout, \
         (directory / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=common.ROOT, env=os.environ.copy(), stdout=stdout,
                stderr=stderr, timeout=int(row["watchdog_seconds"]), check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
            emergency_timeout = True
    result_path = directory / "result.json"
    result: dict[str, Any] | None = None
    if result_path.is_file():
        try:
            result = common.load_json(result_path)
        except (OSError, ValueError, json.JSONDecodeError):
            result = None
    missing = [common.relative(path) for path in common.required_artifacts(
        row["arm"], directory) if not path.is_file()]
    record.update({
        "runner_started_unix_seconds": started_wall,
        "runner_finished_unix_seconds": time.time(),
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code, "emergency_timeout": emergency_timeout,
        "result_json_parse_verified_after_process_exit": result is not None,
        "missing_required_artifacts": missing,
    })
    if result is not None:
        lower, upper = common.result_bounds(row["arm"], result)
        record.update({
            "status": result.get("status"), "objective": result.get("objective"),
            "valid_lower_bound": lower, "verified_upper_bound": upper,
            "gap": max(0.0, (upper - lower) / max(1e-12, abs(upper))),
            "strict_certified_original_problem": result.get(
                "strict_certified_original_problem"),
            "strict_certificate_class": result.get("strict_certificate_class", ""),
            "strict_certificate_rejection_reason": result.get(
                "strict_certificate_rejection_reason", ""),
            "process_entry_time_seconds": common.process_entry_time(result),
            "reported_startup_variant": result.get(
                "external_gini_tree_startup_variant", "not_applicable"),
            "strict_convergence_gate_passed": strict_converged(row["arm"], result),
        })
    finalized = bool(
        not emergency_timeout and return_code == 0 and result is not None
        and not missing and strict_converged(row["arm"], result))
    if not finalized:
        common.write_json(directory / "run_state.json", {
            **record, "runner_state": "incomplete_preserved_requires_extension"})
        raise RuntimeError(
            f"official row did not converge strictly: {row['run_id']} "
            f"rc={return_code} timeout={emergency_timeout} missing={len(missing)} "
            f"strict={record.get('strict_convergence_gate_passed')}")
    scan_sensitive(directory)
    artifacts = artifact_inventory(directory)
    artifact_path = directory / "artifact_manifest.csv"
    common.write_csv(artifact_path, artifacts, ["path", "bytes", "sha256"])
    marker = {
        **record, "artifact_count": len(artifacts),
        "artifact_manifest_sha256": common.sha256(artifact_path),
        "result_sha256": common.sha256(result_path), "completed": True,
        "completion_marker_atomic": True,
        "completed_at_unix_seconds": time.time(),
    }
    common.write_json(directory / "completion_marker.json", marker)
    common.write_json(directory / "run_state.json", {
        **marker, "runner_state": "checksum_valid_strict_convergence"})
    print(
        f"DONE {row['serial_order']}/51 {row['run_id']} "
        f"time={record.get('process_entry_time_seconds'):.3f}", flush=True)
    return marker


def acquire_lock() -> None:
    if LOCK.exists():
        try:
            record = common.load_json(LOCK)
            os.kill(int(record.get("pid", 0)), 0)
            raise RuntimeError("another Round 39 runner is active")
        except OSError:
            LOCK.unlink(missing_ok=True)
        except (ValueError, json.JSONDecodeError):
            LOCK.unlink(missing_ok=True)
    common.write_json(LOCK, {"pid": os.getpid(), "created": time.time()})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", action="append", choices=("primary", "guard"))
    parser.add_argument("--stratum", action="append", choices=(
        "small-easy", "small-medium", "small-hard"))
    parser.add_argument("--run-id", action="append")
    args = parser.parse_args()
    manifest = common.load_json(common.FROZEN_MANIFEST)
    items = common.inventory()
    rows = common.csv_rows(common.OFFICIAL_MATRIX)
    if args.stage:
        rows = [row for row in rows if row["stage"] in set(args.stage)]
    if args.stratum:
        rows = [row for row in rows
                if row["difficulty_stratum"] in set(args.stratum)]
    if args.run_id:
        rows = [row for row in rows if row["run_id"] in set(args.run_id)]
    rows.sort(key=lambda row: int(row["serial_order"]))
    acquire_lock()
    common.RUNS.mkdir(parents=True, exist_ok=True)
    if not START_RECORD.is_file():
        common.write_json(START_RECORD, {
            "schema": "round39-official-start-v1", "round_id": 39,
            "started_at_unix_seconds": time.time(),
            "solver_source_commit": manifest["solver_source_commit"],
            "executable_sha256": manifest["gurobi_executable_sha256"],
            "official_matrix_sha256": manifest["official_matrix_sha256"],
            "frozen_before_official_results": True,
        })
    summaries = common.csv_rows(SUMMARY) if SUMMARY.is_file() else []
    keyed = {row["run_id"]: row for row in summaries}
    try:
        for row in rows:
            marker = run_one(row, items, manifest)
            keyed[row["run_id"]] = marker
            common.write_csv(SUMMARY, sorted(
                keyed.values(), key=lambda item: int(item["serial_order"])))
    finally:
        LOCK.unlink(missing_ok=True)
    print(json.dumps({
        "selected_rows": len(rows), "completed_rows": len(keyed),
        "strict_rows": sum(str(row.get(
            "strict_certified_original_problem")).lower() == "true"
            for row in keyed.values()),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
