#!/usr/bin/env python3
"""Round 32 telemetry and checksum-resume regression tests."""

from __future__ import annotations

import csv
import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_round32_experiments as runner  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_complete(
        run_dir: Path,
        row: dict[str, str],
        item: dict[str, str],
        manifest: dict[str, str]) -> None:
    run_dir.mkdir(parents=True)
    for path, text in (
        (run_dir / "command.json", "{}\n"),
        (run_dir / "result.json", json.dumps({"status": "ok"}) + "\n"),
        (run_dir / "process_phases.csv", "phase,status\nx,complete\n"),
        (run_dir / "progress.csv", "seconds,lower_bound\n0,0\n"),
    ):
        runner.write_text_atomic(path, text)
    artifacts = runner.artifact_inventory(run_dir)
    artifact_manifest = run_dir / "artifact_manifest.csv"
    runner.write_csv_atomic(
        artifact_manifest, artifacts, ["path", "bytes", "sha256"])
    marker = {
        "run_id": row["run_id"],
        "source_commit": manifest["source_commit"],
        "protocol_sha256": manifest["protocol_sha256"],
        "instance_sha256": item["sha256"],
        "executable_sha256": manifest["gurobi_executable_sha256"],
        "artifact_manifest_sha256": runner.sha256(artifact_manifest),
        "completed": True,
    }
    runner.write_json_atomic(run_dir / "completion_marker.json", marker)


def main() -> int:
    source = (
        ROOT / "src" / "PaperExternalGiniTree.cpp"
    ).read_text(encoding="utf-8")
    start = source.index("auto writeGlobalTrace =")
    finish = source.index("auto stopAtDeadline =", start)
    trace_block = source[start:finish]
    require(
        "global_bound = std::min(global_bound, verified_ub);" in trace_block,
        "trace aggregate does not include the verified incumbent")
    require(
        trace_block.count("global_bound = std::min(global_bound, verified_ub);")
        == 1,
        "trace clamp must be one general telemetry aggregation")
    require(
        "scheduler.mergeValidLowerBound" not in trace_block,
        "trace writer unexpectedly mutates scheduler bounds")

    runner_source = (
        ROOT / "scripts" / "run_round32_experiments.py"
    ).read_text(encoding="utf-8")
    require(
        "gurobi.lic" not in runner_source.lower(),
        "runner embeds a license location")
    require(
        'os.environ["GRB_LICENSE_FILE"]' not in runner_source
        and "os.environ.get(\"GRB_LICENSE_FILE\")" not in runner_source,
        "runner reads or serializes the license environment value")
    require(
        "WATCHDOG_SEPARATION = 90" in runner_source
        and "SHUTDOWN_MARGIN = 15" in runner_source,
        "fixed deadline separation is not frozen")
    require(
        '"baseline_round31_run_id", "repetition", "category"' in runner_source,
        "frozen matrix discriminators are not projected to row evidence")

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        run_dir = root / "runs" / "row"
        row = {"run_id": "row", "arm": "P-GRB", "stage_id": "test"}
        item = {"sha256": "instance-hash"}
        manifest = {
            "source_commit": "source",
            "protocol_sha256": "protocol",
            "gurobi_executable_sha256": "executable",
            "cplex_executable_sha256": "cplex",
        }
        make_complete(run_dir, row, item, manifest)
        valid, reason = runner.completion_is_valid(
            run_dir, row, item, manifest)
        require(valid, f"valid completed row rejected: {reason}")

        (run_dir / "progress.csv").write_text(
            "seconds,lower_bound\n0,1\n", encoding="utf-8")
        valid, reason = runner.completion_is_valid(
            run_dir, row, item, manifest)
        require(
            not valid and reason.startswith("artifact_checksum_mismatch:"),
            f"artifact tampering not detected: {reason}")

        original_out = runner.OUT
        original_invalidated = runner.INVALIDATED
        original_log = runner.INVALIDATION_LOG
        original_root = runner.ROOT
        try:
            runner.ROOT = root
            runner.OUT = root
            runner.INVALIDATED = root / "invalidated_rows"
            runner.INVALIDATION_LOG = root / "runner_invalidations.csv"
            runner.invalidate_run(run_dir, row, reason)
            preserved = list(runner.INVALIDATED.iterdir())
            require(len(preserved) == 1, "invalidated row was not preserved")
            require(
                (preserved[0] / "invalidation_record.json").is_file(),
                "preserved row has no invalidation reason")
            records = list(csv.DictReader(
                runner.INVALIDATION_LOG.open(
                    newline="", encoding="utf-8")))
            require(
                len(records) == 1
                and records[0]["algorithmic_solve_state_resumed"] == "false",
                "invalidation audit misclaims algorithmic resume")
        finally:
            runner.ROOT = original_root
            runner.OUT = original_out
            runner.INVALIDATED = original_invalidated
            runner.INVALIDATION_LOG = original_log

        target = root / "atomic.json"
        runner.write_json_atomic(target, {"complete": True})
        require(
            json.loads(target.read_text(encoding="utf-8"))["complete"],
            "atomic JSON did not parse")
        require(
            not target.with_suffix(".json.tmp").exists(),
            "atomic temporary file was left behind")

    print("Round32RunnerTraceTests: 15 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
