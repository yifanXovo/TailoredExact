#!/usr/bin/env python3
"""Frozen serial Round 29 runner.

The license path is assigned only to licensed child environments.  This module
never opens, reads, hashes, copies, prints, or serializes that file.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable

import run_round28_experiments as r28


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_gurobi_performance_recovery_round29"
RUNS = OUT / "runs"
PROTOCOL = OUT / "round29_protocol.md"
INSTANCE_MANIFEST = OUT / "all_authoritative_instances_manifest.csv"
MANIFEST = OUT / "c4_manifest.json"
LICENSE = Path(r"E:\gurobi\gurobi.lic")
GUROBI_EXE = ROOT / "build_round29/with_gurobi/ExactEBRP.exe"
LOCK = OUT / ".round29_runner.lock"
OFFICIAL_BUDGET = 300
SHUTDOWN_MARGIN = 5
COMPRESSION_THRESHOLD = 512 * 1024

INSTANCES = r28.INSTANCES
PRIMARY = r28.PRIMARY
STAGE1_INSTANCES = (
    "V12_M1", "V12_M2", "high_imbalance_seed3202",
    "moderate_seed3302", "tight_T_seed3101", "moderate_seed6301",
)
ANCHORS = (
    "V12_M1", "V12_M2", "high_imbalance_seed3202",
    "moderate_seed3302", "tight_T_seed3101",
)
STAGE4_INSTANCES = (
    "V12_M2", "moderate_seed3302", "tight_T_seed3101",
    "moderate_seed6301", "high_imbalance_seed5202",
)


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


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    os.replace(temporary, path)


def csv_write(path: Path, data: Iterable[dict[str, Any]],
              fields: list[str]) -> None:
    material = list(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(material)
    os.replace(temporary, path)


def add(args: list[str], name: str, value: object) -> None:
    args.extend((name, str(value).lower() if isinstance(value, bool)
                 else str(value)))


def instance_path(instance: str) -> Path:
    return ROOT / INSTANCES[instance][0]


def prepare_instance_manifest() -> None:
    records = []
    for name in PRIMARY:
        path_text, family, vehicles, crews, expected = INSTANCES[name]
        path = ROOT / path_text
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"authoritative instance mismatch: {name}")
        records.append({
            "instance": name, "family": family, "V": vehicles, "M": crews,
            "path": path_text, "bytes": path.stat().st_size,
            "sha256": expected, "primary_stage2": True,
            "stage1_anchor": name in STAGE1_INSTANCES,
            "stage3_anchor": name in ANCHORS,
            "stage4_repeat": name in STAGE4_INSTANCES,
            "frozen_before_official_results": True,
        })
    csv_write(INSTANCE_MANIFEST, records, list(records[0]))


def tailored_options(run_dir: Path, budget: int,
                     local_redecode: bool) -> list[str]:
    # Start from the frozen Round 28 mathematical/static-row option pack.
    args = r28.tailored_options(run_dir, budget)
    add(args, "--exact-phase-local-redecode-repair", local_redecode)
    add(args, "--process-shutdown-margin", SHUTDOWN_MARGIN)
    add(args, "--process-phase-ledger", run_dir / "process_phases.csv")
    return args


def plain_command(instance: str, budget: int, run_dir: Path) -> list[str]:
    args = [str(GUROBI_EXE), "--input", str(instance_path(instance))]
    for name, value in (
        ("--method", "gurobi"), ("--lambda", 0.15), ("--T", 3600),
        ("--time-limit", budget), ("--process-wall-time-limit", budget),
        ("--process-shutdown-margin", SHUTDOWN_MARGIN),
        ("--process-phase-ledger", run_dir / "process_phases.csv"),
        ("--threads", 1), ("--mip-threads", 1), ("--cplex-threads", 1),
        ("--compact-bc-threads", 1),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0), ("--gurobi-presolve", -1),
        ("--gurobi-model-export", run_dir / "canonical.lp"),
        ("--gurobi-progress", run_dir / "progress.csv"),
        ("--round24-executable-sha256", sha256(GUROBI_EXE)),
        ("--round24-manifest-executable-sha256", sha256(GUROBI_EXE)),
        ("--round24-expected-gurobi-model-fingerprint",
         r28.merged_fingerprints().get(instance, 0)),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    args.append("--plain-baseline")
    return args


def external_command(instance: str, arm: str, budget: int,
                     run_dir: Path) -> list[str]:
    c4 = arm == "C4-CANDIDATE"
    args = [str(GUROBI_EXE), "--input", str(instance_path(instance))]
    args.extend(tailored_options(
        run_dir, budget, local_redecode=not c4))
    for name, value in (
        ("--frontier-execution-mode", "external-gini-tree"),
        ("--external-gini-scheduling",
         "round29-bound-gain-incremental" if c4
         else "cplex-algorithm-replica"),
        ("--external-gini-artifact-dir", run_dir / "external"),
        ("--external-gini-backend", "gurobi"),
        ("--external-gini-lifecycle",
         "round29-same-leaf-in-memory-model" if c4
         else "fresh-per-replica-event"),
        ("--external-gini-warm-start", False),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0), ("--gurobi-presolve", -1),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    return args


def command_for(instance: str, arm: str, budget: int,
                run_dir: Path) -> list[str]:
    if arm == "P-GRB":
        return plain_command(instance, budget, run_dir)
    if arm in {"C3-REPLICA", "C4-CANDIDATE"}:
        return external_command(instance, arm, budget, run_dir)
    raise ValueError(arm)


def validate_frozen(instance: str) -> dict[str, Any]:
    if not MANIFEST.is_file():
        raise RuntimeError("C4 manifest is not frozen")
    manifest = load_json(MANIFEST)
    if sha256(PROTOCOL) != manifest["protocol_sha256"]:
        raise RuntimeError("Round 29 protocol changed after freeze")
    if subprocess.check_output(
            ("git", "rev-parse", "HEAD"), cwd=ROOT,
            text=True).strip() != manifest["source_commit"]:
        raise RuntimeError("Round 29 source commit changed after freeze")
    for key in ("instance_manifest", "parameter_freeze",
                "forbidden_logic_scan"):
        path = ROOT / manifest[f"{key}_path"]
        if not path.is_file() or (
                sha256(path) != manifest[f"{key}_sha256"]):
            raise RuntimeError(f"Round 29 frozen {key} changed")
    for path_text, expected_hash in manifest["source_file_sha256"].items():
        path = ROOT / path_text
        if not path.is_file() or sha256(path) != expected_hash:
            raise RuntimeError(f"Round 29 source changed: {path_text}")
    if not GUROBI_EXE.is_file() or (
            sha256(GUROBI_EXE) != manifest["gurobi_executable_sha256"]):
        raise RuntimeError("Round 29 executable changed after freeze")
    expected = INSTANCES[instance][4]
    if not instance_path(instance).is_file() or (
            sha256(instance_path(instance)) != expected):
        raise RuntimeError(f"instance changed after freeze: {instance}")
    return manifest


def sensitive_marker_present(directory: Path) -> bool:
    markers = (
        b"LicenseID", b"WLSAccessID", b"WLSSecret", b"TokenServer",
        b"Set parameter Username", b"Computer ID", b"HOSTID",
    )
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".log", ".txt", ".json"}:
            if any(marker in path.read_bytes() for marker in markers):
                return True
    return False


def run_one(stage: str, instance: str, arm: str, budget: int,
            repetition: int = 0) -> dict[str, Any]:
    suffix = f"__rep{repetition}" if repetition else ""
    slug = arm.lower().replace("-", "_")
    run_id = f"{stage}__{instance}__{slug}{suffix}__{budget}s"
    run_dir = RUNS / run_id
    state_path = run_dir / "run_state.json"
    if state_path.is_file():
        state = load_json(state_path)
        if state.get("completed"):
            print(f"SKIP {run_id}", flush=True)
            return state
        raise RuntimeError(f"incomplete run requires audit: {run_id}")
    manifest = validate_frozen(instance)
    run_dir.mkdir(parents=True, exist_ok=False)
    command = command_for(instance, arm, budget, run_dir)
    record: dict[str, Any] = {
        "schema": "round29-command-v1", "run_id": run_id,
        "stage": stage, "instance": instance,
        "family": INSTANCES[instance][1], "V": INSTANCES[instance][2],
        "M": INSTANCES[instance][3], "arm": arm,
        "repetition": repetition, "budget_seconds": budget,
        "shutdown_margin_seconds": SHUTDOWN_MARGIN,
        "command": command,
        "source_commit": manifest["source_commit"],
        "executable_sha256": sha256(GUROBI_EXE),
        "instance_sha256": sha256(instance_path(instance)),
        "protocol_sha256": sha256(PROTOCOL),
        "license_environment": "process-local-authorized-path-not-serialized",
        "official": True, "started_unix": time.time(), "completed": False,
    }
    json_write(run_dir / "command.json", record)
    environment = os.environ.copy()
    environment["GRB_LICENSE_FILE"] = str(LICENSE)
    started = time.monotonic()
    emergency_timeout = False
    with (run_dir / "console.stdout.log").open("wb") as stdout, \
         (run_dir / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=environment, stdout=stdout,
                stderr=stderr, timeout=budget + 15, check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            emergency_timeout = True
            return_code = 124
    record.update({
        "finished_unix": time.time(),
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code,
        "emergency_timeout": emergency_timeout,
        "result_exists": (run_dir / "result.json").is_file(),
        "phase_ledger_exists": (run_dir / "process_phases.csv").is_file(),
        "sensitive_marker_scan_passed": not sensitive_marker_present(run_dir),
        "completed": True,
    })
    json_write(state_path, record)
    if not record["sensitive_marker_scan_passed"]:
        raise RuntimeError(f"sensitive marker detected: {run_id}")
    print(
        f"DONE {run_id} rc={return_code} "
        f"wall={record['runner_wall_seconds']:.3f}", flush=True)
    return record


def stage_matrix(stage: str) -> tuple[tuple[str, str, int], ...]:
    if stage == "stage1":
        return tuple(
            (instance, arm, 0)
            for instance in STAGE1_INSTANCES
            for arm in ("C3-REPLICA", "C4-CANDIDATE")
        )
    if stage == "stage2":
        # Stage-1 C3/C4 rows are intentionally also the primary Stage-2 rows
        # for the six overlapping instances. Stage 2 adds P-GRB everywhere
        # and C3/C4 on the remaining eleven instances.
        return (
            tuple((instance, "P-GRB", 0) for instance in PRIMARY) +
            tuple(
                (instance, arm, 0)
                for instance in PRIMARY
                if instance not in STAGE1_INSTANCES
                for arm in ("C3-REPLICA", "C4-CANDIDATE")
            )
        )
    if stage == "stage4":
        return tuple(
            (instance, "C4-CANDIDATE", repetition)
            for instance in STAGE4_INSTANCES
            for repetition in (1, 2)
        )
    raise ValueError(stage)


def acquire_lock() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise RuntimeError(f"runner lock exists: {LOCK}") from error
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(f"pid={os.getpid()}\n")


def compress_large_files() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    manifest_path = OUT / "compression_manifest.csv"
    artifact_roots = (
        RUNS,
        OUT / "development",
        OUT / "stage0_runs",
    )
    paths = sorted({
        path
        for root in artifact_roots if root.is_dir()
        for path in root.rglob("*")
    })
    for path in paths:
        if (not path.is_file() or path.stat().st_size < COMPRESSION_THRESHOLD or
                path.suffix.lower() not in {".csv", ".log", ".lp"}):
            continue
        target = Path(str(path) + ".gz")
        original_hash = sha256(path)
        original_bytes = path.stat().st_size
        with path.open("rb") as source, target.open("wb") as raw:
            with gzip.GzipFile(
                    filename="", mode="wb", fileobj=raw,
                    compresslevel=9, mtime=0) as sink:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    sink.write(block)
        restored = hashlib.sha256()
        restored_bytes = 0
        with gzip.open(target, "rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                restored.update(block)
                restored_bytes += len(block)
        if restored.hexdigest() != original_hash or (
                restored_bytes != original_bytes):
            target.unlink(missing_ok=True)
            raise RuntimeError(f"compression verification failed: {path}")
        path.unlink()
        records.append({
            "original_path": relative(path),
            "compressed_path": relative(target),
            "original_bytes": original_bytes,
            "compressed_bytes": target.stat().st_size,
            "original_sha256": original_hash,
            "compressed_sha256": sha256(target),
            "restoration_sha256": restored.hexdigest(),
            "restoration_bytes": restored_bytes,
            "compression": "gzip_level9_mtime0_filename_omitted",
        })
    fields = list(records[0]) if records else [
        "original_path", "compressed_path", "original_bytes",
        "compressed_bytes", "original_sha256", "compressed_sha256",
        "restoration_sha256", "restoration_bytes", "compression",
    ]
    csv_write(manifest_path, records, fields)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-instance-manifest", action="store_true")
    parser.add_argument("--compress", action="store_true")
    parser.add_argument("--stage", choices=("stage1", "stage2", "stage4"))
    args = parser.parse_args()
    if args.prepare_instance_manifest:
        prepare_instance_manifest()
        return 0
    if args.compress:
        print(f"compressed_files={len(compress_large_files())}", flush=True)
        return 0
    if not args.stage:
        parser.error("--stage, --prepare-instance-manifest, or --compress required")
    acquire_lock()
    failures = 0
    try:
        for instance, arm, repetition in stage_matrix(args.stage):
            state = run_one(
                args.stage, instance, arm, OFFICIAL_BUDGET, repetition)
            if (state["return_code"] != 0 or not state["result_exists"] or
                    state["emergency_timeout"] or
                    not state["phase_ledger_exists"]):
                failures += 1
        print(f"{args.stage.upper()} complete process_failures={failures}",
              flush=True)
        return 1 if failures else 0
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
