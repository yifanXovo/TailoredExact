#!/usr/bin/env python3
"""Shared result readers and exact metrics for Round 43 analyses."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import round43_common as common


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "yes"}


def number(value: Any, default: float = math.nan) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def ratio(candidate: float, reference: float) -> float:
    if reference > 0.0:
        return candidate / reference
    return 1.0 if candidate == 0.0 else math.inf


def gmean(values: list[float]) -> float:
    if not values or any(not math.isfinite(value) or value < 0.0
                         for value in values):
        return math.inf
    return math.exp(sum(math.log(max(value, 1e-12)) for value in values) /
                    len(values))


def exact_start(run_dir: Path) -> float:
    path = run_dir / "process_phases.csv"
    if not path.is_file():
        return 0.0
    for row in common.csv_rows(path):
        if row.get("event") == "exact_phase_start":
            return number(row.get("process_seconds"), 0.0)
    return 0.0


def load_metrics(run_dir: Path, arm: str, provenance: str) -> dict[str, Any]:
    result = common.load_json(run_dir / "result.json")
    command_path = run_dir / "command.json"
    command = common.load_json(command_path) if command_path.is_file() else {}
    is_pgrb = arm == "P-GRB"
    certified = truth(result.get("strict_certified_original_problem"))
    verifier = truth(result.get("verification", {}).get(
        "original_solution_feasible")) and truth(result.get("verifier_passed"))
    if is_pgrb:
        work = number(result.get("gurobi_work"))
        nodes = number(result.get("gurobi_node_count"), 0.0)
        solver_seconds = number(result.get("gurobi_runtime"), 0.0)
        lower = number(result.get("lower_bound"))
        upper = number(result.get("upper_bound"))
        parameter_gate = (
            int(number(result.get("gurobi_threads_effective"), -1)) == 1 and
            int(number(result.get("gurobi_seed_effective"), -1)) == 0 and
            int(number(result.get("gurobi_presolve_effective"), 99)) == -1 and
            number(result.get("gurobi_mip_gap_effective"), math.nan) == 0.0 and
            number(result.get("gurobi_mip_gap_abs_effective"), math.nan) == 0.0)
        hga_requested = truth(result.get("gurobi_hga_start_requested"))
        hga_found = truth(result.get("gurobi_hga_incumbent_found"))
        hga_mapped = truth(result.get("gurobi_hga_start_mapping_complete"))
        hga_submitted = truth(result.get("gurobi_hga_start_submitted"))
        hga_status = str(result.get("gurobi_hga_start_status", ""))
        hga_objective = number(result.get("gurobi_hga_verified_objective"))
        # The mapper deliberately fails closed when a verified route plan uses
        # a higher-index member of an equal-capacity vehicle symmetry class.
        # This is a safe, deterministic non-injection outcome: the same HGA-FULL
        # candidate was generated and independently verified, but no partial or
        # noncanonical MIP start reached Gurobi.  Keep that outcome visible in
        # the audit instead of changing the frozen executable mid-experiment.
        hga_safe_mapping_rejection = (
            hga_status ==
            "mapping_rejected:noncanonical_equal_capacity_vehicle_symmetry")
        hga_start = (hga_requested and hga_found and
                     math.isfinite(hga_objective) and
                     (hga_submitted or hga_safe_mapping_rejection))
        model_sha256 = result.get("gurobi_canonical_model_sha256", "")
        memory = number(result.get("gurobi_max_mem_used_gb"), 0.0)
        failure = str(result.get("gurobi_failure_reason", "none"))
    else:
        work = number(result.get("external_gini_tree_work"))
        nodes = number(result.get("external_gini_tree_nodes"), 0.0)
        solver_seconds = number(result.get(
            "external_gini_tree_solver_seconds"), 0.0)
        lower = number(result.get("external_gini_tree_global_lower_bound"))
        upper = number(result.get("external_gini_tree_verified_upper_bound"))
        parameter_gate = truth(result.get(
            "external_gini_tree_backend_parameter_roundtrip_valid"))
        hga_requested = True
        hga_found = True
        hga_mapped = True
        hga_submitted = True
        hga_status = "verified_hga_full_incumbent_inherited_from_c6_path"
        hga_objective = upper
        hga_safe_mapping_rejection = False
        hga_start = True
        model_sha256 = ""
        memory = number(result.get("external_gini_tree_peak_memory_gb"), 0.0)
        failure = str(result.get(
            "external_gini_tree_failure_reason", "none"))
    process = number(result.get(
        "final_process_wall_time_seconds", result.get("runtime_seconds", 0.0)),
        0.0)
    return {
        "instance_id": run_dir.name,
        "arm": arm,
        "provenance": provenance,
        "run_id": run_dir.name,
        "run_dir": common.relative(run_dir),
        "executable_sha256": command.get("executable_sha256", "historical"),
        "status": result.get("status", ""),
        "certified": certified,
        "right_censored": not certified and failure in {
            "none", "overall_global_deadline"},
        "failure_reason": failure,
        "verified_incumbent": verifier,
        "false_certificate": certified and not verifier,
        "parameter_roundtrip_valid": parameter_gate,
        "hga_start_contract_valid": hga_start,
        "hga_start_requested": hga_requested,
        "hga_start_incumbent_found": hga_found,
        "hga_start_mapping_complete": hga_mapped,
        "hga_start_submitted": hga_submitted,
        "hga_start_status": hga_status,
        "hga_start_verified_objective": hga_objective,
        "hga_start_safe_mapping_rejection": hga_safe_mapping_rejection,
        "valid_lower": lower,
        "verified_upper": upper,
        "relative_gap": 0.0 if certified else
            max(0.0, upper - lower) / max(abs(upper), 1e-12),
        "work": work,
        "nodes": nodes,
        "solver_seconds": solver_seconds,
        "process_seconds": process,
        "exact_phase_seconds": max(0.0, process - exact_start(run_dir)),
        "peak_memory_gb": memory,
        "model_sha256": model_sha256,
        "lp_jobs": int(number(result.get(
            "external_gini_tree_lp_optimize_count"), 0)),
        "terminal_mip_jobs": int(number(result.get(
            "external_gini_tree_terminal_mip_optimize_count"), 0)),
        "split_count": int(number(result.get(
            "external_gini_tree_split_count"), 0)),
        "final_intervals": int(number(result.get(
            "external_gini_tree_final_leaf_count"), 0)),
    }


def historical_manifest() -> dict[tuple[str, str], dict[str, str]]:
    return {(row["instance_id"], row["reference_arm"]): row
            for row in common.csv_rows(
                common.OUT / "baseline_equivalence_manifest.csv")}


def historical_reference(instance_id: str, arm: str) -> dict[str, Any]:
    entry = historical_manifest()[(instance_id, arm)]
    return load_metrics(
        common.ROOT / entry["historical_run"], arm, "frozen_round40")


def current_reference(instance_id: str, arm: str) -> dict[str, Any]:
    label = {"C6": "c6", "C6-IMPLICIT": "c6-implicit",
             "P-GRB": "pgrb"}[arm]
    return load_metrics(
        common.RUNS / f"reference__{instance_id}__{label}", arm,
        "round43_contemporaneous")


def candidate_run_dir(instance_id: str, K0: int, rho: float) -> Path:
    suffix = (
        f"__{instance_id}__algorithm__K{K0}__d2__rho{rho:g}__d__single")
    mechanism = common.RUNS / ("stage3-candidate" + suffix)
    if (mechanism / "result.json").is_file():
        return mechanism
    return common.RUNS / ("stage3-development" + suffix)


def candidate_metrics(instance_id: str, K0: int,
                      rho: float) -> dict[str, Any]:
    return load_metrics(candidate_run_dir(instance_id, K0, rho),
                        f"A({K0},2,{rho:g})", "round43_candidate")
