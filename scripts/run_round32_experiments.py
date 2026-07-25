#!/usr/bin/env python3
"""Checksum-resumable serial runner for frozen Round 32 experiments.

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
import sys
import time
from pathlib import Path
from typing import Any, Iterable

import run_round28_experiments as r28
import run_round31_experiments as r31


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_long_run_validation_round32"
RUNS = OUT / "runs"
STAGE0_RUNS = OUT / "stage0_runs"
INVALIDATED = OUT / "invalidated_rows"
MANIFEST = OUT / "round32_frozen_manifest.json"
OFFICIAL_MATRIX = OUT / "round32_official_matrix.csv"
STAGE0_MATRIX = OUT / "round32_stage0_matrix.csv"
EXISTING_MANIFEST = OUT / "round32_existing_instance_manifest.csv"
MULTI_MANIFEST = OUT / "round32_multi_m_manifest.csv"
GUROBI_EXE = ROOT / "build_round32" / "official" / "gurobi" / "ExactEBRP.exe"
CPLEX_EXE = ROOT / "build_round32" / "official" / "cplex" / "ExactEBRP.exe"
GLOBAL_LOCK = OUT / ".round32_runner.lock"
SUMMARY = OUT / "runner_row_summary.csv"
INVALIDATION_LOG = OUT / "runner_invalidations.csv"
SHUTDOWN_MARGIN = 15
WATCHDOG_SEPARATION = 90


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_json_atomic(path: Path, value: Any) -> None:
    write_text_atomic(
        path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv_atomic(path: Path, rows: Iterable[dict[str, Any]],
                     fields: list[str] | None = None) -> None:
    material = list(rows)
    if not material:
        return
    columns = fields or list(material[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def add(args: list[str], name: str, value: object) -> None:
    args.extend((
        name, str(value).lower() if isinstance(value, bool) else str(value)))


def replace_option(args: list[str], name: str, value: object) -> None:
    try:
        index = args.index(name)
    except ValueError as error:
        raise RuntimeError(f"frozen option is missing: {name}") from error
    if index + 1 >= len(args):
        raise RuntimeError(f"frozen option has no value: {name}")
    args[index + 1] = str(value).lower() if isinstance(value, bool) else str(value)


def inventory() -> dict[str, dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}
    for row in csv_rows(EXISTING_MANIFEST):
        items[row["instance_id"]] = {
            "instance_id": row["instance_id"],
            "path": row["path"],
            "sha256": row["instance_sha256"],
            "family": row["family"],
            "V": int(row["V"]),
            "M": int(row["M"]),
            "Q": int(row["Q"]),
            "T": float(row["T"]),
            "lambda": float(row["lambda"]),
            "origin": row["origin"],
        }
    for row in csv_rows(MULTI_MANIFEST):
        items[row["instance_id"]] = {
            "instance_id": row["instance_id"],
            "path": row["path"],
            "sha256": row["sha256"],
            "family": row["stress_type"],
            "V": int(row["V"]),
            "M": int(row["M"]),
            "Q": int(row["Q"]),
            "T": float(row["T"]),
            "lambda": float(row["lambda"]),
            "origin": "round32_multi_m",
        }
    for name in ("toy", "moderate_seed4301"):
        path, family, v, m, expected = r28.INSTANCES[name]
        items[name] = {
            "instance_id": name,
            "path": path,
            "sha256": expected,
            "family": family,
            "V": v,
            "M": m,
            "Q": 30,
            "T": 3600.0,
            "lambda": 0.15,
            "origin": "stage0_sentinel",
        }
    return items


def instance_path(item: dict[str, Any]) -> Path:
    return ROOT / item["path"]


def executable_for(arm: str) -> Path:
    return CPLEX_EXE if arm == "S0-CPLEX" else GUROBI_EXE


def tailored_options(run_dir: Path, budget: int,
                     item: dict[str, Any]) -> list[str]:
    args = r31.tailored_options(run_dir, budget)
    replace_option(args, "--lambda", item["lambda"])
    replace_option(args, "--T", item["T"])
    replace_option(args, "--time-limit", budget)
    replace_option(args, "--process-wall-time-limit", budget)
    replace_option(args, "--process-shutdown-margin", SHUTDOWN_MARGIN)
    return args


def plain_command(item: dict[str, Any], budget: int,
                  run_dir: Path) -> list[str]:
    args = [str(GUROBI_EXE), "--input", str(instance_path(item))]
    for name, value in (
        ("--method", "gurobi"),
        ("--lambda", item["lambda"]),
        ("--T", item["T"]),
        ("--time-limit", budget),
        ("--process-wall-time-limit", budget),
        ("--process-shutdown-margin", SHUTDOWN_MARGIN),
        ("--process-phase-ledger", run_dir / "process_phases.csv"),
        ("--threads", 1),
        ("--mip-threads", 1),
        ("--cplex-threads", 1),
        ("--compact-bc-threads", 1),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0),
        ("--gurobi-presolve", -1),
        ("--gurobi-model-export", run_dir / "canonical.lp"),
        ("--gurobi-progress", run_dir / "progress.csv"),
        ("--round24-executable-sha256", sha256(GUROBI_EXE)),
        ("--round24-manifest-executable-sha256", sha256(GUROBI_EXE)),
        ("--round24-expected-gurobi-model-fingerprint",
         r28.merged_fingerprints().get(item["instance_id"], 0)),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    args.append("--plain-baseline")
    return args


def external_command(item: dict[str, Any], arm: str, budget: int,
                     run_dir: Path) -> list[str]:
    args = [str(GUROBI_EXE), "--input", str(instance_path(item))]
    args.extend(tailored_options(run_dir, budget, item))
    scheduling = {
        "C5-REFERENCE": "round30-dual-bound-target",
        "C6-FROZEN": "round31-nonblocking-native-bound",
    }[arm]
    lifecycle = {
        "C5-REFERENCE": "round30-same-leaf-bound-target",
        "C6-FROZEN": "round31-open-native-bounded",
    }[arm]
    for name, value in (
        ("--frontier-execution-mode", "external-gini-tree"),
        ("--external-gini-scheduling", scheduling),
        ("--external-gini-artifact-dir", run_dir / "external"),
        ("--external-gini-backend", "gurobi"),
        ("--external-gini-lifecycle", lifecycle),
        ("--external-gini-warm-start", False),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0),
        ("--gurobi-presolve", -1),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    return args


def s0_command(item: dict[str, Any], budget: int,
               run_dir: Path) -> list[str]:
    args = [str(CPLEX_EXE), "--input", str(instance_path(item))]
    args.extend(r31.r29.tailored_options(
        run_dir, budget, local_redecode=True))
    replace_option(args, "--lambda", item["lambda"])
    replace_option(args, "--T", item["T"])
    replace_option(args, "--time-limit", budget)
    replace_option(args, "--process-wall-time-limit", budget)
    replace_option(args, "--process-shutdown-margin", SHUTDOWN_MARGIN)
    add(args, "--paper-run-sealed", True)
    for name, value in (
        ("--frontier-execution-mode", "global-gini-tree"),
        ("--global-gini-tree-node-trace", run_dir / "global_node_trace.csv"),
        ("--global-gini-tree-bound-trace",
         run_dir / "global_bound_trajectory.csv"),
        ("--global-gini-tree-manifest",
         run_dir / "model_lifecycle_manifest.csv"),
        ("--global-gini-tree-root-export", run_dir / "global_root.lp"),
        ("--global-gini-tree-post-row-trace", run_dir / "post_rows.csv"),
        ("--global-gini-tree-topology-trace", run_dir / "gini_topology.csv"),
        ("--global-gini-tree-sibling-trace", run_dir / "sibling_delay.csv"),
        ("--global-gini-tree-row-delta-trace", run_dir / "row_delta.csv"),
        ("--global-gini-tree-memory-trace", run_dir / "tree_memory.csv"),
        ("--global-gini-tree-mip-start-audit",
         run_dir / "mip_start_audit.csv"),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    return args


def command_for(item: dict[str, Any], arm: str, budget: int,
                run_dir: Path) -> list[str]:
    if arm == "P-GRB":
        return plain_command(item, budget, run_dir)
    if arm in {"C5-REFERENCE", "C6-FROZEN"}:
        return external_command(item, arm, budget, run_dir)
    if arm == "S0-CPLEX":
        return s0_command(item, budget, run_dir)
    raise ValueError(f"unknown Round 32 arm: {arm}")


def required_artifacts(arm: str, run_dir: Path) -> list[Path]:
    common = [
        run_dir / "command.json",
        run_dir / "result.json",
        run_dir / "process_phases.csv",
    ]
    if arm == "P-GRB":
        return common + [run_dir / "progress.csv"]
    if arm == "S0-CPLEX":
        return common + [run_dir / "global_bound_trajectory.csv"]
    return common + [
        run_dir / "external" / "global_bound_trace.csv",
        run_dir / "external" / "paper_leaf_ledger.csv",
        run_dir / "external" / "paper_optimize_ledger.csv",
        run_dir / "external" / "split_decision_ledger.csv",
        run_dir / "external" / "native_target_ledger.csv",
    ]


def artifact_inventory(run_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(
            (item for item in run_dir.rglob("*") if item.is_file()),
            key=lambda item: item.as_posix()):
        if path.name in {
                "artifact_manifest.csv", "completion_marker.json",
                "run_state.json"}:
            continue
        rows.append({
            "path": path.relative_to(run_dir).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    return rows


def completion_is_valid(run_dir: Path, row: dict[str, str],
                        item: dict[str, Any],
                        manifest: dict[str, Any]) -> tuple[bool, str]:
    marker_path = run_dir / "completion_marker.json"
    if not marker_path.is_file():
        return False, "completion_marker_missing"
    try:
        marker = load_json(marker_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return False, "completion_marker_unparseable"
    expected = {
        "run_id": row["run_id"],
        "source_commit": manifest["source_commit"],
        "protocol_sha256": manifest["protocol_sha256"],
        "instance_sha256": item["sha256"],
        "executable_sha256":
            manifest["cplex_executable_sha256"]
            if row["arm"] == "S0-CPLEX"
            else manifest["gurobi_executable_sha256"],
    }
    for key, value in expected.items():
        if marker.get(key) != value:
            return False, f"completion_identity_mismatch:{key}"
    item_manifest = run_dir / "artifact_manifest.csv"
    if (
        not item_manifest.is_file()
        or sha256(item_manifest) != marker.get("artifact_manifest_sha256")
    ):
        return False, "artifact_manifest_checksum_mismatch"
    try:
        artifact_rows = csv_rows(item_manifest)
    except (OSError, UnicodeError, csv.Error):
        return False, "artifact_manifest_unparseable"
    for item in artifact_rows:
        path = run_dir / item["path"]
        if path.is_file():
            valid = (
                path.stat().st_size == int(item["bytes"])
                and sha256(path) == item["sha256"])
        else:
            compressed = Path(str(path) + ".gz")
            valid = False
            if compressed.is_file():
                restored = hashlib.sha256()
                restored_bytes = 0
                try:
                    with gzip.open(compressed, "rb") as stream:
                        for block in iter(
                                lambda: stream.read(1024 * 1024), b""):
                            restored.update(block)
                            restored_bytes += len(block)
                    valid = (
                        restored_bytes == int(item["bytes"])
                        and restored.hexdigest() == item["sha256"])
                except (OSError, EOFError):
                    valid = False
        if not valid:
            return False, f"artifact_checksum_mismatch:{item['path']}"
    try:
        load_json(run_dir / "result.json")
    except (OSError, ValueError, json.JSONDecodeError):
        return False, "result_json_unparseable_after_completion"
    return True, "checksum_valid_complete_row"


def next_invalidation_target(run_id: str) -> Path:
    INVALIDATED.mkdir(parents=True, exist_ok=True)
    index = 1
    while True:
        candidate = INVALIDATED / f"{run_id}__invalidated{index:03d}"
        if not candidate.exists():
            return candidate
        index += 1


def append_invalidation(record: dict[str, Any]) -> None:
    rows = csv_rows(INVALIDATION_LOG) if INVALIDATION_LOG.is_file() else []
    rows.append({key: str(value) for key, value in record.items()})
    write_csv_atomic(INVALIDATION_LOG, rows, list(rows[0]))


def invalidate_run(run_dir: Path, row: dict[str, str], reason: str) -> None:
    target = next_invalidation_target(row["run_id"])
    if OUT.resolve() not in target.resolve().parents:
        raise RuntimeError(f"unsafe invalidation target: {target}")
    record = {
        "round_id": 32,
        "run_id": row["run_id"],
        "stage_id": row["stage_id"],
        "reason": reason,
        "source_path": relative(run_dir),
        "preserved_path": relative(target),
        "invalidated_at_unix_seconds": f"{time.time():.6f}",
        "algorithmic_solve_state_resumed": "false",
    }
    write_json_atomic(run_dir / "invalidation_record.json", record)
    os.replace(run_dir, target)
    append_invalidation(record)


def validate_frozen(item: dict[str, Any], arm: str,
                    manifest: dict[str, Any]) -> None:
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=ROOT, text=True).strip()
    if head != manifest["source_commit"]:
        raise RuntimeError("source HEAD changed after Round 32 freeze")
    for key in (
        "protocol", "existing_instance_manifest", "multi_m_manifest",
        "stage3_freeze", "official_matrix", "stage0_matrix",
    ):
        path = ROOT / manifest[f"{key}_path"]
        if sha256(path) != manifest[f"{key}_sha256"]:
            raise RuntimeError(f"frozen artifact changed: {key}")
    for path_text, expected in manifest["source_file_sha256"].items():
        if sha256(ROOT / path_text) != expected:
            raise RuntimeError(f"frozen source changed: {path_text}")
    executable = executable_for(arm)
    expected_exe = (
        manifest["cplex_executable_sha256"]
        if arm == "S0-CPLEX"
        else manifest["gurobi_executable_sha256"])
    if not executable.is_file() or sha256(executable) != expected_exe:
        raise RuntimeError(f"official executable changed: {arm}")
    path = instance_path(item)
    if not path.is_file() or sha256(path) != item["sha256"]:
        raise RuntimeError(f"frozen instance changed: {item['instance_id']}")
    if arm != "S0-CPLEX" and "GRB_LICENSE_FILE" not in os.environ:
        raise RuntimeError("licensed child environment is unavailable")


def row_record(row: dict[str, str], item: dict[str, Any],
               manifest: dict[str, Any], command: list[str]) -> dict[str, Any]:
    arm = row["arm"]
    budget = int(row["nominal_budget_seconds"])
    record = {
        "schema": "round32-run-v1",
        "round_id": 32,
        "stage_id": row["stage_id"],
        "run_id": row["run_id"],
        "instance_id": item["instance_id"],
        "instance_path": item["path"],
        "instance_sha256": item["sha256"],
        "family": item["family"],
        "V": item["V"],
        "M": item["M"],
        "Q": item["Q"],
        "T": item["T"],
        "lambda": item["lambda"],
        "nominal_budget_seconds": budget,
        "actual_process_cap_seconds": int(
            row["actual_process_cap_seconds"]),
        "shutdown_margin_seconds": int(row["shutdown_margin_seconds"]),
        "emergency_watchdog_seconds": int(
            row["emergency_watchdog_seconds"]),
        "arm": arm,
        "solver": "CPLEX" if arm == "S0-CPLEX" else "Gurobi",
        "solver_version": "22.1.1" if arm == "S0-CPLEX" else "13.0.2",
        "executable_sha256": sha256(executable_for(arm)),
        "source_commit": manifest["source_commit"],
        "protocol_sha256": manifest["protocol_sha256"],
        "command": command,
        "license_environment": (
            "inherited_by_licensed_solver_child_not_serialized"
            if arm != "S0-CPLEX" else "not_required"),
        "algorithmic_solve_state_resumed": False,
        "completed": False,
    }
    # Preserve every frozen matrix discriminator needed to reconstruct a row
    # without inferring it from a run-id string. These values are evidence
    # metadata only and never enter the solver command.
    for key in (
        "suite", "baseline_round31_run_id", "repetition", "category",
        "serial_order", "frozen_before_stage0_results",
        "frozen_before_official_results",
    ):
        if key in row:
            record[key] = row[key]
    return record


def run_one(row: dict[str, str], items: dict[str, dict[str, Any]],
            manifest: dict[str, Any], runs_root: Path) -> dict[str, Any]:
    item = items[row["instance_id"]]
    run_dir = runs_root / row["run_id"]
    if run_dir.exists():
        valid, reason = completion_is_valid(
            run_dir, row, item, manifest)
        if valid:
            marker = load_json(run_dir / "completion_marker.json")
            print(f"SKIP {row['run_id']} checksum-valid", flush=True)
            return marker
        invalidate_run(run_dir, row, reason)
    validate_frozen(item, row["arm"], manifest)
    run_dir.mkdir(parents=True, exist_ok=False)
    budget = int(row["nominal_budget_seconds"])
    command = command_for(item, row["arm"], budget, run_dir)
    record = row_record(row, item, manifest, command)
    write_json_atomic(run_dir / "command.json", record)
    write_json_atomic(run_dir / "run_state.json", {
        **record,
        "runner_state": "child_launch_pending",
    })
    environment = os.environ.copy()
    if row["arm"] == "S0-CPLEX":
        environment.pop("GRB_LICENSE_FILE", None)
    started_wall = time.time()
    started_monotonic = time.monotonic()
    emergency_timeout = False
    return_code = 125
    with (run_dir / "console.stdout.log").open("wb") as stdout, \
         (run_dir / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=environment,
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
    result_path = run_dir / "result.json"
    result: dict[str, Any] | None = None
    result_error = ""
    if result_path.is_file():
        try:
            result = load_json(result_path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            result_error = f"{type(error).__name__}:{error}"
    else:
        result_error = "result_json_missing"
    missing = [
        relative(path) for path in required_artifacts(row["arm"], run_dir)
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
            "failure_reason": result.get(
                "external_gini_tree_failure_reason",
                result.get("gurobi_failure_reason", "")),
        })
    finalized = (
        not emergency_timeout
        and result is not None
        and not missing
    )
    if not finalized:
        write_json_atomic(run_dir / "run_state.json", {
            **record,
            "runner_state": "incomplete_preserved_requires_invalidation",
        })
        print(
            f"INCOMPLETE {row['run_id']} rc={return_code} "
            f"timeout={emergency_timeout} missing={len(missing)}",
            flush=True)
        return record

    artifact_rows = artifact_inventory(run_dir)
    artifact_manifest = run_dir / "artifact_manifest.csv"
    write_csv_atomic(
        artifact_manifest, artifact_rows, ["path", "bytes", "sha256"])
    marker = {
        **record,
        "artifact_count": len(artifact_rows),
        "artifact_manifest_sha256": sha256(artifact_manifest),
        "result_sha256": sha256(result_path),
        "completed": True,
        "completion_marker_atomic": True,
        "completed_at_unix_seconds": time.time(),
        "run_status": (
            "completed_valid_result"
            if return_code == 0 else "completed_solver_failure_result"),
    }
    write_json_atomic(run_dir / "run_state.json", {
        **marker,
        "runner_state": "completion_marker_pending",
    })
    write_json_atomic(run_dir / "completion_marker.json", marker)
    write_json_atomic(run_dir / "run_state.json", {
        **marker,
        "runner_state": "checksum_valid_complete",
    })
    print(
        f"DONE {row['run_id']} rc={return_code} "
        f"status={record.get('status')} wall={record['runner_wall_seconds']:.3f}",
        flush=True)
    return marker


def pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def acquire_lock(stages: list[str]) -> None:
    if GLOBAL_LOCK.exists():
        try:
            old = load_json(GLOBAL_LOCK)
        except (OSError, ValueError, json.JSONDecodeError):
            old = {}
        if pid_is_running(int(old.get("pid", -1))):
            raise RuntimeError("Round 32 serial runner is already active")
        stale = OUT / "runner_logs" / (
            f"stale_lock_{int(time.time())}.json")
        stale.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(GLOBAL_LOCK, stale)
        GLOBAL_LOCK.unlink()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(GLOBAL_LOCK, flags)
    try:
        value = json.dumps({
            "pid": os.getpid(),
            "stages": stages,
            "created_at_unix_seconds": time.time(),
        }, sort_keys=True) + "\n"
        os.write(descriptor, value.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def release_lock() -> None:
    GLOBAL_LOCK.unlink(missing_ok=True)


def update_summary() -> None:
    rows: list[dict[str, Any]] = []
    for root in (STAGE0_RUNS, RUNS):
        if not root.exists():
            continue
        for marker_path in sorted(root.glob("*/completion_marker.json")):
            marker = load_json(marker_path)
            rows.append({
                key: marker.get(key, "")
                for key in (
                    "round_id", "stage_id", "run_id", "instance_id",
                    "family", "V", "M", "Q", "T",
                    "nominal_budget_seconds", "actual_process_cap_seconds",
                    "arm", "solver", "solver_version",
                    "executable_sha256", "source_commit", "protocol_sha256",
                    "return_code", "emergency_timeout", "status",
                    "lower_bound", "upper_bound", "objective",
                    "strict_certified_original_problem", "run_status",
                    "runner_wall_seconds", "completed",
                )
            })
    if rows:
        write_csv_atomic(SUMMARY, rows, list(rows[0]))


def select_rows(matrix: Path, stage0: bool,
                stages: set[str]) -> list[dict[str, str]]:
    rows = csv_rows(matrix)
    if stage0:
        return rows
    return [row for row in rows if row["stage_id"] in stages]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stages",
        default="stage1,stage2,stage3,stage4,stage5,repeatability")
    parser.add_argument("--stage0", action="store_true")
    parser.add_argument("--max-rows", type=int)
    args = parser.parse_args()
    if not MANIFEST.is_file():
        raise SystemExit("Round 32 frozen manifest is unavailable")
    manifest = load_json(MANIFEST)
    items = inventory()
    stages = {item for item in args.stages.split(",") if item}
    rows = select_rows(
        STAGE0_MATRIX if args.stage0 else OFFICIAL_MATRIX,
        args.stage0, stages)
    if args.max_rows is not None:
        rows = rows[:args.max_rows]
    acquire_lock(["stage0"] if args.stage0 else sorted(stages))
    incomplete = 0
    solver_failures = 0
    try:
        for row in rows:
            state = run_one(
                row, items, manifest, STAGE0_RUNS if args.stage0 else RUNS)
            incomplete += int(not state.get("completed", False))
            solver_failures += int(
                state.get("completed", False)
                and int(state.get("return_code", 1)) != 0)
            update_summary()
    finally:
        release_lock()
    print(json.dumps({
        "selected_rows": len(rows),
        "incomplete_rows": incomplete,
        "completed_solver_failure_rows": solver_failures,
        "experiment_row_resume": True,
        "algorithmic_solve_state_resume": False,
    }, indent=2), flush=True)
    return 1 if incomplete else 0


if __name__ == "__main__":
    raise SystemExit(main())
