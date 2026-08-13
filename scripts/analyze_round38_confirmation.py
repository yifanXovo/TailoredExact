#!/usr/bin/env python3
"""Audit the frozen Round 38 selected confirmation."""

from __future__ import annotations

import analyze_round38_diagnostic as analyzer
import round38_experiment_common as common


analyzer.MATRIX = common.OUT / "round38_confirmation_matrix.csv"
analyzer.FREEZE = common.OUT / "round38_confirmation_freeze.json"
analyzer.RUNS = common.OUT / "confirmation_runs"
analyzer.OUTPUT_PREFIX = "confirmation"
analyzer.ANALYSIS_SCHEMA = "round38-confirmation-analysis-v1"


if __name__ == "__main__":
    raise SystemExit(analyzer.main())
