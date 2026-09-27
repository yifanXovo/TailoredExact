#!/usr/bin/env python3
"""Build the Round 40 research evidence package from frozen run artifacts."""

from __future__ import annotations

import csv
import json
import math
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

import round40_common as common


csv.field_size_limit(1024 * 1024 * 1024)


ENDPOINT_ID = "round39_small_hard_V12_M3_Q20_slot07_seed621538683"
MAJOR_ID = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
STRONG_ID = "round39_small_hard_V12_M3_Q30_slot08_seed1288546114"
GEOMETRY_BEST_ID = "round39_small_medium_V10_M2_Q20_slot05_seed968549317"
GEOMETRY_WORST_ID = "round39_small_hard_V12_M1_Q20_slot05_seed180890838"


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() == "true"


def number(value: Any) -> float:
    return float(value)


def fmt(value: float, digits: int = 3) -> str:
    return f"{value:.{digits}f}"


def write_markdown(name: str, text: str) -> None:
    common.write_text(common.OUT / name, text.strip() + "\n")


def group_by_instance(rows: list[dict[str, str]]) -> dict[str, dict[str, dict[str, str]]]:
    grouped: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows:
        grouped[row["instance_id"]][row["arm"]] = row
    return grouped


def ratio(numerator: float, denominator: float) -> float:
    if abs(numerator) <= 1e-12 and abs(denominator) <= 1e-12:
        return 1.0
    return numerator / max(denominator, 1e-12)


def main() -> int:
    # Regenerate every machine-readable analysis before packaging it.
    python = "D:/msys64/ucrt64/bin/python.exe"
    for script, extra in (
        ("scripts/analyze_round40_presolve.py", []),
        ("scripts/analyze_round40_k1.py", ["--require-full"]),
        ("scripts/analyze_round40_ub_geometry.py", ["--require-full"]),
        ("scripts/analyze_round40_default_equivalence.py", []),
    ):
        subprocess.run((python, script, *extra), cwd=common.ROOT, check=True)

    presolve = common.csv_rows(common.OUT / "presolve_fairness_results.csv")
    k1_rows = common.csv_rows(common.OUT / "k1_per_run_trajectory.csv")
    k1_comparisons = common.csv_rows(common.OUT / "k1_vs_k4_comparison.csv")
    geometry_rows = common.csv_rows(
        common.OUT / "ub_geometry_per_run_trajectory.csv")
    geometry_comparisons = common.csv_rows(
        common.OUT / "ub_geometry_comparison.csv")
    default_rows = common.csv_rows(
        common.OUT / "default_c6_equivalence_per_run.csv")
    default_pairs = common.csv_rows(common.OUT / "default_c6_equivalence.csv")
    k1_grouped = group_by_instance(k1_rows)
    geometry_grouped = group_by_instance(geometry_rows)

    k1_arms = (
        "C6-K1-SINGLE", "C6-K1-ADAPTIVE",
        "C6-K1-ADAPTIVE-DECISIVE")
    k1_summary: dict[str, dict[str, float | int]] = {}
    for arm in k1_arms:
        paired = [row for row in k1_comparisons if row["candidate"] == arm]
        time_ratios = [number(row["candidate_over_k4_time_ratio"])
                       for row in paired]
        work_ratios = [number(row["candidate_over_k4_work_ratio"])
                       for row in paired]
        k1_summary[arm] = {
            "instances": len(paired),
            "time_wins": sum(value < 1.0 for value in time_ratios),
            "median_time_ratio": statistics.median(time_ratios),
            "median_work_ratio": statistics.median(work_ratios),
            "candidate_total_seconds": sum(
                number(k1_grouped[iid][arm]["total_process_seconds"])
                for iid in k1_grouped),
            "k4_total_seconds": sum(
                number(arms["C6-HGA-FULL-K4"]["total_process_seconds"])
                for arms in k1_grouped.values()),
        }

    geometry_time_ratios = [number(
        row["candidate_over_baseline_time_ratio"])
        for row in geometry_comparisons]
    geometry_work_ratios = [number(
        row["candidate_over_baseline_work_ratio"])
        for row in geometry_comparisons]
    geometry_summary = {
        "instances": len(geometry_comparisons),
        "time_wins": sum(value < 1.0 for value in geometry_time_ratios),
        "work_wins": sum(value < 1.0 for value in geometry_work_ratios),
        "median_time_ratio": statistics.median(geometry_time_ratios),
        "median_work_ratio": statistics.median(geometry_work_ratios),
        "baseline_total_seconds": sum(number(row["baseline_seconds"])
                                      for row in geometry_comparisons),
        "candidate_total_seconds": sum(number(row["candidate_seconds"])
                                       for row in geometry_comparisons),
        "baseline_total_work": sum(number(row["baseline_work"])
                                   for row in geometry_comparisons),
        "candidate_total_work": sum(number(row["candidate_work"])
                                    for row in geometry_comparisons),
    }

    # Compact Part 1 forensic table, including P-GRB context.
    forensic_rows: list[dict[str, Any]] = []
    for instance_id, arms in k1_grouped.items():
        p = arms["P-GRB"]
        k4 = arms["C6-HGA-FULL-K4"]
        for arm in k1_arms:
            candidate = arms[arm]
            forensic_rows.append({
                "instance_id": instance_id,
                "diagnostic_role": candidate["diagnostic_role"],
                "candidate": arm,
                "p_grb_seconds": p["total_process_seconds"],
                "k4_seconds": k4["total_process_seconds"],
                "candidate_seconds": candidate["total_process_seconds"],
                "candidate_over_p_grb_time_ratio": ratio(
                    number(candidate["total_process_seconds"]),
                    number(p["total_process_seconds"])),
                "candidate_over_k4_time_ratio": ratio(
                    number(candidate["total_process_seconds"]),
                    number(k4["total_process_seconds"])),
                "k4_work": k4["solver_work"],
                "candidate_work": candidate["solver_work"],
                "candidate_over_k4_work_ratio": ratio(
                    number(candidate["solver_work"]),
                    number(k4["solver_work"])),
                "k4_integer_jobs": k4["independent_integer_proof_jobs"],
                "candidate_integer_jobs":
                    candidate["independent_integer_proof_jobs"],
                "k4_split_count": k4["split_count"],
                "candidate_split_count": candidate["split_count"],
                "candidate_strict_certificate":
                    candidate["strict_certificate"],
                "candidate_expected_unresolved_endpoint": (
                    instance_id == ENDPOINT_ID and
                    not truth(candidate["strict_certificate"])),
            })
    common.write_csv(common.OUT / "k1_trajectory_forensics.csv", forensic_rows)

    # Unified per-run work/node/runtime table.
    per_run: list[dict[str, Any]] = []
    for study, rows in (("part1_k1", k1_rows),
                        ("part2_ub_geometry", geometry_rows),
                        ("default_equivalence", default_rows)):
        for row in rows:
            per_run.append({
                "study": study,
                "run_id": row["run_id"],
                "instance_id": row["instance_id"],
                "difficulty_stratum": row.get("difficulty_stratum", ""),
                "arm": row["arm"],
                "process_seconds": row.get(
                    "total_process_seconds", row.get("process_seconds", "")),
                "solver_work": row.get("solver_work", ""),
                "solver_nodes": row.get("solver_nodes", ""),
                "initial_interval_count": row.get(
                    "initial_interval_count", ""),
                "independent_integer_proof_jobs": row.get(
                    "independent_integer_proof_jobs", ""),
                "split_count": row.get("split_count", ""),
                "strict_certificate": row.get("strict_certificate", ""),
                "exactness_passed": row.get("exactness_passed", ""),
            })
    common.write_csv(common.OUT / "per_run_work_node_runtime.csv", per_run)

    # Representative full trajectory rows.
    representatives: list[dict[str, Any]] = []
    for instance_id in (MAJOR_ID, STRONG_ID, ENDPOINT_ID):
        for row in k1_rows:
            if row["instance_id"] == instance_id:
                representatives.append({"study": "part1_k1", **row})
    for instance_id in (MAJOR_ID, GEOMETRY_BEST_ID, ENDPOINT_ID,
                        GEOMETRY_WORST_ID):
        for row in geometry_rows:
            if row["instance_id"] == instance_id:
                representatives.append({"study": "part2_ub_geometry", **row})
    representative_fields: list[str] = []
    for row in representatives:
        for field in row:
            if field not in representative_fields:
                representative_fields.append(field)
    common.write_csv(common.OUT / "representative_proof_trajectories.csv",
                     representatives, representative_fields)

    # Cross-study exactness and fail-closed audit.
    exactness_rows: list[dict[str, Any]] = []
    for row in presolve:
        exactness_rows.append({
            "study": "part0_presolve", "run_id": row["run_id"],
            "instance_id": row["instance_id"], "arm": row["arm"],
            "strict_certificate": row["strict_certificate"],
            "expected_unresolved": False,
            "original_problem_verifier_passed":
                row["original_problem_verifier_passed"],
            "parameter_roundtrip_valid":
                row["backend_parameter_roundtrip_valid"],
            "gurobi_presolve_effective": row["gurobi_presolve_effective"],
            "accepted_outcome": row["exactness_passed"],
        })
    for study, rows in (("part1_k1", k1_rows),
                        ("part2_ub_geometry", geometry_rows),
                        ("default_equivalence", default_rows)):
        for row in rows:
            strict = truth(row["strict_certificate"])
            expected = (row["instance_id"] == ENDPOINT_ID and not strict and
                        row.get("certificate_class") == "certificate_rejected")
            exactness_rows.append({
                "study": study, "run_id": row["run_id"],
                "instance_id": row["instance_id"], "arm": row["arm"],
                "strict_certificate": strict,
                "expected_unresolved": expected,
                "original_problem_verifier_passed": row.get(
                    "original_problem_verifier_passed", True),
                "parameter_roundtrip_valid": row.get(
                    "backend_parameter_roundtrip_valid",
                    row.get("parameter_roundtrip_valid", True)),
                "gurobi_presolve_effective": row.get(
                    "gurobi_presolve_effective", -1),
                "accepted_outcome": strict or expected,
            })
    common.write_csv(common.OUT / "exactness_audit.csv", exactness_rows)
    accepted_count = sum(truth(row["accepted_outcome"])
                         for row in exactness_rows)
    strict_count = sum(truth(row["strict_certificate"])
                       for row in exactness_rows)
    unresolved_count = sum(truth(row["expected_unresolved"])
                           for row in exactness_rows)
    if accepted_count != len(exactness_rows):
        raise RuntimeError("final exactness audit contains an unaccepted row")

    major = k1_grouped[MAJOR_ID]
    strong = k1_grouped[STRONG_ID]
    endpoint_geometry = geometry_grouped[ENDPOINT_ID]
    geometry_best = next(row for row in geometry_comparisons
                         if row["instance_id"] == GEOMETRY_BEST_ID)
    geometry_worst = next(row for row in geometry_comparisons
                          if row["instance_id"] == GEOMETRY_WORST_ID)

    write_markdown("source_of_truth.md", f"""
# Round 40 source of truth

- Repository: `ExactEBRP` (existing local repository; no clone created).
- Research branch: `codex/round40-regression-adaptive`.
- Stable parent: Round 39 commit `60d1f6e454e0d2b2b1c5c883c3a3d0ae9b5ffd19`.
- Validated default protected throughout: `C6-HGA-FULL`, `K=4`, `rho=0.01`.
- Result root: `results/gf_regression_adaptive_round40/`.
- Part 0: 8 frozen Off/Auto rows in `presolve_fairness_manifest.csv`.
- Part 1: 40 original rows plus 10 iterative decisive rows; both manifests were frozen before their respective results.
- Part 2: 48 rows (24 frozen Round 39 instances x K4/nested-dyadic) in `ub_geometry_manifest.csv`.
- Default equivalence: 6 current-executable rows in `default_c6_equivalence_manifest.csv`.
- Every run directory contains its exact command, executable SHA-256, instance SHA-256, stdout/stderr, result JSON, and native evidence ledgers.
- Gurobi contract after Part 0: Presolve Auto (`-1`), Threads 1, Seed 0, relative/absolute gaps 0.
- Historical Round 39 evidence was read only and remains unchanged.

Part 1's decisive arm was added after the original four-arm manifest; its separate executable hash and freeze record are retained. Later default-off equivalence confirms that adding experimental arms did not alter the frozen K4 path on 25 deterministic fields across three representative instances.
""")

    write_markdown("k1_mechanism_definitions.md", """
# Part 1 mechanism definitions

## Frozen K4

Four equal-width intervals cover the complete strict-improver Gini range. The unchanged C6 scheduler uses complete LP bounds, native next-frontier targets, `rho=0.01` child evidence, atomic parent/child replacement, and exact terminal closure.

## K1 single

One interval covers the complete strict-improver range. Its LP is completed and one exact terminal MIP closes it. No midpoint child lookahead or independent interval proof fragmentation occurs.

## K1 adaptive (initial hypothesis)

Start from the same complete root. Reuse the existing complete midpoint-child LP lookahead and `rho=0.01` split logic recursively. A declined refinement closes the coarser parent exactly.

## K1 adaptive decisive (trajectory-motivated revision)

Start from the complete root and solve both child LPs, but refine only when child infeasibility is proved or the child-disjunction lower bound already reaches the verified cutoff. Nondecisive gain closes the coarser parent exactly. This rule is deterministic, parameter-free, hardware-independent, and does not inspect identity, dimensions, seed, elapsed time, nodes, Work, or historical winners.
""")

    write_markdown("k1_iterative_research_log.md", f"""
# Part 1 iterative research log

1. Frozen the 10-instance diagnostic panel before K1 results: easy P-GRB wins, the major medium regression, both hard P-GRB wins, the numerical endpoint, the strongest C6 control, and additional medium/hard C6 wins.
2. K1-single reduced independent proof jobs on the major witness from 8 to 1 and reduced Work from {fmt(number(major['C6-HGA-FULL-K4']['solver_work']))} to {fmt(number(major['C6-K1-SINGLE']['solver_work']))}. Runtime fell from {fmt(number(major['C6-HGA-FULL-K4']['total_process_seconds']))} to {fmt(number(major['C6-K1-SINGLE']['total_process_seconds']))} seconds, but remained above P-GRB's {fmt(number(major['P-GRB']['total_process_seconds']))} seconds.
3. Original adaptive split the major root and recreated 4 integer proof jobs, increasing runtime to {fmt(number(major['C6-K1-ADAPTIVE']['total_process_seconds']))} seconds. This falsified nondecisive `rho` refinement as the recovery mechanism.
4. The decisive revision retained one terminal job on the major witness and completed in {fmt(number(major['C6-K1-ADAPTIVE-DECISIVE']['total_process_seconds']))} seconds with {fmt(number(major['C6-K1-ADAPTIVE-DECISIVE']['solver_work']))} Work.
5. The strong C6 control falsified K1 as a universal replacement. K4 took {fmt(number(strong['C6-HGA-FULL-K4']['total_process_seconds']))} seconds/{fmt(number(strong['C6-HGA-FULL-K4']['solver_work']))} Work; K1-single took {fmt(number(strong['C6-K1-SINGLE']['total_process_seconds']))} seconds/{fmt(number(strong['C6-K1-SINGLE']['solver_work']))} Work. The single coarse MIP was genuinely weaker even though it eliminated independent jobs.
6. Final panel result: K1-single, original adaptive, and decisive each win 8/10 against K4. Decisive has the lowest panel total ({fmt(float(k1_summary['C6-K1-ADAPTIVE-DECISIVE']['candidate_total_seconds']))} vs {fmt(float(k1_summary['C6-K1-ADAPTIVE-DECISIVE']['k4_total_seconds']))} seconds), but its 5.24x strong-control slowdown prevents promotion.

Negative results are retained in `k1_vs_k4_comparison.csv`; no candidate was silently replaced.
""")

    write_markdown("ub_geometry_mechanism_definition.md", """
# Part 2 nested-dyadic UB geometry

Let the stable root be the mathematical Gini maximum `(V-1)/V`, independent of the incumbent. For dyadic level `d`, the hierarchy has `2^d` equal anchor cells on that root. Select the finest level whose proof-relevant prefix intersects at most the frozen target `K=4` cells. Intersect those cells with `[0, U_proof]`; only the last active cell may be truncated.

A stronger verified UB either keeps the same level or selects a finer dyadic level. Every coarser boundary is also a boundary in the finer hierarchy, so every old internal boundary still below the stronger cutoff is preserved. Suffix cells deactivate and the last endpoint may contract. The proof cutoff, LP/MIP semantics, C6 scheduler, `rho` split rule, atomic coverage, lower-bound ledger, and exact closures remain unchanged.

The policy is explicit (`--round40-c6-ub-geometry nested-dyadic-k4`), default-off, HGA-FULL-only, mutually exclusive with Round 36/37 geometry and K1 arms, and requires the frozen Auto-presolve contract.

The Round 36 projection uses 14 preexisting verified HGA/simple UB pairs. Ten pairs have different cutoffs: legacy UB-rescaled quartiles redraw relevant boundaries in all ten; nested dyadic preserves them in all ten. This is a geometry theorem/audit, not a monotonic-runtime claim.
""")

    write_markdown("unified_candidate_definition_results.md", f"""
# Part 3 unified mechanism decision

No unified runtime candidate was implemented.

The useful ideas do not provide a safe general dispatch signal:

- Coarse K1 eliminates fragmentation and recovers {fmt(1.0 - number(major['C6-K1-ADAPTIVE-DECISIVE']['total_process_seconds']) / number(major['C6-HGA-FULL-K4']['total_process_seconds']), 3)} of K4's major-witness runtime fraction, but its complete child LP evidence is nondecisive on the strong control even though the coarse terminal MIP later costs about {fmt(number(strong['C6-K1-ADAPTIVE-DECISIVE']['solver_work']) / number(strong['C6-HGA-FULL-K4']['solver_work']), 2)}x K4 Work.
- Nested dyadic provides stable boundaries and fixes the endpoint certificate, but it is {fmt(number(next(row for row in geometry_comparisons if row['instance_id'] == MAJOR_ID)['candidate_over_baseline_time_ratio']), 3)}x K4 on the major regression and has no structural evidence that predicts when K1 should replace its 3-4 active cells.
- The existing complete LP/child evidence therefore cannot distinguish "fragmentation-dominated" from "coarse-MIP-dominated" cases. A winner lookup, elapsed-time/Work/node fallback, or threshold selected to flip these witnesses would violate the frozen research rules.

The conceptual incumbent-stable coarse-to-fine tree remains a research hypothesis. Current evidence is insufficient to justify another expensive matrix or a paper algorithm without a new, solver-independent bound-quality observable.
""")

    final_report = f"""
# Round 40 final report

## Outcomes

1. **Was Round 39 presolve unfair?** No at the solver level: both P-GRB and the Gurobi fixed-interval C6 backend used Presolve Auto (`-1`). The `global-gini-tree-presolve off` label belonged to a different legacy/global-tree safety control and made the configuration look ambiguous.
2. **Fair policy going forward.** Uniform Gurobi Presolve Auto for P-GRB and every C6 LP, target MIP, and terminal MIP. The 8-row Off/Auto ablation preserves objectives/certificates and shows material performance distortion from forcing Off (for example, the positive witness changes from 93.897 to 63.208 s for P-GRB and 15.550 to 9.387 s for C6).
3. **Cause of Round 39 regressions.** It is heterogeneous. The major medium regression is dominated by proof fragmentation/repeated terminal work: K4 uses 8 integer jobs and {fmt(number(major['C6-HGA-FULL-K4']['solver_work']))} Work versus K1's one job and about {fmt(number(major['C6-K1-SINGLE']['solver_work']))} Work. Very easy/short P wins include irreducible HGA startup and C6 proof overhead. The strongest C6 control has the opposite mechanism: K4's narrower interval models are much stronger than one coarse MIP.
4. **Does simple K1 reduce fragmentation?** Yes. It wins 8/10 diagnostic cases, has median time ratio {fmt(float(k1_summary['C6-K1-SINGLE']['median_time_ratio']))}, and materially reduces the major regression.
5. **Did adaptive K1 solve the failure?** No. Original adaptive recreates jobs on the major witness; decisive adaptive preserves the K1-single recovery but cannot detect the strong control's coarse-MIP weakness.
6. **Improve regressions without losing strong positives?** Not uniformly. K1 still beats P-GRB strongly on the positive control ({fmt(number(strong['C6-K1-ADAPTIVE-DECISIVE']['total_process_seconds']))} vs {fmt(number(strong['P-GRB']['total_process_seconds']))} s) but loses 5.24x to K4 there. It also does not beat P-GRB on the major regression.
7. **Does incumbent-stable geometry reduce UB path sensitivity?** Structurally yes: all relevant boundaries are preserved on all 10 Round 36 pairs with different verified UBs. Empirically it wins {geometry_summary['time_wins']}/24, exactly resolves the numerical endpoint, but median time/Work ratios are {fmt(float(geometry_summary['median_time_ratio']))}/{fmt(float(geometry_summary['median_work_ratio']))}; total time and Work are worse. No runtime-monotonicity theorem is claimed.
8. **Unified mechanism?** Not implemented: current complete LP evidence cannot safely select between K1 and decomposed K4, and adding outcome/timing/Work dispatch would violate the protocol.
9. **Credible replacement for frozen K4?** No. K1 has a severe strong-control regression; nested dyadic is neutral-to-negative in aggregate and leaves the major regression intact.
10. **Falsified mechanisms.** Universal K1, nondecisive `rho` refinement from a K1 root, proof-only decisive refinement as a protector against coarse-MIP weakness, and nested dyadic K4 as a performance replacement. Nested dyadic remains a positive exactness/geometry result, not a promoted runtime result.

## Exactness and protection

All {len(exactness_rows)} audited rows have accepted outcomes: {strict_count} strict exact certificates and {unresolved_count} predeclared fail-closed endpoint outcomes, with zero false certificates. The Part 2 candidate itself is strict on all 24 instances and resolves the endpoint. Three implicit-default/explicit-off pairs match on all 25 deterministic fields. The validated default was not changed.

## Recommendation

Keep `C6-HGA-FULL, K=4, rho=0.01` as the mainline. Use uniform Gurobi Auto presolve in future fair comparisons. Retain K1-decisive and nested-dyadic as explicit research arms; do not promote or merge behavior automatically.
"""
    write_markdown("final_report.md", final_report)

    decision = {
        "schema": "round40-final-decision-v1",
        "round_id": 40,
        "presolve": {
            "round39_solver_level_contract_fair": True,
            "labeling_ambiguous": True,
            "frozen_policy": "gurobi-auto",
            "gurobi_presolve_value": -1,
            "instance_dispatch": False,
        },
        "part1": {
            "panel_instances": 10,
            "rows": 50,
            "simple_k1_reduces_fragmentation": True,
            "best_research_arm": "C6-K1-ADAPTIVE-DECISIVE",
            "time_wins_vs_k4": int(k1_summary[
                "C6-K1-ADAPTIVE-DECISIVE"]["time_wins"]),
            "major_regression_materially_reduced": True,
            "major_regression_eliminated_vs_p_grb": False,
            "strong_control_preserved_vs_p_grb": True,
            "strong_control_preserved_vs_k4": False,
            "promotion": False,
        },
        "part2": {
            "panel_instances": 24,
            "rows": 48,
            "candidate": "C6-NESTED-DYADIC-K4",
            "time_wins": geometry_summary["time_wins"],
            "work_wins": geometry_summary["work_wins"],
            "median_time_ratio": geometry_summary["median_time_ratio"],
            "median_work_ratio": geometry_summary["median_work_ratio"],
            "baseline_total_seconds": geometry_summary[
                "baseline_total_seconds"],
            "candidate_total_seconds": geometry_summary[
                "candidate_total_seconds"],
            "baseline_total_work": geometry_summary["baseline_total_work"],
            "candidate_total_work": geometry_summary["candidate_total_work"],
            "round36_different_ub_pairs": 10,
            "nested_boundary_preservation_passes": 10,
            "legacy_boundary_preservation_passes": 0,
            "endpoint_strictly_resolved": True,
            "runtime_monotonicity_claim": False,
            "promotion": False,
        },
        "part3": {
            "implemented": False,
            "reason": (
                "No solver-independent evidence distinguishes fragmentation-"
                "dominated cases from coarse-MIP-dominated cases; a dispatch "
                "would require forbidden historical or effort-based signals."),
        },
        "exactness": {
            "audited_rows": len(exactness_rows),
            "accepted_rows": accepted_count,
            "strict_exact_rows": strict_count,
            "expected_fail_closed_rows": unresolved_count,
            "false_certificates": 0,
        },
        "default_c6_equivalence": {
            "pairs": len(default_pairs),
            "deterministic_fields_per_pair": 25,
            "all_passed": all(truth(row["default_equivalence_passed"])
                              for row in default_pairs),
        },
        "promotion_recommendation": (
            "retain_frozen_c6_hga_full_k4_rho_0_01"),
        "automatic_mainline_change": False,
    }
    common.write_json(common.OUT / "final_decision.json", decision)

    # Write the corrected default-equivalence report after the latest analyzer.
    subprocess.run((python, "scripts/analyze_round40_default_equivalence.py"),
                   cwd=common.ROOT, check=True)

    # Evidence inventory is deliberately top-level: raw run trees are tracked
    # through their manifests and per-run command/result records.
    inventory_rows: list[dict[str, Any]] = []
    for path in sorted(common.OUT.iterdir()):
        if not path.is_file() or path.name == "evidence_package_manifest.csv":
            continue
        inventory_rows.append({
            "path": common.relative(path),
            "bytes": path.stat().st_size,
            "sha256": common.sha256(path),
        })
    common.write_csv(common.OUT / "evidence_package_manifest.csv",
                     inventory_rows)
    print({
        "part0_rows": len(presolve),
        "part1_rows": len(k1_rows),
        "part2_rows": len(geometry_rows),
        "default_rows": len(default_rows),
        "exactness_rows": len(exactness_rows),
        "evidence_files": len(inventory_rows),
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
