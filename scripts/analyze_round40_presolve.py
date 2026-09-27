#!/usr/bin/env python3
"""Audit Round 40 presolve fairness rows and freeze the later-round policy."""

from __future__ import annotations

import math
from typing import Any

import round40_common as common


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() == "true"


def main() -> int:
    manifest = common.csv_rows(common.PRESOLVE_MANIFEST)
    rows: list[dict[str, Any]] = []
    for frozen in manifest:
        run_dir = common.RUNS / frozen["run_id"]
        command = common.load_json(run_dir / "command.json")
        result = common.load_json(run_dir / "result.json")
        lower, upper = common.result_bounds(frozen["arm"], result)
        c6 = frozen["arm"].startswith("C6-")
        strict = truth(result.get(
            "external_gini_tree_strict_certified" if c6 else
            "strict_certified_original_problem"))
        row = {
            **frozen,
            "return_code": command["return_code"],
            "watchdog_timeout": command["watchdog_timeout"],
            "process_seconds": result.get(
                "final_process_wall_time_seconds",
                result.get("runtime_seconds")),
            "solver_work": result.get(
                "external_gini_tree_work" if c6 else "gurobi_work", 0.0),
            "solver_nodes": result.get(
                "external_gini_tree_nodes" if c6 else
                "gurobi_node_count", 0.0),
            "lp_work": result.get("external_gini_tree_lp_work", 0.0),
            "partial_mip_work": result.get(
                "external_gini_tree_partial_mip_work", 0.0),
            "terminal_mip_work": result.get(
                "external_gini_tree_terminal_mip_work", 0.0),
            "optimize_count": result.get(
                "external_gini_tree_optimize_count" if c6 else
                "gurobi_optimize_count", 0),
            "presolve_execution_count": result.get(
                "external_gini_tree_presolve_execution_count", 1),
            "gurobi_presolve_requested": result.get(
                "gurobi_presolve_requested"),
            "gurobi_presolve_effective": result.get(
                "gurobi_presolve_effective"),
            "gurobi_threads_effective": result.get(
                "gurobi_threads_effective"),
            "gurobi_seed_effective": result.get("gurobi_seed_effective"),
            "mip_gap_effective": result.get("gurobi_mip_gap_effective"),
            "mip_gap_abs_effective": result.get(
                "gurobi_mip_gap_abs_effective"),
            "backend_parameter_roundtrip_valid": (
                truth(result.get(
                    "external_gini_tree_backend_parameter_roundtrip_valid"))
                if c6 else True),
            "strict_certificate": strict,
            "original_problem_verifier_passed": truth(
                result.get("verification", {}).get(
                    "original_solution_feasible")),
            "valid_lower_bound": lower,
            "verified_upper_bound": upper,
            "objective": result.get("objective"),
            "status": result.get("status"),
        }
        expected = int(frozen["gurobi_presolve_value"])
        row["parameter_contract_passed"] = (
            int(row["gurobi_presolve_requested"]) == expected and
            int(row["gurobi_presolve_effective"]) == expected and
            int(row["gurobi_threads_effective"]) == 1 and
            int(row["gurobi_seed_effective"]) == 0 and
            float(row["mip_gap_effective"]) == 0.0 and
            float(row["mip_gap_abs_effective"]) == 0.0 and
            truth(row["backend_parameter_roundtrip_valid"]))
        row["exactness_passed"] = (
            row["parameter_contract_passed"] and strict and
            row["original_problem_verifier_passed"] and
            math.isfinite(lower) and math.isfinite(upper) and
            lower <= upper + 1e-7)
        rows.append(row)
    common.write_csv(common.OUT / "presolve_fairness_results.csv", rows)

    comparisons: list[dict[str, Any]] = []
    grouped = {(row["instance_id"], row["arm"],
                row["presolve_policy"]): row for row in rows}
    for instance_id in sorted({row["instance_id"] for row in rows}):
        for arm in ("P-GRB", "C6-HGA-FULL-K4"):
            off = grouped[(instance_id, arm, "off")]
            auto = grouped[(instance_id, arm, "auto")]
            off_seconds = float(off["process_seconds"])
            auto_seconds = float(auto["process_seconds"])
            comparisons.append({
                "instance_id": instance_id,
                "arm": arm,
                "off_seconds": off_seconds,
                "auto_seconds": auto_seconds,
                "auto_over_off_time_ratio": auto_seconds / off_seconds,
                "off_work": off["solver_work"],
                "auto_work": auto["solver_work"],
                "off_nodes": off["solver_nodes"],
                "auto_nodes": auto["solver_nodes"],
                "same_objective": math.isclose(
                    float(off["objective"]), float(auto["objective"]),
                    rel_tol=0.0, abs_tol=1e-7),
                "both_exact": (truth(off["exactness_passed"]) and
                               truth(auto["exactness_passed"])),
            })
    common.write_csv(common.OUT / "presolve_off_vs_auto.csv", comparisons)

    all_exact = all(truth(row["exactness_passed"]) for row in rows)
    same_objectives = all(truth(row["same_objective"])
                          for row in comparisons)
    if not all_exact or not same_objectives:
        raise RuntimeError("presolve fairness exactness gate failed")
    decision = {
        "schema": "round40-frozen-presolve-decision-v1",
        "round_id": 40,
        "frozen_policy": "gurobi-auto",
        "gurobi_presolve_value": -1,
        "applies_uniformly_to": [
            "P-GRB target MIP",
            "C6 interval LP relaxations",
            "C6 native-bound target MIPs",
            "C6 terminal interval MIPs",
        ],
        "instance_dispatch": False,
        "reason": (
            "Both arms already used Gurobi Presolve=Auto in Round 39; "
            "the similarly named global-gini-tree presolve-off flag does "
            "not configure the Gurobi fixed-interval backend. Controlled "
            "Off/Off and Auto/Auto rows passed common parameter and "
            "exactness gates. Auto preserves equal solver-level opportunity "
            "and the validated C6 contract."),
        "round39_contract_was_solver_level_fair": True,
        "round39_labeling_was_ambiguous": True,
        "all_rows_exact": all_exact,
        "same_objectives_off_vs_auto": same_objectives,
        "row_count": len(rows),
    }
    common.write_json(common.OUT / "frozen_presolve_decision.json", decision)
    common.write_text(common.OUT / "presolve_fairness_protocol.md", f"""\
# Round 40 presolve fairness protocol

The frozen comparison uses Gurobi 13.0.2, one thread, Seed 0, relative and
absolute MIP gaps 0, the same generated compact formulation, the repository's
process-wall timing convention, and the same machine. The predeclared witnesses
are one short Round-39 P-GRB regression and one C6-positive control.

The four paired arms per witness are P-GRB/C6 with Gurobi `Presolve=0` and
P-GRB/C6 with Gurobi `Presolve=-1` (Auto). `--global-gini-tree-presolve off`
is retained as a frozen legacy safety option but does not control the Gurobi
fixed-interval backend used by C6.

All {len(rows)} rows passed parameter readback, one-thread, seed-zero,
zero-gap, original-problem verification, finite-bound, and strict-certificate
gates. The uniform policy frozen for Parts 1--3 is **Gurobi Auto (-1)** for
plain Gurobi and every C6 Gurobi optimize phase. No instance dispatch is used.
""")
    print(common.load_json(common.OUT / "frozen_presolve_decision.json"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
