#!/usr/bin/env python3
"""Audit GF compact-BC summary/result semantics."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


DISALLOWED_NO_NEW = {
    "direct_gini",
    "interval_tight_mccormick",
    "inventory_conservation",
    "movement_reachability",
    "visit_inventory_linking",
    "objective_lower_estimator",
    "penalty_lower_bound",
    "pair_triple_route_duration",
    "pairwise_transfer",
    "receiver_source_cover",
}


def iter_json(raw_dir: Path) -> Iterable[tuple[Path, Dict[str, Any]]]:
    for path in sorted(raw_dir.rglob("*.json")):
        if path.name.endswith(".trace.json"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and "trace_schema" not in data:
            yield path, data


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/gf_compact_bc_strengthening_round")
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    results = Path(args.results)
    raw_dir = results / "raw"
    rows: List[Dict[str, Any]] = []
    failures = 0
    for path, data in iter_json(raw_dir):
        method = str(data.get("method", ""))
        preset = str(data.get("algorithm_preset", ""))
        status = str(data.get("status", ""))
        variant = str(data.get("ablation_variant_semantics", ""))
        enabled = str(
            data.get("compact_bc_enabled_families_effective")
            or data.get("compact_bc_enabled_cut_families")
            or ""
        )
        cut_scope = str(data.get("compact_bc_bound_scope", ""))
        fairness = str(data.get("thread_fairness_class", ""))
        paper_row = preset == "paper-gf-compact-bc" and method == "gcap-frontier"
        failure_reasons: List[str] = []

        if paper_row and str(data.get("compact_bc_rejection_reason", "")) and as_bool(data.get("certified_original_problem")):
            failure_reasons.append("compact_bc_rejection_reason_present")
        if paper_row and "diagnostic" in enabled and as_bool(data.get("certified_original_problem")):
            failure_reasons.append("diagnostic_cut_used_by_certified_paper_row")
        if paper_row and as_bool(data.get("certificate_uses_bpc_tree")):
            failure_reasons.append("bpc_used_by_compact_bc_paper_row")
        if paper_row and as_bool(data.get("route_mask_all_subset_enumeration_certifying")):
            failure_reasons.append("route_mask_certifying_in_compact_bc_row")
        if method == "cplex" and as_bool(data.get("certified_original_problem")):
            # Plain CPLEX can certify itself, but must remain classified benchmark-only.
            if str(data.get("method_scope", "")) != "plain_cplex":
                failure_reasons.append("cplex_row_not_benchmark_scoped")
        if "no_new_cuts" in path.name or variant == "no_new_cuts":
            lower_enabled = enabled.lower()
            for token in DISALLOWED_NO_NEW:
                if token in lower_enabled:
                    failure_reasons.append(f"no_new_cuts_lists_{token}")
                    break
        if paper_row and fairness and fairness != "one_thread_fair":
            failure_reasons.append("paper_row_not_single_thread_fair")
        if paper_row and not fairness:
            failure_reasons.append("paper_row_missing_thread_fairness_class")
        if paper_row and str(data.get("solver_thread_policy", "")) in {"", "unknown"}:
            failure_reasons.append("paper_row_missing_thread_policy")
        if paper_row and as_bool(data.get("certified_original_problem")):
            mode = str(data.get("compact_bc_receiver_source_cover_mode", ""))
            if "diagnostic" in mode:
                failure_reasons.append("diagnostic_receiver_cover_used_by_certificate")
            if not str(data.get("compact_bc_total_cuts_added_by_family", "")):
                failure_reasons.append("certified_row_missing_top_level_cut_aggregation")
        if method == "interval-cutoff-oracle" and as_bool(data.get("compact_interval_bc_enabled")):
            if cut_scope not in {"original_fixed_interval", "none"}:
                failure_reasons.append("compact_bc_leaf_bad_bound_scope")
            if data.get("compact_bc_bound_valid", "") == "":
                failure_reasons.append("compact_bc_leaf_missing_bound_valid")

        if failure_reasons:
            failures += 1
        rows.append(
            {
                "file": str(path),
                "method": method,
                "algorithm_preset": preset,
                "status": status,
                "thread_fairness_class": fairness,
                "compact_bc_enabled_families_effective": enabled,
                "audit_passed": not failure_reasons,
                "failures": "|".join(failure_reasons),
            }
        )

    out_path = Path(args.out) if args.out else results / "summary_cleanup_audit.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "file",
            "method",
            "algorithm_preset",
            "status",
            "thread_fairness_class",
            "compact_bc_enabled_families_effective",
            "audit_passed",
            "failures",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"audited_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
