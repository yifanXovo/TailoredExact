#!/usr/bin/env python3
"""Frozen serial runner for the Round 27 paper-safe scheduling study.

The existing Gurobi license is exposed only to child processes.  This module
never opens, copies, hashes, prints, or serializes the license or child
environment.  Official rows are immutable and resumable at whole-row
boundaries; an incomplete directory must be audited rather than overwritten.
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
import run_round26_experiments as round26


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_paper_safe_gurobi_scheduling_round27"
LICENSE = Path(r"E:\gurobi\gurobi.lic")
C0_EXE = ROOT / "build_round26/with_gurobi/ExactEBRP.exe"
C2_EXE = ROOT / "build_round27/with_gurobi/ExactEBRP.exe"
PROTOCOL = OUT / "round27_protocol.md"
LOCK = OUT / ".round27_runner.lock"
NO_IMPROVE_GENERATIONS = 2000
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
        "correctness_sentinel", 20),
    "moderate_seed6301": (
        ROOT / "reference/heldout_round26/V50_M3/moderate_seed6301.txt",
        "moderate", 50),
    "toy": (ROOT / "tests/data/round24_toy_V2_M1.txt", "mechanical", 2),
}

STAGE1 = (
    ("V12_M2", "HGA", 1),
    ("V12_M2", "HGA", 2),
    ("high_imbalance_seed3202", "HGA", 1),
    ("moderate_seed6301", "HGA", 1),
)
STAGE2_INSTANCES = (
    "V12_M1", "V12_M2", "high_imbalance_seed3202",
    "moderate_seed3302", "tight_T_seed3101",
)
STAGE2 = tuple((instance, arm, 0) for instance in STAGE2_INSTANCES
               for arm in ("P-GRB", "C0-LEGACY", "C2-PAPER"))
STAGE3 = (
    ("moderate_seed6301", "P-GRB", 0),
    ("moderate_seed6301", "C2-PAPER", 0),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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


def executable_for(arm: str) -> Path:
    return C0_EXE if arm == "C0-LEGACY" else C2_EXE


def fingerprints() -> dict[str, int]:
    merged: dict[str, int] = {}
    for path in (
        ROOT / "results/gf_solver_backend_validation_round25/gurobi_fingerprints.json",
        ROOT / "results/gf_external_gurobi_production_validation_round26/gurobi_fingerprints.json",
    ):
        merged.update({str(key): int(value) for key, value in
                       load_json(path).get("fingerprints", {}).items()})
    return merged


def production_binding(run_dir: Path, arm: str, exe: Path) -> list[str]:
    manifest_path = OUT / "c2_paper_manifest.json"
    source_commit = (load_json(manifest_path)["build_source_commit"]
                     if manifest_path.is_file() else
                     subprocess.check_output(
                         ["git", "rev-parse", "HEAD"], cwd=ROOT,
                         text=True).strip().lower())
    executable_sha = sha256(exe) if exe.is_file() else "0" * 64
    args: list[str] = []
    for name, value in (
        ("--round22-production-mode", True),
        ("--round22-source-commit", source_commit),
        ("--round22-executable-sha256", executable_sha),
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
    exe = C2_EXE
    executable_sha = sha256(exe) if exe.is_file() else "0" * 64
    args = [str(exe), "--input", str(INSTANCES[instance][0])]
    for name, value in (
        ("--method", "gurobi"), ("--lambda", 0.15), ("--T", 3600),
        ("--time-limit", budget * 0.98),
        ("--process-wall-time-limit", budget),
        ("--threads", 1), ("--mip-threads", 1), ("--cplex-threads", 1),
        ("--compact-bc-threads", 1), ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0), ("--gurobi-presolve", -1),
        ("--gurobi-model-export", run_dir / "canonical.lp"),
        ("--gurobi-progress", run_dir / "progress.csv"),
        ("--round24-executable-sha256", executable_sha),
        ("--round24-manifest-executable-sha256", executable_sha),
        ("--log", run_dir / "native.log"),
    ):
        add(args, name, value)
    add(args, "--round24-expected-gurobi-model-fingerprint",
        fingerprints().get(instance, 0))
    args.append("--plain-baseline")
    add(args, "--out", run_dir / "result.json")
    return args


def c0_command(instance: str, budget: int, run_dir: Path) -> list[str]:
    # Deliberately call the frozen Round 26 constructor.  This preserves its
    # 10-second HGA, 30/60/120/... quanta, and split-after-two behavior.
    return round26.external_command(instance, "C0", budget, run_dir)


def _without_option(args: list[str], option: str) -> list[str]:
    out: list[str] = []
    index = 0
    while index < len(args):
        if args[index] == option:
            index += 2
            continue
        out.append(args[index])
        index += 1
    return out


def c2_command(instance: str, budget: int, run_dir: Path) -> list[str]:
    exe = C2_EXE
    args = [str(exe), "--input", str(INSTANCES[instance][0])]
    base = _without_option(
        round25.tailored_base(run_dir, budget), "--primal-heuristic-seconds")
    args.extend(base)
    args.extend(round25.trace_args(run_dir))
    args.extend(production_binding(run_dir, "C2-PAPER", exe))
    for name, value in (
        ("--primal-heuristic-stop", "generation-stagnation"),
        ("--primal-heuristic-no-improve-generations", NO_IMPROVE_GENERATIONS),
        ("--primal-heuristic-generation-log", run_dir / "hga_generations.csv"),
        ("--frontier-execution-mode", "external-gini-tree"),
        ("--external-gini-scheduling", "paper-lp-event"),
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


def hga_command(instance: str, run_dir: Path,
                no_improve: int = NO_IMPROVE_GENERATIONS) -> list[str]:
    args = [str(C2_EXE), "--input", str(INSTANCES[instance][0])]
    for name, value in (
        ("--method", "primal-heuristic"), ("--lambda", 0.15), ("--T", 3600),
        ("--primal-heuristic", "hga-tgbc"),
        ("--primal-heuristic-seed", 20260626),
        ("--primal-heuristic-stop", "generation-stagnation"),
        ("--primal-heuristic-no-improve-generations", no_improve),
        ("--primal-heuristic-generation-log", run_dir / "hga_generations.csv"),
        ("--threads", 1), ("--mip-threads", 1), ("--cplex-threads", 1),
        ("--compact-bc-threads", 1),
        ("--ub-event-log", run_dir / "ub_events.csv"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    return args


def command_for(instance: str, arm: str, budget: int,
                run_dir: Path) -> list[str]:
    if arm == "P-GRB":
        return plain_command(instance, budget, run_dir)
    if arm == "C0-LEGACY":
        return c0_command(instance, budget, run_dir)
    if arm == "C2-PAPER":
        return c2_command(instance, budget, run_dir)
    if arm == "HGA":
        return hga_command(instance, run_dir)
    raise ValueError(f"unknown arm {arm}")


def validate_frozen(arm: str) -> None:
    if not PROTOCOL.is_file():
        raise RuntimeError("Round 27 protocol is missing")
    manifest_path = OUT / (
        "c0_legacy_manifest.json" if arm == "C0-LEGACY"
        else "c2_paper_manifest.json")
    manifest = load_json(manifest_path)
    exe = executable_for(arm)
    if manifest["executable_sha256"] != sha256(exe):
        raise RuntimeError(f"frozen executable mismatch for {arm}")
    if arm != "C0-LEGACY" and manifest["protocol_sha256"] != sha256(PROTOCOL):
        raise RuntimeError(f"frozen protocol mismatch for {arm}")


def sensitive_marker_present(directory: Path) -> bool:
    markers = (
        b"LicenseID", b"WLSAccessID", b"WLSSecret", b"TokenServer",
        b"Set parameter Username", b"Computer ID", b"HOSTID",
    )
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in (".log", ".txt", ".json"):
            if any(marker in path.read_bytes() for marker in markers):
                return True
    return False


def run_one(stage: str, instance: str, arm: str, budget: int,
            repetition: int = 0, official: bool = True,
            no_improve: int = NO_IMPROVE_GENERATIONS) -> dict[str, Any]:
    suffix = f"__rep{repetition}" if repetition else ""
    budget_label = "criterion" if arm == "HGA" else f"{budget}s"
    run_id = (f"{stage}__{instance}__{arm.lower().replace('-', '_')}"
              f"{suffix}__{budget_label}")
    run_dir = OUT / "runs" / run_id
    state_path = run_dir / "run_state.json"
    if state_path.is_file():
        state = load_json(state_path)
        if state.get("completed"):
            print(f"SKIP {run_id}", flush=True)
            return state
        raise RuntimeError(f"incomplete run requires audit: {run_id}")
    validate_frozen("C0-LEGACY" if arm == "C0-LEGACY" else "C2-PAPER")
    exe = executable_for(arm)
    run_dir.mkdir(parents=True, exist_ok=False)
    command = (hga_command(instance, run_dir, no_improve)
               if arm == "HGA" else command_for(instance, arm, budget, run_dir))
    record: dict[str, Any] = {
        "schema": "round27-command-v1", "run_id": run_id, "stage": stage,
        "instance": instance, "family": INSTANCES[instance][1],
        "V": INSTANCES[instance][2], "arm": arm, "repetition": repetition,
        "budget_seconds": None if arm == "HGA" else budget,
        "hga_no_improve_generations": no_improve if arm in ("HGA", "C2-PAPER") else None,
        "command": command, "executable_sha256": sha256(exe),
        "instance_sha256": sha256(INSTANCES[instance][0]),
        "protocol_sha256": sha256(PROTOCOL),
        "license_environment": "process-local-authorized-path-not-serialized",
        "official": official, "started_unix": time.time(), "completed": False,
    }
    json_write(run_dir / "command.json", record)
    env = os.environ.copy()
    env["GRB_LICENSE_FILE"] = str(LICENSE)
    started = time.monotonic()
    emergency_timeout = False
    timeout = None if arm == "HGA" else budget + 8
    with (run_dir / "console.stdout.log").open("wb") as stdout, \
         (run_dir / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                timeout=timeout, check=False)
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
    json_write(state_path, record)
    if not record["sensitive_marker_scan_passed"]:
        raise RuntimeError(f"sensitive marker detected in {run_id}")
    print(f"DONE {run_id} rc={return_code} wall={record['runner_wall_seconds']:.3f}",
          flush=True)
    return record


def configuration(arm: str) -> dict[str, Any]:
    common = {
        "threads": 1, "lambda": 0.15, "T": 3600,
        "gurobi_seed": 0, "gurobi_presolve": "automatic",
        "MIPGap": 0.0, "MIPGapAbs": 0.0,
        "uniform_all_instances": True,
        "instance_family_size_path_performance_dispatch": False,
    }
    if arm == "P-GRB":
        return common | {
            "method": "complete_original_compact_milp", "HGA": False,
            "tailored_information": False,
        }
    return common | {
        "method": "external_gini_tree_paper_lp_event", "backend": "gurobi",
        "HGA_seed": 20260626,
        "HGA_stop": "2000_consecutive_completed_generations_without_strict_global_best_fitness_improvement",
        "HGA_wall_condition": False, "HGA_seconds_option_used": False,
        "initial_intervals": 4, "adaptive_max_depth": 8,
        "adaptive_min_width": 0.0001, "adaptive_split_factor": 2,
        "static_leaf_formulation": "F0", "warm_start": False,
        "leaf_scheduling": "best_bound_complete_LP_event",
        "per_leaf_time_work_node_solution_attempt_retry_budgets": False,
        "terminal_MIP_optimize_count_per_leaf": 1,
    }


def prepare_manifests() -> None:
    if not C2_EXE.is_file() or not C0_EXE.is_file() or not PROTOCOL.is_file():
        raise RuntimeError("Round 27 executables and protocol are required")
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip().lower()
    json_write(OUT / "c2_paper_manifest.json", {
        "schema": "round27-frozen-c2-paper-v1", "arm": "C2-PAPER",
        "paper_compatible": True, "build_source_commit": source_commit,
        "executable_path": relative(C2_EXE),
        "executable_sha256": sha256(C2_EXE),
        "protocol_sha256": sha256(PROTOCOL), "gurobi_version": "13.0.2",
        "configuration": configuration("C2-PAPER"),
    })
    json_write(OUT / "p_grb_manifest.json", {
        "schema": "round27-frozen-p-grb-v1", "arm": "P-GRB",
        "build_source_commit": source_commit,
        "executable_path": relative(C2_EXE),
        "executable_sha256": sha256(C2_EXE),
        "protocol_sha256": sha256(PROTOCOL), "gurobi_version": "13.0.2",
        "configuration": configuration("P-GRB"),
    })


def acquire_lock() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"runner lock exists: {LOCK}") from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(f"pid={os.getpid()}\n")


def compress_large_files() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(OUT.rglob("*")):
        if (not path.is_file() or path.stat().st_size < COMPRESSION_THRESHOLD or
                path.suffix.lower() not in (".csv", ".log", ".lp")):
            continue
        target = Path(str(path) + ".gz")
        original_sha = sha256(path)
        original_size = path.stat().st_size
        with path.open("rb") as source, target.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw,
                               compresslevel=9, mtime=0) as sink:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    sink.write(block)
        restored = hashlib.sha256()
        restored_size = 0
        with gzip.open(target, "rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                restored.update(block)
                restored_size += len(block)
        if restored.hexdigest() != original_sha or restored_size != original_size:
            target.unlink(missing_ok=True)
            raise RuntimeError(f"lossless compression verification failed: {path}")
        path.unlink()
        records.append({
            "original_path": relative(path), "compressed_path": relative(target),
            "original_bytes": original_size, "compressed_bytes": target.stat().st_size,
            "original_sha256": original_sha, "compressed_sha256": sha256(target),
            "restoration_sha256": restored.hexdigest(), "restoration_bytes": restored_size,
            "compression": "gzip_level9_mtime0_filename_omitted",
        })
    csv_write(OUT / "compression_manifest.csv", records,
              list(records[0]) if records else [
                  "original_path", "compressed_path", "original_bytes",
                  "compressed_bytes", "original_sha256", "compressed_sha256",
                  "restoration_sha256", "restoration_bytes", "compression"])
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-manifests", action="store_true")
    parser.add_argument("--compress", action="store_true")
    parser.add_argument("--stage", choices=("stage1", "stage2", "stage3", "sentinel"))
    parser.add_argument("--sentinel-no-improve", type=int, default=2)
    args = parser.parse_args()
    if args.prepare_manifests:
        prepare_manifests()
        return 0
    if args.compress:
        rows = compress_large_files()
        print(f"compressed_files={len(rows)}", flush=True)
        return 0
    if not args.stage:
        parser.error("--stage, --prepare-manifests, or --compress is required")
    if not C0_EXE.is_file() or not C2_EXE.is_file() or not LICENSE.is_file():
        raise SystemExit("frozen executables or authorized license path unavailable")
    acquire_lock()
    failures = 0
    try:
        if args.stage == "stage1":
            matrix = STAGE1
            budget = 0
        elif args.stage == "stage2":
            matrix = STAGE2
            budget = 300
        elif args.stage == "stage3":
            matrix = STAGE3
            budget = 300
        else:
            matrix = (("moderate_seed4301", "C2-PAPER", 0),)
            budget = 60
        for instance, arm, repetition in matrix:
            state = run_one(
                args.stage, instance, arm, budget, repetition,
                official=args.stage in ("stage1", "stage2", "stage3"),
                no_improve=(args.sentinel_no_improve if args.stage == "sentinel"
                            else NO_IMPROVE_GENERATIONS))
            if state["return_code"] != 0 or not state["result_exists"]:
                failures += 1
        print(f"{args.stage.upper()} complete process_failures={failures}", flush=True)
        return 1 if failures else 0
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
