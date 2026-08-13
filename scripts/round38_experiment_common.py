#!/usr/bin/env python3
"""Frozen identities and paired commands for Round 38 experiments."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import round35_common as r35
import run_round31_experiments as r31


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_global_frontier_lift_round38"
PANEL = OUT / "frozen_development_panel.csv"
EXE = ROOT / "build_round38" / "official" / "gurobi" / "ExactEBRP.exe"
SMOKE_MATRIX = OUT / "round38_smoke_matrix.csv"
SMOKE_FREEZE = OUT / "round38_smoke_freeze.json"
SMOKE_RUNS = OUT / "smoke_runs"
SMOKE_SUMMARY = OUT / "smoke_run_summary.csv"
SHUTDOWN_MARGIN = 15
WATCHDOG_SEPARATION = 90


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value[0] if isinstance(value, list) else value


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
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
        writer = csv.DictWriter(
            stream, fieldnames=columns, extrasaction="ignore"
        )
        writer.writeheader()
        writer.writerows(material)
    temporary.replace(path)


def panel() -> dict[str, dict[str, Any]]:
    inventory = r35.inventory()
    output: dict[str, dict[str, Any]] = {}
    for row in csv_rows(PANEL):
        source = inventory[row["instance_id"]]
        output[row["panel_row_id"]] = {
            **source,
            **row,
            "panel_ordinal": int(row["panel_ordinal"]),
            "V": int(row["V"]),
            "M": int(row["M"]),
        }
    return output


def command_for(row: dict[str, str], item: dict[str, Any],
                run_dir: Path) -> list[str]:
    process_cap = int(row["process_cap_seconds"])
    args = [str(EXE), "--input", str(ROOT / item["path"])]
    args.extend(r31.tailored_options(run_dir, process_cap))
    for name, value in (
        ("--lambda", item["lambda"]),
        ("--T", item["T"]),
        ("--time-limit", process_cap),
        ("--process-wall-time-limit", process_cap),
        ("--process-shutdown-margin", SHUTDOWN_MARGIN),
        ("--primal-heuristic", "hga-tgbc"),
        ("--primal-heuristic-stop", "generation-stagnation"),
        ("--primal-heuristic-no-improve-generations", 2000),
    ):
        r35.replace(args, name, value)
    policy = (
        "off" if row["arm"] == "C6"
        else "pilot-next-frontier-complete"
    )
    for name, value in (
        ("--round34-c6-startup-variant", "hga-full"),
        ("--round36-c6-causal-arm", "off"),
        ("--round36-c6-split-normalization", "proof"),
        ("--round37-c6-geometry-policy", "off"),
        ("--round38-c6-frontier-policy", policy),
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
        r35.add(args, name, value)
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
        run_dir / "external" / "paper_tree_events.csv",
    ]

