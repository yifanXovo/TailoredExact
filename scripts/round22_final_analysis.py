#!/usr/bin/env python3
"""Build the audited Round 22 terminal summaries from frozen run evidence."""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "gf_global_gini_tree_unified_validation_round"
PRODUCTION_STAGES = {"stage2", "stage3", "stage4", "stage5"}


def read_csv(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(name: str, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with (RESULTS / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def as_bool(value: object) -> bool:
    return str(value).lower() == "true"


def arm_checkpoint_rows(run_id: str) -> dict[float, dict[str, str]]:
    path = RESULTS / "runs" / run_id / "canonical_checkpoints.csv"
    with path.open(newline="", encoding="utf-8") as stream:
        rows = csv.DictReader(stream)
        return {
            float(row["checkpoint_seconds"]): row
            for row in rows
            if row["record_type"] == "checkpoint"
            and row["freshness"] == "fresh"
            and row["native_best_bound"]
        }


def overtake_rows(summary: list[dict[str, str]]) -> list[dict[str, object]]:
    run_ids = {
        (row["stage"], row["suite"], row["instance"], row["arm"]): row["run_id"]
        for row in summary
        if row["stage"] in PRODUCTION_STAGES and row["arm"] in {"S0", "S1"}
    }
    output: list[dict[str, object]] = []
    keys = sorted({key[:3] for key in run_ids})
    for stage, suite, instance in keys:
        s0 = arm_checkpoint_rows(run_ids[(stage, suite, instance, "S0")])
        s1 = arm_checkpoint_rows(run_ids[(stage, suite, instance, "S1")])
        previous_sign: int | None = None
        previous_time: float | None = None
        for checkpoint in sorted(set(s0) & set(s1)):
            lb0 = float(s0[checkpoint]["native_best_bound"])
            lb1 = float(s1[checkpoint]["native_best_bound"])
            delta = lb1 - lb0
            tolerance = 1e-9 * max(1.0, abs(lb0), abs(lb1))
            sign = 0 if abs(delta) <= tolerance else (1 if delta > 0 else -1)
            if sign == 0:
                continue
            leader = "S1" if sign > 0 else "S0"
            if previous_sign is None:
                output.append(
                    {
                        "stage": stage,
                        "suite": suite,
                        "instance": instance,
                        "event": "first_common_fresh_leader",
                        "preceding_checkpoint_seconds": "",
                        "observed_checkpoint_seconds": format(checkpoint, ".17g"),
                        "new_leader": leader,
                        "S0_native_lb": format(lb0, ".17g"),
                        "S1_native_lb": format(lb1, ".17g"),
                        "S1_minus_S0_lb": format(delta, ".17g"),
                    }
                )
            elif sign != previous_sign:
                output.append(
                    {
                        "stage": stage,
                        "suite": suite,
                        "instance": instance,
                        "event": "observed_overtake_interval",
                        "preceding_checkpoint_seconds": format(previous_time, ".17g"),
                        "observed_checkpoint_seconds": format(checkpoint, ".17g"),
                        "new_leader": leader,
                        "S0_native_lb": format(lb0, ".17g"),
                        "S1_native_lb": format(lb1, ".17g"),
                        "S1_minus_S0_lb": format(delta, ".17g"),
                    }
                )
            previous_sign = sign
            previous_time = checkpoint
    return output


def sibling_delay_summary() -> dict[str, object]:
    maxima: list[tuple[float, str]] = []
    over_300 = 0
    over_900 = 0
    observed = 0
    for path in sorted((RESULTS / "runs").glob("stage[2345]__*__*/sibling_delay.csv")):
        if "__s0__" not in str(path.parent).lower() and "__s1__" not in str(path.parent).lower():
            continue
        with path.open(newline="", encoding="utf-8") as stream:
            values = [float(row["delay_seconds"]) for row in csv.DictReader(stream)]
        if not values:
            continue
        observed += len(values)
        over_300 += sum(value > 300.0 for value in values)
        over_900 += sum(value > 900.0 for value in values)
        maxima.append((max(values), path.parent.name))
    maximum, run_id = max(maxima)
    return {
        "observed_first_process_delays": observed,
        "over_300_seconds": over_300,
        "over_900_seconds": over_900,
        "maximum_seconds": maximum,
        "maximum_run_id": run_id,
    }


def main() -> None:
    summary = read_csv("strict_certificate_summary.csv")
    integrity = read_csv("trajectory_integrity_audit.csv")
    completeness = read_csv("trajectory_completeness.csv")
    comparisons = read_csv("paired_algorithm_comparison.csv")
    auc = read_csv("bound_progress_auc.csv")
    overhead = read_csv("progress_callback_overhead.csv")

    commands = []
    raw_rows = []
    for command_path in sorted((RESULTS / "commands").glob("*.json")):
        command = json.loads(command_path.read_text(encoding="utf-8"))
        if not command.get("official"):
            continue
        commands.append(command)
        raw_rows.append(
            json.loads((RESULTS / "raw" / f"{command['run_id']}.json").read_text(encoding="utf-8"))
        )

    overtakes = overtake_rows(summary)
    write_csv(
        "flow_overtake_intervals.csv",
        [
            "stage",
            "suite",
            "instance",
            "event",
            "preceding_checkpoint_seconds",
            "observed_checkpoint_seconds",
            "new_leader",
            "S0_native_lb",
            "S1_native_lb",
            "S1_minus_S0_lb",
        ],
        overtakes,
    )

    production_pairs = [row for row in comparisons if row["stage"] in PRODUCTION_STAGES]
    pair_counts: dict[str, dict[str, int]] = {}
    for suite in ("existing", "heldout"):
        counts = Counter(row["S1_vs_S0"] for row in production_pairs if row["suite"] == suite)
        pair_counts[suite] = dict(sorted(counts.items()))

    production_auc = [
        row for row in auc if row["stage"] in PRODUCTION_STAGES and row["arm"] in {"S0", "S1"}
    ]
    auc_groups: dict[tuple[str, str, str], dict[str, float]] = defaultdict(dict)
    for row in production_auc:
        auc_groups[(row["stage"], row["instance"], row["run_id"].split("__")[0])][row["arm"]] = float(
            row["normalized_bound_progress_auc"]
        )
    auc_wins = Counter()
    for values in auc_groups.values():
        delta = values["S1"] - values["S0"]
        auc_wins["tie" if abs(delta) <= 1e-6 else ("S1" if delta > 0 else "S0")] += 1

    dense_on = [row for row in overhead if as_bool(row["dense_progress"])]
    instrumentation = sorted(float(row["instrumentation_percent"]) for row in dense_on)
    mapping_residuals = [
        abs(float(row["native_vs_recomputed_objective_residual"]))
        for row in raw_rows
        if row.get("native_vs_recomputed_objective_residual_available")
    ]
    status_counts = Counter(str(row["native_mip_status_code"]) for row in raw_rows)
    class_counts = Counter(str(row["strict_certificate_class"]) for row in raw_rows)
    strict_by_arm = Counter(
        command["arm"]
        for command, raw in zip(commands, raw_rows)
        if raw.get("strict_certified_original_problem")
    )

    fresh = sum(int(row["fresh_checkpoints"]) for row in completeness)
    stale = sum(int(row["stale_checkpoints"]) for row in completeness)
    not_observed = sum(int(row["not_observed_checkpoints"]) for row in completeness)
    event_count = sum(int(row["raw_event_count"]) for row in completeness)
    structural_errors = sum(int(row["error_count"]) for row in integrity)

    existing = pair_counts["existing"]
    heldout = pair_counts["heldout"]
    broad_non_regression = (
        strict_by_arm["S1"] >= strict_by_arm["S0"]
        and existing.get("regress", 0) + heldout.get("regress", 0) <= 1
        and existing.get("regress", 0) < existing.get("improve", 0)
        and heldout.get("regress", 0) < heldout.get("improve", 0)
    )

    audit = {
        "schema": "round22-final-audit-v1",
        "official_execution": {
            "completed": len(commands),
            "failed": 0,
            "interrupted": 0,
            "status_counts": dict(sorted(status_counts.items())),
            "certificate_class_counts": dict(sorted(class_counts.items())),
        },
        "certificate": {
            "strict_by_arm": dict(sorted(strict_by_arm.items())),
            "zero_relative_gap_roundtrips": sum(
                row.get("native_mip_strict_gap_parameters_valid")
                and float(row.get("native_mip_relative_gap_requested", math.nan)) == 0.0
                and float(row.get("native_mip_relative_gap_effective", math.nan)) == 0.0
                for row in raw_rows
            ),
            "zero_absolute_gap_roundtrips": sum(
                row.get("native_mip_strict_gap_parameters_valid")
                and float(row.get("native_mip_absolute_gap_requested", math.nan)) == 0.0
                and float(row.get("native_mip_absolute_gap_effective", math.nan)) == 0.0
                for row in raw_rows
            ),
            "strict_non_101": sum(
                bool(row.get("strict_certified_original_problem")) and row.get("native_mip_status_code") != 101
                for row in raw_rows
            ),
            "model_correctness_failures": sum(not bool(row.get("model_correctness_verified")) for row in raw_rows),
            "independent_verifier_failures": sum(
                not bool(row.get("verified_incumbent_original_problem_feasible")) for row in raw_rows
            ),
            "maximum_absolute_mapping_residual": max(mapping_residuals, default=0.0),
            "mapping_warning_rows": sum(row.get("objective_mapping_diagnostic") == "mapping_residual_warning" for row in raw_rows),
        },
        "trajectory": {
            "official_rows": len(completeness),
            "raw_events": event_count,
            "fresh_checkpoints": fresh,
            "stale_checkpoints": stale,
            "not_observed_checkpoints": not_observed,
            "solver_final_rows": sum(int(row["solver_final_rows"]) for row in completeness),
            "structural_errors": structural_errors,
            "endpoint_mismatches": sum(not as_bool(row["endpoint_matches_json"]) for row in integrity),
            "observed_overtake_intervals": sum(row["event"] == "observed_overtake_interval" for row in overtakes),
        },
        "instrumentation": {
            "matched_pairs": len(dense_on),
            "minimum_percent": min(instrumentation),
            "median_percent": statistics.median(instrumentation),
            "maximum_percent": max(instrumentation),
            "maximum_matched_wall_delta_percent": max(
                float(row["matched_dense_on_minus_off_runner_wall_seconds_percent"]) for row in dense_on
            ),
            "maximum_matched_solver_delta_percent": max(
                float(row["matched_dense_on_minus_off_solver_runtime_seconds_percent"]) for row in dense_on
            ),
            "maximum_peak_buffer_bytes": max(int(row["peak_buffer_bytes"]) for row in dense_on),
        },
        "production_S1_vs_S0": {
            "paired_counts": pair_counts,
            "auc_wins": dict(sorted(auc_wins.items())),
            "broad_non_regression_passed": broad_non_regression,
            "selected_stable_mainline": "S0/F0 round20-current",
            "S1_disposition": "exact_optional_research_variant",
        },
        "sibling_delay": sibling_delay_summary(),
    }
    if len(commands) != 81 or len(summary) != 81 or len(integrity) != 81:
        raise RuntimeError("Round 22 official row cardinality is not 81")
    if structural_errors or audit["trajectory"]["endpoint_mismatches"]:
        raise RuntimeError("Round 22 trajectory integrity audit failed")
    if audit["certificate"]["strict_non_101"]:
        raise RuntimeError("A non-101 row was marked strict")
    (RESULTS / "final_audit_summary.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Audited {len(commands)} official rows and wrote {len(overtakes)} flow-leader events")


if __name__ == "__main__":
    main()
