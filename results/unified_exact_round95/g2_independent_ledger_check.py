"""Read-only independent R95 G2 prefix/point ledger check; never launches native code."""

import ast
import json
import math
from pathlib import Path
import re
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "results/unified_exact_round95/runner_full_block_g2"
PLAN = json.loads((ROOT / "results/unified_exact_round95/full_block_diagnostic_preregistration.json").read_text())


def rows(path):
    with path.open() as stream:
        yield from (json.loads(line) for line in stream)


def vector(source, name):
    match = re.search(r"(?m)^\s*" + name + r"\s*=\s*(\[[^\n]*\])", source)
    assert match is not None
    return ast.literal_eval(match.group(1))


def routes_of(witness):
    return sorted([(route["vehicle"], [
        (op["station"], op["pickup"], op["drop"]) if isinstance(op, dict) else tuple(op)
        for op in route["operations"]]) for route in witness["routes"]])


def bands_for(routes, q, a, b):
    bands = {k: dict(present=False, low=0, high=0, prefixes=0)
             for k in ("band10", "band01", "band11")}
    for vehicle, ops in routes:
        load = 0
        seen_a = seen_b = False
        for station, pickup, drop in ops:
            load += pickup - drop
            assert 0 <= load <= q[vehicle]
            seen_a |= station == a
            seen_b |= station == b
            key = "band11" if seen_a and seen_b else "band10" if seen_a else "band01" if seen_b else None
            if key:
                band = bands[key]
                lo, hi = load - q[vehicle], load
                if band["present"]:
                    band["low"], band["high"] = max(band["low"], lo), min(band["high"], hi)
                else:
                    band.update(present=True, low=lo, high=hi)
                band["prefixes"] += 1
    return bands


started = time.perf_counter()
out = []
for case in PLAN["cases"]:
    name = case["id"]
    source = (ROOT / case["input_path"]).read_text()
    q = ast.literal_eval(re.fullmatch(r"\s*\d+\s+\d+\s+(\[[^\]]*\])\s*", source.splitlines()[0]).group(1))
    initial, capacity = vector(source, "initial"), vector(source, "capacities")
    original = json.loads((ROOT / case["witness_path"]).read_text())
    final = json.loads((BASE / name / "native/final_witness.json").read_text())
    summary = json.loads((BASE / name / "native/summary.json").read_text())
    receipt = json.loads((BASE / name / "outer_receipt.json").read_text())
    routes = routes_of(original)
    assert routes == routes_of(final)
    inventory = initial.copy()
    for _, operations in routes:
        for station, pickup, drop in operations:
            inventory[station] = initial[station] - pickup + drop
    served = sorted({station for _, operations in routes for station, _, _ in operations})
    pairs = rectangles = pruned = evaluated = feasible = duration = intervals = 0
    band_rows = rows(BASE / name / "native/bands.jsonl")
    interval_rows = rows(BASE / name / "native/intervals.jsonl")
    point_rows = rows(BASE / name / "native/points.jsonl")
    base_f = summary["initial_F"]
    assert summary["passes"] == 1 and summary["accepted"] == 0
    assert not (BASE / name / "native/acceptances.jsonl").read_text()
    for ia, a in enumerate(served):
        for b in served[ia + 1:]:
            pairs += 1
            rectangle = (capacity[a] + 1) * (capacity[b] + 1) - 1
            rectangles += rectangle
            bands = bands_for(routes, q, a, b)
            got = next(band_rows)
            assert all(got[k] == v for k, v in dict(**{"pass": 1}, a=a, b=b,
                    old_a=inventory[a], old_b=inventory[b], capacity_a=capacity[a],
                    capacity_b=capacity[b], rectangle_points=rectangle, **bands).items())
            for u in range(capacity[a] + 1):
                intervals += 1
                da = u - inventory[a]
                lo, hi = 0, capacity[b]
                if bands["band10"]["present"] and not bands["band10"]["low"] <= da <= bands["band10"]["high"]:
                    hi = -1
                if bands["band01"]["present"]:
                    lo = max(lo, inventory[b] + bands["band01"]["low"])
                    hi = min(hi, inventory[b] + bands["band01"]["high"])
                if bands["band11"]["present"]:
                    lo = max(lo, inventory[b] + bands["band11"]["low"] - da)
                    hi = min(hi, inventory[b] + bands["band11"]["high"] - da)
                if lo > hi:
                    lo, hi = 0, -1
                survivors = max(0, hi - lo + 1) - (u == inventory[a] and lo <= inventory[b] <= hi)
                pruned += capacity[b] + 1 - (u == inventory[a]) - survivors
                got = next(interval_rows)
                assert got == {"pass": 1, "a": a, "b": b, "u": u,
                               "v_low": lo, "v_high": hi, "surviving_points": survivors}
                for v in range(lo, hi + 1):
                    if u == inventory[a] and v == inventory[b]:
                        continue
                    evaluated += 1
                    point = next(point_rows)
                    assert all(point[k] == val for k, val in
                               (("pass", 1), ("a", a), ("b", b), ("u", u), ("v", v)))
                    assert point["physical_checked"] is True and point["load_feasible"] is True
                    assert point["station_feasible"] is True and point["objective_recomputed"] is True
                    assert all(math.isfinite(point[k]) for k in ("F", "G", "P"))
                    assert abs(point["F"] - (point["G"] + case["scenario"]["lambda"] * point["P"])) < 1e-12
                    if point["feasible"]:
                        feasible += 1
                        assert point["reason"] == "no_strict_original_F_improvement"
                        assert base_f - point["F"] <= 1e-12
                    else:
                        duration += 1
                        assert point["duration_feasible"] is False and point["reason"] == "duration"
    assert next(band_rows, None) is next(interval_rows, None) is next(point_rows, None) is None
    assert rectangles == pruned + evaluated
    assert all(summary[k] == value for k, value in dict(station_pairs=pairs, rectangle_points=rectangles,
        load_pruned=pruned, candidate_points=evaluated, evaluator_points=evaluated,
        feasible_points=feasible, duration_rejections=duration).items())
    assert summary["exhausted"] is True and summary["deadline"] is False and summary["verification_failed"] is False
    assert all(summary[k] == 0 for k in ("integer_domain_rejections", "station_rejections",
        "other_physical_rejections", "nonfinite_rejections", "deleted_stops", "sign_flips"))
    assert all(summary["initial_" + k] == summary["final_" + k] == final[k] for k in ("F", "G", "P"))
    assert final["inventory"] == inventory
    assert receipt["child_exit_code"] == 0 and receipt["evidence"]["status"] == "diagnostic_completed"
    out.append(dict(case=name, pairs=pairs, rectangles=rectangles, pruned=pruned,
                    evaluated=evaluated, feasible=feasible, duration_rejected=duration,
                    band_rows=pairs, interval_rows=intervals, F=base_f))

print(json.dumps(dict(status="independent_ledger_pass", cases=out,
                      sampled_before_output_wall_seconds=time.perf_counter() - started)))
