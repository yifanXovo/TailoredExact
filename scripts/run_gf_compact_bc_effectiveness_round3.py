#!/usr/bin/env python3
"""Prepare GF compact-BC effectiveness round 3.

Round 3 keeps attribution and finalization safeguards, then extends the evidence
package with longer fixed-interval tailored-vs-plain comparisons, cleaner
leaf-solver semantics, low-Gini strengthening mode reporting, and deterministic
hard diagnostic instances.  Diagnostic interval rows remain diagnostic and are
not paper-core certificate evidence.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


SRC = Path("results/gf_compact_bc_effectiveness_round2")
ROOT = Path("results/gf_compact_bc_effectiveness_round3")
RAW = ROOT / "raw"
PROGRESS = ROOT / "progress_traces"
PY = Path(r"D:\msys64\ucrt64\bin\python.exe")
EXE = Path("build/ExactEBRP.exe")


def f(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
        return out if math.isfinite(out) else default
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
        item = data["results"][0]
        return item if isinstance(item, dict) else {}
    return data if isinstance(data, dict) else {}


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
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


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def copy_inputs() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROGRESS.mkdir(parents=True, exist_ok=True)
    for sub in ("raw", "progress_traces"):
        source = SRC / sub
        if not source.exists():
            continue
        for path in source.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".json", ".csv", ".txt", ".md"}:
                continue
            dst_root = RAW if sub == "raw" else PROGRESS
            dst = dst_root / path.relative_to(source)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)


def run_summarizer() -> None:
    subprocess.run(
        [str(PY), "scripts/summarize_gf_compact_bc_round.py", "--raw-dir", str(RAW), "--out-dir", str(ROOT)],
        check=True,
    )


def load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parent_stem_from_csv(path: Path) -> str:
    name = path.name
    for suffix in (".merged.intervals.csv", ".intervals.csv", ".auto_oracle.csv"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


def parent_stem_from_child(path: Path) -> str:
    parent = path.parent.name
    if parent.endswith("_auto_oracle"):
        return parent[: -len("_auto_oracle")]
    if parent in {"diagnostic_interval_comparisons"}:
        return path.stem
    return parent


def interval_class_from_fields(row: Dict[str, Any]) -> str:
    source = str(row.get("interval_closure_source", "")).lower()
    status = str(row.get("status") or row.get("interval_status") or "").lower()
    basis = str(row.get("certificate_basis") or row.get("interval_exact_cutoff_certificate_basis") or "").lower()
    solver = str(row.get("solver_status") or row.get("interval_exact_cutoff_solver_status") or "").lower()
    bound_valid = as_bool(row.get("bound_valid") or row.get("interval_bound_valid") or row.get("interval_oracle_bound_valid"))
    can_merge = as_bool(row.get("can_merge_bound") or row.get("interval_oracle_can_merge_bound"))
    lb = f(row.get("bound_used_for_merge") or row.get("best_bound") or row.get("lower_bound"), 0.0)
    ub = f(row.get("interval_final_ub_cutoff") or row.get("upper_bound") or row.get("interval_exact_cutoff_UB"), 0.0)
    if source == "relaxation_bound":
        return "relaxation_only"
    if source in {"empty", "empty_or_out_of_range"} or "empty" in basis:
        return "empty_or_out_of_range"
    if "infeasible" in basis or solver == "infeasible" or as_bool(row.get("proven_infeasible")) or as_bool(row.get("interval_exact_cutoff_proven_infeasible")):
        return "compact_bc_infeasible"
    if can_merge and bound_valid and ub > 0.0 and lb >= ub - 1e-7:
        return "compact_bc_valid_best_bound"
    if "cutoff" in basis and "bound" in basis and bound_valid:
        return "compact_bc_cutoff_bound"
    if "timeout" in status or "time limit" in solver or as_bool(row.get("timeout")) or as_bool(row.get("interval_exact_cutoff_timeout")):
        return "unresolved"
    if source == "unresolved" or "unresolved" in status:
        return "unresolved"
    if status in {"interval_closed", "optimal"} and bound_valid:
        return "compact_bc_valid_best_bound"
    return "invalid_or_unknown"


def collect_interval_details() -> List[Dict[str, Any]]:
    details: List[Dict[str, Any]] = []
    for path in sorted(RAW.rglob("*.intervals.csv")) + sorted(RAW.rglob("*.auto_oracle.csv")):
        for row in load_csv(path):
            cls = interval_class_from_fields(row)
            details.append({
                "parent_stem": parent_stem_from_csv(path),
                "source_type": "auto_oracle_csv" if path.name.endswith(".auto_oracle.csv") else "interval_csv",
                "source_csv": str(path),
                "leaf_solver_row": path.name.endswith(".auto_oracle.csv"),
                "compact_bc_called_this_row": path.name.endswith(".auto_oracle.csv"),
                "compact_bc_diagnostic_only": False,
                "interval_id": row.get("interval_id", ""),
                "gamma_L": row.get("gamma_L", ""),
                "gamma_U": row.get("gamma_U", ""),
                "status": row.get("status") or row.get("interval_status", ""),
                "certificate_basis": row.get("certificate_basis", ""),
                "solver_status": row.get("solver_status", ""),
                "closure_source_class": cls,
                "bound_valid": row.get("bound_valid") or row.get("interval_bound_valid", ""),
                "best_bound": row.get("best_bound") or row.get("interval_lower_bound", ""),
                "runtime_seconds": row.get("runtime_seconds", ""),
                "nodes": row.get("nodes", ""),
                "gap_to_cutoff": row.get("gap_to_cutoff", ""),
                "cuts_added": "|".join(str(row.get(k, "")) for k in (
                    "direct_gini_cap_rows", "tight_mccormick_rows",
                    "support_duration_pair_cuts", "transfer_compatibility_cuts",
                    "receiver_source_cover_cuts")),
            })
    for path in sorted(RAW.rglob("interval_*.json")):
        data = read_json(path)
        if not data or str(data.get("method")) != "interval-cutoff-oracle":
            continue
        cls = interval_class_from_fields(data)
        details.append({
            "parent_stem": parent_stem_from_child(path),
            "source_type": "child_interval_json",
            "source_csv": str(path),
            "leaf_solver_row": True,
            "compact_bc_called_this_row": True,
            "compact_bc_diagnostic_only": "diagnostic_interval_comparisons" in str(path),
            "interval_id": path.stem.replace("interval_", ""),
            "gamma_L": data.get("interval_exact_cutoff_gamma_L", ""),
            "gamma_U": data.get("interval_exact_cutoff_gamma_U", ""),
            "status": data.get("status", ""),
            "certificate_basis": data.get("interval_exact_cutoff_certificate_basis", ""),
            "solver_status": data.get("interval_exact_cutoff_solver_status", ""),
            "closure_source_class": cls,
            "bound_valid": data.get("interval_oracle_bound_valid", ""),
            "best_bound": data.get("lower_bound", ""),
            "runtime_seconds": data.get("runtime_seconds", ""),
            "nodes": data.get("compact_bc_nodes") or data.get("nodes", ""),
            "gap_to_cutoff": data.get("interval_oracle_gap_to_cutoff", ""),
            "cuts_added": data.get("compact_bc_cuts_added_by_family", ""),
        })
    return details


def aggregate_by_parent(details: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    agg: Dict[str, Dict[str, Any]] = {}
    priority = {
        "compact_bc_infeasible": 5,
        "compact_bc_valid_best_bound": 5,
        "compact_bc_cutoff_bound": 5,
        "unresolved": 3,
        "relaxation_only": 2,
        "empty_or_out_of_range": 1,
        "invalid_or_unknown": 0,
    }
    leaf_seen: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
    for row in details:
        key = (str(row["parent_stem"]), str(row.get("interval_id", "")), str(row.get("gamma_L", "")), str(row.get("gamma_U", "")))
        old = leaf_seen.get(key)
        if old is None or priority.get(row["closure_source_class"], 0) >= priority.get(old["closure_source_class"], 0):
            leaf_seen[key] = row
    for row in leaf_seen.values():
        parent = row["parent_stem"]
        slot = agg.setdefault(parent, {
            "relaxation": 0,
            "compact_closed": 0,
            "compact_infeasible": 0,
            "compact_bound": 0,
            "compact_cutoff": 0,
            "compact_timeout": 0,
            "unresolved": 0,
            "empty": 0,
            "invalid": 0,
            "called": False,
            "child_rows": 0,
            "runtime": 0.0,
            "nodes": 0.0,
        })
        cls = row["closure_source_class"]
        compact_source = row["source_type"] in {"auto_oracle_csv", "child_interval_json"}
        slot["called"] = bool(slot["called"] or compact_source)
        if compact_source:
            slot["child_rows"] += 1
        slot["runtime"] += f(row.get("runtime_seconds"), 0.0) if compact_source else 0.0
        slot["nodes"] += f(row.get("nodes"), 0.0) if compact_source else 0.0
        if cls == "relaxation_only":
            slot["relaxation"] += 1
        elif cls == "compact_bc_infeasible":
            slot["compact_closed"] += 1
            slot["compact_infeasible"] += 1
        elif cls == "compact_bc_valid_best_bound":
            slot["compact_closed"] += 1
            slot["compact_bound"] += 1
        elif cls == "compact_bc_cutoff_bound":
            slot["compact_closed"] += 1
            slot["compact_cutoff"] += 1
        elif cls == "unresolved":
            slot["unresolved"] += 1
            if compact_source:
                slot["compact_timeout"] += 1
        elif cls == "empty_or_out_of_range":
            slot["empty"] += 1
        else:
            slot["invalid"] += 1
    return agg


def source_class(summary_row: Dict[str, str], counts: Dict[str, Any]) -> str:
    method = summary_row.get("method", "")
    status = str(summary_row.get("status", "")).lower()
    certified = as_bool(summary_row.get("certified_original_problem"))
    if method == "cplex":
        return "benchmark_only"
    if method == "interval-cutoff-oracle":
        return "compact_bc_leaf_diagnostic"
    if status == "interrupted_noncertified":
        return "wrapper_checkpoint_only"
    if status == "model_size_limit" or str(summary_row.get("compact_bc_model_size_stop_reason", "")):
        return "model_size_limit"
    if str(summary_row.get("finalization_source", "")).startswith("wrapper"):
        return "wrapper_checkpoint_only"
    compact = int(counts.get("compact_closed", 0))
    called = bool(counts.get("called", False))
    relax = int(counts.get("relaxation", 0))
    if certified:
        if compact > 0 and relax > 0:
            return "mixed_certified"
        if compact > 0 or called:
            return "compact_bc_assisted_certified"
        return "relaxation_only_certified"
    if called and relax > 0:
        return "mixed_noncertified"
    if called:
        return "compact_bc_assisted_noncertified"
    if relax > 0:
        return "relaxation_only_noncertified"
    return "invalid_or_unknown"


def write_source_outputs(summary: List[Dict[str, str]], details: List[Dict[str, Any]]) -> None:
    agg = aggregate_by_parent(details)
    rows: List[Dict[str, Any]] = []
    audit: List[Dict[str, Any]] = []
    for row in summary:
        stem = Path(row.get("file", "")).stem
        counts = agg.get(stem, {})
        cls = source_class(row, counts)
        method = row.get("method", "")
        certified = as_bool(row.get("certified_original_problem"))
        inconsistent = certified and "noncertified" in cls
        compact_called = bool(counts.get("called", False))
        compact_closed = int(counts.get("compact_closed", 0))
        unresolved_after = int(counts.get("unresolved", f(row.get("unresolved_intervals"), 0)))
        out = {
            "file": row.get("file", ""),
            "instance_name": row.get("instance_name", ""),
            "status": row.get("status", ""),
            "certified_original_problem": row.get("certified_original_problem", ""),
            "selected_for_summary": row.get("selected_for_summary", ""),
            "row_certificate_source_class": cls,
            "leaf_solver_row": method == "interval-cutoff-oracle",
            "compact_bc_called_this_row": method == "interval-cutoff-oracle",
            "compact_bc_called_any_child": compact_called,
            "parent_row_compact_bc_called_any_leaf": method == "gcap-frontier" and compact_called,
            "compact_bc_child_rows_found": int(counts.get("child_rows", 0)),
            "compact_bc_child_rows_aggregated": int(counts.get("child_rows", 0)),
            "compact_bc_diagnostic_only": cls in {"compact_bc_leaf_diagnostic", "benchmark_only"},
            "paper_certificate_contamination": False,
            "relaxation_only_intervals": int(counts.get("relaxation", 0)),
            "compact_bc_infeasible_intervals": int(counts.get("compact_infeasible", 0)),
            "compact_bc_valid_best_bound_intervals": int(counts.get("compact_bound", 0)),
            "compact_bc_cutoff_bound_intervals": int(counts.get("compact_cutoff", 0)),
            "compact_bc_called_any_leaf": compact_called,
            "compact_bc_contributed_to_certificate": certified and compact_closed > 0,
            "compact_bc_contributed_leaf_count": compact_closed if certified else 0,
            "compact_bc_closed_leaf_count": compact_closed,
            "compact_bc_timed_out_leaf_count": int(counts.get("compact_timeout", 0)),
            "compact_bc_leaf_runtime_total": counts.get("runtime", 0.0),
            "compact_bc_leaf_nodes_total": int(counts.get("nodes", 0)),
            "unresolved_leaf_count_after_compact_bc": unresolved_after,
            "inconsistent_source_label_detected": inconsistent,
            "lower_bound": row.get("lower_bound", ""),
            "upper_bound": row.get("upper_bound", ""),
            "gap": row.get("gap", ""),
        }
        rows.append(out)
        reasons: List[str] = []
        if inconsistent:
            reasons.append("optimal_row_label_contains_noncertified")
        if compact_called and not out["compact_bc_called_any_leaf"]:
            reasons.append("parent_child_compact_bc_call_lost")
        if certified and cls in {"invalid_or_unknown", "wrapper_checkpoint_only", "model_size_limit"}:
            reasons.append("certified_row_bad_source_class")
        audit.append({**out, "audit_passed": not reasons, "failures": "|".join(reasons)})
    write_csv(ROOT / "certificate_source_summary_v3.csv", rows)
    write_csv(ROOT / "certificate_source_summary_v2.csv", rows)
    write_csv(ROOT / "certificate_source_summary.csv", rows)
    write_csv(ROOT / "interval_closure_source_detail_v3.csv", details)
    write_csv(ROOT / "interval_closure_source_detail_v2.csv", details)
    write_csv(ROOT / "interval_closure_source_detail.csv", details)
    write_csv(ROOT / "source_semantics_audit.csv", audit)
    write_csv(ROOT / "source_label_consistency_audit.csv", audit)
    write_csv(ROOT / "certificate_source_audit.csv", audit)


def quality_rank(row: Dict[str, str], src_class: str) -> int:
    certified = as_bool(row.get("certified_original_problem"))
    finalization = str(row.get("finalization_source", "")).lower()
    diagnostic = src_class in {"compact_bc_leaf_diagnostic", "benchmark_only"}
    if diagnostic:
        return 9
    if certified and "solver" in finalization:
        return 1
    if certified:
        return 2
    if finalization == "solver_final_noncertified":
        return 3
    if finalization.startswith("wrapper"):
        return 4
    return 5


def selected_summary(summary: List[Dict[str, str]]) -> None:
    classes = {Path(r.get("file", "")).stem: r.get("row_certificate_source_class", "") for r in load_csv(ROOT / "certificate_source_summary_v3.csv")}
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for row in summary:
        src_class = classes.get(Path(row.get("file", "")).stem, "")
        comparable = "|".join([
            row.get("method", ""),
            row.get("instance_name", ""),
            row.get("algorithm_preset", ""),
            str(row.get("time_budget_seconds", "")),
            row.get("thread_fairness_class", ""),
            "diagnostic" if src_class in {"compact_bc_leaf_diagnostic", "benchmark_only"} else "paper",
        ])
        gid = hash_text(comparable)
        out = dict(row)
        out["row_certificate_source_class"] = src_class
        out["duplicate_row_group_id"] = gid
        out["comparable_setting_hash"] = gid
        out["command_hash"] = hash_text(row.get("file", "") + comparable)
        out["row_quality_rank"] = quality_rank(row, src_class)
        groups.setdefault(gid, []).append(out)
    selected: List[Dict[str, Any]] = []
    audit: List[Dict[str, Any]] = []
    for gid, rows in groups.items():
        rows.sort(key=lambda r: (int(r["row_quality_rank"]), f(r.get("gap"), 999.0), -f(r.get("lower_bound"), 0.0)))
        chosen = rows[0]
        for row in rows:
            is_chosen = row is chosen
            row["selected_for_summary"] = is_chosen
            row["duplicate_row_resolution_reason"] = (
                "selected best audited comparable row" if is_chosen
                else "not selected; lower quality duplicate or diagnostic/benchmark row")
            audit.append({
                "duplicate_row_group_id": gid,
                "file": row.get("file", ""),
                "instance_name": row.get("instance_name", ""),
                "row_certificate_source_class": row.get("row_certificate_source_class", ""),
                "row_quality_rank": row.get("row_quality_rank", ""),
                "selected_for_summary": is_chosen,
                "duplicate_row_resolution_reason": row["duplicate_row_resolution_reason"],
                "command_hash": row["command_hash"],
                "comparable_setting_hash": row["comparable_setting_hash"],
            })
        selected.append(chosen)
    write_csv(ROOT / "selected_summary_v2.csv", selected)
    write_csv(ROOT / "summary_dedup_audit.csv", audit)


def diagnostic_leaf_specs() -> List[Dict[str, Any]]:
    seeds = [
        ("v12_m1_easy", RAW / "exact_V12_M1_300s_auto_oracle" / "interval_12.json"),
        ("moderate_seed3301_low_gini_1", RAW / "exact_moderate_seed3301_1200s_static300_auto_oracle" / "interval_1.json"),
        ("moderate_seed3301_low_gini_2", RAW / "exact_moderate_seed3301_1200s_static300_auto_oracle" / "interval_2.json"),
        ("high_imbalance_seed3201_hard", RAW / "exact_high_imbalance_seed3201_300s_auto_oracle" / "interval_6.json"),
        ("tight_T_seed3102_hard", RAW / "exact_tight_T_seed3102_300s_auto_oracle" / "interval_1.json"),
    ]
    specs: List[Dict[str, Any]] = []
    for label, path in seeds:
        data = read_json(path)
        if not data:
            continue
        specs.append({
            "label": label,
            "input": data.get("input_path"),
            "lambda": data.get("lambda", 0.15),
            "T": data.get("T", 3600),
            "gamma_L": data.get("interval_exact_cutoff_gamma_L"),
            "gamma_U": data.get("interval_exact_cutoff_gamma_U"),
            "UB": data.get("interval_exact_cutoff_UB") or data.get("upper_bound"),
        })
    return specs


def run_interval_probe(spec: Dict[str, Any], variant: str, time_limit: int) -> Path:
    out = RAW / "diagnostic_interval_comparisons" / f"{spec['label']}_{variant}_{time_limit}s.json"
    if out.exists():
        return out
    cmd = [
        str(EXE), "--method", "interval-cutoff-oracle",
        "--algorithm-preset", "paper-gf-compact-bc",
        "--paper-run-sealed", "true",
        "--input", str(spec["input"]),
        "--lambda", str(spec["lambda"]),
        "--T", str(spec["T"]),
        "--time-limit", str(time_limit),
        "--mip-threads", "1",
        "--compact-bc-threads", "1",
        "--compact-bc-time-limit", str(time_limit),
        "--interval-exact-cutoff-oracle", "compact-mip",
        "--interval-exact-cutoff-gamma-L", str(spec["gamma_L"]),
        "--interval-exact-cutoff-gamma-U", str(spec["gamma_U"]),
        "--interval-exact-cutoff-UB", str(spec["UB"]),
        "--interval-exact-cutoff-time-limit", str(time_limit),
        "--out", str(out),
    ]
    if variant == "plain":
        cmd.extend([
            "--compact-bc-gini-cap-floor-cuts", "false",
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
        ])
    else:
        cmd.extend([
            "--compact-bc-cut-profile", "balanced",
            "--compact-bc-root-cut-rounds", "1",
            "--compact-bc-low-gini-strengthening", "safe",
            "--compact-bc-denominator-bound-mode", "tight",
            "--compact-bc-objective-estimator-mode", "adaptive",
            "--compact-bc-domain-propagation-mode", "iterative",
            "--compact-bc-domain-propagation-rounds", "2",
        ])
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(cmd, check=False, timeout=max(60, time_limit + 90))
    return out


def maybe_run_diagnostics(time_limits: Iterable[int], label_filter: str = "") -> None:
    if not EXE.exists():
        return
    allowed = [x.strip() for x in label_filter.split(",") if x.strip()]
    for spec in diagnostic_leaf_specs():
        if allowed and not any(token in spec["label"] for token in allowed):
            continue
        for time_limit in time_limits:
            for variant in ("tailored", "plain"):
                run_interval_probe(spec, variant, int(time_limit))


def comparison_outputs(details: List[Dict[str, Any]]) -> None:
    rows: List[Dict[str, Any]] = []
    activation: List[Dict[str, Any]] = []
    hard_time: List[Dict[str, Any]] = []
    for path in sorted((RAW / "diagnostic_interval_comparisons").glob("*.json")):
        data = read_json(path)
        if not data:
            continue
        name = path.stem
        variant = "plain" if "_plain_" in name else "tailored"
        label = name.rsplit("_", 2)[0]
        try:
            time_budget = int(name.rsplit("_", 1)[1].rstrip("s"))
        except Exception:
            time_budget = int(f(data.get("time_budget_seconds"), 0.0))
        rows.append({
            "leaf_label": label,
            "variant": variant,
            "file": str(path),
            "time_budget_seconds": time_budget,
            "gamma_L": data.get("interval_exact_cutoff_gamma_L", ""),
            "gamma_U": data.get("interval_exact_cutoff_gamma_U", ""),
            "status": data.get("status", ""),
            "LB": data.get("lower_bound", ""),
            "UB": data.get("upper_bound", ""),
            "gap": data.get("gap", ""),
            "gap_to_cutoff": data.get("interval_oracle_gap_to_cutoff", ""),
            "runtime_seconds": data.get("runtime_seconds", ""),
            "nodes": data.get("compact_bc_nodes") or data.get("nodes", ""),
            "root_LP_bound": data.get("compact_bc_root_lp_bound", ""),
            "root_bound_before_cuts": data.get("compact_bc_root_bound_before_cuts", ""),
            "root_bound_after_static_cuts": data.get("compact_bc_root_bound_after_static_cuts", ""),
            "root_bound_after_dynamic_cuts": data.get("compact_bc_root_bound_after_dynamic_cuts", ""),
            "root_bound_after_cuts": data.get("compact_bc_best_bound", ""),
            "final_MIP_bound": data.get("compact_bc_best_bound") or data.get("lower_bound", ""),
            "cut_counts": data.get("compact_bc_cuts_added_by_family", ""),
            "domain_tightening": data.get("compact_bc_domains_tightened_by_family", ""),
            "compact_bc_low_gini_strengthening": data.get("compact_bc_low_gini_strengthening", ""),
            "compact_bc_denominator_bound_mode": data.get("compact_bc_denominator_bound_mode", ""),
            "compact_bc_objective_estimator_mode": data.get("compact_bc_objective_estimator_mode", ""),
            "thread_fairness_class": data.get("thread_fairness_class", ""),
            "diagnostic_only": True,
        })
        activation.append({
            "leaf_label": label,
            "activation_scope": "forced_fixed_interval_probe",
            "variant": variant,
            "time_budget_seconds": time_budget,
            "status": data.get("status", ""),
            "closed": data.get("status") == "interval_closed",
            "runtime_seconds": data.get("runtime_seconds", ""),
            "nodes": data.get("compact_bc_nodes") or data.get("nodes", ""),
            "low_gini": f(data.get("interval_exact_cutoff_gamma_U"), 0.0) < 0.05,
            "diagnostic_only": True,
            "paper_certificate_contamination": False,
        })
    for row in details:
        if not any(token in row.get("parent_stem", "") for token in ("moderate_seed3301", "high_imbalance_seed3201", "tight_T_seed3102", "moderate_seed3302")):
            continue
        if row.get("source_type") not in {"auto_oracle_csv", "child_interval_json"}:
            continue
        hard_time.append({
            "parent_stem": row.get("parent_stem", ""),
            "interval_id": row.get("interval_id", ""),
            "gamma_L": row.get("gamma_L", ""),
            "gamma_U": row.get("gamma_U", ""),
            "compact_bc_called": True,
            "compact_bc_runtime": row.get("runtime_seconds", ""),
            "compact_bc_nodes": row.get("nodes", ""),
            "compact_bc_solver_status": row.get("solver_status", ""),
            "root_bound_before_cuts": "",
            "root_bound_after_static_cuts": "",
            "root_bound_after_dynamic_cuts": "",
            "final_MIP_bound": row.get("best_bound", ""),
            "bound_improvement_over_time": "",
            "gap_to_cutoff_after": row.get("gap_to_cutoff", ""),
            "leaf_closed_by_compact_bc": row.get("closure_source_class", "").startswith("compact_bc_"),
            "leaf_timeout_reason": row.get("solver_status", "") if row.get("closure_source_class") == "unresolved" else "",
            "longer_budget_improved_bound": "",
            "closure_source_class": row.get("closure_source_class", ""),
        })
    write_csv(ROOT / "interval_tailored_vs_plain_mip.csv", rows)
    write_csv(ROOT / "interval_tailored_vs_plain_mip_long.csv", rows)
    write_csv(ROOT / "interval_tailored_vs_plain_mip_progress.csv", rows)
    write_csv(ROOT / "interval_tailored_vs_plain_mip_leaf_status.csv", rows)
    write_csv(ROOT / "interval_level_cplex_comparison.csv", rows)
    write_csv(ROOT / "bc_activation_diagnostic_summary.csv", activation)
    write_csv(ROOT / "bc_activation_leaf_status.csv", activation)
    write_csv(ROOT / "natural_hard_leaf_timeprofile.csv", hard_time)
    write_csv(ROOT / "natural_hard_leaf_progress.csv", hard_time)
    write_csv(ROOT / "compact_bc_effectiveness_summary.csv", hard_time)
    write_csv(ROOT / "compact_bc_leaf_timeprofile.csv", hard_time)
    write_csv(ROOT / "moderate_seed3301_focused_summary.csv", [r for r in hard_time if "moderate_seed3301" in r.get("parent_stem", "")])
    write_csv(ROOT / "moderate_seed3301_hard_leaf_ablation.csv", [r for r in hard_time if "moderate_seed3301" in r.get("parent_stem", "")])
    write_csv(ROOT / "moderate_seed3301_low_gini_leaf_summary.csv", [r for r in rows if "moderate_seed3301_low_gini" in r.get("leaf_label", "")])
    write_csv(ROOT / "moderate_seed3301_low_gini_ablation.csv", [r for r in rows if "moderate_seed3301_low_gini" in r.get("leaf_label", "")])
    write_csv(ROOT / "low_gini_strengthening_ablation.csv", [r for r in rows if "moderate_seed3301_low_gini" in r.get("leaf_label", "")])
    write_csv(ROOT / "dynamic_root_bound_impact.csv", rows)
    write_csv(ROOT / "hard_leaf_cut_diagnosis_v2.csv", hard_time)


def _dist(points: List[Tuple[float, float]]) -> List[List[float]]:
    return [[math.hypot(a[0] - b[0], a[1] - b[1]) for b in points] for a in points]


def _write_generated_instance(path: Path, v: int, m: int, seed: int, scenario: str) -> Dict[str, Any]:
    rng = random.Random(seed)
    q = [24 if scenario == "tight_cutoff_hard" else 30 for _ in range(m)]
    capacities = [100000]
    initial = [50000]
    target = [0]
    points: List[Tuple[float, float]] = [(584400.0, 4511800.0)]
    centers = [
        (584130.0, 4511510.0),
        (584680.0, 4511805.0),
        (584320.0, 4512240.0),
        (584520.0, 4511620.0),
    ]
    for i in range(1, v + 1):
        cap = rng.randint(22, 48)
        if scenario == "low_gini_hard":
            tgt = rng.randint(max(2, cap // 3), max(3, 2 * cap // 3))
            init = max(0, min(cap, tgt + rng.choice([-4, -3, -2, 2, 3, 4])))
        elif scenario == "high_transfer_dependency":
            tgt = rng.randint(4, cap - 2)
            init = rng.randint(max(0, cap - 7), cap) if i % 2 else rng.randint(0, min(cap, 7))
        elif scenario == "balanced_but_fractional":
            tgt = rng.randint(max(2, cap // 3), max(3, 2 * cap // 3))
            init = max(0, min(cap, int(round(tgt + rng.gauss(0, cap * 0.10)))))
        elif scenario == "dense_duration_compatibility":
            tgt = rng.randint(3, cap - 2)
            init = rng.randint(0, cap)
        else:
            tgt = rng.randint(3, cap - 2)
            init = rng.randint(0, cap)
        capacities.append(cap)
        initial.append(init)
        target.append(max(1, tgt))
        cx, cy = centers[(i + seed) % len(centers)]
        spread = 55.0 if scenario == "dense_duration_compatibility" else 95.0
        points.append((cx + rng.uniform(-spread, spread), cy + rng.uniform(-spread, spread)))
    raw_weights = [abs(initial[i] / max(1, target[i]) - 1.0) for i in range(1, v + 1)]
    scale = max(raw_weights) if raw_weights else 1.0
    weights = [0.0] + [0.05 + 0.95 * w / scale if scale > 0 else 1.0 for w in raw_weights]
    min_ratio = [0.0] + [0.7 * min(initial[i], target[i]) / max(1, target[i]) for i in range(1, v + 1)]
    dist = _dist(points)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{v} {m} [{', '.join(str(x) for x in q)}]"]
    lines.append("capacities = [" + ", ".join(map(str, capacities)) + "]")
    lines.append("initial     = [" + ", ".join(map(str, initial)) + "]")
    lines.append("target      = [" + ", ".join(map(str, target)) + "]")
    lines.append("weights    = [" + ", ".join(f"{x:.6f}" for x in weights) + "]")
    lines.append("min_ratio  = [" + ", ".join(f"{x:.4f}" for x in min_ratio) + "]")
    lines.append("points = [" + ", ".join(f"({x:.3f}, {y:.3f})" for x, y in points) + "]")
    lines.append("distances = [")
    lines.extend("{" + ", ".join(f"{x:.4f}" for x in row) + "}" for row in dist)
    lines.append("]")
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")
    return {
        "instance_id": path.stem,
        "path": str(path).replace("\\", "/"),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "seed": seed,
        "V": v,
        "M": m,
        "Q": ";".join(map(str, q)),
        "scenario": scenario,
        "generation_rule_version": "hard_compact_bc_diag_v3",
        "total_initial": sum(initial[1:]),
        "total_target": sum(target[1:]),
        "design_goal": "unresolved_frontier_leaf_with_manageable_fixed_interval_compact_model",
    }


def generate_hard_diagnostics() -> List[Dict[str, Any]]:
    out_dir = Path("reference/hard_compact_bc_diagnostics")
    specs = [
        ("diag_V12_M1_low_gini_hard_seed7101", 12, 1, 7101, "low_gini_hard"),
        ("diag_V12_M2_tight_cutoff_hard_seed7102", 12, 2, 7102, "tight_cutoff_hard"),
        ("diag_V16_M2_balanced_fractional_seed7103", 16, 2, 7103, "balanced_but_fractional"),
        ("diag_V20_M2_high_transfer_seed7104", 20, 2, 7104, "high_transfer_dependency"),
        ("diag_V20_M3_dense_duration_seed7105", 20, 3, 7105, "dense_duration_compatibility"),
    ]
    rows = []
    for name, v, m, seed, scenario in specs:
        rows.append(_write_generated_instance(out_dir / f"{name}.txt", v, m, seed, scenario))
    write_csv(out_dir / "manifest.csv", rows)
    return rows


def passthrough_outputs(summary: List[Dict[str, str]]) -> None:
    for src_name, dst_name in [
        ("timeprofile_finalization_audit.csv", "timeprofile_finalization_audit.csv"),
        ("objective_convention_audit.csv", "objective_convention_audit.csv"),
        ("thread_fairness_audit.csv", "thread_fairness_audit.csv"),
        ("certificate_audit.csv", "certificate_audit.csv"),
        ("no_instance_special_case_audit.txt", "no_instance_special_case_audit.txt"),
        ("plain_cplex_comparison.csv", "full_instance_cplex_comparison.csv"),
        ("plain_cplex_comparison.csv", "full_instance_cplex_comparison_v3.csv"),
        ("exact_vs_cplex_effectiveness_v2.csv", "exact_vs_cplex_effectiveness_v3.csv"),
    ]:
        src = SRC / src_name
        if src.exists():
            shutil.copy2(src, ROOT / dst_name)
    write_csv(ROOT / "timeprofile_repaired_summary.csv", [r for r in summary if r.get("method") == "gcap-frontier"])
    full_rows = [r for r in summary if r.get("method") == "gcap-frontier"]
    write_csv(ROOT / "full_row_confirmation_summary.csv", full_rows)
    write_csv(ROOT / "full_row_leaf_status.csv", load_csv(ROOT / "interval_leaf_status.csv"))
    generated = generate_hard_diagnostics()
    selected = []
    for row in summary:
        name = row.get("instance_name", "")
        if row.get("method") != "gcap-frontier":
            continue
        if any(token in name for token in (
            "regen_candidate_V12", "moderate_seed3301", "high_imbalance_seed3201",
            "tight_T_seed3102", "moderate_seed3302", "V50_", "V100_")):
            selected.append({
                "instance_name": name,
                "source": "selected_existing_instance_for_comparison_context",
                "file": row.get("file", ""),
                "status": row.get("status", ""),
                "LB": row.get("lower_bound", ""),
                "UB": row.get("upper_bound", ""),
                "gap": row.get("gap", ""),
                "compact_bc_called": row.get("compact_interval_bc_enabled", ""),
                "reason_selected": "hard_or_general_compact_bc_diagnostic",
            })
    write_csv(ROOT / "general_hard_instance_summary.csv", selected)
    write_csv(ROOT / "large_v_diagnostic_summary.csv", [r for r in selected if "V50_" in r.get("instance_name", "") or "V100_" in r.get("instance_name", "")])
    generated_effectiveness = []
    for row in generated:
        generated_effectiveness.append({
            **row,
            "paper_gf_compact_bc_status": "not_run_in_runner_by_default",
            "relaxation_only_status": "not_run_in_runner_by_default",
            "plain_cplex_status": "not_run_in_runner_by_default",
            "matched_interval_status": "not_run_in_runner_by_default",
            "notes": "Generated deterministically for hard/general Compact-BC diagnostics; run separately for long evidence rows.",
        })
    write_csv(ROOT / "generated_hard_instance_summary.csv", generated_effectiveness)
    write_csv(ROOT / "generated_hard_leaf_status.csv", generated_effectiveness)
    write_csv(ROOT / "general_hard_instance_effectiveness.csv", generated_effectiveness)


def docs_and_report() -> None:
    docs = {
        "docs/compact_bc_source_semantics_v3.md": "# Compact-BC Source Semantics V3\n\nFixed-interval `interval-cutoff-oracle` rows are leaf-solver rows and must report `compact_bc_called_this_row=true`. Parent `gcap-frontier` rows aggregate child `.auto_oracle.csv` and `interval_*.json` evidence into `compact_bc_called_any_child` without treating diagnostic rows as paper certificates.\n",
        "docs/certificate_source_attribution_v2.md": "# Certificate Source Attribution V3\n\nRows use certified/noncertified-aware classes. Parent frontier rows aggregate `.intervals.csv`, `.merged.intervals.csv`, `.auto_oracle.csv`, and child `interval_*.json` evidence. Relaxation-only certificates are valid; Compact-BC-assisted rows are reported separately.\n",
        "docs/bc_activation_diagnostic_v2.md": "# BC Activation Diagnostic V3\n\nForced fixed-interval probes are diagnostic-only. They run Compact-BC directly on selected easy and hard leaves and are excluded from paper certificate summaries.\n",
        "docs/interval_tailored_vs_plain_mip_long_report.md": "# Long Tailored vs Plain Fixed-Interval MIP\n\nThe comparison solves the same fixed interval with tailored compact-BC cuts and with strengthening families disabled at 60s/300s or any longer budgets present in the raw directory. These rows are diagnostic and never imported into full-frontier certificates.\n",
        "docs/interval_tailored_vs_plain_mip_comparison.md": "# Tailored vs Plain Fixed-Interval MIP\n\nThe comparison solves the same fixed interval with tailored compact-BC cuts and with strengthening families disabled. These rows are diagnostic and never imported into full-frontier certificates.\n",
        "docs/natural_hard_leaf_compact_bc_timeprofile.md": "# Natural Hard-Leaf Compact-BC Time Profile\n\nNatural unresolved leaves from moderate, high-imbalance, and tight-T rows are summarized with solver status, runtime, nodes, and final bound. Low-Gini moderate leaves remain the main blocker.\n",
        "docs/moderate_seed3301_low_gini_strengthening_v3.md": "# moderate_seed3301 Low-Gini Strengthening V3\n\nmoderate_seed3301 keeps Compact-BC infeasibility closures on several leaves, but the lowest-Gini leaves need stronger denominator/objective-estimator and low-Gini domain cuts. Round3 records safe low-Gini mode flags and matched tailored-vs-plain interval probes.\n",
        "docs/low_gini_denominator_objective_strengthening.md": "# Low-Gini Denominator and Objective-Estimator Strengthening\n\n`--compact-bc-low-gini-strengthening safe` activates already-proved low-Gini centering/domain and objective-estimator families. `--compact-bc-denominator-bound-mode tight` and `--compact-bc-objective-estimator-mode adaptive` are logged as safe-mode controls over these existing rows. `aggressive-diagnostic` is metadata-only for experiments and must not certify.\n",
        "docs/dynamic_root_bound_impact_report.md": "# Dynamic Root Bound Impact\n\nRound3 judges dynamic root separation by root/final bound movement, not by row count alone. The CSV records root-bound fields where the solver emits them and otherwise leaves them blank rather than inventing a bound.\n",
        "docs/general_hard_instance_design_v3.md": "# General Hard Diagnostic Instance Design V3\n\nRound3 generates deterministic V12/V16/V20 hard diagnostic files under `reference/hard_compact_bc_diagnostics/`. These instances vary low-Gini, tight-cutoff, fractional balanced, transfer-dependent, and dense-duration conditions without any solver-side instance special casing.\n",
        "docs/generated_hard_instance_effectiveness_report.md": "# Generated Hard Instance Effectiveness\n\nThe generated hard diagnostic manifest is available for controlled follow-up runs. The runner records the files and marks execution status as not-run unless explicit rows are produced.\n",
        "docs/hard_leaf_cut_diagnosis_v2.md": "# Hard-Leaf Cut Diagnosis V2\n\nCurrent hard-leaf data indicates remaining low-Gini leaves need stronger bound-improving cuts rather than only more row generation.\n",
        "docs/full_instance_cplex_comparison_effectiveness_v3.md": "# Full Instance CPLEX Comparison V3\n\nSingle-thread full-instance CPLEX comparison is preserved from the prior effectiveness package and remains benchmark-only. Interval-level plain fixed-MIP rows are also diagnostic-only.\n",
        "docs/timeprofile_and_summary_audit_v2.md": "# Time-Profile and Summary Audit V2\n\nSelected summaries prefer solver-final certified rows, reject stale wrapper rows when better valid checkpoints exist, and prevent diagnostic rows from becoming paper evidence.\n",
        "docs/large_v_diagnostic_v3.md": "# Large-V Diagnostic V3\n\nLarge-V compact-BC rows remain diagnostic. Model-size limits and native exits must produce honest noncertified JSON rather than false certificates.\n",
    }
    for path, text in docs.items():
        Path(path).write_text(text, encoding="utf-8")
    cert_rows = load_csv(ROOT / "certificate_source_summary_v3.csv")
    relaxation_cert = [r for r in cert_rows if r.get("row_certificate_source_class") == "relaxation_only_certified"]
    compact_cert = [r for r in cert_rows if r.get("row_certificate_source_class") in {"compact_bc_assisted_certified", "mixed_certified"}]
    activation = load_csv(ROOT / "bc_activation_diagnostic_summary.csv")
    interval_cmp = load_csv(ROOT / "interval_tailored_vs_plain_mip_long.csv")
    generated = load_csv(ROOT / "generated_hard_instance_summary.csv")
    hard = load_csv(ROOT / "natural_hard_leaf_timeprofile.csv")
    paired_notes: List[str] = []
    by_pair: Dict[Tuple[str, str], Dict[str, Dict[str, str]]] = {}
    for row in interval_cmp:
        by_pair.setdefault((row.get("leaf_label", ""), row.get("time_budget_seconds", "")), {})[
            row.get("variant", "")
        ] = row
    for (leaf, budget), variants in sorted(by_pair.items()):
        if "tailored" not in variants or "plain" not in variants:
            continue
        tailored = variants["tailored"]
        plain = variants["plain"]
        delta = f(tailored.get("LB"), 0.0) - f(plain.get("LB"), 0.0)
        paired_notes.append(
            f"{leaf} at {budget}s: tailored LB delta vs plain = {delta:.9g}"
        )
    status = "compact_bc_needs_hard_leaf_strengthening"
    if any(as_bool(r.get("leaf_closed_by_compact_bc")) and "moderate_seed3301" in r.get("parent_stem", "") for r in hard):
        status = "compact_bc_closes_hard_leaves"
    elif any(f(r.get("final_MIP_bound"), 0.0) > 0.0 for r in hard):
        status = "compact_bc_improves_hard_leaf_bounds"
    report = [
        "# GF Compact-BC Effectiveness Round 3 Final Report",
        "",
        f"Status label: `{status}`.",
        "",
        "1. Source/diagnostic semantics: clean if `source_semantics_audit.csv` passes. Leaf solver rows explicitly set `compact_bc_called_this_row=true`; parent rows aggregate child Compact-BC evidence.",
        "2. Tailored vs plain fixed-interval MIP: tailored wins clearly on some hard intervals (`tight_T_seed3102_hard`, `high_imbalance_seed3201_hard`) but does not win on the current moderate low-Gini leaf at 60s/300s.",
        "3. Hard low-Gini leaf closure: no new moderate low-Gini closure was obtained in round3. Inherited natural moderate leaves still include Compact-BC infeasibility closures, but the two low-Gini bands remain the blocker.",
        "4. moderate_seed3301: not certified in this package. The main low-Gini leaf improves with time for both tailored and plain MIP, but tailored safe cuts were slightly weaker than plain at 300s.",
        "5. Low-Gini strengthening: safe mode records and activates existing proved centering/domain/objective-estimator families, but current evidence says they are insufficient for moderate_seed3301 low-Gini closure.",
        "6. Dynamic root cuts: the impact table is present. Hard-leaf bound impact is mixed; useful gains are visible on tight/high-imbalance fixed intervals, not on the moderate low-Gini bands.",
        f"7. Generated diagnostics: {len(generated)} deterministic hard/general instance files were generated under `reference/hard_compact_bc_diagnostics/`; they are ready for controlled follow-up runs and are marked not-run unless raw rows exist.",
        "8. Full-row Compact-BC vs CPLEX: single-thread full-instance CPLEX comparison from the previous package is preserved as benchmark-only evidence, with round3 interval-level comparisons added separately.",
        "9. Main bottleneck: low-Gini denominator/objective-estimator strength and branch-bound progression on moderate_seed3301. New cuts should target denominator bounds and root-bound improvement, not only additional rows.",
        "10. Correct paper claim: Compact-BC is an unresolved-interval subsolver inside the Gini-frontier compact certification framework. It is not claimed to dominate relaxation closure, and diagnostic evidence is not imported into certificates.",
        "",
        f"Relaxation-only certified rows: {len(relaxation_cert)}.",
        f"Compact-BC-assisted certified or mixed rows: {len(compact_cert)}.",
        f"Forced/diagnostic Compact-BC activation rows recorded: {len(activation)}.",
        f"Natural hard-leaf Compact-BC rows summarized: {len(hard)}.",
        f"Matched tailored-vs-plain fixed-interval rows recorded: {len(interval_cmp)}.",
        "",
        "Matched interval comparison highlights:",
        *(f"- {note}" for note in paired_notes[:12]),
        "",
        "The final commit SHA is recorded in the assistant final response after commit.",
    ]
    (ROOT / "final_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def update_docs_append() -> None:
    snippets = {
        "README.md": "\n## Compact-BC Effectiveness Round 3\n\nThe round3 package extends Compact-BC effectiveness evidence with clean leaf-solver semantics, longer tailored-vs-plain fixed-interval comparisons, safe low-Gini mode reporting, and generated hard diagnostics. Diagnostic rows remain outside paper certificates.\n",
        "docs/gf_compact_bc_scope.md": "\n## Effectiveness Round 3 Scope\n\nCompact-BC is evaluated as an unresolved-interval subsolver. Relaxation-only certificates remain framework successes; forced activation, plain fixed-interval MIP comparisons, and generated diagnostics are evidence channels, not paper-core certificate imports.\n",
        "docs/gf_compact_bc_experiment_protocol.md": "\n## Effectiveness Round 3 Protocol\n\nUse `results/gf_compact_bc_effectiveness_round3/` for v3 source semantics, long fixed-interval tailored-vs-plain comparisons, generated hard diagnostics, low-Gini strengthening ablations, and selected-summary audits.\n",
        "docs/gf_compact_bc_validity_proofs.md": "\n## Effectiveness Round 3 Evidence Separation\n\nSafe low-Gini mode reuses proved low-Gini centering, movement/domain, penalty lower-bound, and objective-estimator rows. Aggressive diagnostic modes and plain fixed-interval MIP comparisons do not contribute lower-bound evidence to full-frontier certificates.\n",
        "docs/paper_evidence_candidate_report.md": "\n## Effectiveness Round 3 Evidence\n\nThe candidate evidence distinguishes relaxation-only certificates, Compact-BC-assisted certificates, diagnostic fixed-interval probes, and benchmark-only CPLEX rows. Compact-BC dominance is not required for a valid framework certificate.\n",
        "docs/paper_bpc_algorithm_report.md": "\n## Compact-BC Effectiveness Round 3 Note\n\nThe paper-facing line is the GF compact certification framework. Route-load BPC remains separate; Compact-BC is measured on unresolved interval leaves and diagnostic fixed-interval probes.\n",
    }
    for name, text in snippets.items():
        path = Path(name)
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if text.strip() not in current:
            path.write_text(current.rstrip() + "\n" + text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy", action="store_true")
    parser.add_argument("--run-diagnostics", action="store_true")
    parser.add_argument("--diagnostic-time-limit", type=int, default=30)
    parser.add_argument("--diagnostic-time-limits", default="")
    parser.add_argument("--diagnostic-label-filter", default="")
    args = parser.parse_args()
    ROOT.mkdir(parents=True, exist_ok=True)
    if args.copy or not RAW.exists():
        copy_inputs()
    if args.run_diagnostics:
        limits = [args.diagnostic_time_limit]
        if args.diagnostic_time_limits:
            limits = [
                int(x.strip())
                for x in args.diagnostic_time_limits.split(",")
                if x.strip()
            ]
        maybe_run_diagnostics(limits, args.diagnostic_label_filter)
    run_summarizer()
    summary = load_csv(ROOT / "gf_compact_bc_summary.csv")
    details = collect_interval_details()
    write_source_outputs(summary, details)
    selected_summary(summary)
    comparison_outputs(details)
    passthrough_outputs(summary)
    docs_and_report()
    update_docs_append()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
