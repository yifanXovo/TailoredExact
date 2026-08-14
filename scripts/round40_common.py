#!/usr/bin/env python3
"""Shared identities and command construction for Round 40."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import round39_common as round39


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_regression_adaptive_round40"
RUNS = OUT / "runs"
BUILD = ROOT / "build_round40"
EXE = BUILD / "ExactEBRP.exe"
PRESOLVE_MANIFEST = OUT / "presolve_fairness_manifest.csv"
SHUTDOWN_MARGIN = 20


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
    return round39.inventory()


def fingerprint_values() -> dict[str, int]:
    return round39.fingerprint_values()


def replace_all(args: list[str], name: str, value: object) -> None:
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    found = False
    for index, token in enumerate(args[:-1]):
        if token == name:
            args[index + 1] = rendered
            found = True
    if not found:
        raise RuntimeError(f"frozen option missing: {name}")


def _round40_executable(args: list[str]) -> list[str]:
    args[0] = str(EXE)
    executable_hash = sha256(EXE)
    for option in ("--round24-executable-sha256",
                   "--round24-manifest-executable-sha256"):
        if option in args:
            replace_all(args, option, executable_hash)
    return args


def fair_command(item: dict[str, Any], arm: str, run_dir: Path,
                 presolve: int, process_cap: float) -> list[str]:
    fingerprint = fingerprint_values()[item["instance_id"]]
    if arm == "P-GRB":
        args = round39.plain_command(
            item, run_dir, fingerprint, process_cap=process_cap,
            shutdown_margin=SHUTDOWN_MARGIN)
    elif arm == "C6-HGA-FULL-K4":
        args = round39.c6_command(
            item, "C6-HGA-FULL", run_dir, fingerprint,
            process_cap=process_cap)
    else:
        raise ValueError(f"unknown Round 40 arm: {arm}")
    _round40_executable(args)
    replace_all(args, "--gurobi-presolve", presolve)
    return args


def c6_policy_command(item: dict[str, Any], arm: str, run_dir: Path,
                      process_cap: float) -> list[str]:
    policies = {
        "C6-HGA-FULL-K4": "off",
        "C6-K1-SINGLE": "k1-single",
        "C6-K1-ADAPTIVE": "k1-adaptive",
        "C6-K1-ADAPTIVE-DECISIVE": "k1-adaptive-decisive",
    }
    if arm not in policies:
        raise ValueError(f"unknown Round 40 C6 policy arm: {arm}")
    args = fair_command(
        item, "C6-HGA-FULL-K4", run_dir, -1, process_cap)
    args.extend(("--round40-c6-coarse-start", policies[arm]))
    return args


def c6_ub_geometry_command(item: dict[str, Any], arm: str, run_dir: Path,
                           process_cap: float) -> list[str]:
    policies = {
        "C6-HGA-FULL-K4": "off",
        "C6-NESTED-DYADIC-K4": "nested-dyadic-k4",
    }
    if arm not in policies:
        raise ValueError(f"unknown Round 40 UB-geometry arm: {arm}")
    args = fair_command(
        item, "C6-HGA-FULL-K4", run_dir, -1, process_cap)
    args.extend(("--round40-c6-ub-geometry", policies[arm]))
    return args


def result_bounds(arm: str, result: dict[str, Any]) -> tuple[float, float]:
    if arm.startswith("C6-"):
        return (
            float(result["external_gini_tree_global_lower_bound"]),
            float(result["external_gini_tree_verified_upper_bound"]),
        )
    return float(result["lower_bound"]), float(result["upper_bound"])
