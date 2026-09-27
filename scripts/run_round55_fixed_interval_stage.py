#!/usr/bin/env python3
"""Run and compact one Round 55 fixed-interval build/LP/MIP stage."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


EVIDENCE_REL = Path("results/gf_k1_am_sf_station_state_chain_round55")
SOURCE_REL = Path("results/gf_k1_f0_callback_isolation_round53/local_raw")
POLICIES = {
    "F0-CLEAN": "interval-mip-core-no-exhaustive-subset-duration",
    "SF-MC4": "round55-sf-mc4",
    "VD-P": "round55-vd-p",
    "VD-J": "round55-vd-j",
    "SF-R1": "round55-sf-r1-remove-triple-duration",
    "VD-P+SF-R1": "round55-vdp-sf-r1",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_command(root: Path, state_id: str) -> dict:
    if state_id.startswith("D"):
        stage = "f0_development_300s"
    elif state_id.startswith("C"):
        stage = "f0_confirmation_1200s"
    else:
        manifests = [
            ("confirmation_extension_execution_manifest.json", "additional_states"),
            ("key_long_execution_manifest.json", "additional_states"),
            ("offline_census_execution_manifest.json", "additional_states"),
        ]
        for manifest_name, collection in manifests:
            manifest_path = root / EVIDENCE_REL / manifest_name
            if not manifest_path.exists():
                continue
            manifest = read_json(manifest_path)
            for item in manifest.get(collection, []):
                if item["state_id"] == state_id:
                    return {
                        "input": str(root / item["input_path"]),
                        "gamma_lower": item["gamma_lower"],
                        "gamma_upper": item["gamma_upper"],
                        "verified_cutoff": item["verified_cutoff"],
                        "route_time_limit": item["route_time_limit"],
                        "pickup_time": item.get("pickup_time", 60),
                        "drop_time": item.get("drop_time", 60),
                    }
        raise RuntimeError(f"no frozen source command for {state_id}")
    return read_json(
        root / SOURCE_REL / stage / "F0-CLEAN"
        / f"{state_id}__F0-CLEAN" / "command.json"
    )


def normalized_gap_integral(run_dir: Path, result: dict, horizon: float) -> float:
    upper = float(result["verified_upper_bound"])
    events: list[tuple[float, float]] = []
    progress_path = run_dir / "mip_progress.csv"
    if progress_path.exists():
        for row in read_rows(progress_path):
            if row.get("bound_available", "0").lower() not in {"1", "true"}:
                continue
            lower = float(row["best_bound"])
            gap = max(0.0, (upper - lower) / max(1e-12, abs(upper)))
            events.append((max(0.0, float(row["time_seconds"])), gap))
    events.sort()
    area = 0.0
    previous_time = 0.0
    previous_gap = 1.0
    for event_time, event_gap in events:
        event_time = min(horizon, max(previous_time, event_time))
        area += (event_time - previous_time) * previous_gap
        previous_time, previous_gap = event_time, event_gap
        if previous_time >= horizon:
            break
    process_time = min(horizon, float(result["process_time_seconds"]))
    if process_time > previous_time:
        area += (process_time - previous_time) * previous_gap
        previous_time = process_time
    if bool(result["certificate"]):
        previous_gap = 0.0
    if horizon > previous_time:
        area += (horizon - previous_time) * previous_gap
    return area / horizon


def compact(root: Path, run_dir: Path, arm: str, mode: str, cap: int,
            executable_hash: str) -> dict:
    command = read_json(run_dir / "command.json")
    completion = read_json(run_dir / "completion_marker.json")
    size = read_rows(run_dir / "formulation_size_ledger.csv")[0]
    row = {
        "state_id": command["state_id"],
        "arm": arm,
        "policy": command["policy"],
        "mode": mode,
        "cap_seconds": cap,
        "executable_sha256": executable_hash,
        "completion_status": completion["status"],
        "rows": size["original_rows"],
        "columns": size["original_columns"],
        "nonzeros": size["original_nonzeros"],
        "station_state_formulation": size["station_state_formulation"],
        "selector_variables": size["station_state_selector_variables"],
        "perspective_variables": size["station_state_perspective_variables"],
        "aggregate_mccormick_rows": size["aggregate_mccormick_rows"],
    }
    if mode == "build":
        row.update({
            "engineering_gate": True, "certificate": False,
            "false_certificate": False, "lower_bound": "",
            "verified_upper_bound": command["verified_cutoff"], "gap": "",
            "normalized_gap_integral": "", "work": "", "time_seconds": "",
            "nodes": "", "simplex_iterations": "", "root_bound": "",
            "root_work": "", "root_time_seconds": "", "model_build_seconds": "",
            "peak_memory_gb": "", "artifact_dir": run_dir.relative_to(root).as_posix(),
        })
        return row
    if mode == "lp":
        result = read_json(run_dir / "lp_result.json")
        row.update({
            "engineering_gate": result["valid"],
            "certificate": False,
            "false_certificate": False,
            "lower_bound": result["objective"],
            "verified_upper_bound": command["verified_cutoff"],
            "gap": max(0.0, (float(command["verified_cutoff"]) - float(result["objective"]))
                       / max(1e-12, abs(float(command["verified_cutoff"]))),),
            "normalized_gap_integral": "",
            "work": result["work"],
            "time_seconds": result["process_time_seconds"],
            "nodes": 0,
            "simplex_iterations": result["simplex_iterations"],
            "root_bound": result["objective"],
            "root_work": result["work"],
            "root_time_seconds": result["solver_time_seconds"],
            "model_build_seconds": max(
                0.0, float(result["process_time_seconds"]) - float(result["solver_time_seconds"])),
            "peak_memory_gb": "",
            "artifact_dir": run_dir.relative_to(root).as_posix(),
        })
        return row
    result = read_json(run_dir / "result.json")
    root_row = read_rows(run_dir / "root_processing_ledger.csv")[0]
    row.update({
        "engineering_gate": result["engineering_gate"],
        "certificate": result["certificate"],
        "false_certificate": result["false_certificate"],
        "lower_bound": result["lower_bound"],
        "verified_upper_bound": result["verified_upper_bound"],
        "gap": result["gap"],
        "normalized_gap_integral": normalized_gap_integral(run_dir, result, cap),
        "work": result["work"],
        "time_seconds": result["process_time_seconds"],
        "nodes": result["nodes"],
        "simplex_iterations": result["simplex_iterations"],
        "root_bound": root_row["root_relaxation_bound"],
        "root_work": root_row["root_work"],
        "root_time_seconds": root_row["root_time_seconds"],
        "model_build_seconds": result["model_build_seconds"],
        "peak_memory_gb": result["peak_memory_gb"],
        "artifact_dir": run_dir.relative_to(root).as_posix(),
    })
    return row


def run_one(root: Path, executable: Path, executable_hash: str, state_id: str,
            arm: str, mode: str, cap: int, stage: str, gurobi_home: str) -> dict:
    source = source_command(root, state_id)
    run_dir = root / EVIDENCE_REL / "local_raw" / stage / arm / state_id
    reusable = False
    if (run_dir / "completion_marker.json").exists() and (run_dir / "command.json").exists():
        prior = read_json(run_dir / "command.json")
        reusable = (
            prior.get("executable_sha256") == executable_hash
            and prior.get("mode") == mode
            and prior.get("policy") == POLICIES[arm]
            and abs(float(prior.get("process_cap_seconds", -1)) - cap) <= 1e-9
        )
    if not reusable:
        run_dir.mkdir(parents=True, exist_ok=True)
        command = [
            str(executable), "--mode", mode, "--state-id", state_id,
            "--input", source["input"], "--artifact-dir", str(run_dir),
            "--policy", POLICIES[arm], "--gurobi-home", gurobi_home,
            "--gamma-lower", repr(float(source["gamma_lower"])),
            "--gamma-upper", repr(float(source["gamma_upper"])),
            "--cutoff", repr(float(source["verified_cutoff"])),
            "--process-cap", str(cap), "--T", repr(float(source["route_time_limit"])),
            "--pickup-time", repr(float(source["pickup_time"])),
            "--drop-time", repr(float(source["drop_time"])),
        ]
        completed = subprocess.run(
            command, cwd=root, text=True, capture_output=True,
            timeout=cap + 120, check=False,
        )
        (run_dir / "runner_stdout.txt").write_text(completed.stdout, encoding="utf-8")
        (run_dir / "runner_stderr.txt").write_text(completed.stderr, encoding="utf-8")
        if completed.returncode != 0:
            raise RuntimeError(
                f"{stage}/{arm}/{state_id} returned {completed.returncode}: "
                f"{completed.stderr[-800:]}"
            )
    return compact(root, run_dir, arm, mode, cap, executable_hash)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--states", required=True)
    parser.add_argument("--arms", required=True)
    parser.add_argument("--mode", choices=("build", "lp", "solve"), required=True)
    parser.add_argument("--cap", type=int, required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--gurobi-home", default="D:/gurobi1302/win64")
    args = parser.parse_args()
    if args.cap <= 0 or args.cap > 7200:
        raise RuntimeError("cap must be in (0,7200]")
    root = args.root.resolve()
    executable = args.executable if args.executable.is_absolute() else root / args.executable
    executable_hash = sha256(executable)
    states = [item.strip() for item in args.states.split(",") if item.strip()]
    arms = [item.strip() for item in args.arms.split(",") if item.strip()]
    unknown = set(arms) - set(POLICIES)
    if unknown:
        raise RuntimeError(f"unknown arms: {sorted(unknown)}")
    tasks = [(state, arm) for arm in arms for state in states]
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.jobs, len(tasks)))) as pool:
        futures = {
            pool.submit(run_one, root, executable, executable_hash, state, arm,
                        args.mode, args.cap, args.stage, args.gurobi_home): (state, arm)
            for state, arm in tasks
        }
        for ordinal, future in enumerate(as_completed(futures), start=1):
            state, arm = futures[future]
            rows.append(future.result())
            print(f"[{ordinal}/{len(tasks)}] {arm}/{state}", flush=True)
    rows.sort(key=lambda row: (arms.index(row["arm"]), states.index(row["state_id"])))
    output = root / EVIDENCE_REL / args.output
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    decision = {
        "schema": "round55-fixed-interval-stage-summary-v1",
        "stage": args.stage,
        "mode": args.mode,
        "cap_seconds": args.cap,
        "row_count": len(rows),
        "state_count": len(states),
        "arm_count": len(arms),
        "arms": arms,
        "states": states,
        "executable_sha256": executable_hash,
        "all_engineering_valid": all(bool(row["engineering_gate"]) for row in rows),
        "false_certificate_count": sum(bool(row["false_certificate"]) for row in rows),
        "certificate_counts": {
            arm: sum(bool(row["certificate"]) for row in rows if row["arm"] == arm)
            for arm in arms
        },
        "shifted_work_geometric_mean_vs_f0": {},
        "aggregate_gi_vs_f0": {},
    }
    if "F0-CLEAN" in arms and args.mode == "solve":
        by_key = {(row["state_id"], row["arm"]): row for row in rows}
        for arm in arms:
            if arm == "F0-CLEAN":
                continue
            ratios = [
                (float(by_key[(state, arm)]["work"]) + 1.0)
                / (float(by_key[(state, "F0-CLEAN")]["work"]) + 1.0)
                for state in states
            ]
            decision["shifted_work_geometric_mean_vs_f0"][arm] = math.exp(
                sum(math.log(value) for value in ratios) / len(ratios)
            )
            decision["aggregate_gi_vs_f0"][arm] = (
                sum(float(by_key[(state, arm)]["normalized_gap_integral"]) for state in states)
                / max(1e-12, sum(float(by_key[(state, "F0-CLEAN")]["normalized_gap_integral"])
                                 for state in states))
            )
    output.with_suffix(".summary.json").write_text(
        json.dumps(decision, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(decision, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
