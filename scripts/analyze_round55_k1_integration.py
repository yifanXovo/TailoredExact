#!/usr/bin/env python3
"""Compact and gate completed Round 55 K1 integration rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from run_round55_k1_integration import EVIDENCE, FREEZE, RUNS, ARMS, panel_rows


TOL = 1e-7


def truth(value: object) -> bool:
    return value is True or str(value).lower() in {"1", "true"}


def number(value: object, default: float = 0.0) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str] | None = None) -> None:
    if not rows and not fields:
        raise RuntimeError(f"no rows for {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]),
                                extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def gap(lower: float, upper: float) -> float:
    return max(0.0, (upper - lower) / max(1e-12, abs(upper)))


def trace(run_dir: Path) -> list[tuple[float, float]]:
    points = []
    for row in csv_rows(run_dir / "external" / "global_bound_trace.csv"):
        lower = number(row.get("valid_global_lower_bound"), math.nan)
        upper = number(row.get("verified_global_upper_bound"), math.inf)
        if math.isfinite(lower) and math.isfinite(upper):
            points.append((number(row.get("process_elapsed_seconds")),
                           gap(lower, upper)))
    points.sort()
    return points


def normalized_gi(points: list[tuple[float, float]], horizon: float,
                  exact: bool, process_seconds: float) -> float:
    previous_time, previous_gap, area = 0.0, 1.0, 0.0
    for event_time, event_gap in points:
        event_time = min(horizon, max(previous_time, event_time))
        area += (event_time - previous_time) * previous_gap
        previous_time, previous_gap = event_time, event_gap
        if event_time >= horizon:
            break
    if exact and process_seconds <= horizon:
        end = max(previous_time, process_seconds)
        area += (end - previous_time) * previous_gap
        previous_time, previous_gap = end, 0.0
    if previous_time < horizon:
        area += (horizon - previous_time) * previous_gap
    return area / horizon


def gm(values: list[float]) -> float:
    return (math.exp(sum(math.log(max(1e-300, value)) for value in values) /
                     len(values)) if values else 1.0)


def decision_rows(run_dir: Path) -> list[dict[str, str]]:
    path = run_dir / "external" / "adaptive_mass_decision_ledger.csv"
    rows = csv_rows(path)
    keep = ("decision_sequence", "interval_id", "parent_id", "depth",
            "gamma_L", "gamma_U", "selected_action", "native_target",
            "deterministic_reason", "coverage_update")
    return [{key: row.get(key, "") for key in keep} for row in rows]


def load_row(row: dict[str, Any], arm: str, cap: int) -> dict[str, object]:
    run_id = f"{row['instance_id']}__{arm}__{cap}s"
    run_dir = RUNS / run_id
    marker = read_json(run_dir / "completion_marker.json")
    command = read_json(run_dir / "command.json")
    result = read_json(run_dir / "result.json")
    if not (truth(marker.get("complete")) and truth(marker.get("cap_respected")) and
            int(marker.get("cap_seconds", -1)) == cap and
            marker.get("preset") == ARMS[arm]["preset"] and
            marker.get("inner_policy") == ARMS[arm]["policy"]):
        raise RuntimeError(f"unsealed K1 row: {run_id}")
    exact = truth(result.get("strict_certified_original_problem"))
    seconds = number(result.get("final_process_wall_time_seconds"))
    lower = number(result.get("lower_bound"))
    upper = number(result.get("upper_bound"))
    verification = result.get("verification", {})
    correctness = (
        truth(result.get("option_audit_consistent")) and
        isinstance(verification, dict) and truth(verification.get("feasible")) and
        lower <= upper + TOL * max(1.0, abs(upper)) and
        result.get("algorithm_preset") == ARMS[arm]["preset"] and
        result.get("external_gini_tree_interval_mip_policy") == ARMS[arm]["policy"])
    attempted = truth(result.get("external_gini_tree_attempted"))
    if attempted:
        correctness = correctness and all(truth(result.get(key)) for key in (
            "external_gini_tree_root_coverage_valid",
            "external_gini_tree_parent_child_coverage_valid",
            "external_gini_tree_all_leaf_bounds_valid",
            "external_gini_tree_global_bound_monotone",
            "external_gini_tree_lifecycle_complete",
            "external_gini_tree_backend_parameter_roundtrip_valid"))
    else:
        correctness = correctness and not exact
    if exact:
        correctness = correctness and attempted and truth(
            result.get("external_gini_tree_strict_certified"))
    points = trace(run_dir)
    checkpoints = {
        f"gi_{checkpoint}s": normalized_gi(points, checkpoint, exact, seconds)
        for checkpoint in (300, 1200, 1800, 3600) if checkpoint <= cap
    }
    actions = decision_rows(run_dir)
    action_hash = hashlib.sha256(json.dumps(
        actions, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    native_targets = csv_rows(run_dir / "external" / "native_target_ledger.csv")
    leaves = csv_rows(run_dir / "external" / "paper_leaf_ledger.csv")
    exact_closures = sum("exact" in str(leaf.get("closure_source", "")).lower()
                         for leaf in leaves)
    result_row: dict[str, object] = {
        "instance_id": row["instance_id"], "role": row["role"],
        "V": row["V"], "M": row["M"], "Q": row["Q"], "T": row["T"],
        "arm": arm, "preset": ARMS[arm]["preset"],
        "inner_policy": ARMS[arm]["policy"], "cap_seconds": cap,
        "completion_status": result.get("status"),
        "certificate": exact, "correctness_gate": correctness,
        "false_certificate": exact and not correctness,
        "lower_bound": lower, "verified_upper_bound": upper,
        "gap": gap(lower, upper), "work": number(result.get("external_gini_tree_work")),
        "process_time_seconds": seconds,
        "initial_root_range": result.get("external_gini_tree_active_initial_intervals", ""),
        "split_count": int(number(result.get("external_gini_tree_split_count"))),
        "interval_count": int(number(result.get("external_gini_tree_final_leaf_count"))),
        "adaptive_score_count": len(actions), "adaptive_action_sha256": action_hash,
        "native_target_count": len(native_targets),
        "exact_parent_closure_count": exact_closures,
        "fixed_interval_model_count": int(number(result.get("external_gini_tree_model_count"))),
        "model_build_seconds": number(result.get("external_gini_tree_model_build_seconds")),
        "lp_work": number(result.get("external_gini_tree_lp_work")),
        "terminal_mip_work": number(result.get("external_gini_tree_terminal_mip_work")),
        "peak_memory_gb": number(result.get("external_gini_tree_peak_memory_gb")),
        "executable_sha256": marker["executable_sha256"],
        "artifact_dir": run_dir.relative_to(EVIDENCE.parents[1]).as_posix(),
    }
    result_row.update(checkpoints)
    return result_row


def severe(baseline: dict[str, object], candidate: dict[str, object], cap: int) -> bool:
    if truth(baseline["certificate"]) and truth(candidate["certificate"]):
        bw, cw = number(baseline["work"]), number(candidate["work"])
        bt, ct = number(baseline["process_time_seconds"]), number(candidate["process_time_seconds"])
        return ((cw / max(1e-12, bw) > 1.5 and cw - bw > 50) or
                (ct / max(1e-12, bt) > 1.5 and ct - bt > 60))
    if truth(baseline["certificate"]) and not truth(candidate["certificate"]):
        return True
    gi_key = f"gi_{cap}s"
    bg, cg = number(baseline[gi_key]), number(candidate[gi_key])
    gb, gc = number(baseline["gap"]), number(candidate["gap"])
    return ((cg / max(1e-12, bg) > 1.5 and cg - bg >= 0.05) or
            (gc / max(1e-12, gb) > 1.5 and gc - gb >= 0.05))


def split_differences(rows: list[dict[str, Any]], cap: int) -> list[dict[str, object]]:
    output = []
    for row in rows:
        arm_rows = {}
        for arm in ARMS:
            run_dir = RUNS / f"{row['instance_id']}__{arm}__{cap}s"
            arm_rows[arm] = decision_rows(run_dir)
        stable = arm_rows["K1-AM-SF"]
        candidate = arm_rows["K1-AM-SF-CANDIDATE"]
        maximum = max(len(stable), len(candidate))
        changed = 0
        for index in range(maximum):
            left = stable[index] if index < len(stable) else {}
            right = candidate[index] if index < len(candidate) else {}
            if left != right:
                changed += 1
                output.append({
                    "instance_id": row["instance_id"], "role": row["role"],
                    "cap_seconds": cap, "decision_index": index,
                    "stable_interval_id": left.get("interval_id", ""),
                    "candidate_interval_id": right.get("interval_id", ""),
                    "stable_action": left.get("selected_action", ""),
                    "candidate_action": right.get("selected_action", ""),
                    "stable_gamma_L": left.get("gamma_L", ""),
                    "stable_gamma_U": left.get("gamma_U", ""),
                    "candidate_gamma_L": right.get("gamma_L", ""),
                    "candidate_gamma_U": right.get("gamma_U", ""),
                    "stable_reason": left.get("deterministic_reason", ""),
                    "candidate_reason": right.get("deterministic_reason", ""),
                    "classification": "materially_changed_action" if
                        left.get("selected_action") != right.get("selected_action")
                        else "bound_or_telemetry_change",
                })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cap", type=int, choices=(1800, 3600), required=True)
    parser.add_argument("--instances")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    parser.add_argument("--split-diff", type=Path)
    args = parser.parse_args()
    selected = None if not args.instances else {
        value.strip() for value in args.instances.split(",") if value.strip()}
    panel = panel_rows(selected)
    physical = [load_row(row, arm, args.cap) for row in panel for arm in ARMS]
    write_csv(args.output, physical)
    if args.split_diff:
        diffs = split_differences(panel, args.cap)
        fields = ["instance_id", "role", "cap_seconds", "decision_index",
                  "stable_interval_id", "candidate_interval_id", "stable_action",
                  "candidate_action", "stable_gamma_L", "stable_gamma_U",
                  "candidate_gamma_L", "candidate_gamma_U", "stable_reason",
                  "candidate_reason", "classification"]
        write_csv(args.split_diff, diffs, fields)
    by = {(str(row["instance_id"]), str(row["arm"])): row for row in physical}
    pairs = [(by[(row["instance_id"], "K1-AM-SF")],
              by[(row["instance_id"], "K1-AM-SF-CANDIDATE")]) for row in panel]
    gains = sum(truth(c["certificate"]) and not truth(b["certificate"]) for b, c in pairs)
    losses = sum(truth(b["certificate"]) and not truth(c["certificate"]) for b, c in pairs)
    severe_states = [str(b["instance_id"]) for b, c in pairs if severe(b, c, args.cap)]
    work_ratio = gm([(number(c["work"]) + 1.0) / (number(b["work"]) + 1.0)
                     for b, c in pairs])
    gi_key = f"gi_{args.cap}s"
    gi_ratio = (sum(number(c[gi_key]) for _, c in pairs) /
                max(1e-12, sum(number(b[gi_key]) for b, _ in pairs)))
    material_states = []
    for b, c in pairs:
        work_material = ((number(c["work"]) + 1) / (number(b["work"]) + 1) <= 0.8 and
                         number(b["work"]) - number(c["work"]) >= 1)
        gi_material = (number(c[gi_key]) <= 0.8 * number(b[gi_key]) and
                       number(b[gi_key]) - number(c[gi_key]) >= 0.02)
        if (truth(c["certificate"]) and not truth(b["certificate"])) or work_material or gi_material:
            material_states.append(str(b["instance_id"]))
    major = [(b, c) for b, c in pairs if b["role"] == "major witness"]
    major_preserved = bool(major) and all(
        not severe(b, c, args.cap) and
        (not truth(b["certificate"]) or truth(c["certificate"])) for b, c in major)
    benefit_beyond_witness = any(b["instance_id"] != panel[0]["instance_id"]
                                 for b, _ in pairs if b["instance_id"] in material_states)
    scale_pairs = [(b, c) for b, c in pairs if int(b["V"]) >= 20]
    scale_nonworse = (not any(severe(b, c, args.cap) for b, c in scale_pairs) and
                      sum(number(c[gi_key]) for _, c in scale_pairs) <=
                      1.05 * max(1e-12, sum(number(b[gi_key]) for b, _ in scale_pairs)))
    false = sum(truth(row["false_certificate"]) for row in physical)
    invalid = sum(not truth(row["correctness_gate"]) for row in physical)
    gate = (false == 0 and invalid == 0 and losses == 0 and not severe_states and
            work_ratio <= 1.0 and gi_ratio <= 1.0 and bool(material_states) and
            major_preserved and benefit_beyond_witness and scale_nonworse)
    unresolved = [str(b["instance_id"]) for b, c in pairs
                  if not truth(b["certificate"]) or not truth(c["certificate"])]
    decision = {
        "schema": "round55-k1-integration-stage-decision-v1",
        "cap_seconds": args.cap, "physical_rows": len(physical),
        "pair_count": len(pairs), "correctness_failures": invalid,
        "false_certificates": false, "certificate_counts": {
            arm: sum(truth(row["certificate"]) and row["arm"] == arm for row in physical)
            for arm in ARMS},
        "certificate_gains": gains, "certificate_losses": losses,
        "severe_regression_count": len(severe_states), "severe_states": severe_states,
        "shifted_work_geometric_mean_ratio": work_ratio,
        "aggregate_gi_ratio": gi_ratio, "material_states": material_states,
        "major_repair_preserved": major_preserved,
        "benefit_beyond_major_witness": benefit_beyond_witness,
        "V20_V50_not_materially_worsened": scale_nonworse,
        "unresolved_instances": unresolved,
        "conditional_3600_required": args.cap == 1800 and bool(unresolved),
        "gate_pass_at_this_cap": gate,
    }
    write_json(args.decision, decision)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if false == 0 and invalid == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
