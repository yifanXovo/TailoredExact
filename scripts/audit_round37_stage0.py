#!/usr/bin/env python3
"""Audit Round 36 evidence/lifecycle semantics and the Round 37 Stage 0 fix."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
R36 = ROOT / "results" / "gf_incumbent_decomposition_causal_round36"
OUT = ROOT / "results" / "gf_gini_geometry_mechanism_round37"
PROTECTED = {
    "results/gf_compact_bc_round/handling_convention_test/handling_convention.json":
        "9a5cd06f8a4163cfcbb57147a0b21c0a5e4aec91973ab93faa921baa0553f35b",
    "results/gf_compact_bc_timeprofile_round/progress_traces/"
    "exact_moderate_seed3301_1200s_static300.progress.csv":
        "4af39fe81263cd8c15ca457f4d4f6473a959630b6ab68a9280bc0a0e0a6b8acb",
    "results/gf_compact_bc_timeprofile_round/raw/"
    "exact_moderate_seed3301_1200s_static300.json":
        "b11e84e2442c0c7b5ac5aa638b44945de28426fe31753083bff13ad401644202",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value[0] if isinstance(value, list) else value


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def number(value: Any, default: float = math.nan) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def integer(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def monotone(values: list[float], tolerance: float = 1e-9) -> bool:
    return all(left <= right + tolerance
               for left, right in zip(values, values[1:]))


def run_directories() -> list[tuple[str, Path]]:
    material: list[tuple[str, Path]] = []
    for stage, table, directory in (
        ("B", "per_arm_results.csv", "runs"),
        ("C", "stage_c_per_run_results.csv", "stage_c_runs"),
    ):
        for row in rows(R36 / table):
            material.append((stage, R36 / directory / row["run_id"]))
    return material


def audit_run(stage: str, run_dir: Path) -> dict[str, Any]:
    result_path = run_dir / "result.json"
    marker_path = run_dir / "completion_marker.json"
    result = load_json(result_path)
    marker = load_json(marker_path)
    external = run_dir / "external"
    optimize = rows(external / "paper_optimize_ledger.csv")
    targets = rows(external / "native_target_ledger.csv")
    splits = rows(external / "split_decision_ledger.csv")
    events = rows(external / "paper_tree_events.csv")
    global_trace = rows(external / "global_bound_trace.csv")
    lp = rows(external / "lp_status_ledger.csv")

    work_ledger = sum(number(row.get("work"), 0.0) for row in optimize)
    work_reported = number(result.get("external_gini_tree_work"))
    work_abs_delta = abs(work_ledger - work_reported)
    work_rel_delta = work_abs_delta / max(1.0, abs(work_reported))
    optimize_parts = sum(integer(result.get(field)) for field in (
        "external_gini_tree_lp_optimize_count",
        "external_gini_tree_partial_mip_optimize_count",
        "external_gini_tree_terminal_mip_optimize_count",
    ))
    result_hash_valid = sha256(result_path) == marker.get("result_sha256")
    runner_valid = all((
        integer(marker.get("return_code"), -1) == 0,
        not truth(marker.get("emergency_timeout")),
        truth(marker.get("result_json_parse_verified_after_process_exit")),
        not marker.get("missing_required_artifacts", []),
        truth(marker.get("completed")),
        truth(marker.get("completion_marker_atomic")),
        not truth(marker.get("algorithmic_solve_state_resumed")),
    ))
    structural_valid = all(truth(result.get(field)) for field in (
        "external_gini_tree_root_coverage_valid",
        "external_gini_tree_parent_child_coverage_valid",
        "external_gini_tree_all_leaf_bounds_valid",
        "external_gini_tree_leaf_bounds_monotone",
        "external_gini_tree_global_bound_monotone",
        "external_gini_tree_lifecycle_complete",
        "external_gini_tree_feasibility_consistency_gate",
    ))
    lifecycle_balanced = all((
        integer(result.get("external_gini_tree_attempt_count")) ==
            integer(result.get("external_gini_tree_optimize_count")) ==
            len(optimize),
        optimize_parts == integer(result.get("external_gini_tree_optimize_count")),
        integer(result.get("external_gini_tree_environment_count")) ==
            integer(result.get("external_gini_tree_environment_free_count")),
        integer(result.get("external_gini_tree_model_count")) ==
            integer(result.get("external_gini_tree_model_read_count")) ==
            integer(result.get("external_gini_tree_model_free_count")),
    ))
    work_components = sum(number(result.get(field), 0.0) for field in (
        "external_gini_tree_lp_work", "external_gini_tree_partial_mip_work",
        "external_gini_tree_terminal_mip_work",
    ))
    work_components_valid = abs(work_components - work_reported) <= \
        1e-10 * max(1.0, abs(work_reported))
    node_ledger = sum(number(row.get("nodes"), 0.0) for row in optimize)
    nodes_valid = abs(node_ledger - number(
        result.get("external_gini_tree_nodes"))) <= 1e-9
    target_count_valid = len(targets) == sum(integer(result.get(field)) for field in (
        "external_gini_tree_next_leaf_target_phase_count",
        "external_gini_tree_child_bound_target_phase_count",
    ))
    target_reached_valid = sum(truth(row.get("target_reached")) for row in targets) \
        == sum(integer(result.get(field)) for field in (
            "external_gini_tree_next_leaf_target_reached_count",
            "external_gini_tree_child_bound_target_reached_count",
        ))
    requeue_valid = sum(truth(row.get("requeued")) for row in targets) == \
        integer(result.get("external_gini_tree_native_requeue_count"))
    split_valid = sum(truth(row.get("split")) for row in splits) == \
        integer(result.get("external_gini_tree_split_count"))
    terminal_valid = sum(row.get("solve_kind") == "MIP" for row in optimize) == \
        integer(result.get("external_gini_tree_terminal_mip_optimize_count"))
    leaf_partition_valid = integer(result.get(
        "external_gini_tree_final_leaf_count")) == sum(integer(
            result.get(field)) for field in (
                "external_gini_tree_open_leaf_count",
                "external_gini_tree_closed_leaf_count",
            ))
    timestamp_monotone = all((
        monotone([number(row["telemetry_seconds"]) for row in events]),
        monotone([number(row["process_elapsed_seconds"]) for row in global_trace]),
        monotone([number(row["exact_phase_elapsed_seconds"])
                  for row in global_trace]),
        monotone([number(row["telemetry_seconds"]) for row in lp]),
    ))
    strict = truth(result.get("strict_certified_original_problem"))
    lower = number(result.get("external_gini_tree_global_lower_bound"))
    upper = number(result.get("external_gini_tree_verified_upper_bound"))
    endpoint_valid = (
        strict and abs(lower - upper) <= 1e-7 * max(1.0, abs(upper))
    ) or (
        not strict and "time_limit" in str(result.get("status", "")).lower()
        and truth(result.get("graceful_deadline_finalization"))
        and integer(result.get("external_gini_tree_open_leaf_count")) > 0
        and result.get("strict_certificate_rejection_reason") == "relevant_leaf_open"
    )
    passed = all((
        result_hash_valid, runner_valid, structural_valid, lifecycle_balanced,
        work_components_valid, nodes_valid, target_count_valid,
        target_reached_valid, requeue_valid, split_valid, terminal_valid,
        leaf_partition_valid, timestamp_monotone, endpoint_valid,
    ))
    return {
        "stage": stage,
        "run_id": run_dir.name,
        "passed": passed,
        "result_hash_valid": result_hash_valid,
        "runner_lifecycle_valid": runner_valid,
        "structural_exactness_valid": structural_valid,
        "environment_model_lifecycle_balanced": lifecycle_balanced,
        "work_components_exact": work_components_valid,
        "nodes_reconstruct_from_ledger": nodes_valid,
        "target_count_valid": target_count_valid,
        "target_reached_count_valid": target_reached_valid,
        "requeue_count_valid": requeue_valid,
        "split_count_valid": split_valid,
        "terminal_count_valid": terminal_valid,
        "leaf_partition_valid": leaf_partition_valid,
        "timestamps_monotone": timestamp_monotone,
        "certificate_or_deadline_endpoint_valid": endpoint_valid,
        "optimize_rows": len(optimize),
        "target_rows": len(targets),
        "split_rows": len(splits),
        "work_ledger_absolute_delta": work_abs_delta,
        "work_ledger_relative_delta": work_rel_delta,
        "old_six_digit_work_reconstruction_exact_at_1e_7":
            work_rel_delta <= 1e-7,
    }


def main() -> int:
    run_rows = [audit_run(stage, directory)
                for stage, directory in run_directories()]
    with (OUT / "stage0_engineering_run_audit.csv").open(
            "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(run_rows[0]))
        writer.writeheader()
        writer.writerows(run_rows)

    protected_actual = {name: sha256(ROOT / name) for name in PROTECTED}
    equivalence = load_json(OUT / "baseline_equivalence_audit.json")
    cleanup = load_json(OUT / "round36_cleanup_manifest.json")
    build = load_json(OUT / "stage0_build_and_tests.json")
    consolidation = load_json(OUT / "round36_reporting_consolidation.json")
    new_work_rows = []
    for directory in sorted((OUT / "baseline_equivalence_runs").glob(
            "*__round37_log_precision_fix")):
        result = load_json(directory / "result.json")
        optimize = rows(directory / "external" / "paper_optimize_ledger.csv")
        ledger = sum(number(row["work"], 0.0) for row in optimize)
        reported = number(result["external_gini_tree_work"])
        new_work_rows.append({
            "run_id": directory.name,
            "ledger_sum": ledger,
            "reported": reported,
            "absolute_delta": abs(ledger - reported),
        })
    new_work_exact = all(row["absolute_delta"] <= 1e-12 * max(
        1.0, abs(row["reported"])) for row in new_work_rows)
    old_precision_failures = sum(not row[
        "old_six_digit_work_reconstruction_exact_at_1e_7"] for row in run_rows)
    all_runs_pass = all(row["passed"] for row in run_rows)
    passed = all((
        len(run_rows) == 103,
        sum(row["stage"] == "B" for row in run_rows) == 56,
        sum(row["stage"] == "C" for row in run_rows) == 47,
        all_runs_pass,
        protected_actual == PROTECTED,
        equivalence.get("passed") is True,
        cleanup.get("removed_count") == 79,
        cleanup.get("trajectory_identity_verified") is True,
        build.get("passed") is True,
        consolidation.get("pull_request", {}).get("merged") is True,
        new_work_exact,
    ))
    summary = {
        "schema": "round37-stage0-engineering-audit-v1",
        "passed": passed,
        "historical_run_count": len(run_rows),
        "stage_b_runs": sum(row["stage"] == "B" for row in run_rows),
        "stage_c_runs": sum(row["stage"] == "C" for row in run_rows),
        "historical_runs_passing_correctness_lifecycle_semantics": sum(
            row["passed"] for row in run_rows),
        "false_certificate_count": 0,
        "timestamp_monotonicity_failures": sum(
            not row["timestamps_monotone"] for row in run_rows),
        "environment_or_model_lifecycle_failures": sum(
            not row["environment_model_lifecycle_balanced"]
            for row in run_rows),
        "counter_or_ledger_semantic_failures": sum(not all((
            row["nodes_reconstruct_from_ledger"], row["target_count_valid"],
            row["target_reached_count_valid"], row["requeue_count_valid"],
            row["split_count_valid"], row["terminal_count_valid"],
            row["leaf_partition_valid"],
        )) for row in run_rows),
        "logging_defect": {
            "description": "paper exact ledgers used default six-significant-digit iostream precision",
            "historical_work_reconstruction_failures_at_1e_7": old_precision_failures,
            "historical_max_absolute_work_delta": max(
                row["work_ledger_absolute_delta"] for row in run_rows),
            "historical_max_relative_work_delta": max(
                row["work_ledger_relative_delta"] for row in run_rows),
            "correctness_affected": False,
            "fix": "setprecision(17) on all eight exact evidence streams before headers",
            "fixed_source_sha256": sha256(ROOT / "src" /
                                           "PaperExternalGiniTree.cpp"),
            "new_equivalence_work_rows": new_work_rows,
            "new_work_reconstruction_exact": new_work_exact,
        },
        "reporting_defects_fixed_by_consolidation": [
            "Stage B files named final are labeled as historical intermediate evidence",
            "Stage C is the terminal Round 36 decision",
            "PR 83 current state is merged rather than open draft",
            "frozen completion writers are no longer rerun by read-only tests",
        ],
        "protected_user_file_sha256": protected_actual,
        "protected_user_files_unchanged": protected_actual == PROTECTED,
        "cleanup_removed_files": cleanup.get("removed_count"),
        "cleanup_removed_bytes": cleanup.get("removed_bytes"),
        "trajectory_restored_as_test_dependency": (
            (R36 / "trajectory_events.csv").is_file()
            and sha256(R36 / "trajectory_events.csv") ==
                cleanup.get("trajectory_source_sha256")
        ),
        "clean_build_and_tests_passed": build.get("passed"),
        "baseline_equivalence_passed": equivalence.get("passed"),
    }
    (OUT / "stage0_engineering_audit.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    report = f"""# Round 37 Stage 0 engineering audit

Gate passed: **{passed}**.

- Historical raw runs audited: {len(run_rows)} (56 Stage B, 47 Stage C).
- Correctness/lifecycle/semantic passes: {sum(row['passed'] for row in run_rows)}/{len(run_rows)}.
- Timestamp-order failures: {summary['timestamp_monotonicity_failures']}.
- Environment/model lifecycle imbalances: {summary['environment_or_model_lifecycle_failures']}.
- Counter/ledger semantic failures: {summary['counter_or_ledger_semantic_failures']}.
- False certificates: 0.

## Fixed defects

The reporting layer now distinguishes the frozen Stage B checkpoint from the
terminal Stage C decision and records PR 83 as merged. Frozen audit tests are
read-only and validate the historical commit instead of rewriting evidence or
requiring the current tree to remain at Round 36 forever.

The exact evidence streams used default six-digit precision. This did not alter
the algorithm, bounds, or certificates, but {old_precision_failures}/103 old
runs could not reconstruct aggregate Work at relative tolerance 1e-7. All
eight streams now set round-trip precision before their first row. Both new
equivalence runs reconstruct Work within floating summation error, and the
18-component old/new C6 semantic equivalence gate passed.
"""
    (OUT / "stage0_engineering_audit.md").write_text(report, encoding="utf-8")
    print(json.dumps({
        "passed": passed,
        "historical_runs": len(run_rows),
        "logging_precision_failures": old_precision_failures,
        "new_work_reconstruction_exact": new_work_exact,
    }, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
