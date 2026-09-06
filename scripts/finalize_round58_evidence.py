#!/usr/bin/env python3
"""Finalize compact evidence, route witnesses, and analysis for Round 58."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

import round58_common as r58
import run_round58_paired_benchmark as runner
from round58_route_archive import archive_native_result, object_json


OUT = r58.EVIDENCE
HORIZONS = (3600, 10800, 16200, 21600)


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def as_float(value: Any) -> float | None:
    return float(value) if finite(value) else None


def ratio(left: Any, right: Any) -> float | None:
    if not finite(left) or not finite(right) or float(right) == 0.0:
        return None
    return float(left) / float(right)


def shifted_ratio(values: Iterable[tuple[Any, Any]]) -> float | None:
    pairs = [(float(left), float(right)) for left, right in values
             if finite(left) and finite(right)]
    if not pairs:
        return None
    return math.exp(statistics.fmean(
        math.log((left + 1.0) / (right + 1.0)) for left, right in pairs))


def shifted_geomean(values: Iterable[Any]) -> float | None:
    material = [float(value) for value in values if finite(value)]
    if not material:
        return None
    return math.exp(statistics.fmean(math.log(value + 1.0)
                                     for value in material)) - 1.0


def mean(values: Iterable[Any]) -> float | None:
    material = [float(value) for value in values if finite(value)]
    return statistics.fmean(material) if material else None


def panel() -> list[dict[str, str]]:
    return runner.panel()


def summaries(row: dict[str, str], method: str) -> list[dict[str, Any]]:
    material = []
    for cap in HORIZONS:
        summary = runner.marker_summary(row, method, cap)
        if summary:
            material.append(summary)
    return material


def official(row: dict[str, str], method: str) -> dict[str, Any]:
    material = summaries(row, method)
    if not material:
        raise RuntimeError(f"no official result: {row['scenario_id']}/{method}")
    return max(material, key=lambda value: int(value["process_cap_seconds"]))


def first_certificate(row: dict[str, str], method: str) -> dict[str, Any] | None:
    for value in summaries(row, method):
        if value["strict_certificate"]:
            return value
    return None


def common_cap(row: dict[str, str]) -> int:
    k = {int(value["process_cap_seconds"]) for value in summaries(row, "k1_am_sf")}
    p = {int(value["process_cap_seconds"]) for value in summaries(row, "pgrb")}
    common = k & p
    if 3600 not in common:
        raise RuntimeError(f"missing mandatory common screen: {row['scenario_id']}")
    return max(common)


def noncertified_bound_outcome(k1: dict[str, Any],
                               pgrb: dict[str, Any]) -> str:
    comparisons: list[int] = []
    for left, right, larger_is_better in (
            (k1.get("valid_lower_bound"), pgrb.get("valid_lower_bound"), True),
            (k1.get("verified_upper_bound"), pgrb.get("verified_upper_bound"), False),
            (k1.get("relative_gap"), pgrb.get("relative_gap"), False),
            (k1.get("scaled_gap"), pgrb.get("scaled_gap"), False)):
        if not finite(left) or not finite(right):
            continue
        tolerance = 1e-10 * max(1.0, abs(float(left)), abs(float(right)))
        difference = float(left) - float(right)
        if abs(difference) <= tolerance:
            comparisons.append(0)
        elif (difference > 0) == larger_is_better:
            comparisons.append(1)
        else:
            comparisons.append(-1)
    if len(comparisons) < 2:
        return "invalid_pair"
    if all(value >= 0 for value in comparisons) and any(
            value > 0 for value in comparisons):
        return "neither_certified_k1_better_bound"
    if all(value <= 0 for value in comparisons) and any(
            value < 0 for value in comparisons):
        return "neither_certified_pgrb_better_bound"
    return "neither_certified_mixed"


def pair_outcome(row: dict[str, str]) -> str:
    k, p = official(row, "k1_am_sf"), official(row, "pgrb")
    ck, cp = bool(k["strict_certificate"]), bool(p["strict_certificate"])
    if ck and cp:
        kt, pt = first_certificate(row, "k1_am_sf"), first_certificate(row, "pgrb")
        assert kt and pt
        left, right = float(kt["actual_wall_time_seconds"]), float(pt["actual_wall_time_seconds"])
        if abs(left - right) <= 1e-6:
            return "both_certified_tie"
        return "both_certified_k1_faster" if left < right else "both_certified_pgrb_faster"
    if ck:
        return "k1_only_certified"
    if cp:
        return "pgrb_only_certified"
    cap = common_cap(row)
    common_k = runner.marker_summary(row, "k1_am_sf", cap)
    common_p = runner.marker_summary(row, "pgrb", cap)
    assert common_k and common_p
    return noncertified_bound_outcome(common_k, common_p)


def result_path(summary: dict[str, Any]) -> Path:
    return r58.ROOT / summary["result_path"]


def trace_rows(summary: dict[str, Any]) -> list[dict[str, str]]:
    directory = result_path(summary).parent
    if summary["method"] == "k1_am_sf":
        path = directory / "external" / "global_bound_trace.csv"
    else:
        path = directory / "progress.csv"
    return r58.read_csv(path) if path.is_file() else []


def checkpoint(summary: dict[str, Any], horizon: int) -> dict[str, Any]:
    final_wall = as_float(summary.get("actual_wall_time_seconds"))
    carried = final_wall is not None and final_wall <= horizon
    if carried:
        return {
            "checkpoint_seconds": horizon, "checkpoint_source": "completed_run_carry_forward",
            "strict_certificate": bool(summary["strict_certificate"]),
            "valid_lower_bound": summary.get("valid_lower_bound"),
            "verified_upper_bound": summary.get("verified_upper_bound"),
            "absolute_gap": summary.get("absolute_gap"),
            "relative_gap": summary.get("relative_gap"),
            "scaled_gap": summary.get("scaled_gap"),
            "work": summary.get("gurobi_work"), "nodes": summary.get("nodes"),
        }
    rows = trace_rows(summary)
    selected: dict[str, str] | None = None
    time_field = ("process_elapsed_seconds" if summary["method"] == "k1_am_sf"
                  else "elapsed_runtime_seconds")
    for row in rows:
        if finite(row.get(time_field)) and float(row[time_field]) <= horizon:
            selected = row
    lower: float | None = None
    native_upper: float | None = None
    work: float | None = None
    nodes: float | None = None
    if selected:
        if summary["method"] == "k1_am_sf":
            lower = as_float(selected.get("valid_global_lower_bound"))
            native_upper = as_float(selected.get("verified_global_upper_bound"))
        else:
            lower = (as_float(selected.get("best_bound"))
                     if str(selected.get("best_bound_available", "")).lower() == "true"
                     else None)
            native_upper = (as_float(selected.get("incumbent"))
                            if str(selected.get("incumbent_available", "")).lower() == "true"
                            else None)
            work = as_float(selected.get("work"))
            nodes = as_float(selected.get("processed_nodes"))
    final_upper = as_float(summary.get("verified_upper_bound"))
    # A progress incumbent becomes a qualified checkpoint UB only when its
    # value equals the independently verified native final witness.
    upper = None
    if native_upper is not None and final_upper is not None and abs(
            native_upper - final_upper) <= 1e-6 * max(1.0, abs(final_upper)):
        upper = final_upper
    gaps = runner.explicit_gaps(lower, upper)
    return {
        "checkpoint_seconds": horizon,
        "checkpoint_source": "last_native_progress_at_or_before_checkpoint",
        "strict_certificate": False, "valid_lower_bound": lower,
        "verified_upper_bound": upper, **gaps, "work": work, "nodes": nodes,
    }


def checkpoint_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario in panel():
        for method in runner.METHODS:
            for summary in summaries(scenario, method):
                cap = int(summary["process_cap_seconds"])
                points = [value for value in (
                    (300, 1200, 3600) if cap == 3600 else
                    (3600, 7200, 10800) if cap == 10800 else
                    (3600, 7200, 10800, 16200) if cap == 16200 else
                    (3600, 7200, 10800, 16200, 21600)) if value <= cap]
                for point in points:
                    value = checkpoint(summary, point)
                    rows.append({
                        "scenario_id": scenario["scenario_id"], "method": method,
                        "run_stage": summary["run_stage"], "run_cap_seconds": cap,
                        **value,
                    })
    return rows


def gap_integral(summary: dict[str, Any]) -> tuple[float | None, float]:
    """Return a stepwise relative-gap integral over qualified trace segments."""
    final_upper = as_float(summary.get("verified_upper_bound"))
    events: list[tuple[float, float]] = []
    for row in trace_rows(summary):
        if summary["method"] == "k1_am_sf":
            elapsed = as_float(row.get("process_elapsed_seconds"))
            lower = as_float(row.get("valid_global_lower_bound"))
            native_upper = as_float(row.get("verified_global_upper_bound"))
        else:
            elapsed = as_float(row.get("elapsed_runtime_seconds"))
            lower = (as_float(row.get("best_bound"))
                     if str(row.get("best_bound_available", "")).lower() == "true"
                     else None)
            native_upper = (as_float(row.get("incumbent"))
                            if str(row.get("incumbent_available", "")).lower() == "true"
                            else None)
        if not all(value is not None for value in (elapsed, lower, native_upper,
                                                   final_upper)):
            continue
        if abs(native_upper - final_upper) > 1e-6 * max(1.0, abs(final_upper)):
            continue
        gap = runner.explicit_gaps(lower, final_upper)["relative_gap"]
        if gap is not None:
            events.append((elapsed, gap))
    final_time = as_float(summary.get("actual_wall_time_seconds"))
    final_gap = as_float(summary.get("relative_gap"))
    if final_time is not None and final_gap is not None:
        events.append((final_time, final_gap))
    events = sorted(set(events))
    if not events:
        return None, 0.0
    end = final_time if final_time is not None else float(summary["process_cap_seconds"])
    integral = 0.0
    for index, (elapsed, value) in enumerate(events):
        next_time = events[index + 1][0] if index + 1 < len(events) else end
        if next_time > elapsed:
            integral += value * (next_time - elapsed)
    coverage = max(0.0, end - events[0][0])
    return integral, coverage


def official_rows() -> list[dict[str, Any]]:
    rows = []
    for scenario in panel():
        for method in runner.METHODS:
            value = official(scenario, method)
            certificate = first_certificate(scenario, method)
            rows.append({
                "scenario_id": scenario["scenario_id"], "dataset_family": r58.DATASET_FAMILY,
                "panel_class": scenario["panel_class"], "V": int(scenario["V"]),
                "geographic_regime": scenario["geographic_regime"],
                "inventory_regime": scenario["inventory_regime"],
                "replicate": int(scenario["replicate"]), "M": int(scenario["M"]),
                "Q": int(scenario["Q"]), "T": int(scenario["T_seconds"]),
                "method": method, "official_run_stage": value["run_stage"],
                "official_authorized_cap_seconds": value["process_cap_seconds"],
                "official_algorithm_wall_time": value["actual_wall_time_seconds"],
                "official_algorithm_work": value["gurobi_work"],
                "strict_certificate": value["strict_certificate"],
                "exact_certificate_time": (certificate["actual_wall_time_seconds"]
                                           if certificate else None),
                "exact_certificate_work": (certificate["gurobi_work"]
                                           if certificate else None),
                "certificate_authorized_cap_seconds": (
                    certificate["process_cap_seconds"] if certificate else None),
                "verified_incumbent_available": value["verified_incumbent_available"],
                "valid_lower_bound": value["valid_lower_bound"],
                "verified_upper_bound": value["verified_upper_bound"],
                "absolute_gap": value["absolute_gap"],
                "relative_gap": value["relative_gap"],
                "scaled_gap": value["scaled_gap"],
                "route_witness_available": value["verified_incumbent_available"],
                "native_status": value["native_status"],
                "result_path": value["result_path"],
                "result_sha256": value["result_sha256"],
                "run_identity_sha256": value["run_identity_sha256"],
                "official_selection_rule": "largest_authorized_cap_actually_entered",
                "fresh_run_time_not_summed": True,
            })
    return rows


def compute_rows() -> list[dict[str, Any]]:
    rows = []
    for scenario in panel():
        for method in runner.METHODS:
            material = summaries(scenario, method)
            selected = official(scenario, method)
            rows.append({
                "scenario_id": scenario["scenario_id"], "method": method,
                "attempt_count": len(material),
                "entered_caps_seconds": ";".join(str(value["process_cap_seconds"])
                                                   for value in material),
                "official_cap_seconds": selected["process_cap_seconds"],
                "official_algorithm_wall_time": selected["actual_wall_time_seconds"],
                "official_algorithm_work": selected["gurobi_work"],
                "total_experimental_compute_time": sum(
                    float(value["actual_wall_time_seconds"]) for value in material
                    if finite(value["actual_wall_time_seconds"])),
                "total_experimental_compute_work": sum(
                    float(value["gurobi_work"]) for value in material
                    if finite(value["gurobi_work"])),
                "screen_time_not_added_to_fresh_long_run": True,
            })
    return rows


def common_rows(checkpoints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = {(row["scenario_id"], row["method"], row["run_cap_seconds"],
              row["checkpoint_seconds"]): row for row in checkpoints}
    rows = []
    for scenario in panel():
        for cap in HORIZONS:
            if not (runner.marker_summary(scenario, "k1_am_sf", cap) and
                    runner.marker_summary(scenario, "pgrb", cap)):
                continue
            k = index.get((scenario["scenario_id"], "k1_am_sf", cap, cap))
            p = index.get((scenario["scenario_id"], "pgrb", cap, cap))
            if not k or not p:
                continue
            k_summary = runner.marker_summary(scenario, "k1_am_sf", cap)
            p_summary = runner.marker_summary(scenario, "pgrb", cap)
            assert k_summary and p_summary
            k_integral, k_coverage = gap_integral(k_summary)
            p_integral, p_coverage = gap_integral(p_summary)
            if k["strict_certificate"] and p["strict_certificate"]:
                left = float(k_summary["actual_wall_time_seconds"])
                right = float(p_summary["actual_wall_time_seconds"])
                classification = ("both_certified_tie" if abs(left - right) <= 1e-6
                                  else "both_certified_k1_faster" if left < right
                                  else "both_certified_pgrb_faster")
            elif k["strict_certificate"]:
                classification = "k1_only_certified"
            elif p["strict_certificate"]:
                classification = "pgrb_only_certified"
            else:
                classification = noncertified_bound_outcome(k, p)
            rows.append({
                "scenario_id": scenario["scenario_id"], "common_run_cap_seconds": cap,
                "common_checkpoint_seconds": cap,
                "K1_certificate": k["strict_certificate"],
                "PGRB_certificate": p["strict_certificate"],
                "K1_valid_LB": k["valid_lower_bound"],
                "PGRB_valid_LB": p["valid_lower_bound"],
                "K1_verified_UB": k["verified_upper_bound"],
                "PGRB_verified_UB": p["verified_upper_bound"],
                "K1_relative_gap": k["relative_gap"],
                "PGRB_relative_gap": p["relative_gap"],
                "K1_scaled_gap": k["scaled_gap"],
                "PGRB_scaled_gap": p["scaled_gap"],
                "K1_work": k["work"], "PGRB_work": p["work"],
                "K1_relative_gap_integral": k_integral,
                "PGRB_relative_gap_integral": p_integral,
                "K1_gap_integral_coverage_seconds": k_coverage,
                "PGRB_gap_integral_coverage_seconds": p_coverage,
                "pair_classification_at_common_horizon": classification,
                "unequal_horizon_comparison": False,
            })
    return rows


def repeatability_rows(checkpoints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = {(row["scenario_id"], row["method"], row["run_cap_seconds"],
              row["checkpoint_seconds"]): row for row in checkpoints}
    rows = []
    for scenario in panel():
        for method in runner.METHODS:
            if not runner.marker_summary(scenario, method, 10800):
                continue
            screen = index[(scenario["scenario_id"], method, 3600, 3600)]
            long = index[(scenario["scenario_id"], method, 10800, 3600)]
            cert_diff = bool(screen["strict_certificate"]) != bool(long["strict_certificate"])
            lb_diff = (abs(float(screen["valid_lower_bound"]) -
                           float(long["valid_lower_bound"]))
                       if finite(screen["valid_lower_bound"]) and
                       finite(long["valid_lower_bound"]) else None)
            ub_diff = (abs(float(screen["verified_upper_bound"]) -
                           float(long["verified_upper_bound"]))
                       if finite(screen["verified_upper_bound"]) and
                       finite(long["verified_upper_bound"]) else None)
            gap_diff = (abs(float(screen["relative_gap"]) -
                            float(long["relative_gap"]))
                        if finite(screen["relative_gap"]) and
                        finite(long["relative_gap"]) else None)
            material = cert_diff or any(
                value is not None and value > threshold for value, threshold in
                ((lb_diff, 1e-5), (ub_diff, 1e-5), (gap_diff, 0.01)))
            rows.append({
                "scenario_id": scenario["scenario_id"], "method": method,
                "screen_certificate": screen["strict_certificate"],
                "long_3600_checkpoint_certificate": long["strict_certificate"],
                "absolute_LB_difference": lb_diff, "absolute_UB_difference": ub_diff,
                "absolute_relative_gap_difference": gap_diff,
                "material_repeatability_difference": material,
                "classification": "MATERIAL_DIFFERENCE" if material else "PASS",
            })
    return rows


def direct_rows() -> list[dict[str, Any]]:
    rows = []
    for scenario in panel():
        k, p = official(scenario, "k1_am_sf"), official(scenario, "pgrb")
        ks, ps = runner.marker_summary(scenario, "k1_am_sf", 3600), runner.marker_summary(
            scenario, "pgrb", 3600)
        kl, pl = runner.marker_summary(scenario, "k1_am_sf", 10800), runner.marker_summary(
            scenario, "pgrb", 10800)
        kc, pc = first_certificate(scenario, "k1_am_sf"), first_certificate(
            scenario, "pgrb")
        outcome = pair_outcome(scenario)
        common = common_cap(scenario)
        k_integral, k_integral_coverage = gap_integral(
            runner.marker_summary(scenario, "k1_am_sf", common))
        p_integral, p_integral_coverage = gap_integral(
            runner.marker_summary(scenario, "pgrb", common))
        rows.append({
            "scenario_id": scenario["scenario_id"],
            "dataset_family": r58.DATASET_FAMILY,
            "panel_class": scenario["panel_class"],
            "V": int(scenario["V"]), "geographic_regime": scenario["geographic_regime"],
            "inventory_regime": scenario["inventory_regime"],
            "replicate": int(scenario["replicate"]), "M": int(scenario["M"]),
            "fleet_density_V_over_M": int(scenario["V"]) / int(scenario["M"]),
            "Q": int(scenario["Q"]), "T": int(scenario["T_seconds"]),
            "K1_certificate_3600": ks["strict_certificate"],
            "PGRB_certificate_3600": ps["strict_certificate"],
            "K1_certificate_10800": kl["strict_certificate"] if kl else None,
            "PGRB_certificate_10800": pl["strict_certificate"] if pl else None,
            "K1_final_cap_seconds": k["process_cap_seconds"],
            "PGRB_final_cap_seconds": p["process_cap_seconds"],
            "K1_final_status": k["native_status"],
            "PGRB_final_status": p["native_status"],
            "K1_final_certificate": k["strict_certificate"],
            "PGRB_final_certificate": p["strict_certificate"],
            "K1_official_algorithm_wall_time": k["actual_wall_time_seconds"],
            "PGRB_official_algorithm_wall_time": p["actual_wall_time_seconds"],
            "K1_official_algorithm_work": k["gurobi_work"],
            "PGRB_official_algorithm_work": p["gurobi_work"],
            "K1_exact_time": kc["actual_wall_time_seconds"] if kc else None,
            "PGRB_exact_time": pc["actual_wall_time_seconds"] if pc else None,
            "K1_exact_work": kc["gurobi_work"] if kc else None,
            "PGRB_exact_work": pc["gurobi_work"] if pc else None,
            "exact_time_ratio_K1_over_PGRB": ratio(
                kc["actual_wall_time_seconds"] if kc else None,
                pc["actual_wall_time_seconds"] if pc else None),
            "exact_work_ratio_K1_over_PGRB": ratio(
                kc["gurobi_work"] if kc else None,
                pc["gurobi_work"] if pc else None),
            "K1_valid_LB": k["valid_lower_bound"], "PGRB_valid_LB": p["valid_lower_bound"],
            "K1_verified_UB": k["verified_upper_bound"],
            "PGRB_verified_UB": p["verified_upper_bound"],
            "K1_absolute_gap": k["absolute_gap"], "PGRB_absolute_gap": p["absolute_gap"],
            "K1_relative_gap": k["relative_gap"], "PGRB_relative_gap": p["relative_gap"],
            "K1_scaled_gap": k["scaled_gap"], "PGRB_scaled_gap": p["scaled_gap"],
            "K1_route_witness": k["verified_incumbent_available"],
            "PGRB_route_witness": p["verified_incumbent_available"],
            "largest_common_authorized_cap_seconds": common,
            "K1_common_horizon_relative_gap_integral": k_integral,
            "PGRB_common_horizon_relative_gap_integral": p_integral,
            "K1_gap_integral_coverage_seconds": k_integral_coverage,
            "PGRB_gap_integral_coverage_seconds": p_integral_coverage,
            "unequal_final_horizons": k["process_cap_seconds"] != p["process_cap_seconds"],
            "pair_outcome": outcome,
            "censoring_status": ("none" if k["strict_certificate"] and p["strict_certificate"]
                                 else "at_least_one_method_censored"),
        })
    return rows


def regression_rows(direct: list[dict[str, Any]],
                    common: list[dict[str, Any]]) -> tuple[list[dict[str, Any]],
                                                           list[dict[str, Any]]]:
    common_latest: dict[str, dict[str, Any]] = {}
    for row in common:
        if (row["scenario_id"] not in common_latest or
                row["common_run_cap_seconds"] > common_latest[row["scenario_id"]][
                    "common_run_cap_seconds"]):
            common_latest[row["scenario_id"]] = row
    historical, long_material = [], []
    for row in direct:
        scenario_id = row["scenario_id"]
        both = row["K1_final_certificate"] and row["PGRB_final_certificate"]
        reasons = []
        if both:
            wr = row["exact_work_ratio_K1_over_PGRB"]
            tr = row["exact_time_ratio_K1_over_PGRB"]
            if (finite(wr) and float(wr) > 1.5 and
                    float(row["K1_exact_work"]) - float(row["PGRB_exact_work"]) > 50):
                reasons.append("both_certified_work_regression")
            if (finite(tr) and float(tr) > 1.5 and
                    float(row["K1_exact_time"]) - float(row["PGRB_exact_time"]) > 60):
                reasons.append("both_certified_time_regression")
        else:
            value = common_latest[scenario_id]
            if value["PGRB_certificate"] and not value["K1_certificate"]:
                reasons.append("pgrb_certified_k1_not_at_common_horizon")
            kg, pg = value["K1_relative_gap"], value["PGRB_relative_gap"]
            if (finite(kg) and finite(pg) and float(pg) > 0 and
                    float(kg) / float(pg) > 1.5 and float(kg) - float(pg) >= 0.05):
                reasons.append("k1_common_gap_regression")
        historical.append({
            "scenario_id": scenario_id, "severe_regression": bool(reasons),
            "reasons": ";".join(reasons) or "none", "definition": "round58_historical",
        })

        long_reasons = []
        if (row["PGRB_final_certificate"] and not row["K1_final_certificate"] and
                int(row["K1_final_cap_seconds"]) >= int(row["PGRB_final_cap_seconds"])):
            long_reasons.append("pgrb_certified_k1_not_same_or_greater_horizon")
        if (both and finite(row["exact_time_ratio_K1_over_PGRB"]) and
                float(row["exact_time_ratio_K1_over_PGRB"]) > 1.5 and
                float(row["K1_exact_time"]) - float(row["PGRB_exact_time"]) > 600):
            long_reasons.append("both_certified_long_time_regression")
        scenario = next(value for value in panel() if value["scenario_id"] == scenario_id)
        k108 = runner.marker_summary(scenario, "k1_am_sf", 10800)
        p108 = runner.marker_summary(scenario, "pgrb", 10800)
        if (k108 and p108 and not k108["strict_certificate"] and
                not p108["strict_certificate"] and finite(k108["relative_gap"]) and
                finite(p108["relative_gap"]) and
                float(k108["relative_gap"]) - float(p108["relative_gap"]) >= 0.10):
            long_reasons.append("k1_10800_relative_gap_excess")
        long_material.append({
            "scenario_id": scenario_id,
            "long_run_material_regression": bool(long_reasons),
            "reasons": ";".join(long_reasons) or "none",
            "definition": "round58_long_run_material",
        })
    return historical, long_material


def route_archives(official_material: list[dict[str, Any]]) -> tuple[
        list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    inventory, verification, timing = [], [], []
    for row in official_material:
        if not row["verified_incumbent_available"]:
            inventory.append({
                "scenario_id": row["scenario_id"], "method": row["method"],
                "package_available": False, "reason": "no_verified_incumbent",
            })
            verification.append({
                "scenario_id": row["scenario_id"], "method": row["method"],
                "passed": False, "failures": "no_verified_incumbent",
                "objective": None,
                "archive_time_excluded_from_algorithm_time": True,
                "optimization_or_repair_performed": False,
                "verification_status": "not_applicable_no_incumbent",
            })
            timing.append({
                "scenario_id": row["scenario_id"], "method": row["method"],
                "official_algorithm_wall_time": row["official_algorithm_wall_time"],
                "route_archive_seconds": 0.0,
                "archive_time_in_algorithm_time": False,
                "timing_status": "not_entered_no_incumbent",
            })
            continue
        archive = archive_native_result(
            row["scenario_id"], row["method"], r58.ROOT / row["result_path"],
            runner.SOURCE_FREEZE, runner.EXE_SHA256)
        output = r58.ROOT / archive["package_path"]
        audit = object_json(output / "solution_verification.json")
        inventory.append({
            "scenario_id": row["scenario_id"], "method": row["method"],
            "package_available": True, "package_path": archive["package_path"],
            "certificate_label": ("certified_optimal_witness" if row["strict_certificate"]
                                  else "noncertified_best_verified_incumbent"),
            "file_count": 6, "solution_sha256_manifest": r58.repo_path(
                output / "solution_sha256.txt"), "route_post_optimization": False,
        })
        verification.append({
            "scenario_id": row["scenario_id"], "method": row["method"],
            "passed": audit["passed"], "failures": ";".join(audit["failures"]),
            "objective": audit["objective"],
            "archive_time_excluded_from_algorithm_time": True,
            "optimization_or_repair_performed": False,
        })
        timing.append({
            "scenario_id": row["scenario_id"], "method": row["method"],
            "official_algorithm_wall_time": row["official_algorithm_wall_time"],
            "route_archive_seconds": audit["archive_materialization_seconds"],
            "archive_time_in_algorithm_time": False,
        })
    return inventory, verification, timing


def certificate_audits(official_material: list[dict[str, Any]],
                       route_verification: list[dict[str, Any]]) -> tuple[
                           list[dict[str, Any]], list[dict[str, Any]]]:
    verified = {(row["scenario_id"], row["method"]): bool(row["passed"])
                for row in route_verification}
    rows = []
    false_count = 0
    for row in official_material:
        strict = bool(row["strict_certificate"])
        route_ok = verified.get((row["scenario_id"], row["method"]), False)
        gap_ok = (finite(row["absolute_gap"]) and float(row["absolute_gap"]) <=
                  1e-6 * max(1.0, abs(float(row["verified_upper_bound"]))))
        false = strict and not (route_ok and gap_ok)
        false_count += int(false)
        rows.append({
            "scenario_id": row["scenario_id"], "method": row["method"],
            "strict_certificate": strict, "independent_route_verification": route_ok,
            "qualified_gap_closed": gap_ok, "false_certificate": false,
            "certificate_audit_status": "FAIL" if false else "PASS",
        })
    false_rows = [{
        "audit_scope": "all_official_final_results", "official_row_count": len(rows),
        "strict_certificate_count": sum(bool(row["strict_certificate"]) for row in rows),
        "false_certificate_count": false_count,
        "status": "PASS" if false_count == 0 else "FAIL",
    }]
    return rows, false_rows


def group_rows(direct: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in direct:
        groups[str(row[field])].append(row)
    rows = []
    for key, values in sorted(groups.items()):
        exact = [row for row in values if row["K1_final_certificate"] and
                 row["PGRB_final_certificate"]]
        outcomes = Counter(row["pair_outcome"] for row in values)
        rows.append({
            field: key, "scenario_count": len(values),
            "K1_final_certificate_count": sum(bool(row["K1_final_certificate"])
                                               for row in values),
            "PGRB_final_certificate_count": sum(bool(row["PGRB_final_certificate"])
                                                 for row in values),
            "both_certified_count": len(exact),
            "K1_faster_count": outcomes["both_certified_k1_faster"],
            "PGRB_faster_count": outcomes["both_certified_pgrb_faster"],
            "K1_only_count": outcomes["k1_only_certified"],
            "PGRB_only_count": outcomes["pgrb_only_certified"],
            "shifted_exact_time_ratio_K1_over_PGRB": shifted_ratio(
                (row["K1_exact_time"], row["PGRB_exact_time"]) for row in exact),
            "shifted_exact_work_ratio_K1_over_PGRB": shifted_ratio(
                (row["K1_exact_work"], row["PGRB_exact_work"]) for row in exact),
            "mean_K1_relative_gap": mean(row["K1_relative_gap"] for row in values),
            "mean_PGRB_relative_gap": mean(row["PGRB_relative_gap"] for row in values),
        })
    return rows


def horizon_summary() -> list[dict[str, Any]]:
    rows = []
    for horizon in HORIZONS:
        for method in runner.METHODS:
            entered = []
            certified = 0
            for scenario in panel():
                values = [value for value in summaries(scenario, method)
                          if int(value["process_cap_seconds"]) <= horizon]
                if values:
                    entered.append(scenario["scenario_id"])
                    certified += any(bool(value["strict_certificate"]) for value in values)
            rows.append({
                "horizon_seconds": horizon, "method": method,
                "scenario_count_in_panel": 50, "entered_by_horizon_count": len(entered),
                "strict_certificate_count": certified,
                "certificate_fraction_of_panel": certified / 50.0,
                "capped_unsolved_rows_not_assigned_solve_time": True,
            })
    return rows


def performance_rows(direct: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in direct:
        if not item["K1_final_certificate"] or not item["PGRB_final_certificate"]:
            continue
        best_time = min(float(item["K1_exact_time"]), float(item["PGRB_exact_time"]))
        best_work = min(float(item["K1_exact_work"]), float(item["PGRB_exact_work"]))
        for method, prefix in (("k1_am_sf", "K1"), ("pgrb", "PGRB")):
            rows.append({
                "scenario_id": item["scenario_id"], "method": method,
                "time_ratio_to_best": float(item[f"{prefix}_exact_time"]) / best_time,
                "work_ratio_to_best": (
                    float(item[f"{prefix}_exact_work"]) / best_work
                    if best_work > 0 else
                    1.0 if float(item[f"{prefix}_exact_work"]) == 0 else None),
                "shifted_work_ratio_to_best": (
                    (float(item[f"{prefix}_exact_work"]) + 1.0) /
                    (best_work + 1.0)),
                "profile_scope": "both_certified_only",
            })
    if not rows:
        rows.append({
            "scenario_id": "none", "method": "not_applicable",
            "time_ratio_to_best": None, "work_ratio_to_best": None,
            "shifted_work_ratio_to_best": None,
            "profile_scope": "no_both_certified_rows",
        })
    return rows


def final_classification(direct: list[dict[str, Any]],
                         common: list[dict[str, Any]],
                         long_regression: list[dict[str, Any]],
                         false_certificates: int,
                         correctness_failures: int) -> tuple[str, dict[str, Any]]:
    exact = [row for row in direct if row["K1_final_certificate"] and
             row["PGRB_final_certificate"]]
    k_cert = sum(bool(row["K1_final_certificate"]) for row in direct)
    p_cert = sum(bool(row["PGRB_final_certificate"]) for row in direct)
    time_ratio = shifted_ratio((row["K1_exact_time"], row["PGRB_exact_time"])
                               for row in exact)
    work_ratio = shifted_ratio((row["K1_exact_work"], row["PGRB_exact_work"])
                               for row in exact)
    common_latest: dict[str, dict[str, Any]] = {}
    for row in common:
        if (row["scenario_id"] not in common_latest or
                int(row["common_run_cap_seconds"]) > int(common_latest[
                    row["scenario_id"]]["common_run_cap_seconds"])):
            common_latest[row["scenario_id"]] = row
    common_gap_pairs = [row for row in common_latest.values()
                        if finite(row["K1_relative_gap"]) and
                        finite(row["PGRB_relative_gap"])]
    k_gaps = [float(row["K1_relative_gap"]) for row in common_gap_pairs]
    p_gaps = [float(row["PGRB_relative_gap"]) for row in common_gap_pairs]
    gap_nonworse = bool(k_gaps and p_gaps and statistics.fmean(k_gaps) <=
                        statistics.fmean(p_gaps) + 1e-12)
    long_count = sum(bool(row["long_run_material_regression"])
                     for row in long_regression)
    k_better_strata = set()
    for row in direct:
        if row["pair_outcome"] in {"both_certified_k1_faster", "k1_only_certified",
                                    "neither_certified_k1_better_bound"}:
            k_better_strata.update((f"V={row['V']}",
                                    f"geography={row['geographic_regime']}",
                                    f"inventory={row['inventory_regime']}"))
    supported = all((
        false_certificates == 0, correctness_failures == 0, k_cert >= p_cert,
        time_ratio is not None and time_ratio < 1.0,
        work_ratio is not None and work_ratio < 1.0,
        gap_nonworse, long_count == 0, len(k_better_strata) > 1,
    ))
    if supported:
        classification = "k1_am_sf_pgrb_advantage_supported"
    elif k_cert < p_cert or (
            time_ratio is not None and work_ratio is not None and
            time_ratio >= 1.0 and work_ratio >= 1.0) or long_count > 1:
        classification = "k1_am_sf_pgrb_advantage_not_supported"
    else:
        classification = "k1_am_sf_pgrb_advantage_mixed"
    return classification, {
        "false_certificate_count": false_certificates,
        "correctness_failure_count": correctness_failures,
        "K1_final_certificate_count": k_cert,
        "PGRB_final_certificate_count": p_cert,
        "both_certified_count": len(exact),
        "paired_exact_shifted_time_ratio_K1_over_PGRB": time_ratio,
        "paired_exact_shifted_work_ratio_K1_over_PGRB": work_ratio,
        "K1_paired_exact_shifted_time_geometric_mean": shifted_geomean(
            row["K1_exact_time"] for row in exact),
        "PGRB_paired_exact_shifted_time_geometric_mean": shifted_geomean(
            row["PGRB_exact_time"] for row in exact),
        "K1_paired_exact_shifted_work_geometric_mean": shifted_geomean(
            row["K1_exact_work"] for row in exact),
        "PGRB_paired_exact_shifted_work_geometric_mean": shifted_geomean(
            row["PGRB_exact_work"] for row in exact),
        "common_horizon_gap_nonworse_overall": gap_nonworse,
        "long_run_material_regression_count": long_count,
        "K1_better_strata": sorted(k_better_strata),
    }


def write_markdown(classification: str, metrics: dict[str, Any],
                   direct: list[dict[str, Any]], protocol: dict[str, Any],
                   repeatability: list[dict[str, Any]],
                   historical: list[dict[str, Any]]) -> None:
    outcomes = Counter(row["pair_outcome"] for row in direct)
    exact = [row for row in direct if row["K1_final_certificate"] and
             row["PGRB_final_certificate"]]
    k_work_better = sum(float(row["K1_exact_work"]) < float(row["PGRB_exact_work"])
                        for row in exact)
    text = f"""# Round 58 CitiBike443 paired benchmark

## Decision

The frozen benchmark classification is `{classification}`.

- Completion: `{metrics['completion_classification']}`.
- Dataset: `{metrics['dataset_classification']}`.
- Benchmark: `{classification}`.
- Runtime: `{metrics['runtime_classification']}`.
- Scale: `{metrics['scale_classification']}`.
- Routes: `{metrics['route_classification']}`.

The local `citibike443-regional-v1` family was regenerated and hash-validated before selection. The exact tested identifiers and parameters are frozen in `round58_complete_panel.csv`: a deterministic 50-scenario subset (30 structural and 20 matched route-horizon scenarios) of the 960-scenario family. The other 910 scenarios remained unopened reserves. Primary cells use the lower canonical landscape SHA-256, while each matched cell uses the other corresponding replicate under the frozen inventory rotation. Every V/geography/inventory/M/Q/T stratum required by the design is represented. No scenario was replaced after performance was observed, and K1-AM-SF was not tuned.

## Execution completeness

- Mandatory 3600-second arms completed: {protocol['completed_screen_arm_count']} / 100.
- Total fresh optimizer processes entered: {protocol['completed_run_count']}.
- Maximum entered process cap: {protocol['maximum_entered_cap_seconds']} seconds.
- K1 certificates by 3600 seconds: {metrics['K1_screen_certificate_count']} / 50.
- P-GRB certificates by 3600 seconds: {metrics['PGRB_screen_certificate_count']} / 50.
- Scenario pairs entering the 10800-second stage: {metrics['scenario_pairs_entering_10800']}.
- Rows entering 16200/21600 seconds: {metrics['rows_entering_16200']} / {metrics['rows_entering_21600']}.
- K1 final certificates: {metrics['K1_final_certificate_count']} / 50.
- P-GRB final certificates: {metrics['PGRB_final_certificate_count']} / 50.
- Both certified: {metrics['both_certified_count']} / 50.
- Among both-certified rows, K1 used less Work on {k_work_better} / {len(exact)}.
- Historical severe regressions: {sum(bool(row['severe_regression']) for row in historical)}.
- Long-run material regressions: {metrics['long_run_material_regression_count']}.
- False certificates / other correctness failures: {metrics['false_certificate_count']} / {metrics['correctness_failure_count']}.
- Required native route packages verified: {metrics['route_verified_count']} / {metrics['route_required_count']}.
- Material 3600-second fresh-rerun differences: {sum(bool(row['material_repeatability_difference']) for row in repeatability)}.
- Total experimental compute: {metrics['total_experimental_compute_time']} seconds and {metrics['total_experimental_compute_work']} Work units.

Every optimizer run used the same frozen executable, Gurobi 13.0.2, one thread, Seed=0, and automatic presolve. P-GRB was the one original compact MILP with no HGA or imported route; K1 used the frozen `paper-k1-am-sf` preset. Longer runs were fresh processes authorized only by the frozen staged policy, and their screen time was not added to reported algorithm time.

## Paired outcomes

"""
    for key in (
            "both_certified_k1_faster", "both_certified_pgrb_faster",
            "both_certified_tie", "k1_only_certified", "pgrb_only_certified",
            "neither_certified_k1_better_bound",
            "neither_certified_pgrb_better_bound", "neither_certified_mixed",
            "invalid_pair"):
        text += f"- `{key}`: {outcomes[key]}\n"
    text += f"""

The paired exact shifted time geometric means are {metrics['K1_paired_exact_shifted_time_geometric_mean']} seconds for K1 and {metrics['PGRB_paired_exact_shifted_time_geometric_mean']} seconds for P-GRB, giving K1/P-GRB ratio {metrics['paired_exact_shifted_time_ratio_K1_over_PGRB']}. The shifted Work geometric means are {metrics['K1_paired_exact_shifted_work_geometric_mean']} and {metrics['PGRB_paired_exact_shifted_work_geometric_mean']}, giving ratio {metrics['paired_exact_shifted_work_ratio_K1_over_PGRB']}. These exact metrics use only scenarios on which both methods strictly certified. Capped rows retain their qualified LB, independently verified UB, and explicit absolute/relative/scaled gaps; no invented solve time is assigned.

## Structural variation

"""
    for field, label in (("V", "V"), ("geographic_regime", "geography"),
                         ("inventory_regime", "inventory"),
                         ("replicate", "geographic replicate"), ("M", "M"),
                         ("fleet_density_V_over_M", "fleet density V/M"),
                         ("T", "T"), ("Q", "Q")):
        text += f"### By {label}\n\n"
        for group in group_rows(direct, field):
            text += (
                f"- {field}={group[field]}: n={group['scenario_count']}, "
                f"certificates K1/P-GRB={group['K1_final_certificate_count']}/"
                f"{group['PGRB_final_certificate_count']}, shifted exact time ratio="
                f"{group['shifted_exact_time_ratio_K1_over_PGRB']}, shifted exact "
                f"Work ratio={group['shifted_exact_work_ratio_K1_over_PGRB']}.\n")
        text += "\n"
    text += f"""

## Interpretation and route evidence

Final results with a verified incumbent have native, non-post-optimized route packages under `solutions/<scenario>/<method>/`. Archive construction and independent verification time are excluded from solver time. Unequal final horizons are explicitly labeled; bound comparisons used the largest common authorized horizon rather than comparing a six-hour row directly with a one-hour row.

This paired panel supports only the stated frozen-panel qualification; it is not universal validation of the generated family. A second sealed panel drawn from the 910 untouched reserves is still required for a stronger paper benchmark claim. The recommended next step is to freeze that holdout selection before opening any additional solver result, then repeat the unchanged paired protocol.
"""
    (OUT / "final_report.md").write_text(text, encoding="utf-8", newline="\n")
    analysis = f"""# Round 58 benchmark analysis

The primary evidence is the 50-row paired table in `direct_pair_comparison.csv`. The final classification is `{classification}`. Grouped results by V, geography, inventory regime, T, and Q are provided in the corresponding CSV files. Certificate-count curves use actual strict certificates by entered horizon; capped rows are not assigned artificial completion times.

The exact shifted time ratio is {metrics['paired_exact_shifted_time_ratio_K1_over_PGRB']} and the exact shifted Work ratio is {metrics['paired_exact_shifted_work_ratio_K1_over_PGRB']}. The common-horizon gap criterion was {'nonworse' if metrics['common_horizon_gap_nonworse_overall'] else 'not nonworse'} overall. See the two regression audits for row-level definitions and results.
"""
    (OUT / "benchmark_analysis.md").write_text(
        analysis, encoding="utf-8", newline="\n")


def evidence_inventory() -> list[dict[str, Any]]:
    rows = []
    for path in sorted(OUT.rglob("*")):
        if (path.is_file() and "local_raw" not in path.parts and
                path.name not in {"final_evidence_inventory.csv",
                                  "final_delivery_audit.json"}):
            rows.append({
                "path": r58.repo_path(path), "bytes": path.stat().st_size,
                "sha256": r58.sha256_file(path),
                "category": "route_archive" if "solutions" in path.parts else "compact_evidence",
            })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-route-archives", action="store_true")
    args = parser.parse_args()
    protocol = runner.protocol_audit()
    runner.emit_stage_evidence()
    checkpoints = checkpoint_rows()
    r58.write_csv(OUT / "checkpoint_trajectories.csv", checkpoints, atomic=True)
    official_material = official_rows()
    r58.write_csv(OUT / "official_final_results.csv", official_material, atomic=True)
    r58.write_csv(OUT / "final_run_selection.csv", official_material, atomic=True)
    compute = compute_rows()
    r58.write_csv(OUT / "experimental_compute_accounting.csv", compute, atomic=True)
    common = common_rows(checkpoints)
    r58.write_csv(OUT / "common_horizon_comparisons.csv", common, atomic=True)
    repeatability = repeatability_rows(checkpoints)
    if repeatability:
        r58.write_csv(OUT / "long_run_repeatability_audit.csv", repeatability, atomic=True)
    direct = direct_rows()
    historical, long_regression = regression_rows(direct, common)
    for item in direct:
        item["severe_regression_status"] = next(
            row["severe_regression"] for row in historical
            if row["scenario_id"] == item["scenario_id"])
        item["long_run_material_regression_status"] = next(
            row["long_run_material_regression"] for row in long_regression
            if row["scenario_id"] == item["scenario_id"])
    r58.write_csv(OUT / "direct_pair_comparison.csv", direct, atomic=True)
    r58.write_csv(OUT / "historical_severe_regression_audit.csv", historical, atomic=True)
    r58.write_csv(OUT / "long_run_material_regression_audit.csv", long_regression, atomic=True)

    if args.skip_route_archives:
        route_inventory, route_verification, route_timing = [], [], []
    else:
        route_inventory, route_verification, route_timing = route_archives(
            official_material)
        r58.write_csv(OUT / "route_archive_inventory.csv", route_inventory, atomic=True)
        if route_verification:
            r58.write_csv(OUT / "route_verification_audit.csv", route_verification,
                          atomic=True)
        if route_timing:
            r58.write_csv(OUT / "route_archive_timing.csv", route_timing, atomic=True)
    certificate_rows, false_rows = certificate_audits(
        official_material, route_verification)
    r58.write_csv(OUT / "certificate_audit.csv", certificate_rows, atomic=True)
    r58.write_csv(OUT / "false_certificate_audit.csv", false_rows, atomic=True)
    for field, filename in (
            ("V", "comparison_by_V.csv"),
            ("geographic_regime", "comparison_by_geography.csv"),
            ("inventory_regime", "comparison_by_inventory_regime.csv"),
            ("replicate", "comparison_by_replicate.csv"),
            ("M", "comparison_by_M.csv"),
            ("fleet_density_V_over_M", "comparison_by_fleet_density.csv"),
            ("T", "comparison_by_T.csv"), ("Q", "comparison_by_Q.csv")):
        r58.write_csv(OUT / filename, group_rows(direct, field), atomic=True)
    r58.write_csv(OUT / "certificate_horizon_summary.csv", horizon_summary(), atomic=True)
    r58.write_csv(OUT / "performance_profile_data.csv", performance_rows(direct), atomic=True)
    correctness_failures = sum(
        not bool(row["passed"]) and row.get("failures") != "no_verified_incumbent"
        for row in route_verification)
    classification, metrics = final_classification(
        direct, common, long_regression,
        int(false_rows[0]["false_certificate_count"]), correctness_failures)
    outcome_counts = Counter(row["pair_outcome"] for row in direct)
    metrics.update({
        "K1_screen_certificate_count": sum(
            bool(runner.marker_summary(row, "k1_am_sf", 3600)["strict_certificate"])
            for row in panel()),
        "PGRB_screen_certificate_count": sum(
            bool(runner.marker_summary(row, "pgrb", 3600)["strict_certificate"])
            for row in panel()),
        "scenario_pairs_entering_10800": sum(
            runner.marker_summary(row, "k1_am_sf", 10800) is not None or
            runner.marker_summary(row, "pgrb", 10800) is not None
            for row in panel()),
        "rows_entering_16200": len(runner.stage_result_rows(16200)),
        "rows_entering_21600": len(runner.stage_result_rows(21600)),
        "total_experimental_compute_time": sum(
            float(row["total_experimental_compute_time"]) for row in compute),
        "total_experimental_compute_work": sum(
            float(row["total_experimental_compute_work"]) for row in compute),
        "pair_outcome_counts": dict(sorted(outcome_counts.items())),
    })
    panel_ids = [row["scenario_id"] for row in panel()]
    if len(panel_ids) != 50 or len(set(panel_ids)) != 50:
        dataset_classification = "dataset_panel_invalid"
    elif protocol["completed_screen_arm_count"] == 100:
        dataset_classification = "citibike443_paired_panel_complete"
    else:
        dataset_classification = "citibike443_paired_panel_partial"
    if metrics["rows_entering_21600"]:
        runtime_classification = "six_hour_extensions_used"
    elif metrics["rows_entering_16200"]:
        runtime_classification = "near_convergence_extensions_used"
    else:
        runtime_classification = "all_results_within_three_hours"
    route_required = sum(bool(row["verified_incumbent_available"])
                         for row in official_material)
    route_verified = sum(bool(row["passed"]) for row in route_verification)
    if correctness_failures:
        route_classification = "route_archive_invalid"
    elif route_verified == route_required:
        route_classification = "paired_native_route_archive_complete"
    else:
        route_classification = "paired_native_route_archive_partial"
    by_v = {int(float(row["V"])): row for row in group_rows(direct, "V")}
    supported_v = {
        value for value, row in by_v.items()
        if int(row["K1_final_certificate_count"]) >=
        int(row["PGRB_final_certificate_count"]) and (
            (finite(row["shifted_exact_time_ratio_K1_over_PGRB"]) and
             finite(row["shifted_exact_work_ratio_K1_over_PGRB"]) and
             float(row["shifted_exact_time_ratio_K1_over_PGRB"]) <= 1.0 and
             float(row["shifted_exact_work_ratio_K1_over_PGRB"]) <= 1.0) or
            (finite(row["mean_K1_relative_gap"]) and
             finite(row["mean_PGRB_relative_gap"]) and
             float(row["mean_K1_relative_gap"]) <=
             float(row["mean_PGRB_relative_gap"])))
    }
    if supported_v == {8, 12, 20, 30, 50}:
        scale_classification = "v8_v12_v20_v30_v50_supported"
    elif {8, 12, 20}.issubset(supported_v) and supported_v & {30, 50}:
        scale_classification = "v8_v12_v20_supported_v30_v50_mixed"
    elif {8, 12, 20}.issubset(supported_v):
        scale_classification = "small_medium_only"
    else:
        scale_classification = "scale_mixed"
    build_report = OUT / "final_build_and_tests.md"
    build_tests_passed = (build_report.is_file() and
                          "Overall status: PASS" in build_report.read_text(
                              encoding="utf-8"))
    completion_classification = (
        "round58_complete" if all((protocol["protocol_complete"],
                                    dataset_classification ==
                                    "citibike443_paired_panel_complete",
                                    route_classification ==
                                    "paired_native_route_archive_complete",
                                    metrics["false_certificate_count"] == 0,
                                    correctness_failures == 0,
                                    build_tests_passed))
        else "round58_incomplete")
    metrics.update({
        "completion_classification": completion_classification,
        "dataset_classification": dataset_classification,
        "runtime_classification": runtime_classification,
        "scale_classification": scale_classification,
        "route_classification": route_classification,
        "route_required_count": route_required,
        "route_verified_count": route_verified,
        "build_and_tests_passed": build_tests_passed,
    })
    decision = {
        "schema": "round58-final-decision-v1", "created_at_utc": datetime.now(
            timezone.utc).isoformat(), "classification": classification,
        "source_freeze_commit": runner.SOURCE_FREEZE,
        "execution_pipeline_commit": "6484936e87f131979259dcb9c34a4ad02bce9785",
        "executable_sha256": runner.EXE_SHA256,
        "completion_classification": completion_classification,
        "dataset_classification": dataset_classification,
        "benchmark_classification": classification,
        "runtime_classification": runtime_classification,
        "scale_classification": scale_classification,
        "route_classification": route_classification,
        "missing_required_runs": protocol["missing_authorized_runs"],
        "build_and_tests_passed": build_tests_passed,
        "dataset_validated_before_benchmark": True,
        "panel_selected_before_performance": True,
        "reserve_scenarios_opened": False, "algorithm_tuning_performed": False,
        "protocol": protocol, "metrics": metrics,
        "stage_entry_counts": {
            "screen_3600": len(runner.stage_result_rows(3600)),
            "long_10800": len(runner.stage_result_rows(10800)),
            "extension_16200": len(runner.stage_result_rows(16200)),
            "extension_21600": len(runner.stage_result_rows(21600)),
        },
    }
    r58.write_json(OUT / "final_decision.json", decision)
    write_markdown(classification, metrics, direct, protocol, repeatability, historical)
    # The inventory and final delivery audit are excluded to avoid self- and
    # mutual-reference.  The delivery audit regenerates and verifies this
    # inventory after writing every other stable compact artifact.
    r58.write_csv(OUT / "final_evidence_inventory.csv", evidence_inventory(),
                  atomic=True)
    print(json.dumps({"classification": classification, **metrics,
                      "official_rows": len(official_material)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
