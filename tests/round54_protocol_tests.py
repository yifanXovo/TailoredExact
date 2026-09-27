#!/usr/bin/env python3
"""Final compact-evidence protocol checks for Round 54."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_am_sf_inventory_route_round54"
REQUIRED = (
    "final_report.md", "final_decision.json", "source_of_truth.md",
    "stable_mainline_contract.json", "paper_mainline_manifest.json",
    "paper_mainline_semantic_equivalence.csv",
    "round53_pgrb_certificate_correction/round53_pgrb_certificate_erratum.md",
    "round53_pgrb_certificate_correction/round53_pgrb_recertification_results.csv",
    "active_family_manifest.csv", "paper_contribution_matrix.md",
    "documentation_consistency_audit.csv", "manuscript_algorithm_identity_audit.md",
    "manuscript_compile_status.md", "strengthening_roadmap.md",
    "inventory_route_cut_validity_proof.md", "inventory_route_separator_design.md",
    "inventory_route_root_census.csv", "inventory_route_bound_gain.csv",
    "inventory_route_offline_gate.json", "external_root_closure_ledger.csv",
    "root_closure_overhead_audit.csv", "inventory_route_iteration_history.md",
    "ir_fixed_interval_300s.csv", "ir_fixed_interval_1200s.csv",
    "ir_fixed_interval_confirmation.csv", "ir_fixed_interval_long.csv",
    "ir_fixed_interval_promotion_decision.json", "ir_k1_integration_1800s.csv",
    "ir_k1_integration_3600s.csv", "ir_k1_integration_decision.json",
    "round54_generalization_manifest.json", "round54_generalization_3600s.csv",
    "round54_v50_7200s.csv", "round54_generalization_comparison.csv",
    "certificate_audit.csv", "severe_regression_audit.csv",
    "default_off_equivalence.csv", "final_build_and_tests.md",
    "final_evidence_inventory.csv", "reproduction_commands.md",
    "compact_evidence_inventory.csv", "local_raw_evidence_inventory.csv",
    "evidence_storage_audit.md", "source_scope_audit.csv", "secret_license_scan.md",
)


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


checks = 0


def require(value: bool, label: str) -> None:
    global checks
    if not value:
        raise RuntimeError(label)
    checks += 1


require(all((OUT / name).is_file() for name in REQUIRED), "required reports")
decision = json.loads((OUT / "final_decision.json").read_text(encoding="utf-8"))
require(decision["completion_status"] == "round54_complete", "completion")
require(decision["evidence_classification"] == "round53_pgrb_recertified", "pgrb class")
require(decision["mainline_classification"] == "k1_am_sf_mainline_frozen", "mainline class")
require(decision["documentation_classification"] == "documentation_fully_aligned", "docs class")
require(decision["separator_classification"] == "inventory_route_separator_complete", "separator class")
require(decision["strengthening_classification"] == "bounded_negative_inventory_route_strengthening", "strengthening class")
require(decision["algorithm_classification"] == "k1_am_sf_stable_mainline", "algorithm class")
require(decision["scale_qualification"] == "generalization_panel_not_opened", "scale class")
require(not decision["mandatory_entered_stage_missing_rows"], "no missing entered rows")
require(len(rows("round53_pgrb_certificate_correction/round53_pgrb_recertification_results.csv")) == 12, "pgrb rows")
require(sum(r["corrected_strict_certificate"] == "True" for r in rows("round53_pgrb_certificate_correction/round53_pgrb_recertification_results.csv")) == 9, "pgrb certs")
require(all(r["expected_actual_fingerprint_match"] == "True" for r in rows("round53_pgrb_certificate_correction/round53_pgrb_recertification_results.csv")), "pgrb fingerprints")
require(len(rows("paper_mainline_semantic_equivalence.csv")) == 6, "semantic sentinel rows")
require(all(r["semantic_equivalence"] == "True" for r in rows("paper_mainline_semantic_equivalence.csv")), "semantic equivalence")
family = rows("active_family_manifest.csv")
require(sum(r["active"] == "True" for r in family) == 17, "active families")
require(sum(r["active"] == "False" for r in family) == 10, "inactive families")
root = rows("inventory_route_root_census.csv")
require(len(root) == 68 and {r["variant"] for r in root} == {"IR1", "IR2"}, "offline census")
require(all(r["closure_valid"] == "1" for r in root), "offline validity")
live = rows("ir_fixed_interval_300s.csv")
require(len(live) == 28 and all(r["engineering_valid"] == "True" for r in live), "stage A rows")
require(sum(r["certificate"] == "1" for r in live if r["arm"] == "F0-CLEAN") == 11, "F0 certificates")
require(sum(r["certificate"] == "1" for r in live if r["arm"] == "IR1") == 9, "IR1 certificates")
require(all(r["false_certificate"] == "False" for r in live), "zero false certificates")
require(len(rows("severe_regression_audit.csv")) == 2, "severe regressions")
require(len(rows("ir_fixed_interval_1200s.csv")) == 0, "stage B sealed")
require(len(rows("ir_fixed_interval_confirmation.csv")) == 0, "confirmation sealed")
require(len(rows("ir_fixed_interval_long.csv")) == 0, "long sealed")
require(len(rows("ir_k1_integration_1800s.csv")) == 0 and len(rows("ir_k1_integration_3600s.csv")) == 0, "K1 sealed")
require(len(rows("round54_generalization_3600s.csv")) == 0 and len(rows("round54_v50_7200s.csv")) == 0, "generalization sealed")
require(all(r["passed"] == "True" for r in rows("documentation_consistency_audit.csv")), "documentation audit")
require(all(r["result"] == "pass" for r in rows("source_scope_audit.csv")), "source scope")
inventory = rows("final_evidence_inventory.csv")
require(inventory and all(sha256(ROOT / r["path"]) == r["sha256"] for r in inventory), "evidence hashes")
local = rows("local_raw_evidence_inventory.csv")
require(local and all(sha256(ROOT / r["path"]) == r["sha256"] for r in local), "local raw hashes")
require(sha256(ROOT / "build/official-round54-b6784e930/Round54InventoryRouteExperiment.exe") == decision["official_executable_sha256"], "official executable")
require(sha256(ROOT / "build/official-round54-b6784e930/ExactEBRP.exe") == decision["paper_executable_sha256"], "paper executable")

print(f"Round54 protocol tests passed {checks} checks")
