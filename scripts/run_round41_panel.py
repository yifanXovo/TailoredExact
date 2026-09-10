#!/usr/bin/env python3
"""Run the frozen Round 41 static panel serially."""

from __future__ import annotations

import argparse

import round41_common as common
from run_round41_static_segmented import ARMS, run_one


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=("root", "exact", "both"),
                        default="root")
    parser.add_argument("--instance", action="append", default=[])
    parser.add_argument("--arm", action="append", choices=ARMS, default=[])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    rows = common.csv_rows(common.OUT / "diagnostic_panel_manifest.csv")
    requested = set(args.instance)
    if requested:
        known = {row["instance_id"] for row in rows}
        if requested - known:
            raise SystemExit(
                f"instances are not frozen: {sorted(requested - known)}")
        rows = [row for row in rows if row["instance_id"] in requested]
    arms = tuple(args.arm) if args.arm else ARMS
    solves = (("root-lp", "root_lp_cap_seconds"),) \
        if args.stage == "root" else (("mip", "exact_cap_seconds"),) \
        if args.stage == "exact" else (
            ("root-lp", "root_lp_cap_seconds"),
            ("mip", "exact_cap_seconds"))
    for solve, cap_field in solves:
        for row in rows:
            for arm in arms:
                run_one(row["instance_id"], arm, solve,
                        float(row[cap_field]), args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
