#!/usr/bin/env python3
"""Solver-independent instance parsing and structural descriptors for Round 39."""

from __future__ import annotations

import ast
import hashlib
import math
import re
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPEED_METRES_PER_SECOND = 1.5
LOAD_SECONDS = 60.0
UNLOAD_SECONDS = 60.0


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _named(text: str, name: str) -> Any:
    match = re.search(
        rf"^{re.escape(name)}\s*=\s*(\[[^\n]*\])\s*$",
        text,
        flags=re.MULTILINE,
    )
    if not match:
        raise ValueError(f"missing one-line vector: {name}")
    return ast.literal_eval(match.group(1))


def read_instance(path: Path, *, total_time_limit: float) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    first = text.splitlines()[0]
    head = re.match(r"^(\d+)\s+(\d+)\s+(\[[^]]+\])$", first)
    if not head:
        raise ValueError(f"invalid instance header: {path}")
    v, m = int(head.group(1)), int(head.group(2))
    q = [int(value) for value in ast.literal_eval(head.group(3))]
    data = {
        "V": v,
        "M": m,
        "Q_list": q,
        "capacities": [int(value) for value in _named(text, "capacities")],
        "initial": [int(value) for value in _named(text, "initial")],
        "target": [int(value) for value in _named(text, "target")],
        "weights": [float(value) for value in _named(text, "weights")],
        "min_ratio": [float(value) for value in _named(text, "min_ratio")],
        "points": [(float(x), float(y)) for x, y in _named(text, "points")],
        "T": float(total_time_limit),
    }
    if len(q) != m:
        raise ValueError(f"vehicle capacity count mismatch: {path}")
    for field in ("capacities", "initial", "target", "weights", "min_ratio",
                  "points"):
        if len(data[field]) != v + 1:
            raise ValueError(f"{field} size mismatch: {path}")
    return data


def _distances(points: list[tuple[float, float]]) -> list[list[float]]:
    return [[
        math.hypot(x1 - x2, y1 - y2) / SPEED_METRES_PER_SECOND
        for x2, y2 in points
    ] for x1, y1 in points]


def _mst_weight(dist: list[list[float]], nodes: list[int]) -> float:
    if len(nodes) <= 1:
        return 0.0
    reached = {nodes[0]}
    remaining = set(nodes[1:])
    total = 0.0
    while remaining:
        value, node = min(
            (dist[left][right], right)
            for left in reached for right in remaining
        )
        total += value
        reached.add(node)
        remaining.remove(node)
    return total


def _gini(values: list[float]) -> float:
    denominator = 2.0 * len(values) * sum(values)
    if denominator <= 0.0:
        return 0.0
    return sum(abs(left - right) for left in values for right in values) / denominator


def _cv(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = statistics.fmean(values)
    return statistics.pstdev(values) / mean if mean > 0.0 else 0.0


def _clip(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return min(upper, max(lower, value))


def descriptors(data: dict[str, Any]) -> dict[str, Any]:
    v, m, time_limit = data["V"], data["M"], data["T"]
    q = data["Q_list"]
    capacities = data["capacities"]
    initial = data["initial"]
    target = data["target"]
    weights = data["weights"]
    dist = _distances(data["points"])
    deltas = [initial[i] - target[i] for i in range(1, v + 1)]
    absolute = [abs(value) for value in deltas]
    active = [i for i in range(1, v + 1) if deltas[i - 1] != 0]
    surplus = [i for i in active if deltas[i - 1] > 0]
    deficit = [i for i in active if deltas[i - 1] < 0]
    imbalance_l1 = sum(absolute)
    total_surplus = sum(max(0, value) for value in deltas)
    total_deficit = sum(max(0, -value) for value in deltas)
    ratios = [initial[i] / target[i] for i in range(1, v + 1)]
    initial_gini = _gini(ratios)
    initial_penalty = sum(
        weights[i] * abs(ratios[i - 1] - 1.0)
        for i in range(1, v + 1)
    )
    initial_objective = initial_gini + 0.15 * initial_penalty
    fleet_capacity = sum(q)
    handling_lb = LOAD_SECONDS * imbalance_l1
    active_mst = _mst_weight(dist, [0, *active])
    support_pressure = (
        (active_mst + handling_lb) / (m * time_limit)
        if m * time_limit > 0.0 else math.inf
    )
    single_station_tightness = max((
        (2.0 * dist[0][i] + LOAD_SECONDS * absolute[i - 1]) / time_limit
        for i in active
    ), default=0.0)
    pair_count = len(active) * max(0, len(active) - 1)
    plausible_pairs = 0
    full_service_pairs = 0
    for left in active:
        for right in active:
            if left == right:
                continue
            travel = dist[0][left] + dist[left][right] + dist[right][0]
            if travel + LOAD_SECONDS + UNLOAD_SECONDS <= time_limit + 1e-9:
                plausible_pairs += 1
            service = LOAD_SECONDS * (
                absolute[left - 1] + absolute[right - 1])
            if travel + service <= time_limit + 1e-9:
                full_service_pairs += 1
    pair_density = plausible_pairs / pair_count if pair_count else 0.0
    full_pair_density = full_service_pairs / pair_count if pair_count else 0.0
    station_distances = [
        dist[i][j] for i in range(1, v + 1) for j in range(i + 1, v + 1)
    ]
    depot_distances = [dist[0][i] for i in range(1, v + 1)]
    hhi = (
        sum((value / imbalance_l1) ** 2 for value in absolute)
        if imbalance_l1 else 0.0
    )
    fleet_pressure = imbalance_l1 / max(1, fleet_capacity)
    active_fraction = len(active) / v
    sign_balance = (
        min(len(surplus), len(deficit)) / max(len(surplus), len(deficit))
        if surplus and deficit else 0.0
    )

    # The score uses only frozen instance data.  It intentionally combines
    # dimension, active support, amount/capacity pressure, duration pressure,
    # spatial heterogeneity, route-choice density, and vehicle assignment.
    # No solver timing, node, bound, incumbent, or winner field enters it.
    score = 100.0 * (
        0.12 * _clip((v - 8) / 4.0)
        + 0.16 * active_fraction
        + 0.15 * _clip(imbalance_l1 / max(1.0, 8.0 * v))
        + 0.13 * _clip(fleet_pressure / 1.5)
        + 0.18 * _clip(max(support_pressure, single_station_tightness) / 0.75)
        + 0.08 * _clip(_cv(station_distances) / 0.75)
        + 0.09 * _clip(pair_density / 0.80)
        + 0.09 * _clip((m - 1) / 2.0)
    )
    label = (
        "small-easy" if score < 60.0
        else "small-medium" if score < 78.0
        else "small-hard"
    )
    trivial_reasons: list[str] = []
    if len(active) < 3:
        trivial_reasons.append("fewer_than_three_active_stations")
    if not surplus or not deficit:
        trivial_reasons.append("missing_surplus_or_deficit_support")
    if imbalance_l1 < 2 * v:
        trivial_reasons.append("imbalance_l1_below_2V")
    if initial_objective <= 0.03:
        trivial_reasons.append("initial_objective_at_most_0.03")
    if plausible_pairs < 2:
        trivial_reasons.append("fewer_than_two_plausible_ordered_pairs")

    return {
        "V": v,
        "M": m,
        "Q": q[0] if len(set(q)) == 1 else ";".join(map(str, q)),
        "T": time_limit,
        "capacity_min": min(capacities[1:]),
        "capacity_max": max(capacities[1:]),
        "capacity_mean": statistics.fmean(capacities[1:]),
        "total_initial": sum(initial[1:]),
        "total_target": sum(target[1:]),
        "active_station_count": len(active),
        "active_fraction": active_fraction,
        "surplus_count": len(surplus),
        "deficit_count": len(deficit),
        "neutral_count": v - len(active),
        "sign_balance": sign_balance,
        "total_surplus": total_surplus,
        "total_deficit": total_deficit,
        "imbalance_l1": imbalance_l1,
        "imbalance_mean_active": (
            imbalance_l1 / len(active) if active else 0.0),
        "imbalance_max": max(absolute, default=0),
        "imbalance_cv": _cv([float(value) for value in absolute if value]),
        "imbalance_hhi": hhi,
        "fleet_capacity": fleet_capacity,
        "fleet_capacity_pressure": fleet_pressure,
        "handling_lower_bound_seconds": handling_lb,
        "active_support_mst_seconds": active_mst,
        "support_duration_pressure": support_pressure,
        "max_single_station_tightness": single_station_tightness,
        "plausible_ordered_pair_count": plausible_pairs,
        "plausible_ordered_pair_density": pair_density,
        "full_service_pair_density": full_pair_density,
        "mean_depot_distance_seconds": statistics.fmean(depot_distances),
        "max_depot_distance_seconds": max(depot_distances),
        "station_distance_cv": _cv(station_distances),
        "initial_gini": initial_gini,
        "initial_penalty": initial_penalty,
        "initial_objective_lambda_0_15": initial_objective,
        "difficulty_score": score,
        "difficulty_stratum": label,
        "structurally_nontrivial": not trivial_reasons,
        "structural_rejection_reasons": ";".join(trivial_reasons),
    }
