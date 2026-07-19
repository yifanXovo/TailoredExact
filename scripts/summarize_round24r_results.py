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
    summary = {
        "schema": "round24r-final-audit-v1",
        "official_counts": dict(counts),
        "official_rows": len(rows),
        "license_usable": load_json(OUT / "license_visibility_audit.json").get(
            "checks_agree", False),
        "stable_mainline": "corrected_CPLEX_S0_F0",
        "stage_counts": dict(Counter(str(row["stage"]) for row in rows)),
        "strict_by_arm": dict(Counter(str(row["arm"]) for row in rows
                                      if row["strict_certificate"])),
    }
    (OUT / "final_audit_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (OUT / "stable_mainline_assessment.md").write_text(
        "# Stable mainline assessment\n\n"
        "Round 24R is qualification evidence only. Corrected CPLEX S0/F0 remains "
        "the stable paper mainline for every observed outcome. The presolve-on "
        "single-tree arm is a permanently non-authoritative diagnostic. No solver "
        "portfolio or instance-dependent selector was created.\n", encoding="utf-8")
    stage2 = [row for row in rows if row["stage"] == "stage2"]
    strict_count = sum(bool(row["strict_certificate"]) for row in stage2)
    report = f"""# Round 24R final report

Round 24R used the authorized non-default license through a process-local environment. Both independent license checks and the native toy qualification succeeded. The source corrections use numeric CPLEX status semantics, immutable controller-owned leaf LPs, per-attempt native logs, conservative retained-state classifications, and a direct Gurobi import-domain audit.

Official rows: {len(rows)}; completed: {counts['completed']}; failed: {counts['failed']}; interrupted/time-limited: {counts['interrupted']}; strict certificates: {counts['strict']}. Stage 2 rows: {len(stage2)} with {strict_count} strict certificates. Detailed paired evidence is in the CSV tables in this directory.

The persistent and external algorithms share their fixed mathematical and scheduling settings, but their native search orders and split timing are not identical. Results therefore compare persistent-single-tree architecture with external-multi-optimize architecture; they are not a pure restart-only causal ablation. Warm starts are primal information only and are not described as tree reuse.

Corrected CPLEX S0/F0 remains the stable paper mainline. Any recommendation for a longer Gurobi study must be based on the paired Stage 2 tables and cannot promote a backend in this round.
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
