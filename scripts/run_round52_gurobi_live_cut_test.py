#!/usr/bin/env python3
"""Force and audit one real GRBcbcut call on a tiny valid MIP."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import platform
import time
from pathlib import Path


GRB_CB_MIPNODE = 5
GRB_CB_MIPNODE_STATUS = 5001
GRB_CB_MIPNODE_REL = 5002
GRB_OPTIMAL = 2


def bind(dll: ctypes.WinDLL, name: str, restype, argtypes):
    fn = getattr(dll, name)
    fn.restype = restype
    fn.argtypes = argtypes
    return fn


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gurobi-home", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    started = time.monotonic()
    home = Path(args.gurobi_home).resolve()
    dll_path = home / "bin" / "gurobi130.dll"
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    dll = ctypes.WinDLL(str(dll_path))

    void_p = ctypes.c_void_p
    int_p = ctypes.POINTER(ctypes.c_int)
    dbl_p = ctypes.POINTER(ctypes.c_double)
    char_p = ctypes.POINTER(ctypes.c_char)
    cstr = ctypes.c_char_p
    emptyenv = bind(dll, "GRBemptyenv", ctypes.c_int,
                    [ctypes.POINTER(void_p), cstr])
    startenv = bind(dll, "GRBstartenv", ctypes.c_int, [void_p])
    newmodel = bind(
        dll, "GRBnewmodel", ctypes.c_int,
        [void_p, ctypes.POINTER(void_p), cstr, ctypes.c_int, dbl_p, dbl_p,
         dbl_p, char_p, ctypes.POINTER(cstr)])
    addconstr = bind(
        dll, "GRBaddconstr", ctypes.c_int,
        [void_p, ctypes.c_int, int_p, dbl_p, ctypes.c_char,
         ctypes.c_double, cstr])
    updatemodel = bind(dll, "GRBupdatemodel", ctypes.c_int, [void_p])
    getenv = bind(dll, "GRBgetenv", void_p, [void_p])
    setintparam = bind(dll, "GRBsetintparam", ctypes.c_int,
                       [void_p, cstr, ctypes.c_int])
    setdblparam = bind(dll, "GRBsetdblparam", ctypes.c_int,
                       [void_p, cstr, ctypes.c_double])
    getintparam = bind(dll, "GRBgetintparam", ctypes.c_int,
                       [void_p, cstr, int_p])
    setintattr = bind(dll, "GRBsetintattr", ctypes.c_int,
                      [void_p, cstr, ctypes.c_int])
    cbget = bind(dll, "GRBcbget", ctypes.c_int,
                 [void_p, ctypes.c_int, ctypes.c_int, void_p])
    cbcut = bind(dll, "GRBcbcut", ctypes.c_int,
                 [void_p, ctypes.c_int, int_p, dbl_p, ctypes.c_char,
                  ctypes.c_double])
    callback_type = ctypes.WINFUNCTYPE(
        ctypes.c_int, void_p, void_p, ctypes.c_int, void_p)
    setcallback = bind(dll, "GRBsetcallbackfunc", ctypes.c_int,
                       [void_p, callback_type, void_p])
    optimize = bind(dll, "GRBoptimize", ctypes.c_int, [void_p])
    getintattr = bind(dll, "GRBgetintattr", ctypes.c_int,
                      [void_p, cstr, int_p])
    getdblattr = bind(dll, "GRBgetdblattr", ctypes.c_int,
                      [void_p, cstr, dbl_p])
    freemodel = bind(dll, "GRBfreemodel", None, [void_p])
    freeenv = bind(dll, "GRBfreeenv", None, [void_p])

    env = void_p()
    model = void_p()
    calls = 0
    optimal_node_calls = 0
    submissions = 0
    successes = 0
    last_cbcut_rc = -1
    maximum_observed_relaxation_sum = 0.0
    failure = "none"
    function_return_codes: dict[str, int] = {}

    def checked(label: str, rc: int) -> None:
        function_return_codes[label] = int(rc)
        if rc:
            raise RuntimeError(f"{label}_return_code:{rc}")

    @callback_type
    def callback(_model, cbdata, where, _usrdata):
        nonlocal calls, optimal_node_calls, submissions, successes
        nonlocal last_cbcut_rc, maximum_observed_relaxation_sum
        if where != GRB_CB_MIPNODE:
            return 0
        calls += 1
        status = ctypes.c_int()
        if cbget(cbdata, where, GRB_CB_MIPNODE_STATUS,
                 ctypes.byref(status)) or status.value != GRB_OPTIMAL:
            return 0
        optimal_node_calls += 1
        values = (ctypes.c_double * 2)()
        if cbget(cbdata, where, GRB_CB_MIPNODE_REL, values):
            return 0
        relaxation_sum = values[0] + values[1]
        maximum_observed_relaxation_sum = max(
            maximum_observed_relaxation_sum, relaxation_sum)
        if successes == 0 and relaxation_sum > 1.0 + 1e-9:
            indices = (ctypes.c_int * 2)(0, 1)
            coefficients = (ctypes.c_double * 2)(1.0, 1.0)
            submissions += 1
            last_cbcut_rc = int(cbcut(
                cbdata, 2, indices, coefficients, b"<", 1.0))
            if last_cbcut_rc == 0:
                successes += 1
        return 0

    try:
        checked("GRBemptyenv", emptyenv(ctypes.byref(env), None))
        checked("GRBstartenv", startenv(env))
        objective = (ctypes.c_double * 2)(1.0, 1.0)
        lower = (ctypes.c_double * 2)(0.0, 0.0)
        upper = (ctypes.c_double * 2)(1.0, 1.0)
        vtype = (ctypes.c_char * 2)(b"B", b"B")
        names = (ctypes.c_char_p * 2)(b"x", b"y")
        checked("GRBnewmodel", newmodel(
            env, ctypes.byref(model), b"round52_live_cbcut", 2,
            objective, lower, upper, vtype, names))
        model_env = getenv(model)
        checked("ModelSense", setintattr(model, b"ModelSense", -1))
        indices = (ctypes.c_int * 2)(0, 1)
        coefficients = (ctypes.c_double * 2)(1.0, 1.0)
        checked("GRBaddconstr", addconstr(
            model, 2, indices, coefficients, b"<", 1.5,
            b"fractional_knapsack"))
        checked("GRBupdatemodel", updatemodel(model))
        for name, value in ((b"OutputFlag", 0), (b"Threads", 1),
                            (b"Seed", 0), (b"Presolve", 0),
                            (b"Cuts", 0), (b"PreCrush", 1)):
            checked(name.decode(), setintparam(model_env, name, value))
        checked("Heuristics", setdblparam(model_env, b"Heuristics", 0.0))
        precrush = ctypes.c_int(-1)
        checked("PreCrushReadback", getintparam(
            model_env, b"PreCrush", ctypes.byref(precrush)))
        checked("GRBsetcallbackfunc", setcallback(model, callback, None))
        checked("GRBoptimize", optimize(model))
        status = ctypes.c_int()
        objective_value = ctypes.c_double()
        checked("Status", getintattr(model, b"Status", ctypes.byref(status)))
        checked("ObjVal", getdblattr(
            model, b"ObjVal", ctypes.byref(objective_value)))
        passed = (precrush.value == 1 and status.value == GRB_OPTIMAL and
                  optimal_node_calls > 0 and submissions > 0 and
                  successes > 0 and last_cbcut_rc == 0 and
                  maximum_observed_relaxation_sum > 1.0 + 1e-9 and
                  abs(objective_value.value - 1.0) <= 1e-9)
    except Exception as error:  # evidence is written even on failure
        passed = False
        precrush = locals().get("precrush", ctypes.c_int(-1))
        status = locals().get("status", ctypes.c_int(-1))
        objective_value = locals().get(
            "objective_value", ctypes.c_double(float("nan")))
        failure = str(error)
    finally:
        if model:
            freemodel(model)
        if env:
            freeenv(env)

    dll_sha = hashlib.sha256(dll_path.read_bytes()).hexdigest()
    record = {
        "schema": "round52-gurobi-live-cbcut-test-v1",
        "passed": passed,
        "failure_reason": failure,
        "fixture": "maximize x+y; x+y<=1.5; x,y binary",
        "globally_valid_user_cut": "x+y<=1",
        "precrush_requested": 1,
        "precrush_effective": precrush.value,
        "mipnode_callback_calls": calls,
        "optimal_mipnode_callback_calls": optimal_node_calls,
        "maximum_observed_relaxation_sum": maximum_observed_relaxation_sum,
        "grbcbcut_submissions": submissions,
        "grbcbcut_successes": successes,
        "last_grbcbcut_return_code": last_cbcut_rc,
        "native_status": status.value,
        "native_objective": objective_value.value,
        "process_seconds": time.monotonic() - started,
        "gurobi_dll": str(dll_path).replace(os.sep, "/"),
        "gurobi_dll_sha256": dll_sha,
        "python": platform.python_version(),
        "function_return_codes": function_return_codes,
    }
    output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
