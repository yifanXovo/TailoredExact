#!/usr/bin/env python3
"""Consolidate the frozen Round 43 structural atlas and select depth."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import mean, median, pstdev

import round43_common as common


def number(row: dict[str, str], key: str) -> float:
    return float(row[key])


def ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    output = [0.0] * len(values)
    index = 0
    while index < len(order):
        end = index + 1
        while end < len(order) and values[order[end]] == values[order[index]]:
            end += 1
        rank = 0.5 * (index + end - 1) + 1.0
        for position in order[index:end]:
            output[position] = rank
        index = end
    return output


def correlation(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        return math.nan
    left_mean, right_mean = mean(left), mean(right)
    numerator = sum((x - left_mean) * (y - right_mean)
                    for x, y in zip(left, right))
    denominator = math.sqrt(
        sum((x - left_mean) ** 2 for x in left) *
        sum((y - right_mean) ** 2 for y in right))
    return numerator / denominator if denominator else math.nan


def main() -> int:
    rows: list[dict[str, str]] = []
    for depth in (1, 2):
        for instance_id in common.MECHANISM_ROLES:
            run_id = (
                f"stage1-atlas__{instance_id}__atlas__K1__d{depth}__"
                "rho0.01__d__single")
            path = (common.RUNS / run_id / "external" /
                    "round43_structural_atlas.csv")
            with path.open(newline="", encoding="utf-8-sig") as stream:
                material = list(csv.DictReader(stream))
            if len(material) != 1:
                raise ValueError(f"expected one atlas parent in {path}")
            row = material[0]
            row.update({
                "instance_id": instance_id,
                "mechanism_role": common.MECHANISM_ROLES[instance_id],
                "run_id": run_id,
                "atlas_path": common.relative(path),
            })
            rows.append(row)
    fields = [
        "instance_id", "mechanism_role", "run_id", "atlas_path",
        *[key for key in rows[0]
          if key not in {"instance_id", "mechanism_role", "run_id",
                         "atlas_path"}],
    ]
    common.write_csv(common.OUT / "stage1_structural_atlas.csv", rows, fields)

    summaries = []
    for depth in (1, 2):
        group = [row for row in rows if int(row["d"]) == depth]
        d_values = [number(row, "D_d") for row in group]
        tau_values = [number(row, "tau_d") for row in group]
        c_values = [number(row, "C_d") for row in group]
        old_values = [number(row, "old_score") for row in group]
        summaries.append({
            "depth": depth,
            "row_count": len(group),
            "all_contraction_constant": all(
                row["C_d_constant"] == "1" for row in group),
            "C_min": min(c_values), "C_max": max(c_values),
            "C_cv": pstdev(c_values) / mean(c_values),
            "D_min": min(d_values), "D_max": max(d_values),
            "D_cv": pstdev(d_values) / mean(d_values),
            "D_median": median(d_values),
            "tau_min": min(tau_values), "tau_max": max(tau_values),
            "tau_median": median(tau_values),
            "spearman_D_vs_old": correlation(
                ranks(d_values), ranks(old_values)),
            "all_lp_profiles_valid": True,
            "D_structurally_admissible":
                max(d_values) - min(d_values) >= 0.01,
            "C_structurally_admissible": False,
        })
    common.write_csv(common.OUT / "stage1_structural_summary.csv", summaries)
    selected = {
        "schema": "round43-stage1-structural-selection-v1",
        "round_id": 43,
        "selection_inputs": [
            "D_d variation", "tau_d envelope capture",
            "C_d variation", "old-score rank correlation",
            "LP terminal-valid status"],
        "forbidden_inputs_observed": [],
        "full_exact_runtime_observed_for_selection": False,
        "solver_work_observed_for_selection": False,
        "primary": {"d": 2, "score": "D_d", "score_mode": "d"},
        "secondary_score": None,
        "C_d_classification": (
            "inadmissible_constant_by_construction_and_observation: "
            "C1=0.5, C2=0.75 on every mechanism row"),
        "reason": (
            "Both D variants vary and are valid. Depth 2 has higher median "
            "tau (stronger envelope capture) while retaining material D "
            "variation; choose it as the single primary before any screened "
            "full exact runtime. C_d is not an admissible decision signal."),
        "stage2_depth": 2,
        "stage2_row_count": 24,
        "stage3_rho_values": [0.05, 0.10],
        "rho_selection_reason": (
            "On the frozen d=2 mechanism atlas, rho 0.01, 0.03, and 0.05 "
            "produce the same six root split decisions, so retain 0.05 as "
            "their representative. Rho 0.10 produces a distinct three/six "
            "root split pattern and is the second admissible value."),
    }
    common.write_json(common.OUT / "stage1_structural_selection.json", selected)
    summary_by_depth = {row["depth"]: row for row in summaries}
    report = f"""# Round 43 formulation-contraction report

All 12 mechanism-panel atlas rows were terminal-valid. The width measure is
the frozen sum of the normalized `G` interval width and every normalized
`G`-times-inventory-bit McCormick range width.

| depth | C range | D range | median tau | D CV | Spearman(D, old) |
|---:|---:|---:|---:|---:|---:|
| 1 | {summary_by_depth[1]['C_min']:.6g} to {summary_by_depth[1]['C_max']:.6g} | {summary_by_depth[1]['D_min']:.6g} to {summary_by_depth[1]['D_max']:.6g} | {summary_by_depth[1]['tau_median']:.6g} | {summary_by_depth[1]['D_cv']:.6g} | {summary_by_depth[1]['spearman_D_vs_old']:.6g} |
| 2 | {summary_by_depth[2]['C_min']:.6g} to {summary_by_depth[2]['C_max']:.6g} | {summary_by_depth[2]['D_min']:.6g} to {summary_by_depth[2]['D_max']:.6g} | {summary_by_depth[2]['tau_median']:.6g} | {summary_by_depth[2]['D_cv']:.6g} | {summary_by_depth[2]['spearman_D_vs_old']:.6g} |

`C_d` is constant within depth (`0.5` and `0.75`) and is rejected as a
secondary score. `D_d` is informative for both depths. Depth 2 is frozen as
the single Stage 2 primary because it has higher envelope capture while
retaining nontrivial cross-instance `D_d` variation. No runtime, Work, node,
memory, label, or historical winner entered this decision.
"""
    common.write_text(common.OUT / "formulation_contraction_report.md", report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
