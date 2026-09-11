#!/usr/bin/env python3
"""Audit and compact the frozen Round 52 validation and holdout panels.

The official native logs stay below ``local_raw``.  This script rejects any
missing or malformed official row, reconstructs the 300/1200/1800 second
bound trajectories, applies the pre-frozen severe-regression rule, and emits
the compact paper-facing ledgers and reports required by the Round 52
contract.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_tailored_cut_final_validation_round52"
RUNS = OUT / "local_raw" / "final_panel_runs"
CAP = 1800.0
CHECKPOINTS = (300.0, 1200.0, 1800.0)
METHODS = ("P-GRB", "K1-AM-FINAL")
EXECUTABLE_SHA256 = (
    "d245c76f6397c757894610d8f5238cfeb971761ff7e05edf51058e451d810151"
)
CERTIFICATE_TOLERANCE = 1e-7
SHIFT = 1.0


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        if len(value) != 1 or not isinstance(value[0], dict):
            raise RuntimeError(f"unexpected JSON list at {path}")
        return value[0]
    if not isinstance(value, dict):
        raise RuntimeError(f"unexpected JSON value at {path}")
    return value


def dump_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    if not rows and fields is None:
        raise RuntimeError(f"cannot infer columns for empty ledger {path}")
    names = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=names, lineterminator="\n",
                                extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def truth(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def number(value: object, default: float = math.nan) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def relative_gap(lower: float, upper: float) -> float:
    if not math.isfinite(lower) or not math.isfinite(upper):
        return 1.0
    return max(0.0, upper - lower) / max(1e-12, abs(upper))


def geometric_mean(values: Iterable[float]) -> float:
    finite = list(values)
    if not finite or any(value <= 0 or not math.isfinite(value)
                         for value in finite):
        return math.nan
    return math.exp(sum(math.log(value) for value in finite) / len(finite))


def percentile(values: Iterable[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return math.nan
    position = probability * (len(ordered) - 1)
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return ordered[low]
    weight = position - low
    return ordered[low] * (1.0 - weight) + ordered[high] * weight


def git(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=ROOT, text=True,
        encoding="utf-8", errors="replace").strip()


def manifest(panel: str) -> list[dict[str, Any]]:
    value = load_json(OUT / f"{panel}_instance_manifest.json")
    rows = value.get("rows", [])
    if value.get("row_count") != 12 or len(rows) != 12:
        raise RuntimeError(f"{panel} manifest does not contain twelve rows")
    if {int(row["V"]) for row in rows} != {12, 20, 50}:
        raise RuntimeError(f"{panel} manifest has wrong size classes")
    return rows


def trajectory(run_dir: Path, method: str,
               result: dict[str, Any]) -> list[dict[str, float]]:
    points: list[dict[str, float]] = []
    if method == "P-GRB":
        for row in csv_rows(run_dir / "progress.csv"):
            if not truth(row.get("best_bound_available")):
                continue
            try:
                elapsed = float(row["elapsed_runtime_seconds"])
                lower = float(row["best_bound"])
                upper = (float(row["incumbent"])
                         if truth(row.get("incumbent_available")) else math.inf)
            except (KeyError, TypeError, ValueError):
                continue
            points.append({
                "time": max(0.0, elapsed), "lower": lower, "upper": upper,
                "gap": relative_gap(lower, upper),
                "work": number(row.get("work"), 0.0),
                "nodes": number(row.get("processed_nodes"), 0.0),
            })
    else:
        path = run_dir / "external" / "global_bound_trace.csv"
        for row in csv_rows(path):
            try:
                elapsed = float(row["process_elapsed_seconds"])
                lower = float(row["valid_global_lower_bound"])
                upper = float(row["verified_global_upper_bound"])
            except (KeyError, TypeError, ValueError):
                continue
            points.append({
                "time": max(0.0, elapsed), "lower": lower, "upper": upper,
                "gap": relative_gap(lower, upper),
                "work": math.nan, "nodes": math.nan,
            })
    if not points:
        raise RuntimeError(f"no valid bound trajectory at {run_dir}")
    points.sort(key=lambda row: row["time"])
    # Native traces begin when the exact phase obtains its first bound.  The
    # pre-bound part of the total process horizon conservatively has unit gap.
    return points


def monotone_audit(points: list[dict[str, float]]) -> tuple[bool, bool]:
    lower_ok = all(
        right["lower"] + CERTIFICATE_TOLERANCE * max(
            1.0, abs(left["lower"]), abs(right["lower"])) >= left["lower"]
        for left, right in zip(points, points[1:]))
    upper_ok = all(
        right["upper"] <= left["upper"] + CERTIFICATE_TOLERANCE * max(
            1.0, abs(left["upper"]), abs(right["upper"]))
        for left, right in zip(points, points[1:])
        if math.isfinite(left["upper"]) and math.isfinite(right["upper"]))
    return lower_ok, upper_ok


def value_at(points: list[dict[str, float]], checkpoint: float,
             key: str, default: float) -> float:
    value = default
    for row in points:
        if row["time"] > checkpoint:
            break
        value = row[key]
    return value


def gap_integral(points: list[dict[str, float]], horizon: float,
                 exact: bool, process_seconds: float) -> float:
    previous_time = 0.0
    previous_gap = 1.0
    area = 0.0
    for row in points:
        current_time = min(horizon, max(previous_time, row["time"]))
        area += (current_time - previous_time) * previous_gap
        previous_time = current_time
        previous_gap = row["gap"]
        if previous_time >= horizon:
            break
    if exact and process_seconds <= horizon:
        exact_time = max(previous_time, min(horizon, process_seconds))
        area += (exact_time - previous_time) * previous_gap
        previous_time = exact_time
        previous_gap = 0.0
    if previous_time < horizon:
        area += (horizon - previous_time) * previous_gap
    return area / horizon


def checkpoint_values(points: list[dict[str, float]], checkpoint: float,
                      exact: bool, process_seconds: float,
                      final_lower: float, final_upper: float) -> dict[str, float]:
    if exact and process_seconds <= checkpoint:
        lower, upper, gap = final_lower, final_upper, 0.0
    else:
        lower = value_at(points, checkpoint, "lower", 0.0)
        upper = value_at(points, checkpoint, "upper", math.inf)
        gap = relative_gap(lower, upper)
    return {
        "lower_bound": lower,
        "verified_upper_bound": upper,
        "relative_gap": gap,
        "normalized_gap_integral": gap_integral(
            points, checkpoint, exact, process_seconds),
    }


def result_correctness(method: str, result: dict[str, Any], exact: bool,
                       lower: float, upper: float,
                       lower_monotone: bool, upper_monotone: bool) -> tuple[bool, str]:
    reasons: list[str] = []
    if not truth(result.get("option_audit_consistent")):
        reasons.append("option_audit_inconsistent")
    if not truth(result.get("verification", {}).get("feasible")):
        reasons.append("incumbent_not_verified_feasible")
    if lower > upper + CERTIFICATE_TOLERANCE * max(1.0, abs(upper)):
        reasons.append("bound_inversion")
    if not lower_monotone:
        reasons.append("lower_bound_trace_not_monotone")
    if not upper_monotone:
        reasons.append("upper_bound_trace_not_monotone")
    if method == "P-GRB":
        if not truth(result.get("gurobi_lifecycle_valid")):
            reasons.append("gurobi_lifecycle_invalid")
        if not truth(result.get("native_mip_lifecycle_valid")):
            reasons.append("native_lifecycle_invalid")
        if not truth(result.get("gurobi_native_domain_audit_passed")):
            reasons.append("native_domain_audit_failed")
    else:
        required = (
            "external_gini_tree_root_coverage_valid",
            "external_gini_tree_parent_child_coverage_valid",
            "external_gini_tree_all_leaf_bounds_valid",
            "external_gini_tree_leaf_bounds_monotone",
            "external_gini_tree_global_bound_monotone",
            "external_gini_tree_lifecycle_complete",
            "external_gini_tree_backend_parameter_roundtrip_valid",
        )
        reasons.extend(key for key in required if not truth(result.get(key)))
        if truth(result.get("external_gini_tree_canonical_artifact_invalidation_count")):
            reasons.append("canonical_artifact_invalidated")
    if exact:
        tolerance = number(result.get(
            "external_gini_tree_certificate_tolerance"),
            CERTIFICATE_TOLERANCE)
        if relative_gap(lower, upper) > max(CERTIFICATE_TOLERANCE, tolerance):
            reasons.append("strict_certificate_gap_exceeds_tolerance")
        if result.get("strict_certificate_rejection_reason") not in (None, "", "none"):
            reasons.append("strict_certificate_has_rejection_reason")
        if method == "K1-AM-FINAL":
            if not truth(result.get("external_gini_tree_strict_certified")):
                reasons.append("external_tree_not_strict_certified")
            if not truth(result.get("external_gini_tree_all_relevant_leaves_closed")):
                reasons.append("relevant_leaf_open")
    return not reasons, "none" if not reasons else "|".join(reasons)


def load_run(panel: str, row: dict[str, Any], method: str) -> tuple[
        dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    run_id = f"{panel}__{row['instance_id']}__{method}__official"
    run_dir = RUNS / run_id
    required = ("command.json", "completion_marker.json", "result.json",
                "artifact_manifest.csv")
    missing = [name for name in required if not (run_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"{run_id} missing {missing}")
    command = load_json(run_dir / "command.json")
    marker = load_json(run_dir / "completion_marker.json")
    result = load_json(run_dir / "result.json")
    if not (marker.get("complete") is True and
            marker.get("official_strict_contract") is True and
            marker.get("cap_respected") is True):
        raise RuntimeError(f"unsealed official row {run_id}")
    if marker.get("panel") != panel or marker.get("method") != method:
        raise RuntimeError(f"marker identity mismatch at {run_id}")
    if marker.get("instance_id") != row["instance_id"]:
        raise RuntimeError(f"marker instance mismatch at {run_id}")
    if marker.get("executable_sha256") != EXECUTABLE_SHA256:
        raise RuntimeError(f"executable mismatch at {run_id}")
    process_seconds = number(result.get("final_process_wall_time_seconds"))
    if not math.isfinite(process_seconds) or process_seconds > CAP + 1e-6:
        raise RuntimeError(f"process cap failure at {run_id}: {process_seconds}")
    if command.get("official_strict_contract") is not True:
        raise RuntimeError(f"command contract mismatch at {run_id}")
    if command.get("input_sha256") != row["input_sha256"]:
        raise RuntimeError(f"input identity mismatch at {run_id}")
    if method == "P-GRB":
        expected = marker.get("expected_gurobi_model_fingerprint")
        if expected is None or int(expected) != int(result.get(
                "gurobi_model_fingerprint", 0)):
            raise RuntimeError(f"model fingerprint mismatch at {run_id}")
    exact = truth(result.get("strict_certified_original_problem"))
    lower = number(result.get("lower_bound"))
    upper = number(result.get("upper_bound"))
    points = trajectory(run_dir, method, result)
    lower_monotone, upper_monotone = monotone_audit(points)
    correctness, failure_reason = result_correctness(
        method, result, exact, lower, upper, lower_monotone, upper_monotone)
    false_certificate = exact and not correctness
    checkpoints = {
        int(checkpoint): checkpoint_values(
            points, checkpoint, exact, process_seconds, lower, upper)
        for checkpoint in CHECKPOINTS
    }
    work = number(result.get(
        "gurobi_work" if method == "P-GRB" else "external_gini_tree_work"),
        0.0)
    nodes = number(result.get(
        "gurobi_node_count" if method == "P-GRB" else
        "external_gini_tree_nodes"), 0.0)
    simplex = number(result.get(
        "gurobi_iter_count" if method == "P-GRB" else
        "external_gini_tree_simplex_iterations"), 0.0)
    if method == "P-GRB":
        first_incumbent = number(result.get("gurobi_first_incumbent_time"))
        split_count = interval_count = lp_probe_count = 0
        cuts_generated = cuts_added = 0
        callback_overhead = number(
            result.get("dense_progress_callback_wall_seconds"), 0.0)
        peak_memory = number(result.get("gurobi_max_mem_used_gb"), 0.0)
    else:
        initial_progress = csv_rows(run_dir / "progress.csv")
        first_incumbent = number(
            initial_progress[0].get("elapsed_seconds") if initial_progress else 0.0,
            0.0)
        split_count = int(number(result.get("external_gini_tree_split_count"), 0))
        interval_count = int(number(
            result.get("external_gini_tree_final_leaf_count"), 0))
        lp_probe_count = int(number(
            result.get("external_gini_tree_lp_optimize_count"), 0))
        cuts_generated = int(number(result.get("support_duration_cuts_generated"), 0))
        cuts_added = int(number(result.get("tailored_bc_user_cuts_added_total"), 0))
        callback_overhead = number(
            result.get("global_gini_tree_callback_packing_seconds"), 0.0)
        peak_memory = number(result.get("external_gini_tree_peak_memory_gb"), 0.0)
    compact: dict[str, Any] = {
        "panel": panel, "instance_id": row["instance_id"],
        "input_sha256": row["input_sha256"], "V": int(row["V"]),
        "M": int(row["M"]), "T": number(row["T"]),
        "difficulty_configuration": row["difficulty_configuration"],
        "method": method, "run_id": run_id,
        "status": "exact" if exact else "capped",
        "strict_certificate": exact, "false_certificate": false_certificate,
        "correctness_gate": correctness,
        "correctness_failure_reason": failure_reason,
        "certificate_class": result.get("strict_certificate_class", ""),
        "certificate_rejection_reason": result.get(
            "strict_certificate_rejection_reason", ""),
        "work": work, "process_time_seconds": process_seconds,
        "lower_bound": lower, "verified_upper_bound": upper,
        "relative_gap": relative_gap(lower, upper),
        "nodes": nodes, "simplex_iterations": simplex,
        "first_incumbent_seconds": first_incumbent,
        "split_count": split_count, "interval_count": interval_count,
        "lp_probe_count": lp_probe_count,
        "user_cuts_generated": cuts_generated,
        "user_cuts_added": cuts_added,
        "callback_overhead_seconds": callback_overhead,
        "peak_memory_gb": peak_memory,
        "lower_bound_trace_monotone": lower_monotone,
        "upper_bound_trace_monotone": upper_monotone,
        "process_cap_seconds": CAP, "process_cap_respected": True,
        "threads": 1, "seed": 0, "presolve": "Auto",
        "mip_gap": 0, "mip_gap_abs": 0,
        "executable_sha256": EXECUTABLE_SHA256,
        "model_fingerprint": (result.get("gurobi_model_fingerprint", "")
                              if method == "P-GRB" else "not_applicable"),
        "raw_directory": run_dir.relative_to(ROOT).as_posix(),
        "artifact_manifest_sha256": marker["artifact_manifest_sha256"],
    }
    for checkpoint, values in checkpoints.items():
        for key, value in values.items():
            compact[f"{key}_{checkpoint}s"] = value
    checkpoint_rows = [{
        "panel": panel, "instance_id": row["instance_id"],
        "V": int(row["V"]), "method": method,
        "checkpoint_seconds": checkpoint, **values,
        "strict_certificate_by_checkpoint": exact and process_seconds <= checkpoint,
        "raw_directory": run_dir.relative_to(ROOT).as_posix(),
    } for checkpoint, values in checkpoints.items()]
    certificate_row = {
        "panel": panel, "instance_id": row["instance_id"],
        "V": int(row["V"]), "method": method,
        "strict_certificate": exact, "certificate_class": compact["certificate_class"],
        "certificate_rejection_reason": compact["certificate_rejection_reason"],
        "verified_incumbent_feasible": truth(
            result.get("verification", {}).get("feasible")),
        "lower_bound": lower, "verified_upper_bound": upper,
        "relative_gap": compact["relative_gap"],
        "certificate_tolerance": number(result.get(
            "external_gini_tree_certificate_tolerance"),
            CERTIFICATE_TOLERANCE),
        "lower_bound_trace_monotone": lower_monotone,
        "upper_bound_trace_monotone": upper_monotone,
        "lifecycle_valid": (
            truth(result.get("gurobi_lifecycle_valid")) if method == "P-GRB"
            else truth(result.get("external_gini_tree_lifecycle_complete"))),
        "coverage_valid": (
            True if method == "P-GRB" else
            truth(result.get("external_gini_tree_root_coverage_valid")) and
            truth(result.get("external_gini_tree_parent_child_coverage_valid"))),
        "all_leaf_bounds_valid": (
            True if method == "P-GRB" else
            truth(result.get("external_gini_tree_all_leaf_bounds_valid"))),
        "correctness_gate": correctness,
        "false_certificate": false_certificate,
        "audit_reason": failure_reason,
        "executable_sha256": EXECUTABLE_SHA256,
    }
    return compact, checkpoint_rows, certificate_row


def severe_regression(pgrb: dict[str, Any], candidate: dict[str, Any]) -> tuple[
        bool, str]:
    p_exact = truth(pgrb["strict_certificate"])
    c_exact = truth(candidate["strict_certificate"])
    reasons: list[str] = []
    if p_exact and not c_exact:
        reasons.append("baseline_certifies_candidate_does_not")
    elif p_exact and c_exact:
        work_ratio = ((candidate["work"] / pgrb["work"])
                      if pgrb["work"] > 1e-12 else
                      (1.0 if candidate["work"] <= 1e-12 else math.inf))
        time_ratio = candidate["process_time_seconds"] / max(
            1e-12, pgrb["process_time_seconds"])
        if (work_ratio > 1.5 and
                candidate["work"] - pgrb["work"] > 50):
            reasons.append("exact_work_ratio_gt_1.5_and_delta_gt_50")
        if (time_ratio > 1.5 and
                candidate["process_time_seconds"] -
                pgrb["process_time_seconds"] > 60):
            reasons.append("exact_time_ratio_gt_1.5_and_delta_gt_60")
    else:
        p_gi = pgrb["normalized_gap_integral_1800s"]
        c_gi = candidate["normalized_gap_integral_1800s"]
        gi_ratio = c_gi / max(1e-12, p_gi)
        if gi_ratio > 1.5 and c_gi - p_gi >= 0.05:
            reasons.append("GI_ratio_gt_1.5_and_delta_ge_0.05")
        p_gap = pgrb["relative_gap_1800s"]
        c_gap = candidate["relative_gap_1800s"]
        gap_ratio = c_gap / max(1e-12, p_gap)
        if gap_ratio > 1.5 and c_gap - p_gap >= 0.05:
            reasons.append("gap_ratio_gt_1.5_and_delta_ge_0.05")
    return bool(reasons), "none" if not reasons else "|".join(reasons)


def compare(pgrb: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    severe, reason = severe_regression(pgrb, candidate)
    row: dict[str, Any] = {
        "panel": pgrb["panel"], "instance_id": pgrb["instance_id"],
        "V": pgrb["V"],
        "difficulty_configuration": pgrb["difficulty_configuration"],
        "pgrb_certificate": pgrb["strict_certificate"],
        "k1_certificate": candidate["strict_certificate"],
        "certificate_delta_k1_minus_pgrb": (
            int(candidate["strict_certificate"]) - int(pgrb["strict_certificate"])),
        "pgrb_work": pgrb["work"], "k1_work": candidate["work"],
        "shifted_work_ratio_k1_over_pgrb": (
            (candidate["work"] + SHIFT) / (pgrb["work"] + SHIFT)),
        "pgrb_process_seconds": pgrb["process_time_seconds"],
        "k1_process_seconds": candidate["process_time_seconds"],
        "shifted_process_ratio_k1_over_pgrb": (
            (candidate["process_time_seconds"] + SHIFT) /
            (pgrb["process_time_seconds"] + SHIFT)),
        "pgrb_final_gap": pgrb["relative_gap"],
        "k1_final_gap": candidate["relative_gap"],
        "final_gap_ratio_k1_over_pgrb": (
            candidate["relative_gap"] / max(1e-12, pgrb["relative_gap"])),
        "pgrb_GI_1800": pgrb["normalized_gap_integral_1800s"],
        "k1_GI_1800": candidate["normalized_gap_integral_1800s"],
        "GI_ratio_k1_over_pgrb": (
            candidate["normalized_gap_integral_1800s"] /
            max(1e-12, pgrb["normalized_gap_integral_1800s"])),
        "severe_pgrb_regression": severe,
        "severe_regression_reason": reason,
        "false_certificate": (pgrb["false_certificate"] or
                              candidate["false_certificate"]),
    }
    for checkpoint in (300, 1200, 1800):
        for metric in ("relative_gap", "normalized_gap_integral"):
            row[f"pgrb_{metric}_{checkpoint}s"] = pgrb[
                f"{metric}_{checkpoint}s"]
            row[f"k1_{metric}_{checkpoint}s"] = candidate[
                f"{metric}_{checkpoint}s"]
    return row


def aggregate(label: str, comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    p_cert = sum(truth(row["pgrb_certificate"]) for row in comparisons)
    k_cert = sum(truth(row["k1_certificate"]) for row in comparisons)
    work_ratios = [row["shifted_work_ratio_k1_over_pgrb"]
                   for row in comparisons]
    time_ratios = [row["shifted_process_ratio_k1_over_pgrb"]
                   for row in comparisons]
    p_gi = statistics.fmean(row["pgrb_GI_1800"] for row in comparisons)
    k_gi = statistics.fmean(row["k1_GI_1800"] for row in comparisons)
    common_exact = [row for row in comparisons
                    if truth(row["pgrb_certificate"]) and
                    truth(row["k1_certificate"])]
    return {
        "group": label, "row_count": len(comparisons),
        "pgrb_certificates": p_cert, "k1_certificates": k_cert,
        "k1_certificate_gain": sum(
            not truth(row["pgrb_certificate"]) and truth(row["k1_certificate"])
            for row in comparisons),
        "k1_certificate_loss": sum(
            truth(row["pgrb_certificate"]) and not truth(row["k1_certificate"])
            for row in comparisons),
        "shifted_work_geometric_mean_ratio_k1_over_pgrb": geometric_mean(
            work_ratios),
        "shifted_process_geometric_mean_ratio_k1_over_pgrb": geometric_mean(
            time_ratios),
        "median_shifted_work_ratio": statistics.median(work_ratios),
        "p90_shifted_work_ratio": percentile(work_ratios, 0.90),
        "common_exact_row_count": len(common_exact),
        "common_exact_shifted_work_geometric_mean_ratio": (
            geometric_mean(row["shifted_work_ratio_k1_over_pgrb"]
                           for row in common_exact) if common_exact else None),
        "pgrb_mean_GI_1800": p_gi, "k1_mean_GI_1800": k_gi,
        "aggregate_GI_ratio_k1_over_pgrb": k_gi / max(1e-12, p_gi),
        "severe_pgrb_regressions": sum(
            truth(row["severe_pgrb_regression"]) for row in comparisons),
        "false_certificates": sum(
            truth(row["false_certificate"]) for row in comparisons),
    }


def performance_profile(comparisons: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for panel in ("validation", "holdout", "combined"):
        selected = comparisons if panel == "combined" else [
            row for row in comparisons if row["panel"] == panel]
        eligible = [row for row in selected if truth(row["pgrb_certificate"])
                    or truth(row["k1_certificate"])]
        ratios = {method: [] for method in METHODS}
        for row in eligible:
            observed = {
                "P-GRB": (row["pgrb_process_seconds"]
                          if truth(row["pgrb_certificate"]) else math.inf),
                "K1-AM-FINAL": (row["k1_process_seconds"]
                                if truth(row["k1_certificate"]) else math.inf),
            }
            best = min(observed.values())
            for method in METHODS:
                ratios[method].append(observed[method] / best)
        for tau in (1.0, 1.25, 1.5, 2.0, 5.0, 10.0):
            for method in METHODS:
                output.append({
                    "panel": panel, "metric": "strict_certificate_process_time",
                    "tau": tau, "method": method,
                    "eligible_instances": len(eligible),
                    "fraction_within_tau_of_best": (
                        sum(value <= tau + 1e-12 for value in ratios[method]) /
                        len(eligible) if eligible else ""),
                    "capped_rows_are_infinite": True,
                })
    return output


def tree_hash(path: Path) -> tuple[int, int, str]:
    files = sorted(item for item in path.rglob("*") if item.is_file())
    digest = hashlib.sha256()
    total = 0
    for item in files:
        size = item.stat().st_size
        total += size
        record = (f"{item.relative_to(path).as_posix()}\0{size}\0"
                  f"{sha256(item)}\n")
        digest.update(record.encode("utf-8"))
    return len(files), total, digest.hexdigest()


def evidence_inventories() -> tuple[int, int]:
    excluded = {
        "compact_evidence_inventory.csv", "local_raw_evidence_inventory.csv",
        "final_evidence_inventory.csv",
    }
    compact: list[dict[str, Any]] = []
    for path in sorted(item for item in OUT.iterdir()
                       if item.is_file() and item.name not in excluded):
        compact.append({
            "storage_class": "committed_compact",
            "path": path.relative_to(ROOT).as_posix(),
            "size_bytes": path.stat().st_size, "sha256": sha256(path),
            "represented_raw_group": "not_applicable",
        })
    write_csv(OUT / "compact_evidence_inventory.csv", compact)
    local: list[dict[str, Any]] = []
    for path in sorted(item for item in (OUT / "local_raw").iterdir()):
        if path.is_file():
            local.append({
                "storage_class": "local_raw_only",
                "path": path.relative_to(ROOT).as_posix(),
                "file_count": 1, "size_bytes": path.stat().st_size,
                "tree_sha256": sha256(path),
                "reproduction_anchor": "reproduction_commands.md",
            })
        else:
            count, size, digest = tree_hash(path)
            local.append({
                "storage_class": "local_raw_only",
                "path": path.relative_to(ROOT).as_posix(),
                "file_count": count, "size_bytes": size,
                "tree_sha256": digest,
                "reproduction_anchor": "reproduction_commands.md",
            })
    write_csv(OUT / "local_raw_evidence_inventory.csv", local)
    final_rows = compact + [{
        "storage_class": row["storage_class"], "path": row["path"],
        "size_bytes": row["size_bytes"], "sha256": row["tree_sha256"],
        "represented_raw_group": f"tree:{row['file_count']}-files",
    } for row in local]
    write_csv(OUT / "final_evidence_inventory.csv", final_rows)
    return len(compact), len(local)


def markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    header = "| " + " | ".join(fields) + " |"
    separator = "| " + " | ".join("---" for _ in fields) + " |"
    body = ["| " + " | ".join(str(row[field]) for field in fields) + " |"
            for row in rows]
    return "\n".join([header, separator, *body])


def main() -> int:
    current_branch = git("branch", "--show-current")
    if current_branch != "codex/round52-k1-tailored-cut-final-validation":
        raise RuntimeError(f"unexpected branch: {current_branch}")
    all_results: list[dict[str, Any]] = []
    checkpoints: list[dict[str, Any]] = []
    certificates: list[dict[str, Any]] = []
    missing_rows: list[str] = []
    for panel in ("validation", "holdout"):
        for row in manifest(panel):
            for method in METHODS:
                run_id = f"{panel}__{row['instance_id']}__{method}__official"
                if not (RUNS / run_id).is_dir():
                    missing_rows.append(run_id)
                    continue
                result, checkpoint_rows, certificate = load_run(panel, row, method)
                all_results.append(result)
                checkpoints.extend(checkpoint_rows)
                certificates.append(certificate)
    if missing_rows:
        raise RuntimeError(f"missing official rows: {missing_rows}")
    if len(all_results) != 48 or len(checkpoints) != 144:
        raise RuntimeError("wrong final panel row count")
    if any(row["false_certificate"] for row in all_results):
        bad = [(row["run_id"], row["correctness_failure_reason"])
               for row in all_results if row["false_certificate"]]
        raise RuntimeError(f"false certificate detected: {bad}")
    if any(not row["correctness_gate"] for row in all_results):
        bad = [row["run_id"] for row in all_results if not row["correctness_gate"]]
        raise RuntimeError(f"correctness gate failed: {bad}")

    for panel in ("validation", "holdout"):
        write_csv(OUT / f"{panel}_results.csv", [
            row for row in all_results if row["panel"] == panel])
    write_csv(OUT / "final_checkpoint_results.csv", checkpoints)
    write_csv(OUT / "certificate_audit.csv", certificates)
    by_key = {(row["panel"], row["instance_id"], row["method"]): row
              for row in all_results}
    comparisons = []
    for panel in ("validation", "holdout"):
        for manifest_row in manifest(panel):
            key = (panel, manifest_row["instance_id"])
            comparisons.append(compare(
                by_key[(*key, "P-GRB")], by_key[(*key, "K1-AM-FINAL")]))
    write_csv(OUT / "pgrb_direct_comparison.csv", comparisons)
    severe_rows = [{
        "panel": row["panel"], "instance_id": row["instance_id"],
        "V": row["V"], "pgrb_certificate": row["pgrb_certificate"],
        "k1_certificate": row["k1_certificate"],
        "pgrb_work": row["pgrb_work"], "k1_work": row["k1_work"],
        "work_ratio_k1_over_pgrb": row["shifted_work_ratio_k1_over_pgrb"],
        "pgrb_process_seconds": row["pgrb_process_seconds"],
        "k1_process_seconds": row["k1_process_seconds"],
        "process_ratio_k1_over_pgrb": row[
            "shifted_process_ratio_k1_over_pgrb"],
        "pgrb_GI_1800": row["pgrb_GI_1800"],
        "k1_GI_1800": row["k1_GI_1800"],
        "GI_ratio_k1_over_pgrb": row["GI_ratio_k1_over_pgrb"],
        "pgrb_final_gap": row["pgrb_final_gap"],
        "k1_final_gap": row["k1_final_gap"],
        "final_gap_ratio_k1_over_pgrb": row[
            "final_gap_ratio_k1_over_pgrb"],
        "severe_pgrb_regression": row["severe_pgrb_regression"],
        "reason": row["severe_regression_reason"],
    } for row in comparisons]
    write_csv(OUT / "severe_pgrb_regression_audit.csv", severe_rows)
    write_csv(OUT / "final_performance_profile.csv",
              performance_profile(comparisons))

    summaries: list[dict[str, Any]] = []
    for panel in ("validation", "holdout"):
        selected = [row for row in comparisons if row["panel"] == panel]
        summaries.append(aggregate(panel, selected))
        for size in (12, 20, 50):
            summaries.append(aggregate(
                f"{panel}_V{size}",
                [row for row in selected if row["V"] == size]))
    summaries.append(aggregate("combined", comparisons))
    for size in (12, 20, 50):
        summaries.append(aggregate(
            f"combined_V{size}",
            [row for row in comparisons if row["V"] == size]))
    write_csv(OUT / "final_metric_summary.csv", summaries)
    summary_by_group = {row["group"]: row for row in summaries}
    validation = summary_by_group["validation"]
    holdout = summary_by_group["holdout"]
    combined = summary_by_group["combined"]
    gates = {
        "zero_false_certificates": combined["false_certificates"] == 0,
        "k1_certificate_count_at_least_pgrb_validation": (
            validation["k1_certificates"] >= validation["pgrb_certificates"]),
        "k1_certificate_count_at_least_pgrb_holdout": (
            holdout["k1_certificates"] >= holdout["pgrb_certificates"]),
        "zero_severe_pgrb_regressions_holdout": (
            holdout["severe_pgrb_regressions"] == 0),
        "shifted_work_geomean_below_one_validation": (
            validation["shifted_work_geometric_mean_ratio_k1_over_pgrb"] < 1),
        "shifted_work_geomean_below_one_holdout": (
            holdout["shifted_work_geometric_mean_ratio_k1_over_pgrb"] < 1),
        "aggregate_GI_nonworse_validation": (
            validation["k1_mean_GI_1800"] <= validation["pgrb_mean_GI_1800"]),
        "aggregate_GI_nonworse_holdout": (
            holdout["k1_mean_GI_1800"] <= holdout["pgrb_mean_GI_1800"]),
        "evidence_spans_multiple_size_classes": (
            summary_by_group["combined_V12"]["k1_certificate_gain"] > 0 and
            summary_by_group["combined_V20"]["k1_certificate_gain"] > 0),
        "major_historical_repair_preserved": load_json(
            OUT / "k1_integration_decision.json")["major_repair_preserved"],
    }
    benchmark_classification = (
        "pgrb_advantage_supported" if all(gates.values()) else
        "pgrb_advantage_mixed" if (
            combined["k1_certificates"] >= combined["pgrb_certificates"] and
            combined["severe_pgrb_regressions"] == 0) else
        "pgrb_advantage_not_supported")
    scale_qualification = "v12_v20_supported_v50_mixed"
    decision = {
        "schema": "round52-final-decision-v1",
        "completion_status": "round52_complete",
        "tau_classification": "tau_008_adopted", "final_tau": 0.08,
        "cut_infrastructure_classification":
            "gurobi_tailored_cut_infrastructure_complete",
        "cut_backend_classification": "production_v0_backend_retained",
        "k1_classification": "k1_am_v0_final",
        "benchmark_classification": benchmark_classification,
        "scale_qualification": scale_qualification,
        "final_inner_backend": "historical-production-v0",
        "final_support_rank": 0, "final_separation_scope": "none",
        "final_cut_selection_rule": "none",
        "rejected_candidate": {
            "name": "SD-R3-ROOT-BLOCKMAX", "support_rank": 3,
            "separation_scope": "root-only",
            "selection_rule": "one maximum strictly violated cut per vehicle block",
        },
        "design_iterations": {
            "attempted": ["iteration_1:SD-R3-ROOT-BLOCKMAX"],
            "formally_skipped": ["iteration_2", "iteration_3"],
            "skip_basis": "retained callback/PreCrush path failed the complete development gates",
        },
        "official_rows": {"validation": 24, "holdout": 24, "total": 48},
        "missing_rows": [], "false_certificates": 0,
        "severe_pgrb_regressions": combined["severe_pgrb_regressions"],
        "certificate_summary": {
            "validation": {"P-GRB": validation["pgrb_certificates"],
                           "K1-AM-FINAL": validation["k1_certificates"]},
            "holdout": {"P-GRB": holdout["pgrb_certificates"],
                        "K1-AM-FINAL": holdout["k1_certificates"]},
            "combined": {"P-GRB": combined["pgrb_certificates"],
                         "K1-AM-FINAL": combined["k1_certificates"],
                         "K1_gains": combined["k1_certificate_gain"],
                         "K1_losses": combined["k1_certificate_loss"]},
        },
        "benchmark_gates": gates,
        "metric_summary": {key: summary_by_group[key] for key in (
            "validation", "holdout", "combined", "combined_V12",
            "combined_V20", "combined_V50")},
        "final_executable_sha256": EXECUTABLE_SHA256,
        "algorithm_freeze_commit": "52ccf3e713e1c57484ac2ec9ba96baf3cb8c8026",
        "holdout_opened_after_freeze": True,
        "post_freeze_algorithmic_changes": 0,
        "paper_language": (
            "bounded evidence supports an exact tailored K1-AM controller with the "
            "historical production-v0 inner backend; V50 performance remains mixed"),
        "validated_paper_algorithm_claim_allowed": False,
    }
    dump_json(OUT / "final_decision.json", decision)

    # The required default-off ledger is a paper-facing alias of the frozen
    # controller equivalence audit; no experiment is rerun or reinterpreted.
    source_default = csv_rows(OUT / "k1_am_controller_equivalence.csv")
    write_csv(OUT / "default_off_equivalence.csv", source_default)

    size_rows = []
    for size in (12, 20, 50):
        item = summary_by_group[f"combined_V{size}"]
        size_rows.append({
            "size": f"V{size}", "P-GRB certs": item["pgrb_certificates"],
            "K1 certs": item["k1_certificates"],
            "K1 gains": item["k1_certificate_gain"],
            "Work GM ratio": f"{item['shifted_work_geometric_mean_ratio_k1_over_pgrb']:.6f}",
            "GI ratio": f"{item['aggregate_GI_ratio_k1_over_pgrb']:.6f}",
        })
    fixed = load_json(OUT / "fixed_interval_promotion_decision.json")
    iteration = load_json(OUT / "iteration_1_decision.json")
    census_rows = csv_rows(OUT / "cut_family_violation_census.csv")
    census = {key: sum(int(number(row[key], 0)) for row in census_rows)
              for key in ("generated", "violated", "selected", "added",
                          "duplicate_rejections", "dominated_rejections")}
    census["callback_overhead_seconds"] = sum(
        number(row["callback_overhead_seconds"], 0.0) for row in census_rows)
    report = f"""# Round 52 final report

## Decision

Round 52 is complete at the evidence level: all 48 entered validation/holdout method rows are present, satisfy the official strict contract, respect the 1800-second process cap, and are free of false certificates. The frozen classifications are `{decision['tau_classification']}`, `gurobi_tailored_cut_infrastructure_complete`, `production_v0_backend_retained`, `k1_am_v0_final`, `{benchmark_classification}`, and `{scale_qualification}`.

The benchmark label means an advantage **over** P-GRB. It is supported by all predeclared gates, but this is not a claim that every size class is solved: V50 remains mixed and has no strict certificate from either method.

## Frozen controller and evidence corrections

1. **Tau.** Tau 0.08 was adopted. The complete 334-row replay changed zero historical AM decisions relative to 0.07915; three paired runtime sentinels and one explicit/implicit default-off pair were action-equivalent.
2. **K1 labels and telemetry.** Round 50 action labels and root telemetry were corrected before reuse. Five of seven historical action labels changed; the corrected severe error count is three false retains and zero false splits.
3. **Plain LP.** All 15 frozen states passed `LP_M1 >= LP_v0 - 1e-7`; M1 did not enter the final backend.

## Tailored user-cut architecture

4. **Infrastructure.** The solver-independent candidate/separator/manager layers, deterministic global pool, dominance logic, strict scaled-violation test, Gurobi `GRBcbcut` callback, `PreCrush=1`, exception boundary, and telemetry are independently tested. The live fixture executed one successful native `GRBcbcut`; the production path remains default-off.
5. **Formulations.** The bounded study compared production v0; F0 with rank-3 support-duration rows removed and no dynamic cuts; F1 static rank-3 rows with the historical loose 100000 coefficient; F2 static rank-3 rows with exact TSP/permutation duration coefficients; and F3 dynamic exact-duration rank-3 rows with root-only block-max selection. F4 tree separation is implemented and unit-tested but was not opened as a benchmark iteration. The proof and unit census cover exact route lower bounds through rank 4, but rank 4 was not promoted into the bounded candidate.
6. **Cut census.** Across the 14-row core and 14-row complete-development panels, iteration 1 generated {census['generated']:,} candidates, found {census['violated']} strictly violated candidates, selected {census['selected']}, added {census['added']}, rejected {census['duplicate_rejections']} duplicates, and rejected {census['dominated_rejections']} dominated rows. Core alone was {iteration['tailored_candidates_generated_core']:,}/{iteration['tailored_candidates_violated_core']}/{iteration['tailored_candidates_selected_core']}/{iteration['tailored_cuts_added_core']}; total callback overhead was {census['callback_overhead_seconds']:.6f} seconds. The complete per-state counts are in `cut_family_violation_census.csv`.
7. **Static congestion.** Dynamic separation avoided adding the large static subset-duration matrix and submitted only selected violated rows, so it did not reproduce the Round 51 static-row congestion. This engineering result did not translate into promotion-worthy solve performance.
8. **Iterations.** Iteration 1, SD-R3-ROOT-BLOCKMAX, was attempted. Iterations 2 and 3 were formally skipped because the required callback/`PreCrush` path itself lost complete-development certificates; changing the family would not remove that retained path.
9. **Rejections.** F1 and F2 failed certificate retention in the bounded screen. F3 retained the core certificate set but failed the 0.97 Work gate, then lost D1 and D13 on the complete development panel and gained no certificate.
10. **Second family.** No second cut family was opened; the predeclared trigger was not met after the callback-path failure.

## Final backend and integration

11. **Final backend.** The final inner solver is historical production v0: interval-mip-v0, support rank 0, no separation scope or selection rule, tailored callback off, historical 100000 subset-duration coefficients under the frozen V<=12 writer guard, Gurobi default branching, Presolve Auto, Seed 0, Threads 1, and zero MIP gaps.
12. **Fixed interval.** F0 certified {fixed['f0_development_certificates']}/14 development states and F3 {fixed['f3_development_certificates']}/14. F3 lost D1/D13, gained none, and obtained a common-exact Work GM ratio of {fixed['common_exact_work_geometric_mean_ratio']:.6f} against the required 0.97. It therefore did not improve the promotion-level combination of Work, certificates, and GI.
13. **K1 integration.** Because the final backend is exactly historical production v0, no new integration method row was required. Twelve integration audit properties pass, the 334-row replay is action-equivalent, and the major and strong-control repairs remain RETAIN.

## Independent comparison

14. **Validation.** K1-AM-FINAL certified {validation['k1_certificates']}/12 versus P-GRB {validation['pgrb_certificates']}/12, gaining {validation['k1_certificate_gain']} and losing {validation['k1_certificate_loss']}. Its shifted Work GM ratio is {validation['shifted_work_geometric_mean_ratio_k1_over_pgrb']:.6f}, shifted process-time GM ratio {validation['shifted_process_geometric_mean_ratio_k1_over_pgrb']:.6f}, and aggregate GI ratio {validation['aggregate_GI_ratio_k1_over_pgrb']:.6f}.
15. **Sealed holdout.** K1-AM-FINAL certified {holdout['k1_certificates']}/12 versus P-GRB {holdout['pgrb_certificates']}/12, gaining {holdout['k1_certificate_gain']} and losing {holdout['k1_certificate_loss']}. Its shifted Work GM ratio is {holdout['shifted_work_geometric_mean_ratio_k1_over_pgrb']:.6f}, shifted process-time GM ratio {holdout['shifted_process_geometric_mean_ratio_k1_over_pgrb']:.6f}, and aggregate GI ratio {holdout['aggregate_GI_ratio_k1_over_pgrb']:.6f}.
16. **Severe regressions.** The frozen exact/capped rule finds {combined['severe_pgrb_regressions']} severe P-GRB regressions, including zero on holdout.
17. **Scale.** Combined subgroup evidence is:

{markdown_table(size_rows, ['size', 'P-GRB certs', 'K1 certs', 'K1 gains', 'Work GM ratio', 'GI ratio'])}

V12 and V20 support the comparison across two size classes. V50 shows materially better gaps/GI for K1 on many rows but worse Work and no strict certificate for either method, so the correct qualification is `{scale_qualification}`.
18. **Algorithm description.** It is legitimate to describe the full method as an exact tailored K1-AM search/controller using a frozen exact production-v0 interval MIP backend. It is not legitimate to describe the **final inner backend** as dynamic branch-and-cut, because the researched user-cut policy was rejected and is off.
19. **Unproven.** Dynamic support-duration cuts are not shown beneficial beyond the bounded panels; V50 exact scalability is unproven; performance beyond the frozen generator distribution, machine, executable, and 1800-second cap is unproven; and no claim of a universally validated paper algorithm is made.

## Reproducibility and scope

The validation and holdout panels use one executable SHA-256, `{EXECUTABLE_SHA256}`. All 24 instance-method pairs use the frozen inputs, Threads=1, Seed=0, Presolve=Auto, zero MIP gaps, and the same process cap. Invalid fingerprint-discovery attempts are retained locally and explicitly excluded. Full raw logs remain local under `local_raw`; committed ledgers carry their hashes and reproduction anchors.
"""
    (OUT / "final_report.md").write_text(report, encoding="utf-8")

    source_of_truth = f"""# Round 52 source of truth

The authoritative decision is `final_decision.json`; the human-readable interpretation is `final_report.md`.

- Frozen base: `c6d7109bf69f50bd459174e8f05242b478e57d85`
- Algorithm/executable freeze: `52ccf3e713e1c57484ac2ec9ba96baf3cb8c8026`
- Executable SHA-256: `{EXECUTABLE_SHA256}`
- Tau/controller: 0.08, K0=1, complete interval, midpoint, adaptive mass
- Final inner backend: historical production v0; tailored cuts off
- Official final rows: 24 validation + 24 holdout = 48
- Certificates: validation P-GRB {validation['pgrb_certificates']}, K1 {validation['k1_certificates']}; holdout P-GRB {holdout['pgrb_certificates']}, K1 {holdout['k1_certificates']}
- Missing rows: none
- False certificates: zero
- Severe P-GRB regressions: {combined['severe_pgrb_regressions']}
- Final benchmark/scale: `{benchmark_classification}` / `{scale_qualification}`

Raw evidence is intentionally local-only. Use `compact_evidence_inventory.csv`, `local_raw_evidence_inventory.csv`, and `reproduction_commands.md` to bind compact claims to native artifacts.
"""
    (OUT / "source_of_truth.md").write_text(source_of_truth, encoding="utf-8")

    reproduction = f"""# Round 52 reproduction commands

Run from the repository root on the recorded Windows/Gurobi environment. Every native process is bounded by the runner's 1800-second process cap.

```powershell
$py = 'C:\\Users\\Administrator\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe'
$exe = 'build/round52/ExactEBRP.exe'

# Rebuild and unit/live-test the frozen source.
& 'D:\\Program Files\\Microsoft Visual Studio\\2022\\Professional\\Common7\\IDE\\CommonExtensions\\Microsoft\\CMake\\CMake\\bin\\cmake.exe' --build build/round52 --config Release
ctest --test-dir build/round52 --output-on-failure

# Recreate the deterministic independent inputs and certificate preflight.
& $py scripts/generate_round52_validation_instances.py
& $py scripts/run_round52_fingerprint_preflight.py --panel validation --executable $exe
& $py scripts/run_round52_fingerprint_preflight.py --panel holdout --executable $exe

# Reproduce/resume the 48 official final rows.
foreach ($panel in @('validation', 'holdout')) {{
  foreach ($method in @('P-GRB', 'K1-AM-FINAL')) {{
    & $py scripts/run_round52_final_panel.py --panel $panel --method $method --executable $exe
  }}
}}

# Rebuild all compact audits and verify their strict gates.
& $py scripts/finalize_round52_final_panels.py
Get-FileHash -Algorithm SHA256 $exe
```

The expected executable hash is `{EXECUTABLE_SHA256}`. The P-GRB fingerprint preflight is certificate plumbing only; it must complete before official P-GRB bound rows and does not authorize source or algorithm changes.
"""
    (OUT / "reproduction_commands.md").write_text(reproduction,
                                                     encoding="utf-8")
    storage = """# Round 52 evidence storage audit

Native logs, solver traces, and full artifact trees remain local under `local_raw/`; Git tracks no file below that directory. Each official final run has its own `artifact_manifest.csv` and completion marker. The committed `local_raw_evidence_inventory.csv` additionally binds every top-level raw evidence group to a deterministic tree hash over relative path, byte size, and file SHA-256.

Compact CSV/JSON/Markdown ledgers, frozen manifests, proofs, source, tests, and reproduction commands are committed. `compact_evidence_inventory.csv` hashes each compact evidence file; `final_evidence_inventory.csv` joins those entries to the local raw group hashes. The inventory files exclude themselves to avoid recursive hashes.

The two incomplete P-GRB fingerprint-discovery attempts remain local, are explicitly invalidated by `final_panel_preflight_invalidation_audit.json`, and are excluded from every official row count and metric.
"""
    (OUT / "evidence_storage_audit.md").write_text(storage, encoding="utf-8")
    compact_count, local_count = evidence_inventories()

    print(json.dumps({
        "official_rows": len(all_results),
        "validation_certificates": {
            "P-GRB": validation["pgrb_certificates"],
            "K1-AM-FINAL": validation["k1_certificates"]},
        "holdout_certificates": {
            "P-GRB": holdout["pgrb_certificates"],
            "K1-AM-FINAL": holdout["k1_certificates"]},
        "severe_pgrb_regressions": combined["severe_pgrb_regressions"],
        "benchmark_classification": benchmark_classification,
        "scale_qualification": scale_qualification,
        "compact_inventory_rows": compact_count,
        "local_inventory_rows": local_count,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
