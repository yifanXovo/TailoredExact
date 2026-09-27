"""Conditional, fixed A/B/C LP diagnostic for the Round91 five-station export.

No action on import. `supervise` needs a root-signed admission and owns one
300-second wall deadline, including preparation, three LPs and serialization.
No row from this study is installed in the production solver.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LIMIT_SECONDS = 300
ARMS = ("A", "B", "C")
gp = None  # Loaded only in the supervised child, after its shared deadline starts.
GRB = None


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def write_new(path: Path, value: Any) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def read(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def peak_working_set() -> int | None:
    if os.name != "nt":
        return None
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t) for name in (
                "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
    value = Counters()
    value.cb = ctypes.sizeof(Counters)
    ctypes.windll.kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    handle = ctypes.windll.kernel32.GetCurrentProcess()
    if not ctypes.windll.psapi.GetProcessMemoryInfo(
            ctypes.c_void_p(handle), ctypes.byref(value), value.cb):
        return None
    return value.PeakWorkingSetSize


def close_enough(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12)


def row_data(model: gp.Model, constraint: gp.Constr) -> dict:
    expr = model.getRow(constraint)
    terms = [(expr.getVar(index).VarName, float(expr.getCoeff(index)))
             for index in range(expr.size())]
    return dict(name=constraint.ConstrName, sense=constraint.Sense,
                rhs=float(constraint.RHS), terms=sorted(terms))


def original_matrix(model: gp.Model) -> dict:
    model.update()
    assert model.NumQConstrs == 0 and model.NumGenConstrs == 0 and model.NumSOS == 0
    variables = model.getVars()
    names = [var.VarName for var in variables]
    assert len(names) == len(set(names)), "duplicate LP variable name"
    rows = [row_data(model, constr) for constr in model.getConstrs()]
    core = dict(
        variables=[(var.VarName, float(var.LB), float(var.UB)) for var in variables],
        rows=rows)
    signature = hashlib.sha256(json.dumps(core, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return dict(signature=signature, variables=core["variables"], rows=rows,
                rows_count=len(rows), columns_count=len(variables))


def validate_export(manifest_path: Path, admission_path: Path) -> tuple[dict, dict, Path]:
    manifest = read(manifest_path)
    admission = read(admission_path)
    assert manifest["diagnostic"] == "round91_fixed_five_station_handling_rounding"
    assert manifest["optimizer_calls"] == 0
    assert admission == dict(
        schema="round91-handling-rounding-diagnostic-admission-v1",
        authorized_by="root", allow_optimize=True, whole_process_limit_seconds=LIMIT_SECONDS,
        script_sha256=digest(Path(__file__)), manifest_sha256=digest(manifest_path),
        lp_sha256=manifest["lp_sha256"], input_sha256=manifest["input_sha256"],
        exporter_binary_sha256=manifest["binary_sha256"])
    export_dir = manifest_path.resolve().parent
    lp_path = Path(manifest["lp_path"]).resolve()
    input_path = Path(manifest["input_path"]).resolve()
    assert lp_path.parent == input_path.parent == export_dir
    assert lp_path.name == "canonical_L0.lp" and input_path.name == "five_station_input.txt"
    assert digest(lp_path) == manifest["lp_sha256"]
    assert digest(input_path) == manifest["input_sha256"]
    assert manifest["model_scope"] == (
        "complete_original_compact_milp_intersected_with_static_gini_interval")
    assert manifest["spec"]["station_state_formulation"] == "vd-p"
    assert manifest["spec"]["verified_incumbent_row"] is True
    assert manifest["spec"]["strengthened"] is True
    assert manifest["spec"]["interval_restricted"] is True
    assert manifest["spec"]["gamma_L"] == 0.0
    assert manifest["spec"]["incumbent_epsilon"] == 0
    assert manifest["instance"] == dict(
        V=5, M=2, Q=[5, 5], capacity=[0, 2, 2, 2, 2, 2],
        initial=[0, 2, 2, 2, 2, 2], target=[0, 1, 1, 1, 1, 1],
        weights=[0, 1, 1, 1, 1, 1], T=5,
        pickup_time=1, drop_time=1, travel="all_zero_6_by_6")
    assert manifest["witness"]["feasible"] is True
    assert manifest["witness"]["final_inventory"] == [0, 1, 1, 1, 1, 2]
    assert close_enough(manifest["spec"]["verified_incumbent"], manifest["witness"]["F"])
    assert close_enough(manifest["spec"]["gamma_U"], manifest["witness"]["F"])
    assert close_enough(manifest["effective_options"]["lambda"], 0.15)
    source_root = Path(manifest["source_root"]).resolve()
    assert source_root == ROOT
    source_hashes = manifest["source_files_sha256"]
    assert "tests/round91_handling_rounding_probe.cpp" in source_hashes
    assert "CMakeLists.txt" in source_hashes
    for relative, expected in source_hashes.items():
        assert digest(source_root / relative) == expected, relative
    required = set(manifest["required_variable_names"])
    assert required == {"G"} | {
        f"Y_{i}" for i in range(1, 6)} | {
        f"state_{i}_{y}" for i in range(1, 6) for y in range(3)} | {
        f"{operation}_{k}_{i}" for operation in ("p", "d")
        for k in range(2) for i in range(1, 6)}
    return manifest, admission, lp_path


def audit_original_lp(model: gp.Model, manifest: dict) -> tuple[dict, dict[str, float]]:
    scope = original_matrix(model)
    assert scope["rows_count"] == manifest["rows"]
    assert scope["columns_count"] == manifest["columns"]
    variables = {var.VarName: var for var in model.getVars()}
    assert set(manifest["required_variable_names"]) <= set(variables)
    assert model.ModelSense == GRB.MINIMIZE and close_enough(model.ObjCon, 0.0)
    objective = {var.VarName: float(var.Obj) for var in model.getVars() if var.Obj != 0.0}
    wanted = {"G": 1.0, **{f"e_{i}": 0.15 for i in range(1, 6)}}
    assert set(objective) == set(wanted)
    assert all(close_enough(objective[name], value) for name, value in wanted.items())
    assert close_enough(variables["G"].LB, manifest["spec"]["gamma_L"])
    assert close_enough(variables["G"].UB, manifest["spec"]["gamma_U"])
    for i in range(1, 6):
        assert {y for y in range(3) if f"state_{i}_{y}" in variables} == {0, 1, 2}
        for y in range(3):
            var = variables[f"state_{i}_{y}"]
            assert var.VType == GRB.BINARY and close_enough(var.LB, 0.0) and close_enough(var.UB, 1.0)
        for k in range(2):
            pickup = variables[f"p_{k}_{i}"]
            drop = variables[f"d_{k}_{i}"]
            assert pickup.VType == GRB.INTEGER and close_enough(pickup.LB, 0.0)
            assert close_enough(pickup.UB, 2.0), "fixture pickup domain changed"
            assert drop.VType == GRB.INTEGER and close_enough(drop.LB, 0.0)
            assert close_enough(drop.UB, 0.0), "fixture has no legal drop mass"
        assert variables[f"Y_{i}"].VType == GRB.INTEGER
        assert close_enough(variables[f"Y_{i}"].LB, 0.0)
        assert close_enough(variables[f"Y_{i}"].UB, 2.0)
        def original_row(terms: dict[str, float], sense: str, rhs: float) -> bool:
            return any(row["sense"] == sense and close_enough(row["rhs"], rhs) and
                       {name: coeff for name, coeff in row["terms"] if coeff != 0.0} == terms
                       for row in scope["rows"])
        assert original_row({f"state_{i}_{y}": 1.0 for y in range(3)}, "=", 1.0)
        assert original_row({f"Y_{i}": 1.0, f"state_{i}_1": -1.0,
                             f"state_{i}_2": -2.0}, "=", 0.0)
        assert original_row({f"Y_{i}": 1.0, f"p_0_{i}": 1.0,
                             f"p_1_{i}": 1.0, f"d_0_{i}": -1.0,
                             f"d_1_{i}": -1.0}, "=", 2.0)
    cutoff = manifest["spec"]["verified_incumbent"]
    found_cutoff = any(
        row["sense"] == "<" and close_enough(row["rhs"], cutoff) and
        {name: coeff for name, coeff in row["terms"] if coeff != 0.0} == objective
        for row in scope["rows"])
    assert found_cutoff, "missing exact verified objective cutoff row"
    return scope, objective


def residuals(model: gp.Model, original_count: int, directory: Path) -> dict:
    variables = model.getVars()
    values = {var.VarName: float(var.X) for var in variables}
    maxima = dict(original_rows=0.0, added_rows=0.0, bounds=0.0)
    certified = True
    epsilon = sys.float_info.epsilon
    with (directory / "primal.jsonl").open("x", encoding="utf-8") as primal, \
         (directory / "row_residuals.jsonl").open("x", encoding="utf-8") as rows, \
         (directory / "bound_residuals.jsonl").open("x", encoding="utf-8") as bounds:
        for var in variables:
            x = values[var.VarName]
            primal.write(json.dumps(dict(variable=var.VarName, value=x), allow_nan=False) + "\n")
            lower = max(0.0, float(var.LB) - x)
            upper = max(0.0, x - float(var.UB))
            violation = max(lower, upper)
            allowance = float(model.Params.FeasibilityTol) + 64 * epsilon * (abs(x) + 1)
            maxima["bounds"] = max(maxima["bounds"], violation)
            certified &= violation <= allowance
            bounds.write(json.dumps(dict(variable=var.VarName, value=x,
                lower_bound=float(var.LB), upper_bound=float(var.UB),
                lower_violation=lower, upper_violation=upper,
                numerical_allowance=allowance, within_allowance=violation <= allowance),
                allow_nan=False) + "\n")
        for index, constr in enumerate(model.getConstrs()):
            row = row_data(model, constr)
            lhs = math.fsum(coeff * values[name] for name, coeff in row["terms"])
            if row["sense"] == "<":
                violation = max(0.0, lhs - row["rhs"])
            elif row["sense"] == ">":
                violation = max(0.0, row["rhs"] - lhs)
            else:
                assert row["sense"] == "="
                violation = abs(lhs - row["rhs"])
            activity_scale = math.fsum(abs(coeff * values[name]) for name, coeff in row["terms"])
            allowance = float(model.Params.FeasibilityTol) + 64 * epsilon * (
                1 + abs(row["rhs"]) + activity_scale)
            group = "original_rows" if index < original_count else "added_rows"
            maxima[group] = max(maxima[group], violation)
            certified &= violation <= allowance
            rows.write(json.dumps(dict(index=index, kind=group, name=row["name"],
                sense=row["sense"], lhs=lhs, rhs=row["rhs"],
                violation=violation, numerical_allowance=allowance,
                within_allowance=violation <= allowance), allow_nan=False) + "\n")
    return dict(variables=len(variables), rows=model.NumConstrs,
                original_rows=original_count, added_rows=model.NumConstrs - original_count,
                maximum_violations=maxima, all_within_numerical_allowance=certified,
                primal_sha256=digest(directory / "primal.jsonl"),
                row_residuals_sha256=digest(directory / "row_residuals.jsonl"),
                bound_residuals_sha256=digest(directory / "bound_residuals.jsonl"))


def one_arm(env: gp.Env, arm: str, lp_path: Path, manifest: dict,
            source_signature: str | None, directory: Path, deadline: float) -> tuple[dict, str]:
    started = time.perf_counter()
    directory.mkdir(exist_ok=False)
    if time.perf_counter() >= deadline:
        return dict(arm=arm, status="unknown_shared_deadline_before_read"), source_signature or ""
    read_started = time.perf_counter()
    original = gp.read(str(lp_path), env)
    original.update()
    scope, objective = audit_original_lp(original, manifest)
    if source_signature is not None:
        assert scope["signature"] == source_signature, "A/B/C original LP matrix changed"
    relaxed = original.relax()
    relaxed.update()
    relaxed_scope = original_matrix(relaxed)
    assert relaxed_scope["signature"] == scope["signature"]
    assert all(var.VType == GRB.CONTINUOUS for var in relaxed.getVars())
    read_seconds = time.perf_counter() - read_started
    variables = {var.VarName: var for var in relaxed.getVars()}
    target = gp.quicksum(variables[f"state_{i}_1"] for i in range(1, 6))
    relaxed.setObjective(target, GRB.MAXIMIZE)
    if arm == "B":
        for k in range(2):
            relaxed.addConstr(gp.quicksum(variables[f"p_{k}_{i}"] for i in range(1, 6)) <= 2,
                              name=f"research_vehicle_{k}_pickup_rounding")
    elif arm == "C":
        relaxed.addConstr(target <= 4, name="research_five_station_event_rounding")
    else:
        assert arm == "A"
    relaxed.update()
    assert relaxed.NumConstrs == scope["rows_count"] + (2 if arm == "B" else 1 if arm == "C" else 0)
    assert [row_data(relaxed, constr) for constr in relaxed.getConstrs()[:scope["rows_count"]]] == scope["rows"]
    relaxed.Params.Threads = 1
    relaxed.Params.Seed = 0
    relaxed.Params.Presolve = -1
    relaxed.Params.LogFile = str(directory / "gurobi.log")
    remaining = deadline - time.perf_counter()
    if remaining <= 0:
        return dict(arm=arm, status="unknown_shared_deadline_before_optimize",
                    read_relax_prepare_seconds=time.perf_counter() - started), scope["signature"]
    relaxed.Params.TimeLimit = remaining
    optimize_started = time.perf_counter()
    relaxed.optimize()
    optimize_seconds = time.perf_counter() - optimize_started
    result: dict[str, Any] = dict(
        arm=arm, solver_status_code=int(relaxed.Status),
        solver_status="OPTIMAL" if relaxed.Status == GRB.OPTIMAL else "UNKNOWN_OR_NONOPTIMAL",
        original_lp_sha256=digest(lp_path), original_matrix_signature=scope["signature"],
        original_rows=scope["rows_count"], original_columns=scope["columns_count"],
        added_rows=relaxed.NumConstrs - scope["rows_count"],
        original_objective_coefficients=objective,
        parameters=dict(Threads=relaxed.Params.Threads, Seed=relaxed.Params.Seed,
                        Presolve=relaxed.Params.Presolve, TimeLimit=relaxed.Params.TimeLimit,
                        FeasibilityTol=relaxed.Params.FeasibilityTol,
                        OptimalityTol=relaxed.Params.OptimalityTol),
        read_relax_seconds=read_seconds, optimize_seconds=optimize_seconds,
        gurobi_runtime_seconds=float(relaxed.Runtime),
        gurobi_work=float(relaxed.Work),
        gurobi_iteration_count=float(relaxed.IterCount),
        solution_count=int(relaxed.SolCount),
        process_peak_working_set_bytes=peak_working_set())
    if relaxed.SolCount > 0:
        save_started = time.perf_counter()
        receipt = residuals(relaxed, scope["rows_count"], directory)
        values = {var.VarName: float(var.X) for var in relaxed.getVars()}
        state_sum = math.fsum(values[f"state_{i}_1"] for i in range(1, 6))
        original_f = math.fsum(coefficient * values[name]
                               for name, coefficient in objective.items()) + float(original.ObjCon)
        gini = values["G"]
        penalty = math.fsum(values[f"e_{i}"] for i in range(1, 6))
        result.update(primal_receipt=receipt, state_i_1_sum=state_sum,
                      vehicle_pickup_sums={str(k): math.fsum(values[f"p_{k}_{i}"]
                                                            for i in range(1, 6)) for k in range(2)},
                      state_one_values={str(i): values[f"state_{i}_1"] for i in range(1, 6)},
                      original_F=original_f, G=gini, weighted_penalty_P=penalty,
                      original_F_reconstruction_residual=original_f - (gini + 0.15 * penalty),
                      research_objective_value=float(relaxed.ObjVal),
                      research_objective_residual=float(relaxed.ObjVal) - state_sum,
                      primal_save_seconds=time.perf_counter() - save_started)
        result["status"] = ("certified_optimal_primal" if relaxed.Status == GRB.OPTIMAL and
                            receipt["all_within_numerical_allowance"] and
                            close_enough(float(relaxed.ObjVal), state_sum) and
                            close_enough(original_f, gini + 0.15 * penalty)
                            else "unknown_status_or_residual")
    else:
        result["status"] = "unknown_no_primal"
    result["arm_complete_wall_seconds"] = time.perf_counter() - started
    write_new(directory / "arm_result.json", result)
    return result, scope["signature"]


def diagnose(manifest_path: Path, admission_path: Path, directory: Path,
             deadline: float) -> int:
    global gp, GRB
    assert os.environ.get("ROUND91_HANDLING_ROUNDING_SUPERVISED") == "1"
    started = time.perf_counter()
    directory.mkdir(exist_ok=False)
    outcomes: list[dict] = []
    try:
        import gurobipy as gurobipy_module
        gp, GRB = gurobipy_module, gurobipy_module.GRB
        manifest, _, lp_path = validate_export(manifest_path, admission_path)
        identity = dict(manifest_sha256=digest(manifest_path), lp_sha256=digest(lp_path),
                        input_sha256=manifest["input_sha256"],
                        source_files_sha256=manifest["source_files_sha256"],
                        exporter_binary_sha256=manifest["binary_sha256"],
                        script_sha256=digest(Path(__file__)),
                        python_executable=sys.executable,
                        python_version=sys.version,
                        gurobi_version=list(gp.gurobi.version()))
        write_new(directory / "identity.json", identity)
        if time.perf_counter() >= deadline:
            write_new(directory / "diagnostic_result.json", dict(
                status="unknown_shared_deadline_before_A", outcomes=outcomes,
                full_child_wall_seconds=time.perf_counter() - started, identity=identity))
            return 2
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()
        signature = None
        for arm in ARMS:
            outcome, signature = one_arm(env, arm, lp_path, manifest, signature,
                                         directory / arm, deadline)
            outcomes.append(outcome)
            if outcome["status"] != "certified_optimal_primal":
                write_new(directory / "diagnostic_result.json", dict(
                    status="partial_unknown", outcomes=outcomes, identity=identity,
                    full_child_wall_seconds=time.perf_counter() - started,
                    interpretation="No A/B/C dominance claim until all arms certified"))
                return 2
        assert digest(lp_path) == identity["lp_sha256"]
        assert digest(manifest_path) == identity["manifest_sha256"]
        write_new(directory / "diagnostic_result.json", dict(
            status="all_three_certified", outcomes=outcomes, identity=identity,
            full_child_wall_seconds=time.perf_counter() - started,
            interpretation="Only this fixed full-canonical-root LP; B dominates C."
                           " No formal B3 admission or MIP performance inference."))
        return 0
    except Exception as error:
        write_new(directory / "failure.json", dict(
            status="invalid_or_failed", error=repr(error), outcomes=outcomes,
            full_child_wall_seconds=time.perf_counter() - started))
        return 1


def supervise(manifest_path: Path, admission_path: Path, directory: Path) -> int:
    assert os.name == "nt", "the frozen exporter and supervision contract are Windows-only"
    started = time.perf_counter()
    deadline = started + LIMIT_SECONDS
    directory.mkdir(parents=True, exist_ok=False)
    try:
        # Root admission and complete preflight are part of the shared 300 s.
        manifest, admission, lp_path = validate_export(manifest_path, admission_path)
    except Exception as error:
        expired = time.perf_counter() >= deadline
        write_new(directory / "supervision.json", dict(
            schema="round91-handling-rounding-supervision-v1",
            status=("unknown_whole_process_deadline" if expired
                    else "invalid_preflight_no_optimize"), error=repr(error),
            supervisor_body_wall_seconds=time.perf_counter() - started,
            ceiling_seconds=LIMIT_SECONDS, returncode=None))
        return 2 if expired else 1
    command = [sys.executable, str(Path(__file__).resolve()), "diagnose",
               "--manifest", str(manifest_path.resolve()),
               "--admission", str(admission_path.resolve()),
               "--out", str((directory / "diagnostic").resolve()),
               "--deadline-monotonic", repr(deadline)]
    process = None
    status = "unknown_shared_deadline_before_launch"
    returncode = None
    with (directory / "stdout.log").open("x", encoding="utf-8") as stdout, \
         (directory / "stderr.log").open("x", encoding="utf-8") as stderr:
        try:
            if time.perf_counter() < deadline:
                environment = dict(os.environ, ROUND91_HANDLING_ROUNDING_SUPERVISED="1")
                process = subprocess.Popen(command, cwd=ROOT, env=environment,
                                           stdout=stdout, stderr=stderr)
                try:
                    returncode = process.wait(timeout=max(0.0, deadline - time.perf_counter()))
                except subprocess.TimeoutExpired:
                    process.kill()  # Gurobi runs in this Python process, not a child executable.
                    returncode = process.wait()
                    status = "unknown_whole_process_deadline"
                if status != "unknown_whole_process_deadline":
                    if time.perf_counter() > deadline:
                        status = "unknown_whole_process_deadline"
                    elif returncode == 0:
                        status = "child_returned_zero_pending_result_audit"
                    elif returncode == 2:
                        status = "partial_unknown"
                    else:
                        status = "invalid_or_failed"
        finally:
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()
    result_path = directory / "diagnostic" / "diagnostic_result.json"
    result_invalid = False
    try:
        result = read(result_path) if result_path.is_file() else None
    except (OSError, ValueError):
        result, result_invalid = None, True
    manifest_after = digest(manifest_path) if manifest_path.is_file() else None
    lp_after = digest(lp_path) if lp_path.is_file() else None
    script_after = digest(Path(__file__))
    manifest_unchanged = manifest_after == admission["manifest_sha256"]
    lp_unchanged = lp_after == admission["lp_sha256"]
    script_unchanged = script_after == admission["script_sha256"]
    if not manifest_unchanged or not lp_unchanged or not script_unchanged:
        status = "invalid_source_drift"
    elif status == "child_returned_zero_pending_result_audit":
        status = ("all_three_certified" if result is not None and
                  result.get("status") == "all_three_certified" and
                  result.get("identity", {}).get("manifest_sha256") == manifest_after and
                  result.get("identity", {}).get("lp_sha256") == lp_after and
                  len(result.get("outcomes", [])) == 3 and
                  all(row.get("status") == "certified_optimal_primal"
                      for row in result["outcomes"]) else "invalid_missing_complete_result")
    if time.perf_counter() > deadline and status not in {
            "invalid_source_drift", "invalid_missing_complete_result", "invalid_or_failed"}:
        status = "unknown_whole_process_deadline"
    write_new(directory / "supervision.json", dict(
        schema="round91-handling-rounding-supervision-v1", status=status,
        returncode=returncode, command=command, ceiling_seconds=LIMIT_SECONDS,
        supervisor_body_wall_seconds=time.perf_counter() - started,
        manifest_sha256_before=admission["manifest_sha256"],
        manifest_sha256_after=manifest_after,
        lp_sha256_before=admission["lp_sha256"], lp_sha256_after=lp_after,
        script_sha256_after=script_after, script_identity_consistent=script_unchanged,
        result_present=result is not None, result_file_invalid=result_invalid,
        process_peak_working_set_bytes=peak_working_set(),
        scope="One research diagnostic; nonoptimal/residual failure is unknown, not a bound"))
    return 0 if status == "all_three_certified" else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("supervise", "diagnose"))
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--admission", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--deadline-monotonic", type=float)
    args = parser.parse_args()
    if args.mode == "supervise":
        assert args.deadline_monotonic is None
        return supervise(args.manifest, args.admission, args.out)
    assert args.deadline_monotonic is not None
    return diagnose(args.manifest, args.admission, args.out, args.deadline_monotonic)


if __name__ == "__main__":
    raise SystemExit(main())
