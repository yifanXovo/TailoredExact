#!/usr/bin/env python3
"""Freeze and analyze the sealed Round 44 qualification stages."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import analyze_round44_stage3 as stage3
import round43_analysis as historical
import round44_common as common


FINAL_TAG = "final"
CHECKPOINTS = (300.0, 1200.0, 3600.0)
GAP_LEVELS = (0.10, 0.05, 0.01, 0.001)


def freeze_final() -> None:
    development = common.load_json(
        common.OUT / "stage3_development_selection.json")
    lifted = common.load_json(common.OUT / "stage4_disposition.json")
    engineering = common.load_json(common.OUT / "stage5_disposition.json")
    selected = "noadaptive"
    passed = development["passing_tags"]
    if selected not in passed:
        raise RuntimeError("selected candidate did not pass development")
    if lifted["selected_lifted_cut_mode"] != "off":
        raise RuntimeError("unexpected lifted-cut disposition")
    config = common.candidate_identity(
        execution="algorithm", lookahead="fixed-d1", injection="all",
        scope="parent", family="no-adaptive", rho_f=.5, rho_m=.007,
        rho_h=.0004, rank1="off",
        mip_starts=engineering["mip_start_mode"],
        consolidation=engineering["frontier_consolidation_mode"])
    freeze = {
        "schema": "round44-final-candidate-freeze-v1",
        "selected_candidate": selected,
        "configuration": config,
        "executable_sha256": common.sha256(common.EXE),
        "solver_contract": {
            "gurobi": "13.0.2", "threads": 1, "seed": 0,
            "presolve": "Auto", "mip_gap": 0.0,
            "mip_gap_abs": 0.0, "small_cap_seconds": 3600,
            "additional_v12_cap_seconds": 7200,
            "v20_cap_seconds": 3600,
        },
        "selection_basis": {
            "development_work_gmean": next(
                row["shifted_work_gmean"]
                for row in development["dispositions"]
                if row["tag"] == selected),
            "rank1": "complete normalized CGLP no-cut result",
            "mip_start_mode": engineering["mip_start_mode"],
            "consolidation_mode":
                engineering["frontier_consolidation_mode"],
        },
        "pre_frozen_validation_fallbacks": [{
            **common.candidate_identity(
                execution="algorithm", lookahead="fixed-d1",
                injection="all", scope="parent", family="veto",
                rho_f=.5, rho_m=.007, rho_h=.0004, rank1="off",
                mip_starts="off", consolidation="off"),
            "tag": "veto-f05",
        }],
        "validation_results_observed": False,
        "holdout_results_observed": False,
        "external_results_observed": False,
        "no_post_validation_tuning": True,
    }
    common.write_json(common.OUT / "final_candidate_freeze.json", freeze)


def activate_fallback() -> None:
    """Bind the pre-frozen veto fallback to the rebuilt qualification binary."""
    source_path = common.OUT / "final_candidate_freeze.json"
    primary_path = common.OUT / "validation_disposition.json"
    source = common.load_json(source_path)
    primary = common.load_json(primary_path)
    if primary.get("passes_all_gates"):
        raise RuntimeError("fallback activation requires failed primary validation")
    matches = [row for row in source["pre_frozen_validation_fallbacks"]
               if row.get("tag") == "veto-f05"]
    if len(matches) != 1:
        raise RuntimeError("exactly one pre-frozen veto-f05 fallback is required")
    config = dict(matches[0])
    config.pop("tag", None)
    common.write_json(
        common.OUT / "fallback_candidate_activation_freeze.json", {
            "schema": "round44-fallback-candidate-activation-freeze-v1",
            "selected_candidate": "veto-f05",
            "configuration": config,
            "executable_sha256": common.sha256(common.EXE),
            "source_final_candidate_freeze_sha256": common.sha256(source_path),
            "primary_validation_disposition_sha256": common.sha256(primary_path),
            "primary_validation_passed": False,
            "frozen_before_fallback_validation": True,
            "fallback_validation_results_observed": False,
            "holdout_results_observed": False,
            "external_results_observed": False,
            "activation_is_selection_not_tuning": True,
            "no_post_validation_parameter_change": True,
            "solver_contract": source["solver_contract"],
        })


def seal_negative_terminal() -> None:
    """Seal downstream panels without opening them after both frozen failures."""
    primary = common.load_json(common.OUT / "validation_disposition.json")
    fallback = common.load_json(
        common.OUT / "validation_fallback_disposition.json")
    if primary.get("passes_all_gates") or fallback.get("passes_all_gates"):
        raise RuntimeError("negative terminal requires both frozen candidates to fail")
    reason = "not_opened_due_to_failure_of_all_pre_frozen_validation_candidates"
    blocked_row = {
        "instance_id": "not_opened", "run_id": reason,
        "status": "not_opened", "reason": reason,
        "correctness": "not_applicable", "certified": False,
        "right_censored": False, "false_certificate": False,
    }
    for name, phase in (("holdout_comparison.csv", "holdout"),
                        ("additional_v12_comparison.csv", "additional_v12"),
                        ("v20_profile_comparison.csv", "v20")):
        common.write_csv(common.OUT / name, [{"phase": phase, **blocked_row}])
    common.write_json(common.OUT / "holdout_disposition.json", {
        "schema": "round44-holdout-disposition-v1", "stage": "holdout",
        "status": "not_opened", "reason": reason,
        "passes_all_gates": False, "row_count": 0,
        "shifted_work_gmean": None, "shifted_time_gmean": None,
        "sealed_until_validation_passes": True,
    })
    common.write_json(common.OUT / "additional_v12_disposition.json", {
        "schema": "round44-additional-v12-disposition-v1",
        "status": "not_opened", "reason": reason,
        "passes_all_gates": False, "row_count": 0,
        "shifted_work_gmean": None,
        "requires_passing_holdout": True,
    })
    common.write_json(common.OUT / "v20_disposition.json", {
        "schema": "round44-v20-disposition-v1", "status": "not_opened",
        "reason": reason, "passes_qualification": False, "row_count": 0,
        "candidate_certified_rows": 0, "pgrb_certified_rows": 0,
        "candidate_lower_gap_integral_rows": 0,
        "zero_false_certificates": True,
        "no_candidate_specific_memory_or_engineering_failure": True,
        "no_severe_fully_solved_pgrb_regression": True,
        "requires_passing_holdout": True,
    })
    common.write_json(common.OUT / "qualification_terminal_gate.json", {
        "schema": "round44-qualification-terminal-gate-v1",
        "terminal_classification": "bounded_systematic_negative_result",
        "scale_qualification": "small_panel_only",
        "primary_candidate": "noadaptive",
        "primary_validation_passed": False,
        "pre_frozen_fallback": "veto-f05",
        "fallback_validation_passed": False,
        "all_pre_frozen_candidates_exhausted": True,
        "holdout_opened": False, "additional_v12_opened": False,
        "v20_opened": False, "post_validation_tuning": False,
        "promotion": "none",
    })


def candidate_directory(stage: str, instance_id: str,
                        candidate: str = "primary") -> Path:
    if candidate == "veto-f05" and stage == "validation":
        return common.RUNS / f"validation-fallback__{instance_id}__veto-f05"
    tag = "veto-f05" if candidate == "veto-f05" else FINAL_TAG
    return common.RUNS / f"{stage}__{instance_id}__{tag}"


def frozen_small_reference(instance_id: str, arm: str) -> dict[str, Any]:
    """Use Round 40 dev references and the frozen all-24 validation sources."""
    try:
        return historical.historical_reference(instance_id, arm)
    except KeyError:
        if arm == "P-GRB":
            directory = (common.ROOT / "results" /
                         "gf_small_hard_light_round39" / "runs" /
                         f"primary__{instance_id}__p_grb")
        else:
            directory = (common.ROOT / "results" /
                         "gf_regression_adaptive_round40" / "runs" /
                         f"ub_geometry__{instance_id}__c6_hga_full_k4")
        return historical.load_metrics(
            directory, arm, "frozen_round39_40_all24_reference")


def correctness(metric: dict[str, Any], result: dict[str, Any],
                command: dict[str, Any], marker: dict[str, Any],
                *, candidate: bool) -> bool:
    exact_tree = (not candidate or (
        common.truth(result.get("external_gini_tree_root_coverage_valid")) and
        common.truth(result.get(
            "external_gini_tree_global_bound_monotone", True))))
    fail_closed = (metric["certified"] or
                   metric["status"] not in {"optimal", "OPTIMAL"})
    return (
        marker.get("complete") is True and
        not command.get("invalidated", False) and
        not metric["false_certificate"] and
        metric["parameter_roundtrip_valid"] and exact_tree and fail_closed and
        (not metric["certified"] or metric["verified_incumbent"]))


def small_row(stage: str, instance_id: str,
              candidate: str = "primary") -> dict[str, Any]:
    directory = candidate_directory(stage, instance_id, candidate)
    label = "veto-f05" if candidate == "veto-f05" else FINAL_TAG
    metric = historical.load_metrics(directory, label, "round44_final")
    result = common.load_json(directory / "result.json")
    command = common.load_json(directory / "command.json")
    marker = common.load_json(directory / "completion_marker.json")
    pgrb = frozen_small_reference(instance_id, "P-GRB")
    c6 = frozen_small_reference(instance_id, "C6")
    rw = stage3.shifted(metric["work"], pgrb["work"], stage3.S_W)
    rt = stage3.shifted(
        metric["process_seconds"], pgrb["process_seconds"], stage3.S_T)
    p_over_c6 = stage3.shifted(pgrb["work"], c6["work"], stage3.S_W)
    advantage_applies = p_over_c6 >= 5.0 and (
        pgrb["process_seconds"] > stage3.S_T)
    p_over_candidate = stage3.shifted(
        pgrb["work"], metric["work"], stage3.S_W)
    return {
        "stage": stage,
        "tag": "noadaptive" if candidate == "primary" else candidate,
        "instance_id": instance_id,
        "run_id": directory.name,
        "executable_sha256": metric["executable_sha256"],
        "correctness": correctness(
            metric, result, command, marker, candidate=True),
        "certified": metric["certified"],
        "right_censored": metric["right_censored"],
        "failure_reason": metric["failure_reason"],
        "verified_incumbent": metric["verified_incumbent"],
        "false_certificate": metric["false_certificate"],
        "parameter_roundtrip_valid": metric["parameter_roundtrip_valid"],
        "root_coverage_valid": common.truth(result.get(
            "external_gini_tree_root_coverage_valid")),
        "global_bound_monotone": common.truth(result.get(
            "external_gini_tree_global_bound_monotone", True)),
        "work": metric["work"],
        "process_seconds": metric["process_seconds"],
        "nodes": metric["nodes"],
        "lp_jobs": metric["lp_jobs"],
        "terminal_mip_jobs": metric["terminal_mip_jobs"],
        "pgrb_work": pgrb["work"],
        "pgrb_process_seconds": pgrb["process_seconds"],
        "pgrb_reference_provenance": pgrb["provenance"],
        "pgrb_reference_run": pgrb["run_dir"],
        "shifted_work_over_pgrb": rw,
        "shifted_time_over_pgrb": rt,
        "c6_work": c6["work"],
        "c6_process_seconds": c6["process_seconds"],
        "c6_reference_provenance": c6["provenance"],
        "c6_reference_run": c6["run_dir"],
        "shifted_work_over_c6": stage3.shifted(
            metric["work"], c6["work"], stage3.S_W),
        "shifted_time_over_c6": stage3.shifted(
            metric["process_seconds"], c6["process_seconds"], stage3.S_T),
        "severe_pgrb_regression": stage3.severe(metric, pgrb),
        "c6_advantage_gate_applies": advantage_applies,
        "pgrb_advantage_over_candidate": p_over_candidate,
        "c6_advantage_retained": (
            not advantage_applies or p_over_candidate >= 2.0),
        "material_win": rw <= .95,
        "material_loss": rw >= 1.05,
    }


def analyze_small(stage: str, candidate: str = "primary") -> None:
    ids = (common.VALIDATION_IDS if stage == "validation"
           else common.HOLDOUT_IDS)
    if stage == "holdout":
        prior = common.load_json(common.OUT / "validation_disposition.json")
        if not prior["passes_all_gates"]:
            raise RuntimeError("holdout remains sealed because validation failed")
    rows = [small_row(stage, instance_id, candidate) for instance_id in ids]
    work_gmean = stage3.gmean([
        row["shifted_work_over_pgrb"] for row in rows])
    time_gmean = stage3.gmean([
        row["shifted_time_over_pgrb"] for row in rows])
    wins = sum(row["material_win"] for row in rows)
    losses = sum(row["material_loss"] for row in rows)
    disposition = {
        "schema": f"round44-{stage}-disposition-v1",
        "stage": stage,
        "candidate": ("noadaptive" if candidate == "primary" else candidate),
        "configuration_sha256": (
            common.load_json(common.OUT / "final_candidate_freeze.json")
            ["configuration"]["decision_identity_sha256"] if
            candidate == "primary" else common.load_json(
                common.OUT / "fallback_candidate_activation_freeze.json")
            ["configuration"]["decision_identity_sha256"]),
        "row_count": len(rows),
        "certified_rows": sum(row["certified"] for row in rows),
        "all_correctness_gates": all(row["correctness"] for row in rows),
        "no_severe_pgrb_regression": not any(
            row["severe_pgrb_regression"] for row in rows),
        "shifted_work_gmean": work_gmean,
        "shifted_time_gmean": time_gmean,
        "c6_strong_win_advantage_retained": all(
            row["c6_advantage_retained"] for row in rows),
        "material_wins": wins,
        "material_losses": losses,
        "material_wins_at_least_losses": wins >= losses,
        "thresholds": {
            "shifted_work_gmean_max": 1.0,
            "shifted_time_gmean_max": 1.05,
            "material_work_deadband": .05,
        },
        "no_post_stage_tuning": True,
    }
    disposition["passes_all_gates"] = (
        disposition["all_correctness_gates"] and
        disposition["no_severe_pgrb_regression"] and
        work_gmean <= 1.0 and time_gmean <= 1.05 and
        disposition["c6_strong_win_advantage_retained"] and wins >= losses)
    suffix = (stage if candidate == "primary" or stage == "holdout" else
              f"{stage}_fallback")
    common.write_csv(common.OUT / f"{suffix}_comparison.csv", rows)
    common.write_json(common.OUT / f"{suffix}_disposition.json", disposition)


def external_directory(group: str, instance_id: str, arm: str) -> Path:
    return common.RUNS / f"{group}__{instance_id}__{arm}"


def gap(lower: float, upper: float) -> float:
    if not math.isfinite(lower) or not math.isfinite(upper):
        return 1.0
    return max(0.0, upper - lower) / max(abs(upper), 1e-12)


def trace(run_dir: Path, arm: str, metric: dict[str, Any]) -> list[dict[str, float]]:
    bound_path = run_dir / "global_bound_trace.csv"
    points: list[dict[str, float]] = []
    if bound_path.is_file():
        for row in common.csv_rows(bound_path):
            try:
                elapsed = float(row["process_elapsed_seconds"])
                lower = float(row["valid_global_lower_bound"])
                upper = float(row["verified_global_upper_bound"])
            except (KeyError, TypeError, ValueError):
                continue
            points.append({"time": elapsed, "work": math.nan,
                           "lower": lower, "upper": upper,
                           "gap": gap(lower, upper)})
    else:
        offset = historical.exact_start(run_dir) if arm == "pgrb" else 0.0
        for row in common.csv_rows(run_dir / "progress.csv"):
            try:
                if "elapsed_runtime_seconds" in row:
                    elapsed = offset + float(row["elapsed_runtime_seconds"])
                    lower = (float(row["best_bound"])
                             if common.truth(row["best_bound_available"])
                             else -math.inf)
                    upper = (float(row["incumbent"])
                             if common.truth(row["incumbent_available"])
                             else math.inf)
                    work = float(row["work"])
                else:
                    elapsed = float(row["elapsed_seconds"])
                    lower = float(row["global_LB"])
                    upper = float(row["incumbent_UB"])
                    work = float(row.get("work", "nan"))
            except (KeyError, TypeError, ValueError):
                continue
            points.append({"time": elapsed, "work": work,
                           "lower": lower, "upper": upper,
                           "gap": gap(lower, upper)})
    if not points:
        points.append({"time": 0.0, "work": 0.0,
                       "lower": metric["valid_lower"],
                       "upper": metric["verified_upper"],
                       "gap": metric["relative_gap"]})
    points.sort(key=lambda row: row["time"])
    if points[0]["time"] > 0.0:
        first = dict(points[0])
        first["time"] = 0.0
        first["work"] = 0.0
        points.insert(0, first)
    return points


def work_events(run_dir: Path, arm: str, cap: float,
                points: list[dict[str, float]]) -> list[tuple[float, float]]:
    if arm == "pgrb":
        return [(row["time"], row["work"]) for row in points
                if math.isfinite(row["work"])]
    ledger = run_dir / "native_optimize_ledger.csv"
    if not ledger.is_file():
        return [(0.0, 0.0)]
    total = 0.0
    events = [(0.0, 0.0)]
    for row in common.csv_rows(ledger):
        try:
            launch = cap - 20.0 - float(
                row["global_deadline_remaining_at_launch"])
            completion = max(0.0, launch) + float(row["solver_runtime"])
            total += float(row["work"])
        except (KeyError, TypeError, ValueError):
            continue
        events.append((completion, total))
    return sorted(events)


def value_at(points: list[dict[str, float]], time_value: float,
             key: str) -> float:
    value = points[0][key]
    for row in points:
        if row["time"] > time_value:
            break
        value = row[key]
    return value


def work_at(events: list[tuple[float, float]], time_value: float) -> float:
    value = 0.0
    for elapsed, current in events:
        if elapsed > time_value:
            break
        value = current
    return value


def gap_integral(points: list[dict[str, float]], horizon: float,
                 certified: bool, solve_time: float) -> float:
    area = 0.0
    previous_time = 0.0
    previous_gap = points[0]["gap"]
    for row in points[1:]:
        current_time = min(horizon, max(previous_time, row["time"]))
        area += (current_time - previous_time) * previous_gap
        previous_time = current_time
        previous_gap = row["gap"]
        if previous_time >= horizon:
            break
    end = min(horizon, solve_time) if certified else horizon
    if end > previous_time:
        area += (end - previous_time) * previous_gap
    return area / horizon


def trajectory_metrics(run_dir: Path, arm: str, metric: dict[str, Any],
                       cap: float) -> dict[str, Any]:
    points = trace(run_dir, arm, metric)
    events = work_events(run_dir, arm, cap, points)
    first_incumbent = next((row for row in points
                            if math.isfinite(row["upper"])), None)
    result: dict[str, Any] = {
        "gap_integral": gap_integral(
            points, cap, metric["certified"], metric["process_seconds"]),
        "time_to_first_incumbent": (
            first_incumbent["time"] if first_incumbent else math.nan),
        "work_to_first_incumbent": (
            work_at(events, first_incumbent["time"])
            if first_incumbent else math.nan),
    }
    for checkpoint in CHECKPOINTS:
        result[f"gap_at_{int(checkpoint)}s"] = (
            0.0 if metric["certified"] and
            metric["process_seconds"] <= checkpoint else
            value_at(points, checkpoint, "gap"))
    for level in GAP_LEVELS:
        label = {0.10: "10pct", 0.05: "5pct", 0.01: "1pct",
                 0.001: "0p1pct"}[level]
        hit = next((row for row in points if row["gap"] <= level), None)
        result[f"time_to_{label}_gap"] = hit["time"] if hit else math.nan
        result[f"work_to_{label}_gap"] = (
            work_at(events, hit["time"]) if hit else math.nan)
    return result


def external_metric(group: str, path_string: str, arm: str,
                    cap: float) -> dict[str, Any]:
    instance_id = Path(path_string).stem
    directory = external_directory(group, instance_id, arm)
    label = {"candidate": FINAL_TAG, "pgrb": "P-GRB", "c6": "C6"}[arm]
    metric = historical.load_metrics(directory, label, "round44_external")
    command = common.load_json(directory / "command.json")
    marker = common.load_json(directory / "completion_marker.json")
    result = common.load_json(directory / "result.json")
    row = {
        "group": group,
        "instance_id": instance_id,
        "instance_path": path_string,
        "arm": arm,
        "run_id": directory.name,
        "correctness": correctness(
            metric, result, command, marker, candidate=arm == "candidate"),
        "certified": metric["certified"],
        "right_censored": metric["right_censored"],
        "failure_reason": metric["failure_reason"],
        "false_certificate": metric["false_certificate"],
        "verified_incumbent": metric["verified_incumbent"],
        "parameter_roundtrip_valid": metric["parameter_roundtrip_valid"],
        "work": metric["work"],
        "process_seconds": metric["process_seconds"],
        "nodes": metric["nodes"],
        "peak_memory_gb": metric["peak_memory_gb"],
        "valid_lower": metric["valid_lower"],
        "verified_upper": metric["verified_upper"],
        "final_relative_gap": metric["relative_gap"],
        "lp_jobs": metric["lp_jobs"],
        "terminal_mip_jobs": metric["terminal_mip_jobs"],
    }
    row.update(trajectory_metrics(directory, arm, metric, cap))
    return row


def analyze_external() -> None:
    holdout = common.load_json(common.OUT / "holdout_disposition.json")
    if not holdout["passes_all_gates"]:
        raise RuntimeError("external qualification requires passing holdout")
    groups = [
        ("additional-v12", common.ADDITIONAL_V12, 7200.0),
        ("v20-development", common.V20_DEVELOPMENT, 3600.0),
        ("v20-confirmation", common.V20_CONFIRMATION, 3600.0),
    ]
    rows = [external_metric(group, path, arm, cap)
            for group, paths, cap in groups for path in paths
            for arm in ("candidate", "pgrb", "c6")]
    v12: list[dict[str, Any]] = []
    for path in common.ADDITIONAL_V12:
        instance_id = Path(path).stem
        candidate = next(row for row in rows if row["group"] ==
                         "additional-v12" and
                         row["instance_id"] == instance_id and
                         row["arm"] == "candidate")
        pgrb = next(row for row in rows if row["group"] ==
                    "additional-v12" and row["instance_id"] == instance_id
                    and row["arm"] == "pgrb")
        c6 = next(row for row in rows if row["group"] ==
                  "additional-v12" and row["instance_id"] == instance_id
                  and row["arm"] == "c6")
        v12.append({
            **candidate,
            "pgrb_certified": pgrb["certified"],
            "pgrb_work": pgrb["work"],
            "pgrb_process_seconds": pgrb["process_seconds"],
            "shifted_work_over_pgrb": stage3.shifted(
                candidate["work"], pgrb["work"], 1.0),
            "shifted_time_over_pgrb": stage3.shifted(
                candidate["process_seconds"], pgrb["process_seconds"], 1.0),
            "severe_pgrb_regression": stage3.severe(candidate, pgrb),
            "c6_certified": c6["certified"],
            "c6_work": c6["work"],
            "c6_process_seconds": c6["process_seconds"],
            "shifted_work_over_c6": stage3.shifted(
                candidate["work"], c6["work"], 1.0),
        })
    v12_work_gmean = stage3.gmean([
        row["shifted_work_over_pgrb"] for row in v12])
    v12_disposition = {
        "schema": "round44-additional-v12-disposition-v1",
        "zero_false_certificates": not any(
            row["false_certificate"] for row in rows
            if row["group"] == "additional-v12"),
        "candidate_correctness": all(row["correctness"] for row in v12),
        "no_severe_pgrb_regression": not any(
            row["severe_pgrb_regression"] for row in v12),
        "shifted_work_gmean": v12_work_gmean,
        "shifted_work_gmean_max": 1.0,
    }
    v12_disposition["passes_all_gates"] = (
        v12_disposition["zero_false_certificates"] and
        v12_disposition["candidate_correctness"] and
        v12_disposition["no_severe_pgrb_regression"] and
        v12_work_gmean <= 1.0)
    common.write_csv(common.OUT / "additional_v12_comparison.csv", v12)
    common.write_json(
        common.OUT / "additional_v12_disposition.json", v12_disposition)

    v20: list[dict[str, Any]] = []
    lower_gi = 0
    for group, paths in (("v20-development", common.V20_DEVELOPMENT),
                         ("v20-confirmation", common.V20_CONFIRMATION)):
        for path in paths:
            instance_id = Path(path).stem
            candidate = next(row for row in rows if row["group"] == group and
                             row["instance_id"] == instance_id and
                             row["arm"] == "candidate")
            pgrb = next(row for row in rows if row["group"] == group and
                        row["instance_id"] == instance_id and
                        row["arm"] == "pgrb")
            c6 = next(row for row in rows if row["group"] == group and
                      row["instance_id"] == instance_id and
                      row["arm"] == "c6")
            better_gi = candidate["gap_integral"] < pgrb["gap_integral"]
            lower_gi += better_gi
            solved_severe = (candidate["certified"] and pgrb["certified"] and
                             stage3.severe(candidate, pgrb))
            v20.append({
                **candidate,
                "pgrb_certified": pgrb["certified"],
                "pgrb_work": pgrb["work"],
                "pgrb_process_seconds": pgrb["process_seconds"],
                "pgrb_gap_integral": pgrb["gap_integral"],
                "candidate_lower_gap_integral": better_gi,
                "fully_solved_severe_pgrb_regression": solved_severe,
                "c6_certified": c6["certified"],
                "c6_work": c6["work"],
                "c6_gap_integral": c6["gap_integral"],
            })
    candidate_certs = sum(row["certified"] for row in v20)
    pgrb_certs = sum(row["pgrb_certified"] for row in v20)
    no_engineering_failure = all(
        row["failure_reason"] in {"none", "overall_global_deadline"}
        for row in v20)
    v20_disposition = {
        "schema": "round44-v20-disposition-v1",
        "zero_false_certificates": not any(
            row["false_certificate"] for row in rows
            if row["group"].startswith("v20-")),
        "no_candidate_specific_memory_or_engineering_failure":
            no_engineering_failure,
        "candidate_certified_rows": candidate_certs,
        "pgrb_certified_rows": pgrb_certs,
        "candidate_certifies_at_least_as_many":
            candidate_certs >= pgrb_certs,
        "candidate_lower_gap_integral_rows": lower_gi,
        "lower_gap_integral_required_rows": 4,
        "no_severe_fully_solved_pgrb_regression": not any(
            row["fully_solved_severe_pgrb_regression"] for row in v20),
        "mixed_outcomes_reported": True,
    }
    v20_disposition["passes_qualification"] = (
        v20_disposition["zero_false_certificates"] and
        no_engineering_failure and
        (candidate_certs >= pgrb_certs or lower_gi >= 4) and
        v20_disposition["no_severe_fully_solved_pgrb_regression"])
    common.write_csv(common.OUT / "v20_profile_comparison.csv", v20)
    common.write_csv(common.OUT / "external_all_arms.csv", rows)
    common.write_json(common.OUT / "v20_disposition.json", v20_disposition)


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--freeze-final", action="store_true")
    action.add_argument("--activate-fallback", action="store_true")
    action.add_argument("--seal-negative", action="store_true")
    action.add_argument("--small", choices=("validation", "holdout"))
    action.add_argument("--external", action="store_true")
    parser.add_argument("--candidate", choices=("primary", "veto-f05"),
                        default="primary")
    args = parser.parse_args()
    if args.freeze_final:
        freeze_final()
    elif args.activate_fallback:
        activate_fallback()
    elif args.seal_negative:
        seal_negative_terminal()
    elif args.small:
        analyze_small(args.small, args.candidate)
    else:
        analyze_external()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
