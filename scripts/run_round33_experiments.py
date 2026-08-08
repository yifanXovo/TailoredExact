#!/usr/bin/env python3
"""Checksum-resumable serial runner for frozen Round 33 experiments.

The Gurobi license location is inherited only by licensed solver children.
This module never opens, reads, copies, hashes, prints, or serializes the
license file or its location. Resume is row-level experiment resume only.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable

import round33_common as common


LOCK = common.OUT / ".round33_runner.lock"
SUMMARY = common.OUT / "runner_row_summary.csv"
INVALIDATION_LOG = common.OUT / "runner_invalidations.csv"
START_RECORD = common.OUT / "official_start_record.json"
SENSITIVE_MARKERS = (
    b"GRB_LICENSE_FILE",
    b"gurobi.lic",
    b"LicenseID",
    b"WLSAccessID",
    b"WLSSecret",
)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: Iterable[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    material = list(rows)
    if not material:
        return
    columns = fields or list(material[0])
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def artifact_inventory(directory: Path) -> list[dict[str, Any]]:
    output = []
    for path in sorted(
            (item for item in directory.rglob("*") if item.is_file()),
            key=lambda item: item.as_posix()):
        if path.name in {
                "artifact_manifest.csv", "completion_marker.json",
                "run_state.json"}:
            continue
        output.append({
            "path": path.relative_to(directory).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": common.sha256(path),
        })
    return output


def restored_hash(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with gzip.open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return size, digest.hexdigest()


def completion_valid(directory: Path, row: dict[str, str],
                     item: dict[str, Any], manifest: dict[str, Any]
                     ) -> tuple[bool, str]:
    marker_path = directory / "completion_marker.json"
    if not marker_path.is_file():
        return False, "completion_marker_missing"
    try:
        marker = common.load_json(marker_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return False, "completion_marker_unparseable"
    expected = {
        "round_id": 33,
        "run_id": row["run_id"],
        "source_commit": manifest["source_commit"],
        "protocol_sha256": manifest["protocol_sha256"],
        "instance_sha256": item["sha256"],
        "executable_sha256": manifest["gurobi_executable_sha256"],
    }
    for key, value in expected.items():
        if marker.get(key) != value:
            return False, f"completion_identity_mismatch:{key}"
    artifact_path = directory / "artifact_manifest.csv"
    if (
        not artifact_path.is_file()
        or common.sha256(artifact_path) !=
            marker.get("artifact_manifest_sha256")
    ):
        return False, "artifact_manifest_checksum_mismatch"
    try:
        artifacts = common.csv_rows(artifact_path)
    except (OSError, UnicodeError, csv.Error):
        return False, "artifact_manifest_unparseable"
    for artifact in artifacts:
        path = directory / artifact["path"]
        if path.is_file():
            valid = (
                path.stat().st_size == int(artifact["bytes"])
                and common.sha256(path) == artifact["sha256"])
        else:
            compressed = Path(str(path) + ".gz")
            valid = False
            if compressed.is_file():
                try:
                    size, digest = restored_hash(compressed)
                    valid = (
                        size == int(artifact["bytes"])
                        and digest == artifact["sha256"])
                except (OSError, EOFError):
                    valid = False
        if not valid:
            return False, f"artifact_checksum_mismatch:{artifact['path']}"
    try:
        common.load_json(directory / "result.json")
    except (OSError, ValueError, json.JSONDecodeError):
        return False, "result_json_unparseable_after_completion"
    return True, "checksum_valid_complete_row"


def next_invalidation(run_id: str) -> Path:
    common.INVALIDATED.mkdir(parents=True, exist_ok=True)
    index = 1
    while True:
        target = common.INVALIDATED / f"{run_id}__invalidated{index:03d}"
        if not target.exists():
            return target
        index += 1


def invalidate(directory: Path, row: dict[str, str], reason: str) -> None:
    target = next_invalidation(row["run_id"])
    if common.OUT.resolve() not in target.resolve().parents:
        raise RuntimeError(f"unsafe invalidation target: {target}")
    record = {
        "round_id": 33,
        "run_id": row["run_id"],
        "stage_id": row["stage_id"],
        "reason": reason,
        "source_path": common.relative(directory),
        "preserved_path": common.relative(target),
        "invalidated_at_unix_seconds": f"{time.time():.6f}",
        "algorithmic_solve_state_resumed": False,
    }
    write_json(directory / "invalidation_record.json", record)
    os.replace(directory, target)
    history = (
        common.csv_rows(INVALIDATION_LOG)
        if INVALIDATION_LOG.is_file() else [])
    history.append(record)
    write_csv(INVALIDATION_LOG, history, list(history[0]))


def validate_frozen(item: dict[str, Any], manifest: dict[str, Any]) -> None:
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=common.ROOT,
        text=True).strip()
    if head != manifest["source_commit"]:
        raise RuntimeError("source HEAD changed after Round 33 freeze")
    for key in (
        "protocol", "v10_instance_manifest", "v12_anchor_manifest",
        "fingerprints", "certificate_preflight", "official_matrix",
        "repeatability_freeze", "stage0_matrix",
    ):
        path = common.ROOT / manifest[f"{key}_path"]
        if common.sha256(path) != manifest[f"{key}_sha256"]:
            raise RuntimeError(f"frozen artifact changed: {key}")
    for path_text, expected in manifest["source_file_sha256"].items():
        if common.sha256(common.ROOT / path_text) != expected:
            raise RuntimeError(f"frozen source changed: {path_text}")
    if (
        not common.EXE.is_file()
        or common.sha256(common.EXE) !=
            manifest["gurobi_executable_sha256"]
    ):
        raise RuntimeError("official Gurobi executable changed")
    path = common.instance_path(item)
    if not path.is_file() or common.sha256(path) != item["sha256"]:
        raise RuntimeError(f"frozen instance changed: {item['instance_id']}")
    if "GRB_LICENSE_FILE" not in os.environ:
        raise RuntimeError("licensed child environment is unavailable")


def scan_sensitive(directory: Path) -> None:
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        if any(marker.lower() in data.lower() for marker in SENSITIVE_MARKERS):
            raise RuntimeError(
                f"sensitive license marker detected in {path.name}")


def run_record(row: dict[str, str], item: dict[str, Any],
               manifest: dict[str, Any], command: list[str]) -> dict[str, Any]:
    return {
        "schema": "round33-run-v1",
        "round_id": 33,
        "stage_id": row["stage_id"],
        "run_id": row["run_id"],
        "instance_id": item["instance_id"],
        "instance_path": item["path"],
        "instance_sha256": item["sha256"],
        "scenario": item["scenario"],
        "family": item["family"],
        "V": item["V"],
        "M": item["M"],
        "Q": item["Q"],
        "T": item["T"],
        "lambda": item["lambda"],
        "nominal_process_cap_seconds": int(
            row["nominal_process_cap_seconds"]),
        "actual_process_cap_seconds": int(row["actual_process_cap_seconds"]),
        "shutdown_margin_seconds": int(row["shutdown_margin_seconds"]),
        "emergency_watchdog_seconds": int(
            row["emergency_watchdog_seconds"]),
        "arm": row["arm"],
        "solver": "Gurobi",
        "solver_version": "13.0.2",
        "executable_sha256": common.sha256(common.EXE),
        "source_commit": manifest["source_commit"],
        "protocol_sha256": manifest["protocol_sha256"],
        "model_fingerprint": common.fingerprint_values()[item["instance_id"]],
        "primary_timing_field": "final_process_wall_time_seconds",
        "repetition": row["repetition"],
        "serial_order": int(row["serial_order"]),
        "command": command,
        "license_environment":
            "inherited_by_licensed_solver_child_not_serialized",
        "algorithmic_solve_state_resumed": False,
        "completed": False,
    }


def ensure_start_record(manifest: dict[str, Any]) -> None:
    if START_RECORD.is_file():
        record = common.load_json(START_RECORD)
        if (
            record.get("source_commit") != manifest["source_commit"]
            or record.get("official_matrix_sha256") !=
                manifest["official_matrix_sha256"]
        ):
            raise RuntimeError("official start record identity mismatch")
        return
    write_json(START_RECORD, {
        "schema": "round33-official-start-v1",
        "round_id": 33,
        "started_at_unix_seconds": time.time(),
        "source_commit": manifest["source_commit"],
        "protocol_sha256": manifest["protocol_sha256"],
        "official_matrix_sha256": manifest["official_matrix_sha256"],
        "gurobi_executable_sha256":
            manifest["gurobi_executable_sha256"],
        "fingerprints_sha256": manifest["fingerprints_sha256"],
        "frozen_before_official_results": True,
    })


def run_one(row: dict[str, str], items: dict[str, dict[str, Any]],
            manifest: dict[str, Any]) -> dict[str, Any]:
    item = items[row["instance_id"]]
    directory = common.RUNS / row["run_id"]
    if directory.exists():
        valid, reason = completion_valid(directory, row, item, manifest)
        if valid:
            marker = common.load_json(directory / "completion_marker.json")
            print(f"SKIP {row['run_id']} checksum-valid", flush=True)
            return marker
        invalidate(directory, row, reason)
    validate_frozen(item, manifest)
    ensure_start_record(manifest)
    directory.mkdir(parents=True, exist_ok=False)
    command = common.command_for(item, row["arm"], directory)
    record = run_record(row, item, manifest, command)
    write_json(directory / "command.json", record)
    write_json(directory / "run_state.json", {
        **record, "runner_state": "child_launch_pending"})
    started_wall = time.time()
    started_monotonic = time.monotonic()
    emergency_timeout = False
    return_code = 125
    with (directory / "console.stdout.log").open("wb") as stdout, \
         (directory / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=common.ROOT, env=os.environ.copy(),
                stdout=stdout, stderr=stderr,
                timeout=int(row["emergency_watchdog_seconds"]),
                check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
            emergency_timeout = True
        stdout.flush()
        os.fsync(stdout.fileno())
        stderr.flush()
        os.fsync(stderr.fileno())
    finished_wall = time.time()
    result_path = directory / "result.json"
    result: dict[str, Any] | None = None
    result_error = ""
    if result_path.is_file():
        try:
            result = common.load_json(result_path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            result_error = f"{type(error).__name__}:{error}"
    else:
        result_error = "result_json_missing"
    missing = [
        common.relative(path)
        for path in common.required_artifacts(row["arm"], directory)
        if not path.is_file()
    ]
    record.update({
        "runner_started_unix_seconds": started_wall,
        "runner_finished_unix_seconds": finished_wall,
        "runner_wall_seconds": time.monotonic() - started_monotonic,
        "return_code": return_code,
        "emergency_timeout": emergency_timeout,
        "result_json_parse_verified_after_process_exit": result is not None,
        "result_json_flush_verified_after_process_exit": result is not None,
        "result_error": result_error,
        "missing_required_artifacts": missing,
        "completed": False,
    })
    if result is not None:
        record.update({
            "status": result.get("status"),
            "objective": result.get("objective"),
            "lower_bound": result.get("lower_bound"),
            "upper_bound": result.get("upper_bound"),
            "strict_certified_original_problem":
                result.get("strict_certified_original_problem"),
            "process_entry_time_seconds":
                common.process_entry_time(result),
            "strict_certificate_class":
                result.get("strict_certificate_class", ""),
            "strict_certificate_rejection_reason":
                result.get("strict_certificate_rejection_reason", ""),
        })
    finalized = (
        not emergency_timeout
        and result is not None
        and not missing
    )
    if not finalized:
        write_json(directory / "run_state.json", {
            **record,
            "runner_state": "incomplete_preserved_requires_invalidation",
        })
        print(
            f"INCOMPLETE {row['run_id']} rc={return_code} "
            f"timeout={emergency_timeout} missing={len(missing)}",
            flush=True)
        return record
    scan_sensitive(directory)
    artifact_rows = artifact_inventory(directory)
    artifact_path = directory / "artifact_manifest.csv"
    write_csv(artifact_path, artifact_rows, ["path", "bytes", "sha256"])
    marker = {
        **record,
        "artifact_count": len(artifact_rows),
        "artifact_manifest_sha256": common.sha256(artifact_path),
        "result_sha256": common.sha256(result_path),
        "completed": True,
        "completion_marker_atomic": True,
        "completed_at_unix_seconds": time.time(),
        "run_status": (
            "completed_valid_result"
            if return_code == 0 else "completed_solver_failure_result"),
    }
    write_json(directory / "run_state.json", {
        **marker, "runner_state": "completion_marker_pending"})
    write_json(directory / "completion_marker.json", marker)
    write_json(directory / "run_state.json", {
        **marker, "runner_state": "checksum_valid_complete"})
    print(
        f"DONE {row['run_id']} rc={return_code} "
        f"status={record.get('status')} "
        f"time={record.get('process_entry_time_seconds')}", flush=True)
    return marker


def pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def acquire_lock(stages: list[str]) -> None:
    if LOCK.exists():
        try:
            old = common.load_json(LOCK)
        except (OSError, ValueError, json.JSONDecodeError):
            old = {}
        if pid_running(int(old.get("pid", -1))):
            raise RuntimeError("Round 33 serial runner is already active")
        stale = common.OUT / "runner_logs" / (
            f"stale_lock_{int(time.time())}.json")
        stale.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LOCK, stale)
        LOCK.unlink()
    descriptor = os.open(LOCK, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        data = json.dumps({
            "pid": os.getpid(),
            "stages": stages,
            "created_at_unix_seconds": time.time(),
        }, sort_keys=True) + "\n"
        os.write(descriptor, data.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def update_summary() -> None:
    output = []
    for marker_path in sorted(common.RUNS.glob("*/completion_marker.json")):
        marker = common.load_json(marker_path)
        output.append({
            key: marker.get(key, "")
            for key in (
                "round_id", "stage_id", "run_id", "instance_id",
                "scenario", "V", "M", "Q", "arm", "solver_version",
                "instance_sha256", "executable_sha256", "source_commit",
                "protocol_sha256", "nominal_process_cap_seconds",
                "actual_process_cap_seconds", "return_code",
                "emergency_timeout", "status", "objective", "lower_bound",
                "upper_bound", "strict_certified_original_problem",
                "process_entry_time_seconds", "run_status", "completed",
            )
        })
    if output:
        write_csv(SUMMARY, output, list(output[0]))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stages", default="stage1,stage2,stage3")
    parser.add_argument("--max-rows", type=int)
    args = parser.parse_args()
    if not common.MANIFEST.is_file():
        raise SystemExit("Round 33 frozen manifest is unavailable")
    manifest = common.load_json(common.MANIFEST)
    items = common.inventory()
    stages = {item for item in args.stages.split(",") if item}
    selected = [
        row for row in common.csv_rows(common.MATRIX)
        if row["stage_id"] in stages
    ]
    if args.max_rows is not None:
        selected = selected[:args.max_rows]
    acquire_lock(sorted(stages))
    incomplete = 0
    failures = 0
    try:
        for row in selected:
            state = run_one(row, items, manifest)
            incomplete += int(not state.get("completed", False))
            failures += int(
                state.get("completed", False)
                and int(state.get("return_code", 1)) != 0)
            update_summary()
    finally:
        LOCK.unlink(missing_ok=True)
    print(json.dumps({
        "selected_rows": len(selected),
        "incomplete_rows": incomplete,
        "completed_solver_failure_rows": failures,
        "experiment_row_resume": True,
        "algorithmic_solve_state_resume": False,
    }, indent=2), flush=True)
    return 1 if incomplete else 0


if __name__ == "__main__":
    raise SystemExit(main())
