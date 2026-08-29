#!/usr/bin/env python3
"""Summarize and gate Round 53 K1 integration and sealed-panel runs."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from run_round53_k1_panel import OUT, panel_rows


RUNS = OUT / "local_raw" / "k1_panel_runs"
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
    if not path.is_file():
        return []
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def relative_gap(lower: float, upper: float) -> float:
    if not math.isfinite(lower) or not math.isfinite(upper):
        return 1.0
    return max(0.0, (upper - lower) / max(1e-12, abs(upper)))


def trajectory(run_dir: Path, method: str) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    if method == "P-GRB":
        for row in csv_rows(run_dir / "progress.csv"):
            if not truth(row.get("best_bound_available")):
                continue
            lower = number(row.get("best_bound"), math.nan)
            upper = (number(row.get("incumbent"), math.inf)
                     if truth(row.get("incumbent_available")) else math.inf)
            points.append((number(row.get("elapsed_runtime_seconds")),
                           relative_gap(lower, upper)))
    else:
        for row in csv_rows(run_dir / "external" / "global_bound_trace.csv"):
            lower = number(row.get("valid_global_lower_bound"), math.nan)
            upper = number(row.get("verified_global_upper_bound"), math.inf)
            points.append((number(row.get("process_elapsed_seconds")),
                           relative_gap(lower, upper)))
    points.sort()
    return points


def gi(points: list[tuple[float, float]], horizon: float,
       exact: bool, process_seconds: float) -> float:
    previous_time, previous_gap, area = 0.0, 1.0, 0.0
    for current_time, current_gap in points:
        current_time = min(horizon, max(previous_time, current_time))
        area += (current_time - previous_time) * previous_gap
        previous_time, previous_gap = current_time, current_gap
        if current_time >= horizon:
            break
    if exact and process_seconds <= horizon:
        end = max(previous_time, process_seconds)
        area += (end - previous_time) * previous_gap
        previous_time, previous_gap = end, 0.0
    if previous_time < horizon:
        area += (horizon - previous_time) * previous_gap
    return area / horizon


def gm(values: list[float]) -> float:
    return math.exp(sum(math.log(max(1e-300, value)) for value in values) /
                    len(values)) if values else 1.0


def load_row(panel: str, row: dict[str, Any], method: str,
             cap: float) -> dict[str, object]:
    run_id = f"{panel}__{row['instance_id']}__{method}__{int(cap)}s"
    run_dir = RUNS / run_id
    marker = read_json(run_dir / "completion_marker.json")
    command = read_json(run_dir / "command.json")
    result = read_json(run_dir / "result.json")
    if not (marker.get("complete") is True and
            marker.get("cap_respected") is True and
            float(marker.get("process_cap_seconds", -1)) == cap):
        raise RuntimeError(f"unsealed K1 row: {run_id}")
    exact = truth(result.get("strict_certified_original_problem"))
    process_seconds = number(result.get("final_process_wall_time_seconds"))
    lower, upper = number(result.get("lower_bound")), number(result.get("upper_bound"))
    points = trajectory(run_dir, method)
    gap = relative_gap(lower, upper)
    normalized_gi = gi(points, cap, exact, process_seconds)
    verification = result.get("verification", {})
    correctness = (truth(result.get("option_audit_consistent")) and
                   isinstance(verification, dict) and
                   truth(verification.get("feasible")) and
                   lower <= upper + TOL * max(1.0, abs(upper)))
    if method == "P-GRB":
        correctness = correctness and truth(result.get("gurobi_lifecycle_valid"))
        work = number(result.get("gurobi_work"))
        nodes = number(result.get("gurobi_node_count"))
        simplex = number(result.get("gurobi_iter_count"))
        split_count = 0
        interval_count = 0
        fixed_interval_model_count = 1
        peak_memory = number(result.get("gurobi_max_mem_used_gb"))
        first_incumbent = number(result.get("gurobi_first_incumbent_time"), -1.0)
        policy = "not_applicable"
        external_attempted = False
    else:
        external_attempted = truth(result.get("external_gini_tree_attempted"))
        required = (
            "external_gini_tree_root_coverage_valid",
            "external_gini_tree_parent_child_coverage_valid",
            "external_gini_tree_all_leaf_bounds_valid",
            "external_gini_tree_global_bound_monotone",
            "external_gini_tree_lifecycle_complete",
            "external_gini_tree_backend_parameter_roundtrip_valid")
        if external_attempted:
            correctness = correctness and all(
                truth(result.get(key)) for key in required)
        else:
            # A short sentinel may legitimately finish in the outer heuristic
            # before the exact tree starts.  Such a capped run is valid only
            # as a dispatch/policy sentinel, never as a certificate.
            correctness = correctness and not exact
        if exact and external_attempted:
            correctness = correctness and truth(
                result.get("external_gini_tree_strict_certified"))
        work = number(result.get("external_gini_tree_work"))
        nodes = number(result.get("external_gini_tree_nodes"))
        simplex = number(result.get("external_gini_tree_simplex_iterations"))
        split_count = int(number(result.get("external_gini_tree_split_count")))
        interval_count = int(number(
            result.get("external_gini_tree_final_leaf_count")))
        fixed_interval_model_count = int(number(
            result.get("external_gini_tree_model_count")))
        peak_memory = number(result.get("external_gini_tree_peak_memory_gb"))
        first_incumbent = number(
            result.get("external_gini_tree_first_incumbent_time_seconds"),
            -1.0)
        policy = str(result.get("external_gini_tree_interval_mip_policy"))
        expected_policy = str(command.get("inner_backend_policy"))
        correctness = correctness and policy == expected_policy
    return {
        "panel": panel, "instance_id": row["instance_id"],
        "difficulty_configuration": row["difficulty_configuration"],
        "V": row["V"], "M": row["M"], "T": row["T"],
        "method": method, "inner_backend_policy": policy,
        "external_tree_attempted": external_attempted,
        "cap_seconds": cap, "status": result.get("status"),
        "certificate": exact, "correctness_gate": correctness,
        "false_certificate": exact and not correctness,
        "lower_bound": lower, "verified_upper_bound": upper, "gap": gap,
        "gi_common_horizon": normalized_gi, "work": work,
        "process_time_seconds": process_seconds, "nodes": nodes,
        "simplex_iterations": simplex,
        "iterations_per_node": simplex / nodes if nodes > 0 else simplex,
        "split_count": split_count,
        "interval_count": interval_count,
        "fixed_interval_model_count": fixed_interval_model_count,
        "peak_memory_gb": peak_memory,
        "first_incumbent_time_seconds": first_incumbent,
        "adaptive_mass_mode": result.get("round47_c6_adaptive_mass"),
        "adaptive_mass_tau": result.get("round47_c6_adaptive_mass_tau"),
        "adaptive_mass_tau_explicit":
            result.get("round47_c6_adaptive_mass_tau_explicit"),
        "executable_sha256": marker["executable_sha256"],
        "run_id": run_id,
        "artifact_dir": run_dir.relative_to(OUT.parents[1]).as_posix()}


def severe(b: dict[str, object], c: dict[str, object]) -> bool:
    if truth(b["certificate"]) and truth(c["certificate"]):
        bw, cw = number(b["work"]), number(c["work"])
        bt, ct = number(b["process_time_seconds"]), number(c["process_time_seconds"])
        return ((cw / max(1e-12, bw) > 1.5 and cw - bw > 50) or
                (ct / max(1e-12, bt) > 1.5 and ct - bt > 60))
    if truth(b["certificate"]) and not truth(c["certificate"]):
        return True
    bg, cg = number(b["gi_common_horizon"]), number(c["gi_common_horizon"])
    gap_b, gap_c = number(b["gap"]), number(c["gap"])
    return ((cg / max(1e-12, bg) > 1.5 and cg - bg >= .05) or
            (gap_c / max(1e-12, gap_b) > 1.5 and gap_c - gap_b >= .05))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", choices=("integration", "sentinel", "sealed"),
                        required=True)
    parser.add_argument("--methods", required=True)
    parser.add_argument("--cap", type=float, required=True)
    parser.add_argument("--instances")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--decision", type=Path)
    args = parser.parse_args()
    methods = [value.strip() for value in args.methods.split(",") if value.strip()]
    selected = None if not args.instances else {
        value.strip() for value in args.instances.split(",") if value.strip()}
    rows = [row for row in panel_rows(args.panel)
            if selected is None or row["instance_id"] in selected]
    physical = [load_row(args.panel, row, method, args.cap)
                for row in rows for method in methods]
    args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
    with args.output.resolve().open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(physical[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(physical)
    if args.decision:
        by = {(str(row["instance_id"]), str(row["method"])): row
              for row in physical}
        baseline_method = "K1-AM-v0" if "K1-AM-v0" in methods else "P-GRB"
        candidate_method = "K1-AM-CANDIDATE"
        if candidate_method not in methods:
            raise RuntimeError("decision requires K1-AM-CANDIDATE")
        pairs = [(by[(str(row["instance_id"]), baseline_method)],
                  by[(str(row["instance_id"]), candidate_method)])
                 for row in rows]
        gains = sum(truth(c["certificate"]) and not truth(b["certificate"])
                    for b, c in pairs)
        losses = sum(truth(b["certificate"]) and not truth(c["certificate"])
                     for b, c in pairs)
        severe_count = sum(severe(b, c) for b, c in pairs)
        work_ratio = gm([(number(c["work"]) + 1) / (number(b["work"]) + 1)
                         for b, c in pairs])
        gi_ratio = (sum(number(c["gi_common_horizon"]) for _, c in pairs) /
                    max(1e-12, sum(number(b["gi_common_horizon"])
                                  for b, _ in pairs)))
        common_exact = [(number(c["work"]) / max(1e-12, number(b["work"])))
                        for b, c in pairs if truth(b["certificate"]) and
                        truth(c["certificate"])]
        exact_work_ratio = gm(common_exact)
        correctness_failures = sum(not truth(row["correctness_gate"])
                                   for row in physical)
        false_certificates = sum(truth(row["false_certificate"])
                                 for row in physical)
        material = exact_work_ratio <= .95 or (
            gains >= 1 and work_ratio <= 1.0 and gi_ratio <= 1.0)
        major_pairs = [(b, c) for b, c in pairs
                       if b["difficulty_configuration"] == "major witness"]
        easy_pairs = [(b, c) for b, c in pairs
                      if b["difficulty_configuration"] in {
                          "easy negative control", "startup/easy control"}]
        major_repair_preserved = bool(major_pairs) and all(
            (not truth(b["certificate"]) or truth(c["certificate"])) and
            number(c["gi_common_horizon"]) <=
                number(b["gi_common_horizon"]) + 1e-12
            for b, c in major_pairs)
        easy_controls_remain_easy = bool(easy_pairs) and all(
            (not truth(b["certificate"]) or truth(c["certificate"])) and
            not severe(b, c) for b, c in easy_pairs)
        passed = (correctness_failures == 0 and false_certificates == 0 and
                  losses == 0 and severe_count == 0 and work_ratio <= 1.0 and
                  gi_ratio <= 1.0 and material and major_repair_preserved and
                  easy_controls_remain_easy)
        decision = {
            "schema": "round53-k1-panel-decision-v1", "panel": args.panel,
            "cap_seconds": args.cap, "physical_rows": len(physical),
            "pair_count": len(pairs), "baseline_method": baseline_method,
            "candidate_method": candidate_method,
            "correctness_failures": correctness_failures,
            "false_certificates": false_certificates,
            "certificate_gains": gains, "certificate_losses": losses,
            "severe_regressions": severe_count,
            "shifted_work_geometric_mean_ratio": work_ratio,
            "common_exact_work_geometric_mean_ratio": exact_work_ratio,
            "aggregate_gi_ratio": gi_ratio,
            "material_improvement": material,
            "major_repair_preserved": major_repair_preserved,
            "easy_negative_control_remains_easy":
                easy_controls_remain_easy,
            "gate_pass": passed}
        args.decision.resolve().write_text(
            json.dumps(decision, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        print(json.dumps(decision, indent=2, sort_keys=True))
        return 0 if passed else 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
