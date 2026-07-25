#!/usr/bin/env python3
"""Write the evidence-backed Round 31 final report."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_nonblocking_gurobi_c6_round31"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def rows(name: str) -> list[dict[str, str]]:
    path = OUT / name
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def integer(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def number(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def comparison_summary(data: list[dict[str, str]]) -> dict[str, int]:
    available = [
        row for row in data
        if row.get("auc_status") == "observed_common_window"]
    return {
        "rows": len(data),
        "final_wins": sum(
            number(row.get("final_lb_delta_right_minus_left")) > 1e-7
            for row in data),
        "final_losses": sum(
            number(row.get("final_lb_delta_right_minus_left")) < -1e-7
            for row in data),
        "final_ties": sum(
            abs(number(row.get(
                "final_lb_delta_right_minus_left"))) <= 1e-7
            for row in data),
        "auc_available": len(available),
        "auc_wins": sum(
            number(row.get(
                "normalized_proof_auc_delta_right_minus_left")) > 1e-7
            for row in available),
        "auc_losses": sum(
            number(row.get(
                "normalized_proof_auc_delta_right_minus_left")) < -1e-7
            for row in available),
        "auc_ties": sum(
            abs(number(row.get(
                "normalized_proof_auc_delta_right_minus_left"))) <= 1e-7
            for row in available),
    }


def main() -> int:
    source = (OUT / "source_of_truth.md").read_text(encoding="utf-8")
    manifest = load_json("c6_manifest.json")
    build = load_json("stage0_build_and_tests.json")
    stage0 = load_json("stage0_gate_summary.json")
    development = load_json("c6_development_selection.json")
    final = load_json("final_audit_summary.json")
    primary_rows = rows("p_grb_vs_c6.csv")
    sealed_rows = [
        row for row in rows("stage3_sealed_heldout.csv")
        if row.get("arm") in {"P-GRB", "C6-CANDIDATE"}]
    c5_rows = rows("c5_vs_c6.csv")
    hga_rows = rows("p_grb_hga_ablation.csv")
    s0_rows = rows("s0_vs_c6_anchor.csv")
    family_rows = rows("existing_family_summary.csv")
    sealed_family = rows("sealed_family_summary.csv")
    repeat_rows = rows("stage5_repeatability_audit.csv")
    medium_rows = rows("stage6_medium_run.csv")
    blocking = rows("terminal_blocking_summary.csv")
    avoidance = rows("child_lookahead_avoidance.csv")
    lifecycle = rows("lifecycle_and_resource_summary.csv")
    primary = comparison_summary(primary_rows)
    c5 = comparison_summary(c5_rows)

    stage2_c6_ids = {
        row["run_id"] for row in rows("stage2_existing_primary.csv")
        if row.get("arm") == "C6-CANDIDATE"}
    primary_blocking = [
        row for row in blocking if row.get("run_id") in stage2_c6_ids]
    primary_avoidance = [
        row for row in avoidance if row.get("run_id") in stage2_c6_ids]
    primary_lifecycle = [
        row for row in lifecycle if row.get("run_id") in stage2_c6_ids]
    terminal_calls = sum(
        integer(row.get("terminal_mip_calls")) for row in primary_blocking)
    terminal_work = sum(
        number(row.get("terminal_mip_work_ledger"))
        for row in primary_blocking)
    total_work = sum(
        number(row.get("total_external_work"))
        for row in primary_blocking)
    lp_calls = sum(
        integer(row.get("lp_calls")) for row in primary_lifecycle)
    partial_calls = sum(
        integer(row.get("partial_target_calls"))
        for row in primary_lifecycle)
    child_avoided = sum(
        integer(row.get("child_lookaheads_avoided"))
        for row in primary_avoidance)
    target_phases = sum(
        integer(row.get("next_leaf_target_phases")) +
        integer(row.get("child_bound_target_phases"))
        for row in primary_avoidance)
    requeues = sum(
        integer(row.get("native_requeues"))
        for row in primary_avoidance)
    forced_avoided = sum(
        integer(row.get("forced_splits_avoided"))
        for row in primary_avoidance)
    splits = sum(
        integer(row.get("splits")) for row in primary_lifecycle)
    cutoff_prunes = sum(
        integer(row.get("lp_cutoff_prunes")) for row in primary_blocking)
    first_times = [
        number(row.get("first_observed_process_seconds"))
        for row in rows("time_to_gap_thresholds.csv")
        if row.get("arm") == "C6-CANDIDATE" and
        row.get("common_gap_threshold") == "0.1" and
        truth(row.get("reached"))]
    stagnation = [
        number(row.get("final_stagnation_seconds"))
        for row in primary_blocking]
    sealed_pairs: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in sealed_rows:
        sealed_pairs[row["instance"]][row["arm"]] = row
    sealed_final_wins_ties = 0
    for pair in sealed_pairs.values():
        if {"P-GRB", "C6-CANDIDATE"} <= pair.keys():
            sealed_final_wins_ties += int(
                number(pair["C6-CANDIDATE"].get("valid_final_lb")) >=
                number(pair["P-GRB"].get("valid_final_lb")) - 1e-7)
    medium_by_instance: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in medium_rows:
        medium_by_instance[row["instance"]][row["arm"]] = row

    def medium_comparison(left: str) -> tuple[int, int, int]:
        wins = losses = ties = 0
        for pair in medium_by_instance.values():
            if {left, "C6-CANDIDATE"} > pair.keys():
                continue
            delta = (
                number(pair["C6-CANDIDATE"].get("valid_final_lb")) -
                number(pair[left].get("valid_final_lb")))
            wins += delta > 1e-7
            losses += delta < -1e-7
            ties += abs(delta) <= 1e-7
        return wins, losses, ties

    medium_vs_p = medium_comparison("P-GRB")
    medium_vs_c5 = medium_comparison("C5-CANDIDATE")
    medium_certificates = {
        arm: sum(
            row.get("arm") == arm and truth(row.get("strict_certificate"))
            for row in medium_rows)
        for arm in ("P-GRB", "C5-CANDIDATE", "C6-CANDIDATE")
    }
    sealed_v50 = medium_by_instance.get(
        "round31_sealed_high_imbalance_V50_seed802548647", {})

    lines = [
        "# Round 31 final report",
        "",
        "## Outcome",
        "",
        f"Final classification: **{final['classification']}**.",
        "",
        "S0/F0-CPLEX remains the stable accepted paper mainline. C0-DIAG "
        "remains the exact but non-paper-compatible performance teacher. "
        "C5 remains the exact first-generation partial-bound transfer. C6 "
        "is retained as the Round 31 candidate; it is not automatically "
        "promoted.",
        "",
        "## Frozen provenance and toolchain",
        "",
        f"- Starting HEAD: `{manifest['starting_head']}`",
        f"- Frozen C6 source commit: `{manifest['source_commit']}`",
        f"- Observed live main at entry: "
        "`224e9bb333d08956dc37172d12544201bc48e5f5`",
        f"- Compiler: `{build['compiler']}`",
        f"- CMake: `{build['cmake']}`",
        f"- CPLEX: `{build['cplex_version']}`",
        f"- Gurobi: `{build['gurobi_version']}`",
        f"- CPLEX executable SHA-256: "
        f"`{build['cplex_executable_sha256']}`",
        f"- Gurobi executable SHA-256: "
        f"`{build['gurobi_executable_sha256']}`",
        "",
        "## Forensic diagnosis",
        "",
        "Phase A found that C5's failures were primarily continuation and "
        "scheduling failures, not evidence for a new inequality family. "
        "Thirty of 55 selected parents were no longer strictly controlling "
        "after their complete LP, making 60 child LPs avoidable. Eighty-six "
        "of 94 attained child targets then forced delayed splits with zero "
        "current child gain and zero immediate global-bound gain. No-gain "
        "terminal parents consumed 98.13% of terminal Work; a small set of "
        "root/cut-loop or deep one-node MIPs dominated the deadline losses. "
        "C5 interval models were also materially larger than P-GRB, "
        "especially at V50.",
        "",
        "## Selected C6 algorithm",
        "",
        "C6 is parent-native-first. After a complete parent LP, it requeues "
        "a parent that is no longer controlling. Otherwise it processes one "
        "launch-frozen target equal to the smallest strictly higher valid "
        "bound of another relevant leaf. Ties do not create targets. After "
        "that one OPEN_NATIVE_BOUNDED transition, child LPs are computed "
        "lazily only when the leaf controls again.",
        "",
        "The split threshold remains `rho=0.01`, and it is the sole policy "
        "threshold. A small current child gain targets the complete child "
        "disjunction bound. Reaching it retains and requeues the open parent "
        "with cached complete children; it never forces a delayed split. A "
        "no-gain parent launches exact closure after its unused frontier "
        "milestone is exhausted. Only optimality, infeasibility, or verified "
        "cutoff closes coverage.",
        "",
        "C6 adds zero strategy parameters and contains no internal time, "
        "Work, node, solution, attempt, retry, family, size, seed, path, or "
        "historical-objective dispatch.",
        "",
        "The implementation retains the same model object only. It makes no "
        "LP-basis, simplex-reoptimization, or native-tree continuation claim.",
        "",
        "## Tests and correctness",
        "",
        f"- C++ tests per clean build: {build['cpp_test_count_per_build']}",
        f"- Python test scripts: {build['python_test_script_count']}",
        f"- Stage 0 state-machine cases: "
        f"{stage0['state_machine_case_count']}",
        f"- Tiny exactness rows: {stage0['tiny_exactness_rows']}",
        f"- Moderate4301 sentinel rows: {stage0['sentinel_rows']}",
        f"- All Stage 0 gates: "
        f"{stage0['all_stage0_gates_passed']}",
        f"- Official false certificates: "
        f"{final['false_certificate_count']}",
        "",
        "## Development mechanism evidence",
        "",
        f"The 71-second development matrix contained {development['runs']} "
        f"rows: {development['c6_exact_phase_runs']} reached exact C6 and "
        f"{development['excluded_pre_exact_hga_deadline_runs']} was retained "
        "as a pre-exact HGA-deadline exclusion. C6 avoided "
        f"{development['child_lookaheads_avoided']} child lookaheads, ran "
        f"{development['next_leaf_target_phases']} next-leaf targets, reached "
        f"{development['next_leaf_targets_reached']}, and issued "
        f"{development['native_requeues']} native requeues.",
        "",
        "## Primary same-solver result: C6 versus P-GRB",
        "",
        f"- Final-LB wins/losses/ties: "
        f"{primary['final_wins']}/{primary['final_losses']}/"
        f"{primary['final_ties']}",
        f"- Observed-AUC wins/losses/ties over "
        f"{primary['auc_available']} compatible pairs: "
        f"{primary['auc_wins']}/{primary['auc_losses']}/"
        f"{primary['auc_ties']}",
        f"- Short-run broad-nonregression gate: "
        f"{final['short_run_gate_passed']}",
        "",
        "### Existing-family breakdown",
        "",
        "| Family | V | Rows | C6 final W/L/T | C6 AUC W/L/T |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in family_rows:
        lines.append(
            f"| {row['family']} | {row['V']} | {row['instances']} | "
            f"{row['right_final_lb_wins']}/"
            f"{row['left_final_lb_wins']}/{row['final_lb_ties']} | "
            f"{row['right_auc_wins']}/"
            f"{row['left_auc_wins']}/{row['auc_ties']} |")
    lines.extend([
        "",
        "## Sealed held-out evidence",
        "",
        f"Final-LB wins/ties versus P-GRB: {sealed_final_wins_ties}/6. "
        f"The frozen audit reports AUC wins/ties "
        f"{final['sealed_auc_wins_ties']}/6 where compatible.",
        "",
        "| Family | V | Rows | C6 final W/L/T | C6 AUC W/L/T |",
        "|---|---:|---:|---:|---:|",
    ])
    for row in sealed_family:
        lines.append(
            f"| {row['family']} | {row['V']} | {row['instances']} | "
            f"{row['right_final_lb_wins']}/"
            f"{row['left_final_lb_wins']}/{row['final_lb_ties']} | "
            f"{row['right_auc_wins']}/"
            f"{row['left_auc_wins']}/{row['auc_ties']} |")
    lines.extend([
        "",
        "## Ablations and anchors",
        "",
        f"- C6 versus C5 final-LB wins/losses/ties on directly paired "
        f"mechanism/sealed rows: {c5['final_wins']}/"
        f"{c5['final_losses']}/{c5['final_ties']}.",
        f"- P-GRB-HGA ablation rows: {len(hga_rows)}.",
        f"- S0/F0 anchor rows: {len(s0_rows)}.",
        "",
        "P-GRB-HGA changes only the independently verified incumbent start; "
        "it leaves the compact model and plain one-tree Gurobi configuration "
        "unchanged. S0 comparisons remain cross-solver anchors, not the "
        "primary promotion criterion.",
        "",
        "## C6 mechanism totals on the 17-instance primary matrix",
        "",
        f"- Parent/child LP optimize calls recorded: {lp_calls}",
        f"- Native target phases: {target_phases}",
        f"- Partial target optimize calls: {partial_calls}",
        f"- Native requeues: {requeues}",
        f"- Child lookaheads avoided: {child_avoided}",
        f"- Forced delayed splits avoided: {forced_avoided}",
        f"- Atomic splits: {splits}",
        f"- Terminal MIP calls: {terminal_calls}",
        f"- Terminal MIP Work: {terminal_work:.6f}",
        f"- Total external Work: {total_work:.6f}",
        f"- LP cutoff prunes: {cutoff_prunes}",
        f"- Mean observed time to common 10% gap among reached rows: "
        f"{(sum(first_times) / len(first_times)) if first_times else 0.0:.6f}s",
        f"- Mean final stagnation: "
        f"{(sum(stagnation) / len(stagnation)) if stagnation else 0.0:.6f}s",
        "",
        "## Repeatability and conditional medium runs",
        "",
        f"Repeatability rows: {len(repeat_rows)}. Exact target-sequence "
        f"matches: {sum(truth(row.get('target_sequence_exact')) for row in repeat_rows)}; "
        f"exact split-sequence matches: "
        f"{sum(truth(row.get('split_sequence_exact')) for row in repeat_rows)}.",
        "",
        f"Conditional Stage 6 executed: "
        f"{final['conditional_stage6_executed']}. Excluded conditional rows: "
        f"{final['excluded_stage6_rows']}.",
        "",
        "### Conditional 1200-second results",
        "",
        f"Stage 6 materialized {len(medium_rows)} rows over "
        f"{len(medium_by_instance)} instances. C6 final-LB "
        f"wins/losses/ties were {medium_vs_p[0]}/{medium_vs_p[1]}/"
        f"{medium_vs_p[2]} versus P-GRB and {medium_vs_c5[0]}/"
        f"{medium_vs_c5[1]}/{medium_vs_c5[2]} versus C5.",
        "",
        f"Strict certificates: P-GRB {medium_certificates['P-GRB']}, "
        f"C5 {medium_certificates['C5-CANDIDATE']}, "
        f"C6 {medium_certificates['C6-CANDIDATE']}.",
        "",
        "On sealed V50, C6 uniquely certified optimality in "
        f"{number(sealed_v50.get('C6-CANDIDATE', {}).get(
            'runtime_seconds')):.3f}s; P-GRB and C5 remained open at "
        "their fixed caps. On sealed V20, C5 and C6 certified while "
        "P-GRB remained open.",
        "",
        "The first Stage 6 launch was a zero-solve preflight refusal: "
        "the source freeze guard correctly detected the analyzer's "
        "analysis-only keyword-interface repair. The frozen analyzer bytes "
        "were restored for all 27 solver runs, and the one-line repair was "
        "reapplied only after the runner exited.",
        "",
        "## Final interpretation",
        "",
        f"Completed process rows: {final['completed_process_rows']}; failed "
        f"rows: {final['failed_process_rows']}; time-limited rows: "
        f"{final['time_limited_rows']}; emergency timeouts: "
        f"{final['emergency_timeout_rows']}.",
        "",
        "The unresolved mechanism, if C6 is not broadly dominant, is the "
        "remaining cost of complete parent closure and the gap between "
        "external interval-model proof structure and P-GRB's single compact "
        "native tree—not correctness, target validity, or delayed-split "
        "degeneracy.",
        "",
        f"A later long-run promotion study is justified: "
        f"{final['long_run_promotion_study_justified']}. Regardless, C6 does "
        "not replace S0/F0-CPLEX in this round.",
        "",
        "## Evidence package",
        "",
        f"- Files excluding manifest: "
        f"{final.get('evidence_package_file_count_excluding_self', 'pending')}",
        f"- Bytes excluding manifest: "
        f"{final.get('evidence_package_bytes_excluding_self', 'pending')}",
        f"- Largest artifact: "
        f"`{final.get('largest_artifact_path', 'pending')}` "
        f"({final.get('largest_artifact_bytes', 'pending')} bytes)",
        f"- Losslessly compressed files: "
        f"{final.get('losslessly_compressed_files', 'pending')}",
        f"- Restoration hashes verified: "
        f"{final.get('compression_restoration_hashes_verified', 'pending')}",
        "",
        "Task wall-clock and token usage are recorded in the final Codex "
        "handoff because those counters are supplied by the execution "
        "orchestrator, not by repository code.",
    ])
    (OUT / "final_report.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": final["classification"],
        "primary": primary,
        "sealed_final_wins_ties": sealed_final_wins_ties,
        "report_lines": len(lines),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
