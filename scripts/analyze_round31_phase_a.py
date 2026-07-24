#!/usr/bin/env python3
"""Round 31 evidence-led C5/C0/plain-Gurobi failure forensics."""

from __future__ import annotations

import csv
import gzip
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, TextIO


ROOT = Path(__file__).resolve().parents[1]
R30 = ROOT / "results" / "gf_c0_mechanism_transfer_c5_round30"
OUT = ROOT / "results" / "gf_nonblocking_gurobi_c6_round31"
TOL = 1e-7

FINAL_LB_LOSSES = {
    "high_imbalance_seed6202",
    "tight_T_seed4101",
    "tight_T_seed5102",
    "tight_T_seed5103",
}
AUC_REGRESSIONS = {
    "V12_M1",
    "V12_M2",
    "high_imbalance_seed6202",
    "moderate_seed5302",
    "moderate_seed6301",
    "tight_T_seed4101",
    "tight_T_seed5102",
    "tight_T_seed5103",
    "tight_T_seed6102",
}
C0_ADVANTAGE_TARGETS = {
    "tight_T_seed5102",
    "moderate_seed3302",
}
CRITICAL = sorted(FINAL_LB_LOSSES | AUC_REGRESSIONS | C0_ADVANTAGE_TARGETS)


def open_text(path: Path) -> TextIO:
    candidate = path
    if not candidate.is_file() and Path(str(path) + ".gz").is_file():
        candidate = Path(str(path) + ".gz")
    if candidate.suffix.lower() == ".gz":
        return gzip.open(candidate, "rt", encoding="utf-8", errors="replace")
    return candidate.open("r", encoding="utf-8", errors="replace")


def csv_rows(path: Path) -> list[dict[str, str]]:
    candidate = path
    if not candidate.is_file() and Path(str(path) + ".gz").is_file():
        candidate = Path(str(path) + ".gz")
    if not candidate.is_file():
        return []
    with open_text(candidate) as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    material = list(rows)
    fields: list[str] = []
    for row in material:
        for field in row:
            if field not in fields:
                fields.append(field)
    if not fields:
        fields = ["status"]
        material = [{"status": "no_rows"}]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(material)


def num(value: Any, default: float = math.nan) -> float:
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


def finite(value: float) -> bool:
    return math.isfinite(value)


def leaf_depth(leaf_id: str) -> int:
    return leaf_id.count(".") if leaf_id else -1


def parent_id(leaf_id: str) -> str:
    return leaf_id.rsplit(".", 1)[0] if "." in leaf_id else ""


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def run_maps() -> tuple[
        dict[tuple[str, str], Path], list[dict[str, str]]]:
    stage2 = csv_rows(R30 / "stage2_full_300s_results.csv")
    mapping: dict[tuple[str, str], Path] = {}
    for row in stage2:
        mapping[(row["instance"], row["arm"])] = ROOT / row["run_path"]
    return mapping, stage2


def lp_by_leaf(run_dir: Path) -> dict[str, dict[str, str]]:
    return {
        row["leaf_id"]: row
        for row in csv_rows(run_dir / "external/paper_optimize_ledger.csv")
        if row.get("solve_kind") == "LP"
    }


def optimize_by_leaf(run_dir: Path) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in csv_rows(run_dir / "external/paper_optimize_ledger.csv"):
        grouped[row.get("leaf_id", "")].append(row)
    return grouped


def trace_rows(run_dir: Path) -> list[dict[str, str]]:
    return csv_rows(run_dir / "external/global_bound_trace.csv")


def comparison_maps() -> tuple[
        dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    p = {
        row["instance"]: row
        for row in csv_rows(R30 / "p_grb_vs_c5.csv")
    }
    c0 = {
        row["instance"]: row
        for row in csv_rows(R30 / "c0_vs_c5_diagnostic.csv")
    }
    return p, c0


def parent_native_first_rows(
        mapping: dict[tuple[str, str], Path]
        ) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instance in sorted({key[0] for key in mapping}):
        run_dir = mapping.get((instance, "C5-CANDIDATE"))
        if not run_dir:
            continue
        trace = trace_rows(run_dir)
        optimize = optimize_by_leaf(run_dir)
        split = {
            row["parent_id"]: row
            for row in csv_rows(
                run_dir / "external/split_decision_ledger.csv")
        }
        bounds = {
            row["parent_id"]: row
            for row in csv_rows(
                run_dir / "external/parent_child_bound_ledger.csv")
        }
        for index, event in enumerate(trace):
            if event.get("event_type") != "parent_lp_completion":
                continue
            leaf = event.get("active_leaf", "")
            active = num(event.get("active_leaf_valid_lower_bound"))
            other = num(event.get("other_open_leaf_min_valid_lower_bound"))
            pc = bounds.get(leaf, {})
            sd = split.get(leaf, {})
            left = pc.get("left_id", f"{leaf}.0")
            right = pc.get("right_id", f"{leaf}.1")
            child_rows = [
                row for child in (left, right)
                for row in optimize.get(child, [])
                if row.get("solve_kind") == "LP"
            ]
            child_work = sum(num(row.get("work"), 0.0) for row in child_rows)
            child_runtime = sum(
                num(row.get("solver_runtime"), 0.0) for row in child_rows)
            terminal = next((
                row for row in optimize.get(leaf, [])
                if row.get("solve_kind") == "MIP"), {})
            partial = next((
                row for row in optimize.get(leaf, [])
                if row.get("solve_kind") == "PARTIAL_MIP_TARGET"), {})
            next_target = (
                other if finite(other) and other > active + TOL
                else math.nan)
            requeue_after_lp = (
                finite(other) and active + TOL >= other)
            rows.append({
                "instance": instance,
                "critical_instance": instance in CRITICAL,
                "run_id": run_dir.name,
                "trace_index": index,
                "parent_id": leaf,
                "depth": leaf_depth(leaf),
                "parent_lp_bound": active,
                "other_open_leaf_min_bound": other,
                "parent_still_strictly_controlling_after_lp":
                    finite(other) and active + TOL < other,
                "parameter_free_next_leaf_target_available":
                    finite(next_target),
                "next_leaf_target": next_target,
                "safe_requeue_after_parent_lp": requeue_after_lp,
                "child_lp_calls_paid_at_this_selection": len(child_rows),
                "child_lp_work_paid": child_work,
                "child_lp_runtime_paid": child_runtime,
                "child_lookahead_deferable_under_parent_first":
                    requeue_after_lp,
                "split_reason": sd.get("reason", "not_eligible_or_missing"),
                "normalized_child_gain":
                    num(sd.get("normalized_disjunction_gain")),
                "post_split_bound": num(pc.get("post_split_bound")),
                "partial_target_launched": bool(partial),
                "partial_target_work": num(partial.get("work"), 0.0),
                "terminal_mip_launched": bool(terminal),
                "terminal_mip_status": terminal.get("native_status", ""),
                "terminal_mip_work": num(terminal.get("work"), 0.0),
                "terminal_mip_runtime":
                    num(terminal.get("solver_runtime"), 0.0),
                "terminal_mip_would_be_deferred_at_this_selection":
                    requeue_after_lp and bool(terminal),
            })
    return rows


def child_lookahead_rows(
        mapping: dict[tuple[str, str], Path],
        parent_first: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parent_index = {
        (row["instance"], row["parent_id"]): row for row in parent_first
    }
    rows: list[dict[str, Any]] = []
    for instance in sorted({key[0] for key in mapping}):
        run_dir = mapping.get((instance, "C5-CANDIDATE"))
        if not run_dir:
            continue
        optimize = optimize_by_leaf(run_dir)
        split = {
            row["parent_id"]: row
            for row in csv_rows(
                run_dir / "external/split_decision_ledger.csv")
        }
        for pc in csv_rows(
                run_dir / "external/parent_child_bound_ledger.csv"):
            leaf = pc["parent_id"]
            sd = split.get(leaf, {})
            child_rows = [
                row for child in (pc.get("left_id"), pc.get("right_id"))
                for row in optimize.get(child or "", [])
                if row.get("solve_kind") == "LP"
            ]
            parent_bound = num(pc.get("parent_lp_bound"))
            post = num(pc.get("post_split_bound"))
            raw_gain = post - parent_bound
            pfirst = parent_index.get((instance, leaf), {})
            rows.append({
                "instance": instance,
                "critical_instance": instance in CRITICAL,
                "run_id": run_dir.name,
                "parent_id": leaf,
                "depth": leaf_depth(leaf),
                "parent_bound": parent_bound,
                "left_bound": num(pc.get("left_lp_bound")),
                "left_infeasible": truth(pc.get("left_infeasible")),
                "right_bound": num(pc.get("right_lp_bound")),
                "right_infeasible": truth(pc.get("right_infeasible")),
                "post_split_bound": post,
                "raw_child_disjunction_gain": raw_gain,
                "normalized_child_gain":
                    num(sd.get("normalized_disjunction_gain")),
                "decision": pc.get("decision", sd.get("reason", "")),
                "split": truth(sd.get("split")),
                "target_phase_required":
                    truth(sd.get("target_phase_required")),
                "child_lp_calls": len(child_rows),
                "child_lp_work":
                    sum(num(row.get("work"), 0.0) for row in child_rows),
                "child_lp_runtime": sum(
                    num(row.get("solver_runtime"), 0.0)
                    for row in child_rows),
                "current_mathematical_value":
                    truth(sd.get("split")) or raw_gain > TOL,
                "safe_parent_first_deferral":
                    pfirst.get(
                        "child_lookahead_deferable_under_parent_first",
                        False),
                "parent_was_noncontrolling_after_lp":
                    pfirst.get("safe_requeue_after_parent_lp", False),
            })
    return rows


def forced_split_rows(
        mapping: dict[tuple[str, str], Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instance in sorted({key[0] for key in mapping}):
        run_dir = mapping.get((instance, "C5-CANDIDATE"))
        if not run_dir:
            continue
        trace = trace_rows(run_dir)
        bounds = {
            row["parent_id"]: row
            for row in csv_rows(
                run_dir / "external/parent_child_bound_ledger.csv")
        }
        for sd in csv_rows(
                run_dir / "external/split_decision_ledger.csv"):
            if not truth(sd.get("target_phase_required")):
                continue
            leaf = sd["parent_id"]
            target_events = [
                (index, row) for index, row in enumerate(trace)
                if row.get("active_leaf") == leaf
                and row.get("event_source") ==
                    "c5_target_reached_parent_requeued_before_split"
            ]
            delayed = [
                (index, row) for index, row in enumerate(trace)
                if row.get("active_leaf") == leaf
                and row.get("event_source") ==
                    "c5_parent_native_target_reached_delayed_atomic_split"
            ]
            pc = bounds.get(leaf, {})
            target = num(sd.get("parent_native_bound_target"))
            target_index, target_event = (
                target_events[-1] if target_events else (-1, {}))
            split_index, split_event = (
                delayed[-1] if delayed else (-1, {}))
            parent_at_target = num(
                target_event.get("active_leaf_valid_lower_bound"))
            post = num(pc.get("post_split_bound"), target)
            gain_at_split = (
                post - parent_at_target
                if finite(post) and finite(parent_at_target) else math.nan)
            before_global = (
                num(trace[split_index - 1].get("valid_global_lower_bound"))
                if split_index > 0 else math.nan)
            after_global = num(split_event.get("valid_global_lower_bound"))
            rows.append({
                "instance": instance,
                "critical_instance": instance in CRITICAL,
                "run_id": run_dir.name,
                "parent_id": leaf,
                "depth": leaf_depth(leaf),
                "original_normalized_child_gain":
                    num(sd.get("normalized_disjunction_gain")),
                "frozen_child_target": target,
                "parent_bound_at_target": parent_at_target,
                "child_disjunction_bound_at_delayed_split": post,
                "current_raw_gain_at_delayed_split": gain_at_split,
                "current_gain_exceeds_certificate_tolerance":
                    finite(gain_at_split) and gain_at_split > TOL,
                "current_gain_reaches_rho": False,
                "target_event_seen": target_index >= 0,
                "delayed_split_seen": split_index >= 0,
                "global_lb_before_delayed_split": before_global,
                "global_lb_after_delayed_split": after_global,
                "immediate_global_lb_gain": (
                    after_global - before_global
                    if finite(before_global) and finite(after_global)
                    else math.nan),
                "forced_split_avoidable_under_current_value_rule":
                    finite(gain_at_split) and gain_at_split <= TOL,
                "audit_conclusion": (
                    "parent_caught_child_bound_no_current_rho_value"
                    if finite(gain_at_split) and gain_at_split <= TOL
                    else "current_gain_remains_positive_or_unavailable"),
            })
    return rows


def no_gain_rows(
        mapping: dict[tuple[str, str], Path],
        parent_first: list[dict[str, Any]]) -> list[dict[str, Any]]:
    parent_index = {
        (row["instance"], row["parent_id"]): row for row in parent_first
    }
    rows: list[dict[str, Any]] = []
    for instance in sorted({key[0] for key in mapping}):
        run_dir = mapping.get((instance, "C5-CANDIDATE"))
        if not run_dir:
            continue
        optimize = optimize_by_leaf(run_dir)
        bounds = {
            row["parent_id"]: row
            for row in csv_rows(
                run_dir / "external/parent_child_bound_ledger.csv")
        }
        trace = trace_rows(run_dir)
        for sd in csv_rows(
                run_dir / "external/split_decision_ledger.csv"):
            if sd.get("reason") != "no_strict_child_disjunction_gain":
                continue
            leaf = sd["parent_id"]
            terminal = next((
                row for row in optimize.get(leaf, [])
                if row.get("solve_kind") == "MIP"), {})
            declined = next((
                row for row in trace
                if row.get("active_leaf") == leaf
                and row.get("event_type") == "declined_split"), {})
            pfirst = parent_index.get((instance, leaf), {})
            pc = bounds.get(leaf, {})
            rows.append({
                "instance": instance,
                "critical_instance": instance in CRITICAL,
                "run_id": run_dir.name,
                "parent_id": leaf,
                "depth": leaf_depth(leaf),
                "parent_bound": num(pc.get("parent_lp_bound")),
                "child_disjunction_bound": num(pc.get("post_split_bound")),
                "other_open_leaf_min_at_decline": num(
                    declined.get("other_open_leaf_min_valid_lower_bound")),
                "parent_noncontrolling_after_lp":
                    pfirst.get("safe_requeue_after_parent_lp", False),
                "finite_next_leaf_target_available":
                    pfirst.get(
                        "parameter_free_next_leaf_target_available", False),
                "next_leaf_target": pfirst.get("next_leaf_target", math.nan),
                "terminal_mip_launched": bool(terminal),
                "terminal_status": terminal.get("native_status", ""),
                "terminal_runtime": num(terminal.get("solver_runtime"), 0.0),
                "terminal_work": num(terminal.get("work"), 0.0),
                "terminal_nodes": num(terminal.get("nodes"), 0.0),
                "deadline_remaining_at_launch": num(
                    terminal.get(
                        "global_deadline_remaining_at_launch"), 0.0),
                "deadline_blocking": (
                    bool(terminal)
                    and terminal.get("native_status") not in {
                        "OPTIMAL", "INFEASIBLE"}
                ),
                "c6_nonblocking_opportunity": (
                    pfirst.get("safe_requeue_after_parent_lp", False)
                    or pfirst.get(
                        "parameter_free_next_leaf_target_available", False)
                ),
            })
    return rows


MODEL_RE = re.compile(
    r"Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros")
VARIABLE_RE = re.compile(
    r"Variable types: (\d+) continuous, (\d+) integer \((\d+) binary\)")
PRESOLVE_RE = re.compile(
    r"Presolve removed (\d+) rows and (\d+) columns")
PRESOLVED_RE = re.compile(
    r"Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros")
ROOT_RE = re.compile(
    r"Root relaxation: objective\s+([+\-\deE.]+),\s+"
    r"(\d+) iterations,\s+([\d.]+) seconds \(([\d.]+) work units\)")
LP_SOLVED_RE = re.compile(
    r"Solved in (\d+) iterations and ([\d.]+) seconds "
    r"\(([\d.]+) work units\)")
LP_OBJECTIVE_RE = re.compile(r"Optimal objective\s+([+\-\deE.]+)")
EXPLORED_RE = re.compile(
    r"Explored (\d+) nodes \((\d+) simplex iterations\) in "
    r"([\d.]+) seconds \(([\d.]+) work units\)")
RANGE_RE = re.compile(
    r"^\s*(Matrix|Objective|Bounds|RHS) range\s+\[([^,]+),\s*([^\]]+)\]",
    re.MULTILINE)
CUT_RE = re.compile(r"^\s{2}([^:\n]+):\s+(\d+)\s*$", re.MULTILINE)


def parse_native_log(path_value: str | Path) -> dict[str, Any]:
    path = Path(path_value)
    if not path.is_file() and Path(str(path) + ".gz").is_file():
        path = Path(str(path) + ".gz")
    if not path.is_file():
        return {"log_available": False}
    with open_text(path) as stream:
        text = stream.read()
    out: dict[str, Any] = {
        "log_available": True,
        "log_path": path.relative_to(ROOT).as_posix(),
    }
    match = MODEL_RE.search(text)
    if match:
        out.update({
            "model_rows": int(match.group(1)),
            "model_columns": int(match.group(2)),
            "model_nonzeros": int(match.group(3)),
        })
    match = VARIABLE_RE.search(text)
    if match:
        out.update({
            "continuous_variables": int(match.group(1)),
            "integer_variables": int(match.group(2)),
            "binary_variables": int(match.group(3)),
        })
    match = PRESOLVE_RE.search(text)
    if match:
        out.update({
            "presolve_removed_rows": int(match.group(1)),
            "presolve_removed_columns": int(match.group(2)),
        })
    match = PRESOLVED_RE.search(text)
    if match:
        out.update({
            "presolved_rows": int(match.group(1)),
            "presolved_columns": int(match.group(2)),
            "presolved_nonzeros": int(match.group(3)),
        })
    match = ROOT_RE.search(text)
    if match:
        out.update({
            "root_relaxation_objective": float(match.group(1)),
            "root_iterations": int(match.group(2)),
            "root_seconds": float(match.group(3)),
            "root_work": float(match.group(4)),
        })
    match = LP_SOLVED_RE.search(text)
    if match:
        out.update({
            "lp_iterations": int(match.group(1)),
            "lp_seconds": float(match.group(2)),
            "lp_work": float(match.group(3)),
        })
    match = LP_OBJECTIVE_RE.search(text)
    if match:
        out["lp_objective"] = float(match.group(1))
    match = EXPLORED_RE.search(text)
    if match:
        out.update({
            "explored_nodes": int(match.group(1)),
            "total_simplex_iterations": int(match.group(2)),
            "native_seconds": float(match.group(3)),
            "native_work": float(match.group(4)),
        })
    for label, lower, upper in RANGE_RE.findall(text):
        stem = label.lower()
        out[f"{stem}_range_min"] = lower.strip()
        out[f"{stem}_range_max"] = upper.strip()
    cuts = {
        label.strip(): int(count)
        for label, count in CUT_RE.findall(text)
        if label.strip() not in {
            "Matrix range", "Objective range", "Bounds range", "RHS range"}
    }
    out["reported_cut_families"] = len(cuts)
    out["reported_cut_count"] = sum(cuts.values())
    out["cut_summary"] = ";".join(
        f"{label}={count}" for label, count in sorted(cuts.items()))
    return out


def lp_pattern_rows(
        mapping: dict[tuple[str, str], Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instance in CRITICAL:
        run_dir = mapping.get((instance, "C5-CANDIDATE"))
        if not run_dir:
            continue
        for row in csv_rows(
                run_dir / "external/paper_optimize_ledger.csv"):
            if row.get("solve_kind") != "LP":
                continue
            metrics = parse_native_log(row.get("native_log", ""))
            rows.append({
                "instance": instance,
                "run_id": run_dir.name,
                "arm": "C5-CANDIDATE",
                "leaf_id": row.get("leaf_id"),
                "depth": leaf_depth(row.get("leaf_id", "")),
                "status": row.get("native_status"),
                "ledger_work": num(row.get("work"), 0.0),
                "ledger_runtime": num(row.get("solver_runtime"), 0.0),
                **metrics,
                "primal_dual_vector_export_available": False,
                "binding_row_family_counts_available": False,
                "fractional_pattern_export_available": False,
            })
    return rows


def root_pattern_rows(
        mapping: dict[tuple[str, str], Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instance in CRITICAL:
        for arm in ("P-GRB", "C5-CANDIDATE"):
            run_dir = mapping.get((instance, arm))
            if not run_dir:
                continue
            if arm == "P-GRB":
                metrics = parse_native_log(run_dir / "native.log")
                rows.append({
                    "instance": instance,
                    "run_id": run_dir.name,
                    "arm": arm,
                    "leaf_id": "complete_original_model",
                    "solve_kind": "MIP",
                    **metrics,
                })
                continue
            for row in csv_rows(
                    run_dir / "external/paper_optimize_ledger.csv"):
                if row.get("solve_kind") == "LP":
                    continue
                metrics = parse_native_log(row.get("native_log", ""))
                rows.append({
                    "instance": instance,
                    "run_id": run_dir.name,
                    "arm": arm,
                    "leaf_id": row.get("leaf_id"),
                    "depth": leaf_depth(row.get("leaf_id", "")),
                    "solve_kind": row.get("solve_kind"),
                    "native_status": row.get("native_status"),
                    "ledger_work": num(row.get("work"), 0.0),
                    "ledger_runtime": num(row.get("solver_runtime"), 0.0),
                    "ledger_nodes": num(row.get("nodes"), 0.0),
                    **metrics,
                })
    return rows


def terminal_leaf_rows(
        mapping: dict[tuple[str, str], Path],
        parent_first: list[dict[str, Any]],
        no_gain: list[dict[str, Any]],
        root_patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pfirst = {
        (row["instance"], row["parent_id"]): row for row in parent_first
    }
    nogain = {
        (row["instance"], row["parent_id"]): row for row in no_gain
    }
    patterns = {
        (row["instance"], row.get("leaf_id")): row
        for row in root_patterns if row.get("arm") == "C5-CANDIDATE"
    }
    raw: list[dict[str, Any]] = []
    for instance in sorted({key[0] for key in mapping}):
        run_dir = mapping.get((instance, "C5-CANDIDATE"))
        if not run_dir:
            continue
        leaf_ledger = {
            row["leaf_id"]: row
            for row in csv_rows(
                run_dir / "external/paper_leaf_ledger.csv")
        }
        split = {
            row["parent_id"]: row
            for row in csv_rows(
                run_dir / "external/split_decision_ledger.csv")
        }
        for row in csv_rows(
                run_dir / "external/paper_optimize_ledger.csv"):
            if row.get("solve_kind") != "MIP":
                continue
            leaf = row.get("leaf_id", "")
            work = num(row.get("work"), 0.0)
            runtime = num(row.get("solver_runtime"), 0.0)
            nodes = num(row.get("nodes"), 0.0)
            sd = split.get(leaf, {})
            pf = pfirst.get((instance, leaf), {})
            ng = nogain.get((instance, leaf), {})
            pattern = patterns.get((instance, leaf), {})
            root_work = num(pattern.get("root_work"), 0.0)
            raw.append({
                "instance": instance,
                "critical_instance": instance in CRITICAL,
                "run_id": run_dir.name,
                "leaf_id": leaf,
                "depth": leaf_depth(leaf),
                "gamma_L": num(leaf_ledger.get(leaf, {}).get("gamma_L")),
                "gamma_U": num(leaf_ledger.get(leaf, {}).get("gamma_U")),
                "interval_width": (
                    num(leaf_ledger.get(leaf, {}).get("gamma_U"))
                    - num(leaf_ledger.get(leaf, {}).get("gamma_L"))),
                "split_reason": sd.get("reason", "structurally_terminal"),
                "native_status": row.get("native_status"),
                "runtime": runtime,
                "work": work,
                "nodes": nodes,
                "deadline_remaining_at_launch": num(
                    row.get("global_deadline_remaining_at_launch"), 0.0),
                "deadline_blocking":
                    row.get("native_status") not in {"OPTIMAL", "INFEASIBLE"},
                "safe_requeue_available_after_parent_lp":
                    pf.get("safe_requeue_after_parent_lp", False),
                "next_leaf_target_available":
                    pf.get(
                        "parameter_free_next_leaf_target_available", False),
                "no_gain_parent": bool(ng),
                "root_work": root_work,
                "root_work_share": (
                    root_work / work if work > 0.0 else math.nan),
                "reported_cut_count":
                    integer(pattern.get("reported_cut_count")),
                "model_rows": integer(pattern.get("model_rows")),
                "model_columns": integer(pattern.get("model_columns")),
                "model_nonzeros": integer(pattern.get("model_nonzeros")),
            })
    works = [row["work"] for row in raw]
    threshold = (
        statistics.quantiles(works, n=4, method="inclusive")[2]
        if len(works) >= 4 else (max(works) if works else 0.0))
    for row in raw:
        categories: list[str] = []
        if row["safe_requeue_available_after_parent_lp"]:
            categories.extend(
                ["insufficient_interleaving", "child-lookahead dominated"])
        if row["no_gain_parent"]:
            categories.append("no-gain parent blocking")
        if row["depth"] >= 8:
            categories.append("interval geometry mismatch")
        if row["root_work_share"] >= 0.5:
            categories.append("expensive root processing")
        if row["nodes"] <= 1 and row["work"] >= 10.0:
            categories.append("expensive root/cut-loop processing")
        if row["nodes"] > 1 and row["root_work_share"] < 0.5:
            categories.append("expensive branch-and-bound continuation")
        if row["deadline_blocking"]:
            categories.append("deadline-blocking leaf")
        if row["work"] >= threshold:
            categories.append("top-quartile terminal Work")
        if not categories:
            categories.append("terminal exact closure")
        row["expensive_work_threshold"] = threshold
        row["expensive_leaf"] = row["work"] >= threshold
        row["classification"] = ";".join(dict.fromkeys(categories))
    return raw


def critical_history_rows(
        mapping: dict[tuple[str, str], Path],
        terminals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    terminal_index = {
        (row["instance"], row["leaf_id"]): row for row in terminals
    }
    rows: list[dict[str, Any]] = []
    for instance in CRITICAL:
        run_dir = mapping.get((instance, "C5-CANDIDATE"))
        if not run_dir:
            continue
        bounds = {
            row["parent_id"]: row
            for row in csv_rows(
                run_dir / "external/parent_child_bound_ledger.csv")
        }
        split = {
            row["parent_id"]: row
            for row in csv_rows(
                run_dir / "external/split_decision_ledger.csv")
        }
        for index, event in enumerate(trace_rows(run_dir)):
            leaf = event.get("active_leaf", "")
            parent = leaf if leaf in bounds else parent_id(leaf)
            pc = bounds.get(parent, {})
            sd = split.get(parent, {})
            terminal = terminal_index.get((instance, leaf), {})
            rows.append({
                "instance": instance,
                "run_id": run_dir.name,
                "event_index": index,
                "process_elapsed_seconds":
                    num(event.get("process_elapsed_seconds")),
                "event_type": event.get("event_type"),
                "event_source": event.get("event_source"),
                "active_leaf": leaf,
                "parent_id": parent,
                "depth": leaf_depth(leaf),
                "active_leaf_bound": num(
                    event.get("active_leaf_valid_lower_bound")),
                "next_best_relevant_leaf_bound": num(
                    event.get("other_open_leaf_min_valid_lower_bound")),
                "valid_global_lb": num(
                    event.get("valid_global_lower_bound")),
                "verified_ub": num(
                    event.get("verified_global_upper_bound")),
                "open_relevant_leaves":
                    integer(event.get("open_relevant_leaf_count")),
                "closed_relevant_leaves":
                    integer(event.get("closed_relevant_leaf_count")),
                "parent_lp_bound": num(pc.get("parent_lp_bound")),
                "left_child_bound": num(pc.get("left_lp_bound")),
                "right_child_bound": num(pc.get("right_lp_bound")),
                "child_disjunction_bound": num(pc.get("post_split_bound")),
                "normalized_child_gain":
                    num(sd.get("normalized_disjunction_gain")),
                "native_target": num(sd.get("parent_native_bound_target")),
                "target_phase_required":
                    truth(sd.get("target_phase_required")),
                "split_reason": sd.get("reason", ""),
                "terminal_mip_work": terminal.get("work", 0.0),
                "terminal_mip_runtime": terminal.get("runtime", 0.0),
                "terminal_mip_status": terminal.get("native_status", ""),
                "leaf_classification": terminal.get("classification", ""),
            })
    return rows


def model_structure_rows(
        mapping: dict[tuple[str, str], Path],
        lp_patterns: list[dict[str, Any]],
        root_patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lp_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    root_group: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in lp_patterns:
        lp_group[row["instance"]].append(row)
    for row in root_patterns:
        root_group[(row["instance"], row["arm"])].append(row)
    rows: list[dict[str, Any]] = []
    for instance in CRITICAL:
        for arm in ("P-GRB", "C5-CANDIDATE", "C0-DIAG"):
            run_dir = mapping.get((instance, arm))
            if arm == "C0-DIAG":
                matches = sorted(
                    (R30 / "runs").glob(
                        f"stage1__{instance}__c0_diag__300s"))
                run_dir = matches[0] if matches else None
            if not run_dir:
                continue
            if arm == "P-GRB":
                patterns = root_group.get((instance, arm), [])
                pattern = patterns[0] if patterns else {}
                rows.append({
                    "instance": instance,
                    "arm": arm,
                    "run_id": run_dir.name,
                    "model_rows": pattern.get("model_rows", ""),
                    "model_columns": pattern.get("model_columns", ""),
                    "model_nonzeros": pattern.get("model_nonzeros", ""),
                    "presolve_removed_rows":
                        pattern.get("presolve_removed_rows", ""),
                    "presolve_removed_columns":
                        pattern.get("presolve_removed_columns", ""),
                    "root_relaxation_objective":
                        pattern.get("root_relaxation_objective", ""),
                    "root_work": pattern.get("root_work", ""),
                    "reported_cut_count":
                        pattern.get("reported_cut_count", ""),
                    "native_tree_concentration":
                        "one_continuous_complete_original_mip",
                    "model_rebuild_pattern": "single_model_single_optimize",
                    "safe_vector_pattern_evidence": "not_exported",
                })
            elif arm == "C5-CANDIDATE":
                lps = lp_group.get(instance, [])
                roots = root_group.get((instance, arm), [])
                rows.append({
                    "instance": instance,
                    "arm": arm,
                    "run_id": run_dir.name,
                    "model_rows": max(
                        (integer(row.get("model_rows")) for row in lps),
                        default=0),
                    "model_columns": max(
                        (integer(row.get("model_columns")) for row in lps),
                        default=0),
                    "model_nonzeros": max(
                        (integer(row.get("model_nonzeros")) for row in lps),
                        default=0),
                    "presolve_removed_rows": max(
                        (integer(row.get("presolve_removed_rows"))
                         for row in lps), default=0),
                    "presolve_removed_columns": max(
                        (integer(row.get("presolve_removed_columns"))
                         for row in lps), default=0),
                    "root_relaxation_objective_min": min(
                        (num(row.get("root_relaxation_objective"))
                         for row in roots
                         if finite(num(row.get("root_relaxation_objective")))),
                        default=math.nan),
                    "root_work_total": sum(
                        num(row.get("root_work"), 0.0) for row in roots),
                    "reported_cut_count_total": sum(
                        integer(row.get("reported_cut_count"))
                        for row in roots),
                    "native_tree_concentration":
                        "many_leaf_local_native_searches",
                    "model_rebuild_pattern":
                        "canonical_leaf_models_same_leaf_lp_to_mip_object_reuse",
                    "safe_vector_pattern_evidence": "not_exported",
                })
            else:
                attempts = csv_rows(
                    run_dir / "external/enhanced_attempt_trace.csv")
                first = attempts[0] if attempts else {}
                rows.append({
                    "instance": instance,
                    "arm": arm,
                    "run_id": run_dir.name,
                    "model_rows": integer(first.get("model_rows")),
                    "model_columns": integer(first.get("model_columns")),
                    "model_nonzeros": integer(first.get("model_nonzeros")),
                    "presolve_removed_rows": "",
                    "presolve_removed_columns": "",
                    "root_relaxation_objective": "",
                    "root_work": "",
                    "reported_cut_count": "",
                    "native_tree_concentration":
                        "time_quantized_repeated_leaf_native_search",
                    "model_rebuild_pattern":
                        "fresh_or_same_leaf_restart_no_tree_claim",
                    "safe_vector_pattern_evidence": "not_exported",
                })
    return rows


def c0_parent_value_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for instance in CRITICAL:
        matches = sorted(
            (R30 / "runs").glob(
                f"stage1__{instance}__c0_diag__300s"))
        if not matches:
            continue
        run_dir = matches[0]
        attempts = csv_rows(
            run_dir / "external/enhanced_attempt_trace.csv")
        for row in attempts:
            before = num(row.get("leaf_lb_before"))
            after = num(row.get("leaf_lb_after"))
            global_before = num(row.get("global_lb_before"))
            global_after = num(row.get("global_lb_after"))
            rows.append({
                "instance": instance,
                "run_id": run_dir.name,
                "leaf_id": row.get("leaf_id"),
                "attempt": integer(row.get("attempt")),
                "first_processing": integer(row.get("attempt")) == 0,
                "selected_while_controlling":
                    truth(row.get("selected_while_controlling")),
                "leaf_bound_before": before,
                "leaf_bound_after": after,
                "leaf_bound_gain": (
                    after - before
                    if finite(before) and finite(after) else math.nan),
                "global_lb_before": global_before,
                "global_lb_after": global_after,
                "global_lb_gain": (
                    global_after - global_before
                    if finite(global_before) and finite(global_after)
                    else math.nan),
                "solver_runtime": num(row.get("solver_runtime_seconds"), 0.0),
                "work": num(row.get("work"), 0.0),
                "nodes": num(row.get("nodes"), 0.0),
                "native_status": row.get("native_status"),
                "historical_time_quantum":
                    num(row.get("allocated_time_seconds"), 0.0),
                "transferable_conclusion":
                    "valid_partial_bound_event_not_time_quantum",
            })
    return rows


def summary(
        parent_first: list[dict[str, Any]],
        child: list[dict[str, Any]],
        forced: list[dict[str, Any]],
        no_gain: list[dict[str, Any]],
        terminals: list[dict[str, Any]],
        c0_value: list[dict[str, Any]]) -> dict[str, Any]:
    critical_parent = [
        row for row in parent_first if row["critical_instance"]]
    critical_terminal = [
        row for row in terminals if row["critical_instance"]]
    return {
        "primary_parent_lp_selections": len(parent_first),
        "primary_safe_requeue_after_parent_lp": sum(
            bool(row["safe_requeue_after_parent_lp"])
            for row in parent_first),
        "primary_next_leaf_targets_available_after_parent_lp": sum(
            bool(row["parameter_free_next_leaf_target_available"])
            for row in parent_first),
        "primary_parent_lp_selections_with_parameter_free_transition": sum(
            bool(row["safe_requeue_after_parent_lp"])
            or bool(row["parameter_free_next_leaf_target_available"])
            for row in parent_first),
        "primary_child_lp_calls_deferable": sum(
            integer(row["child_lp_calls_paid_at_this_selection"])
            for row in parent_first
            if row["child_lookahead_deferable_under_parent_first"]),
        "primary_child_lp_work_deferable": sum(
            num(row["child_lp_work_paid"], 0.0)
            for row in parent_first
            if row["child_lookahead_deferable_under_parent_first"]),
        "critical_parent_lp_selections": len(critical_parent),
        "critical_safe_requeue_after_parent_lp": sum(
            bool(row["safe_requeue_after_parent_lp"])
            for row in critical_parent),
        "child_lookahead_rows": len(child),
        "child_lookahead_work": sum(
            num(row["child_lp_work"], 0.0) for row in child),
        "zero_or_tolerance_child_gain_rows": sum(
            num(row["raw_child_disjunction_gain"], 0.0) <= TOL
            for row in child),
        "forced_delayed_split_rows": len(forced),
        "forced_delayed_splits_without_current_gain": sum(
            bool(row["forced_split_avoidable_under_current_value_rule"])
            for row in forced),
        "no_gain_parent_rows": len(no_gain),
        "no_gain_deadline_blocking_rows": sum(
            bool(row["deadline_blocking"]) for row in no_gain),
        "no_gain_terminal_work": sum(
            num(row["terminal_work"], 0.0) for row in no_gain),
        "terminal_mip_rows": len(terminals),
        "terminal_mip_work": sum(
            num(row["work"], 0.0) for row in terminals),
        "critical_terminal_mip_rows": len(critical_terminal),
        "critical_terminal_mip_work": sum(
            num(row["work"], 0.0) for row in critical_terminal),
        "critical_deadline_blocking_terminal_rows": sum(
            bool(row["deadline_blocking"]) for row in critical_terminal),
        "c0_attempt_rows": len(c0_value),
        "c0_first_attempt_leaf_gain": sum(
            num(row["leaf_bound_gain"], 0.0)
            for row in c0_value
            if row["first_processing"]
            and abs(num(row["leaf_bound_after"], math.inf)) < 1e50),
        "c0_first_attempt_global_gain": sum(
            num(row["global_lb_gain"], 0.0)
            for row in c0_value if row["first_processing"]),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    mapping, _ = run_maps()
    p_comparison, c0_comparison = comparison_maps()
    parent_first = parent_native_first_rows(mapping)
    child = child_lookahead_rows(mapping, parent_first)
    forced = forced_split_rows(mapping)
    no_gain = no_gain_rows(mapping, parent_first)
    lp_patterns = lp_pattern_rows(mapping)
    root_patterns = root_pattern_rows(mapping)
    terminals = terminal_leaf_rows(
        mapping, parent_first, no_gain, root_patterns)
    histories = critical_history_rows(mapping, terminals)
    structures = model_structure_rows(
        mapping, lp_patterns, root_patterns)
    c0_value = c0_parent_value_rows()

    write_csv(OUT / "critical_leaf_histories.csv", histories)
    write_csv(OUT / "expensive_terminal_leaf_audit.csv", terminals)
    write_csv(OUT / "child_lookahead_value.csv", child)
    write_csv(OUT / "parent_native_first_value.csv", parent_first)
    write_csv(OUT / "forced_split_regression_audit.csv", forced)
    write_csv(OUT / "no_gain_parent_blocking_audit.csv", no_gain)
    write_csv(OUT / "lp_pattern_summary.csv", lp_patterns)
    write_csv(OUT / "root_pattern_summary.csv", root_patterns)
    write_csv(OUT / "model_structure_comparison.csv", structures)
    write_csv(OUT / "c0_parent_native_value.csv", c0_value)

    report = summary(
        parent_first, child, forced, no_gain, terminals, c0_value)
    report.update({
        "critical_instances": CRITICAL,
        "p_grb_comparison_rows_available": sum(
            instance in p_comparison for instance in CRITICAL),
        "c0_comparison_rows_available": sum(
            instance in c0_comparison for instance in CRITICAL),
        "historical_inputs_modified": False,
    })
    (OUT / "phase_a_summary.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
