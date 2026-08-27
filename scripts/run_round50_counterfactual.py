#!/usr/bin/env python3
"""Run one frozen Round 50 RETAIN/MIDPOINT counterfactual arm."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import round48_common as common  # noqa: E402

EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
CASES = {
    "major_root": ("round39_small_medium_V12_M3_Q30_slot08_seed1343324363", "L0"),
    "strong_control_root": ("round39_small_hard_V12_M3_Q30_slot08_seed1288546114", "L0"),
    "numerical_endpoint_root": ("round39_small_hard_V12_M3_Q20_slot07_seed621538683", "L0"),
    "v12_m2_root": ("round39_small_hard_V12_M2_Q20_slot06_seed258908503", "L0"),
    "tight3102_L0_0": ("tight_T_seed3102", "L0.0"),
    "high_imbalance_matched": ("high_imbalance_seed3201", "L0.1.0"),
    "moderate3301_root": ("moderate_seed3301", "L0"),
}


def normalized(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def write_csv(path: Path, fields: list[str], row: dict[str, object]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", required=True, choices=sorted(CASES))
    parser.add_argument("--arm", required=True, choices=("retain", "midpoint"))
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--process-cap", type=float, default=1200.0)
    args = parser.parse_args()
    if not (0 < args.process_cap <= 1800):
        raise SystemExit("process cap must satisfy 0 < cap <= 1800")
    executable = args.executable.resolve()
    if not executable.is_file() or "dev-gurobi-release" in executable.as_posix().lower():
        raise SystemExit("a clean official full executable is required")

    instance, interval = CASES[args.case]
    item = common.frozen_instances()[instance]
    run_id = f"{args.case}__{args.arm}"
    run_dir = EVIDENCE / "counterfactual_runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    marker_path = run_dir / "completion_marker.json"
    if marker_path.is_file():
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        if (marker.get("complete") is True and
                marker.get("executable_sha256") == common.sha256(executable) and
                float(marker.get("process_cap_seconds", -1)) == args.process_cap):
            print(json.dumps(marker, sort_keys=True))
            return 0
        raise RuntimeError(f"nonreusable completion marker exists: {run_id}")

    command = common.counterfactual_command(
        item, run_dir, args.process_cap, interval, args.arm, executable)
    parent_rows = common.csv_rows(
        EVIDENCE / "vnext_counterfactual_parent_manifest.csv")
    parent = next(row for row in parent_rows if row["case"] == args.case)
    record = {
        "schema": "round50-vnext-counterfactual-command-v1",
        "run_id": run_id,
        "case": args.case,
        "instance": instance,
        "interval": interval,
        "arm": args.arm,
        "parent_identity_sha256": parent["parent_identity_sha256"],
        "backend": "Interval-MIP-vNext == Interval-MIP-v0",
        "diagnostic_not_original_problem_certificate": True,
        "process_cap_seconds": args.process_cap,
        "executable_path": str(executable),
        "executable_sha256": common.sha256(executable),
        "input_sha256": item["sha256"],
        "command": command,
    }
    common.write_json(run_dir / "command.json", record)
    common.write_json(run_dir / "process_manifest.json", {
        "schema": "round50-vnext-counterfactual-process-manifest-v1",
        "run_id": run_id,
        "backend": record["backend"],
        "K0": 1,
        "tau": common.TAU,
        "point_rule": "midpoint",
        "forced_action": args.arm,
        "forced_interval": interval,
        "descendant_splits_forbidden": args.arm == "midpoint",
        "process_cap_seconds": args.process_cap,
        "executable_sha256": record["executable_sha256"],
        "runtime_dispatch": False,
    })
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result_path = run_dir / "result.json"
    started = time.monotonic()
    recovered_existing_result = result_path.is_file()
    if recovered_existing_result:
        return_code, watchdog = 0, False
    else:
        with (run_dir / "stdout.log").open("wb") as stdout, \
                (run_dir / "stderr.log").open("wb") as stderr:
            try:
                process = subprocess.run(
                    command, cwd=ROOT, env=environment, stdout=stdout,
                    stderr=stderr, timeout=args.process_cap + 45.0, check=False)
                return_code, watchdog = process.returncode, False
            except subprocess.TimeoutExpired:
                return_code, watchdog = -1, True
    if return_code or watchdog or not result_path.is_file():
        raise RuntimeError(
            f"counterfactual failed: {run_id}, rc={return_code}, watchdog={watchdog}")
    result = normalized(result_path)
    if not result.get("round48_counterfactual_performed"):
        raise RuntimeError(f"counterfactual target was not performed: {run_id}")

    external = run_dir / "external"
    ledger_mapping = {
        "global_bound_trace.csv": "global_bound_trace.csv",
        "interval_tree_events.csv": "paper_tree_events.csv",
        "interval_coverage_ledger.csv": "paper_leaf_ledger.csv",
        "parent_lp_ledger.csv": "parent_child_bound_ledger.csv",
        "child_lp_ledger.csv": "lp_status_ledger.csv",
        "adaptive_mass_decision_ledger.csv": "adaptive_mass_decision_ledger.csv",
        "native_target_ledger.csv": "native_target_ledger.csv",
    }
    for target, source in ledger_mapping.items():
        source_path = external / source
        if not source_path.is_file():
            raise RuntimeError(f"required live ledger missing: {source_path}")
        shutil.copyfile(source_path, run_dir / target)
    write_csv(run_dir / "certificate_ledger.csv", [
        "run_id", "local_counterfactual_exact",
        "diagnostic_not_original_problem_certificate", "status",
        "lower_bound", "upper_bound", "gap", "false_certificate"], {
            "run_id": run_id,
            "local_counterfactual_exact":
                result.get("status") == "round48_counterfactual_exact",
            "diagnostic_not_original_problem_certificate": True,
            "status": result.get("status", ""),
            "lower_bound": result.get("lower_bound", 0),
            "upper_bound": result.get("upper_bound", 0),
            "gap": result.get("gap", 0),
            "false_certificate": False,
        })

    write_csv(run_dir / "fixed_interval_mip_summary.csv", [
        "backend", "policy", "model_count", "model_build_seconds",
        "total_work"], {
            "backend": "Interval-MIP-vNext == Interval-MIP-v0",
            "policy": "historical fixed-interval v0",
            "model_count": result.get("external_gini_tree_model_count", 0),
            "model_build_seconds": result.get(
                "external_gini_tree_model_build_seconds", 0),
            "total_work": result.get("external_gini_tree_work", 0),
        })
    write_csv(run_dir / "branching_policy_summary.csv", [
        "policy", "runtime_dispatch"], {
            "policy": "Gurobi default; no Round 50 priorities",
            "runtime_dispatch": False,
        })
    write_csv(run_dir / "cut_family_summary.csv", [
        "policy", "round50_candidate_changes"], {
            "policy": "original v0 cut/formulation pack",
            "round50_candidate_changes": 0,
        })
    write_csv(run_dir / "model_reuse_summary.csv", [
        "policy", "reuse_change"], {
            "policy": "historical K1-AM model lifecycle",
            "reuse_change": False,
        })

    required = [
        "command.json", "process_manifest.json", "process_phases.csv", "result.json",
        "global_bound_trace.csv", "interval_tree_events.csv",
        "interval_coverage_ledger.csv", "parent_lp_ledger.csv",
        "child_lp_ledger.csv", "adaptive_mass_decision_ledger.csv",
        "native_target_ledger.csv", "fixed_interval_mip_summary.csv",
        "branching_policy_summary.csv", "cut_family_summary.csv",
        "model_reuse_summary.csv", "certificate_ledger.csv",
    ]
    missing = [name for name in required if not (run_dir / name).is_file()]
    if missing:
        raise RuntimeError(f"missing required full-K1 artifacts: {missing}")
    with (run_dir / "artifact_manifest.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "sha256", "bytes"])
        writer.writeheader()
        for name in required:
            path = run_dir / name
            writer.writerow({
                "path": name,
                "sha256": common.sha256(path),
                "bytes": path.stat().st_size,
            })
    marker = {
        "schema": "round50-vnext-counterfactual-completion-v1",
        "complete": True,
        "run_id": run_id,
        "case": args.case,
        "instance": instance,
        "interval": interval,
        "arm": args.arm,
        "parent_identity_sha256": parent["parent_identity_sha256"],
        "process_cap_seconds": args.process_cap,
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code,
        "watchdog_timeout": watchdog,
        "sealed_from_completed_unsealed_result": recovered_existing_result,
        "executable_sha256": common.sha256(executable),
        "result_sha256": common.sha256(result_path),
        "artifact_manifest_sha256": common.sha256(
            run_dir / "artifact_manifest.csv"),
        "counterfactual_performed": True,
        "descendant_split_suppression_count": result.get(
            "round48_counterfactual_descendant_split_suppression_count", 0),
        "local_exact": result.get("status") == "round48_counterfactual_exact",
        "status": result.get("status"),
        "work": result.get("external_gini_tree_work", 0),
        "time_seconds": result.get("runtime_seconds", 0),
        "lower_bound": result.get("lower_bound", 0),
        "upper_bound": result.get("upper_bound", 0),
        "gap": result.get("gap", 0),
    }
    common.write_json(marker_path, marker)
    print(json.dumps(marker, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
