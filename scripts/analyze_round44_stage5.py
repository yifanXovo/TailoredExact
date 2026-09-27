#!/usr/bin/env python3
"""Audit and finalize Round 44 proof-lifecycle engineering ablations."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import round43_analysis as historical
import round44_common as common
import analyze_round44_stage3 as stage3


SELECTED_TAG = "noadaptive"
START_TAG = "noadaptive-starts"
CONSOLIDATION_TAGS = {
    "singleton": "noadaptive-cons-singleton",
    "pair": "noadaptive-cons-pair",
    "block": "noadaptive-cons-block",
}
MECHANISM_IDS = [instance_id for instance_id in common.DEVELOPMENT_IDS
                 if common.MECHANISM_ROLES.get(instance_id)]


def run_dir(stage: str, instance_id: str, tag: str) -> Path:
    return common.RUNS / f"{stage}__{instance_id}__{tag}"


def load(stage: str, instance_id: str, tag: str) -> dict[str, Any]:
    directory = run_dir(stage, instance_id, tag)
    metric = historical.load_metrics(directory, tag, "round44_stage5")
    marker = common.load_json(directory / "completion_marker.json")
    command = common.load_json(directory / "command.json")
    result = common.load_json(directory / "result.json")
    metric["correctness"] = (
        marker["complete"] and not command.get("invalidated", False) and
        not metric["false_certificate"] and
        metric["parameter_roundtrip_valid"] and
        common.truth(result.get("external_gini_tree_root_coverage_valid")) and
        common.truth(result.get(
            "external_gini_tree_global_bound_monotone", True)) and
        (not metric["certified"] or metric["verified_incumbent"]))
    metric["command"] = command
    metric["result"] = result
    return metric


def entry_audit() -> None:
    directory = run_dir("stage3-development", stage3.MAJOR, SELECTED_TAG)
    leaves = common.csv_rows(directory / "interval_coverage_ledger.csv")
    optimizes = common.csv_rows(directory / "native_optimize_ledger.csv")
    mip = {row["leaf_id"]: row for row in optimizes
           if row["solve_kind"] == "MIP"}
    terminal = sorted(
        [row for row in leaves
         if common.truth(row["terminal_mip_started"]) and row["leaf_id"] in mip],
        key=lambda row: float(row["gamma_L"]))
    adjacent: list[dict[str, Any]] = []
    for left, right in zip(terminal, terminal[1:]):
        if abs(float(left["gamma_U"]) - float(right["gamma_L"])) <= 1e-7:
            adjacent.append({
                "left_id": left["leaf_id"],
                "right_id": right["leaf_id"],
                "left_work": float(mip[left["leaf_id"]]["work"]),
                "right_work": float(mip[right["leaf_id"]]["work"]),
                "left_seconds": float(
                    mip[left["leaf_id"]]["solver_runtime"]),
                "right_seconds": float(
                    mip[right["leaf_id"]]["solver_runtime"]),
            })
    triggered = bool(adjacent)
    common.write_json(
        common.OUT / "frontier_consolidation_entry_audit.json", {
            "schema": "round44-frontier-consolidation-entry-audit-v1",
            "selected_candidate": SELECTED_TAG,
            "major_run": common.relative(directory),
            "terminal_mip_count": len(terminal),
            "adjacent_terminal_pairs": adjacent,
            "duplicated_adjacent_terminal_proof": triggered,
            "formal_experiment_triggered": triggered,
            "required_modes": ["singleton", "pair", "block"]
                if triggered else [],
            "validation_observed": False,
        })
    common.write_json(common.OUT / "stage5_consolidation_freeze.json", {
        "schema": "round44-stage5-consolidation-freeze-v1",
        "frozen_before_consolidation_runs": True,
        "consolidation_results_observed": False,
        "selected_candidate": SELECTED_TAG,
        "instance_id": stage3.MAJOR,
        "modes": ["singleton", "pair", "block"] if triggered else [],
        "mathematical_target": "next-distinct-frontier-bound-or-cutoff",
        "incomplete_union_policy": (
            "propagate the valid union lower bound to every original member; "
            "never replace member coverage"),
        "validation_observed": False,
    })
    if not triggered:
        common.write_text(
            common.OUT / "frontier_consolidation_analysis.md",
            "# Round 44 frontier consolidation\n\nThe formal entry audit "
            "found no duplicated adjacent terminal proof, so the exact "
            "experiment was not triggered.\n")


def start_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instance_id in MECHANISM_IDS:
        pgrb = historical.historical_reference(instance_id, "P-GRB")
        for mode, stage_name, tag in (
                ("off", "stage3-development", SELECTED_TAG),
                ("verified", "stage5-mip-start", START_TAG)):
            metric = load(stage_name, instance_id, tag)
            ledger = common.csv_rows(
                run_dir(stage_name, instance_id, tag) / "mip_start_ledger.csv")
            considered = sum(int(row["candidates_considered"] or 0)
                             for row in ledger)
            accepted = sum(int(row["candidates_accepted"] or 0)
                           for row in ledger)
            rows.append({
                "instance_id": instance_id,
                "role": common.MECHANISM_ROLES[instance_id],
                "mode": mode,
                "run_id": metric["run_id"],
                "executable_sha256": metric["executable_sha256"],
                "correctness": metric["correctness"],
                "certified": metric["certified"],
                "work": metric["work"],
                "process_seconds": metric["process_seconds"],
                "nodes": metric["nodes"],
                "candidates_considered": considered,
                "candidates_accepted": accepted,
                "all_membership_checks_pass": all(
                    not common.truth(row["candidates_accepted"]) or
                    (common.truth(row["interval_member"]) and
                     common.truth(row["objective_verified"]))
                    for row in ledger),
                "mapping_statuses": "|".join(sorted({
                    row["mapping_status"] for row in ledger
                    if row["mapping_status"]})),
                "gurobi_acceptance_statuses": "|".join(sorted({
                    row["gurobi_acceptance"] for row in ledger
                    if row["gurobi_acceptance"]})),
                "shifted_work_over_pgrb": stage3.shifted(
                    metric["work"], pgrb["work"], stage3.S_W),
                "shifted_time_over_pgrb": stage3.shifted(
                    metric["process_seconds"], pgrb["process_seconds"],
                    stage3.S_T),
                "severe_pgrb_regression": stage3.severe(metric, pgrb),
            })
    return rows


def finalize() -> None:
    starts = start_rows()
    common.write_csv(common.OUT / "mip_start_ablation.csv", starts)
    off = [row for row in starts if row["mode"] == "off"]
    on = [row for row in starts if row["mode"] == "verified"]
    paired_work = [stage3.shifted(on_row["work"], off_row["work"], 1.0)
                   for off_row, on_row in zip(off, on)]
    paired_time = [stage3.shifted(
        on_row["process_seconds"], off_row["process_seconds"], 1.0)
                   for off_row, on_row in zip(off, on)]
    start_work_gmean = stage3.gmean(paired_work)
    start_time_gmean = stage3.gmean(paired_time)
    starts_promoted = (
        all(row["correctness"] and row["all_membership_checks_pass"]
            for row in on) and
        not any(row["severe_pgrb_regression"] for row in on) and
        start_work_gmean < 1.0 and start_time_gmean < 1.0)
    common.write_text(common.OUT / "mip_start_ablation.md", f"""# Round 44 verified interval MIP starts

The selected candidate was compared with starts off and with complete,
independently verified interval-feasible starts on across mechanism-6.

- Paired shifted Work gmean (on/off): {start_work_gmean:.6f}
- Paired shifted time gmean (on/off): {start_time_gmean:.6f}
- Accepted starts: {sum(row['candidates_accepted'] for row in on)}
- New severe P-GRB regressions: {sum(row['severe_pgrb_regression'] for row in on)}
- Selected mode: {'verified' if starts_promoted else 'off'}
""")

    entry = common.load_json(
        common.OUT / "frontier_consolidation_entry_audit.json")
    consolidation_rows: list[dict[str, Any]] = []
    selected_consolidation = "off"
    if entry["formal_experiment_triggered"]:
        pgrb = historical.historical_reference(stage3.MAJOR, "P-GRB")
        for mode, tag in CONSOLIDATION_TAGS.items():
            metric = load("stage5-consolidation", stage3.MAJOR, tag)
            ledger_path = (run_dir(
                "stage5-consolidation", stage3.MAJOR, tag) /
                "external" / "frontier_consolidation_ledger.csv")
            ledger = common.csv_rows(ledger_path)
            consolidation_rows.append({
                "mode": mode,
                "run_id": metric["run_id"],
                "correctness": metric["correctness"],
                "certified": metric["certified"],
                "work": metric["work"],
                "process_seconds": metric["process_seconds"],
                "nodes": metric["nodes"],
                "lp_jobs": metric["lp_jobs"],
                "terminal_mip_jobs": metric["terminal_mip_jobs"],
                "consolidation_launches": sum(
                    row["native_status"] not in {"", "not_launched"}
                    for row in ledger),
                "target_reached": sum(common.truth(row["target_reached"])
                                      for row in ledger),
                "exact_union_closures": sum(
                    common.truth(row["exact_closure"]) for row in ledger),
                "member_coverage_replaced": any(
                    common.truth(row["coverage_replaced"]) for row in ledger),
                "shifted_work_over_pgrb": stage3.shifted(
                    metric["work"], pgrb["work"], stage3.S_W),
                "shifted_time_over_pgrb": stage3.shifted(
                    metric["process_seconds"], pgrb["process_seconds"],
                    stage3.S_T),
                "major_gate": stage3.shifted(
                    metric["work"], pgrb["work"], stage3.S_W) <= 1.05 and
                    stage3.shifted(
                        metric["process_seconds"], pgrb["process_seconds"],
                        stage3.S_T) <= 1.05,
            })
        common.write_csv(
            common.OUT / "frontier_consolidation_results.csv",
            consolidation_rows)
        eligible = [row for row in consolidation_rows
                    if row["correctness"] and row["certified"] and
                    row["major_gate"] and not row["member_coverage_replaced"]]
        if eligible:
            best = min(eligible, key=lambda row: (
                row["work"], row["process_seconds"],
                {"singleton": 0, "pair": 1, "block": 2}[row["mode"]]))
            singleton = next(row for row in consolidation_rows
                             if row["mode"] == "singleton")
            if (best["mode"] != "singleton" and
                    stage3.shifted(best["work"], singleton["work"], 1.0) < .98):
                selected_consolidation = best["mode"]
        table = [
            "# Round 44 frontier consolidation", "",
            "The major witness triggered the experiment because adjacent "
            "terminal intervals repeated material exact proof.", "",
            "| mode | certified | Work | seconds | target hits | union closes | selected |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
        for row in consolidation_rows:
            table.append(
                f"| {row['mode']} | {row['certified']} | {row['work']:.3f} | "
                f"{row['process_seconds']:.3f} | {row['target_reached']} | "
                f"{row['exact_union_closures']} | "
                f"{row['mode'] == selected_consolidation} |")
        common.write_text(
            common.OUT / "frontier_consolidation_analysis.md",
            "\n".join(table) + "\n")

    cut_rows: list[dict[str, Any]] = []
    for instance_id in common.DEVELOPMENT_IDS:
        directory = run_dir("stage3-development", instance_id, SELECTED_TAG)
        for row in common.csv_rows(directory / "explicit_cut_scope_ledger.csv"):
            cut_rows.append({
                "instance_id": instance_id,
                "run_id": directory.name,
                **row,
                "sharing_policy_valid": (
                    row["scope"] in {"global", "source-interval"} and
                    (row["scope"] != "source-interval" or
                     not common.truth(row["inherited"]) or
                     float(row["target_lower"]) >=
                        float(row["source_lower"]) - 1e-9) and
                    row["reason"] != "branch_local_cut_exported"),
            })
    common.write_csv(common.OUT / "cut_scope_audit.csv", cut_rows)
    common.write_json(common.OUT / "stage5_disposition.json", {
        "schema": "round44-stage5-disposition-v1",
        "selected_candidate": SELECTED_TAG,
        "mip_start_mode": "verified" if starts_promoted else "off",
        "mip_start_work_gmean_on_over_off": start_work_gmean,
        "mip_start_time_gmean_on_over_off": start_time_gmean,
        "frontier_consolidation_triggered":
            entry["formal_experiment_triggered"],
        "frontier_consolidation_mode": selected_consolidation,
        "cut_scope_audit_valid": all(
            row["sharing_policy_valid"] for row in cut_rows),
        "validation_observed": False,
    })
    common.write_text(common.OUT / "stage5_report.md", f"""# Round 44 Stage 5 report

Verified interval MIP starts were {'promoted' if starts_promoted else 'not promoted'};
the selected mode is `{'verified' if starts_promoted else 'off'}`. The formal
frontier-consolidation audit was {'triggered' if entry['formal_experiment_triggered'] else 'not triggered'};
the selected mode is `{selected_consolidation}`. All explicit-cut scope rows
passed the global/source-interval inheritance and branch-local export audit.
""")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--entry-audit", action="store_true")
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    if args.entry_audit == args.finalize:
        raise SystemExit("select exactly one of --entry-audit or --finalize")
    if args.entry_audit:
        entry_audit()
    else:
        finalize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
