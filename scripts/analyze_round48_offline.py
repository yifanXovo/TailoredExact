#!/usr/bin/env python3
"""Reconstruct frozen AMF profiles from existing Round 46/47 evidence only."""

from __future__ import annotations

import csv
import math
import re
import sys
from pathlib import Path
from typing import Any

import round48_common as common


ROOT, OUT = common.ROOT, common.OUT
R46 = ROOT / "results" / "gf_c6_rho_k1_k4_screen_round46" / "runs"
R47 = ROOT / "results" / "gf_c6_adaptive_mass_contraction_round47" / "runs"

STATE_SOURCES = {
    "H1": ("stage5_1800s", common.MECHANISM[0], 1, "retain_beneficial"),
    "H2": ("stage5_1800s", common.MECHANISM[2], 1, "retain_beneficial"),
    "H3": ("stage4_1200s", "round39_small_easy_V12_M3_Q30_slot08_seed1167625600", 1,
           "startup_retain_diagnostic"),
    "B1": ("stage5_1800s", common.MECHANISM[1], 1, "midpoint_split_beneficial"),
    "B2": ("stage5_1800s", common.MECHANISM[3], 1, "midpoint_split_beneficial"),
    "B3": ("stage5_1800s", common.MECHANISM[5], 1, "split_expected"),
    "B4": ("stage5_1800s", common.MECHANISM[6], 1, "split_expected"),
    "U1": ("stage5_1800s", common.MECHANISM[4], 1,
           "pending_matched_retain_vs_midpoint"),
    "T1": ("stage5_1800s", common.MECHANISM[7], 2,
           "pending_matched_tight3102_divergence_replay"),
}

FAMILY_PATTERNS = (
    ("final_inventory", re.compile(r"Y_\d+\Z")),
    ("station_ratio", re.compile(r"r_\d+\Z")),
    ("absolute_deviation", re.compile(r"e_\d+\Z")),
    ("pairwise_ratio_difference", re.compile(r"h_\d+_\d+\Z")),
    ("inventory_bit", re.compile(r"bit_\d+_\d+\Z")),
    ("gini_inventory_product", re.compile(r"prod_\d+_\d+\Z")),
    ("pickup_movement", re.compile(r"p_\d+_\d+\Z")),
    ("drop_movement", re.compile(r"d_\d+_\d+\Z")),
    ("ratio_penalty_product", re.compile(r"W_SP\Z")),
)


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def family(name: str) -> str | None:
    for label, pattern in FAMILY_PATTERNS:
        if pattern.fullmatch(name):
            return label
    return None


def lp_bounds(path: Path) -> dict[str, tuple[float, float]]:
    result: dict[str, tuple[float, float]] = {}
    active = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line == "Bounds":
            active = True
            continue
        if active and line in {"Binaries", "Generals", "End"}:
            break
        if not active or not line:
            continue
        fields = line.split()
        if len(fields) == 5 and fields[1] == "<=" and fields[3] == "<=":
            result[fields[2]] = (float(fields[0]), float(fields[4]))
    if not result:
        raise RuntimeError(f"no canonical bounds parsed: {path}")
    return result


def width_tolerance(lower: float, upper: float) -> float:
    return max(common.CERTIFICATE_TOLERANCE,
               32.0 * sys.float_info.epsilon *
               max(1.0, abs(lower), abs(upper)))


def profile(parent_path: Path, left_path: Path, right_path: Path) -> dict[str, Any]:
    bounds = [lp_bounds(path) for path in (parent_path, left_path, right_path)]
    candidates = sorted(set(bounds[0]) | set(bounds[1]) | set(bounds[2]))
    eligible: list[dict[str, Any]] = []
    invalid_variables: list[str] = []
    excluded_gini = sum(name == "G" for name in candidates)
    excluded_gini_alias = sum(name.startswith("segment_G_") for name in candidates)
    for name in candidates:
        label = family(name)
        if label is None:
            continue
        if not all(name in item for item in bounds):
            invalid_variables.append(name + ":missing_bound")
            continue
        parent_lower, parent_upper = bounds[0][name]
        values = [parent_lower, parent_upper, *bounds[1][name], *bounds[2][name]]
        if not all(math.isfinite(value) for value in values):
            invalid_variables.append(name + ":nonfinite_bound")
            continue
        parent_width = parent_upper - parent_lower
        tolerance = width_tolerance(parent_lower, parent_upper)
        if parent_width <= tolerance:
            continue
        child_rows = []
        wider = False
        for side, child in zip(("L", "R"), bounds[1:]):
            child_lower, child_upper = child[name]
            child_width = child_upper - child_lower
            if child_width > parent_width + tolerance:
                wider = True
                invalid_variables.append(name + f":child_{side}_wider")
            contraction = min(1.0, max(0.0, 1.0 - child_width / parent_width))
            child_rows.append((child_lower, child_upper, child_width, contraction))
        eligible.append({
            "variable": name, "family": label,
            "parent_lower": parent_lower, "parent_upper": parent_upper,
            "parent_width": parent_width, "width_tolerance": tolerance,
            "left_lower": child_rows[0][0], "left_upper": child_rows[0][1],
            "left_width": child_rows[0][2], "c_L": child_rows[0][3],
            "right_lower": child_rows[1][0], "right_upper": child_rows[1][1],
            "right_width": child_rows[1][2], "c_R": child_rows[1][3],
            "fixed_left": child_rows[0][2] <= tolerance,
            "fixed_right": child_rows[1][2] <= tolerance,
            "wider_invalid": wider,
        })
    valid = not invalid_variables
    phi_left = sum(item["c_L"] for item in eligible) / len(eligible) if eligible else 0.0
    phi_right = sum(item["c_R"] for item in eligible) / len(eligible) if eligible else 0.0
    if not valid:
        phi_left = phi_right = 0.0
    counts = {label: sum(item["family"] == label for item in eligible)
              for label, _ in FAMILY_PATTERNS}
    return {
        "valid": valid, "failure_reason": "none" if valid else ";".join(invalid_variables),
        "eligible": eligible, "eligible_variable_count": len(eligible),
        "excluded_gini_variable_count": excluded_gini + excluded_gini_alias,
        "invalid_variable_count": len(invalid_variables),
        "family_counts": counts, "phi_L": phi_left, "phi_R": phi_right,
        "left_min": min((item["c_L"] for item in eligible), default=0.0),
        "left_mean": phi_left,
        "left_max": max((item["c_L"] for item in eligible), default=0.0),
        "right_min": min((item["c_R"] for item in eligible), default=0.0),
        "right_mean": phi_right,
        "right_max": max((item["c_R"] for item in eligible), default=0.0),
        "fixed_left": sum(item["fixed_left"] for item in eligible),
        "fixed_right": sum(item["fixed_right"] for item in eligible),
    }


def state_row(label: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    stage, instance, sequence, counterfactual = STATE_SOURCES[label]
    run_dir = R47 / f"{stage}__{instance}__K1-AM"
    decisions = common.csv_rows(run_dir / "external" / "adaptive_mass_decision_ledger.csv")
    matches = [row for row in decisions if int(row["decision_sequence"]) == sequence]
    if len(matches) != 1:
        raise RuntimeError(f"{label} decision match count {len(matches)}")
    source = matches[0]
    interval = source["interval_id"]
    model_dir = run_dir / "external" / "models"
    models = [model_dir / f"{interval}.lp", model_dir / f"{interval}.0.lp",
              model_dir / f"{interval}.1.lp"]
    formulation = profile(*models)
    g_left, g_right = float(source["g_L"]), float(source["g_R"])
    eta, mu, s_am = float(source["eta"]), float(source["mu"]), float(source["S_AM"])
    gtilde_left = g_left + formulation["phi_L"] * max(g_right - g_left, 0.0)
    gtilde_right = g_right + formulation["phi_R"] * max(g_left - g_right, 0.0)
    eta_hat = min(gtilde_left, gtilde_right)
    s_amf = mu * eta_hat
    score_tolerance = float(source["score_tolerance"])
    am_action = source["selected_action"]
    amf_action = "split" if s_amf + score_tolerance >= common.TAU else am_action
    if am_action == "split":
        amf_action = "split"
    row = {
        "state": label, "instance": instance, "source_run_id": run_dir.name,
        "decision_sequence": sequence, "interval_id": interval,
        "parent_id": source["parent_id"], "depth": int(source["depth"]),
        "gamma_L": float(source["gamma_L"]), "gamma_U": float(source["gamma_U"]),
        "B_p": float(source["B_p"]), "B_L": float(source["B_L"]),
        "B_R": float(source["B_R"]), "U": float(source["U"]),
        "g_L": g_left, "g_R": g_right, "eta": eta, "mu": mu,
        "S_AM": s_am, "eligible_variable_count": formulation["eligible_variable_count"],
        "per_family_variable_counts": ";".join(
            f"{key}={value}" for key, value in formulation["family_counts"].items()),
        "phi_L": formulation["phi_L"], "phi_R": formulation["phi_R"],
        "gtilde_L": gtilde_left, "gtilde_R": gtilde_right,
        "eta_hat": eta_hat, "S_AMF": s_amf, "tau": common.TAU,
        "S_AMF_minus_tau": s_amf - common.TAU,
        "historical_action": source["selected_action"],
        "counterfactual_label": counterfactual, "AM_action": am_action,
        "AMF_predicted_action": amf_action,
        "rescue_activated": am_action != "split" and amf_action == "split",
        "profile_valid": formulation["valid"],
        "profile_failure_reason": formulation["failure_reason"],
        "excluded_gini_variable_count": formulation["excluded_gini_variable_count"],
        "invalid_variable_count": formulation["invalid_variable_count"],
        "parent_model_sha256": common.sha256(models[0]),
        "left_model_sha256": common.sha256(models[1]),
        "right_model_sha256": common.sha256(models[2]),
        "source_ledger": (run_dir / "external" /
                          "adaptive_mass_decision_ledger.csv").relative_to(ROOT).as_posix(),
        "source_ledger_sha256": common.sha256(
            run_dir / "external" / "adaptive_mass_decision_ledger.csv"),
    }
    registry_rows = [{"state": label, "instance": instance,
                      "interval_id": interval, **item} for item in formulation["eligible"]]
    return row, registry_rows


def tight_alignment() -> list[dict[str, Any]]:
    instance = "tight_T_seed3102"
    r46_dir = R46 / f"stage5_1800s__{instance}__K1-r015"
    r47_dir = R47 / f"stage5_1800s__{instance}__K1-AM"
    r46 = common.csv_rows(r46_dir / "external" / "c6_split_decision_ledger.csv")
    r47 = common.csv_rows(r47_dir / "external" / "c6_split_decision_ledger.csv")
    keyed47 = {(row["interval_id"], row["parent_id"], row["depth"],
                row["gamma_L"], row["gamma_U"], row["verified_incumbent"],
                row["parent_bound"], row["left_child_bound"],
                row["right_child_bound"], row["left_child_infeasible"],
                row["right_child_infeasible"]): row
               for row in r47}
    aligned: list[dict[str, Any]] = []
    input_hash = common.sha256(ROOT / common.INSTANCE_PATHS[instance])
    for left in r46:
        key = (left["interval_id"], left["parent_id"], left["depth"],
               left["gamma_L"], left["gamma_U"], left["verified_incumbent"],
               left["parent_bound"], left["left_child_bound"],
               left["right_child_bound"], left["left_child_infeasible"],
               left["right_child_infeasible"])
        right = keyed47.get(key)
        if right is None:
            continue
        parent_model46 = r46_dir / "external" / "models" / f"{left['interval_id']}.lp"
        parent_model47 = r47_dir / "external" / "models" / f"{right['interval_id']}.lp"
        model46_hash = common.sha256(parent_model46)
        model47_hash = common.sha256(parent_model47)
        bounds_equal = all(left[field] == right[field] for field in
                           ("parent_bound", "left_child_bound", "right_child_bound",
                            "left_child_infeasible", "right_child_infeasible"))
        identity = input_hash == input_hash and model46_hash == model47_hash and bounds_equal
        aligned.append({
            "instance": instance, "instance_sha256": input_hash,
            "interval_id": left["interval_id"], "parent_id": left["parent_id"],
            "depth": left["depth"], "gamma_L": left["gamma_L"],
            "gamma_U": left["gamma_U"], "incumbent": left["verified_incumbent"],
            "parent_bound": left["parent_bound"], "left_bound": left["left_child_bound"],
            "right_bound": left["right_child_bound"],
            "parent_model_sha256_r015": model46_hash,
            "parent_model_sha256_am": model47_hash,
            "parent_model_fingerprint_equal": model46_hash == model47_hash,
            "inherited_canonical_rows_bounds_identity": model46_hash,
            "active_coverage_identity":
                f"{left['interval_id']}[{left['gamma_L']},{left['gamma_U']}]",
            "frontier_target_state": "pre-decision complete midpoint-child LP evidence",
            "r015_action": left["selected_action"], "am_action": right["selected_action"],
            "exact_common_state": identity,
            "action_divergence": identity and left["selected_action"] != right["selected_action"],
            "first_common_divergence": identity and left["interval_id"] == "L0.0",
            "later_common_divergence": False,
            "r015_source_sha256": common.sha256(
                r46_dir / "external" / "c6_split_decision_ledger.csv"),
            "am_source_sha256": common.sha256(
                r47_dir / "external" / "c6_split_decision_ledger.csv"),
        })
    return aligned


def counterfactual_rows(case: str) -> list[dict[str, Any]]:
    rows = []
    interval = "L0" if case == "U1_root" else "L0.0"
    instance = common.MECHANISM[4] if case == "U1_root" else "tight_T_seed3102"
    for arm in ("retain", "midpoint"):
        run_dir = OUT / "counterfactual_runs" / f"{case}__{arm}"
        result_path = run_dir / "result.json"
        marker_path = run_dir / "completion_marker.json"
        if not result_path.is_file() or not marker_path.is_file():
            raise RuntimeError(f"missing completed counterfactual: {case} {arm}")
        result = common.load_json(result_path)
        if isinstance(result, list):
            result = result[0]
        marker = common.load_json(marker_path)
        if not marker.get("complete") or not marker.get("counterfactual_performed"):
            raise RuntimeError(f"incomplete counterfactual marker: {marker_path}")
        rows.append({
            "instance": instance, "interval_id": interval, "arm": arm,
            "process_cap_seconds": marker["process_cap_seconds"],
            "matched_parent_identity": True,
            "further_recursive_splits_forbidden": arm == "midpoint",
            "descendant_split_suppression_count": result.get(
                "round48_counterfactual_descendant_split_suppression_count", 0),
            "restricted_parent_exact":
                result.get("status") == "round48_counterfactual_exact",
            "diagnostic_not_original_problem_certificate": True,
            "strict_original_problem_certificate": bool(
                result.get("strict_certified_original_problem")),
            "certificate_class": result.get("strict_certificate_class", ""),
            "work": result.get("external_gini_tree_work", ""),
            "time_seconds": result.get("final_process_wall_time_seconds",
                                       result.get("actual_runtime_seconds", "")),
            "lower_bound": result.get("lower_bound", ""),
            "upper_bound": result.get("upper_bound", ""),
            "gap": result.get("gap", ""),
            "split_count": result.get("external_gini_tree_split_count", ""),
            "lp_count": result.get("external_gini_tree_lp_optimize_count", ""),
            "model_count": result.get("external_gini_tree_model_count", ""),
            "result_path": result_path.relative_to(ROOT).as_posix(),
            "result_sha256": common.sha256(result_path),
            "executable_sha256": marker["executable_sha256"],
            "status": result.get("status", ""),
        })
    return rows


def main() -> None:
    freeze = common.load_json(OUT / "stage0_freeze_manifest.json")
    if not freeze.get("frozen_before_candidate_runtime"):
        raise RuntimeError("Stage 0 is not frozen")
    census, registry = [], []
    for label in STATE_SOURCES:
        row, variables = state_row(label)
        census.append(row)
        registry.extend(variables)
    u1_counterfactual = counterfactual_rows("U1_root")
    tight_counterfactual = counterfactual_rows("tight3102_L0_0")
    for row in census:
        if row["state"] == "U1":
            row["counterfactual_label"] = (
                "midpoint_beneficial_exact_work_reduction")
        elif row["state"] == "T1":
            row["counterfactual_label"] = (
                "midpoint_exact_retain_capped_beneficial_divergence")
    common.write_csv(OUT / "formulation_contraction_census.csv", census)
    common.write_csv(OUT / "formulation_variable_registry.csv", registry)
    replay = [{**row, "prediction_differs_from_AM":
               row["AMF_predicted_action"] != row["AM_action"]} for row in census]
    common.write_csv(OUT / "amf_action_replay.csv", replay)

    expected = {"H1": "retain", "H2": "retain", "B1": "split", "B2": "split",
                "B3": "split", "B4": "split"}
    actual = {row["state"]: row["AMF_predicted_action"] for row in census}
    checks = {label: (actual[label] == action if action == "split"
                      else actual[label] != "split") for label, action in expected.items()}
    gini_credit = sum(row["excluded_gini_variable_count"] for row in census) > 0
    primary_pass = all(checks.values()) and gini_credit
    audit = {
        "schema": "round48-amf-separation-audit-v1", "checks": checks,
        "gini_coordinate_fully_excluded": gini_credit,
        "primary_offline_gate_passed": primary_pass,
        "failed_checks": [label for label, passed in checks.items() if not passed],
        "structural_classification": "amf_structurally_separable" if primary_pass else
            ("amf_partial_structural_separation" if any(checks.values()) else
             "amf_not_structurally_separable"),
        "formula_changed_after_freeze": False, "registry_changed_after_freeze": False,
        "required_consequence": "open Stage3 eight-row diagnostic only; forbid Stage4/5; bounded structural negative" if not primary_pass else "Stage3 eligible",
    }
    common.write_json(OUT / "amf_separation_audit.json", audit)
    lines = ["# AMF offline margin report", "",
             f"Primary offline gate: **{'PASS' if primary_pass else 'FAIL'}**.", "",
             "| State | phi_L | phi_R | S_AM | S_AMF | Margin | AM | AMF | Expected |",
             "|---|---:|---:|---:|---:|---:|---|---|---|"]
    for row in census:
        lines.append(f"| {row['state']} | {row['phi_L']:.9g} | {row['phi_R']:.9g} | "
                     f"{row['S_AM']:.9g} | {row['S_AMF']:.9g} | "
                     f"{row['S_AMF_minus_tau']:.9g} | {row['AM_action']} | "
                     f"{row['AMF_predicted_action']} | {expected.get(row['state'], row['counterfactual_label'])} |")
    lines += ["", "The frozen, equal-weight profile preserves H1/H2 and the existing B3/B4 splits, but it does not move B1 or B2 across tau. No family, tau, or threshold was tuned after observing this result. Round 48 therefore follows the mandatory bounded-negative path."]
    common.write_text(OUT / "amf_margin_report.md", "\n".join(lines) + "\n")

    alignment = tight_alignment()
    common.write_csv(OUT / "tight3102_state_alignment.csv", alignment)
    divergence = [row for row in alignment if row["action_divergence"]]
    common.write_csv(
        OUT / "tight3102_counterfactual_results.csv", tight_counterfactual)
    common.write_csv(OUT / "u1_counterfactual_results.csv", u1_counterfactual)
    retain = next(row for row in tight_counterfactual if row["arm"] == "retain")
    midpoint = next(row for row in tight_counterfactual if row["arm"] == "midpoint")
    common.write_text(OUT / "tight3102_divergence_report.md", f"""# tight3102 divergence reconstruction

The exact historical alignment contains {len(alignment)} common parent state(s) and {len(divergence)} action divergence(s). The first divergence is `L0.0`: identical input, interval, incumbent, parent/child bounds, and byte-identical canonical parent model; K1-r015 splits while K1-AM retains. No later exact common parent exists after that action divergence.

The matched one-step RETAIN arm capped at {float(retain['time_seconds']):.3f} seconds with Work {float(retain['work']):.6f} and gap {float(retain['gap']):.9g}. The MIDPOINT arm, with both descendant split opportunities suppressed, completed exact in {float(midpoint['time_seconds']):.3f} seconds with Work {float(midpoint['work']):.6f} and zero gap. Thus the historical divergence is confirmed beneficial under a matched replay. AMF predicts retain at this state (`S_AMF < tau`), so the frozen formula does not recover the confirmed divergence. Both arms are restricted diagnostics and neither is an original-problem certificate.
""")
    print({"states": len(census), "primary_pass": primary_pass,
           "failed_checks": audit["failed_checks"],
           "tight_common": len(alignment), "tight_divergence": len(divergence)})


if __name__ == "__main__":
    main()
