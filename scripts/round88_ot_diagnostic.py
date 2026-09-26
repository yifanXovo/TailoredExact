"""Read a frozen ENS-C VD-P LP and diagnose one fixed-point OT cut round.

`audit` only reads and checks an LP; `diagnose` invokes Gurobi Optimize and
requires a separately frozen audit manifest. Never use this driver as an
internal algorithm switch or as an alternative model generator.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import ctypes
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time
from typing import Any

import gurobipy as gp
from gurobipy import GRB

sys.path.insert(0, str(Path(__file__).resolve().parent))
from round88_ot_math import (aggregate_cut, h_name, pair_cut, q_name,
                             row_value, state_name, support_fingerprint, z_name)

ROUND83_SOURCE = "4496078f25c0cdad1cf7a5c39835fd23121e8978"
VIOLATION_TOL = 1e-6  # fixed numerical diagnostic threshold, not an algorithm budget
MAX_SCALED_COEFF = 1e8


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def process_peak_memory_bytes() -> int | None:
    """Windows process peak working set; cumulative across diagnostic arms."""
    if sys.platform != "win32":
        return None
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
    counters = Counters()
    counters.cb = ctypes.sizeof(Counters)
    ctypes.windll.kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.c_void_p(handle), ctypes.byref(counters), counters.cb):
        return None
    return counters.PeakWorkingSetSize


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n",
                    encoding="utf-8")


def read_instance(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    first = text.splitlines()[0]
    head = re.findall(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", first)
    if len(head) < 2:
        raise ValueError("invalid instance header")
    n, vehicles = int(float(head[0])), int(float(head[1]))

    def vector(label: str) -> list[float]:
        m = re.search(r"\b" + re.escape(label) + r"\s*=\s*\[([^]]*)\]", text, re.S)
        if not m:
            return []
        return [float(x) for x in re.findall(
            r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?", m.group(1))]

    target = vector("target")
    weights = vector("weights") or [0.0] + [1.0] * n
    capacities = vector("capacities")
    if len(target) != n + 1 or len(weights) != n + 1 or len(capacities) != n + 1:
        raise ValueError("instance target/weight/capacity dimension mismatch")
    if any(x != int(x) or x <= 0 for x in target[1:]):
        raise ValueError("all station targets D must be positive integers")
    if any(x != int(x) for x in capacities):
        raise ValueError("nonintegral capacity")
    if abs(max(weights[1:]) - 10.0) <= 1e-6:
        weights = [weights[0]] + [x / 10.0 for x in weights[1:]]
    return {"n": n, "vehicles": vehicles,
            "targets": {i: int(target[i]) for i in range(1, n + 1)},
            "weights": {i: weights[i] for i in range(1, n + 1)},
            "capacities": {i: int(capacities[i]) for i in range(1, n + 1)}}


def row_terms(model: gp.Model, constr: gp.Constr) -> dict[str, float]:
    row = model.getRow(constr)
    return {row.getVar(k).VarName: row.getCoeff(k) for k in range(row.size())
            if row.getCoeff(k) != 0.0}


def row_matches(actual: dict[str, float], sense: str, rhs: float,
                expected: dict[str, float], wanted_sense: str,
                wanted_rhs: float) -> bool:
    if sense != wanted_sense or not math.isclose(rhs, wanted_rhs, rel_tol=1e-10, abs_tol=1e-13):
        return False
    if actual.keys() != expected.keys():
        return False
    return all(math.isclose(actual[k], expected[k], rel_tol=1e-10, abs_tol=1e-13)
               for k in actual)


def audit_model(model: gp.Model, instance: dict[str, Any],
                a: Fraction, b: Fraction, cutoff: float, lam: float) -> dict[str, Any]:
    n = instance["n"]
    if not Fraction(0) <= a <= b <= Fraction(1):
        raise ValueError("G interval must satisfy 0<=a<=b<=1")
    if a < b and not float(a) < float(b):
        raise ValueError("G interval width is below double-precision resolution")
    variables = {v.VarName: v for v in model.getVars()}
    if len(variables) != model.NumVars:
        raise ValueError("duplicate variable names")
    if "G" not in variables:
        raise ValueError("missing G")
    if model.ModelSense != GRB.MINIMIZE or not math.isclose(model.ObjCon, 0.0, abs_tol=1e-12):
        raise ValueError("expected zero-constant minimization objective")
    wanted_objective = {"G": 1.0}
    wanted_objective.update({f"e_{i}": lam * instance["weights"][i]
                             for i in range(1, n + 1)
                             if lam * instance["weights"][i] != 0.0})
    actual_objective = {name: var.Obj for name, var in variables.items() if var.Obj != 0.0}
    if not row_matches(actual_objective, "=", 0.0, wanted_objective, "=", 0.0):
        raise ValueError("actual LP objective differs from declared G+lambda*weighted penalty")
    g = variables["G"]
    if g.LB != float(a) or g.UB != float(b):
        raise ValueError("actual G bounds do not match declared leaf interval")
    # All local cuts below use the actual parsed LP bounds, never a CLI
    # decimal approximation that could be a strict subset of the LP domain.
    a, b = Fraction.from_float(g.LB), Fraction.from_float(g.UB)
    if any(name.startswith("state_code_") for name in variables):
        raise ValueError("logarithmic state code is not VD-P")
    supports: dict[int, list[int]] = defaultdict(list)
    for name, var in variables.items():
        m = re.fullmatch(r"state_(\d+)_(\d+)", name)
        if m:
            i, y = map(int, m.groups())
            if i < 1 or i > n or var.VType != GRB.BINARY:
                raise ValueError("unexpected selector station or variable type")
            supports[i].append(y)
    if set(supports) != set(range(1, n + 1)):
        raise ValueError("not every station has VD-P state selectors")
    def domain(name: str, kind: str, lo: float, hi: float) -> None:
        var = variables.get(name)
        if var is None or var.VType != kind or not math.isclose(var.LB, lo, abs_tol=1e-10) or not math.isclose(var.UB, hi, abs_tol=1e-10):
            raise ValueError(f"unexpected type or bounds for {name}")
    for i in range(1, n + 1):
        supports[i].sort()
        if supports[i] != list(range(supports[i][0], supports[i][-1] + 1)):
            raise ValueError(f"station {i} has an incomplete inventory domain")
        if supports[i][0] < 0 or supports[i][-1] > instance["capacities"][i]:
            raise ValueError(f"station {i} domain violates input capacity")
        for y in supports[i]:
            domain(state_name(i, y), GRB.BINARY, 0.0, 1.0)
            domain(q_name(i, y), GRB.CONTINUOUS, 0.0, float(b))
        domain(z_name(i), GRB.CONTINUOUS, 0.0, instance["capacities"][i])
        domain(f"Y_{i}", GRB.INTEGER, supports[i][0], supports[i][-1])
        domain(f"r_{i}", GRB.CONTINUOUS, 0.0,
               instance["capacities"][i] / instance["targets"][i])
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            h_upper = (instance["capacities"][i] / instance["targets"][i]
                       + instance["capacities"][j] / instance["targets"][j])
            domain(h_name(i, j), GRB.CONTINUOUS, 0.0, h_upper)

    # Audit actual rows, rather than trusting column names or a legacy model.
    expected: dict[str, tuple[dict[str, float], str, float]] = {}
    for i in range(1, n + 1):
        expected[f"onehot_{i}"] = ({state_name(i, y): 1.0 for y in supports[i]}, "=", 1.0)
        inventory = {f"Y_{i}": 1.0}
        inventory.update({state_name(i, y): -float(y) for y in supports[i] if y != 0})
        expected[f"inventory_reconstruction_{i}"] = (inventory, "=", 0.0)
        expected[f"ratio_reconstruction_{i}"] = (
            {f"r_{i}": 1.0, f"Y_{i}": -1.0 / instance["targets"][i]}, "=", 0.0)
        expected[f"qsum_{i}"] = ({**{q_name(i, y): 1.0 for y in supports[i]}, "G": -1.0}, "=", 0.0)
        product = {z_name(i): 1.0}
        product.update({q_name(i, y): -float(y) for y in supports[i] if y != 0})
        expected[f"zprod_reconstruction_{i}"] = (product, "=", 0.0)
        for y in supports[i]:
            lower = {q_name(i, y): 1.0}
            upper = {q_name(i, y): 1.0}
            if a:
                lower[state_name(i, y)] = -float(a)
            if b:
                upper[state_name(i, y)] = -float(b)
            expected[f"lower_{i}_{y}"] = (lower, ">", 0.0)
            expected[f"upper_{i}_{y}"] = (upper, "<", 0.0)
    gini = {z_name(i): n / instance["targets"][i] for i in range(1, n + 1)}
    gini.update({h_name(i, j): -1.0 for i in range(1, n + 1)
                 for j in range(i + 1, n + 1)})
    expected["gini"] = (gini, ">", 0.0)
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            positive = {h_name(i, j): 1.0, f"r_{i}": -1.0, f"r_{j}": 1.0}
            negative = {h_name(i, j): 1.0, f"r_{i}": 1.0, f"r_{j}": -1.0}
            expected[f"h_positive_{i}_{j}"] = (positive, ">", 0.0)
            expected[f"h_negative_{i}_{j}"] = (negative, ">", 0.0)
    objective_cutoff = {"G": 1.0}
    objective_cutoff.update({f"e_{i}": lam * instance["weights"][i]
                             for i in range(1, n + 1)
                             if lam * instance["weights"][i] != 0.0})
    expected["verified_cutoff"] = (objective_cutoff, "<", cutoff)
    by_names: dict[frozenset[str], list[str]] = defaultdict(list)
    for label, (terms, _, _) in expected.items():
        by_names[frozenset(terms)].append(label)
    found: set[str] = set()
    for constr in model.getConstrs():
        terms = row_terms(model, constr)
        for label in by_names.get(frozenset(terms), []):
            wanted, sense, rhs = expected[label]
            if row_matches(terms, constr.Sense, constr.RHS, wanted, sense, rhs):
                found.add(label)
    missing = sorted(set(expected) - found)
    if missing:
        raise ValueError("actual LP failed VD-P/Gini/cutoff row audit: " + ",".join(missing[:20]))
    return {"support": {str(i): supports[i] for i in range(1, n + 1)},
            "support_fingerprint": support_fingerprint(supports, instance["targets"], a, b),
            "audited_rows": len(found), "variables": model.NumVars,
            "constraints": model.NumConstrs, "nonzeros": model.NumNZs,
            "g_bounds": [g.LB, g.UB],
            "effective_gamma_l": str(a), "effective_gamma_u": str(b),
            "objective": {k: v for k, v in sorted(wanted_objective.items())}}


def load_model(lp: Path) -> gp.Model:
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)
    env.start()
    return gp.read(str(lp), env)


def configure(model: gp.Model, log_path: Path) -> None:
    model.Params.Threads = 1
    model.Params.Seed = 0
    model.Params.Presolve = -1
    model.Params.FeasibilityTol = 1e-6
    model.Params.OptimalityTol = 1e-6
    model.Params.MIPGap = 0.0
    model.Params.LogToConsole = 0
    model.Params.LogFile = str(log_path)
    model.Params.OutputFlag = 1


def save_primal_and_residuals(model: gp.Model, out: Path) -> dict[str, float | int]:
    """Persist the entire original LP point and independently recomputed row residuals."""
    primal = {v.VarName: v.X for v in model.getVars()}
    write_json(out / "fixed_point_primal.json", primal)
    max_row_violation = 0.0
    max_bound_violation = 0.0
    row_count = 0
    with (out / "base_row_residuals.jsonl").open("w", encoding="utf-8") as stream:
        for constr in model.getConstrs():
            terms = row_terms(model, constr)
            lhs = math.fsum(coef * primal[name] for name, coef in terms.items())
            rhs = constr.RHS
            if constr.Sense == ">":
                violation = max(0.0, rhs - lhs)
            elif constr.Sense == "<":
                violation = max(0.0, lhs - rhs)
            elif constr.Sense == "=":
                violation = abs(lhs - rhs)
            else:
                raise ValueError("unsupported row sense")
            stream.write(json.dumps({"name": constr.ConstrName, "sense": constr.Sense,
                                     "lhs": lhs, "rhs": rhs, "violation": violation},
                                    allow_nan=False) + "\n")
            max_row_violation = max(max_row_violation, violation)
            row_count += 1
    for var in model.getVars():
        max_bound_violation = max(max_bound_violation, var.LB - var.X, var.X - var.UB)
    return {"row_count": row_count, "maximum_row_violation": max_row_violation,
            "maximum_variable_bound_violation": max_bound_violation,
            "primal_variables": len(primal)}


def optimize(model: gp.Model, log_path: Path) -> dict[str, Any]:
    configure(model, log_path)
    started = time.perf_counter()
    model.optimize()
    result = {"status_code": model.Status, "wall_seconds": time.perf_counter() - started,
              "solver_runtime_seconds": model.Runtime, "work": model.Work,
              "process_peak_working_set_bytes_so_far": process_peak_memory_bytes(),
              "variables": model.NumVars, "constraints": model.NumConstrs,
              "nonzeros": model.NumNZs}
    if model.Status == GRB.OPTIMAL:
        result["objective"] = model.ObjVal
    return result


def arms_comparable(arms: dict[str, dict[str, Any]], equal_endpoints: bool) -> bool:
    return all(
        name == "B2" and equal_endpoints
        or arms[name].get("status_code") == GRB.OPTIMAL
        for name in ("B1", "B2", "B1+B2", "aggregate"))


def add_cut(model: gp.Model, coeff: dict[str, Fraction], name: str,
            scale: Fraction = Fraction(1)) -> None:
    expr = gp.LinExpr()
    for var_name, value in sorted(coeff.items()):
        expr.addTerms(float(value / scale), model.getVarByName(var_name))
    model.addConstr(expr >= 0.0, name=name)


def reliable(coeff: dict[str, Fraction], scale: Fraction, violation: float,
             values: dict[str, float], base_residual: float) -> tuple[bool, str, float | None]:
    magnitudes = [abs(float(v / scale)) for v in coeff.values()]
    if any(not math.isfinite(v) or v > MAX_SCALED_COEFF for v in magnitudes):
        return False, "unreliable_scaled_coefficient", None
    coefficient_l1 = math.fsum(magnitudes)
    activity_l1 = math.fsum(abs(float(v / scale) * values[name])
                            for name, v in coeff.items())
    # The conservative residual amplification also protects very narrow
    # local G intervals; it may reject a useful cut, never force one in.
    margin = max(VIOLATION_TOL, 10.0 * base_residual * coefficient_l1
                 + 128.0 * sys.float_info.epsilon * activity_l1)
    if not math.isfinite(violation) or violation <= margin:
        return False, "violation_below_numerical_margin", margin
    return True, "selected", margin


def cut_record(cut: Any, values: dict[str, float], scale: Fraction,
               selected: bool, reason: str, margin: float | None,
               leaf_support_identity: str) -> dict[str, Any]:
    coeff = cut.coeff if hasattr(cut, "coeff") else cut
    raw_violation = -math.fsum(float(c) * values[name] for name, c in coeff.items())
    signature_payload = {
        "leaf_support_identity": leaf_support_identity,
        "kind": getattr(cut, "kind", "aggregate"),
        "pair": [cut.i, cut.j] if hasattr(cut, "i") else None,
        "pair_support_identity": getattr(cut, "support_identity", None),
        "signs": getattr(cut, "signs", None),
        "coefficients_exact": {k: str(v) for k, v in sorted(coeff.items())}}
    signature = hashlib.sha256(json.dumps(signature_payload, sort_keys=True).encode()).hexdigest()
    return {"kind": getattr(cut, "kind", "aggregate"),
            "pair": [cut.i, cut.j] if hasattr(cut, "i") else None,
            "support_fingerprint": getattr(cut, "support_identity", None),
            "signs": getattr(cut, "signs", None),
            "intervals": [str(x) for x in cut.intervals] if hasattr(cut, "intervals") else None,
            "a_values": getattr(cut, "a_values", None),
            "b_values": getattr(cut, "b_values", None),
            "coefficients_exact": {k: str(v) for k, v in sorted(coeff.items())},
            "row_signature": signature,
            "raw_violation": raw_violation,
            "normalized_violation": raw_violation / float(scale),
            "solver_row_scale": str(scale), "selected": selected, "reason": reason,
            "selection_margin": margin}


def audit(args: argparse.Namespace) -> None:
    process_started = time.perf_counter()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    lp, input_path = args.lp.resolve(), args.input.resolve()
    if sha256(lp) != args.expected_lp_sha256.lower() or sha256(input_path) != args.expected_input_sha256.lower():
        raise ValueError("frozen LP or input SHA256 mismatch")
    if args.source_sha256.lower() != ROUND83_SOURCE:
        raise ValueError("not the frozen ENS-C source identity")
    instance = read_instance(input_path)
    a, b = Fraction(args.gamma_l), Fraction(args.gamma_u)
    started = time.perf_counter()
    model = load_model(lp)
    read_seconds = time.perf_counter() - started
    structure = audit_model(model, instance, a, b, args.verified_ub, args.lambda_value)
    manifest = {"contract": "round88_same_source_one_round_ot_diagnostic_v1",
                "provenance_scope": "LP/input SHA and structural content independently checked; scenario, source, binary and leaf labels are operator declarations requiring external export receipts",
                "lp": str(lp), "lp_sha256": args.expected_lp_sha256.lower(),
                "input": str(input_path), "input_sha256": args.expected_input_sha256.lower(),
                "source_sha256": args.source_sha256.lower(),
                "binary_sha256": args.binary_sha256.lower(),
                "scenario_id": args.scenario_id, "leaf_id": args.leaf_id,
                "parent_id": args.parent_id, "gamma_l": str(a), "gamma_u": str(b),
                "verified_ub": args.verified_ub, "T": args.time_limit,
                "lambda": args.lambda_value, "pickup_time": args.pickup_time,
                "drop_time": args.drop_time, "instance": instance,
                "structure": structure, "lp_read_and_audit_wall_seconds": read_seconds,
                "gurobi_version": gp.gurobi.version(),
                "numeric_protocol": {"violation_tolerance": VIOLATION_TOL,
                                     "maximum_scaled_coefficient": MAX_SCALED_COEFF,
                                     "FeasibilityTol": 1e-6, "OptimalityTol": 1e-6,
                                     "Threads": 1, "Seed": 0, "Presolve": -1,
                                     "MIPGap": 0.0}}
    write_json(out / "manifest.json", manifest)
    write_json(out / "audit_timing.json", {
        "audit_wall_seconds_through_manifest_write": time.perf_counter() - process_started})
    print(out / "manifest.json")


def diagnose(args: argparse.Namespace) -> None:
    process_started = time.perf_counter()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("contract") != "round88_same_source_one_round_ot_diagnostic_v1":
        raise ValueError("wrong audit manifest contract")
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    lp, input_path = Path(manifest["lp"]), Path(manifest["input"])
    if sha256(lp) != manifest["lp_sha256"] or sha256(input_path) != manifest["input_sha256"]:
        raise ValueError("frozen asset changed since audit")
    a, b = Fraction(manifest["gamma_l"]), Fraction(manifest["gamma_u"])
    instance = read_instance(input_path)
    started = time.perf_counter()
    original = load_model(lp)
    read_seconds = time.perf_counter() - started
    structure = audit_model(original, instance, a, b,
                            manifest["verified_ub"], manifest["lambda"])
    if structure != manifest["structure"] or instance != {
            **manifest["instance"],
            "targets": {int(k): v for k, v in manifest["instance"]["targets"].items()},
            "weights": {int(k): v for k, v in manifest["instance"]["weights"].items()},
            "capacities": {int(k): v for k, v in manifest["instance"]["capacities"].items()}}:
        raise ValueError("support/domain/instance identity changed since audit")
    a = Fraction(structure["effective_gamma_l"])
    b = Fraction(structure["effective_gamma_u"])
    relax_started = time.perf_counter()
    base = original.relax()
    relax_seconds = time.perf_counter() - relax_started
    base_result = optimize(base, out / "base.log")
    result: dict[str, Any] = {
        "manifest_sha256": sha256(args.manifest), "lp_sha256": manifest["lp_sha256"],
        "shared_costs": {"model_read_seconds": read_seconds,
                         "relax_integrality_seconds": relax_seconds},
        "arms": {"base": base_result}, "status": "base_not_optimal"}
    if base.Status != GRB.OPTIMAL:
        write_json(out / "result.json", result)
        return
    values = {v.VarName: v.X for v in base.getVars()}
    if any(v.VType != GRB.CONTINUOUS for v in base.getVars()):
        raise ValueError("relax() did not remove every integrality restriction")
    residual_started = time.perf_counter()
    primal_residuals = save_primal_and_residuals(base, out)
    primal_residuals["save_and_check_wall_seconds"] = time.perf_counter() - residual_started
    result["base_primal_residuals"] = primal_residuals
    if (primal_residuals["maximum_row_violation"] > 1e-5
            or primal_residuals["maximum_variable_bound_violation"] > 1e-5):
        result["status"] = "base_primal_residual_too_large"
        write_json(out / "result.json", result)
        return
    supports = {int(k): v for k, v in structure["support"].items()}
    targets = instance["targets"]
    n = instance["n"]
    pair_rows: dict[str, list[Any]] = {"B1": [], "B2": []}
    records = []
    selected: dict[str, list[tuple[dict[str, Fraction], Fraction, str]]] = {
        "B1": [], "B2": [], "B1+B2": [], "aggregate": []}
    combined_signatures: set[tuple[tuple[str, Fraction], ...]] = set()
    separation_started = time.perf_counter()
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            h = values[h_name(i, j)]
            mean_i = sum(y * values[state_name(i, y)] / targets[i] for y in supports[i])
            mean_j = sum(y * values[state_name(j, y)] / targets[j] for y in supports[j])
            pair_record: dict[str, Any] = {"pair": [i, j], "h": h,
                                           "absolute_mean_difference": abs(mean_i - mean_j),
                                           "station_residuals": {}}
            levels = sorted({Fraction(y, targets[k]) for k in (i, j) for y in supports[k]})
            w1 = 0.0
            b2_raw_rhs = 0.0
            for lo, hi in zip(levels, levels[1:]):
                cdf = (math.fsum(values[state_name(i, y)] for y in supports[i]
                                 if Fraction(y, targets[i]) <= lo)
                       - math.fsum(values[state_name(j, y)] for y in supports[j]
                                   if Fraction(y, targets[j]) <= lo))
                weighted_cdf = (math.fsum(values[q_name(i, y)] for y in supports[i]
                                          if Fraction(y, targets[i]) <= lo)
                                - math.fsum(values[q_name(j, y)] for y in supports[j]
                                            if Fraction(y, targets[j]) <= lo))
                delta = float(hi - lo)
                w1 += delta * abs(cdf)
                b2_raw_rhs += delta * (abs(float(b) * cdf - weighted_cdf)
                                       + abs(weighted_cdf - float(a) * cdf))
            pair_record["W1_B1_rhs"] = w1
            pair_record["B2_normalized_rhs"] = (b2_raw_rhs / float(b - a)
                                                 if a < b else None)
            for k in (i, j):
                s_sum = math.fsum(values[state_name(k, y)] for y in supports[k])
                q_sum = math.fsum(values[q_name(k, y)] for y in supports[k])
                pair_record["station_residuals"][str(k)] = {
                    "sum_s_minus_1": s_sum - 1.0,
                    "sum_q_minus_G": q_sum - values["G"],
                    "min_q_minus_a_s": min(values[q_name(k, y)] - float(a) * values[state_name(k, y)]
                                           for y in supports[k]),
                    "min_b_s_minus_q": min(float(b) * values[state_name(k, y)] - values[q_name(k, y)]
                                           for y in supports[k]),
                    "lower_layer_mass": math.fsum(
                        (float(b) * values[state_name(k, y)] - values[q_name(k, y)]) / float(b - a)
                        for y in supports[k]) if a < b else None,
                    "upper_layer_mass": math.fsum(
                        (values[q_name(k, y)] - float(a) * values[state_name(k, y)]) / float(b - a)
                        for y in supports[k]) if a < b else None}
            for kind in ("B1", "B2"):
                if kind == "B2" and a == b:
                    pair_record[kind] = {"status": "not_applicable_a_equals_b"}
                    continue
                cut = pair_cut(kind, i, j, supports, targets, a, b, values)
                pair_rows[kind].append(cut)
                scale = b - a if kind == "B2" else Fraction(1)
                violation = cut.violation(values) / float(scale)
                use, reason, margin = reliable(
                    cut.coeff, scale, violation, values,
                    max(primal_residuals["maximum_row_violation"],
                        primal_residuals["maximum_variable_bound_violation"]))
                pair_record[kind] = {"lower_bound": h + violation,
                                     "violation": violation, "raw_violation": cut.violation(values),
                                     "selection_margin": margin,
                                     "selected": use, "reason": reason}
                records.append(cut_record(cut, values, scale, use, reason, margin,
                                          structure["support_fingerprint"]))
                if use:
                    payload = (cut.coeff, scale, f"ot_{kind}_{i}_{j}")
                    selected[kind].append(payload)
                    normalized = tuple(sorted((name, value / scale)
                                              for name, value in cut.coeff.items()))
                    if normalized not in combined_signatures:
                        selected["B1+B2"].append(payload)
                        combined_signatures.add(normalized)
            records.append({"diagnostic_pair": pair_record})
    family = "B2" if a < b else "B1"
    aggregate = aggregate_cut(pair_rows[family], n, targets, a, b)
    aggregate_scale = b - a if family == "B2" else Fraction(1)
    aggregate_violation = -math.fsum(float(c) * values[name] for name, c in aggregate.items()) / float(aggregate_scale)
    aggregate_selected, aggregate_reason, aggregate_margin = reliable(
        aggregate, aggregate_scale, aggregate_violation, values,
        max(primal_residuals["maximum_row_violation"],
            primal_residuals["maximum_variable_bound_violation"]))
    records.append(cut_record(aggregate, values, aggregate_scale,
                              aggregate_selected, aggregate_reason, aggregate_margin,
                              structure["support_fingerprint"]))
    if aggregate_selected:
        selected["aggregate"].append((aggregate, aggregate_scale, f"ot_aggregate_{family}"))
    separation_seconds = time.perf_counter() - separation_started
    with (out / "fixed_point_rows.jsonl").open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
    shared_preparation_seconds = time.perf_counter() - process_started
    result["shared_costs"]["diagnose_shared_preparation_wall_seconds"] = shared_preparation_seconds
    result["fixed_point"] = {"objective": base.ObjVal, "G": values["G"],
                              "fractional_selectors": sum(
                                  1 for i in supports for y in supports[i]
                                  if 1e-7 < values[state_name(i, y)] < 1 - 1e-7),
                              "separation_seconds": separation_seconds,
                              "selected_rows": {k: len(v) for k, v in selected.items()},
                              "aggregate_family": family,
                              "aggregate_normalized_violation": aggregate_violation,
                              "aggregate_selection_margin": aggregate_margin}
    for arm in ("B1", "B2", "B1+B2", "aggregate"):
        if arm == "B2" and a == b:
            result["arms"][arm] = {"status": "not_applicable_a_equals_b"}
            continue
        copied = time.perf_counter()
        model = base.copy()
        copy_seconds = time.perf_counter() - copied
        added = time.perf_counter()
        for coeff, scale, name in selected[arm]:
            add_cut(model, coeff, name, scale)
        model.update()
        add_seconds = time.perf_counter() - added
        arm_result = optimize(model, out / f"{arm}.log")
        arm_result.update({"copy_seconds": copy_seconds, "add_rows_seconds": add_seconds,
                           "new_rows": len(selected[arm]),
                           "arm_marginal_wall_seconds": copy_seconds + add_seconds +
                               arm_result["wall_seconds"],
                           "shared_plus_arm_component_seconds": shared_preparation_seconds +
                               copy_seconds + add_seconds + arm_result["wall_seconds"]})
        result["arms"][arm] = arm_result
    all_comparable = arms_comparable(result["arms"], a == b)
    result["all_arm_objectives_comparable"] = all_comparable
    result["status"] = ("completed_fixed_point_one_round" if all_comparable
                        else "partial_unknown_one_round")
    write_json(out / "result.json", result)
    write_json(out / "diagnose_timing.json", {
        "diagnose_wall_seconds_through_result_write": time.perf_counter() - process_started,
        "audit_separate": True,
        "arms_run_sequentially_in_one_process": True})


def cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    a = sub.add_parser("audit", help="read and fingerprint the actual frozen LP; never Optimize")
    for name in ("lp", "input", "out-dir"):
        a.add_argument("--" + name, type=Path, required=True)
    for name in ("expected-lp-sha256", "expected-input-sha256", "source-sha256",
                 "binary-sha256", "scenario-id", "leaf-id", "parent-id",
                 "gamma-l", "gamma-u"):
        a.add_argument("--" + name, required=True)
    for name in ("verified-ub", "lambda-value", "time-limit", "pickup-time", "drop-time"):
        a.add_argument("--" + name, type=float, required=True)
    d = sub.add_parser("diagnose", help="Optimize base and four same-source one-round arms")
    d.add_argument("--manifest", type=Path, required=True)
    d.add_argument("--out-dir", type=Path, required=True)
    return parser.parse_args()


if __name__ == "__main__":
    options = cli()
    try:
        if options.command == "audit":
            audit(options)
        else:
            diagnose(options)
    except Exception as exc:
        print(f"Round88 OT {options.command} failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
