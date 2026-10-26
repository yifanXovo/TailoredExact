#!/usr/bin/env python3
"""Verify that the Round 49 research mode is inert when default-off."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import subprocess

import round49_common as common


INSTANCE = "round39_small_hard_V10_M3_Q20_slot04_seed1145042375"
FIELDS = (
    "status", "strict_certified_original_problem", "strict_certificate_class",
    "strict_certificate_rejection_reason", "external_gini_tree_failure_reason",
    "external_gini_tree_root_coverage_valid",
    "external_gini_tree_parent_child_coverage_valid",
    "external_gini_tree_global_lower_bound",
    "external_gini_tree_verified_upper_bound",
    "external_gini_tree_initial_leaf_count",
    "external_gini_tree_final_leaf_count", "external_gini_tree_split_count",
    "external_gini_tree_declined_split_count",
    "external_gini_tree_lp_optimize_count",
    "external_gini_tree_partial_mip_optimize_count",
    "external_gini_tree_terminal_mip_optimize_count",
    "round47_adaptive_mass_decision_count",
)


def normalized(path: Path) -> dict:
    value = common.load_json(path)
    return value[0] if isinstance(value, list) else value


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--process-cap", type=float, default=120.0)
    args = parser.parse_args()
    if args.process_cap <= 0 or args.process_cap > common.MAX_PROCESS_CAP:
        raise SystemExit("sentinel cap must satisfy 0 < cap <= 1800")
    executable = args.executable.resolve()
    if not executable.is_file():
        raise SystemExit(f"missing executable: {executable}")
    item = common.frozen_instances()[INSTANCE]
    root = common.OUT / "default_off_equivalence_runs"
    results: dict[str, dict] = {}
    commands: dict[str, list[str]] = {}
    for mode in ("implicit", "explicit"):
        run_dir = root / mode
        run_dir.mkdir(parents=True, exist_ok=True)
        command = common.historical_k1_am_command(
            item, run_dir, args.process_cap, executable)
        if mode == "implicit":
            common.remove_option(command, "--round49-k1-am-rc")
        common.write_json(run_dir / "command.json", {
            "schema": "round49-default-off-command-v1",
            "mode": mode,
            "round49_k1_am_rc":
                "implicit-default" if mode == "implicit" else "off",
            "command": command,
            "executable_sha256": common.sha256(executable),
            "correctness_sentinel_not_benchmark_row": True,
        })
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            command, cwd=common.ROOT, env=env, check=False,
            timeout=args.process_cap + 45.0)
        if completed.returncode:
            raise SystemExit(f"{mode} sentinel failed: {completed.returncode}")
        results[mode] = normalized(run_dir / "result.json")
        commands[mode] = command
    comparisons = []
    for field in FIELDS:
        left = results["implicit"].get(field)
        right = results["explicit"].get(field)
        comparisons.append({"check": field, "implicit": left,
                            "explicit": right, "equal": left == right})
    for ledger in ("adaptive_mass_decision_ledger.csv",
                   "c6_split_decision_ledger.csv",
                   "parent_child_bound_ledger.csv"):
        left = rows(root / "implicit" / "external" / ledger)
        right = rows(root / "explicit" / "external" / ledger)
        comparisons.append({
            "check": f"exact_{ledger}_rows", "implicit": len(left),
            "explicit": len(right), "equal": left == right,
        })
    common.write_csv(common.OUT / "default_off_equivalence.csv", comparisons)
    passed = all(row["equal"] for row in comparisons)
    common.write_json(common.OUT / "default_off_equivalence.json", {
        "schema": "round49-default-off-equivalence-v1",
        "passed": passed,
        "instance": INSTANCE,
        "process_cap_seconds": args.process_cap,
        "executable_sha256": common.sha256(executable),
        "historical_mode": "K1-AM",
        "correctness_sentinel_not_benchmark_row": True,
        "implicit_command_omits_round49_option":
            "--round49-k1-am-rc" not in commands["implicit"],
        "explicit_command_supplies_off":
            commands["explicit"][commands["explicit"].index(
                "--round49-k1-am-rc") + 1] == "off",
    })
    print(json.dumps({"passed": passed, "checks": len(comparisons)},
                     sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
