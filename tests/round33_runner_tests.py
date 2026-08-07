#!/usr/bin/env python3
"""Runner, timing, and evidence-contract checks for Round 33."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import round33_common as common  # noqa: E402
import run_round33_experiments as runner  # noqa: E402


class Checks:
    def __init__(self) -> None:
        self.count = 0

    def require(self, value: bool, message: str) -> None:
        self.count += 1
        if not value:
            raise AssertionError(message)


def main() -> int:
    checks = Checks()
    (ROOT / "build_round33").mkdir(parents=True, exist_ok=True)
    checks.require(
        common.process_entry_time({
            "runtime_seconds": 2.0,
            "final_process_wall_time_seconds": 3.5,
        }) == 3.5,
        "primary timing must use process-entry field")
    checks.require(
        common.process_entry_time({"runtime_seconds": 2.0}) == 2.0,
        "legacy fallback timing mismatch")
    required_p = common.required_artifacts("P-GRB", Path("run"))
    required_c = common.required_artifacts("C6-FROZEN", Path("run"))
    checks.require(any(path.name == "canonical.lp" for path in required_p),
                   "plain canonical model must be retained")
    checks.require(any(path.name == "global_bound_trace.csv"
                       for path in required_c), "C6 trace must be retained")
    checks.require(any(path.name == "native_target_ledger.csv"
                       for path in required_c), "C6 targets must be retained")

    with tempfile.TemporaryDirectory(dir=ROOT / "build_round33") as raw:
        directory = Path(raw)
        payload = directory / "evidence.bin"
        payload.write_bytes(b"round33-evidence")
        inventory = runner.artifact_inventory(directory)
        checks.require(len(inventory) == 1, "artifact inventory count mismatch")
        checks.require(inventory[0]["bytes"] == len(b"round33-evidence"),
                       "artifact byte count mismatch")
        checks.require(inventory[0]["sha256"] == common.sha256(payload),
                       "artifact checksum mismatch")
        runner.write_json(directory / "atomic.json", {"round_id": 33})
        checks.require(json.loads((directory / "atomic.json").read_text())[
            "round_id"] == 33, "atomic JSON write failed")

    matrix = common.csv_rows(common.MATRIX)
    checks.require(all(row["emergency_watchdog_seconds"] == "3690"
                       for row in matrix), "watchdog separation mismatch")
    checks.require(all(row["shutdown_margin_seconds"] == "15"
                       for row in matrix), "shutdown margin mismatch")
    checks.require(all(row["repetition"] in {"primary", "repeat1"}
                       for row in matrix), "repetition metadata missing")
    runner_text = (ROOT / "scripts/run_round33_experiments.py").read_text(
        encoding="utf-8")
    checks.require("algorithmic_solve_state_resumed" in runner_text,
                   "solve-state resume disclaimer missing")
    checks.require("result_json_flush_verified_after_process_exit" in
                   runner_text, "result flush audit missing")
    checks.require("completion_marker.json" in runner_text,
                   "atomic completion marker missing")
    checks.require("artifact_manifest_sha256" in runner_text,
                   "checksum resume gate missing")
    checks.require("GRB_LICENSE_FILE" in runner_text,
                   "licensed child environment gate missing")
    checks.require("E:\\gurobi" not in runner_text,
                   "license path must not be serialized")
    analyzer = (ROOT / "scripts/analyze_round33.py").read_text(
        encoding="utf-8")
    checks.require("final_process_wall_time_seconds" not in analyzer or
                   "process_entry_time" in analyzer,
                   "analyzer must use shared process-entry timing helper")
    checks.require("speedup_p_grb_over_c6" in analyzer,
                   "certificate speedup calculation missing")
    checks.require("no_post_final_extension" in analyzer,
                   "trace extension audit missing")
    print(f"Round33RunnerTests: {checks.count} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
