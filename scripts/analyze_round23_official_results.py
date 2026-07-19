#!/usr/bin/env python3
"""Produce the preregistered Round 23 paired and exactness analyses."""

from __future__ import annotations

import csv
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_global_gini_tree_round23"
OFFICIAL = OUT / "official"
R22 = ROOT / "results" / "gf_global_gini_tree_unified_validation_round"
INSTANCES = (
    "V12_M1", "V12_M2", "high_imbalance_seed3202",
    "high_imbalance_seed4201", "tight_T_seed3101", "moderate_seed4302",
)
ARMS = ("s0c", "s0m")
THRESHOLDS = (0.20, 0.10, 0.05, 0.02, 0.01, 0.005, 0.001)


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def boolean(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def read_csv_maybe_gzip(path: Path) -> list[dict[str, str]]:
    actual = path if path.exists() else path.with_suffix(path.suffix + ".gz")
    opener = gzip.open if actual.suffix == ".gz" else open
    with opener(actual, "rt", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_rows(path: Path, values: list[dict[str, Any]]) -> None:
    if not values:
        raise RuntimeError(f"refusing empty required artifact: {path}")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(values)


def common_ubs() -> dict[str, float]:
    return {
        row["instance"]: float(row["frozen_common_verified_ub"])
        for row in csv_rows(OUT / "comparison_ub_manifest.csv")
    }


def run_dir(instance: str, arm: str, stage: str = "stage2") -> Path:
    budget = 900 if stage == "stage2" else 300
    return OFFICIAL / f"round23_{stage}__{instance}__{arm}__{budget}s"


def load_run(instance: str, arm: str, stage: str = "stage2") -> dict[str, Any]:
    directory = run_dir(instance, arm, stage)
    return {
        "directory": directory,
        "command": json.loads((directory / "command.json").read_text(encoding="utf-8")),
        "result": json.loads((directory / "result.json").read_text(encoding="utf-8")),
        "events": read_csv_maybe_gzip(directory / "raw_progress.csv"),
    }


def gap(upper: float, lower: Any) -> float | None:
    if not finite(lower):
        return None
    residual = max(0.0, upper - float(lower))
    return residual / abs(upper) if abs(upper) > 1e-12 else (
        0.0 if residual == 0.0 else math.inf)


def points(events: list[dict[str, str]], upper: float) -> list[tuple[float, float]]:
    answer = []
    for event in events:
        if finite(event.get("observation_time_seconds")) and finite(
                event.get("native_best_bound")):
            current = gap(upper, event["native_best_bound"])
            if current is not None:
                answer.append((float(event["observation_time_seconds"]), current))
    return answer


def normalized_auc(values: list[tuple[float, float]]) -> tuple[float | None, float]:
    if len(values) < 2:
        return None, 0.0
    area = 0.0
    for (t0, g0), (t1, g1) in zip(values, values[1:]):
        p0 = max(0.0, min(1.0, 1.0 - g0))
        p1 = max(0.0, min(1.0, 1.0 - g1))
        area += max(0.0, t1 - t0) * (p0 + p1) / 2.0
    horizon = values[-1][0] - values[0][0]
    return (area / horizon if horizon > 0.0 else None), horizon


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def topology_metrics(directory: Path) -> dict[str, Any]:
    rows = csv_rows(directory / "gini_topology.csv")
    lifts: list[float] = []
    used = contradictions = discriminated = 0
    for row in rows:
        if boolean(row.get("sibling_discriminated")):
            discriminated += 1
        for prefix in ("lower", "upper"):
            if finite(row.get(f"{prefix}_lift")):
                lifts.append(float(row[f"{prefix}_lift"]))
            if boolean(row.get(f"{prefix}_dispersion_bound_used")):
                used += 1
            if boolean(row.get(f"{prefix}_domain_contradiction")):
                contradictions += 1
    return {
        "topology_branch_rows": len(rows),
        "proved_child_estimates": len(lifts),
        "dispersion_bound_used_children": used,
        "domain_contradiction_children": contradictions,
        "discriminated_pairs_from_trace": discriminated,
        "mean_estimate_lift": mean(lifts) if lifts else None,
        "maximum_estimate_lift": max(lifts) if lifts else None,
    }


def sibling_metrics(directory: Path) -> dict[str, Any]:
    rows = csv_rows(directory / "sibling_delay.csv")
    seconds = [float(row["delay_seconds"]) for row in rows
               if finite(row.get("delay_seconds"))]
    nodes = [float(row["delay_processed_nodes"]) for row in rows
             if finite(row.get("delay_processed_nodes"))]
    return {
        "sibling_observations": len(rows),
        "median_sibling_delay_seconds": median(seconds) if seconds else None,
        "p95_sibling_delay_seconds": percentile(seconds, 0.95),
        "maximum_sibling_delay_seconds": max(seconds) if seconds else None,
        "median_sibling_delay_nodes": median(nodes) if nodes else None,
        "p95_sibling_delay_nodes": percentile(nodes, 0.95),
        "maximum_sibling_delay_nodes": max(nodes) if nodes else None,
    }


def raw_audit(run: dict[str, Any]) -> dict[str, Any]:
    events = run["events"]
    times = [float(row["observation_time_seconds"]) for row in events
             if finite(row.get("observation_time_seconds"))]
    bounds = [float(row["native_best_bound"]) for row in events
              if finite(row.get("native_best_bound"))]
    strict_times = all(right > left for left, right in zip(times, times[1:]))
    final_bound = float(run["result"]["native_mip_best_bound"])
    endpoint_matches = bool(bounds) and math.isclose(
        bounds[-1], final_bound, rel_tol=1e-12, abs_tol=1e-12)
    final_record = boolean(run["result"].get("dense_progress_final_record_appended"))
    return {
        "raw_event_count": len(events),
        "raw_timestamps_strictly_increase": strict_times,
        "raw_final_bound": bounds[-1] if bounds else None,
        "solver_final_endpoint_matches_result": endpoint_matches,
        "final_record_appended": final_record,
    }


def main() -> int:
    ubs = common_ubs()
    loaded = {(instance, arm): load_run(instance, arm)
              for instance in INSTANCES for arm in ARMS}

    auc_rows: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []
    for instance in INSTANCES:
        upper = ubs[instance]
        for arm in ARMS:
            run = loaded[(instance, arm)]
            values = points(run["events"], upper)
            auc_value, horizon = normalized_auc(values)
            result = run["result"]
            last_improvement = max(
                (float(row["last_valid_lower_bound_improvement_time"])
                 for row in run["events"]
                 if finite(row.get("last_valid_lower_bound_improvement_time"))),
                default=None)
            end_time = values[-1][0] if values else None
            auc_rows.append({
                "instance": instance,
                "arm": "S0-C" if arm == "s0c" else "S0-M",
                "run_id": run["command"]["run_id"],
                "frozen_common_verified_ub": upper,
                "final_native_lb": result["native_mip_best_bound"],
                "final_common_ub_gap": gap(upper, result["native_mip_best_bound"]),
                "normalized_bound_progress_auc": auc_value,
                "auc_horizon_seconds": horizon,
                "raw_bound_observation_count": len(values),
                "last_valid_lb_improvement_seconds": last_improvement,
                "stagnation_duration_seconds": (
                    end_time - last_improvement
                    if end_time is not None and last_improvement is not None else None),
            })
            for threshold in THRESHOLDS:
                found = next((item for item in values if item[1] <= threshold), None)
                previous = None
                for item in values:
                    if found is not None and item == found:
                        break
                    previous = item
                threshold_rows.append({
                    "instance": instance,
                    "arm": "S0-C" if arm == "s0c" else "S0-M",
                    "run_id": run["command"]["run_id"],
                    "frozen_common_verified_ub": upper,
                    "gap_threshold": threshold,
                    "crossing_observed": found is not None,
                    "preceding_observation_seconds": previous[0] if previous else None,
                    "preceding_gap": previous[1] if previous else None,
                    "first_observed_crossing_seconds": found[0] if found else None,
                    "first_observed_gap": found[1] if found else None,
                })
    write_rows(OUT / "common_ub_bound_progress_auc.csv", auc_rows)
    write_rows(OUT / "common_ub_time_to_gap_thresholds.csv", threshold_rows)

    auc_by = {(row["instance"], row["arm"]): row for row in auc_rows}
    pair_rows: list[dict[str, Any]] = []
    for instance in INSTANCES:
        control = loaded[(instance, "s0c")]
        candidate = loaded[(instance, "s0m")]
        c_result, m_result = control["result"], candidate["result"]
        c_command, m_command = control["command"], candidate["command"]
        c_strict = boolean(c_result["strict_certified_original_problem"])
        m_strict = boolean(m_result["strict_certified_original_problem"])
        c_lb, m_lb = float(c_result["native_mip_best_bound"]), float(
            m_result["native_mip_best_bound"])
        tolerance = 1e-12 * max(1.0, abs(c_lb), abs(m_lb))
        c_auc = auc_by[(instance, "S0-C")]["normalized_bound_progress_auc"]
        m_auc = auc_by[(instance, "S0-M")]["normalized_bound_progress_auc"]
        if c_strict != m_strict:
            classification = "improve" if m_strict else "regress"
            basis = "strict_certificate_gain" if m_strict else "strict_certificate_loss"
        elif c_strict and m_strict:
            delta = float(m_command["runner_wall_seconds"]) - float(
                c_command["runner_wall_seconds"])
            if abs(delta) <= 1e-6:
                classification, basis = "tie", "strict_process_wall_time_tie"
            else:
                classification = "improve" if delta < 0.0 else "regress"
                basis = "strict_process_wall_time"
        elif m_lb > c_lb + tolerance:
            classification, basis = "improve", "higher_final_native_lb_under_common_ub"
        elif c_lb > m_lb + tolerance:
            classification, basis = "regress", "lower_final_native_lb_under_common_ub"
        elif finite(c_auc) and finite(m_auc) and float(m_auc) > float(c_auc) + 1e-12:
            classification, basis = "improve", "higher_common_ub_auc"
        elif finite(c_auc) and finite(m_auc) and float(c_auc) > float(m_auc) + 1e-12:
            classification, basis = "regress", "lower_common_ub_auc"
        else:
            classification, basis = "tie", "hierarchy_tie"
        strict_slowdown = ((float(m_command["runner_wall_seconds"]) /
                            float(c_command["runner_wall_seconds"]) - 1.0)
                           if c_strict and m_strict else None)
        common_gap_delta = (gap(ubs[instance], m_lb) - gap(ubs[instance], c_lb))
        auc_delta = (float(m_auc) - float(c_auc)) if finite(c_auc) and finite(m_auc) else None
        material = ((c_strict and not m_strict) or
                    (strict_slowdown is not None and strict_slowdown > 0.10) or
                    (common_gap_delta is not None and common_gap_delta > 0.01) or
                    (auc_delta is not None and auc_delta < -0.02))
        pair_rows.append({
            "instance": instance,
            "classification": classification,
            "decision_basis": basis,
            "S0_C_strict": c_strict,
            "S0_M_strict": m_strict,
            "certificate_gain": (not c_strict and m_strict),
            "certificate_loss": (c_strict and not m_strict),
            "S0_C_process_wall_seconds": c_command["runner_wall_seconds"],
            "S0_M_process_wall_seconds": m_command["runner_wall_seconds"],
            "strict_time_delta_seconds": (
                float(m_command["runner_wall_seconds"]) -
                float(c_command["runner_wall_seconds"]) if c_strict and m_strict else None),
            "strict_slowdown_fraction": strict_slowdown,
            "frozen_common_verified_ub": ubs[instance],
            "S0_C_final_native_lb": c_lb,
            "S0_M_final_native_lb": m_lb,
            "native_lb_delta_M_minus_C": m_lb - c_lb,
            "S0_C_common_ub_gap": gap(ubs[instance], c_lb),
            "S0_M_common_ub_gap": gap(ubs[instance], m_lb),
            "common_ub_gap_delta_M_minus_C": common_gap_delta,
            "S0_C_normalized_auc": c_auc,
            "S0_M_normalized_auc": m_auc,
            "auc_delta_M_minus_C": auc_delta,
            "material_regression": material,
        })
    write_rows(OUT / "paired_candidate_comparison.csv", pair_rows)

    time_rows: list[dict[str, Any]] = []
    for instance in INSTANCES:
        for arm in ARMS:
            run = loaded[(instance, arm)]
            result, command = run["result"], run["command"]
            strict = boolean(result["strict_certified_original_problem"])
            time_rows.append({
                "instance": instance,
                "arm": "S0-C" if arm == "s0c" else "S0-M",
                "evidence_source": "Round23_official_live",
                "run_id": command["run_id"],
                "native_status_code": result["native_mip_status_code"],
                "strict_certified_original_problem": strict,
                "time_to_strict_certificate_seconds": (
                    command["runner_wall_seconds"] if strict else None),
                "time_unavailable_reason": None if strict else "no_strict_certificate_by_deadline",
            })
    plain_rows = [row for row in csv_rows(R22 / "strict_certificate_summary.csv")
                  if row["instance"] in INSTANCES and row["arm"] == "plain" and
                  row["budget_seconds"] == "900"]
    for instance in INSTANCES:
        matches = [row for row in plain_rows if row["instance"] == instance]
        if len(matches) != 1:
            raise RuntimeError(f"expected one reused plain row for {instance}, found {len(matches)}")
        row = matches[0]
        strict = boolean(row["strict_certified"])
        time_rows.append({
            "instance": instance,
            "arm": "plain",
            "evidence_source": "immutable_Round22_reused_comparison_only",
            "run_id": row["run_id"],
            "native_status_code": row["native_status_code"],
            "strict_certified_original_problem": strict,
            "time_to_strict_certificate_seconds": row["runtime_seconds"] if strict else None,
            "time_unavailable_reason": None if strict else "no_strict_certificate_by_deadline",
        })
    write_rows(OUT / "time_to_strict_certificate.csv", time_rows)

    overhead_rows: list[dict[str, Any]] = []
    for instance in INSTANCES:
        runs = {arm: loaded[(instance, arm)] for arm in ARMS}
        metrics = {}
        for arm, run in runs.items():
            result = run["result"]
            metrics[arm] = {
                **topology_metrics(run["directory"]),
                **sibling_metrics(run["directory"]),
                "process_wall_seconds": run["command"]["runner_wall_seconds"],
                "row_factory_seconds": result["global_gini_tree_row_factory_seconds"],
                "callback_packing_seconds": result["global_gini_tree_callback_packing_seconds"],
                "local_row_api_seconds": result["global_gini_tree_local_row_api_seconds"],
                "dense_callback_wall_seconds": result["dense_progress_callback_wall_seconds"],
                "dense_serialization_seconds": result["dense_progress_serialization_seconds"],
                "dense_instrumentation_wall_percent": result[
                    "dense_progress_instrumentation_wall_percent"],
                "processed_nodes": result["native_mip_node_count"],
                "simplex_iterations": result["global_gini_tree_native_simplex_iterations"],
                "gini_children": result["global_gini_tree_gini_children_created"],
                "ordinary_branches": result["global_gini_tree_ordinary_branch_fallbacks"],
            }
        row: dict[str, Any] = {"instance": instance}
        for label, arm in (("S0_C", "s0c"), ("S0_M", "s0m")):
            for key, value in metrics[arm].items():
                row[f"{label}_{key}"] = value
        row["process_wall_delta_M_minus_C"] = (
            metrics["s0m"]["process_wall_seconds"] -
            metrics["s0c"]["process_wall_seconds"])
        row["callback_packing_delta_M_minus_C"] = (
            metrics["s0m"]["callback_packing_seconds"] -
            metrics["s0c"]["callback_packing_seconds"])
        overhead_rows.append(row)
    write_rows(OUT / "mechanism_overhead.csv", overhead_rows)

    exactness_rows: list[dict[str, Any]] = []
    for stage, instances in (("stage1", ("V12_M2", "high_imbalance_seed3202",
                                          "tight_T_seed3101")),
                             ("stage2", INSTANCES)):
        for instance in instances:
            for arm in ARMS:
                run = load_run(instance, arm, stage)
                result, command = run["result"], run["command"]
                audit = raw_audit(run)
                failure_count = sum(int(result[key]) for key in (
                    "global_gini_tree_callback_failures",
                    "global_gini_tree_child_estimate_failures",
                    "global_gini_tree_coverage_failures",
                    "global_gini_tree_local_row_failures",
                    "global_gini_tree_column_mapping_failures",
                    "global_gini_tree_local_bound_api_failures",
                    "global_gini_tree_node_info_api_failures",
                    "global_gini_tree_post_row_reoptimization_failures",
                ))
                valid = all((
                    boolean(command["structural_gate_passed"]),
                    boolean(result["model_correctness_verified"]),
                    boolean(result["global_gini_tree_lifecycle_valid"]),
                    boolean(result["native_mip_strict_gap_parameters_valid"]),
                    boolean(result["feasibility_consistency_gate_passed"]),
                    boolean(result["verified_incumbent_original_problem_feasible"]),
                    failure_count == 0,
                    audit["raw_timestamps_strictly_increase"],
                    audit["solver_final_endpoint_matches_result"],
                    audit["final_record_appended"],
                ))
                exactness_rows.append({
                    "stage": stage,
                    "instance": instance,
                    "arm": "S0-C" if arm == "s0c" else "S0-M",
                    "run_id": command["run_id"],
                    "source_commit": command["source_commit"],
                    "executable_sha256": command["executable_sha256"],
                    "instance_sha256": command["instance_sha256"],
                    "manifest_sha256": command["option_manifest_sha256"],
                    "structural_gate_passed": command["structural_gate_passed"],
                    "native_status_code": result["native_mip_status_code"],
                    "strict_certificate_class": result["strict_certificate_class"],
                    "strict_certified_original_problem": result[
                        "strict_certified_original_problem"],
                    "model_correctness_verified": result["model_correctness_verified"],
                    "verified_incumbent_original_problem_feasible": result[
                        "verified_incumbent_original_problem_feasible"],
                    "feasibility_consistency_gate_passed": result[
                        "feasibility_consistency_gate_passed"],
                    "strict_gap_parameter_readbacks_valid": result[
                        "native_mip_strict_gap_parameters_valid"],
                    "global_tree_lifecycle_valid": result[
                        "global_gini_tree_lifecycle_valid"],
                    "callback_and_exactness_failure_count": failure_count,
                    **audit,
                    "exactness_audit_passed": valid,
                })
    write_rows(OUT / "exactness_audit.csv", exactness_rows)

    counts = defaultdict(int)
    for row in pair_rows:
        counts[row["classification"]] += 1
    if sum(counts.values()) != len(INSTANCES):
        raise RuntimeError("paired classification count mismatch")
    if not all(boolean(row["exactness_audit_passed"]) for row in exactness_rows):
        raise RuntimeError("one or more official exactness audits failed")
    print(json.dumps({
        "pair_counts": dict(counts),
        "certificate_gains": sum(boolean(row["certificate_gain"]) for row in pair_rows),
        "certificate_losses": sum(boolean(row["certificate_loss"]) for row in pair_rows),
        "material_regressions": sum(boolean(row["material_regression"]) for row in pair_rows),
        "exactness_rows": len(exactness_rows),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
