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
        time_budget = data.get("time_budget_seconds", "")
        progress_log = str(data.get("progress_log") or data.get("progress_log_path") or "")
        model_size_limit = status == "model_size_limit" or bool(
            str(data.get("compact_bc_model_size_stop_reason", ""))
        )
        force_diag = as_bool(data.get("compact_bc_diagnostic_force_leaf_solve"))
        aggressive_low_gini = as_bool(data.get("compact_bc_low_gini_aggressive_diagnostic"))
        paper_row = (
            preset in {"paper-gf-compact-bc", "paper-gf-tailored-bc"} and
            method == "gcap-frontier" and
            not force_diag
        )
        failure_reasons: List[str] = []

        if paper_row and str(data.get("compact_bc_rejection_reason", "")) and as_bool(data.get("certified_original_problem")):
            failure_reasons.append("compact_bc_rejection_reason_present")
        if paper_row and "diagnostic" in enabled and as_bool(data.get("certified_original_problem")):
            failure_reasons.append("diagnostic_cut_used_by_certified_paper_row")
        if paper_row and as_bool(data.get("certificate_uses_bpc_tree")):
            failure_reasons.append("bpc_used_by_compact_bc_paper_row")
        if paper_row and aggressive_low_gini and as_bool(data.get("certified_original_problem")):
            failure_reasons.append("aggressive_low_gini_diagnostic_used_by_certificate")
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
        if paper_row and time_budget in {"", None}:
            failure_reasons.append("paper_row_missing_time_budget_seconds")
        if paper_row and not progress_log and not model_size_limit:
            failure_reasons.append("paper_row_missing_progress_log_field")
        if paper_row and as_bool(data.get("certified_original_problem")):
            mode = str(data.get("compact_bc_receiver_source_cover_mode", ""))
            if "diagnostic" in mode:
                failure_reasons.append("diagnostic_receiver_cover_used_by_certificate")
            if not str(data.get("compact_bc_total_cuts_added_by_family", "")):
                failure_reasons.append("certified_row_missing_top_level_cut_aggregation")
        if force_diag and as_bool(data.get("certified_original_problem")):
            failure_reasons.append("diagnostic_force_leaf_row_marked_certified")
        if preset == "paper-gf-tailored-bc":
            callback_available = as_bool(data.get("tailored_bc_callback_available"))
            callback_claim = (
                as_bool(data.get("tailored_bc_user_cut_callback_enabled")) or
                as_bool(data.get("tailored_bc_lazy_callback_enabled")) or
                as_bool(data.get("tailored_bc_incumbent_callback_enabled")) or
                as_bool(data.get("tailored_bc_branch_callback_enabled")) or
                str(data.get("tailored_bc_source_class", "")) == "tailored_bc_certified"
            )
            if callback_claim and not callback_available:
                failure_reasons.append("tailored_bc_callback_claim_without_callback_api")
            if paper_row and as_bool(data.get("certified_original_problem")) and str(data.get("tailored_bc_source_class", "")) == "static_fallback":
                failure_reasons.append("tailored_bc_static_fallback_marked_as_paper_callback_certificate")
        if method == "interval-cutoff-oracle" and as_bool(data.get("compact_interval_bc_enabled")):
            if cut_scope not in {"original_fixed_interval", "none"}:
                failure_reasons.append("compact_bc_leaf_bad_bound_scope")
            if data.get("compact_bc_bound_valid", "") == "":
                failure_reasons.append("compact_bc_leaf_missing_bound_valid")
            if str(data.get("compact_bc_called_this_row", "")).lower() == "false":
                failure_reasons.append("compact_bc_leaf_reports_not_called")

        if failure_reasons:
            failures += 1
        rows.append(
            {
                "file": str(path),
                "method": method,
                "algorithm_preset": preset,
                "status": status,
                "thread_fairness_class": fairness,
                "time_budget_seconds": time_budget,
                "progress_log": progress_log,
                "compact_bc_enabled_families_effective": enabled,
                "compact_bc_diagnostic_force_leaf_solve": force_diag,
                "compact_bc_low_gini_aggressive_diagnostic": aggressive_low_gini,
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
            "time_budget_seconds",
            "progress_log",
            "compact_bc_enabled_families_effective",
            "compact_bc_diagnostic_force_leaf_solve",
            "compact_bc_low_gini_aggressive_diagnostic",
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
