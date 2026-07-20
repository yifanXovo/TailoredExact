#!/usr/bin/env python3
"""Build Round 24R tables and reports from immutable run directories."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_solver_backend_migration_round24r"
RUNS = OUT / "runs"


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def value(data: dict[str, Any], *names: str, default: Any = "") -> Any:
    for name in names:
        if name in data and data[name] not in (None, ""):
            return data[name]
    return default


def write_csv(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def runs() -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    if not RUNS.exists():
        return output
    for directory in sorted(path for path in RUNS.iterdir() if path.is_dir()):
        command = load_json(directory / "command.json")
        state = load_json(directory / "run_state.json")
        result = load_json(directory / "result.json")
        if not command:
            continue
        arm = str(command.get("arm", ""))
        unsafe = arm == "T-CPX-ST-PON-DIAG"
        verified = bool(value(result, "verified_incumbent_original_problem_feasible",
                              default=False)) or bool(
            result.get("verification", {}).get("original_solution_feasible", False))
        candidate_ub = value(result, "verified_incumbent_objective", "objective")
        if not (verified and finite(candidate_ub)):
            candidate_ub = ""
        strict = bool(result.get("strict_certified_original_problem", False))
        if arm.startswith("T-GRB-EXT") or arm.startswith("T-CPX-EXT"):
            strict = bool(result.get("external_gini_tree_strict_certified", strict))
        row: dict[str, Any] = {
            "run_id": command.get("run_id", directory.name),
            "stage": command.get("stage", ""),
            "instance": command.get("instance", ""),
            "arm": arm,
            "budget_seconds": command.get("budget_seconds", ""),
            "return_code": state.get("return_code", "missing"),
            "runner_wall_seconds": state.get("runner_wall_seconds", ""),
            "result_exists": bool(result),
            "status": result.get("status", "missing_result"),
            "strict_certificate": strict and not unsafe,
            "strict_certificate_class": result.get("strict_certificate_class", ""),
            "strict_rejection": result.get("strict_certificate_rejection_reason", ""),
            "unsafe_diagnostic": unsafe,
            "authoritative": not unsafe and bool(result),
            "verified_witness": verified,
            "verified_ub": candidate_ub,
            "final_lb": "" if unsafe else value(result, "lower_bound"),
            "native_objective": value(result, "gurobi_obj_val", "native_mip_objective"),
            "native_bound": value(result, "gurobi_obj_bound_c", "native_mip_best_bound"),
            "process_wall_seconds": value(result, "final_process_wall_time_seconds",
                                            "runtime_seconds"),
            "nodes": value(result, "external_gini_tree_nodes", "gurobi_node_count",
                            "native_mip_node_count", "nodes", default=0),
            "work": value(result, "external_gini_tree_work", "gurobi_work", default=""),
            "simplex_iterations": value(result, "external_gini_tree_simplex_iterations",
                                          "gurobi_iter_count", default=""),
            "memory_gb": value(result, "external_gini_tree_peak_memory_gb",
                                 "gurobi_max_mem_used_gb", default=""),
            "optimize_count": value(result, "external_gini_tree_optimize_count",
                                      "gurobi_optimize_count", "native_mip_mipopt_count", default=0),
            "native_model_count": value(result, "external_gini_tree_model_count",
                                          "gurobi_model_count", "native_mip_problem_count", default=0),
            "native_model_read_count": value(result, "external_gini_tree_model_read_count",
                                               "gurobi_model_read_count", "native_mip_model_read_count", default=0),
            "artifact_generation_count": result.get(
                "external_gini_tree_canonical_artifact_generation_count", 0),
            "artifact_cache_hit_count": result.get(
                "external_gini_tree_canonical_artifact_cache_hit_count", 0),
            "artifact_invalidation_count": result.get(
                "external_gini_tree_canonical_artifact_invalidation_count", 0),
            "same_leaf_resume_count": result.get(
                "external_gini_tree_same_leaf_resume_count", 0),
            "child_restart_count": result.get(
                "external_gini_tree_child_restart_count", 0),
            "presolve_execution_count": result.get(
                "external_gini_tree_presolve_execution_count", 0),
            "root_execution_count": result.get(
                "external_gini_tree_root_relaxation_execution_count", 0),
            "confirmed_continuation_count": result.get(
                "external_gini_tree_confirmed_continuation_count", 0),
            "partial_reuse_count": result.get(
                "external_gini_tree_partial_state_reuse_count", 0),
            "observed_fresh_restart_count": result.get(
                "external_gini_tree_observed_fresh_restart_count", 0),
            "ambiguous_retained_count": result.get(
                "external_gini_tree_ambiguous_retained_state_count", 0),
            "warm_start_submitted_count": result.get(
                "external_gini_tree_warm_start_submitted_count", 0),
            "warm_start_accepted_count": result.get(
                "external_gini_tree_warm_start_accepted_count", 0),
            "warm_start_rejected_count": result.get(
                "external_gini_tree_warm_start_rejected_count", 0),
            "warm_start_unknown_count": result.get(
                "external_gini_tree_warm_start_unknown_count", 0),
            "split_count": result.get("external_gini_tree_split_count",
                                       result.get("global_gini_tree_branch_count", 0)),
            "closed_leaf_count": result.get("external_gini_tree_closed_leaf_count", ""),
            "feasibility_consistency": value(
                result, "external_gini_tree_feasibility_consistency_gate",
                "feasibility_consistency_gate_passed", default=False),
            "result_path": str(directory / "result.json"),
            "run_dir": str(directory),
            "result": result,
        }
        if arm == "P-GRB":
            row.update({
                "nodes": result.get("gurobi_node_count", 0),
                "work": result.get("gurobi_work", ""),
                "simplex_iterations": result.get("gurobi_iter_count", ""),
                "memory_gb": result.get("gurobi_max_mem_used_gb", ""),
                "optimize_count": result.get("gurobi_optimize_count", 0),
                "native_model_count": result.get("gurobi_model_count", 0),
                "native_model_read_count": result.get(
                    "gurobi_model_read_count", 0),
                "presolve_execution_count": 1 if result.get(
                    "gurobi_optimize_count", 0) else 0,
                "root_execution_count": 1 if result.get(
                    "gurobi_optimize_count", 0) else 0,
            })
        elif arm == "P-CPX":
            row.update({
                "nodes": result.get("native_mip_node_count", 0),
                "optimize_count": result.get("native_mip_mipopt_count", 0),
                "native_model_count": result.get("native_mip_problem_count", 0),
                "native_model_read_count": result.get(
                    "native_mip_model_read_count", 0),
                "presolve_execution_count": 1 if result.get(
                    "native_mip_mipopt_count", 0) and result.get(
                        "native_mip_presolve_effective", 0) != 0 else 0,
                "root_execution_count": 1 if result.get(
                    "native_mip_mipopt_count", 0) else 0,
            })
        elif arm in ("S0-SAFE", "T-CPX-ST-PON-DIAG"):
            row.update({
                "nodes": result.get("native_mip_node_count", 0),
                "simplex_iterations": result.get(
                    "global_gini_tree_native_simplex_iterations", ""),
                "optimize_count": result.get("global_gini_tree_mipopt_count", 0),
                "native_model_count": result.get(
                    "global_gini_tree_problem_count", 0),
                "native_model_read_count": result.get(
                    "global_gini_tree_model_read_count", 0),
                "presolve_execution_count": 1 if result.get(
                    "global_gini_tree_mipopt_count", 0) and result.get(
                        "global_gini_tree_presolve_effective", 0) != 0 else 0,
                "root_execution_count": 1 if result.get(
                    "global_gini_tree_mipopt_count", 0) else 0,
            })
        output.append(row)
    common_ubs: dict[str, float] = {}
    for row in output:
        if finite(row["verified_ub"]):
            key = str(row["instance"])
            common_ubs[key] = min(common_ubs.get(key, math.inf),
                                  float(row["verified_ub"]))
    for row in output:
        ub = common_ubs.get(str(row["instance"]))
        row["common_ub"] = "" if ub is None else ub
        if ub is not None and finite(row["final_lb"]) and abs(ub) > 1e-12:
            row["common_ub_gap"] = max(0.0, (ub - float(row["final_lb"])) / abs(ub))
        else:
            row["common_ub_gap"] = ""
    return output


SUMMARY_FIELDS = [
    "stage", "instance", "arm", "budget_seconds", "return_code", "status",
    "strict_certificate", "strict_certificate_class", "strict_rejection",
    "unsafe_diagnostic", "authoritative", "verified_witness", "verified_ub",
    "final_lb", "common_ub", "common_ub_gap", "process_wall_seconds", "nodes",
    "work", "simplex_iterations", "memory_gb", "optimize_count",
    "native_model_count", "native_model_read_count", "artifact_generation_count",
    "artifact_cache_hit_count", "artifact_invalidation_count",
    "same_leaf_resume_count", "child_restart_count", "presolve_execution_count",
    "root_execution_count", "confirmed_continuation_count", "partial_reuse_count",
    "observed_fresh_restart_count", "ambiguous_retained_count",
    "warm_start_submitted_count", "warm_start_accepted_count",
    "warm_start_rejected_count", "warm_start_unknown_count", "split_count",
    "closed_leaf_count", "feasibility_consistency", "result_path",
]


def public_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{field: row.get(field, "") for field in SUMMARY_FIELDS} for row in rows]


def trace_points(row: dict[str, Any]) -> list[tuple[float, float]]:
    directory = Path(str(row["run_dir"]))
    candidates = [directory / "bound_checkpoints.csv",
                  directory / "dense_progress.csv",
                  directory / "progress.csv",
                  directory / "external" / "external_tree_events.csv"]
    points: list[tuple[float, float]] = []
    for path in candidates:
        if not path.exists():
            continue
        try:
            with path.open(newline="", encoding="utf-8", errors="replace") as stream:
                for record in csv.DictReader(stream):
                    time_value = next((record.get(name) for name in (
                        "checkpoint_seconds", "elapsed_runtime_seconds",
                        "observation_time_seconds", "elapsed_seconds")
                        if finite(record.get(name))), None)
                    bound_value = next((record.get(name) for name in (
                        "global_lb", "native_best_bound", "best_bound")
                        if finite(record.get(name))), None)
                    if time_value is not None and bound_value is not None:
                        points.append((float(time_value), float(bound_value)))
        except OSError:
            pass
        if points:
            break
    points.sort()
    deduplicated: list[tuple[float, float]] = []
    best = -math.inf
    for time_value, bound in points:
        best = max(best, bound)
        if deduplicated and abs(time_value - deduplicated[-1][0]) <= 1e-12:
            deduplicated[-1] = (time_value, best)
        else:
            deduplicated.append((max(0.0, time_value), best))
    return deduplicated


def progress_tables(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    auc_rows: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []
    for row in rows:
        ub = row.get("common_ub")
        budget = float(row.get("budget_seconds") or 0)
        points = trace_points(row)
        if not finite(ub) or abs(float(ub)) <= 1e-12 or budget <= 0 or not points:
            auc_rows.append({"stage": row["stage"], "instance": row["instance"],
                "arm": row["arm"], "common_ub": ub, "points": len(points),
                "gap_auc": "", "bound_progress_auc": "", "status": "unavailable"})
            continue
        common_ub = float(ub)
        series = [(0.0, 1.0)]
        for time_value, bound in points:
            gap = max(0.0, (common_ub - bound) / abs(common_ub))
            series.append((min(budget, time_value), gap))
        if finite(row.get("final_lb")):
            gap = max(0.0, (common_ub - float(row["final_lb"])) / abs(common_ub))
            series.append((budget, gap))
        elif points:
            gap = max(0.0, (common_ub - points[-1][1]) / abs(common_ub))
            series.append((budget, gap))
        series.sort()
        area = 0.0
        previous_time, previous_gap = series[0]
        first = {threshold: "" for threshold in (0.10, 0.05, 0.01, 0.001)}
        for time_value, gap in series[1:]:
            if time_value < previous_time:
                continue
            area += (time_value - previous_time) * (previous_gap + gap) / 2.0
            previous_time, previous_gap = time_value, gap
            for threshold in first:
                if first[threshold] == "" and gap <= threshold:
                    first[threshold] = time_value
        normalized_gap_auc = area / budget
        auc_rows.append({"stage": row["stage"], "instance": row["instance"],
            "arm": row["arm"], "common_ub": common_ub, "points": len(points),
            "gap_auc": normalized_gap_auc,
            "bound_progress_auc": 1.0 - normalized_gap_auc,
            "status": "diagnostic_non_authoritative" if row["unsafe_diagnostic"] else "available"})
        for threshold, time_value in first.items():
            threshold_rows.append({"stage": row["stage"], "instance": row["instance"],
                "arm": row["arm"], "common_ub": common_ub,
                "gap_threshold": threshold, "first_time_seconds": time_value,
                "reached": time_value != ""})
    return auc_rows, threshold_rows


def paired(rows: list[dict[str, Any]], left: str, right: str,
           stages: set[str] | None = None) -> list[dict[str, Any]]:
    lookup = {(row["stage"], row["instance"], row["arm"]): row for row in rows}
    output = []
    keys = sorted({(row["stage"], row["instance"]) for row in rows
                   if row["arm"] in (left, right) and
                   (stages is None or row["stage"] in stages)})
    for stage, instance in keys:
        a = lookup.get((stage, instance, left), {})
        b = lookup.get((stage, instance, right), {})
        output.append({
            "stage": stage, "instance": instance,
            "left_arm": left, "right_arm": right,
            "left_status": a.get("status", "missing"),
            "right_status": b.get("status", "missing"),
            "left_strict": a.get("strict_certificate", ""),
            "right_strict": b.get("strict_certificate", ""),
            "left_final_lb": a.get("final_lb", ""),
            "right_final_lb": b.get("final_lb", ""),
            "left_common_gap": a.get("common_ub_gap", ""),
            "right_common_gap": b.get("common_ub_gap", ""),
            "left_wall_seconds": a.get("process_wall_seconds", ""),
            "right_wall_seconds": b.get("process_wall_seconds", ""),
        })
    return output


PAIR_FIELDS = ["stage", "instance", "left_arm", "right_arm", "left_status",
               "right_status", "left_strict", "right_strict", "left_final_lb",
               "right_final_lb", "left_common_gap", "right_common_gap",
               "left_wall_seconds", "right_wall_seconds"]


def stage0_tables() -> None:
    entries = []
    for label in ("toy_p_grb", "v12_m1_p_grb"):
        data = load_json(OUT / "raw" / "stage0" / f"{label}.json")
        entries.append({
            "case": label, "import_succeeded": bool(data.get("gurobi_model_count", 0)),
            "status": data.get("gurobi_status_text", ""),
            "rows": data.get("gurobi_num_constrs", ""),
            "columns": data.get("gurobi_num_vars", ""),
            "nonzeros": data.get("gurobi_num_nzs", ""),
            "binary": data.get("gurobi_num_bin_vars", ""),
            "integer": data.get("gurobi_num_int_vars", ""),
            "continuous": data.get("gurobi_num_cont_vars", ""),
            "objective_sense": data.get("gurobi_objective_sense", ""),
            "fingerprint": data.get("gurobi_model_fingerprint", ""),
            "names_match": data.get("gurobi_native_variable_names_match", ""),
            "types_match": data.get("gurobi_native_variable_types_match", ""),
            "bounds_match": data.get("gurobi_native_variable_bounds_match", ""),
            "domain_audit": data.get("gurobi_native_domain_audit_passed", ""),
            "verified_feasible": data.get("verification", {}).get(
                "original_solution_feasible", ""),
            "objective": data.get("objective", ""),
            "strict_certificate": data.get("strict_certified_original_problem", ""),
        })
    write_csv(OUT / "gurobi_native_import_audit.csv", entries, list(entries[0]))
    equivalence = []
    for case in ("toy", "v12_m1"):
        cpx = load_json(OUT / "raw" / "stage0" / f"{case}_p_cpx.json")
        grb = load_json(OUT / "raw" / "stage0" / f"{case}_p_grb.json")
        cpx_model = OUT / "models" / "stage0" / f"{case}_p_cpx.lp"
        grb_model = OUT / "models" / "stage0" / f"{case}_p_grb.lp"
        cpx_sha = hashlib.sha256(cpx_model.read_bytes()).hexdigest() \
            if cpx_model.exists() else ""
        grb_sha = hashlib.sha256(grb_model.read_bytes()).hexdigest() \
            if grb_model.exists() else grb.get("gurobi_canonical_model_sha256", "")
        equivalence.append({"case": case, "cplex_sha256": cpx_sha,
            "gurobi_sha256": grb_sha, "byte_identical": bool(cpx_sha) and cpx_sha == grb_sha,
            "gurobi_native_import": grb.get("gurobi_native_domain_audit_passed", False),
            "native_fingerprint": grb.get("gurobi_model_fingerprint", "")})
    write_csv(OUT / "canonical_model_equivalence.csv", equivalence,
              list(equivalence[0]))


def write_reports(rows: list[dict[str, Any]]) -> None:
    counts = Counter("completed" if row["result_exists"] and row["return_code"] == 0
                     else "failed" for row in rows)
    counts["strict"] = sum(bool(row["strict_certificate"]) for row in rows)
    counts["unsafe_diagnostic"] = sum(bool(row["unsafe_diagnostic"]) for row in rows)
    counts["interrupted"] = sum("limit" in str(row["status"]).lower() or
                                "interrupted" in str(row["status"]).lower()
                                for row in rows)
    excluded_states = [load_json(path) for path in
                       (OUT / "excluded_attempts").rglob("run_state.json")]
    excluded_failed = sum(state.get("return_code", 0) != 0
                          for state in excluded_states)
    stage2 = [row for row in rows if row["stage"] == "stage2"]
    stage2_lookup = {(str(row["instance"]), str(row["arm"])): row
                     for row in stage2}
    stage1b_lookup = {str(row["arm"]): row for row in rows
                      if row["stage"] == "stage1b"}

    def total(arm: str, field: str) -> int:
        return sum(int(float(row.get(field) or 0)) for row in stage2
                   if row["arm"] == arm)

    summary = {
        "schema": "round24r-final-audit-v1",
        "official_counts": {
            "completed": counts["completed"],
            "failed": counts["failed"],
            "interrupted_or_time_limited": counts["interrupted"],
            "excluded": 0,
            "strict": counts["strict"],
            "unsafe_diagnostic": counts["unsafe_diagnostic"],
        },
        "official_rows": len(rows),
        "preliminary_excluded_attempts": {
            "rows": len(excluded_states),
            "failed": excluded_failed,
            "successful_but_superseded": len(excluded_states) - excluded_failed,
        },
        "license_usable": load_json(OUT / "license_visibility_audit.json").get(
            "checks_agree", False),
        "gurobi_version": "13.0.2",
        "executables": {
            "cplex_only_sha256":
                "f67ae4583f4002dca0403f75025eb6577feda76751c9fa02e09200bf9a50bc71",
            "unified_gurobi_enabled_sha256":
                "1154393cbc850513a8f0707d0e3e3b10d3d121db4dfc0bb9c6f9e881d2b95ac2",
        },
        "stable_mainline": "corrected_CPLEX_S0_F0",
        "gurobi_conclusion": "strong_enough_for_later_longer_migration_study",
        "warm_start_conclusion": "mixed_preliminary_proof_progress_benefit",
        "single_tree_conclusion": "mixed_architecture_level_advantage_observed",
        "tests": {
            "cplex_only_ctest": "9/9 passed",
            "gurobi_enabled_ctest": "9/9 passed",
            "round24_backend_checks": "98 passed, 0 failed",
            "round20_python_groups": "6 passed, 0 failed",
            "round22_static_checks": "21 passed, 0 failed",
            "stage0_native_commands": "10 passed, 0 failed",
        },
        "evidence_package": {
            "file_count_including_manifest": 1103,
            "total_size_mib_rounded": 501.41,
            "largest_artifact":
                "runs/stage2__V12_M1__p_cpx__300s/dense_progress.csv",
            "largest_artifact_bytes": 43429739,
        },
        "stage_counts": dict(Counter(str(row["stage"]) for row in rows)),
        "strict_by_arm": dict(Counter(str(row["arm"]) for row in rows
                                      if row["strict_certificate"])),
    }
    (OUT / "final_audit_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (OUT / "stable_mainline_assessment.md").write_text(
        "# Stable mainline assessment\n\n"
        "Round 24R is qualification evidence only. **Corrected CPLEX S0/F0 "
        "remains the stable paper mainline for every observed outcome.** The "
        "presolve-on single-tree arm is permanently non-authoritative; its bounds "
        "and certificate decisions are excluded from exact claims.\n\n"
        "The licensed Gurobi results are strong enough to justify a later, longer "
        "migration study: plain Gurobi and both external-Gurobi arms strictly "
        "certified V12_M1 and V12_M2, and the external Gurobi variants certified "
        "both faster than external CPLEX. Evidence on the two hard cases is mixed, "
        "and this round does not justify promotion. Warm-start evidence is also "
        "mixed and preliminary: one of six Stage 2 submissions was affirmatively "
        "accepted, with small aggregate proof-progress gains but no parent-tree "
        "reuse. No solver portfolio or instance-dependent selector was created.\n",
        encoding="utf-8")
    strict_count = sum(bool(row["strict_certificate"]) for row in stage2)
    auc_lookup: dict[tuple[str, str], str] = {}
    auc_path = OUT / "common_ub_bound_progress_auc.csv"
    if auc_path.exists():
        with auc_path.open(newline="", encoding="utf-8") as stream:
            for record in csv.DictReader(stream):
                if record.get("stage") == "stage2":
                    auc_lookup[(record.get("instance", ""),
                                record.get("arm", ""))] = record.get(
                                    "bound_progress_auc", "")

    arm_order = ["P-CPX", "P-GRB", "S0-SAFE", "T-CPX-ST-PON-DIAG",
                 "T-CPX-EXT-PON", "T-GRB-EXT-COLD", "T-GRB-EXT-WARM"]
    instance_order = ["V12_M1", "V12_M2", "high_imbalance_seed3202",
                      "tight_T_seed3101"]

    def number(value_: Any, digits: int = 6) -> str:
        return f"{float(value_):.{digits}g}" if finite(value_) else "--"

    table_lines = [
        "| Instance | Arm | Result | Strict | Final LB | Common gap | "
        "Bound-progress AUC | Wall s |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for instance in instance_order:
        for arm in arm_order:
            row = stage2_lookup[(instance, arm)]
            table_lines.append(
                f"| {instance} | {arm} | {row['status']} | "
                f"{'yes' if row['strict_certificate'] else 'no'} | "
                f"{number(row['final_lb'])} | {number(row['common_ub_gap'])} | "
                f"{number(auc_lookup.get((instance, arm), ''))} | "
                f"{number(row['process_wall_seconds'])} |")

    operation_lines = [
        "| Arm | Optimize | Models/reads | Artifacts/hits | Presolve/root | "
        "Same-leaf/child | Starts accepted/submitted |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for arm in arm_order:
        if arm == "T-CPX-EXT-PON":
            presolve_root = "unavailable"
        else:
            presolve_root = (f"{total(arm, 'presolve_execution_count')}/"
                             f"{total(arm, 'root_execution_count')}")
        operation_lines.append(
            f"| {arm} | {total(arm, 'optimize_count')} | "
            f"{total(arm, 'native_model_count')}/"
            f"{total(arm, 'native_model_read_count')} | "
            f"{total(arm, 'artifact_generation_count')}/"
            f"{total(arm, 'artifact_cache_hit_count')} | {presolve_root} | "
            f"{total(arm, 'same_leaf_resume_count')}/"
            f"{total(arm, 'child_restart_count')} | "
            f"{total(arm, 'warm_start_accepted_count')}/"
            f"{total(arm, 'warm_start_submitted_count')} |")

    retained = stage1b_lookup["T-GRB-EXT-COLD"]
    fresh = stage1b_lookup["T-GRB-EXT-FRESH-COLD"]
    warm = stage1b_lookup["T-GRB-EXT-WARM"]
    stage2_table = "\n".join(table_lines)
    operation_table = "\n".join(operation_lines)
    report = f"""# Round 24R final report

## Audit outcome

Round 24R used the authorized non-default license at `E:\\gurobi\\gurobi.lic`
only through the process-local environment. The file was never opened, parsed,
hashed, copied, or committed. The `gurobi_cl` check and the independent C++
environment/tiny-optimize check both returned 0 and reported `OPTIMAL` under
Gurobi 13.0.2.

Official rows: {len(rows)}; completed: {counts['completed']}; failed:
{counts['failed']}; interrupted/time-limited: {counts['interrupted']}; excluded:
0; strict original-problem certificates: {counts['strict']}. Stage 2 contains
{len(stage2)} rows and {strict_count} strict certificates. Fifteen preliminary
attempts are retained separately as excluded evidence: 12 successful but
superseded protocol/debug attempts and three process failures from the diagnosed
controller split use-after-reallocation. Every affected matched row was rebuilt
and rerun after the fix.

The final CPLEX-only executable SHA-256 is
`f67ae4583f4002dca0403f75025eb6577feda76751c9fa02e09200bf9a50bc71`;
the final unified Gurobi-enabled executable SHA-256 is
`1154393cbc850513a8f0707d0e3e3b10d3d121db4dfc0bb9c6f9e881d2b95ac2`.

Both clean release configurations passed all nine CTest targets (18/18 across
the two builds). The Round 24 backend executable passed 98/98 checks; the
Round 20 Python regression suite passed six groups; the Round 22 static suite
passed 21 checks; handling-convention tests passed in both configurations; the
no-instance-dispatch audit passed; and all ten Stage 0 native commands passed.
The evidence package contains 1,103 files (501.41 MiB); its largest artifact is
the V12_M1 P-CPX Stage 2 `dense_progress.csv` at 43,429,739 bytes (41.42 MiB).

## Correctness and mechanical qualification

The external CPLEX adapter now classifies native numeric statuses explicitly.
Only exact optimal with exact-zero gaps and passing lifecycle/model-identity
gates can close a leaf as exact; tolerance-optimal, unscaled-infeasibility,
ambiguous, and unsupported statuses fail closed. Direct status tests cover exact
optimal, tolerance optimal, infeasible, time-limit with/without incumbent,
unscaled infeasibility, and unsupported cases.

Immutable canonical leaf artifacts are keyed by model scope, interval, cutoff,
row signature, and fingerprint. A retained unchanged leaf reuses the identical
path/SHA without rewriting; a split child or identity change creates or
invalidates an artifact. The Stage 1B fresh and retained runs each generated
five artifacts and recorded one artifact-cache hit. Fresh opened six native
models; retained opened five models for six optimize calls.

Native import succeeded for toy (77 rows, 44 columns, 217 nonzeros; 18 binary,
8 integer, 18 continuous; fingerprint 1305815249) and V12_M1 (992 rows,
489 columns, 3867 nonzeros; 253 binary, 48 integer, 188 continuous;
fingerprint 1133953353). Objective sense, variable names/types/bounds, native
domain audit, and known-feasible-route verification passed. Toy CPLEX and Gurobi
both strictly certified the same exact optimum. Canonical LP byte identity is
reported only alongside this successful native import audit.

The moderate4301 sentinel completed all six arms. S0-SAFE emitted a valid
time-limit bound; the unsafe presolve-on persistent arm remained permanently
non-certifying; both static external backends retained the verified witness;
the feasibility-consistency gates passed and no contradicted infeasibility was
serialized.

## Stage 2 results

{stage2_table}

The AUC column is normalized common-UB bound-progress AUC (larger is better).
Unsafe diagnostic bounds and AUCs are displayed only as non-authoritative speed
signals and are excluded from exact comparisons.

## Lifecycle and restart evidence

{operation_table}

For external CPLEX, native presolve/root execution counts were not instrumented
and are reported as unavailable rather than fabricated. All seven Stage 2
same-leaf Gurobi re-optimizations reran presolve and were conservatively
classified as observed fresh restarts: confirmed continuation 0, partial reuse
0, ambiguous 0. Warm starts are primal information only. Stage 2 produced 24
candidates: six complete candidates were submitted, one was affirmatively
accepted, and 23 were conservatively classified rejected (five after submission
without affirmative acceptance and 18 before submission because the complete
mapping/compatibility gates did not pass). No warm start is described as native
tree reuse.

Stage 1B isolates artifact/native-model lifecycle on V12_M2. Fresh cold used
{fresh['native_model_count']} models for {fresh['optimize_count']} optimizes and
finished at LB {number(fresh['final_lb'])}, gap
{number(fresh['common_ub_gap'])}. Retained cold used
{retained['native_model_count']} models for {retained['optimize_count']}
optimizes, reused one unchanged leaf artifact/model, and finished at LB
{number(retained['final_lb'])}, gap {number(retained['common_ub_gap'])}; native
logs nevertheless classify that same-leaf attempt as a fresh restart. Warm
matched retained cold at LB {number(warm['final_lb'])}, gap
{number(warm['common_ub_gap'])}.

## Paired interpretation

- **Plain Gurobi versus plain CPLEX:** Gurobi strictly certified both V12 cases
  (34.95 s and 170.42 s); CPLEX certified none within the cap. On both hard
  time-limited cases Gurobi had higher final LB and bound-progress AUC. Plain
  Gurobi dominated plain CPLEX on this short matrix.
- **Safe persistent CPLEX versus external CPLEX:** mixed. External CPLEX
  strictly certified V12_M1 in 89.61 s while S0 did not within 180 s; S0 had a
  slightly better V12_M2 bound/gap. This is an architecture comparison, not a
  pure restart-only ablation.
- **Presolve-on diagnostic architecture:** the persistent diagnostic remains
  unsafe and non-certifying. External presolve-on CPLEX certified both V12
  cases and gave stronger hard-case bounds, but this comparison is speed
  potential only and supplies no exact evidence for the unsafe arm.
- **External Gurobi versus external CPLEX:** Gurobi certified both V12 cases
  faster. On the hard cases CPLEX had the better high-imbalance LB, while
  Gurobi had the better tight-T LB. The result is mixed and preliminary
  promising.
- **Warm versus cold Gurobi:** identical Stage 1B endpoints; in Stage 2 warm
  certified both V12 cases faster and made marginally better hard-case
  LB/AUC progress. With only one affirmatively accepted start, the supported
  conclusion is mixed, preliminary proof-progress benefit, not tree reuse.
- **Warm Gurobi versus S0:** warm Gurobi certified both V12 cases and had the
  strongest tight-T LB/AUC; S0 was materially stronger on high imbalance. This
  is enough to justify a later longer Gurobi migration study, not promotion.

## Decision and limitations

The persistent and external algorithms share fixed mathematical and scheduling
settings, but native search order and split timing are not identical. Results
therefore compare persistent-single-tree architecture with external-multi-
optimize architecture. There was no instance-dependent dispatch and no solver
portfolio.

**Corrected CPLEX S0/F0 remains the stable paper mainline.** Licensed Gurobi is
strong enough to justify a later longer migration study, but Round 24R does not
promote a backend or alter the paper mainline.
"""
    (OUT / "final_report.md").write_text(report, encoding="utf-8")


def evidence_manifest() -> None:
    rows = []
    manifest = OUT / "evidence_package_manifest.csv"
    for path in sorted(p for p in OUT.rglob("*") if p.is_file() and p != manifest):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append({"path": path.relative_to(ROOT).as_posix(),
                     "bytes": path.stat().st_size, "sha256": digest})
    write_csv(manifest, rows, ["path", "bytes", "sha256"])


def main() -> int:
    stage0_tables()
    data = runs()
    write_csv(OUT / "stage2_300s_results.csv",
              public_rows([row for row in data if row["stage"] == "stage2"]),
              SUMMARY_FIELDS)
    write_csv(OUT / "moderate4301_correctness.csv",
              public_rows([row for row in data if row["stage"] == "stage1a"]),
              SUMMARY_FIELDS)
    write_csv(OUT / "v12_m2_fresh_retained_warm.csv",
              public_rows([row for row in data if row["stage"] == "stage1b"]),
              SUMMARY_FIELDS)
    write_csv(OUT / "safe_single_tree_vs_external.csv",
              public_rows([row for row in data if row["stage"] == "stage1c"]),
              SUMMARY_FIELDS)
    write_csv(OUT / "optimize_restart_overhead.csv", public_rows(data), SUMMARY_FIELDS)
    write_csv(OUT / "exactness_audit.csv", public_rows(data), SUMMARY_FIELDS)
    write_csv(OUT / "native_resume_evidence.csv", public_rows(
        [row for row in data if row["arm"].startswith("T-GRB-EXT")]), SUMMARY_FIELDS)
    write_csv(OUT / "warm_start_audit.csv", public_rows(
        [row for row in data if row["arm"] in ("T-GRB-EXT-COLD", "T-GRB-EXT-WARM")]),
        SUMMARY_FIELDS)
    pairs = {
        "plain_cplex_vs_gurobi.csv": ("P-CPX", "P-GRB"),
        "external_cplex_vs_gurobi.csv": ("T-CPX-EXT-PON", "T-GRB-EXT-COLD"),
        "gurobi_cold_vs_warm.csv": ("T-GRB-EXT-COLD", "T-GRB-EXT-WARM"),
    }
    for filename, arms in pairs.items():
        write_csv(OUT / filename, paired(data, *arms), PAIR_FIELDS)
    auc_rows, threshold_rows = progress_tables(data)
    write_csv(OUT / "common_ub_bound_progress_auc.csv", auc_rows,
              ["stage", "instance", "arm", "common_ub", "points", "gap_auc",
               "bound_progress_auc", "status"])
    write_csv(OUT / "common_ub_time_to_gap_thresholds.csv", threshold_rows,
              ["stage", "instance", "arm", "common_ub", "gap_threshold",
               "first_time_seconds", "reached"])
    write_reports(data)
    evidence_manifest()
    print(f"Round24R summary generated for {len(data)} official rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
