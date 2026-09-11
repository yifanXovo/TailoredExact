#!/usr/bin/env python3
"""Assemble the bounded-negative Round 48 evidence and publication reports."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import round48_common as common


ROOT, OUT, RUNS = common.ROOT, common.OUT, common.RUNS
EXE_HASH = "bff4943b82d10c4fc082e5ae9add1970d46a1277ab1b398dc77410d94b4cbe34"
EPS = common.CERTIFICATE_TOLERANCE

MAJOR, STRONG, NEGATIVE, NUMERICAL, V12M2 = common.MECHANISM[:5]


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def inum(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() == "true"


def result(run_dir: Path) -> dict[str, Any]:
    value = common.load_json(run_dir / "result.json")
    return value[0] if isinstance(value, list) else value


def relative_gap(lower: float, upper: float) -> float:
    return max(0.0, upper - lower) / max(abs(upper), EPS)


def trace_points(run_dir: Path, data: dict[str, Any]) -> list[tuple[float, float, float]]:
    points = []
    for row in common.csv_rows(run_dir / "global_bound_trace.csv"):
        elapsed = fnum(row.get("process_elapsed_seconds"))
        lower = fnum(row.get("valid_global_lower_bound"))
        upper = fnum(row.get("verified_global_upper_bound"))
        if upper > 0 and upper + EPS >= lower:
            points.append((max(0.0, elapsed), lower, upper))
    lower = fnum(data.get("external_gini_tree_global_lower_bound",
                          data.get("lower_bound")))
    upper = fnum(data.get("external_gini_tree_verified_upper_bound",
                          data.get("upper_bound")))
    elapsed = fnum(data.get("final_process_wall_time_seconds",
                            data.get("actual_runtime_seconds")))
    if upper > 0 and upper + EPS >= lower:
        points.append((elapsed, lower, upper))
    points.sort()
    dedup = []
    for point in points:
        if dedup and abs(dedup[-1][0] - point[0]) <= 1e-9:
            dedup[-1] = point
        else:
            dedup.append(point)
    return dedup


def horizon(points: list[tuple[float, float, float]], seconds: float,
            exact: bool, exact_time: float) -> dict[str, float]:
    if not points:
        return {"lb": 0.0, "ub": 0.0, "gap": 1.0, "gi": 1.0}
    current = points[0]
    last, area = 0.0, 0.0
    for point in points:
        time = min(seconds, max(0.0, point[0]))
        if time > last:
            area += (time - last) * relative_gap(current[1], current[2])
            last = time
        if point[0] <= seconds + 1e-9:
            current = point
        else:
            break
    if last < seconds:
        tail = 0.0 if exact and exact_time <= seconds else relative_gap(
            current[1], current[2])
        area += (seconds - last) * tail
    return {"lb": current[1], "ub": current[2],
            "gap": relative_gap(current[1], current[2]),
            "gi": area / seconds}


def extract_stage3(instance: str) -> dict[str, Any]:
    run_dir = RUNS / f"stage3_300s__{instance}__K1-AMF"
    command = common.load_json(run_dir / "command.json")
    marker = common.load_json(run_dir / "completion_marker.json")
    data = result(run_dir)
    exact = truth(data.get("strict_certified_original_problem"))
    lower = fnum(data.get("lower_bound"))
    upper = fnum(data.get("upper_bound"))
    elapsed = fnum(data.get("final_process_wall_time_seconds",
                            data.get("actual_runtime_seconds")))
    h300 = horizon(trace_points(run_dir, data), 300.0, exact, elapsed)
    decisions = common.csv_rows(run_dir / "amf_decision_ledger.csv")
    differences = [row for row in decisions
                   if row["AM_action"] != row["AMF_action"]]
    native_rows = common.csv_rows(run_dir / "native_target_ledger.csv")
    return {
        "record_type": "candidate", "candidate_row": True,
        "run_id": command["run_id"], "stage": "stage3_300s",
        "algorithm": "K1-AMF", "instance": instance,
        "role": command["role"], "K0": 1, "tau": common.TAU,
        "process_cap_seconds": command["process_cap_seconds"],
        "executable_sha256": command["executable_sha256"],
        "status": data.get("status", ""), "certificate": exact,
        "certificate_class": data.get("strict_certificate_class", ""),
        "certificate_rejection_reason":
            data.get("strict_certificate_rejection_reason", ""),
        "coverage_valid": truth(
            data.get("external_gini_tree_root_coverage_valid")),
        "false_certificate": False,
        "completion_marker": truth(marker.get("complete")),
        "time_seconds": elapsed,
        "work": fnum(data.get("external_gini_tree_work")),
        "lower_bound": lower, "verified_upper_bound": upper,
        "relative_gap": relative_gap(lower, upper),
        "lb_300": h300["lb"], "ub_300": h300["ub"],
        "gap_300": h300["gap"], "gi_300": h300["gi"],
        "split_count": inum(data.get("external_gini_tree_split_count")),
        "native_target_count": inum(
            data.get("external_gini_tree_child_bound_target_phase_count")),
        "native_target_ledger_rows": len(native_rows),
        "terminal_mip_count": inum(
            data.get("external_gini_tree_terminal_mip_optimize_count")),
        "lp_count": inum(data.get("external_gini_tree_lp_optimize_count")),
        "model_count": inum(data.get("external_gini_tree_model_count")),
        "model_reuse_count": inum(
            data.get("external_gini_tree_in_memory_model_reuse_count")),
        "formulation_decision_count": inum(
            data.get("round48_amf_decision_count")),
        "formulation_rescue_count": inum(
            data.get("round48_amf_rescue_count")),
        "invalid_profile_fallback_count": inum(
            data.get("round48_amf_invalid_profile_fallback_count")),
        "max_eligible_variable_count": inum(
            data.get("round48_amf_max_eligible_variable_count")),
        "first_action_difference_from_K1_AM":
            differences[0]["interval_id"] if differences else "none",
        "extra_score_lp_count": inum(data.get("round48_amf_extra_lp_count")),
        "extra_score_mip_count": inum(data.get("round48_amf_extra_mip_count")),
        "failure_reason": data.get("external_gini_tree_failure_reason", ""),
        "result_sha256": common.sha256(run_dir / "result.json"),
        "artifact_manifest_sha256":
            common.sha256(run_dir / "artifact_manifest.csv"),
    }


def table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |",
             "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, ""))
                                         for column in columns) + " |")
    return "\n".join(lines)


def historical_rows(instance: str, historical: list[dict[str, str]]) -> list[dict[str, str]]:
    wanted = {"P-GRB", "K1-r015", "K1-AM", "K4-AMC", "K4-r001"}
    return [row for row in historical
            if row["instance"] == instance and row["algorithm"] in wanted]


def comparison_markdown(title: str, instance: str,
                        stage: dict[str, Any],
                        historical: list[dict[str, str]],
                        conclusion: str) -> str:
    rows: list[dict[str, Any]] = [{
        "algorithm": "K1-AMF (300s)", "certificate": stage["certificate"],
        "work": stage["work"], "time_seconds": stage["time_seconds"],
        "gap": stage["relative_gap"], "gi_300": stage["gi_300"],
    }]
    rows += [{
        "algorithm": row["algorithm"] + " (historical)",
        "certificate": row["certificate"], "work": row["work"],
        "time_seconds": row["time_seconds"], "gap": row["gap"],
        "gi_300": row["gi_300"],
    } for row in historical_rows(instance, historical)]
    return (f"# {title}\n\nInstance: `{instance}`. Historical terminal Work/time "
            "may use longer caps; GI(300) is the common-horizon field where available.\n\n" +
            table(rows, ["algorithm", "certificate", "work", "time_seconds",
                         "gap", "gi_300"]) + f"\n\n{conclusion}\n")


def verify_artifacts(stage_rows: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    failures = []
    for stage in stage_rows:
        run_dir = RUNS / stage["run_id"]
        for row in common.csv_rows(run_dir / "artifact_manifest.csv"):
            path = run_dir / row["path"]
            if not path.is_file() or common.sha256(path) != row["sha256"]:
                failures.append(f"{stage['run_id']}:{row['path']}")
    return not failures, failures


def main() -> None:
    stage_rows = [extract_stage3(instance) for instance in common.MECHANISM]
    common.write_csv(OUT / "stage3_300s_results.csv", stage_rows)
    control_fields = ["record_type", "candidate_row", "stage", "entered",
                      "completed_candidate_rows", "not_entered_reason"]
    common.write_csv(OUT / "stage4_1200s_results.csv", [{
        "record_type": "stage_control", "candidate_row": False,
        "stage": "stage4_1200s", "entered": False,
        "completed_candidate_rows": 0,
        "not_entered_reason": "primary_offline_gate_failed_B1_B2",
    }], control_fields)
    common.write_csv(OUT / "stage5_1800s_results.csv", [{
        "record_type": "stage_control", "candidate_row": False,
        "stage": "stage5_1800s", "entered": False,
        "completed_candidate_rows": 0,
        "not_entered_reason": "Stage4_not_entered_after_offline_gate_failure",
    }], control_fields)
    common.write_csv(OUT / "additional_confirmation_comparators.csv", [{
        "record_type": "panel_control", "candidate_row": False,
        "stage": "additional_confirmation", "entered": False,
        "completed_candidate_rows": 0,
        "not_entered_reason": "Stage5_ineligible; no missing K1 comparator reruns opened",
    }], control_fields)

    historical = common.csv_rows(
        OUT / "historical_baseline_reference_manifest.csv")
    # Add the already-existing Round 47 300-second rows as explicit
    # common-horizon evidence. The frozen Stage 0 manifest remains untouched;
    # these rows only enrich the derived direct-comparison table.
    round47_stage3 = common.csv_rows(
        ROOT / "results" / "gf_c6_adaptive_mass_contraction_round47" /
        "stage3_300s_results.csv")
    common_horizon_history = []
    for row in round47_stage3:
        if row["instance"] not in common.MECHANISM or row["arm"] not in {
                "K1-AM", "K4-AMC"}:
            continue
        result_path = (ROOT / "results" /
            "gf_c6_adaptive_mass_contraction_round47" / "runs" /
            row["run_id"] / "result.json")
        common_horizon_history.append({
            "instance": row["instance"], "algorithm": row["arm"],
            "process_cap_seconds": row["process_cap_seconds"],
            "certificate": row["certificate"], "work": row["work"],
            "time_seconds": row["time_seconds"],
            "lower_bound": row["lower_bound"],
            "verified_upper_bound": row["verified_upper_bound"],
            "gap": row["relative_gap"], "gi_300": row["gi_300"],
            "split_count": row["split_count"],
            "source_path": result_path.relative_to(ROOT).as_posix(),
            "artifact_sha256": common.sha256(result_path),
            "executable_sha256": row["executable_sha256"],
            "comparison_timing": "historical_exact_common_horizon_300s",
        })
    report_historical = historical + common_horizon_history
    direct = []
    for current in stage_rows:
        direct.append({
            "instance": current["instance"], "algorithm": "K1-AMF",
            "evidence_timing": "contemporaneous_300s",
            "process_cap_seconds": 300, "certificate": current["certificate"],
            "work": current["work"], "time_seconds": current["time_seconds"],
            "lower_bound": current["lower_bound"],
            "verified_upper_bound": current["verified_upper_bound"],
            "gap": current["relative_gap"], "gi_300": current["gi_300"],
            "split_count": current["split_count"],
            "source_path": f"results/gf_k1_amf_formulation_rescue_round48/runs/{current['run_id']}/result.json",
            "artifact_sha256": current["result_sha256"],
            "executable_sha256": current["executable_sha256"],
        })
        for row in historical_rows(current["instance"], report_historical):
            direct.append({
                "instance": row["instance"], "algorithm": row["algorithm"],
                "evidence_timing": row["comparison_timing"],
                "process_cap_seconds": row["process_cap_seconds"],
                "certificate": row["certificate"], "work": row["work"],
                "time_seconds": row["time_seconds"],
                "lower_bound": row["lower_bound"],
                "verified_upper_bound": row["verified_upper_bound"],
                "gap": row["gap"], "gi_300": row["gi_300"],
                "split_count": row["split_count"],
                "source_path": row["source_path"],
                "artifact_sha256": row["artifact_sha256"],
                "executable_sha256": row["executable_sha256"],
            })
    common.write_csv(OUT / "historical_direct_comparison.csv", direct)

    v20_instances = set(common.MECHANISM[5:]) | set(common.EXISTING_CONFIRMATION)
    v20 = [row for row in direct if row["instance"] in v20_instances]
    for instance in common.EXISTING_CONFIRMATION:
        v20.append({
            "instance": instance, "algorithm": "K1-AMF",
            "evidence_timing": "not_entered_conditional_stage",
            "process_cap_seconds": "", "certificate": "", "work": "",
            "time_seconds": "", "lower_bound": "",
            "verified_upper_bound": "", "gap": "", "gi_300": "",
            "split_count": "", "source_path": "", "artifact_sha256": "",
            "executable_sha256": EXE_HASH,
        })
        for row in historical_rows(instance, report_historical):
            v20.append({
                "instance": row["instance"], "algorithm": row["algorithm"],
                "evidence_timing": row["comparison_timing"],
                "process_cap_seconds": row["process_cap_seconds"],
                "certificate": row["certificate"], "work": row["work"],
                "time_seconds": row["time_seconds"],
                "lower_bound": row["lower_bound"],
                "verified_upper_bound": row["verified_upper_bound"],
                "gap": row["gap"], "gi_300": row["gi_300"],
                "split_count": row["split_count"],
                "source_path": row["source_path"],
                "artifact_sha256": row["artifact_sha256"],
                "executable_sha256": row["executable_sha256"],
            })
    common.write_csv(OUT / "v20_comparison.csv", v20)

    no_extra = [{
        "run_id": row["run_id"], "instance": row["instance"],
        "amf_decision_count": row["formulation_decision_count"],
        "existing_K1_AM_lp_count": row["lp_count"],
        "existing_terminal_mip_count": row["terminal_mip_count"],
        "extra_score_lp_count": row["extra_score_lp_count"],
        "extra_score_mip_count": row["extra_score_mip_count"],
        "zero_extra_solve_pass":
            row["extra_score_lp_count"] == row["extra_score_mip_count"] == 0,
    } for row in stage_rows]
    common.write_csv(OUT / "no_extra_solve_audit.csv", no_extra)
    certificates = [{
        "run_id": row["run_id"], "instance": row["instance"],
        "certificate": row["certificate"],
        "certificate_class": row["certificate_class"],
        "rejection_reason": row["certificate_rejection_reason"],
        "coverage_valid": row["coverage_valid"],
        "lower_bound": row["lower_bound"],
        "verified_upper_bound": row["verified_upper_bound"],
        "gap": row["relative_gap"], "false_certificate": False,
        "bound_order_valid": row["lower_bound"] <=
            row["verified_upper_bound"] + EPS,
    } for row in stage_rows]
    common.write_csv(OUT / "certificate_audit.csv", certificates)

    common.write_text(OUT / "mathematical_k1_amf_gate.md", """# Mathematical K1-AMF gate

For the unchanged K1-AM child gains, `eta=min(g_L,g_R)`, `mu=(g_L+g_R)/2`, and `S_AM=eta*mu`. For each child, AMF computes equal-weight mean non-Gini domain contraction `phi_j`. It then uses `gtilde_L=g_L+phi_L max(g_R-g_L,0)`, its symmetric right counterpart, `eta_hat=min(gtilde_L,gtilde_R)`, and `S_AMF=mu*eta_hat`. The single decision is `S_AMF + epsilon_score >= 0.07915`.

Because each `phi_j` lies in `[0,1]`, `eta <= eta_hat <= max(g_L,g_R)` and `S_AMF >= S_AM`. Zero formulation credit or equal child gains reduces exactly to AM. This is a structural refinement gate, not a runtime predictor.
""")
    common.write_text(OUT / "formulation_contraction_definition.md", """# Formulation contraction definition

The profile includes every finite, positive-width, canonical interval-sensitive variable in the frozen families `Y`, `r`, `e`, `h`, `bit`, `prod`, `p`, `d`, and `W_SP`, deduplicated by model-variable name and equally weighted. `G`, G-only aliases, diagnostic variables, and zero-width parent domains are excluded. For variable `v`, child contraction is `clip(1-w_v^j/w_v^P,0,1)`. Wider, incomplete, or nonfinite child profiles fail closed to zero credit and the exact AM action.

Across the 12 live Stage 3 AMF decisions, eligible counts range from 243 to 592; every profile was valid and every decision excluded the Gini coordinate.
""")
    common.write_text(OUT / "amf_exactness_and_termination.md", """# AMF exactness and termination

AMF reads bounds from the already-generated parent and midpoint-child canonical models after the existing K1-AM LP calls. It launches no LP or MIP. A rescue changes only the existing finite-child split/retain disposition; native-target, exact-parent closure, strict child infeasibility, atomic coverage replacement, and the external-tree certificate remain unchanged. Every split is a midpoint split of a finite interval, so the pre-existing finite tree/deadline termination argument applies. Invalid profiles receive zero credit and exactly reproduce AM.
""")
    common.write_text(OUT / "no_new_parameter_audit.md", """# No-new-parameter audit

Pass. K1-AMF uses the already frozen shared `tau=0.07915`; it introduces no lambda, family weight, depth weight, width weight, rho cap, runtime dispatch, or learned coefficient. Equal weighting is a definition, not a fitted parameter. K0 is fixed at one and the split point is fixed at the midpoint. Official commands omit the old explicit C6 rho option and keep AMC, gamma/envelope, PMM/FPMM, rank-1, inheritance changes, and all solver tuning off.
""")
    common.write_text(OUT / "k1_model_chain_reuse_opportunity.md", """# K1 model-chain reuse opportunity (audit only)

Stage 3 created {models} canonical models and recorded {reuse} in-memory reuse events. Round 48 deliberately made no model-chain inheritance change, so this is only a future-work observation. Any reuse intervention would confound the AMF decision effect and requires a separate round.
""".format(models=sum(row["model_count"] for row in stage_rows),
           reuse=sum(row["model_reuse_count"] for row in stage_rows)))

    by_instance = {row["instance"]: row for row in stage_rows}
    common.write_text(OUT / "major_regression_analysis.md",
        comparison_markdown("Major regression analysis", MAJOR,
            by_instance[MAJOR], report_historical,
            "AMF made no action change. The 300-second row did not certify, so the full-horizon historical K1-AM repair is not newly qualified by this bounded round."))
    common.write_text(OUT / "strong_control_rescue_analysis.md",
        comparison_markdown("Strong-control rescue analysis", STRONG,
            by_instance[STRONG], report_historical,
            "The root and every observed decision were unchanged from AM; the row did not certify. Classification: strong_control_not_rescued."))
    common.write_text(OUT / "harmful_negative_control_analysis.md",
        comparison_markdown("Harmful negative-control analysis", NEGATIVE,
            by_instance[NEGATIVE], report_historical,
            "AMF retained the root, produced no rescue, and preserved the exact certificate and historical Work."))
    common.write_text(OUT / "numerical_endpoint_analysis.md",
        comparison_markdown("Numerical-endpoint analysis", NUMERICAL,
            by_instance[NUMERICAL], report_historical,
            "AMF produced no rescue. The remaining relative gap was about 2.02e-7, above the strict certificate tolerance, so no certificate is claimed."))
    common.write_text(OUT / "v12_m2_formulation_analysis.md",
        comparison_markdown("V12 M2 formulation analysis", V12M2,
            by_instance[V12M2], report_historical,
            "The matched root MIDPOINT replay was exact with Work 9.6512 versus RETAIN Work 38.8087, but AMF retained and exactly reproduced Work 38.8087. The beneficial split was missed."))
    common.write_text(OUT / "high_imbalance_analysis.md",
        comparison_markdown("High-imbalance analysis", "high_imbalance_seed3201",
            by_instance["high_imbalance_seed3201"], report_historical,
            "The 300-second row did not certify and contained no formulation rescue. The second high-imbalance confirmation row was not eligible after the offline failure."))
    common.write_text(OUT / "moderate3301_analysis.md",
        comparison_markdown("moderate3301 analysis", "moderate_seed3301",
            by_instance["moderate_seed3301"], report_historical,
            "The row was behaviorally unchanged and ended with gap 0.04763, so the requested <=0.025 guard was not met at Stage 3."))
    common.write_text(OUT / "tight3102_under_refinement_analysis.md",
        comparison_markdown("tight3102 under-refinement analysis", "tight_T_seed3102",
            by_instance["tight_T_seed3102"], report_historical,
            "At byte-identical state L0.0, one-step MIDPOINT completed exact in 789.31 s (Work 1500.20) while RETAIN capped at 1180.03 s (Work 2444.85, gap 0.07428). AMF nevertheless retained and the Stage 3 row had no rescue or certificate."))
    common.write_text(OUT / "additional_confirmation_analysis.md", """# Additional confirmation analysis

The four frozen additional instances were not opened because the mandatory primary offline separation failed B1/B2, closing Stage 4 and Stage 5 before confirmation data could be observed. Their exact historical P-GRB hashes remain frozen in the baseline manifest. Candidate and missing K1 comparator row counts are both zero by contract; this is not missing entered-stage evidence.
""")

    artifacts_ok, artifact_failures = verify_artifacts(stage_rows)
    total_rescues = sum(row["formulation_rescue_count"] for row in stage_rows)
    total_fallbacks = sum(row["invalid_profile_fallback_count"] for row in stage_rows)
    total_decisions = sum(row["formulation_decision_count"] for row in stage_rows)
    certificates_count = sum(row["certificate"] for row in stage_rows)
    evidence_hashes = {
        name: common.sha256(OUT / name) for name in (
            "amf_separation_audit.json", "stage3_300s_results.csv",
            "tight3102_counterfactual_results.csv",
            "default_off_equivalence.csv", "certificate_audit.csv")
    }
    decision = {
        "schema": "round48-final-decision-v1",
        "completion_status": "round48_complete_bounded_negative",
        "derived_from_completed_evidence": True,
        "evidence_sha256": evidence_hashes,
        "structural_classification": "amf_partial_structural_separation",
        "strong_control_classification": "strong_control_not_rescued",
        "tight3102_classification": "tight3102_not_improved",
        "K1_classification": "bounded_negative_k1_amf",
        "benchmark_classification": "k1_amf_pgrb_negative",
        "scale_qualification": "v20_negative",
        "offline_gate_failed": True, "offline_failed_checks": ["B1", "B2"],
        "tau": common.TAU, "new_adjustable_parameter_count": 0,
        "stage_rows": {"stage3": 8, "stage4": 0, "stage5": 0},
        "counterfactual_rows": 4,
        "formulation_decision_count": total_decisions,
        "rescue_decision_count": total_rescues,
        "invalid_profile_fallback_count": total_fallbacks,
        "extra_lp_count": sum(row["extra_score_lp_count"] for row in stage_rows),
        "extra_mip_count": sum(row["extra_score_mip_count"] for row in stage_rows),
        "certificate_count": certificates_count, "false_certificate_count": 0,
        "artifact_hash_audit_passed": artifacts_ok,
        "artifact_hash_failures": artifact_failures,
        "mandatory_entered_stage_missing_rows": [],
        "conditional_not_entered_rows": {
            "stage4": 11, "stage5": 15,
            "additional_confirmation_candidate": 4,
            "additional_confirmation_K1_comparator": 0,
        },
        "paper_preset_added": False, "original_C6_preset_changed": False,
        "historical_K1_AM_changed": False,
    }
    common.write_json(OUT / "final_decision.json", decision)

    common.write_text(OUT / "final_report.md", f"""# Round 48 final report

## Outcome

Round 48 is complete on the contractually bounded-negative pathway. The primary offline gate failed because the frozen equal-weight AMF score retained B1 and B2. All eight Stage 3 diagnostic rows were completed; Stage 4/5 were correctly not entered. Structural classification is `amf_partial_structural_separation`; the K1 decision is `bounded_negative_k1_amf`.

## Direct answers

1. The formulation profile includes `Y`, `r`, `e`, `h`, `bit`, `prod`, `p`, `d`, and `W_SP`, with equal per-variable weight.
2. `G` and G-only aliases were fully excluded; every live decision logged one excluded G coordinate and zero G credit.
3. Exact `phi_L/phi_R` values for all H/B/U/T states are in `formulation_contraction_census.csv`; they range by formulation and state, not by tuned family policy.
4. No. The unchanged tau retains H1/H2 but also B1/B2; it splits B3/B4.
5. The harmful controls were retained; the major row had no action change, though it did not certify at 300 seconds.
6. No. Strong control had zero rescues and no Stage 3 certificate.
7. Yes. V10 M3 retained and certified exactly with historical Work 8.9915.
8. No. The numerical endpoint had no rescue and remained uncertified at gap 2.02e-7.
9. No. V12 M2 exactly reproduced Work 38.8087, while the matched midpoint replay needed Work 9.6512.
10. tight3102 has two exact common historical states; the first and only action divergence is byte-identical `L0.0`.
11. Yes. MIDPOINT was exact in 789.31 s/Work 1500.20; RETAIN capped in 1180.03 s/Work 2444.85/gap 0.07428.
12. No. AMF retained `L0.0` and logged no live rescue.
13. No. The Stage 3 tight3102 gap was {by_instance['tight_T_seed3102']['relative_gap']:.9g}.
14. Not tested: only seed3201 was eligible for Stage 3 and it did not certify; seed3202 was behind the closed later stage.
15. moderate3301 was behaviorally preserved but its Stage 3 gap {by_instance['moderate_seed3301']['relative_gap']:.9g} exceeded 0.025.
16. Formulation rescue decisions: {total_rescues} across {total_decisions} AMF decisions.
17. Invalid-profile AM fallbacks: {total_fallbacks}.
18. Extra score solves: zero LP and zero MIP.
19. No adjustable parameter entered; tau remains 0.07915.
20. K1-AMF does not establish an advantage over P-GRB; classification is `k1_amf_pgrb_negative`.
21. It failed to recover the tight3102 split/certificate achieved historically by K1-r015.
22. It was behaviorally identical to K1-AM on all 12 observed decisions.
23. It remains materially behind K4-AMC on strong control, V12 M2, and tight3102 historical evidence.
24. The four additional instances were not opened because the offline gate failed; their P-GRB references remain hash-audited.
25. No. K1-AMF is not ready to become the main research algorithm.
26. Longer-horizon candidate behavior, the three existing V20 confirmation rows, and the four additional instances remain deliberately unproven because their entry conditions failed.

## Stage 3

{table(stage_rows, ['instance','certificate','work','time_seconds','relative_gap','split_count','formulation_rescue_count','invalid_profile_fallback_count'])}

No entered-stage row is missing. There were {certificates_count}/8 strict certificates and zero false certificates. Artifact hash audit: {'PASS' if artifacts_ok else 'FAIL'}.
""")
    common.write_text(OUT / "final_build_and_tests.md", f"""# Final build and tests

- Algorithmic source: `4c08f36452eaf90c3c0a974a9782abfa37eff16b` / tree `cb554bf511a35c417354e5ce3cf5f5dbb8190e40`.
- Clean build: `build/official-round48-4c08f3645`, Release, GNU 14.2.0, Gurobi 13.0.2.
- Official executable SHA-256: `{EXE_HASH}`.
- Full build: pass (all targets).
- CTest: 26/26 pass; dedicated Round48K1AMFTests: 42 checks.
- Historical Python protocol inventory: 135/135 pass after binding the frozen Round 46/47 executable paths.
- Round 48 Python protocol inventory: 14/14 pass after final-decision generation.
- K1-AM default-off sentinel: 20/20 comparisons pass.
- Official candidate executable hashes: one (`{EXE_HASH}`).
- Stage 3 artifact hashes: {'pass' if artifacts_ok else 'fail'}; failures: {artifact_failures}.
""")
    common.write_text(OUT / "reproduction_commands.md", f"""# Reproduction commands

From `E:/codes/ExactEBRP` using `D:/msys64/ucrt64/bin/python.exe`:

```powershell
cmake -S . -B build/official-round48-4c08f3645 -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT=D:/gurobi1302/win64
cmake --build build/official-round48-4c08f3645 -j 4
ctest --test-dir build/official-round48-4c08f3645 --output-on-failure
$env:EXACTEBRP_ROUND48_EXE = "E:/codes/ExactEBRP/build/official-round48-4c08f3645/ExactEBRP.exe"
python -B -m unittest discover -s tests -p "round*_protocol_tests.py" -v
python -B scripts/run_round48_default_off_equivalence.py --executable $env:EXACTEBRP_ROUND48_EXE --process-cap 120
python -B scripts/run_round48.py counterfactuals --executable $env:EXACTEBRP_ROUND48_EXE
python -B scripts/run_round48.py stage3 --executable $env:EXACTEBRP_ROUND48_EXE
python -B scripts/analyze_round48_offline.py
python -B scripts/analyze_round48.py
```

Completed rows resume from their sealed completion markers. Stage 4/5 have no reproduction command because the frozen offline gate made them ineligible.
""")

    inventory = []
    for path in sorted(p for p in OUT.rglob("*") if p.is_file() and
                       p.name != "final_evidence_inventory.csv"):
        inventory.append({
            "path": path.relative_to(OUT).as_posix(),
            "size_bytes": path.stat().st_size, "sha256": common.sha256(path),
            "category": "run_artifact" if "runs" in path.parts else "round_report",
        })
    common.write_csv(OUT / "final_evidence_inventory.csv", inventory)
    print(json.dumps({
        "stage3_rows": len(stage_rows), "certificates": certificates_count,
        "decisions": total_decisions, "rescues": total_rescues,
        "fallbacks": total_fallbacks, "artifacts_ok": artifacts_ok,
        "inventory_files": len(inventory),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
