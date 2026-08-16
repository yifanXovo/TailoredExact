#!/usr/bin/env python3
"""Terminal protocol and compact-evidence tests for Round 43."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_k4_envelope_refinement_round43"
RUNS = OUT / "runs"
sys.path.insert(0, str(ROOT / "scripts"))
import round43_common as common  # noqa: E402


REQUIRED_REPORTS = {
    "final_report.md", "final_decision.json", "source_of_truth.md",
    "mathematical_mechanism_note.md", "exactness_and_validity_note.md",
    "k1_vs_k4_factor_analysis.md", "mechanism_atlas.md",
    "envelope_ablation.md", "refinement_score_ablation.md",
    "performance_profile.csv", "per_run_results.csv",
    "development_comparison.csv", "validation_comparison.csv",
    "holdout_comparison.csv", "certificate_audit.csv",
    "default_off_equivalence.csv", "forbidden_logic_audit.csv",
    "final_build_and_tests.md", "final_evidence_inventory.csv",
    "reproduction_commands.md",
}

REQUIRED_ROW_ARTIFACTS = {
    "process_phases.csv", "progress.csv", "result.json",
    "global_bound_trace.csv", "interval_tree_events.csv",
    "interval_coverage_ledger.csv", "parent_lp_ledger.csv",
    "lookahead_profile_ledger.csv", "envelope_facet_ledger.csv",
    "envelope_integral_ledger.csv", "refinement_decision_ledger.csv",
    "formulation_contraction_ledger.csv", "native_target_ledger.csv",
    "native_optimize_ledger.csv", "incumbent_verification_ledger.csv",
    "model_size_ledger.csv", "certificate_ledger.csv",
    "artifact_manifest.csv", "command.json", "completion_marker.json",
}


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repository_blob_sha256(path: Path) -> str:
    material = path.read_bytes()
    if path.suffix.lower() in {".csv", ".json", ".md", ".txt"}:
        material = material.replace(b"\r\n", b"\n")
    return hashlib.sha256(material).hexdigest()


def truth(value) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "yes"}


class Round43EvidenceTests(unittest.TestCase):
    def test_all_required_reports_exist(self) -> None:
        missing = sorted(name for name in REQUIRED_REPORTS
                         if not (OUT / name).is_file())
        self.assertEqual(missing, [])

    def test_terminal_classification_is_consistent(self) -> None:
        final = load(OUT / "final_decision.json")
        self.assertEqual(final["terminal_classification"],
                         "bounded_systematic_negative_result")
        self.assertFalse(final["promotion"])
        self.assertIsNone(final["selected_algorithm"])
        self.assertFalse(final["development_passed"])
        self.assertFalse(final["validation_opened"])
        self.assertFalse(final["holdout_opened"])
        self.assertTrue(final["holdout_remained_sealed"])
        self.assertEqual(final["false_certificates"], 0)

    def test_no_false_certificate(self) -> None:
        audit = rows(OUT / "certificate_audit.csv")
        self.assertGreaterEqual(len(audit), 70)
        self.assertFalse(any(truth(row["false_certificate"]) for row in audit))
        for row in audit:
            if truth(row["strict_certificate"]):
                self.assertTrue(truth(row["independent_verifier_passed"]), row)

    def test_default_off_equivalence(self) -> None:
        audit = rows(OUT / "default_off_equivalence.csv")
        self.assertEqual(len(audit), 3)
        self.assertTrue(all(truth(row["default_off_equivalence_passed"])
                            for row in audit))
        self.assertTrue(all(row["mismatch_count"] == "0" for row in audit))

    def test_forbidden_logic_audit(self) -> None:
        audit = rows(OUT / "forbidden_logic_audit.csv")
        self.assertGreaterEqual(len(audit), 19)
        self.assertTrue(all(not truth(row["observed"]) for row in audit))
        self.assertTrue(all(truth(row["audit_passed"]) for row in audit))

    def test_deterministic_decisions_reconstruct(self) -> None:
        audit = rows(OUT / "stage3_mechanism_results.csv")
        self.assertEqual(len(audit), 24)
        self.assertTrue(all(truth(row["decision_reconstruction_valid"])
                            for row in audit))

    def test_fallback_stages_formally_disposed(self) -> None:
        stage4 = load(OUT / "stage4_disposition.json")
        stage5 = load(OUT / "stage5_entry_audit.json")
        self.assertFalse(stage4["stage4_required"])
        self.assertFalse(stage4["stage4_entered"])
        self.assertTrue(stage4["audit_passed"])
        self.assertFalse(stage5["stage5_required"])
        self.assertFalse(stage5["stage5_entered"])
        self.assertTrue(stage5["audit_passed"])

    def test_validation_and_holdout_remain_sealed(self) -> None:
        validation = rows(OUT / "validation_comparison.csv")
        holdout = rows(OUT / "holdout_comparison.csv")
        self.assertEqual(validation[0]["status"], "not_run")
        self.assertEqual(holdout[0]["status"], "not_run")
        self.assertTrue(truth(validation[0]["holdout_remained_sealed"]))
        self.assertTrue(truth(holdout[0]["holdout_remained_sealed"]))
        names = {path.name for path in RUNS.iterdir() if path.is_dir()}
        for instance_id in common.VALIDATION_IDS + common.HOLDOUT_IDS:
            self.assertFalse(any(instance_id in name for name in names))

    def test_every_sealed_row_publishes_twenty_artifacts(self) -> None:
        runs = rows(OUT / "official_run_evidence_manifest.csv")
        artifacts = rows(OUT / "artifact_manifest.csv")
        self.assertGreaterEqual(len(runs), 70)
        by_run: dict[str, set[str]] = {}
        for row in artifacts:
            if truth(row["required_protocol_artifact"]):
                by_run.setdefault(row["run_id"], set()).add(row["artifact"])
        for row in runs:
            self.assertEqual(int(row["artifact_count"]), 20)
            self.assertEqual(by_run[row["run_id"]], REQUIRED_ROW_ARTIFACTS)
            self.assertGreaterEqual(int(row["published_file_count"]), 20)

    def test_local_raw_hashes_match_when_retained(self) -> None:
        for row in rows(OUT / "artifact_manifest.csv"):
            path = ROOT / row["path"]
            if path.is_file():
                self.assertEqual(path.stat().st_size, int(row["bytes"]), path)
                self.assertEqual(sha256(path), row["sha256"], path)

    def test_candidate_commands_obey_solver_contract(self) -> None:
        checked = 0
        for run_dir in RUNS.iterdir():
            if not run_dir.is_dir() or not run_dir.name.startswith("stage3-"):
                continue
            command_path = run_dir / "command.json"
            if not command_path.is_file():
                continue
            record = load(command_path)
            command = record.get("command", [])
            if not record.get("completed") or "--round43-envelope-refinement" not in command:
                continue
            def option(name: str) -> str:
                return str(command[command.index(name) + 1])
            self.assertEqual(option("--threads"), "1")
            self.assertEqual(option("--gurobi-seed"), "0")
            self.assertEqual(option("--gurobi-presolve"), "-1")
            self.assertEqual(option("--round43-width-measure"),
                             "g-mccormick-unit")
            checked += 1
        self.assertGreaterEqual(checked, 44)

    def test_final_inventory_hashes(self) -> None:
        inventory = rows(OUT / "final_evidence_inventory.csv")
        compact = [row for row in inventory
                   if row["category"] == "compact_committed_evidence"]
        self.assertGreaterEqual(len(compact), 40)
        for row in compact:
            path = ROOT / row["path"]
            self.assertTrue(path.is_file(), path)
            self.assertEqual(repository_blob_sha256(path), row["sha256"], path)


if __name__ == "__main__":
    unittest.main()
