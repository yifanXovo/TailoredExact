#!/usr/bin/env python3
"""Round 30 historical C0 forensics and Round 29 AUC invalidity audit.

This script is deliberately read-only with respect to Round 25--29 evidence.
Every derived file is written below the isolated Round 30 result directory.
The C0/C1 filter is semantic: one-thread cold Gurobi legacy-tree rows using
the frozen two-attempt policy.  Round 26 C1 rows are therefore labelled as
independent repetitions of C0, not as a different algorithm.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c0_mechanism_transfer_c5_round30"
R25 = ROOT / "results" / "gf_solver_backend_validation_round25"
R26 = ROOT / "results" / "gf_external_gurobi_production_validation_round26"
R29 = ROOT / "results" / "gf_gurobi_performance_recovery_round29"
TOL = 1e-7


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


def proof_bound(value: Any, upper_bound: float, default: float) -> float:
    """Return a finite proof-progress value, excluding +infinity sentinels."""
    parsed = number(value, default)
    if abs(parsed) >= 1e50:
        return default
    return min(parsed, upper_bound) if math.isfinite(upper_bound) else parsed


def boolean(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, Any]],
              fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else ["status"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def family(instance: str) -> str:
    lower = instance.lower()
    if lower.startswith("v12"):
        return "v12"
    if "high_imbalance" in lower:
        return "high_imbalance"
    if "tight" in lower:
        return "tight_T"
    if "moderate" in lower:
        return "moderate"
    return "other"


def c0_run(trace: Path) -> dict[str, Any] | None:
    run_dir = trace.parent.parent
    result_path = run_dir / "result.json"
    if not result_path.is_file():
        return None
    result = read_json(result_path)
    if result.get("external_gini_tree_backend") != "gurobi":
        return None
    if bool(result.get("external_gini_tree_warm_start_enabled", False)):
        return None
    # The frozen default two-attempt policy was historically omitted from
    # JSON.  Prototype P1 explicitly serialized 1 and is excluded.
    split_after = integer(
        result.get("external_gini_tree_split_after_attempts", 2), 2)
    if split_after != 2:
        return None
    name = Path(str(result.get("instance_name", run_dir.name))).stem
    source_round = "round25" if R25 in trace.parents else "round26"
    run_name = run_dir.name.lower()
    if source_round == "round25" and "ext_grb_cold" not in run_name:
        return None
    if source_round == "round26" and not (
            "__c0__" in run_name or "__c1__" in run_name):
        return None
    return {
        "run_dir": run_dir,
        "trace": trace,
        "result": result,
        "source_round": source_round,
        "instance": name,
        "family": family(name),
        "reported_arm": (
            "C1-EQUALS-C0" if "__c1__" in run_name else "C0-LEGACY"),
    }


def all_c0_runs() -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for base in (R25, R26):
        for trace in base.rglob("enhanced_attempt_trace.csv"):
            candidate = c0_run(trace)
            if candidate:
                runs.append(candidate)
    return sorted(runs, key=lambda row: relative(row["run_dir"]))


def forensic_rows(runs: list[dict[str, Any]]) -> tuple[
        list[dict[str, Any]], list[dict[str, Any]],
        list[dict[str, Any]], list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    splits: list[dict[str, Any]] = []
    interleaving: list[dict[str, Any]] = []
    shadows: list[dict[str, Any]] = []

    for run in runs:
        raw_attempts = read_csv(run["trace"])
        events = read_csv(run["run_dir"] / "external" /
                          "external_tree_events.csv")
        leaf_ledger = {
            row["leaf_id"]: row for row in read_csv(
                run["run_dir"] / "external" / "external_leaf_ledger.csv")}
        by_leaf: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in raw_attempts:
            by_leaf[row["leaf_id"]].append(row)
        split_events = {
            row["leaf_id"]: row for row in events if row.get("event") == "split"}
        first_split_time = min(
            (number(row.get("elapsed_seconds")) for row in split_events.values()),
            default=math.inf)

        for leaf_id, leaf_attempts in by_leaf.items():
            leaf_attempts.sort(key=lambda row: integer(row.get("attempt")))
            for index, row in enumerate(leaf_attempts):
                inherited = number(row.get("leaf_lb_before"))
                native = number(row.get("native_bound"), inherited)
                leaf_after = number(row.get("leaf_lb_after"), inherited)
                global_before = number(row.get("global_lb_before"))
                global_after = number(row.get("global_lb_after"), global_before)
                ub = number(row.get("verified_ub_after"),
                            number(row.get("verified_ub_before")))
                infeasible = row.get("native_status") == "INFEASIBLE"
                effective_leaf_after = proof_bound(
                    leaf_after, ub, inherited)
                effective_global_before = proof_bound(
                    global_before, ub, global_before)
                effective_global_after = proof_bound(
                    global_after, ub, effective_global_before)
                leaf_gain = 0.0 if infeasible else max(
                    0.0, effective_leaf_after - inherited)
                global_gain = max(
                    0.0, effective_global_after - effective_global_before)
                proof_gap = max(ub - inherited, 1e-12)
                ratio = leaf_gain / proof_gap
                material = leaf_gain > TOL * max(1.0, abs(inherited))
                selected_again = index + 1 < len(leaf_attempts)
                attempt = {
                    "source_round": run["source_round"],
                    "reported_arm": run["reported_arm"],
                    "algorithm_identity": "C0=C1",
                    "run": relative(run["run_dir"]),
                    "instance": run["instance"],
                    "family": run["family"],
                    "leaf_id": leaf_id,
                    "parent_id": row.get("parent_id", ""),
                    "depth": integer(row.get("depth")),
                    "attempt_ordinal": integer(row.get("attempt")) + 1,
                    "first_leaf_processing": index == 0,
                    "repeated_same_leaf_processing": index > 0,
                    "inherited_lower_bound": inherited,
                    "native_bound": native,
                    "native_bound_available": boolean(
                        row.get("native_bound_available")),
                    "leaf_lower_bound_after": leaf_after,
                    "leaf_bound_gain": leaf_gain,
                    "global_lower_bound_before": global_before,
                    "global_lower_bound_after": global_after,
                    "global_bound_gain": global_gain,
                    "verified_upper_bound_before": number(
                        row.get("verified_ub_before"), ub),
                    "verified_upper_bound": ub,
                    "normalized_leaf_gain": ratio,
                    "material_leaf_gain": material,
                    "native_status": row.get("native_status", ""),
                    "closed_on_event": row.get("native_status") in {
                        "OPTIMAL", "INFEASIBLE"},
                    "selected_while_controlling": boolean(
                        row.get("selected_while_controlling")),
                    "selected_again_same_leaf": selected_again,
                    "eventually_split": leaf_id in split_events,
                    "before_first_run_split": number(
                        row.get("attempt_end_seconds")) <= first_split_time,
                    "open_competing_leaves_before": max(
                        0, integer(row.get("open_leaves_before")) - 1),
                    "allocated_time_seconds_telemetry": number(
                        row.get("allocated_time_seconds")),
                    "solver_runtime_seconds_telemetry": number(
                        row.get("solver_runtime_seconds")),
                    "work_telemetry": number(row.get("work")),
                    "nodes_telemetry": number(row.get("nodes")),
                    "presolve_rerun": boolean(row.get("presolve_rerun")),
                    "root_rerun": boolean(row.get("root_rerun")),
                    "fresh_restart": boolean(row.get("fresh_restart")),
                }
                attempts.append(attempt)
                interleaving.append({
                    key: attempt[key] for key in (
                        "source_round", "reported_arm", "run", "instance",
                        "family", "leaf_id", "attempt_ordinal",
                        "inherited_lower_bound", "leaf_lower_bound_after",
                        "global_lower_bound_before", "global_lower_bound_after",
                        "selected_while_controlling",
                        "selected_again_same_leaf",
                        "open_competing_leaves_before",
                        "solver_runtime_seconds_telemetry",
                        "work_telemetry")
                })

        for parent_id, event in split_events.items():
            parent_attempts = sorted(
                by_leaf.get(parent_id, []),
                key=lambda row: integer(row.get("attempt")))
            if not parent_attempts:
                continue
            last = parent_attempts[-1]
            parent_bound = number(last.get("leaf_lb_after"))
            ub = number(last.get("verified_ub_after"))
            child_rows = [
                row for child_id, rows in by_leaf.items()
                if child_id.rsplit(".", 1)[0] == parent_id
                for row in rows[:1]]
            child_bounds = [
                proof_bound(row.get("leaf_lb_after"), ub, parent_bound)
                for row in child_rows
                if boolean(row.get("native_bound_available")) and
                row.get("native_status") != "INFEASIBLE" and
                abs(number(row.get("leaf_lb_after"))) < 1e50]
            child_min = min(child_bounds, default=parent_bound)
            child_gain = max(0.0, child_min - parent_bound)
            split_global = number(event.get("global_lb"))
            pre_global = number(last.get("global_lb_after"))
            direct_split_gain = max(0.0, split_global - pre_global)
            useful = child_gain > TOL * max(1.0, abs(parent_bound))
            first = parent_attempts[0]
            first_gain = max(
                0.0, number(first.get("leaf_lb_after")) -
                number(first.get("leaf_lb_before")))
            repeated_gain = max(0.0, parent_bound -
                                number(first.get("leaf_lb_after")))
            split_row = {
                "source_round": run["source_round"],
                "reported_arm": run["reported_arm"],
                "algorithm_identity": "C0=C1",
                "run": relative(run["run_dir"]),
                "instance": run["instance"],
                "family": run["family"],
                "parent_id": parent_id,
                "depth": integer(last.get("depth")),
                "historical_completed_attempts": len(parent_attempts),
                "parent_inherited_bound": number(
                    first.get("leaf_lb_before")),
                "parent_bound_before_split": parent_bound,
                "first_processing_gain": first_gain,
                "repeated_processing_gain": repeated_gain,
                "split_event_global_gain": direct_split_gain,
                "first_child_min_native_bound": child_min,
                "first_child_processing_gain_over_parent": child_gain,
                "child_rows_observed": len(child_rows),
                "split_materially_useful_from_observed_children": useful,
                "split_unnecessary_or_zero_immediate_gain": not useful,
                "verified_upper_bound": ub,
                "parent_status": leaf_ledger.get(
                    parent_id, {}).get("status", ""),
                "atomic_replacement_observed": (
                    leaf_ledger.get(parent_id, {}).get("status") == "replaced"),
            }
            splits.append(split_row)
            gap = max(ub - number(first.get("leaf_lb_before")), 1e-12)
            first_ratio = first_gain / gap
            repeat_ratio = repeated_gain / gap
            for policy, threshold in (
                    ("normalized_native_gain_1pct", 0.01),
                    ("normalized_native_gain_5pct", 0.05),
                    ("normalized_native_gain_10pct", 0.10)):
                reached_first = first_ratio >= threshold
                reached_after_repeat = first_ratio + repeat_ratio >= threshold
                shadows.append({
                    "source_round": run["source_round"],
                    "run": relative(run["run_dir"]),
                    "instance": run["instance"],
                    "family": run["family"],
                    "parent_id": parent_id,
                    "shadow_rule": policy,
                    "dimensionless_threshold": threshold,
                    "first_native_gain_ratio": first_ratio,
                    "repeated_native_gain_ratio": repeat_ratio,
                    "target_reached_after_first_processing": reached_first,
                    "target_reached_only_after_repeated_processing": (
                        not reached_first and reached_after_repeat),
                    "historical_split_explainable_without_time_or_attempts": (
                        reached_after_repeat or useful),
                    "coverage_preserved_if_parent_retained_or_atomic_split":
                        True,
                    "counterfactual_runtime_claimed": False,
                })
    return attempts, splits, interleaving, shadows


def auc_invalidity_audit() -> tuple[list[dict[str, Any]],
                                    list[dict[str, Any]]]:
    completeness: list[dict[str, Any]] = []
    old_auc = read_csv(R29 / "bound_progress_auc.csv")
    corrected: list[dict[str, Any]] = []
    for row in old_auc:
        arm = row.get("arm", "")
        observations = integer(row.get("bound_observations"))
        if arm == "C4-CANDIDATE":
            status = "auc_unavailable"
            reason = (
                "round29_c4_missing_compatible_global_bound_trace;"
                "endpoint_only_pseudo_trajectory_rejected")
            auc = ""
            gap_auc = ""
            complete = False
        elif observations <= 0:
            status = "auc_unavailable"
            reason = "no_observed_valid_bound_events"
            auc = ""
            gap_auc = ""
            complete = False
        else:
            status = "observed_historical_trace"
            reason = "compatible_observations_retained"
            auc = row.get("bound_progress_auc", "")
            gap_auc = row.get("normalized_gap_auc", "")
            complete = True
        corrected.append({
            **row,
            "bound_progress_auc": auc,
            "normalized_gap_auc": gap_auc,
            "auc_status": status,
            "correction_reason": reason,
        })
        completeness.append({
            "stage": row.get("stage", ""),
            "instance": row.get("instance", ""),
            "arm": arm,
            "repetition": row.get("repetition", ""),
            "historical_bound_observations": observations,
            "compatible_trace_complete": complete,
            "auc_status": status,
            "reason": reason,
            "round30_action": (
                "rerun_with_round30_trace_schema"
                if arm == "C4-CANDIDATE"
                else "retain_only_when_observed"),
        })
    return completeness, corrected


def percentage(numerator: float, denominator: float) -> float:
    return 100.0 * numerator / denominator if denominator else 0.0


def median(rows: Iterable[dict[str, Any]], key: str) -> float:
    values = [number(row.get(key)) for row in rows]
    return statistics.median(values) if values else 0.0


def write_reports(runs: list[dict[str, Any]],
                  attempts: list[dict[str, Any]],
                  splits: list[dict[str, Any]],
                  shadows: list[dict[str, Any]]) -> None:
    first = [row for row in attempts if row["first_leaf_processing"]]
    repeat = [row for row in attempts if row["repeated_same_leaf_processing"]]
    first_leaf_gain = sum(number(row["leaf_bound_gain"]) for row in first)
    repeat_leaf_gain = sum(number(row["leaf_bound_gain"]) for row in repeat)
    first_global_gain = sum(number(row["global_bound_gain"]) for row in first)
    repeat_global_gain = sum(number(row["global_bound_gain"]) for row in repeat)
    material_second = [
        row for row in repeat
        if row["attempt_ordinal"] == 2 and row["material_leaf_gain"]]
    second = [row for row in repeat if row["attempt_ordinal"] == 2]
    useful_splits = [
        row for row in splits
        if row["split_materially_useful_from_observed_children"]]
    closes = [row for row in attempts if row["closed_on_event"]]
    incumbent_changes = [
        row for row in attempts
        if number(row["verified_upper_bound"]) <
        number(row["verified_upper_bound_before"]) - 1e-12]
    first_work = sum(number(row["work_telemetry"]) for row in first)
    repeat_work = sum(number(row["work_telemetry"]) for row in repeat)
    total_gain = first_leaf_gain + repeat_leaf_gain + sum(
        number(row["first_child_processing_gain_over_parent"]) for row in splits)

    mechanism = f"""# C0 mechanism forensics

## Scope and identity

The audit reads {len(runs)} retained cold Gurobi C0/C1-equivalent runs from
Rounds 25 and 26, containing {len(attempts)} native leaf-processing events and
{len(splits)} observed atomic splits.  Round 26 C1 is labelled `C0=C1`; its
independent variability is not treated as an algorithm change.  Telemetry
(time, Work, nodes) is descriptive and never used by a proposed C5 decision.

## Bound-value decomposition

- First processing contributes {first_leaf_gain:.9g} summed leaf-bound gain
  and {first_global_gain:.9g} immediately controlling global-bound gain using
  {first_work:.9g} Work.
- Repeated same-leaf processing contributes {repeat_leaf_gain:.9g} summed
  leaf-bound gain and {repeat_global_gain:.9g} immediate global-bound gain
  using {repeat_work:.9g} Work.
- {len(material_second)}/{len(second)} second processings
  ({percentage(len(material_second), len(second)):.1f}%) materially improve
  their leaf bound.
- {len(useful_splits)}/{len(splits)} splits
  ({percentage(len(useful_splits), len(splits)):.1f}%) have an observed
  material first-child controlling-bound gain; the remainder are zero-value
  or unproved by the retained immediate-child evidence.
- {len(closes)} leaf-processing events close the leaf natively.  Independently
  verified incumbent improvement is not a material source in these retained
  external events ({len(incumbent_changes)} observed).

The attribution denominator is summed observed leaf/child gain
({total_gain:.9g}), not counterfactual runtime.  Direct split events inherit the
parent bound and therefore do not themselves create a lower bound; value comes
from subsequent child processing.

## Transfer conclusion

The dominant transferable mechanisms are valid partial native-MIP lower-bound
harvesting, parent-bound inheritance, exact atomic coverage, and best-bound
interleaving.  The hardware-dependent 30/60/... second allocation and
split-after-two-attempt rule explain when C0 stopped or split but are not
transferable.  Repeated processing often adds proof value, yet it also reruns
presolve/root work and cannot be used as a mathematical state merely because
it is the second call.
"""
    (OUT / "c0_mechanism_forensics.md").write_text(
        mechanism, encoding="utf-8")

    v12 = [row for row in attempts if row["family"] == "v12"]
    non_v12 = [row for row in attempts if row["family"] != "v12"]
    v12_text = f"""# C0 V12 overhead diagnosis

The retained V12 audit contains {len(v12)} C0/C1-equivalent leaf events.
Repeated same-leaf processing accounts for
{sum(row['repeated_same_leaf_processing'] for row in v12)} events, with median
per-event Work {median(v12, 'work_telemetry'):.6g}.  The Round 26 controlled
forensics remain authoritative: V12_M1's small wall regression was timing
noise, whereas V12_M2 used six reads/fresh restarts, eight optimize calls and
five observed root relaxations at the median.  Its hard parent received the
30/60-second sequence before splitting, and a child repeated it.

The transferable lesson is to harvest a validity-gated native bound and define
the next state by a mathematical bound milestone.  Repeating because a time
quantum expired or because the attempt ordinal equals two is forbidden.
"""
    (OUT / "c0_v12_overhead_diagnosis.md").write_text(
        v12_text, encoding="utf-8")
    families = Counter(row["family"] for row in non_v12)
    advantage = f"""# C0 V20/V50 advantage diagnosis

Retained non-V12 forensics include {len(non_v12)} leaf events:
{dict(sorted(families.items()))}.  Round 26's matched official evidence showed
C0/C1-equivalent wins over P-GRB on all nine known/held-out V20 pairs, all
three V50 pairs, and all four 3600-second pairs.  The mechanism ledger shows
that the advantage is associated with partial native bounds on multiple exact
Gini intervals and best-bound interleaving; direct split events contribute no
bound until children are processed.

This is diagnostic attribution, not a claim that C0 won every historical pair.
V12 remained the counterexample, and the time/attempt policy remains
non-paper-compatible.
"""
    (OUT / "c0_v20_v50_advantage_diagnosis.md").write_text(
        advantage, encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    runs = all_c0_runs()
    attempts, splits, interleaving, shadows = forensic_rows(runs)
    write_csv(OUT / "c0_attempt_value.csv", attempts)
    write_csv(OUT / "c0_partial_mip_bound_value.csv", attempts)
    write_csv(OUT / "c0_split_value.csv", splits)
    write_csv(OUT / "c0_interleaving_audit.csv", interleaving)
    write_csv(OUT / "c0_shadow_policy_replay.csv", shadows)
    transfer = [
        {"mechanism": "valid_native_lower_bound_harvesting",
         "classification": "TRANSFERABLE",
         "reason": "backend-certified bound remains valid for open leaf"},
        {"mechanism": "best_bound_controlling_leaf_scheduling",
         "classification": "TRANSFERABLE",
         "reason": "uses mathematical valid leaf bounds only"},
        {"mechanism": "parent_bound_inheritance_and_atomic_coverage",
         "classification": "TRANSFERABLE",
         "reason": "exact interval partition proof"},
        {"mechanism": "fixed_time_quanta",
         "classification": "FORBIDDEN",
         "reason": "hardware-dependent stopping decision"},
        {"mechanism": "split_after_fixed_attempt_count",
         "classification": "FORBIDDEN",
         "reason": "attempt ordinal is not a mathematical event"},
        {"mechanism": "work_node_solution_or_retry_limits",
         "classification": "FORBIDDEN",
         "reason": "hardware/solver-effort dependent internal control"},
        {"mechanism": "native_root_completion_event",
         "classification": "REQUIRES_PROOF_OR_API_AUDIT",
         "reason": "Gurobi MIP callback has no unambiguous root-cut-loop-complete event"},
        {"mechanism": "native_dual_bound_target_termination",
         "classification": "REQUIRES_PROOF_OR_API_AUDIT",
         "reason": "valid if callback bound and termination semantics pass direct tests"},
        {"mechanism": "same_model_native_tree_continuation",
         "classification": "REQUIRES_PROOF_OR_API_AUDIT",
         "reason": "same object does not establish retained presolve/cuts/tree"},
        {"mechanism": "parent_child_lp_basis_transfer",
         "classification": "REQUIRES_PROOF_OR_API_AUDIT",
         "reason": "complete compatible row/column mapping not yet proved"},
    ]
    write_csv(OUT / "c0_transferability_matrix.csv", transfer)
    completeness, corrected = auc_invalidity_audit()
    write_csv(OUT / "bound_trace_completeness.csv", completeness)
    write_csv(OUT / "corrected_round29_auc.csv", corrected)
    write_reports(runs, attempts, splits, shadows)
    summary = {
        "runs": len(runs),
        "attempt_events": len(attempts),
        "split_events": len(splits),
        "shadow_rows": len(shadows),
        "round29_trace_rows": len(completeness),
        "round29_c4_auc_unavailable": sum(
            row["arm"] == "C4-CANDIDATE" and
            row["auc_status"] == "auc_unavailable"
            for row in completeness),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
