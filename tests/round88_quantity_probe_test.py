"""Small no-solver A2 endpoint adapter qualifications."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import round88_quantity_flow as flow
import round88_quantity_probe as probe


def fixture() -> tuple[probe.Parsed, probe.Case, dict, Path]:
    case = probe.Case("tiny", "tiny.txt", "", "tiny.json", "", 100,
                      1, 1, 0.15)
    stations = (flow.Station(2, 4, 2, F(1)),
                flow.Station(1, 3, 1, F(1)))
    distances = ((F(0), F(1), F(2)),
                 (F(1), F(0), F(1)),
                 (F(2), F(1), F(0)))
    vehicle = flow.Vehicle((0,), 3, F(100), distances)
    parsed = probe.Parsed(flow.Problem(stations, (vehicle,), F(1), F(1),
                                       F.from_float(0.15)), 99,
                          Path("C:/probe/tiny.txt"))
    candidate = dict(routes=[dict(vehicle=0, nodes=[0, 1, 0],
                                  operations=[dict(station=1, pickup=1,
                                                   drop=0)])])
    return parsed, case, candidate, Path("C:/probe/output.json")


def receipt(parsed: probe.Parsed, case: probe.Case,
            candidate: dict, output: Path) -> dict:
    return dict(method="incumbent-import-test", status="diagnostic_complete",
                incumbent_import_attempted=True,
                incumbent_import_verified=True,
                incumbent_source="incumbent-json",
                incumbent_import_errors=[],
                instance_name=parsed.source_input.name,
                input_path=str(parsed.source_input), result_file=str(output),
                route_time_limit_seconds=case.route_deadline,
                pickup_time_seconds=case.pickup_seconds,
                drop_time_seconds=case.drop_seconds,
                routes=deepcopy(candidate["routes"]),
                final_inventories=[99, 1, 1],
                objective=0.15, G=0.0, P=1.0,
                incumbent_import_objective=0.15,
                verification=dict(
                    feasible=True, original_solution_feasible=True,
                    original_objective_recomputed=True,
                    routes_start_end_depot=True, station_disjoint=True,
                    load_feasible=True, station_feasible=True,
                    duration_feasible=True, objective_matches=True,
                    errors=[], final_inventories=[99, 1, 1],
                    objective=0.15, G=0.0, P=1.0,
                    route_travel_time=[2.0], route_duration=[4.0]))


class ParserMappingTest(unittest.TestCase):
    def test_points_override_serialized_distances_and_depot(self) -> None:
        case = probe.Case("tiny", "", "", "", "", 100, 1, 1)
        source = """2 1 [3]
capacities = [100, 4, 3]
initial = [99, 2, 1]
target = [0, 2, 1]
weights = [0, 10, 5]
points = [(0,0), (3,0), (3,4)]
distances = [ [0,999,999] ]
"""
        parsed = probe.parse_instance(source, case, Path("tiny.txt"))
        self.assertEqual(len(parsed.problem.stations), 2)
        self.assertEqual(parsed.depot_initial, 99)
        self.assertEqual(parsed.problem.stations[0].weight, F(1))
        self.assertEqual(parsed.problem.vehicles[0].distances[0][1], F(2))
        self.assertEqual(parsed.problem.vehicles[0].distances[1][2], F.from_float(4 / 1.5))

    def test_route_round_trip_unvisited_and_empty_vehicle(self) -> None:
        parsed, _, candidate, _ = fixture()
        canonical = probe.canonical_routes(candidate["routes"], 1, 2)
        self.assertEqual(probe.inventory_from_routes(parsed, canonical), (1, 1))
        attached = probe.attach_fixed_routes(parsed, canonical)
        self.assertEqual(probe.routes_from_inventory(attached, (1, 1)),
                         candidate)
        p = parsed.problem
        empty = flow.Vehicle((), 3, F(100), p.vehicles[0].distances)
        two = probe.Parsed(flow.Problem(p.stations,
                                        (p.vehicles[0], empty),
                                        p.pickup_time, p.drop_time,
                                        p.penalty_weight), 99,
                           parsed.source_input)
        routes = probe.routes_from_inventory(two, (1, 1))["routes"]
        self.assertEqual(routes[1], dict(vehicle=1, nodes=[0, 0],
                                         operations=[]))
        with self.assertRaises(probe.ProbeError):
            probe.canonical_routes([dict(vehicle=0, nodes=[0, 1, 0],
                                         operations=[dict(station=1,
                                                          pickup=1,
                                                          drop=1)])], 1, 2)


class ReceiptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.parsed, self.case, self.candidate, self.output = fixture()
        self.good = receipt(self.parsed, self.case, self.candidate, self.output)

    def test_complete_original_cpp_receipt(self) -> None:
        evidence = probe.validate_cpp_receipt(
            self.good, self.candidate, self.parsed, self.case, self.output)
        self.assertEqual(evidence.objective, F.from_float(0.15))
        self.assertEqual(evidence.route_travel, (F(2),))

    def test_fallback_failure_and_candidate_mismatch_rejected(self) -> None:
        mutants = []
        for path, value in (
                (("status",), "diagnostic_failed"),
                (("incumbent_import_verified",), False),
                (("incumbent_source",), "external-incumbent"),
                (("verification", "feasible"), False),
                (("verification", "original_objective_recomputed"), False),
                (("verification", "errors"), ["bad"]),
                (("verification", "final_inventories"), [99, 2, 1]),
                (("routes", 0, "nodes"), [0, 0]),
                (("routes", 0, "operations", 0, "pickup"), 2),
                (("input_path",), "C:/other/tiny.txt"),
                (("result_file",), "C:/other/result.json"),
                (("route_time_limit_seconds",), 101),
                (("verification", "objective"), float("nan")),
                (("P",), 0.0)):
            mutant = deepcopy(self.good)
            cursor = mutant
            for key in path[:-1]:
                cursor = cursor[key]
            cursor[path[-1]] = value
            mutants.append((path, mutant))
        for path, mutant in mutants:
            with self.subTest(path=path), self.assertRaises(probe.ProbeError):
                probe.validate_cpp_receipt(mutant, self.candidate,
                                           self.parsed, self.case, self.output)
        wrong_lambda = deepcopy(self.good)
        wrong_lambda["P"] = wrong_lambda["verification"]["P"] = 0.0
        with self.assertRaisesRegex(probe.ProbeError,
                                    "receipt_lambda_objective_identity"):
            probe.validate_cpp_receipt(wrong_lambda, self.candidate,
                                       self.parsed, self.case, self.output)


class BudgetAndLineTest(unittest.TestCase):
    def test_budget_floor_uses_cpp_binary_evidence_not_epsilon(self) -> None:
        parsed, _, _, _ = fixture()
        p = parsed.problem
        one = flow.Vehicle((0,), 3, F(2),
                           tuple(tuple(F(0) for _ in range(3))
                                 for _ in range(3)))
        parsed = probe.Parsed(flow.Problem(p.stations, (one,), F(1), F(1),
                                           p.penalty_weight), 99,
                              parsed.source_input)
        good = probe.CppEvidence(F(0), F(0), F(0), (F(0),), (F(0),))
        self.assertEqual(probe.cpp_nominal_budgets(parsed, good), (1,))
        tiny = probe.CppEvidence(F(0), F(0), F(0),
                                 (F(1, 2**52),), (F(0),))
        with self.assertRaisesRegex(probe.ProbeError,
                                    "domain_uncertain_budget_floor"):
            probe.cpp_nominal_budgets(parsed, tiny)

    def test_nonmetric_deleted_stop_rejected_before_cpp(self) -> None:
        p = flow.Problem(
            (flow.Station(1, 1, 1), flow.Station(1, 1, 1)),
            (flow.Vehicle((0, 1), 2, F(8),
                          ((F(0), F(1), F(10)),
                           (F(1), F(0), F(1)),
                           (F(1), F(1), F(0)))),), F(1), F(1), F(0))
        parsed = probe.Parsed(p, 0, Path("tiny.txt"))
        self.assertTrue(flow.exact_physical_feasible(p, (0, 0)))
        self.assertFalse(flow.exact_physical_feasible(p, (1, 0)))
        events = []
        def forbidden(_inventory):
            raise AssertionError("internal reject called C++")
        evidence = probe.CppEvidence(F(3), F(0), F(0), (F(3),), (F(7),))
        best, _, rejected, calls = probe.scan_integer_line(
            parsed, (0, 0), (1, 0), evidence, forbidden, events.append)
        self.assertEqual((best, rejected, calls), ((0, 0), 1, 0))
        self.assertEqual(events[0]["kind"], "internal_physical_reject")

    def test_full_primitive_segment_strict_cpp_improvement_and_tie(self) -> None:
        p = flow.Problem(
            (flow.Station(3, 3, 1),),
            (flow.Vehicle((0,), 3, F(100),
                          ((F(0), F(1)), (F(1), F(0)))),),
            F(1), F(1), F(0))
        parsed = probe.Parsed(p, 0, Path("tiny.txt"))
        called = []
        def verify(inventory):
            called.append(inventory)
            return probe.CppEvidence(F(4), F(0), F(0), (F(2),), (F(5),))
        current_evidence = probe.CppEvidence(F(6), F(0), F(0),
                                              (F(2),), (F(4),))
        best, evidence, rejected, calls = probe.scan_integer_line(
            parsed, (2,), (0,), current_evidence, verify, lambda _: None)
        self.assertEqual(called, [(1,), (0,)])
        self.assertEqual((best, evidence.objective, rejected, calls),
                         ((1,), F(4), 0, 2))

    def test_supervisor_rejects_altered_limit_without_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as root:
            destination = Path(root) / "output"
            with self.assertRaises(probe.ProbeError):
                probe.supervise(probe.CASES["D6"], destination, 119.0)
            self.assertFalse(destination.exists())

    def test_preflight_deadline_never_spawns_child(self) -> None:
        with tempfile.TemporaryDirectory() as root, \
                mock.patch.object(probe, "require_sha"), \
                mock.patch.object(probe, "sha256", return_value="fake"), \
                mock.patch.object(probe.time, "perf_counter",
                                  side_effect=(0.0, 121.0, 121.0, 121.0)), \
                mock.patch.object(probe.subprocess, "Popen",
                                  side_effect=AssertionError("late spawn")):
            summary = probe.supervise(probe.CASES["D6"],
                                      Path(root) / "late", 120.0)
            self.assertEqual(summary["status"],
                             "unknown_whole_process_deadline")
            self.assertIsNone(summary["child_pid"])

    def test_job_close_cleans_descendants_after_parent_exit(self) -> None:
        class FakeJob:
            closed = False
            def close(self):
                self.closed = True
        class ExitedParent:
            pid = 987654
            def poll(self):
                return 0
            def wait(self, timeout=None):
                return 0
        job = FakeJob()
        if probe.os.name == "nt":
            probe._kill_process_tree(ExitedParent(), job)
            self.assertTrue(job.closed)


if __name__ == "__main__":
    unittest.main()
