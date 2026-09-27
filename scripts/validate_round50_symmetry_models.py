#!/usr/bin/env python3
"""Validate Round 50 symmetry candidate LP deltas and representative rows."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

import audit_round50_cut_formulation as audit


def split_lp(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    before, rest = text.split("Subject To\n", 1)
    _, after = rest.split("Bounds\n", 1)
    return before, after


def signature(row: dict[str, object]) -> tuple[object, ...]:
    return row["exact_signature"]


def valid_v0_row(row: dict[str, object], vehicle_a: int,
                 vehicle_b: int, stations: int) -> bool:
    coefficients = row["coefficients"]
    expected = {f"z_{vehicle_a}_{i}": 1.0 for i in range(1, stations + 1)}
    expected.update({f"z_{vehicle_b}_{i}": -1.0
                     for i in range(1, stations + 1)})
    return row["sense"] == ">=" and abs(float(row["rhs"])) <= 1e-12 and coefficients == expected


def valid_candidate_row(row: dict[str, object], vehicle_a: int,
                        vehicle_b: int, stations: int,
                        policy: str) -> bool:
    coefficients = row["coefficients"]
    expected = {}
    for i in range(1, stations + 1):
        coefficient = float(i) if policy == "route-start-order" else float(i - (stations + 1))
        expected[f"x_{vehicle_a}_0_{i}"] = coefficient
        expected[f"x_{vehicle_b}_0_{i}"] = -coefficient
    return row["sense"] == "<=" and abs(float(row["rhs"])) <= 1e-12 and coefficients == expected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-root", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--baseline-policy", default="interval-mip-v0")
    parser.add_argument("--candidate-policy", required=True)
    parser.add_argument("--symmetry-policy", required=True,
                        choices=["route-start-order", "used-first-route-start-order"])
    parser.add_argument("--states", required=True)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    manifest = {row["state_id"]: row for row in csv.DictReader(
        args.manifest.open(newline="", encoding="utf-8-sig"))}
    fields = [
        "candidate_policy", "state_id", "vehicle_count", "station_count",
        "identical_vehicle_capacities", "objective_section_identical",
        "bounds_and_types_identical", "baseline_rows", "candidate_rows",
        "removed_cardinality_rows", "added_route_start_rows",
        "all_non_symmetry_rows_identical", "candidate_row_formula_valid",
        "optimal_representative_preserved", "status", "failure_reason",
    ]
    output = []
    for state in [value.strip() for value in args.states.split(",") if value.strip()]:
        input_path = audit.ROOT / manifest[state]["input_path"]
        header = input_path.read_text(encoding="utf-8").splitlines()[0]
        match = re.fullmatch(r"(\d+)\s+(\d+)\s+\[([^]]+)\]", header.strip())
        if not match:
            raise RuntimeError(f"unparsed instance header for {state}")
        stations = int(match.group(1))
        vehicles = int(match.group(2))
        capacities = [int(value.strip()) for value in match.group(3).split(",")]
        identical = len(capacities) == vehicles and len(set(capacities)) == 1
        base_dir = args.baseline_root / f"{state}__{args.baseline_policy}"
        candidate_dir = args.candidate_root / f"{state}__{args.candidate_policy}"
        base_lp = base_dir / "canonical_model.lp"
        candidate_lp = candidate_dir / "canonical_model.lp"
        base_before, base_after = split_lp(base_lp)
        cand_before, cand_after = split_lp(candidate_lp)
        base_rows = audit.parse_model(base_lp)
        candidate_rows = audit.parse_model(candidate_lp)
        base_map = {signature(row): row for row in base_rows}
        candidate_map = {signature(row): row for row in candidate_rows}
        base_counter = Counter(signature(row) for row in base_rows)
        candidate_counter = Counter(signature(row) for row in candidate_rows)
        removed_signatures = list((base_counter - candidate_counter).elements())
        added_signatures = list((candidate_counter - base_counter).elements())
        expected_count = max(0, vehicles - 1) if identical else 0
        removed_valid = len(removed_signatures) == expected_count
        added_valid = len(added_signatures) == expected_count
        for k, sig in enumerate(removed_signatures):
            removed_valid = removed_valid and valid_v0_row(
                base_map[sig], k, k + 1, stations)
        for k, sig in enumerate(added_signatures):
            added_valid = added_valid and valid_candidate_row(
                candidate_map[sig], k, k + 1, stations,
                args.symmetry_policy)
        non_symmetry_identical = (
            len(base_rows) == len(candidate_rows) and
            len(removed_signatures) == len(added_signatures) == expected_count)
        representative = identical and removed_valid and added_valid
        status = (
            base_before == cand_before and base_after == cand_after and
            non_symmetry_identical and representative)
        output.append({
            "candidate_policy": args.candidate_policy, "state_id": state,
            "vehicle_count": vehicles, "station_count": stations,
            "identical_vehicle_capacities": str(identical).lower(),
            "objective_section_identical": str(base_before == cand_before).lower(),
            "bounds_and_types_identical": str(base_after == cand_after).lower(),
            "baseline_rows": len(base_rows), "candidate_rows": len(candidate_rows),
            "removed_cardinality_rows": len(removed_signatures),
            "added_route_start_rows": len(added_signatures),
            "all_non_symmetry_rows_identical": str(non_symmetry_identical).lower(),
            "candidate_row_formula_valid": str(added_valid).lower(),
            "optimal_representative_preserved": str(representative).lower(),
            "status": "pass" if status else "fail",
            "failure_reason": "none" if status else "symmetry_delta_validation_failed",
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    if any(row["status"] != "pass" for row in output):
        raise RuntimeError("symmetry model validation failed")
    print(f"validated {len(output)} symmetry model deltas for {args.candidate_policy}")


if __name__ == "__main__":
    main()
