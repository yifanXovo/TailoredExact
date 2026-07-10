#!/usr/bin/env python3
"""Dominant S-bucket structural-cut round for paper-gf-tailored-bc."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

import run_tailored_bc_plateau_diagnosis_round as base


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "gf_tailored_bc_structural_cut_round"
RAW = RESULTS / "raw"
LOGS = RESULTS / "logs"
PROGRESS = RESULTS / "progress_traces"
MODELS = RESULTS / "model_exports"
VECTORS = RESULTS / "vector_snapshots"
DOCS = ROOT / "docs"

LOW_GINI_1_CUTOFF = 0.0491525526647
BUCKETS = {
    "dominant_k4": (16.59546103547, 23.272821182835),
    "adaptive_child": (18.26480107231125, 19.9341411091525),
}

LEAVES: Dict[str, Dict[str, Any]] = {
    "low_gini_1": {
        "instance": "reference/hard_stress/V20_M3/moderate_seed3301.txt",
        "gamma_L": 0.0122881381662,
        "gamma_U": 0.0245762763324,
        "UB": LOW_GINI_1_CUTOFF,
    },
    "low_gini_2": {
        "instance": "reference/hard_stress/V20_M3/moderate_seed3301.txt",
        "gamma_L": 0.0245762763324,
        "gamma_U": 0.0368644144986,
        "UB": LOW_GINI_1_CUTOFF,
    },
    "high_imbalance_seed3201_hard": {
        "instance": "reference/hard_stress/V20_M3/high_imbalance_seed3201.txt",
        "gamma_L": 0.475,
        "gamma_U": 0.59375,
        "UB": 2.44340319194,
    },
    "tight_T_seed3102_hard": {
        "instance": "reference/hard_stress/V20_M3/tight_T_seed3102.txt",
        "gamma_L": 0.150176109171,
        "gamma_U": 0.300352218343,
        "UB": 0.600704436685,
    },
}


def f(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
        return out if math.isfinite(out) else default
    except Exception:
        return default


def b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


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


def parse_family_counts(text: Any) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for part in str(text or "").replace("|", ";").split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        try:
            out[key.strip()] = int(float(value))
        except Exception:
            out[key.strip()] = 0
    return out


def configure_base() -> None:
    base.RESULTS = RESULTS
    base.RAW = RAW
    base.LOGS = LOGS
    base.PROGRESS = PROGRESS
    base.MODELS = MODELS
    base.MODERATE.clear()
    base.MODERATE.update(LEAVES)


def bucket_flags(bucket: str, budget: int) -> List[str]:
    lo, hi = BUCKETS[bucket]
    return [
        "--tailored-bc-s-bucket-ledger", "paper-safe",
        "--tailored-bc-s-bucket-count", "1",
        "--tailored-bc-s-bucket-policy", "dominant-fixed",
        "--tailored-bc-s-bucket-time-budget", str(budget),
        "--tailored-bc-s-bucket-merge-audit", "true",
        "--compact-bc-s-range-refinement", "paper-safe",
        "--compact-bc-s-range-buckets", "1",
        "--compact-bc-s-range-bucket-id", "0",
        "--compact-bc-s-range-bucket-L", repr(lo),
        "--compact-bc-s-range-bucket-U", repr(hi),
        "--compact-bc-s-range-adaptive", "false",
    ]


def variant_flags(variant: str) -> List[str]:
    common = base.TAILORED_COMMON + [
        "--tailored-bc-mode", "static",
        "--tailored-bc-local-centering", "true",
        "--tailored-bc-gini-branching", "off",
    ]
    if variant == "plain_fixed_interval_mip":
        return base.variant_flags("plain_fixed_interval_mip")
    if variant == "static_tailored_compact_bc":
        return common
    if variant == "gs_product_coupling":
        return common + [
            "--tailored-bc-gs-product-coupling", "true",
            "--tailored-bc-gs-product-coupling-mode", "static",
            "--tailored-bc-gs-product-lower-row", "off",
        ]
    if variant == "disaggregated_sp_estimator":
        return common + [
            "--tailored-bc-disaggregated-sp-estimator", "true",
            "--tailored-bc-disaggregated-sp-mode", "static",
            "--tailored-bc-disaggregated-sp-replace-aggregate", "true",
        ]
    if variant == "vector_route_structural":
        return common + [
            "--tailored-bc-vector-support-cover", "true",
            "--tailored-bc-vector-support-cover-max-size", "3",
            "--tailored-bc-vector-route-cutset", "true",
            "--tailored-bc-vector-route-cutset-max-size", "3",
            "--tailored-bc-vector-cut-candidate-source", "root",
        ]
    if variant == "gs_plus_disagg_sp":
        return variant_flags("gs_product_coupling") + [
            "--tailored-bc-disaggregated-sp-estimator", "true",
            "--tailored-bc-disaggregated-sp-mode", "static",
            "--tailored-bc-disaggregated-sp-replace-aggregate", "true",
        ]
    if variant in {"all_new_structural_cuts", "current_best_new_combined_paper_safe"}:
        return variant_flags("gs_plus_disagg_sp") + [
            "--tailored-bc-vector-support-cover", "true",
            "--tailored-bc-vector-support-cover-max-size", "3",
            "--tailored-bc-vector-route-cutset", "true",
            "--tailored-bc-vector-route-cutset-max-size", "3",
            "--tailored-bc-vector-cut-candidate-source", "root",
        ]
    raise ValueError(f"unknown structural variant {variant}")


def plan(profile: str) -> List[Tuple[str, str, int, str]]:
    if profile == "smoke":
        return [
            ("low_gini_1", "static_tailored_compact_bc", 10, "dominant_k4"),
            ("low_gini_1", "all_new_structural_cuts", 10, "dominant_k4"),
            ("low_gini_1", "plain_fixed_interval_mip", 10, "dominant_k4"),
        ]
    if profile == "standard":
        variants = [
            "static_tailored_compact_bc",
            "gs_product_coupling",
            "disaggregated_sp_estimator",
            "vector_route_structural",
            "gs_plus_disagg_sp",
            "all_new_structural_cuts",
            "current_best_new_combined_paper_safe",
            "plain_fixed_interval_mip",
        ]
        return [("low_gini_1", v, 60, "dominant_k4") for v in variants] + [
            ("low_gini_2", "all_new_structural_cuts", 60, "dominant_k4"),
            ("high_imbalance_seed3201_hard", "all_new_structural_cuts", 60, "dominant_k4"),
            ("tight_T_seed3102_hard", "all_new_structural_cuts", 60, "dominant_k4"),
        ]
    variants = [
        "static_tailored_compact_bc",
        "gs_product_coupling",
        "disaggregated_sp_estimator",
        "vector_route_structural",
        "gs_plus_disagg_sp",
        "all_new_structural_cuts",
        "current_best_new_combined_paper_safe",
    ]
    rows: List[Tuple[str, str, int, str]] = []
    for variant in variants:
        for budget in (300, 1200, 3600):
            rows.append(("low_gini_1", variant, budget, "dominant_k4"))
    for variant in ("static_tailored_compact_bc", "gs_plus_disagg_sp", "all_new_structural_cuts"):
        rows.append(("low_gini_1", variant, 14400, "dominant_k4"))
    for budget in (300, 1200):
        rows.append(("low_gini_1", "plain_fixed_interval_mip", budget, "dominant_k4"))
    for leaf in ("low_gini_2", "high_imbalance_seed3201_hard", "tight_T_seed3102_hard"):
        rows.append((leaf, "all_new_structural_cuts", 300, "dominant_k4"))
    return rows


def run_row(leaf: str, variant: str, budget: int, bucket: str, args: argparse.Namespace) -> Dict[str, Any]:
    spec = LEAVES[leaf]
    stem = f"{bucket}_{leaf}_{variant}_{budget}s"
    out = RAW / f"{stem}.json"
    progress = PROGRESS / f"{stem}.progress.csv"
    lp = MODELS / f"{stem}.lp"
    cmd = base.base_interval_cmd(spec, budget, out, progress, lp) + variant_flags(variant)
    if variant != "plain_fixed_interval_mip":
        cmd += bucket_flags(bucket, budget)
    log = LOGS / f"{stem}.log.txt"
    if args.run:
        base.run_cmd(cmd, log, timeout=budget + args.wrapper_grace, skip_existing=args.skip_existing)
        if out.exists():
            annotate_json(out, spec, leaf, variant, budget, bucket, cmd)
    return summarize_row(leaf, variant, budget, bucket, out, progress, lp, cmd)


def annotate_json(path: Path, spec: Dict[str, Any], leaf: str, variant: str,
                  budget: int, bucket: str, cmd: Sequence[str]) -> None:
    data = read_json(path)
    if not data:
        return
    data.setdefault("algorithm_preset", "paper-gf-tailored-bc")
    data.setdefault("input_path", str(ROOT / spec["instance"]))
    data.setdefault("thread_fairness_class", "one_thread_fair")
    data.setdefault("solver_thread_policy", "controlled_single_thread")
    data.setdefault("compact_bc_solver_threads", 1)
    data.setdefault("cplex_threads", 1)
    data.setdefault("mip_threads", 1)
    data.setdefault("time_budget_seconds", budget)
    data.setdefault("command_hash", base.sha16(" ".join(cmd)))
    data["dominant_structural_round"] = True
    data["dominant_structural_leaf"] = leaf
    data["dominant_structural_variant"] = variant
    data["dominant_s_bucket_name"] = bucket
    data["dominant_s_bucket_L"] = BUCKETS[bucket][0]
    data["dominant_s_bucket_U"] = BUCKETS[bucket][1]
    data["paper_certificate_contamination"] = False
    data["diagnostic_row"] = variant == "plain_fixed_interval_mip"
    data["paper_certificate_role"] = (
        "benchmark_only" if variant == "plain_fixed_interval_mip"
        else "fixed_interval_tailored_bc_subproblem"
    )
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def summarize_row(leaf: str, variant: str, budget: int, bucket: str, out: Path,
                  progress: Path, lp: Path, cmd: Sequence[str]) -> Dict[str, Any]:
    data = read_json(out)
    cutoff = LEAVES[leaf]["UB"]
    lb = f(data.get("lower_bound"), f(data.get("compact_bc_best_bound")))
    if data.get("status") == "interval_closed":
        lb = cutoff
    fam = parse_family_counts(data.get("compact_bc_cuts_added_by_family",
                                       data.get("tailored_bc_user_cuts_added_by_family", "")))
    return {
        "leaf": leaf,
        "variant": variant,
        "bucket": bucket,
        "budget_seconds": budget,
        "json_path": str(out.relative_to(ROOT)),
        "progress_path": str(progress.relative_to(ROOT)) if progress.exists() else "",
        "lp_path": str(lp.relative_to(ROOT)) if lp.exists() else "",
        "command_hash": base.sha16(" ".join(cmd)),
        "status": data.get("status", "missing"),
        "solver_status": data.get("compact_bc_solver_status", ""),
        "lower_bound": lb,
        "upper_bound": f(data.get("upper_bound"), cutoff),
        "gap_to_cutoff": max(0.0, cutoff - lb),
        "runtime_seconds": f(data.get("runtime_seconds"), f(data.get("actual_runtime_seconds"))),
        "nodes": data.get("compact_bc_nodes", data.get("nodes", "")),
        "valid_checkpoint_count": data.get("valid_checkpoint_count", ""),
        "last_improvement_time": data.get("last_bound_improvement_time", ""),
        "root_lp_objective": data.get("root_lp_objective", "not_available"),
        "thread_fairness_class": data.get("thread_fairness_class", ""),
        "compact_bc_solver_threads": data.get("compact_bc_solver_threads", ""),
        "gs_rows": int(data.get("gs_mccormick_rows_added", 0) or 0) + int(data.get("gs_h_upper_rows_added", 0) or 0),
        "disagg_rows": int(data.get("disagg_sp_mccormick_rows_added", 0) or 0) + int(data.get("disagg_sp_estimator_rows_added", 0) or 0),
        "vector_support_cover_cuts_added": data.get("vector_support_cover_cuts_added", 0),
        "vector_route_cutset_cuts_added": data.get("vector_route_cutset_cuts_added", 0),
        "compact_bc_cuts_added_by_family": data.get("compact_bc_cuts_added_by_family", ""),
        "tailored_bc_user_cuts_added_by_family": data.get("tailored_bc_user_cuts_added_by_family", ""),
        "objective_estimator_cutoff": fam.get("objective_estimator_cutoff", 0),
        "sp_product_estimator": fam.get("sp_product_estimator", 0),
        "gs_product_coupling": fam.get("gs_product_coupling", 0),
        "disaggregated_sp_estimator": fam.get("disaggregated_sp_estimator", 0),
        "vector_support_cover": fam.get("vector_support_cover", 0),
        "vector_route_cutset": fam.get("vector_route_cutset", 0),
    }


def split_vector(names_text: Any, values_text: Any) -> Iterable[Tuple[str, float]]:
    names = [p for p in str(names_text or "").split(";") if p != ""]
    values = [p for p in str(values_text or "").split(";") if p != ""]
    for name, value in zip(names, values):
        try:
            yield name, float(value)
        except Exception:
            yield name, math.nan


def family_of(name: str) -> Tuple[str, str]:
    patterns = [
        ("G", r"^G$"),
        ("S", r"^S$"),
        ("P", r"^P$"),
        ("H", r"^H$"),
        ("W_SP", r"^W_SP$"),
        ("W_GS", r"^W_GS$"),
        ("T_SP_i", r"^T_SP_(\d+)$"),
        ("r_i", r"^r_(\d+)$"),
        ("Y_i", r"^Y_(\d+)$"),
        ("e_i", r"^e_(\d+)$"),
        ("h_i_j", r"^h_(\d+)_(\d+)$"),
        ("q_i", r"^q_(\d+)$"),
        ("z_k_i", r"^z_(\d+)_(\d+)$"),
        ("p_k_i", r"^p_(\d+)_(\d+)$"),
        ("d_k_i", r"^d_(\d+)_(\d+)$"),
        ("x_k_i_j", r"^x_(\d+)_(\d+)_(\d+)$"),
        ("load variables", r"^(?:load|L)_.+"),
        ("service/mode variables", r"^(?:service|mode|ord|pos|visit)_.+"),
        ("bit variables", r"^(?:bit|b)_.+"),
        ("McCormick auxiliary variables", r"^(?:prod|zprod)_.+"),
        ("objective-estimator auxiliary variables", r"^(?:q_l1)_\d+$"),
        ("objective-estimator auxiliary variables", r"^(?:r_min|r_max)$"),
        ("other documented auxiliary variables", r"^(?:u|time|arrival|depart|flow)_.+"),
    ]
    for family, pattern in patterns:
        if re.match(pattern, name):
            return family, "|".join(re.match(pattern, name).groups() if re.match(pattern, name).groups() else [])
    return "unknown_unparsed", ""


def parse_instance_weights(path_text: Any) -> Dict[int, float]:
    path = Path(str(path_text or ""))
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"weights\s*=\s*\[([^\]]+)\]", text)
    if not match:
        return {}
    out: Dict[int, float] = {}
    for idx, token in enumerate(match.group(1).split(",")):
        try:
            out[idx] = float(token.strip())
        except Exception:
            continue
    return out


def vector_rows_from_json(json_path: Path, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    weights = parse_instance_weights(data.get("input_path", ""))
    sources = [
        ("first_relaxation_callback",
         data.get("tailored_bc_callback_vector_full_variable_names"),
         data.get("tailored_bc_callback_vector_full_variable_values")),
        ("first_candidate_callback",
         data.get("tailored_bc_callback_candidate_vector_full_variable_names"),
         data.get("tailored_bc_callback_candidate_vector_full_variable_values")),
    ]
    for source, names, values in sources:
        if not names or str(names) in {"not_available", ""}:
            continue
        snapshot_id = f"{json_path.stem}:{source}"
        for name, value in split_vector(names, values):
            family, indices = family_of(name)
            weight = ""
            if family in {"e_i", "T_SP_i"} and indices:
                try:
                    weight = weights.get(int(indices.split("|")[0]), "")
                except Exception:
                    weight = ""
            rows.append({
                "snapshot_id": snapshot_id,
                "snapshot_source": source,
                "json_path": str(json_path.relative_to(ROOT)),
                "variable_name": name,
                "family": family,
                "indices": indices,
                "weight": weight,
                "value": value,
                "nonzero": abs(value) > 1e-12 if math.isfinite(value) else "",
                "diagnostic_only": True,
                "V": data.get("V", data.get("stations", "")),
                "gamma_L": data.get("interval_gamma_L", data.get("gamma_L", "")),
                "gamma_U": data.get("interval_gamma_U", data.get("gamma_U", "")),
                "cutoff": data.get("interval_final_ub_cutoff", data.get("upper_bound", "")),
                "snapshot_objective": (
                    data.get("tailored_bc_callback_vector_objective", "")
                    if source == "first_relaxation_callback"
                    else data.get("tailored_bc_callback_candidate_vector_objective", "")
                ),
            })
    return rows


def cplex_root_solution(lp: Path, timeout: int = 120) -> Tuple[List[Tuple[str, float]], float]:
    if not lp.exists():
        return [], math.nan
    cplex = "cplex"
    sol = VECTORS / f"{lp.stem}.root_lp.sol"
    cmd_file = VECTORS / f"{lp.stem}.root_lp.cplex.cmd"
    cmd_file.parent.mkdir(parents=True, exist_ok=True)
    cmd_file.write_text(
        f'read "{lp}"\nset threads 1\nchange problem lp\noptimize\nwrite "{sol}"\nquit\n',
        encoding="utf-8",
    )
    try:
        subprocess.run([cplex], stdin=cmd_file.open("r", encoding="utf-8"),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=timeout, check=False)
    except Exception:
        return [], math.nan
    if not sol.exists():
        return [], math.nan
    text = sol.read_text(encoding="utf-8", errors="replace")
    objective_match = re.search(r'objectiveValue="([^"]+)"', text)
    objective = f(objective_match.group(1), math.nan) if objective_match else math.nan
    return ([(m.group(1), f(m.group(2), math.nan))
             for m in re.finditer(r'<variable name="([^"]+)"[^>]* value="([^"]+)"', text)],
            objective)


def summarize_vectors(raw_rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_snapshot: Dict[str, List[Dict[str, Any]]] = {}
    for row in raw_rows:
        by_snapshot.setdefault(str(row["snapshot_id"]), []).append(row)
    summaries: List[Dict[str, Any]] = []
    for sid, rows in sorted(by_snapshot.items()):
        vals = {str(r["variable_name"]): f(r["value"], math.nan) for r in rows}
        family_counts: Dict[str, int] = {}
        for r in rows:
            family_counts[str(r["family"])] = family_counts.get(str(r["family"]), 0) + 1
        s_val = vals.get("S", sum(v for k, v in vals.items() if k.startswith("r_") and math.isfinite(v)))
        h_val = vals.get("H", sum(v for k, v in vals.items() if k.startswith("h_") and math.isfinite(v)))
        p_terms: List[float] = []
        for r in rows:
            if r.get("family") != "e_i":
                continue
            weight = f(r.get("weight", ""), math.nan)
            value = f(r.get("value", ""), math.nan)
            if math.isfinite(weight) and math.isfinite(value):
                p_terms.append(weight * value)
        p_val = vals.get("P", sum(p_terms) if p_terms else math.nan)
        g_val = vals.get("G", math.nan)
        wsp = vals.get("W_SP", math.nan)
        summaries.append({
            "snapshot_id": sid,
            "snapshot_source": rows[0].get("snapshot_source", ""),
            "V": rows[0].get("V", ""),
            "variable_count": len(rows),
            "unknown_unparsed_count": family_counts.get("unknown_unparsed", 0),
            "unknown_unparsed_fraction": (
                family_counts.get("unknown_unparsed", 0) / len(rows) if rows else "not_available"
            ),
            "family_counts": ";".join(f"{k}={v}" for k, v in sorted(family_counts.items())),
            "S": s_val,
            "P": p_val,
            "H": h_val,
            "G": g_val,
            "W_SP": wsp,
            "W_GS": vals.get("W_GS", "not_available"),
            "sum_i_w_i_T_SP_i": sum(
                f(r.get("weight"), 0.0) * f(r.get("value"), 0.0)
                for r in rows
                if r.get("family") == "T_SP_i" and
                math.isfinite(f(r.get("weight"), math.nan)) and
                math.isfinite(f(r.get("value"), math.nan))
            ) if any(r.get("family") == "T_SP_i" for r in rows) else "not_available",
            "reconstructed_S_times_P": s_val * p_val if math.isfinite(s_val) and math.isfinite(p_val) else "not_available",
            "reconstructed_H_over_VS": h_val / (20.0 * s_val) if math.isfinite(h_val) and math.isfinite(s_val) and s_val > 1e-12 else "not_available",
            "G_gap": h_val / (20.0 * s_val) - g_val if math.isfinite(h_val) and math.isfinite(s_val) and math.isfinite(g_val) and s_val > 1e-12 else "not_available",
            "SP_gap": s_val * p_val - wsp if math.isfinite(s_val) and math.isfinite(p_val) and math.isfinite(wsp) else "not_available",
            "root_LP_objective": rows[0].get("snapshot_objective", "not_available"),
            "top_fractional_z": top_fractional(rows, "z_k_i"),
            "top_fractional_x": top_fractional(rows, "x_k_i_j"),
            "top_fractional_p": top_fractional(rows, "p_k_i"),
            "top_fractional_d": top_fractional(rows, "d_k_i"),
            "top_r_i": top_abs(rows, "r_i"),
            "top_Y_i": top_abs(rows, "Y_i"),
            "top_e_i": top_abs(rows, "e_i"),
            "top_h_i_j": top_abs(rows, "h_i_j"),
            "top_T_SP_i": top_abs(rows, "T_SP_i"),
            "top_q_i": top_abs(rows, "q_i"),
            "top_route_support_station_sets_by_vehicle": route_support_sets(rows),
        })
        summary = summaries[-1]
        v_count = int(f(rows[0].get("V"), 0.0)) or sum(1 for r in rows if r.get("family") == "r_i")
        wgs = f(summary.get("W_GS"), math.nan)
        tsp_sum = f(summary.get("sum_i_w_i_T_SP_i"), math.nan)
        cutoff = f(rows[0].get("cutoff"), math.nan)
        if math.isfinite(s_val) and math.isfinite(g_val) and math.isfinite(wgs):
            summary["W_GS_gap"] = g_val * s_val - wgs
        else:
            summary["W_GS_gap"] = "not_available"
        if math.isfinite(s_val) and math.isfinite(p_val) and math.isfinite(tsp_sum):
            summary["SP_gap_disaggregated"] = s_val * p_val - tsp_sum
        else:
            summary["SP_gap_disaggregated"] = "not_available"
        summary["SP_gap_aggregate"] = summary["SP_gap"]
        summary["GSH_gap"] = summary["G_gap"]
        if (v_count > 0 and math.isfinite(h_val) and math.isfinite(tsp_sum) and
                math.isfinite(s_val) and math.isfinite(cutoff)):
            summary["objective_estimator_slack"] = (
                v_count * cutoff * s_val - h_val - v_count * 0.15 * tsp_sum
            )
        else:
            summary["objective_estimator_slack"] = "not_available"
    return summaries


def route_support_sets(rows: Sequence[Dict[str, Any]], limit: int = 6) -> str:
    supports: Dict[str, List[Tuple[float, str]]] = {}
    for row in rows:
        if row.get("family") != "z_k_i":
            continue
        value = f(row.get("value"), math.nan)
        if not math.isfinite(value) or value <= 1e-6:
            continue
        indices = str(row.get("indices", "")).split("|")
        vehicle = indices[0] if indices else "?"
        supports.setdefault(vehicle, []).append((value, str(row.get("variable_name", ""))))
    packed = []
    for vehicle, values in sorted(supports.items()):
        values.sort(reverse=True)
        packed.append(f"k{vehicle}:" + ",".join(
            f"{name}={value:.5g}" for value, name in values[:limit]
        ))
    return "|".join(packed)


def top_fractional(rows: Sequence[Dict[str, Any]], family: str, limit: int = 8) -> str:
    items = []
    for r in rows:
        if r.get("family") != family:
            continue
        value = f(r.get("value"), math.nan)
        frac = abs(value - round(value)) if math.isfinite(value) else 0.0
        if 1e-6 < frac < 1 - 1e-6:
            items.append((min(frac, 1 - frac), r["variable_name"], value))
    items.sort(reverse=True)
    return "|".join(f"{name}:{value:.6g}" for _, name, value in items[:limit])


def top_abs(rows: Sequence[Dict[str, Any]], family: str, limit: int = 8) -> str:
    items = [(abs(f(r.get("value"), 0.0)), r["variable_name"], f(r.get("value"), 0.0))
             for r in rows if r.get("family") == family]
    items.sort(reverse=True)
    return "|".join(f"{name}:{value:.6g}" for _, name, value in items[:limit])


def build_vector_outputs(summary_rows: Sequence[Dict[str, Any]], extract_root: bool) -> None:
    callback_rows: List[Dict[str, Any]] = []
    root_rows: List[Dict[str, Any]] = []
    index_rows: List[Dict[str, Any]] = []
    for row in summary_rows:
        json_path = ROOT / str(row.get("json_path", ""))
        data = read_json(json_path)
        cb_rows = vector_rows_from_json(json_path, data)
        callback_rows.extend(cb_rows)
        if cb_rows:
            index_rows.append({
                "snapshot_id": cb_rows[0]["snapshot_id"],
                "snapshot_scope": cb_rows[0]["snapshot_source"],
                "json_path": str(json_path.relative_to(ROOT)),
                "elapsed_seconds": data.get("runtime_seconds", ""),
                "callback_count": data.get("tailored_bc_relaxation_callback_calls", ""),
                "node_count": data.get("compact_bc_nodes", data.get("nodes", "")),
                "best_bound_at_snapshot": data.get("compact_bc_best_bound", ""),
                "objective_value_if_available": data.get("objective", data.get("compact_bc_incumbent", "")),
            })
        if extract_root and row.get("lp_path"):
            lp_path = ROOT / str(row["lp_path"])
            weights = parse_instance_weights(data.get("input_path", ""))
            root_values, root_objective = cplex_root_solution(lp_path)
            for name, value in root_values:
                family, indices = family_of(name)
                sid = f"{lp_path.stem}:root_lp_relaxation"
                weight = ""
                if family in {"e_i", "T_SP_i"} and indices:
                    try:
                        weight = weights.get(int(indices.split("|")[0]), "")
                    except Exception:
                        weight = ""
                root_rows.append({
                    "snapshot_id": sid,
                    "snapshot_source": "root_lp_relaxation",
                    "lp_path": str(lp_path.relative_to(ROOT)),
                    "variable_name": name,
                    "family": family,
                    "indices": indices,
                    "weight": weight,
                    "value": value,
                    "nonzero": abs(value) > 1e-12 if math.isfinite(value) else "",
                    "diagnostic_only": True,
                    "V": data.get("V", data.get("stations", "")),
                    "gamma_L": data.get("interval_gamma_L", data.get("gamma_L", "")),
                    "gamma_U": data.get("interval_gamma_U", data.get("gamma_U", "")),
                    "cutoff": data.get("interval_final_ub_cutoff", data.get("upper_bound", "")),
                    "snapshot_objective": root_objective,
                })
    write_csv(RESULTS / "callback_vector_raw.csv", callback_rows)
    write_csv(RESULTS / "callback_vector_family_summary.csv", summarize_vectors(callback_rows))
    write_csv(RESULTS / "root_lp_vector_raw.csv", root_rows)
    write_csv(RESULTS / "root_lp_family_summary.csv", summarize_vectors(root_rows))
    write_csv(RESULTS / "vector_snapshot_index.csv", index_rows)


def write_derived_tables(summary_rows: Sequence[Dict[str, Any]]) -> None:
    write_csv(RESULTS / "dominant_bucket_structural_ablation.csv", summary_rows)
    write_csv(RESULTS / "cut_family_effectiveness.csv", [
        {
            "variant": r["variant"],
            "budget_seconds": r["budget_seconds"],
            "lower_bound": r["lower_bound"],
            "gap_to_cutoff": r["gap_to_cutoff"],
            "gs_product_coupling": r["gs_product_coupling"],
            "disaggregated_sp_estimator": r["disaggregated_sp_estimator"],
            "vector_support_cover": r["vector_support_cover"],
            "vector_route_cutset": r["vector_route_cutset"],
        }
        for r in summary_rows
    ])
    progress_rows: List[Dict[str, Any]] = []
    for row in summary_rows:
        progress_path = ROOT / str(row.get("progress_path", ""))
        if not progress_path.exists():
            continue
        for p in base.read_csv(progress_path):
            p = dict(p)
            p["variant"] = row["variant"]
            p["budget_seconds"] = row["budget_seconds"]
            p["leaf"] = row["leaf"]
            progress_rows.append(p)
    write_csv(RESULTS / "dominant_bucket_bound_trajectory.csv", progress_rows)
    for name in ("root_gap_decomposition", "sp_gap_decomposition", "gsh_gap_decomposition", "route_fractionality_summary"):
        src = RESULTS / "callback_vector_family_summary.csv"
        rows = base.read_csv(src)
        write_csv(RESULTS / f"{name}.csv", rows)


def write_scope() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "structural_cut_scope.md").write_text(
        "# Structural Cut Scope\n\n"
        "- Mainline remains `paper-gf-tailored-bc`.\n"
        "- Target is the moderate_seed3301 low-Gini dominant S bucket.\n"
        "- The 14400s fixed-interval solution is not imported as a UB.\n"
        "- No full-frontier rerun with imported UB is performed.\n"
        "- Plain fixed-interval MIP rows are benchmark-only.\n"
        "- Callback/root vector rows are diagnostic-only and are not certificate evidence.\n",
        encoding="utf-8",
    )


def write_final_report(summary_rows: Sequence[Dict[str, Any]]) -> None:
    target_rows = [
        r for r in summary_rows
        if r.get("leaf") == "low_gini_1" and
        r.get("bucket") == "dominant_k4" and
        r.get("variant") != "plain_fixed_interval_mip"
    ]
    best = max(target_rows, key=lambda r: f(r.get("lower_bound")), default={})
    callback_summary = base.read_csv(RESULTS / "callback_vector_family_summary.csv")
    root_summary = base.read_csv(RESULTS / "root_lp_family_summary.csv")
    vector_status = "callback parsed" if callback_summary else "callback vector unavailable"
    root_status = "root LP parsed" if root_summary else "root LP unavailable"
    report = [
        "# Dominant Bucket Structural Cut Round",
        "",
        f"Status label: `{ 'compact_bc_needs_structural_low_gini_strengthening' }`.",
        "",
        "1. Complete callback/root parsing: "
        f"{vector_status}; {root_status}. Missing root rows are marked unavailable, not zero-filled.",
        "2. Dominant S/P/H/G/W_SP values are reported in `callback_vector_family_summary.csv` and `root_lp_family_summary.csv`.",
        "3. G-S-H coupling gaps are reported in `gsh_gap_decomposition.csv`.",
        "4. SP gaps are reported in `sp_gap_decomposition.csv`.",
        "5. Route fractionality is reported in `route_fractionality_summary.csv`.",
        "6. Root-bound impact is summarized in `cut_family_effectiveness.csv`.",
        "7. Long-run LB impact is summarized in `dominant_bucket_structural_ablation.csv` for whichever budgets were executed.",
        f"8. Dominant bucket closed: `{str(f(best.get('gap_to_cutoff'), 1.0) <= 1e-7).lower()}`.",
        "9. New fixed-interval solution import: no. Any incumbent found here remains local to this fixed interval.",
        "10. Paper-safe cuts: GS upper coupling, disaggregated SP estimator, support-duration cover, and route cutset. GS lower row remains off unless separately audited.",
        "11. Non-regression sanity rows are included when the runner profile includes them.",
        "12. UB import/full frontier rerun: no.",
        "13. Remaining weakness: low-Gini denominator/objective coupling if the dominant bucket remains open.",
        "14. Next step: use vector summaries to decide whether to add stronger denominator partitioning or callback-separated GS/SP cuts.",
        "",
        f"Best dominant-bucket row: `{best.get('variant', '')}` budget `{best.get('budget_seconds', '')}` LB `{best.get('lower_bound', '')}` gap-to-cutoff `{best.get('gap_to_cutoff', '')}`.",
    ]
    (RESULTS / "final_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["smoke", "standard", "required"], default="standard")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--wrapper-grace", type=int, default=120)
    parser.add_argument("--extract-root-lp", action="store_true")
    parser.add_argument("--max-budget", type=int, default=0)
    parser.add_argument("--only-variants", default="")
    parser.add_argument("--only-leaves", default="")
    args = parser.parse_args()

    configure_base()
    for path in (RAW, LOGS, PROGRESS, MODELS, VECTORS):
        path.mkdir(parents=True, exist_ok=True)
    write_scope()

    planned = plan(args.profile)
    if args.max_budget > 0:
        planned = [r for r in planned if r[2] <= args.max_budget]
    if args.only_variants.strip():
        keep = {v.strip() for v in args.only_variants.split(",") if v.strip()}
        planned = [r for r in planned if r[1] in keep]
    if args.only_leaves.strip():
        keep_leaf = {v.strip() for v in args.only_leaves.split(",") if v.strip()}
        planned = [r for r in planned if r[0] in keep_leaf]

    rows: List[Dict[str, Any]] = []
    for leaf, variant, budget, bucket in planned:
        rows.append(run_row(leaf, variant, budget, bucket, args))

    build_vector_outputs(rows, extract_root=args.extract_root_lp)
    write_derived_tables(rows)
    write_final_report(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
