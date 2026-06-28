#!/usr/bin/env python3
"""Summarize the V20 replication/certificate mini-suite."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUND = ROOT / "results" / "v20_replication_round"
RAW = ROUND / "raw"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


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


def result_row(label: str, path: Path, notes: str = "") -> dict:
    j = load_json(path)
    if not j:
        return {"row": label, "status": "missing", "result_file": str(path), "notes": notes}
    return {
        "row": label,
        "instance": j.get("instance_name", j.get("instance", "")),
        "instance_scope": j.get("instance_scope", ""),
        "algorithm_preset": j.get("algorithm_preset", ""),
        "status": j.get("status", ""),
        "objective": j.get("objective", ""),
        "lower_bound": j.get("lower_bound", ""),
        "upper_bound": j.get("upper_bound", ""),
        "gap": j.get("gap", ""),
        "runtime_seconds": j.get("runtime_seconds", ""),
        "certified_original_problem": j.get("certified_original_problem", ""),
        "verifier_passed": j.get("verifier_passed", ""),
        "unresolved_intervals": j.get("unresolved_intervals", ""),
        "invalid_bound_intervals": j.get("invalid_bound_intervals", ""),
        "open_nodes": j.get("open_nodes", ""),
        "frontier_covers_all_improving_gini_values": j.get("frontier_covers_all_improving_gini_values", ""),
        "frontier_range_certificate_scope": j.get("frontier_range_certificate_scope", ""),
        "large_compact_flow_relaxation": j.get("large_compact_flow_relaxation", ""),
        "route_mask_all_subset_enumeration_certifying": j.get("route_mask_all_subset_enumeration_certifying", ""),
        "incumbent_source_category": j.get("incumbent_source_category", ""),
        "incumbent_source_contributes_lower_bound": j.get("incumbent_source_contributes_lower_bound", ""),
        "result_file": str(path),
        "notes": notes,
    }


def interval_fingerprint(path: Path) -> str:
    rows = read_csv(path)
    parts = []
    for r in rows:
        if r.get("interval_status") != "replaced_by_children":
            parts.append(
                f"{r.get('gamma_L')}:{r.get('gamma_U')}:{r.get('interval_status')}:{r.get('certificate_basis')}"
            )
    return "|".join(parts)


def main() -> None:
    reps = []
    for i in range(1, 4):
        name = f"high_imbalance_seed3202_rep{i}"
        row = result_row(name, RAW / f"{name}.json")
        row["interval_ledger_fingerprint"] = interval_fingerprint(RAW / f"{name}.intervals.csv")
        reps.append(row)
    if reps:
        first = reps[0].get("interval_ledger_fingerprint", "")
        for r in reps:
            r["ledger_structurally_identical_to_rep1"] = str(r.get("interval_ledger_fingerprint", "") == first).lower()
            r["objective_identical_to_rep1"] = str(r.get("objective") == reps[0].get("objective")).lower()
    write_csv(ROUND / "high_imbalance_seed3202_repro_summary.csv", reps)

    previous_rows = [
        result_row("previous_v20_certificate_round_full", ROOT / "results/v20_exact_certificate_round/raw/high_imbalance_seed3202_reproduced_baseline.json"),
        result_row("previous_exhaustive_300s", ROOT / "results/v20_certificate_round/raw/high_imbalance_seed3202_exhaustive_300s.json"),
        result_row("current_rep1", RAW / "high_imbalance_seed3202_rep1.json"),
    ]
    opt_fields = [
        "algorithm_preset", "frontier_intervals", "large_compact_flow_relaxation",
        "relaxation_certificate_mode", "relaxation_portfolio_mode",
        "route_mask_all_subset_enumeration_enabled", "route_mask_all_subset_enumeration_certifying",
        "incumbent_source_category", "instance_hash", "T", "lambda",
    ]
    diff_rows = []
    for r in previous_rows:
        j = load_json(Path(r["result_file"]))
        out = {"row": r["row"], "status": r["status"], "gap": r["gap"], "runtime_seconds": r["runtime_seconds"]}
        for f in opt_fields:
            out[f] = j.get(f, "")
        out["frontier_scheduling_mode"] = j.get("frontier_scheduling_mode", "")
        out["large_compact_flow_connectivity_enabled"] = j.get("large_compact_flow_connectivity_enabled", "")
        out["station_residual_cover_cuts_enabled"] = j.get("station_residual_cover_cuts_enabled", "")
        out["v20_cover_cuts_added"] = j.get("v20_cover_cuts_added", "")
        diff_rows.append(out)
    write_csv(ROUND / "high_imbalance_seed3202_option_diff.csv", diff_rows)

    instances = [
        ("high_imbalance_seed3201", "full_3600", ""),
        ("tight_T_seed3101", "full_3600", ""),
        ("tight_T_seed3102", "full_3600", ""),
        ("moderate_seed3301", "full_3600", "oracle closed 9 final leaves; interval 1 remains open after 600s oracle and BPC fallback"),
        ("moderate_seed3302", "full_1200", "completed noncertified row; runtime exceeded requested 1200s budget"),
    ]
    mini = []
    for name, suffix, notes in instances:
        mini.append(result_row(name, RAW / f"{name}.{suffix}.json", notes))
    write_csv(ROUND / "v20_minisuite_summary.csv", mini)

    interval_rows = []
    for name, suffix, notes in instances:
        for r in read_csv(RAW / f"{name}.{suffix}.intervals.csv"):
            if r.get("interval_status") in {"unresolved", "replaced_by_children"}:
                interval_rows.append({
                    "instance": name,
                    "interval_id": r.get("interval_id", ""),
                    "gamma_L": r.get("gamma_L", ""),
                    "gamma_U": r.get("gamma_U", ""),
                    "interval_lower_bound": r.get("interval_lower_bound", ""),
                    "incumbent_upper_bound": r.get("incumbent_upper_bound", ""),
                    "interval_status": r.get("interval_status", ""),
                    "certificate_basis": r.get("certificate_basis", ""),
                    "open_nodes": r.get("open_nodes", ""),
                    "notes": notes,
                })
    write_csv(ROUND / "v20_minisuite_interval_status.csv", interval_rows)

    oracle_rows = []
    for p in sorted((ROUND / "oracle").glob("*.oracle*.csv")):
        for r in read_csv(p):
            r = dict(r)
            r["oracle_summary_file"] = str(p)
            oracle_rows.append(r)
    write_csv(ROUND / "v20_minisuite_oracle_results.csv", oracle_rows)
    write_csv(ROUND / "interval_oracle_ablation.csv", oracle_rows)

    write_csv(ROUND / "v12_stability_summary.csv", [
        result_row("v4_smoke_30s", RAW / "v4_smoke_30s.json"),
        result_row("v12_m2_canonical_300s", RAW / "v12_m2_canonical_300s.json"),
        result_row("v12_m1_diagnostic_300s", RAW / "v12_m1_diagnostic_300s.json"),
        result_row("v12_m1_600s", RAW / "v12_m1_600s.json"),
    ])

    write_csv(ROUND / "ledger_merge_audit.csv", read_csv(ROUND / "moderate_seed3301_ledger_merge_audit.csv"))


if __name__ == "__main__":
    main()
