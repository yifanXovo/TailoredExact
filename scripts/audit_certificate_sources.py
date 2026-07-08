#!/usr/bin/env python3
"""Audit compact-BC certificate-source attribution tables."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _fallback_rows_from_round_tables(root: Path) -> list[dict[str, str]]:
    """Build a source-class table for fixed-interval round packages.

    Older effectiveness rounds write certificate_source_summary*.csv directly.
    Fixed-interval strengthening rounds instead summarize rows in longrun and
    comparison CSVs.  This fallback keeps the audit meaningful for those
    packages without changing the stricter checks below.
    """

    candidates = [
        root / "dominant_bucket_longrun.csv",
        root / "adaptive_child_longrun.csv",
        root / "plain_vs_tailored_10800s.csv",
        root / "secondary_regression_summary.csv",
        root / "full_convergence_comparison.csv",
    ]
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for path in candidates:
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for source in csv.DictReader(handle):
                json_path = source.get("json_path") or source.get("result_file") or source.get("raw_json") or ""
                variant = source.get("variant") or source.get("best_variant") or source.get("row_class") or path.stem
                budget = source.get("budget_seconds") or source.get("time_budget_seconds") or ""
                key = (json_path, variant, budget)
                if key in seen:
                    continue
                seen.add(key)

                row_class = source.get("row_class", "")
                diagnostic = _truthy(source.get("diagnostic_only", ""))
                paper_role = source.get("paper_certificate_role", "")
                status = (source.get("status") or source.get("solver_status") or "").lower()
                certified = _truthy(source.get("certified", "")) or _truthy(source.get("certified_original_problem", ""))
                if "benchmark_only" in row_class or "benchmark" in paper_role or "plain_fixed_interval" in variant:
                    cls = "benchmark_only"
                elif diagnostic:
                    cls = "compact_bc_leaf_diagnostic"
                elif certified:
                    cls = "tailored_bc_certified"
                elif "model_size" in status:
                    cls = "model_size_limit"
                elif "tailored" in row_class or "tailored" in variant or "all_new" in variant or "bucket_" in variant or "sp_h" in variant:
                    cls = "tailored_bc_assisted_noncertified"
                else:
                    cls = "compact_bc_leaf_diagnostic"

                is_benchmark = cls == "benchmark_only"
                rows.append(
                    {
                        "row": source.get("leaf") or source.get("instance") or source.get("bucket_name") or path.stem,
                        "variant": variant,
                        "budget_seconds": budget,
                        "json_path": json_path,
                        "selected_for_summary": source.get("selected_for_summary", "false"),
                        "certified_original_problem": "true" if certified else "false",
                        "row_certificate_source_class": cls,
                        "leaf_solver_row": "false" if is_benchmark else "true",
                        "compact_bc_called_this_row": "false" if is_benchmark else "true",
                        "compact_bc_called_any_child": "false",
                        "parent_row_compact_bc_called_any_leaf": "false",
                        "compact_bc_called_any_leaf": "false" if is_benchmark else "true",
                        "compact_bc_contributed_to_certificate": "true" if certified and cls == "tailored_bc_certified" else "false",
                        "compact_bc_diagnostic_only": "true" if cls in {"compact_bc_leaf_diagnostic", "benchmark_only"} else "false",
                        "paper_certificate_contamination": "false",
                        "inconsistent_source_label_detected": "false",
                    }
                )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", default="results/gf_compact_bc_effectiveness_round")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    root = Path(args.results)
    src = root / "certificate_source_summary_v3.csv"
    if not src.exists():
        src = root / "certificate_source_summary_v2.csv"
    if not src.exists():
        src = root / "certificate_source_summary.csv"
    rows = list(csv.DictReader(src.open(newline="", encoding="utf-8"))) if src.exists() else []
    if not rows:
        rows = _fallback_rows_from_round_tables(root)
    failures = 0
    out_rows = []
    allowed = {
        "relaxation_only_certified",
        "relaxation_only_noncertified",
        "compact_bc_assisted_certified",
        "compact_bc_assisted_noncertified",
        "mixed_certified",
        "mixed_noncertified",
        "compact_bc_leaf_diagnostic",
        "diagnostic",
        "benchmark_only",
        "wrapper_checkpoint_only",
        "model_size_limit",
        "invalid_or_unknown",
        "static_fallback",
        "tailored_bc_certified",
        "tailored_bc_assisted_noncertified",
        # Backward-compatible classes from the first effectiveness package.
        "relaxation_only",
        "relaxation_plus_compact_bc",
        "relaxation_plus_compact_bc_noncertified",
        "unresolved",
    }
    for row in rows:
        reasons = []
        cls = row.get("row_certificate_source_class", "")
        certified = str(row.get("certified_original_problem", "")).lower() == "true"
        if cls not in allowed:
            reasons.append("unknown_row_source_class")
        if certified and "noncertified" in cls:
            reasons.append("optimal_row_has_noncertified_source_class")
        if certified and cls in {"unresolved", "wrapper_checkpoint_only", "invalid_or_unknown", "model_size_limit"}:
            reasons.append("certified_row_has_invalid_source_class")
        if certified and cls == "static_fallback":
            reasons.append("certified_row_static_fallback_not_true_tailored_callback")
        if str(row.get("inconsistent_source_label_detected", "")).lower() == "true":
            reasons.append("inconsistent_source_label_detected")
        if str(row.get("selected_for_summary", "")).lower() == "true" and cls in {"compact_bc_leaf_diagnostic", "benchmark_only"}:
            reasons.append("diagnostic_or_benchmark_selected_as_paper_summary")
        leaf_solver = str(row.get("leaf_solver_row", "")).lower() == "true"
        if leaf_solver and str(row.get("compact_bc_called_this_row", "")).lower() != "true":
            reasons.append("leaf_solver_row_without_compact_bc_call")
        if cls == "compact_bc_leaf_diagnostic" and row.get("compact_bc_called_this_row", "") != "" and str(row.get("compact_bc_called_this_row", "")).lower() != "true":
            reasons.append("diagnostic_leaf_label_without_compact_bc_call")
        if str(row.get("paper_certificate_contamination", "")).lower() == "true":
            reasons.append("paper_certificate_contamination")
        if str(row.get("parent_row_compact_bc_called_any_leaf", "")).lower() == "true" and str(row.get("compact_bc_called_any_child", "")).lower() != "true":
            reasons.append("parent_child_compact_bc_aggregation_missing")
        if reasons:
            failures += 1
        out_rows.append({**row, "audit_passed": not reasons, "failures": "|".join(reasons)})
    out = Path(args.out) if args.out else root / "certificate_source_audit.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out_rows:
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(out_rows[0]))
            writer.writeheader()
            writer.writerows(out_rows)
    else:
        out.write_text("", encoding="utf-8")
    print(f"audited_rows={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
