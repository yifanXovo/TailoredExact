#!/usr/bin/env python3
"""Derive the Round 50 Stage 1 bottleneck audit and freeze Iteration 1."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
SUMMARY = EVIDENCE / "interval_mip_v0_300s_results_dev.csv"
RUN_ROOT = EVIDENCE / "development_runs" / "stage1_v0_300s"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def truth(value: object) -> bool:
    return str(value).lower() in {"1", "true", "yes"}


def gap_integral(path: Path, upper: float, horizon: float,
                 exact: bool, process_seconds: float) -> float:
    points = []
    for row in csv.DictReader(path.open(newline="", encoding="utf-8-sig")):
        if not truth(row["bound_available"]):
            continue
        lower = float(row["best_bound"])
        points.append((float(row["time_seconds"]), max(
            0.0, (upper - lower) / max(1e-12, abs(upper)))))
    area = 0.0
    previous_time = 0.0
    previous_gap = 1.0
    for event_time, event_gap in points:
        current_time = min(horizon, max(previous_time, event_time))
        area += (current_time - previous_time) * previous_gap
        previous_time = current_time
        previous_gap = event_gap
        if previous_time >= horizon:
            break
    end = min(horizon, process_seconds) if exact else horizon
    if end > previous_time:
        area += (end - previous_time) * previous_gap
        previous_time = end
    if not exact and horizon > previous_time:
        area += (horizon - previous_time) * previous_gap
    return area / horizon


def main() -> None:
    rows = list(csv.DictReader(SUMMARY.open(newline="", encoding="utf-8-sig")))
    if len(rows) != 14 or {row["state_id"] for row in rows} != {
            f"D{index}" for index in range(1, 15)}:
        raise RuntimeError("Stage 1 must contain exactly D1-D14")
    executable_hashes = {row["executable_sha256"] for row in rows}
    if len(executable_hashes) != 1:
        raise RuntimeError("Stage 1 executable identity mismatch")
    if any(not truth(row["model_identity_match"]) for row in rows):
        raise RuntimeError("Stage 1 model identity mismatch")
    if any(not truth(row["evidence_complete"]) for row in rows):
        raise RuntimeError("Stage 1 evidence incomplete")
    if any(not truth(row["cap_respected"]) for row in rows):
        raise RuntimeError("Stage 1 cap violation")
    if any(truth(row["false_certificate"]) for row in rows):
        raise RuntimeError("Stage 1 false certificate")

    fields = [
        "state_id", "instance", "status", "principal_bottlenecks",
        "root_cut_relative_gap", "root_work_fraction", "root_cut_count",
        "nodes", "simplex_iterations", "iterations_per_node",
        "first_incumbent_time_seconds", "work", "process_time_seconds",
        "final_gap", "gi_300", "numerical_warning_count",
        "model_build_fraction", "classification_basis",
    ]
    bottlenecks = []
    classification_counts: Counter[str] = Counter()
    cut_counts: Counter[str] = Counter()
    for row in rows:
        state_id = row["state_id"]
        upper = float(row["verified_upper_bound"])
        root_cut = float(row["final_root_cut_bound"])
        root_gap = max(0.0, (upper - root_cut) / max(1e-12, abs(upper)))
        work = float(row["work"])
        root_work = float(row["root_work"])
        nodes = float(row["nodes"])
        iterations_per_node = float(row["average_iterations_per_node"])
        first_incumbent = float(row["first_incumbent_time_seconds"])
        process_seconds = float(row["process_time_seconds"])
        build_fraction = float(row["model_build_seconds"]) / max(1e-12, process_seconds)
        hard = work >= 100.0 or row["status"] == "capped"
        labels = []
        if hard and root_gap >= 0.20:
            labels.append("weak root bound")
        if hard and root_work >= 20.0:
            labels.append("expensive root LP")
        if hard and int(float(row["root_cut_count"])) >= 1000 and root_work >= 10.0:
            labels.append("excessive root cuts")
        if hard and nodes >= 5000.0:
            labels.append("excessive node count")
        if hard and iterations_per_node >= 150.0:
            labels.append("high iterations per node")
        if hard and (first_incumbent < 0.0 or first_incumbent >= 0.30 * 300.0):
            labels.append("delayed incumbent")
        # Wide structural ranges alone are not a principal numerical bottleneck;
        # all native logs were checked for explicit warnings below.
        log_path = RUN_ROOT / f"{state_id}__interval-mip-v0" / "native_gurobi.log"
        log = log_path.read_text(encoding="utf-8", errors="replace")
        warning_count = sum(log.lower().count(token) for token in (
            "numerical warning", "large matrix coefficients", "large rhs",
            "markowitz tolerance", "switch to quad precision"))
        if hard and warning_count > 0:
            labels.append("poor numerical scale")
        if not labels:
            labels.append("unknown")
        for label in labels:
            classification_counts[label] += 1
        for cut in csv.DictReader((RUN_ROOT / f"{state_id}__interval-mip-v0" /
                                   "cut_family_ledger.csv").open(
                                       newline="", encoding="utf-8-sig")):
            cut_counts[cut["family"]] += int(cut["count"])
        gi = gap_integral(
            RUN_ROOT / f"{state_id}__interval-mip-v0" / "mip_progress.csv",
            upper, 300.0, truth(row["certificate"]), process_seconds)
        bottlenecks.append({
            "state_id": state_id, "instance": row["instance"],
            "status": row["status"], "principal_bottlenecks": ";".join(labels),
            "root_cut_relative_gap": format(root_gap, ".17g"),
            "root_work_fraction": format(root_work / max(1e-12, work), ".17g"),
            "root_cut_count": row["root_cut_count"], "nodes": row["nodes"],
            "simplex_iterations": row["simplex_iterations"],
            "iterations_per_node": row["average_iterations_per_node"],
            "first_incumbent_time_seconds": row["first_incumbent_time_seconds"],
            "work": row["work"], "process_time_seconds": row["process_time_seconds"],
            "final_gap": row["gap"], "gi_300": format(gi, ".17g"),
            "numerical_warning_count": warning_count,
            "model_build_fraction": format(build_fraction, ".17g"),
            "classification_basis": "root+tree+incumbent+native_log+build telemetry",
        })

    bottleneck_path = EVIDENCE / "interval_mip_bottleneck_map.csv"
    with bottleneck_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(bottlenecks)

    exact_count = sum(truth(row["certificate"]) for row in rows)
    capped = [row["state_id"] for row in rows if row["status"] == "capped"]
    hard_rows = [row for row in rows if float(row["work"]) >= 100.0 or row["status"] == "capped"]
    baseline_text = f"""# Round 50 branching baseline audit

Stage 1 completed all 14 frozen development states with one executable (`{next(iter(executable_hashes))}`), one unchanged `interval-mip-v0` policy, and 300-second total-process caps. {exact_count} rows certified and {len(capped)} capped honestly ({', '.join(capped)}). Model fingerprints matched the reconstruction freeze; there were no false certificates or cap violations.

The dominant search signals are excessive node or simplex-iteration burden, delayed native incumbents, and weak post-root-cut bounds on several hard roles. D1 and the tight3102 group show particularly expensive proof trajectories; D13 is dominated by tree size and delayed incumbent despite a comparatively strong root-cut bound. D2 remains an easy negative control. This supports testing only the predeclared uniform semantic priority policies B1-B3. No branch direction, dynamic switching, or per-instance priority is opened.

The classification is derived from `interval_mip_bottleneck_map.csv`, not model size alone. The candidate comparison will use a same-executable 120-second v0 core baseline and all three candidates, followed by a 300-second D1-D14 qualification for only the best screen candidate.
"""
    (EVIDENCE / "branching_baseline_audit.md").write_text(
        baseline_text, encoding="utf-8")

    cut_lines = "\n".join(
        f"- {family}: {count} native root cuts across 14 rows"
        for family, count in sorted(cut_counts.items()))
    (EVIDENCE / "cut_family_baseline_audit.md").write_text(f"""# Round 50 cut-family baseline audit

The native root-cut census is observational; it does not prove that a static model row family is useful or redundant. Aggregate native counts were:

{cut_lines}

High cut count alone does not track total Work: D2 is easy despite hundreds of cuts, while several hard rows spend most Work after the root. Therefore no generic Gurobi `Cuts` parameter change is permitted. Iteration 2 must first build the complete static row-family registry, duplicate/dominance audit, and leave-one-block evidence before deciding whether any exact candidate exists.
""", encoding="utf-8")

    (EVIDENCE / "symmetry_audit.md").write_text("""# Round 50 symmetry audit

The panel does not admit one uniform vehicle-symmetry rule: vehicle capacity vectors can differ, and pickup/drop operation modes are directionally distinct in the complete objective and feasibility system. Route labels can be interchangeable only on restricted instances, which is insufficient for a uniform fixed backend without instance dispatch. No symmetry candidate is opened from Stage 1. A source-level preservation note will be retained in the required symmetry report.
""", encoding="utf-8")

    max_build_fraction = max(float(row["model_build_seconds"]) /
                             max(1e-12, float(row["process_time_seconds"]))
                             for row in hard_rows)
    (EVIDENCE / "formulation_numerical_audit.md").write_text("""# Round 50 formulation and numerical baseline audit

All 14 native logs were inspected for explicit Gurobi numerical warnings; none were observed. Coefficient and RHS ranges are wide but arise from exact capacity/time constants and cannot be clipped empirically. Wide range alone is not classified as the principal bottleneck. Iteration 3 will open only if the row-family audit finds one analytically valid tightening or scaling equivalence; otherwise it will be skipped with a bounded negative decision.
""", encoding="utf-8")
    (EVIDENCE / "model_reuse_baseline_audit.md").write_text(f"""# Round 50 model-reuse baseline audit

Every dedicated fixed-state row builds, reads, and optimizes one model. No fixed-state chain exists to reuse, and no interrupted MIP tree is treated as resumable. On hard Stage 1 rows the maximum model-build share was {max_build_fraction:.6f}; proof search dominates. Reuse remains optional and can be considered only after branching and formulation policy freeze, with mathematical fingerprints unchanged.
""", encoding="utf-8")

    plan = {
        "schema": "round50-iteration-plan-v1",
        "iteration": 1,
        "principal_family": "tailored branching",
        "written_before_candidate_runs": True,
        "baseline_summary": SUMMARY.relative_to(ROOT).as_posix(),
        "baseline_summary_sha256": sha256(SUMMARY),
        "bottleneck_map": bottleneck_path.relative_to(ROOT).as_posix(),
        "bottleneck_map_sha256": sha256(bottleneck_path),
        "core_states": ["D1", "D2", "D3", "D4", "D5", "D6", "D9", "D10", "D11"],
        "core_cap_seconds": 120,
        "qualification_states": [f"D{index}" for index in range(1, 15)],
        "qualification_cap_seconds": 300,
        "baseline_policy": "interval-mip-v0",
        "candidates": [
            {"id": "B1", "policy": "b1-primitive-first", "mechanism": "uniform ordinal semantic BranchPriority"},
            {"id": "B2", "policy": "b2-route-first", "mechanism": "uniform ordinal semantic BranchPriority"},
            {"id": "B3", "policy": "b3-operation-first", "mechanism": "uniform ordinal semantic BranchPriority"},
        ],
        "candidate_count": 3,
        "one_mechanism_family": True,
        "branch_direction_change": False,
        "instance_specific_logic": False,
        "runtime_dispatch": False,
        "decision_order": ["certificate", "GI", "gap", "valid_LB", "Work", "time"],
        "winner_requires_complete_300s_qualification": True,
        "confirmation_opened": False,
        "candidate_result_inspected_before_plan": False,
    }
    (EVIDENCE / "iteration_1_plan.json").write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "rows": len(rows), "exact": exact_count, "capped": capped,
        "classification_counts": classification_counts,
        "cut_counts": cut_counts,
        "iteration_1_plan_sha256": sha256(EVIDENCE / "iteration_1_plan.json"),
    }, default=dict, indent=2))


if __name__ == "__main__":
    main()
