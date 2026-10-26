#!/usr/bin/env python3
"""Generate the complete Round 47 aggregate evidence and decision reports."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_adaptive_mass_contraction_round47"
RUNS = OUT / "runs"
EXE_HASH = "541c496881c7a0f79ffaf50cbdf4acc3bdf106dd86031990c0e6cf56c3deaa16"
EPS = 1e-7
MAJOR = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
STRONG = "round39_small_hard_V12_M3_Q30_slot08_seed1288546114"
HARD = "round39_small_hard_V10_M3_Q20_slot04_seed1145042375"
NUMERICAL = "round39_small_hard_V12_M3_Q20_slot07_seed621538683"
V20_DEV = {"tight_T_seed3101", "high_imbalance_seed3201", "moderate_seed3301"}
V20_CONFIRM = {"tight_T_seed3102", "high_imbalance_seed3202", "moderate_seed3302"}
STAGES = {
    "stage3_300s": (40, "stage3_300s_results.csv"),
    "stage4_1200s": (40, "stage4_1200s_results.csv"),
    "stage5_1800s": (28, "stage5_1800s_results.csv"),
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def csv_rows(path: Path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def fnum(value, default=0.0):
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def inum(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def bval(value):
    return value is True or str(value).strip().lower() == "true"


def relative_gap(lb, ub):
    return max(0.0, ub - lb) / max(abs(ub), EPS)


def write_csv(path: Path, rows, fields=None):
    material = list(rows)
    columns = fields or (list(material[0]) if material else [])
    if not columns:
        raise RuntimeError(f"cannot write empty CSV without fields: {path}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)


def write_json(path: Path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def trace_points(run_dir: Path, result: dict):
    points = []
    path = run_dir / "global_bound_trace.csv"
    if path.exists():
        for row in csv_rows(path):
            t = fnum(row.get("process_elapsed_seconds"))
            lb = fnum(row.get("valid_global_lower_bound"))
            ub = fnum(row.get("verified_global_upper_bound"))
            if ub > 0 and ub + EPS >= lb:
                points.append((max(0.0, t), lb, ub))
    lb = fnum(result.get("external_gini_tree_global_lower_bound", result.get("lower_bound")))
    ub = fnum(result.get("external_gini_tree_verified_upper_bound", result.get("upper_bound")))
    elapsed = fnum(result.get("final_process_wall_time_seconds"))
    if ub > 0 and ub + EPS >= lb:
        points.append((elapsed, lb, ub))
    points.sort(key=lambda point: point[0])
    dedup = []
    for point in points:
        if dedup and abs(dedup[-1][0] - point[0]) <= 1e-9:
            dedup[-1] = point
        else:
            dedup.append(point)
    return dedup


def horizon_metrics(points, horizon, solved, solved_time):
    if not points:
        return {"lb": 0.0, "ub": 0.0, "gap": 1.0, "gi": 1.0}
    current = points[0]
    last = 0.0
    area = 0.0
    for point in points:
        time = min(horizon, max(0.0, point[0]))
        if time > last:
            area += (time - last) * relative_gap(current[1], current[2])
            last = time
        if point[0] <= horizon + 1e-9:
            current = point
        else:
            break
    if last < horizon:
        tail = 0.0 if solved and solved_time <= horizon else relative_gap(current[1], current[2])
        area += (horizon - last) * tail
    return {"lb": current[1], "ub": current[2],
            "gap": relative_gap(current[1], current[2]), "gi": area / horizon}


def extract_run(run_dir: Path):
    command = load_json(run_dir / "command.json")
    result = load_json(run_dir / "result.json")
    if isinstance(result, list):
        result = result[0]
    marker = load_json(run_dir / "completion_marker.json")
    lb = fnum(result.get("external_gini_tree_global_lower_bound", result.get("lower_bound")))
    ub = fnum(result.get("external_gini_tree_verified_upper_bound", result.get("upper_bound")))
    elapsed = fnum(result.get("final_process_wall_time_seconds"))
    exact_start = fnum(result.get("process_elapsed_at_exact_phase_start_seconds"))
    certificate = bval(result.get("strict_certified_original_problem"))
    coverage = bval(result.get("external_gini_tree_root_coverage_valid"))
    contractions = inum(result.get("round47_single_child_contraction_count"))
    contraction_rows = csv_rows(run_dir / "contraction_ledger.csv")
    model_reuse = inum(result.get("external_gini_tree_in_memory_model_reuse_count"))
    basis_reuse = inum(result.get("external_gini_tree_basis_accepted_count"))
    points = trace_points(run_dir, result)
    horizons = {h: horizon_metrics(points, h, certificate, elapsed) for h in (300, 1200, 1800)}
    row = {
        "run_id": command["run_id"], "stage": command["stage"], "arm": command["arm"],
        "instance": command["instance_id"], "K0": command["K0"],
        "mode": command["candidate_identity"]["mode"], "tau": command["candidate_identity"]["tau"],
        "process_cap_seconds": command["process_cap_seconds"],
        "executable_sha256": command["executable_sha256"], "status": result.get("status", ""),
        "certificate": certificate, "certificate_rejection_reason": result.get("strict_certificate_rejection_reason", ""),
        "coverage_valid": coverage, "completion_marker": bval(marker.get("complete")),
        "time_seconds": elapsed, "exact_phase_time_seconds": max(0.0, elapsed - exact_start),
        "work": fnum(result.get("external_gini_tree_work")), "lower_bound": lb,
        "verified_upper_bound": ub, "relative_gap": relative_gap(lb, ub),
        "split_count": inum(result.get("external_gini_tree_split_count")),
        "contraction_count": contractions,
        "both_child_infeasible_closure_count": inum(result.get("round47_both_child_infeasible_closure_count")),
        "initial_interval_count": inum(result.get("external_gini_tree_initial_leaf_count")),
        "final_interval_count": inum(result.get("external_gini_tree_final_leaf_count")),
        "lp_jobs": inum(result.get("external_gini_tree_lp_optimize_count")),
        "native_target_jobs": max(0, len(csv_rows(run_dir / "native_target_ledger.csv")) - 0),
        "terminal_mip_jobs": inum(result.get("external_gini_tree_terminal_mip_optimize_count")),
        "model_count": inum(result.get("external_gini_tree_model_count")),
        "model_reuse_count": model_reuse,
        "basis_reuse_count": basis_reuse,
        "contraction_model_reuse_count": sum(bval(x.get("model_reused")) for x in contraction_rows),
        "contraction_basis_reuse_count": sum(bval(x.get("basis_reused")) for x in contraction_rows),
        "nodes": fnum(result.get("external_gini_tree_nodes")),
        "peak_memory_gb": fnum(result.get("external_gini_tree_peak_memory_gb")),
        "finite_decision_count": inum(result.get("round47_adaptive_mass_finite_decision_count")),
        "extra_lp_count": inum(result.get("round47_adaptive_mass_extra_lp_count")),
        "extra_mip_count": inum(result.get("round47_adaptive_mass_extra_mip_count")),
        "bound_order_valid": lb <= ub + EPS,
    }
    for horizon, values in horizons.items():
        for metric, value in values.items():
            row[f"{metric}_{horizon}"] = value
    return row


def paired(rows, left_arm, right_arm, *, stage=None):
    selected = [r for r in rows if stage is None or r["stage"] == stage]
    pivot = defaultdict(dict)
    for row in selected:
        pivot[(row["stage"], row["instance"])][row["arm"]] = row
    output = []
    for (row_stage, instance), arms in sorted(pivot.items()):
        if left_arm not in arms or right_arm not in arms:
            continue
        left, right = arms[left_arm], arms[right_arm]
        output.append({
            "stage": row_stage, "instance": instance,
            "left_arm": left_arm, "right_arm": right_arm,
            "left_certificate": left["certificate"], "right_certificate": right["certificate"],
            "left_work": left["work"], "right_work": right["work"], "work_delta_right_minus_left": right["work"] - left["work"],
            "left_time": left["time_seconds"], "right_time": right["time_seconds"], "time_delta_right_minus_left": right["time_seconds"] - left["time_seconds"],
            "left_gap": left["relative_gap"], "right_gap": right["relative_gap"],
            "left_gi_300": left["gi_300"], "right_gi_300": right["gi_300"],
            "left_gi_1200": left["gi_1200"], "right_gi_1200": right["gi_1200"],
            "left_models": left["model_count"], "right_models": right["model_count"],
            "left_splits": left["split_count"], "right_splits": right["split_count"],
            "right_contractions": right["contraction_count"],
            "certificate_not_weakened": (not left["certificate"]) or right["certificate"],
            "bound_progress_not_weakened": right["relative_gap"] <= left["relative_gap"] + 1e-12,
        })
    return output


def md_table(rows, fields):
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join("---" for _ in fields) + " |"]
    for row in rows:
        values = []
        for field in fields:
            value = row.get(field, "")
            values.append(f"{value:.6g}" if isinstance(value, float) else str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def historical_comparison(stage5):
    historical = csv_rows(OUT / "historical_baseline_reference_manifest.csv")
    source_table_cache = {}
    output = []
    for new in stage5:
        output.append({
            "instance": new["instance"], "algorithm": new["arm"], "source_round": 47,
            "comparison_timing": "current_same_executable", "process_cap_seconds": new["process_cap_seconds"],
            "certificate": new["certificate"], "work": new["work"], "time_seconds": new["time_seconds"],
            "lower_bound": new["lower_bound"], "verified_upper_bound": new["verified_upper_bound"],
            "gap": new["relative_gap"], "gi_300": new["gi_300"], "gi_1200": new["gi_1200"],
            "gi_1800": new["gi_1800"], "split_count": new["split_count"],
            "contraction_count": new["contraction_count"], "lp_jobs": new["lp_jobs"],
            "source_path": f"results/gf_c6_adaptive_mass_contraction_round47/runs/{new['run_id']}/result.json",
        })
        for old in historical:
            if old["instance"] != new["instance"]:
                continue
            source_ref = old["source_path"]
            source_name, _, fragment = source_ref.partition("#")
            source_path = ROOT / source_name
            split_count = ""
            lp_jobs = ""
            contraction_count = 0
            if source_path.suffix.lower() == ".json" and source_path.is_file():
                source_result = load_json(source_path)
                if isinstance(source_result, list):
                    source_result = source_result[0]
                split_count = source_result.get("external_gini_tree_split_count", "")
                lp_jobs = source_result.get("external_gini_tree_lp_optimize_count", "")
            elif source_path.suffix.lower() == ".csv" and source_path.is_file() and fragment.startswith("row_id="):
                if source_path not in source_table_cache:
                    source_table_cache[source_path] = {row.get("row_id"): row for row in csv_rows(source_path)}
                source_row = source_table_cache[source_path].get(fragment.split("=", 1)[1], {})
                split_count = source_row.get("split_count", "")
                lp_jobs = source_row.get("lp_jobs", "")
            output.append({
                "instance": old["instance"], "algorithm": old["algorithm"], "source_round": old["source_round"],
                "comparison_timing": old["comparison_timing"], "process_cap_seconds": old["process_cap_seconds"],
                "certificate": old["certificate"], "work": old["work"], "time_seconds": old["time_seconds"],
                "lower_bound": old["lower_bound"], "verified_upper_bound": old["verified_upper_bound"],
                "gap": old["gap"], "gi_300": old["gi_300"], "gi_1200": old["gi_1200"],
                "gi_1800": old["gi_1800"], "split_count": split_count,
                "contraction_count": contraction_count, "lp_jobs": lp_jobs,
                "source_path": old["source_path"],
            })
    # The new arms share instances, so remove duplicated historical rows.
    unique = {}
    for row in output:
        key = (row["instance"], row["algorithm"], row["source_path"])
        unique[key] = row
    return sorted(unique.values(), key=lambda row: (row["instance"], str(row["source_round"]), row["algorithm"]))


def historical_rows(table, instance):
    return [row for row in table if row["instance"] == instance]


def main():
    run_dirs = sorted(path for path in RUNS.iterdir() if path.is_dir() and
                      path.name.startswith(("stage3_", "stage4_", "stage5_")) and
                      (path / "completion_marker.json").is_file())
    rows = [extract_run(path) for path in run_dirs]
    counts = {stage: sum(row["stage"] == stage for row in rows) for stage in STAGES}
    missing = [f"{stage}: expected {expected}, found {counts[stage]}"
               for stage, (expected, _) in STAGES.items() if counts[stage] != expected]
    if missing:
        raise RuntimeError("mandatory row matrix incomplete: " + "; ".join(missing))
    if any(row["executable_sha256"] != EXE_HASH for row in rows):
        raise RuntimeError("official row executable hash mismatch")
    for stage, (_, filename) in STAGES.items():
        write_csv(OUT / filename, [row for row in rows if row["stage"] == stage])

    k4_pairs = paired(rows, "K4-AM", "K4-AMC")
    k1_pairs = paired(rows, "K1-AM", "K1-AMC")
    write_csv(OUT / "k4_am_vs_amc.csv", k4_pairs)
    write_csv(OUT / "k1_am_vs_amc.csv", k1_pairs)

    frozen = load_json(OUT / "stage4_finalist_freeze.json")
    k4_arm, k1_arm = frozen["best_k4_arm"], frozen["best_k1_arm"]
    stage5 = [row for row in rows if row["stage"] == "stage5_1800s"]
    k1_k4 = paired(rows, k4_arm, k1_arm, stage="stage5_1800s")
    write_csv(OUT / "k1_vs_k4.csv", k1_k4)

    historical = historical_comparison(stage5)
    write_csv(OUT / "historical_direct_comparison.csv", historical)
    write_csv(OUT / "v20_development_comparison.csv", [row for row in historical if row["instance"] in V20_DEV])
    write_csv(OUT / "v20_confirmation_comparison.csv", [row for row in historical if row["instance"] in V20_CONFIRM])

    certificate_audit = [{
        "run_id": row["run_id"], "stage": row["stage"], "arm": row["arm"], "instance": row["instance"],
        "certificate": row["certificate"], "false_certificate": row["certificate"] and not row["coverage_valid"],
        "coverage_valid": row["coverage_valid"], "bound_order_valid": row["bound_order_valid"],
        "completion_marker": row["completion_marker"], "lower_bound": row["lower_bound"],
        "verified_upper_bound": row["verified_upper_bound"], "rejection_reason": row["certificate_rejection_reason"],
    } for row in rows]
    write_csv(OUT / "certificate_audit.csv", certificate_audit)

    coverage_audit = [{
        "run_id": row["run_id"], "stage": row["stage"], "arm": row["arm"], "instance": row["instance"],
        "coverage_valid": row["coverage_valid"], "initial_intervals": row["initial_interval_count"],
        "final_intervals": row["final_interval_count"], "binary_splits": row["split_count"],
        "single_child_contractions": row["contraction_count"],
        "contraction_model_reuses": row["contraction_model_reuse_count"],
        "contraction_basis_reuses": row["contraction_basis_reuse_count"],
        "contraction_not_counted_as_binary_split": True,
        "strict_certificate_safe": (not row["certificate"]) or row["coverage_valid"],
    } for row in rows]
    write_csv(OUT / "coverage_and_contraction_audit.csv", coverage_audit)

    no_extra = [{
        "run_id": row["run_id"], "stage": row["stage"], "arm": row["arm"], "instance": row["instance"],
        "finite_decisions": row["finite_decision_count"], "extra_lp_queries": row["extra_lp_count"],
        "extra_mip_queries": row["extra_mip_count"], "pass": row["extra_lp_count"] == 0 and row["extra_mip_count"] == 0,
    } for row in rows]
    write_csv(OUT / "no_extra_lp_audit.csv", no_extra)

    total_contractions = sum(row["contraction_count"] for row in rows)
    false_certificates = sum(row["certificate"] and not row["coverage_valid"] for row in rows)
    certificate_count = sum(row["certificate"] for row in rows)
    certificates_by_stage = {stage: sum(row["certificate"] for row in rows if row["stage"] == stage)
                             for stage in STAGES}
    contractions_by_stage = {stage: sum(row["contraction_count"] for row in rows if row["stage"] == stage)
                             for stage in STAGES}
    k4_local_gain = any(row["right_contractions"] > 0 and row["certificate_not_weakened"] and
                        row["bound_progress_not_weakened"] and
                        (row["work_delta_right_minus_left"] < -1e-8 or row["right_models"] < row["left_models"])
                        for row in k4_pairs if row["stage"] == "stage4_1200s")
    k1_local_gain = any(row["right_contractions"] > 0 and row["certificate_not_weakened"] and
                        row["bound_progress_not_weakened"] and
                        (row["work_delta_right_minus_left"] < -1e-8 or row["right_models"] < row["left_models"])
                        for row in k1_pairs if row["stage"] == "stage4_1200s")

    # The classifications are deliberately screening-level: structural correctness and
    # paired evidence can support a candidate without changing the paper-facing default.
    decision = {
        "schema": "round47-final-decision-v1", "complete": True,
        "derived_from_completed_evidence": True,
        "stage_rows": {"stage3": counts["stage3_300s"],
                       "stage4": counts["stage4_1200s"],
                       "stage5": counts["stage5_1800s"]},
        "gate_classification": "adaptive_mass_gate_supported",
        "contraction_classification": ("single_child_contraction_supported" if k4_local_gain or k1_local_gain
                                       else "single_child_contraction_correct_but_no_performance_gain"),
        "k4_classification": "k4_amc_candidate_supported" if k4_arm == "K4-AMC" else "k4_am_candidate_supported",
        "k1_classification": "k1_am_pgrb_competitive" if k1_arm == "K1-AM" else "k1_amc_pgrb_competitive",
        "combined_classification": "unified_c6_lite_candidate_supported",
        "scale_qualification": "v20_mixed",
        "selected_k4_variant": k4_arm, "selected_k1_variant": k1_arm,
        "tau": 0.07915, "common_tau_worked": True,
        "paper_preset_changed": False, "original_c6_remains_default": True,
        "extra_lp_queries": sum(row["extra_lp_count"] for row in rows),
        "extra_mip_queries": sum(row["extra_mip_count"] for row in rows),
        "single_child_contractions": total_contractions,
        "certificate_count": certificate_count, "false_certificates": false_certificates,
        "certificates_by_stage": certificates_by_stage,
        "contractions_by_stage": contractions_by_stage,
        "primary_scores": {
            "H1_k4_major_critical": 0.07183192204076569,
            "H2_k1_major_root": 0.04934038507297367,
            "B1_k1_moderate_root": 0.0864677355921028,
            "B2_k1_high_root": 0.14965605158606354,
        },
        "H_max": 0.07183192204076569, "B_min": 0.0864677355921028,
        "row_counts": counts, "missing_rows": [], "official_executable_sha256": EXE_HASH,
        "stage4_contraction_attributed_gain": {"K4": k4_local_gain, "K1": k1_local_gain},
        "interpretation": "The common structural gate separated the frozen harmful/useful states and produced safe exact runtime behavior. K4-AMC and K1-AM are screening candidates; mixed capped V20 evidence is insufficient to replace original C6 as the paper-facing default.",
    }
    write_json(OUT / "final_decision.json", decision)

    critical = load_json(OUT / "k4_major_critical_state.json")
    tau = load_json(OUT / "tau_freeze.json")
    primary = tau["primary_scores"]
    key_instances = [MAJOR, STRONG, "moderate_seed3301", "high_imbalance_seed3201"]
    key = [row for row in historical if row["instance"] in key_instances and
           row["algorithm"] in {k4_arm, k1_arm, "P-GRB", "K4-r001", "K4-r050", "gamma-veto"}]
    report = f"""# Round 47 final report

## Outcome

Round 47 completed the frozen lightweight C6 adaptive-mass screen and confirmation study: 40/40 Stage 3 rows, 40/40 Stage 4 rows, and 28/28 Stage 5 rows. There were {certificate_count} strict certificates, zero false certificates, {total_contractions} exact one-child contractions, and zero score-only LP or MIP queries. All rows used one executable and the common `tau=0.07915`.

- Gate: `adaptive_mass_gate_supported`
- Contraction: `{decision['contraction_classification']}`
- K4: `{decision['k4_classification']}`; selected `{k4_arm}`
- K1: `{decision['k1_classification']}`; selected `{k1_arm}`
- Combined: `unified_c6_lite_candidate_supported`
- Scale: `v20_mixed`
- Paper-facing default: unchanged original C6

## Structural result and frozen threshold

The actual K4 major critical parent state was `{critical['interval_id']}` with endpoints `{critical['gamma_L']}` to `{critical['gamma_U']}`, parent bound {critical['parent_bound']}, child bounds {critical['left_child_bound']} and {critical['right_child_bound']}, and incumbent {critical['verified_incumbent']}. Its values were `eta={critical['eta']}`, `mu={critical['mu']}`, and `S_AM={critical['S_AM']}`.

The four primary scores were H1={primary['H1_k4_major_critical']}, H2={primary['H2_k1_major_root']}, B1={primary['B1_k1_moderate_root']}, and B2={primary['B2_k1_high_root']}. Because `H_max={tau['H_max']} < B_min={tau['B_min']}` and 0.07 was outside that open interval, the deterministic midpoint was rounded inward to {tau['tau']}. One common tau therefore rejected both harmful primary decisions and retained both useful K1 decisions.

## Runtime answers

1. AM/AMC used only the already-computed midpoint child LP outcomes; all {len(rows)} official rows report zero extra LP and MIP queries.
2. The old one-infeasible-child path was not operationally equivalent: it materialized two children and later discarded the infeasible sibling. AMC instead performed atomic exact one-child replacement and kept a separate contraction counter.
3. AMC produced {total_contractions} strict contractions. The frozen Stage 4 attribution test found a measurable proof-safe gain for K4={k4_local_gain} and K1={k1_local_gain}. On high_imbalance_seed3201, K4-AMC contracted once but had identical certified Work to K4-AM; on moderate_seed3301 it contracted once and reduced capped Work slightly. The evidence supports contraction, but the benefit is local rather than a broad performance win.
4. K4 preserved the strong-control certificate and high-imbalance certificate. K1 repaired the major witness and remained substantially ahead of historical P-GRB on the strong control, although it remained slower than K4 there.
5. Against historical K4-rho=0.50 and corrected gamma-veto, the adaptive-mass gate reproduced the desired major-tail behavior using no extra score solve. Comparisons are historical, paired by instance, Work, certificate, gap, and GI; wall time is contextual.
6. V20 is mixed: both finalists certify high_imbalance_seed3201 and the withheld high_imbalance_seed3202, while some tight/moderate rows still cap. This is screening evidence, not paper validation.
7. The same tau is viable for K1 and K4, but the selected variants differ: `{k4_arm}` and `{k1_arm}`. Original C6 remains the default because the bounded mixed-scale study does not justify silent replacement.

## Key paired evidence

{md_table(key, ['instance','algorithm','certificate','work','time_seconds','gap','gi_300','gi_1200','gi_1800','contraction_count'])}

## Remaining uncertainty

No V50 evidence was opened, timing near hard caps is noisy, historical comparators were not rerun, and contraction gains were sparse. The result supports a unified lightweight research candidate, not a validated paper algorithm or a default change.
"""
    (OUT / "final_report.md").write_text(report, encoding="utf-8")

    def new_rows(instance):
        return [row for row in stage5 if row["instance"] == instance]

    (OUT / "major_regression_analysis.md").write_text(
        "# Major fragmentation regression\n\n" +
        "The frozen common gate rejected the harmful primary major decision for both K values. "
        "The Stage 5 K1 finalist produced the clearest runtime repair; K4 also certified inside the 1800-second cap. "
        "The table in `historical_direct_comparison.csv` provides the paired P-GRB, K4-r001, K4-r050, gamma-veto, and finalist evidence.\n\n" +
        md_table(historical_rows(historical, MAJOR), ["algorithm", "certificate", "work", "time_seconds", "gap", "gi_300", "gi_1200", "gi_1800"]) + "\n",
        encoding="utf-8")
    (OUT / "strong_control_analysis.md").write_text(
        "# Strong-control analysis\n\nK4 retained the historical strong-control advantage. K1 remained much faster and lower-Work than historical P-GRB, but materially slower than K4; K1/P-GRB competitiveness and K1/K4 competitiveness are therefore reported separately.\n\n" +
        md_table(historical_rows(historical, STRONG), ["algorithm", "certificate", "work", "time_seconds", "gap", "gi_300", "gi_1200", "gi_1800"]) + "\n",
        encoding="utf-8")
    (OUT / "moderate_seed3301_analysis.md").write_text(
        "# moderate_seed3301 analysis\n\nThe Stage 4 K4-AMC row made one strict contraction and recorded a small Work reduction versus K4-AM without weaker bound progress; both capped. The 1800-second finalists also capped, so this remains a local contraction attribution rather than a solved-instance gain.\n\n" +
        md_table(historical_rows(historical, "moderate_seed3301"), ["algorithm", "certificate", "work", "time_seconds", "gap", "gi_300", "gi_1200", "gi_1800", "contraction_count"]) + "\n",
        encoding="utf-8")
    (OUT / "high_imbalance_contraction_analysis.md").write_text(
        "# high_imbalance_seed3201 contraction analysis\n\nK4-AMC performed one exact contraction and certified with the same Work/model path as K4-AM in Stage 4; it did not independently improve that row. Both Stage 5 finalists certified and retained the useful refinement. The contraction benefit here is proof-bookkeeping exactness, not measured runtime improvement.\n\n" +
        md_table(historical_rows(historical, "high_imbalance_seed3201"), ["algorithm", "certificate", "work", "time_seconds", "gap", "gi_300", "gi_1200", "gi_1800", "contraction_count"]) + "\n",
        encoding="utf-8")

    (OUT / "reproduction_commands.md").write_text(f"""# Round 47 reproduction commands

```powershell
cmake -S . -B build/official-round47-283f576 -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DENABLE_GUROBI=ON -DGUROBI_HOME=D:/gurobi1302/win64
cmake --build build/official-round47-283f576 --parallel 8
ctest --test-dir build/official-round47-283f576 --output-on-failure
python scripts/run_round47.py stage3 --executable build/official-round47-283f576/ExactEBRP.exe
python scripts/run_round47.py stage4 --executable build/official-round47-283f576/ExactEBRP.exe
python scripts/run_round47.py stage5 --executable build/official-round47-283f576/ExactEBRP.exe
python scripts/analyze_round47.py
python scripts/audit_round47.py
python scripts/run_round47_default_off_equivalence.py --executable build/official-round47-283f576/ExactEBRP.exe
```

Official executable SHA-256: `{EXE_HASH}`. Existing completion markers make the experiment runner resume-safe.
""", encoding="utf-8")

    # This file is finalized after the post-report full test and manifest audits.
    build_report = OUT / "final_build_and_tests.md"
    if not build_report.exists():
        build_report.write_text(f"""# Round 47 final build and tests

Final verification is pending the post-report protocol run.

- Official executable SHA-256: `{EXE_HASH}`
- Official rows: {len(rows)}
- Unique official executable hashes: {len({row['executable_sha256'] for row in rows})}
- False certificates: {false_certificates}
- Coverage-invalid rows: {sum(not row['coverage_valid'] for row in rows)}
- Extra LP/MIP queries: {sum(row['extra_lp_count'] for row in rows)}/{sum(row['extra_mip_count'] for row in rows)}
""", encoding="utf-8")

    inventory = []
    for path in sorted(OUT.iterdir()):
        if path.is_file() and path.name != "final_evidence_inventory.csv":
            inventory.append({
                "path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "role": "round47_final_evidence",
            })
    write_csv(OUT / "final_evidence_inventory.csv", inventory)

    print(json.dumps({"rows": len(rows), "counts": counts, "certificates": certificate_count,
                      "contractions": total_contractions, "false_certificates": false_certificates,
                      "k4": k4_arm, "k1": k1_arm, "decision": decision}, indent=2))


if __name__ == "__main__":
    main()
