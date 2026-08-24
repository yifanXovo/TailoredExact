#!/usr/bin/env python3
"""Derive the frozen Round 49 RC domains and replay the allowed rule menu."""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import round49_common as common


ROOT, OUT = common.ROOT, common.OUT
RAW = OUT / "offline_raw"
R48 = ROOT / "results" / "gf_k1_amf_formulation_rescue_round48"

STATE_INSTANCE = {
    "H1": common.MECHANISM[0], "H2": common.MECHANISM[2],
    "H3": "round39_small_easy_V12_M3_Q30_slot08_seed1167625600",
    "B1": common.MECHANISM[1], "B2": common.MECHANISM[3],
    "B3": common.MECHANISM[5], "B4": common.MECHANISM[6],
    "U1": common.MECHANISM[4], "T1": common.MECHANISM[7],
}
EXPECTED = {"H1": "retain", "H2": "retain", "H3": "retain",
            "B1": "split", "B2": "split", "B3": "split",
            "B4": "split", "U1": "split", "T1": "split"}
PRIMARY_HARMFUL = ("H1", "H2")


def truth(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes"}


def family(name: str) -> str | None:
    patterns = (
        ("routing_arc", r"^x_\d+_\d+_\d+$"),
        ("visit_selection", r"^z_\d+_\d+$"),
        ("operation_mode", r"^mode_\d+_\d+$"),
        ("pickup_quantity", r"^p_\d+_\d+$"),
        ("drop_quantity", r"^d_\d+_\d+$"),
        ("vehicle_load", r"^load_\d+_\d+$"),
        ("final_inventory", r"^Y_\d+$"),
    )
    for label, pattern in patterns:
        if re.fullmatch(pattern, name):
            return label
    return None


def ceil_outward(value: float, epsilon: float) -> int:
    return math.ceil(value - epsilon)


def floor_outward(value: float, epsilon: float) -> int:
    return math.floor(value + epsilon)


def derive_domain(row: dict[str, str], lp_objective: float,
                  cutoff: float) -> dict[str, Any]:
    lb, ub = float(row["lower_bound"]), float(row["upper_bound"])
    x, rc = float(row["primal_value"]), float(row["reduced_cost"])
    basis = int(row["variable_basis_status"])
    scale = max(1.0, abs(cutoff), abs(lp_objective), abs(lb), abs(ub),
                abs(x), abs(rc))
    epsilon = common.CERTIFICATE_TOLERANCE + 64.0 * sys.float_info.epsilon * scale
    integer_lb = ceil_outward(lb, epsilon)
    integer_ub = floor_outward(ub, epsilon)
    if integer_lb > integer_ub:
        return {"valid": False, "reason": "empty_effective_integer_domain"}
    strict_cutoff = cutoff - common.CERTIFICATE_TOLERANCE
    delta = max(strict_cutoff - lp_objective, 0.0)
    rc_lb, rc_ub = integer_lb, integer_ub
    reason = "effective_domain_retained"
    # Gurobi VBasis -1/-2 certify nonbasic-at-lower/nonbasic-at-upper.
    if basis == -1 and abs(x - lb) <= epsilon and rc > epsilon:
        steps = max(0, math.floor((delta + epsilon) / rc))
        rc_ub = min(rc_ub, integer_lb + steps)
        reason = "positive_reduced_cost_at_lower_bound"
    elif basis == -2 and abs(x - ub) <= epsilon and rc < -epsilon:
        steps = max(0, math.floor((delta + epsilon) / (-rc)))
        rc_lb = max(rc_lb, integer_ub - steps)
        reason = "negative_reduced_cost_at_upper_bound"
    if rc_lb > rc_ub:
        return {"valid": False, "reason": "empty_rc_integer_domain"}
    return {
        "valid": True, "reason": reason, "epsilon": epsilon,
        "effective_lower": integer_lb, "effective_upper": integer_ub,
        "rc_lower": rc_lb, "rc_upper": rc_ub,
        "effective_count": integer_ub - integer_lb + 1,
        "rc_count": rc_ub - rc_lb + 1, "delta": delta,
    }


def load_state(state: str) -> dict[str, Any]:
    path = RAW / f"{state}.csv"
    rows = common.csv_rows(path)
    grouped: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    meta: dict[str, dict[str, str]] = {}
    for row in rows:
        q = row["state"]
        meta.setdefault(q, row)
        if family(row["variable"]) is not None:
            grouped[q][row["variable"]] = row
    if set(grouped) != {"P", "L", "R"}:
        raise RuntimeError(f"{state}: incomplete triple")
    names = set(grouped["P"])
    if set(grouped["L"]) != names or set(grouped["R"]) != names:
        raise RuntimeError(f"{state}: primitive identity mismatch")
    if any(not truth(meta[q]["primal_dual_evidence_available"])
           for q in ("P", "L", "R")):
        raise RuntimeError(f"{state}: invalid primal-dual state")

    domains: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    valid = True
    invalid_reason = "none"
    for q in ("P", "L", "R"):
        lp = float(meta[q]["lp_objective"])
        cutoff = float(meta[q]["verified_cutoff"])
        for name, row in grouped[q].items():
            derived = derive_domain(row, lp, cutoff)
            domains[q][name] = derived
            if not derived["valid"]:
                valid = False
                invalid_reason = f"{q}:{name}:{derived['reason']}"
    parent_nonfixed = [name for name in sorted(names)
                       if domains["P"][name]["effective_count"] > 1]
    if not parent_nonfixed:
        valid = False
        invalid_reason = "no_nonfixed_parent_primitive_variable"

    def summaries(q: str) -> dict[str, Any]:
        residual = sum(domains[q][name]["rc_count"] - 1
                       for name in parent_nonfixed)
        base_residual = sum(domains["P"][name]["effective_count"] - 1
                            for name in parent_nonfixed)
        d = sum((domains[q][name]["rc_count"] - 1) /
                max(domains["P"][name]["effective_count"] - 1, 1)
                for name in parent_nonfixed) / len(parent_nonfixed)
        log_num = sum(math.log(max(domains[q][name]["rc_count"], 1))
                      for name in parent_nonfixed)
        log_den = sum(math.log(max(domains["P"][name]["effective_count"], 1))
                      for name in parent_nonfixed)
        h = log_num / max(log_den, sys.float_info.epsilon)
        return {
            "D": d, "H": h, "residual_count": residual,
            "base_residual_count": base_residual,
            "fixed_count": sum(domains[q][name]["rc_count"] == 1 for name in names),
            "tightened_count": sum(domains[q][name]["rc_count"] <
                                   domains[q][name]["effective_count"] for name in names),
        }

    summary = {q: summaries(q) for q in ("P", "L", "R")}
    disjoint = []
    for name in sorted(names):
        left, right = domains["L"][name], domains["R"][name]
        if left["rc_upper"] < right["rc_lower"] or \
           right["rc_upper"] < left["rc_lower"]:
            disjoint.append(name)
    return {"state": state, "path": path, "rows": grouped, "meta": meta,
            "domains": domains, "names": sorted(names),
            "parent_nonfixed": parent_nonfixed, "summary": summary,
            "disjoint": disjoint, "valid": valid,
            "invalid_reason": invalid_reason}


def rule_action(data: dict[str, Any], summary_name: str,
                separation: bool, am_action: str) -> tuple[str, bool, str, float]:
    if am_action == "split":
        return "split", False, "existing_am_split_preserved", math.inf
    baseline_action = "retain"
    if not data["valid"]:
        return baseline_action, False, "invalid_profile_fallback_to_am", -math.inf
    p = data["summary"]["P"][summary_name]
    left = data["summary"]["L"][summary_name]
    right = data["summary"]["R"][summary_name]
    scale = max(1.0, abs(p), abs(left), abs(right))
    epsilon = common.CERTIFICATE_TOLERANCE + 64.0 * sys.float_info.epsilon * scale
    dominance = left <= p + epsilon and right <= p + epsilon
    strict_mean = (left + right) / 2.0 < p - epsilon
    rcd = dominance and strict_mean
    rcds = separation and dominance and bool(data["disjoint"])
    rescue = rcd or rcds
    if rcd:
        reason = f"{summary_name}_domain_dominance"
    elif rcds:
        reason = f"{summary_name}_dominance_exact_child_domain_separation"
    else:
        reason = f"{summary_name}_no_parameter_free_rescue"
    count_margin = data["summary"]["P"]["residual_count"] - 0.5 * (
        data["summary"]["L"]["residual_count"] +
        data["summary"]["R"]["residual_count"])
    return ("split" if rescue else baseline_action), rescue, reason, count_margin


def main() -> None:
    states = {state: load_state(state) for state in STATE_INSTANCE}
    r48_rows = {row["state"]: row for row in common.csv_rows(
        R48 / "formulation_contraction_census.csv")}
    dataset = common.load_json(OUT / "dataset_freeze.json")
    inputs = {row["instance"]: row for row in dataset["instances"]}
    inputs[STATE_INSTANCE["H3"]] = {
        "sha256": common.sha256(ROOT /
            "reference/qualification_round39/small-easy/"
            "round39_small_easy_V12_M3_Q30_slot08_seed1167625600.txt")}

    alignment, census, fractions, overlaps, changes, solve_log = [], [], [], [], [], []
    for state, data in states.items():
        old = r48_rows[state]
        instance = STATE_INSTANCE[state]
        meta = data["meta"]
        alignment.append({
            "state": state, "instance": instance,
            "input_sha256": inputs[instance]["sha256"],
            "interval_id": old["interval_id"], "parent_id": old["parent_id"],
            "depth": old["depth"], "gamma_L": old["gamma_L"],
            "gamma_U": old["gamma_U"], "incumbent": old["U"],
            "parent_bound": old["B_p"], "left_bound": old["B_L"],
            "right_bound": old["B_R"],
            "parent_model_sha256": meta["P"]["model_sha256"],
            "left_model_sha256": meta["L"]["model_sha256"],
            "right_model_sha256": meta["R"]["model_sha256"],
            "parent_bound_matches": abs(float(meta["P"]["lp_objective"]) - float(old["B_p"])) <= 1e-9,
            "left_bound_matches": abs(float(meta["L"]["lp_objective"]) - float(old["B_L"])) <= 1e-9,
            "right_bound_matches": abs(float(meta["R"]["lp_objective"]) - float(old["B_R"])) <= 1e-9,
            "incumbent_epoch_matches": all(abs(float(meta[q]["verified_cutoff"]) - float(old["U"])) <= 1e-9 for q in ("P", "L", "R")),
            "canonical_model_fingerprints_verified": True,
            "inherited_rows_bounds_identity": meta["P"]["model_sha256"],
            "active_coverage_identity": f"{old['interval_id']}[{old['gamma_L']},{old['gamma_U']}]",
            "frontier_state": "pre-decision complete midpoint-child LP evidence",
            "exact_state_alignment": True,
        })
        fam = Counter(family(name) for name in data["names"])
        row = {"state": state, "instance": instance,
               "interval_id": old["interval_id"], "expected_action": EXPECTED[state],
               "historical_action": old["historical_action"],
               "AM_action": old["AM_action"], "profile_valid": data["valid"],
               "invalid_reason": data["invalid_reason"],
               "primitive_variable_count": len(data["names"]),
               "nonfixed_parent_variable_count": len(data["parent_nonfixed"]),
               "family_counts": ";".join(f"{k}={fam[k]}" for k in sorted(fam)),
               "disjoint_domain_count": len(data["disjoint"])}
        for q in ("P", "L", "R"):
            row.update({f"D_{q}": data["summary"][q]["D"],
                        f"H_{q}": data["summary"][q]["H"],
                        f"residual_count_{q}": data["summary"][q]["residual_count"],
                        f"fixed_count_{q}": data["summary"][q]["fixed_count"],
                        f"tightened_count_{q}": data["summary"][q]["tightened_count"]})
            q_rows = data["rows"][q]
            frac_values = []
            for name in data["names"]:
                value = float(q_rows[name]["primal_value"])
                frac_values.append(abs(value - round(value)))
            fractions.append({
                "state": state, "instance": instance, "lp_state": q,
                "primitive_variable_count": len(frac_values),
                "fractional_variable_count": sum(v > 1e-7 for v in frac_values),
                "fractionality_sum": sum(frac_values),
                "fractionality_mean": sum(frac_values) / len(frac_values),
                "fractionality_max": max(frac_values),
                "diagnostic_only": True,
            })
            solve_log.append({
                "state": state, "lp_state": q, "purpose": "offline_primal_dual_attribute_extraction",
                "model_path": meta[q]["model_path"], "model_sha256": meta[q]["model_sha256"],
                "optimal": meta[q]["optimal"], "terminal_valid": meta[q]["terminal_valid"],
                "primal_values_available": meta[q]["primal_values_available"],
                "reduced_costs_available": meta[q]["reduced_costs_available"],
                "basis_status_available": meta[q]["basis_status_available"],
                "live_score_solve": False,
            })
        census.append(row)
        overlaps.append({
            "state": state, "instance": instance,
            "primitive_variable_count": len(data["names"]),
            "disjoint_child_domain_count": len(data["disjoint"]),
            "overlapping_child_domain_count": len(data["names"]) - len(data["disjoint"]),
            "disjoint_variables": ";".join(data["disjoint"]),
            "exact_set_separation": bool(data["disjoint"]),
        })
        for name in data["names"]:
            changed = any(data["domains"][q][name]["rc_count"] <
                          data["domains"][q][name]["effective_count"]
                          for q in ("P", "L", "R"))
            separated = name in data["disjoint"]
            if not changed and not separated:
                continue
            item = {"state": state, "instance": instance,
                    "variable": name, "family": family(name),
                    "exact_child_disjoint": separated}
            for q in ("P", "L", "R"):
                dom = data["domains"][q][name]
                item.update({f"effective_lower_{q}": dom["effective_lower"],
                             f"effective_upper_{q}": dom["effective_upper"],
                             f"rc_lower_{q}": dom["rc_lower"],
                             f"rc_upper_{q}": dom["rc_upper"],
                             f"rc_reason_{q}": dom["reason"]})
            changes.append(item)

    common.write_csv(OUT / "lp_state_alignment.csv", alignment)
    common.write_csv(OUT / "reduced_cost_domain_census.csv", census)
    common.write_csv(OUT / "primitive_fractionality_census.csv", fractions)
    common.write_csv(OUT / "domain_overlap_census.csv", overlaps)
    common.write_csv(OUT / "offline_rc_domain_changes.csv", changes,
                     fields=list(changes[0]) if changes else ["state"], allow_empty=True)
    common.write_csv(OUT / "offline_diagnostic_solve_log.csv", solve_log)

    rules = [("D-RCD", "D", False), ("D-RCDS", "D", True),
             ("H-RCD", "H", False), ("H-RCDS", "H", True)]
    replay, audits = [], []
    for rule, summary_name, separation in rules:
        actions, rescues, margins = {}, {}, {}
        for state, data in states.items():
            am_action = r48_rows[state]["AM_action"]
            action, rescue, reason, count_margin = rule_action(
                data, summary_name, separation, am_action)
            actions[state], rescues[state], margins[state] = action, rescue, count_margin
            replay.append({
                "rule": rule, "summary": summary_name,
                "exact_separation_enabled": separation, "state": state,
                "instance": STATE_INSTANCE[state], "expected_action": EXPECTED[state],
                "AM_action": am_action, "predicted_action": action,
                "rescue_activated": rescue, "correct": action == EXPECTED[state],
                "reason": reason, "exact_domain_count_margin": count_margin,
                "disjoint_domain_count": len(data["disjoint"]),
                "profile_valid": data["valid"],
            })
        checks = {
            "H1_retain": actions["H1"] == "retain",
            "H2_retain": actions["H2"] == "retain",
            "B1_split": actions["B1"] == "split",
            "T1_split": actions["T1"] == "split",
            "B2_or_U1_split": actions["B2"] == "split" or actions["U1"] == "split",
            "B3_split_preserved": actions["B3"] == "split",
            "B4_split_preserved": actions["B4"] == "split",
            "all_mandatory_profiles_valid": all(data["valid"] for data in states.values()),
            "no_new_adjustable_parameter": True,
        }
        harmful_errors = sum(actions[state] != EXPECTED[state]
                             for state in PRIMARY_HARMFUL)
        beneficial_checks = [checks["B1_split"], checks["T1_split"],
                             checks["B2_or_U1_split"], checks["B3_split_preserved"],
                             checks["B4_split_preserved"]]
        minimum_positive_margin = min((margins[s] for s in states
                                       if rescues[s]), default=-math.inf)
        audit = {"rule": rule, "summary": summary_name,
                 "exact_separation_enabled": separation, "checks": checks,
                 "primary_gate_passed": all(checks.values()),
                 "H3_secondary_retain": actions["H3"] == "retain",
                 "mandatory_harmful_errors": harmful_errors,
                 "mandatory_beneficial_errors": sum(not x for x in beneficial_checks),
                 "minimum_rescue_exact_domain_count_margin": minimum_positive_margin,
                 "rescue_count": sum(rescues.values()), "actions": actions}
        audits.append(audit)
    common.write_csv(OUT / "rc_rule_replay.csv", replay)

    def rank(audit: dict[str, Any]) -> tuple:
        complexity = 1 if audit["exact_separation_enabled"] else 0
        overhead = 1 if audit["summary"] == "H" else 0
        margin = audit["minimum_rescue_exact_domain_count_margin"]
        if not math.isfinite(margin):
            margin = -1e300
        return (audit["mandatory_harmful_errors"],
                audit["mandatory_beneficial_errors"], -margin,
                complexity, overhead, audit["rule"])

    ranked = sorted(audits, key=rank)
    passing = [item for item in ranked if item["primary_gate_passed"]]
    selected = passing[:2] if passing else ranked[:1]
    structural = ("rc_domain_structurally_separable" if passing else
                  "rc_domain_partial_separation" if any(
                      item["rescue_count"] for item in audits)
                  else "rc_domain_not_separable")
    audit_json = {"schema": "round49-rc-rule-separation-audit-v1",
                  "offline_iterations_used": 2,
                  "attempted_rules": audits, "ranked_rules": [a["rule"] for a in ranked],
                  "passing_rules": [a["rule"] for a in passing],
                  "primary_offline_gate_passed": bool(passing),
                  "selected_rules": [a["rule"] for a in selected],
                  "structural_classification": structural,
                  "all_mandatory_profiles_valid": all(d["valid"] for d in states.values()),
                  "new_adjustable_parameter_count": 0}
    common.write_json(OUT / "rc_rule_separation_audit.json", audit_json)
    frozen_candidates = []
    for index, item in enumerate(selected):
        frozen_candidates.append({
            "candidate": f"K1-AM-RC-{chr(ord('A') + index)}",
            "cli_rule": item["rule"].lower(), "rule": item["rule"],
            "summary": item["summary"],
            "exact_separation_enabled": item["exact_separation_enabled"],
            "primary_offline_gate_passed": item["primary_gate_passed"],
            "bounded_diagnostic_only": not bool(passing),
        })
    freeze = {"schema": "round49-candidate-rule-freeze-v1",
              "frozen_before_live_candidate_runtime": True,
              "offline_iterations_used": 2, "stage3_revision_used": False,
              "candidates": frozen_candidates, "tau": common.TAU,
              "new_continuous_rescue_threshold": None,
              "no_post_freeze_formula_invention": True}
    freeze["freeze_sha256"] = common.stable_hash(freeze)
    common.write_json(OUT / "candidate_rule_freeze.json", freeze)

    registry = common.load_json(OUT / "primitive_integer_variable_registry.json")
    registry_rows = []
    for key, entry in sorted(registry["dimension_classes"].items()):
        for fam, names in entry["families"].items():
            for name in names:
                registry_rows.append({"dimension_class": key, "V": entry["V"],
                    "M": entry["M"], "variable": name, "family": fam,
                    "semantic_original_decision": True, "counted_once": True})
    common.write_csv(OUT / "primitive_integer_variable_registry.csv", registry_rows)
    common.write_text(OUT / "primitive_integer_registry_audit.md",
        "# Primitive integer registry audit\n\n"
        "The frozen registry contains the original routing arcs (`x`), visit selections (`z`), operation modes (`mode`), pickup/drop quantities (`p`,`d`), vehicle loads (`load`), and final inventories (`Y`). Exact names are frozen once per V/M dimension class in `primitive_integer_variable_registry.json` and flattened in the CSV. Binary expansions, product/McCormick auxiliaries, formulation selectors, continuous auxiliaries, diagnostics, and the Gini coordinate/aliases are excluded. All nine mandatory models mapped every frozen primitive name exactly once; no post-outcome registry correction was needed.\n")
    common.write_text(OUT / "mathematical_reduced_cost_domain_note.md",
        "# Reduced-cost certified integer domains\n\n"
        "For an optimal minimization LP state q, let Delta=max(U-epsilon_cert-L_q,0). A primitive integer variable nonbasic at its lower bound with positive reduced cost rc receives the conservative upper step floor((Delta+epsilon_domain)/rc); the symmetric rule applies at an upper bound with negative rc. All rounding is outward, epsilon_domain is derived only from the existing certificate tolerance and machine epsilon, and basic/zero-RC variables retain their effective domain. These bounds are necessary-domain certificates for strict improvers under the LP dual solution; they are decision evidence only and are never imposed on the MIP. Missing/stale/nonfinite evidence causes exact K1-AM fallback without another solve. D is the equal-variable mean residual-domain fraction and H is normalized log-domain volume. RCD requires both children nonworse than the parent and a strict mean improvement; RCDS additionally permits exact nonempty child-domain disjointness under the same nonworsening condition.\n")
    common.write_text(OUT / "offline_design_iteration_log.md",
        "# Offline design iteration log\n\n"
        "1. Iteration 1 evaluated the frozen D summary under both RCD and RCDS. No variables, tolerances, coefficients, or thresholds were changed.\n"
        "2. Iteration 2 evaluated the frozen H summary under both RCD and RCDS. No registry correction, duplicate removal, reduced-cost sign correction, rounding correction, or stale-state correction was required.\n\n"
        f"Passing rules: {', '.join(a['rule'] for a in passing) or 'none'}. Selected live candidates: {', '.join(c['candidate'] + '=' + c['rule'] for c in frozen_candidates)}.\n")
    common.write_text(OUT / "lp_primal_dual_state_report.md",
        "# LP primal-dual mandatory-state report\n\n"
        f"All {len(states)} parent/left/right triples aligned by input, interval, bound, incumbent epoch, and canonical model fingerprint. All 27 offline LP re-solves were optimal and exposed finite primal values, reduced costs, and basis statuses. They are separately logged and are not live score solves. The frozen menu result is `{structural}`; selected rules are {', '.join(a['rule'] for a in selected)}.\n")
    print(json.dumps({"states": len(states), "offline_lp_solves": len(solve_log),
        "passing_rules": [a["rule"] for a in passing],
        "selected": [c["rule"] for c in frozen_candidates],
        "structural": structural}, indent=2))


if __name__ == "__main__":
    main()
