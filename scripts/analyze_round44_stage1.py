#!/usr/bin/env python3
"""Assemble the sealed Round 44 structural atlas and freeze Stage 1 choices."""

from __future__ import annotations

import csv
import math
from pathlib import Path
import statistics
from typing import Any

import round44_common as common


TAGS = {
    ("fixed-d1", "none"): "d1-none",
    ("fixed-d1", "all"): "d1-all",
    ("fixed-d1", "violated"): "d1-violated",
    ("fixed-d1", "active-one"): "d1-active-one",
    ("fixed-d2", "none"): "d2-none",
    ("fixed-d2", "all"): "d2-all",
    ("fixed-d2", "violated"): "d2-violated",
    ("fixed-d2", "active-one"): "d2-active-one",
    ("frontier-d2", "none"): "frontier-d2-none",
    ("frontier-d2", "all"): "frontier-d2-all",
    ("frontier-d2", "violated"): "frontier-d2-violated",
    ("frontier-d2", "active-one"): "frontier-d2-active-one",
}


def run_dir(instance_id: str, tag: str) -> Path:
    return common.RUNS / f"stage1-atlas__{instance_id}__{tag}"


def number(value: Any) -> float:
    return float(value)


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = probability * (len(ordered) - 1)
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - index) + ordered[upper] * (index - lower)


def ceil_one_significant(value: float) -> float:
    exponent = math.floor(math.log10(value))
    unit = 10.0 ** exponent
    return math.ceil(value / unit - 1e-12) * unit


def main() -> int:
    structural: list[dict[str, Any]] = []
    frontier_rows: list[dict[str, Any]] = []
    scores: list[dict[str, Any]] = []
    costs: list[dict[str, Any]] = []
    executable_hashes: set[str] = set()
    for instance_id in common.DEVELOPMENT_IDS:
        for (lookahead, injection), tag in TAGS.items():
            directory = run_dir(instance_id, tag)
            marker = common.load_json(directory / "completion_marker.json")
            command = common.load_json(directory / "command.json")
            executable_hashes.add(command["executable_sha256"])
            if not marker["complete"] or command.get("invalidated"):
                raise RuntimeError(f"invalid or incomplete atlas row: {directory}")
            decisions = common.csv_rows(
                directory / "refinement_decision_ledger.csv")
            lookahead_rows = common.csv_rows(
                directory / "lookahead_profile_ledger.csv")
            frontier = common.csv_rows(
                directory / "frontier_target_ledger.csv")
            facets = common.csv_rows(directory / "envelope_facet_ledger.csv")
            for row in decisions:
                copied: dict[str, Any] = {
                    "instance_id": instance_id,
                    "role": common.MECHANISM_ROLES.get(
                        instance_id, "development_context"),
                    "run_id": command["run_id"],
                    "lookahead_policy": lookahead,
                    "injection_policy": injection,
                    "scope": "parent",
                    **row,
                }
                copied["width"] = number(row["upper"]) - number(row["lower"])
                copied["facet_count"] = sum(
                    1 for facet in facets
                    if facet["parent_id"] == row["parent_id"])
                copied["violated_facet_count"] = sum(
                    1 for facet in facets
                    if facet["parent_id"] == row["parent_id"] and
                    number(facet["violation"]) > 1e-7 * max(
                        1.0, abs(number(row["L_I"]))))
                copied["predicted_veto_rho_05"] = (
                    row["old_c6_action"] == "split" and
                    number(row["F"]) >= 0.5 - 1e-7)
                copied["predicted_veto_promotion_rho_05_m_0007"] = (
                    copied["predicted_veto_rho_05"] or
                    (row["old_c6_action"] != "split" and
                     common.truth(row["decisive"]) and
                     number(row["M_root"]) >= 0.007 - 1e-7))
                structural.append(copied)
                scores.append({
                    "instance_id": instance_id,
                    "lookahead_policy": lookahead,
                    "injection_policy": injection,
                    "parent_id": row["parent_id"],
                    "width": copied["width"],
                    "old_c6_action": row["old_c6_action"],
                    "D_R43": row["D_R43"],
                    "P_profile": row["P_profile"],
                    "M_root": row["M_root"],
                    "F": row["F"],
                    "H": row["H"],
                    "decisive": row["decisive"],
                    "veto_rho_05": copied["predicted_veto_rho_05"],
                    "veto_promotion":
                        copied["predicted_veto_promotion_rho_05_m_0007"],
                })
            for row in frontier:
                frontier_rows.append({
                    "instance_id": instance_id,
                    "lookahead_policy": lookahead,
                    "injection_policy": injection,
                    **row,
                })
            costs.append({
                "instance_id": instance_id,
                "lookahead_policy": lookahead,
                "injection_policy": injection,
                "parent_decisions": len(decisions),
                "lookahead_lp_jobs": len(lookahead_rows),
                "depth2_lp_jobs": sum(
                    int(row["cell_depth"]) == int(row["parent_depth"]) + 2
                    for row in lookahead_rows),
                "fixed_d2_reference_jobs": 6 * len(decisions),
                "lp_jobs_avoided_vs_fixed_d2":
                    6 * len(decisions) - len(lookahead_rows),
                "complete_gap_free_profiles": len(decisions),
            })
    if len(executable_hashes) != 1:
        raise RuntimeError(f"atlas executable drift: {executable_hashes}")
    common.write_csv(common.OUT / "structural_atlas.csv", structural)
    common.write_csv(common.OUT / "frontier_target_ledger.csv", frontier_rows)
    common.write_csv(common.OUT / "score_reconstruction.csv", scores)
    common.write_csv(common.OUT / "lookahead_cost_projection.csv", costs)

    principal = [row for row in structural
                 if row["lookahead_policy"] == "frontier-d2" and
                 row["injection_policy"] == "active-one"]
    nonzero_m = [number(row["M_root"]) for row in principal
                 if number(row["M_root"]) > 0.0]
    nonzero_h = [number(row["H"]) for row in principal
                 if number(row["H"]) > 1e-15]
    m_median = statistics.median(nonzero_m)
    m_q3 = quantile(nonzero_m, 0.75)
    h_median = statistics.median(nonzero_h)
    h_q3 = quantile(nonzero_h, 0.75)
    freeze = {
        "schema": "round44-stage1-selection-freeze-v1",
        "frozen_before_algorithm_candidate_runs": True,
        "candidate_algorithm_results_observed": False,
        "source_stage": "diagnostic_atlas_only",
        "atlas_run_count": len(common.DEVELOPMENT_IDS) * len(TAGS),
        "atlas_decision_count": len(structural),
        "executable_sha256": next(iter(executable_hashes)),
        "principal_lookahead_policy": "frontier-d2",
        "secondary_lookahead_reference": "fixed-d1",
        "fixed_d2_role": "causal_reference_only",
        "envelope_injection_policies": ["active-one", "violated"],
        "scope_policies": ["parent", "nested"],
        "rho_F_values": [0.5, 0.75],
        "rho_M_distribution": {
            "positive_count": len(nonzero_m),
            "median": m_median,
            "upper_quartile": m_q3,
        },
        "rho_M_values": [
            ceil_one_significant(m_median),
            ceil_one_significant(m_q3),
        ],
        "rho_H_distribution": {
            "positive_count": len(nonzero_h),
            "median": h_median,
            "upper_quartile": h_q3,
        },
        "rho_H_values": [
            ceil_one_significant(h_median),
            ceil_one_significant(h_q3),
        ],
        "threshold_selection_rule":
            "median and upper quartile of positive structural scores, each "
            "rounded upward to one significant digit; no runtime fitting",
        "runtime_fit_used": False,
        "forbidden_inputs_used": False,
        "validation_observed": False,
        "holdout_observed": False,
    }
    common.write_json(common.OUT / "stage1_selection_freeze.json", freeze)

    principal_cost = [row for row in costs
                      if row["lookahead_policy"] == "frontier-d2" and
                      row["injection_policy"] == "active-one"]
    fixed_cost = [row for row in costs
                  if row["lookahead_policy"] == "fixed-d2" and
                  row["injection_policy"] == "active-one"]
    jobs_frontier = sum(int(row["lookahead_lp_jobs"])
                        for row in principal_cost)
    jobs_fixed = sum(int(row["lookahead_lp_jobs"]) for row in fixed_cost)
    major = [row for row in principal if row["role"] ==
             "major_fragmentation_regression"]
    control = [row for row in principal if row["role"] ==
               "strongest_k4_positive_control"]
    report = f"""# Round 44 Stage 1 structural atlas

The sealed atlas contains {len(structural)} interval decisions from
{len(common.DEVELOPMENT_IDS) * len(TAGS)} diagnostic-only runs on the frozen
development-10 panel. All profiles were complete and gap-free, every run used
one executable hash (`{next(iter(executable_hashes))}`), and no algorithm
candidate result was observed before this freeze.

## Findings

- The corrected `D_R43` remains width-local: its denominator contains current
  interval width, so proportional residual profiles need not decay as the tree
  narrows. This explains the hundreds of rho=0.05 Round 43 splits; rho=0.10
  sharply reduced them by crossing a broad portion of the local-score mass.
- `M_root` retains absolute root-relative mass and therefore decays under
  narrowing. The frozen values are `{freeze['rho_M_values']}`.
- `F` is zero unless genuine disjunction improves on the strengthened envelope
  toward the mathematical next frontier. The frozen grid is
  `{freeze['rho_F_values']}`; `H=F*M_root` uses
  `{freeze['rho_H_values']}`.
- Frontier-d2 used {jobs_frontier} lookahead LP jobs versus {jobs_fixed} for
  fixed-d2 with active-one, avoiding {jobs_fixed - jobs_frontier} jobs while
  preserving exact nonuniform coverage. Fixed-d1 remains the secondary causal
  reference.
- Active-one and violated separation are retained. Active-one perturbs fewer
  rows; violated separation tests whether the extra valid rows buy enough proof
  progress. Parent-only and nested scopes must both reach Stage 2 because atlas
  runs do not exercise descendant inheritance.
- At rho_F=0.5 the veto prediction retains all four major-witness initial
  parents ({sum(not common.truth(row['predicted_veto_rho_05']) for row in major)}
  retained) rather than reproducing Round 43 fragmentation. On the strongest
  control it also vetoes the only old split, so exact Stage 2 evidence - not
  the atlas - must decide whether the P-GRB advantage-retention gate survives.
- Fixed-d1 yields F=0 on both principal witnesses. It is therefore a clean
  no-adaptive/overlay reference but cannot distinguish frontier-relevant splits
  there.
- Parent-only scope permits no descendant model reuse for new facets. Nested
  scope validly inherits only source-interval facets to nested descendants and
  may trade model strengthening for row-signature churn; Stage 2 measures it.

The selection freeze is [stage1_selection_freeze.json](stage1_selection_freeze.json).
"""
    common.write_text(common.OUT / "stage1_report.md", report)
    common.write_text(common.OUT / "structural_atlas.md", report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
