#!/usr/bin/env python3
"""Run and audit Round 30 post-freeze correctness/mechanical gates serially."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import analyze_round30_c0_forensics as c0_forensic
import analyze_round30_results as analysis
import run_round30_experiments as runner


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_c0_mechanism_transfer_c5_round30"

SUITES = {
    "trace": (
        ("moderate_seed4301", "C0-DIAG", 45),
        ("moderate_seed4301", "C3-REPLICA", 45),
        ("moderate_seed4301", "C4-CANDIDATE", 45),
        ("moderate_seed4301", "C5-CANDIDATE", 45),
    ),
    "exactness": (
        ("toy", "P-GRB", 30),
        ("toy", "C5-CANDIDATE", 30),
    ),
    "sentinel": (
        ("moderate_seed4301", "P-GRB", 120),
        ("moderate_seed4301", "C5-CANDIDATE", 120),
    ),
}


def stage_name(suite: str) -> str:
    return f"stage0r1_{suite}"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    analysis.write_csv(path, rows)


def audit_all() -> None:
    build = json.loads(
        (OUT / "build_and_test_record.json").read_text(encoding="utf-8"))
    write_csv(OUT / "stage0_build_and_tests.csv", [
        {
            "name": row["name"],
            "return_code": row["return_code"],
            "wall_seconds": row["wall_seconds"],
            "passed": row["passed"],
            "stdout_path": row["stdout_path"],
            "stderr_path": row["stderr_path"],
        }
        for row in build["records"]
    ])
    runs = analysis.raw_runs()
    trace_rows = []
    # Exact toy closure is an exactness gate, not an anytime-trajectory gate:
    # plain Gurobi can close the toy in one callback observation.  Trajectory
    # completeness is required on the four nontrivial external rows and on
    # the nontrivial P-GRB/C5 sentinels.
    for suite in ("trace", "sentinel"):
        for instance, arm, _ in SUITES[suite]:
            run = analysis.require_run(
                runs, stage_name(suite), instance, arm)
            if arm in {"P-GRB", "C0-DIAG", "C3-REPLICA",
                       "C4-CANDIDATE", "C5-CANDIDATE"}:
                complete, reason, observations, count = analysis.trace_for(run)
                trace_rows.append({
                    "suite": suite,
                    "instance": instance,
                    "arm": arm,
                    "trace_complete": complete,
                    "trace_reason": reason,
                    "valid_bound_observation_count": count,
                    "first_process_seconds": (
                        observations[0].process_seconds
                        if observations else ""),
                    "last_process_seconds": (
                        observations[-1].process_seconds
                        if observations else ""),
                    "auc_eligible": complete,
                    "no_interpolation": True,
                    "no_post_last_event_extension": True,
                })
    write_csv(OUT / "stage0_trace_correctness.csv", trace_rows)

    retained = c0_forensic.all_c0_runs()
    attempts, splits, interleaving, shadows = (
        c0_forensic.forensic_rows(retained))
    parser_rows = [{
        "retained_c0_c1_equivalent_runs": len(retained),
        "attempt_events": len(attempts),
        "split_events": len(splits),
        "interleaving_rows": len(interleaving),
        "shadow_rows": len(shadows),
        "expected_runs": 57,
        "expected_attempt_events": 1386,
        "expected_split_events": 317,
        "expected_shadow_rows": 951,
        "passed": (
            len(retained) == 57 and len(attempts) == 1386
            and len(splits) == 317 and len(interleaving) == 1386
            and len(shadows) == 951),
    }]
    write_csv(OUT / "stage0_c0_parser.csv", parser_rows)

    sentinel_c5 = analysis.require_run(
        runs, stage_name("sentinel"),
        "moderate_seed4301", "C5-CANDIDATE")
    result = sentinel_c5["result"]
    native_rows = [{
        "instance": "moderate_seed4301",
        "arm": "C5-CANDIDATE",
        "partial_mip_optimize_count":
            analysis.result_metric(
                sentinel_c5, "partial_mip_optimize_count"),
        "valid_partial_bound_event_count":
            analysis.result_metric(
                sentinel_c5, "partial_mip_bound_event_count"),
        "target_reached_count":
            analysis.result_metric(
                sentinel_c5, "partial_mip_target_reached_count"),
        "callback_termination_tested": (
            analysis.integer(analysis.result_metric(
                sentinel_c5, "partial_mip_optimize_count")) > 0),
        "same_model_object_reuse_count":
            analysis.result_metric(
                sentinel_c5, "in_memory_model_reuse_count"),
        "basis_reuse_claimed": False,
        "native_tree_continuation_claimed": (
            analysis.integer(analysis.result_metric(
                sentinel_c5, "confirmed_continuation_count")) > 0),
        "lifecycle_complete":
            analysis.truth(analysis.result_metric(
                sentinel_c5, "lifecycle_complete")),
        "coverage_valid": (
            analysis.truth(analysis.result_metric(
                sentinel_c5, "root_coverage_valid"))
            and analysis.truth(analysis.result_metric(
                sentinel_c5, "parent_child_coverage_valid"))),
        "passed": (
            analysis.integer(analysis.result_metric(
                sentinel_c5, "partial_mip_optimize_count")) > 0
            and analysis.integer(analysis.result_metric(
                sentinel_c5, "partial_mip_bound_event_count")) > 0
            and analysis.truth(analysis.result_metric(
                sentinel_c5, "lifecycle_complete"))),
    }]
    write_csv(OUT / "stage0_native_event_tests.csv", native_rows)

    exactness_rows = []
    for instance, arm, _ in SUITES["exactness"]:
        run = analysis.require_run(
            runs, stage_name("exactness"), instance, arm)
        result = run["result"]
        exactness_rows.append({
            "instance": instance,
            "arm": arm,
            "return_code": run["state"]["return_code"],
            "status": result.get("status"),
            "objective": analysis.number(result.get("objective")),
            "lower_bound": analysis.number(result.get("lower_bound")),
            "upper_bound": analysis.number(result.get("upper_bound")),
            "strict_certificate":
                analysis.truth(
                    result.get("strict_certified_original_problem")),
            "verification_feasible":
                analysis.truth(result.get(
                    "verification_original_solution_feasible",
                    result.get("solution_feasible", True))),
            "passed": (
                run["state"]["return_code"] == 0
                and not run["state"]["emergency_timeout"]),
        })
    if len(exactness_rows) == 2:
        same = abs(
            exactness_rows[0]["objective"] -
            exactness_rows[1]["objective"]) <= 1e-7
        for row in exactness_rows:
            row["toy_objective_identity"] = same
            row["passed"] = row["passed"] and same
    write_csv(OUT / "stage0_exactness.csv", exactness_rows)

    sentinel_rows = []
    for instance, arm, _ in SUITES["sentinel"]:
        run = analysis.require_run(
            runs, stage_name("sentinel"), instance, arm)
        result = run["result"]
        false_certificate = (
            analysis.truth(result.get("strict_certified_original_problem"))
            and abs(
                analysis.number(result.get("lower_bound")) -
                analysis.number(result.get("upper_bound"))) >
                1e-7 * max(
                    1.0, abs(analysis.number(result.get("upper_bound")))))
        sentinel_rows.append({
            "instance": instance,
            "arm": arm,
            "return_code": run["state"]["return_code"],
            "status": result.get("status"),
            "valid_final_lb": result.get("lower_bound"),
            "verified_ub": result.get("upper_bound"),
            "strict_certificate":
                result.get("strict_certified_original_problem"),
            "false_certificate": false_certificate,
            "lifecycle_complete":
                result.get("external_gini_tree_lifecycle_complete", ""),
            "passed": (
                run["state"]["return_code"] == 0
                and not run["state"]["emergency_timeout"]
                and not false_certificate),
        })
    write_csv(OUT / "stage0_sentinel.csv", sentinel_rows)

    gates = (
        all(row["passed"] for row in build["records"])
        and all(row["trace_complete"] for row in trace_rows)
        and parser_rows[0]["passed"]
        and all(row["passed"] for row in native_rows)
        and all(row["passed"] for row in exactness_rows)
        and all(row["passed"] for row in sentinel_rows)
    )
    runner.json_write(OUT / "stage0_gate_summary.json", {
        "schema": "round30-stage0-gates-v1",
        "build_and_tests": all(row["passed"] for row in build["records"]),
        "trace_correctness": all(
            row["trace_complete"] for row in trace_rows),
        "c0_parser": parser_rows[0]["passed"],
        "native_events": all(row["passed"] for row in native_rows),
        "exactness": all(row["passed"] for row in exactness_rows),
        "sentinel": all(row["passed"] for row in sentinel_rows),
        "all_stage0_gates_passed": gates,
    })
    if not gates:
        raise RuntimeError("Round 30 Stage 0 gate failure")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--suite", choices=tuple(SUITES) + ("all",), required=True)
    args = parser.parse_args()
    suites = tuple(SUITES) if args.suite == "all" else (args.suite,)
    failures = 0
    for suite in suites:
        for instance, arm, budget in SUITES[suite]:
            state = runner.run_one(
                stage_name(suite), instance, arm, budget)
            failures += int(
                state["return_code"] != 0
                or state["emergency_timeout"]
                or not state["result_exists"]
                or not state["phase_ledger_exists"])
    if failures:
        raise RuntimeError(
            f"Stage 0 process/mechanical failures: {failures}")
    if args.suite == "all":
        audit_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
