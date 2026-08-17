#!/usr/bin/env python3
"""Frozen identities and deterministic I/O for Round 45."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

import round44_common as round44


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45"
RUNS = OUT / "runs"
BUILD = ROOT / "build_round45"
EXE = Path(os.environ.get(
    "EXACTEBRP_ROUND45_EXE", str(BUILD / "ExactEBRP.exe")))

BASE_BRANCH = "codex/round44-c6-envelope-tail-repair"
BASE_SHA = "7cd1ba335aada5a8438cc6c622ef6ec1e6c5061f"
BASE_TREE_SHA = "6e0637eb91c8703438e22ca97241c0c5f8dc4c82"
RESEARCH_BRANCH = "codex/round45-adaptive-timing-parametric-partition"

DEVELOPMENT_IDS = list(round44.DEVELOPMENT_IDS)
VALIDATION_IDS = list(round44.VALIDATION_IDS)
HOLDOUT_IDS = list(round44.HOLDOUT_IDS)
SMALL_IDS = DEVELOPMENT_IDS + VALIDATION_IDS + HOLDOUT_IDS
MECHANISM_ROLES = dict(round44.MECHANISM_ROLES)

MAJOR_WITNESS = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
STRONG_CONTROL = "round39_small_hard_V12_M3_Q30_slot08_seed1288546114"
STARTUP_PATHOLOGY = "round39_small_easy_V12_M3_Q30_slot08_seed1167625600"
NUMERIC_ENDPOINT = "round39_small_hard_V12_M3_Q20_slot07_seed621538683"

V20_DEVELOPMENT = [
    "reference/hard_stress/V20_M3/tight_T_seed3101.txt",
    "reference/hard_stress/V20_M3/high_imbalance_seed3201.txt",
    "reference/hard_stress/V20_M3/moderate_seed3301.txt",
]
V20_CONFIRMATION = [
    "reference/hard_stress/V20_M3/tight_T_seed3102.txt",
    "reference/hard_stress/V20_M3/high_imbalance_seed3202.txt",
    "reference/hard_stress/V20_M3/moderate_seed3302.txt",
]
V50_DEVELOPMENT = [
    "reference/qualification_round32/V50_M2/round32_multi_m_tight_T_V50_M2_seed104207248.txt",
    "reference/qualification_round32/V50_M2/round32_multi_m_high_imbalance_V50_M2_seed910922492.txt",
    "reference/qualification_round32/V50_M2/round32_multi_m_moderate_V50_M2_seed254020866.txt",
]
V50_CONFIRMATION = [
    "reference/qualification_round32/V50_M4/round32_multi_m_tight_T_V50_M4_seed1562257203.txt",
    "reference/qualification_round32/V50_M4/round32_multi_m_high_imbalance_V50_M4_seed163456187.txt",
    "reference/qualification_round32/V50_M4/round32_multi_m_moderate_V50_M4_seed721910669.txt",
]


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


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


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
    return round44.inventory()


def replace_option(arguments: list[str], option: str, value: Any) -> None:
    rendered = "true" if value is True else (
        "false" if value is False else str(value))
    if option in arguments:
        arguments[arguments.index(option) + 1] = rendered
    else:
        arguments.extend((option, rendered))
