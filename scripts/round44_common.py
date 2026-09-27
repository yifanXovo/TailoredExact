#!/usr/bin/env python3
"""Shared frozen identities, commands, and deterministic I/O for Round 44."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

import round43_common as round43


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_envelope_tail_repair_round44"
RUNS = OUT / "runs"
BUILD = ROOT / "build_round44"
EXE = Path(os.environ.get(
    "EXACTEBRP_ROUND44_EXE", str(BUILD / "ExactEBRP.exe")))

BASE_BRANCH = "codex/round43-k1-k4-envelope-refinement"
BASE_SHA = "3b4b50da3292a834c5731fb2c00f056a22c77cff"
BASE_TREE_SHA = "280d711a005d28d54b543606c976f48ce53f5a84"
RESEARCH_BRANCH = "codex/round44-c6-envelope-tail-repair"

MECHANISM_ROLES = dict(round43.MECHANISM_ROLES)
DEVELOPMENT_IDS = list(round43.DEVELOPMENT_IDS)
VALIDATION_IDS = list(round43.VALIDATION_IDS)
HOLDOUT_IDS = list(round43.HOLDOUT_IDS)
SMALL_24_IDS = DEVELOPMENT_IDS + VALIDATION_IDS + HOLDOUT_IDS

ADDITIONAL_V12 = [
    "reference/regen_candidate_V12_M1_average.txt",
    "reference/regen_candidate_V12_M2_average.txt",
]
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repository_text_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


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


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "yes"}


def replace_option(arguments: list[str], option: str, value: Any) -> None:
    rendered = "true" if value is True else (
        "false" if value is False else str(value))
    if option in arguments:
        index = arguments.index(option)
        arguments[index + 1] = rendered
    else:
        arguments.extend((option, rendered))


def bind_executable(arguments: list[str]) -> list[str]:
    arguments[0] = str(EXE)
    executable_hash = sha256(EXE)
    for option in ("--round24-executable-sha256",
                   "--round24-manifest-executable-sha256"):
        replace_option(arguments, option, executable_hash)
    return arguments


def inventory() -> dict[str, dict[str, Any]]:
    return round43.inventory()


def fair_candidate_command(
        item: dict[str, Any], run_dir: Path, process_cap: float, *,
        execution: str, lookahead: str, injection: str, scope: str,
        family: str, rho_f: float, rho_m: float, rho_h: float,
        rank1: str = "off", mip_starts: str = "off",
        consolidation: str = "off") -> list[str]:
    """Return the one shared default-off Round 44 C6 command path."""
    arguments = bind_executable(round43.fair_c6_command(
        item, run_dir, process_cap, execution="algorithm", K0=4,
        depth=1, rho=0.1, score="d", envelope="single"))
    replace_option(arguments, "--round43-envelope-refinement", "off")
    for option, value in (
        ("--round44-envelope-tail-repair", execution),
        ("--round44-initial-k0", 4),
        ("--round44-lookahead-policy", lookahead),
        ("--round44-envelope-injection", injection),
        ("--round44-envelope-scope", scope),
        ("--round44-refinement-family", family),
        ("--round44-rho-f", rho_f),
        ("--round44-rho-m", rho_m),
        ("--round44-rho-h", rho_h),
        ("--round44-rank1-cuts", rank1),
        ("--round44-mip-starts", mip_starts),
        ("--round44-frontier-consolidation", consolidation),
    ):
        replace_option(arguments, option, value)
    return arguments


def candidate_identity(*, execution: str, lookahead: str, injection: str,
                       scope: str, family: str, rho_f: float, rho_m: float,
                       rho_h: float, rank1: str = "off",
                       mip_starts: str = "off",
                       consolidation: str = "off") -> dict[str, Any]:
    value = {
        "K0": 4,
        "execution": execution,
        "lookahead": lookahead,
        "injection": injection,
        "scope": scope,
        "family": family,
        "rho_F": rho_f,
        "rho_M": rho_m,
        "rho_H": rho_h,
        "rank1": rank1,
        "mip_starts": mip_starts,
        "consolidation": consolidation,
    }
    value["decision_identity_sha256"] = stable_hash(value)
    return value
