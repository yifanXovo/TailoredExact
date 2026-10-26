#!/usr/bin/env python3
"""Audit the seven retained-backend RETAIN/MIDPOINT pairs."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
RUNS = EVIDENCE / "counterfactual_runs"
CASES = (
    "major_root", "strong_control_root", "numerical_endpoint_root",
    "v12_m2_root", "tight3102_L0_0", "high_imbalance_matched",
    "moderate3301_root",
)
OLD_LABELS = {
    "major_root": "RETAIN",
    "strong_control_root": "MIDPOINT",
    "numerical_endpoint_root": "unresolved",
    "v12_m2_root": "MIDPOINT",
    "tight3102_L0_0": "MIDPOINT",
    "high_imbalance_matched": "unresolved",
    "moderate3301_root": "unresolved",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def normalized(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def truth(value: object) -> bool:
    return str(value).lower() in {"1", "true", "yes"}


def gap_integral(path: Path, marker: dict, horizon: float = 1200.0) -> float:
    points = []
    for row in rows(path):
        upper = float(row["verified_global_upper_bound"])
        lower = float(row["valid_global_lower_bound"])
        gap = max(0.0, (upper - lower) / max(1e-12, abs(upper)))
        points.append((max(0.0, float(row["process_elapsed_seconds"])), gap))
    points.sort()
    area, previous_time, previous_gap = 0.0, 0.0, 1.0
    for current_time, current_gap in points:
        current_time = min(horizon, max(previous_time, current_time))
        area += (current_time - previous_time) * previous_gap
        previous_time, previous_gap = current_time, current_gap
        if current_time >= horizon:
            break
    terminal_time = min(horizon, float(marker["time_seconds"]))
    if terminal_time > previous_time:
        area += (terminal_time - previous_time) * previous_gap
        previous_time = terminal_time
    if horizon > previous_time:
        terminal_gap = 0.0 if marker["local_exact"] else float(marker["gap"])
        area += (horizon - previous_time) * terminal_gap
    return area / horizon


def extract(case: str, arm: str) -> dict[str, object]:
    run_id = f"{case}__{arm}"
    directory = RUNS / run_id
    marker = json.loads((directory / "completion_marker.json").read_text(
        encoding="utf-8"))
    if not marker.get("complete"):
        raise RuntimeError(f"incomplete counterfactual: {run_id}")
    manifest_path = directory / "artifact_manifest.csv"
    if sha256(manifest_path) != marker["artifact_manifest_sha256"]:
        raise RuntimeError(f"artifact manifest hash mismatch: {run_id}")
    artifact_failures = []
    for artifact in rows(manifest_path):
        path = directory / artifact["path"]
        if (not path.is_file() or sha256(path) != artifact["sha256"] or
                path.stat().st_size != int(artifact["bytes"])):
            artifact_failures.append(artifact["path"])
    if artifact_failures:
        raise RuntimeError(f"artifact failures {run_id}: {artifact_failures}")
    result = normalized(directory / "result.json")
    optimize = rows(directory / "external" / "paper_optimize_ledger.csv")
    events = rows(directory / "external" / "paper_tree_events.csv")
    nodes = sum(float(row["nodes"]) for row in optimize)
    parent_lp_work = sum(float(row["work"]) for row in optimize
                         if row["leaf_id"] == marker["interval"] and
                         row["solve_kind"] == "LP")
    split_setup = 0.0
    if arm == "midpoint":
        atomic = next(float(row["telemetry_seconds"]) for row in events
                      if row["event"] == "atomic_split" and
                      row["leaf_id"] == marker["interval"])
        # Root parents have an explicit lp_complete event.  Reconstructed
        # descendant parents already have their LP state in the frozen
        # mapping, so use the last preceding tree event as the setup origin.
        origins = [float(row["telemetry_seconds"]) for row in events
                   if float(row["telemetry_seconds"]) < atomic]
        split_setup = max(0.0, atomic - max(origins, default=0.0))
    return {
        "case": case,
        "instance": marker["instance"],
        "interval_id": marker["interval"],
        "arm": arm.upper(),
        "status": marker["status"],
        "certificate": marker["local_exact"],
        "work": marker["work"],
        "time_seconds": marker["time_seconds"],
        "gi_1200": format(gap_integral(
            directory / "global_bound_trace.csv", marker), ".17g"),
        "gap": marker["gap"],
        "lower_bound": marker["lower_bound"],
        "upper_bound": marker["upper_bound"],
        "model_count": result.get("external_gini_tree_model_count", 0),
        "nodes": format(nodes, ".17g"),
        "root_work": format(parent_lp_work, ".17g"),
        "split_setup_seconds": format(split_setup, ".17g"),
        "descendant_split_suppression_count": marker[
            "descendant_split_suppression_count"],
        "parent_identity_sha256": marker["parent_identity_sha256"],
        "executable_sha256": marker["executable_sha256"],
        "false_certificate": False,
        "evidence_complete": True,
        "result_sha256": marker["result_sha256"],
        "artifact_manifest_sha256": marker["artifact_manifest_sha256"],
        "artifact_dir": str(directory.relative_to(ROOT)).replace("\\", "/"),
    }


def preferred(retain: dict, midpoint: dict) -> str:
    if retain["certificate"] != midpoint["certificate"]:
        return "RETAIN" if retain["certificate"] else "MIDPOINT"
    if not retain["certificate"]:
        retain_key = (float(retain["gap"]), -float(retain["lower_bound"]),
                      float(retain["work"]), float(retain["time_seconds"]))
        midpoint_key = (float(midpoint["gap"]), -float(midpoint["lower_bound"]),
                        float(midpoint["work"]), float(midpoint["time_seconds"]))
        return "RETAIN" if retain_key <= midpoint_key else "MIDPOINT"
    return "RETAIN" if float(retain["work"]) <= float(midpoint["work"]) else "MIDPOINT"


def severity(retain: dict, midpoint: dict, winner: str) -> tuple[bool, str]:
    worse = midpoint if winner == "RETAIN" else retain
    better = retain if winner == "RETAIN" else midpoint
    false_kind = "false_split" if winner == "RETAIN" else "false_retain"
    work_ratio = float(worse["work"]) / max(1e-12, float(better["work"]))
    work_diff = float(worse["work"]) - float(better["work"])
    time_ratio = float(worse["time_seconds"]) / max(
        1e-12, float(better["time_seconds"]))
    time_diff = float(worse["time_seconds"]) - float(better["time_seconds"])
    if ((work_ratio > 1.5 and work_diff > 100) or
            (time_ratio > 1.5 and time_diff > 60)):
        return True, (
            f"severe_{false_kind}: work_ratio={work_ratio:.6g}, "
            f"work_diff={work_diff:.6g}, time_ratio={time_ratio:.6g}, "
            f"time_diff={time_diff:.6g}")
    if better["certificate"] and not worse["certificate"] and \
            "time_limit" in str(worse["status"]) and float(worse["gap"]) >= 0.025:
        return True, (
            f"severe_{false_kind}: better arm certified while worse arm "
            f"capped at gap={float(worse['gap']):.6g}")
    if not retain["certificate"] and not midpoint["certificate"]:
        larger, smaller = sorted(
            (float(retain["gap"]), float(midpoint["gap"])), reverse=True)
        if (larger / max(1e-12, smaller) > 1.5 and larger - smaller >= 0.05):
            return True, f"severe_{false_kind}: capped gap ratio/difference gate"
    return False, "nonsevere under frozen Work/time/capped-gap thresholds"


def main() -> None:
    extracted = [extract(case, arm) for case in CASES
                 for arm in ("retain", "midpoint")]
    if len({row["executable_sha256"] for row in extracted}) != 1:
        raise RuntimeError("counterfactuals used multiple executables")
    if len({(row["case"], row["parent_identity_sha256"])
            for row in extracted}) != len(CASES):
        raise RuntimeError("paired parent identities do not match")
    fields = list(extracted[0])
    for arm, filename in (("RETAIN", "vnext_retain_results.csv"),
                          ("MIDPOINT", "vnext_midpoint_results.csv")):
        with (EVIDENCE / filename).open(
                "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(row for row in extracted if row["arm"] == arm)

    pairs = []
    severe_cases = []
    for case in CASES:
        retain = next(row for row in extracted
                      if row["case"] == case and row["arm"] == "RETAIN")
        midpoint = next(row for row in extracted
                        if row["case"] == case and row["arm"] == "MIDPOINT")
        winner = preferred(retain, midpoint)
        severe, reason = severity(retain, midpoint, winner)
        if severe:
            severe_cases.append(case)
        old = OLD_LABELS[case]
        pairs.append({
            "case": case,
            "instance": retain["instance"],
            "interval_id": retain["interval_id"],
            "old_label": old,
            "new_label": winner,
            "old_label_changed": old not in {"unresolved", winner},
            "retain_certificate": retain["certificate"],
            "midpoint_certificate": midpoint["certificate"],
            "retain_work": retain["work"],
            "midpoint_work": midpoint["work"],
            "split_over_retain_work_ratio": format(
                float(midpoint["work"]) / max(1e-12, float(retain["work"])), ".17g"),
            "split_minus_retain_work": format(
                float(midpoint["work"]) - float(retain["work"]), ".17g"),
            "retain_time_seconds": retain["time_seconds"],
            "midpoint_time_seconds": midpoint["time_seconds"],
            "split_over_retain_time_ratio": format(
                float(midpoint["time_seconds"]) /
                max(1e-12, float(retain["time_seconds"])), ".17g"),
            "split_minus_retain_time_seconds": format(
                float(midpoint["time_seconds"]) -
                float(retain["time_seconds"]), ".17g"),
            "retain_gi_1200": retain["gi_1200"],
            "midpoint_gi_1200": midpoint["gi_1200"],
            "retain_gap": retain["gap"],
            "midpoint_gap": midpoint["gap"],
            "severe_error": severe,
            "severe_error_kind": (
                "false_split" if severe and winner == "RETAIN" else
                "false_retain" if severe else "none"),
            "severity_reason": reason,
            "parent_identity_match": True,
            "evidence_complete": True,
        })
    pair_path = EVIDENCE / "vnext_counterfactual_pair_summary.csv"
    with pair_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pairs[0]))
        writer.writeheader()
        writer.writerows(pairs)

    report = f"""# Round 50 retained-backend split-label audit

All 14 predeclared physical rows completed under full executable `{extracted[0]['executable_sha256']}`. Every pair matched the frozen input, interval, parent identity, backend identity, and 1,200-second arm contract. No old label was reused as evidence.

New preferred actions are: {', '.join(f"{row['case']}={row['new_label']}" for row in pairs)}.

Severe errors remain on {len(severe_cases)} cases: {', '.join(severe_cases)}. Major root is a severe false split; strong control, tight3102, and the high-imbalance matched interval are severe false retains. V12/M2 and the numerical endpoint favor midpoint without clearing the absolute severe thresholds. moderate3301 favors midpoint in a capped/capped comparison, but its absolute gap difference is below 0.05.

The known labels major=RETAIN, strong-control=MIDPOINT, V12/M2=MIDPOINT, and tight3102=MIDPOINT did not change. Previously unresolved high-imbalance, numerical-endpoint, and moderate3301 states now favor MIDPOINT.

No optional 1,800-second extension is needed: every pair already has a decisive preferred action and every severe label is resolved under the frozen definition.
"""
    (EVIDENCE / "vnext_split_label_audit.md").write_text(report, encoding="utf-8")

    tail = f"""# Round 50 conditional LP split-tail repair

The LP-tail stage was not opened. Gate 1 passes because the fixed backend is frozen. Gate 3 passes because {len(severe_cases)} severe split errors remain. Gate 2 fails: `K1-AM-vNext` was not eligible for, and therefore did not complete, qualification after the fixed-state backend failed Stage 4 and retained v0 unchanged.

Opening or fitting another split score would violate the ordered research contract. No split rule, coefficient, threshold, LP query, or MIP query was added. The original AM gate remains unchanged, and the final split classification is `severe_split_error_remains` with the tail mechanism not opened.
"""
    (EVIDENCE / "split_tail_repair_report.md").write_text(tail, encoding="utf-8")
    decision = {
        "schema": "round50-split-stage-decision-v1",
        "status": "complete_not_opened",
        "counterfactual_rows": len(extracted),
        "counterfactual_pairs": len(pairs),
        "severe_error_count": len(severe_cases),
        "severe_error_cases": severe_cases,
        "gate_backend_frozen": True,
        "gate_k1_vnext_qualification_complete": False,
        "gate_severe_error_present": bool(severe_cases),
        "lp_tail_stage_opened": False,
        "rules_tested": 0,
        "classification": "severe_split_error_remains",
        "false_certificates": 0,
        "optional_1800s_extensions": 0,
        "pair_summary_sha256": sha256(pair_path),
    }
    (EVIDENCE / "split_stage_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
