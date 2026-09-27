#!/usr/bin/env python3
"""Run resumable contemporaneous Round 55 K1 integration pairs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import round46_common as round46


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_am_sf_station_state_chain_round55"
FREEZE = EVIDENCE / "k1_integration_panel_freeze.json"
RUNS = EVIDENCE / "local_raw" / "k1_integration"
ARMS = {
    "K1-AM-SF": {
        "preset": "paper-k1-am-sf",
        "policy": "interval-mip-core-no-exhaustive-subset-duration",
    },
    "K1-AM-SF-CANDIDATE": {
        "preset": "research-k1-am-sf-vdp",
        "policy": "round55-vd-p",
    },
}
T_BY_INSTANCE = {
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


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def dimensions(identifier: str) -> tuple[int, int, int]:
    if identifier in {
            "tight_T_seed3102", "tight_T_seed3101",
            "high_imbalance_seed3201", "high_imbalance_seed3202",
            "moderate_seed3301", "moderate_seed3302"}:
        return 20, 3, 30
    values = []
    for label in ("V", "M", "Q"):
        match = re.search(rf"_{label}(\d+)_", identifier + "_")
        if not match:
            raise RuntimeError(f"{label} unavailable in {identifier}")
        values.append(int(match.group(1)))
    return values[0], values[1], values[2]


def route_limit(identifier: str) -> float:
    if identifier in T_BY_INSTANCE:
        return T_BY_INSTANCE[identifier]
    match = re.search(r"_(2400|3600)_V", identifier)
    if match:
        return float(match.group(1))
    if identifier in {
            "tight_T_seed3102", "tight_T_seed3101",
            "high_imbalance_seed3201", "high_imbalance_seed3202",
            "moderate_seed3301", "moderate_seed3302"}:
        return 3600.0
    raise RuntimeError(f"route-time limit unavailable in freeze for {identifier}")


def panel_rows(selected: set[str] | None) -> list[dict[str, Any]]:
    rows = []
    for raw in read_json(FREEZE)["instances"]:
        if selected is not None and raw["instance_id"] not in selected:
            continue
        row = dict(raw)
        row["V"], row["M"], row["Q"] = dimensions(row["instance_id"])
        row["T"] = route_limit(row["instance_id"])
        rows.append(row)
    if selected is not None and selected != {row["instance_id"] for row in rows}:
        raise RuntimeError("requested instance is not frozen")
    return rows


def command_for(row: dict[str, Any], arm: str, run_dir: Path,
                executable: Path, cap: int) -> list[str]:
    item = {
        "instance": row["instance_id"], "path": row["input_path"],
        "sha256": row["input_sha256"], "T": row["T"],
        "V": row["V"], "M": row["M"],
    }
    command = round46.c6_command(item, run_dir, cap, 1, 0.08, executable)
    round46.replace_option(command, "--algorithm-preset", ARMS[arm]["preset"])
    round46.replace_option(command, "--external-gini-interval-mip-policy",
                           ARMS[arm]["policy"])
    round46.replace_option(command, "--T", row["T"])
    round46.replace_option(command, "--round47-c6-adaptive-mass", "adaptive-mass")
    round46.replace_option(command, "--round47-c6-adaptive-mass-tau", 0.08)
    round46.replace_option(command, "--round48-k1-amf", "off")
    round46.replace_option(command, "--round49-k1-am-rc", "off")
    round46.replace_option(command, "--process-shutdown-margin", 2)
    round46.replace_option(command, "--time-limit", max(1, cap - 6))
    round46.replace_option(command, "--process-wall-time-limit", cap)
    round46.replace_option(command, "--threads", 1)
    round46.replace_option(command, "--mip-threads", 1)
    round46.replace_option(command, "--gurobi-seed", 0)
    round46.replace_option(command, "--gurobi-presolve", -1)
    round46.replace_option(command, "--primal-heuristic-generation-log",
                           run_dir / "hga_generations.csv")
    round46.replace_option(command, "--heuristic-candidates-csv",
                           run_dir / "heuristic_candidates.csv")
    return command


def run_one(row: dict[str, Any], arm: str, executable: Path,
            executable_hash: str, cap: int) -> dict[str, object]:
    run_id = f"{row['instance_id']}__{arm}__{cap}s"
    run_dir = RUNS / run_id
    command_path = run_dir / "command.json"
    result_path = run_dir / "result.json"
    marker_path = run_dir / "completion_marker.json"
    if marker_path.exists() and command_path.exists() and result_path.exists():
        marker = read_json(marker_path)
        if (marker.get("complete") is True and
                marker.get("executable_sha256") == executable_hash and
                marker.get("preset") == ARMS[arm]["preset"] and
                marker.get("inner_policy") == ARMS[arm]["policy"] and
                int(marker.get("cap_seconds", -1)) == cap):
            return {"run_id": run_id, "resumed": True}

    run_dir.mkdir(parents=True, exist_ok=True)
    command = command_for(row, arm, run_dir, executable, cap)
    record = {
        "schema": "round55-k1-integration-command-v1",
        "run_id": run_id, "instance_id": row["instance_id"],
        "role": row["role"], "V": row["V"], "M": row["M"], "Q": row["Q"],
        "T": row["T"], "input_path": row["input_path"],
        "input_sha256": row["input_sha256"], "arm": arm,
        "preset": ARMS[arm]["preset"], "inner_policy": ARMS[arm]["policy"],
        "outer_controller": "paper-k1-am-sf-first-class",
        "K0": 1, "split_rule": "balanced-normalized-closure",
        "tau": 0.08, "cap_seconds": cap,
        "checkpoints_seconds": [x for x in (300, 1200, 1800, 3600) if x <= cap],
        "executable_sha256": executable_hash, "command": command,
        "started": True, "completed": False,
    }
    write_json(command_path, record)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    with (run_dir / "stdout.log").open("wb") as stdout, \
            (run_dir / "stderr.log").open("wb") as stderr:
        try:
            process = subprocess.run(
                command, cwd=ROOT, env=environment, stdout=stdout,
                stderr=stderr, timeout=cap + 90, check=False)
            return_code, watchdog = process.returncode, False
        except subprocess.TimeoutExpired:
            return_code, watchdog = -1, True
    record.update({
        "return_code": return_code, "watchdog_timeout": watchdog,
        "runner_wall_seconds": time.monotonic() - started,
        "completed": result_path.exists(),
    })
    write_json(command_path, record)
    if return_code != 0 or watchdog or not result_path.exists():
        raise RuntimeError(f"K1 integration row failed: {run_id}")
    result = read_json(result_path)
    process_seconds = float(result.get("final_process_wall_time_seconds", 0.0))
    if process_seconds > cap + 1e-6:
        raise RuntimeError(f"process cap exceeded: {run_id}")
    if result.get("algorithm_preset") != ARMS[arm]["preset"]:
        raise RuntimeError(f"preset roundtrip failed: {run_id}")
    if result.get("external_gini_tree_interval_mip_policy") != ARMS[arm]["policy"]:
        raise RuntimeError(f"inner policy roundtrip failed: {run_id}")
    marker = {
        "schema": "round55-k1-integration-completion-v1",
        "complete": True, "run_id": run_id, "instance_id": row["instance_id"],
        "arm": arm, "preset": ARMS[arm]["preset"],
        "inner_policy": ARMS[arm]["policy"], "cap_seconds": cap,
        "process_seconds": process_seconds, "cap_respected": True,
        "executable_sha256": executable_hash,
        "result_sha256": sha256(result_path),
    }
    write_json(marker_path, marker)
    return {"run_id": run_id, "resumed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--cap", type=int, choices=(1800, 3600), required=True)
    parser.add_argument("--arms", default="K1-AM-SF,K1-AM-SF-CANDIDATE")
    parser.add_argument("--instances")
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    executable = (args.executable if args.executable.is_absolute()
                  else ROOT / args.executable).resolve()
    executable_hash = sha256(executable)
    arms = [value.strip() for value in args.arms.split(",") if value.strip()]
    if any(arm not in ARMS for arm in arms):
        raise RuntimeError("unknown K1 arm")
    selected = None if not args.instances else {
        value.strip() for value in args.instances.split(",") if value.strip()}
    rows = panel_rows(selected)
    tasks = [(row, arm) for row in rows for arm in arms]
    with ThreadPoolExecutor(max_workers=max(1, min(args.jobs, len(tasks)))) as pool:
        futures = {
            pool.submit(run_one, row, arm, executable, executable_hash, args.cap):
            (row["instance_id"], arm)
            for row, arm in tasks
        }
        for ordinal, future in enumerate(as_completed(futures), start=1):
            instance, arm = futures[future]
            status = future.result()
            print(f"[{ordinal}/{len(tasks)}] {arm}/{instance}"
                  f"{' (resumed)' if status['resumed'] else ''}", flush=True)
    print(json.dumps({
        "schema": "round55-k1-integration-run-summary-v1",
        "row_count": len(tasks), "instance_count": len(rows), "arms": arms,
        "cap_seconds": args.cap, "executable_sha256": executable_hash,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
