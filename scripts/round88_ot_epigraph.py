"""Independent fixed-LP OT epigraph diagnostic; never a production ENS switch.

The pure-rational row plan has no solver dependency. Real arms require a
separately signed lease and a 300-second outside-process deadline.
"""

from __future__ import annotations

import argparse
from bisect import bisect_right
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence

from round88_ot_math import h_name, q_name, ratio, state_name
from round88_ot_closure import (
    ROOT, CAMPAIGN, SOURCES, _WindowsJob, _kill_tree, _wait_with_deadline,
    frozen_source, read, save, sha,
)

ARMS = ("B1", "B2")
CHILD_STATUSES = {"complete_optimal_numeric_lp", "unknown_lp_not_optimal",
                  "observed_lp_infeasible_requires_scope_audit",
                  "numeric_rejection_original_or_added_rows"}
WHOLE_ARM_SECONDS = 300.0
LEASE = CAMPAIGN / "ot_epigraph_lease.json"
SCRIPT = Path(__file__).resolve()
SOLVER_PARAMETERS = {"Threads": 1, "Seed": 0, "Presolve": -1,
                     "FeasibilityTol": 1e-6, "OptimalityTol": 1e-6,
                     "MIPGap": 0.0}


@dataclass(frozen=True)
class Expr:
    coefficients: dict[str, F]
    constant: F = F(0)

    def __add__(self, other: Expr) -> Expr:
        coefficients = dict(self.coefficients)
        for key, value in other.coefficients.items():
            coefficients[key] = coefficients.get(key, F(0)) + value
            if not coefficients[key]:
                del coefficients[key]
        return Expr(coefficients, self.constant + other.constant)

    def __neg__(self) -> Expr:
        return Expr({key: -value for key, value in self.coefficients.items()},
                    -self.constant)

    def __sub__(self, other: Expr) -> Expr:
        return self + -other

    def __mul__(self, scale: F | int) -> Expr:
        scale = F(scale)
        return Expr({key: scale * value for key, value in self.coefficients.items()
                     if scale * value}, scale * self.constant)

    __rmul__ = __mul__


ZERO = Expr({})


def variable(name: str) -> Expr:
    return Expr({name: F(1)})


@dataclass(frozen=True)
class Row:
    name: str
    sense: str
    coefficients: dict[str, F]
    rhs: F


def row(name: str, sense: str, lhs: Expr) -> Row:
    if sense not in ("=", ">"):
        raise ValueError("unsupported row sense")
    if not lhs.coefficients:
        raise ValueError("empty epigraph row")
    return Row(name, sense, lhs.coefficients, -lhs.constant)


@dataclass(frozen=True)
class Plan:
    arm: str
    domain: tuple[F, F]
    columns: tuple[str, ...]
    rows: tuple[Row, ...]
    N: int
    P: int
    K: int
    pair_levels: dict[str, tuple[F, ...]]

    @property
    def counts(self) -> dict[str, int]:
        upper = ((3 * self.N + 7 * self.P + self.K) if self.arm == "B1"
                 else (6 * self.N + 26 * self.P + self.K))
        return {"new_columns": len(self.columns), "new_rows": len(self.rows),
                "new_nonzeros": sum(len(r.coefficients) for r in self.rows),
                "nonzero_upper_bound": upper, "N": self.N, "P": self.P,
                "K": self.K}


def make_plan(arm: str, supports: Mapping[int, Sequence[int]],
              targets: Mapping[int, int], a: F, b: F) -> Plan:
    """Build exact sparse rows; full prefix is 1/G from audited original rows."""
    if arm not in ARMS or not F(0) <= a <= b <= F(1) or (arm == "B2" and a == b):
        raise ValueError("invalid family or actual G domain")
    if not supports or set(supports) != set(targets):
        raise ValueError("support and target station sets disagree")
    ordered: dict[int, tuple[int, ...]] = {}
    for i in sorted(supports):
        ys = tuple(sorted(supports[i], key=lambda y: ratio(y, targets[i])))
        if not ys or len(set(ys)) != len(ys) or targets[i] <= 0:
            raise ValueError("empty, duplicate or invalid station support")
        ordered[i] = ys
    ratios = {i: tuple(ratio(y, targets[i]) for y in ys)
              for i, ys in ordered.items()}
    columns: list[str] = []
    rows: list[Row] = []
    n_true = 0
    for i, ys in ordered.items():
        n_true += len(ys) - 1
        for prefix in ("C", "Q") if arm == "B2" else ("C",):
            for k in range(1, len(ys)):
                name = f"otepi_{prefix}_{i}_{k}"
                previous = (variable(f"otepi_{prefix}_{i}_{k-1}") if k > 1 else ZERO)
                base = state_name(i, ys[k-1]) if prefix == "C" else q_name(i, ys[k-1])
                columns.append(name)
                rows.append(row(f"otepi_rec_{prefix}_{i}_{k}", "=",
                                variable(name) - previous - variable(base)))

    def prefix(i: int, k: int, kind: str) -> Expr:
        if k == 0:
            return ZERO
        if k == len(ordered[i]):
            return Expr({}, F(1)) if kind == "C" else variable("G")
        return variable(f"otepi_{kind}_{i}_{k}")

    pair_levels: dict[str, tuple[F, ...]] = {}
    P = K = 0
    stations = sorted(ordered)
    for index, i in enumerate(stations):
        for j in stations[index+1:]:
            levels = tuple(sorted(set(ratios[i]) | set(ratios[j])))
            pair_levels[f"{i}_{j}"] = levels
            p = len(levels) - 1
            if not p:
                continue
            P += p
            K += 1
            summed = ZERO
            for l, (lo, hi) in enumerate(zip(levels, levels[1:]), 1):
                delta = hi - lo
                if delta <= 0:
                    raise AssertionError("nonpositive exact support interval")
                ki = bisect_right(ratios[i], lo)
                kj = bisect_right(ratios[j], lo)
                A = prefix(i, ki, "C") - prefix(j, kj, "C")
                if arm == "B1":
                    v = variable(f"otepi_v_{i}_{j}_{l}")
                    columns.append(next(iter(v.coefficients)))
                    rows.extend((row(f"otepi_abs_pos_{i}_{j}_{l}", ">", v-A),
                                 row(f"otepi_abs_neg_{i}_{j}_{l}", ">", v+A)))
                    summed = summed + delta*v
                else:
                    B = prefix(i, ki, "Q") - prefix(j, kj, "Q")
                    u = variable(f"otepi_u_{i}_{j}_{l}")
                    v = variable(f"otepi_v_{i}_{j}_{l}")
                    columns.extend((next(iter(u.coefficients)), next(iter(v.coefficients))))
                    X, Y = b*A-B, B-a*A
                    rows.extend((row(f"otepi_u_pos_{i}_{j}_{l}", ">", u-X),
                                 row(f"otepi_u_neg_{i}_{j}_{l}", ">", u+X),
                                 row(f"otepi_v_pos_{i}_{j}_{l}", ">", v-Y),
                                 row(f"otepi_v_neg_{i}_{j}_{l}", ">", v+Y)))
                    summed = summed + delta*(u+v)
            scale = b-a if arm == "B2" else F(1)
            rows.append(row(f"otepi_sum_{i}_{j}", ">",
                            scale*variable(h_name(i, j))-summed))
    if len(columns) != len(set(columns)) or len(rows) != len({r.name for r in rows}):
        raise AssertionError("duplicate epigraph name")
    plan = Plan(arm, (a, b), tuple(columns), tuple(rows), n_true, P, K, pair_levels)
    expected_columns = (n_true + P) * (2 if arm == "B2" else 1)
    expected_rows = ((2*n_true + 4*P + K) if arm == "B2" else
                     (n_true + 2*P + K))
    if len(columns) != expected_columns or len(rows) != expected_rows or (
            plan.counts["new_nonzeros"] > plan.counts["nonzero_upper_bound"]):
        raise AssertionError("sparse epigraph count formula failed")
    return plan


def evaluate(row_: Row, values: Mapping[str, F]) -> F:
    return sum((v*values[k] for k, v in row_.coefficients.items()), F(0)) - row_.rhs


def save_exact_plan(plan: Plan, out: Path) -> dict[str, Any]:
    """Persist reconstructible exact rows; the write is charged to its arm."""
    save(out / "new_columns.json", list(plan.columns))
    digest = hashlib.sha256()
    path = out / "new_rows_exact.jsonl"
    with path.open("wb") as stream:
        for item in plan.rows:
            payload = {"name": item.name, "sense": item.sense, "rhs": str(item.rhs),
                       "coefficients": {key: str(value)
                                        for key, value in sorted(item.coefficients.items())}}
            line = (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode()
            digest.update(line)
            stream.write(line)
    return {"new_columns_sha256": sha(out / "new_columns.json"),
            "new_rows_exact_sha256": digest.hexdigest(),
            "new_rows_exact_bytes": path.stat().st_size}


def prepare(out: Path) -> None:
    if out.exists():
        raise FileExistsError(out)
    started = time.perf_counter()
    sources: dict[str, Any] = {}
    for label in SOURCES:
        qualified, path = frozen_source(label)
        sources[label] = {
            "qualification_manifest": str(path.resolve()),
            "qualification_sha256": sha(path), "lp_sha256": qualified["lp_sha256"],
            "input_sha256": qualified["input_sha256"],
            "support_fingerprint": qualified["structure"]["support_fingerprint"],
            "effective_gamma_l": qualified["structure"]["effective_gamma_l"],
            "effective_gamma_u": qualified["structure"]["effective_gamma_u"],
            "leaf_id": qualified["leaf_id"], "parent_id": qualified["parent_id"],
        }
    prereg = {
        "schema": "round88-ot-epigraph-prereg-v1", "status": "prepared_not_admitted",
        "sources": sources, "source_order": list(SOURCES), "arms": list(ARMS),
        "whole_arm_seconds": WHOLE_ARM_SECONDS, "source_arm_order":
            [[s, arm] for s in SOURCES for arm in ARMS],
        "original_lp_each_arm": True, "historical_rowbank_or_warmstart": False,
        "no_internal_budget_or_fallback": True, "script_sha256": sha(SCRIPT),
        "closure_helper_sha256": sha(ROOT / "scripts/round88_ot_closure.py"),
        "math_sha256": sha(ROOT / "scripts/round88_ot_math.py"),
        "diagnostic_sha256": sha(ROOT / "scripts/round88_ot_diagnostic.py"),
        "solver_parameters": SOLVER_PARAMETERS,
    }
    out.mkdir(parents=True, exist_ok=False)
    save(out / "manifest.json", prereg)
    save(out / "preparation_cost.json", {"nested_wall_seconds": time.perf_counter()-started,
                                        "scope": "shared source identity only; not per-arm startup"})


def supervise_prepare(out: Path) -> int:
    started = time.perf_counter()
    if out.exists():
        raise FileExistsError(out)
    command = [sys.executable, str(SCRIPT), "prepare", "--out-dir", str(out.resolve())]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                               check=False)
    out.mkdir(parents=True, exist_ok=True)
    (out / "preparation_stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (out / "preparation_stderr.txt").write_text(completed.stderr, encoding="utf-8")
    save(out / "preparation_supervision.json", {
        "status": "prepared" if completed.returncode == 0 else "preparation_failed",
        "external_launch_to_exit_wall_seconds": time.perf_counter()-started,
        "command": command, "returncode": completed.returncode,
        "manifest_sha256": sha(out / "manifest.json") if (out / "manifest.json").is_file() else None})
    return completed.returncode


def verify_prepared(manifest_path: Path, source: str, arm: str) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = read(manifest_path)
    if (manifest.get("schema") != "round88-ot-epigraph-prereg-v1" or
            manifest.get("source_order") != list(SOURCES) or
            manifest.get("arms") != list(ARMS) or
            manifest.get("source_arm_order") != [[s, x] for s in SOURCES for x in ARMS] or
            manifest.get("whole_arm_seconds") != WHOLE_ARM_SECONDS or
            manifest.get("solver_parameters") != SOLVER_PARAMETERS or
            set(manifest.get("sources", {})) != set(SOURCES) or
            not manifest.get("original_lp_each_arm") or
            manifest.get("historical_rowbank_or_warmstart") is not False or
            not manifest.get("no_internal_budget_or_fallback")):
        raise ValueError("epigraph preregistration drift")
    paths = {"script_sha256": SCRIPT,
             "closure_helper_sha256": ROOT / "scripts/round88_ot_closure.py",
             "math_sha256": ROOT / "scripts/round88_ot_math.py",
             "diagnostic_sha256": ROOT / "scripts/round88_ot_diagnostic.py"}
    if any(manifest.get(key) != sha(path) for key, path in paths.items()):
        raise ValueError("script/helper identity drift")
    if source not in SOURCES or arm not in ARMS:
        raise ValueError("unregistered source or arm")
    qualified, path = frozen_source(source)
    saved = manifest["sources"][source]
    if (saved["qualification_sha256"] != sha(path) or
            saved["lp_sha256"] != qualified["lp_sha256"] or
            saved["input_sha256"] != qualified["input_sha256"] or
            saved["support_fingerprint"] != qualified["structure"]["support_fingerprint"] or
            saved["effective_gamma_l"] != qualified["structure"]["effective_gamma_l"] or
            saved["effective_gamma_u"] != qualified["structure"]["effective_gamma_u"]):
        raise ValueError("qualified source identity drift")
    return manifest, qualified


def require_lease(manifest_path: Path, source: str, arm: str) -> None:
    expected = {"schema": "round88-ot-epigraph-lease-v1", "authorized_by": "Astra",
                "allow_optimize": True, "manifest_sha256": sha(manifest_path),
                "source_arms": [[s, x] for s in SOURCES for x in ARMS]}
    if read(LEASE) != expected or [source, arm] not in expected["source_arms"]:
        raise ValueError("missing or altered epigraph Optimize lease")


def _finite_float(value: F) -> float:
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError("nonfinite epigraph coefficient")
    return converted


def add_plan(model: Any, plan: Plan) -> dict[str, int]:
    import gurobipy as gp
    existing = {var.VarName for var in model.getVars()}
    existing_rows = {c.ConstrName for c in model.getConstrs()}
    if set(plan.columns) & existing or any(r.name in existing_rows for r in plan.rows):
        raise ValueError("epigraph names collide with original model")
    before = (model.NumVars, model.NumConstrs, model.NumNZs)
    variables = {v.VarName: v for v in model.getVars()}
    for name in plan.columns:
        variables[name] = model.addVar(lb=0.0, obj=0.0, vtype=gp.GRB.CONTINUOUS, name=name)
    model.update()
    for item in plan.rows:
        lhs = gp.LinExpr([_finite_float(coef) for coef in item.coefficients.values()],
                         [variables[name] for name in item.coefficients])
        rhs = _finite_float(item.rhs)
        if item.sense == "=":
            model.addConstr(lhs == rhs, name=item.name)
        else:
            model.addConstr(lhs >= rhs, name=item.name)
    model.update()
    actual = {"new_columns": model.NumVars-before[0],
              "new_rows": model.NumConstrs-before[1],
              "new_nonzeros": model.NumNZs-before[2]}
    if any(actual[key] != plan.counts[key] for key in actual):
        raise ValueError(f"planned/actual sparse matrix mismatch: {actual} vs {plan.counts}")
    return actual


def primal_residuals(model: Any, out: Path, original_rows: int) -> dict[str, Any]:
    from round88_ot_diagnostic import row_terms
    values = {v.VarName: v.X for v in model.getVars()}
    save(out / "primal.json", values)
    maxima = {"original": 0.0, "epigraph": 0.0, "bounds": 0.0}
    with (out / "all_row_residuals.jsonl").open("w", encoding="utf-8") as stream:
        for index, constr in enumerate(model.getConstrs()):
            lhs = math.fsum(coef*values[name] for name, coef in row_terms(model, constr).items())
            violation = (max(0.0, constr.RHS-lhs) if constr.Sense == ">" else
                         max(0.0, lhs-constr.RHS) if constr.Sense == "<" else
                         abs(lhs-constr.RHS) if constr.Sense == "=" else float("inf"))
            family = "original" if index < original_rows else "epigraph"
            maxima[family] = max(maxima[family], violation)
            stream.write(json.dumps({"index": index, "name": constr.ConstrName,
                                     "family": family, "sense": constr.Sense,
                                     "lhs": lhs, "rhs": constr.RHS,
                                     "violation": violation}, allow_nan=False)+"\n")
    for var in model.getVars():
        maxima["bounds"] = max(maxima["bounds"], var.LB-var.X, var.X-var.UB)
    save(out / "residuals.json", maxima)
    return maxima


def diagnose(manifest_path: Path, source: str, arm: str, out: Path) -> None:
    ready = Path(os.environ["ROUND88_OT_EPIGRAPH_READY_PATH"])
    while not ready.is_file():
        time.sleep(0.01)
    started = time.perf_counter()
    out.mkdir(parents=True, exist_ok=False)
    save(out / "inflight.json", {"phase": "source_verification", "source": source,
                                 "arm": arm, "manifest_sha256": sha(manifest_path)})
    require_lease(manifest_path, source, arm)
    t = time.perf_counter()
    prepared, qualified = verify_prepared(manifest_path, source, arm)
    identity_seconds = time.perf_counter()-t
    from gurobipy import GRB
    from round88_ot_diagnostic import (audit_model, configure, load_model,
                                       process_peak_memory_bytes, read_instance)
    input_path, lp = Path(qualified["input"]), Path(qualified["lp"])
    instance = read_instance(input_path)
    t = time.perf_counter()
    original = load_model(lp)
    read_seconds = time.perf_counter()-t
    t = time.perf_counter()
    structure = audit_model(original, instance, F(qualified["gamma_l"]),
                            F(qualified["gamma_u"]), qualified["verified_ub"],
                            qualified["lambda"])
    audit_seconds = time.perf_counter()-t
    if structure != qualified["structure"]:
        raise ValueError("actual model differs from qualified original LP")
    a, b = F(structure["effective_gamma_l"]), F(structure["effective_gamma_u"])
    supports = {int(k): v for k, v in structure["support"].items()}
    t = time.perf_counter()
    model = original.relax()
    relax_seconds = time.perf_counter()-t
    if any(var.VType != GRB.CONTINUOUS for var in model.getVars()):
        raise ValueError("LP relaxation retained integer variables")
    original_counts = {"variables": model.NumVars, "rows": model.NumConstrs,
                       "nonzeros": model.NumNZs}
    original_rows = model.NumConstrs
    t = time.perf_counter()
    plan = make_plan(arm, supports, instance["targets"], a, b)
    plan_seconds = time.perf_counter()-t
    t = time.perf_counter()
    plan_files = save_exact_plan(plan, out)
    plan_evidence_seconds = time.perf_counter()-t
    t = time.perf_counter()
    actual = add_plan(model, plan)
    build_seconds = time.perf_counter()-t
    provenance = {
        "schema": "round88-ot-epigraph-arm-v1", "source": source, "arm": arm,
        "manifest_sha256": sha(manifest_path), "qualification_manifest_sha256":
            prepared["sources"][source]["qualification_sha256"],
        "lp": str(lp), "lp_sha256": qualified["lp_sha256"],
        "input": str(input_path), "input_sha256": qualified["input_sha256"],
        "source_sha256": qualified["source_sha256"],
        "binary_sha256": qualified["binary_sha256"],
        "scenario_id": qualified["scenario_id"], "T_seconds": qualified["T"],
        "lambda": qualified["lambda"], "pickup_seconds": qualified["pickup_time"],
        "drop_seconds": qualified["drop_time"], "verified_cutoff_UB": qualified["verified_ub"],
        "leaf_id": qualified["leaf_id"], "parent_id": qualified["parent_id"],
        "support_fingerprint": structure["support_fingerprint"],
        "effective_gamma_l": str(a), "effective_gamma_u": str(b),
        "original_model": original_counts, "predicted_additions": plan.counts,
        "actual_additions": actual, "exact_plan_files": plan_files,
        "full_support": structure["support"], "pair_interval_counts":
            {key: len(levels)-1 for key, levels in plan.pair_levels.items()},
        "whole_arm_deadline_seconds": WHOLE_ARM_SECONDS,
        "no_historical_rows_or_warmstart": True, "no_mip_transition": True,
        "gurobi_version": __import__("gurobipy").gurobi.version(),
        "costs": {"identity_seconds": identity_seconds, "model_read_seconds": read_seconds,
                  "structure_audit_seconds": audit_seconds, "relax_seconds": relax_seconds,
                  "rational_plan_seconds": plan_seconds,
                  "plan_evidence_write_seconds": plan_evidence_seconds,
                  "matrix_build_seconds": build_seconds,
                  "process_wall_through_build_seconds": time.perf_counter()-started}}
    save(out / "provenance.json", provenance)
    save(out / "inflight.json", {"phase": "optimize", "elapsed_seconds": time.perf_counter()-started,
                                 "predicted_additions": plan.counts})
    configure(model, out / "optimizer.log")
    t = time.perf_counter()
    model.optimize()
    optimize_seconds = time.perf_counter()-t
    result: dict[str, Any] = {
        "schema": "round88-ot-epigraph-result-v1", "source": source, "arm": arm,
        "manifest_sha256": sha(manifest_path), "lp_sha256": qualified["lp_sha256"],
        "status_code": model.Status, "optimize_wall_seconds": optimize_seconds,
        "solver_runtime_seconds": model.Runtime, "solver_work": model.Work,
        "process_peak_working_set_bytes_so_far": process_peak_memory_bytes(),
        "final_model": {"variables": model.NumVars, "rows": model.NumConstrs,
                        "nonzeros": model.NumNZs},
        "process_wall_through_optimize_seconds": time.perf_counter()-started,
        "scope": "Numerical fixed-LP diagnostic; not a rational LB or whole-method certificate"}
    if model.Status == GRB.OPTIMAL:
        result["objective"] = model.ObjVal
        save(out / "inflight.json", {"phase": "primal_and_residual_audit",
                                     "elapsed_seconds": time.perf_counter()-started})
        t = time.perf_counter()
        residuals = primal_residuals(model, out, original_rows)
        result["primal_audit_wall_seconds"] = time.perf_counter()-t
        result["residuals"] = residuals
        result["status"] = ("numeric_rejection_original_or_added_rows" if
                            max(residuals.values()) > 1e-5 else "complete_optimal_numeric_lp")
    elif model.Status == GRB.INFEASIBLE:
        result["status"] = "observed_lp_infeasible_requires_scope_audit"
    else:
        result["status"] = "unknown_lp_not_optimal"
    result["process_wall_through_result_seconds"] = time.perf_counter()-started
    save(out / "result.json", result)


def supervise(manifest_path: Path, source: str, arm: str, out: Path) -> int:
    started = time.perf_counter()
    out.mkdir(parents=True, exist_ok=False)
    process: subprocess.Popen[str] | None = None
    job: _WindowsJob | None = None
    stdout = stderr = ""
    expired = assigned = False
    before = sha(manifest_path) if manifest_path.is_file() else None
    command: list[str] | None = None
    try:
        require_lease(manifest_path, source, arm)
        verify_prepared(manifest_path, source, arm)
        command = [sys.executable, str(SCRIPT), "diagnose", "--manifest",
                   str(manifest_path.resolve()), "--source", source, "--arm", arm,
                   "--out-dir", str((out / "diagnostic").resolve())]
        if time.perf_counter()-started >= WHOLE_ARM_SECONDS:
            expired = True
        else:
            ready = out / "supervisor_ready.flag"
            env = os.environ.copy()
            env["ROUND88_OT_EPIGRAPH_READY_PATH"] = str(ready)
            if os.name == "nt":
                job = _WindowsJob()
            process = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True,
                                       creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
                                       start_new_session=os.name != "nt")
            if job:
                job.assign(process)
                assigned = True
            ready.write_text("assigned\n", encoding="ascii")
            stdout, stderr, expired = _wait_with_deadline(
                process, job, max(0.0, WHOLE_ARM_SECONDS-(time.perf_counter()-started)))
            if job:
                job.close()
    except Exception as exc:
        if process:
            _kill_tree(process, job)
        elif job:
            job.close()
        stderr += "\nsupervisor_exception=" + repr(exc)
    (out / "stdout.txt").write_text(stdout, encoding="utf-8")
    (out / "stderr.txt").write_text(stderr, encoding="utf-8")
    after = sha(manifest_path) if manifest_path.is_file() else None
    identity_ok = False
    if after == before and before is not None:
        try:
            require_lease(manifest_path, source, arm)
            verify_prepared(manifest_path, source, arm)
            identity_ok = True
        except Exception as exc:
            stderr += "\nfinal_identity_exception=" + repr(exc)
            (out / "stderr.txt").write_text(stderr, encoding="utf-8")
    elapsed = time.perf_counter()-started
    child_path = out / "diagnostic/result.json"
    child: dict[str, Any] | None = None
    if child_path.is_file():
        try:
            loaded = read(child_path)
            if isinstance(loaded, dict) and isinstance(loaded.get("status"), str) and (
                    loaded["status"] in CHILD_STATUSES):
                child = loaded
            else:
                stderr += "\ninvalid_result_structure_or_status"
                (out / "stderr.txt").write_text(stderr, encoding="utf-8")
        except (OSError, ValueError) as exc:
            stderr += "\nresult_read_exception=" + repr(exc)
            (out / "stderr.txt").write_text(stderr, encoding="utf-8")
    if expired or elapsed > WHOLE_ARM_SECONDS:
        status = "unknown_whole_diagnostic_deadline"
    elif not identity_ok:
        status = "invalid_source_or_manifest_drift"
    elif process is None or process.returncode != 0 or child is None:
        status = "invalid_or_unknown_diagnostic_failure"
    elif (child.get("manifest_sha256") != before or child.get("source") != source or
          child.get("arm") != arm):
        status = "invalid_result_identity"
    else:
        status = child["status"]
    receipt = {"status": status, "whole_arm_limit_seconds": WHOLE_ARM_SECONDS,
               "whole_arm_wall_seconds_before_receipt": elapsed,
               "returncode": process.returncode if process else None,
               "child_pid": process.pid if process else None, "command": command,
               "source": source, "arm": arm, "manifest_sha256_before": before,
               "manifest_sha256_after": after, "source_identity_consistent_after": identity_ok,
               "child_result_status": child.get("status") if child else None,
               "timed_out": expired or elapsed > WHOLE_ARM_SECONDS,
               "job_object_assigned": assigned if os.name == "nt" else None}
    save(out / "supervision.json", receipt)
    after_write = time.perf_counter()-started
    if after_write > WHOLE_ARM_SECONDS and status != "unknown_whole_diagnostic_deadline":
        receipt["status"] = "unknown_whole_diagnostic_deadline"
        receipt["timed_out"] = True
        receipt["after_first_receipt_wall_seconds"] = after_write
        save(out / "supervision.json", receipt)
    print(receipt["status"])
    return (0 if receipt["status"] in CHILD_STATUSES
            else 124 if receipt["status"] == "unknown_whole_diagnostic_deadline" else 125)


def run_batch(manifest_path: Path, out: Path) -> int:
    """Six independent arms; deadline unknown continues, correctness failure stops."""
    if out.exists():
        raise FileExistsError(out)
    started = time.perf_counter()
    out.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, Any]] = []
    continuable = {"complete_optimal_numeric_lp", "unknown_whole_diagnostic_deadline"}
    for source in SOURCES:
        for arm in ARMS:
            name = f"{len(records)+1:02d}_{source}_{arm}"
            code = supervise(manifest_path, source, arm, out / name)
            receipt = read(out / name / "supervision.json")
            records.append({"source": source, "arm": arm, "directory": name,
                            "status": receipt["status"], "supervisor_returncode": code,
                            "whole_arm_wall_seconds_before_receipt":
                                receipt["whole_arm_wall_seconds_before_receipt"]})
            save(out / "batch_summary.json", {
                "schema": "round88-ot-epigraph-batch-v1", "manifest_sha256": sha(manifest_path),
                "records": records, "completed_arms": len(records),
                "sum_whole_arm_wall_seconds_before_receipt":
                    sum(r["whole_arm_wall_seconds_before_receipt"] for r in records),
                "outside_batch_wall_seconds_so_far": time.perf_counter()-started,
                "status": ("running" if receipt["status"] in continuable else
                           "stopped_correctness_identity_or_resource_signal")})
            if receipt["status"] not in continuable:
                return 125
    summary = read(out / "batch_summary.json")
    summary["status"] = "six_independent_arms_complete_or_unknown"
    summary["outside_batch_wall_seconds"] = time.perf_counter()-started
    save(out / "batch_summary.json", summary)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prepare", "prepare-supervise"):
        part = commands.add_parser(name)
        part.add_argument("--out-dir", type=Path, required=True)
    for name in ("diagnose", "supervise"):
        part = commands.add_parser(name)
        part.add_argument("--manifest", type=Path, required=True)
        part.add_argument("--source", choices=tuple(SOURCES), required=True)
        part.add_argument("--arm", choices=ARMS, required=True)
        part.add_argument("--out-dir", type=Path, required=True)
    batch = commands.add_parser("run-batch")
    batch.add_argument("--manifest", type=Path, required=True)
    batch.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.out_dir)
        return 0
    if args.command == "prepare-supervise":
        return supervise_prepare(args.out_dir)
    if args.command == "supervise":
        return supervise(args.manifest, args.source, args.arm, args.out_dir)
    if args.command == "run-batch":
        return run_batch(args.manifest, args.out_dir)
    diagnose(args.manifest, args.source, args.arm, args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
