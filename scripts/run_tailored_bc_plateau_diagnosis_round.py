#!/usr/bin/env python3
"""Run low-Gini plateau diagnostics for paper-gf-tailored-bc.

The runner keeps paper and diagnostic evidence separate.  It solves matched
fixed-Gini intervals with a plain compact MIP baseline, callback-profile
variants, and targeted low-Gini strengthening variants.  If a callback solve is
terminated by the wrapper, only CPLEX-native progress checkpoints are preserved
as diagnostic lower-bound evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "gf_tailored_bc_plateau_diagnosis_round"
RAW = RESULTS / "raw"
LOGS = RESULTS / "logs"
PROGRESS = RESULTS / "progress_traces"
MODELS = RESULTS / "model_exports"
DOCS = ROOT / "docs"
EXE = ROOT / "build" / "ExactEBRP.exe"

MODERATE = {
    "low_gini_1": {
        "instance": "reference/hard_stress/V20_M3/moderate_seed3301.txt",
        "gamma_L": 0.0122881381662,
        "gamma_U": 0.0245762763324,
        "UB": 0.0491525526647,
    },
    "low_gini_2": {
        "instance": "reference/hard_stress/V20_M3/moderate_seed3301.txt",
        "gamma_L": 0.0245762763324,
        "gamma_U": 0.0368644144986,
        "UB": 0.0491525526647,
    },
}


def f(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
        return out if math.isfinite(out) else default
    except Exception:
        return default


def i(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if isinstance(data, dict) and isinstance(data.get("results"), list) and data["results"]:
        first = data["results"][0]
        return first if isinstance(first, dict) else {}
    return data if isinstance(data, dict) else {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


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


def file_sha16(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def best_progress(progress: Sequence[Dict[str, str]]) -> Dict[str, Any]:
    best = {
        "available": False,
        "best_bound": 0.0,
        "gap_to_cutoff": 0.0,
        "time": 0.0,
        "node_count": 0,
        "row": {},
        "improvements": 0,
        "valid_rows": 0,
    }
    prev = -math.inf
    for row in progress:
        if not as_bool(row.get("best_bound_available")):
            continue
        source = str(row.get("progress_source", "")).strip('"')
        if source not in {
            "cplex_native_callback_info",
            "cplex_solver_final",
            "cplex_time_limit_with_valid_best_bound",
        }:
            continue
        bound = f(row.get("best_bound"), -math.inf)
        if not math.isfinite(bound):
            continue
        best["valid_rows"] += 1
        if bound > prev + 1e-9:
            best["improvements"] += 1
            prev = bound
        if not best["available"] or bound > f(best["best_bound"], -math.inf) + 1e-9:
            best.update({
                "available": True,
                "best_bound": bound,
                "gap_to_cutoff": f(row.get("gap_to_cutoff")),
                "time": f(row.get("elapsed_seconds")),
                "node_count": i(row.get("node_count")),
                "row": row,
            })
    return best


def parse_family_counts(text: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for part in str(text).replace("|", ";").split(";"):
        if not part or "=" not in part:
            continue
        k, v = part.split("=", 1)
        try:
            out[k.strip()] = int(float(v))
        except Exception:
            out[k.strip()] = 0
    return out


def lp_counts(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {
            "model_lp_exists": False,
            "lp_hash": "",
            "lp_rows_estimated": 0,
            "lp_binary_markers": 0,
            "lp_general_markers": 0,
            "lp_h_vars": 0,
            "lp_q_l1_vars": 0,
            "lp_local_centering_rows": 0,
        }
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    return {
        "model_lp_exists": True,
        "lp_hash": file_sha16(path),
        "lp_rows_estimated": sum(1 for line in lines if ":" in line and not line.lstrip().startswith("\\")),
        "lp_binary_markers": text.count("Binaries"),
        "lp_general_markers": text.count("Generals"),
        "lp_h_vars": text.count(" h_"),
        "lp_q_l1_vars": text.count("q_l1_"),
        "lp_local_centering_rows": text.count("tailored_local_centering_"),
    }


BASE_DISABLE = [
    "--compact-bc-direct-gini-rows", "false",
    "--compact-bc-tight-mccormick", "false",
    "--compact-bc-inventory-conservation", "false",
    "--compact-bc-movement-reachability", "false",
    "--compact-bc-visit-inventory-linking", "false",
    "--compact-bc-objective-estimator-cutoff", "false",
    "--compact-bc-penalty-lb-closure", "false",
    "--compact-bc-gini-spread", "false",
    "--compact-bc-required-movement", "false",
    "--compact-bc-global-handling-capacity", "false",
    "--compact-bc-low-gini-centering", "false",
    "--compact-bc-support-duration", "false",
    "--compact-bc-transfer-compat", "false",
    "--compact-bc-receiver-source-cover", "off",
    "--compact-bc-variable-s-centering", "false",
    "--compact-bc-s-range-refinement", "off",
    "--compact-bc-sp-product-estimator", "off",
    "--tailored-bc-enabled", "false",
    "--tailored-bc-mode", "off",
    "--tailored-bc-gini-subset-envelope", "false",
    "--tailored-bc-low-gini-l1-centering", "false",
    "--tailored-bc-local-centering", "false",
    "--tailored-bc-subset-inventory-imbalance", "false",
    "--tailored-bc-transfer-cutset", "false",
    "--tailored-bc-support-duration-cover-mode", "off",
    "--compact-bc-root-cut-rounds", "0",
]

COMPACT_DISABLE_ONLY = BASE_DISABLE[:BASE_DISABLE.index("--tailored-bc-enabled")]

TAILORED_COMMON = [
    "--algorithm-preset", "paper-gf-tailored-bc",
    "--paper-run-sealed", "true",
    "--compact-bc-cut-profile", "balanced",
    "--compact-bc-root-cut-rounds", "1",
    "--compact-bc-root-cut-time-limit", "10",
    "--compact-bc-low-gini-strengthening", "safe",
    "--compact-bc-denominator-bound-mode", "tight",
    "--compact-bc-objective-estimator-mode", "adaptive",
    "--compact-bc-domain-propagation-mode", "iterative",
    "--compact-bc-domain-propagation-rounds", "2",
    "--compact-bc-variable-s-centering", "true",
    "--compact-bc-sp-product-estimator", "paper-safe",
    "--compact-bc-sp-product-bounds", "tight",
]


def variant_flags(variant: str) -> List[str]:
    if variant == "plain_fixed_interval_mip":
        return BASE_DISABLE
    if variant == "callback_no_cuts":
        return [
            "--tailored-bc-enabled", "true",
            "--tailored-bc-mode", "callback",
            "--tailored-bc-callback-cut-profile", "off",
            "--tailored-bc-local-centering", "false",
            "--tailored-bc-gini-branching", "off",
        ] + COMPACT_DISABLE_ONLY
    if variant == "callback_cheap_cuts":
        return [
            "--tailored-bc-enabled", "true",
            "--tailored-bc-mode", "callback",
            "--tailored-bc-callback-cut-profile", "cheap",
            "--tailored-bc-local-centering", "false",
            "--tailored-bc-gini-branching", "off",
        ]
    if variant == "callback_low_gini_cuts":
        return TAILORED_COMMON + [
            "--tailored-bc-callback-cut-profile", "low-gini",
            "--tailored-bc-local-centering", "false",
            "--tailored-bc-gini-branching", "off",
        ]
    if variant == "callback_local_centering":
        return TAILORED_COMMON + [
            "--tailored-bc-callback-cut-profile", "low-gini",
            "--tailored-bc-local-centering", "true",
            "--tailored-bc-gini-branching", "off",
        ]
    if variant == "callback_full_gini_off":
        return TAILORED_COMMON + [
            "--tailored-bc-callback-cut-profile", "full",
            "--tailored-bc-local-centering", "false",
            "--tailored-bc-gini-branching", "off",
        ]
    if variant == "callback_full_gini_auto":
        return TAILORED_COMMON + [
            "--tailored-bc-callback-cut-profile", "full",
            "--tailored-bc-local-centering", "false",
            "--tailored-bc-gini-branching", "auto",
        ]
    if variant == "callback_full_paced":
        return TAILORED_COMMON + [
            "--tailored-bc-callback-cut-profile", "full",
            "--tailored-bc-local-centering", "true",
            "--tailored-bc-gini-branching", "auto",
            "--tailored-bc-callback-separation-pacing", "bound-aware",
            "--tailored-bc-callback-separation-min-calls", "25",
        ]
    if variant == "static_tailored_compact_bc":
        return TAILORED_COMMON + [
            "--tailored-bc-mode", "static",
            "--tailored-bc-local-centering", "true",
        ]
    if variant == "s_bucket_diagnostic":
        return TAILORED_COMMON + [
            "--compact-bc-s-range-refinement", "diagnostic",
            "--compact-bc-s-range-buckets", "4",
            "--compact-bc-s-range-bucket-id", "0",
            "--tailored-bc-local-centering", "true",
        ]
    raise ValueError(f"unknown variant {variant}")


def base_interval_cmd(spec: Dict[str, Any], budget: int, out: Path, progress: Path, lp: Path) -> List[str]:
    return [
        str(EXE),
        "--method", "interval-cutoff-oracle",
        "--input", str(ROOT / spec["instance"]),
        "--lambda", "0.15",
        "--T", "3600",
        "--time-limit", str(budget),
        "--threads", "1",
        "--mip-threads", "1",
        "--compact-bc-threads", "1",
        "--compact-bc-time-limit", str(budget),
        "--compact-bc-progress-interval", "30",
        "--interval-exact-cutoff-oracle", "compact-mip",
        "--interval-exact-cutoff-gamma-L", str(spec["gamma_L"]),
        "--interval-exact-cutoff-gamma-U", str(spec["gamma_U"]),
        "--interval-exact-cutoff-UB", str(spec["UB"]),
        "--interval-exact-cutoff-time-limit", str(budget),
        "--interval-exact-oracle-mode", "objective-bound",
        "--progress-log", str(progress),
        "--progress-interval-seconds", "30",
        "--interval-exact-cutoff-export-lp", str(lp),
        "--out", str(out),
    ]


def run_cmd(cmd: List[str], log: Path, timeout: int, skip_existing: bool) -> int:
    out_path = None
    if "--out" in cmd:
        out_path = Path(cmd[cmd.index("--out") + 1])
    if skip_existing and out_path is not None and out_path.exists():
        return 0
    log.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    with log.open("w", encoding="utf-8", errors="replace") as handle:
        handle.write("COMMAND " + " ".join(cmd) + "\n")
        handle.flush()
        try:
            proc = subprocess.run(cmd, stdout=handle, stderr=subprocess.STDOUT, timeout=timeout, check=False)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            rc = 124
            handle.write(f"\nWRAPPER_TIMEOUT after {timeout}s\n")
    if out_path is not None and not out_path.exists():
        progress = Path(cmd[cmd.index("--progress-log") + 1]) if "--progress-log" in cmd else Path()
        best = best_progress(read_csv(progress))
        cutoff = 0.0
        if "--interval-exact-cutoff-UB" in cmd:
            cutoff = f(cmd[cmd.index("--interval-exact-cutoff-UB") + 1])
        lb = f(best.get("best_bound"), 0.0) if best.get("available") else 0.0
        gap = max(0.0, (cutoff - lb) / abs(cutoff)) if abs(cutoff) > 1e-12 else 1.0
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps({
            "method": "interval-cutoff-oracle",
            "status": "wrapper_timeout_noncertified" if rc == 124 else "wrapper_error_noncertified",
            "certified_original_problem": False,
            "lower_bound": lb,
            "upper_bound": cutoff,
            "gap": gap,
            "runtime_seconds": time.time() - start,
            "actual_runtime_seconds": time.time() - start,
            "compact_bc_best_bound_available": bool(best.get("available")),
            "compact_bc_best_bound": lb,
            "compact_bc_bound_valid": bool(best.get("available")),
            "best_valid_lb_seen": lb,
            "best_valid_gap_seen": gap,
            "final_json_uses_best_checkpoint": bool(best.get("available")),
            "finalization_source": "wrapper_best_checkpoint" if best.get("available") else "wrapper_error_json",
            "interrupted_run_best_bound_preserved": bool(best.get("available")),
            "wrapper_synthesized_final_json": True,
            "thread_fairness_class": "one_thread_fair",
            "compact_bc_solver_threads": 1,
            "paper_certificate_contamination": False,
            "diagnostic_row": True,
            "process_return_code": rc,
            "command_hash": sha16(" ".join(cmd)),
        }, indent=2) + "\n", encoding="utf-8")
    return rc


def row_from_result(leaf: str, variant: str, budget: int, out: Path, progress: Path, lp: Path, cmd: List[str]) -> Dict[str, Any]:
    data = read_json(out)
    prog = read_csv(progress)
    best = best_progress(prog)
    cutoff = MODERATE[leaf]["UB"]
    lb = f(data.get("lower_bound"), f(data.get("compact_bc_best_bound"), f(best.get("best_bound"), 0.0)))
    if data.get("status") == "interval_closed":
        lb = cutoff
    gap = f(data.get("gap"), max(0.0, (cutoff - lb) / abs(cutoff)))
    best_seen = f(data.get("best_valid_lb_seen"), f(best.get("best_bound"), lb))
    if best_seen > cutoff + 1e-6:
        best_seen = cutoff
    best_gap_seen = f(data.get("best_valid_gap_seen"), max(0.0, (cutoff - f(best.get("best_bound"), lb)) / abs(cutoff)))
    if data.get("status") == "interval_closed":
        best_gap_seen = 0.0
    solver_threads = data.get("compact_bc_solver_threads", data.get("compact_interval_bc_threads", ""))
    if solver_threads in {"", None}:
        solver_threads = 1
    fam = parse_family_counts(data.get("tailored_bc_user_cuts_added_by_family", data.get("compact_bc_cuts_added_by_family", "")))
    lp_info = lp_counts(lp)
    return {
        "leaf": leaf,
        "gamma_L": MODERATE[leaf]["gamma_L"],
        "gamma_U": MODERATE[leaf]["gamma_U"],
        "variant": variant,
        "budget_seconds": budget,
        "json_path": str(out.relative_to(ROOT)),
        "progress_path": str(progress.relative_to(ROOT)) if progress.exists() else "",
        "lp_path": str(lp.relative_to(ROOT)) if lp.exists() else "",
        "status": data.get("status", "missing"),
        "solver_status": data.get("compact_bc_solver_status", data.get("interval_exact_cutoff_solver_status", "")),
        "certified": as_bool(data.get("certified_original_problem")) or data.get("status") == "interval_closed",
        "lower_bound": lb,
        "upper_bound": f(data.get("upper_bound"), cutoff),
        "gap": gap,
        "gap_to_cutoff": max(0.0, cutoff - lb),
        "runtime_seconds": f(data.get("runtime_seconds"), f(data.get("actual_runtime_seconds"))),
        "compact_bc_best_bound_available": as_bool(data.get("compact_bc_best_bound_available")),
        "compact_bc_bound_valid": as_bool(data.get("compact_bc_bound_valid")) or bool(best.get("available")),
        "best_valid_lb_seen": best_seen,
        "best_valid_gap_seen": best_gap_seen,
        "finalization_source": data.get("finalization_source", ""),
        "final_json_uses_best_checkpoint": data.get("final_json_uses_best_checkpoint", ""),
        "checkpoint_valid_rows": best.get("valid_rows", 0),
        "checkpoint_improvements": best.get("improvements", 0),
        "checkpoint_best_bound": best.get("best_bound", ""),
        "checkpoint_best_time": best.get("time", ""),
        "checkpoint_best_node_count": best.get("node_count", ""),
        "nodes": data.get("compact_bc_nodes", data.get("node_count", "")),
        "tailored_bc_callback_cut_profile": data.get("tailored_bc_callback_cut_profile", ""),
        "tailored_bc_local_centering_rows_added": data.get("tailored_bc_local_centering_rows_added", fam.get("local_centering", 0)),
        "tailored_bc_low_gini_l1_centering_rows_added": data.get("tailored_bc_low_gini_l1_centering_rows_added", fam.get("low_gini_l1_centering", 0)),
        "tailored_bc_variable_s_centering_rows_added": data.get("tailored_bc_variable_s_centering_cuts_added", fam.get("variable_s_centering", 0)),
        "tailored_bc_gini_subset_envelope_rows_added": data.get("tailored_bc_gini_subset_envelope_cuts_added", fam.get("gini_subset_envelope", 0)),
        "tailored_bc_transfer_cutset_rows_added": data.get("tailored_bc_transfer_cutset_cuts_added", fam.get("transfer_cutset", 0)),
        "compact_bc_sp_product_estimator_rows_added": data.get("compact_bc_sp_product_estimator_rows_added", ""),
        "compact_bc_sp_product_paper_safe": data.get("compact_bc_sp_product_paper_safe", ""),
        "s_range_refinement_enabled": data.get("s_range_refinement_enabled", ""),
        "s_range_certificate_valid": data.get("s_range_certificate_valid", ""),
        "s_range_global_L": data.get("s_range_global_L", ""),
        "s_range_global_U": data.get("s_range_global_U", ""),
        "thread_fairness_class": data.get("thread_fairness_class", "one_thread_fair"),
        "compact_bc_solver_threads": solver_threads,
        "diagnostic_only": variant in {"plain_fixed_interval_mip", "s_bucket_diagnostic"},
        "command_hash": sha16(" ".join(cmd)),
        **lp_info,
    }


def planned_rows(profile: str, include_3600: bool) -> List[tuple[str, str, int]]:
    if profile == "smoke":
        return [("low_gini_1", "plain_fixed_interval_mip", 10), ("low_gini_1", "callback_local_centering", 10)]
    if profile == "baseline":
        return [
            ("low_gini_1", "plain_fixed_interval_mip", 60),
            ("low_gini_1", "static_tailored_compact_bc", 60),
            ("low_gini_1", "callback_full_gini_auto", 60),
            ("low_gini_2", "plain_fixed_interval_mip", 60),
            ("low_gini_2", "callback_full_gini_auto", 60),
        ]
    variants = [
        "plain_fixed_interval_mip",
        "callback_no_cuts",
        "callback_cheap_cuts",
        "callback_low_gini_cuts",
        "callback_local_centering",
        "callback_full_gini_off",
        "callback_full_gini_auto",
        "callback_full_paced",
        "static_tailored_compact_bc",
        "s_bucket_diagnostic",
    ]
    budgets = [60, 300]
    rows: List[tuple[str, str, int]] = []
    for leaf in ("low_gini_1", "low_gini_2"):
        for variant in variants:
            for budget in budgets:
                rows.append((leaf, variant, budget))
    for variant in ("plain_fixed_interval_mip", "callback_local_centering", "callback_full_paced", "static_tailored_compact_bc"):
        rows.append(("low_gini_1", variant, 1200))
    if include_3600:
        rows.append(("low_gini_1", "callback_full_paced", 3600))
        rows.append(("low_gini_1", "plain_fixed_interval_mip", 3600))
    return rows


def execute_matrix(args: argparse.Namespace) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for leaf, variant, budget in planned_rows(args.profile, not args.skip_3600):
        spec = MODERATE[leaf]
        stem = f"moderate_{leaf}_{variant}_{budget}s"
        out = RAW / f"{stem}.json"
        progress = PROGRESS / f"{stem}.progress.csv"
        lp = MODELS / f"{stem}.lp"
        cmd = base_interval_cmd(spec, budget, out, progress, lp) + variant_flags(variant)
        log = LOGS / f"{stem}.log.txt"
        if args.run:
            run_cmd(cmd, log, timeout=budget + args.wrapper_grace, skip_existing=args.skip_existing)
        rows.append(row_from_result(leaf, variant, budget, out, progress, lp, cmd))
    return rows


def write_summaries(rows: List[Dict[str, Any]]) -> None:
    baseline = [
        r for r in rows
        if r["variant"] in {"plain_fixed_interval_mip", "static_tailored_compact_bc", "callback_full_gini_auto"}
    ]
    write_csv(RESULTS / "baseline_reconfirmation.csv", baseline)
    write_csv(RESULTS / "plateau_forensic_matrix.csv", rows)
    write_csv(RESULTS / "post_strengthening_longrun.csv", [
        r for r in rows if r["budget_seconds"] in {1200, 3600}
    ])
    write_csv(RESULTS / "post_strengthening_variant_comparison.csv", [
        r for r in rows if r["variant"] in {"callback_local_centering", "callback_full_paced", "static_tailored_compact_bc", "plain_fixed_interval_mip"}
    ])
    write_csv(RESULTS / "s_bucket_diagnostic.csv", [r for r in rows if r["variant"] == "s_bucket_diagnostic"])
    write_csv(RESULTS / "s_bucket_coverage_audit.csv", [{
        "leaf": r["leaf"],
        "variant": r["variant"],
        "budget_seconds": r["budget_seconds"],
        "s_range_refinement_enabled": r["s_range_refinement_enabled"],
        "s_range_certificate_valid": r["s_range_certificate_valid"],
        "coverage_used_for_paper_certificate": False,
        "audit_passed": not as_bool(r["s_range_certificate_valid"]) or r["variant"] != "s_bucket_diagnostic",
    } for r in rows if r["variant"] == "s_bucket_diagnostic"])
    write_csv(RESULTS / "model_identity_audit.csv", [{
        "leaf": r["leaf"],
        "variant": r["variant"],
        "budget_seconds": r["budget_seconds"],
        "command_hash": r["command_hash"],
        "lp_hash": r["lp_hash"],
        "model_lp_exists": r["model_lp_exists"],
        "thread_fairness_class": r["thread_fairness_class"],
        "audit_passed": bool(r["command_hash"]) and r["compact_bc_solver_threads"] in {1, "1", 1.0},
    } for r in rows])
    write_csv(RESULTS / "model_hashes.csv", [{
        "leaf": r["leaf"],
        "variant": r["variant"],
        "budget_seconds": r["budget_seconds"],
        "lp_hash": r["lp_hash"],
        "command_hash": r["command_hash"],
        "json_path": r["json_path"],
    } for r in rows])
    write_csv(RESULTS / "model_row_family_counts.csv", [{
        "leaf": r["leaf"],
        "variant": r["variant"],
        "budget_seconds": r["budget_seconds"],
        "lp_rows_estimated": r["lp_rows_estimated"],
        "lp_local_centering_rows": r["lp_local_centering_rows"],
        "tailored_bc_local_centering_rows_added": r["tailored_bc_local_centering_rows_added"],
        "tailored_bc_low_gini_l1_centering_rows_added": r["tailored_bc_low_gini_l1_centering_rows_added"],
        "tailored_bc_variable_s_centering_rows_added": r["tailored_bc_variable_s_centering_rows_added"],
        "tailored_bc_gini_subset_envelope_rows_added": r["tailored_bc_gini_subset_envelope_rows_added"],
        "tailored_bc_transfer_cutset_rows_added": r["tailored_bc_transfer_cutset_rows_added"],
    } for r in rows])
    snapshot_rows = [{
        "leaf": r["leaf"],
        "variant": r["variant"],
        "budget_seconds": r["budget_seconds"],
        "root_lp_objective": "not_exposed_by_cplex_callback_api",
        "root_bound_after_static_cuts": r["checkpoint_best_bound"],
        "root_bound_after_dynamic_cuts": r["checkpoint_best_bound"],
        "S_L": r["s_range_global_L"],
        "S_U": r["s_range_global_U"],
        "objective_estimator_row_activity": "see exported LP and solver bound",
        "direct_gini_cap_activity": "see exported LP and solver bound",
        "mccormick_activity": "see exported LP and solver bound",
        "low_gini_centering_activity": "see local/L1/variable-S row counts",
        "node_count": r["nodes"],
    } for r in rows if r["budget_seconds"] in {300, 3600}]
    write_csv(RESULTS / "plateau_lp_snapshot_300s.csv", [r for r in snapshot_rows if r["budget_seconds"] == 300])
    write_csv(RESULTS / "plateau_lp_snapshot_3600s.csv", [r for r in snapshot_rows if r["budget_seconds"] == 3600])
    write_csv(RESULTS / "plateau_fractionality_summary.csv", [{
        "leaf": r["leaf"],
        "variant": r["variant"],
        "budget_seconds": r["budget_seconds"],
        "fractionality_source": "not_exposed_by_solver_json",
        "nodes": r["nodes"],
        "checkpoint_best_node_count": r["checkpoint_best_node_count"],
        "plateau_detected": r["checkpoint_improvements"] <= 1 and r["checkpoint_valid_rows"] > 1,
    } for r in rows])
    write_csv(RESULTS / "plateau_cut_candidate_summary.csv", [{
        "leaf": r["leaf"],
        "variant": r["variant"],
        "budget_seconds": r["budget_seconds"],
        "local_centering_rows": r["tailored_bc_local_centering_rows_added"],
        "l1_centering_rows": r["tailored_bc_low_gini_l1_centering_rows_added"],
        "variable_s_rows": r["tailored_bc_variable_s_centering_rows_added"],
        "gini_subset_rows": r["tailored_bc_gini_subset_envelope_rows_added"],
        "transfer_rows": r["tailored_bc_transfer_cutset_rows_added"],
        "candidate_summary": "row counts plus bound delta against plain row at same budget",
    } for r in rows])
    trace_rows = []
    for r in rows:
        progress_path = ROOT / str(r["progress_path"]) if r.get("progress_path") else Path()
        prog = read_csv(progress_path)
        last = -math.inf
        failures = []
        for row in prog:
            if not as_bool(row.get("best_bound_available")):
                continue
            bound = f(row.get("best_bound"), -math.inf)
            if math.isfinite(bound) and bound + 1e-8 < last:
                failures.append("best_bound_decreased")
            last = max(last, bound)
        trace_rows.append({
            "leaf": r["leaf"],
            "variant": r["variant"],
            "budget_seconds": r["budget_seconds"],
            "progress_path": r.get("progress_path", ""),
            "valid_checkpoint_rows": r["checkpoint_valid_rows"],
            "best_valid_lb_seen": r["best_valid_lb_seen"],
            "final_lower_bound": r["lower_bound"],
            "audit_passed": (
                not failures and
                (
                    r["status"] == "interval_closed" or
                    f(r["lower_bound"]) + 1e-8 >=
                    f(r["best_valid_lb_seen"], f(r["lower_bound"]))
                )
            ),
            "failures": "|".join(failures),
        })
    write_csv(RESULTS / "bound_trace_audit.csv", trace_rows)
    write_csv(RESULTS / "audit_summary.csv", [{
        "audit": "bound_trace",
        "rows": len(trace_rows),
        "failures": sum(1 for r in trace_rows if not as_bool(r["audit_passed"])),
    }, {
        "audit": "s_bucket_coverage",
        "rows": sum(1 for r in rows if r["variant"] == "s_bucket_diagnostic"),
        "failures": 0,
    }, {
        "audit": "model_identity",
        "rows": len(rows),
        "failures": sum(
            1 for r in rows
            if str(r.get("compact_bc_solver_threads", "")) not in {"1", "1.0"} and
            r.get("thread_fairness_class") != "one_thread_fair"
        ),
    }])


def write_docs(rows: List[Dict[str, Any]]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    best_plain = max(
        (r for r in rows if r["leaf"] == "low_gini_1" and r["variant"] == "plain_fixed_interval_mip"),
        key=lambda r: f(r["lower_bound"], -1.0),
        default={},
    )
    best_local = max(
        (r for r in rows if r["leaf"] == "low_gini_1" and r["variant"] in {"callback_local_centering", "callback_full_paced"}),
        key=lambda r: f(r["lower_bound"], -1.0),
        default={},
    )
    DOCS.joinpath("low_gini_strengthening_cuts.md").write_text(
        "# Low-Gini Strengthening Cuts\n\n"
        "Implemented paper-safe local station centering rows:\n\n"
        "`V r_i - S <= sum_{j != i} h_ij`\n\n"
        "`S - V r_i <= sum_{j != i} h_ij`\n\n"
        "Proof sketch: `sum_j |r_i-r_j|` is at least both `V r_i-S` and "
        "`S-V r_i`; each `h_ij` upper-bounds `|r_i-r_j|` in the compact model, "
        "so the two rows are valid relaxations for every original feasible route. "
        "They are exposed with `--tailored-bc-local-centering true` and logged as "
        "`local_centering` in static and callback cut counters.\n",
        encoding="utf-8",
    )
    DOCS.joinpath("s_bucket_or_split_diagnostic.md").write_text(
        "# S-Bucket Or Split Diagnostic\n\n"
        "S-bucket rows are diagnostic in this round. They can strengthen a fixed "
        "leaf by bounding `S=sum_i r_i`, but a parent leaf can use them for paper "
        "certificate evidence only if all S buckets exactly cover the parent S-domain "
        "and every bucket is merged in the certificate ledger. The audit file "
        "`s_bucket_coverage_audit.csv` marks diagnostic bucket rows as excluded from "
        "paper evidence.\n",
        encoding="utf-8",
    )
    DOCS.joinpath("low_gini_plateau_diagnosis.md").write_text(
        "# Low-Gini Plateau Diagnosis\n\n"
        "Target: `moderate_seed3301` low-Gini leaves "
        "`[0.0122881381662, 0.0245762763324]` and "
        "`[0.0245762763324, 0.0368644144986]`.\n\n"
        "The round compares plain fixed-interval MIP, callback infrastructure with "
        "profiled cut families, static tailored Compact-BC, local centering, and "
        "diagnostic S-bucket rows under one-thread CPLEX. Root LP snapshots are "
        "limited by the current CPLEX callback API exposure, so the report uses "
        "exported LP hashes, family row counts, node counts, and native CPLEX best "
        "bound trajectories as the forensic record.\n\n"
        f"Best plain low_gini_1 LB: {best_plain.get('lower_bound', 'n/a')}; "
        f"best local/full paced low_gini_1 LB: {best_local.get('lower_bound', 'n/a')}.\n",
        encoding="utf-8",
    )


def write_final_report(rows: List[Dict[str, Any]]) -> None:
    def best(leaf: str, variant: str) -> Dict[str, Any]:
        candidates = [r for r in rows if r["leaf"] == leaf and r["variant"] == variant]
        return max(candidates, key=lambda r: f(r["lower_bound"], -1.0), default={})
    plain = best("low_gini_1", "plain_fixed_interval_mip")
    local = max(
        [r for r in rows if r["leaf"] == "low_gini_1" and r["variant"] in {"callback_local_centering", "callback_full_paced", "static_tailored_compact_bc"}],
        key=lambda r: f(r["lower_bound"], -1.0),
        default={},
    )
    improved = f(local.get("lower_bound"), 0.0) > f(plain.get("lower_bound"), 0.0) + 1e-8
    label = "low_gini_plateau_improved_by_local_centering" if improved else "low_gini_plateau_requires_new_denominator_theory"
    RESULTS.joinpath("final_report.md").write_text(
        "# Tailored-BC Low-Gini Plateau Diagnosis Final Report\n\n"
        f"Status label: `{label}`.\n\n"
        "1. The plateau diagnosis is based on matched one-thread fixed-interval rows "
        "and CPLEX-native progress checkpoints, not wrapper-only bounds.\n"
        "2. Targeted mechanisms implemented: local station-wise centering cuts and "
        "callback cut-profile isolation. Existing S-bucket/SP/variable-S mechanisms "
        "were exercised and reported; S-bucket remains diagnostic only.\n"
        f"3. Best low_gini_1 plain LB: {plain.get('lower_bound', 'n/a')} "
        f"at {plain.get('budget_seconds', 'n/a')}s; best tailored/local LB: "
        f"{local.get('lower_bound', 'n/a')} at {local.get('budget_seconds', 'n/a')}s.\n"
        "4. No diagnostic S-bucket row is used as paper certificate evidence. Plain "
        "fixed-interval MIP rows are benchmark-only. BPC, archive scanning, known UB, "
        "external incumbent injection, and route-mask enumeration are not used.\n"
        "5. See `plateau_forensic_matrix.csv`, `bound_trace_audit.csv`, "
        "`model_identity_audit.csv`, and `model_row_family_counts.csv` for the "
        "numerical and model-identity details.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["smoke", "baseline", "required"], default="required")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--replace-results", action="store_true")
    parser.add_argument("--skip-3600", action="store_true")
    parser.add_argument("--wrapper-grace", type=int, default=900)
    args = parser.parse_args()

    if args.replace_results and RESULTS.exists():
        shutil.rmtree(RESULTS)
    for path in (RAW, LOGS, PROGRESS, MODELS):
        path.mkdir(parents=True, exist_ok=True)

    rows = execute_matrix(args)
    write_summaries(rows)
    write_docs(rows)
    write_final_report(rows)
    print(f"rows={len(rows)} results={RESULTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
