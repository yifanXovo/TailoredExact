"""Independent exact 2x2 transport oracle for the Round 88 OT cuts."""

from fractions import Fraction as F
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from round88_ot_math import h_name, pair_cut, q_name, row_value, state_name


def transport_2x2(left, right, left_levels, right_levels):
    """Enumerate the two vertices of a 2x2 transport polytope in Fractions."""
    total = sum(left, F(0))
    if total != sum(right, F(0)):
        raise ValueError("marginals do not have equal mass")
    low = max(F(0), left[0] + right[0] - total)
    high = min(left[0], right[0])
    candidates = []
    for corner in (low, high):
        plan = ((corner, left[0] - corner),
                (right[0] - corner, total - left[0] - right[0] + corner))
        cost = sum((plan[i][j] * abs(left_levels[i] - right_levels[j])
                    for i in range(2) for j in range(2)), F(0))
        candidates.append((cost, plan))
    return min(candidates)


def composition(total, rng):
    cuts = sorted((0, total, rng.randrange(total + 1), rng.randrange(total + 1),
                   rng.randrange(total + 1)))
    return [cuts[i + 1] - cuts[i] for i in range(4)]


class IndependentOracleTests(unittest.TestCase):
    def test_random_fractional_two_endpoint_transport(self):
        rng = random.Random(8802)
        supports = {1: [0, 2], 2: [1, 3]}
        targets = {1: 1, 2: 2}
        levels = [[F(0), F(2)], [F(1, 2), F(3, 2)]]
        for a, b in ((F(0), F(1)), (F(1, 5), F(4, 5)),
                     (F(1, 2), F(1, 2) + F(1, 1000)),
                     (F(2, 5), F(2, 5))):
            for trial in range(100):
                lower_units = (0, 6, 12, rng.randrange(13))[trial % 4]
                upper_units = 12 - lower_units
                low_plan = composition(lower_units, rng)
                high_plan = composition(upper_units, rng)
                s = {1: [F(low_plan[0] + low_plan[1] + high_plan[0] + high_plan[1], 12),
                         F(low_plan[2] + low_plan[3] + high_plan[2] + high_plan[3], 12)],
                     2: [F(low_plan[0] + low_plan[2] + high_plan[0] + high_plan[2], 12),
                         F(low_plan[1] + low_plan[3] + high_plan[1] + high_plan[3], 12)]}
                lo = {1: [F(low_plan[0] + low_plan[1], 12), F(low_plan[2] + low_plan[3], 12)],
                      2: [F(low_plan[0] + low_plan[2], 12), F(low_plan[1] + low_plan[3], 12)]}
                hi = {i: [s[i][k] - lo[i][k] for k in range(2)] for i in (1, 2)}
                q = {i: [a * lo[i][k] + b * hi[i][k] for k in range(2)] for i in (1, 2)}
                values = {h_name(1, 2): F(0)}
                for i in (1, 2):
                    for k, y in enumerate(supports[i]):
                        values[state_name(i, y)] = s[i][k]
                        values[q_name(i, y)] = q[i][k]
                floats = {name: float(value) for name, value in values.items()}
                b1_cost, _ = transport_2x2(s[1], s[2], levels[0], levels[1])
                b1_row = pair_cut("B1", 1, 2, supports, targets, a, b, floats)
                self.assertEqual(-row_value(b1_row.coeff, values), b1_cost)
                if a < b:
                    low_cost, _ = transport_2x2(lo[1], lo[2], levels[0], levels[1])
                    high_cost, _ = transport_2x2(hi[1], hi[2], levels[0], levels[1])
                    b2_row = pair_cut("B2", 1, 2, supports, targets, a, b, floats)
                    self.assertEqual(-row_value(b2_row.coeff, values) / (b - a),
                                     low_cost + high_cost)
                else:
                    self.assertEqual(q[1], [a * x for x in s[1]])


if __name__ == "__main__":
    unittest.main()
