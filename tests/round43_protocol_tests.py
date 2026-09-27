#!/usr/bin/env python3
"""Round 43 frozen-contract and forbidden-dispatch tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_k4_envelope_refinement_round43"
sys.path.insert(0, str(ROOT / "scripts"))
import round43_common as common  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class Round43ProtocolTests(unittest.TestCase):
    def test_frozen_split_is_complete_and_disjoint(self) -> None:
        self.assertEqual(len(common.DEVELOPMENT_IDS), 10)
        self.assertEqual(len(common.VALIDATION_IDS), 7)
        self.assertEqual(len(common.HOLDOUT_IDS), 7)
        groups = [set(common.DEVELOPMENT_IDS), set(common.VALIDATION_IDS),
                  set(common.HOLDOUT_IDS)]
        self.assertEqual(len(set().union(*groups)), 24)
        self.assertFalse(groups[0] & groups[1])
        self.assertFalse(groups[0] & groups[2])
        self.assertFalse(groups[1] & groups[2])

    def test_stage0_freeze_hashes_are_immutable(self) -> None:
        manifest = json.loads((OUT / "stage0_freeze_manifest.json").read_text(
            encoding="utf-8"))
        self.assertEqual(manifest["round_id"], 43)
        self.assertEqual(len(manifest["file_sha256"]), 10)
        for name, frozen_hash in manifest["file_sha256"].items():
            path = OUT / name
            self.assertTrue(path.is_file(), path)
            self.assertEqual(sha256(path), frozen_hash, path)

    def test_round43_family_is_default_off(self) -> None:
        source = (ROOT / "include" / "Instance.hpp").read_text(
            encoding="utf-8")
        self.assertIn('round43_envelope_refinement = "off"', source)
        self.assertIn("round43_initial_k0 = 4", source)
        self.assertIn("round43_lookahead_depth = 1", source)
        self.assertIn("round43_rho = 0.01", source)

    def test_writer_emits_the_certified_objective_envelope_row(self) -> None:
        source = (ROOT / "src" / "CplexBaseline.cpp").read_text(
            encoding="utf-8")
        self.assertIn("1.0 - facet.beta", source)
        self.assertIn("facet.alpha", source)
        self.assertIn("objective_gini_envelope_facets", source)
        self.assertIn("validEnvelopeFacetScope", source)

    def test_shared_runtime_has_no_instance_or_history_dispatch(self) -> None:
        paths = [
            ROOT / "src" / "PaperExternalGiniTree.cpp",
            ROOT / "src" / "GiniEnvelopeRefinement.cpp",
            ROOT / "include" / "GiniEnvelopeRefinement.hpp",
        ]
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        for forbidden in (
                "seed1343324363", "seed1288546114",
                "major_fragmentation_regression", "historical_winner",
                "difficulty_stratum", "elapsed_time_switch"):
            self.assertNotIn(forbidden, text)

    def test_k0_only_selects_the_initial_equal_partition(self) -> None:
        source = (ROOT / "src" / "PaperExternalGiniTree.cpp").read_text(
            encoding="utf-8")
        occurrences = source.count("options.round43_initial_k0")
        self.assertGreaterEqual(occurrences, 4)
        self.assertIn(
            "makeEnvelopeInitialPartition(\n"
            "              {root_gamma_L, root_gamma_U}, "
            "options.round43_initial_k0)", source)
        self.assertNotIn("round43_initial_k0 ==", source)

    def test_iterated_mode_requires_violation_and_unique_facet(self) -> None:
        source = (ROOT / "src" / "PaperExternalGiniTree.cpp").read_text(
            encoding="utf-8")
        self.assertIn("violation > violation_tolerance", source)
        self.assertIn("violated_new_facets.empty()", source)
        self.assertIn("while (!fixed_point_reached", source)
        self.assertNotIn("iteration <= 64", source)
        self.assertNotIn("fixed_point_iteration_limit", source)

    def test_pgrb_reference_uses_the_frozen_hga_start(self) -> None:
        item = common.inventory()[common.DEVELOPMENT_IDS[0]]
        command = common.fair_pgrb_command(
            item, common.RUNS / "protocol_command_sentinel", 3600.0)
        index = command.index("--gurobi-hga-start")
        self.assertEqual(command[index + 1], "true")


if __name__ == "__main__":
    unittest.main()
