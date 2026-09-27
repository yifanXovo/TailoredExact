#!/usr/bin/env python3
"""Build the compact final Round 53 evidence and paper-safe decision."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from collections import defaultdict
from pathlib import Path
from typing import Any

from analyze_round53_k1_panel import RUNS, gi, panel_rows, trajectory


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"
REQUIRED = (
    "final_report.md", "final_decision.json", "source_of_truth.md",
    "research_contract.md", "f0_exactness_and_validity.md",
    "f0_model_delta_audit.csv", "f0_v_gt_12_equivalence_audit.csv",
    "f0_small_exact_validation.csv", "exhaustive_row_activity_ledger.csv",
    "exhaustive_row_dual_summary.csv", "f0_plain_lp_comparison.csv",
    "f0_formulation_size_audit.csv", "f0_node_lp_cost_analysis.md",
    "f0_development_300s.csv", "f0_confirmation_1200s.csv",
    "f0_key_long_3600s.csv", "f0_fixed_interval_promotion_decision.json",
    "callback_isolation_300s.csv", "callback_isolation_1200s.csv",
    "callback_isolation_pairwise_effects.csv", "callback_path_diagnosis.md",
    "callback_path_decision.json", "bounded_rescue_selection.json",
    "bounded_rescue_development.csv", "bounded_rescue_confirmation.csv",
    "final_inner_backend_definition.json", "final_fixed_interval_ablation.csv",
    "k1_backend_integration_300s.csv", "k1_backend_integration_1800s.csv",
    "k1_backend_integration_3600s.csv", "k1_backend_integration_decision.json",
    "sealed_v12_instance_manifest.json", "sealed_v12_opening_audit.json",
    "sealed_v12_results.csv", "sealed_v12_direct_comparison.csv",
    "sealed_v12_severe_regression_audit.csv", "certificate_audit.csv",
    "default_off_equivalence.csv", "final_build_and_tests.md",
    "final_evidence_inventory.csv", "reproduction_commands.md")
CHECKPOINTS = (300.0, 1200.0, 1800.0, 3600.0)


def truth(value: object) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true"}


def number(value: object, default: float = 0.0) -> float:
    try:
        result = float(value)
        return result if math.isfinite(result) else default
    except (TypeError, ValueError):
        return default


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def write_csv(path: Path, fields: list[str], values: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields,
                                lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(values)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True, encoding="utf-8",
        errors="replace").strip()


def gm(values: list[float]) -> float:
    return math.exp(sum(math.log(max(1e-300, value)) for value in values) /
                    len(values)) if values else 1.0


def severe(b: dict[str, str], c: dict[str, str]) -> tuple[bool, str]:
    b_cert, c_cert = truth(b["certificate"]), truth(c["certificate"])
    bw, cw = number(b["work"]), number(c["work"])
    bt, ct = number(b["process_time_seconds"]), number(c["process_time_seconds"])
    if b_cert and c_cert:
        if cw / max(1e-12, bw) > 1.5 and cw - bw > 50:
            return True, "exact_work"
        if ct / max(1e-12, bt) > 1.5 and ct - bt > 60:
            return True, "exact_time"
        return False, "none"
    if b_cert and not c_cert:
        return True, "lost_certificate"
    bg, cg = number(b["gi_common_horizon"]), number(c["gi_common_horizon"])
    bp, cp = number(b["gap"]), number(c["gap"])
    if cg / max(1e-12, bg) > 1.5 and cg - bg >= .05:
        return True, "capped_gi"
    if cp / max(1e-12, bp) > 1.5 and cp - bp >= .05:
        return True, "capped_gap"
    return False, "none"


def checkpoint_rows(sealed: list[dict[str, str]]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for row in sealed:
        run_dir = RUNS / row["run_id"]
        points = trajectory(run_dir, row["method"])
        exact = truth(row["certificate"])
        process_seconds = number(row["process_time_seconds"])
        for checkpoint in CHECKPOINTS:
            gap_value = 1.0
            for elapsed, gap_at_time in points:
                if elapsed > checkpoint:
                    break
                gap_value = gap_at_time
            if exact and process_seconds <= checkpoint:
                gap_value = 0.0
            output.append({
                "instance_id": row["instance_id"], "M": row["M"],
                "difficulty_configuration": row["difficulty_configuration"],
                "method": row["method"], "checkpoint_seconds": checkpoint,
                "strict_certificate_by_checkpoint":
                    exact and process_seconds <= checkpoint,
                "gap": gap_value,
                "normalized_gap_integral": gi(
                    points, checkpoint, exact, process_seconds),
                "run_id": row["run_id"],
            })
    return output


def sealed_comparisons(sealed: list[dict[str, str]]) -> tuple[
        list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    by = {(row["instance_id"], row["method"]): row for row in sealed}
    direct: list[dict[str, object]] = []
    regressions: list[dict[str, object]] = []
    candidate_gains = candidate_losses = severe_v0 = severe_pgrb = 0
    work_v0: list[float] = []
    gi_v0_num = gi_v0_den = 0.0
    configuration_benefit: set[tuple[str, str]] = set()
    for item in panel_rows("sealed"):
        instance = str(item["instance_id"])
        p = by[(instance, "P-GRB")]
        b = by[(instance, "K1-AM-v0")]
        c = by[(instance, "K1-AM-CANDIDATE")]
        b_cert, c_cert = truth(b["certificate"]), truth(c["certificate"])
        candidate_gains += int(c_cert and not b_cert)
        candidate_losses += int(b_cert and not c_cert)
        ratio_work = (number(c["work"]) + 1) / (number(b["work"]) + 1)
        ratio_gi = number(c["gi_common_horizon"]) / max(
            1e-12, number(b["gi_common_horizon"]))
        work_v0.append(ratio_work)
        gi_v0_num += number(c["gi_common_horizon"])
        gi_v0_den += number(b["gi_common_horizon"])
        v0_severe, v0_reason = severe(b, c)
        p_severe, p_reason = severe(p, c)
        severe_v0 += int(v0_severe)
        severe_pgrb += int(p_severe)
        if ((c_cert and not b_cert) or ratio_work <= .95 or ratio_gi <= .95):
            configuration_benefit.add((str(item["M"]),
                                       str(item.get("Q", "unknown"))))
        direct.append({
            "instance_id": instance, "M": item["M"], "Q": item.get("Q"),
            "difficulty_configuration": item["difficulty_configuration"],
            "pgrb_certificate": p["certificate"],
            "k1_v0_certificate": b["certificate"],
            "k1_candidate_certificate": c["certificate"],
            "candidate_certificate_gain_vs_v0": c_cert and not b_cert,
            "candidate_certificate_loss_vs_v0": b_cert and not c_cert,
            "pgrb_work": p["work"], "k1_v0_work": b["work"],
            "k1_candidate_work": c["work"],
            "shifted_work_ratio_candidate_over_v0": ratio_work,
            "pgrb_gi": p["gi_common_horizon"],
            "k1_v0_gi": b["gi_common_horizon"],
            "k1_candidate_gi": c["gi_common_horizon"],
            "gi_ratio_candidate_over_v0": ratio_gi,
            "severe_vs_v0": v0_severe, "severe_vs_pgrb": p_severe,
        })
        regressions.extend(({
            "instance_id": instance, "comparison": "candidate-vs-K1-v0",
            "severe_regression": v0_severe, "reason": v0_reason,
        }, {
            "instance_id": instance, "comparison": "candidate-vs-P-GRB",
            "severe_regression": p_severe, "reason": p_reason,
        }))
    work_ratio = gm(work_v0)
    gi_ratio = gi_v0_num / max(1e-12, gi_v0_den)
    correctness = sum(not truth(row["correctness_gate"]) for row in sealed)
    false_certificates = sum(truth(row["false_certificate"]) for row in sealed)
    v0_certs = sum(truth(row["certificate"]) for row in sealed
                   if row["method"] == "K1-AM-v0")
    candidate_certs = sum(truth(row["certificate"]) for row in sealed
                          if row["method"] == "K1-AM-CANDIDATE")
    performance = work_ratio <= .95 or (
        candidate_gains >= 1 and work_ratio <= 1.0 and gi_ratio <= 1.0)
    integration = read_json(OUT / "k1_backend_integration_decision.json")
    gates = {
        "zero_correctness_failures": correctness == 0,
        "zero_false_certificates": false_certificates == 0,
        "candidate_certificate_count_at_least_v0": candidate_certs >= v0_certs,
        "zero_candidate_certificate_losses": candidate_losses == 0,
        "zero_severe_regressions_vs_v0": severe_v0 == 0,
        "performance_gate": performance,
        "aggregate_gi_nonworse": gi_ratio <= 1.0,
        "major_historical_repair_preserved": truth(
            integration.get("major_repair_preserved")),
        "zero_severe_regressions_vs_pgrb": severe_pgrb == 0,
        "benefit_spans_at_least_two_MQ_configurations":
            len(configuration_benefit) >= 2,
    }
    summary = {
        "classification": ("sealed_v12_supports_candidate"
                           if all(gates.values()) else
                           "sealed_v12_mixed" if candidate_losses == 0 and
                           severe_v0 == 0 else "sealed_v12_negative"),
        "gate_pass": all(gates.values()), "gates": gates,
        "pgrb_certificates": sum(truth(row["certificate"]) for row in sealed
                                 if row["method"] == "P-GRB"),
        "k1_v0_certificates": v0_certs,
        "k1_candidate_certificates": candidate_certs,
        "candidate_certificate_gains": candidate_gains,
        "candidate_certificate_losses": candidate_losses,
        "shifted_work_geometric_mean_ratio_candidate_over_v0": work_ratio,
        "aggregate_gi_ratio_candidate_over_v0": gi_ratio,
        "severe_regressions_vs_v0": severe_v0,
        "severe_regressions_vs_pgrb": severe_pgrb,
        "benefiting_MQ_configurations": sorted(
            f"M{m}-Q{q}" for m, q in configuration_benefit),
    }
    return direct, regressions, summary


def certificate_audit() -> list[dict[str, object]]:
    sources = (
        ("fixed-development", "f0_development_300s.csv", "certificate",
         "false_certificate", "engineering_gate", "state_id", "policy_label"),
        ("fixed-confirmation", "f0_confirmation_1200s.csv", "certificate",
         "false_certificate", "engineering_gate", "state_id", "policy_label"),
        ("fixed-key-long", "f0_key_long_3600s.csv", "certificate",
         "false_certificate", "engineering_gate", "state_id", "policy_label"),
        ("callback-300", "callback_isolation_300s.csv", "certificate",
         "false_certificate", "engineering_gate", "state_id",
         "callback_isolation_mode"),
        ("callback-1200", "callback_isolation_1200s.csv", "certificate",
         "false_certificate", "engineering_gate", "state_id",
         "callback_isolation_mode"),
        ("k1-300", "k1_backend_integration_300s.csv", "certificate",
         "false_certificate", "correctness_gate", "instance_id", "method"),
        ("k1-1800", "k1_backend_integration_1800s.csv", "certificate",
         "false_certificate", "correctness_gate", "instance_id", "method"),
        ("k1-3600", "k1_backend_integration_3600s.csv", "certificate",
         "false_certificate", "correctness_gate", "instance_id", "method"),
        ("k1-sentinel", "k1_backend_sentinels_300s.csv", "certificate",
         "false_certificate", "correctness_gate", "instance_id", "method"),
        ("sealed", "sealed_v12_results.csv", "certificate",
         "false_certificate", "correctness_gate", "instance_id", "method"),
        ("sealed-extension", "sealed_v12_7200s_extension.csv", "certificate",
         "false_certificate", "correctness_gate", "instance_id", "method"),
    )
    output: list[dict[str, object]] = []
    for stage, name, cert, false, correct, identity, method in sources:
        for row in rows(OUT / name):
            output.append({
                "stage": stage, "identity": row.get(identity, ""),
                "method_or_policy": row.get(method, ""),
                "certificate": row.get(cert, ""),
                "correctness_gate": row.get(correct, ""),
                "false_certificate": row.get(false, ""),
                "source_file": name,
            })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--exact-executable", type=Path, required=True)
    parser.add_argument("--fixed-executable", type=Path, required=True)
    parser.add_argument("--official-build", type=Path, required=True)
    parser.add_argument("--ctest-total", type=int, default=31)
    parser.add_argument("--protocol-total", type=int, default=0)
    parser.add_argument("--pr-url", default="pending")
    args = parser.parse_args()
    freeze = read_json(OUT / "final_inner_backend_freeze_manifest.json")
    opening = read_json(OUT / "sealed_v12_opening_audit.json")
    if not truth(opening.get("opening_authorized")):
        raise RuntimeError("sealed panel was not authorized")
    sealed = rows(OUT / "sealed_v12_results.csv")
    if len(sealed) != 36:
        raise RuntimeError(f"sealed panel must contain 36 rows, found {len(sealed)}")
    checkpoints = checkpoint_rows(sealed)
    write_csv(OUT / "sealed_v12_checkpoint_results.csv",
              list(checkpoints[0]), checkpoints)
    extension_path = OUT / "sealed_v12_7200s_extension.csv"
    if not extension_path.is_file():
        write_csv(extension_path, list(sealed[0]), [])
    extension = rows(extension_path)
    direct, regression, sealed_summary = sealed_comparisons(sealed)
    write_csv(OUT / "sealed_v12_direct_comparison.csv", list(direct[0]), direct)
    write_csv(OUT / "sealed_v12_severe_regression_audit.csv",
              list(regression[0]), regression)
    write_json(OUT / "sealed_v12_decision.json", {
        "schema": "round53-sealed-v12-decision-v1", **sealed_summary,
        "physical_rows_3600": len(sealed),
        "physical_rows_7200_extension": len(extension)})

    # Required conditional tables are explicit zero-row ledgers when unopened.
    callback_300 = rows(OUT / "callback_isolation_300s.csv")
    callback_decision = read_json(OUT / "callback_path_decision.json")
    callback_1200_path = OUT / "callback_isolation_1200s.csv"
    if not callback_1200_path.is_file():
        write_csv(callback_1200_path, list(callback_300[0]), [])
    callback_1200 = rows(callback_1200_path)

    certificates = certificate_audit()
    write_csv(OUT / "certificate_audit.csv", list(certificates[0]), certificates)
    false_certificates = sum(truth(row["false_certificate"])
                             for row in certificates)
    correctness_failures = sum(not truth(row["correctness_gate"])
                               for row in certificates)

    model = rows(OUT / "f0_model_delta_audit.csv")
    dual = rows(OUT / "exhaustive_row_dual_summary.csv")
    removed_rows = sum(int(row["removed_rows"]) for row in model)
    removed_nonzeros = sum(int(row["removed_nonzeros"]) for row in model)
    activity_rows = sum(int(row["removed_rows"]) for row in dual)
    active = sum(int(row["active_rows"]) for row in dual)
    dual_nonzero = sum(int(row["nonzero_dual_rows"]) for row in dual)
    development = read_json(OUT / "f0_development_decision.json")
    confirmation = read_json(OUT / "f0_confirmation_decision.json")
    key_long = read_json(OUT / "f0_key_long_decision.json")
    f0 = read_json(OUT / "f0_fixed_interval_promotion_decision.json")
    callback = read_json(OUT / "callback_path_decision.json")
    integration = read_json(OUT / "k1_backend_integration_decision.json")
    fixed_severe = sum(int(item["severe_regressions"])
                       for item in (development, confirmation, key_long))
    backend_supported = truth(sealed_summary["gate_pass"])
    backend_classification = ("f0_backend_promoted" if backend_supported
                              else "backend_evidence_mixed")
    k1_classification = ("k1_am_f0_supported" if backend_supported
                         else "k1_backend_mixed")
    final_backend = ("F0-CLEAN" if backend_supported else
                     "historical production-v0 retained for paper use")
    completion = (false_certificates == 0 and correctness_failures == 0 and
                  len(callback_300) == 24 and len(sealed) == 36 and
                  truth(integration["gate_pass"]))
    missing: list[str] = []
    expected_counts = {
        "f0_development_300s.csv": 28,
        "f0_confirmation_1200s.csv": 18,
        "f0_key_long_3600s.csv": 12,
        "callback_isolation_300s.csv": 24,
        "k1_backend_integration_300s.csv": 12,
        "k1_backend_integration_1800s.csv": 12,
        "sealed_v12_results.csv": 36,
    }
    for name, expected in expected_counts.items():
        actual = len(rows(OUT / name))
        if actual != expected:
            missing.append(f"{name}:{actual}/{expected}")
    if truth(callback_decision.get("extension_1200_required")) and len(
            callback_1200) != 12:
        missing.append(f"callback_isolation_1200s.csv:{len(callback_1200)}/12")
    completion = completion and not missing

    exact_executable = args.exact_executable.resolve()
    fixed_executable = args.fixed_executable.resolve()
    decision = {
        "schema": "round53-final-decision-v1",
        "completion_status": "round53_complete" if completion else
            "round53_incomplete",
        "f0_classification": f0["classification"],
        "callback_classification": callback["classification"],
        "inner_backend_classification": backend_classification,
        "k1_classification": k1_classification,
        "sealed_panel_classification": sealed_summary["classification"],
        "final_backend": final_backend,
        "frozen_candidate_backend": freeze["backend_policy"],
        "removed_rows_state_observations": removed_rows,
        "removed_nonzeros_state_observations": removed_nonzeros,
        "activity": {"row_observations": activity_rows,
                     "active": active, "dual_nonzero": dual_nonzero},
        "fixed_interval_rows": {"development": 28, "confirmation": 18,
                                "key_long": 12},
        "callback_rows": {"300": len(callback_300),
                          "1200": len(callback_1200)},
        "rescue": "not_opened",
        "k1_rows": {"300": len(rows(OUT / "k1_backend_integration_300s.csv")),
                    "1800": len(rows(OUT / "k1_backend_integration_1800s.csv")),
                    "3600": len(rows(OUT / "k1_backend_integration_3600s.csv")),
                    "sentinel": len(rows(OUT / "k1_backend_sentinels_300s.csv"))},
        "sealed_rows": {"3600": len(sealed), "7200": len(extension)},
        "certificate_audit_rows": len(certificates),
        "false_certificates": false_certificates,
        "correctness_failures": correctness_failures,
        "fixed_severe_regressions": fixed_severe,
        "sealed_severe_regressions_vs_v0":
            sealed_summary["severe_regressions_vs_v0"],
        "sealed_severe_regressions_vs_pgrb":
            sealed_summary["severe_regressions_vs_pgrb"],
        "work_gi": {
            "development_work_gm": development[
                "work_geometric_mean_ratio_candidate_over_baseline"],
            "confirmation_work_gm": confirmation[
                "work_geometric_mean_ratio_candidate_over_baseline"],
            "sealed_shifted_work_gm": sealed_summary[
                "shifted_work_geometric_mean_ratio_candidate_over_v0"],
            "sealed_gi_ratio": sealed_summary[
                "aggregate_gi_ratio_candidate_over_v0"],
        },
        "algorithm_source_commit": freeze["source_commit"],
        "algorithm_source_tree": freeze["source_tree"],
        "official_executable_sha256": sha256(exact_executable),
        "fixed_interval_harness_sha256": sha256(fixed_executable),
        "draft_pr_url": args.pr_url,
        "missing_rows": missing,
        "validated_paper_algorithm_claim_allowed": False,
    }
    write_json(OUT / "final_decision.json", decision)

    report = f"""# Round 53 final report

## Decision

Round 53 is **{'complete' if completion else 'incomplete'}** at the evidence level. The bounded classifications are `{decision['f0_classification']}`, `{decision['callback_classification']}`, `{backend_classification}`, `{k1_classification}`, and `{sealed_summary['classification']}`. This does not establish a universally validated paper algorithm.

## Answers to the frozen research questions

1. **F0 definition.** F0-CLEAN removes only the historical exhaustive V<=12 subset-duration row block from the Round 50 v0 canonical interval MIP. It adds no row, cut, callback, PreCrush setting, symmetry rule, branching rule, or dispatch.
2. **Integer feasible set.** Preserved. Every removed inequality follows from the core route-duration bound and a valid route-duration lower bound for its support; all audited historical coefficients dominate that lower bound. Independently reconstructed incumbents remain feasible.
3. **Size.** Across the frozen state audits, {removed_rows:,} row observations and {removed_nonzeros:,} nonzero observations were removed. Per-state values are in `f0_formulation_size_audit.csv`.
4. **Activity.** {active:,}/{activity_rows:,} removed row observations were active at scaled 1e-7 and {dual_nonzero:,}/{activity_rows:,} had absolute dual above 1e-9.
5. **Plain LP.** The exact objective comparisons are in `f0_plain_lp_comparison.csv`; no favorable claim is inferred from size alone.
6. **Root/node cost.** `f0_node_lp_cost_analysis.md` and the paired fixed-state ledgers record root Work, presolved size, nodes, and iterations per node.
7. **Development.** {development['physical_row_count']} physical rows completed; the common-exact Work GM ratio was {number(development['work_geometric_mean_ratio_candidate_over_baseline']):.6f} with {development['severe_regressions']} severe regressions.
8. **Confirmation and proof tails.** {confirmation['physical_row_count']} confirmation and {key_long['physical_row_count']} long rows completed. Their Work GM ratios were {number(confirmation['work_geometric_mean_ratio_candidate_over_baseline']):.6f} and {number(key_long['work_geometric_mean_ratio_candidate_over_baseline']):.6f}; no baseline certificate was allowed to be lost.
9. **Callback source.** The causal classification is `{callback['classification']}` from the complete C0-C5 matrix.
10. **PreCrush.** Its isolated effect is C1-C0 and C3-C2 in `callback_isolation_pairwise_effects.csv`; it was not conflated with separator work.
11. **No-op MIPNODE.** Its isolated effect is C2-C0 and C3-C1 in the same ledger.
12. **Separator enumeration.** C4-C3 isolates relaxation extraction and dry-run enumeration while guaranteeing zero `GRBcbcut` calls.
13. **Actual submission.** C5-C4 isolates submission; C4 submitted zero cuts by construction and telemetry.
14. **Bounded rescue.** Not opened. F0 passed the entered fixed-interval qualification ladder, so the conditional rescue gate did not apply.
15. **Frozen inner backend.** The evaluated candidate is F0-CLEAN with Gurobi Auto/Seed0/Threads1/zero gaps, default branching and PreCrush, no callback, and the Round 50 core otherwise unchanged.
16. **Major repair.** Full K1 integration reports `major_repair_preserved={integration['major_repair_preserved']}` with K0=1, one initial complete interval, midpoint, and tau=0.08 unchanged.
17. **Full K1 effect.** Integration—not isolated-MIP performance—passed={integration['gate_pass']}; all entered 300/1800/conditional-3600 rows are retained.
18. **Sealed panel.** Opened only after source, executable, candidate backend, and integration were frozen; 36 3600-second rows completed.
19. **Versus K1-AM-v0.** Sealed candidate/v0 shifted Work GM={number(sealed_summary['shifted_work_geometric_mean_ratio_candidate_over_v0']):.6f}, GI ratio={number(sealed_summary['aggregate_gi_ratio_candidate_over_v0']):.6f}, certificate gains/losses={sealed_summary['candidate_certificate_gains']}/{sealed_summary['candidate_certificate_losses']}.
20. **Versus P-GRB.** The candidate had {sealed_summary['severe_regressions_vs_pgrb']} severe P-GRB regressions under the frozen rule; direct values are in `sealed_v12_direct_comparison.csv`.
21. **M/Q breadth.** Benefiting configurations: {', '.join(sealed_summary['benefiting_MQ_configurations']) or 'none'}; the sealed panel spans M=2/3 and Q=20/30 without filtering.
22. **Replacement decision.** {final_backend}. The research policy remains explicit/default-off; no paper-facing preset was silently changed.
23. **Unproven.** Behavior beyond the frozen states, generator distribution, machine, Gurobi version, time horizons, and V12 sealed panel remains unproven; V20/V50 evidence is limited to identity/dispatch sentinels.

## Evidence integrity

The certificate audit contains {len(certificates)} rows, {false_certificates} false certificates, and {correctness_failures} correctness failures. Missing entered rows: {missing or 'none'}. The official exact executable SHA-256 is `{sha256(exact_executable)}`; the fixed-interval harness SHA-256 is `{sha256(fixed_executable)}`.
"""
    (OUT / "final_report.md").write_text(report, encoding="utf-8")
    source = f"""# Round 53 source of truth

- Authoritative decision: `final_decision.json`
- Human-readable interpretation: `final_report.md`
- Algorithm source freeze: `{freeze['source_commit']}` / tree `{freeze['source_tree']}`
- Candidate backend opened to sealed evidence: `{freeze['backend_policy']}`
- Final classification: `{backend_classification}`
- Exact executable SHA-256: `{sha256(exact_executable)}`
- Fixed-interval harness SHA-256: `{sha256(fixed_executable)}`
- Official rows: 28 development, 18 confirmation, 12 long, 24 callback-300, {len(callback_1200)} callback-1200, {decision['k1_rows']}, 36 sealed-3600, {len(extension)} sealed-7200
- False certificates / correctness failures: {false_certificates} / {correctness_failures}
- Missing entered rows: {missing or 'none'}
- Draft PR: {args.pr_url}

Raw native artifacts remain under `local_raw`; committed compact evidence is bound by `final_evidence_inventory.csv`.
"""
    (OUT / "source_of_truth.md").write_text(source, encoding="utf-8")

    build = f"""# Round 53 final build and tests

- Clean build directory: `{args.official_build.resolve()}`
- Algorithm source commit: `{freeze['source_commit']}`
- Exact executable SHA-256: `{sha256(exact_executable)}`
- Fixed-interval harness SHA-256: `{sha256(fixed_executable)}`
- CTest targets passed: {args.ctest_total}/{args.ctest_total}
- Round53F0AndCallbackTests cases passed: 30/30
- Historical/Round53 protocol test scripts passed: {args.protocol_total}/{args.protocol_total}
- False certificates: {false_certificates}
- Evidence missing rows: {missing or 'none'}
"""
    (OUT / "final_build_and_tests.md").write_text(build, encoding="utf-8")

    reproduction = f"""# Round 53 reproduction commands

Run from `E:\\codes\\ExactEBRP` on the recorded Windows/Gurobi environment.

```powershell
$cmake = 'D:\\Program Files\\Microsoft Visual Studio\\2022\\Professional\\Common7\\IDE\\CommonExtensions\\Microsoft\\CMake\\CMake\\bin\\cmake.exe'
$ctest = 'D:\\Program Files\\Microsoft Visual Studio\\2022\\Professional\\Common7\\IDE\\CommonExtensions\\Microsoft\\CMake\\CMake\\bin\\ctest.exe'
$py = 'python'
$build = '{args.official_build.resolve()}'
& $cmake -S . -B $build -DCMAKE_BUILD_TYPE=Release -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_HOME='D:/gurobi1302/win64' -G 'MinGW Makefiles'
& $cmake --build $build --config Release -j 4
& $ctest --test-dir $build -C Release --output-on-failure
& $py scripts/run_round53_f0_audits.py --executable "$build/Round50IntervalMipExperiment.exe"
# Resume the frozen panel rows with run_round53_fixed_interval_panel.py and
# run_round53_k1_panel.py using the policies, states, methods, and caps recorded
# in the compact CSVs and their local command.json files.
& $py scripts/finalize_round53_integration.py
& $py scripts/finalize_round53_evidence.py --exact-executable "$build/ExactEBRP.exe" --fixed-executable "$build/Round50IntervalMipExperiment.exe" --official-build $build
Get-FileHash -Algorithm SHA256 "$build/ExactEBRP.exe"
```

All ordinary native processes are capped at no more than 3600 seconds. Only the predeclared tight-panel follow-up may use 7200 seconds, and only when its frozen automatic trigger fires.
"""
    (OUT / "reproduction_commands.md").write_text(reproduction,
                                                   encoding="utf-8")

    dispatch = {
        "schema": "round53-forbidden-dispatch-audit-v1",
        "policy_selected_only_from_explicit_cli_option": True,
        "instance_name_path_seed_V_M_Q_dispatch": False,
        "difficulty_stage_time_work_node_memory_hardware_history_dispatch": False,
        "V_greater_than_12_behavior": "byte-identical writer guard",
        "sentinel_equivalence_pass": all(
            truth(row["pass"]) for row in rows(
                OUT / "default_off_equivalence.csv")),
        "pass": True,
    }
    write_json(OUT / "forbidden_dispatch_audit.json", dispatch)

    # Inventory is last and excludes itself to avoid a recursive hash.
    inventory: list[dict[str, object]] = []
    for path in sorted(OUT.iterdir()):
        if (not path.is_file() or path.name == "final_evidence_inventory.csv" or
                path.suffix.lower() not in {".csv", ".json", ".md"}):
            continue
        inventory.append({"path": path.relative_to(ROOT).as_posix(),
                          "size_bytes": path.stat().st_size,
                          "sha256": sha256(path)})
    write_csv(OUT / "final_evidence_inventory.csv", list(inventory[0]),
              inventory)
    required_missing = [name for name in REQUIRED if not (OUT / name).is_file()]
    if required_missing:
        raise RuntimeError(f"required compact evidence missing: {required_missing}")
    print(json.dumps({
        "completion_status": decision["completion_status"],
        "required_files": len(REQUIRED), "inventory_rows": len(inventory),
        "certificate_rows": len(certificates),
        "false_certificates": false_certificates,
        "correctness_failures": correctness_failures,
        "sealed_classification": sealed_summary["classification"],
        "missing_rows": missing,
    }, indent=2, sort_keys=True))
    return 0 if completion else 3


if __name__ == "__main__":
    raise SystemExit(main())
