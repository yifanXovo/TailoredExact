"""Independent rational qualifications for the composite quantity proxy.

No native binary, MIP solver, endpoint or performance run is used here.
"""

from __future__ import annotations

from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import round88_quantity_flow as q
import round88_quantity_composite as c


def manual_proxy(problem: q.Problem, gradient: tuple[F, ...],
                 inventory: tuple[int, ...]) -> F:
    """A direct absolute-value formula, independent of arc generation."""
    total = F(0)
    for i, station in enumerate(problem.stations):
        y, b, target = inventory[i], station.initial, station.target
        total += gradient[i] * (y - b)
        total += F(problem.penalty_weight) * F(station.weight) * (
            abs(F(y - target, target)) - abs(F(b - target, target)))
    return total


def manual_gini_gradient(problem: q.Problem,
                         inventory: tuple[int, ...]) -> tuple[F, ...] | None:
    ratios = tuple(F(y, s.target) for y, s in
                   zip(inventory, problem.stations))
    mass = sum(ratios, F(0))
    if not mass:
        return None
    pair_sum = sum((abs(ratios[i] - ratios[j])
                    for i in range(len(ratios))
                    for j in range(i + 1, len(ratios))), F(0))
    answer = []
    for i, station in enumerate(problem.stations):
        sign_sum = 0
        for j in range(len(ratios)):
            if j != i:
                sign_sum += (1 if ratios[i] > ratios[j] else
                             -1 if ratios[i] < ratios[j] else 0)
        answer.append((mass * sign_sum - pair_sum) /
                      (len(ratios) * mass * mass * station.target))
    return tuple(answer)


def independent_budgets(problem: q.Problem) -> tuple[int, ...] | None:
    service = problem.pickup_time + problem.drop_time
    answer = []
    for vehicle in problem.vehicles:
        visits = vehicle.visits
        nodes = (0,) + tuple(i + 1 for i in visits) + (0,)
        travel = (sum((vehicle.distances[a][b] for a, b in
                       zip(nodes, nodes[1:])), F(0)) if visits else F(0))
        if travel > vehicle.deadline:
            return None
        stock = sum(problem.stations[i].initial for i in visits)
        answer.append(stock if service == 0 else
                      min(stock, int((vehicle.deadline - travel) // service)))
    return tuple(answer)


def independent_states(problem: q.Problem,
                       budgets: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    visited = {i for vehicle in problem.vehicles for i in vehicle.visits}
    candidates = []
    for y in product(*(range(s.capacity + 1) for s in problem.stations)):
        if any(y[i] != s.initial for i, s in enumerate(problem.stations)
               if i not in visited):
            continue
        valid = True
        for vehicle, budget in zip(problem.vehicles, budgets):
            load = pickups = 0
            for i in vehicle.visits:
                net = problem.stations[i].initial - y[i]
                pickups += max(net, 0)
                load += net
                valid &= 0 <= load <= vehicle.capacity
            valid &= pickups <= budget
        if valid:
            candidates.append(tuple(y))
    return tuple(candidates)


def independent_residual_certificate(
        test: unittest.TestCase, certificate: q.FlowCertificate) -> None:
    balance = [0] * len(certificate.potentials)
    paid_cost = 0
    residual_count = 0
    for u, v, capacity, cost, amount in certificate.arc_flows:
        test.assertTrue(all(isinstance(x, int) for x in
                            (u, v, capacity, cost, amount)))
        test.assertTrue(0 <= u < len(balance) and 0 <= v < len(balance))
        test.assertTrue(0 <= amount <= capacity)
        balance[u] -= amount
        balance[v] += amount
        paid_cost += amount * cost
        if capacity > amount:
            residual_count += 1
            test.assertGreaterEqual(
                cost + certificate.potentials[u] -
                certificate.potentials[v], 0)
        if amount:
            residual_count += 1
            test.assertGreaterEqual(
                -cost + certificate.potentials[v] -
                certificate.potentials[u], 0)
    test.assertEqual(balance, [0] * len(balance))
    test.assertEqual(paid_cost, certificate.integer_flow_cost)
    test.assertEqual(residual_count, certificate.positive_residual_edges)


def independent_unit_costs(b: int, capacity: int, target: F,
                           gradient: F, lambda_weight: F,
                           direction: str) -> tuple[F, ...]:
    # Closed-form absolute penalty differences, with no call to phi/segments.
    out = []
    limit = b if direction == "pickup" else capacity - b
    for unit in range(1, limit + 1):
        old = b - unit + 1 if direction == "pickup" else b + unit - 1
        new = old - 1 if direction == "pickup" else old + 1
        out.append(gradient * (new - old) + lambda_weight * (
            abs(F(new, 1) / target - 1) -
            abs(F(old, 1) / target - 1)))
    return tuple(out)


def independent_arc_set(test: unittest.TestCase, problem: q.Problem,
                        gradient: tuple[F, ...], budgets: tuple[int, ...],
                        cert: c.CompositeCertificate) -> None:
    scale = cert.network.integer_cost_scale
    expected = []
    marginal_expected = []
    next_node = 2 + len(problem.vehicles)
    for k, (vehicle, budget) in enumerate(zip(problem.vehicles, budgets)):
        vehicle_node = 2 + k
        expected.append((0, vehicle_node, budget, 0))
        nodes = tuple(range(next_node,
                            next_node + len(vehicle.visits)))
        next_node += len(nodes)
        for position, (i, node) in enumerate(zip(vehicle.visits, nodes)):
            station = problem.stations[i]
            penalty = problem.penalty_weight * station.weight
            for direction, u, v in (("pickup", vehicle_node, node),
                                    ("drop", node, 1)):
                costs = independent_unit_costs(
                    station.initial, station.capacity, F(station.target),
                    gradient[i], penalty, direction)
                for unit, cost in enumerate(costs, 1):
                    test.assertEqual((cost * scale).denominator, 1)
                    if (marginal_expected and marginal_expected[-1][0] == i
                            and marginal_expected[-1][1] == direction
                            and marginal_expected[-1][4] == cost):
                        old = marginal_expected[-1]
                        marginal_expected[-1] = (i, direction, old[2],
                                                  old[3] + 1, cost, u, v)
                        old_arc = expected[-1]
                        expected[-1] = (u, v, old_arc[2] + 1,
                                        int(cost * scale))
                    else:
                        marginal_expected.append((i, direction, unit,
                                                  1, cost, u, v))
                        expected.append((u, v, 1, int(cost * scale)))
            following = (nodes[position + 1]
                         if position + 1 < len(nodes) else 1)
            expected.append((node, following, vehicle.capacity, 0))
    expected.append((1, 0, sum(problem.stations[i].initial
                               for vehicle in problem.vehicles
                               for i in vehicle.visits), 0))
    test.assertEqual(tuple(arc[:4] for arc in cert.network.arc_flows),
                     tuple(expected))
    for marginal, declared in zip(marginal_expected, cert.marginal_arcs):
        test.assertEqual(marginal[:5],
                         (declared.station, declared.direction,
                          declared.first_unit, declared.units,
                          declared.rational_cost))
        test.assertEqual(cert.network.arc_flows[declared.arc_id][:4],
                         (marginal[5], marginal[6], marginal[3],
                          int(marginal[4] * scale)))
    test.assertEqual(len(marginal_expected), len(cert.marginal_arcs))


class CompositeQuantityTests(unittest.TestCase):
    def test_manual_two_station_penalty_rebalancing(self) -> None:
        matrix = tuple(tuple(F(0) for _ in range(3)) for _ in range(3))
        problem = q.Problem(
            (q.Station(2, 2, 1, F(1)),
             q.Station(0, 1, 1, F(1))),
            (q.Vehicle((0, 1), 1, F(2), matrix),),
            F(1), F(1), F(1))
        current = (2, 0)
        gradient = c.gini_local_gradient(problem, current)
        self.assertEqual(gradient, (F(0), F(-1, 2)))
        self.assertEqual(gradient, manual_gini_gradient(problem, current))
        budgets = independent_budgets(problem)
        self.assertEqual(budgets, (1,))
        proposal, certificate = c.composite_oracle(problem, gradient, budgets)
        self.assertEqual(proposal, (1, 1))
        self.assertEqual(certificate.proxy_cost_from_initial, F(-5, 2))
        self.assertEqual(certificate.raw_flow_cost_from_initial, F(-5, 2))
        self.assertEqual(certificate.network.integer_flow_cost,
                         F(-5, 2) * certificate.network.integer_cost_scale)
        self.assertEqual(q.objective(problem, current), F(5, 2))
        self.assertEqual(q.objective(problem, proposal), F(0))
        independent_residual_certificate(self, certificate.network)
        independent_arc_set(self, problem, gradient, budgets, certificate)

    def test_integer_and_fractional_targets_make_exact_two_or_three_segments(self):
        self.assertEqual(c.marginal_segments(
            1, 6, F(7, 2), F(0), F(1), "drop"),
            ((1, 2, F(-2, 7)), (3, 1, F(0)), (4, 2, F(2, 7))))
        self.assertEqual(c.marginal_segments(
            6, 6, F(7, 2), F(0), F(1), "pickup"),
            ((1, 2, F(-2, 7)), (3, 1, F(0)), (4, 3, F(2, 7))))
        self.assertEqual(c.marginal_segments(
            1, 5, F(3), F(0), F(1), "drop"),
            ((1, 2, F(-1, 3)), (3, 2, F(1, 3))))
        self.assertEqual(c.marginal_segments(
            1, 3, F(10), F(0), F(1), "drop"),
            ((1, 2, F(-1, 10)),))
        self.assertEqual(c.marginal_segments(
            1, 4, F(3, 2), F(2, 3), F(0), "drop"),
            ((1, 3, F(2, 3)),))
        with self.assertRaises(ValueError):
            c.marginal_segments(2, 1, F(1), F(0), F(1), "drop")

    def test_independent_inventory_enumeration_and_full_arc_certificate(self):
        matrix = tuple(tuple(F(0) for _ in range(3)) for _ in range(3))
        patterns = (((0, 1),), ((0,), (1,)), ((), (0, 1)))
        combinations = 0
        for initials in ((0, 1), (1, 1), (2, 0)):
            for extras in ((0, 1), (1, 1)):
                stations = (q.Station(initials[0], initials[0] + extras[0],
                                      1, F(0)),
                            q.Station(initials[1], initials[1] + extras[1],
                                      2, F(2, 3)))
                for pattern in patterns:
                    for vehicle_capacity in (0, 2):
                        for deadline in (F(0), F(2), F(4)):
                            for penalty in (F(0), F(1, 2)):
                                vehicles = tuple(q.Vehicle(
                                    route, vehicle_capacity if k == 0 else 2,
                                    deadline, matrix)
                                    for k, route in enumerate(pattern))
                                problem = q.Problem(
                                    stations, vehicles, F(1), F(1), penalty)
                                budgets = independent_budgets(problem)
                                self.assertEqual(budgets,
                                                 q.nominal_budgets(problem))
                                gradient = manual_gini_gradient(
                                    problem, initials)
                                if gradient is None:
                                    gradient = (F(-1, 3), F(1, 4))
                                self.assertEqual(
                                    c.gini_local_gradient(problem, initials),
                                    manual_gini_gradient(problem, initials))
                                proposal, certificate = c.composite_oracle(
                                    problem, gradient, budgets)
                                states = independent_states(problem, budgets)
                                direct = {y: manual_proxy(problem, gradient, y)
                                          for y in states}
                                self.assertTrue(states)
                                self.assertIn(proposal, states)
                                self.assertEqual(direct[proposal],
                                                 min(direct.values()))
                                self.assertEqual(
                                    certificate.network.integer_flow_cost,
                                    min(direct.values()) *
                                    certificate.network.integer_cost_scale)
                                self.assertEqual(certificate.proxy_cost_from_initial,
                                                 direct[proposal])
                                self.assertEqual(certificate.raw_flow_cost_from_initial,
                                                 direct[proposal])
                                independent_residual_certificate(
                                    self, certificate.network)
                                independent_arc_set(
                                    self, problem, gradient, budgets,
                                    certificate)
                                combinations += 1
        self.assertEqual(combinations, 216)

    def test_cancellation_never_increases_convex_proxy_or_changes_load(self):
        cases = 0
        for b in range(4):
            for capacity in range(b, 5):
                for target in (F(1), F(3, 2), F(5)):
                    for gradient in (F(-2, 3), F(1, 4)):
                        for penalty in (F(0), F(1, 2), F(2)):
                            for pickup in range(b + 1):
                                for drop in range(capacity - b + 1):
                                    canceled = min(pickup, drop)
                                    net_before = pickup - drop
                                    net_after = ((pickup - canceled) -
                                                 (drop - canceled))
                                    self.assertEqual(net_before, net_after)
                                    self.assertLessEqual(pickup - canceled,
                                                         pickup)
                                    before = (
                                        gradient * (-pickup + drop) +
                                        penalty * (
                                            abs(F(b - pickup, 1) / target - 1) +
                                            abs(F(b + drop, 1) / target - 1) -
                                            2 * abs(F(b, 1) / target - 1)))
                                    final = b - pickup + drop
                                    after = (
                                        gradient * (final - b) +
                                        penalty * (
                                            abs(F(final, 1) / target - 1) -
                                            abs(F(b, 1) / target - 1)))
                                    self.assertLessEqual(after, before)
                                    cases += 1
        self.assertGreater(cases, 1000)

    def test_empty_route_zero_Q_zero_K_and_zero_weight(self):
        matrix = tuple(tuple(F(0) for _ in range(3)) for _ in range(3))
        problem = q.Problem(
            (q.Station(1, 1, 2, F(0)), q.Station(0, 0, 1, F(0))),
            (q.Vehicle((), 0, F(0), matrix),), F(1), F(1), F(0))
        gradient = c.gini_local_gradient(problem, (1, 0))
        budgets = independent_budgets(problem)
        self.assertEqual(budgets, (0,))
        proposal, certificate = c.composite_oracle(problem, gradient, budgets)
        self.assertEqual(proposal, (1, 0))
        self.assertEqual(certificate.marginal_arcs, ())
        self.assertEqual(certificate.proxy_cost_from_initial, 0)
        independent_residual_certificate(self, certificate.network)
        independent_arc_set(self, problem, gradient, budgets, certificate)
        outcome = c.run_composite_oracle(
            problem, (1, 0), lambda p, y, r: q.PhysicalEvidence(
                True, q.objective(p, y)))
        self.assertEqual(outcome.status, "no_direction")

    def test_loaded_return_full_line_and_zero_mass(self):
        matrix = tuple(tuple(F(0) for _ in range(3)) for _ in range(3))
        problem = q.Problem(
            (q.Station(2, 2, 2, F(1)),
             q.Station(1, 1, 1, F(1))),
            (q.Vehicle((0,), 1, F(2), matrix),),
            F(1), F(1), F(1))
        seen = []
        def verifier(p, y, routes):
            seen.append((y, routes))
            return q.PhysicalEvidence(True, q.objective(p, y))
        outcome = c.run_composite_oracle(problem, (1, 1), verifier)
        self.assertEqual(outcome.status, "improved")
        self.assertEqual(outcome.proposal_inventory, (2, 1))
        self.assertEqual(outcome.accepted_inventory, (2, 1))
        self.assertEqual(len(seen), 2)
        self.assertEqual(seen[0], ((1, 1), ((0,),)))
        self.assertEqual(seen[1], ((2, 1), ((),)))
        self.assertLess(outcome.accepted_original_objective,
                        outcome.current_original_objective)
        self.assertEqual(outcome.checked_integer_points, 2)
        zero_mass = q.Problem(
            (q.Station(1, 1, 1), q.Station(0, 0, 1)),
            (q.Vehicle((0,), 1, F(2), matrix),),
            F(1), F(1), F(1))
        status = c.run_composite_oracle(
            zero_mass, (0, 0), lambda p, y, r: q.PhysicalEvidence(
                True, q.objective(p, y)))
        self.assertEqual(status.status, "no_gradient_at_zero")


if __name__ == "__main__":
    unittest.main()
