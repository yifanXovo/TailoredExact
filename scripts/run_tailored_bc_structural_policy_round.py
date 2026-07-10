#!/usr/bin/env python3
"""Fresh structural-cut activation policy experiments for the dominant S bucket."""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import run_tailored_bc_structural_cut_round as structural


ROOT = Path(__file__).resolve().parents[1]
ROUND = "gf_tailored_bc_structural_policy_round"
RESULTS = ROOT / "results" / ROUND
RAW = RESULTS / "raw"
LOGS = RESULTS / "logs"
PROGRESS = RESULTS / "progress_traces"
MODELS = RESULTS / "model_exports"
VECTORS = RESULTS / "vector_snapshots"

LEAVES = structural.LEAVES
BUCKETS = structural.BUCKETS

DIAGNOSTIC_VARIANTS = {
    "plain_fixed_interval_mip",
    "gs_static_upper_plus_diagnostic_lower_row",
    "auto_diagnostic_recommended_profile",
}

GS_VARIANTS = {
    "gs_off",
    "gs_static_upper_only",
    "gs_callback_upper_only",
    "gs_static_plus_callback_upper_only",
    "gs_static_upper_plus_diagnostic_lower_row",
}

SP_VARIANTS = {
    "sp_aggregate_only",
    "sp_disaggregated_additive",
    "sp_disaggregated_replace_aggregate",
    "sp_disaggregated_with_tight_e_bounds",
    "sp_disaggregated_callback_only_if_violated",
}

ROUTE_VARIANTS = {
    "route_cuts_off",
    "support_cover_root_limited",
    "support_cover_callback_limited",
    "route_cutset_root_limited",
    "route_cutset_callback_limited",
    "support_cover_only_high_violation",
    "route_cutset_only_high_violation",
    "combined_route_cuts_limited",
}

SCREEN_VARIANTS = [
    "plain_fixed_interval_mip",
    "static_tailored_compact_bc",
    *sorted(GS_VARIANTS),
    *sorted(SP_VARIANTS),
    "gs_plus_sp",
    *sorted(ROUTE_VARIANTS),
    "gs_sp_route_limited",
    "auto_diagnostic_recommended_profile",
]


def f(value: Any, default: float = math.nan) -> float:
    try:
        out = float(value)
        return out if math.isfinite(out) else default
    except Exception:
        return default


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
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


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def source_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def configure_imported_runner() -> None:
    structural.RESULTS = RESULTS
    structural.RAW = RAW
    structural.LOGS = LOGS
    structural.PROGRESS = PROGRESS
    structural.MODELS = MODELS
    structural.VECTORS = VECTORS
    structural.base.RESULTS = RESULTS
    structural.base.RAW = RAW
    structural.base.LOGS = LOGS
    structural.base.PROGRESS = PROGRESS
    structural.base.MODELS = MODELS
    structural.base.MODERATE.clear()
    structural.base.MODERATE.update(LEAVES)


def base_tailored(profile: str = "manual") -> List[str]:
    return structural.base.TAILORED_COMMON + [
        "--tailored-bc-enabled", "true",
        "--tailored-bc-mode", "static",
        "--tailored-bc-callback-cut-profile", "off",
        "--tailored-bc-local-centering", "true",
        "--tailored-bc-gini-branching", "off",
        "--compact-bc-root-cut-rounds", "0",
        "--tailored-bc-gs-product-coupling", "false",
        "--tailored-bc-gs-product-lower-row", "off",
        "--tailored-bc-disaggregated-sp-estimator", "false",
        "--tailored-bc-disaggregated-sp-replace-aggregate", "false",
        "--tailored-bc-vector-support-cover", "false",
        "--tailored-bc-vector-route-cutset", "false",
        "--tailored-bc-vector-support-cover-max-cuts", "50",
        "--tailored-bc-vector-route-cutset-max-cuts", "50",
        "--tailored-bc-vector-cut-min-violation", "0.000001",
        "--tailored-bc-structural-profile", profile,
    ]


def route_flags(source: str, support: bool, route: bool,
                cap: int = 50, size: int = 4, violation: float = 1e-6) -> List[str]:
    flags = [
        "--tailored-bc-vector-support-cover", str(support).lower(),
        "--tailored-bc-vector-support-cover-max-size", str(size),
        "--tailored-bc-vector-support-cover-max-cuts", str(cap),
        "--tailored-bc-vector-route-cutset", str(route).lower(),
        "--tailored-bc-vector-route-cutset-max-size", str(size),
        "--tailored-bc-vector-route-cutset-max-cuts", str(cap),
        "--tailored-bc-vector-cut-min-violation", repr(violation),
        "--tailored-bc-vector-cut-candidate-source", source,
        "--compact-bc-support-cut-max-size", str(size),
    ]
    if source == "root":
        families = ",".join(
            family for family, enabled in (("support", support), ("route", route)) if enabled
        )
        flags += [
            "--compact-bc-root-cut-rounds", "1",
            "--compact-bc-root-cut-time-limit", "30",
            "--compact-bc-root-probe", "lp",
            "--compact-bc-dynamic-cut-families", families or "none",
            "--tailored-bc-vector-support-cover", "false",
            "--tailored-bc-vector-route-cutset", "false",
        ]
    else:
        callback_profile = "route-combined" if support and route else (
            "support-only" if support else "route-cutset-only"
        )
        flags += [
            "--tailored-bc-mode", "callback",
            "--tailored-bc-callback-cut-profile", callback_profile,
            "--tailored-bc-gini-subset-max-size", str(size),
            "--tailored-bc-gini-subset-max-cuts", str(cap),
        ]
    return flags


def variant_flags(variant: str) -> List[str]:
    if variant == "plain_fixed_interval_mip":
        return structural.base.variant_flags("plain_fixed_interval_mip") + [
            "--compact-bc-root-cut-rounds", "0",
            "--tailored-bc-structural-profile", "structural_none",
        ]
    common = base_tailored()
    if variant in {"static_tailored_compact_bc", "gs_off", "sp_aggregate_only", "route_cuts_off"}:
        return common + ["--tailored-bc-structural-profile", "structural_none"]
    if variant == "gs_static_upper_only":
        return common + [
            "--tailored-bc-gs-product-coupling", "true",
            "--tailored-bc-gs-product-coupling-mode", "static",
            "--tailored-bc-structural-profile", "structural_gs_only",
        ]
    if variant == "gs_callback_upper_only":
        return common + [
            "--tailored-bc-mode", "callback",
            "--tailored-bc-callback-cut-profile", "gs-only",
            "--tailored-bc-gs-product-coupling", "true",
            "--tailored-bc-gs-product-coupling-mode", "callback",
            "--tailored-bc-structural-profile", "structural_gs_only",
        ]
    if variant == "gs_static_plus_callback_upper_only":
        return common + [
            "--tailored-bc-mode", "callback",
            "--tailored-bc-callback-cut-profile", "gs-only",
            "--tailored-bc-gs-product-coupling", "true",
            "--tailored-bc-gs-product-coupling-mode", "both",
            "--tailored-bc-structural-profile", "structural_gs_only",
        ]
    if variant == "gs_static_upper_plus_diagnostic_lower_row":
        return common + [
            "--tailored-bc-gs-product-coupling", "true",
            "--tailored-bc-gs-product-coupling-mode", "static",
            "--tailored-bc-gs-product-lower-row", "diagnostic",
            "--tailored-bc-structural-profile", "structural_gs_only_diagnostic_lower",
        ]
    if variant in {"sp_disaggregated_additive", "sp_disaggregated_with_tight_e_bounds"}:
        return common + [
            "--tailored-bc-disaggregated-sp-estimator", "true",
            "--tailored-bc-disaggregated-sp-mode", "static",
            "--tailored-bc-disaggregated-sp-replace-aggregate", "false",
            "--tailored-bc-structural-profile", "structural_sp_only",
        ]
    if variant == "sp_disaggregated_replace_aggregate":
        return common + [
            "--tailored-bc-disaggregated-sp-estimator", "true",
            "--tailored-bc-disaggregated-sp-mode", "static",
            "--tailored-bc-disaggregated-sp-replace-aggregate", "true",
            "--tailored-bc-structural-profile", "structural_sp_only",
        ]
    if variant == "sp_disaggregated_callback_only_if_violated":
        return common + [
            "--tailored-bc-mode", "callback",
            "--tailored-bc-callback-cut-profile", "sp-only",
            "--tailored-bc-disaggregated-sp-estimator", "true",
            "--tailored-bc-disaggregated-sp-mode", "callback",
            "--tailored-bc-disaggregated-sp-replace-aggregate", "false",
            "--tailored-bc-structural-profile", "structural_sp_only",
        ]
    if variant == "gs_plus_sp":
        return variant_flags("gs_static_upper_only") + [
            "--tailored-bc-disaggregated-sp-estimator", "true",
            "--tailored-bc-disaggregated-sp-mode", "static",
            "--tailored-bc-disaggregated-sp-replace-aggregate", "false",
            "--tailored-bc-structural-profile", "structural_gs_plus_sp",
        ]
    if variant == "support_cover_root_limited":
        return common + route_flags("root", True, False)
    if variant == "support_cover_callback_limited":
        return common + route_flags("callback", True, False)
    if variant == "route_cutset_root_limited":
        return common + route_flags("root", False, True)
    if variant == "route_cutset_callback_limited":
        return common + route_flags("callback", False, True)
    if variant == "support_cover_only_high_violation":
        return common + route_flags("root", True, False, cap=20, size=3, violation=0.05)
    if variant == "route_cutset_only_high_violation":
        return common + route_flags("root", False, True, cap=20, size=3, violation=0.05)
    if variant == "combined_route_cuts_limited":
        return common + route_flags("root", True, True, cap=50, size=4)
    if variant == "gs_sp_route_limited":
        return variant_flags("gs_plus_sp") + route_flags("root", True, True, cap=20, size=3)
    if variant == "auto_diagnostic_recommended_profile":
        return variant_flags("gs_static_upper_only") + [
            "--tailored-bc-structural-profile", "auto-diagnostic",
        ]
    raise ValueError(f"unknown variant: {variant}")


def plan(profile: str) -> List[Tuple[str, str, int, str]]:
    if profile == "smoke":
        return [("low_gini_1", v, 10, "dominant_k4") for v in (
            "static_tailored_compact_bc", "gs_callback_upper_only",
            "sp_disaggregated_callback_only_if_violated", "route_cutset_callback_limited")]
    if profile == "screening":
        return [("low_gini_1", v, budget, "dominant_k4")
                for budget in (300, 1200) for v in SCREEN_VARIANTS]
    if profile == "long":
        return [("low_gini_1", v, 3600, "dominant_k4") for v in (
            "static_tailored_compact_bc", "gs_static_upper_only",
            "gs_callback_upper_only", "gs_plus_sp")]
    if profile == "very-long":
        return [("low_gini_1", v, 14400, "dominant_k4") for v in (
            "static_tailored_compact_bc", "gs_static_upper_only", "gs_plus_sp")]
    if profile == "sanity":
        return [(leaf, "gs_static_upper_only", 300, "dominant_k4") for leaf in (
            "low_gini_2", "high_imbalance_seed3201_hard", "tight_T_seed3102_hard")]
    raise ValueError(profile)


def annotate(path: Path, leaf: str, variant: str, budget: int,
             bucket: str, cmd: Sequence[str], commit: str) -> None:
    data = read_json(path)
    if not data:
        return
    data.update({
        "result_package": f"results/{ROUND}",
        "command_hash": sha16(" ".join(cmd)),
        "git_commit": commit,
        "fresh_run": True,
        "source_round": ROUND,
        "dominant_structural_policy_round": True,
        "dominant_structural_leaf": leaf,
        "dominant_structural_variant": variant,
        "dominant_s_bucket_name": bucket,
        "dominant_s_bucket_L": BUCKETS[bucket][0],
        "dominant_s_bucket_U": BUCKETS[bucket][1],
        "diagnostic_row": variant in DIAGNOSTIC_VARIANTS,
        "paper_certificate_contamination": False,
        "paper_certificate_role": (
            "diagnostic_or_benchmark_only" if variant in DIAGNOSTIC_VARIANTS
            else "paper_safe_fixed_interval_subproblem"
        ),
    })
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def row(leaf: str, variant: str, budget: int, bucket: str,
        args: argparse.Namespace, commit: str) -> Dict[str, Any]:
    spec = LEAVES[leaf]
    stem = f"{bucket}_{leaf}_{variant}_{budget}s"
    out = RAW / f"{stem}.json"
    progress = PROGRESS / f"{stem}.progress.csv"
    lp = MODELS / f"{stem}.lp"
    log = LOGS / f"{stem}.log.txt"
    cmd = structural.base.base_interval_cmd(spec, budget, out, progress, lp)
    cmd += variant_flags(variant)
    cmd += structural.bucket_flags(bucket, budget)
    if args.run:
        structural.base.run_cmd(
            cmd, log, timeout=budget + args.wrapper_grace,
            skip_existing=args.skip_existing,
        )
        if out.exists():
            annotate(out, leaf, variant, budget, bucket, cmd, commit)
    data = read_json(out)
    cutoff = f(spec["UB"], 0.0)
    lb = f(data.get("lower_bound"), f(data.get("compact_bc_best_bound"), 0.0))
    if data.get("status") == "interval_closed":
        lb = cutoff
    return {
        "result_package": f"results/{ROUND}",
        "command_hash": sha16(" ".join(cmd)),
        "git_commit": commit,
        "fresh_run": True,
        "source_round": ROUND,
        "leaf": leaf,
        "variant": variant,
        "bucket": bucket,
        "budget_seconds": budget,
        "json_path": str(out.relative_to(ROOT)),
        "progress_path": str(progress.relative_to(ROOT)) if progress.exists() else "",
        "model_path": str(lp.relative_to(ROOT)) if lp.exists() else "",
        "log_path": str(log.relative_to(ROOT)) if log.exists() else "",
        "status": data.get("status", "missing"),
        "solver_status": data.get("compact_bc_solver_status", ""),
        "lower_bound": lb,
        "upper_bound": cutoff,
        "gap_to_cutoff": max(0.0, cutoff - lb),
        "runtime_seconds": f(data.get("runtime_seconds"), 0.0),
        "nodes": data.get("compact_bc_nodes", data.get("nodes", "")),
        "last_improvement_time": data.get("last_bound_improvement_time", ""),
        "paper_safe_or_diagnostic": "diagnostic" if variant in DIAGNOSTIC_VARIANTS else "paper_safe",
        "gs_product_variable_added": data.get("gs_product_variable_added", 0),
        "gs_mccormick_rows_added": data.get("gs_mccormick_rows_added", 0),
        "gs_h_upper_rows_added": data.get("gs_h_upper_rows_added", 0),
        "gs_h_lower_rows_added": data.get("gs_h_lower_rows_added", 0),
        "gs_product_callback_rows_added": data.get("gs_product_callback_rows_added", 0),
        "disagg_sp_variables_added": data.get("disagg_sp_variables_added", 0),
        "disagg_sp_mccormick_rows_added": data.get("disagg_sp_mccormick_rows_added", 0),
        "disagg_sp_estimator_rows_added": data.get("disagg_sp_estimator_rows_added", 0),
        "disagg_sp_callback_rows_added": data.get("disagg_sp_callback_rows_added", 0),
        "vector_support_cover_candidates": data.get("vector_support_cover_candidates", 0),
        "vector_support_cover_cuts_added": data.get("vector_support_cover_cuts_added", 0),
        "vector_route_cutset_candidates": data.get("vector_route_cutset_candidates", 0),
        "vector_route_cutset_cuts_added": data.get("vector_route_cutset_cuts_added", 0),
        "vector_callback_support_cover_candidates": data.get("vector_callback_support_cover_candidates", 0),
        "vector_callback_support_cover_cuts_added": data.get("vector_callback_support_cover_cuts_added", 0),
        "vector_callback_route_cutset_candidates": data.get("vector_callback_route_cutset_candidates", 0),
        "vector_callback_route_cutset_cuts_added": data.get("vector_callback_route_cutset_cuts_added", 0),
        "dynamic_cuts": data.get("compact_bc_dynamic_cuts_added_by_family", ""),
        "thread_fairness_class": data.get("thread_fairness_class", ""),
    }


def all_rows(commit: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path in sorted(RAW.glob("*.json")):
        data = read_json(path)
        if data.get("source_round") != ROUND or not data.get("fresh_run"):
            continue
        leaf = str(data.get("dominant_structural_leaf", ""))
        variant = str(data.get("dominant_structural_variant", ""))
        bucket = str(data.get("dominant_s_bucket_name", "dominant_k4"))
        budget = int(f(data.get("time_budget_seconds"), 0.0))
        if not leaf or not variant or budget <= 0:
            continue
        class Dummy:
            run = False
            wrapper_grace = 0
            skip_existing = True
        rows.append(row(leaf, variant, budget, bucket, Dummy(), commit))
    return rows


def write_vector_tables(rows: Sequence[Dict[str, Any]], extract_root: bool) -> None:
    structural.build_vector_outputs(rows, extract_root=extract_root)
    callback = read_csv(RESULTS / "callback_vector_family_summary.csv")
    root = read_csv(RESULTS / "root_lp_family_summary.csv")
    combined = callback + root
    write_csv(RESULTS / "root_gap_decomposition.csv", combined)
    write_csv(RESULTS / "sp_gap_decomposition.csv", [
        {k: r.get(k, "") for k in (
            "snapshot_id", "snapshot_source", "S", "P", "W_SP",
            "sum_i_w_i_T_SP_i", "reconstructed_S_times_P",
            "SP_gap_aggregate", "SP_gap_disaggregated", "top_T_SP_i")}
        for r in combined
    ])
    write_csv(RESULTS / "gsh_gap_decomposition.csv", [
        {k: r.get(k, "") for k in (
            "snapshot_id", "snapshot_source", "S", "H", "G", "W_GS",
            "reconstructed_H_over_VS", "GSH_gap", "W_GS_gap")}
        for r in combined
    ])
    write_csv(RESULTS / "route_fractionality_summary.csv", [
        {k: r.get(k, "") for k in (
            "snapshot_id", "snapshot_source", "top_fractional_z", "top_fractional_x",
            "top_fractional_p", "top_fractional_d", "top_route_support_station_sets_by_vehicle")}
        for r in combined
    ])
    raw = read_csv(RESULTS / "callback_vector_raw.csv") + read_csv(RESULTS / "root_lp_vector_raw.csv")
    unknown = [r for r in raw if r.get("family") == "unknown_unparsed"]
    write_csv(RESULTS / "unparsed_column_report.csv", unknown)
    write_csv(RESULTS / "vector_parser_audit.csv", [{
        "result_package": f"results/{ROUND}",
        "fresh_run": True,
        "vector_rows": len(raw),
        "unknown_unparsed_rows": len(unknown),
        "unknown_fraction": len(unknown) / len(raw) if raw else "not_available",
        "passed": bool(raw) and (len(unknown) / len(raw) <= 0.05),
    }])


def write_tables(rows: Sequence[Dict[str, Any]]) -> None:
    target = [r for r in rows if r["leaf"] == "low_gini_1"]
    write_csv(RESULTS / "dominant_bucket_policy_comparison.csv", target)
    write_csv(RESULTS / "dominant_bucket_fresh_baseline.csv", [
        r for r in target if r["variant"] in {"plain_fixed_interval_mip", "static_tailored_compact_bc"}
    ])
    write_csv(RESULTS / "gs_activation_ablation.csv", [r for r in target if r["variant"] in GS_VARIANTS])
    write_csv(RESULTS / "disaggregated_sp_ablation.csv", [r for r in target if r["variant"] in SP_VARIANTS])
    write_csv(RESULTS / "vector_route_activation_ablation.csv", [r for r in target if r["variant"] in ROUTE_VARIANTS])
    write_csv(RESULTS / "non_regression_sanity_summary.csv", [r for r in rows if r["leaf"] != "low_gini_1"])
    write_csv(RESULTS / "cut_family_effectiveness.csv", target)

    callback = read_csv(RESULTS / "callback_vector_family_summary.csv")
    root = read_csv(RESULTS / "root_lp_family_summary.csv")
    write_csv(RESULTS / "gs_gap_impact_summary.csv", [r for r in callback + root if r.get("W_GS") not in {"", "not_available"}])
    write_csv(RESULTS / "disaggregated_sp_gap_summary.csv", [r for r in callback + root if r.get("sum_i_w_i_T_SP_i") not in {"", "not_available"}])
    write_csv(RESULTS / "vector_route_fractionality_impact.csv", callback + root)

    progress_rows: List[Dict[str, Any]] = []
    for summary in rows:
        for item in read_csv(ROOT / summary["progress_path"]) if summary["progress_path"] else []:
            item.update({
                "variant": summary["variant"],
                "leaf": summary["leaf"],
                "budget_seconds": summary["budget_seconds"],
                "source_round": ROUND,
                "fresh_run": True,
            })
            progress_rows.append(item)
    write_csv(RESULTS / "dominant_bucket_bound_trajectory.csv", progress_rows)


def write_policy(rows: Sequence[Dict[str, Any]]) -> None:
    target_1200 = [r for r in rows if r["leaf"] == "low_gini_1" and r["budget_seconds"] == 1200]
    safe = [r for r in target_1200 if r["paper_safe_or_diagnostic"] == "paper_safe"]
    best = max(safe, key=lambda r: f(r.get("lower_bound"), -math.inf), default={})
    decisions = []
    profiles = {
        "structural_none": "static_tailored_compact_bc",
        "structural_gs_only": "gs_static_upper_only",
        "structural_sp_only": "sp_disaggregated_additive",
        "structural_gs_plus_sp": "gs_plus_sp",
        "structural_route_limited": "combined_route_cuts_limited",
        "structural_gs_sp_route_limited": "gs_sp_route_limited",
        "static_tailored_baseline": "static_tailored_compact_bc",
    }
    for profile, variant in profiles.items():
        observed = next((r for r in target_1200 if r["variant"] == variant), {})
        selected = variant == best.get("variant")
        decisions.append({
            "profile": profile,
            "selection_reason": (
                "best_fresh_1200s_valid_LB" if selected else "not_best_fresh_1200s_valid_LB"
            ),
            "generic_metrics_used": "gamma_U|S_bucket_active|root_GSH_gap|root_SP_gap|route_fractionality|model_size|1200s_LB",
            "observed_variant": variant,
            "observed_1200s_LB": observed.get("lower_bound", "not_run"),
            "paper_default_candidate": selected,
            "diagnostic_only": False,
        })
    write_csv(RESULTS / "structural_profile_decision_table.csv", decisions)
    (RESULTS / "structural_profile_policy.md").write_text(
        "# Structural Profile Policy\n\n"
        "`auto-diagnostic` recommends a profile from generic interval metrics only. "
        "It does not alter paper-default behavior in this round and never reads an instance name, seed, path, or known outcome.\n\n"
        f"Fresh 1200s recommendation: `{best.get('variant', 'insufficient_data')}`.\n",
        encoding="utf-8",
    )


def write_scope(commit: str) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "structural_policy_scope.md").write_text(
        "# Structural Policy Scope\n\n"
        f"- Source commit for fresh solver rows: `{commit}`.\n"
        "- Mainline: `paper-gf-tailored-bc`.\n"
        "- Official benchmark: current binary-expansion compact MILP with CPLEX.\n"
        "- Callback/root vectors and auto-selection are diagnostic only.\n"
        "- No fixed-interval incumbent is imported as a global UB.\n"
        "- No full-frontier run uses an imported UB.\n"
        "- BPC, route-mask, archive, known-UB, external-incumbent, and focus-only evidence are excluded.\n",
        encoding="utf-8",
    )
    (RESULTS / "historical_context.md").write_text(
        "# Historical Context\n\n"
        "Historical motivation only: the previous structural round suggested GS coupling was promising, "
        "the prior static tailored long run was strong, and broad static vector route rows weakened the bound. "
        "No prior raw row is copied into this package or used in its comparison tables.\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", choices=["smoke", "screening", "long", "very-long", "sanity"], default="smoke")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--skip-existing", action="store_true")
    ap.add_argument("--extract-root-lp", action="store_true")
    ap.add_argument("--wrapper-grace", type=int, default=180)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--only-variants", default="")
    ap.add_argument("--max-budget", type=int, default=0)
    args = ap.parse_args()

    configure_imported_runner()
    for directory in (RAW, LOGS, PROGRESS, MODELS, VECTORS):
        directory.mkdir(parents=True, exist_ok=True)
    commit = source_commit()
    write_scope(commit)
    planned = plan(args.profile)
    if args.only_variants:
        keep = {v.strip() for v in args.only_variants.split(",") if v.strip()}
        planned = [item for item in planned if item[1] in keep]
    if args.max_budget > 0:
        planned = [item for item in planned if item[2] <= args.max_budget]

    def execute(item: Tuple[str, str, int, str]) -> Dict[str, Any]:
        return row(*item, args, commit)

    if args.jobs > 1 and len(planned) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
            list(pool.map(execute, planned))
    else:
        for item in planned:
            execute(item)

    summaries = all_rows(commit)
    write_vector_tables(summaries, extract_root=args.extract_root_lp)
    write_tables(summaries)
    write_policy(summaries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
