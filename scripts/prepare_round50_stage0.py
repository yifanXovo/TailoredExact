#!/usr/bin/env python3
"""Create the immutable Round 50 Stage 0 research freeze.

This script may be run only before any Round 50 optimization result exists.  It
derives historical references from committed Round 45--49 evidence and freezes
selectors for states whose canonical Round 50 identity is reconstructed later.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
ROUND49 = ROOT / "results" / "gf_k1_lp_primal_dual_rescue_round49"
BASE_BRANCH = "codex/round49-k1-lp-primal-dual-rescue"
BRANCH = "codex/round50-k1-interval-mip-vnext"
BASE_HEAD = "550e2e491a270448e0bae4dcdb07cc1e2296a329"
BASE_TREE = "097be172f3944f6449ebaa6adc606caac48af6b7"
PR102_URL = "https://github.com/yifanXovo/TailoredExact/pull/102"
SCHEMA_VERSION = 1


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(OUT).as_posix(),
        "sha256": sha256(path),
        "size_bytes": path.stat().st_size,
    }


def write_text(name: str, text: str) -> None:
    (OUT / name).write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(name: str, value: Any) -> None:
    write_text(name, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def input_path(instance: str) -> Path:
    candidates = list((ROOT / "reference").rglob(f"{instance}.txt"))
    if len(candidates) != 1:
        raise RuntimeError(f"expected one input for {instance}, found {candidates}")
    return candidates[0]


def historical_manifest() -> None:
    source = ROUND49 / "historical_baseline_reference_manifest.csv"
    with source.open(newline="", encoding="utf-8-sig") as handle:
        inherited = list(csv.DictReader(handle))

    fieldnames = [
        "instance", "algorithm", "source_round", "source_path",
        "source_commit", "source_tree", "artifact_sha256", "input_sha256",
        "executable_sha256", "gurobi_version", "machine_identity",
        "process_cap_seconds", "certificate", "work", "total_time_seconds",
        "lower_bound", "verified_upper_bound", "gap", "gi_300", "gi_1200",
        "gi_1800", "split_count", "lp_model_count", "model_count",
        "comparison_status", "source_algorithm_identity",
    ]

    def status(row: dict[str, str]) -> str:
        cap = float(row.get("process_cap_seconds") or 0)
        timing = row.get("comparison_timing", "")
        if cap > 1800 or "context" in timing or "negative" in timing:
            return "historical-contextual"
        return "historical-common-horizon"

    rows: list[dict[str, Any]] = []
    for old in inherited:
        if "V50" in old.get("instance", ""):
            continue
        rows.append({
            "instance": old.get("instance", ""),
            "algorithm": old.get("algorithm", ""),
            "source_round": old.get("source_round", ""),
            "source_path": old.get("source_path", ""),
            "source_commit": old.get("source_commit", ""),
            "source_tree": old.get("source_tree", ""),
            "artifact_sha256": old.get("artifact_sha256", ""),
            "input_sha256": old.get("input_sha256", ""),
            "executable_sha256": old.get("executable_sha256", ""),
            "gurobi_version": old.get("solver_version", ""),
            "machine_identity": old.get("machine", ""),
            "process_cap_seconds": old.get("process_cap_seconds", ""),
            "certificate": old.get("certificate", ""),
            "work": old.get("work", ""),
            "total_time_seconds": old.get("time_seconds", ""),
            "lower_bound": old.get("lower_bound", ""),
            "verified_upper_bound": old.get("verified_upper_bound", ""),
            "gap": old.get("gap", ""),
            "gi_300": old.get("gi_300", ""),
            "gi_1200": old.get("gi_1200", ""),
            "gi_1800": old.get("gi_1800", ""),
            "split_count": old.get("split_count", ""),
            "lp_model_count": old.get("lp_model_count", ""),
            "model_count": old.get("native_target_count", ""),
            "comparison_status": status(old),
            "source_algorithm_identity": old.get("algorithm_identity", ""),
        })

    # Round 49's bounded-negative live candidate becomes historical context here.
    stage3 = ROUND49 / "stage3_300s_results.csv"
    round49_tree = run("git", "rev-parse", "36990fc47c8f86a458e9c068c471ac6ec45454a9^{tree}")
    with stage3.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            run_dir = ROUND49 / "runs" / row["run_id"]
            command = json.loads((run_dir / "command.json").read_text(encoding="utf-8"))
            rows.append({
                "instance": row["instance"],
                "algorithm": "K1-AM-RC",
                "source_round": "49",
                "source_path": (run_dir / "result.json").relative_to(ROOT).as_posix(),
                "source_commit": "36990fc47c8f86a458e9c068c471ac6ec45454a9",
                "source_tree": round49_tree,
                "artifact_sha256": row["result_sha256"],
                "input_sha256": command["instance_sha256"],
                "executable_sha256": row["executable_sha256"],
                "gurobi_version": "13.0.2 build v13.0.2rc1",
                "machine_identity": "WIN-3NO58RVQ4VC",
                "process_cap_seconds": row["process_cap_seconds"],
                "certificate": row["certificate"],
                "work": row["work"],
                "total_time_seconds": row["time_seconds"],
                "lower_bound": row["lower_bound"],
                "verified_upper_bound": row["verified_upper_bound"],
                "gap": row["relative_gap"],
                "gi_300": row["gi_300"],
                "gi_1200": "",
                "gi_1800": "",
                "split_count": row["split_count"],
                "lp_model_count": row["lp_count"],
                "model_count": row["model_count"],
                "comparison_status": "historical-contextual",
                "source_algorithm_identity": "Round 49 bounded-negative K1-AM-RC (D-RCD)",
            })

    rows.sort(key=lambda r: (str(r["instance"]), str(r["algorithm"]), str(r["source_round"])))
    with (OUT / "historical_baseline_reference_manifest.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def fixed_states() -> list[dict[str, Any]]:
    state_columns = [
        "state_id", "panel", "instance", "input_path", "input_sha256",
        "historical_source_run", "interval_id", "parent_id", "gamma_lower",
        "gamma_upper", "split_depth", "verified_cutoff", "cutoff_source",
        "canonical_model_fingerprint", "formulation_profile",
        "row_bound_signature", "objective_sense", "original_variable_mapping",
        "historical_role", "state_kind", "selection_rule", "reconstruction_status",
        "recovery_state_id",
    ]

    specs = [
        ("D1", "development", "round39_small_medium_V12_M3_Q30_slot08_seed1343324363", "L0", "", 0.0, 0.049468682614419446, 0, 0.049468682614419446, "retain historically preferable; severe fragmentation guard", "parent", "explicit K1 root"),
        ("D2", "development", "round39_small_hard_V10_M3_Q20_slot04_seed1145042375", "L0", "", 0.0, 0.50454385216420738, 0, 0.5045438521642074, "complete parent is already easy; harmful-split negative control", "parent", "explicit K1 root"),
        ("D3", "development", "round39_small_hard_V12_M3_Q30_slot08_seed1288546114", "L0", "", 0.0, 0.50642278922416295, 0, 0.506422789224163, "strong-control difficult parent", "parent", "explicit K1 root"),
        ("D4", "development", "round39_small_hard_V12_M3_Q30_slot08_seed1288546114", "L0.0", "L0", 0.0, 0.25321139461208148, 1, 0.506422789224163, "strong-control exact midpoint left child", "child", "exact midpoint child of D3"),
        ("D5", "development", "round39_small_hard_V12_M3_Q30_slot08_seed1288546114", "L0.1", "L0", 0.25321139461208148, 0.50642278922416295, 1, 0.506422789224163, "strong-control exact midpoint right child", "child", "exact midpoint child of D3"),
        ("D6", "development", "round39_small_hard_V12_M2_Q20_slot06_seed258908503", "L0", "", 0.0, 0.70625309852907492, 0, 0.7062530985290749, "V12 M2 historically expensive parent", "parent", "explicit K1 root"),
        ("D7", "development", "round39_small_hard_V12_M2_Q20_slot06_seed258908503", "L0.0", "L0", 0.0, 0.35312654926453746, 1, 0.7062530985290749, "V12 M2 exact midpoint left child", "child", "exact midpoint child of D6"),
        ("D8", "development", "round39_small_hard_V12_M2_Q20_slot06_seed258908503", "L0.1", "L0", 0.35312654926453746, 0.70625309852907492, 1, 0.7062530985290749, "V12 M2 exact midpoint right child", "child", "exact midpoint child of D6"),
        ("D9", "development", "tight_T_seed3102", "L0.0", "L0", 0.0, 0.30035221834255404, 1, 0.6007044366851081, "tight3102 matched difficult parent", "parent", "explicit historical K1-AM L0.0"),
        ("D10", "development", "tight_T_seed3102", "L0.0.0", "L0.0", 0.0, 0.15017610917127702, 2, 0.6007044366851081, "tight3102 exact midpoint left child", "child", "exact midpoint child of D9"),
        ("D11", "development", "tight_T_seed3102", "L0.0.1", "L0.0", 0.15017610917127702, 0.30035221834255404, 2, 0.6007044366851081, "tight3102 exact midpoint right child", "child", "exact midpoint child of D9"),
        ("D12", "development", "round39_small_hard_V12_M3_Q20_slot07_seed621538683", "L0", "", 0.0, 0.64711643345550207, 0, 0.6471164334555021, "numerical-endpoint parent", "parent", "explicit K1 root"),
        ("D13", "development", "high_imbalance_seed3201", "L0.1.0", "L0.1", 0.47499999999999998, 0.71249999999999991, 2, 2.4434031919432, "high-imbalance difficult K1 interval", "child", "largest terminal/native MIP Work in Round 47 K1-AM; tie interval id"),
        ("D14", "development", "moderate_seed3301", "L0.0", "L0", 0.0, 0.024576276332372575, 1, 0.04915255266474515, "moderate3301 difficult K1 interval", "child", "largest terminal/native MIP Work in Round 47 K1-AM; tie interval id"),
        ("C1", "confirmation", "round39_small_hard_V12_M3_Q20_slot07_seed621538683", "L0.0", "L0", 0.0, 0.32355821672775104, 1, 0.6471164334555021, "numerical-endpoint midpoint left child", "child", "exact midpoint child of D12"),
        ("C2", "confirmation", "round39_small_hard_V12_M3_Q20_slot07_seed621538683", "L0.1", "L0", 0.32355821672775104, 0.64711643345550207, 1, 0.6471164334555021, "numerical-endpoint midpoint right child", "child", "exact midpoint child of D12"),
        ("C3", "confirmation", "tight_T_seed3101", "L0", "", 0.0, 0.10725273413394144, 0, 0.10725273413394144, "tight3101 highest-Work K1-AM fixed interval", "parent", "largest terminal/native MIP Work in Round 47 K1-AM; tie interval id"),
        ("C4", "confirmation", "high_imbalance_seed3202", "L0.1.0", "L0.1", 0.47499999999999998, 0.71249999999999991, 2, 1.7493134520506337, "high3202 highest-Work K1-AM fixed interval", "child", "largest terminal/native MIP Work in Round 47 K1-AM; tie interval id"),
        ("C5", "confirmation", "moderate_seed3302", "L0", "", 0.0, 0.19563620654901237, 0, 0.19563620654901237, "moderate3302 highest-Work K1-AM fixed interval", "parent", "largest terminal/native MIP Work in Round 47 K1-AM; tie interval id"),
        # C6--C9 cannot use the old exact P-GRB winners.  Their upper endpoint and
        # cutoff are resolved by the frozen deterministic HGA reconstruction gate.
        ("C6", "confirmation", "round39_small_hard_V10_M1_Q30_slot02_seed1721447042", "L0", "", "deterministic_hga:0", "deterministic_hga:verified_objective", 0, "deterministic_hga:verified_objective", "additional confirmation K1 root V10 M1 Q30", "parent", "K1 root after HGA seed 20260626 reconstruction"),
        ("C7", "confirmation", "round39_small_hard_V12_M1_Q20_slot05_seed180890838", "L0", "", "deterministic_hga:0", "deterministic_hga:verified_objective", 0, "deterministic_hga:verified_objective", "additional confirmation K1 root V12 M1 Q20", "parent", "K1 root after HGA seed 20260626 reconstruction"),
        ("C8", "confirmation", "round39_small_medium_V10_M1_Q20_slot04_seed1035775879", "L0", "", "deterministic_hga:0", "deterministic_hga:verified_objective", 0, "deterministic_hga:verified_objective", "additional confirmation K1 root V10 M1 Q20", "parent", "K1 root after HGA seed 20260626 reconstruction"),
        ("C9", "confirmation", "round39_small_medium_V8_M3_Q30_slot03_seed1177285734", "L0", "", "deterministic_hga:0", "deterministic_hga:verified_objective", 0, "deterministic_hga:verified_objective", "additional confirmation K1 root V8 M3 Q30", "parent", "K1 root after HGA seed 20260626 reconstruction"),
    ]
    historical_run = {
        "tight_T_seed3102": "results/gf_c6_adaptive_mass_contraction_round47/runs/stage5_1800s__tight_T_seed3102__K1-AM",
        "tight_T_seed3101": "results/gf_c6_adaptive_mass_contraction_round47/runs/stage5_1800s__tight_T_seed3101__K1-AM",
        "high_imbalance_seed3201": "results/gf_c6_adaptive_mass_contraction_round47/runs/stage5_1800s__high_imbalance_seed3201__K1-AM",
        "high_imbalance_seed3202": "results/gf_c6_adaptive_mass_contraction_round47/runs/stage5_1800s__high_imbalance_seed3202__K1-AM",
        "moderate_seed3301": "results/gf_c6_adaptive_mass_contraction_round47/runs/stage5_1800s__moderate_seed3301__K1-AM",
        "moderate_seed3302": "results/gf_c6_adaptive_mass_contraction_round47/runs/stage5_1800s__moderate_seed3302__K1-AM",
    }
    recovery = {
        "C1": "C1R=D4", "C2": "C2R=D5", "C3": "C3R=D9",
        "C4": "C4R=D13", "C5": "C5R=D14", "C6": "C6R=D2",
        "C7": "C7R=D12", "C8": "C8R=D6", "C9": "C9R=D1",
    }
    rows: list[dict[str, Any]] = []
    for spec in specs:
        sid, panel, instance, interval, parent, lo, hi, depth, cutoff, role, kind, selector = spec
        ipath = input_path(instance)
        source = historical_run.get(
            instance,
            f"results/gf_c6_adaptive_mass_contraction_round47/runs/stage5_1800s__{instance}__K1-AM",
        )
        pending = isinstance(cutoff, str)
        rows.append({
            "state_id": sid,
            "panel": panel,
            "instance": instance,
            "input_path": ipath.relative_to(ROOT).as_posix(),
            "input_sha256": sha256(ipath),
            "historical_source_run": source,
            "interval_id": interval,
            "parent_id": parent,
            "gamma_lower": lo,
            "gamma_upper": hi,
            "split_depth": depth,
            "verified_cutoff": cutoff,
            "cutoff_source": "Round 47 verified HGA incumbent" if not pending else "frozen deterministic HGA seed 20260626; known optimum forbidden",
            "canonical_model_fingerprint": "resolved_and_frozen_by_reconstruction_audit_before_stage1",
            "formulation_profile": "Interval-MIP-v0 paper-safe fixed-interval formulation",
            "row_bound_signature": "resolved_and_frozen_by_reconstruction_audit_before_stage1",
            "objective_sense": "minimize complete original G+lambda*P objective",
            "original_variable_mapping": "Round 49 semantic primitive registry plus exact auxiliary mapping; hash frozen by reconstruction audit",
            "historical_role": role,
            "state_kind": kind,
            "selection_rule": selector,
            "reconstruction_status": "deterministic_cutoff_pending" if pending else "historical_identity_frozen_round50_rebuild_required",
            "recovery_state_id": recovery.get(sid, ""),
        })
    with (OUT / "fixed_interval_state_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=state_columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    if run("git", "branch", "--show-current") != BRANCH:
        raise RuntimeError(f"Stage 0 must be created on {BRANCH}")
    if run("git", "rev-parse", "HEAD") != BASE_HEAD:
        raise RuntimeError("Stage 0 base HEAD changed")
    if OUT.exists() and any(OUT.iterdir()):
        raise RuntimeError(f"refusing to overwrite non-empty {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)

    status_lines = run("git", "status", "--porcelain=v1").splitlines()
    write_text("preexisting_worktree_status.txt", "\n".join(status_lines))

    write_text("research_contract.md", """
# Round 50 research contract

Round 50 first audits and optimizes the uniform fixed-interval MIP backend, freezes one backend, and only then integrates that backend into unchanged K1-AM. The K1 controller remains `K0=1`, exact midpoint refinement, adaptive-mass gate, and `tau=0.07915`. AMF-v1, reduced-cost rescue, gamma-veto, root-processing rescue, fixed-rho fallback, and AMC are inactive.

Every official solve uses Gurobi Presolve Auto, Seed 0, Threads 1, zero relative and absolute MIP gaps, the complete minimization objective, the same verified cutoff, certificate tolerance `1e-7`, and an honest external process cap no greater than 1800 seconds. The feasible set, valid bounds, interval coverage, monotone bounds, exact termination, and original-problem certificate are invariant.

At most four one-family development iterations are permitted. Confirmation freezes all algorithmic choices. The conditional LP tail-repair stage may open only after a backend freeze, K1 qualification, and a newly recomputed severe split error. No instance, size, panel, runtime, Work, nodes, memory, machine, historical-winner, or known-optimum dispatch is permitted.
""")

    write_text("source_of_truth.md", f"""
# Round 50 source of truth

- Repository: `E:/codes/ExactEBRP`
- Base branch: `{BASE_BRANCH}`
- Base/local/PR #102 head: `{BASE_HEAD}`
- Base/local/remote tree: `{BASE_TREE}`
- Base draft PR: {PR102_URL} (read-only for this round)
- Stacked branch: `{BRANCH}`
- Evidence root: `results/gf_k1_interval_mip_vnext_round50/`
- Broad validated tailored baseline: historical C6 with initial K4
- K1 research baseline: K1-AM (`K0=1`, midpoint, adaptive mass, `tau=0.07915`)
- Negative historical ablations: K1-AMF-v1 (Round 48) and K1-AM-RC (Round 49)

Stage 0 files and their hashes are authoritative for allowed mechanisms, state selection, panels, metrics, gates, and iteration limits. Resolved reconstructed model fingerprints are authoritative only after the pre-Stage-1 reconstruction audit is frozen; candidate results cannot be opened first.
""")

    write_json("solver_contract.json", {
        "schema": "round50-solver-contract-v1",
        "backend": "Gurobi", "version": "13.0.2 build v13.0.2rc1",
        "Presolve": "Auto", "Seed": 0, "Threads": 1,
        "MIPGap": 0.0, "MIPGapAbs": 0.0, "certificate_tolerance": 1e-7,
        "objective_sense": "minimize", "same_complete_objective": True,
        "same_verified_incumbent_cutoff": True, "strict_improver_gini_range": True,
        "known_optimum_injection": False, "archive_winner_injection": False,
        "instance_specific_parameters": False, "max_process_cap_seconds": 1800,
        "terminal_conditions": ["strict_exact_certificate", "honest_external_cap_with_valid_evidence"],
    })
    write_json("forbidden_mechanisms.json", {
        "schema": "round50-forbidden-mechanisms-v1",
        "backend_dispatch_inputs": ["instance_name", "V", "M", "Q", "panel_membership", "historical_winner", "elapsed_time", "work", "nodes", "memory", "machine_identity"],
        "forbidden_in_interval_mip_development": ["AMF-v1", "reduced-cost split rescue", "gamma-veto", "root-processing rescue", "fixed-rho fallback", "AMC", "split-gate modification", "Gurobi generic Cuts tuning", "known-optimum injection", "archive-winner injection"],
        "paper_presets_must_remain_unchanged": True,
        "V50_forbidden": True,
    })

    historical_manifest()
    states = fixed_states()

    write_json("fixed_interval_state_protocol.json", {
        "schema": "round50-fixed-interval-state-protocol-v1",
        "rebuild": "deterministically from original input, frozen interval, and independently verified cutoff; copied LP files are not identity",
        "cutoff_reconstruction": {"heuristic": "HGA-TGBC full verified incumbent", "seed": 20260626, "stop": "generation-stagnation", "no_improve_generations": 2000, "known_optimum_forbidden": True, "archive_scan_forbidden": True},
        "identity_fields": ["input_sha256", "interval", "verified_cutoff", "complete_objective", "canonical_model_fingerprint", "formulation_profile", "row_bound_signature", "original_variable_mapping"],
        "selection_rule": "largest complete terminal/native MIP Work; tie by interval id",
        "resolution_gate": "all pending cutoffs, fingerprints, row/bound signatures, and mappings must be frozen in fixed_interval_state_reconstruction_audit.csv before any Stage 1 result",
        "substitution": "forbidden after candidate results; only predeclared recovery states may be used",
    })
    write_json("mip_metric_contract.json", {
        "schema": "round50-mip-metric-contract-v1",
        "primary": "Gurobi Work",
        "secondary": ["strict_certificate", "GI_common_horizon", "final_gap", "valid_lower_bound", "time", "nodes", "root_bound", "root_work", "simplex_iterations", "presolved_size", "numerical_warnings"],
        "required_model_metrics": ["original_rows", "original_columns", "original_nonzeros", "presolved_rows", "presolved_columns", "presolved_nonzeros", "continuous_columns", "integer_columns", "binary_columns", "coefficient_range", "objective_range", "bound_range", "rhs_range"],
        "required_solve_metrics": ["root_relaxation_bound", "final_root_cut_bound", "root_work", "root_time", "root_simplex_iterations", "root_cut_family_counts", "first_incumbent_work", "first_incumbent_time", "final_best_bound", "final_incumbent", "nodes", "simplex_iterations", "average_iterations_per_node", "total_work", "total_process_time", "peak_memory", "exact_or_capped"],
        "capped_comparison_order": ["strict_certificate", "lower_GI", "smaller_gap", "larger_valid_LB", "lower_Work", "lower_time"],
        "decision_hash_excludes": ["time", "work", "nodes", "memory"],
    })
    write_json("optimization_direction_menu.json", {
        "schema": "round50-optimization-direction-menu-v1",
        "ordered_families": [
            {"iteration": 1, "family": "tailored_branching", "mandatory": True, "candidates": ["B1 primitive-first", "B2 route-first", "B3 operation-first"]},
            {"iteration": 2, "family": "cut_formulation_management", "mandatory": True, "candidates": ["C1 duplicate/dominated elimination", "C2 one exact delayed separator", "C3 one proved tightening", "C4 one defect-specific proved cut"]},
            {"iteration": 3, "family": "symmetry_or_numerical", "mandatory": False, "candidates": ["one exact symmetry family", "one exact numerical/formulation strengthening"]},
            {"iteration": 4, "family": "model_basis_reuse", "mandatory": False, "candidates": ["R1 exact in-memory LP-to-MIP promotion"]},
        ],
        "max_candidates_per_iteration": 3, "max_accepted_cut_formulation_changes": 2,
        "post_confirmation_change_forbidden": True,
    })
    write_json("bounded_iteration_policy.json", {
        "schema": "round50-bounded-iteration-policy-v1", "maximum_iterations": 4,
        "one_principal_family_per_iteration": True, "maximum_candidates_per_iteration": 3,
        "maximum_development_revisions_per_iteration": 1,
        "revision_conditions": ["same_family", "before_confirmation", "no_instance_dispatch", "retain_all_prior_rows", "rerun_complete_iteration_panel"],
        "candidate_screen_seconds": 120, "development_qualification_seconds": 300,
        "confirmation_seconds": 1200, "key_check_seconds": 1800,
    })
    write_json("development_panel_freeze.json", {
        "schema": "round50-development-panel-freeze-v1",
        "states": [r["state_id"] for r in states if r["panel"] == "development"],
        "core_screen": ["D1", "D2", "D3", "D4", "D5", "D6", "D9", "D10", "D11"],
        "screen_cap_seconds": 120, "qualification_cap_seconds": 300,
        "full_k1_instances": ["round39_small_medium_V12_M3_Q30_slot08_seed1343324363", "round39_small_hard_V12_M3_Q30_slot08_seed1288546114", "round39_small_hard_V10_M3_Q20_slot04_seed1145042375", "round39_small_hard_V12_M3_Q20_slot07_seed621538683", "round39_small_hard_V12_M2_Q20_slot06_seed258908503", "high_imbalance_seed3201", "moderate_seed3301", "tight_T_seed3102"],
        "full_k1_arms": ["K1-AM-v0", "K1-AM-vNext"], "full_k1_300s_rows": 16,
    })
    write_json("confirmation_panel_freeze.json", {
        "schema": "round50-confirmation-panel-freeze-v1",
        "states": [r["state_id"] for r in states if r["panel"] == "confirmation"],
        "recovery_states": {"C1R": "D4", "C2R": "D5", "C3R": "D9", "C4R": "D13", "C5R": "D14", "C6R": "D2", "C7R": "D12", "C8R": "D6", "C9R": "D1"},
        "recovery_rule": "use only when exact primary reconstruction fails before Stage 2; never choose after candidate results",
        "fixed_interval_cap_seconds": 1200,
        "k1_existing_confirmation": ["tight_T_seed3101", "high_imbalance_seed3202", "moderate_seed3302"],
        "k1_additional_confirmation": ["round39_small_hard_V10_M1_Q30_slot02_seed1721447042", "round39_small_hard_V12_M1_Q20_slot05_seed180890838", "round39_small_medium_V10_M1_Q20_slot04_seed1035775879", "round39_small_medium_V8_M3_Q30_slot03_seed1177285734"],
        "no_algorithm_change_after_panel_open": True,
    })
    write_json("severe_regression_definition.json", {
        "schema": "round50-severe-regression-definition-v1",
        "fixed_exact": {"work_ratio_gt": 1.5, "work_absolute_gt": 50, "time_ratio_gt": 1.5, "time_absolute_seconds_gt": 60, "ratio_and_absolute": True},
        "fixed_capped": ["baseline_certifies_candidate_does_not", "GI_ratio>=1.5_and_absolute_increase>=0.05", "gap_ratio>=1.5_and_absolute_increase>=0.05"],
        "split_exact": {"work_ratio_gt": 1.5, "work_absolute_gt": 100, "time_ratio_gt": 1.5, "time_absolute_seconds_gt": 60, "ratio_and_absolute": True},
        "split_capped": ["one_arm_certifies_other_materially_capped", "GI_ratio>1.5_and_absolute_difference>=0.05", "gap_ratio>1.5_and_absolute_difference>=0.05"],
    })
    write_json("promotion_gates.json", {
        "schema": "round50-promotion-gates-v1",
        "iteration": ["zero_correctness_failures", "zero_false_certificates", "complete_identity_audit", "no_severe_regression", "not_one_instance_only", "one_hard_state_materially_improves", "aggregate_work_or_capped_progress_nonworse", "confirmation_not_open"],
        "fixed_backend": ["zero_correctness_failures", "zero_severe_confirmation_regressions", "certificate_count_non_decreasing", "paired_work_geomean<=0.95_or_material_capped_progress_without_aggregate_regression", "two_structural_roles_improve", "numerical_conditioning_nonworse"],
        "k1_300s": ["zero_correctness_failures", "major_trajectory_nonworse", "V10_M3_easy", "one_hard_K1_weakness_improves", "no_severe_historical_PGRB_regression"],
        "split_tail_open": ["Interval-MIP-vNext_frozen", "K1-AM-vNext_qualified", "one_recomputed_severe_split_error"],
    })
    write_text("evidence_storage_policy.md", """
# Round 50 evidence storage policy

Commit source, tests, frozen manifests, concise state identities, compact ledgers, summaries, reports, hashes, and reproduction commands. Do not commit every native Gurobi log, canonical LP, copied historical result tree, or duplicated run tree. Large local-only artifacts must be inventoried by path and SHA-256 with compact extracted evidence. Historical evidence is referenced in place by source/tree/input/executable/artifact hashes. All doubles use round-trip precision. No V50 evidence is admitted.
""")

    write_json("official_start_record.json", {
        "schema": "round50-official-start-record-v1", "unix_seconds": time.time(),
        "branch": BRANCH, "base_branch": BASE_BRANCH, "base_head": BASE_HEAD,
        "base_tree": BASE_TREE, "remote_pr_102_head": BASE_HEAD, "remote_pr_102_tree": BASE_TREE,
        "local_remote_tree_equal": True, "upstream_before_branch": f"origin/{BASE_BRANCH}",
        "draft_pr_102": PR102_URL, "pr_102_untouched": True,
        "compiler": "g++ 14.2.0 (MSYS2 UCRT64)", "cmake": "3.30.5-msvc23",
        "gurobi": "13.0.2 build v13.0.2rc1", "machine": socket.gethostname(),
        "platform": platform.platform(), "processor": platform.processor(),
        "preexisting_tracked_diff_git_hash_object": "174771ed1c9cd5a5490b90b5922fec7ddf644d3a",
        "preexisting_status_git_hash_object": "fc51d2d6febae8688606b88a9077f19824839361",
        "preexisting_status_path": "preexisting_worktree_status.txt",
        "preexisting_status_entry_count": len(status_lines),
        "candidate_runtime_started": False, "new_optimization_result_inspected": False,
        "fixed_state_reconstruction_started": False,
        "written_before_new_optimization_runtime_or_result_inspection": True,
    })

    frozen_names = [
        "research_contract.md", "source_of_truth.md", "solver_contract.json",
        "forbidden_mechanisms.json", "historical_baseline_reference_manifest.csv",
        "fixed_interval_state_protocol.json", "fixed_interval_state_manifest.csv",
        "mip_metric_contract.json", "optimization_direction_menu.json",
        "bounded_iteration_policy.json", "development_panel_freeze.json",
        "confirmation_panel_freeze.json", "severe_regression_definition.json",
        "promotion_gates.json", "evidence_storage_policy.md", "official_start_record.json",
        "preexisting_worktree_status.txt",
    ]
    records = [file_record(OUT / name) for name in frozen_names]
    aggregate = hashlib.sha256("".join(r["sha256"] for r in records).encode()).hexdigest()
    write_json("stage0_freeze_manifest.json", {
        "schema": "round50-stage0-freeze-manifest-v1", "schema_version": SCHEMA_VERSION,
        "frozen_before_new_optimization_runtime_or_result_inspection": True,
        "candidate_runtime_started": False, "K0": 1, "split_point": "midpoint",
        "tau": 0.07915, "split_rescue_active": False, "maximum_iterations": 4,
        "no_algorithm_change_after_confirmation": True, "V50_forbidden": True,
        "maximum_process_cap_seconds": 1800, "required_files": records,
        "aggregate_sha256": aggregate,
    })
    print(json.dumps({
        "evidence_root": str(OUT), "frozen_files": len(records) + 1,
        "historical_rows": sum(1 for _ in (OUT / "historical_baseline_reference_manifest.csv").open(encoding="utf-8")) - 1,
        "fixed_states": len(states), "aggregate_sha256": aggregate,
    }, indent=2))


if __name__ == "__main__":
    main()
