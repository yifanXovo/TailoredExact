#!/usr/bin/env python3
"""Build the authoritative Round 46 C6 score census and trace comparisons."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import round46_common as common


FIELDS = [
    "evidence_source", "source_path", "run_id", "stage", "instance",
    "K0", "rho", "rho_source", "decision_sequence", "interval_id",
    "parent_id", "depth", "gamma_L", "gamma_U", "parent_bound",
    "left_child_id", "left_child_bound", "left_child_infeasible",
    "right_child_id", "right_child_bound", "right_child_infeasible",
    "verified_incumbent", "normalized_c6_gain",
    "child_infeasibility_trigger", "threshold_comparison",
    "selected_action", "target_value", "deterministic_reason",
    "coverage_update",
]


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def relative(path: Path) -> str:
    return path.resolve().relative_to(common.ROOT.resolve()).as_posix()


def official_census() -> list[dict[str, Any]]:
    census = []
    for path in sorted(common.RUNS.glob(
            "stage3_300s__*/c6_split_decision_ledger.csv")):
        command = common.load_json(path.parent / "command.json")
        if command["arm"] == "P-GRB":
            continue
        for row in rows(path):
            census.append({
                "evidence_source": "round46_stage3_full_tree",
                "source_path": relative(path), "stage": command["stage"],
                "instance": command["instance_id"], **row,
            })
    return census


def historical_census() -> list[dict[str, Any]]:
    root = common.ROOT / "results" / "gf_nonblocking_gurobi_c6_round31"
    census = []
    for path in sorted(root.rglob("split_decision_ledger.csv")):
        lowered = path.as_posix().lower()
        if "__c6_" not in lowered or "__c5_" in lowered:
            continue
        run_id = path.parent.parent.name
        for sequence, row in enumerate(rows(path), start=1):
            split = str(row.get("split", "")).lower() in {"1", "true"}
            target = str(row.get("target_phase_required", "")).lower() in {
                "1", "true"}
            action = "split" if split else (
                "native-target" if target else "exact-close")
            census.append({
                "evidence_source": "historical_round31_authoritative_full_tree",
                "source_path": relative(path), "run_id": run_id,
                "stage": "historical_round31", "instance": run_id,
                "K0": 4, "rho": 0.01, "rho_source": "historical_frozen",
                "decision_sequence": sequence,
                "interval_id": row.get("parent_id", ""),
                "parent_id": row.get("parent_id", ""),
                "normalized_c6_gain":
                    row.get("normalized_disjunction_gain", ""),
                "child_infeasibility_trigger":
                    row.get("child_infeasibility_trigger", ""),
                "threshold_comparison": "historical_rho_001",
                "selected_action": action,
                "target_value": row.get("parent_native_bound_target", ""),
                "deterministic_reason": row.get("reason", ""),
                "coverage_update": "historical_c6_lifecycle",
            })
    return census


def trace_comparison() -> list[dict[str, Any]]:
    output = []
    arms = common.load_json(common.OUT / "arm_definition.json")["arms"]
    for arm in arms:
        if arm["rho"] == 0.01:
            continue
        baseline = common.ARM_BY_K_RHO[(arm["K0"], 0.01)]
        for item in common.frozen_instances().values():
            if item["panel"] != "development":
                continue
            left_path = common.RUNS / (
                f"stage3_300s__{item['instance']}__{baseline}") / \
                "c6_split_decision_ledger.csv"
            right_path = common.RUNS / (
                f"stage3_300s__{item['instance']}__{arm['arm']}") / \
                "c6_split_decision_ledger.csv"
            left, right = rows(left_path), rows(right_path)
            divergence = None
            for index in range(max(len(left), len(right))):
                lrow = left[index] if index < len(left) else {}
                rrow = right[index] if index < len(right) else {}
                if (lrow.get("selected_action"), lrow.get("interval_id")) != (
                        rrow.get("selected_action"), rrow.get("interval_id")):
                    divergence = (index + 1, lrow, rrow)
                    break
            sequence, lrow, rrow = divergence or ("", {}, {})
            output.append({
                "instance": item["instance"], "K0": arm["K0"],
                "baseline_arm": baseline, "candidate_arm": arm["arm"],
                "candidate_rho": arm["rho"],
                "decision_trace_equivalent": divergence is None,
                "first_divergence_sequence": sequence,
                "interval_id": rrow.get("interval_id", lrow.get("interval_id", "")),
                "normalized_c6_gain": rrow.get(
                    "normalized_c6_gain", lrow.get("normalized_c6_gain", "")),
                "baseline_action": lrow.get("selected_action", "trace-ended"),
                "candidate_action": rrow.get("selected_action", "trace-ended"),
                "candidate_threshold_comparison":
                    rrow.get("threshold_comparison", ""),
            })
    return output


def equivalence_intervals(census: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gains = set()
    for row in census:
        if row.get("evidence_source") != "round46_stage3_full_tree":
            continue
        try:
            gain = float(row.get("normalized_c6_gain", ""))
        except (TypeError, ValueError):
            continue
        if math.isfinite(gain) and 0.0 <= gain <= 1.0:
            gains.add(gain)
    distinct = sorted(gains)
    boundaries = [0.0, *[gain for gain in distinct if gain > 0.0], 1.0]
    output = []
    for index in range(len(boundaries) - 1):
        lower, upper = boundaries[index], boundaries[index + 1]
        representative = upper if upper == lower else (lower + upper) / 2.0
        output.append({
            "interval_index": index + 1,
            "rho_lower_exclusive": lower,
            "rho_upper_inclusive": upper,
            "representative_rho": representative,
            "decision_equivalence_rule":
                "finite gain splits iff normalized_gain + 1e-15 >= rho; "
                "child infeasibility is rho-independent",
            "distinct_gain_count": len(distinct),
        })
    return output


def main() -> int:
    census = official_census() + historical_census()
    common.write_csv(common.OUT / "c6_split_score_census.csv", census, FIELDS)
    comparisons = trace_comparison()
    common.write_csv(common.OUT / "c6_decision_trace_comparison.csv",
                     comparisons)
    intervals = equivalence_intervals(census)
    common.write_csv(common.OUT / "c6_decision_equivalence_intervals.csv",
                     intervals)
    print({"census_rows": len(census),
           "trace_comparisons": len(comparisons),
           "equivalence_intervals": len(intervals)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
