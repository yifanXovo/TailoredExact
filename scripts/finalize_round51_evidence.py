#!/usr/bin/env python3
"""Assemble cross-stage Round 51 audits and the bounded negative decision."""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"
ROUND50 = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"


def truth(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def write_rows(path: Path, data: list[dict[str, object]]) -> None:
    if not data:
        raise RuntimeError(f"refusing to write empty table: {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(data[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(data)


def main() -> None:
    summaries = [
        ("stage0_reproduction", "baseline_reproduction_raw.csv"),
        ("m1_small_exact", "big_m_small_exact_raw.csv"),
        ("m1_core_comparator", "m1_core_v0_raw.csv"),
        ("m1_core_candidate", "m1_core_m1_raw.csv"),
        ("symmetry_core_s1", "symmetry_core_s1_raw.csv"),
        ("symmetry_core_s1r", "symmetry_core_s1r_raw.csv"),
        ("symmetry_development_comparator", "symmetry_development_m1_raw.csv"),
        ("symmetry_development_s1", "symmetry_development_s1_raw.csv"),
        ("symmetry_development_s1r", "symmetry_development_s1r_raw.csv"),
        ("a1_core_comparator", "a1_core_m1_raw.csv"),
        ("a1_core_candidate", "a1_core_a1_raw.csv"),
        ("a1r_core_comparator", "a1r_core_m1_raw.csv"),
        ("a1r_core_candidate", "a1r_core_a1r_raw.csv"),
    ]
    certificate_rows: list[dict[str, object]] = []
    for stage, filename in summaries:
        for row in rows(EVIDENCE / filename):
            valid = (truth(row.get("evidence_complete", True))
                     and truth(row.get("cap_respected", True))
                     and not truth(row.get("false_certificate", False)))
            certificate_rows.append({
                "stage": stage,
                "source_summary": filename,
                "state_id": row["state_id"],
                "policy": row["policy"],
                "process_cap_seconds": row["process_cap_seconds"],
                "executable_sha256": row["executable_sha256"],
                "model_sha256": row["model_sha256"],
                "status": row["status"],
                "certificate": str(truth(row["certificate"])).lower(),
                "certificate_class": row["certificate_class"],
                "false_certificate":
                    str(truth(row["false_certificate"])).lower(),
                "evidence_complete":
                    str(truth(row.get("evidence_complete", True))).lower(),
                "cap_respected":
                    str(truth(row.get("cap_respected", True))).lower(),
                "failure_reason": row.get("failure_reason", "none"),
                "artifact_dir": row["artifact_dir"],
                "audit_status": "pass" if valid else "fail",
            })
    write_rows(EVIDENCE / "certificate_audit.csv", certificate_rows)
    if any(row["audit_status"] != "pass" for row in certificate_rows):
        raise RuntimeError("certificate/evidence audit failure")

    reproduction = {row["state_id"]: row for row in rows(
        EVIDENCE / "baseline_reproduction_audit.csv")}
    default_rows: list[dict[str, object]] = []
    for model in rows(EVIDENCE / "big_m_model_delta_audit.csv"):
        state = model["state_id"]
        runtime = reproduction.get(state)
        runtime_pass = (runtime is not None and
                        truth(runtime["model_identity_match"]) and
                        truth(runtime["work_exact_match"]) and
                        runtime["status"] == runtime["round50_status"] and
                        truth(runtime["certificate"]) ==
                        truth(runtime["round50_certificate"]))
        default_rows.append({
            "state_id": state,
            "historical_policy": "interval-mip-v0",
            "round50_frozen_model_sha256": model["historical_model_sha256"],
            "round51_default_off_model_sha256": model["historical_model_sha256"],
            "canonical_model_exact_match":
                model["historical_matches_round50_frozen"],
            "m1_target_affected": model["big_m_affected"],
            "v_gt_12_byte_identical_under_m1":
                model["v_gt_12_model_identical"],
            "runtime_reproduction_available": str(runtime is not None).lower(),
            "runtime_status_certificate_work_exact_match":
                str(runtime_pass).lower() if runtime is not None else
                "not_sampled",
            "audit_status": "pass" if
                truth(model["historical_matches_round50_frozen"]) and
                (runtime is None or runtime_pass) else "fail",
        })
    write_rows(EVIDENCE / "default_off_equivalence.csv", default_rows)
    if any(row["audit_status"] != "pass" for row in default_rows):
        raise RuntimeError("default-off equivalence failure")

    severe_rows: list[dict[str, object]] = []
    sources = [
        ("M1", "big_m_severe_regression_audit.csv"),
        ("symmetry", "symmetry_m1_severe_regression_audit.csv"),
        ("adaptive", "adaptive_branching_severe_regression_audit.csv"),
    ]
    for stage, filename in sources:
        for row in rows(EVIDENCE / filename):
            severe_rows.append({
                "stage": stage,
                "source_audit": filename,
                "mechanism": row.get("mechanism", stage),
                "candidate_policy": row["candidate_policy"],
                "state_id": row["state_id"],
                "baseline_certificate": row["baseline_certificate"],
                "candidate_certificate": row["candidate_certificate"],
                "work_ratio": row["work_ratio"],
                "work_absolute_increase": row["work_absolute_increase"],
                "gi_ratio": row["gi_ratio"],
                "gi_absolute_increase": row["gi_absolute_increase"],
                "gap_ratio": row["gap_ratio"],
                "gap_absolute_increase": row["gap_absolute_increase"],
                "severe_regression": row["severe_regression"],
                "reason": row["reason"],
            })
    write_rows(EVIDENCE / "severe_regression_audit.csv", severe_rows)

    inventories = [
        ("stage0_reproduction", "baseline_reproduction_runs",
         "baseline_reproduction_raw.csv"),
        ("m1_small_exact", "big_m_small_exact_runs",
         "big_m_small_exact_raw.csv"),
        ("m1_core", "m1_core_runs", "m1_core_v0_raw.csv|m1_core_m1_raw.csv"),
        ("symmetry_core", "symmetry_core_runs",
         "symmetry_core_s1_raw.csv|symmetry_core_s1r_raw.csv"),
        ("symmetry_development", "symmetry_development_runs",
         "symmetry_development_m1_raw.csv|symmetry_development_s1_raw.csv|symmetry_development_s1r_raw.csv"),
        ("a1_core", "a1_core_runs",
         "a1_core_m1_raw.csv|a1_core_a1_raw.csv"),
        ("a1r_core", "a1r_core_runs",
         "a1r_core_m1_raw.csv|a1r_core_a1r_raw.csv"),
        ("all_state_m1_model_audit", "model_audit_runs", "big_m_model_delta_audit.csv"),
        ("all_state_a1_model_audit", "model_audit_runs_a1", "adaptive_branching_model_correctness.csv"),
        ("all_state_a1r_model_audit", "model_audit_runs_a1r", "adaptive_branching_revision_model_correctness.csv"),
    ]
    inventory_rows: list[dict[str, object]] = []
    for stage, dirname, compact in inventories:
        directory = EVIDENCE / dirname
        run_dirs = [path for path in directory.iterdir() if path.is_dir()]
        files = [path for path in directory.rglob("*") if path.is_file()]
        policies = sorted({path.name.split("__", 1)[1]
                           for path in run_dirs if "__" in path.name})
        states = sorted({path.name.split("__", 1)[0]
                         for path in run_dirs if "__" in path.name})
        inventory_rows.append({
            "stage": stage,
            "raw_directory": directory.relative_to(ROOT).as_posix(),
            "run_directory_count": len(run_dirs),
            "state_count": len(states),
            "policies": "|".join(policies),
            "file_count": len(files),
            "total_bytes": sum(path.stat().st_size for path in files),
            "compact_committed_evidence": compact,
            "raw_available_locally": str(bool(files)).lower(),
        })
    write_rows(EVIDENCE / "raw_evidence_inventory.csv", inventory_rows)

    stages = [
        {"stage": "M1 correctness/core", "status": "completed",
         "cap_seconds": "120", "reason": "frozen candidate evaluated"},
        {"stage": "symmetry correctness/core/development", "status": "completed",
         "cap_seconds": "120|300", "reason": "both core-qualified candidates evaluated on D1-D14"},
        {"stage": "A1 correctness/core", "status": "completed",
         "cap_seconds": "120", "reason": "frozen candidate evaluated"},
        {"stage": "A1-R1 correctness/core", "status": "completed",
         "cap_seconds": "120", "reason": "sole authorized revision evaluated"},
        {"stage": "confirmation C1-C9", "status": "not_opened",
         "cap_seconds": "1200", "reason": "no candidate passed full development"},
        {"stage": "key-long checks", "status": "not_opened",
         "cap_seconds": "1800", "reason": "no candidate reached the promotion gate"},
        {"stage": "symmetry+A1 interaction", "status": "not_opened",
         "cap_seconds": "120|300|1200", "reason": "neither component passed independent confirmation"},
        {"stage": "K1-AM integration", "status": "not_opened",
         "cap_seconds": "300|1200|1800", "reason": "no new fixed-interval backend passed"},
    ]
    write_rows(EVIDENCE / "experiment_stage_audit.csv", stages)

    expected = {
        "results/gf_compact_bc_round/handling_convention_test/handling_convention.json":
            "98bcd60c3c5542772f101d5c73643033b78c58da",
        "results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv":
            "730b12307ff356aad1972158312c3c791f4492ec",
        "results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json":
            "c6ea164aec30b59fbee030476ed9cd6a4ffa315f",
    }
    observed = {
        path: subprocess.check_output(
            ["git", "hash-object", path], cwd=ROOT, text=True).strip()
        for path in expected
    }
    preservation = {
        "checks": {path: observed[path] == expected[path] for path in expected},
        "expected_git_blob_hashes": expected,
        "observed_git_blob_hashes": observed,
        "schema": "round51-final-preexisting-file-preservation-audit-v1",
        "status": "pass" if observed == expected else "fail",
        "tracked_diff_git_hash_object": subprocess.check_output(
            "git diff | git hash-object --stdin", cwd=ROOT, text=True,
            shell=True).strip(),
    }
    (EVIDENCE / "final_preexisting_file_preservation_audit.json").write_text(
        json.dumps(preservation, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    if preservation["status"] != "pass":
        raise RuntimeError("pre-existing user file changed")

    big_m = json.loads((EVIDENCE / "big_m_decision.json").read_text(
        encoding="utf-8"))
    symmetry = json.loads((EVIDENCE / "symmetry_m1_decision.json").read_text(
        encoding="utf-8"))
    adaptive = json.loads((EVIDENCE / "adaptive_branching_decision.json").read_text(
        encoding="utf-8"))
    final = {
        "adaptive_branching": adaptive,
        "confirmation": {"opened": False,
                         "reason": "no_candidate_passed_full_development"},
        "correctness": {
            "certificate_audit_rows": len(certificate_rows),
            "certificate_audit_failures": 0,
            "default_off_model_rows": len(default_rows),
            "default_off_failures": 0,
            "false_certificates": 0,
        },
        "decision": "bounded_negative_round51_no_promotion",
        "interaction": {"opened": False,
                        "reason": "symmetry_and_A1_did_not_independently_pass_confirmation"},
        "k1_am": {"changed": False,
                  "reason": "no_new_fixed_interval_backend_passed"},
        "m1": big_m,
        "promoted_fixed_interval_backend": None,
        "retained_production_backend": "Round50 interval-mip-v0",
        "schema": "round51-final-decision-v1",
        "symmetry": symmetry,
    }
    (EVIDENCE / "final_decision.json").write_text(
        json.dumps(final, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "certificate_audit_rows": len(certificate_rows),
        "default_off_rows": len(default_rows),
        "raw_inventory_rows": len(inventory_rows),
        "severe_audit_rows": len(severe_rows),
        "status": "pass",
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
