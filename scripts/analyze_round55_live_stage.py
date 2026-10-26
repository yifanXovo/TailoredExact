#!/usr/bin/env python3
"""Create paired gate evidence for a Round 55 F0/candidate live stage."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def truth(value: str) -> bool:
    return value.lower() == "true"


def severe(base: dict[str, str], arm: dict[str, str]) -> tuple[bool, str]:
    if truth(base["certificate"]) and not truth(arm["certificate"]):
        return True, "lost_baseline_certificate"
    if truth(base["certificate"]) and truth(arm["certificate"]):
        work_ratio = (float(arm["work"]) + 1e-12) / (float(base["work"]) + 1e-12)
        if work_ratio > 1.50 and float(arm["work"]) - float(base["work"]) > 50:
            return True, "exact_work_regression"
        time_ratio = (float(arm["time_seconds"]) + 1e-12) / (float(base["time_seconds"]) + 1e-12)
        if time_ratio > 1.50 and float(arm["time_seconds"]) - float(base["time_seconds"]) > 60:
            return True, "exact_time_regression"
    gi_ratio = (float(arm["normalized_gap_integral"]) + 1e-12) / (float(base["normalized_gap_integral"]) + 1e-12)
    if gi_ratio > 1.50 and float(arm["normalized_gap_integral"]) - float(base["normalized_gap_integral"]) >= 0.05:
        return True, "capped_gi_regression"
    gap_ratio = (float(arm["gap"]) + 1e-12) / (float(base["gap"]) + 1e-12)
    if gap_ratio > 1.50 and float(arm["gap"]) - float(base["gap"]) >= 0.05:
        return True, "capped_gap_regression"
    return False, "none"


def material(base: dict[str, str], arm: dict[str, str]) -> tuple[bool, str]:
    if not truth(base["certificate"]) and truth(arm["certificate"]):
        return True, "certificate_gain"
    if truth(base["certificate"]) and truth(arm["certificate"]):
        ratio = (float(arm["work"]) + 1e-12) / (float(base["work"]) + 1e-12)
        if ratio <= 0.90 and float(base["work"]) - float(arm["work"]) >= 10:
            return True, "exact_work_reduction"
    gi_ratio = (float(arm["normalized_gap_integral"]) + 1e-12) / (float(base["normalized_gap_integral"]) + 1e-12)
    if gi_ratio <= 0.90 and float(base["normalized_gap_integral"]) - float(arm["normalized_gap_integral"]) >= 0.05:
        return True, "capped_gi_reduction"
    gap_ratio = (float(arm["gap"]) + 1e-12) / (float(base["gap"]) + 1e-12)
    if gap_ratio <= 0.90 and float(base["gap"]) - float(arm["gap"]) >= 0.05:
        return True, "capped_gap_reduction"
    return False, "none"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--combined", type=Path)
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--select", default="")
    parser.add_argument("--reject", default="")
    args = parser.parse_args()
    data = rows(args.input)
    if args.baseline:
        data = [row for row in rows(args.baseline) if row["arm"] == "F0-CLEAN"] + data
    if args.combined:
        with args.combined.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0]))
            writer.writeheader(); writer.writerows(data)
    states = list(dict.fromkeys(row["state_id"] for row in data))
    arms = list(dict.fromkeys(row["arm"] for row in data))
    by_key = {(row["state_id"], row["arm"]): row for row in data}
    pairs = []
    summaries = {}
    for arm in arms:
        if arm == "F0-CLEAN":
            continue
        work_ratios = []
        gi_arm = gi_base = 0.0
        severe_states = []
        material_states = []
        gains = losses = 0
        for state in states:
            base = by_key[(state, "F0-CLEAN")]
            candidate = by_key[(state, arm)]
            is_severe, severe_reason = severe(base, candidate)
            is_material, material_reason = material(base, candidate)
            gain = int(truth(candidate["certificate"]) and not truth(base["certificate"]))
            loss = int(truth(base["certificate"]) and not truth(candidate["certificate"]))
            gains += gain; losses += loss
            if is_severe: severe_states.append(state)
            if is_material: material_states.append(state)
            work_ratio = (float(candidate["work"]) + 1.0) / (float(base["work"]) + 1.0)
            work_ratios.append(work_ratio)
            gi_base += float(base["normalized_gap_integral"])
            gi_arm += float(candidate["normalized_gap_integral"])
            pairs.append({
                "stage": args.stage, "state_id": state, "arm": arm,
                "baseline_certificate": base["certificate"],
                "candidate_certificate": candidate["certificate"],
                "certificate_gain": gain, "certificate_loss": loss,
                "baseline_work": base["work"], "candidate_work": candidate["work"],
                "shifted_work_ratio": work_ratio,
                "baseline_gi": base["normalized_gap_integral"],
                "candidate_gi": candidate["normalized_gap_integral"],
                "gi_ratio": (float(candidate["normalized_gap_integral"]) + 1e-12) / (float(base["normalized_gap_integral"]) + 1e-12),
                "baseline_gap": base["gap"], "candidate_gap": candidate["gap"],
                "severe_regression": is_severe, "severe_reason": severe_reason,
                "material_improvement": is_material, "material_reason": material_reason,
            })
        summaries[arm] = {
            "certificate_gain_count": gains,
            "certificate_loss_count": losses,
            "severe_regression_count": len(severe_states),
            "severe_states": severe_states,
            "material_improvement_states": material_states,
            "shifted_work_geometric_mean_ratio": math.exp(sum(math.log(v) for v in work_ratios) / len(work_ratios)),
            "aggregate_gi_ratio": gi_arm / max(1e-12, gi_base),
        }
    with args.pairs.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pairs[0]))
        writer.writeheader(); writer.writerows(pairs)
    selected = [value for value in args.select.split(",") if value]
    rejected = [value for value in args.reject.split(",") if value]
    decision = {
        "schema": "round55-live-stage-decision-v1", "stage": args.stage,
        "row_count": len(data), "pair_count": len(pairs),
        "all_engineering_valid": all(truth(row["engineering_gate"]) for row in data),
        "false_certificate_count": sum(truth(row["false_certificate"]) for row in data),
        "summaries": summaries, "selected_for_next_stage": selected,
        "rejected": rejected,
    }
    args.decision.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
