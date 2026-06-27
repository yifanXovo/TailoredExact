#!/usr/bin/env python3
"""Summarize the paper-candidate relaxation round.

This script intentionally reports negative outcomes.  It compares the new
adaptive-portfolio rows against the best valid rows from the previous
relaxation-closure round and writes compact CSVs used by the round report.
"""

from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "paper_candidate_relaxation_round"
RAW = OUT / "raw"
PREV = ROOT / "results" / "relaxation_closure_round"


V20_CASES = [
    "high_imbalance_seed3201",
    "high_imbalance_seed3202",
    "tight_T_seed3101",
    "tight_T_seed3102",
    "moderate_seed3301",
    "moderate_seed3302",
]


def safe_float(value, default=math.inf):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_str(value):
    return "" if value is None else str(value)


def infer_case(name: str) -> str:
    text = name.replace("\\", "/")
    base = Path(text).stem
    if base.endswith(".trace"):
        base = base[:-6]
    for case in V20_CASES:
        if case in base:
            return case
    if "v12_m1" in base:
        return "v12_m1"
    if "v12_m2" in base:
        return "v12_m2"
    if "v4" in base:
        return "v4"
    return base


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def raw_rows():
    rows = []
    for path in sorted(RAW.glob("*.json")):
        if path.name.endswith(".trace.json"):
            continue
        j = load_json(path)
        variant = path.stem
        case = infer_case(variant)
        rows.append(
            {
                "instance": safe_str(j.get("instance")) or case,
                "case": case,
                "instance_scope": safe_str(j.get("instance_scope"))
                or ("hard_generated_v20_m3" if case in V20_CASES else "regenerated_engineering"),
                "variant": variant,
                "status": safe_str(j.get("status")),
                "objective": safe_str(j.get("objective")),
                "lower_bound": safe_str(j.get("lower_bound")),
                "upper_bound": safe_str(j.get("upper_bound")),
                "gap": safe_str(j.get("gap")),
                "runtime_seconds": safe_str(j.get("runtime_seconds")),
                "certified_original_problem": safe_str(j.get("certified_original_problem")),
                "verifier_passed": safe_str(j.get("verifier_passed")),
                "unresolved_intervals": safe_str(j.get("unresolved_intervals")),
                "invalid_bound_intervals": safe_str(j.get("invalid_bound_intervals")),
                "open_nodes": safe_str(j.get("open_nodes")),
                "bound_time_seconds": safe_str(j.get("bound_time_seconds")),
                "pricing_time_seconds": safe_str(j.get("pricing_time_seconds")),
                "master_time_seconds": safe_str(j.get("master_time_seconds")),
                "large_compact_flow_relaxation": safe_str(j.get("large_compact_flow_relaxation")),
                "relaxation_portfolio_mode": safe_str(j.get("relaxation_portfolio_mode")),
                "relaxation_variants_tried": safe_str(j.get("relaxation_variants_tried")),
                "selected_relaxation_variant": safe_str(j.get("selected_relaxation_variant")),
                "selected_variant_reason": safe_str(j.get("selected_variant_reason")),
                "best_variant_bound": safe_str(j.get("best_variant_bound")),
                "variant_bound_improvement": safe_str(j.get("variant_bound_improvement")),
                "variants_skipped_reason": safe_str(j.get("variants_skipped_reason")),
                "large_compact_flow_connectivity_enabled": safe_str(j.get("large_compact_flow_connectivity_enabled")),
                "service_operation_min_handling_cuts_added": safe_str(j.get("service_operation_min_handling_cuts_added")),
                "penalty_movement_lb_cuts_added": safe_str(j.get("penalty_movement_lb_cuts_added")),
                "transfer_subset_capacity_cuts_added": safe_str(j.get("transfer_subset_capacity_cuts_added")),
                "v20_cover_cuts_added": safe_str(j.get("v20_cover_cuts_added")),
                "station_residual_cover_cuts_added": safe_str(j.get("station_residual_cover_cuts_added")),
                "route_mask_all_subset_enumeration_certifying": safe_str(j.get("route_mask_all_subset_enumeration_certifying")),
                "result_file": str(path),
            }
        )
    return rows


def previous_best_rows():
    rows = []
    path = PREV / "summary.csv"
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                variant = safe_str(r.get("variant"))
                result_file = safe_str(r.get("result_file"))
                case = infer_case(variant or result_file)
                rows.append({**r, "case": case})

    best = {}
    for r in rows:
        case = r["case"]
        if case not in V20_CASES and case not in {"v12_m1", "v12_m2"}:
            continue
        gap = safe_float(r.get("gap"))
        runtime = safe_float(r.get("runtime_seconds"))
        certified = safe_str(r.get("certified_original_problem")).lower() == "true"
        key = (0 if certified else 1, gap, runtime)
        if case not in best or key < best[case][0]:
            best[case] = (key, r)

    fixed = {
        "v12_m1": {
            "case": "v12_m1",
            "instance": "regen_candidate_V12_M1_average",
            "instance_scope": "regenerated_engineering",
            "best_previous_variant": "v12_m1_current_300s / v12_m1_default_600s",
            "best_previous_LB": "0.332675660948",
            "UB": "0.357200583208",
            "best_previous_gap": "0.0686586848205",
            "runtime": "300.8282635",
            "relaxation_mode": "paper-core baseline",
            "certified": "False at 300s; True in 600s row",
            "controlling_interval_ids": "",
        },
        "v12_m2": {
            "case": "v12_m2",
            "instance": "regen_candidate_V12_M2_average",
            "instance_scope": "regenerated_engineering",
            "best_previous_variant": "canonical paper-core 300s",
            "best_previous_LB": "0.718504070755",
            "UB": "0.718504070755",
            "best_previous_gap": "0",
            "runtime": "205.628",
            "relaxation_mode": "paper-core relaxation-only",
            "certified": "True",
            "controlling_interval_ids": "",
        },
    }

    out = []
    for case in ["v12_m1", "v12_m2"] + V20_CASES:
        if case in fixed:
            out.append(fixed[case])
            continue
        r = best.get(case, (None, {}))[1]
        out.append(
            {
                "case": case,
                "instance": case,
                "instance_scope": "hard_generated_v20_m3",
                "best_previous_variant": safe_str(r.get("variant")),
                "best_previous_LB": safe_str(r.get("lower_bound")),
                "UB": safe_str(r.get("upper_bound")),
                "best_previous_gap": safe_str(r.get("gap")),
                "runtime": safe_str(r.get("runtime_seconds")),
                "relaxation_mode": safe_str(r.get("large_compact_flow_relaxation")),
                "certified": safe_str(r.get("certified_original_problem")),
                "controlling_interval_ids": "",
            }
        )
    return out


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        keys = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fields = keys
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def v12_scheduling(rows):
    return [r for r in rows if r["case"] in {"v12_m1", "v12_m2", "v4"}]


def v20_rows(rows):
    return [r for r in rows if r["case"] in V20_CASES]


def cover_rows(rows):
    out = []
    for r in v20_rows(rows):
        out.append(
            {
                "instance": r["case"],
                "variant": r["variant"],
                "v20_cover_cuts_added": r["v20_cover_cuts_added"],
                "station_residual_cover_cuts_added": r["station_residual_cover_cuts_added"],
                "service_operation_min_handling_cuts_added": r["service_operation_min_handling_cuts_added"],
                "penalty_movement_lb_cuts_added": r["penalty_movement_lb_cuts_added"],
                "transfer_subset_capacity_cuts_added": r["transfer_subset_capacity_cuts_added"],
                "large_compact_flow_connectivity_enabled": r["large_compact_flow_connectivity_enabled"],
                "gap": r["gap"],
                "notes": "valid but not selected as a paper-core default; adaptive/default mix did not beat previous best fixed LP/mip-light rows",
            }
        )
    return out


def compare_to_previous(rows, previous):
    prev = {r["case"]: r for r in previous}
    out = []
    for r in rows:
        case = r["case"]
        p = prev.get(case, {})
        prev_gap = safe_float(p.get("best_previous_gap"))
        new_gap = safe_float(r.get("gap"))
        out.append(
            {
                **r,
                "previous_best_gap": "" if math.isinf(prev_gap) else f"{prev_gap:.12g}",
                "gap_delta_vs_previous": "" if math.isinf(prev_gap) or math.isinf(new_gap) else f"{new_gap - prev_gap:.12g}",
                "improved_vs_previous_best": "" if math.isinf(prev_gap) or math.isinf(new_gap) else str(new_gap < prev_gap - 1e-9),
            }
        )
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = raw_rows()
    target_cases = {"v4", "v12_m1", "v12_m2", *V20_CASES}
    target_rows = [r for r in rows if r["case"] in target_cases]
    prev = previous_best_rows()
    write_csv(OUT / "baseline_best_by_instance.csv", prev)
    write_csv(OUT / "summary.csv", compare_to_previous(target_rows, prev))
    write_csv(OUT / "v12_m1_scheduling_ablation.csv", compare_to_previous(v12_scheduling(target_rows), prev))
    write_csv(OUT / "variant_selector_trace.csv", compare_to_previous(v20_rows(target_rows), prev))
    write_csv(OUT / "cover_cut_activity.csv", cover_rows(target_rows))
    write_csv(OUT / "cache_parallel_ablation.csv", [
        {
            "instance": "v12_m1",
            "variant": "previous_round_parallel2_300s",
            "source": str(PREV / "cache_parallel_ablation.csv"),
            "result": "No improvement over 1-worker baseline; this round did not make parallelism the main path.",
        }
    ])
    write_csv(OUT / "bpc_fallback_retest.csv", [
        {
            "instance": "v12_m1",
            "variant": "previous_round_bpc_fallback_300s",
            "source": str(PREV / "bpc_fallback_retest.csv"),
            "result": "Fallback launched a small tree but weakened final LB by displacing relaxation time.",
        },
        {
            "instance": "v20_m3",
            "variant": "previous_round_selected_fallback_rows",
            "source": str(PREV / "bpc_fallback_retest.csv"),
            "result": "Fallback did not improve interval lower bounds; remains diagnostic/off by default.",
        },
    ])


if __name__ == "__main__":
    main()
