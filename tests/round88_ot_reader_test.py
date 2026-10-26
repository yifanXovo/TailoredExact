"""Read-only Gurobi LP API qualification; no Optimize is called."""

from fractions import Fraction as F
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import gurobipy as gp
from gurobipy import GRB

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from round88_ot_diagnostic import arms_comparable, audit_model, load_model, reliable


class ReaderTests(unittest.TestCase):
    def test_partial_arm_status_never_claims_comparable_results(self):
        arms = {name: {"status_code": GRB.OPTIMAL}
                for name in ("B1", "B2", "B1+B2", "aggregate")}
        self.assertTrue(arms_comparable(arms, False))
        arms["aggregate"]["status_code"] = GRB.TIME_LIMIT
        self.assertFalse(arms_comparable(arms, False))
        arms["aggregate"]["status_code"] = GRB.OPTIMAL
        arms["B2"] = {"status": "not_applicable_a_equals_b"}
        self.assertTrue(arms_comparable(arms, True))
        self.assertFalse(arms_comparable(arms, False))

    def test_narrow_interval_numerical_guard_rejects_weak_signal(self):
        coeff = {"q": F(1), "s": -F(1, 2)}
        selected, reason, margin = reliable(coeff, F(1, 10**6), 1e-5,
                                            {"q": 0.5, "s": 1.0}, 1e-6)
        self.assertFalse(selected)
        self.assertEqual(reason, "violation_below_numerical_margin")
        self.assertGreater(margin, 1e-5)

    def test_lp_roundtrip_structure_and_rejections_without_optimize(self):
        a, b = F(1, 2), F(1)
        instance = {"n": 2, "vehicles": 1,
                    "targets": {1: 1, 2: 1}, "weights": {1: 1.0, 2: 1.0},
                    "capacities": {1: 1, 2: 1}}
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()
        model = gp.Model(env=env)
        g = model.addVar(lb=float(a), ub=float(b), name="G")
        h = model.addVar(lb=0, ub=2, name="h_1_2")
        e = {}
        r = {}
        z = {}
        for i in (1, 2):
            s = [model.addVar(lb=0, ub=1, vtype=GRB.BINARY, name=f"state_{i}_{y}")
                 for y in (0, 1)]
            q = [model.addVar(lb=0, ub=1, name=f"state_g_{i}_{y}")
                 for y in (0, 1)]
            z[i] = model.addVar(lb=0, ub=1, name=f"zprod_{i}")
            y_var = model.addVar(lb=0, ub=1, vtype=GRB.INTEGER, name=f"Y_{i}")
            r[i] = model.addVar(lb=0, ub=1, name=f"r_{i}")
            e[i] = model.addVar(lb=0, ub=1, name=f"e_{i}")
            model.addConstr(s[0] + s[1] == 1)
            model.addConstr(y_var - s[1] == 0)
            model.addConstr(r[i] - y_var == 0)
            model.addConstr(q[0] + q[1] - g == 0)
            model.addConstr(z[i] - q[1] == 0)
            for y in (0, 1):
                model.addConstr(q[y] - float(a) * s[y] >= 0)
                model.addConstr(q[y] - float(b) * s[y] <= 0)
        model.addConstr(h - r[1] + r[2] >= 0)
        model.addConstr(h + r[1] - r[2] >= 0)
        model.addConstr(2 * z[1] + 2 * z[2] - h >= 0)
        model.addConstr(g + e[1] + e[2] <= 3)
        model.setObjective(g + e[1] + e[2], GRB.MINIMIZE)
        model.update()
        with TemporaryDirectory() as tmp:
            lp = Path(tmp) / "synthetic_identity.lp"
            model.write(str(lp))
            read = load_model(lp)
            audit = audit_model(read, instance, a, b, 3, 1)
            self.assertEqual(audit["support"], {"1": [0, 1], "2": [0, 1]})
            self.assertEqual(F(audit["effective_gamma_l"]), F.from_float(float(a)))
            self.assertEqual(F(audit["effective_gamma_u"]), F.from_float(float(b)))
            with self.assertRaisesRegex(ValueError, "G bounds"):
                audit_model(read, instance, a + F(1, 10**13), b, 3, 1)
            read.getVarByName("zprod_1").UB = 2
            read.update()
            with self.assertRaisesRegex(ValueError, "type or bounds"):
                audit_model(read, instance, a, b, 3, 1)
            read.getVarByName("zprod_1").UB = 1
            read.getVarByName("G").Obj = 2
            read.update()
            with self.assertRaisesRegex(ValueError, "objective"):
                audit_model(read, instance, a, b, 3, 1)


if __name__ == "__main__":
    unittest.main()
