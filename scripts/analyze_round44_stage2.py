#!/usr/bin/env python3
"""Assemble Round 44 Stage 2 pilot evidence and freeze its extension."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

import round43_analysis as historical
import round44_common as common


MAJOR = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
CONTROL = "round39_small_hard_V12_M3_Q30_slot08_seed1288546114"
WITNESSES = (MAJOR, CONTROL)

VARIANTS: list[dict[str, Any]] = [
    {"tag": "na-d1-all", "family": "no-adaptive", "lookahead": "fixed-d1",
     "injection": "all", "scope": "parent", "causal_only": False},
    {"tag": "na-frontier-all", "family": "no-adaptive",
     "lookahead": "frontier-d2", "injection": "all", "scope": "parent",
     "causal_only": False},
    {"tag": "overlay-d1-all-parent", "family": "c6-overlay",
     "lookahead": "fixed-d1", "injection": "all", "scope": "parent",
     "causal_only": False},
    {"tag": "overlay-frontier-all-parent", "family": "c6-overlay",
     "lookahead": "frontier-d2", "injection": "all", "scope": "parent",
     "causal_only": False},
    {"tag": "overlay-frontier-all-nested", "family": "c6-overlay",
     "lookahead": "frontier-d2", "injection": "all", "scope": "nested",
     "causal_only": False},
    {"tag": "overlay-frontier-violated-parent", "family": "c6-overlay",
     "lookahead": "frontier-d2", "injection": "violated", "scope": "parent",
     "causal_only": False},
    {"tag": "overlay-frontier-active-parent", "family": "c6-overlay",
     "lookahead": "frontier-d2", "injection": "active-one", "scope": "parent",
     "causal_only": False},
    {"tag": "overlay-d2-all-reference", "family": "c6-overlay",
     "lookahead": "fixed-d2", "injection": "all", "scope": "parent",
     "causal_only": True},
]
BY_TAG = {row["tag"]: row for row in VARIANTS}
MECHANISM_IDS = [instance_id for instance_id in common.DEVELOPMENT_IDS
                 if common.MECHANISM_ROLES.get(instance_id)]


def run_dir(stage: str, instance_id: str, tag: str) -> Path:
    return common.RUNS / f"{stage}__{instance_id}__{tag}"


def ratio(candidate: float, reference: float) -> float:
    return (candidate + 1.0) / (reference + 1.0)


def gmean(values: list[float]) -> float:
    return math.exp(sum(math.log(value) for value in values) / len(values))


def severe(candidate: dict[str, Any], reference: dict[str, Any]) -> bool:
    work_ratio = ratio(candidate["work"], reference["work"])
    time_ratio = ratio(candidate["process_seconds"],
                       reference["process_seconds"])
    large_delta = (
        candidate["work"] - reference["work"] > 100.0 or
        candidate["process_seconds"] - reference["process_seconds"] >
        max(60.0, 10.0))
    return work_ratio > 1.5 and time_ratio > 1.5 and large_delta


def metrics(stage: str, instance_id: str, tag: str) -> dict[str, Any]:
    directory = run_dir(stage, instance_id, tag)
    marker = common.load_json(directory / "completion_marker.json")
    command = common.load_json(directory / "command.json")
    candidate = historical.load_metrics(directory, tag, "round44_stage2")
    pgrb = historical.historical_reference(instance_id, "P-GRB")
    c6 = historical.historical_reference(instance_id, "C6")
    variant = BY_TAG[tag]
    result = common.load_json(directory / "result.json")
    correctness = (
        marker["complete"] and not command.get("invalidated", False) and
        not candidate["false_certificate"] and
        candidate["parameter_roundtrip_valid"] and
        (not candidate["certified"] or candidate["verified_incumbent"]))
    row = {
        "stage": stage,
        "instance_id": instance_id,
        "role": common.MECHANISM_ROLES.get(instance_id, "pilot_witness"),
        "tag": tag,
        "family": variant["family"],
        "lookahead": variant["lookahead"],
        "injection": variant["injection"],
        "scope": variant["scope"],
        "causal_only": variant["causal_only"],
        "run_id": command["run_id"],
        "decision_identity_sha256": command["candidate_identity"][
            "decision_identity_sha256"],
        "executable_sha256": command["executable_sha256"],
        "complete_marker": marker["complete"],
        "correctness": correctness,
        "certified": candidate["certified"],
        "right_censored": candidate["right_censored"],
        "failure_reason": candidate["failure_reason"],
        "work": candidate["work"],
        "process_seconds": candidate["process_seconds"],
        "nodes": candidate["nodes"],
        "lp_jobs": candidate["lp_jobs"],
        "terminal_mip_jobs": candidate["terminal_mip_jobs"],
        "split_count": candidate["split_count"],
        "final_intervals": candidate["final_intervals"],
        "pgrb_work": pgrb["work"],
        "pgrb_process_seconds": pgrb["process_seconds"],
        "shifted_work_over_pgrb": ratio(candidate["work"], pgrb["work"]),
        "shifted_time_over_pgrb": ratio(
            candidate["process_seconds"], pgrb["process_seconds"]),
        "c6_work": c6["work"],
        "c6_process_seconds": c6["process_seconds"],
        "shifted_work_over_c6": ratio(candidate["work"], c6["work"]),
        "shifted_time_over_c6": ratio(
            candidate["process_seconds"], c6["process_seconds"]),
        "pgrb_advantage_over_candidate":
            (pgrb["work"] + 1.0) / (candidate["work"] + 1.0),
        "severe_pgrb_regression": severe(candidate, pgrb),
        "global_lower_bound": result.get(
            "external_gini_tree_global_lower_bound"),
        "verified_upper_bound": result.get(
            "external_gini_tree_verified_upper_bound"),
    }
    row["major_gate"] = (
        instance_id != MAJOR or
        (row["shifted_work_over_pgrb"] <= 1.05 and
         row["shifted_time_over_pgrb"] <= 1.05))
    row["control_advantage_retained"] = (
        instance_id != CONTROL or
        row["pgrb_advantage_over_candidate"] >= 2.0)
    return row


def pilot_rows() -> list[dict[str, Any]]:
    return [metrics("stage2-pilot", instance_id, variant["tag"])
            for variant in VARIANTS for instance_id in WITNESSES]


def select_pilot(rows: list[dict[str, Any]], family: str) -> str:
    candidates: list[tuple[tuple[Any, ...], str]] = []
    for variant in VARIANTS:
        if variant["family"] != family or variant["causal_only"]:
            continue
        paired = [row for row in rows if row["tag"] == variant["tag"]]
        if len(paired) != 2 or not all(row["correctness"] for row in paired):
            continue
        major = next(row for row in paired if row["instance_id"] == MAJOR)
        control = next(row for row in paired if row["instance_id"] == CONTROL)
        key = (
            not major["major_gate"],
            major["severe_pgrb_regression"],
            not control["control_advantage_retained"],
            major["shifted_work_over_pgrb"],
            major["shifted_time_over_pgrb"],
            control["shifted_work_over_pgrb"],
            0 if variant["lookahead"] == "frontier-d2" else 1,
            variant["tag"],
        )
        candidates.append((key, variant["tag"]))
    if not candidates:
        raise RuntimeError(f"no technically admissible {family} pilot")
    return min(candidates)[1]


def report_table(rows: list[dict[str, Any]], title: str,
                 observation: str) -> str:
    lines = [f"# {title}", "", observation, "",
             "| variant | witness | certified | Work/P-GRB | time/P-GRB | splits | terminal MIPs |",
             "|---|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(
            f"| {row['tag']} | {row['role']} | {row['certified']} | "
            f"{row['shifted_work_over_pgrb']:.4f} | "
            f"{row['shifted_time_over_pgrb']:.4f} | "
            f"{row['split_count']} | {row['terminal_mip_jobs']} |")
    return "\n".join(lines) + "\n"


def freeze_pilots(rows: list[dict[str, Any]]) -> dict[str, Any]:
    noadaptive = select_pilot(rows, "no-adaptive")
    overlay = select_pilot(rows, "c6-overlay")
    executable_hashes = sorted({row["executable_sha256"] for row in rows})
    if len(executable_hashes) != 1:
        raise RuntimeError(f"Stage 2 executable drift: {executable_hashes}")
    freeze = {
        "schema": "round44-stage2-retention-freeze-v1",
        "frozen_before_mechanism_extension": True,
        "mechanism_results_observed": False,
        "validation_observed": False,
        "holdout_observed": False,
        "pilot_rows": len(rows),
        "retained_variant_count": 2,
        "retained_tags": [noadaptive, overlay],
        "best_pilot_noadaptive_tag": noadaptive,
        "best_pilot_overlay_tag": overlay,
        "retention_order": [
            "correctness", "major/P-GRB repair",
            "no severe P-GRB regression", "C6-advantage retention",
            "worst shifted P-GRB ratio", "shifted Work geometric mean",
            "shifted time geometric mean", "simplicity"],
        "executable_sha256": executable_hashes[0],
    }
    common.write_json(common.OUT / "stage2_retention_freeze.json", freeze)
    return freeze


def finalize(freeze: dict[str, Any]) -> None:
    retained = freeze["retained_tags"]
    rows = [metrics("stage2-mechanism", instance_id, tag)
            for tag in retained for instance_id in MECHANISM_IDS]
    common.write_csv(common.OUT / "stage2_mechanism_results.csv", rows)
    summaries: list[dict[str, Any]] = []
    for tag in retained:
        selected = [row for row in rows if row["tag"] == tag]
        major = next(row for row in selected if row["instance_id"] == MAJOR)
        control = next(row for row in selected if row["instance_id"] == CONTROL)
        summaries.append({
            "tag": tag,
            "family": BY_TAG[tag]["family"],
            "correctness": all(row["correctness"] for row in selected),
            "major_gate": major["major_gate"],
            "no_severe_pgrb_regression": not any(
                row["severe_pgrb_regression"] for row in selected),
            "c6_advantage_retained": control["control_advantage_retained"],
            "worst_shifted_work_over_pgrb": max(
                row["shifted_work_over_pgrb"] for row in selected),
            "shifted_work_gmean": gmean([
                row["shifted_work_over_pgrb"] for row in selected]),
            "shifted_time_gmean": gmean([
                row["shifted_time_over_pgrb"] for row in selected]),
            "certified_rows": sum(row["certified"] for row in selected),
            "row_count": len(selected),
        })
    selection = {
        "schema": "round44-stage2-selection-v1",
        "retention_freeze": common.relative(
            common.OUT / "stage2_retention_freeze.json"),
        "mechanism6_instances": MECHANISM_IDS,
        "mechanism6_summaries": summaries,
        "best_noadaptive_tag": freeze["best_pilot_noadaptive_tag"],
        "best_unchanged_c6_envelope_tag":
            freeze["best_pilot_overlay_tag"],
        "stage3_envelope_policy": BY_TAG[
            freeze["best_pilot_overlay_tag"]],
        "selected_before_stage3_runs": True,
        "stage3_results_observed": False,
        "validation_observed": False,
        "holdout_observed": False,
    }
    common.write_json(common.OUT / "stage2_selection.json", selection)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args()
    rows = pilot_rows()
    common.write_csv(common.OUT / "stage2_pilot_results.csv", rows)
    freeze = freeze_pilots(rows)
    common.write_text(
        common.OUT / "envelope_injection_ablation.md",
        report_table(
            [row for row in rows if row["lookahead"] == "frontier-d2"],
            "Round 44 envelope-injection ablation",
            "All, violated-only, and active-one policies use the same frozen "
            "frontier-d2 profiles; exact proof cost decides the ablation."))
    common.write_text(
        common.OUT / "propagation_scope_ablation.md",
        report_table(
            [row for row in rows if row["tag"] in {
                "overlay-frontier-all-parent",
                "overlay-frontier-all-nested"}],
            "Round 44 propagation-scope ablation",
            "Parent and nested scope differ only in valid descendant "
            "inheritance of source-interval envelope facets."))
    common.write_text(
        common.OUT / "lookahead_policy_ablation.md",
        report_table(rows, "Round 44 lookahead-policy ablation",
                     "Fixed-d1, frontier-d2, and the fixed-d2 causal reference "
                     "are compared under the sealed Stage 2 solver contract."))
    if args.finalize:
        finalize(freeze)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
