#!/usr/bin/env python3
"""Frozen identities, commands, panels, and deterministic I/O for Round 47."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

import round46_common as round46


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_adaptive_mass_contraction_round47"
RUNS = OUT / "runs"
EXE = Path(os.environ.get(
    "EXACTEBRP_ROUND47_EXE",
    str(ROOT / "build" / "official-round47" / "ExactEBRP.exe")))

TAU = 0.07915
ARMS = ("K4-AM", "K4-AMC", "K1-AM", "K1-AMC")
ARM_DEFINITIONS = {
    "K4-AM": {"K0": 4, "mode": "adaptive-mass", "contraction": False},
    "K4-AMC": {"K0": 4, "mode": "adaptive-mass-contraction", "contraction": True},
    "K1-AM": {"K0": 1, "mode": "adaptive-mass", "contraction": False},
    "K1-AMC": {"K0": 1, "mode": "adaptive-mass-contraction", "contraction": True},
}

DEVELOPMENT = (
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114",
    "round39_small_hard_V10_M1_Q20_slot01_seed561355351",
    "round39_small_medium_V10_M2_Q20_slot05_seed968549317",
    "round39_small_hard_V10_M3_Q20_slot04_seed1145042375",
    "round39_small_hard_V12_M3_Q20_slot07_seed621538683",
    "round39_small_easy_V12_M3_Q30_slot08_seed1167625600",
    "tight_T_seed3101",
    "high_imbalance_seed3201",
    "moderate_seed3301",
)

STAGE5 = (
    DEVELOPMENT[0], DEVELOPMENT[1], DEVELOPMENT[4], DEVELOPMENT[5],
    DEVELOPMENT[7], DEVELOPMENT[8], DEVELOPMENT[9],
    "tight_T_seed3102", "high_imbalance_seed3202", "moderate_seed3302",
    "round39_small_medium_V8_M2_Q20_slot02_seed890603285",
    "round39_small_hard_V10_M2_Q20_slot03_seed490008310",
    "round39_small_hard_V12_M2_Q20_slot06_seed258908503",
    "round39_small_medium_V10_M3_Q30_slot06_seed2147082032",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    material = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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
              fields: list[str] | None = None, *, allow_empty: bool = False) -> None:
    material = list(rows)
    if not material and not (allow_empty and fields):
        raise ValueError(f"cannot write empty CSV: {path}")
    columns = fields or list(material[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)
    temporary.replace(path)


def replace_option(arguments: list[str], option: str, value: Any) -> None:
    rendered = "true" if value is True else (
        "false" if value is False else format(value, ".17g")
        if isinstance(value, float) else str(value))
    if option in arguments:
        arguments[arguments.index(option) + 1] = rendered
    else:
        arguments.extend((option, rendered))


def frozen_instances() -> dict[str, dict[str, Any]]:
    freeze = load_json(OUT / "dataset_freeze.json")
    return {row["instance"]: row for row in freeze["instances"]}


def input_path(item: dict[str, Any]) -> Path:
    return ROOT / item["path"]


def candidate_command(item: dict[str, Any], run_dir: Path, process_cap: float,
                      arm: str, executable: Path) -> list[str]:
    definition = ARM_DEFINITIONS[arm]
    command = round46.c6_command(
        item, run_dir, process_cap, definition["K0"], 0.01, executable)
    # Rho remains explicitly at the historical default but is not the active
    # Round 47 finite-child gate.
    replace_option(command, "--round47-c6-adaptive-mass", definition["mode"])
    replace_option(command, "--round47-c6-adaptive-mass-tau", TAU)
    replace_option(command, "--external-gini-artifact-dir", run_dir / "external")
    return command


def identity(arm: str) -> dict[str, Any]:
    definition = ARM_DEFINITIONS[arm]
    value = {
        "arm": arm,
        "K0": definition["K0"],
        "mode": definition["mode"],
        "contraction": definition["contraction"],
        "tau": TAU,
        "point_rule": "midpoint",
        "score_inputs": ["parent_lower_bound", "left_child_lp_bound",
                         "right_child_lp_bound", "verified_incumbent",
                         "strict_child_infeasibility", "certificate_tolerance"],
        "extra_lp_queries": 0,
        "extra_mip_queries": 0,
        "gamma_veto": "off", "Gamma_sum": "off",
        "round43": "off", "round44": "off", "round45": "off",
        "PMM": "off", "FPMM": "off", "rank1": "off",
        "frontier_consolidation": "off", "verified_mip_starts": "off",
        "solver": {"Presolve": "Auto", "Seed": 0, "Threads": 1,
                   "MIPGap": 0.0, "MIPGapAbs": 0.0},
    }
    value["decision_identity_sha256"] = stable_hash(value)
    return value
