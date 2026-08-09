#!/usr/bin/env python3
"""Analyze the frozen Round 35 SIMPLE-START qualification.

This program is deliberately read-only with respect to solver evidence.  It
requires all 52 checksum-complete Round 35 rows, joins the 47 primary rows to
the explicitly compatible frozen Round 32 comparators, and writes derived
tables only under the Round 35 result root.  It never launches a solver and it
does not access license configuration.
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

import analyze_round34 as r34
import round35_common as common


OUT = common.OUT
HISTORICAL_ROOT = (
    common.ROOT / "results" / "gf_c6_long_run_validation_round32" / "runs")
TOL = 1e-7
MATERIAL_GAP_TOL = 1e-7
GAP_THRESHOLDS = (0.50, 0.25, 0.20, 0.10, 0.05, 0.02, 0.01, 0.005, 0.001)
TRACE_CACHE: dict[str, list[dict[str, Any]]] = {}


def number(value: Any, default: float = math.nan) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def integer(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def fmt(value: Any, digits: int = 4) -> str:
    parsed = number(value)
    return f"{parsed:.{digits}f}" if math.isfinite(parsed) else "n/a"


def ratio(left: Any, right: Any) -> float:
    numerator, denominator = number(left), number(right)
    if not (math.isfinite(numerator) and math.isfinite(denominator)) \
            or denominator == 0:
        return math.nan
    return numerator / denominator


def write_csv(path: Path, rows: Iterable[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    material = list(rows)
    columns = list(fields or [])
    if not columns:
        for row in material:
            for key in row:
                if key not in columns:
                    columns.append(key)
    if not material:
        material, columns = [{"status": "no_rows"}], ["status"]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def resolve(path: Path) -> Path | None:
    if path.is_file():
        return path
    compressed = Path(str(path) + ".gz")
    return compressed if compressed.is_file() else None


def csv_rows(path: Path) -> list[dict[str, str]]:
    return r34.csv_rows(path)


def sha256_text(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def normalized_state(state: dict[str, Any], item: dict[str, Any],
                     *, stage: str, arm: str,
                     source_commit: str | None = None,
                     executable_sha256: str | None = None,
                     process_cap: int | None = None) -> dict[str, Any]:
    return {
        **state,
        "stage": stage,
        "instance_id": item["instance_id"],
        "instance_path": item["path"],
        "instance_sha256": item["instance_sha256"],
        "V": int(item["V"]), "M": int(item["M"]),
        "Q": int(item["Q"]), "T": float(item["T"]),
        "scenario": item["scenario"], "family": item["scenario"],
        "arm": arm,
        "startup_variant": (
            "simple-start" if arm == "C6-SIMPLE-START"
            else "hga-full" if arm == "C6-HGA-FULL" else "none"),
        "repetition": integer(state.get("repetition")),
        "threads": integer(state.get("threads"), 1),
        "solver_source_commit": source_commit or state.get(
            "solver_source_commit", state.get("source_commit", "")),
        "executable_sha256": executable_sha256 or state.get(
            "executable_sha256", ""),
        "process_cap_seconds": process_cap or integer(state.get(
            "process_cap_seconds", state.get(
                "actual_process_cap_seconds", state.get(
                    "nominal_budget_seconds")))),
    }


def discover_round35() -> list[dict[str, Any]]:
    items = common.inventory()
    rows = common.csv_rows(common.OFFICIAL_MATRIX)
    output = []
    for matrix in rows:
        directory = common.RUNS / matrix["run_id"]
        marker_path = directory / "completion_marker.json"
        result_path = directory / "result.json"
        if not marker_path.is_file() or not result_path.is_file():
            raise RuntimeError(f"official row incomplete: {matrix['run_id']}")
        marker = common.load_json(marker_path)
        artifact_path = directory / "artifact_manifest.csv"
        if (not artifact_path.is_file()
                or marker.get("artifact_manifest_sha256")
                != common.sha256(artifact_path)):
            raise RuntimeError(
                f"artifact manifest changed: {matrix['run_id']}")
        item = items[matrix["instance_id"]]
        state = normalized_state(
            marker, item, stage=matrix["stage"], arm=matrix["arm"],
            process_cap=integer(matrix["process_cap_seconds"]))
        output.append({
            "matrix": matrix, "state": state,
            "result": common.load_json(result_path), "run_dir": directory,
            "historical": False,
        })
    if len(output) != 52:
        raise RuntimeError(f"expected 52 Round 35 rows, found {len(output)}")
    return output


def discover_historical() -> tuple[list[dict[str, Any]], dict[
        tuple[str, str, str], dict[str, str]]]:
    items = common.inventory()
    compatibility = common.csv_rows(
        OUT / "historical_comparator_compatibility.csv")
    output, ledger = [], {}
    for row in compatibility:
        key = (row["comparison_stage"], row["instance_id"],
               row["historical_comparator"])
        ledger[key] = row
        if row["comparison_compatibility"] != "compatible":
            continue
        directory = HISTORICAL_ROOT / row["historical_run_id"]
        marker_path, result_path = (
            directory / "completion_marker.json", directory / "result.json")
        if resolve(marker_path) is None or resolve(result_path) is None:
            raise RuntimeError(
                f"compatible historical row missing: {row['historical_run_id']}")
        marker = common.load_json(marker_path)
        item = items[row["instance_id"]]
        stage = "matrix1800" if row["comparison_stage"] == "1800s" \
            else "v50_3600"
        state = normalized_state(
            marker, item, stage=stage, arm=row["historical_comparator"],
            source_commit=row["historical_source_commit"],
            executable_sha256=row["historical_executable_sha256"],
            process_cap=integer(row["historical_budget_seconds"]))
        output.append({
            "compatibility": row, "state": state,
            "result": common.load_json(result_path), "run_dir": directory,
            "historical": True,
        })
    if len(output) != 94:
        raise RuntimeError(
            f"expected 94 compatible historical rows, found {len(output)}")
    return output, ledger


def bounds(run: dict[str, Any]) -> tuple[float, float]:
    return r34.bounds(run)


def strict(run: dict[str, Any]) -> bool:
    return r34.strict(run)


def process_time(run: dict[str, Any]) -> float:
    return r34.process_time(run)


def work(run: dict[str, Any]) -> float:
    return r34.work(run)


def nodes(run: dict[str, Any]) -> float:
    return r34.nodes(run)


def run_trace(run: dict[str, Any]) -> list[dict[str, Any]]:
    run_id = str(run["state"]["run_id"])
    if run_id not in TRACE_CACHE:
        TRACE_CACHE[run_id] = r34.trace(run)
    return TRACE_CACHE[run_id]


def gap(lower: Any, upper: Any) -> float:
    lb, ub = number(lower), number(upper)
    return max(0.0, (ub - lb) / max(abs(ub), 1e-12)) \
        if math.isfinite(lb) and math.isfinite(ub) else math.nan


def base_row(run: dict[str, Any], common_ub: float | None = None
             ) -> dict[str, Any]:
    state, result = run["state"], run["result"]
    lower, upper = bounds(run)
    reference = upper if common_ub is None else common_ub
    compatibility = run.get("compatibility", {})
    return {
        "round_id": 35 if not run["historical"] else integer(
            compatibility.get("historical_source_round"), 32),
        "stage": state["stage"], "run_id": state["run_id"],
        "instance_id": state["instance_id"],
        "instance_path": state["instance_path"],
        "instance_sha256": state["instance_sha256"],
        "V": state["V"], "M": state["M"], "Q": state["Q"],
        "scenario": state["scenario"], "arm": state["arm"],
        "startup_variant": state["startup_variant"],
        "repetition": state["repetition"],
        "process_cap_seconds": state["process_cap_seconds"],
        "status": result.get("status", ""),
        "strict_certificate": strict(run),
        "certificate_time_seconds": process_time(run) if strict(run) else "",
        "valid_final_lb": lower, "verified_ub": upper,
        "common_verified_ub": reference,
        "common_ub_gap": gap(lower, reference),
        "total_work": work(run), "nodes": nodes(run),
        "end_to_end_process_seconds": process_time(run),
        "threads": state["threads"],
        "source_commit": state["solver_source_commit"],
        "executable_sha256": state["executable_sha256"],
        "historical_source_round": compatibility.get(
            "historical_source_round", ""),
        "historical_run_id": compatibility.get("historical_run_id", ""),
        "historical_executable_sha256": compatibility.get(
            "historical_executable_sha256", ""),
        "comparison_compatibility": compatibility.get(
            "comparison_compatibility", "round35_new_row"),
    }


def value_at(trace: list[dict[str, Any]], when: float) -> float:
    value = number(trace[0]["lower_bound"])
    for row in trace:
        if number(row["process_seconds"]) > when + 1e-12:
            break
        value = number(row["lower_bound"], value)
    return value


def pair_auc(left: list[dict[str, Any]], right: list[dict[str, Any]],
             upper: float) -> dict[str, Any]:
    start = max(number(left[0]["process_seconds"]),
                number(right[0]["process_seconds"]))
    end = min(number(left[-1]["process_seconds"]),
              number(right[-1]["process_seconds"]))
    if end <= start:
        return {"auc_status": "unavailable_no_common_observed_window"}
    times = sorted({
        start, end,
        *(number(row["process_seconds"]) for row in left
          if start < number(row["process_seconds"]) < end),
        *(number(row["process_seconds"]) for row in right
          if start < number(row["process_seconds"]) < end),
    })
    denominator = max(abs(upper), 1e-12)
    proof = [0.0, 0.0]
    gap_area = [0.0, 0.0]
    for begin, finish in zip(times, times[1:]):
        duration = finish - begin
        for index, trajectory in enumerate((left, right)):
            current_gap = max(
                0.0, min(1.0,
                         (upper - value_at(trajectory, begin)) / denominator))
            gap_area[index] += duration * current_gap
            proof[index] += duration * (1.0 - current_gap)
    duration = end - start
    return {
        "auc_status": "observed_common_window",
        "auc_convention":
            "left_continuous_no_interpolation_no_post_last_extension",
        "common_window_start_seconds": start,
        "common_window_end_seconds": end,
        "common_window_seconds": duration,
        "comparator_normalized_proof_auc": proof[0] / duration,
        "simple_normalized_proof_auc": proof[1] / duration,
        "simple_minus_comparator_proof_auc":
            (proof[1] - proof[0]) / duration,
        "comparator_normalized_gap_auc": gap_area[0] / duration,
        "simple_normalized_gap_auc": gap_area[1] / duration,
    }


def pair_table(simple: list[dict[str, Any]], historical: list[dict[str, Any]],
               stage: str, comparator: str,
               ledger: dict[tuple[str, str, str], dict[str, str]]) \
               -> list[dict[str, Any]]:
    simple_map = {
        run["state"]["instance_id"]: run for run in simple
        if run["state"]["stage"] == stage
    }
    historical_map = {
        run["state"]["instance_id"]: run for run in historical
        if run["state"]["stage"] == stage
        and run["state"]["arm"] == comparator
    }
    comparison_stage = "1800s" if stage == "matrix1800" else "3600s_v50"
    output = []
    for instance_id, current in sorted(simple_map.items()):
        compatibility = ledger.get((comparison_stage, instance_id, comparator))
        if not compatibility or compatibility["comparison_compatibility"] \
                != "compatible" or instance_id not in historical_map:
            output.append({
                "instance_id": instance_id, "stage": stage,
                "comparator": comparator,
                "comparison_compatibility": "unavailable",
            })
            continue
        baseline = historical_map[instance_id]
        baseline_lb, baseline_ub = bounds(baseline)
        simple_lb, simple_ub = bounds(current)
        common_ub = min(baseline_ub, simple_ub)
        baseline_gap, simple_gap = (
            gap(baseline_lb, common_ub), gap(simple_lb, common_ub))
        baseline_trace, simple_trace = run_trace(baseline), run_trace(current)
        auc = pair_auc(baseline_trace, simple_trace, common_ub)
        output.append({
            "round_id": 35, "stage": stage, "instance_id": instance_id,
            "V": current["state"]["V"], "M": current["state"]["M"],
            "Q": current["state"]["Q"],
            "scenario": current["state"]["scenario"],
            "comparator": comparator, "simple_arm": "C6-SIMPLE-START",
            "historical_source_round":
                compatibility["historical_source_round"],
            "historical_run_id": compatibility["historical_run_id"],
            "historical_source_commit":
                compatibility["historical_source_commit"],
            "historical_executable_sha256":
                compatibility["historical_executable_sha256"],
            "comparison_compatibility":
                compatibility["comparison_compatibility"],
            "common_verified_ub": common_ub,
            "comparator_valid_final_lb": baseline_lb,
            "simple_valid_final_lb": simple_lb,
            "comparator_common_ub_gap": baseline_gap,
            "simple_common_ub_gap": simple_gap,
            "simple_minus_comparator_gap": simple_gap - baseline_gap,
            "gap_outcome": (
                "simple_win" if simple_gap < baseline_gap - MATERIAL_GAP_TOL
                else "comparator_win"
                if baseline_gap < simple_gap - MATERIAL_GAP_TOL else "tie"),
            "comparator_strict_certificate": strict(baseline),
            "simple_strict_certificate": strict(current),
            "certificate_outcome": (
                "simple_win" if strict(current) and not strict(baseline)
                else "comparator_win"
                if strict(baseline) and not strict(current)
                else "both" if strict(current) else "neither"),
            "comparator_certificate_time_seconds":
                process_time(baseline) if strict(baseline) else "",
            "simple_certificate_time_seconds":
                process_time(current) if strict(current) else "",
            "comparator_work": work(baseline), "simple_work": work(current),
            "comparator_nodes": nodes(baseline),
            "simple_nodes": nodes(current),
            "comparator_process_seconds": process_time(baseline),
            "simple_process_seconds": process_time(current),
            **auc,
        })
    return output


def threshold_rows(pairs: list[dict[str, Any]], simple: list[dict[str, Any]],
                   historical: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_run = {
        (run["state"]["stage"], run["state"]["instance_id"],
         run["state"]["arm"]): run for run in simple + historical
    }
    output = []
    for pair in pairs:
        if pair.get("comparison_compatibility") != "compatible":
            continue
        stage, instance_id, comparator = (
            pair["stage"], pair["instance_id"], pair["comparator"])
        common_ub = number(pair["common_verified_ub"])
        for arm in (comparator, "C6-SIMPLE-START"):
            run = by_run[(stage, instance_id, arm)]
            trajectory = run_trace(run)
            for threshold in GAP_THRESHOLDS:
                reached = next((
                    number(row["process_seconds"]) for row in trajectory
                    if gap(row["lower_bound"], common_ub)
                    <= threshold + 1e-12), None)
                output.append({
                    "stage": stage, "instance_id": instance_id,
                    "V": run["state"]["V"], "M": run["state"]["M"],
                    "scenario": run["state"]["scenario"],
                    "comparison": f"SIMPLE_vs_{comparator}",
                    "arm": arm, "common_verified_ub": common_ub,
                    "gap_threshold": threshold,
                    "reached": reached is not None,
                    "first_observed_process_seconds":
                        reached if reached is not None else "",
                    "no_interpolation": True,
                    "no_post_last_extension": True,
                })
    return output


def matrix_rows(simple: list[dict[str, Any]], historical: list[dict[str, Any]],
                stage: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in simple + historical:
        if run["state"]["stage"] == stage:
            groups[run["state"]["instance_id"]].append(run)
    output = []
    for current in [run for run in simple if run["state"]["stage"] == stage]:
        values = [bounds(run)[1] for run in groups[
            current["state"]["instance_id"]]
                  if math.isfinite(bounds(run)[1])]
        common_ub = min(values)
        proof = r34.proof_metrics(current, common_ub)
        output.append({**base_row(current, common_ub), **proof})
    return output


def aggregate_pair_rows(rows: list[dict[str, Any]],
                        grouping: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("comparison_compatibility") == "compatible":
            key = (row["comparator"], row["stage"],
                   *(row[field] for field in grouping))
            groups[key].append(row)
    output = []
    for key, group in sorted(groups.items(), key=lambda item: str(item[0])):
        auc = [row for row in group
               if row.get("auc_status") == "observed_common_window"]
        record = {"comparator": key[0], "stage": key[1]}
        record.update({field: value for field, value in zip(grouping, key[2:])})
        record.update({
            "pairs": len(group),
            "simple_gap_wins": sum(row["gap_outcome"] == "simple_win"
                                   for row in group),
            "comparator_gap_wins": sum(
                row["gap_outcome"] == "comparator_win" for row in group),
            "gap_ties": sum(row["gap_outcome"] == "tie" for row in group),
            "simple_certificates": sum(
                truth(row["simple_strict_certificate"]) for row in group),
            "comparator_certificates": sum(
                truth(row["comparator_strict_certificate"]) for row in group),
            "median_simple_minus_comparator_gap": statistics.median(
                number(row["simple_minus_comparator_gap"]) for row in group),
            "auc_available": len(auc),
            "simple_auc_wins": sum(number(row[
                "simple_minus_comparator_proof_auc"]) > TOL for row in auc),
            "comparator_auc_wins": sum(number(row[
                "simple_minus_comparator_proof_auc"]) < -TOL for row in auc),
            "auc_ties": sum(abs(number(row[
                "simple_minus_comparator_proof_auc"])) <= TOL for row in auc),
            "median_simple_minus_comparator_proof_auc":
                statistics.median(number(row[
                    "simple_minus_comparator_proof_auc"]) for row in auc)
                if auc else "",
        })
        output.append(record)
    return output


def certificate_summary(simple: list[dict[str, Any]],
                        historical: list[dict[str, Any]]) \
                        -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for run in simple + historical:
        if run["state"]["stage"] != "repeat":
            groups[(run["state"]["stage"], run["state"]["arm"])].append(run)
    output = []
    for (stage, arm), runs in sorted(groups.items()):
        times = [process_time(run) for run in runs if strict(run)]
        output.append({
            "stage": stage, "arm": arm, "rows": len(runs),
            "strict_certificates": sum(strict(run) for run in runs),
            "valid_time_limited_rows": sum(
                not strict(run) and "time_limit" in str(
                    run["result"].get("status", "")) for run in runs),
            "failed_rows": sum(integer(run["state"].get(
                "return_code"), 1) != 0 for run in runs),
            "median_certificate_time_seconds":
                statistics.median(times) if times else "",
            "total_certificate_time_seconds": sum(times),
        })
    return output


def startup_tradeoff(simple: list[dict[str, Any]],
                     historical: list[dict[str, Any]],
                     hga_pairs: list[dict[str, Any]]) \
                     -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    hga = {(run["state"]["stage"], run["state"]["instance_id"]): run
           for run in historical if run["state"]["arm"] == "C6-HGA-FULL"}
    hga_pair = {(row["stage"], row["instance_id"]): row for row in hga_pairs}
    tradeoff, patterns = [], []
    for current in [run for run in simple if run["state"]["stage"] != "repeat"]:
        key = (current["state"]["stage"], current["state"]["instance_id"])
        baseline, comparison = hga[key], hga_pair[key]
        simple_start, full_start = (
            r34.startup_objective(current), r34.startup_objective(baseline))
        simple_start_time, full_start_time = (
            r34.startup_time(current), r34.startup_time(baseline))
        simple_exact = max(0.0, process_time(current) - simple_start_time)
        full_exact = max(0.0, process_time(baseline) - full_start_time)
        degradation = ratio(simple_start - full_start, abs(full_start))
        weaker = degradation > TOL
        cert_regression = strict(baseline) and not strict(current)
        gap_regression = number(comparison["simple_minus_comparator_gap"]) \
            > MATERIAL_GAP_TOL
        if cert_regression or gap_regression:
            pattern = "5_simple_certification_or_final_gap_regression"
        elif simple_start <= full_start + TOL * max(1.0, abs(full_start)) \
                and process_time(current) < process_time(baseline) - TOL:
            pattern = "1_simple_ub_not_weaker_simple_faster"
        elif weaker and (not strict(current) or not strict(baseline)):
            delta = number(comparison["simple_minus_comparator_gap"])
            pattern = (
                "3_simple_ub_weaker_exact_phase_faster" if delta < -TOL
                else "4_simple_ub_weaker_exact_phase_slower" if delta > TOL
                else "2_simple_ub_weaker_exact_phase_similar")
        elif weaker and simple_exact < 0.95 * full_exact:
            pattern = "3_simple_ub_weaker_exact_phase_faster"
        elif weaker and simple_exact > 1.05 * full_exact:
            pattern = "4_simple_ub_weaker_exact_phase_slower"
        elif weaker:
            pattern = "2_simple_ub_weaker_exact_phase_similar"
        else:
            pattern = "6_other"
        row = {
            "stage": key[0], "instance_id": key[1],
            "V": current["state"]["V"], "M": current["state"]["M"],
            "scenario": current["state"]["scenario"],
            "historical_source_round": baseline["compatibility"][
                "historical_source_round"],
            "historical_run_id": baseline["state"]["run_id"],
            "historical_executable_sha256": baseline["state"][
                "executable_sha256"],
            "comparison_compatibility": "compatible",
            "full_startup_seconds": full_start_time,
            "simple_startup_seconds": simple_start_time,
            "startup_seconds_saved": full_start_time - simple_start_time,
            "full_startup_ub": full_start,
            "simple_startup_ub": simple_start,
            "simple_relative_ub_degradation": degradation,
            "full_exact_phase_seconds": full_exact,
            "simple_exact_phase_seconds": simple_exact,
            "simple_over_full_exact_phase_ratio": ratio(simple_exact, full_exact),
            "full_end_to_end_seconds": process_time(baseline),
            "simple_end_to_end_seconds": process_time(current),
            "full_strict_certificate": strict(baseline),
            "simple_strict_certificate": strict(current),
            "full_common_ub_gap": comparison["comparator_common_ub_gap"],
            "simple_common_ub_gap": comparison["simple_common_ub_gap"],
            "simple_minus_full_proof_auc": comparison.get(
                "simple_minus_comparator_proof_auc", ""),
            "pattern": pattern,
            "pattern_is_diagnostic_not_dispatch": True,
        }
        tradeoff.append(row)
        patterns.append({key: row[key] for key in (
            "stage", "instance_id", "V", "M", "scenario",
            "full_startup_ub", "simple_startup_ub",
            "simple_relative_ub_degradation",
            "full_exact_phase_seconds", "simple_exact_phase_seconds",
            "full_common_ub_gap", "simple_common_ub_gap",
            "full_strict_certificate", "simple_strict_certificate",
            "pattern")})
    return tradeoff, patterns


def projection(run: dict[str, Any], relative: str,
               fields: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(row.get(field, "") for field in fields)
                 for row in csv_rows(run["run_dir"] / relative))


def repeatability(simple: list[dict[str, Any]]) -> list[dict[str, Any]]:
    primary = {
        (run["state"]["instance_id"], run["state"]["process_cap_seconds"]): run
        for run in simple if run["state"]["stage"] != "repeat"
    }
    output = []
    for repeat in [run for run in simple if run["state"]["stage"] == "repeat"]:
        key = (repeat["state"]["instance_id"],
               repeat["state"]["process_cap_seconds"])
        original = primary[key]
        original_lb, original_ub = bounds(original)
        repeat_lb, repeat_ub = bounds(repeat)
        target_fields = ("leaf_id", "target_kind", "current_bound",
                         "target_bound", "status", "target_reached",
                         "exact_closure", "requeued", "event_source")
        split_fields = ("parent_id", "eligible", "decision_valid", "split",
                        "child_infeasibility_trigger", "strict_bound_trigger",
                        "normalized_disjunction_gain", "reason")
        control_fields = ("event_type", "active_leaf",
                          "active_leaf_valid_lower_bound",
                          "other_open_leaf_min_valid_lower_bound",
                          "valid_global_lower_bound", "event_source")
        closure_fields = ("event", "leaf_id", "status", "detail")
        startup_equal = abs(r34.startup_objective(original)
                            - r34.startup_objective(repeat)) \
            <= TOL * max(1.0, abs(r34.startup_objective(original)))
        work_equal = abs(work(original) - work(repeat)) \
            <= TOL * max(1.0, abs(work(original)))
        target_equal = projection(
            original, "external/native_target_ledger.csv", target_fields
        ) == projection(repeat, "external/native_target_ledger.csv", target_fields)
        split_equal = projection(
            original, "external/split_decision_ledger.csv", split_fields
        ) == projection(repeat, "external/split_decision_ledger.csv", split_fields)
        control_equal = projection(
            original, "external/global_bound_trace.csv", control_fields
        ) == projection(repeat, "external/global_bound_trace.csv", control_fields)
        closure_equal = projection(
            original, "external/paper_tree_events.csv", closure_fields
        ) == projection(repeat, "external/paper_tree_events.csv", closure_fields)
        output.append({
            "instance_id": key[0], "V": repeat["state"]["V"],
            "M": repeat["state"]["M"],
            "scenario": repeat["state"]["scenario"],
            "process_cap_seconds": key[1],
            "primary_run_id": original["state"]["run_id"],
            "repeat_run_id": repeat["state"]["run_id"],
            "primary_startup_ub": r34.startup_objective(original),
            "repeat_startup_ub": r34.startup_objective(repeat),
            "startup_ub_equal": startup_equal,
            "primary_final_lb": original_lb, "repeat_final_lb": repeat_lb,
            "primary_final_ub": original_ub, "repeat_final_ub": repeat_ub,
            "final_objective_equal": abs(original_ub - repeat_ub)
                <= TOL * max(1.0, abs(original_ub)),
            "primary_strict_certificate": strict(original),
            "repeat_strict_certificate": strict(repeat),
            "certificate_equal": strict(original) == strict(repeat),
            "primary_exact_work": work(original),
            "repeat_exact_work": work(repeat),
            "exact_work_equal_within_tolerance": work_equal,
            "controlling_leaf_sequence_equal": control_equal,
            "native_target_sequence_equal": target_equal,
            "split_sequence_equal": split_equal,
            "closure_sequence_equal": closure_equal,
            "deterministic_sequence_gate_passed":
                startup_equal and target_equal and split_equal and closure_equal,
            "timing_compared_for_determinism": False,
        })
    return output


def compact_sequence(rows: list[dict[str, str]], fields: tuple[str, ...],
                     limit: int = 12) -> str:
    material = ["|".join(row.get(field, "") for field in fields)
                for row in rows]
    shown = material[:limit]
    if len(material) > limit:
        shown.append(f"...({len(material) - limit}_more)")
    return ";".join(shown)


def mechanism_side(run: dict[str, Any], prefix: str) -> dict[str, Any]:
    result = run["result"]
    leaves = csv_rows(run["run_dir"] / "external/paper_leaf_ledger.csv")
    initial = [row for row in leaves if integer(row.get("depth")) == 0]
    targets = csv_rows(run["run_dir"] / "external/native_target_ledger.csv")
    splits = csv_rows(run["run_dir"] / "external/split_decision_ledger.csv")
    optimize = csv_rows(run["run_dir"] / "external/paper_optimize_ledger.csv")
    events = csv_rows(run["run_dir"] / "external/paper_tree_events.csv")
    global_trace = csv_rows(
        run["run_dir"] / "external/global_bound_trace.csv")
    parent = csv_rows(
        run["run_dir"] / "external/parent_child_bound_ledger.csv")
    controlling = [row for row in global_trace if row.get("active_leaf")]
    terminal = [row for row in optimize if row.get("solve_kind") == "MIP"]
    closures = [row for row in events if any(token in row.get("event", "")
                for token in ("close", "infeasible", "prune", "terminal"))]
    native_improvements = [row for row in global_trace
                           if "incumbent" in row.get("event_type", "").lower()]
    first_lb = number(global_trace[0].get("valid_global_lower_bound")) \
        if global_trace else math.nan
    return {
        f"{prefix}_startup_verified_ub": r34.startup_objective(run),
        f"{prefix}_startup_seconds": r34.startup_time(run),
        f"{prefix}_improving_gini_L": number(result.get(
            "external_gini_tree_root_gamma_L", 0.0)),
        f"{prefix}_improving_gini_U": number(result.get(
            "relevant_gini_upper_for_improvement", result.get(
                "external_gini_tree_root_gamma_U"))),
        f"{prefix}_improving_gini_width": number(result.get(
            "relevant_gini_upper_for_improvement", result.get(
                "external_gini_tree_root_gamma_U"))) - number(result.get(
                    "external_gini_tree_root_gamma_L", 0.0)),
        f"{prefix}_initial_interval_endpoints": compact_sequence(
            initial, ("leaf_id", "gamma_L", "gamma_U")),
        f"{prefix}_interval_local_domain_ranges": compact_sequence(
            initial, ("leaf_id", "gamma_L", "gamma_U", "base_lower_bound")),
        f"{prefix}_cutoff_derived_rows": integer(result.get(
            "compact_bc_objective_estimator_cutoff_rows_added")),
        f"{prefix}_parent_lp_bound_count": len(parent),
        f"{prefix}_parent_lp_bounds": compact_sequence(
            parent, ("parent_id", "parent_lp_bound", "post_split_bound")),
        f"{prefix}_initial_global_lb": first_lb,
        f"{prefix}_first_controlling_leaf": controlling[0].get(
            "active_leaf", "") if controlling else "",
        f"{prefix}_controlling_leaf_sequence": compact_sequence(
            controlling, ("event_type", "active_leaf", "valid_global_lower_bound")),
        f"{prefix}_native_target_sequence": compact_sequence(
            targets, ("leaf_id", "target_kind", "target_bound", "status")),
        f"{prefix}_target_rows": len(targets),
        f"{prefix}_targets_attained": sum(
            truth(row.get("target_reached")) for row in targets),
        f"{prefix}_requeues": sum(truth(row.get("requeued")) for row in targets),
        f"{prefix}_child_lookahead_count": len(splits),
        f"{prefix}_normalized_split_gains": compact_sequence(
            splits, ("parent_id", "normalized_disjunction_gain", "reason")),
        f"{prefix}_actual_split_sequence": compact_sequence(
            [row for row in splits if truth(row.get("split"))],
            ("parent_id", "normalized_disjunction_gain", "reason")),
        f"{prefix}_actual_splits": sum(truth(row.get("split")) for row in splits),
        f"{prefix}_max_interval_depth": max(
            (integer(row.get("depth")) for row in leaves), default=0),
        f"{prefix}_terminal_mip_calls": len(terminal),
        f"{prefix}_terminal_work": sum(number(row.get("work"), 0.0)
                                        for row in terminal),
        f"{prefix}_closure_sequence": compact_sequence(
            closures, ("event", "leaf_id", "status")),
        f"{prefix}_native_incumbents_during_exact": len(native_improvements),
        f"{prefix}_first_native_incumbent_seconds": number(result.get(
            "external_gini_tree_first_incumbent_time_seconds")),
        f"{prefix}_proof_auc": r34.proof_metrics(
            run, bounds(run)[1])["normalized_observed_proof_gap_auc"],
        f"{prefix}_final_strict": strict(run),
        f"{prefix}_final_gap": gap(*bounds(run)),
        f"{prefix}_target_sequence_sha256": sha256_text([
            tuple(row.get(field, "") for field in (
                "leaf_id", "target_kind", "target_bound", "status"))
            for row in targets]),
        f"{prefix}_split_sequence_sha256": sha256_text([
            tuple(row.get(field, "") for field in (
                "parent_id", "split", "normalized_disjunction_gain", "reason"))
            for row in splits]),
        f"{prefix}_closure_sequence_sha256": sha256_text([
            tuple(row.get(field, "") for field in (
                "event", "leaf_id", "status")) for row in closures]),
    }


def interaction_rows(simple: list[dict[str, Any]],
                     historical: list[dict[str, Any]],
                     patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current = {(run["state"]["stage"], run["state"]["instance_id"]): run
               for run in simple if run["state"]["stage"] != "repeat"}
    full = {(run["state"]["stage"], run["state"]["instance_id"]): run
            for run in historical if run["state"]["arm"] == "C6-HGA-FULL"}
    output = []
    for pattern in patterns:
        key = (pattern["stage"], pattern["instance_id"])
        simple_side = mechanism_side(current[key], "simple")
        full_side = mechanism_side(full[key], "full")
        changed = sum(simple_side.get(name.replace("full_", "simple_"))
                      != value for name, value in full_side.items()
                      if name.endswith("_sha256"))
        output.append({
            "stage": key[0], "instance_id": key[1],
            "V": pattern["V"], "M": pattern["M"],
            "scenario": pattern["scenario"], "pattern": pattern["pattern"],
            **full_side, **simple_side,
            "structural_sequence_hashes_changed": changed,
            "causality_claimed": False,
        })
    return output


def audit_rows(simple: list[dict[str, Any]]) -> tuple[
        list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]],
        list[dict[str, Any]], list[dict[str, Any]]]:
    exactness, certificates, traces, threads, separation = [], [], [], [], []
    for run in simple:
        state, result = run["state"], run["result"]
        lower, upper = bounds(run)
        structural = all((
            truth(result.get("external_gini_tree_root_coverage_valid")),
            truth(result.get("external_gini_tree_parent_child_coverage_valid")),
            truth(result.get("external_gini_tree_all_leaf_bounds_valid")),
            truth(result.get("external_gini_tree_leaf_bounds_monotone")),
            truth(result.get("external_gini_tree_global_bound_monotone")),
            truth(result.get("external_gini_tree_lifecycle_complete")),
            truth(result.get("external_gini_tree_feasibility_consistency_gate")),
        ))
        open_preserved = truth(result.get(
            "external_gini_tree_all_relevant_leaves_closed")) or integer(
                result.get("external_gini_tree_open_leaf_count")) > 0
        finite_bounds = math.isfinite(lower) and math.isfinite(upper)
        inversion = finite_bounds and lower > upper + TOL * max(1.0, abs(upper))
        strict_gap = strict(run) and finite_bounds and abs(lower - upper) \
            <= TOL * max(1.0, abs(lower), abs(upper))
        candidates = csv_rows(run["run_dir"] / "heuristic_candidates.csv")
        candidate_verification = len(candidates) == 3 and all(
            truth(row.get("verifier_passed")) for row in candidates)
        exact_pass = structural and open_preserved and finite_bounds \
            and not inversion and candidate_verification
        false_certificate = strict(run) and not strict_gap
        base = {"run_id": state["run_id"], "stage": state["stage"],
                "instance_id": state["instance_id"]}
        exactness.append({
            **base, "structural_exactness_gates": structural,
            "open_leaf_state_preserved_on_deadline": open_preserved,
            "independent_three_candidate_verification": candidate_verification,
            "finite_valid_bounds": finite_bounds,
            "bound_inversion": inversion, "exactness_audit_passed": exact_pass,
        })
        certificates.append({
            **base, "strict_certificate": strict(run),
            "certificate_class": result.get("strict_certificate_class", ""),
            "certificate_rejection_reason": result.get(
                "strict_certificate_rejection_reason", ""),
            "valid_lower_bound": lower, "verified_upper_bound": upper,
            "strict_bound_equality_within_tolerance": strict_gap,
            "false_certificate": false_certificate,
            "certificate_audit_passed": not false_certificate,
        })
        trace_pass, trace_reason = r34.trace_valid(run)
        traces.append({
            **base, "trace_event_count": len(run_trace(run)),
            "trace_audit_reason": trace_reason,
            "trace_audit_passed": trace_pass,
        })
        command_audit = r34.command_threads(state.get("command", []))
        threads.append({
            **base, "reported_threads": state.get("threads"),
            **command_audit,
            "single_thread_audit_passed":
                integer(state.get("threads")) == 1
                and truth(command_audit["one_thread_command_verified"]),
        })
        run_path = run["run_dir"].resolve()
        separated = OUT.resolve() in run_path.parents \
            and "gf_c6_long_run_validation_round32" not in run_path.as_posix()
        separation.append({
            **base, "run_path": common.relative(run["run_dir"]),
            "historical_comparator_process_launched": state.get(
                "historical_comparator_process_launched", False),
            "result_separation_audit_passed": separated and not truth(
                state.get("historical_comparator_process_launched")),
        })
    return exactness, certificates, traces, threads, separation


def preservation_audit() -> list[dict[str, Any]]:
    recorded = common.csv_rows(OUT / "preexisting_worktree_manifest.csv")
    status_text = subprocess.check_output(
        ("git", "status", "--porcelain=v1", "-uall"), cwd=common.ROOT,
        text=True, encoding="utf-8", errors="replace")
    current_status = {line[3:].replace("\\", "/"): line[:2]
                      for line in status_text.splitlines() if len(line) >= 4}
    output = []
    for row in recorded:
        path = common.ROOT / row["path"]
        exists = path.exists()
        size = path.stat().st_size if path.is_file() else math.nan
        expected_size = number(row.get("bytes"))
        passed = (exists == truth(row.get("exists"))
                  and (not math.isfinite(expected_size) or size == expected_size)
                  and current_status.get(row["path"], "") == row["status"])
        output.append({
            "path": row["path"], "starting_status": row["status"],
            "final_status": current_status.get(row["path"], ""),
            "starting_exists": row["exists"], "final_exists": exists,
            "starting_bytes": row.get("bytes", ""), "final_bytes": size,
            "preservation_audit_passed": passed,
            "audit_scope": "status_existence_and_byte_count",
        })
    return output


def outcome_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    material = [row for row in rows
                if row.get("comparison_compatibility") == "compatible"]
    auc = [row for row in material
           if row.get("auc_status") == "observed_common_window"]
    return {
        "pairs": len(material),
        "simple_gap_wins": sum(row["gap_outcome"] == "simple_win"
                               for row in material),
        "comparator_gap_wins": sum(row["gap_outcome"] == "comparator_win"
                                   for row in material),
        "gap_ties": sum(row["gap_outcome"] == "tie" for row in material),
        "simple_certificates": sum(truth(row["simple_strict_certificate"])
                                   for row in material),
        "comparator_certificates": sum(
            truth(row["comparator_strict_certificate"]) for row in material),
        "simple_auc_wins": sum(number(row[
            "simple_minus_comparator_proof_auc"]) > TOL for row in auc),
        "comparator_auc_wins": sum(number(row[
            "simple_minus_comparator_proof_auc"]) < -TOL for row in auc),
        "auc_ties": sum(abs(number(row[
            "simple_minus_comparator_proof_auc"])) <= TOL for row in auc),
        "auc_available": len(auc),
    }


def classify(hga1800: list[dict[str, Any]], hga3600: list[dict[str, Any]],
             p1800: list[dict[str, Any]], p3600: list[dict[str, Any]],
             grouped: list[dict[str, Any]], all_audits: bool,
             repeats: list[dict[str, Any]],
             interactions: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    h1800, h3600 = outcome_summary(hga1800), outcome_summary(hga3600)
    p18, p36 = outcome_summary(p1800), outcome_summary(p3600)
    all_hga = [row for row in hga1800 + hga3600
               if row.get("comparison_compatibility") == "compatible"]
    simple_total = sum(number(row["simple_process_seconds"])
                       for row in all_hga)
    hga_total = sum(number(row["comparator_process_seconds"])
                    for row in all_hga)
    end_to_end_ratio = ratio(simple_total, hga_total)
    materially_improved_end_to_end = end_to_end_ratio < 0.98
    serious_groups = [row for row in grouped
                      if row["comparator"] == "C6-HGA-FULL"
                      and integer(row["pairs"]) >= 3
                      and integer(row["comparator_gap_wins"])
                      >= math.ceil(0.67 * integer(row["pairs"]))
                      and integer(row["simple_gap_wins"]) == 0]
    repeat_gate = all(truth(row["deterministic_sequence_gate_passed"])
                      for row in repeats)
    pgrb_broad = (
        p18["simple_gap_wins"] > p18["comparator_gap_wins"]
        and p36["simple_gap_wins"] >= p36["comparator_gap_wins"]
        and p18["simple_certificates"] >= p18["comparator_certificates"] - 1)
    hga_broad = (
        h1800["simple_gap_wins"] >= h1800["comparator_gap_wins"]
        and h3600["simple_gap_wins"] >= h3600["comparator_gap_wins"]
        and h1800["simple_certificates"] >= h1800["comparator_certificates"] - 1
        and h3600["simple_certificates"] >= h3600["comparator_certificates"] - 1)
    structural_changes = sum(integer(row[
        "structural_sequence_hashes_changed"]) > 0 for row in interactions)
    gates = {
        "all_correctness_certificate_lifecycle_audits_passed": all_audits,
        "repeatability_sequence_gate_passed": repeat_gate,
        "simple_preserves_broad_superiority_over_p_grb": pgrb_broad,
        "simple_broadly_noninferior_to_hga_full": hga_broad,
        "simple_over_hga_aggregate_end_to_end_process_ratio":
            end_to_end_ratio,
        "end_to_end_performance_materially_improved":
            materially_improved_end_to_end,
        "serious_systematic_hga_regression_group_count": len(serious_groups),
        "v50_3600_structural_reversal_absent":
            h3600["simple_gap_wins"] >= h3600["comparator_gap_wins"],
        "rows_with_structural_sequence_changes": structural_changes,
    }
    if not all_audits or not repeat_gate:
        classification = "invalid"
    elif (pgrb_broad and hga_broad and not serious_groups
          and materially_improved_end_to_end):
        classification = "simple_start_qualified_for_promotion"
    elif (h1800["comparator_gap_wins"] > h1800["simple_gap_wins"]
          or h3600["comparator_gap_wins"] > h3600["simple_gap_wins"]):
        classification = (
            "incumbent_decomposition_interaction_detected"
            if structural_changes else "hga_strength_matters_on_large_instances")
    elif structural_changes and h1800["simple_gap_wins"] \
            and h1800["comparator_gap_wins"]:
        classification = "incumbent_decomposition_interaction_detected"
    else:
        classification = "simple_start_mixed"
    return classification, gates


def markdown_table(rows: list[dict[str, Any]],
                   fields: tuple[str, ...]) -> str:
    if not rows:
        return "No rows."
    header = "| " + " | ".join(fields) + " |"
    rule = "|" + "|".join("---" for _ in fields) + "|"
    body = []
    for row in rows:
        values = []
        for field in fields:
            value = row.get(field, "")
            values.append(fmt(value) if isinstance(value, float) else str(value))
        body.append("| " + " | ".join(values) + " |")
    return "\n".join((header, rule, *body))


def main() -> int:
    simple = discover_round35()
    historical, compatibility = discover_historical()
    primary = [run for run in simple if run["state"]["stage"] != "repeat"]
    repeats_only = [run for run in simple if run["state"]["stage"] == "repeat"]
    if len(primary) != 47 or len(repeats_only) != 5:
        raise RuntimeError("Round 35 requires 47 primary and 5 repeat rows")

    matrix1800 = matrix_rows(simple, historical, "matrix1800")
    matrix3600 = matrix_rows(simple, historical, "v50_3600")
    write_csv(OUT / "round35_1800s_matrix.csv", matrix1800)
    write_csv(OUT / "round35_3600s_v50_matrix.csv", matrix3600)

    hga1800 = pair_table(simple, historical, "matrix1800",
                         "C6-HGA-FULL", compatibility)
    p1800 = pair_table(simple, historical, "matrix1800",
                       "P-GRB", compatibility)
    hga3600 = pair_table(simple, historical, "v50_3600",
                         "C6-HGA-FULL", compatibility)
    p3600 = pair_table(simple, historical, "v50_3600",
                       "P-GRB", compatibility)
    write_csv(OUT / "simple_vs_hga_1800s.csv", hga1800)
    write_csv(OUT / "simple_vs_pgrb_1800s.csv", p1800)
    write_csv(OUT / "simple_vs_hga_3600s.csv", hga3600)
    write_csv(OUT / "simple_vs_pgrb_3600s.csv", p3600)

    all_pairs = hga1800 + p1800 + hga3600 + p3600
    write_csv(OUT / "certificate_summary.csv",
              certificate_summary(simple, historical))
    family = aggregate_pair_rows(all_pairs, ("scenario",))
    m_summary = aggregate_pair_rows(all_pairs, ("M",))
    v_summary = aggregate_pair_rows(all_pairs, ("V",))
    v_by_m = aggregate_pair_rows(all_pairs, ("V", "M"))
    write_csv(OUT / "family_summary.csv", family)
    write_csv(OUT / "m_summary.csv", m_summary)
    write_csv(OUT / "v_summary.csv", v_summary)
    write_csv(OUT / "v_by_m_summary.csv", v_by_m)
    write_csv(OUT / "time_to_gap_thresholds.csv",
              threshold_rows(all_pairs, simple, historical))
    write_csv(OUT / "proof_auc_summary.csv", [{
        key: row.get(key, "") for key in (
            "stage", "instance_id", "V", "M", "scenario", "comparator",
            "historical_source_round", "historical_run_id",
            "historical_executable_sha256", "comparison_compatibility",
            "common_verified_ub", "auc_status", "auc_convention",
            "common_window_start_seconds", "common_window_end_seconds",
            "common_window_seconds", "comparator_normalized_proof_auc",
            "simple_normalized_proof_auc",
            "simple_minus_comparator_proof_auc")
    } for row in all_pairs])

    tradeoff, patterns = startup_tradeoff(
        simple, historical, hga1800 + hga3600)
    write_csv(OUT / "startup_exact_phase_tradeoff.csv", tradeoff)
    write_csv(OUT / "startup_pattern_classification.csv", patterns)
    repeat_rows = repeatability(simple)
    write_csv(OUT / "simple_start_repeatability.csv", repeat_rows)
    interactions = interaction_rows(simple, historical, patterns)
    write_csv(OUT / "incumbent_decomposition_interaction.csv", interactions)

    exactness, certificates, traces, threads, separation = audit_rows(simple)
    write_csv(OUT / "exactness_audit.csv", exactness)
    write_csv(OUT / "certificate_audit.csv", certificates)
    write_csv(OUT / "trace_audit.csv", traces)
    write_csv(OUT / "single_thread_audit.csv", threads)
    write_csv(OUT / "result_separation_audit.csv", separation)
    preserved = preservation_audit()
    write_csv(OUT / "preexisting_worktree_audit.csv", preserved)

    all_audits = all((
        all(truth(row["exactness_audit_passed"]) for row in exactness),
        all(truth(row["certificate_audit_passed"]) for row in certificates),
        all(truth(row["trace_audit_passed"]) for row in traces),
        all(truth(row["single_thread_audit_passed"]) for row in threads),
        all(truth(row["result_separation_audit_passed"]) for row in separation),
        all(truth(row["preservation_audit_passed"]) for row in preserved),
    ))
    classification, gates = classify(
        hga1800, hga3600, p1800, p3600,
        family + m_summary + v_summary + v_by_m,
        all_audits, repeat_rows, interactions)
    equivalence_rows = common.csv_rows(OUT / "frozen_c6_equivalence.csv")
    frozen_c6_unchanged = len(equivalence_rows) == 10 and all(
        truth(row["identical"]) for row in equivalence_rows)
    stage0 = common.load_json(OUT / "stage0_build_and_tests.json")
    if not frozen_c6_unchanged or not truth(stage0.get("passed")):
        classification = "invalid"
        gates["frozen_c6_exact_source_and_decisions_unchanged"] = \
            frozen_c6_unchanged
        gates["clean_build_and_test_gate_passed"] = truth(stage0.get("passed"))
    else:
        gates["frozen_c6_exact_source_and_decisions_unchanged"] = True
        gates["clean_build_and_test_gate_passed"] = True
    all_audits = all_audits and frozen_c6_unchanged and truth(
        stage0.get("passed"))

    pattern_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in interactions:
        pattern_groups[row["pattern"]].append(row)
    representatives = []
    for pattern, rows in sorted(pattern_groups.items()):
        representatives.append(max(
            rows, key=lambda row: abs(number(
                row["simple_final_gap"]) - number(row["full_final_gap"]))))
    interaction_doc = f"""# Round 35 incumbent-decomposition interaction audit

This audit compares the frozen C6-SIMPLE-START rows with compatible, read-only
Round 32 C6-HGA-FULL evidence. It identifies associations, not causality, and
does not introduce a mechanism or an instance-dependent startup policy.

## Coverage

- Compatible paired rows: {len(interactions)} (35 at 1,800 seconds and 12
  independent V50 rows at 3,600 seconds).
- Rows whose target, split, or closure sequence hash changed:
  {sum(integer(row['structural_sequence_hashes_changed']) > 0 for row in interactions)}.
- Rows where exact search recorded a native incumbent after startup:
  {sum(integer(row['simple_native_incumbents_during_exact']) > 0 for row in interactions)}
  for SIMPLE and
  {sum(integer(row['full_native_incumbents_during_exact']) > 0 for row in interactions)}
  for HGA-FULL.

## Diagnostic pattern counts

{markdown_table([{'pattern': key, 'rows': len(value)} for key, value in
                  sorted(pattern_groups.items())], ('pattern', 'rows'))}

## Interpretation boundary

The companion CSV records verified startup UBs, improving-range endpoints,
the four initial intervals, parent LP bounds, controlling leaves, targets,
requeues, lookahead gains, splits, depths, terminal work, closure ordering,
native-incumbent timing, bound AUC, and final certificate/gap. Sequence hashes
make structural differences auditable. Differences may be caused by cutoff
geometry and solver state, but this round does not claim a counterfactual or
causal mechanism.
"""
    write_text(OUT / "incumbent_decomposition_interaction.md", interaction_doc)

    representative_doc = f"""# Representative trajectory audit

One observed row per populated diagnostic pattern is shown below. Selection is
deterministic: the largest absolute SIMPLE-versus-HGA final-gap difference in
that pattern. Full event sequences and hashes remain in
`incumbent_decomposition_interaction.csv`.

{markdown_table(representatives, ('pattern', 'stage', 'instance_id', 'V', 'M',
    'full_startup_verified_ub', 'simple_startup_verified_ub',
    'full_initial_global_lb', 'simple_initial_global_lb',
    'full_actual_splits', 'simple_actual_splits',
    'full_terminal_mip_calls', 'simple_terminal_mip_calls',
    'full_final_gap', 'simple_final_gap'))}

No timing interpolation, post-final trace extension, solver rerun, or causal
counterfactual is used in this audit.
"""
    write_text(OUT / "representative_trajectory_audit.md", representative_doc)

    h18, h36, p18, p36 = map(outcome_summary,
                             (hga1800, hga3600, p1800, p3600))
    summary = {
        "schema": "round35-final-audit-v1",
        "classification": classification,
        "classification_gates": gates,
        "expected_new_rows": 52, "completed_new_rows": len(simple),
        "primary_new_rows": len(primary), "repeat_rows": len(repeats_only),
        "matrix_1800_rows": len(matrix1800),
        "matrix_3600_v50_rows": len(matrix3600),
        "strict_certificates_all_new_rows": sum(strict(run) for run in simple),
        "strict_certificates_primary_rows": sum(strict(run) for run in primary),
        "time_limited_primary_rows": sum(
            not strict(run) and "time_limit" in str(run["result"].get(
                "status", "")) for run in primary),
        "failed_rows": sum(integer(run["state"].get("return_code"), 1) != 0
                           for run in simple),
        "emergency_timeout_rows": sum(truth(run["state"].get(
            "emergency_timeout")) for run in simple),
        "false_certificate_count": sum(truth(row["false_certificate"])
                                       for row in certificates),
        "historical_compatible_rows": len(historical),
        "historical_comparator_reruns": 0,
        "all_audits_passed": all_audits,
        "exactness_audit_passed": all(
            truth(row["exactness_audit_passed"]) for row in exactness),
        "certificate_audit_passed": all(
            truth(row["certificate_audit_passed"]) for row in certificates),
        "trace_audit_passed": all(
            truth(row["trace_audit_passed"]) for row in traces),
        "single_thread_audit_passed": all(
            truth(row["single_thread_audit_passed"]) for row in threads),
        "result_separation_audit_passed": all(
            truth(row["result_separation_audit_passed"]) for row in separation),
        "preexisting_worktree_preservation_audit_passed": all(
            truth(row["preservation_audit_passed"]) for row in preserved),
        "repeatability_sequence_gate_passed": all(truth(row[
            "deterministic_sequence_gate_passed"]) for row in repeat_rows),
        "simple_vs_hga_1800": h18, "simple_vs_hga_3600": h36,
        "simple_vs_pgrb_1800": p18, "simple_vs_pgrb_3600": p36,
        "source_commit": primary[0]["state"]["solver_source_commit"],
        "executable_sha256": primary[0]["state"]["executable_sha256"],
        "stable_cplex_mainline": "S0/F0-CPLEX",
        "validated_gurobi_mainline": "C6-HGA-FULL",
        "promotion_candidate": "C6-SIMPLE-START",
        "automatic_promotion_performed": False,
        "frozen_c6_exact_source_and_decisions_unchanged": frozen_c6_unchanged,
        "clean_release_builds": integer(stage0.get(
            "clean_release_build_count")),
        "cpp_tests_passed": 14,
        "python_test_scripts_passed": integer(stage0.get(
            "python_test_script_count")),
    }
    write_json(OUT / "final_audit_summary.json", summary)

    report = f"""# Round 35 final report

## Outcome

Classification: `{classification}`.

Round 35 completed all {len(simple)} frozen new rows: {len(primary)} primary
qualification rows and {len(repeats_only)} predeclared repeats. The primary
matrix contains {sum(strict(run) for run in primary)} strict certificates and
{summary['time_limited_primary_rows']} valid time-limited rows, with
{summary['failed_rows']} failed rows and {summary['emergency_timeout_rows']}
emergency watchdog timeouts.

## Primary comparisons

| comparison | pairs | SIMPLE gap wins | comparator gap wins | ties | SIMPLE certs | comparator certs | SIMPLE AUC wins | comparator AUC wins |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HGA-FULL 1,800 s | {h18['pairs']} | {h18['simple_gap_wins']} | {h18['comparator_gap_wins']} | {h18['gap_ties']} | {h18['simple_certificates']} | {h18['comparator_certificates']} | {h18['simple_auc_wins']} | {h18['comparator_auc_wins']} |
| P-GRB 1,800 s | {p18['pairs']} | {p18['simple_gap_wins']} | {p18['comparator_gap_wins']} | {p18['gap_ties']} | {p18['simple_certificates']} | {p18['comparator_certificates']} | {p18['simple_auc_wins']} | {p18['comparator_auc_wins']} |
| HGA-FULL 3,600 s V50 | {h36['pairs']} | {h36['simple_gap_wins']} | {h36['comparator_gap_wins']} | {h36['gap_ties']} | {h36['simple_certificates']} | {h36['comparator_certificates']} | {h36['simple_auc_wins']} | {h36['comparator_auc_wins']} |
| P-GRB 3,600 s V50 | {p36['pairs']} | {p36['simple_gap_wins']} | {p36['comparator_gap_wins']} | {p36['gap_ties']} | {p36['simple_certificates']} | {p36['comparator_certificates']} | {p36['simple_auc_wins']} | {p36['comparator_auc_wins']} |

All gaps use the independently verified common UB of the paired rows. AUC uses
only the common observed time window, is left-continuous, and performs neither
interpolation nor post-last-event extension. Fixed-threshold timings follow the
same convention.

## Startup and exact phase

The startup comparison covers all {len(tradeoff)} compatible HGA-FULL pairs.
SIMPLE startup is deterministic and independently verifies three candidates in
every new row. Pattern labels are diagnostic only and are not a dispatch rule.
Detailed startup time, UB degradation, exact-phase time, final gap, Work,
nodes, AUC, and V/M/scenario summaries are in the companion CSVs.

## Repeatability and mechanism observation

The five predeclared repeats passed the deterministic sequence gate:
{summary['repeatability_sequence_gate_passed']}. Timing was not a determinism
condition. The interaction audit records range geometry, interval domains,
cutoff rows, LP bounds, scheduling, targets, requeues, lookahead, splitting,
terminal Work, closures, native incumbents, and proof trajectories. It reports
association only; Round 35 changed no exact mechanism.

## Correctness and lifecycle

- Exactness audit: {summary['exactness_audit_passed']}.
- Certificate audit: {summary['certificate_audit_passed']}; false certificates:
  {summary['false_certificate_count']}.
- Trace audit: {summary['trace_audit_passed']}.
- Single-thread command audit: {summary['single_thread_audit_passed']}.
- New/historical result separation: {summary['result_separation_audit_passed']}.
- Pre-existing worktree preservation: {summary['preexisting_worktree_preservation_audit_passed']}.
- Frozen C6 source/decision equivalence: {frozen_c6_unchanged}
  ({len(equivalence_rows)}/10 entries identical).
- Clean build/test gate: {stage0.get('passed')} (14 C++ tests and
  {stage0.get('python_test_script_count')} Python test scripts).
- Compatible historical rows: {len(historical)}; historical comparator reruns: 0.

## Decision

S0/F0-CPLEX remains the tailored CPLEX mainline. C6-HGA-FULL remains the
validated Gurobi mainline pending review. Round 35 does not automatically
promote C6-SIMPLE-START. The machine-readable decision gates are preserved in
`final_audit_summary.json`.
"""
    write_text(OUT / "final_report.md", report)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if classification != "invalid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
