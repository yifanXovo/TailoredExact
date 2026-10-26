#!/usr/bin/env python3
"""Run and seal one frozen Round 48 K1-AMF candidate row."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time
from typing import Any

import round48_common as common


REQUIRED_LEDGERS = (
    "amf_decision_ledger.csv",
    "formulation_strength_ledger.csv",
    "formulation_variable_registry.csv",
    "native_target_ledger.csv",
    "interval_tree_events.csv",
    "interval_coverage_ledger.csv",
    "global_bound_trace.csv",
    "model_size_ledger.csv",
    "certificate_ledger.csv",
)
REQUIRED = (
    "command.json", "process_manifest.json", "process_phases.csv",
    "progress.csv", "result.json", *REQUIRED_LEDGERS,
    "artifact_manifest.csv", "completion_marker.json",
)


def normalized_json(path: Path) -> dict[str, Any]:
    value = common.load_json(path)
    return value[0] if isinstance(value, list) else value


def copy_required(source: Path, target: Path) -> None:
    if not source.is_file():
        raise RuntimeError(f"required live artifact missing: {source}")
    shutil.copyfile(source, target)


def seal(run_dir: Path, record: dict[str, Any]) -> None:
    external = run_dir / "external"
    live_marker = common.load_json(external / "completion_marker.json")
    if not live_marker.get("completed"):
        raise RuntimeError(f"live completion marker is not complete: {run_dir}")
    for name in REQUIRED_LEDGERS:
        copy_required(external / name, run_dir / name)
    result = normalized_json(run_dir / "result.json")
    if result.get("round48_k1_amf") != "k1-amf":
        raise RuntimeError("sealed row is not K1-AMF")
    if result.get("round48_amf_extra_lp_count") != 0 or \
            result.get("round48_amf_extra_mip_count") != 0:
        raise RuntimeError("AMF reported an extra score solve")
    missing = [name for name in REQUIRED[:-2]
               if not (run_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"required official artifacts missing: {missing}")
    rows = []
    for path in sorted(p for p in run_dir.rglob("*") if p.is_file() and
                       p.parent != run_dir / "models" and
                       p.name not in {"artifact_manifest.csv",
                                      "completion_marker.json"}):
        rows.append({
            "path": path.relative_to(run_dir).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": common.sha256(path),
        })
    common.write_csv(run_dir / "artifact_manifest.csv", rows)
    common.write_json(run_dir / "completion_marker.json", {
        "schema": "round48-sealed-completion-marker-v1",
        "complete": True, "run_id": record["run_id"],
        "artifact_count": len(rows),
        "artifact_manifest_sha256":
            common.sha256(run_dir / "artifact_manifest.csv"),
        "live_completion_marker_sha256":
            common.sha256(external / "completion_marker.json"),
        "executable_sha256": record["executable_sha256"],
        "decision_identity_sha256":
            record["candidate_identity"]["decision_identity_sha256"],
        "strict_certificate": bool(
            result.get("strict_certified_original_problem")),
        "rescue_count": result.get("round48_amf_rescue_count", 0),
        "invalid_profile_fallback_count": result.get(
            "round48_amf_invalid_profile_fallback_count", 0),
        "extra_lp_count": result.get("round48_amf_extra_lp_count", 0),
        "extra_mip_count": result.get("round48_amf_extra_mip_count", 0),
    })


def run_one(args: argparse.Namespace, item: dict[str, Any],
            executable: Path) -> None:
    run_id = f"{args.stage}__{item['instance']}__K1-AMF"
    run_dir = common.RUNS / run_id
    marker = run_dir / "completion_marker.json"
    if marker.is_file() and not args.force:
        print(f"resume: {run_id}", flush=True)
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    for name in ("artifact_manifest.csv", "completion_marker.json"):
        (run_dir / name).unlink(missing_ok=True)
    command = common.candidate_command(
        item, run_dir, args.process_cap, executable)
    identity = common.identity()
    record = {
        "schema": "round48-run-v1", "round_id": 48,
        "stage": args.stage, "run_id": run_id,
        "instance_id": item["instance"], "instance_path": item["path"],
        "instance_sha256": item["sha256"], "role": item["role"],
        "algorithm": "K1-AMF", "K0": 1, "tau": common.TAU,
        "tau_explicit": True, "point_rule": "midpoint",
        "candidate_identity": identity,
        "process_cap_seconds": args.process_cap,
        "watchdog_seconds": args.process_cap + 45.0,
        "command": command, "executable_path": str(executable.resolve()),
        "executable_sha256": common.sha256(executable),
        "completed": False, "invalidated": False,
        "bounded_diagnostic_due_offline_gate_failure": True,
    }
    common.write_json(run_dir / "command.json", record)
    common.write_json(run_dir / "process_manifest.json", {
        "schema": "round48-process-manifest-v1", "run_id": run_id,
        "algorithm": "K1-AMF", "K0": 1, "tau": common.TAU,
        "tau_explicit": True, "point_rule": "midpoint",
        "process_cap_seconds": args.process_cap,
        "executable_sha256": record["executable_sha256"],
        "solver_contract": identity["solver"],
        "formulation_profile_version":
            "round48-canonical-interval-sensitive-v1",
        "extra_lp_queries_for_score": 0,
        "extra_mip_queries_for_score": 0,
        "rho_cap": False, "contraction": False,
        "model_chain_inheritance_change": False,
        "algorithmic_switches_use_runtime_outcomes": False,
    })
    common.write_json(run_dir / "command_environment.json", {
        "machine": platform.node(), "platform": platform.platform(),
        "python": platform.python_version(),
        "executable_sha256": record["executable_sha256"],
    })
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    with (run_dir / "stdout.log").open("wb") as stdout, \
            (run_dir / "stderr.log").open("wb") as stderr:
        try:
            process = subprocess.run(
                command, cwd=common.ROOT, env=env, stdout=stdout,
                stderr=stderr, timeout=record["watchdog_seconds"],
                check=False)
            return_code, watchdog = process.returncode, False
        except subprocess.TimeoutExpired:
            return_code, watchdog = -1, True
    record.update({
        "completed": (run_dir / "result.json").is_file(),
        "return_code": return_code, "watchdog_timeout": watchdog,
        "runner_wall_seconds": time.monotonic() - started,
    })
    common.write_json(run_dir / "command.json", record)
    if return_code or watchdog or not record["completed"]:
        raise RuntimeError(f"Round 48 row failed: {run_id}")
    seal(run_dir, record)
    result = normalized_json(run_dir / "result.json")
    print(json.dumps({
        "run_id": run_id, "status": result.get("status"),
        "certificate": result.get("strict_certified_original_problem"),
        "rescues": result.get("round48_amf_rescue_count", 0),
        "fallbacks": result.get("round48_amf_invalid_profile_fallback_count", 0),
        "work": result.get("external_gini_tree_work", result.get("work")),
        "seconds": result.get("final_process_wall_time_seconds",
                              result.get("actual_runtime_seconds")),
    }, sort_keys=True), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("stage3_300s",), required=True)
    parser.add_argument("--instance", action="append", required=True)
    parser.add_argument("--process-cap", type=float, required=True)
    parser.add_argument("--executable", type=Path, default=common.EXE)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.process_cap != 300.0:
        raise SystemExit("Round 48 Stage 3 is frozen at exactly 300 seconds")
    executable = args.executable.resolve()
    if not executable.is_file():
        raise SystemExit(f"Round 48 executable missing: {executable}")
    if "dev-gurobi-release" in executable.as_posix().lower():
        raise SystemExit("official Stage 3 rows cannot use development executable")
    items = common.frozen_instances()
    unknown = set(args.instance) - set(common.MECHANISM)
    if unknown:
        raise SystemExit(f"instances are not in the Stage 3 panel: {sorted(unknown)}")
    for name in args.instance:
        run_one(args, items[name], executable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
