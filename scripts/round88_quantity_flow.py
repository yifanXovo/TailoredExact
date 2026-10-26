"""Round88 A2 fixed-route, exact-integer quantity oracle prototype.

This is an independent research model, not an ENS-C integration. All arithmetic
in the network, gradient, and objective is exact. An original-problem verifier
callback is required for accepting a move. No solver library or runtime budget
is used.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from functools import reduce
from math import gcd, lcm
from typing import Callable


F = Fraction
PHYSICAL_TOLERANCE = F(1, 10_000_000)  # Evaluator.cpp fixed 1e-7


@dataclass(frozen=True)
class Station:
    initial: int
    capacity: int
    target: int
    weight: F = F(1)


@dataclass(frozen=True)
class Vehicle:
    visits: tuple[int, ...]  # station indices; node zero in distances is depot
    capacity: int
    deadline: F
    distances: tuple[tuple[F, ...], ...]  # directed, vehicle-specific


@dataclass(frozen=True)
class Problem:
    stations: tuple[Station, ...]
    vehicles: tuple[Vehicle, ...]
    pickup_time: F
    drop_time: F
    penalty_weight: F


@dataclass(frozen=True)
class PhysicalEvidence:
    feasible: bool
    objective: F


OriginalVerifier = Callable[
    [Problem, tuple[int, ...], tuple[tuple[int, ...], ...]], PhysicalEvidence
]


@dataclass(frozen=True)
class FlowCertificate:
    integer_cost_scale: int
    integer_flow_cost: int
    potentials: tuple[int, ...]
    positive_residual_edges: int
    negative_cycle_augmentations: int
    # (tail, head, original capacity, integer cost, final integer flow)
    arc_flows: tuple[tuple[int, int, int, int, int], ...]


@dataclass(frozen=True)
class Outcome:
    status: str
    current_inventory: tuple[int, ...]
    proposal_inventory: tuple[int, ...] | None = None
    accepted_inventory: tuple[int, ...] | None = None
    gradient: tuple[F, ...] | None = None
    linear_delta: F | None = None
    certificate: FlowCertificate | None = None
    primitive_steps: int = 0
    checked_integer_points: int = 0
    rejected_physical_points: int = 0
    current_original_objective: F | None = None
    accepted_original_objective: F | None = None


class QuantityDomainError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _fraction(value: F | int | float) -> F:
    if isinstance(value, bool):
        raise ValueError("boolean is not a rational input")
    return F(value)


def validate_problem(problem: Problem) -> None:
    n = len(problem.stations)
    if n == 0 or not problem.vehicles:
        raise ValueError("stations and vehicles must be nonempty")
    for station in problem.stations:
        if (not isinstance(station.initial, int) or
                not isinstance(station.capacity, int) or
                not isinstance(station.target, int) or
                isinstance(station.initial, bool) or
                isinstance(station.capacity, bool) or
                isinstance(station.target, bool) or
                not 0 <= station.initial <= station.capacity or
                station.target <= 0 or _fraction(station.weight) < 0):
            raise ValueError("invalid station domain")
    if any(_fraction(x) < 0 for x in (problem.pickup_time,
                                      problem.drop_time,
                                      problem.penalty_weight)):
        raise ValueError("negative service or penalty")
    seen: set[int] = set()
    for vehicle in problem.vehicles:
        if (not isinstance(vehicle.capacity, int) or
                isinstance(vehicle.capacity, bool) or vehicle.capacity < 0 or
                _fraction(vehicle.deadline) < 0):
            raise ValueError("invalid vehicle capacity or deadline")
        if len(vehicle.distances) != n + 1 or any(
                len(row) != n + 1 for row in vehicle.distances):
            raise ValueError("distance matrix dimension")
        if any(_fraction(d) < 0 for row in vehicle.distances for d in row):
            raise ValueError("negative travel")
        for station in vehicle.visits:
            if not isinstance(station, int) or isinstance(station, bool):
                raise ValueError("noninteger visit")
            if not 0 <= station < n or station in seen:
                raise ValueError("station missing/out of range or revisited")
            seen.add(station)


def route_travel(vehicle: Vehicle, visits: tuple[int, ...]) -> F:
    if not visits:
        return F(0)
    nodes = (0,) + tuple(i + 1 for i in visits) + (0,)
    return sum((_fraction(vehicle.distances[a][b])
                for a, b in zip(nodes, nodes[1:])), F(0))


def nominal_budgets(problem: Problem) -> tuple[int, ...]:
    service = _fraction(problem.pickup_time) + _fraction(problem.drop_time)
    budgets = []
    for vehicle in problem.vehicles:
        travel = route_travel(vehicle, vehicle.visits)
        if travel > _fraction(vehicle.deadline):
            raise QuantityDomainError("domain_rejected_full_template_time")
        stock = sum(problem.stations[i].initial for i in vehicle.visits)
        if service == 0:
            budgets.append(stock)
        else:
            budgets.append(min(stock, int((_fraction(vehicle.deadline) -
                                           travel) // service)))
    return tuple(budgets)


def _net(problem: Problem, inventory: tuple[int, ...], station: int) -> int:
    return problem.stations[station].initial - inventory[station]


def validate_current(problem: Problem, inventory: tuple[int, ...],
                     budgets: tuple[int, ...]) -> None:
    if len(inventory) != len(problem.stations) or any(
            not isinstance(y, int) or isinstance(y, bool) or
            not 0 <= y <= station.capacity
            for y, station in zip(inventory, problem.stations)):
        raise QuantityDomainError("domain_rejected_inventory")
    visited = {i for vehicle in problem.vehicles for i in vehicle.visits}
    if any(inventory[i] != station.initial for i, station in
           enumerate(problem.stations) if i not in visited):
        raise QuantityDomainError("domain_rejected_unvisited_inventory")
    for vehicle, budget in zip(problem.vehicles, budgets):
        load = pickup = 0
        for i in vehicle.visits:
            net = _net(problem, inventory, i)
            if net == 0:
                raise QuantityDomainError("domain_rejected_current_zero_visit")
            pickup += max(net, 0)
            load += net
            if not 0 <= load <= vehicle.capacity:
                raise QuantityDomainError("domain_rejected_current_prefix")
        if pickup > budget:
            raise QuantityDomainError("domain_rejected_current_budget")


def in_nominal_network_domain(problem: Problem, inventory: tuple[int, ...],
                              budgets: tuple[int, ...]) -> bool:
    """Quantity-set check, allowing visits that become zero and get deleted."""
    if len(inventory) != len(problem.stations) or any(
            not isinstance(y, int) or isinstance(y, bool) or
            not 0 <= y <= station.capacity
            for y, station in zip(inventory, problem.stations)):
        return False
    visited = {i for vehicle in problem.vehicles for i in vehicle.visits}
    if any(inventory[i] != station.initial for i, station in
           enumerate(problem.stations) if i not in visited):
        return False
    for vehicle, budget in zip(problem.vehicles, budgets):
        carried = pickups = 0
        for i in vehicle.visits:
            u = _net(problem, inventory, i)
            carried += u
            pickups += max(u, 0)
            if not 0 <= carried <= vehicle.capacity:
                return False
        if pickups > budget:
            return False
    return True


def shortened_routes(problem: Problem, inventory: tuple[int, ...]
                     ) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(i for i in vehicle.visits
                       if _net(problem, inventory, i) != 0)
                 for vehicle in problem.vehicles)


def exact_physical_feasible(problem: Problem,
                            inventory: tuple[int, ...]) -> bool:
    """Independent internal gate; original verifier is still required."""
    if len(inventory) != len(problem.stations) or any(
            not isinstance(y, int) or not 0 <= y <= s.capacity
            for y, s in zip(inventory, problem.stations)):
        return False
    visited = {i for v in problem.vehicles for i in v.visits}
    if any(inventory[i] != s.initial for i, s in
           enumerate(problem.stations) if i not in visited):
        return False
    for vehicle, route in zip(problem.vehicles,
                              shortened_routes(problem, inventory)):
        load = pickups = drops = 0
        for i in route:
            u = _net(problem, inventory, i)
            pickups += max(u, 0)
            drops += max(-u, 0)
            load += u
            if not 0 <= load <= vehicle.capacity:
                return False
        service = (_fraction(problem.pickup_time) * pickups +
                   _fraction(problem.drop_time) * (drops + load))
        if service != (_fraction(problem.pickup_time) +
                       _fraction(problem.drop_time)) * pickups:
            raise AssertionError("loaded-return conservation")
        if (route_travel(vehicle, route) + service >
                _fraction(vehicle.deadline) +
                PHYSICAL_TOLERANCE):
            return False
    return True


def objective(problem: Problem, inventory: tuple[int, ...]) -> F:
    ratios = tuple(F(y, station.target) for y, station in
                   zip(inventory, problem.stations))
    total = sum(ratios, F(0))
    pair_sum = sum((abs(a - b) for i, a in enumerate(ratios)
                    for b in ratios[i + 1:]), F(0))
    penalty = sum((_fraction(station.weight) * abs(r - 1)
                   for station, r in zip(problem.stations, ratios)), F(0))
    gini = pair_sum / (len(ratios) * total) if total else F(0)
    return gini + _fraction(problem.penalty_weight) * penalty


def gradient(problem: Problem,
             inventory: tuple[int, ...]) -> tuple[F, ...] | None:
    ratios = tuple(F(y, station.target) for y, station in
                   zip(inventory, problem.stations))
    total = sum(ratios, F(0))
    if total == 0:
        return None
    pair_sum = sum((abs(a - b) for i, a in enumerate(ratios)
                    for b in ratios[i + 1:]), F(0))
    n = len(ratios)

    def sign(x: F) -> int:
        return (x > 0) - (x < 0)

    return tuple(
        (total * sum(sign(ratios[i] - ratios[j])
                     for j in range(n) if j != i) - pair_sum) /
        (n * total * total * station.target) +
        _fraction(problem.penalty_weight) * _fraction(station.weight) *
        sign(ratios[i] - 1) / station.target
        for i, station in enumerate(problem.stations)
    )


@dataclass
class _ResidualEdge:
    to: int
    reverse: int
    capacity: int
    cost: int


class MinCostCirculation:
    """Integer residual negative-cycle cancellation with dual certificate."""

    def __init__(self, nodes: int):
        if nodes <= 0:
            raise ValueError("empty network")
        self.adj: list[list[_ResidualEdge]] = [[] for _ in range(nodes)]
        self.forward: list[tuple[int, int, int]] = []

    def add_arc(self, start: int, end: int, capacity: int,
                cost: int) -> int:
        if (not 0 <= start < len(self.adj) or
                not 0 <= end < len(self.adj) or start == end or
                not isinstance(capacity, int) or
                isinstance(capacity, bool) or capacity < 0 or
                not isinstance(cost, int) or isinstance(cost, bool)):
            raise ValueError("invalid arc")
        forward_index = len(self.adj[start])
        reverse_index = len(self.adj[end])
        self.adj[start].append(_ResidualEdge(end, reverse_index,
                                             capacity, cost))
        self.adj[end].append(_ResidualEdge(start, forward_index, 0, -cost))
        self.forward.append((start, forward_index, capacity))
        return len(self.forward) - 1

    def flow(self, arc_id: int) -> int:
        start, index, original_capacity = self.forward[arc_id]
        return original_capacity - self.adj[start][index].capacity

    def _bellman_ford(self) -> tuple[list[int], list[tuple[int, int] | None],
                                     int | None]:
        count = len(self.adj)
        potential = [0] * count  # implicit zero-cost super-source
        predecessor: list[tuple[int, int] | None] = [None] * count
        changed: int | None = None
        for _ in range(count):
            changed = None
            for u, row in enumerate(self.adj):
                for edge_index, edge in enumerate(row):
                    if edge.capacity <= 0:
                        continue
                    candidate = potential[u] + edge.cost
                    if candidate < potential[edge.to]:
                        potential[edge.to] = candidate
                        predecessor[edge.to] = (u, edge_index)
                        changed = edge.to
            if changed is None:
                break
        return potential, predecessor, changed

    def solve(self, scale: int = 1) -> FlowCertificate:
        if scale <= 0:
            raise ValueError("nonpositive cost scale")
        augmentations = 0
        while True:
            potentials, predecessor, changed = self._bellman_ford()
            if changed is None:
                break
            cursor = changed
            for _ in self.adj:
                previous = predecessor[cursor]
                if previous is None:
                    raise AssertionError("negative-cycle predecessor missing")
                cursor = previous[0]
            cycle_start = cursor
            cycle: list[tuple[int, int]] = []
            while True:
                previous = predecessor[cursor]
                if previous is None:
                    raise AssertionError("negative-cycle reconstruction")
                cycle.append(previous)
                cursor = previous[0]
                if cursor == cycle_start:
                    break
            cycle.reverse()
            delta = min(self.adj[u][idx].capacity for u, idx in cycle)
            cycle_cost = sum(self.adj[u][idx].cost for u, idx in cycle)
            if delta <= 0 or cycle_cost >= 0:
                raise AssertionError("invalid negative cycle")
            for u, idx in cycle:
                edge = self.adj[u][idx]
                edge.capacity -= delta
                self.adj[edge.to][edge.reverse].capacity += delta
            augmentations += 1

        residual_edges = 0
        for u, row in enumerate(self.adj):
            for edge in row:
                if edge.capacity > 0:
                    residual_edges += 1
                    if edge.cost + potentials[u] - potentials[edge.to] < 0:
                        raise AssertionError("negative reduced-cost residual arc")
        balance = [0] * len(self.adj)
        total_cost = 0
        arc_flows = []
        for start, idx, original_capacity in self.forward:
            edge = self.adj[start][idx]
            flow = original_capacity - edge.capacity
            if not 0 <= flow <= original_capacity:
                raise AssertionError("nonintegral or unbounded flow")
            balance[start] -= flow
            balance[edge.to] += flow
            total_cost += flow * edge.cost
            arc_flows.append((start, edge.to, original_capacity,
                              edge.cost, flow))
        if any(balance):
            raise AssertionError("flow conservation")
        return FlowCertificate(scale, total_cost, tuple(potentials),
                               residual_edges, augmentations,
                               tuple(arc_flows))


def cancel_same_station(pickups: int, drops: int) -> tuple[int, int, int]:
    if (not isinstance(pickups, int) or isinstance(pickups, bool) or
            not isinstance(drops, int) or isinstance(drops, bool) or
            min(pickups, drops) < 0):
        raise ValueError("operations must be nonnegative integers")
    canceled = min(pickups, drops)
    return pickups - canceled, drops - canceled, canceled


def _linear_oracle(problem: Problem, weights: tuple[F, ...],
                   budgets: tuple[int, ...]
                   ) -> tuple[tuple[int, ...], FlowCertificate]:
    scale = lcm(*(weight.denominator for weight in weights))
    integer_weights = tuple(int(weight * scale) for weight in weights)
    visits = sum(len(v.visits) for v in problem.vehicles)
    network = MinCostCirculation(2 + len(problem.vehicles) + visits)
    source, disposal = 0, 1
    next_visit_node = 2 + len(problem.vehicles)
    pickups: dict[int, int] = {}
    drops: dict[int, int] = {}
    for k, (vehicle, budget) in enumerate(zip(problem.vehicles, budgets)):
        vehicle_node = 2 + k
        network.add_arc(source, vehicle_node, budget, 0)
        nodes = tuple(range(next_visit_node,
                            next_visit_node + len(vehicle.visits)))
        next_visit_node += len(nodes)
        for position, (station_index, node) in enumerate(
                zip(vehicle.visits, nodes)):
            station = problem.stations[station_index]
            pickups[station_index] = network.add_arc(
                vehicle_node, node, station.initial,
                -integer_weights[station_index])
            drops[station_index] = network.add_arc(
                node, disposal, station.capacity - station.initial,
                integer_weights[station_index])
            following = (nodes[position + 1]
                         if position + 1 < len(nodes) else disposal)
            network.add_arc(node, following, vehicle.capacity, 0)
    network.add_arc(disposal, source,
                    sum(problem.stations[i].initial for i in pickups), 0)
    certificate = network.solve(scale)
    inventory = [station.initial for station in problem.stations]
    for i in pickups:
        pickup, drop, _ = cancel_same_station(
            network.flow(pickups[i]), network.flow(drops[i]))
        inventory[i] = problem.stations[i].initial - pickup + drop
    proposal = tuple(inventory)
    expected = sum((weights[i] *
                    (proposal[i] - problem.stations[i].initial)
                    for i in range(len(inventory))), F(0))
    if certificate.integer_flow_cost != expected * scale:
        raise AssertionError("projection changed linear objective")
    return proposal, certificate


def primitive_segment(start: tuple[int, ...],
                      end: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    if len(start) != len(end):
        raise ValueError("inventory dimension mismatch")
    difference = tuple(b - a for a, b in zip(start, end))
    steps = reduce(gcd, (abs(value) for value in difference), 0)
    if steps == 0:
        return (start,)
    direction = tuple(value // steps for value in difference)
    return tuple(tuple(a + t * d for a, d in zip(start, direction))
                 for t in range(steps + 1))


def run_quantity_oracle(problem: Problem, current: tuple[int, ...],
                        original_verifier: OriginalVerifier) -> Outcome:
    """One exact linear proposal and exhaustive primitive integer line.

    A strict original-verifier F decrease is required. No-improvement and
    zero-gradient statuses are heuristic outcomes, never optimality claims.
    """
    validate_problem(problem)
    current = tuple(current)
    try:
        budgets = nominal_budgets(problem)
        validate_current(problem, current, budgets)
    except QuantityDomainError as error:
        return Outcome(error.code, current)
    if not exact_physical_feasible(problem, current):
        return Outcome("domain_rejected_current_physical", current)
    current_evidence = original_verifier(
        problem, current, shortened_routes(problem, current))
    if not current_evidence.feasible:
        return Outcome("domain_rejected_original_witness", current)
    weights = gradient(problem, current)
    if weights is None:
        return Outcome("no_gradient_at_zero", current,
                       current_original_objective=current_evidence.objective)
    proposal, certificate = _linear_oracle(problem, weights, budgets)
    if not in_nominal_network_domain(problem, proposal, budgets):
        raise AssertionError("integer circulation projected outside nominal domain")
    delta = sum((weight * (a - b) for weight, a, b in
                 zip(weights, proposal, current)), F(0))
    line = primitive_segment(current, proposal)
    if any(not in_nominal_network_domain(problem, y, budgets) for y in line):
        raise AssertionError("primitive line left nominal network domain")
    if len(line) == 1:
        return Outcome("no_direction", current, proposal_inventory=proposal,
                       gradient=weights, linear_delta=delta,
                       certificate=certificate,
                       current_original_objective=current_evidence.objective)

    best_inventory = current
    best_objective = current_evidence.objective
    rejected = 0
    for inventory in line[1:]:
        if not exact_physical_feasible(problem, inventory):
            rejected += 1
            continue
        evidence = original_verifier(problem, inventory,
                                     shortened_routes(problem, inventory))
        if not evidence.feasible:
            rejected += 1
            continue
        if evidence.objective < best_objective:
            best_objective = evidence.objective
            best_inventory = inventory
    improved = best_inventory != current
    return Outcome(
        "improved" if improved else "no_verified_improvement",
        current, proposal, best_inventory if improved else None,
        weights, delta, certificate, len(line) - 1, len(line), rejected,
        current_evidence.objective,
        best_objective if improved else None,
    )
