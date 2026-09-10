#!/usr/bin/env python3
"""Run one resumable frozen Round 53 fixed-interval panel."""

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


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def one_csv(path: Path) -> dict[str, str]:
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))
    if len(rows) != 1:
        raise RuntimeError(f"expected one row in {path}, found {len(rows)}")
    return rows[0]


def boolean(value: object) -> bool:
    return value is True or str(value).lower() in {"1", "true"}


def normalized_gi(path: Path, upper: float, horizon: float,
                  exact: bool, process_seconds: float) -> float:
    points: list[tuple[float, float]] = []
    for row in csv.DictReader(path.open(newline="", encoding="utf-8-sig")):
        if not boolean(row["bound_available"]):
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


FIELDS = [
    "state_id", "policy_label", "policy", "role", "state_kind",
    "process_cap_seconds", "executable_sha256", "input_sha256",
    "model_sha256", "status", "certificate", "certificate_class",
    "false_certificate", "engineering_gate", "evidence_complete",
    "cap_respected", "native_status", "lower_bound", "verified_upper_bound",
    "gap", "gi_common_horizon", "work", "solver_time_seconds",
    "process_time_seconds", "nodes", "simplex_iterations",
    "average_iterations_per_node", "peak_memory_gb",
    "root_relaxation_bound_available", "root_relaxation_bound",
    "final_root_cut_bound_available", "final_root_cut_bound", "root_work",
    "root_time_seconds", "root_simplex_iterations", "first_incumbent_work",
    "first_incumbent_time_seconds", "model_build_seconds",
    "model_read_seconds", "original_rows", "original_columns",
    "original_nonzeros", "subset_duration_policy", "subset_duration_rows",
    "subset_duration_first_row_id", "subset_duration_last_row_id",
    "subset_duration_min_m", "subset_duration_max_m",
    "historical_m_may_be_unsafe", "tailored_cut_policy",
    "round53_callback_mode", "callback_active", "cbcut_symbol_loaded",
    "cblazy_symbol_loaded", "precrush_requested", "precrush_effective",
    "precrush_roundtrip_valid", "mipnode_calls", "mipnode_status_reads",
    "relaxation_vector_reads", "separator_calls", "cut_submission_calls",
    "callback_disabled_after_failure", "callback_calls",
    "root_callback_calls", "tree_callback_calls",
    "nonoptimal_mipnode_callbacks", "relaxation_vector_failures",
    "cuts_generated", "cuts_violated", "cuts_selected", "cuts_added",
    "duplicate_rejections", "dominated_rejections",
    "nonviolated_rejections", "invalid_rejections", "submission_failures",
    "callback_failures", "cut_pool_size", "callback_overhead_seconds",
    "cut_infrastructure_gate", "failure_reason", "artifact_dir"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--policy-label", required=True)
    parser.add_argument("--states", required=True)
    parser.add_argument("--cap", required=True, type=float)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--gurobi-home", default="D:/gurobi1302/win64")
    args = parser.parse_args()
    if not 0.0 < args.cap <= 3600.0:
        raise RuntimeError("ordinary process cap must be in (0,3600]")
    executable = args.executable.resolve()
    executable_hash = sha256(executable)
    frozen_map = {row["state_id"]: row for row in csv.DictReader(
        MANIFEST.open(newline="", encoding="utf-8-sig"))}
    state_map = {row["state_id"]: row for row in csv.DictReader(
        RECONSTRUCTION.open(newline="", encoding="utf-8-sig"))}
    states = [value.strip() for value in args.states.split(",")
              if value.strip()]
    if len(states) != len(set(states)) or any(
            value not in frozen_map or value not in state_map
            for value in states):
        raise RuntimeError("unknown or duplicate frozen state")
    run_root = args.run_root.resolve()
    summary = args.summary.resolve()
    run_root.mkdir(parents=True, exist_ok=True)
    summary.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for state_id in states:
        frozen, state = frozen_map[state_id], state_map[state_id]
        artifact = run_root / f"{state_id}__{args.policy_label}"
        completion_path = artifact / "completion_marker.json"
        reusable = False
        if completion_path.is_file() and (artifact / "command.json").is_file():
            completion = read_json(completion_path)
            command = read_json(artifact / "command.json")
            reusable = (completion.get("evidence_complete") is True and
                        completion.get("cap_respected") is True and
                        command.get("policy") == args.policy and
                        command.get("executable_sha256") == executable_hash and
                        abs(float(command.get("process_cap_seconds", -1)) -
                            args.cap) <= 1e-9)
        if not reusable:
            if artifact.exists():
                raise RuntimeError(f"stale script-owned artifact: {artifact}")
            artifact.mkdir(parents=True)
            command = [
                str(executable), "--mode", "solve", "--state-id", state_id,
                "--input", str(ROOT / frozen["input_path"]),
                "--artifact-dir", str(artifact), "--policy", args.policy,
                "--gurobi-home", args.gurobi_home,
                "--gamma-lower", state["gamma_lower"],
                "--gamma-upper", state["gamma_upper"],
                "--cutoff", state["verified_cutoff"], "--process-cap",
                format(args.cap, ".17g"), "--T", state["route_time_limit"],
                "--pickup-time", "60", "--drop-time", "60"]
            completed = subprocess.run(
                command, cwd=ROOT, timeout=max(60.0, args.cap + 45.0),
                check=False)
            if completed.returncode != 0:
                raise RuntimeError(
                    f"state {state_id} returned {completed.returncode}")
        completion = read_json(completion_path)
        result = read_json(artifact / "result.json")
        model = read_json(artifact / "model_fingerprint.json")
        size = one_csv(artifact / "formulation_size_ledger.csv")
        cut = one_csv(artifact / "cut_lifecycle_ledger.csv")
        gi = normalized_gi(
            artifact / "mip_progress.csv", float(result["verified_upper_bound"]),
            args.cap, bool(result["certificate"]),
            float(result["process_time_seconds"]))
        row: dict[str, object] = {
            "state_id": state_id, "policy_label": args.policy_label,
            "policy": args.policy, "role": frozen["historical_role"],
            "state_kind": frozen["state_kind"],
            "process_cap_seconds": format(args.cap, ".17g"),
            "executable_sha256": executable_hash,
            "input_sha256": frozen["input_sha256"],
            "model_sha256": model["sha256"],
            "evidence_complete": completion["evidence_complete"],
            "cap_respected": completion["cap_respected"],
            "gi_common_horizon": gi,
            "original_rows": size["original_rows"],
            "original_columns": size["original_columns"],
            "original_nonzeros": size["original_nonzeros"],
            "subset_duration_policy": model["round51_subset_duration_big_m"],
            "subset_duration_rows": model["round51_subset_duration_rows"],
            "subset_duration_first_row_id":
                model["round51_subset_duration_first_row_id"],
            "subset_duration_last_row_id":
                model["round51_subset_duration_last_row_id"],
            "subset_duration_min_m": model["round51_subset_duration_min_m"],
            "subset_duration_max_m": model["round51_subset_duration_max_m"],
            "historical_m_may_be_unsafe":
                model["round51_historical_m_may_be_unsafe"],
            "callback_active": cut["callback_active"],
            "cbcut_symbol_loaded": cut["cbcut_symbol_loaded"],
            "cblazy_symbol_loaded": cut["cblazy_symbol_loaded"],
            "precrush_requested": cut["precrush_requested"],
            "precrush_effective": cut["precrush_effective"],
            "precrush_roundtrip_valid": cut["precrush_roundtrip_valid"],
            "mipnode_calls": cut["mipnode_calls"],
            "mipnode_status_reads": cut["mipnode_status_reads"],
            "relaxation_vector_reads": cut["relaxation_vector_reads"],
            "separator_calls": cut["separator_calls"],
            "cut_submission_calls": cut["cut_submission_calls"],
            "callback_disabled_after_failure":
                cut["callback_disabled_after_failure"],
            "callback_calls": cut["callback_calls"],
            "root_callback_calls": cut["root_callback_calls"],
            "tree_callback_calls": cut["tree_callback_calls"],
            "nonoptimal_mipnode_callbacks": cut[
                "nonoptimal_mipnode_callbacks"],
            "relaxation_vector_failures": cut["relaxation_vector_failures"],
            "cuts_generated": cut["generated"],
            "cuts_violated": cut["violated"],
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
            "artifact_dir": artifact.relative_to(ROOT).as_posix()}
        for key in (
                "status", "certificate", "certificate_class",
                "false_certificate", "engineering_gate", "native_status",
                "lower_bound", "verified_upper_bound", "gap", "work",
                "solver_time_seconds", "process_time_seconds", "nodes",
                "simplex_iterations", "average_iterations_per_node",
                "peak_memory_gb", "root_relaxation_bound_available",
                "root_relaxation_bound", "final_root_cut_bound_available",
                "final_root_cut_bound", "root_work", "root_time_seconds",
                "root_simplex_iterations", "first_incumbent_work",
                "first_incumbent_time_seconds", "model_build_seconds",
                "model_read_seconds", "tailored_cut_policy",
                "round53_callback_mode", "failure_reason"):
            row[key] = result[key]
        rows.append(row)
        with summary.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS,
                                    lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(f"{state_id}: {result['status']} Work={result['work']} "
              f"mode={result['round53_callback_mode']}", flush=True)
    for row in rows:
        if not (boolean(row["evidence_complete"]) and
                boolean(row["cap_respected"]) and
                boolean(row["engineering_gate"]) and
                not boolean(row["false_certificate"])):
            raise RuntimeError(f"evidence gate failed: {row['state_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
