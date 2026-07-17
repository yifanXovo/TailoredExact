#!/usr/bin/env python3
"""Serial fail-closed runner and analyzer for the frozen Round 22 protocol."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
ROUND = "gf_global_gini_tree_unified_validation_round"
RESULTS = ROOT / "results" / ROUND
RAW = RESULTS / "raw"
LOGS = RESULTS / "logs"
COMMANDS = RESULTS / "commands"
RUNS = RESULTS / "runs"
ATTEMPTS = RESULTS / "attempts" / "excluded"
MECHANICAL = RESULTS / "mechanical"
EXE = ROOT / "build_round22" / "ExactEBRP-frozen.exe"
FROZEN = ROOT / "build_round22" / "frozen_executable.json"
TESTS = ROOT / "build_round22" / "release" / "tests"
PYTHON = Path(r"D:\msys64\ucrt64\bin\python.exe")
LOCK = RESULTS / ".round22_runner.lock"
REL_GAP_PARAM = 2009
ABS_GAP_PARAM = 2008
CHECKPOINTS = (1, 2, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180,
               240, 300, 450, 600, 750, 900, 1200, 1500, 1800,
               2400, 3000, 3600)
THRESHOLDS = (0.20, 0.10, 0.05, 0.02, 0.01, 0.005, 0.001)
TRAJECTORY_NUMERICAL_SCALE = 1e-6
UNIT_TESTS = (
    "ConnectivityFlowTests", "ControllingLeafSchedulerTests",
    "DenseProgressTests", "GlobalGiniTreeTests", "ModelCorrectnessTests",
    "StrictCertificateTests", "StrictSerializationTests",
)

INSTANCES: dict[str, tuple[str, str]] = {
    "V12_M1": ("reference/regen_candidate_V12_M1_average.txt", "existing"),
    "V12_M2": ("reference/regen_candidate_V12_M2_average.txt", "existing"),
    "high_imbalance_seed3201": ("reference/hard_stress/V20_M3/high_imbalance_seed3201.txt", "existing"),
    "high_imbalance_seed3202": ("reference/hard_stress/V20_M3/high_imbalance_seed3202.txt", "existing"),
    "moderate_seed3301": ("reference/hard_stress/V20_M3/moderate_seed3301.txt", "existing"),
    "moderate_seed3302": ("reference/hard_stress/V20_M3/moderate_seed3302.txt", "existing"),
    "tight_T_seed3101": ("reference/hard_stress/V20_M3/tight_T_seed3101.txt", "existing"),
    "tight_T_seed3102": ("reference/hard_stress/V20_M3/tight_T_seed3102.txt", "existing"),
    "tight_T_seed4101": ("reference/heldout_round22/V20_M3/tight_T_seed4101.txt", "heldout"),
    "tight_T_seed4102": ("reference/heldout_round22/V20_M3/tight_T_seed4102.txt", "heldout"),
    "high_imbalance_seed4201": ("reference/heldout_round22/V20_M3/high_imbalance_seed4201.txt", "heldout"),
    "high_imbalance_seed4202": ("reference/heldout_round22/V20_M3/high_imbalance_seed4202.txt", "heldout"),
    "moderate_seed4301": ("reference/heldout_round22/V20_M3/moderate_seed4301.txt", "heldout"),
    "moderate_seed4302": ("reference/heldout_round22/V20_M3/moderate_seed4302.txt", "heldout"),
}
EXISTING = tuple(key for key, value in INSTANCES.items() if value[1] == "existing")
HELDOUT = tuple(key for key, value in INSTANCES.items() if value[1] == "heldout")
LIVE = ("V12_M2", "moderate_seed3301", "high_imbalance_seed3202")
FLOWS = {"S0": "round20-current", "S1": "normalized-start-coupled", "plain": "plain"}
MANIFESTS = {
    "S0": RESULTS / "stable_mainline_manifest.json",
    "S1": RESULTS / "candidate_mainline_manifest.json",
    "plain": RESULTS / "plain_cplex_manifest.json",
}


@dataclass(frozen=True)
class RunSpec:
    stage: str
    instance: str
    arm: str
    budget: int
    dense: bool = True
    official: bool = True

    @property
    def run_id(self) -> str:
        suffix = "dense_on" if self.dense else "dense_off"
        prefix = self.stage if self.official else f"{self.stage}_overhead"
        return f"{prefix}__{self.instance}__{self.arm.lower()}__{self.budget}s__{suffix}"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def csv_write(path: Path, rows: Iterable[Mapping[str, Any]], fields: Sequence[str] = ()) -> None:
    material = [dict(row) for row in rows]
    names = list(fields)
    for row in material:
        for key in row:
            if key not in names:
                names.append(key)
    if not names:
        names = ["status"]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=names)
        writer.writeheader(); writer.writerows(material)
    os.replace(temporary, path)


def finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def as_bool(value: Any) -> bool:
    return value is True or str(value).lower() == "true"


def reserve(budget: int) -> float:
    if budget < 1 or budget > 3600:
        raise ValueError(f"invalid official budget {budget}")
    return min(30.0, max(2.0, 0.02 * budget))


def paths(spec: RunSpec) -> dict[str, Path]:
    run = RUNS / spec.run_id
    return {
        "run": run, "json": RAW / f"{spec.run_id}.json",
        "console": LOGS / f"{spec.run_id}.console.log",
        "native_log": LOGS / f"{spec.run_id}.native.log",
        "command": COMMANDS / f"{spec.run_id}.json",
        "raw_progress": run / "raw_progress.csv",
        "checkpoints": run / "canonical_checkpoints.csv",
        "progress": run / "legacy_progress.csv",
        "node": run / "global_node_trace.csv",
        "bound": run / "legacy_global_bound.csv",
        "lifecycle": run / "model_lifecycle_manifest.csv",
        "root": run / "global_root.lp", "post": run / "post_rows.csv",
        "topology": run / "gini_topology.csv", "sibling": run / "sibling_delay.csv",
        "delta": run / "row_delta.csv", "memory": run / "tree_memory.csv",
        "mip": run / "mip_start_audit.csv", "artifacts": run / "artifact_manifest.csv",
    }


def callback_off_flags() -> list[str]:
    return [
        "--tailored-bc-branching-priority", "off",
        "--tailored-bc-gini-branching", "off",
        "--tailored-bc-gini-subset-envelope", "false",
        "--tailored-bc-low-gini-l1-centering", "false",
        "--tailored-bc-local-centering", "false",
        "--tailored-bc-subset-cross-h-centering", "false",
        "--tailored-bc-local-q-centering", "false",
        "--tailored-bc-subset-inventory-imbalance", "false",
        "--tailored-bc-transfer-cutset", "false",
        "--tailored-bc-gs-product-coupling", "false",
        "--tailored-bc-disaggregated-sp-estimator", "false",
        "--tailored-bc-bucket-ratio-domain-tightening", "false",
        "--tailored-bc-bucket-subset-ratio-domain", "false",
        "--tailored-bc-bucket-integer-inventory-domain", "false",
        "--tailored-bc-bucket-required-movement", "false",
        "--tailored-bc-bucket-required-visit", "false",
        "--tailored-bc-s-bucket-ledger", "off",
    ]


def nonflow_flags() -> list[str]:
    return [
        "--tailored-bc-enabled", "true", "--tailored-bc-mode", "static",
        "--tailored-bc-callback-cut-profile", "off",
        "--compact-bc-root-cut-rounds", "0",
        "--compact-bc-dynamic-cut-families", "none",
        "--compact-bc-cut-profile", "balanced",
        "--compact-bc-low-gini-strengthening", "safe",
        "--compact-bc-denominator-bound-mode", "tight",
        "--compact-bc-objective-estimator-mode", "adaptive",
        "--compact-bc-domain-propagation-mode", "iterative",
        "--compact-bc-domain-propagation-rounds", "2",
        "--compact-bc-variable-s-centering", "true",
        "--compact-bc-sp-product-estimator", "paper-safe",
        "--compact-bc-sp-product-bounds", "tight",
        "--compact-bc-s-range-refinement", "off",
    ] + callback_off_flags()


def frozen_data() -> dict[str, Any]:
    if not FROZEN.exists() or not EXE.exists():
        raise RuntimeError("Round 22 executable is not frozen; run build_round22_release.py --clean")
    data = json.loads(FROZEN.read_text(encoding="utf-8"))
    if sha(EXE) != data.get("executable_sha256"):
        raise RuntimeError("frozen executable SHA-256 mismatch")
    return data


def command(spec: RunSpec, p: Mapping[str, Path], frozen: Mapping[str, Any]) -> list[str]:
    manifest_hash = sha(MANIFESTS[spec.arm])
    provenance = [
        "--round22-production-mode", "true" if spec.official else "false",
        "--round22-source-commit", str(frozen["source_commit"]),
        "--round22-executable-sha256", str(frozen["executable_sha256"]),
        "--round22-production-manifest-sha256", manifest_hash,
        "--dense-progress", "true" if spec.dense else "false",
        "--dense-progress-run-id", spec.run_id,
        "--dense-progress-raw", str(p["raw_progress"]),
        "--dense-progress-checkpoints", str(p["checkpoints"]),
        "--dense-progress-algorithm-arm", spec.arm,
    ]
    common = [
        str(EXE), "--input", str(ROOT / INSTANCES[spec.instance][0]),
        "--lambda", "0.15", "--T", "3600",
        "--time-limit", format(spec.budget - reserve(spec.budget), ".17g"),
        "--process-wall-time-limit", str(spec.budget),
        "--threads", "1", "--mip-threads", "1", "--cplex-threads", "1",
        "--progress-log", str(p["progress"]), "--progress-interval-seconds", "30",
        "--log", str(p["native_log"]), "--out", str(p["json"]),
    ]
    if spec.arm == "plain":
        return common[:1] + ["--method", "cplex", "--plain-baseline"] + common[1:] + provenance
    return common[:1] + [
        "--method", "gcap-frontier", "--algorithm-preset", "paper-gf-tailored-bc",
        "--paper-run-sealed", "true",
    ] + common[1:17] + ["--compact-bc-threads", "1", "--primal-heuristic", "hga-tgbc"] + common[17:] + nonflow_flags() + [
        "--frontier-execution-mode", "global-gini-tree",
        "--global-gini-tree-presolve", "on",
        "--global-gini-tree-search", "traditional",
        "--global-gini-tree-child-estimate", "parent-copy",
        "--global-gini-tree-row-attachment", "full-inherited-pack",
        "--global-gini-tree-row-timing", "deferred",
        "--global-gini-tree-native-mip-start", "false",
        "--global-gini-tree-root-connectivity-flow", "false",
        "--global-gini-tree-root-connectivity-flow-variant", FLOWS[spec.arm],
        "--global-gini-tree-node-trace", str(p["node"]),
        "--global-gini-tree-bound-trace", str(p["bound"]),
        "--global-gini-tree-manifest", str(p["lifecycle"]),
        "--global-gini-tree-root-export", str(p["root"]),
        "--global-gini-tree-post-row-trace", str(p["post"]),
        "--global-gini-tree-topology-trace", str(p["topology"]),
        "--global-gini-tree-sibling-trace", str(p["sibling"]),
        "--global-gini-tree-row-delta-trace", str(p["delta"]),
        "--global-gini-tree-memory-trace", str(p["memory"]),
        "--global-gini-tree-mip-start-audit", str(p["mip"]),
    ] + provenance


def heartbeat(elapsed: float) -> float:
    if elapsed < 60: return 1.0
    if elapsed < 300: return 5.0
    if elapsed < 900: return 10.0
    return 30.0


def verified_ub(data: Mapping[str, Any]) -> float | None:
    if as_bool(data.get("verified_incumbent_objective_available")) and finite(
            data.get("verified_incumbent_objective")):
        return float(data["verified_incumbent_objective"])
    verification = data.get("verification") or {}
    if as_bool(verification.get("original_solution_feasible", verification.get("feasible"))) and finite(
            verification.get("objective")):
        return float(verification["objective"])
    return None


def gap(ub: float | None, lb: Any) -> float | None:
    if ub is None or not finite(lb): return None
    residual = max(0.0, ub - float(lb))
    return residual / abs(ub) if abs(ub) > 1e-12 else (0.0 if residual == 0 else math.inf)


def read_events(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def derive_checkpoints(spec: RunSpec, p: Mapping[str, Path], data: Mapping[str, Any]) -> list[dict[str, Any]]:
    events = read_events(p["raw_progress"])
    ub = verified_ub(data)
    rows: list[dict[str, Any]] = []
    native_events = [event for event in events if event.get("retention_trigger") != "solver_final"]
    for checkpoint in CHECKPOINTS:
        if checkpoint > spec.budget: continue
        eligible = [event for event in native_events
                    if finite(event.get("observation_time_seconds"))
                    and float(event["observation_time_seconds"]) <= checkpoint + 1e-12]
        event = eligible[-1] if eligible else None
        age = checkpoint - float(event["observation_time_seconds"]) if event else None
        freshness = "not_observed" if event is None else (
            "fresh" if age is not None and age <= heartbeat(checkpoint) + 1e-9 else "stale")
        row: dict[str, Any] = {
            "run_id": spec.run_id, "stage": spec.stage, "suite": INSTANCES[spec.instance][1],
            "instance": spec.instance, "arm": spec.arm, "flow": FLOWS[spec.arm],
            "record_type": "checkpoint", "checkpoint_seconds": checkpoint,
            "observation_available": event is not None, "freshness": freshness,
            "source_observation_time_seconds": event.get("observation_time_seconds", "") if event else "",
            "observation_age_seconds": age if age is not None else "",
            "analysis_reference_verified_ub": ub if ub is not None else "",
        }
        for field in ("observation_source", "callback_context", "phase", "native_best_bound",
                      "native_incumbent", "verified_same_run_ub", "native_cplex_gap",
                      "processed_nodes", "open_nodes", "native_solution_count",
                      "simplex_iterations", "tree_memory_mb", "gini_branch_count",
                      "ordinary_branch_count", "current_open_gini_siblings",
                      "oldest_gini_sibling_delay_seconds", "maximum_gini_sibling_delay_seconds"):
            row[field] = event.get(field, "") if event else ""
        project_gap = gap(ub, row["native_best_bound"])
        row["analysis_project_gap"] = project_gap if project_gap is not None else ""
        rows.append(row)
    final = next((event for event in reversed(events)
                  if event.get("retention_trigger") == "solver_final"), None)
    if final:
        row = {
            "run_id": spec.run_id, "stage": spec.stage, "suite": INSTANCES[spec.instance][1],
            "instance": spec.instance, "arm": spec.arm, "flow": FLOWS[spec.arm],
            "record_type": "solver_final", "checkpoint_seconds": "solver_final",
            "observation_available": True, "freshness": "solver_final",
            "source_observation_time_seconds": final.get("observation_time_seconds", ""),
            "observation_age_seconds": 0, "analysis_reference_verified_ub": ub if ub is not None else "",
        }
        for field in ("observation_source", "callback_context", "phase", "native_best_bound",
                      "native_incumbent", "verified_same_run_ub", "native_cplex_gap",
                      "processed_nodes", "open_nodes", "native_solution_count",
                      "simplex_iterations", "tree_memory_mb", "gini_branch_count",
                      "ordinary_branch_count", "current_open_gini_siblings",
                      "oldest_gini_sibling_delay_seconds", "maximum_gini_sibling_delay_seconds"):
            row[field] = final.get(field, "")
        project_gap = gap(ub, row["native_best_bound"])
        row["analysis_project_gap"] = project_gap if project_gap is not None else ""
        rows.append(row)
    csv_write(p["checkpoints"], rows)
    return rows


def integrity(spec: RunSpec, p: Mapping[str, Path], data: Mapping[str, Any]) -> dict[str, Any]:
    events = read_events(p["raw_progress"])
    errors: list[str] = []
    previous_time = -math.inf; previous_lb: float | None = None
    previous_inc: float | None = None; previous_nodes: int | None = None
    lb_negative_steps = 0; lb_material_negative_steps = 0; lb_max_negative_step = 0.0
    incumbent_positive_steps = 0; incumbent_material_positive_steps = 0
    incumbent_max_positive_step = 0.0
    for event in events:
        current_time = float(event["observation_time_seconds"])
        if current_time <= previous_time: errors.append("timestamp_not_strict")
        previous_time = current_time
        if finite(event.get("native_best_bound")):
            current = float(event["native_best_bound"])
            if previous_lb is not None and current < previous_lb:
                decrease = previous_lb - current
                lb_negative_steps += 1
                lb_max_negative_step = max(lb_max_negative_step, decrease)
                material_scale = TRAJECTORY_NUMERICAL_SCALE * max(
                    1.0, abs(previous_lb), abs(current))
                if decrease > material_scale:
                    lb_material_negative_steps += 1
                    errors.append("lower_bound_material_decrease")
            previous_lb = current
        if finite(event.get("native_incumbent")):
            current = float(event["native_incumbent"])
            if previous_inc is not None and current > previous_inc:
                increase = current - previous_inc
                incumbent_positive_steps += 1
                incumbent_max_positive_step = max(
                    incumbent_max_positive_step, increase)
                material_scale = TRAJECTORY_NUMERICAL_SCALE * max(
                    1.0, abs(previous_inc), abs(current))
                if increase > material_scale:
                    incumbent_material_positive_steps += 1
                    errors.append("incumbent_material_increase")
            previous_inc = current
        if event.get("processed_nodes", "") != "":
            current_nodes = int(float(event["processed_nodes"]))
            if previous_nodes is not None and current_nodes < previous_nodes:
                errors.append("processed_nodes_decreased")
            previous_nodes = current_nodes
    final = next((event for event in reversed(events)
                  if event.get("retention_trigger") == "solver_final"), None)
    if final is None: errors.append("solver_final_missing")
    elif as_bool(data.get("native_mip_best_bound_available")):
        if not finite(final.get("native_best_bound")) or float(final["native_best_bound"]) != float(data["native_mip_best_bound"]):
            errors.append("final_bound_json_mismatch")
    return {
        "run_id": spec.run_id, "stage": spec.stage, "instance": spec.instance,
        "arm": spec.arm, "event_count": len(events),
        "timestamps_strict": "timestamp_not_strict" not in errors,
        "trajectory_numerical_scale": TRAJECTORY_NUMERICAL_SCALE,
        "raw_values_reported_not_repaired": True,
        "lower_bound_nondecreasing": lb_negative_steps == 0,
        "lower_bound_no_material_decrease": lb_material_negative_steps == 0,
        "lower_bound_negative_step_count": lb_negative_steps,
        "lower_bound_material_negative_step_count": lb_material_negative_steps,
        "lower_bound_max_negative_step": lb_max_negative_step,
        "incumbent_nonincreasing": incumbent_positive_steps == 0,
        "incumbent_no_material_increase": incumbent_material_positive_steps == 0,
        "incumbent_positive_step_count": incumbent_positive_steps,
        "incumbent_material_positive_step_count": incumbent_material_positive_steps,
        "incumbent_max_positive_step": incumbent_max_positive_step,
        "node_counters_consistent": "processed_nodes_decreased" not in errors,
        "solver_final_present": final is not None,
        "endpoint_matches_json": "final_bound_json_mismatch" not in errors,
        "error_count": len(errors), "errors": "|".join(sorted(set(errors))),
    }


def stage1_dense_quality(spec: RunSpec, p: Mapping[str, Path],
                         checkpoint_rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """Fail closed when the preregistered live gate is only nominally dense."""
    if not (spec.official and spec.stage == "stage1" and spec.dense):
        return []
    events = read_events(p["raw_progress"])
    native_events = [event for event in events
                     if event.get("retention_trigger") != "solver_final"]
    scheduled = [row for row in checkpoint_rows if row.get("record_type") == "checkpoint"]
    fresh = sum(row.get("freshness") == "fresh" for row in scheduled)
    failures: list[str] = []
    if len(scheduled) != 11:
        failures.append(f"stage1_dense_checkpoint_count:{len(scheduled)}/11")
    if len(native_events) < 20:
        failures.append(f"stage1_dense_native_event_count:{len(native_events)}")
    if fresh < 9:
        failures.append(f"stage1_dense_fresh_checkpoints:{fresh}/{len(scheduled)}")
    if spec.arm == "plain":
        progress_records = sum(event.get("callback_context") in
                               ("local_progress", "global_progress")
                               for event in native_events)
        if progress_records == 0:
            failures.append("stage1_plain_supported_progress_context_missing")
    else:
        relaxation_records = sum(
            event.get("observation_source") ==
            "cplex_generic_relaxation_read_only_progress"
            for event in native_events)
        if relaxation_records == 0:
            failures.append("stage1_tailored_relaxation_progress_missing")
    return failures


def validate(spec: RunSpec, p: Mapping[str, Path], frozen: Mapping[str, Any],
             data: Mapping[str, Any], return_code: int) -> list[str]:
    failures: list[str] = []
    def require(condition: bool, name: str) -> None:
        if not condition: failures.append(name)
    require(return_code == 0, "process_return_code")
    require(data.get("native_mip_status_code") in (101, 102, 103, 107, 108, 115), "native_status")
    require(data.get("native_mip_relative_gap_param_id") == REL_GAP_PARAM, "relative_gap_id")
    require(data.get("native_mip_relative_gap_requested") == 0, "relative_gap_requested")
    require(data.get("native_mip_relative_gap_set_return_code") == 0, "relative_gap_set")
    require(data.get("native_mip_relative_gap_get_return_code") == 0, "relative_gap_get")
    require(data.get("native_mip_relative_gap_effective") == 0, "relative_gap_readback")
    require(data.get("native_mip_absolute_gap_param_id") == ABS_GAP_PARAM, "absolute_gap_id")
    require(data.get("native_mip_absolute_gap_requested") == 0, "absolute_gap_requested")
    require(data.get("native_mip_absolute_gap_set_return_code") == 0, "absolute_gap_set")
    require(data.get("native_mip_absolute_gap_get_return_code") == 0, "absolute_gap_get")
    require(data.get("native_mip_absolute_gap_effective") == 0, "absolute_gap_readback")
    require(as_bool(data.get("native_mip_lifecycle_valid")), "native_lifecycle")
    require(as_bool(data.get("native_mip_solver_finalization_reached")), "native_finalization")
    require(data.get("model_correctness_executable_sha256") == frozen["executable_sha256"], "executable_hash")
    require(data.get("model_correctness_source_commit_sha") == frozen["source_commit"], "source_commit")
    require(data.get("model_correctness_production_option_manifest_sha256") == sha(MANIFESTS[spec.arm]), "manifest_hash")
    if spec.official:
        require(as_bool(data.get("model_correctness_verified")), "model_correctness")
    if spec.dense:
        require(as_bool(data.get("dense_progress_enabled")), "dense_enabled")
        require(as_bool(data.get("dense_progress_final_record_appended")), "dense_final")
        require(as_bool(data.get("dense_progress_flush_succeeded")), "dense_flush")
        require(as_bool(data.get("dense_progress_read_only_contract")), "dense_read_only")
        require(p["raw_progress"].exists(), "dense_raw_missing")
    if spec.arm != "plain":
        require(data.get("global_gini_tree_root_connectivity_flow_variant_resolved") == FLOWS[spec.arm], "flow")
        require(data.get("global_gini_tree_child_estimate_mode") == "parent-copy", "child_estimate")
        require(data.get("global_gini_tree_row_attachment_mode") == "full-inherited-pack", "row_attachment")
        require(data.get("global_gini_tree_row_timing_mode") == "deferred", "row_timing")
        require(not as_bool(data.get("global_gini_tree_native_mip_start_attempted")), "native_mip_start")
    if spec.official and data.get("native_mip_status_code") == 101:
        require(as_bool(data.get("strict_certified_original_problem")), "status101_not_strict")
        require(data.get("strict_certificate_class") == "native_engineering_exact_optimal", "status101_class")
        verification = data.get("verification") or {}
        require(as_bool(verification.get("original_solution_feasible", verification.get("feasible"))), "status101_verifier")
    if data.get("native_mip_status_code") == 102:
        require(not as_bool(data.get("strict_certified_original_problem")), "status102_false_promotion")
        require(data.get("strict_certificate_class") == "native_tolerance_optimal_only", "status102_class")
    return failures


def artifact_manifest(p: Mapping[str, Path]) -> None:
    rows = []
    for path in sorted(p["run"].glob("*")) + [p["json"], p["console"], p["native_log"], p["command"]]:
        if path.exists() and path.is_file():
            rows.append({"path": relative(path), "bytes": path.stat().st_size, "sha256": sha(path)})
    csv_write(p["artifacts"], rows)


def existing_valid(spec: RunSpec, p: Mapping[str, Path], frozen: Mapping[str, Any]) -> bool:
    if not (p["json"].exists() and p["command"].exists()): return False
    try:
        record = json.loads(p["command"].read_text(encoding="utf-8"))
        data = json.loads(p["json"].read_text(encoding="utf-8"))
        return (record.get("validation_passed") is True
                and record.get("executable_sha256") == frozen["executable_sha256"]
                and record.get("source_commit") == frozen["source_commit"]
                and not validate(spec, p, frozen, data, int(record.get("return_code", -1))))
    except Exception:
        return False


def run_one(spec: RunSpec, frozen: Mapping[str, Any], dry_run: bool = False) -> dict[str, Any]:
    p = paths(spec)
    for key in ("run",): p[key].mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True); LOGS.mkdir(parents=True, exist_ok=True)
    COMMANDS.mkdir(parents=True, exist_ok=True)
    cmd = command(spec, p, frozen)
    if existing_valid(spec, p, frozen):
        print(f"RESUME {spec.run_id}", flush=True)
        return json.loads(p["json"].read_text(encoding="utf-8"))
    if dry_run:
        print(subprocess.list2cmdline(cmd)); return {}
    if any(proc.stdout for proc in []):  # explicit serial-run marker
        raise RuntimeError("unreachable")
    signature = hashlib.sha256("\0".join(cmd).encode()).hexdigest()
    record = {
        "schema": "round22-command-v1", "run_id": spec.run_id,
        "stage": spec.stage, "suite": INSTANCES[spec.instance][1],
        "instance": spec.instance, "arm": spec.arm, "flow": FLOWS[spec.arm],
        "budget_seconds": spec.budget, "native_reserve_seconds": reserve(spec.budget),
        "dense_progress": spec.dense, "official": spec.official,
        "source_commit": frozen["source_commit"],
        "executable_sha256": frozen["executable_sha256"],
        "manifest_sha256": sha(MANIFESTS[spec.arm]),
        "instance_sha256": sha(ROOT / INSTANCES[spec.instance][0]),
        "command": cmd, "command_signature": signature,
        "host": socket.gethostname(), "platform": platform.platform(),
        "started_at": now(), "validation_passed": False,
    }
    json_write(p["command"], record)
    print(f"START {spec.run_id} {now()}", flush=True)
    started = time.perf_counter()
    timed_out = False
    with p["console"].open("w", encoding="utf-8", errors="replace") as console:
        try:
            completed = subprocess.run(cmd, cwd=ROOT, stdout=console,
                                       stderr=subprocess.STDOUT,
                                       timeout=spec.budget + 30, check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            timed_out = True; return_code = 124
    elapsed = time.perf_counter() - started
    record.update({"finished_at": now(), "runner_wall_seconds": elapsed,
                   "return_code": return_code, "emergency_timeout": timed_out})
    data: dict[str, Any] = {}
    failures = ["result_json_missing"]
    if p["json"].exists():
        try:
            data = json.loads(p["json"].read_text(encoding="utf-8"))
            failures = validate(spec, p, frozen, data, return_code)
            if spec.dense and p["raw_progress"].exists():
                checkpoint_rows = derive_checkpoints(spec, p, data)
                audit = integrity(spec, p, data)
                if audit["error_count"]:
                    failures.append("trajectory_integrity:" + audit["errors"])
                failures.extend(stage1_dense_quality(spec, p, checkpoint_rows))
        except Exception as exc:
            failures = [f"validation_exception:{type(exc).__name__}:{exc}"]
    record["validation_failures"] = failures
    record["validation_passed"] = not failures
    json_write(p["command"], record)
    artifact_manifest(p)
    if failures:
        attempt = ATTEMPTS / spec.run_id
        attempt.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p["command"], attempt / "command.json")
        if p["console"].exists(): shutil.copy2(p["console"], attempt / "console.log")
        if p["native_log"].exists(): shutil.copy2(p["native_log"], attempt / "native.log")
        if p["json"].exists(): shutil.copy2(p["json"], attempt / "result.json")
        if p["run"].exists():
            archived_run = attempt / "run_artifacts"
            if archived_run.exists(): shutil.rmtree(archived_run)
            shutil.copytree(p["run"], archived_run)
        print(f"FAIL {spec.run_id}: {'|'.join(failures)}", flush=True)
        raise RuntimeError(f"official validation failed for {spec.run_id}")
    print(f"PASS {spec.run_id} wall={elapsed:.3f}s", flush=True)
    return data


def stage_specs(stage: str) -> list[RunSpec]:
    if stage == "stage1":
        live = [RunSpec(stage, instance, arm, 120)
                for instance in LIVE for arm in ("S0", "S1", "plain")]
        overhead = [RunSpec(stage, instance, arm, 300, dense, False)
                    for instance in LIVE for arm in ("S0", "S1") for dense in (False, True)]
        return live + overhead
    if stage == "stage2":
        return [RunSpec(stage, instance, arm, 900)
                for instance in EXISTING for arm in ("S0", "S1", "plain")]
    if stage == "stage3":
        return [RunSpec(stage, instance, arm, 1800)
                for instance in EXISTING for arm in ("S0", "S1", "plain")]
    if stage == "stage4":
        return [RunSpec(stage, instance, arm, 900)
                for instance in HELDOUT for arm in ("S0", "S1", "plain")]
    raise ValueError(stage)


def run_stage0() -> None:
    rows: list[dict[str, Any]] = []
    commands: list[tuple[str, list[str]]] = []
    for name in UNIT_TESTS:
        commands.append((name, [str(TESTS / f"{name}.exe")]))
    commands.extend([
        ("round20_regression_tests", [str(PYTHON), str(ROOT / "tests" / "round20_regression_tests.py")]),
        ("round22_runner_integrity_tests", [str(PYTHON), str(ROOT / "tests" / "round22_runner_integrity_tests.py")]),
        ("round22_static_audit", [str(PYTHON), str(ROOT / "scripts" / "round22_static_audit.py")]),
        ("round22_certificate_migration", [str(PYTHON), str(ROOT / "scripts" / "round22_certificate_migration_audit.py")]),
    ])
    MECHANICAL.mkdir(parents=True, exist_ok=True)
    for name, cmd in commands:
        log = MECHANICAL / f"{name}.log"; started = time.perf_counter()
        with log.open("w", encoding="utf-8") as stream:
            completed = subprocess.run(cmd, cwd=ROOT, stdout=stream,
                                       stderr=subprocess.STDOUT, check=False)
        rows.append({"test": name, "status": "PASS" if completed.returncode == 0 else "FAIL",
                     "return_code": completed.returncode,
                     "wall_seconds": time.perf_counter() - started,
                     "command": subprocess.list2cmdline(cmd), "log": relative(log)})
        if completed.returncode != 0:
            csv_write(MECHANICAL / "stage0_tests.csv", rows)
            raise RuntimeError(f"stage0 failed: {name}")
    csv_write(MECHANICAL / "stage0_tests.csv", rows)
    print(f"Stage 0 PASS: {len(rows)} executable/script gates", flush=True)


def official_records() -> list[tuple[RunSpec, dict[str, Any], dict[str, Any]]]:
    records = []
    for path in sorted(COMMANDS.glob("*.json")):
        command_record = json.loads(path.read_text(encoding="utf-8"))
        if command_record.get("official") is not True or command_record.get("validation_passed") is not True:
            continue
        spec = RunSpec(str(command_record["stage"]), str(command_record["instance"]),
                       str(command_record["arm"]), int(command_record["budget_seconds"]),
                       bool(command_record["dense_progress"]), True)
        result_path = RAW / f"{spec.run_id}.json"
        if result_path.exists():
            records.append((spec, command_record,
                            json.loads(result_path.read_text(encoding="utf-8"))))
    return records


def summary_row(spec: RunSpec, data: Mapping[str, Any]) -> dict[str, Any]:
    ub = verified_ub(data); lb = data.get("native_mip_best_bound", "")
    return {
        "run_id": spec.run_id, "stage": spec.stage, "suite": INSTANCES[spec.instance][1],
        "instance": spec.instance, "arm": spec.arm, "flow": FLOWS[spec.arm],
        "budget_seconds": spec.budget, "native_status_code": data.get("native_mip_status_code", ""),
        "native_status_text": data.get("native_mip_status_text", ""),
        "strict_certificate_class": data.get("strict_certificate_class", ""),
        "strict_certified": data.get("strict_certified_original_problem", False),
        "runtime_seconds": data.get("runtime_seconds", ""),
        "native_objective": data.get("native_mip_objective", ""),
        "native_best_bound": lb, "verified_ub": ub if ub is not None else "",
        "project_gap": gap(ub, lb) if gap(ub, lb) is not None else "",
        "recomputed_objective": (data.get("verification") or {}).get("objective", ""),
        "mapping_residual": data.get("native_vs_recomputed_objective_residual", ""),
        "mapping_diagnostic": data.get("objective_mapping_diagnostic", ""),
        "nodes": data.get("native_mip_node_count", data.get("nodes", "")),
        "open_nodes": data.get("native_mip_open_node_count", data.get("open_nodes", "")),
        "simplex_iterations": data.get("global_gini_tree_native_simplex_iterations", ""),
        "gini_branches": data.get("global_gini_tree_gini_branch_nodes", 0),
        "ordinary_branches": data.get("global_gini_tree_ordinary_branch_fallbacks", 0),
        "dense_callback_invocations": data.get("dense_progress_callback_invocation_count", ""),
        "dense_records": data.get("dense_progress_record_count", ""),
        "instrumentation_percent": data.get("dense_progress_instrumentation_wall_percent", ""),
        "model_correctness_verified": data.get("model_correctness_verified", False),
        "independent_verifier_passed": (data.get("verification") or {}).get(
            "original_solution_feasible", (data.get("verification") or {}).get("feasible", False)),
    }


def auc_and_crossings(spec: RunSpec, data: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    event_path = paths(spec)["raw_progress"]
    events = read_events(event_path); ub = verified_ub(data)
    points = [(float(e["observation_time_seconds"]), gap(ub, e.get("native_best_bound")))
              for e in events if finite(e.get("observation_time_seconds"))
              and finite(e.get("native_best_bound"))]
    points = [(t, g) for t, g in points if g is not None]
    area = 0.0
    for (t0, g0), (t1, g1) in zip(points, points[1:]):
        area += max(0.0, t1 - t0) * ((max(0.0, min(1.0, 1-g0)) +
                                      max(0.0, min(1.0, 1-g1))) / 2.0)
    horizon = points[-1][0] - points[0][0] if len(points) > 1 else 0.0
    auc = {
        "run_id": spec.run_id, "stage": spec.stage, "instance": spec.instance,
        "arm": spec.arm, "verified_ub": ub if ub is not None else "",
        "observed_horizon_seconds": horizon,
        "normalized_bound_progress_auc": area / horizon if horizon > 0 else "",
        "raw_area": area, "observation_count": len(points),
    }
    crossings = []
    for threshold in THRESHOLDS:
        found = None; previous = None
        for point in points:
            if point[1] <= threshold:
                found = point; break
            previous = point
        crossings.append({
            "run_id": spec.run_id, "stage": spec.stage, "instance": spec.instance,
            "arm": spec.arm, "gap_threshold": threshold,
            "crossing_observed": found is not None,
            "preceding_observation_seconds": previous[0] if previous else "",
            "preceding_gap": previous[1] if previous else "",
            "first_observed_crossing_seconds": found[0] if found else "",
            "first_observed_gap": found[1] if found else "",
            "crossing_interval_lower_seconds": previous[0] if previous else "",
            "crossing_interval_upper_seconds": found[0] if found else "",
        })
    return auc, crossings


def analyze() -> None:
    records = official_records(); summaries = [summary_row(spec, data) for spec, _, data in records]
    by_stage = {stage: [row for row in summaries if row["stage"] == stage]
                for stage in ("stage1", "stage2", "stage3", "stage4", "stage5")}
    csv_write(RESULTS / "existing_suite_900s.csv", by_stage["stage2"])
    csv_write(RESULTS / "existing_suite_1800s.csv", by_stage["stage3"])
    csv_write(RESULTS / "heldout_suite_900s.csv", by_stage["stage4"])
    csv_write(RESULTS / "strict_certificate_summary.csv", summaries)
    csv_write(RESULTS / "time_to_strict_certificate.csv", [{
        "run_id": row["run_id"], "stage": row["stage"], "instance": row["instance"],
        "arm": row["arm"], "strict_certified": row["strict_certified"],
        "time_to_strict_certificate_seconds": row["runtime_seconds"] if as_bool(row["strict_certified"]) else "",
    } for row in summaries])
    audits = []; completeness = []; auc_rows = []; crossing_rows = []
    for spec, _, data in records:
        p = paths(spec); audit = integrity(spec, p, data); audits.append(audit)
        checkpoints = list(csv.DictReader(p["checkpoints"].open(encoding="utf-8")))
        scheduled = [row for row in checkpoints if row["record_type"] == "checkpoint"]
        events = read_events(p["raw_progress"])
        times = [float(e["observation_time_seconds"]) for e in events]
        completeness.append({
            "run_id": spec.run_id, "stage": spec.stage, "instance": spec.instance,
            "arm": spec.arm, "raw_event_count": len(events),
            "first_observation_seconds": min(times) if times else "",
            "last_observation_seconds": max(times) if times else "",
            "local_progress_records": sum(e.get("callback_context") == "local_progress" for e in events),
            "global_progress_records": sum(e.get("callback_context") == "global_progress" for e in events),
            "relaxation_progress_records": sum(
                e.get("observation_source") == "cplex_generic_relaxation_read_only_progress"
                for e in events),
            "fresh_checkpoints": sum(r["freshness"] == "fresh" for r in scheduled),
            "stale_checkpoints": sum(r["freshness"] == "stale" for r in scheduled),
            "not_observed_checkpoints": sum(r["freshness"] == "not_observed" for r in scheduled),
            "solver_final_rows": sum(r["record_type"] == "solver_final" for r in checkpoints),
        })
        auc, crossings = auc_and_crossings(spec, data)
        auc_rows.append(auc); crossing_rows.extend(crossings)
    csv_write(RESULTS / "trajectory_integrity_audit.csv", audits)
    csv_write(RESULTS / "trajectory_completeness.csv", completeness)
    csv_write(RESULTS / "bound_progress_auc.csv", auc_rows)
    csv_write(RESULTS / "time_to_gap_thresholds.csv", crossing_rows)
    overhead_rows = []
    for path in sorted(COMMANDS.glob("stage1_overhead*.json")):
        rec = json.loads(path.read_text(encoding="utf-8")); result_path = RAW / f"{rec['run_id']}.json"
        if result_path.exists() and rec.get("validation_passed"):
            data = json.loads(result_path.read_text(encoding="utf-8"))
            overhead_rows.append({
                "run_id": rec["run_id"], "instance": rec["instance"], "arm": rec["arm"],
                "dense_progress": rec["dense_progress"], "runner_wall_seconds": rec["runner_wall_seconds"],
                "solver_runtime_seconds": data.get("runtime_seconds", ""),
                "callback_invocations": data.get("dense_progress_callback_invocation_count", 0),
                "retained_records": data.get("dense_progress_record_count", 0),
                "callback_wall_seconds": data.get("dense_progress_callback_wall_seconds", 0),
                "serialization_seconds": data.get("dense_progress_serialization_seconds", 0),
                "peak_buffer_bytes": data.get("dense_progress_peak_buffer_bytes", 0),
                "instrumentation_percent": data.get("dense_progress_instrumentation_wall_percent", 0),
                "native_status_code": data.get("native_mip_status_code", ""),
                "native_best_bound": data.get("native_mip_best_bound", ""),
            })
    overhead_pairs: dict[tuple[str, str], dict[bool, dict[str, Any]]] = {}
    for row in overhead_rows:
        overhead_pairs.setdefault((str(row["instance"]), str(row["arm"])), {})[
            as_bool(row["dense_progress"])] = row
    for row in overhead_rows:
        pair = overhead_pairs[(str(row["instance"]), str(row["arm"]))]
        off = pair.get(False); on = pair.get(True)
        row["matched_pair_complete"] = off is not None and on is not None
        row["matched_pair_id"] = f"{row['instance']}__{row['arm']}"
        for clock in ("runner_wall_seconds", "solver_runtime_seconds"):
            off_value = float(off[clock]) if off is not None and finite(off.get(clock)) else None
            on_value = float(on[clock]) if on is not None and finite(on.get(clock)) else None
            delta = on_value - off_value if off_value is not None and on_value is not None else None
            percent = (100.0 * delta / off_value
                       if delta is not None and off_value is not None and off_value != 0 else None)
            row[f"matched_dense_off_{clock}"] = off_value if off_value is not None else ""
            row[f"matched_dense_on_{clock}"] = on_value if on_value is not None else ""
            row[f"matched_dense_on_minus_off_{clock}"] = delta if delta is not None else ""
            row[f"matched_dense_on_minus_off_{clock}_percent"] = percent if percent is not None else ""
    csv_write(RESULTS / "progress_callback_overhead.csv", overhead_rows)
    paired = []
    auc_map = {row["run_id"]: row for row in auc_rows}
    for stage in ("stage2", "stage3", "stage4", "stage5"):
        instances = sorted({r["instance"] for r in by_stage[stage]})
        for instance in instances:
            arms = {r["arm"]: r for r in by_stage[stage] if r["instance"] == instance}
            if "S0" not in arms or "S1" not in arms: continue
            a, b = arms["S0"], arms["S1"]
            classification = "tie"; reason = "within_tolerance"
            if as_bool(a["strict_certified"]) != as_bool(b["strict_certified"]):
                classification = "improve" if as_bool(b["strict_certified"]) else "regress"
                reason = "strict_certificate"
            elif as_bool(a["strict_certified"]) and as_bool(b["strict_certified"]):
                delta = float(a["runtime_seconds"]) - float(b["runtime_seconds"])
                if abs(delta) > 1e-6: classification = "improve" if delta > 0 else "regress"
                reason = "strict_time"
            elif finite(a["native_best_bound"]) and finite(b["native_best_bound"]):
                delta = float(b["native_best_bound"]) - float(a["native_best_bound"])
                tol = 1e-9 * max(1.0, abs(float(a["native_best_bound"])), abs(float(b["native_best_bound"])))
                if abs(delta) > tol: classification = "improve" if delta > 0 else "regress"
                reason = "final_native_lower_bound"
                if classification == "tie":
                    aa = auc_map.get(a["run_id"], {}).get("normalized_bound_progress_auc", "")
                    bb = auc_map.get(b["run_id"], {}).get("normalized_bound_progress_auc", "")
                    if finite(aa) and finite(bb) and abs(float(bb)-float(aa)) > 1e-6:
                        classification = "improve" if float(bb) > float(aa) else "regress"
                        reason = "normalized_auc"
            else:
                classification = "unavailable"; reason = "missing_comparable_bound"
            paired.append({
                "stage": stage, "suite": a["suite"], "instance": instance,
                "S0_status": a["native_status_code"], "S1_status": b["native_status_code"],
                "S0_strict": a["strict_certified"], "S1_strict": b["strict_certified"],
                "S0_native_lb": a["native_best_bound"], "S1_native_lb": b["native_best_bound"],
                "S0_project_gap": a["project_gap"], "S1_project_gap": b["project_gap"],
                "S1_vs_S0": classification, "decision_basis": reason,
            })
    csv_write(RESULTS / "paired_algorithm_comparison.csv", paired)
    print(f"Analyzed {len(records)} official rows", flush=True)


def selected_stage5() -> list[RunSpec]:
    analyze()
    summaries = list(csv.DictReader((RESULTS / "strict_certificate_summary.csv").open(encoding="utf-8")))
    selected: list[str] = []
    v12 = [row for row in summaries if row["stage"] == "stage3" and row["instance"] == "V12_M2"]
    if any(row["native_status_code"] == "101" and not as_bool(row["strict_certified"]) for row in v12):
        selected.append("V12_M2")
    for stage, suite in (("stage3", "existing"), ("stage4", "heldout")):
        eligible = [row for row in summaries if row["stage"] == stage and row["suite"] == suite
                    and not row["instance"].startswith("V12_") and finite(row["project_gap"])]
        if eligible:
            best_gap = min(float(row["project_gap"]) for row in eligible)
            instance = min(row["instance"] for row in eligible
                           if float(row["project_gap"]) == best_gap)
            if instance not in selected: selected.append(instance)
    json_write(RESULTS / "stage5_selection.json", {
        "schema": "round22-stage5-preregistered-selection-v1",
        "selected_instances": selected,
        "rule": "V12 certificate-issue condition; then minimum complete-matrix project gap by suite, tie instance ID",
        "selected_at": now(),
    })
    return [RunSpec("stage5", instance, arm, 3600)
            for instance in selected for arm in ("S0", "S1", "plain")]


def acquire_lock() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        raise RuntimeError(f"runner lock exists: {LOCK}")
    LOCK.write_text(json.dumps({"pid": os.getpid(), "started_at": now()}) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("stage0", "stage1", "stage2", "stage3", "stage4", "stage5", "analyze", "all"), required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    acquire_lock()
    try:
        if args.stage == "stage0":
            run_stage0(); return
        if args.stage == "analyze":
            analyze(); return
        frozen = frozen_data()
        stages = ("stage1", "stage2", "stage3", "stage4", "stage5") if args.stage == "all" else (args.stage,)
        for stage in stages:
            specs = selected_stage5() if stage == "stage5" else stage_specs(stage)
            for spec in specs:
                run_one(spec, frozen, args.dry_run)
            if not args.dry_run: analyze()
    finally:
        if LOCK.exists(): LOCK.unlink()


if __name__ == "__main__":
    main()
