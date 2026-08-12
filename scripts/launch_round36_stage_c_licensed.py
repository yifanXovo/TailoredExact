#!/usr/bin/env python3
"""Launch the frozen Round 36 Stage C runner with child-only licensing."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

import run_round25_experiments as licensed


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(r"D:\msys64\ucrt64\bin\python.exe")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", action="append")
    parser.add_argument("--validation-stage", action="append")
    parser.add_argument("--max-rows", type=int)
    args = parser.parse_args()
    command = [str(PYTHON), "-B",
               str(ROOT / "scripts" / "run_round36_stage_c.py")]
    for value in args.run_id or ():
        command.extend(("--run-id", value))
    for value in args.validation_stage or ():
        command.extend(("--validation-stage", value))
    if args.max_rows is not None:
        command.extend(("--max-rows", str(args.max_rows)))
    environment = os.environ.copy()
    environment["GRB_LICENSE_FILE"] = str(licensed.LICENSE)
    return subprocess.run(command, cwd=ROOT, env=environment,
                          check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
