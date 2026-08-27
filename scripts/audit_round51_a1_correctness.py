#!/usr/bin/env python3
"""Audit A1 model identity, disposable lifecycle, and smoke accounting."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"
MODEL_ROOT = EVIDENCE / "model_audit_runs_a1"
RECONSTRUCTION = (ROOT / "results" /
    "gf_k1_interval_mip_vnext_round50" /
    "fixed_interval_state_reconstruction_audit.csv")


def one(path: Path) -> dict[str, str]:
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))
    if len(rows) != 1:
        raise RuntimeError(f"expected one row in {path}")
    return rows[0]


def truth(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def main() -> None:
    frozen = list(csv.DictReader(RECONSTRUCTION.open(
        newline="", encoding="utf-8-sig")))
    model_rows: list[dict[str, object]] = []
    for state in frozen:
        state_id = state["state_id"]
        base_dir = MODEL_ROOT / f"{state_id}__m1-tight-big-m-v0"
        a1_dir = MODEL_ROOT / f"{state_id}__a1-root-sparse-2x2"
        base = json.loads((base_dir / "model_fingerprint.json").read_text(
            encoding="utf-8"))
        a1 = json.loads((a1_dir / "model_fingerprint.json").read_text(
            encoding="utf-8"))
        same_bytes = ((base_dir / "canonical_model.lp").read_bytes() ==
                      (a1_dir / "canonical_model.lp").read_bytes())
        status = (
            same_bytes and base["sha256"] == a1["sha256"]
            and base["rows"] == a1["rows"]
            and base["columns"] == a1["columns"]
            and base["nonzeros"] == a1["nonzeros"]
            and base["round50_symmetry_policy"] ==
                a1["round50_symmetry_policy"] == "v0-cardinality"
            and base["round51_subset_duration_big_m"] ==
                a1["round51_subset_duration_big_m"] ==
                    "tight-tsp-lower-bound")
        model_rows.append({
            "state_id": state_id,
            "m1_v0_model_sha256": base["sha256"],
            "a1_model_sha256": a1["sha256"],
            "canonical_lp_byte_identical": str(same_bytes).lower(),
            "objective_rows_domains_identical": str(same_bytes).lower(),
            "symmetry_policy_identical": str(
                base["round50_symmetry_policy"] ==
                a1["round50_symmetry_policy"]).lower(),
            "big_m_policy_identical": str(
                base["round51_subset_duration_big_m"] ==
                a1["round51_subset_duration_big_m"]).lower(),
            "status": "pass" if status else "fail",
            "failure_reason": "none" if status else "a1_model_delta_detected",
        })
    with (EVIDENCE / "adaptive_branching_model_correctness.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(model_rows[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(model_rows)

    smoke = EVIDENCE / "a1_smoke_runs" / "D2__a1-root-sparse-2x2"
    result = json.loads((smoke / "result.json").read_text(encoding="utf-8"))
    completion = json.loads((smoke / "completion_marker.json").read_text(
        encoding="utf-8"))
    overhead = one(smoke / "adaptive_branching_overhead_ledger.csv")
    reuse = one(smoke / "model_reuse_ledger.csv")
    probes = list(csv.DictReader((smoke /
        "adaptive_branching_probe_evidence.csv").open(
            newline="", encoding="utf-8-sig")))
    priorities = list(csv.DictReader((smoke /
        "adaptive_branching_priority_assignment_audit.csv").open(
            newline="", encoding="utf-8-sig")))
    candidate_directions = Counter(
        (row["variable_name"], row["semantic_family"]) for row in probes)
    family_candidates = Counter()
    for variable, family in candidate_directions:
        family_candidates[family] += 1
    accounting = (
        float(overhead["root_lp_work"])
        + float(overhead["child_probe_work"])
        + float(overhead["terminal_mip_work"]))
    expected_models = (
        int(overhead["root_model_reads"])
        + int(overhead["probe_model_reads"])
        + int(overhead["terminal_model_reads"]))
    checks = {
        "all_23_a1_models_byte_identical_to_m1_v0": all(
            row["status"] == "pass" for row in model_rows),
        "candidate_budget_at_most_four":
            int(overhead["candidate_count"]) <= 4,
        "candidate_family_cap_at_most_two": all(
            count <= 2 for count in family_candidates.values()),
        "each_candidate_has_down_and_up_probe": all(
            count == 2 for count in candidate_directions.values()),
        "probe_budget_at_most_eight": int(overhead["probe_count"]) <= 8,
        "every_probe_bound_readback_valid": all(
            truth(row["bound_override_readback_valid"]) for row in probes),
        "every_probe_fresh_and_fingerprint_matched": all(
            truth(row["fresh_disposable_model"]) and
            truth(row["model_fingerprint_match"]) for row in probes),
        "positive_priority_count_at_most_two":
            int(overhead["priority_count"]) <= 2,
        "every_positive_priority_exact_readback": all(
            truth(row["exact_readback"]) for row in priorities),
        "terminal_model_fresh": all(
            truth(row["terminal_model_fresh"]) for row in priorities),
        "no_in_memory_model_reuse": not truth(reuse["in_memory_model_reused"]),
        "one_fresh_model_per_root_probe_terminal_event":
            int(reuse["model_count"]) == int(reuse["model_read_count"])
            == int(reuse["optimize_count"]) == expected_models,
        "end_to_end_work_accounting_exact": math.isclose(
            accounting, float(overhead["total_work"]),
            rel_tol=0.0, abs_tol=1e-12) and math.isclose(
                accounting, float(result["work"]),
                rel_tol=0.0, abs_tol=1e-12),
        "lifecycle_valid": truth(overhead["lifecycle_valid"]),
        "smoke_exact_certificate": truth(result["certificate"]),
        "smoke_evidence_complete_and_cap_respected":
            truth(completion["evidence_complete"]) and
            truth(completion["cap_respected"]),
        "false_certificate_absent": not truth(result["false_certificate"]),
    }
    document = {
        "checks": checks,
        "executable_sha256": json.loads(
            (smoke / "command.json").read_text(encoding="utf-8"))[
                "executable_sha256"],
        "model_count": int(reuse["model_count"]),
        "probe_count": len(probes),
        "schema": "round51-a1-correctness-smoke-audit-v1",
        "selected_priority_count": len(priorities),
        "status": "pass" if all(checks.values()) else "fail",
    }
    (EVIDENCE / "adaptive_branching_correctness_smoke_audit.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if document["status"] != "pass":
        raise RuntimeError("A1 correctness smoke audit failed")
    print(json.dumps(document, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
