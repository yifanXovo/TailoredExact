#!/usr/bin/env python3
"""Regression totals for the retained Round 25/26 C0 forensic parser."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import analyze_round30_c0_forensics as forensic  # noqa: E402


def main() -> int:
    runs = forensic.all_c0_runs()
    attempts, splits, interleaving, shadows = forensic.forensic_rows(runs)
    assert len(runs) == 57, len(runs)
    assert len(attempts) == 1386, len(attempts)
    assert len(splits) == 317, len(splits)
    assert len(interleaving) == 1386, len(interleaving)
    assert len(shadows) == 951, len(shadows)
    second = [row for row in attempts if row["attempt_ordinal"] == 2]
    assert len(second) == 517, len(second)
    assert sum(row["material_leaf_gain"] for row in second) == 307
    assert all(
        row["coverage_preserved_if_parent_retained_or_atomic_split"]
        for row in shadows)
    print("round30_c0_parser_tests: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
