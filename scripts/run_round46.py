#!/usr/bin/env python3
"""Resume-safe staged orchestrator for the complete Round 46 screen."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import round46_common as common


DEVELOPMENT = [
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114",
    "round39_small_hard_V10_M1_Q20_slot01_seed561355351",
    "round39_small_medium_V10_M2_Q20_slot05_seed968549317",
    "round39_small_hard_V10_M3_Q20_slot04_seed1145042375",
    "round39_small_hard_V12_M3_Q20_slot07_seed621538683",
    "round39_small_easy_V12_M3_Q30_slot08_seed1167625600",
    "tight_T_seed3101", "high_imbalance_seed3201", "moderate_seed3301",
]
STAGE5 = [
    DEVELOPMENT[0], DEVELOPMENT[1], DEVELOPMENT[4],
    "tight_T_seed3101", "high_imbalance_seed3201", "moderate_seed3301",
    "tight_T_seed3102", "high_imbalance_seed3202", "moderate_seed3302",
    "round39_small_medium_V8_M2_Q20_slot02_seed890603285",
    "round39_small_hard_V10_M2_Q20_slot03_seed490008310",
    "round39_small_hard_V12_M2_Q20_slot06_seed258908503",
    "round39_small_medium_V10_M3_Q30_slot06_seed2147082032",
]


def result(stage: str, instance: str, arm: str) -> dict[str, Any]:
    path = common.RUNS / f"{stage}__{instance}__{arm}" / "result.json"
    value = common.load_json(path)
    return value[0] if isinstance(value, list) else value


def finite(value: Any, fallback: float = math.inf) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) else fallback
    except (TypeError, ValueError):
        return fallback


def relative_gap(value: dict[str, Any]) -> float:
    lower = finite(value.get("external_gini_tree_global_lower_bound",
                             value.get("lower_bound")))
    upper = finite(value.get("external_gini_tree_verified_upper_bound",
                             value.get("upper_bound")))
    if not math.isfinite(lower) or not math.isfinite(upper):
        return math.inf
    return max(0.0, upper - lower) / max(abs(upper), 1e-7)


def row_score(stage: str, arm: str, instances: list[str]) -> tuple[Any, ...]:
    values = [result(stage, name, arm) for name in instances]
    invalid = sum(bool(value.get("external_gini_tree_failure_reason")) or
                  value.get("external_gini_tree_root_coverage_valid") is False
                  for value in values)
    major = values[0]
    strong = values[1]
    v20 = values[-3:]
    v20_certificates = sum(bool(value.get(
        "strict_certified_original_problem")) for value in v20)
    gaps = [relative_gap(value) for value in values]
    works = [finite(value.get("external_gini_tree_work",
                              value.get("gurobi_work")), 1e30)
             for value in values]
    times = [finite(value.get("final_process_wall_time_seconds",
                              value.get("runtime_seconds")), 1e30)
             for value in values]
    return (invalid, relative_gap(major),
            finite(major.get("final_process_wall_time_seconds"), 1e30),
            relative_gap(strong), -v20_certificates,
            sum(gaps), sum(works), sum(times))


def invoke(executable: Path, stage: str, arm: str, instances: list[str],
           cap: int) -> None:
    command = [sys.executable, str(common.ROOT / "scripts" /
               "round46_experiment.py"), "--stage", stage, "--arm", arm,
               "--process-cap", str(cap), "--executable", str(executable)]
    if arm != "P-GRB":
        definition = next(row for row in common.load_json(
            common.OUT / "arm_definition.json")["arms"]
            if row["arm"] == arm)
        command += ["--k0", str(definition["K0"]),
                    "--rho", str(definition["rho"])]
    for instance in instances:
        command += ["--instance", instance]
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(command, cwd=common.ROOT, env=environment, check=True)


def assert_complete(stage: str, arms: list[str], instances: list[str]) -> None:
    missing = []
    for arm in arms:
        for instance in instances:
            marker = (common.RUNS / f"{stage}__{instance}__{arm}" /
                      "completion_marker.json")
            if not marker.is_file():
                missing.append(f"{stage}:{instance}:{arm}")
    if missing:
        raise RuntimeError(f"incomplete required rows: {missing}")


def freeze_stage3() -> list[str]:
    arms = list(common.ARM_BY_K_RHO.values())
    assert_complete("stage3_300s", arms, DEVELOPMENT)
    selections, rankings = [], []
    for k0 in common.K_GRID:
        choices = [common.ARM_BY_K_RHO[(k0, rho)]
                   for rho in common.RHO_GRID if rho != 0.01]
        ranked = sorted(choices, key=lambda arm: row_score(
            "stage3_300s", arm, DEVELOPMENT))
        selected = ranked[:2]
        selections.extend([common.ARM_BY_K_RHO[(k0, 0.01)], *selected])
        rankings.append({
            "K0": k0, "ordered_nonbaseline_arms": ranked,
            "selected_nonbaseline_arms": selected,
            "scores": {arm: row_score(
                "stage3_300s", arm, DEVELOPMENT) for arm in ranked},
        })
    common.write_json(common.OUT / "stage3_candidate_freeze.json", {
        "schema": "round46-stage3-candidate-freeze-v1",
        "frozen_before_stage4_results": True,
        "stage3_candidate_rows": 100, "selection_order":
            "frozen correctness/major/strong-control/V20/gap/Work/time tuple",
        "rankings": rankings, "stage4_arms": selections,
    })
    return selections


def freeze_stage4(arms: list[str]) -> list[str]:
    assert_complete("stage4_1200s", arms, DEVELOPMENT)
    finalists, rankings = [], []
    definitions = common.load_json(common.OUT / "arm_definition.json")["arms"]
    for k0 in common.K_GRID:
        choices = [arm for arm in arms if next(
            row["K0"] for row in definitions if row["arm"] == arm) == k0]
        ranked = sorted(choices, key=lambda arm: row_score(
            "stage4_1200s", arm, DEVELOPMENT))
        finalists.append(ranked[0])
        rankings.append({
            "K0": k0, "ordered_arms": ranked, "finalist": ranked[0],
            "scores": {arm: row_score(
                "stage4_1200s", arm, DEVELOPMENT) for arm in ranked},
        })
    common.write_json(common.OUT / "stage4_finalist_freeze.json", {
        "schema": "round46-stage4-finalist-freeze-v1",
        "frozen_before_v20_confirmation_opened": True,
        "stage4_candidate_rows": len(arms) * len(DEVELOPMENT),
        "rankings": rankings, "best_k4_arm": finalists[0],
        "best_k1_arm": finalists[1],
    })
    return finalists


def stage3(executable: Path) -> None:
    for (k0, rho), arm in common.ARM_BY_K_RHO.items():
        invoke(executable, "stage3_300s", arm, DEVELOPMENT, 300)
    invoke(executable, "stage3_300s", "P-GRB", DEVELOPMENT, 300)
    freeze_stage3()


def stage4(executable: Path) -> None:
    frozen = common.load_json(common.OUT / "stage3_candidate_freeze.json")
    arms = frozen["stage4_arms"]
    for arm in arms:
        invoke(executable, "stage4_1200s", arm, DEVELOPMENT, 1200)
    invoke(executable, "stage4_1200s", "P-GRB", DEVELOPMENT, 1200)
    freeze_stage4(arms)


def stage5(executable: Path) -> None:
    frozen = common.load_json(common.OUT / "stage4_finalist_freeze.json")
    arms = list(dict.fromkeys([
        "K4-r001", frozen["best_k4_arm"], frozen["best_k1_arm"]]))
    for arm in arms:
        invoke(executable, "stage5_1800s", arm, STAGE5, 1800)
    invoke(executable, "stage5_1800s", "P-GRB", STAGE5, 1800)
    assert_complete("stage5_1800s", [*arms, "P-GRB"], STAGE5)
    common.write_json(common.OUT / "stage5_completion.json", {
        "schema": "round46-stage5-completion-v1", "complete": True,
        "algorithm_arms": arms, "pgrb_arm": "P-GRB",
        "instances": STAGE5,
        "candidate_rows": len(arms) * len(STAGE5),
        "pgrb_rows": len(STAGE5), "maximum_cap_seconds": 1800,
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("stage3", "stage4", "stage5", "all"))
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    executable = args.executable.resolve()
    if not executable.is_file():
        raise SystemExit(f"missing official executable: {executable}")
    if "dev-gurobi-release" in executable.as_posix().lower():
        raise SystemExit("official orchestration cannot use development build")
    if args.action in {"stage3", "all"}:
        stage3(executable)
    if args.action in {"stage4", "all"}:
        stage4(executable)
    if args.action in {"stage5", "all"}:
        stage5(executable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
