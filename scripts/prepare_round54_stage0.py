#!/usr/bin/env python3
"""Create the Round 54 pre-result freeze and its hash manifest.

This script is definition-only.  It reads repository identities and frozen
prior-round manifests, but never invokes a solver or reads a Round 54
performance result.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_am_sf_inventory_route_round54"
ROUND50 = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
ROUND52 = ROOT / "results" / "gf_k1_tailored_cut_final_validation_round52"
ROUND53 = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"
BASE_HEAD = "bbf2044ec710f5eb8bde19d2ed183caa84055dcc"
BASE_TREE = "711d464f12699970b62b8385bd7a365b89b8ce62"
BRANCH = "codex/round54-k1-am-sf-inventory-route-cuts"
PR110 = "https://github.com/yifanXovo/TailoredExact/pull/110"
CERT_EPS = 1e-7
ROUND53_EXE_SHA = (
    "b49cc5a5e631c6a8ce7a8bd4d0e6da44162800c97996494b1ee6a04071286c85")


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n",
                            encoding="utf-8")


def write_text(name: str, value: str) -> None:
    (OUT / name).write_text(value.rstrip() + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def file_entry(path: Path) -> dict[str, object]:
    return {"path": repo_path(path), "bytes": path.stat().st_size,
            "sha256": sha256(path)}


def input_row(path_text: str, role: str, cap: int, route_limit: float,
              instance_id: str | None = None) -> dict[str, object]:
    path = ROOT / path_text
    return {"instance_id": instance_id or path.stem, "role": role,
            "input_path": path_text, "input_sha256": sha256(path),
            "route_time_limit": route_limit, "process_cap_seconds": cap}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    generalization = read_json(OUT / "round54_generalization_manifest.json")
    if (generalization.get("row_count") != 12 or
            generalization.get("solver_results_opened") is not False or
            generalization.get(
                "generated_before_any_round54_candidate_runtime_result") is not True):
        raise RuntimeError("unopened Round 54 generalization manifest required")

    dev53 = read_json(ROUND53 / "fixed_interval_development_freeze.json")
    conf53 = read_json(ROUND53 / "fixed_interval_confirmation_freeze.json")
    if len(dev53["states"]) != 14 or len(conf53["states"]) != 9:
        raise RuntimeError("Round 53 fixed-state freezes are incomplete")

    tracked_user_files = [
        {"path": "results/gf_compact_bc_round/handling_convention_test/handling_convention.json",
         "bytes": 53767,
         "sha256": "9a5cd06f8a4163cfcbb57147a0b21c0a5e4aec91973ab93faa921baa0553f35b",
         "git_blob": "98bcd60c3c5542772f101d5c73643033b78c58da"},
        {"path": "results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv",
         "bytes": 6792,
         "sha256": "4af39fe81263cd8c15ca457f4d4f6473a959630b6ab68a9280bc0a0e0a6b8acb",
         "git_blob": "730b12307ff356aad1972158312c3c791f4492ec"},
        {"path": "results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json",
         "bytes": 73034,
         "sha256": "b11e84e2442c0c7b5ac5aa638b44945de28426fe31753083bff13ad401644202",
         "git_blob": "c6ea164aec30b59fbee030476ed9cd6a4ffa315f"},
    ]
    untracked_snapshot = {
        "file_count": 49751,
        "total_bytes": 27089466488,
        "aggregate_sha256": (
            "34e0ec8a17908d3f816cc0fda1fbb2ebd6830cf584a452a7faf5ab201738c98f"),
        "local_inventory_path": "build/round54_preexisting_untracked_snapshot.csv",
        "local_inventory_sha256": (
            "fdf5e271de839ab73ba3a5bc6c2cb478f1c98b1941cd9c9591ab3ac81bfdecc5"),
    }
    write_json("repository_start_audit.json", {
        "schema": "round54-repository-start-audit-v1",
        "recorded_at_utc": "2026-08-29T06:30:56.5668766Z",
        "starting_branch": "codex/round53-f0-qualification-callback-isolation",
        "created_branch": BRANCH,
        "local_head": BASE_HEAD, "local_tree": BASE_TREE,
        "expected_base_head": BASE_HEAD,
        "pr110": {"url": PR110, "state": "OPEN", "draft": True,
                  "head_branch": "codex/round53-f0-qualification-callback-isolation",
                  "head": BASE_HEAD, "tree": BASE_TREE},
        "local_remote_head_equal": True, "local_remote_tree_equal": True,
        "tracked_preexisting_modification_count": 3,
        "untracked_preexisting_file_count": 49751,
        "toolchain": {
            "host": "WIN-3NO58RVQ4VC",
            "os": "Microsoft Windows 10 Professional 10.0.19045 64-bit",
            "compiler": "MSYS2 UCRT64 g++ 14.2.0",
            "cmake": "3.30.5-msvc23",
            "gurobi": "13.0.2 build v13.0.2rc1 win64",
            "python": "3.12.7",
        },
        "round54_performance_result_inspected": False,
        "repository_recloned_or_reset": False,
    })
    write_json("preexisting_file_preservation_audit.json", {
        "schema": "round54-preexisting-file-preservation-audit-v1",
        "baseline_recorded_before_round54_artifact_generation": True,
        "tracked_modified_files": tracked_user_files,
        "untracked_snapshot": untracked_snapshot,
        "preservation_rule": (
            "Every listed tracked file must retain its byte SHA-256 and Git "
            "clean-filtered blob; every path in the local untracked inventory "
            "must retain its path, byte length, and SHA-256."),
        "round54_outputs_excluded_from_baseline": True,
        "final_reverification_pending": True,
    })

    write_text("research_contract.md", """
# Round 54 frozen research contract

Round 54 is stacked on Round 53 commit
`bbf2044ec710f5eb8bde19d2ed183caa84055dcc`.  It has two independent
tracks.  First, the exact Round 53 K1-AM controller with F0-CLEAN is named and
documented as the stable paper-facing **K1-AM-SF** mainline and exposed by
`paper-k1-am-sf`, while historical aliases remain reproducible.  Second, one
default-off research family—Gini-induced inventory–route cutsets—is studied
under preregistered gates.

The stable controller, split point, tau, scheduler, lifecycle, interval
coverage, certificate contract, solver parameters, F0 row omission,
branching, symmetry, callbacks, and PreCrush behavior are immutable.  The
Round 53 P-GRB fingerprint repair is evidence-only and cannot tune either
mainline or candidate.

Only IR-IN/IR-OUT and valid interval-projected companions may be implemented.
Separation is an exact deterministic min-cut/maximum-closure computation with
direct reconstruction.  Candidate cuts are applied through external root LP
closure; the terminal MIP uses no callback and default PreCrush.  At most two
development iterations and two live variants are allowed, and only one
variant may enter confirmation.  No time, Work, node, memory, name, size,
difficulty, or historical-result dispatch is permitted.

Ordinary process caps are at most 3600 seconds.  Only predeclared V50 sealed
rows may use 7200 seconds under the frozen all-arm trigger.  No source change
is allowed after fixed-interval confirmation opens or after the sealed panel
opens.  Negative and partial strengthening conclusions are acceptable; the
stable `paper-k1-am-sf` preset is never silently replaced in this round.
""")
    write_text("source_of_truth.md", f"""
# Round 54 source of truth

- Base commit/tree: `{BASE_HEAD}` / `{BASE_TREE}`.
- Base draft PR: {PR110}; it must remain untouched and unmerged.
- Round 54 branch: `{BRANCH}`.
- Stable algorithm: K1-AM-SF, exactly Round 53 K1-AM-F0 with F0-CLEAN.
- Stable preset: `paper-k1-am-sf`; aliases: `K1-AM-F0` and
  `interval-mip-core-no-exhaustive-subset-duration`.
- Round 53 executable preferred for P-GRB repair: `{ROUND53_EXE_SHA}`.
- Fixed-state identities: Round 53 D1–D14 and C1–C9 freezes, ultimately
  derived from the hashed Round 50 reconstruction manifest.
- Sealed identities: the unopened deterministic Round 54 generalization
  manifest and its 12 hashed inputs.
- Candidate menu: IR1, IR2, and conditionally IR3 only; one may enter
  confirmation.

Compact committed ledgers and final JSON decisions are authoritative.  Raw
native artifacts may remain local only when inventoried, hashed, and
represented by committed summaries.  No universal paper-algorithm claim is
authorized.
""")

    write_json("solver_contract.json", {
        "schema": "round54-solver-contract-v1",
        "gurobi": {"Presolve": "Auto", "Seed": 0, "Threads": 1,
                   "MIPGap": 0.0, "MIPGapAbs": 0.0,
                   "Branching": "default", "PreCrush": "default"},
        "terminal_mip_callback": "off",
        "objective": "complete original minimization objective",
        "certificate_tolerance": CERT_EPS,
        "strict_original_problem_certificate_required": True,
        "ordinary_maximum_total_process_seconds": 3600,
        "v50_extension_maximum_total_process_seconds": 7200,
        "cap_includes": ["construction", "root LP", "separation",
                         "root closure", "terminal MIP", "verification",
                         "serialization"],
        "one_official_executable_for_all_round54_comparators": True,
        "known_optimum_or_archive_winner_injection": False,
    })
    write_json("stable_mainline_contract.json", {
        "schema": "round54-stable-mainline-contract-v1",
        "short_name": "K1-AM-SF",
        "full_name": "K1 Adaptive-Mass with Sparse Fixed-Interval Formulation",
        "preset": "paper-k1-am-sf",
        "outer_controller": {
            "K0": 1, "initial_intervals": 1,
            "initial_interval": "complete strict-improver Gini interval",
            "split_point": "midpoint", "split_score": "adaptive-mass",
            "tau": 0.08, "native_target": "Round 53 unchanged",
            "exact_parent_closure": True, "child_infeasibility": "strict",
            "exact_interval_coverage": True,
            "monotone_valid_global_lower_bound": True,
            "strict_original_problem_certification": True,
        },
        "inner_backend": {
            "name": "F0-CLEAN",
            "policy": "interval-mip-core-no-exhaustive-subset-duration",
            "base": "Round 50 interval-MIP v0 core",
            "only_removed_family": "historical exhaustive V<=12 subset-duration block",
            "all_other_static_families_retained": True,
            "callback": "off", "tailored_dynamic_user_cuts": "off",
            "branching": "Gurobi default", "PreCrush": "default",
            "Presolve": "Auto", "Seed": 0, "Threads": 1,
            "MIPGap": 0.0, "MIPGapAbs": 0.0,
        },
        "forbidden_changes": ["K0", "tau", "split score", "split point",
                              "scheduler", "native-target lifecycle",
                              "exact closure", "incumbent contract",
                              "F0 row omission", "branching priorities",
                              "symmetry", "solver parameters"],
        "instance_size_time_or_history_dispatch": False,
    })
    write_json("paper_preset_contract.json", {
        "schema": "round54-paper-preset-contract-v1",
        "preset": "paper-k1-am-sf", "human_name": "K1-AM-SF",
        "stable_contract": "stable_mainline_contract.json",
        "controller": "Round 53 frozen K1-AM", "K0": 1,
        "tau": 0.08, "split_point": "midpoint",
        "inner_policy": "interval-mip-core-no-exhaustive-subset-duration",
        "all_research_mechanisms_default_off": True,
        "semantic_sentinels": ["major witness", "strong control",
                               "V10 easy negative control",
                               "numerical endpoint", "V20 sentinel",
                               "V50 sentinel"],
        "required_equivalence": ["controller actions", "interval endpoints",
                                 "inner backend policy", "model fingerprints",
                                 "objective", "bounds", "certificate class",
                                 "deterministic command settings"],
    })
    write_json("historical_alias_contract.json", {
        "schema": "round54-historical-alias-contract-v1",
        "canonical": "paper-k1-am-sf",
        "aliases": [
            {"name": "K1-AM-F0", "kind": "algorithm reproduction alias",
             "must_remain_valid": True},
            {"name": "interval-mip-core-no-exhaustive-subset-duration",
             "kind": "inner-policy reproduction alias",
             "must_remain_valid": True}],
        "existing_historical_preset_semantics_may_change": False,
    })
    write_json("pgrb_certificate_repair_protocol.json", {
        "schema": "round54-pgrb-certificate-repair-protocol-v1",
        "evidence_only": True, "may_change_k1_am_sf": False,
        "source_panel": repo_path(ROUND53 / "sealed_v12_instance_manifest.json"),
        "source_panel_sha256": sha256(ROUND53 / "sealed_v12_instance_manifest.json"),
        "row_count": 12, "method": "P-GRB", "process_cap_seconds": 3600,
        "preferred_executable_sha256": ROUND53_EXE_SHA,
        "solver": {"Threads": 1, "Seed": 0, "Presolve": "Auto",
                   "MIPGap": 0.0, "MIPGapAbs": 0.0},
        "preflight_before_solves": True,
        "preflight_output": "round53_pgrb_expected_fingerprints.json",
        "expected_fingerprint_readback_required": True,
        "strict_checks": ["expected/actual fingerprint equality",
                          "lifecycle validity", "objective recomputation",
                          "independent original-solution verification",
                          "strict rejection reason", "strict certificate"],
        "original_round53_evidence_overwrite_forbidden": True,
        "correction_root": "round53_pgrb_certificate_correction",
        "algorithm_tuning_from_correction_forbidden": True,
    })
    families = [
        "Gini interval bounds", "direct Gini cap/floor",
        "interval-tight G x binary McCormick hull",
        "final-inventory penalty domains", "movement-reachability domains",
        "inventory conservation", "visit-inventory linking",
        "verified-incumbent objective row", "objective lower estimator",
        "penalty lower-bound closure", "SP-product McCormick rows",
        "SP-product objective estimator", "pair/triple support-duration covers",
        "connectivity-flow formulation", "iterative domain propagation",
        "tight denominator bounds", "removed exhaustive subset-duration block",
        "inactive Gini spread", "inactive required movement",
        "inactive transfer cutset", "inactive subset-inventory cuts",
        "inactive dynamic callback families"]
    write_json("active_family_audit_protocol.json", {
        "schema": "round54-active-family-audit-protocol-v1",
        "source": "actual paper-k1-am-sf runtime telemetry and code",
        "documentation_is_not_authoritative": True,
        "families_minimum": families,
        "fields": ["family", "active", "type", "scope", "proof_tag",
                   "code_location", "activation_condition", "representative_count",
                   "depends_gamma_L", "depends_gamma_U",
                   "depends_verified_incumbent", "ablation_evidence", "novelty_status"],
        "novelty_labels": ["standard formulation",
                           "standard technique adapted to this problem",
                           "potentially novel and literature review required",
                           "inactive research family"],
        "unverified_novelty_must_be_explicit": True,
    })
    write_json("documentation_alignment_protocol.json", {
        "schema": "round54-documentation-alignment-protocol-v1",
        "markdown_paths": ["README.md", "docs/algorithm_report.md",
                           "docs/attempt_log.md", "docs/current_mainline.md",
                           "docs/algorithm_lineage.md", "docs/k1_am_sf_algorithm.md",
                           "docs/f0_sparse_formulation.md",
                           "docs/active_formulation_families.md",
                           "docs/strengthening_roadmap.md",
                           "docs/reproduction_k1_am_sf.md"],
        "manuscript_paths": ["Manuscript/sections/algorithm_framework.tex",
                             "Manuscript/sections/valid_inequalities.tex",
                             "Manuscript/sections/branch_and_cut_implementation.tex",
                             "Manuscript/sections/certificate_and_audit.tex",
                             "Manuscript/sections/computational_protocol.tex",
                             "Manuscript/generated_results.tex", "Manuscript/main.tex"],
        "required_identity": ["Gurobi MIP engine", "K0=1", "tau=0.08",
                              "midpoint", "F0-CLEAN", "callback off",
                              "native branching", "removed exhaustive family",
                              "exact coverage/certification", "V50 limitations"],
        "stable_backend_term": (
            "sparse tailored fixed-interval MILP solved by Gurobi's native branch-and-cut"),
        "whole_framework_term": "tailored Gini-interval branch-and-cut framework",
        "bibliographic_metadata_may_be_fabricated": False,
    })
    write_json("strengthening_roadmap_protocol.json", {
        "schema": "round54-strengthening-roadmap-protocol-v1",
        "independent_of_round54_runtime_results": True,
        "implemented_this_round": "Track A only",
        "tracks": [
            {"track": "A", "priority": 1,
             "direction": "inventory-route cutsets with exact min-cut and external root closure",
             "motivation": "link interval inventory imbalance to necessary route boundary capacity",
             "expected_benefit": "stronger root bound and proof tail",
             "cost": "repeated deterministic LP/min-cut closure", "new_parameters": [],
             "exactness": "global mixed cuts; interval-local projected cuts; direct reconstruction",
             "panel": "offline census then gated fixed/K1/generalization",
             "stop": "frozen gates fail or full bounded qualification completes",
             "dependencies": ["F0-CLEAN LP telemetry", "exact separator"]},
            {"track": "B", "priority": 2,
             "direction": "value-disaggregated ideal G x Y formulation",
             "motivation": "compare ideal disaggregation with current binary product formulation",
             "expected_benefit": "polyhedral strength", "cost": "larger formulation",
             "new_parameters": [], "exactness": "ideal-equivalence proof required",
             "panel": "future fixed-state ablation", "stop": "separate future round",
             "dependencies": ["Track A disposition"]},
            {"track": "C", "priority": 3,
             "direction": "long-horizon V20/V50 proof-tail validation",
             "motivation": "establish scale behavior", "expected_benefit": "scalability evidence",
             "cost": "long exact runs", "new_parameters": [],
             "exactness": "frozen backend and strict certificates",
             "panel": "future V20/V50 benchmark", "stop": "predeclared horizon complete",
             "dependencies": ["final backend freeze"]},
            {"track": "D", "priority": 4,
             "direction": "paper finalization and ablation",
             "motivation": "align claims with reproducible evidence",
             "expected_benefit": "publication-ready tables and novelty audit",
             "cost": "documentation/literature/table work", "new_parameters": [],
             "exactness": "all claims trace to committed evidence",
             "panel": "final formulation ablation", "stop": "manuscript audit passes",
             "dependencies": ["Tracks A-C decisions"]}],
        "simultaneously_reopened": [],
    })
    write_json("inventory_route_cut_validity_protocol.json", {
        "schema": "round54-ir-cut-validity-protocol-v1",
        "global_cuts": {
            "IR-IN": "sum_{i in A}(Y_i-b_i) <= sum_k Q_k delta^-_k(A)",
            "IR-OUT": "sum_{i in A}(b_i-Y_i) <= sum_k Q_k delta^+_k(A)"},
        "interval_projected": {
            "IR-PROJ-IN": "sum_k Q_k delta^-_k(A) >= max(0,sum_{i in A}(L_i-b_i))",
            "IR-PROJ-OUT": "sum_k Q_k delta^+_k(A) >= max(0,sum_{i in A}(b_i-U_i))"},
        "proof": "sum vehicle load conservation inside A; crossing load is in [0,Q_k]; sum vehicles and substitute inventory balance",
        "depot_outside_subset": True, "empty_subset_cut_forbidden": True,
        "projected_scope": "interval-local and incumbent-epoch-local",
        "cardinality_companions": "forbidden unless separately formally proved",
        "integer_validity_and_lp_reconstruction_required": True,
    })
    write_json("separator_and_root_closure_protocol.json", {
        "schema": "round54-separator-root-closure-protocol-v1",
        "separator": "exact deterministic source-sink min-cut or maximum closure",
        "subset_enumeration": False, "heuristic_sampling": False,
        "depot_fixed_outside": True, "deterministic_tie_breaking": True,
        "returns": ["most violated inbound", "most violated outbound"],
        "direct_recomputation_required": True,
        "tolerance": {"source": "certificate tolerance", "value": CERT_EPS,
                      "fitted_threshold": False},
        "cut_record": ["subset", "direction", "raw/scaled violation",
                       "coefficients", "RHS", "min-cut objective",
                       "direct objective", "canonical signature", "scope"],
        "root_closure": ["build F0-CLEAN continuous relaxation", "solve LP",
                         "separate exact inbound/outbound cuts",
                         "reject nonviolated/duplicate/dominated cuts",
                         "add selected cuts and reoptimize",
                         "repeat to no strict violation or LP infeasibility",
                         "restore/rebuild integer model", "add accepted pool",
                         "terminal MIP with callback off/default PreCrush/native branching"],
        "performance_based_loop_stop": False,
        "safety_failures": ["repeated canonical cut",
                            "nondecreasing violation from numerical inconsistency",
                            "invalid min-cut reconstruction", "nonfinite LP result"],
        "safety_failure_action": "candidate invalid; exact F0 fallback; fallback is not supporting evidence",
        "end_to_end_accounting": True, "LP_evidence_reuse_requires": [
            "complete fingerprint match", "same interval", "same incumbent epoch"],
    })
    write_json("bounded_revision_policy.json", {
        "schema": "round54-bounded-revision-policy-v1",
        "maximum_development_iterations": 2,
        "maximum_candidates_per_iteration": 2,
        "maximum_live_family_count": 1,
        "maximum_candidate_variants_total": 2,
        "maximum_confirmation_candidates": 1,
        "candidates": {
            "IR1": "full mixed IR-IN/IR-OUT closure",
            "IR2": "full mixed plus nondominated projected closure",
            "IR3": "one exact root pass; at most one inbound and one outbound mixed cut"},
        "IR3_entry": "only when full closure overhead clearly dominates observed bound gain",
        "allowed_revisions": ["mixed-only versus mixed-plus-projected",
                              "full closure versus one exact pass",
                              "remove projected cut proved dominated",
                              "correct validity/mincut/canonicalization/accounting defect"],
        "forbidden": ["instance subset", "V/M/Q dispatch", "difficulty dispatch",
                      "time/Work/node/memory switch", "fitted threshold", "family weight",
                      "learned classifier", "named-witness policy", "other cut/symmetry/branching family",
                      "post-confirmation revision"],
        "offline_negative_rule": "if fewer than two structurally distinct strict violations, no live candidate",
        "failed_evidence_retained": True,
    })
    write_json("fixed_interval_development_freeze.json", {
        "schema": "round54-ir-fixed-development-freeze-v1",
        "source_freeze": repo_path(ROUND53 / "fixed_interval_development_freeze.json"),
        "source_sha256": sha256(ROUND53 / "fixed_interval_development_freeze.json"),
        "state_ids": dev53["state_ids"], "states": dev53["states"],
        "stable_arm": "F0-CLEAN", "candidate_menu": ["IR1", "IR2", "IR3"],
        "candidate_selected_only_after_offline_gate": True,
        "stage_A": {"cap_seconds": 300, "physical_rows_per_candidate": 28,
                    "mandatory_after_live_entry": True},
        "stage_B": {"cap_seconds": 1200, "physical_rows": 28,
                    "opens_only_if_stage_A_passes": True},
        "stage_B_gate": ["zero false certificates", "zero correctness failures",
                         "no lost F0 certificate", "zero severe regressions",
                         "one material hard-state improvement",
                         "candidate aggregate Work/GI nonworse"],
        "same_executable_required": True,
    })
    long_state_ids = ["D1", "D3", "D4", "D12", "D9", "D13", "D14"]
    dev_by_id = {row["state_id"]: row for row in dev53["states"]}
    write_json("fixed_interval_confirmation_freeze.json", {
        "schema": "round54-ir-fixed-confirmation-freeze-v1",
        "confirmation": {"state_ids": conf53["state_ids"],
                         "states": conf53["states"], "cap_seconds": 1800,
                         "physical_rows": 18},
        "long": {"state_ids": long_state_ids,
                 "states": [dev_by_id[state] for state in long_state_ids],
                 "cap_seconds": 3600, "physical_rows": 14},
        "arms": ["F0-CLEAN", "frozen selected IR candidate"],
        "opens_only_if_development_passes": True,
        "source_change_after_opening_forbidden": True,
        "promotion_gate": ["zero false certificates", "no lost F0 certificate",
                           "zero severe regression",
                           "exact Work GM <=0.95 OR certificate gain with nonworse Work/GI",
                           "capped GI nonworse", "two structural roles",
                           "full root-closure overhead included", "no forbidden dispatch"],
    })

    k1_rows = [
        input_row("reference/qualification_round39/small-medium/round39_small_medium_V12_M3_Q30_slot08_seed1343324363.txt", "major witness", 1800, 2850),
        input_row("reference/qualification_round39/small-hard/round39_small_hard_V12_M3_Q30_slot08_seed1288546114.txt", "strong control", 1800, 2400),
        input_row("reference/qualification_round39/small-hard/round39_small_hard_V10_M3_Q20_slot04_seed1145042375.txt", "V10 easy negative control", 1800, 2400),
        input_row("reference/qualification_round39/small-hard/round39_small_hard_V12_M3_Q20_slot07_seed621538683.txt", "numerical endpoint", 1800, 2400),
        input_row("reference/qualification_round39/small-hard/round39_small_hard_V12_M2_Q20_slot06_seed258908503.txt", "V12 M2", 1800, 2400),
        input_row("reference/qualification_round39/small-easy/round39_small_easy_V12_M3_Q30_slot08_seed1167625600.txt", "startup/easy V12", 1800, 3600),
        input_row("reference/hard_stress/V20_M3/tight_T_seed3102.txt", "tight3102", 1800, 2550),
        input_row("reference/hard_stress/V20_M3/high_imbalance_seed3201.txt", "high-imbalance 3201", 1800, 3600),
        input_row("reference/hard_stress/V20_M3/moderate_seed3301.txt", "moderate3301", 1800, 3600),
        input_row("reference/hard_stress/V20_M3/tight_T_seed3101.txt", "tight3101", 1800, 2400),
        input_row("reference/hard_stress/V20_M3/high_imbalance_seed3202.txt", "high-imbalance 3202", 1800, 3600),
        input_row("reference/hard_stress/V20_M3/moderate_seed3302.txt", "moderate3302", 1800, 3600),
    ]
    write_json("k1_integration_panel_freeze.json", {
        "schema": "round54-ir-k1-integration-freeze-v1",
        "arms": ["K1-AM-SF", "K1-AM-SF-IR"],
        "outer_controller_identical": True, "K0": 1, "tau": 0.08,
        "instances": k1_rows,
        "stage_1800": {"cap_seconds": 1800, "physical_rows": 24},
        "stage_3600": {"cap_seconds": 3600,
                       "conditional_roles": ["major witness", "strong control",
                                             "tight3102", "high-imbalance 3201",
                                             "moderate3301"],
                       "maximum_physical_rows": 10,
                       "trigger": "predeclared row unresolved at 1800"},
        "opens_only_if_fixed_confirmation_passes": True,
        "gate": ["zero false certificates", "major repair preserved",
                 "no severe regression", "certificate count nondecreasing",
                 "shifted Work and GI nonworse", "material improvement",
                 "no hidden-dispatch controller action change"],
    })
    write_json("new_generalization_panel_freeze.json", {
        "schema": "round54-generalization-panel-freeze-v1",
        "manifest": repo_path(OUT / "round54_generalization_manifest.json"),
        "manifest_sha256": sha256(OUT / "round54_generalization_manifest.json"),
        "row_count": 12, "arms": ["K1-AM-SF", "K1-AM-SF-IR"],
        "stage_3600": {"cap_seconds": 3600, "physical_rows": 24},
        "v50_extension": {"cap_seconds": 7200, "maximum_physical_rows": 8,
                          "trigger": "neither arm certifies input by 3600",
                          "both_arms_required": True},
        "opening_gate": ["K1 integration passes", "candidate source frozen",
                         "official executable frozen", "no later algorithm change"],
        "promotion_gate": ["zero false certificates", "no certificate loss",
                           "zero severe regression",
                           "shifted Work GM <=0.95 OR new certificate with nonworse Work/GI",
                           "aggregate GI nonworse", "two size/config groups",
                           "V50 not materially worsened"],
        "panel_initially_sealed": True, "rows": generalization["rows"],
    })

    validation = read_json(ROUND52 / "validation_instance_manifest.json")
    v50 = [row for row in validation["rows"] if int(row["V"]) == 50]
    v50_tight = next(row for row in v50 if row["difficulty_configuration"] == "tight_T_2400")
    v50_moderate = next(row for row in v50 if row["difficulty_configuration"] == "moderate_3600")
    write_json("offline_root_census_freeze.json", {
        "schema": "round54-offline-root-census-freeze-v1",
        "fixed_states": dev53["states"] + conf53["states"],
        "required_structural_roles": ["major", "strong control", "numerical endpoint",
                                      "V12 M2", "tight3102", "high-imbalance 3201",
                                      "high-imbalance 3202", "moderate3301", "moderate3302"],
        "v50_states": [v50_tight, v50_moderate],
        "candidate_variants": ["IR1", "IR2"],
        "live_entry_gate": ["valid separation every state",
                            "strict violation in two structural roles",
                            "strict LP-bound gain in two states OR one LP infeasibility plus another violation",
                            "no numerical inconsistency", "no new parameter"],
        "final_MIP_runtime_may_select_candidate": False,
    })
    write_json("severe_regression_definition.json", {
        "schema": "round54-severe-regression-definition-v1",
        "exact_rows": {"work": "candidate/baseline >1.50 and delta >50",
                       "time": "candidate/baseline >1.50 and delta >60 seconds"},
        "capped_rows_any": ["baseline certifies and candidate does not",
                            "GI ratio >1.50 and absolute increase >=0.05",
                            "gap ratio >1.50 and absolute increase >=0.05"],
        "root_closure_invalid": "candidate row invalid; F0 fallback is correctness-only",
        "generalization_v50_material_worsening": "same capped-row severe criteria",
    })
    write_json("promotion_gates.json", {
        "schema": "round54-promotion-gates-v1",
        "offline_to_live": "all five frozen offline gates",
        "development_300_to_1200": "all six Stage A gates",
        "confirmation_to_k1": "all eight fixed-interval promotion gates",
        "k1_to_generalization": "all seven K1 integration gates",
        "generalization_support": "all seven sealed support gates",
        "stable_mainline_regardless_of_ir": "K1-AM-SF",
        "strengthened_candidate_only_if_all_gates_pass": "K1-AM-SF-IR",
        "paper_preset_replacement_this_round": False,
        "post_confirmation_source_change": False,
        "post_sealed_source_or_documentation_change_without_authorization": False,
    })
    write_text("evidence_storage_policy.md", """
# Round 54 evidence storage policy

Commit source, tests, frozen contracts, deterministic inputs, proofs,
documentation and manuscript sources, compact ledgers, decisions, hashes, and
reproduction commands.  Do not commit complete native run trees.  Local raw
evidence must be path/size/SHA-256 inventoried and reproducible from committed
commands, frozen inputs, and the official executable hash.  Compact evidence
must retain every failed or invalid entered row and distinguish physical rows,
checkpoints, fallbacks, and unopened conditional stages.  Credentials,
licenses, machine-private configuration, and oversized native logs are never
published.
""")
    write_json("official_start_record.json", {
        "schema": "round54-official-start-record-v1",
        "recorded_at_utc": "2026-08-29T06:30:56.5668766Z",
        "base_commit": BASE_HEAD, "base_tree": BASE_TREE,
        "branch": BRANCH, "base_pr": PR110,
        "repository_start_audit": "repository_start_audit.json",
        "preexisting_file_preservation_audit": "preexisting_file_preservation_audit.json",
        "round53_official_executable_sha256": ROUND53_EXE_SHA,
        "round53_official_executable_path": (
            "build/official-round53-5b1e7d5bb/ExactEBRP.exe"),
        "round53_official_executable_available": True,
        "round54_candidate_results_inspected": False,
        "round54_candidate_results_generated": False,
        "generalization_panel_generated_and_sealed": True,
        "ordinary_process_cap_seconds": 3600,
        "v50_extension_cap_seconds": 7200,
    })

    required = [
        "research_contract.md", "source_of_truth.md", "solver_contract.json",
        "stable_mainline_contract.json", "paper_preset_contract.json",
        "historical_alias_contract.json", "pgrb_certificate_repair_protocol.json",
        "active_family_audit_protocol.json", "documentation_alignment_protocol.json",
        "strengthening_roadmap_protocol.json", "inventory_route_cut_validity_protocol.json",
        "separator_and_root_closure_protocol.json", "bounded_revision_policy.json",
        "fixed_interval_development_freeze.json",
        "fixed_interval_confirmation_freeze.json", "k1_integration_panel_freeze.json",
        "new_generalization_panel_freeze.json", "severe_regression_definition.json",
        "promotion_gates.json", "evidence_storage_policy.md", "official_start_record.json",
    ]
    extra = ["repository_start_audit.json", "preexisting_file_preservation_audit.json",
             "offline_root_census_freeze.json", "round54_generalization_manifest.json",
             "round54_generalization_manifest.csv"]
    entries = [file_entry(OUT / name) for name in required + extra]
    for row in generalization["rows"]:
        entries.append(file_entry(ROOT / row["input_path"]))
    for path in [ROOT / "scripts" / "generate_round54_generalization_instances.py",
                 ROOT / "scripts" / "prepare_round54_stage0.py",
                 ROUND50 / "fixed_interval_state_manifest.csv",
                 ROUND50 / "fixed_interval_state_reconstruction_audit.csv",
                 ROUND52 / "k1_am_controller_freeze.json",
                 ROUND53 / "final_inner_backend_definition.json",
                 ROUND53 / "sealed_v12_instance_manifest.json",
                 ROOT / "src" / "PaperExternalGiniTree.cpp",
                 ROOT / "src" / "Round50IntervalMip.cpp",
                 ROOT / "src" / "GurobiBaseline.cpp"]:
        entries.append(file_entry(path))
    write_json("stage0_freeze_manifest.json", {
        "schema": "round54-stage0-freeze-manifest-v1",
        "base_commit": BASE_HEAD, "base_tree": BASE_TREE, "branch": BRANCH,
        "round54_performance_results_inspected_before_freeze": False,
        "stable_mainline": "K1-AM-SF", "stable_preset": "paper-k1-am-sf",
        "live_cut_family_maximum": 1, "live_candidate_variants_maximum": 2,
        "development_iterations_maximum": 2,
        "post_confirmation_source_changes_allowed": 0,
        "post_sealed_opening_source_changes_allowed": 0,
        "algorithm_changes_from_pgrb_repair_allowed": 0,
        "ordinary_maximum_process_seconds": 3600,
        "v50_extension_maximum_process_seconds": 7200,
        "required_stage0_file_count_excluding_manifest": len(required),
        "generalization_input_count": 12, "entries": entries,
        "self_hash_note": "generated last and intentionally excludes its own recursive hash",
    })
    print(json.dumps({"stage0_files": len(required) + 1,
                      "manifest_entries": len(entries),
                      "generalization_inputs": 12}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
