"""Independent, tiny Fraction oracle for the R95 fixed-two-station block.

No production module, native executable, or solver is imported or started.
The direct side rebuilds every route and its physical prefixes; the other
side derives bands solely from the unchanged baseline's prefix loads.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from fractions import Fraction as F


ZERO = F(0)
TOL = F(1, 10_000_000)
LAMBDA = F(3, 20)


def matrix(n: int, default: F = ZERO) -> tuple[tuple[F, ...], ...]:
    return tuple(tuple(ZERO if i == j else default for j in range(n + 1))
                 for i in range(n + 1))


def edge(base: tuple[tuple[F, ...], ...], i: int, j: int, value: F):
    rows = [list(row) for row in base]
    rows[i][j] = value
    return tuple(tuple(row) for row in rows)


@dataclass(frozen=True)
class Case:
    name: str
    initial: tuple[int, ...]  # depot excluded; station i uses index i-1
    capacity: tuple[int, ...]
    target: tuple[int, ...]
    weight: tuple[F, ...]
    baseline: tuple[int, ...]
    routes: tuple[tuple[int, ...], ...]
    vehicle_capacity: tuple[int, ...]
    distance: tuple[tuple[F, ...], ...]
    pickup_time: F = ZERO
    drop_time: F = ZERO
    T: F = F(1)
    a: int = 1
    b: int = 2


def objective(case: Case, inventory: tuple[int, ...]) -> tuple[F, F, F]:
    ratio = [F(y, d) for y, d in zip(inventory, case.target)]
    total = sum(ratio, ZERO)
    pairwise = sum((abs(ratio[i] - ratio[j]) for i in range(len(ratio))
                    for j in range(i)), ZERO)
    gini = pairwise / (len(ratio) * total) if total else ZERO
    penalty = sum((w * abs(r - 1) for w, r in zip(case.weight, ratio)), ZERO)
    return gini + LAMBDA * penalty, gini, penalty


def direct_rebuild(case: Case, inventory: tuple[int, ...]) -> dict:
    """Rebuild canonical signed operations, remove zeros, then simulate routes."""
    assert len(inventory) == len(case.initial)
    stock_ok = all(0 <= y <= c for y, c in zip(inventory, case.capacity))
    assert stock_ok
    route_rows = []
    load_ok = True
    duration_ok = True
    for vehicle, original in enumerate(case.routes):
        kept = [s for s in original if case.initial[s - 1] != inventory[s - 1]]
        load = 0
        loads = []
        pickups = drops = 0
        for s in kept:
            signed = case.initial[s - 1] - inventory[s - 1]
            pickups += max(0, signed)
            drops += max(0, -signed)
            load += signed
            loads.append(load)
            if not 0 <= load <= case.vehicle_capacity[vehicle]:
                load_ok = False
        tour = [0, *kept, 0]
        travel = sum((case.distance[i][j] for i, j in zip(tour, tour[1:])), ZERO)
        duration = (travel + case.pickup_time * pickups + case.drop_time * drops
                    + case.drop_time * (pickups - drops))
        if duration > case.T + TOL:
            duration_ok = False
        route_rows.append(dict(vehicle=vehicle, kept=kept, loads=loads,
                               travel=str(travel), duration=str(duration)))
    f, g, p = objective(case, inventory)
    return dict(load_ok=load_ok, duration_ok=duration_ok,
                physical=load_ok and duration_ok, F=f, G=g, P=p,
                routes=route_rows)


def bands_from_baseline(case: Case) -> dict[tuple[int, int], tuple[int, int]]:
    """Independent algebraic prediction from old prefixes; no candidate rebuild."""
    raw: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for vehicle, route in enumerate(case.routes):
        load = 0
        seen_a = seen_b = 0
        for station in route:
            load += case.initial[station - 1] - case.baseline[station - 1]
            seen_a |= int(station == case.a)
            seen_b |= int(station == case.b)
            if seen_a or seen_b:
                raw.setdefault((seen_a, seen_b), []).append(
                    (load - case.vehicle_capacity[vehicle], load))
    return {group: (max(x[0] for x in values), min(x[1] for x in values))
            for group, values in raw.items()}


def band_predict(case: Case, inventory: tuple[int, ...], bands: dict) -> bool:
    da = inventory[case.a - 1] - case.baseline[case.a - 1]
    db = inventory[case.b - 1] - case.baseline[case.b - 1]
    return all(low <= sa * da + sb * db <= high
               for (sa, sb), (low, high) in bands.items())


def interval_predict(case: Case, da: int, bands: dict) -> tuple[int, int]:
    """The proposed per-da interval, separately checked against brute bands."""
    low = -case.baseline[case.b - 1]
    high = case.capacity[case.b - 1] - case.baseline[case.b - 1]
    if (1, 0) in bands:
        a, z = bands[(1, 0)]
        if not a <= da <= z:
            return 1, 0
    if (0, 1) in bands:
        a, z = bands[(0, 1)]
        low, high = max(low, a), min(high, z)
    if (1, 1) in bands:
        a, z = bands[(1, 1)]
        low, high = max(low, a - da), min(high, z - da)
    return low, high


def fixtures() -> list[Case]:
    small_metric = matrix(2, F(1, 100))
    micro = Case('strong_micro_zero', (2, 8), (8, 8), (4, 8),
                 (F(1), F(1)), (1, 2), ((1, 2),), (7,), matrix(2))
    metric = Case('strong_micro_positive', micro.initial, micro.capacity,
                  micro.target, micro.weight, micro.baseline, micro.routes,
                  micro.vehicle_capacity, small_metric, F(1, 100), F(1, 100))
    s0 = Case('zero_ratio_sum_heterogeneous', (1, 1), (2, 3), (2, 3),
              (F(2), F(1, 2)), (0, 0), ((1, 2),), (2,), matrix(2))
    same = Case('same_owner_intervening', (3, 2, 4), (5, 3, 6), (3, 4, 5),
                (F(1, 2), F(2), F(3, 4)), (2, 1, 3), ((1, 2, 3),),
                (3,), matrix(3), F(1, 20), F(1, 40), F(2), 1, 3)
    reverse = Case('reversed_order_original_drop', (1, 2, 2), (4, 4, 3),
                   (2, 3, 4), (F(1), F(3, 2), F(1, 2)), (2, 1, 0),
                   ((3, 2, 1),), (3,), matrix(3), F(1, 40), F(1, 40), F(2))
    cross = Case('different_vehicle_owners', (3, 2, 2, 3), (5, 4, 3, 4),
                 (4, 3, 2, 5), (F(2), F(1), F(1, 3), F(3, 2)),
                 (2, 1, 1, 2), ((3, 1), (4, 2)), (3, 3), matrix(4),
                 F(1, 50), F(1, 50), F(2))
    nonmetric_dist = edge(matrix(2), 0, 2, F(11))
    nonmetric = Case('nonmetric_deletion_increases_travel', (2, 4), (4, 5),
                     (3, 4), (F(1), F(2)), (1, 2), ((1, 2),), (3,),
                     nonmetric_dist, ZERO, ZERO, F(5))
    eq = Case('duration_exact_T_plus_tol', (1, 1), (2, 2), (1, 1),
              (F(1), F(1)), (0, 0), ((1, 2),), (2,),
              edge(matrix(2), 0, 2, F(1) + TOL))
    out = Case('duration_beyond_T_plus_tol', eq.initial, eq.capacity,
               eq.target, eq.weight, eq.baseline, eq.routes,
               eq.vehicle_capacity, edge(matrix(2), 0, 2,
                                         F(1) + TOL + F(1, 100_000_000)))
    return [micro, metric, s0, same, reverse, cross, nonmetric, eq, out]


def check_case(case: Case) -> dict:
    n = len(case.initial)
    assert len(case.capacity) == len(case.target) == len(case.weight) == n
    assert len(case.routes) == len(case.vehicle_capacity)
    assert {s for route in case.routes for s in route} == {
        i for i in range(1, n + 1) if case.baseline[i - 1] != case.initial[i - 1]}
    assert len({s for route in case.routes for s in route}) == sum(map(len, case.routes))
    baseline = direct_rebuild(case, case.baseline)
    assert baseline['physical'], case.name
    bands = bands_from_baseline(case)
    assert len(bands) <= 2
    rows = 0
    load_rows = 0
    physical_rows = 0
    best = (baseline['F'], case.baseline[case.a - 1], case.baseline[case.b - 1])
    for u in range(case.capacity[case.a - 1] + 1):
        da = u - case.baseline[case.a - 1]
        low, high = interval_predict(case, da, bands)
        for v in range(case.capacity[case.b - 1] + 1):
            if (u, v) == (case.baseline[case.a - 1], case.baseline[case.b - 1]):
                continue
            inventory = list(case.baseline)
            inventory[case.a - 1], inventory[case.b - 1] = u, v
            actual = direct_rebuild(case, tuple(inventory))
            predicted = band_predict(case, tuple(inventory), bands)
            interval = low <= v - case.baseline[case.b - 1] <= high
            assert actual['load_ok'] == predicted == interval, (case.name, u, v, bands)
            rows += 1
            load_rows += actual['load_ok']
            physical_rows += actual['physical']
            if actual['physical'] and (actual['F'], u, v) < best:
                best = (actual['F'], u, v)
    return dict(name=case.name, rectangle_points=rows, load_feasible=load_rows,
                physical=physical_rows, bands={str(k): v for k, v in bands.items()},
                baseline_F=str(baseline['F']), best_F=str(best[0]), best_inventory=best[1:])


def check_strong_micro(case: Case):
    initial = direct_rebuild(case, case.baseline)
    improved = direct_rebuild(case, (2, 4))
    empty = direct_rebuild(case, case.initial)
    assert initial['F'] == F(9, 40)
    assert improved['physical'] and improved['F'] == F(3, 20)
    assert improved['routes'][0]['kept'] == [2]
    assert empty['F'] == F(29, 120) and empty['F'] > initial['F']
    a, b = case.baseline
    for u in range(case.capacity[0] + 1):
        for v in range(case.capacity[1] + 1):
            da, db = u - a, v - b
            old_direction = da == 0 or db == 0 or da == -db or da == db
            if old_direction:
                row = direct_rebuild(case, (u, v))
                assert not (row['physical'] and row['F'] < initial['F']), (u, v)
    assert direct_rebuild(case, (2, 2))['F'] == F(17, 48)
    assert direct_rebuild(case, (0, 3))['F'] == F(119, 160)
    assert direct_rebuild(case, (2, 1))['F'] == F(81, 160)
    assert direct_rebuild(case, (2, 3))['F'] == F(269, 1120)


def main():
    started = time.perf_counter()
    cases = fixtures()
    result = [check_case(case) for case in cases]
    check_strong_micro(cases[0])
    check_strong_micro(cases[1])
    assert direct_rebuild(cases[6], (2, 2))['load_ok']
    assert not direct_rebuild(cases[6], (2, 2))['duration_ok']
    assert direct_rebuild(cases[7], (1, 0))['physical']
    assert not direct_rebuild(cases[8], (1, 0))['duration_ok']
    assert objective(cases[2], (0, 0))[1] == ZERO
    print(json.dumps(dict(schema='round95-independent-rational-oracle-v1',
                          case_count=len(cases), total_rectangle_points=sum(r['rectangle_points'] for r in result),
                          total_load_feasible=sum(r['load_feasible'] for r in result),
                          internal_seconds_before_stdout=time.perf_counter() - started,
                          cases=result), ensure_ascii=False))


if __name__ == '__main__':
    main()
