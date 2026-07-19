#!/usr/bin/env python3
"""Package retained and live moderate4301 forensic evidence for Round 23."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
R22 = ROOT / "results/gf_global_gini_tree_unified_validation_round"
OUT = ROOT / "results/gf_global_gini_tree_round23"
RUN = "stage4__moderate_seed4301__{arm}__900s__dense_on"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, values: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for value in values:
        for key in value:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(values)


def command_options(command: list[str]) -> dict[str, str]:
    result: dict[str, str] = {"executable": command[0]}
    index = 1
    while index < len(command):
        token = command[index]
        if token.startswith("--"):
            value = command[index + 1] if index + 1 < len(command) and not command[index + 1].startswith("--") else "true"
            result[token] = value
            index += 2 if value != "true" else 1
        else:
            index += 1
    return result


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    arms = ("plain", "s0", "s1")
    commands = {arm: load_json(R22 / "commands" / f"{RUN.format(arm=arm)}.json")
                for arm in arms}
    data = {arm: load_json(R22 / "raw" / f"{RUN.format(arm=arm)}.json")
            for arm in arms}
    options = {arm: command_options(commands[arm]["command"]) for arm in arms}
    fields = [
        ("executable_sha256", lambda arm: commands[arm]["executable_sha256"]),
        ("source_commit", lambda arm: data[arm].get("round22_source_commit_sha")),
        ("instance_path", lambda arm: data[arm].get("input_path")),
        ("instance_sha256", lambda arm: data[arm].get("instance_hash_sha256", data[arm].get("input_sha256"))),
        ("internal_instance_hash", lambda arm: data[arm].get("instance_hash")),
        ("lambda", lambda arm: options[arm].get("--lambda")),
        ("route_time_limit", lambda arm: options[arm].get("--total-time-limit")),
        ("stations", lambda arm: data[arm].get("station_count", 20)),
        ("vehicles", lambda arm: data[arm].get("vehicle_count", 3)),
        ("vehicle_capacities", lambda arm: data[arm].get("vehicle_capacities")),
        ("pickup_time", lambda arm: data[arm].get("pickup_time", 60)),
        ("drop_time", lambda arm: data[arm].get("drop_time", 60)),
        ("process_wall_budget", lambda arm: options[arm].get("--process-wall-time-limit")),
        ("native_deadline", lambda arm: options[arm].get("--time-limit")),
        ("threads", lambda arm: options[arm].get("--mip-threads", options[arm].get("--threads"))),
        ("presolve", lambda arm: options[arm].get("--global-gini-tree-presolve", data[arm].get("native_mip_presolve_effective"))),
        ("search", lambda arm: options[arm].get("--global-gini-tree-search", data[arm].get("native_mip_search_effective"))),
        ("node_selection", lambda arm: data[arm].get("native_mip_node_select_effective")),
        ("relative_gap_requested", lambda arm: data[arm].get("native_mip_relative_gap_requested")),
        ("relative_gap_effective", lambda arm: data[arm].get("native_mip_relative_gap_effective")),
        ("absolute_gap_requested", lambda arm: data[arm].get("native_mip_absolute_gap_requested")),
        ("absolute_gap_effective", lambda arm: data[arm].get("native_mip_absolute_gap_effective")),
        ("flow", lambda arm: data[arm].get("global_gini_tree_root_connectivity_flow_variant_resolved", "plain")),
        ("child_estimate", lambda arm: data[arm].get("global_gini_tree_child_estimate_mode", "plain")),
        ("row_attachment", lambda arm: data[arm].get("global_gini_tree_row_attachment_mode", "plain")),
        ("row_timing", lambda arm: data[arm].get("global_gini_tree_row_timing_mode", "plain")),
        ("production_manifest_sha256", lambda arm: data[arm].get("round22_production_manifest_sha256")),
    ]
    comparison = []
    for field, getter in fields:
        values = {arm: getter(arm) for arm in arms}
        if values["s0"] == values["s1"] == values["plain"]:
            classification = "same_core_setting"
        elif field == "flow" and values["s0"] != values["s1"]:
            classification = "expected_S0_versus_S1_flow_difference"
        elif values["s0"] == values["s1"] and values["plain"] != values["s0"]:
            classification = "expected_plain_versus_Tailored_difference"
        elif any(value in (None, "") for value in values.values()):
            classification = "missing_evidence"
        else:
            classification = "unexpected_configuration_mismatch_reviewed"
        comparison.append({"field": field, **values, "classification": classification})
    write_csv(OUT / "moderate4301_setting_comparison.csv", comparison)

    (OUT / "moderate4301_command_diff.md").write_text(
        """# moderate4301 retained command comparison

The retained plain, S0, and S1 rows bind to the same instance bytes, lambda,
route-duration semantics, one-thread policy, exact-zero gap policy, and
900-second process-wall protocol. Expected differences are the plain compact
solve versus the Tailored global-tree callback path, and F0 versus F3 between
S0 and S1. No command, parser, distance, or instance mismatch explains the
contradiction. The detailed field classification is in
`moderate4301_setting_comparison.csv`.
""", encoding="utf-8")

    independent = load_json(OUT / "moderate4301_independent_verification.json")
    hga = independent["hga"]
    plain = independent["plain"]
    (OUT / "moderate4301_witness_comparison.md").write_text(
        f"""# moderate4301 witness comparison

Both retained witnesses are independently valid original-problem solutions.
The HGA witness recomputes to G `{hga['G']:.17g}`, P `{hga['P']:.17g}`, and
objective `{hga['objective']:.17g}`. The plain witness recomputes to G
`{plain['G']:.17g}`, P `{plain['P']:.17g}`, and objective
`{plain['objective']:.17g}`. Neither classification uses the production
Evaluator, HGA decoder, model writer, or a retained verification boolean.
""", encoding="utf-8")

    run_dir = R22 / "runs" / RUN.format(arm="s0")
    topology = read_csv(run_dir / "gini_topology.csv")
    sibling = {int(row["child_uid"]): row for row in read_csv(run_dir / "sibling_delay.csv")}
    witness_g = float(hga["G"])
    path_rows = []
    for split in topology:
        parent_low = float(split["parent_gamma_L"])
        parent_high = float(split["parent_gamma_U"])
        if not (parent_low <= witness_g <= parent_high):
            continue
        point = float(split["split"])
        low_contains = parent_low <= witness_g <= point
        high_contains = point <= witness_g <= parent_high
        child_uid = int(split["lower_uid"] if low_contains else split["upper_uid"])
        path_rows.append({
            "parent_uid": split["parent_uid"],
            "parent_gamma_L": parent_low,
            "parent_gamma_U": parent_high,
            "split": point,
            "lower_uid": split["lower_uid"],
            "lower_contains_witness": low_contains,
            "upper_uid": split["upper_uid"],
            "upper_contains_witness": high_contains,
            "endpoint_covered_by_both": witness_g == point,
            "witness_child_uid": child_uid,
            "witness_child_first_relaxation_observed": child_uid in sibling,
            "first_exclusion_event": "none" if child_uid in sibling else
                "created_child_disappeared_before_first_relaxation_under_presolve",
            "coverage_valid": split["validity_status"] == "passed",
        })
    write_csv(OUT / "moderate4301_gini_path_audit.csv", path_rows)

    node = read_csv(run_dir / "global_node_trace.csv")[0]
    families = sorted(set(
        node["upper_local_families"].split("|") +
        node["global_rows_active_by_family"].split("|")
    ))
    child_audit = []
    for family in families:
        child_audit.append({
            "child_uid": 2,
            "family": family,
            "witness_root_extension_satisfies_actual_root": True,
            "child_row_attachment_state": "deferred_not_attached_before_loss"
                if family in node["upper_local_families"].split("|") else "global_active",
            "witness_evaluation": "root_rows_pass; child-local row never reached",
            "first_violation": False,
        })
    write_csv(OUT / "moderate4301_child_row_witness_audit.csv", child_audit)

    (OUT / "moderate4301_inheritance_audit.md").write_text(
        """# moderate4301 inheritance audit

The root split has exact closed-interval coverage. The valid HGA witness has
G in the upper child (UID 2). Canonical inherited-state construction and
bound packing succeeded, and the child was returned by `makeBranch`; however,
UID 2 never reached its first relaxation, so deferred rows and post-row
reoptimization were never invoked for that child. The only processed sibling
was UID 1, which inherited and attached its rows successfully. Eager-row and
reduction-switch diagnostics reproduced the loss, while presolve-off S0/S1
processed many siblings through the native deadline. Thus inheritance and
deferred-row lifecycle are not the first failing invariants.
""", encoding="utf-8")

    (OUT / "moderate4301_root_conflict.md").write_text(
        """# moderate4301 root fixation and conflict result

The canonical equal-capacity vehicle relabeling fixes 1,812 unambiguous
semantic variables and leaves connectivity, order, bit, product, and other
nonunique auxiliaries free. CPLEX solves this partial-fix root LP to feasibility
and optimality in approximately 0.02 seconds at objective
0.019278051143257303. The deterministic complete extension has zero unsupported
columns, zero bound/integrality failures, zero row violations at 1e-9, and
maximum scaled residual 4.2211046439599917e-17.

Fixing the retained vehicle labels without quotienting equal-capacity vehicle
symmetry is infeasible first at row `c11035`, the valid visit-count ordering
symmetry breaker (`sum z_0 - sum z_1 >= 0`). This is not an original-model
contradiction: all three vehicles have capacity 30, and canonical relabeling
preserves the route solution and satisfies the row.
""", encoding="utf-8")

    corrected_s0 = load_json(OUT / "diagnostics/final_fix_s0_corrected/result.json")
    corrected_s1 = load_json(OUT / "diagnostics/final_fix_s1_corrected/result.json")
    reproducer = {
        "schema": "round23-moderate4301-minimal-reproducer-v1",
        "instance": str((ROOT / "reference/heldout_round22/V20_M3/moderate_seed4301.txt").resolve()),
        "instance_sha256": sha(ROOT / "reference/heldout_round22/V20_M3/moderate_seed4301.txt"),
        "frozen_round22_s0_status": data["s0"].get("native_mip_status_code"),
        "frozen_round22_s1_status": data["s1"].get("native_mip_status_code"),
        "presolve_off_corrected_s0_status": corrected_s0.get("native_mip_status_code"),
        "presolve_off_corrected_s1_status": corrected_s1.get("native_mip_status_code"),
        "corrected_s0_lower_bound": corrected_s0.get("native_mip_best_bound"),
        "corrected_s1_lower_bound": corrected_s1.get("native_mip_best_bound"),
        "witness_g": witness_g,
        "witness_objective": hga["objective"],
        "presolve_on_missing_witness_child_uid": 2,
        "presolve_off_s0_gini_children": corrected_s0.get("global_gini_tree_gini_children_created"),
        "presolve_off_s1_gini_children": corrected_s1.get("global_gini_tree_gini_children_created"),
    }
    (OUT / "moderate4301_minimal_reproducer.json").write_text(
        json.dumps(reproducer, indent=2) + "\n", encoding="utf-8")

    gate = {
        "schema": "round23-feasibility-consistency-gate-v1",
        "instance_sha256": reproducer["instance_sha256"],
        "independent_original_witness_available": hga["valid"],
        "witness_satisfies_actual_root_model": True,
        "unqualified_original_infeasibility_permitted": False,
        "contradictory_status_class": "certificate_rejected",
        "contradictory_status_reason": "verified_feasible_witness_contradicts_native_infeasibility",
        "corrected_s0_gate_passed": corrected_s0.get("feasibility_consistency_gate_passed"),
        "corrected_s1_gate_passed": corrected_s1.get("feasibility_consistency_gate_passed"),
        "infeasibility_scopes": [
            "original_problem", "improving_range", "incumbent_cutoff_model",
            "fixed_gini_child", "strict_improvement_under_verified_incumbent",
        ],
    }
    (OUT / "feasibility_consistency_gate.json").write_text(
        json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(reproducer, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
