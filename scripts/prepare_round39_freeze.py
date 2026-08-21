#!/usr/bin/env python3
"""Predeclare Round 39 rows and bind all protocol inputs before comparisons."""

from __future__ import annotations

import json
import math
import os
import platform
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

import round39_common as common


STARTING_HEAD = "1459308492a5eceed523dee53b5f9d79141b5242"
BRANCH = "codex/round39-small-hard-light-qualification"
GUARD_SLOTS = ("small-easy-01", "small-medium-04", "small-hard-08")


def preexisting_worktree() -> list[dict[str, Any]]:
    intended_prefixes = (
        "build_round39/", "reference/qualification_round39/",
        "results/gf_small_hard_light_round39/",
    )
    intended_files = {
        "scripts/round39_instance_tools.py",
        "scripts/generate_round39_small_hard.py",
        "scripts/round39_common.py",
        "scripts/prepare_round39_freeze.py",
        "scripts/run_round39_experiments.py",
        "scripts/analyze_round39.py",
        "scripts/audit_round39_final.py",
        "tests/round39_protocol_tests.py",
    }
    status = subprocess.check_output(
        ("git", "status", "--porcelain=v1", "-uall"), cwd=common.ROOT,
        text=True, encoding="utf-8", errors="replace")
    output = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        state, path_text = line[:2], line[3:].replace("\\", "/")
        if path_text in intended_files or path_text.startswith(intended_prefixes):
            continue
        path = common.ROOT / path_text
        output.append({
            "status": state, "path": path_text, "exists": path.exists(),
            "bytes": path.stat().st_size if path.is_file() else "",
            "sha256": common.sha256(path) if path.is_file() else "",
            "preserve_untouched": True,
        })
    return output


def matrix_row(item: dict[str, Any], arm: str, stage: str,
               serial_order: int) -> dict[str, Any]:
    token = arm.lower().replace("-", "_")
    return {
        "round_id": 39,
        "stage": stage,
        "run_id": f"{stage}__{item['instance_id']}__{token}",
        "serial_order": serial_order,
        "instance_id": item["instance_id"],
        "instance_sha256": item["sha256"],
        "V": item["V"], "M": item["M"], "Q": item["Q"],
        "T": item["T"], "difficulty_stratum": item["difficulty_stratum"],
        "arm": arm,
        "startup_variant": (
            "not_applicable" if arm == "P-GRB"
            else "hga-light-1000" if arm == "C6-HGA-LIGHT-1000"
            else "hga-full"),
        "process_cap_seconds": common.PROCESS_CAP_SECONDS,
        "shutdown_margin_seconds": common.SHUTDOWN_MARGIN,
        "watchdog_seconds": common.PROCESS_CAP_SECONDS + 180,
        "run_to_convergence": True,
        "frozen_before_official_results": True,
    }


def main() -> int:
    if common.RUNS.exists() or common.FROZEN_MANIFEST.exists():
        raise RuntimeError("Round 39 official results or freeze already exist")
    branch = subprocess.check_output(
        ("git", "branch", "--show-current"), cwd=common.ROOT,
        text=True).strip()
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=common.ROOT, text=True).strip()
    if branch != BRANCH or head != STARTING_HEAD:
        raise RuntimeError(f"unexpected base identity: {branch} {head}")
    if not common.EXE.is_file():
        raise RuntimeError("Round 39 Gurobi executable is missing")
    items = common.inventory()
    descriptors = common.csv_rows(common.DESCRIPTOR_TABLE)
    if len(items) != 24 or len(descriptors) != 24:
        raise RuntimeError("Round 39 requires 24 frozen instance descriptors")
    for item in items.values():
        path = common.item_path(item)
        if not path.is_file() or common.sha256(path) != item["sha256"]:
            raise RuntimeError(f"instance identity mismatch: {item['instance_id']}")
    keyed_slots = {item["stratum_slot"]: item for item in items.values()}
    guard_rows = []
    for order, slot in enumerate(GUARD_SLOTS, start=1):
        item = keyed_slots[slot]
        guard_rows.append({
            "round_id": 39, "selection_order": order,
            "purpose": "full_vs_light_guard",
            "selection_basis": "predeclared_structural_stratum_coverage",
            "stratum_slot": slot, "instance_id": item["instance_id"],
            "instance_sha256": item["sha256"], "V": item["V"],
            "M": item["M"], "Q": item["Q"], "T": item["T"],
            "difficulty_stratum": item["difficulty_stratum"],
            "selected_before_official_results": True,
        })
    common.write_csv(common.GUARD_MANIFEST, guard_rows)

    # Fingerprint probes build the canonical original model for 1 ms.  They
    # bind model identity but are not comparative results or difficulty input.
    if "GRB_LICENSE_FILE" not in os.environ:
        raise RuntimeError("licensed child environment is unavailable")
    probe_root = common.OUT / "fingerprint_probes"
    probe_root.mkdir(parents=True, exist_ok=False)
    fingerprints: dict[str, Any] = {}
    for order, item in enumerate(sorted(items.values(), key=lambda x: x["instance_id"]), 1):
        directory = probe_root / item["instance_id"]
        directory.mkdir()
        command = common.plain_command(
            item, directory, 0, process_cap=5.0, solver_seconds=0.001,
            shutdown_margin=0.0)
        with (directory / "stdout.log").open("wb") as stdout, \
             (directory / "stderr.log").open("wb") as stderr:
            completed = subprocess.run(
                command, cwd=common.ROOT, env=os.environ.copy(),
                stdout=stdout, stderr=stderr, timeout=60, check=False)
        result = common.load_json(directory / "result.json")
        model = directory / "canonical.lp"
        fingerprint = int(result.get("gurobi_model_fingerprint", 0))
        if completed.returncode != 0 or fingerprint == 0 or not model.is_file():
            raise RuntimeError(f"fingerprint probe failed: {item['instance_id']}")
        fingerprints[item["instance_id"]] = {
            "serial_order": order,
            "instance_sha256": item["sha256"],
            "gurobi_model_fingerprint": fingerprint,
            "canonical_model_sha256": common.sha256(model),
            "gurobi_native_domain_audit_passed": bool(
                result.get("gurobi_native_domain_audit_passed")),
            "not_an_official_comparison_result": True,
        }
    common.write_json(common.FINGERPRINTS, {
        "schema": "round39-gurobi-fingerprints-v1", "round_id": 39,
        "executable_sha256": common.sha256(common.EXE),
        "solver_version": "13.0.2", "instance_count": len(fingerprints),
        "created_before_official_results": True, "instances": fingerprints,
    })

    rows: list[dict[str, Any]] = []
    order = 1
    for item in sorted(items.values(), key=lambda x: (
            x["difficulty_stratum"], x["stratum_slot"])):
        for arm in ("P-GRB", "C6-HGA-LIGHT-1000"):
            rows.append(matrix_row(item, arm, "primary", order))
            order += 1
    for guard in guard_rows:
        item = items[guard["instance_id"]]
        rows.append(matrix_row(item, "C6-HGA-FULL", "guard", order))
        order += 1
    common.write_csv(common.OFFICIAL_MATRIX, rows)
    commands = {}
    for row in rows:
        item = items[row["instance_id"]]
        directory = common.RUNS / row["run_id"]
        commands[row["run_id"]] = {
            "serial_order": int(row["serial_order"]), "stage": row["stage"],
            "instance_id": row["instance_id"], "arm": row["arm"],
            "command": common.command_for(row, item, directory),
        }
    common.write_json(common.COMMAND_FREEZE, {
        "schema": "round39-command-freeze-v1", "round_id": 39,
        "frozen_before_official_results": True, "row_count": len(commands),
        "commands": commands,
    })
    common.write_csv(
        common.OUT / "preexisting_worktree_manifest.csv", preexisting_worktree())
    protocol = """# Round 39 protocol frozen before official comparison

Round 39 creates a new, independent 24-instance V<=12 benchmark with exactly
eight structurally labelled small-easy, small-medium, and small-hard cases.
Generation, rejection, and classification use only frozen instance data; no
solver time, work, node, bound, incumbent, gap, certificate, or winner field
may influence selection. Historical instances and tables remain unchanged.

The primary comparison is the same original compact model under P-GRB versus
the validated C6 exact framework with HGA-LIGHT-1000. LIGHT changes only the
uniform completed-generation stagnation threshold from FULL's 2000 to 1000;
population, seed 20260626, operators, decoder, repair, selection, exact model,
strengthening, K=4 decomposition, scheduler, rho=0.01 split rule, and
certificate path are unchanged. The default remains C6-HGA-FULL.

All runs are contemporaneous, serial, one-thread Gurobi 13.0.2, exact Seed 0,
zero exact gaps, and process-entry timed. The 21,600-second limit is an
engineering watchdog, not a benchmark horizon: incomplete rows must be
preserved and extended before final reporting. No known optimum, prior archive,
or comparator incumbent enters either arm. Every primary row must reach a
strict original-problem certificate or be reported separately as unresolved.

The FULL guard subset was predeclared by structural stratum coverage before
official runs: slots small-easy-01, small-medium-04, and small-hard-08. Guard
analysis compares startup UB, startup/exact/total time, initial LP ledger,
target/requeue/split/closure event sequences, and final certificate. It will
not be expanded unless evidence requires it.
"""
    common.write_text(common.OUT / "benchmark_generation_protocol.md", protocol)
    source_files = (
        "CMakeLists.txt", "include/Instance.hpp", "include/Result.hpp",
        "include/hga_tgbc/HybridGA.h", "src/GurobiBaseline.cpp",
        "src/HgaTgbcRunner.cpp", "src/PaperExternalGiniTree.cpp",
        "src/ControllingLeafScheduler.cpp", "src/IntervalRowFactory.cpp",
        "src/Result.cpp", "src/main.cpp",
        "scripts/round39_instance_tools.py",
        "scripts/generate_round39_small_hard.py",
        "scripts/round39_common.py", "scripts/prepare_round39_freeze.py",
    )
    artifacts = {
        "protocol": common.OUT / "benchmark_generation_protocol.md",
        "generator_config": common.OUT / "generator_frozen_config.json",
        "instance_manifest": common.INSTANCE_MANIFEST,
        "descriptor_table": common.DESCRIPTOR_TABLE,
        "rejected_manifest": common.OUT / "rejected_generation_manifest.csv",
        "seed_manifest": common.OUT / "seed_manifest.csv",
        "guard_manifest": common.GUARD_MANIFEST,
        "fingerprints": common.FINGERPRINTS,
        "official_matrix": common.OFFICIAL_MATRIX,
        "command_freeze": common.COMMAND_FREEZE,
    }
    manifest: dict[str, Any] = {
        "schema": "round39-frozen-manifest-v1", "round_id": 39,
        "branch": branch, "starting_head": head,
        "solver_source_commit": head,
        "gurobi_executable_path": common.relative(common.EXE),
        "gurobi_executable_sha256": common.sha256(common.EXE),
        "gurobi_version": "13.0.2", "threads": 1, "gurobi_seed": 0,
        "official_instance_count": 24, "primary_row_count": 48,
        "guard_row_count": 3, "official_row_count": 51,
        "primary_timing_field": "final_process_wall_time_seconds",
        "run_to_convergence": True,
        "engineering_process_cap_seconds": common.PROCESS_CAP_SECONDS,
        "certificate_tolerance": 1e-7,
        "mainline_remains": "C6-HGA-FULL",
        "light_status": "experimental_uniform_startup_policy",
        "automatic_promotion_allowed": False,
        "default_c6_source_changed": False,
        "source_file_sha256": {
            path: common.sha256(common.ROOT / path) for path in source_files},
        "environment": {
            "hostname": socket.gethostname(), "platform": platform.platform(),
            "processor": platform.processor(),
            "python": platform.python_version(),
        },
        "frozen_before_official_results": True,
        "official_results_started_when_written": False,
        "written_at_unix_seconds": time.time(),
    }
    for key, path in artifacts.items():
        manifest[f"{key}_path"] = common.relative(path)
        manifest[f"{key}_sha256"] = common.sha256(path)
    common.write_json(common.FROZEN_MANIFEST, manifest)
    common.write_text(common.OUT / "source_of_truth.md", """# Source of truth

`round39_frozen_manifest.json` binds the executable, source, generator,
instances, descriptors, rejected candidates, guard subset, fingerprints,
official matrix, and commands before any official result. `runs/` is the raw
official source; derived CSV/JSON/Markdown files never replace raw evidence.
Historical benchmarks are read-only context and are not Round 39 rows.
""")
    print(json.dumps({
        "instances": len(items), "fingerprints": len(fingerprints),
        "primary_rows": 48, "guard_rows": 3,
        "executable_sha256": common.sha256(common.EXE),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
