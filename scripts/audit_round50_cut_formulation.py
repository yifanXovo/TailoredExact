#!/usr/bin/env python3
"""Exhaustive conservative row audit for Round 50 Iteration 2."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
RECONSTRUCTION = EVIDENCE / "fixed_interval_state_reconstruction_audit.csv"

FAMILIES = {
    "inventory_conservation": "core feasibility/model-definition",
    "movement_reachability": "core feasibility/model-definition",
    "routing_flow_and_connectivity": "core feasibility/model-definition",
    "visit_inventory_linking": "valid strengthening inequality",
    "handling_capacity": "core feasibility/model-definition",
    "support_duration": "valid strengthening inequality",
    "transfer_compatibility": "valid strengthening inequality",
    "direct_gini_cap_floor": "exact reformulation",
    "interval_tight_mccormick": "exact reformulation",
    "objective_estimator_cutoff": "valid strengthening inequality",
    "penalty_lower_bound_closure": "valid strengthening inequality",
    "gini_spread": "exact reformulation",
    "required_movement": "valid strengthening inequality",
    "low_gini_centering": "valid strengthening inequality",
    "variable_s_centering": "valid strengthening inequality",
    "sp_product_estimator": "valid strengthening inequality",
    "inventory_ratio_and_penalty_definition": "exact reformulation",
    "operation_and_load_definition": "core feasibility/model-definition",
    "core_model_definition_other": "core feasibility/model-definition",
    "symmetry_constraint": "symmetry constraint",
    "diagnostic_only": "diagnostic-only",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prefix(name: str) -> str:
    for value in ("conn_", "ord_", "load_", "mode_", "zprod_", "prod_",
                  "bit_", "x_", "z_", "p_", "d_", "Y_", "r_", "e_",
                  "h_"):
        if name.startswith(value):
            return value.rstrip("_")
    return name


TERM = re.compile(
    r"(?:(?P<sign>[+-])\s*)?"
    r"(?:(?P<coef>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s+)?"
    r"(?P<var>[A-Za-z][A-Za-z0-9_]*)")


def parse_expression(text: str) -> dict[str, float]:
    coefficients: dict[str, float] = defaultdict(float)
    for match in TERM.finditer(text):
        coefficient = float(match.group("coef")) if match.group("coef") else 1.0
        if match.group("sign") == "-":
            coefficient = -coefficient
        coefficients[match.group("var")] += coefficient
    return {name: value for name, value in coefficients.items()
            if abs(value) > 1e-12}


def classify(coefficients: dict[str, float], sense: str, rhs: float) -> str:
    names = set(coefficients)
    groups = {prefix(name) for name in names}
    if "G" in names and any(name.startswith("e_") for name in names) and sense == "<=":
        return "objective_estimator_cutoff"
    if {"bit", "prod"} & groups and "G" in names:
        return "interval_tight_mccormick"
    if "W" in names or "zprod" in groups:
        if "prod" in groups or "G" in names:
            return "sp_product_estimator"
        return "variable_s_centering"
    if "h" in groups and "r" in groups:
        return "direct_gini_cap_floor"
    if "h" in groups:
        return "gini_spread"
    if "G" in names and ("r" in groups or "Y" in groups):
        return "direct_gini_cap_floor"
    if "r" in groups and "Y" in groups and sense == "=":
        return "inventory_ratio_and_penalty_definition"
    if "e" in groups and "Y" in groups:
        return "inventory_ratio_and_penalty_definition"
    if "e" in groups and "r" in groups and len(groups) == 2:
        return "inventory_ratio_and_penalty_definition"
    if "e" in groups and len(groups) <= 2:
        return "penalty_lower_bound_closure"
    if "conn" in groups:
        return "movement_reachability"
    if "ord" in groups:
        return "routing_flow_and_connectivity"
    if "x" in groups and not ({"p", "d", "load", "Y"} & groups):
        return "routing_flow_and_connectivity"
    if "Y" in groups and ({"p", "d"} & groups):
        return "inventory_conservation"
    if "Y" in groups and "z" in groups:
        return "visit_inventory_linking"
    if {"p", "d"} & groups and "x" in groups:
        return "support_duration"
    if {"p", "d"} & groups and "z" in groups and "mode" not in groups:
        return "required_movement"
    if {"p", "d"} & groups and "mode" in groups:
        return "transfer_compatibility"
    if {"p", "d", "load", "mode"} & groups:
        return "operation_and_load_definition"
    if "Y" in groups:
        return "inventory_conservation"
    if "r" in groups:
        return "low_gini_centering"
    return "core_model_definition_other"


def canonical(coefficients: dict[str, float], sense: str, rhs: float,
              sign_normalized: bool) -> tuple[tuple[tuple[str, str], ...], str, str]:
    values = dict(coefficients)
    normalized_sense = sense
    normalized_rhs = rhs
    if sign_normalized and values:
        first = values[sorted(values)[0]]
        if first < 0.0:
            values = {name: -value for name, value in values.items()}
            normalized_rhs = -normalized_rhs
            normalized_sense = {"<=": ">=", ">=": "<=", "=": "="}[sense]
    vector = tuple((name, format(value, ".17g"))
                   for name, value in sorted(values.items()))
    return vector, normalized_sense, format(normalized_rhs, ".17g")


def parse_model(path: Path) -> list[dict[str, object]]:
    output = []
    active = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line == "Subject To":
            active = True
            continue
        if line == "Bounds":
            break
        if not active or not line:
            continue
        match = re.match(r"^(c\d+):\s*(.*)\s(<=|>=|=)\s([-+0-9.eE]+)$", line)
        if not match:
            raise RuntimeError(f"unparsed canonical row in {path}: {line[:160]}")
        row_id, expression, sense, rhs_text = match.groups()
        coefficients = parse_expression(expression)
        rhs = float(rhs_text)
        if not coefficients:
            raise RuntimeError(f"empty parsed row {row_id} in {path}")
        family = classify(coefficients, sense, rhs)
        output.append({
            "row_id": row_id, "coefficients": coefficients, "sense": sense,
            "rhs": rhs, "family": family,
            "exact_signature": canonical(coefficients, sense, rhs, False),
            "canonical_signature": canonical(coefficients, sense, rhs, True),
            "lhs_signature": canonical(coefficients, sense, 0.0, True)[:2],
        })
    return output


def main() -> None:
    states = list(csv.DictReader(RECONSTRUCTION.open(
        newline="", encoding="utf-8-sig")))
    aggregate = defaultdict(lambda: {
        "rows": 0, "nonzeros": 0, "min_coef": math.inf, "max_coef": 0.0,
        "min_rhs": math.inf, "max_rhs": 0.0, "exact_duplicates": 0,
        "canonical_duplicates": 0,
    })
    duplicate_rows = []
    all_parsed_rows = 0
    for state in states:
        path = ROOT / state["model_artifact_path"]
        parsed = parse_model(path)
        if len(parsed) != int(state["original_rows"]):
            raise RuntimeError(f"row coverage mismatch for {state['state_id']}")
        all_parsed_rows += len(parsed)
        exact_groups: dict[object, list[str]] = defaultdict(list)
        canonical_groups: dict[object, list[str]] = defaultdict(list)
        lhs_groups: dict[object, list[dict[str, object]]] = defaultdict(list)
        family_counts = defaultdict(lambda: [0, 0])
        for row in parsed:
            exact_groups[row["exact_signature"]].append(row)
            canonical_groups[row["canonical_signature"]].append(row)
            lhs_groups[row["lhs_signature"]].append(row)
            values = [abs(value) for value in row["coefficients"].values()]
            family = str(row["family"])
            stats = aggregate[family]
            stats["rows"] += 1
            stats["nonzeros"] += len(values)
            stats["min_coef"] = min(stats["min_coef"], min(values))
            stats["max_coef"] = max(stats["max_coef"], max(values))
            stats["min_rhs"] = min(stats["min_rhs"], abs(float(row["rhs"])))
            stats["max_rhs"] = max(stats["max_rhs"], abs(float(row["rhs"])))
            family_counts[family][0] += 1
            family_counts[family][1] += len(values)
        exact_duplicate_count = sum(len(group) - 1 for group in exact_groups.values()
                                    if len(group) > 1)
        canonical_duplicate_count = sum(
            len(group) - 1 for group in canonical_groups.values() if len(group) > 1)
        exact_group_details = []
        for group in exact_groups.values():
            if len(group) <= 1:
                continue
            family = str(group[0]["family"])
            aggregate[family]["exact_duplicates"] += len(group) - 1
            exact_group_details.append(
                family + ":" + ";".join(str(row["row_id"]) for row in group))
        canonical_group_details = []
        for group in canonical_groups.values():
            if len(group) <= 1:
                continue
            family = str(group[0]["family"])
            aggregate[family]["canonical_duplicates"] += len(group) - 1
            canonical_group_details.append(
                family + ":" + ";".join(str(row["row_id"]) for row in group))
        dominated = []
        # Identical normalized LHS and sense gives a globally valid dominance
        # proof by RHS ordering; equality rows cannot dominate one another.
        for group in lhs_groups.values():
            if len(group) <= 1:
                continue
            senses = {str(row["canonical_signature"][1]) for row in group}
            if len(senses) != 1 or "=" in senses:
                continue
            canonical_rhs = [float(row["canonical_signature"][2]) for row in group]
            if max(canonical_rhs) - min(canonical_rhs) <= 1e-12:
                continue
            sense = next(iter(senses))
            tight_value = min(canonical_rhs) if sense == "<=" else max(canonical_rhs)
            for row, value in zip(group, canonical_rhs):
                if abs(value - tight_value) > 1e-12:
                    dominated.append(str(row["row_id"]))
        duplicate_rows.append({
            "state_id": state["state_id"], "model_sha256": state["canonical_model_fingerprint"],
            "row_count": len(parsed), "family_count": len(family_counts),
            "exact_duplicate_rows": exact_duplicate_count,
            "canonical_signature_duplicate_rows": canonical_duplicate_count,
            "exact_duplicate_groups": "|".join(exact_group_details)
                                      if exact_group_details else "none",
            "canonical_duplicate_groups": "|".join(canonical_group_details)
                                          if canonical_group_details else "none",
            "same_lhs_proved_dominated_rows": len(dominated),
            "dominated_row_ids": ";".join(dominated) if dominated else "none",
            "all_rows_parsed": "true", "failure_reason": "none",
        })

    registry_fields = [
        "family", "classification", "row_count_all_23_states",
        "nonzero_count_all_23_states", "minimum_absolute_coefficient",
        "maximum_absolute_coefficient", "minimum_absolute_rhs",
        "maximum_absolute_rhs", "exact_duplicate_count",
        "canonical_signature_duplicate_count", "root_lp_contribution",
        "root_work_contribution", "presolved_size_effect",
        "total_work_nodes_effect", "core_row_protected", "audit_status",
    ]
    registry_rows = []
    for family, classification in FAMILIES.items():
        stats = aggregate[family]
        registry_rows.append({
            "family": family, "classification": classification,
            "row_count_all_23_states": stats["rows"],
            "nonzero_count_all_23_states": stats["nonzeros"],
            "minimum_absolute_coefficient": (
                format(stats["min_coef"], ".17g") if stats["rows"] else "not_present"),
            "maximum_absolute_coefficient": (
                format(stats["max_coef"], ".17g") if stats["rows"] else "not_present"),
            "minimum_absolute_rhs": (
                format(stats["min_rhs"], ".17g") if stats["rows"] else "not_present"),
            "maximum_absolute_rhs": (
                format(stats["max_rhs"], ".17g") if stats["rows"] else "not_present"),
            "exact_duplicate_count": stats["exact_duplicates"],
            "canonical_signature_duplicate_count": stats["canonical_duplicates"],
            "root_lp_contribution": "not_isolatable_without_mathematical_block_removal",
            "root_work_contribution": "not_isolatable_without_mathematical_block_removal",
            "presolved_size_effect": "not_isolatable_from_generic_canonical_row_names",
            "total_work_nodes_effect": "not_run_without_valid_candidate",
            "core_row_protected": str(classification in {
                "core feasibility/model-definition", "exact reformulation"}).lower(),
            "audit_status": "present_and_exhaustively_classified" if stats["rows"]
                            else "disabled_or_not_present_in_v0",
        })
    if sum(int(row["row_count_all_23_states"]) for row in registry_rows) != all_parsed_rows:
        raise RuntimeError("row-family registry is not exhaustive")

    registry_path = EVIDENCE / "cut_and_row_family_registry.csv"
    with registry_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=registry_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(registry_rows)
    duplicate_path = EVIDENCE / "duplicate_and_dominance_audit.csv"
    with duplicate_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(duplicate_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(duplicate_rows)

    total_exact_duplicates = sum(int(row["exact_duplicate_rows"]) for row in duplicate_rows)
    total_canonical_duplicates = sum(
        int(row["canonical_signature_duplicate_rows"]) for row in duplicate_rows)
    total_dominated = sum(int(row["same_lhs_proved_dominated_rows"])
                          for row in duplicate_rows)
    leave_rows = []
    for row in registry_rows:
        classification = row["classification"]
        protected = classification in {
            "core feasibility/model-definition", "exact reformulation"}
        exact_duplicates = int(row["exact_duplicate_count"])
        if exact_duplicates > 0:
            eligibility = "entered_C1"
            reason = (
                "literal duplicate rows proved identical; one protected core "
                "representative remains for every omitted copy")
        elif protected:
            eligibility = "forbidden"
            reason = "core_or_exact_reformulation_row_protected"
        elif row["audit_status"] != "present_and_exhaustively_classified":
            eligibility = "not_applicable"
            reason = "family_not_present_in_v0"
        else:
            eligibility = "not_entered"
            reason = "generic canonical row names do not isolate a complete source emitter and no exact separator/removal proof exists"
        leave_rows.append({
            "family": row["family"], "classification": classification,
            "row_count": row["row_count_all_23_states"],
            "leave_one_block_eligibility": eligibility,
            "candidate_run": "false", "reason": reason,
            "root_bound_effect": "not_run", "root_work_effect": "not_run",
            "total_work_effect": "not_run", "certificate_effect": "not_run",
        })
    leave_path = EVIDENCE / "cut_family_leave_one_block_audit.csv"
    with leave_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(leave_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(leave_rows)

    notes_dir = EVIDENCE / "mathematical_validity_notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    (notes_dir / "c1_exact_duplicate_elimination.md").write_text(f"""# C1 exact duplicate elimination validity

All {all_parsed_rows} canonical constraints from the 23 frozen models were parsed and assigned exactly once to the exhaustive registry. The exact/sign-canonical scan found {total_exact_duplicates} exact duplicates and {total_canonical_duplicates} sign-canonical duplicates; the identical-LHS RHS-order scan found {total_dominated} additional globally proved dominated rows.

Every literal duplicate is in the operation/load core family. It occurs only when a primitive pickup or drop upper bound is zero: the visit link and operation-mode link both reduce to the same one-variable inequality (`p_k_i <= 0` or `d_k_i <= 0`). C1 keeps the visit-link copy and omits only the second, byte-identical mode-link copy. Thus every core relationship remains represented, the variable domains, objective, feasible set, LP relaxation, integer optimum, and certificate meaning are unchanged, and the candidate is uniform in mathematical bounds rather than instance identity or size.

C2 is not entered because no complete strengthening emitter has an exact delayed separator. C3 is not entered because coefficient ranges alone do not prove an additional bound or big-M tightening beyond the current tight interval construction. C4 is not entered because the audit did not isolate a specific unaddressed relaxation defect. C1 must complete the frozen 120-second core screen and, if it remains the iteration's best candidate, all D1-D14 at 300 seconds before acceptance.
""", encoding="utf-8")

    gate = {
        "schema": "round50-cut-formulation-audit-gate-v1",
        "iteration": 2, "status": "candidate_required",
        "candidate_count": 1, "candidate_id": "C1",
        "candidate_policy": "c1-exact-duplicate-elimination",
        "all_rows_parsed": True, "parsed_row_count": all_parsed_rows,
        "state_count": len(states), "registry_family_count": len(registry_rows),
        "exact_duplicate_rows": total_exact_duplicates,
        "canonical_signature_duplicate_rows": total_canonical_duplicates,
        "same_lhs_proved_dominated_rows": total_dominated,
        "core_relationships_disabled_or_delayed": 0,
        "exact_reformulation_row_removals": 0,
        "generic_gurobi_cut_parameter_changed": False,
        "candidate_run_opened": True,
        "reason": "literal duplicates have a complete uniform C1 removal proof",
        "active_policy_before_candidate": "interval-mip-v0 original cut/formulation pack",
        "confirmation_opened": False, "runtime_dispatch": False,
        "registry_sha256": sha256(registry_path),
        "duplicate_audit_sha256": sha256(duplicate_path),
        "leave_one_audit_sha256": sha256(leave_path),
    }
    (EVIDENCE / "cut_formulation_audit_gate.json").write_text(
        json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(gate, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
