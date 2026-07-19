#!/usr/bin/env python3
"""Static manifest, dispatch, and protocol gates for Round 23."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_global_gini_tree_round23"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    stable = json.loads((OUT / "stable_s0_reference_manifest.json").read_text())
    corrected = json.loads((OUT / "corrected_s0_manifest.json").read_text())
    candidate = json.loads((OUT / "round23_candidate_manifest.json").read_text())
    require(stable["flow"] == "round20-current", "F0 is not stable")
    require(stable["optional_candidate_mechanism"] == "off",
            "candidate does not default off")
    require(stable["child_estimate"] == corrected["child_estimate"] == "parent-copy",
            "mechanism-off is not corrected S0")
    require(candidate["child_estimate"] == "dispersion-coupled",
            "candidate mechanism mismatch")
    for key in ("flow", "presolve", "preprocessing_reduce", "preprocessing_linear"):
        require(corrected[key] == candidate[key], f"candidate changed {key}")
    for key in ("mechanism_changes_rows", "mechanism_changes_bounds",
                "mechanism_changes_objective", "mechanism_changes_pruning"):
        require(candidate[key] is False, f"candidate unexpectedly changes {key}")

    with (OUT / "round23_instance_manifest.csv").open(newline="") as stream:
        instances = list(csv.DictReader(stream))
    require(len(instances) == 6, "fixed subset changed")
    for row in instances:
        path = ROOT / row["path"]
        require(path.exists(), f"instance missing: {path}")
        require(sha(path) == row["sha256"], f"instance hash mismatch: {path}")
        require(row["algorithm_dispatch_allowed"] == "false",
                "instance dispatch was permitted")

    api = (ROOT / "src/TailoredBCCplexApi.cpp").read_text(encoding="utf-8")
    bound = (ROOT / "src/DispersionChildBound.cpp").read_text(encoding="utf-8")
    correction = api + bound
    for token in ("moderate_seed4301", "seed4301", "67459d3ab38ff69f",
                  "8841820f8028da45"):
        require(token not in correction, f"benchmark-specific correction token: {token}")
    require("instance.V <= 1" in bound,
            "mathematical V<=1 domain guard missing")
    for prohibited in ("instance.name", "input_path", "elapsed_wall_time",
                       "solve_time_limit", "benchmark_family"):
        require(prohibited not in bound,
                f"mechanism dispatcher/control found: {prohibited}")
    require("computeDispersionCoupledChildEstimate" in api,
            "candidate is not wired to the common callback")
    require("flow_resolution.resolved" not in bound,
            "candidate contains flow-specific logic")

    runner = (ROOT / "scripts/run_round23_targeted_validation.py").read_text(
        encoding="utf-8")
    require("STAGE1 = (\"V12_M2\", \"high_imbalance_seed3202\", \"tight_T_seed3101\")" in runner,
            "Stage 1 subset changed")
    require("native = budget - 18" in runner, "reserve policy changed")
    require("for arm in ARMS" in runner, "matched arm loop missing")
    require("plain" not in runner.split("def run_one", 1)[1].split("def write_stage_summary", 1)[0],
            "plain-to-Tailored channel found")
    print("Round23RunnerIntegrityTests: 28 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
