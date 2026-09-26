"""One-shot, evidence-preserving qualification for the admitted OT epigraph.

This helper is not a production runner and cannot Optimize an original LP.
Only the isolated B1/B2 toy stages below call Optimize, once each.
"""

from __future__ import annotations

import argparse
import ctypes
from fractions import Fraction as F
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

from round88_ot_closure import (ROOT, SOURCES, _WindowsJob, _kill_tree,
                                _wait_with_deadline, frozen_source, save, sha)
from round88_ot_epigraph import (ARMS, add_plan, make_plan, primal_residuals,
                                 save_exact_plan)
from round88_ot_math import h_name, q_name, ratio, state_name

SCRIPT = Path(__file__).resolve()
EPIGRAPH = ROOT / "scripts/round88_ot_epigraph.py"
TEST = ROOT / "tests/round88_ot_epigraph_test.py"
FROZEN_SCRIPT_SHA = "5d49c3fc12cc806a8008e43d756bf9c46810b21e7efc2b64c2383da4624bd7da"
FROZEN_TEST_SHA = "2be3e3e51333e29fcfa3b52c17f90ce4603603dd2032979191fb96a1624913ab"


def receipt(out: Path, name: str, command: list[str]) -> dict[str, Any]:
    started = time.perf_counter()
    attempted = {"stage": name, "command": command, "started_perf_counter": started,
                 "helper_sha256": sha(SCRIPT), "epigraph_sha256": sha(EPIGRAPH),
                 "tests_sha256": sha(TEST)}
    save(out / f"{name}_attempt.json", attempted)
    try:
        run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
        code, stdout, stderr = run.returncode, run.stdout, run.stderr
    except Exception as exc:
        code, stdout, stderr = 125, "", "launch_exception=" + repr(exc)
    elapsed = time.perf_counter()-started
    (out / f"{name}_stdout.txt").write_text(stdout, encoding="utf-8")
    (out / f"{name}_stderr.txt").write_text(stderr, encoding="utf-8")
    record = {"stage": name, "command": command, "returncode": code,
              "external_launch_to_exit_wall_seconds": elapsed,
              "stdout_sha256": sha(out / f"{name}_stdout.txt"),
              "stderr_sha256": sha(out / f"{name}_stderr.txt"),
              "scope": "Full stage command outside wall; nested stage timings are not additive"}
    save(out / f"{name}_receipt.json", record)
    return record


def run_all(out: Path) -> int:
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    identity = {"schema": "round88-ot-epigraph-qualification-v1",
                "helper_sha256": sha(SCRIPT), "epigraph_sha256": sha(EPIGRAPH),
                "tests_sha256": sha(TEST), "python": sys.executable,
                "stages": ["micro", "toy", "job", "audit", "prepare"],
                "real_source_optimize_calls_allowed": 0, "toy_optimize_calls_allowed": 2}
    save(out / "qualification_identity.json", identity)
    if identity["epigraph_sha256"] != FROZEN_SCRIPT_SHA or (
            identity["tests_sha256"] != FROZEN_TEST_SHA):
        save(out / "qualification_failure.json", {"reason": "frozen source/test SHA drift"})
        return 125
    stages = [
        ("micro", [sys.executable, str(TEST)]),
        ("toy", [sys.executable, str(SCRIPT), "toy", "--out-dir", str(out / "toy")]),
        ("job", [sys.executable, str(SCRIPT), "job", "--out-dir", str(out / "job")]),
        ("audit", [sys.executable, str(SCRIPT), "audit", "--out-dir", str(out / "source_audit")]),
        ("prepare", [sys.executable, str(EPIGRAPH), "prepare-supervise", "--out-dir",
                     str(out / "preparation")]),
    ]
    records: list[dict[str, Any]] = []
    for name, command in stages:
        record = receipt(out, name, command)
        records.append(record)
        summary = {"schema": "round88-ot-epigraph-qualification-summary-v1",
                   "stages": records, "completed_stages": len(records),
                   "sum_external_stage_command_wall_seconds": sum(
                       entry["external_launch_to_exit_wall_seconds"] for entry in records),
                   "outer_qualifier_elapsed_seconds_so_far": time.perf_counter()-started,
                   "status": "running" if record["returncode"] == 0 else "stopped_on_failure",
                   "real_source_optimize_calls": 0,
                   "toy_optimize_calls": 2 if name in ("toy", "job", "audit", "prepare")
                       and record["returncode"] == 0 else None}
        save(out / "qualification_summary.json", summary)
        if record["returncode"] != 0:
            return 125
    summary["status"] = "qualification_stages_completed_pending_independent_review"
    summary["outer_qualifier_wall_seconds"] = time.perf_counter()-started
    save(out / "qualification_summary.json", summary)
    return 0


def toy(out: Path) -> None:
    import gurobipy as gp
    from gurobipy import GRB
    from round88_ot_diagnostic import configure, process_peak_memory_bytes

    out.mkdir(parents=True, exist_ok=False)
    supports = {1: (0, 1), 2: (0, 1)}
    targets = {1: 1, 2: 1}
    fixed_s = {(i, y): 0.5 for i in supports for y in supports[i]}
    fixed_q = {(1, 0): 0.0, (1, 1): 0.5, (2, 0): 0.5, (2, 1): 0.0}
    independent = {"s_each": "1/2", "G": "1/2", "q_1": ["0", "1/2"],
                   "q_2": ["1/2", "0"], "threshold": "0", "delta": "1",
                   "direct_A": "0", "direct_B": "-1/2",
                   "direct_B1_min_h": "0", "direct_B2_min_h": "1"}
    save(out / "independent_hand_oracle.json", independent)
    completed = 0
    for arm in ARMS:
        arm_dir = out / arm
        arm_dir.mkdir()
        save(arm_dir / "inflight.json", {"phase": "original_toy_model", "toy_optimize_calls_before": completed})
        model = gp.Model(f"round88_epigraph_{arm}_toy")
        variables = {}
        for (i, y), value in fixed_s.items():
            variables[state_name(i, y)] = model.addVar(lb=value, ub=value, vtype=GRB.CONTINUOUS,
                                                        name=state_name(i, y))
        for (i, y), value in fixed_q.items():
            variables[q_name(i, y)] = model.addVar(lb=value, ub=value, vtype=GRB.CONTINUOUS,
                                                    name=q_name(i, y))
        variables["G"] = model.addVar(lb=0.5, ub=0.5, vtype=GRB.CONTINUOUS, name="G")
        variables[h_name(1, 2)] = model.addVar(lb=0.0, ub=2.0, obj=1.0,
                                               vtype=GRB.CONTINUOUS, name=h_name(1, 2))
        for i in supports:
            model.addConstr(gp.quicksum(variables[state_name(i, y)] for y in supports[i]) == 1,
                            name=f"onehot_{i}")
            model.addConstr(gp.quicksum(variables[q_name(i, y)] for y in supports[i]) ==
                            variables["G"], name=f"qsum_{i}")
            for y in supports[i]:
                model.addConstr(variables[q_name(i, y)] <= variables[state_name(i, y)],
                                name=f"perspective_upper_{i}_{y}")
        model.ModelSense = GRB.MINIMIZE
        model.update()
        original = {"variables": model.NumVars, "rows": model.NumConstrs,
                    "nonzeros": model.NumNZs}
        model.write(str(arm_dir / "original.lp"))
        plan = make_plan(arm, supports, targets, F(0), F(1))
        plan_files = save_exact_plan(plan, arm_dir)
        actual = add_plan(model, plan)
        model.write(str(arm_dir / "augmented.lp"))
        configure(model, arm_dir / "optimizer.log")
        save(arm_dir / "inflight.json", {"phase": "toy_optimize", "toy_optimize_calls_before": completed,
                                         "predicted": plan.counts, "actual": actual})
        started = time.perf_counter()
        model.optimize()
        completed += 1
        optimize_seconds = time.perf_counter()-started
        result = {"arm": arm, "status_code": model.Status, "optimize_calls_this_arm": 1,
                  "optimize_calls_total_so_far": completed, "optimize_wall_seconds": optimize_seconds,
                  "solver_runtime_seconds": model.Runtime, "solver_work": model.Work,
                  "original": original, "predicted": plan.counts, "actual": actual,
                  "exact_plan_files": plan_files, "gurobi_version": gp.gurobi.version(),
                  "peak_working_set_bytes": process_peak_memory_bytes(),
                  "independent_expected_objective": 0.0 if arm == "B1" else 1.0}
        save(arm_dir / "optimizer_status.json", result)
        if model.Status != GRB.OPTIMAL:
            raise RuntimeError(f"toy {arm} nonoptimal status {model.Status}")
        result["objective"] = model.ObjVal
        result["residuals"] = primal_residuals(model, arm_dir, original["rows"])
        if abs(model.ObjVal-result["independent_expected_objective"]) > 1e-8 or (
                max(result["residuals"].values()) > 1e-6):
            save(arm_dir / "result.json", result)
            raise RuntimeError(f"toy {arm} projection or residual mismatch")
        result["status"] = "optimal_matches_independent_hand_oracle"
        save(arm_dir / "result.json", result)
    save(out / "toy_summary.json", {"schema": "round88-epigraph-two-toy-optimize-v1",
                                    "toy_optimize_calls": completed,
                                    "real_source_optimize_calls": 0,
                                    "B1_expected_and_actual": 0.0,
                                    "B2_expected_and_actual": 1.0})


def _process_alive(pid: int) -> bool:
    if os.name != "nt":
        raise RuntimeError("Windows Job qualification requires Windows")
    api = ctypes.windll.kernel32
    api.OpenProcess.argtypes = (ctypes.c_uint, ctypes.c_int, ctypes.c_uint)
    api.OpenProcess.restype = ctypes.c_void_p
    api.GetExitCodeProcess.argtypes = (ctypes.c_void_p, ctypes.c_void_p)
    api.CloseHandle.argtypes = (ctypes.c_void_p,)
    handle = api.OpenProcess(0x1000, 0, pid)
    if not handle:
        return False
    code = ctypes.c_ulong()
    try:
        if not api.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise RuntimeError("GetExitCodeProcess failed")
        return code.value == 259
    finally:
        api.CloseHandle(handle)


def job(out: Path) -> None:
    if os.name != "nt":
        raise RuntimeError("Windows child-tree qualification requires Windows")
    out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    pid_file, ready = out / "grandchild.pid", out / "ready.flag"
    program = """
import pathlib, subprocess, sys, time
ready = pathlib.Path(sys.argv[2]); until = time.monotonic()+5
while not ready.is_file() and time.monotonic()<until: time.sleep(0.01)
if not ready.is_file(): raise RuntimeError('job handshake missing')
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
pathlib.Path(sys.argv[1]).write_text(str(child.pid))
time.sleep(60)
"""
    assigned_job = _WindowsJob()
    child: subprocess.Popen[str] | None = None
    descendant: int | None = None
    result = {"schema": "round88-ot-epigraph-job-qualification-v1",
              "no_solver_or_model": True, "deadline_seconds": 0.2,
              "helper_sha256": sha(SCRIPT)}
    try:
        child = subprocess.Popen([sys.executable, "-c", program, str(pid_file), str(ready)],
                                 cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        result["child_pid"] = child.pid
        assigned_job.assign(child)
        ready.write_text("assigned\n", encoding="ascii")
        until = time.monotonic()+5
        while not pid_file.is_file() and time.monotonic()<until:
            time.sleep(0.02)
        if not pid_file.is_file():
            raise RuntimeError("grandchild never started")
        descendant = int(pid_file.read_text(encoding="ascii"))
        result["grandchild_pid"] = descendant
        stdout, stderr, timed_out = _wait_with_deadline(child, assigned_job, 0.2)
        (out / "child_stdout.txt").write_text(stdout, encoding="utf-8")
        (out / "child_stderr.txt").write_text(stderr, encoding="utf-8")
        result["timed_out"] = timed_out
        result["child_returncode"] = child.returncode
        result["child_alive_after"] = _process_alive(child.pid)
        result["grandchild_alive_after"] = _process_alive(descendant)
        result["external_job_stage_wall_seconds"] = time.perf_counter()-started
        result["status"] = ("timeout_tree_clean" if timed_out and
                            not result["child_alive_after"] and
                            not result["grandchild_alive_after"] else "cleanup_failure")
        save(out / "job_result.json", result)
        if result["status"] != "timeout_tree_clean":
            raise RuntimeError("Win32 Job failed to terminate process tree")
    finally:
        assigned_job.close()
        if child and child.poll() is None:
            _kill_tree(child, assigned_job)
        if descendant and _process_alive(descendant):
            subprocess.run(["taskkill", "/PID", str(descendant), "/T", "/F"],
                           capture_output=True, check=False)


def audit(out: Path) -> None:
    from round88_ot_diagnostic import audit_model, load_model, read_instance
    import gurobipy as gp

    out.mkdir(parents=True, exist_ok=False)
    entries = []
    for label in SOURCES:
        started = time.perf_counter()
        qualified, manifest_path = frozen_source(label)
        instance = read_instance(Path(qualified["input"]))
        model = load_model(Path(qualified["lp"]))
        actual = audit_model(model, instance, F(qualified["gamma_l"]),
                             F(qualified["gamma_u"]), qualified["verified_ub"],
                             qualified["lambda"])
        a, b = F(actual["effective_gamma_l"]), F(actual["effective_gamma_u"])
        supports = {int(i): ys for i, ys in actual["support"].items()}
        N = sum(len(ys)-1 for ys in supports.values())
        P = K = 0
        for i, j in itertools.combinations(sorted(supports), 2):
            p = len({ratio(y, instance["targets"][station])
                     for station in (i, j) for y in supports[station]})-1
            P += p
            K += int(p > 0)
        predicted = {"N": N, "P": P, "K": K,
                     "B1_columns": N+P, "B1_rows": N+2*P+K,
                     "B1_nz_upper": 3*N+7*P+K,
                     "B2_columns": 2*N+2*P, "B2_rows": 2*N+4*P+K,
                     "B2_nz_upper": 6*N+26*P+K}
        entry = {"source": label, "qualification_manifest_sha256": sha(manifest_path),
                 "lp_sha256": qualified["lp_sha256"],
                 "input_sha256": qualified["input_sha256"],
                 "source_sha256": qualified["source_sha256"],
                 "structure_equal": actual == qualified["structure"],
                 "support_fingerprint": actual["support_fingerprint"],
                 "effective_gamma_l": str(a), "effective_gamma_u": str(b),
                 "original_variables": model.NumVars, "original_rows": model.NumConstrs,
                 "original_nonzeros": model.NumNZs,
                 "predicted_epigraph_sparse_sizes": predicted,
                 "gurobi_version": gp.gurobi.version(),
                 "zero_optimize_calls": True,
                 "external_source_audit_wall_seconds": time.perf_counter()-started}
        save(out / f"{label}_audit.json", entry)
        entries.append(entry)
        if not entry["structure_equal"]:
            raise ValueError(f"qualified original LP changed for {label}")
    save(out / "source_comparison.json", {
        "schema": "round88-ot-epigraph-zero-optimize-sources-v1", "entries": entries,
        "all_structure_equal": True, "real_source_optimize_calls": 0})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    for name in ("run-all", "toy", "job", "audit"):
        sub = commands.add_parser(name)
        sub.add_argument("--out-dir", required=True, type=Path)
    args = parser.parse_args()
    if args.mode == "run-all":
        return run_all(args.out_dir)
    if args.mode == "toy":
        toy(args.out_dir)
    elif args.mode == "job":
        job(args.out_dir)
    else:
        audit(args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
