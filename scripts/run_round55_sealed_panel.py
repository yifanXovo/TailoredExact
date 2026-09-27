#!/usr/bin/env python3
"""Freeze P-GRB identities and run the hard-gated Round 55 sealed panel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pgrb_fingerprint_pipeline as fingerprint
import round46_common as round46


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_am_sf_station_state_chain_round55"
MANIFEST = EVIDENCE / "sealed_generalization_manifest.json"
OPENING = EVIDENCE / "sealed_generalization_opening_audit.json"
FINGERPRINT_FREEZE = EVIDENCE / "sealed_pgrb_fingerprint_freeze.json"
RUNS = EVIDENCE / "local_raw" / "sealed_generalization"
PROBES = EVIDENCE / "local_raw" / "sealed_pgrb_fingerprint_probe"
ARMS = {
    "P-GRB": {"preset": "plain-gurobi", "policy": "not_applicable"},
    "K1-AM-SF": {
        "preset": "paper-k1-am-sf",
        "policy": "interval-mip-core-no-exhaustive-subset-duration",
    },
    "K1-AM-SF-CANDIDATE": {
        "preset": "research-k1-am-sf-vdp", "policy": "round55-vd-p",
    },
}
CAP_BY_V = {12: 3600, 20: 3600, 50: 7200}


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


def rows(selected_sizes: set[int] | None,
         selected_instances: set[str] | None) -> list[dict[str, Any]]:
    output = []
    for raw in read_json(MANIFEST)["rows"]:
        if selected_sizes is not None and int(raw["V"]) not in selected_sizes:
            continue
        if selected_instances is not None and raw["instance_id"] not in selected_instances:
            continue
        output.append(dict(raw))
    known = {row["instance_id"] for row in output}
    if selected_instances is not None and known != selected_instances:
        raise RuntimeError("requested sealed instance is not frozen")
    return output


def base_item(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "instance": row["instance_id"], "path": row["input_path"],
        "sha256": row["input_sha256"], "T": float(row["T"]),
        "V": int(row["V"]), "M": int(row["M"]),
    }


def common_k1(command: list[str], row: dict[str, Any], arm: str,
              run_dir: Path, cap: int) -> list[str]:
    round46.replace_option(command, "--algorithm-preset", ARMS[arm]["preset"])
    round46.replace_option(command, "--external-gini-interval-mip-policy",
                           ARMS[arm]["policy"])
    round46.replace_option(command, "--T", float(row["T"]))
    round46.replace_option(command, "--round47-c6-adaptive-mass", "adaptive-mass")
    round46.replace_option(command, "--round47-c6-adaptive-mass-tau", 0.08)
    round46.replace_option(command, "--round48-k1-amf", "off")
    round46.replace_option(command, "--round49-k1-am-rc", "off")
    round46.replace_option(command, "--process-shutdown-margin", 2)
    round46.replace_option(command, "--time-limit", max(1, cap - 6))
    round46.replace_option(command, "--process-wall-time-limit", cap)
    round46.replace_option(command, "--primal-heuristic-generation-log",
                           run_dir / "hga_generations.csv")
    round46.replace_option(command, "--heuristic-candidates-csv",
                           run_dir / "heuristic_candidates.csv")
    return command


def pgrb_command(row: dict[str, Any], run_dir: Path, executable: Path,
                 cap: int, expected: int | None, probe: bool) -> list[str]:
    command = round46.pgrb_command(base_item(row), run_dir, cap, executable)
    round46.replace_option(command, "--T", float(row["T"]))
    round46.replace_option(command, "--process-shutdown-margin", 2)
    if probe:
        round46.replace_option(command, "--gurobi-hga-start", False)
        round46.replace_option(command, "--time-limit", 1)
    elif expected is not None:
        round46.replace_option(command, "--round24-expected-gurobi-model-fingerprint",
                               expected)
    return command


def execute(command: list[str], run_dir: Path, cap: int) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    with (run_dir / "stdout.log").open("wb") as stdout, \
            (run_dir / "stderr.log").open("wb") as stderr:
        try:
            process = subprocess.run(command, cwd=ROOT, env=environment,
                                     stdout=stdout, stderr=stderr,
                                     timeout=cap + 90, check=False)
            return_code, watchdog = process.returncode, False
        except subprocess.TimeoutExpired:
            return_code, watchdog = -1, True
    result_path = run_dir / "result.json"
    if return_code != 0 or watchdog or not result_path.exists():
        raise RuntimeError(f"sealed subprocess failed in {run_dir}")
    return read_json(result_path)


def freeze_one(row: dict[str, Any], executable: Path,
               executable_hash: str) -> dict[str, Any]:
    run_dir = PROBES / row["instance_id"]
    result_path = run_dir / "result.json"
    canonical = run_dir / "canonical.lp"
    if not (result_path.exists() and canonical.exists()):
        command = pgrb_command(row, run_dir, executable, 120, None, True)
        write_json(run_dir / "command.json", {
            "schema": "round55-sealed-pgrb-probe-command-v1",
            "instance_id": row["instance_id"], "performance_result": False,
            "probe_cap_seconds": 120, "executable_sha256": executable_hash,
            "command": command,
        })
        result = execute(command, run_dir, 120)
    else:
        result = read_json(result_path)
    domain = {
        "native_domain_audit_passed": truth(result.get("gurobi_native_domain_audit_passed")),
        "native_variables": result.get("gurobi_native_variable_count"),
        "native_rows": result.get("gurobi_native_constraint_count"),
        "binary_variables": result.get("gurobi_native_binary_variable_count"),
        "integer_variables": result.get("gurobi_native_integer_variable_count"),
    }
    return fingerprint.freeze_entry(
        instance_id=row["instance_id"], input_path=row["input_path"],
        input_sha256=row["input_sha256"], time_limit=float(row["T"]),
        executable_sha256=executable_hash,
        native_fingerprint=int(result.get("gurobi_model_fingerprint", 0)),
        canonical_lp=canonical, native_domain=domain,
        solver_contract={"Presolve": "Auto", "Seed": 0, "Threads": 1,
                         "MIPGap": 0, "MIPGapAbs": 0},
        probe_metadata={"performance_result": False, "probe_cap_seconds": 120,
                        "probe_result_sha256": sha256(result_path)},
    )


def truth(value: object) -> bool:
    return value is True or str(value).lower() in {"1", "true"}


def require_opening(executable_hash: str) -> dict[str, Any]:
    if not OPENING.exists():
        raise RuntimeError("sealed opening audit is absent")
    opening = read_json(OPENING)
    if not (truth(opening.get("opening_authorized")) and
            truth(opening.get("source_frozen")) and
            truth(opening.get("k1_integration_passed")) and
            opening.get("executable_sha256") == executable_hash and
            FINGERPRINT_FREEZE.exists() and
            opening.get("pgrb_fingerprint_freeze_sha256") == sha256(FINGERPRINT_FREEZE)):
        raise RuntimeError("sealed opening gate failed")
    return opening


def run_one(row: dict[str, Any], arm: str, executable: Path,
            executable_hash: str, fingerprint_entries: dict[str, dict[str, Any]]) -> dict[str, object]:
    cap = CAP_BY_V[int(row["V"])]
    run_id = f"{row['instance_id']}__{arm}__{cap}s"
    run_dir = RUNS / run_id
    marker_path = run_dir / "completion_marker.json"
    result_path = run_dir / "result.json"
    if marker_path.exists() and result_path.exists():
        marker = read_json(marker_path)
        if (truth(marker.get("complete")) and marker.get("executable_sha256") == executable_hash and
                int(marker.get("cap_seconds", -1)) == cap and marker.get("arm") == arm):
            return {"run_id": run_id, "resumed": True}
    if arm == "P-GRB":
        entry = fingerprint_entries[row["instance_id"]]
        command = pgrb_command(row, run_dir, executable, cap,
                               int(entry["expected_gurobi_model_fingerprint"]), False)
    else:
        command = round46.c6_command(base_item(row), run_dir, cap, 1, 0.08, executable)
        common_k1(command, row, arm, run_dir, cap)
    write_json(run_dir / "command.json", {
        "schema": "round55-sealed-panel-command-v1", "run_id": run_id,
        "instance_id": row["instance_id"], "V": row["V"], "M": row["M"],
        "Q": row["Q"], "T": row["T"], "difficulty_configuration": row["difficulty_configuration"],
        "input_path": row["input_path"], "input_sha256": row["input_sha256"],
        "arm": arm, "preset": ARMS[arm]["preset"],
        "inner_policy": ARMS[arm]["policy"], "cap_seconds": cap,
        "executable_sha256": executable_hash, "command": command,
    })
    started = time.monotonic()
    result = execute(command, run_dir, cap)
    process_seconds = float(result.get("final_process_wall_time_seconds", 0.0))
    if process_seconds > cap + 1e-6:
        raise RuntimeError(f"process cap exceeded: {run_id}")
    binding_passed, binding_reason = True, "not_applicable"
    if arm == "P-GRB":
        entry = fingerprint_entries[row["instance_id"]]
        binding_passed, binding_reason = fingerprint.audit_binding(
            entry, input_file=ROOT / row["input_path"], executable=executable,
            canonical_lp=run_dir / "canonical.lp", result=result)
        if not binding_passed:
            raise RuntimeError(f"P-GRB fingerprint binding failed: {run_id}: {binding_reason}")
    else:
        if (result.get("algorithm_preset") != ARMS[arm]["preset"] or
                result.get("external_gini_tree_interval_mip_policy") != ARMS[arm]["policy"]):
            raise RuntimeError(f"K1 identity failed: {run_id}")
    write_json(marker_path, {
        "schema": "round55-sealed-panel-completion-v1", "complete": True,
        "run_id": run_id, "instance_id": row["instance_id"], "arm": arm,
        "cap_seconds": cap, "process_seconds": process_seconds,
        "cap_respected": True, "executable_sha256": executable_hash,
        "result_sha256": sha256(result_path),
        "pgrb_fingerprint_binding_passed": binding_passed,
        "pgrb_fingerprint_binding_reason": binding_reason,
        "runner_wall_seconds": time.monotonic() - started,
    })
    return {"run_id": run_id, "resumed": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("freeze-pgrb", "run"), required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--sizes")
    parser.add_argument("--instances")
    parser.add_argument("--arms", default="P-GRB,K1-AM-SF,K1-AM-SF-CANDIDATE")
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    executable = (args.executable if args.executable.is_absolute()
                  else ROOT / args.executable).resolve()
    executable_hash = sha256(executable)
    selected_sizes = None if not args.sizes else {
        int(value.removeprefix("V")) for value in args.sizes.split(",")}
    selected_instances = None if not args.instances else {
        value.strip() for value in args.instances.split(",") if value.strip()}
    panel = rows(selected_sizes, selected_instances)
    if args.mode == "freeze-pgrb":
        if FINGERPRINT_FREEZE.exists():
            raise RuntimeError("sealed P-GRB fingerprint freeze already exists")
        entries = []
        with ThreadPoolExecutor(max_workers=max(1, min(args.jobs, len(panel)))) as pool:
            futures = {pool.submit(freeze_one, row, executable, executable_hash): row["instance_id"]
                       for row in panel}
            for ordinal, future in enumerate(as_completed(futures), start=1):
                entries.append(future.result())
                print(f"[{ordinal}/{len(panel)}] fingerprint/{futures[future]}", flush=True)
        order = {row["instance_id"]: i for i, row in enumerate(panel)}
        entries.sort(key=lambda entry: order[entry["instance_id"]])
        write_json(FINGERPRINT_FREEZE, {
            "schema": "round55-sealed-pgrb-fingerprint-freeze-v1",
            "created_before_sealed_performance_results": True,
            "manifest_sha256": sha256(MANIFEST),
            "executable_sha256": executable_hash, "entry_count": len(entries),
            "entries": entries,
        })
        print(sha256(FINGERPRINT_FREEZE))
        return 0
    require_opening(executable_hash)
    freeze = read_json(FINGERPRINT_FREEZE)
    fingerprint_entries = {entry["instance_id"]: entry for entry in freeze["entries"]}
    arms = [value.strip() for value in args.arms.split(",") if value.strip()]
    if any(arm not in ARMS for arm in arms):
        raise RuntimeError("unknown sealed arm")
    tasks = [(row, arm) for row in panel for arm in arms]
    with ThreadPoolExecutor(max_workers=max(1, min(args.jobs, len(tasks)))) as pool:
        futures = {pool.submit(run_one, row, arm, executable, executable_hash,
                               fingerprint_entries): (row["instance_id"], arm)
                   for row, arm in tasks}
        for ordinal, future in enumerate(as_completed(futures), start=1):
            instance, arm = futures[future]
            status = future.result()
            print(f"[{ordinal}/{len(tasks)}] {arm}/{instance}"
                  f"{' (resumed)' if status['resumed'] else ''}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
