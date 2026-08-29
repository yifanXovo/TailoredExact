#!/usr/bin/env python3
"""Assemble and audit the frozen Round 50 fixed-state confirmation."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
SUMMARY_ROOT = EVIDENCE / "official_confirmation" / "summaries"
EXPECTED = [f"D{i}" for i in range(1, 15)] + [f"C{i}" for i in range(1, 10)]


def truth(value: object) -> bool:
    return str(value).lower() in {"1", "true", "yes"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    physical: dict[str, dict[str, str]] = {}
    for path in sorted(SUMMARY_ROOT.glob("v0_*.csv")):
        for row in csv.DictReader(path.open(newline="", encoding="utf-8-sig")):
            state = row["state_id"]
            if state in physical:
                raise RuntimeError(f"duplicate physical confirmation state {state}")
            physical[state] = row
    if set(physical) != set(EXPECTED):
        raise RuntimeError(
            f"confirmation states mismatch: missing={set(EXPECTED)-set(physical)} "
            f"extra={set(physical)-set(EXPECTED)}")
    executable_hashes = {row["executable_sha256"] for row in physical.values()}
    if len(executable_hashes) != 1:
        raise RuntimeError("physical confirmation uses multiple executables")
    if any(not truth(row["evidence_complete"]) or
           not truth(row["cap_respected"]) or
           not truth(row["model_identity_match"])
           for row in physical.values()):
        raise RuntimeError("incomplete or identity-invalid physical row")

    logical_fields = [
        "logical_arm", "physical_run_shared", "physical_run_id",
        "equivalence_basis", *next(iter(physical.values())).keys(),
    ]
    logical_rows: list[dict[str, object]] = []
    for state in EXPECTED:
        row = physical[state]
        for arm in ("Interval-MIP-v0", "Interval-MIP-vNext"):
            logical_rows.append({
                "logical_arm": arm,
                "physical_run_shared": True,
                "physical_run_id": f"official-confirmation:{state}",
                "equivalence_basis": (
                    "vNext accepted zero modifications and is definitionally "
                    "the interval-mip-v0 execution policy"),
                **row,
            })
    results_path = EVIDENCE / "fixed_interval_confirmation_results.csv"
    with results_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=logical_fields)
        writer.writeheader()
        writer.writerows(logical_rows)

    pair_fields = [
        "state_id", "panel", "v0_status", "vnext_status",
        "v0_certificate", "vnext_certificate", "v0_work", "vnext_work",
        "work_ratio", "v0_gi", "vnext_gi", "gi_ratio", "v0_gap",
        "vnext_gap", "severe_regression", "correctness_failure",
        "false_certificate", "physical_run_shared",
    ]
    panel_rows: dict[str, list[dict[str, object]]] = {
        "development": [], "confirmation": []}
    for state in EXPECTED:
        row = physical[state]
        work = float(row["work"])
        gi = float(row["gi_common_horizon"])
        status = row["status"]
        paired = {
            "state_id": state,
            "panel": row["panel"],
            "v0_status": status,
            "vnext_status": status,
            "v0_certificate": row["certificate"],
            "vnext_certificate": row["certificate"],
            "v0_work": row["work"],
            "vnext_work": row["work"],
            "work_ratio": 1.0 if work >= 0 else "",
            "v0_gi": row["gi_common_horizon"],
            "vnext_gi": row["gi_common_horizon"],
            "gi_ratio": 1.0 if gi >= 0 else "",
            "v0_gap": row["gap"],
            "vnext_gap": row["gap"],
            "severe_regression": False,
            "correctness_failure": status == "failed",
            "false_certificate": truth(row["false_certificate"]),
            "physical_run_shared": True,
        }
        panel_rows[row["panel"]].append(paired)
    for panel, filename in (
            ("development", "fixed_interval_development_summary.csv"),
            ("confirmation", "fixed_interval_confirmation_summary.csv")):
        with (EVIDENCE / filename).open(
                "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=pair_fields)
            writer.writeheader()
            writer.writerows(panel_rows[panel])

    physical_rows = list(physical.values())
    exact = sum(truth(row["certificate"]) for row in physical_rows)
    failed = sum(row["status"] == "failed" for row in physical_rows)
    capped = sum(row["status"] == "capped" for row in physical_rows)
    false = sum(truth(row["false_certificate"]) for row in physical_rows)
    audit = {
        "schema": "round50-interval-mip-vnext-promotion-audit-v1",
        "status": "complete",
        "physical_row_count": len(physical_rows),
        "logical_comparison_row_count": len(logical_rows),
        "development_physical_rows": 14,
        "confirmation_physical_rows": 9,
        "physical_exact_rows": exact,
        "physical_capped_rows": capped,
        "physical_failed_rows": failed,
        "false_certificates": false,
        "correctness_failures": failed,
        "severe_confirmation_regressions": 0,
        "v0_certificate_count": exact,
        "vnext_certificate_count": exact,
        "paired_exact_work_geometric_mean_ratio": 1.0,
        "capped_material_progress_gains": 0,
        "structural_roles_improved": 0,
        "numerical_conditioning_worsened": False,
        "same_official_executable": True,
        "official_executable_sha256": next(iter(executable_hashes)),
        "physical_run_sharing": True,
        "physical_run_sharing_basis": (
            "the Stage 3 freeze accepted zero factors; vNext and v0 invoke the "
            "same policy in the same executable with identical model fingerprints "
            "and runtime options"),
        "promotion_supported": False,
        "classification": "interval_mip_v0_retained",
        "reasons": [
            "C1 is a strict-certificate correctness failure: native OPTIMAL "
            "bound is below the frozen verified cutoff by about 1.76e-7",
            "vNext contains no accepted change, so exact-row Work ratio is 1.0 "
            "rather than the required <=0.95",
            "no capped hard state or structural role gains proof progress",
        ],
        "stage5_1800s_opened": False,
        "stage5_reason": "Stage 4 promotion gate failed",
        "k1_backend_integration_eligible": False,
        "confirmation_results_sha256": sha256(results_path),
    }
    (EVIDENCE / "interval_mip_vnext_promotion_audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    key_path = EVIDENCE / "fixed_interval_1800s_key_results.csv"
    with key_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "stage", "status", "row_count", "reason"])
        writer.writeheader()
        writer.writerow({
            "stage": "Stage 5",
            "status": "not_opened",
            "row_count": 0,
            "reason": "Interval-MIP-vNext did not pass Stage 4",
        })
    print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
