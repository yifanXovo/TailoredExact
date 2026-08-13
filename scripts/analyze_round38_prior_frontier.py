#!/usr/bin/env python3
"""Read-only global-frontier forensics over official Round 37 G1 runs."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
R37 = ROOT / "results" / "gf_gini_geometry_mechanism_round37"
OUT = ROOT / "results" / "gf_global_frontier_lift_round38"
TOLERANCE = 1e-7
STAGES = (
    ("exploratory_smoke", R37 / "smoke_runs"),
    ("focused_diagnostic", R37 / "diagnostic_runs"),
    ("selected_confirmation", R37 / "confirmation_runs"),
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value[0] if isinstance(value, list) else value


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def finite(value: str) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def write_csv(path: Path, material: list[dict[str, Any]]) -> None:
    if not material:
        raise ValueError("no prior G1 runs found")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(material[0]))
        writer.writeheader()
        writer.writerows(material)


def analyze(stage: str, run_dir: Path) -> dict[str, Any] | None:
    result = load_json(run_dir / "result.json")
    if not result.get("round37_pilot_prefinement_performed", False):
        return None
    external = run_dir / "external"
    lp = rows(external / "lp_status_ledger.csv")
    parent_child = rows(external / "parent_child_bound_ledger.csv")
    trace = rows(external / "global_bound_trace.csv")
    targets = rows(external / "native_target_ledger.csv")
    events = rows(external / "paper_tree_events.csv")
    parent_id = str(result["round37_pilot_weakest_leaf_id"])
    initial = []
    for row in lp:
        if row["parent_id"] or int(row["depth"]) != 0:
            continue
        bound = finite(row["lower_bound"])
        if (row["optimal"] == "1" and row["bound_available"] == "1" and
                bound is not None):
            initial.append((row["leaf_id"], bound))
    if not initial:
        raise ValueError(f"no complete initial bounds: {run_dir}")
    initial.sort(key=lambda item: (item[1], item[0]))
    selected = next(value for leaf, value in initial if leaf == parent_id)
    others = [value for leaf, value in initial if leaf != parent_id]
    next_strict_values = [
        value for _, value in initial if value > selected + TOLERANCE
    ]
    next_strict = min(next_strict_values) if next_strict_values else None
    plateau = sum(abs(value - selected) <= TOLERANCE for _, value in initial)
    split_row = next(
        row for row in parent_child
        if row["parent_id"] == parent_id and
        row["decision"] == "round37_pilot_weakest_midpoint_prefinement"
    )
    child_bounds = [
        float(split_row["left_lp_bound"]),
        float(split_row["right_lp_bound"]),
    ]
    b_plus = min(child_bounds)
    global_before = min(value for _, value in initial)
    global_after = min([b_plus, *others])
    completion = (
        next_strict is not None and b_plus + TOLERANCE >= next_strict
    )
    hypothetical = sorted([*others, *child_bounds])

    split_index = next(
        index for index, row in enumerate(trace)
        if row["event_type"] == "split" and row["event_source"] ==
        "round37_pilot_weakest_midpoint_prefinement"
    )
    split_time = float(trace[split_index]["exact_phase_elapsed_seconds"])
    descendant_prefix = parent_id + "."
    post = trace[split_index + 1:]
    controlling_descendant_events = 0
    first_other_time: float | None = None
    first_other_leaf = ""
    for row in post:
        active = row["active_leaf"]
        active_bound = finite(row["active_leaf_valid_lower_bound"])
        other_bound = finite(row["other_open_leaf_min_valid_lower_bound"])
        if not active or active_bound is None:
            continue
        controls = other_bound is None or active_bound <= other_bound + TOLERANCE
        if not controls:
            continue
        if active.startswith(descendant_prefix):
            controlling_descendant_events += 1
        elif first_other_time is None:
            first_other_time = float(row["exact_phase_elapsed_seconds"])
            first_other_leaf = active
            break
    persistence = (
        first_other_time - split_time if first_other_time is not None else None
    )
    descendant_targets = [
        row for row in targets if row["leaf_id"].startswith(descendant_prefix)
    ]
    descendant_requeues = sum(
        row["requeued"] == "1" for row in descendant_targets
    )
    descendant_terminal_events = sum(
        row["leaf_id"].startswith(descendant_prefix) and
        row["event"] in {"terminal_mip_complete", "terminal_mip_bound_improvement"}
        for row in events
    )
    final_bound = float(result["external_gini_tree_global_lower_bound"])
    verified_ub = float(result["external_gini_tree_verified_upper_bound"])
    gap = max(0.0, verified_ub - final_bound) / max(abs(verified_ub), 1e-12)
    return {
        "stage": stage,
        "run_id": run_dir.name,
        "instance_id": result.get("instance", run_dir.name),
        "process_cap_seconds": load_json(run_dir / "command.json")[
            "process_cap_seconds"
        ],
        "selected_leaf": parent_id,
        "complete_open_initial_count": len(initial),
        "initial_sorted_bound_vector": ";".join(
            f"{leaf}:{value:.17g}" for leaf, value in initial
        ),
        "initial_global_lb": f"{global_before:.17g}",
        "frontier_plateau_size": plateau,
        "next_strict_frontier_available": next_strict is not None,
        "next_strict_frontier": (
            f"{next_strict:.17g}" if next_strict is not None else ""
        ),
        "b_plus": f"{b_plus:.17g}",
        "delta_local": f"{b_plus - selected:.17g}",
        "L_i_plus": f"{global_after:.17g}",
        "delta_global": f"{global_after - global_before:.17g}",
        "frontier_completion": (
            f"{min(b_plus, next_strict) - selected:.17g}"
            if next_strict is not None else ""
        ),
        "completes_next_strict_frontier": completion,
        "hypothetical_sorted_post_vector": ";".join(
            f"{value:.17g}" for value in hypothetical
        ),
        "immediate_other_bottleneck": (
            next_strict is not None and b_plus > next_strict + TOLERANCE
        ),
        "refined_descendant_controlling_event_count_before_displacement":
            controlling_descendant_events,
        "first_other_controlling_leaf": first_other_leaf,
        "exact_seconds_until_other_controls": (
            f"{persistence:.17g}" if persistence is not None else ""
        ),
        "descendant_target_event_count": len(descendant_targets),
        "descendant_requeue_count": descendant_requeues,
        "descendant_terminal_event_count": descendant_terminal_events,
        "final_valid_lb": f"{final_bound:.17g}",
        "verified_ub": f"{verified_ub:.17g}",
        "final_verified_ub_gap": f"{gap:.17g}",
        "strict_certificate": bool(
            result.get("strict_certified_original_problem", False)
        ),
    }


def main() -> int:
    material: list[dict[str, Any]] = []
    for stage, directory in STAGES:
        for result_path in sorted(directory.glob("*__g1/result.json")):
            record = analyze(stage, result_path.parent)
            if record is not None:
                material.append(record)
    write_csv(OUT / "prior_round37_frontier_forensics.csv", material)
    completion_count = sum(
        bool(row["completes_next_strict_frontier"]) for row in material
    )
    unique_geometry: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in material:
        key = (
            str(row["selected_leaf"]),
            str(row["initial_sorted_bound_vector"]),
            str(row["b_plus"]),
        )
        unique_geometry.setdefault(key, row)
    summary = {
        "schema": "round38-prior-frontier-forensics-v1",
        "official_exposed_run_count": len(material),
        "unique_initial_geometry_count": len(unique_geometry),
        "next_frontier_completion_run_count": completion_count,
        "all_exposed_runs_have_strict_next_frontier": all(
            bool(row["next_strict_frontier_available"]) for row in material
        ),
        "tolerance": TOLERANCE,
        "decision": (
            "G2-A would suppress every observed Round 37 G1 exposure"
            if completion_count == 0 else
            "G2-A has at least one historical exposure"
        ),
    }
    (OUT / "prior_round37_frontier_forensics.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lines = [
        "# Prior Round 37 global-frontier forensics",
        "",
        f"Official exposed G1 runs: **{len(material)}**.",
        f"Unique initial geometries: **{len(unique_geometry)}**.",
        "Next-strict-frontier completions: "
        f"**{completion_count}/{len(material)}**.",
        "",
        summary["decision"] + ".",
        "",
        "This is read-only retrospective mechanism analysis. It does not make",
        "a Round 38 candidate decision from instance labels or outcomes.",
    ]
    (OUT / "prior_round37_frontier_forensics.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
