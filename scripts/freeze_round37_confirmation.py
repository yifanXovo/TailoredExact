#!/usr/bin/env python3
"""Freeze the two-pair 900-second Round 37 selected confirmation."""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any

import round37_confirmation_common as common


CONFIRMATION_ORDINALS = (8, 10)
SOURCE_FILES = (
    Path("include/Instance.hpp"), Path("include/Result.hpp"),
    Path("include/GiniFrontierGeometry.hpp"), Path("src/main.cpp"),
    Path("src/Result.cpp"), Path("src/PaperExternalGiniTree.cpp"),
    Path("src/GiniFrontierGeometry.cpp"),
    Path("scripts/round37_experiment_common.py"),
    Path("scripts/round37_confirmation_common.py"),
    Path("scripts/run_round37_frozen_stage.py"),
    Path("scripts/analyze_round37_stage.py"),
    Path("results/gf_gini_geometry_mechanism_round37/research_protocol.md"),
    Path("results/gf_gini_geometry_mechanism_round37/hypothesis_register.json"),
    Path("results/gf_gini_geometry_mechanism_round37/diagnostic_analysis.json"),
    Path("results/gf_gini_geometry_mechanism_round37/diagnostic_analysis.md"),
    Path("results/gf_gini_geometry_mechanism_round37/confirmation_selection_predeclaration.md"),
)


def source_fingerprint(records: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for path, checksum in sorted(records.items()):
        digest.update(path.encode("utf-8") + b"\0" +
                      checksum.encode("ascii") + b"\n")
    return digest.hexdigest()


def main() -> int:
    if common.RUNS.exists() and any(common.RUNS.iterdir()):
        raise SystemExit("refusing to freeze after confirmation results exist")
    panel = common.panel()
    selected = sorted(
        (item for item in panel.values()
         if item["panel_ordinal"] in CONFIRMATION_ORDINALS),
        key=lambda item: item["panel_ordinal"],
    )
    if [item["panel_ordinal"] for item in selected] != \
            list(CONFIRMATION_ORDINALS):
        raise SystemExit("confirmation ordinal selection is incomplete")
    rows: list[dict[str, Any]] = []
    serial = 0
    for item in selected:
        for arm in ("C6", "G1"):
            serial += 1
            rows.append({
                "serial_order": serial, "stage": "selected_confirmation",
                "run_id": f"confirmation_{item['panel_row_id']}__{arm.lower()}",
                "panel_ordinal": item["panel_ordinal"],
                "panel_row_id": item["panel_row_id"],
                "instance_id": item["instance_id"], "V": item["V"],
                "M": item["M"], "scenario": item["scenario"],
                "arm": arm, "process_cap_seconds": 900,
                "watchdog_seconds": 990,
            })
    common.write_csv(common.MATRIX, rows)
    source_hashes: dict[str, str] = {}
    for relative in SOURCE_FILES:
        path = common.ROOT / relative
        if not path.is_file():
            raise SystemExit(f"freeze source missing: {relative.as_posix()}")
        source_hashes[relative.as_posix()] = common.sha256(path)
    commands: dict[str, Any] = {}
    for row in rows:
        item = panel[row["panel_row_id"]]
        run_dir = common.RUNS / row["run_id"]
        commands[row["run_id"]] = {
            "command": common.command_for(row, item, run_dir),
            "instance_sha256": item["instance_sha256"],
        }
    freeze = {
        "schema": "round37-confirmation-freeze-v1",
        "frozen_at_unix_seconds": time.time(), "exploratory": False,
        "confirmatory": True,
        "candidate_result_rows_present_before_freeze": 0,
        "panel_sha256": common.sha256(common.PANEL),
        "matrix_sha256": common.sha256(common.MATRIX),
        "executable_sha256": common.sha256(common.EXE),
        "source_file_sha256": source_hashes,
        "source_tree_fingerprint": source_fingerprint(source_hashes),
        "confirmation_panel_ordinals": list(CONFIRMATION_ORDINALS),
        "pair_count": len(selected), "run_count": len(rows),
        "process_cap_seconds": 900, "K": 4, "rho": 0.01,
        "reference": "C6-HGA-FULL",
        "candidate": "G1-pilot-weakest-prefine",
        "selection_basis": (
            "replicated 180/480 positive witness and replicated 180/480 "
            "regression witness"
        ),
        "automatic_promotion_allowed": False,
        "commands": commands,
    }
    common.write_json(common.FREEZE, freeze)
    print(common.FREEZE.relative_to(common.ROOT).as_posix())
    print(f"matrix_sha256={freeze['matrix_sha256']}")
    print(f"executable_sha256={freeze['executable_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
