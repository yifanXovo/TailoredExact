#!/usr/bin/env python3
"""Frozen serial runner for the preregistered Round 23 targeted validation."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
R22 = ROOT / "results/gf_global_gini_tree_unified_validation_round"
OUT = ROOT / "results/gf_global_gini_tree_round23"
OFFICIAL = OUT / "official"
EXE = ROOT / "build_round23/ExactEBRP-frozen.exe"
FROZEN = ROOT / "build_round23/frozen_executable.json"
PATH_FLAGS = {
    "--progress-log": "legacy_progress.csv",
    "--log": "native.log",
    "--out": "result.json",
    "--global-gini-tree-node-trace": "global_node_trace.csv",
    "--global-gini-tree-bound-trace": "legacy_global_bound.csv",
    "--global-gini-tree-manifest": "model_lifecycle_manifest.csv",
    "--global-gini-tree-root-export": "global_root.lp",
    "--global-gini-tree-post-row-trace": "post_rows.csv",
    "--global-gini-tree-topology-trace": "gini_topology.csv",
    "--global-gini-tree-sibling-trace": "sibling_delay.csv",
    "--global-gini-tree-row-delta-trace": "row_delta.csv",
    "--global-gini-tree-memory-trace": "tree_memory.csv",
    "--global-gini-tree-mip-start-audit": "mip_start_audit.csv",
    "--dense-progress-raw": "raw_progress.csv",
    "--dense-progress-checkpoints": "canonical_checkpoints.csv",
}
INSTANCES = {
    "V12_M1": ("stage2", "existing"),
    "V12_M2": ("stage2", "existing"),
    "high_imbalance_seed3202": ("stage2", "existing"),
    "high_imbalance_seed4201": ("stage4", "heldout"),
    "tight_T_seed3101": ("stage2", "existing"),
    "moderate_seed4302": ("stage4", "heldout"),
}
STAGE1 = ("V12_M2", "high_imbalance_seed3202", "tight_T_seed3101")
STAGE2 = tuple(INSTANCES)
ARMS = {
    "s0c": ("S0-C", "parent-copy", "corrected_s0_manifest.json"),
    "s0m": ("S0-M", "dispersion-coupled", "round23_candidate_manifest.json"),
}


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def set_flag(command: list[str], flag: str, value: str) -> None:
    try:
        index = command.index(flag)
    except ValueError:
        command.extend([flag, value])
    else:
        command[index + 1] = value


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes"}


def finite(value: Any) -> bool:
    try:
        return float("-inf") < float(value) < float("inf")
    except (TypeError, ValueError):
        return False


def verified_ub(data: dict[str, Any]) -> float | None:
    if as_bool(data.get("verified_incumbent_objective_available")) and finite(
        data.get("verified_incumbent_objective")
    ):
        return float(data["verified_incumbent_objective"])
    verification = data.get("verification") or {}
    if as_bool(verification.get("original_solution_feasible", verification.get("feasible"))) and finite(
        verification.get("objective")
    ):
        return float(verification["objective"])
    return None


def gap(upper: float | None, lower: Any) -> float | None:
    if upper is None or not finite(lower):
        return None
    residual = max(0.0, upper - float(lower))
    return residual / abs(upper) if abs(upper) > 1e-12 else (
        0.0 if residual == 0.0 else None
    )


def derive_checkpoints(raw: Path, output: Path, run_id: str, data: dict[str, Any], budget: int) -> None:
    with raw.open("r", encoding="utf-8", newline="") as stream:
        events = list(csv.DictReader(stream))
    native = [event for event in events if event.get("retention_trigger") != "solver_final"]
    checkpoints = [1, 2, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240,
                   300, 450, 600, 750, 900]
    upper = verified_ub(data)
    values: list[dict[str, Any]] = []
    for checkpoint in checkpoints:
        if checkpoint > budget:
            continue
        eligible = [event for event in native if finite(event.get("observation_time_seconds"))
                    and float(event["observation_time_seconds"]) <= checkpoint]
        event = eligible[-1] if eligible else None
        age = checkpoint - float(event["observation_time_seconds"]) if event else None
        heartbeat = 1.0 if checkpoint < 60 else (5.0 if checkpoint < 300 else 10.0)
        values.append({
            "run_id": run_id,
            "record_type": "checkpoint",
            "checkpoint_seconds": checkpoint,
            "observation_available": event is not None,
            "freshness": "not_observed" if event is None else (
                "fresh" if age <= heartbeat + 1e-9 else "stale"),
            "source_observation_time_seconds": event.get("observation_time_seconds", "") if event else "",
            "observation_age_seconds": age if age is not None else "",
            "native_best_bound": event.get("native_best_bound", "") if event else "",
            "processed_nodes": event.get("processed_nodes", "") if event else "",
            "open_nodes": event.get("open_nodes", "") if event else "",
            "simplex_iterations": event.get("simplex_iterations", "") if event else "",
            "gini_branch_count": event.get("gini_branch_count", "") if event else "",
            "ordinary_branch_count": event.get("ordinary_branch_count", "") if event else "",
            "common_same_run_ub": upper if upper is not None else "",
            "same_run_project_gap": gap(upper, event.get("native_best_bound")) if event else "",
        })
    final = next((event for event in reversed(events)
                  if event.get("retention_trigger") == "solver_final"), None)
    if final:
        values.append({
            "run_id": run_id, "record_type": "solver_final",
            "checkpoint_seconds": "solver_final", "observation_available": True,
            "freshness": "solver_final",
            "source_observation_time_seconds": final.get("observation_time_seconds", ""),
            "observation_age_seconds": 0,
            "native_best_bound": final.get("native_best_bound", ""),
            "processed_nodes": final.get("processed_nodes", ""),
            "open_nodes": final.get("open_nodes", ""),
            "simplex_iterations": final.get("simplex_iterations", ""),
            "gini_branch_count": final.get("gini_branch_count", ""),
            "ordinary_branch_count": final.get("ordinary_branch_count", ""),
            "common_same_run_ub": upper if upper is not None else "",
            "same_run_project_gap": gap(upper, final.get("native_best_bound")),
        })
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(values)


def deterministic_gzip(path: Path) -> Path:
    destination = path.with_suffix(path.suffix + ".gz")
    with path.open("rb") as source, destination.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
    path.unlink()
    return destination


def structural_audit(data: dict[str, Any], arm: str, topology: Path) -> tuple[bool, list[str]]:
    expected_mode = ARMS[arm][1]
    checks = {
        "global_tree_solved": as_bool(data.get("global_gini_tree_solved")),
        "solver_finalization": as_bool(data.get("global_gini_tree_solver_finalization_reached")),
        "lifecycle": as_bool(data.get("global_gini_tree_lifecycle_valid")),
        "recursive_branching": as_bool(data.get("global_gini_tree_recursive_branching_complete")),
        "row_migration": as_bool(data.get("global_gini_tree_row_migration_complete")),
        "root_coverage": as_bool(data.get("global_gini_tree_root_coverage_valid")),
        "branch_coverage": as_bool(data.get("global_gini_tree_branch_coverage_valid")),
        "feasibility_consistency": as_bool(data.get("feasibility_consistency_gate_passed")),
        "strict_gap_parameters": as_bool(data.get("native_mip_strict_gap_parameters_valid")),
        "model_correctness": as_bool(data.get("model_correctness_verified")),
        "independent_verifier": as_bool((data.get("verification") or {}).get(
            "original_solution_feasible", (data.get("verification") or {}).get("feasible"))),
        "callback_failures": int(data.get("global_gini_tree_callback_failures", -1)) == 0,
        "coverage_failures": int(data.get("global_gini_tree_coverage_failures", -1)) == 0,
        "column_mapping_failures": int(data.get("global_gini_tree_column_mapping_failures", -1)) == 0,
        "child_estimate_failures": int(data.get("global_gini_tree_child_estimate_failures", -1)) == 0,
        "presolve_off": int(data.get("global_gini_tree_presolve_effective", -1)) == 0,
        "reduce_none": int(data.get("global_gini_tree_preprocessing_reduce_effective", -1)) == 0,
        "linear_reductions_off": int(data.get("global_gini_tree_preprocessing_linear_effective", -1)) == 0,
        "continuous_branch_contract": as_bool(data.get("global_gini_tree_continuous_branch_presolve_valid")),
        "child_estimate_mode": data.get("global_gini_tree_child_estimate_mode") == expected_mode,
    }
    if arm == "s0m" and int(data.get("global_gini_tree_gini_children_created", 0)) > 0:
        with topology.open("r", encoding="utf-8", newline="") as stream:
            trace = list(csv.DictReader(stream))
        checks["mechanism_telemetry_present"] = bool(trace) and all(
            row.get("estimate_mode") == "dispersion-coupled" and
            row.get("validity_status") == "passed" and
            row.get("lower_validation_status") and
            row.get("upper_validation_status")
            for row in trace
        )
    failures = [name for name, passed in checks.items() if not passed]
    return not failures, failures


def base_command(instance: str) -> tuple[list[str], Path]:
    source_stage, _ = INSTANCES[instance]
    source_run = f"{source_stage}__{instance}__s0__900s__dense_on"
    source = R22 / "commands" / f"{source_run}.json"
    return list(json.loads(source.read_text(encoding="utf-8"))["command"]), source


def run_one(stage: str, instance: str, arm: str, budget: int, native: int,
            executable_sha: str, source_commit: str) -> dict[str, Any]:
    arm_label, estimate_mode, manifest_name = ARMS[arm]
    run_id = f"round23_{stage}__{instance}__{arm}__{budget}s"
    run_dir = OFFICIAL / run_id
    if run_dir.exists():
        raise RuntimeError(f"official run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True)
    command, source_command = base_command(instance)
    command[0] = str(EXE.resolve())
    set_flag(command, "--time-limit", str(native))
    set_flag(command, "--process-wall-time-limit", str(budget))
    set_flag(command, "--global-gini-tree-presolve", "off")
    set_flag(command, "--global-gini-tree-child-estimate", estimate_mode)
    set_flag(command, "--global-gini-tree-root-connectivity-flow", "false")
    set_flag(command, "--global-gini-tree-root-connectivity-flow-variant", "round20-current")
    set_flag(command, "--round22-source-commit", source_commit)
    set_flag(command, "--round22-executable-sha256", executable_sha)
    manifest = OUT / manifest_name
    set_flag(command, "--round22-production-manifest-sha256", sha(manifest))
    set_flag(command, "--dense-progress-run-id", run_id)
    set_flag(command, "--dense-progress-algorithm-arm", arm_label)
    for flag, filename in PATH_FLAGS.items():
        set_flag(command, flag, str((run_dir / filename).resolve()))
    metadata: dict[str, Any] = {
        "schema": "round23-official-command-v1",
        "run_id": run_id,
        "stage": stage,
        "instance": instance,
        "arm": arm_label,
        "source_retained_command": str(source_command.resolve()),
        "source_retained_command_sha256": sha(source_command),
        "executable": str(EXE.resolve()),
        "executable_sha256": executable_sha,
        "source_commit": source_commit,
        "instance_sha256": sha(Path(command[command.index("--input") + 1])),
        "option_manifest": str(manifest.resolve()),
        "option_manifest_sha256": sha(manifest),
        "process_wall_budget_seconds": budget,
        "native_deadline_seconds": native,
        "command": command,
        "started_at": datetime.now(timezone.utc).astimezone().isoformat(),
    }
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            command, cwd=ROOT, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, timeout=budget + 90,
        )
        metadata["return_code"] = completed.returncode
        metadata["interrupted"] = False
        (run_dir / "console.log").write_text(completed.stdout, encoding="utf-8")
    except subprocess.TimeoutExpired as error:
        metadata["return_code"] = None
        metadata["interrupted"] = True
        metadata["failure_reason"] = "runner_timeout_after_process_budget_plus_90"
        output = error.stdout or ""
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")
        (run_dir / "console.log").write_text(output, encoding="utf-8")
    metadata["runner_wall_seconds"] = time.perf_counter() - start
    metadata["finished_at"] = datetime.now(timezone.utc).astimezone().isoformat()
    result_path = run_dir / "result.json"
    if result_path.exists():
        data = json.loads(result_path.read_text(encoding="utf-8"))
        raw = run_dir / "raw_progress.csv"
        if raw.exists():
            derive_checkpoints(raw, run_dir / "canonical_checkpoints.csv", run_id, data, budget)
        passed, failures = structural_audit(data, arm, run_dir / "gini_topology.csv")
        metadata["structural_gate_passed"] = passed
        metadata["structural_gate_failures"] = failures
        metadata["result_summary"] = {
            key: data.get(key) for key in (
                "status", "native_mip_status_code", "native_mip_status_text",
                "strict_certified_original_problem", "strict_certificate_class",
                "runtime_seconds", "wall_time_seconds", "native_mip_best_bound",
                "verified_incumbent_objective", "global_gini_tree_gini_children_created",
                "global_gini_tree_sibling_first_process_count",
                "global_gini_tree_sibling_equal_estimate_pairs",
                "global_gini_tree_sibling_discriminated_pairs",
            )
        }
    else:
        metadata["structural_gate_passed"] = False
        metadata["structural_gate_failures"] = ["result_json_missing"]
    stored = []
    for filename in ("global_node_trace.csv", "raw_progress.csv", "global_root.lp"):
        path = run_dir / filename
        if path.exists() and path.stat().st_size > 1024 * 1024:
            before_sha = sha(path)
            before_size = path.stat().st_size
            compressed = deterministic_gzip(path)
            stored.append({
                "logical_path": filename, "stored_path": compressed.name,
                "original_bytes": before_size, "original_sha256": before_sha,
                "stored_bytes": compressed.stat().st_size,
                "stored_sha256": sha(compressed), "compression": "gzip_mtime_0",
            })
    if stored:
        with (run_dir / "compressed_artifacts.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(stored[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(stored)
    (run_dir / "command.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def write_stage_summary(stage: str, records: list[dict[str, Any]]) -> None:
    path = OUT / ("stage1_300s_gate_results.csv" if stage == "stage1" else "stage2_900s_results.csv")
    values = []
    for record in records:
        result = record.get("result_summary", {})
        values.append({
            "run_id": record["run_id"], "instance": record["instance"],
            "arm": record["arm"], "return_code": record.get("return_code"),
            "interrupted": record.get("interrupted"),
            "runner_wall_seconds": record.get("runner_wall_seconds"),
            "structural_gate_passed": record.get("structural_gate_passed"),
            "structural_gate_failures": "|".join(record.get("structural_gate_failures", [])),
            **result,
        })
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(values)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("stage1", "stage2"))
    args = parser.parse_args()
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    executable_sha = sha(EXE)
    if frozen.get("executable_sha256") != executable_sha:
        raise RuntimeError("Round 23 executable does not match frozen metadata")
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    instances = STAGE1 if args.stage == "stage1" else STAGE2
    budget = 300 if args.stage == "stage1" else 900
    native = budget - 18
    records = []
    for instance in instances:
        for arm in ARMS:
            record = run_one(args.stage, instance, arm, budget, native,
                             executable_sha, source_commit)
            records.append(record)
            print(json.dumps({
                "run_id": record["run_id"],
                "gate": record.get("structural_gate_passed"),
                "result": record.get("result_summary"),
            }, indent=2))
    write_stage_summary(args.stage, records)
    return 0 if all(record.get("structural_gate_passed") for record in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
