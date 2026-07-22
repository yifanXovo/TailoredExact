#!/usr/bin/env python3
"""Frozen serial runner for the Round 28 C3 migration qualification.

The Gurobi license path is injected only into licensed child environments.
This module never reads, hashes, prints, copies, or serializes that file.
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
OUT = ROOT / "results/gf_cplex_equivalent_gurobi_replica_round28"
RUNS = OUT / "runs"
PROTOCOL = OUT / "round28_protocol.md"
INSTANCE_MANIFEST = OUT / "all_authoritative_instances_manifest.csv"
C3_MANIFEST = OUT / "c3_replica_manifest.json"
LICENSE = Path(r"E:\gurobi\gurobi.lic")
S0_EXE = ROOT / "build_round28/cplex_only/ExactEBRP.exe"
C2_EXE = ROOT / "build_round27/with_gurobi/ExactEBRP.exe"
P_EXE = C2_EXE
C3_EXE = ROOT / "build_round28/with_gurobi/ExactEBRP.exe"
LOCK = OUT / ".round28_runner.lock"
OFFICIAL_BUDGET = 300
NO_IMPROVE_GENERATIONS = 2000
COMPRESSION_THRESHOLD = 512 * 1024


INSTANCES: dict[str, tuple[str, str, int, int, str]] = {
    "V12_M1": ("reference/regen_candidate_V12_M1_average.txt", "v12", 12, 1,
        "e395cfef336d3407a65f04d7e201aa29ac844a08aff25d1991ce6983e5e9508d"),
    "V12_M2": ("reference/regen_candidate_V12_M2_average.txt", "v12", 12, 2,
        "0bb0416cc9540fffbb91299d5c9ed3d6c2363906424005b1c40b4e3829ddf4f0"),
    "high_imbalance_seed3202": ("reference/hard_stress/V20_M3/high_imbalance_seed3202.txt", "high_imbalance", 20, 3,
        "902f4c46fa076f3e24b537737c5d58ffe833e6de21e900a42bb8846d3f76db50"),
    "moderate_seed3302": ("reference/hard_stress/V20_M3/moderate_seed3302.txt", "moderate", 20, 3,
        "0b329df7711155131b33dfd14cfee8e85a17f60cc003863dbe004eb085c5f77e"),
    "tight_T_seed3101": ("reference/hard_stress/V20_M3/tight_T_seed3101.txt", "tight_T", 20, 3,
        "30aea92f1d6ce551ef8fffe15acdd3422a94b06e60ddd13ad5166149653d4ef3"),
    "high_imbalance_seed4201": ("reference/heldout_round22/V20_M3/high_imbalance_seed4201.txt", "high_imbalance", 20, 3,
        "79d27b2247247c7f86a20e4fd5a123ab1b5e41dfd193f3bdb4b88297f243f368"),
    "moderate_seed4302": ("reference/heldout_round22/V20_M3/moderate_seed4302.txt", "moderate", 20, 3,
        "ce1aaed9987b1d34c665df323f602ca36223eab6da3bffd73c0ead4f78d936a7"),
    "tight_T_seed4101": ("reference/heldout_round22/V20_M3/tight_T_seed4101.txt", "tight_T", 20, 3,
        "57efa512535d9914d51bfa1a16ccfbe602bd5c04080698bc7a7de611bcc54a3d"),
    "high_imbalance_seed5202": ("reference/heldout_round26/V20_M3/high_imbalance_seed5202.txt", "high_imbalance", 20, 3,
        "18df273a1bb599a8d85ba695f107711331ffc1ff101eb67d3603cf28ce0510fb"),
    "high_imbalance_seed5203": ("reference/heldout_round26/V20_M3/high_imbalance_seed5203.txt", "high_imbalance", 20, 3,
        "261a4e276df0a95d5ade89f6067b3451fa74650a70970cfa27248c4884f29761"),
    "moderate_seed5301": ("reference/heldout_round26/V20_M3/moderate_seed5301.txt", "moderate", 20, 3,
        "7d1b9e36dec1a5389d2d76af66c9476e642fac496530154bd4418e2082e5d0a5"),
    "moderate_seed5302": ("reference/heldout_round26/V20_M3/moderate_seed5302.txt", "moderate", 20, 3,
        "29d6c063e60366697a215808677ac53e958cb916103382f91a3b92957bd9dc3f"),
    "tight_T_seed5102": ("reference/heldout_round26/V20_M3/tight_T_seed5102.txt", "tight_T", 20, 3,
        "7c6d264827a64fc1da476a350f4312c947f27c94ba1b7cf775347fdd407363d5"),
    "tight_T_seed5103": ("reference/heldout_round26/V20_M3/tight_T_seed5103.txt", "tight_T", 20, 3,
        "96043ed4a57c0596cd1acf7d7028a3b8c9edcbd7610e6d7a5772d55f75c5b528"),
    "high_imbalance_seed6202": ("reference/heldout_round26/V50_M3/high_imbalance_seed6202.txt", "high_imbalance", 50, 3,
        "dc638980e691c1e5a0db8863194d2c961c9548923de05ea66613c11a7b8542ba"),
    "moderate_seed6301": ("reference/heldout_round26/V50_M3/moderate_seed6301.txt", "moderate", 50, 3,
        "d07c4fc1d6f4c54b1964d7d1c925dd12b780f1973f5b61f1e02c1cfa35404ae3"),
    "tight_T_seed6102": ("reference/heldout_round26/V50_M3/tight_T_seed6102.txt", "tight_T", 50, 3,
        "62ed13533967116ca5cb0f3d3e8c4b984900b8aa11306aa6bb20a1aa6584e16c"),
    "moderate_seed4301": ("reference/heldout_round22/V20_M3/moderate_seed4301.txt", "correctness_sentinel", 20, 3,
        "8841820f8028da45d98c7d4ebebdb182df03f4a3909b877e4d3ce2bcd131daf6"),
    "toy": ("tests/data/round24_toy_V2_M1.txt", "mechanical", 2, 1,
        "297623332fb58e7f62a7c86e976c8e875ec2cea59b9169d6bb29328c15cdb141"),
}

PRIMARY = tuple(name for name in INSTANCES
                if name not in ("moderate_seed4301", "toy"))
ANCHORS = ("V12_M1", "V12_M2", "high_imbalance_seed3202",
           "moderate_seed3302", "tight_T_seed3101")
STAGE1_INSTANCES = ("toy", "V12_M1", "V12_M2",
                    "high_imbalance_seed3202", "moderate_seed4301")
STAGE4_INSTANCES = ("V12_M2", "moderate_seed3302", "moderate_seed6301")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    os.replace(temporary, path)


def csv_write(path: Path, rows: Iterable[dict[str, Any]],
              fields: list[str]) -> None:
    material = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(material)
    os.replace(temporary, path)


def add(args: list[str], name: str, value: object) -> None:
    args.extend((name, str(value).lower() if isinstance(value, bool)
                 else str(value)))


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def instance_path(instance: str) -> Path:
    return ROOT / INSTANCES[instance][0]


def verify_instance(instance: str) -> None:
    path = instance_path(instance)
    expected = INSTANCES[instance][4]
    if not path.is_file() or sha256(path) != expected:
        raise RuntimeError(f"authoritative instance mismatch: {instance}")
    if instance != "toy" and INSTANCE_MANIFEST.is_file():
        with INSTANCE_MANIFEST.open(newline="", encoding="utf-8") as stream:
            rows = {row["instance"]: row for row in csv.DictReader(stream)}
        row = rows.get(instance)
        if (row is None or row["sha256"] != expected or
                int(row["bytes"]) != path.stat().st_size or
                row["path"] != INSTANCES[instance][0]):
            raise RuntimeError(f"frozen Round 28 instance mismatch: {instance}")


def prepare_instance_manifest() -> None:
    rows: list[dict[str, Any]] = []
    for name, (path_text, family, vehicles, crews, expected) in INSTANCES.items():
        if name == "toy":
            continue
        path = ROOT / path_text
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"retained authoritative hash mismatch: {name}")
        authority = ("round26_v50_manifest.csv" if vehicles == 50 else
                     "round26_heldout_v20_manifest.csv" if "heldout_round26" in path_text else
                     "round25_instance_manifest.csv")
        rows.append({
            "instance": name, "family": family, "V": vehicles, "M": crews,
            "path": path_text, "bytes": path.stat().st_size,
            "sha256": expected, "retained_authority": authority,
            "primary_stage2": name in PRIMARY,
            "correctness_only": name == "moderate_seed4301",
            "frozen_before_official_results": True,
        })
    csv_write(INSTANCE_MANIFEST, rows, list(rows[0]))


def merged_fingerprints() -> dict[str, int]:
    values: dict[str, int] = {}
    for path in (
        ROOT / "results/gf_solver_backend_validation_round25/gurobi_fingerprints.json",
        ROOT / "results/gf_external_gurobi_production_validation_round26/gurobi_fingerprints.json",
    ):
        values.update({str(key): int(value) for key, value in
                       load_json(path).get("fingerprints", {}).items()})
    return values


def tailored_options(run_dir: Path, budget: int) -> list[str]:
    args: list[str] = []
    values: tuple[tuple[str, object], ...] = (
        ("--method", "gcap-frontier"),
        ("--algorithm-preset", "paper-gf-tailored-bc"),
        ("--lambda", 0.15), ("--T", 3600),
        ("--time-limit", budget * 0.98),
        ("--process-wall-time-limit", budget),
        ("--threads", 1), ("--mip-threads", 1),
        ("--cplex-threads", 1), ("--compact-bc-threads", 1),
        ("--primal-heuristic", "hga-tgbc"),
        ("--primal-heuristic-seed", 20260626),
        ("--primal-heuristic-stop", "generation-stagnation"),
        ("--primal-heuristic-no-improve-generations", 2000),
        ("--primal-heuristic-generation-log", run_dir / "hga_generations.csv"),
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
        ("--global-gini-tree-presolve", "off"),
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
    for name, value in values:
        add(args, name, value)
    return args


def production_binding(run_dir: Path, arm: str, exe: Path,
                       source_commit: str, manifest_sha: str) -> list[str]:
    args: list[str] = []
    for name, value in (
        ("--round22-production-mode", True),
        ("--round22-source-commit", source_commit),
        ("--round22-executable-sha256", sha256(exe)),
        ("--round22-production-manifest-sha256", manifest_sha),
        ("--dense-progress", True),
        ("--dense-progress-run-id", run_dir.name),
        ("--dense-progress-algorithm-arm", arm),
        ("--dense-progress-raw", run_dir / "dense_progress.csv"),
        ("--dense-progress-checkpoints", run_dir / "bound_checkpoints.csv"),
    ):
        add(args, name, value)
    return args


def plain_command(instance: str, budget: int, run_dir: Path) -> list[str]:
    args = [str(P_EXE), "--input", str(instance_path(instance))]
    for name, value in (
        ("--method", "gurobi"), ("--lambda", 0.15), ("--T", 3600),
        ("--time-limit", budget * 0.98),
        ("--process-wall-time-limit", budget),
        ("--threads", 1), ("--mip-threads", 1), ("--cplex-threads", 1),
        ("--compact-bc-threads", 1),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0), ("--gurobi-presolve", -1),
        ("--gurobi-model-export", run_dir / "canonical.lp"),
        ("--gurobi-progress", run_dir / "progress.csv"),
        ("--round24-executable-sha256", sha256(P_EXE)),
        ("--round24-manifest-executable-sha256", sha256(P_EXE)),
        ("--round24-expected-gurobi-model-fingerprint",
         merged_fingerprints().get(instance, 0)),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    args.append("--plain-baseline")
    return args


def s0_command(instance: str, budget: int, run_dir: Path) -> list[str]:
    manifest = load_json(C3_MANIFEST)
    args = [str(S0_EXE), "--input", str(instance_path(instance))]
    args.extend(tailored_options(run_dir, budget))
    # This is the frozen corrected S0 implementation and production binding.
    add(args, "--paper-run-sealed", True)
    for name, value in (
        ("--frontier-execution-mode", "global-gini-tree"),
        ("--global-gini-tree-node-trace", run_dir / "global_node_trace.csv"),
        ("--global-gini-tree-bound-trace", run_dir / "global_bound_trajectory.csv"),
        ("--global-gini-tree-manifest", run_dir / "model_lifecycle_manifest.csv"),
        ("--global-gini-tree-root-export", run_dir / "global_root.lp"),
        ("--global-gini-tree-post-row-trace", run_dir / "post_rows.csv"),
        ("--global-gini-tree-topology-trace", run_dir / "gini_topology.csv"),
        ("--global-gini-tree-sibling-trace", run_dir / "sibling_delay.csv"),
        ("--global-gini-tree-row-delta-trace", run_dir / "row_delta.csv"),
        ("--global-gini-tree-memory-trace", run_dir / "tree_memory.csv"),
        ("--global-gini-tree-mip-start-audit", run_dir / "mip_start_audit.csv"),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    args.extend(production_binding(
        run_dir, "S0-CPLEX", S0_EXE,
        manifest["source_commit"], manifest["protocol_sha256"]))
    return args


def c2_command(instance: str, budget: int, run_dir: Path) -> list[str]:
    manifest = load_json(
        ROOT / "results/gf_paper_safe_gurobi_scheduling_round27/c2_paper_manifest.json")
    args = [str(C2_EXE), "--input", str(instance_path(instance))]
    args.extend(tailored_options(run_dir, budget))
    for name, value in (
        ("--frontier-execution-mode", "external-gini-tree"),
        ("--external-gini-scheduling", "paper-lp-event"),
        ("--external-gini-artifact-dir", run_dir / "external"),
        ("--external-gini-backend", "gurobi"),
        ("--external-gini-lifecycle", "retained-per-leaf"),
        ("--external-gini-warm-start", False),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0), ("--gurobi-presolve", -1),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    args.extend(production_binding(
        run_dir, "C2-PAPER", C2_EXE, manifest["build_source_commit"],
        manifest["protocol_sha256"]))
    return args


def c3_command(instance: str, budget: int, run_dir: Path) -> list[str]:
    manifest = load_json(C3_MANIFEST)
    args = [str(C3_EXE), "--input", str(instance_path(instance))]
    args.extend(tailored_options(run_dir, budget))
    for name, value in (
        ("--frontier-execution-mode", "external-gini-tree"),
        ("--external-gini-scheduling", "cplex-algorithm-replica"),
        ("--external-gini-artifact-dir", run_dir / "external"),
        ("--external-gini-backend", "gurobi"),
        ("--external-gini-lifecycle", "retained-per-leaf"),
        ("--external-gini-warm-start", False),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0), ("--gurobi-presolve", -1),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        add(args, name, value)
    args.extend(production_binding(
        run_dir, "C3-REPLICA", C3_EXE, manifest["source_commit"],
        manifest["protocol_sha256"]))
    return args


def command_for(instance: str, arm: str, budget: int,
                run_dir: Path) -> list[str]:
    if arm == "P-GRB":
        return plain_command(instance, budget, run_dir)
    if arm == "S0-CPLEX":
        return s0_command(instance, budget, run_dir)
    if arm == "C2-PAPER":
        return c2_command(instance, budget, run_dir)
    if arm == "C3-REPLICA":
        return c3_command(instance, budget, run_dir)
    raise ValueError(f"unknown arm: {arm}")


def executable_for(arm: str) -> Path:
    return {"P-GRB": P_EXE, "S0-CPLEX": S0_EXE,
            "C2-PAPER": C2_EXE, "C3-REPLICA": C3_EXE}[arm]


def licensed_arm(arm: str) -> bool:
    return arm in ("P-GRB", "C2-PAPER", "C3-REPLICA")


def sensitive_marker_present(directory: Path) -> bool:
    markers = (b"LicenseID", b"WLSAccessID", b"WLSSecret", b"TokenServer",
               b"Set parameter Username", b"Computer ID", b"HOSTID")
    for path in directory.rglob("*"):
        if path.is_file() and path.suffix.lower() in (".log", ".txt", ".json"):
            if any(marker in path.read_bytes() for marker in markers):
                return True
    return False


def validate_frozen(arm: str, instance: str) -> None:
    verify_instance(instance)
    if sha256(PROTOCOL) != load_json(C3_MANIFEST)["protocol_sha256"]:
        raise RuntimeError("Round 28 protocol changed after C3 freeze")
    exe = executable_for(arm)
    if not exe.is_file():
        raise RuntimeError(f"missing frozen executable: {arm}")
    if (arm == "C3-REPLICA" and sha256(exe) !=
            load_json(C3_MANIFEST)["executable_sha256"]):
        raise RuntimeError("C3 executable changed after freeze")


def run_one(stage: str, instance: str, arm: str, budget: int,
            repetition: int = 0, official: bool = True) -> dict[str, Any]:
    suffix = f"__rep{repetition}" if repetition else ""
    run_id = (f"{stage}__{instance}__{arm.lower().replace('-', '_')}"
              f"{suffix}__{budget}s")
    run_dir = RUNS / run_id
    state_path = run_dir / "run_state.json"
    if state_path.is_file():
        state = load_json(state_path)
        if state.get("completed"):
            print(f"SKIP {run_id}", flush=True)
            return state
        raise RuntimeError(f"incomplete run requires audit: {run_id}")
    validate_frozen(arm, instance)
    run_dir.mkdir(parents=True, exist_ok=False)
    command = command_for(instance, arm, budget, run_dir)
    record: dict[str, Any] = {
        "schema": "round28-command-v1", "run_id": run_id,
        "stage": stage, "instance": instance,
        "family": INSTANCES[instance][1], "V": INSTANCES[instance][2],
        "M": INSTANCES[instance][3], "arm": arm,
        "repetition": repetition, "budget_seconds": budget,
        "command": command,
        "executable_sha256": sha256(executable_for(arm)),
        "instance_sha256": sha256(instance_path(instance)),
        "protocol_sha256": sha256(PROTOCOL),
        "license_environment": ("process-local-authorized-path-not-serialized"
                                if licensed_arm(arm) else "not_required"),
        "official": official, "started_unix": time.time(),
        "completed": False,
    }
    json_write(run_dir / "command.json", record)
    environment = os.environ.copy()
    if licensed_arm(arm):
        environment["GRB_LICENSE_FILE"] = str(LICENSE)
    started = time.monotonic()
    emergency_timeout = False
    with (run_dir / "console.stdout.log").open("wb") as stdout, \
         (run_dir / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=environment, stdout=stdout,
                stderr=stderr, timeout=budget + 15, check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            emergency_timeout = True
            return_code = 124
    record.update({
        "finished_unix": time.time(),
        "runner_wall_seconds": time.monotonic() - started,
        "return_code": return_code,
        "emergency_timeout": emergency_timeout,
        "result_exists": (run_dir / "result.json").is_file(),
        "sensitive_marker_scan_passed": not sensitive_marker_present(run_dir),
        "completed": True,
    })
    json_write(state_path, record)
    if not record["sensitive_marker_scan_passed"]:
        raise RuntimeError(f"sensitive marker detected: {run_id}")
    print(f"DONE {run_id} rc={return_code} "
          f"wall={record['runner_wall_seconds']:.3f}", flush=True)
    return record


def acquire_lock() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as error:
        raise RuntimeError(f"runner lock exists: {LOCK}") from error
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(f"pid={os.getpid()}\n")


def stage_matrix(stage: str) -> tuple[tuple[str, str, int], ...]:
    if stage == "stage1":
        return tuple((instance, arm, 0) for instance in STAGE1_INSTANCES
                     for arm in ("S0-CPLEX", "C3-REPLICA"))
    if stage == "stage2":
        return tuple((instance, arm, 0) for instance in PRIMARY
                     for arm in ("P-GRB", "C3-REPLICA"))
    if stage == "stage3":
        return tuple((instance, arm, 0) for instance in ANCHORS
                     for arm in ("S0-CPLEX", "C2-PAPER", "C3-REPLICA"))
    if stage == "stage4":
        return tuple((instance, "C3-REPLICA", repetition)
                     for instance in STAGE4_INSTANCES
                     for repetition in (1, 2))
    raise ValueError(stage)


def compress_large_files() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    manifest_path = OUT / "compression_manifest.csv"
    if manifest_path.is_file():
        with manifest_path.open(newline="", encoding="utf-8") as stream:
            records.extend(csv.DictReader(stream))
    for path in sorted(RUNS.rglob("*")):
        if (not path.is_file() or path.stat().st_size < COMPRESSION_THRESHOLD or
                path.suffix.lower() not in (".csv", ".log", ".lp")):
            continue
        target = Path(str(path) + ".gz")
        original_hash = sha256(path)
        original_bytes = path.stat().st_size
        with path.open("rb") as source, target.open("wb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw,
                               compresslevel=9, mtime=0) as sink:
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    sink.write(block)
        restored = hashlib.sha256()
        restored_bytes = 0
        with gzip.open(target, "rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                restored.update(block)
                restored_bytes += len(block)
        if (restored.hexdigest() != original_hash or
                restored_bytes != original_bytes):
            target.unlink(missing_ok=True)
            raise RuntimeError(f"compression verification failed: {path}")
        path.unlink()
        records.append({
            "original_path": relative(path),
            "compressed_path": relative(target),
            "original_bytes": original_bytes,
            "compressed_bytes": target.stat().st_size,
            "original_sha256": original_hash,
            "compressed_sha256": sha256(target),
            "restoration_sha256": restored.hexdigest(),
            "restoration_bytes": restored_bytes,
            "compression": "gzip_level9_mtime0_filename_omitted",
        })
    fields = list(records[0]) if records else [
        "original_path", "compressed_path", "original_bytes",
        "compressed_bytes", "original_sha256", "compressed_sha256",
        "restoration_sha256", "restoration_bytes", "compression"]
    csv_write(manifest_path, records, fields)
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-instance-manifest", action="store_true")
    parser.add_argument("--compress", action="store_true")
    parser.add_argument("--stage", choices=("stage1", "stage2", "stage3", "stage4"))
    args = parser.parse_args()
    if args.prepare_instance_manifest:
        prepare_instance_manifest()
        return 0
    if args.compress:
        print(f"compressed_files={len(compress_large_files())}", flush=True)
        return 0
    if not args.stage:
        parser.error("--stage, --prepare-instance-manifest, or --compress required")
    if not C3_MANIFEST.is_file():
        raise SystemExit("C3 manifest must be frozen before official runs")
    if not LICENSE.is_file():
        raise SystemExit("authorized Gurobi license path unavailable")
    acquire_lock()
    failures = 0
    try:
        for instance, arm, repetition in stage_matrix(args.stage):
            state = run_one(args.stage, instance, arm, OFFICIAL_BUDGET,
                            repetition=repetition, official=True)
            if (state["return_code"] != 0 or not state["result_exists"] or
                    state["emergency_timeout"]):
                failures += 1
        print(f"{args.stage.upper()} complete process_failures={failures}",
              flush=True)
        return 1 if failures else 0
    finally:
        LOCK.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
