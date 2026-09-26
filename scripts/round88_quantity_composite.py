"""Research-only fixed-route flow with an exact convex inventory penalty.

The Gini ratio contributes one local generalized gradient. The full separable
absolute penalty stays in the integer arc costs. This module does not change
the frozen linear A2 oracle or its endpoint adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction as F
from math import lcm

import round88_quantity_flow as base


@dataclass(frozen=True)
class MarginalArc:
    station: int
    direction: str
    first_unit: int
    units: int
    rational_cost: F
    arc_id: int


@dataclass(frozen=True)
class StationProjection:
    station: int
    raw_pickup: int
    raw_drop: int
    canceled: int
    canonical_pickup: int
    canonical_drop: int
    final_inventory: int
    raw_cost_from_initial: F
    projected_cost_from_initial: F


@dataclass(frozen=True)
class CompositeCertificate:
    network: base.FlowCertificate
    gini_gradient: tuple[F, ...]
    marginal_arcs: tuple[MarginalArc, ...]
    projections: tuple[StationProjection, ...]
    raw_flow_cost_from_initial: F
    proxy_cost_from_initial: F


@dataclass(frozen=True)
class CompositeOutcome:
    status: str
    current_inventory: tuple[int, ...]
    proposal_inventory: tuple[int, ...] | None = None
    accepted_inventory: tuple[int, ...] | None = None
    gini_gradient: tuple[F, ...] | None = None
    proxy_delta_from_current: F | None = None
    certificate: CompositeCertificate | None = None
    primitive_steps: int = 0
    checked_integer_points: int = 0
    rejected_physical_points: int = 0
    current_original_objective: F | None = None
    accepted_original_objective: F | None = None


def gini_local_gradient(problem: base.Problem,
                        inventory: tuple[int, ...]) -> tuple[F, ...] | None:
    """One local generalized gradient of H/(n*S), tie signs fixed at zero."""
    ratios = tuple(F(y, station.target) for y, station in
                   zip(inventory, problem.stations))
    if len(ratios) != len(problem.stations):
        raise ValueError("inventory dimension mismatch")
    mass = sum(ratios, F(0))
    if mass == 0:
        return None
    h = sum((abs(a - b) for i, a in enumerate(ratios)
             for b in ratios[i + 1:]), F(0))
    n = len(ratios)
    return tuple(
        (mass * sum((ratios[i] > ratios[j]) -
                    (ratios[i] < ratios[j]) for j in range(n) if j != i)
         - h) / (n * mass * mass * station.target)
        for i, station in enumerate(problem.stations))


def phi_value(gini_gradient: F, lambda_weight: F,
              target: F, inventory: int) -> F:
    if target <= 0 or lambda_weight < 0:
        raise ValueError("invalid target or penalty")
    return F(gini_gradient) * inventory + F(lambda_weight) * abs(
        F(inventory, 1) / target - 1)


def marginal_segments(initial: int, capacity: int, target: F,
                      gradient: F, lambda_weight: F,
                      direction: str) -> tuple[tuple[int, int, F], ...]:
    """(first unit, length, cost) for contiguous equal marginal units."""
    if (not isinstance(initial, int) or isinstance(initial, bool) or
            not isinstance(capacity, int) or isinstance(capacity, bool) or
            not 0 <= initial <= capacity or direction not in
            ("pickup", "drop")):
        raise ValueError("invalid marginal domain")
    limit = initial if direction == "pickup" else capacity - initial
    costs = []
    for unit in range(1, limit + 1):
        if direction == "pickup":
            cost = (phi_value(gradient, lambda_weight, target,
                              initial - unit) -
                    phi_value(gradient, lambda_weight, target,
                              initial - unit + 1))
        else:
            cost = (phi_value(gradient, lambda_weight, target,
                              initial + unit) -
                    phi_value(gradient, lambda_weight, target,
                              initial + unit - 1))
        if costs and cost < costs[-1]:
            raise AssertionError("convex marginal ordering violated")
        costs.append(cost)
    segments: list[tuple[int, int, F]] = []
    for unit, cost in enumerate(costs, 1):
        if segments and segments[-1][2] == cost:
            start, count, old = segments[-1]
            segments[-1] = start, count + 1, old
        else:
            segments.append((unit, 1, cost))
    return tuple(segments)


def proxy_increment(problem: base.Problem,
                    gradient: tuple[F, ...],
                    inventory: tuple[int, ...]) -> F:
    if len(gradient) != len(problem.stations) or len(inventory) != len(gradient):
        raise ValueError("proxy dimension mismatch")
    return sum((
        phi_value(gradient[i], F(problem.penalty_weight) * F(s.weight),
                  F(s.target), inventory[i]) -
        phi_value(gradient[i], F(problem.penalty_weight) * F(s.weight),
                  F(s.target), s.initial)
        for i, s in enumerate(problem.stations)), F(0))


def _prefix_flow(network: base.MinCostCirculation,
                 arcs: tuple[MarginalArc, ...]) -> int:
    used = 0
    partial = False
    for arc in arcs:
        amount = network.flow(arc.arc_id)
        if partial and amount:
            raise AssertionError("noncanonical marginal prefix")
        if not 0 <= amount <= arc.units:
            raise AssertionError("marginal flow out of bounds")
        used += amount
        if amount < arc.units:
            partial = True
    return used


def composite_oracle(
        problem: base.Problem, gradient: tuple[F, ...],
        budgets: tuple[int, ...]
        ) -> tuple[tuple[int, ...], CompositeCertificate]:
    """Exact integer minimum of the fixed-template composite proxy."""
    base.validate_problem(problem)
    if (len(gradient) != len(problem.stations) or
            len(budgets) != len(problem.vehicles) or
            any(not isinstance(k, int) or isinstance(k, bool) or k < 0
                for k in budgets)):
        raise ValueError("composite oracle dimension or budget")
    visited = {i for vehicle in problem.vehicles for i in vehicle.visits}
    station_segments = {}
    for i in visited:
        station = problem.stations[i]
        target = F(station.target)
        lambda_weight = F(problem.penalty_weight) * F(station.weight)
        station_segments[i] = (
            marginal_segments(station.initial, station.capacity, target,
                              gradient[i], lambda_weight, "pickup"),
            marginal_segments(station.initial, station.capacity, target,
                              gradient[i], lambda_weight, "drop"))
    all_costs = [segment[2] for pair in station_segments.values()
                 for direction in pair for segment in direction]
    scale = lcm(*(cost.denominator for cost in all_costs))
    visits = sum(len(vehicle.visits) for vehicle in problem.vehicles)
    network = base.MinCostCirculation(2 + len(problem.vehicles) + visits)
    source, disposal = 0, 1
    next_visit_node = 2 + len(problem.vehicles)
    marginal_arcs: list[MarginalArc] = []
    pickup_arcs: dict[int, tuple[MarginalArc, ...]] = {}
    drop_arcs: dict[int, tuple[MarginalArc, ...]] = {}
    for k, (vehicle, budget) in enumerate(zip(problem.vehicles, budgets)):
        vehicle_node = 2 + k
        network.add_arc(source, vehicle_node, budget, 0)
        nodes = tuple(range(next_visit_node,
                            next_visit_node + len(vehicle.visits)))
        next_visit_node += len(nodes)
        for position, (station_index, node) in enumerate(
                zip(vehicle.visits, nodes)):
            pickup_specs, drop_specs = station_segments[station_index]
            p_arcs = []
            d_arcs = []
            for first_unit, units, cost in pickup_specs:
                arc_id = network.add_arc(vehicle_node, node, units,
                                         int(cost * scale))
                arc = MarginalArc(station_index, "pickup", first_unit,
                                  units, cost, arc_id)
                marginal_arcs.append(arc)
                p_arcs.append(arc)
            for first_unit, units, cost in drop_specs:
                arc_id = network.add_arc(node, disposal, units,
                                         int(cost * scale))
                arc = MarginalArc(station_index, "drop", first_unit,
                                  units, cost, arc_id)
                marginal_arcs.append(arc)
                d_arcs.append(arc)
            pickup_arcs[station_index] = tuple(p_arcs)
            drop_arcs[station_index] = tuple(d_arcs)
            following = (nodes[position + 1]
                         if position + 1 < len(nodes) else disposal)
            network.add_arc(node, following, vehicle.capacity, 0)
    network.add_arc(disposal, source,
                    sum(problem.stations[i].initial for i in visited), 0)
    network_certificate = network.solve(scale)
    proposal = [station.initial for station in problem.stations]
    projections = []
    raw_total = F(0)
    for i, station in enumerate(problem.stations):
        pickup = _prefix_flow(network, pickup_arcs.get(i, ()))
        drop = _prefix_flow(network, drop_arcs.get(i, ()))
        canonical_pickup, canonical_drop, canceled = (
            base.cancel_same_station(pickup, drop))
        final = station.initial - canonical_pickup + canonical_drop
        if final != station.initial - pickup + drop:
            raise AssertionError("cancellation changed net inventory")
        proposal[i] = final
        lambda_weight = F(problem.penalty_weight) * F(station.weight)
        target = F(station.target)
        initial_phi = phi_value(gradient[i], lambda_weight,
                                target, station.initial)
        raw = (phi_value(gradient[i], lambda_weight, target,
                         station.initial - pickup) +
               phi_value(gradient[i], lambda_weight, target,
                         station.initial + drop) - 2 * initial_phi)
        arc_cost = sum((arc.rational_cost * network.flow(arc.arc_id)
                        for arc in pickup_arcs.get(i, ()) +
                        drop_arcs.get(i, ())), F(0))
        if raw != arc_cost:
            raise AssertionError("marginal prefix cost not telescoping")
        projected = phi_value(gradient[i], lambda_weight, target,
                              final) - initial_phi
        if projected > raw:
            raise AssertionError("same-station cancellation increased proxy")
        raw_total += raw
        projections.append(StationProjection(
            i, pickup, drop, canceled,
            canonical_pickup, canonical_drop, final, raw, projected))
    proposal_tuple = tuple(proposal)
    projected_total = proxy_increment(problem, gradient, proposal_tuple)
    if projected_total != sum((x.projected_cost_from_initial
                               for x in projections), F(0)):
        raise AssertionError("projected station costs disagree")
    if network_certificate.integer_flow_cost != raw_total * scale:
        raise AssertionError("network integer cost not raw phi from initial")
    if projected_total > raw_total:
        raise AssertionError("projection exceeds certified network value")
    if not base.in_nominal_network_domain(problem, proposal_tuple, budgets):
        raise AssertionError("canceled flow outside fixed network domain")
    # If a cancellation lowers cost strictly, the raw flow was not optimal.
    if projected_total != raw_total:
        raise AssertionError("optimal flow has strictly improvable cancellation")
    return proposal_tuple, CompositeCertificate(
        network_certificate, tuple(gradient), tuple(marginal_arcs),
        tuple(projections), raw_total, projected_total)


def run_composite_oracle(
        problem: base.Problem, current: tuple[int, ...],
        original_verifier: base.OriginalVerifier) -> CompositeOutcome:
    """One complete proxy proposal and all primitive-line original checks."""
    base.validate_problem(problem)
    current = tuple(current)
    try:
        budgets = base.nominal_budgets(problem)
        base.validate_current(problem, current, budgets)
    except base.QuantityDomainError as error:
        return CompositeOutcome(error.code, current)
    if not base.exact_physical_feasible(problem, current):
        return CompositeOutcome("domain_rejected_current_physical", current)
    current_evidence = original_verifier(
        problem, current, base.shortened_routes(problem, current))
    if not current_evidence.feasible:
        return CompositeOutcome("domain_rejected_original_witness", current)
    gradient = gini_local_gradient(problem, current)
    if gradient is None:
        return CompositeOutcome(
            "no_gradient_at_zero", current,
            current_original_objective=current_evidence.objective)
    proposal, certificate = composite_oracle(problem, gradient, budgets)
    line = base.primitive_segment(current, proposal)
    if any(not base.in_nominal_network_domain(problem, inventory, budgets)
           for inventory in line):
        raise AssertionError("primitive line left nominal network domain")
    delta = (proxy_increment(problem, gradient, proposal) -
             proxy_increment(problem, gradient, current))
    if len(line) == 1:
        return CompositeOutcome(
            "no_direction", current, proposal_inventory=proposal,
            gini_gradient=gradient, proxy_delta_from_current=delta,
            certificate=certificate,
            current_original_objective=current_evidence.objective)
    best_inventory = current
    best_evidence = current_evidence
    rejected = 0
    for inventory in line[1:]:
        if not base.exact_physical_feasible(problem, inventory):
            rejected += 1
            continue
        evidence = original_verifier(
            problem, inventory, base.shortened_routes(problem, inventory))
        if not evidence.feasible:
            rejected += 1
            continue
        if evidence.objective < best_evidence.objective:
            best_inventory, best_evidence = inventory, evidence
    improved = best_inventory != current
    return CompositeOutcome(
        "improved" if improved else "no_verified_improvement",
        current, proposal, best_inventory if improved else None,
        gradient, delta, certificate, len(line) - 1, len(line), rejected,
        current_evidence.objective,
        best_evidence.objective if improved else None)
