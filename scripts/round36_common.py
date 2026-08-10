#!/usr/bin/env python3
"""Shared frozen identities and commands for Round 36."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import round35_common as r35
import run_round31_experiments as r31


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_incumbent_decomposition_causal_round36"
RUNS = OUT / "runs"
INVALIDATED = OUT / "invalidated_rows"
BUILD = ROOT / "build_round36" / "official" / "gurobi"
EXE = BUILD / "ExactEBRP.exe"
PANEL = OUT / "frozen_causal_panel.csv"
OFFICIAL_MATRIX = OUT / "round36_official_matrix.csv"
COMMAND_FREEZE = OUT / "round36_command_freeze.json"
FROZEN_MANIFEST = OUT / "round36_frozen_manifest.json"
SUMMARY = OUT / "runner_row_summary.csv"
START_RECORD = OUT / "official_start_record.json"
SHUTDOWN_MARGIN = 15
WATCHDOG_SEPARATION = 90
ARMS = ("HH", "SS", "BW-P", "BW-A")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(read_text(path))
    return value[0] if isinstance(value, list) else value


def csv_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(read_text(path).splitlines()))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def write_csv(path: Path, rows: Iterable[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    material = list(rows)
    if not material:
        raise ValueError(f"cannot write empty CSV: {path}")
    columns = fields or list(material[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns,
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)
    temporary.replace(path)


def inventory() -> dict[str, dict[str, Any]]:
    historical = r35.inventory()
    output: dict[str, dict[str, Any]] = {}
    for row in csv_rows(PANEL):
        source = historical[row["instance_id"]]
        output[row["instance_id"]] = {
            **source,
            "panel_ordinal": int(row["panel_ordinal"]),
            "panel_row_id": row["panel_row_id"],
            "round35_stage": row["round35_stage"],
            "process_cap_seconds": int(row["process_cap_seconds"]),
            "round35_pattern": row["round35_pattern"],
            "selection_basis": row["selection_basis"],
        }
    return output


def item_path(item: dict[str, Any]) -> Path:
    return ROOT / str(item["path"])


def add(args: list[str], name: str, value: object) -> None:
    r35.add(args, name, value)


def replace(args: list[str], name: str, value: object) -> None:
    r35.replace(args, name, value)


def command_for(row: dict[str, str], item: dict[str, Any],
                run_dir: Path) -> list[str]:
    process_cap = int(row["process_cap_seconds"])
    arm = row["arm"]
    args = [str(EXE), "--input", str(item_path(item))]
    args.extend(r31.tailored_options(run_dir, process_cap))
    startup = "simple-start" if arm == "SS" else "hga-full"
    heuristic = "greedy" if arm == "SS" else "hga-tgbc"
    normalization = "anchor" if arm == "BW-A" else "proof"
    for name, value in (
        ("--lambda", item["lambda"]),
        ("--T", item["T"]),
        ("--time-limit", process_cap),
        ("--process-wall-time-limit", process_cap),
        ("--process-shutdown-margin", SHUTDOWN_MARGIN),
        ("--primal-heuristic", heuristic),
        ("--primal-heuristic-stop", "generation-stagnation"),
        ("--primal-heuristic-no-improve-generations", 2000),
    ):
        replace(args, name, value)
    for name, value in (
        ("--round34-c6-startup-variant", startup),
        ("--round36-c6-causal-arm", arm.lower()),
        ("--round36-c6-split-normalization", normalization),
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
         r35.fingerprint_values()[item["instance_id"]]),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    return [str(value) for value in args]


def required_artifacts(run_dir: Path) -> list[Path]:
    return [
        run_dir / "command.json",
        run_dir / "result.json",
        run_dir / "process_phases.csv",
        run_dir / "heuristic_candidates.csv",
        run_dir / "external" / "initial_decomposition_ledger.csv",
        run_dir / "external" / "global_bound_trace.csv",
        run_dir / "external" / "paper_leaf_ledger.csv",
        run_dir / "external" / "paper_optimize_ledger.csv",
        run_dir / "external" / "lp_status_ledger.csv",
        run_dir / "external" / "parent_child_bound_ledger.csv",
        run_dir / "external" / "split_decision_ledger.csv",
        run_dir / "external" / "native_target_ledger.csv",
    ]


def result_bounds(result: dict[str, Any]) -> tuple[float, float]:
    return (float(result["external_gini_tree_global_lower_bound"]),
            float(result["external_gini_tree_verified_upper_bound"]))


def process_entry_time(result: dict[str, Any]) -> float:
    return float(result.get("final_process_wall_time_seconds",
                            result.get("runtime_seconds", 0.0)))
