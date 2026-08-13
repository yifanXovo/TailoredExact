#!/usr/bin/env python3
"""Run the frozen Round 38 full-panel diagnostic with the audited runner."""

from __future__ import annotations

import round38_experiment_common as common


common.SMOKE_MATRIX = common.OUT / "round38_diagnostic_matrix.csv"
common.SMOKE_FREEZE = common.OUT / "round38_diagnostic_freeze.json"
common.SMOKE_RUNS = common.OUT / "diagnostic_runs"
common.SMOKE_SUMMARY = common.OUT / "diagnostic_run_summary.csv"

import run_round38_smoke as runner  # noqa: E402  (bind paths before import)


runner.LOCK = common.OUT / ".round38_diagnostic_runner.lock"
_smoke_run_one = runner.run_one


def diagnostic_run_one(row, item, freeze):
    """Reuse audited mechanics while labelling diagnostic evidence honestly."""
    marker = _smoke_run_one(row, item, freeze)
    if marker.get("schema") == "round38-smoke-run-v1":
        marker["schema"] = "round38-frozen-stage-run-v1"
        directory = common.SMOKE_RUNS / row["run_id"]
        common.write_json(directory / "completion_marker.json", marker)
        state = common.load_json(directory / "run_state.json")
        state["schema"] = marker["schema"]
        common.write_json(directory / "run_state.json", state)
    return marker


runner.run_one = diagnostic_run_one


if __name__ == "__main__":
    raise SystemExit(runner.main())
