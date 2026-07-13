#!/usr/bin/env python3
"""Audit ExactEBRP JSON results for paper-core BPC certificate safety.

The script is intentionally conservative.  A result passes only when the JSON
fields prove the certificate conditions; missing or ambiguous evidence is
reported as a failure for any original-problem optimality claim.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


TOL = 1e-7


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "on"}
    return False


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def nearly_equal(a: float, b: float, tol: float = TOL) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def collect_json_paths(inputs: Iterable[str]) -> List[Path]:
    paths: List[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            paths.extend(sorted(path.rglob("*.json")))
        elif path.is_file():
            paths.append(path)
        else:
            paths.append(path)
    return paths


def iter_result_objects(path: Path) -> Iterable[Tuple[str, Dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict) and isinstance(data.get("results"), list):
        for idx, item in enumerate(data["results"]):
            if isinstance(item, dict):
                yield f"{path}#{idx}", item
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, dict):
                yield f"{path}#{idx}", item
    elif isinstance(data, dict):
        if "trace_schema" in data:
            return
        yield str(path), data


def audit_one(source: str, result: Dict[str, Any]) -> Dict[str, Any]:
    failures: List[str] = []
    warnings: List[str] = []

    method = str(result.get("method", ""))
    status = str(result.get("status", ""))
    method_scope = str(result.get("method_scope", ""))
    is_bpc = as_bool(result.get("is_bpc", method == "gcap-frontier"))
    solves_original = as_bool(result.get("solves_original_objective", False))
    certified = as_bool(result.get("certified_original_problem", False))
    verifier = as_bool(result.get("verifier_passed", False))
    gap = as_float(result.get("gap", 0.0))
    objective = as_float(result.get("objective", 0.0))
    lower_bound = as_float(result.get("lower_bound", 0.0))
    upper_bound = as_float(result.get("upper_bound", 0.0))
    unresolved = as_int(result.get("unresolved_intervals", 0))
    invalid = as_int(result.get("invalid_bound_intervals", 0))
    open_nodes = as_int(result.get("open_nodes", 0))
    incumbent_source_category = str(result.get("incumbent_source_category", ""))
    incumbent_source_reproducible = as_bool(
        result.get("incumbent_source_is_paper_reproducible", False)
    )
    incumbent_source_lb = as_bool(
        result.get("incumbent_source_contributes_lower_bound", False)
    )
    sealed_run = as_bool(result.get("sealed_run", False))
    finalization_source = str(result.get("finalization_source", ""))
    benchmark_only = (
        as_bool(result.get("benchmark_only", False))
        or as_bool(result.get("plain_cplex_benchmark_row", False))
        or str(result.get("classification", "")) == "benchmark_only"
    )

    original_scope = (
        solves_original
        or method_scope in {
            "original_bpc",
            "original_compact",
            "plain_cplex",
        }
    ) and not benchmark_only

    if not as_bool(result.get("option_audit_consistent", True)):
        if certified or (status == "optimal" and original_scope):
            failures.append("option_audit_failed_but_certificate_or_optimal_claimed")

    if status == "optimal" and original_scope and not certified:
        failures.append("original_optimal_without_certified_original_problem")

    if method == "gcap-frontier" and status == "optimal" and not certified:
        failures.append("gcap_frontier_optimal_without_full_bpc_certificate")

    if incumbent_source_lb:
        failures.append("incumbent_source_marked_as_lower_bound_evidence")

    if incumbent_source_category == "diagnostic_archive" and incumbent_source_reproducible:
        failures.append("diagnostic_archive_marked_paper_reproducible")

    if sealed_run:
        if not finalization_source:
            failures.append("sealed_run_missing_finalization_source")
        if as_bool(result.get("sealed_run_forbidden_source_used", False)):
            failures.append("sealed_run_forbidden_source_used")
        if not as_bool(result.get("no_archive_scanning", False)):
            failures.append("sealed_run_archive_scanning_not_disabled")
        if not as_bool(result.get("no_external_known_ub", False)):
            failures.append("sealed_run_external_known_ub_used")
        if not as_bool(result.get("no_focus_only_certificate", False)):
            failures.append("sealed_run_focus_only_certificate_used")
        if incumbent_source_category == "diagnostic_archive":
            failures.append("sealed_run_used_diagnostic_archive_incumbent")

    if certified:
        if status != "optimal":
            failures.append("certified_but_status_not_optimal")
        if not original_scope and not benchmark_only:
            failures.append("certified_but_not_original_objective_scope")
        if not verifier:
            failures.append("certified_but_verifier_failed")
        if gap > TOL:
            failures.append("certified_positive_gap")
        if not nearly_equal(lower_bound, upper_bound):
            failures.append("certified_lower_upper_mismatch")
        if not nearly_equal(objective, upper_bound):
            failures.append("certified_objective_upper_mismatch")
        if unresolved != 0:
            failures.append("certified_with_unresolved_intervals")
        if invalid != 0:
            failures.append("certified_with_invalid_bound_intervals")
        if is_bpc:
            if sealed_run:
                if not as_bool(result.get("no_archive_scanning", False)):
                    failures.append("certified_sealed_bpc_with_archive_scanning")
                if not as_bool(result.get("no_external_known_ub", False)):
                    failures.append("certified_sealed_bpc_with_external_ub")
                if not as_bool(result.get("no_focus_only_certificate", False)):
                    failures.append("certified_sealed_bpc_focus_only")
                if as_bool(result.get("sealed_run_forbidden_source_used", False)):
                    failures.append("certified_sealed_bpc_forbidden_source")
            if open_nodes != 0:
                failures.append("certified_bpc_with_open_nodes")
            if not as_bool(result.get("frontier_covers_all_improving_gini_values", False)):
                failures.append("certified_bpc_without_full_improving_gini_coverage")
            if result.get("frontier_range_certificate_scope") != "original_full_improving_range":
                failures.append("certified_bpc_wrong_frontier_scope")
            if result.get("full_certificate_rejection_reason", "none") not in {"", "none", None}:
                failures.append("certified_bpc_has_rejection_reason")
            if "full_certificate_all_intervals_accounted" in result and not as_bool(
                result.get("full_certificate_all_intervals_accounted")
            ):
                failures.append("certified_bpc_not_all_intervals_accounted")
            if as_bool(result.get("full_certificate_requires_pricing_closure", False)) and not as_bool(
                result.get("full_certificate_pricing_closure_satisfied", False)
            ):
                failures.append("certified_bpc_pricing_required_but_unsatisfied")
            if as_int(result.get("frontier_tree_closed_interval_count", 0)) > 0:
                if not as_bool(result.get("pricing_completed_exactly", False)):
                    failures.append("certified_bpc_tree_without_exact_pricing_completion")
                if not as_bool(result.get("pricing_closure_certified_exact", False)):
                    failures.append("certified_bpc_tree_without_exact_pricing_closure")
                if as_int(result.get("pricing_closed_nodes", 0)) <= 0:
                    failures.append("certified_bpc_tree_without_closed_pricing_nodes")

    pricing_closure = as_bool(result.get("pricing_closure_certified_exact", False))
    best_rc = as_float(result.get("pricing_best_reduced_cost_any", 0.0))
    remaining_rc = as_float(result.get("pricing_remaining_negative_rc", 0.0))
    status_text = str(result.get("pricing_closure_status", ""))
    if pricing_closure:
        if not as_bool(result.get("pricing_completed_exactly", False)):
            failures.append("pricing_closure_claimed_without_exact_completion")
        if best_rc < -TOL or remaining_rc < -TOL:
            failures.append("pricing_closure_claimed_with_negative_reduced_cost")
        if as_bool(result.get("pricing_blocked_by_duplicate_projection", False)):
            failures.append("pricing_closure_claimed_with_duplicate_negative_blockage")
        if status_text and status_text not in {"exact_no_negative", "not_run"}:
            warnings.append("pricing_closure_status_not_exact_no_negative")

    if not as_bool(result.get("route_mask_all_subset_enumeration_enabled", True)) and as_bool(
        result.get("route_mask_all_subset_enumeration_certifying", False)
    ):
        failures.append("route_mask_certifying_while_all_subset_enumeration_disabled")

    if as_bool(result.get("relaxed_rmp_certificate_valid", False)) and not as_bool(
        result.get("relaxed_rmp_pricing_closed", False)
    ):
        failures.append("relaxed_rmp_certificate_without_closed_relaxed_pricing")

    if method == "interval-cutoff-oracle":
        basis = str(result.get("interval_exact_cutoff_certificate_basis", ""))
        solver_status = str(result.get("interval_exact_cutoff_solver_status", "")).lower()
        proven = as_bool(result.get("interval_exact_cutoff_proven_infeasible", False))
        if status == "interval_closed":
            if basis not in {
                "interval_exact_cutoff_mip_infeasible",
                "interval_exact_cutoff_mip_optimal_no_improver",
                "interval_exact_objective_bound_optimal_no_improver",
            }:
                failures.append("interval_oracle_closed_without_accepted_basis")
            if not proven:
                failures.append("interval_oracle_closed_without_proven_flag")
            if basis == "interval_exact_cutoff_mip_infeasible" and "infeasible" not in solver_status:
                failures.append("interval_oracle_infeasible_basis_without_solver_infeasible")
            if not result.get("interval_exact_cutoff_scope"):
                failures.append("interval_oracle_closed_without_scope")
        if as_bool(result.get("interval_oracle_can_merge_bound", False)):
            if not as_bool(result.get("interval_oracle_bound_valid", False)):
                failures.append("interval_oracle_mergeable_bound_marked_invalid")
            if result.get("interval_oracle_bound_scope") != "original_fixed_interval":
                failures.append("interval_oracle_mergeable_bound_wrong_scope")
            if result.get("interval_oracle_model_type") not in {
                "original_compact_objective_bound",
                "original_compact_cutoff_feasibility",
            }:
                failures.append("interval_oracle_mergeable_bound_wrong_model_type")
            if str(result.get("interval_oracle_objective_sense", "")) != "minimize":
                failures.append("interval_oracle_mergeable_bound_wrong_sense")
            if not as_bool(result.get("interval_oracle_has_gamma_interval_rows", False)):
                failures.append("interval_oracle_mergeable_bound_without_gamma_rows")
        if as_bool(result.get("certified_original_problem", False)):
            failures.append("interval_oracle_claimed_full_original_certificate")

    if method == "gcap-frontier" and as_int(result.get("oracle_bound_merged_leaves", 0)) > 0:
        if result.get("oracle_bound_merge_audit_csv_path", "") == "":
            failures.append("frontier_oracle_bound_merge_missing_audit_path")
        if result.get("full_ledger_merge_status", "") == "merged_all_unresolved_leaves_closed":
            if as_int(result.get("auto_interval_oracle_remaining_open_leaves", 0)) != 0:
                failures.append("frontier_oracle_bound_closed_status_with_open_leaves")

    preset = str(result.get("algorithm_preset", ""))
    if preset in {"paper-gf-bpc-core", "paper-bpc-core"}:
        if as_bool(result.get("route_mask_all_subset_enumeration_certifying", False)):
            failures.append("paper_gf_bpc_core_route_mask_enumeration_certifying")
        if as_bool(result.get("certificate_uses_interval_oracle", False)):
            failures.append("paper_gf_bpc_core_certificate_uses_interval_oracle")
        if as_int(result.get("intervals_closed_by_oracle_count", 0)) > 0 and certified:
            failures.append("paper_gf_bpc_core_closed_by_oracle")
        if certified and not as_bool(result.get("bpc_core_certificate_valid", False)):
            failures.append("paper_gf_bpc_core_certified_but_core_certificate_invalid")
        if certified and as_int(result.get("intervals_closed_by_bpc_count", 0)) > 0:
            if not as_bool(result.get("pricing_closure_certified_exact", False)):
                failures.append("paper_gf_bpc_core_bpc_without_exact_pricing")
    if preset in {"paper-gf-compact-bc", "paper-gf-tailored-bc"}:
        preset_tag = "paper_gf_tailored_bc" if preset == "paper-gf-tailored-bc" else "paper_gf_compact_bc"
        if as_bool(result.get("route_mask_all_subset_enumeration_certifying", False)):
            failures.append(f"{preset_tag}_route_mask_enumeration_certifying")
        if as_bool(result.get("certificate_uses_bpc_tree", False)):
            failures.append(f"{preset_tag}_certificate_uses_bpc_tree")
        if as_int(result.get("intervals_closed_by_bpc_count", 0)) > 0:
            failures.append(f"{preset_tag}_closed_by_bpc")
        if preset == "paper-gf-tailored-bc":
            callback_available = as_bool(result.get("tailored_bc_callback_available", False))
            callback_claim = (
                as_bool(result.get("tailored_bc_user_cut_callback_enabled", False)) or
                as_bool(result.get("tailored_bc_lazy_callback_enabled", False)) or
                as_bool(result.get("tailored_bc_incumbent_callback_enabled", False)) or
                as_bool(result.get("tailored_bc_branch_callback_enabled", False)) or
                str(result.get("tailored_bc_mode", "")) == "callback" or
                str(result.get("tailored_bc_source_class", "")) == "tailored_bc_certified"
            )
            if callback_claim and not callback_available:
                failures.append("paper_gf_tailored_bc_callback_claim_without_callback_api")
            if certified and str(result.get("tailored_bc_source_class", "")) == "static_fallback":
                warnings.append("paper_gf_tailored_bc_certified_without_true_callback_evidence")
        if certified:
            if method != "gcap-frontier":
                failures.append(f"{preset_tag}_certified_wrong_method")
            if not as_bool(result.get("frontier_covers_all_improving_gini_values", False)):
                failures.append(f"{preset_tag}_without_full_improving_gini_coverage")
            if result.get("frontier_range_certificate_scope") != "original_full_improving_range":
                failures.append(f"{preset_tag}_wrong_frontier_scope")
            if result.get("full_certificate_rejection_reason", "none") not in {"", "none", None}:
                failures.append(f"{preset_tag}_has_rejection_reason")
            if not as_bool(result.get("full_certificate_all_intervals_accounted", False)):
                failures.append(f"{preset_tag}_not_all_intervals_accounted")
            if not as_bool(result.get("compact_bc_certificate_valid", False)):
                failures.append(f"{preset_tag}_certificate_not_marked_valid")
            uses_compact = as_bool(result.get("certificate_uses_compact_interval_bc", False))
            if uses_compact:
                if not as_bool(result.get("compact_interval_bc_enabled", False)):
                    failures.append(f"{preset_tag}_used_but_not_enabled")
                if result.get("compact_interval_bc_bound_scope") != "original_fixed_interval":
                    failures.append(f"{preset_tag}_wrong_bound_scope")
                if not as_bool(result.get("compact_interval_bc_bound_valid", False)):
                    failures.append(f"{preset_tag}_invalid_compact_bound")
                if as_int(result.get("compact_bc_closed_leaf_count", 0)) <= 0 and as_int(
                    result.get("compact_interval_bc_closed_leaves", 0)
                ) <= 0:
                    failures.append(f"{preset_tag}_no_closed_compact_leaves")
    if preset in {"paper-exact-portfolio", "paper-exact-v20-certificate"}:
        if certified and as_bool(result.get("certificate_uses_interval_oracle", False)):
            if not as_bool(result.get("exact_portfolio_certificate_valid", False)):
                failures.append("exact_portfolio_oracle_certificate_not_marked_valid")

    return {
        "source": source,
        "instance_name": result.get("instance_name", ""),
        "method": method,
        "status": status,
        "method_scope": method_scope,
        "solves_original_objective": solves_original,
        "is_bpc": is_bpc,
        "certified_original_problem": certified,
        "verifier_passed": verifier,
        "gap": gap,
        "unresolved_intervals": unresolved,
        "invalid_bound_intervals": invalid,
        "open_nodes": open_nodes,
        "sealed_run": sealed_run,
        "no_archive_scanning": as_bool(result.get("no_archive_scanning", False)),
        "no_external_known_ub": as_bool(result.get("no_external_known_ub", False)),
        "no_focus_only_certificate": as_bool(result.get("no_focus_only_certificate", False)),
        "sealed_run_forbidden_source_used": as_bool(
            result.get("sealed_run_forbidden_source_used", False)
        ),
        "finalization_source": finalization_source,
        "audit_passed": not failures,
        "failure_count": len(failures),
        "failures": ";".join(failures),
        "warnings": ";".join(warnings),
    }


def write_csv(rows: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source",
        "instance_name",
        "method",
        "status",
        "method_scope",
        "solves_original_objective",
        "is_bpc",
        "certified_original_problem",
        "verifier_passed",
        "gap",
        "unresolved_intervals",
        "invalid_bound_intervals",
        "open_nodes",
        "sealed_run",
        "no_archive_scanning",
        "no_external_known_ub",
        "no_focus_only_certificate",
        "sealed_run_forbidden_source_used",
        "finalization_source",
        "audit_passed",
        "failure_count",
        "failures",
        "warnings",
    ]
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run_self_test() -> int:
    valid = {
        "instance_name": "smoke",
        "method": "gcap-frontier",
        "method_scope": "original_bpc",
        "solves_original_objective": True,
        "is_bpc": True,
        "status": "optimal",
        "certified_original_problem": True,
        "verifier_passed": True,
        "objective": 0.0,
        "lower_bound": 0.0,
        "upper_bound": 0.0,
        "gap": 0.0,
        "unresolved_intervals": 0,
        "invalid_bound_intervals": 0,
        "open_nodes": 0,
        "frontier_covers_all_improving_gini_values": True,
        "frontier_range_certificate_scope": "original_full_improving_range",
        "full_certificate_all_intervals_accounted": True,
        "full_certificate_rejection_reason": "none",
        "pricing_completed_exactly": True,
        "pricing_closure_certified_exact": True,
        "pricing_closure_status": "exact_no_negative",
        "pricing_best_reduced_cost_any": 0.0,
        "pricing_remaining_negative_rc": 0.0,
        "pricing_closed_nodes": 1,
        "frontier_tree_closed_interval_count": 1,
    }
    cases = {
        "valid.json": valid,
        "incomplete_pricing.json": {
            **valid,
            "pricing_completed_exactly": False,
        },
        "duplicate_negative.json": {
            **valid,
            "pricing_blocked_by_duplicate_projection": True,
        },
        "partial_frontier.json": {
            **valid,
            "frontier_covers_all_improving_gini_values": False,
        },
        "route_mask_disabled_certifying.json": {
            **valid,
            "route_mask_all_subset_enumeration_enabled": False,
            "route_mask_all_subset_enumeration_certifying": True,
        },
        "incumbent_as_lb.json": {
            **valid,
            "incumbent_source_contributes_lower_bound": True,
        },
        "archive_marked_reproducible.json": {
            **valid,
            "incumbent_source_category": "diagnostic_archive",
            "incumbent_source_is_paper_reproducible": True,
        },
        "optimal_without_cert.json": {
            **valid,
            "certified_original_problem": False,
        },
    }
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for name, payload in cases.items():
            (tmp_path / name).write_text(json.dumps(payload), encoding="utf-8")
        rows = []
        for path in sorted(tmp_path.glob("*.json")):
            for source, result in iter_result_objects(path):
                rows.append(audit_one(source, result))
        passed = {Path(row["source"].split("#")[0]).name: row["audit_passed"] for row in rows}
        expected = {
            "valid.json": True,
            "incomplete_pricing.json": False,
            "duplicate_negative.json": False,
            "partial_frontier.json": False,
            "route_mask_disabled_certifying.json": False,
            "incumbent_as_lb.json": False,
            "archive_marked_reproducible.json": False,
            "optimal_without_cert.json": False,
        }
        if passed != expected:
            print("self-test failed", file=sys.stderr)
            print("expected:", expected, file=sys.stderr)
            print("actual:", passed, file=sys.stderr)
            return 1
    print("audit_bpc_certificate self-test passed")
    return 0


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="*", help="JSON files or directories")
    parser.add_argument("--csv-out", default="", help="write audit CSV to this path")
    parser.add_argument("--fail-on-error", action="store_true", help="exit 1 when any row fails")
    parser.add_argument("--self-test", action="store_true", help="run built-in regression cases")
    parser.add_argument(
        "--require-progress-finals",
        action="append",
        default=[],
        help="directory whose *.progress.csv files must have matching final JSON",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()
    if not args.inputs:
        parser.error("provide at least one JSON file or directory, or use --self-test")

    rows: List[Dict[str, Any]] = []
    for path in collect_json_paths(args.inputs):
        if not path.exists():
            rows.append({
                "source": str(path),
                "instance_name": "",
                "method": "",
                "status": "",
                "method_scope": "",
                "solves_original_objective": False,
                "is_bpc": False,
                "certified_original_problem": False,
                "verifier_passed": False,
                "gap": "",
                "unresolved_intervals": "",
                "invalid_bound_intervals": "",
                "open_nodes": "",
                "audit_passed": False,
                "failure_count": 1,
                "failures": "missing_file",
                "warnings": "",
            })
            continue
        try:
            for source, result in iter_result_objects(path):
                rows.append(audit_one(source, result))
        except Exception as exc:  # keep audit evidence instead of crashing mid-directory
            rows.append({
                "source": str(path),
                "instance_name": "",
                "method": "",
                "status": "",
                "method_scope": "",
                "solves_original_objective": False,
                "is_bpc": False,
                "certified_original_problem": False,
                "verifier_passed": False,
                "gap": "",
                "unresolved_intervals": "",
                "invalid_bound_intervals": "",
                "open_nodes": "",
                "audit_passed": False,
                "failure_count": 1,
                "failures": f"json_parse_or_audit_error:{exc}",
                "warnings": "",
            })

    for raw_dir_text in args.require_progress_finals:
        raw_dir = Path(raw_dir_text)
        for progress_path in sorted(raw_dir.glob("*.progress.csv")):
            json_path = progress_path.with_name(
                progress_path.name.replace(".progress.csv", ".json")
            )
            if json_path.exists():
                continue
            rows.append({
                "source": str(progress_path),
                "instance_name": progress_path.name.replace(".progress.csv", ""),
                "method": "gcap-frontier",
                "status": "missing_final_json",
                "method_scope": "original_bpc",
                "solves_original_objective": True,
                "is_bpc": True,
                "certified_original_problem": False,
                "verifier_passed": False,
                "gap": "",
                "unresolved_intervals": "",
                "invalid_bound_intervals": "",
                "open_nodes": "",
                "sealed_run": True,
                "no_archive_scanning": True,
                "no_external_known_ub": True,
                "no_focus_only_certificate": True,
                "sealed_run_forbidden_source_used": False,
                "finalization_source": "",
                "audit_passed": False,
                "failure_count": 1,
                "failures": "progress_log_without_final_json",
                "warnings": "",
            })

    if args.csv_out:
        write_csv(rows, Path(args.csv_out))
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=list(rows[0].keys()) if rows else [])
        if rows:
            writer.writeheader()
            writer.writerows(rows)

    failures = sum(1 for row in rows if not row["audit_passed"])
    print(f"audited_rows={len(rows)} failures={failures}", file=sys.stderr)
    return 1 if args.fail_on_error and failures else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
