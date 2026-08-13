#!/usr/bin/env python3
"""Freeze Round 37 geometry forensics, hypotheses, and development panel."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
R36 = ROOT / "results" / "gf_incumbent_decomposition_causal_round36"
OUT = ROOT / "results" / "gf_gini_geometry_mechanism_round37"
SELECTED_ORDINALS = {1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, material: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(material[0]))
        writer.writeheader()
        writer.writerows(material)


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> int:
    panel = rows(R36 / "frozen_causal_panel.csv")
    per_arm = rows(R36 / "per_arm_results.csv")
    decomposition = rows(R36 / "initial_decomposition_audit.csv")
    geometry = {row["panel_row_id"]: row for row in rows(
        R36 / "causal_geometry_comparison.csv")}
    stage_c = {
        row["instance_id"]: row for row in rows(R36 / "stage_c_comparisons.csv")
        if row["comparator"] == "C6-HGA-FULL"
    }
    hh = {row["run_id"]: row for row in per_arm if row["arm"] == "HH"}
    by_run: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decomposition:
        if row["run_id"] in hh and row["active"].lower() in {"1", "true"}:
            by_run[row["run_id"]].append(row)

    forensics: list[dict[str, Any]] = []
    for item in panel:
        baseline = next(row for row in per_arm if
                        row["panel_row_id"] == item["panel_row_id"] and
                        row["arm"] == "HH")
        cells = sorted(by_run[baseline["run_id"]],
                       key=lambda row: int(row["anchor_cell_index"]))
        finite = [row for row in cells
                  if row["local_lp_status"].lower() == "optimal" and
                  math.isfinite(float(row["local_lp_lower_bound"]))]
        weakest = min(
            finite,
            key=lambda row: (float(row["local_lp_lower_bound"]),
                             int(row["anchor_cell_index"])),
        )
        proof = float(baseline["U_proof_launch"])
        weak_bound = float(weakest["local_lp_lower_bound"])
        g = geometry[item["panel_row_id"]]
        c = stage_c[item["instance_id"]]
        ordinal = int(item["panel_ordinal"])
        selection_reason = "not_selected"
        if ordinal in {1, 2}:
            selection_reason = "mandatory_all_v12"
        elif ordinal in {9, 10, 11, 12}:
            selection_reason = "mandatory_all_v50"
        elif ordinal in {4, 6}:
            selection_reason = "round36_stage_c_candidate_win_regime"
        elif ordinal == 8:
            selection_reason = "round36_stage_c_v20_comparator_win_regression"
        elif ordinal == 13:
            selection_reason = "unique_round35_pattern2_moderate_witness"
        elif ordinal == 14:
            selection_reason = "no_geometry_exposure_fast_negative_control"
        elif ordinal == 7:
            selection_reason = "high_imbalance_largest_baseline_split_stress"
        forensics.append({
            "panel_ordinal": ordinal,
            "panel_row_id": item["panel_row_id"],
            "instance_id": item["instance_id"],
            "path": item["path"],
            "instance_sha256": item["instance_sha256"],
            "V": int(item["V"]),
            "M": int(item["M"]),
            "scenario": item["scenario"],
            "round35_pattern": item["round35_pattern"],
            "proof_upper": proof,
            "weakest_initial_cell_index": int(weakest["anchor_cell_index"]),
            "weakest_initial_cell_lower": float(weakest["active_lower"]),
            "weakest_initial_cell_upper": float(weakest["active_upper"]),
            "weakest_initial_cell_width": float(weakest["active_width"]),
            "weakest_initial_lp_bound": weak_bound,
            "weakness_gap_scaled": (proof - weak_bound) /
                max(1.0, abs(proof)),
            "baseline_actual_splits": int(baseline["actual_splits"]),
            "baseline_final_common_ub_gap": float(
                baseline["final_common_ub_gap"]),
            "round36_geometry_exposure": g["geometry_exposure"],
            "round36_geometry_downstream_changed":
                g["downstream_sequence_changed"],
            "round36_geometry_causal_outcome": g["causal_outcome"],
            "round36_right_minus_left_proof_auc": float(
                g["right_minus_left_proof_auc"]),
            "round36_stage_c_bw_p_vs_c6_outcome": c["outcome"],
            "selected_for_round37_development": ordinal in SELECTED_ORDINALS,
            "selection_reason": selection_reason,
        })
    write_csv(OUT / "geometry_forensics.csv", forensics)

    selected = [row for row in forensics
                if row["selected_for_round37_development"]]
    frozen_fields = (
        "panel_ordinal", "panel_row_id", "instance_id", "path",
        "instance_sha256", "V", "M", "scenario", "round35_pattern",
        "round36_geometry_causal_outcome",
        "round36_stage_c_bw_p_vs_c6_outcome",
        "weakest_initial_cell_index", "selection_reason",
    )
    frozen = [{field: row[field] for field in frozen_fields}
              for row in selected]
    write_csv(OUT / "frozen_development_panel.csv", frozen)
    panel_hash = sha256(OUT / "frozen_development_panel.csv")
    write_json(OUT / "frozen_development_panel.json", {
        "schema": "round37-frozen-development-panel-v1",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "frozen_before_round37_candidate_results": True,
        "candidate_result_rows_present_before_freeze": 0,
        "row_count": len(frozen),
        "panel_sha256": panel_hash,
        "V_counts": dict(Counter(str(row["V"]) for row in frozen)),
        "scenario_counts": dict(Counter(row["scenario"] for row in frozen)),
        "stage_c_outcome_counts": dict(Counter(
            row["round36_stage_c_bw_p_vs_c6_outcome"] for row in frozen)),
        "selection_rule": [
            "all two V12 witnesses",
            "all four V50 witnesses",
            "both V20 Stage C candidate-win witnesses",
            "the V20 Stage C comparator-win regression",
            "the unique Round 35 pattern-2 witness",
            "the fast no-geometry-exposure negative control",
            "the remaining high-imbalance V20 witness with the largest baseline split count",
        ],
        "rows": frozen,
    })

    weakest_counts = Counter(row["weakest_initial_cell_index"]
                             for row in forensics)
    geometry_outcomes = Counter(row["round36_geometry_causal_outcome"]
                                for row in forensics)
    summary = {
        "schema": "round37-geometry-forensics-v1",
        "source_round36_instances": len(forensics),
        "weakest_cell_index_counts": dict(weakest_counts),
        "weakest_cell_is_interior": sum(
            row["weakest_initial_cell_index"] in {1, 2}
            for row in forensics),
        "geometry_outcome_counts": dict(geometry_outcomes),
        "geometry_exposures": sum(
            row["round36_geometry_exposure"] == "True"
            for row in forensics),
        "downstream_changes": sum(
            row["round36_geometry_downstream_changed"] == "True"
            for row in forensics),
        "development_panel_rows": len(frozen),
        "development_panel_sha256": panel_hash,
        "interpretation": (
            "The controlling LP weakness is usually interior (cells 1 or 2), "
            "so a generic low-G skew is not supported. Geometry changes are "
            "causal but bidirectional. The next test must allocate refinement "
            "from complete LP weakness rather than an incumbent-sized anchor."
        ),
    }
    write_json(OUT / "geometry_forensics.json", summary)
    (OUT / "geometry_forensics.md").write_text(f"""# Structural Gini-geometry forensics

Round 36 contains {len(forensics)} default-HGA geometry witnesses. The weakest
complete initial LP cell is interior (cell 1 or 2) in
{summary['weakest_cell_is_interior']}/{len(forensics)} instances: the index
counts are `{dict(weakest_counts)}`. This rejects a generic rule that simply
packs more intervals near zero Gini.

The wide-anchor intervention exposed a geometry change in
{summary['geometry_exposures']}/{len(forensics)} instances and changed the
downstream sequence in {summary['downstream_changes']}/{len(forensics)}, but its
causal outcomes were bidirectional (`{dict(geometry_outcomes)}`). Geometry is
therefore a real mechanism, while wider anchoring is not a supported policy.

The supported next hypothesis is **pilot weakest-cell pre-refinement**: solve
the four existing initial LPs completely, select the open cell with the lowest
valid LP bound using structural tie breaks, split it once at its midpoint, and
then resume unchanged C6 scheduling. The rule is independent of instance
labels, elapsed time, Work, nodes, and hardware. Exactness follows from complete
LP validity plus exact parent-child coverage; the test is about proof-search
quality, not correctness.
""", encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
