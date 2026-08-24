#!/usr/bin/env python3
"""Resume-safe orchestrator for the complete Round 47 study."""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import round47_common as common


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


def work(value: dict[str, Any]) -> float:
    return finite(value.get("external_gini_tree_work", value.get("work")), 1e30)


def elapsed(value: dict[str, Any]) -> float:
    return finite(value.get("final_process_wall_time_seconds",
                            value.get("runtime_seconds")), 1e30)


def model_count(value: dict[str, Any]) -> float:
    return finite(value.get("external_gini_tree_model_count"), 1e30)


def selection_score(arm: str) -> tuple[Any, ...]:
    values = {name: result("stage4_1200s", name, arm)
              for name in common.DEVELOPMENT}
    invalid = sum(bool(value.get("strict_certified_original_problem")) and
                  value.get("external_gini_tree_root_coverage_valid") is False
                  for value in values.values())
    major = values[common.DEVELOPMENT[0]]
    strong = values[common.DEVELOPMENT[1]]
    numerical = values[common.DEVELOPMENT[5]]
    high = values["high_imbalance_seed3201"]
    moderate = values["moderate_seed3301"]
    tight = values["tight_T_seed3101"]
    high_cert = bool(high.get("strict_certified_original_problem"))
    severe_numerical = bool(numerical.get(
        "strict_certified_original_problem")) and numerical.get(
            "external_gini_tree_root_coverage_valid") is False
    gaps = sum(relative_gap(value) for value in values.values())
    works = sum(work(value) for value in values.values())
    times = sum(elapsed(value) for value in values.values())
    models = sum(model_count(value) for value in values.values())
    simplicity = 0 if arm.endswith("-AM") else 1
    # Frozen Section 17 ordering, expressed only in evidence quantities.
    return (invalid, relative_gap(major), relative_gap(strong), -int(high_cert),
            work(high), relative_gap(moderate), relative_gap(tight),
            int(severe_numerical), gaps, works, times, models, simplicity)


def contraction_has_measurable_gain(k0: int) -> tuple[bool, list[dict[str, Any]]]:
    am = f"K{k0}-AM"
    amc = f"K{k0}-AMC"
    comparisons = []
    supported = False
    for instance in common.DEVELOPMENT:
        left = result("stage4_1200s", instance, am)
        right = result("stage4_1200s", instance, amc)
        contractions = int(right.get(
            "round47_single_child_contraction_count", 0))
        if contractions <= 0:
            continue
        left_work, right_work = work(left), work(right)
        left_models, right_models = model_count(left), model_count(right)
        left_gap, right_gap = relative_gap(left), relative_gap(right)
        certificate_not_weakened = (
            not bool(left.get("strict_certified_original_problem")) or
            bool(right.get("strict_certified_original_problem")))
        proof_not_weakened = right_gap <= left_gap + 1e-12
        measurable = certificate_not_weakened and proof_not_weakened and (
            right_work < left_work - max(1e-9, abs(left_work) * 1e-9) or
            right_models < left_models)
        supported = supported or measurable
        comparisons.append({
            "instance": instance, "contractions": contractions,
            "am_work": left_work, "amc_work": right_work,
            "am_models": left_models, "amc_models": right_models,
            "am_gap": left_gap, "amc_gap": right_gap,
            "certificate_not_weakened": certificate_not_weakened,
            "proof_not_weakened": proof_not_weakened,
            "measurable_contraction_attributed_gain": measurable,
        })
    return supported, comparisons


def invoke(executable: Path, stage: str, arm: str,
           instances: tuple[str, ...], cap: int) -> None:
    command = [sys.executable, str(common.ROOT / "scripts" /
               "round47_experiment.py"), "--stage", stage, "--arm", arm,
               "--process-cap", str(cap), "--executable", str(executable)]
    for instance in instances:
        command += ["--instance", instance]
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(command, cwd=common.ROOT, env=environment, check=True)


def assert_complete(stage: str, arms: list[str] | tuple[str, ...],
                    instances: tuple[str, ...]) -> None:
    missing = []
    for arm in arms:
        for instance in instances:
            marker = (common.RUNS / f"{stage}__{instance}__{arm}" /
                      "completion_marker.json")
            if not marker.is_file():
                missing.append(f"{stage}:{instance}:{arm}")
    if missing:
        raise RuntimeError(f"incomplete required rows: {missing}")


def stage3(executable: Path) -> None:
    for arm in common.ARMS:
        invoke(executable, "stage3_300s", arm, common.DEVELOPMENT, 300)
    assert_complete("stage3_300s", common.ARMS, common.DEVELOPMENT)
    common.write_json(common.OUT / "stage3_completion.json", {
        "schema": "round47-stage3-completion-v1", "complete": True,
        "arms": list(common.ARMS), "instances": list(common.DEVELOPMENT),
        "candidate_rows": 40, "process_cap_seconds": 300,
    })


def freeze_stage4() -> tuple[str, str]:
    assert_complete("stage4_1200s", common.ARMS, common.DEVELOPMENT)
    rankings = {}
    finalists = []
    for k0 in (4, 1):
        choices = [arm for arm in common.ARMS
                   if common.ARM_DEFINITIONS[arm]["K0"] == k0]
        ranked = sorted(choices, key=selection_score)
        contraction_supported, contraction_comparisons = \
            contraction_has_measurable_gain(k0)
        if not contraction_supported:
            ranked = [f"K{k0}-AM", f"K{k0}-AMC"]
        finalists.append(ranked[0])
        rankings[f"K{k0}"] = {
            "ordered_arms": ranked, "finalist": ranked[0],
            "contraction_attributed_gain": contraction_supported,
            "contraction_event_comparisons": contraction_comparisons,
            "scores": {arm: selection_score(arm) for arm in ranked},
        }
    common.write_json(common.OUT / "stage4_finalist_freeze.json", {
        "schema": "round47-stage4-finalist-freeze-v1",
        "frozen_before_confirmation_instances_opened": True,
        "stage4_candidate_rows": 40,
        "selection_order": "Section 17 frozen lexicographic evidence order",
        "tau": common.TAU, "rankings": rankings,
        "best_k4_arm": finalists[0], "best_k1_arm": finalists[1],
    })
    return finalists[0], finalists[1]


def stage4(executable: Path) -> None:
    assert_complete("stage3_300s", common.ARMS, common.DEVELOPMENT)
    for arm in common.ARMS:
        invoke(executable, "stage4_1200s", arm, common.DEVELOPMENT, 1200)
    freeze_stage4()


def stage5(executable: Path) -> None:
    frozen = common.load_json(common.OUT / "stage4_finalist_freeze.json")
    arms = [frozen["best_k4_arm"], frozen["best_k1_arm"]]
    if len(set(arms)) != 2:
        raise RuntimeError("Stage 5 must have distinct K4 and K1 finalists")
    for arm in arms:
        invoke(executable, "stage5_1800s", arm, common.STAGE5, 1800)
    assert_complete("stage5_1800s", arms, common.STAGE5)
    common.write_json(common.OUT / "stage5_completion.json", {
        "schema": "round47-stage5-completion-v1", "complete": True,
        "algorithm_arms": arms, "instances": list(common.STAGE5),
        "candidate_rows": 28, "maximum_cap_seconds": 1800,
        "historical_comparator_rows_rerun": 0,
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
