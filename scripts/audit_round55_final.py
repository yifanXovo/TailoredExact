#!/usr/bin/env python3
"""Verify final Round 55 completeness, row closure, and evidence hashes."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_am_sf_station_state_chain_round55"


def rows(name: str) -> list[dict[str, str]]:
    with (EVIDENCE / name).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def read_json(name: str) -> dict[str, object]:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    expected_counts = {
        "stable_requalification_results.csv": 14,
        "live_pilot_120s.csv": 32,
        "fixed_interval_development_300s.csv": 42,
        "revision_1_results.csv": 28,
        "fixed_interval_confirmation_1200s.csv": 18,
        "fixed_interval_confirmation_1800s.csv": 38,
        "fixed_interval_key_long_3600s.csv": 22,
        "k1_integration_1800s.csv": 34,
        "k1_integration_3600s.csv": 10,
        "sealed_generalization_results.csv": 0,
        "expansion_results_7200s.csv": 0,
        "expansion_results_14400s.csv": 0,
        "split_counterfactual_matrix.csv": 0,
    }
    row_mismatches = {
        name: {"expected": expected, "actual": len(rows(name))}
        for name, expected in expected_counts.items() if len(rows(name)) != expected
    }
    required = [
        "final_report.md", "final_decision.json", "certificate_audit.csv",
        "severe_regression_audit.csv", "final_build_and_tests.md",
        "final_evidence_inventory.csv", "reproduction_commands.md",
        "manuscript_compile_status.md", "documentation_consistency_audit.csv",
        "manuscript_algorithm_identity_audit.md",
    ]
    missing_required = [name for name in required if not (EVIDENCE / name).is_file()]
    inventory_failures = []
    inventory = rows("final_evidence_inventory.csv")
    for row in inventory:
        path = ROOT / row["path"]
        if not path.is_file() or path.stat().st_size != int(row["size_bytes"]) or sha256(path) != row["sha256"]:
            inventory_failures.append(row["path"])
    certificate_rows = rows("certificate_audit.csv")
    false_count = sum(str(row["false_certificate"]).lower() in {"1", "true"}
                      for row in certificate_rows)
    preservation = read_json("preexisting_untracked_final_verification.json")
    final = read_json("final_decision.json")
    passed = not (row_mismatches or missing_required or inventory_failures or false_count or
                  not preservation["all_preserved"] or final["entered_stage_missing_rows"])
    result = {
        "schema": "round55-final-evidence-hash-audit-v1",
        "status": "pass" if passed else "fail",
        "row_count_mismatches": row_mismatches,
        "missing_required_files": missing_required,
        "inventory_row_count": len(inventory),
        "inventory_hash_failures": inventory_failures,
        "certificate_audit_rows": len(certificate_rows),
        "false_certificate_count": false_count,
        "preexisting_user_files_preserved": preservation["all_preserved"],
        "entered_stage_missing_rows": final["entered_stage_missing_rows"],
    }
    (EVIDENCE / "final_evidence_hash_audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
