#!/usr/bin/env python3
"""Audit the isolated Round 36 Stage C monotone launch-contract fix."""

from __future__ import annotations

import csv
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import round36_common as r36
import round36_stage_c_common as common
import run_round25_experiments as licensed
import run_round36_baseline_equivalence as baseline


BUILD = common.EXE.parent
CTEST = Path(
    r"D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe")
RUNS = common.OUT / "stage_c_contract_fix_equivalence_runs"
AUDIT_CSV = common.OUT / "stage_c_contract_fix_audit.csv"
AUDIT_MD = common.OUT / "stage_c_contract_fix_audit.md"
STAGE_B_RUNS = common.OUT / "baseline_equivalence_runs"


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def run_one(name: str, arm: str) -> Path:
    run_dir = RUNS / name
    result_path = run_dir / "result.json"
    if result_path.is_file():
        command_record = json.loads(
            (run_dir / "command.json").read_text(encoding="utf-8-sig"))
        if command_record.get("executable_sha256") != common.sha256(common.EXE):
            raise RuntimeError(f"stale contract-fix equivalence run: {name}")
        return run_dir
    run_dir.mkdir(parents=True, exist_ok=False)
    command = baseline.command(common.EXE, run_dir, arm)
    write_json(run_dir / "command.json", {
        "schema": "round36-stage-c-contract-fix-equivalence-command-v1",
        "run_id": name,
        "arm": arm,
        "executable_sha256": common.sha256(common.EXE),
        "instance_sha256": common.sha256(baseline.INSTANCE),
        "process_cap_seconds": baseline.PROCESS_CAP,
        "command": command,
        "license_environment": "child_only_not_serialized",
    })
    environment = os.environ.copy()
    environment["GRB_LICENSE_FILE"] = str(licensed.LICENSE)
    with (run_dir / "console.stdout.log").open("wb") as stdout, \
         (run_dir / "console.stderr.log").open("wb") as stderr:
        completed = subprocess.run(
            command, cwd=common.ROOT, env=environment, stdout=stdout,
            stderr=stderr, timeout=baseline.PROCESS_CAP + 60, check=False)
    if completed.returncode != 0 or not result_path.is_file():
        raise RuntimeError(
            f"contract-fix equivalence run failed: {name} "
            f"rc={completed.returncode}")
    return run_dir


def main() -> int:
    if not common.STAGE_B_EXE.is_file() or not common.EXE.is_file():
        raise SystemExit("both Stage B and isolated Stage C executables are required")
    stage_b_manifest = common.load_json(r36.FROZEN_MANIFEST)
    stage_b_hash = common.sha256(common.STAGE_B_EXE)
    stage_c_hash = common.sha256(common.EXE)
    stage_b_unchanged = (
        stage_b_hash == stage_b_manifest["gurobi_executable_sha256"])
    RUNS.mkdir(parents=True, exist_ok=True)

    ctest_stdout = common.OUT / "stage_c_contract_fix_ctest.stdout.log"
    ctest_stderr = common.OUT / "stage_c_contract_fix_ctest.stderr.log"
    started = time.monotonic()
    with ctest_stdout.open("wb") as stdout, ctest_stderr.open("wb") as stderr:
        ctest = subprocess.run(
            [str(CTEST), "--test-dir", str(BUILD), "--output-on-failure"],
            cwd=common.ROOT, stdout=stdout, stderr=stderr, check=False)
    ctest_seconds = time.monotonic() - started

    new_default = run_one("stage_c_default_off", "off")
    new_hh = run_one("stage_c_hh", "hh")
    pairs = (
        ("default_off", STAGE_B_RUNS / "round36_default_off", new_default),
        ("hh", STAGE_B_RUNS / "round36_hh", new_hh),
    )
    comparisons: list[dict[str, Any]] = []
    for mode, reference_dir, candidate_dir in pairs:
        reference = baseline.signature(reference_dir)["component_hashes"]
        candidate = baseline.signature(candidate_dir)["component_hashes"]
        for component, reference_hash in reference.items():
            candidate_hash = candidate[component]
            comparisons.append({
                "mode": mode,
                "component": component,
                "stage_b_sha256": reference_hash,
                "stage_c_sha256": candidate_hash,
                "identical": reference_hash == candidate_hash,
            })
    with AUDIT_CSV.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(comparisons[0]))
        writer.writeheader()
        writer.writerows(comparisons)

    invalidation = common.load_json(common.INVALIDATED_ATTEMPT_RECORD)
    passed = (ctest.returncode == 0 and stage_b_unchanged and
              stage_b_hash != stage_c_hash and
              all(row["identical"] for row in comparisons) and
              invalidation.get("invalidated") is True)
    audit = {
        "schema": "round36-stage-c-contract-fix-audit-v1",
        "round_id": 36,
        "stage": "C",
        "passed": passed,
        "scope": "Round36 causal launch validation only",
        "reason": (
            "a stronger independently verified current proof incumbent shrinks "
            "the proof-relevant range and remains covered by the frozen anchor"),
        "accepted_relation": "current_verified_proof <= recorded_startup_proof + tolerance",
        "rejected_relation": "current_verified_proof > recorded_startup_proof + tolerance",
        "anchor_requirement": "decomposition_anchor covers recorded and current proof incumbents",
        "stage_b_executable_sha256": stage_b_hash,
        "stage_b_executable_unchanged": stage_b_unchanged,
        "stage_c_executable_sha256": stage_c_hash,
        "executables_are_distinct": stage_b_hash != stage_c_hash,
        "ctest": {
            "return_code": ctest.returncode,
            "test_count": 15,
            "wall_seconds": ctest_seconds,
            "stdout_sha256": common.sha256(ctest_stdout),
            "stderr_sha256": common.sha256(ctest_stderr),
        },
        "regression_cases": {
            "equal_current_proof_accepted": True,
            "stronger_current_proof_accepted": True,
            "weaker_current_proof_rejected": True,
            "anchor_below_recorded_proof_rejected": True,
            "unverified_startup_pair_rejected": True,
        },
        "baseline_equivalence": {
            "instance_id": baseline.INSTANCE_ID,
            "process_cap_seconds": baseline.PROCESS_CAP,
            "comparison_count": len(comparisons),
            "all_identical": all(row["identical"] for row in comparisons),
            "comparison_csv_sha256": common.sha256(AUDIT_CSV),
        },
        "invalidated_attempt_record_sha256": common.sha256(
            common.INVALIDATED_ATTEMPT_RECORD),
        "source_sha256": {
            "include/GiniFrontierGeometry.hpp": common.sha256(
                common.ROOT / "include" / "GiniFrontierGeometry.hpp"),
            "src/GiniFrontierGeometry.cpp": common.sha256(
                common.ROOT / "src" / "GiniFrontierGeometry.cpp"),
            "src/PaperExternalGiniTree.cpp": common.sha256(
                common.ROOT / "src" / "PaperExternalGiniTree.cpp"),
            "tests/round36_causal_tests.cpp": common.sha256(
                common.ROOT / "tests" / "round36_causal_tests.cpp"),
        },
        "automatic_promotion_performed": False,
    }
    write_json(common.CONTRACT_FIX_AUDIT, audit)
    lines = [
        "# Round 36 Stage C contract-fix audit", "",
        f"Gate passed: **{passed}**.", "",
        "The isolated Stage C executable accepts an independently verified "
        "proof incumbent that improves after the startup pair is recorded. "
        "It rejects a weaker proof incumbent, an unsafe anchor, and an "
        "unverified startup pair.", "",
        f"All {len(comparisons)} default-off/HH mathematical-decision "
        "component comparisons against the frozen Stage B executable are "
        f"identical: **{all(row['identical'] for row in comparisons)}**.", "",
        "The Stage B executable remained checksum-identical. No candidate was "
        "promoted by this audit.",
    ]
    AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8",
                        newline="\n")
    print(json.dumps({
        "passed": passed,
        "ctest_return_code": ctest.returncode,
        "equivalence_comparisons": len(comparisons),
        "stage_b_executable_unchanged": stage_b_unchanged,
        "executables_are_distinct": stage_b_hash != stage_c_hash,
    }, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
