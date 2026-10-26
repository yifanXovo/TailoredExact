"""Independent tiny-state qualifications for the A2 fixed-route prototype.

This file deliberately uses a separate exhaustive quantity enumerator and
separate physical/objective arithmetic as the linear-oracle reference. It has
no project binary, native solver, or external dependency.
"""

from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import round88_quantity_flow as q  # noqa: E402


def line_matrix(points: tuple[F, ...]) -> tuple[tuple[F, ...], ...]:
    return tuple(tuple(abs(a - b) for b in points) for a in points)


def independent_evidence(problem: q.Problem, inventory: tuple[int, ...],
                         routes: tuple[tuple[int, ...], ...]
                         ) -> q.PhysicalEvidence:
    n = len(problem.stations)
    if len(inventory) != n:
        return q.PhysicalEvidence(False, F(0))
    visited = {i for v in problem.vehicles for i in v.visits}
    if any(inventory[i] != s.initial for i, s in enumerate(problem.stations)
           if i not in visited):
        return q.PhysicalEvidence(False, F(0))
    for vehicle, route in zip(problem.vehicles, routes):
        if route != tuple(i for i in vehicle.visits
                          if problem.stations[i].initial - inventory[i] != 0):
            return q.PhysicalEvidence(False, F(0))
        carried = pickup = dropped = 0
        for i in route:
            s = problem.stations[i]
            if not 0 <= inventory[i] <= s.capacity:
                return q.PhysicalEvidence(False, F(0))
            u = s.initial - inventory[i]
            if u == 0:
                return q.PhysicalEvidence(False, F(0))
            carried += u
            pickup += max(u, 0)
            dropped += max(-u, 0)
            if not 0 <= carried <= vehicle.capacity:
                return q.PhysicalEvidence(False, F(0))
        path = (0,) + tuple(i + 1 for i in route) + (0,)
        travel = (sum((vehicle.distances[a][b]
                       for a, b in zip(path, path[1:])), F(0))
                  if route else F(0))
        duration = (travel + problem.pickup_time * pickup +
                    problem.drop_time * (dropped + carried))
        if duration > vehicle.deadline + q.PHYSICAL_TOLERANCE:
            return q.PhysicalEvidence(False, F(0))
    ratios = [F(y, s.target) for y, s in zip(inventory, problem.stations)]
    mass = sum(ratios, F(0))
    h = sum((abs(ratios[i] - ratios[j]) for i in range(n)
             for j in range(i + 1, n)), F(0))
    penalty = sum((s.weight * abs(r - 1)
                   for s, r in zip(problem.stations, ratios)), F(0))
    return q.PhysicalEvidence(
        True, (h / (n * mass) if mass else F(0)) +
        problem.penalty_weight * penalty)


def witness_problem() -> q.Problem:
    stations = (q.Station(4, 4, 3), q.Station(1, 4, 3),
                q.Station(4, 6, 1))
    vehicle = q.Vehicle((0, 1, 2), 3, F(18, 5),
                        line_matrix((F(0), F(1, 10), F(1, 5), F(3, 10))))
    return q.Problem(stations, (vehicle,), F(1, 2), F(1, 2), F(2))


def independently_enumerate_full_template(
        problem: q.Problem) -> tuple[tuple[int, ...], ...]:
    visited = {i for v in problem.vehicles for i in v.visits}
    states = []
    for candidate in product(*(range(s.capacity + 1)
                               for s in problem.stations)):
        if any(candidate[i] != s.initial for i, s in
               enumerate(problem.stations) if i not in visited):
            continue
        valid = True
        for vehicle in problem.vehicles:
            path = (0,) + tuple(i + 1 for i in vehicle.visits) + (0,)
            travel = sum((vehicle.distances[a][b]
                          for a, b in zip(path, path[1:])), F(0))
            if travel > vehicle.deadline:
                valid = False
                break
            service_unit = problem.pickup_time + problem.drop_time
            budget = (sum(problem.stations[i].initial
                          for i in vehicle.visits) if service_unit == 0
                      else int((vehicle.deadline - travel) // service_unit))
            carried = pickup = 0
            for i in vehicle.visits:
                u = problem.stations[i].initial - candidate[i]
                carried += u
                pickup += max(u, 0)
                if not 0 <= carried <= vehicle.capacity:
                    valid = False
            if pickup > budget:
                valid = False
        if valid:
            states.append(candidate)
    return tuple(states)


def independently_check_certificate(
        test: unittest.TestCase, certificate: q.FlowCertificate) -> None:
    """Rebuild the residual graph from returned primal arcs, outside solve()."""
    balance = [0 for _ in certificate.potentials]
    integer_cost = 0
    positive_residual = 0
    for start, end, capacity, cost, flow in certificate.arc_flows:
        test.assertTrue(all(isinstance(x, int) for x in
                            (start, end, capacity, cost, flow)))
        test.assertTrue(0 <= start < len(balance))
        test.assertTrue(0 <= end < len(balance))
        test.assertTrue(0 <= flow <= capacity)
        balance[start] -= flow
        balance[end] += flow
        integer_cost += flow * cost
        if capacity - flow > 0:
            positive_residual += 1
            test.assertGreaterEqual(
                cost + certificate.potentials[start] -
                certificate.potentials[end], 0)
        if flow > 0:
            positive_residual += 1
            test.assertGreaterEqual(
                -cost + certificate.potentials[end] -
                certificate.potentials[start], 0)
    test.assertEqual(balance, [0] * len(balance))
    test.assertEqual(integer_cost, certificate.integer_flow_cost)
    test.assertEqual(positive_residual,
                     certificate.positive_residual_edges)


def independently_check_network_arcs(
        test: unittest.TestCase, problem: q.Problem,
        budgets: tuple[int, ...], weights: tuple[F, ...],
        certificate: q.FlowCertificate) -> None:
    """Check that the certified graph is the declared complete route network."""
    scale = certificate.integer_cost_scale
    expected = []
    next_node = 2 + len(problem.vehicles)
    for k, (vehicle, budget) in enumerate(zip(problem.vehicles, budgets)):
        v = 2 + k
        expected.append((0, v, budget, 0))
        nodes = tuple(range(next_node, next_node + len(vehicle.visits)))
        next_node += len(nodes)
        for position, (i, node) in enumerate(zip(vehicle.visits, nodes)):
            station = problem.stations[i]
            test.assertEqual((weights[i] * scale).denominator, 1)
            cost = int(weights[i] * scale)
            expected.extend((
                (v, node, station.initial, -cost),
                (node, 1, station.capacity - station.initial, cost),
                (node, nodes[position + 1] if position + 1 < len(nodes)
                 else 1, vehicle.capacity, 0),
            ))
    expected.append((1, 0, sum(problem.stations[i].initial
                               for v in problem.vehicles
                               for i in v.visits), 0))
    test.assertEqual(tuple(arc[:4] for arc in certificate.arc_flows),
                     tuple(expected))


class QuantityFlowTests(unittest.TestCase):
    def test_three_station_joint_direction_matches_independent_enumerator(self):
        problem = witness_problem()
        current = (3, 2, 2)
        states = independently_enumerate_full_template(problem)
        self.assertEqual(len(states), 40)
        weights = q.gradient(problem, current)
        self.assertEqual(weights, (F(-8, 363), F(-272, 363), F(256, 121)))
        independent_cost = lambda y: sum(
            (g * (a - b) for g, a, b in zip(weights, y, current)), F(0))
        minimizers = tuple(y for y in states if independent_cost(y) ==
                           min(map(independent_cost, states)))
        self.assertEqual(minimizers, ((4, 1, 1),))
        outcome = q.run_quantity_oracle(problem, current, independent_evidence)
        self.assertEqual(outcome.status, "improved")
        self.assertEqual(outcome.proposal_inventory, (4, 1, 1))
        self.assertEqual(outcome.accepted_inventory, (4, 1, 1))
        self.assertEqual(outcome.current_original_objective, F(32, 11))
        self.assertEqual(outcome.accepted_original_objective, F(9, 4))
        self.assertEqual(outcome.primitive_steps, 1)
        self.assertEqual(outcome.certificate.integer_flow_cost,
                         sum((g * (a - s.initial) for g, a, s in
                              zip(weights, outcome.proposal_inventory,
                                  problem.stations)), F(0)) *
                         outcome.certificate.integer_cost_scale)
        independently_check_certificate(self, outcome.certificate)
        independently_check_network_arcs(
            self, problem, q.nominal_budgets(problem), weights,
            outcome.certificate)
        self.assertTrue(q.exact_physical_feasible(
            problem, outcome.accepted_inventory))

    def test_tie_gradient_failure_is_not_neighborhood_certificate(self):
        stations = (q.Station(2, 6, 2), q.Station(3, 3, 3),
                    q.Station(3, 7, 4))
        vehicle = q.Vehicle((0, 1, 2), 4, F(33, 5),
                            line_matrix((F(0), F(1, 10),
                                         F(1, 5), F(3, 10))))
        problem = q.Problem(stations, (vehicle,), F(1, 2), F(1, 2), F(2))
        current = (1, 2, 4)
        outcome = q.run_quantity_oracle(problem, current, independent_evidence)
        self.assertEqual(outcome.status, "no_verified_improvement")
        self.assertEqual(outcome.proposal_inventory, (2, 3, 0))
        self.assertEqual(outcome.primitive_steps, 1)
        self.assertEqual(outcome.current_original_objective, F(71, 39))
        self.assertEqual(independent_evidence(
            problem, outcome.proposal_inventory, ((2,),)).objective, F(7, 3))
        self.assertEqual(independent_evidence(
            problem, (2, 3, 3), ((),)).objective, F(37, 66))

    def test_heterogeneous_vehicles_loaded_returns_and_unvisited_global_ratio(self):
        stations = (q.Station(2, 2, 1), q.Station(2, 2, 1),
                    q.Station(5, 5, 10))
        matrix = tuple(tuple(F(0) for _ in range(4)) for _ in range(4))
        problem = q.Problem(
            stations,
            (q.Vehicle((0,), 1, F(0), matrix),
             q.Vehicle((1,), 2, F(0), matrix)),
            F(0), F(0), F(1))
        budgets = q.nominal_budgets(problem)
        self.assertEqual(budgets, (2, 2))
        proposal, certificate = q._linear_oracle(
            problem, (F(1), F(1), F(-10)), budgets)
        self.assertEqual(proposal, (1, 0, 5))
        self.assertEqual(certificate.integer_flow_cost, -3)
        independently_check_certificate(self, certificate)
        independently_check_network_arcs(
            self, problem, budgets, (F(1), F(1), F(-10)), certificate)
        self.assertTrue(q.exact_physical_feasible(problem, proposal))
        self.assertFalse(q.exact_physical_feasible(problem, (0, 1, 5)))
        # The unvisited third station still changes the global S/H/P terms.
        short = q.Problem(stations[:2], (
            q.Vehicle((0,), 1, F(0), tuple(row[:3] for row in matrix[:3])),
            q.Vehicle((1,), 2, F(0), tuple(row[:3] for row in matrix[:3]))),
            F(0), F(0), F(1))
        self.assertNotEqual(q.objective(problem, proposal),
                            q.objective(short, proposal[:2]))
        self.assertEqual(len(q.gradient(problem, proposal)), 3)

    def test_parallel_residual_arcs_and_no_negative_cycle_certificate(self):
        network = q.MinCostCirculation(2)
        first = network.add_arc(0, 1, 1, -1)
        second = network.add_arc(0, 1, 1, -2)
        network.add_arc(1, 0, 2, 0)
        certificate = network.solve()
        self.assertEqual((network.flow(first), network.flow(second)), (1, 1))
        self.assertEqual(certificate.integer_flow_cost, -3)
        self.assertGreater(certificate.negative_cycle_augmentations, 0)
        independently_check_certificate(self, certificate)

    def test_exhaustive_two_station_cross_product_against_separate_enumerator(self):
        matrix = tuple(tuple(F(0) for _ in range(3)) for _ in range(3))
        route_patterns = (((0, 1),), ((0,), (1,)), ((), (0, 1)))
        weights_cases = ((F(-1), F(1)), (F(1, 2), F(2, 3)))
        for initials in ((0, 1), (1, 1)):
            for extras in ((0, 1), (1, 0)):
                stations = tuple(q.Station(b, b + extra, 1)
                                 for b, extra in zip(initials, extras))
                for pattern in route_patterns:
                    for service in (F(0), F(1)):
                        for deadline in (F(0), F(2)):
                            vehicles = tuple(q.Vehicle(
                                route, 1 if k == 0 else 2,
                                deadline, matrix)
                                for k, route in enumerate(pattern))
                            problem = q.Problem(stations, vehicles,
                                                service, F(0), F(1))
                            budgets = q.nominal_budgets(problem)
                            states = independently_enumerate_full_template(
                                problem)
                            self.assertGreater(len(states), 0)
                            for weights in weights_cases:
                                proposal, certificate = q._linear_oracle(
                                    problem, weights, budgets)
                                linear = lambda y: sum(
                                    (g * (yi - s.initial) for g, yi, s in
                                     zip(weights, y, stations)), F(0))
                                self.assertEqual(linear(proposal),
                                                 min(map(linear, states)))
                                self.assertIn(proposal, states)
                                self.assertEqual(
                                    certificate.integer_flow_cost,
                                    linear(proposal) *
                                    certificate.integer_cost_scale)
                                independently_check_certificate(
                                    self, certificate)
                                independently_check_network_arcs(
                                    self, problem, budgets, weights,
                                    certificate)

    def test_same_station_pick_drop_cancellation_and_primitive_integer_line(self):
        self.assertEqual(q.cancel_same_station(2, 1), (1, 0, 1))
        self.assertEqual(q.cancel_same_station(1, 2), (0, 1, 1))
        self.assertEqual(q.primitive_segment((0, 1, 3), (4, 3, 1)),
                         ((0, 1, 3), (2, 2, 2), (4, 3, 1)))
        self.assertEqual(q.primitive_segment((2, 1), (2, 1)), ((2, 1),))

    def test_full_integer_line_selects_verified_interior_point(self):
        matrix = ((F(0), F(0)), (F(0), F(0)))
        problem = q.Problem(
            (q.Station(3, 3, 2),),
            (q.Vehicle((0,), 3, F(0), matrix),),
            F(0), F(0), F(1))
        outcome = q.run_quantity_oracle(problem, (1,), independent_evidence)
        self.assertEqual(outcome.proposal_inventory, (3,))
        self.assertEqual(outcome.accepted_inventory, (2,))
        self.assertEqual(outcome.status, "improved")
        self.assertEqual(outcome.primitive_steps, 2)
        self.assertEqual(outcome.checked_integer_points, 3)
        self.assertEqual(outcome.accepted_original_objective, F(0))

        def reject_interior(p, y, route):
            evidence = independent_evidence(p, y, route)
            return q.PhysicalEvidence(False, evidence.objective) if y == (2,) \
                else evidence

        blocked = q.run_quantity_oracle(problem, (1,), reject_interior)
        self.assertEqual(blocked.status, "no_verified_improvement")
        self.assertEqual(blocked.rejected_physical_points, 1)

    def test_nonmetric_deletion_requires_actual_route_recheck(self):
        # Full 0->A->B->0 is 3, but deleting A changes travel to 11.
        distances = ((F(0), F(1), F(10)),
                     (F(1), F(0), F(1)),
                     (F(1), F(1), F(0)))
        problem = q.Problem(
            (q.Station(1, 1, 1), q.Station(1, 1, 1)),
            (q.Vehicle((0, 1), 2, F(3), distances),),
            F(0), F(0), F(1))
        self.assertTrue(q.exact_physical_feasible(problem, (0, 0)))
        self.assertFalse(q.exact_physical_feasible(problem, (1, 0)))
        self.assertEqual(q.route_travel(problem.vehicles[0], (0, 1)), F(3))
        self.assertEqual(q.route_travel(problem.vehicles[0], (1,)), F(11))

    def test_nominal_budget_rejects_tolerance_only_current(self):
        matrix = ((F(0), F(0)), (F(0), F(0)))
        problem = q.Problem(
            (q.Station(1, 1, 1),),
            (q.Vehicle((0,), 1, F(1) - F(5, 100_000_000), matrix),),
            F(1), F(0), F(0))
        self.assertTrue(q.exact_physical_feasible(problem, (0,)))
        def should_not_verify(*_args):
            self.fail("current point outside nominal network domain")
        self.assertEqual(q.run_quantity_oracle(
            problem, (0,), should_not_verify).status,
            "domain_rejected_current_budget")

    def test_zero_service_still_checks_full_template_and_current_zero_visit(self):
        matrix = ((F(0), F(2)), (F(2), F(0)))
        problem = q.Problem(
            (q.Station(1, 1, 1),),
            (q.Vehicle((0,), 1, F(1), matrix),),
            F(0), F(0), F(0))
        self.assertEqual(q.run_quantity_oracle(
            problem, (0,), independent_evidence).status,
            "domain_rejected_full_template_time")
        zero_matrix = ((F(0), F(0)), (F(0), F(0)))
        valid_template = q.Problem(
            problem.stations, (q.Vehicle((0,), 1, F(0), zero_matrix),),
            F(0), F(0), F(0))
        self.assertEqual(q.run_quantity_oracle(
            valid_template, (1,), independent_evidence).status,
            "domain_rejected_current_zero_visit")

    def test_S_zero_and_gcd_zero_have_distinct_safe_statuses(self):
        matrix = ((F(0), F(0)), (F(0), F(0)))
        zero = q.Problem((q.Station(0, 1, 1),),
                         (q.Vehicle((), 1, F(0), matrix),),
                         F(0), F(0), F(1))
        self.assertEqual(q.run_quantity_oracle(
            zero, (0,), independent_evidence).status,
            "no_gradient_at_zero")
        flat = q.Problem((q.Station(1, 1, 1),),
                         (q.Vehicle((), 1, F(0), matrix),),
                         F(0), F(0), F(1))
        outcome = q.run_quantity_oracle(flat, (1,), independent_evidence)
        self.assertEqual(outcome.status, "no_direction")
        self.assertEqual(outcome.primitive_steps, 0)
        self.assertEqual(outcome.proposal_inventory, (1,))


if __name__ == "__main__":
    unittest.main()
