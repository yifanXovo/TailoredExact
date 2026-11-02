"""Independent Round146 pre-review: exact arithmetic only, no solver imports."""
from fractions import Fraction as F
from pathlib import Path
import gzip
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT / "results/unified_exact_round145"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def denominator(c, supports, bm, bp, fixed=None):
    low = {i: min(ys) for i, ys in supports.items()}
    high = {i: max(ys) for i, ys in supports.items()}
    if fixed:
        i, y = fixed
        low[i] = high[i] = y
    minimum, maximum = sum(low.values()), sum(high.values())
    bm, bp = max(bm, minimum), min(bp, maximum)
    if bm > bp:
        return None
    def fill(total, reverse):
        value = sum((c[i] * low[i] for i in c), F(0))
        remaining = total - minimum
        for i in sorted(c, key=lambda i: (c[i], i), reverse=reverse):
            take = min(remaining, high[i] - low[i])
            value += c[i] * take
            remaining -= take
        assert remaining == 0
        return value
    return fill(bm, False), fill(bp, True)

def point(role, compact=False):
    folder = OLD / "LP" / (role + "_joint")
    scope_path = folder / "scope.json"
    solution_path = (OLD / "compact" / role if compact else folder) / "solution.json.gz"
    scope = json.loads(scope_path.read_text())["RN"]
    c = {int(i): F(x) for i, x in scope["c_binary64"].items()}
    support = {int(i): ys for i, ys in scope["supports"].items()}
    bm, bp = scope["Bminus"], scope["B"]
    sl, su = denominator(c, support, bm, bp)
    assert sl == F(scope["S_L_exact"]) and su == F(scope["S_U_exact"])
    assert sl > 0
    with gzip.open(solution_path, "rt") as f:
        x = {name: F(v) for name, v in json.load(f).items()}
    n = len(c)
    state_low = state_high = global_low = global_high = F(0)
    coefficients = 0
    for i, ys in support.items():
        for y in ys:
            d = denominator(c, support, bm, bp, (i, y))
            a = b = F(0)
            if d is not None:
                dl, du = d
                assert sl <= dl <= du <= su
                a, b = max(0, F(1, n)-c[i]*y/dl), max(0, c[i]*y/du-F(1, n))
            ag, bg = max(0, F(1, n)-c[i]*y/sl), max(0, c[i]*y/su-F(1, n))
            if d is not None:
                assert a >= ag and b >= bg
            value = x["state_%s_%s" % (i, y)]
            state_low += a*value
            state_high += b*value
            global_low += ag*value
            global_high += bg*value
            coefficients += 1
    margins = {"state_low": state_low-x["G"], "state_high": state_high-x["G"],
               "global_low": global_low-x["G"], "global_high": global_high-x["G"]}
    return {"role": role, "point": "compact" if compact else "joint",
            "scope_sha256": sha(scope_path), "solution_sha256": sha(solution_path),
            "coefficient_states": coefficients, "G": float(x["G"]),
            "violation_exact": {k: str(v) for k, v in margins.items()},
            "violation": {k: float(v) for k, v in margins.items()},
            "zero_selector_weight": float(sum(x["state_%s_0" % i] for i in support if 0 in support[i])),
            "saved_values_renormalized": False}

if __name__ == "__main__":
    result = {"PASS": True, "Optimize_calls": 0, "Native_loads": 0,
              "scope": "independent exact recheck of selected supplied saved-point claims; not production qualification",
              "points": [point("K-20-S"), point("K-35-U"), point("R-X20-S-T1"), point("R-X20-S-T1", True)]}
    output = Path(__file__).with_name("independent_saved_point_check.json")
    output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"PASS": result["PASS"], "Optimize_calls": 0,
                      "points": [{k: p[k] for k in ["role", "point", "violation", "zero_selector_weight"]} for p in result["points"]]}, indent=2))
