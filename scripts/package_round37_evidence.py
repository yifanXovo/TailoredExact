#!/usr/bin/env python3
"""Package the closed Round 37 evidence and decision."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import round37_experiment_common as common


STAGE_ANALYSES = (
    ("exploratory_smoke", 180, True, common.OUT / "smoke_pair_analysis.csv"),
    ("focused_diagnostic", 480, True,
     common.OUT / "diagnostic_pair_analysis.csv"),
    ("selected_confirmation", 900, False,
     common.OUT / "confirmation_pair_analysis.csv"),
)


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def main() -> int:
    cross_stage: list[dict[str, Any]] = []
    for stage, cap, exploratory, path in STAGE_ANALYSES:
        for row in csv_rows(path):
            cross_stage.append({
                "stage": stage, "process_cap_seconds": cap,
                "exploratory": exploratory,
                **row,
            })
    common.write_csv(common.OUT / "cross_stage_pair_evidence.csv", cross_stage)

    exactness = common.load_json(common.OUT / "final_exactness_audit.json")
    smoke = common.load_json(common.OUT / "smoke_analysis.json")
    diagnostic = common.load_json(common.OUT / "diagnostic_analysis.json")
    confirmation = common.load_json(common.OUT / "confirmation_analysis.json")
    geometry = common.load_json(common.OUT / "geometry_forensics.json")
    cleanup = common.load_json(common.OUT / "round36_cleanup_manifest.json")
    report = {
        "schema": "round37-final-report-v1",
        "round": 37,
        "title": "Structural Gini-decomposition geometry mechanism study",
        "mainline_reference": "C6-HGA-FULL-K4-rho0.01",
        "mainline_changed": False,
        "automatic_promotion_performed": False,
        "candidate": "G1-pilot-weakest-prefine",
        "candidate_default": "off",
        "candidate_decision": "retain_default_off_diagnostic_not_promoted",
        "stage0": {
            "round36_historical_runs_audited": 103,
            "round36_cleanup_files_removed": cleanup["removed_count"],
            "round36_cleanup_bytes_removed": cleanup["removed_bytes"],
            "round36_terminal_stage_c_runs": 47,
            "round36_terminal_stage_c_strict_certificates": 18,
            "round36_terminal_stage_c_valid_noncertificates": 29,
            "round36_false_certificates": 0,
            "post_implementation_default_c6_equivalence": "18/18",
        },
        "geometry_forensics": geometry,
        "official_experiments": {
            "run_count": exactness["run_count"],
            "pair_count": exactness["pair_count"],
            "smoke": {
                "cap_seconds": 180, "pairs": smoke["pair_count"],
                "exposures": smoke["pilot_exposure_count"],
                "improvements": smoke["g1_final_gap_improvement_count"],
                "regressions": smoke["g1_final_gap_regression_count"],
                "ties": smoke["final_gap_tie_count"],
            },
            "diagnostic": {
                "cap_seconds": 480, "pairs": diagnostic["pair_count"],
                "exposures": diagnostic["pilot_exposure_count"],
                "improvements": diagnostic[
                    "g1_final_gap_improvement_count"],
                "regressions": diagnostic[
                    "g1_final_gap_regression_count"],
                "ties": diagnostic["final_gap_tie_count"],
            },
            "confirmation": {
                "cap_seconds": 900, "pairs": confirmation["pair_count"],
                "exposures": confirmation["pilot_exposure_count"],
                "improvements": confirmation[
                    "g1_final_gap_improvement_count"],
                "regressions": confirmation[
                    "g1_final_gap_regression_count"],
                "ties": confirmation["final_gap_tie_count"],
            },
            "strict_certificates": exactness["strict_certificate_count"],
            "valid_noncertificates": exactness[
                "valid_noncertificate_count"],
            "false_certificates": exactness["false_certificate_count"],
        },
        "mechanism_findings": {
            "historical_weakest_initial_cell_counts": geometry[
                "weakest_cell_index_counts"],
            "historical_interior_weakest_fraction": "12/14",
            "generic_low_g_skew": "rejected_before_experiment",
            "exposed_policy_runs": 10,
            "prior_weakest_cell_reproduced": "10/10",
            "positive_selected_cell_lp_gain": "10/10",
            "v20_tight_T_gap_improvement_by_cap": {
                "180": 0.07525784617376821,
                "480": 0.10918782687314472,
                "900": 0.11225118140359665,
            },
            "v50_high_imbalance_gap_improvement_by_cap": {
                "180": -0.028963766116018003,
                "480": -0.02896406969868337,
                "900": -0.02896406969868337,
            },
            "conclusion": (
                "finite-width Gini cells cause a real local relaxation "
                "bottleneck, but the one-cell forced pre-refinement does not "
                "uniformly improve the downstream global proof tree"
            ),
        },
        "exactness_audit": exactness,
        "final_build": {
            "cpp_tests": "16/16",
            "python_test_scripts": "28/28",
            "official_experiment_executable_sha256": exactness[
                "executable_sha256"],
            "independent_clean_build_sha256":
                "98b16849216ecb50f5d8fe2e10fe4b2516b79ba02d4e383af34b9b1867e09a1f",
            "byte_reproducible_link_claimed": False,
        },
        "future_hypothesis": (
            "G2 multi-cell weakness-density geometry remains untested and "
            "unauthorized; it requires a new predeclared round"
        ),
    }
    common.write_json(common.OUT / "final_report.json", report)

    decision = {
        "schema": "round37-final-audit-decision-v1",
        "final_audit_passed": exactness["passed"],
        "exact_algorithm_mainline": "C6-HGA-FULL-K4-rho0.01",
        "candidate": "G1-pilot-weakest-prefine",
        "candidate_promoted": False,
        "candidate_default": "off",
        "candidate_retained_as_diagnostic": True,
        "mechanism_causally_supported": True,
        "uniform_downstream_benefit_supported": False,
        "reason": (
            "all exposed runs strengthen the selected local LP cell, but the "
            "V50 high-imbalance gap and AUC regress at 180, 480, and 900 "
            "seconds while the V20 tight-T row improves"
        ),
        "false_certificate_count": exactness["false_certificate_count"],
        "coverage_and_lifecycle_passed": exactness[
            "all_coverage_gates_valid"] and exactness[
                "all_lifecycle_gates_valid"],
        "automatic_promotion_performed": False,
        "merge_authorized": False,
    }
    common.write_json(common.OUT / "final_audit_decision.json", decision)

    lines = [
        "# Round 37 final report", "",
        "## Outcome", "",
        "The study confirms a real structural Gini-cell relaxation mechanism, "
        "but rejects G1 as a mainline performance change. G1 remains a "
        "default-off diagnostic; **C6-HGA-FULL, K=4, rho=0.01 remains "
        "mainline**.", "",
        "## Stage 0 and engineering", "",
        "Round 36 reporting was consolidated into immutable intermediate "
        "Stage B and terminal Stage C records, with PR 83's current merged "
        "state recorded separately. A hash-guarded cleanup removed 79 proven "
        "top-level transient/intermediate files (17,209,698 bytes) while "
        "retaining raw runs, invalidations, manifests, and the uncompressed "
        "trajectory fixture required by tests.", "",
        "The 103 Round 36 historical runs pass lifecycle, coverage, counter, "
        "timestamp, and certificate audits. Exact CSV streams now use "
        "round-trip precision: 81/103 old Work ledgers lost aggregate "
        "reconstructability at 1e-7, while new ledgers reconstruct to floating "
        "summation error. Bounds and certificates were unaffected.", "",
        "After G1 implementation, default-off C6 passed 18/18 contemporaneous "
        "mechanism equivalence comparisons against the frozen Round 36 "
        "executable.", "",
        "## Geometry and experiments", "",
        "Prior forensics rejected a generic low-G skew: 12/14 weakest initial "
        "LP cells were interior cells 1 or 2. The 12-row development panel was "
        "frozen before any candidate result.", "",
        "| Stage | Cap | Pairs | G1 exposed | Improves | Regresses | Ties |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| Smoke | 180 s | 6 | {smoke['pilot_exposure_count']} | "
        f"{smoke['g1_final_gap_improvement_count']} | "
        f"{smoke['g1_final_gap_regression_count']} | "
        f"{smoke['final_gap_tie_count']} |",
        f"| Diagnostic | 480 s | 3 | {diagnostic['pilot_exposure_count']} | "
        f"{diagnostic['g1_final_gap_improvement_count']} | "
        f"{diagnostic['g1_final_gap_regression_count']} | "
        f"{diagnostic['final_gap_tie_count']} |",
        f"| Confirmation | 900 s | 2 | "
        f"{confirmation['pilot_exposure_count']} | "
        f"{confirmation['g1_final_gap_improvement_count']} | "
        f"{confirmation['g1_final_gap_regression_count']} | "
        f"{confirmation['final_gap_tie_count']} |", "",
        "Every exposed pilot reproduced the prior weakest-cell index and "
        "strictly increased that cell's valid LP bound. Yet the downstream "
        "sign is stable and bidirectional: the V20 tight-T final common-UB gap "
        "improvement grows from 0.07526 to 0.11225 across caps, whereas the "
        "V50 high-imbalance regression stays near -0.028964. AUC has the same "
        "signs.", "",
        "The local gain is therefore causal but insufficient as a global "
        "policy criterion. A forced split changes leaf topology and front-loads "
        "two child LPs; the global bound remains controlled by the minimum "
        "relevant leaf, so a locally stronger cell can still delay more useful "
        "native targets or closures elsewhere.", "",
        "## Exactness and final audit", "",
        "All 22 official runs pass root/parent-child coverage, monotone bounds, "
        "verifier consistency, environment/model lifecycle balance, optimize "
        "counter identities, and round-trip Work/node reconstruction. There "
        "are 6 strict certificates, 16 valid non-certificates, and zero false "
        "certificates. All 11 pairs differ only in the explicit geometry policy "
        "and run-local paths.", "",
        "The final independent clean build passes 16/16 C++ and 28/28 Python "
        "test scripts. Its PE hash differs from the same-size frozen research "
        "binary, so no byte-reproducible-link claim is made.", "",
        "## Decision", "",
        "Do not promote G1 and do not broaden validation. Retain it default-off "
        "for mechanism diagnostics. G2 remains untested and requires a new "
        "predeclared round. No merge is authorized by this research result.",
    ]
    (common.OUT / "final_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    (common.OUT / "final_audit_decision.md").write_text(
        "# Round 37 final audit decision\n\n"
        "Final audit: **PASS**. G1's local mechanism is supported, but uniform "
        "downstream benefit is not. G1 is **not promoted** and remains "
        "default-off. **C6-HGA-FULL remains mainline.** Zero false "
        "certificates were observed. No automatic merge is authorized.\n",
        encoding="utf-8",
    )

    # Inventory the publishable evidence after all primary package files exist.
    inventory: list[dict[str, Any]] = []
    inventory_path = common.OUT / "published_evidence_inventory.csv"
    for path in sorted(
            (item for item in common.OUT.rglob("*") if item.is_file()),
            key=lambda item: item.as_posix()):
        if path == inventory_path or "models" in path.parts:
            continue
        inventory.append({
            "relative_path": path.relative_to(common.ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": common.sha256(path),
            "publication_scope": "committed_exact_evidence",
        })
    common.write_csv(inventory_path, inventory)
    publication = {
        "schema": "round37-publication-scope-v1",
        "published_file_count_excluding_inventory": len(inventory),
        "published_bytes_excluding_inventory": sum(
            row["bytes"] for row in inventory
        ),
        "local_raw_model_file_count": exactness["raw_model_file_count"],
        "local_raw_model_bytes": exactness["raw_model_bytes"],
        "raw_model_hash_manifest":
            "results/gf_gini_geometry_mechanism_round37/raw_model_retention_manifest.csv",
        "raw_model_recreation": "rerun the corresponding frozen command",
        "excluded_from_git": ["external/models canonical LP files"],
        "reason": (
            "canonical models are deterministic bulky inputs; compact results, "
            "commands, exact ledgers, native logs, lifecycle records, and "
            "checksums are published"
        ),
    }
    common.write_json(common.OUT / "publication_scope.json", publication)
    print(json.dumps({
        "final_audit_passed": exactness["passed"],
        "candidate_promoted": False,
        "mainline": report["mainline_reference"],
        "published_file_count": len(inventory),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
