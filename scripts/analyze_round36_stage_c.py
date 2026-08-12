#!/usr/bin/env python3
"""Analyze the separately frozen Round 36 Stage C validation matrix."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import round35_common as r35
import round36_stage_c_common as common


HGA_FILES = {
    "qualification_1800": r35.OUT / "simple_vs_hga_1800s.csv",
    "independent_v50_3600": r35.OUT / "simple_vs_hga_3600s.csv",
}
PGRB_FILES = {
    "qualification_1800": r35.OUT / "simple_vs_pgrb_1800s.csv",
    "independent_v50_3600": r35.OUT / "simple_vs_pgrb_3600s.csv",
}
SIMPLE_FILES = {
    "qualification_1800": r35.OUT / "round35_1800s_matrix.csv",
    "independent_v50_3600": r35.OUT / "round35_3600s_v50_matrix.csv",
}


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() == "true"


def number(value: Any, default: float = math.nan) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_gap(upper: float, lower: float) -> float:
    return max(0.0, (upper - lower) / max(1e-12, abs(upper)))


def comparison_outcome(candidate_strict: bool, comparator_strict: bool,
                       candidate_gap: float, comparator_gap: float,
                       tolerance: float = 1e-9) -> str:
    if candidate_strict != comparator_strict:
        return "candidate_win" if candidate_strict else "comparator_win"
    delta = candidate_gap - comparator_gap
    if delta < -tolerance:
        return "candidate_win"
    if delta > tolerance:
        return "comparator_win"
    return "tie"


def keyed(path: Path) -> dict[str, dict[str, str]]:
    return {row["instance_id"]: row for row in common.csv_rows(path)}


def frozen_audit() -> dict[str, Any]:
    manifest = common.load_json(common.FROZEN_MANIFEST)
    candidate = common.load_json(common.CANDIDATE)
    contract_fix = common.load_json(common.CONTRACT_FIX_AUDIT)
    invalidated_attempt = common.load_json(
        common.INVALIDATED_ATTEMPT_RECORD)
    identities = {
        "candidate_definition": (
            common.sha256(common.CANDIDATE) ==
            manifest["candidate_definition_sha256"]),
        "validation_matrix": (
            common.sha256(common.MATRIX) ==
            manifest["validation_matrix_sha256"]),
        "command_freeze": (
            common.sha256(common.COMMAND_FREEZE) ==
            manifest["command_freeze_sha256"]),
        "executable": (
            common.sha256(common.EXE) ==
            manifest["gurobi_executable_sha256"]),
        "stage_b_executable": (
            common.sha256(common.STAGE_B_EXE) ==
            manifest["stage_b_executable_sha256"]),
        "stage_b_decision": (
            common.sha256(common.OUT / "final_audit_decision.json") ==
            manifest["stage_b_final_decision_sha256"]),
        "candidate_frozen_before_results": (
            candidate.get("frozen_before_stage_c_results") is True),
        "candidate_executable_provenance": (
            candidate.get("stage_b_executable_sha256") ==
            manifest["stage_b_executable_sha256"] and
            candidate.get("stage_c_executable_sha256") ==
            manifest["gurobi_executable_sha256"]),
        "contract_fix_audit": (
            common.sha256(common.CONTRACT_FIX_AUDIT) ==
            manifest["contract_fix_audit_sha256"] and
            contract_fix.get("passed") is True and
            contract_fix.get("stage_b_executable_unchanged") is True and
            contract_fix.get("executables_are_distinct") is True and
            contract_fix.get("baseline_equivalence", {}).get(
                "all_identical") is True),
        "invalidated_attempt": (
            common.sha256(common.INVALIDATED_ATTEMPT_RECORD) ==
            manifest["invalidated_attempt_record_sha256"] and
            invalidated_attempt.get("invalidated") is True and
            invalidated_attempt.get("completed_valid_rows") == 18 and
            invalidated_attempt.get("failed_serial_order") == 19 and
            invalidated_attempt.get("row_reuse_permitted") is False),
        "source_tree": all(
            (common.ROOT / path).is_file() and
            common.sha256(common.ROOT / path) == expected
            for path, expected in manifest["source_file_sha256"].items()),
    }
    comparator_hashes = manifest["historical_comparator_sha256"]
    identities["historical_comparators"] = all(
        (common.ROOT / path).is_file() and
        common.sha256(common.ROOT / path) == expected
        for path, expected in comparator_hashes.items())
    identities["all"] = all(identities.values())
    return identities


def per_run(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    matrix = {row["run_id"]: row for row in common.csv_rows(common.MATRIX)}
    output: list[dict[str, Any]] = []
    for row in rows:
        design = matrix[row["run_id"]]
        output.append({
            "round_id": 36,
            "stage": "C",
            "serial_order": int(row["serial_order"]),
            "validation_stage": row["validation_stage"],
            "run_id": row["run_id"],
            "instance_id": row["instance_id"],
            "V": int(row["V"]),
            "M": int(row["M"]),
            "scenario": row["scenario"],
            "candidate": "C6-BEST-PROOF-WIDE-ANCHOR-PROOF-NORM",
            "status": row.get("status", ""),
            "strict_certificate": truth(row.get(
                "strict_certified_original_problem")),
            "verified_upper_bound": number(row.get(
                "verified_upper_bound")),
            "valid_lower_bound": number(row.get("valid_lower_bound")),
            "final_gap": number(row.get("final_gap")),
            "process_seconds": number(row.get(
                "process_entry_time_seconds")),
            "runner_wall_seconds": number(row.get("runner_wall_seconds")),
            "proof_incumbent_launch": number(row.get(
                "proof_incumbent_launch")),
            "decomposition_anchor_launch": number(row.get(
                "decomposition_anchor_launch")),
            "anchor_safety_valid": truth(row.get("anchor_safety_valid")),
            "arm_contract_matches": truth(row.get("arm_contract_matches")),
            "root_coverage_valid": truth(row.get("root_coverage_valid")),
            "parent_child_coverage_valid": truth(row.get(
                "parent_child_coverage_valid")),
            "result_sha256": row.get("result_sha256", ""),
            "matrix_instance_sha256_matches": (
                row.get("instance_sha256") == design["instance_sha256"]),
        })
    return output


def comparisons(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources = {
        stage: {
            "C6-HGA-FULL": keyed(HGA_FILES[stage]),
            "C6-SIMPLE-START": keyed(SIMPLE_FILES[stage]),
            "P-GRB": keyed(PGRB_FILES[stage]),
        }
        for stage in HGA_FILES
    }
    output: list[dict[str, Any]] = []
    for candidate in candidate_rows:
        stage = candidate["validation_stage"]
        instance = candidate["instance_id"]
        hga = sources[stage]["C6-HGA-FULL"][instance]
        simple = sources[stage]["C6-SIMPLE-START"][instance]
        pgrb = sources[stage]["P-GRB"][instance]
        records = {
            "C6-HGA-FULL": {
                "source": HGA_FILES[stage],
                "compatibility": hga["comparison_compatibility"],
                "common_ub": number(hga["common_verified_ub"]),
                "lower": number(hga["comparator_valid_final_lb"]),
                "strict": truth(hga["comparator_strict_certificate"]),
                "seconds": number(hga["comparator_process_seconds"]),
                "work": number(hga["comparator_work"]),
                "nodes": number(hga["comparator_nodes"]),
                "run_id": hga["historical_run_id"],
            },
            "C6-SIMPLE-START": {
                "source": SIMPLE_FILES[stage],
                "compatibility": "compatible",
                "source_compatibility_label": simple[
                    "comparison_compatibility"],
                "common_ub": number(simple["common_verified_ub"]),
                "lower": number(simple["valid_final_lb"]),
                "strict": truth(simple["strict_certificate"]),
                "seconds": number(simple["end_to_end_process_seconds"]),
                "work": number(simple["total_work"]),
                "nodes": number(simple["nodes"]),
                "run_id": simple["run_id"],
            },
            "P-GRB": {
                "source": PGRB_FILES[stage],
                "compatibility": pgrb["comparison_compatibility"],
                "common_ub": number(pgrb["common_verified_ub"]),
                "lower": number(pgrb["comparator_valid_final_lb"]),
                "strict": truth(pgrb["comparator_strict_certificate"]),
                "seconds": number(pgrb["comparator_process_seconds"]),
                "work": number(pgrb["comparator_work"]),
                "nodes": number(pgrb["comparator_nodes"]),
                "run_id": pgrb["historical_run_id"],
            },
        }
        for comparator, record in records.items():
            common_ub = min(candidate["verified_upper_bound"],
                            record["common_ub"])
            candidate_gap = safe_gap(common_ub,
                                     candidate["valid_lower_bound"])
            comparator_gap = safe_gap(common_ub, record["lower"])
            outcome = comparison_outcome(
                candidate["strict_certificate"], record["strict"],
                candidate_gap, comparator_gap)
            output.append({
                "round_id": 36,
                "stage": "C",
                "validation_stage": stage,
                "instance_id": instance,
                "V": candidate["V"], "M": candidate["M"],
                "scenario": candidate["scenario"],
                "candidate": candidate["candidate"],
                "comparator": comparator,
                "comparison_compatibility": record["compatibility"],
                "source_compatibility_label": record.get(
                    "source_compatibility_label", record["compatibility"]),
                "historical_source": common.relative(record["source"]),
                "historical_run_id": record["run_id"],
                "common_verified_ub": common_ub,
                "candidate_valid_lower_bound": candidate[
                    "valid_lower_bound"],
                "comparator_valid_lower_bound": record["lower"],
                "candidate_common_ub_gap": candidate_gap,
                "comparator_common_ub_gap": comparator_gap,
                "candidate_minus_comparator_gap": (
                    candidate_gap - comparator_gap),
                "candidate_strict_certificate": candidate[
                    "strict_certificate"],
                "comparator_strict_certificate": record["strict"],
                "certificate_regression": (
                    record["strict"] and not candidate[
                        "strict_certificate"]),
                "outcome": outcome,
                "candidate_process_seconds": candidate["process_seconds"],
                "comparator_process_seconds": record["seconds"],
                "candidate_over_comparator_process_ratio": (
                    candidate["process_seconds"] / record["seconds"]
                    if record["seconds"] > 0 else math.nan),
                "comparator_work": record["work"],
                "comparator_nodes": record["nodes"],
                "wall_clock_monotonicity_claimed": False,
            })
    return output


def group_summaries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for comparator in ("C6-HGA-FULL", "C6-SIMPLE-START", "P-GRB"):
        selected = [row for row in rows if row["comparator"] == comparator]
        for grouping in ("all", "validation_stage", "scenario", "V", "M"):
            groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in selected:
                value = "all" if grouping == "all" else str(row[grouping])
                groups[value].append(row)
            for value, group in sorted(groups.items()):
                non_ties = [row for row in group if row["outcome"] != "tie"]
                output.append({
                    "comparison": f"candidate_vs_{comparator}",
                    "grouping": grouping,
                    "group_value": value,
                    "rows": len(group),
                    "candidate_wins": sum(row["outcome"] == "candidate_win"
                                          for row in group),
                    "comparator_wins": sum(
                        row["outcome"] == "comparator_win" for row in group),
                    "ties": sum(row["outcome"] == "tie" for row in group),
                    "non_tie_candidate_win_fraction": (
                        sum(row["outcome"] == "candidate_win" for row in group)
                        / len(non_ties) if non_ties else math.nan),
                    "certificate_regressions": sum(
                        row["certificate_regression"] for row in group),
                    "median_candidate_minus_comparator_gap": statistics.median(
                        row["candidate_minus_comparator_gap"] for row in group),
                    "median_candidate_over_comparator_process_ratio":
                        statistics.median(
                            row["candidate_over_comparator_process_ratio"]
                            for row in group),
                    "all_historical_rows_compatible": all(
                        row["comparison_compatibility"] == "compatible"
                        for row in group),
                })
    return output


def final_decision(candidate_rows: list[dict[str, Any]],
                   comparison_rows: list[dict[str, Any]],
                   frozen: dict[str, Any], complete: bool) -> dict[str, Any]:
    hga = [row for row in comparison_rows
           if row["comparator"] == "C6-HGA-FULL"]
    stages: dict[str, dict[str, Any]] = {}
    for stage in HGA_FILES:
        group = [row for row in hga if row["validation_stage"] == stage]
        non_ties = [row for row in group if row["outcome"] != "tie"]
        stages[stage] = {
            "rows": len(group),
            "candidate_wins": sum(row["outcome"] == "candidate_win"
                                  for row in group),
            "comparator_wins": sum(row["outcome"] == "comparator_win"
                                   for row in group),
            "ties": sum(row["outcome"] == "tie" for row in group),
            "non_tie_candidate_win_fraction": (
                sum(row["outcome"] == "candidate_win" for row in group) /
                len(non_ties) if non_ties else 0.0),
            "median_candidate_minus_comparator_gap": (
                statistics.median(row["candidate_minus_comparator_gap"]
                                  for row in group) if group else math.nan),
            "certificate_regressions": sum(
                row["certificate_regression"] for row in group),
        }
    false_certificates = sum(
        row["strict_certificate"] and row["final_gap"] > 1e-6
        for row in candidate_rows)
    valid_rows = sum(
        row["anchor_safety_valid"] and row["arm_contract_matches"] and
        row["root_coverage_valid"] and row["parent_child_coverage_valid"]
        for row in candidate_rows)
    performance_gate = (
        complete and valid_rows == common.EXPECTED_ROWS and
        false_certificates == 0 and
        all(stages[stage]["non_tie_candidate_win_fraction"] >= 0.60
            and stages[stage]["median_candidate_minus_comparator_gap"] <= 0.0
            for stage in stages) and
        sum(stage["certificate_regressions"]
            for stage in stages.values()) == 0)
    if performance_gate:
        recommendation = (
            "Keep C6-HGA-FULL unchanged; the candidate passes the frozen "
            "historical-comparator gate and merits a later contemporaneous "
            "publication-grade validation, without automatic promotion.")
    else:
        recommendation = (
            "Keep C6-HGA-FULL unchanged; the geometry mechanism remains "
            "scientifically identified, but the candidate does not pass the "
            "frozen broad performance gate and should not be promoted.")
    return {
        "schema": "round36-stage-c-final-audit-v2",
        "round_id": 36,
        "stage": "C",
        "completed": complete,
        "expected_rows": common.EXPECTED_ROWS,
        "completed_rows": len(candidate_rows),
        "valid_rows": valid_rows,
        "strict_certificates": sum(row["strict_certificate"]
                                   for row in candidate_rows),
        "valid_nocertificates": sum(not row["strict_certificate"]
                                    for row in candidate_rows),
        "false_certificate_count": false_certificates,
        "separately_frozen_validation": frozen["all"],
        "frozen_identity_audit": frozen,
        "candidate": "C6-BEST-PROOF-WIDE-ANCHOR-PROOF-NORM",
        "stage_b_classification": "decomposition_geometry_dominant",
        "historical_comparator_compatibility_valid": all(
            row["comparison_compatibility"] == "compatible"
            for row in comparison_rows),
        "candidate_vs_hga_gate_by_stage": stages,
        "predeclared_performance_gate_passed": performance_gate,
        "automatic_promotion_performed": False,
        "rho_sensitivity_performed": False,
        "instance_dependent_dispatch_introduced": False,
        "validated_gurobi_mainline": "C6-HGA-FULL",
        "recommendation": recommendation,
    }


def report(decision: dict[str, Any], groups: list[dict[str, Any]]) -> str:
    overall = [row for row in groups if row["grouping"] == "all"]
    lines = [
        "# Round 36 Stage C broader validation",
        "",
        "The separately frozen candidate is "
        "`C6-BEST-PROOF-WIDE-ANCHOR-PROOF-NORM` (BW-P): the best verified "
        "startup incumbent controls proof, the wider verified value fixes "
        "decomposition geometry, and split normalization uses the proof "
        "incumbent. K=4 and rho=0.01 remain fixed.",
        "",
        f"Completed rows: {decision['completed_rows']}/"
        f"{decision['expected_rows']}; strict certificates: "
        f"{decision['strict_certificates']}; valid noncertificates: "
        f"{decision['valid_nocertificates']}; false certificates: "
        f"{decision['false_certificate_count']}.",
        "",
        "## Historical-comparator endpoint summary",
        "",
        "| Comparator | Candidate wins | Comparator wins | Ties | "
        "Certificate regressions | Median candidate-minus-comparator gap |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in overall:
        lines.append(
            f"| {row['comparison'].removeprefix('candidate_vs_')} | "
            f"{row['candidate_wins']} | {row['comparator_wins']} | "
            f"{row['ties']} | {row['certificate_regressions']} | "
            f"{row['median_candidate_minus_comparator_gap']:.9g} |")
    lines.extend([
        "",
        "Historical comparisons are used only where the Round 35 "
        "compatibility audit marks them compatible. Wall-clock monotonicity "
        "is not claimed; the frozen gate prioritizes certificate state and "
        "common-UB proof gaps.",
        "",
        "## Decision",
        "",
        decision["recommendation"],
        "",
        "No automatic promotion, rho tuning, K change, or instance-dependent "
        "dispatch was performed.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    if not common.SUMMARY.is_file():
        raise SystemExit("Stage C runner summary is absent")
    summary = common.csv_rows(common.SUMMARY)
    summary.sort(key=lambda row: int(row["serial_order"]))
    complete = len(summary) == common.EXPECTED_ROWS
    if not complete and not args.allow_partial:
        raise SystemExit(f"Stage C incomplete: {len(summary)}/47 rows")
    frozen = frozen_audit()
    candidate_rows = per_run(summary)
    comparison_rows = comparisons(candidate_rows)
    groups = group_summaries(comparison_rows)
    decision = final_decision(candidate_rows, comparison_rows, frozen,
                              complete)
    prefix = "" if complete else "interim_"
    common.write_csv(common.OUT / f"{prefix}stage_c_per_run_results.csv",
                     candidate_rows)
    common.write_csv(common.OUT / f"{prefix}stage_c_comparisons.csv",
                     comparison_rows)
    common.write_csv(common.OUT / f"{prefix}stage_c_group_summaries.csv",
                     groups)
    audit_path = (common.FINAL_AUDIT if complete else
                  common.OUT / "interim_stage_c_final_audit.json")
    report_path = (common.FINAL_REPORT if complete else
                   common.OUT / "interim_stage_c_final_report.md")
    common.write_json(audit_path, decision)
    report_path.write_text(report(decision, groups), encoding="utf-8",
                           newline="\n")
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
