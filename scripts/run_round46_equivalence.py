#!/usr/bin/env python3
"""Run the implicit/explicit rho=0.01 semantic equivalence sentinel."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import subprocess

import round46_common as common


INSTANCE = "round39_small_medium_V10_M2_Q20_slot05_seed968549317"
FIELDS = (
    "status", "strict_certified_original_problem",
    "strict_certificate_class", "strict_certificate_rejection_reason",
    "external_gini_tree_failure_reason",
    "external_gini_tree_root_coverage_valid",
    "external_gini_tree_parent_child_coverage_valid",
    "external_gini_tree_global_lower_bound",
    "external_gini_tree_verified_upper_bound",
    "external_gini_tree_initial_leaf_count",
    "external_gini_tree_final_leaf_count",
    "external_gini_tree_split_count",
    "external_gini_tree_declined_split_count",
    "external_gini_tree_lp_optimize_count",
    "external_gini_tree_partial_mip_optimize_count",
    "external_gini_tree_terminal_mip_optimize_count",
)


def remove_option(command: list[str], option: str) -> None:
    index = command.index(option)
    del command[index:index + 2]


def decision_projection(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    for row in rows:
        row.pop("rho", None)
        row.pop("rho_source", None)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--process-cap", type=float, default=120.0)
    args = parser.parse_args()
    executable = args.executable.resolve()
    if not executable.is_file():
        raise SystemExit(f"missing executable: {executable}")
    item = common.frozen_instances()[INSTANCE]
    root = common.OUT / "equivalence_runs"
    results = {}
    commands = {}
    for mode in ("implicit", "explicit"):
        run_dir = root / mode
        run_dir.mkdir(parents=True, exist_ok=True)
        command = common.c6_command(
            item, run_dir, args.process_cap, 4, 0.01, executable)
        if mode == "implicit":
            remove_option(command, "--c6-normalized-split-threshold")
        common.write_json(run_dir / "command.json", {
            "mode": mode, "rho": 0.01,
            "rho_explicit": mode == "explicit", "command": command,
            "executable_sha256": common.sha256(executable),
        })
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            command, cwd=common.ROOT, env=environment, check=False,
            timeout=args.process_cap + 45.0)
        if completed.returncode:
            raise SystemExit(f"{mode} sentinel failed: {completed.returncode}")
        value = common.load_json(run_dir / "result.json")
        results[mode] = value[0] if isinstance(value, list) else value
        commands[mode] = command
    comparisons = []
    for field in FIELDS:
        left, right = results["implicit"].get(field), results["explicit"].get(field)
        comparisons.append({
            "check": field, "implicit": left, "explicit": right,
            "equal": left == right,
        })
    trace_equal = decision_projection(
        root / "implicit" / "external" / "c6_split_decision_ledger.csv") == \
        decision_projection(
            root / "explicit" / "external" / "c6_split_decision_ledger.csv")
    comparisons.append({
        "check": "c6_decision_trace_excluding_rho_identity",
        "implicit": "projected_trace", "explicit": "projected_trace",
        "equal": trace_equal,
    })
    common.write_csv(common.OUT / "default_off_equivalence.csv", comparisons)
    passed = all(row["equal"] for row in comparisons)
    common.write_json(common.OUT / "default_off_equivalence.json", {
        "schema": "round46-default-equivalence-v1", "passed": passed,
        "instance": INSTANCE, "process_cap_seconds": args.process_cap,
        "executable_sha256": common.sha256(executable),
        "implicit_command_omits_rho_option":
            "--c6-normalized-split-threshold" not in commands["implicit"],
        "explicit_command_supplies_rho_001":
            "--c6-normalized-split-threshold" in commands["explicit"],
    })
    print(json.dumps({"passed": passed, "checks": len(comparisons)},
                     sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
