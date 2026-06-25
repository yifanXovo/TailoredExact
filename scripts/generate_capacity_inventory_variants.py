#!/usr/bin/env python3
"""Generate regenerated capacity/inventory variants from parser-compatible inputs.

The generator preserves network geometry, distances, station ordering, vehicle
count, truck capacities, and all non-inventory lines.  Only station capacities,
initial inventories, and positive targets are regenerated.  Outputs are
engineering benchmarks, not historical paper targets.
"""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASES = [
    "reference/regen_candidate_V12_M1_average.txt",
    "reference/regen_candidate_V12_M2_average.txt",
    "reference/generated/regen_V10_M2_average.txt",
    "reference/generated/regen_V8_M2_average.txt",
]


def parse_list_line(line: str) -> list[int]:
    return list(ast.literal_eval(line.split("=", 1)[1].strip()))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_header(line: str) -> tuple[int, int, list[int]]:
    parts = line.lstrip("\ufeff").strip().split(maxsplit=2)
    if len(parts) < 3:
        raise ValueError(f"bad instance header: {line!r}")
    return int(parts[0]), int(parts[1]), list(ast.literal_eval(parts[2]))


def generate_one(base: Path, out_dir: Path, variant_index: int, seed: int) -> dict[str, object]:
    lines = base.read_text(encoding="utf-8").splitlines()
    v, m, q = parse_header(lines[0])
    rng = random.Random(seed)

    capacities = [100000]
    initial = [50000]
    target = [0]
    for _station in range(1, v + 1):
        cap = rng.randint(20, 50)
        capacities.append(cap)
        inv = rng.randint(0, cap)
        tgt = rng.randint(1, cap)
        initial.append(inv)
        target.append(tgt)
    if not any(x > 0 for x in initial[1:]):
        idx = rng.randint(1, v)
        initial[idx] = 1

    out_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("capacities"):
            out_lines.append("capacities = [" + ", ".join(map(str, capacities)) + "]")
        elif stripped.startswith("initial"):
            out_lines.append("initial     = [" + ", ".join(map(str, initial)) + "]")
        elif stripped.startswith("target"):
            out_lines.append("target      = [" + ", ".join(map(str, target)) + "]")
        else:
            out_lines.append(line)

    base_stem = base.stem
    variant_id = f"{base_stem}_capinv_seed{seed}"
    out_path = out_dir / f"{variant_id}.txt"
    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return {
        "variant_id": variant_id,
        "base_instance": str(base.relative_to(ROOT) if base.is_relative_to(ROOT) else base),
        "base_instance_hash": sha256(base),
        "output_path": str(out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path),
        "sha256": sha256(out_path),
        "seed": seed,
        "V": v,
        "M": m,
        "Q": ";".join(map(str, q)),
        "total_initial_inventory": sum(initial[1:]),
        "total_target_inventory": sum(target[1:]),
        "min_capacity": min(capacities[1:]),
        "max_capacity": max(capacities[1:]),
        "min_initial": min(initial[1:]),
        "max_initial": max(initial[1:]),
        "min_target": min(target[1:]),
        "max_target": max(target[1:]),
        "generation_rule_version": "capacity_inventory_v1",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", action="append", default=[])
    parser.add_argument("--variants-per-base", type=int, default=3)
    parser.add_argument("--seed-base", type=int, default=260626)
    parser.add_argument("--out-dir", default=str(ROOT / "reference" / "generated_variants"))
    args = parser.parse_args()

    bases = [Path(p) for p in (args.base or DEFAULT_BASES)]
    bases = [p if p.is_absolute() else ROOT / p for p in bases]
    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, object]] = []
    for bidx, base in enumerate(bases):
        if not base.exists():
            continue
        for ridx in range(max(1, args.variants_per_base)):
            seed = args.seed_base + 1000 * bidx + ridx
            rows.append(generate_one(base, out_dir, ridx, seed))

    manifest = out_dir / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"generated {len(rows)} variants under {out_dir}")


if __name__ == "__main__":
    main()
