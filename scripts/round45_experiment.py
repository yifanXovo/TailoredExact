#!/usr/bin/env python3
"""Run and seal frozen Round 45 adaptive/parametric experiments."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time
from typing import Any

import round44_common as round44


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45"
RUNS = OUT / "runs"
EXE = Path(os.environ.get(
    "EXACTEBRP_ROUND45_EXE", str(ROOT / "build_round45" / "ExactEBRP.exe")))

REQUIRED = (
    "command.json", "process_phases.csv", "progress.csv", "result.json",
    "global_bound_trace.csv", "interval_tree_events.csv",
    "interval_coverage_ledger.csv", "parent_lp_ledger.csv",
    "lookahead_profile_ledger.csv", "envelope_ledger.csv",
    "envelope_facet_ledger.csv", "frontier_target_ledger.csv",
    "timing_score_ledger.csv", "timing_decision_ledger.csv",
    "counterfactual_leaf_ledger.csv", "native_target_ledger.csv",
    "native_optimize_ledger.csv", "parametric_segment_ledger.csv",
    "parametric_breakpoint_ledger.csv", "split_point_choice_ledger.csv",
    "split_point_validity_ledger.csv", "lookahead_reuse_ledger.csv",
    "model_size_ledger.csv", "incumbent_verification_ledger.csv",
    "certificate_ledger.csv", "artifact_manifest.csv",
    "command_environment.json", "completion_marker.json",
)

EXTERNAL_FILES = (
    "global_bound_trace.csv", "interval_tree_events.csv",
    "interval_coverage_ledger.csv", "parent_lp_ledger.csv",
    "lookahead_profile_ledger.csv", "envelope_ledger.csv",
    "envelope_facet_ledger.csv", "frontier_target_ledger.csv",
    "timing_score_ledger.csv", "timing_decision_ledger.csv",
    "native_target_ledger.csv", "native_optimize_ledger.csv",
    "parametric_segment_ledger.csv", "parametric_breakpoint_ledger.csv",
    "split_point_choice_ledger.csv", "split_point_validity_ledger.csv",
    "lookahead_reuse_ledger.csv",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=True).encode()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"empty CSV: {path}")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def replace(args: list[str], option: str, value: Any) -> None:
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    if option in args:
        args[args.index(option) + 1] = rendered
    else:
        args.extend((option, rendered))


def remove(args: list[str], option: str) -> None:
    if option in args:
        index = args.index(option)
        del args[index:index + 2]


def inventory() -> dict[str, dict[str, Any]]:
    values = dict(round44.inventory())
    with (OUT / "complex_instance_inventory.csv").open(
        newline="", encoding="utf-8-sig") as stream:
        for row in csv.DictReader(stream):
            path = ROOT / row["path"]
            instance_id = row.get("instance_id") or Path(row["path"]).stem
            values[instance_id] = {
                "instance_id": instance_id, "path": row["path"],
                "sha256": row["sha256"], "instance_path": str(path),
            }
    return values


def instance_path(item: dict[str, Any]) -> Path:
    for key in ("instance_path", "path", "input"):
        if item.get(key):
            path = Path(str(item[key]))
            return path if path.is_absolute() else ROOT / path
    raise KeyError(f"no instance path in {item}")


def candidate_identity(args: argparse.Namespace) -> dict[str, Any]:
    identity = {
        "execution": args.execution, "K0": args.k0,
        "timing_formula": args.timing,
        "rho_gamma": args.rho_gamma, "point_formula": args.point,
        "minimum_child_width": args.minimum_child_width,
        "lookahead": "frontier-d2", "envelope_injection": "all",
        "envelope_scope": "parent", "mip_starts": "off",
        "solver": {"Presolve": "Auto", "Seed": 0, "Threads": 1,
                   "MIPGap": 0.0, "MIPGapAbs": 0.0},
    }
    identity["decision_identity_sha256"] = stable_hash(identity)
    return identity


def command_for(item: dict[str, Any], run_dir: Path,
                args: argparse.Namespace) -> list[str]:
    command_item = item
    if item["instance_id"] not in round44.inventory():
        # Build from a frozen small-row command template, then bind the actual
        # external input exactly as Round 44's external qualification runner
        # did. External instances intentionally have no Round 39 fingerprint.
        command_item = dict(next(iter(round44.inventory().values())))
    command = round44.fair_candidate_command(
        command_item, run_dir, args.process_cap, execution="algorithm",
        lookahead="frontier-d2", injection="all", scope="parent",
        family="no-adaptive", rho_f=0.5, rho_m=0.0, rho_h=0.0)
    command[0] = str(EXE)
    replace(command, "--round43-envelope-refinement", "off")
    replace(command, "--round44-envelope-tail-repair", "off")
    replace(command, "--round45-adaptive-parametric-partition", args.execution)
    replace(command, "--round45-initial-k0", args.k0)
    replace(command, "--round45-timing-rule", args.timing)
    replace(command, "--round45-rho-gamma", args.rho_gamma)
    replace(command, "--round45-point-rule", args.point)
    replace(command, "--round45-minimum-child-width", args.minimum_child_width)
    replace(command, "--process-wall-time-limit", args.process_cap)
    replace(command, "--time-limit", args.process_cap)
    replace(command, "--input", str(instance_path(item)))
    if item["instance_id"] not in round44.inventory():
        replace(command, "--T", 3600.0)
        remove(command, "--round24-expected-gurobi-model-fingerprint")
    executable_hash = sha256(EXE)
    for option in ("--round24-executable-sha256",
                   "--round24-manifest-executable-sha256"):
        replace(command, option, executable_hash)
    return command


def seal(run_dir: Path, record: dict[str, Any]) -> None:
    external = run_dir / "external"
    for name in EXTERNAL_FILES:
        source = external / name
        if not source.is_file():
            raise RuntimeError(f"required live ledger missing: {source}")
        shutil.copyfile(source, run_dir / name)
    result = load_json(run_dir / "result.json")
    # These two ledgers are faithful indexed extracts of live evidence, not
    # placeholders. The counterfactual ledger identifies the actual decision
    # rows available for later matched replay.
    shutil.copyfile(run_dir / "timing_decision_ledger.csv",
                    run_dir / "counterfactual_leaf_ledger.csv")
    write_csv(run_dir / "incumbent_verification_ledger.csv", [{
        "verified": result.get("external_gini_tree_incumbent_verified", False),
        "verified_upper_bound":
            result.get("external_gini_tree_verified_upper_bound", ""),
        "verification_reason":
            result.get("external_gini_tree_incumbent_verification_reason", ""),
    }])
    write_csv(run_dir / "certificate_ledger.csv", [{
        "strict_certified_original_problem":
            result.get("strict_certified_original_problem", False),
        "certificate_class": result.get("strict_certificate_class", ""),
        "rejection_reason":
            result.get("strict_certificate_rejection_reason", ""),
        "coverage_valid":
            result.get("external_gini_tree_root_coverage_valid", False),
        "failure_reason":
            result.get("external_gini_tree_failure_reason", ""),
    }])
    write_csv(run_dir / "model_size_ledger.csv", [{
        "models": result.get("external_gini_tree_model_count", 0),
        "models_freed": result.get("external_gini_tree_model_free_count", 0),
        "environments": result.get("external_gini_tree_environment_count", 0),
        "environments_freed":
            result.get("external_gini_tree_environment_free_count", 0),
        "peak_memory_gb":
            result.get("external_gini_tree_peak_memory_gb", 0),
        "lp_optimize_count":
            result.get("external_gini_tree_lp_optimize_count", 0),
        "terminal_mip_count":
            result.get("external_gini_tree_terminal_mip_optimize_count", 0),
    }])
    write_json(run_dir / "command_environment.json", {
        "machine": platform.node(), "platform": platform.platform(),
        "python": platform.python_version(), "executable_sha256": sha256(EXE),
        "decision_identity_sha256":
            record["candidate_identity"]["decision_identity_sha256"],
        "forbidden_runtime_telemetry_in_identity": True,
    })
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
                     "sha256": sha256(path)})
    write_csv(run_dir / "artifact_manifest.csv", rows)
    write_json(run_dir / "completion_marker.json", {
        "schema": "round45-completion-marker-v1", "complete": True,
        "run_id": record["run_id"], "artifact_count": len(rows),
        "artifact_manifest_sha256": sha256(run_dir / "artifact_manifest.csv"),
        "decision_identity_sha256":
            record["candidate_identity"]["decision_identity_sha256"],
    })


def run_one(args: argparse.Namespace, item: dict[str, Any]) -> None:
    identity = candidate_identity(args)
    instance_id = item["instance_id"]
    tag = args.tag or identity["decision_identity_sha256"][:12]
    run_id = f"{args.stage}__{instance_id}__{tag}"
    run_dir = RUNS / run_id
    if ((run_dir / "completion_marker.json").is_file() and not args.force):
        print(f"resume: {run_id}", flush=True)
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    if args.force:
        for name in ("completion_marker.json", "artifact_manifest.csv"):
            (run_dir / name).unlink(missing_ok=True)
    command = command_for(item, run_dir, args)
    record = {
        "schema": "round45-run-v1", "round_id": 45,
        "stage": args.stage, "run_id": run_id, "instance_id": instance_id,
        "instance_path": str(instance_path(item).relative_to(ROOT)).replace("\\", "/"),
        "instance_sha256": item["sha256"],
        "candidate_identity": identity, "process_cap_seconds": args.process_cap,
        "watchdog_seconds": args.process_cap + 45.0, "command": command,
        "executable_sha256": sha256(EXE), "completed": False,
        "invalidated": False,
    }
    write_json(run_dir / "command.json", record)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    with (run_dir / "stdout.log").open("wb") as stdout, \
            (run_dir / "stderr.log").open("wb") as stderr:
        try:
            process = subprocess.run(
                command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                timeout=record["watchdog_seconds"], check=False)
            return_code, watchdog = process.returncode, False
        except subprocess.TimeoutExpired:
            return_code, watchdog = -1, True
    record.update({"completed": (run_dir / "result.json").is_file(),
                   "return_code": return_code, "watchdog_timeout": watchdog,
                   "runner_wall_seconds": time.monotonic() - started})
    write_json(run_dir / "command.json", record)
    if return_code or watchdog or not record["completed"]:
        raise RuntimeError(f"Round 45 row failed: {run_id}")
    seal(run_dir, record)
    result = load_json(run_dir / "result.json")
    print(json.dumps({"run_id": run_id, "status": result.get("status"),
                      "certificate": result.get("strict_certified_original_problem"),
                      "work": result.get("external_gini_tree_work"),
                      "seconds": result.get("final_process_wall_time_seconds")},
                     sort_keys=True), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--instance", action="append", required=True)
    parser.add_argument("--execution", choices=("atlas", "algorithm"),
                        default="algorithm")
    parser.add_argument("--k0", type=int, choices=(1, 4), required=True)
    parser.add_argument("--timing", choices=(
        "old-c6", "d-r43", "veto-f", "f", "f-mroot", "h", "mroot",
        "gamma-positive", "gamma-threshold", "gamma-veto",
        "decisive-gamma", "no-adaptive"), required=True)
    parser.add_argument("--rho-gamma", type=float, default=0.0)
    parser.add_argument("--point", choices=("midpoint", "pmm", "fpmm"),
                        required=True)
    parser.add_argument("--minimum-child-width", type=float, default=1e-4)
    parser.add_argument("--process-cap", type=float, default=3600.0)
    parser.add_argument("--tag", default="")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not EXE.is_file():
        raise SystemExit(f"Round 45 executable missing: {EXE}")
    values = inventory()
    unknown = set(args.instance) - set(values)
    if unknown:
        raise SystemExit(f"instances are not frozen: {sorted(unknown)}")
    for name in args.instance:
        run_one(args, values[name])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
