#!/usr/bin/env python3
"""Build historical and M1 canonical LPs for every frozen Round 50 state."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUND50 = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
RECONSTRUCTION = ROUND50 / "fixed_interval_state_reconstruction_audit.csv"
MANIFEST = ROUND50 / "fixed_interval_state_manifest.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", required=True, type=Path)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--cap", default=120.0, type=float)
    args = parser.parse_args()
    if not (0.0 < args.cap <= 1800.0):
        raise RuntimeError("cap must be in (0,1800]")
    executable = args.executable.resolve()
    executable_hash = sha256(executable)
    frozen = list(csv.DictReader(RECONSTRUCTION.open(
        newline="", encoding="utf-8-sig")))
    manifest = {row["state_id"]: row for row in csv.DictReader(
        MANIFEST.open(newline="", encoding="utf-8-sig"))}
    if len(frozen) != 23:
        raise RuntimeError(f"expected 23 frozen states, found {len(frozen)}")
    args.run_root.mkdir(parents=True, exist_ok=True)
    for state in frozen:
        state_id = state["state_id"]
        for policy in ("interval-mip-v0", "m1-tight-big-m-v0"):
            output = args.run_root / f"{state_id}__{policy}"
            command_path = output / "command.json"
            completion_path = output / "completion_marker.json"
            reusable = False
            if command_path.exists() and completion_path.exists():
                command = json.loads(command_path.read_text(encoding="utf-8"))
                completion = json.loads(
                    completion_path.read_text(encoding="utf-8"))
                reusable = (
                    command.get("executable_sha256") == executable_hash
                    and command.get("policy") == policy
                    and command.get("mode") == "build"
                    and completion.get("status") == "model_built"
                    and completion.get("evidence_complete") is True
                    and completion.get("cap_respected") is True
                )
            if reusable:
                print(f"reuse {state_id} {policy}", flush=True)
                continue
            command = [
                str(executable), "--mode", "build", "--state-id", state_id,
                "--input", str(ROOT / manifest[state_id]["input_path"]),
                "--artifact-dir", str(output), "--policy", policy,
                "--gamma-lower", state["gamma_lower"], "--gamma-upper",
                state["gamma_upper"], "--cutoff", state["verified_cutoff"],
                "--process-cap", format(args.cap, ".17g"), "--T",
                state["route_time_limit"],
            ]
            completed = subprocess.run(
                command, cwd=ROOT, timeout=max(60.0, args.cap + 45.0))
            if completed.returncode != 0:
                raise RuntimeError(
                    f"model build failed {completed.returncode}: "
                    f"{state_id} {policy}")
            print(f"built {state_id} {policy}", flush=True)


if __name__ == "__main__":
    main()
