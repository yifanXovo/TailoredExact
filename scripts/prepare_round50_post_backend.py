#!/usr/bin/env python3
"""Close ineligible K1 integration and freeze v0 counterfactual parents."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
FULL_EXE = ROOT / "build" / "official-round50-fe793b20e" / "ExactEBRP.exe"
CASES = (
    ("major_root", "D1", "L0"),
    ("strong_control_root", "D3", "L0"),
    ("numerical_endpoint_root", "D12", "L0"),
    ("v12_m2_root", "D6", "L0"),
    ("tight3102_L0_0", "D9", "L0.0"),
    ("high_imbalance_matched", "D13", "L0.1.0"),
    ("moderate3301_root", "D14", "L0"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def main() -> None:
    promotion = json.loads((
        EVIDENCE / "interval_mip_vnext_promotion_audit.json").read_text(
            encoding="utf-8"))
    if promotion["k1_backend_integration_eligible"]:
        raise RuntimeError("this closure script is only for the ineligible path")

    control_fields = [
        "stage", "status", "physical_row_count", "logical_row_count", "reason"]
    for filename, stage in (
            ("k1_integration_300s_results.csv", "K1 Stage 300s"),
            ("k1_integration_1200s_results.csv", "K1 Stage 1200s"),
            ("k1_integration_1800s_results.csv", "K1 Stage 1800s"),
            ("k1_historical_direct_comparison.csv", "K1 direct comparison")):
        with (EVIDENCE / filename).open(
                "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=control_fields)
            writer.writeheader()
            writer.writerow({
                "stage": stage,
                "status": "not_opened",
                "physical_row_count": 0,
                "logical_row_count": 0,
                "reason": (
                    "Interval-MIP-vNext failed Stage 4 and is exactly v0; "
                    "K1-AM-vNext integration is not eligible"),
            })
    k1_audit = {
        "schema": "round50-k1-backend-promotion-audit-v1",
        "status": "complete_not_opened",
        "backend_promotion_supported": False,
        "integration_eligible": False,
        "research_mode_added": False,
        "paper_preset_changed": False,
        "physical_rows": {"300s": 0, "1200s": 0, "1800s": 0},
        "logical_rows": {"300s": 0, "1200s": 0, "1800s": 0},
        "classification": "historical_k1_am_retained",
        "reason": (
            "the candidate backend accepted zero changes, failed the fixed-state "
            "promotion gate, and is definitionally identical to historical K1-AM's backend"),
        "counterfactual_recomputation_still_required": True,
    }
    (EVIDENCE / "k1_backend_promotion_audit.json").write_text(
        json.dumps(k1_audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    manifest = {
        row["state_id"]: row for row in csv_rows(
            EVIDENCE / "fixed_interval_state_manifest.csv")}
    reconstruction = {
        row["state_id"]: row for row in csv_rows(
            EVIDENCE / "fixed_interval_state_reconstruction_audit.csv")}
    backend_definition = EVIDENCE / "interval_mip_vnext_definition.json"
    backend_hash = sha256(backend_definition)
    rows = []
    for case, state, interval in CASES:
        frozen = manifest[state]
        audit = reconstruction[state]
        source = ROOT / frozen["historical_source_run"]
        decisions = csv_rows(source / "external" / "adaptive_mass_decision_ledger.csv")
        decision = next((row for row in decisions
                         if row["interval_id"] == interval), None)
        if decision is None:
            raise RuntimeError(f"historical parent decision missing: {case}")
        model_path = source / "external" / "models" / f"{interval}.lp"
        coverage_path = source / "interval_coverage_ledger.csv"
        if not model_path.is_file() or not coverage_path.is_file():
            raise RuntimeError(f"historical parent evidence missing: {case}")
        identity_payload = {
            "input_sha256": frozen["input_sha256"],
            "interval": interval,
            "parent_bound": decision["B_p"],
            "child_left_bound": decision["B_L"],
            "child_right_bound": decision["B_R"],
            "incumbent": decision["U"],
            "model_sha256": sha256(model_path),
            "coverage_sha256": sha256(coverage_path),
            "backend_definition_sha256": backend_hash,
        }
        parent_identity = hashlib.sha256(json.dumps(
            identity_payload, sort_keys=True, separators=(",", ":"))
            .encode("utf-8")).hexdigest()
        rows.append({
            "case": case,
            "anchor_state_id": state,
            "instance": frozen["instance"],
            "input_path": frozen["input_path"],
            "input_sha256": frozen["input_sha256"],
            "interval_id": interval,
            "incumbent": decision["U"],
            "parent_bound": decision["B_p"],
            "left_child_lp_bound": decision["B_L"],
            "right_child_lp_bound": decision["B_R"],
            "active_coverage_sha256": sha256(coverage_path),
            "model_fingerprint": sha256(model_path),
            "vnext_backend_identity_sha256": backend_hash,
            "full_executable_sha256": sha256(FULL_EXE),
            "target_contract": (
                "historical K1-AM native-target and exact-close lifecycle unchanged"),
            "retain_contract": "preserve parent; recursive split disabled locally",
            "midpoint_contract": (
                "perform exactly one midpoint split; solve both children; "
                "suppress descendant splits"),
            "parent_identity_sha256": parent_identity,
            "historical_parent_decision_source": str(
                (source / "external" / "adaptive_mass_decision_ledger.csv")
                .relative_to(ROOT)).replace("\\", "/"),
            "reconstruction_model_fingerprint": audit[
                "canonical_model_fingerprint"] if interval == frozen["interval_id"] else "",
        })
    parent_path = EVIDENCE / "vnext_counterfactual_parent_manifest.csv"
    with parent_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    protocol = {
        "schema": "round50-vnext-counterfactual-protocol-v1",
        "status": "frozen_before_runtime",
        "case_count": len(rows),
        "arms": ["RETAIN", "MIDPOINT"],
        "physical_row_count": 14,
        "process_cap_seconds_per_arm": 1200,
        "optional_extension_cap_seconds": 1800,
        "optional_extensions_entered": 0,
        "backend": "Interval-MIP-vNext == Interval-MIP-v0",
        "full_executable_sha256": sha256(FULL_EXE),
        "parent_manifest_sha256": sha256(parent_path),
        "no_old_label_reuse": True,
        "no_recursive_split_after_forced_action": True,
        "runtime_dispatch": False,
    }
    (EVIDENCE / "vnext_counterfactual_protocol.json").write_text(
        json.dumps(protocol, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(protocol, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
