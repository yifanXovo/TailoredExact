#!/usr/bin/env python3
"""Freeze Round 44 before any new exact candidate outcome is observed."""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import math
import platform
import subprocess
from pathlib import Path

import round44_common as common


ROUND39 = common.ROOT / "results" / "gf_small_hard_light_round39"
ROUND43 = common.ROOT / "results" / "gf_k1_k4_envelope_refinement_round43"


def git(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=common.ROOT, text=True).strip()


def nearest_rank(values: list[float], quantile: float) -> float:
    if not values:
        raise RuntimeError("empty frozen startup distribution")
    ordered = sorted(values)
    return ordered[max(0, math.ceil(quantile * len(ordered)) - 1)]


def frozen_instances() -> dict[str, dict[str, str]]:
    rows = common.csv_rows(ROUND39 / "round39_official_matrix.csv")
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["arm"] == "P-GRB" and row["stage"] == "primary":
            result.setdefault(row["instance_id"], row)
    missing = sorted(set(common.SMALL_24_IDS) - set(result))
    if missing:
        raise RuntimeError(f"Round 39 instance freeze missing: {missing}")
    return result


def startup_freeze() -> tuple[float, list[dict[str, object]]]:
    rows = common.csv_rows(ROUND39 / "runner_row_summary.csv")
    selected = {
        row["instance_id"]: row for row in rows
        if row["stage"] == "primary" and row["arm"] == "P-GRB" and
        row["instance_id"] in common.SMALL_24_IDS
    }
    if set(selected) != set(common.SMALL_24_IDS):
        raise RuntimeError("startup freeze does not cover the frozen small-24")
    audit = []
    for instance_id in common.SMALL_24_IDS:
        row = selected[instance_id]
        phase_path = ROUND39 / "runs" / row["run_id"] / "process_phases.csv"
        phases = common.csv_rows(phase_path)
        launches = [phase for phase in phases
                    if phase["event"] == "plain_gurobi_optimize_launch"]
        if len(launches) != 1:
            raise RuntimeError(
                f"missing unique candidate-independent launch phase: {phase_path}")
        seconds = float(launches[0]["process_seconds"])
        audit.append({
            "instance_id": instance_id,
            "baseline_arm": "P-GRB",
            "candidate_independent_setup_seconds": seconds,
            "source": common.relative(phase_path),
            "source_sha256": common.sha256(phase_path),
        })
    shift = max(1.0, nearest_rank(
        [float(row["candidate_independent_setup_seconds"]) for row in audit],
        0.95))
    return shift, audit


def dataset_row(instance_id: str, split: str,
                items: dict[str, dict[str, str]]) -> dict[str, object]:
    row = items[instance_id]
    relative_path = (
        Path("reference") / "qualification_round39" /
        row["difficulty_stratum"] / f"{instance_id}.txt")
    path = common.ROOT / relative_path
    return {
        "instance_id": instance_id,
        "split": split,
        "path": relative_path.as_posix(),
        "sha256": common.sha256(path),
        "candidate_results_observed": False,
    }


def main() -> int:
    common.OUT.mkdir(parents=True, exist_ok=True)
    if common.RUNS.exists() and any(common.RUNS.iterdir()):
        raise RuntimeError("Stage 0 must precede every Round 44 candidate run")
    head = git("rev-parse", "HEAD")
    tree = git("rev-parse", "HEAD^{tree}")
    branch = git("branch", "--show-current")
    if head != common.BASE_SHA or tree != common.BASE_TREE_SHA:
        raise RuntimeError(
            f"unexpected Round 44 base: {head} tree {tree}")
    if branch != common.RESEARCH_BRANCH:
        raise RuntimeError(f"unexpected Round 44 branch: {branch}")

    items = frozen_instances()
    startup_shift, startup_rows = startup_freeze()
    datasets = (
        [dataset_row(i, "development", items)
         for i in common.DEVELOPMENT_IDS] +
        [dataset_row(i, "validation", items)
         for i in common.VALIDATION_IDS] +
        [dataset_row(i, "sealed_holdout", items)
         for i in common.HOLDOUT_IDS])
    for path_text, split in (
            *[(p, "additional_v12") for p in common.ADDITIONAL_V12],
            *[(p, "v20_development_profile") for p in common.V20_DEVELOPMENT],
            *[(p, "v20_confirmation") for p in common.V20_CONFIRMATION]):
        path = common.ROOT / path_text
        datasets.append({
            "instance_id": path.stem,
            "split": split,
            "path": path_text,
            "sha256": common.sha256(path),
            "candidate_results_observed": False,
        })

    common.write_text(common.OUT / "research_contract.md", """# Round 44 research contract

Round 44 evaluates one paper-facing **C6-compatible envelope tail repair**
family. K0=4, the C6 exact-cover lifecycle, native frontier targets, verified
HGA-FULL incumbent, exact terminal closure, and fail-closed certification are
preserved. New behavior may replace only a mathematically defined split/retain
decision and is explicit and default-off.

The primary objective is P-GRB-oriented: repair the major fragmentation
regression, eliminate severe P-GRB-relative regressions, and retain a meaningful
fraction of C6's strong-win advantage. Candidate/C6 <= 1 is not a universal
gate. No decision may depend on timing, Work, nodes, memory, hardware, instance
identity, dataset membership, or historical outcomes.

Every mandatory family in Stages 2--5 is required. Validation remains sealed
until one global candidate is frozen after the rank-1 and engineering
ablations; holdout remains sealed until validation passes. V12 and V20 are run
only after the preceding gates trigger them. Exactly one permitted terminal
classification and one scale qualification will be reported.
""")
    erratum = (ROUND43 / "round43_formula_erratum.md").read_text(
        encoding="utf-8")
    common.write_text(common.OUT / "round43_erratum.md", erratum)
    common.write_text(common.OUT / "round43_formula_erratum.md", erratum)
    common.write_text(common.OUT / "source_of_truth.md", f"""# Round 44 source of truth

- Base branch: `{common.BASE_BRANCH}`
- Base commit: `{common.BASE_SHA}`
- Base tree: `{common.BASE_TREE_SHA}`
- Research branch: `{common.RESEARCH_BRANCH}`
- Validated tailored baseline: C6-HGA-FULL, K0=4, rho=0.01
- External comparator: canonical P-GRB
- Solver: Gurobi 13.0.2, Presolve Auto, Seed 0, Threads 1, zero gaps
- Certificate tolerance: 1e-7
- Small-run cap: 3600 seconds; paired extension: 7200 seconds
- V12 cap: 7200 seconds; V20 checkpoints: 300/1200/3600 seconds

Round 43's executable score is `D_R43`, not `P_profile`; see the erratum.
Round 44 raw runs live under `runs/`. Compact committed summaries and manifests
are derived only from completed, noninvalidated rows bound to one frozen
executable. Native logs and large model artifacts may remain local when their
hash, size, signature, generation command, and retention state are published.
""")
    common.write_text(common.OUT / "candidate_family_definition.md", """# Candidate family definition

All primary arms use K0=4 and a shared implementation path.

- A: K4 envelope with no recursive refinement.
- B: unchanged C6 decisions plus parent-only or nested envelope strengthening.
- C: C6 split veto, `old_split AND F >= rho_F`.
- D: veto plus parameter-free decisive-frontier promotion gated by M_root.
- E: F-only, F-and-M_root, or H=F*M_root conservative refinement.
- F: M_root-only causal reference.

Lookahead is fixed-d1, fixed-d2 reference, or bound-driven frontier-d2.
Injection is E-all, E-violated, E-active-one, or causal E-none. Scope is parent
or nested. Every split is a binary midpoint split. D_R43 and P_profile are
diagnostics only; fitted score combinations are forbidden.
""")
    common.write_json(common.OUT / "solver_contract.json", {
        "schema": "round44-solver-contract-v1",
        "gurobi_version": "13.0.2",
        "presolve": "auto",
        "presolve_value": -1,
        "seed": 0,
        "threads": 1,
        "relative_mip_gap": 0.0,
        "absolute_mip_gap": 0.0,
        "certificate_tolerance": 1e-7,
        "startup_incumbent": "independently_verified_HGA_FULL",
        "external_cap_small_seconds": 3600,
        "symmetric_extension_seconds": 7200,
        "additional_v12_cap_seconds": 7200,
        "v20_cap_seconds": 3600,
        "v20_checkpoints_seconds": [300, 1200, 3600],
        "per_instance_tuning": False,
        "known_optimum_injection": False,
    })
    forbidden = [
        "instance_name", "instance_path", "random_seed", "V", "M", "Q",
        "difficulty_label", "historical_winner", "dataset_membership",
        "elapsed_time", "gurobi_work", "node_count", "iterations",
        "memory", "hardware", "leaf_runtime", "learned_classifier",
        "known_instance_table", "external_cap_state",
    ]
    common.write_json(common.OUT / "forbidden_decision_inputs.json", {
        "schema": "round44-forbidden-inputs-v1",
        "forbidden": forbidden,
        "allowed": [
            "interval_endpoints", "exact_cover_tree", "verified_incumbent",
            "valid_lp_or_native_mip_bounds", "valid_infeasibility",
            "next_frontier_target", "valid_envelope_facets",
            "fixed_global_parameters", "certificate_tolerance",
        ],
        "telemetry_excluded_from_decision_hash": True,
    })
    common.write_json(common.OUT / "dataset_freeze.json", {
        "schema": "round44-dataset-freeze-v1",
        "frozen_before_candidate_exact_runs": True,
        "candidate_results_observed": False,
        "datasets": datasets,
        "mechanism_roles": common.MECHANISM_ROLES,
        "validation_state": "sealed",
        "holdout_state": "sealed",
        "v20_candidate_state": "not_yet_frozen",
    })
    common.write_json(common.OUT / "performance_metric_freeze.json", {
        "schema": "round44-performance-metric-freeze-v1",
        "frozen_before_candidate_exact_runs": True,
        "candidate_results_observed": False,
        "startup_time_shift_seconds": startup_shift,
        "startup_time_shift_rule": (
            "max(1 second, nearest-rank 95th percentile of candidate-independent "
            "P-GRB process-entry time on the frozen development+validation+holdout small-24)"),
        "startup_work_shift": 1.0,
        "startup_work_shift_reason": (
            "root/presolve Work is not separated consistently across every "
            "frozen P-GRB/C6 historical row"),
        "startup_audit": startup_rows,
        "shifted_work_ratio": "(W_candidate+s_W)/(W_PGRB+s_W)",
        "shifted_time_ratio": "(T_candidate+s_T)/(T_PGRB+s_T)",
        "severe_regression": {
            "shifted_work_ratio_gt": 1.50,
            "shifted_time_ratio_gt": 1.50,
            "and_delta_time_gt": f"max(60,{10*startup_shift:.17g})",
            "or_delta_work_gt": 100.0,
        },
    })
    common.write_json(common.OUT / "promotion_gates.json", {
        "schema": "round44-promotion-gates-v1",
        "frozen_before_candidate_exact_runs": True,
        "correctness": [
            "zero_false_certificates", "zero_incorrect_optimality_claims",
            "independently_verified_incumbents", "complete_exact_coverage",
            "monotone_valid_global_bound", "default_off_C6_equivalence",
            "fail_closed_censoring",
        ],
        "major_candidate_over_pgrb_work_max": 1.05,
        "major_candidate_over_pgrb_time_max": 1.05,
        "development_shifted_work_gmean_max": 0.90,
        "development_shifted_time_gmean_max": 0.95,
        "development_shifted_work_p90_max": 1.50,
        "material_wins_at_least_losses": True,
        "no_severe_regression": True,
        "c6_advantage_trigger_pgrb_over_c6_work_min": 5.0,
        "candidate_retained_advantage_pgrb_over_candidate_work_min": 2.0,
        "validation_shifted_work_gmean_max": 1.00,
        "validation_shifted_time_gmean_max": 1.05,
        "holdout_same_as_validation": True,
        "additional_v12_shifted_work_gmean_max": 1.00,
        "v20": {
            "candidate_certificates_at_least_pgrb_or_lower_GI_rows_min": 4,
            "no_candidate_specific_engineering_failure": True,
            "no_false_certificate": True,
            "no_severe_solved_regression": True,
        },
    })

    baseline_rows = []
    for row in common.csv_rows(ROUND43 / "default_off_equivalence.csv"):
        baseline_rows.append({
            "kind": "round43_default_off_sentinel",
            "instance_id": row["instance_id"],
            "source": common.relative(
                ROUND43 / "default_off_equivalence.csv"),
            "source_sha256": common.repository_text_sha256(
                ROUND43 / "default_off_equivalence.csv"),
            "equivalence_passed": row["default_off_equivalence_passed"],
            "candidate_results_observed": False,
        })
    for row in startup_rows:
        baseline_rows.append({
            "kind": "candidate_independent_startup_reference",
            "instance_id": row["instance_id"],
            "source": row["source"],
            "source_sha256": row["source_sha256"],
            "equivalence_passed": True,
            "candidate_results_observed": False,
        })
    common.write_csv(common.OUT / "baseline_equivalence_manifest.csv",
                     baseline_rows)
    common.write_json(common.OUT / "official_start_record.json", {
        "schema": "round44-official-start-record-v1",
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "base_branch": common.BASE_BRANCH,
        "base_sha": common.BASE_SHA,
        "base_tree_sha": common.BASE_TREE_SHA,
        "research_branch": common.RESEARCH_BRANCH,
        "candidate_results_observed": False,
        "round44_executable_frozen": False,
        "machine": {
            "node": platform.node(),
            "platform": platform.platform(),
            "processor": platform.processor(),
        },
        "baseline_tests": {
            "release_gurobi_build": "passed_gnu_14.2.0_mingw",
            "ctest": "21/21",
            "python_protocol_scripts": "19/19",
            "round43_default_off": "3/3",
            "msvc_generator_probe": (
                "preexisting_failure_due_to_GNU_builtins_and_Windows_minmax_macros; "
                "not_the_audited_generator"),
        },
    })

    frozen_names = [
        "research_contract.md", "round43_erratum.md",
        "round43_formula_erratum.md", "source_of_truth.md",
        "candidate_family_definition.md", "solver_contract.json",
        "forbidden_decision_inputs.json", "dataset_freeze.json",
        "performance_metric_freeze.json", "promotion_gates.json",
        "baseline_equivalence_manifest.csv", "official_start_record.json",
    ]
    manifest = []
    for name in frozen_names:
        path = common.OUT / name
        manifest.append({
            "path": common.relative(path),
            "sha256": common.repository_text_sha256(path),
            "bytes": path.stat().st_size,
        })
    common.write_json(common.OUT / "stage0_freeze_manifest.json", {
        "schema": "round44-stage0-freeze-manifest-v1",
        "frozen_before_candidate_exact_runs": True,
        "candidate_results_observed": False,
        "base_sha": common.BASE_SHA,
        "base_tree_sha": common.BASE_TREE_SHA,
        "artifact_count": len(manifest),
        "artifacts": manifest,
        "manifest_content_sha256": common.stable_hash(manifest),
    })
    print(json.dumps({
        "stage0_artifacts": len(manifest) + 1,
        "small_panel": len(common.SMALL_24_IDS),
        "startup_time_shift_seconds": startup_shift,
        "startup_work_shift": 1.0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
