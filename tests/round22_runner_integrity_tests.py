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
    assert nominal["native_monotonicity_is_diagnostic_only"] is True
    assert nominal["lower_bound_nondecreasing"] is False
    assert nominal["lower_bound_negative_step_count"] == 1
    assert abs(float(nominal["lower_bound_max_negative_step"]) - 6e-7) < 1e-15
    assert nominal["incumbent_nonincreasing"] is False

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
    assert material["error_count"] == 0, material
    assert material["lower_bound_negative_step_count"] == 1
    assert material["incumbent_positive_step_count"] == 1

    structural = audit([
        {"observation_time_seconds": 1, "native_best_bound": 0.5,
         "native_incumbent": 1.0, "processed_nodes": 2,
         "retention_trigger": "first_observation"},
        {"observation_time_seconds": 1, "native_best_bound": 0.4,
         "native_incumbent": 1.1, "processed_nodes": 1,
         "retention_trigger": "heartbeat"},
        {"observation_time_seconds": 3, "native_best_bound": 0.59,
         "native_incumbent": 0.9, "processed_nodes": 3,
         "retention_trigger": "solver_final"},
    ])
    assert structural["error_count"] == 2, structural
    assert "timestamp_not_strict" in str(structural["errors"])
    assert "final_bound_json_mismatch" in str(structural["errors"])
    assert structural["processed_nodes_negative_step_count"] == 1

    with tempfile.TemporaryDirectory() as directory:
        raw = Path(directory) / "raw_progress.csv"
        with raw.open("w", encoding="utf-8", newline="") as stream:
            fields = ("observation_time_seconds", "observation_source",
                      "callback_context", "retention_trigger")
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            for sequence in range(20):
                writer.writerow({
                    "observation_time_seconds": 0.5 + 5.0 * sequence,
                    "observation_source":
                        "cplex_generic_relaxation_read_only_progress",
                    "callback_context": "relaxation",
                    "retention_trigger": "heartbeat",
                })
        checkpoints = [
            {"record_type": "checkpoint", "checkpoint_seconds": checkpoint,
             "freshness": "fresh" if checkpoint not in (5, 45, 120) else "stale"}
            for checkpoint in (1, 2, 5, 10, 15, 20, 30, 45, 60, 90, 120)
        ]
        quality = runner.stage1_dense_quality(
            runner.RunSpec("stage1", "V12_M2", "S0", 120),
            {"raw_progress": raw}, checkpoints)
        assert quality == [], quality
        checkpoints[5]["freshness"] = "stale"
        quality = runner.stage1_dense_quality(
            runner.RunSpec("stage1", "V12_M2", "S0", 120),
            {"raw_progress": raw}, checkpoints)
        assert any("horizon_fresh_checkpoints" in item for item in quality), quality

    print("round22 runner integrity tests: 5 groups passed")


if __name__ == "__main__":
    main()
