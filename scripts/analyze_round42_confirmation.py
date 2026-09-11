#!/usr/bin/env python3
"""Evaluate a frozen Round 42 validation or holdout candidate."""

from __future__ import annotations

import argparse
import math
from typing import Any

import analyze_round42_development as dev
import round42_common as common


def load_candidate(group: str, candidate: str,
                   instance_id: str) -> dict[str, Any] | None:
    tag = f"{group}_candidate_{candidate.replace('-', '_')}"
    if candidate == "sibling-core":
        return dev.c6_row(instance_id, candidate, tag)
    if candidate == "sibling-core-factored":
        return dev.c6_row(instance_id, candidate, tag)
    report = candidate.upper()
    if candidate in {"paired-k4", "paired-k4-factored"}:
        return dev.composite_row(instance_id, candidate, tag, report)
    return dev.static_row(instance_id, candidate, tag, report)


def gmean(values: list[float]) -> float:
    return math.exp(sum(math.log(value) for value in values) / len(values))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=("validation", "holdout"),
                        required=True)
    args = parser.parse_args()
    freeze = common.load_json(
        common.OUT / f"{args.group}_candidate_freeze.json")
    candidate_name = freeze["candidate"]
    manifest_name = "validation_manifest.csv" if args.group == "validation" \
        else "final_holdout_manifest.csv"
    manifests = sorted(common.csv_rows(common.OUT / manifest_name),
                       key=lambda row: int(row["serial_order"]))
    comparisons: list[dict[str, Any]] = []
    for item in manifests:
        instance = item["instance_id"]
        baseline = dev.c6_row(
            instance, "c6-reference", f"{args.group}_reference")
        candidate = load_candidate(args.group, candidate_name, instance)
        if not baseline or not candidate:
            raise RuntimeError(f"missing {args.group} pair for {instance}")
        work_ratio = dev.ratio(dev.number(candidate["solver_work"]),
                               dev.number(baseline["solver_work"]))
        time_ratio = dev.ratio(
            dev.number(candidate["exact_phase_seconds"]) + 1.0,
            dev.number(baseline["exact_phase_seconds"]) + 1.0)
        comparisons.append({
            "experiment_group": args.group,
            "serial_order": item["serial_order"],
            "instance_id": instance,
            "candidate": candidate_name,
            "baseline": "C6-HGA-FULL-K4",
            "candidate_work": candidate["solver_work"],
            "baseline_work": baseline["solver_work"],
            "work_ratio": work_ratio,
            "candidate_exact_phase_seconds": candidate[
                "exact_phase_seconds"],
            "baseline_exact_phase_seconds": baseline[
                "exact_phase_seconds"],
            "shifted_time_ratio": time_ratio,
            "materiality": "win" if work_ratio <= 0.95 else (
                "loss" if work_ratio >= 1.05 else "tie"),
            "catastrophic_both_above_1_25": (
                work_ratio > 1.25 and time_ratio > 1.25),
            "baseline_strict_certificate": baseline["strict_certificate"],
            "candidate_strict_certificate": candidate["strict_certificate"],
            "certificate_regression": (
                dev.truth(baseline["strict_certificate"]) and
                not dev.truth(candidate["strict_certificate"])),
            "false_certificate": candidate["false_certificate"],
            "candidate_verifier_passed": candidate[
                "original_problem_verifier_passed"],
        })
    common.write_csv(common.OUT / f"{args.group}_comparison.csv", comparisons)
    work_gmean = gmean([dev.number(row["work_ratio"])
                        for row in comparisons])
    time_gmean = gmean([dev.number(row["shifted_time_ratio"])
                        for row in comparisons])
    wins = sum(row["materiality"] == "win" for row in comparisons)
    losses = sum(row["materiality"] == "loss" for row in comparisons)
    work_limit = 0.95 if args.group == "validation" else 1.00
    time_limit = 0.98 if args.group == "validation" else 1.00
    passed = (
        all(not dev.truth(row["false_certificate"]) for row in comparisons) and
        all(not dev.truth(row["certificate_regression"])
            for row in comparisons) and
        all(not dev.truth(row["catastrophic_both_above_1_25"])
            for row in comparisons) and
        work_gmean <= work_limit and time_gmean <= time_limit and
        wins >= losses)
    decision = {
        "schema": f"round42-{args.group}-decision-v1",
        "round_id": 42,
        "group": args.group,
        "candidate": candidate_name,
        "row_count": len(comparisons),
        "geometric_mean_work_ratio": work_gmean,
        "geometric_mean_shifted_time_ratio": time_gmean,
        "material_wins": wins,
        "material_losses": losses,
        "ties": len(comparisons) - wins - losses,
        "false_certificates": sum(dev.truth(row["false_certificate"])
                                  for row in comparisons),
        "certificate_regressions": sum(dev.truth(
            row["certificate_regression"]) for row in comparisons),
        "catastrophic_regressions": sum(dev.truth(
            row["catastrophic_both_above_1_25"]) for row in comparisons),
        "gate_passed": passed,
    }
    common.write_json(common.OUT / f"{args.group}_decision.json", decision)
    print(decision)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
