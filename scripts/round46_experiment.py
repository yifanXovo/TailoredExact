#!/usr/bin/env python3
"""Run and seal one or more frozen Round 46 rows."""

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

import round46_common as common


REQUIRED = (
    "command.json", "process_manifest.json", "process_phases.csv",
    "progress.csv", "result.json", "global_bound_trace.csv",
    "interval_tree_events.csv", "interval_coverage_ledger.csv",
    "parent_lp_ledger.csv", "child_lp_ledger.csv",
    "c6_split_decision_ledger.csv", "native_target_ledger.csv",
    "native_optimize_ledger.csv", "certificate_ledger.csv",
    "model_size_ledger.csv", "artifact_manifest.csv",
    "completion_marker.json",
)


def normalized_json(path: Path) -> dict[str, Any]:
    value = common.load_json(path)
    return value[0] if isinstance(value, list) else value


def copy_required(source: Path, target: Path) -> None:
    if not source.is_file():
        raise RuntimeError(f"required live artifact missing: {source}")
    shutil.copyfile(source, target)


def add_run_id(source: Path, target: Path, run_id: str) -> None:
    if not source.is_file():
        raise RuntimeError(f"required C6 decision ledger missing: {source}")
    with source.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        fields = ["run_id", *(reader.fieldnames or [])]
        rows = [{"run_id": run_id, **row} for row in reader]
    common.write_csv(target, rows, fields, allow_empty=True)


def empty_csv(path: Path, fields: list[str]) -> None:
    common.write_csv(path, [], fields, allow_empty=True)


def seal_c6(run_dir: Path, run_id: str) -> None:
    external = run_dir / "external"
    mapping = {
        "global_bound_trace.csv": "global_bound_trace.csv",
        "interval_tree_events.csv": "paper_tree_events.csv",
        "interval_coverage_ledger.csv": "paper_leaf_ledger.csv",
        "parent_lp_ledger.csv": "parent_child_bound_ledger.csv",
        "child_lp_ledger.csv": "lp_status_ledger.csv",
        "native_target_ledger.csv": "native_target_ledger.csv",
        "native_optimize_ledger.csv": "paper_optimize_ledger.csv",
    }
    for target, source in mapping.items():
        copy_required(external / source, run_dir / target)
    add_run_id(external / "c6_split_decision_ledger.csv",
               run_dir / "c6_split_decision_ledger.csv", run_id)


def seal_pgrb(run_dir: Path) -> None:
    copy_required(run_dir / "progress.csv", run_dir / "global_bound_trace.csv")
    empty_csv(run_dir / "interval_tree_events.csv",
              ["run_id", "event", "reason"])
    empty_csv(run_dir / "interval_coverage_ledger.csv",
              ["run_id", "coverage_status", "reason"])
    empty_csv(run_dir / "parent_lp_ledger.csv",
              ["run_id", "parent_id", "bound", "reason"])
    empty_csv(run_dir / "child_lp_ledger.csv",
              ["run_id", "child_id", "bound", "reason"])
    empty_csv(run_dir / "c6_split_decision_ledger.csv", [
        "run_id", "decision_sequence", "K0", "rho", "rho_source",
        "interval_id", "parent_id", "depth", "gamma_L", "gamma_U",
        "parent_bound", "left_child_id", "left_child_bound",
        "left_child_infeasible", "right_child_id", "right_child_bound",
        "right_child_infeasible", "verified_incumbent",
        "normalized_c6_gain", "child_infeasibility_trigger",
        "threshold_comparison", "selected_action", "target_value",
        "deterministic_reason", "coverage_update"])
    empty_csv(run_dir / "native_target_ledger.csv",
              ["run_id", "target", "reason"])
    empty_csv(run_dir / "native_optimize_ledger.csv",
              ["run_id", "solve_kind", "reason"])


def seal(run_dir: Path, record: dict[str, Any], arm: str) -> None:
    result = normalized_json(run_dir / "result.json")
    if arm == "P-GRB":
        seal_pgrb(run_dir)
    else:
        seal_c6(run_dir, record["run_id"])
    common.write_csv(run_dir / "certificate_ledger.csv", [{
        "run_id": record["run_id"],
        "strict_certified_original_problem":
            result.get("strict_certified_original_problem", False),
        "certificate_class": result.get("strict_certificate_class", ""),
        "rejection_reason":
            result.get("strict_certificate_rejection_reason", ""),
        "coverage_valid":
            result.get("external_gini_tree_root_coverage_valid", "n/a"),
        "failure_reason":
            result.get("external_gini_tree_failure_reason", ""),
    }])
    common.write_csv(run_dir / "model_size_ledger.csv", [{
        "run_id": record["run_id"],
        "models": result.get("external_gini_tree_model_count", 0),
        "models_freed": result.get("external_gini_tree_model_free_count", 0),
        "environments": result.get("external_gini_tree_environment_count", 0),
        "environments_freed":
            result.get("external_gini_tree_environment_free_count", 0),
        "peak_memory_gb":
            result.get("external_gini_tree_peak_memory_gb", 0),
        "lp_jobs": result.get("external_gini_tree_lp_optimize_count", 0),
        "native_target_jobs":
            result.get("external_gini_tree_native_bound_target_count", 0),
        "terminal_mip_jobs":
            result.get("external_gini_tree_terminal_mip_optimize_count", 0),
        "nodes": result.get("nodes", result.get("gurobi_node_count", 0)),
    }])
    before_manifest = [name for name in REQUIRED
                       if name not in {"artifact_manifest.csv",
                                       "completion_marker.json"}]
    missing = [name for name in before_manifest
               if not (run_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"required official artifacts missing: {missing}")
    rows = []
    for path in sorted(p for p in run_dir.rglob("*") if p.is_file() and
                       p.name not in {"artifact_manifest.csv",
                                      "completion_marker.json"}):
        rows.append({"path": path.relative_to(run_dir).as_posix(),
                     "size_bytes": path.stat().st_size,
                     "sha256": common.sha256(path)})
    common.write_csv(run_dir / "artifact_manifest.csv", rows)
    common.write_json(run_dir / "completion_marker.json", {
        "schema": "round46-completion-marker-v1", "complete": True,
        "run_id": record["run_id"], "artifact_count": len(rows),
        "artifact_manifest_sha256":
            common.sha256(run_dir / "artifact_manifest.csv"),
        "executable_sha256": record["executable_sha256"],
        "decision_identity_sha256":
            record["candidate_identity"]["decision_identity_sha256"],
    })


def run_one(args: argparse.Namespace, item: dict[str, Any],
            executable: Path) -> None:
    k0 = None if args.arm == "P-GRB" else args.k0
    rho = None if args.arm == "P-GRB" else args.rho
    identity = common.identity(args.arm, k0, rho)
    run_id = f"{args.stage}__{item['instance']}__{args.arm}"
    run_dir = common.RUNS / run_id
    marker = run_dir / "completion_marker.json"
    if marker.is_file() and not args.force:
        print(f"resume: {run_id}", flush=True)
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    for name in ("artifact_manifest.csv", "completion_marker.json"):
        (run_dir / name).unlink(missing_ok=True)
    command = (common.pgrb_command(item, run_dir, args.process_cap, executable)
               if args.arm == "P-GRB" else
               common.c6_command(item, run_dir, args.process_cap,
                                 args.k0, args.rho, executable))
    record = {
        "schema": "round46-run-v1", "round_id": 46,
        "stage": args.stage, "run_id": run_id,
        "instance_id": item["instance"], "instance_path": item["path"],
        "instance_sha256": item["sha256"], "arm": args.arm,
        "K0": k0, "rho": rho, "rho_explicit": rho is not None,
        "rho_source": "explicit" if rho is not None else "not_applicable",
        "candidate_identity": identity,
        "process_cap_seconds": args.process_cap,
        "watchdog_seconds": args.process_cap + 45.0,
        "command": command, "executable_path": str(executable.resolve()),
        "executable_sha256": common.sha256(executable),
        "completed": False, "invalidated": False,
    }
    common.write_json(run_dir / "command.json", record)
    common.write_json(run_dir / "process_manifest.json", {
        "schema": "round46-process-manifest-v1", "run_id": run_id,
        "arm": args.arm, "K0": k0, "rho": rho,
        "rho_explicit": rho is not None,
        "rho_source": record["rho_source"], "point_rule": "midpoint",
        "process_cap_seconds": args.process_cap,
        "executable_sha256": record["executable_sha256"],
        "solver_contract": identity["solver"],
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
        raise RuntimeError(f"Round 46 row failed: {run_id}")
    seal(run_dir, record, args.arm)
    result = normalized_json(run_dir / "result.json")
    print(json.dumps({
        "run_id": run_id, "status": result.get("status"),
        "certificate": result.get("strict_certified_original_problem"),
        "work": result.get("external_gini_tree_work", result.get("work")),
        "seconds": result.get("final_process_wall_time_seconds"),
    }, sort_keys=True), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--instance", action="append", required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--k0", type=int, choices=(1, 4))
    parser.add_argument("--rho", type=float, choices=common.RHO_GRID)
    parser.add_argument("--process-cap", type=float, required=True)
    parser.add_argument("--executable", type=Path, default=common.EXE)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.process_cap <= 0 or args.process_cap > 1800:
        raise SystemExit("process cap must satisfy 0 < cap <= 1800")
    if args.arm == "P-GRB":
        if args.k0 is not None or args.rho is not None:
            raise SystemExit("P-GRB has no K0/rho")
    else:
        if args.k0 is None or args.rho is None:
            raise SystemExit("C6 arms require --k0 and --rho")
        if common.ARM_BY_K_RHO.get((args.k0, args.rho)) != args.arm:
            raise SystemExit("arm/K0/rho identity mismatch")
    executable = args.executable.resolve()
    if not executable.is_file():
        raise SystemExit(f"Round 46 executable missing: {executable}")
    if (args.stage.lower().startswith(("stage3", "stage4", "stage5")) and
            "dev-gurobi-release" in executable.as_posix().lower()):
        raise SystemExit("official Stage 3/4/5 rows cannot use the development executable")
    items = common.frozen_instances()
    unknown = set(args.instance) - set(items)
    if unknown:
        raise SystemExit(f"instances are not frozen: {sorted(unknown)}")
    for name in args.instance:
        run_one(args, items[name], executable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
