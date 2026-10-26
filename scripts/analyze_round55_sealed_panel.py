#!/usr/bin/env python3
"""Compact, audit, and gate the completed Round 55 sealed panel."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

from run_round55_sealed_panel import (ARMS, CAP_BY_V, EVIDENCE, MANIFEST,
                                      RUNS, read_json)


TOL = 1e-7


def truth(value: object) -> bool:
    return value is True or str(value).lower() in {"1", "true"}


def number(value: object, default: float = 0.0) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]],
              fields: list[str] | None = None) -> None:
    columns = fields or (list(rows[0]) if rows else None)
    if not columns:
        raise RuntimeError(f"fields unavailable for {path}")
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore",
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def relative_gap(lower: float, upper: float) -> float:
    return max(0.0, (upper - lower) / max(1e-12, abs(upper)))


def trajectory(run_dir: Path, arm: str) -> list[tuple[float, float, float, float]]:
    points = []
    if arm == "P-GRB":
        for row in csv_rows(run_dir / "progress.csv"):
            if not truth(row.get("best_bound_available")):
                continue
            lower = number(row.get("best_bound"), math.nan)
            upper = (number(row.get("incumbent"), math.inf)
                     if truth(row.get("incumbent_available")) else math.inf)
            if math.isfinite(lower) and math.isfinite(upper):
                points.append((number(row.get("elapsed_runtime_seconds")),
                               relative_gap(lower, upper), lower, upper))
    else:
        for row in csv_rows(run_dir / "external" / "global_bound_trace.csv"):
            lower = number(row.get("valid_global_lower_bound"), math.nan)
            upper = number(row.get("verified_global_upper_bound"), math.inf)
            if math.isfinite(lower) and math.isfinite(upper):
                points.append((number(row.get("process_elapsed_seconds")),
                               relative_gap(lower, upper), lower, upper))
    points.sort()
    return points


def checkpoint(points: list[tuple[float, float, float, float]], horizon: float,
               exact: bool, process_seconds: float,
               final_lower: float, final_upper: float) -> dict[str, float]:
    previous_time, previous_gap, area = 0.0, 1.0, 0.0
    lower, upper = 0.0, final_upper
    for event_time, event_gap, event_lower, event_upper in points:
        event_time = min(horizon, max(previous_time, event_time))
        area += (event_time - previous_time) * previous_gap
        previous_time, previous_gap = event_time, event_gap
        lower, upper = event_lower, event_upper
        if event_time >= horizon:
            break
    if exact and process_seconds <= horizon:
        end = max(previous_time, process_seconds)
        area += (end - previous_time) * previous_gap
        previous_time, previous_gap = end, 0.0
        lower, upper = final_lower, final_upper
    if previous_time < horizon:
        area += (horizon - previous_time) * previous_gap
    return {"lower_bound": lower, "upper_bound": upper,
            "gap": relative_gap(lower, upper), "normalized_gi": area / horizon}


def load_row(instance: dict[str, Any], arm: str) -> tuple[dict[str, object], list[dict[str, object]]]:
    cap = CAP_BY_V[int(instance["V"])]
    run_id = f"{instance['instance_id']}__{arm}__{cap}s"
    run_dir = RUNS / run_id
    marker = read_json(run_dir / "completion_marker.json")
    result = read_json(run_dir / "result.json")
    if not (truth(marker.get("complete")) and truth(marker.get("cap_respected")) and
            int(marker.get("cap_seconds", -1)) == cap):
        raise RuntimeError(f"unsealed row: {run_id}")
    exact = truth(result.get("strict_certified_original_problem"))
    seconds = number(result.get("final_process_wall_time_seconds"))
    lower, upper = number(result.get("lower_bound")), number(result.get("upper_bound"))
    verification = result.get("verification", {})
    correctness = (truth(result.get("option_audit_consistent")) and
                   isinstance(verification, dict) and truth(verification.get("feasible")) and
                   lower <= upper + TOL * max(1.0, abs(upper)))
    if arm == "P-GRB":
        correctness = (correctness and truth(result.get("gurobi_lifecycle_valid")) and
                       truth(marker.get("pgrb_fingerprint_binding_passed")))
        work = number(result.get("gurobi_work"))
        nodes = number(result.get("gurobi_node_count"))
        memory = number(result.get("gurobi_max_mem_used_gb"))
        split_count, interval_count, model_count = 0, 0, 1
        policy = "not_applicable"
    else:
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
        correctness = correctness and result.get("algorithm_preset") == ARMS[arm]["preset"]
        policy = str(result.get("external_gini_tree_interval_mip_policy"))
        correctness = correctness and policy == ARMS[arm]["policy"]
        work = number(result.get("external_gini_tree_work"))
        nodes = number(result.get("external_gini_tree_nodes"))
        memory = number(result.get("external_gini_tree_peak_memory_gb"))
        split_count = int(number(result.get("external_gini_tree_split_count")))
        interval_count = int(number(result.get("external_gini_tree_final_leaf_count")))
        model_count = int(number(result.get("external_gini_tree_model_count")))
    points = trajectory(run_dir, arm)
    checkpoints = []
    for horizon in (300, 1200, 1800, 3600, 7200):
        if horizon > cap:
            continue
        values = checkpoint(points, horizon, exact, seconds, lower, upper)
        checkpoints.append({
            "instance_id": instance["instance_id"], "V": instance["V"],
            "difficulty_configuration": instance["difficulty_configuration"],
            "arm": arm, "cap_seconds": cap, "checkpoint_seconds": horizon,
            **values,
        })
    final_gi = next(row["normalized_gi"] for row in checkpoints
                    if row["checkpoint_seconds"] == cap)
    return ({
        "instance_id": instance["instance_id"], "V": instance["V"],
        "M": instance["M"], "Q": instance["Q"], "T": instance["T"],
        "difficulty_configuration": instance["difficulty_configuration"],
        "arm": arm, "inner_policy": policy, "cap_seconds": cap,
        "status": result.get("status"), "certificate": exact,
        "correctness_gate": correctness, "false_certificate": exact and not correctness,
        "lower_bound": lower, "verified_upper_bound": upper,
        "gap": relative_gap(lower, upper), "normalized_gi": final_gi,
        "work": work, "process_time_seconds": seconds, "nodes": nodes,
        "split_count": split_count, "interval_count": interval_count,
        "fixed_interval_model_count": model_count, "peak_memory_gb": memory,
        "executable_sha256": marker["executable_sha256"],
        "artifact_dir": run_dir.relative_to(EVIDENCE.parents[1]).as_posix(),
    }, checkpoints)


def severe(b: dict[str, object], c: dict[str, object]) -> bool:
    if truth(b["certificate"]) and truth(c["certificate"]):
        bw, cw = number(b["work"]), number(c["work"])
        bt, ct = number(b["process_time_seconds"]), number(c["process_time_seconds"])
        return ((cw / max(1e-12, bw) > 1.5 and cw - bw > 50) or
                (ct / max(1e-12, bt) > 1.5 and ct - bt > 60))
    if truth(b["certificate"]) and not truth(c["certificate"]):
        return True
    bg, cg = number(b["normalized_gi"]), number(c["normalized_gi"])
    gb, gc = number(b["gap"]), number(c["gap"])
    return ((cg / max(1e-12, bg) > 1.5 and cg - bg >= 0.05) or
            (gc / max(1e-12, gb) > 1.5 and gc - gb >= 0.05))


def gm(values: list[float]) -> float:
    return (math.exp(sum(math.log(max(1e-300, value)) for value in values) /
                     len(values)) if values else 1.0)


def comparison(instances: list[dict[str, Any]],
               by: dict[tuple[str, str], dict[str, object]],
               baseline_arm: str) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows = []
    for instance in instances:
        baseline = by[(instance["instance_id"], baseline_arm)]
        candidate = by[(instance["instance_id"], "K1-AM-SF-CANDIDATE")]
        rows.append({
            "instance_id": instance["instance_id"], "V": instance["V"],
            "difficulty_configuration": instance["difficulty_configuration"],
            "baseline_arm": baseline_arm, "candidate_arm": "K1-AM-SF-CANDIDATE",
            "baseline_certificate": baseline["certificate"],
            "candidate_certificate": candidate["certificate"],
            "certificate_gain": truth(candidate["certificate"]) and not truth(baseline["certificate"]),
            "certificate_loss": truth(baseline["certificate"]) and not truth(candidate["certificate"]),
            "shifted_work_ratio": (number(candidate["work"]) + 1) /
                                  (number(baseline["work"]) + 1),
            "gi_ratio": number(candidate["normalized_gi"]) /
                        max(1e-12, number(baseline["normalized_gi"])),
            "gap_ratio": number(candidate["gap"]) / max(1e-12, number(baseline["gap"])),
            "severe_regression": severe(baseline, candidate),
        })
    gains = sum(truth(row["certificate_gain"]) for row in rows)
    losses = sum(truth(row["certificate_loss"]) for row in rows)
    severe_count = sum(truth(row["severe_regression"]) for row in rows)
    return rows, {
        "baseline_arm": baseline_arm, "pair_count": len(rows),
        "certificate_gains": gains, "certificate_losses": losses,
        "severe_regressions": severe_count,
        "shifted_work_geometric_mean_ratio": gm([number(row["shifted_work_ratio"]) for row in rows]),
        "aggregate_gi_ratio": (sum(number(by[(instance["instance_id"], "K1-AM-SF-CANDIDATE")]["normalized_gi"])
                                   for instance in instances) /
                               max(1e-12, sum(number(by[(instance["instance_id"], baseline_arm)]["normalized_gi"])
                                              for instance in instances))),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkpoints", type=Path, required=True)
    parser.add_argument("--direct", type=Path, required=True)
    parser.add_argument("--certificate-audit", type=Path, required=True)
    parser.add_argument("--severe-audit", type=Path, required=True)
    parser.add_argument("--decision", type=Path, required=True)
    args = parser.parse_args()
    instances = [dict(row) for row in read_json(MANIFEST)["rows"]]
    physical, checkpoints = [], []
    for instance in instances:
        for arm in ARMS:
            result, result_checkpoints = load_row(instance, arm)
            physical.append(result)
            checkpoints.extend(result_checkpoints)
    write_csv(args.output, physical)
    write_csv(args.checkpoints, checkpoints)
    by = {(str(row["instance_id"]), str(row["arm"])): row for row in physical}
    stable_rows, stable = comparison(instances, by, "K1-AM-SF")
    pgrb_rows, pgrb = comparison(instances, by, "P-GRB")
    direct = stable_rows + pgrb_rows
    write_csv(args.direct, direct)
    certificate_rows = [{
        "instance_id": row["instance_id"], "arm": row["arm"],
        "certificate": row["certificate"], "correctness_gate": row["correctness_gate"],
        "false_certificate": row["false_certificate"],
        "classification": "valid_certificate" if truth(row["certificate"]) and truth(row["correctness_gate"])
                          else "valid_capped" if truth(row["correctness_gate"])
                          else "invalid",
    } for row in physical]
    write_csv(args.certificate_audit, certificate_rows)
    severe_rows = [row for row in direct if truth(row["severe_regression"])]
    write_csv(args.severe_audit, severe_rows, list(direct[0]))
    false = sum(truth(row["false_certificate"]) for row in physical)
    invalid = sum(not truth(row["correctness_gate"]) for row in physical)
    candidate_certs = sum(truth(row["certificate"]) and row["arm"] == "K1-AM-SF-CANDIDATE"
                          for row in physical)
    stable_certs = sum(truth(row["certificate"]) and row["arm"] == "K1-AM-SF"
                       for row in physical)
    pgrb_certs = sum(truth(row["certificate"]) and row["arm"] == "P-GRB"
                     for row in physical)
    benefited_groups = sorted({
        f"V{row['V']}:{row['difficulty_configuration']}" for row in stable_rows
        if truth(row["certificate_gain"]) or number(row["shifted_work_ratio"]) <= 0.8 or
        number(row["gi_ratio"]) <= 0.8})
    v50_worse = any(truth(row["severe_regression"]) for row in stable_rows if int(row["V"]) == 50)
    stable_gate = (false == 0 and invalid == 0 and candidate_certs >= stable_certs and
                   stable["severe_regressions"] == 0 and
                   ((stable["shifted_work_geometric_mean_ratio"] <= 0.95 and
                     stable["aggregate_gi_ratio"] <= 1.0) or
                    (stable["certificate_gains"] >= 1 and
                     stable["shifted_work_geometric_mean_ratio"] <= 1.0 and
                     stable["aggregate_gi_ratio"] <= 1.0)) and
                   len(benefited_groups) >= 2 and not v50_worse)
    pgrb_gate = (false == 0 and invalid == 0 and pgrb["severe_regressions"] == 0 and
                 pgrb["shifted_work_geometric_mean_ratio"] < 1.0 and
                 pgrb["aggregate_gi_ratio"] < 1.0 and candidate_certs >= pgrb_certs)
    strong = (stable["severe_regressions"] == 0 and stable["certificate_losses"] == 0 and
              ((stable["shifted_work_geometric_mean_ratio"] <= 0.8 and
                stable["aggregate_gi_ratio"] <= 0.8) or stable["certificate_gains"] >= 2) and
              len({str(row["V"]) for row in stable_rows
                   if truth(row["certificate_gain"]) or number(row["shifted_work_ratio"]) <= 0.8 or
                   number(row["gi_ratio"]) <= 0.8}) >= 2)
    decision = {
        "schema": "round55-sealed-generalization-decision-v1",
        "physical_rows": len(physical), "instance_count": len(instances),
        "correctness_failures": invalid, "false_certificates": false,
        "certificate_counts": {"P-GRB": pgrb_certs, "K1-AM-SF": stable_certs,
                               "K1-AM-SF-CANDIDATE": candidate_certs},
        "candidate_vs_stable": stable, "candidate_vs_pgrb": pgrb,
        "benefited_size_configuration_groups": benefited_groups,
        "V50_materially_worsened": v50_worse,
        "promotion_gate_vs_stable": stable_gate,
        "final_pgrb_gate": pgrb_gate,
        "strong_result_expansion_gate": strong,
    }
    write_json(args.decision, decision)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if false == 0 and invalid == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
