#!/usr/bin/env python3
"""Orchestrate the contractually bounded Round 48 live work."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

import round48_common as common


def invoke(script: str, executable: Path, *arguments: str) -> None:
    command = [sys.executable, str(common.ROOT / "scripts" / script),
               *arguments, "--executable", str(executable)]
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(command, cwd=common.ROOT, env=environment, check=True)


def stage3(executable: Path) -> None:
    separation = common.load_json(common.OUT / "amf_separation_audit.json")
    if separation.get("primary_offline_gate_passed"):
        raise RuntimeError(
            "runner is frozen for the observed offline-gate-failed pathway")
    arguments = ["--stage", "stage3_300s", "--process-cap", "300"]
    for instance in common.MECHANISM:
        arguments += ["--instance", instance]
    invoke("round48_experiment.py", executable, *arguments)
    missing = [instance for instance in common.MECHANISM
               if not (common.RUNS /
                       f"stage3_300s__{instance}__K1-AMF" /
                       "completion_marker.json").is_file()]
    if missing:
        raise RuntimeError(f"incomplete Stage 3 rows: {missing}")
    common.write_json(common.OUT / "stage3_completion.json", {
        "schema": "round48-stage3-completion-v1", "complete": True,
        "row_count": 8, "instances": list(common.MECHANISM),
        "algorithm": "K1-AMF", "process_cap_seconds": 300,
        "bounded_diagnostic_due_offline_gate_failure": True,
        "stage4_entered": False, "stage5_entered": False,
    })


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("counterfactuals", "stage3", "all"))
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    executable = args.executable.resolve()
    if not executable.is_file():
        raise SystemExit(f"official executable missing: {executable}")
    if "dev-gurobi-release" in executable.as_posix().lower():
        raise SystemExit("official orchestration cannot use a development build")
    if args.action in {"counterfactuals", "all"}:
        invoke("run_round48_counterfactuals.py", executable)
    if args.action in {"stage3", "all"}:
        stage3(executable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
