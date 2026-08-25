#!/usr/bin/env python3
"""Freeze the Round 51 contract before formulation or candidate work."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"
R50 = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    research_contract = """# Round 51 frozen research contract

Round 51 starts from Round 50 commit `eccc795c0f5b2df5b57e24da31b56648150334b9`. It preserves all 23 frozen fixed-state identities, gamma intervals, verified cutoffs, objective, certificate tolerance, and panel roles.

The ordered mechanisms are causally separated:

1. M1 replaces only the `V<=12` exhaustive subset-duration conditional-row constant 100000 with the analytic row value `max(0,tsp[mask])` and fails closed for nonfinite or materially negative values.
2. S1 and S1-R1 are re-audited only on M1 with default branching.
3. A1 is developed only on M1 plus v0 cardinality symmetry. It reuses the required root LP evidence, probes at most four fractional primitive integer variables with two disposable child LPs each, gives positive priority to at most two variables, includes every probe in total Work/time, and never adapts after terminal MIP start.

No instance, panel, seed, V/M/Q, size, runtime, Work, node, memory, machine, historical-winner, or known-optimum dispatch is allowed. No MIP pilot, learned classifier, branching callback, controller change, or silent historical-mode change is allowed. Candidate selection uses only current root-LP primal values, original types/bounds, semantic families, and valid child-LP bounds/infeasibility.

Solver contract: Gurobi Presolve Auto, Seed 0, Threads 1, MIPGap 0, MIPGapAbs 0, complete minimization objective, identical verified cutoff, certificate tolerance 1e-7, honest process caps, and zero false certificates. Core is D1,D2,D3,D4,D5,D6,D9,D10,D11 at 120 seconds; development is D1-D14 at 300 seconds; confirmation is C1-C9 at 1200 seconds; predeclared long checks are at most 1800 seconds. Confirmation cannot select or revise a candidate.

The historical Round 50 backend remains explicit and reproducible. M1 is a candidate baseline, not an automatic production promotion. Symmetry/A1 interaction opens only if both independently pass. K1-AM integration opens only if a new fixed backend passes, and its K0=1, midpoint, adaptive-mass gate, tau=0.07915, controller, and certificates remain unchanged.
"""
    (OUT / "research_contract.md").write_text(research_contract,
                                                  encoding="utf-8")

    promotion = {
        "schema": "round51-promotion-gates-v1",
        "frozen_before_candidate_results": True,
        "severe_regression_definition":
            "Round 50 results/gf_k1_interval_mip_vnext_round50/severe_regression_definition.json",
        "global_required": [
            "zero_correctness_failures", "zero_false_certificates",
            "complete_model_identity_and_delta_audit",
            "no_lost_baseline_certificate", "no_severe_regression",
            "numerical_conditioning_nonworse",
            "aggregate_paired_end_to_end_work_nonworse_or_predeclared_material_capped_progress_without_aggregate_regression",
            "improvement_on_more_than_one_structural_role",
            "no_instance_only_effect",
        ],
        "m1_additional": [
            "formal_integer_validity_proof", "target_rows_only",
            "all_retained_incumbents_satisfy_m1", "v_gt_12_model_identical",
        ],
        "symmetry_additional": [
            "optimal_representative_preserved", "D13_included",
            "D13_no_lost_certificate_or_severe_regression",
        ],
        "a1_additional": [
            "probe_lifecycle_disposable", "terminal_model_clean",
            "priority_readback_exact", "probe_overhead_included",
            "candidate_budget_at_most_four", "positive_priorities_at_most_two",
        ],
        "confirmation_requires_full_development_pass": True,
        "interaction_requires_both_components_independently_passed_confirmation": True,
        "k1_requires_new_fixed_backend": True,
    }
    write_json(OUT / "promotion_gates.json", promotion)

    bounded = {
        "schema": "round51-bounded-iteration-policy-v1",
        "frozen_before_candidate_results": True,
        "ordered_stages": ["M1", "symmetry_reaudit", "A1"],
        "m1_candidates": ["m1-tight-big-m-v0"],
        "symmetry_candidates": ["m1-s1-route-start-order",
                                "m1-s1r-used-first-route-start-order"],
        "adaptive_candidates": ["a1-root-sparse-2x2"],
        "adaptive_revision_maximum": 1,
        "adaptive_revision_only": "a1r-root-sparse-top1",
        "adaptive_revision_change": "select only the best already-probed candidate",
        "candidate_pool_maximum": 4,
        "candidate_family_maximum": 2,
        "child_lp_probe_maximum": 8,
        "positive_priority_maximum": 2,
        "core_states": ["D1", "D2", "D3", "D4", "D5", "D6",
                        "D9", "D10", "D11"],
        "development_states": [f"D{i}" for i in range(1, 15)],
        "confirmation_states": [f"C{i}" for i in range(1, 10)],
        "caps_seconds": {"core": 120, "development": 300,
                         "confirmation": 1200, "key_long": 1800},
        "post_confirmation_revision_allowed": False,
    }
    write_json(OUT / "bounded_iteration_policy.json", bounded)

    preservation = {
        "schema": "round51-preexisting-file-preservation-audit-v1",
        "status": "frozen_monitoring",
        "recorded_before_round51_files": True,
        "git_status_entry_count": 94,
        "git_status_porcelain_git_hash_object":
            "c9e4b6830d201011b3c9c22a28f38d852c744942",
        "tracked_diff_git_hash_object":
            "174771ed1c9cd5a5490b90b5922fec7ddf644d3a",
        "tracked_paths": {
            "results/gf_compact_bc_round/handling_convention_test/handling_convention.json":
                "98bcd60c3c5542772f101d5c73643033b78c58da",
            "results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv":
                "730b12307ff356aad1972158312c3c791f4492ec",
            "results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json":
                "c6ea164aec30b59fbee030476ed9cd6a4ffa315f",
        },
        "unrelated_untracked_files_are_user_owned": True,
    }
    write_json(OUT / "preexisting_file_preservation_audit.json", preservation)

    references = []
    for name in (
        "fixed_interval_state_manifest.csv",
        "fixed_interval_state_reconstruction_audit.csv",
        "development_panel_freeze.json", "confirmation_panel_freeze.json",
        "severe_regression_definition.json", "solver_contract.json",
    ):
        path = R50 / name
        references.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(path), "size_bytes": path.stat().st_size,
        })
    local_files = []
    for name in ("research_contract.md", "promotion_gates.json",
                 "bounded_iteration_policy.json",
                 "preexisting_file_preservation_audit.json"):
        path = OUT / name
        local_files.append({"path": name, "sha256": sha256(path),
                            "size_bytes": path.stat().st_size})
    stage0 = {
        "schema": "round51-stage0-freeze-manifest-v1",
        "frozen_before_formulation_change": True,
        "frozen_before_candidate_build_or_result": True,
        "base_branch": "codex/round50-k1-interval-mip-vnext",
        "base_head": "eccc795c0f5b2df5b57e24da31b56648150334b9",
        "base_tree": "e6d6ea69ce69bb2fb659b7f65506ad1ed90b98e7",
        "branch": "codex/round51-tight-big-m-root-sparse-branching",
        "round50_pr": "https://github.com/yifanXovo/TailoredExact/pull/104",
        "compiler": "g++ 14.2.0 MSYS2 UCRT64",
        "cmake": "3.30.5-msvc23",
        "gurobi": "13.0.2 build v13.0.2rc1",
        "machine": "WIN-3NO58RVQ4VC; Intel i7-12700KF; Windows 10 19045",
        "round50_fixed_executable_sha256":
            "85a6404acb015ea71e1b56a656f85665cda46b1f72a29a7174e6f48d96f8e81a",
        "round50_full_executable_sha256":
            "7cc8ecb324c69526b38f21a8d66cdc4ca6ab6de0cd03639f916f25340d097a2e",
        "round50_references": references,
        "round51_frozen_files": local_files,
        "baseline_reproduction_states": ["D2", "D5", "D6", "C6"],
        "baseline_reproduction_cap_seconds": 120,
        "baseline_reproduction_policy": "interval-mip-v0",
        "baseline_reproduction_result_inspected": False,
        "formulation_changed": False,
    }
    write_json(OUT / "stage0_freeze_manifest.json", stage0)
    print(json.dumps({"out": str(OUT), "references": len(references),
                      "frozen_files": len(local_files)}, indent=2))


if __name__ == "__main__":
    main()
