#!/usr/bin/env python3
"""Shared frozen identities and deterministic I/O for Round 43."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

import round42_common as round42


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_k4_envelope_refinement_round43"
RUNS = OUT / "runs"
BUILD = ROOT / "build_round43"
EXE = Path(os.environ.get(
    "EXACTEBRP_ROUND43_EXE", str(BUILD / "ExactEBRP.exe")))

BASE_BRANCH = "codex/round42-decomposition-architecture-optimization"
BASE_SHA = "a188181a3257270eebc6d546b121a168184ae951"
RESEARCH_BRANCH = "codex/round43-k1-k4-envelope-refinement"

MECHANISM_ROLES = {
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363":
        "major_fragmentation_regression",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114":
        "strongest_k4_positive_control",
    "round39_small_hard_V10_M1_Q20_slot01_seed561355351":
        "hard_p_grb_win_guard",
    "round39_small_medium_V10_M2_Q20_slot05_seed968549317":
        "medium_c6_win_guard",
    "round39_small_hard_V10_M3_Q20_slot04_seed1145042375":
        "hard_c6_win_guard",
    "round39_small_hard_V12_M3_Q20_slot07_seed621538683":
        "numerical_fail_closed_endpoint",
}

DEVELOPMENT_IDS = [
    "round39_small_easy_V10_M1_Q30_slot04_seed1099392856",
    "round39_small_easy_V12_M3_Q30_slot08_seed1167625600",
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363",
    "round39_small_medium_V8_M3_Q30_slot03_seed1177285734",
    "round39_small_medium_V10_M2_Q20_slot05_seed968549317",
    "round39_small_hard_V10_M1_Q30_slot02_seed1721447042",
    "round39_small_hard_V10_M1_Q20_slot01_seed561355351",
    "round39_small_hard_V12_M3_Q20_slot07_seed621538683",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114",
    "round39_small_hard_V10_M3_Q20_slot04_seed1145042375",
]

VALIDATION_IDS = [
    "round39_small_easy_V8_M1_Q30_slot01_seed432322553",
    "round39_small_easy_V10_M3_Q20_slot06_seed1178207568",
    "round39_small_easy_V12_M2_Q30_slot07_seed1210444511",
    "round39_small_medium_V8_M2_Q20_slot02_seed890603285",
    "round39_small_medium_V12_M1_Q30_slot07_seed907224013",
    "round39_small_hard_V12_M1_Q20_slot05_seed180890838",
    "round39_small_hard_V10_M2_Q20_slot03_seed490008310",
]

HOLDOUT_IDS = [
    "round39_small_easy_V8_M2_Q30_slot03_seed1019524729",
    "round39_small_easy_V8_M2_Q20_slot02_seed944712007",
    "round39_small_easy_V10_M2_Q30_slot05_seed332426708",
    "round39_small_hard_V12_M2_Q20_slot06_seed258908503",
    "round39_small_medium_V8_M1_Q20_slot01_seed244478273",
    "round39_small_medium_V10_M3_Q30_slot06_seed2147082032",
    "round39_small_medium_V10_M1_Q20_slot04_seed1035775879",
]

CONTEMPORARY_REFERENCE_IDS = {
    "round39_small_easy_V10_M1_Q30_slot04_seed1099392856":
        "easy_startup_guard",
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363":
        "major_fragmentation_regression",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114":
        "strongest_k4_positive_control",
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
    return round42.inventory()


def replace_option(arguments: list[str], option: str, value: Any) -> None:
    rendered = "true" if value is True else (
        "false" if value is False else str(value))
    if option in arguments:
        index = arguments.index(option)
        arguments[index + 1] = rendered
    else:
        arguments.extend((option, rendered))


def _bind_round43_executable(arguments: list[str]) -> list[str]:
    arguments[0] = str(EXE)
    executable_hash = sha256(EXE)
    for option in ("--round24-executable-sha256",
                   "--round24-manifest-executable-sha256"):
        replace_option(arguments, option, executable_hash)
    return arguments


def fair_c6_command(item: dict[str, Any], run_dir: Path,
                    process_cap: float, *, execution: str,
                    K0: int, depth: int, rho: float,
                    score: str = "d", envelope: str = "single") -> list[str]:
    arguments = _bind_round43_executable(
        round42.fair_c6_command(item, run_dir, process_cap))
    for option, value in (
        ("--round43-envelope-refinement", execution),
        ("--round43-initial-k0", K0),
        ("--round43-lookahead-depth", depth),
        ("--round43-rho", rho),
        ("--round43-score", score),
        ("--round43-envelope-mode", envelope),
        ("--round43-width-measure", "g-mccormick-unit"),
        ("--round43-lifted-cuts", "off"),
        ("--round43-frontier-consolidation", "off"),
    ):
        replace_option(arguments, option, value)
    return arguments


def fair_pgrb_command(item: dict[str, Any], run_dir: Path,
                      process_cap: float) -> list[str]:
    arguments = _bind_round43_executable(
        round42.fair_pgrb_command(item, run_dir, process_cap))
    # Round 43's comparison contract requires the same independently verified
    # HGA-FULL startup incumbent for the monolithic P-GRB reference and C6.
    replace_option(arguments, "--gurobi-hga-start", True)
    return arguments
