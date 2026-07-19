#!/usr/bin/env python3
"""Round 23 no-solve reanalysis of immutable Round 22 evidence."""

from __future__ import annotations

import csv
import gzip
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
R22 = ROOT / "results/gf_global_gini_tree_unified_validation_round"
OUT = ROOT / "results/gf_global_gini_tree_round23"
THRESHOLDS = (0.2, 0.1, 0.05, 0.02, 0.01, 0.005, 0.001)


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_rows(path: Path, values: list[dict[str, Any]]) -> None:
    if not values:
        raise RuntimeError(f"refusing empty artifact: {path}")
    fields: list[str] = []
    for value in values:
        for key in value:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(values)


def read_json(run_id: str) -> dict[str, Any]:
    return json.loads((R22 / "raw" / f"{run_id}.json").read_text(encoding="utf-8"))


def read_csv_maybe_gzip(base: Path) -> list[dict[str, str]]:
    path = base if base.exists() else base.with_suffix(base.suffix + ".gz")
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def gap(upper: float, lower: Any) -> float | None:
    if not finite(lower):
        return None
    residual = max(0.0, upper - float(lower))
    return residual / abs(upper) if abs(upper) > 1e-12 else (
        0.0 if residual == 0.0 else math.inf
    )


def event_points(run_id: str, upper: float) -> list[tuple[float, float]]:
    events = read_csv_maybe_gzip(R22 / "runs" / run_id / "raw_progress.csv")
    points = []
    for event in events:
        if finite(event.get("observation_time_seconds")) and finite(
            event.get("native_best_bound")
        ):
            current_gap = gap(upper, event["native_best_bound"])
            if current_gap is not None:
                points.append((float(event["observation_time_seconds"]), current_gap))
    return points


def auc(points: list[tuple[float, float]]) -> tuple[float | None, float, int]:
    if len(points) < 2:
        return None, 0.0, len(points)
    area = 0.0
    for (t0, g0), (t1, g1) in zip(points, points[1:]):
        p0 = max(0.0, min(1.0, 1.0 - g0))
        p1 = max(0.0, min(1.0, 1.0 - g1))
        area += max(0.0, t1 - t0) * (p0 + p1) / 2.0
    horizon = points[-1][0] - points[0][0]
    return (area / horizon if horizon > 0.0 else None), horizon, len(points)


def threshold_rows(
    meta: dict[str, str], view: str, upper: float, points: list[tuple[float, float]]
) -> list[dict[str, Any]]:
    result = []
    for threshold in THRESHOLDS:
        found = None
        previous = None
        for point in points:
            if point[1] <= threshold:
                found = point
                break
            previous = point
        result.append({
            **meta,
            "ub_view": view,
            "comparison_ub": upper,
            "gap_threshold": threshold,
            "crossing_observed": found is not None,
            "preceding_observation_seconds": previous[0] if previous else "",
            "preceding_gap": previous[1] if previous else "",
            "first_observed_crossing_seconds": found[0] if found else "",
            "first_observed_gap": found[1] if found else "",
        })
    return result


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


def final_pair_classification(s0: dict[str, str], plain: dict[str, str]) -> tuple[str, str]:
    if s0["instance"] == "moderate_seed4301":
        return "unavailable", "round22_s0_status103_excluded_after_correctness_fix"
    s0_strict = s0["strict_certified"] == "True"
    plain_strict = plain["strict_certified"] == "True"
    if s0_strict != plain_strict:
        return ("S0", "strict_certificate") if s0_strict else ("plain", "strict_certificate")
    if s0_strict and plain_strict:
        s0_time = float(s0["runtime_seconds"])
        plain_time = float(plain["runtime_seconds"])
        if s0_time != plain_time:
            return ("S0", "strict_process_wall_time") if s0_time < plain_time else (
                "plain", "strict_process_wall_time"
            )
    s0_lb = float(s0["native_best_bound"]) if finite(s0["native_best_bound"]) else None
    plain_lb = float(plain["native_best_bound"]) if finite(plain["native_best_bound"]) else None
    if s0_lb is None or plain_lb is None:
        if s0_lb is None and plain_lb is None:
            return "unavailable", "both_native_lower_bounds_unavailable"
        return ("S0", "native_lower_bound_availability") if s0_lb is not None else (
            "plain", "native_lower_bound_availability"
        )
    tolerance = 1e-12 * max(1.0, abs(s0_lb), abs(plain_lb))
    if s0_lb > plain_lb + tolerance:
        return "S0", "common_ub_native_lower_bound"
    if plain_lb > s0_lb + tolerance:
        return "plain", "common_ub_native_lower_bound"
    return "tie", "native_lower_bound_tie"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = [row for row in rows(R22 / "strict_certificate_summary.csv")
               if row["stage"] in {"stage2", "stage3", "stage4", "stage5"}]
    by_key = {(row["stage"], row["instance"], row["arm"].lower()): row
              for row in summary}
    comparison_ubs: dict[str, float] = {}
    ub_sources: dict[str, list[str]] = defaultdict(list)
    for row in summary:
        if row["independent_verifier_passed"] == "True" and finite(row["verified_ub"]):
            value = float(row["verified_ub"])
            if row["instance"] not in comparison_ubs or value < comparison_ubs[row["instance"]]:
                comparison_ubs[row["instance"]] = value
                ub_sources[row["instance"]] = [row["run_id"]]
            elif value == comparison_ubs[row["instance"]]:
                ub_sources[row["instance"]].append(row["run_id"])
    ub_manifest = []
    for instance in sorted(comparison_ubs):
        ub_manifest.append({
            "instance": instance,
            "frozen_common_verified_ub": comparison_ubs[instance],
            "selection_rule": "minimum independently verified UB in immutable Round 22 official evidence",
            "source_run_ids": "|".join(ub_sources[instance]),
            "frozen_before_round23_candidate_runs": True,
            "plain_information_enters_tailored_solve": False,
        })
    write_rows(OUT / "comparison_ub_manifest.csv", ub_manifest)

    exact_rows: list[dict[str, Any]] = []
    final_rows: list[dict[str, Any]] = []
    auc_rows: list[dict[str, Any]] = []
    crossing_rows: list[dict[str, Any]] = []
    pair_keys = sorted({(row["stage"], row["suite"], row["instance"], row["budget_seconds"])
                        for row in summary if row["arm"] == "S0"})
    for stage, suite, instance, budget in pair_keys:
        s0 = by_key[(stage, instance, "s0")]
        plain = by_key[(stage, instance, "plain")]
        winner, basis = final_pair_classification(s0, plain)
        common_ub = comparison_ubs[instance]
        plain_ub = float(plain["verified_ub"])
        exact_rows.append({
            "stage": stage, "suite": suite, "instance": instance,
            "budget_seconds": budget,
            "S0_strict": s0["strict_certified"],
            "plain_strict": plain["strict_certified"],
            "S0_process_wall_seconds": s0["runtime_seconds"],
            "plain_process_wall_seconds": plain["runtime_seconds"],
            "hierarchy_winner": winner,
            "decision_basis": basis,
        })
        final_rows.append({
            "stage": stage, "suite": suite, "instance": instance,
            "budget_seconds": budget,
            "S0_status": s0["native_status_code"],
            "plain_status": plain["native_status_code"],
            "S0_native_lb": s0["native_best_bound"],
            "plain_native_lb": plain["native_best_bound"],
            "plain_verified_ub": plain_ub,
            "frozen_common_verified_ub": common_ub,
            "S0_plain_ub_gap": gap(plain_ub, s0["native_best_bound"]),
            "plain_plain_ub_gap": gap(plain_ub, plain["native_best_bound"]),
            "S0_common_ub_gap": gap(common_ub, s0["native_best_bound"]),
            "plain_common_ub_gap": gap(common_ub, plain["native_best_bound"]),
            "hierarchy_winner": winner,
            "decision_basis": basis,
            "performance_eligible": instance != "moderate_seed4301",
        })
        for arm, row in (("S0", s0), ("plain", plain)):
            meta = {"stage": stage, "suite": suite, "instance": instance,
                    "budget_seconds": budget, "arm": arm, "run_id": row["run_id"]}
            for view, upper in (("plain_ub", plain_ub), ("frozen_common_ub", common_ub)):
                points = event_points(row["run_id"], upper)
                normalized, horizon, count = auc(points)
                auc_rows.append({
                    **meta, "ub_view": view, "comparison_ub": upper,
                    "observed_horizon_seconds": horizon,
                    "normalized_bound_progress_auc": normalized,
                    "observation_count": count,
                    "performance_eligible": instance != "moderate_seed4301",
                })
                crossing_rows.extend(threshold_rows(meta, view, upper, points))
    write_rows(OUT / "stable_s0_vs_plain_exact_time.csv", exact_rows)
    write_rows(OUT / "stable_s0_vs_plain_common_ub_final.csv", final_rows)
    write_rows(OUT / "stable_s0_vs_plain_common_ub_auc.csv", auc_rows)
    write_rows(OUT / "stable_s0_vs_plain_gap_thresholds.csv", crossing_rows)

    bottleneck_rows: list[dict[str, Any]] = []
    sibling_rows: list[dict[str, Any]] = []
    discrimination_rows: list[dict[str, Any]] = []
    for row in summary:
        if row["arm"] not in {"S0", "S1"} or row["instance"] == "moderate_seed4301":
            continue
        run_id = row["run_id"]
        data = read_json(run_id)
        events = read_csv_maybe_gzip(R22 / "runs" / run_id / "raw_progress.csv")
        first_gini = data.get("global_gini_tree_first_gini_branch_time")
        root_bounds = [float(event["native_best_bound"]) for event in events
                       if finite(event.get("native_best_bound")) and finite(first_gini)
                       and float(event["observation_time_seconds"]) <= float(first_gini)]
        first_ordinary = next((float(event["observation_time_seconds"])
                               for event in events
                               if finite(event.get("ordinary_branch_count"))
                               and float(event["ordinary_branch_count"]) > 0), None)
        open_values = [float(event["open_nodes"]) for event in events
                       if finite(event.get("open_nodes"))]
        sibling_path = R22 / "runs" / run_id / "sibling_delay.csv"
        sibling_data = rows(sibling_path) if sibling_path.exists() else []
        delays = [float(item["delay_seconds"]) for item in sibling_data
                  if finite(item.get("delay_seconds"))]
        node_delays = [float(item["delay_processed_nodes"]) for item in sibling_data
                       if finite(item.get("delay_processed_nodes"))]
        post_path = R22 / "runs" / run_id / "post_rows.csv"
        post = rows(post_path) if post_path.exists() else []
        lifts = [float(item["post_local_row_relaxation"]) -
                 float(item["pre_local_row_relaxation"])
                 for item in post if finite(item.get("pre_local_row_relaxation"))
                 and finite(item.get("post_local_row_relaxation"))]
        runtime = float(row["runtime_seconds"])
        last_improvement = data.get("last_bound_improvement_time")
        equal_pairs = int(data.get("global_gini_tree_sibling_equal_estimate_pairs", 0))
        discriminated = int(data.get("global_gini_tree_sibling_discriminated_pairs", 0))
        max_delay = max(delays, default=0.0)
        if max_delay >= 300.0:
            classification = "sibling_starvation"
        elif equal_pairs > discriminated and equal_pairs > 0:
            classification = "equal_child_estimates"
        elif int(data.get("global_gini_tree_ordinary_branch_fallbacks", 0)) > 1000:
            classification = "ordinary_B&B_growth"
        else:
            classification = "mixed"
        bottleneck_rows.append({
            "run_id": run_id, "stage": row["stage"], "suite": row["suite"],
            "instance": row["instance"], "arm": row["arm"],
            "budget_seconds": row["budget_seconds"],
            "root_completion_seconds": first_gini,
            "root_lower_bound": root_bounds[-1] if root_bounds else "",
            "first_gini_branch_seconds": first_gini,
            "first_ordinary_branch_seconds": first_ordinary,
            "gini_branches": data.get("global_gini_tree_gini_branch_nodes"),
            "ordinary_branches": data.get("global_gini_tree_ordinary_branch_fallbacks"),
            "equal_estimate_sibling_pairs": equal_pairs,
            "discriminated_sibling_pairs": discriminated,
            "sibling_delay_max_seconds": max_delay,
            "sibling_delay_max_nodes": max(node_delays, default=0.0),
            "maximum_open_nodes": max(open_values, default=""),
            "final_native_lower_bound": row["native_best_bound"],
            "last_lower_bound_improvement_seconds": last_improvement,
            "stagnation_seconds": runtime - float(last_improvement)
                if finite(last_improvement) else "",
            "simplex_iterations": data.get("global_gini_tree_native_simplex_iterations"),
            "iterations_per_processed_node":
                float(data.get("global_gini_tree_native_simplex_iterations", 0)) /
                max(1.0, float(row["nodes"])),
            "local_rows": data.get("global_gini_tree_local_rows_attached"),
            "mean_post_row_relaxation_lift": sum(lifts) / len(lifts) if lifts else "",
            "row_factory_seconds": data.get("global_gini_tree_row_factory_seconds"),
            "row_api_seconds": data.get("global_gini_tree_local_row_api_seconds"),
            "native_cut_counts": data.get("global_gini_tree_native_cut_counts"),
            "dense_instrumentation_percent": row["instrumentation_percent"],
            "dominant_observed_bottleneck": classification,
        })
        sibling_rows.append({
            "run_id": run_id, "instance": row["instance"], "arm": row["arm"],
            "observed_first_touch_count": len(delays),
            "delay_seconds_median": percentile(delays, 0.5),
            "delay_seconds_p90": percentile(delays, 0.9),
            "delay_seconds_p95": percentile(delays, 0.95),
            "delay_seconds_max": max(delays, default=""),
            "delay_nodes_median": percentile(node_delays, 0.5),
            "delay_nodes_p95": percentile(node_delays, 0.95),
            "delay_nodes_max": max(node_delays, default=""),
            "delays_over_300_seconds": sum(value > 300 for value in delays),
            "delays_over_900_seconds": sum(value > 900 for value in delays),
            "positive_node_delay_count": sum(value > 0 for value in node_delays),
        })
        discrimination_rows.append({
            "run_id": run_id, "instance": row["instance"], "arm": row["arm"],
            "estimate_mode": data.get("global_gini_tree_child_estimate_mode"),
            "equal_estimate_pairs": equal_pairs,
            "discriminated_pairs": discriminated,
            "discrimination_fraction": discriminated / max(1, equal_pairs + discriminated),
            "child_estimate_failures": data.get("global_gini_tree_child_estimate_failures"),
        })
    write_rows(OUT / "round23_bottleneck_metrics.csv", bottleneck_rows)
    write_rows(OUT / "sibling_starvation_distribution.csv", sibling_rows)
    write_rows(OUT / "child_estimate_discrimination.csv", discrimination_rows)

    wins = Counter(row["hierarchy_winner"] for row in final_rows
                   if row["performance_eligible"])
    horizon_counts = Counter(row["budget_seconds"] for row in final_rows)
    plain_counterexamples = [row for row in final_rows
                             if row["performance_eligible"] and
                             row["hierarchy_winner"] == "plain"]
    strict_shared = sum(row["S0_strict"] == "True" and
                        row["plain_strict"] == "True" for row in exact_rows)
    strict_one_sided = sum((row["S0_strict"] == "True") !=
                           (row["plain_strict"] == "True") for row in exact_rows)
    report = f"""# Stable S0 versus plain reanalysis

This is a no-solve Round 23 analysis of immutable Round 22 evidence. Different
horizons are reported as repeated measurements, not new instances. There are
{len(comparison_ubs)} unique instances, {horizon_counts['900']} 900-second
pairs, {horizon_counts['1800']} 1,800-second pairs, and
{horizon_counts['3600']} selected 3,600-second pairs. There are
{strict_shared} shared-strict pairs and {strict_one_sided} one-sided-strict
pairs.

Every noncertified comparison was recomputed twice: once using the verified
plain incumbent as U for both arms, and once using the frozen common U in
`comparison_ub_manifest.csv`. AUC was recomputed from raw retained events;
arm-specific Round 22 normalized AUC values were not reused.

Under the fixed hierarchy and excluding the invalidated moderate4301 Round 22
S0 row, S0 wins {wins['S0']} pairs, plain wins {wins['plain']}, ties occur in
{wins['tie']}, and {wins['unavailable']} are unavailable. The non-anomalous
plain-over-S0 counterexamples are: {', '.join(row['stage'] + '/' + row['instance'] for row in plain_counterexamples) or 'none'}.

The tested evidence supports comparative statements only for these retained
instances, horizons, executable, and manifests. It does not prove universal
dominance. Rows with large remaining common-UB gaps remain far from exact
closure even when S0 has the stronger final lower bound. Moderate4301 is
correctness-resolved by Round 23 live gates, but its contradictory Round 22 S0
900-second row remains excluded rather than retroactively repaired.
"""
    (OUT / "stable_s0_vs_plain_reanalysis.md").write_text(report, encoding="utf-8")

    bottlenecks = Counter(row["dominant_observed_bottleneck"] for row in bottleneck_rows)
    all_delay_seconds: list[float] = []
    all_delay_nodes: list[float] = []
    for item in sibling_rows:
        if finite(item["delay_seconds_max"]):
            all_delay_seconds.append(float(item["delay_seconds_max"]))
        if finite(item["delay_nodes_max"]):
            all_delay_nodes.append(float(item["delay_nodes_max"]))
    synthesis = f"""# Round 23 retained search-bottleneck synthesis

This synthesis uses only Round 22 dense trajectories, node/topology/sibling
traces, post-row traces, native JSONs, and logs. It excludes the anomalous
moderate4301 performance row.

The dominant per-run classifications are {dict(bottlenecks)}. Sibling delay is
present in both wall time and processed-node count: the maximum retained
per-run wall delay is {max(all_delay_seconds, default=0.0):.17g} seconds and
the maximum processed-node delay is {max(all_delay_nodes, default=0.0):.17g}.
Parent-copy creates no proved estimate lift, so equal estimates and native
best-bound tie behavior can compound starvation. Ordinary B&B growth,
simplex work, and late stagnation remain secondary or mixed signals.

Mechanism ranking under the preregistered criteria:

1. P1 would directly target starvation, but the CPLEX 22.1.1 generic callback
   exposes high-level branch/prune operations, not supported open-node
   enumeration and next-node selection. The documented selector is a legacy
   NodeCallback, so P1 requires an incomplete and forbidden callback migration.
2. P2 is a uniform, model-size-free child estimate derived from a proved
   dispersion/deviation inequality. It changes neither rows, bounds,
   objective, branching, nor pruning and is therefore the lower-risk supported
   candidate if its proof and exhaustive tests pass.
"""
    (OUT / "round23_bottleneck_synthesis.md").write_text(
        synthesis, encoding="utf-8")
    print(json.dumps({
        "unique_instances": len(comparison_ubs),
        "pair_winners": dict(wins),
        "bottleneck_rows": len(bottleneck_rows),
        "bottleneck_classes": dict(bottlenecks),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
