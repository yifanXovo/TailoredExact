#!/usr/bin/env python3
"""Create the preregistered Round 52 Stage 0 contract and hash manifest.

This script is definition-only: it does not read candidate results, run a
solver, or make any result-dependent choice.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_tailored_cut_final_validation_round52"
ROUND50 = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
BASE_HEAD = "c6d7109bf69f50bd459174e8f05242b478e57d85"
BASE_TREE = "d9c26d64f9b0c45047f908c6fc76744d0e41dc57"
BRANCH = "codex/round52-k1-tailored-cut-final-validation"
CERT_EPS = 1e-7


def dump_json(name: str, payload: object) -> None:
    (OUT / name).write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load_fixed_states() -> list[dict[str, str]]:
    with (ROUND50 / "fixed_interval_state_manifest.csv").open(
            encoding="utf-8", newline="") as src:
        return list(csv.DictReader(src))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    states = load_fixed_states()
    by_id = {row["state_id"]: row for row in states}

    (OUT / "research_contract.md").write_text(
        """# Round 52 frozen research contract

Round 52 is a preregistered, bounded study on base commit
`c6d7109bf69f50bd459174e8f05242b478e57d85`. Its ordered objectives are:

1. Correct the K1-AM action mapping and root-telemetry semantics, audit plain-LP
   v0/M1 monotonicity, and decide whether tau 0.08 is decision-equivalent to
   historical tau 0.07915.
2. Freeze the K0=1 midpoint K1-AM outer interval controller.
3. Complete a solver-independent cut library and a genuine default-off Gurobi
   `GRBcbcut` user-cut adapter, initially for rank-2/rank-3 support-duration
   inequalities.
4. Execute at most three preregistered cut-management iterations, freeze one
   inner backend, and independently compare contemporaneous P-GRB with
   K1-AM-FINAL on frozen V12/V20/V50 validation and holdout panels.

All official optimization uses Presolve=Auto, Seed=0, Threads=1, MIPGap=0,
MIPGapAbs=0, the complete original minimization objective, the verified
incumbent contract, the strict-improver Gini range, certificate tolerance
1e-7, and honest total-process caps no greater than 1800 seconds. Known-optimum
and archive-winner injection, instance-specific parameterization, and
result-dependent instance selection are forbidden.

Every candidate must preserve the exact original feasible set, complete
interval coverage, valid and monotone global lower bounds, finite exact
termination, and strict original-problem certificates. Algorithmic actions may
depend only on current mathematical state (for example LP violation, exact
dominance, duplicate identity, infeasibility, closure, or canonical support),
never on identity, dimensions, benchmark role, historical winner, elapsed
time, Work, nodes, memory, or hardware.

Cut development is limited to three iterations, two candidates per iteration,
and one development-only revision per iteration. Each plan is hashed before
runs, changes one allowed design dimension, evaluates the complete frozen core,
and preserves failed evidence. No algorithm change is allowed after fixed-
interval confirmation or final validation opens. If the permitted candidates
fail, the outcome is a bounded systematic negative result and production v0 is
retained. Independent P-GRB validation and sealed holdout remain mandatory.
""",
        encoding="utf-8")

    (OUT / "source_of_truth.md").write_text(
        """# Round 52 source of truth

The authoritative K1-AM action source is the Round 47 adaptive-mass decision
ledger, not inferred labels in later counterfactual summaries:

- `results/gf_c6_adaptive_mass_contraction_round47/adaptive_mass_action_replay.csv`
- `results/gf_c6_adaptive_mass_contraction_round47/adaptive_mass_score_census.csv`
- `results/gf_c6_adaptive_mass_contraction_round47/tau_freeze.json`

All available Round 47--51 adaptive-mass decision ledgers are replay inputs;
raw historical files are immutable. Corrections are additive errata. The
Round 50 fixed-state identity source is
`results/gf_k1_interval_mip_vnext_round50/fixed_interval_state_manifest.csv`.
The Round 51 v0/M1 affected-state and experiment ledgers under
`results/gf_k1_tight_big_m_sparse_branching_round51/` are the telemetry-audit
inputs. Plain continuous LP solves, rather than MIP callback telemetry, define
the v0/M1 LP monotonicity audit.

Historical decisions are fixed by each round's `final_decision.json` and
`stage0_freeze_manifest.json` under the Round 47--51 evidence roots. The Round
52 validation/holdout identities are the Stage-0 JSON/CSV manifests generated
from the Round 51 base commit without solver observation. Committed compact
ledgers are authoritative for conclusions; inventoried native logs are local
reproduction evidence only.
""",
        encoding="utf-8")

    dump_json("solver_contract.json", {
        "schema": "round52-solver-contract-v1",
        "gurobi": {"Presolve": "Auto", "Seed": 0, "Threads": 1,
                    "MIPGap": 0.0, "MIPGapAbs": 0.0, "PreCrush_for_user_cuts": 1},
        "objective": "complete original minimization objective",
        "incumbent_contract": "same verified incumbent contract",
        "gini_range": "same strict-improver Gini range",
        "certificate_tolerance": CERT_EPS,
        "maximum_total_process_seconds": 1800,
        "cap_includes": ["model construction", "callback", "cut generation",
                         "solver", "verification", "checkpoint emission"],
        "known_optimum_injection": False,
        "archive_winner_injection": False,
        "instance_specific_parameters": False,
        "required_invariants": ["exact original feasible set",
                                "complete interval coverage", "valid lower bounds",
                                "monotone global bounds", "finite exact termination",
                                "strict original-problem certificates"]
    })

    dump_json("forbidden_mechanisms.json", {
        "schema": "round52-forbidden-mechanisms-v1",
        "controller_research_after_freeze": True,
        "mechanism_research_forbidden": [
            "symmetry", "branching_priority", "adaptive_branching", "AMF",
            "reduced_cost_rescue", "M1", "gamma_veto", "PMM", "FPMM",
            "breakpoint_research", "non_midpoint_splits", "AMC_for_K1"
        ],
        "dispatch_inputs_forbidden": ["instance_name", "path", "seed", "V", "M",
                                      "Q", "difficulty_label", "panel_membership",
                                      "historical_winner", "elapsed_time", "Work",
                                      "node_count", "memory", "hardware"],
        "core_constraints_removed_for_lazy_constraints": False,
        "user_cuts_as_lazy_constraints": False,
        "post_confirmation_revision": False,
        "post_validation_revision": False
    })

    history_fields = ["round", "mechanism", "implementation", "evidence",
                      "historical_decision", "round52_default", "reproducible"]
    history_rows = [
        [47, "K1-AM adaptive mass", "src/PaperExternalGiniTree.cpp",
         "results/gf_c6_adaptive_mass_contraction_round47/final_decision.json",
         "research candidate tau=0.07915", "off unless named K1-AM policy", True],
        [48, "K1-AMF", "src/Round48K1AMF.cpp",
         "results/gf_k1_amf_formulation_rescue_round48/final_decision.json",
         "bounded negative", "off", True],
        [49, "K1-AM-RC D-RCD", "src/Round49K1RC.cpp",
         "results/gf_k1_lp_primal_dual_rescue_round49/final_decision.json",
         "bounded negative", "off", True],
        [50, "interval-MIP vNext research policies", "src/round50_interval_mip_main.cpp",
         "results/gf_k1_interval_mip_vnext_round50/final_decision.json",
         "production interval-MIP-v0 retained", "off", True],
        [51, "M1 tight Big-M", "src/Round51TightBigM.cpp",
         "results/gf_k1_tight_big_m_sparse_branching_round51/final_decision.json",
         "rejected", "off", True],
        [51, "S1/S1R symmetry and A1/A1R branching", "src/round50_interval_mip_main.cpp",
         "results/gf_k1_tight_big_m_sparse_branching_round51/final_decision.json",
         "rejected", "off", True],
    ]
    with (OUT / "historical_algorithm_manifest.csv").open(
            "w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(history_fields)
        writer.writerows(history_rows)

    dump_json("tau_rounding_protocol.json", {
        "schema": "round52-tau-rounding-protocol-v1",
        "reference_tau": 0.07915,
        "candidate_tau": 0.08,
        "authoritative_inputs": [
            "results/gf_c6_adaptive_mass_contraction_round47/adaptive_mass_action_replay.csv",
            "all available Round 47-51 adaptive-mass decision ledgers"
        ],
        "complete_replay_fields": ["instance", "interval", "parent_id", "depth",
                                   "S_AM", "action_reference", "action_candidate",
                                   "action_changed", "margin_reference",
                                   "margin_candidate", "historical_outcome"],
        "anchor_requirements": {"major_root": "retain",
                                "strong_control_root": "retain",
                                "tight3102_L0.0": "retain",
                                "high_imbalance_root": "split"},
        "if_no_changed_decisions": "freeze 0.08 and run equivalence sentinels only",
        "if_changed_decisions": {
            "screen_seconds": 300,
            "confirmation_seconds_only_if_unresolved": 1200,
            "panels": ["all affected instances", "known regression panel"]},
        "adoption_gates": ["zero correctness failures", "zero new severe regressions",
                           "major repair preserved", "useful high-imbalance and moderate splits preserved",
                           "aggregate Work/proof progress nonworse"],
        "no_retuning_after_decision": True
    })

    dump_json("controller_freeze_protocol.json", {
        "schema": "round52-controller-freeze-protocol-v1",
        "freeze_after_tau_decision": True,
        "controller": {"K0": 1, "initial_intervals": 1,
                       "initial_range": "complete strict-improver Gini interval",
                       "refinement": "midpoint", "adaptive_mass_formula": "Round47",
                       "native_target_behavior": "Round47",
                       "exact_parent_closure": "Round47",
                       "infeasible_child_behavior": "Round47",
                       "coverage": "exact complete", "certification": "global exact"},
        "no_split_controller_research_after_freeze": True,
        "default_off": ["gamma-veto", "AMF", "reduced-cost rescue",
                        "fixed-rho fallback", "root-processing rescue", "PMM/FPMM",
                        "non-midpoint split points", "AMC for K1",
                        "adaptive branching", "Round51 M1"]
    })

    dump_json("cut_architecture_contract.json", {
        "schema": "round52-cut-architecture-contract-v1",
        "solver_independent_components": ["CutCandidate", "CutSeparator", "CutManager"],
        "candidate_fields": ["family", "validity_scope", "sparse_coefficients", "sense",
                             "rhs", "raw_violation", "scaled_violation",
                             "canonical_signature", "generating_interval",
                             "generating_context", "support_set", "vehicle_index",
                             "derivation_metadata"],
        "manager": ["canonical normalization", "exact duplicate rejection",
                    "global pool membership", "provable exact dominance",
                    "deterministic ranking and selection", "block accounting",
                    "callback-safe failure handling", "lifecycle telemetry"],
        "gurobi_adapter": {"callback": "MIPNODE", "required_status": "optimal",
                            "PreCrush": 1, "submission": "GRBcbcut",
                            "global_user_cuts_only": True,
                            "lazy_constraint_semantics": False,
                            "exception_safe": True},
        "base_core_constraints_retained": True,
        "default_off_without_named_policy": True
    })

    dump_json("allowed_cut_design_space.json", {
        "schema": "round52-allowed-cut-design-space-v1",
        "initial_family": "support-duration",
        "initial_policy": "SD-R3-ROOT-BLOCKMAX",
        "initial_rank": 3,
        "iteration_1": ["SD-R3-ROOT-BLOCKMAX"],
        "iteration_2_exactly_one_dimension": {
            "support_rank": [2, 3, 4],
            "separation_scope": ["root-only", "all optimal tree MIPNODE relaxations"],
            "selection": ["one max-scaled-violation cut per vehicle",
                          "all Pareto-undominated cuts"],
            "rank_hierarchy": ["rank-2 static plus rank-3 dynamic"]},
        "iteration_3": {"same_dimensions_refinement": True,
                        "or_second_family": ["transfer cutset",
                                             "subset inventory imbalance",
                                             "vector route cutset"],
                        "second_family_selection": "offline LP violation census only"},
        "second_family_census_metrics": ["violated-state fraction", "normalized violation",
                                         "generation complexity", "duplicate/dominance rate"],
        "runtime_may_select_second_family": False,
        "uniform_across_instance_sizes": True,
        "result_dependent_dispatch": False
    })

    dump_json("bounded_iteration_policy.json", {
        "schema": "round52-bounded-iteration-policy-v1",
        "maximum_iterations": 3,
        "maximum_candidates_per_iteration": 2,
        "maximum_development_only_revisions_per_iteration": 1,
        "plan_written_and_hashed_before_runs": True,
        "one_design_dimension_per_iteration": True,
        "complete_frozen_core_required": True,
        "failed_candidate_source_and_evidence_retained": True,
        "rejected_production_change_reverted_before_next_iteration": True,
        "algorithm_changes_after_confirmation_opens": 0,
        "algorithm_changes_after_validation_opens": 0,
        "maximum_process_seconds": 1800,
        "negative_termination_if_all_permitted_candidates_fail": True
    })

    development_ids = [f"D{i}" for i in range(1, 15)]
    confirmation_ids = [f"C{i}" for i in range(1, 10)]
    dump_json("fixed_interval_development_freeze.json", {
        "schema": "round52-fixed-interval-development-freeze-v1",
        "source_manifest": repo_path(ROUND50 / "fixed_interval_state_manifest.csv"),
        "source_manifest_sha256": sha256(ROUND50 / "fixed_interval_state_manifest.csv"),
        "core_cap_seconds": 120,
        "development_cap_seconds": 300,
        "core_state_ids": development_ids,
        "development_state_ids": development_ids,
        "complete_core_required_for_each_candidate": True,
        "roles": [{"state_id": sid, "instance": by_id[sid]["instance"],
                   "interval_id": by_id[sid]["interval_id"],
                   "role": by_id[sid]["historical_role"],
                   "input_path": by_id[sid]["input_path"],
                   "input_sha256": by_id[sid]["input_sha256"]}
                  for sid in development_ids]
    })

    dump_json("fixed_interval_confirmation_freeze.json", {
        "schema": "round52-fixed-interval-confirmation-freeze-v1",
        "source_manifest": repo_path(ROUND50 / "fixed_interval_state_manifest.csv"),
        "source_manifest_sha256": sha256(ROUND50 / "fixed_interval_state_manifest.csv"),
        "confirmation_cap_seconds": 1200,
        "confirmation_state_ids": confirmation_ids,
        "predeclared_key_1800_state_ids": ["C3", "C4", "C5"],
        "key_1800_requires_confirmation_eligibility": True,
        "algorithm_change_after_opening_forbidden": True,
        "roles": [{"state_id": sid, "instance": by_id[sid]["instance"],
                   "interval_id": by_id[sid]["interval_id"],
                   "role": by_id[sid]["historical_role"],
                   "input_path": by_id[sid]["input_path"],
                   "input_sha256": by_id[sid]["input_sha256"]}
                  for sid in confirmation_ids]
    })

    dump_json("severe_regression_definition.json", {
        "schema": "round52-severe-regression-definition-v1",
        "exact_rows": {"ratio_strictly_greater_than": 1.50,
                       "and_either": {"work_absolute_increase_greater_than": 50,
                                      "process_time_absolute_increase_seconds_greater_than": 60}},
        "capped_rows_any": ["baseline certifies but candidate does not",
                            "GI ratio > 1.50 and absolute GI increase >= 0.05",
                            "gap ratio > 1.50 and absolute gap increase >= 0.05"],
        "zero_new_severe_regressions_required": True
    })

    dump_json("promotion_gates.json", {
        "schema": "round52-promotion-gates-v1",
        "mandatory": ["zero correctness failures", "zero false certificates",
                      "no lost baseline certificate in confirmation", "no severe regression",
                      "improvement in at least two structural roles",
                      "callback and cut overhead included", "capped-row GI aggregate nonworse",
                      "numerical conditioning nonworse", "no forbidden dispatch"],
        "performance_disjunction": {
            "A": "paired exact-row Work geometric mean <= 0.97",
            "B": "at least one additional strict certificate with no aggregate Work/GI regression"},
        "failure_action": "retain historical production v0"
    })

    (OUT / "evidence_storage_policy.md").write_text(
        """# Round 52 evidence storage policy

Commit source, tests, frozen manifests, proofs, concise cut ledgers, summary
CSV/JSON, hashes, reproduction commands, and compact archives where useful.
Do not commit every native log or full raw model tree. Large native evidence may
remain local only when its path, size, SHA-256, generating command, executable
hash, and compact committed representative are inventoried. No raw historical
evidence may be rewritten. Every entered-stage row must be represented in a
committed compact ledger; missing entered rows force `round52_incomplete`.
Secret/license scanning, source-scope auditing, evidence hashing, cap auditing,
and preservation auditing are publication gates.
""",
        encoding="utf-8")

    dump_json("official_start_record.json", {
        "schema": "round52-official-start-record-v1",
        "repository": "E:/codes/ExactEBRP",
        "starting_branch": "codex/round51-tight-big-m-root-sparse-branching",
        "created_branch": BRANCH,
        "local_head": BASE_HEAD,
        "local_tree": BASE_TREE,
        "remote_pr": {"number": 106, "state": "OPEN", "is_draft": True,
                      "base": "codex/round50-k1-interval-mip-vnext",
                      "head": "codex/round51-tight-big-m-root-sparse-branching",
                      "head_sha": BASE_HEAD, "head_tree": BASE_TREE},
        "local_remote_head_equivalent": True,
        "local_remote_tree_equivalent": True,
        "working_tree_start": {
            "porcelain_entry_count": 43740,
            "tracked_modified_count": 3,
            "untracked_entry_count": 43737,
            "porcelain_snapshot_git_hash_object_sha1": "fdce62548fb44b631b5cb56da9179108c4afb814",
            "tracked_diff_git_hash_object_sha1": "174771ed1c9cd5a5490b90b5922fec7ddf644d3a",
            "tracked_modified": [
                {"path": "results/gf_compact_bc_round/handling_convention_test/handling_convention.json",
                 "start_blob_sha1": "98bcd60c3c5542772f101d5c73643033b78c58da"},
                {"path": "results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv",
                 "start_blob_sha1": "730b12307ff356aad1972158312c3c791f4492ec"},
                {"path": "results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json",
                 "start_blob_sha1": "c6ea164aec30b59fbee030476ed9cd6a4ffa315f"}
            ],
            "preservation_rule": "all three tracked modifications and all unrelated untracked paths are user-owned and excluded from Round52 commits"
        },
        "toolchain": {"compiler": "GCC 14.2.0", "cmake": "3.30.5-msvc23",
                      "gurobi": "13.0.2rc1", "gurobi_api": "C API"},
        "machine": {"hostname": "WIN-3NO58RVQ4VC",
                    "cpu": "Intel Core i7-12700KF", "logical_processors": 20,
                    "memory_bytes": 34079084544,
                    "os": "Microsoft Windows 10.0.19045"},
        "pr106_mutation_forbidden": True,
        "candidate_result_inspected_before_stage0": False,
        "note": "PowerShell initially parsed HEAD^{tree} incorrectly; the recorded tree was re-queried with git show -s --format=%T and verified against the remote head."
    })

    required = [
        "research_contract.md", "source_of_truth.md", "solver_contract.json",
        "forbidden_mechanisms.json", "historical_algorithm_manifest.csv",
        "tau_rounding_protocol.json", "controller_freeze_protocol.json",
        "cut_architecture_contract.json", "allowed_cut_design_space.json",
        "bounded_iteration_policy.json", "fixed_interval_development_freeze.json",
        "fixed_interval_confirmation_freeze.json", "final_validation_instance_freeze.json",
        "severe_regression_definition.json", "promotion_gates.json",
        "evidence_storage_policy.md", "official_start_record.json"
    ]
    supporting = [
        "validation_instance_manifest.csv", "validation_instance_manifest.json",
        "holdout_instance_manifest.csv", "holdout_instance_manifest.json"
    ]
    input_paths: list[str] = []
    for manifest in ("validation_instance_manifest.json", "holdout_instance_manifest.json"):
        payload = json.loads((OUT / manifest).read_text(encoding="utf-8"))
        input_paths.extend(row["input_path"] for row in payload["rows"])

    hash_paths = [OUT / name for name in required + supporting]
    hash_paths += [ROOT / path for path in input_paths]
    hash_paths += [
        ROOT / "scripts" / "generate_round52_validation_instances.py",
        ROOT / "scripts" / "prepare_round52_stage0.py",
        ROUND50 / "fixed_interval_state_manifest.csv",
        ROOT / "results" / "gf_c6_adaptive_mass_contraction_round47" / "adaptive_mass_action_replay.csv",
        ROOT / "results" / "gf_c6_adaptive_mass_contraction_round47" / "tau_freeze.json",
        ROOT / "results" / "gf_c6_adaptive_mass_contraction_round47" / "final_decision.json",
        ROOT / "results" / "gf_k1_amf_formulation_rescue_round48" / "final_decision.json",
        ROOT / "results" / "gf_k1_lp_primal_dual_rescue_round49" / "final_decision.json",
        ROUND50 / "final_decision.json",
        ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51" / "final_decision.json",
    ]
    entries = [{"path": repo_path(path), "sha256": sha256(path),
                "bytes": path.stat().st_size} for path in hash_paths]
    dump_json("stage0_freeze_manifest.json", {
        "schema": "round52-stage0-freeze-manifest-v1",
        "base_commit": BASE_HEAD,
        "branch": BRANCH,
        "candidate_results_inspected_before_freeze": False,
        "required_stage0_file_count_excluding_manifest": len(required),
        "validation_input_count": 12,
        "holdout_input_count": 12,
        "maximum_cut_development_iterations": 3,
        "maximum_candidates_per_iteration": 2,
        "maximum_development_only_revisions_per_iteration": 1,
        "maximum_process_seconds": 1800,
        "post_confirmation_algorithm_changes_allowed": 0,
        "post_validation_algorithm_changes_allowed": 0,
        "entries": entries,
        "self_hash_note": "this manifest is generated last and is intentionally not recursively self-hashed"
    })
    print(f"created and hashed {len(required) + 1} required Stage 0 files")


if __name__ == "__main__":
    main()
