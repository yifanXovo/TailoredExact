"""Pure logic tests for the separate composite endpoint adapter.

These tests do not start the native importer, supervisor, or a solver.
"""

from __future__ import annotations

from fractions import Fraction as F
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import round88_quantity_flow as flow
import round88_quantity_probe as old_probe
import round88_quantity_composite as composite
import round88_quantity_composite_probe as adapter


def fixture() -> tuple[old_probe.Parsed, tuple[int, ...],
                       old_probe.CppEvidence]:
    matrix = tuple(tuple(F(0) for _ in range(3)) for _ in range(3))
    problem = flow.Problem(
        (flow.Station(4, 4, 1, F(1)),
         flow.Station(0, 3, 3, F(1))),
        (flow.Vehicle((0, 1), 3, F(6), matrix),),
        F(1), F(1), F(1))
    current = (3, 1)
    parsed = old_probe.Parsed(problem, 0, Path("C:/probe/tiny.txt"))
    initial = old_probe.CppEvidence(flow.objective(problem, current),
                                    F(0), F(0), (F(0),), (F(2),))
    return parsed, current, initial


def fake_cpp_evidence(problem: flow.Problem,
                      inventory: tuple[int, ...]
                      ) -> old_probe.CppEvidence:
    return old_probe.CppEvidence(flow.objective(problem, inventory),
                                 F(0), F(0), (F(0),), (F(2),))


class CompositeAdapterTests(unittest.TestCase):
    def test_fixed_case_and_immutable_source_identity_contract(self) -> None:
        self.assertEqual(tuple(old_probe.CASES), ("D6", "E8", "S12"))
        assets = adapter.source_assets(old_probe.CASES["E8"])
        self.assertEqual(tuple(item[0] for item in assets),
                         ("binary", "flow", "old_probe", "composite",
                          "input", "witness"))
        self.assertEqual(dict((label, expected) for label, _, expected
                              in assets)["composite"],
                         adapter.COMPOSITE_SHA)
        self.assertEqual(adapter.METHOD_ID,
                         "round88-a2-composite-penalty-offline")
        self.assertEqual(adapter.WHOLE_CASE_SECONDS, 120.0)

    def test_two_point_integer_line_and_original_strict_improvement(self) -> None:
        parsed, current, evidence = fixture()
        called = []
        events = []
        checkpoints = []

        def verifier(inventory):
            called.append(inventory)
            return fake_cpp_evidence(parsed.problem, inventory)

        status, best, best_evidence, record = adapter.one_round(
            parsed, current, evidence, verifier, events.append,
            checkpoints.append)
        self.assertEqual(status, "improved")
        self.assertEqual(record["proposal_inventory"], (1, 3))
        self.assertEqual(record["primitive_steps"], 2)
        self.assertEqual(called, [(2, 2), (1, 3)])
        self.assertEqual(best, (1, 3))
        self.assertLess(best_evidence.objective, evidence.objective)
        self.assertEqual(record["cpp_verified_line_points"], 2)
        self.assertEqual(record["internal_rejected_points"], 0)
        self.assertEqual(len(checkpoints), 1)
        self.assertIs(checkpoints[0], record)
        self.assertEqual(events[0]["kind"], "composite_oracle_complete")
        self.assertEqual(record["certificate"]["gini_gradient"],
                         [str(x) for x in composite.gini_local_gradient(
                             parsed.problem, current)])
        self.assertEqual(F(record["certificate"]["proxy_cost_from_initial"]),
                         composite.proxy_increment(
                             parsed.problem,
                             composite.gini_local_gradient(
                                 parsed.problem, current), (1, 3)))
        self.assertEqual(json.loads(json.dumps(record))["status"],
                         "improved")

    def test_ties_never_accepted_but_whole_line_checked(self) -> None:
        parsed, current, evidence = fixture()
        called = []

        def verifier(inventory):
            called.append(inventory)
            return evidence

        status, best, best_evidence, record = adapter.one_round(
            parsed, current, evidence, verifier, lambda _: None)
        self.assertEqual(status, "no_verified_improvement")
        self.assertEqual(best, current)
        self.assertIs(best_evidence, evidence)
        self.assertEqual(called, [(2, 2), (1, 3)])
        self.assertIsNone(record["accepted_inventory"])

    def test_invalid_current_rejected_before_cpp_and_s0_terminates(self) -> None:
        parsed, _current, evidence = fixture()

        def forbidden(_inventory):
            raise AssertionError("unexpected C++ candidate")

        with self.assertRaisesRegex(old_probe.ProbeError,
                                    "domain_rejected_current_zero_visit"):
            adapter.one_round(parsed, (4, 0), evidence, forbidden,
                              lambda _: None)
        matrix = tuple(tuple(F(0) for _ in range(3)) for _ in range(3))
        zero = flow.Problem(
            (flow.Station(1, 1, 1), flow.Station(0, 0, 1)),
            (flow.Vehicle((0,), 1, F(2), matrix),), F(1), F(1), F(0))
        parsed = old_probe.Parsed(zero, 0, Path("C:/probe/zero.txt"))
        evidence = fake_cpp_evidence(zero, (0, 0))
        status, best, _, record = adapter.one_round(
            parsed, (0, 0), evidence, forbidden, lambda _: None)
        self.assertEqual((status, best), ("no_gradient_at_zero", (0, 0)))
        self.assertEqual(record["status"], status)

    def test_bad_external_limit_rejected_before_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "not_created"
            with self.assertRaisesRegex(old_probe.ProbeError,
                                        "whole_case_limit_must_be_120"):
                adapter.supervise(old_probe.CASES["D6"], output, 119.0)
            self.assertFalse(output.exists())

    def test_supervision_requires_exit_status_method_and_case(self) -> None:
        case = old_probe.CASES["D6"]
        valid = dict(method=adapter.METHOD_ID, case=case.key,
                     status="domain_rejected_current_budget")
        classify = adapter.classify_supervision
        self.assertEqual(classify(False, 1.0, 120.0, True, 2,
                                  valid, case), "diagnostic_inapplicable")
        for returncode, child in (
                (1, valid), (0, valid),
                (2, dict(valid, method="old-linear-probe")),
                (2, dict(valid, case="E8"))):
            with self.subTest(returncode=returncode, child=child):
                self.assertEqual(classify(False, 1.0, 120.0, True,
                                          returncode, child, case),
                                 "diagnostic_invalid")
        complete = dict(valid, status="completed_composite_endpoint")
        self.assertEqual(classify(False, 1.0, 120.0, True, 0,
                                  complete, case), "diagnostic_completed")
        self.assertEqual(classify(False, 121.0, 120.0, True, 0,
                                  complete, case),
                         "unknown_whole_process_deadline")
        self.assertEqual(classify(False, 1.0, 120.0, False, 0,
                                  complete, case),
                         "invalid_source_identity_drift")


if __name__ == "__main__":
    unittest.main()
