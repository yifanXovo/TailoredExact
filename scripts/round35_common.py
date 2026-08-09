#!/usr/bin/env python3
"""Shared identities, commands, and evidence helpers for Round 35.

The module contains no license location. Licensed runners require the
established parent controller to inject the authorized license only into
solver child environments.
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import run_round31_experiments as round31


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_simple_start_qualification_round35"
RUNS = OUT / "runs"
INVALIDATED = OUT / "invalidated_rows"
BUILD = ROOT / "build_round35" / "official" / "gurobi"
EXE = BUILD / "ExactEBRP.exe"
INSTANCE_MANIFEST = OUT / "round35_instance_manifest.csv"
MATRIX_1800 = OUT / "round35_1800s_freeze.csv"
MATRIX_3600 = OUT / "round35_3600s_v50_freeze.csv"
REPEAT_FREEZE = OUT / "round35_repeat_freeze.csv"
OFFICIAL_MATRIX = OUT / "round35_official_matrix.csv"
FINGERPRINTS = OUT / "round35_gurobi_fingerprints.json"
COMMAND_FREEZE = OUT / "round35_command_freeze.json"
FROZEN_MANIFEST = OUT / "round35_frozen_manifest.json"
SHUTDOWN_MARGIN = 15
WATCHDOG_SEPARATION = 90
ARM = "C6-SIMPLE-START"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    candidate = path
    if not candidate.is_file() and path.with_suffix(path.suffix + ".gz").is_file():
        candidate = path.with_suffix(path.suffix + ".gz")
    if candidate.suffix == ".gz":
        with gzip.open(candidate, "rt", encoding="utf-8-sig", errors="replace") as stream:
            return stream.read()
    return candidate.read_text(encoding="utf-8-sig", errors="replace")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(read_text(path))
    return value[0] if isinstance(value, list) else value


def csv_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(read_text(path).splitlines()))


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


def simple_command(item: dict[str, Any], run_dir: Path,
                   *, process_cap: int) -> list[str]:
    """Return the frozen Round 34 SIMPLE-START plus unchanged C6 command."""
    args = [str(EXE), "--input", str(item_path(item))]
    args.extend(round31.tailored_options(run_dir, process_cap))
    for name, value in (
        ("--lambda", item["lambda"]),
        ("--T", item["T"]),
        ("--time-limit", process_cap),
        ("--process-wall-time-limit", process_cap),
        ("--process-shutdown-margin", SHUTDOWN_MARGIN),
        ("--primal-heuristic", "greedy"),
        ("--primal-heuristic-stop", "generation-stagnation"),
        ("--primal-heuristic-no-improve-generations", 2000),
    ):
        replace(args, name, value)
    for name, value in (
        ("--round34-c6-startup-variant", "simple-start"),
        ("--heuristic-candidates-csv", run_dir / "heuristic_candidates.csv"),
        ("--frontier-execution-mode", "external-gini-tree"),
        ("--external-gini-scheduling", "round31-nonblocking-native-bound"),
        ("--external-gini-artifact-dir", run_dir / "external"),
        ("--external-gini-backend", "gurobi"),
        ("--external-gini-lifecycle", "round31-open-native-bounded"),
        ("--external-gini-warm-start", False),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0),
        ("--gurobi-presolve", -1),
        ("--round24-executable-sha256", sha256(EXE)),
        ("--round24-manifest-executable-sha256", sha256(EXE)),
        ("--round24-expected-gurobi-model-fingerprint",
         fingerprint_values()[item["instance_id"]]),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    return args


def command_for(row: dict[str, str], item: dict[str, Any],
                run_dir: Path) -> list[str]:
    if row["arm"] != ARM:
        raise ValueError(f"Round 35 cannot execute comparator arm {row['arm']}")
    return simple_command(
        item, run_dir, process_cap=int(row["process_cap_seconds"]))


def required_artifacts(run_dir: Path) -> list[Path]:
    return [
        run_dir / "command.json",
        run_dir / "result.json",
        run_dir / "process_phases.csv",
        run_dir / "heuristic_candidates.csv",
        run_dir / "external/global_bound_trace.csv",
        run_dir / "external/paper_leaf_ledger.csv",
        run_dir / "external/paper_optimize_ledger.csv",
        run_dir / "external/split_decision_ledger.csv",
        run_dir / "external/native_target_ledger.csv",
    ]


def result_bounds(result: dict[str, Any]) -> tuple[float, float]:
    return (
        float(result.get("external_gini_tree_global_lower_bound",
                         result.get("lower_bound", "nan"))),
        float(result.get("external_gini_tree_verified_upper_bound",
                         result.get("upper_bound", "nan"))),
    )


def process_entry_time(result: dict[str, Any]) -> float:
    return float(result.get(
        "final_process_wall_time_seconds", result.get("runtime_seconds", 0.0)))
