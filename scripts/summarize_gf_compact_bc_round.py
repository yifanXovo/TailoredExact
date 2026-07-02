#!/usr/bin/env python3
"""Summarize GF compact-BC round JSON and interval traces."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def iter_json_objects(raw_dir: Path) -> Iterable[tuple[Path, Dict[str, Any]]]:
    for path in sorted(raw_dir.rglob("*.json")):
        if path.name.endswith(".trace.json"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and isinstance(data.get("results"), list):
            for item in data["results"]:
                if isinstance(item, dict):
                    yield path, item
        elif isinstance(data, dict) and "trace_schema" not in data:
            yield path, data


def pick(d: Dict[str, Any], *keys: str) -> Dict[str, Any]:
    return {k: d.get(k, "") for k in keys}


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: List[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", default="results/gf_compact_bc_round/raw")
    parser.add_argument("--out-dir", default="results/gf_compact_bc_round")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)

    summary_rows: List[Dict[str, Any]] = []
    cplex_rows: List[Dict[str, Any]] = []
    strengthening_rows: List[Dict[str, Any]] = []
    interval_rows: List[Dict[str, Any]] = []

    for path, d in iter_json_objects(raw_dir):
        method = str(d.get("method", ""))
        row = {
            "file": str(path),
            **pick(
                d,
                "instance_name",
                "algorithm_preset",
                "method",
                "status",
                "certified_original_problem",
                "objective",
                "lower_bound",
                "upper_bound",
                "gap",
                "runtime_seconds",
                "unresolved_intervals",
                "invalid_bound_intervals",
                "open_nodes",
                "compact_interval_bc_enabled",
                "compact_interval_bc_closed_leaves",
                "compact_interval_bc_timed_out_leaves",
                "compact_bc_bound_valid",
                "compact_bc_bound_scope",
                "compact_bc_certificate_valid",
                "compact_bc_enabled_families_requested",
                "compact_bc_enabled_families_effective",
                "compact_bc_total_cuts_added_by_family",
                "compact_bc_total_domains_tightened_by_family",
                "compact_bc_total_root_cut_rounds",
                "compact_bc_total_leaf_nodes",
                "compact_bc_total_solver_time",
                "cplex_threads",
                "mip_threads",
                "compact_bc_solver_threads",
                "solver_thread_policy",
                "thread_fairness_class",
                "ablation_variant_semantics",
                "certificate_uses_bpc_tree",
                "no_archive_scanning",
                "no_external_known_ub",
            ),
        }
        summary_rows.append(row)
        if method == "cplex":
            cplex_rows.append(
                {
                    "file": str(path),
                    **pick(
                        d,
                        "instance_name",
                        "method",
                        "status",
                        "objective",
                        "lower_bound",
                        "upper_bound",
                        "gap",
                        "runtime_seconds",
                        "nodes",
                        "cplex_threads",
                        "solver_thread_policy",
                        "thread_fairness_class",
                        "verifier_passed",
                    ),
                }
            )
        if d.get("compact_interval_bc_enabled"):
            strengthening_rows.append(
                {
                    "file": str(path),
                    **pick(
                        d,
                        "instance_name",
                        "compact_bc_cut_profile",
                        "compact_bc_enabled_cut_families",
                        "compact_bc_enabled_families_requested",
                        "compact_bc_enabled_families_effective",
                        "compact_bc_cuts_added_by_family",
                        "compact_bc_domains_tightened_by_family",
                        "compact_bc_total_cuts_added_by_family",
                        "compact_bc_total_domains_tightened_by_family",
                        "compact_bc_total_root_cut_rounds",
                        "compact_bc_total_leaf_nodes",
                        "compact_bc_total_solver_time",
                        "compact_bc_solver_threads",
                        "thread_fairness_class",
                        "compact_bc_direct_gini_cap_rows_added",
                        "compact_bc_direct_gini_floor_rows_added",
                        "compact_bc_tight_mccormick_rows_added",
                        "compact_bc_inventory_conservation_rows_added",
                        "compact_bc_movement_reachability_domains_tightened",
                        "compact_bc_visit_inventory_linking_rows_added",
                        "compact_bc_objective_estimator_cutoff_rows_added",
                        "compact_bc_penalty_lb",
                        "compact_bc_penalty_lb_rows_added",
                        "compact_bc_support_duration_pair_cuts_added",
                        "compact_bc_support_duration_triple_cuts_added",
                        "compact_bc_pairwise_transfer_compatibility_cuts_added",
                    ),
                }
            )

    for csv_path in sorted(raw_dir.glob("*.auto_oracle.csv")):
        with csv_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                row = {"source_csv": str(csv_path), **row}
                interval_rows.append(row)

    write_csv(out_dir / "gf_compact_bc_summary.csv", summary_rows)
    write_csv(out_dir / "plain_cplex_comparison.csv", cplex_rows)
    write_csv(out_dir / "model_strengthening_audit.csv", strengthening_rows)
    write_csv(out_dir / "interval_leaf_status.csv", interval_rows)
    print(
        f"wrote {len(summary_rows)} summary rows, {len(cplex_rows)} CPLEX rows, "
        f"{len(interval_rows)} interval rows"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
