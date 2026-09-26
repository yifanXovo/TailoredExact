"""Exact-rational coefficient construction for Round 88 OT diagnostics.

All rows use the convention ``sum(coeff[name] * variable[name]) >= 0``.
This module has no solver dependency and never reads benchmark outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Mapping, Sequence


def state_name(i: int, y: int) -> str:
    return f"state_{i}_{y}"


def q_name(i: int, y: int) -> str:
    return f"state_g_{i}_{y}"


def h_name(i: int, j: int) -> str:
    return f"h_{i}_{j}"


def z_name(i: int) -> str:
    return f"zprod_{i}"


def ratio(y: int, target: int) -> Fraction:
    if target <= 0:
        raise ValueError("station target D must be positive")
    return Fraction(y, target)


def _add(coeff: dict[str, Fraction], name: str, amount: Fraction) -> None:
    coeff[name] = coeff.get(name, Fraction(0)) + amount
    if not coeff[name]:
        del coeff[name]


def _sign(value: float) -> int:
    return -1 if value < 0 else 1  # deterministic tie at zero


@dataclass(frozen=True)
class PairCut:
    kind: str
    i: int
    j: int
    coeff: dict[str, Fraction]
    signs: tuple[tuple[int, int], ...]
    intervals: tuple[Fraction, ...]
    a_values: tuple[float, ...]
    b_values: tuple[float, ...]
    support_identity: str

    def violation(self, values: Mapping[str, float]) -> float:
        return -sum(float(c) * values[name] for name, c in self.coeff.items())


def support_fingerprint(
    supports: Mapping[int, Sequence[int]], targets: Mapping[int, int],
    a: Fraction, b: Fraction,
) -> str:
    payload = {
        "a": str(a), "b": str(b),
        "stations": [(i, targets[i], list(supports[i])) for i in sorted(supports)],
    }
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def pair_cut(
    kind: str, i: int, j: int,
    supports: Mapping[int, Sequence[int]], targets: Mapping[int, int],
    a: Fraction, b: Fraction, values: Mapping[str, float],
) -> PairCut:
    if i >= j:
        raise ValueError("pairs require i<j")
    if kind not in {"B1", "B2"}:
        raise ValueError(kind)
    if kind == "B2" and not a < b:
        raise ValueError("B2 requires a strictly positive interval width")
    levels = sorted({ratio(y, targets[k]) for k in (i, j) for y in supports[k]})
    coeff: dict[str, Fraction] = {}
    signs: list[tuple[int, int]] = []
    intervals: list[Fraction] = []
    av: list[float] = []
    bv: list[float] = []
    for lo, hi in zip(levels, levels[1:]):
        delta = hi - lo
        if delta <= 0:
            raise AssertionError("support levels must be strictly ordered")
        a_value = sum(values[state_name(i, y)] for y in supports[i]
                      if ratio(y, targets[i]) <= lo) - sum(
            values[state_name(j, y)] for y in supports[j]
            if ratio(y, targets[j]) <= lo)
        b_value = sum(values[q_name(i, y)] for y in supports[i]
                      if ratio(y, targets[i]) <= lo) - sum(
            values[q_name(j, y)] for y in supports[j]
            if ratio(y, targets[j]) <= lo)
        if kind == "B1":
            alpha, beta = _sign(a_value), 0
            s_factor, q_factor = Fraction(alpha), Fraction(0)
        else:
            alpha = _sign(float(b) * a_value - b_value)
            beta = _sign(b_value - float(a) * a_value)
            s_factor = b * alpha - a * beta
            q_factor = Fraction(beta - alpha)
        for k, direction in ((i, 1), (j, -1)):
            for y in supports[k]:
                if ratio(y, targets[k]) <= lo:
                    _add(coeff, state_name(k, y), -delta * s_factor * direction)
                    if q_factor:
                        _add(coeff, q_name(k, y), -delta * q_factor * direction)
        signs.append((alpha, beta))
        intervals.append(delta)
        av.append(a_value)
        bv.append(b_value)
    _add(coeff, h_name(i, j), b - a if kind == "B2" else Fraction(1))
    return PairCut(kind, i, j, coeff, tuple(signs), tuple(intervals),
                   tuple(av), tuple(bv),
                   support_fingerprint({i: supports[i], j: supports[j]},
                                       targets, a, b))


def aggregate_cut(
    pair_rows: Sequence[PairCut], n: int,
    targets: Mapping[int, int], a: Fraction, b: Fraction,
) -> dict[str, Fraction]:
    kind = "B2" if a < b else "B1"
    if len(pair_rows) != n * (n - 1) // 2 or any(r.kind != kind for r in pair_rows):
        raise ValueError("aggregate requires every pair of the active endpoint family")
    expected_pairs = {(i, j) for i in range(1, n + 1) for j in range(i + 1, n + 1)}
    if {(r.i, r.j) for r in pair_rows} != expected_pairs:
        raise ValueError("aggregate pair collection is duplicated or incomplete")
    coeff: dict[str, Fraction] = {}
    for row in pair_rows:
        for name, value in row.coeff.items():
            if name != h_name(row.i, row.j):
                _add(coeff, name, value)
    scale = b - a if kind == "B2" else Fraction(1)
    for i in range(1, n + 1):
        _add(coeff, z_name(i), Fraction(n, targets[i]) * scale)
    return coeff


def row_value(coeff: Mapping[str, Fraction], values: Mapping[str, Fraction]) -> Fraction:
    return sum((c * values[name] for name, c in coeff.items()), Fraction(0))


def common_quantile_atoms(
    supports: Mapping[int, Sequence[int]], targets: Mapping[int, int],
    masses: Mapping[int, Mapping[int, Fraction]],
) -> list[tuple[Fraction, tuple[int, ...]]]:
    """Independent finite comonotone coupling of equal-mass marginals."""
    stations = sorted(supports)
    totals = [sum(masses[i].values(), Fraction(0)) for i in stations]
    if len(set(totals)) != 1:
        raise ValueError("endpoint-layer masses differ between stations")
    total = totals[0]
    if total == 0:
        return []
    breaks = {Fraction(0), total}
    ordered: dict[int, list[tuple[int, Fraction]]] = {}
    for i in stations:
        ordered[i] = sorted(masses[i].items(), key=lambda item: ratio(item[0], targets[i]))
        running = Fraction(0)
        for _, mass in ordered[i]:
            if mass < 0:
                raise ValueError("negative layer mass")
            running += mass
            breaks.add(running)
    points = sorted(breaks)
    atoms = []
    for lo, hi in zip(points, points[1:]):
        if hi == lo:
            continue
        midpoint = (lo + hi) / 2
        chosen = []
        for i in stations:
            running = Fraction(0)
            for y, mass in ordered[i]:
                running += mass
                if midpoint < running:
                    chosen.append(y)
                    break
            else:
                raise AssertionError("quantile breakpoint coverage failed")
        atoms.append((hi - lo, tuple(chosen)))
    return atoms
