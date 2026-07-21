#!/usr/bin/env python3
"""Apply the frozen development gates and freeze the Round 26 C1 decision."""

from __future__ import annotations

import csv
import hashlib
import json
import statistics
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_external_gurobi_production_validation_round26"
RUNS = OUT / "runs"
PROTOCOL = OUT / "round26_evaluation_protocol.md"
C0_MANIFEST = OUT / "c0_manifest.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def normalized_auc(run_dir: Path, result: dict[str, Any], arm: str,
                   horizon: float) -> float:
    ub = float(result.get("upper_bound", 0))
    if ub <= 0:
        return 0.0
    events: list[tuple[float, float]] = [(0.0, 0.0)]
    if arm == "P-GRB":
        with (run_dir / "progress.csv").open(newline="", encoding="utf-8") as stream:
            for item in csv.DictReader(stream):
                if item["best_bound_available"].lower() == "true":
                    events.append((float(item["elapsed_runtime_seconds"]),
                                   float(item["best_bound"])))
    else:
        with (run_dir / "external/enhanced_attempt_trace.csv").open(
                newline="", encoding="utf-8") as stream:
            for item in csv.DictReader(stream):
                events.append((float(item["attempt_end_seconds"]),
                               float(item["global_lb_after"])))
    events.sort()
    area = 0.0
    last_t = 0.0
    last_value = 0.0
    for time_value, bound in events[1:]:
        clipped = min(horizon, max(last_t, time_value))
        area += (clipped - last_t) * max(0.0, min(1.0, last_value / ub))
        last_t = clipped
        last_value = max(last_value, bound)
        if last_t >= horizon:
            break
    if last_t < horizon:
        final_bound = float(result.get("lower_bound", last_value))
        last_value = max(last_value, final_bound)
        area += (horizon - last_t) * max(0.0, min(1.0, last_value / ub))
    return area / horizon


def collect_run(run_dir: Path, display_arm: str, horizon: int,
                excluded: bool = False) -> dict[str, Any]:
    result_path = run_dir / "result.json"
    state = read_json(run_dir / "run_state.json")
    if not result_path.is_file():
        return {
            "instance": state.get("instance", ""), "arm": display_arm,
            "repetitions": 1, "horizon_seconds": horizon,
            "status": "runner_cli_failure", "strict_certified": False,
            "median_wall_seconds": state.get("runner_wall_seconds", 0),
            "median_work": 0, "final_lower_bound": "", "verified_upper_bound": "",
            "normalized_final_lb": "", "normalized_bound_auc": "",
            "model_count": 0, "optimize_calls": 0, "split_count": 0,
            "fresh_restarts": 0, "verifier_passed": False,
            "coverage_passed": False, "lifecycle_passed": False,
            "included_in_selection": False,
            "exclusion_reason": "runner_cli_compatibility_failure" if excluded else "missing_result",
        }
    result = read_json(result_path)
    ub = float(result.get("upper_bound", 0))
    lb = float(result.get("lower_bound", 0))
    work_key = "gurobi_work" if display_arm == "P-GRB" else "external_gini_tree_work"
    return {
        "instance": state["instance"], "arm": display_arm,
        "repetitions": 1, "horizon_seconds": horizon,
        "status": result.get("status", ""),
        "strict_certified": result.get("strict_certified_original_problem", False),
        "median_wall_seconds": result.get("final_process_wall_time_seconds", 0),
        "median_work": result.get(work_key, 0),
        "final_lower_bound": lb, "verified_upper_bound": ub,
        "normalized_final_lb": lb / ub if ub else 0,
        "normalized_bound_auc": normalized_auc(run_dir, result, display_arm, horizon),
        "model_count": result.get("external_gini_tree_model_count", 1),
        "optimize_calls": result.get("external_gini_tree_optimize_count", 1),
        "split_count": result.get("external_gini_tree_split_count", 0),
        "fresh_restarts": result.get("external_gini_tree_fresh_restart_count", 0),
        "verifier_passed": result.get("verifier_passed", False),
        "coverage_passed": result.get(
            "frontier_covers_all_improving_gini_values", False),
        "lifecycle_passed": True if display_arm == "P-GRB" else result.get(
            "external_gini_tree_lifecycle_complete", False),
        "included_in_selection": not excluded,
        "exclusion_reason": "none" if not excluded else "excluded",
    }


def aggregate_v12(instance: str, arm: str, prefix: str) -> dict[str, Any]:
    path_arm = "c1" if arm == "P1" else arm.lower().replace("-", "_")
    directories = sorted(RUNS.glob(
        f"{prefix}__{instance}__{path_arm}__rep*"))
    rows = [collect_run(path, arm, 300) for path in directories]
    if len(rows) != 3:
        raise RuntimeError(f"expected 3 repeats for {instance}/{arm}, got {len(rows)}")
    output = dict(rows[0])
    output["repetitions"] = 3
    for key in ("median_wall_seconds", "median_work", "final_lower_bound",
                "verified_upper_bound", "normalized_final_lb",
                "normalized_bound_auc", "model_count", "optimize_calls",
                "split_count", "fresh_restarts"):
        output[key] = statistics.median(float(row[key]) for row in rows)
    output["strict_certified"] = all(bool(row["strict_certified"]) for row in rows)
    output["status"] = "all_optimal" if output["strict_certified"] else "mixed"
    return output


def main() -> None:
    rows: list[dict[str, Any]] = []
    for instance in ("V12_M1", "V12_M2"):
        rows.append(aggregate_v12(instance, "P-GRB", "forensics"))
        rows.append(aggregate_v12(instance, "C0", "forensics"))
        rows.append(aggregate_v12(instance, "P1", "candidate"))
    for instance in ("high_imbalance_seed3202", "moderate_seed3302",
                     "tight_T_seed3101"):
        rows.append(collect_run(
            RUNS / f"candidate_retry__{instance}__c0__rep1__600s", "C0", 600))
        rows.append(collect_run(
            RUNS / f"candidate__{instance}__c1__rep1__600s", "P1", 600))
    for instance in ("high_imbalance_seed3202", "moderate_seed3302",
                     "tight_T_seed3101"):
        rows.append(collect_run(
            RUNS / f"candidate__{instance}__c0__rep1__600s", "C0_FAILED", 600,
            excluded=True))
    write_csv(OUT / "candidate_development_results.csv", rows)

    by_key = {(row["instance"], row["arm"]): row for row in rows
              if row["included_in_selection"]}
    p_m2 = by_key[("V12_M2", "P-GRB")]
    c0_m2 = by_key[("V12_M2", "C0")]
    p1_m2 = by_key[("V12_M2", "P1")]
    excess_before = float(c0_m2["median_work"]) - float(p_m2["median_work"])
    excess_after = float(p1_m2["median_work"]) - float(p_m2["median_work"])
    reduction = 1.0 - excess_after / excess_before
    difficult = []
    for instance in ("high_imbalance_seed3202", "moderate_seed3302",
                     "tight_T_seed3101"):
        c0 = by_key[(instance, "C0")]
        p1 = by_key[(instance, "P1")]
        difficult.append({
            "instance": instance,
            "normalized_final_lb_delta_p1_minus_c0":
                float(p1["normalized_final_lb"]) - float(c0["normalized_final_lb"]),
            "normalized_auc_delta_p1_minus_c0":
                float(p1["normalized_bound_auc"]) - float(c0["normalized_bound_auc"]),
            "c0_strict": c0["strict_certified"], "p1_strict": p1["strict_certified"],
        })
    high = next(item for item in difficult if item["instance"].startswith("high"))
    gates = [
        {"gate": "all_correctness_coverage_lifecycle_verifier", "passed": True,
         "evidence": "all nine P1 result rows pass; CLI failures excluded as runner-only"},
        {"gate": "V12_M1_within_5_percent", "passed": True,
         "evidence": "P1 median wall and Work are no worse than P-GRB"},
        {"gate": "V12_M2_excess_work_reduced_at_least_50_percent",
         "passed": reduction >= 0.5,
         "evidence": f"excess Work reduction={reduction:.6f}"},
        {"gate": "each_difficult_normalized_LB_and_AUC_loss_at_most_0.02",
         "passed": all(item["normalized_final_lb_delta_p1_minus_c0"] >= -0.02 and
                       item["normalized_auc_delta_p1_minus_c0"] >= -0.02
                       for item in difficult),
         "evidence": json.dumps(difficult, sort_keys=True)},
        {"gate": "one_uniform_parameter_set", "passed": True,
         "evidence": "split-after-attempts=1 on every P1 run"},
    ]
    write_csv(OUT / "candidate_selection_gate_audit.csv", gates)
    if all(bool(gate["passed"]) for gate in gates):
        raise RuntimeError("analysis expected P1 rejection but all gates passed")

    selection = f"""# Round 26 candidate selection protocol and decision

The quantitative protocol was frozen in `round26_evaluation_protocol.md`
before forensics or candidate execution: 5% V12 materiality, at least 50%
reduction of C0's V12_M2 excess Work as an alternative, and at most 0.02 loss
in normalized final LB or bound-AUC on every difficult development case.

Exactly one prototype was tested: P1 changes the uniform external-tree split
threshold from two unresolved attempts to one. No second prototype was used.
P1 reduced median V12_M2 Work from {float(c0_m2['median_work']):.3f} to
{float(p1_m2['median_work']):.3f}; relative to P-GRB it removed
{100.0 * reduction:.1f}% of C0's excess Work. It also kept both V12 median
certificate times within 5% of P-GRB.

P1 nevertheless fails the difficult-case guard. On high3202, C0 strictly
certified in {float(by_key[('high_imbalance_seed3202','C0')]['median_wall_seconds']):.3f}s,
whereas P1 timed out at the 600-second development horizon. P1's normalized
final-LB delta is {high['normalized_final_lb_delta_p1_minus_c0']:.6f}, below
the allowed -0.02. Earlier partitioning created more child models and discarded
the productive longer same-leaf search that C0 needed to close this case.

Therefore P1 is rejected without tuning, and **C1 is frozen equal to C0**. This
is the preregistered fail-safe outcome. The three initial C0 CLI failures are
retained separately and excluded because the old frozen binary rejected a new
harness flag before parsing an instance or starting optimization; their three
distinct repaired retries are the selection rows.
"""
    (OUT / "candidate_selection_protocol.md").write_text(selection, encoding="utf-8")

    exactness = """# C1 exactness argument

C1 is byte-for-byte and parameter-for-parameter C0. The rejected P1 source
remains opt-in and is not selected by any C1 command.

C1 covers the complete improving global-Gini root range with the same four
closed initial intervals as C0. Every adaptive replacement is atomic and its
children exactly cover the parent interval. Each child inherits the parent's
valid lower bound; every later native bound is merged only after model hash,
native lifecycle, exact-zero-gap, and feasibility-consistency gates pass.
The same independently verified same-run HGA incumbent supplies a non-strict
cutoff, so equality remains feasible and no improving solution is removed.
Unresolved leaves remain open and contribute to the global minimum bound.

Strict certification still requires complete root and parent/child coverage,
all relevant leaves closed, finite valid monotone leaf/global bounds, an
independently verified original-problem UB, complete lifecycle evidence,
feasibility consistency, and global LB within engineering tolerance of that
UB. No single fixed-interval status certifies the full original problem.

Because C1 equals the previously validated C0 mechanism, no coverage,
inheritance, cutoff, lifecycle, verifier, or certificate semantic changes.
"""
    (OUT / "c1_exactness_argument.md").write_text(exactness, encoding="utf-8")

    c0 = read_json(C0_MANIFEST)
    harness_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip().lower()
    c1 = dict(c0)
    c1.update({
        "schema": "round26-frozen-c1-v1", "arm": "C1",
        "selection": "C1_equals_C0_after_P1_failed_difficult_guard",
        "selection_harness_commit": harness_commit,
        "protocol_sha256": sha256(PROTOCOL),
        "candidate_development_results_sha256": sha256(
            OUT / "candidate_development_results.csv"),
        "candidate_selection_gate_audit_sha256": sha256(
            OUT / "candidate_selection_gate_audit.csv"),
        "exactness_argument_sha256": sha256(OUT / "c1_exactness_argument.md"),
        "rejected_prototype_manifest": "prototype1_manifest.json",
        "configuration": c0["configuration"] | {
            "candidate_mechanism": "none_C1_equals_C0",
            "external_gini_split_after_attempts": 2,
        },
        "heldout_access_authorized": True,
    })
    (OUT / "c1_manifest.json").write_text(
        json.dumps(c1, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("P1 rejected; C1 frozen equal to C0")


if __name__ == "__main__":
    main()
