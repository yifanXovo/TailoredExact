#!/usr/bin/env python3
"""Run the frozen Round 24R experiment stages serially.

The runner deliberately keeps the Gurobi license setting process-local and
never reads the license file.  It records commands and sanitized process state,
but does not place the environment in a command line or output document.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_solver_backend_migration_round24r"
LICENSE = Path(r"E:\gurobi\gurobi.lic")
DEFAULT_EXE = ROOT / "build_round24r" / "with_gurobi_clean" / "ExactEBRP.exe"

INSTANCES = {
    "toy": ROOT / "tests" / "data" / "round24_toy_V2_M1.txt",
    "V12_M1": ROOT / "reference" / "regen_candidate_V12_M1_average.txt",
    "V12_M2": ROOT / "reference" / "regen_candidate_V12_M2_average.txt",
    "moderate4301": ROOT / "reference" / "heldout_round22" / "V20_M3" / "moderate_seed4301.txt",
    "high_imbalance_seed3202": ROOT / "reference" / "hard_stress" / "V20_M3" / "high_imbalance_seed3202.txt",
    "tight_T_seed3101": ROOT / "reference" / "hard_stress" / "V20_M3" / "tight_T_seed3101.txt",
}

STAGES = {
    "stage1a": (120, [
        ("moderate4301", arm) for arm in (
            "S0-SAFE", "T-CPX-ST-PON-DIAG", "T-CPX-EXT-PON",
            "P-GRB", "T-GRB-EXT-COLD", "T-GRB-EXT-WARM")]),
    "stage1b": (120, [
        ("V12_M2", arm) for arm in (
            "T-GRB-EXT-FRESH-COLD", "T-GRB-EXT-COLD",
            "T-GRB-EXT-WARM")]),
    "stage1c": (180, [
        (instance, arm)
        for instance in ("V12_M1", "V12_M2")
        for arm in ("S0-SAFE", "T-CPX-EXT-POFF",
                    "T-CPX-ST-PON-DIAG", "T-CPX-EXT-PON")]),
    "stage2": (300, [
        (instance, arm)
        for instance in ("V12_M1", "V12_M2",
                         "high_imbalance_seed3202", "tight_T_seed3101")
        for arm in ("P-CPX", "P-GRB", "S0-SAFE",
                    "T-CPX-ST-PON-DIAG", "T-CPX-EXT-PON",
                    "T-GRB-EXT-COLD", "T-GRB-EXT-WARM")]),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add(args: list[str], name: str, value: object) -> None:
    args.extend((name, str(value).lower() if isinstance(value, bool) else str(value)))


def tailored_base(run_dir: Path, budget: int) -> list[str]:
    native_budget = max(0.001, budget * 0.98)
    args: list[str] = []
    for name, value in (
        ("--method", "gcap-frontier"),
        ("--algorithm-preset", "paper-gf-tailored-bc"),
        ("--lambda", 0.15), ("--T", 3600),
        ("--time-limit", native_budget),
        ("--process-wall-time-limit", budget),
        ("--threads", 1), ("--mip-threads", 1),
        ("--cplex-threads", 1), ("--compact-bc-threads", 1),
        ("--primal-heuristic", "hga-tgbc"),
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
    ):
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


def load_fingerprints() -> dict[str, int]:
    path = OUT / "gurobi_fingerprints.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): int(v) for k, v in data.get("fingerprints", {}).items()}


def production_binding_args(executable_sha: str, arm: str,
                            run_dir: Path) -> list[str]:
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip().lower()
    protocol_sha = sha256(OUT / "corrected_evaluation_protocol.md")
    args: list[str] = []
    for name, item in (
        ("--round22-production-mode", True),
        ("--round22-source-commit", source_commit),
        ("--round22-executable-sha256", executable_sha),
        ("--round22-production-manifest-sha256", protocol_sha),
        ("--dense-progress", True),
        ("--dense-progress-run-id", run_dir.name),
        ("--dense-progress-algorithm-arm", arm),
        ("--dense-progress-raw", run_dir / "dense_progress.csv"),
        ("--dense-progress-checkpoints", run_dir / "bound_checkpoints.csv"),
    ):
        add(args, name, item)
    return args


def make_command(exe: Path, stage: str, instance: str, arm: str,
                 budget: int, run_dir: Path, executable_sha: str) -> list[str]:
    result_path = run_dir / "result.json"
    native_log = run_dir / "native.log"
    model_path = run_dir / "canonical.lp"
    args: list[str] = [str(exe), "--input", str(INSTANCES[instance])]
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
            args.extend(production_binding_args(executable_sha, arm, run_dir))
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
        args.extend(production_binding_args(executable_sha, arm, run_dir))
        if arm in ("S0-SAFE", "T-CPX-ST-PON-DIAG"):
            add(args, "--frontier-execution-mode", "global-gini-tree")
            add(args, "--global-gini-tree-presolve",
                "off" if arm == "S0-SAFE" else "on")
            if arm == "T-CPX-ST-PON-DIAG":
                add(args, "--round24-research-mode", True)
                add(args, "--allow-unsafe-continuous-branch-presolve-diagnostic", True)
        else:
            add(args, "--frontier-execution-mode", "external-gini-tree")
            add(args, "--external-gini-artifact-dir", run_dir / "external")
            backend = "cplex" if arm.startswith("T-CPX") else "gurobi"
            add(args, "--external-gini-backend", backend)
            add(args, "--global-gini-tree-presolve",
                "on" if arm == "T-CPX-EXT-PON" else "off")
            lifecycle = "fresh-per-attempt" if arm == "T-GRB-EXT-FRESH-COLD" else "retained-per-leaf"
            add(args, "--external-gini-lifecycle", lifecycle)
            add(args, "--external-gini-warm-start", arm == "T-GRB-EXT-WARM")
            if backend == "gurobi":
                add(args, "--gurobi-home", "D:/gurobi1302/win64")
                add(args, "--gurobi-seed", 0)
                add(args, "--gurobi-presolve", -1)
        add(args, "--log", native_log)
    add(args, "--out", result_path)
    return args


def run_one(exe: Path, stage: str, instance: str, arm: str,
            budget: int, force: bool) -> dict[str, object]:
    run_id = f"{stage}__{instance}__{arm.lower().replace('-', '_')}__{budget}s"
    run_dir = OUT / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    state_path = run_dir / "run_state.json"
    result_path = run_dir / "result.json"
    if not force and state_path.exists() and result_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state.get("completed"):
            print(f"SKIP {run_id}", flush=True)
            return state
    executable_sha = sha256(exe)
    command = make_command(
        exe, stage, instance, arm, budget, run_dir, executable_sha)
    record = {
        "schema": "round24r-command-v1", "run_id": run_id,
        "stage": stage, "instance": instance, "arm": arm,
        "budget_seconds": budget, "command": command,
        "executable_sha256": executable_sha,
        "instance_sha256": sha256(INSTANCES[instance]),
        "gurobi_license_environment": "process_local_authorized_path",
        "started_unix": time.time(), "completed": False,
    }
    (run_dir / "command.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8")
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
                timeout=budget + 45, check=False)
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
        "completed": True,
    })
    state_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"DONE {run_id} rc={return_code} wall={record['runner_wall_seconds']:.3f}", flush=True)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=sorted(STAGES), required=True)
    parser.add_argument("--exe", type=Path, default=DEFAULT_EXE)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    exe = args.exe.resolve()
    if not exe.is_file():
        raise SystemExit(f"missing executable: {exe}")
    if not LICENSE.is_file():
        raise SystemExit("authorized Gurobi license path is unavailable")
    budget, matrix = STAGES[args.stage]
    failures = 0
    for instance, arm in matrix:
        state = run_one(exe, args.stage, instance, arm, budget, args.force)
        if int(state.get("return_code", 1)) != 0 or not state.get("result_exists"):
            failures += 1
    print(f"STAGE {args.stage} complete runs={len(matrix)} process_failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
