#!/usr/bin/env python3
"""Run frozen Round 44 V12/V20 candidate, P-GRB, and C6 rows."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from typing import Any

import round43_common as round43
import round44_common as common
from run_round44_experiments import seal_run


GROUPS = {
    "additional-v12": common.ADDITIONAL_V12,
    "v20-development": common.V20_DEVELOPMENT,
    "v20-confirmation": common.V20_CONFIRMATION,
}


def remove_option(arguments: list[str], option: str) -> None:
    if option in arguments:
        index = arguments.index(option)
        del arguments[index:index + 2]


def external_item(path_string: str) -> tuple[str, dict[str, Any]]:
    path = common.ROOT / path_string
    if not path.is_file():
        raise RuntimeError(f"frozen external instance missing: {path}")
    instance_id = path.stem
    template = dict(next(iter(common.inventory().values())))
    template.update({
        "instance_id": template["instance_id"],
        "path": path_string,
        "sha256": common.sha256(path),
        "T": 3600.0,
        "lambda": 0.15,
    })
    return instance_id, template


def bind_input(arguments: list[str], item: dict[str, Any]) -> list[str]:
    common.replace_option(
        arguments, "--input", str(common.ROOT / item["path"]))
    common.replace_option(arguments, "--T", item["T"])
    # The external files are frozen by SHA-256, but they are outside the old
    # Round 39 fingerprint table. The backend records the actual canonical
    # model hash; no unrelated small-instance expected fingerprint is used.
    remove_option(arguments, "--round24-expected-gurobi-model-fingerprint")
    return arguments


def command_for(arm: str, item: dict[str, Any], run_dir: Path,
                cap: float, freeze: dict[str, Any]) -> list[str]:
    if arm == "candidate":
        config = freeze["configuration"]
        command = common.fair_candidate_command(
            item, run_dir, cap,
            execution="algorithm", lookahead=config["lookahead"],
            injection=config["injection"], scope=config["scope"],
            family=config["family"], rho_f=config["rho_F"],
            rho_m=config["rho_M"], rho_h=config["rho_H"],
            rank1=config["rank1"], mip_starts=config["mip_starts"],
            consolidation=config["consolidation"])
    elif arm == "pgrb":
        command = round43.fair_pgrb_command(item, run_dir, cap)
        command[0] = str(common.EXE)
        for option in ("--round24-executable-sha256",
                       "--round24-manifest-executable-sha256"):
            common.replace_option(command, option, common.sha256(common.EXE))
    else:
        command = round43.fair_c6_command(
            item, run_dir, cap, execution="algorithm", K0=4, depth=2,
            rho=.05, score="d", envelope="single")
        command[0] = str(common.EXE)
        common.replace_option(command, "--round43-envelope-refinement", "off")
        for option in ("--round24-executable-sha256",
                       "--round24-manifest-executable-sha256"):
            common.replace_option(command, option, common.sha256(common.EXE))
    return bind_input(command, item)


def seal_reference(run_dir: Path) -> None:
    external = run_dir / "external"
    for source_name, target_name in (
            ("global_bound_trace.csv", "global_bound_trace.csv"),
            ("paper_optimize_ledger.csv", "native_optimize_ledger.csv")):
        source = external / source_name
        if source.is_file():
            shutil.copyfile(source, run_dir / target_name)
    rows = []
    for path in sorted(p for p in run_dir.rglob("*") if p.is_file() and
                       p.name not in {"artifact_manifest.csv",
                                      "completion_marker.json"}):
        rows.append({
            "path": path.relative_to(run_dir).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": common.sha256(path),
        })
    common.write_csv(run_dir / "artifact_manifest.csv", rows)
    common.write_json(run_dir / "completion_marker.json", {
        "schema": "round44-external-reference-completion-v1",
        "complete": True,
        "artifact_count": len(rows),
        "artifact_manifest_sha256": common.sha256(
            run_dir / "artifact_manifest.csv"),
    })


def run_one(group: str, path_string: str, arm: str, cap: float,
            freeze: dict[str, Any], force: bool) -> None:
    instance_id, item = external_item(path_string)
    run_id = f"{group}__{instance_id}__{arm}"
    run_dir = common.RUNS / run_id
    result_path = run_dir / "result.json"
    marker = run_dir / "completion_marker.json"
    if result_path.is_file() and marker.is_file() and not force:
        print(f"resume: {run_id}", flush=True)
        return
    run_dir.mkdir(parents=True, exist_ok=True)
    if force:
        for stale in (marker, run_dir / "artifact_manifest.csv"):
            if stale.is_file():
                stale.unlink()
    command = command_for(arm, item, run_dir, cap, freeze)
    record = {
        "schema": "round44-external-qualification-run-v1",
        "round_id": 44,
        "stage": group,
        "run_id": run_id,
        "instance_id": instance_id,
        "instance_path": path_string,
        "instance_sha256": item["sha256"],
        "arm": arm,
        "process_cap_seconds": cap,
        "watchdog_seconds": cap + 60.0,
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
                command, cwd=common.ROOT, env=environment, stdout=stdout,
                stderr=stderr, check=False, timeout=cap + 60.0)
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
        raise RuntimeError(f"external qualification row failed: {run_id}")
    if arm == "candidate":
        seal_run(run_dir, record)
    else:
        seal_reference(run_dir)
    result = common.load_json(result_path)
    print(json.dumps({
        "run_id": run_id,
        "status": result.get("status"),
        "certified": result.get("strict_certified_original_problem"),
        "seconds": result.get("final_process_wall_time_seconds"),
        "work": (result.get("external_gini_tree_work")
                 if arm != "pgrb" else result.get("gurobi_work")),
    }, sort_keys=True), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=tuple(GROUPS), required=True)
    parser.add_argument("--arm", action="append",
                        choices=("candidate", "pgrb", "c6"), required=True)
    parser.add_argument("--process-cap", type=float, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    freeze_path = common.OUT / "final_candidate_freeze.json"
    if not freeze_path.is_file():
        raise SystemExit("final candidate must be frozen before external runs")
    freeze = common.load_json(freeze_path)
    if freeze.get("external_results_observed") is not False:
        raise SystemExit("invalid external-results freeze gate")
    if freeze.get("executable_sha256") != common.sha256(common.EXE):
        raise SystemExit("current executable does not match final freeze")
    for path_string in GROUPS[args.group]:
        for arm in args.arm:
            run_one(args.group, path_string, arm, args.process_cap,
                    freeze, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
