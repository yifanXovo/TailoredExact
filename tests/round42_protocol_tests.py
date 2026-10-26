#!/usr/bin/env python3
"""Protocol and forbidden-dispatch checks for Round 42."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_decomposition_architecture_optimization_round42"
sys.path.insert(0, str(ROOT / "scripts"))
import analyze_round42_development as development  # noqa: E402


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class Round42ProtocolTests(unittest.TestCase):
    def test_geometric_mean_preserves_infinite_work_regression(self) -> None:
        self.assertTrue(math.isinf(development.gmean([1.0, math.inf, 0.5])))
        self.assertTrue(math.isnan(development.gmean([1.0, math.nan])))

    def test_same_k_references_are_not_promotion_candidates(self) -> None:
        self.assertEqual(
            development.REFERENCE_ARMS,
            {"C6-K1-SINGLE", "EXTERNAL-K2-FIXED", "ST-K2-P-CORE"},
        )

    def test_frozen_split_is_complete_and_disjoint(self) -> None:
        groups = {
            "development": rows("development_manifest.csv"),
            "validation": rows("validation_manifest.csv"),
            "holdout": rows("final_holdout_manifest.csv"),
        }
        self.assertEqual([len(groups[key]) for key in groups], [10, 7, 7])
        identities = [{row["instance_id"] for row in group}
                      for group in groups.values()]
        self.assertEqual(len(set().union(*identities)), 24)
        self.assertFalse(identities[0] & identities[1])
        self.assertFalse(identities[0] & identities[2])
        self.assertFalse(identities[1] & identities[2])
        for group in groups.values():
            self.assertTrue(all(len(row["instance_sha256"]) == 64
                                for row in group))

    def test_split_was_frozen_before_candidates(self) -> None:
        freeze = json.loads((OUT / "experiment_split_freeze.json").read_text(
            encoding="utf-8"))
        self.assertTrue(freeze[
            "frozen_before_any_round42_candidate_run"])
        self.assertFalse(freeze["candidate_outcomes_used"])
        self.assertEqual(freeze["development_count"], 10)
        self.assertEqual(freeze["validation_count"], 7)
        self.assertEqual(freeze["final_holdout_count"], 7)

    def test_round42_controls_are_default_off(self) -> None:
        source = (ROOT / "include" / "Instance.hpp").read_text(
            encoding="utf-8")
        self.assertIn('round42_static_architecture = "off"', source)
        self.assertIn(
            'round42_terminal_sibling_coalescing = "off"', source)

    def test_no_forbidden_instance_dispatch(self) -> None:
        paths = [
            ROOT / "src" / "PaperExternalGiniTree.cpp",
            ROOT / "src" / "StaticSegmentedGini.cpp",
            ROOT / "src" / "ControllingLeafScheduler.cpp",
            ROOT / "scripts" / "run_round42_c6.py",
            ROOT / "scripts" / "run_round42_static.py",
        ]
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        forbidden_ids = [
            "seed1343324363", "seed1288546114", "major_fragmentation",
            "strongest_k4_positive", "difficulty_stratum",
        ]
        for token in forbidden_ids:
            self.assertNotIn(token, text)
        self.assertNotIn("elapsed_time_switch", text)
        self.assertNotIn("historical_winner", text)

    def test_frozen_executable_hash_matches(self) -> None:
        freeze = json.loads((OUT / "implementation_freeze.json").read_text(
            encoding="utf-8"))
        executable = Path(os.environ.get(
            "EXACTEBRP_ROUND42_EXE", ROOT / freeze["executable"]))
        self.assertTrue(executable.is_file())
        self.assertEqual(sha256(executable), freeze["executable_sha256"])


if __name__ == "__main__":
    unittest.main()
