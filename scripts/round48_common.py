#!/usr/bin/env python3
"""Frozen identities and deterministic helpers for Round 48 K1-AMF."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

import round46_common as round46


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_amf_formulation_rescue_round48"
RUNS = OUT / "runs"
TAU = 0.07915
MAX_PROCESS_CAP = 1800
CERTIFICATE_TOLERANCE = 1e-7
EXE = Path(os.environ.get(
    "EXACTEBRP_ROUND48_EXE",
    str(ROOT / "build" / "official-round48" / "ExactEBRP.exe")))

MECHANISM = (
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114",
    "round39_small_hard_V10_M3_Q20_slot04_seed1145042375",
    "round39_small_hard_V12_M3_Q20_slot07_seed621538683",
    "round39_small_hard_V12_M2_Q20_slot06_seed258908503",
    "high_imbalance_seed3201",
    "moderate_seed3301",
    "tight_T_seed3102",
)
EXISTING_CONFIRMATION = (
    "tight_T_seed3101", "high_imbalance_seed3202", "moderate_seed3302",
)
ADDITIONAL_CONFIRMATION = (
    "round39_small_hard_V10_M1_Q30_slot02_seed1721447042",
    "round39_small_hard_V12_M1_Q20_slot05_seed180890838",
    "round39_small_medium_V10_M1_Q20_slot04_seed1035775879",
    "round39_small_medium_V8_M3_Q30_slot03_seed1177285734",
)
STAGE5 = MECHANISM + EXISTING_CONFIRMATION + ADDITIONAL_CONFIRMATION

INSTANCE_PATHS = {
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363":
        "reference/qualification_round39/small-medium/round39_small_medium_V12_M3_Q30_slot08_seed1343324363.txt",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114":
        "reference/qualification_round39/small-hard/round39_small_hard_V12_M3_Q30_slot08_seed1288546114.txt",
    "round39_small_hard_V10_M3_Q20_slot04_seed1145042375":
        "reference/qualification_round39/small-hard/round39_small_hard_V10_M3_Q20_slot04_seed1145042375.txt",
    "round39_small_hard_V12_M3_Q20_slot07_seed621538683":
        "reference/qualification_round39/small-hard/round39_small_hard_V12_M3_Q20_slot07_seed621538683.txt",
    "round39_small_hard_V12_M2_Q20_slot06_seed258908503":
        "reference/qualification_round39/small-hard/round39_small_hard_V12_M2_Q20_slot06_seed258908503.txt",
    "high_imbalance_seed3201": "reference/hard_stress/V20_M3/high_imbalance_seed3201.txt",
    "moderate_seed3301": "reference/hard_stress/V20_M3/moderate_seed3301.txt",
    "tight_T_seed3102": "reference/hard_stress/V20_M3/tight_T_seed3102.txt",
    "tight_T_seed3101": "reference/hard_stress/V20_M3/tight_T_seed3101.txt",
    "high_imbalance_seed3202": "reference/hard_stress/V20_M3/high_imbalance_seed3202.txt",
    "moderate_seed3302": "reference/hard_stress/V20_M3/moderate_seed3302.txt",
    "round39_small_hard_V10_M1_Q30_slot02_seed1721447042":
        "reference/qualification_round39/small-hard/round39_small_hard_V10_M1_Q30_slot02_seed1721447042.txt",
    "round39_small_hard_V12_M1_Q20_slot05_seed180890838":
        "reference/qualification_round39/small-hard/round39_small_hard_V12_M1_Q20_slot05_seed180890838.txt",
    "round39_small_medium_V10_M1_Q20_slot04_seed1035775879":
        "reference/qualification_round39/small-medium/round39_small_medium_V10_M1_Q20_slot04_seed1035775879.txt",
    "round39_small_medium_V8_M3_Q30_slot03_seed1177285734":
        "reference/qualification_round39/small-medium/round39_small_medium_V8_M3_Q30_slot03_seed1177285734.txt",
}

ROLES = {
    MECHANISM[0]: "major_regression_retain",
    MECHANISM[1]: "strong_control_rescue",
    MECHANISM[2]: "harmful_split_negative_control",
    MECHANISM[3]: "numerical_endpoint_rescue",
    MECHANISM[4]: "v12_m2_formulation_deficit",
    MECHANISM[5]: "high_imbalance_development",
    MECHANISM[6]: "moderate_trajectory_guard",
    MECHANISM[7]: "tight3102_under_refinement",
    EXISTING_CONFIRMATION[0]: "tight_v20_confirmation",
    EXISTING_CONFIRMATION[1]: "high_imbalance_confirmation",
    EXISTING_CONFIRMATION[2]: "moderate_confirmation",
    ADDITIONAL_CONFIRMATION[0]: "unused_round39_hard_v10_m1_q30",
    ADDITIONAL_CONFIRMATION[1]: "unused_round39_hard_v12_m1_q20",
    ADDITIONAL_CONFIRMATION[2]: "unused_round39_medium_v10_m1_q20",
    ADDITIONAL_CONFIRMATION[3]: "unused_round39_medium_v8_m3_q30",
}


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
    """Replace one CLI value without changing the surrounding frozen command."""
    rendered = "true" if value is True else (
        "false" if value is False else format(value, ".17g")
        if isinstance(value, float) else str(value))
    if option in arguments:
        arguments[arguments.index(option) + 1] = rendered
    else:
        arguments.extend((option, rendered))


def remove_option(arguments: list[str], option: str) -> None:
    while option in arguments:
        index = arguments.index(option)
        del arguments[index:index + 2]


def frozen_instances() -> dict[str, dict[str, Any]]:
    freeze = load_json(OUT / "dataset_freeze.json")
    return {row["instance"]: row for row in freeze["instances"]}


def input_path(item: dict[str, Any]) -> Path:
    return ROOT / item["path"]


def historical_k1_am_command(item: dict[str, Any], run_dir: Path,
                             process_cap: float,
                             executable: Path) -> list[str]:
    """Build the unchanged Round 47 K1-AM command used by diagnostics."""
    command = round46.c6_command(
        item, run_dir, process_cap, 1, 0.01, executable)
    # The old C6 rho is inactive under adaptive-mass. Omit its explicit CLI
    # form so Round 48 commands cannot be mistaken for a rho-cap experiment.
    remove_option(command, "--c6-normalized-split-threshold")
    replace_option(command, "--round47-c6-adaptive-mass", "adaptive-mass")
    replace_option(command, "--round47-c6-adaptive-mass-tau", TAU)
    replace_option(command, "--round48-k1-amf", "off")
    replace_option(command, "--round48-counterfactual-mode", "off")
    replace_option(command, "--external-gini-artifact-dir", run_dir / "external")
    return command


def candidate_command(item: dict[str, Any], run_dir: Path,
                      process_cap: float,
                      executable: Path) -> list[str]:
    """Build the sole official Round 48 candidate command: K1-AMF."""
    command = historical_k1_am_command(
        item, run_dir, process_cap, executable)
    replace_option(command, "--round48-k1-amf", "k1-amf")
    return command


def counterfactual_command(item: dict[str, Any], run_dir: Path,
                           process_cap: float, interval: str, arm: str,
                           executable: Path) -> list[str]:
    if arm not in {"retain", "midpoint"}:
        raise ValueError(f"unsupported counterfactual arm: {arm}")
    if not interval:
        raise ValueError("counterfactual interval must be nonempty")
    command = historical_k1_am_command(
        item, run_dir, process_cap, executable)
    replace_option(command, "--round48-counterfactual-mode", arm)
    replace_option(command, "--round48-counterfactual-interval", interval)
    return command


def identity() -> dict[str, Any]:
    value = {
        "algorithm": "K1-AMF", "K0": 1, "point_rule": "midpoint",
        "tau": TAU, "formulation_profile":
            "round48-canonical-interval-sensitive-v1",
        "eligible_weighting": "equal_per_model_variable",
        "gini_coordinate_credit": False, "rho_cap": False,
        "contraction": False, "model_chain_inheritance_change": False,
        "extra_lp_queries": 0, "extra_mip_queries": 0,
        "gamma_veto": "off", "Gamma_sum": "off",
        "round43": "off", "round44": "off", "round45": "off",
        "PMM": "off", "FPMM": "off", "rank1": "off",
        "frontier_consolidation": "off", "verified_mip_starts": "off",
        "solver": {"Presolve": "Auto", "Seed": 0, "Threads": 1,
                   "MIPGap": 0.0, "MIPGapAbs": 0.0},
    }
    value["decision_identity_sha256"] = stable_hash(value)
    return value
