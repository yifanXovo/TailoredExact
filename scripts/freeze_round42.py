#!/usr/bin/env python3
"""Freeze Round 42 splits, metrics, gates, and evidence identity.

This script deliberately reads no candidate result. Validation selection is an
exhaustive, solver-independent structural stratification of the fourteen rows
outside the unchanged Round 40 diagnostic development panel.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
from typing import Any

import round42_common as common


DEVELOPMENT_ROLES = {
    "round39_small_easy_V10_M1_Q30_slot04_seed1099392856":
        "easy_p_grb_win",
    "round39_small_easy_V12_M3_Q30_slot08_seed1167625600":
        "largest_easy_p_grb_win",
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363":
        "major_fragmentation_regression",
    "round39_small_medium_V8_M3_Q30_slot03_seed1177285734":
        "additional_medium_c6_win",
    "round39_small_medium_V10_M2_Q20_slot05_seed968549317":
        "additional_medium_c6_win",
    "round39_small_hard_V10_M1_Q30_slot02_seed1721447042":
        "hard_p_grb_win",
    "round39_small_hard_V10_M1_Q20_slot01_seed561355351":
        "hard_p_grb_win",
    "round39_small_hard_V12_M3_Q20_slot07_seed621538683":
        "numerical_fail_closed_endpoint",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114":
        "strongest_k4_positive_control",
    "round39_small_hard_V10_M3_Q20_slot04_seed1145042375":
        "additional_hard_c6_win",
}

VALIDATION_QUOTAS = {
    "small-easy": 3,
    "small-medium": 2,
    "small-hard": 2,
}


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def choose_stratified(rows: list[dict[str, Any]], quota: int) -> list[str]:
    ordered = sorted(rows, key=lambda row: (
        row["difficulty_score"], row["V"], row["M"], row["Q"],
        row["instance_id"]))
    n = len(ordered)
    target_quantiles = [(index + 0.5) / quota for index in range(quota)]
    ranked = {row["instance_id"]: (index + 0.5) / n
              for index, row in enumerate(ordered)}

    def objective(combo: tuple[dict[str, Any], ...]) -> tuple[Any, ...]:
        by_score = sorted(combo, key=lambda row: (
            row["difficulty_score"], row["instance_id"]))
        categorical_coverage = sum(
            len({row[field] for row in combo}) for field in ("V", "M", "Q"))
        quantile_error = sum(
            (ranked[row["instance_id"]] - target) ** 2
            for row, target in zip(by_score, target_quantiles))
        score_span = (by_score[-1]["difficulty_score"] -
                      by_score[0]["difficulty_score"])
        tie = stable_hash("|".join(sorted(
            row["instance_id"] for row in combo)))
        return (-categorical_coverage, quantile_error, -score_span, tie)

    selected = min(itertools.combinations(ordered, quota), key=objective)
    return [row["instance_id"] for row in sorted(selected, key=lambda row: (
        row["difficulty_score"], row["V"], row["M"], row["Q"],
        row["instance_id"]))]


def manifest_row(serial: int, instance_id: str, group: str,
                 role: str, selection_basis: str,
                 inventory: dict[str, dict[str, Any]],
                 descriptors: dict[str, dict[str, Any]]) -> dict[str, Any]:
    item = inventory[instance_id]
    descriptor = descriptors[instance_id]
    return {
        "round_id": 42,
        "serial_order": serial,
        "experiment_group": group,
        "instance_id": instance_id,
        "instance_sha256": item["sha256"],
        "diagnostic_role": role,
        "difficulty_stratum": item["difficulty_stratum"],
        "V": item["V"],
        "M": item["M"],
        "Q": item["Q"],
        "structural_score": descriptor["difficulty_score"],
        "selection_basis": selection_basis,
        "solver_outcomes_used_for_selection": False,
        "candidate_results_observed_before_freeze": False,
        "one_thread": True,
        "gurobi_seed": 0,
        "gurobi_presolve": -1,
        "relative_gap": 0.0,
        "absolute_gap": 0.0,
    }


def main() -> int:
    inventory = common.inventory()
    descriptors = common.descriptor_inventory()
    if set(inventory) != set(descriptors) or len(inventory) != 24:
        raise RuntimeError("Round 39 inventory/descriptor identity mismatch")
    if not set(DEVELOPMENT_ROLES) <= set(inventory):
        raise RuntimeError("development panel is not a subset of Round 39")

    remaining = [descriptors[name] for name in inventory
                 if name not in DEVELOPMENT_ROLES]
    validation_ids: list[str] = []
    for stratum, quota in VALIDATION_QUOTAS.items():
        stratum_rows = [row for row in remaining
                        if row["difficulty_stratum"] == stratum]
        validation_ids.extend(choose_stratified(stratum_rows, quota))
    holdout_ids = sorted(
        set(inventory) - set(DEVELOPMENT_ROLES) - set(validation_ids),
        key=lambda name: (
            descriptors[name]["difficulty_stratum"],
            descriptors[name]["difficulty_score"], name))
    if len(validation_ids) != 7 or len(holdout_ids) != 7:
        raise RuntimeError("Round 42 split cardinality mismatch")
    if set(DEVELOPMENT_ROLES) & set(validation_ids) or \
            set(DEVELOPMENT_ROLES) & set(holdout_ids) or \
            set(validation_ids) & set(holdout_ids):
        raise RuntimeError("Round 42 split overlap")

    development = [manifest_row(
        serial, name, "development", DEVELOPMENT_ROLES[name],
        "unchanged_round40_ten_instance_diagnostic_panel",
        inventory, descriptors)
        for serial, name in enumerate(DEVELOPMENT_ROLES, start=1)]
    validation = [manifest_row(
        serial, name, "validation", "structural_validation",
        "exhaustive_stratum_quota_categorical_coverage_quantile_score_v1",
        inventory, descriptors)
        for serial, name in enumerate(validation_ids, start=1)]
    holdout = [manifest_row(
        serial, name, "final_holdout", "sealed_final_holdout",
        "complement_after_frozen_development_and_validation",
        inventory, descriptors)
        for serial, name in enumerate(holdout_ids, start=1)]

    manifests = {
        "development_manifest.csv": development,
        "validation_manifest.csv": validation,
        "final_holdout_manifest.csv": holdout,
    }
    for name, rows in manifests.items():
        common.write_csv(common.OUT / name, rows)

    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=common.ROOT,
        text=True).strip()
    if head != "75fe23e591a39b54f7940eb0012a245e3a92d955":
        raise RuntimeError(f"unexpected Round 42 source head: {head}")
    manifest_hashes = {
        name: common.sha256(common.OUT / name) for name in manifests
    }
    split_signature = stable_hash(json.dumps({
        "development": list(DEVELOPMENT_ROLES),
        "validation": validation_ids,
        "holdout": holdout_ids,
        "manifest_hashes": manifest_hashes,
    }, sort_keys=True))
    freeze = {
        "schema": "round42-experiment-split-freeze-v1",
        "round_id": 42,
        "frozen_before_any_round42_candidate_run": True,
        "source_head": head,
        "round39_inventory_sha256": common.sha256(
            common.ROUND39 / "frozen_instance_manifest.csv"),
        "round39_descriptor_sha256": common.sha256(common.DESCRIPTORS),
        "freeze_script_sha256": common.sha256(
            common.ROOT / "scripts" / "freeze_round42.py"),
        "development_count": len(development),
        "validation_count": len(validation),
        "final_holdout_count": len(holdout),
        "validation_quota_by_stratum": VALIDATION_QUOTAS,
        "validation_selection_algorithm": (
            "within each difficulty stratum exhaust all quota-sized subsets; "
            "lexicographically maximize distinct V/M/Q levels, minimize "
            "squared empirical difficulty-score quantile error, maximize score "
            "span, then use SHA-256 of sorted instance IDs as tie-breaker"),
        "selection_is_solver_independent": True,
        "candidate_outcomes_used": False,
        "holdout_candidate_results_inspected": False,
        "manifest_sha256": manifest_hashes,
        "split_signature_sha256": split_signature,
        "reference_arms": [
            "C6-HGA-FULL-K4-rho0.01", "External-K1",
            "Round41-ST-K2-P-Core", "P-GRB-where-repair-diagnosis-needed",
        ],
        "solver_contract": {
            "threads": 1, "seed": 0, "presolve": "auto(-1)",
            "mip_gap": 0.0, "mip_gap_abs": 0.0,
            "startup_incumbent": "verified HGA-FULL",
            "certificate_tolerance": 1e-7,
        },
        "materiality": {
            "primary_metric": "exact_phase_gurobi_work",
            "secondary_metric": "exact_phase_time",
            "shifted_time_ratio": "(candidate_seconds+1)/(C6_seconds+1)",
            "material_win_max_ratio": 0.95,
            "material_loss_min_ratio": 1.05,
        },
        "development_gates": {
            "fragmentation_max_work_ratio": 0.80,
            "fragmentation_max_shifted_time_ratio": 0.80,
            "positive_control_max_work_ratio": 1.10,
            "positive_control_max_shifted_time_ratio": 1.10,
            "geomean_work_ratio_max": 0.90,
            "geomean_shifted_time_ratio_max": 0.95,
            "no_joint_ratio_above": 1.25,
            "zero_false_certificates": True,
            "no_certificate_regression": True,
        },
        "validation_gates": {
            "geomean_work_ratio_max": 0.95,
            "geomean_shifted_time_ratio_max": 0.98,
            "wins_at_least_losses": True,
            "no_joint_ratio_above": 1.25,
            "zero_false_certificates": True,
            "no_certificate_regression": True,
        },
        "holdout_gates": {
            "geomean_work_ratio_max": 1.00,
            "geomean_shifted_time_ratio_max": 1.00,
            "wins_at_least_losses": True,
            "no_joint_ratio_above": 1.25,
            "zero_false_certificates": True,
            "no_certificate_regression": True,
        },
        "runtime_policy_seconds": {
            "smoke_max": 600, "development_max": 1800,
            "validation_holdout_max": 3600,
            "symmetric_two_row_extension_max": 7200,
        },
        "validated_default_unchanged": "C6-HGA-FULL K=4 rho=0.01",
    }
    common.write_json(common.OUT / "experiment_split_freeze.json", freeze)
    common.write_json(common.OUT / "split_freeze.json", freeze)
    common.write_text(common.OUT / "source_of_truth.md", f"""# Round 42 source of truth

- Existing repository only; source is verified Round 41 commit `{head}`.
- Research branch: `codex/round42-decomposition-architecture-optimization`.
- Frozen benchmark: all 24 Round 39 instances, partitioned 10/7/7 before any
  Round 42 candidate execution.
- Split signature: `{split_signature}`.
- Solver contract: verified HGA-FULL start, Threads 1, Seed 0, Gurobi Presolve
  Auto, zero relative and absolute MIP gaps.
- Primary performance metric: exact-phase Gurobi Work. Secondary: shifted
  exact-phase time ratio `(candidate+1)/(C6+1)`.
- Validated default remains `C6-HGA-FULL, K=4, rho=0.01`.
- Every Round 42 mechanism is explicit and default-off.
- Raw runs remain under `results/gf_decomposition_architecture_optimization_round42/runs/`;
  compact manifests, hashes, audits, and reports are the committed evidence.
""")
    common.write_text(common.OUT / "scientific_problem_statement.md", """# Scientific problem statement

External K4 decomposition has two opposing effects: quarter-width Gini ranges
strengthen the interval-local formulation, while independent terminal MIP jobs
fragment proof search. Round 41 showed that a static segmented Core model is
exact and feasible at K2, but changed both granularity and proof architecture.

Round 42 holds the validated K4 interval endpoints, HGA-FULL incumbent, rho,
presolve, seed, thread count, and certificate contract fixed while testing
three bounded architectures: one static K4 proof tree, two adjacent K4-pair
blocks, and C6 terminal sibling coalescing. The objective is either a unified
candidate that passes development, validation, and sealed holdout gates, or a
bounded systematic negative result after every feasible family and its
required uniform refinement is completed.
""")
    print(json.dumps({
        "development": len(development),
        "validation": len(validation),
        "holdout": len(holdout),
        "split_signature_sha256": split_signature,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
