#!/usr/bin/env python3
"""Run the frozen Round 58 paired benchmark with hash-bound resumption."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import round46_common as round46
import round58_common as r58
from round58_route_archive import object_json, verify_native_result


SOURCE_FREEZE = "8ec0e1e151a5f25cb0594852f896b04303c0ba34"
EXE = (r58.ROOT / "build" / "official-round58-citibike443-8ec0e1e15" /
       "ExactEBRP.exe")
EXE_SHA256 = "0f7570d4c421b9d2f4cb2941bf4d426fe396a25b26ef1c0618df0f3a675333f2"
CONTRACT = r58.EVIDENCE / "paired_solver_contract.json"
FINGERPRINTS = r58.EVIDENCE / "pgrb_expected_fingerprints.json"
RAW_RUNS = r58.RAW / "official_runs"
SCREEN_RESULTS = r58.EVIDENCE / "screen_results_3600.csv"
SCREEN_DECISIONS = r58.EVIDENCE / "screen_extension_decisions.csv"
LONG_RESULTS = r58.EVIDENCE / "long_run_results_10800.csv"
NEAR_DECISIONS = r58.EVIDENCE / "near_convergence_extension_decisions.csv"
EXTENDED_16200 = r58.EVIDENCE / "extended_results_16200.csv"
EXTENDED_21600 = r58.EVIDENCE / "extended_results_21600.csv"

METHODS = ("k1_am_sf", "pgrb")
METHOD_LABEL = {"k1_am_sf": "K1-AM-SF", "pgrb": "P-GRB"}
STAGE_CAP = {
    "screen_3600": 3600,
    "long_10800": 10800,
    "extension_16200": 16200,
    "extension_21600": 21600,
}
STAGE_BY_CAP = {cap: stage for stage, cap in STAGE_CAP.items()}
FORBIDDEN_OPTIONS = (
    "--incumbent-json", "--hga-incumbent", "--external-incumbent",
    "--frontier-focus-from-result", "--frontier-import-interval-bound",
    "--frontier-focus-only", "--frontier-resume-state",
    "--frontier-resume-open-nodes", "--incumbent-archive-auto",
    "--incumbent-archive-dir",
)
RUN_FIELDS = [
    "completion_sequence_number", "completion_timestamp_utc", "scenario_id",
    "dataset_family", "V", "geographic_regime", "inventory_regime",
    "replicate", "M", "Q", "T", "method", "method_label", "run_stage",
    "process_cap_seconds", "actual_wall_time_seconds", "gurobi_work",
    "native_status", "strict_certificate", "verified_incumbent_available",
    "objective", "G", "P", "valid_lower_bound", "verified_upper_bound",
    "absolute_gap", "relative_gap", "scaled_gap", "nodes",
    "simplex_iterations", "split_count", "interval_count",
    "route_witness_status", "expected_model_fingerprint",
    "actual_model_fingerprint", "fingerprint_match", "completion_marker_path",
    "result_path", "run_identity_sha256", "result_sha256", "next_action",
    "notes",
]
PAIR_FIELDS = [
    "scenario_id", "K1_screen_status", "PGRB_screen_status",
    "K1_final_status", "PGRB_final_status", "K1_certificate",
    "PGRB_certificate", "K1_wall_time", "PGRB_wall_time", "K1_work",
    "PGRB_work", "K1_valid_LB", "PGRB_valid_LB", "K1_verified_UB",
    "PGRB_verified_UB", "K1_relative_gap", "PGRB_relative_gap",
    "current_pair_classification", "current_winner_at_common_horizon",
    "extension_state", "pair_complete", "severe_regression_flag",
    "last_update_timestamp_utc",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def panel() -> list[dict[str, str]]:
    rows = r58.read_csv(r58.EVIDENCE / "round58_complete_panel.csv")
    if len(rows) != 50 or len({row["scenario_id"] for row in rows}) != 50:
        raise RuntimeError("Round 58 panel must contain exactly 50 unique scenarios")
    return rows


def panel_by_id() -> dict[str, dict[str, str]]:
    return {row["scenario_id"]: row for row in panel()}


def fingerprint_index() -> dict[str, dict[str, Any]]:
    manifest = r58.read_json(FINGERPRINTS)
    if (manifest.get("created_before_any_round58_benchmark_solve") is not True or
            len(manifest.get("entries", [])) != 50 or
            manifest.get("source_freeze_commit") != SOURCE_FREEZE or
            manifest.get("executable_sha256") != EXE_SHA256):
        raise RuntimeError("P-GRB expected-fingerprint manifest is not qualified")
    return {entry["instance_id"]: entry for entry in manifest["entries"]}


def run_dir(row: dict[str, str], method: str, cap: int) -> Path:
    return RAW_RUNS / row["scenario_id"] / method / STAGE_BY_CAP[cap]


def expected_identity(row: dict[str, str], method: str, cap: int) -> str:
    return r58.run_identity(
        scenario_sha=row["scenario_sha256"], method=method, cap=cap,
        stage=STAGE_BY_CAP[cap], source_sha=SOURCE_FREEZE,
        executable_sha=EXE_SHA256, contract_sha=r58.sha256_file(CONTRACT))


def set_option(command: list[str], option: str, value: Any) -> None:
    round46.replace_option(command, option, value)


def base_item(row: dict[str, str]) -> dict[str, Any]:
    return {
        "instance": row["scenario_id"], "path": row["instance_path"],
        "sha256": row["instance_file_sha256"], "T": int(row["T_seconds"]),
        "V": int(row["V"]), "M": int(row["M"]),
    }


def command_for(row: dict[str, str], method: str, cap: int,
                destination: Path) -> tuple[list[str], str]:
    identity = expected_identity(row, method, cap)
    if method == "k1_am_sf":
        command = round46.c6_command(
            base_item(row), destination, float(cap), 1, 0.08, EXE)
    elif method == "pgrb":
        command = round46.pgrb_command(
            base_item(row), destination, float(cap), EXE)
    else:
        raise RuntimeError(f"unknown method: {method}")
    for option in FORBIDDEN_OPTIONS:
        round46.remove_option(command, option)
    common: tuple[tuple[str, Any], ...] = (
        ("--T", int(row["T_seconds"])),
        ("--lambda", float(row["lambda"])),
        ("--threads", 1), ("--mip-threads", 1),
        ("--gurobi-threads", 1), ("--gurobi-seed", 0),
        ("--gurobi-presolve", -1),
        ("--process-wall-time-limit", float(cap)),
        ("--time-limit", float(max(1, cap - 6))),
        ("--process-shutdown-margin", 2.0),
        ("--round56-scenario-id", row["scenario_id"]),
        ("--round56-mathematical-instance-sha256", row["scenario_sha256"]),
        ("--round56-run-identity-sha256", identity),
        ("--round22-source-commit", SOURCE_FREEZE),
        ("--round22-executable-sha256", EXE_SHA256),
        ("--round24-executable-sha256", EXE_SHA256),
        ("--round24-manifest-executable-sha256", EXE_SHA256),
        ("--process-phase-ledger", destination / "process_phases.csv"),
        ("--log", destination / "native.log"),
        ("--out", destination / "result.json"),
    )
    for option, value in common:
        set_option(command, option, value)
    if method == "k1_am_sf":
        for option, value in (
            ("--algorithm-preset", "paper-k1-am-sf"),
            ("--external-gini-interval-mip-policy",
             "interval-mip-core-no-exhaustive-subset-duration"),
            ("--round48-k1-amf", "off"),
            ("--round49-k1-am-rc", "off"),
            ("--progress-log", destination / "progress.csv"),
            ("--external-gini-artifact-dir", destination / "external"),
            ("--primal-heuristic-generation-log",
             destination / "hga_generations.csv"),
            ("--heuristic-candidates-csv",
             destination / "heuristic_candidates.csv"),
        ):
            set_option(command, option, value)
    else:
        expected = fingerprint_index()[row["scenario_id"]]
        set_option(command, "--method", "gurobi")
        if "--plain-baseline" not in command:
            command.append("--plain-baseline")
        set_option(command, "--gurobi-hga-start", False)
        set_option(command, "--gurobi-progress", destination / "progress.csv")
        set_option(command, "--progress-log", destination / "progress.csv")
        set_option(command, "--round24-expected-gurobi-model-fingerprint",
                   int(expected["expected_gurobi_model_fingerprint"]))
        round46.remove_option(command, "--gurobi-model-export")
    if any(option in command for option in FORBIDDEN_OPTIONS):
        raise RuntimeError(f"forbidden mechanism present: {row['scenario_id']}/{method}")
    if method == "pgrb" and "--plain-baseline" not in command:
        raise RuntimeError("P-GRB plain baseline was not bound")
    return command, identity


def option_value(command: list[str], option: str) -> str | None:
    if option not in command:
        return None
    index = command.index(option)
    return command[index + 1] if index + 1 < len(command) else None


def preflight() -> None:
    if not EXE.is_file() or r58.sha256_file(EXE) != EXE_SHA256:
        raise RuntimeError("official Round 58 executable hash mismatch")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", SOURCE_FREEZE, "HEAD"],
        cwd=r58.ROOT, check=False).returncode
    if ancestor != 0:
        raise RuntimeError("Round 58 source freeze is not an ancestor of HEAD")
    expected = fingerprint_index()
    if set(expected) != {row["scenario_id"] for row in panel()}:
        raise RuntimeError("P-GRB fingerprint coverage differs from frozen panel")
    for row in panel():
        if r58.sha256_file(r58.ROOT / row["instance_path"]) != row["instance_file_sha256"]:
            raise RuntimeError(f"input hash mismatch: {row['scenario_id']}")
        for method in METHODS:
            for cap in STAGE_CAP.values():
                command, identity = command_for(row, method, cap, run_dir(row, method, cap))
                if option_value(command, "--round56-run-identity-sha256") != identity:
                    raise RuntimeError("run identity did not round trip into command")
                if float(option_value(command, "--process-wall-time-limit") or -1) != cap:
                    raise RuntimeError("process cap did not round trip into command")
    print(json.dumps({
        "preflight": "PASS", "panel_rows": 50,
        "command_variants_checked": 400,
        "source_freeze_commit": SOURCE_FREEZE,
        "executable_sha256": EXE_SHA256,
    }, indent=2))


def native_incumbent_claimed(result: dict[str, Any]) -> bool:
    verification = result.get("verification") or {}
    return bool(
        verification.get("original_solution_feasible") and
        verification.get("original_objective_recomputed") and
        not verification.get("errors") and finite(verification.get("objective")))


def k1_valid_bound(result: dict[str, Any]) -> float | None:
    value = result.get("lower_bound")
    valid = bool(
        finite(value) and result.get("external_gini_tree_available") is True and
        result.get("external_gini_tree_all_leaf_bounds_valid") is True and
        result.get("external_gini_tree_global_bound_monotone") is True and
        result.get("external_gini_tree_feasibility_consistency_gate") is True and
        result.get("strict_lower_bound_source"))
    if result.get("strict_certified_original_problem") is True and finite(value):
        valid = True
    return float(value) if valid else None


def pgrb_scope_valid(row: dict[str, str], result: dict[str, Any]) -> bool:
    expected = fingerprint_index()[row["scenario_id"]]
    expected_fp = int(expected["expected_gurobi_model_fingerprint"])
    return bool(
        result.get("method") == "gurobi" and
        result.get("method_scope") == "plain_gurobi" and
        result.get("cplex_plain_baseline") is True and
        result.get("gurobi_hga_incumbent_found") is not True and
        result.get("gurobi_hga_start_submitted") is not True and
        result.get("gurobi_model_fingerprint") == expected_fp and
        result.get("gurobi_native_domain_audit_passed") is True and
        result.get("gurobi_native_variable_names_match") is True and
        result.get("gurobi_native_variable_types_match") is True and
        result.get("gurobi_native_variable_bounds_match") is True and
        result.get("gurobi_lifecycle_valid") is True and
        int(result.get("gurobi_threads_effective", -999)) == 1 and
        int(result.get("gurobi_seed_effective", -999)) == 0 and
        int(result.get("gurobi_presolve_effective", -999)) == -1)


def pgrb_valid_bound(row: dict[str, str], result: dict[str, Any]) -> float | None:
    value = result.get("gurobi_obj_bound_c")
    if (pgrb_scope_valid(row, result) and
            result.get("gurobi_obj_bound_c_available") is True and finite(value)):
        return float(value)
    return None


def explicit_gaps(lower: float | None, upper: float | None) -> dict[str, float | None]:
    if lower is None or upper is None:
        return {"absolute_gap": None, "relative_gap": None, "scaled_gap": None}
    absolute = max(0.0, float(upper) - float(lower))
    return {
        "absolute_gap": absolute,
        "relative_gap": absolute / max(abs(float(upper)), 1e-6),
        "scaled_gap": absolute / max(1.0, abs(float(upper))),
    }


def result_status(method: str, result: dict[str, Any]) -> str:
    if method == "pgrb":
        return str(result.get("gurobi_status_text") or result.get("status") or "unknown")
    return str(result.get("status") or "unknown")


def summarize_result(row: dict[str, str], method: str, cap: int,
                     result_path: Path, verification_path: Path,
                     timestamp: str, sequence: int) -> dict[str, Any]:
    result = object_json(result_path)
    verification = object_json(verification_path)
    incumbent = verification.get("passed") is True
    lower = k1_valid_bound(result) if method == "k1_am_sf" else pgrb_valid_bound(row, result)
    upper = float(verification["objective"]) if incumbent else None
    gaps = explicit_gaps(lower, upper)
    expected_fp: int | None = None
    actual_fp: int | None = None
    fingerprint_match: bool | None = None
    if method == "pgrb":
        expected_fp = int(fingerprint_index()[row["scenario_id"]][
            "expected_gurobi_model_fingerprint"])
        actual_fp = result.get("gurobi_model_fingerprint")
        fingerprint_match = actual_fp == expected_fp
    strict = bool(result.get("strict_certified_original_problem"))
    if strict and not incumbent:
        raise RuntimeError(f"strict certificate without verified incumbent: {row['scenario_id']}/{method}")
    if strict and method == "pgrb" and not pgrb_scope_valid(row, result):
        raise RuntimeError(f"strict P-GRB certificate outside frozen scope: {row['scenario_id']}")
    if strict and (lower is None or upper is None or gaps["absolute_gap"] is None or
                   gaps["absolute_gap"] > 1e-6 * max(1.0, abs(upper))):
        raise RuntimeError(f"strict certificate does not close qualified gap: {row['scenario_id']}/{method}")
    actual_wall = result.get("final_process_wall_time_seconds")
    if not finite(actual_wall):
        actual_wall = result.get("runtime_seconds")
    if method == "k1_am_sf":
        work = result.get("external_gini_tree_work")
        nodes = result.get("external_gini_tree_nodes")
        simplex = result.get("external_gini_tree_simplex_iterations")
        split_count = result.get("external_gini_tree_split_count")
        intervals = result.get("external_gini_tree_final_leaf_count")
    else:
        work = result.get("gurobi_work")
        nodes = result.get("gurobi_node_count")
        simplex = result.get("gurobi_iter_count")
        split_count = None
        intervals = None
    return {
        "completion_sequence_number": sequence,
        "completion_timestamp_utc": timestamp,
        "scenario_id": row["scenario_id"], "dataset_family": r58.DATASET_FAMILY,
        "V": int(row["V"]), "geographic_regime": row["geographic_regime"],
        "inventory_regime": row["inventory_regime"],
        "replicate": int(row["replicate"]), "M": int(row["M"]),
        "Q": int(row["Q"]), "T": int(row["T_seconds"]), "method": method,
        "method_label": METHOD_LABEL[method], "run_stage": STAGE_BY_CAP[cap],
        "process_cap_seconds": cap, "actual_wall_time_seconds": actual_wall,
        "gurobi_work": work, "native_status": result_status(method, result),
        "strict_certificate": strict,
        "verified_incumbent_available": incumbent,
        "objective": upper, "G": verification.get("G") if incumbent else None,
        "P": verification.get("P") if incumbent else None,
        "valid_lower_bound": lower, "verified_upper_bound": upper,
        **gaps, "nodes": nodes, "simplex_iterations": simplex,
        "split_count": split_count, "interval_count": intervals,
        "route_witness_status": ("verified_native_incumbent" if incumbent
                                 else "no_verified_incumbent"),
        "expected_model_fingerprint": expected_fp,
        "actual_model_fingerprint": actual_fp,
        "fingerprint_match": fingerprint_match,
        "completion_marker_path": r58.repo_path(result_path.parent /
                                                  "completion_marker.json"),
        "result_path": r58.repo_path(result_path),
        "run_identity_sha256": result.get("run_identity_sha256"),
        "result_sha256": r58.sha256_file(result_path),
        "next_action": "pending_frozen_stage_decision",
        "notes": "fresh independent optimizer process; archive time excluded",
    }


def completion_marker(row: dict[str, str], method: str,
                      cap: int) -> dict[str, Any] | None:
    directory = run_dir(row, method, cap)
    marker_path = directory / "completion_marker.json"
    result_path = directory / "result.json"
    verification_path = directory / "independent_verification.json"
    command_path = directory / "command.json"
    if not all(path.is_file() for path in (
            marker_path, result_path, verification_path, command_path)):
        return None
    marker = object_json(marker_path)
    result = object_json(result_path)
    identity = expected_identity(row, method, cap)
    valid = all((
        marker.get("complete") is True,
        marker.get("source_freeze_commit") == SOURCE_FREEZE,
        marker.get("executable_sha256") == EXE_SHA256,
        marker.get("scenario_sha256") == row["scenario_sha256"],
        marker.get("run_identity_sha256") == identity,
        marker.get("result_sha256") == r58.sha256_file(result_path),
        marker.get("verification_sha256") == r58.sha256_file(verification_path),
        marker.get("command_sha256") == r58.sha256_file(command_path),
        result.get("run_identity_sha256") == identity,
        result.get("mathematical_instance_sha256") == row["scenario_sha256"],
        int(float(result.get("route_time_limit_seconds", -1))) == int(row["T_seconds"]),
        int(float(result.get("solver_process_cap_seconds", -1))) == cap,
    ))
    if not valid:
        raise RuntimeError(f"stale or hash-invalid completed arm retained: {directory}")
    return marker


def all_markers() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario in panel():
        for method in METHODS:
            for cap in sorted(STAGE_BY_CAP):
                marker = completion_marker(scenario, method, cap)
                if marker is not None:
                    rows.append(marker)
    return sorted(rows, key=lambda value: int(value["summary"][
        "completion_sequence_number"]))


def append_live_run(summary: dict[str, Any]) -> None:
    r58.LIVE_RUNS.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, str]] = []
    if r58.LIVE_RUNS.is_file():
        existing = r58.read_csv(r58.LIVE_RUNS)
    identity = summary["run_identity_sha256"]
    if any(row["run_identity_sha256"] == identity for row in existing):
        return
    mode = "a" if r58.LIVE_RUNS.is_file() and r58.LIVE_RUNS.stat().st_size else "w"
    with r58.LIVE_RUNS.open(mode, newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=RUN_FIELDS, lineterminator="\n")
        if mode == "w":
            writer.writeheader()
        writer.writerow({field: summary.get(field) for field in RUN_FIELDS})
        stream.flush()
        os.fsync(stream.fileno())


def rebuild_live_runs() -> None:
    markers = all_markers()
    rows = [marker["summary"] for marker in markers]
    if rows:
        r58.write_csv(r58.LIVE_RUNS, rows, RUN_FIELDS, atomic=True)


def marker_summary(row: dict[str, str], method: str, cap: int) -> dict[str, Any] | None:
    marker = completion_marker(row, method, cap)
    return dict(marker["summary"]) if marker else None


def latest_summary(row: dict[str, str], method: str) -> dict[str, Any] | None:
    for cap in sorted(STAGE_BY_CAP, reverse=True):
        summary = marker_summary(row, method, cap)
        if summary is not None:
            return summary
    return None


def pair_class(k1: dict[str, Any] | None,
               pgrb: dict[str, Any] | None) -> str:
    if k1 is None or pgrb is None:
        return "pair_incomplete"
    ck, cp = bool(k1["strict_certificate"]), bool(pgrb["strict_certificate"])
    if ck and cp:
        left, right = float(k1["actual_wall_time_seconds"]), float(pgrb["actual_wall_time_seconds"])
        if abs(left - right) <= 1e-6:
            return "both_certified_tie"
        return "both_certified_k1_faster" if left < right else "both_certified_pgrb_faster"
    if ck:
        return "k1_only_certified"
    if cp:
        return "pgrb_only_certified"
    kg, pg = k1.get("relative_gap"), pgrb.get("relative_gap")
    kl, pl = k1.get("valid_lower_bound"), pgrb.get("valid_lower_bound")
    ku, pu = k1.get("verified_upper_bound"), pgrb.get("verified_upper_bound")
    if not all(finite(value) for value in (kg, pg, kl, pl, ku, pu)):
        return "invalid_pair"
    k_better = (float(kl) >= float(pl) and float(ku) <= float(pu) and
                float(kg) <= float(pg) and
                any((float(kl) > float(pl), float(ku) < float(pu), float(kg) < float(pg))))
    p_better = (float(pl) >= float(kl) and float(pu) <= float(ku) and
                float(pg) <= float(kg) and
                any((float(pl) > float(kl), float(pu) < float(ku), float(pg) < float(kg))))
    if k_better:
        return "neither_certified_k1_better_bound"
    if p_better:
        return "neither_certified_pgrb_better_bound"
    return "neither_certified_mixed"


def screen_action(row: dict[str, str]) -> dict[str, Any] | None:
    k1 = marker_summary(row, "k1_am_sf", r58.SCREEN_CAP)
    pgrb = marker_summary(row, "pgrb", r58.SCREEN_CAP)
    if k1 is None or pgrb is None:
        return None
    ck, cp = bool(k1["strict_certificate"]), bool(pgrb["strict_certificate"])
    extend_k1 = extend_pgrb = False
    reason = ""
    if ck and cp:
        reason = "both_certified_stop"
    elif ck != cp:
        noncert = pgrb if ck else k1
        certified = k1 if ck else pgrb
        eligible_gap = finite(noncert.get("relative_gap")) and float(
            noncert["relative_gap"]) <= 0.10
        slow_certificate = finite(certified.get("actual_wall_time_seconds")) and float(
            certified["actual_wall_time_seconds"]) >= 2700.0
        should_extend = eligible_gap or slow_certificate
        extend_pgrb = ck and should_extend
        extend_k1 = cp and should_extend
        reason = ("single_certified_extend_noncertified" if should_extend else
                  "single_certified_censored_large_gap_stop")
    else:
        extend_k1 = extend_pgrb = True
        reason = "neither_certified_extend_both"
    if extend_k1 and extend_pgrb:
        action = "both_extensions_required"
    elif extend_k1:
        action = "K1_extension_required"
    elif extend_pgrb:
        action = "P-GRB_extension_required"
    elif ck and cp:
        action = "pair_complete"
    else:
        action = "no_extension_due_to_large_remaining_gap"
    return {
        "scenario_id": row["scenario_id"],
        "screen_k1_certificate": ck, "screen_pgrb_certificate": cp,
        "screen_k1_relative_gap": k1.get("relative_gap"),
        "screen_pgrb_relative_gap": pgrb.get("relative_gap"),
        "screen_k1_wall_seconds": k1.get("actual_wall_time_seconds"),
        "screen_pgrb_wall_seconds": pgrb.get("actual_wall_time_seconds"),
        "extend_k1_to_10800": extend_k1,
        "extend_pgrb_to_10800": extend_pgrb,
        "next_action": action, "decision_reason": reason,
        "decision_frozen_after_both_screen_arms": True,
    }


def near_action(row: dict[str, str], method: str) -> dict[str, Any] | None:
    long = marker_summary(row, method, r58.LONG_CAP)
    if long is None:
        return None
    certificate = bool(long["strict_certificate"])
    relative = long.get("relative_gap")
    target: int | None = None
    if certificate:
        reason = "certified_at_10800_stop"
    elif not finite(relative):
        reason = "missing_qualified_gap_stop"
    elif float(relative) <= 0.05:
        target, reason = 21600, "five_percent_tier_direct_21600"
    elif float(relative) <= 0.10:
        target, reason = 16200, "ten_percent_tier_16200"
    else:
        reason = "relative_gap_above_ten_percent_stop"
    return {
        "scenario_id": row["scenario_id"], "method": method,
        "certificate_at_10800": certificate,
        "valid_lower_bound_at_10800": long.get("valid_lower_bound"),
        "verified_upper_bound_at_10800": long.get("verified_upper_bound"),
        "relative_gap_at_10800": relative,
        "authorized_next_cap_seconds": target,
        "decision_reason": reason,
        "decision_frozen_from_10800_result": True,
    }


def post_16200_action(row: dict[str, str], method: str) -> dict[str, Any] | None:
    current = marker_summary(row, method, 16200)
    if current is None:
        return None
    if current["strict_certificate"]:
        target, reason = None, "certified_at_16200_stop"
    elif finite(current.get("relative_gap")) and float(current["relative_gap"]) <= 0.05:
        target, reason = 21600, "post_16200_five_percent_tier_21600"
    else:
        target, reason = None, "post_16200_gap_above_five_percent_stop"
    return {
        "scenario_id": row["scenario_id"], "method": method,
        "certificate_at_16200": bool(current["strict_certificate"]),
        "relative_gap_at_16200": current.get("relative_gap"),
        "authorized_next_cap_seconds": target,
        "decision_reason": reason,
        "decision_frozen_from_16200_result": True,
    }


def extension_state(row: dict[str, str]) -> str:
    decision = screen_action(row)
    if decision is None:
        return "awaiting_screen_pair"
    pending: list[str] = []
    for method, key in (("k1_am_sf", "extend_k1_to_10800"),
                        ("pgrb", "extend_pgrb_to_10800")):
        if decision[key] and marker_summary(row, method, 10800) is None:
            pending.append(f"{method}:10800")
            continue
        near = near_action(row, method) if decision[key] else None
        if near and near["authorized_next_cap_seconds"]:
            target = int(near["authorized_next_cap_seconds"])
            if marker_summary(row, method, target) is None:
                pending.append(f"{method}:{target}")
            elif target == 16200:
                post = post_16200_action(row, method)
                if (post and post["authorized_next_cap_seconds"] == 21600 and
                        marker_summary(row, method, 21600) is None):
                    pending.append(f"{method}:21600")
    return "complete" if not pending else "pending:" + ";".join(pending)


def live_pair_row(row: dict[str, str]) -> dict[str, Any]:
    k_screen = marker_summary(row, "k1_am_sf", 3600)
    p_screen = marker_summary(row, "pgrb", 3600)
    k_final = latest_summary(row, "k1_am_sf")
    p_final = latest_summary(row, "pgrb")
    classification = pair_class(k_final, p_final)
    winner = "none"
    if classification.endswith("k1_faster") or "k1_better" in classification:
        winner = "k1_am_sf"
    elif classification.endswith("pgrb_faster") or "pgrb_better" in classification:
        winner = "pgrb"
    elif classification.endswith("tie"):
        winner = "tie"
    state = extension_state(row)
    return {
        "scenario_id": row["scenario_id"],
        "K1_screen_status": k_screen.get("native_status") if k_screen else "pending",
        "PGRB_screen_status": p_screen.get("native_status") if p_screen else "pending",
        "K1_final_status": k_final.get("native_status") if k_final else "pending",
        "PGRB_final_status": p_final.get("native_status") if p_final else "pending",
        "K1_certificate": bool(k_final and k_final["strict_certificate"]),
        "PGRB_certificate": bool(p_final and p_final["strict_certificate"]),
        "K1_wall_time": k_final.get("actual_wall_time_seconds") if k_final else None,
        "PGRB_wall_time": p_final.get("actual_wall_time_seconds") if p_final else None,
        "K1_work": k_final.get("gurobi_work") if k_final else None,
        "PGRB_work": p_final.get("gurobi_work") if p_final else None,
        "K1_valid_LB": k_final.get("valid_lower_bound") if k_final else None,
        "PGRB_valid_LB": p_final.get("valid_lower_bound") if p_final else None,
        "K1_verified_UB": k_final.get("verified_upper_bound") if k_final else None,
        "PGRB_verified_UB": p_final.get("verified_upper_bound") if p_final else None,
        "K1_relative_gap": k_final.get("relative_gap") if k_final else None,
        "PGRB_relative_gap": p_final.get("relative_gap") if p_final else None,
        "current_pair_classification": classification,
        "current_winner_at_common_horizon": winner,
        "extension_state": state, "pair_complete": state == "complete",
        "severe_regression_flag": False,
        "last_update_timestamp_utc": now_utc(),
    }


def refresh_live_pairs() -> list[dict[str, Any]]:
    rows = [live_pair_row(row) for row in panel()]
    r58.write_csv(r58.LIVE_PAIRS, rows, PAIR_FIELDS, atomic=True)
    return rows


def write_live_status(**updates: Any) -> None:
    state: dict[str, Any] = {}
    if r58.LIVE_STATUS.is_file():
        state = object_json(r58.LIVE_STATUS)
    state.update(updates)
    state["schema"] = "round58-live-status-v1"
    state["updated_at_utc"] = now_utc()
    markers = all_markers()
    state["completed_run_count"] = len(markers)
    state["completed_screen_arm_count"] = sum(
        marker["summary"]["process_cap_seconds"] == 3600 for marker in markers)
    state["screen_pair_count"] = sum(
        marker_summary(row, "k1_am_sf", 3600) is not None and
        marker_summary(row, "pgrb", 3600) is not None for row in panel())
    state["optimizer_processes_allowed_concurrently"] = 1
    r58.atomic_write_json(r58.LIVE_STATUS, state)


def validate_result_identity(row: dict[str, str], method: str, cap: int,
                             identity: str, result: dict[str, Any]) -> None:
    failures = []
    if result.get("run_identity_sha256") != identity:
        failures.append("run_identity")
    if result.get("mathematical_instance_sha256") != row["scenario_sha256"]:
        failures.append("scenario_sha256")
    if int(float(result.get("route_time_limit_seconds", -1))) != int(row["T_seconds"]):
        failures.append("T")
    if int(float(result.get("solver_process_cap_seconds", -1))) != cap:
        failures.append("process_cap")
    if method == "k1_am_sf":
        if result.get("method") != "gcap-frontier":
            failures.append("k1_method")
        if result.get("algorithm_preset") != "paper-k1-am-sf":
            failures.append("k1_preset")
        # The frozen public preset is K1-AM-SF.  Its historical native result
        # token remains K1-AM for schema compatibility and is audited together
        # with the first-class preset and frozen SF station-state policy.
        if result.get("external_gini_tree_algorithm_arm") != "K1-AM":
            failures.append("k1_algorithm_arm")
        if result.get("round48_k1_amf") not in (None, "off"):
            failures.append("round48_not_off")
        if result.get("round49_k1_am_rc") not in (None, "off"):
            failures.append("round49_not_off")
    elif not pgrb_scope_valid(row, result):
        failures.append("pgrb_scope")
    if failures:
        raise RuntimeError(
            f"official result identity failure {row['scenario_id']}/{method}: " +
            ";".join(failures))


def verification_record(row: dict[str, str], result_path: Path) -> dict[str, Any]:
    result = object_json(result_path)
    if not native_incumbent_claimed(result):
        return {
            "schema": "round58-independent-native-result-verification-v1",
            "scenario_id": row["scenario_id"],
            "result_path": r58.repo_path(result_path),
            "result_sha256": r58.sha256_file(result_path),
            "passed": False, "failures": [],
            "original_solution_feasible": False,
            "verification_status": "no_native_incumbent_available",
            "optimization_or_repair_performed": False,
            "independent_verification_seconds": 0.0,
        }
    verified = verify_native_result(row["scenario_id"], result_path)
    if not verified["passed"]:
        raise RuntimeError(
            f"independent incumbent verification failure {row['scenario_id']}: " +
            ";".join(verified["failures"]))
    verified["verification_status"] = "verified_native_incumbent"
    return verified


def next_sequence() -> int:
    markers = all_markers()
    if not markers:
        return 1
    return max(int(marker["summary"]["completion_sequence_number"])
               for marker in markers) + 1


def mark_benchmark_started() -> None:
    manifest = r58.read_json(FINGERPRINTS)
    if manifest.get("benchmark_solves_started") is not True:
        manifest["benchmark_solves_started"] = True
        manifest["first_benchmark_solve_started_at_utc"] = now_utc()
        r58.write_json(FINGERPRINTS, manifest)


def run_one(row: dict[str, str], method: str, cap: int) -> dict[str, Any]:
    existing = completion_marker(row, method, cap)
    if existing is not None:
        append_live_run(existing["summary"])
        return dict(existing["summary"])
    destination = run_dir(row, method, cap)
    if destination.exists() and any(destination.iterdir()):
        raise RuntimeError(
            f"incomplete official run directory retained; manual audit required: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    command, identity = command_for(row, method, cap, destination)
    command_path = destination / "command.json"
    result_path = destination / "result.json"
    verification_path = destination / "independent_verification.json"
    started_timestamp = now_utc()
    command_record = {
        "schema": "round58-official-command-v1", "official_benchmark_run": True,
        "scenario_id": row["scenario_id"], "scenario_sha256": row["scenario_sha256"],
        "dataset_family": r58.DATASET_FAMILY, "method": method,
        "method_label": METHOD_LABEL[method], "run_stage": STAGE_BY_CAP[cap],
        "process_cap_seconds": cap, "fresh_process": True,
        "source_freeze_commit": SOURCE_FREEZE, "executable_sha256": EXE_SHA256,
        "solver_contract_sha256": r58.sha256_file(CONTRACT),
        "run_identity_sha256": identity, "started_at_utc": started_timestamp,
        "started": True, "completed": False, "command": command,
    }
    r58.write_json(command_path, command_record)
    mark_benchmark_started()
    write_live_status(
        state="running", current_scenario_id=row["scenario_id"],
        current_method=method, current_stage=STAGE_BY_CAP[cap],
        current_process_cap_seconds=cap, current_run_identity_sha256=identity,
        current_run_started_at_utc=started_timestamp,
        current_run_elapsed_seconds=0.0)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    print(f"START {row['scenario_id']} {method} {STAGE_BY_CAP[cap]} cap={cap}",
          flush=True)
    with (destination / "stdout.log").open("wb") as stdout, \
            (destination / "stderr.log").open("wb") as stderr:
        process = subprocess.Popen(
            command, cwd=r58.ROOT, env=environment, stdout=stdout, stderr=stderr)
        watchdog = False
        last_status = 0.0
        try:
            while process.poll() is None:
                elapsed = time.monotonic() - started
                if elapsed - last_status >= 15.0:
                    write_live_status(current_run_elapsed_seconds=elapsed,
                                      current_process_id=process.pid)
                    last_status = elapsed
                if elapsed > cap + 180.0:
                    watchdog = True
                    process.terminate()
                    try:
                        process.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    break
                time.sleep(1.0)
        except BaseException:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
            raise
        return_code = process.wait()
    runner_wall = time.monotonic() - started
    command_record.update({
        "completed": result_path.is_file(), "completed_at_utc": now_utc(),
        "return_code": return_code, "watchdog_timeout": watchdog,
        "runner_wall_seconds": runner_wall,
    })
    r58.write_json(command_path, command_record)
    if watchdog or return_code != 0 or not result_path.is_file():
        write_live_status(state="execution_failure", current_run_elapsed_seconds=runner_wall)
        raise RuntimeError(f"official execution failed: {row['scenario_id']}/{method}/{cap}")
    result = object_json(result_path)
    validate_result_identity(row, method, cap, identity, result)
    verification = verification_record(row, result_path)
    r58.write_json(verification_path, verification)
    timestamp = now_utc()
    summary = summarize_result(
        row, method, cap, result_path, verification_path, timestamp,
        next_sequence())
    marker = {
        "schema": "round58-official-completion-v1", "complete": True,
        "official_benchmark_run": True, "scenario_id": row["scenario_id"],
        "scenario_sha256": row["scenario_sha256"], "method": method,
        "run_stage": STAGE_BY_CAP[cap], "process_cap_seconds": cap,
        "fresh_process": True, "source_freeze_commit": SOURCE_FREEZE,
        "executable_sha256": EXE_SHA256,
        "solver_contract_sha256": r58.sha256_file(CONTRACT),
        "run_identity_sha256": identity,
        "command_sha256": r58.sha256_file(command_path),
        "result_sha256": r58.sha256_file(result_path),
        "verification_sha256": r58.sha256_file(verification_path),
        "runner_wall_seconds": runner_wall,
        "cap_respected": finite(summary["actual_wall_time_seconds"]) and float(
            summary["actual_wall_time_seconds"]) <= cap + max(2.0, 0.01 * cap),
        "summary": summary,
    }
    r58.write_json(destination / "completion_marker.json", marker)
    append_live_run(summary)
    refresh_live_pairs()
    write_live_status(
        state="between_runs", current_run_completed_at_utc=timestamp,
        current_run_elapsed_seconds=runner_wall, current_process_id=None)
    print(
        f"DONE {row['scenario_id']} {method} {STAGE_BY_CAP[cap]} "
        f"cert={summary['strict_certificate']} rel={summary['relative_gap']} "
        f"wall={summary['actual_wall_time_seconds']}", flush=True)
    return summary


def execution_order(rows: Iterable[dict[str, str]]) -> Iterable[tuple[dict[str, str], str]]:
    for row in rows:
        yield row, row["method_first"]
        yield row, row["method_second"]


def stage_result_rows(cap: int) -> list[dict[str, Any]]:
    rows = []
    for scenario in panel():
        for method in METHODS:
            summary = marker_summary(scenario, method, cap)
            if summary:
                rows.append(summary)
    return rows


def emit_stage_evidence() -> None:
    screen = stage_result_rows(3600)
    if screen:
        r58.write_csv(SCREEN_RESULTS, screen, RUN_FIELDS, atomic=True)
    decisions = [value for row in panel() if (value := screen_action(row))]
    if decisions:
        r58.write_csv(SCREEN_DECISIONS, decisions, atomic=True)
    long_rows = stage_result_rows(10800)
    if long_rows:
        r58.write_csv(LONG_RESULTS, long_rows, RUN_FIELDS, atomic=True)
    near = []
    for row in panel():
        for method in METHODS:
            value = near_action(row, method)
            if value:
                post = post_16200_action(row, method)
                value["post_16200_authorized_next_cap_seconds"] = (
                    post.get("authorized_next_cap_seconds") if post else None)
                value["post_16200_decision_reason"] = (
                    post.get("decision_reason") if post else None)
                near.append(value)
    if near:
        r58.write_csv(NEAR_DECISIONS, near, atomic=True)
    rows_16200 = stage_result_rows(16200)
    if rows_16200:
        r58.write_csv(EXTENDED_16200, rows_16200, RUN_FIELDS, atomic=True)
    rows_21600 = stage_result_rows(21600)
    if rows_21600:
        r58.write_csv(EXTENDED_21600, rows_21600, RUN_FIELDS, atomic=True)


def require_screen_complete() -> None:
    missing = [
        f"{row['scenario_id']}/{method}" for row in panel() for method in METHODS
        if marker_summary(row, method, 3600) is None]
    if missing:
        raise RuntimeError(f"mandatory screen incomplete ({len(missing)} arms): {missing[0]}")


def run_screen() -> None:
    for row, method in execution_order(panel()):
        run_one(row, method, 3600)
        if (marker_summary(row, "k1_am_sf", 3600) and
                marker_summary(row, "pgrb", 3600)):
            emit_stage_evidence()
    require_screen_complete()
    emit_stage_evidence()


def run_long() -> None:
    require_screen_complete()
    selected: list[dict[str, str]] = []
    decisions = {row["scenario_id"]: screen_action(row) for row in panel()}
    for row, method in execution_order(panel()):
        decision = decisions[row["scenario_id"]]
        key = "extend_k1_to_10800" if method == "k1_am_sf" else "extend_pgrb_to_10800"
        if decision and decision[key]:
            run_one(row, method, 10800)
            selected.append(row)
    emit_stage_evidence()


def require_long_complete() -> None:
    for row in panel():
        decision = screen_action(row)
        if not decision:
            raise RuntimeError("screen decisions are not complete")
        for method, key in (("k1_am_sf", "extend_k1_to_10800"),
                            ("pgrb", "extend_pgrb_to_10800")):
            if decision[key] and marker_summary(row, method, 10800) is None:
                raise RuntimeError(f"authorized long run missing: {row['scenario_id']}/{method}")


def run_near() -> None:
    require_long_complete()
    tasks_16200: set[tuple[str, str]] = set()
    tasks_21600: set[tuple[str, str]] = set()
    for row in panel():
        for method in METHODS:
            decision = near_action(row, method)
            if decision and decision["authorized_next_cap_seconds"] == 16200:
                tasks_16200.add((row["scenario_id"], method))
            elif decision and decision["authorized_next_cap_seconds"] == 21600:
                tasks_21600.add((row["scenario_id"], method))
    for row, method in execution_order(panel()):
        if (row["scenario_id"], method) in tasks_16200:
            run_one(row, method, 16200)
    for row in panel():
        for method in METHODS:
            post = post_16200_action(row, method)
            if post and post["authorized_next_cap_seconds"] == 21600:
                tasks_21600.add((row["scenario_id"], method))
    for row, method in execution_order(panel()):
        if (row["scenario_id"], method) in tasks_21600:
            run_one(row, method, 21600)
    emit_stage_evidence()


def protocol_audit() -> dict[str, Any]:
    require_screen_complete()
    require_long_complete()
    unauthorized: list[str] = []
    missing_near: list[str] = []
    for row in panel():
        for method in METHODS:
            near = near_action(row, method)
            allowed_16200 = bool(near and near["authorized_next_cap_seconds"] == 16200)
            allowed_21600 = bool(near and near["authorized_next_cap_seconds"] == 21600)
            if marker_summary(row, method, 16200):
                if not allowed_16200:
                    unauthorized.append(f"{row['scenario_id']}/{method}/16200")
                post = post_16200_action(row, method)
                allowed_21600 = allowed_21600 or bool(
                    post and post["authorized_next_cap_seconds"] == 21600)
            if marker_summary(row, method, 21600) and not allowed_21600:
                unauthorized.append(f"{row['scenario_id']}/{method}/21600")
            target = near.get("authorized_next_cap_seconds") if near else None
            if target and marker_summary(row, method, int(target)) is None:
                missing_near.append(f"{row['scenario_id']}/{method}/{target}")
            post = post_16200_action(row, method)
            if (post and post["authorized_next_cap_seconds"] == 21600 and
                    marker_summary(row, method, 21600) is None):
                missing_near.append(f"{row['scenario_id']}/{method}/21600")
    value = {
        "protocol_complete": not unauthorized and not missing_near,
        "completed_run_count": len(all_markers()),
        "completed_screen_arm_count": len(stage_result_rows(3600)),
        "unauthorized_runs": unauthorized, "missing_authorized_runs": missing_near,
        "maximum_entered_cap_seconds": max(
            (int(marker["process_cap_seconds"]) for marker in all_markers()), default=0),
    }
    if not value["protocol_complete"]:
        raise RuntimeError(json.dumps(value, indent=2))
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--stage", choices=("screen", "long", "near", "all"))
    parser.add_argument("--refresh-live", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    if sum(bool(value) for value in (
            args.preflight, args.stage, args.refresh_live, args.audit)) != 1:
        raise RuntimeError("select exactly one runner action")
    if args.preflight:
        preflight()
        return 0
    preflight()
    rebuild_live_runs()
    refresh_live_pairs()
    if args.refresh_live:
        write_live_status(state="resumed_live_ledgers")
    elif args.audit:
        print(json.dumps(protocol_audit(), indent=2))
    else:
        write_live_status(state="starting_stage", requested_stage=args.stage)
        if args.stage in ("screen", "all"):
            run_screen()
        if args.stage in ("long", "all"):
            run_long()
        if args.stage in ("near", "all"):
            run_near()
        emit_stage_evidence()
        write_live_status(state="stage_complete", completed_stage=args.stage)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
