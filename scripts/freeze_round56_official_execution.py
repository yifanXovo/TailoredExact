#!/usr/bin/env python3
"""Freeze the single Round 56 official executable and solver contract."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import round56_common as r56


SOURCE_FREEZE = "75e58521158aba8628ebc9444444ec3841415285"
SOURCE_TREE = "d66244f060aed61f40ac7cc72c931ab573f8cbff"
BUILD = r56.ROOT / "build" / "official-round56-paper-dataset-75e585211"
EXECUTABLE = BUILD / "ExactEBRP.exe"
EXPECTED_EXECUTABLE_SHA256 = "34e992060e3adffd3a7795c2c783672044996edd7234bf7e9f58a662b1c32fea"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=r56.ROOT, text=True).strip()


def main() -> int:
    if not EXECUTABLE.is_file():
        raise RuntimeError("official executable is missing")
    executable_sha = r56.sha256_file(EXECUTABLE)
    if executable_sha != EXPECTED_EXECUTABLE_SHA256:
        raise RuntimeError("official executable SHA-256 mismatch")
    if git("show", "-s", "--format=%T", SOURCE_FREEZE) != SOURCE_TREE:
        raise RuntimeError("source-freeze tree mismatch")
    source_changes = git(
        "diff", "--name-only", SOURCE_FREEZE, "--",
        "CMakeLists.txt", "include", "src", "tests",
    ).splitlines()
    if source_changes:
        raise RuntimeError("algorithm/build/test source changed after source freeze: " + ", ".join(source_changes))

    contract_path = r56.EVIDENCE / "official_solver_parameter_contract.json"
    contract = {
        "schema": "round56-official-solver-parameter-contract-v1",
        "algorithm_preset": "paper-k1-am-sf",
        "outer_controller": {
            "K0": 1,
            "split_point_rule": "midpoint",
            "split_score_rule": "balanced-normalized-closure",
            "tau": 0.08,
        },
        "fixed_interval_backend": "F0-CLEAN",
        "Gurobi": {
            "Threads": 1,
            "Seed": 0,
            "Presolve": "Auto",
            "MIPGap": 0.0,
            "MIPGapAbs": 0.0,
            "PreCrush": "default",
            "branching": "native/default",
        },
        "dynamic_user_cut_callback": False,
        "external_known_upper_bound": False,
        "archive_scanning": False,
        "imported_incumbent": False,
        "prior_result_interval_bounds": False,
        "focus_only": False,
        "one_optimizer_process_at_a_time": True,
    }
    r56.write_json(contract_path, contract)
    r56.write_json(r56.EVIDENCE / "official_execution_freeze.json", {
        "schema": "round56-official-execution-freeze-v1",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_freeze_commit": SOURCE_FREEZE,
        "source_freeze_tree": SOURCE_TREE,
        "official_build_path": r56.repo_path(BUILD),
        "official_executable_path": r56.repo_path(EXECUTABLE),
        "official_executable_sha256": executable_sha,
        "solver_parameter_contract_path": r56.repo_path(contract_path),
        "solver_parameter_contract_sha256": r56.sha256_file(contract_path),
        "scenario_manifest_sha256": r56.sha256_file(r56.EVIDENCE / "scenario_manifest.json"),
        "scenario_count": 50,
        "primary_q30_count": 40,
        "q20_sentinel_count": 10,
        "extension_7200_count": 9,
        "source_scope_changes_after_freeze": source_changes,
        "official_results_started": False,
    })
    r56.write_json(r56.EVIDENCE / "engineering_issue_resolution.json", {
        "schema": "round56-engineering-issue-resolution-v1",
        "issues": [
            {
                "issue_id": "R56-META-001",
                "resolution": "explicit T, process cap, service-time, distance-convention, scenario-hash, and run-hash result fields added",
                "fix_commit": SOURCE_FREEZE,
                "algorithm_semantics_changed": False,
                "historical_numerical_evidence_affected": False,
            },
            {
                "issue_id": "R56-GEN-001",
                "resolution": "distances regenerated from exact serialized coordinates before any optimizer result",
                "fix_commit": "eba41f90b",
                "algorithm_semantics_changed": False,
                "historical_evidence_affected": False,
                "round56_results_rerun_required": False,
            },
        ],
        "engineering_classification_candidate": "scenario_identity_bug_fixed",
    })
    r56.write_json(r56.EVIDENCE / "source_scope_audit.json", {
        "schema": "round56-source-scope-audit-v1",
        "source_freeze_commit": SOURCE_FREEZE,
        "algorithm_source_changes_after_freeze": [],
        "permitted_changes_in_freeze_commit": [
            "result metadata fields and CLI provenance inputs",
            "serialization of those descriptive fields",
            "Round56PaperBenchmarkTests and CMake registration",
        ],
        "algorithm_controller_or_formulation_change": False,
        "source_scope_pass": True,
    })
    print(json.dumps({
        "official_execution_frozen": True,
        "source_freeze_commit": SOURCE_FREEZE,
        "executable_sha256": executable_sha,
        "solver_parameter_contract_sha256": r56.sha256_file(contract_path),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
