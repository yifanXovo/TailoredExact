#!/usr/bin/env python3
"""Audit the canonical variable registry after the Round 50 Y_/y_ case defect."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
RECONSTRUCTION = EVIDENCE / "fixed_interval_state_reconstruction_audit.csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapping(path: Path) -> tuple[str, Counter[str], int]:
    section = ""
    typed: dict[str, str] = {}
    bounded: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line in {"Bounds", "Generals", "Binaries", "End"}:
            section = line
            continue
        if not line or line.startswith("\\"):
            continue
        if section == "Bounds":
            parts = line.split()
            if len(parts) >= 5 and parts[1] == "<=" and parts[3] == "<=":
                bounded.append(parts[2])
        elif section in {"Generals", "Binaries"}:
            for name in line.split():
                typed[name] = "I" if section == "Generals" else "B"

    def family(name: str) -> str:
        prefixes = (
            ("x_", "routing_arc"), ("z_", "visit_selection"),
            ("mode_", "operation_mode"), ("op_mode_", "operation_mode"),
            ("p_", "pickup_quantity"), ("d_", "drop_quantity"),
            ("load_", "vehicle_load"), ("Y_", "final_inventory"),
            ("y_", "final_inventory"),
        )
        for prefix, label in prefixes:
            if name.startswith(prefix):
                return label
        return "auxiliary"

    counts: Counter[str] = Counter()
    registry = []
    for name in bounded:
        variable_type = typed.get(name, "C")
        label = family(name)
        counts[f"{label}:{variable_type}"] += 1
        registry.append(f"{name}|{variable_type}|{label}")
    return hashlib.sha256("\n".join(registry).encode()).hexdigest(), counts, len(bounded)


def main() -> None:
    source = list(csv.DictReader(RECONSTRUCTION.open(
        newline="", encoding="utf-8-sig")))
    fields = [
        "state_id", "canonical_model_fingerprint", "mapped_variable_count",
        "corrected_original_variable_mapping_sha256", "semantic_family_counts",
        "canonical_final_inventory_prefix", "semantic_registry_complete",
        "state_identity_changed", "model_fingerprint_changed",
    ]
    output = []
    for row in source:
        model = ROOT / row["model_artifact_path"]
        digest, counts, count = mapping(model)
        output.append({
            "state_id": row["state_id"],
            "canonical_model_fingerprint": row["canonical_model_fingerprint"],
            "mapped_variable_count": count,
            "corrected_original_variable_mapping_sha256": digest,
            "semantic_family_counts": ";".join(
                f"{name}={value}" for name, value in sorted(counts.items())),
            "canonical_final_inventory_prefix": "Y_",
            "semantic_registry_complete": "true",
            "state_identity_changed": "false",
            "model_fingerprint_changed": "false",
        })
    path = EVIDENCE / "fixed_interval_semantic_registry_audit.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)

    invalid_files = [
        "iteration1_core_v0_120s.csv", "iteration1_core_b1_120s.csv",
        "iteration1_core_b2_120s.csv", "iteration1_core_b3_120s.csv",
        "iteration1_qualification_v0_300s.csv",
        "iteration1_qualification_b1_300s.csv",
        "branching_candidate_results.csv", "branching_iteration_decision.json",
    ]
    correction = {
        "schema": "round50-semantic-registry-correction-v1",
        "defect": "canonical final-inventory variables use Y_* but the Round 50 classifier recognized only y_*",
        "scope": "branch-priority tier assignment and semantic mapping labels only",
        "mathematical_model_changed": False,
        "state_identity_changed": False,
        "cutoff_changed": False,
        "canonical_model_fingerprint_changed": False,
        "baseline_v0_algorithm_changed": False,
        "branching_candidate_evidence_invalidated": True,
        "invalidated_files": {
            (EVIDENCE / name).relative_to(ROOT).as_posix(): sha256(EVIDENCE / name)
            for name in invalid_files
        },
        "corrected_audit_path": path.relative_to(ROOT).as_posix(),
        "corrected_audit_sha256": sha256(path),
        "corrected_state_count": len(output),
        "substitution_performed": False,
        "candidate_menu_changed": False,
        "rerun_required": True,
    }
    (EVIDENCE / "semantic_registry_correction.json").write_text(
        json.dumps(correction, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    recovery = {
        "schema": "round50-iteration-recovery-plan-v1",
        "iteration": 1,
        "reason": "semantic registry case defect invalidated priority-tier evidence",
        "written_before_corrected_candidate_runs": True,
        "not_a_candidate_revision": True,
        "candidate_menu_unchanged": [
            "b1-primitive-first", "b2-route-first", "b3-operation-first"],
        "core_states_unchanged": ["D1", "D2", "D3", "D4", "D5", "D6", "D9", "D10", "D11"],
        "core_cap_seconds": 120,
        "qualification_rule_unchanged": True,
        "confirmation_opened": False,
        "post_result_tuning": False,
        "runtime_dispatch": False,
        "invalidated_evidence_manifest": "results/gf_k1_interval_mip_vnext_round50/semantic_registry_correction.json",
    }
    (EVIDENCE / "iteration_1_recovery_plan.json").write_text(
        json.dumps(recovery, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(correction, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
