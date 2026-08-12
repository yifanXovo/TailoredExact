#!/usr/bin/env python3
"""Integrity checks for the Round 36 semantic separation audit."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_incumbent_decomposition_causal_round36"
PYTHON = Path(r"D:\msys64\ucrt64\bin\python.exe")


class Round36SemanticAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run((str(PYTHON), "-B",
                        "scripts/audit_round36_semantics.py"),
                       cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        cls.summary = json.loads((OUT / "semantic_separation_audit.json").read_text(
            encoding="utf-8"))
        with (OUT / "semantic_separation_audit.csv").open(
                newline="", encoding="utf-8") as stream:
            cls.rows = list(csv.DictReader(stream))

    def test_all_semantic_invariants_pass(self) -> None:
        self.assertTrue(self.summary["passed"])
        self.assertEqual(19, self.summary["semantic_invariants"])
        self.assertEqual(19, self.summary["semantic_invariants_passed"])
        self.assertTrue(all(row["passed"] == "True" for row in self.rows))

    def test_split_and_action_controls_are_hardware_independent(self) -> None:
        rows = {row["id"]: row for row in self.rows}
        self.assertEqual("True", rows[
            "S18_hardware_independent_split_inputs"]["passed"])
        self.assertEqual("True", rows["S19_global_deadline_only"]["passed"])
        self.assertEqual([], self.summary["hardware_dependent_split_tokens"])
        self.assertEqual([], self.summary["native_action_time_slice_tokens"])

    def test_proof_ub_updates_are_verifier_guarded(self) -> None:
        self.assertEqual(4, self.summary["verified_ub_assignments"])
        self.assertEqual(4, self.summary["verified_ub_assignments_guarded"])

    def test_anchor_has_no_forbidden_proof_consumer(self) -> None:
        self.assertEqual(9, self.summary["anchor_symbol_occurrences"])
        self.assertEqual(0, self.summary[
            "anchor_forbidden_consumer_occurrences"])

    def test_audited_sources_match_frozen_or_contract_fix_identity(self) -> None:
        manifest = json.loads((OUT / "round36_frozen_manifest.json").read_text(
            encoding="utf-8"))
        contract_audit = json.loads((OUT / "stage_c_contract_fix_audit.json").read_text(
            encoding="utf-8"))
        for relative, audited in self.summary["source_sha256"].items():
            path = ROOT / relative
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(audited, actual)
            if relative in contract_audit["source_sha256"]:
                self.assertEqual(
                    contract_audit["source_sha256"][relative], actual)
                self.assertNotEqual(
                    manifest["source_file_sha256"][relative], actual)
            else:
                self.assertEqual(
                    manifest["source_file_sha256"][relative], actual)


if __name__ == "__main__":
    unittest.main()
