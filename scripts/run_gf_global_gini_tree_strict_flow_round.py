#!/usr/bin/env python3
"""Run and audit the serial Round 21 strict-certificate/flow experiment.

The runner is deliberately fail closed.  A result is resumable only when it was
produced by the frozen executable and its native gap parameters, lifecycle,
lower-bound retention, gap arithmetic, certificate classification, and process
wall accounting all validate.  Failed attempts are retained but are excluded
from fresh numerical tables.

Windows/MSYS2 usage (the WindowsApps ``python`` shim is not used)::

    D:/msys64/ucrt64/bin/python.exe scripts/run_gf_global_gini_tree_strict_flow_round.py --stage stage0
    D:/msys64/ucrt64/bin/python.exe scripts/run_gf_global_gini_tree_strict_flow_round.py --stage stage1 --dry-run
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import gzip
import hashlib
import io
import json
import math
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
ROUND = "gf_global_gini_tree_strict_flow_round"
RESULTS = ROOT / "results" / ROUND
RAW = RESULTS / "raw"
LOGS = RESULTS / "logs"
COMMANDS = RESULTS / "commands"
RUNS = RESULTS / "runs"
AUDITS = RESULTS / "audits"
INTERRUPTED = RESULTS / "interrupted"
MECHANICAL = RESULTS / "mechanical"
EXE = ROOT / "build_round21" / "ExactEBRP-frozen.exe"
TEST_BIN_DIR = ROOT / "build_round21" / "tests"
LOCK = RESULTS / ".round21_runner.lock"
FROZEN = AUDITS / "frozen_executable.json"

# The native CPLEX deadline is kept below the nominal process-wall deadline.
# The runner timeout is an emergency engineering guard, not an official budget.
EMERGENCY_CLEANUP_TOLERANCE_SECONDS = 30.0
COMPRESS_THRESHOLD_BYTES = 4 * 1024 * 1024
# Keep a margin below GitHub's 100 MiB hard object limit.  Oversized compressed
# evidence is split into ordered reconstruction parts, each below this ceiling.
MAX_COMMITTED_ARTIFACT_BYTES = 90 * 1024 * 1024
REL_GAP_PARAM_ID = 2009
ABS_GAP_PARAM_ID = 2008

INSTANCES: dict[str, dict[str, str]] = {
    "V12_M1": {
        "path": "reference/regen_candidate_V12_M1_average.txt",
        "class": "V12-control",
    },
    "V12_M2": {
        "path": "reference/regen_candidate_V12_M2_average.txt",
        "class": "V12-control",
    },
    "tight_T_seed3101": {
        "path": "reference/hard_stress/V20_M3/tight_T_seed3101.txt",
        "class": "V20-control",
    },
    "high_imbalance_seed3202": {
        "path": "reference/hard_stress/V20_M3/high_imbalance_seed3202.txt",
        "class": "V20-control",
    },
    "moderate_seed3301": {
        "path": "reference/hard_stress/V20_M3/moderate_seed3301.txt",
        "class": "V20-primary-regression",
    },
    "moderate_seed3302": {
        "path": "reference/hard_stress/V20_M3/moderate_seed3302.txt",
        "class": "V20-control",
    },
    "high_imbalance_seed3201": {
        "path": "reference/hard_stress/V20_M3/high_imbalance_seed3201.txt",
        "class": "V20-control",
    },
    "tight_T_seed3102": {
        "path": "reference/hard_stress/V20_M3/tight_T_seed3102.txt",
        "class": "V20-control",
    },
    "round21_toy_V2_M1": {
        "path": f"results/{ROUND}/mechanical/round21_toy_V2_M1.txt",
        "class": "Stage0-exact-toy",
    },
}
ROUND20_INSTANCES = (
    "V12_M1", "V12_M2", "tight_T_seed3101", "high_imbalance_seed3202",
    "moderate_seed3301", "moderate_seed3302", "high_imbalance_seed3201",
    "tight_T_seed3102",
)
STAGE0_TOY = "round21_toy_V2_M1"

STAGE0_INSTANCES = (
    "V12_M1",
    "V12_M2",
    "moderate_seed3301",
    "tight_T_seed3101",
    "high_imbalance_seed3202",
)
STAGE1_INSTANCES = (
    "moderate_seed3301",
    "tight_T_seed3101",
    "high_imbalance_seed3202",
    "moderate_seed3302",
    "V12_M2",
)
STAGE3_INSTANCES = (
    "moderate_seed3301",
    "tight_T_seed3101",
    "high_imbalance_seed3202",
    "moderate_seed3302",
    "tight_T_seed3102",
)

FLOW_VARIANTS: dict[str, str] = {
    "off": "off",
    "F0": "round20-current",
    "F1": "zero-return",
    "F2": "normalized",
    "F3": "normalized-start-coupled",
}
FLOW_ALIASES = {
    "off": "off",
    "no-flow": "off",
    "no_flow": "off",
    "f0": "F0",
    "round20-current": "F0",
    "round20_current": "F0",
    "f1": "F1",
    "zero-return": "F1",
    "zero_return": "F1",
    "f2": "F2",
    "normalized": "F2",
    "f3": "F3",
    "normalized-start-coupled": "F3",
    "normalized_start_coupled": "F3",
}
STAGE1_ARMS = ("off", "F0", "F1", "F2", "F3")
THRESHOLDS = (0.20, 0.10, 0.05, 0.01, 0.0)
CHECKPOINTS: dict[str, tuple[int, ...]] = {
    "stage0": (30,),
    "stage1": (30, 60, 120, 180, 300),
    "stage2": (30, 60, 120, 300, 600, 900),
    "stage3": (30, 60, 120, 300, 600, 900, 1200, 1800),
    "stage4": (30, 60, 120, 300, 600, 900, 1200, 1800, 2400, 3000, 3600),
}

UNIT_EXECUTABLES = (
    "StrictCertificateTests.exe",
    "ConnectivityFlowTests.exe",
    "StrictSerializationTests.exe",
    "GlobalGiniTreeTests.exe",
    "ControllingLeafSchedulerTests.exe",
)


@dataclass(frozen=True)
class RunSpec:
    stage: str
    instance: str
    arm: str
    budget_seconds: int

    @property
    def run_id(self) -> str:
        arm = "plain" if self.arm == "plain" else self.arm.lower()
        return f"{self.stage}__{self.instance}__{arm}__{self.budget_seconds}s"

    @property
    def variant(self) -> str:
        return "plain" if self.arm == "plain" else FLOW_VARIANTS[self.arm]


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", delete=False,
        prefix=path.name + ".", suffix=".tmp", dir=path.parent,
    ) as stream:
        temporary = Path(stream.name)
        stream.write(content)
    os.replace(temporary, path)


def atomic_json(path: Path, value: Any) -> None:
    atomic_text(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Sequence[str] = ()) -> None:
    material = [dict(row) for row in rows]
    names = list(fields)
    for row in material:
        for key in row:
            if key not in names:
                names.append(key)
    if not names:
        names = ["status", "not_run_reason"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="", delete=False,
        prefix=path.name + ".", suffix=".tmp", dir=path.parent,
    ) as stream:
        temporary = Path(stream.name)
        writer = csv.DictWriter(stream, fieldnames=names, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(material)
    os.replace(temporary, path)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    if isinstance(value, dict) and isinstance(value.get("results"), list):
        values = value["results"]
        return values[0] if values and isinstance(values[0], dict) else {}
    return value if isinstance(value, dict) else {}


def read_csv(path: Path) -> list[dict[str, str]]:
    candidate = path
    if not candidate.exists() and Path(str(path) + ".gz").exists():
        candidate = Path(str(path) + ".gz")
    multipart = sorted(path.parent.glob(path.name + ".gz.part[0-9][0-9][0-9]"))
    if not candidate.exists() and multipart:
        compressed = tempfile.SpooledTemporaryFile(max_size=32 * 1024 * 1024)
        for part in multipart:
            with part.open("rb") as stream:
                shutil.copyfileobj(stream, compressed)
        compressed.seek(0)
        binary = gzip.GzipFile(fileobj=compressed, mode="rb")
        with io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))
    if not candidate.exists() or candidate.stat().st_size == 0:
        return []
    opener = gzip.open if candidate.suffix == ".gz" else open
    with opener(candidate, "rt", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def number(value: Any, default: float = math.nan) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result


def integer(value: Any, default: int = -1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "yes"}


def same_float(left: Any, right: Any) -> bool:
    a, b = number(left), number(right)
    return math.isfinite(a) and math.isfinite(b) and a == b


def close_float(left: Any, right: Any, scale: float = 8.0) -> bool:
    a, b = number(left), number(right)
    if not (math.isfinite(a) and math.isfinite(b)):
        return False
    tolerance = scale * math.ulp(max(1.0, abs(a), abs(b)))
    return abs(a - b) <= tolerance


def ensure_dirs() -> None:
    for path in (RESULTS, RAW, LOGS, COMMANDS, RUNS, AUDITS, INTERRUPTED, MECHANICAL):
        path.mkdir(parents=True, exist_ok=True)


def ensure_stage0_toy() -> Path:
    """Materialize the fixed two-station exact toy inside the fresh package."""
    path = ROOT / INSTANCES[STAGE0_TOY]["path"]
    content = """2 1 [1]
capacities = [100000, 2, 2]
initial     = [50000, 2, 0]
target      = [0, 1, 1]
weights     = [0.0, 1.0, 1.0]
min_ratio  = [0.0, 0.0, 0.0]
distances = [
{0.0, 1.0, 1.0}
{1.0, 0.0, 1.0}
{1.0, 1.0, 0.0}
]
"""
    if path.exists() and path.read_text(encoding="utf-8") != content:
        raise RuntimeError(f"Stage 0 toy fixture changed unexpectedly: {path}")
    if not path.exists():
        atomic_text(path, content)
    return path


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
            encoding="utf-8", errors="replace",
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def native_reserve(budget_seconds: int) -> float:
    if budget_seconds <= 0 or budget_seconds > 3600:
        raise ValueError(f"official budget must be in 1..3600 seconds, got {budget_seconds}")
    return min(30.0, max(2.0, 0.02 * float(budget_seconds)))


def native_budget(budget_seconds: int) -> float:
    return float(budget_seconds) - native_reserve(budget_seconds)


def normalize_variant(value: str) -> str:
    key = value.strip()
    normalized = FLOW_ALIASES.get(key, FLOW_ALIASES.get(key.lower(), ""))
    if normalized not in {"F1", "F2", "F3"}:
        raise ValueError("--selected-variant must be F1, F2, or F3")
    return normalized


def paths(run_id: str) -> dict[str, Path]:
    run = RUNS / run_id
    return {
        "run": run,
        "json": RAW / f"{run_id}.json",
        "log": LOGS / f"{run_id}.log",
        "command": COMMANDS / f"{run_id}.json",
        "progress": run / "progress.csv",
        "node": run / "global_node_trace.csv",
        "bound": run / "global_bound_trajectory.csv",
        "root": run / "global_root.lp",
        "manifest": run / "model_lifecycle_manifest.csv",
        "post": run / "post_local_row_trace.csv",
        "topology": run / "gini_topology.csv",
        "sibling": run / "sibling_delay.csv",
        "delta": run / "row_delta.csv",
        "memory": run / "tree_memory.csv",
        "mip": run / "mip_start_audit.csv",
        "artifacts": run / "artifact_manifest.csv",
        "pristine": run / "solver_result_pristine.json",
        "checkpoints": run / "checkpoint_metrics.csv",
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


def frozen_nonflow_flags() -> list[str]:
    return [
        "--tailored-bc-enabled", "true",
        "--tailored-bc-mode", "static",
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


def global_command(spec: RunSpec, p: Mapping[str, Path]) -> list[str]:
    return [
        str(EXE),
        "--method", "gcap-frontier",
        "--algorithm-preset", "paper-gf-tailored-bc",
        "--paper-run-sealed", "true",
        "--input", str(ROOT / INSTANCES[spec.instance]["path"]),
        "--lambda", "0.15",
        "--T", "3600",
        "--time-limit", format(native_budget(spec.budget_seconds), ".17g"),
        "--process-wall-time-limit", str(spec.budget_seconds),
        "--threads", "1",
        "--mip-threads", "1",
        "--compact-bc-threads", "1",
        "--cplex-threads", "1",
        "--primal-heuristic", "hga-tgbc",
        "--progress-log", str(p["progress"]),
        "--progress-interval-seconds", "30",
        "--log", str(p["log"]),
        "--out", str(p["json"]),
    ] + frozen_nonflow_flags() + [
        "--frontier-execution-mode", "global-gini-tree",
        "--global-gini-tree-presolve", "on",
        "--global-gini-tree-search", "traditional",
        "--global-gini-tree-child-estimate", "parent-copy",
        "--global-gini-tree-row-attachment", "full-inherited-pack",
        "--global-gini-tree-row-timing", "deferred",
        "--global-gini-tree-native-mip-start", "false",
        "--global-gini-tree-root-connectivity-flow", "false",
        "--global-gini-tree-root-connectivity-flow-variant", spec.variant,
        "--global-gini-tree-node-trace", str(p["node"]),
        "--global-gini-tree-bound-trace", str(p["bound"]),
        "--global-gini-tree-manifest", str(p["manifest"]),
        "--global-gini-tree-root-export", str(p["root"]),
        "--global-gini-tree-post-row-trace", str(p["post"]),
        "--global-gini-tree-topology-trace", str(p["topology"]),
        "--global-gini-tree-sibling-trace", str(p["sibling"]),
        "--global-gini-tree-row-delta-trace", str(p["delta"]),
        "--global-gini-tree-memory-trace", str(p["memory"]),
        "--global-gini-tree-mip-start-audit", str(p["mip"]),
    ]


def plain_command(spec: RunSpec, p: Mapping[str, Path]) -> list[str]:
    return [
        str(EXE),
        "--method", "cplex",
        "--plain-baseline",
        "--input", str(ROOT / INSTANCES[spec.instance]["path"]),
        "--lambda", "0.15",
        "--T", "3600",
        "--time-limit", format(native_budget(spec.budget_seconds), ".17g"),
        "--process-wall-time-limit", str(spec.budget_seconds),
        "--threads", "1",
        "--cplex-threads", "1",
        "--mip-threads", "1",
        "--progress-log", str(p["progress"]),
        "--progress-interval-seconds", "30",
        "--log", str(p["log"]),
        "--out", str(p["json"]),
    ]


def command_for(spec: RunSpec, p: Mapping[str, Path]) -> list[str]:
    return plain_command(spec, p) if spec.arm == "plain" else global_command(spec, p)


def stage_specs(stage: str, selected: str) -> list[RunSpec]:
    if stage == "stage0":
        # The first five rows compare the exact original toy optimum under every
        # formulation.  The remaining integration gates exercise F2 plus the
        # strict native evidence path on the requested benchmark controls.
        return (
            [RunSpec(stage, STAGE0_TOY, arm, 30) for arm in STAGE1_ARMS] +
            [RunSpec(stage, instance, "F2", 30) for instance in STAGE0_INSTANCES]
        )
    if stage == "stage1":
        return [
            RunSpec(stage, instance, arm, 300)
            for instance in STAGE1_INSTANCES for arm in STAGE1_ARMS
        ]
    if stage == "stage2":
        return [
            RunSpec(stage, instance, arm, 900)
            for instance in ROUND20_INSTANCES for arm in ("F0", selected, "plain")
        ]
    if stage == "stage3":
        return [
            RunSpec(stage, instance, arm, 1800)
            for instance in STAGE3_INSTANCES for arm in ("F0", selected, "plain")
        ]
    if stage == "stage4":
        return conditional_stage4_specs(selected)
    raise ValueError(stage)


def command_signature(spec: RunSpec, command: Sequence[str], executable_hash: str) -> str:
    return json_hash({
        "runner_schema": "round21-runner-v1",
        "run_id": spec.run_id,
        "command": list(command),
        "executable_sha256": executable_hash,
        "instance_sha256": sha256(ROOT / INSTANCES[spec.instance]["path"]),
    })


def process_snapshot() -> dict[str, Any]:
    answer: dict[str, Any] = {
        "exactebrp_count": 0, "external_cplex_count": 0, "source": "tasklist",
    }
    try:
        output = subprocess.check_output(
            ["tasklist", "/FO", "CSV", "/NH"], text=True,
            encoding="utf-8", errors="replace",
        )
        names = [line.split(",", 1)[0].strip('"').lower() for line in output.splitlines()]
        answer["exactebrp_count"] = sum(name.startswith("exactebrp") for name in names)
        answer["external_cplex_count"] = sum(name == "cplex.exe" for name in names)
    except Exception as error:  # process inventory failure itself is retained
        answer["source"] = f"snapshot_failed:{error}"
    return answer


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


@contextlib.contextmanager
def serial_lock() -> Iterator[None]:
    ensure_dirs()
    record = {"pid": os.getpid(), "hostname": socket.gethostname(), "created_at": now()}
    try:
        descriptor = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        retained = read_json(LOCK)
        if retained.get("hostname") == socket.gethostname() and not pid_alive(integer(retained.get("pid"), -1)):
            stale = RESULTS / f".round21_runner.stale.{int(time.time())}.lock"
            os.replace(LOCK, stale)
            descriptor = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        else:
            raise RuntimeError(f"serial runner lock is active: {LOCK}: {retained}")
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")
    try:
        yield
    finally:
        try:
            current = read_json(LOCK)
            if integer(current.get("pid"), -1) == os.getpid():
                LOCK.unlink()
        except OSError:
            pass


def freeze_executable() -> str:
    if not EXE.is_file():
        raise FileNotFoundError(f"frozen release executable is missing: {EXE}")
    current_hash = sha256(EXE)
    existing = read_json(FROZEN)
    if existing:
        if existing.get("sha256") != current_hash:
            raise RuntimeError(
                "build_round21/ExactEBRP-frozen.exe changed after the Round 21 result package was frozen"
            )
        return current_hash
    atomic_json(FROZEN, {
        "schema": "round21-frozen-executable-v1",
        "frozen_at": now(),
        "path": relative(EXE),
        "sha256": current_hash,
        "size_bytes": EXE.stat().st_size,
        "git_head": git_head(),
    })
    return current_hash


def archive_attempt(spec: RunSpec, reason: str) -> Path:
    p = paths(spec.run_id)
    base = INTERRUPTED / spec.run_id
    index = 1
    while (base / f"attempt_{index}").exists():
        index += 1
    target = base / f"attempt_{index}"
    target.mkdir(parents=True, exist_ok=False)
    for key in ("json", "log", "command"):
        source = p[key]
        if source.exists():
            shutil.copy2(source, target / source.name)
    if p["run"].exists():
        shutil.copytree(p["run"], target / "run_artifacts")
    atomic_text(target / "archive_reason.txt", reason.rstrip() + "\n")
    normalize_archived_evidence(target)
    return target


def clear_attempt(spec: RunSpec) -> None:
    p = paths(spec.run_id)
    for key in ("json", "log", "command"):
        try:
            p[key].unlink()
        except FileNotFoundError:
            pass
    if p["run"].exists():
        shutil.rmtree(p["run"])


def append_runner_output(log: Path, stdout: str, stderr: str) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8", newline="") as stream:
        stream.write("\n--- ROUND21 RUNNER CAPTURED STDOUT ---\n")
        stream.write(stdout or "")
        stream.write("\n--- ROUND21 RUNNER CAPTURED STDERR ---\n")
        stream.write(stderr or "")


def stamp_result(path: Path, spec: RunSpec, executable_hash: str, signature: str) -> None:
    data = read_json(path)
    if not data:
        return
    data.update({
        "source_round": ROUND,
        "fresh_run": True,
        "result_package": relative(RESULTS),
        "round21_run_id": spec.run_id,
        "round21_stage": spec.stage,
        "round21_instance": spec.instance,
        "round21_arm": spec.arm,
        "round21_flow_variant": spec.variant,
        "round21_nominal_process_wall_seconds": spec.budget_seconds,
        "round21_native_time_limit_seconds": native_budget(spec.budget_seconds),
        "round21_finalization_reserve_seconds": native_reserve(spec.budget_seconds),
        "round21_executable_sha256": executable_hash,
        "round21_command_signature": signature,
    })
    atomic_json(path, data)


def compress_file(path: Path) -> Path:
    target = Path(str(path) + ".gz")
    with path.open("rb") as source, target.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as sink:
            shutil.copyfileobj(source, sink, length=1024 * 1024)
    with gzip.open(target, "rb") as check:
        while check.read(1024 * 1024):
            pass
    path.unlink()
    return target


def harvest_plain_model(data: Mapping[str, Any], p: Mapping[str, Path]) -> None:
    if p["root"].exists() or Path(str(p["root"]) + ".gz").exists():
        return
    notes = data.get("notes", [])
    if not isinstance(notes, list):
        return
    for note in notes:
        match = re.match(r"LP file:\s*(.+)$", str(note))
        if not match:
            continue
        source = Path(match.group(1).strip())
        if not source.is_absolute():
            source = ROOT / source
        if source.is_file():
            shutil.copy2(source, p["root"])
            return


def update_result_artifact_paths(path: Path, replacements: Mapping[str, str]) -> None:
    data = read_json(path)
    if not data:
        return
    keys = (
        "global_gini_tree_root_model_path",
        "global_gini_tree_node_trace_path",
        "global_gini_tree_bound_trace_path",
        "global_gini_tree_row_delta_trace_path",
        "global_gini_tree_memory_trace_path",
        "log_file",
    )
    for key in keys:
        value = str(data.get(key, ""))
        if value in replacements:
            data[key] = replacements[value]
        elif value and str(Path(value)) in replacements:
            data[key] = replacements[str(Path(value))]
    atomic_json(path, data)


def update_lifecycle_artifact_paths(path: Path, replacements: Mapping[str, str]) -> None:
    # The lifecycle manifest is a two-column key/value CSV without a header.
    if not path.exists():
        return
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        raw_rows = list(csv.reader(stream))
    changed = False
    for row in raw_rows:
        if len(row) >= 2 and row[1] in replacements:
            row[1] = replacements[row[1]]
            changed = True
    if changed:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", delete=False,
            prefix=path.name + ".", suffix=".tmp", dir=path.parent,
        ) as stream:
            temporary = Path(stream.name)
            csv.writer(stream, lineterminator="\n").writerows(raw_rows)
        os.replace(temporary, path)


def split_oversized(path: Path) -> tuple[list[Path], str]:
    """Split an already-compressed artifact into ordered reconstruction parts."""
    complete_hash = sha256(path)
    parts: list[Path] = []
    with path.open("rb") as source:
        index = 1
        while True:
            block = source.read(MAX_COMMITTED_ARTIFACT_BYTES)
            if not block:
                break
            part = Path(f"{path}.part{index:03d}")
            with part.open("wb") as sink:
                sink.write(block)
            parts.append(part)
            index += 1
    if not parts or any(part.stat().st_size > MAX_COMMITTED_ARTIFACT_BYTES for part in parts):
        raise RuntimeError(f"could not split oversized committed artifact safely: {path}")
    path.unlink()
    return parts, complete_hash


def normalize_archived_evidence(root: Path) -> None:
    """Compress a possibly half-written attempt before retaining it forever."""
    rows: list[dict[str, Any]] = []
    for source in sorted(path for path in root.rglob("*") if path.is_file()):
        if source.name == "archive_artifact_manifest.csv" or ".gz.part" in source.name:
            continue
        requested = source.relative_to(root).as_posix()
        actual = source
        gzip_appended = False
        # JSON and command records stay directly inspectable.  Large logs, LPs,
        # and traces are compressed even for failed/interrupted attempts.
        if source.suffix not in {".json"} and source.suffix != ".gz" and (
            source.suffix in {".lp", ".log"} or source.stat().st_size >= COMPRESS_THRESHOLD_BYTES
        ):
            actual = compress_file(source)
            gzip_appended = True
        parts = [actual]
        complete_hash = sha256(actual)
        if actual.stat().st_size > MAX_COMMITTED_ARTIFACT_BYTES:
            if actual.suffix != ".gz":
                raise RuntimeError(f"archived directly readable artifact exceeds safe GitHub limit: {actual}")
            parts, complete_hash = split_oversized(actual)
        for index, part in enumerate(parts, start=1):
            rows.append({
                "requested_path": requested,
                "retained_path": part.relative_to(root).as_posix(),
                "gzip_appended": gzip_appended,
                "multipart": len(parts) > 1,
                "part_index": index,
                "part_count": len(parts),
                "size_bytes": part.stat().st_size,
                "sha256": sha256(part),
                "complete_retained_sha256": complete_hash,
            })
    write_csv(root / "archive_artifact_manifest.csv", rows)


def package_size_audit() -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    violations: list[str] = []
    size_audit_path = AUDITS / "commit_artifact_size_audit.csv"
    for path in sorted(item for item in RESULTS.rglob("*") if item.is_file()):
        # A checksum ledger cannot truthfully contain its own post-write hash.
        if path == LOCK or path == size_audit_path:
            continue
        size = path.stat().st_size
        passed = size <= MAX_COMMITTED_ARTIFACT_BYTES
        rows.append({
            "path": relative(path),
            "size_bytes": size,
            "safe_limit_bytes": MAX_COMMITTED_ARTIFACT_BYTES,
            "status": "PASS" if passed else "FAIL",
            "sha256": sha256(path),
        })
        if not passed:
            violations.append(relative(path))
    return rows, violations


def retain_artifacts(spec: RunSpec) -> None:
    p = paths(spec.run_id)
    data = read_json(p["json"])
    if spec.arm == "plain":
        harvest_plain_model(data, p)

    replacements: dict[str, str] = {}
    requested = {
        "root_model": p["root"],
        "node_trace": p["node"],
        "bound_trace": p["bound"],
        "row_delta_trace": p["delta"],
        "post_row_trace": p["post"],
        "topology_trace": p["topology"],
        "sibling_trace": p["sibling"],
        "tree_memory_trace": p["memory"],
        "mip_start_audit": p["mip"],
        "progress_trace": p["progress"],
        "lifecycle_manifest": p["manifest"],
        "solver_result_pristine": p["pristine"],
        "solver_log": p["log"],
        "checkpoint_metrics": p["checkpoints"],
    }
    retained: dict[str, tuple[list[Path], bool, str]] = {}
    for role, source in requested.items():
        actual = source
        appended = False
        # Raw/stamped JSON and command/summary CSVs remain directly readable.
        directly_readable = role == "solver_result_pristine"
        if source.exists() and not directly_readable and (
            source.suffix == ".lp" or source.stat().st_size >= COMPRESS_THRESHOLD_BYTES
        ):
            original_text = str(source)
            actual = compress_file(source)
            replacements[original_text] = str(actual)
            replacements[str(source.resolve())] = str(actual.resolve())
            appended = True
        elif not source.exists() and Path(str(source) + ".gz").exists():
            actual = Path(str(source) + ".gz")
            appended = True
        if actual.exists():
            complete_hash = sha256(actual)
            actual_parts = [actual]
            if actual.stat().st_size > MAX_COMMITTED_ARTIFACT_BYTES:
                if actual.suffix != ".gz":
                    raise RuntimeError(
                        f"directly readable artifact exceeds safe GitHub size limit: {actual}"
                    )
                actual_parts, complete_hash = split_oversized(actual)
                first_part = str(actual_parts[0])
                for old, replacement in list(replacements.items()):
                    if replacement == str(actual) or replacement == str(actual.resolve()):
                        replacements[old] = first_part
            retained[role] = (actual_parts, appended, complete_hash)

    if replacements:
        update_result_artifact_paths(p["json"], replacements)
        update_lifecycle_artifact_paths(p["manifest"], replacements)

    rows: list[dict[str, Any]] = []
    for role, requested_path in requested.items():
        if role not in retained:
            rows.append({
                "artifact_role": role,
                "requested_path": relative(requested_path),
                "retained_path": "",
                "exists": False,
                "gzip_appended": False,
                "size_bytes": "",
                "sha256": "",
            })
            continue
        actual_parts, appended, complete_hash = retained[role]
        for part_index, actual in enumerate(actual_parts, start=1):
            if actual.stat().st_size > MAX_COMMITTED_ARTIFACT_BYTES:
                raise RuntimeError(f"retained artifact exceeds safe GitHub size limit: {actual}")
            rows.append({
                "artifact_role": role,
                "requested_path": relative(requested_path),
                "retained_path": relative(actual),
                "exists": True,
                "gzip_appended": appended,
                "multipart": len(actual_parts) > 1,
                "part_index": part_index,
                "part_count": len(actual_parts),
                "size_bytes": actual.stat().st_size,
                "sha256": sha256(actual),
                "complete_retained_sha256": complete_hash,
                "reconstruction": (
                    "concatenate parts in part_index order, then gunzip"
                    if len(actual_parts) > 1 else "none"
                ),
            })
    write_csv(p["artifacts"], rows)


def append_control_artifacts_to_manifest(spec: RunSpec) -> None:
    """Add final readable JSON/command records after validation metadata settles."""
    p = paths(spec.run_id)
    rows = [
        row for row in read_csv(p["artifacts"])
        if row.get("artifact_role") not in {"stamped_result_json", "command_record"}
    ]
    for role, path in (("stamped_result_json", p["json"]), ("command_record", p["command"])):
        if not path.exists():
            continue
        if path.stat().st_size > MAX_COMMITTED_ARTIFACT_BYTES:
            raise RuntimeError(f"directly readable {role} exceeds safe GitHub size limit: {path}")
        rows.append({
            "artifact_role": role,
            "requested_path": relative(path),
            "retained_path": relative(path),
            "exists": True,
            "gzip_appended": False,
            "multipart": False,
            "part_index": 1,
            "part_count": 1,
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
            "complete_retained_sha256": sha256(path),
            "reconstruction": "none",
        })
    write_csv(p["artifacts"], rows)


def expected_policy_outcome(data: Mapping[str, Any]) -> tuple[str, bool]:
    """Mirror the production Round-21 policy order for observational auditing."""
    status = integer(data.get("native_mip_status_code"), 0)
    status_consistent = truth(data.get("native_mip_status_code_text_consistent"))
    gap_parameters_valid = truth(data.get("native_mip_strict_gap_parameters_valid"))
    finalized = truth(data.get("native_mip_solver_finalization_reached"))
    lifecycle = truth(data.get("native_mip_lifecycle_valid"))
    bound_valid = (
        integer(data.get("native_mip_best_bound_return_code")) == 0 and
        truth(data.get("native_mip_best_bound_available")) and
        math.isfinite(number(data.get("native_mip_best_bound"))) and
        abs(number(data.get("native_mip_best_bound"))) < 1e20
    )
    objective_valid = (
        integer(data.get("native_mip_objective_return_code")) == 0 and
        truth(data.get("native_mip_objective_available")) and
        math.isfinite(number(data.get("native_mip_objective"))) and
        abs(number(data.get("native_mip_objective"))) < 1e20
    )
    cplex_gap_valid = (
        integer(data.get("native_mip_cplex_relative_gap_return_code")) == 0 and
        truth(data.get("native_mip_cplex_relative_gap_available")) and
        math.isfinite(number(data.get("native_mip_cplex_relative_gap"))) and
        0.0 <= number(data.get("native_mip_cplex_relative_gap")) < 1e20
    )
    verified_available = (
        truth(data.get("verified_incumbent_objective_available")) and
        math.isfinite(number(data.get("verified_incumbent_objective"))) and
        abs(number(data.get("verified_incumbent_objective"))) < 1e20
    )
    verifier_passed = (
        truth(data.get("verified_incumbent_original_problem_feasible")) and
        truth(data.get("verified_incumbent_objective_consistent"))
    )
    if not status_consistent or not gap_parameters_valid or not finalized or not lifecycle:
        return "certificate_rejected", False
    if status == 103:
        return "infeasible", False
    if status == 115:
        return "certificate_rejected", False
    if not bound_valid:
        return "invalid_or_unavailable_bound", False
    if status == 101 and not cplex_gap_valid:
        return "certificate_rejected", False
    # Production Round 21 deliberately has no enabled independent equality or
    # objective-lattice proof module.
    if status == 101:
        if verifier_passed and objective_valid and verified_available:
            objective = number(data.get("native_mip_objective"))
            bound = number(data.get("native_mip_best_bound"))
            verified = number(data.get("verified_incumbent_objective"))
            if (
                number(data.get("native_mip_cplex_relative_gap")) == 0.0 and
                objective - bound == 0.0 and bound <= objective and
                verified - bound == 0.0 and bound <= verified
            ):
                return "native_exact_optimal", True
        return "certificate_rejected", False
    if status == 102:
        return "native_tolerance_optimal_only", False
    if status in (107, 108):
        return "time_limit_valid_bound", False
    return "invalid_or_unavailable_bound", False


def validation_errors(data: Mapping[str, Any], spec: RunSpec, command: Mapping[str, Any], executable_hash: str) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, label: str) -> None:
        if not condition:
            errors.append(label)

    require(bool(data), "missing_or_unreadable_result_json")
    if not data:
        return errors
    require(truth(data.get("fresh_run")), "not_stamped_fresh_round21")
    require(data.get("source_round") == ROUND, "source_round_mismatch")
    require(data.get("round21_run_id") == spec.run_id, "run_id_mismatch")
    require(data.get("round21_executable_sha256") == executable_hash, "result_executable_hash_mismatch")
    require(command.get("executable_sha256") == executable_hash, "command_executable_hash_mismatch")
    require(command.get("command_signature") == data.get("round21_command_signature"), "command_signature_mismatch")
    require(integer(command.get("return_code"), -1) == 0, "process_return_code_nonzero")
    require(not truth(command.get("runner_timeout")), "runner_emergency_timeout")
    require(not command.get("engineering_blocker"), "engineering_blocker")

    require(integer(data.get("native_mip_relative_gap_param_id")) == REL_GAP_PARAM_ID, "relative_gap_parameter_id")
    require(number(data.get("native_mip_relative_gap_requested")) == 0.0, "relative_gap_not_requested_zero")
    require(integer(data.get("native_mip_relative_gap_set_return_code")) == 0, "relative_gap_set_failed")
    require(integer(data.get("native_mip_relative_gap_get_return_code")) == 0, "relative_gap_readback_failed")
    require(truth(data.get("native_mip_relative_gap_effective_available")), "relative_gap_readback_unavailable")
    require(number(data.get("native_mip_relative_gap_effective")) == 0.0, "relative_gap_effective_nonzero")
    require(integer(data.get("native_mip_absolute_gap_param_id")) == ABS_GAP_PARAM_ID, "absolute_gap_parameter_id")
    require(number(data.get("native_mip_absolute_gap_requested")) == 0.0, "absolute_gap_not_requested_zero")
    require(integer(data.get("native_mip_absolute_gap_set_return_code")) == 0, "absolute_gap_set_failed")
    require(integer(data.get("native_mip_absolute_gap_get_return_code")) == 0, "absolute_gap_readback_failed")
    require(truth(data.get("native_mip_absolute_gap_effective_available")), "absolute_gap_readback_unavailable")
    require(number(data.get("native_mip_absolute_gap_effective")) == 0.0, "absolute_gap_effective_nonzero")
    require(truth(data.get("native_mip_strict_gap_parameters_valid")), "strict_gap_parameter_roundtrip_invalid")

    require(integer(data.get("native_mipopt_return_code")) == 0, "CPXmipopt_return_code_nonzero")
    require(truth(data.get("native_mip_evidence_available")), "native_evidence_unavailable")
    require(truth(data.get("native_mip_status_code_text_consistent")), "native_status_code_text_inconsistent")
    require(truth(data.get("native_mip_solver_finalization_reached")), "native_solver_finalization_missing")
    require(truth(data.get("native_mip_evidence_capture_complete")), "native_evidence_capture_incomplete")
    require(truth(data.get("native_mip_lifecycle_valid")), "native_lifecycle_invalid")
    require(truth(data.get("native_mip_problem_freed")), "native_problem_not_freed")
    require(integer(data.get("native_mip_freeprob_return_code")) == 0, "CPXfreeprob_failed")
    require(truth(data.get("native_mip_environment_closed")), "native_environment_not_closed")
    require(integer(data.get("native_mip_close_return_code")) == 0, "CPXcloseCPLEX_failed")
    for field in (
        "native_mip_environment_count", "native_mip_problem_count",
        "native_mip_model_read_count", "native_mip_mipopt_count",
        "native_mip_freeprob_count", "native_mip_close_count",
    ):
        require(integer(data.get(field)) == 1, f"{field}_not_one")

    require(integer(data.get("native_mip_threads_effective")) == 1, "not_one_thread")
    require(integer(data.get("native_mip_presolve_effective")) == 1, "presolve_not_on")
    require(integer(data.get("native_mip_search_effective")) == 1, "search_not_traditional")
    require(integer(data.get("native_mip_node_select_effective")) == 1, "node_selection_not_best_bound")
    native_time_requested = number(data.get("native_mip_time_limit_requested"))
    native_time_effective = number(data.get("native_mip_time_limit_effective"))
    require(math.isfinite(native_time_requested) and native_time_requested > 0.0,
            "native_time_limit_requested_invalid")
    require(native_time_requested <= native_budget(spec.budget_seconds),
            "native_time_limit_exceeds_reserved_budget")
    require(close_float(native_time_effective, native_time_requested),
            "native_time_limit_readback_mismatch")
    require(number(data.get("round21_finalization_reserve_seconds"), -1) > 0.0, "finalization_reserve_missing")
    require(number(data.get("round21_native_time_limit_seconds"), math.inf) < spec.budget_seconds, "native_limit_not_below_nominal_wall")
    require(number(data.get("final_process_wall_time_seconds"), math.inf) <= spec.budget_seconds + max(2.0, 0.01 * spec.budget_seconds), "nominal_process_wall_overrun")
    require(truth(data.get("process_wall_time_comparable")), "process_wall_not_comparable")

    status = integer(data.get("native_mip_status_code"), 0)
    require(status in (101, 102, 103, 107, 108), "unsupported_or_rejected_native_status")
    observed_finite_bound = (
        truth(data.get("native_mip_best_bound_available")) and
        integer(data.get("native_mip_best_bound_return_code")) == 0 and
        math.isfinite(number(data.get("native_mip_best_bound")))
    )
    bound_required = status in (101, 102, 107, 108)
    bound = number(data.get("native_mip_best_bound"))
    if bound_required:
        require(truth(data.get("native_mip_best_bound_available")), "native_best_bound_unavailable")
        require(integer(data.get("native_mip_best_bound_return_code")) == 0, "CPXgetbestobjval_failed")
        require(math.isfinite(bound), "native_best_bound_nonfinite")
        require(same_float(data.get("lower_bound"), bound), "serialized_lower_bound_not_raw_native_bound")
        require(truth(data.get("strict_serialized_lower_bound_matches_native")), "lower_bound_retention_flag_false")
        require(str(data.get("strict_lower_bound_source")) == "native_CPXgetbestobjval", "strict_lower_bound_source_not_CPXgetbestobjval")
    elif status == 103 and observed_finite_bound:
        require(same_float(data.get("lower_bound"), bound), "infeasible_serialized_lower_bound_not_raw_native")
        require(str(data.get("strict_lower_bound_source")) == "native_CPXgetbestobjval", "infeasible_observed_lower_bound_source_mismatch")
    elif status == 103:
        require(data.get("lower_bound") is None, "infeasible_row_invented_lower_bound")
        require(str(data.get("strict_lower_bound_source")) == "unavailable", "infeasible_lower_bound_source_not_unavailable")

    verified_available = truth(data.get("verified_incumbent_objective_available"))
    if status in (101, 102, 107):
        require(verified_available, "verified_upper_bound_unavailable")
    if verified_available:
        ub = number(data.get("verified_incumbent_objective"))
        require(math.isfinite(ub), "verified_upper_bound_nonfinite")
        require(truth(data.get("verified_incumbent_original_problem_feasible")), "verified_original_solution_infeasible")
        require(same_float(data.get("upper_bound"), ub), "serialized_upper_bound_not_verified_objective")
        expected_abs = max(0.0, ub - bound)
        expected_rel = expected_abs / max(1.0, abs(ub))
        expected_project = (
            expected_abs / abs(ub) if abs(ub) > 1e-12
            else (0.0 if expected_abs == 0.0 else math.inf)
        )
        expected_signed = ub - bound
        require(close_float(data.get("verified_incumbent_absolute_gap"), expected_abs), "verified_absolute_gap_inconsistent")
        require(close_float(data.get("verified_incumbent_relative_gap"), expected_rel), "verified_max1_relative_gap_inconsistent")
        if math.isfinite(expected_project):
            require(close_float(data.get("verified_incumbent_project_relative_gap"), expected_project), "verified_project_gap_inconsistent")
            require(close_float(data.get("gap"), expected_project), "serialized_gap_inconsistent")
        else:
            require(data.get("verified_incumbent_project_relative_gap") is None, "nonfinite_verified_project_gap_not_null")
            require(data.get("gap") is None, "nonfinite_serialized_gap_not_null")
        require(truth(data.get("verified_incumbent_signed_bound_residual_available")), "verified_signed_bound_residual_unavailable")
        require(close_float(data.get("verified_incumbent_signed_bound_residual"), expected_signed), "verified_signed_bound_residual_inconsistent")
        require(truth(data.get("verified_incumbent_bound_inversion")) == (bound > ub), "verified_bound_inversion_inconsistent")
        require(truth(data.get("strict_serialized_gap_consistent")), "serialized_gap_consistency_flag_false")
    elif status in (103, 108):
        require(data.get("upper_bound") is None, "no_incumbent_row_invented_upper_bound")
        require(data.get("gap") is None, "no_incumbent_row_invented_gap")

    native_objective_available = truth(data.get("native_mip_objective_available"))
    if status in (101, 102, 107):
        require(native_objective_available, "native_incumbent_objective_unavailable")
        require(integer(data.get("native_mip_objective_return_code")) == 0, "CPXgetobjval_failed")
    if native_objective_available:
        objective = number(data.get("native_mip_objective"))
        expected_native_abs = max(0.0, objective - bound)
        expected_native_rel = expected_native_abs / max(1.0, abs(objective))
        expected_native_signed = objective - bound
        require(close_float(data.get("native_mip_absolute_gap"), expected_native_abs), "raw_native_absolute_gap_inconsistent")
        require(close_float(data.get("native_mip_relative_gap"), expected_native_rel), "raw_native_project_gap_inconsistent")
        require(truth(data.get("native_mip_signed_bound_residual_available")), "native_signed_bound_residual_unavailable")
        require(close_float(data.get("native_mip_signed_bound_residual"), expected_native_signed), "native_signed_bound_residual_inconsistent")
        require(truth(data.get("native_mip_bound_inversion")) == (bound > objective), "native_bound_inversion_inconsistent")
        expected_cplex = abs(objective - bound) / (1e-10 + abs(objective))
        require(close_float(data.get("native_mip_cplex_relative_gap"), expected_cplex), "native_cplex_denominator_gap_inconsistent")

    certificate_class = str(data.get("strict_certificate_class", ""))
    strict = truth(data.get("strict_certified_original_problem"))
    strict_classes = {
        "native_exact_optimal", "native_bound_equality_closed", "independent_exact_certificate",
    }
    require(strict == (certificate_class in strict_classes), "strict_boolean_class_disagreement")
    expected_class, expected_strict = expected_policy_outcome(data)
    require(certificate_class == expected_class, "certificate_class_disagrees_with_policy")
    require(strict == expected_strict, "strict_boolean_disagrees_with_policy")

    if spec.arm != "plain":
        require(data.get("global_gini_tree_root_connectivity_flow_variant_resolved") == spec.variant, "resolved_flow_variant_mismatch")
        require(truth(data.get("global_gini_tree_root_coverage_valid")), "root_coverage_invalid")
        require(truth(data.get("global_gini_tree_branch_coverage_valid")), "branch_coverage_invalid")
        require(truth(data.get("global_gini_tree_recursive_branching_complete")), "recursive_branching_incomplete")
        require(truth(data.get("global_gini_tree_row_migration_complete")), "row_migration_incomplete")
        require(truth(data.get("global_gini_tree_sibling_isolation_by_construction")), "sibling_isolation_invalid")
        require(truth(data.get("global_gini_tree_global_bound_monotone")), "native_global_bound_not_monotone")
        require(integer(data.get("global_gini_tree_interval_oracle_count"), 0) == 0, "production_auxiliary_interval_solve")
        require(integer(data.get("global_gini_tree_child_process_count"), 0) == 0, "production_child_process")
        require(not truth(data.get("global_gini_tree_callback_abort_used")), "callback_abort_used")
        require(data.get("global_gini_tree_child_estimate_mode") == "parent-copy", "nonflow_child_estimate_changed")
        require(data.get("global_gini_tree_row_attachment_mode") == "full-inherited-pack", "nonflow_row_attachment_changed")
        require(data.get("global_gini_tree_row_timing_mode") == "deferred", "nonflow_row_timing_changed")
        require(not truth(data.get("global_gini_tree_native_mip_start_attempted")), "nonflow_native_mip_start_changed")
    return errors


def validate_result(spec: RunSpec, executable_hash: str) -> tuple[bool, list[str]]:
    p = paths(spec.run_id)
    data = read_json(p["json"])
    command = read_json(p["command"])
    errors = validation_errors(data, spec, command, executable_hash)
    return not errors, errors


def run_one(spec: RunSpec, executable_hash: str) -> dict[str, Any]:
    p = paths(spec.run_id)
    cmd = command_for(spec, p)
    signature = command_signature(spec, cmd, executable_hash)
    existing_command = read_json(p["command"])
    valid, errors = validate_result(spec, executable_hash)
    if valid and existing_command.get("command_signature") == signature:
        existing_command["validation_passed"] = True
        existing_command["validation_errors"] = []
        atomic_json(p["command"], existing_command)
        append_control_artifacts_to_manifest(spec)
        print(f"[{now()}] RESUME-SKIP {spec.run_id}", flush=True)
        return {"run_id": spec.run_id, "skipped": True, "validated": True}

    has_attempt = any(p[key].exists() for key in ("json", "log", "command")) or p["run"].exists()
    if has_attempt:
        archive_attempt(
            spec,
            "archived before fail-closed retry: " + "|".join(errors or ["command_signature_changed"]),
        )
        clear_attempt(spec)
    p["run"].mkdir(parents=True, exist_ok=True)

    before = process_snapshot()
    record: dict[str, Any] = {
        "schema": "round21-command-v1",
        "run_id": spec.run_id,
        "stage": spec.stage,
        "instance": spec.instance,
        "instance_class": INSTANCES[spec.instance]["class"],
        "instance_path": INSTANCES[spec.instance]["path"],
        "instance_sha256": sha256(ROOT / INSTANCES[spec.instance]["path"]),
        "arm": spec.arm,
        "flow_variant": spec.variant,
        "nominal_process_wall_seconds": spec.budget_seconds,
        "native_time_limit_seconds": native_budget(spec.budget_seconds),
        "finalization_reserve_seconds": native_reserve(spec.budget_seconds),
        "command": cmd,
        "command_line": subprocess.list2cmdline(cmd),
        "command_signature": signature,
        "executable": relative(EXE),
        "executable_sha256": executable_hash,
        "git_head": git_head(),
        "start_time": now(),
        "pre_process_snapshot": before,
        "stale_process_detected": bool(before["exactebrp_count"] or before["external_cplex_count"]),
    }
    if record["stale_process_detected"]:
        record.update({
            "return_code": -99,
            "end_time": now(),
            "engineering_blocker": "stale_solver_process_detected_before_serial_run",
        })
        atomic_json(p["command"], record)
        print(f"[{now()}] BLOCKED {spec.run_id}: stale solver process", flush=True)
        return record

    atomic_json(p["command"], record)
    print(f"[{now()}] START {spec.run_id}", flush=True)
    started = time.perf_counter()
    timed_out = False
    try:
        completed = subprocess.run(
            cmd, cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=spec.budget_seconds + EMERGENCY_CLEANUP_TOLERANCE_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        timed_out = True
        completed = subprocess.CompletedProcess(
            cmd, -98,
            error.stdout if isinstance(error.stdout, str) else "",
            error.stderr if isinstance(error.stderr, str) else "",
        )
    wall = time.perf_counter() - started
    append_runner_output(p["log"], completed.stdout, completed.stderr)

    record.update({
        "end_time": now(),
        "actual_process_wall_seconds": wall,
        "return_code": completed.returncode,
        "runner_timeout": timed_out,
        "post_process_snapshot": process_snapshot(),
        "engineering_blocker": "runner_emergency_timeout" if timed_out else "",
    })
    atomic_json(p["command"], record)

    if p["json"].exists():
        shutil.copy2(p["json"], p["pristine"])
        stamp_result(p["json"], spec, executable_hash, signature)
    build_checkpoint_file(spec)
    retain_artifacts(spec)
    valid, errors = validate_result(spec, executable_hash)
    record["validation_passed"] = valid
    record["validation_errors"] = errors
    atomic_json(p["command"], record)
    append_control_artifacts_to_manifest(spec)
    if timed_out:
        archive_attempt(spec, "runner emergency timeout; active attempt retained for visibility")
    print(
        f"[{now()}] END {spec.run_id} rc={completed.returncode} "
        f"wall={wall:.3f}s validation={'PASS' if valid else 'FAIL'}",
        flush=True,
    )
    return record


def run_command_test(name: str, command: Sequence[str], executable_hash: str) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            list(command), cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300,
        )
        timeout = False
    except subprocess.TimeoutExpired as error:
        completed = subprocess.CompletedProcess(
            list(command), -98,
            error.stdout if isinstance(error.stdout, str) else "",
            error.stderr if isinstance(error.stderr, str) else "",
        )
        timeout = True
    log = MECHANICAL / f"{name}.log"
    atomic_text(log, (completed.stdout or "") + (completed.stderr or ""))
    return {
        "test": name,
        "status": "PASS" if completed.returncode == 0 and not timeout else "FAIL",
        "return_code": completed.returncode,
        "timeout": timeout,
        "wall_seconds": time.perf_counter() - started,
        "command_line": subprocess.list2cmdline(list(command)),
        "log": relative(log),
        "executable_sha256": executable_hash,
    }


def run_stage0_mechanical(executable_hash: str) -> None:
    record_path = MECHANICAL / "stage0_tests.json"
    old = read_json(record_path)
    if old.get("executable_sha256") == executable_hash and truth(old.get("all_passed")):
        print(f"[{now()}] RESUME-SKIP stage0 mechanical tests", flush=True)
        return
    tests: list[tuple[str, list[str]]] = []
    for filename in UNIT_EXECUTABLES:
        target = TEST_BIN_DIR / filename
        tests.append((Path(filename).stem, [str(target)]))
    tests.extend([
        (
            "round20_regression_tests",
            [sys.executable, str(ROOT / "tests" / "round20_regression_tests.py")],
        ),
        (
            "round21_static_exactness_audit",
            [sys.executable, str(ROOT / "scripts" / "round21_static_exactness_audit.py")],
        ),
        (
            "round21_historical_certificate_audit",
            [sys.executable, str(ROOT / "scripts" / "round21_historical_certificate_audit.py")],
        ),
    ])
    rows: list[dict[str, Any]] = []
    for name, command in tests:
        if not Path(command[0]).exists() and command[0].lower().endswith(".exe"):
            rows.append({
                "test": name, "status": "FAIL", "return_code": -97,
                "timeout": False, "wall_seconds": 0,
                "command_line": subprocess.list2cmdline(command),
                "log": "", "executable_sha256": executable_hash,
                "reason": "missing_test_executable",
            })
        else:
            rows.append(run_command_test(name, command, executable_hash))
    write_csv(MECHANICAL / "stage0_tests.csv", rows)
    payload = {
        "schema": "round21-stage0-mechanical-v1",
        "generated_at": now(),
        "executable_sha256": executable_hash,
        "all_passed": all(row["status"] == "PASS" for row in rows),
        "tests": rows,
    }
    atomic_json(record_path, payload)
    if not payload["all_passed"]:
        failed = [row["test"] for row in rows if row["status"] != "PASS"]
        raise RuntimeError("Stage 0 mechanical tests failed: " + "|".join(failed))


def stage_complete(stage: str, selected: str, executable_hash: str) -> tuple[bool, list[str]]:
    missing: list[str] = []
    if stage == "stage0":
        mechanical = read_json(MECHANICAL / "stage0_tests.json")
        if mechanical.get("executable_sha256") != executable_hash or not truth(mechanical.get("all_passed")):
            missing.append("stage0_mechanical_tests")
        toy_audit = read_csv(MECHANICAL / "toy_original_optimum_comparison.csv")
        if len(toy_audit) != len(STAGE1_ARMS) or any(row.get("status") != "PASS" for row in toy_audit):
            missing.append("stage0_toy_original_optimum_comparison")
    for spec in stage_specs(stage, selected):
        valid, _ = validate_result(spec, executable_hash)
        if not valid:
            missing.append(spec.run_id)
    return not missing, missing


def audit_stage0_toy(executable_hash: str) -> None:
    rows: list[dict[str, Any]] = []
    objectives: list[float] = []
    retained: list[tuple[RunSpec, dict[str, Any], bool, list[str]]] = []
    for arm in STAGE1_ARMS:
        spec = RunSpec("stage0", STAGE0_TOY, arm, 30)
        data = read_json(paths(spec.run_id)["json"])
        valid, errors = validate_result(spec, executable_hash)
        objective = number(data.get("verified_incumbent_objective"))
        if math.isfinite(objective):
            objectives.append(objective)
        retained.append((spec, data, valid, errors))
    reference = objectives[0] if objectives else math.nan
    for spec, data, valid, errors in retained:
        objective = number(data.get("verified_incumbent_objective"))
        same_optimum = math.isfinite(reference) and same_float(objective, reference)
        strict = truth(data.get("strict_certified_original_problem"))
        passed = valid and strict and same_optimum
        rows.append({
            "run_id": spec.run_id,
            "arm": spec.arm,
            "flow_variant": spec.variant,
            "validation_passed": valid,
            "native_status_code": data.get("native_mip_status_code", ""),
            "strict_certificate_class": data.get("strict_certificate_class", ""),
            "strict_certified_original_problem": strict,
            "verified_original_objective": data.get("verified_incumbent_objective", ""),
            "reference_verified_original_objective": reference if math.isfinite(reference) else "",
            "objective_exactly_equal": same_optimum,
            "status": "PASS" if passed else "FAIL",
            "failure_reason": "|".join(
                errors +
                ([] if strict else ["toy_not_strictly_certified"]) +
                ([] if same_optimum else ["toy_original_optimum_changed"])
            ),
        })
    write_csv(MECHANICAL / "toy_original_optimum_comparison.csv", rows)
    if any(row["status"] != "PASS" for row in rows):
        raise RuntimeError("Stage 0 exact toy optimum comparison failed")


def require_prerequisite(stage: str, selected: str, executable_hash: str) -> None:
    prior = {"stage1": "stage0", "stage2": "stage1", "stage3": "stage2"}.get(stage)
    if prior:
        complete, missing = stage_complete(prior, selected, executable_hash)
        if not complete:
            raise RuntimeError(f"{stage} is fail-closed until {prior} completes: " + "|".join(missing))


def read_log(run_id: str) -> str:
    path = paths(run_id)["log"]
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    compressed = Path(str(path) + ".gz")
    if compressed.exists():
        with gzip.open(compressed, "rt", encoding="utf-8", errors="replace") as stream:
            return stream.read()
    parts = sorted(path.parent.glob(path.name + ".gz.part[0-9][0-9][0-9]"))
    if parts:
        joined = tempfile.SpooledTemporaryFile(max_size=32 * 1024 * 1024)
        for part in parts:
            with part.open("rb") as stream:
                shutil.copyfileobj(stream, joined)
        joined.seek(0)
        binary = gzip.GzipFile(fileobj=joined, mode="rb")
        with io.TextIOWrapper(binary, encoding="utf-8", errors="replace") as stream:
            return stream.read()
    return ""


def log_metrics(text: str) -> dict[str, Any]:
    reduced = re.findall(
        r"Reduced MIP has\s+(\d+) rows,\s+(\d+) columns, and\s+(\d+) nonzeros", text,
    )
    eliminated = re.findall(r"MIP Presolve eliminated\s+(\d+) rows and\s+(\d+) columns", text)
    root_times = re.findall(r"Root relaxation solution time\s*=\s*([0-9.eE+-]+) sec", text)
    elapsed = [number(value) for value in re.findall(r"Elapsed time\s*=\s*([0-9.eE+-]+) sec", text)]
    memories = [number(value) for value in re.findall(r"tree\s*=\s*([0-9.eE+-]+) MB", text)]
    root_objectives: list[float] = []
    for line in text.splitlines():
        match = re.match(r"^\s*0\s+\d+\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)", line)
        if match:
            root_objectives.append(number(match.group(1)))
    return {
        "root_uncut_relaxation": root_objectives[0] if root_objectives else "",
        "post_root_cut_relaxation": root_objectives[-1] if root_objectives else "",
        "root_lp_time_seconds": number(root_times[-1]) if root_times else "",
        "root_completion_elapsed_seconds": elapsed[0] if elapsed else "",
        "maximum_tree_memory_mb": max(memories) if memories else "",
        "reduced_model_rows": integer(reduced[-1][0]) if reduced else "",
        "reduced_model_columns": integer(reduced[-1][1]) if reduced else "",
        "reduced_model_nonzeros": integer(reduced[-1][2]) if reduced else "",
        "presolve_eliminated_rows_total": sum(integer(row) for row, _ in eliminated),
        "presolve_eliminated_columns_total": sum(integer(col) for _, col in eliminated),
    }


def trace_points(spec: RunSpec, data: Mapping[str, Any]) -> list[dict[str, Any]]:
    p = paths(spec.run_id)
    points: list[dict[str, Any]] = []
    for row in read_csv(p["bound"]):
        elapsed = number(row.get("elapsed_time"))
        lb = number(row.get("native_global_LB"))
        incumbent = number(row.get("native_incumbent"))
        cutoff = number(row.get("verified_cutoff"))
        ub = cutoff if math.isfinite(cutoff) and cutoff < 1e50 else incumbent
        if not (math.isfinite(elapsed) and math.isfinite(lb)):
            continue
        gap = math.nan
        if math.isfinite(ub) and ub < 1e50:
            gap = max(0.0, ub - lb) / max(1.0, abs(ub))
        points.append({
            "elapsed_seconds": elapsed,
            "lower_bound": lb,
            "upper_bound": ub if math.isfinite(ub) and ub < 1e50 else math.nan,
            "gap": gap,
            "nodes": integer(row.get("node_count"), 0),
            "open_nodes": integer(row.get("open_nodes"), 0),
            "simplex_iterations": integer(row.get("simplex_iterations"), 0),
            "event_source": row.get("event_source", "bound_trace"),
            "observation_source": "global_bound_trajectory",
        })
    # A solver-final observation is always appended from validated full-precision
    # JSON.  This does not invent an earlier checkpoint for plain CPLEX.
    runtime = number(data.get("actual_runtime_seconds"), number(data.get("runtime_seconds")))
    lb = number(data.get("native_mip_best_bound"))
    ub = number(data.get("verified_incumbent_objective"))
    if math.isfinite(runtime) and math.isfinite(lb):
        gap = max(0.0, ub - lb) / max(1.0, abs(ub)) if math.isfinite(ub) else math.nan
        points.append({
            "elapsed_seconds": runtime,
            "lower_bound": lb,
            "upper_bound": ub,
            "gap": gap,
            "nodes": integer(data.get("native_mip_node_count"), 0),
            "open_nodes": integer(data.get("native_mip_open_node_count"), 0),
            "simplex_iterations": integer(data.get("global_gini_tree_native_simplex_iterations"), 0),
            "event_source": "solver_final",
            "observation_source": "full_precision_final_json",
        })
    points.sort(key=lambda row: (number(row["elapsed_seconds"]), row["event_source"] != "solver_final"))
    return points


def build_checkpoint_file(spec: RunSpec) -> None:
    data = read_json(paths(spec.run_id)["json"])
    if not data:
        return
    points = trace_points(spec, data)
    rows: list[dict[str, Any]] = []
    for checkpoint in CHECKPOINTS[spec.stage]:
        eligible = [point for point in points if number(point["elapsed_seconds"]) <= checkpoint + 1e-6]
        # The solver-final row within its reserved margin represents the nominal
        # final checkpoint, but is never backfilled into earlier checkpoints.
        if checkpoint == spec.budget_seconds and points:
            eligible = points
        if not eligible:
            rows.append({
                "run_id": spec.run_id, "instance": spec.instance, "arm": spec.arm,
                "flow_variant": spec.variant, "checkpoint_seconds": checkpoint,
                "status": "not_observed", "not_observed_reason": (
                    "plain_cplex_has_solver_final_observation_only"
                    if spec.arm == "plain" else "no_native_trace_observation_by_checkpoint"
                ),
            })
            continue
        point = eligible[-1]
        rows.append({
            "run_id": spec.run_id,
            "instance": spec.instance,
            "arm": spec.arm,
            "flow_variant": spec.variant,
            "checkpoint_seconds": checkpoint,
            "status": "observed",
            "observation_elapsed_seconds": point["elapsed_seconds"],
            "lower_bound": point["lower_bound"],
            "upper_bound": point["upper_bound"],
            "gap": point["gap"],
            "nodes": point["nodes"],
            "open_nodes": point["open_nodes"],
            "simplex_iterations": point["simplex_iterations"],
            "event_source": point["event_source"],
            "observation_source": point["observation_source"],
            "not_observed_reason": "",
        })
    write_csv(paths(spec.run_id)["checkpoints"], rows)


def lb_improvement_times(points: Sequence[Mapping[str, Any]]) -> tuple[Any, Any]:
    best = -math.inf
    improvements: list[float] = []
    for point in points:
        lb = number(point.get("lower_bound"))
        if not math.isfinite(lb):
            continue
        tolerance = 16 * math.ulp(max(1.0, abs(lb), abs(best) if math.isfinite(best) else 1.0))
        if lb > best + tolerance:
            improvements.append(number(point.get("elapsed_seconds")))
            best = lb
    return (improvements[0], improvements[-1]) if improvements else ("", "")


def max_sibling_delay(spec: RunSpec) -> Any:
    values = [number(row.get("delay_seconds")) for row in read_csv(paths(spec.run_id)["sibling"])]
    finite = [value for value in values if math.isfinite(value)]
    return max(finite) if finite else ""


def summary_row(spec: RunSpec, data: Mapping[str, Any]) -> dict[str, Any]:
    metrics = log_metrics(read_log(spec.run_id))
    points = trace_points(spec, data)
    first_lb, last_lb = lb_improvement_times(points)
    nodes = integer(data.get("native_mip_node_count"), integer(data.get("nodes"), 0))
    iterations = integer(data.get("global_gini_tree_native_simplex_iterations"), 0)
    runtime = number(data.get("actual_runtime_seconds"), number(data.get("runtime_seconds")))
    requested_bound_path = paths(spec.run_id)["bound"]
    retained_bound_path: Path | None = None
    if requested_bound_path.exists():
        retained_bound_path = requested_bound_path
    elif Path(str(requested_bound_path) + ".gz").exists():
        retained_bound_path = Path(str(requested_bound_path) + ".gz")
    else:
        bound_parts = sorted(
            requested_bound_path.parent.glob(
                requested_bound_path.name + ".gz.part[0-9][0-9][0-9]"
            )
        )
        if bound_parts:
            retained_bound_path = bound_parts[0]
    row: dict[str, Any] = {
        "run_id": spec.run_id,
        "stage": spec.stage,
        "instance": spec.instance,
        "instance_class": INSTANCES[spec.instance]["class"],
        "arm": spec.arm,
        "flow_variant": spec.variant,
        "nominal_process_wall_seconds": spec.budget_seconds,
        "native_time_limit_seconds": data.get("round21_native_time_limit_seconds", ""),
        "finalization_reserve_seconds": data.get("round21_finalization_reserve_seconds", ""),
        "actual_runtime_seconds": runtime,
        "final_process_wall_time_seconds": data.get("final_process_wall_time_seconds", ""),
        "solver_status": data.get("status", ""),
        "native_status_code": data.get("native_mip_status_code", ""),
        "native_status_text": data.get("native_mip_status_text", ""),
        "strict_certificate_class": data.get("strict_certificate_class", ""),
        "strict_certified_original_problem": data.get("strict_certified_original_problem", False),
        "strict_rejection_reason": data.get("strict_certificate_rejection_reason", ""),
        "native_objective": data.get("native_mip_objective", ""),
        "native_best_bound": data.get("native_mip_best_bound", ""),
        "verified_incumbent_objective": data.get("verified_incumbent_objective", ""),
        "serialized_lower_bound": data.get("lower_bound", ""),
        "serialized_upper_bound": data.get("upper_bound", ""),
        "serialized_gap": data.get("gap", ""),
        "native_absolute_gap": data.get("native_mip_absolute_gap", ""),
        "native_signed_bound_residual": data.get("native_mip_signed_bound_residual", ""),
        "native_bound_inversion": data.get("native_mip_bound_inversion", ""),
        "native_project_relative_gap": data.get("native_mip_relative_gap", ""),
        "native_cplex_relative_gap": data.get("native_mip_cplex_relative_gap", ""),
        "verified_absolute_gap": data.get("verified_incumbent_absolute_gap", ""),
        "verified_signed_bound_residual": data.get("verified_incumbent_signed_bound_residual", ""),
        "verified_bound_inversion": data.get("verified_incumbent_bound_inversion", ""),
        "verified_project_relative_gap": data.get("verified_incumbent_project_relative_gap", ""),
        "nodes_processed": nodes,
        "open_nodes": data.get("native_mip_open_node_count", data.get("open_nodes", "")),
        "native_solution_count": data.get("native_mip_solution_count", ""),
        "simplex_iterations": iterations,
        "simplex_iterations_per_processed_node": iterations / max(1, nodes),
        "nodes_per_second": nodes / runtime if math.isfinite(runtime) and runtime > 0 else "",
        "time_to_first_gini_branch": data.get("global_gini_tree_first_gini_branch_time", ""),
        "gini_branch_count": data.get("global_gini_tree_gini_branch_nodes", ""),
        "ordinary_branch_count": data.get("global_gini_tree_ordinary_branch_fallbacks", ""),
        "maximum_gini_sibling_delay": max_sibling_delay(spec),
        "native_cut_counts": data.get("global_gini_tree_native_cut_counts", ""),
        "root_model_rows": data.get("global_gini_tree_root_model_rows", ""),
        "root_model_columns": data.get("global_gini_tree_root_model_cols", ""),
        "root_model_nonzeros": data.get("global_gini_tree_root_model_nonzeros", ""),
        "first_valid_lb_improvement_seconds": first_lb,
        "last_valid_lb_improvement_seconds": last_lb,
        "bound_trajectory_path": (
            relative(retained_bound_path) if retained_bound_path is not None else ""
        ),
        "executable_sha256": data.get("round21_executable_sha256", ""),
    }
    row.update(metrics)
    root_time = number(row.get("root_completion_elapsed_seconds"))
    row["branch_and_cut_time_seconds"] = max(0.0, runtime - root_time) if math.isfinite(runtime) and math.isfinite(root_time) else ""
    return row


def all_specs() -> Iterator[RunSpec]:
    # Discover from stamped JSON rather than presuming a selected variant.
    for path in sorted(RAW.glob("*.json")):
        data = read_json(path)
        stage = str(data.get("round21_stage", ""))
        instance = str(data.get("round21_instance", ""))
        arm = str(data.get("round21_arm", ""))
        budget = integer(data.get("round21_nominal_process_wall_seconds"), 0)
        if stage in CHECKPOINTS and instance in INSTANCES and (arm in FLOW_VARIANTS or arm == "plain") and budget > 0:
            yield RunSpec(stage, instance, arm, budget)


def validated_rows(executable_hash: str) -> tuple[list[tuple[RunSpec, dict[str, Any]]], list[dict[str, Any]]]:
    valid_rows: list[tuple[RunSpec, dict[str, Any]]] = []
    audit_rows: list[dict[str, Any]] = []
    for spec in all_specs():
        valid, errors = validate_result(spec, executable_hash)
        data = read_json(paths(spec.run_id)["json"])
        command = read_json(paths(spec.run_id)["command"])
        audit_rows.append({
            "run_id": spec.run_id,
            "stage": spec.stage,
            "instance": spec.instance,
            "arm": spec.arm,
            "status": "PASS" if valid else "FAIL",
            "validation_errors": "|".join(errors),
            "process_return_code": command.get("return_code", ""),
            "runner_timeout": command.get("runner_timeout", ""),
            "native_status_code": data.get("native_mip_status_code", ""),
            "strict_certificate_class": data.get("strict_certificate_class", ""),
            "artifact_manifest": relative(paths(spec.run_id)["artifacts"]),
        })
        if valid:
            valid_rows.append((spec, data))
    return valid_rows, audit_rows


def native_audit_row(spec: RunSpec, data: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "run_id": spec.run_id,
        "stage": spec.stage,
        "instance": spec.instance,
        "arm": spec.arm,
        "flow_variant": spec.variant,
        "native_status_code": data.get("native_mip_status_code", ""),
        "native_status_text": data.get("native_mip_status_text", ""),
        "status_code_text_consistent": data.get("native_mip_status_code_text_consistent", ""),
        "strict_certificate_class": data.get("strict_certificate_class", ""),
        "strict_certified_original_problem": data.get("strict_certified_original_problem", ""),
        "native_objective_return_code": data.get("native_mip_objective_return_code", ""),
        "native_objective_available": data.get("native_mip_objective_available", ""),
        "native_objective": data.get("native_mip_objective", ""),
        "native_best_bound_return_code": data.get("native_mip_best_bound_return_code", ""),
        "native_best_bound_available": data.get("native_mip_best_bound_available", ""),
        "native_best_bound": data.get("native_mip_best_bound", ""),
        "verified_incumbent_objective": data.get("verified_incumbent_objective", ""),
        "native_absolute_gap": data.get("native_mip_absolute_gap", ""),
        "native_signed_bound_residual": data.get("native_mip_signed_bound_residual", ""),
        "native_bound_inversion": data.get("native_mip_bound_inversion", ""),
        "native_project_relative_gap_max1": data.get("native_mip_relative_gap", ""),
        "native_cplex_relative_gap": data.get("native_mip_cplex_relative_gap", ""),
        "verified_absolute_gap": data.get("verified_incumbent_absolute_gap", ""),
        "verified_signed_bound_residual": data.get("verified_incumbent_signed_bound_residual", ""),
        "verified_bound_inversion": data.get("verified_incumbent_bound_inversion", ""),
        "verified_project_relative_gap_max1": data.get("verified_incumbent_project_relative_gap", ""),
        "serialized_lower_bound": data.get("lower_bound", ""),
        "serialized_upper_bound": data.get("upper_bound", ""),
        "serialized_gap": data.get("gap", ""),
        "relative_gap_parameter_id": data.get("native_mip_relative_gap_param_id", ""),
        "relative_gap_requested": data.get("native_mip_relative_gap_requested", ""),
        "relative_gap_set_return_code": data.get("native_mip_relative_gap_set_return_code", ""),
        "relative_gap_get_return_code": data.get("native_mip_relative_gap_get_return_code", ""),
        "relative_gap_effective": data.get("native_mip_relative_gap_effective", ""),
        "absolute_gap_parameter_id": data.get("native_mip_absolute_gap_param_id", ""),
        "absolute_gap_requested": data.get("native_mip_absolute_gap_requested", ""),
        "absolute_gap_set_return_code": data.get("native_mip_absolute_gap_set_return_code", ""),
        "absolute_gap_get_return_code": data.get("native_mip_absolute_gap_get_return_code", ""),
        "absolute_gap_effective": data.get("native_mip_absolute_gap_effective", ""),
        "node_count": data.get("native_mip_node_count", ""),
        "open_node_count": data.get("native_mip_open_node_count", ""),
        "solution_count": data.get("native_mip_solution_count", ""),
        "solver_finalization_reached": data.get("native_mip_solver_finalization_reached", ""),
        "lifecycle_valid": data.get("native_mip_lifecycle_valid", ""),
        "lower_bound_matches_native": data.get("strict_serialized_lower_bound_matches_native", ""),
        "serialized_gap_consistent": data.get("strict_serialized_gap_consistent", ""),
    }


def time_rows(validated: Sequence[tuple[RunSpec, Mapping[str, Any]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    strict_rows: list[dict[str, Any]] = []
    gap_rows: list[dict[str, Any]] = []
    for spec, data in validated:
        points = trace_points(spec, data)
        strict = truth(data.get("strict_certified_original_problem"))
        strict_rows.append({
            "run_id": spec.run_id,
            "stage": spec.stage,
            "instance": spec.instance,
            "arm": spec.arm,
            "flow_variant": spec.variant,
            "strict_certificate_class": data.get("strict_certificate_class", ""),
            "strict_certified": strict,
            "time_to_strict_certificate_seconds": (
                number(data.get("actual_runtime_seconds"), number(data.get("runtime_seconds")))
                if strict else ""
            ),
            "censor_time_seconds": "" if strict else spec.budget_seconds,
            "observation": "observed_at_solver_final" if strict else "right_censored_no_strict_certificate",
        })
        row: dict[str, Any] = {
            "run_id": spec.run_id,
            "stage": spec.stage,
            "instance": spec.instance,
            "arm": spec.arm,
            "flow_variant": spec.variant,
        }
        for threshold in THRESHOLDS:
            label = "gap_0" if threshold == 0 else f"gap_{int(threshold * 100)}pct"
            hit = next(
                (number(point["elapsed_seconds"]) for point in points
                 if math.isfinite(number(point.get("gap"))) and number(point["gap"]) <= threshold),
                None,
            )
            row[f"time_to_{label}_seconds"] = "" if hit is None else hit
            row[f"{label}_observation"] = "not_observed" if hit is None else "observed"
        gap_rows.append(row)
    return strict_rows, gap_rows


def flow_model_row(spec: RunSpec, data: Mapping[str, Any]) -> dict[str, Any]:
    row = summary_row(spec, data)
    return {
        "run_id": spec.run_id,
        "stage": spec.stage,
        "instance": spec.instance,
        "arm": spec.arm,
        "flow_variant": spec.variant,
        "root_model_rows": data.get("global_gini_tree_root_model_rows", ""),
        "root_model_columns": data.get("global_gini_tree_root_model_cols", ""),
        "root_model_nonzeros": data.get("global_gini_tree_root_model_nonzeros", ""),
        "flow_columns": data.get("global_gini_tree_connectivity_flow_columns", ""),
        "flow_upper_link_rows": data.get("global_gini_tree_connectivity_flow_upper_link_rows", ""),
        "flow_lower_link_rows": data.get("global_gini_tree_connectivity_flow_lower_link_rows", ""),
        "flow_station_balance_rows": data.get("global_gini_tree_connectivity_flow_station_balance_rows", ""),
        "flow_depot_balance_rows": data.get("global_gini_tree_connectivity_flow_depot_balance_rows", ""),
        "flow_start_upper_rows": data.get("global_gini_tree_connectivity_flow_start_upper_rows", ""),
        "flow_start_lower_rows": data.get("global_gini_tree_connectivity_flow_start_lower_rows", ""),
        "flow_total_rows": data.get("global_gini_tree_connectivity_flow_total_rows", ""),
        "flow_total_nonzeros": data.get("global_gini_tree_connectivity_flow_total_nonzeros", ""),
        "presolve_eliminated_rows_total": row.get("presolve_eliminated_rows_total", ""),
        "presolve_eliminated_columns_total": row.get("presolve_eliminated_columns_total", ""),
        "reduced_model_rows": row.get("reduced_model_rows", ""),
        "reduced_model_columns": row.get("reduced_model_columns", ""),
        "reduced_model_nonzeros": row.get("reduced_model_nonzeros", ""),
        "root_lp_time_seconds": row.get("root_lp_time_seconds", ""),
        "root_uncut_relaxation": row.get("root_uncut_relaxation", ""),
        "post_root_cut_relaxation": row.get("post_root_cut_relaxation", ""),
        "native_cut_counts": data.get("global_gini_tree_native_cut_counts", ""),
    }


def exactness_rows(validated: Sequence[tuple[RunSpec, Mapping[str, Any]]], validation_audit: Sequence[Mapping[str, Any]], executable_hash: str) -> list[dict[str, Any]]:
    mechanical = read_json(MECHANICAL / "stage0_tests.json")
    static_rows = read_csv(RESULTS / "static_audit" / "checks.csv")
    toy_rows = read_csv(MECHANICAL / "toy_original_optimum_comparison.csv")
    all_data = [data for _, data in validated]
    globals_only = [data for spec, data in validated if spec.arm != "plain"]

    def status(ok: bool, observed: bool = True) -> str:
        return "PASS" if ok else ("FAIL" if observed else "NOT_RUN")

    checks: list[tuple[str, str, bool, bool, str]] = [
        ("CERT001", "Stage 0 deterministic tests all pass",
         mechanical.get("executable_sha256") == executable_hash and truth(mechanical.get("all_passed")), bool(mechanical),
         relative(MECHANICAL / "stage0_tests.csv")),
        ("SRC001", "Round 21 fail-closed static source audit passes",
         bool(static_rows) and all(row.get("status") == "PASS" for row in static_rows), bool(static_rows),
         relative(RESULTS / "static_audit" / "checks.csv")),
        ("RUN001", "every retained active official result validates",
         bool(validation_audit) and all(row.get("status") == "PASS" for row in validation_audit), bool(validation_audit),
         relative(AUDITS / "run_validation_audit.csv")),
        ("CERT002", "relative and absolute zero MIP gaps round-trip in every fresh row",
         bool(all_data) and all(truth(data.get("native_mip_strict_gap_parameters_valid")) for data in all_data), bool(all_data),
         "fresh validated result JSONs"),
        ("CERT003", "raw CPXgetbestobjval is retained as serialized lower_bound",
         bool(all_data) and all(truth(data.get("strict_serialized_lower_bound_matches_native")) for data in all_data), bool(all_data),
         "fresh validated result JSONs"),
        ("CERT004", "serialized full-precision gaps agree with retained bounds",
         bool(all_data) and all(
             truth(data.get("strict_serialized_gap_consistent"))
             for data in all_data if truth(data.get("verified_incumbent_objective_available"))
         ), bool(all_data), "fresh validated result JSONs"),
        ("CERT005", "no tolerance-optimal or time-limit row is labelled strict",
         bool(all_data) and all(
             not truth(data.get("strict_certified_original_problem"))
             for data in all_data if integer(data.get("native_mip_status_code")) in (102, 107, 108)
         ), bool(all_data), "numeric native status and strict class"),
        ("LIFE001", "one environment/problem/read/mipopt/free/close and native finalization",
         bool(all_data) and all(truth(data.get("native_mip_lifecycle_valid")) for data in all_data), bool(all_data),
         "fresh validated result JSONs"),
        ("FAIR001", "all rows use one thread, presolve on, traditional search, best-bound node selection",
         bool(all_data) and all(
             integer(data.get("native_mip_threads_effective")) == 1 and
             integer(data.get("native_mip_presolve_effective")) == 1 and
             integer(data.get("native_mip_search_effective")) == 1 and
             integer(data.get("native_mip_node_select_effective")) == 1
             for data in all_data
         ), bool(all_data), "effective native parameter readbacks"),
        ("TREE001", "global-tree coverage, row migration, sibling isolation, and bound monotonicity pass",
         bool(globals_only) and all(
             truth(data.get("global_gini_tree_root_coverage_valid")) and
             truth(data.get("global_gini_tree_branch_coverage_valid")) and
             truth(data.get("global_gini_tree_row_migration_complete")) and
             truth(data.get("global_gini_tree_sibling_isolation_by_construction")) and
             truth(data.get("global_gini_tree_global_bound_monotone"))
             for data in globals_only
         ), bool(globals_only), "fresh validated global-tree JSONs"),
        ("TREE002", "production global-tree rows perform no auxiliary solve or child process",
         bool(globals_only) and all(
             integer(data.get("global_gini_tree_interval_oracle_count"), 0) == 0 and
             integer(data.get("global_gini_tree_child_process_count"), 0) == 0 and
             integer(data.get("global_gini_tree_mipopt_count"), 0) == 1
             for data in globals_only
         ), bool(globals_only), "fresh validated global-tree JSONs"),
        ("FLOW001", "all requested explicit flow variants resolve exactly",
         bool(globals_only) and all(
             data.get("global_gini_tree_root_connectivity_flow_variant_resolved") == data.get("round21_flow_variant")
             for data in globals_only
         ), bool(globals_only), "requested/resolved variant fields"),
        ("FLOW002", "off/F0/F1/F2/F3 preserve the exact strictly certified toy original optimum",
         len(toy_rows) == len(STAGE1_ARMS) and all(row.get("status") == "PASS" for row in toy_rows),
         bool(toy_rows), relative(MECHANICAL / "toy_original_optimum_comparison.csv")),
    ]
    return [
        {
            "check_id": check_id,
            "status": status(ok, observed),
            "requirement": requirement,
            "evidence": evidence,
        }
        for check_id, requirement, ok, observed, evidence in checks
    ]


def conditional_stage4_specs(selected: str) -> list[RunSpec]:
    frozen = read_json(FROZEN)
    executable_hash = str(frozen.get("sha256", ""))
    if not executable_hash:
        return []
    stage3_ok, _ = stage_complete("stage3", selected, executable_hash)
    exact = read_csv(RESULTS / "exactness_audit.csv")
    exact_ok = bool(exact) and all(row.get("status") == "PASS" for row in exact)
    if not (stage3_ok and exact_ok):
        return []

    specs: list[RunSpec] = []
    # Priority 1 is retained whenever moderate_seed3301 has no strict selected
    # certificate, or when the selected/F0 final gaps differ by less than 20%.
    moderate: dict[str, dict[str, Any]] = {}
    for arm in ("F0", selected, "plain"):
        prior = RunSpec("stage3", "moderate_seed3301", arm, 1800)
        moderate[arm] = read_json(paths(prior.run_id)["json"])
    selected_data = moderate.get(selected, {})
    selected_gap = number(selected_data.get("gap"))
    f0_gap = number(moderate.get("F0", {}).get("gap"))
    ambiguous = (
        not truth(selected_data.get("strict_certified_original_problem")) and
        (not (math.isfinite(selected_gap) and math.isfinite(f0_gap)) or
         abs(selected_gap - f0_gap) <= 0.2 * max(selected_gap, f0_gap, 1e-12))
    )
    near = math.isfinite(selected_gap) and selected_gap <= 0.05
    if ambiguous or near:
        specs.extend(RunSpec("stage4", "moderate_seed3301", arm, 3600) for arm in ("F0", selected, "plain"))

    # Priority 2: V12 rows without a fresh strict Stage-2 certificate.
    for instance in ("V12_M1", "V12_M2"):
        strict_seen = False
        for arm in ("F0", selected, "plain"):
            prior = read_json(paths(RunSpec("stage2", instance, arm, 900).run_id)["json"])
            strict_seen = strict_seen or truth(prior.get("strict_certified_original_problem"))
        if not strict_seen:
            specs.extend(RunSpec("stage4", instance, arm, 3600) for arm in ("F0", selected, "plain"))

    # Priority 3: only the selected high-imbalance arm when already near closure.
    high = read_json(paths(RunSpec("stage3", "high_imbalance_seed3202", selected, 1800).run_id)["json"])
    if not truth(high.get("strict_certified_original_problem")) and number(high.get("gap")) <= 0.01:
        specs.append(RunSpec("stage4", "high_imbalance_seed3202", selected, 3600))
    return specs


def write_selection(selected: str, executable_hash: str) -> None:
    complete, missing = stage_complete("stage1", selected, executable_hash)
    if not complete:
        raise RuntimeError("selection is fail-closed until all 25 Stage 1 rows validate: " + "|".join(missing))
    path = RESULTS / "selection.json"
    existing = read_json(path)
    if existing and existing.get("selected_variant") != selected:
        raise RuntimeError("selection.json already freezes a different Stage-1-only variant")
    if not existing:
        atomic_json(path, {
            "schema": "round21-stage1-selection-v1",
            "selected_variant": selected,
            "selected_solver_option": FLOW_VARIANTS[selected],
            "selected_at": now(),
            "executable_sha256": executable_hash,
            "evidence_scope": "Stage 1 validated 300-second rows only",
            "selection_mechanism": "explicit --selected-variant after inspection of flow_variant_300s_ablation.csv",
            "stage2_or_later_evidence_used": False,
        })


def summarize(executable_hash: str, selected: str, stage4_requested: bool = False) -> None:
    validated, validation_audit = validated_rows(executable_hash)
    write_csv(AUDITS / "run_validation_audit.csv", validation_audit)
    summaries = [summary_row(spec, data) for spec, data in validated]
    write_csv(AUDITS / "all_validated_fresh_runs.csv", summaries)
    write_csv(
        RESULTS / "native_gap_and_status_audit.csv",
        [native_audit_row(spec, data) for spec, data in validated],
    )
    write_csv(
        RESULTS / "flow_variant_300s_ablation.csv",
        [row for row in summaries if row.get("stage") == "stage1"],
    )
    write_csv(
        RESULTS / "matched_900s_comparison.csv",
        [row for row in summaries if row.get("stage") == "stage2"],
    )

    stage3_checkpoints: list[dict[str, Any]] = []
    for spec, _ in validated:
        if spec.stage == "stage3":
            stage3_checkpoints.extend(read_csv(paths(spec.run_id)["checkpoints"]))
    write_csv(RESULTS / "selected_1800s_convergence.csv", stage3_checkpoints)

    stage4_checkpoints: list[dict[str, Any]] = []
    for spec, _ in validated:
        if spec.stage == "stage4":
            stage4_checkpoints.extend(read_csv(paths(spec.run_id)["checkpoints"]))
    if stage4_checkpoints:
        write_csv(RESULTS / "conditional_3600s_convergence.csv", stage4_checkpoints)
    else:
        reason = (
            "stage4_requested_but_exactness_or_trend_gate_did_not_select_any_priority_run"
            if stage4_requested else
            "stage4_not_requested; conditional evidence is intentionally not inferred"
        )
        write_csv(RESULTS / "conditional_3600s_convergence.csv", [{
            "status": "not_run", "not_run_reason": reason,
            "generated_at": now(), "selected_variant": selected,
        }])

    strict_rows, gap_rows = time_rows(validated)
    write_csv(RESULTS / "time_to_strict_certificate.csv", strict_rows)
    write_csv(RESULTS / "time_to_gap_thresholds.csv", gap_rows)
    write_csv(
        RESULTS / "flow_model_size_and_presolve.csv",
        [flow_model_row(spec, data) for spec, data in validated if spec.arm != "plain"],
    )
    exact = exactness_rows(validated, validation_audit, executable_hash)
    write_csv(RESULTS / "exactness_audit.csv", exact)

    artifact_rows: list[dict[str, Any]] = []
    for spec, _ in validated:
        for row in read_csv(paths(spec.run_id)["artifacts"]):
            artifact_rows.append({"run_id": spec.run_id, **row})
    write_csv(AUDITS / "artifact_inventory.csv", artifact_rows)
    atomic_json(AUDITS / "build_and_machine.json", {
        "generated_at": now(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python": sys.version,
        "logical_cpus": os.cpu_count(),
        "git_head": git_head(),
        "executable": relative(EXE),
        "executable_sha256": executable_hash,
        "selected_variant": selected,
        "validated_run_count": len(validated),
        "invalid_active_attempt_count": sum(row.get("status") != "PASS" for row in validation_audit),
        "interrupted_attempt_count": sum(1 for _ in INTERRUPTED.glob("*/attempt_*")),
    })
    size_rows, violations = package_size_audit()
    write_csv(AUDITS / "commit_artifact_size_audit.csv", size_rows)
    if violations:
        raise RuntimeError(
            "Round 21 package contains artifacts above the 90 MiB safe commit limit: "
            + "|".join(violations)
        )


def parse_stages(value: str) -> list[str]:
    allowed = ("stage0", "stage1", "stage2", "stage3", "stage4", "summarize")
    if value.strip().lower() == "all":
        return list(allowed[:-1])
    requested = [item.strip().lower() for item in value.split(",") if item.strip()]
    invalid = [item for item in requested if item not in allowed]
    if invalid or not requested:
        raise ValueError("invalid --stage selection: " + "|".join(invalid or ["empty"]))
    return [stage for stage in allowed if stage in requested]


def dry_run(stages: Sequence[str], selected: str, max_runs: int | None) -> None:
    planned: list[dict[str, Any]] = []
    for stage in stages:
        if stage == "summarize":
            continue
        specs = stage_specs(stage, selected) if stage != "stage4" else [
            RunSpec("stage4", "moderate_seed3301", arm, 3600)
            for arm in ("F0", selected, "plain")
        ]
        for spec in specs:
            p = paths(spec.run_id)
            planned.append({
                "run_id": spec.run_id,
                "stage": spec.stage,
                "instance": spec.instance,
                "arm": spec.arm,
                "flow_variant": spec.variant,
                "nominal_process_wall_seconds": spec.budget_seconds,
                "native_time_limit_seconds": native_budget(spec.budget_seconds),
                "finalization_reserve_seconds": native_reserve(spec.budget_seconds),
                "command_line": subprocess.list2cmdline(command_for(spec, p)),
            })
    if max_runs is not None:
        planned = planned[:max_runs]
    print(json.dumps({
        "dry_run": True,
        "stages": list(stages),
        "selected_variant": selected,
        "planned_solver_runs": len(planned),
        "runs": planned,
    }, indent=2))


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", required=True,
        help="stage0, stage1, stage2, stage3, stage4, summarize, comma list, or all",
    )
    parser.add_argument(
        "--selected-variant", default="F2",
        help="Stage-1-selected exact normalized flow: F1, F2, or F3 (default: F2)",
    )
    parser.add_argument("--max-runs", type=int, default=None, help="stop after this many non-resumed solver launches")
    parser.add_argument("--dry-run", action="store_true", help="print the serial plan without writing artifacts or launching tests/solves")
    args = parser.parse_args(argv)
    if args.max_runs is not None and args.max_runs < 0:
        parser.error("--max-runs must be nonnegative")
    try:
        args.stages = parse_stages(args.stage)
        args.selected_variant = normalize_variant(args.selected_variant)
    except ValueError as error:
        parser.error(str(error))
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.dry_run:
        dry_run(args.stages, args.selected_variant, args.max_runs)
        return 0

    with serial_lock():
        executable_hash = freeze_executable()
        launches = 0
        stage4_requested = "stage4" in args.stages
        for stage in args.stages:
            if stage == "summarize":
                summarize(executable_hash, args.selected_variant, stage4_requested)
                continue
            if stage == "stage0":
                ensure_stage0_toy()
                run_stage0_mechanical(executable_hash)
            else:
                require_prerequisite(stage, args.selected_variant, executable_hash)
            if stage == "stage2":
                write_selection(args.selected_variant, executable_hash)
            if stage == "stage4":
                complete, missing = stage_complete("stage3", args.selected_variant, executable_hash)
                if not complete:
                    raise RuntimeError("Stage 4 is fail-closed until Stage 3 completes: " + "|".join(missing))
                summarize(executable_hash, args.selected_variant, True)

            specs = stage_specs(stage, args.selected_variant)
            for spec in specs:
                valid, _ = validate_result(spec, executable_hash)
                if valid:
                    run_one(spec, executable_hash)
                    continue
                if args.max_runs is not None and launches >= args.max_runs:
                    atomic_json(AUDITS / "run_limit_stop.json", {
                        "stopped_at": now(), "max_runs": args.max_runs,
                        "next_run_id": spec.run_id, "stage": stage,
                    })
                    summarize(executable_hash, args.selected_variant, stage4_requested)
                    print(f"[{now()}] max-runs limit reached before {spec.run_id}", flush=True)
                    return 0
                run_one(spec, executable_hash)
                launches += 1
            if stage == "stage0":
                audit_stage0_toy(executable_hash)
            summarize(executable_hash, args.selected_variant, stage4_requested)
            complete, missing = stage_complete(stage, args.selected_variant, executable_hash)
            if not complete and (stage != "stage4" or specs):
                raise RuntimeError(f"{stage} completed with invalid or missing rows: " + "|".join(missing))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
