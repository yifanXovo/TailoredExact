#!/usr/bin/env python3
"""Audit vector structural summaries for consistency."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Dict, List


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def f(value: str) -> float:
    try:
        out = float(value)
        return out if math.isfinite(out) else math.nan
    except Exception:
        return math.nan


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["audit", "passed", "reason"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", default="results/gf_tailored_bc_structural_cut_round")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    root = Path(args.results)
    summaries = read_csv(root / "callback_vector_family_summary.csv")
    rows: List[Dict[str, object]] = []
    failures = 0

    def add(name: str, passed: bool, reason: str) -> None:
        nonlocal failures
        if not passed:
            failures += 1
        rows.append({"audit": name, "passed": passed, "reason": reason})

    add("summary_rows_present", bool(summaries), f"rows={len(summaries)}")
    if summaries:
        structural = 0
        for row in summaries:
            s = f(row.get("S", ""))
            h = f(row.get("H", ""))
            g = f(row.get("G", ""))
            if math.isfinite(s) and s > 1e-12 and math.isfinite(h):
                structural += 1
                if math.isfinite(g):
                    v = f(row.get("V", ""))
                    if not math.isfinite(v) or v <= 0:
                        v = 20.0
                    expected = h / (v * s) - g
                    reported = f(row.get("G_gap", ""))
                    add("g_gap_reconstruction", math.isfinite(reported) and abs(expected - reported) < 1e-7,
                        f"snapshot={row.get('snapshot_id')} expected={expected} reported={reported}")
                    break
        add("structural_values_available", structural > 0,
            f"structural_summary_rows={structural}")
        unknown_bad = [
            row for row in summaries
            if math.isfinite(f(row.get("unknown_unparsed_fraction", ""))) and
            f(row.get("unknown_unparsed_fraction", "")) > 0.05 + 1e-12
        ]
        add("unknown_fraction_at_most_five_percent", not unknown_bad,
            f"bad_snapshots={len(unknown_bad)}")
    out = Path(args.out) if args.out else root / "vector_structural_summary_audit.csv"
    write_csv(out, rows)
    print(f"audits={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
