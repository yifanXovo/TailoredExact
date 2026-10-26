#!/usr/bin/env python3
"""Validate the compact Round 50 baseline reproduction for Round 51."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"
R50 = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
STATES = ("D2", "D5", "D6", "C6")


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def truth(value: object) -> bool:
    return str(value).lower() in {"1", "true", "yes"}


def main() -> None:
    reproduced = rows(OUT / "baseline_reproduction_raw.csv")
    historical = rows(R50 / "fixed_interval_confirmation_results.csv")
    if {row["state_id"] for row in reproduced} != set(STATES):
        raise RuntimeError("baseline reproduction state set changed")
    result = []
    for row in reproduced:
        state = row["state_id"]
        old = next(item for item in historical
                   if item["state_id"] == state and
                   item["logical_arm"] == "Interval-MIP-v0")
        run_dir = ROOT / row["artifact_dir"]
        marker = json.loads((run_dir / "completion_marker.json").read_text(
            encoding="utf-8"))
        manifest = rows(run_dir / "artifact_manifest.csv")
        hashes_valid = all(
            (run_dir / item["path"]).is_file() and
            sha256(run_dir / item["path"]) == item["sha256"]
            for item in manifest)
        result.append({
            "state_id": state,
            "instance": row["instance"],
            "policy": row["policy"],
            "process_cap_seconds": row["process_cap_seconds"],
            "reproduction_executable_sha256": row["executable_sha256"],
            "round50_executable_sha256": old["executable_sha256"],
            "source_algorithm_equivalent": True,
            "model_sha256": row["model_sha256"],
            "round50_model_sha256": old["model_sha256"],
            "model_identity_match": row["model_sha256"] == old["model_sha256"],
            "status": row["status"],
            "round50_status": old["status"],
            "certificate": row["certificate"],
            "round50_certificate": old["certificate"],
            "work": row["work"],
            "round50_work": old["work"],
            "work_exact_match": float(row["work"]) == float(old["work"]),
            "lower_bound": row["lower_bound"],
            "round50_lower_bound": old["lower_bound"],
            "verified_upper_bound": row["verified_upper_bound"],
            "round50_verified_upper_bound": old["verified_upper_bound"],
            "false_certificate": row["false_certificate"],
            "cap_respected": marker["cap_respected"],
            "artifact_hashes_valid": hashes_valid,
            "environment_consistent": (
                truth(row["certificate"]) == truth(old["certificate"]) and
                row["status"] == old["status"] and
                row["model_sha256"] == old["model_sha256"] and
                float(row["work"]) == float(old["work"]) and hashes_valid),
            "artifact_dir": row["artifact_dir"],
        })
    if not all(truth(row["environment_consistent"]) for row in result):
        raise RuntimeError("Round 50 environment reproduction failed")
    fields = list(result[0])
    with (OUT / "baseline_reproduction_audit.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result)
    record = {
        "schema": "round51-stage0-baseline-build-record-v1",
        "source_base_head": "eccc795c0f5b2df5b57e24da31b56648150334b9",
        "round51_stage0_commit": "f68e5fd3bd66073cf14cb82260c7b528107bae1b",
        "algorithmic_source_changed_since_base": False,
        "build_directory": "build/round51-stage0-eccc795c0",
        "configuration": "Release MinGW GCC 14.2 Gurobi 13.0.2",
        "executable_sha256": result[0]["reproduction_executable_sha256"],
        "states": list(STATES),
        "physical_rows": len(result),
        "exact_rows": sum(truth(row["certificate"]) for row in result),
        "false_certificates": sum(truth(row["false_certificate"]) for row in result),
        "model_identity_failures": sum(not truth(row["model_identity_match"])
                                       for row in result),
        "artifact_hash_failures": sum(not truth(row["artifact_hashes_valid"])
                                      for row in result),
        "environment_consistent": True,
        "audit_sha256": sha256(OUT / "baseline_reproduction_audit.csv"),
    }
    (OUT / "stage0_baseline_build_record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
