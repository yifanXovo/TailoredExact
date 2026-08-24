#!/usr/bin/env python3
"""Run a frozen Round 50 fixed-interval policy panel sequentially."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
RECONSTRUCTION = EVIDENCE / "fixed_interval_state_reconstruction_audit.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv_row(path: Path) -> dict[str, str]:
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))
    if len(rows) != 1:
        raise RuntimeError(f"expected one data row in {path}, found {len(rows)}")
    return rows[0]


def lp_variable_type_counts(path: Path, total_columns: int) -> tuple[int, int, int]:
    section = ""
    generals = 0
    binaries = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line in {"Generals", "Binaries", "End"}:
            section = line
            continue
        if not line or section not in {"Generals", "Binaries"}:
            continue
        count = len(line.split())
        if section == "Generals":
            generals += count
        else:
            binaries += count
    integer = generals + binaries
    if integer > total_columns:
        raise RuntimeError(f"typed variable count exceeds columns in {path}")
    return total_columns - integer, integer, binaries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--states", required=True,
                        help="comma-separated frozen state IDs")
    parser.add_argument("--cap", required=True, type=float)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--gurobi-home", default="D:/gurobi1302/win64")
    args = parser.parse_args()
    if not (0.0 < args.cap <= 1800.0):
        raise RuntimeError("cap must be in (0,1800]")

    executable = args.executable.resolve()
    executable_sha = sha256(executable)
    reconstruction_rows = {
        row["state_id"]: row for row in csv.DictReader(
            RECONSTRUCTION.open(newline="", encoding="utf-8-sig"))
    }
    manifest_rows = {
        row["state_id"]: row for row in csv.DictReader(
            (EVIDENCE / "fixed_interval_state_manifest.csv").open(
                newline="", encoding="utf-8-sig"))
    }
    requested = [value.strip() for value in args.states.split(",") if value.strip()]
    if len(requested) != len(set(requested)):
        raise RuntimeError("duplicate state ID in requested panel")
    missing = [state for state in requested if state not in reconstruction_rows]
    if missing:
        raise RuntimeError(f"unknown state IDs: {missing}")

    run_root = args.run_root.resolve()
    summary_path = args.summary.resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict[str, object]] = []
    fields = [
        "state_id", "panel", "instance", "policy", "process_cap_seconds",
        "executable_sha256", "model_sha256", "model_identity_match",
        "status", "certificate", "certificate_class", "false_certificate",
        "evidence_complete", "cap_respected", "native_status", "lower_bound",
        "verified_upper_bound", "gap", "work", "solver_time_seconds",
        "process_time_seconds", "nodes", "simplex_iterations",
        "average_iterations_per_node", "peak_memory_gb",
        "root_relaxation_bound_available", "root_relaxation_bound",
        "final_root_cut_bound_available", "final_root_cut_bound", "root_work",
        "root_time_seconds", "root_simplex_iterations", "root_cut_count",
        "first_incumbent_work", "first_incumbent_time_seconds",
        "model_build_seconds", "model_read_seconds", "original_rows",
        "original_columns", "original_nonzeros", "presolved_rows",
        "presolved_columns", "presolved_nonzeros", "continuous_variables",
        "integer_variables", "binary_variables", "min_matrix", "max_matrix",
        "min_objective", "max_objective", "min_bound", "max_bound",
        "min_rhs", "max_rhs", "branch_priority_assignment_status",
        "failure_reason", "artifact_dir",
    ]

    for state_id in requested:
        frozen = reconstruction_rows[state_id]
        artifact_dir = run_root / f"{state_id}__{args.policy}"
        completion_path = artifact_dir / "completion_marker.json"
        reusable = False
        if completion_path.exists() and (artifact_dir / "command.json").exists():
            completion = json.loads(completion_path.read_text(encoding="utf-8"))
            command = json.loads((artifact_dir / "command.json").read_text(encoding="utf-8"))
            reusable = (
                completion.get("evidence_complete") is True
                and completion.get("cap_respected") is True
                and command.get("policy") == args.policy
                and abs(float(command.get("process_cap_seconds", -1.0)) - args.cap) <= 1e-9
                and command.get("executable_sha256") == executable_sha
            )
        if not reusable:
            command = [
                str(executable), "--mode", "solve", "--state-id", state_id,
                "--input", str(ROOT / manifest_rows[state_id]["input_path"]),
                "--artifact-dir", str(artifact_dir), "--policy", args.policy,
                "--gamma-lower", frozen["gamma_lower"], "--gamma-upper",
                frozen["gamma_upper"], "--cutoff", frozen["verified_cutoff"],
                "--process-cap", format(args.cap, ".17g"), "--T",
                frozen["route_time_limit"], "--gurobi-home", args.gurobi_home,
            ]
            completed = subprocess.run(
                command, cwd=ROOT, timeout=max(60.0, args.cap + 45.0))
            if completed.returncode != 0:
                raise RuntimeError(
                    f"fixed-state process failed {completed.returncode}: {state_id}")

        completion = json.loads(completion_path.read_text(encoding="utf-8"))
        result = json.loads((artifact_dir / "result.json").read_text(encoding="utf-8"))
        model = json.loads((artifact_dir / "model_fingerprint.json").read_text(encoding="utf-8"))
        root = read_csv_row(artifact_dir / "root_processing_ledger.csv")
        presolve = read_csv_row(artifact_dir / "presolve_ledger.csv")
        size = read_csv_row(artifact_dir / "formulation_size_ledger.csv")
        numerical = read_csv_row(artifact_dir / "numerical_quality_ledger.csv")
        branch = read_csv_row(artifact_dir / "branching_policy_ledger.csv")
        continuous_count, integer_count, binary_count = lp_variable_type_counts(
            artifact_dir / "canonical_model.lp", int(size["original_columns"]))
        summary_rows.append({
            "state_id": state_id, "panel": frozen["panel"],
            "instance": frozen["instance"], "policy": args.policy,
            "process_cap_seconds": format(args.cap, ".17g"),
            "executable_sha256": executable_sha, "model_sha256": model["sha256"],
            "model_identity_match": str(
                model["sha256"] == frozen["canonical_model_fingerprint"]).lower(),
            "status": result["status"], "certificate": result["certificate"],
            "certificate_class": result["certificate_class"],
            "false_certificate": result["false_certificate"],
            "evidence_complete": completion["evidence_complete"],
            "cap_respected": completion["cap_respected"],
            "native_status": result["native_status"],
            "lower_bound": result["lower_bound"],
            "verified_upper_bound": result["verified_upper_bound"],
            "gap": result["gap"], "work": result["work"],
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
            "root_cut_count": root["root_cut_count"],
            "first_incumbent_work": result["first_incumbent_work"],
            "first_incumbent_time_seconds": result["first_incumbent_time_seconds"],
            "model_build_seconds": result["model_build_seconds"],
            "model_read_seconds": result["model_read_seconds"],
            "original_rows": size["original_rows"],
            "original_columns": size["original_columns"],
            "original_nonzeros": size["original_nonzeros"],
            "presolved_rows": presolve["rows"],
            "presolved_columns": presolve["columns"],
            "presolved_nonzeros": presolve["nonzeros"],
            "continuous_variables": continuous_count,
            "integer_variables": integer_count,
            "binary_variables": binary_count,
            "min_matrix": numerical["min_matrix"],
            "max_matrix": numerical["max_matrix"],
            "min_objective": numerical["min_objective"],
            "max_objective": numerical["max_objective"],
            "min_bound": numerical["min_bound"], "max_bound": numerical["max_bound"],
            "min_rhs": numerical["min_rhs"], "max_rhs": numerical["max_rhs"],
            "branch_priority_assignment_status": branch["assignment_status"],
            "failure_reason": result["failure_reason"],
            "artifact_dir": artifact_dir.relative_to(ROOT).as_posix(),
        })
        with summary_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(summary_rows)
        print(f"{state_id}: {result['status']} Work={result['work']}", flush=True)

    if len(summary_rows) != len(requested):
        raise RuntimeError("panel summary incomplete")
    if any(str(row["model_identity_match"]).lower() != "true" for row in summary_rows):
        raise RuntimeError("model identity mismatch")
    if any(str(row["evidence_complete"]).lower() != "true" for row in summary_rows):
        raise RuntimeError("incomplete evidence row")


if __name__ == "__main__":
    main()
