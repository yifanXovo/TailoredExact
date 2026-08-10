#!/usr/bin/env python3
"""Freeze the Round 36 Stage B matrix and command identities."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import round36_common as common


SOURCE_FILES = (
    "CMakeLists.txt",
    "include/GiniFrontierGeometry.hpp",
    "include/Instance.hpp",
    "include/PaperExternalGiniTree.hpp",
    "include/Result.hpp",
    "src/GiniFrontierGeometry.cpp",
    "src/PaperExternalGiniTree.cpp",
    "src/Result.cpp",
    "src/main.cpp",
    "tests/round36_causal_tests.cpp",
    "tests/round36_protocol_tests.py",
    "scripts/freeze_round36.py",
    "scripts/round36_common.py",
    "scripts/prepare_round36.py",
    "scripts/run_round36_experiments.py",
    "scripts/launch_round36_licensed.py",
    "scripts/run_round36_baseline_equivalence.py",
    "scripts/run_round36_stage_a.py",
)
FROZEN_ARTIFACTS = {
    "protocol": common.OUT / "round36_protocol.md",
    "theory": common.OUT / "theory_and_mechanism_note.md",
    "source_of_truth": common.OUT / "source_of_truth.md",
    "panel_csv": common.OUT / "frozen_causal_panel.csv",
    "panel_json": common.OUT / "frozen_causal_panel.json",
    "stage_a": common.OUT / "stage_a_build_and_tests.json",
    "baseline_equivalence": common.OUT / "baseline_equivalence_audit.json",
}


def tree_fingerprint(files: dict[str, str]) -> str:
    digest = hashlib.sha256()
    for name, value in sorted(files.items()):
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(value.encode())
        digest.update(b"\n")
    return digest.hexdigest()


def main() -> int:
    if common.START_RECORD.exists():
        raise SystemExit("official Round 36 runs already started; freeze is immutable")
    if not common.EXE.is_file():
        raise SystemExit("clean Round 36 executable is missing")
    stage_a = common.load_json(FROZEN_ARTIFACTS["stage_a"])
    equivalence = common.load_json(FROZEN_ARTIFACTS["baseline_equivalence"])
    if not stage_a.get("passed") or not equivalence.get("passed"):
        raise SystemExit("Stage A gate is not green")

    items = common.inventory()
    matrix = []
    serial = 0
    for item in sorted(items.values(), key=lambda value: value["panel_ordinal"]):
        for arm in common.ARMS:
            serial += 1
            slug = arm.lower().replace("-", "_")
            run_id = (f"{item['panel_row_id']}__{slug}__"
                      f"{item['process_cap_seconds']}s")
            matrix.append({
                "serial_order": serial,
                "run_id": run_id,
                "panel_ordinal": item["panel_ordinal"],
                "panel_row_id": item["panel_row_id"],
                "instance_id": item["instance_id"],
                "V": item["V"], "M": item["M"],
                "scenario": item["scenario"],
                "round35_pattern": item["round35_pattern"],
                "arm": arm,
                "startup_variant": "simple-start" if arm == "SS" else "hga-full",
                "proof_source": "simple" if arm == "SS" else (
                    "hga" if arm == "HH" else "best-of-hga-simple"),
                "anchor_source": "simple" if arm == "SS" else (
                    "hga" if arm == "HH" else "wide-of-hga-simple"),
                "split_normalization": "anchor" if arm == "BW-A" else "proof",
                "process_cap_seconds": item["process_cap_seconds"],
                "shutdown_margin_seconds": common.SHUTDOWN_MARGIN,
                "watchdog_seconds": item["process_cap_seconds"] +
                    common.WATCHDOG_SEPARATION,
                "rho": 0.01,
                "initial_interval_count": 4,
                "frozen_before_causal_results": True,
            })
    if len(matrix) != 56:
        raise RuntimeError(f"expected 56 Stage B runs, found {len(matrix)}")
    common.write_csv(common.OFFICIAL_MATRIX, matrix)

    commands = {}
    for row in matrix:
        item = items[row["instance_id"]]
        run_dir = common.RUNS / row["run_id"]
        commands[row["run_id"]] = {
            "serial_order": row["serial_order"],
            "instance_sha256": item["instance_sha256"],
            "executable_sha256": common.sha256(common.EXE),
            "command": common.command_for(row, item, run_dir),
        }
    command_payload = {
        "schema": "round36-command-freeze-v1",
        "frozen_before_causal_results": True,
        "row_count": len(commands),
        "commands": commands,
    }
    common.write_json(common.COMMAND_FREEZE, command_payload)

    source_hashes = {
        path: common.sha256(common.ROOT / path) for path in SOURCE_FILES
    }
    artifact_hashes = {
        name: {"path": common.relative(path), "sha256": common.sha256(path)}
        for name, path in FROZEN_ARTIFACTS.items()
    }
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=common.ROOT,
        text=True).strip()
    manifest = {
        "schema": "round36-frozen-manifest-v1",
        "round_id": 36,
        "source_base_commit": head,
        "source_file_sha256": source_hashes,
        "source_tree_fingerprint": tree_fingerprint(source_hashes),
        "gurobi_executable_path": common.relative(common.EXE),
        "gurobi_executable_sha256": common.sha256(common.EXE),
        "gurobi_version": "13.0.2",
        "official_matrix_path": common.relative(common.OFFICIAL_MATRIX),
        "official_matrix_sha256": common.sha256(common.OFFICIAL_MATRIX),
        "command_freeze_path": common.relative(common.COMMAND_FREEZE),
        "command_freeze_sha256": common.sha256(common.COMMAND_FREEZE),
        "frozen_artifacts": artifact_hashes,
        "row_count": len(matrix),
        "panel_row_count": len(items),
        "arms": list(common.ARMS),
        "frozen_before_causal_results": True,
    }
    common.write_json(common.FROZEN_MANIFEST, manifest)
    print(json.dumps({
        "matrix_rows": len(matrix),
        "panel_rows": len(items),
        "source_tree_fingerprint": manifest["source_tree_fingerprint"],
        "executable_sha256": manifest["gurobi_executable_sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
