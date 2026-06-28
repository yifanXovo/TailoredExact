#!/usr/bin/env python3
"""Create conservative summaries for the V20 exact-certificate round."""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "results" / "v20_exact_certificate_round"
RAW = ROUND / "raw"


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
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def result_row(label: str, path: Path) -> dict:
    if not path.exists():
        return {"row": label, "status": "missing", "result_file": str(path)}
    r = load_json(path)
    return {
        "row": label,
        "instance": r.get("instance", r.get("instance_name", "")),
        "instance_scope": r.get("instance_scope", ""),
        "method": r.get("method", ""),
        "status": r.get("status", ""),
        "objective": r.get("objective", ""),
        "lower_bound": r.get("lower_bound", ""),
        "upper_bound": r.get("upper_bound", ""),
        "gap": r.get("gap", ""),
        "runtime_seconds": r.get("runtime_seconds", ""),
        "certified_original_problem": r.get("certified_original_problem", ""),
        "verifier_passed": r.get("verifier_passed", ""),
        "unresolved_intervals": r.get("unresolved_intervals", ""),
        "invalid_bound_intervals": r.get("invalid_bound_intervals", ""),
        "open_nodes": r.get("open_nodes", ""),
        "frontier_covers_all_improving_gini_values": r.get("frontier_covers_all_improving_gini_values", ""),
        "frontier_range_certificate_scope": r.get("frontier_range_certificate_scope", ""),
        "full_certificate_basis": r.get("full_certificate_basis", ""),
        "route_mask_all_subset_enumeration_certifying": r.get("route_mask_all_subset_enumeration_certifying", ""),
        "large_compact_flow_relaxation": r.get("large_compact_flow_relaxation", ""),
        "interval_exact_cutoff_certificate_basis": r.get("interval_exact_cutoff_certificate_basis", ""),
        "interval_exact_cutoff_solver_status": r.get("interval_exact_cutoff_solver_status", ""),
        "result_file": str(path),
    }


def main() -> None:
    ROUND.mkdir(parents=True, exist_ok=True)
    baseline = RAW / "high_imbalance_seed3202_reproduced_baseline.json"
    baseline_intervals = RAW / "high_imbalance_seed3202_reproduced_baseline.intervals.csv"
    if baseline.exists():
        shutil.copyfile(baseline, ROUND / "high_imbalance_seed3202_full_certificate.json")
    if baseline_intervals.exists():
        shutil.copyfile(baseline_intervals, ROUND / "high_imbalance_seed3202_full_certificate.intervals.csv")
        shutil.copyfile(baseline_intervals, ROUND / "high_imbalance_seed3202_reproduced_intervals.csv")

    write_csv(ROUND / "high_imbalance_seed3202_certificate_attempt.csv", [
        result_row("reproduced_full_frontier_mip_light_1200s_budget", baseline),
        result_row("oracle_smoke_interval_13", RAW / "smoke_interval_13_oracle.json"),
    ])
    write_csv(ROUND / "v12_stability_summary.csv", [
        result_row("v4_smoke_30s", RAW / "v4_smoke_30s.json"),
        result_row("v12_m2_canonical_300s", RAW / "v12_m2_canonical_300s.json"),
        result_row("v12_m1_diagnostic_300s", RAW / "v12_m1_diagnostic_300s.json"),
        result_row("v12_m1_600s", RAW / "v12_m1_600s.json"),
    ])
    write_csv(ROUND / "interval_bpc_fallback_results.csv", [
        {
            "instance": "high_imbalance_seed3202",
            "status": "not_run",
            "reason": "full-frontier reproduced baseline certified before exact BPC interval fallback was required",
            "pricing_closure": "",
            "interval_lb_improvement": "",
        }
    ])
    write_csv(ROUND / "secondary_target_summary.csv", [
        {
            "instance": "high_imbalance_seed3201",
            "status": "not_run",
            "reason": "priority high_imbalance_seed3202 certified; secondary target deferred",
        },
        {
            "instance": "tight_T_seed3102",
            "status": "not_run",
            "reason": "priority high_imbalance_seed3202 certified; secondary target deferred",
        },
    ])


if __name__ == "__main__":
    main()
