#!/usr/bin/env python3
"""Static Round 34 guards for startup-only C6 ablation plumbing."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class Round34ProtocolTests(unittest.TestCase):
    def test_default_is_frozen_full(self) -> None:
        source = text("include/Instance.hpp")
        self.assertIn(
            'round34_c6_startup_variant = "hga-full"', source)

    def test_full_light_and_simple_are_uniformly_gated(self) -> None:
        source = text("src/PaperExternalGiniTree.cpp")
        self.assertRegex(source, r'hga_full[\s\S]+no_improve_generations == 2000')
        self.assertRegex(source, r'hga_light[\s\S]+no_improve_generations == 1000')
        self.assertRegex(source, r'simple_start[\s\S]+primal_heuristic == "greedy"')
        self.assertIn("options.exact_phase_local_redecode_repair", source)

    def test_hga_elapsed_logging_is_observational(self) -> None:
        hga = text("include/hga_tgbc/HybridGA.h")
        runner = text("src/HgaTgbcRunner.cpp")
        self.assertIn("get_elapsed_history", hga)
        self.assertIn("generation,elapsed_seconds,best_fitness", runner)
        self.assertNotRegex(
            hga,
            r'elapsed_history[^;]*\b(?:select|mutate|crossover|fitness)\b')

    def test_round34_flag_is_not_used_by_exact_decision_functions(self) -> None:
        source = text("src/PaperExternalGiniTree.cpp")
        for name in (
            "evaluateC6FrontierDecision",
            "evaluateC6CurrentSplitDecision",
            "evaluatePaperTerminalMipDecision",
        ):
            match = re.search(
                rf"{name}\([^{{]+\{{(.*?\n\}})", source, re.S)
            self.assertIsNotNone(match, name)
            self.assertNotIn("round34_c6_startup_variant", match.group(1))

    def test_common_commands_preserve_exact_settings(self) -> None:
        source = text("scripts/round34_common.py")
        for token in (
            '"--frontier-intervals", 4',
            '"--frontier-adaptive-max-depth", 8',
            '"--frontier-adaptive-min-width", 0.0001',
            '"round31-nonblocking-native-bound"',
            '"round31-open-native-bounded"',
        ):
            if token.startswith('"--frontier'):
                # These inherited options live in the authoritative Round 28
                # pack called by round31.tailored_options.
                self.assertIn(token, text("scripts/run_round28_experiments.py"))
            else:
                self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main()
