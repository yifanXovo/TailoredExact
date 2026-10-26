#!/usr/bin/env python3
"""Create the Round 55 pre-result contracts and recursive hash freeze.

The script reads only repository identity, prior frozen manifests, and the
definition-only Round 55 instance manifests. It never invokes a solver or
opens a Round 55 performance result.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_am_sf_station_state_chain_round55"
ROUND53 = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"
ROUND54 = ROOT / "results" / "gf_k1_am_sf_inventory_route_round54"
BASE_HEAD = "324646af2e253618218812717a53e3e9e9cf1d9c"
BASE_TREE = "137c7071757957648cc9a9fd2873d35e26ff1231"
BRANCH = "codex/round55-k1-am-sf-station-state-chain"
BASE_BRANCH = "codex/round54-k1-am-sf-inventory-route-cuts"
BASE_PR = "https://github.com/yifanXovo/TailoredExact/pull/112"
CERT_EPS = 1e-7


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_text(name: str, value: str) -> None:
    (OUT / name).write_text(value.strip() + "\n", encoding="utf-8")


def entry(path: Path) -> dict[str, object]:
    return {"path": repo_path(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def instance_row(source: dict[str, Any], role: str, cap: int) -> dict[str, object]:
    return {
        "instance_id": source["instance_id"], "role": role,
        "input_path": source["input_path"], "input_sha256": source["input_sha256"],
        "process_cap_seconds": cap,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if git("rev-parse", "HEAD") != BASE_HEAD or git("show", "-s", "--format=%T", "HEAD") != BASE_TREE:
        raise RuntimeError("Round 55 Stage 0 must start from the frozen Round 54 commit/tree")

    now = datetime.now(timezone.utc).isoformat()
    dev = read_json(ROUND53 / "fixed_interval_development_freeze.json")
    conf = read_json(ROUND53 / "fixed_interval_confirmation_freeze.json")
    primary = read_json(OUT / "sealed_generalization_manifest.json")
    expansion = read_json(OUT / "expansion_panel_manifest.json")
    r54_panel = read_json(ROUND54 / "round54_generalization_manifest.json")
    if len(dev["states"]) != 14 or len(conf["states"]) != 9:
        raise RuntimeError("incomplete inherited D/C fixed-state freezes")
    if primary["row_count"] != 12 or expansion["row_count"] != 10:
        raise RuntimeError("incomplete Round 55 sealed panels")

    tracked = [
        {"path": "results/gf_compact_bc_round/handling_convention_test/handling_convention.json", "bytes": 53767,
         "sha256": "9a5cd06f8a4163cfcbb57147a0b21c0a5e4aec91973ab93faa921baa0553f35b", "git_blob": "98bcd60c3c5542772f101d5c73643033b78c58da"},
        {"path": "results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv", "bytes": 6792,
         "sha256": "4af39fe81263cd8c15ca457f4d4f6473a959630b6ab68a9280bc0a0e0a6b8acb", "git_blob": "730b12307ff356aad1972158312c3c791f4492ec"},
        {"path": "results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json", "bytes": 73034,
         "sha256": "b11e84e2442c0c7b5ac5aa638b44945de28426fe31753083bff13ad401644202", "git_blob": "c6ea164aec30b59fbee030476ed9cd6a4ffa315f"},
    ]
    untracked = {
        "file_count": 50851, "total_bytes": 27113346320,
        "aggregate_sha256": "f0e17c92f92143e68e5b061c46898d89969e479b7a8ef91c5eda7c2bcf79c42d",
        "local_inventory_path": "build/round55_preexisting_untracked_snapshot.csv",
        "local_inventory_sha256": "c4f14e6cb2682a3d4b3004f8ddb3360866db754473f7b2e82ff93a2218e3e48f",
    }
    write_json("repository_start_audit.json", {
        "schema": "round55-repository-start-audit-v1", "recorded_at_utc": now,
        "starting_branch": BASE_BRANCH, "created_branch": BRANCH,
        "local_head": BASE_HEAD, "local_tree": BASE_TREE,
        "upstream": f"origin/{BASE_BRANCH}",
        "base_pr": {"number": 112, "url": BASE_PR, "state": "OPEN", "draft": True,
                    "head_branch": BASE_BRANCH, "head": BASE_HEAD, "tree": BASE_TREE},
        "local_remote_head_equal": True, "local_remote_tree_equal": True,
        "tracked_preexisting_modification_count": 3,
        "untracked_preexisting_file_count": untracked["file_count"],
        "repository_recloned_reset_or_cleaned": False,
        "round55_performance_result_inspected": False,
    })
    write_json("environment_audit.json", {
        "schema": "round55-environment-audit-v1", "recorded_at_utc": now,
        "os": "Microsoft Windows 10 Professional 10.0.19045 64-bit",
        "cpu": "12th Gen Intel(R) Core(TM) i7-12700KF; 12 cores; 20 logical processors",
        "memory_kib": {"total": 33363244, "available_at_start": 16872232},
        "compiler": "MSYS2 UCRT64 g++ 14.2.0",
        "cmake": "3.30.5-msvc23", "python": "3.12.13",
        "gurobi": "13.0.2 build v13.0.2rc1 win64",
        "development_build": "build/dev-gurobi-release",
    })
    write_json("preexisting_file_preservation_audit.json", {
        "schema": "round55-preexisting-file-preservation-audit-v1",
        "baseline_recorded_before_round55_artifact_generation": True,
        "tracked_modified_files": tracked, "untracked_snapshot": untracked,
        "preservation_rule": "Retain every listed path byte-for-byte; verify path, byte count, SHA-256, and tracked Git blob at finalization.",
        "round55_outputs_excluded_from_baseline": True,
        "final_reverification_pending": True,
    })

    write_text("research_contract.md", f"""
# Round 55 frozen research contract

Round 55 is stacked on `{BASE_HEAD}` / `{BASE_TREE}` and PR #112. The stable
paper algorithm remains **K1-AM-SF** (`paper-k1-am-sf`): one complete initial
strict-improver interval, midpoint splitting, balanced normalized closure
score with `tau=0.08`, F0-CLEAN, and Gurobi native branch-and-cut with no
dynamic callback. The first-class controller cleanup is semantics-preserving.

Engineering correctness precedes optimization. The mandatory candidate chain
is MC4 implication analysis, exact VD-P, exact VD-J, and an efficacy audit of
optional active families. At most two proved uniform removals and three
single-mechanism revisions may be tested. Exact penalty-cover separation opens
only after a joint station-state formulation passes confirmation. Interaction,
split revision, sealed generalization, and strong expansion each retain their
written entry gates. A bounded negative result is acceptable.

No algorithm may dispatch on name, path, seed, panel, V/M/Q, difficulty, time,
Work, nodes, memory, winner, optimum, or witness. Confirmation and sealed
panels never guide design. Ordinary runs cap at 3600 seconds; sealed V50 and
the expansion panel may use 7200 seconds, with the predeclared all-arm 14400
extension only for unresolved expansion V50/V70 rows.
""")
    write_text("source_of_truth.md", f"""
# Round 55 source of truth

- Base: `{BASE_HEAD}` / `{BASE_TREE}`; draft PR [#112]({BASE_PR}) remains untouched.
- Branch: `{BRANCH}`; evidence root: `{repo_path(OUT)}/`.
- Stable comparator: K1-AM-SF / `paper-k1-am-sf` / F0-CLEAN.
- Direct development comparator: F0-CLEAN; final benchmark: P-GRB.
- Fixed states: inherited hashed D1-D14 and C1-C9 freezes from Round 53.
- Sealed panels: the unopened 12-row primary and 10-row expansion manifests.
- Candidate menu: conditionally SF-MC4, mandatory VD-P/VD-J, and at most two
  independently proved sparse removals. PC1/PC2 and combinations are gated.

The compact CSV/JSON decisions and hash inventories are authoritative. Raw
native logs may remain local only when inventoried and represented compactly.
Unopened conditional stages are reported as unopened, never as missing rows.
""")
    solver = {
        "schema": "round55-solver-contract-v1",
        "Gurobi": {"Presolve": "Auto", "Seed": 0, "Threads": 1, "MIPGap": 0.0,
                   "MIPGapAbs": 0.0, "Branching": "native/default", "PreCrush": "default"},
        "dynamic_user_cut_callback": False, "certificate_tolerance": CERT_EPS,
        "strict_original_problem_certificate_required": True,
        "total_process_cap_includes": ["construction", "root LP", "separation", "closure", "terminal MIP", "verification", "serialization"],
        "ordinary_cap_seconds": 3600, "sealed_v50_cap_seconds": 7200,
        "conditional_expansion_cap_seconds": 14400,
        "known_optimum_injection": False,
    }
    write_json("solver_contract.json", solver)
    write_json("stable_mainline_contract.json", {
        "schema": "round55-stable-mainline-contract-v1", "name": "K1-AM-SF", "preset": "paper-k1-am-sf",
        "outer": {"initial_gini_interval_count": 1, "initial_interval": "complete strict-improver Gini range",
                  "scheduler": "best-valid-bound", "split_point_rule": "midpoint",
                  "split_score_rule": "balanced-normalized-closure", "split_threshold": 0.08,
                  "maximum_split_depth": 8, "minimum_interval_width": 0.0001, "split_factor": 2,
                  "child_infeasibility_policy": "exact", "native_target_policy": "existing-k1-am-sf",
                  "exact_parent_closure": True, "exact_interval_coverage": True,
                  "monotone_global_lower_bound": True, "original_problem_certificate": "strict"},
        "inner": {"name": "F0-CLEAN", "only_omitted_family": "historical exhaustive V<=12 subset-duration block",
                  "all_other_active_families_retained": True, "callback": False},
        "solver_contract": solver["Gurobi"], "paper_preset_replacement_allowed": False,
        "historical_round_fields_are_compatibility_adapters_only": True,
    })
    write_json("engineering_audit_protocol.json", {
        "schema": "round55-engineering-audit-protocol-v1",
        "must_precede_optimization": True,
        "areas": ["controller/preset", "all K1 model-construction paths", "variable domains/objective/scaling",
                  "lifecycle/reuse/cache keys", "certificate/P-GRB pipeline", "return codes/numerics/sanitizers"],
        "model_paths": ["root", "parent LP", "child LP", "partial native-target MIP", "exact parent MIP",
                        "exact child MIP", "cutoff", "interrupted leaf", "infeasible child", "certificate finalization"],
        "optimization_opening_condition": "issue ledger closed or every unresolved material issue explicitly blocks the round",
    })
    write_json("bug_classification_protocol.json", {
        "schema": "round55-bug-classification-protocol-v1",
        "classes": ["no defect", "documentation/telemetry defect", "evidence-only defect",
                    "performance-accounting defect", "semantic implementation defect", "exactness/certificate defect"],
        "fields": ["source", "mathematical impact", "historical rounds", "evidence invalidation", "fix", "tests", "rerun"],
        "semantic_or_exactness_action": "fix, freeze corrected baseline, and rerun all mandatory baseline qualification rows",
    })
    write_json("first_class_controller_refactor_protocol.json", {
        "schema": "round55-first-class-controller-refactor-protocol-v1", "semantic_change_allowed": False,
        "canonical_fields": {"initial_gini_interval_count": 1, "split_point_rule": "midpoint",
                             "split_score_rule": "balanced-normalized-closure", "split_threshold": 0.08,
                             "maximum_split_depth": 8, "minimum_interval_width": 0.0001, "split_factor": 2,
                             "child_infeasibility_policy": "exact", "native_target_policy": "existing-k1-am-sf",
                             "exact_parent_closure": True},
        "legacy_fields": ["frontier_intervals", "round43_initial_k0", "c6_normalized_split_threshold",
                          "round40_c6_coarse_start", "round47_c6_adaptive_mass", "round47_c6_adaptive_mass_tau"],
        "legacy_role": "compatibility adapters only", "paper_preset_may_depend_on_contradictory_inert_values": False,
    })
    write_json("gy_semantics_audit_protocol.json", {
        "schema": "round55-gy-semantics-audit-protocol-v1",
        "derive_from_source": True, "per_station_fields": ["Y", "ratio", "binary expansion", "G-times-bit",
            "aggregate product", "scaling", "use sites", "interval endpoints", "proved Y domain", "invalid codes", "penalty"],
        "unscaled_product_assumption_forbidden": True,
    })
    write_json("aggregate_mccormick_protocol.json", {
        "schema": "round55-aggregate-mccormick-protocol-v1", "candidate": "MC4", "new_parameters": [],
        "methods": ["symbolic implication", "root-LP violation census", "exact LP violation maximization if needed"],
        "outcomes": ["exactly implied", "numerically implied", "strictly strengthening", "implementation inconsistency"],
        "live_if_exactly_implied": False, "live_name_if_strict": "SF-MC4",
    })
    write_json("station_state_formulation_protocol.json", {
        "schema": "round55-station-state-formulation-protocol-v1", "empirical_parameters": [],
        "station_domain": "actual integer final-inventory domain after frozen propagation; no size dispatch",
        "VD-P": {"selectors": "sum_y s_i_y=1; Y_i=sum_y y s_i_y", "perspective": "l*s_i_y<=q_i_y<=u*s_i_y",
                 "reconstruction": "sum_y q_i_y=G; Z_i=sum_y y*q_i_y", "replacement": "product-only bit block"},
        "VD-J": {"base": "VD-P", "ratio": "jointly represented when applicable",
                 "penalty": "e_i=sum_y |y/D_i-1| s_i_y", "nonobjective_e_constraints_must_be_preserved": True},
        "required": ["forward integer mapping", "reverse projection", "integer product exactness",
                     "isolated disjunctive convex-hull proof", "projection-strength caveat", "no V/M/Q dispatch"],
    })
    write_json("sparse_family_audit_protocol.json", {
        "schema": "round55-sparse-family-audit-protocol-v1", "active_family_count": 17,
        "panels": ["D1-D14", "C1-C9", "selected V20/V50"],
        "measurements": ["rows", "columns", "nonzeros", "root activity", "dual nonzero rate", "slack",
                         "root contribution", "LP Work", "presolve elimination", "build cost", "one-family-removal effect"],
        "maximum_single_family_removals": 2, "candidate_names": ["SF-R1", "SF-R2"],
        "removal_gate": ["exactness proved", "negligible contribution across roles", "material matrix cost", "uniform", "no dispatch"],
    })
    write_json("penalty_cover_dp_protocol.json", {
        "schema": "round55-penalty-cover-dp-protocol-v1", "conditional": True,
        "opening_gate": "VD-J or equivalent passes fixed-interval confirmation",
        "budget": "sum c_i_y s_i_y <= (U_bar-epsilon-l)/lambda_P for lambda_P>0",
        "cover": "at most one state per station; sum c_i_y>B; sum s_i_y<=|C|-1",
        "separation": "exact DP, exact shortest path, or exact zero-gap MIP; no unsafe rounding",
        "PC1": "one most-violated inclusion-minimal cover, one reoptimization",
        "PC2": "single-cut exact nonduplicate closure until no strict violation",
        "callback": False, "PreCrush_change": False,
        "offline_entry": "strict violations in at least two structural roles",
    })
    write_json("controlled_innovation_policy.json", {
        "schema": "round55-controlled-innovation-policy-v1", "maximum_revisions": 3,
        "one_mechanism_per_revision": True, "hash_before_testing": True, "complete_panel_required": True,
        "allowed": ["equivalent station-state implementation", "one valid cut-management change",
                    "exact DP/separation", "exact lifecycle/reuse", "conditionally one split mechanism"],
        "forbidden": ["instance/seed/panel/size/difficulty dispatch", "time/Work/node/memory dispatch",
                      "post-confirmation tuning", "combined unqualified mechanisms", "witness lookup", "fitted score"],
    })

    r54_v20 = [r for r in r54_panel["rows"] if int(r["V"]) == 20]
    r54_v50 = [r for r in r54_panel["rows"] if int(r["V"]) == 50]
    write_json("fixed_interval_development_freeze.json", {
        "schema": "round55-fixed-interval-development-freeze-v1",
        "source": repo_path(ROUND53 / "fixed_interval_development_freeze.json"),
        "source_sha256": sha256(ROUND53 / "fixed_interval_development_freeze.json"),
        "states": dev["states"], "state_ids": dev["state_ids"], "cap_seconds": 300,
        "stable": "F0-CLEAN", "initial_candidates": ["SF-MC4 if strict", "VD-P", "VD-J", "SF-R1 if eligible", "SF-R2 if eligible"],
        "maximum_selected_candidates": 3, "same_executable": True,
        "advancement_gate": ["zero false/correctness failures", "no lost F0 certificate", "zero severe",
                             "two roles", "shifted Work GM<=0.95 or certificate gain with nonworse Work/GI",
                             "capped GI nonworse", "no dispatch"],
    })
    extension = list(dev["states"]) + [instance_row(r, "V20 extension", 1800) for r in r54_v20[:2]] + [instance_row(r, "V50 extension", 1800) for r in r54_v50[:2]]
    write_json("fixed_interval_confirmation_freeze.json", {
        "schema": "round55-fixed-interval-confirmation-freeze-v1", "maximum_leaders": 2,
        "C1_C9": {"source": repo_path(ROUND53 / "fixed_interval_confirmation_freeze.json"),
                  "source_sha256": sha256(ROUND53 / "fixed_interval_confirmation_freeze.json"),
                  "states": conf["states"], "cap_seconds": 1200},
        "extension": {"states": extension, "cap_seconds": 1800},
        "source_or_policy_change_after_opening": False,
        "advancement_gate": ["zero false certificates", "no lost F0 certificate", "zero severe",
                             "exact-row shifted Work GM<=0.95 or certificate gain with nonworse Work/GI",
                             "capped GI nonworse", "two roles", "acceptable V20/V50 size/memory", "no post-development change"],
    })
    dev_by_id = {r["state_id"]: r for r in dev["states"]}
    long_ids = ["D1", "D3", "D4", "D12", "D5", "D9", "D13", "D14"]
    write_json("key_long_state_freeze.json", {
        "schema": "round55-key-long-state-freeze-v1", "cap_seconds": 3600,
        "states": [dev_by_id[i] for i in long_ids] + [instance_row(r54_v20[2], "V20 difficult", 3600), instance_row(r54_v50[2], "V50 difficult", 3600)],
        "arms": ["F0-CLEAN", "frozen formulation leader"],
        "failure": ["lost certificate", "new severe proof-tail regression", "material reversal", "unstable memory"],
    })
    standard_k1 = [
        ("reference/qualification_round39/small-medium/round39_small_medium_V12_M3_Q30_slot08_seed1343324363.txt", "major witness"),
        ("reference/qualification_round39/small-hard/round39_small_hard_V12_M3_Q30_slot08_seed1288546114.txt", "strong control"),
        ("reference/qualification_round39/small-hard/round39_small_hard_V10_M3_Q20_slot04_seed1145042375.txt", "V10 easy negative control"),
        ("reference/qualification_round39/small-hard/round39_small_hard_V12_M3_Q20_slot07_seed621538683.txt", "numerical endpoint"),
        ("reference/qualification_round39/small-hard/round39_small_hard_V12_M2_Q20_slot06_seed258908503.txt", "V12 M2 hard"),
        ("reference/qualification_round39/small-easy/round39_small_easy_V12_M3_Q30_slot08_seed1167625600.txt", "startup/easy V12"),
        ("reference/hard_stress/V20_M3/tight_T_seed3102.txt", "tight3102"),
        ("reference/hard_stress/V20_M3/tight_T_seed3101.txt", "tight3101"),
        ("reference/hard_stress/V20_M3/high_imbalance_seed3201.txt", "high-imbalance 3201"),
        ("reference/hard_stress/V20_M3/high_imbalance_seed3202.txt", "high-imbalance 3202"),
        ("reference/hard_stress/V20_M3/moderate_seed3301.txt", "moderate3301"),
        ("reference/hard_stress/V20_M3/moderate_seed3302.txt", "moderate3302"),
    ]
    k1_rows = []
    for path_text, role in standard_k1:
        path = ROOT / path_text
        k1_rows.append({"instance_id": path.stem, "role": role, "input_path": path_text,
                        "input_sha256": sha256(path), "cap_1800_seconds": 1800, "conditional_cap_3600_seconds": 3600})
    k1_rows.extend(instance_row(r, "additional V20", 1800) for r in r54_v20[:3])
    k1_rows.extend(instance_row(r, "additional V50", 1800) for r in r54_v50[:2])
    write_json("k1_integration_panel_freeze.json", {
        "schema": "round55-k1-integration-panel-freeze-v1", "arms": ["K1-AM-SF", "K1-AM-SF-CANDIDATE"],
        "instances": k1_rows, "cap_seconds": 1800, "conditional_unresolved_cap_seconds": 3600,
        "outer_controller_identical": True, "gate": ["zero false certificates", "major repair preserved",
            "certificate count nondecreasing", "zero severe", "shifted Work/GI nonworse", "material improvement",
            "benefit beyond one witness", "V20/V50 nonworse"],
    })
    write_json("split_action_diagnostic_protocol.json", {
        "schema": "round55-split-action-diagnostic-protocol-v1", "conditional": True,
        "opening": ["inner candidate passes fixed confirmation", "fails full K1", "material AM action changes",
                    "matched evidence links failure to action changes"],
        "counterfactuals": ["stable formulation+stable action", "candidate formulation+candidate action",
                            "candidate formulation+stable action", "stable formulation+candidate action"],
        "restricted_runs_are_original_certificates": False, "maximum_split_revisions": 1,
        "forbidden_inputs": ["time", "Work", "nodes", "V/M/Q", "instance features", "history", "classifier"],
    })
    write_json("sealed_generalization_protocol.json", {
        "schema": "round55-sealed-generalization-protocol-v1",
        "manifest": repo_path(OUT / "sealed_generalization_manifest.json"),
        "manifest_sha256": sha256(OUT / "sealed_generalization_manifest.json"),
        "arms": ["P-GRB", "K1-AM-SF", "K1-AM-SF-CANDIDATE"],
        "caps": {"V12": 3600, "V20": 3600, "V50": 7200},
        "checkpoints": [300, 1200, 1800, 3600, 7200],
        "opening": ["candidate source frozen", "official executable frozen", "full K1 passes", "no later algorithm change"],
        "expected_pgrb_fingerprint_pre_frozen": True,
    })
    write_json("strong_result_expansion_protocol.json", {
        "schema": "round55-strong-result-expansion-protocol-v1",
        "manifest": repo_path(OUT / "expansion_panel_manifest.json"),
        "manifest_sha256": sha256(OUT / "expansion_panel_manifest.json"),
        "opening_gate": ["zero severe vs stable", "no certificate loss", "shifted Work GM<=0.80",
                         "GI ratio<=0.80 or at least two additional certificates", "improvement in two size groups"],
        "arms": ["P-GRB", "K1-AM-SF", "K1-AM-SF-CANDIDATE"], "cap_seconds": 7200,
        "extension": {"sizes": [50, 70], "cap_seconds": 14400,
                      "trigger": "none of the three arms certifies that input by 7200", "all_arms": True},
        "V70_claim": "diagnostic unless sufficient exact certificates",
    })
    severe = {
        "schema": "round55-severe-regression-definition-v1",
        "exact": {"work": "ratio>1.50 and delta>50", "time": "ratio>1.50 and delta>60 seconds"},
        "capped_any": ["baseline certifies and candidate does not", "GI ratio>1.50 and absolute GI increase>=0.05",
                       "gap ratio>1.50 and absolute gap increase>=0.05"],
        "sub10_startup_exception": "not severe absent certificate loss, absolute severity-floor delay, or repeated systematic pattern",
        "same_definition_against_pgrb": True,
    }
    write_json("severe_regression_definition.json", severe)
    write_json("promotion_gates.json", {
        "schema": "round55-promotion-gates-v1",
        "pilot_to_development": "zero failures/false certificates/severe; exact mapping; benefit in two roles, certificate, or strong affordable LP gain",
        "development": "all Stage 6 gates", "confirmation": "all Stage 7 gates", "long": "all Stage 8 gates",
        "k1": "all Stage 12 gates", "sealed_vs_stable": "all seven Stage 13 gates",
        "sealed_vs_pgrb": "no severe; Work GM<1; GI<1; certificates>=P-GRB; not startup-only",
        "strong_expansion": "all five Stage 24 gates", "stable_paper_preset_replacement": False,
    })
    write_text("evidence_storage_policy.md", """
# Round 55 evidence storage policy

Commit source, tests, protocols, proofs, deterministic inputs, compact CSV/JSON
ledgers, decisions, hashes, documentation, manuscript sources, and reproduction
commands. Do not commit complete native run trees or model dumps. Local raw
evidence must be path/size/SHA-256 inventoried and represented by committed
compact rows that retain all failures and entered-stage outcomes. Never publish
credentials, licenses, machine-private configuration, or oversized logs.
""")
    write_json("official_start_record.json", {
        "schema": "round55-official-start-record-v1", "recorded_at_utc": now,
        "base_commit": BASE_HEAD, "base_tree": BASE_TREE, "base_branch": BASE_BRANCH,
        "base_pr": BASE_PR, "branch": BRANCH, "performance_results_inspected": False,
        "primary_panel_generated_and_sealed": True, "expansion_panel_generated_and_sealed": True,
        "ordinary_cap_seconds": 3600, "sealed_v50_cap_seconds": 7200, "conditional_expansion_cap_seconds": 14400,
        "development_build_reused": "build/dev-gurobi-release",
    })

    required = [
        "research_contract.md", "source_of_truth.md", "solver_contract.json", "stable_mainline_contract.json",
        "engineering_audit_protocol.json", "bug_classification_protocol.json", "first_class_controller_refactor_protocol.json",
        "gy_semantics_audit_protocol.json", "aggregate_mccormick_protocol.json", "station_state_formulation_protocol.json",
        "sparse_family_audit_protocol.json", "penalty_cover_dp_protocol.json", "controlled_innovation_policy.json",
        "fixed_interval_development_freeze.json", "fixed_interval_confirmation_freeze.json", "key_long_state_freeze.json",
        "k1_integration_panel_freeze.json", "split_action_diagnostic_protocol.json", "sealed_generalization_protocol.json",
        "sealed_generalization_manifest.json", "strong_result_expansion_protocol.json", "severe_regression_definition.json",
        "promotion_gates.json", "evidence_storage_policy.md", "official_start_record.json",
    ]
    extras = ["repository_start_audit.json", "environment_audit.json", "preexisting_file_preservation_audit.json",
              "expansion_panel_manifest.json"]
    entries = [entry(OUT / name) for name in required + extras]
    for panel in (primary, expansion):
        entries.extend(entry(ROOT / row["input_path"]) for row in panel["rows"])
    for path in [ROOT / "scripts" / "generate_round55_sealed_instances.py", ROOT / "scripts" / "prepare_round55_stage0.py",
                 ROUND53 / "fixed_interval_development_freeze.json", ROUND53 / "fixed_interval_confirmation_freeze.json",
                 ROUND54 / "stable_mainline_contract.json", ROOT / "src" / "main.cpp",
                 ROOT / "src" / "PaperExternalGiniTree.cpp", ROOT / "src" / "Round50IntervalMip.cpp", ROOT / "src" / "GurobiBaseline.cpp"]:
        entries.append(entry(path))
    write_json("stage0_freeze_manifest.json", {
        "schema": "round55-stage0-freeze-manifest-v1", "base_commit": BASE_HEAD, "base_tree": BASE_TREE,
        "branch": BRANCH, "performance_results_inspected_before_freeze": False,
        "required_stage0_file_count_excluding_manifest": len(required), "controlled_revision_maximum": 3,
        "split_revision_maximum": 1, "development_leader_maximum": 3, "confirmation_leader_maximum": 2,
        "post_confirmation_algorithm_source_changes_allowed": 0, "post_sealed_algorithm_source_changes_allowed": 0,
        "primary_sealed_input_count": 12, "expansion_sealed_input_count": 10,
        "ordinary_cap_seconds": 3600, "sealed_v50_cap_seconds": 7200, "conditional_expansion_cap_seconds": 14400,
        "entries": entries, "self_hash_note": "generated last; recursive self-hash intentionally excluded",
    })
    print(json.dumps({"required_stage0_files_including_manifest": len(required) + 1,
                      "manifest_entries": len(entries), "primary_inputs": 12, "expansion_inputs": 10}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
