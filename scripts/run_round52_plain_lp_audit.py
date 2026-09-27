#!/usr/bin/env python3
"""Solve paired Round 51 v0/M1 canonical models as plain continuous LPs."""

from __future__ import annotations

import csv
import ctypes
import hashlib
import json
import math
import os
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUND51 = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"
OUT = ROOT / "results" / "gf_k1_tailored_cut_final_validation_round52"
DLL = Path(os.environ.get("GUROBI_HOME", "D:/gurobi1302/win64")) / "bin" / "gurobi130.dll"
CERT_EPS = 1e-7
PROCESS_CAP_SECONDS = 1800.0
PER_MODEL_CAP_SECONDS = 60.0


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Gurobi:
    def __init__(self) -> None:
        if not DLL.exists():
            raise FileNotFoundError(DLL)
        self.lib = ctypes.WinDLL(str(DLL))
        void_p = ctypes.c_void_p
        int_p = ctypes.POINTER(ctypes.c_int)
        dbl_p = ctypes.POINTER(ctypes.c_double)
        char_p = ctypes.POINTER(ctypes.c_char)
        self._bind("GRBemptyenvinternal", ctypes.c_int,
                   [ctypes.POINTER(void_p), ctypes.c_int, ctypes.c_int, ctypes.c_int])
        self._bind("GRBstartenv", ctypes.c_int, [void_p])
        self._bind("GRBfreeenv", None, [void_p])
        self._bind("GRBgeterrormsg", ctypes.c_char_p, [void_p])
        self._bind("GRBsetintparam", ctypes.c_int,
                   [void_p, ctypes.c_char_p, ctypes.c_int])
        self._bind("GRBsetdblparam", ctypes.c_int,
                   [void_p, ctypes.c_char_p, ctypes.c_double])
        self._bind("GRBreadmodel", ctypes.c_int,
                   [void_p, ctypes.c_char_p, ctypes.POINTER(void_p)])
        self._bind("GRBfreemodel", None, [void_p])
        self._bind("GRBgetenv", void_p, [void_p])
        self._bind("GRBgetintattr", ctypes.c_int,
                   [void_p, ctypes.c_char_p, int_p])
        self._bind("GRBgetdblattr", ctypes.c_int,
                   [void_p, ctypes.c_char_p, dbl_p])
        self._bind("GRBgetcharattrarray", ctypes.c_int,
                   [void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, char_p])
        self._bind("GRBsetcharattrarray", ctypes.c_int,
                   [void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, char_p])
        self._bind("GRBupdatemodel", ctypes.c_int, [void_p])
        self._bind("GRBoptimize", ctypes.c_int, [void_p])
        self.env = void_p()
        self.check(self.lib.GRBemptyenvinternal(ctypes.byref(self.env), 13, 0, 2))
        self.check(self.lib.GRBsetintparam(self.env, b"LogToConsole", 0))
        self.check(self.lib.GRBstartenv(self.env))

    def _bind(self, name: str, restype: object, argtypes: list[object]) -> None:
        fn = getattr(self.lib, name)
        fn.restype = restype
        fn.argtypes = argtypes

    def error(self) -> str:
        raw = self.lib.GRBgeterrormsg(self.env)
        return raw.decode("utf-8", errors="replace") if raw else "unknown"

    def check(self, rc: int) -> None:
        if rc:
            raise RuntimeError(f"Gurobi error {rc}: {self.error()}")

    def close(self) -> None:
        if self.env:
            self.lib.GRBfreeenv(self.env)
            self.env = ctypes.c_void_p()

    def int_attr(self, model: ctypes.c_void_p, name: str) -> int:
        value = ctypes.c_int()
        self.check(self.lib.GRBgetintattr(model, name.encode(), ctypes.byref(value)))
        return value.value

    def dbl_attr(self, model: ctypes.c_void_p, name: str) -> float:
        value = ctypes.c_double()
        self.check(self.lib.GRBgetdblattr(model, name.encode(), ctypes.byref(value)))
        return value.value

    def solve_relaxation(self, path: Path, time_limit: float) -> dict[str, object]:
        model = ctypes.c_void_p()
        self.check(self.lib.GRBreadmodel(
            self.env, str(path.resolve()).encode("utf-8"), ctypes.byref(model)))
        try:
            model_env = self.lib.GRBgetenv(model)
            for name, value in ((b"Presolve", -1), (b"Seed", 0),
                                (b"Threads", 1), (b"Method", -1)):
                self.check(self.lib.GRBsetintparam(model_env, name, value))
            for name, value in ((b"MIPGap", 0.0), (b"MIPGapAbs", 0.0),
                                (b"TimeLimit", time_limit)):
                self.check(self.lib.GRBsetdblparam(model_env, name, value))
            nvars = self.int_attr(model, "NumVars")
            original = (ctypes.c_char * nvars)()
            self.check(self.lib.GRBgetcharattrarray(
                model, b"VType", 0, nvars, original))
            original_types = bytes(original)
            relaxed = (ctypes.c_char * nvars)(*([b"C"] * nvars))
            self.check(self.lib.GRBsetcharattrarray(
                model, b"VType", 0, nvars, relaxed))
            self.check(self.lib.GRBupdatemodel(model))
            self.check(self.lib.GRBoptimize(model))
            status = self.int_attr(model, "Status")
            row: dict[str, object] = {
                "status_code": status,
                "status": {2: "OPTIMAL", 3: "INFEASIBLE", 4: "INF_OR_UNBD",
                           5: "UNBOUNDED", 9: "TIME_LIMIT"}.get(status, f"STATUS_{status}"),
                "original_variable_count": nvars,
                "original_continuous_variables": original_types.count(ord("C")),
                "original_integer_variables": original_types.count(ord("I")),
                "original_binary_variables": original_types.count(ord("B")),
                "relaxed_variable_count": nvars,
                "all_variables_continuous": True,
                "rows": self.int_attr(model, "NumConstrs"),
                "nonzeros": self.int_attr(model, "NumNZs"),
                "solver_runtime_seconds": self.dbl_attr(model, "Runtime"),
                "solver_work": self.dbl_attr(model, "Work"),
                "simplex_iterations": self.dbl_attr(model, "IterCount"),
            }
            if status == 2:
                row["objective"] = self.dbl_attr(model, "ObjVal")
            else:
                row["objective"] = math.nan
            return row
        finally:
            self.lib.GRBfreemodel(model)


def main() -> None:
    start = time.monotonic()
    with (ROUND51 / "big_m_model_delta_audit.csv").open(
            encoding="utf-8", newline="") as src:
        affected = [row for row in csv.DictReader(src)
                    if row["big_m_affected"].lower() == "true"]
    if len(affected) != 15:
        raise RuntimeError(f"expected 15 affected states, found {len(affected)}")
    solver = Gurobi()
    output_rows: list[dict[str, object]] = []
    try:
        for audit in affected:
            state = audit["state_id"]
            pair: dict[str, dict[str, object]] = {}
            for label, policy, expected_hash in (
                ("v0", "interval-mip-v0", audit["historical_model_sha256"]),
                ("M1", "m1-tight-big-m-v0", audit["m1_model_sha256"]),
            ):
                model = (ROUND51 / "model_audit_runs" /
                         f"{state}__{policy}" / "canonical_model.lp")
                if not model.exists():
                    raise FileNotFoundError(model)
                model_sha = digest(model)
                if model_sha != expected_hash:
                    raise RuntimeError(
                        f"{state} {label} canonical model hash mismatch")
                elapsed = time.monotonic() - start
                remaining = PROCESS_CAP_SECONDS - elapsed - 5.0
                if remaining <= 0:
                    raise TimeoutError("plain-LP audit process cap exhausted")
                solved = solver.solve_relaxation(
                    model, min(PER_MODEL_CAP_SECONDS, remaining))
                solved.update({"policy": policy, "model_path": model.relative_to(ROOT).as_posix(),
                               "model_sha256": model_sha})
                pair[label] = solved
            v0 = float(pair["v0"]["objective"])
            m1 = float(pair["M1"]["objective"])
            passed = (pair["v0"]["status"] == "OPTIMAL" and
                      pair["M1"]["status"] == "OPTIMAL" and
                      m1 >= v0 - CERT_EPS)
            output_rows.append({
                "state_id": state,
                "big_m_affected": True,
                "v0_model_path": pair["v0"]["model_path"],
                "v0_model_sha256": pair["v0"]["model_sha256"],
                "m1_model_path": pair["M1"]["model_path"],
                "m1_model_sha256": pair["M1"]["model_sha256"],
                "objective_identity_preverified": audit["objective_identical"],
                "variable_domain_identity_preverified": audit["variable_names_types_bounds_identical"],
                "v0_plain_lp_status": pair["v0"]["status"],
                "m1_plain_lp_status": pair["M1"]["status"],
                "v0_plain_lp_optimum": format(v0, ".17g"),
                "m1_plain_lp_optimum": format(m1, ".17g"),
                "m1_minus_v0": format(m1 - v0, ".17g"),
                "certificate_tolerance": CERT_EPS,
                "monotonicity_requirement": "LP_M1 >= LP_v0 - epsilon_cert",
                "monotonicity_pass": passed,
                "v0_original_integer_variables": pair["v0"]["original_integer_variables"],
                "v0_original_binary_variables": pair["v0"]["original_binary_variables"],
                "m1_original_integer_variables": pair["M1"]["original_integer_variables"],
                "m1_original_binary_variables": pair["M1"]["original_binary_variables"],
                "v0_relaxed_variables": pair["v0"]["relaxed_variable_count"],
                "m1_relaxed_variables": pair["M1"]["relaxed_variable_count"],
                "v0_rows": pair["v0"]["rows"],
                "m1_rows": pair["M1"]["rows"],
                "v0_nonzeros": pair["v0"]["nonzeros"],
                "m1_nonzeros": pair["M1"]["nonzeros"],
                "v0_solver_work": pair["v0"]["solver_work"],
                "m1_solver_work": pair["M1"]["solver_work"],
                "v0_solver_runtime_seconds": pair["v0"]["solver_runtime_seconds"],
                "m1_solver_runtime_seconds": pair["M1"]["solver_runtime_seconds"],
                "v0_simplex_iterations": pair["v0"]["simplex_iterations"],
                "m1_simplex_iterations": pair["M1"]["simplex_iterations"],
                "Presolve": "Auto",
                "Seed": 0,
                "Threads": 1,
                "Method": "Auto",
            })
    finally:
        solver.close()
    process_seconds = time.monotonic() - start
    if process_seconds > PROCESS_CAP_SECONDS:
        raise TimeoutError(f"plain-LP process exceeded cap: {process_seconds}")
    if not all(bool(row["monotonicity_pass"]) for row in output_rows):
        failures = [row["state_id"] for row in output_rows
                    if not row["monotonicity_pass"]]
        raise RuntimeError(f"plain-LP monotonicity failure: {failures}")
    with (OUT / "plain_lp_monotonicity_audit.csv").open(
            "w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(output_rows[0].keys()))
        writer.writeheader()
        writer.writerows(output_rows)

    (OUT / "root_telemetry_semantics.md").write_text(
        """# Root and LP telemetry semantics

The following quantities are distinct and must not be relabeled as each other:

- `plain_continuous_lp_optimum`: optimum after every integer/semi-integer
  variable in the canonical model is changed to continuous, solved as an LP.
- `initial_mip_root_relaxation_bound`: the first valid root-relaxation bound
  observed by the MIP engine before its root cutting loop is complete.
- `post_presolve_root_cut_bound`: the final valid root bound after presolve and
  the root cutting loop, before branching when such an event is available.
- `first_branching_bound`: the first valid best bound after the tree has opened
  beyond the root.
- `mip_best_bound`: general monotone MIP best-bound telemetry at an identified
  event/checkpoint; it is not assumed to be a plain-LP optimum.

Round 51 `root_relaxation_bound` is migrated to
`initial_mip_root_relaxation_bound`; `final_root_cut_bound` is migrated to
`post_presolve_root_cut_bound`. Neither is used as the new plain-LP value. The
paired audit reconstructs the exact hashed Round 51 canonical v0/M1 models,
relaxes all integer variables through the Gurobi model API, and solves with
identical Presolve=Auto, Seed=0, Threads=1, and Method=Auto settings.
""", encoding="utf-8")
    migration = {
        "schema": "round52-telemetry-field-migration-v1",
        "new_fields": {
            "plain_continuous_lp_optimum": "new independent LP solve",
            "initial_mip_root_relaxation_bound": "formerly root_relaxation_bound",
            "post_presolve_root_cut_bound": "formerly final_root_cut_bound",
            "first_branching_bound": "new explicitly event-scoped field",
            "mip_best_bound": "general event/checkpoint best-bound field"},
        "forbidden_aliases": [
            ["plain_continuous_lp_optimum", "initial_mip_root_relaxation_bound"],
            ["plain_continuous_lp_optimum", "post_presolve_root_cut_bound"],
            ["initial_mip_root_relaxation_bound", "post_presolve_root_cut_bound"],
            ["first_branching_bound", "mip_best_bound_without_event"]],
        "historical_raw_files_rewritten": False,
        "affected_state_count": len(output_rows),
        "all_plain_lp_monotonicity_rows_passed": True,
        "audit_process_seconds": process_seconds,
        "audit_process_cap_seconds": PROCESS_CAP_SECONDS,
        "gurobi_library": str(DLL),
        "gurobi_version": "13.0.2rc1",
    }
    (OUT / "telemetry_field_migration.json").write_text(
        json.dumps(migration, indent=2) + "\n", encoding="utf-8")
    print(f"plain-LP audit passed for {len(output_rows)} affected states in {process_seconds:.3f}s")


if __name__ == "__main__":
    main()
