#!/usr/bin/env python3
"""Freeze the positive-signal Round 36 Stage C validation before execution."""

from __future__ import annotations

import json
import time
from pathlib import Path

import round35_common as r35
import round36_common as r36
import round36_stage_c_common as common
import prepare_round36 as stage_b_freeze


FINAL_DECISION = common.OUT / "final_audit_decision.json"
R35_COMPARATORS = (
    r35.OUT / "simple_vs_hga_1800s.csv",
    r35.OUT / "simple_vs_hga_3600s.csv",
    r35.OUT / "simple_vs_pgrb_1800s.csv",
    r35.OUT / "simple_vs_pgrb_3600s.csv",
    r35.OUT / "round35_1800s_matrix.csv",
    r35.OUT / "round35_3600s_v50_matrix.csv",
)
OUTPUTS = (common.CANDIDATE, common.MATRIX, common.COMMAND_FREEZE,
           common.FROZEN_MANIFEST)
STAGE_C_SOURCE_FILES = tuple(dict.fromkeys((
    *stage_b_freeze.SOURCE_FILES,
    "scripts/round36_stage_c_common.py",
    "scripts/freeze_round36_stage_c.py",
    "scripts/run_round36_stage_c.py",
    "scripts/launch_round36_stage_c_licensed.py",
    "scripts/audit_round36_stage_c_contract_fix.py",
    "tests/round36_stage_c_tests.py",
)))


def source_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    serial = 0
    for stage, source in (
        ("qualification_1800", r35.MATRIX_1800),
        ("independent_v50_3600", r35.MATRIX_3600),
    ):
        for source_row in r35.csv_rows(source):
            serial += 1
            cap = int(source_row["process_cap_seconds"])
            instance = source_row["instance_id"]
            safe = "".join(character if character.isalnum() or character in
                           "-_" else "_" for character in instance)
            rows.append({
                "round_id": 36,
                "stage": "C",
                "serial_order": serial,
                "validation_stage": stage,
                "stage_row_id": f"r36c_{serial:02d}_{safe}",
                "run_id": f"r36c_{serial:02d}_{safe}__bw_p__{cap}s",
                "instance_id": instance,
                "instance_path": source_row["path"],
                "instance_sha256": source_row["instance_sha256"],
                "V": int(source_row["V"]),
                "M": int(source_row["M"]),
                "Q": int(source_row["Q"]),
                "scenario": source_row["scenario"],
                "family": source_row["family"],
                "arm": common.ARM,
                "causal_arm": common.CAUSAL_ARM,
                "startup_variant": common.STARTUP,
                "split_normalization": common.NORMALIZATION,
                "K": 4,
                "rho": 0.01,
                "process_cap_seconds": cap,
                "watchdog_seconds": cap + common.WATCHDOG_SEPARATION,
                "source_freeze": common.relative(source),
                "source_serial_order": int(source_row["serial_order"]),
                "historical_source_round": 35,
                "frozen_before_stage_c_results": True,
            })
    if len(rows) != common.EXPECTED_ROWS:
        raise RuntimeError(f"expected 47 validation rows, found {len(rows)}")
    keys = {(row["validation_stage"], row["instance_id"]) for row in rows}
    if len(keys) != len(rows):
        raise RuntimeError("duplicate Stage C validation identity")
    return rows


def main() -> int:
    existing = [path for path in OUTPUTS if path.exists()]
    if existing:
        raise SystemExit("refusing to overwrite frozen Stage C files: " +
                         ", ".join(path.name for path in existing))
    decision = common.load_json(FINAL_DECISION)
    if (decision.get("stage_c_authorized_by_positive_signal") is not True or
            decision.get("classification") !=
            "decomposition_geometry_dominant" or
            int(decision.get("completed_official_rows", 0)) != 56 or
            int(decision.get("false_certificate_count", -1)) != 0):
        raise SystemExit("completed positive Stage B geometry gate is absent")
    stage_b_manifest = common.load_json(r36.FROZEN_MANIFEST)
    if common.sha256(common.STAGE_B_EXE) != stage_b_manifest[
            "gurobi_executable_sha256"]:
        raise SystemExit("Stage B executable identity changed")
    if not common.EXE.is_file():
        raise SystemExit("isolated Stage C contract-fix executable is missing")
    contract_fix_audit = common.load_json(common.CONTRACT_FIX_AUDIT)
    if contract_fix_audit.get("passed") is not True:
        raise SystemExit("Stage C contract-fix correctness audit is not green")
    invalidated_attempt = common.load_json(common.INVALIDATED_ATTEMPT_RECORD)
    if (invalidated_attempt.get("invalidated") is not True or
            int(invalidated_attempt.get("completed_valid_rows", -1)) != 18 or
            int(invalidated_attempt.get("failed_serial_order", -1)) != 19):
        raise SystemExit("the first Stage C attempt was not safely invalidated")
    for path in R35_COMPARATORS:
        if not path.is_file():
            raise SystemExit(f"missing historical comparator: {path}")

    rows = source_rows()
    candidate = {
        "schema": "round36-stage-c-candidate-definition-v2",
        "round_id": 36,
        "stage": "C",
        "candidate_name": "C6-BEST-PROOF-WIDE-ANCHOR-PROOF-NORM",
        "causal_arm": common.CAUSAL_ARM,
        "proof_incumbent": "min(verified HGA, verified SIMPLE)",
        "decomposition_anchor": "max(verified HGA, verified SIMPLE)",
        "split_normalization": common.NORMALIZATION,
        "startup_variant": common.STARTUP,
        "K": 4,
        "rho": 0.01,
        "gurobi_seed": 0,
        "threads": 1,
        "warm_resume": False,
        "automatic_promotion_performed": False,
        "stage_b_classification": decision["classification"],
        "stage_b_final_decision_sha256": common.sha256(FINAL_DECISION),
        "stage_b_executable_sha256": stage_b_manifest[
            "gurobi_executable_sha256"],
        "stage_c_executable_sha256": common.sha256(common.EXE),
        "conditional_contract_fix": {
            "scope": "Round36 causal launch validation only",
            "stronger_current_verified_proof_is_safe": True,
            "weaker_current_verified_proof_is_rejected": True,
            "default_c6_behavior_changed": False,
            "audit_path": common.relative(common.CONTRACT_FIX_AUDIT),
            "audit_sha256": common.sha256(common.CONTRACT_FIX_AUDIT),
            "invalidated_attempt_record_path": common.relative(
                common.INVALIDATED_ATTEMPT_RECORD),
            "invalidated_attempt_record_sha256": common.sha256(
                common.INVALIDATED_ATTEMPT_RECORD),
        },
        "validation_matrix": {
            "qualification_1800_rows": 35,
            "independent_v50_3600_rows": 12,
            "total_rows": common.EXPECTED_ROWS,
        },
        "historical_comparators": [
            {"path": common.relative(path), "sha256": common.sha256(path)}
            for path in R35_COMPARATORS
        ],
        "predeclared_performance_gate": {
            "validity_required": "47/47 valid rows and zero false certificates",
            "comparison": "fresh candidate versus compatible historical C6-HGA-FULL",
            "qualification_non_tie_win_fraction_minimum": 0.60,
            "independent_v50_non_tie_win_fraction_minimum": 0.60,
            "candidate_certificate_regressions_maximum": 0,
            "median_common_ub_gap_delta_maximum_each_stage": 0.0,
            "interpretation": "gate supports later contemporaneous validation only; never automatic promotion",
        },
        "frozen_before_stage_c_results": True,
        "frozen_at_unix_seconds": time.time(),
    }
    common.write_json(common.CANDIDATE, candidate)
    common.write_csv(common.MATRIX, rows)
    inventory = common.inventory()
    commands: dict[str, dict[str, object]] = {}
    for row in rows:
        run_dir = common.RUNS / row["run_id"]
        command = common.command_for(row, inventory[row["instance_id"]],
                                     run_dir)
        commands[row["run_id"]] = {
            "serial_order": row["serial_order"],
            "instance_id": row["instance_id"],
            "validation_stage": row["validation_stage"],
            "command": command,
        }
    common.write_json(common.COMMAND_FREEZE, {
        "schema": "round36-stage-c-command-freeze-v2",
        "round_id": 36,
        "stage": "C",
        "candidate_definition_sha256": common.sha256(common.CANDIDATE),
        "matrix_sha256": common.sha256(common.MATRIX),
        "commands": commands,
        "frozen_before_stage_c_results": True,
    })
    source_hashes = {
        path: common.sha256(common.ROOT / path)
        for path in STAGE_C_SOURCE_FILES
    }
    manifest = {
        "schema": "round36-stage-c-frozen-manifest-v2",
        "round_id": 36,
        "stage": "C",
        "expected_rows": common.EXPECTED_ROWS,
        "candidate_definition_sha256": common.sha256(common.CANDIDATE),
        "validation_matrix_sha256": common.sha256(common.MATRIX),
        "command_freeze_sha256": common.sha256(common.COMMAND_FREEZE),
        "stage_b_final_decision_sha256": common.sha256(FINAL_DECISION),
        "stage_b_executable_sha256": stage_b_manifest[
            "gurobi_executable_sha256"],
        "stage_c_executable_path": common.relative(common.EXE),
        "gurobi_executable_sha256": common.sha256(common.EXE),
        "source_tree_fingerprint": stage_b_freeze.tree_fingerprint(
            source_hashes),
        "source_file_sha256": source_hashes,
        "stage_b_source_tree_fingerprint": stage_b_manifest[
            "source_tree_fingerprint"],
        "contract_fix_audit_sha256": common.sha256(
            common.CONTRACT_FIX_AUDIT),
        "invalidated_attempt_record_sha256": common.sha256(
            common.INVALIDATED_ATTEMPT_RECORD),
        "instance_sha256": {row["instance_id"]: row["instance_sha256"]
                            for row in rows},
        "historical_comparator_sha256": {
            common.relative(path): common.sha256(path)
            for path in R35_COMPARATORS
        },
        "frozen_before_stage_c_results": True,
        "frozen_at_unix_seconds": candidate["frozen_at_unix_seconds"],
    }
    common.write_json(common.FROZEN_MANIFEST, manifest)
    print(json.dumps({
        "candidate": candidate["candidate_name"],
        "rows": len(rows),
        "matrix_sha256": manifest["validation_matrix_sha256"],
        "executable_sha256": manifest["gurobi_executable_sha256"],
        "stage_b_final_decision_sha256": manifest[
            "stage_b_final_decision_sha256"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
