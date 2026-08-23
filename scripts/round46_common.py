#!/usr/bin/env python3
"""Frozen identities, commands, and deterministic I/O for Round 46."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

import round43_common as round43


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_rho_k1_k4_screen_round46"
RUNS = OUT / "runs"
EXE = Path(os.environ.get(
    "EXACTEBRP_ROUND46_EXE", str(ROOT / "build" / "official-round46" /
                                  "ExactEBRP.exe")))

RHO_GRID = (0.01, 0.12, 0.15, 0.20, 0.50)
K_GRID = (4, 1)
ARM_BY_K_RHO = {
    (k0, rho): f"K{k0}-r{int(round(rho * 100)):03d}"
    for k0 in K_GRID for rho in RHO_GRID
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
        writer = csv.DictWriter(
            stream, fieldnames=columns, extrasaction="ignore")
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


def remove_option(arguments: list[str], option: str) -> None:
    while option in arguments:
        index = arguments.index(option)
        del arguments[index:index + 2]


def frozen_instances() -> dict[str, dict[str, Any]]:
    freeze = load_json(OUT / "dataset_freeze.json")
    return {row["instance"]: row for row in freeze["instances"]}


def input_path(item: dict[str, Any]) -> Path:
    return ROOT / item["path"]


def _template_item(item: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    previous = round43.inventory()
    if item["instance"] in previous:
        return previous[item["instance"]], True
    return dict(next(iter(previous.values()))), False


def _bind_common(command: list[str], item: dict[str, Any], run_dir: Path,
                 process_cap: float, executable: Path) -> list[str]:
    command[0] = str(executable.resolve())
    replace_option(command, "--input", str(input_path(item).resolve()))
    replace_option(command, "--process-wall-time-limit", process_cap)
    replace_option(command, "--time-limit", max(1.0, process_cap - 6.0))
    replace_option(command, "--progress-log", str(run_dir / "progress.csv"))
    replace_option(command, "--process-phase-ledger",
                   str(run_dir / "process_phases.csv"))
    replace_option(command, "--log", str(run_dir / "native.log"))
    replace_option(command, "--out", str(run_dir / "result.json"))
    replace_option(command, "--threads", 1)
    replace_option(command, "--mip-threads", 1)
    replace_option(command, "--gurobi-seed", 0)
    replace_option(command, "--gurobi-presolve", -1)
    executable_hash = sha256(executable)
    replace_option(command, "--round24-executable-sha256", executable_hash)
    replace_option(command, "--round24-manifest-executable-sha256",
                   executable_hash)
    if item["instance"] not in round43.inventory():
        replace_option(command, "--T", 3600.0)
        remove_option(command, "--round24-expected-gurobi-model-fingerprint")
    return command


def c6_command(item: dict[str, Any], run_dir: Path, process_cap: float,
               k0: int, rho: float, executable: Path) -> list[str]:
    template, _ = _template_item(item)
    command = round43.fair_c6_command(
        template, run_dir, process_cap, execution="off", K0=4,
        depth=1, rho=0.1, score="d", envelope="single")
    _bind_common(command, item, run_dir, process_cap, executable)
    replace_option(command, "--round40-c6-coarse-start",
                   "off" if k0 == 4 else "k1-adaptive")
    replace_option(command, "--c6-normalized-split-threshold", rho)
    replace_option(command, "--round43-envelope-refinement", "off")
    replace_option(command, "--round43-lifted-cuts", "off")
    replace_option(command, "--round43-frontier-consolidation", "off")
    replace_option(command, "--round44-envelope-tail-repair", "off")
    replace_option(command, "--round44-rank1-cuts", "off")
    replace_option(command, "--round44-mip-starts", "off")
    replace_option(command, "--round44-frontier-consolidation", "off")
    replace_option(command, "--round45-adaptive-parametric-partition", "off")
    replace_option(command, "--round45-point-rule", "midpoint")
    replace_option(command, "--external-gini-artifact-dir",
                   str(run_dir / "external"))
    return command


def pgrb_command(item: dict[str, Any], run_dir: Path, process_cap: float,
                 executable: Path) -> list[str]:
    template, _ = _template_item(item)
    command = round43.fair_pgrb_command(template, run_dir, process_cap)
    _bind_common(command, item, run_dir, process_cap, executable)
    replace_option(command, "--gurobi-hga-start", True)
    return command


def identity(arm: str, k0: int | None, rho: float | None) -> dict[str, Any]:
    value = {
        "arm": arm, "K0": k0, "rho": rho,
        "rho_explicit": rho is not None,
        "rho_source": "explicit" if rho is not None else "not_applicable",
        "point_rule": "midpoint" if rho is not None else "not_applicable",
        "gamma_veto": "off", "Gamma_sum": "off",
        "round43": "off", "round44": "off", "round45": "off",
        "PMM": "off", "FPMM": "off", "rank1": "off",
        "frontier_consolidation": "off", "verified_mip_starts": "off",
        "solver": {"Presolve": "Auto", "Seed": 0, "Threads": 1,
                   "MIPGap": 0.0, "MIPGapAbs": 0.0},
    }
    value["decision_identity_sha256"] = stable_hash(value)
    return value
