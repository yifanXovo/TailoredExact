#!/usr/bin/env python3
"""Freeze predeclared Round 38 stable witnesses plus worst regression."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

import round38_experiment_common as common


ORDINALS = (8, 10, 11)
MATRIX = common.OUT / "round38_confirmation_matrix.csv"
FREEZE = common.OUT / "round38_confirmation_freeze.json"
RUNS = common.OUT / "confirmation_runs"
DIAGNOSTIC_FREEZE = common.OUT / "round38_diagnostic_freeze.json"
DIAGNOSTIC_ANALYSIS = common.OUT / "diagnostic_analysis.json"
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
    Path("scripts/run_round38_confirmation.py"),
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
        raise SystemExit("refusing to freeze after confirmation results exist")
    for path in (common.EXE, DIAGNOSTIC_FREEZE, DIAGNOSTIC_ANALYSIS):
        if not path.is_file():
            raise SystemExit(f"required evidence missing: {path.name}")
    diagnostic_freeze = common.load_json(DIAGNOSTIC_FREEZE)
    diagnostic = common.load_json(DIAGNOSTIC_ANALYSIS)
    if not diagnostic.get("confirmation_eligible"):
        raise SystemExit("frozen diagnostic rule does not permit confirmation")
    if common.sha256(common.EXE) != diagnostic_freeze["executable_sha256"]:
        raise SystemExit("candidate executable changed after diagnostic freeze")
    by_ordinal = {
        item["panel_ordinal"]: item for item in common.panel().values()
    }
    selected = [by_ordinal[ordinal] for ordinal in ORDINALS]
    diagnostic_pairs = {
        int(row["panel_ordinal"]): row for row in diagnostic["pairs"]
    }
    if diagnostic_pairs[8]["outcome"] != "g2a_improves":
        raise SystemExit("stable V20 positive did not meet frozen rule")
    if diagnostic_pairs[10]["outcome"] == "g2a_regresses":
        raise SystemExit("stable V50 witness failed frozen rule")
    regressions = [row for row in diagnostic["pairs"]
                   if row["outcome"] == "g2a_regresses"]
    if regressions:
        worst = min(regressions, key=lambda row: row["g2a_gap_improvement"])
        if int(worst["panel_ordinal"]) != 11:
            raise SystemExit("ordinal 11 is not the worst diagnostic regression")
    rows: list[dict[str, Any]] = []
    serial = 0
    for item in selected:
        for arm in ("C6", "G2A"):
            serial += 1
            rows.append({
                "serial_order": serial,
                "stage": "selected_confirmation",
                "run_id": f"confirmation_{item['panel_row_id']}__{arm.lower()}",
                "panel_ordinal": item["panel_ordinal"],
                "panel_row_id": item["panel_row_id"],
                "instance_id": item["instance_id"],
                "V": item["V"],
                "M": item["M"],
                "scenario": item["scenario"],
                "arm": arm,
                "process_cap_seconds": 900,
                "watchdog_seconds": 990,
            })
    common.write_csv(MATRIX, rows)
    source_hashes: dict[str, str] = {}
    for relative in SOURCE_FILES:
        path = common.ROOT / relative
        if not path.is_file():
            raise SystemExit(f"freeze source missing: {relative.as_posix()}")
        source_hashes[relative.as_posix()] = common.sha256(path)
    for relative, expected in diagnostic_freeze["source_file_sha256"].items():
        if relative in source_hashes and source_hashes[relative] != expected:
            raise SystemExit(f"implementation changed after diagnostic: {relative}")
    panel = common.panel()
    commands: dict[str, Any] = {}
    for row in rows:
        item = panel[row["panel_row_id"]]
        run_dir = RUNS / row["run_id"]
        commands[row["run_id"]] = {
            "command": common.command_for(row, item, run_dir),
            "instance_sha256": item["instance_sha256"],
        }
    freeze = {
        "schema": "round38-confirmation-freeze-v1",
        "frozen_at_unix_seconds": time.time(),
        "candidate_result_rows_present_before_freeze": 0,
        "panel_sha256": common.sha256(common.PANEL),
        "matrix_sha256": common.sha256(MATRIX),
        "executable_sha256": common.sha256(common.EXE),
        "source_file_sha256": source_hashes,
        "source_tree_fingerprint": source_fingerprint(source_hashes),
        "diagnostic_freeze_sha256": common.sha256(DIAGNOSTIC_FREEZE),
        "diagnostic_analysis_sha256": common.sha256(DIAGNOSTIC_ANALYSIS),
        "selected_panel_ordinals": list(ORDINALS),
        "selection_reason": {
            "8": "predeclared stable V20 positive witness",
            "10": "predeclared stable V50 adversarial witness",
            "11": "worst final-gap regression in the full-panel diagnostic",
        },
        "pair_count": len(selected),
        "run_count": len(rows),
        "process_cap_seconds": 900,
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
