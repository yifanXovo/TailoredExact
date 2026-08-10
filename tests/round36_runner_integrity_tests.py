#!/usr/bin/env python3
"""Read-only integrity tests for completed Round 36 official rows."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import analyze_round36 as analysis  # noqa: E402
import round36_common as common  # noqa: E402
import run_round36_experiments as runner  # noqa: E402


class Round36RunnerIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = common.load_json(common.FROZEN_MANIFEST)
        cls.items = common.inventory()
        cls.matrix = common.csv_rows(common.OFFICIAL_MATRIX)
        cls.complete = []
        for row in cls.matrix:
            directory = common.RUNS / row["run_id"]
            valid, _ = analysis.artifact_complete(
                directory, row, cls.items[row["instance_id"]], cls.manifest)
            if valid:
                cls.complete.append((row, directory,
                                     common.load_json(directory /
                                                      "completion_marker.json")))

    def test_at_least_one_checksum_complete_row_exists(self) -> None:
        self.assertTrue(self.complete)

    def test_completed_rows_have_safe_nonresumed_lifecycle(self) -> None:
        for row, _, marker in self.complete:
            with self.subTest(run_id=row["run_id"]):
                self.assertFalse(marker["algorithmic_solve_state_resumed"])
                self.assertFalse(marker["emergency_timeout"])
                self.assertEqual([], marker["missing_required_artifacts"])
                self.assertEqual(0, marker["return_code"])
                self.assertTrue(marker["arm_contract_matches"])
                self.assertTrue(marker["anchor_safety_valid"])
                self.assertTrue(marker["root_coverage_valid"])
                self.assertTrue(marker["parent_child_coverage_valid"])

    def test_actual_commands_match_frozen_commands(self) -> None:
        frozen = common.load_json(common.COMMAND_FREEZE)["commands"]
        for row, directory, _ in self.complete:
            actual = common.load_json(directory / "command.json")["command"]
            self.assertEqual(frozen[row["run_id"]]["command"], actual)

    def test_complete_directories_pass_license_sensitive_scan(self) -> None:
        for row, directory, _ in self.complete:
            with self.subTest(run_id=row["run_id"]):
                runner.scan_sensitive(directory)

    def test_runner_summary_contains_only_checksum_complete_rows(self) -> None:
        summary = common.csv_rows(common.SUMMARY)
        complete_ids = {row["run_id"] for row, _, _ in self.complete}
        self.assertTrue({row["run_id"] for row in summary}.issubset(complete_ids))
        # A completion marker is atomically written immediately before the
        # summary update, so tolerate only that one-row live race.
        self.assertGreaterEqual(len(summary), max(0, len(complete_ids) - 1))

    def test_invalidated_attempts_are_preserved_without_state_resume(self) -> None:
        records = list(common.INVALIDATED.glob("*/invalidation_record.json"))
        self.assertTrue(records)
        for path in records:
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(value["algorithmic_solve_state_resumed"])
            self.assertTrue(value["reason"])

    def test_frozen_runner_source_and_executable_still_match(self) -> None:
        for relative, expected in self.manifest["source_file_sha256"].items():
            self.assertEqual(expected, common.sha256(ROOT / relative))
        self.assertEqual(self.manifest["gurobi_executable_sha256"],
                         common.sha256(common.EXE))


if __name__ == "__main__":
    unittest.main()
