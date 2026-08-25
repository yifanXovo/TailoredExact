#!/usr/bin/env python3
"""Freeze Round 47 contracts, offline score census, tau, and references."""

from __future__ import annotations

import csv
import json
import math
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

import round47_common as common


ROOT = common.ROOT
OUT = common.OUT
R46 = ROOT / "results" / "gf_c6_rho_k1_k4_screen_round46"
R46_RUNS = R46 / "runs"
R45 = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45" / "completion"
CERT = 1e-7
MASS_EPS = max(CERT, 1e-12)

LOCAL_R46_HEAD = "a0b5f5f623d6adbbbbfa01c31d95aaf3d65d3dce"
LOCAL_R46_TREE = "4cc1b162d0ccdab87610a3c8f2411a87798b9a84"
REMOTE_R46_HEAD = "4798a9905c1d4a1f4ab9d8ca7baa7cf6f7d3ce9b"
REMOTE_R46_TREE = LOCAL_R46_TREE
R46_SOURCE_COMMIT = "36033fab439ceb76ff6c82a28a897f423a3a501d"
R46_SOURCE_TREE = "545bb7629500f6154534a4b690769a78254fed79"
R45_COMMIT = "1313086b8d1e1b1c163a8bf1c4011f08e8534dc8"
R45_TREE = "fd1378ef7f93f444049d21dba58e104a0fed446d"


def git(*arguments: str) -> str:
    return subprocess.check_output(
        ["git", *arguments], cwd=ROOT, text=True).strip()


def truth(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def finite(value: Any, default: float = math.nan) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def score(row: dict[str, str]) -> dict[str, float]:
    parent = float(row["parent_bound"])
    left = float(row["left_child_bound"])
    right = float(row["right_child_bound"])
    upper = float(row["verified_incumbent"])
    proof_gap = max(upper - parent, CERT)
    left_raw = (left - parent) / proof_gap
    right_raw = (right - parent) / proof_gap
    left_gain = min(1.0, max(0.0, left_raw))
    right_gain = min(1.0, max(0.0, right_raw))
    eta = min(left_gain, right_gain)
    mu = (left_gain + right_gain) / 2.0
    value = eta * mu
    scale = max(1.0, abs(parent), abs(left), abs(right), abs(upper))
    bound_tolerance = max(CERT, 32.0 * sys.float_info.epsilon * scale)
    score_tolerance = min(
        1.0, bound_tolerance / proof_gap + 32.0 * sys.float_info.epsilon)
    return {
        "proof_gap": proof_gap,
        "g_L_raw": left_raw, "g_R_raw": right_raw,
        "g_L": left_gain, "g_R": right_gain,
        "eta": eta, "mu": mu, "S_AM": value,
        "adaptive_rho": min(1.0, common.TAU / max(mu, MASS_EPS)),
        "score_tolerance": score_tolerance,
    }


def direct_ledgers() -> list[Path]:
    return sorted(path for path in R46_RUNS.glob("*/c6_split_decision_ledger.csv")
                  if path.is_file())


def augmented(row: dict[str, str], ledger: Path) -> dict[str, Any]:
    values = score(row)
    run_id = row["run_id"]
    stage = run_id.split("__", 1)[0]
    instance = run_id.split("__", 2)[1]
    arm = run_id.rsplit("__", 1)[1]
    return {
        "source_run_id": run_id, "stage": stage, "instance": instance,
        "arm": arm, "K0": int(row["K0"]), "rho": float(row["rho"]),
        "decision_sequence": int(row["decision_sequence"]),
        "interval_id": row["interval_id"], "parent_id": row["parent_id"],
        "depth": int(row["depth"]), "gamma_L": float(row["gamma_L"]),
        "gamma_U": float(row["gamma_U"]),
        "parent_bound": float(row["parent_bound"]),
        "left_child_bound": float(row["left_child_bound"]),
        "right_child_bound": float(row["right_child_bound"]),
        "verified_incumbent": float(row["verified_incumbent"]),
        **values, "round46_action": row["selected_action"],
        "round46_reason": row["deterministic_reason"],
        "source_ledger": ledger.relative_to(ROOT).as_posix(),
        "source_ledger_sha256": common.sha256(ledger),
    }


def primary_states(all_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    major = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
    specifications = {
        "H1_k4_major_critical": ("stage4_1200s", major, "K4-r001", 3),
        "H2_k1_major_root": ("stage4_1200s", major, "K1-r001", 1),
        "B1_k1_moderate_root": ("stage3_300s", "moderate_seed3301", "K1-r015", 1),
        "B2_k1_high_root": ("stage3_300s", "high_imbalance_seed3201", "K1-r020", 1),
        "D1_easy_v12_k1_root": (
            "stage3_300s",
            "round39_small_easy_V12_M3_Q30_slot08_seed1167625600",
            "K1-r001", 1),
    }
    selected: dict[str, dict[str, Any]] = {}
    for label, key in specifications.items():
        matches = [row for row in all_rows if
                   (row["stage"], row["instance"], row["arm"],
                    row["decision_sequence"]) == key]
        if len(matches) != 1:
            raise RuntimeError(f"primary state {label} match count {len(matches)}")
        selected[label] = matches[0]
    return selected


def write_census() -> dict[str, Any]:
    finite_rows: list[dict[str, Any]] = []
    one_child_rows: list[dict[str, Any]] = []
    for ledger in direct_ledgers():
        rows = common.csv_rows(ledger)
        for row in rows:
            left_infeasible = truth(row["left_child_infeasible"])
            right_infeasible = truth(row["right_child_infeasible"])
            if not left_infeasible and not right_infeasible and \
                    row["left_child_bound"] and row["right_child_bound"]:
                finite_rows.append(augmented(row, ledger))
            elif left_infeasible ^ right_infeasible:
                run_id = row["run_id"]
                run_dir = ledger.parent
                child_lp = common.csv_rows(run_dir / "child_lp_ledger.csv")
                infeasible_id = row["left_child_id"] if left_infeasible \
                    else row["right_child_id"]
                feasible_id = row["right_child_id"] if left_infeasible \
                    else row["left_child_id"]
                descendants = sum(
                    item.get("interval_id", "").startswith(feasible_id + ".")
                    for item in rows)
                related_lp = sum(
                    item.get("child_id", "").startswith(feasible_id)
                    for item in child_lp)
                one_child_rows.append({
                    "run_id": run_id,
                    "stage": run_id.split("__", 1)[0],
                    "instance": run_id.split("__", 2)[1],
                    "arm": run_id.rsplit("__", 1)[1],
                    "K0": row["K0"], "rho": row["rho"],
                    "decision_sequence": row["decision_sequence"],
                    "parent_interval": row["interval_id"],
                    "gamma_L": row["gamma_L"], "gamma_U": row["gamma_U"],
                    "infeasible_side": "left" if left_infeasible else "right",
                    "infeasible_child_id": infeasible_id,
                    "feasible_child_id": feasible_id,
                    "feasible_child_bound": row["right_child_bound"]
                    if left_infeasible else row["left_child_bound"],
                    "current_c6_action": row["selected_action"],
                    "infeasible_sibling_materialized": row["selected_action"] == "split",
                    "binary_split_count_incremented": row["selected_action"] == "split",
                    "feasible_model_already_built": True,
                    "potential_contraction_model_reuse": True,
                    "later_feasible_descendant_decisions": descendants,
                    "later_feasible_child_lp_rows": related_lp,
                    "source_ledger": ledger.relative_to(ROOT).as_posix(),
                    "source_ledger_sha256": common.sha256(ledger),
                })
    finite_rows.sort(key=lambda row: (
        row["stage"], row["instance"], row["arm"], row["decision_sequence"]))
    common.write_csv(OUT / "adaptive_mass_score_census.csv", finite_rows)
    common.write_csv(OUT / "infeasible_child_event_census.csv", one_child_rows)

    primary = primary_states(finite_rows)
    harmful = [primary["H1_k4_major_critical"]["S_AM"],
               primary["H2_k1_major_root"]["S_AM"]]
    useful = [primary["B1_k1_moderate_root"]["S_AM"],
              primary["B2_k1_high_root"]["S_AM"]]
    h_max, b_min = max(harmful), min(useful)
    if not h_max < b_min:
        raise RuntimeError("primary adaptive-mass states unexpectedly nonseparable")
    midpoint = (h_max + b_min) / 2.0
    if not h_max < common.TAU <= b_min:
        raise RuntimeError("frozen concise tau is outside admissible interval")

    replay = []
    for row in finite_rows:
        strict = min(row["left_child_bound"], row["right_child_bound"]) > \
            row["parent_bound"] + CERT
        action = "exact-close" if not strict else (
            "split" if row["S_AM"] + row["score_tolerance"] >= common.TAU
            else "native-target")
        replay.append({**row, "frozen_tau": common.TAU,
                       "round47_replay_action": action,
                       "action_differs_from_round46": action != row["round46_action"]})
    common.write_csv(OUT / "adaptive_mass_action_replay.csv", replay)

    tau_record = {
        "schema": "round47-tau-freeze-v1", "tau": common.TAU,
        "selection_case": "separable_deterministic_midpoint",
        "tau_007_inside_interval": h_max < 0.07 <= b_min,
        "unrounded_midpoint": midpoint,
        "rounding_rule": "concise decimal strictly inside admissible interval",
        "H_max": h_max, "B_min": b_min,
        "strict_lower_bound": h_max, "inclusive_upper_bound": b_min,
        "frozen_before_candidate_runtime": True,
        "common_for_K1_K4_AM_AMC": True,
        "primary_scores": {label: value["S_AM"]
                           for label, value in primary.items()},
    }
    common.write_json(OUT / "tau_admissible_interval.json", {
        "schema": "round47-tau-admissible-interval-v1",
        "separable": True, "H_max": h_max, "B_min": b_min,
        "admissible": f"{h_max:.17g} < tau <= {b_min:.17g}",
        "tau_007_admissible": False,
        "deterministic_midpoint": midpoint,
    })
    common.write_json(OUT / "tau_freeze.json", tau_record)

    h1 = primary["H1_k4_major_critical"]
    counterpart_path = R46_RUNS / (
        "stage4_1200s__round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
        "__K4-r050") / "c6_split_decision_ledger.csv"
    counterpart = common.csv_rows(counterpart_path)[2]
    matching = (
        counterpart["interval_id"] == h1["interval_id"] and
        counterpart["parent_id"] == h1["parent_id"] and
        int(counterpart["depth"]) == h1["depth"] and
        all(abs(float(counterpart[field]) - float(h1[field])) <= 1e-15
            for field in ("gamma_L", "gamma_U", "parent_bound",
                          "left_child_bound", "right_child_bound",
                          "verified_incumbent")))
    if not matching or counterpart["selected_action"] != "native-target":
        raise RuntimeError("K4 major critical-state replay mismatch")
    common.write_json(OUT / "k4_major_critical_state.json", {
        "schema": "round47-k4-major-critical-state-v1",
        **h1,
        "rho001_action": h1["round46_action"],
        "rho050_action": counterpart["selected_action"],
        "rho050_source_ledger": counterpart_path.relative_to(ROOT).as_posix(),
        "rho050_source_ledger_sha256": common.sha256(counterpart_path),
        "common_parent_state_exact_match": matching,
        "predecision_context": {
            "prior_decisions": ["L0 exact-close", "L1 exact-close"],
            "initial_K4_intervals": ["L0", "L1", "L2", "L3"],
            "controlling_interval": "L2",
            "coverage_state_source": (
                "Round46 interval_tree_events.csv and interval_coverage_ledger.csv"),
        },
    })
    return {"finite_rows": len(finite_rows),
            "one_child_events": len(one_child_rows), **tau_record}


def round46_historical_rows(instances: set[str]) -> list[dict[str, Any]]:
    tables = [("stage5_1800s_results.csv", 3),
              ("stage4_1200s_results.csv", 2),
              ("stage3_300s_results.csv", 1)]
    wanted = {"P-GRB", "K4-r001", "K4-r050", "K1-r015"}
    selected: dict[tuple[str, str], tuple[int, dict[str, str], Path]] = {}
    for name, priority in tables:
        path = R46 / name
        for row in common.csv_rows(path):
            key = (row["instance"], row["arm"])
            if row["instance"] not in instances or row["arm"] not in wanted:
                continue
            if key not in selected or priority > selected[key][0]:
                selected[key] = (priority, row, path)
    output = []
    for (_, _), (_, row, table) in sorted(selected.items()):
        run_dir = R46_RUNS / row["run_id"]
        result_path = run_dir / "result.json"
        output.append({
            "instance": row["instance"], "algorithm": row["arm"],
            "source_round": 46,
            "source_path": result_path.relative_to(ROOT).as_posix(),
            "source_commit": R46_SOURCE_COMMIT, "source_tree": R46_SOURCE_TREE,
            "evidence_commit": LOCAL_R46_HEAD, "evidence_tree": LOCAL_R46_TREE,
            "artifact_sha256": common.sha256(result_path),
            "input_sha256": common.load_json(run_dir / "command.json")["instance_sha256"],
            "executable_sha256": row["executable_sha256"],
            "solver_version": "Gurobi 13.0.2 build v13.0.2rc1",
            "machine": "WIN-3NO58RVQ4VC", "process_cap_seconds": row["process_cap_seconds"],
            "work": row["work"], "time_seconds": row["time_seconds"],
            "certificate": row["certificate"], "lower_bound": row["lower_bound"],
            "verified_upper_bound": row["verified_upper_bound"], "gap": row["relative_gap"],
            "gi_300": row.get("gi_300", ""), "gi_1200": row.get("gi_1200", ""),
            "gi_1800": row.get("gi_1800", ""),
            "comparison_timing": "historical_same_machine_solver_context",
            "source_table": table.relative_to(ROOT).as_posix(),
        })
    return output


def round45_historical_rows(instances: set[str]) -> list[dict[str, Any]]:
    matrix_path = R45 / "full_run_matrix_results.csv"
    matrix = common.csv_rows(matrix_path)
    horizon_path = R45 / "common_horizon_complex_results.csv"
    horizon = common.csv_rows(horizon_path)
    gi: dict[tuple[str, str, str], str] = {
        (row["instance"], row["arm"], row["horizon_seconds"]):
            row["normalized_gap_integral"] for row in horizon}
    candidates: dict[tuple[str, str], tuple[int, dict[str, str]]] = {}
    for row in matrix:
        if row["instance"] not in instances or row["arm"] not in \
                {"gamma-veto", "no-adaptive"}:
            continue
        priority = 3 if row["row_id"].startswith("rerun19") else (
            2 if row["row_id"].startswith("complex") else 1)
        key = (row["instance"], row["arm"])
        if key not in candidates or priority > candidates[key][0]:
            candidates[key] = (priority, row)
    output = []
    matrix_hash = common.sha256(matrix_path)
    for (_, _), (_, row) in sorted(candidates.items()):
        output.append({
            "instance": row["instance"], "algorithm": row["arm"],
            "source_round": 45,
            "source_path": (matrix_path.relative_to(ROOT).as_posix() +
                            "#row_id=" + row["row_id"]),
            "source_commit": R45_COMMIT, "source_tree": R45_TREE,
            "evidence_commit": R45_COMMIT, "evidence_tree": R45_TREE,
            "artifact_sha256": matrix_hash, "input_sha256": row["input_sha256"],
            "executable_sha256": "d0b17662a6021cf2cc3c7b4c66868bf76c3d11e268f0b63afc71a7a77e7e88f4",
            "solver_version": "Gurobi 13.0.2 build v13.0.2rc1",
            "machine": "WIN-3NO58RVQ4VC", "process_cap_seconds": row["process_cap_seconds"],
            "work": row["work"], "time_seconds": row["seconds"],
            "certificate": row["strict_certificate"], "lower_bound": row["lower_bound"],
            "verified_upper_bound": row["verified_upper_bound"], "gap": row["relative_gap"],
            "gi_300": gi.get((row["instance"], row["arm"], "300"), ""),
            "gi_1200": gi.get((row["instance"], row["arm"], "1200"), ""),
            "gi_1800": "",
            "comparison_timing": "historical_same_machine_solver_longer_cap",
            "source_table": matrix_path.relative_to(ROOT).as_posix(),
        })
    return output


def write_stage0(census: dict[str, Any]) -> None:
    r46_dataset = common.load_json(R46 / "dataset_freeze.json")["instances"]
    wanted = set(common.DEVELOPMENT) | set(common.STAGE5)
    instances = [row for row in r46_dataset if row["instance"] in wanted]
    if len(instances) != 17:
        raise RuntimeError(f"expected 17 frozen instances, got {len(instances)}")
    common.write_json(OUT / "dataset_freeze.json", {
        "schema": "round47-dataset-freeze-v1", "instances": instances,
        "development_instances": list(common.DEVELOPMENT),
        "stage5_instances": list(common.STAGE5), "new_instances_generated": False,
        "V50_allowed": False, "frozen_before_candidate_runtime": True,
    })
    common.write_json(OUT / "solver_contract.json", {
        "schema": "round47-solver-contract-v1", "Presolve": "Auto",
        "Seed": 0, "Threads": 1, "MIPGap": 0.0, "MIPGapAbs": 0.0,
        "certificate_tolerance": CERT, "maximum_process_cap_seconds": 1800,
        "midpoint_only": True, "runtime_outcomes_are_decision_inputs": False,
    })
    common.write_json(OUT / "forbidden_mechanisms.json", {
        "schema": "round47-forbidden-mechanisms-v1",
        "all_off": ["gamma-veto", "Gamma_sum", "Round43 D_R43",
                    "Round44 envelope-tail-repair", "frontier-d2 beyond C6",
                    "affine-envelope", "PMM", "FPMM", "non-midpoint",
                    "rank-1 CGLP", "frontier consolidation", "verified MIP starts",
                    "runtime classifiers", "size-dependent dispatch"],
        "extra_score_LP_MIP_CGLP_queries": 0,
    })
    common.write_json(OUT / "algorithm_arm_definition.json", {
        "schema": "round47-arm-definition-v1", "tau": common.TAU,
        "arms": [{"arm": arm, **common.ARM_DEFINITIONS[arm],
                  "midpoint": True, "identity": common.identity(arm)}
                 for arm in common.ARMS],
        "only_official_candidate_arms": list(common.ARMS),
    })
    common.write_json(OUT / "score_definition.json", {
        "schema": "round47-adaptive-mass-score-v1",
        "G_p": "max(U-B_p, epsilon_cert)",
        "g_j_raw": "(B_j-B_p)/G_p", "g_j": "clip(g_j_raw,0,1)",
        "eta": "min(g_L,g_R)", "mu": "(g_L+g_R)/2",
        "S_AM": "eta*mu", "rho_I": "min(1,tau/max(mu,epsilon_mass))",
        "epsilon_cert": CERT, "epsilon_mass": MASS_EPS,
        "score_tolerance": (
            "min(1,max(epsilon_cert,32*machine_epsilon*bound_scale)/G_p"
            "+32*machine_epsilon)"),
        "additional_solve_count": 0,
    })
    common.write_json(OUT / "tau_selection_protocol.json", {
        "schema": "round47-tau-selection-protocol-v1",
        "primary_harmful": ["H1_k4_major_critical", "H2_k1_major_root"],
        "primary_useful": ["B1_k1_moderate_root", "B2_k1_high_root"],
        "separable_rule": "use 0.07 iff strictly inside; otherwise concise midpoint",
        "nonseparable_order": ["retain K4 major", "retain K1 major",
                               "split K1 moderate", "split K1 high",
                               "maximize minimum margin"],
        "retuning_after_runtime": False,
    })
    common.write_json(OUT / "promotion_gates.json", {
        "schema": "round47-promotion-gates-v1",
        "study_scope": "screening_and_confirmation_not_paper_validation",
        "k4": ["major repair", "strong control", "V20 competitiveness",
               "no aggregate GI loss", "no extra LP", "zero false certificates"],
        "k1": ["major repair", "P-GRB strong-control advantage",
               "V20 advantage", "moderate retained", "same tau"],
        "contraction": "measurable resource reduction without proof loss",
        "default_replacement_automatic": False,
    })
    common.write_text(OUT / "research_contract.md", """# Round 47 research contract

Round 47 studies exactly four default-off arms: K4-AM, K4-AMC, K1-AM, and
K1-AMC. The midpoint is fixed. One frozen tau is shared by all arms. AM uses
only the two child LP outcomes already computed by original C6. AMC differs
only at strict one-child LP-infeasibility events. No baseline matrix, V50,
gamma-veto, envelope, PMM/FPMM, extra score solve, or runtime dispatch is
permitted. This is screening and confirmation, not paper validation.
""")
    common.write_text(OUT / "source_of_truth.md", f"""# Round 47 source of truth

- Detailed local Round 46 base: `{LOCAL_R46_HEAD}` / `{LOCAL_R46_TREE}`.
- Remote Round 46 PR head: `{REMOTE_R46_HEAD}` / `{REMOTE_R46_TREE}`.
- Round 46 official source: `{R46_SOURCE_COMMIT}` / `{R46_SOURCE_TREE}`.
- Round 45 corrected evidence: `{R45_COMMIT}` / `{R45_TREE}`.
- Frozen tau: `{common.TAU}`.
- Candidate evidence root: `results/gf_c6_adaptive_mass_contraction_round47/`.
- Historical rows are references only and are never copied into Round 47 runs.
""")

    historical = round46_historical_rows(wanted) + round45_historical_rows(wanted)
    historical.sort(key=lambda row: (row["instance"], row["source_round"],
                                     row["algorithm"]))
    common.write_csv(OUT / "historical_baseline_reference_manifest.csv", historical)

    protected = []
    for name in [
        "results/gf_compact_bc_round/handling_convention_test/handling_convention.json",
        "results/gf_compact_bc_timeprofile_round/progress_traces/"
        "exact_moderate_seed3301_1200s_static300.progress.csv",
        "results/gf_compact_bc_timeprofile_round/raw/"
        "exact_moderate_seed3301_1200s_static300.json",
    ]:
        path = ROOT / name
        protected.append({"path": name, "sha256": common.sha256(path)})
    status = subprocess.check_output(
        ["git", "status", "--porcelain=v1"], cwd=ROOT, text=True).splitlines()
    common.write_json(OUT / "official_start_record.json", {
        "schema": "round47-official-start-record-v1", "round_id": 47,
        "branch": git("branch", "--show-current"), "starting_head": git("rev-parse", "HEAD"),
        "starting_tree": git("rev-parse", "HEAD^{tree}"),
        "local_round46_head": LOCAL_R46_HEAD, "local_round46_tree": LOCAL_R46_TREE,
        "remote_round46_head": REMOTE_R46_HEAD, "remote_round46_tree": REMOTE_R46_TREE,
        "pr97": {"state": "OPEN", "draft": True,
                 "url": "https://github.com/yifanXovo/TailoredExact/pull/97",
                 "modified": False},
        "compiler": "g++.exe (Rev2, Built by MSYS2 project) 14.2.0",
        "cmake": "3.30.5-msvc23", "gurobi": "13.0.2 build v13.0.2rc1 win64",
        "machine": platform.node(), "working_tree_status_at_freeze": status,
        "protected_tracked_files": protected,
        "candidate_run_files_present": any(common.RUNS.glob("*")) if common.RUNS.exists() else False,
        "frozen_before_candidate_runtime": True,
    })

    common.write_text(OUT / "existing_infeasible_child_path_audit.md", """# Existing infeasible-child path audit

The Round 46 C6 path is mathematically exact but is not operationally a
single-child contraction. It constructs and solves both midpoint child LP
models, calls `splitLeafAtomically` with two persistent children, increments
the binary split counter, then marks a strict-infeasible child empty and
discards its retained backend model. The feasible child model is already
available and retained. Therefore AMC requires a new atomic one-child
replacement with explicit infeasible-half certificate metadata; duplicate
no-op code is not appropriate.
""")
    common.write_text(OUT / "mathematical_adaptive_mass_gate.md", """# Adaptive residual-mass gate

For finite complete child LP bounds, `G_p=max(U-B_p,epsilon_cert)`, clipped
gains are `g_j=clip((B_j-B_p)/G_p,0,1)`, `eta=min(g_L,g_R)`, and
`mu=(g_L+g_R)/2`. The score is `S_AM=eta*mu`. Equivalently,
`rho_I=min(1,tau/max(mu,epsilon_mass))` and the split tests
`S_AM>=tau` and `eta>=rho_I` agree up to the documented score tolerance.
The gate changes only split timing: below tau the existing native parent
target is `min(B_L,B_R)`, and without strict improvement exact parent closure
is retained. It launches no additional solve and is a structural proof-mass
gate, not a runtime predictor.
""")
    common.write_text(OUT / "mathematical_single_child_contraction.md", """# Exact single-child contraction

If exactly one complete midpoint child LP is strictly infeasible, LP
infeasibility proves its MIP feasible set empty. The parent feasible set thus
equals the feasible sibling's set. AMC atomically replaces the parent by only
that sibling, records the eliminated half and strict status, preserves the
midpoint endpoint convention, inherits `max(B_p,B_feasible)`, and reuses the
already-built feasible model. Numerical, interrupted, ambiguous, or missing
statuses never contract. If both children are strictly infeasible, the parent
is closed through the exact infeasibility path.
""")
    common.write_text(OUT / "exactness_and_termination_note.md", """# Exactness and termination

AM changes neither root coverage nor feasible sets; split, native-target, and
exact-close remain existing valid C6 alternatives. AMC removes only an LP-
proven-empty half and records this exclusion in certificate-aware coverage
metadata. Active endpoints remain gap-free relative to the feasible domain.
Inherited bounds are monotone, the global minimum remains valid, and each
transition either closes, strengthens, splits, or strictly contracts a finite
interval. The existing finite-tree and terminal-MIP termination argument and
zero-gap certificate gate therefore remain unchanged. Neither AM nor AMC adds
an LP, MIP, CGLP, or parametric query.
""")

    stage0_names = [
        "research_contract.md", "source_of_truth.md", "solver_contract.json",
        "forbidden_mechanisms.json", "dataset_freeze.json",
        "algorithm_arm_definition.json", "score_definition.json",
        "tau_selection_protocol.json", "historical_baseline_reference_manifest.csv",
        "promotion_gates.json", "official_start_record.json",
    ]
    files = [{"path": name, "sha256": common.sha256(OUT / name),
              "size_bytes": (OUT / name).stat().st_size} for name in stage0_names]
    common.write_json(OUT / "stage0_freeze_manifest.json", {
        "schema": "round47-stage0-freeze-manifest-v1",
        "frozen_before_candidate_runtime": True,
        "candidate_run_files_present": False, "files": files,
        "score_census_rows": census["finite_rows"],
        "one_child_infeasibility_events": census["one_child_events"],
        "tau": common.TAU,
    })


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if common.RUNS.exists() and any(common.RUNS.iterdir()):
        raise SystemExit("Round 47 candidate runtime exists before Stage 0 freeze")
    census = write_census()
    write_stage0(census)
    print(json.dumps({
        "stage0_complete": True, "tau": common.TAU,
        "finite_score_rows": census["finite_rows"],
        "one_child_events": census["one_child_events"],
        "H_max": census["H_max"], "B_min": census["B_min"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
