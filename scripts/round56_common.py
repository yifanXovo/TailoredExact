#!/usr/bin/env python3
"""Shared deterministic definitions for the Round 56 paper-candidate panel."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_paper_benchmark_time_horizon_round56"
REFERENCE = ROOT / "reference" / "round56_paper_candidate"
BASE_COMMIT = "06b4c0634cbb85d3440be88511c736dd3282fdc9"
BASE_TREE = "412de9e5c5e5e2c90d18634abe83ebf72b0abc1a"
BASE_BRANCH = "codex/round55-k1-am-sf-station-state-chain"
BRANCH = "codex/round56-paper-benchmark-time-horizon"
BASE_PR_URL = "https://github.com/yifanXovo/TailoredExact/pull/113"
DERIVATION_VERSION = "round56-paper-time-horizon-v1"
GENERATOR_VERSION = "round56-moderate-landscape-generator-v2-serialized-coordinate-distance"
SCENARIO_SCHEMA_VERSION = "round56-mathematical-scenario-v1"
RUN_SCHEMA_VERSION = "round56-official-run-v1"
DISTANCE_CONVENTION = (
    "parsed Hybrid GA text format; distances rebuilt from points at speed factor 1.5"
)
PICKUP_SECONDS = 60
DROP_SECONDS = 60
LAMBDA = 0.15
V_SET = (8, 12, 20, 30, 50)
M_BY_V = {8: (1, 2), 12: (2, 3), 20: (2, 3), 30: (3, 4), 50: (4, 5)}
T_SET = (1800, 3600, 10800, 18000)
Q20_SENTINELS = ((8, 1), (12, 2), (20, 2), (30, 3), (50, 4))
CHECKPOINTS = (300, 1200, 3600)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def repo_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: Iterable[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(fields or (rows[0].keys() if rows else ()))
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def derived_seed(v: int) -> tuple[int, str, str]:
    material = f"{DERIVATION_VERSION}|{BASE_COMMIT}|V={v}|scenario=moderate"
    digest = sha256_bytes(material.encode("utf-8"))
    seed = 10_000 + int(digest[:16], 16) % 1_900_000_000
    return seed, material, digest


def clustered_points(rng: random.Random, v: int) -> list[tuple[float, float]]:
    depot = (584400.0, 4511800.0)
    centers = (
        (584120.0, 4511500.0),
        (584700.0, 4511760.0),
        (584320.0, 4512220.0),
    )
    points = [depot]
    for index in range(v):
        cx, cy = centers[index % len(centers)]
        points.append((cx + rng.uniform(-85.0, 85.0), cy + rng.uniform(-85.0, 85.0)))
    return points


def parser_distances(points: list[tuple[float, float]]) -> list[list[float]]:
    return [
        [math.hypot(x1 - x2, y1 - y2) / 1.5 for x2, y2 in points]
        for x1, y1 in points
    ]


def moderate_inventories(
    rng: random.Random, capacities: list[int]
) -> tuple[list[int], list[int]]:
    initial = [50000]
    target = [0]
    for capacity in capacities[1:]:
        center = capacity // 2
        initial.append(max(0, min(capacity, center + rng.randint(-12, 12))))
        target.append(max(1, min(capacity, center + rng.randint(-12, 12))))
    if not any(initial[i] > target[i] for i in range(1, len(initial))):
        initial[1] = min(capacities[1], target[1] + 5)
    if not any(initial[i] < target[i] for i in range(1, len(initial))):
        target[2] = min(capacities[2], initial[2] + 5)
        if target[2] <= initial[2]:
            initial[2] = max(0, target[2] - 5)
    return initial, target


def weight_vector(initial: list[int], target: list[int]) -> list[float]:
    raw = [abs(initial[i] / target[i] - 1.0) for i in range(1, len(initial))]
    scale = max(raw, default=1.0)
    return [0.0] + [0.05 + 0.95 * value / scale if scale > 0 else 1.0 for value in raw]


def min_ratio_vector(initial: list[int], target: list[int]) -> list[float]:
    return [0.0] + [
        max(0.0, min(initial[i], target[i]) / target[i] * 0.7)
        for i in range(1, len(initial))
    ]


def make_base_landscape(v: int) -> dict[str, Any]:
    seed, material, material_sha = derived_seed(v)
    rng = random.Random(seed)
    capacities = [100000] + [rng.randint(20, 50) for _ in range(v)]
    initial, target = moderate_inventories(rng, capacities)
    weights = weight_vector(initial, target)
    min_ratio = min_ratio_vector(initial, target)
    # The parser reads the serialized three-decimal coordinates and rebuilds
    # travel times from them. Round before computing distances so the frozen
    # generator data and the mathematical model are exactly identical.
    points = [(round(x, 3), round(y, 3)) for x, y in clustered_points(rng, v)]
    distances = parser_distances(points)
    off_diagonal = [
        distances[i][j]
        for i in range(v + 1)
        for j in range(v + 1)
        if i != j
    ]
    return {
        "schema": "round56-base-landscape-v1",
        "classification": "round56_paper_candidate_generated",
        "V": v,
        "seed": seed,
        "seed_derivation_material": material,
        "seed_derivation_sha256": material_sha,
        "generator_version": GENERATOR_VERSION,
        "source_commit": BASE_COMMIT,
        "station_order": list(range(v + 1)),
        "capacities": capacities,
        "initial": initial,
        "target": target,
        "weights": [round(value, 6) for value in weights],
        "min_ratio": [round(value, 4) for value in min_ratio],
        "points": [[x, y] for x, y in points],
        "distances": [[round(value, 10) for value in row] for row in distances],
        "distance_convention": DISTANCE_CONVENTION,
        "statistics": {
            "capacity_min": min(capacities[1:]),
            "capacity_max": max(capacities[1:]),
            "capacity_mean": sum(capacities[1:]) / v,
            "total_initial_inventory": sum(initial[1:]),
            "total_target_inventory": sum(target[1:]),
            "surplus_count": sum(initial[i] > target[i] for i in range(1, v + 1)),
            "deficit_count": sum(initial[i] < target[i] for i in range(1, v + 1)),
            "coordinate_min_x": min(x for x, _ in points),
            "coordinate_max_x": max(x for x, _ in points),
            "coordinate_min_y": min(y for _, y in points),
            "coordinate_max_y": max(y for _, y in points),
            "distance_min": min(off_diagonal),
            "distance_mean": sum(off_diagonal) / len(off_diagonal),
            "distance_max": max(off_diagonal),
        },
    }


def write_fleet_variant(path: Path, base: dict[str, Any], m: int, q: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"{base['V']} {m} [{', '.join(str(q) for _ in range(m))}]",
        "capacities = [" + ", ".join(map(str, base["capacities"])) + "]",
        "initial     = [" + ", ".join(map(str, base["initial"])) + "]",
        "target      = [" + ", ".join(map(str, base["target"])) + "]",
        "weights    = [" + ", ".join(f"{x:.6f}" for x in base["weights"]) + "]",
        "min_ratio  = [" + ", ".join(f"{x:.4f}" for x in base["min_ratio"]) + "]",
        "points = [" + ", ".join(f"({x:.3f}, {y:.3f})" for x, y in base["points"]) + "]",
        "distances = [",
    ]
    lines.extend("{" + ", ".join(f"{x:.10f}" for x in row) + "}" for row in base["distances"])
    lines.append("]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def mathematical_identity_material(descriptor: dict[str, Any]) -> str:
    values = (
        descriptor["base_landscape_sha256"],
        descriptor["fleet_variant_file_sha256"],
        str(descriptor["V"]),
        str(descriptor["M"]),
        canonical_json(descriptor["complete_Q_vector"]),
        str(descriptor["route_time_limit_seconds"]),
        str(descriptor["pickup_time_seconds"]),
        str(descriptor["drop_time_seconds"]),
        format(float(descriptor["lambda"]), ".17g"),
        descriptor["distance_convention"],
        SCENARIO_SCHEMA_VERSION,
    )
    return "||".join(values)


def mathematical_identity(descriptor: dict[str, Any]) -> str:
    return sha256_bytes(mathematical_identity_material(descriptor).encode("utf-8"))


def run_identity(
    mathematical_sha256: str,
    source_commit: str,
    executable_sha256: str,
    solver_contract_sha256: str,
    solver_process_cap_seconds: int,
    repetition_id: str,
) -> str:
    values = (
        mathematical_sha256,
        source_commit,
        executable_sha256,
        "paper-k1-am-sf",
        solver_contract_sha256,
        str(solver_process_cap_seconds),
        repetition_id,
        RUN_SCHEMA_VERSION,
    )
    return sha256_bytes("||".join(values).encode("utf-8"))


def final_cap(v: int, t: int) -> int:
    return 7200 if v >= 20 and t == 18000 else 3600
