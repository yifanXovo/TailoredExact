#!/usr/bin/env python3
"""Exact all-state LP delta and coefficient audit for Round 51 M1."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import statistics
from pathlib import Path

import audit_round50_cut_formulation as lp_audit


ROOT = Path(__file__).resolve().parents[1]
ROUND50 = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
EVIDENCE = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"
RECONSTRUCTION = ROUND50 / "fixed_interval_state_reconstruction_audit.csv"
MANIFEST = ROUND50 / "fixed_interval_state_manifest.csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_lp(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    objective, rest = text.split("Subject To\n", 1)
    _, domains = rest.split("Bounds\n", 1)
    return objective, domains


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = fraction * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def model_ranges(rows: list[dict[str, object]]) -> tuple[float, float, float]:
    coefficients = [abs(value) for row in rows
                    for value in row["coefficients"].values()
                    if abs(value) > 0.0]
    rhs_values = [abs(float(row["rhs"])) for row in rows]
    minimum = min(coefficients)
    maximum = max(coefficients)
    return minimum, maximum, max(rhs_values)


def parse_header(path: Path) -> tuple[int, int]:
    header = path.read_text(encoding="utf-8").splitlines()[0].strip()
    match = re.fullmatch(r"(\d+)\s+(\d+)\s+\[[^]]+\]", header)
    if not match:
        raise RuntimeError(f"unparsed instance header: {path}")
    return int(match.group(1)), int(match.group(2))


def validate_target_delta(old: dict[str, object], new: dict[str, object],
                          total_time: float) -> tuple[bool, float, int, str]:
    if old["sense"] != "<=" or new["sense"] != "<=":
        return False, 0.0, 0, "target_row_sense_changed"
    old_c = old["coefficients"]
    new_c = new["coefficients"]
    old_names = set(old_c)
    new_names = set(new_c)
    if old_names != new_names:
        return False, 0.0, 0, "target_variable_set_changed"
    p_names = sorted(name for name in old_names if name.startswith("p_"))
    z_names = sorted(name for name in old_names if name.startswith("z_"))
    if not p_names or len(p_names) != len(z_names):
        return False, 0.0, 0, "target_semantic_sets_invalid"
    p_keys = {name.split("_", 1)[1] for name in p_names}
    z_keys = {name.split("_", 1)[1] for name in z_names}
    if p_keys != z_keys or old_names != set(p_names) | set(z_names):
        return False, 0.0, 0, "target_pickup_visit_sets_differ"
    if any(abs(float(old_c[name]) - float(new_c[name])) > 1e-12
           for name in p_names):
        return False, 0.0, 0, "pickup_coefficient_changed"
    if any(abs(float(old_c[name]) - 100000.0) > 1e-9 for name in z_names):
        return False, 0.0, 0, "historical_m_not_100000"
    analytic_values = [float(new_c[name]) for name in z_names]
    if max(analytic_values) - min(analytic_values) > 1e-9:
        return False, 0.0, 0, "m1_row_m_not_uniform"
    tsp_bound = analytic_values[0]
    if not math.isfinite(tsp_bound) or tsp_bound < -1e-9:
        return False, 0.0, 0, "m1_tsp_bound_invalid"
    cardinality = len(z_names)
    expected_old_rhs = total_time - tsp_bound + 100000.0 * cardinality
    expected_new_rhs = total_time - tsp_bound + tsp_bound * cardinality
    tolerance = 1e-7 * max(1.0, abs(expected_old_rhs), abs(expected_new_rhs))
    if abs(float(old["rhs"]) - expected_old_rhs) > tolerance:
        return False, tsp_bound, cardinality, "historical_rhs_formula_invalid"
    if abs(float(new["rhs"]) - expected_new_rhs) > tolerance:
        return False, tsp_bound, cardinality, "m1_rhs_formula_invalid"
    return True, tsp_bound, cardinality, "none"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", required=True, type=Path)
    args = parser.parse_args()
    reconstruction = list(csv.DictReader(RECONSTRUCTION.open(
        newline="", encoding="utf-8-sig")))
    manifest = {row["state_id"]: row for row in csv.DictReader(
        MANIFEST.open(newline="", encoding="utf-8-sig"))}
    if len(reconstruction) != 23:
        raise RuntimeError("all 23 frozen states are required")
    coefficient_rows: list[dict[str, object]] = []
    delta_rows: list[dict[str, object]] = []
    range_rows: list[dict[str, object]] = []
    failures: list[str] = []
    for state in reconstruction:
        state_id = state["state_id"]
        input_path = ROOT / manifest[state_id]["input_path"]
        stations, vehicles = parse_header(input_path)
        old_dir = args.run_root / f"{state_id}__interval-mip-v0"
        new_dir = args.run_root / f"{state_id}__m1-tight-big-m-v0"
        old_lp = old_dir / "canonical_model.lp"
        new_lp = new_dir / "canonical_model.lp"
        old_model = json.loads((old_dir / "model_fingerprint.json").read_text(
            encoding="utf-8"))
        new_model = json.loads((new_dir / "model_fingerprint.json").read_text(
            encoding="utf-8"))
        old_rows = lp_audit.parse_model(old_lp)
        new_rows = lp_audit.parse_model(new_lp)
        old_objective, old_domains = split_lp(old_lp)
        new_objective, new_domains = split_lp(new_lp)
        expected_target_rows = vehicles * ((1 << stations) - 1) \
            if stations <= 12 else 0
        changed: list[tuple[dict[str, object], dict[str, object]]] = []
        senses_identical = len(old_rows) == len(new_rows)
        non_target_identical = len(old_rows) == len(new_rows)
        for old, new in zip(old_rows, new_rows):
            if old["row_id"] != new["row_id"] or old["sense"] != new["sense"]:
                senses_identical = False
            if old["exact_signature"] != new["exact_signature"]:
                changed.append((old, new))
        target_values: list[float] = []
        target_formulas_valid = True
        target_failure = "none"
        for old, new in changed:
            valid, tsp_bound, _, reason = validate_target_delta(
                old, new, float(state["route_time_limit"]))
            if not valid:
                target_formulas_valid = False
                target_failure = reason
                non_target_identical = False
                break
            target_values.append(tsp_bound)
        affected = stations <= 12
        changed_count_valid = len(changed) == expected_target_rows
        objective_identical = old_objective == new_objective
        domains_identical = old_domains == new_domains
        frozen_default_match = (
            sha256(old_lp) == state["canonical_model_fingerprint"]
            == old_model["sha256"])
        v_gt_12_identical = (not affected and sha256(old_lp) == sha256(new_lp))
        static_model_parts_identical = non_target_identical and senses_identical
        status = all((
            objective_identical, domains_identical, senses_identical,
            static_model_parts_identical, changed_count_valid,
            target_formulas_valid, frozen_default_match,
            affected or v_gt_12_identical,
            int(old_model["rows"]) == int(new_model["rows"]),
            int(old_model["columns"]) == int(new_model["columns"]),
        ))
        if not status:
            failures.append(state_id)
        unique_values = target_values[::vehicles] if vehicles > 0 else target_values
        # Row order is mask-major within each vehicle block; de-duplicate by
        # numeric multiset instead of relying on that order.
        if target_values:
            unique_values = target_values[:expected_target_rows // vehicles]
        else:
            unique_values = []
        coefficient_rows.append({
            "state_id": state_id, "panel": state["panel"],
            "station_count": stations, "vehicle_count": vehicles,
            "big_m_affected": str(affected).lower(), "old_m": 100000.0,
            "min_m_s": min(unique_values) if unique_values else 0.0,
            "median_m_s": statistics.median(unique_values) if unique_values else 0.0,
            "mean_m_s": statistics.fmean(unique_values) if unique_values else 0.0,
            "p95_m_s": percentile(unique_values, 0.95),
            "max_m_s": max(unique_values) if unique_values else 0.0,
            "min_ratio_to_old": min(unique_values) / 100000.0 if unique_values else 0.0,
            "median_ratio_to_old": statistics.median(unique_values) / 100000.0 if unique_values else 0.0,
            "mean_ratio_to_old": statistics.fmean(unique_values) / 100000.0 if unique_values else 0.0,
            "p95_ratio_to_old": percentile(unique_values, 0.95) / 100000.0 if unique_values else 0.0,
            "max_ratio_to_old": max(unique_values) / 100000.0 if unique_values else 0.0,
            "rows_affected": len(changed),
            "expected_rows_affected": expected_target_rows,
            "m_s_above_100000_count": sum(value > 100000.0 for value in unique_values),
            "historical_m_may_be_unsafe": str(any(
                value > 100000.0 for value in unique_values)).lower(),
            "all_target_formulas_valid": str(target_formulas_valid).lower(),
            "status": "pass" if status else "fail",
            "failure_reason": "none" if status else target_failure,
        })
        delta_rows.append({
            "state_id": state_id, "big_m_affected": str(affected).lower(),
            "historical_model_sha256": old_model["sha256"],
            "m1_model_sha256": new_model["sha256"],
            "historical_matches_round50_frozen": str(frozen_default_match).lower(),
            "objective_identical": str(objective_identical).lower(),
            "variable_names_types_bounds_identical": str(domains_identical).lower(),
            "row_count_identical": str(len(old_rows) == len(new_rows)).lower(),
            "row_senses_identical": str(senses_identical).lower(),
            "changed_rows": len(changed),
            "expected_changed_rows": expected_target_rows,
            "all_non_target_rows_identical": str(non_target_identical).lower(),
            "symmetry_rows_identical": str(static_model_parts_identical).lower(),
            "interval_rows_identical": str(static_model_parts_identical).lower(),
            "cutoff_rows_identical": str(static_model_parts_identical).lower(),
            "target_row_formula_valid": str(target_formulas_valid).lower(),
            "v_gt_12_expected_model_identical": str(not affected).lower(),
            "v_gt_12_model_identical": str(v_gt_12_identical).lower(),
            "status": "pass" if status else "fail",
            "failure_reason": "none" if status else target_failure,
        })
        old_min, old_max, old_rhs = model_ranges(old_rows)
        new_min, new_max, new_rhs = model_ranges(new_rows)
        range_rows.append({
            "state_id": state_id, "big_m_affected": str(affected).lower(),
            "old_min_matrix": old_min, "m1_min_matrix": new_min,
            "old_max_matrix": old_max, "m1_max_matrix": new_max,
            "max_matrix_reduction": old_max - new_max,
            "old_max_abs_rhs": old_rhs, "m1_max_abs_rhs": new_rhs,
            "max_abs_rhs_reduction": old_rhs - new_rhs,
            "old_matrix_range_ratio": old_max / old_min,
            "m1_matrix_range_ratio": new_max / new_min,
            "matrix_range_ratio_reduction": old_max / old_min - new_max / new_min,
            "status": "pass" if status else "fail",
        })
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    for path, rows in (
        (EVIDENCE / "big_m_row_coefficient_audit.csv", coefficient_rows),
        (EVIDENCE / "big_m_model_delta_audit.csv", delta_rows),
        (EVIDENCE / "numerical_conditioning_before_after.csv", range_rows),
    ):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]),
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    if failures:
        raise RuntimeError(f"M1 model audit failed: {failures}")
    print("M1 all-state model delta and coefficient audit passed (23/23)")


if __name__ == "__main__":
    main()
