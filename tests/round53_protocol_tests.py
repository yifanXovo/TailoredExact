#!/usr/bin/env python3
"""Final compact-evidence protocol checks for Round 53."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"
REQUIRED = (
    "final_report.md", "final_decision.json", "source_of_truth.md",
    "research_contract.md", "f0_exactness_and_validity.md",
    "f0_model_delta_audit.csv", "f0_v_gt_12_equivalence_audit.csv",
    "f0_small_exact_validation.csv", "exhaustive_row_activity_ledger.csv",
    "exhaustive_row_dual_summary.csv", "f0_plain_lp_comparison.csv",
    "f0_formulation_size_audit.csv", "f0_node_lp_cost_analysis.md",
    "f0_development_300s.csv", "f0_confirmation_1200s.csv",
    "f0_key_long_3600s.csv", "f0_fixed_interval_promotion_decision.json",
    "callback_isolation_300s.csv", "callback_isolation_1200s.csv",
    "callback_isolation_pairwise_effects.csv", "callback_path_diagnosis.md",
    "callback_path_decision.json", "bounded_rescue_selection.json",
    "bounded_rescue_development.csv", "bounded_rescue_confirmation.csv",
    "final_inner_backend_definition.json", "final_fixed_interval_ablation.csv",
    "k1_backend_integration_300s.csv", "k1_backend_integration_1800s.csv",
    "k1_backend_integration_3600s.csv", "k1_backend_integration_decision.json",
    "sealed_v12_instance_manifest.json", "sealed_v12_opening_audit.json",
    "sealed_v12_results.csv", "sealed_v12_direct_comparison.csv",
    "sealed_v12_severe_regression_audit.csv", "certificate_audit.csv",
    "default_off_equivalence.csv", "final_build_and_tests.md",
    "final_evidence_inventory.csv", "reproduction_commands.md")


def load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(name: str) -> list[dict[str, str]]:
    path = OUT / name
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def truth(value: object) -> bool:
    return value is True or str(value).lower() in {"1", "true"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha1(path: Path) -> str:
    # Git blob identity includes the canonical blob header.
    data = path.read_bytes()
    return hashlib.sha1(
        b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def check(condition: bool, label: str, passed: list[str]) -> None:
    if not condition:
        raise RuntimeError(label)
    passed.append(label)


def main() -> int:
    passed: list[str] = []
    try:
        check(all((OUT / name).is_file() for name in REQUIRED),
              "01_required_compact_files", passed)
        decision = load(OUT / "final_decision.json")
        check(decision["completion_status"] == "round53_complete",
              "02_completion", passed)
        check(not decision["missing_rows"], "03_no_missing_rows", passed)
        check(int(decision["false_certificates"]) == 0,
              "04_zero_false_certificates", passed)
        check(int(decision["correctness_failures"]) == 0,
              "05_zero_correctness_failures", passed)
        check(len(rows("f0_development_300s.csv")) == 28,
              "06_development_rows", passed)
        check(len(rows("f0_confirmation_1200s.csv")) == 18,
              "07_confirmation_rows", passed)
        check(len(rows("f0_key_long_3600s.csv")) == 12,
              "08_key_long_rows", passed)
        callback = rows("callback_isolation_300s.csv")
        check(len(callback) == 24, "09_callback_rows", passed)
        check({row["callback_isolation_mode"] for row in callback} ==
              {"C0", "C1", "C2", "C3", "C4", "C5"},
              "10_callback_modes", passed)
        check(all(int(row["cut_submission_calls"]) == 0 for row in callback
                  if row["callback_isolation_mode"] == "C4"),
              "11_c4_zero_submission", passed)
        check(all(int(row["mipnode_calls"]) == 0 for row in callback
                  if row["callback_isolation_mode"] in {"C0", "C1"}),
              "12_c0_c1_no_mipnode", passed)
        model = rows("f0_model_delta_audit.csv")
        check(model and all(truth(row["pass"]) for row in model),
              "13_model_delta", passed)
        check(all(truth(row["pass"]) for row in
                  rows("f0_v_gt_12_equivalence_audit.csv")),
              "14_v_gt_12_identity", passed)
        check(all(truth(row["pass"]) for row in
                  rows("f0_plain_lp_comparison.csv")),
              "15_plain_lp", passed)
        check(all(truth(row["big_m_valid_all"]) for row in
                  rows("exhaustive_row_dual_summary.csv")),
              "16_big_m_validity", passed)
        check(all(truth(row["pass"]) for row in
                  rows("f0_small_exact_validation.csv")),
              "17_small_exact", passed)
        check(len(rows("k1_backend_integration_300s.csv")) == 12,
              "18_k1_300", passed)
        check(len(rows("k1_backend_integration_1800s.csv")) == 12,
              "19_k1_1800", passed)
        integration = load(OUT / "k1_backend_integration_decision.json")
        check(truth(integration["gate_pass"]), "20_k1_gate", passed)
        check(truth(integration["major_repair_preserved"]),
              "21_major_repair", passed)
        opening = load(OUT / "sealed_v12_opening_audit.json")
        check(truth(opening["opening_authorized"]),
              "22_sealed_opening", passed)
        sealed = rows("sealed_v12_results.csv")
        check(len(sealed) == 36, "23_sealed_rows", passed)
        check({row["method"] for row in sealed} ==
              {"P-GRB", "K1-AM-v0", "K1-AM-CANDIDATE"},
              "24_sealed_methods", passed)
        check(len(rows("sealed_v12_checkpoint_results.csv")) == 144,
              "25_sealed_checkpoints", passed)
        manifest = load(OUT / "sealed_v12_instance_manifest.json")
        check(len(manifest["rows"]) == 12 and all(
            sha256(ROOT / row["input_path"]) == row["input_sha256"]
            for row in manifest["rows"]), "26_sealed_input_hashes", passed)
        check(all(truth(row["pass"]) for row in
                  rows("default_off_equivalence.csv")),
              "27_default_off", passed)
        certificates = rows("certificate_audit.csv")
        check(certificates and all(not truth(row["false_certificate"])
                                   for row in certificates),
              "28_certificate_invariance", passed)
        freeze = load(OUT / "final_inner_backend_freeze_manifest.json")
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", freeze["source_commit"], "HEAD",
             "--", "CMakeLists.txt", "include", "src", "tests", "scripts"],
            cwd=ROOT, text=True, encoding="utf-8", errors="replace").strip()
        check(not changed, "29_no_post_freeze_source_change", passed)
        start = load(OUT / "official_start_record.json")
        check(all(sha1(ROOT / item["path"]) == item["blob_sha1"]
                  for item in start["working_tree_start"]["tracked_modified"]),
              "30_user_files_preserved", passed)
        inventory = rows("final_evidence_inventory.csv")
        check(inventory and all(sha256(ROOT / row["path"]) == row["sha256"]
                                for row in inventory),
              "31_evidence_hashes", passed)
        print(f"Round53 protocol tests passed {len(passed)} checks")
        return 0
    except Exception as error:
        print(f"Round53 protocol tests failed after {len(passed)} checks: "
              f"{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
