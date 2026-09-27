"""Conditional D3/C2 historical-L0 handling perspective diagnostic.

Each case has exactly three original-objective LP arms (A, B, C) and its own
shared 120 s deadline. There is no Optimize on import. A separate root-signed
launch-to-exit process-tree watchdog remains mandatory for a hard outer cap.
"""

from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

import round91_handling_rounding_diagnostic as evidence

ROOT = Path(__file__).resolve().parents[1]
LIMIT_SECONDS = 120
ARMS = ("A", "B", "C")
GRB = None
gp = None


def resolved(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(f"missing or external evidence path: {relative}")
    return path


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def signed_identity(prereg_path: Path, admission_path: Path, case_id: str) -> tuple[dict, dict, Path]:
    prereg = read_json(prereg_path)
    admission = read_json(admission_path)
    if prereg["schema"] != "round91-real-handling-row-diagnostic-prereg-v1":
        raise ValueError("wrong preregistration")
    if Path(sys.executable).resolve() != resolved(prereg["qualified_python"]):
        raise ValueError("not the qualified Gurobi Python interpreter")
    if prereg["order"] != ["D3", "C2"] or [arm["name"] for arm in prereg["arms"]] != list(ARMS) or \
            prereg["lambda"] != 0.15:
        raise ValueError("case or arm order changed")
    if resolved(prereg["residual_evidence_helper"]) != Path(evidence.__file__).resolve() or \
            evidence.digest(Path(evidence.__file__)) != prereg["residual_evidence_helper_sha256"]:
        raise ValueError("frozen residual evidence helper changed")
    case = next((row for row in prereg["cases"] if row["id"] == case_id), None)
    if case is None or len(prereg["cases"]) != 2:
        raise ValueError("not a registered fixed case")
    if admission != dict(
        schema="round91-real-handling-diagnostic-admission-v1",
        authorized_by="root", allow_optimize=True, case=case_id,
        whole_process_limit_seconds=LIMIT_SECONDS,
        script_sha256=evidence.digest(Path(__file__)),
        prereg_sha256=evidence.digest(prereg_path),
        lp_sha256=case["lp_sha256"], input_sha256=case["input_sha256"]):
        raise ValueError("missing or stale exact admission")
    if case["shared_item_limit_seconds"] != LIMIT_SECONDS:
        raise ValueError("deadline changed")
    lp_path = resolved(case["lp_path"])
    input_path = resolved(case["input_path"])
    if lp_path.stat().st_size != case["lp_size_bytes"] or evidence.digest(lp_path) != case["lp_sha256"]:
        raise ValueError("historical LP bytes changed")
    if evidence.digest(input_path) != case["input_sha256"]:
        raise ValueError("historical input bytes changed")
    gate = read_json(resolved(prereg["historical_qualification_gate"]))
    if not gate["qualified"] or gate["source_commit"] != prereg["historical_source_commit"] or \
            gate["candidate_binary_sha256"] != prereg["historical_binary_sha256"]:
        raise ValueError("historical source/binary qualification differs")
    launch = read_json(resolved(case["launch_path"]))
    command = launch["command"]
    if launch["id"] != case_id or launch["arm"] != "ENS-C" or \
            launch["prereg_sha256"] != gate["prereg_sha256"] or \
            "--round90-lp-g-split" not in command or \
            command[command.index("--round90-lp-g-split") + 1] != "false":
        raise ValueError("historical ENS-C launch identity differs")
    index = read_json(resolved(prereg["historical_archive_index"]))
    wanted_path = str(lp_path.relative_to(ROOT / "results/unified_exact_round90")).replace("\\", "/")
    archive_members = {entry["path"]: entry for group in index["groups"] for entry in group["files"]}
    member = archive_members.get(wanted_path)
    if member is None or member["sha256"] != case["lp_sha256"] or \
            member["size"] != case["lp_size_bytes"]:
        raise ValueError("historical archive index does not pin this L0")
    witness_path = resolved(case["initial_witness_path"])
    witness_member_path = str(witness_path.relative_to(ROOT / "results/unified_exact_round90")).replace("\\", "/")
    witness_member = archive_members.get(witness_member_path)
    if witness_member is None or witness_member["sha256"] != case["initial_witness_sha256"] or \
            witness_member["size"] != witness_path.stat().st_size or \
            evidence.digest(witness_path) != case["initial_witness_sha256"]:
        raise ValueError("historical verified witness bytes changed")
    ledger = read_csv(resolved(case["paper_optimize_ledger_path"]))
    root_lp = [row for row in ledger if row["leaf_id"] == "L0" and row["solve_kind"] == "LP"]
    if len(root_lp) != 1 or root_lp[0]["native_status"] != "OPTIMAL" or \
            root_lp[0]["optimize_return_code"] != "0" or \
            root_lp[0]["model_sha256"] != case["lp_sha256"]:
        raise ValueError("historical L0 Optimize identity differs")
    status = read_csv(resolved(case["lp_status_ledger_path"]))
    root_status = [row for row in status if row["leaf_id"] == "L0"]
    if len(root_status) != 1 or root_status[0]["terminal_valid"] != "1" or \
            root_status[0]["optimal"] != "1" or root_status[0]["infeasible"] != "0":
        raise ValueError("historical root LP was not complete optimal")
    leaf = read_csv(resolved(case["paper_leaf_ledger_path"]))
    root_leaf = [row for row in leaf if row["leaf_id"] == "L0"]
    if len(root_leaf) != 1 or root_leaf[0]["depth"] != "0" or \
            root_leaf[0]["lp_complete"] != "1" or root_leaf[0]["lp_optimal"] != "1":
        raise ValueError("historical root leaf scope differs")
    for number, value in enumerate(case["historical_G_bounds"]):
        field = "gamma_L" if number == 0 else "gamma_U"
        if not math.isclose(float(root_leaf[0][field]), value, rel_tol=0, abs_tol=1e-14):
            raise ValueError("historical L0 interval differs")
    witness = read_json(witness_path)
    audit = read_json(resolved(case["audit_path"]))
    if not math.isclose(float(witness["objective"]), case["historical_cutoff"],
                        rel_tol=0, abs_tol=1e-14) or not audit["physical_upper_available"] or \
            audit["binary_sha256"] != prereg["historical_binary_sha256"] or \
            not any(item.get("source") == "same_run_verified_startup" and
                    item.get("original_T_feasible") is True and
                    math.isclose(float(item["F"]), case["historical_cutoff"],
                                 rel_tol=0, abs_tol=1e-14)
                    for item in audit["witnesses"]):
        raise ValueError("historical verified cutoff identity differs")
    return prereg, case, lp_path


def terms(model: Any, constraint: Any) -> dict[str, float]:
    row = model.getRow(constraint)
    return {row.getVar(i).VarName: float(row.getCoeff(i)) for i in range(row.size())}


def has_row(rows: list[tuple[str, float, dict[str, float]]], sense: str,
            rhs: float, required: dict[str, float]) -> bool:
    return any(s == sense and r == rhs and t == required for s, r, t in rows)


def exact_dyadic(value: float) -> Fraction:
    if not math.isfinite(value):
        raise ValueError("nonfinite LP coefficient")
    return Fraction.from_float(value)


def perspective_coefficients(costs: dict[tuple[int, int], Fraction],
                             stations: int, rhs: Fraction, handling: Fraction) -> dict:
    if handling <= 0 or rhs <= 0:
        raise ValueError("duration has invalid service or horizon")
    nodes = range(stations + 1)
    distance = [[Fraction(0) if i == j else costs[i, j] for j in nodes] for i in nodes]
    for middle in nodes:
        for i in nodes:
            for j in nodes:
                via = distance[i][middle] + distance[middle][j]
                if via < distance[i][j]:
                    distance[i][j] = via
    minimum = min(distance[0][i] + distance[i][0] for i in range(1, stations + 1))
    exact_beta = (rhs - minimum) / handling
    if exact_beta <= 0:
        raise ValueError("nonpositive activated service envelope; fixed diagnostic inapplicable")
    integer_beta = exact_beta.numerator // exact_beta.denominator
    if integer_beta > 2**53:
        raise ValueError("integer cut coefficient exceeds exact binary64 integer range")
    continuous = float(exact_beta)
    if not math.isfinite(continuous):
        raise ValueError("continuous beta exceeds binary64")
    if Fraction.from_float(continuous) < exact_beta:
        continuous = math.nextafter(continuous, math.inf)
    if not math.isfinite(continuous) or Fraction.from_float(continuous) < exact_beta:
        raise ValueError("failed binary64 upward enclosure")
    return dict(lmin=str(minimum), exact_beta=str(exact_beta),
                continuous_beta_upper=continuous, integer_beta=integer_beta,
                upward_excess=str(Fraction.from_float(continuous) - exact_beta),
                directed_arc_costs={f"{i}_{j}": str(costs[i, j]) for i in nodes for j in nodes if i != j})


def audit_lp(model: Any, case: dict) -> tuple[dict, dict[int, dict], dict[str, float]]:
    model.update()
    if model.ModelSense != GRB.MINIMIZE or model.NumQConstrs or model.NumSOS or model.NumGenConstrs:
        raise ValueError("not the registered linear original minimization")
    if model.ObjCon != 0:
        raise ValueError("unexpected original objective constant")
    scope = evidence.original_matrix(model)
    variables = {var.VarName: var for var in model.getVars()}
    rows = [(c.Sense, float(c.RHS), terms(model, c)) for c in model.getConstrs()]
    V, M = case["stations"], case["vehicles"]
    G = variables["G"]
    if G.LB != case["historical_G_bounds"][0] or not math.isclose(
            G.UB, case["historical_G_bounds"][1], rel_tol=0, abs_tol=1e-14):
        raise ValueError("historical G domain differs")
    objective = {var.VarName: float(var.Obj) for var in model.getVars() if var.Obj != 0}
    if objective.get("G") != 1 or set(objective) != {"G"} | {f"e_{i}" for i in range(1, V + 1)}:
        raise ValueError("original F objective differs")
    if not any(s == "<" and math.isclose(r, case["historical_cutoff"], rel_tol=0, abs_tol=1e-14)
               and t == objective for s, r, t in rows):
        raise ValueError("verified original objective cutoff row missing")
    recipes: dict[int, dict] = {}
    for k in range(M):
        outbound = {f"x_{k}_0_{j}": 1.0 for j in range(1, V + 1)}
        inbound = {f"x_{k}_{j}_0": -1.0 for j in range(1, V + 1)}
        if not has_row(rows, "<", 1.0, outbound) or not has_row(rows, "=", 0.0,
                                                            outbound | inbound):
            raise ValueError("depot activation/return rows missing")
        for i in range(1, V + 1):
            p, z = variables[f"p_{k}_{i}"], variables[f"z_{k}_{i}"]
            if p.VType != GRB.INTEGER or p.LB != 0 or z.VType != GRB.BINARY or \
                    z.LB != 0 or z.UB != 1 or not math.isfinite(p.UB) or p.UB < 0:
                raise ValueError("pickup/visit domain differs")
            link = {p.VarName: 1.0}
            if p.UB:
                link[z.VarName] = -float(p.UB)
            if not has_row(rows, "<", 0.0, link):
                raise ValueError("pickup-to-visit link missing")
            visits_in = {f"x_{k}_{j}_{i}": 1.0 for j in range(V + 1) if j != i}
            visits_out = {f"x_{k}_{i}_{j}": 1.0 for j in range(V + 1) if j != i}
            if not has_row(rows, "=", 0.0, visits_in | {z.VarName: -1.0}) or \
                    not has_row(rows, "=", 0.0, visits_out | {z.VarName: -1.0}):
                raise ValueError("visit flow balance missing")
            conn_in = {f"conn_{k}_{j}_{i}": 1.0 for j in range(V + 1) if j != i}
            conn_out = {f"conn_{k}_{i}_{j}": -1.0 for j in range(V + 1) if j != i}
            if not has_row(rows, "=", 0.0, conn_in | conn_out | {z.VarName: -1.0}):
                raise ValueError("F0 station connectivity balance missing")
        depot_connectivity = ({f"conn_{k}_0_{j}": 1.0 for j in range(1, V + 1)} |
                              {f"conn_{k}_{j}_0": -1.0 for j in range(1, V + 1)} |
                              {f"z_{k}_{j}": -1.0 for j in range(1, V + 1)})
        if not has_row(rows, "=", 0.0, depot_connectivity):
            raise ValueError("F0 depot connectivity balance missing")
        costs: dict[tuple[int, int], Fraction] = {}
        for i in range(V + 1):
            for j in range(V + 1):
                if i == j:
                    continue
                x = variables[f"x_{k}_{i}_{j}"]
                conn = variables[f"conn_{k}_{i}_{j}"]
                if x.VType != GRB.BINARY or x.LB != 0 or x.UB != 1 or conn.LB != 0:
                    raise ValueError("arc or F0 flow domain differs")
                if not has_row(rows, "<", 0.0, {conn.VarName: 1.0, x.VarName: -float(V)}):
                    raise ValueError("F0 connectivity arc link missing")
        pickups = {f"p_{k}_{i}" for i in range(1, V + 1)}
        arcs = {f"x_{k}_{i}_{j}" for i in range(V + 1) for j in range(V + 1) if i != j}
        candidates = [t for s, r, t in rows if s == "<" and r == case["duration_rhs_seconds"]
                      and set(t) <= pickups | arcs and pickups <= set(t)]
        if len(candidates) != 1:
            raise ValueError("unique original vehicle duration row not found")
        duration = candidates[0]
        c = {duration[name] for name in pickups}
        if len(c) != 1 or next(iter(c)) != case["handling_coefficient_seconds"]:
            raise ValueError("duration handling coefficients differ")
        for i in range(V + 1):
            for j in range(V + 1):
                if i != j:
                    cost = exact_dyadic(duration.get(f"x_{k}_{i}_{j}", 0.0))
                    if cost < 0:
                        raise ValueError("negative directed travel coefficient")
                    costs[i, j] = cost
        recipes[k] = perspective_coefficients(
            costs, V, exact_dyadic(float(case["duration_rhs_seconds"])),
            exact_dyadic(float(next(iter(c)))))
    return scope, recipes, objective


def arm_solve(env: Any, name: str, lp_path: Path, case: dict, signature: str | None,
              directory: Path, deadline: float) -> tuple[dict, str | None]:
    started = time.perf_counter()
    directory.mkdir(exist_ok=False)
    if started >= deadline:
        return dict(arm=name, status="unknown_shared_deadline_before_read"), signature
    original = gp.read(str(lp_path), env)
    original.update()
    scope, recipes, objective = audit_lp(original, case)
    if signature is not None and scope["signature"] != signature:
        raise ValueError("A/B/C original matrix identity differs")
    relaxed = original.relax()
    relaxed.update()
    if evidence.original_matrix(relaxed)["signature"] != scope["signature"]:
        raise ValueError("relax changed an original row or bound")
    if any(var.VType != GRB.CONTINUOUS for var in relaxed.getVars()):
        raise ValueError("not a full integrality relaxation")
    variables = {var.VarName: var for var in relaxed.getVars()}
    if name != "A":
        for k, recipe in recipes.items():
            beta = recipe["continuous_beta_upper"] if name == "B" else recipe["integer_beta"]
            pickup = gp.quicksum(variables[f"p_{k}_{i}"] for i in range(1, case["stations"] + 1))
            activation = gp.quicksum(variables[f"x_{k}_0_{j}"]
                                     for j in range(1, case["stations"] + 1))
            relaxed.addConstr(pickup <= beta * activation, name=f"research_{name}_vehicle_{k}")
    relaxed.update()
    if relaxed.NumConstrs != scope["rows_count"] + (0 if name == "A" else case["vehicles"]):
        raise ValueError("unexpected research-row count")
    if [evidence.row_data(relaxed, row) for row in relaxed.getConstrs()[:scope["rows_count"]]] != scope["rows"]:
        raise ValueError("original LP rows changed after research-row insertion")
    for k, recipe in recipes.items():
        if name == "A":
            continue
        added = relaxed.getConstrByName(f"research_{name}_vehicle_{k}")
        if added is None or added.Sense != "<" or added.RHS != 0:
            raise ValueError("research row missing after insertion")
        actual = terms(relaxed, added)
        beta = recipe["continuous_beta_upper"] if name == "B" else recipe["integer_beta"]
        expected = ({f"p_{k}_{i}": 1.0 for i in range(1, case["stations"] + 1)} |
                    {f"x_{k}_0_{j}": -float(beta) for j in range(1, case["stations"] + 1)})
        if actual != expected:
            raise ValueError("research row coefficients changed by API")
        if name == "B" and Fraction.from_float(-actual[f"x_{k}_0_1"]) < Fraction(recipe["exact_beta"]):
            raise ValueError("continuous readback coefficient rounded downward")
        if name == "C" and -actual[f"x_{k}_0_1"] != recipe["integer_beta"]:
            raise ValueError("integer readback coefficient changed")
    if relaxed.ModelSense != GRB.MINIMIZE or relaxed.ObjCon != original.ObjCon or \
            {v.VarName: float(v.Obj) for v in relaxed.getVars()
                                              if v.Obj != 0} != objective:
        raise ValueError("original objective changed")
    prepare_seconds = time.perf_counter() - started
    remaining = deadline - time.perf_counter()
    if remaining <= 0:
        return dict(arm=name, status="unknown_shared_deadline_before_optimize",
                    read_relax_prepare_seconds=prepare_seconds), scope["signature"]
    relaxed.Params.Threads = 1
    relaxed.Params.Seed = 0
    relaxed.Params.Presolve = -1
    relaxed.Params.LogFile = str(directory / "gurobi.log")
    relaxed.Params.TimeLimit = remaining
    optimize_started = time.perf_counter()
    relaxed.optimize()
    optimize_seconds = time.perf_counter() - optimize_started
    outcome: dict[str, Any] = dict(
        arm=name, solver_status_code=int(relaxed.Status),
        solver_status="OPTIMAL" if relaxed.Status == GRB.OPTIMAL else "UNKNOWN_OR_NONOPTIMAL",
        original_lp_sha256=case["lp_sha256"], original_matrix_signature=scope["signature"],
        original_rows=scope["rows_count"], original_columns=scope["columns_count"],
        original_nonzeros=sum(len(row["terms"]) for row in scope["rows"]),
        research_rows=relaxed.NumConstrs - scope["rows_count"],
        research_nonzeros=sum(len(evidence.row_data(relaxed, row)["terms"])
                              for row in relaxed.getConstrs()[scope["rows_count"]:]),
        recipes=recipes, original_objective_coefficients=objective,
        parameters=dict(Threads=relaxed.Params.Threads, Seed=relaxed.Params.Seed,
                        Presolve=relaxed.Params.Presolve, TimeLimit=relaxed.Params.TimeLimit,
                        FeasibilityTol=relaxed.Params.FeasibilityTol,
                        OptimalityTol=relaxed.Params.OptimalityTol),
        read_relax_prepare_seconds=prepare_seconds, optimize_seconds=optimize_seconds,
        gurobi_runtime_seconds=float(relaxed.Runtime), gurobi_work=float(relaxed.Work),
        gurobi_iteration_count=float(relaxed.IterCount),
        solution_count=int(relaxed.SolCount),
        verified_U=case["historical_cutoff"],
        verified_U_witness_sha256=case["initial_witness_sha256"],
        process_peak_working_set_bytes=evidence.peak_working_set())
    try:
        raw_bound = float(relaxed.ObjBound)
        outcome["solver_objbound_raw"] = raw_bound if math.isfinite(raw_bound) else None
    except (AttributeError, gp.GurobiError):
        outcome["solver_objbound_raw"] = None
    if relaxed.SolCount:
        save_started = time.perf_counter()
        receipt = evidence.residuals(relaxed, scope["rows_count"], directory)
        values = {var.VarName: float(var.X) for var in relaxed.getVars()}
        original_f = math.fsum(coefficient * values[var] for var, coefficient in objective.items())
        pickup = {str(k): math.fsum(values[f"p_{k}_{i}"] for i in range(1, case["stations"] + 1))
                  for k in range(case["vehicles"])}
        activation = {str(k): math.fsum(values[f"x_{k}_0_{j}"] for j in range(1, case["stations"] + 1))
                      for k in range(case["vehicles"])}
        row_margins = {str(k): dict(
            continuous=recipes[k]["continuous_beta_upper"] * activation[str(k)] - pickup[str(k)],
            integer=recipes[k]["integer_beta"] * activation[str(k)] - pickup[str(k)])
            for k in recipes}
        objective_ok = math.isclose(float(relaxed.ObjVal), original_f,
                                    rel_tol=1e-9, abs_tol=1e-8)
        native_bound = outcome["solver_objbound_raw"]
        bound_allowance = max(float(relaxed.Params.FeasibilityTol),
                              float(relaxed.Params.OptimalityTol)) + \
            64 * sys.float_info.epsilon * (1 + abs(original_f))
        bound_consistent = native_bound is None or native_bound <= original_f + bound_allowance
        outcome.update(primal_receipt=receipt, original_F=original_f,
                       solver_objval_raw=float(relaxed.ObjVal),
                       G=values["G"], original_P=(original_f - values["G"]) / 0.15,
                       lambda_P=original_f - values["G"],
                       original_F_solver_residual=float(relaxed.ObjVal) - original_f,
                       native_bound_vs_primal_consistent=bound_consistent,
                       native_bound_allowance=bound_allowance,
                       pickup_sums=pickup, activation=activation, row_margins=row_margins,
                       primal_save_seconds=time.perf_counter() - save_started)
        outcome["status"] = ("solver_numeric_optimal_primal" if
                             relaxed.Status == GRB.OPTIMAL and objective_ok and bound_consistent and
                             receipt["all_within_numerical_allowance"] and
                             time.perf_counter() < deadline else "unknown_status_or_residual")
        if outcome["status"] == "solver_numeric_optimal_primal":
            outcome["numeric_L"] = (native_bound if native_bound is not None
                                    else float(relaxed.ObjVal))
            outcome["numeric_L_source"] = ("Gurobi_ObjBound_under_OPTIMAL" if native_bound is not None
                                           else "Gurobi_ObjVal_under_OPTIMAL")
        else:
            outcome["numeric_L"] = None
            outcome["numeric_L_source"] = None
    else:
        outcome["status"] = "unknown_no_primal"
        outcome["solver_objval_raw"] = None
        outcome["numeric_L"] = None
        outcome["numeric_L_source"] = None
    outcome["arm_complete_wall_seconds"] = time.perf_counter() - started
    evidence.write_new(directory / "arm_result.json", outcome)
    return outcome, scope["signature"]


def diagnose(prereg_path: Path, admission_path: Path, case_id: str,
             directory: Path, deadline: float) -> int:
    global gp, GRB
    if os.environ.get("ROUND91_HANDLING_REAL_SUPERVISED") != "1":
        raise ValueError("diagnose requires the supervisor")
    started = time.perf_counter()
    directory.mkdir(exist_ok=False)
    outcomes: list[dict] = []
    try:
        import gurobipy as imported_gurobi
        gp, GRB = imported_gurobi, imported_gurobi.GRB
        prereg, case, lp_path = signed_identity(prereg_path, admission_path, case_id)
        identity = dict(case=case_id, prereg_sha256=evidence.digest(prereg_path),
                        lp_sha256=evidence.digest(lp_path), script_sha256=evidence.digest(Path(__file__)),
                        input_sha256=case["input_sha256"],
                        historical_binary_sha256=prereg["historical_binary_sha256"],
                        python_executable=sys.executable, python_version=sys.version,
                        gurobi_version=list(gp.gurobi.version()))
        evidence.write_new(directory / "identity.json", identity)
        if time.perf_counter() >= deadline:
            evidence.write_new(directory / "diagnostic_result.json", dict(
                status="unknown_shared_deadline_before_A", outcomes=outcomes, identity=identity))
            return 2
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()
        signature = None
        for name in ARMS:
            outcome, signature = arm_solve(env, name, lp_path, case, signature,
                                           directory / name, deadline)
            outcomes.append(outcome)
            if outcome["status"] != "solver_numeric_optimal_primal":
                evidence.write_new(directory / "diagnostic_result.json", dict(
                    status="partial_unknown", outcomes=outcomes, identity=identity,
                    full_child_wall_seconds=time.perf_counter() - started))
                return 2
        if evidence.digest(lp_path) != identity["lp_sha256"] or \
                evidence.digest(prereg_path) != identity["prereg_sha256"]:
            raise ValueError("input asset changed during diagnostic")
        evidence.write_new(directory / "diagnostic_result.json", dict(
            status="all_three_solver_numeric_optimal", outcomes=outcomes, identity=identity,
            full_child_wall_seconds=time.perf_counter() - started,
            interpretation="Fixed full canonical L0 relaxation only; no MIP performance claim or rational dual proof"))
        return 0
    except Exception as error:
        evidence.write_new(directory / "failure.json", dict(
            status="invalid_or_failed", error=repr(error), outcomes=outcomes,
            full_child_wall_seconds=time.perf_counter() - started))
        return 1


def supervise(prereg_path: Path, admission_path: Path, case_id: str, directory: Path) -> int:
    if os.name != "nt":
        raise ValueError("historical binary and watchdog are Windows-only")
    started = time.perf_counter()
    deadline = started + LIMIT_SECONDS
    directory.mkdir(parents=True, exist_ok=False)
    try:
        _, case, lp_path = signed_identity(prereg_path, admission_path, case_id)
    except Exception as error:
        status = "unknown_shared_deadline" if time.perf_counter() >= deadline else "invalid_preflight_no_optimize"
        evidence.write_new(directory / "supervision.json", dict(
            status=status, error=repr(error), ceiling_seconds=LIMIT_SECONDS,
            supervisor_body_wall_seconds=time.perf_counter() - started, optimizer_calls=0))
        return 2 if status.startswith("unknown") else 1
    command = [sys.executable, str(Path(__file__).resolve()), "diagnose",
               "--prereg", str(prereg_path.resolve()), "--admission", str(admission_path.resolve()),
               "--case", case_id, "--out", str((directory / "diagnostic").resolve()),
               "--deadline-monotonic", repr(deadline)]
    process = None
    code = None
    status = "unknown_shared_deadline_before_launch"
    with (directory / "stdout.log").open("x", encoding="utf-8") as stdout, \
         (directory / "stderr.log").open("x", encoding="utf-8") as stderr:
        try:
            if time.perf_counter() < deadline:
                environment = dict(os.environ, ROUND91_HANDLING_REAL_SUPERVISED="1")
                process = subprocess.Popen(command, cwd=ROOT, env=environment,
                                           stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
                try:
                    code = process.wait(timeout=max(0.0, deadline - time.perf_counter()))
                except subprocess.TimeoutExpired:
                    process.kill()
                    code = process.wait()
                    status = "unknown_shared_deadline"
                if status != "unknown_shared_deadline":
                    if time.perf_counter() >= deadline:
                        status = "unknown_shared_deadline"
                    elif code == 0:
                        status = "child_zero_pending_audit"
                    elif code == 2:
                        status = "partial_unknown"
                    else:
                        status = "invalid_or_failed"
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
    result_path = directory / "diagnostic" / "diagnostic_result.json"
    try:
        result = read_json(result_path) if result_path.is_file() else None
    except (OSError, ValueError):
        result = None
    admission = read_json(admission_path)
    assets = dict(prereg=evidence.digest(prereg_path), lp=evidence.digest(lp_path),
                  script=evidence.digest(Path(__file__)))
    identity_ok = (assets["prereg"] == admission["prereg_sha256"] and
                   assets["lp"] == admission["lp_sha256"] and
                   assets["script"] == admission["script_sha256"])
    if not identity_ok:
        status = "invalid_source_drift"
    elif status == "child_zero_pending_audit":
        status = ("all_three_solver_numeric_optimal" if result is not None and
                  result.get("status") == "all_three_solver_numeric_optimal" and
                  result.get("identity", {}).get("case") == case_id and
                  result.get("identity", {}).get("lp_sha256") == assets["lp"] and
                  [item.get("arm") for item in result.get("outcomes", [])] == list(ARMS) and
                  all(item.get("status") == "solver_numeric_optimal_primal"
                      for item in result["outcomes"]) else "invalid_missing_complete_result")
    if time.perf_counter() >= deadline and status not in {"invalid_source_drift", "invalid_or_failed"}:
        status = "unknown_shared_deadline"
    evidence.write_new(directory / "supervision.json", dict(
        status=status, case=case_id, returncode=code, command=command,
        ceiling_seconds=LIMIT_SECONDS, supervisor_body_wall_seconds=time.perf_counter() - started,
        asset_sha256_after=assets, identity_consistent=identity_ok,
        result_present=result is not None, process_peak_working_set_bytes=evidence.peak_working_set(),
        optimizer_calls_recorded=(sum("solver_status_code" in item for item in result.get("outcomes", []))
                                  if result else None),
        scope="Root-signed external launch-to-exit process-tree watchdog is still required"))
    return 0 if status == "all_three_solver_numeric_optimal" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("supervise", "diagnose"))
    parser.add_argument("--prereg", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--case", choices=("D3", "C2"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--deadline-monotonic", type=float)
    args = parser.parse_args()
    if args.mode == "supervise":
        if args.deadline_monotonic is not None:
            raise ValueError("external deadline only belongs to diagnose")
        return supervise(args.prereg, args.admission, args.case, args.out)
    if args.deadline_monotonic is None:
        raise ValueError("diagnose requires the supervisor deadline")
    return diagnose(args.prereg, args.admission, args.case, args.out, args.deadline_monotonic)


if __name__ == "__main__":
    raise SystemExit(main())
