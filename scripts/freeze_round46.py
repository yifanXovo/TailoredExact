#!/usr/bin/env python3
"""Freeze the Round 46 C6 rho screen before any candidate result exists."""

from __future__ import annotations

import csv
import hashlib
import json
import platform
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_rho_k1_k4_screen_round46"
RUNS = OUT / "runs"
ROUND45_HEAD = "1313086b8d1e1b1c163a8bf1c4011f08e8534dc8"
ROUND45_TREE = "fd1378ef7f93f444049d21dba58e104a0fed446d"
BRANCH = "codex/round46-c6-rho-k1-k4-screen"
RHO_GRID = (0.01, 0.12, 0.15, 0.20, 0.50)

DEVELOPMENT = (
    ("round39_small_medium_V12_M3_Q30_slot08_seed1343324363",
     "reference/qualification_round39/small-medium/round39_small_medium_V12_M3_Q30_slot08_seed1343324363.txt",
     "major_fragmentation_regression"),
    ("round39_small_hard_V12_M3_Q30_slot08_seed1288546114",
     "reference/qualification_round39/small-hard/round39_small_hard_V12_M3_Q30_slot08_seed1288546114.txt",
     "strongest_k4_positive_control"),
    ("round39_small_hard_V10_M1_Q20_slot01_seed561355351",
     "reference/qualification_round39/small-hard/round39_small_hard_V10_M1_Q20_slot01_seed561355351.txt",
     "hard_pgrb_win_guard"),
    ("round39_small_medium_V10_M2_Q20_slot05_seed968549317",
     "reference/qualification_round39/small-medium/round39_small_medium_V10_M2_Q20_slot05_seed968549317.txt",
     "medium_c6_win_guard"),
    ("round39_small_hard_V10_M3_Q20_slot04_seed1145042375",
     "reference/qualification_round39/small-hard/round39_small_hard_V10_M3_Q20_slot04_seed1145042375.txt",
     "hard_c6_win_guard"),
    ("round39_small_hard_V12_M3_Q20_slot07_seed621538683",
     "reference/qualification_round39/small-hard/round39_small_hard_V12_M3_Q20_slot07_seed621538683.txt",
     "numerical_fail_closed_endpoint"),
    ("round39_small_easy_V12_M3_Q30_slot08_seed1167625600",
     "reference/qualification_round39/small-easy/round39_small_easy_V12_M3_Q30_slot08_seed1167625600.txt",
     "startup_pathology_nonveto"),
    ("tight_T_seed3101",
     "reference/hard_stress/V20_M3/tight_T_seed3101.txt",
     "v20_development_tight_T"),
    ("high_imbalance_seed3201",
     "reference/hard_stress/V20_M3/high_imbalance_seed3201.txt",
     "v20_development_beneficial_refinement_witness"),
    ("moderate_seed3301",
     "reference/hard_stress/V20_M3/moderate_seed3301.txt",
     "v20_development_mandatory_bound_progress_witness"),
)

CONFIRMATION = (
    ("tight_T_seed3102", "reference/hard_stress/V20_M3/tight_T_seed3102.txt",
     "v20_confirmation_tight_T"),
    ("high_imbalance_seed3202",
     "reference/hard_stress/V20_M3/high_imbalance_seed3202.txt",
     "v20_confirmation_high_imbalance"),
    ("moderate_seed3302",
     "reference/hard_stress/V20_M3/moderate_seed3302.txt",
     "v20_confirmation_moderate"),
)

EXPANDED = (
    ("round39_small_medium_V8_M2_Q20_slot02_seed890603285",
     "reference/qualification_round39/small-medium/round39_small_medium_V8_M2_Q20_slot02_seed890603285.txt",
     "expanded_material_confirmation"),
    ("round39_small_hard_V10_M2_Q20_slot03_seed490008310",
     "reference/qualification_round39/small-hard/round39_small_hard_V10_M2_Q20_slot03_seed490008310.txt",
     "expanded_material_confirmation"),
    ("round39_small_hard_V12_M2_Q20_slot06_seed258908503",
     "reference/qualification_round39/small-hard/round39_small_hard_V12_M2_Q20_slot06_seed258908503.txt",
     "expanded_material_confirmation"),
    ("round39_small_medium_V10_M3_Q30_slot06_seed2147082032",
     "reference/qualification_round39/small-medium/round39_small_medium_V10_M3_Q30_slot06_seed2147082032.txt",
     "expanded_material_confirmation"),
)

HISTORICAL = (
    ("results/gf_nonblocking_gurobi_c6_round31/c6_split_strategy.md",
     "original_c6_split_lifecycle_and_rho_001"),
    ("results/gf_nonblocking_gurobi_c6_round31/c6_parameter_freeze.json",
     "original_c6_parameter_contract"),
    ("results/gf_regression_adaptive_round40/k1_vs_k4_comparison.csv",
     "historical_k1_adaptive_vs_k4_auxiliary"),
    ("results/gf_regression_adaptive_round40/final_report.md",
     "round40_k1_context_only"),
    ("results/gf_adaptive_timing_parametric_partition_round45/completion/final_report.md",
     "round45_gamma_veto_context_only"),
    ("results/gf_adaptive_timing_parametric_partition_round45/completion/common_horizon_complex_results.csv",
     "round45_v20_context_only"),
    ("results/gf_adaptive_timing_parametric_partition_round45/completion/k1_vs_k4_completion.csv",
     "round45_k1_k4_context_only"),
)


def git(*args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=ROOT,
                                   text=True).strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"refusing empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def dataset_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for panel, values, opened in (
        ("development", DEVELOPMENT, True),
        ("v20_confirmation", CONFIRMATION, False),
        ("expanded_material_confirmation", EXPANDED, True),
    ):
        for instance, relative, role in values:
            path = ROOT / relative
            if not path.is_file():
                raise RuntimeError(f"frozen input missing: {relative}")
            if "V50" in relative:
                raise RuntimeError(f"V50 forbidden in Round 46: {relative}")
            rows.append({
                "instance": instance,
                "path": relative,
                "sha256": sha256(path),
                "panel": panel,
                "role": role,
                "opened_before_stage4_finalist_freeze": opened,
                "selection_use": panel == "development",
            })
    return rows


def main() -> int:
    if git("branch", "--show-current") != BRANCH:
        raise SystemExit(f"Stage 0 must be frozen on {BRANCH}")
    if git("rev-parse", "HEAD") != ROUND45_HEAD:
        raise SystemExit("Stage 0 source head drifted from completed Round 45")
    if git("rev-parse", "HEAD^{tree}") != ROUND45_TREE:
        raise SystemExit("Stage 0 source tree drifted from completed Round 45")
    if RUNS.exists() and any(path.is_file() for path in RUNS.rglob("*")):
        raise SystemExit("candidate evidence exists before Stage 0 freeze")
    OUT.mkdir(parents=True, exist_ok=True)
    data = dataset_rows()
    write_text(OUT / "research_contract.md", """
# Round 46 research contract

This is a focused, default-off parameter screen of the original C6 lifecycle.
The only algorithmic factors are `K0 in {1,4}` and
`rho in {0.01,0.12,0.15,0.20,0.50}`. Every split point is the midpoint.

K4 uses the original four-interval C6 cover. K1 uses only
`round40_c6_coarse_start=k1-adaptive`, begins with one complete
strict-improver interval, and then executes the identical C6 child-LP,
native-target, split/retain, requeue, and exact-closure lifecycle.

Gamma-veto, Gamma_sum, D_R43, Round 44 envelope-tail decisions, PMM/FPMM,
rank-1 CGLP cuts, frontier consolidation, verified MIP starts, and every
instance-, size-, time-, Work-, node-, memory-, or hardware-dependent choice
are forbidden. Round 43--45 results are historical context only.

All official comparisons use Gurobi Auto presolve, Seed 0, Threads 1, zero
relative and absolute MIP gaps, HGA-FULL, midpoint, certificate tolerance
1e-7, and an end-to-end process cap no greater than 1800 seconds. Timing and
Work are outcomes only.

The complete 100-row Stage 3 grid is mandatory. Stage 4 and Stage 5 arms are
selected only through the frozen gates. This round is screening and
confirmation, not paper-algorithm validation.
""")
    write_text(OUT / "source_of_truth.md", """
# Round 46 source of truth

The immutable Stage 0 contract consists of this file, `research_contract.md`,
`solver_contract.json`, `dataset_freeze.json`, `rho_grid_freeze.json`,
`arm_definition.json`, `build_policy.json`,
`historical_reference_manifest.csv`, `pgrb_equivalence_manifest.csv`,
`promotion_gates.json`, `official_start_record.json`, and
`stage0_freeze_manifest.json`.

Official runtime evidence is valid only when a completion marker and an
artifact manifest bind it to the single frozen official executable. Candidate
selection is authoritative only in `stage3_candidate_freeze.json`; finalist
selection is authoritative only in `stage4_finalist_freeze.json`. Final claims
are authoritative only in `final_decision.json` after all completion gates
pass. Raw run directories are immutable after sealing.

Historical Round 31/40/45 files are auxiliary references by path, commit, and
SHA-256. They are never candidate rows and never change the frozen rho grid.
""")
    write_json(OUT / "solver_contract.json", {
        "schema": "round46-solver-contract-v1",
        "backend": "gurobi",
        "gurobi_version": "13.0.2",
        "presolve": "Auto",
        "seed": 0,
        "threads": 1,
        "mip_gap": 0.0,
        "mip_gap_abs": 0.0,
        "certificate_tolerance": 1e-7,
        "objective": "complete_original_objective",
        "incumbent": "independently_verified_hga_full",
        "gini_range": "complete_strict_improver_range",
        "split_point": "midpoint",
        "maximum_process_cap_seconds": 1800,
        "required_common_horizons_seconds": [300, 1200, 1800],
        "forbidden_algorithm_inputs": [
            "instance_identity", "instance_size", "time", "work", "nodes",
            "memory", "hardware", "historical_winner", "known_optimum"],
    })
    write_json(OUT / "dataset_freeze.json", {
        "schema": "round46-dataset-freeze-v1",
        "frozen_before_candidate_results": True,
        "no_generated_instances": True,
        "no_v50": True,
        "development_count": len(DEVELOPMENT),
        "v20_confirmation_count": len(CONFIRMATION),
        "expanded_confirmation_count": len(EXPANDED),
        "instances": data,
    })
    write_json(OUT / "rho_grid_freeze.json", {
        "schema": "round46-rho-grid-freeze-v1",
        "frozen_before_candidate_results": True,
        "K0": [1, 4],
        "rho": list(RHO_GRID),
        "point_rule": "midpoint",
        "arm_count": 10,
        "rho_additions_after_results_forbidden": True,
    })
    arms = []
    for k0 in (4, 1):
        for rho, tag in zip(RHO_GRID, ("r001", "r012", "r015", "r020", "r050")):
            arms.append({
                "arm": f"K{k0}-{tag}", "K0": k0, "rho": rho,
                "coarse_start": "off" if k0 == 4 else "k1-adaptive",
                "lifecycle": "original_c6",
                "point_rule": "midpoint",
                "round43": "off", "round44": "off", "round45": "off",
                "research_default_off": True,
            })
    write_json(OUT / "arm_definition.json", {
        "schema": "round46-arm-definition-v1",
        "frozen_before_candidate_results": True,
        "arms": arms,
        "only_differences": ["K0_initialization", "c6_normalized_split_threshold"],
        "paper_c6_preset_rho": 0.01,
        "historical_old_c6_reconstruction_rho": 0.01,
    })
    write_json(OUT / "build_policy.json", {
        "schema": "round46-build-policy-v1",
        "development_build": "build/dev-gurobi-release",
        "development_configuration": "Release",
        "development_generator": "MinGW Makefiles",
        "development_targets": ["ExactEBRP", "Round31C6Tests",
                                "Round40CoarseStartTests", "Round46C6RhoTests"],
        "official_build_template": "build/official-round46-<short-head-sha>",
        "official_clean_build_count": 1,
        "one_official_executable_for_all_rows": True,
        "source_change_invalidates_all_official_rows": True,
        "build_products_committed": False,
    })
    historical = []
    for relative, role in HISTORICAL:
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"historical reference missing: {relative}")
        historical.append({
            "path": relative, "commit_sha": ROUND45_HEAD,
            "sha256": sha256(path), "role": role,
            "selection_use": False, "rerun_in_round46": False,
        })
    write_csv(OUT / "historical_reference_manifest.csv", historical)
    pgrb = []
    for row in data:
        pgrb.append({
            "instance": row["instance"], "input_path": row["path"],
            "input_sha256": row["sha256"],
            "historical_evidence": "auxiliary_only",
            "historical_semantic_equivalence_accepted": False,
            "round46_disposition": "contemporaneous_single_rerun",
            "duplicate_pgrb_per_rho": False,
            "required_by_section8": row["instance"] in {
                "round39_small_medium_V12_M3_Q30_slot08_seed1343324363",
                "round39_small_hard_V12_M3_Q30_slot08_seed1288546114",
                "round39_small_hard_V10_M3_Q20_slot04_seed1145042375",
                "tight_T_seed3101", "high_imbalance_seed3201",
                "moderate_seed3301", "tight_T_seed3102",
                "high_imbalance_seed3202", "moderate_seed3302"},
        })
    write_csv(OUT / "pgrb_equivalence_manifest.csv", pgrb)
    write_json(OUT / "promotion_gates.json", {
        "schema": "round46-promotion-gates-v1",
        "screening_not_validation": True,
        "candidate_requirements": [
            "zero_false_certificates", "exact_complete_coverage",
            "major_fragmentation_regression_repaired_or_materially_reduced",
            "no_new_severe_pgrb_regression",
            "strong_c6_win_advantage_substantially_retained",
            "v20_aggregate_gi_not_materially_worse_than_original_c6",
            "consistent_v20_development_and_confirmation",
            "no_lp_mechanism_beyond_original_c6"],
        "severe_regression": {
            "work_ratio_over_pgrb": 1.50,
            "time_ratio_over_pgrb": 1.50,
            "minimum_time_delta_seconds": 60,
            "minimum_work_delta": 100,
            "all_ratio_conditions_and_one_delta_condition": True},
        "startup_pathology_cannot_alone_reject": True,
        "paper_preset_replacement_automatic": False,
    })
    status = git("status", "--short").splitlines()
    protected = [
        "results/gf_compact_bc_round/handling_convention_test/handling_convention.json",
        "results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv",
        "results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json",
    ]
    write_json(OUT / "official_start_record.json", {
        "schema": "round46-official-start-record-v1",
        "round_id": 46,
        "frozen_before_candidate_results": True,
        "branch": BRANCH,
        "starting_head": ROUND45_HEAD,
        "starting_tree": ROUND45_TREE,
        "upstream_at_start": "none_new_branch",
        "round45_upstream": "origin/codex/round45-adaptive-timing-parametric-partition",
        "pr95": {"url": "https://github.com/yifanXovo/TailoredExact/pull/95",
                 "state": "OPEN", "draft": True, "head": ROUND45_HEAD,
                 "base": "codex/round44-c6-envelope-tail-repair"},
        "pr96": {"url": "https://github.com/yifanXovo/TailoredExact/pull/96",
                 "state": "OPEN", "draft": False, "head": ROUND45_HEAD,
                 "base": "main"},
        "compiler": "g++.exe (Rev2, Built by MSYS2 project) 14.2.0",
        "cmake": "3.30.5-msvc23",
        "gurobi": "13.0.2 build v13.0.2rc1 win64",
        "machine": platform.node(),
        "working_tree_status_at_freeze": status,
        "protected_tracked_files": [{"path": p, "sha256": sha256(ROOT / p)}
                                    for p in protected],
        "candidate_run_files_present": False,
    })
    frozen_names = (
        "research_contract.md", "source_of_truth.md", "solver_contract.json",
        "dataset_freeze.json", "rho_grid_freeze.json", "arm_definition.json",
        "build_policy.json", "historical_reference_manifest.csv",
        "pgrb_equivalence_manifest.csv", "promotion_gates.json",
        "official_start_record.json",
    )
    write_json(OUT / "stage0_freeze_manifest.json", {
        "schema": "round46-stage0-freeze-manifest-v1",
        "frozen_before_candidate_results": True,
        "starting_head": ROUND45_HEAD,
        "starting_tree": ROUND45_TREE,
        "rho_grid": list(RHO_GRID),
        "K0": [1, 4],
        "point_rule": "midpoint",
        "stage3_candidate_rows": 100,
        "v50_forbidden": True,
        "maximum_process_cap_seconds": 1800,
        "files": [{"path": f"results/gf_c6_rho_k1_k4_screen_round46/{name}",
                   "size_bytes": (OUT / name).stat().st_size,
                   "sha256": sha256(OUT / name)} for name in frozen_names],
    })
    print(json.dumps({"frozen": True, "files": len(frozen_names) + 1,
                      "instances": len(data), "arms": 10,
                      "stage3_rows": 100}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
