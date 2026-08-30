#!/usr/bin/env python3
"""Combine 1,800/3,600-second K1 rows and apply the frozen integration gate."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from analyze_round55_k1_integration import gm, number, severe, truth


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore",
                                lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    temporary.replace(path)


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows-1800", type=Path, required=True)
    parser.add_argument("--rows-3600", type=Path, required=True)
    parser.add_argument("--diff-1800", type=Path, required=True)
    parser.add_argument("--diff-3600", type=Path, required=True)
    parser.add_argument("--split-output", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    args = parser.parse_args()
    rows1800 = csv_rows(args.rows_1800)
    rows3600 = csv_rows(args.rows_3600)
    extended = {row["instance_id"] for row in rows3600}
    effective = [row for row in rows1800 if row["instance_id"] not in extended] + rows3600
    by = {(row["instance_id"], row["arm"]): row for row in effective}
    instances = list(dict.fromkeys(row["instance_id"] for row in effective))
    pairs = [(by[(instance, "K1-AM-SF")],
              by[(instance, "K1-AM-SF-CANDIDATE")]) for instance in instances]
    false = sum(truth(row["false_certificate"]) for row in rows1800 + rows3600)
    invalid = sum(not truth(row["correctness_gate"]) for row in rows1800 + rows3600)
    gains = sum(truth(c["certificate"]) and not truth(b["certificate"]) for b, c in pairs)
    losses = sum(truth(b["certificate"]) and not truth(c["certificate"]) for b, c in pairs)
    severe_states = []
    work_ratios, base_gi, candidate_gi, material = [], 0.0, 0.0, []
    for baseline, candidate in pairs:
        cap = int(candidate["cap_seconds"])
        gi_key = f"gi_{cap}s"
        if severe(baseline, candidate, cap):
            severe_states.append(candidate["instance_id"])
        ratio = (number(candidate["work"]) + 1) / (number(baseline["work"]) + 1)
        work_ratios.append(ratio)
        base_gi += number(baseline[gi_key]); candidate_gi += number(candidate[gi_key])
        if ((truth(candidate["certificate"]) and not truth(baseline["certificate"])) or
                (ratio <= 0.8 and number(baseline["work"]) - number(candidate["work"]) >= 1) or
                (number(candidate[gi_key]) <= 0.8 * number(baseline[gi_key]) and
                 number(baseline[gi_key]) - number(candidate[gi_key]) >= 0.02)):
            material.append(candidate["instance_id"])
    work_ratio = gm(work_ratios)
    gi_ratio = candidate_gi / max(1e-12, base_gi)
    major = next((pair for pair in pairs if pair[0]["role"] == "major witness"), None)
    major_preserved = bool(major) and not severe(major[0], major[1],
                                                 int(major[1]["cap_seconds"])) and (
        not truth(major[0]["certificate"]) or truth(major[1]["certificate"]))
    benefit_beyond_major = any(instance != (major[0]["instance_id"] if major else "")
                               for instance in material)
    scale_pairs = [(b, c) for b, c in pairs if int(b["V"]) >= 20]
    scale_gi_base = sum(number(b[f"gi_{b['cap_seconds']}s"]) for b, _ in scale_pairs)
    scale_gi_candidate = sum(number(c[f"gi_{c['cap_seconds']}s"]) for _, c in scale_pairs)
    scale_nonworse = (not any(severe(b, c, int(c["cap_seconds"])) for b, c in scale_pairs) and
                      scale_gi_candidate <= 1.05 * max(1e-12, scale_gi_base))
    diffs = csv_rows(args.diff_1800) + csv_rows(args.diff_3600)
    deduplicated = []
    seen = set()
    for row in diffs:
        key = (row["instance_id"], row["cap_seconds"], row["decision_index"],
               row["stable_interval_id"], row["candidate_interval_id"])
        if key not in seen:
            seen.add(key); deduplicated.append(row)
    diff_fields = ["instance_id", "role", "cap_seconds", "decision_index",
                   "stable_interval_id", "candidate_interval_id", "stable_action",
                   "candidate_action", "stable_gamma_L", "stable_gamma_U",
                   "candidate_gamma_L", "candidate_gamma_U", "stable_reason",
                   "candidate_reason", "classification"]
    write_csv(args.split_output, deduplicated, diff_fields)
    material_action_instances = sorted({row["instance_id"] for row in deduplicated
                                        if row["classification"] == "materially_changed_action"})
    gate = (false == 0 and invalid == 0 and losses == 0 and not severe_states and
            work_ratio <= 1.0 and gi_ratio <= 1.0 and bool(material) and
            major_preserved and benefit_beyond_major and scale_nonworse)
    decision = {
        "schema": "round55-k1-integration-final-decision-v1",
        "entered_physical_rows": len(rows1800) + len(rows3600),
        "effective_pair_count": len(pairs),
        "initial_1800_rows": len(rows1800), "conditional_3600_rows": len(rows3600),
        "extended_instances": sorted(extended),
        "correctness_failures": invalid, "false_certificates": false,
        "effective_certificate_counts": {
            arm: sum(truth(row["certificate"]) and row["arm"] == arm for row in effective)
            for arm in ("K1-AM-SF", "K1-AM-SF-CANDIDATE")},
        "certificate_gains": gains, "certificate_losses": losses,
        "severe_regression_count": len(severe_states), "severe_states": severe_states,
        "shifted_work_geometric_mean_ratio": work_ratio,
        "aggregate_gi_ratio": gi_ratio, "material_improvement_instances": material,
        "major_repair_preserved": major_preserved,
        "benefit_beyond_major_witness": benefit_beyond_major,
        "V20_V50_not_materially_worsened": scale_nonworse,
        "changed_action_instance_count": len(material_action_instances),
        "changed_action_instances": material_action_instances,
        "gate_pass": gate,
        "split_diagnosis_entry_condition": (not gate and bool(material_action_instances)),
    }
    write_json(args.decision, decision)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if false == 0 and invalid == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
