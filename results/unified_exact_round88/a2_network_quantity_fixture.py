"""Exact Fraction enumeration for the A2 three-station joint-quantity witness.

No optimizer, project binary, or external dependency is imported. Running this
file writes its deterministic expectation JSON beside the script.
"""

from fractions import Fraction as F
from functools import reduce
from itertools import product
from math import gcd
from pathlib import Path
import json


B = (4, 1, 4)                 # initial inventories
C = (4, 4, 6)                 # station capacities
D = (3, 3, 1)                 # positive targets
POSITIONS = (F(0), F(1, 10), F(1, 5), F(3, 10))
Q = 3
T = F(18, 5)                 # 3.6
CP = CD = F(1, 2)
LAMBDA = F(2)
CURRENT = (1, -1, 2)         # net pickups; every current visit is nonzero


def inventories(u):
    return tuple(b - x for b, x in zip(B, u))


def quantities(u):
    pickups = tuple(max(x, 0) for x in u)
    drops = tuple(max(-x, 0) for x in u)
    load = 0
    prefixes = []
    for x in u:
        load += x
        prefixes.append(load)
    return pickups, drops, tuple(prefixes)


def travel_after_deleting_zero_visits(u):
    nodes = (0,) + tuple(i + 1 for i, x in enumerate(u) if x) + (0,)
    return sum((abs(POSITIONS[j] - POSITIONS[i])
                for i, j in zip(nodes, nodes[1:])), F(0))


def network_feasible(u):
    if any(not 0 <= y <= cap for y, cap in zip(inventories(u), C)):
        return False
    pickups, _, prefixes = quantities(u)
    return all(0 <= load <= Q for load in prefixes) and sum(pickups) <= 3


def physically_feasible(u):
    if any(not 0 <= y <= cap for y, cap in zip(inventories(u), C)):
        return False
    pickups, drops, prefixes = quantities(u)
    if not all(0 <= load <= Q for load in prefixes):
        return False
    # Evaluator.cpp: pickup, station drop, plus loaded depot return.
    service = CP * sum(pickups) + CD * sum(drops) + CD * prefixes[-1]
    assert service == (CP + CD) * sum(pickups)
    return travel_after_deleting_zero_visits(u) + service <= T


def objective(u):
    ratios = tuple(F(y, d) for y, d in zip(inventories(u), D))
    s = sum(ratios, F(0))
    h = sum((abs(ratios[i] - ratios[j])
             for i in range(3) for j in range(i + 1, 3)), F(0))
    penalty = sum((abs(r - 1) for r in ratios), F(0))
    return (h / (3 * s) if s else F(0)) + LAMBDA * penalty


def sign(x):
    return (x > 0) - (x < 0)


def gradient(u):
    ratios = tuple(F(y, d) for y, d in zip(inventories(u), D))
    s = sum(ratios, F(0))
    assert s > 0
    h = sum((abs(ratios[i] - ratios[j])
             for i in range(3) for j in range(i + 1, 3)), F(0))
    return tuple(
        (s * sum(sign(ratios[i] - ratios[j]) for j in range(3) if j != i) - h)
        / (3 * s * s * D[i])
        + LAMBDA * sign(ratios[i] - 1) / D[i]
        for i in range(3)
    )


def is_round75_single_or_pair_neighbor(u):
    delta = tuple(x - y for x, y in zip(u, CURRENT))
    nonzero = sum(x != 0 for x in delta)
    return nonzero == 1 or (nonzero == 2 and sum(delta) == 0)


def main():
    full_travel = travel_after_deleting_zero_visits(CURRENT)
    assert full_travel == F(3, 5)
    assert (T - full_travel) / (CP + CD) == 3
    universe = tuple(product(*(range(-(cap - b), b + 1)
                               for b, cap in zip(B, C))))
    states = tuple(u for u in universe if network_feasible(u))
    physical = tuple(u for u in universe if physically_feasible(u))
    assert states == physical, "metric deletion / integer service budget mismatch"
    assert len(states) == 40 and CURRENT in states

    neighbors = tuple(u for u in states if is_round75_single_or_pair_neighbor(u))
    assert len(neighbors) == 8
    minimum_neighbor = min(neighbors, key=lambda u: (objective(u), u))
    assert minimum_neighbor == (1, 0, 2)
    assert objective(CURRENT) == F(32, 11)
    assert objective(minimum_neighbor) == F(11, 3)

    weights = gradient(CURRENT)
    assert weights == (F(-8, 363), F(-272, 363), F(256, 121))
    linear_cost = lambda u: sum((g * (y - y0) for g, y, y0 in zip(
        weights, inventories(u), inventories(CURRENT))), F(0))
    best_cost = min(map(linear_cost, states))
    linear_minimizers = tuple(u for u in states if linear_cost(u) == best_cost)
    assert linear_minimizers == ((0, 0, 3),)
    oracle = linear_minimizers[0]
    direction = tuple(y - y0 for y, y0 in zip(inventories(oracle),
                                               inventories(CURRENT)))
    steps = reduce(gcd, (abs(x) for x in direction))
    assert steps == 1
    line = tuple(tuple(y0 + t * dy // steps for y0, dy in zip(
        inventories(CURRENT), direction)) for t in range(steps + 1))
    assert line == (inventories(CURRENT), inventories(oracle))
    assert objective(oracle) == F(9, 4) < objective(CURRENT)
    assert travel_after_deleting_zero_visits(oracle) == F(3, 5)

    result = {
        "schema": "round88-a2-exact-three-station-quantity-fixture-v1",
        "enumeration": "all integer net operations within stock bounds; exact Fraction prefix, pickup, travel and F",
        "enumerated_stock_domain_states": len(universe),
        "network_and_physical_state_sets_equal": states == physical,
        "network_feasible_states": len(states),
        "round75_single_or_pair_neighbors": len(neighbors),
        "current_net_operations": CURRENT,
        "current_inventory": inventories(CURRENT),
        "current_F": str(objective(CURRENT)),
        "best_round75_neighbor_net_operations": minimum_neighbor,
        "best_round75_neighbor_F": str(objective(minimum_neighbor)),
        "gradient": [str(x) for x in weights],
        "linear_oracle_unique_net_operations": oracle,
        "linear_oracle_F": str(objective(oracle)),
        "linear_oracle_cost_delta": str(best_cost),
        "primitive_gcd_steps": steps,
        "line_inventories": line,
        "full_template_travel": str(full_travel),
        "oracle_shortened_travel": str(travel_after_deleting_zero_visits(oracle)),
    }
    output = Path(__file__).with_name("a2_network_quantity_fixture_output.json")
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
