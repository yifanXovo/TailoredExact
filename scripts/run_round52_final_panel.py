#!/usr/bin/env python3
"""Run resumable frozen Round 52 K1-AM-FINAL or P-GRB panel rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import time
from pathlib import Path

import round46_common as round46


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_tailored_cut_final_validation_round52"
CAP = 1800.0
TAU = 0.08


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def manifest(panel: str) -> list[dict[str, object]]:
    value = json.loads((OUT / f"{panel}_instance_manifest.json").read_text(
        encoding="utf-8"))
    if value.get("row_count") != 12 or len(value.get("rows", [])) != 12:
        raise RuntimeError(f"invalid frozen {panel} manifest")
    return value["rows"]


def item(row: dict[str, object]) -> dict[str, object]:
    return {
        "instance": row["instance_id"],
        "path": row["input_path"],
        "sha256": row["input_sha256"],
        "T": float(row["T"]), "V": int(row["V"]), "M": int(row["M"]),
    }


def command_for(method: str, row: dict[str, object], run_dir: Path,
                executable: Path) -> list[str]:
    bound = item(row)
    if method == "P-GRB":
        command = round46.pgrb_command(bound, run_dir, CAP, executable)
    else:
        command = round46.c6_command(
            bound, run_dir, CAP, 1, 0.01, executable)
        round46.replace_option(command, "--round47-c6-adaptive-mass",
                               "adaptive-mass")
        round46.replace_option(command, "--round47-c6-adaptive-mass-tau", TAU)
        round46.replace_option(command, "--round48-k1-amf", "off")
        round46.replace_option(command, "--round49-k1-am-rc", "off")
        round46.replace_option(command, "--external-gini-artifact-dir",
                               run_dir / "external")
    round46.replace_option(command, "--T", float(row["T"]))
    round46.replace_option(command, "--process-wall-time-limit", CAP)
    round46.replace_option(command, "--time-limit", CAP - 6.0)
    round46.replace_option(command, "--threads", 1)
    round46.replace_option(command, "--mip-threads", 1)
    round46.replace_option(command, "--gurobi-seed", 0)
    round46.replace_option(command, "--gurobi-presolve", -1)
    return command


def result_value(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def seal(run_dir: Path, record: dict[str, object]) -> None:
    result = result_value(run_dir / "result.json")
    process_seconds = float(result.get("final_process_wall_time_seconds", 0.0))
    if process_seconds > CAP + 1e-6:
        raise RuntimeError(f"internal process cap exceeded: {process_seconds}")
    inventory = []
    for path in sorted(p for p in run_dir.rglob("*") if p.is_file() and
                       p.name not in {"artifact_manifest.csv",
                                      "completion_marker.json"}):
        inventory.append({
            "path": path.relative_to(run_dir).as_posix(),
            "size_bytes": path.stat().st_size, "sha256": sha256(path)})
    with (run_dir / "artifact_manifest.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "path", "size_bytes", "sha256"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(inventory)
    write_json(run_dir / "completion_marker.json", {
        "schema": "round52-final-panel-completion-v1",
        "complete": True, "panel": record["panel"],
        "instance_id": record["instance_id"], "method": record["method"],
        "process_cap_seconds": CAP, "process_seconds": process_seconds,
        "cap_respected": True, "executable_sha256": record["executable_sha256"],
        "artifact_count": len(inventory),
        "artifact_manifest_sha256": sha256(run_dir / "artifact_manifest.csv"),
    })


def run_one(panel: str, method: str, row: dict[str, object],
            executable: Path, force: bool) -> None:
    executable_hash = sha256(executable)
    run_id = f"{panel}__{row['instance_id']}__{method}"
    run_dir = OUT / "local_raw" / "final_panel_runs" / run_id
    marker = run_dir / "completion_marker.json"
    if marker.is_file() and not force:
        prior = json.loads(marker.read_text(encoding="utf-8"))
        if (prior.get("complete") is True and
                prior.get("executable_sha256") == executable_hash and
                prior.get("process_cap_seconds") == CAP):
            print(f"resume: {run_id}", flush=True)
            return
    run_dir.mkdir(parents=True, exist_ok=True)
    marker.unlink(missing_ok=True)
    (run_dir / "artifact_manifest.csv").unlink(missing_ok=True)
    command = command_for(method, row, run_dir, executable)
    record: dict[str, object] = {
        "schema": "round52-final-panel-command-v1", "panel": panel,
        "run_id": run_id, "instance_id": row["instance_id"],
        "input_path": row["input_path"], "input_sha256": row["input_sha256"],
        "V": row["V"], "M": row["M"], "T": row["T"],
        "difficulty_configuration": row["difficulty_configuration"],
        "method": method, "process_cap_seconds": CAP,
        "checkpoints_seconds": [300, 1200, 1800],
        "executable_path": str(executable),
        "executable_sha256": executable_hash, "tau": TAU if method != "P-GRB" else None,
        "controller": "K1-AM-FINAL" if method != "P-GRB" else "not_applicable",
        "solver": {"Presolve": "Auto", "Seed": 0, "Threads": 1,
                   "MIPGap": 0, "MIPGapAbs": 0},
        "command": command, "started": False, "completed": False,
    }
    write_json(run_dir / "command.json", record)
    write_json(run_dir / "command_environment.json", {
        "machine": platform.node(), "platform": platform.platform(),
        "python": platform.python_version(), "executable_sha256": executable_hash,
    })
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    record["started"] = True
    write_json(run_dir / "command.json", record)
    with (run_dir / "stdout.log").open("wb") as stdout, \
            (run_dir / "stderr.log").open("wb") as stderr:
        try:
            process = subprocess.run(
                command, cwd=ROOT, env=environment, stdout=stdout,
                stderr=stderr, timeout=CAP + 45.0, check=False)
            return_code, watchdog = process.returncode, False
        except subprocess.TimeoutExpired:
            return_code, watchdog = -1, True
    record.update({
        "return_code": return_code, "watchdog_timeout": watchdog,
        "runner_wall_seconds": time.monotonic() - started,
        "completed": (run_dir / "result.json").is_file(),
    })
    write_json(run_dir / "command.json", record)
    if return_code != 0 or watchdog or not record["completed"]:
        raise RuntimeError(f"final panel row failed: {run_id}")
    seal(run_dir, record)
    result = result_value(run_dir / "result.json")
    print(json.dumps({
        "run_id": run_id, "status": result.get("status"),
        "certificate": result.get("strict_certified_original_problem"),
        "work": (result.get("gurobi_work") if method == "P-GRB" else
                 result.get("external_gini_tree_work")),
        "seconds": result.get("final_process_wall_time_seconds"),
    }, sort_keys=True), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", choices=("validation", "holdout"), required=True)
    parser.add_argument("--method", choices=("P-GRB", "K1-AM-FINAL"), required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--instances", help="optional comma-separated IDs")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    executable = args.executable.resolve()
    if not executable.is_file():
        raise SystemExit("frozen executable missing")
    if args.panel == "holdout":
        seal_path = OUT / "holdout_seal_audit.json"
        if not seal_path.is_file():
            raise SystemExit("holdout opening forbidden before seal audit")
        seal_value = json.loads(seal_path.read_text(encoding="utf-8"))
        if (seal_value.get("opening_authorized") is not True or
                seal_value.get("executable_sha256") != sha256(executable)):
            raise SystemExit("holdout seal/executable mismatch")
    selected = None if not args.instances else {
        value.strip() for value in args.instances.split(",") if value.strip()}
    all_rows = manifest(args.panel)
    if selected and selected - {str(row["instance_id"]) for row in all_rows}:
        raise SystemExit("requested instance is not frozen")
    for row in all_rows:
        if selected is None or row["instance_id"] in selected:
            run_one(args.panel, args.method, row, executable, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
