#!/usr/bin/env python3
"""Prepare and run the 50-row Round 56 official panel sequentially."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import round46_common as round46
import round56_common as r56
from round56_route_archive import build_package, classify


SOURCE_FREEZE = "75e58521158aba8628ebc9444444ec3841415285"
EXE = r56.ROOT / "build" / "official-round56-paper-dataset-75e585211" / "ExactEBRP.exe"
EXE_SHA256 = "34e992060e3adffd3a7795c2c783672044996edd7234bf7e9f58a662b1c32fea"
CONTRACT = r56.EVIDENCE / "official_solver_parameter_contract.json"
RAW = r56.EVIDENCE / "local_raw" / "official"
RUN_INDEX = RAW / "official_run_index.csv"
FORBIDDEN_OPTIONS = (
    "--incumbent-json", "--hga-incumbent", "--external-incumbent",
    "--frontier-focus-from-result", "--frontier-import-interval-bound",
    "--frontier-focus-only", "--frontier-resume-state",
    "--frontier-resume-open-nodes", "--incumbent-archive-auto",
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        if len(value) != 1:
            raise RuntimeError(f"expected one result: {path}")
        value = value[0]
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def descriptors() -> list[dict[str, Any]]:
    return [
        load_json(r56.ROOT / row["descriptor_path"])
        for row in load_json(r56.EVIDENCE / "scenario_manifest.json")["rows"]
    ]


def command_for(descriptor: dict[str, Any], run_dir: Path, repetition_id: str = "official") -> tuple[list[str], str]:
    cap = int(descriptor["solver_process_cap_seconds"])
    identity = r56.run_identity(
        descriptor["mathematical_instance_sha256"], SOURCE_FREEZE,
        EXE_SHA256, r56.sha256_file(CONTRACT), cap, repetition_id)
    item = {
        "instance": descriptor["scenario_id"], "path": descriptor["fleet_variant_path"],
        "sha256": descriptor["fleet_variant_file_sha256"],
        "T": descriptor["route_time_limit_seconds"], "V": descriptor["V"], "M": descriptor["M"],
    }
    command = round46.c6_command(item, run_dir, cap, 1, 0.08, EXE)
    for option in FORBIDDEN_OPTIONS:
        round46.remove_option(command, option)
    for option, value in (
        ("--algorithm-preset", "paper-k1-am-sf"),
        ("--external-gini-interval-mip-policy", "interval-mip-core-no-exhaustive-subset-duration"),
        ("--T", float(descriptor["route_time_limit_seconds"])),
        ("--threads", 1), ("--mip-threads", 1), ("--gurobi-threads", 1),
        ("--gurobi-seed", 0), ("--gurobi-presolve", -1),
        ("--process-wall-time-limit", float(cap)),
        ("--time-limit", float(max(1, cap - 6))),
        ("--process-shutdown-margin", 2.0),
        ("--round48-k1-amf", "off"), ("--round49-k1-am-rc", "off"),
        ("--round56-scenario-id", descriptor["scenario_id"]),
        ("--round56-mathematical-instance-sha256", descriptor["mathematical_instance_sha256"]),
        ("--round56-run-identity-sha256", identity),
        ("--round22-source-commit", SOURCE_FREEZE),
        ("--round22-executable-sha256", EXE_SHA256),
        ("--round24-executable-sha256", EXE_SHA256),
        ("--round24-manifest-executable-sha256", EXE_SHA256),
        ("--progress-log", run_dir / "progress.csv"),
        ("--process-phase-ledger", run_dir / "process_phases.csv"),
        ("--external-gini-artifact-dir", run_dir / "external"),
        ("--primal-heuristic-generation-log", run_dir / "hga_generations.csv"),
        ("--heuristic-candidates-csv", run_dir / "heuristic_candidates.csv"),
        ("--log", run_dir / "native.log"), ("--out", run_dir / "result.json"),
    ):
        round46.replace_option(command, option, value)
    if any(option in command for option in FORBIDDEN_OPTIONS):
        raise RuntimeError(f"forbidden official option in {descriptor['scenario_id']}")
    return command, identity


def prepare() -> None:
    if r56.sha256_file(EXE) != EXE_SHA256:
        raise RuntimeError("official executable mismatch")
    rows = []
    for ordinal, descriptor in enumerate(descriptors(), start=1):
        run_dir = RAW / descriptor["scenario_id"]
        command, identity = command_for(descriptor, run_dir)
        rows.append({
            "ordinal": ordinal, "scenario_id": descriptor["scenario_id"],
            "panel_class": descriptor["panel_class"], "V": descriptor["V"], "M": descriptor["M"],
            "Q": descriptor["Q"], "T": descriptor["route_time_limit_seconds"],
            "solver_process_cap_seconds": descriptor["solver_process_cap_seconds"],
            "checkpoint_seconds": descriptor["checkpoint_seconds"],
            "mathematical_instance_sha256": descriptor["mathematical_instance_sha256"],
            "run_identity_sha256": identity, "output_directory": r56.repo_path(run_dir),
            "command": command,
        })
    if len(rows) != 50 or sum(row["solver_process_cap_seconds"] == 7200 for row in rows) != 9:
        raise RuntimeError("execution manifest cardinality failure")
    r56.write_json(r56.EVIDENCE / "execution_manifest.json", {
        "schema": "round56-execution-manifest-v1", "source_freeze_commit": SOURCE_FREEZE,
        "executable_sha256": EXE_SHA256, "solver_parameter_contract_sha256": r56.sha256_file(CONTRACT),
        "one_optimizer_process_at_a_time": True, "row_count": 50,
        "primary_q30_count": 40, "q20_sentinel_count": 10, "extension_7200_count": 9,
        "common_comparison_horizon_seconds": 3600, "rows": rows,
    })
    print(json.dumps({"execution_manifest_prepared": True, "row_count": 50}, indent=2))


def completed_row(descriptor: dict[str, Any], run_dir: Path, identity: str) -> dict[str, Any] | None:
    marker_path = run_dir / "completion_marker.json"
    result_path = run_dir / "result.json"
    if not marker_path.is_file() or not result_path.is_file():
        return None
    marker = load_json(marker_path)
    result = load_json(result_path)
    if not all((
        marker.get("complete") is True,
        marker.get("executable_sha256") == EXE_SHA256,
        marker.get("run_identity_sha256") == identity,
        marker.get("result_sha256") == r56.sha256_file(result_path),
        result.get("run_identity_sha256") == identity,
        result.get("mathematical_instance_sha256") == descriptor["mathematical_instance_sha256"],
    )):
        return None
    return result


def refresh_index() -> list[dict[str, Any]]:
    rows = []
    for descriptor in descriptors():
        run_dir = RAW / descriptor["scenario_id"]
        result_path = run_dir / "result.json"
        marker_path = run_dir / "completion_marker.json"
        if not result_path.is_file() or not marker_path.is_file():
            continue
        result = load_json(result_path)
        marker = load_json(marker_path)
        rows.append({
            "scenario_id": descriptor["scenario_id"], "V": descriptor["V"], "M": descriptor["M"],
            "Q": descriptor["Q"], "T": descriptor["route_time_limit_seconds"],
            "cap_seconds": descriptor["solver_process_cap_seconds"], "solution_class": marker.get("solution_class"),
            "strict_certificate": bool(result.get("strict_certified_original_problem")),
            "verified_incumbent": bool((result.get("verification") or {}).get("original_solution_feasible")),
            "algorithm_wall_seconds": result.get("final_process_wall_time_seconds"),
            "result_sha256": marker.get("result_sha256"), "route_package_available": marker.get("route_package_available"),
            "archive_verification_passed": marker.get("archive_verification_passed"),
        })
    if rows:
        r56.write_csv(RUN_INDEX, rows)
    return rows


def run(selected_ids: set[str] | None = None) -> None:
    if not (r56.EVIDENCE / "execution_manifest.json").is_file():
        raise RuntimeError("run --prepare and commit the execution manifest first")
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    all_rows = descriptors()
    for ordinal, descriptor in enumerate(all_rows, start=1):
        scenario_id = descriptor["scenario_id"]
        if selected_ids is not None and scenario_id not in selected_ids:
            continue
        run_dir = RAW / scenario_id
        run_dir.mkdir(parents=True, exist_ok=True)
        command, identity = command_for(descriptor, run_dir)
        result = completed_row(descriptor, run_dir, identity)
        if result is not None:
            print(f"[{ordinal}/50] {scenario_id} resumed", flush=True)
            continue
        command_path = run_dir / "command.json"
        r56.write_json(command_path, {
            "schema": "round56-official-command-v1", "scenario_id": scenario_id,
            "mathematical_instance_sha256": descriptor["mathematical_instance_sha256"],
            "run_identity_sha256": identity, "source_freeze_commit": SOURCE_FREEZE,
            "executable_sha256": EXE_SHA256, "solver_process_cap_seconds": descriptor["solver_process_cap_seconds"],
            "command": command, "started": True, "completed": False,
        })
        cap = int(descriptor["solver_process_cap_seconds"])
        print(f"[{ordinal}/50] START {scenario_id} cap={cap}s", flush=True)
        started = time.monotonic()
        with (run_dir / "stdout.log").open("wb") as stdout, (run_dir / "stderr.log").open("wb") as stderr:
            try:
                completed = subprocess.run(command, cwd=r56.ROOT, env=env, stdout=stdout, stderr=stderr, timeout=cap + 180, check=False)
                return_code, watchdog = completed.returncode, False
            except subprocess.TimeoutExpired:
                return_code, watchdog = -1, True
        result_path = run_dir / "result.json"
        runner_wall = time.monotonic() - started
        record = load_json(command_path)
        record.update({"return_code": return_code, "watchdog_timeout": watchdog, "runner_wall_seconds": runner_wall, "completed": result_path.is_file()})
        r56.write_json(command_path, record)
        if watchdog or return_code != 0 or not result_path.is_file():
            raise RuntimeError(f"official execution failure: {scenario_id}")
        result = load_json(result_path)
        if result.get("algorithm_preset") != "paper-k1-am-sf":
            raise RuntimeError(f"preset mismatch: {scenario_id}")
        if result.get("mathematical_instance_sha256") != descriptor["mathematical_instance_sha256"] or result.get("run_identity_sha256") != identity:
            raise RuntimeError(f"identity mismatch: {scenario_id}")
        if int(float(result.get("route_time_limit_seconds", -1))) != int(descriptor["route_time_limit_seconds"]):
            raise RuntimeError(f"T roundtrip mismatch: {scenario_id}")
        if int(float(result.get("solver_process_cap_seconds", -1))) != cap:
            raise RuntimeError(f"process cap roundtrip mismatch: {scenario_id}")
        solution_class = classify(result)
        package = build_package(scenario_id)
        marker = {
            "schema": "round56-official-completion-v1", "complete": True,
            "scenario_id": scenario_id, "solution_class": solution_class,
            "strict_certificate": bool(result.get("strict_certified_original_problem")),
            "solver_process_cap_seconds": cap, "runner_wall_seconds": runner_wall,
            "process_seconds": result.get("final_process_wall_time_seconds"),
            "cap_respected": float(result.get("final_process_wall_time_seconds", 0.0)) <= cap + max(2.0, 0.01 * cap),
            "mathematical_instance_sha256": descriptor["mathematical_instance_sha256"],
            "run_identity_sha256": identity, "executable_sha256": EXE_SHA256,
            "result_sha256": r56.sha256_file(result_path),
            "route_package_available": package.get("package_available", False),
            "archive_verification_passed": package.get("archive_verification_passed"),
        }
        r56.write_json(run_dir / "completion_marker.json", marker)
        refresh_index()
        print(f"[{ordinal}/50] DONE {scenario_id} class={solution_class} wall={runner_wall:.3f}s", flush=True)
    rows = refresh_index()
    print(json.dumps({"official_rows_complete": len(rows), "required": 50}, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--scenario-id", action="append")
    args = parser.parse_args()
    if args.prepare == args.run:
        raise RuntimeError("select exactly one of --prepare or --run")
    if args.prepare:
        prepare()
    else:
        run(set(args.scenario_id) if args.scenario_id else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
