#!/usr/bin/env python3
"""Paths and frozen command wrapper for Round 37 focused diagnostics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import round37_experiment_common as base


ROOT = base.ROOT
OUT = base.OUT
PANEL = base.PANEL
EXE = base.EXE
MATRIX = OUT / "round37_diagnostic_matrix.csv"
FREEZE = OUT / "round37_diagnostic_freeze.json"
RUNS = OUT / "diagnostic_runs"
SUMMARY = OUT / "diagnostic_run_summary.csv"

sha256 = base.sha256
load_json = base.load_json
csv_rows = base.csv_rows
write_json = base.write_json
write_csv = base.write_csv
panel = base.panel
required_artifacts = base.required_artifacts


def command_for(row: dict[str, str], item: dict[str, Any],
                run_dir: Path) -> list[str]:
    return base.command_for(row, item, run_dir)
