#!/usr/bin/env python3
"""Freeze the unchanged G2-A policy on the full Round 38 panel."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

import round38_experiment_common as common


MATRIX = common.OUT / "round38_diagnostic_matrix.csv"
FREEZE = common.OUT / "round38_diagnostic_freeze.json"
RUNS = common.OUT / "diagnostic_runs"
SMOKE_FREEZE = common.OUT / "round38_smoke_freeze.json"
SOURCE_FILES = (
    Path("CMakeLists.txt"),
    Path("include/Instance.hpp"),
    Path("include/Result.hpp"),
    Path("include/GiniFrontierGeometry.hpp"),
    Path("src/main.cpp"),
    Path("src/Result.cpp"),
    Path("src/PaperExternalGiniTree.cpp"),
    Path("src/GiniFrontierGeometry.cpp"),
    Path("tests/round38_frontier_tests.cpp"),
    Path("tests/round38_protocol_tests.py"),
    Path("scripts/round38_experiment_common.py"),
    Path("scripts/run_round38_smoke.py"),
    Path("scripts/run_round38_diagnostic.py"),
    Path("results/gf_global_frontier_lift_round38/research_protocol.md"),
    Path("results/gf_global_frontier_lift_round38/hypothesis_register.md"),
    Path("results/gf_global_frontier_lift_round38/diagnostic_advancement_rule.md"),
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
    if RUNS.exists() and any(RUNS.iterdir()):
        raise SystemExit("refusing to freeze after diagnostic results exist")
    if not common.EXE.is_file() or not SMOKE_FREEZE.is_file():
        raise SystemExit("smoke-frozen executable/evidence is missing")
    smoke = common.load_json(SMOKE_FREEZE)
    executable_sha = common.sha256(common.EXE)
    if executable_sha != smoke["executable_sha256"]:
        raise SystemExit("candidate executable changed after smoke freeze")
    panel = sorted(common.panel().values(), key=lambda row: row["panel_ordinal"])
    if len(panel) != 12:
        raise SystemExit(f"expected 12 frozen panel rows, found {len(panel)}")
    rows: list[dict[str, Any]] = []
    serial = 0
    for item in panel:
        for arm in ("C6", "G2A"):
            serial += 1
            rows.append({
                "serial_order": serial,
                "stage": "medium_full_panel_diagnostic",
                "run_id": f"diagnostic_{item['panel_row_id']}__{arm.lower()}",
                "panel_ordinal": item["panel_ordinal"],
                "panel_row_id": item["panel_row_id"],
                "instance_id": item["instance_id"],
                "V": item["V"],
                "M": item["M"],
                "scenario": item["scenario"],
                "arm": arm,
                "process_cap_seconds": 480,
                "watchdog_seconds": 570,
            })
    common.write_csv(MATRIX, rows)
    source_hashes: dict[str, str] = {}
    for relative in SOURCE_FILES:
        path = common.ROOT / relative
        if not path.is_file():
            raise SystemExit(f"freeze source missing: {relative.as_posix()}")
        source_hashes[relative.as_posix()] = common.sha256(path)
    # Every smoke-frozen implementation file must remain byte-identical.
    for relative, expected in smoke["source_file_sha256"].items():
        if relative in source_hashes and source_hashes[relative] != expected:
            raise SystemExit(f"implementation changed after smoke: {relative}")
    commands: dict[str, Any] = {}
    for row in rows:
        item = common.panel()[row["panel_row_id"]]
        run_dir = RUNS / row["run_id"]
        commands[row["run_id"]] = {
            "command": common.command_for(row, item, run_dir),
            "instance_sha256": item["instance_sha256"],
        }
    freeze = {
        "schema": "round38-diagnostic-freeze-v1",
        "frozen_at_unix_seconds": time.time(),
        "candidate_result_rows_present_before_freeze": 0,
        "panel_sha256": common.sha256(common.PANEL),
        "matrix_sha256": common.sha256(MATRIX),
        "executable_sha256": executable_sha,
        "source_file_sha256": source_hashes,
        "source_tree_fingerprint": source_fingerprint(source_hashes),
        "smoke_freeze_sha256": common.sha256(SMOKE_FREEZE),
        "full_panel_ordinals": [item["panel_ordinal"] for item in panel],
        "pair_count": len(panel),
        "run_count": len(rows),
        "process_cap_seconds": 480,
        "K": 4,
        "rho": 0.01,
        "reference": "C6-HGA-FULL",
        "candidate": "G2A-pilot-next-frontier-complete",
        "commands": commands,
    }
    common.write_json(FREEZE, freeze)
    print(FREEZE.relative_to(common.ROOT).as_posix())
    print(f"matrix_sha256={freeze['matrix_sha256']}")
    print(f"executable_sha256={freeze['executable_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
