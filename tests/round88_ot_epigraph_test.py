"""Solver-free independent Fraction oracles for the sparse OT epigraph."""

from __future__ import annotations

from fractions import Fraction as F
import itertools
import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import round88_ot_epigraph as epi
from round88_ot_epigraph import evaluate, make_plan
from round88_ot_math import q_name


def direct_pair(supports, targets, i, j, s, q, a, b, arm):
    """Re-enumerate every original state at each threshold, without prefixes."""
    levels = sorted({F(y, targets[k]) for k in (i, j) for y in supports[k]})
    pieces = []
    for lo, hi in zip(levels, levels[1:]):
        A = sum((s[(i, y)] for y in supports[i] if F(y, targets[i]) <= lo), F(0))
        A -= sum((s[(j, y)] for y in supports[j] if F(y, targets[j]) <= lo), F(0))
        B = sum((q[(i, y)] for y in supports[i] if F(y, targets[i]) <= lo), F(0))
        B -= sum((q[(j, y)] for y in supports[j] if F(y, targets[j]) <= lo), F(0))
        pieces.append((hi-lo, A, B))
    if arm == "B1":
        return sum((d*abs(A) for d, A, _ in pieces), F(0)), pieces
    return sum((d*(abs(b*A-B)+abs(B-a*A)) for d, A, B in pieces), F(0))/(b-a), pieces


def direct_sign_maximum(pieces, a, b, arm):
    """Independent exponential oracle for the original complete signed family."""
    if arm == "B1":
        return max((sum((d*sign*A for (d, A, _), sign in zip(pieces, signs)), F(0))
                    for signs in itertools.product((-1, 1), repeat=len(pieces))), default=F(0))
    return max((sum((d*(alpha*(b*A-B)+beta*(B-a*A))
                     for (d, A, B), alpha, beta in zip(pieces, signs[::2], signs[1::2])), F(0))
                for signs in itertools.product((-1, 1), repeat=2*len(pieces))),
               default=F(0))/(b-a)


def direct_lift(plan, supports, targets, s, q, h):
    """Construct a feasible lift from direct CDF sums, not the row builder."""
    values = {f"state_{i}_{y}": value for (i, y), value in s.items()}
    values.update({q_name(i, y): value for (i, y), value in q.items()})
    values["G"] = sum(q[(min(supports), y)] for y in supports[min(supports)])
    for (i, j), value in h.items():
        values[f"h_{i}_{j}"] = value
    for i, ys in supports.items():
        ordered = sorted(ys, key=lambda y: F(y, targets[i]))
        for k in range(1, len(ordered)):
            values[f"otepi_C_{i}_{k}"] = sum((s[(i, y)] for y in ordered[:k]), F(0))
            if plan.arm == "B2":
                values[f"otepi_Q_{i}_{k}"] = sum((q[(i, y)] for y in ordered[:k]), F(0))
    for key, levels in plan.pair_levels.items():
        i, j = map(int, key.split("_"))
        for l, lo in enumerate(levels[:-1], 1):
            A = sum((s[(i, y)] for y in supports[i] if F(y, targets[i]) <= lo), F(0))
            A -= sum((s[(j, y)] for y in supports[j] if F(y, targets[j]) <= lo), F(0))
            B = sum((q[(i, y)] for y in supports[i] if F(y, targets[i]) <= lo), F(0))
            B -= sum((q[(j, y)] for y in supports[j] if F(y, targets[j]) <= lo), F(0))
            if plan.arm == "B1":
                values[f"otepi_v_{i}_{j}_{l}"] = abs(A)
            else:
                a, b = plan.domain
                values[f"otepi_u_{i}_{j}_{l}"] = abs(b*A-B)
                values[f"otepi_v_{i}_{j}_{l}"] = abs(B-a*A)
    return values


def feasible(plan, values):
    return all((evaluate(r, values) == 0 if r.sense == "=" else
                evaluate(r, values) >= 0) for r in plan.rows)


class SparseEpigraphTest(unittest.TestCase):
    def setUp(self):
        # Ratio 1/2 occurs twice across stations; 0 is another tied level.
        self.supports = {1: (0, 1, 2), 2: (0, 2, 4), 3: (0, 1)}
        self.targets = {1: 2, 2: 4, 3: 3}

    def test_exact_projection_and_integer_validity(self):
        a, b = F(1, 4), F(3, 4)
        for arm in ("B1", "B2"):
            plan = make_plan(arm, self.supports, self.targets, a, b)
            self.assertEqual(plan.pair_levels["1_2"], (F(0), F(1, 2), F(1)))
            for G in (a, F(1, 2), b):
                for choices in itertools.product(*self.supports.values()):
                    s = {(i, y): F(y == choices[i-1])
                         for i in self.supports for y in self.supports[i]}
                    q = {key: G*value for key, value in s.items()}
                    h = {}
                    for i, j in itertools.combinations(self.supports, 2):
                        bound, pieces = direct_pair(self.supports, self.targets, i, j,
                                                    s, q, a, b, arm)
                        self.assertEqual(bound, direct_sign_maximum(pieces, a, b, arm))
                        physical = abs(F(choices[i-1], self.targets[i])-
                                       F(choices[j-1], self.targets[j]))
                        self.assertEqual(bound, physical)
                        h[(i, j)] = bound
                    lifted = direct_lift(plan, self.supports, self.targets, s, q, h)
                    self.assertTrue(feasible(plan, lifted))
                    pair = (1, 3)
                    if h[pair] > 0:
                        lifted[f"h_{pair[0]}_{pair[1]}"] -= F(1, 1000)
                        self.assertFalse(feasible(plan, lifted))

    def test_fractional_original_point_and_hand_calculated_toy(self):
        supports = {1: (0, 1), 2: (0, 2)}
        targets = {1: 2, 2: 4}  # equal support levels 0,1/2; one interval.
        a, b, G = F(0), F(1), F(1, 2)
        s = {(1, 0): F(1, 4), (1, 1): F(3, 4),
             (2, 0): F(3, 4), (2, 2): F(1, 4)}
        q = {(1, 0): F(1, 8), (1, 1): F(3, 8),
             (2, 0): F(3, 8), (2, 2): F(1, 8)}
        for arm in ("B1", "B2"):
            plan = make_plan(arm, supports, targets, a, b)
            required, pieces = direct_pair(supports, targets, 1, 2, s, q, a, b, arm)
            self.assertEqual(pieces, [(F(1, 2), F(-1, 2), F(-1, 4))])
            self.assertEqual(required, F(1, 4))
            self.assertEqual(required, direct_sign_maximum(pieces, a, b, arm))
            values = direct_lift(plan, supports, targets, s, q, {(1, 2): required})
            self.assertEqual(values["G"], G)
            self.assertTrue(feasible(plan, values))
            values["h_1_2"] = F(0)
            self.assertFalse(feasible(plan, values))
            self.assertTrue(feasible(type("P", (), {"rows": plan.rows[:-1]})(), values))

    def test_fractional_perspective_coupling_not_proportional_to_s(self):
        supports = {1: (0, 1), 2: (0, 2)}
        targets = {1: 2, 2: 4}
        a, b = F(0), F(1)
        s = {(1, 0): F(1, 2), (1, 1): F(1, 2),
             (2, 0): F(1, 2), (2, 2): F(1, 2)}
        q = {(1, 0): F(1, 10), (1, 1): F(2, 5),
             (2, 0): F(1, 5), (2, 2): F(3, 10)}
        self.assertEqual(sum(q[(1, y)] for y in supports[1]), F(1, 2))
        self.assertEqual(sum(q[(2, y)] for y in supports[2]), F(1, 2))
        self.assertTrue(all(a*s[key] <= value <= b*s[key] for key, value in q.items()))
        for arm, hand_bound in (("B1", F(0)), ("B2", F(1, 10))):
            plan = make_plan(arm, supports, targets, a, b)
            bound, pieces = direct_pair(supports, targets, 1, 2, s, q, a, b, arm)
            self.assertEqual(bound, hand_bound)
            self.assertEqual(bound, direct_sign_maximum(pieces, a, b, arm))
            self.assertTrue(feasible(plan, direct_lift(plan, supports, targets,
                                                        s, q, {(1, 2): bound})))

    def test_full_prefix_constant_and_zero_width(self):
        supports = {1: (0,), 2: (1,)}
        targets = {1: 1, 2: 1}
        plan = make_plan("B1", supports, targets, F(1, 2), F(1, 2))
        self.assertEqual(plan.counts["new_columns"], 1)
        self.assertEqual(plan.counts["new_rows"], 3)
        self.assertEqual(plan.pair_levels["1_2"], (F(0), F(1)))
        s = {(1, 0): F(1), (2, 1): F(1)}
        q = {key: F(1, 2) for key in s}
        values = direct_lift(plan, supports, targets, s, q, {(1, 2): F(1)})
        self.assertTrue(feasible(plan, values))
        self.assertIn(F(1), [abs(r.rhs) for r in plan.rows])
        with self.assertRaises(ValueError):
            make_plan("B2", supports, targets, F(1, 2), F(1, 2))

    def test_b2_full_q_prefix_is_original_G_with_exact_rhs(self):
        supports = {1: (0,), 2: (0, 1)}
        targets = {1: 1, 2: 1}
        a, b = F(1, 4), F(3, 4)
        plan = make_plan("B2", supports, targets, a, b)
        positive = next(r for r in plan.rows if r.name == "otepi_u_pos_1_2_1")
        # At threshold zero: A=1-C_2, B=G-Q_2. Thus u-bA+B>=0.
        self.assertEqual(positive.rhs, b)
        self.assertEqual(positive.coefficients, {
            "otepi_u_1_2_1": F(1), "otepi_C_2_1": b,
            "G": F(1), "otepi_Q_2_1": F(-1)})
        negative = next(r for r in plan.rows if r.name == "otepi_u_neg_1_2_1")
        self.assertEqual(negative.rhs, -b)
        self.assertEqual(negative.coefficients, {
            "otepi_u_1_2_1": F(1), "otepi_C_2_1": -b,
            "G": F(-1), "otepi_Q_2_1": F(1)})

    def test_prefix_recurrence_detects_wrong_original_state(self):
        plan = make_plan("B2", self.supports, self.targets, F(0), F(1))
        G = F(1, 2)
        s = {(i, y): F(y == self.supports[i][0])
             for i in self.supports for y in self.supports[i]}
        q = {key: G*value for key, value in s.items()}
        h = {(i, j): direct_pair(self.supports, self.targets, i, j,
                                  s, q, F(0), F(1), "B2")[0]
             for i, j in itertools.combinations(self.supports, 2)}
        values = direct_lift(plan, self.supports, self.targets, s, q, h)
        self.assertTrue(feasible(plan, values))
        values["otepi_C_1_1"] += F(1, 4)
        self.assertFalse(feasible(plan, values))
        self.assertNotEqual(next(r for r in plan.rows if r.name == "otepi_rec_C_1_1").rhs,
                            F(1, 2))

    def test_domain_support_and_count_guards(self):
        with self.assertRaises(ValueError):
            make_plan("B2", self.supports, self.targets, F(3, 4), F(1, 4))
        with self.assertRaises(ValueError):
            make_plan("B1", {1: (0, 0), 2: (1,)}, {1: 1, 2: 1}, F(0), F(1))
        with self.assertRaises(ValueError):
            make_plan("B1", self.supports, {1: 2, 2: 4}, F(0), F(1))
        single = make_plan("B2", {1: (1,), 2: (2,)},
                           {1: 2, 2: 4}, F(0), F(1))
        self.assertEqual(single.pair_levels["1_2"], (F(1, 2),))
        self.assertEqual(single.counts["new_columns"], 0)
        self.assertEqual(single.counts["new_rows"], 0)
        for arm in ("B1", "B2"):
            plan = make_plan(arm, self.supports, self.targets, F(1, 5), F(4, 5))
            n = sum(len(v)-1 for v in self.supports.values())
            p = sum(max(0, len(levels)-1) for levels in plan.pair_levels.values())
            k = sum(len(levels) > 1 for levels in plan.pair_levels.values())
            self.assertEqual((plan.N, plan.P, plan.K), (n, p, k))
            self.assertEqual(plan.counts["new_columns"], (n+p)*(2 if arm == "B2" else 1))
            self.assertEqual(plan.counts["new_rows"],
                             (2*n+4*p+k) if arm == "B2" else (n+2*p+k))
            self.assertLessEqual(plan.counts["new_nonzeros"],
                                 plan.counts["nonzero_upper_bound"])

    def test_malformed_child_result_still_gets_supervision_receipt(self):
        for malformed in (["not-a-dict"], {}, {"status": 1}, {"status": "unregistered"}):
            with self.subTest(malformed=malformed), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                manifest = root / "manifest.json"
                manifest.write_text("{}\n", encoding="utf-8")
                out = root / "arm"

                def spawn(*args, **kwargs):
                    child = out / "diagnostic"
                    child.mkdir()
                    (child / "result.json").write_text(json.dumps(malformed), encoding="utf-8")
                    fake = mock.Mock()
                    fake.returncode = 0
                    fake.pid = 1001
                    return fake

                with (mock.patch.object(epi, "require_lease"),
                      mock.patch.object(epi, "verify_prepared", return_value=({}, {})),
                      mock.patch.object(epi.subprocess, "Popen", side_effect=spawn),
                      mock.patch.object(epi, "_WindowsJob", return_value=mock.Mock()),
                      mock.patch.object(epi, "_wait_with_deadline", return_value=("", "", False))):
                    code = epi.supervise(manifest, "F2-root", "B1", out)
                receipt = json.loads((out / "supervision.json").read_text(encoding="utf-8"))
                self.assertEqual(code, 125)
                self.assertEqual(receipt["status"], "invalid_or_unknown_diagnostic_failure")
                self.assertEqual(receipt["manifest_sha256_before"],
                                 receipt["manifest_sha256_after"])


if __name__ == "__main__":
    unittest.main()
