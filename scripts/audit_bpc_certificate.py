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

    original_scope = solves_original or method_scope in {
        "original_bpc",
        "original_compact",
        "plain_cplex",
    }

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

    if certified:
        if status != "optimal":
            failures.append("certified_but_status_not_optimal")
        if not original_scope:
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
            }:
                failures.append("interval_oracle_closed_without_accepted_basis")
            if not proven:
                failures.append("interval_oracle_closed_without_proven_flag")
            if basis == "interval_exact_cutoff_mip_infeasible" and "infeasible" not in solver_status:
                failures.append("interval_oracle_infeasible_basis_without_solver_infeasible")
            if not result.get("interval_exact_cutoff_scope"):
                failures.append("interval_oracle_closed_without_scope")
        if as_bool(result.get("certified_original_problem", False)):
            failures.append("interval_oracle_claimed_full_original_certificate")

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
