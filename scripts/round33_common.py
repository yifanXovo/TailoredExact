#!/usr/bin/env python3
"""Shared frozen identities and command construction for Round 33."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import run_round31_experiments as round31


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_v10_convergence_round33"
RUNS = OUT / "runs"
STAGE0 = OUT / "stage0_runs"
INVALIDATED = OUT / "invalidated_rows"
BUILD = ROOT / "build_round33" / "official" / "gurobi"
EXE = BUILD / "ExactEBRP.exe"
MANIFEST = OUT / "round33_frozen_manifest.json"
MATRIX = OUT / "round33_official_matrix.csv"
V10_MANIFEST = OUT / "round33_v10_instance_manifest.csv"
V12_MANIFEST = OUT / "round33_v12_anchor_manifest.csv"
FINGERPRINTS = OUT / "round33_gurobi_fingerprints.json"
SHUTDOWN_MARGIN = 15
WATCHDOG = 3690


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


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def inventory() -> dict[str, dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}
    for path in (V10_MANIFEST, V12_MANIFEST):
        for row in csv_rows(path):
            sha = row.get("sha256", row.get("instance_sha256", ""))
            items[row["instance_id"]] = {
                "instance_id": row["instance_id"],
                "path": row["path"],
                "sha256": sha,
                "scenario": row.get("scenario", row.get("family", "")),
                "family": row.get("family", row.get("scenario", "")),
                "V": int(row["V"]),
                "M": int(row["M"]),
                "Q": int(row["Q"]),
                "T": float(row["T"]),
                "lambda": float(row["lambda"]),
                "origin": row.get("origin", "round33_v10_new"),
            }
    return items


def fingerprint_values() -> dict[str, int]:
    data = load_json(FINGERPRINTS)
    return {
        name: int(item["gurobi_model_fingerprint"])
        for name, item in data["instances"].items()
    }


def add(args: list[str], name: str, value: object) -> None:
    args.extend((
        name, str(value).lower() if isinstance(value, bool) else str(value)))


def replace(args: list[str], name: str, value: object) -> None:
    try:
        index = args.index(name)
    except ValueError as error:
        raise RuntimeError(f"frozen C6 option missing: {name}") from error
    args[index + 1] = (
        str(value).lower() if isinstance(value, bool) else str(value))


def instance_path(item: dict[str, Any]) -> Path:
    return ROOT / item["path"]


def plain_command(
        item: dict[str, Any], run_dir: Path, expected_fingerprint: int,
        *, process_cap: float = 3600.0, solver_seconds: float | None = None,
        shutdown_margin: float = SHUTDOWN_MARGIN,
        executable_sha256_override: str | None = None) -> list[str]:
    solve_cap = process_cap if solver_seconds is None else solver_seconds
    executable_sha = executable_sha256_override or sha256(EXE)
    args = [str(EXE), "--input", str(instance_path(item))]
    for name, value in (
        ("--method", "gurobi"),
        ("--lambda", item["lambda"]),
        ("--T", item["T"]),
        ("--time-limit", solve_cap),
        ("--process-wall-time-limit", process_cap),
        ("--process-shutdown-margin", shutdown_margin),
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
        ("--round24-executable-sha256", executable_sha),
        ("--round24-manifest-executable-sha256", executable_sha),
        ("--round24-expected-gurobi-model-fingerprint",
         expected_fingerprint),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    args.append("--plain-baseline")
    return args


def c6_command(
        item: dict[str, Any], run_dir: Path, expected_fingerprint: int,
        *, process_cap: float = 3600.0) -> list[str]:
    args = [str(EXE), "--input", str(instance_path(item))]
    args.extend(round31.tailored_options(run_dir, int(process_cap)))
    for name, value in (
        ("--lambda", item["lambda"]),
        ("--T", item["T"]),
        ("--time-limit", process_cap),
        ("--process-wall-time-limit", process_cap),
        ("--process-shutdown-margin", SHUTDOWN_MARGIN),
    ):
        replace(args, name, value)
    for name, value in (
        ("--frontier-execution-mode", "external-gini-tree"),
        ("--external-gini-scheduling", "round31-nonblocking-native-bound"),
        ("--external-gini-artifact-dir", run_dir / "external"),
        ("--external-gini-backend", "gurobi"),
        ("--external-gini-lifecycle", "round31-open-native-bounded"),
        ("--external-gini-warm-start", False),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0),
        ("--gurobi-presolve", -1),
        ("--round24-expected-gurobi-model-fingerprint",
         expected_fingerprint),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    return args


def command_for(item: dict[str, Any], arm: str,
                run_dir: Path) -> list[str]:
    fingerprint = fingerprint_values()[item["instance_id"]]
    if arm == "P-GRB":
        return plain_command(item, run_dir, fingerprint)
    if arm == "C6-FROZEN":
        return c6_command(item, run_dir, fingerprint)
    raise ValueError(f"unknown Round 33 arm: {arm}")


def required_artifacts(arm: str, run_dir: Path) -> list[Path]:
    common = [
        run_dir / "command.json",
        run_dir / "result.json",
        run_dir / "process_phases.csv",
    ]
    if arm == "P-GRB":
        return common + [run_dir / "progress.csv", run_dir / "canonical.lp"]
    return common + [
        run_dir / "hga_generations.csv",
        run_dir / "external/global_bound_trace.csv",
        run_dir / "external/paper_leaf_ledger.csv",
        run_dir / "external/paper_optimize_ledger.csv",
        run_dir / "external/split_decision_ledger.csv",
        run_dir / "external/native_target_ledger.csv",
    ]


def result_bounds(arm: str, result: dict[str, Any]) -> tuple[float, float]:
    if arm == "C6-FROZEN":
        return (
            float(result.get(
                "external_gini_tree_global_lower_bound",
                result.get("lower_bound", "nan"))),
            float(result.get(
                "external_gini_tree_verified_upper_bound",
                result.get("upper_bound", "nan"))),
        )
    return float(result["lower_bound"]), float(result["upper_bound"])


def process_entry_time(result: dict[str, Any]) -> float:
    return float(result.get(
        "final_process_wall_time_seconds", result.get("runtime_seconds")))
