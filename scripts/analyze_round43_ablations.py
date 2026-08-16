#!/usr/bin/env python3
"""Assemble the frozen Round 43 mechanism ablations and factor evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import round43_analysis as analysis
import round43_common as common


RHO = 0.10
MAJOR = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"


def candidate_dir(stage: str, instance_id: str, *, score: str,
                  envelope: str) -> Path:
    extension_stages = {
        "stage3-ablation-old-no-envelope": "x43an",
        "stage3-ablation-old-envelope": "x43ae",
    }
    if instance_id == MAJOR and stage in extension_stages:
        extended = common.RUNS / (
            f"{extension_stages[stage]}__{instance_id}__algorithm__K1__d2__"
            f"rho{RHO:g}__{score}__{envelope}")
        if (extended / "result.json").is_file():
            return extended
    return common.RUNS / (
        f"{stage}__{instance_id}__algorithm__K1__d2__rho{RHO:g}__"
        f"{score}__{envelope}")


def no_adaptive_dir(instance_id: str) -> Path:
    prefix = ("stage2-envelope" if instance_id in common.MECHANISM_ROLES
              else "stage2-development")
    return common.RUNS / (
        f"{prefix}__{instance_id}__algorithm__K1__d2__rho0.01__"
        "no-adaptive__single")


def reference(instance_id: str, arm: str) -> dict[str, Any]:
    if arm == "P-GRB":
        return analysis.current_reference(instance_id, arm)
    if arm == "C6" and instance_id in common.CONTEMPORARY_REFERENCE_IDS:
        return analysis.current_reference(instance_id, arm)
    return analysis.historical_reference(instance_id, arm)


def metric_row(instance_id: str, arm: str, source: str,
               run_dir: Path | None = None) -> dict[str, Any]:
    if run_dir is None:
        metrics = reference(instance_id, arm)
    else:
        metrics = analysis.load_metrics(run_dir, arm, source)
    return {
        "instance_id": instance_id,
        "mechanism_role": common.MECHANISM_ROLES[instance_id],
        "arm": arm,
        "source": source,
        "run_id": metrics["run_id"],
        "certified": metrics["certified"],
        "right_censored": metrics["right_censored"],
        "false_certificate": metrics["false_certificate"],
        "work": metrics["work"],
        "process_seconds": metrics["process_seconds"],
        "exact_phase_seconds": metrics["exact_phase_seconds"],
        "nodes": metrics["nodes"],
        "lp_jobs": metrics["lp_jobs"],
        "terminal_mip_jobs": metrics["terminal_mip_jobs"],
        "split_count": metrics["split_count"],
        "run_dir": metrics["run_dir"],
    }


def main() -> int:
    rows: list[dict[str, Any]] = []
    for instance_id in common.MECHANISM_ROLES:
        rows.extend((
            metric_row(instance_id, "old-score-no-envelope",
                       "round43_ablation", candidate_dir(
                           "stage3-ablation-old-no-envelope", instance_id,
                           score="old", envelope="none")),
            metric_row(instance_id, "envelope-no-adaptive",
                       "round43_stage2_reuse",
                       no_adaptive_dir(instance_id)),
            metric_row(instance_id, "envelope-old-score",
                       "round43_ablation", candidate_dir(
                           "stage3-ablation-old-envelope", instance_id,
                           score="old", envelope="single")),
            metric_row(instance_id, "envelope-D-score",
                       "round43_stage3_reuse", candidate_dir(
                           "stage3-candidate", instance_id,
                           score="d", envelope="single")),
            metric_row(instance_id, "C6", "reference"),
            metric_row(instance_id, "K1-single", "reference"),
            metric_row(instance_id, "P-GRB", "reference"),
        ))
    common.write_csv(common.OUT / "refinement_score_ablation.csv", rows)

    summaries = []
    arms = list(dict.fromkeys(row["arm"] for row in rows))
    for arm in arms:
        group = [row for row in rows if row["arm"] == arm]
        summaries.append({
            "arm": arm,
            "row_count": len(group),
            "certified_count": sum(row["certified"] for row in group),
            "right_censored_count": sum(
                row["right_censored"] for row in group),
            "false_certificate_count": sum(
                row["false_certificate"] for row in group),
            "work_geomean": analysis.gmean(
                [float(row["work"]) for row in group]),
            "process_seconds_geomean": analysis.gmean(
                [float(row["process_seconds"]) for row in group]),
            "total_terminal_mip_jobs": sum(
                int(row["terminal_mip_jobs"]) for row in group),
            "total_splits": sum(int(row["split_count"]) for row in group),
        })
    common.write_csv(
        common.OUT / "refinement_score_ablation_summary.csv", summaries)

    lines = [
        "# Refinement-score ablation",
        "",
        "The frozen mechanism-6 panel compares the required causal arms at "
        "K0=1. The no-adaptive arm is the selected single-pass affine "
        "envelope with exact parent closure; the D-score arm is A(1,2,0.10).",
        "",
        "| Arm | Exact | Censored | Work geometric mean | Terminal MIPs | Splits |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['arm']} | {row['certified_count']}/{row['row_count']} | "
            f"{row['right_censored_count']} | {row['work_geomean']:.6g} | "
            f"{row['total_terminal_mip_jobs']} | {row['total_splits']} |")
    lines.extend((
        "",
        "The comparison is causal only at the frozen arm level. Differences "
        "in Work are not inferred from root-bound strength alone, and timing "
        "or hardware outcomes are excluded from every refinement decision.",
        "",
    ))
    (common.OUT / "refinement_score_ablation.md").write_text(
        "\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
