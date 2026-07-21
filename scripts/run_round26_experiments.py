#!/usr/bin/env python3
"""Frozen, serial experiment runner for Round 26.

The authorized Gurobi license path is exposed only to child processes.  This
module never opens, copies, hashes, prints, or serializes the license file or
the child environment.
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

import run_round25_experiments as round25


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_external_gurobi_production_validation_round26"
LICENSE = Path(r"E:\gurobi\gurobi.lic")
EXE = ROOT / "build_round26" / "with_gurobi" / "ExactEBRP.exe"
PROTOCOL = OUT / "round26_evaluation_protocol.md"
SEAL = OUT / "heldout_seal.json"
LOCK = OUT / ".round26_runner.lock"
BUILD_SOURCE_COMMIT = "e8b37e1f65a0250a4ad52f92dfa59807a16d56ff"
COMPRESSION_THRESHOLD = 4 * 1024 * 1024

INSTANCES: dict[str, tuple[Path, str, int]] = {
    "V12_M1": (ROOT / "reference/regen_candidate_V12_M1_average.txt", "v12", 12),
    "V12_M2": (ROOT / "reference/regen_candidate_V12_M2_average.txt", "v12", 12),
    "high_imbalance_seed3202": (
        ROOT / "reference/hard_stress/V20_M3/high_imbalance_seed3202.txt",
        "high_imbalance", 20),
    "moderate_seed3302": (
        ROOT / "reference/hard_stress/V20_M3/moderate_seed3302.txt",
        "moderate", 20),
    "tight_T_seed3101": (
        ROOT / "reference/hard_stress/V20_M3/tight_T_seed3101.txt",
        "tight_T", 20),
    "moderate_seed4301": (
        ROOT / "reference/heldout_round22/V20_M3/moderate_seed4301.txt",
        "sentinel", 20),
    "high_imbalance_seed5202": (
        ROOT / "reference/heldout_round26/V20_M3/high_imbalance_seed5202.txt",
        "high_imbalance", 20),
    "high_imbalance_seed5203": (
        ROOT / "reference/heldout_round26/V20_M3/high_imbalance_seed5203.txt",
        "high_imbalance", 20),
    "moderate_seed5301": (
        ROOT / "reference/heldout_round26/V20_M3/moderate_seed5301.txt",
        "moderate", 20),
    "moderate_seed5302": (
        ROOT / "reference/heldout_round26/V20_M3/moderate_seed5302.txt",
        "moderate", 20),
    "tight_T_seed5102": (
        ROOT / "reference/heldout_round26/V20_M3/tight_T_seed5102.txt",
        "tight_T", 20),
    "tight_T_seed5103": (
        ROOT / "reference/heldout_round26/V20_M3/tight_T_seed5103.txt",
        "tight_T", 20),
    "high_imbalance_seed6202": (
        ROOT / "reference/heldout_round26/V50_M3/high_imbalance_seed6202.txt",
        "high_imbalance", 50),
    "moderate_seed6301": (
        ROOT / "reference/heldout_round26/V50_M3/moderate_seed6301.txt",
        "moderate", 50),
    "tight_T_seed6102": (
        ROOT / "reference/heldout_round26/V50_M3/tight_T_seed6102.txt",
        "tight_T", 50),
}

DEVELOPMENT = (
    "V12_M1", "V12_M2", "high_imbalance_seed3202",
    "moderate_seed3302", "tight_T_seed3101",
)
HELDOUT_V20 = (
    "high_imbalance_seed5202", "high_imbalance_seed5203",
    "moderate_seed5301", "moderate_seed5302",
    "tight_T_seed5102", "tight_T_seed5103",
)
V50 = (
    "high_imbalance_seed6202", "moderate_seed6301", "tight_T_seed6102",
)
LONG_CASES = (
    "high_imbalance_seed5202", "moderate_seed5301",
    "tight_T_seed5102", "moderate_seed6301",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def json_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def csv_write(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    material = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(material)
    os.replace(temporary, path)


def add(args: list[str], name: str, value: object) -> None:
    args.extend((name, str(value).lower() if isinstance(value, bool) else str(value)))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def production_binding(run_dir: Path, arm: str) -> list[str]:
    args: list[str] = []
    for name, value in (
        ("--round22-production-mode", True),
        ("--round22-source-commit", BUILD_SOURCE_COMMIT),
        ("--round22-executable-sha256", sha256(EXE)),
        ("--round22-production-manifest-sha256", sha256(PROTOCOL)),
        ("--dense-progress", True),
        ("--dense-progress-run-id", run_dir.name),
        ("--dense-progress-algorithm-arm", arm),
        ("--dense-progress-raw", run_dir / "dense_progress.csv"),
        ("--dense-progress-checkpoints", run_dir / "bound_checkpoints.csv"),
    ):
        add(args, name, value)
    return args


def plain_command(instance: str, budget: int, run_dir: Path) -> list[str]:
    args = [str(EXE), "--input", str(INSTANCES[instance][0])]
    for name, value in (
        ("--method", "gurobi"), ("--lambda", 0.15), ("--T", 3600),
        ("--time-limit", budget * 0.98),
        ("--process-wall-time-limit", budget),
        ("--threads", 1), ("--mip-threads", 1), ("--cplex-threads", 1),
        ("--compact-bc-threads", 1), ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0), ("--gurobi-presolve", -1),
        ("--gurobi-model-export", run_dir / "canonical.lp"),
        ("--gurobi-progress", run_dir / "progress.csv"),
        ("--round24-executable-sha256", sha256(EXE)),
        ("--round24-manifest-executable-sha256", sha256(EXE)),
        ("--log", run_dir / "native.log"),
    ):
        add(args, name, value)
    fingerprints = load_json(
        ROOT / "results/gf_solver_backend_validation_round25/gurobi_fingerprints.json"
    ).get("fingerprints", {})
    add(args, "--round24-expected-gurobi-model-fingerprint",
        int(fingerprints.get(instance, 0)))
    args.append("--plain-baseline")
    add(args, "--out", run_dir / "result.json")
    return args


def external_command(instance: str, arm: str, budget: int,
                     run_dir: Path) -> list[str]:
    args = [str(EXE), "--input", str(INSTANCES[instance][0])]
    args.extend(round25.tailored_base(run_dir, budget))
    args.extend(round25.trace_args(run_dir))
    args.extend(production_binding(run_dir, arm))
    for name, value in (
        ("--frontier-execution-mode", "external-gini-tree"),
        ("--external-gini-artifact-dir", run_dir / "external"),
        ("--external-gini-backend", "gurobi"),
        ("--global-gini-tree-presolve", "off"),
        ("--external-gini-lifecycle", "retained-per-leaf"),
        ("--external-gini-warm-start", False),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0), ("--gurobi-presolve", -1),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    return args


def make_command(instance: str, arm: str, budget: int, run_dir: Path) -> list[str]:
    if arm == "P-GRB":
        return plain_command(instance, budget, run_dir)
    if arm in ("C0", "C1"):
        return external_command(instance, arm, budget, run_dir)
    raise ValueError(f"unknown arm: {arm}")


def sensitive_marker_present(directory: Path) -> bool:
    markers = (
        b"LicenseID", b"WLSAccessID", b"WLSSecret", b"TokenServer",
        b"Set parameter Username", b"Computer ID", b"HOSTID",
    )
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in (".log", ".txt", ".json"):
            data = path.read_bytes()
            if any(marker in data for marker in markers):
                return True
    return False


def compress_large_files(directory: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(directory.rglob("*")):
        if (not path.is_file() or path.stat().st_size < COMPRESSION_THRESHOLD or
                path.suffix.lower() not in (".csv", ".log", ".lp")):
            continue
        target = Path(str(path) + ".gz")
        original_sha = sha256(path)
        original_bytes = path.stat().st_size
        with path.open("rb") as source, target.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw,
                               compresslevel=9, mtime=0) as sink:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    sink.write(block)
        digest = hashlib.sha256()
        restored_bytes = 0
        with gzip.open(target, "rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
                restored_bytes += len(block)
        if digest.hexdigest() != original_sha or restored_bytes != original_bytes:
            target.unlink(missing_ok=True)
            raise RuntimeError(f"compression verification failed: {path}")
        path.unlink()
        records.append({
            "original_path": relative(path), "compressed_path": relative(target),
            "original_bytes": original_bytes,
            "compressed_bytes": target.stat().st_size,
            "original_sha256": original_sha,
            "compressed_sha256": sha256(target),
            "compression": "gzip_level9_mtime0_filename_omitted",
        })
    if records:
        csv_write(directory / "compression_manifest.csv", records,
                  list(records[0]))
    return records


def verify_frozen(instance: str, arm: str, allow_heldout: bool) -> None:
    if sha256(EXE) != load_json(OUT / "round26_build_manifest.json")[
            "gurobi_enabled_sha256"]:
        raise RuntimeError("frozen executable mismatch")
    manifest_name = "p_grb_manifest.json" if arm == "P-GRB" else f"{arm.lower()}_manifest.json"
    manifest = load_json(OUT / manifest_name)
    if manifest["executable_sha256"] != sha256(EXE):
        raise RuntimeError(f"{arm} executable mismatch")
    if manifest["protocol_sha256"] != sha256(PROTOCOL):
        raise RuntimeError(f"{arm} protocol mismatch")
    path = INSTANCES[instance][0]
    if instance in HELDOUT_V20 + V50:
        if not allow_heldout:
            raise RuntimeError(f"sealed instance access blocked before C1 freeze: {instance}")
        entries = load_json(SEAL)["files"]
        expected = {item["path"]: item["sha256"] for item in entries}
        if expected.get(relative(path)) != sha256(path):
            raise RuntimeError(f"held-out seal mismatch: {instance}")


def run_one(stage: str, instance: str, arm: str, budget: int,
            repetition: int = 0, allow_heldout: bool = False,
            official: bool = False, diagnostic_trigger: dict[str, Any] | None = None
            ) -> dict[str, Any]:
    suffix = f"__rep{repetition}" if repetition else ""
    run_id = f"{stage}__{instance}__{arm.lower().replace('-', '_')}{suffix}__{budget}s"
    run_dir = OUT / "runs" / run_id
    state_path = run_dir / "run_state.json"
    if state_path.exists():
        state = load_json(state_path)
        if state.get("completed"):
            print(f"SKIP {run_id}", flush=True)
            return state
        raise RuntimeError(f"incomplete run requires explicit audit: {run_id}")
    verify_frozen(instance, arm, allow_heldout)
    run_dir.mkdir(parents=True, exist_ok=False)
    command = make_command(instance, arm, budget, run_dir)
    record: dict[str, Any] = {
        "schema": "round26-command-v1", "run_id": run_id, "stage": stage,
        "instance": instance, "family": INSTANCES[instance][1],
        "V": INSTANCES[instance][2], "arm": arm, "repetition": repetition,
        "budget_seconds": budget, "command": command,
        "executable_sha256": sha256(EXE),
        "instance_sha256": sha256(INSTANCES[instance][0]),
        "protocol_sha256": sha256(PROTOCOL),
        "license_environment": "process-local-authorized-path-not-serialized",
        "official": official, "diagnostic_only": not official,
        "diagnostic_trigger": diagnostic_trigger or {},
        "started_unix": time.time(), "completed": False,
    }
    json_write(run_dir / "command.json", record)
    env = os.environ.copy()
    env["GRB_LICENSE_FILE"] = str(LICENSE)
    started = time.monotonic()
    emergency_timeout = False
    with (run_dir / "console.stdout.log").open("wb") as stdout, \
         (run_dir / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                timeout=budget + 90, check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            emergency_timeout = True
            return_code = 124
    record.update({
        "finished_unix": time.time(),
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code, "emergency_timeout": emergency_timeout,
        "result_exists": (run_dir / "result.json").is_file(),
        "sensitive_marker_scan_passed": not sensitive_marker_present(run_dir),
        "completed": True,
    })
    if not record["sensitive_marker_scan_passed"]:
        raise RuntimeError(f"sensitive marker detected: {run_id}")
    record["compressed_artifacts"] = compress_large_files(run_dir)
    json_write(state_path, record)
    print(f"DONE {run_id} rc={return_code} wall={record['runner_wall_seconds']:.3f}",
          flush=True)
    return record


def configuration(arm: str) -> dict[str, Any]:
    common = {
        "threads": 1, "seed": 0, "lambda": 0.15, "T": 3600,
        "MIPGap": 0.0, "MIPGapAbs": 0.0,
        "uniform_all_instances": True, "instance_or_family_dispatch": False,
        "process_wall_includes_all_phases": True,
    }
    if arm == "P-GRB":
        return common | {
            "method": "plain_gurobi", "complete_original_compact_milp": True,
            "presolve": "automatic", "HGA_or_known_UB": False,
        }
    return common | {
        "method": "external_solver_neutral_global_gini_tree",
        "backend": "gurobi", "presolve": "automatic",
        "same_run_verified_HGA": True, "HGA_seed": 20260626,
        "HGA_seconds": 10, "initial_intervals": 4,
        "adaptive_split": True, "adaptive_max_depth": 8,
        "adaptive_min_width": 0.0001, "adaptive_split_factor": 2,
        "static_leaf_formulation": "F0", "child_estimate": "parent-copy",
        "lifecycle": "retained-per-leaf", "immutable_artifact_cache": True,
        "non_strict_verified_cutoff": True,
        "explicit_cross_model_warm_start": False,
        "candidate_mechanism": "none" if arm == "C0" else "TO_BE_FROZEN",
    }


def prepare_manifests() -> None:
    if not EXE.is_file() or not PROTOCOL.is_file() or not SEAL.is_file():
        raise RuntimeError("executable, protocol, and held-out seal are required")
    harness_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip().lower()
    build = {
        "schema": "round26-build-manifest-v1",
        "build_source_commit": BUILD_SOURCE_COMMIT,
        "harness_commit_at_freeze": harness_commit,
        "gurobi_enabled_executable": relative(EXE),
        "gurobi_enabled_sha256": sha256(EXE),
        "protocol_sha256": sha256(PROTOCOL),
        "gurobi_version": "13.0.2",
    }
    json_write(OUT / "round26_build_manifest.json", build)
    for arm, filename in (("P-GRB", "p_grb_manifest.json"),
                          ("C0", "c0_manifest.json")):
        json_write(OUT / filename, {
            "schema": "round26-frozen-arm-v1", "arm": arm,
            "build_source_commit": BUILD_SOURCE_COMMIT,
            "harness_commit_at_freeze": harness_commit,
            "executable_path": relative(EXE),
            "executable_sha256": sha256(EXE),
            "protocol_sha256": sha256(PROTOCOL),
            "configuration": configuration(arm),
        })
    print("Round 26 P-GRB/C0 manifests frozen", flush=True)


def acquire_lock() -> None:
    try:
        descriptor = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"runner lock exists: {LOCK}") from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(f"pid={os.getpid()}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-manifests", action="store_true")
    parser.add_argument("--stage", choices=("forensics",))
    args = parser.parse_args()
    if args.prepare_manifests:
        prepare_manifests()
        return 0
    if args.stage != "forensics":
        parser.error("--stage forensics or --prepare-manifests is required")
    if not EXE.is_file() or not LICENSE.is_file():
        raise SystemExit("frozen executable or authorized license path unavailable")
    acquire_lock()
    failures = 0
    try:
        for instance in ("V12_M1", "V12_M2"):
            for repetition in (1, 2, 3):
                for arm in ("P-GRB", "C0"):
                    state = run_one(
                        "forensics", instance, arm, 300,
                        repetition=repetition, allow_heldout=False,
                        official=False)
                    if state["return_code"] != 0 or not state["result_exists"]:
                        failures += 1
        print(f"FORENSICS complete process_failures={failures}", flush=True)
        return 1 if failures else 0
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
