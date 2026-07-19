#!/usr/bin/env python3
"""Permanent external-data regression for the Round 23 feasibility witness."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import round23_moderate4301_forensic as forensic  # noqa: E402


INSTANCE = ROOT / "reference/heldout_round22/V20_M3/moderate_seed4301.txt"
ROUND22 = ROOT / "results/gf_global_gini_tree_unified_validation_round"
HGA = ROUND22 / "raw/stage4__moderate_seed4301__s0__900s__dense_on.json"
PLAIN = ROUND22 / "raw/stage4__moderate_seed4301__plain__900s__dense_on.json"
ROOT_LP = ROUND22 / (
    "runs/stage4__moderate_seed4301__s0__900s__dense_on/global_root.lp.gz"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    instance = forensic.parse_instance(INSTANCE)
    hga = json.loads(HGA.read_text(encoding="utf-8"))
    plain = json.loads(PLAIN.read_text(encoding="utf-8"))
    kwargs = {
        "total_time": 3600.0,
        "pickup_time": 60.0,
        "drop_time": 60.0,
        "lam": 0.15,
    }
    hga_check = forensic.independent_verify(instance, hga["routes"], **kwargs)
    plain_check = forensic.independent_verify(instance, plain["routes"], **kwargs)
    require(hga_check["valid"], f"external HGA witness invalid: {hga_check['errors']}")
    require(plain_check["valid"],
            f"external plain witness invalid: {plain_check['errors']}")

    canonical = forensic.symmetry_canonical_routes(instance, hga["routes"])
    complete = forensic.complete_values(instance, canonical, hga_check)
    columns, rows, unsupported = forensic.complete_extension_audit(
        forensic.read_lp(ROOT_LP), complete)
    require(not unsupported, f"unsupported retained root columns: {unsupported}")
    require(all(row["mapped"] for row in columns), "unmapped root-model column")
    require(all(row["lower_bound_satisfied"] for row in columns),
            "root-model lower bound failure")
    require(all(row["upper_bound_satisfied"] for row in columns),
            "root-model upper bound failure")
    require(all(row["integrality_satisfied"] for row in columns),
            "root-model integrality failure")
    require(max(row["scaled_violation"] for row in rows) <= 1e-9,
            "retained feasible witness violates the actual root model")
    print("Round23Moderate4301ForensicTests: 2 witnesses and root extension passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
