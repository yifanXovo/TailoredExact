#!/usr/bin/env python3
"""Freeze the Round 43 protocol before any new candidate exact run."""

from __future__ import annotations

import json
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import round43_common as common


ROUND40_RUNS = (
    common.ROOT / "results" / "gf_regression_adaptive_round40" / "runs")
ROUND42 = (
    common.ROOT / "results" /
    "gf_decomposition_architecture_optimization_round42")

REFERENCE_RUN_PATTERNS = {
    "C6": "k1__{instance}__c6_hga_full_k4",
    "K1-old": "k1__{instance}__c6_k1_adaptive",
    "K1-single": "k1__{instance}__c6_k1_single",
    "K1-adaptive-decisive":
        "k1_iterative__{instance}__c6_k1_adaptive_decisive",
    "P-GRB": "k1__{instance}__p_grb",
}


def git(*args: str) -> str:
    return subprocess.check_output(
        ("git", *args), cwd=common.ROOT, text=True).strip()


def result_value(result: dict[str, Any], arm: str, c6: str, plain: str,
                 default: Any = "") -> Any:
    key = c6 if arm != "P-GRB" else plain
    return result.get(key, default)


def model_signature(run_dir: Path, result: dict[str, Any],
                    arm: str) -> tuple[str, bool]:
    if arm == "P-GRB":
        value = str(result.get("gurobi_canonical_model_sha256", ""))
        if not value:
            raise RuntimeError(f"missing P-GRB canonical hash: {run_dir}")
        return value, True
    optimize = run_dir / "external" / "paper_optimize_ledger.csv"
    rows = common.csv_rows(optimize)
    hashes = sorted({row["model_sha256"] for row in rows
                     if row.get("model_sha256")})
    if hashes:
        return common.stable_hash(hashes), True
    if (bool(result.get("strict_certified_original_problem", False)) and
            float(result.get("external_gini_tree_work", 0.0)) <= 1e-12):
        return common.stable_hash({
            "model_state": "no_exact_model_generated",
            "status": result.get("status", ""),
            "objective": result.get("objective", ""),
            "lower_bound": result.get("lower_bound", ""),
            "upper_bound": result.get("upper_bound", ""),
        }), False
    raise RuntimeError(f"missing external model hashes: {run_dir}")


def historical_result(instance: str, arm: str) -> tuple[Path, dict[str, Any],
                                                         dict[str, Any]]:
    run_dir = ROUND40_RUNS / REFERENCE_RUN_PATTERNS[arm].format(
        instance=instance)
    command = common.load_json(run_dir / "command.json")
    result = common.load_json(run_dir / "result.json")
    return run_dir, command, result


def historical_startup_classification(instance: str) -> dict[str, Any]:
    run_dir, _, result = historical_result(instance, "C6")
    startup = float(result["process_elapsed_at_exact_phase_start_seconds"])
    total = float(result["final_process_wall_time_seconds"])
    exact = max(0.0, total - startup)
    work = float(result["external_gini_tree_work"])
    startup_dominated = exact <= startup or work <= 1e-7
    return {
        "classification": (
            "startup_dominated" if startup_dominated else "material_proof"),
        "frozen_source": common.relative(run_dir / "result.json"),
        "historical_startup_seconds": startup,
        "historical_exact_phase_seconds": exact,
        "historical_exact_phase_work": work,
        "rule": (
            "startup_dominated iff historical C6 exact-phase elapsed is no "
            "greater than startup elapsed or exact-phase Work <= 1e-7; all "
            "other rows are material_proof"),
        "excluded_from_severe_tail": startup_dominated,
    }


def baseline_rows(inventory: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instance in common.DEVELOPMENT_IDS:
        for arm in REFERENCE_RUN_PATTERNS:
            run_dir, command, result = historical_result(instance, arm)
            input_hash = command.get("instance_sha256", "")
            expected_hash = inventory[instance]["sha256"]
            if input_hash != expected_hash:
                raise RuntimeError(f"historical input mismatch: {instance}/{arm}")
            threads = int(result_value(
                result, arm, "gurobi_threads_effective",
                "gurobi_threads_effective", 0))
            presolve = int(result_value(
                result, arm, "gurobi_presolve_effective",
                "gurobi_presolve_effective", -99))
            seed = int(result_value(
                result, arm, "gurobi_seed_effective",
                "gurobi_seed_effective", -99))
            rel_gap = float(result_value(
                result, arm, "gurobi_mip_gap_effective",
                "gurobi_mip_gap_effective", -1.0))
            abs_gap = float(result_value(
                result, arm, "gurobi_mip_gap_abs_effective",
                "gurobi_mip_gap_abs_effective", -1.0))
            contract = (threads == 1 and presolve == -1 and seed == 0 and
                        rel_gap == 0.0 and abs_gap == 0.0)
            contemporary = instance in common.CONTEMPORARY_REFERENCE_IDS and \
                arm in {"C6", "P-GRB"}
            canonical_signature, canonical_available = model_signature(
                run_dir, result, arm)
            rows.append({
                "instance_id": instance,
                "reference_arm": arm,
                "historical_run": common.relative(run_dir),
                "input_sha256": input_hash,
                "historical_executable_sha256":
                    command.get("executable_sha256", ""),
                "canonical_model_signature_sha256": canonical_signature,
                "canonical_model_hash_available": canonical_available,
                "gurobi_version": result.get("gurobi_version", "13.0.2"),
                "machine_identifier": "WIN-3NO58RVQ4VC",
                "threads_effective": threads,
                "presolve_effective": presolve,
                "seed_effective": seed,
                "relative_gap_effective": rel_gap,
                "absolute_gap_effective": abs_gap,
                "historical_solver_contract_valid": contract,
                "historical_strict_certificate": bool(
                    result.get("strict_certified_original_problem", False)),
                "post_implementation_model_equivalence_required": True,
                "candidate_outcomes_may_authorize_reuse": False,
                "mandatory_contemporary_rerun": contemporary,
                "contemporary_role": common.CONTEMPORARY_REFERENCE_IDS.get(
                    instance, ""),
                "frozen_disposition": (
                    "rerun_contemporaneously" if contemporary else
                    "reuse_only_after_post_implementation_equivalence_audit"),
            })
    return rows


def main() -> int:
    head = git("rev-parse", "HEAD")
    branch = git("branch", "--show-current")
    status = git("status", "--porcelain")
    allowed_stage0_sources = {
        "scripts/freeze_round43.py", "scripts/round43_common.py"}
    unexpected_status = []
    for line in status.splitlines():
        path = line[3:].replace("\\", "/") if len(line) >= 4 else ""
        if (path in allowed_stage0_sources or
                path == "results/gf_k1_k4_envelope_refinement_round43/"):
            continue
        unexpected_status.append(line)
    if (head != common.BASE_SHA or branch != common.RESEARCH_BRANCH or
            unexpected_status):
        raise RuntimeError(
            f"invalid Stage 0 checkout: head={head} branch={branch} "
            f"unexpected_status={unexpected_status}")
    inventory = common.inventory()
    expected = (set(common.DEVELOPMENT_IDS) | set(common.VALIDATION_IDS) |
                set(common.HOLDOUT_IDS))
    if len(expected) != 24 or expected != set(inventory):
        raise RuntimeError("Round 43 dataset is not the exact Round 39 inventory")
    if set(common.MECHANISM_ROLES) - set(common.DEVELOPMENT_IDS):
        raise RuntimeError("mechanism subset is not contained in development")

    common.OUT.mkdir(parents=True, exist_ok=True)
    captured = datetime.now(timezone.utc).isoformat()
    startup = {
        instance: historical_startup_classification(instance)
        for instance in common.DEVELOPMENT_IDS
    }

    dataset = {
        "schema": "round43-dataset-freeze-v1",
        "round_id": 43,
        "frozen_before_candidate_exact_runs": True,
        "candidate_results_observed": False,
        "round42_split_signature_sha256": common.load_json(
            ROUND42 / "experiment_split_freeze.json")
            ["split_signature_sha256"],
        "mechanism_development": [
            {"instance_id": item, "role": common.MECHANISM_ROLES[item],
             "sha256": inventory[item]["sha256"]}
            for item in common.MECHANISM_ROLES
        ],
        "development": [
            {"instance_id": item, "sha256": inventory[item]["sha256"],
             **startup[item]}
            for item in common.DEVELOPMENT_IDS
        ],
        "validation": [
            {"instance_id": item, "sha256": inventory[item]["sha256"]}
            for item in common.VALIDATION_IDS
        ],
        "sealed_holdout": [
            {"instance_id": item, "sha256": inventory[item]["sha256"]}
            for item in common.HOLDOUT_IDS
        ],
        "holdout_state": "sealed_no_round43_candidate_result",
        "no_v20_or_v50_generation": True,
    }
    common.write_json(common.OUT / "dataset_freeze.json", dataset)

    solver = {
        "schema": "round43-solver-contract-v1",
        "gurobi_version": "13.0.2",
        "presolve": "auto",
        "presolve_value": -1,
        "seed": 0,
        "threads": 1,
        "relative_mip_gap": 0.0,
        "absolute_mip_gap": 0.0,
        "startup_incumbent": "same independently verified HGA-FULL as C6",
        "complete_objective":
            "G + lambda * weighted absolute satisfaction deviation",
        "strict_improver_range": "unchanged existing exact construction",
        "certificate_tolerance": 1e-7,
        "independent_original_space_verifier": True,
        "archive_winner_injection": False,
        "known_optimum_injection": False,
        "per_instance_solver_tuning": False,
        "official_process_cap_seconds": 3600,
        "symmetric_extension_seconds": 7200,
    }
    common.write_json(common.OUT / "solver_contract.json", solver)

    gates = {
        "schema": "round43-promotion-gates-v1",
        "frozen_before_candidate_exact_runs": True,
        "correctness": {
            "false_certificates": 0,
            "incorrect_optimality_claims": 0,
            "every_incumbent_independently_verified": True,
            "complete_interval_coverage": True,
            "monotone_valid_global_lower_bound": True,
            "no_c6_certificate_regression": True,
            "default_off_semantic_equivalence": True,
        },
        "development": {
            "major_candidate_over_pgrb_work_max": 1.25,
            "strong_control_candidate_over_c6_work_max": 1.20,
            "strong_control_shifted_exact_time_max": 1.25,
            "material_candidate_over_pgrb_work_max": 1.35,
            "geomean_candidate_over_pgrb_work_max": 0.90,
            "geomean_candidate_over_c6_work_max": 1.05,
            "material_wins_at_least_losses": True,
            "joint_work_and_time_ratio_max": 1.50,
        },
        "validation": {
            "material_candidate_over_pgrb_work_max": 1.35,
            "geomean_candidate_over_pgrb_work_max": 1.00,
            "material_wins_at_least_losses": True,
            "strong_control_uses_frozen_development_result": True,
        },
        "selection_order": [
            "correctness", "major severe-regression protection",
            "strongest C6 positive-control protection",
            "worst material ratio", "aggregate Work", "aggregate time",
            "prefer K0=1 only if otherwise materially tied",
        ],
        "gates_may_change_after_candidate_results": False,
    }
    common.write_json(common.OUT / "promotion_gates.json", gates)

    forbidden = {
        "schema": "round43-forbidden-decision-inputs-v1",
        "forbidden": [
            "instance filename", "instance ID", "generation seed", "V", "M",
            "Q", "scenario label", "difficulty stratum", "historical winner",
            "elapsed seconds", "Gurobi Work", "processed nodes",
            "simplex iterations", "barrier iterations", "memory",
            "hardware identifier", "leaf effort", "historical classifier",
            "known regression lookup table",
        ],
        "allowed": [
            "interval endpoints", "verified incumbent U",
            "valid parent and descendant lower bounds",
            "valid infeasibility and optimality statuses",
            "model-derived interval geometry", "fixed K0", "fixed d",
            "fixed rho", "certificate tolerance",
        ],
        "decision_hash_excludes_telemetry": True,
        "source_level_audit_required": True,
    }
    common.write_json(common.OUT / "forbidden_decision_inputs.json", forbidden)

    environment = {
        "schema": "round43-base-environment-v1",
        "captured_utc": captured,
        "base_branch": common.BASE_BRANCH,
        "base_sha": common.BASE_SHA,
        "research_branch": common.RESEARCH_BRANCH,
        "upstream_branch": "origin/" + common.BASE_BRANCH,
        "base_upstream_ahead": 0,
        "base_upstream_behind": 0,
        "machine_identifier": socket.gethostname(),
        "established_protocol_machine_identifier": "WIN-3NO58RVQ4VC",
        "machine_identifier_matches_protocol":
            socket.gethostname() == "WIN-3NO58RVQ4VC",
        "gurobi": "13.0.2 build v13.0.2rc1",
        "compiler": "g++.exe (MSYS2 Rev2) 14.2.0",
        "cmake": "3.30.5-msvc23",
        "generator": "MinGW Makefiles",
        "configuration": "Release",
        "baseline_cpp_build": "passed",
        "baseline_ctest": "20/20 passed",
        "baseline_python_protocol": "117/118 passed",
        "baseline_python_failure": (
            "pre-existing Round41ProtocolTests source-name assertion expects "
            "solveRound41StaticSegmentedGini after Round42 renamed the shared "
            "function to solveStaticSegmentedGini"),
        "checkout_clean_before_branch_after_reversible_preservation": True,
        "preexisting_tracked_artifact_stash":
            "pre-round43-preserve-user-generated-results-2026-08-16",
        "preexisting_untracked_artifacts":
            "preserved in place by exact local .git/info/exclude entries",
    }
    common.write_json(
        common.OUT / "base_and_environment_manifest.json", environment)

    common.write_json(common.OUT / "official_start_record.json", {
        "schema": "round43-official-start-v1",
        "captured_utc": captured,
        "round_id": 43,
        "branch": common.RESEARCH_BRANCH,
        "base_sha": common.BASE_SHA,
        "candidate_exact_runs_started": False,
        "validation_opened": False,
        "holdout_opened": False,
        "protocol_files_frozen": True,
    })

    common.write_csv(
        common.OUT / "baseline_equivalence_manifest.csv",
        baseline_rows(inventory))

    common.write_text(common.OUT / "research_contract.md", """# Round 43 research contract

This round evaluates one exact, parameterized family `A(K0,d,rho)` at globally
fixed `K0` values 1 and 4. Both values use the same node operator and code path;
`K0` changes only the complete equal-width initial partition. Every Round 43
control is explicit and default-off.

The primary score is `D_d`. The only admissible secondary score is
`max(D_d,C_d)`, and only if the frozen structural atlas proves that `C_d` is
complete, stable, solver-independent, and adds information. Candidate behavior
may not inspect metadata, historical outcomes, hardware, time, Work, nodes,
iterations, or memory. The external 3600/7200 second caps interrupt the entire
algorithm but never choose an algorithmic action.

Development precedes validation. Validation remains closed until one globally
frozen candidate passes every development gate; the sealed holdout remains
closed until that same candidate passes validation. If no candidate passes,
all mathematically triggered Stage 4/5 branches must be completed or formally
ruled inadmissible before `bounded_systematic_negative_result` is assigned.
""")

    common.write_text(common.OUT / "candidate_family_definition.md", """# Candidate family definition

`A(K0,d,rho)` starts from the existing complete strict-improver Gini range and
uses an equal-width exact cover with `K0` in `{1,4}`. At every active interval
the shared node operator completes the parent LP, completes every cell of the
fixed dyadic depth-`d` lookahead profile, constructs the greatest convex affine
minorant of the clipped descendant bounds, computes `D_d`, and either performs
one binary midpoint split when the frozen score is at least `rho` or solves the
envelope-strengthened parent MIP exactly.

Lookahead depth never directly creates active leaves. Completed bounds are
retained, midpoint-child records receive valid aggregate descendant bounds, and
every facet is tagged with its source interval and propagated only to nested
descendants. The complete objective expression is used for envelope rows:
`(1-beta) G + lambda * sum_i weight_i e_i >= alpha`.

The Stage 1 depth choices are 1 and 2. The threshold grid is fixed at
`{0.01,0.03,0.05,0.10}`; no more than two values may be frozen from structural
scores before exact candidate runtimes are observed.
""")

    common.write_text(common.OUT / "source_of_truth.md", f"""# Round 43 source of truth

- Base: `{common.BASE_BRANCH}` at `{common.BASE_SHA}`; upstream was exactly
  synchronized (ahead 0, behind 0).
- Research branch: `{common.RESEARCH_BRANCH}`.
- Machine: `{socket.gethostname()}`; Gurobi 13.0.2; one thread; Seed 0;
  Presolve Auto; zero relative and absolute gaps.
- Dataset: the unchanged Round 39 10/7/7 Round 42 split. No V20 or V50 run is
  permitted. Validation and holdout candidate results are unopened at freeze.
- Validated default: C6-HGA-FULL, K0=4, rho=0.01. All Round 43 behavior is off
  unless explicitly selected.
- Baseline before changes: Release build passed and CTest was 20/20. The Python
  suite was 117/118 because the Round 41 source-name test was not updated after
  the Round 42 shared-function rename; this pre-existing failure is recorded
  and must be repaired without weakening its assertions.
- The raw checkout contained old generated artifacts despite the expected clean
  start. Six tracked artifacts are preserved in a named Git stash and exact
  untracked paths remain on disk behind local excludes. Neither is Round 43
  evidence or part of the PR.
- Existing Round 40 comparator rows are inventory-only until the required
  post-implementation model/contract equivalence audit passes. C6 and P-GRB are
  always rerun contemporaneously on the major regression, strongest control,
  and one easy startup guard.
""")

    frozen_names = [
        "research_contract.md", "source_of_truth.md",
        "candidate_family_definition.md", "forbidden_decision_inputs.json",
        "dataset_freeze.json", "solver_contract.json", "promotion_gates.json",
        "official_start_record.json", "base_and_environment_manifest.json",
        "baseline_equivalence_manifest.csv",
    ]
    hashes = {name: common.sha256(common.OUT / name) for name in frozen_names}
    common.write_json(common.OUT / "stage0_freeze_manifest.json", {
        "schema": "round43-stage0-freeze-manifest-v1",
        "round_id": 43,
        "captured_utc": captured,
        "frozen_before_candidate_exact_runs": True,
        "base_sha": common.BASE_SHA,
        "freeze_script_sha256": common.sha256(Path(__file__)),
        "common_script_sha256": common.sha256(
            common.ROOT / "scripts" / "round43_common.py"),
        "file_sha256": hashes,
    })
    print(json.dumps({
        "round": 43, "frozen_files": len(hashes),
        "baseline_equivalence_rows": len(baseline_rows(inventory)),
        "development": len(common.DEVELOPMENT_IDS),
        "validation": len(common.VALIDATION_IDS),
        "holdout": len(common.HOLDOUT_IDS),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
