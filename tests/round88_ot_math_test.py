"""Solver-free exact arithmetic qualification for Round 88 OT rows."""

from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from round88_ot_math import (aggregate_cut, common_quantile_atoms, h_name,
                             pair_cut, q_name, ratio, row_value, state_name,
                             support_fingerprint, z_name)


def point(supports, targets, s, q, g, h=None, z=None):
    values = {"G": g}
    for i, states in supports.items():
        for y in states:
            values[state_name(i, y)] = s[i].get(y, F(0))
            values[q_name(i, y)] = q[i].get(y, F(0))
        values[z_name(i)] = z[i] if z else sum(
            (F(y) * values[q_name(i, y)] for y in states), F(0))
    for i in supports:
        for j in supports:
            if i < j:
                values[h_name(i, j)] = (h or {}).get((i, j), F(0))
    return values


def as_float(values):
    return {k: float(v) for k, v in values.items()}


class OtMathTests(unittest.TestCase):
    def test_integer_validity_and_equality_over_heterogeneous_targets(self):
        supports = {1: [0, 2], 2: [0, 1, 2]}
        targets = {1: 1, 2: 2}
        a, b = F(1, 5), F(4, 5)
        witness = point(supports, targets,
                        {1: {0: F(1, 2), 2: F(1, 2)}, 2: {1: F(1)}},
                        {1: {0: F(1, 4), 2: F(1, 4)}, 2: {1: F(1, 2)}}, F(1, 2))
        rows = [pair_cut(k, 1, 2, supports, targets, a, b, as_float(witness))
                for k in ("B1", "B2")]
        for y, z, g in product(supports[1], supports[2], (a, (a + b) / 2, b)):
            distance = abs(ratio(y, targets[1]) - ratio(z, targets[2]))
            atom = point(supports, targets, {1: {y: F(1)}, 2: {z: F(1)}},
                         {1: {y: g}, 2: {z: g}}, g,
                         {(1, 2): distance})
            for row in rows:
                self.assertGreaterEqual(row_value(row.coeff, atom), 0)
            for kind in ("B1", "B2"):
                tight = pair_cut(kind, 1, 2, supports, targets, a, b, as_float(atom))
                self.assertEqual(row_value(tight.coeff, atom), 0)

    def test_b1_strict_over_mean_and_b2_strict_over_b1(self):
        a, b = F(0), F(1)
        supports = {1: [0, 2], 2: [1]}
        targets = {1: 1, 2: 1}
        p = point(supports, targets,
                  {1: {0: F(1, 2), 2: F(1, 2)}, 2: {1: F(1)}},
                  {1: {0: F(1, 4), 2: F(1, 4)}, 2: {1: F(1, 2)}}, F(1, 2))
        self.assertEqual(F(0), sum(F(y) * p[state_name(1, y)] for y in supports[1])
                         - p[state_name(2, 1)])
        b1 = pair_cut("B1", 1, 2, supports, targets, a, b, as_float(p))
        self.assertEqual(row_value(b1.coeff, p), -1)

        supports = {1: [0, 1], 2: [0, 1]}
        q = point(supports, targets,
                  {1: {0: F(1, 2), 1: F(1, 2)},
                   2: {0: F(1, 2), 1: F(1, 2)}},
                  {1: {0: F(0), 1: F(1, 2)},
                   2: {0: F(1, 2), 1: F(0)}}, F(1, 2))
        b1 = pair_cut("B1", 1, 2, supports, targets, a, b, as_float(q))
        b2 = pair_cut("B2", 1, 2, supports, targets, a, b, as_float(q))
        self.assertEqual(row_value(b1.coeff, q), 0)
        self.assertEqual(row_value(b2.coeff, q), -1)
        self.assertEqual(b2.signs, ((1, -1),))

    def test_equal_and_narrow_intervals_zero_layer_and_zero_inventory(self):
        supports = {1: [0, 1], 2: [0, 1]}
        targets = {1: 1, 2: 1}
        for a, b in ((F(2, 5), F(2, 5)),
                     (F(1, 2), F(1, 2) + F(1, 10**12)),
                     (F(0), F(1))):
            for g in (a, (a + b) / 2, b):
                p = point(supports, targets, {1: {0: F(1)}, 2: {0: F(1)}},
                          {1: {0: g}, 2: {0: g}}, g,
                          {(1, 2): F(0)})
                b1 = pair_cut("B1", 1, 2, supports, targets, a, b, as_float(p))
                self.assertEqual(row_value(b1.coeff, p), 0)
                if a == b:
                    with self.assertRaises(ValueError):
                        pair_cut("B2", 1, 2, supports, targets, a, b, as_float(p))
                else:
                    b2 = pair_cut("B2", 1, 2, supports, targets, a, b, as_float(p))
                    self.assertEqual(row_value(b2.coeff, p), 0)
                self.assertEqual(sum(F(y) * p[state_name(i, y)]
                                     for i in supports for y in supports[i]), 0)

    def test_local_row_rejects_outside_integer_and_support_reuse(self):
        supports = {1: [0, 1], 2: [0, 1]}
        targets = {1: 1, 2: 1}
        a, b = F(1, 2), F(1)
        local = point(supports, targets,
                      {1: {0: F(1, 2), 1: F(1, 2)},
                       2: {0: F(1, 2), 1: F(1, 2)}},
                      {1: {0: F(1, 4), 1: F(1, 2)},
                       2: {0: F(1, 2), 1: F(1, 4)}}, F(3, 4))
        row = pair_cut("B2", 1, 2, supports, targets, a, b, as_float(local))
        outside = point(supports, targets, {1: {0: F(1)}, 2: {1: F(1)}},
                        {1: {0: F(0)}, 2: {1: F(0)}}, F(0),
                        {(1, 2): F(1)})
        self.assertLess(row_value(row.coeff, outside), 0)
        widened = {1: [0, 1, 2], 2: [0, 1]}
        self.assertNotEqual(row.support_identity,
            support_fingerprint(widened, targets, a, b))

    def test_aggregate_exact_pair_coefficient_sum_and_joint_coupling(self):
        supports = {1: [0, 2], 2: [0, 2], 3: [0, 2]}
        targets = {1: 1, 2: 1, 3: 1}
        s = {i: {0: F(1, 2), 2: F(1, 2)} for i in supports}
        q = {1: {2: F(1, 2)},
             2: {0: F(1, 4), 2: F(1, 4)},
             3: {0: F(1, 2)}}
        p = point(supports, targets, s, q, F(1, 2))
        rows = [pair_cut("B2", i, j, supports, targets, F(0), F(1), as_float(p))
                for i in supports for j in supports if i < j]
        agg = aggregate_cut(rows, 3, targets, F(0), F(1))
        pair_names = (set().union(*(row.coeff for row in rows))
                      - {h_name(1, 2), h_name(1, 3), h_name(2, 3)})
        for name in pair_names:
            self.assertEqual(agg.get(name, F(0)),
                             sum((row.coeff.get(name, F(0)) for row in rows), F(0)))
        for i in supports:
            self.assertEqual(agg[z_name(i)], F(3))
        layer_a = {i: {y: s[i].get(y, F(0)) - q[i].get(y, F(0))
                       for y in supports[i]} for i in supports}
        layer_b = {i: {y: q[i].get(y, F(0)) for y in supports[i]}
                   for i in supports}
        atoms_a = common_quantile_atoms(supports, targets, layer_a)
        atoms_b = common_quantile_atoms(supports, targets, layer_b)
        self.assertEqual(sum((m for m, _ in atoms_a + atoms_b), F(0)), F(1))
        self.assertEqual([m for m, _ in atoms_a + atoms_b], [F(1, 4)] * 4)
        for i in supports:
            for y in supports[i]:
                self.assertEqual(
                    sum((mass for mass, route in atoms_a if route[i - 1] == y), F(0)),
                    layer_a[i][y])
                self.assertEqual(
                    sum((mass for mass, route in atoms_b if route[i - 1] == y), F(0)),
                    layer_b[i][y])
        expected = {(1, 2): F(1), (1, 3): F(2), (2, 3): F(1)}
        for (i, j), cost in expected.items():
            realized = sum((mass * abs(F(route[i - 1] - route[j - 1]))
                            for mass, route in atoms_a + atoms_b), F(0))
            self.assertEqual(realized, cost)
        # Raw aggregate has left side 3*(1+1/2+0), right side 4.
        self.assertEqual(row_value(agg, p), F(1, 2))

    def test_aggregate_locality_counterexample(self):
        supports = {1: [1], 2: [1], 3: [2]}
        targets = {i: 1 for i in supports}
        a, b = F(1, 2), F(1)
        # A valid member of the local sign family has RHS 7/6 for each
        # separated pair at this outside point; its two signs are opposite.
        # The aggregate replacement would assert 1 >= 7/3, which is false.
        outside_g = F(1, 6)
        scaled_h = (b - a) * F(2)
        rhs = F(0)
        for i, j in ((1, 2), (1, 3), (2, 3)):
            ai = F(supports[i][0], targets[i])
            aj = F(supports[j][0], targets[j])
            cdf_difference = F(0) if ai == aj else F(1) if ai < aj else F(-1)
            weighted_difference = outside_g * cdf_difference
            rhs += abs(b * cdf_difference - weighted_difference)
            rhs += abs(weighted_difference - a * cdf_difference)
        self.assertEqual(rhs, F(7, 3))
        self.assertLess(scaled_h - rhs, 0)
        self.assertNotEqual(support_fingerprint(supports, targets, a, b),
                            support_fingerprint(supports, targets, F(0), b))


if __name__ == "__main__":
    unittest.main()
