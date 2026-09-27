#!/usr/bin/env python3
"""Contemporaneous implicit versus explicit Round 45 default-off sentinel."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path
import subprocess

import round44_common as common


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45"
EXE = ROOT / "build_round45" / "ExactEBRP.exe"
INSTANCE = "round39_small_medium_V8_M3_Q30_slot03_seed1177285734"


def replace(args: list[str], option: str, value: object) -> None:
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    if option in args:
        args[args.index(option) + 1] = rendered
    else:
        args.extend((option, rendered))


def load(path: Path):
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def run(explicit: bool) -> tuple[Path, dict]:
    label = "explicit" if explicit else "implicit"
    directory = OUT / "default_off_runs" / label
    directory.mkdir(parents=True, exist_ok=True)
    item = common.inventory()[INSTANCE]
    args = common.fair_candidate_command(
        item, directory, 120.0, execution="off", lookahead="frontier-d2",
        injection="all", scope="parent", family="no-adaptive",
        rho_f=0.5, rho_m=0.0, rho_h=0.0)
    args[0] = str(EXE)
    if explicit:
        replace(args, "--round45-adaptive-parametric-partition", "off")
    for option, value in (
        ("--round24-executable-sha256", common.sha256(EXE)),
        ("--round24-manifest-executable-sha256", common.sha256(EXE)),
        ("--process-phase-ledger", directory / "process_phases.csv"),
        ("--gurobi-progress", directory / "progress.csv"),
        ("--external-gini-artifact-dir", directory / "external"),
        ("--heuristic-candidates-csv", directory / "heuristic_candidates.csv"),
        ("--log", directory / "native.log"),
        ("--out", directory / "result.json"),
    ):
        replace(args, option, value)
    record = {"label": label, "command": args,
              "executable_sha256": common.sha256(EXE), "completed": False}
    common.write_json(directory / "command.json", record)
    with (directory / "stdout.log").open("wb") as stdout, \
            (directory / "stderr.log").open("wb") as stderr:
        process = subprocess.run(args, cwd=ROOT, env={**os.environ,
            "PYTHONDONTWRITEBYTECODE": "1"}, stdout=stdout, stderr=stderr,
            check=False, timeout=165)
    if process.returncode or not (directory / "result.json").is_file():
        raise RuntimeError(f"default-off {label} failed: {process.returncode}")
    record.update({"completed": True, "return_code": process.returncode})
    common.write_json(directory / "command.json", record)
    return directory, load(directory / "result.json")


def main() -> int:
    implicit_dir, implicit = run(False)
    explicit_dir, explicit = run(True)
    fields = (
        "status", "strict_certified_original_problem", "objective",
        "external_gini_tree_global_lower_bound",
        "external_gini_tree_verified_upper_bound",
        "external_gini_tree_split_count", "external_gini_tree_final_leaf_count",
        "external_gini_tree_lp_optimize_count",
        "external_gini_tree_terminal_mip_optimize_count",
        "external_gini_tree_root_coverage_valid",
    )
    mismatches = [field for field in fields
                  if implicit.get(field) != explicit.get(field)]
    rows = [{"pair": INSTANCE, "implicit_run": implicit_dir.name,
             "explicit_run": explicit_dir.name, "fields_compared": len(fields),
             "mismatch_count": len(mismatches), "mismatches": ";".join(mismatches),
             "passed": not mismatches, "round45_default": "off",
             "c6_changed": False}]
    with (OUT / "default_off_equivalence.csv").open(
            "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    common.write_json(OUT / "default_off_equivalence_manifest.json", {
        "schema": "round45-default-off-equivalence-v1",
        "executable_sha256": common.sha256(EXE), "pairs": 1,
        "passed": not mismatches, "mismatches": mismatches,
        "implicit_command_omits_round45_flag": True,
        "explicit_command_sets_round45_off": True,
    })
    print(json.dumps(rows[0], sort_keys=True))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
