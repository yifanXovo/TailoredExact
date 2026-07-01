#!/usr/bin/env python3
"""Aggregate per-leaf BPC validation CSVs into round-level tables."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, Iterable, List


INPUT_OUTPUT = {
    "bpc_leaf_validation_summary.csv": "bpc_long_baseline_summary.csv",
    "bpc_pricing_profile.csv": "bpc_long_pricing_profile.csv",
    "pricing_state_audit.csv": "pricing_state_audit.csv",
    "pricing_depth_profile.csv": "pricing_depth_profile.csv",
    "operation_dp_profile.csv": "operation_dp_profile.csv",
}


def csv_rows(files: Iterable[Path]) -> tuple[list[str], list[Dict[str, str]]]:
    fields: List[str] = []
    rows: List[Dict[str, str]] = []
    for path in files:
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                continue
            if not fields:
                fields = list(reader.fieldnames)
                if "source_dir" not in fields:
                    fields.append("source_dir")
            for row in reader:
                if not any((value or "").strip() for value in row.values()):
                    continue
                row["source_dir"] = str(path.parent)
                rows.append(row)
    return fields, rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round-dir", required=True)
    parser.add_argument("--pattern", default="*")
    args = parser.parse_args()

    round_dir = Path(args.round_dir)
    for input_name, output_name in INPUT_OUTPUT.items():
        files = sorted(
            path for path in round_dir.glob(f"{args.pattern}/{input_name}")
            if path.is_file()
        )
        fields, rows = csv_rows(files)
        out = round_dir / output_name
        if not fields:
            out.write_text("", encoding="utf-8")
            continue
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        print(f"{output_name}: rows={len(rows)} files={len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
