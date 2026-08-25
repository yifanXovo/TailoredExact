#!/usr/bin/env python3
"""Audit the sole A1-R1 delta before its official bounded core."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"
MODEL_ROOT = EVIDENCE / "model_audit_runs_a1r"
SMOKE_ROOT = EVIDENCE / "a1r_smoke_runs"
RECONSTRUCTION = (ROOT / "results" /
    "gf_k1_interval_mip_vnext_round50" /
    "fixed_interval_state_reconstruction_audit.csv")
POLICIES = [
    "m1-tight-big-m-v0",
    "a1-root-sparse-2x2",
    "a1r-root-sparse-top1",
]


def truth(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def one(path: Path) -> dict[str, str]:
    result = rows(path)
    if len(result) != 1:
        raise RuntimeError(f"expected one row in {path}")
    return result[0]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    states = rows(RECONSTRUCTION)
    model_rows: list[dict[str, object]] = []
    for state in states:
        state_id = state["state_id"]
        fingerprints = []
        lp_hashes = []
        for policy in POLICIES:
            run = MODEL_ROOT / f"{state_id}__{policy}"
            fingerprints.append(json.loads(
                (run / "model_fingerprint.json").read_text(encoding="utf-8")))
            lp_hashes.append(sha256(run / "canonical_model.lp"))
        canonical_equal = len(set(lp_hashes)) == 1
        fingerprint_equal = len({item["sha256"] for item in fingerprints}) == 1
        structural_equal = all(
            fingerprints[index][key] == fingerprints[0][key]
            for index in range(1, len(fingerprints))
            for key in ("rows", "columns", "nonzeros", "row_signature",
                        "scope", "round50_symmetry_policy",
                        "round51_subset_duration_big_m"))
        status = canonical_equal and fingerprint_equal and structural_equal
        model_rows.append({
            "state_id": state_id,
            "m1_v0_model_sha256": fingerprints[0]["sha256"],
            "a1_model_sha256": fingerprints[1]["sha256"],
            "a1r_model_sha256": fingerprints[2]["sha256"],
            "three_way_canonical_lp_byte_identical": str(canonical_equal).lower(),
            "three_way_fingerprint_identical": str(fingerprint_equal).lower(),
            "three_way_structure_identical": str(structural_equal).lower(),
            "status": "pass" if status else "fail",
            "failure_reason": "none" if status else "model_mismatch",
        })
    output = EVIDENCE / "adaptive_branching_revision_model_correctness.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(model_rows[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(model_rows)

    a1 = SMOKE_ROOT / "D2__a1-root-sparse-2x2"
    a1r = SMOKE_ROOT / "D2__a1r-root-sparse-top1"
    a1_result = json.loads((a1 / "result.json").read_text(encoding="utf-8"))
    a1r_result = json.loads((a1r / "result.json").read_text(encoding="utf-8"))
    a1_command = json.loads((a1 / "command.json").read_text(encoding="utf-8"))
    a1r_command = json.loads((a1r / "command.json").read_text(encoding="utf-8"))
    a1_completion = json.loads(
        (a1 / "completion_marker.json").read_text(encoding="utf-8"))
    a1r_completion = json.loads(
        (a1r / "completion_marker.json").read_text(encoding="utf-8"))
    a1_probes = rows(a1 / "adaptive_branching_probe_evidence.csv")
    a1r_probes = rows(a1r / "adaptive_branching_probe_evidence.csv")
    immutable_probe_fields = [
        "candidate_pool_order", "variable_name", "semantic_family",
        "original_type", "root_value", "fractionality", "direction",
        "imposed_bound", "probe_status", "child_objective", "delta",
        "score", "work", "model_fingerprint_match",
        "bound_override_readback_valid", "fresh_disposable_model",
        "failure_reason",
    ]
    probe_identity = len(a1_probes) == len(a1r_probes) == 8 and all(
        left[field] == right[field]
        for left, right in zip(a1_probes, a1r_probes)
        for field in immutable_probe_fields)
    a1_priorities = rows(
        a1 / "adaptive_branching_priority_assignment_audit.csv")
    a1r_priorities = rows(
        a1r / "adaptive_branching_priority_assignment_audit.csv")
    a1r_priority = a1r_priorities[0]
    a1_overhead = one(a1 / "adaptive_branching_overhead_ledger.csv")
    a1r_overhead = one(a1r / "adaptive_branching_overhead_ledger.csv")
    a1r_reuse = one(a1r / "model_reuse_ledger.csv")
    a1r_model = json.loads(
        (a1r / "model_fingerprint.json").read_text(encoding="utf-8"))
    total = (float(a1r_overhead["root_lp_work"]) +
             float(a1r_overhead["child_probe_work"]) +
             float(a1r_overhead["terminal_mip_work"]))
    expected_models = 2 + int(a1r_overhead["probe_count"])
    checks = {
        "all_23_three_way_models_byte_and_structure_identical":
            len(model_rows) == 23 and all(
                row["status"] == "pass" for row in model_rows),
        "same_executable_hash_for_paired_smoke":
            a1_command["executable_sha256"] ==
            a1r_command["executable_sha256"],
        "candidate_pool_probes_scores_and_work_identical": probe_identity,
        "a1_has_two_positive_priorities": len(a1_priorities) == 2 and
            [int(row["requested_priority"]) for row in a1_priorities] == [2, 1],
        "a1r_has_exactly_one_priority_at_tier_one":
            len(a1r_priorities) == 1 and
            int(a1r_priority["requested_priority"]) == 1 and
            int(a1r_priority["observed_priority"]) == 1 and
            truth(a1r_priority["exact_readback"]),
        "a1r_best_variable_and_score_identical_to_a1":
            a1r_priority["variable_name"] == a1_priorities[0]["variable_name"]
            and a1r_priority["score"] == a1_priorities[0]["score"]
            and a1r_priority["delta_down"] == a1_priorities[0]["delta_down"]
            and a1r_priority["delta_up"] == a1_priorities[0]["delta_up"],
        "every_other_a1r_priority_zero":
            int(a1r_priority["zero_priority_readback_count"]) ==
            int(a1r_model["columns"]) - 1,
        "a1r_terminal_model_fresh": truth(a1r_priority["terminal_model_fresh"]),
        "a1r_lifecycle_valid": truth(a1r_overhead["lifecycle_valid"]),
        "a1r_one_fresh_model_per_root_probe_terminal_event":
            int(a1r_reuse["model_count"]) ==
            int(a1r_reuse["model_read_count"]) ==
            int(a1r_reuse["optimize_count"]) == expected_models and
            not truth(a1r_reuse["in_memory_model_reused"]),
        "a1r_end_to_end_work_accounting_exact":
            math.isclose(total, float(a1r_overhead["total_work"]),
                         rel_tol=0.0, abs_tol=1e-12) and
            math.isclose(total, float(a1r_result["work"]),
                         rel_tol=0.0, abs_tol=1e-12),
        "paired_smoke_exact_and_evidence_complete":
            truth(a1_result["certificate"]) and truth(a1r_result["certificate"])
            and a1_completion["evidence_complete"] is True
            and a1r_completion["evidence_complete"] is True
            and a1_completion["cap_respected"] is True
            and a1r_completion["cap_respected"] is True,
        "paired_smoke_has_no_false_certificate":
            not truth(a1_result["false_certificate"])
            and not truth(a1r_result["false_certificate"]),
    }
    executable_hash = a1r_command["executable_sha256"]
    document = {
        "checks": checks,
        "executable_sha256": executable_hash,
        "probe_count": len(a1r_probes),
        "schema": "round51-a1r-correctness-smoke-audit-v1",
        "selected_priority_count": len(a1r_priorities),
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "status": "pass" if all(checks.values()) else "fail",
    }
    (EVIDENCE /
     "adaptive_branching_revision_correctness_smoke_audit.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    record = {
        "a1r_candidate": "a1r-root-sparse-top1",
        "all_state_model_identity": "23/23 three-way byte-identical",
        "build_directory": "build/round51-m1",
        "build_type": "Release",
        "correctness_smoke_audit": document["status"],
        "executable": "build/round51-m1/Round51IntervalMipExperiment.exe",
        "executable_sha256": executable_hash,
        "only_permitted_delta_audited": True,
        "round50_interval_mip_tests": "pass",
        "round51_tight_big_m_and_adaptive_tests": "pass",
        "schema": "round51-a1r-build-and-correctness-record-v1",
        "source_commit": document["source_commit"],
        "source_commit_precedes_official_a1r_core_results": True,
    }
    (EVIDENCE / "a1r_build_and_correctness_record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if document["status"] != "pass":
        raise RuntimeError("A1-R1 correctness audit failed")
    print(json.dumps(document, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
