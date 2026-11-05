"""Independent saved-point readback; no solver import, Native read or Optimize."""
from pathlib import Path
from fractions import Fraction as F
import gzip
import hashlib
import json
import math
import time

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "results/unified_exact_round154"


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def true_f(scope, stock):
    ss = scope["stations"]
    assert len(stock) == len(ss)
    assert all(isinstance(y, int) and y in s["support"] for s, y in zip(ss, stock))
    assert scope["Bminus"] <= sum(stock) <= scope["B"]
    ratios = [F(s["c"]) * y for s, y in zip(ss, stock)]
    total = sum(ratios, F(0))
    if total:
        g = sum((abs(a - b) for j, a in enumerate(ratios) for b in ratios[j + 1:]), F(0)) / (len(ss) * total)
    else:
        assert not any(stock)
        g = F(0)
    assert g <= F(scope["gamma_U"])
    return max(F(scope["gamma_L"]), g)


def check(phase, solve_name, point_name, expected_columns):
    folder = OUT / "coupled" / phase
    solve = folder / solve_name
    result = read(folder / "result.json")
    record = read(solve / "call.json")
    returned = read(solve / "return.json")
    saved = gz(folder / point_name)
    solution = gz(solve / "solution.json.gz")
    point, scope, columns = saved["point"], result["scope"], result["columns"]
    assert point == solution, "final saved witness must be the actual returned solution"
    assert returned["Status"] == 2 and returned["solution_count"] >= 1
    assert record["Seed"] == 0 and record["Threads"] == 1 and record["all_original_variables_free"]
    assert len(columns) == expected_columns and len({tuple(y) for y in columns}) == expected_columns
    names = {k for k in point if k.startswith("hull_lambda_")}
    assert names == {f"hull_lambda_{j:05}" for j in range(expected_columns)}
    assert len(point) == record["columns"] and not any(k.startswith("hull_art_") for k in point)
    qual = saved["check"]
    assert qual["qualified"] and qual["column_count"] == expected_columns
    assert max(qual["constraints"], qual["bounds"]) <= 1e-6
    assert not result["refresh_required"]
    assert result["last_columns_evaluated"]

    weights = [point[f"hull_lambda_{j:05}"] for j in range(expected_columns)]
    mass = math.fsum(weights)
    negative = math.fsum(max(0.0, -w) for w in weights)
    assert abs(mass - 1) <= 1e-8 and negative <= 1e-8
    marginals = {(s["i"], y): [] for s in scope["stations"] for y in s["support"]}
    expected = F(0)
    nonzero = []
    for stock, weight in zip(columns, weights):
        if not weight:
            continue
        value = true_f(scope, stock)
        expected += F(weight) * value
        nonzero.append((stock, weight, value))
        for s, y in zip(scope["stations"], stock):
            marginals[s["i"], y].append(weight)
    mismatch = max(abs(math.fsum(values) - point[f"state_{i}_{y}"])
                   for (i, y), values in marginals.items())
    completion = F(point["G"]) - expected
    assert mismatch <= 1e-8 and completion >= 0
    assert abs(mass - qual["mass"]) <= 1e-12
    assert F(qual["true_expected_f_exact"]) == expected
    assert F(qual["true_completion_slack_exact"]) == completion
    indices = {tuple(stock): j for j, stock in enumerate(columns)}
    for stock in saved["stocks"]:
        j = indices[tuple(stock["Y"])]
        assert stock["weight"] == weights[j]
        assert F(stock["f_exact"]) == true_f(scope, stock["Y"])

    prior = read(result["prior_results"][0])
    if result.get("records") and solve_name == "final_refresh":
        assert result["records"][-1]["columns"] == expected_columns
        assert result["records"][-1]["added"] > 0
    objective = qual["objective"]
    assert abs(objective - result["upper"]) <= 1e-9 or result["upper"] == prior["upper"]
    return dict(phase=phase, columns=expected_columns, point_variables=len(point),
                original_variables=len(point) - expected_columns,
                actual_return_status=returned["Status"], mass=mass, negative_mass=negative,
                nonzero_columns=len(nonzero), marginal_mismatch=mismatch,
                completion_slack=float(completion), final_RMP_objective=objective,
                retained_upper=result["upper"], prior_upper=prior["upper"],
                all_final_lambda_variables_present=True, actual_solution_equals_saved_point=True,
                saved_full_Q_primal_qualified=qual["qualified"],
                original_Q_rows_rechecked_in_this_script=False,
                independent_active_stock_marginal_completion_check=True,
                refresh_required=result["refresh_required"],
                result_SHA=sha(folder / "result.json"), call_SHA=sha(solve / "call.json"),
                return_SHA=sha(solve / "return.json"), point_SHA=sha(folder / point_name),
                actual_solution_SHA=sha(solve / "solution.json.gz"))


def main():
    start = time.perf_counter()
    checks = [
        check("K-35-U_target_residual_v2", "final_refresh", "final_primal.json.gz", 33896),
        check("N-C20-U_target_residual_v1", "final_refresh", "final_primal.json.gz", 54227),
        check("N-C20-U_interior_final_refresh", "solve", "primal.json.gz", 54235),
    ]
    result = dict(PASS=True, independent_nonimplementer_review=True, checks=checks,
                  Native_model_reads=0, Optimize=0, helper_source_SHA=sha(__file__),
                  seconds=time.perf_counter() - start)
    target = OUT / "review/last_refresh_readback.json"
    assert not target.exists()
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(PASS=True, checks=len(checks), seconds=result["seconds"], Native=0, Optimize=0)))


if __name__ == "__main__":
    main()
