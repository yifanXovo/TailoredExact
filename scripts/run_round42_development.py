#!/usr/bin/env python3
"""Run one frozen Round 42 development campaign stage sequentially."""

from __future__ import annotations

import argparse

import round42_common as common
import run_round42_c6 as c6
import run_round42_static as static


STAGES = (
    "c6-reference",
    "k1-reference",
    "same-k",
    "family-a-base",
    "family-a-refinement",
    "family-b-base",
    "family-b-refinement",
    "family-c-base",
    "family-c-refinement",
    "static-root-lp-diagnostics",
)


def development_ids() -> list[str]:
    rows = common.csv_rows(common.OUT / "development_manifest.csv")
    return [row["instance_id"] for row in sorted(
        rows, key=lambda row: int(row["serial_order"]))]


def run_stage(stage: str, process_cap: float) -> None:
    for instance_id in development_ids():
        if stage == "c6-reference":
            c6.run_one(instance_id, "c6-reference", process_cap,
                       False, "development_reference")
        elif stage == "k1-reference":
            c6.run_one(instance_id, "k1-single-reference", process_cap,
                       False, "development_k1_reference")
        elif stage == "same-k":
            static.run_composite(
                instance_id, "external-k2-fixed", "mip", process_cap,
                False, "development_same_k")
            static.run_one(
                instance_id, "st-k2-p-core-reference", "mip", process_cap,
                False, "development_same_k")
        elif stage == "family-a-base":
            static.run_one(
                instance_id, "st-k4-p-core", "mip", process_cap,
                False, "development_family_a_base")
        elif stage == "family-a-refinement":
            static.run_one(
                instance_id, "st-k4-p-core-hierarchical", "mip",
                process_cap, False, "development_family_a_hierarchical")
        elif stage == "family-b-base":
            static.run_composite(
                instance_id, "paired-k4", "mip", process_cap,
                False, "development_family_b_base")
        elif stage == "family-b-refinement":
            static.run_composite(
                instance_id, "paired-k4-factored", "mip", process_cap,
                False, "development_family_b_factored")
        elif stage == "family-c-base":
            c6.run_one(instance_id, "sibling-core", process_cap,
                       False, "development_family_c_base")
        elif stage == "family-c-refinement":
            c6.run_one(instance_id, "sibling-core-factored", process_cap,
                       False, "development_family_c_factored")
        elif stage == "static-root-lp-diagnostics":
            for arm, tag in (
                ("st-k2-p-core-reference", "diagnostic_st_k2"),
                ("st-k4-p-core", "diagnostic_st_k4"),
                ("st-k4-p-core-hierarchical", "diagnostic_st_k4_hier"),
            ):
                static.run_one(instance_id, arm, "root-lp", process_cap,
                               False, tag)
            for arm, tag in (
                ("external-k2-fixed", "diagnostic_external_k2"),
                ("paired-k4", "diagnostic_paired_k4"),
                ("paired-k4-factored", "diagnostic_paired_k4_factored"),
            ):
                static.run_composite(instance_id, arm, "root-lp",
                                     process_cap, False, tag)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--process-cap", type=float, default=1800.0)
    args = parser.parse_args()
    run_stage(args.stage, args.process_cap)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
