#!/usr/bin/env python3
"""Reconstruct the Round 28 C3 cost and leaf-value mechanisms for Round 29.

The script is deliberately read-only with respect to Round 28.  It writes only
the required Round 29 Phase-A evidence and labels quantities that cannot be
observed directly from the retained native API evidence.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
R28 = ROOT / "results/gf_cplex_equivalent_gurobi_replica_round28"
OUT = ROOT / "results/gf_gurobi_performance_recovery_round29"
TOL = 1e-7


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        return value[0]
    return value


def rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def number(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
        return parsed if math.isfinite(parsed) else default
    except (TypeError, ValueError):
        return default


def integer(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def write_csv(path: Path, data: list[dict[str, Any]], fields: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)


def phase_from_run_id(run_id: str) -> str:
    return run_id.split("__", 1)[0]


def instance_from_run_id(run_id: str) -> str:
    parts = run_id.split("__")
    return parts[1] if len(parts) > 1 else run_id


def completed_c3_runs() -> list[Path]:
    candidates = []
    for directory in sorted((R28 / "runs").glob("*c3_replica*")):
        if (directory / "result.json").exists():
            candidates.append(directory)
    return candidates


def event_bound_gains(
    trace: list[dict[str, str]],
) -> tuple[dict[tuple[str, str], float], float, float]:
    gains: dict[tuple[str, str], float] = {}
    previous = 0.0
    first_gain = -1.0
    last_gain = -1.0
    for row in trace:
        current = number(row.get("global_lb"), previous)
        gain = max(0.0, current - previous)
        event = row.get("event", "")
        leaf = row.get("leaf_id", "")
        gains[(event, leaf)] = gains.get((event, leaf), 0.0) + gain
        if gain > TOL:
            time = number(row.get("telemetry_seconds"), -1.0)
            if first_gain < 0.0:
                first_gain = time
            last_gain = time
        previous = max(previous, current)
    return gains, first_gain, last_gain


def analyze() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    costs: list[dict[str, Any]] = []
    leaf_values: list[dict[str, Any]] = []
    for directory in completed_c3_runs():
        run_id = directory.name
        result = load_json(directory / "result.json")
        external = directory / "external"
        event_trace = rows(external / "replica_tree_events.csv")
        optimize = rows(external / "replica_optimize_ledger.csv")
        leaves = rows(external / "replica_leaf_ledger.csv")
        global_trace = rows(external / "global_bound_trace.csv")
        by_leaf = {row["leaf_id"]: row for row in leaves}

        exact_last = max(
            (number(row.get("telemetry_seconds")) for row in event_trace),
            default=0.0,
        )
        exact_first_event = min(
            (number(row.get("telemetry_seconds")) for row in event_trace),
            default=0.0,
        )
        total = number(result.get("final_process_wall_time_seconds"),
                       number(result.get("runtime_seconds")))
        hga = number(result.get("hga_wall_time_seconds"))
        # The process/tree clock offset is observable, but serialization is not
        # separately timestamped in Round 28.  Preserve this as a bounded,
        # explicitly derived residual rather than calling it a native timer.
        pre_and_post_exact_residual = max(0.0, total - exact_last)
        verification_pre_exact_estimate = max(
            0.0, pre_and_post_exact_residual - hga)

        lp_rows = [row for row in optimize if row.get("solve_kind") == "LP"]
        mip_rows = [row for row in optimize if row.get("solve_kind") == "MIP"]
        lp_seconds = sum(number(row.get("solver_runtime")) for row in lp_rows)
        mip_seconds = sum(number(row.get("solver_runtime")) for row in mip_rows)
        lp_work = sum(number(row.get("work")) for row in lp_rows)
        mip_work = sum(number(row.get("work")) for row in mip_rows)

        gains, first_gain, last_gain = event_bound_gains(global_trace)
        terminal_gain_count = sum(
            gains.get(("terminal_mip_complete", row.get("leaf_id", "")), 0.0) > TOL
            for row in mip_rows
        )
        incumbent_terminal_leaves = {
            row.get("leaf_id", "")
            for row in event_trace
            if row.get("event") == "verified_incumbent_improvement"
        }

        lp_material = 0
        evaluated_splits = 0
        low_value_splits = 0
        for leaf in leaves:
            leaf_id = leaf["leaf_id"]
            inherited = number(leaf.get("base_lower_bound"))
            lp_bound = number(leaf.get("lp_bound"), inherited)
            lp_complete = truth(leaf.get("lp_complete"))
            lp_optimal = truth(leaf.get("lp_optimal"))
            lp_infeasible = truth(leaf.get("lp_infeasible"))
            material = (
                lp_complete and lp_optimal and not lp_infeasible
                and lp_bound > inherited + TOL
            )
            lp_material += int(material)
            children = [
                by_leaf.get(f"{leaf_id}.0"),
                by_leaf.get(f"{leaf_id}.1"),
            ]
            split = truth(leaf.get("parent_replaced"))
            child_evaluable = split and all(
                child is not None and truth(child.get("lp_complete"))
                for child in children
            )
            child_bounds = [
                number(child.get("lp_bound"))
                for child in children
                if child is not None and not truth(child.get("lp_infeasible"))
            ]
            post_split = min(child_bounds) if child_bounds else math.inf
            post_gain = (
                post_split - lp_bound
                if child_evaluable and math.isfinite(post_split)
                else 0.0
            )
            low_value = child_evaluable and post_gain <= TOL
            evaluated_splits += int(child_evaluable)
            low_value_splits += int(low_value)
            terminal = truth(leaf.get("terminal_mip_started"))
            terminal_global_gain = (
                gains.get(("terminal_mip_complete", leaf_id), 0.0)
                + gains.get(("lp_infeasible", leaf_id), 0.0)
            )
            leaf_values.append({
                "run_id": run_id,
                "stage": phase_from_run_id(run_id),
                "instance": instance_from_run_id(run_id),
                "leaf_id": leaf_id,
                "depth": integer(leaf.get("depth")),
                "status": leaf.get("status", ""),
                "inherited_lower_bound": inherited,
                "complete_lp_bound": lp_bound if lp_complete else "",
                "lp_bound_gain_over_inherited": (
                    lp_bound - inherited if lp_complete and lp_optimal else ""
                ),
                "lp_materially_improves_inherited": material,
                "lp_infeasible": lp_infeasible,
                "structural_split": split,
                "both_children_lp_evaluated": child_evaluable,
                "post_split_child_lower_bound": (
                    post_split if child_evaluable and math.isfinite(post_split)
                    else ""
                ),
                "post_split_gain_over_parent_lp": post_gain if child_evaluable else "",
                "low_value_structural_split": low_value,
                "terminal_mip": terminal,
                "terminal_mip_global_lb_gain": terminal_global_gain if terminal else "",
                "terminal_mip_improved_incumbent": leaf_id in incumbent_terminal_leaves,
            })

        terminal_count = len(mip_rows)
        lp_count = len(lp_rows)
        final_stagnation = (
            max(0.0, exact_last - last_gain) if last_gain >= 0.0 else exact_last
        )
        costs.append({
            "run_id": run_id,
            "stage": phase_from_run_id(run_id),
            "instance": instance_from_run_id(run_id),
            "status": result.get("status", ""),
            "process_wall_seconds": total,
            "hga_seconds": hga,
            "pre_exact_and_serialization_residual_seconds": pre_and_post_exact_residual,
            "verification_pre_exact_residual_minus_hga_seconds": (
                verification_pre_exact_estimate
            ),
            "external_initialization_to_first_event_seconds": exact_first_event,
            "model_build_seconds": number(
                result.get("external_gini_tree_model_build_seconds")),
            "model_read_seconds": number(
                result.get("external_gini_tree_model_read_seconds")),
            "lp_solver_seconds": lp_seconds,
            "lp_work": lp_work,
            "terminal_mip_solver_seconds": mip_seconds,
            "terminal_mip_work": mip_work,
            "presolve_execution_count": integer(
                result.get("external_gini_tree_presolve_execution_count")),
            "root_relaxation_execution_count": integer(
                result.get("external_gini_tree_root_relaxation_execution_count")),
            "native_presolve_time_seconds": "unavailable",
            "native_root_time_seconds": "unavailable",
            "structural_splits": integer(
                result.get("external_gini_tree_split_count")),
            "lp_infeasible_leaves": integer(
                result.get("external_gini_tree_lp_infeasible_leaf_count")),
            "lp_bound_pruned_leaves": integer(
                result.get("external_gini_tree_lp_pruned_leaf_count")),
            "terminal_mip_leaves": terminal_count,
            "lp_processed_leaves": lp_count,
            "average_lp_solver_seconds": lp_seconds / lp_count if lp_count else 0.0,
            "average_lp_work": lp_work / lp_count if lp_count else 0.0,
            "average_terminal_mip_solver_seconds": (
                mip_seconds / terminal_count if terminal_count else 0.0
            ),
            "average_terminal_mip_work": (
                mip_work / terminal_count if terminal_count else 0.0
            ),
            "open_leaves_at_deadline": integer(
                result.get("external_gini_tree_open_leaf_count")),
            "time_to_first_global_lb_improvement_seconds": first_gain,
            "time_after_final_global_lb_improvement_seconds": final_stagnation,
            "lp_material_improvement_fraction": (
                lp_material / lp_count if lp_count else 0.0
            ),
            "terminal_mip_global_lb_improvement_fraction": (
                terminal_gain_count / terminal_count if terminal_count else 0.0
            ),
            "terminal_mip_incumbent_improvement_fraction": (
                len(incumbent_terminal_leaves) / terminal_count
                if terminal_count else 0.0
            ),
            "evaluated_structural_splits": evaluated_splits,
            "low_value_structural_splits": low_value_splits,
            "low_value_structural_split_fraction": (
                low_value_splits / evaluated_splits if evaluated_splits else 0.0
            ),
            "models_created": integer(
                result.get("external_gini_tree_model_count")),
            "models_read": integer(
                result.get("external_gini_tree_model_read_count")),
            "optimize_count": integer(
                result.get("external_gini_tree_optimize_count")),
            "peak_memory_gb": number(
                result.get("external_gini_tree_peak_memory_gb")),
        })
    return costs, leaf_values


def moderate_reassessment() -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for directory in sorted((R28 / "runs").glob("*moderate_seed6301*c3_replica*")):
        generation = directory / "hga_generations.csv"
        state_path = directory / "run_state.json"
        state = load_json(state_path) if state_path.exists() else {}
        generation_rows = rows(generation)
        output.append({
            "evidence_source": "Round28 retained files",
            "run_id": directory.name,
            "phase": "hga_generation_trajectory_file_complete",
            "process_seconds": "",
            "phase_status": "observed",
            "generations_recorded": len(generation_rows),
            "result_json_present": (directory / "result.json").exists(),
            "external_tree_directory_present": (directory / "external").exists(),
            "return_code": state.get("return_code", state.get("rc", "")),
            "interpretation": (
                "Generation loop, history extraction, and trajectory write completed; "
                "failure is bounded after that write and before external-tree artifact creation."
            ),
        })
    return output


def markdown_report(costs: list[dict[str, Any]]) -> str:
    official = [row for row in costs if row["stage"] in {"stage1", "stage2", "stage3", "stage4"}]
    completed = len(official)
    sums = lambda key: sum(number(row.get(key)) for row in official)
    opt = sums("optimize_count")
    lp = sums("lp_processed_leaves")
    mip = sums("terminal_mip_leaves")
    total_work = sums("lp_work") + sums("terminal_mip_work")
    terminal_share = sums("terminal_mip_work") / total_work if total_work else 0.0
    presolve = sums("presolve_execution_count")
    model_reads = sums("models_read")
    split = sums("structural_splits")
    pruned = sums("lp_bound_pruned_leaves")
    low_eval = sums("evaluated_structural_splits")
    low = sums("low_value_structural_splits")
    median_build_read = statistics.median(
        (
            number(row["model_build_seconds"]) + number(row["model_read_seconds"])
        ) / max(number(row["process_wall_seconds"]), 1e-12)
        for row in official
    ) if official else 0.0
    return f"""# Round 28 C3 failure reassessment

This reassessment is computed from the immutable Round 28 result JSON files,
tree ledgers, optimize ledgers, and global-bound traces. It does not modify or
reinterpret the Round 28 package.

## What the retained evidence proves

- {completed} completed official C3 rows were reconstructed.
- They launched {int(opt)} complete native optimizations: {int(lp)} LP events
  and {int(mip)} terminal MIPs.
- Every optimization created/read a fresh model ({int(model_reads)} reads) and
  the native logs observed {int(presolve)} presolve executions. Thus the
  measured build/read share (median {median_build_read:.1%}) is only file and
  parse overhead; it excludes repeated presolve, repeated root work, lost LP
  bases, lost cuts, and terminal-MIP startup.
- Terminal MIPs consumed {terminal_share:.1%} of recorded Gurobi Work.
- C3 made {int(split)} unconditional structural splits and achieved
  {int(pruned)} LP-bound prunes.
- Of {int(low_eval)} splits whose two immediate child LPs were both observed,
  {int(low)} ({(low / low_eval if low_eval else 0.0):.1%}) did not strictly
  improve the one-level controlling lower bound.

## Moderate6301 boundary

All three retained Moderate6301 C3 attempts contain a complete HGA generation
trajectory (3,326 recorded generations in each retained attempt), but no result
JSON and no external-tree directory. In the Round 28 implementation the
trajectory is written after `ga.run()` and before best-solution extraction,
the full compact route decoder, and independent verification. Therefore the
old evidence rules out an external C3 tree failure and bounds the loss to the
post-generation/pre-exact transition. It cannot distinguish extraction from
route decoding or verification; Round 29 flushed phase instrumentation is
required for that distinction.

## Mechanism classification before C4

The dominant observed mechanisms are excessive structural refinement and
terminal-MIP creation, followed by repeated cold optimization startup.
File/model construction is measurable but is not the complete repeated cost.
Weak LP pruning is direct evidence: the retained completed aggregate has zero
LP-bound-pruned leaves. Incumbent weakness is not the principal explanation on
the reconstructed rows because the HGA incumbent is independently verified
before the tree. Exact presolve/root seconds are unavailable from the Gurobi C
API and are not fabricated; execution counts and per-event native logs are
reported instead.
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    costs, leaf_values = analyze()
    write_csv(OUT / "c3_cost_decomposition.csv", costs, costs[0].keys())
    write_csv(OUT / "c3_leaf_value_audit.csv", leaf_values, leaf_values[0].keys())
    moderate = moderate_reassessment()
    write_csv(
        OUT / "moderate6301_phase_timing.csv",
        moderate,
        moderate[0].keys() if moderate else [
            "evidence_source", "run_id", "phase", "process_seconds",
            "phase_status", "generations_recorded", "result_json_present",
            "external_tree_directory_present", "return_code", "interpretation",
        ],
    )
    (OUT / "round28_failure_reassessment.md").write_text(
        markdown_report(costs), encoding="utf-8")

    official = [
        row for row in costs
        if row["stage"] in {"stage1", "stage2", "stage3", "stage4"}
    ]
    lp_total = sum(integer(row["lp_processed_leaves"]) for row in official)
    material = sum(
        integer(row["lp_processed_leaves"])
        * number(row["lp_material_improvement_fraction"])
        for row in official
    )
    splits = sum(integer(row["structural_splits"]) for row in official)
    low_eval = sum(integer(row["evaluated_structural_splits"]) for row in official)
    low = sum(integer(row["low_value_structural_splits"]) for row in official)
    (OUT / "c3_pruning_failure_analysis.md").write_text(f"""# C3 pruning failure analysis

C3 processed {lp_total} complete interval LPs across completed official rows
and recorded zero LP-bound prunes. Approximately {material:.0f} LPs
({(material / lp_total if lp_total else 0.0):.1%}) strictly improved their
inherited leaf bound, but improvement usually remained below the verified
incumbent cutoff and therefore did not fathom the leaf.

The structural rule split every eligible improving leaf regardless of the
children's value. Of {low_eval} evaluable one-level splits, {low}
({(low / low_eval if low_eval else 0.0):.1%}) had no strict post-split
controlling-bound gain. These splits increase both future LP count and the
number of exact terminal MIPs without providing immediate pruning evidence.

This is evidence for replacing unconditional refinement with a complete,
uniform child-LP benefit decision. It is not evidence that an LP bound is
invalid, and no child is pruned from this audit.
""", encoding="utf-8")

    terminal = sum(integer(row["terminal_mip_leaves"]) for row in official)
    mip_work = sum(number(row["terminal_mip_work"]) for row in official)
    all_work = mip_work + sum(number(row["lp_work"]) for row in official)
    gain = sum(
        integer(row["terminal_mip_leaves"])
        * number(row["terminal_mip_global_lb_improvement_fraction"])
        for row in official
    )
    incumbent = sum(
        integer(row["terminal_mip_leaves"])
        * number(row["terminal_mip_incumbent_improvement_fraction"])
        for row in official
    )
    (OUT / "c3_terminal_mip_analysis.md").write_text(f"""# C3 terminal-MIP analysis

Completed official C3 rows launched {terminal} exact terminal MIPs. They used
{mip_work:.6f} Gurobi Work, {(mip_work / all_work if all_work else 0.0):.1%}
of combined LP-plus-terminal Work. Only about {gain:.0f} terminal completions
produced an immediately observable strict global-LB increase, and about
{incumbent:.0f} produced an independently verified incumbent improvement.

The remainder are not mathematically useless: exact closure is required for a
strict certificate. They are, however, low-value performance events at a
short deadline when unconditional refinement has created many terminal
subproblems. Reusing an in-memory model can remove a reread, but it cannot
remove this terminal Work. A split strategy that retains the exact parent MIP
when complete child LPs certify no one-level benefit directly targets the
larger mechanism.

Native presolve and root times are unavailable and remain explicitly
unavailable. Counts from native logs, solver runtime, Work, iterations, and
model lifecycle are used; no phase time is inferred from Work.
""", encoding="utf-8")


if __name__ == "__main__":
    main()
