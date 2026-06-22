#!/usr/bin/env python3
"""Generate deterministic parser-compatible EBRP benchmark inputs.

These are engineering benchmarks when historical source files are not present.
They intentionally use nontrivial station capacities and inventory/target
imbalances, but they are not historical paper instances.
"""

from __future__ import annotations

import csv
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reference" / "generated"


CASES = [
    ("V8_M2_average", 8, 2, [20, 20], "average", 8201),
    ("V10_M1_average", 10, 1, [30], "average", 10031),
    ("V10_M2_average", 10, 2, [20, 20], "average", 10032),
    ("V10_M2_low", 10, 2, [20, 20], "low", 10033),
    ("V20_M2_average", 20, 2, [30, 30], "average", 20032),
    ("V20_M3_low", 20, 3, [20, 20, 20], "low", 20033),
    ("V50_M3_average", 50, 3, [30, 30, 30], "average", 50033),
    ("V50_M5_low", 50, 5, [20, 20, 20, 20, 20], "low", 50035),
    ("V70_M5_average", 70, 5, [30, 30, 30, 30, 30], "average", 70035),
    ("V100_M5_average", 100, 5, [30, 30, 30, 30, 30], "average", 100055),
    ("V100_M8_low", 100, 8, [20, 20, 20, 20, 20, 20, 20, 20], "low", 100088),
]


def euclidean_time(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1]) / 1.5


def fmt_int_list(values: list[int]) -> str:
    return "[" + ", ".join(str(v) for v in values) + "]"


def fmt_float_list(values: list[float], digits: int = 6) -> str:
    return "[" + ", ".join(f"{v:.{digits}f}" for v in values) + "]"


def fmt_points(points: list[tuple[float, float]]) -> str:
    return "[" + ", ".join(f"({x:.3f}, {y:.3f})" for x, y in points) + "]"


def build_case(name: str, v: int, m: int, q: list[int], scenario: str, seed: int):
    rng = random.Random(seed)
    capacities = [100000]
    initial = [50000]
    target = [0]
    weights = [0.0]
    min_ratio = [0.0]

    target_shift = -3 if scenario == "low" else 0
    for i in range(1, v + 1):
        cap = rng.randint(24, 50)
        capacities.append(cap)
        tgt = rng.randint(10, max(12, cap - 8)) + target_shift
        tgt = max(6, min(cap - 3, tgt))
        target.append(tgt)
        delta = rng.choice([-1, 1]) * rng.randint(5, max(6, cap // 2))
        inv = max(1, min(cap - 1, tgt + delta))
        initial.append(inv)
        imbalance = abs(inv / max(1, tgt) - 1.0)
        weights.append(min(1.0, max(0.05, 0.15 + 0.85 * imbalance)))
        min_ratio.append(rng.uniform(0.02, 0.50))

    # Keep total bikes in a realistic range without making the cases balanced.
    if sum(initial[1:]) < int(0.35 * sum(capacities[1:])):
        for i in range(1, v + 1):
            add = min(capacities[i] - 1 - initial[i], rng.randint(0, 6))
            initial[i] += max(0, add)

    points = [(586500.0, 4512500.0)]
    for _ in range(v):
        angle = rng.uniform(0.0, 2.0 * math.pi)
        radius = rng.uniform(90.0, 430.0)
        jitter_x = rng.uniform(-60.0, 60.0)
        jitter_y = rng.uniform(-60.0, 60.0)
        points.append(
            (
                points[0][0] + radius * math.cos(angle) + jitter_x,
                points[0][1] + radius * math.sin(angle) + jitter_y,
            )
        )

    dist = [[euclidean_time(points[i], points[j]) for j in range(v + 1)] for i in range(v + 1)]
    path = OUT_DIR / f"regen_{name}.txt"
    with path.open("w", encoding="utf-8") as f:
        f.write(f"{v} {m} {fmt_int_list(q)}\n")
        f.write(f"capacities = {fmt_int_list(capacities)}\n")
        f.write(f"initial     = {fmt_int_list(initial)}\n")
        f.write(f"target      = {fmt_int_list(target)}\n")
        f.write(f"weights    = {fmt_float_list(weights)}\n")
        f.write(f"min_ratio  = {fmt_float_list(min_ratio, 4)}\n")
        f.write(f"points = {fmt_points(points)}\n")
        f.write("distances = [\n")
        for row in dist:
            f.write("{" + ", ".join(f"{x:.4f}" for x in row) + "}\n")
        f.write("]\n")
    return {
        "file": str(path.relative_to(ROOT)),
        "case": name,
        "seed": seed,
        "V": v,
        "M": m,
        "Q": ";".join(str(x) for x in q),
        "capacity_min": min(capacities[1:]),
        "capacity_max": max(capacities[1:]),
        "scenario": scenario,
        "total_bikes": sum(initial[1:]),
        "total_target": sum(target[1:]),
        "generated_for": "engineering_scalability",
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [build_case(*case) for case in CASES]
    with (OUT_DIR / "manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"generated {len(rows)} instances under {OUT_DIR}")


if __name__ == "__main__":
    main()
