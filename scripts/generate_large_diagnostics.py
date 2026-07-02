#!/usr/bin/env python3
"""Generate deterministic large diagnostic EBRP instances."""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import random
from pathlib import Path
from typing import List, Tuple


def weights_from_targets(target: List[int]) -> List[float]:
    vals = [0.0]
    max_dev = max(abs(t - sum(target[1:]) / (len(target) - 1)) for t in target[1:]) or 1.0
    for t in target[1:]:
        vals.append(min(1.0, 0.05 + abs(t - sum(target[1:]) / (len(target) - 1)) / max_dev))
    return vals


def build_instance(v: int, m: int, seed: int, stress: str) -> str:
    rng = random.Random(seed)
    q = [30 for _ in range(m)]
    capacities = [100000]
    initial = [50000]
    target = [0]
    points: List[Tuple[float, float]] = [(584400.0, 4511800.0)]
    for i in range(1, v + 1):
        if stress == "high_imbalance":
            cap = rng.randint(24, 62)
            tgt = rng.randint(2, cap - 2)
            if i % 3 == 0:
                init = rng.randint(0, max(1, cap // 5))
            elif i % 3 == 1:
                init = rng.randint(max(1, 4 * cap // 5), cap)
            else:
                init = rng.randint(0, cap)
        else:
            cap = rng.randint(24, 58)
            tgt = rng.randint(max(1, cap // 3), max(2, 2 * cap // 3))
            init = min(cap, max(0, int(round(rng.gauss(tgt, cap * 0.16)))))
        capacities.append(cap)
        initial.append(init)
        target.append(tgt)
        cluster = i % 3
        cx = [584150.0, 584650.0, 584380.0][cluster]
        cy = [4511520.0, 4511810.0, 4512240.0][cluster]
        points.append((cx + rng.uniform(-100, 100), cy + rng.uniform(-100, 100)))
    weights = weights_from_targets(target)
    min_ratio = [0.0] + [0.0 if capacities[i] == 0 else initial[i] / capacities[i] for i in range(1, v + 1)]
    dist = []
    for x1, y1 in points:
        row = []
        for x2, y2 in points:
            row.append(math.hypot(x1 - x2, y1 - y2) / 1.5)
        dist.append(row)

    lines = [f"{v} {m} [{', '.join(map(str, q))}]"]
    lines.append(f"capacities = [{', '.join(map(str, capacities))}]")
    lines.append(f"initial     = [{', '.join(map(str, initial))}]")
    lines.append(f"target      = [{', '.join(map(str, target))}]")
    lines.append("weights    = [" + ", ".join(f"{w:.6f}" for w in weights) + "]")
    lines.append("min_ratio  = [" + ", ".join(f"{r:.4f}" for r in min_ratio) + "]")
    lines.append("points = [" + ", ".join(f"({x:.3f}, {y:.3f})" for x, y in points) + "]")
    lines.append("distances = [")
    for row in dist:
        lines.append("{" + ", ".join(f"{d:.4f}" for d in row) + "}")
    lines.append("]")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default="reference/large_diagnostics")
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = [
        ("V50_M3_moderate_seed5101", 50, 3, 5101, "moderate"),
        ("V50_M3_high_imbalance_seed5201", 50, 3, 5201, "high_imbalance"),
        ("V100_M5_moderate_seed6101", 100, 5, 6101, "moderate"),
        ("V100_M5_high_imbalance_seed6201", 100, 5, 6201, "high_imbalance"),
    ]
    rows = []
    for name, v, m, seed, stress in specs:
        path = out_dir / f"{name}.txt"
        text = build_instance(v, m, seed, stress)
        path.write_text(text, encoding="utf-8")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        rows.append(
            {
                "instance_id": name,
                "path": str(path).replace("\\", "/"),
                "sha256": digest,
                "seed": seed,
                "V": v,
                "M": m,
                "stress_type": stress,
                "generation_rule_version": "large_diag_v1",
            }
        )
    with (out_dir / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} instances to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
