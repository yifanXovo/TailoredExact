#!/usr/bin/env python3
"""Freeze the predeclared six-pair Round 37 smoke experiment."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

import round37_experiment_common as common


SMOKE_ORDINALS = (1, 2, 4, 8, 9, 10)
SOURCE_FILES = (
    Path("include/Instance.hpp"),
    Path("include/Result.hpp"),
    Path("include/GiniFrontierGeometry.hpp"),
    Path("src/main.cpp"),
    Path("src/Result.cpp"),
    Path("src/PaperExternalGiniTree.cpp"),
    Path("src/GiniFrontierGeometry.cpp"),
    Path("scripts/round37_experiment_common.py"),
    Path("scripts/run_round37_smoke.py"),
    Path("results/gf_gini_geometry_mechanism_round37/research_protocol.md"),
    Path("results/gf_gini_geometry_mechanism_round37/hypothesis_register.json"),
)


def source_fingerprint(records: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for path, checksum in sorted(records.items()):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(checksum.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> int:
    if common.SMOKE_RUNS.exists() and any(common.SMOKE_RUNS.iterdir()):
        raise SystemExit("refusing to freeze after smoke results exist")
    if not common.EXE.is_file():
        raise SystemExit("Round 37 executable is missing")
    panel = common.panel()
    selected = sorted(
        (item for item in panel.values()
         if item["panel_ordinal"] in SMOKE_ORDINALS),
        key=lambda item: item["panel_ordinal"],
    )
    if [item["panel_ordinal"] for item in selected] != list(SMOKE_ORDINALS):
        raise SystemExit("smoke ordinal selection is incomplete")

    rows: list[dict[str, Any]] = []
    serial = 0
    for item in selected:
        for arm in ("C6", "G1"):
            serial += 1
            rows.append({
                "serial_order": serial,
                "stage": "exploratory_smoke",
                "run_id": f"smoke_{item['panel_row_id']}__{arm.lower()}",
                "panel_ordinal": item["panel_ordinal"],
                "panel_row_id": item["panel_row_id"],
                "instance_id": item["instance_id"],
                "V": item["V"],
                "M": item["M"],
                "scenario": item["scenario"],
                "arm": arm,
                "process_cap_seconds": 180,
                "watchdog_seconds": 270,
            })
    common.write_csv(common.SMOKE_MATRIX, rows)

    source_hashes: dict[str, str] = {}
    for relative in SOURCE_FILES:
        path = common.ROOT / relative
        if not path.is_file():
            raise SystemExit(f"freeze source missing: {relative.as_posix()}")
        source_hashes[relative.as_posix()] = common.sha256(path)
    commands: dict[str, Any] = {}
    for row in rows:
        item = panel[row["panel_row_id"]]
        run_dir = common.SMOKE_RUNS / row["run_id"]
        commands[row["run_id"]] = {
            "command": common.command_for(row, item, run_dir),
            "instance_sha256": item["instance_sha256"],
        }
    freeze = {
        "schema": "round37-smoke-freeze-v1",
        "frozen_at_unix_seconds": time.time(),
        "exploratory": True,
        "candidate_result_rows_present_before_freeze": 0,
        "panel_sha256": common.sha256(common.PANEL),
        "matrix_sha256": common.sha256(common.SMOKE_MATRIX),
        "executable_sha256": common.sha256(common.EXE),
        "source_file_sha256": source_hashes,
        "source_tree_fingerprint": source_fingerprint(source_hashes),
        "smoke_panel_ordinals": list(SMOKE_ORDINALS),
        "pair_count": len(selected),
        "run_count": len(rows),
        "process_cap_seconds": 180,
        "K": 4,
        "rho": 0.01,
        "reference": "C6-HGA-FULL",
        "candidate": "G1-pilot-weakest-prefine",
        "commands": commands,
    }
    common.write_json(common.SMOKE_FREEZE, freeze)
    print(common.SMOKE_FREEZE.relative_to(common.ROOT).as_posix())
    print(f"matrix_sha256={freeze['matrix_sha256']}")
    print(f"executable_sha256={freeze['executable_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
