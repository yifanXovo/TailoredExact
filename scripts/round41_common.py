#!/usr/bin/env python3
"""Shared paths and frozen command construction for Round 41."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

import round40_common as round40


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_decomposition_single_tree_round41"
RUNS = OUT / "runs"
BUILD = ROOT / "build_round41"
EXE = Path(os.environ.get(
    "EXACTEBRP_ROUND41_EXE", str(BUILD / "ExactEBRP.exe")))


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
    return round40.inventory()


def fair_c6_command(item: dict[str, Any], run_dir: Path,
                    process_cap: float) -> list[str]:
    args = round40.fair_command(
        item, "C6-HGA-FULL-K4", run_dir, -1, process_cap)
    args[0] = str(EXE)
    executable_hash = sha256(EXE)
    for option in ("--round24-executable-sha256",
                   "--round24-manifest-executable-sha256"):
        if option in args:
            round40.replace_all(args, option, executable_hash)
    return args


def fair_pgrb_command(item: dict[str, Any], run_dir: Path,
                      process_cap: float) -> list[str]:
    args = round40.fair_command(
        item, "P-GRB", run_dir, -1, process_cap)
    args[0] = str(EXE)
    executable_hash = sha256(EXE)
    for option in ("--round24-executable-sha256",
                   "--round24-manifest-executable-sha256"):
        if option in args:
            round40.replace_all(args, option, executable_hash)
    return args
