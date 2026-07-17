#!/usr/bin/env python3
"""Deterministic tests for raw Round 22 trajectory-integrity semantics."""

from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import run_gf_global_gini_tree_unified_validation_round as runner  # noqa: E402


FIELDS = (
    "observation_time_seconds", "native_best_bound", "native_incumbent",
    "processed_nodes", "retention_trigger",
)


def audit(rows: list[dict[str, object]]) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as directory:
        raw = Path(directory) / "raw_progress.csv"
        with raw.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader(); writer.writerows(rows)
        return runner.integrity(
            runner.RunSpec("stage2", "V12_M1", "plain", 900),
            {"raw_progress": raw},
            {"native_mip_best_bound_available": True,
             "native_mip_best_bound": 0.6},
        )


def main() -> None:
    nominal = audit([
        {"observation_time_seconds": 1, "native_best_bound": 0.5,
         "native_incumbent": 1.0, "processed_nodes": 0,
         "retention_trigger": "first_observation"},
        {"observation_time_seconds": 2, "native_best_bound": 0.4999994,
         "native_incumbent": 1.0000005, "processed_nodes": 1,
         "retention_trigger": "heartbeat"},
        {"observation_time_seconds": 3, "native_best_bound": 0.6,
         "native_incumbent": 0.9, "processed_nodes": 2,
         "retention_trigger": "solver_final"},
    ])
    assert nominal["error_count"] == 0, nominal
    assert nominal["raw_values_reported_not_repaired"] is True
    assert nominal["lower_bound_nondecreasing"] is False
    assert nominal["lower_bound_no_material_decrease"] is True
    assert nominal["lower_bound_negative_step_count"] == 1
    assert abs(float(nominal["lower_bound_max_negative_step"]) - 6e-7) < 1e-15
    assert nominal["incumbent_nonincreasing"] is False
    assert nominal["incumbent_no_material_increase"] is True

    material = audit([
        {"observation_time_seconds": 1, "native_best_bound": 0.5,
         "native_incumbent": 1.0, "processed_nodes": 0,
         "retention_trigger": "first_observation"},
        {"observation_time_seconds": 2, "native_best_bound": 0.499998,
         "native_incumbent": 1.000002, "processed_nodes": 1,
         "retention_trigger": "heartbeat"},
        {"observation_time_seconds": 3, "native_best_bound": 0.6,
         "native_incumbent": 0.9, "processed_nodes": 2,
         "retention_trigger": "solver_final"},
    ])
    assert material["error_count"] == 2, material
    assert "lower_bound_material_decrease" in str(material["errors"])
    assert "incumbent_material_increase" in str(material["errors"])
    assert material["lower_bound_material_negative_step_count"] == 1
    assert material["incumbent_material_positive_step_count"] == 1
    print("round22 runner integrity tests: 2 groups passed")


if __name__ == "__main__":
    main()
