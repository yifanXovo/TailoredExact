#!/usr/bin/env python3
"""Shared identities, commands, and evidence helpers for Round 34.

The module contains no license path.  Licensed runners require the established
parent controller to inject the authorized license only into child-process
environments.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import run_round31_experiments as round31


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_documentation_hga_round34"
RUNS = OUT / "runs"
DEVELOPMENT_RUNS = OUT / "development_runs"
STAGE0_RUNS = OUT / "stage0_runs"
INVALIDATED = OUT / "invalidated_rows"
BUILD = ROOT / "build_round34" / "official" / "gurobi"
EXE = BUILD / "ExactEBRP.exe"
INSTANCE_MANIFEST = OUT / "round34_instance_manifest.csv"
CASE_MANIFEST = OUT / "convergence_case_manifest.csv"
DEVELOPMENT_MANIFEST = OUT / "hga_development_manifest.csv"
TRANSFER_MANIFEST = OUT / "hga_transfer_anchor_manifest.csv"
REPEAT_MANIFEST = OUT / "hga_repeat_manifest.csv"
FINGERPRINTS = OUT / "round34_gurobi_fingerprints.json"
VARIANT_FREEZE = OUT / "hga_variant_freeze.json"
OFFICIAL_MATRIX = OUT / "round34_official_matrix.csv"
FROZEN_MANIFEST = OUT / "round34_frozen_manifest.json"
SHUTDOWN_MARGIN = 15

STARTUP_ARMS = (
    "C6-HGA-FULL",
    "C6-HGA-LIGHT",
    "C6-SIMPLE-START",
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


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8", newline="\n")
    temporary.replace(path)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: Iterable[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    material = list(rows)
    if not material:
        raise ValueError(f"cannot write empty CSV: {path}")
    columns = fields or list(material[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)
    temporary.replace(path)


def inventory() -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for row in csv_rows(INSTANCE_MANIFEST):
        output[row["instance_id"]] = {
            **row,
            "V": int(row["V"]),
            "M": int(row["M"]),
            "Q": int(row["Q"]),
            "T": float(row["T"]),
            "lambda": float(row["lambda"]),
        }
    return output


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
        raise RuntimeError(f"frozen option missing: {name}") from error
    args[index + 1] = (
        str(value).lower() if isinstance(value, bool) else str(value))


def item_path(item: dict[str, Any]) -> Path:
    return ROOT / str(item["path"])


def plain_command(item: dict[str, Any], run_dir: Path,
                  expected_fingerprint: int, *, process_cap: float,
                  solver_seconds: float | None = None,
                  shutdown_margin: float = SHUTDOWN_MARGIN) -> list[str]:
    solve_cap = process_cap if solver_seconds is None else solver_seconds
    args = [str(EXE), "--input", str(item_path(item))]
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
        ("--round24-executable-sha256", sha256(EXE)),
        ("--round24-manifest-executable-sha256", sha256(EXE)),
        ("--round24-expected-gurobi-model-fingerprint",
         expected_fingerprint),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    args.append("--plain-baseline")
    return args


def startup_definition(arm: str) -> dict[str, Any]:
    definitions = {
        "C6-HGA-FULL": {
            "startup_variant": "hga-full",
            "primal_heuristic": "hga-tgbc",
            "stop": "generation-stagnation",
            "no_improve": 2000,
        },
        "C6-HGA-LIGHT": {
            "startup_variant": "hga-light-1000",
            "primal_heuristic": "hga-tgbc",
            "stop": "generation-stagnation",
            "no_improve": 1000,
        },
        "C6-SIMPLE-START": {
            "startup_variant": "simple-start",
            "primal_heuristic": "greedy",
            "stop": "generation-stagnation",
            "no_improve": 2000,
        },
    }
    if arm not in definitions:
        raise ValueError(f"unknown startup arm: {arm}")
    return definitions[arm]


def c6_command(item: dict[str, Any], arm: str, run_dir: Path,
               expected_fingerprint: int, *, process_cap: float) -> list[str]:
    startup = startup_definition(arm)
    args = [str(EXE), "--input", str(item_path(item))]
    args.extend(round31.tailored_options(run_dir, int(process_cap)))
    for name, value in (
        ("--lambda", item["lambda"]),
        ("--T", item["T"]),
        ("--time-limit", process_cap * 0.98),
        ("--process-wall-time-limit", process_cap),
        ("--process-shutdown-margin", SHUTDOWN_MARGIN),
        ("--primal-heuristic", startup["primal_heuristic"]),
        ("--primal-heuristic-stop", startup["stop"]),
        ("--primal-heuristic-no-improve-generations",
         startup["no_improve"]),
    ):
        replace(args, name, value)
    for name, value in (
        ("--round34-c6-startup-variant", startup["startup_variant"]),
        ("--heuristic-candidates-csv",
         run_dir / "heuristic_candidates.csv"),
        ("--frontier-execution-mode", "external-gini-tree"),
        ("--external-gini-scheduling",
         "round31-nonblocking-native-bound"),
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


def development_command(item: dict[str, Any], arm: str,
                        run_dir: Path) -> list[str]:
    startup = startup_definition(arm)
    args = [str(EXE), "--input", str(item_path(item))]
    for name, value in (
        ("--method", "primal-heuristic"),
        ("--lambda", item["lambda"]),
        ("--T", item["T"]),
        ("--threads", 1),
        ("--mip-threads", 1),
        ("--cplex-threads", 1),
        ("--compact-bc-threads", 1),
        ("--primal-heuristic", startup["primal_heuristic"]),
        ("--primal-heuristic-seed", 20260626),
        ("--primal-heuristic-stop", startup["stop"]),
        ("--primal-heuristic-no-improve-generations",
         startup["no_improve"]),
        ("--primal-heuristic-generation-log",
         run_dir / "hga_generations.csv"),
        ("--heuristic-candidates-csv",
         run_dir / "heuristic_candidates.csv"),
        ("--process-phase-ledger", run_dir / "process_phases.csv"),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    return args


def command_for(row: dict[str, str], item: dict[str, Any],
                run_dir: Path) -> list[str]:
    cap = float(row["process_cap_seconds"])
    fingerprint = fingerprint_values()[item["instance_id"]]
    if row["arm"] == "P-GRB":
        return plain_command(
            item, run_dir, fingerprint, process_cap=cap)
    return c6_command(
        item, row["arm"], run_dir, fingerprint, process_cap=cap)


def required_artifacts(arm: str, run_dir: Path) -> list[Path]:
    common = [
        run_dir / "command.json",
        run_dir / "result.json",
        run_dir / "process_phases.csv",
    ]
    if arm == "P-GRB":
        return common + [run_dir / "progress.csv", run_dir / "canonical.lp"]
    exact = common + [
        run_dir / "heuristic_candidates.csv",
        run_dir / "external/global_bound_trace.csv",
        run_dir / "external/paper_leaf_ledger.csv",
        run_dir / "external/paper_optimize_ledger.csv",
        run_dir / "external/split_decision_ledger.csv",
        run_dir / "external/native_target_ledger.csv",
    ]
    if arm != "C6-SIMPLE-START":
        exact.append(run_dir / "hga_generations.csv")
    return exact


def result_bounds(arm: str, result: dict[str, Any]) -> tuple[float, float]:
    if arm.startswith("C6-"):
        return (
            float(result.get("external_gini_tree_global_lower_bound",
                             result.get("lower_bound", "nan"))),
            float(result.get("external_gini_tree_verified_upper_bound",
                             result.get("upper_bound", "nan"))),
        )
    return float(result["lower_bound"]), float(result["upper_bound"])


def process_entry_time(result: dict[str, Any]) -> float:
    return float(result.get(
        "final_process_wall_time_seconds", result.get("runtime_seconds", 0.0)))
