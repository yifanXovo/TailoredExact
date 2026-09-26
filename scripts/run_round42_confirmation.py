#!/usr/bin/env python3
"""Run a frozen candidate and C6 on validation or final holdout."""

from __future__ import annotations

import argparse

import round42_common as common
import run_round42_c6 as c6
import run_round42_static as static


CANDIDATES = (
    "st-k4-p-core",
    "st-k4-p-core-hierarchical",
    "paired-k4",
    "paired-k4-factored",
    "sibling-core",
    "sibling-core-factored",
)


def instance_ids(group: str) -> list[str]:
    name = "validation_manifest.csv" if group == "validation" \
        else "final_holdout_manifest.csv"
    rows = common.csv_rows(common.OUT / name)
    return [row["instance_id"] for row in sorted(
        rows, key=lambda row: int(row["serial_order"]))]


def run_candidate(instance_id: str, candidate: str, cap: float,
                  group: str) -> None:
    tag = f"{group}_candidate_{candidate.replace('-', '_')}"
    if candidate in {"sibling-core", "sibling-core-factored"}:
        c6.run_one(instance_id, candidate, cap, False, tag)
    elif candidate in {"paired-k4", "paired-k4-factored"}:
        static.run_composite(instance_id, candidate, "mip", cap,
                             False, tag)
    else:
        static.run_one(instance_id, candidate, "mip", cap,
                       False, tag)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--group", choices=("validation", "holdout"),
                        required=True)
    parser.add_argument("--candidate", choices=CANDIDATES, required=True)
    parser.add_argument("--process-cap", type=float, default=3600.0)
    args = parser.parse_args()
    freeze_path = common.OUT / f"{args.group}_candidate_freeze.json"
    if freeze_path.exists():
        frozen = common.load_json(freeze_path)
        if frozen["candidate"] != args.candidate:
            raise RuntimeError(
                f"{args.group} candidate already frozen as "
                f"{frozen['candidate']}")
    else:
        common.write_json(freeze_path, {
            "schema": f"round42-{args.group}-candidate-freeze-v1",
            "round_id": 42,
            "group": args.group,
            "candidate": args.candidate,
            "candidate_frozen_before_group_results": True,
            "process_cap_seconds": args.process_cap,
            "executable_sha256": common.sha256(common.EXE),
            "validated_default_unchanged": "C6-HGA-FULL K=4 rho=0.01",
        })
    for instance_id in instance_ids(args.group):
        c6.run_one(instance_id, "c6-reference", args.process_cap,
                   False, f"{args.group}_reference")
        run_candidate(instance_id, args.candidate, args.process_cap,
                      args.group)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
