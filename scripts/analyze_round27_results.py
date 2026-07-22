#!/usr/bin/env python3
"""Build the Round 27 result tables, audits, package manifest, and report."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any, Iterable

import run_round27_experiments as frozen


ROOT = frozen.ROOT
OUT = frozen.OUT
RUNS = OUT / "runs"


def result_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def truth(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def open_csv(path: Path) -> tuple[Any, Any]:
    if path.is_file():
        stream = path.open(newline="", encoding="utf-8")
        return stream, csv.DictReader(stream)
    compressed = Path(str(path) + ".gz")
    if compressed.is_file():
        stream = gzip.open(compressed, "rt", newline="", encoding="utf-8")
        return stream, csv.DictReader(stream)
    return None, None


def write_csv(path: Path, rows: Iterable[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    material = list(rows)
    if fields is None:
        fields = list(material[0]) if material else ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)


def verified(result: dict[str, Any]) -> bool:
    verification = result.get("verification", {})
    return bool(result.get("verifier_passed") or
                verification.get("original_solution_feasible"))


def external_gates(result: dict[str, Any]) -> bool:
    return all(truth(result.get(name)) for name in (
        "external_gini_tree_root_coverage_valid",
        "external_gini_tree_parent_child_coverage_valid",
        "external_gini_tree_all_leaf_bounds_valid",
        "external_gini_tree_global_bound_monotone",
        "external_gini_tree_leaf_bounds_monotone",
        "external_gini_tree_lifecycle_complete",
        "external_gini_tree_feasibility_consistency_gate",
    ))


def progress_points(run_dir: Path, arm: str,
                    result: dict[str, Any]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    if arm == "P-GRB":
        stream, reader = open_csv(run_dir / "progress.csv")
        if reader:
            with stream:
                for row in reader:
                    if truth(row.get("best_bound_available")) and finite(row.get("best_bound")):
                        points.append((float(row["elapsed_runtime_seconds"]),
                                       float(row["best_bound"])))
    elif arm == "C0-LEGACY":
        stream, reader = open_csv(run_dir / "external/external_tree_events.csv")
        shift = float(result.get("hga_wall_time_seconds") or
                      result.get("incumbent_generation_time_seconds") or 0.0)
        if reader:
            with stream:
                for row in reader:
                    if finite(row.get("global_lb")):
                        points.append((shift + float(row["elapsed_seconds"]),
                                       float(row["global_lb"])))
    elif arm == "C2-PAPER":
        stream, reader = open_csv(run_dir / "external/paper_tree_events.csv")
        shift = float(result.get("hga_wall_time_seconds") or 0.0)
        if reader:
            with stream:
                for row in reader:
                    if finite(row.get("global_lb")):
                        points.append((shift + float(row["telemetry_seconds"]),
                                       float(row["global_lb"])))
    points.sort()
    return points


def bound_auc(points: list[tuple[float, float]], final_lb: Any,
              common_ub: float, horizon: float) -> float | str:
    if horizon <= 0 or not finite(final_lb) or abs(common_ub) <= 1e-12:
        return ""
    series: list[tuple[float, float]] = [(0.0, 1.0)]
    for timestamp, lower_bound in points:
        timestamp = max(0.0, min(horizon, timestamp))
        gap = max(0.0, (common_ub - lower_bound) / abs(common_ub))
        series.append((timestamp, gap))
    final_gap = max(0.0, (common_ub - float(final_lb)) / abs(common_ub))
    series.append((horizon, final_gap))
    series.sort()
    # At duplicate times the last observation wins, then a right-continuous
    # bound process is integrated. This reports 1 - normalized gap area.
    collapsed: list[tuple[float, float]] = []
    for item in series:
        if collapsed and abs(collapsed[-1][0] - item[0]) <= 1e-12:
            collapsed[-1] = item
        else:
            collapsed.append(item)
    area = 0.0
    for (left_t, left_gap), (right_t, _) in zip(collapsed, collapsed[1:]):
        area += (right_t - left_t) * left_gap
    return 1.0 - area / horizon


def extract_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not RUNS.is_dir():
        return rows
    for run_dir in sorted(path for path in RUNS.iterdir() if path.is_dir()):
        command_path = run_dir / "command.json"
        state_path = run_dir / "run_state.json"
        if not command_path.is_file() or not state_path.is_file():
            continue
        command = frozen.load_json(command_path)
        stage = str(command.get("stage", ""))
        arm = str(command.get("arm", ""))
        if stage not in ("stage1", "stage2", "stage3"):
            continue
        state = frozen.load_json(state_path)
        result_path = run_dir / "result.json"
        result = result_object(result_path) if result_path.is_file() else {}
        external = arm in ("C0-LEGACY", "C2-PAPER")
        process_ok = (state.get("return_code") == 0 and bool(result) and
                      state.get("sensitive_marker_scan_passed") is True)
        gates = external_gates(result) if external and result.get(
            "external_gini_tree_attempted") else (arm == "HGA" or not external)
        witness = verified(result)
        authoritative = process_ok and witness and gates
        ub = (result.get("external_gini_tree_verified_upper_bound")
              if external and finite(result.get("external_gini_tree_verified_upper_bound"))
              else result.get("hga_verified_objective")
              if arm == "HGA" and finite(result.get("hga_verified_objective"))
              else result.get("objective"))
        lb = (result.get("external_gini_tree_global_lower_bound")
              if external and finite(result.get("external_gini_tree_global_lower_bound"))
              else result.get("lower_bound"))
        row = {
            "stage": stage, "instance": command.get("instance", ""),
            "family": command.get("family", ""), "V": command.get("V", ""),
            "arm": arm, "repetition": command.get("repetition", 0),
            "horizon_seconds": command.get("budget_seconds", ""),
            "return_code": state.get("return_code", ""),
            "runner_wall_seconds": state.get("runner_wall_seconds", ""),
            "emergency_timeout": state.get("emergency_timeout", False),
            "result_exists": bool(result), "status": result.get("status", "missing_result"),
            "completed_process": process_ok, "authoritative": authoritative,
            "verified_witness": witness, "correctness_gates": gates,
            "strict_certificate": bool(result.get(
                "external_gini_tree_strict_certified",
                result.get("strict_certified_original_problem", False))) and authoritative,
            "certificate_class": result.get(
                "external_gini_tree_certificate_class",
                result.get("strict_certificate_class", "")),
            "certificate_wall_seconds": result.get("final_process_wall_time_seconds", "")
                if result.get("external_gini_tree_strict_certified") else "",
            "verified_ub": ub if witness and finite(ub) else "",
            "valid_final_lb": lb if authoritative and finite(lb) else "",
            "common_ub": "", "common_ub_gap": "", "bound_progress_auc": "",
            "process_wall_seconds": result.get(
                "final_process_wall_time_seconds", state.get("runner_wall_seconds", "")),
            "work": result.get("external_gini_tree_work",
                               result.get("gurobi_work", "")),
            "lp_relaxation_count": result.get("external_gini_tree_lp_relaxation_count", 0),
            "lp_work": result.get("external_gini_tree_lp_work", 0),
            "terminal_mip_leaf_count": result.get(
                "external_gini_tree_terminal_mip_leaf_count", 0),
            "terminal_mip_optimize_count": result.get(
                "external_gini_tree_terminal_mip_optimize_count", 0),
            "terminal_mip_work": result.get("external_gini_tree_terminal_mip_work", 0),
            "split_count": result.get("external_gini_tree_split_count", 0),
            "optimize_count": result.get("external_gini_tree_optimize_count",
                                         result.get("gurobi_optimize_count", 0)),
            "model_count": result.get("external_gini_tree_model_count",
                                      result.get("gurobi_model_count", 0)),
            "model_read_count": result.get("external_gini_tree_model_read_count",
                                           result.get("gurobi_model_read_count", 0)),
            "model_build_count": result.get(
                "external_gini_tree_canonical_artifact_generation_count", 0),
            "model_free_count": result.get("external_gini_tree_model_free_count",
                                           result.get("gurobi_model_free_count", 0)),
            "environment_count": result.get("external_gini_tree_environment_count",
                                            result.get("gurobi_environment_count", 0)),
            "environment_free_count": result.get(
                "external_gini_tree_environment_free_count",
                result.get("gurobi_environment_free_count", 0)),
            "peak_memory_gb": result.get("external_gini_tree_peak_memory_gb",
                                         result.get("gurobi_max_mem_used_gb", "")),
            "final_stagnation_seconds": result.get(
                "external_gini_tree_final_stagnation_seconds", ""),
            "open_leaf_count": result.get("external_gini_tree_open_leaf_count", ""),
            "closed_leaf_count": result.get("external_gini_tree_closed_leaf_count", ""),
            "global_deadline_interruptions": result.get(
                "external_gini_tree_global_deadline_interruption_count", 0),
            "same_leaf_restarts": result.get("external_gini_tree_same_leaf_resume_count", 0),
            "fresh_restarts": result.get("external_gini_tree_fresh_restart_count", 0),
            "child_restarts": result.get("external_gini_tree_child_restart_count", 0),
            "attempt_count": result.get("external_gini_tree_attempt_count", 0),
            "hga_stop_mode": result.get("hga_stop_mode", ""),
            "hga_generations": result.get("hga_total_generations", 0),
            "hga_no_improve_generations": result.get(
                "hga_generations_since_improvement", 0),
            "hga_improvement_count": result.get("hga_objective_improvement_count", 0),
            "hga_decoder_calls": result.get("hga_decoder_calls", 0),
            "hga_final_fitness": result.get("hga_final_fitness", ""),
            "hga_verified_objective": result.get("hga_verified_objective", ""),
            "hga_wall_time_seconds": result.get("hga_wall_time_seconds", ""),
            "result_path": frozen.relative(result_path) if result_path.is_file() else "",
            "run_path": frozen.relative(run_dir),
            "_result": result, "_run_dir": run_dir,
        }
        rows.append(row)
    return rows


def add_common_metrics(rows: list[dict[str, Any]]) -> None:
    common: dict[tuple[str, str], float] = {}
    for row in rows:
        if row["stage"] not in ("stage2", "stage3") or not finite(row["verified_ub"]):
            continue
        key = (str(row["stage"]), str(row["instance"]))
        common[key] = min(common.get(key, math.inf), float(row["verified_ub"]))
    for row in rows:
        if row["stage"] not in ("stage2", "stage3"):
            continue
        ub = common.get((str(row["stage"]), str(row["instance"])))
        if ub is None:
            continue
        row["common_ub"] = ub
        if finite(row["valid_final_lb"]):
            row["common_ub_gap"] = max(
                0.0, (ub - float(row["valid_final_lb"])) / abs(ub))
            row["bound_progress_auc"] = bound_auc(
                progress_points(row["_run_dir"], str(row["arm"]), row["_result"]),
                row["valid_final_lb"], ub, float(row["horizon_seconds"]))


PUBLIC_FIELDS = [
    "stage", "instance", "family", "V", "arm", "repetition",
    "horizon_seconds", "return_code", "runner_wall_seconds", "emergency_timeout",
    "result_exists", "status", "completed_process", "authoritative",
    "verified_witness", "correctness_gates", "strict_certificate",
    "certificate_class", "certificate_wall_seconds", "verified_ub",
    "valid_final_lb", "common_ub", "common_ub_gap", "bound_progress_auc",
    "process_wall_seconds", "work", "lp_relaxation_count", "lp_work",
    "terminal_mip_leaf_count", "terminal_mip_optimize_count", "terminal_mip_work",
    "split_count", "optimize_count", "model_count", "model_read_count",
    "model_build_count", "model_free_count", "environment_count",
    "environment_free_count", "peak_memory_gb", "final_stagnation_seconds",
    "open_leaf_count", "closed_leaf_count", "global_deadline_interruptions",
    "same_leaf_restarts", "fresh_restarts", "child_restarts", "attempt_count",
    "hga_stop_mode", "hga_generations", "hga_no_improve_generations",
    "hga_improvement_count", "hga_decoder_calls", "hga_final_fitness",
    "hga_verified_objective", "hga_wall_time_seconds", "result_path", "run_path",
]


def pair_rows(rows: list[dict[str, Any]], other_arm: str) -> list[dict[str, Any]]:
    official = [row for row in rows if row["stage"] in ("stage2", "stage3")]
    keyed = {(row["stage"], row["instance"], row["arm"]): row for row in official}
    output: list[dict[str, Any]] = []
    for c2 in (row for row in official if row["arm"] == "C2-PAPER"):
        other = keyed.get((c2["stage"], c2["instance"], other_arm))
        if other is None:
            continue
        def delta(field: str) -> Any:
            return (float(c2[field]) - float(other[field])
                    if finite(c2[field]) and finite(other[field]) else "")
        output.append({
            "stage": c2["stage"], "instance": c2["instance"],
            "comparison": f"C2-PAPER minus {other_arm}",
            "other_strict": other["strict_certificate"],
            "c2_strict": c2["strict_certificate"],
            "other_verified_ub": other["verified_ub"], "c2_verified_ub": c2["verified_ub"],
            "other_final_lb": other["valid_final_lb"], "c2_final_lb": c2["valid_final_lb"],
            "other_common_ub_gap": other["common_ub_gap"],
            "c2_common_ub_gap": c2["common_ub_gap"],
            "gap_delta": delta("common_ub_gap"),
            "other_bound_auc": other["bound_progress_auc"],
            "c2_bound_auc": c2["bound_progress_auc"],
            "auc_delta": delta("bound_progress_auc"),
            "other_work": other["work"], "c2_work": c2["work"],
            "work_delta": delta("work"),
        })
    return output


def trajectory_hash(run_dir: Path) -> str:
    path = run_dir / "hga_generations.csv"
    if path.is_file():
        return frozen.sha256(path)
    path = Path(str(path) + ".gz")
    if path.is_file():
        digest = hashlib.sha256()
        with gzip.open(path, "rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
    return ""


def exactness_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        if row["arm"] != "C2-PAPER" or row["stage"] not in ("stage2", "stage3"):
            continue
        result = row["_result"]
        checks = {
            "root_coverage": result.get("external_gini_tree_root_coverage_valid", False),
            "parent_child_coverage": result.get(
                "external_gini_tree_parent_child_coverage_valid", False),
            "all_bounds_valid": result.get("external_gini_tree_all_leaf_bounds_valid", False),
            "global_bound_monotone": result.get(
                "external_gini_tree_global_bound_monotone", False),
            "leaf_bounds_monotone": result.get(
                "external_gini_tree_leaf_bounds_monotone", False),
            "lifecycle_complete": result.get("external_gini_tree_lifecycle_complete", False),
            "verified_incumbent": verified(result),
            "no_same_leaf_restart": row["same_leaf_restarts"] == 0,
            "no_attempt_scheduling": row["attempt_count"] == 0,
            "terminal_mip_once": row["terminal_mip_leaf_count"] ==
                                  row["terminal_mip_optimize_count"],
        }
        output.append({
            "stage": row["stage"], "instance": row["instance"],
            **checks, "passed": bool(row["result_exists"] and all(checks.values())),
            "strict_certificate": row["strict_certificate"],
            "open_leaf_count": row["open_leaf_count"],
        })
    return output


def make_manifest() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(path for path in OUT.rglob("*") if path.is_file() and
                       path.name != "evidence_package_manifest.csv"):
        rows.append({
            "path": frozen.relative(path), "bytes": path.stat().st_size,
            "sha256": frozen.sha256(path),
            "kind": "lossless_gzip" if path.suffix == ".gz" else path.suffix.lstrip("."),
        })
    return rows


def fmt(value: Any, digits: int = 6) -> str:
    return f"{float(value):.{digits}g}" if finite(value) else "unavailable"


def main() -> int:
    rows = extract_rows()
    add_common_metrics(rows)
    stage1 = [row for row in rows if row["stage"] == "stage1"]
    stage2 = [row for row in rows if row["stage"] == "stage2"]
    stage3 = [row for row in rows if row["stage"] == "stage3"]
    write_csv(OUT / "stage1_hga_results.csv", stage1, PUBLIC_FIELDS)
    write_csv(OUT / "stage2_300s_results.csv", stage2, PUBLIC_FIELDS)
    write_csv(OUT / "stage3_v50_smoke.csv", stage3, PUBLIC_FIELDS)

    repeat_rows: list[dict[str, Any]] = []
    v12 = [row for row in stage1 if row["instance"] == "V12_M2"]
    for row in v12:
        repeat_rows.append({
            "instance": row["instance"], "repetition": row["repetition"],
            "generations": row["hga_generations"],
            "no_improve_generations": row["hga_no_improve_generations"],
            "final_fitness": row["hga_final_fitness"],
            "verified_objective": row["hga_verified_objective"],
            "decoder_calls": row["hga_decoder_calls"],
            "trajectory_restored_sha256": trajectory_hash(row["_run_dir"]),
            "identity_with_first": not v12 or all(
                row[field] == v12[0][field] for field in (
                    "hga_generations", "hga_final_fitness",
                    "hga_verified_objective", "hga_decoder_calls")) and
                trajectory_hash(row["_run_dir"]) == trajectory_hash(v12[0]["_run_dir"]),
        })
    write_csv(OUT / "hga_repeatability.csv", repeat_rows)

    p_pairs = pair_rows(rows, "P-GRB")
    c0_pairs = pair_rows(rows, "C0-LEGACY")
    write_csv(OUT / "p_grb_vs_c2.csv", p_pairs)
    write_csv(OUT / "c0_vs_c2.csv", c0_pairs)
    exact = exactness_rows(rows)
    write_csv(OUT / "exactness_audit.csv", exact)

    lifecycle = [{key: row[key] for key in (
        "stage", "instance", "arm", "status", "authoritative", "work",
        "lp_relaxation_count", "lp_work", "terminal_mip_leaf_count",
        "terminal_mip_optimize_count", "terminal_mip_work", "split_count",
        "optimize_count", "model_count", "model_read_count", "model_build_count",
        "model_free_count", "environment_count", "environment_free_count",
        "peak_memory_gb", "same_leaf_restarts", "fresh_restarts", "child_restarts",
        "global_deadline_interruptions", "open_leaf_count", "closed_leaf_count",
    )} for row in rows if row["stage"] in ("stage2", "stage3")]
    write_csv(OUT / "lifecycle_and_resource_summary.csv", lifecycle)

    completed = sum(row["completed_process"] for row in rows)
    failed = sum(not row["completed_process"] for row in rows)
    time_limited = sum(
        bool(row["emergency_timeout"]) or "time" in str(row["status"]).lower() or
        int(row["global_deadline_interruptions"] or 0) > 0 for row in rows)
    excluded = sum(not row["authoritative"] for row in rows)
    c2_rows = [row for row in stage2 + stage3 if row["arm"] == "C2-PAPER"]
    exact_valid = bool(exact) and all(row["passed"] for row in exact)
    v12_c2 = [row for row in c2_rows if row["instance"] in ("V12_M1", "V12_M2")]
    v12_closed = len(v12_c2) == 2 and all(row["strict_certificate"] for row in v12_c2)
    difficult = [row for row in c0_pairs if row["instance"] in (
        "high_imbalance_seed3202", "moderate_seed3302", "tight_T_seed3101")]
    gap_deltas = [float(row["gap_delta"]) for row in difficult if finite(row["gap_delta"])]
    auc_deltas = [float(row["auc_delta"]) for row in difficult if finite(row["auc_delta"])]
    median_gap_delta = median(gap_deltas) if gap_deltas else ""
    median_auc_delta = median(auc_deltas) if auc_deltas else ""
    static_rows = list(csv.DictReader((OUT / "forbidden_internal_budget_scan.csv").open(
        newline="", encoding="utf-8")))
    static_pass = all(truth(row["pass"]) for row in static_rows)
    repeat_pass = len(repeat_rows) == 2 and all(truth(row["identity_with_first"])
                                                for row in repeat_rows)
    if not static_pass or not exact_valid:
        classification = "invalid"
    elif (v12_closed and finite(median_gap_delta) and finite(median_auc_delta) and
          float(median_gap_delta) <= 0.02 and float(median_auc_delta) >= -0.10):
        classification = "approximately_reproduced"
    else:
        classification = "paper_compatible_but_performance_risky"

    totals: dict[str, dict[str, float]] = {}
    for arm in ("P-GRB", "C0-LEGACY", "C2-PAPER"):
        selected = [row for row in stage2 + stage3 if row["arm"] == arm]
        totals[arm] = {field: sum(float(row[field]) for row in selected if finite(row[field]))
                       for field in ("work", "lp_relaxation_count", "lp_work",
                                     "terminal_mip_optimize_count", "terminal_mip_work",
                                     "split_count", "model_read_count", "model_build_count")}
        memories = [float(row["peak_memory_gb"]) for row in selected
                    if finite(row["peak_memory_gb"])]
        totals[arm]["maximum_peak_memory_gb"] = max(memories) if memories else 0.0

    audit = {
        "schema": "round27-final-audit-v1", "classification": classification,
        "stable_mainline_decision": "no_promotion_round27",
        "paper_compatibility_passed": static_pass,
        "exactness_passed": exact_valid, "hga_repeatability_passed": repeat_pass,
        "official_expected_rows": 21, "official_observed_rows": len(rows),
        "completed": completed, "failed": failed, "time_limited": time_limited,
        "excluded": excluded, "stage1_rows": len(stage1),
        "stage2_rows": len(stage2), "stage3_rows": len(stage3),
        "V12_C2_strict_certificates": sum(row["strict_certificate"] for row in v12_c2),
        "difficult_V20_median_C2_minus_C0_gap": median_gap_delta,
        "difficult_V20_median_C2_minus_C0_AUC": median_auc_delta,
        "resource_totals": totals,
        "unresolved_performance_issue": (
            "none observed in the short matrix" if classification == "approximately_reproduced"
            else "generation-stagnation or complete LP/MIP events lose short-horizon bound progress"),
    }
    frozen.json_write(OUT / "final_audit_summary.json", audit)

    hga_lines = "\n".join(
        f"- {row['instance']} rep {row['repetition']}: {row['hga_generations']} generations, "
        f"{row['hga_no_improve_generations']} final non-improving generations, "
        f"UB {fmt(row['hga_verified_objective'])}, {row['hga_decoder_calls']} decoder calls, "
        f"{fmt(row['hga_wall_time_seconds'])} s telemetry."
        for row in stage1)
    v12_lines = "\n".join(
        f"- {row['instance']}: strict={row['strict_certificate']}, LB={fmt(row['valid_final_lb'])}, "
        f"UB={fmt(row['verified_ub'])}, gap={fmt(row['common_ub_gap'])}, "
        f"wall={fmt(row['process_wall_seconds'])} s."
        for row in v12_c2)
    v50 = next((row for row in stage3 if row["arm"] == "C2-PAPER"), None)
    report = f"""# Round 27 final report

## Outcome

Classification: **{classification}**. C2 is not promoted; the stable mainline
is unchanged. The paper-compatibility static audit is {static_pass}, the
dynamic exactness/lifecycle audit is {exact_valid}, and deterministic HGA
repeatability is {repeat_pass}.

## Frozen algorithm

C2 fixes seed 20260626 and stops HGA only after 2,000 consecutive completed
generations without strict global-best fitness improvement. No wall-clock
predicate is present in that loop; wall time is telemetry. The exact phase
selects the minimum-valid-bound leaf, solves its complete LP relaxation,
solves both eligible midpoint-child LPs, atomically splits only for child LP
infeasibility or a strict certificate-tolerance bound gain, and otherwise
optimizes the complete terminal interval MIP exactly once. An overall-deadline
interruption leaves that leaf open and stops the whole tree.

## HGA qualification

{hga_lines or '- No completed HGA qualification rows.'}

## V12 certificates

{v12_lines or '- No completed C2 V12 rows.'}

## Difficult V20 comparison

Across available high-imbalance, moderate, and tight-T pairs, median C2-minus-C0
common-UB gap is {fmt(median_gap_delta)} and median C2-minus-C0 bound-progress
AUC is {fmt(median_auc_delta)}. Pairwise evidence is in `c0_vs_c2.csv`; the
plain-Gurobi comparison is in `p_grb_vs_c2.csv`.

## V50 smoke

{('- C2 status=' + str(v50['status']) + ', authoritative=' + str(v50['authoritative']) +
   ', LB=' + fmt(v50['valid_final_lb']) + ', UB=' + fmt(v50['verified_ub']) +
   ', gap=' + fmt(v50['common_ub_gap']) + ', peak memory=' +
   fmt(v50['peak_memory_gb']) + ' GB, lifecycle=' + str(v50['correctness_gates']) + '.')
  if v50 else '- No completed C2 V50 row.'}

## Run accounting and resources

The official matrix contains {len(rows)}/21 observed rows: {completed} completed,
{failed} process failures, {time_limited} time-limited/interrupted, and
{excluded} excluded from authoritative quantitative comparison. Aggregate Work,
LP Work/count, terminal-MIP Work/count, splits, model reads/builds, and maximum
peak memory by arm are serialized in `final_audit_summary.json` and the
per-run values in `lifecycle_and_resource_summary.csv`.

## Exactness and compatibility

The LP relaxation is a valid lower bound for its unchanged interval MIP; child
bounds inherit valid parent bounds; atomic interval replacement preserves
coverage; declining a split retains and solves the entire parent MIP; LP
statuses never serve as integer certificates; interrupted terminal leaves stay
open; and the global bound remains the minimum valid relevant-leaf bound.
Strict certification requires every relevant leaf closed. C2 contains no
internal seconds, Work, node, solution, attempt, or retry scheduling decision.
The only event TimeLimit is the remaining overall experiment deadline.

Unresolved performance issue: {audit['unresolved_performance_issue']}.
"""
    (OUT / "final_report.md").write_text(report, encoding="utf-8")
    manifest = make_manifest()
    write_csv(OUT / "evidence_package_manifest.csv", manifest)
    print(json.dumps(audit, indent=2, sort_keys=True))
    return 0 if len(rows) == 21 and static_pass and repeat_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
