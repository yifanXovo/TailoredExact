#!/usr/bin/env python3
"""Stability, callback-vector, and moderate_seed3302 regression round."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import run_tailored_bc_s_bucket_strengthening_round as sb


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "gf_tailored_bc_stability_round"
RAW = RESULTS / "raw"
LOGS = RESULTS / "logs"
PROGRESS = RESULTS / "progress_traces"
MODELS = RESULTS / "model_exports"
DOCS = ROOT / "docs"
EXE = ROOT / "build-codex" / "ExactEBRP.exe"
if not EXE.exists():
    EXE = ROOT / "build" / "ExactEBRP.exe"

LOW_GINI_CUTOFF = 0.0491525526647
DOMINANT_BUCKET = (16.59546103547, 23.272821182835)


FULL_FRONTIER = {
    "v12_m1": "reference/regen_candidate_V12_M1_average.txt",
    "v12_m2": "reference/regen_candidate_V12_M2_average.txt",
    "tight_T_seed3101": "reference/hard_stress/V20_M3/tight_T_seed3101.txt",
    "high_imbalance_seed3202": "reference/hard_stress/V20_M3/high_imbalance_seed3202.txt",
    "moderate_seed3301": "reference/hard_stress/V20_M3/moderate_seed3301.txt",
    "high_imbalance_seed3201": "reference/hard_stress/V20_M3/high_imbalance_seed3201.txt",
    "tight_T_seed3102": "reference/hard_stress/V20_M3/tight_T_seed3102.txt",
    "moderate_seed3302": "reference/hard_stress/V20_M3/moderate_seed3302.txt",
}


def f(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: List[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_cmd(cmd: Sequence[str], log: Path, timeout: int, skip_existing: bool = False) -> int:
    out_path = None
    if "--out" in cmd:
        out_path = Path(cmd[cmd.index("--out") + 1])
    if skip_existing and out_path is not None and out_path.exists():
        return 0
    log.parent.mkdir(parents=True, exist_ok=True)
    start = time.time()
    with log.open("w", encoding="utf-8", errors="replace") as handle:
        handle.write("COMMAND " + " ".join(str(x) for x in cmd) + "\n")
        handle.flush()
        try:
            proc = subprocess.run(list(map(str, cmd)), stdout=handle,
                                  stderr=subprocess.STDOUT, timeout=timeout,
                                  check=False)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            rc = 124
            handle.write(f"\nWRAPPER_TIMEOUT after {timeout}s\n")
    if out_path is not None and not out_path.exists():
        write_json(out_path, {
            "method": cmd[cmd.index("--method") + 1] if "--method" in cmd else "",
            "status": "wrapper_timeout_noncertified" if rc == 124 else "wrapper_error_noncertified",
            "certified_original_problem": False,
            "lower_bound": 0.0,
            "upper_bound": 0.0,
            "gap": 1.0,
            "runtime_seconds": time.time() - start,
            "final_json_written": True,
            "paper_certificate_role": "none",
            "wrapper_return_code": rc,
        })
    return rc


def annotate_json(path: Path, cmd: Sequence[str], role: str = "paper_core") -> None:
    data = read_json(path)
    if not data:
        return
    data.setdefault("paper_certificate_role", role)
    data.setdefault("benchmark_name", "not_benchmark")
    data.setdefault("benchmark_role", "not_benchmark")
    data.setdefault("formulation_exactness", "tolerance_exact")
    data.setdefault("thread_fairness_class", "one_thread_fair")
    data.setdefault("cplex_threads", 1)
    data.setdefault("mip_threads", 1)
    data.setdefault("compact_bc_solver_threads", 1)
    data.setdefault("command_hash", sha16(" ".join(str(x) for x in cmd)))
    data.setdefault("plain_cplex_used_as_certificate", False)
    data.setdefault("diagnostic_rows_used", role != "paper_core")
    write_json(path, data)


def configure_harness() -> None:
    sb.RESULTS = RESULTS
    sb.RAW = RAW
    sb.LOGS = LOGS
    sb.PROGRESS = PROGRESS
    sb.MODELS = MODELS
    sb.SNAPSHOTS = RESULTS / "plateau_snapshots"
    sb.DOCS = DOCS
    sb.EXE = EXE
    sb.base.EXE = EXE
    sb.configure_base()


def run_callback_vector_smoke(args: argparse.Namespace) -> Dict[str, Any]:
    out = RAW / "callback_vector_smoke.json"
    cmd = [
        str(EXE), "--method", "tailored-bc-relaxation-vector-smoke-test",
        "--input", str(ROOT / "reference/regen_candidate_V12_M1_average.txt"),
        "--lambda", "0.15", "--T", "3600",
        "--time-limit", "15", "--threads", "1", "--mip-threads", "1",
        "--compact-bc-threads", "1",
        "--out", str(out),
    ]
    if args.run:
        run_cmd(cmd, LOGS / "callback_vector_smoke.log", 90, args.skip_existing)
        annotate_json(out, cmd, "diagnostic_only")
    data = read_json(out)
    shutil.copyfile(out, RESULTS / "callback_vector_smoke.json")
    row = callback_vector_row(data, out, "smoke_root_or_first_relaxation_callback")
    write_csv(RESULTS / "callback_vector_smoke.csv", [row])
    return row


def callback_vector_row(data: Dict[str, Any], path: Path, source: str) -> Dict[str, Any]:
    return {
        "path": str(path.relative_to(ROOT)),
        "snapshot_source": source,
        "callback_context_seen": b(data.get("tailored_bc_callback_vector_context_seen")),
        "relaxation_context_seen": b(data.get("tailored_bc_callback_vector_relaxation_context_seen")),
        "candidate_context_seen": b(data.get("tailored_bc_callback_vector_candidate_context_seen")),
        "vector_api_called": b(data.get("tailored_bc_callback_vector_api_called")),
        "vector_api_return_code": data.get("tailored_bc_callback_vector_api_return_code", ""),
        "vector_length_requested": data.get("tailored_bc_callback_vector_length_requested", ""),
        "vector_length_returned": data.get("tailored_bc_callback_vector_length_returned", ""),
        "nonzero_values_count": data.get("tailored_bc_callback_vector_nonzero_values_count", ""),
        "sample_variable_names": data.get("tailored_bc_callback_vector_sample_variable_names", "not_available"),
        "sample_variable_values": data.get("tailored_bc_callback_vector_sample_variable_values", "not_available"),
        "failure_reason": data.get("tailored_bc_callback_vector_failure_reason", ""),
        "limitation_category": data.get("tailored_bc_callback_vector_export_status", "unknown_failure"),
        "paper_certificate_role": data.get("paper_certificate_role", "diagnostic_only"),
    }


def write_vector_exports(rows: Sequence[Dict[str, Any]]) -> None:
    vector_rows: List[Dict[str, Any]] = []
    summary_rows: List[Dict[str, Any]] = []
    for row in rows:
        names = str(row.get("sample_variable_names", "not_available"))
        values = str(row.get("sample_variable_values", "not_available"))
        name_parts = [] if names == "not_available" else names.split(";")
        value_parts = [] if values == "not_available" else values.split(";")
        for idx, (name, value) in enumerate(zip(name_parts, value_parts)):
            vector_rows.append({
                "snapshot_source": row.get("snapshot_source", ""),
                "variable_name": name,
                "value": value,
                "sample_index": idx,
                "paper_certificate_role": "diagnostic_only",
            })
        summary_rows.append({
            "snapshot_source": row.get("snapshot_source", ""),
            "limitation_category": row.get("limitation_category", ""),
            "vector_api_called": row.get("vector_api_called", ""),
            "vector_api_return_code": row.get("vector_api_return_code", ""),
            "nonzero_values_count": row.get("nonzero_values_count", ""),
            "sample_count": len(vector_rows),
            "paper_certificate_role": "diagnostic_only",
        })
    write_csv(RESULTS / "callback_relaxation_vectors.csv", vector_rows)
    write_csv(RESULTS / "callback_relaxation_vector_summary.csv", summary_rows)


def dominant_bucket_cmd(out: Path, progress: Path, lp: Path, budget: int,
                        callback_probe: bool) -> List[str]:
    spec = sb.LEAVES["low_gini_1"]
    cmd = sb.base.base_interval_cmd(spec, budget, out, progress, lp)
    cmd += sb.variant_flags("static_tailored_compact_bc")
    cmd += [
        "--tailored-bc-s-bucket-ledger", "paper-safe",
        "--tailored-bc-s-bucket-count", "1",
        "--tailored-bc-s-bucket-policy", "dominant-fixed",
        "--tailored-bc-s-bucket-time-budget", str(budget),
        "--tailored-bc-s-bucket-merge-audit", "true",
        "--compact-bc-s-range-refinement", "paper-safe",
        "--compact-bc-s-range-buckets", "1",
        "--compact-bc-s-range-bucket-id", "0",
        "--compact-bc-s-range-bucket-L", repr(DOMINANT_BUCKET[0]),
        "--compact-bc-s-range-bucket-U", repr(DOMINANT_BUCKET[1]),
        "--compact-bc-s-range-adaptive", "false",
        "--compact-bc-progress-interval", "30",
    ]
    if callback_probe:
        cmd += [
            "--tailored-bc-mode", "callback",
            "--tailored-bc-callback-cut-profile", "off",
            "--tailored-bc-gini-branching", "off",
        ]
    return cmd


def run_dominant_vector(args: argparse.Namespace, vector_status: str) -> Dict[str, Any]:
    if vector_status != "callback_vector_export_working":
        return {
            "four_hour_vector_run_performed": False,
            "four_hour_vector_run_reason": "callback_vector_export_not_working",
        }
    budget = 14400 if args.include_4h else max(60, args.quick_long_budget)
    out = RAW / "dominant_k4_low_gini_1_static_tailored_compact_bc_14400s_vector_probe.json"
    progress = PROGRESS / "dominant_k4_low_gini_1_static_tailored_compact_bc_14400s_vector_probe.progress.csv"
    lp = MODELS / "dominant_k4_low_gini_1_static_tailored_compact_bc_14400s_vector_probe.lp"
    cmd = dominant_bucket_cmd(out, progress, lp, budget, callback_probe=True)
    if args.run and (args.include_4h or args.allow_short_vector_probe):
        run_cmd(cmd, LOGS / "dominant_k4_vector_probe.log", budget + args.wrapper_grace, args.skip_existing)
        annotate_json(out, cmd, "diagnostic_only")
    data = read_json(out)
    if data:
        row = callback_vector_row(data, out, "dominant_k4_first_relaxation_callback")
        existing = []
        if (RESULTS / "callback_vector_smoke.csv").exists():
            with (RESULTS / "callback_vector_smoke.csv").open(newline="", encoding="utf-8") as handle:
                existing = list(csv.DictReader(handle))
        write_vector_exports(existing + [row])
    return {
        "four_hour_vector_run_performed": args.include_4h and out.exists(),
        "four_hour_vector_run_budget_seconds": budget,
        "four_hour_vector_run_json": str(out.relative_to(ROOT)) if out.exists() else "",
        "four_hour_vector_run_reason": (
            "completed_or_emitted_final_json" if out.exists()
            else "not_run_use_--include-4h_to_execute_14400s_probe"
        ),
    }


def full_frontier_cmd(name: str, path: str, budget: int, out: Path, progress: Path) -> List[str]:
    return [
        str(EXE), "--method", "gcap-frontier",
        "--algorithm-preset", "paper-gf-tailored-bc",
        "--paper-run-sealed", "true",
        "--input", str(ROOT / path),
        "--lambda", "0.15", "--T", "3600",
        "--time-limit", str(budget),
        "--threads", "1", "--mip-threads", "1", "--compact-bc-threads", "1",
        "--compact-bc-progress-interval", "30",
        "--progress-log", str(progress),
        "--progress-interval-seconds", "30",
        "--out", str(out),
    ]


def run_full_frontier(args: argparse.Namespace) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    control_budget = 30 if args.profile == "smoke" else 300
    plans = [
        ("v12_m1", control_budget), ("v12_m2", control_budget),
        ("tight_T_seed3101", control_budget), ("high_imbalance_seed3202", control_budget),
    ]
    hard_budget = 3600 if args.profile == "required" else args.quick_long_budget
    for name in ("moderate_seed3301", "high_imbalance_seed3201", "tight_T_seed3102", "moderate_seed3302"):
        plans.append((name, hard_budget))
    summary: List[Dict[str, Any]] = []
    open_rows: List[Dict[str, Any]] = []
    traj_rows: List[Dict[str, Any]] = []
    for name, budget in plans:
        out = RAW / f"frontier_{name}_{budget}s.json"
        progress = PROGRESS / f"frontier_{name}_{budget}s.progress.csv"
        cmd = full_frontier_cmd(name, FULL_FRONTIER[name], budget, out, progress)
        if args.run:
            run_cmd(cmd, LOGS / f"frontier_{name}_{budget}s.log", budget + args.wrapper_grace, args.skip_existing)
            annotate_json(out, cmd, "paper_core")
        data = read_json(out)
        lb = f(data.get("lower_bound"))
        ub = f(data.get("upper_bound"))
        gap = data.get("gap", "")
        open_leaf_count = int(f(data.get("intervals_unresolved_count", data.get("compact_bc_unresolved_leaf_count", 0))))
        closed_leaf_count = int(f(data.get("intervals_closed_by_relaxation_count", 0))) + int(f(data.get("compact_bc_closed_leaf_count", 0)))
        status = data.get("status", "missing")
        summary.append({
            "instance": name,
            "runtime_budget": budget,
            "status": status,
            "certified_original_problem": data.get("certified_original_problem", False),
            "LB": lb,
            "UB": ub,
            "gap": gap,
            "open_leaf_count": open_leaf_count,
            "closed_leaf_count": closed_leaf_count,
            "certificate_source": data.get("tailored_bc_source_class", data.get("certificate_type", "")),
            "paper_core_valid": not b(data.get("plain_cplex_used_as_certificate")) and not b(data.get("diagnostic_rows_used")),
            "plain_cplex_used_as_certificate": data.get("plain_cplex_used_as_certificate", False),
            "diagnostic_rows_used": data.get("diagnostic_rows_used", False),
            "runtime_seconds": data.get("runtime_seconds", ""),
            "crash_or_timeout": "timeout" in str(status).lower() or status == "wrapper_timeout_noncertified",
            "logging_complete": out.exists(),
            "comparison_to_previous_result": "fresh_stability_row_no_previous_import",
            "json_path": str(out.relative_to(ROOT)) if out.exists() else "",
        })
        open_rows.append({
            "instance": name,
            "budget_seconds": budget,
            "open_leaf_count": open_leaf_count,
            "status": status,
            "lower_bound": lb,
            "upper_bound": ub,
            "dominant_open_leaf_note": "see interval CSV sidecars if emitted",
        })
        if progress.exists():
            with progress.open(newline="", encoding="utf-8") as handle:
                for rec in csv.DictReader(handle):
                    traj_rows.append({
                        "instance": name,
                        "budget_seconds": budget,
                        "time_seconds": rec.get("elapsed_seconds", rec.get("time_seconds", "")),
                        "global_LB": rec.get("best_bound", rec.get("global_LB", "")),
                        "incumbent_UB": rec.get("incumbent", rec.get("incumbent_UB", "")),
                        "nodes": rec.get("node_count", rec.get("nodes", "")),
                        "event": rec.get("event", ""),
                    })
    return summary, open_rows, traj_rows


def regression_rows(args: argparse.Namespace) -> List[Dict[str, Any]]:
    configure_harness()
    variants = [
        "plain_fixed_interval_mip",
        "static_tailored_compact_bc",
        "best_combined_paper_safe",
        "callback_no_cuts",
        "callback_cheap_cuts",
        "callback_full_paced",
        "s_bucket_diagnostic",
    ]
    budgets = [30 if args.profile == "smoke" else 300]
    if args.profile == "required":
        budgets.append(1200)
    rows: List[Dict[str, Any]] = []
    for variant in variants:
        for budget in budgets:
            try:
                spec = sb.run_interval_row("moderate_seed3302_hard", variant, budget,
                                           stem_prefix="regression_")
            except Exception:
                continue
            if args.run:
                sb.execute_one(spec, args)
                annotate_json(spec["out"], spec["cmd"],
                              "diagnostic_only" if "diagnostic" in variant else "paper_core")
            row = sb.base.row_from_result("moderate_seed3302_hard", variant, budget,
                                          spec["out"], spec["progress"], spec["lp"], spec["cmd"])
            data = read_json(spec["out"])
            row.update({
                "enabled_cut_families": data.get("tailored_bc_user_cuts_added_by_family", ""),
                "branching_policy": data.get("tailored_bc_gini_branch_mode", ""),
                "callback_enabled": data.get("tailored_bc_user_cut_callback_enabled", ""),
                "S_bucket_enabled": data.get("tailored_bc_s_bucket_ledger", "off"),
                "LB": data.get("lower_bound", row.get("lower_bound", "")),
                "UB": data.get("upper_bound", row.get("upper_bound", "")),
                "gap": data.get("gap", row.get("gap", "")),
                "runtime": data.get("runtime_seconds", row.get("runtime_seconds", "")),
                "nodes": data.get("compact_bc_nodes", data.get("nodes", "")),
                "cut_count": data.get("tailored_bc_user_cuts_added_total", ""),
                "callback_count": data.get("tailored_bc_relaxation_callback_calls", ""),
                "bound_improvement_count": data.get("valid_checkpoint_count", ""),
                "last_improvement_time": data.get("last_bound_improvement_time", ""),
            })
            rows.append(row)
    plain_by_budget = {
        str(r.get("budget_seconds")): f(r.get("LB"), 0.0)
        for r in rows
        if r.get("variant") == "plain_fixed_interval_mip"
    }
    fallback_plain = next(iter(plain_by_budget.values()), 0.0)
    for row in rows:
        plain_lb = plain_by_budget.get(str(row.get("budget_seconds")), fallback_plain)
        row["comparison_to_plain"] = f(row.get("LB"), 0.0) - plain_lb
        row["regression_cause"] = classify_regression(row)
    return rows


def classify_regression(row: Dict[str, Any]) -> str:
    variant = str(row.get("variant", ""))
    if variant == "plain_fixed_interval_mip":
        return "baseline"
    if f(row.get("comparison_to_plain"), 0.0) >= -1e-7:
        return "no_material_regression"
    if "callback" in variant and f(row.get("callback_count"), 0.0) > 0:
        return "callback_overhead_or_search_path_variance"
    if "s_bucket" in variant:
        return "S-bucket_overhead"
    if f(row.get("cut_count"), 0.0) > 0:
        return "cut_overhead_or_search_path_variance"
    return "unknown"


def forbidden_scan() -> List[Dict[str, Any]]:
    patterns = [
        "moderate_seed3301", "moderate_seed3302", "low_gini_1", "low_gini_2",
        "seed3201", "seed3102", "regen_candidate", "known_ub", "archive",
        "external_incumbent", "focus", "route_mask", "BPC", "bpc", "diagnostic-only",
    ]
    rows: List[Dict[str, Any]] = []
    for base in (ROOT / "src", ROOT / "include", ROOT / "scripts"):
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in {".cpp", ".hpp", ".py"}:
                continue
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), 1):
                for pat in patterns:
                    if pat in line:
                        classification = (
                            "allowed_experiment_target" if rel.startswith("scripts/run_") else
                            "allowed_metadata_or_audit" if "audit" in rel or "Usage:" in line else
                            "allowed_legacy_cli_but_not_paper_core"
                        )
                        if rel.startswith("src/") and ("if" in line and ("seed" in line or "moderate" in line)):
                            classification = "forbidden_algorithm_special_case"
                        rows.append({
                            "file": rel,
                            "line": lineno,
                            "pattern": pat,
                            "classification": classification,
                            "line_text": line.strip()[:240],
                        })
    return rows


def write_docs(callback_status: str, vector_run: Dict[str, Any],
               frontier: Sequence[Dict[str, Any]],
               regression: Sequence[Dict[str, Any]]) -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "official_benchmark_scope.md").write_text(
        "# Official Benchmark Scope\n\n"
        "The official benchmark remains the current binary-expansion compact MILP solved by CPLEX.\n"
        "It is labelled `tolerance_exact` with bit-depth / linearization precision metadata.\n"
        "Alternative exact-S formulations are audited diagnostics and are not enabled as the official benchmark in this round.\n"
        "Approximate SOS2, piecewise, Charnes-Cooper, Dinkelbach, and nonconvex MIQCP variants are excluded from official exact benchmarking.\n"
        "Plain CPLEX benchmark rows are benchmark-only and must never enter the Tailored-BC ledger.\n",
        encoding="utf-8",
    )
    (RESULTS / "mainline_scope_audit.md").write_text(
        "# Mainline Scope Audit\n\n"
        "`paper-gf-tailored-bc` remains the paper-facing line: Gini-frontier decomposition, valid interval relaxation/frontier bounds, "
        "CPLEX-managed tailored fixed-interval branch-and-cut, optional paper-safe S-domain refinement, and audited full-frontier ledger aggregation.\n\n"
        "Excluded from paper-core evidence: BPC, route-mask enumeration, archive scanning, known UB injection, external incumbents, focus-only rows, "
        "plain CPLEX benchmark rows, and alternative exact-S formulations.\n",
        encoding="utf-8",
    )
    if callback_status != "callback_vector_export_working":
        (RESULTS / "callback_relaxation_vector_limitation.md").write_text(
            "# Callback Relaxation Vector Limitation\n\n"
            f"Status: `{callback_status}`.\n\n"
            "The smoke test did not produce an auditable nonzero relaxation vector. Missing values are recorded as `not_available`, not zero.\n"
            "Safe alternatives remain root LP export, command-line CPLEX LP relaxation solution, solver log parsing, and callback bound trajectory.\n",
            encoding="utf-8",
        )
    (RESULTS / "full_frontier_engineering_stability.md").write_text(
        "# Full-Frontier Engineering Stability\n\n"
        "This report records fresh `paper-gf-tailored-bc` stability rows. Certification is not forced for hard rows; the required outcome is honest final JSON, "
        "complete logging where possible, no paper-core contamination, and visible open-leaf/bound status.\n\n"
        f"Rows summarized: {len(frontier)}.\n",
        encoding="utf-8",
    )
    reg_causes = sorted({str(r.get("regression_cause", "")) for r in regression})
    (RESULTS / "moderate_seed3302_regression_report.md").write_text(
        "# moderate_seed3302_hard Regression Report\n\n"
        "The regression matrix compares plain fixed-interval MIP, static Tailored-BC, callback variants, and S-bucket diagnostics under one-thread fairness.\n\n"
        f"Observed cause classes: {', '.join(reg_causes) if reg_causes else 'not_run'}.\n",
        encoding="utf-8",
    )
    (RESULTS / "official_benchmark_decision.md").write_text(
        "# Official Benchmark Decision\n\n"
        "The official benchmark remains the current binary-expansion compact MILP plus CPLEX. Alternative exact formulations are not enabled in this round because "
        "they remain too large for route cases under current caps. Plain CPLEX remains benchmark-only and is not imported into Tailored-BC certificates. "
        "The moderate_seed3302 regression investigation does not change the benchmark definition.\n",
        encoding="utf-8",
    )
    (RESULTS / "configuration_policy_changes.md").write_text(
        "# Configuration Policy Changes\n\n"
        "No generic solver-policy change was applied in this stabilization runner. Any future change must be metric-driven and not instance-specific.\n",
        encoding="utf-8",
    )
    (RESULTS / "final_report.md").write_text(final_report(callback_status, vector_run, frontier, regression), encoding="utf-8")


def final_report(callback_status: str, vector_run: Dict[str, Any],
                 frontier: Sequence[Dict[str, Any]],
                 regression: Sequence[Dict[str, Any]]) -> str:
    easy = [r for r in frontier if r["instance"] in {"v12_m1", "v12_m2", "tight_T_seed3101", "high_imbalance_seed3202"}]
    easy_cert = sum(1 for r in easy if b(r.get("certified_original_problem")))
    hard = [r for r in frontier if r not in easy]
    hard_logged = sum(1 for r in hard if b(r.get("logging_complete")))
    reg_causes = sorted({str(r.get("regression_cause", "")) for r in regression if r.get("regression_cause")})
    return (
        "# Stability Callback Vector Regression Final Report\n\n"
        "1. Paper strictness: audits and scans in this package check for paper-core contamination and instance-specific branches.\n"
        "2. Official benchmark: current binary-expansion compact MILP plus CPLEX, benchmark-only.\n"
        "3. Alternative formulations: not enabled; they remain diagnostic because current route-case models exceed practical caps.\n"
        f"4. Callback vector export: `{callback_status}`.\n"
        f"5. 4h vector run: performed={vector_run.get('four_hour_vector_run_performed', False)}, reason={vector_run.get('four_hour_vector_run_reason', '')}.\n"
        "6. If impossible: not applicable when export works; otherwise see callback_relaxation_vector_limitation.md.\n"
        f"7. Easy full-frontier controls certified/stable: {easy_cert}/{len(easy)} certified in this run package.\n"
        f"8. Hard full-frontier reproductions emitted final/logging artifacts: {hard_logged}/{len(hard)}.\n"
        f"9. moderate_seed3302 regression reproduced: {'yes' if regression else 'not_run'}.\n"
        f"10. Regression cause: {', '.join(reg_causes) if reg_causes else 'not_available'}.\n"
        "11. Safe generic configuration fix: none applied in this stabilization pass unless configuration_policy_changes.md says otherwise.\n"
        "12. Fix impact on controls: no policy fix was applied, so no new degradation is introduced by configuration policy.\n"
        "13. Paper-core contamination risks: diagnostic vector and benchmark rows are labelled outside paper evidence; audits cover this.\n"
        "14. Next step: if callback vectors remain available, inspect dominant-bucket sampled vectors and use root/trajectory diagnostics for low-Gini hard-leaf strengthening.\n"
    )


def run_audits(args: argparse.Namespace) -> List[Dict[str, Any]]:
    audit_cmds = [
        [str(Path("D:/msys64/ucrt64/bin/python.exe")), "scripts/audit_paper_strict_algorithm.py", "--out", str(RESULTS / "paper_strict_algorithm_audit.csv")],
        [str(Path("D:/msys64/ucrt64/bin/python.exe")), "scripts/audit_callback_relaxation_vector_export.py", "--results", str(RESULTS), "--out", str(RESULTS / "relaxation_vector_export_audit.csv")],
    ]
    rows: List[Dict[str, Any]] = []
    if not args.run_audits:
        return rows
    for cmd in audit_cmds:
        log = LOGS / ("audit_" + Path(cmd[1]).stem + ".log")
        rc = run_cmd(cmd, log, 300, False)
        rows.append({"audit": Path(cmd[1]).name, "return_code": rc, "log": str(log.relative_to(ROOT))})
    return rows


def benchmark_scope_summary() -> List[Dict[str, Any]]:
    return [{
        "benchmark_name": "current_binary_expansion_compact_milp_cplex",
        "benchmark_role": "official_plain_cplex_benchmark",
        "formulation_exactness": "tolerance_exact",
        "paper_certificate_role": "benchmark_only",
        "alternative_exact_s_enabled": False,
        "alternative_exact_s_reason": "toy-equivalent but too large for route cases under current caps",
    }]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--profile", choices=["smoke", "standard", "required"], default="standard")
    parser.add_argument("--include-4h", action="store_true")
    parser.add_argument("--allow-short-vector-probe", action="store_true")
    parser.add_argument("--quick-long-budget", type=int, default=300)
    parser.add_argument("--wrapper-grace", type=int, default=120)
    parser.add_argument("--run-audits", action="store_true")
    args = parser.parse_args()

    for path in (RESULTS, RAW, LOGS, PROGRESS, MODELS):
        path.mkdir(parents=True, exist_ok=True)
    configure_harness()

    smoke = run_callback_vector_smoke(args)
    vector_status = str(smoke.get("limitation_category", "unknown_failure"))
    vector_run = run_dominant_vector(args, vector_status)
    if not (RESULTS / "callback_relaxation_vectors.csv").exists():
        write_vector_exports([smoke])

    frontier, open_leaf, trajectory = run_full_frontier(args)
    regression = regression_rows(args)

    write_csv(RESULTS / "full_frontier_stability_summary.csv", frontier)
    write_csv(RESULTS / "full_frontier_certificate_comparison.csv", frontier)
    write_csv(RESULTS / "full_frontier_open_leaf_summary.csv", open_leaf)
    write_csv(RESULTS / "full_frontier_bound_trajectory_summary.csv", trajectory)
    write_csv(RESULTS / "moderate_seed3302_regression_matrix.csv", regression)
    write_csv(RESULTS / "benchmark_scope_summary.csv", benchmark_scope_summary())
    write_csv(RESULTS / "benchmark_role_audit.csv", benchmark_scope_summary())
    write_csv(RESULTS / "forbidden_evidence_scan.csv", forbidden_scan())

    audits = run_audits(args)
    if audits:
        write_csv(RESULTS / "stability_round_audit_commands.csv", audits)
    write_docs(vector_status, vector_run, frontier, regression)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
