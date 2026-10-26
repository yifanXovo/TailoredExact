#!/usr/bin/env python3
"""Run and summarize one frozen Round 52 fixed-interval policy panel."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUND50 = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
MANIFEST = ROUND50 / "fixed_interval_state_manifest.csv"
RECONSTRUCTION = ROUND50 / "fixed_interval_state_reconstruction_audit.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def one_csv(path: Path) -> dict[str, str]:
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))
    if len(rows) != 1:
        raise RuntimeError(f"expected one row in {path}, found {len(rows)}")
    return rows[0]


def normalized_gi(path: Path, upper: float, horizon: float,
                  exact: bool, process_seconds: float) -> float:
    points: list[tuple[float, float]] = []
    for row in csv.DictReader(path.open(newline="", encoding="utf-8-sig")):
        if row["bound_available"].lower() not in {"1", "true"}:
            continue
        lower = float(row["best_bound"])
        gap = max(0.0, (upper - lower) / max(1e-12, abs(upper)))
        points.append((max(0.0, float(row["time_seconds"])), gap))
    area, previous_time, previous_gap = 0.0, 0.0, 1.0
    for current_time, current_gap in points:
        current_time = min(horizon, max(previous_time, current_time))
        area += (current_time - previous_time) * previous_gap
        previous_time, previous_gap = current_time, current_gap
        if current_time >= horizon:
            break
    end = min(horizon, process_seconds) if exact else horizon
    if end > previous_time:
        area += (end - previous_time) * previous_gap
        previous_time = end
    if not exact and horizon > previous_time:
        area += (horizon - previous_time) * previous_gap
    return area / horizon


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--states", required=True)
    parser.add_argument("--cap", required=True, type=float)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--gurobi-home", default="D:/gurobi1302/win64")
    args = parser.parse_args()
    if not 0.0 < args.cap <= 1800.0:
        raise RuntimeError("process cap must be in (0,1800]")

    executable = args.executable.resolve()
    executable_sha = sha256(executable)
    manifest = {row["state_id"]: row for row in csv.DictReader(
        MANIFEST.open(newline="", encoding="utf-8-sig"))}
    reconstruction = {row["state_id"]: row for row in csv.DictReader(
        RECONSTRUCTION.open(newline="", encoding="utf-8-sig"))}
    states = [item.strip() for item in args.states.split(",") if item.strip()]
    if len(states) != len(set(states)) or any(s not in manifest for s in states):
        raise RuntimeError("duplicate or unknown state in panel")
    args.run_root.resolve().mkdir(parents=True, exist_ok=True)
    args.summary.resolve().parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "state_id", "policy", "role", "state_kind", "process_cap_seconds",
        "executable_sha256", "input_sha256", "model_sha256", "status",
        "certificate", "certificate_class", "false_certificate",
        "engineering_gate", "evidence_complete", "cap_respected",
        "native_status", "lower_bound", "verified_upper_bound", "gap",
        "gi_common_horizon", "work", "solver_time_seconds",
        "process_time_seconds", "nodes", "simplex_iterations",
        "average_iterations_per_node", "peak_memory_gb",
        "root_relaxation_bound_available", "root_relaxation_bound",
        "final_root_cut_bound_available", "final_root_cut_bound",
        "root_work", "root_time_seconds", "root_simplex_iterations",
        "first_incumbent_work", "first_incumbent_time_seconds",
        "model_build_seconds", "model_read_seconds", "original_rows",
        "original_columns", "original_nonzeros", "subset_duration_policy",
        "subset_duration_rows", "subset_duration_min_m",
        "subset_duration_max_m", "historical_m_may_be_unsafe",
        "min_matrix", "max_matrix", "min_objective", "max_objective",
        "min_bound", "max_bound", "min_rhs", "max_rhs",
        "tailored_cut_policy", "callback_active", "cbcut_symbol_loaded",
        "cblazy_symbol_loaded", "precrush_requested", "precrush_effective",
        "precrush_roundtrip_valid", "callback_disabled_after_failure",
        "callback_calls", "root_callback_calls", "tree_callback_calls",
        "nonoptimal_mipnode_callbacks", "relaxation_vector_failures",
        "cuts_generated", "cuts_violated", "cuts_selected", "cuts_added",
        "duplicate_rejections", "dominated_rejections",
        "nonviolated_rejections", "invalid_rejections",
        "submission_failures", "callback_failures", "cut_pool_size",
        "callback_overhead_seconds", "cut_infrastructure_gate",
        "failure_reason", "artifact_dir"
    ]
    rows: list[dict[str, object]] = []
    for state_id in states:
        frozen = manifest[state_id]
        state = reconstruction[state_id]
        artifact = args.run_root.resolve() / f"{state_id}__{args.policy}"
        completion_path = artifact / "completion_marker.json"
        reusable = False
        if completion_path.exists() and (artifact / "command.json").exists():
            completion = json.loads(completion_path.read_text(encoding="utf-8"))
            command = json.loads((artifact / "command.json").read_text(
                encoding="utf-8"))
            reusable = (completion.get("evidence_complete") is True and
                        completion.get("cap_respected") is True and
                        command.get("policy") == args.policy and
                        command.get("executable_sha256") == executable_sha and
                        abs(float(command.get("process_cap_seconds", -1)) -
                            args.cap) <= 1e-9)
        if not reusable:
            command = [
                str(executable), "--mode", "solve", "--state-id", state_id,
                "--input", str(ROOT / frozen["input_path"]),
                "--artifact-dir", str(artifact), "--policy", args.policy,
                "--gurobi-home", args.gurobi_home,
                "--gamma-lower", state["gamma_lower"],
                "--gamma-upper", state["gamma_upper"],
                "--cutoff", state["verified_cutoff"],
                "--process-cap", format(args.cap, ".17g"),
                "--T", state["route_time_limit"],
                "--pickup-time", "60", "--drop-time", "60"
            ]
            completed = subprocess.run(
                command, cwd=ROOT, timeout=max(60.0, args.cap + 45.0))
            if completed.returncode != 0:
                raise RuntimeError(
                    f"state {state_id} returned {completed.returncode}")

        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        result = json.loads((artifact / "result.json").read_text(
            encoding="utf-8"))
        model = json.loads((artifact / "model_fingerprint.json").read_text(
            encoding="utf-8"))
        size = one_csv(artifact / "formulation_size_ledger.csv")
        numerical = one_csv(artifact / "numerical_quality_ledger.csv")
        cut = one_csv(artifact / "cut_lifecycle_ledger.csv")
        gi = normalized_gi(
            artifact / "mip_progress.csv", float(result["verified_upper_bound"]),
            args.cap, bool(result["certificate"]),
            float(result["process_time_seconds"]))
        row: dict[str, object] = {
            "state_id": state_id, "policy": args.policy,
            "role": frozen["historical_role"],
            "state_kind": frozen["state_kind"],
            "process_cap_seconds": format(args.cap, ".17g"),
            "executable_sha256": executable_sha,
            "input_sha256": frozen["input_sha256"],
            "model_sha256": model["sha256"], "status": result["status"],
            "certificate": result["certificate"],
            "certificate_class": result["certificate_class"],
            "false_certificate": result["false_certificate"],
            "engineering_gate": result["engineering_gate"],
            "evidence_complete": completion["evidence_complete"],
            "cap_respected": completion["cap_respected"],
            "native_status": result["native_status"],
            "lower_bound": result["lower_bound"],
            "verified_upper_bound": result["verified_upper_bound"],
            "gap": result["gap"], "gi_common_horizon": gi,
            "work": result["work"],
            "solver_time_seconds": result["solver_time_seconds"],
            "process_time_seconds": result["process_time_seconds"],
            "nodes": result["nodes"],
            "simplex_iterations": result["simplex_iterations"],
            "average_iterations_per_node": result["average_iterations_per_node"],
            "peak_memory_gb": result["peak_memory_gb"],
            "root_relaxation_bound_available": result["root_relaxation_bound_available"],
            "root_relaxation_bound": result["root_relaxation_bound"],
            "final_root_cut_bound_available": result["final_root_cut_bound_available"],
            "final_root_cut_bound": result["final_root_cut_bound"],
            "root_work": result["root_work"],
            "root_time_seconds": result["root_time_seconds"],
            "root_simplex_iterations": result["root_simplex_iterations"],
            "first_incumbent_work": result["first_incumbent_work"],
            "first_incumbent_time_seconds": result["first_incumbent_time_seconds"],
            "model_build_seconds": result["model_build_seconds"],
            "model_read_seconds": result["model_read_seconds"],
            "original_rows": size["original_rows"],
            "original_columns": size["original_columns"],
            "original_nonzeros": size["original_nonzeros"],
            "subset_duration_policy": model["round51_subset_duration_big_m"],
            "subset_duration_rows": model["round51_subset_duration_rows"],
            "subset_duration_min_m": model["round51_subset_duration_min_m"],
            "subset_duration_max_m": model["round51_subset_duration_max_m"],
            "historical_m_may_be_unsafe": model["round51_historical_m_may_be_unsafe"],
            "min_matrix": numerical["min_matrix"],
            "max_matrix": numerical["max_matrix"],
            "min_objective": numerical["min_objective"],
            "max_objective": numerical["max_objective"],
            "min_bound": numerical["min_bound"], "max_bound": numerical["max_bound"],
            "min_rhs": numerical["min_rhs"], "max_rhs": numerical["max_rhs"],
            "tailored_cut_policy": cut["tailored_cut_policy"],
            "callback_active": cut["callback_active"],
            "cbcut_symbol_loaded": cut["cbcut_symbol_loaded"],
            "cblazy_symbol_loaded": cut["cblazy_symbol_loaded"],
            "precrush_requested": cut["precrush_requested"],
            "precrush_effective": cut["precrush_effective"],
            "precrush_roundtrip_valid": cut["precrush_roundtrip_valid"],
            "callback_disabled_after_failure": cut["callback_disabled_after_failure"],
            "callback_calls": cut["callback_calls"],
            "root_callback_calls": cut["root_callback_calls"],
            "tree_callback_calls": cut["tree_callback_calls"],
            "nonoptimal_mipnode_callbacks": cut["nonoptimal_mipnode_callbacks"],
            "relaxation_vector_failures": cut["relaxation_vector_failures"],
            "cuts_generated": cut["generated"], "cuts_violated": cut["violated"],
            "cuts_selected": cut["selected"], "cuts_added": cut["added"],
            "duplicate_rejections": cut["duplicate_rejections"],
            "dominated_rejections": cut["dominated_rejections"],
            "nonviolated_rejections": cut["nonviolated_rejections"],
            "invalid_rejections": cut["invalid_rejections"],
            "submission_failures": cut["submission_failures"],
            "callback_failures": cut["callback_failures"],
            "cut_pool_size": cut["global_pool_size"],
            "callback_overhead_seconds": cut["callback_overhead_seconds"],
            "cut_infrastructure_gate": cut["infrastructure_gate"],
            "failure_reason": result["failure_reason"],
            "artifact_dir": artifact.relative_to(ROOT).as_posix()
        }
        rows.append(row)
        with args.summary.resolve().open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(f"{state_id}: {result['status']} Work={result['work']} cuts={cut['added']}",
              flush=True)

    if len(rows) != len(states):
        raise RuntimeError("panel summary incomplete")
    for row in rows:
        if not (row["evidence_complete"] and row["cap_respected"] and
                row["engineering_gate"] and not row["false_certificate"]):
            raise RuntimeError(f"evidence/correctness gate failed: {row['state_id']}")


if __name__ == "__main__":
    main()
