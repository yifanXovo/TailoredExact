#!/usr/bin/env python3
"""Orchestrate the contractually bounded Round 49 live work."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

import round49_common as common


def stage3(executable: Path) -> None:
    separation = common.load_json(common.OUT / "rc_rule_separation_audit.json")
    if separation.get("primary_offline_gate_passed"):
        raise RuntimeError(
            "runner is frozen for the observed offline-gate-failed pathway")
    freeze = common.load_json(common.OUT / "candidate_rule_freeze.json")
    candidates = freeze.get("candidates", [])
    if len(candidates) != 1 or candidates[0].get("cli_rule") != "d-rcd":
        raise RuntimeError("candidate freeze is not the one bounded D-RCD arm")
    command = [
        sys.executable,
        str(common.ROOT / "scripts" / "round49_experiment.py"),
        "--stage", "stage3_300s", "--process-cap", "300",
    ]
    for instance in common.MECHANISM:
        command += ["--instance", instance]
    command += ["--executable", str(executable)]
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(command, cwd=common.ROOT, env=environment, check=True)
    missing = [instance for instance in common.MECHANISM
               if not (common.RUNS /
                       f"stage3_300s__{instance}__K1-AM-RC-A" /
                       "completion_marker.json").is_file()]
    if missing:
        raise RuntimeError(f"incomplete Stage 3 rows: {missing}")
    common.write_json(common.OUT / "stage3_completion.json", {
        "schema": "round49-stage3-completion-v1",
        "complete": True,
        "row_count": 8,
        "instances": list(common.MECHANISM),
        "algorithm": "K1-AM-RC-A",
        "rule": "D-RCD",
        "process_cap_seconds": 300,
        "bounded_diagnostic_due_offline_gate_failure": True,
        "stage3_revision_used": False,
        "stage4_entered": False,
        "stage5_entered": False,
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("stage3", "all"))
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    executable = args.executable.resolve()
    if not executable.is_file():
        raise SystemExit(f"official executable missing: {executable}")
    if "dev-gurobi-release" in executable.as_posix().lower():
        raise SystemExit("official orchestration cannot use a development build")
    stage3(executable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
