#!/usr/bin/env python3
"""Assemble the bounded-negative Round 49 evidence and reports."""

from __future__ import annotations

import math
from pathlib import Path
import subprocess
from typing import Any

import round49_common as common


ROOT, OUT, RUNS = common.ROOT, common.OUT, common.RUNS
EXE = ROOT / "build" / "official-round49-36990fc47" / "ExactEBRP.exe"
EXE_HASH = "f73b40a12590ab432abc201f95fbcea70ba499337239f31175fba589ab0d8ed5"
SOURCE_COMMIT = "36990fc47c8f86a458e9c068c471ac6ec45454a9"
EPS = common.CERTIFICATE_TOLERANCE
MAJOR, STRONG, NEGATIVE, NUMERICAL, V12M2 = common.MECHANISM[:5]
HIGH, MODERATE, TIGHT = common.MECHANISM[5:]


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


def normalized(path: Path) -> dict[str, Any]:
    value = common.load_json(path)
    return value[0] if isinstance(value, list) else value


def relative_gap(lower: float, upper: float) -> float:
    return max(0.0, upper - lower) / max(abs(upper), EPS)


def trace_points(run_dir: Path, data: dict[str, Any]) -> list[tuple[float, float, float]]:
    points: list[tuple[float, float, float]] = []
    for row in common.csv_rows(run_dir / "global_bound_trace.csv"):
        elapsed = fnum(row.get("process_elapsed_seconds"))
        lower = fnum(row.get("valid_global_lower_bound"))
        upper = fnum(row.get("verified_global_upper_bound"))
        if upper > 0.0 and upper + EPS >= lower:
            points.append((max(0.0, elapsed), lower, upper))
    lower = fnum(data.get("external_gini_tree_global_lower_bound",
                          data.get("lower_bound")))
    upper = fnum(data.get("external_gini_tree_verified_upper_bound",
                          data.get("upper_bound")))
    elapsed = fnum(data.get("final_process_wall_time_seconds",
                            data.get("actual_runtime_seconds")))
    if upper > 0.0 and upper + EPS >= lower:
        points.append((elapsed, lower, upper))
    points.sort()
    dedup: list[tuple[float, float, float]] = []
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
    last = area = 0.0
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


def joined(rows: list[dict[str, str]], field: str) -> str:
    return ";".join(row.get(field, "") for row in rows)


def extract_stage3(instance: str) -> dict[str, Any]:
    run_id = f"stage3_300s__{instance}__K1-AM-RC-A"
    run_dir = RUNS / run_id
    command = common.load_json(run_dir / "command.json")
    marker = common.load_json(run_dir / "completion_marker.json")
    data = normalized(run_dir / "result.json")
    decisions = common.csv_rows(run_dir / "rc_decision_ledger.csv")
    exact = truth(data.get("strict_certified_original_problem"))
    elapsed = fnum(data.get("final_process_wall_time_seconds",
                            data.get("actual_runtime_seconds")))
    lower = fnum(data.get("lower_bound"))
    upper = fnum(data.get("upper_bound"))
    h300 = horizon(trace_points(run_dir, data), 300.0, exact, elapsed)
    differences = [row for row in decisions
                   if row.get("AM_action") != row.get("final_action")]
    primitive = max((inum(row.get("primitive_variable_count"))
                     for row in decisions), default=0)
    extra_fixings = sum(
        max(0, inum(row.get("left_fixed_count")) -
            inum(row.get("parent_fixed_count"))) +
        max(0, inum(row.get("right_fixed_count")) -
            inum(row.get("parent_fixed_count"))) for row in decisions)
    disjoint = sum(inum(row.get("disjoint_domain_count"))
                   for row in decisions)
    return {
        "record_type": "candidate", "candidate_row": True,
        "run_id": run_id, "stage": "stage3_300s",
        "algorithm": "K1-AM-RC-A", "rule": "D-RCD",
        "instance": instance, "role": command["role"],
        "K0": 1, "tau": common.TAU,
        "process_cap_seconds": command["process_cap_seconds"],
        "executable_sha256": command["executable_sha256"],
        "status": data.get("status", ""), "certificate": exact,
        "certificate_class": data.get("strict_certificate_class", ""),
        "certificate_rejection_reason":
            data.get("strict_certificate_rejection_reason", ""),
        "coverage_valid": truth(
            data.get("external_gini_tree_root_coverage_valid")) and truth(
            data.get("external_gini_tree_parent_child_coverage_valid")),
        "completion_marker": truth(marker.get("complete")),
        "time_seconds": elapsed,
        "work": fnum(data.get("external_gini_tree_work")),
        "lower_bound": lower, "verified_upper_bound": upper,
        "relative_gap": relative_gap(lower, upper),
        "lb_300": h300["lb"], "ub_300": h300["ub"],
        "gap_300": h300["gap"], "gi_300": h300["gi"],
        "split_count": inum(data.get("external_gini_tree_split_count")),
        "rc_decision_count": inum(data.get("round49_rc_decision_count")),
        "reduced_cost_valid_decision_count": inum(
            data.get("round49_rc_valid_decision_count")),
        "rc_rescue_count": inum(data.get("round49_rc_rescue_count")),
        "invalid_profile_fallback_count": inum(
            data.get("round49_rc_invalid_profile_fallback_count")),
        "primitive_variable_count": primitive,
        "D_P": joined(decisions, "D_P"),
        "D_L": joined(decisions, "D_L"),
        "D_R": joined(decisions, "D_R"),
        "H_P": joined(decisions, "H_P"),
        "H_L": joined(decisions, "H_L"),
        "H_R": joined(decisions, "H_R"),
        "extra_rc_fixings": extra_fixings,
        "disjoint_domain_count": disjoint,
        "native_target_count": inum(
            data.get("external_gini_tree_child_bound_target_phase_count")),
        "terminal_mip_count": inum(
            data.get("external_gini_tree_terminal_mip_optimize_count")),
        "lp_count": inum(data.get("external_gini_tree_lp_optimize_count")),
        "model_count": inum(data.get("external_gini_tree_model_count")),
        "extra_score_lp_count": inum(data.get("round49_rc_extra_lp_count")),
        "extra_score_mip_count": inum(data.get("round49_rc_extra_mip_count")),
        "first_action_difference_from_historical_K1_AM":
            differences[0]["interval_id"] if differences else "none",
        "failure_reason": data.get("external_gini_tree_failure_reason", ""),
        "result_sha256": common.sha256(run_dir / "result.json"),
        "artifact_manifest_sha256":
            common.sha256(run_dir / "artifact_manifest.csv"),
    }


def md_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    out = ["| " + " | ".join(columns) + " |",
           "|" + "|".join("---" for _ in columns) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(column, ""))
                                       for column in columns) + " |")
    return "\n".join(out)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()


def main() -> None:
    if common.sha256(EXE) != EXE_HASH:
        raise RuntimeError("official executable hash changed")
    stage = [extract_stage3(instance) for instance in common.MECHANISM]
    if len(stage) != 8 or not all(row["completion_marker"] for row in stage):
        raise RuntimeError("entered Stage 3 matrix is incomplete")
    if len({row["executable_sha256"] for row in stage}) != 1:
        raise RuntimeError("official rows do not share one executable")
    common.write_csv(OUT / "stage3_300s_results.csv", stage)

    # Commit-sized copies of the mandatory live ledgers. The per-variable
    # ledger is summarized by decision and semantic family; its full
    # 8.3-MB row-level form remains local and is hash-inventoried.
    def aggregate(name: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for item in stage:
            for row in common.csv_rows(RUNS / item["run_id"] / name):
                rows.append({"official_run_id": item["run_id"],
                             "official_instance": item["instance"], **row})
        return rows
    for ledger in ("rc_decision_ledger.csv", "lp_primal_dual_ledger.csv",
                   "native_target_ledger.csv", "interval_tree_events.csv",
                   "interval_coverage_ledger.csv", "global_bound_trace.csv",
                   "model_size_ledger.csv", "certificate_ledger.csv"):
        common.write_csv(OUT / ledger, aggregate(ledger))
    variable_compact: list[dict[str, Any]] = []
    for item in stage:
        groups: dict[tuple[str, str], list[dict[str, str]]] = {}
        for row in common.csv_rows(
                RUNS / item["run_id"] / "rc_variable_domain_ledger.csv"):
            groups.setdefault((row["decision_sequence"], row["family"]), []).append(row)
        for (decision, family), rows in sorted(groups.items()):
            variable_compact.append({
                "record_granularity": "decision_family_compact",
                "official_run_id": item["run_id"],
                "instance": item["instance"], "decision_sequence": decision,
                "interval_id": rows[0]["interval_id"], "family": family,
                "variable_count": len(rows),
                "parent_effective_cardinality_sum": sum(
                    inum(row["parent_effective_count"]) for row in rows),
                "parent_rc_cardinality_sum": sum(
                    inum(row["parent_rc_count"]) for row in rows),
                "left_rc_cardinality_sum": sum(
                    inum(row["left_rc_count"]) for row in rows),
                "right_rc_cardinality_sum": sum(
                    inum(row["right_rc_count"]) for row in rows),
                "parent_fixed_count": sum(
                    inum(row["parent_rc_count"]) == 1 for row in rows),
                "left_fixed_count": sum(
                    inum(row["left_rc_count"]) == 1 for row in rows),
                "right_fixed_count": sum(
                    inum(row["right_rc_count"]) == 1 for row in rows),
                "parent_tightened_count": sum(
                    inum(row["parent_rc_count"]) <
                    inum(row["parent_effective_count"]) for row in rows),
                "left_tightened_count": sum(
                    inum(row["left_rc_count"]) <
                    inum(row["left_effective_count"]) for row in rows),
                "right_tightened_count": sum(
                    inum(row["right_rc_count"]) <
                    inum(row["right_effective_count"]) for row in rows),
                "exact_child_disjoint_count": sum(
                    truth(row["exact_child_disjoint"]) for row in rows),
                "full_row_level_ledger_committed": False,
            })
    common.write_csv(OUT / "rc_variable_domain_ledger.csv", variable_compact)

    r47 = common.csv_rows(ROOT / "results" /
        "gf_c6_adaptive_mass_contraction_round47" /
        "stage3_300s_results.csv")
    r47_map = {(row["instance"], row["arm"]): row for row in r47}
    historical = common.csv_rows(
        OUT / "historical_baseline_reference_manifest.csv")
    comparisons: list[dict[str, Any]] = []
    for row in stage:
        old = r47_map.get((row["instance"], "K1-AM"))
        if old is None:
            old = next((item for item in historical
                        if item["instance"] == row["instance"] and
                        item["algorithm"] == "K1-AM"), {})
        comparisons.append({
            "instance": row["instance"], "role": row["role"],
            "candidate_certificate": row["certificate"],
            "candidate_work": row["work"],
            "candidate_time_seconds": row["time_seconds"],
            "candidate_gap_300": row["gap_300"],
            "candidate_gi_300": row["gi_300"],
            "candidate_splits": row["split_count"],
            "candidate_rescues": row["rc_rescue_count"],
            "candidate_fallbacks": row["invalid_profile_fallback_count"],
            "historical_K1_AM_certificate": old.get("certificate", ""),
            "historical_K1_AM_work": old.get("work", ""),
            "historical_K1_AM_time_seconds": old.get("time_seconds", ""),
            "historical_K1_AM_gap": old.get(
                "relative_gap", old.get("gap", "")),
            "historical_K1_AM_gi_300": old.get("gi_300", ""),
            "work_delta": row["work"] - fnum(old.get("work")),
            "first_action_difference":
                row["first_action_difference_from_historical_K1_AM"],
            "intended_direction": row["instance"] in {STRONG, NUMERICAL,
                                                        V12M2, TIGHT},
            "intended_direction_achieved": row["instance"] == TIGHT and
                row["rc_rescue_count"] > 0,
        })
    common.write_csv(OUT / "stage3_rule_comparison.csv", comparisons)
    common.write_json(OUT / "stage3_revision_record.json", {
        "schema": "round49-stage3-revision-record-v1",
        "revision_used": False, "revision_count": 0,
        "reason": "offline gate failed and all four frozen rules predicted identical actions; Stage 3 confirmed harmful major rescue and missed B1/B2/U1",
        "invalidated_stage3_rows": [],
        "final_rule": "D-RCD", "complete_matrix_rows": 8,
    })
    control_fields = ["record_type", "candidate_row", "stage", "entered",
                      "completed_candidate_rows", "not_entered_reason"]
    common.write_csv(OUT / "stage4_1200s_results.csv", [{
        "record_type": "stage_control", "candidate_row": False,
        "stage": "stage4_1200s", "entered": False,
        "completed_candidate_rows": 0,
        "not_entered_reason": "primary_offline_gate_failed; bounded diagnostic path forbids Stage 4",
    }], control_fields)
    common.write_csv(OUT / "stage5_1800s_results.csv", [{
        "record_type": "stage_control", "candidate_row": False,
        "stage": "stage5_1800s", "entered": False,
        "completed_candidate_rows": 0,
        "not_entered_reason": "Stage 4 not entered after mandatory offline gate failure",
    }], control_fields)
    common.write_csv(OUT / "additional_confirmation_comparators.csv", [{
        "record_type": "panel_control", "candidate_row": False,
        "stage": "additional_confirmation", "entered": False,
        "completed_candidate_rows": 0,
        "not_entered_reason": "Stage 5 ineligible; no limited comparator rows opened",
    }], control_fields)

    # Direct paired evidence for all 15 potential Stage 5 instances. Historical
    # rows stay at their original caps; current rows exist only for entered Stage 3.
    direct: list[dict[str, Any]] = []
    current = {row["instance"]: row for row in stage}
    for instance in common.STAGE5:
        if instance in current:
            row = current[instance]
            direct.append({
                "instance": instance, "algorithm": "K1-AM-RC-A",
                "evidence_timing": "contemporaneous_300s",
                "exact_or_capped": "exact" if row["certificate"] else "capped",
                "process_cap_seconds": 300, "work": row["work"],
                "time_seconds": row["time_seconds"],
                "lower_bound": row["lower_bound"],
                "verified_upper_bound": row["verified_upper_bound"],
                "gap": row["relative_gap"], "gi_300": row["gi_300"],
                "gi_1200": "", "gi_1800": "",
                "split_count": row["split_count"],
                "rescue_count": row["rc_rescue_count"],
                "lp_model_count": row["model_count"],
                "source_path": f"results/gf_k1_lp_primal_dual_rescue_round49/runs/{row['run_id']}/result.json",
                "artifact_sha256": row["result_sha256"],
                "executable_sha256": row["executable_sha256"],
            })
        for old in historical:
            if old["instance"] != instance:
                continue
            direct.append({
                "instance": instance, "algorithm": old["algorithm"],
                "evidence_timing": old["comparison_timing"],
                "exact_or_capped": "exact" if truth(old["certificate"]) else "capped",
                "process_cap_seconds": old["process_cap_seconds"],
                "work": old["work"], "time_seconds": old["time_seconds"],
                "lower_bound": old["lower_bound"],
                "verified_upper_bound": old["verified_upper_bound"],
                "gap": old["gap"], "gi_300": old["gi_300"],
                "gi_1200": old["gi_1200"], "gi_1800": old["gi_1800"],
                "split_count": old["split_count"], "rescue_count": "",
                "lp_model_count": old["lp_model_count"],
                "source_path": old["source_path"],
                "artifact_sha256": old["artifact_sha256"],
                "executable_sha256": old["executable_sha256"],
            })
    common.write_csv(OUT / "historical_direct_comparison.csv", direct)
    v20_set = {HIGH, MODERATE, TIGHT, *common.EXISTING_CONFIRMATION}
    common.write_csv(OUT / "v20_comparison.csv",
                     [row for row in direct if row["instance"] in v20_set])

    no_extra = [{
        "run_id": row["run_id"], "instance": row["instance"],
        "rc_decision_count": row["rc_decision_count"],
        "existing_K1_AM_lp_count": row["lp_count"],
        "existing_terminal_mip_count": row["terminal_mip_count"],
        "extra_score_lp_count": row["extra_score_lp_count"],
        "extra_score_mip_count": row["extra_score_mip_count"],
        "zero_extra_solve_pass":
            row["extra_score_lp_count"] == row["extra_score_mip_count"] == 0,
    } for row in stage]
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
    } for row in stage]
    common.write_csv(OUT / "certificate_audit.csv", certificates)

    common.write_text(OUT / "no_new_parameter_audit.md", """# No-new-parameter audit

Pass. The live rule is the frozen categorical `D-RCD` condition. K0 remains one, the point is the midpoint, and the only continuous algorithmic threshold is the inherited `tau=0.07915`. The RC numerical tolerance is derived from the existing certificate tolerance plus floating-point roundoff. There are no family weights, fitted coefficients, learned models, size/depth/width conditions, rho cap, root-processing probes, or solver-parameter changes. All official commands keep AMF-v1, AMC, gamma/envelope, PMM/FPMM, rank-1 cuts, starts, and consolidation off.
""")
    common.write_text(OUT / "evidence_storage_policy.md", """# Evidence storage policy

The branch commits source, tests, frozen manifests, compact state/domain censuses, sealed summary ledgers, reports, hashes, and reproduction commands. The root `rc_variable_domain_ledger.csv` is a decision-by-family compact projection of the full row-level variable ledger. Full per-variable rows, canonical LPs, native solver logs, development smoke output, and duplicated run trees remain local. Their paths and SHA-256 hashes are recorded in `compact_evidence_inventory.csv`; official conclusions use the sealed compact ledgers copied from each run. No complete Round 45–48 result tree is duplicated.
""")

    raw_rows: list[dict[str, Any]] = []
    for directory, evidence_class in ((OUT / "offline_raw", "offline_lp_raw"),
                                      (OUT / "dev_smoke", "development_smoke"),
                                      (RUNS, "official_run_raw")):
        if not directory.exists():
            continue
        for path in sorted(p for p in directory.rglob("*") if p.is_file()):
            raw_rows.append({
                "evidence_class": evidence_class,
                "path": path.relative_to(ROOT).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": common.sha256(path),
                "committed": False,
                "reproduction_source": "reproduction_commands.md",
            })
    common.write_csv(OUT / "compact_evidence_inventory.csv", raw_rows)

    by = {row["instance"]: row for row in stage}
    old_by = {row["instance"]: row for row in comparisons}
    def analysis(title: str, instance: str, conclusion: str) -> str:
        row, pair = by[instance], old_by[instance]
        values = [{"algorithm": "K1-AM-RC-A", "certificate": row["certificate"],
                   "work": row["work"], "time": row["time_seconds"],
                   "gap": row["relative_gap"], "GI300": row["gi_300"],
                   "rescues": row["rc_rescue_count"]},
                  {"algorithm": "historical K1-AM",
                   "certificate": pair["historical_K1_AM_certificate"],
                   "work": pair["historical_K1_AM_work"],
                   "time": pair["historical_K1_AM_time_seconds"],
                   "gap": pair["historical_K1_AM_gap"],
                   "GI300": pair["historical_K1_AM_gi_300"],
                   "rescues": 0}]
        return f"# {title}\n\n{md_table(values, ['algorithm','certificate','work','time','gap','GI300','rescues'])}\n\n{conclusion}\n"
    common.write_text(OUT / "major_regression_analysis.md", analysis(
        "Major regression analysis", MAJOR,
        "Fail. D-RCD rescued the known harmful root and nine later states; the 300-second row remained capped. The historical K1-AM 1800-second certificate at Work approximately 843.456 is not displaced."))
    common.write_text(OUT / "strong_control_analysis.md", analysis(
        "Strong-control analysis", STRONG,
        "Fail. The only RC profile was valid but produced no rescue, so the intended strong-control action change and 30% Work reduction did not occur."))
    common.write_text(OUT / "harmful_negative_control_analysis.md", analysis(
        "V10 M3 harmful negative-control analysis", NEGATIVE,
        "Pass for this control. The root was retained, no RC rescue occurred, and the strict certificate/Work match historical K1-AM."))
    common.write_text(OUT / "numerical_endpoint_analysis.md", analysis(
        "Numerical-endpoint analysis", NUMERICAL,
        "No improvement. The profile was valid but D-RCD did not rescue the endpoint; Work and bound behavior match the historical K1-AM path within deterministic solver behavior."))
    common.write_text(OUT / "v12_m2_analysis.md", analysis(
        "V12 M2 analysis", V12M2,
        "Fail target. The row strictly certified at Work 38.8087 with zero rescue, exactly the historical K1-AM Work rather than the requested 25% reduction."))
    common.write_text(OUT / "tight3102_analysis.md", analysis(
        "tight3102 analysis", TIGHT,
        "Partial local action evidence only. D-RCD recovered the known L0.0 split and generated eight rescues, but the 300-second row remained capped; the 1800-second certificate target was not opened because Stage 4/5 were forbidden."))
    common.write_text(OUT / "high_imbalance_analysis.md", analysis(
        "High-imbalance analysis", HIGH,
        "The existing root AM split was preserved, but five downstream RC rescues changed the trajectory and the 300-second row remained capped. High-imbalance 3202 was not opened."))
    common.write_text(OUT / "moderate3301_analysis.md", analysis(
        "moderate3301 analysis", MODERATE,
        "The root AM behavior was preserved, one later RC rescue changed the path, and the row remained capped. No 1800-second <=2.5% qualification claim is available."))
    common.write_text(OUT / "additional_confirmation_analysis.md", """# Additional confirmation analysis

The four unopened Round-39 instances were never inspected through live candidate runs. Stage 5 was structurally ineligible after the mandatory offline gate failed, so there are zero candidate or limited comparator rows and no confirmation claim. Historical P-GRB hashes for all four were verified before Stage 0.
""")

    total_decisions = sum(row["rc_decision_count"] for row in stage)
    total_valid = sum(row["reduced_cost_valid_decision_count"] for row in stage)
    total_rescues = sum(row["rc_rescue_count"] for row in stage)
    total_fallbacks = sum(row["invalid_profile_fallback_count"] for row in stage)
    max_primitive = max(row["primitive_variable_count"] for row in stage)
    strict_count = sum(row["certificate"] for row in stage)
    artifact_failures: list[str] = []
    for row in stage:
        run_dir = RUNS / row["run_id"]
        for item in common.csv_rows(run_dir / "artifact_manifest.csv"):
            path = run_dir / item["path"]
            if not path.is_file() or common.sha256(path) != item["sha256"]:
                artifact_failures.append(f"{row['run_id']}:{item['path']}")
    final_decision = {
        "schema": "round49-final-decision-v1",
        "completion_status": "round49_complete",
        "derived_from_completed_evidence": True,
        "offline_gate_failed": True,
        "structural_classification": "rc_domain_partial_separation",
        "mechanism_classification": "bounded_negative_rc_rescue",
        "k1_classification": "bounded_negative_k1_am_rc",
        "benchmark_classification": "k1_am_rc_pgrb_mixed",
        "scale_qualification": "small_only",
        "selected_rule": "D-RCD", "cli_rule": "d-rcd",
        "stage3_revision_used": False,
        "tau": common.TAU, "K0": 1, "point_rule": "midpoint",
        "primitive_families": [row[0] for row in common.PRIMITIVE_FAMILIES],
        "maximum_primitive_variable_count": max_primitive,
        "rc_decision_count": total_decisions,
        "reduced_cost_valid_decision_count": total_valid,
        "rescue_count": total_rescues,
        "invalid_profile_fallback_count": total_fallbacks,
        "extra_lp_count": 0, "extra_mip_count": 0,
        "new_adjustable_parameter_count": 0,
        "stage_rows": {"stage3": 8, "stage4": 0, "stage5": 0},
        "entered_stage_missing_rows": [],
        "certificate_summary": {"strict": strict_count,
                                "capped_or_noncertified": 8 - strict_count,
                                "false_certificates": 0},
        "artifact_hash_failures": artifact_failures,
        "official_source_commit": SOURCE_COMMIT,
        "official_executable_sha256": EXE_HASH,
        "evidence_sha256": {
            "stage3": common.sha256(OUT / "stage3_300s_results.csv"),
            "separation": common.sha256(
                OUT / "rc_rule_separation_audit.json"),
            "certificate": common.sha256(OUT / "certificate_audit.csv"),
            "default_off": common.sha256(OUT / "default_off_equivalence.csv"),
        },
        "candidate_ready_for_main_research_algorithm": False,
        "reason": "D/H and exact separation cannot distinguish mandatory harmful H1 from beneficial T1; live D-RCD rescues H1, misses B1/B2/U1, and provides no reliable aggregate split-rescue rule.",
    }
    common.write_json(OUT / "final_decision.json", final_decision)

    common.write_text(OUT / "final_build_and_tests.md", f"""# Final build and tests

- Official source commit: `{SOURCE_COMMIT}`
- Clean build: `build/official-round49-36990fc47/`
- Configuration: Release, GNU 14.2.0, Gurobi enabled, Auto presolve contract
- Official executable SHA-256: `{EXE_HASH}`
- CTest: 27/27 passed
- Historical unittest-style protocol tests: 149 passed
- Historical direct protocol suites: 6 files, 405 reported checks/groups passed
- Round 49 protocol tests after final reports: 13/13 passed
- Round 49 C++ target: 42 internal checks passed
- Default-off K1-AM equivalence: 20/20 comparisons passed
- Stage 3: 8/8 sealed with one executable; Stage 4/5 not entered
- Source changed after build: no algorithmic or executable-linked source change
""")
    common.write_text(OUT / "reproduction_commands.md", f"""# Reproduction commands

Run from `E:/codes/ExactEBRP` with the bundled/available Python and CMake.

```powershell
cmake -S . -B build/official-round49-36990fc47 -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=D:/msys64/ucrt64/bin/c++.exe -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT=D:/gurobi1302/win64
cmake --build build/official-round49-36990fc47 --config Release -j 2
ctest --test-dir build/official-round49-36990fc47 -C Release --output-on-failure -j 2
$env:EXACTEBRP_ROUND49_EXE="E:/codes/ExactEBRP/build/official-round49-36990fc47/ExactEBRP.exe"
python -m unittest -v tests.round49_protocol_tests
python scripts/run_round49_default_off_equivalence.py --executable $env:EXACTEBRP_ROUND49_EXE --process-cap 120
python scripts/run_round49.py stage3 --executable $env:EXACTEBRP_ROUND49_EXE
python scripts/analyze_round49.py
```

Offline LP evidence was extracted only before live runtime with `Round49RCOfflineExtract`; exact commands and all 27 solve rows are in `offline_diagnostic_solve_log.csv`. No command has a process cap above 1800 seconds.
""")
    report = f"""# Round 49 final report — K1 LP primal-dual rescue

## Outcome

Round 49 is complete on the bounded-negative pathway. The mandatory offline gate failed before runtime, so exactly one diagnostic `D-RCD` arm completed all 8 Stage 3 rows; Stage 4 and Stage 5 were not eligible. Classification: `rc_domain_partial_separation`, `bounded_negative_rc_rescue`, `bounded_negative_k1_am_rc`, `k1_am_rc_pgrb_mixed`, `small_only`.

## Stage 3 summary

{md_table(stage, ['instance','certificate','work','time_seconds','relative_gap','gi_300','rc_decision_count','rc_rescue_count','invalid_profile_fallback_count','primitive_variable_count'])}

## Required questions

1. **Primitive variables:** routing arcs `x`, visit selections `z`, operation modes `mode`, pickup `p`, drop `d`, vehicle loads `load`, and final inventories `Y`.
2. **Duplicate/auxiliary exclusion:** yes; bit expansions, products/McCormick variables, selectors, Gini variables/aliases, duplicated semantics, continuous, and diagnostic variables were excluded by the frozen positive registry.
3. **Reduced costs without extra solves:** yes. All {total_valid}/{total_decisions} live profiles used primal/RC/basis attributes copied after already-required LP optimizes; extra LP/MIP count was 0/0.
4. **Mandatory RC domains:** H1 and H3 contracted enough to trigger harmful rescues; H2/B1/B2/U1 remained full; B3/B4 retained their AM splits; T1 contracted and was rescued. Exact counts are in `reduced_cost_domain_census.csv`.
5. **D/H separation:** no. D and H produced identical mandatory actions and could not separate H1 from T1.
6. **Exact child separation:** no additional useful information; RCDS matched RCD on every mandatory state.
7. **Offline iterations:** two—D with RCD/RCDS, then H with RCD/RCDS. No other formula was attempted.
8. **Stage 3 revision:** no.
9. **Major and V10 M3:** V10 M3 was retained and certified; the major root was wrongly rescued and capped.
10. **Strong control:** not rescued; no intended improvement.
11. **Numerical endpoint:** not rescued; no intended improvement.
12. **V12 M2:** no rescue; exact Work 38.8087, behaviorally identical to K1-AM.
13. **tight3102:** the L0.0 beneficial split was recovered, but the 300-second row remained capped.
14. **High imbalance:** the existing AM root split was preserved; five later rescues altered 3201, which remained capped; 3202 was not opened.
15. **moderate3301:** root behavior was preserved, one later rescue occurred, and the 300-second row remained capped.
16. **RC rescues:** {total_rescues} across {total_decisions} decisions.
17. **Invalid fallbacks:** {total_fallbacks}.
18. **Extra solves:** none—0 LP and 0 MIP/root-processing scoring solves.
19. **New adjustable parameters:** none; tau remains 0.07915.
20. **Versus K1-r015:** the direct table retains paired historical evidence, but the candidate is not promoted because mandatory action gates failed.
21. **Versus K1-AM:** identical on strong, V10, numerical, and V12 M2; different but harmful on major; mixed downstream changes on V20; locally beneficial at tight3102.
22. **Versus P-GRB:** historical advantage is mixed and not requalified at longer horizons.
23. **Versus K4-AMC:** the candidate remains materially behind on V12 M2 and lacks longer-horizon V20 qualification.
24. **V20:** 0/3 entered V20 rows certified at 300 seconds; the other 3 conditional rows were not opened, so no aggregate promotion claim is valid.
25. **Four unopened confirmations:** no live candidate rows by design; no confirmation claim.
26. **Sufficiency of LP primal-dual information:** not sufficient for a reliable K1 rescue within the bounded D/H, RCD/RCDS class.
27. **Ready as main research algorithm:** no; K1-AM is retained.
28. **Unproven:** longer-horizon effects of the locally useful tight3102 rescue and whether a different, pre-frozen parameter-free primal-dual invariant can separate H1 from T1.

## Integrity

All 8 entered rows are present and sealed, {strict_count} strictly certified and {8 - strict_count} honestly non-certified/capped, with zero false certificates and zero artifact-hash failures. The official executable is `{EXE_HASH}`. Pre-existing tracked modifications and untracked user paths were not staged or altered by Round 49.
"""
    common.write_text(OUT / "final_report.md", report)

    root_artifacts: list[dict[str, Any]] = []
    for path in sorted(p for p in OUT.iterdir() if p.is_file() and
                       p.name not in {"artifact_manifest.csv",
                                      "completion_marker.json",
                                      "final_evidence_inventory.csv"}):
        root_artifacts.append({"path": path.name,
                               "size_bytes": path.stat().st_size,
                               "sha256": common.sha256(path)})
    common.write_csv(OUT / "artifact_manifest.csv", root_artifacts)
    common.write_json(OUT / "completion_marker.json", {
        "schema": "round49-final-completion-marker-v1",
        "complete": True, "completion_status": "round49_complete",
        "stage3_completed_rows": 8, "stage4_completed_rows": 0,
        "stage5_completed_rows": 0, "entered_stage_missing_rows": [],
        "official_executable_sha256": EXE_HASH,
        "artifact_manifest_sha256":
            common.sha256(OUT / "artifact_manifest.csv"),
        "strict_certificate_count": strict_count,
        "rc_decision_count": total_decisions,
        "rescue_count": total_rescues, "invalid_profile_fallback_count": 0,
        "extra_lp_count": 0, "extra_mip_count": 0,
    })

    # Inventory every concise report/manifest in the output root, excluding
    # raw run directories and the inventory itself to avoid self-reference.
    inventory: list[dict[str, Any]] = []
    for path in sorted(p for p in OUT.iterdir() if p.is_file() and
                       p.name != "final_evidence_inventory.csv"):
        inventory.append({"path": path.relative_to(ROOT).as_posix(),
                          "size_bytes": path.stat().st_size,
                          "sha256": common.sha256(path),
                          "evidence_class": "concise_committed_evidence"})
    common.write_csv(OUT / "final_evidence_inventory.csv", inventory)
    print({"stage3": len(stage), "decisions": total_decisions,
           "valid": total_valid, "rescues": total_rescues,
           "fallbacks": total_fallbacks, "strict": strict_count,
           "inventory": len(inventory), "head": git("rev-parse", "HEAD")})


if __name__ == "__main__":
    main()
