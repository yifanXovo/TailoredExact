#!/usr/bin/env python3
"""Pair and gate contemporaneous Round 53 fixed-interval evidence."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"


def boolean(value: object) -> bool:
    return value is True or str(value).lower() in {"1", "true"}


def ratio(candidate: float, baseline: float) -> float:
    if baseline == 0.0:
        return 1.0 if candidate == 0.0 else math.inf
    return candidate / baseline


def geometric_mean(values: list[float]) -> float:
    if not values:
        return 1.0
    return math.exp(sum(math.log(max(1e-300, value)) for value in values) /
                    len(values))


def read_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def severe(baseline: dict[str, str], candidate: dict[str, str]) -> tuple[bool, str]:
    b_cert, c_cert = boolean(baseline["certificate"]), boolean(candidate["certificate"])
    b_work, c_work = float(baseline["work"]), float(candidate["work"])
    b_time, c_time = (float(baseline["process_time_seconds"]),
                      float(candidate["process_time_seconds"]))
    if b_cert and c_cert:
        if ratio(c_work, b_work) > 1.5 and c_work - b_work > 50:
            return True, "exact_work"
        if ratio(c_time, b_time) > 1.5 and c_time - b_time > 60:
            return True, "exact_time"
        return False, "none"
    if b_cert and not c_cert:
        return True, "lost_baseline_certificate"
    b_gi, c_gi = (float(baseline["gi_common_horizon"]),
                  float(candidate["gi_common_horizon"]))
    if ratio(c_gi, b_gi) > 1.5 and c_gi - b_gi >= .05:
        return True, "capped_gi"
    b_gap, c_gap = float(baseline["gap"]), float(candidate["gap"])
    if ratio(c_gap, b_gap) > 1.5 and c_gap - b_gap >= .05:
        return True, "capped_gap"
    return False, "none"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("development", "confirmation", "key-long"),
                        required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--physical-output", type=Path, required=True)
    parser.add_argument("--pair-output", type=Path, required=True)
    parser.add_argument("--decision-output", type=Path, required=True)
    args = parser.parse_args()
    baseline_rows, candidate_rows = read_rows(args.baseline), read_rows(args.candidate)
    baseline = {row["state_id"]: row for row in baseline_rows}
    candidate = {row["state_id"]: row for row in candidate_rows}
    if set(baseline) != set(candidate) or len(baseline) != len(baseline_rows):
        raise RuntimeError("fixed-interval pairing mismatch")
    physical = baseline_rows + candidate_rows
    write_csv(args.physical_output.resolve(), list(physical[0]), physical)
    pairs: list[dict[str, object]] = []
    exact_ratios, shifted_work_ratios = [], []
    capped_b_gi = capped_c_gi = all_b_gi = all_c_gi = 0.0
    gains = losses = correctness = false_certificates = severe_count = 0
    improvement_roles: set[str] = set()
    for state_id in baseline:
        b, c = baseline[state_id], candidate[state_id]
        b_cert, c_cert = boolean(b["certificate"]), boolean(c["certificate"])
        gains += int(c_cert and not b_cert)
        losses += int(b_cert and not c_cert)
        correctness += int(not boolean(b["engineering_gate"]) or
                           not boolean(c["engineering_gate"]))
        false_certificates += int(boolean(b["false_certificate"])) + int(
            boolean(c["false_certificate"]))
        b_work, c_work = float(b["work"]), float(c["work"])
        b_gi, c_gi = float(b["gi_common_horizon"]), float(c["gi_common_horizon"])
        b_gap, c_gap = float(b["gap"]), float(c["gap"])
        changed = int(b["subset_duration_rows"]) > 0
        exact_common = b_cert and c_cert and changed
        if exact_common:
            exact_ratios.append(ratio(c_work, b_work))
        shifted_work_ratios.append((c_work + 1.0) / (b_work + 1.0))
        all_b_gi += b_gi
        all_c_gi += c_gi
        if not (b_cert and c_cert):
            capped_b_gi += b_gi
            capped_c_gi += c_gi
        is_severe, severe_reason = severe(b, c)
        severe_count += int(is_severe)
        materially_better = ((c_cert and not b_cert) or
            (exact_common and ratio(c_work, b_work) <= .95) or
            (not b_cert and not c_cert and c_gi <= .95 * b_gi))
        if materially_better:
            improvement_roles.add(b["role"])
        pairs.append({
            "state_id": state_id, "role": b["role"],
            "state_kind": b["state_kind"], "changed_model": changed,
            "baseline_certificate": b_cert, "candidate_certificate": c_cert,
            "certificate_gain": c_cert and not b_cert,
            "certificate_loss": b_cert and not c_cert,
            "baseline_work": b_work, "candidate_work": c_work,
            "work_ratio_candidate_over_baseline": ratio(c_work, b_work),
            "baseline_process_time": b["process_time_seconds"],
            "candidate_process_time": c["process_time_seconds"],
            "baseline_gap": b_gap, "candidate_gap": c_gap,
            "gap_ratio_candidate_over_baseline": ratio(c_gap, b_gap),
            "baseline_gi": b_gi, "candidate_gi": c_gi,
            "gi_ratio_candidate_over_baseline": ratio(c_gi, b_gi),
            "baseline_root_work": b["root_work"],
            "candidate_root_work": c["root_work"],
            "baseline_nodes": b["nodes"], "candidate_nodes": c["nodes"],
            "baseline_iterations_per_node": b["average_iterations_per_node"],
            "candidate_iterations_per_node": c["average_iterations_per_node"],
            "severe_regression": is_severe,
            "severe_regression_reason": severe_reason,
            "material_improvement": materially_better})
    write_csv(args.pair_output.resolve(), list(pairs[0]), pairs)
    exact_gm = geometric_mean(exact_ratios)
    shifted_work_gm = geometric_mean(shifted_work_ratios)
    capped_gi_ratio = ratio(capped_c_gi, capped_b_gi)
    all_gi_ratio = ratio(all_c_gi, all_b_gi)
    performance = (exact_gm <= .95 or
                   (gains >= 1 and shifted_work_gm <= 1.0 and
                    all_gi_ratio <= 1.0))
    vgt12_pass = True
    if args.stage == "development":
        vgt = read_rows(OUT / "f0_v_gt_12_equivalence_audit.csv")
        vgt12_pass = bool(vgt) and all(boolean(row["pass"]) for row in vgt)
    mandatory = (correctness == 0 and false_certificates == 0 and losses == 0
                 and severe_count == 0 and capped_gi_ratio <= 1.0 + 1e-12)
    if args.stage == "development":
        mandatory = mandatory and len(improvement_roles) >= 2 and vgt12_pass
    if args.stage == "key-long":
        performance = True
    passed = mandatory and performance
    decision = {
        "schema": "round53-fixed-interval-stage-decision-v1",
        "stage": args.stage, "row_count_per_policy": len(baseline),
        "physical_row_count": len(physical), "paired_row_count": len(pairs),
        "correctness_failures": correctness,
        "false_certificates": false_certificates,
        "baseline_certificates": sum(boolean(row["certificate"])
                                     for row in baseline_rows),
        "candidate_certificates": sum(boolean(row["certificate"])
                                      for row in candidate_rows),
        "certificate_gains": gains, "certificate_losses": losses,
        "severe_regressions": severe_count,
        "common_exact_changed_state_count": len(exact_ratios),
        "work_geometric_mean_ratio_candidate_over_baseline": exact_gm,
        "shifted_all_row_work_geometric_mean_ratio": shifted_work_gm,
        "capped_state_aggregate_gi_ratio": capped_gi_ratio,
        "all_state_aggregate_gi_ratio": all_gi_ratio,
        "material_improvement_role_count": len(improvement_roles),
        "material_improvement_roles": sorted(improvement_roles),
        "v_gt_12_equivalence_pass": vgt12_pass,
        "mandatory_gate_pass": mandatory,
        "performance_gate_pass": performance,
        "stage_pass": passed}
    write_json(args.decision_output.resolve(), decision)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())
