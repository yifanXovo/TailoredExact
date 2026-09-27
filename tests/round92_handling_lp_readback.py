"""Zero-Optimize G1 check of the actual parsed Round92 canonical LP artifacts.

Run after Round92HandlingIntegrationTests OUT_DIR, in the qualified local
Gurobi Python environment. This imports and reads LP files but never solves.
"""
from __future__ import annotations

import collections
import math
import sys
from pathlib import Path

import gurobipy as gp


def require(ok: bool, why: str) -> None:
    if not ok:
        raise AssertionError(why)


def row_terms(model: gp.Model, constr: gp.Constr) -> dict[str, float]:
    row = model.getRow(constr)
    return {row.getVar(i).VarName: row.getCoeff(i) for i in range(row.size())}


def signature(model: gp.Model, constr: gp.Constr) -> tuple:
    return (
        constr.Sense,
        constr.RHS,
        tuple(sorted(row_terms(model, constr).items())),
    )


def main(directory: Path) -> None:
    with gp.Env(empty=True) as env:
        env.setParam("OutputFlag", 0)
        env.start()
        off = gp.read(str(directory / "off.lp"), env=env)
        on = gp.read(str(directory / "on.lp"), env=env)
        off.update()
        on.update()
        require(on.NumConstrs == off.NumConstrs + 2, "row count is not +M")
        require(on.NumVars == off.NumVars, "candidate changed column set")
        require(off.ModelSense == on.ModelSense == gp.GRB.MINIMIZE,
                "objective sense changed")
        for old in off.getVars():
            new = on.getVarByName(old.VarName)
            require(new is not None and
                    (old.LB, old.UB, old.VType, old.Obj) ==
                    (new.LB, new.UB, new.VType, new.Obj),
                    f"column domain/objective changed: {old.VarName}")
        g = on.getVarByName("G")
        require(g is not None and g.VType == gp.GRB.CONTINUOUS and
                g.LB == 0 and g.UB == 17.0 / 60.0,
                "G interval changed")
        for k in range(2):
            for i in range(1, 6):
                p = on.getVarByName(f"p_{k}_{i}")
                x = on.getVarByName(f"x_{k}_0_{i}")
                conn = on.getVarByName(f"conn_{k}_0_{i}")
                require(p is not None and p.VType == gp.GRB.INTEGER and p.LB == 0,
                        "pickup integer/nonnegative domain missing")
                require(x is not None and x.VType == gp.GRB.BINARY and
                        x.LB == 0 and x.UB == 1,
                        "activation binary domain missing")
                require(conn is not None and conn.VType == gp.GRB.CONTINUOUS,
                        "original F0 connectivity column missing")
        candidate = []
        for c in on.getConstrs():
            terms = row_terms(on, c)
            for k in range(2):
                expected = {f"p_{k}_{i}": 1.0 for i in range(1, 6)}
                expected.update({f"x_{k}_0_{i}": -2.0 for i in range(1, 6)})
                if terms == expected and c.Sense == "<" and c.RHS == 0:
                    candidate.append((k, c))
                    break
        require(sorted(k for k, _ in candidate) == [0, 1],
                "one rounded handling/activation row per vehicle missing")
        for k, c in candidate:
            duration = on.getConstrByName(f"c{int(c.ConstrName[1:]) - 1}")
            require(duration is not None and duration.Sense == "<" and
                    duration.RHS == 5.0 and
                    row_terms(on, duration) ==
                    {f"p_{k}_{i}": 2.0 for i in range(1, 6)},
                    "candidate proof does not match its original duration row")
        actual_without_candidate = collections.Counter(
            signature(on, c) for c in on.getConstrs())
        for _, c in candidate:
            actual_without_candidate[signature(on, c)] -= 1
        require(actual_without_candidate ==
                collections.Counter(signature(off, c) for c in off.getConstrs()),
                "original objective/cutoff/F0/duration rows changed")
        cutoff = {"G": 1.0, **{f"e_{i}": 0.15 for i in range(1, 6)}}
        require(any(c.Sense == "<" and math.isclose(c.RHS, 17 / 60) and
                    all(math.isclose(row_terms(on, c).get(v, 0), value,
                                     rel_tol=0, abs_tol=1e-15)
                        for v, value in cutoff.items()) and
                    len(row_terms(on, c)) == len(cutoff)
                    for c in on.getConstrs()),
                "verified incumbent cutoff row missing")
        physical = gp.read(str(directory / "physical_delta.lp"), env=env)
        physical.update()
        physical_rows = []
        for c in physical.getConstrs():
            terms = row_terms(physical, c)
            if (terms.get("p_0_1") == 1.0 and terms.get("p_0_2") == 1.0 and
                    terms.get("x_0_0_1", 0.0) <= -2.0 and
                    terms.get("x_0_0_2", 0.0) <= -2.0 and
                    len(terms) == 4 and c.Sense == "<" and c.RHS == 0.0):
                physical_rows.append(c)
        require(len(physical_rows) == 1,
                "dyadic physical P=2 route excluded by serialized candidate row")
        preceding = physical.getConstrByName(
            f"c{int(physical_rows[0].ConstrName[1:]) - 1}")
        require(preceding is not None and preceding.Sense == "<" and
                preceding.RHS == 2.0 - 2.0**-42 and
                row_terms(physical, preceding) == {"p_0_1": 1.0,
                                                    "p_0_2": 1.0},
                "dyadic canonical duration identity differs from original writer")
    print("Round92 parsed canonical LP identity/row/domain readback PASS")


if __name__ == "__main__":
    require(len(sys.argv) == 2, "usage: round92_handling_lp_readback.py OUT_DIR")
    main(Path(sys.argv[1]))
