#!/usr/bin/env python3
"""Full-matrix rank-1 split-cut separation for Round 44 LP artifacts.

The separator treats every linear row and every finite variable bound as a
row of ``A x >= b``.  It solves the normalized CGLP from the frozen Round 44
protocol, independently replays both multiplier identities, and adds a cut
only when the audited violation exceeds ``epsilon_sep``.  Repeated separation
continues until the CGLP proves that no violated normalized cut remains.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCAL_DEPS = ROOT / "work" / "round44_pydeps"
if LOCAL_DEPS.is_dir():
    sys.path.insert(0, str(LOCAL_DEPS))

import gurobipy as gp  # type: ignore  # noqa: E402
import numpy as np  # noqa: E402
from scipy import sparse  # noqa: E402


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"cannot write empty CSV: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _json_sparse(values: np.ndarray, tolerance: float = 1e-12) -> str:
    return json.dumps(
        [[int(index), float(value)] for index, value in enumerate(values)
         if abs(float(value)) > tolerance],
        separators=(",", ":"))


def _constraint_system(model: gp.Model) -> tuple[sparse.csr_matrix, np.ndarray,
                                                   list[str]]:
    """Return the complete finite parent system in canonical >= form."""
    matrix = sparse.csr_matrix(model.getA(), dtype=float)
    constraints = model.getConstrs()
    senses = np.asarray(model.getAttr(gp.GRB.Attr.Sense, constraints))
    rhs = np.asarray(model.getAttr(gp.GRB.Attr.RHS, constraints), dtype=float)
    names = list(model.getAttr(gp.GRB.Attr.ConstrName, constraints))
    rows: list[sparse.csr_matrix] = []
    bounds: list[float] = []
    labels: list[str] = []
    for index, sense in enumerate(senses):
        row = matrix.getrow(index)
        if sense in (gp.GRB.GREATER_EQUAL, gp.GRB.EQUAL):
            rows.append(row)
            bounds.append(float(rhs[index]))
            labels.append(f"row:{names[index]}:ge")
        if sense in (gp.GRB.LESS_EQUAL, gp.GRB.EQUAL):
            rows.append(-row)
            bounds.append(float(-rhs[index]))
            labels.append(f"row:{names[index]}:le")

    variables = model.getVars()
    lower = np.asarray(model.getAttr(gp.GRB.Attr.LB, variables), dtype=float)
    upper = np.asarray(model.getAttr(gp.GRB.Attr.UB, variables), dtype=float)
    variable_names = list(model.getAttr(gp.GRB.Attr.VarName, variables))
    columns = len(variables)
    for index in range(columns):
        if math.isfinite(float(lower[index])) and lower[index] > -gp.GRB.INFINITY:
            rows.append(sparse.csr_matrix(
                ([1.0], ([0], [index])), shape=(1, columns)))
            bounds.append(float(lower[index]))
            labels.append(f"bound:{variable_names[index]}:lb")
        if math.isfinite(float(upper[index])) and upper[index] < gp.GRB.INFINITY:
            rows.append(sparse.csr_matrix(
                ([-1.0], ([0], [index])), shape=(1, columns)))
            bounds.append(float(-upper[index]))
            labels.append(f"bound:{variable_names[index]}:ub")
    return sparse.vstack(rows, format="csr"), np.asarray(bounds), labels


def _separate(model: gp.Model, gamma: float, epsilon_sep: float,
              source_id: str, round_index: int) -> tuple[dict[str, Any],
                                                         dict[str, Any] | None]:
    variables = model.getVars()
    names = list(model.getAttr(gp.GRB.Attr.VarName, variables))
    if "G" not in names:
        raise RuntimeError("canonical parent model has no G variable")
    g = np.zeros(len(variables), dtype=float)
    g[names.index("G")] = 1.0
    x_bar = np.asarray(model.getAttr(gp.GRB.Attr.X, variables), dtype=float)
    A, b, row_labels = _constraint_system(model)
    row_count, column_count = A.shape

    cglp = gp.Model(f"round44_cglp_{source_id}_{round_index}")
    cglp.Params.OutputFlag = 0
    cglp.Params.Threads = 1
    cglp.Params.Seed = 0
    cglp.Params.Presolve = -1
    u_minus = cglp.addMVar(row_count, lb=0.0, name="u_minus")
    u_plus = cglp.addMVar(row_count, lb=0.0, name="u_plus")
    lambda_minus = cglp.addVar(lb=0.0, name="lambda_minus")
    lambda_plus = cglp.addVar(lb=0.0, name="lambda_plus")
    pi = cglp.addMVar(column_count, lb=-gp.GRB.INFINITY, name="pi")
    pi0 = cglp.addVar(lb=-gp.GRB.INFINITY, name="pi0")
    left_coefficients = A.transpose() @ u_minus
    right_coefficients = A.transpose() @ u_plus
    g_index = names.index("G")
    for index in range(column_count):
        cglp.addConstr(
            pi[index] == left_coefficients[index] -
            (lambda_minus if index == g_index else 0.0),
            name=f"left_coefficient_identity_{index}")
        cglp.addConstr(
            pi[index] == right_coefficients[index] +
            (lambda_plus if index == g_index else 0.0),
            name=f"right_coefficient_identity_{index}")
    cglp.addConstr(
        pi0 <= b @ u_minus - gamma * lambda_minus,
        name="left_rhs_validity")
    cglp.addConstr(
        pi0 <= b @ u_plus + gamma * lambda_plus,
        name="right_rhs_validity")
    cglp.addConstr(
        u_minus.sum() + u_plus.sum() + lambda_minus + lambda_plus == 1.0,
        name="finite_normalization")
    cglp.setObjective(pi0 - x_bar @ pi, gp.GRB.MAXIMIZE)
    started = time.monotonic()
    cglp.optimize()
    wall_seconds = time.monotonic() - started
    if cglp.Status != gp.GRB.OPTIMAL:
        raise RuntimeError(f"CGLP did not solve to optimality: {cglp.Status}")

    um = np.asarray(u_minus.X, dtype=float)
    up = np.asarray(u_plus.X, dtype=float)
    lm = float(lambda_minus.X)
    lp = float(lambda_plus.X)
    pi_value = np.asarray(pi.X, dtype=float)
    pi0_value = float(pi0.X)
    left_coeff = pi_value - (A.transpose() @ um - lm * g)
    right_coeff = pi_value - (A.transpose() @ up + lp * g)
    left_rhs_slack = float(b @ um - lm * gamma - pi0_value)
    right_rhs_slack = float(b @ up + lp * gamma - pi0_value)
    normalization = float(um.sum() + up.sum() + lm + lp)
    violation = float(pi0_value - pi_value @ x_bar)
    multiplier_nonnegative = (
        float(um.min(initial=0.0)) >= -1e-9 and
        float(up.min(initial=0.0)) >= -1e-9 and lm >= -1e-9 and lp >= -1e-9)
    max_identity_residual = max(
        float(np.max(np.abs(left_coeff), initial=0.0)),
        float(np.max(np.abs(right_coeff), initial=0.0)))
    audit_valid = (
        multiplier_nonnegative and abs(normalization - 1.0) <= 1e-8 and
        max_identity_residual <= 1e-7 and left_rhs_slack >= -1e-7 and
        right_rhs_slack >= -1e-7 and math.isfinite(violation))
    audit = {
        "source_interval": source_id,
        "round": round_index,
        "parent_rows_ge": row_count,
        "parent_columns": column_count,
        "gamma": gamma,
        "normalization": normalization,
        "multiplier_nonnegative": multiplier_nonnegative,
        "left_coefficient_residual_inf": float(np.max(
            np.abs(left_coeff), initial=0.0)),
        "right_coefficient_residual_inf": float(np.max(
            np.abs(right_coeff), initial=0.0)),
        "left_rhs_slack": left_rhs_slack,
        "right_rhs_slack": right_rhs_slack,
        "current_lp_violation": violation,
        "epsilon_sep": epsilon_sep,
        "cglp_solver_seconds": float(cglp.Runtime),
        "cglp_wall_seconds": wall_seconds,
        "cglp_work": float(cglp.Work),
        "cglp_nodes": float(cglp.NodeCount),
        "audit_valid": audit_valid,
        "cut_accepted": audit_valid and violation > epsilon_sep,
        "u_minus_sparse": _json_sparse(um),
        "u_plus_sparse": _json_sparse(up),
        "lambda_minus": lm,
        "lambda_plus": lp,
        "pi_sparse": _json_sparse(pi_value),
        "pi0": pi0_value,
        "row_labels_json": json.dumps(row_labels, separators=(",", ":")),
        "variable_names_json": json.dumps(names, separators=(",", ":")),
    }
    if not audit_valid:
        raise RuntimeError(f"invalid CGLP multiplier certificate: {audit}")
    if violation <= epsilon_sep:
        return audit, None
    coefficients = {
        name: float(value) for name, value in zip(names, pi_value)
        if abs(float(value)) > 1e-12
    }
    cut = {
        "source_interval": source_id,
        "round": round_index,
        "source_disjunction": f"G<={gamma:.17g}|G>={gamma:.17g}",
        "propagation_scope": "source-interval-and-nested-descendants",
        "sense": ">=",
        "rhs": pi0_value,
        "violation": violation,
        "coefficient_count": len(coefficients),
        "coefficients_json": json.dumps(coefficients, separators=(",", ":")),
        "certificate_status": "audited_valid_violated_rank1_cut",
    }
    return audit, cut


def separate_model(model_path: Path, gamma: float, source_id: str,
                   epsilon_sep: float) -> tuple[list[dict[str, Any]],
                                                list[dict[str, Any]], gp.Model]:
    model = gp.read(str(model_path))
    model.Params.OutputFlag = 0
    model.Params.Threads = 1
    model.Params.Seed = 0
    model.Params.Presolve = -1
    for variable in model.getVars():
        variable.VType = gp.GRB.CONTINUOUS
    model.update()
    audits: list[dict[str, Any]] = []
    cuts: list[dict[str, Any]] = []
    round_index = 0
    while True:
        model.optimize()
        if model.Status != gp.GRB.OPTIMAL:
            raise RuntimeError(
                f"parent LP is not complete optimal: status {model.Status}")
        audit, cut = _separate(
            model, gamma, epsilon_sep, source_id, round_index)
        audits.append(audit)
        if cut is None:
            cuts.append({
                "source_interval": source_id,
                "round": round_index,
                "source_disjunction": f"G<={gamma:.17g}|G>={gamma:.17g}",
                "propagation_scope":
                    "source-interval-and-nested-descendants",
                "sense": ">=",
                "rhs": audit["pi0"],
                "violation": audit["current_lp_violation"],
                "coefficient_count": 0,
                "coefficients_json": "{}",
                "certificate_status":
                    "audited_no_violated_normalized_rank1_cut",
            })
            break
        cuts.append(cut)
        coefficients = json.loads(cut["coefficients_json"])
        expression = gp.LinExpr(
            list(coefficients.values()),
            [model.getVarByName(name) for name in coefficients])
        model.addConstr(
            expression >= float(cut["rhs"]),
            name=f"round44_rank1_{source_id}_{round_index}")
        model.update()
        round_index += 1
    return audits, cuts, model


def run(model_path: Path, gamma: float, source_id: str, epsilon_sep: float,
        cut_ledger: Path, audit_ledger: Path, output_model: Path) -> None:
    audits, cuts, model = separate_model(
        model_path, gamma, source_id, epsilon_sep)
    output_model.parent.mkdir(parents=True, exist_ok=True)
    model.write(str(output_model))
    _write_csv(cut_ledger, cuts)
    _write_csv(audit_ledger, audits)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--gamma", type=float, required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--epsilon-sep", type=float, default=1e-7)
    parser.add_argument("--cut-ledger", type=Path, required=True)
    parser.add_argument("--audit-ledger", type=Path, required=True)
    parser.add_argument("--output-model", type=Path, required=True)
    args = parser.parse_args()
    run(args.model, args.gamma, args.source_id, args.epsilon_sep,
        args.cut_ledger, args.audit_ledger, args.output_model)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
