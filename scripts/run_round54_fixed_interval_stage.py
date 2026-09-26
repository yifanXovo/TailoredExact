#!/usr/bin/env python3
"""Run one frozen paired Round 54 fixed-interval live stage."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path


EVIDENCE_REL = Path("results/gf_k1_am_sf_inventory_route_round54")
ROUND53_REL = Path("results/gf_k1_f0_callback_isolation_round53/local_raw")
ARMS = (("F0-CLEAN", "f0-clean"), ("IR1", "ir1"))
HARD_STATES = {"D1", "D3", "D4", "D6", "D9", "D12", "D13", "D14"}


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_command(root: Path, state_id: str) -> dict:
    stage = "f0_development_300s" if state_id.startswith("D") else "f0_confirmation_1200s"
    return read_json(
        root / ROUND53_REL / stage / "F0-CLEAN"
        / f"{state_id}__F0-CLEAN" / "command.json"
    )


def rows_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def relative_gap(upper: float, lower: float) -> float:
    return max(0.0, (upper - lower) / max(1e-12, abs(upper)))


def normalized_gap_integral(run_dir: Path, result: dict, horizon: float) -> float:
    upper = float(result["verified_upper_bound"])
    points: list[tuple[float, float]] = []
    cumulative_root_time = 0.0
    for row in rows_csv(run_dir / "external_root_closure_ledger.csv"):
        cumulative_root_time += max(0.0, float(row["lp_time"]))
        if str(row["lp_valid"]).lower() in {"1", "true"}:
            points.append(
                (cumulative_root_time,
                 relative_gap(upper, float(row["lp_objective"])))
            )
    preterminal = max(
        cumulative_root_time,
        float(result["process_time_seconds"])
        - float(result["terminal_solver_time_seconds"]),
    )
    for row in rows_csv(run_dir / "mip_progress.csv"):
        if str(row["bound_available"]).lower() not in {"1", "true"}:
            continue
        points.append(
            (preterminal + max(0.0, float(row["time_seconds"])),
             relative_gap(upper, float(row["best_bound"])))
        )
    points.sort()
    area = 0.0
    previous_time = 0.0
    previous_gap = 1.0
    for point_time, point_gap in points:
        point_time = min(horizon, max(previous_time, point_time))
        area += (point_time - previous_time) * previous_gap
        previous_time = point_time
        previous_gap = point_gap
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


def run_one(
    root: Path,
    executable: Path,
    executable_hash: str,
    state_id: str,
    arm: str,
    variant: str,
    cap: int,
    run_root: Path,
    gurobi_home: str,
) -> dict:
    source = source_command(root, state_id)
    run_dir = run_root / arm / state_id
    result_path = run_dir / "result.json"
    reusable = False
    if result_path.exists() and (run_dir / "command.json").exists():
        prior = read_json(run_dir / "command.json")
        reusable = (
            prior.get("executable_sha256") == executable_hash
            and prior.get("variant") == variant
            and abs(float(prior.get("process_cap_seconds", -1)) - cap) <= 1e-9
        )
    if not reusable:
        run_dir.mkdir(parents=True, exist_ok=True)
        command = [
            str(executable), "--mode", "solve",
            "--state-id", state_id,
            "--input", source["input"],
            "--artifact-dir", str(run_dir),
            "--variant", variant,
            "--gurobi-home", gurobi_home,
            "--gamma-lower", repr(float(source["gamma_lower"])),
            "--gamma-upper", repr(float(source["gamma_upper"])),
            "--cutoff", repr(float(source["verified_cutoff"])),
            "--process-cap", str(cap),
            "--route-time-limit", repr(float(source["route_time_limit"])),
            "--pickup-time", repr(float(source["pickup_time"])),
            "--drop-time", repr(float(source["drop_time"])),
        ]
        completed = subprocess.run(
            command, cwd=root, text=True, capture_output=True,
            timeout=cap + 90, check=False,
        )
        (run_dir / "runner_stdout.txt").write_text(completed.stdout, encoding="utf-8")
        (run_dir / "runner_stderr.txt").write_text(completed.stderr, encoding="utf-8")
        if completed.returncode != 0:
            raise RuntimeError(
                f"{arm}/{state_id} returned {completed.returncode}: {completed.stderr[-500:]}"
            )
        command_record = read_json(run_dir / "command.json")
        command_record["executable_path"] = str(executable)
        command_record["executable_sha256"] = executable_hash
        (run_dir / "command.json").write_text(
            json.dumps(command_record, indent=2) + "\n", encoding="utf-8"
        )
    result = read_json(result_path)
    gi = normalized_gap_integral(run_dir, result, float(cap))
    engineering_valid = (
        bool(result["closure_valid"])
        and not bool(result["fallback_required"])
        and bool(result["terminal_engineering_gate"])
        and bool(result["cap_respected"])
        and not bool(result["terminal_callback_active"])
        and int(result["terminal_precrush_requested"]) == -1
        and int(result["subset_duration_rows"]) == 0
    )
    return {
        "state_id": state_id,
        "arm": arm,
        "variant": result["variant"],
        "cap_seconds": cap,
        "executable_sha256": executable_hash,
        "engineering_valid": engineering_valid,
        "closure_valid": result["closure_valid"],
        "closure_converged": result["closure_converged"],
        "fallback_required": result["fallback_required"],
        "certificate": result["certificate"],
        "false_certificate": result["false_certificate"],
        "native_status": result["terminal_native_status"],
        "lower_bound": result["lower_bound"],
        "verified_upper_bound": result["verified_upper_bound"],
        "gap": result["final_gap"],
        "normalized_gap_integral": gi,
        "total_work": result["total_work"],
        "closure_work": result["closure_work"],
        "terminal_work": result["terminal_work"],
        "process_time_seconds": result["process_time_seconds"],
        "closure_solver_time_seconds": result["closure_solver_time_seconds"],
        "terminal_solver_time_seconds": result["terminal_solver_time_seconds"],
        "nodes": result["terminal_nodes"],
        "simplex_iterations": (
            float(result["closure_simplex_iterations"])
            + float(result["terminal_simplex_iterations"])
        ),
        "first_incumbent_work": result["first_incumbent_work"],
        "first_incumbent_time_seconds": result["first_incumbent_time_seconds"],
        "peak_memory_gb": result["terminal_peak_memory_gb"],
        "root_lp_objective": result["initial_root_lp_objective"],
        "root_closure_bound": result["final_root_closure_objective"],
        "root_bound_gain": result["root_bound_gain"],
        "closure_rounds": result["closure_rounds"],
        "cuts_generated": result["cuts_generated"],
        "cuts_added": result["cuts_added"],
        "model_rows": result["model_rows"],
        "model_columns": result["model_columns"],
        "model_nonzeros": result["model_nonzeros"],
        "subset_duration_rows": result["subset_duration_rows"],
        "artifact_dir": str(run_dir.relative_to(root)).replace("\\", "/"),
    }


def severe(base: dict, candidate: dict) -> tuple[bool, str]:
    if bool(base["certificate"]) and not bool(candidate["certificate"]):
        return True, "lost_baseline_certificate"
    if bool(base["certificate"]) and bool(candidate["certificate"]):
        work_ratio = (float(candidate["total_work"]) + 1e-12) / (
            float(base["total_work"]) + 1e-12
        )
        if work_ratio > 1.50 and float(candidate["total_work"]) - float(base["total_work"]) > 50:
            return True, "exact_work_regression"
        time_ratio = (float(candidate["process_time_seconds"]) + 1e-12) / (
            float(base["process_time_seconds"]) + 1e-12
        )
        if time_ratio > 1.50 and float(candidate["process_time_seconds"]) - float(base["process_time_seconds"]) > 60:
            return True, "exact_time_regression"
    gi_delta = float(candidate["normalized_gap_integral"]) - float(base["normalized_gap_integral"])
    gi_ratio = (float(candidate["normalized_gap_integral"]) + 1e-12) / (
        float(base["normalized_gap_integral"]) + 1e-12
    )
    if gi_ratio > 1.50 and gi_delta >= 0.05:
        return True, "capped_gi_regression"
    gap_delta = float(candidate["gap"]) - float(base["gap"])
    gap_ratio = (float(candidate["gap"]) + 1e-12) / (float(base["gap"]) + 1e-12)
    if gap_ratio > 1.50 and gap_delta >= 0.05:
        return True, "capped_gap_regression"
    return False, "none"


def material_improvement(state_id: str, base: dict, candidate: dict) -> tuple[bool, str]:
    if state_id not in HARD_STATES:
        return False, "not_predeclared_hard_state"
    if not bool(base["certificate"]) and bool(candidate["certificate"]):
        return True, "certificate_gain"
    if bool(base["certificate"]) and bool(candidate["certificate"]):
        ratio = (float(candidate["total_work"]) + 1e-12) / (float(base["total_work"]) + 1e-12)
        if ratio <= 0.90 and float(base["total_work"]) - float(candidate["total_work"]) >= 10:
            return True, "exact_work_reduction"
    gi_ratio = (float(candidate["normalized_gap_integral"]) + 1e-12) / (
        float(base["normalized_gap_integral"]) + 1e-12
    )
    if gi_ratio <= 0.90 and float(base["normalized_gap_integral"]) - float(candidate["normalized_gap_integral"]) >= 0.05:
        return True, "gi_reduction"
    gap_ratio = (float(candidate["gap"]) + 1e-12) / (float(base["gap"]) + 1e-12)
    if gap_ratio <= 0.90 and float(base["gap"]) - float(candidate["gap"]) >= 0.05:
        return True, "gap_reduction"
    return False, "none"


def geometric_mean_ratio(pairs: list[tuple[float, float]]) -> float:
    return math.exp(sum(math.log((right + 1.0) / (left + 1.0)) for left, right in pairs) / len(pairs))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--states", required=True)
    parser.add_argument("--cap", type=int, required=True)
    parser.add_argument("--stage", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--gurobi-home", default="D:/gurobi1302/win64")
    args = parser.parse_args()
    if args.cap <= 0 or args.cap > 3600:
        raise RuntimeError("ordinary stage cap must be in (0,3600]")
    root = args.root.resolve()
    executable = args.executable
    if not executable.is_absolute():
        executable = root / executable
    executable_hash = sha256(executable)
    state_ids = [item.strip() for item in args.states.split(",") if item.strip()]
    if len(state_ids) != len(set(state_ids)):
        raise RuntimeError("duplicate state IDs")
    run_root = root / EVIDENCE_REL / "local_raw" / args.stage
    results: list[dict] = []
    for arm, variant in ARMS:
        for ordinal, state_id in enumerate(state_ids, start=1):
            print(f"[{arm} {ordinal}/{len(state_ids)}] {state_id}", flush=True)
            results.append(run_one(
                root, executable, executable_hash, state_id, arm, variant,
                args.cap, run_root, args.gurobi_home,
            ))
    output_path = root / EVIDENCE_REL / args.output
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)

    by_key = {(row["state_id"], row["arm"]): row for row in results}
    pair_rows: list[dict] = []
    for state_id in state_ids:
        base = by_key[(state_id, "F0-CLEAN")]
        candidate = by_key[(state_id, "IR1")]
        is_severe, severe_reason = severe(base, candidate)
        material, material_reason = material_improvement(state_id, base, candidate)
        pair_rows.append({
            "stage": args.stage,
            "cap_seconds": args.cap,
            "state_id": state_id,
            "f0_certificate": base["certificate"],
            "ir1_certificate": candidate["certificate"],
            "certificate_gain": int(bool(candidate["certificate"]) and not bool(base["certificate"])),
            "certificate_loss": int(bool(base["certificate"]) and not bool(candidate["certificate"])),
            "f0_work": base["total_work"],
            "ir1_work": candidate["total_work"],
            "shifted_work_ratio": (float(candidate["total_work"]) + 1) / (float(base["total_work"]) + 1),
            "f0_gi": base["normalized_gap_integral"],
            "ir1_gi": candidate["normalized_gap_integral"],
            "gi_delta": float(candidate["normalized_gap_integral"]) - float(base["normalized_gap_integral"]),
            "f0_gap": base["gap"],
            "ir1_gap": candidate["gap"],
            "severe_regression": is_severe,
            "severe_reason": severe_reason,
            "material_hard_state_improvement": material,
            "material_reason": material_reason,
        })
    pair_path = root / EVIDENCE_REL / "ir_fixed_interval_pair_summary.csv"
    existing = []
    if pair_path.exists():
        existing = [row for row in rows_csv(pair_path) if row["stage"] != args.stage]
    combined = existing + pair_rows
    with pair_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(pair_rows[0]))
        writer.writeheader()
        writer.writerows(combined)

    all_valid = all(bool(row["engineering_valid"]) for row in results)
    false_certificates = sum(bool(row["false_certificate"]) for row in results)
    losses = sum(int(row["certificate_loss"]) for row in pair_rows)
    severe_count = sum(bool(row["severe_regression"]) for row in pair_rows)
    material_rows = [row["state_id"] for row in pair_rows if row["material_hard_state_improvement"]]
    work_ratio = geometric_mean_ratio([
        (float(by_key[(state, "F0-CLEAN")]["total_work"]),
         float(by_key[(state, "IR1")]["total_work"]))
        for state in state_ids
    ])
    f0_gi = sum(float(by_key[(state, "F0-CLEAN")]["normalized_gap_integral"]) for state in state_ids)
    ir1_gi = sum(float(by_key[(state, "IR1")]["normalized_gap_integral"]) for state in state_ids)
    aggregate_nonworse = work_ratio <= 1.0 + 1e-12 and ir1_gi <= f0_gi + 1e-12
    gate_passed = (
        all_valid and false_certificates == 0 and losses == 0
        and severe_count == 0 and bool(material_rows) and aggregate_nonworse
    )
    gate = {
        "schema": "round54-fixed-interval-stage-gate-v1",
        "stage": args.stage,
        "cap_seconds": args.cap,
        "row_count": len(results),
        "pair_count": len(pair_rows),
        "executable_sha256": executable_hash,
        "all_engineering_valid": all_valid,
        "false_certificate_count": false_certificates,
        "lost_f0_certificate_count": losses,
        "severe_regression_count": severe_count,
        "material_hard_state_improvement_rows": material_rows,
        "shifted_work_geometric_mean_ratio_ir1_over_f0": work_ratio,
        "aggregate_gi_f0": f0_gi,
        "aggregate_gi_ir1": ir1_gi,
        "aggregate_work_and_gi_nonworse": aggregate_nonworse,
        "next_stage_gate_passed": gate_passed,
    }
    gate_name = f"{args.stage}_gate.json"
    (root / EVIDENCE_REL / gate_name).write_text(
        json.dumps(gate, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(gate, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
