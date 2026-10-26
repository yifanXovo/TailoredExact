"""One-shot supervised G2 diagnosis on the three frozen Round88 A2 witnesses.

`validate` is read-only and never launches native code. `run` requires a later
G1 qualification gate binding the built driver and source hashes. This script
does not build, run ENS-C, or inject a historical witness into a formal arm.
"""

from __future__ import annotations

import argparse
import ast
import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "results/unified_exact_round93/coquantity_diagnostic_preregistration.json"
EXPECTED_SCHEMA = "round93-coquantity-fixed-witness-diagnostic-preregistration-v1"
GATE_SCHEMA = "round93-coquantity-g1-qualified-driver-v1"
ORDER = ("D6", "E8", "S12")
CASE_SECONDS = 120.0
TOTAL_SECONDS = 360.0


class GateError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checked_path(relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise GateError("path must be nonempty and repository-relative")
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise GateError("path escapes repository: " + relative)
    return path


def require_hash(path: Path, expected: str, name: str) -> str:
    if not path.is_file() or not isinstance(expected, str) or len(expected) != 64:
        raise GateError(name + " missing or unbound")
    actual = sha256(path)
    if actual != expected.lower():
        raise GateError(name + " SHA256 mismatch: " + str(path))
    return actual


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise GateError("JSON root is not an object: " + str(path))
    return value


def preregistration() -> dict[str, Any]:
    plan = read_json(PREREG)
    execution = plan.get("execution", {})
    cases = plan.get("cases", [])
    if (plan.get("schema") != EXPECTED_SCHEMA or
            execution.get("case_order") != list(ORDER) or
            execution.get("planned_cases") != 3 or
            execution.get("repetitions_per_case") != 1 or
            execution.get("whole_case_external_deadline_seconds") != 120 or
            execution.get("maximum_sum_case_deadlines_seconds") != 360 or
            not isinstance(cases, list) or [c.get("id") for c in cases] != list(ORDER)):
        raise GateError("preregistration scope differs from frozen D6/E8/S12 contract")
    return plan


def check_cases(plan: dict[str, Any]) -> list[dict[str, Any]]:
    prepared = []
    for case in plan["cases"]:
        scenario = case.get("scenario", {})
        if (scenario.get("pickup_seconds") != 60 or scenario.get("drop_seconds") != 60 or
                scenario.get("lambda") != 0.15 or
                not isinstance(scenario.get("T_seconds"), int) or
                scenario["T_seconds"] <= 0):
            raise GateError("scenario mismatch: " + str(case.get("id")))
        source = checked_path(case["input_path"])
        witness = checked_path(case["witness_path"])
        source_hash = require_hash(source, case["input_sha256"], "input")
        witness_hash = require_hash(witness, case["witness_sha256"], "witness")
        # Parse the small witness enough to reject a misplaced or malformed
        # artifact. The qualified C++ driver remains the original evaluator.
        witness_json = read_json(witness)
        routes = witness_json.get("routes")
        if not isinstance(routes, list) or len(routes) != scenario["M"]:
            raise GateError("witness route count mismatch: " + case["id"])
        vehicles = []
        for route in routes:
            if not isinstance(route, dict) or not isinstance(route.get("nodes"), list):
                raise GateError("malformed witness route: " + case["id"])
            vehicles.append(route.get("vehicle"))
            if not isinstance(route.get("operations"), list):
                raise GateError("malformed witness operations: " + case["id"])
        if sorted(vehicles) != list(range(scenario["M"])):
            raise GateError("witness vehicle identity mismatch: " + case["id"])
        prepared.append(dict(case=case, source=source, witness=witness,
                             input_sha256=source_hash, witness_sha256=witness_hash))
    return prepared


def qualified_gate(path: Path) -> dict[str, Any]:
    gate = read_json(path)
    if (gate.get("schema") != GATE_SCHEMA or gate.get("status") != "qualified" or
            gate.get("preregistration_sha256") != sha256(PREREG)):
        raise GateError("missing/mismatched independently qualified G1 gate")
    binary = gate.get("driver_binary", {})
    if not isinstance(binary, dict):
        raise GateError("G1 driver binary not bound")
    executable = checked_path(binary.get("path"))
    require_hash(executable, binary.get("sha256"), "G1 driver binary")
    required_source = {
        "src/Round93CoQuantityDescent.cpp",
        "include/Round93CoQuantityDescent.hpp",
        "tests/round93_co_quantity_diagnostic.cpp",
        "scripts/round93_coquantity_diagnostic.py",
    }
    pins = gate.get("source_sha256")
    if not isinstance(pins, dict) or not required_source.issubset(pins):
        raise GateError("G1 source set incomplete")
    for relative, expected in pins.items():
        require_hash(checked_path(relative), expected, "G1 source")
    return dict(gate=gate, gate_path=path, gate_sha256=sha256(path),
                executable=executable, binary_sha256=binary["sha256"].lower(),
                source_sha256={k: v.lower() for k, v in pins.items()})


class WindowsJob:
    """Kill all assigned native descendants when the job closes."""

    def __init__(self) -> None:
        class BasicLimit(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                        ("PerJobUserTimeLimit", ctypes.c_int64),
                        ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t),
                        ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t),
                        ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class IoCounters(ctypes.Structure):
            _fields_ = [(name, ctypes.c_uint64) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class ExtendedLimit(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BasicLimit),
                        ("IoInfo", IoCounters),
                        ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        self.api = ctypes.windll.kernel32
        self.api.CreateJobObjectW.argtypes = (ctypes.c_void_p, ctypes.c_wchar_p)
        self.api.CreateJobObjectW.restype = ctypes.c_void_p
        self.api.SetInformationJobObject.argtypes = (
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint)
        self.api.SetInformationJobObject.restype = wintypes.BOOL
        self.api.AssignProcessToJobObject.argtypes = (ctypes.c_void_p, ctypes.c_void_p)
        self.api.AssignProcessToJobObject.restype = wintypes.BOOL
        self.api.CloseHandle.argtypes = (ctypes.c_void_p,)
        self.api.CloseHandle.restype = wintypes.BOOL
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise GateError("Windows job creation failed")
        info = ExtendedLimit()
        info.BasicLimitInformation.LimitFlags = 0x00002000
        if not self.api.SetInformationJobObject(
                self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            self.close()
            raise GateError("Windows kill-on-close job setup failed")

    def assign(self, process: subprocess.Popen[Any]) -> None:
        if not self.api.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise GateError("Windows job assignment failed")

    def close(self) -> None:
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def kill_tree(process: subprocess.Popen[Any], job: WindowsJob | None) -> None:
    if job is not None:
        job.close()
    if os.name != "nt":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       check=False)
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], bool]:
    if not path.is_file():
        return [], False
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                item = json.loads(line)
                if not isinstance(item, dict):
                    return rows, False
                rows.append(item)
    except (OSError, ValueError):
        return rows, False
    return rows, True


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def normalize_routes(routes: Any, vehicles: int) -> list[dict[str, Any]]:
    if not isinstance(routes, list) or len(routes) != vehicles:
        raise GateError("route count mismatch")
    normalized = []
    for route in routes:
        if not isinstance(route, dict):
            raise GateError("route is not an object")
        vehicle, nodes, operations = (route.get(k) for k in ("vehicle", "nodes", "operations"))
        if (not isinstance(vehicle, int) or not isinstance(nodes, list) or
                not isinstance(operations, list) or len(nodes) != len(operations) + 2):
            raise GateError("route structure invalid")
        if nodes[0] != 0 or nodes[-1] != 0:
            raise GateError("route depot endpoints invalid")
        ops = []
        for op in operations:
            if isinstance(op, dict):
                triple = [op.get("station"), op.get("pickup"), op.get("drop")]
            else:
                triple = op
            if (not isinstance(triple, list) or len(triple) != 3 or
                    not all(isinstance(x, int) and not isinstance(x, bool) for x in triple)):
                raise GateError("route operation invalid")
            ops.append(triple)
        if nodes[1:-1] != [o[0] for o in ops]:
            raise GateError("route station/operation mismatch")
        normalized.append(dict(vehicle=vehicle, nodes=list(nodes), operations=ops))
    if sorted(r["vehicle"] for r in normalized) != list(range(vehicles)):
        raise GateError("route vehicle identity invalid")
    return sorted(normalized, key=lambda r: r["vehicle"])


def inventory_vectors(input_path: Path, vertices: int) -> tuple[list[int], list[int]]:
    source = input_path.read_text(encoding="utf-8")
    vectors = []
    for name in ("initial", "capacities"):
        match = re.search(r"(?m)^\s*" + name + r"\s*=\s*(\[[^\n]*\])", source)
        if match is None:
            raise GateError("missing input inventory vector: " + name)
        vector = ast.literal_eval(match.group(1))
        if (not isinstance(vector, list) or len(vector) != vertices + 1 or
                not all(isinstance(x, int) and not isinstance(x, bool) for x in vector)):
            raise GateError("invalid input inventory vector: " + name)
        vectors.append(vector)
    return vectors[0], vectors[1]


def apply_change(routes: list[dict[str, Any]], a: int, b: int, delta: int) -> None:
    seen = []
    for route in routes:
        next_ops = []
        for station, pickup, drop in route["operations"]:
            if station in (a, b):
                seen.append(station)
                signed = pickup - drop - delta
                pickup, drop = max(signed, 0), max(-signed, 0)
            if pickup or drop:
                next_ops.append([station, pickup, drop])
        route["operations"] = next_ops
        route["nodes"] = [0] + [op[0] for op in next_ops] + [0]
    if sorted(seen) != [a, b]:
        raise GateError("accepted stations absent or repeated")


def expected_point_tuples(routes: list[dict[str, Any]], initial: list[int],
                          capacities: list[int], pass_no: int) -> list[tuple[int, int, int, int, int, int]]:
    inventory = initial.copy()
    stations = []
    for route in routes:
        for station, pickup, drop in route["operations"]:
            if not 0 < station < len(initial) or station in stations:
                raise GateError("invalid served station in replay")
            stations.append(station)
            inventory[station] = initial[station] - pickup + drop
    stations.sort()
    expected = []
    for i, a in enumerate(stations):
        for b in stations[i + 1:]:
            lo = max(-inventory[a], -inventory[b])
            hi = min(capacities[a] - inventory[a], capacities[b] - inventory[b])
            for delta in range(lo, hi + 1):
                if delta:
                    expected.append((pass_no, a, b, delta,
                                     inventory[a] + delta, inventory[b] + delta))
    return expected


def replay_acceptances(witness: Path, choices: list[dict[str, Any]],
                       final: dict[str, Any], vehicles: int) -> bool:
    routes = normalize_routes(read_json(witness).get("routes"), vehicles)
    for choice in choices:
        a, b, delta = (choice.get(k) for k in ("a", "b", "t"))
        if not all(isinstance(x, int) and not isinstance(x, bool) for x in (a, b, delta)) or not 0 < a < b or delta == 0:
            return False
        apply_change(routes, a, b, delta)
    return routes == normalize_routes(final.get("routes"), vehicles)


def audit_native(directory: Path, case: dict[str, Any], returncode: int | None,
                 timed_out: bool) -> dict[str, Any]:
    points, points_ok = load_jsonl(directory / "native" / "points.jsonl")
    choices, choices_ok = load_jsonl(directory / "native" / "acceptances.jsonl")
    base = dict(point_rows=len(points), acceptance_rows=len(choices),
                point_ledger_parseable=points_ok,
                acceptance_ledger_parseable=choices_ok)
    if timed_out:
        return dict(base, status="unknown_whole_case_deadline",
                    reason="native receipts may have unflushed accepted work")
    if returncode != 0:
        return dict(base, status="unknown_native_no_complete_receipt",
                    reason="native process did not return zero")
    try:
        summary = read_json(directory / "native" / "summary.json")
        final = read_json(directory / "native" / "final_witness.json")
    except (OSError, ValueError, GateError):
        return dict(base, status="unknown_missing_or_malformed_receipt",
                    reason="summary or final witness absent/invalid")
    if not points_ok or not choices_ok:
        return dict(base, status="unknown_missing_or_malformed_receipt",
                    reason="point or acceptance ledger absent/invalid")
    scenario = case["scenario"]
    if (summary.get("input_sha256", "").lower() != case["input_sha256"] or
            summary.get("witness_sha256", "").lower() != case["witness_sha256"] or
            summary.get("V") != scenario["V"] or summary.get("M") != scenario["M"] or
            summary.get("T") != scenario["T_seconds"] or
            summary.get("pickup_time") != scenario["pickup_seconds"] or
            summary.get("drop_time") != scenario["drop_seconds"] or
            summary.get("lambda") != scenario["lambda"]):
        return dict(base, status="invalid_identity_or_scenario_receipt")
    if summary.get("verification_failed") is not False:
        return dict(base, status="invalid_native_verification_failed",
                    reason="driver reports an original Evaluator/acceptance failure")
    if summary.get("deadline") is True or not summary.get("exhausted"):
        return dict(base, status="unknown_native_incomplete",
                    reason="native did not attest complete exhausted descent")
    if (summary.get("integer_points") != len(points) or
            summary.get("accepted") != len(choices) or
            summary.get("feasible_points") != sum(p.get("feasible") is True for p in points)):
        return dict(base, status="invalid_ledger_counts")
    if not all(finite_number(summary.get(k)) for k in
               ("initial_F", "initial_G", "initial_P", "final_F", "final_G", "final_P")):
        return dict(base, status="invalid_nonfinite_objective_receipt")
    if abs(summary["initial_F"] - case["historical_original_F"]) > 1e-7:
        return dict(base, status="invalid_baseline_objective_identity")
    if not all(isinstance(p.get("pass"), int) and
               all(isinstance(p.get(k), int) for k in ("a", "b", "t")) and
               isinstance(p.get("feasible"), bool) and
               (not p["feasible"] or finite_number(p.get("F"))) for p in points):
        return dict(base, status="invalid_point_receipt")
    grouped: dict[int, list[dict[str, Any]]] = {}
    for point in points:
        grouped.setdefault(point["pass"], []).append(point)
    accepted_by_pass = {c.get("pass"): c for c in choices}
    passes = summary.get("passes")
    if (not isinstance(passes, int) or passes < 1 or
            len(accepted_by_pass) != len(choices) or
            any(not isinstance(p, int) for p in accepted_by_pass)):
        return dict(base, status="invalid_pass_sequence")
    accepted_count = len(choices)
    if (passes != accepted_count + 1 or
            sorted(accepted_by_pass) != list(range(1, accepted_count + 1))):
        return dict(base, status="invalid_pass_sequence")
    # The final exhaustive pass may have zero candidates after earlier
    # accepted moves remove all but one served station.
    nonempty_passes = max(grouped, default=0)
    if (sorted(grouped) != list(range(1, nonempty_passes + 1)) or
            passes not in (nonempty_passes, nonempty_passes + 1) or
            any(p < 1 or p > nonempty_passes for p in accepted_by_pass)):
        return dict(base, status="invalid_pass_sequence")
    current = float(summary["initial_F"])
    try:
        initial, capacities = inventory_vectors(
            checked_path(case["input_path"]), scenario["V"])
        replay_routes = normalize_routes(
            read_json(checked_path(case["witness_path"])).get("routes"), scenario["M"])
    except (GateError, OSError, ValueError, SyntaxError):
        return dict(base, status="invalid_original_input_or_witness_replay")
    for pass_no in range(1, passes + 1):
        expected = expected_point_tuples(replay_routes, initial, capacities, pass_no)
        actual = [(p.get("pass"), p.get("a"), p.get("b"), p.get("t"),
                   p.get("Y_a"), p.get("Y_b")) for p in grouped.get(pass_no, [])]
        if actual != expected:
            return dict(base, status="invalid_point_tuple_coverage")
        candidates = [p for p in grouped.get(pass_no, []) if p["feasible"] and
                      current - float(p["F"]) > 1e-12]
        best = min(candidates, key=lambda p: (p["F"], p["a"], p["b"], p["t"])) if candidates else None
        accepted = accepted_by_pass.get(pass_no)
        if (best is None) != (accepted is None):
            return dict(base, status="invalid_acceptance_reconstruction")
        if accepted is not None:
            if any(accepted.get(k) != best[k] for k in ("a", "b", "t")) or not finite_number(accepted.get("F")) or accepted["F"] != best["F"]:
                return dict(base, status="invalid_acceptance_reconstruction")
            current = float(accepted["F"])
            try:
                apply_change(replay_routes, accepted["a"], accepted["b"], accepted["t"])
            except GateError:
                return dict(base, status="invalid_acceptance_route_replay")
    if ((passes == nonempty_passes and accepted_by_pass.get(nonempty_passes) is not None) or
            (passes == nonempty_passes + 1 and
             (nonempty_passes and accepted_by_pass.get(nonempty_passes) is None)) or
            current != summary["final_F"]):
        return dict(base, status="invalid_final_exhaustion_reconstruction")
    routes = final.get("routes")
    if (not isinstance(routes, list) or len(routes) != scenario["M"] or
            sorted(r.get("vehicle") for r in routes if isinstance(r, dict)) != list(range(scenario["M"])) or
            any(not isinstance(r.get("nodes"), list) or not isinstance(r.get("operations"), list)
                for r in routes if isinstance(r, dict)) or
            not all(finite_number(final.get(k)) and
                    final[k] == summary["final_" + k]
                    for k in ("F", "G", "P"))):
        return dict(base, status="invalid_final_witness_receipt")
    try:
        route_replay_agrees = replay_routes == normalize_routes(final.get("routes"), scenario["M"])
    except (GateError, OSError, ValueError):
        route_replay_agrees = False
    if not route_replay_agrees:
        return dict(base, status="invalid_final_route_reconstruction")
    return dict(base, status="diagnostic_completed",
                initial_F=summary["initial_F"], final_F=summary["final_F"],
                initial_G=summary["initial_G"], final_G=summary["final_G"],
                initial_P=summary["initial_P"], final_P=summary["final_P"],
                strict_gain=summary["initial_F"] - summary["final_F"],
                physically_valid_points=summary["feasible_points"],
                accepted=summary["accepted"], exhausted=True,
                expected_integer_point_tuples_reconstructed=True,
                final_route_reconstructed_from_acceptances=True,
                final_witness_sha256=sha256(directory / "native" / "final_witness.json"),
                physical_verification_scope="qualified driver original Evaluator plus final VerifiedCandidateStore; outer route/objective consistency checked")


def write_once(path: Path, payload: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def launch_child(ready: Path, command_file: Path) -> int:
    """Wait under the assigned process job before starting the native driver."""
    while not ready.is_file():
        time.sleep(0.01)
    command = read_json(command_file).get("command")
    if not isinstance(command, list) or not all(isinstance(x, str) for x in command):
        raise GateError("invalid frozen native command")
    return subprocess.call(command, cwd=str(ROOT))


def run_case(item: dict[str, Any], binding: dict[str, Any], batch: Path,
             global_started: float) -> dict[str, Any]:
    case = item["case"]
    directory = batch / case["id"]
    case_started = time.perf_counter()
    cpu_started = time.process_time()
    directory.mkdir(exist_ok=False)
    native_dir = directory / "native"
    stdout_path = directory / "stdout.txt"
    stderr_path = directory / "stderr.txt"
    process: subprocess.Popen[Any] | None = None
    job: WindowsJob | None = None
    timed_out = False
    fault: str | None = None
    command: list[str] | None = None
    try:
        require_hash(item["source"], case["input_sha256"], "input")
        require_hash(item["witness"], case["witness_sha256"], "witness")
        require_hash(binding["executable"], binding["binary_sha256"], "driver")
        for relative, expected in binding["source_sha256"].items():
            require_hash(checked_path(relative), expected, "driver source")
        limit = min(CASE_SECONDS - (time.perf_counter() - case_started),
                    TOTAL_SECONDS - (time.perf_counter() - global_started))
        if limit <= 0:
            timed_out = True
        else:
            scenario = case["scenario"]
            command = [str(binding["executable"]), "--input", str(item["source"]),
                       "--witness", str(item["witness"]), "--T", str(scenario["T_seconds"]),
                       "--pickup-time", str(scenario["pickup_seconds"]),
                       "--drop-time", str(scenario["drop_seconds"]),
                       "--lambda", str(scenario["lambda"]), "--out-dir", str(native_dir),
                       "--whole-run-seconds", format(limit, ".9f")]
            command_file = directory / "command.json"
            ready = directory / "job_assigned.flag"
            write_once(command_file, {"command": command})
            wrapper_command = [sys.executable, str(Path(__file__).resolve()),
                               "child", "--ready", str(ready),
                               "--command-file", str(command_file)]
            with stdout_path.open("x", encoding="utf-8") as stdout, stderr_path.open("x", encoding="utf-8") as stderr:
                if os.name == "nt":
                    job = WindowsJob()
                flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
                process = subprocess.Popen(wrapper_command, cwd=str(ROOT), stdout=stdout, stderr=stderr,
                                           creationflags=flags, start_new_session=os.name != "nt")
                if job is not None:
                    job.assign(process)
                ready.write_text("assigned\n", encoding="ascii")
                remaining = min(CASE_SECONDS - (time.perf_counter() - case_started),
                                TOTAL_SECONDS - (time.perf_counter() - global_started))
                if remaining <= 0:
                    timed_out = True
                    kill_tree(process, job)
                else:
                    try:
                        process.wait(timeout=remaining)
                    except subprocess.TimeoutExpired:
                        timed_out = True
                        kill_tree(process, job)
                if job is not None:
                    job.close()
    except Exception as error:
        fault = type(error).__name__ + ": " + str(error)
        if process is not None:
            kill_tree(process, job)
        elif job is not None:
            job.close()
    returncode = process.returncode if process is not None else None
    audit = audit_native(directory, case, returncode, timed_out)
    final_hashes: dict[str, str | None] = {}
    for label, path in (("input", item["source"]), ("witness", item["witness"]),
                        ("binary", binding["executable"]),
                        ("gate", binding["gate_path"]), ("prereg", PREREG)):
        final_hashes[label] = sha256(path) if path.is_file() else None
    source_stable = all(checked_path(p).is_file() and sha256(checked_path(p)) == h
                        for p, h in binding["source_sha256"].items())
    if (final_hashes["input"] != case["input_sha256"] or
            final_hashes["witness"] != case["witness_sha256"] or
            final_hashes["binary"] != binding["binary_sha256"] or
            final_hashes["gate"] != binding["gate_sha256"] or
            final_hashes["prereg"] != binding["gate"]["preregistration_sha256"] or
            not source_stable):
        audit = dict(audit, status="invalid_identity_drift")
    if fault is not None:
        audit = dict(audit, status="resource_or_supervisor_fault", fault=fault)
    elapsed = time.perf_counter() - case_started
    overall = time.perf_counter() - global_started
    blocking_status = audit["status"].startswith(("invalid_", "resource_or_supervisor_fault"))
    if (elapsed >= CASE_SECONDS or overall >= TOTAL_SECONDS) and not blocking_status:
        audit = dict(audit, status="unknown_whole_case_deadline",
                     reason="outer receipt/audit crossed shared deadline")
    receipt = dict(schema="round93-coquantity-case-outer-receipt-v1",
                   case=case["id"], pre_receipt_status=audit["status"],
                   case_deadline_seconds=CASE_SECONDS, total_deadline_seconds=TOTAL_SECONDS,
                   outer_wall_seconds_before_receipt=elapsed,
                   total_elapsed_seconds_before_receipt=overall,
                   supervisor_cpu_seconds=time.process_time() - cpu_started,
                   child_cpu_seconds=None, child_cpu_note="not directly observable by stdlib supervisor on this host",
                   command=command, wrapper_pid=process.pid if process else None,
                   child_exit_code=returncode, timed_out=timed_out,
                   stdout_path=str(stdout_path) if stdout_path.is_file() else None,
                   stderr_path=str(stderr_path) if stderr_path.is_file() else None,
                   hashes_after=final_hashes, source_stable=source_stable,
                   evidence=audit,
                   authority="batch_completion status overrides this pre-receipt status if serialization crosses deadline")
    write_once(directory / "outer_receipt.json", receipt)
    # Receipt serialization is part of the whole-case boundary. A late write
    # is never presented as a complete exhausted case.
    after_receipt_wall = time.perf_counter() - case_started
    after_receipt_total = time.perf_counter() - global_started
    if ((after_receipt_wall >= CASE_SECONDS or after_receipt_total >= TOTAL_SECONDS)
            and not audit["status"].startswith(("invalid_", "resource_or_supervisor_fault"))):
        return dict(receipt, status="unknown_whole_case_deadline_after_receipt",
                    outer_wall_seconds_including_receipt=after_receipt_wall,
                    total_elapsed_seconds_including_receipt=after_receipt_total,
                    evidence=dict(audit, status="unknown_whole_case_deadline_after_receipt"))
    return dict(receipt, status=audit["status"],
                outer_wall_seconds_including_receipt=after_receipt_wall,
                total_elapsed_seconds_including_receipt=after_receipt_total)


def run(gate_path: Path, out: Path) -> int:
    started = time.perf_counter()
    plan = preregistration()
    cases = check_cases(plan)
    binding = qualified_gate(gate_path.resolve())
    if out.exists():
        raise GateError("batch output path already exists; no overwrite or resume")
    out.mkdir(parents=True, exist_ok=False)
    write_once(out / "batch_start.json", dict(
        schema="round93-coquantity-batch-start-v1", case_order=list(ORDER),
        prereg_sha256=sha256(PREREG), gate_path=str(gate_path.resolve()),
        gate_sha256=binding["gate_sha256"],
        binary_path=str(binding["executable"]), binary_sha256=binding["binary_sha256"],
        source_sha256=binding["source_sha256"],
        total_deadline_seconds=TOTAL_SECONDS))
    records = []
    for item in cases:
        if time.perf_counter() - started >= TOTAL_SECONDS:
            break
        receipt = run_case(item, binding, out, started)
        records.append(receipt)
        status = receipt["status"]
        if status == "diagnostic_completed":
            continue
        if status == "unknown_whole_case_deadline" and time.perf_counter() - started < TOTAL_SECONDS:
            continue
        break
    completion_wall = time.perf_counter() - started
    if completion_wall >= TOTAL_SECONDS and records and records[-1]["status"] == "diagnostic_completed":
        records[-1]["status"] = "unknown_total_deadline_before_batch_receipt"
    summary = dict(schema="round93-coquantity-batch-completion-v1",
                   statuses=[dict(case=r["case"], status=r["status"],
                                  outer_wall_seconds_including_receipt=r["outer_wall_seconds_including_receipt"])
                             for r in records],
                   completed_cases=sum(r["status"] == "diagnostic_completed" for r in records),
                   attempted_cases=len(records), planned_cases=3,
                   full_outer_wall_seconds_before_receipt=completion_wall,
                   remaining_unrun=list(ORDER[len(records):]))
    write_once(out / "batch_completion.json", summary)
    after_batch_receipt = time.perf_counter() - started
    if after_batch_receipt >= TOTAL_SECONDS:
        return 2
    return 0 if len(records) == 3 and all(r["status"] == "diagnostic_completed" for r in records) else 2


def validate() -> int:
    plan = preregistration()
    cases = check_cases(plan)
    print(json.dumps(dict(schema=plan["schema"], prereg_sha256=sha256(PREREG),
                          cases=[dict(id=i["case"]["id"], input_sha256=i["input_sha256"],
                                      witness_sha256=i["witness_sha256"]) for i in cases],
                          native_launched=False), indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="read-only prereg/path/hash/witness format check")
    launch = sub.add_parser("run", help="one complete qualified three-case batch")
    launch.add_argument("--qualification-gate", type=Path, required=True)
    launch.add_argument("--out-dir", type=Path, required=True)
    child = sub.add_parser("child", help=argparse.SUPPRESS)
    child.add_argument("--ready", type=Path, required=True)
    child.add_argument("--command-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "validate":
            return validate()
        if args.command == "child":
            return launch_child(args.ready, args.command_file)
        return run(args.qualification_gate, args.out_dir.resolve())
    except (GateError, OSError, ValueError) as error:
        print("round93 coquantity harness stopped: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
