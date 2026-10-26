#!/usr/bin/env python3
"""Create the pre-runtime Round 49 contract, panels, registry, and provenance freeze."""

from __future__ import annotations

import csv
import json
import platform
import re
import subprocess
import time
from collections import defaultdict
from pathlib import Path

import round49_common as common


ROOT, OUT = common.ROOT, common.OUT
R48 = ROOT / "results" / "gf_k1_amf_formulation_rescue_round48"
R48_BASE_HEAD = "fb94950bcdaa04486a3b6e05fb515c719589b96d"
R48_EVIDENCE_COMMIT = "88193d43781da035a8ec0b387e7e824ca8dae3f5"
R48_TREE = "a5ecc486db0fe4ad160b1bb56caec1229332c2a5"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read_dimensions(path: Path) -> tuple[int, int]:
    first = path.read_text(encoding="utf-8").splitlines()[0]
    match = re.fullmatch(r"\s*(\d+)\s+(\d+)\s+\[.*\]\s*", first)
    if not match:
        raise RuntimeError(f"cannot parse V/M from {path}")
    return int(match.group(1)), int(match.group(2))


def primitive_names(v: int, m: int) -> dict[str, list[str]]:
    families: dict[str, list[str]] = defaultdict(list)
    for k in range(m):
        for i in range(v + 1):
            for j in range(v + 1):
                if i != j:
                    families["routing_arc"].append(f"x_{k}_{i}_{j}")
        for i in range(1, v + 1):
            families["visit_selection"].append(f"z_{k}_{i}")
            families["operation_mode"].append(f"mode_{k}_{i}")
            families["pickup_quantity"].append(f"p_{k}_{i}")
            families["drop_quantity"].append(f"d_{k}_{i}")
            families["vehicle_load"].append(f"load_{k}_{i}")
    families["final_inventory"] = [f"Y_{i}" for i in range(1, v + 1)]
    return dict(families)


def build_registry(instances: list[dict]) -> dict:
    classes: dict[str, dict] = {}
    for row in instances:
        v, m = read_dimensions(ROOT / row["path"])
        key = f"V{v}_M{m}"
        if key not in classes:
            families = primitive_names(v, m)
            classes[key] = {
                "V": v,
                "M": m,
                "instances": [],
                "families": families,
                "family_counts": {name: len(values)
                                  for name, values in families.items()},
                "primitive_variable_count": sum(map(len, families.values())),
            }
        classes[key]["instances"].append(row["instance"])
    registry = {
        "schema": "round49-primitive-integer-variable-registry-v1",
        "frozen_before_offline_census": True,
        "semantic_source": "canonical CplexBaseline model-variable factory roles",
        "deduplicate_by": "canonical model-variable name within one model",
        "included_family_rules": [
            {"family": family, "prefix": prefix, "indices": indices,
             "type": kind, "semantic_role": role}
            for family, prefix, indices, kind, role in common.PRIMITIVE_FAMILIES
        ],
        "always_excluded": [
            {"patterns": ["bit_*"], "reason": "binary expansion of Y"},
            {"patterns": ["prod_*", "zprod_*", "seg_q_*", "W_SP"],
             "reason": "product/McCormick auxiliary"},
            {"patterns": ["seg_z_*", "seg_half_z_*"],
             "reason": "formulation selector auxiliary"},
            {"patterns": ["G", "seg_G_*"],
             "reason": "Gini coordinate or Gini-only alias"},
            {"patterns": ["r_*", "e_*", "h_*", "ord_*", "conn_*"],
             "reason": "continuous relaxation/ordering/connectivity auxiliary"},
            {"patterns": ["diagnostic_*"], "reason": "diagnostic-only"},
        ],
        "dimension_classes": classes,
        "post_outcome_selection_allowed": False,
    }
    registry["registry_sha256"] = common.stable_hash(registry)
    return registry


def source_branch(round_number: str) -> str:
    return {
        "45": "codex/round45-adaptive-timing-parametric-partition",
        "46": "codex/round46-c6-rho-k1-k4-screen",
        "47": "codex/round47-c6-adaptive-mass-contraction",
        "39": "historical-round39",
    }.get(str(round_number), f"historical-round{round_number}")


def historical_manifest(instances: list[dict]) -> list[dict]:
    input_hash = {row["instance"]: row["sha256"] for row in instances}
    rows: list[dict] = []
    for row in common.csv_rows(R48 / "historical_baseline_reference_manifest.csv"):
        copied = dict(row)
        copied["source_branch"] = source_branch(row["source_round"])
        copied["source_algorithm"] = row["algorithm"]
        if copied["algorithm"] == "K4-r001":
            copied["algorithm"] = "K4-C6"
            copied["algorithm_identity"] = "original K4-C6 (Round 46 K4-r001 label)"
        else:
            copied["algorithm_identity"] = copied["algorithm"]
        rows.append(copied)

    direct = common.csv_rows(R48 / "historical_direct_comparison.csv")
    for row in direct:
        if row.get("algorithm") != "K1-AMF":
            continue
        rows.append({
            "instance": row["instance"], "algorithm": "K1-AMF-v1",
            "algorithm_identity": "Round 48 bounded-negative K1-AMF-v1",
            "source_algorithm": "K1-AMF", "source_round": 48,
            "source_branch": "codex/round48-k1-amf-formulation-rescue",
            "source_path": row["source_path"],
            "source_commit": R48_EVIDENCE_COMMIT, "source_tree": R48_TREE,
            "evidence_commit": R48_EVIDENCE_COMMIT, "evidence_tree": R48_TREE,
            "artifact_sha256": row["artifact_sha256"],
            "input_sha256": input_hash[row["instance"]],
            "executable_sha256": row["executable_sha256"],
            "solver_version": "13.0.2", "machine": "WIN-3NO58RVQ4VC",
            "process_cap_seconds": row["process_cap_seconds"],
            "work": row["work"], "time_seconds": row["time_seconds"],
            "certificate": row["certificate"],
            "lower_bound": row["lower_bound"],
            "verified_upper_bound": row["verified_upper_bound"],
            "gap": row["gap"], "gi_300": row.get("gi_300", ""),
            "gi_1200": "", "gi_1800": "",
            "split_count": row.get("split_count", ""),
            "native_target_count": "", "lp_model_count": "",
            "comparison_timing": "historical_negative_ablation_context",
            "source_table": "Round 48 historical_direct_comparison.csv",
        })
    rows.sort(key=lambda row: (row["instance"], row["algorithm"],
                               float(row.get("process_cap_seconds") or 0)))
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    head = git("rev-parse", "HEAD")
    tree = git("show", "-s", "--format=%T", "HEAD")
    if head != R48_BASE_HEAD or tree != R48_TREE:
        raise RuntimeError("Round 49 no longer points at the verified Round 48 base")
    if git("branch", "--show-current") != "codex/round49-k1-lp-primal-dual-rescue":
        raise RuntimeError("unexpected Round 49 branch")

    instances = []
    for instance in common.STAGE5:
        path = ROOT / common.INSTANCE_PATHS[instance]
        if not path.is_file():
            raise FileNotFoundError(path)
        panel = ("mechanism" if instance in common.MECHANISM else
                 "existing_confirmation" if instance in common.EXISTING_CONFIRMATION
                 else "additional_confirmation")
        instances.append({
            "instance": instance, "path": path.relative_to(ROOT).as_posix(),
            "sha256": common.sha256(path), "panel": panel,
            "role": common.ROLES[instance],
            "offline_formula_construction_use": instance in common.MECHANISM,
            "additional_substitution": False,
        })

    common.write_text(OUT / "research_contract.md", """# Round 49 research contract

Round 49 studies only K1-AM-RC: K0=1, midpoint, the unchanged AM gate at tau=0.07915, and a parameter-free rescue derived from primal values, reduced costs, and effective domains already available from the parent/child LP solves. AM splits are never vetoed. Invalid or stale RC evidence falls back exactly to K1-AM. AMF-v1, root processing, extra score solves, K4 initialization, contraction, tuning, learned rules, and broad baseline reruns are forbidden. No process cap may exceed 1800 seconds.
""")
    common.write_text(OUT / "source_of_truth.md", f"""# Source of truth

- Published Round 48 base and PR 101 head: `{R48_BASE_HEAD}` / `{R48_TREE}`.
- Frozen Round 48 evidence commit: `{R48_EVIDENCE_COMMIT}` with the same tree.
- Round 49 branch: `codex/round49-k1-lp-primal-dual-rescue`.
- Evidence root: `results/gf_k1_lp_primal_dual_rescue_round49/`.
- Historical rows are immutable path/hash references; no full prior result tree is copied.
- Candidate truth will be the single frozen official executable plus compact ledgers, completion markers, artifact hashes, and commands.
""")
    common.write_json(OUT / "solver_contract.json", {
        "schema": "round49-solver-contract-v1", "backend": "Gurobi",
        "version": "13.0.2 build v13.0.2rc1", "Presolve": "Auto",
        "Seed": 0, "Threads": 1, "MIPGap": 0.0, "MIPGapAbs": 0.0,
        "certificate_tolerance": common.CERTIFICATE_TOLERANCE,
        "max_process_cap_seconds": common.MAX_PROCESS_CAP,
        "objective_sense": "minimize", "same_complete_objective": True,
        "same_hga_full_incumbent": True,
        "same_external_tree_certificate_lifecycle": True,
    })
    common.write_json(OUT / "forbidden_mechanisms.json", {
        "schema": "round49-forbidden-mechanisms-v1", "all_off": True,
        "mechanisms": ["K4 initialization", "AMF-v1", "AMC", "single-child contraction",
            "gamma-veto", "Gamma_sum", "Round43", "Round44", "frontier-d2",
            "PMM", "FPMM", "non-midpoint", "rho cap", "fixed-rho fallback",
            "MIP root-processing probe", "rank-1 CGLP", "verified MIP starts",
            "frontier consolidation", "model-chain inheritance changes", "new cuts",
            "solver tuning", "learned classifier", "family weights", "fitted coefficient",
            "depth/width/K/instance threshold", "new continuous rescue threshold"],
        "broad_baseline_rerun": False, "V50_allowed": False,
        "candidate_cap_above_1800_allowed": False,
    })
    common.write_json(OUT / "dataset_freeze.json", {
        "schema": "round49-dataset-freeze-v1", "instances": instances,
        "mechanism_instances": list(common.MECHANISM),
        "existing_confirmation_instances": list(common.EXISTING_CONFIRMATION),
        "additional_confirmation_instances": list(common.ADDITIONAL_CONFIRMATION),
        "additional_instances_frozen_before_outcomes": True,
        "V50_allowed": False, "new_instances_generated": False,
    })

    registry = build_registry(instances)
    common.write_json(OUT / "primitive_integer_variable_registry.json", registry)
    common.write_json(OUT / "primitive_integer_registry_protocol.json", {
        "schema": "round49-primitive-integer-registry-protocol-v1",
        "registry_file": "primitive_integer_variable_registry.json",
        "registry_sha256": common.sha256(OUT / "primitive_integer_variable_registry.json"),
        "selection_basis": "semantic original decision role from canonical model factory",
        "count_once_by_canonical_name": True,
        "required_families": [item[0] for item in common.PRIMITIVE_FAMILIES],
        "encoding_duplicates_and_auxiliaries_excluded": True,
        "post_outcome_revision_allowed_only_for_proven_semantic_error": True,
    })
    common.write_json(OUT / "reduced_cost_domain_protocol.json", {
        "schema": "round49-reduced-cost-domain-protocol-v1",
        "required_state_validity": ["optimal complete LP", "primal available",
            "reduced costs available", "minimization", "model fingerprint match",
            "incumbent/cutoff epoch match", "finite bounds", "registry mapping complete"],
        "strict_cutoff": "U_strict=U-epsilon_cert",
        "delta": "max(U_strict-L_q,0)",
        "integer_effective_domain": "[ceil(lb-epsilon_domain),floor(ub+epsilon_domain)]",
        "lower_bound_case": "if x is at lower bound and rc>epsilon_rc, upper step=floor((Delta+epsilon_domain)/rc)",
        "upper_bound_case": "if x is at upper bound and rc<-epsilon_rc, lower step=floor((Delta+epsilon_domain)/(-rc))",
        "otherwise": "retain effective integer domain",
        "rounding_policy": "outward/conservative; never exclude a possible strict improver",
        "epsilon_domain": "certificate tolerance plus 64 machine epsilons at state scale",
        "D": "mean((N_i^q-1)/max(N_i^base-1,1)) over nonfixed parent variables",
        "H": "sum(log(max(N_i^q,1)))/max(sum(log(max(N_i^base,1))),epsilon_log)",
        "disjointness": "exact empty intersection of nonempty left/right certified integer domains",
        "invalid_policy": "zero rescue and exact K1-AM fallback; no replacement solve",
        "applied_to_mip": False, "extra_live_solves": 0,
    })
    common.write_json(OUT / "allowed_rule_menu.json", {
        "schema": "round49-allowed-rule-menu-v1", "tau": common.TAU,
        "rules": [
            {"id": "D-RCD", "summary": "D", "separation": False},
            {"id": "D-RCDS", "summary": "D", "separation": True},
            {"id": "H-RCD", "summary": "H", "separation": False},
            {"id": "H-RCDS", "summary": "H", "separation": True},
        ],
        "RCD": "children nonworse than parent and strict mean improvement",
        "RCDS": "RCD or exact child-domain separation with neither child summary worse",
        "continuous_rescue_threshold": None, "post_stage3_new_formula_allowed": False,
    })
    common.write_json(OUT / "bounded_iteration_policy.json", {
        "schema": "round49-bounded-iteration-policy-v1",
        "max_offline_design_iterations": 2, "max_live_candidates": 2,
        "max_stage3_rule_revisions": 1,
        "offline_permitted_changes": ["D versus H", "RCD versus RCDS",
            "proven registry correction", "proven duplicate removal",
            "reduced-cost sign/rounding/stale-state bug correction"],
        "post_stage3_permitted_change": "switch only among frozen D/H and RCD/RCDS",
        "post_stage4_change_allowed": False, "confirmation_before_final_freeze": False,
    })
    common.write_json(OUT / "promotion_gates.json", {
        "schema": "round49-promotion-gates-v1",
        "offline_primary": ["H1 retain", "H2 retain", "B1 split", "T1 split",
            "B2 or U1 split", "B3 split preserved", "B4 split preserved",
            "zero new parameter", "all mandatory RC profiles valid"],
        "stage4_entry": ["zero correctness/certificate failure", "zero extra solve",
            "major not materially worse", "V10 root not rescued",
            "intended strong rescue", "B3/B4 preserved", "no severe P-GRB regression",
            "exactly one finalist frozen"],
        "stage5_entry": ["major repair preserved", "strong improved/correctly refined",
            "V10 preserved", "high imbalance trajectory preserved",
            "material improvement on strong/numerical/V12M2/tight3102", "no correctness failure"],
    })

    manifest = historical_manifest(instances)
    common.write_csv(OUT / "historical_baseline_reference_manifest.csv", manifest)
    additional_pgrb = {row["instance"] for row in manifest
                       if row["instance"] in common.ADDITIONAL_CONFIRMATION
                       and row["algorithm"] == "P-GRB"
                       and str(row["certificate"]).lower() == "true"}
    if additional_pgrb != set(common.ADDITIONAL_CONFIRMATION):
        raise RuntimeError("additional historical P-GRB freeze incomplete")
    common.write_json(OUT / "official_start_record.json", {
        "schema": "round49-official-start-record-v1",
        "written_before_new_diagnostic_or_candidate_runtime": True,
        "unix_seconds": time.time(), "branch": git("branch", "--show-current"),
        "base_local_head": head, "base_local_tree": tree,
        "round48_remote_pr": 101, "round48_remote_head": R48_BASE_HEAD,
        "round48_remote_tree": R48_TREE, "local_remote_tree_equal": True,
        "compiler": "g++ 14.2.0", "cmake": "3.30.5-msvc23",
        "gurobi": "13.0.2 build v13.0.2rc1", "machine": platform.node(),
        "platform": platform.platform(),
        "historical_manifest_sha256": common.sha256(
            OUT / "historical_baseline_reference_manifest.csv"),
        "primitive_registry_sha256": common.sha256(
            OUT / "primitive_integer_variable_registry.json"),
        "additional_pgrb_verified": sorted(additional_pgrb),
        "new_diagnostic_runtime_started": False, "candidate_runtime_started": False,
    })

    required = ["research_contract.md", "source_of_truth.md", "solver_contract.json",
        "forbidden_mechanisms.json", "dataset_freeze.json",
        "historical_baseline_reference_manifest.csv",
        "primitive_integer_registry_protocol.json", "reduced_cost_domain_protocol.json",
        "allowed_rule_menu.json", "bounded_iteration_policy.json", "promotion_gates.json",
        "official_start_record.json"]
    entries = [{"path": name, "sha256": common.sha256(OUT / name),
                "size_bytes": (OUT / name).stat().st_size} for name in required]
    registry_entry = {"path": "primitive_integer_variable_registry.json",
        "sha256": common.sha256(OUT / "primitive_integer_variable_registry.json"),
        "size_bytes": (OUT / "primitive_integer_variable_registry.json").stat().st_size}
    common.write_json(OUT / "stage0_freeze_manifest.json", {
        "schema": "round49-stage0-freeze-manifest-v1",
        "frozen_before_new_diagnostic_or_candidate_runtime": True,
        "candidate_runtime_started": False, "K0": 1, "tau": common.TAU,
        "split_point": "midpoint", "AMF_v1": False, "root_processing": False,
        "extra_live_score_solves": 0, "max_offline_iterations": 2,
        "max_stage3_rule_switches": 1, "max_process_cap_seconds": common.MAX_PROCESS_CAP,
        "required_files": entries, "additional_pre_census_registry": registry_entry,
        "aggregate_sha256": common.stable_hash(entries + [registry_entry]),
    })
    print(json.dumps({"stage0_complete": True, "required_files": len(entries) + 1,
        "additional_registry": True, "historical_rows": len(manifest),
        "additional_pgrb_rows": len(additional_pgrb)}, indent=2))


if __name__ == "__main__":
    main()
