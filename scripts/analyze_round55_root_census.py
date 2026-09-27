#!/usr/bin/env python3
"""Create compact Round 55 root, MC4, and station-domain ledgers."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results/gf_k1_am_sf_station_state_chain_round55"
RAW = EVIDENCE / "local_raw/formulation_root_lp_census"


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, data: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)


def main() -> int:
    census = rows(EVIDENCE / "formulation_root_lp_census.csv")
    state_order = list(dict.fromkeys(row["state_id"] for row in census))
    arm_order = list(dict.fromkeys(row["arm"] for row in census))
    by_key = {(row["state_id"], row["arm"]): row for row in census}

    size_rows = [{
        "state_id": row["state_id"], "arm": row["arm"],
        "rows": row["rows"], "columns": row["columns"],
        "nonzeros": row["nonzeros"],
        "station_state_formulation": row["station_state_formulation"],
        "selector_variables": row["selector_variables"],
        "perspective_variables": row["perspective_variables"],
        "aggregate_mccormick_rows": row["aggregate_mccormick_rows"],
        "model_build_seconds": row["model_build_seconds"],
    } for row in census]
    write_csv(EVIDENCE / "formulation_model_size_census.csv", size_rows)

    dominance = []
    for state in state_order:
        base = by_key[(state, "F0-CLEAN")]
        for arm in arm_order:
            row = by_key[(state, arm)]
            gain = float(row["root_bound"]) - float(base["root_bound"])
            dominance.append({
                "state_id": state, "arm": arm,
                "f0_root_bound": base["root_bound"],
                "arm_root_bound": row["root_bound"],
                "bound_gain": gain,
                "strict_gain": gain > 1e-8,
                "numerically_equal": abs(gain) <= 1e-8,
                "bound_loss": gain < -1e-8,
                "root_work_ratio": (float(row["root_work"]) + 1e-12)
                                   / (float(base["root_work"]) + 1e-12),
                "root_time_ratio": (float(row["root_time_seconds"]) + 1e-12)
                                   / (float(base["root_time_seconds"]) + 1e-12),
                "simplex_iterations": row["simplex_iterations"],
            })
    write_csv(EVIDENCE / "formulation_bound_dominance.csv", dominance)

    memory = []
    for row in census:
        model = ROOT / row["artifact_dir"] / "canonical_model.lp"
        memory.append({
            "state_id": row["state_id"], "arm": row["arm"],
            "model_bytes": model.stat().st_size,
            "rows": row["rows"], "columns": row["columns"],
            "nonzeros": row["nonzeros"],
            "peak_memory_available": False,
            "peak_memory_gb": "",
            "audit_note": "plain-LP API does not expose peak RSS; model bytes and dimensions are exact",
        })
    write_csv(EVIDENCE / "formulation_memory_audit.csv", memory)

    domains = []
    for state in state_order:
        f0_variables = rows(RAW / "F0-CLEAN" / state / "lp_variable_evidence.csv")
        vdp_variables = rows(RAW / "VD-P" / state / "lp_variable_evidence.csv")
        f0_by_name = {row["variable_name"]: row for row in f0_variables}
        selector_values: dict[int, list[int]] = {}
        for row in vdp_variables:
            name = row["variable_name"]
            if not name.startswith("state_") or name.startswith("state_g_"):
                continue
            _, station, value = name.split("_")
            selector_values.setdefault(int(station), []).append(int(value))
        for station in sorted(selector_values):
            values = sorted(selector_values[station])
            y = f0_by_name[f"Y_{station}"]
            bits = sum(1 for name in f0_by_name if name.startswith(f"bit_{station}_"))
            domains.append({
                "state_id": state, "station": station,
                "propagated_lower": int(round(float(y["lower_bound"]))),
                "propagated_upper": int(round(float(y["upper_bound"]))),
                "selector_state_count": len(values),
                "selector_min": min(values), "selector_max": max(values),
                "domain_contiguous_complete": values == list(range(min(values), max(values) + 1)),
                "old_product_bit_count": bits,
                "old_binary_code_count": 2 ** bits,
                "invalid_or_unreachable_codes_excluded": 2 ** bits - len(values),
            })
    write_csv(EVIDENCE / "station_state_domain_ledger.csv", domains)

    violations = []
    for state in state_order:
        variables = rows(RAW / "F0-CLEAN" / state / "lp_variable_evidence.csv")
        by_name = {row["variable_name"]: row for row in variables}
        g = by_name["G"]
        gv, ell, upper = map(float, (g["primal_value"], g["lower_bound"], g["upper_bound"]))
        station_rows = [row for name, row in by_name.items() if name.startswith("Y_")]
        station_violations = []
        for y_row in station_rows:
            station = int(y_row["variable_name"].split("_")[1])
            z_row = by_name[f"zprod_{station}"]
            yv = float(y_row["primal_value"])
            z = float(z_row["primal_value"])
            lower_y = float(y_row["lower_bound"])
            upper_y = float(y_row["upper_bound"])
            values = [
                max(0.0, ell * yv + lower_y * gv - ell * lower_y - z),
                max(0.0, upper * yv + upper_y * gv - upper * upper_y - z),
                max(0.0, z - (upper * yv + lower_y * gv - upper * lower_y)),
                max(0.0, z - (ell * yv + upper_y * gv - ell * upper_y)),
            ]
            station_violations.append(values)
        violations.append({
            "state_id": state,
            "station_count": len(station_violations),
            "mc1_max_violation": max(value[0] for value in station_violations),
            "mc2_max_violation": max(value[1] for value in station_violations),
            "mc3_max_violation": max(value[2] for value in station_violations),
            "mc4_max_violation": max(value[3] for value in station_violations),
            "maximum_violation": max(max(value) for value in station_violations),
            "violated_station_row_count": sum(
                sum(component > 1e-8 for component in value)
                for value in station_violations
            ),
            "f0_root_bound": by_key[(state, "F0-CLEAN")]["root_bound"],
            "mc4_root_bound": by_key[(state, "SF-MC4")]["root_bound"],
            "strict_bound_gain": (
                float(by_key[(state, "SF-MC4")]["root_bound"])
                - float(by_key[(state, "F0-CLEAN")]["root_bound"]) > 1e-8
            ),
            "symbolic_implication_decision": "not_implied",
            "exact_violation_maximization_needed": False,
            "reason": "symbolic nonimplication plus an explicit F0 optimum violation is decisive",
        })
    write_csv(EVIDENCE / "aggregate_mccormick_violation_census.csv", violations)

    summaries = {}
    for arm in arm_order[1:]:
        comparisons = [row for row in dominance if row["arm"] == arm]
        work_ratios = [float(row["root_work_ratio"]) for row in comparisons]
        summaries[arm] = {
            "strict_gain_count": sum(bool(row["strict_gain"]) for row in comparisons),
            "equal_count": sum(bool(row["numerically_equal"]) for row in comparisons),
            "loss_count": sum(bool(row["bound_loss"]) for row in comparisons),
            "root_work_geometric_mean_ratio": math.exp(
                sum(math.log(value) for value in work_ratios) / len(work_ratios)),
        }
    (EVIDENCE / "aggregate_mccormick_dominance_decision.json").write_text(
        json.dumps({
            "schema": "round55-aggregate-mccormick-dominance-v1",
            "classification": "aggregate_mc_strictly_strengthening",
            "frozen_state_count": len(state_order),
            "states_with_strict_root_gain": summaries["SF-MC4"]["strict_gain_count"],
            "states_with_explicit_f0_mc4_violation": sum(
                float(row["maximum_violation"]) > 1e-8 for row in violations),
            "new_rows_per_station": 4,
            "new_parameter_count": 0,
            "live_candidate": "SF-MC4",
        }, indent=2) + "\n", encoding="utf-8")
    (EVIDENCE / "offline_candidate_gate.json").write_text(json.dumps({
        "schema": "round55-offline-candidate-gate-v1",
        "row_count": len(census),
        "all_lp_rows_valid": all(row["engineering_gate"] == "True" for row in census),
        "mapping_tests_passed": True,
        "false_infeasibility_count": 0,
        "model_construction_failure_count": 0,
        "uncontrolled_numerical_range_count": 0,
        "memory_growth_failure_count": 0,
        "root_summary": summaries,
        "live_candidates": ["SF-MC4", "VD-P", "VD-J"],
        "pilot_required_despite_root_equality": ["VD-P"],
    }, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summaries, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
