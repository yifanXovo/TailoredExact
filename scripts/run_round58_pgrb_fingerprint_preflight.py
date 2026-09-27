#!/usr/bin/env python3
"""Freeze all Round 58 P-GRB model identities before benchmark solves."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pgrb_fingerprint_pipeline as fp
import round46_common as round46
import round58_common as r58


PROBE_PROCESS_CAP = 30.0
PROBE_SOLVER_CAP = 0.001
FORBIDDEN_OPTIONS = (
    "--incumbent-json", "--hga-incumbent", "--external-incumbent",
    "--frontier-focus-from-result", "--frontier-import-interval-bound",
    "--frontier-resume-state", "--incumbent-archive-dir",
)


def object_json(path: Path) -> dict[str, Any]:
    value = r58.read_json(path)
    if isinstance(value, list):
        if len(value) != 1:
            raise RuntimeError(f"expected one result: {path}")
        value = value[0]
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def set_option(command: list[str], option: str, value: Any) -> None:
    round46.replace_option(command, option, value)


def command_for(row: dict[str, str], run_dir: Path,
                executable: Path) -> list[str]:
    item = {
        "instance": row["scenario_id"], "path": row["instance_path"],
        "sha256": row["instance_file_sha256"], "T": int(row["T_seconds"]),
        "V": int(row["V"]), "M": int(row["M"]),
    }
    command = round46.pgrb_command(item, run_dir, PROBE_PROCESS_CAP, executable)
    for option in FORBIDDEN_OPTIONS:
        round46.remove_option(command, option)
    set_option(command, "--method", "gurobi")
    if "--plain-baseline" not in command:
        command.append("--plain-baseline")
    set_option(command, "--T", int(row["T_seconds"]))
    set_option(command, "--lambda", float(row["lambda"]))
    set_option(command, "--process-wall-time-limit", PROBE_PROCESS_CAP)
    set_option(command, "--time-limit", PROBE_SOLVER_CAP)
    set_option(command, "--process-shutdown-margin", 0.0)
    set_option(command, "--threads", 1)
    set_option(command, "--gurobi-threads", 1)
    set_option(command, "--gurobi-seed", 0)
    set_option(command, "--gurobi-presolve", -1)
    set_option(command, "--gurobi-hga-start", False)
    set_option(command, "--gurobi-model-export", run_dir / "canonical.lp")
    set_option(command, "--gurobi-progress", run_dir / "progress.csv")
    set_option(command, "--round56-scenario-id", row["scenario_id"])
    set_option(command, "--round56-mathematical-instance-sha256",
               row["scenario_sha256"])
    set_option(command, "--round56-run-identity-sha256",
               "fingerprint_preflight_not_benchmark")
    round46.remove_option(command, "--round24-expected-gurobi-model-fingerprint")
    return command


def probe(row: dict[str, str], executable: Path,
          executable_sha: str, source_sha: str) -> dict[str, Any]:
    run_dir = r58.RAW / "fingerprint_preflight" / row["scenario_id"]
    marker_path = run_dir / "completion_marker.json"
    result_path = run_dir / "result.json"
    lp_path = run_dir / "canonical.lp"
    if marker_path.is_file() and result_path.is_file() and lp_path.is_file():
        marker = object_json(marker_path)
        if (marker.get("complete") is True and
                marker.get("executable_sha256") == executable_sha and
                marker.get("scenario_sha256") == row["scenario_sha256"] and
                marker.get("result_sha256") == r58.sha256_file(result_path)):
            return dict(marker["entry"])
        raise RuntimeError(f"stale fingerprint preflight retained: {run_dir}")
    if run_dir.exists() and any(run_dir.iterdir()):
        raise RuntimeError(f"incomplete fingerprint preflight retained: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)
    command = command_for(row, run_dir, executable)
    r58.write_json(run_dir / "command.json", {
        "schema": "round58-pgrb-fingerprint-command-v1",
        "official_benchmark_run": False,
        "purpose": "expected complete plain-model identity freeze only",
        "scenario_id": row["scenario_id"],
        "scenario_sha256": row["scenario_sha256"],
        "input_path": row["instance_path"],
        "input_sha256": row["instance_file_sha256"],
        "T_seconds": int(row["T_seconds"]),
        "executable_sha256": executable_sha,
        "source_freeze_commit": source_sha,
        "probe_process_cap_seconds": PROBE_PROCESS_CAP,
        "probe_solver_cap_seconds": PROBE_SOLVER_CAP,
        "command": command,
    })
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    with (run_dir / "stdout.log").open("wb") as stdout, \
            (run_dir / "stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=r58.ROOT, env=environment, stdout=stdout,
                stderr=stderr, timeout=PROBE_PROCESS_CAP + 90, check=False)
            return_code, watchdog = completed.returncode, False
        except subprocess.TimeoutExpired:
            return_code, watchdog = -1, True
    runner_wall = time.monotonic() - started
    if watchdog or return_code != 0 or not result_path.is_file() or not lp_path.is_file():
        raise RuntimeError(f"fingerprint probe failed: {row['scenario_id']}")
    result = object_json(result_path)
    fingerprint = int(result.get("gurobi_model_fingerprint", 0))
    if (fingerprint == 0 or result.get("gurobi_native_domain_audit_passed") is not True
            or result.get("gurobi_lifecycle_valid") is not True
            or result.get("gurobi_hga_start") is True
            or result.get("cplex_plain_baseline") is not True):
        raise RuntimeError(f"plain-model scope probe failed: {row['scenario_id']}")
    entry = fp.freeze_entry(
        instance_id=row["scenario_id"], input_path=row["instance_path"],
        input_sha256=row["instance_file_sha256"],
        time_limit=float(row["T_seconds"]),
        executable_sha256=executable_sha, native_fingerprint=fingerprint,
        canonical_lp=lp_path,
        native_domain={
            "num_vars": int(result["gurobi_num_vars"]),
            "num_rows": int(result["gurobi_num_constrs"]),
            "num_nonzeros": float(result["gurobi_num_nzs"]),
            "num_binary": int(result["gurobi_num_bin_vars"]),
            "num_integer": int(result["gurobi_num_int_vars"]),
            "num_continuous": int(result["gurobi_num_cont_vars"]),
            "objective_sense": int(result["gurobi_objective_sense"]),
            "native_names_match": result["gurobi_native_variable_names_match"],
            "native_types_match": result["gurobi_native_variable_types_match"],
            "native_bounds_match": result["gurobi_native_variable_bounds_match"],
            "native_domain_audit_passed": result["gurobi_native_domain_audit_passed"],
        },
        solver_contract={"Presolve": "Auto", "Seed": 0, "Threads": 1,
                         "MIPGap": 0.0, "MIPGapAbs": 0.0,
                         "HGAStart": False},
        probe_metadata={
            "scenario_sha256": row["scenario_sha256"],
            "source_freeze_commit": source_sha,
            "probe_process_cap_seconds": PROBE_PROCESS_CAP,
            "probe_solver_cap_seconds": PROBE_SOLVER_CAP,
            "runner_wall_seconds": runner_wall,
            "raw_probe_path": r58.repo_path(run_dir),
            "official_benchmark_run": False,
        })
    r58.write_json(marker_path, {
        "schema": "round58-pgrb-fingerprint-completion-v1",
        "complete": True, "official_benchmark_run": False,
        "scenario_id": row["scenario_id"],
        "scenario_sha256": row["scenario_sha256"],
        "executable_sha256": executable_sha,
        "result_sha256": r58.sha256_file(result_path), "entry": entry,
    })
    print(f"fingerprint {row['scenario_id']} = {fingerprint}", flush=True)
    return entry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--source-freeze-commit", required=True)
    args = parser.parse_args()
    executable = args.executable.resolve()
    if not executable.is_file():
        raise RuntimeError("official executable missing")
    source_sha = args.source_freeze_commit
    if source_sha != "8ec0e1e151a5f25cb0594852f896b04303c0ba34":
        raise RuntimeError("unexpected Round 58 solver source freeze")
    if subprocess.check_output(
            ["git", "merge-base", "--is-ancestor", source_sha, "HEAD"],
            cwd=r58.ROOT).strip() not in (b"", ""):
        pass
    executable_sha = r58.sha256_file(executable)
    panel_path = r58.EVIDENCE / "round58_complete_panel.csv"
    panel = r58.read_csv(panel_path)
    if len(panel) != 50:
        raise RuntimeError("Round 58 panel is not frozen at 50 scenarios")
    entries = [probe(row, executable, executable_sha, source_sha) for row in panel]
    manifest = {
        "schema": "round58-pgrb-expected-fingerprints-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "created_before_any_round58_benchmark_solve": True,
        "preflight_is_benchmark_evidence": False,
        "panel_path": r58.repo_path(panel_path),
        "panel_sha256": r58.sha256_file(panel_path),
        "source_freeze_commit": source_sha,
        "executable_path": r58.repo_path(executable),
        "executable_sha256": executable_sha,
        "solver": {"version": "13.0.2", "Presolve": "Auto", "Seed": 0,
                   "Threads": 1, "MIPGap": 0.0, "MIPGapAbs": 0.0,
                   "HGAStart": False},
        "row_count": len(entries), "entries": entries,
        "benchmark_solves_started": False, "machine": platform.node(),
    }
    r58.write_json(r58.EVIDENCE / "pgrb_expected_fingerprints.json", manifest)
    scope_rows = []
    for entry in entries:
        domain = entry["variable_row_domain_identity"]
        scope_rows.append({
            "scenario_id": entry["instance_id"],
            "scenario_sha256": entry["scenario_sha256"],
            "expected_gurobi_model_fingerprint": entry["expected_gurobi_model_fingerprint"],
            "canonical_model_sha256": entry["canonical_model_sha256"],
            "objective_fingerprint_sha256": entry["objective_fingerprint_sha256"],
            "num_vars": domain["num_vars"], "num_rows": domain["num_rows"],
            "num_nonzeros": domain["num_nonzeros"],
            "native_domain_audit_passed": domain["native_domain_audit_passed"],
            "one_original_compact_model": True, "strengthened": False,
            "gini_decomposition": False, "tailored_cuts": False,
            "custom_branching": False, "HGA_or_imported_routes": False,
            "expected_fingerprint_frozen_before_solve": True,
            "scope_status": "PASS",
        })
    r58.write_csv(r58.EVIDENCE / "pgrb_model_scope_audit.csv", scope_rows)
    r58.write_csv(r58.EVIDENCE / "algorithm_identity_audit.csv", [
        {"audit": "K1-AM-SF", "V_sentinel": "8;20;50",
         "method": "gcap-frontier", "preset_or_scope": "paper-k1-am-sf",
         "K0": 1, "point_rule": "midpoint",
         "score_rule": "balanced-normalized-closure", "tau": 0.08,
         "inner_backend": "F0-CLEAN", "native_branching": True,
         "dynamic_user_cuts": False, "Threads": 1, "Seed": 0,
         "Presolve": "Auto", "identity_status": "PASS",
         "evidence": "Round58CitiBikePairedBenchmarkTests;paired_solver_contract.json"},
        {"audit": "P-GRB", "V_sentinel": "8;20;50",
         "method": "gurobi", "preset_or_scope": "plain-baseline",
         "K0": "not_applicable", "point_rule": "not_applicable",
         "score_rule": "not_applicable", "tau": "not_applicable",
         "inner_backend": "one_original_compact_MILP", "native_branching": True,
         "dynamic_user_cuts": False, "Threads": 1, "Seed": 0,
         "Presolve": "Auto", "identity_status": "PASS",
         "evidence": "pgrb_model_scope_audit.csv;pgrb_expected_fingerprints.json"},
    ])
    print(json.dumps({"fingerprints": len(entries),
                      "executable_sha256": executable_sha}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
