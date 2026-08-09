#!/usr/bin/env python3
"""Launch the frozen Round 35 runner with child-only license inheritance.

The established authorized path is imported from the existing controller.
This module does not open, print, hash, copy, or serialize that path or file.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import run_round25_experiments as licensed


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(r"D:\msys64\ucrt64\bin\python.exe")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, choices=(
        "matrix1800", "v50_3600", "repeat"))
    args = parser.parse_args()
    environment = os.environ.copy()
    environment["GRB_LICENSE_FILE"] = str(licensed.LICENSE)
    command = [
        str(PYTHON), "-B", str(ROOT / "scripts/run_round35_experiments.py"),
        "--stage", args.stage,
    ]
    completed = subprocess.run(command, cwd=ROOT, env=environment, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
