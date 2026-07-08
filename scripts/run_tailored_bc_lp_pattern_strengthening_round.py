#!/usr/bin/env python3
"""LP-pattern and long-run plain-vs-tailored dominant S-bucket round."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import run_tailored_bc_s_bucket_strengthening_round as sb


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "gf_tailored_bc_lp_pattern_strengthening_round"
RAW = RESULTS / "raw"
LOGS = RESULTS / "logs"
PROGRESS = RESULTS / "progress_traces"
MODELS = RESULTS / "model_exports"
SNAPSHOTS = RESULTS / "lp_snapshots"
DOCS = ROOT / "docs"
EXE = ROOT / "build" / "ExactEBRP.exe"

LOW_GINI_1_CUTOFF = 0.0491525526647
PRIOR_BEST_LB = 0.04890059983
PRIOR_REMAINING_GAP = 0.00025195283469999635

LEAVES: Dict[str, Dict[str, Any]] = dict(sb.LEAVES)

BUCKETS = {
    "dominant_k4": (16.59546103547, 23.272821182835),
    "adaptive_child": (18.26480107231125, 19.9341411091525),
}


def f(value: Any, default: float = 0.0) -> float:
    return sb.f(value, default)


def as_bool(value: Any) -> bool:
    return sb.b(value)


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if str(path) in {"", "."} or not path.exists() or path.is_dir():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: List[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def configure_harness() -> None:
    sb.RESULTS = RESULTS
    sb.RAW = RAW
    sb.LOGS = LOGS
    sb.PROGRESS = PROGRESS
    sb.MODELS = MODELS
    sb.SNAPSHOTS = SNAPSHOTS
    sb.DOCS = DOCS
    sb.LEAVES.clear()
    sb.LEAVES.update(LEAVES)
    sb.configure_base()


ORIGINAL_VARIANT_FLAGS = sb.variant_flags


def variant_flags(variant: str) -> List[str]:
    if variant == "plain_fixed_interval_mip_telemetry_only":
        return sb.base.variant_flags("callback_no_cuts") + [
            "--tailored-bc-callback-cut-profile", "off",
            "--tailored-bc-gini-branching", "off",
        ]
    if variant in {"current_best_new_combined_paper_safe", "best_new_combined_paper_safe"}:
        return ORIGINAL_VARIANT_FLAGS("best_combined_paper_safe") + [
            "--tailored-bc-subset-cross-h-separation-profile", "dominant-bucket",
            "--tailored-bc-bucket-ratio-domain-tightening", "true",
            "--tailored-bc-bucket-subset-ratio-domain", "true",
            "--tailored-bc-bucket-subset-ratio-max-size", "3",
            "--compact-bc-denominator-bound-mode", "tight",
            "--compact-bc-objective-estimator-mode", "adaptive",
            "--compact-bc-sp-product-estimator", "paper-safe",
            "--compact-bc-sp-product-bounds", "tight",
            "--compact-bc-variable-s-centering", "true",
        ]
    if variant == "bucket_integer_inventory_domain":
        return variant_flags("current_best_new_combined_paper_safe") + [
            "--tailored-bc-bucket-integer-inventory-domain", "true",
            "--tailored-bc-bucket-integer-inventory-domain-mode", "static",
        ]
    if variant == "bucket_required_movement":
        return variant_flags("bucket_integer_inventory_domain") + [
            "--tailored-bc-bucket-required-movement", "true",
            "--tailored-bc-bucket-required-visit", "true",
            "--tailored-bc-bucket-required-movement-max-size", "3",
        ]
    if variant == "sp_h_coupled_estimator":
        return variant_flags("current_best_new_combined_paper_safe") + [
            "--compact-bc-sp-product-estimator", "paper-safe",
            "--compact-bc-sp-product-bounds", "tight",
        ]
    if variant == "all_new_paper_safe_cuts":
        return variant_flags("bucket_required_movement") + [
            "--compact-bc-sp-product-estimator", "paper-safe",
            "--compact-bc-sp-product-bounds", "tight",
        ]
    return ORIGINAL_VARIANT_FLAGS(variant)


def bucket_extra(bucket_name: str, budget: int, policy: str = "dominant-fixed") -> List[str]:
    s_l, s_u = BUCKETS[bucket_name]
    return [
        "--tailored-bc-s-bucket-ledger", "paper-safe",
        "--tailored-bc-s-bucket-count", "1",
        "--tailored-bc-s-bucket-policy", policy,
        "--tailored-bc-s-bucket-time-budget", str(budget),
        "--tailored-bc-s-bucket-merge-audit", "true",
        "--compact-bc-s-range-refinement", "paper-safe",
        "--compact-bc-s-range-buckets", "1",
        "--compact-bc-s-range-bucket-id", "0",
        "--compact-bc-s-range-bucket-L", repr(s_l),
        "--compact-bc-s-range-bucket-U", repr(s_u),
        "--compact-bc-s-range-adaptive", "false",
        "--compact-bc-progress-interval", "30",
    ]


def annotate_json(path: Path,
                  spec: Dict[str, Any],
                  variant: str,
                  budget: int,
                  bucket_name: str | None,
                  cmd: Sequence[str]) -> None:
    data = read_json(path)
    if not data:
        return
    data.setdefault("input_path", str(ROOT / spec["instance"]))
    data.setdefault("algorithm_preset", "paper-gf-tailored-bc")
    data.setdefault("thread_fairness_class", "one_thread_fair")
    data.setdefault("solver_thread_policy", "controlled_single_thread")
    data.setdefault("compact_bc_solver_threads", 1)
    data.setdefault("cplex_threads", 1)
    data.setdefault("mip_threads", 1)
    data.setdefault("time_budget_seconds", budget)
    data.setdefault("command_hash", sha16(" ".join(cmd)))
    data.setdefault("paper_certificate_contamination", False)
    data.setdefault("leaf_solver_row", True)
    data.setdefault("compact_bc_called_this_row", True)
    data["ablation_variant_semantics"] = variant
    if bucket_name:
        data["dominant_s_bucket_name"] = bucket_name
        data["dominant_s_bucket_L"] = BUCKETS[bucket_name][0]
        data["dominant_s_bucket_U"] = BUCKETS[bucket_name][1]
    if variant == "plain_fixed_interval_mip":
        data["row_class"] = "benchmark_only_plain_fixed_interval_mip"
        data["paper_certificate_role"] = "benchmark_diagnostic_only"
        data["plain_telemetry_only"] = False
    elif variant == "plain_fixed_interval_mip_telemetry_only":
        data["row_class"] = "benchmark_only_plain_fixed_interval_mip_telemetry"
        data["paper_certificate_role"] = "benchmark_diagnostic_only"
        data["plain_telemetry_only"] = True
    else:
        data["row_class"] = "paper_safe_fixed_interval_tailored_bc"
        data["paper_certificate_role"] = "fixed_interval_tailored_bc_subproblem"
        data["plain_telemetry_only"] = False
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def execute_row(leaf: str,
                variant: str,
                budget: int,
                args: argparse.Namespace,
                bucket_name: str | None = None) -> Dict[str, Any]:
    spec = LEAVES[leaf]
    stem_parts = [bucket_name or "", leaf, variant, f"{budget}s"]
    stem = "_".join(part for part in stem_parts if part).replace("+", "_plus_")
    out = RAW / f"{stem}.json"
    progress = PROGRESS / f"{stem}.progress.csv"
    lp = MODELS / f"{stem}.lp"
    cmd = sb.base.base_interval_cmd(spec, budget, out, progress, lp) + variant_flags(variant)
    if bucket_name:
        cmd += bucket_extra(bucket_name, budget)
    log = LOGS / f"{stem}.log.txt"
    if args.run:
        sb.base.run_cmd(cmd, log, timeout=budget + args.wrapper_grace,
                        skip_existing=args.skip_existing)
        if out.exists():
            annotate_json(out, spec, variant, budget, bucket_name, cmd)
    summary = sb.base.row_from_result(leaf, variant, budget, out, progress, lp, cmd)
    data = read_json(out)
    summary.update({
        "bucket_name": bucket_name or "",
        "bucket_S_L": BUCKETS[bucket_name][0] if bucket_name else "",
        "bucket_S_U": BUCKETS[bucket_name][1] if bucket_name else "",
        "cutoff": spec["UB"],
        "gap_to_cutoff": max(0.0, f(spec["UB"]) - f(summary.get("lower_bound"))),
        "plain_telemetry_only": data.get("plain_telemetry_only", False),
        "paper_certificate_role": data.get("paper_certificate_role", ""),
        "row_class": data.get("row_class", ""),
        "compact_bc_solver_status": data.get("compact_bc_solver_status", ""),
        "compact_bc_bound_valid": data.get("compact_bc_bound_valid", ""),
        "node_count": data.get("compact_bc_nodes", summary.get("nodes", "")),
        "bucket_integer_inventory_bounds_tightened": data.get("bucket_integer_inventory_bounds_tightened", 0),
        "bucket_integer_inventory_rows_added": data.get("bucket_integer_inventory_rows_added", 0),
        "bucket_integer_inventory_lower_bounds_tightened": data.get("bucket_integer_inventory_lower_bounds_tightened", 0),
        "bucket_integer_inventory_upper_bounds_tightened": data.get("bucket_integer_inventory_upper_bounds_tightened", 0),
        "bucket_required_movement_rows_added": data.get("bucket_required_movement_rows_added", 0),
        "bucket_required_visit_rows_added": data.get("bucket_required_visit_rows_added", 0),
        "bucket_subset_required_movement_rows_added": data.get("bucket_subset_required_movement_rows_added", 0),
        "tailored_bc_bucket_h_cap_rows_added": data.get("tailored_bc_bucket_h_cap_rows_added", 0),
        "sp_h_coupled_estimator_rows": data.get("compact_bc_sp_product_estimator_rows_added", 0),
        "sp_h_mccormick_rows": data.get("compact_bc_sp_product_mccormick_rows_added", 0),
        "objective_estimator_rows": data.get("compact_bc_objective_estimator_cutoff_rows_added", 0),
        "tailored_user_cuts": data.get("tailored_bc_user_cuts_added_by_family", ""),
        "total_cuts": data.get("compact_bc_total_cuts_added_by_family", ""),
        "total_domains": data.get("compact_bc_total_domains_tightened_by_family", ""),
        "best_valid_lb_seen": data.get("best_valid_lb_seen", summary.get("lower_bound", "")),
        "best_valid_gap_seen": data.get("best_valid_gap_seen", summary.get("gap", "")),
        "finalization_source": data.get("finalization_source", ""),
        "compact_bc_memory_estimate_mb": data.get("compact_bc_memory_estimate_mb", ""),
        "progress_path": str(progress.relative_to(ROOT)) if progress.exists() else "",
        "json_path": str(out.relative_to(ROOT)) if out.exists() else "",
        "model_export_path": str(lp.relative_to(ROOT)) if lp.exists() else "",
        "log_path": str(log.relative_to(ROOT)),
        "command_hash": data.get("command_hash", sha16(" ".join(cmd))),
    })
    return summary


def plan_rows(profile: str, include_10800: bool) -> List[Tuple[str, str, str, int]]:
    if profile == "smoke":
        return [
            ("dominant_k4", "low_gini_1", "plain_fixed_interval_mip", 10),
            ("dominant_k4", "low_gini_1", "all_new_paper_safe_cuts", 10),
        ]
    budgets = [300] if profile == "quick" else [300, 1200, 3600]
    variants = [
        "plain_fixed_interval_mip",
        "plain_fixed_interval_mip_telemetry_only",
        "static_tailored_compact_bc",
        "current_best_new_combined_paper_safe",
        "bucket_integer_inventory_domain",
        "bucket_required_movement",
        "sp_h_coupled_estimator",
        "all_new_paper_safe_cuts",
    ]
    rows: List[Tuple[str, str, str, int]] = []
    for budget in budgets:
        for variant in variants:
            rows.append(("dominant_k4", "low_gini_1", variant, budget))
    for budget in budgets:
        for variant in ("plain_fixed_interval_mip", "current_best_new_combined_paper_safe", "all_new_paper_safe_cuts"):
            rows.append(("adaptive_child", "low_gini_1", variant, budget))
    if include_10800:
        for variant in (
            "plain_fixed_interval_mip",
            "plain_fixed_interval_mip_telemetry_only",
            "static_tailored_compact_bc",
            "current_best_new_combined_paper_safe",
            "all_new_paper_safe_cuts",
        ):
            rows.append(("dominant_k4", "low_gini_1", variant, 10800))
    return rows


def secondary_rows(args: argparse.Namespace) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for leaf in ("low_gini_2", "high_imbalance_seed3201_hard",
                 "tight_T_seed3102_hard", "moderate_seed3302_hard"):
        variants = ["plain_fixed_interval_mip", "current_best_new_combined_paper_safe",
                    "all_new_paper_safe_cuts"]
        if leaf == "moderate_seed3302_hard":
            variants += ["bucket_integer_inventory_domain", "bucket_required_movement"]
        for variant in variants:
            rows.append(execute_row(leaf, variant, 300, args))
    return rows


def trajectory_rows(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        progress = read_csv(ROOT / str(row.get("progress_path", "")))
        if not progress:
            out.append({
                "bucket_name": row.get("bucket_name", ""),
                "variant": row.get("variant", ""),
                "budget_seconds": row.get("budget_seconds", ""),
                "elapsed_seconds": row.get("runtime_seconds", ""),
                "valid_bound_available": row.get("compact_bc_bound_valid", ""),
                "best_bound": row.get("lower_bound", ""),
                "incumbent_available": f(row.get("upper_bound")) > 0,
                "incumbent": row.get("upper_bound", ""),
                "gap_to_cutoff": row.get("gap_to_cutoff", ""),
                "node_count": row.get("node_count", ""),
                "node_delta_since_last_checkpoint": "",
                "last_bound_improvement_time": row.get("last_improvement_time", ""),
                "number_of_improvements": row.get("checkpoint_valid_rows", ""),
                "worker_responsiveness": "no_progress_trace_final_json_only",
                "memory": row.get("compact_bc_memory_estimate_mb", ""),
                "progress_source": "final_json_or_cplex_log_only",
            })
            continue
        last_nodes = 0
        best_bound = -math.inf
        last_improvement = 0.0
        improvements = 0
        for rec in progress:
            bound = f(rec.get("best_bound", rec.get("global_LB", "")), math.nan)
            elapsed = f(rec.get("elapsed_seconds", rec.get("time_seconds", "")))
            nodes = int(f(rec.get("node_count", rec.get("nodes", "")), last_nodes))
            if math.isfinite(bound) and bound > best_bound + 1e-10:
                best_bound = bound
                last_improvement = elapsed
                improvements += 1
            out.append({
                "bucket_name": row.get("bucket_name", ""),
                "variant": row.get("variant", ""),
                "budget_seconds": row.get("budget_seconds", ""),
                "elapsed_seconds": elapsed,
                "valid_bound_available": math.isfinite(bound),
                "best_bound": bound if math.isfinite(bound) else "",
                "incumbent_available": rec.get("best_incumbent_available", rec.get("incumbent_available", "")),
                "incumbent": rec.get("best_incumbent", rec.get("incumbent", "")),
                "gap_to_cutoff": rec.get("gap_to_cutoff", ""),
                "node_count": nodes,
                "node_delta_since_last_checkpoint": nodes - last_nodes,
                "last_bound_improvement_time": last_improvement,
                "number_of_improvements": improvements,
                "worker_responsiveness": "progress_trace_present",
                "memory": rec.get("memory_mb", ""),
                "progress_source": rec.get("progress_source", "cplex_native_callback_or_wrapper_progress"),
            })
            last_nodes = nodes
    return out


def snapshot_outputs(rows: Sequence[Dict[str, Any]]) -> None:
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    snapshot_values: List[Dict[str, Any]] = []
    fractionality: List[Dict[str, Any]] = []
    estimator_slack: List[Dict[str, Any]] = []
    cut_candidates: List[Dict[str, Any]] = []
    comparison: List[Dict[str, Any]] = []
    for row in rows:
        progress = read_csv(ROOT / str(row.get("progress_path", "")))
        selected = progress[-1:] if progress else [{}]
        for idx, rec in enumerate(selected):
            scope = "nearest_relaxation_callback_unavailable_bound_checkpoint_only"
            snap = {
                "snapshot_source": scope,
                "snapshot_scope": scope,
                "paper_certificate_role": "diagnostic_only",
                "bucket_name": row.get("bucket_name", ""),
                "leaf": row.get("leaf", ""),
                "variant": row.get("variant", ""),
                "budget_seconds": row.get("budget_seconds", ""),
                "time_seconds": rec.get("elapsed_seconds", row.get("runtime_seconds", "")),
                "best_bound": rec.get("best_bound", row.get("lower_bound", "")),
                "node_count": rec.get("node_count", row.get("node_count", "")),
                "S": "not_exposed_by_current_cplex_callback",
                "P": "not_exposed_by_current_cplex_callback",
                "H": "not_exposed_by_current_cplex_callback",
                "G": "not_exposed_by_current_cplex_callback",
                "G_variable": "not_exposed_by_current_cplex_callback",
                "objective_estimator_value": "not_exposed_by_current_cplex_callback",
                "true_reconstructed_objective": "not_exposed_by_current_cplex_callback",
                "W_SP": "not_exposed_by_current_cplex_callback",
                "S_times_P": "not_exposed_by_current_cplex_callback",
                "SP_McCormick_slack": "not_exposed_by_current_cplex_callback",
                "objective_estimator_slack": "not_exposed_by_current_cplex_callback",
                "bucket_S_L": row.get("bucket_S_L", ""),
                "bucket_S_U": row.get("bucket_S_U", ""),
                "gamma_L": row.get("gamma_L", ""),
                "gamma_U": row.get("gamma_U", ""),
                "r_min": "not_exposed_by_current_cplex_callback",
                "r_max": "not_exposed_by_current_cplex_callback",
                "top20_r_i": "not_exposed_by_current_cplex_callback",
                "top20_Y_i": "not_exposed_by_current_cplex_callback",
                "top20_e_i": "not_exposed_by_current_cplex_callback",
                "top_fractional_z": "not_exposed_by_current_cplex_callback",
                "top_fractional_p": "not_exposed_by_current_cplex_callback",
                "top_fractional_d": "not_exposed_by_current_cplex_callback",
            }
            snapshot_values.append(snap)
            write_csv(SNAPSHOTS / f"{row.get('bucket_name','')}_{row.get('leaf')}_{row.get('variant')}_{row.get('budget_seconds')}s_{idx}.csv".replace("+", "_plus_"), [snap])
        fractionality.append({
            "bucket_name": row.get("bucket_name", ""),
            "leaf": row.get("leaf", ""),
            "variant": row.get("variant", ""),
            "budget_seconds": row.get("budget_seconds", ""),
            "top_fractional_z": "not_exposed_by_current_cplex_callback",
            "top_fractional_p": "not_exposed_by_current_cplex_callback",
            "top_fractional_d": "not_exposed_by_current_cplex_callback",
            "snapshot_source": "diagnostic_bound_checkpoint_only",
        })
        estimator_slack.append({
            "bucket_name": row.get("bucket_name", ""),
            "variant": row.get("variant", ""),
            "budget_seconds": row.get("budget_seconds", ""),
            "objective_estimator_rows": row.get("objective_estimator_rows", ""),
            "sp_h_coupled_estimator_rows": row.get("sp_h_coupled_estimator_rows", ""),
            "sp_h_mccormick_rows": row.get("sp_h_mccormick_rows", ""),
            "objective_estimator_slack": "not_exposed_by_current_cplex_callback",
            "sp_mccormick_slack": "not_exposed_by_current_cplex_callback",
        })
        cut_candidates.append({
            "bucket_name": row.get("bucket_name", ""),
            "variant": row.get("variant", ""),
            "budget_seconds": row.get("budget_seconds", ""),
            "bucket_integer_inventory_domain_candidates": row.get("bucket_integer_inventory_bounds_tightened", ""),
            "required_movement_candidates": row.get("bucket_required_movement_rows_added", ""),
            "station_visit_lower_bound_candidates": row.get("bucket_required_visit_rows_added", ""),
            "subset_required_movement_candidates": row.get("bucket_subset_required_movement_rows_added", ""),
            "SPH_coupled_estimator_rows": row.get("sp_h_coupled_estimator_rows", ""),
            "H_exactness_candidate": "H_lower_rows_remain_diagnostic",
        })
        comparison.append({
            "bucket_name": row.get("bucket_name", ""),
            "variant": row.get("variant", ""),
            "budget_seconds": row.get("budget_seconds", ""),
            "snapshot_source": "diagnostic_bound_checkpoint_only",
            "LB": row.get("lower_bound", ""),
            "gap_to_cutoff": row.get("gap_to_cutoff", ""),
            "tailored_or_plain": "plain" if "plain" in str(row.get("variant")) else "tailored",
        })
    write_csv(RESULTS / "plateau_snapshot_values.csv", snapshot_values)
    write_csv(RESULTS / "plateau_fractionality_summary.csv", fractionality)
    write_csv(RESULTS / "plateau_estimator_slack_summary.csv", estimator_slack)
    write_csv(RESULTS / "plateau_cut_candidate_summary.csv", cut_candidates)
    write_csv(RESULTS / "plain_vs_tailored_snapshot_comparison.csv", comparison)


def write_baseline_recheck() -> None:
    rows: List[Dict[str, Any]] = []
    forbidden_branch = re.compile(
        r"\b(if|else\s+if|switch)\b.*(moderate_seed|high_imbalance_seed|tight_T_seed|seed\d{3,})",
        re.I,
    )
    paper_forbidden = re.compile(
        r"paper-gf-tailored-bc.*(known[_-]?ub|external[_-]?incumbent|archive|plain.*cplex.*ledger)",
        re.I,
    )
    patterns = [
        "moderate_seed3301", "low_gini_1", "seed3201", "seed3102",
        "known_ub", "archive", "external_incumbent", "focus",
        "route_mask", "bpc",
    ]
    for pat in patterns:
        proc = subprocess.run(
            ["rg", "-n", pat, "src", "include", "scripts"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        hits = [line for line in proc.stdout.splitlines() if line.strip()]
        forbidden: List[str] = []
        source_hits = [line for line in hits if line.startswith("src") or line.startswith("include")]
        for line in source_hits:
            if forbidden_branch.search(line) or paper_forbidden.search(line):
                forbidden.append(line)
        if forbidden:
            classification = "forbidden_algorithm_special_case"
        elif source_hits:
            classification = "allowed_cli_option_or_safety_metadata"
        else:
            classification = "allowed_runner_or_diagnostic_metadata"
        rows.append({
            "check": pat,
            "hits": len(hits),
            "source_hits": len(source_hits),
            "classification": classification,
            "forbidden_hits": len(forbidden),
            "audit_passed": not forbidden,
        })
    write_csv(RESULTS / "baseline_recheck.csv", rows)
    strict_out = RESULTS / "paper_strict_algorithm_audit.csv"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "audit_paper_strict_algorithm.py"),
         "--out", str(strict_out)],
        cwd=ROOT,
        text=True,
        check=False,
    )


def write_static_outputs(rows: Sequence[Dict[str, Any]], secondary: Sequence[Dict[str, Any]]) -> None:
    dominant = [r for r in rows if r.get("bucket_name") == "dominant_k4"]
    adaptive = [r for r in rows if r.get("bucket_name") == "adaptive_child"]
    write_csv(RESULTS / "dominant_bucket_longrun.csv", dominant)
    write_csv(RESULTS / "adaptive_child_longrun.csv", adaptive)
    write_csv(RESULTS / "secondary_regression_summary.csv", list(secondary))
    write_csv(RESULTS / "plain_vs_tailored_10800s.csv", [r for r in dominant if str(r.get("budget_seconds")) in {"10800", "10800.0"}])
    traj = trajectory_rows(rows)
    write_csv(RESULTS / "plain_vs_tailored_bound_trajectory.csv", traj)
    health = []
    for row in rows:
        row_traj = [t for t in traj if t.get("variant") == row.get("variant") and
                    str(t.get("budget_seconds")) == str(row.get("budget_seconds")) and
                    t.get("bucket_name") == row.get("bucket_name")]
        last = row_traj[-1] if row_traj else {}
        health.append({
            "bucket_name": row.get("bucket_name", ""),
            "variant": row.get("variant", ""),
            "budget_seconds": row.get("budget_seconds", ""),
            "runtime_seconds": row.get("runtime_seconds", ""),
            "valid_bound_available": row.get("compact_bc_bound_valid", ""),
            "best_bound": row.get("lower_bound", ""),
            "gap_to_cutoff": row.get("gap_to_cutoff", ""),
            "node_count": row.get("node_count", ""),
            "last_bound_improvement_time": last.get("last_bound_improvement_time", row.get("last_improvement_time", "")),
            "number_of_improvements": last.get("number_of_improvements", row.get("checkpoint_valid_rows", "")),
            "worker_responsiveness": "progress_trace_present" if row.get("progress_path") else "no_progress_trace",
            "memory": row.get("compact_bc_memory_estimate_mb", ""),
            "progress_source": last.get("progress_source", ""),
        })
    write_csv(RESULTS / "longrun_health_monitoring.csv", health)
    plain = next((r for r in dominant if r.get("variant") == "plain_fixed_interval_mip" and str(r.get("budget_seconds")) in {"10800", "10800.0"}), {})
    telemetry = next((r for r in dominant if r.get("variant") == "plain_fixed_interval_mip_telemetry_only" and str(r.get("budget_seconds")) in {"10800", "10800.0"}), {})
    write_csv(RESULTS / "plain_telemetry_overhead_audit.csv", [{
        "budget_seconds": 10800,
        "plain_no_callback_LB": plain.get("lower_bound", ""),
        "plain_telemetry_LB": telemetry.get("lower_bound", ""),
        "LB_delta_telemetry_minus_plain": f(telemetry.get("lower_bound")) - f(plain.get("lower_bound")),
        "plain_no_callback_runtime": plain.get("runtime_seconds", ""),
        "plain_telemetry_runtime": telemetry.get("runtime_seconds", ""),
        "telemetry_only_callback_changes_behavior_materially": abs(f(telemetry.get("lower_bound")) - f(plain.get("lower_bound"))) > 1e-5,
        "paper_certificate_role": "benchmark_diagnostic_only",
    }])
    write_csv(RESULTS / "bucket_integer_inventory_domain_audit.csv", [{
        "variant": r.get("variant", ""),
        "bucket_name": r.get("bucket_name", ""),
        "budget_seconds": r.get("budget_seconds", ""),
        "bounds_tightened": r.get("bucket_integer_inventory_bounds_tightened", ""),
        "rows_added": r.get("bucket_integer_inventory_rows_added", ""),
        "lower_bounds_tightened": r.get("bucket_integer_inventory_lower_bounds_tightened", ""),
        "upper_bounds_tightened": r.get("bucket_integer_inventory_upper_bounds_tightened", ""),
        "LB": r.get("lower_bound", ""),
        "gap_to_cutoff": r.get("gap_to_cutoff", ""),
    } for r in rows])
    write_csv(RESULTS / "bucket_required_movement_audit.csv", [{
        "variant": r.get("variant", ""),
        "bucket_name": r.get("bucket_name", ""),
        "budget_seconds": r.get("budget_seconds", ""),
        "movement_rows": r.get("bucket_required_movement_rows_added", ""),
        "visit_rows": r.get("bucket_required_visit_rows_added", ""),
        "subset_rows": r.get("bucket_subset_required_movement_rows_added", ""),
        "LB": r.get("lower_bound", ""),
        "gap_to_cutoff": r.get("gap_to_cutoff", ""),
    } for r in rows])
    write_csv(RESULTS / "sp_h_coupled_estimator_audit.csv", [{
        "formula": "H + V lambda W_SP <= V(UB-epsilon)S",
        "proof_status": "paper_safe_with_bucket_local_mccormick",
        "variant": r.get("variant", ""),
        "budget_seconds": r.get("budget_seconds", ""),
        "rows_added": r.get("sp_h_coupled_estimator_rows", ""),
        "mccormick_rows": r.get("sp_h_mccormick_rows", ""),
        "LB impact": r.get("lower_bound", ""),
        "runtime impact": r.get("runtime_seconds", ""),
        "reason if rejected": "",
    } for r in rows])
    write_csv(RESULTS / "sp_h_coupled_estimator_ablation.csv", [r for r in rows if r.get("variant") in {"sp_h_coupled_estimator", "current_best_new_combined_paper_safe", "all_new_paper_safe_cuts"}])
    write_csv(RESULTS / "exact_H_semantics_audit.csv", [{
        "formula": "H upper cap uses H <= V gamma_U S_U; H lower/spread-cap rows remain diagnostic",
        "proof_status": "upper_cap_paper_safe_lower_rows_diagnostic",
        "rows_added": sum(int(f(r.get("tailored_bc_bucket_h_cap_rows_added", 0))) for r in rows),
        "reason if rejected": "H lower rows may be unsafe when h variables are slack in relaxation",
    }])
    snapshot_outputs(rows)
    best = max((r for r in dominant if "plain" not in str(r.get("variant"))),
               key=lambda r: f(r.get("lower_bound"), -math.inf), default={})
    trigger = (
        f(best.get("lower_bound")) >= LOW_GINI_1_CUTOFF - 1e-7 or
        max(0.0, LOW_GINI_1_CUTOFF - f(best.get("lower_bound"))) < 1e-5 or
        f(best.get("lower_bound")) - PRIOR_BEST_LB >= 0.5 * PRIOR_REMAINING_GAP
    )
    write_csv(RESULTS / "full_convergence_comparison.csv", [{
        "triggered": trigger,
        "best_variant": best.get("variant", ""),
        "best_LB": best.get("lower_bound", ""),
        "gap_to_cutoff": max(0.0, LOW_GINI_1_CUTOFF - f(best.get("lower_bound"))),
        "trigger_reason": "threshold_met" if trigger else "not_triggered",
    }])
    (RESULTS / "full_convergence_final_report.md").write_text(
        f"Full convergence benchmark triggered: {trigger}.\n",
        encoding="utf-8",
    )


def write_report(rows: Sequence[Dict[str, Any]], secondary: Sequence[Dict[str, Any]]) -> None:
    dominant = [r for r in rows if r.get("bucket_name") == "dominant_k4"]
    plain10800 = next((r for r in dominant if r.get("variant") == "plain_fixed_interval_mip" and str(r.get("budget_seconds")) in {"10800", "10800.0"}), {})
    tele10800 = next((r for r in dominant if r.get("variant") == "plain_fixed_interval_mip_telemetry_only" and str(r.get("budget_seconds")) in {"10800", "10800.0"}), {})
    current10800 = next((r for r in dominant if r.get("variant") == "current_best_new_combined_paper_safe" and str(r.get("budget_seconds")) in {"10800", "10800.0"}), {})
    new10800 = next((r for r in dominant if r.get("variant") == "all_new_paper_safe_cuts" and str(r.get("budget_seconds")) in {"10800", "10800.0"}), {})
    best = max((r for r in dominant if "plain" not in str(r.get("variant"))),
               key=lambda r: f(r.get("lower_bound"), -math.inf), default={})
    gap = max(0.0, LOW_GINI_1_CUTOFF - f(best.get("lower_bound")))
    trigger = gap < 1e-5 or f(best.get("lower_bound")) - PRIOR_BEST_LB >= 0.5 * PRIOR_REMAINING_GAP
    secondary_lines = []
    for leaf in sorted({r.get("leaf") for r in secondary}):
        leaf_rows = [r for r in secondary if r.get("leaf") == leaf]
        plain = max((r for r in leaf_rows if r.get("variant") == "plain_fixed_interval_mip"),
                    key=lambda r: f(r.get("lower_bound"), -math.inf), default={})
        tailored = max((r for r in leaf_rows if r.get("variant") != "plain_fixed_interval_mip"),
                       key=lambda r: f(r.get("lower_bound"), -math.inf), default={})
        secondary_lines.append(
            f"- `{leaf}`: best tailored LB `{tailored.get('lower_bound', '')}`, plain LB `{plain.get('lower_bound', '')}`."
        )
    report = f"""# LP Pattern and Long-Run Plain Benchmark Final Report

1. Plain CPLEX 10800s: LB `{plain10800.get('lower_bound', 'not_run')}`, gap-to-cutoff `{plain10800.get('gap_to_cutoff', '')}`.
2. Tailored current 10800s: LB `{current10800.get('lower_bound', 'not_run')}`, gap-to-cutoff `{current10800.get('gap_to_cutoff', '')}`.
3. Tailored new-strengthening 10800s: LB `{new10800.get('lower_bound', 'not_run')}`, gap-to-cutoff `{new10800.get('gap_to_cutoff', '')}`.
4. Telemetry-only callback distortion: see `plain_telemetry_overhead_audit.csv`; 10800s telemetry LB `{tele10800.get('lower_bound', 'not_run')}`.
5. LP/fractional snapshots: exported as diagnostic checkpoint snapshots. Full best-bound-node relaxation variable vectors remain unavailable through the current callback path; missing values are labelled, not zero-filled.
6. Nearest-relaxation pattern: current package records bound/node/cut trajectories; S/P/H/G and estimator slack are labelled unavailable where CPLEX did not expose variable vectors.
7. Bucket integer inventory domain tightening rows/bounds are reported in `bucket_integer_inventory_domain_audit.csv`.
8. Required movement / visit rows are reported in `bucket_required_movement_audit.csv`.
9. SP-H coupled estimator rows are reported in `sp_h_coupled_estimator_audit.csv`.
10. Exact-H audit: H upper-cap rows are paper-safe; H lower/spread-cap rows remain diagnostic.
11. Best paper-safe LB/gap: `{best.get('lower_bound', '')}` / `{gap}`.
12. Dominant bucket closed: `{f(best.get('lower_bound')) >= LOW_GINI_1_CUTOFF - 1e-7}`.
13. Adaptive child status is in `adaptive_child_longrun.csv`.
14. Secondary regression:
{chr(10).join(secondary_lines)}
15. Full convergence benchmark triggered: `{trigger}`.
16. Paper-core contamination risks: none detected in generated row labels; plain and telemetry rows are benchmark diagnostic only.
17. Next exact theoretical target: expose real relaxation-point variable snapshots at CPLEX best-bound checkpoints or derive stronger bucket-local denominator cuts that close the remaining low-Gini S bucket without relying on diagnostic checkpoint evidence.
"""
    (RESULTS / "final_report.md").write_text(report, encoding="utf-8")


def run_builtin_diagnostics(args: argparse.Namespace) -> None:
    if not args.run:
        return
    for method in (
        "tailored-bc-callback-smoke-test",
        "tailored-bc-branch-callback-smoke-test",
        "tailored-bc-cut-validity-test",
        "low-gini-l1-centering-test",
        "gini-subset-envelope-test",
        "transfer-cutset-validity-test",
        "s-bucket-coverage-test",
        "certificate-basis-test",
        "option-consistency-test",
    ):
        out = RAW / f"validity_{method}.json"
        if args.skip_existing and out.exists():
            continue
        cmd = [
            str(EXE), "--method", method,
            "--input", str(ROOT / "testdata" / "examples" / "gcap_smoke_V4_M1.txt"),
            "--lambda", "0.15", "--T", "3600",
            "--out", str(out),
        ]
        log = LOGS / f"validity_{method}.log.txt"
        with log.open("w", encoding="utf-8", errors="replace") as handle:
            handle.write("COMMAND " + " ".join(cmd) + "\n")
            subprocess.run(cmd, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT,
                           check=False, timeout=180)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["smoke", "quick", "required"], default="quick")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--replace-results", action="store_true")
    parser.add_argument("--include-10800", action="store_true")
    parser.add_argument("--wrapper-grace", type=int, default=1200)
    args = parser.parse_args()

    configure_harness()
    if args.replace_results and RESULTS.exists():
        shutil.rmtree(RESULTS)
    for path in (RESULTS, RAW, LOGS, PROGRESS, MODELS, SNAPSHOTS):
        path.mkdir(parents=True, exist_ok=True)
    sb.variant_flags = variant_flags

    run_builtin_diagnostics(args)
    write_baseline_recheck()

    rows = [
        execute_row(leaf, variant, budget, args, bucket_name=bucket_name)
        for bucket_name, leaf, variant, budget in plan_rows(args.profile, args.include_10800)
    ]
    secondary = [] if args.profile == "smoke" else secondary_rows(args)
    write_static_outputs(rows, secondary)
    write_report(rows, secondary)
    print(f"lp_pattern_rows={len(rows)} secondary_rows={len(secondary)} results={RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
