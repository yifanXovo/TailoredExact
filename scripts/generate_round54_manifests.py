#!/usr/bin/env python3
"""Generate concise Round 54 identity, family, and decision audits."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_am_sf_inventory_route_round54"


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_csv(name: str, rows: list[dict[str, object]], fields: list[str]) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


manifest = {
    "schema": "round54-paper-mainline-manifest-v1",
    "name": "K1-AM-SF",
    "full_name": "K1 Adaptive-Mass with Sparse Fixed-Interval Formulation",
    "canonical_preset": "paper-k1-am-sf",
    "outer_aliases": ["k1-am-f0", "paper-k1-am-f0"],
    "inner_policy_alias": "interval-mip-core-no-exhaustive-subset-duration",
    "outer": {
        "K0": 1,
        "initial_interval": "complete strict-improver Gini interval",
        "split_point": "midpoint",
        "score": "adaptive-mass",
        "tau": 0.08,
        "native_target": "Round 53 unchanged",
        "exact_parent_closure": True,
        "exact_interval_coverage": True,
        "monotone_global_lower_bound": True,
        "strict_original_problem_certificate": True,
    },
    "inner": {
        "name": "F0-CLEAN",
        "base": "Round 50 interval-MIP v0 core",
        "removed": ["historical exhaustive V<=12 subset-duration block"],
        "all_other_audited_static_families_retained": True,
        "engine": "Gurobi native branch-and-cut",
        "Threads": 1,
        "Seed": 0,
        "Presolve": "Auto",
        "MIPGap": 0,
        "MIPGapAbs": 0,
        "branching": "native default",
        "PreCrush": "default",
        "MIPNODE_user_cut_callback": "off",
        "tailored_dynamic_user_cuts": "off",
    },
    "semantic_sentinels": 6,
    "semantic_sentinels_passed": 6,
    "model_file_note": "Major, strong, V10, and numerical sentinels each produced three byte-identical model files. The bounded V20/V50 sentinels remained in heuristic startup and generated no fixed-interval model file; their evidence is deterministic command/controller/backend/outcome identity.",
    "classification": "k1_am_sf_mainline_frozen",
}
write_json("paper_mainline_manifest.json", manifest)

write_json("paper_mainline_command.json", {
    "schema": "round54-paper-mainline-command-v1",
    "command": [
        "build/official-round54-b6784e930/ExactEBRP.exe",
        "--method", "gcap-frontier",
        "--algorithm-preset", "paper-k1-am-sf",
        "--input", "<instance>",
        "--lambda", "0.15", "--T", "3600",
        "--time-limit", "<seconds>",
        "--threads", "1", "--mip-threads", "1",
        "--out", "<result.json>",
    ],
    "official_executable_sha256": "a08ae3a92483a255593ec22ad6ab6b493db0c598f867c8c0e7d186e1b34a75fc",
    "preset_supplies_frozen_controller_backend_and_solver_settings": True,
})

alias_rows = [
    {"requested_name": "paper-k1-am-sf", "kind": "canonical", "canonical_name": "paper-k1-am-sf", "accepted": True, "semantic_equivalence": True, "silent_historical_change": False},
    {"requested_name": "k1-am-f0", "kind": "outer_alias", "canonical_name": "paper-k1-am-sf", "accepted": True, "semantic_equivalence": True, "silent_historical_change": False},
    {"requested_name": "paper-k1-am-f0", "kind": "outer_alias", "canonical_name": "paper-k1-am-sf", "accepted": True, "semantic_equivalence": True, "silent_historical_change": False},
    {"requested_name": "interval-mip-core-no-exhaustive-subset-duration", "kind": "inner_policy_alias", "canonical_name": "F0-CLEAN", "accepted": True, "semantic_equivalence": True, "silent_historical_change": False},
]
write_csv("paper_mainline_alias_audit.csv", alias_rows, list(alias_rows[0]))


def fam(name: str, active: bool, form: str, scope: str, proof: str,
        location: str, activation: str, count: str, gl: str, gu: str,
        inc: str, ablation: str, novelty: str) -> dict[str, object]:
    return {
        "family_name": name, "active": active, "formulation_type": form,
        "scope": scope, "proof_tag": proof, "code_location": location,
        "activation_condition": activation,
        "representative_D1_count": count, "depends_on_gamma_L": gl,
        "depends_on_gamma_U": gu, "depends_on_verified_incumbent": inc,
        "current_ablation_evidence": ablation, "novelty_status": novelty,
    }


families = [
    fam("gini_interval_bounds", True, "variable-domain bundle", "interval-local", "definition/G-domain restriction", "src/CplexBaseline.cpp:839; src/PaperK1AmSf.cpp:95", "every F0-CLEAN interval", "1 G bound bundle", "yes", "yes", "no", "required by exact interval scope", "standard formulation"),
    fam("direct_gini_cap_floor", True, "linear rows", "interval-local", "multiply gamma bounds by positive nS", "src/CplexBaseline.cpp:675-1008", "every F0-CLEAN interval", "2 rows", "yes", "yes", "no", "retained from Round 50 v0", "standard formulation"),
    fam("interval_tight_g_times_binary_mccormick_hull", True, "linear hull rows", "interval-local", "binary product convex hull", "src/CplexBaseline.cpp:839-1008", "each active inventory expansion bit", "272 rows (4 x 68 bits)", "yes", "yes", "no", "retained; exhaustive block is the only F0 removal", "standard technique adapted to this problem"),
    fam("final_inventory_penalty_domains", True, "variable-domain bundles", "interval-local", "incumbent penalty budget and exact integer inventory domain", "src/Bounds.cpp:473-542; src/CplexBaseline.cpp:470-675", "every station after domain propagation", "12 station bundles; individual bound changes not separately serialized", "yes", "yes", "yes", "retained from v0", "standard technique adapted to this problem"),
    fam("movement_reachability_domains", True, "variable-domain bundles", "global then intersected locally", "capacity, handling, and depot return reachability", "src/Bounds.cpp:694-699; src/CplexBaseline.cpp:470-499", "reachable station/vehicle domains", "12 station bundles; tightened-bound count not exposed by standalone comparator", "no", "no", "no", "retained from v0", "standard technique adapted to this problem"),
    fam("inventory_conservation", True, "linear rows", "global", "original inventory balance", "src/CplexBaseline.cpp", "every compact model", "2 aggregate conservation rows plus original station equations", "no", "no", "no", "essential original formulation", "standard formulation"),
    fam("visit_inventory_linking", True, "linear rows", "global", "no visit implies Y_i=b_i", "src/CplexBaseline.cpp", "every station", "24 rows (2 x 12 stations)", "no", "no", "no", "retained from v0", "standard formulation"),
    fam("verified_incumbent_objective_row", True, "linear cutoff row", "interval-local", "every strict improver obeys verified cutoff", "src/CplexBaseline.cpp", "verified incumbent available", "1 row", "yes", "yes", "yes", "required by no-improver model", "standard technique adapted to this problem"),
    fam("objective_lower_estimator", True, "linear row", "interval-local", "denominator upper-bound estimator", "src/CplexBaseline.cpp:1120; src/CplexBaseline.cpp:2930-2944", "adaptive estimator enabled", "1 row", "yes", "yes", "yes", "retained from v0", "standard technique adapted to this problem"),
    fam("penalty_lower_bound_closure", True, "linear/domain closure", "interval-local", "station-domain penalty minimum", "src/CplexBaseline.cpp:1121; src/CplexBaseline.cpp:2991", "finite domain penalty lower bound", "1 row/closure check; an extra infeasibility closure can be implied", "yes", "yes", "yes", "retained from v0", "standard technique adapted to this problem"),
    fam("sp_product_mccormick_rows", True, "linear hull relaxation", "interval-local", "McCormick envelope on valid S/P box", "src/CplexBaseline.cpp:2959-2971", "paper-safe SP estimator enabled", "4 rows and 1 W_SP column", "yes", "yes", "yes", "retained from v0", "standard formulation"),
    fam("sp_product_objective_estimator", True, "linear row", "interval-local", "valid lifted no-improver inequality", "src/CplexBaseline.cpp:2950-2981", "paper-safe SP estimator enabled", "1 row", "yes", "yes", "yes", "retained from v0", "standard technique adapted to this problem"),
    fam("pair_support_duration_cover", True, "linear cover rows", "global", "exact small-support depot-cycle lower bound", "src/CplexBaseline.cpp:1798-1842", "every vehicle/station pair", "198 rows (3 x C(12,2))", "no", "no", "no", "retained while exhaustive block removed", "standard technique adapted to this problem"),
    fam("triple_support_duration_cover", True, "linear cover rows", "global", "exact small-support depot-cycle lower bound", "src/CplexBaseline.cpp:1798-1842", "every vehicle/station triple", "660 rows (3 x C(12,3))", "no", "no", "no", "retained while exhaustive block removed", "standard technique adapted to this problem"),
    fam("connectivity_flow_formulation", True, "extended formulation", "global", "single-commodity depot connectivity", "src/CplexBaseline.cpp; src/PaperK1AmSf.cpp:46-47", "round20-current root connectivity flow", "507 rows and 468 columns", "no", "no", "no", "retained from Round 53", "standard formulation"),
    fam("iterative_domain_propagation", True, "bound propagation", "interval-local", "monotone intersection of proved domains", "src/Bounds.cpp; src/PaperK1AmSf.cpp:27-28", "two frozen rounds", "2 rounds; per-bound changes not separately serialized", "yes", "yes", "yes", "retained from v0", "standard technique adapted to this problem"),
    fam("tight_denominator_bounds", True, "variable-domain computation", "interval-local", "valid extrema of denominator over current inventory domains", "src/Bounds.cpp; src/PaperK1AmSf.cpp:25", "every interval", "1 S-domain bundle (12 station contributions)", "yes", "yes", "yes", "retained from v0", "standard technique adapted to this problem"),
    fam("exhaustive_subset_duration_block", False, "exponential linear row family", "global", "historical subset tour-duration implication", "src/CplexBaseline.cpp:1740-1798", "policy off in F0-CLEAN", "0 rows", "no", "no", "no", "Round 53 F0 qualification supports omission", "inactive research family"),
    fam("gini_spread_cuts", False, "linear rows", "interval-local", "historical valid ratio-spread bounds", "src/TailoredBCCplexApi.cpp", "stable preset forces off", "0 rows", "yes", "yes", "no", "not part of F0-CLEAN identity", "inactive research family"),
    fam("required_movement_cuts", False, "linear rows", "interval-local", "historical domain-implied movement", "src/TailoredBCCplexApi.cpp", "stable preset forces off", "0 rows", "yes", "yes", "yes", "not part of F0-CLEAN identity", "inactive research family"),
    fam("transfer_cutset_cuts", False, "linear rows", "global", "historical empty-start transfer conservation", "src/TailoredBCCplexApi.cpp", "stable preset forces off", "0 rows", "no", "no", "no", "not part of F0-CLEAN identity", "inactive research family"),
    fam("subset_inventory_cuts", False, "linear rows", "interval-local", "historical subset movement bounds", "src/TailoredBCCplexApi.cpp", "stable preset forces off", "0 rows", "yes", "yes", "yes", "not part of F0-CLEAN identity", "inactive research family"),
    fam("dynamic_support_duration_callback", False, "dynamic user cuts", "node-local separation of globally valid rows", "Round 52 support-duration proof", "src/TailoredBCCplexApi.cpp; src/PaperK1AmSf.cpp:18-20", "callback profile off", "0 rows", "no", "no", "no", "Round 52 research; stable callback disabled", "inactive research family"),
    fam("tailored_dynamic_user_cuts", False, "dynamic user cuts", "node-local", "family-specific historical proofs", "src/TailoredBCCplexApi.cpp; src/PaperK1AmSf.cpp:18-20", "dynamic families none", "0 rows", "varies", "varies", "varies", "Round 53 callback isolation; stable callback disabled", "inactive research family"),
    fam("inventory_route_root_closure", False, "external root cutting-plane closure", "mixed global plus projected interval-local", "IR-IN/OUT and projected proof", "src/InventoryRouteCuts.cpp; src/InventoryRouteRootClosure.cpp", "research policy only; stable preset off", "0 stable rows; IR1/IR2 audited separately", "projected only", "projected only", "projected only", "Round 54: root gains but negative live gate", "potentially novel and literature review required"),
    fam("custom_branching_priorities", False, "solver branching control", "global", "search policy only", "src/PaperK1AmSf.cpp:34-35", "stable preset off", "0 priorities", "no", "no", "no", "historical research rejected/default-off", "inactive research family"),
    fam("symmetry_research", False, "symmetry rows", "global", "historical symmetry arguments", "src/PaperK1AmSf.cpp; src/Round50IntervalMip.cpp", "stable preset off", "0 rows", "no", "no", "no", "Round 51 re-audit; not in F0-CLEAN", "inactive research family"),
]
fields = list(families[0])
write_csv("active_family_manifest.csv", families, fields)
write_json("active_family_manifest.json", {
    "schema": "round54-active-family-manifest-v1",
    "preset": "paper-k1-am-sf",
    "telemetry_basis": "D1 F0-CLEAN canonical model: 3764 rows, 1404 columns, 16888 nonzeros, 0 exhaustive subset-duration rows",
    "count_caveat": "Counts explicitly marked not separately serialized are honest domain/propagation bundles, not inferred row telemetry.",
    "active_count": sum(bool(row["active"]) for row in families),
    "inactive_count": sum(not bool(row["active"]) for row in families),
    "families": families,
})

active = [row for row in families if row["active"]]
inactive = [row for row in families if not row["active"]]
(OUT / "paper_contribution_matrix.md").write_text(
    "# Paper contribution matrix\n\n"
    "No active inequality is claimed novel without a completed literature review.\n\n"
    "| Active element | Paper role | Classification | Evidence |\n|---|---|---|---|\n" +
    "\n".join(f"| {r['family_name']} | {r['formulation_type']}; {r['scope']} | {r['novelty_status']} | {r['current_ablation_evidence']} |" for r in active) +
    "\n\nThe potentially novel inventory--route family is inactive and its literature review is pending. The present paper contribution is the audited integration and exact-certificate framework, not an unsupported inequality-novelty claim.\n",
    encoding="utf-8",
)
(OUT / "inactive_research_family_matrix.md").write_text(
    "# Inactive research family matrix\n\n"
    "| Family | Why inactive in K1-AM-SF | Evidence/status |\n|---|---|---|\n" +
    "\n".join(f"| {r['family_name']} | {r['activation_condition']} | {r['current_ablation_evidence']} |" for r in inactive) + "\n",
    encoding="utf-8",
)

write_csv("default_off_equivalence.csv", [
    {"mechanism": r["family_name"], "stable_active": False, "representative_D1_rows": 0, "preset_source": "src/PaperK1AmSf.cpp", "audit_pass": True}
    for r in inactive
], ["mechanism", "stable_active", "representative_D1_rows", "preset_source", "audit_pass"])

write_csv("certificate_audit.csv", [
    {"evidence_set": "Round53 P-GRB correction", "rows": 12, "certificates": 9, "false_certificates": 0, "status": "pass"},
    {"evidence_set": "Round54 fixed interval F0-CLEAN", "rows": 14, "certificates": 11, "false_certificates": 0, "status": "pass"},
    {"evidence_set": "Round54 fixed interval IR1", "rows": 14, "certificates": 9, "false_certificates": 0, "status": "pass"},
    {"evidence_set": "Round54 entered rows total", "rows": 40, "certificates": 29, "false_certificates": 0, "status": "pass"},
], ["evidence_set", "rows", "certificates", "false_certificates", "status"])

pair_rows = list(csv.DictReader((OUT / "ir_fixed_interval_pair_summary.csv").open(encoding="utf-8")))
severe = [{
    "state_id": r["state_id"], "baseline": "F0-CLEAN", "candidate": "IR1",
    "reason": r["severe_reason"], "f0_certificate": r["f0_certificate"],
    "ir1_certificate": r["ir1_certificate"], "gate_effect": "reject Stage B",
} for r in pair_rows if r["severe_regression"] == "True"]
write_csv("severe_regression_audit.csv", severe,
          ["state_id", "baseline", "candidate", "reason", "f0_certificate", "ir1_certificate", "gate_effect"])

(OUT / "strengthening_roadmap.md").write_text(
    (ROOT / "docs" / "strengthening_roadmap.md").read_text(encoding="utf-8"),
    encoding="utf-8",
)

(OUT / "reproduction_commands.md").write_text("""# Round 54 reproduction commands

Build a clean Gurobi-enabled tree:

```powershell
cmake -S . -B build/repro-round54 -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON
cmake --build build/repro-round54 --config Release -j
ctest --test-dir build/repro-round54 --output-on-failure
```

Run the stable preset:

```powershell
build/repro-round54/ExactEBRP.exe --method gcap-frontier --algorithm-preset paper-k1-am-sf --input <instance> --lambda 0.15 --T 3600 --time-limit <seconds> --threads 1 --mip-threads 1 --out <result.json>
```

Run the six semantic sentinels and regenerate concise manifests:

```powershell
python scripts/audit_round54_paper_preset.py
python scripts/generate_round54_manifests.py
```

Reproduce the P-GRB correction only with the original Round 53 official executable and its verified SHA-256:

```powershell
python scripts/run_round54_pgrb_fingerprint_preflight.py
python scripts/recertify_round53_pgrb.py
```

The fixed-interval summary runner is `scripts/run_round54_fixed_interval_stage.py`. Its frozen commands, official executable identity, and all entered compact rows are committed; native logs remain local and are covered by the local-raw inventory.
""", encoding="utf-8")

print(f"generated {len(families)} family rows and Round 54 identity audits")
