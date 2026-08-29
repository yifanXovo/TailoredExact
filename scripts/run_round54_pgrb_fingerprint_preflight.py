#!/usr/bin/env python3
"""Freeze expected fingerprints for the Round 53 P-GRB correction.

The probes construct and export each complete plain-Gurobi model under the
original Round 53 executable.  They are bounded model-discovery probes, not
benchmark rows and not correction solves.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import round46_common as round46


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_am_sf_inventory_route_round54"
ROUND53 = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"
CORRECTION = OUT / "round53_pgrb_certificate_correction"
RAW = CORRECTION / "local_raw" / "fingerprint_preflight"
MANIFEST = CORRECTION / "round53_pgrb_expected_fingerprints.json"
EXPECTED_EXE_SHA = (
    "b49cc5a5e631c6a8ce7a8bd4d0e6da44162800c97996494b1ee6a04071286c85")
PROBE_PROCESS_CAP = 5.0
PROBE_SOLVER_CAP = 0.001
ACCOUNTING_TOLERANCE = 1.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        value = value[0]
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def set_option(command: list[str], option: str, value: object) -> None:
    if option in command:
        round46.replace_option(command, option, value)
    else:
        command.extend([option, str(value).lower() if isinstance(value, bool)
                        else str(value)])


def objective_fingerprint(lp_path: Path) -> str:
    lines = lp_path.read_text(encoding="utf-8", errors="replace").splitlines()
    try:
        start = next(i for i, line in enumerate(lines)
                     if line.strip().lower() in {"minimize", "maximize"})
        end = next(i for i, line in enumerate(lines[start + 1:], start + 1)
                   if line.strip().lower().startswith("subject to"))
    except StopIteration as exc:
        raise RuntimeError(f"canonical LP objective section unavailable: {lp_path}") from exc
    canonical = "\n".join(line.rstrip() for line in lines[start:end]) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def command_for(row: dict[str, Any], run_dir: Path,
                executable: Path) -> list[str]:
    item = {"instance": row["instance_id"], "path": row["input_path"],
            "sha256": row["input_sha256"], "T": float(row["T"]),
            "V": int(row["V"]), "M": int(row["M"])}
    command = round46.pgrb_command(item, run_dir, PROBE_PROCESS_CAP, executable)
    round46.replace_option(command, "--T", float(row["T"]))
    round46.replace_option(command, "--process-wall-time-limit", PROBE_PROCESS_CAP)
    round46.replace_option(command, "--time-limit", PROBE_SOLVER_CAP)
    set_option(command, "--process-shutdown-margin", 0.0)
    set_option(command, "--gurobi-hga-start", False)
    round46.remove_option(command, "--round24-expected-gurobi-model-fingerprint")
    return command


def probe(row: dict[str, Any], executable: Path,
          executable_hash: str) -> dict[str, object]:
    run_dir = RAW / f"fingerprint__{row['instance_id']}"
    marker_path = run_dir / "completion_marker.json"
    result_path = run_dir / "result.json"
    lp_path = run_dir / "canonical.lp"
    if marker_path.is_file() and result_path.is_file() and lp_path.is_file():
        marker = read_json(marker_path)
        if (marker.get("complete") is True and
                marker.get("executable_sha256") == executable_hash and
                marker.get("input_sha256") == row["input_sha256"]):
            return dict(marker["entry"])
    if run_dir.exists() and any(run_dir.iterdir()):
        raise RuntimeError(f"incomplete preflight artifact retained: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=True)
    command = command_for(row, run_dir, executable)
    write_json(run_dir / "command.json", {
        "schema": "round54-pgrb-fingerprint-probe-command-v1",
        "official_benchmark_row": False,
        "purpose": "expected model fingerprint freeze only",
        "instance_id": row["instance_id"],
        "input_path": row["input_path"], "input_sha256": row["input_sha256"],
        "T": row["T"], "process_cap_seconds": PROBE_PROCESS_CAP,
        "solver_cap_seconds": PROBE_SOLVER_CAP,
        "executable_sha256": executable_hash, "command": command,
    })
    started = time.monotonic()
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    with (run_dir / "stdout.log").open("wb") as stdout, \
            (run_dir / "stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr,
                timeout=60, check=False)
            return_code, watchdog = completed.returncode, False
        except subprocess.TimeoutExpired:
            return_code, watchdog = -1, True
    if return_code != 0 or watchdog or not result_path.is_file() or not lp_path.is_file():
        raise RuntimeError(f"fingerprint probe failed: {row['instance_id']}")
    result = read_json(result_path)
    process_seconds = float(result.get("final_process_wall_time_seconds", 0.0))
    fingerprint = int(result.get("gurobi_model_fingerprint", 0))
    if (fingerprint == 0 or
            result.get("gurobi_native_domain_audit_passed") is not True or
            process_seconds > PROBE_PROCESS_CAP + ACCOUNTING_TOLERANCE):
        raise RuntimeError(f"fingerprint probe audit failed: {row['instance_id']}")
    entry: dict[str, object] = {
        "instance_id": row["instance_id"], "input_path": row["input_path"],
        "input_sha256": row["input_sha256"], "T": row["T"],
        "expected_gurobi_model_fingerprint": fingerprint,
        "canonical_model_sha256": sha256(lp_path),
        "objective_fingerprint_sha256": objective_fingerprint(lp_path),
        "variable_row_domain_identity": {
            "num_vars": int(result["gurobi_num_vars"]),
            "num_rows": int(result["gurobi_num_constrs"]),
            "num_nonzeros": int(result["gurobi_num_nzs"]),
            "num_binary": int(result["gurobi_num_bin_vars"]),
            "num_integer": int(result["gurobi_num_int_vars"]),
            "num_continuous": int(result["gurobi_num_cont_vars"]),
            "objective_sense": int(result["gurobi_objective_sense"]),
            "native_names_match": result["gurobi_native_variable_names_match"],
            "native_types_match": result["gurobi_native_variable_types_match"],
            "native_bounds_match": result["gurobi_native_variable_bounds_match"],
            "native_domain_audit_passed": result["gurobi_native_domain_audit_passed"],
        },
        "executable_sha256": executable_hash,
        "solver": {"Presolve": "Auto", "Seed": 0, "Threads": 1,
                   "MIPGap": 0.0, "MIPGapAbs": 0.0},
        "probe_process_cap_seconds": PROBE_PROCESS_CAP,
        "probe_solver_cap_seconds": PROBE_SOLVER_CAP,
        "probe_process_seconds": process_seconds,
        "raw_probe_path": run_dir.relative_to(ROOT).as_posix(),
    }
    write_json(marker_path, {
        "schema": "round54-pgrb-fingerprint-probe-completion-v1",
        "complete": True, "official_benchmark_row": False,
        "input_sha256": row["input_sha256"],
        "executable_sha256": executable_hash, "entry": entry,
    })
    print(f"fingerprint {row['instance_id']} = {fingerprint}", flush=True)
    return entry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    executable = args.executable.resolve()
    if not executable.is_file():
        raise RuntimeError("Round 53 official executable unavailable")
    executable_hash = sha256(executable)
    if executable_hash != EXPECTED_EXE_SHA:
        raise RuntimeError("Round 53 official executable hash mismatch")
    stage0 = read_json(OUT / "stage0_freeze_manifest.json")
    if stage0.get("round54_performance_results_inspected_before_freeze") is not False:
        raise RuntimeError("Stage 0 freeze is invalid")
    sealed = read_json(ROUND53 / "sealed_v12_instance_manifest.json")
    rows = list(sealed["rows"])
    if len(rows) != 12:
        raise RuntimeError("Round 53 sealed manifest must contain 12 inputs")
    entries = [probe(row, executable, executable_hash) for row in rows]
    created = datetime.now(timezone.utc).isoformat()
    source_commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    write_json(MANIFEST, {
        "schema": "round54-round53-pgrb-expected-fingerprints-v1",
        "created_at_utc": created,
        "created_before_any_round54_correction_solve": True,
        "stage0_commit": source_commit,
        "source_round53_panel": (
            "results/gf_k1_f0_callback_isolation_round53/sealed_v12_instance_manifest.json"),
        "source_round53_panel_sha256": sha256(
            ROUND53 / "sealed_v12_instance_manifest.json"),
        "executable_path": executable.relative_to(ROOT).as_posix(),
        "executable_sha256": executable_hash,
        "solver": {"version": "13.0.2", "Presolve": "Auto", "Seed": 0,
                   "Threads": 1, "MIPGap": 0.0, "MIPGapAbs": 0.0},
        "row_count": len(entries), "entries": entries,
        "correction_solves_started": False,
        "preflight_is_benchmark_evidence": False,
        "machine": platform.node(),
    })
    print(json.dumps({"fingerprints": len(entries),
                      "manifest": MANIFEST.relative_to(ROOT).as_posix(),
                      "executable_sha256": executable_hash}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
