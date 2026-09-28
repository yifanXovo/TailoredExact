"""Independent, solver-free rational micro oracle for the R93 co-quantity line.

This models the mathematical route/stock/objective convention directly. It is
not a binary64 replica of Evaluator.cpp and is never a production witness.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from fractions import Fraction as F
from pathlib import Path


TOL = F(1, 10_000_000)
IMPROVEMENT = F(1, 1_000_000_000_000)


def q(value: str | int) -> F:
    return F(value)


@dataclass(frozen=True)
class Case:
    name: str
    initial: tuple[int, ...]
    capacity: tuple[int, ...]
    target: tuple[int, ...]
    weights: tuple[F, ...]
    vehicle_capacity: tuple[int, ...]
    routes: tuple[tuple[tuple[int, int], ...], ...]  # station, pickup-minus-drop
    dist: tuple[tuple[F, ...], ...]
    pickup_time: F
    drop_time: F
    horizon: F
    lam: F = F(3, 20)
    pair: tuple[int, int] = (1, 2)


def matrix(n: int, value: str = "0") -> tuple[tuple[F, ...], ...]:
    return tuple(tuple(F(0) if i == j else q(value) for j in range(n + 1))
                 for i in range(n + 1))


def evaluate(case: Case, routes: tuple[tuple[tuple[int, int], ...], ...]) -> dict:
    n = len(case.initial)
    assert n == len(case.target) == len(case.capacity) == len(case.weights)
    assert len(routes) == len(case.vehicle_capacity)
    assert len(case.dist) == n + 1 and all(len(row) == n + 1 for row in case.dist)
    assert all(d > 0 for d in case.target)
    inventory = list(case.initial)
    seen: set[int] = set()
    durations: list[F] = []
    for k, route in enumerate(routes):
        previous = 0
        travel = F(0)
        load = 0
        pickups = 0
        station_drops = 0
        for station, op in route:
            if station < 1 or station > n or station in seen or op == 0:
                return {"feasible": False, "reason": "invalid_visit_or_operation"}
            seen.add(station)
            travel += case.dist[previous][station]
            previous = station
            load += op
            pickups += max(op, 0)
            station_drops += max(-op, 0)
            inventory[station - 1] -= op
            if load < 0 or load > case.vehicle_capacity[k]:
                return {"feasible": False, "reason": "prefix_load"}
        travel += case.dist[previous][0]
        # The final positive load is unloaded at the depot.
        duration = (travel + case.pickup_time * pickups
                    + case.drop_time * station_drops + case.drop_time * load)
        durations.append(duration)
        if duration > case.horizon + TOL:
            return {"feasible": False, "reason": "duration"}
    if any(y < 0 or y > c for y, c in zip(inventory, case.capacity)):
        return {"feasible": False, "reason": "station_stock"}
    ratios = [F(y, d) for y, d in zip(inventory, case.target)]
    mass = sum(ratios, F(0))
    spread = sum((abs(ratios[i] - ratios[j])
                  for i in range(n) for j in range(i + 1, n)), F(0))
    gini = spread / (n * mass) if mass > 0 else F(0)
    penalty = sum((w * abs(r - 1) for w, r in zip(case.weights, ratios)), F(0))
    return {"feasible": True, "reason": "valid", "inventory": tuple(inventory),
            "mass": mass, "spread": spread, "gini": gini, "penalty": penalty,
            "objective": gini + case.lam * penalty,
            "durations": tuple(durations)}


def replace_operations(case: Case, changes: dict[int, int]):
    """Rebuild the original route order, deleting every newly zero operation."""
    return tuple(tuple((station, changes.get(station, op))
                       for station, op in route if changes.get(station, op) != 0)
                 for route in case.routes)


def operation(case: Case, station: int) -> int:
    matches = [op for route in case.routes for i, op in route if i == station]
    assert len(matches) == 1
    return matches[0]


def pair_line(case: Case):
    base = evaluate(case, case.routes)
    assert base["feasible"]
    a, b = case.pair
    ya, yb = base["inventory"][a - 1], base["inventory"][b - 1]
    lower = max(-ya, -yb)
    upper = min(case.capacity[a - 1] - ya, case.capacity[b - 1] - yb)
    rows = []
    best = (base["objective"], 0)
    for t in range(lower, upper + 1):
        changed = {a: operation(case, a) - t, b: operation(case, b) - t}
        trial = evaluate(case, replace_operations(case, changed))
        rows.append({"t": t, **trial})
        if trial["feasible"] and base["objective"] - trial["objective"] > IMPROVEMENT:
            if trial["objective"] < best[0] or (trial["objective"] == best[0] and t < best[1]):
                best = (trial["objective"], t)
    return {"base": base, "bounds": (lower, upper), "rows": rows,
            "best_t": best[1], "best_objective": best[0]}


def old_single_transfer_neighborhood(case: Case):
    """Independent mathematical enumeration of R75's single/transfer shapes."""
    base = evaluate(case, case.routes)
    assert base["feasible"]
    a, b = case.pair
    stocks = base["inventory"]
    rows = []
    for station in (a, b):
        for new_y in range(case.capacity[station - 1] + 1):
            if new_y == stocks[station - 1]:
                continue
            new_op = case.initial[station - 1] - new_y
            trial = evaluate(case, replace_operations(case, {station: new_op}))
            rows.append({"kind": "single", "station": station,
                         "new_inventory": new_y, **trial})
    for new_a in range(case.capacity[a - 1] + 1):
        delta = new_a - stocks[a - 1]
        if delta == 0:
            continue
        new_b = stocks[b - 1] - delta
        if not (0 <= new_b <= case.capacity[b - 1]):
            continue
        trial = evaluate(case, replace_operations(case, {
            a: case.initial[a - 1] - new_a,
            b: case.initial[b - 1] - new_b}))
        rows.append({"kind": "transfer", "new_inventory": (new_a, new_b), **trial})
    feasible = [r for r in rows if r["feasible"]]
    return {"rows": rows, "feasible_count": len(feasible),
            "best_objective": min((r["objective"] for r in feasible),
                                  default=base["objective"])}


def make_cases() -> list[Case]:
    gap = Case("nonempty_gap", (3, 6), (6, 6), (4, 4), (F(1), F(1)),
               (5,), (((1, 1), (2, 4)),), matrix(2), F(0), F(0), F(1))
    positive = Case("positive_metric_gap", (3, 6), (6, 6), (4, 4),
                    (F(1), F(1)), (5,), (((1, 1), (2, 4)),),
                    matrix(2, "1/100"), F(1, 100), F(1, 100), F(1))
    zero_mass = Case("zero_mass", (1, 1), (2, 2), (1, 1), (F(1), F(1)),
                     (2,), (((1, 1), (2, 1)),), matrix(2), F(0), F(0), F(1))
    hetero = Case("heterogeneous_target_weight", (3, 3), (5, 5), (2, 4),
                  (F(2), F(1)), (3,), (((1, 1), (2, 1)),),
                  matrix(2, "1/100"), F(1, 100), F(1, 100), F(1))
    cross = Case("cross_vehicle_loaded_return", (2, 2), (3, 3), (2, 2),
                 (F(1), F(1)), (1, 1), (((1, 1),), ((2, 1),)),
                 matrix(2, "1/100"), F(1, 100), F(1, 100), F(1))
    flip = Case("sign_flip", (3, 2, 2), (3, 4, 4), (3, 2, 2),
                (F(1), F(1), F(1)), (5,), (((1, 3), (2, 1), (3, 1)),),
                matrix(3, "1/100"), F(1, 100), F(1, 100), F(1),
                pair=(2, 3))
    nonmetric_dist = ((F(0), F(1), F(100)), (F(1), F(0), F(1)),
                      (F(1), F(1), F(0)))
    nonmetric = Case("nonmetric_zero_deletion", (2, 2), (3, 3), (2, 2),
                     (F(1), F(1)), (3,), (((1, 1), (2, 2)),),
                     nonmetric_dist, F(0), F(0), F(10))
    exact = Case("physical_tolerance_equal", (2, 2), (3, 3), (2, 2),
                 (F(1), F(1)), (4,), (((1, 1), (2, 1)),), matrix(2),
                 F(1, 80_000_000), F(1, 80_000_000), F(0))
    outside = Case("physical_tolerance_exceeded", (2, 2), (3, 3), (2, 2),
                   (F(1), F(1)), (4,), (((1, 1), (2, 1)),), matrix(2),
                   F(3, 200_000_000), F(3, 200_000_000), F(0))
    return [gap, positive, zero_mass, hetero, cross, flip, nonmetric, exact, outside]


def serial(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, tuple):
        return [serial(x) for x in value]
    if isinstance(value, list):
        return [serial(x) for x in value]
    if isinstance(value, dict):
        return {str(k): serial(v) for k, v in value.items()}
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    reports = {}
    for case in make_cases():
        line = pair_line(case)
        reports[case.name] = line
        assert line["base"]["feasible"]
    gap = reports["nonempty_gap"]
    assert gap["base"]["objective"] == F(3, 20)
    assert gap["best_t"] == 1 and gap["best_objective"] == F(3, 40)
    assert next(r for r in gap["rows"] if r["t"] == 1)["inventory"] == (3, 3)
    old = old_single_transfer_neighborhood(make_cases()[0])
    assert old["best_objective"] == F(17, 80)  # 0.2125, no old strict improvement
    assert old["best_objective"] > gap["base"]["objective"]
    assert reports["positive_metric_gap"]["best_t"] == 1
    assert reports["zero_mass"]["base"]["mass"] == 0
    assert reports["zero_mass"]["base"]["gini"] == 0
    assert reports["zero_mass"]["best_t"] == 1
    assert reports["heterogeneous_target_weight"]["base"]["objective"] == F(29, 120)
    assert reports["cross_vehicle_loaded_return"]["base"]["durations"] == (F(1, 25), F(1, 25))
    assert reports["cross_vehicle_loaded_return"]["best_t"] == 1
    flip = next(r for r in reports["sign_flip"]["rows"] if r["t"] == 2)
    assert flip["feasible"] and flip["inventory"] == (0, 3, 3)
    deleted = next(r for r in reports["nonmetric_zero_deletion"]["rows"] if r["t"] == 1)
    assert not deleted["feasible"] and deleted["reason"] == "duration"
    equal = next(r for r in reports["physical_tolerance_equal"]["rows"] if r["t"] == -1)
    exceeded = next(r for r in reports["physical_tolerance_exceeded"]["rows"] if r["t"] == -1)
    assert equal["feasible"] and equal["durations"] == (TOL,)
    assert not exceeded["feasible"] and exceeded["reason"] == "duration"
    output = {"status": "all_assertions_passed", "scope": "exact_rational_micro_oracle_only",
              "binary64_evaluator_equivalence": False, "production_solver_calls": 0,
              "cases": serial(reports), "old_gap_neighborhood": serial(old),
              "wall_seconds": time.perf_counter() - start_wall,
              "cpu_seconds": time.process_time() - start_cpu}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": output["status"], "cases": len(reports),
                      "wall_seconds": output["wall_seconds"],
                      "cpu_seconds": output["cpu_seconds"]}))


if __name__ == "__main__":
    main()
