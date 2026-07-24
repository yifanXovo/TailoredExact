#!/usr/bin/env python3
"""Unit tests for strict Round 30 trace/AUC semantics."""

from __future__ import annotations

import csv
import importlib.util
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/round30_bound_trace.py"
SPEC = importlib.util.spec_from_file_location("round30_bound_trace", MODULE_PATH)
assert SPEC and SPEC.loader
TRACE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = TRACE
SPEC.loader.exec_module(TRACE)


def write_trace(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=TRACE.REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def row(t: float, event: str, active: object, other: object,
        global_lb: float, open_count: int, closed_count: int) -> dict[str, object]:
    return {
        "process_elapsed_seconds": t,
        "exact_phase_elapsed_seconds": t,
        "event_type": event,
        "active_leaf": "L0" if active != "" else "",
        "active_leaf_valid_lower_bound": active,
        "other_open_leaf_min_valid_lower_bound": other,
        "valid_global_lower_bound": global_lb,
        "verified_global_upper_bound": 10.0,
        "open_relevant_leaf_count": open_count,
        "closed_relevant_leaf_count": closed_count,
        "event_source": "unit_test_observed_event",
    }


def main() -> int:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        good = root / "good.csv"
        write_trace(good, [
            row(0.0, "exact_tree_initialization", 0.0, "", 0.0, 2, 0),
            row(1.0, "parent_lp_completion", 2.0, 0.0, 0.0, 2, 0),
            row(2.0, "partial_native_mip_bound_improvement",
                4.0, 3.0, 3.0, 2, 0),
            row(3.0, "interruption", 4.0, 3.0, 3.0, 2, 0),
            row(3.1, "finalization", 3.0, "", 3.0, 2, 0),
        ])
        audit = TRACE.audit_external_trace(good)
        assert audit.complete, audit.reason
        auc = TRACE.observed_step_auc(
            audit.observations, common_verified_upper_bound=10.0)
        assert auc["observed_end_process_seconds"] == 3.1
        assert auc["normalized_proof_progress_auc"] > 0.0

        nonmonotone = root / "nonmonotone.csv"
        write_trace(nonmonotone, [
            row(0.0, "exact_tree_initialization", 1.0, "", 1.0, 1, 0),
            row(1.0, "parent_lp_completion", 0.5, "", 0.5, 1, 0),
            row(2.0, "interruption", 0.5, "", 0.5, 1, 0),
            row(2.1, "finalization", 0.5, "", 0.5, 1, 0),
        ])
        assert "global_bound_nonmonotone" in (
            TRACE.audit_external_trace(nonmonotone).reason)

        wrong_min = root / "wrong_min.csv"
        write_trace(wrong_min, [
            row(0.0, "exact_tree_initialization", 0.0, "", 0.0, 1, 0),
            row(1.0, "parent_lp_completion", 3.0, 2.0, 3.0, 1, 0),
            row(2.0, "interruption", 3.0, "", 3.0, 1, 0),
            row(2.1, "finalization", 3.0, "", 3.0, 1, 0),
        ])
        assert "active_other_min_mismatch" in (
            TRACE.audit_external_trace(wrong_min).reason)

        endpoint_only = root / "endpoint_only.csv"
        write_trace(endpoint_only, [
            row(0.0, "exact_tree_initialization", 0.0, "", 0.0, 1, 0),
            row(3.0, "finalization", 0.0, "", 0.0, 1, 0),
        ])
        endpoint_audit = TRACE.audit_external_trace(endpoint_only)
        assert not endpoint_audit.complete
        assert endpoint_audit.reason == "open_finalization_without_interruption"

        exact_empty = root / "exact_empty.csv"
        write_trace(exact_empty, [
            row(0.0, "exact_tree_initialization", 0.0, "", 0.0, 0, 1),
            row(0.1, "finalization", 10.0, "", 10.0, 0, 1),
        ])
        assert TRACE.audit_external_trace(exact_empty).complete

    print("round30_trace_tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
