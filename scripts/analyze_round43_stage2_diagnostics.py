#!/usr/bin/env python3
"""Complete the Stage 2 root-capture and model-size diagnostics."""

from __future__ import annotations

import math
import re
from typing import Any

import round43_common as common


MODES = ("none", "constant", "single", "iterated")
EPS = 1e-7


def number(value: str | None, default: float = math.nan) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def first_native_root(run_dir) -> float:
    rows = common.csv_rows(run_dir / "external" / "global_bound_trace.csv")
    native = [number(row["active_leaf_valid_lower_bound"])
              for row in rows
              if row["event_type"] == "native_root_processing_bound"]
    return native[0] if native else math.nan


def model_size(run_dir) -> dict[str, int]:
    logs = sorted((run_dir / "external" / "native_logs").glob(
        "*_terminal_mip.gurobi.log"))
    if not logs:
        return {key: 0 for key in (
            "model_rows", "model_columns", "model_nonzeros",
            "general_constraints", "presolved_rows", "presolved_columns",
            "presolved_nonzeros")}
    text = logs[0].read_text(encoding="utf-8", errors="replace")
    model = re.search(
        r"Optimize a model with (\d+) rows, (\d+) columns and (\d+) nonzeros",
        text)
    general = re.search(r"Model has (\d+) general constraints", text)
    presolved = re.search(
        r"Presolved: (\d+) rows, (\d+) columns, (\d+) nonzeros", text)
    return {
        "model_rows": int(model.group(1)) if model else 0,
        "model_columns": int(model.group(2)) if model else 0,
        "model_nonzeros": int(model.group(3)) if model else 0,
        "general_constraints": int(general.group(1)) if general else 0,
        "presolved_rows": int(presolved.group(1)) if presolved else 0,
        "presolved_columns": int(presolved.group(2)) if presolved else 0,
        "presolved_nonzeros": int(presolved.group(3)) if presolved else 0,
    }


def run_dir(instance_id: str, mode: str):
    return common.RUNS / (
        f"stage2-envelope__{instance_id}__algorithm__K1__d2__"
        f"rho0.01__no-adaptive__{mode}")


def k4_root(instance_id: str) -> float:
    run = common.RUNS / (
        f"stage3-candidate__{instance_id}__algorithm__K4__d2__"
        "rho0.1__d__single")
    path = run / "external" / "round43_structural_atlas.csv"
    rows = [row for row in common.csv_rows(path)
            if int(row["parent_depth"]) == 0]
    return min(number(row["parent_lp_bound"]) for row in rows)


def main() -> int:
    rows: list[dict[str, Any]] = []
    for instance_id, role in common.MECHANISM_ROLES.items():
        e0_dir = run_dir(instance_id, "none")
        e0_native = first_native_root(e0_dir)
        e0_atlas = common.csv_rows(
            e0_dir / "external" / "round43_structural_atlas.csv")
        k1_lp = number(e0_atlas[0]["parent_lp_bound"]) if e0_atlas else math.nan
        fixed_k4 = k4_root(instance_id)
        transfer_gap = fixed_k4 - k1_lp
        e0_result = common.load_json(e0_dir / "result.json")
        e0_work = number(e0_result.get("external_gini_tree_work"))
        for mode in MODES:
            directory = run_dir(instance_id, mode)
            result = common.load_json(directory / "result.json")
            root = first_native_root(directory)
            improvement = root - e0_native
            facets = common.csv_rows(
                directory / "external" / "round43_facet_ledger.csv")
            accepted = sum(row["accepted"].lower() in {"1", "true"}
                           for row in facets)
            work = number(result.get("external_gini_tree_work"))
            rows.append({
                "instance_id": instance_id,
                "mechanism_role": role,
                "mode": mode,
                "K1_parent_lp_bound": k1_lp,
                "mode_first_native_root_bound": root,
                "E0_first_native_root_bound": e0_native,
                "root_bound_improvement_over_E0": improvement,
                "fixed_K4_global_initial_lp_bound": fixed_k4,
                "fixed_K4_minus_K1_transfer_gap": transfer_gap,
                "chi_denominator_material": transfer_gap > EPS,
                "chi": improvement / max(transfer_gap, EPS),
                **model_size(directory),
                "accepted_facet_rows": accepted,
                "work": work,
                "work_ratio_vs_E0": work / max(e0_work, 1e-12),
                "solver_seconds": number(result.get(
                    "external_gini_tree_solver_seconds")),
                "process_seconds": number(result.get(
                    "final_process_wall_time_seconds")),
                "strict_certificate": bool(result.get(
                    "strict_certified_original_problem")),
                "major_fragmentation_advantage_preserved": (
                    role != "major_fragmentation_regression" or
                    work <= e0_work),
                "strong_control_work_reduced_vs_E0": (
                    role == "strongest_k4_positive_control" and
                    work < e0_work),
                "run_dir": common.relative(directory),
            })
    common.write_csv(common.OUT / "stage2_envelope_diagnostics.csv", rows)
    control_single = next(row for row in rows
                          if row["mechanism_role"] ==
                          "strongest_k4_positive_control" and
                          row["mode"] == "single")
    common.write_json(common.OUT / "stage2_envelope_capture.json", {
        "schema": "round43-stage2-envelope-capture-v1",
        "round_id": 43,
        "row_count": len(rows),
        "selected_mode": "single",
        "strong_control_chi": control_single["chi"],
        "strong_control_transfer_gap": control_single[
            "fixed_K4_minus_K1_transfer_gap"],
        "strong_control_chi_denominator_material": control_single[
            "chi_denominator_material"],
        "interpretation": (
            "The fixed-K4 and K1 complete global root LP bounds coincide on "
            "the strongest control, so chi has a vacuous epsilon denominator; "
            "it does not identify missing transferable root strength."),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
