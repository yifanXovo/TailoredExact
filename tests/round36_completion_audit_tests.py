#!/usr/bin/env python3
"""Integrity checks for the Round 36 requirement-level completion audit."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_incumbent_decomposition_causal_round36"
ROUND37 = ROOT / "results" / "gf_gini_geometry_mechanism_round37"


class Round36CompletionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # This is a historical completion audit.  Re-running its pre-merge
        # writer after later rounds would conflate live repository state with
        # the state attested when Round 36 completed.
        with (OUT / "completion_requirements_audit.csv").open(
                newline="", encoding="utf-8") as stream:
            cls.rows = list(csv.DictReader(stream))
        cls.summary = json.loads((
            OUT / "completion_requirements_audit.json").read_text(
                encoding="utf-8"))
        cls.current = json.loads((
            ROUND37 / "round36_reporting_consolidation.json").read_text(
                encoding="utf-8"))

    def test_all_requested_sections_are_represented(self) -> None:
        prefixes = {row["section"].split("_", 1)[0] for row in self.rows}
        self.assertEqual({str(value) for value in range(22)}, prefixes)

    def test_interim_audit_has_no_contradiction_or_missing_evidence(self) -> None:
        self.assertFalse(any(row["status"] in {"contradicted", "missing"}
                             for row in self.rows))

    def test_preexisting_work_and_default_c6_are_achieved(self) -> None:
        required = {
            "pre-existing user work is preserved",
            "clean licensed build and relevant tests pass",
            "default-off and explicit HH are decision-equivalent",
        }
        status = {row["requirement"]: row["status"] for row in self.rows}
        self.assertTrue(all(status.get(requirement) == "achieved"
                            for requirement in required))

    def test_reproducibility_prohibitions_are_explicitly_achieved(self) -> None:
        required = {
            "frozen commands and completed rows exclude warm/resume contamination",
            "split and native-action control is hardware-independent and unsliced",
        }
        status = {row["requirement"]: row["status"] for row in self.rows}
        self.assertTrue(all(status.get(requirement) == "achieved"
                            for requirement in required))

    def test_completion_state_matches_official_row_count(self) -> None:
        count = self.summary["completed_official_rows"]
        stage_b = next(row for row in self.rows if row["requirement"] ==
                       "all 56 official rows are checksum-complete")
        self.assertEqual("achieved" if count == 56 else "incomplete",
                         stage_b["status"])
        exactness = next(row for row in self.rows if row["requirement"] ==
                         "all official rows pass lifecycle, exactness, and certificate audits")
        self.assertEqual("achieved" if count == 56 else "incomplete",
                         exactness["status"])

    def test_historical_draft_and_current_merge_are_both_explicit(self) -> None:
        requirements = {
            "draft PR 83 is open and unmerged",
            "draft PR record attests the current head or its attestation parent",
        }
        rows = {row["requirement"]: row for row in self.rows}
        self.assertTrue(all(rows[item]["status"] == "achieved"
                            for item in requirements))
        pull = self.current["pull_request"]
        self.assertEqual(83, pull["number"])
        self.assertTrue(pull["merged"])
        self.assertFalse(pull["draft"])
        self.assertEqual("closed", pull["state"])


if __name__ == "__main__":
    unittest.main()
