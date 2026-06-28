#!/usr/bin/env python3
"""Summarize V20 certificate-round results without upgrading diagnostics."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "results" / "v20_certificate_round"
RAW = ROUND / "raw"
PREV = ROOT / "results" / "relaxation_closure_round" / "raw"


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def result_row(name: str, path: Path) -> dict:
    j = load_json(path)
    return {
        "row": name,
        "instance": j.get("instance", j.get("instance_name", "")),
        "instance_scope": j.get("instance_scope", ""),
        "status": j.get("status", ""),
        "objective": j.get("objective", ""),
        "lower_bound": j.get("lower_bound", ""),
        "upper_bound": j.get("upper_bound", ""),
        "gap": j.get("gap", ""),
        "runtime_seconds": j.get("runtime_seconds", ""),
        "certified_original_problem": j.get("certified_original_problem", ""),
        "unresolved_intervals": j.get("unresolved_intervals", ""),
        "open_nodes": j.get("open_nodes", ""),
        "large_compact_flow_relaxation": j.get("large_compact_flow_relaxation", ""),
        "relaxation_portfolio_mode": j.get("relaxation_portfolio_mode", ""),
        "relaxation_certificate_mode": j.get("relaxation_certificate_mode", ""),
        "cutoff_feasibility_attempted": j.get("cutoff_feasibility_attempted", ""),
        "cutoff_feasibility_infeasible": j.get("cutoff_feasibility_infeasible", ""),
        "cutoff_feasibility_status": j.get("cutoff_feasibility_status", ""),
        "selected_relaxation_variant": j.get("selected_relaxation_variant", ""),
        "result_file": str(path),
    }


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    ROUND.mkdir(parents=True, exist_ok=True)
    rows = []
    for name in [
        "high_imbalance_seed3202_exhaustive_300s",
        "v4_smoke_30s",
        "v12_m2_canonical_300s",
        "v12_m1_adaptive_300s",
        "v12_m1_adaptive_600s",
    ]:
        path = RAW / f"{name}.json"
        if path.exists():
            rows.append(result_row(name, path))
    write_csv(ROUND / "high_imbalance_seed3202_certificate_attempt.csv",
              [r for r in rows if "high_imbalance_seed3202" in r["row"]])
    write_csv(ROUND / "v12_stability_summary.csv",
              [r for r in rows if r["row"].startswith("v")])

    focused = read_csv(ROUND / "interval_closure_trace.csv")
    previous = read_csv(PREV / "high_imbalance_seed3202_miplight_1200s.intervals.csv")
    interval_rows = []
    focus_by_id = {r["interval_id"]: r for r in focused}
    for r in previous:
        if r.get("interval_status") in {"unresolved", "replaced_by_children"}:
            f = focus_by_id.get(r.get("interval_id", ""), {})
            interval_rows.append({
                "interval_id": r.get("interval_id", ""),
                "gamma_L": r.get("gamma_L", ""),
                "gamma_U": r.get("gamma_U", ""),
                "previous_interval_lb": r.get("interval_lower_bound", ""),
                "previous_status": r.get("interval_status", ""),
                "focused_status": f.get("focused_status", ""),
                "focused_lb": f.get("focused_lb", ""),
                "focused_gap": f.get("focused_gap", ""),
                "focused_safe_to_merge": f.get("safe_to_merge_full_ledger", "False"),
                "diagnosis": "focused run did not produce safe full-ledger closure" if f else "not targeted",
            })
    write_csv(ROUND / "high_imbalance_seed3202_interval_status.csv", interval_rows)

    exhaustive = []
    interval_csv = RAW / "high_imbalance_seed3202_exhaustive_300s.intervals.csv"
    for r in read_csv(interval_csv):
        exhaustive.append({
            "interval_id": r.get("interval_id", ""),
            "gamma_L": r.get("gamma_L", ""),
            "gamma_U": r.get("gamma_U", ""),
            "interval_status": r.get("interval_status", ""),
            "interval_lower_bound": r.get("interval_lower_bound", ""),
            "incumbent_upper_bound": r.get("incumbent_upper_bound", ""),
            "relaxation_portfolio_mode": r.get("relaxation_portfolio_mode", ""),
            "relaxation_variants_tried": r.get("relaxation_variants_tried", ""),
            "selected_relaxation_variant": r.get("selected_relaxation_variant", ""),
            "variant_bound_improvement": r.get("variant_bound_improvement", ""),
            "fathomed": str(r.get("interval_status", "") == "bound_fathomed"),
        })
    write_csv(ROUND / "exhaustive_variant_trace.csv", exhaustive)
    write_csv(ROUND / "cutoff_feasibility_ablation.csv", [
        {
            "row": r["row"],
            "cutoff_feasibility_attempted": r["cutoff_feasibility_attempted"],
            "cutoff_feasibility_infeasible": r["cutoff_feasibility_infeasible"],
            "cutoff_feasibility_status": r["cutoff_feasibility_status"],
            "gap": r["gap"],
            "result_file": r["result_file"],
        }
        for r in rows if "high_imbalance" in r["row"]
    ])
    write_csv(ROUND / "secondary_targets_summary.csv", [
        {"instance": "high_imbalance_seed3201", "status": "not rerun this round", "previous_best_gap": "0.0682096293371", "notes": "secondary target deferred because priority target did not close"},
        {"instance": "tight_T_seed3102", "status": "not rerun this round", "previous_best_gap": "0.168318012854", "notes": "secondary target deferred because priority target did not close"},
        {"instance": "moderate_seed3302", "status": "not rerun this round", "previous_best_gap": "0.329231102492", "notes": "secondary target deferred because priority target did not close"},
    ])


if __name__ == "__main__":
    main()
