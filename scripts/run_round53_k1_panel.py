#!/usr/bin/env python3
"""Run resumable Round 53 K1-v0, K1-candidate, or P-GRB rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import subprocess
import time
from pathlib import Path
from typing import Any

import round46_common as round46


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"
TAU = 0.08
F0 = "interval-mip-core-no-exhaustive-subset-duration"
V0 = "interval-mip-v0"
INTEGRATION_T = {
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363": 2850.0,
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114": 2400.0,
    "round39_small_hard_V10_M3_Q20_slot04_seed1145042375": 2400.0,
    "round39_small_hard_V12_M3_Q20_slot07_seed621538683": 2400.0,
    "round39_small_hard_V12_M2_Q20_slot06_seed258908503": 2400.0,
    "round39_small_easy_V12_M3_Q30_slot08_seed1167625600": 3600.0,
}


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


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def result_value(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def set_option(command: list[str], option: str, value: object) -> None:
    if option in command:
        round46.replace_option(command, option, value)
    else:
        command.extend([option, str(value).lower() if isinstance(value, bool)
                        else str(value)])


def parse_dimensions(identifier: str) -> tuple[int, int]:
    V = re.search(r"_V(\d+)_", identifier + "_")
    M = re.search(r"_M(\d+)_", identifier + "_")
    if not V or not M:
        raise RuntimeError(f"dimensions unavailable: {identifier}")
    return int(V.group(1)), int(M.group(1))


def panel_rows(panel: str) -> list[dict[str, Any]]:
    if panel == "sealed":
        return read_json(OUT / "sealed_v12_instance_manifest.json")["rows"]
    freeze = read_json(OUT / "k1_integration_panel_freeze.json")
    source = (freeze["changed_model_instances"] if panel == "integration"
              else freeze["V20_V50_short_sentinels"])
    rows: list[dict[str, Any]] = []
    for raw in source:
        row = dict(raw)
        V, M = parse_dimensions(str(row["instance_id"]))
        row.update({"V": V, "M": M,
                    "T": (INTEGRATION_T[str(row["instance_id"])]
                          if panel == "integration" else 3600.0),
                    "difficulty_configuration": row.get("role", panel)})
        rows.append(row)
    return rows


def command_for(method: str, row: dict[str, Any], run_dir: Path,
                executable: Path, cap: float) -> list[str]:
    item = {"instance": row["instance_id"], "path": row["input_path"],
            "sha256": row["input_sha256"], "T": float(row["T"]),
            "V": int(row["V"]), "M": int(row["M"])}
    if method == "P-GRB":
        command = round46.pgrb_command(item, run_dir, cap, executable)
    else:
        command = round46.c6_command(item, run_dir, cap, 1, 0.01, executable)
        round46.replace_option(command, "--round47-c6-adaptive-mass",
                               "adaptive-mass")
        round46.replace_option(command, "--round47-c6-adaptive-mass-tau",
                               TAU)
        round46.replace_option(command, "--round48-k1-amf", "off")
        round46.replace_option(command, "--round49-k1-am-rc", "off")
        round46.replace_option(command, "--external-gini-artifact-dir",
                               run_dir / "external")
        set_option(command, "--external-gini-interval-mip-policy",
                   F0 if method == "K1-AM-CANDIDATE" else V0)
    round46.replace_option(command, "--T", float(row["T"]))
    round46.replace_option(command, "--process-wall-time-limit", cap)
    round46.replace_option(command, "--time-limit", max(0.001, cap - 6.0))
    round46.replace_option(command, "--threads", 1)
    round46.replace_option(command, "--mip-threads", 1)
    round46.replace_option(command, "--gurobi-seed", 0)
    round46.replace_option(command, "--gurobi-presolve", -1)
    return command


def opening_gate(panel: str, executable_hash: str) -> None:
    if panel != "sealed":
        return
    opening = OUT / "sealed_v12_opening_audit.json"
    if not opening.is_file():
        raise RuntimeError("sealed panel opening audit is absent")
    value = read_json(opening)
    if (value.get("opening_authorized") is not True or
            value.get("executable_sha256") != executable_hash or
            value.get("source_frozen") is not True or
            value.get("k1_integration_passed") is not True):
        raise RuntimeError("sealed panel opening gate failed")


def seal(run_dir: Path, record: dict[str, object], cap: float) -> None:
    result = result_value(run_dir / "result.json")
    process_seconds = float(result.get("final_process_wall_time_seconds", 0.0))
    if process_seconds > cap + 1e-6:
        raise RuntimeError(f"internal process cap exceeded: {process_seconds}")
    if str(record["method"]).startswith("K1-AM"):
        expected = (F0 if record["method"] == "K1-AM-CANDIDATE" else V0)
        if result.get("external_gini_tree_interval_mip_policy") != expected:
            raise RuntimeError("inner-backend policy roundtrip failed")
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
        "schema": "round53-k1-panel-completion-v1", "complete": True,
        "panel": record["panel"], "instance_id": record["instance_id"],
        "method": record["method"], "process_cap_seconds": cap,
        "process_seconds": process_seconds, "cap_respected": True,
        "executable_sha256": record["executable_sha256"],
        "inner_backend_policy": record["inner_backend_policy"],
        "artifact_count": len(inventory),
        "artifact_manifest_sha256": sha256(
            run_dir / "artifact_manifest.csv")})


def run_one(panel: str, method: str, row: dict[str, Any], executable: Path,
            cap: float, force: bool) -> None:
    executable_hash = sha256(executable)
    run_id = f"{panel}__{row['instance_id']}__{method}__{int(cap)}s"
    run_dir = OUT / "local_raw" / "k1_panel_runs" / run_id
    marker = run_dir / "completion_marker.json"
    if marker.is_file() and not force:
        prior = read_json(marker)
        if (prior.get("complete") is True and
                prior.get("executable_sha256") == executable_hash and
                float(prior.get("process_cap_seconds", -1)) == cap):
            print(f"resume: {run_id}", flush=True)
            return
    if run_dir.exists() and not marker.is_file():
        raise RuntimeError(f"incomplete script-owned run exists: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)
    command = command_for(method, row, run_dir, executable, cap)
    policy = F0 if method == "K1-AM-CANDIDATE" else (
        V0 if method == "K1-AM-v0" else "not_applicable")
    record: dict[str, object] = {
        "schema": "round53-k1-panel-command-v1", "panel": panel,
        "run_id": run_id, "instance_id": row["instance_id"],
        "input_path": row["input_path"], "input_sha256": row["input_sha256"],
        "V": row["V"], "M": row["M"], "T": row["T"],
        "difficulty_configuration": row["difficulty_configuration"],
        "method": method, "inner_backend_policy": policy,
        "process_cap_seconds": cap,
        "checkpoints_seconds": [value for value in (300, 1200, 1800, 3600,
                                                       7200) if value <= cap],
        "executable_path": str(executable),
        "executable_sha256": executable_hash,
        "tau": TAU if method != "P-GRB" else None,
        "K0": 1 if method != "P-GRB" else None,
        "controller": "Round52-frozen-K1-AM" if method != "P-GRB"
                      else "not_applicable",
        "solver": {"Presolve": "Auto", "Seed": 0, "Threads": 1,
                   "MIPGap": 0, "MIPGapAbs": 0},
        "forbidden_dispatch": False, "command": command,
        "started": False, "completed": False}
    write_json(run_dir / "command.json", record)
    write_json(run_dir / "command_environment.json", {
        "machine": platform.node(), "platform": platform.platform(),
        "python": platform.python_version(),
        "executable_sha256": executable_hash})
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
                stderr=stderr, timeout=cap + 45.0, check=False)
            return_code, watchdog = process.returncode, False
        except subprocess.TimeoutExpired:
            return_code, watchdog = -1, True
    record.update({"return_code": return_code,
                   "watchdog_timeout": watchdog,
                   "runner_wall_seconds": time.monotonic() - started,
                   "completed": (run_dir / "result.json").is_file()})
    write_json(run_dir / "command.json", record)
    if return_code != 0 or watchdog or not record["completed"]:
        raise RuntimeError(f"K1 panel row failed: {run_id}")
    seal(run_dir, record, cap)
    result = result_value(run_dir / "result.json")
    print(json.dumps({
        "run_id": run_id, "status": result.get("status"),
        "certificate": result.get("strict_certified_original_problem"),
        "work": (result.get("gurobi_work") if method == "P-GRB" else
                 result.get("external_gini_tree_work")),
        "seconds": result.get("final_process_wall_time_seconds")},
        sort_keys=True), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", choices=("integration", "sentinel", "sealed"),
                        required=True)
    parser.add_argument("--method", choices=(
        "P-GRB", "K1-AM-v0", "K1-AM-CANDIDATE"), required=True)
    parser.add_argument("--cap", type=float, required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--instances")
    parser.add_argument("--extension-authorized", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not 0 < args.cap <= 7200:
        raise RuntimeError("invalid process cap")
    if args.cap > 3600 and not (
            args.panel == "sealed" and args.cap == 7200 and
            args.extension_authorized):
        raise RuntimeError("cap above 3600 requires sealed tight extension")
    executable = args.executable.resolve()
    executable_hash = sha256(executable)
    opening_gate(args.panel, executable_hash)
    selected = None if not args.instances else {
        value.strip() for value in args.instances.split(",") if value.strip()}
    rows = panel_rows(args.panel)
    known = {str(row["instance_id"]) for row in rows}
    if selected and selected - known:
        raise RuntimeError("requested instance is not frozen")
    for row in rows:
        if selected is not None and row["instance_id"] not in selected:
            continue
        if args.cap > 3600 and row.get("extension_eligible") is not True:
            raise RuntimeError("7200-second extension requested on ineligible row")
        run_one(args.panel, args.method, row, executable, args.cap, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
