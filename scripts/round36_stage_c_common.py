#!/usr/bin/env python3
"""Shared identities and frozen command construction for Round 36 Stage C."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import round35_common as r35
import round36_common as r36
import run_round31_experiments as r31


ROOT = Path(__file__).resolve().parents[1]
OUT = r36.OUT
RUNS = OUT / "stage_c_runs"
INVALIDATED = OUT / "stage_c_invalidated_rows"
LOCK = OUT / ".round36_stage_c_runner.lock"
CANDIDATE = OUT / "stage_c_candidate_definition.json"
MATRIX = OUT / "stage_c_validation_matrix.csv"
COMMAND_FREEZE = OUT / "stage_c_command_freeze.json"
FROZEN_MANIFEST = OUT / "stage_c_frozen_manifest.json"
SUMMARY = OUT / "stage_c_runner_row_summary.csv"
START_RECORD = OUT / "stage_c_start_record.json"
FINAL_AUDIT = OUT / "stage_c_final_audit.json"
FINAL_REPORT = OUT / "stage_c_final_report.md"
CONTRACT_FIX_AUDIT = OUT / "stage_c_contract_fix_audit.json"
INVALIDATED_ATTEMPT_RECORD = (
    OUT / "stage_c_invalidated_attempt_1_contract_bug.json")
STAGE_B_EXE = r36.EXE
EXE = (ROOT / "build_round36_stage_c_contract_fix" / "official" /
       "gurobi" / "ExactEBRP.exe")
SHUTDOWN_MARGIN = 15
WATCHDOG_SEPARATION = 90
EXPECTED_ROWS = 47
ARM = "BW-P"
CAUSAL_ARM = "bw-p"
NORMALIZATION = "proof"
STARTUP = "hga-full"


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
                         encoding="utf-8", newline="\n")
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
    return r35.inventory()


def item_path(item: dict[str, Any]) -> Path:
    return ROOT / str(item["path"])


def command_for(row: dict[str, str], item: dict[str, Any],
                run_dir: Path) -> list[str]:
    """Construct the fixed best-proof + wide-anchor candidate command."""
    process_cap = int(row["process_cap_seconds"])
    args = [str(EXE), "--input", str(item_path(item))]
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
    for name, value in (
        ("--round34-c6-startup-variant", STARTUP),
        ("--round36-c6-causal-arm", CAUSAL_ARM),
        ("--round36-c6-split-normalization", NORMALIZATION),
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
    return r36.required_artifacts(run_dir)


def result_bounds(result: dict[str, Any]) -> tuple[float, float]:
    return r36.result_bounds(result)


def process_entry_time(result: dict[str, Any]) -> float:
    return r36.process_entry_time(result)
