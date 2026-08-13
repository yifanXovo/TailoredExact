#!/usr/bin/env python3
"""Fail-closed final audit for the compact Round 38 evidence package."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import round38_experiment_common as common


STAGES = ("smoke", "diagnostic", "confirmation")
EXPECTED = {
    "smoke": (12, 6, 180),
    "diagnostic": (24, 12, 480),
    "confirmation": (6, 3, 900),
}
PROTECTED = {
    Path("results/gf_compact_bc_round/handling_convention_test/"
         "handling_convention.json"):
        "9a5cd06f8a4163cfcbb57147a0b21c0a5e4aec91973ab93faa921baa0553f35b",
    Path("results/gf_compact_bc_timeprofile_round/progress_traces/"
         "exact_moderate_seed3301_1200s_static300.progress.csv"):
        "4af39fe81263cd8c15ca457f4d4f6473a959630b6ab68a9280bc0a0e0a6b8acb",
    Path("results/gf_compact_bc_timeprofile_round/raw/"
         "exact_moderate_seed3301_1200s_static300.json"):
        "b11e84e2442c0c7b5ac5aa638b44945de28426fe31753083bff13ad401644202",
}
SENSITIVE = (
    b"grb_license_file", b"gurobi.lic", b"licenseid",
    b"wlsaccessid", b"wlssecret", b"tokenserver",
)


def boolean(value: Any) -> bool:
    return value is True or str(value).lower() in {"1", "true", "yes"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    checks = 0
    for relative, checksum in PROTECTED.items():
        path = common.ROOT / relative
        require(path.is_file(), f"protected file missing: {relative}")
        require(common.sha256(path) == checksum,
                f"protected file changed: {relative}")
        checks += 1
    pre = common.load_json(
        common.OUT / "baseline_equivalence_pre_mechanism_audit.json"
    )
    post = common.load_json(
        common.OUT / "baseline_equivalence_post_implementation_audit.json"
    )
    require(pre["passed"] and pre["comparison_count"] == 18,
            "pre-mechanism equivalence failed")
    require(post["passed"] and post["comparison_count"] == 18,
            "post-implementation equivalence failed")
    checks += 2
    total_runs = 0
    total_pairs = 0
    total_children = 0
    total_completions = 0
    total_refinements = 0
    for stage in STAGES:
        expected_runs, expected_pairs, cap = EXPECTED[stage]
        matrix = common.OUT / f"round38_{stage}_matrix.csv"
        freeze_path = common.OUT / f"round38_{stage}_freeze.json"
        runs = common.OUT / f"{stage}_runs"
        audit = common.csv_rows(common.OUT / f"{stage}_run_audit.csv")
        pairs = common.csv_rows(common.OUT / f"{stage}_pair_analysis.csv")
        analysis = common.load_json(common.OUT / f"{stage}_analysis.json")
        freeze = common.load_json(freeze_path)
        require(common.sha256(matrix) == freeze["matrix_sha256"],
                f"{stage} matrix hash mismatch")
        require(common.sha256(common.PANEL) == freeze["panel_sha256"],
                f"{stage} panel hash mismatch")
        require(freeze["executable_sha256"] ==
                "701d6cae4bdb9639ddc8a9046618ec97cdb5687ee534c808efb3497948b4077d",
                f"{stage} executable identity mismatch")
        require(len(audit) == expected_runs and len(pairs) == expected_pairs,
                f"{stage} run/pair cardinality mismatch")
        require(all(boolean(row["all_gates_pass"]) for row in audit),
                f"{stage} run gate failed")
        require(analysis["false_certificate_count"] == 0 and
                analysis["certificate_regression_count"] == 0,
                f"{stage} certificate audit failed")
        matrix_rows = common.csv_rows(matrix)
        require(all(int(row["process_cap_seconds"]) == cap and
                    int(row["watchdog_seconds"]) == cap + 90
                    for row in matrix_rows),
                f"{stage} time contract mismatch")
        require(all(int(row["process_cap_seconds"]) < 3600
                    for row in matrix_rows),
                f"{stage} violates long-run ban")
        for row in matrix_rows:
            directory = runs / row["run_id"]
            marker_path = directory / "completion_marker.json"
            manifest_path = directory / "artifact_manifest.csv"
            require(marker_path.is_file() and manifest_path.is_file(),
                    f"{stage} completion missing: {row['run_id']}")
            marker = common.load_json(marker_path)
            require(marker.get("completed") is True and
                    marker.get("completion_marker_atomic") is True,
                    f"{stage} non-atomic completion: {row['run_id']}")
            require(common.sha256(manifest_path) ==
                    marker["artifact_manifest_sha256"],
                    f"{stage} manifest hash mismatch: {row['run_id']}")
        total_runs += len(audit)
        total_pairs += len(pairs)
        total_children += analysis["pilot_child_evaluation_count"]
        total_completions += analysis["next_frontier_completion_count"]
        total_refinements += analysis["pilot_refinement_count"]
        checks += 8
    diagnostic_freeze = common.load_json(
        common.OUT / "round38_diagnostic_freeze.json"
    )
    smoke_freeze_sha = common.sha256(
        common.OUT / "round38_smoke_freeze.json"
    )
    require(diagnostic_freeze["smoke_freeze_sha256"] == smoke_freeze_sha,
            "smoke-to-diagnostic provenance chain mismatch")
    confirmation_freeze = common.load_json(
        common.OUT / "round38_confirmation_freeze.json"
    )
    require(confirmation_freeze["diagnostic_freeze_sha256"] == common.sha256(
        common.OUT / "round38_diagnostic_freeze.json"
    ), "diagnostic-to-confirmation freeze chain mismatch")
    require(confirmation_freeze["diagnostic_analysis_sha256"] == common.sha256(
        common.OUT / "diagnostic_analysis.json"
    ), "diagnostic-to-confirmation analysis chain mismatch")
    checks += 3
    exact = common.load_json(common.OUT / "exactness_audit.json")
    decision = common.load_json(common.OUT / "final_decision.json")
    require(total_runs == 42 and total_pairs == 21,
            "official total cardinality mismatch")
    require(total_children == 19 and total_completions == 0 and
            total_refinements == 0,
            "mechanism exposure totals mismatch")
    require(exact["all_run_gates_pass"] and
            exact["false_certificate_count"] == 0 and
            exact["certificate_regression_count"] == 0,
            "final exactness summary mismatch")
    require(decision["decision"] ==
            "do_not_promote_g2a_retain_c6_hga_full" and
            decision["stable_general_improvement_found"] is False,
            "final decision mismatch")
    require(decision["validated_mainline"] == {
        "K": 4,
        "policy": "C6-HGA-FULL",
        "rho": 0.01,
        "round38_frontier_policy_default": "off",
    }, "validated mainline mismatch")
    require(len(common.csv_rows(common.OUT / "per_pair_results.csv")) == 21,
            "per-pair compact evidence incomplete")
    require(len(common.csv_rows(common.OUT / "local_raw_manifest.csv")) == 42,
            "local raw manifest incomplete")
    invalid = common.load_json(
        common.OUT / "invalidated_attempt_summary.json"
    )
    require(not invalid["completion_marker_present"] and
            not invalid["official_evidence"] and
            invalid["replacement_completion_marker_present"],
            "invalidated attempt quarantine mismatch")
    checks += 8
    # Scan only committed-eligible Round 38 evidence/scripts, never raw logs.
    for path in sorted(common.OUT.iterdir()):
        if not path.is_file():
            continue
        data = path.read_bytes().lower()
        require(not any(marker in data for marker in SENSITIVE),
                f"sensitive marker in compact evidence: {path.name}")
    print(json.dumps({
        "schema": "round38-final-audit-v1",
        "checks_passed": checks,
        "official_runs": total_runs,
        "official_pairs": total_pairs,
        "child_evaluations": total_children,
        "next_frontier_completions": total_completions,
        "accepted_refinements": total_refinements,
        "false_certificates": exact["false_certificate_count"],
        "certificate_regressions": exact[
            "certificate_regression_count"
        ],
        "decision": decision["decision"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
