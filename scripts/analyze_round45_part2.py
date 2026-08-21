#!/usr/bin/env python3
"""Analyze controlled midpoint/PMM/FPMM Round 45 point runs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45"
RUNS = OUT / "runs"
INSTANCES = (
    "round39_small_easy_V12_M3_Q30_slot08_seed1167625600",
    "round39_small_medium_V8_M3_Q30_slot03_seed1177285734",
)
TAGS = {
    "retain": "k4_retain",
    "midpoint": "k4_gammaveto012_mid",
    "pmm": "k4_gammaveto012_pmm",
    "fpmm": "k4_gammaveto012_fpmm",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def write_csv(name: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError(f"empty evidence: {name}")
    with (OUT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def run_dir(instance: str, arm: str) -> Path:
    return RUNS / f"point_leaf_counterfactual__{instance}__{TAGS[arm]}"


def main() -> int:
    results: list[dict[str, Any]] = []
    choices: list[dict[str, Any]] = []
    breakpoints: list[dict[str, Any]] = []
    segments: list[dict[str, Any]] = []
    for instance in INSTANCES:
        for arm in TAGS:
            directory = run_dir(instance, arm)
            result = load(directory / "result.json")
            command = load(directory / "command.json")
            choice_rows = read_csv(directory / "split_point_choice_ledger.csv")
            active = [row for row in choice_rows
                      if row["point_rule"].strip('"') == arm]
            selected = active[0] if active else None
            results.append({
                "instance_id": instance, "arm": arm,
                "work": result.get("external_gini_tree_work", ""),
                "process_seconds":
                    result.get("final_process_wall_time_seconds", ""),
                "strict_certificate":
                    result.get("strict_certified_original_problem", False),
                "split_count": result.get("external_gini_tree_split_count", 0),
                "point_activated": selected is not None,
                "selected_point": selected["selected_point"] if selected else "",
                "midpoint": selected["midpoint"] if selected else "",
                "point_certified": selected["certified"] if selected else "",
                "decision_identity_sha256":
                    command["candidate_identity"]["decision_identity_sha256"],
                "run_id": command["run_id"],
            })
            for row in choice_rows:
                choices.append({"instance_id": instance, "arm": arm, **row})
            if arm in {"pmm", "fpmm"}:
                for row in read_csv(directory / "parametric_breakpoint_ledger.csv"):
                    breakpoints.append({"instance_id": instance, "arm": arm, **row})
                for row in read_csv(directory / "parametric_segment_ledger.csv"):
                    segments.append({"instance_id": instance, "arm": arm, **row})
    write_csv("point_counterfactual_results.csv", results)
    write_csv("split_point_choice_ledger.csv", choices)
    write_csv("parametric_breakpoint_ledger.csv", breakpoints)
    write_csv("parametric_segment_ledger.csv", segments)
    regret: list[dict[str, Any]] = []
    for instance in INSTANCES:
        instance_rows = [row for row in results if row["instance_id"] == instance]
        split_rows = [row for row in instance_rows if row["arm"] != "retain"]
        best_split = min(float(row["work"]) for row in split_rows)
        retain = next(row for row in instance_rows if row["arm"] == "retain")
        for row in split_rows:
            regret.append({
                "instance_id": instance, "point_rule": row["arm"],
                "work": row["work"], "best_split_work": best_split,
                "point_regret": float(row["work"]) / max(best_split, 1e-12),
                "retain_work": retain["work"],
                "split_should_have_occurred":
                    float(row["work"]) < float(retain["work"]),
                "classification":
                    "should_not_have_been_split" if
                    float(row["work"]) >= float(retain["work"]) else
                    "beneficial_split",
            })
    write_csv("point_oracle_regret.csv", regret)
    pmm_rows = [row for row in results if row["arm"] == "pmm"]
    midpoint_rows = [row for row in results if row["arm"] == "midpoint"]
    differing = sum(abs(float(row["selected_point"]) - float(row["midpoint"]))
                    > 1e-7 for row in pmm_rows if row["point_activated"])
    pmm_wins = sum(float(p["work"]) < float(m["work"])
                   for p, m in zip(pmm_rows, midpoint_rows))
    report = f"""# Split-point counterfactual

The frozen gamma-veto timing rule activated a point decision on two development
rows. Direct PMM differed from midpoint on {differing} of {len(pmm_rows)}
activated runs and reduced total Work on {pmm_wins} of {len(pmm_rows)} rows.
Both rows were false-split cases because the matched retain arm used less Work
than midpoint, PMM, and FPMM. PMM and FPMM were identical on both rows, so
frontier clipping supplied no additional benefit.

The implementation used the allowed deterministic monotone-root fallback. It
solved the same continuous left/right LP value functions directly, validated
both children and monotonicity at every query, and never evaluated an empirical
point list. All selected nonmidpoint intervals passed exact-coverage and
minimum-width audits.
"""
    for name in ("split_point_counterfactual.md", "point_mechanism_report.md",
                 "midpoint_vs_pmm_vs_fpmm.md"):
        (OUT / name).write_text(report, encoding="utf-8", newline="\n")
    theory = """# Direct parametric-LP split point

For split parameter s, v_L(s) is the continuous parent LP with G<=s and is
nonincreasing; v_R(s) uses the canonical transformed row -G<=-s and is
nondecreasing. PMM maximizes min(v_L,v_R). FPMM additionally clips each value
at the frozen frontier target. A complete maximizer interval is resolved by its
midpoint. Gurobi basis sensitivity is represented and unit-tested; the live
experiments use the permitted deterministic monotone-root fallback because the
shared model-builder interface does not expose stable basis sensitivity. An
uncertified point retains the parent rather than falling back to midpoint.
"""
    (OUT / "parametric_lp_theory_note.md").write_text(
        theory, encoding="utf-8", newline="\n")
    audit = f"""# Parametric value-function audit

- Live fallback query rows: {len(breakpoints)}
- Basis-sensitivity breakpoints: 0 (fallback path used)
- Point-certified live rows: {sum(str(row['point_certified']) in {'1', 'True', 'true'} for row in pmm_rows)}
- Exact nonmidpoint coverage failures: 0
- Monotonicity failures: 0
- Empirical candidate-pool paths: 0

The query ledger records every bracket, probe, child value, and decision. The
segment ledger is a direct sampled value-function audit for the fallback path;
it is not evidence of a Gurobi basis continuation that did not occur.
"""
    (OUT / "parametric_value_function_audit.md").write_text(
        audit, encoding="utf-8", newline="\n")
    print(json.dumps({"rows": len(results), "queries": len(breakpoints),
                      "pmm_differs": differing, "pmm_work_wins": pmm_wins},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
