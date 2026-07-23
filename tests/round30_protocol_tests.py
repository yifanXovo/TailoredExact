#!/usr/bin/env python3
"""Static and command-construction gates for the Round 30 protocol."""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import run_round30_experiments as runner  # noqa: E402


def option(command: list[str], name: str) -> str:
    return command[command.index(name) + 1]


class Round30ProtocolTests(unittest.TestCase):
    def test_matrix_materializes_required_rows_without_rerunning_overlap(
            self) -> None:
        stage1 = runner.stage_matrix("stage1")
        stage2 = runner.stage_matrix("stage2")
        stage3 = runner.stage_matrix("stage3")
        stage4 = runner.stage_matrix("stage4")
        self.assertEqual(len(stage1), 21)
        self.assertEqual(len(stage2), 37)
        self.assertEqual(len(stage3), 10)
        self.assertEqual(len(stage4), 10)
        primary = {
            (instance, arm)
            for instance, arm, _ in stage1 + stage2
            if arm in {"P-GRB", "C4-CANDIDATE", "C5-CANDIDATE"}
        }
        self.assertEqual(len(primary), 51)
        anchors = {
            (instance, arm)
            for instance, arm, _ in stage1 + stage3
            if instance in runner.ANCHORS
            and arm in {"S0-CPLEX", "C0-DIAG", "C3-REPLICA",
                        "C4-CANDIDATE", "C5-CANDIDATE"}
        }
        self.assertEqual(len(anchors), 25)

    def test_c5_command_is_uniform_and_contains_no_license(self) -> None:
        normalized = []
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for instance in runner.PRIMARY:
                command = runner.command_for(
                    instance, "C5-CANDIDATE", 300, root / instance)
                self.assertEqual(
                    option(command, "--external-gini-scheduling"),
                    "round30-dual-bound-target")
                self.assertEqual(
                    option(command, "--external-gini-lifecycle"),
                    "round30-same-leaf-bound-target")
                self.assertEqual(
                    option(command, "--exact-phase-local-redecode-repair"),
                    "false")
                self.assertEqual(option(command, "--threads"), "1")
                self.assertEqual(
                    option(command, "--process-wall-time-limit"), "300")
                self.assertNotIn(str(runner.LICENSE), command)
                variable_values = {
                    command.index("--input") + 1,
                    command.index("--external-gini-artifact-dir") + 1,
                    command.index("--primal-heuristic-generation-log") + 1,
                    command.index("--progress-log") + 1,
                    command.index("--process-phase-ledger") + 1,
                    command.index("--log") + 1,
                    command.index("--out") + 1,
                }
                normalized.append(tuple(
                    value for index, value in enumerate(command)
                    if index not in variable_values))
        self.assertTrue(all(row == normalized[0] for row in normalized))

    def test_c5_is_distinct_from_c0_c3_and_c4(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            selectors = {
                arm: option(
                    runner.command_for("V12_M1", arm, 300, root / arm),
                    "--external-gini-scheduling")
                for arm in (
                    "C0-DIAG", "C3-REPLICA",
                    "C4-CANDIDATE", "C5-CANDIDATE")
            }
        self.assertEqual(len(set(selectors.values())), 4)

    def test_bound_target_callback_uses_certified_mip_dual_bound(self) -> None:
        source = (ROOT / "src/GurobiBaseline.cpp").read_text(encoding="utf-8")
        callback = source[
            source.index("int __stdcall progressAndBoundTargetCallback"):
            source.index("std::string versionString")]
        self.assertIn("GRB_CB_MIP_OBJBND", callback)
        self.assertIn("finiteNative", callback)
        self.assertIn("bound_target", callback)
        self.assertIn("terminate(model)", callback)
        self.assertNotIn("GRB_CB_MIP_OBJBST", callback[
            callback.index("if (state->bound_target_enabled"):])

    def test_c5_decision_has_no_hardware_or_metadata_dispatch(self) -> None:
        source = (
            ROOT / "src/PaperExternalGiniTree.cpp"
        ).read_text(encoding="utf-8")
        decision = source[
            source.index("C5BoundTargetSplitDecision "
                         "evaluateC5BoundTargetSplitDecision"):
            source.index("PaperTerminalMipDecision "
                         "evaluatePaperTerminalMipDecision")]
        for token in (
                "time", "work", "node", "solution", "attempt", "retry",
                "instance", "family", "seed", "path", "known_optimum"):
            self.assertIsNone(
                re.search(rf"\b{re.escape(token)}\b", decision, re.I), token)
        self.assertIn("normalized_split_threshold", decision)
        self.assertIn("parent_native_bound_target = post", decision)

    def test_license_is_only_assigned_to_child_environment(self) -> None:
        for filename in (
                "run_round30_development.py",
                "run_round30_experiments.py"):
            text = (SCRIPTS / filename).read_text(encoding="utf-8")
            self.assertNotRegex(
                text, r"LICENSE\.(read_|open|stat|is_file|exists|resolve)")
            self.assertNotRegex(text, r"sha256\s*\(\s*LICENSE")
            self.assertIn('environment["GRB_LICENSE_FILE"]', text)

    def test_stable_mainline_and_c0_roles_are_frozen(self) -> None:
        protocol = (
            ROOT /
            "results/gf_c0_mechanism_transfer_c5_round30/round30_protocol.md"
        ).read_text(encoding="utf-8")
        self.assertIn("S0/F0-CPLEX remains the stable accepted paper mainline",
                      protocol)
        self.assertIn("C0-DIAG is never promotion-eligible", protocol)


if __name__ == "__main__":
    unittest.main()
