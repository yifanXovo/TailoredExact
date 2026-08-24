#!/usr/bin/env python3
"""Freeze and analyze the Round 44 conservative-refinement screen."""

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
MECHANISM_IDS = [instance_id for instance_id in common.DEVELOPMENT_IDS
                 if common.MECHANISM_ROLES.get(instance_id)]

VARIANTS: list[dict[str, Any]] = [
    {"tag": "veto-f05", "family": "veto", "rho_f": .5,
     "rho_m": .007, "rho_h": .0004, "kind": "conservative"},
    {"tag": "veto-f075", "family": "veto", "rho_f": .75,
     "rho_m": .007, "rho_h": .0004, "kind": "conservative"},
    {"tag": "veto-prom-f05-m0007", "family": "veto-promotion",
     "rho_f": .5, "rho_m": .007, "rho_h": .0004,
     "kind": "conservative"},
    {"tag": "veto-prom-f05-m002", "family": "veto-promotion",
     "rho_f": .5, "rho_m": .02, "rho_h": .0004,
     "kind": "conservative"},
    {"tag": "veto-prom-f075-m0007", "family": "veto-promotion",
     "rho_f": .75, "rho_m": .007, "rho_h": .0004,
     "kind": "conservative"},
    {"tag": "veto-prom-f075-m002", "family": "veto-promotion",
     "rho_f": .75, "rho_m": .02, "rho_h": .0004,
     "kind": "conservative"},
    {"tag": "f-f05", "family": "f", "rho_f": .5,
     "rho_m": .007, "rho_h": .0004, "kind": "conservative"},
    {"tag": "f-f075", "family": "f", "rho_f": .75,
     "rho_m": .007, "rho_h": .0004, "kind": "conservative"},
    {"tag": "fm-f05-m0007", "family": "f-mroot", "rho_f": .5,
     "rho_m": .007, "rho_h": .0004, "kind": "conservative"},
    {"tag": "fm-f05-m002", "family": "f-mroot", "rho_f": .5,
     "rho_m": .02, "rho_h": .0004, "kind": "conservative"},
    {"tag": "fm-f075-m0007", "family": "f-mroot", "rho_f": .75,
     "rho_m": .007, "rho_h": .0004, "kind": "conservative"},
    {"tag": "fm-f075-m002", "family": "f-mroot", "rho_f": .75,
     "rho_m": .02, "rho_h": .0004, "kind": "conservative"},
    {"tag": "h-h0004", "family": "h", "rho_f": .5,
     "rho_m": .007, "rho_h": .0004, "kind": "conservative"},
    {"tag": "h-h0009", "family": "h", "rho_f": .5,
     "rho_m": .007, "rho_h": .0009, "kind": "conservative"},
    {"tag": "mroot-m0007", "family": "mroot", "rho_f": .5,
     "rho_m": .007, "rho_h": .0004, "kind": "causal"},
    {"tag": "mroot-m002", "family": "mroot", "rho_f": .5,
     "rho_m": .02, "rho_h": .0004, "kind": "causal"},
    {"tag": "overlay", "family": "c6-overlay", "rho_f": .5,
     "rho_m": .007, "rho_h": .0004, "kind": "envelope"},
    {"tag": "noadaptive", "family": "no-adaptive", "rho_f": .5,
     "rho_m": .007, "rho_h": .0004, "kind": "envelope"},
]
BY_TAG = {row["tag"]: row for row in VARIANTS}
S_T = 1.0
S_W = 1.0


def shifted(candidate: float, reference: float, shift: float) -> float:
    return (candidate + shift) / (reference + shift)


def gmean(values: list[float]) -> float:
    return math.exp(sum(math.log(value) for value in values) / len(values))


def percentile_nearest_rank(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(fraction * len(ordered)) - 1)]


def severe(candidate: dict[str, Any], reference: dict[str, Any]) -> bool:
    rw = shifted(candidate["work"], reference["work"], S_W)
    rt = shifted(candidate["process_seconds"],
                 reference["process_seconds"], S_T)
    large_delta = (
        candidate["work"] - reference["work"] > max(100.0, 10.0 * S_W)
        or candidate["process_seconds"] - reference["process_seconds"] >
        max(60.0, 10.0 * S_T))
    return rw > 1.5 and rt > 1.5 and large_delta


def locate(stage: str, instance_id: str, tag: str) -> Path:
    return common.RUNS / f"{stage}__{instance_id}__{tag}"


def candidate_dir(phase: str, instance_id: str, tag: str) -> Path:
    if phase == "witness":
        return locate("stage3-witness", instance_id, tag)
    development = locate("stage3-development", instance_id, tag)
    if (phase == "development" and
            development.joinpath("completion_marker.json").is_file()):
        return development
    witness = locate("stage3-witness", instance_id, tag)
    if witness.joinpath("completion_marker.json").is_file():
        return witness
    mechanism = locate("stage3-mechanism", instance_id, tag)
    if mechanism.joinpath("completion_marker.json").is_file():
        return mechanism
    return development


def metrics(phase: str, instance_id: str, tag: str) -> dict[str, Any]:
    directory = candidate_dir(phase, instance_id, tag)
    marker = common.load_json(directory / "completion_marker.json")
    command = common.load_json(directory / "command.json")
    candidate = historical.load_metrics(directory, tag, "round44_stage3")
    pgrb = historical.historical_reference(instance_id, "P-GRB")
    c6 = historical.historical_reference(instance_id, "C6")
    variant = BY_TAG[tag]
    result = common.load_json(directory / "result.json")
    complete_coverage = common.truth(result.get(
        "external_gini_tree_root_coverage_valid"))
    monotone = common.truth(result.get(
        "external_gini_tree_global_bound_monotone", True))
    correctness = (
        marker["complete"] and not command.get("invalidated", False) and
        not candidate["false_certificate"] and
        candidate["parameter_roundtrip_valid"] and complete_coverage and
        monotone and
        (not candidate["certified"] or candidate["verified_incumbent"]))
    rw = shifted(candidate["work"], pgrb["work"], S_W)
    rt = shifted(candidate["process_seconds"], pgrb["process_seconds"], S_T)
    p_over_c6 = shifted(pgrb["work"], c6["work"], S_W)
    advantage_required = p_over_c6 >= 5.0 and pgrb["process_seconds"] > S_T
    p_over_candidate = shifted(pgrb["work"], candidate["work"], S_W)
    row = {
        "phase": phase,
        "instance_id": instance_id,
        "role": common.MECHANISM_ROLES.get(instance_id, phase),
        "tag": tag,
        "family": variant["family"],
        "kind": variant["kind"],
        "rho_F": variant["rho_f"],
        "rho_M": variant["rho_m"],
        "rho_H": variant["rho_h"],
        "lookahead": "fixed-d1",
        "injection": "all",
        "scope": "parent",
        "run_id": command["run_id"],
        "decision_identity_sha256": command["candidate_identity"][
            "decision_identity_sha256"],
        "executable_sha256": command["executable_sha256"],
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
        "shifted_work_over_pgrb": rw,
        "shifted_time_over_pgrb": rt,
        "c6_work": c6["work"],
        "c6_process_seconds": c6["process_seconds"],
        "shifted_work_over_c6": shifted(candidate["work"], c6["work"], S_W),
        "shifted_time_over_c6": shifted(
            candidate["process_seconds"], c6["process_seconds"], S_T),
        "severe_pgrb_regression": severe(candidate, pgrb),
        "c6_advantage_gate_applies": advantage_required,
        "pgrb_advantage_over_candidate": p_over_candidate,
        "c6_advantage_retained": (
            not advantage_required or p_over_candidate >= 2.0),
    }
    row["major_gate"] = (
        instance_id != MAJOR or (rw <= 1.05 and rt <= 1.05))
    return row


def summary(rows: list[dict[str, Any]], tag: str) -> dict[str, Any]:
    chosen = [row for row in rows if row["tag"] == tag]
    major = next(row for row in chosen if row["instance_id"] == MAJOR)
    return {
        "tag": tag,
        "family": BY_TAG[tag]["family"],
        "kind": BY_TAG[tag]["kind"],
        "correctness": all(row["correctness"] for row in chosen),
        "major_gate": major["major_gate"],
        "no_severe_pgrb_regression": not any(
            row["severe_pgrb_regression"] for row in chosen),
        "c6_advantage_retained": all(
            row["c6_advantage_retained"] for row in chosen),
        "worst_shifted_work_over_pgrb": max(
            row["shifted_work_over_pgrb"] for row in chosen),
        "shifted_work_gmean": gmean([
            row["shifted_work_over_pgrb"] for row in chosen]),
        "shifted_time_gmean": gmean([
            row["shifted_time_over_pgrb"] for row in chosen]),
        "certified_rows": sum(row["certified"] for row in chosen),
        "row_count": len(chosen),
    }


def witness_and_freeze() -> None:
    rows = [metrics("witness", instance_id, variant["tag"])
            for variant in VARIANTS for instance_id in WITNESSES]
    common.write_csv(common.OUT / "stage3_witness_results.csv", rows)
    summaries = [summary(rows, variant["tag"]) for variant in VARIANTS]
    common.write_json(common.OUT / "stage3_witness_selection.json", {
        "schema": "round44-stage3-witness-selection-v1",
        "summaries": summaries,
    })
    # The witness screen leaves exactly two non-dominated mechanisms.  The
    # no-adaptive arm is the simplest envelope repair.  All admissible F/H/
    # promotion settings are trajectory-equivalent here, so veto at the lower
    # frozen threshold is the simplest conservative representative.
    retained = ["noadaptive", "veto-f05"]
    for tag in retained:
        selected = next(item for item in summaries if item["tag"] == tag)
        if not (selected["correctness"] and selected["major_gate"] and
                selected["no_severe_pgrb_regression"] and
                selected["c6_advantage_retained"]):
            raise RuntimeError(f"frozen Stage 3 retention gate failed: {tag}")
    common.write_json(common.OUT / "stage3_retention_freeze.json", {
        "schema": "round44-stage3-retention-freeze-v1",
        "frozen_before_mechanism6_extension": True,
        "mechanism6_results_observed": False,
        "development_results_observed": False,
        "validation_observed": False,
        "retained_tags": retained,
        "retained_count": len(retained),
        "selection_order": [
            "correctness", "major/P-GRB repair",
            "no severe P-GRB regression", "C6-advantage retention",
            "worst shifted P-GRB ratio", "shifted Work geometric mean",
            "shifted time geometric mean", "simplicity"],
        "tie_disposition": (
            "All passing conservative score/threshold arms had identical "
            "major and control Work except rho_M=0.007 root-mass-only on the "
            "control; veto-f05 is the simplest conservative representative."),
        "executable_sha256": rows[0]["executable_sha256"],
    })
    lines = [
        "# Round 44 conservative-refinement witness ablation", "",
        "The complete frozen two-witness screen was retained; no family was "
        "discarded because of the positive-control time alone.", "",
        "| tag | family | major Work/P-GRB | control P-GRB/candidate Work | retained |",
        "|---|---|---:|---:|---:|",
    ]
    for item in summaries:
        pair = [row for row in rows if row["tag"] == item["tag"]]
        major = next(row for row in pair if row["instance_id"] == MAJOR)
        control = next(row for row in pair if row["instance_id"] == CONTROL)
        lines.append(
            f"| {item['tag']} | {item['family']} | "
            f"{major['shifted_work_over_pgrb']:.4f} | "
            f"{control['pgrb_advantage_over_candidate']:.2f} | "
            f"{item['tag'] in retained} |")
    common.write_text(common.OUT / "conservative_refinement_ablation.md",
                      "\n".join(lines) + "\n")


def finalize_mechanism() -> None:
    freeze = common.load_json(common.OUT / "stage3_retention_freeze.json")
    retained = freeze["retained_tags"]
    rows = [metrics("mechanism", instance_id, tag)
            for tag in retained for instance_id in MECHANISM_IDS]
    common.write_csv(common.OUT / "stage3_mechanism_results.csv", rows)
    summaries = [summary(rows, tag) for tag in retained]
    finalists = [item["tag"] for item in summaries
                 if item["correctness"] and item["major_gate"] and
                 item["no_severe_pgrb_regression"] and
                 item["c6_advantage_retained"]][:2]
    if not finalists:
        raise RuntimeError("no Stage 3 mechanism-6 finalist")
    common.write_json(common.OUT / "stage3_development_freeze.json", {
        "schema": "round44-stage3-development-freeze-v1",
        "frozen_before_development_extension": True,
        "development_results_observed": False,
        "validation_observed": False,
        "finalist_tags": finalists,
        "finalist_count": len(finalists),
        "different_mechanisms": len({BY_TAG[tag]["family"]
                                     for tag in finalists}) == len(finalists),
        "mechanism6_summaries": summaries,
        "executable_sha256": rows[0]["executable_sha256"],
    })


def development_gate(rows: list[dict[str, Any]], tag: str) -> dict[str, Any]:
    chosen = [row for row in rows if row["tag"] == tag]
    work_ratios = [row["shifted_work_over_pgrb"] for row in chosen]
    time_ratios = [row["shifted_time_over_pgrb"] for row in chosen]
    # A material result is a >=5% shifted Work change.  This symmetric deadband
    # is external evaluation only and is recorded explicitly in the result.
    wins = sum(value <= .95 for value in work_ratios)
    losses = sum(value >= 1.05 for value in work_ratios)
    item = summary(chosen, tag)
    item.update({
        "shifted_work_p90": percentile_nearest_rank(work_ratios, .9),
        "material_work_deadband": .05,
        "material_wins": wins,
        "material_losses": losses,
        "material_wins_at_least_losses": wins >= losses,
    })
    item["passes_all_development_gates"] = (
        item["correctness"] and item["major_gate"] and
        item["no_severe_pgrb_regression"] and
        item["c6_advantage_retained"] and
        item["shifted_work_gmean"] <= .90 and
        item["shifted_time_gmean"] <= .95 and
        item["shifted_work_p90"] <= 1.50 and wins >= losses)
    return item


def finalize_development() -> None:
    freeze = common.load_json(common.OUT / "stage3_development_freeze.json")
    finalists = freeze["finalist_tags"]
    rows = [metrics("development", instance_id, tag)
            for tag in finalists for instance_id in common.DEVELOPMENT_IDS]
    common.write_csv(common.OUT / "development_comparison.csv", rows)
    dispositions = [development_gate(rows, tag) for tag in finalists]
    common.write_json(common.OUT / "stage3_development_selection.json", {
        "schema": "round44-stage3-development-selection-v1",
        "development_instances": common.DEVELOPMENT_IDS,
        "dispositions": dispositions,
        "passing_tags": [item["tag"] for item in dispositions
                         if item["passes_all_development_gates"]],
        "validation_observed": False,
    })
    causal_rows: list[dict[str, Any]] = []
    representatives = [
        ("C6 + envelope only", "overlay"),
        ("no-adaptive K4 + envelope", "noadaptive"),
        ("veto-only", "veto-f05"),
        ("veto+promotion", "veto-prom-f05-m0007"),
        ("frontier-only", "f-f05"),
        ("frontier-mass", "fm-f05-m002"),
        ("H=F*M_root", "h-h0004"),
        ("root-mass-only", "mroot-m002"),
    ]
    round43_rows = common.csv_rows(
        common.ROOT / "results" /
        "gf_k1_k4_envelope_refinement_round43" /
        "stage3_mechanism_results.csv")
    for instance_id in WITNESSES:
        for mechanism in ("C6", "P-GRB"):
            base = historical.historical_reference(instance_id, mechanism)
            pgrb = historical.historical_reference(instance_id, "P-GRB")
            causal_rows.append({
                "instance_id": instance_id,
                "role": common.MECHANISM_ROLES[instance_id],
                "mechanism": mechanism,
                "provenance": "frozen_round40_reference",
                "certified": base["certified"],
                "work": base["work"],
                "process_seconds": base["process_seconds"],
                "shifted_work_over_pgrb": shifted(
                    base["work"], pgrb["work"], S_W),
                "shifted_time_over_pgrb": shifted(
                    base["process_seconds"], pgrb["process_seconds"], S_T),
                "split_count": base["split_count"],
                "terminal_mip_jobs": base["terminal_mip_jobs"],
            })
        for label, tag in representatives:
            row = metrics("witness", instance_id, tag)
            causal_rows.append({
                "instance_id": instance_id,
                "role": common.MECHANISM_ROLES[instance_id],
                "mechanism": label,
                "provenance": row["run_id"],
                "certified": row["certified"],
                "work": row["work"],
                "process_seconds": row["process_seconds"],
                "shifted_work_over_pgrb": row["shifted_work_over_pgrb"],
                "shifted_time_over_pgrb": row["shifted_time_over_pgrb"],
                "split_count": row["split_count"],
                "terminal_mip_jobs": row["terminal_mip_jobs"],
            })
        round43 = next(row for row in round43_rows
                       if row["instance_id"] == instance_id and
                       row["configuration"] == "A(4,2,0.1)")
        pgrb = historical.historical_reference(instance_id, "P-GRB")
        causal_rows.append({
            "instance_id": instance_id,
            "role": common.MECHANISM_ROLES[instance_id],
            "mechanism": "Round 43 D recursion A(4,2,0.1)",
            "provenance": round43["run_id"],
            "certified": round43["certified"],
            "work": float(round43["total_work"]),
            "process_seconds": float(round43["process_seconds"]),
            "shifted_work_over_pgrb": shifted(
                float(round43["total_work"]), pgrb["work"], S_W),
            "shifted_time_over_pgrb": shifted(
                float(round43["process_seconds"]),
                pgrb["process_seconds"], S_T),
            "split_count": round43["split_count"],
            "terminal_mip_jobs": round43["terminal_mip_jobs"],
        })
    common.write_csv(common.OUT / "stage3_causal_table.csv", causal_rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--finalize-mechanism", action="store_true")
    parser.add_argument("--finalize-development", action="store_true")
    args = parser.parse_args()
    if args.finalize_development:
        finalize_development()
    elif args.finalize_mechanism:
        finalize_mechanism()
    else:
        witness_and_freeze()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
