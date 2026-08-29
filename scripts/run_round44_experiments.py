#!/usr/bin/env python3
"""Run and seal one or more frozen Round 44 candidate rows."""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any

import round44_common as common


STANDARD_LEDGER_SOURCES = {
    "global_bound_trace.csv": "global_bound_trace.csv",
    "interval_tree_events.csv": "paper_tree_events.csv",
    "interval_coverage_ledger.csv": "paper_leaf_ledger.csv",
    "parent_lp_ledger.csv": "lp_status_ledger.csv",
    "lookahead_profile_ledger.csv": "lookahead_profile_ledger.csv",
    "envelope_ledger.csv": "envelope_ledger.csv",
    "envelope_facet_ledger.csv": "envelope_facet_ledger.csv",
    "frontier_target_ledger.csv": "frontier_target_ledger.csv",
    "refinement_decision_ledger.csv": "refinement_decision_ledger.csv",
    "old_c6_action_ledger.csv": "old_c6_action_ledger.csv",
    "lookahead_reuse_ledger.csv": "lookahead_reuse_ledger.csv",
    "native_target_ledger.csv": "native_target_ledger.csv",
    "native_optimize_ledger.csv": "paper_optimize_ledger.csv",
    "mip_start_ledger.csv": "mip_start_ledger.csv",
    "explicit_cut_scope_ledger.csv": "explicit_cut_scope_ledger.csv",
    "cglp_multiplier_ledger.csv": "cglp_multiplier_ledger.csv",
}


def write_single_csv(path: Path, row: dict[str, Any]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def seal_run(run_dir: Path, command_record: dict[str, Any]) -> None:
    external = run_dir / "external"
    missing: list[str] = []
    for target_name, source_name in STANDARD_LEDGER_SOURCES.items():
        source = external / source_name
        target = run_dir / target_name
        if not source.is_file():
            missing.append(source_name)
            continue
        shutil.copyfile(source, target)
    result = common.load_json(run_dir / "result.json")
    write_single_csv(run_dir / "certificate_ledger.csv", {
        "strict_certified_original_problem":
            result.get("strict_certified_original_problem", False),
        "certificate_class": result.get("strict_certificate_class", ""),
        "rejection_reason":
            result.get("strict_certificate_rejection_reason", ""),
        "valid_global_lower_bound":
            result.get("external_gini_tree_global_lower_bound", ""),
        "verified_global_upper_bound":
            result.get("external_gini_tree_verified_upper_bound", ""),
        "coverage_valid":
            result.get("external_gini_tree_root_coverage_valid", False),
        "failure_reason":
            result.get("external_gini_tree_failure_reason", ""),
    })
    write_single_csv(run_dir / "model_size_ledger.csv", {
        "models": result.get("external_gini_tree_model_count", 0),
        "models_freed":
            result.get("external_gini_tree_model_free_count", 0),
        "environments":
            result.get("external_gini_tree_environment_count", 0),
        "environments_freed":
            result.get("external_gini_tree_environment_free_count", 0),
        "peak_memory_gb":
            result.get("external_gini_tree_peak_memory_gb", 0),
        "lp_optimize_count":
            result.get("external_gini_tree_lp_optimize_count", 0),
        "terminal_mip_count":
            result.get("external_gini_tree_terminal_mip_optimize_count", 0),
    })
    if missing:
        raise RuntimeError(f"required raw Round 44 ledgers missing: {missing}")
    required = [
        "command.json", "process_phases.csv", "progress.csv", "result.json",
        *STANDARD_LEDGER_SOURCES, "certificate_ledger.csv",
        "model_size_ledger.csv",
    ]
    absent = [name for name in required if not (run_dir / name).is_file()]
    if absent:
        raise RuntimeError(f"required sealed artifacts missing: {absent}")
    manifest_rows = []
    for path in sorted(p for p in run_dir.rglob("*") if p.is_file() and
                       p.name not in {"artifact_manifest.csv",
                                      "completion_marker.json"}):
        manifest_rows.append({
            "path": path.relative_to(run_dir).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": common.sha256(path),
        })
    common.write_csv(run_dir / "artifact_manifest.csv", manifest_rows)
    marker = {
        "schema": "round44-completion-marker-v1",
        "run_id": command_record["run_id"],
        "complete": True,
        "candidate_identity_sha256":
            command_record["candidate_identity"][
                "decision_identity_sha256"],
        "executable_sha256": command_record["executable_sha256"],
        "artifact_count": len(manifest_rows),
        "artifact_manifest_sha256":
            common.sha256(run_dir / "artifact_manifest.csv"),
    }
    common.write_json(run_dir / "completion_marker.json", marker)


def run_one(args: argparse.Namespace, instance_id: str) -> dict[str, Any]:
    identity = common.candidate_identity(
        execution=args.execution, lookahead=args.lookahead,
        injection=args.injection, scope=args.scope, family=args.family,
        rho_f=args.rho_f, rho_m=args.rho_m, rho_h=args.rho_h,
        rank1=args.rank1, mip_starts=args.mip_starts,
        consolidation=args.consolidation)
    label = args.tag or identity["decision_identity_sha256"][:12]
    run_id = f"{args.stage}__{instance_id}__{label}"
    run_dir = common.RUNS / run_id
    result_path = run_dir / "result.json"
    if (result_path.is_file() and
            (run_dir / "completion_marker.json").is_file() and
            not args.force):
        print(f"resume: {run_id}", flush=True)
        return common.load_json(result_path)
    run_dir.mkdir(parents=True, exist_ok=True)
    if args.force:
        # A forced rerun must never look sealed while the replacement process
        # is still active or after a failed replacement attempt.
        for stale_name in ("completion_marker.json", "artifact_manifest.csv"):
            stale = run_dir / stale_name
            if stale.is_file():
                stale.unlink()
    item = common.inventory()[instance_id]
    command = common.fair_candidate_command(
        item, run_dir, args.process_cap, execution=args.execution,
        lookahead=args.lookahead, injection=args.injection,
        scope=args.scope, family=args.family, rho_f=args.rho_f,
        rho_m=args.rho_m, rho_h=args.rho_h, rank1=args.rank1,
        mip_starts=args.mip_starts, consolidation=args.consolidation)
    record: dict[str, Any] = {
        "schema": "round44-run-v1",
        "round_id": 44,
        "stage": args.stage,
        "run_id": run_id,
        "instance_id": instance_id,
        "instance_sha256": item["sha256"],
        "candidate_identity": identity,
        "process_cap_seconds": args.process_cap,
        "watchdog_seconds": args.process_cap + 45.0,
        "command": command,
        "executable_sha256": common.sha256(common.EXE),
        "completed": False,
        "invalidated": False,
    }
    common.write_json(run_dir / "command.json", record)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    timed_out = False
    return_code = -1
    with (run_dir / "stdout.log").open("wb") as stdout, \
            (run_dir / "stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=common.ROOT, env=environment,
                stdout=stdout, stderr=stderr, check=False,
                timeout=record["watchdog_seconds"])
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
    record.update({
        "completed": result_path.is_file(),
        "return_code": return_code,
        "watchdog_timeout": timed_out,
        "runner_wall_seconds": time.monotonic() - started,
    })
    common.write_json(run_dir / "command.json", record)
    if return_code != 0 or timed_out or not result_path.is_file():
        raise RuntimeError(f"Round 44 row failed: {run_id}")
    seal_run(run_dir, record)
    result = common.load_json(result_path)
    print(json.dumps({
        "run_id": run_id,
        "status": result.get("status"),
        "certified": result.get("strict_certified_original_problem"),
        "work": result.get("external_gini_tree_work"),
        "seconds": result.get("final_process_wall_time_seconds"),
    }, sort_keys=True), flush=True)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--instance", action="append", required=True)
    parser.add_argument("--execution", choices=("atlas", "algorithm"),
                        required=True)
    parser.add_argument("--lookahead", choices=(
        "fixed-d1", "fixed-d2", "frontier-d2"), required=True)
    parser.add_argument("--injection", choices=(
        "none", "all", "violated", "active-one"), required=True)
    parser.add_argument("--scope", choices=("parent", "nested"),
                        required=True)
    parser.add_argument("--family", choices=(
        "no-adaptive", "c6-overlay", "veto", "veto-promotion",
        "f", "f-mroot", "h", "mroot"), required=True)
    parser.add_argument("--rho-f", type=float, default=0.5)
    parser.add_argument("--rho-m", type=float, default=0.0)
    parser.add_argument("--rho-h", type=float, default=0.0)
    parser.add_argument("--rank1", choices=("off", "on"), default="off")
    parser.add_argument("--mip-starts", choices=("off", "verified"),
                        default="off")
    parser.add_argument("--consolidation", choices=(
        "off", "singleton", "pair", "block"), default="off")
    parser.add_argument("--process-cap", type=float, default=3600.0)
    parser.add_argument("--tag", default="")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not common.EXE.is_file():
        raise SystemExit(f"Round 44 executable missing: {common.EXE}")
    unknown = set(args.instance) - set(common.inventory())
    if unknown:
        raise SystemExit(f"instances are not frozen: {sorted(unknown)}")
    for instance_id in args.instance:
        run_one(args, instance_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
