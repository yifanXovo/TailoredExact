#!/usr/bin/env python3
"""Static and command-construction gates for the frozen Round 29 protocol."""

from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "round29_runner", SCRIPTS / "run_round29_experiments.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load_runner()


def option(command: list[str], name: str) -> str:
    return command[command.index(name) + 1]


class Round29ProtocolTests(unittest.TestCase):
    def test_official_matrix_is_exact_and_nonduplicating(self) -> None:
        stage1 = RUNNER.stage_matrix("stage1")
        stage2 = RUNNER.stage_matrix("stage2")
        stage4 = RUNNER.stage_matrix("stage4")
        self.assertEqual(len(stage1), 12)
        self.assertEqual(len(stage2), 39)
        self.assertEqual(len(stage4), 10)
        stage12 = {
            (instance, arm)
            for instance, arm, _ in stage1 + stage2
        }
        self.assertEqual(len(stage12), 51)
        self.assertEqual(
            {row[0] for row in stage2 if row[1] == "P-GRB"},
            set(RUNNER.PRIMARY))

    def test_c4_command_has_one_uniform_algorithm(self) -> None:
        commands = []
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            for instance in RUNNER.PRIMARY:
                commands.append(
                    RUNNER.external_command(
                        instance, "C4-CANDIDATE", 300,
                        base / instance))
        for command in commands:
            self.assertEqual(
                option(command, "--external-gini-scheduling"),
                "round29-bound-gain-incremental")
            self.assertEqual(
                option(command, "--external-gini-lifecycle"),
                "round29-same-leaf-in-memory-model")
            self.assertEqual(
                option(command, "--exact-phase-local-redecode-repair"),
                "false")
            self.assertEqual(
                option(command, "--process-shutdown-margin"), "5")
            self.assertEqual(option(command, "--threads"), "1")
            self.assertEqual(option(command, "--gurobi-seed"), "0")
            self.assertNotIn("E:\\gurobi\\gurobi.lic", command)
        stripped = [
            tuple(
                value for index, value in enumerate(command)
                if index not in {
                    command.index("--input") + 1,
                    command.index("--external-gini-artifact-dir") + 1,
                    command.index("--primal-heuristic-generation-log") + 1,
                    command.index("--progress-log") + 1,
                    command.index("--process-phase-ledger") + 1,
                    command.index("--log") + 1,
                    command.index("--out") + 1,
                })
            for command in commands
        ]
        self.assertTrue(all(value == stripped[0] for value in stripped))

    def test_c3_is_not_aliased_to_c4(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            c3 = RUNNER.external_command(
                "V12_M1", "C3-REPLICA", 300, base / "c3")
            c4 = RUNNER.external_command(
                "V12_M1", "C4-CANDIDATE", 300, base / "c4")
        self.assertEqual(
            option(c3, "--external-gini-scheduling"),
            "cplex-algorithm-replica")
        self.assertEqual(
            option(c4, "--external-gini-scheduling"),
            "round29-bound-gain-incremental")
        self.assertEqual(
            option(c3, "--exact-phase-local-redecode-repair"), "true")
        self.assertEqual(
            option(c4, "--exact-phase-local-redecode-repair"), "false")

    def test_c4_lifecycle_survives_cli_normalization(self) -> None:
        main = (ROOT / "src/main.cpp").read_text(encoding="utf-8")
        normalization = main[
            main.index("opt.external_gini_lifecycle = lowerAscii"):
            main.index(
                "opt.primal_heuristic = lowerAscii",
                main.index("opt.external_gini_lifecycle = lowerAscii"))
        ]
        self.assertIn(
            '"round29-same-leaf-in-memory-model"', normalization)

    def test_plain_gurobi_recomputes_absolute_deadline_at_optimize(self) -> None:
        source = (
            ROOT / "src/GurobiBaseline.cpp"
        ).read_text(encoding="utf-8")
        launch = source[
            source.index("const double optimize_remaining"):
            source.index(
                "result.gurobi_optimize_return_code",
                source.index("const double optimize_remaining"))
        ]
        self.assertIn("processWorkRemainingSeconds(options)", launch)
        self.assertIn("GRB_DBL_PAR_TIMELIMIT", launch)

    def test_license_is_only_assigned_to_child_environment(self) -> None:
        for filename in (
            "run_round29_experiments.py",
            "run_round29_development.py",
            "run_round29_stage0.py",
        ):
            text = (SCRIPTS / filename).read_text(encoding="utf-8")
            self.assertNotRegex(
                text,
                r"LICENSE\.(read_|open|stat|is_file|exists|resolve)")
            self.assertNotRegex(text, r"sha256\s*\(\s*LICENSE")
            self.assertIn('environment["GRB_LICENSE_FILE"]', text)

    def test_all_required_phase_events_are_implemented(self) -> None:
        source = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in (
                "src/main.cpp",
                "src/HgaTgbcRunner.cpp",
                "src/ReplicaExternalGiniTree.cpp",
                "src/PaperExternalGiniTree.cpp",
                "src/GurobiBaseline.cpp",
            ))
        required = (
            "process_entry",
            "instance_parsing_complete",
            "initial_model_data_preprocessing_complete",
            "hga_start",
            "hga_generation_loop_complete",
            "hga_best_solution_extraction_complete",
            "hga_route_decoding_complete",
            "independent_hga_verification_start",
            "independent_hga_verification_complete",
            "improving_gini_range_construction_complete",
            "static_row_factory_preparation_complete",
            "connectivity_flow_preparation_complete",
            "root_canonical_model_construction_start",
            "root_canonical_model_construction_complete",
            "gurobi_environment_creation",
            "external_backend_creation",
            "external_artifact_directory_creation",
            "first_tree_ledger_opened",
            "first_external_tree_event",
            "first_interval_model_build",
            "first_lp_optimize_launch",
            "final_result_serialization_start",
            "final_result_serialization_complete",
            "process_exit",
        )
        for phase in required:
            self.assertIn(f'"{phase}"', source, phase)

    def test_c4_source_has_no_metadata_dispatch(self) -> None:
        source = (
            ROOT / "src/PaperExternalGiniTree.cpp"
        ).read_text(encoding="utf-8")
        body = source[source.index("round29C4FrozenOptionsValid"):]
        forbidden = (
            r"if\s*\([^\)]*instance\.(?:name|path|V|M)",
            r"switch\s*\([^\)]*instance\.(?:name|path|V|M)",
            r"if\s*\([^\)]*(?:gurobi_work|node_count|known_opt)",
        )
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, body), pattern)

    def test_protocol_declares_stable_mainline(self) -> None:
        protocol = (
            ROOT /
            "results/gf_gurobi_performance_recovery_round29/round29_protocol.md"
        ).read_text(encoding="utf-8")
        self.assertIn("corrected CPLEX S0/F0", protocol)
        self.assertIn("does not replace", protocol)


if __name__ == "__main__":
    unittest.main()
