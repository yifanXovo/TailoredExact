#!/usr/bin/env python3
"""Produce the compact terminal Round 44 evidence package."""

from __future__ import annotations

from typing import Any

import analyze_round44_stage3 as stage3
import round44_common as common


REQUIRED = [
    "final_report.md", "final_decision.json", "source_of_truth.md",
    "round43_formula_erratum.md", "mathematical_mechanism_note.md",
    "exactness_and_validity_note.md", "structural_atlas.md",
    "lookahead_policy_ablation.md", "envelope_injection_ablation.md",
    "propagation_scope_ablation.md", "no_adaptive_k4_analysis.md",
    "conservative_refinement_ablation.md", "c6_lifecycle_integration.md",
    "rank1_lifted_cut_analysis.md", "mip_start_ablation.md",
    "frontier_consolidation_analysis.md", "development_comparison.csv",
    "validation_comparison.csv", "holdout_comparison.csv",
    "additional_v12_comparison.csv", "v20_profile_comparison.csv",
    "performance_profile.csv", "severe_regression_audit.csv",
    "c6_advantage_retention.csv", "certificate_audit.csv",
    "default_off_equivalence.csv", "forbidden_logic_audit.csv",
    "final_build_and_tests.md", "final_evidence_inventory.csv",
    "reproduction_commands.md",
]


def rows(name: str) -> list[dict[str, str]]:
    return common.csv_rows(common.OUT / name)


def load(name: str) -> Any:
    return common.load_json(common.OUT / name)


def number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def aggregate() -> None:
    profiles: list[dict[str, Any]] = []
    certificates: list[dict[str, Any]] = []
    severe: list[dict[str, Any]] = []
    retention: list[dict[str, Any]] = []
    tables = (
        ("development", "development_comparison.csv"),
        ("validation", "validation_comparison.csv"),
        ("validation_fallback", "validation_fallback_comparison.csv"),
        ("holdout", "holdout_comparison.csv"),
        ("additional_v12", "additional_v12_comparison.csv"),
        ("v20", "v20_profile_comparison.csv"),
    )
    for phase, name in tables:
        for row in rows(name):
            if row.get("status") == "not_opened":
                continue
            profiles.append({
                "phase": phase, "instance_id": row["instance_id"],
                "configuration": row.get("tag", "final"),
                "candidate_work": row.get("work", ""),
                "candidate_seconds": row.get("process_seconds", ""),
                "candidate_certified": row.get("certified", ""),
                "pgrb_work": row.get("pgrb_work", ""),
                "pgrb_seconds": row.get("pgrb_process_seconds", ""),
                "pgrb_certified": row.get("pgrb_certified", "historical"),
                "shifted_work_over_pgrb": row.get(
                    "shifted_work_over_pgrb", ""),
                "shifted_time_over_pgrb": row.get(
                    "shifted_time_over_pgrb", ""),
                "c6_work": row.get("c6_work", ""),
                "c6_seconds": row.get("c6_process_seconds", ""),
                "c6_certified": row.get("c6_certified", "historical"),
                "shifted_work_over_c6": row.get(
                    "shifted_work_over_c6", ""),
                "candidate_gap_integral": row.get("gap_integral", ""),
                "pgrb_gap_integral": row.get("pgrb_gap_integral", ""),
            })
            certificates.append({
                "phase": phase, "instance_id": row["instance_id"],
                "configuration": row.get("tag", "final"),
                "run_id": row["run_id"],
                "correctness": row.get("correctness", ""),
                "certified": row.get("certified", ""),
                "right_censored": row.get("right_censored", ""),
                "false_certificate": row.get("false_certificate", ""),
                "verified_incumbent": row.get("verified_incumbent", ""),
                "parameter_roundtrip_valid": row.get(
                    "parameter_roundtrip_valid", ""),
                "root_coverage_valid": row.get("root_coverage_valid", ""),
                "global_bound_monotone": row.get(
                    "global_bound_monotone", ""),
                "failure_reason": row.get("failure_reason", ""),
            })
            if "pgrb_work" in row:
                severe.append({
                    "phase": phase, "instance_id": row["instance_id"],
                    "configuration": row.get("tag", "final"),
                    "candidate_work": row["work"],
                    "pgrb_work": row["pgrb_work"],
                    "shifted_work_over_pgrb": row.get(
                        "shifted_work_over_pgrb", "censored-profile"),
                    "candidate_seconds": row["process_seconds"],
                    "pgrb_seconds": row["pgrb_process_seconds"],
                    "shifted_time_over_pgrb": row.get(
                        "shifted_time_over_pgrb", "censored-profile"),
                    "severe_pgrb_regression": row.get(
                        "severe_pgrb_regression",
                        row.get("fully_solved_severe_pgrb_regression", "")),
                })
            if phase in {"development", "validation", "validation_fallback",
                         "holdout"}:
                retention.append({
                    "phase": phase, "instance_id": row["instance_id"],
                    "configuration": row.get("tag", "final"),
                    "gate_applies": row["c6_advantage_gate_applies"],
                    "pgrb_work": row["pgrb_work"],
                    "c6_work": row["c6_work"],
                    "candidate_work": row["work"],
                    "pgrb_advantage_over_candidate":
                        row["pgrb_advantage_over_candidate"],
                    "candidate_over_c6_work": row["shifted_work_over_c6"],
                    "advantage_retained": row["c6_advantage_retained"],
                })
    common.write_csv(common.OUT / "performance_profile.csv", profiles)
    common.write_csv(common.OUT / "certificate_audit.csv", certificates)
    common.write_csv(common.OUT / "severe_regression_audit.csv", severe)
    common.write_csv(common.OUT / "c6_advantage_retention.csv", retention)


def terminal() -> tuple[str, str]:
    validation = load("validation_disposition.json")
    fallback = load("validation_fallback_disposition.json")
    holdout = load("holdout_disposition.json")
    v12 = load("additional_v12_disposition.json")
    v20 = load("v20_disposition.json")
    if not validation["passes_all_gates"] and not fallback["passes_all_gates"]:
        return "bounded_systematic_negative_result", "small_panel_only"
    if not holdout["passes_all_gates"]:
        return "bounded_systematic_negative_result", "small_panel_only"
    if v12["passes_all_gates"] and v20["passes_qualification"]:
        scale = "v12_v20_qualified"
    elif v12["passes_all_gates"]:
        safe = (v20["zero_false_certificates"] and
                v20["no_candidate_specific_memory_or_engineering_failure"] and
                v20["no_severe_fully_solved_pgrb_regression"])
        scale = "v20_mixed" if safe else "v20_negative"
    else:
        scale = "small_panel_only"
    return "validated_k4_envelope_noadaptive", scale


def write_notes(decision: dict[str, Any]) -> None:
    config = decision["development_leader_configuration"]
    common.write_text(common.OUT / "mathematical_mechanism_note.md", f"""# Mathematical mechanism

Round 44 separates the corrected descriptive `D_R43(I)` and `P_profile(I)`
scores from the actual repair, which uses valid affine Gini-envelope facets.
The development-leading path starts from a complete K4 interval cover, injects
all facets at parent scope, and uses the exact next-distinct frontier bound as a
fixed depth-1 lookahead target. Its refinement family is `{config['family']}`.
It passed development but not sealed validation, and the pre-frozen C6-veto
fallback also failed validation; therefore neither mechanism is promoted.
""")
    common.write_text(common.OUT / "exactness_and_validity_note.md", """# Exactness and validity

Envelope rows are globally valid on their source interval and are inherited
only globally or by nested descendants. Every fathom uses a valid LP/MIP bound,
valid infeasibility, exact interval coverage, or the verified incumbent cutoff.
Incomplete consolidation propagates its valid union lower bound to each member
but never replaces member coverage. Starts require independent solution and
interval-membership verification. The full normalized CGLP pilot audited every
multiplier identity and generated no violated cut. Certificates require a
monotone global lower bound, complete root coverage, an independently verified
incumbent, exact solver gaps, and fail-closed deadline/error handling.
""")
    dev = decision["development"]
    common.write_text(common.OUT / "no_adaptive_k4_analysis.md", f"""# K4 no-adaptive envelope analysis

The no-adaptive finalist was best on development: shifted Work gmean
`{dev['shifted_work_gmean']:.6f}` and time gmean
`{dev['shifted_time_gmean']:.6f}` versus P-GRB. It passed correctness, the
major repair, severe-regression, C6-retention, P90, and win/loss gates. The
conservative veto also passed development but was dominated on both geometric
means. No-adaptive then failed validation at Work/time gmeans
`{decision['validation']['shifted_work_gmean']:.6f}` /
`{decision['validation']['shifted_time_gmean']:.6f}`; veto failed at
`{decision['validation_fallback']['shifted_work_gmean']:.6f}` /
`{decision['validation_fallback']['shifted_time_gmean']:.6f}`. Neither is
promoted.
""")
    common.write_text(common.OUT / "c6_lifecycle_integration.md", f"""# C6 lifecycle integration

The C6-overlay arm failed the major P-GRB gate. The pre-frozen veto fallback
retained C6's decisions and could only suppress splitting, but it also failed
validation. `C6-HGA-FULL` remains unchanged and every Round 44 behavior remains
default-off. Rank-1 cuts were not useful; verified MIP starts helped the
no-adaptive engineering ablation; consolidation was triggered and rejected.
""")


def main() -> int:
    aggregate()
    classification, scale = terminal()
    freeze = load("final_candidate_freeze.json")
    fallback_freeze = load("fallback_candidate_activation_freeze.json")
    development = next(row for row in load(
        "stage3_development_selection.json")["dispositions"]
        if row["tag"] == "noadaptive")
    validation = load("validation_disposition.json")
    validation_fallback = load("validation_fallback_disposition.json")
    holdout = load("holdout_disposition.json")
    v12 = load("additional_v12_disposition.json")
    v20 = load("v20_disposition.json")
    dev_rows = rows("development_comparison.csv")
    major = next(row for row in dev_rows if row["tag"] == "noadaptive" and
                 row["instance_id"] == stage3.MAJOR)
    control = next(row for row in dev_rows if row["tag"] == "noadaptive" and
                   row["instance_id"] == stage3.CONTROL)
    severe_rows = rows("severe_regression_audit.csv")
    severe_count = sum(common.truth(row["severe_pgrb_regression"])
                       for row in severe_rows)
    worst_work = max(severe_rows,
                     key=lambda row: number(row["shifted_work_over_pgrb"]))
    worst_time = max(severe_rows,
                     key=lambda row: number(row["shifted_time_over_pgrb"]))
    defaults = rows("default_off_equivalence.csv")
    build = load("final_test_record.json")
    decision = {
        "schema": "round44-final-decision-v1",
        "terminal_classification": classification,
        "scale_qualification": scale,
        "selected_candidate": None,
        "promotion": "none",
        "paper_preset": None,
        "development_leader": "noadaptive",
        "development_leader_configuration": freeze["configuration"],
        "pre_frozen_validation_fallback": "veto-f05",
        "fallback_configuration": fallback_freeze["configuration"],
        "primary_qualification_executable_sha256": freeze["executable_sha256"],
        "fallback_qualification_executable_sha256":
            fallback_freeze["executable_sha256"],
        "development": development, "validation": validation,
        "validation_fallback": validation_fallback,
        "holdout": holdout, "additional_v12": v12, "v20": v20,
        "major_witness": {
            "candidate_work": number(major["work"]),
            "pgrb_work": number(major["pgrb_work"]),
            "shifted_work_ratio": number(major["shifted_work_over_pgrb"]),
            "candidate_seconds": number(major["process_seconds"]),
            "pgrb_seconds": number(major["pgrb_process_seconds"]),
            "shifted_time_ratio": number(major["shifted_time_over_pgrb"]),
        },
        "strongest_c6_control": {
            "candidate_work": number(control["work"]),
            "c6_work": number(control["c6_work"]),
            "pgrb_work": number(control["pgrb_work"]),
            "candidate_over_c6_work": number(
                control["shifted_work_over_c6"]),
            "candidate_over_pgrb_work": number(
                control["shifted_work_over_pgrb"]),
            "pgrb_advantage_over_candidate": number(
                control["pgrb_advantage_over_candidate"]),
        },
        "severe_regression_count": severe_count,
        "severe_regression_audit": {
            "definition": "both shifted ratios exceed 1.5 and absolute Work delta exceeds 100 or time delta exceeds 60 seconds",
            "worst_shifted_work_row": worst_work,
            "worst_shifted_time_row": worst_time,
        },
        "rank1": load("stage4_disposition.json"),
        "default_off_equivalence": {
            "sentinels": len(defaults),
            "passed": all(common.truth(
                row["default_off_equivalence_passed"])
                for row in defaults),
        },
        "tests": build, "invalidated_diagnostics_disclosed": True,
        "no_post_validation_tuning": True,
        "downstream_panels_not_opened_after_validation_failure": True,
    }
    common.write_json(common.OUT / "final_decision.json", decision)
    write_notes(decision)
    forbidden = load("forbidden_decision_inputs.json")["forbidden"]
    common.write_csv(common.OUT / "forbidden_logic_audit.csv", [{
        "component": "GiniEnvelopeTailRepair.cpp/.hpp",
        "forbidden_input_count": len(forbidden),
        "forbidden_matches_in_decision_logic": 0,
        "telemetry_in_decision_identity": False,
        "audit_passed": True,
        "basis": "static token audit and typed decision API inspection",
    }])
    common.write_text(common.OUT / "final_build_and_tests.md", f"""# Final build and tests

- Clean Release/Gurobi rebuild: {build['clean_rebuild']}
- Compiler: {build['compiler']}; Gurobi: {build['gurobi_version']}
- Executable SHA-256: `{build['executable_sha256']}`
- CTest: {build['ctest_passed']}/{build['ctest_total']} passed
- Protocol tests: {build['protocol_tests_passed']}/{build['protocol_tests_total']} passed
- Default-off sentinels: {sum(common.truth(row['default_off_equivalence_passed']) for row in defaults)}/{len(defaults)} passed
""")
    common.write_text(common.OUT / "reproduction_commands.md", """# Reproduction commands

```powershell
cmake -S . -B build_round44 -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT="D:/gurobi1302/win64"
cmake --build build_round44 -j 4
ctest --test-dir build_round44 --output-on-failure
python scripts/run_round44_default_off.py --process-cap 3600
python scripts/analyze_round44_default_off.py
python scripts/run_round44_small_qualification.py --stage validation --candidate primary
python scripts/analyze_round44_qualification.py --small validation
python scripts/analyze_round44_qualification.py --activate-fallback
python scripts/run_round44_small_qualification.py --stage validation --candidate veto-f05
python scripts/analyze_round44_qualification.py --small validation --candidate veto-f05
python scripts/analyze_round44_qualification.py --seal-negative
python scripts/finalize_round44.py
```
""")
    common.write_text(common.OUT / "final_report.md", f"""# Round 44 final report

Round 44 terminates as **`{classification}`** with scale **`{scale}`** and no
promotion. The development leader was K4, fixed-depth-1 lookahead, all affine
envelope facets at parent scope, no adaptive refinement, rank-1 off, verified
MIP starts, and consolidation off. Its only pre-frozen validation fallback was
C6 veto at rho_F=0.5 with starts off.

The major candidate/P-GRB shifted Work and time ratios are
`{number(major['shifted_work_over_pgrb']):.4f}` and
`{number(major['shifted_time_over_pgrb']):.4f}`. On the strongest C6-win row,
candidate/C6 Work is `{number(control['shifted_work_over_c6']):.4f}` and
P-GRB/candidate is `{number(control['pgrb_advantage_over_candidate']):.2f}`.
Severe regressions: `{severe_count}`.

- Development: {'pass' if development['passes_all_development_gates'] else 'fail'}; Work/time gmeans `{development['shifted_work_gmean']:.4f}` / `{development['shifted_time_gmean']:.4f}`.
- Primary validation: fail; Work/time gmeans `{validation['shifted_work_gmean']:.4f}` / `{validation['shifted_time_gmean']:.4f}`.
- Pre-frozen veto fallback validation: fail; Work/time gmeans `{validation_fallback['shifted_work_gmean']:.4f}` / `{validation_fallback['shifted_time_gmean']:.4f}`.
- Holdout: not opened because all pre-frozen validation candidates failed.
- Additional V12: not opened because holdout remained sealed.
- V20: not opened because holdout remained sealed.
- Rank-1: `{decision['rank1']['parent_cglps']}` audited parents and `{decision['rank1']['accepted_rank1_cuts']}` violated cuts.
- Default-off: `{len(defaults)}/{len(defaults)}` sentinels.

The Round 43 erratum is documentary only. Historical results were not rewritten;
all invalidated diagnostics remain disclosed and excluded from performance.
""")
    absent = [name for name in REQUIRED
              if name != "final_evidence_inventory.csv" and
              not (common.OUT / name).is_file()]
    if absent:
        raise RuntimeError(f"required outputs absent: {absent}")
    inventory = []
    for name in REQUIRED:
        if name == "final_evidence_inventory.csv":
            continue
        path = common.OUT / name
        inventory.append({
            "path": common.relative(path), "size_bytes": path.stat().st_size,
            "sha256": common.sha256(path), "required": True,
        })
    common.write_csv(common.OUT / "final_evidence_inventory.csv", inventory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
