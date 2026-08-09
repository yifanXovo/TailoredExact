#!/usr/bin/env python3
"""Protocol gates for the frozen Round 35 SIMPLE-START qualification."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import round35_common as common  # noqa: E402


class Round35ProtocolTests(unittest.TestCase):
    def test_frozen_matrix_cardinality_and_only_new_arm(self) -> None:
        rows = common.csv_rows(common.OFFICIAL_MATRIX)
        self.assertEqual(52, len(rows))
        self.assertEqual({common.ARM}, {row["arm"] for row in rows})
        self.assertEqual(35, sum(row["stage"] == "matrix1800" for row in rows))
        self.assertEqual(12, sum(row["stage"] == "v50_3600" for row in rows))
        self.assertEqual(5, sum(row["stage"] == "repeat" for row in rows))
        self.assertFalse(any(row["instance_id"].startswith("round33_v10")
                             for row in rows))

    def test_instance_and_repeat_freezes(self) -> None:
        items = common.inventory()
        self.assertEqual(35, len(items))
        self.assertEqual(12, sum(item["V"] == 50 for item in items.values()))
        repeats = common.csv_rows(common.REPEAT_FREEZE)
        self.assertEqual([2, 3, 4], sorted(
            int(row["M"]) for row in repeats if int(row["V"]) == 50))
        self.assertEqual(2, sum(int(row["V"]) == 20 for row in repeats))
        self.assertEqual(
            {1800}, {int(row["process_cap_seconds"])
                     for row in repeats if int(row["V"]) == 20})
        self.assertEqual(
            {3600}, {int(row["process_cap_seconds"])
                     for row in repeats if int(row["V"]) == 50})

    def test_historical_compatibility_is_explicit(self) -> None:
        rows = common.csv_rows(
            common.OUT / "historical_comparator_compatibility.csv")
        self.assertEqual(94, len(rows))
        self.assertEqual({"compatible"}, {
            row["comparison_compatibility"] for row in rows})
        self.assertEqual({"32"}, {row["historical_source_round"] for row in rows})
        self.assertEqual({"True"}, {row["historical_data_read_only"] for row in rows})

    def test_frozen_exact_decisions_are_identical(self) -> None:
        rows = common.csv_rows(common.OUT / "frozen_c6_equivalence.csv")
        self.assertEqual(10, len(rows))
        self.assertTrue(all(row["identical"] == "True" for row in rows))

    def test_preservation_manifest_covers_starting_worktree(self) -> None:
        rows = common.csv_rows(common.OUT / "preexisting_worktree_manifest.csv")
        self.assertEqual(592, len(rows))
        self.assertTrue(all(row["preserve_untouched"] == "True" for row in rows))

    def test_simple_command_contract_when_executable_exists(self) -> None:
        if not common.EXE.is_file():
            self.skipTest("clean Round 35 executable is built after protocol preparation")
        item = next(iter(common.inventory().values()))
        command = common.simple_command(item, common.OUT / "command_probe",
                                        process_cap=1800)
        values = [str(value) for value in command]
        def option(name: str) -> str:
            return values[values.index(name) + 1]
        self.assertEqual("greedy", option("--primal-heuristic"))
        self.assertEqual("simple-start", option("--round34-c6-startup-variant"))
        self.assertEqual("round31-nonblocking-native-bound",
                         option("--external-gini-scheduling"))
        self.assertEqual("round31-open-native-bounded",
                         option("--external-gini-lifecycle"))
        self.assertEqual("0", option("--gurobi-seed"))
        self.assertEqual("1", option("--threads"))
        self.assertEqual("1800", option("--process-wall-time-limit"))


if __name__ == "__main__":
    unittest.main()
