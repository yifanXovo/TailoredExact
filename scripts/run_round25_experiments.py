#!/usr/bin/env python3
"""Frozen serial runner for Round 25 backend validation.

The authorized Gurobi license is exposed only in each child process environment.
The runner never opens the license file and never serializes the environment.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_solver_backend_validation_round25"
LICENSE = Path(r"E:\gurobi\gurobi.lic")
DEFAULT_EXE = ROOT / "build_round25" / "with_gurobi" / "ExactEBRP.exe"
DEFAULT_CPLEX_EXE = ROOT / "build_round25" / "no_gurobi" / "ExactEBRP.exe"
PROTOCOL = OUT / "round25_evaluation_protocol.md"
LOCK = OUT / ".round25_runner.lock"
COMPRESSION_THRESHOLD = 4 * 1024 * 1024

INSTANCES: dict[str, tuple[Path, str]] = {
    "V12_M1": (ROOT / "reference" / "regen_candidate_V12_M1_average.txt", "v12"),
    "V12_M2": (ROOT / "reference" / "regen_candidate_V12_M2_average.txt", "v12"),
    "high_imbalance_seed3202": (
        ROOT / "reference" / "hard_stress" / "V20_M3" /
        "high_imbalance_seed3202.txt", "high_imbalance"),
    "high_imbalance_seed4201": (
        ROOT / "reference" / "heldout_round22" / "V20_M3" /
        "high_imbalance_seed4201.txt", "high_imbalance"),
    "moderate_seed3302": (
        ROOT / "reference" / "hard_stress" / "V20_M3" /
        "moderate_seed3302.txt", "moderate"),
    "moderate_seed4302": (
        ROOT / "reference" / "heldout_round22" / "V20_M3" /
        "moderate_seed4302.txt", "moderate"),
    "tight_T_seed3101": (
        ROOT / "reference" / "hard_stress" / "V20_M3" /
        "tight_T_seed3101.txt", "tight_T"),
    "tight_T_seed4101": (
        ROOT / "reference" / "heldout_round22" / "V20_M3" /
        "tight_T_seed4101.txt", "tight_T"),
    "moderate_seed4301": (
        ROOT / "reference" / "heldout_round22" / "V20_M3" /
        "moderate_seed4301.txt", "correctness_sentinel"),
    "toy": (ROOT / "tests" / "data" / "round24_toy_V2_M1.txt", "mechanical"),
}

STAGE1_INSTANCES = (
    "V12_M1", "V12_M2", "high_imbalance_seed3202",
    "high_imbalance_seed4201", "moderate_seed3302", "moderate_seed4302",
    "tight_T_seed3101", "tight_T_seed4101",
)
STAGE2_INSTANCES = (
    "high_imbalance_seed3202", "high_imbalance_seed4201",
    "moderate_seed4302", "tight_T_seed3101",
)
ARMS = (
    "P-CPX", "P-GRB", "S0-SAFE", "EXT-CPX",
    "EXT-GRB-COLD", "EXT-GRB-WARM",
)
ARM_MANIFESTS = {
    "P-CPX": "p_cpx_manifest.json",
    "P-GRB": "p_grb_manifest.json",
    "S0-SAFE": "s0_safe_manifest.json",
    "EXT-CPX": "ext_cpx_manifest.json",
    "EXT-GRB-COLD": "ext_grb_cold_manifest.json",
    "EXT-GRB-WARM": "ext_grb_warm_manifest.json",
}
STAGES = {
    "sentinel": (120, [("moderate_seed4301", arm) for arm in
                        ("S0-SAFE", "EXT-CPX", "EXT-GRB-COLD")]),
    "stage1": (900, [(instance, arm) for instance in STAGE1_INSTANCES
                      for arm in ARMS]),
    "stage2": (1200, [(instance, arm) for instance in STAGE2_INSTANCES
                       for arm in ARMS]),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def json_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def csv_write(path: Path, rows: Iterable[dict[str, Any]], fields: list[str]) -> None:
    material = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(material)
    os.replace(temporary, path)


def add(args: list[str], name: str, value: object) -> None:
    args.extend((name, str(value).lower() if isinstance(value, bool) else str(value)))


def tailored_base(run_dir: Path, budget: int) -> list[str]:
    native_budget = max(0.001, budget * 0.98)
    args: list[str] = []
    options: tuple[tuple[str, object], ...] = (
        ("--method", "gcap-frontier"),
        ("--algorithm-preset", "paper-gf-tailored-bc"),
        ("--lambda", 0.15), ("--T", 3600),
        ("--time-limit", native_budget),
        ("--process-wall-time-limit", budget),
        ("--threads", 1), ("--mip-threads", 1),
        ("--cplex-threads", 1), ("--compact-bc-threads", 1),
        ("--primal-heuristic", "hga-tgbc"),
        ("--primal-heuristic-seconds", 10),
        ("--primal-heuristic-seed", 20260626),
        ("--frontier-intervals", 4),
        ("--frontier-adaptive-split", True),
        ("--frontier-adaptive-max-depth", 8),
        ("--frontier-adaptive-min-width", 0.0001),
        ("--frontier-adaptive-split-factor", 2),
        ("--tailored-bc-enabled", True),
        ("--tailored-bc-mode", "static"),
        ("--tailored-bc-callback-cut-profile", "off"),
        ("--compact-bc-root-cut-rounds", 0),
        ("--compact-bc-dynamic-cut-families", "none"),
        ("--compact-bc-cut-profile", "balanced"),
        ("--compact-bc-low-gini-strengthening", "safe"),
        ("--compact-bc-denominator-bound-mode", "tight"),
        ("--compact-bc-objective-estimator-mode", "adaptive"),
        ("--compact-bc-domain-propagation-mode", "iterative"),
        ("--compact-bc-domain-propagation-rounds", 2),
        ("--compact-bc-variable-s-centering", True),
        ("--compact-bc-sp-product-estimator", "paper-safe"),
        ("--compact-bc-sp-product-bounds", "tight"),
        ("--compact-bc-s-range-refinement", "off"),
        ("--tailored-bc-branching-priority", "off"),
        ("--tailored-bc-gini-branching", "off"),
        ("--tailored-bc-gini-subset-envelope", False),
        ("--tailored-bc-low-gini-l1-centering", False),
        ("--tailored-bc-local-centering", False),
        ("--tailored-bc-subset-cross-h-centering", False),
        ("--tailored-bc-local-q-centering", False),
        ("--tailored-bc-subset-inventory-imbalance", False),
        ("--tailored-bc-transfer-cutset", False),
        ("--tailored-bc-gs-product-coupling", False),
        ("--tailored-bc-disaggregated-sp-estimator", False),
        ("--tailored-bc-bucket-ratio-domain-tightening", False),
        ("--tailored-bc-bucket-subset-ratio-domain", False),
        ("--tailored-bc-bucket-integer-inventory-domain", False),
        ("--tailored-bc-bucket-required-movement", False),
        ("--tailored-bc-bucket-required-visit", False),
        ("--tailored-bc-s-bucket-ledger", "off"),
        ("--global-gini-tree-search", "traditional"),
        ("--global-gini-tree-child-estimate", "parent-copy"),
        ("--global-gini-tree-row-attachment", "full-inherited-pack"),
        ("--global-gini-tree-row-timing", "deferred"),
        ("--global-gini-tree-native-mip-start", False),
        ("--global-gini-tree-root-connectivity-flow", True),
        ("--global-gini-tree-root-connectivity-flow-variant", "round20-current"),
        ("--progress-log", run_dir / "progress.csv"),
        ("--progress-interval-seconds", 5),
    )
    for name, value in options:
        add(args, name, value)
    return args


def trace_args(run_dir: Path) -> list[str]:
    args: list[str] = []
    for name, filename in (
        ("--global-gini-tree-node-trace", "global_node_trace.csv"),
        ("--global-gini-tree-bound-trace", "global_bound_trajectory.csv"),
        ("--global-gini-tree-manifest", "model_lifecycle_manifest.csv"),
        ("--global-gini-tree-root-export", "global_root.lp"),
        ("--global-gini-tree-post-row-trace", "post_rows.csv"),
        ("--global-gini-tree-topology-trace", "gini_topology.csv"),
        ("--global-gini-tree-sibling-trace", "sibling_delay.csv"),
        ("--global-gini-tree-row-delta-trace", "row_delta.csv"),
        ("--global-gini-tree-memory-trace", "tree_memory.csv"),
        ("--global-gini-tree-mip-start-audit", "mip_start_audit.csv"),
    ):
        add(args, name, run_dir / filename)
    return args


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_fingerprints() -> dict[str, int]:
    path = OUT / "gurobi_fingerprints.json"
    if not path.exists():
        return {}
    return {str(k): int(v) for k, v in
            load_json(path).get("fingerprints", {}).items()}


def arm_manifest(arm: str) -> dict[str, Any]:
    path = OUT / ARM_MANIFESTS[arm]
    if not path.is_file():
        raise RuntimeError(f"missing frozen arm manifest: {path}")
    return load_json(path)


def validate_frozen(exe: Path, arm: str, instance: str) -> dict[str, Any]:
    manifest = arm_manifest(arm)
    if sha256(exe) != manifest.get("executable_sha256"):
        raise RuntimeError(f"frozen executable mismatch for {arm}")
    if sha256(PROTOCOL) != manifest.get("protocol_sha256"):
        raise RuntimeError(f"frozen protocol mismatch for {arm}")
    instance_rows = list(csv.DictReader(
        (OUT / "round25_instance_manifest.csv").open(
            newline="", encoding="utf-8")))
    matches = [row for row in instance_rows if row["instance"] == instance]
    if len(matches) != 1 or sha256(INSTANCES[instance][0]) != matches[0]["sha256"]:
        raise RuntimeError(f"instance manifest mismatch for {instance}")
    return manifest


def production_binding_args(executable_sha: str, source_commit: str,
                            arm: str, run_dir: Path) -> list[str]:
    args: list[str] = []
    for name, item in (
        ("--round22-production-mode", True),
        ("--round22-source-commit", source_commit),
        ("--round22-executable-sha256", executable_sha),
        ("--round22-production-manifest-sha256", sha256(PROTOCOL)),
        ("--dense-progress", True),
        ("--dense-progress-run-id", run_dir.name),
        ("--dense-progress-algorithm-arm", arm),
        ("--dense-progress-raw", run_dir / "dense_progress.csv"),
        ("--dense-progress-checkpoints", run_dir / "bound_checkpoints.csv"),
    ):
        add(args, name, item)
    return args


def make_command(exe: Path, instance: str, arm: str, budget: int,
                 run_dir: Path, manifest: dict[str, Any]) -> list[str]:
    result_path = run_dir / "result.json"
    native_log = run_dir / "native.log"
    model_path = run_dir / "canonical.lp"
    executable_sha = str(manifest["executable_sha256"])
    source_commit = str(manifest["source_commit"])
    args: list[str] = [str(exe), "--input", str(INSTANCES[instance][0])]
    if arm in ("P-CPX", "P-GRB"):
        method = "cplex" if arm == "P-CPX" else "gurobi"
        for name, value in (
            ("--method", method), ("--lambda", 0.15), ("--T", 3600),
            ("--time-limit", budget * 0.98),
            ("--process-wall-time-limit", budget),
            ("--threads", 1), ("--mip-threads", 1),
            ("--cplex-threads", 1), ("--compact-bc-threads", 1),
            ("--log", native_log),
        ):
            add(args, name, value)
        args.append("--plain-baseline")
        if arm == "P-CPX":
            add(args, "--cplex-model-export", model_path)
            add(args, "--progress-log", run_dir / "progress.csv")
            args.extend(production_binding_args(
                executable_sha, source_commit, arm, run_dir))
        else:
            for name, value in (
                ("--gurobi-home", "D:/gurobi1302/win64"),
                ("--gurobi-seed", 0), ("--gurobi-presolve", -1),
                ("--gurobi-model-export", model_path),
                ("--gurobi-progress", run_dir / "progress.csv"),
                ("--round24-executable-sha256", executable_sha),
                ("--round24-manifest-executable-sha256", executable_sha),
                ("--round24-expected-gurobi-model-fingerprint",
                 load_fingerprints().get(instance, 0)),
            ):
                add(args, name, value)
    else:
        args.extend(tailored_base(run_dir, budget))
        args.extend(trace_args(run_dir))
        args.extend(production_binding_args(
            executable_sha, source_commit, arm, run_dir))
        if arm == "S0-SAFE":
            add(args, "--frontier-execution-mode", "global-gini-tree")
            add(args, "--global-gini-tree-presolve", "off")
        else:
            add(args, "--frontier-execution-mode", "external-gini-tree")
            add(args, "--external-gini-artifact-dir", run_dir / "external")
            backend = "cplex" if arm == "EXT-CPX" else "gurobi"
            add(args, "--external-gini-backend", backend)
            add(args, "--global-gini-tree-presolve",
                "on" if backend == "cplex" else "off")
            add(args, "--external-gini-lifecycle", "retained-per-leaf")
            add(args, "--external-gini-warm-start", arm == "EXT-GRB-WARM")
            if backend == "gurobi":
                add(args, "--gurobi-home", "D:/gurobi1302/win64")
                add(args, "--gurobi-seed", 0)
                add(args, "--gurobi-presolve", -1)
        add(args, "--log", native_log)
    add(args, "--out", result_path)
    return args


def sensitive_marker_present(directory: Path) -> bool:
    markers = (b"LicenseID", b"WLSAccessID", b"WLSSecret", b"TokenServer",
               b"Set parameter Username", b"Computer ID", b"HOSTID")
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in (".log", ".txt", ".json"):
            data = path.read_bytes()
            if any(marker in data for marker in markers):
                return True
    return False


def compress_large_files(
        directory: Path, min_bytes: int = COMPRESSION_THRESHOLD,
        suffixes: tuple[str, ...] = (".csv", ".log", ".lp"),
        manifest_name: str = "compression_manifest.csv") -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(directory.rglob("*")):
        if (not path.is_file() or path.stat().st_size < min_bytes or
                path.suffix.lower() not in suffixes):
            continue
        target = Path(str(path) + ".gz")
        original_sha = sha256(path)
        original_bytes = path.stat().st_size
        with path.open("rb") as source, target.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw,
                               compresslevel=9, mtime=0) as sink:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    sink.write(block)
        digest = hashlib.sha256()
        restored_bytes = 0
        with gzip.open(target, "rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
                restored_bytes += len(block)
        if digest.hexdigest() != original_sha or restored_bytes != original_bytes:
            target.unlink(missing_ok=True)
            raise RuntimeError(f"deterministic compression verification failed: {path}")
        path.unlink()
        records.append({
            "original_path": relative(path),
            "compressed_path": relative(target),
            "original_bytes": original_bytes,
            "compressed_bytes": target.stat().st_size,
            "original_sha256": original_sha,
            "compressed_sha256": sha256(target),
            "compression": "gzip_level9_mtime0_filename_omitted",
        })
    if records:
        csv_write(directory / manifest_name, records,
                  list(records[0]))
    return records


def run_one(exe: Path, stage: str, instance: str, arm: str, budget: int,
            diagnostic_trigger: dict[str, Any] | None = None) -> dict[str, Any]:
    slug = arm.lower().replace("-", "_")
    run_id = f"{stage}__{instance}__{slug}__{budget}s"
    run_dir = OUT / "runs" / run_id
    state_path = run_dir / "run_state.json"
    result_path = run_dir / "result.json"
    if state_path.exists():
        state = load_json(state_path)
        if state.get("completed"):
            print(f"SKIP {run_id}", flush=True)
            return state
        raise RuntimeError(f"incomplete existing run requires exclusion audit: {run_id}")
    run_dir.mkdir(parents=True, exist_ok=False)
    manifest = validate_frozen(exe, arm, instance)
    command = make_command(exe, instance, arm, budget, run_dir, manifest)
    record: dict[str, Any] = {
        "schema": "round25-command-v1", "run_id": run_id,
        "stage": stage, "instance": instance, "arm": arm,
        "budget_seconds": budget, "command": command,
        "executable_sha256": sha256(exe),
        "instance_sha256": sha256(INSTANCES[instance][0]),
        "protocol_sha256": sha256(PROTOCOL),
        "arm_manifest": ARM_MANIFESTS[arm],
        "arm_manifest_sha256": sha256(OUT / ARM_MANIFESTS[arm]),
        "instance_manifest_sha256": sha256(OUT / "round25_instance_manifest.csv"),
        "common_ub_manifest_sha256": sha256(OUT / "round25_common_ub_manifest.csv"),
        "gurobi_license_environment": "process_local_authorized_path",
        "official": stage in ("stage1", "stage2"),
        "diagnostic_only": stage == "diagnostic",
        "diagnostic_trigger": diagnostic_trigger or {},
        "started_unix": time.time(), "completed": False,
    }
    json_write(run_dir / "command.json", record)
    env = os.environ.copy()
    env["GRB_LICENSE_FILE"] = str(LICENSE)
    print(f"RUN {run_id}", flush=True)
    started = time.monotonic()
    emergency_timeout = False
    with (run_dir / "console.stdout.log").open("wb") as stdout, \
         (run_dir / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                timeout=budget + 90, check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            emergency_timeout = True
            return_code = 124
    record.update({
        "finished_unix": time.time(),
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code,
        "emergency_timeout": emergency_timeout,
        "result_exists": result_path.exists(),
        "sensitive_marker_scan_passed": not sensitive_marker_present(run_dir),
        "completed": True,
    })
    if not record["sensitive_marker_scan_passed"]:
        raise RuntimeError(f"sensitive marker detected in {run_id}; publication blocked")
    record["compressed_artifacts"] = compress_large_files(run_dir)
    json_write(state_path, record)
    print(f"DONE {run_id} rc={return_code} "
          f"wall={record['runner_wall_seconds']:.3f}", flush=True)
    return record


def configuration(arm: str) -> dict[str, Any]:
    common = {
        "uniform_all_instances": True,
        "threads": 1, "lambda": 0.15, "T": 3600,
        "relative_mip_gap": 0.0, "absolute_mip_gap": 0.0,
        "process_wall_includes_all_phases": True,
        "instance_or_family_dispatch": False,
    }
    if arm == "P-CPX":
        return common | {
            "method": "plain_cplex", "canonical_original_compact_milp": True,
            "native_defaults": "presolve_cuts_heuristics_branching",
            "hga_or_known_ub": False,
        }
    if arm == "P-GRB":
        return common | {
            "method": "plain_gurobi", "canonical_original_compact_milp": True,
            "presolve": "automatic", "seed": 0, "hga_or_known_ub": False,
        }
    tailored = common | {
        "same_run_verified_hga": True, "hga_seed": 20260626,
        "hga_seconds": 10, "initial_intervals": 4,
        "adaptive_max_depth": 8, "adaptive_min_width": 0.0001,
        "adaptive_split_factor": 2, "child_estimate": "parent-copy",
        "row_factory": "round18_static_F0", "P1_P2_F3": "off",
        "native_mip_start": False,
    }
    if arm == "S0-SAFE":
        return tailored | {
            "method": "persistent_cplex_global_gini_tree",
            "presolve": "off", "reduce": 0, "linear": 0,
            "native_tree_count": 1,
        }
    base = tailored | {
        "method": "external_solver_neutral_gini_tree",
        "lifecycle": "retained-per-leaf",
        "immutable_artifact_cache": True,
        "non_strict_verified_cutoff": True,
    }
    if arm == "EXT-CPX":
        return base | {"backend": "cplex", "presolve": "on"}
    return base | {
        "backend": "gurobi", "presolve": "automatic", "seed": 0,
        "explicit_cross_model_warm_start": arm == "EXT-GRB-WARM",
    }


def prepare_manifests(exe: Path, cplex_exe: Path) -> None:
    if not exe.is_file() or not cplex_exe.is_file() or not PROTOCOL.is_file():
        raise RuntimeError("built executables and protocol are required")
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip().lower()
    instance_rows = []
    for instance in (*STAGE1_INSTANCES, "moderate_seed4301", "toy"):
        path, family = INSTANCES[instance]
        if not path.is_file():
            raise RuntimeError(f"missing frozen instance {path}")
        instance_rows.append({
            "instance": instance, "family": family,
            "path": relative(path), "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "stage1_900s": instance in STAGE1_INSTANCES,
            "stage2_1200s": instance in STAGE2_INSTANCES,
            "sentinel_120s": instance == "moderate_seed4301",
            "fixed_before_results": True,
        })
    csv_write(OUT / "round25_instance_manifest.csv", instance_rows,
              list(instance_rows[0]))
    common_rows = []
    for horizon, instances in ((900, STAGE1_INSTANCES),
                               (1200, STAGE2_INSTANCES)):
        for instance in instances:
            common_rows.append({
                "horizon_seconds": horizon, "instance": instance,
                "numeric_common_ub": "postrun_from_official_rows",
                "frozen_rule":
                    "minimum_independently_verified_UB_among_same_horizon_official_rows",
                "solver_use": "reporting_only_never_passed_to_any_solver",
                "different_ub_warning":
                    "native_objective_native_bound_verified_ub_and_common_ub_remain_separate",
            })
    csv_write(OUT / "round25_common_ub_manifest.csv", common_rows,
              list(common_rows[0]))
    unified_sha = sha256(exe)
    cplex_sha = sha256(cplex_exe)
    protocol_sha = sha256(PROTOCOL)
    json_write(OUT / "round25_build_manifest.json", {
        "schema": "round25-build-manifest-v1",
        "source_commit": source_commit,
        "unified_gurobi_enabled_executable": relative(exe),
        "unified_gurobi_enabled_sha256": unified_sha,
        "cplex_only_executable": relative(cplex_exe),
        "cplex_only_sha256": cplex_sha,
        "protocol_sha256": protocol_sha,
    })
    for arm, filename in ARM_MANIFESTS.items():
        json_write(OUT / filename, {
            "schema": "round25-frozen-arm-v1", "arm": arm,
            "source_commit": source_commit,
            "protocol_sha256": protocol_sha,
            "executable_path": relative(exe),
            "executable_sha256": unified_sha,
            "cplex_only_qualification_sha256": cplex_sha,
            "configuration": configuration(arm),
        })
    print("Round25 manifests prepared", flush=True)


def diagnostic_matrix() -> list[tuple[str, str, dict[str, Any]]]:
    path = OUT / "underperformance_trigger_table.csv"
    if not path.is_file():
        raise RuntimeError("underperformance trigger table is missing")
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    triggered = [row for row in rows if row.get("triggered", "").lower() == "true"]
    matrix: list[tuple[str, str, dict[str, Any]]] = []
    seen: set[tuple[str, str]] = set()
    for row in triggered:
        key = (row["instance"], row["replay_arm"])
        if key in seen:
            raise RuntimeError(f"duplicate diagnostic trigger {key}")
        seen.add(key)
        matrix.append((key[0], key[1], row))
    return matrix


def acquire_lock() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError(f"Round25 runner lock exists: {LOCK}") from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(f"pid={os.getpid()}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=(*STAGES, "diagnostic"))
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--prepare-manifests", action="store_true")
    parser.add_argument("--cplex-only-exe", type=Path, default=DEFAULT_CPLEX_EXE)
    args = parser.parse_args()
    exe = args.exe.resolve()
    if args.prepare_manifests:
        prepare_manifests(exe, args.cplex_only_exe.resolve())
        return 0
    if not args.stage:
        parser.error("--stage is required unless --prepare-manifests is used")
    if not exe.is_file() or not LICENSE.is_file():
        raise SystemExit("frozen executable or authorized license path is unavailable")
    acquire_lock()
    failures = 0
    try:
        if args.stage == "diagnostic":
            matrix = diagnostic_matrix()
            budget = 300
            for instance, arm, trigger in matrix:
                state = run_one(exe, "diagnostic", instance, arm, budget, trigger)
                if int(state.get("return_code", 1)) != 0 or not state.get("result_exists"):
                    failures += 1
        else:
            budget, matrix = STAGES[args.stage]
            for instance, arm in matrix:
                state = run_one(exe, args.stage, instance, arm, budget)
                if int(state.get("return_code", 1)) != 0 or not state.get("result_exists"):
                    failures += 1
        print(f"STAGE {args.stage} complete process_failures={failures}", flush=True)
        return 1 if failures else 0
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
