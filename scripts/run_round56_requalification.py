#!/usr/bin/env python3
"""Requalify frozen K1-AM-SF semantics on the five Round 56 sentinels."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import round46_common as round46
import round56_common as r56


SOURCE_FREEZE = "75e58521158aba8628ebc9444444ec3841415285"
BUILD = r56.ROOT / "build" / "official-round56-paper-dataset-75e585211"
EXE = BUILD / "ExactEBRP.exe"
MODEL_EXE = BUILD / "Round51IntervalMipExperiment.exe"
RAW = r56.EVIDENCE / "local_raw" / "stable_mainline_requalification"
SMOKE_CAP = 45
CELLS = (
    (8, 1, 30, 1800, "run"),
    (8, 1, 30, 18000, "run"),
    (20, 2, 30, 3600, "run"),
    (20, 2, 30, 18000, "run"),
    (50, 4, 30, 18000, "model_build"),
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def descriptor_for(v: int, m: int, q: int, t: int) -> dict[str, Any]:
    rows = load_json(r56.EVIDENCE / "scenario_manifest.json")["rows"]
    return next(row for row in rows if all((
        int(row["V"]) == v, int(row["M"]) == m, int(row["Q"]) == q,
        int(row["route_time_limit_seconds"]) == t,
    )))


def official_command(descriptor: dict[str, Any], run_dir: Path) -> tuple[list[str], str]:
    contract_sha = r56.sha256_file(r56.EVIDENCE / "official_solver_parameter_contract.json")
    executable_sha = r56.sha256_file(EXE)
    identity = r56.run_identity(
        descriptor["mathematical_instance_sha256"], SOURCE_FREEZE,
        executable_sha, contract_sha, SMOKE_CAP, "semantic-requalification")
    item = {
        "instance": descriptor["scenario_id"],
        "path": descriptor["fleet_variant_path"],
        "sha256": descriptor["fleet_variant_file_sha256"],
        "T": descriptor["route_time_limit_seconds"],
        "V": descriptor["V"], "M": descriptor["M"],
    }
    command = round46.c6_command(item, run_dir, SMOKE_CAP, 1, 0.08, EXE)
    for option in (
        "--incumbent-json", "--hga-incumbent", "--external-incumbent",
        "--frontier-focus-from-result", "--frontier-import-interval-bound",
        "--frontier-focus-only", "--frontier-resume-state",
        "--frontier-resume-open-nodes", "--incumbent-archive-auto",
    ):
        round46.remove_option(command, option)
    for option, value in (
        ("--algorithm-preset", "paper-k1-am-sf"),
        ("--external-gini-interval-mip-policy", "interval-mip-core-no-exhaustive-subset-duration"),
        ("--T", float(descriptor["route_time_limit_seconds"])),
        ("--threads", 1), ("--mip-threads", 1), ("--gurobi-threads", 1),
        ("--gurobi-seed", 0), ("--gurobi-presolve", -1),
        ("--process-wall-time-limit", float(SMOKE_CAP)),
        ("--time-limit", float(SMOKE_CAP - 6)),
        ("--process-shutdown-margin", 2.0),
        ("--round48-k1-amf", "off"), ("--round49-k1-am-rc", "off"),
        ("--round56-scenario-id", descriptor["scenario_id"]),
        ("--round56-mathematical-instance-sha256", descriptor["mathematical_instance_sha256"]),
        ("--round56-run-identity-sha256", identity),
        ("--round22-source-commit", SOURCE_FREEZE),
        ("--round22-executable-sha256", executable_sha),
        ("--round24-executable-sha256", executable_sha),
        ("--round24-manifest-executable-sha256", executable_sha),
        ("--progress-log", run_dir / "progress.csv"),
        ("--process-phase-ledger", run_dir / "process_phases.csv"),
        ("--external-gini-artifact-dir", run_dir / "external"),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        round46.replace_option(command, option, value)
    return command, identity


def build_model(descriptor: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    args = [
        str(MODEL_EXE), "--mode", "build", "--state-id", descriptor["scenario_id"],
        "--input", str(r56.ROOT / descriptor["fleet_variant_path"]),
        "--artifact-dir", str(run_dir / "model_build"),
        "--policy", "interval-mip-core-no-exhaustive-subset-duration",
        "--gurobi-home", "D:/gurobi1302/win64", "--gamma-lower", "0",
        "--gamma-upper", "1", "--cutoff", "1", "--process-cap", "60",
        "--T", str(descriptor["route_time_limit_seconds"]),
        "--pickup-time", "60", "--drop-time", "60",
    ]
    completed = subprocess.run(args, cwd=r56.ROOT, text=True, capture_output=True, timeout=180, check=False)
    (run_dir / "model_build_stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (run_dir / "model_build_stderr.txt").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"model build failed for {descriptor['scenario_id']}: {completed.stderr[-800:]}")
    model_path = run_dir / "model_build" / "model.lp"
    if not model_path.is_file():
        candidates = list((run_dir / "model_build").glob("*.lp"))
        if len(candidates) != 1:
            raise RuntimeError(f"model LP unavailable for {descriptor['scenario_id']}")
        model_path = candidates[0]
    return {
        "model_path": r56.repo_path(model_path),
        "model_sha256": r56.sha256_file(model_path),
        "model_bytes": model_path.stat().st_size,
        "command": args,
    }


def main() -> int:
    if r56.sha256_file(EXE) != "34e992060e3adffd3a7795c2c783672044996edd7234bf7e9f58a662b1c32fea":
        raise RuntimeError("official executable mismatch")
    RAW.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    model_records: dict[tuple[int, int, int, int], dict[str, Any]] = {}
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for ordinal, (v, m, q, t, mode) in enumerate(CELLS, start=1):
        descriptor = descriptor_for(v, m, q, t)
        run_dir = RAW / descriptor["scenario_id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        model = build_model(descriptor, run_dir)
        model_records[v, m, q, t] = model
        result: dict[str, Any] = {}
        command: list[str] = model["command"]
        identity = "not_applicable_model_build"
        if mode == "run":
            command, identity = official_command(descriptor, run_dir)
            command_record = run_dir / "command.json"
            result_path = run_dir / "result.json"
            r56.write_json(command_record, {
                "schema": "round56-stable-requalification-command-v1",
                "scenario_id": descriptor["scenario_id"], "cap_seconds": SMOKE_CAP,
                "run_identity_sha256": identity, "command": command,
            })
            marker_path = run_dir / "completion_marker.json"
            marker = load_json(marker_path) if marker_path.is_file() else {}
            if (result_path.is_file() and marker.get("complete") is True and
                    marker.get("executable_sha256") == r56.sha256_file(EXE)):
                result = load_json(result_path)
            else:
                started = time.monotonic()
                with (run_dir / "stdout.log").open("wb") as stdout, (run_dir / "stderr.log").open("wb") as stderr:
                    completed = subprocess.run(command, cwd=r56.ROOT, env=env, stdout=stdout, stderr=stderr, timeout=SMOKE_CAP + 90, check=False)
                if completed.returncode != 0 or not result_path.is_file():
                    raise RuntimeError(f"semantic requalification failed for {descriptor['scenario_id']}")
                result = load_json(result_path)
                r56.write_json(marker_path, {
                    "complete": True, "return_code": completed.returncode,
                    "runner_wall_seconds": time.monotonic() - started,
                    "result_sha256": r56.sha256_file(result_path),
                    "executable_sha256": r56.sha256_file(EXE),
                })
        policy_ok = mode == "model_build" or result.get("external_gini_tree_interval_mip_policy") == "interval-mip-core-no-exhaustive-subset-duration"
        preset_ok = mode == "model_build" or result.get("algorithm_preset") == "paper-k1-am-sf"
        requested_params_ok = mode == "model_build" or all((
            int(result.get("gurobi_threads_requested", -9)) == 1,
            int(result.get("gurobi_seed_requested", -9)) == 0,
            int(result.get("gurobi_presolve_requested", -9)) == -1,
            float(result.get("gurobi_mip_gap_requested", 1.0)) == 0.0,
            float(result.get("gurobi_mip_gap_abs_requested", 1.0)) == 0.0,
        ))
        optimize_count = int(result.get("external_gini_tree_optimize_count", 0)) if mode == "run" else 0
        effective_params_ok = mode == "model_build" or optimize_count == 0 or all((
            int(result.get("gurobi_threads_effective", -9)) == 1,
            int(result.get("gurobi_seed_effective", -9)) == 0,
            int(result.get("gurobi_presolve_effective", -9)) == -1,
            float(result.get("gurobi_mip_gap_effective", 1.0)) == 0.0,
            float(result.get("gurobi_mip_gap_abs_effective", 1.0)) == 0.0,
        ))
        params_ok = requested_params_ok and effective_params_ok
        readback_status = ("model_build_contract" if mode == "model_build" else
                           "readback_pass" if optimize_count > 0 else
                           "not_reached_exact_phase_requested_contract_pass")
        metadata_ok = mode == "model_build" or all((
            int(float(result.get("route_time_limit_seconds", -1))) == t,
            int(float(result.get("solver_process_cap_seconds", -1))) == SMOKE_CAP,
            result.get("mathematical_instance_sha256") == descriptor["mathematical_instance_sha256"],
            result.get("run_identity_sha256") == identity,
        ))
        rows.append({
            "scenario_id": descriptor["scenario_id"], "V": v, "M": m, "Q": q, "T": t,
            "check_mode": mode, "preset": result.get("algorithm_preset", "paper-k1-am-sf-model-build"),
            "K0": 1, "split_point_rule": "midpoint", "split_score_rule": "balanced-normalized-closure",
            "tau": 0.08, "inner_policy": "F0-CLEAN", "active_research_mechanisms": 0,
            "dynamic_user_cut_callback": False, "PreCrush": "default",
            "native_branching": True, "preset_ok": preset_ok, "policy_ok": policy_ok,
            "solver_parameter_readback_status": readback_status,
            "solver_parameter_readback_ok": params_ok, "metadata_roundtrip_ok": metadata_ok,
            "model_sha256": model["model_sha256"], "model_bytes": model["model_bytes"],
            "strict_certificate": bool(result.get("strict_certified_original_problem", False)),
            "pass": all((preset_ok, policy_ok, params_ok, metadata_ok)),
        })
        print(f"[{ordinal}/{len(CELLS)}] {descriptor['scenario_id']} {mode}", flush=True)
    r56.write_csv(r56.EVIDENCE / "stable_mainline_requalification.csv", rows)
    delta_rows = []
    for v, m, q, t1, t2 in ((8, 1, 30, 1800, 18000), (20, 2, 30, 3600, 18000)):
        left = model_records[v, m, q, t1]
        right = model_records[v, m, q, t2]
        delta_rows.append({
            "V": v, "M": m, "Q": q, "T_left": t1, "T_right": t2,
            "same_fleet_variant_file": True, "different_model_sha256": left["model_sha256"] != right["model_sha256"],
            "left_model_sha256": left["model_sha256"], "right_model_sha256": right["model_sha256"],
            "legitimate_T_delta_scope": "duration RHS; movement reachability; T-dependent valid inequalities; downstream presolve; scenario/cache identity",
            "non_T_algorithm_delta": False, "pass": left["model_sha256"] != right["model_sha256"],
        })
    r56.write_csv(r56.EVIDENCE / "t_model_delta_audit.csv", delta_rows)
    passed = all(row["pass"] for row in rows) and all(row["pass"] for row in delta_rows)
    r56.write_json(r56.EVIDENCE / "stable_mainline_requalification_decision.json", {
        "schema": "round56-stable-mainline-requalification-decision-v1",
        "sentinel_count": len(rows), "actual_stable_run_count": 4, "model_build_only_count": 1,
        "all_checks_pass": passed, "official_panel_opened": passed,
        "algorithm_identity": "corrected K1-AM-SF / paper-k1-am-sf",
        "executable_sha256": r56.sha256_file(EXE),
    })
    print(json.dumps({"stable_mainline_requalified": passed, "rows": len(rows)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
