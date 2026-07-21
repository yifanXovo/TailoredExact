#!/usr/bin/env python3
"""Generate deterministic V20/M3 and V50/M3 stress instances.

The output uses the Hybrid-GA-compatible text format parsed by ExactEBRP.
These are regenerated engineering benchmarks, not historical paper targets.
"""

from __future__ import annotations

import csv
import argparse
import hashlib
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RULE_VERSION = "hard_v20_m3_v1"


CASES = [
    ("tight_T_seed3101", 3101, "tight_T", 2400.0),
    ("tight_T_seed3102", 3102, "tight_T", 2550.0),
    ("high_imbalance_seed3201", 3201, "high_imbalance", 3600.0),
    ("high_imbalance_seed3202", 3202, "high_imbalance", 3600.0),
    ("moderate_seed3301", 3301, "moderate", 3600.0),
    ("moderate_seed3302", 3302, "moderate", 3600.0),
]

ROUND22_HELDOUT_CASES = [
    ("tight_T_seed4101", 4101, "tight_T", 2400.0),
    ("tight_T_seed4102", 4102, "tight_T", 2550.0),
    ("high_imbalance_seed4201", 4201, "high_imbalance", 3600.0),
    ("high_imbalance_seed4202", 4202, "high_imbalance", 3600.0),
    ("moderate_seed4301", 4301, "moderate", 3600.0),
    ("moderate_seed4302", 4302, "moderate", 3600.0),
]

# Round 26 selections were fixed before generation and before any solver run.
# Preferred seeds already present in tracked evidence were replaced by the
# first globally unused seed above that family's preferred range.  The exact
# pre-generation audit is retained in the Round 26 evaluation evidence.
ROUND26_HELDOUT_V20_CASES = [
    ("tight_T_seed5102", 5102, "tight_T", 2400.0),
    ("tight_T_seed5103", 5103, "tight_T", 2550.0),
    ("high_imbalance_seed5202", 5202, "high_imbalance", 3600.0),
    ("high_imbalance_seed5203", 5203, "high_imbalance", 3600.0),
    ("moderate_seed5301", 5301, "moderate", 3600.0),
    ("moderate_seed5302", 5302, "moderate", 3600.0),
]

ROUND26_V50_CASES = [
    ("tight_T_seed6102", 6102, "tight_T", 2400.0),
    ("high_imbalance_seed6202", 6202, "high_imbalance", 3600.0),
    ("moderate_seed6301", 6301, "moderate", 3600.0),
]


def clustered_points(rng: random.Random, v: int, stress_type: str) -> list[tuple[float, float]]:
    depot = (584400.0, 4511800.0)
    centers = [
        (584120.0, 4511500.0),
        (584700.0, 4511760.0),
        (584320.0, 4512220.0),
    ]
    points = [depot]
    for i in range(v):
        cx, cy = centers[i % len(centers)]
        spread = 85.0 if stress_type != "tight_T" else 115.0
        points.append((cx + rng.uniform(-spread, spread),
                       cy + rng.uniform(-spread, spread)))
    return points


def distance_matrix(points: list[tuple[float, float]]) -> list[list[float]]:
    dist: list[list[float]] = []
    for x1, y1 in points:
        row = []
        for x2, y2 in points:
            row.append(math.hypot(x1 - x2, y1 - y2))
        dist.append(row)
    return dist


def make_inventories(rng: random.Random, capacities: list[int],
                     stress_type: str) -> tuple[list[int], list[int]]:
    initial = [50000]
    target = [0]
    surplus_seen = False
    deficit_seen = False
    for cap in capacities[1:]:
        if stress_type == "high_imbalance":
            if rng.random() < 0.5:
                init = rng.randint(max(0, cap - 8), cap)
                tgt = rng.randint(1, max(1, cap // 3))
            else:
                init = rng.randint(0, min(cap, cap // 4))
                tgt = rng.randint(max(1, 2 * cap // 3), cap)
        elif stress_type == "tight_T":
            init = rng.randint(0, cap)
            tgt = rng.randint(1, cap)
        else:
            center = cap // 2
            init = max(0, min(cap, center + rng.randint(-12, 12)))
            tgt = max(1, min(cap, center + rng.randint(-12, 12)))
        surplus_seen = surplus_seen or init > tgt
        deficit_seen = deficit_seen or init < tgt
        initial.append(init)
        target.append(tgt)
    if not surplus_seen:
        initial[1] = min(capacities[1], target[1] + 5)
    if not deficit_seen:
        target[2] = min(capacities[2], initial[2] + 5)
        if target[2] <= initial[2]:
            initial[2] = max(0, target[2] - 5)
    if sum(initial[1:]) == 0:
        initial[1] = max(1, capacities[1] // 2)
    return initial, target


def weight_vector(initial: list[int], target: list[int]) -> list[float]:
    weights = [0.0]
    raw = []
    for i in range(1, len(initial)):
        raw.append(abs(initial[i] / max(1, target[i]) - 1.0))
    scale = max(raw) if raw else 1.0
    for value in raw:
        weights.append(0.05 + 0.95 * value / scale if scale > 0 else 1.0)
    return weights


def min_ratio_vector(initial: list[int], target: list[int]) -> list[float]:
    out = [0.0]
    for i in range(1, len(initial)):
        out.append(max(0.0, min(initial[i], target[i]) / max(1, target[i]) * 0.7))
    return out


def write_instance(path: Path, seed: int, stress_type: str, t_limit: float,
                   v: int = 20) -> dict[str, str]:
    rng = random.Random(seed)
    m = 3
    q = 30
    capacities = [100000] + [rng.randint(20, 50) for _ in range(v)]
    initial, target = make_inventories(rng, capacities, stress_type)
    weights = weight_vector(initial, target)
    min_ratio = min_ratio_vector(initial, target)
    points = clustered_points(rng, v, stress_type)
    dist = distance_matrix(points)

    with path.open("w", encoding="utf-8", newline="\n") as out:
        out.write(f"{v} {m} [{', '.join(str(q) for _ in range(m))}]\n")
        out.write("capacities = [" + ", ".join(map(str, capacities)) + "]\n")
        out.write("initial     = [" + ", ".join(map(str, initial)) + "]\n")
        out.write("target      = [" + ", ".join(map(str, target)) + "]\n")
        out.write("weights    = [" + ", ".join(f"{x:.6f}" for x in weights) + "]\n")
        out.write("min_ratio  = [" + ", ".join(f"{x:.4f}" for x in min_ratio) + "]\n")
        out.write("points = [" + ", ".join(f"({x:.3f}, {y:.3f})" for x, y in points) + "]\n")
        out.write("distances = [\n")
        for row in dist:
            out.write("{" + ", ".join(f"{x:.4f}" for x in row) + "}\n")
        out.write("]\n")

    data = path.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    surplus = sum(1 for i in range(1, v + 1) if initial[i] > target[i])
    deficit = sum(1 for i in range(1, v + 1) if initial[i] < target[i])
    return {
        "path": path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "sha256": sha,
        "seed": str(seed),
        "V": str(v),
        "M": str(m),
        "Q": str(q),
        "T": f"{t_limit:.0f}",
        "lambda": "0.15",
        "capacity_min": str(min(capacities[1:])),
        "capacity_max": str(max(capacities[1:])),
        "total_initial": str(sum(initial[1:])),
        "total_target": str(sum(target[1:])),
        "surplus_count": str(surplus),
        "deficit_count": str(deficit),
        "coordinate_pattern": "three_cluster_metric",
        "stress_type": stress_type,
        "generation_rule_version": RULE_VERSION,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite",
        choices=(
            "existing", "round22-heldout", "round26-heldout-v20",
            "round26-v50",
        ),
        default="existing",
        help="deterministic case registry to generate",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        help="optional output directory (relative paths resolve from the repository root)",
    )
    args = parser.parse_args()

    suites = {
        "existing": (
            CASES, 20, ROOT / "reference" / "hard_stress" / "V20_M3"),
        "round22-heldout": (
            ROUND22_HELDOUT_CASES, 20,
            ROOT / "reference" / "heldout_round22" / "V20_M3"),
        "round26-heldout-v20": (
            ROUND26_HELDOUT_V20_CASES, 20,
            ROOT / "reference" / "heldout_round26" / "V20_M3"),
        "round26-v50": (
            ROUND26_V50_CASES, 50,
            ROOT / "reference" / "heldout_round26" / "V50_M3"),
    }
    cases, v, default_out = suites[args.suite]
    out_dir = args.out_dir or default_out
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for instance_id, seed, stress_type, t_limit in cases:
        path = out_dir / f"{instance_id}.txt"
        row = write_instance(path, seed, stress_type, t_limit, v=v)
        row["instance_id"] = instance_id
        rows.append(row)

    manifest = out_dir / "manifest.csv"
    fields = [
        "instance_id", "path", "sha256", "seed", "V", "M", "Q", "T",
        "lambda", "capacity_min", "capacity_max", "total_initial",
        "total_target", "surplus_count", "deficit_count",
        "coordinate_pattern", "stress_type", "generation_rule_version",
    ]
    with manifest.open("w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"generated {len(rows)} instances under {out_dir}")


if __name__ == "__main__":
    main()
