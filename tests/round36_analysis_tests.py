#!/usr/bin/env python3
"""Integrity checks for derived Round 36 causal-analysis outputs."""

from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_incumbent_decomposition_causal_round36"
PREFIX = "" if (OUT / "per_arm_results.csv").is_file() else "interim_"


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / f"{PREFIX}{name}").open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def yes(value: object) -> bool:
    return str(value).strip().lower() == "true"


class Round36AnalysisTests(unittest.TestCase):
    def test_complete_panels_have_four_arms(self) -> None:
        per_arm = rows("per_arm_results.csv")
        grouped: dict[str, set[str]] = {}
        for row in per_arm:
            grouped.setdefault(row["panel_row_id"], set()).add(row["arm"])
        self.assertTrue(grouped)
        self.assertTrue(all(arms == {"HH", "SS", "BW-P", "BW-A"}
                            for arms in grouped.values()))

    def test_exactness_audits_are_green(self) -> None:
        audits = rows("exactness_certificate_audit.csv")
        self.assertTrue(audits)
        self.assertTrue(all(yes(row["exactness_certificate_audit_passed"])
                            for row in audits))
        self.assertFalse(any(yes(row["false_certificate"])
                             for row in audits))

    def test_geometry_and_normalization_controls(self) -> None:
        geometry = rows("causal_geometry_comparison.csv")
        normalization = rows("causal_normalization_comparison.csv")
        self.assertEqual(len(geometry), len(normalization))
        self.assertTrue(all(yes(row["same_proof_incumbent"])
                            for row in geometry if yes(row["geometry_exposure"])))
        self.assertTrue(all(yes(row["same_proof_incumbent"])
                            and yes(row["same_anchor"])
                            for row in normalization))

    def test_auc_handling_convention(self) -> None:
        comparisons = (rows("causal_geometry_comparison.csv")
                       + rows("causal_normalization_comparison.csv"))
        observed = [row for row in comparisons
                    if row.get("auc_status") == "observed_common_window"]
        self.assertTrue(observed)
        self.assertTrue(all(row["auc_convention"] ==
            "left_continuous_no_interpolation_no_post_last_extension"
            for row in observed))

    def test_machine_decision_matches_completion_state(self) -> None:
        decision = json.loads((OUT / f"{PREFIX}final_audit_decision.json").read_text(
            encoding="utf-8"))
        self.assertFalse(decision["automatic_promotion_performed"])
        self.assertEqual(decision["validated_gurobi_mainline"], "C6-HGA-FULL")
        self.assertEqual(decision["false_certificate_count"], 0)
        if PREFIX:
            self.assertEqual(decision["classification"], "incomplete_stage_b")
        else:
            self.assertEqual(decision["completed_official_rows"], 56)


if __name__ == "__main__":
    unittest.main()
