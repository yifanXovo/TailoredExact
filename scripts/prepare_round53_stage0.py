#!/usr/bin/env python3
"""Create and hash the Round 53 pre-result research freeze.

This script is definition-only: it reads frozen manifests and source identity,
but never invokes a solver or reads a Round 53 candidate result.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"
ROUND50 = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
ROUND52 = ROOT / "results" / "gf_k1_tailored_cut_final_validation_round52"
BASE_HEAD = "44ed4057cc4d2ce67b86d623b57500e95cad5058"
BASE_TREE = "5e2f5a144b8f3f31439c1010ef07c8926d061d68"
BRANCH = "codex/round53-f0-qualification-callback-isolation"
CERT_EPS = 1e-7


def write_json(name: str, payload: object) -> None:
    (OUT / name).write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def json_value(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object in {path}")
    return value


def frozen_state(row: dict[str, str]) -> dict[str, object]:
    return {
        "state_id": row["state_id"], "instance": row["instance"],
        "interval_id": row["interval_id"], "state_kind": row["state_kind"],
        "role": row["historical_role"], "input_path": row["input_path"],
        "input_sha256": row["input_sha256"],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    sealed = json_value(OUT / "sealed_v12_instance_manifest.json")
    if (sealed.get("row_count") != 12 or
            sealed.get("solver_results_opened") is not False):
        raise RuntimeError("sealed V12 manifest is missing or already open")
    states = csv_rows(ROUND50 / "fixed_interval_state_manifest.csv")
    by_state = {row["state_id"]: row for row in states}
    development_ids = [f"D{index}" for index in range(1, 15)]
    confirmation_ids = [f"C{index}" for index in range(1, 10)]
    if any(state not in by_state for state in development_ids + confirmation_ids):
        raise RuntimeError("Round 50 fixed-state manifest is incomplete")

    (OUT / "research_contract.md").write_text(
        """# Round 53 frozen research contract

Round 53 is a preregistered, gated study on Round 52 head
`44ed4057cc4d2ce67b86d623b57500e95cad5058`. It asks whether the uniform
F0-CLEAN interval-MIP formulation should replace production v0, what proof
value the removed exhaustive subset-duration rows provided, which part of the
rejected Round 52 callback path caused regressions, and—only after fixed-MIP
qualification—whether unchanged K1-AM benefits on a new sealed V12 panel.

F0-CLEAN is frozen before results as
`interval-mip-core-no-exhaustive-subset-duration`: it removes only the
historical exhaustive subset-duration strengthening family, adds neither the
Round 52 static rank-2/rank-3 block nor a dynamic callback, leaves PreCrush at
its default, and preserves all other variables, rows, bounds, objectives,
interval/cutoff semantics, symmetry, branching, and solver settings. It is
uniform at every instance size. Historical v0 happens not to write the target
family for V>12, so equivalence there is a mathematical consequence, never a
dispatch rule.

The K1-AM outer controller is immutable: K0=1, one complete strict-improver
interval, midpoint refinement, adaptive-mass tau=0.08, and the Round 47 native
target, exact-parent closure, infeasible-child, coverage, bound, and strict
certificate lifecycle. All rescues, alternative points, symmetry/branching
research, M1, and additional cut families remain off.

Every official row uses the same executable and complete minimization
objective with Presolve=Auto, Seed=0, Threads=1, MIPGap=0, MIPGapAbs=0,
certificate tolerance 1e-7, verified incumbent/cutoff contract, honest
total-process accounting, and no known-optimum/archive-winner injection.
Ordinary caps are at most 3600 seconds. Only the four sealed tight-T instances
may trigger the frozen all-arm 7200-second extension.

Stages open only through their written gates. F0 itself may never be revised.
At most one uniform rescue, selected from R1/R2 using LP/callback diagnostics
rather than runtime wins, may open. No algorithm change is permitted after
fixed confirmation opens or after the sealed panel opens. Negative and mixed
conclusions are valid outcomes; witness-, size-, identity-, time-, Work-,
node-, memory-, or hardware-dependent actions are forbidden.
""", encoding="utf-8")

    (OUT / "source_of_truth.md").write_text(
        """# Round 53 source of truth

The base repository identity is Round 52 commit
`44ed4057cc4d2ce67b86d623b57500e95cad5058` and tree
`5e2f5a144b8f3f31439c1010ef07c8926d061d68`. The outer controller is exactly
the committed Round 52 `k1_am_controller_freeze.json`; its source SHA-256 is
`169e4b7a509a307fa90d3075523f4b42e81cc8530a22592e1ce501bf35d9a64a`.

Fixed state identities and reconstruction data come only from Round 50
`fixed_interval_state_manifest.csv` and
`fixed_interval_state_reconstruction_audit.csv`. F0-CLEAN is defined only by
`f0_mathematical_contract.json` and the explicit named policy. Historical
`f0-no-rank3-support-duration` remains an alias for reproduction.

The sealed panel identities are the deterministic Stage-0 JSON/CSV manifests
under this evidence root and the hashed inputs under
`reference/round53_sealed_v12/`. Solver results remain sealed until the final
backend, integration decision, source commit, official build directory, and
executable SHA-256 are frozen. Compact committed ledgers are authoritative;
inventoried native logs are local reproduction evidence only.
""", encoding="utf-8")

    write_json("solver_contract.json", {
        "schema": "round53-solver-contract-v1",
        "gurobi": {"Presolve": "Auto", "Seed": 0, "Threads": 1,
                   "MIPGap": 0.0, "MIPGapAbs": 0.0},
        "objective": "complete original minimization objective",
        "incumbent_cutoff_contract": "same verified incumbent and cutoff",
        "certificate_tolerance": CERT_EPS,
        "ordinary_maximum_total_process_seconds": 3600,
        "sealed_tight_extension_maximum_total_process_seconds": 7200,
        "cap_includes": ["construction", "LP diagnostics", "callback",
                         "separator", "solver", "verification", "serialization"],
        "known_optimum_injection": False,
        "archive_winner_injection": False,
        "one_official_executable_for_all_entered_comparators": True,
    })
    write_json("forbidden_mechanisms.json", {
        "schema": "round53-forbidden-mechanisms-v1",
        "outer_controller_changes": 0,
        "mechanisms_forbidden": [
            "gamma-veto", "AMF", "reduced-cost rescue", "fixed-rho fallback",
            "PMM", "FPMM", "non-midpoint points", "AMC for K1", "symmetry variants",
            "static branching priorities", "adaptive branching priorities",
            "root strong-branch probes", "Round51 M1", "additional cut families"],
        "dispatch_inputs_forbidden": [
            "instance_name", "path", "seed", "V", "M", "Q", "difficulty_label",
            "stage_membership", "elapsed_time", "Work", "node_count", "memory",
            "hardware", "historical_winner"],
        "core_feasibility_constraint_removal": False,
        "known_optimum_or_archive_injection": False,
        "post_confirmation_revision": False,
        "post_sealed_opening_revision": False,
    })

    history = [
        [47, "K1-AM", "src/PaperExternalGiniTree.cpp",
         "results/gf_c6_adaptive_mass_contraction_round47/final_decision.json",
         "frozen as Round52 K1-AM tau=0.08", "only named K1-AM policies"],
        [48, "K1-AMF", "src/Round48K1AMF.cpp",
         "results/gf_k1_amf_formulation_rescue_round48/final_decision.json",
         "bounded negative", "off"],
        [49, "K1 reduced-cost rescue", "src/Round49K1RC.cpp",
         "results/gf_k1_lp_primal_dual_rescue_round49/final_decision.json",
         "bounded negative", "off"],
        [50, "interval-MIP policies", "src/Round50IntervalMip.cpp",
         "results/gf_k1_interval_mip_vnext_round50/final_decision.json",
         "production v0 retained", "off unless explicit"],
        [51, "M1/symmetry/branching", "src/Round51TightBigM.cpp",
         "results/gf_k1_tight_big_m_sparse_branching_round51/final_decision.json",
         "rejected", "off"],
        [52, "rank-3 root user cuts", "src/Round52TailoredCuts.cpp",
         "results/gf_k1_tailored_cut_final_validation_round52/final_decision.json",
         "rejected; infrastructure retained", "off"],
        [52, "historical F0 alias", "src/Round50IntervalMip.cpp",
         "results/gf_k1_tailored_cut_final_validation_round52/static_dynamic_ablation.csv",
         "preliminary only; not independently qualified", "off"],
    ]
    with (OUT / "historical_algorithm_manifest.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["round", "mechanism", "implementation", "evidence",
                         "historical_decision", "round53_default"])
        writer.writerows(history)

    write_json("f0_mathematical_contract.json", {
        "schema": "round53-f0-mathematical-contract-v1",
        "paper_name": "F0-CLEAN",
        "research_policy": "interval-mip-core-no-exhaustive-subset-duration",
        "historical_alias": "f0-no-rank3-support-duration",
        "primary_candidate_frozen_before_runs": True,
        "removed_family": (
            "historical exhaustive subset-duration strengthening block written "
            "under the production-v0 V<=12 guard"),
        "removed_round52_static_rank2_rank3_block": True,
        "dynamic_support_duration_callback": "off",
        "PreCrush_override": "none",
        "preserved": [
            "all core feasibility rows", "all variables and order", "all domains",
            "all non-target coefficients and RHS", "objective", "interval restriction",
            "cutoff", "symmetry", "Gurobi default branching", "solver parameters"],
        "uniform_definition": (
            "F0-CLEAN never includes the exhaustive static subset-duration family"),
        "V_gt_12_equivalence_reason": (
            "production v0 historically does not generate the target family for V>12"),
        "instance_size_dispatch": False,
        "integer_feasible_set_and_objective_must_match": True,
    })

    write_json("fixed_interval_development_freeze.json", {
        "schema": "round53-f0-development-freeze-v1",
        "source_manifest": repo_path(ROUND50 / "fixed_interval_state_manifest.csv"),
        "source_manifest_sha256": sha256(ROUND50 / "fixed_interval_state_manifest.csv"),
        "state_ids": development_ids, "state_count": 14,
        "policies": ["production-v0", "F0-CLEAN"],
        "physical_row_count": 28, "total_process_cap_seconds": 300,
        "same_executable_required": True,
        "states": [frozen_state(by_state[state]) for state in development_ids],
        "gate": {
            "correctness_failures": 0, "false_certificates": 0,
            "lost_baseline_certificates": 0, "severe_regressions": 0,
            "common_exact_changed_work_geomean_max": 0.95,
            "alternative": "certificate gain with nonworse aggregate Work/GI",
            "capped_GI_nonworse": True, "structural_roles_improved_minimum": 2,
            "V_gt_12_equivalence": True, "forbidden_dispatch": False,
        },
    })
    write_json("fixed_interval_confirmation_freeze.json", {
        "schema": "round53-f0-confirmation-freeze-v1",
        "source_manifest": repo_path(ROUND50 / "fixed_interval_state_manifest.csv"),
        "source_manifest_sha256": sha256(ROUND50 / "fixed_interval_state_manifest.csv"),
        "state_ids": confirmation_ids, "state_count": 9,
        "policies": ["production-v0", "F0-CLEAN"], "physical_row_count": 18,
        "total_process_cap_seconds": 1200,
        "opens_only_if_development_passes": True,
        "algorithm_change_after_opening_forbidden": True,
        "states": [frozen_state(by_state[state]) for state in confirmation_ids],
        "gate": {
            "false_certificates": 0, "lost_baseline_certificates": 0,
            "severe_regressions": 0, "exact_work_geomean_max": 0.95,
            "alternative": "certificate gain with nonworse aggregate Work/GI",
            "capped_GI_nonworse": True, "post_development_source_changes": 0,
        },
    })
    key_ids = ["D1", "D3", "D4", "D12", "C1", "C2"]
    write_json("key_long_state_freeze.json", {
        "schema": "round53-key-long-state-freeze-v1",
        "state_ids": key_ids, "state_count": 6,
        "policies": ["production-v0", "F0-CLEAN"], "physical_row_count": 12,
        "total_process_cap_seconds": 3600,
        "opens_only_if_confirmation_passes": True,
        "promotion_forbidden_if_baseline_certificate_lost": True,
        "states": [frozen_state(by_state[state]) for state in key_ids],
    })

    callback_modes = [
        {"mode": "C0", "name": "baseline", "PreCrush": "default",
         "mipnode": False, "vector": False, "separator": False, "submit": False},
        {"mode": "C1", "name": "precrush-only", "PreCrush": 1,
         "mipnode": False, "vector": False, "separator": False, "submit": False},
        {"mode": "C2", "name": "status-only", "PreCrush": "default",
         "mipnode": True, "vector": False, "separator": False, "submit": False},
        {"mode": "C3", "name": "status-only-precrush", "PreCrush": 1,
         "mipnode": True, "vector": False, "separator": False, "submit": False},
        {"mode": "C4", "name": "separator-dry-run", "PreCrush": 1,
         "mipnode": True, "vector": True, "separator": True, "submit": False},
        {"mode": "C5", "name": "live-round52", "PreCrush": 1,
         "mipnode": True, "vector": True, "separator": True, "submit": True},
    ]
    callback_ids = ["D1", "D3", "D13", "D14"]
    write_json("callback_isolation_protocol.json", {
        "schema": "round53-callback-isolation-protocol-v1",
        "mathematical_model": "F0-CLEAN for every mode",
        "state_ids": callback_ids, "states": [frozen_state(by_state[state])
                                               for state in callback_ids],
        "modes": callback_modes, "mode_count": 6,
        "cap_300_seconds": 300, "physical_rows_300": 24,
        "conditional_cap_1200_seconds": 1200,
        "conditional_state_ids": ["D1", "D13"],
        "conditional_physical_rows": 12,
        "conditional_trigger": (
            "D1 or D13 certificate classification differs among modes, or "
            "primary source remains ambiguous"),
        "diagnostic_may_change_f0_decision": False,
        "classifications": [
            "no material callback-path effect", "PreCrush-dominant effect",
            "MIPNODE-registration effect", "PreCrush/callback interaction",
            "relaxation-extraction/separator overhead", "actual-cut effect",
            "mixed or inconclusive"],
    })
    write_json("bounded_revision_policy.json", {
        "schema": "round53-bounded-revision-policy-v1",
        "opens_only_after_f0_gate_failure": True,
        "requires_useful_support_duration_strength_loss_not_correctness_error": True,
        "maximum_rescue_candidates": 1,
        "menu": {
            "R1": "F0-CLEAN plus static exact rank-2 rows; callback off; PreCrush default",
            "R2": ("F0-CLEAN plus finite external rank-2/rank-3 root-LP closure; "
                   "restore integer types; terminal callback off; PreCrush default")},
        "R1_trigger": (
            "repeated rank-2 activity or nonzero dual contribution in at least "
            "two structural roles"),
        "R2_trigger": (
            "strict root-LP violations in at least two structural roles and "
            "live callback/PreCrush—not cut mathematics—is primary problem"),
        "selection_may_use_final_mip_runtime_wins": False,
        "development": {"state_ids": development_ids, "cap_seconds": 300},
        "confirmation": {"state_ids": confirmation_ids, "cap_seconds": 1200,
                         "opens_only_if_rescue_development_passes": True},
        "second_revision_allowed": False,
    })

    integration_names = [
        ("round39_small_medium_V12_M3_Q30_slot08_seed1343324363", "major witness"),
        ("round39_small_hard_V12_M3_Q30_slot08_seed1288546114", "strong control"),
        ("round39_small_hard_V10_M3_Q20_slot04_seed1145042375", "easy negative control"),
        ("round39_small_hard_V12_M3_Q20_slot07_seed621538683", "numerical endpoint"),
        ("round39_small_hard_V12_M2_Q20_slot06_seed258908503", "V12 M2 hard"),
        ("round39_small_easy_V12_M3_Q30_slot08_seed1167625600", "startup/easy control"),
    ]
    integration_rows = []
    all_reference = list((ROOT / "reference").rglob("*.txt"))
    by_stem = {path.stem: path for path in all_reference}
    for name, role in integration_names:
        path = by_stem.get(name)
        if path is None:
            raise RuntimeError(f"missing integration input {name}")
        integration_rows.append({
            "instance_id": name, "role": role, "input_path": repo_path(path),
            "input_sha256": sha256(path)})
    round52_validation = json_value(ROUND52 / "validation_instance_manifest.json")
    sentinel_rows = []
    for size in (20, 50):
        match = next(row for row in round52_validation["rows"]
                     if int(row["V"]) == size and
                     row["difficulty_configuration"] == "moderate_3600")
        sentinel_rows.append({
            "size": size, "instance_id": match["instance_id"],
            "input_path": match["input_path"], "input_sha256": match["input_sha256"],
            "cap_seconds": 300, "purpose": "hidden dispatch/policy leakage sentinel"})
    write_json("k1_integration_panel_freeze.json", {
        "schema": "round53-k1-integration-panel-freeze-v1",
        "controller": "Round52 frozen K1-AM", "K0": 1, "tau": 0.08,
        "arms": ["K1-AM-v0", "K1-AM-CANDIDATE"],
        "changed_model_instances": integration_rows,
        "stages": [
            {"cap_seconds": 300, "physical_rows": 12, "mandatory": True},
            {"cap_seconds": 1800, "physical_rows": 12,
             "opens_only_if_300_gate_passes": True},
            {"cap_seconds": 3600, "instance_roles": [
                 "major witness", "strong control", "numerical endpoint"],
             "physical_rows": 6, "opens_for_unresolved_predeclared_hard_rows": True}],
        "V20_V50_short_sentinels": sentinel_rows, "sentinel_arms": 2,
        "sentinel_physical_rows": 4,
        "broad_V20_V50_duplicate_matrix_forbidden": True,
        "gate": ["zero false certificates", "major repair preserved",
                 "easy negative control remains easy", "no severe regression",
                 "certificate count nondecreasing", "aggregate Work/GI nonworse",
                 "material improvement required for new backend"],
    })
    write_json("sealed_v12_instance_protocol.json", {
        "schema": "round53-sealed-v12-protocol-v1",
        "base_commit": BASE_HEAD, "derivation_version": "round53-sealed-v12-v1",
        "cartesian_product": {"V": [12], "M": [2, 3], "Q": [20, 30],
                              "configurations": ["tight_T_2400",
                                                 "high_imbalance_3600",
                                                 "moderate_3600"]},
        "instance_count": 12, "methods": ["P-GRB", "K1-AM-v0",
                                           "K1-AM-CANDIDATE"],
        "ordinary_cap_seconds": 3600, "ordinary_physical_rows": 36,
        "checkpoints_seconds": [300, 1200, 1800, 3600],
        "extension_cap_seconds": 7200, "extension_eligible_instances": 4,
        "extension_rule": (
            "extend all three methods on a tight_T_2400 instance iff none of "
            "the three certifies by 3600 seconds"),
        "opening_requires": ["qualified frozen new backend",
                             "passing K1 integration decision",
                             "frozen source commit", "clean official build",
                             "frozen executable SHA-256",
                             "no remaining algorithmic changes"],
        "algorithm_changes_after_opening": 0,
        "result_dependent_instance_selection": False,
    })
    write_json("severe_regression_definition.json", {
        "schema": "round53-severe-regression-definition-v1",
        "exact_rows": {
            "work": "candidate/baseline > 1.50 and candidate-baseline > 50",
            "time": "candidate/baseline > 1.50 and candidate-baseline > 60 seconds"},
        "capped_rows_any": ["baseline certifies and candidate does not",
                            "GI ratio > 1.50 and absolute increase >= 0.05",
                            "gap ratio > 1.50 and absolute increase >= 0.05"],
        "full_k1_vs_pgrb": (
            "reuse results/gf_k1_tailored_cut_final_validation_round52/"
            "severe_regression_definition.json"),
    })
    write_json("promotion_gates.json", {
        "schema": "round53-promotion-gates-v1",
        "f0_development": {
            "mandatory": ["zero correctness failures", "zero false certificates",
                          "no lost v0 certificate", "zero severe regressions",
                          "capped aggregate GI nonworse", "two structural roles",
                          "V>12 equivalence", "no forbidden dispatch"],
            "performance": (
                "common-exact changed-state Work GM <=0.95 OR certificate gain "
                "with nonworse aggregate Work/GI")},
        "f0_confirmation": {
            "mandatory": ["zero false certificates", "no lost v0 certificate",
                          "zero severe regressions", "capped aggregate GI nonworse",
                          "no post-development source change"],
            "performance": (
                "exact Work GM <=0.95 OR certificate gain with nonworse aggregate Work/GI")},
        "key_long": "no production-v0 certificate lost",
        "fixed_interval_promotion": "all entered fixed-interval stages pass",
        "k1_integration": (
            "zero false certificates; repair/control gates; no severe regression; "
            "certificates nondecreasing; aggregate Work/GI nonworse; material gain"),
        "sealed": (
            "zero false certificates; candidate certificates >= v0; no severe v0 "
            "regression; Work GM <=0.95 OR certificate gain with nonworse Work/GI; "
            "GI nonworse; repair preserved; no severe P-GRB regression; benefit "
            "spans more than one M/Q configuration"),
    })
    (OUT / "evidence_storage_policy.md").write_text(
        """# Round 53 evidence storage policy

Commit source, tests, pre-result freezes, exactness proofs, compact row/model/
activity/callback ledgers, summary CSV/JSON, hashes, final reports, and
reproduction commands. Native logs and full model trees remain local-only
unless a compact archive is specifically useful. Every local-only group must
be inventoried with deterministic SHA-256 tree identity, size, file count,
generating command, executable hash, and a committed representative ledger.
Historical raw evidence is immutable. Missing entered-stage rows force
`round53_incomplete`. Source-scope, secret/license, cap, certificate,
preservation, and evidence-hash audits are publication gates.
""", encoding="utf-8")
    write_json("official_start_record.json", {
        "schema": "round53-official-start-record-v1",
        "repository": "E:/codes/ExactEBRP",
        "expected_base_branch": "codex/round52-k1-tailored-cut-final-validation",
        "starting_branch": "codex/round52-k1-tailored-cut-final-validation",
        "created_branch": BRANCH,
        "local_head": BASE_HEAD, "local_tree": BASE_TREE,
        "upstream_at_start": "origin/codex/round52-k1-tailored-cut-final-validation",
        "remote_pr": {"number": 108, "state": "OPEN", "is_draft": True,
                      "base": "codex/round51-tight-big-m-root-sparse-branching",
                      "head": "codex/round52-k1-tailored-cut-final-validation",
                      "head_sha": BASE_HEAD, "head_tree": BASE_TREE},
        "local_remote_head_equivalent": True,
        "local_remote_tree_equivalent": True,
        "working_tree_start": {
            "porcelain_entry_count": 46290, "tracked_modified_count": 3,
            "untracked_entry_count": 46287,
            "porcelain_snapshot_sha1": "7a44b1bcc0cd4b2accee609fdcd877d10640e18d",
            "tracked_diff_sha1": "174771ed1c9cd5a5490b90b5922fec7ddf644d3a",
            "tracked_modified": [
                {"path": "results/gf_compact_bc_round/handling_convention_test/handling_convention.json",
                 "blob_sha1": "98bcd60c3c5542772f101d5c73643033b78c58da"},
                {"path": "results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv",
                 "blob_sha1": "730b12307ff356aad1972158312c3c791f4492ec"},
                {"path": "results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json",
                 "blob_sha1": "c6ea164aec30b59fbee030476ed9cd6a4ffa315f"}],
            "preservation_rule": (
                "all pre-existing modifications and unrelated untracked paths "
                "are user-owned and excluded from Round53 commits")},
        "toolchain": {"compiler": "GCC 14.2.0", "cmake": "3.30.5-msvc23",
                      "gurobi": "13.0.2rc1", "gurobi_api": "C API"},
        "machine": {"hostname": "WIN-3NO58RVQ4VC",
                    "manufacturer": "ASUS", "model": "System Product Name",
                    "cpu": "12th Gen Intel(R) Core(TM) i7-12700KF",
                    "logical_processors": 20, "memory_bytes": 34163961856,
                    "os": "Microsoft Windows 10 Professional 10.0.19045"},
        "pr108_mutation_forbidden": True,
        "candidate_result_inspected_before_stage0": False,
        "network_note": (
            "one git fetch reset occurred; GitHub API PR identity and the "
            "existing remote-tracking ref independently matched local identity"),
    })

    required = [
        "research_contract.md", "source_of_truth.md", "solver_contract.json",
        "forbidden_mechanisms.json", "historical_algorithm_manifest.csv",
        "f0_mathematical_contract.json", "fixed_interval_development_freeze.json",
        "fixed_interval_confirmation_freeze.json", "key_long_state_freeze.json",
        "callback_isolation_protocol.json", "bounded_revision_policy.json",
        "k1_integration_panel_freeze.json", "sealed_v12_instance_protocol.json",
        "sealed_v12_instance_manifest.json", "severe_regression_definition.json",
        "promotion_gates.json", "evidence_storage_policy.md",
        "official_start_record.json",
    ]
    supporting = ["sealed_v12_instance_manifest.csv"]
    hash_paths = [OUT / name for name in required + supporting]
    hash_paths.extend(ROOT / row["input_path"] for row in sealed["rows"])
    hash_paths.extend([
        ROOT / "scripts" / "generate_round53_sealed_v12_instances.py",
        ROOT / "scripts" / "prepare_round53_stage0.py",
        ROUND50 / "fixed_interval_state_manifest.csv",
        ROUND50 / "fixed_interval_state_reconstruction_audit.csv",
        ROUND52 / "k1_am_controller_freeze.json",
        ROUND52 / "final_decision.json",
        ROUND52 / "severe_regression_definition.json",
        ROOT / "src" / "PaperExternalGiniTree.cpp",
        ROOT / "src" / "Round50IntervalMip.cpp",
        ROOT / "src" / "Round52TailoredCuts.cpp",
        ROOT / "src" / "GurobiBaseline.cpp",
    ])
    entries = [{"path": repo_path(path), "bytes": path.stat().st_size,
                "sha256": sha256(path)} for path in hash_paths]
    write_json("stage0_freeze_manifest.json", {
        "schema": "round53-stage0-freeze-manifest-v1",
        "base_commit": BASE_HEAD, "base_tree": BASE_TREE, "branch": BRANCH,
        "candidate_results_inspected_before_freeze": False,
        "primary_candidate": "F0-CLEAN",
        "primary_policy": "interval-mip-core-no-exhaustive-subset-duration",
        "required_stage0_file_count_excluding_manifest": len(required),
        "sealed_v12_input_count": 12,
        "maximum_rescue_candidates": 1,
        "ordinary_maximum_process_seconds": 3600,
        "extension_maximum_process_seconds": 7200,
        "post_confirmation_algorithm_changes_allowed": 0,
        "post_sealed_opening_algorithm_changes_allowed": 0,
        "entries": entries,
        "self_hash_note": (
            "generated last and intentionally excludes its own recursive hash"),
    })
    print(f"created and hashed {len(required) + 1} required Stage 0 files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
