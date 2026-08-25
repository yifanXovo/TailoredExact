#!/usr/bin/env python3
"""Create the pre-runtime Round 48 contract, registry, panel, and provenance freeze."""

from __future__ import annotations

import json
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

import round48_common as common


ROOT, OUT = common.ROOT, common.OUT
R47 = ROOT / "results" / "gf_c6_adaptive_mass_contraction_round47"
R39 = ROOT / "results" / "gf_small_hard_light_round39"
R47_SOURCE_COMMIT = "776a06eacd82153a6b19d78e18e10056dd22f481"
R47_SOURCE_TREE = "d27a40ab9c9f14175d00caef37ab04579bc6fec4"
R47_REMOTE_COMMIT = "f4e7b8b1675b6816dd3f7b9c22fae275f618491b"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def result_value(data: dict[str, Any], *names: str, default: Any = "") -> Any:
    for name in names:
        value = data.get(name)
        if value is not None and value != "":
            return value
    return default


def append_round47_rows(rows: list[dict[str, Any]]) -> None:
    runs = R47 / "runs"
    for instance in common.STAGE5:
        for algorithm in ("K1-AM", "K4-AMC"):
            choices = sorted(runs.glob(f"stage*_s__{instance}__{algorithm}"))
            # Glob spelling uses stageN_CAPs; sort by parsed cap explicitly.
            choices = sorted(runs.glob(f"stage*__{instance}__{algorithm}"),
                             key=lambda p: int(p.name.split("_", 2)[1][:-1]))
            if not choices:
                continue
            run_dir = choices[-1]
            result_path = run_dir / "result.json"
            data = common.load_json(result_path)
            cap = int(run_dir.name.split("_", 2)[1][:-1])
            input_path = ROOT / common.INSTANCE_PATHS[instance]
            rows.append({
                "instance": instance, "algorithm": algorithm,
                "source_round": 47,
                "source_path": result_path.relative_to(ROOT).as_posix(),
                "source_commit": R47_SOURCE_COMMIT,
                "source_tree": R47_SOURCE_TREE,
                "evidence_commit": R47_SOURCE_COMMIT,
                "evidence_tree": R47_SOURCE_TREE,
                "artifact_sha256": common.sha256(result_path),
                "input_sha256": common.sha256(input_path),
                "executable_sha256":
                    "541c496881c7a0f79ffaf50cbdf4acc3bdf106dd86031990c0e6cf56c3deaa16",
                "solver_version": result_value(data, "gurobi_version", default="13.0.2"),
                "machine": "WIN-3NO58RVQ4VC", "process_cap_seconds": cap,
                "work": result_value(data, "external_gini_tree_work", "gurobi_work"),
                "time_seconds": result_value(data, "final_process_wall_time_seconds",
                                               "actual_runtime_seconds"),
                "certificate": bool(data.get("strict_certified_original_problem")),
                "lower_bound": data.get("lower_bound", ""),
                "verified_upper_bound": result_value(data, "upper_bound", "objective"),
                "gap": data.get("gap", ""), "gi_300": "", "gi_1200": "",
                "gi_1800": "", "split_count": data.get(
                    "external_gini_tree_split_count", ""),
                "native_target_count": data.get(
                    "external_gini_tree_native_target_optimize_count", ""),
                "lp_model_count": data.get("external_gini_tree_model_count", ""),
                "comparison_timing": "historical_same_machine_solver",
                "source_table": "round47 result.json",
            })


def append_additional_pgrb(rows: list[dict[str, Any]]) -> None:
    frozen = common.load_json(R39 / "round39_frozen_manifest.json")
    exe_hash = frozen["gurobi_executable_sha256"]
    source_commit = frozen["solver_source_commit"]
    source_tree = subprocess.check_output(
        ["git", "show", "-s", "--format=%T", source_commit], cwd=ROOT,
        text=True).strip()
    for instance in common.ADDITIONAL_CONFIRMATION:
        candidates = list((R39 / "runs").glob(f"primary__{instance}__p_grb/result.json"))
        if len(candidates) != 1:
            raise RuntimeError(f"historical P-GRB match count for {instance}: {len(candidates)}")
        result_path = candidates[0]
        data = common.load_json(result_path)
        input_path = ROOT / common.INSTANCE_PATHS[instance]
        if not data.get("strict_certified_original_problem"):
            raise RuntimeError(f"historical P-GRB is not exact for {instance}")
        rows.append({
            "instance": instance, "algorithm": "P-GRB", "source_round": 39,
            "source_path": result_path.relative_to(ROOT).as_posix(),
            "source_commit": source_commit, "source_tree": source_tree,
            "evidence_commit": source_commit, "evidence_tree": source_tree,
            "artifact_sha256": common.sha256(result_path),
            "input_sha256": common.sha256(input_path),
            "executable_sha256": exe_hash,
            "solver_version": data.get("gurobi_version", "13.0.2"),
            "machine": frozen["environment"]["hostname"],
            "process_cap_seconds": frozen["engineering_process_cap_seconds"],
            "work": data.get("gurobi_work", ""),
            "time_seconds": result_value(data, "final_process_wall_time_seconds",
                                           "actual_runtime_seconds"),
            "certificate": True, "lower_bound": data.get("lower_bound", ""),
            "verified_upper_bound": result_value(data, "upper_bound", "objective"),
            "gap": data.get("gap", 0.0), "gi_300": "", "gi_1200": "",
            "gi_1800": "", "split_count": 0, "native_target_count": 0,
            "lp_model_count": data.get("gurobi_model_count", ""),
            "comparison_timing": "historical_exact_same_machine_solver",
            "source_table": "round39 audited P-GRB result.json",
        })


def historical_manifest() -> list[dict[str, Any]]:
    wanted = {"P-GRB", "K1-r015", "K4-r001", "gamma-veto"}
    rows = [row for row in common.csv_rows(
        R47 / "historical_baseline_reference_manifest.csv")
        if row["instance"] in common.STAGE5 and row["algorithm"] in wanted]
    for row in rows:
        row.setdefault("split_count", "")
        row.setdefault("native_target_count", "")
        row.setdefault("lp_model_count", "")
    append_round47_rows(rows)
    existing = {(row["instance"], row["algorithm"]) for row in rows}
    if any((instance, "P-GRB") not in existing
           for instance in common.ADDITIONAL_CONFIRMATION):
        append_additional_pgrb(rows)
    rows.sort(key=lambda row: (row["instance"], row["algorithm"],
                               int(float(row["process_cap_seconds"] or 0))))
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    current_head = git("rev-parse", "HEAD")
    current_tree = git("rev-parse", "HEAD^{tree}")
    if current_head != R47_SOURCE_COMMIT or current_tree != R47_SOURCE_TREE:
        raise RuntimeError("Round 48 branch no longer points at verified Round 47 base")

    common.write_text(OUT / "research_contract.md", """# Round 48 research contract

K1-AMF is the only new algorithm: K0=1, midpoint, tau=0.07915, Round 47 K1-AM lifecycle, no contraction, and no extra solve. The formulation credit uses equal-weight contraction of every eligible non-Gini variable domain. The original C6 and historical K1-AM paths remain unchanged and default-off. Candidate process caps are at most 1800 seconds; V50 and broad baseline reruns are forbidden.
""")
    common.write_text(OUT / "source_of_truth.md", f"""# Source of truth

- Verified local Round 47 base: `{R47_SOURCE_COMMIT}` / `{R47_SOURCE_TREE}`.
- Verified PR 99 remote head: `{R47_REMOTE_COMMIT}` with the same tree.
- Round 48 branch: `codex/round48-k1-amf-formulation-rescue`.
- Evidence root: `results/gf_k1_amf_formulation_rescue_round48/`.
- Historical evidence is referenced by immutable path and hash; it is not copied.
- Candidate truth is the frozen official executable plus per-run commands, ledgers, markers, and hashes.
""")
    common.write_json(OUT / "solver_contract.json", {
        "schema": "round48-solver-contract-v1", "backend": "Gurobi",
        "version": "13.0.2 build v13.0.2rc1", "Presolve": "Auto",
        "Seed": 0, "Threads": 1, "MIPGap": 0.0, "MIPGapAbs": 0.0,
        "certificate_tolerance": common.CERTIFICATE_TOLERANCE,
        "max_process_cap_seconds": common.MAX_PROCESS_CAP,
        "same_complete_objective": True, "same_hga_full_incumbent": True,
        "same_external_tree_certificate_lifecycle": True,
    })
    forbidden = ["K4 initialization", "AMC", "single-child contraction",
        "gamma-veto", "Gamma_sum", "Round43", "Round44", "frontier-d2",
        "affine-envelope injection", "PMM", "FPMM", "non-midpoint",
        "rho cap", "fixed-rho fallback", "rank-1 CGLP", "verified MIP starts",
        "frontier consolidation", "model-chain inheritance changes",
        "new cuts", "solver tuning", "rho_I<=0.15", "family weights",
        "depth weights", "width weights", "instance dispatch"]
    common.write_json(OUT / "forbidden_mechanisms.json", {
        "schema": "round48-forbidden-mechanisms-v1", "all_off": True,
        "mechanisms": forbidden, "broad_baseline_rerun": False,
        "V50_allowed": False, "candidate_cap_above_1800_allowed": False,
    })
    formula = {
        "schema": "round48-amf-formula-v1", "K0": 1,
        "split_point": "midpoint", "tau": common.TAU,
        "weighting": "equal_per_eligible_model_variable",
        "parent_gap": "max(U-B_p,epsilon_cert)",
        "g_j": "clip((B_j-B_p)/G_p,0,1)", "eta": "min(g_L,g_R)",
        "mu": "(g_L+g_R)/2", "S_AM": "eta*mu",
        "c_v_j": "clip(1-(u_v_j-l_v_j)/(u_v_P-l_v_P),0,1)",
        "phi_j": "mean(c_v_j over V_P), or 0 for empty V_P",
        "gtilde_L": "g_L+phi_L*max(g_R-g_L,0)",
        "gtilde_R": "g_R+phi_R*max(g_L-g_R,0)",
        "eta_hat": "min(gtilde_L,gtilde_R)", "S_AMF": "mu*eta_hat",
        "decision": "split iff S_AMF+epsilon_score>=tau",
        "invalid_profile": "phi_L=phi_R=0 and exact AM fallback",
        "adjustable_parameters_introduced": 0,
    }
    formula["formula_sha256"] = common.stable_hash(formula)
    common.write_json(OUT / "amf_formula_freeze.json", formula)
    registry = {
        "schema": "round48-eligible-variable-registry-v1",
        "frozen_before_candidate_runtime": True,
        "selection_rule": "union of genuine variables named by non-diagnostic canonical interval rows or bounds whose coefficients, RHS, or bounds depend on gamma_L/gamma_U; finite effective parent and both-child bounds; parent width above certificate-derived tolerance; deduplicated; equal weight",
        "included_families": [
            {"family": "final_inventory", "pattern": "Y_[i]", "factory_source": "penalty_final_inventory_domain bounds"},
            {"family": "station_ratio", "pattern": "r_[i]", "factory_source": "direct/spread/centering interval rows"},
            {"family": "absolute_deviation", "pattern": "e_[i]", "factory_source": "estimator/penalty interval rows"},
            {"family": "pairwise_ratio_difference", "pattern": "h_[i]_[j]", "factory_source": "direct/spread/estimator interval rows"},
            {"family": "inventory_bit", "pattern": "bit_[i]_[b]", "factory_source": "interval-tight McCormick rows"},
            {"family": "gini_inventory_product", "pattern": "prod_[i]_[b]", "factory_source": "interval-tight McCormick rows", "not_gini_duplicate": "joint product G*bit, not an encoding of G alone"},
            {"family": "pickup_movement", "pattern": "p_[k]_[i]", "factory_source": "required-movement interval rows"},
            {"family": "drop_movement", "pattern": "d_[k]_[i]", "factory_source": "required-movement interval rows"},
            {"family": "ratio_penalty_product", "pattern": "W_SP", "factory_source": "sp-product interval factory domain/rows"},
        ],
        "always_excluded": [
            {"pattern": "G", "reason": "Gini split coordinate"},
            {"pattern": "segment_G_* or exact G aliases", "reason": "duplicate/auxiliary encoding of G alone"},
            {"pattern": "diagnostic-only variables", "reason": "factory scope diagnostic_excluded"},
        ],
        "inactive_not_eligible": ["W_GS", "T_SP_*", "Round43/44/45 variables"],
        "equal_family_weights": False, "equal_variable_weights": True,
        "post_outcome_family_selection_allowed": False,
    }
    registry["registry_sha256"] = common.stable_hash(registry)
    common.write_json(OUT / "eligible_variable_registry.json", registry)

    instances = []
    for instance in common.STAGE5:
        path = ROOT / common.INSTANCE_PATHS[instance]
        if not path.is_file():
            raise FileNotFoundError(path)
        panel = "mechanism" if instance in common.MECHANISM else (
            "existing_confirmation" if instance in common.EXISTING_CONFIRMATION
            else "additional_confirmation")
        instances.append({"instance": instance, "path": path.relative_to(ROOT).as_posix(),
                          "sha256": common.sha256(path), "panel": panel,
                          "role": common.ROLES[instance],
                          "formula_construction_use": instance in common.MECHANISM,
                          "additional_substitution": False})
    common.write_json(OUT / "dataset_freeze.json", {
        "schema": "round48-dataset-freeze-v1", "instances": instances,
        "mechanism_instances": list(common.MECHANISM),
        "existing_confirmation_instances": list(common.EXISTING_CONFIRMATION),
        "additional_confirmation_instances": list(common.ADDITIONAL_CONFIRMATION),
        "additional_instances_frozen_before_outcomes": True,
        "V50_allowed": False, "new_instances_generated": False,
    })
    common.write_json(OUT / "offline_census_protocol.json", {
        "schema": "round48-offline-census-protocol-v1",
        "states": ["H1", "H2", "H3", "B1", "B2", "B3", "B4", "U1",
                   "tight3102 exact common divergence states"],
        "primary_pass": ["H1 retain", "H2 retain", "B1 split", "B2 split",
                         "B3 split", "B4 split", "zero Gini-coordinate credit"],
        "no_retuning_after_census": True,
        "failure_policy": "implement exact frozen AMF; Stage3 eight diagnostic rows only; no Stage4/5; bounded structural negative",
    })
    common.write_json(OUT / "promotion_gates.json", {
        "schema": "round48-promotion-gates-v1", "offline_gate_mandatory": True,
        "major": "certificate and Work<=927.8016 with no material time regression",
        "strong": "certificate and >=35% Work reduction vs K1-AM or equal certificate-time improvement",
        "negative": "no harmful root split and no material Work regression",
        "v12_m2": "target >=25% Work reduction from 38.8087",
        "high_imbalance": "both certificates", "moderate3301": "gap<=0.025 or certificate",
        "tight3102": "certificate, or gap<=0.01 with substantial Work/GI improvement",
        "v20": ">=3/6 certificates, no fewer than K1-AM, P-GRB advantage",
        "additional": "zero correctness failures and no systematic/severe regression",
    })
    manifest = historical_manifest()
    common.write_csv(OUT / "historical_baseline_reference_manifest.csv", manifest)
    additional_pgrb = {row["instance"] for row in manifest if
                       row["instance"] in common.ADDITIONAL_CONFIRMATION and
                       row["algorithm"] == "P-GRB" and
                       str(row["certificate"]).lower() == "true"}
    if additional_pgrb != set(common.ADDITIONAL_CONFIRMATION):
        raise RuntimeError("additional historical P-GRB freeze incomplete")
    common.write_json(OUT / "official_start_record.json", {
        "schema": "round48-official-start-record-v1",
        "written_before_candidate_runtime": True,
        "unix_seconds": time.time(), "branch": git("branch", "--show-current"),
        "base_local_head": current_head, "base_local_tree": current_tree,
        "round47_remote_head": R47_REMOTE_COMMIT,
        "round47_remote_tree": R47_SOURCE_TREE,
        "local_remote_tree_equal": True, "compiler": "g++ 14.2.0",
        "cmake": "3.30.5-msvc23", "gurobi": "13.0.2 build v13.0.2rc1",
        "machine": platform.node(), "platform": platform.platform(),
        "historical_manifest_sha256": common.sha256(
            OUT / "historical_baseline_reference_manifest.csv"),
        "additional_pgrb_verified": sorted(additional_pgrb),
        "candidate_runtime_started": False,
    })
    names = ["research_contract.md", "source_of_truth.md", "solver_contract.json",
             "forbidden_mechanisms.json", "amf_formula_freeze.json",
             "eligible_variable_registry.json", "historical_baseline_reference_manifest.csv",
             "dataset_freeze.json", "offline_census_protocol.json",
             "promotion_gates.json", "official_start_record.json"]
    entries = [{"path": name, "sha256": common.sha256(OUT / name),
                "size_bytes": (OUT / name).stat().st_size} for name in names]
    common.write_json(OUT / "stage0_freeze_manifest.json", {
        "schema": "round48-stage0-freeze-manifest-v1",
        "frozen_before_candidate_runtime": True, "candidate_runtime_started": False,
        "K0": 1, "tau": common.TAU, "split_point": "midpoint",
        "equal_weighting": True, "Gini_coordinate_excluded": True,
        "rho_cap": False, "AMC": False, "model_chain_inheritance_changes": False,
        "max_process_cap_seconds": common.MAX_PROCESS_CAP,
        "files": entries, "aggregate_sha256": common.stable_hash(entries),
    })
    print(json.dumps({"stage0_complete": True, "files": len(entries) + 1,
                      "historical_rows": len(manifest),
                      "additional_pgrb_rows": len(additional_pgrb)}, indent=2))


if __name__ == "__main__":
    main()
