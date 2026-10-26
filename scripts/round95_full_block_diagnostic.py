"""One-shot R95 full-block G2 diagnosis on the three frozen R93 witnesses.

`validate` is read-only and never launches native code. `run` requires a later
G1 qualification gate binding the built driver and source hashes. This script
does not build, run ENS-C, or inject a historical witness into a formal arm.

The Windows job/deadline and identity supervision below is scoped adaptation
of frozen scripts/round93_coquantity_diagnostic.py, SHA256
79a1440e6690e0299211149457cf112cfcaae9c79d5985133dd37f5b8000cd09.
Only the R95 receipt/domain/acceptance audit is new; R93 bytes are untouched.
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
PREREG = ROOT / "results/unified_exact_round95/full_block_diagnostic_preregistration.json"
R93_PREREG = ROOT / "results/unified_exact_round93/coquantity_diagnostic_preregistration.json"
EXPECTED_SCHEMA = "round95-full-block-fixed-witness-diagnostic-preregistration-v1"
GATE_SCHEMA = "round95-full-block-g1-qualified-driver-v1"
LEASE_SCHEMA = "round95-full-block-g2-run-lease-v1"
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
    require_hash(R93_PREREG, plan.get("round93_source_manifest_sha256"),
                 "frozen R93 source manifest")
    previous = read_json(R93_PREREG)
    execution = plan.get("execution", {})
    cases = plan.get("cases", [])
    if (plan.get("schema") != EXPECTED_SCHEMA or
            execution.get("case_order") != list(ORDER) or
            execution.get("planned_cases") != 3 or
            execution.get("repetitions_per_case") != 1 or
            execution.get("whole_case_external_deadline_seconds") != 120 or
            execution.get("maximum_sum_case_deadlines_seconds") != 360 or
            not isinstance(cases, list) or [c.get("id") for c in cases] != list(ORDER) or
            cases != previous.get("cases")):
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
        "src/Round95FullBlockDescent.cpp",
        "include/Round95FullBlockDescent.hpp",
        "tests/round95_full_block_diagnostic.cpp",
        "tests/round95_full_block_tests.cpp",
        "scripts/round95_full_block_diagnostic.py",
        "CMakeLists.txt",
    }
    pins = gate.get("source_sha256")
    if not isinstance(pins, dict) or not required_source.issubset(pins):
        raise GateError("G1 source set incomplete")
    for relative, expected in pins.items():
        require_hash(checked_path(relative), expected, "G1 source")
    return dict(gate=gate, gate_path=path, gate_sha256=sha256(path),
                executable=executable, binary_sha256=binary["sha256"].lower(),
                source_sha256={k: v.lower() for k, v in pins.items()})


def qualified_lease(path: Path, binding: dict[str, Any], out: Path) -> dict[str, Any]:
    if not path.is_relative_to(ROOT.resolve()):
        raise GateError("G2 run lease must be a repository file")
    lease = read_json(path)
    output = lease.get("output_dir")
    if (lease.get("schema") != LEASE_SCHEMA or
            lease.get("status") != "authorized" or
            lease.get("qualification_gate_sha256") != binding["gate_sha256"] or
            lease.get("preregistration_sha256") != sha256(PREREG) or
            lease.get("harness_sha256") != sha256(Path(__file__).resolve()) or
            lease.get("case_order") != list(ORDER) or
            lease.get("repetitions_per_case") != 1 or
            lease.get("whole_case_external_deadline_seconds") != CASE_SECONDS or
            lease.get("maximum_sum_case_deadlines_seconds") != TOTAL_SECONDS or
            not isinstance(output, str) or checked_path(output) != out):
        raise GateError("missing/mismatched separate root G2 run lease")
    return dict(run_lease_path=path, run_lease_sha256=sha256(path))


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


def whole_number(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def vehicle_capacities(path: Path, vertices: int, vehicles: int) -> list[int]:
    first = path.read_text(encoding="utf-8").splitlines()[0]
    match = re.fullmatch(r"\s*(\d+)\s+(\d+)\s+(\[[^\]]*\])\s*", first)
    if match is None or int(match.group(1)) != vertices or int(match.group(2)) != vehicles:
        raise GateError("input vehicle/capacity header mismatch")
    q = ast.literal_eval(match.group(3))
    if not isinstance(q, list) or len(q) != vehicles or not all(
            whole_number(x) and x >= 0 for x in q):
        raise GateError("input vehicle capacities malformed")
    return q


def inventory_state(routes: list[dict[str, Any]], initial: list[int],
                    capacities: list[int]) -> tuple[list[int], list[int]]:
    y = initial.copy()
    served: list[int] = []
    for route in routes:
        for station, pickup, drop in route["operations"]:
            if (not 0 < station < len(initial) or station in served or
                    pickup < 0 or drop < 0 or (pickup > 0) == (drop > 0)):
                raise GateError("invalid served operation in route replay")
            served.append(station)
            y[station] = initial[station] - pickup + drop
            if not 0 <= y[station] <= capacities[station]:
                raise GateError("replayed inventory outside capacity")
    return y, sorted(served)


def apply_change(routes: list[dict[str, Any]], initial: list[int],
                 a: int, b: int, u: int, v: int) -> None:
    found: list[int] = []
    for route in routes:
        next_ops = []
        for station, pickup, drop in route["operations"]:
            if station in (a, b):
                found.append(station)
                signed = initial[station] - (u if station == a else v)
                pickup, drop = max(signed, 0), max(-signed, 0)
            if pickup or drop:
                next_ops.append([station, pickup, drop])
        route["operations"] = next_ops
        route["nodes"] = [0] + [op[0] for op in next_ops] + [0]
    if sorted(found) != [a, b]:
        raise GateError("accepted stations absent or repeated")


def prefix_bands(routes: list[dict[str, Any]], q: list[int],
                 a: int, b: int) -> dict[str, dict[str, int | bool]]:
    bands: dict[str, dict[str, int | bool]] = {
        name: dict(present=False, low=0, high=0, prefixes=0)
        for name in ("band10", "band01", "band11")
    }
    for route in routes:
        load = 0
        passed_a = passed_b = False
        capacity = q[route["vehicle"]]
        for station, pickup, drop in route["operations"]:
            load += pickup - drop
            if not 0 <= load <= capacity:
                raise GateError("replay baseline route load invalid")
            passed_a |= station == a
            passed_b |= station == b
            name = ("band11" if passed_a and passed_b else
                    "band10" if passed_a else "band01" if passed_b else None)
            if name is None:
                continue
            band = bands[name]
            low, high = load - capacity, load
            if band["present"]:
                band["low"] = max(band["low"], low)
                band["high"] = min(band["high"], high)
            else:
                band.update(present=True, low=low, high=high)
            band["prefixes"] += 1
    return bands


def interval_for_u(bands: dict[str, dict[str, int | bool]],
                   old_a: int, old_b: int, capacity_b: int, u: int) -> tuple[int, int, int]:
    da = u - old_a
    low, high = 0, capacity_b
    ten, one, eleven = (bands[k] for k in ("band10", "band01", "band11"))
    if ten["present"] and not ten["low"] <= da <= ten["high"]:
        high = -1
    if one["present"]:
        low = max(low, old_b + one["low"])
        high = min(high, old_b + one["high"])
    if eleven["present"]:
        low = max(low, old_b + eleven["low"] - da)
        high = min(high, old_b + eleven["high"] - da)
    if low > high:
        return 0, -1, 0
    count = high - low + 1 - (u == old_a and low <= old_b <= high)
    return low, high, count


def replay_complete(case: dict[str, Any], summary: dict[str, Any],
                    final: dict[str, Any], bands: list[dict[str, Any]],
                    intervals: list[dict[str, Any]], points: list[dict[str, Any]],
                    choices: list[dict[str, Any]]) -> dict[str, Any]:
    scenario = case["scenario"]
    source = checked_path(case["input_path"])
    witness = checked_path(case["witness_path"])
    initial, capacities = inventory_vectors(source, scenario["V"])
    q = vehicle_capacities(source, scenario["V"], scenario["M"])
    routes = normalize_routes(read_json(witness).get("routes"), scenario["M"])
    if not all(finite_number(summary.get(k)) for k in
               ("initial_F", "initial_G", "initial_P", "final_F", "final_G", "final_P")):
        raise GateError("nonfinite baseline/final original F/G/P")
    if abs(summary["initial_F"] - case["historical_original_F"]) > 1e-7:
        raise GateError("baseline original F differs from frozen witness")
    passes = summary.get("passes")
    if (not whole_number(passes) or passes != len(choices) + 1 or passes < 1 or
            summary.get("accepted") != len(choices)):
        raise GateError("pass/acceptance count mismatch")
    bi = ii = pi = 0
    pair_count = rectangle_count = pruned_count = survivor_count = feasible_count = 0
    current_F = float(summary["initial_F"])
    for pass_no in range(1, passes + 1):
        inventory, served = inventory_state(routes, initial, capacities)
        best: tuple[float, int, int, int, int] | None = None
        for ia, a in enumerate(served):
            for b in served[ia + 1:]:
                pair_count += 1
                rectangle = (capacities[a] + 1) * (capacities[b] + 1) - 1
                rectangle_count += rectangle
                expected_bands = prefix_bands(routes, q, a, b)
                expected_pair = dict(pass_=pass_no, a=a, b=b, old_a=inventory[a],
                                     old_b=inventory[b], capacity_a=capacities[a],
                                     capacity_b=capacities[b], rectangle_points=rectangle)
                if bi >= len(bands):
                    raise GateError("pair-band ledger ends early")
                pair = bands[bi]; bi += 1
                if (not all(pair.get(k) == value for k, value in expected_pair.items()
                            if k != "pass_") or pair.get("pass") != pass_no or
                        any(pair.get(name) != expected_bands[name]
                            for name in ("band10", "band01", "band11"))):
                    raise GateError("pair-band row differs from original prefixes")
                for u in range(capacities[a] + 1):
                    low, high, survivors = interval_for_u(
                        expected_bands, inventory[a], inventory[b], capacities[b], u)
                    pruned_count += capacities[b] + 1 - (u == inventory[a]) - survivors
                    survivor_count += survivors
                    if ii >= len(intervals):
                        raise GateError("u-interval ledger ends early")
                    row = intervals[ii]; ii += 1
                    expected_interval = dict(pass_=pass_no, a=a, b=b, u=u,
                                             v_low=low, v_high=high,
                                             surviving_points=survivors)
                    if (row.get("pass") != pass_no or
                            not all(row.get(k) == value for k, value in
                                    expected_interval.items() if k != "pass_")):
                        raise GateError("u-interval differs from exact prefix bands")
                    for v in range(low, high + 1):
                        if u == inventory[a] and v == inventory[b]:
                            continue
                        if pi >= len(points):
                            raise GateError("Evaluator point ledger ends early")
                        point = points[pi]; pi += 1
                        if (not all(point.get(k) == value for k, value in
                                    dict(pass_=pass_no, a=a, b=b, u=u, v=v).items()
                                    if k != "pass_") or point.get("pass") != pass_no):
                            raise GateError("Evaluator tuple coverage/order mismatch")
                        if (point.get("physical_checked") is not True or
                                point.get("load_feasible") is not True or
                                point.get("objective_recomputed") is not True or
                                not isinstance(point.get("feasible"), bool) or
                                not all(finite_number(point.get(k)) for k in ("F", "G", "P"))):
                            raise GateError("surviving point lacks original Evaluator receipt")
                        if point["feasible"]:
                            feasible_count += 1
                            improving = current_F - point["F"] > 1e-12
                            if point.get("reason") != ("" if improving else
                                                      "no_strict_original_F_improvement"):
                                raise GateError("point strict original-F decision mismatch")
                            if improving:
                                key = (point["F"], a, b, u, v)
                                best = key if best is None or key < best else best
                        elif not point.get("reason"):
                            raise GateError("infeasible original Evaluator point lacks reason")
        accepted = choices[pass_no - 1] if pass_no <= len(choices) else None
        if (best is None) != (accepted is None):
            raise GateError("accepted move not complete-scan strict best")
        if accepted is not None:
            if (accepted.get("pass") != pass_no or
                    not all(accepted.get(k) == value for k, value in
                            zip(("F", "a", "b", "u", "v"), best))):
                raise GateError("accepted F/tie/tuple differs from complete-scan best")
            _, a, b, u, v = best
            apply_change(routes, initial, a, b, u, v)
            current_F = best[0]
    if (bi != len(bands) or ii != len(intervals) or pi != len(points) or
            rectangle_count != pruned_count + survivor_count):
        raise GateError("full domain ledgers have surplus or missing rows")
    expected_counts = dict(station_pairs=pair_count, rectangle_points=rectangle_count,
                           load_pruned=pruned_count, candidate_points=survivor_count,
                           evaluator_points=survivor_count, feasible_points=feasible_count)
    if not all(summary.get(k) == value and whole_number(summary.get(k))
               for k, value in expected_counts.items()):
        raise GateError("summary rectangle/pruned/Evaluator counts mismatch")
    if (summary.get("integer_domain_rejections") != 0 or
            summary.get("nonfinite_rejections") != 0):
        raise GateError("integer/nonfinite Evaluator uncertainty cannot be exhausted")
    if current_F != summary["final_F"]:
        raise GateError("accepted chain final F differs from summary")
    if routes != normalize_routes(final.get("routes"), scenario["M"]):
        raise GateError("accepted chain final route differs from original witness")
    if not all(finite_number(final.get(k)) and final[k] == summary["final_" + k]
               for k in ("F", "G", "P")):
        raise GateError("final original F/G/P receipt mismatch")
    return dict(initial_F=summary["initial_F"], final_F=summary["final_F"],
                initial_G=summary["initial_G"], final_G=summary["final_G"],
                initial_P=summary["initial_P"], final_P=summary["final_P"],
                strict_gain=summary["initial_F"] - summary["final_F"],
                physically_valid_points=feasible_count, accepted=len(choices),
                rectangle_points=rectangle_count, load_pruned=pruned_count,
                evaluator_points=survivor_count, exhausted=True,
                exact_band_interval_tuple_coverage=True,
                final_route_reconstructed_from_acceptances=True,
                physical_verification_scope="qualified original C++ Evaluator plus final VerifiedCandidateStore; outer checks band/route/F receipts")


def audit_native(directory: Path, case: dict[str, Any], returncode: int | None,
                 timed_out: bool) -> dict[str, Any]:
    ledgers = {}
    parseable = {}
    for name, filename in (("bands", "bands.jsonl"), ("intervals", "intervals.jsonl"),
                           ("points", "points.jsonl"),
                           ("acceptances", "acceptances.jsonl")):
        ledgers[name], parseable[name] = load_jsonl(directory / "native" / filename)
    base = dict(ledger_rows={k: len(v) for k, v in ledgers.items()},
                ledger_parseable=parseable)
    # A fully written point row is evidence of a domain/numeric fault even
    # when the driver is killed before its summary can be committed.
    if any(p.get("reason") in ("evaluator_integer_domain", "nonfinite_original_F")
           for p in ledgers["points"]):
        return dict(base, status="invalid_original_evaluator_or_domain_fault",
                    reason="committed point reports Evaluator domain/nonfinite F")
    summary_path = directory / "native" / "summary.json"
    try:
        summary = read_json(summary_path) if summary_path.is_file() else None
    except (OSError, ValueError, GateError):
        summary = None
    # A recorded correctness fault has priority over timeout or nonzero exit.
    if summary is not None:
        domain = summary.get("integer_domain_rejections", 0)
        nonfinite = summary.get("nonfinite_rejections", 0)
        if (not whole_number(domain) or not whole_number(nonfinite) or
                domain < 0 or nonfinite < 0):
            return dict(base, status="invalid_original_evaluator_or_domain_fault",
                        reason="malformed domain/nonfinite counters")
        if (summary.get("verification_failed") is True or domain > 0 or
                nonfinite > 0):
            return dict(base, status="invalid_original_evaluator_or_domain_fault",
                        reason=summary.get("rejection_reason", ""))
        scenario = case["scenario"]
        input_hash = summary.get("input_sha256")
        witness_hash = summary.get("witness_sha256")
        if (not isinstance(input_hash, str) or
                not isinstance(witness_hash, str) or
                input_hash.lower() != case["input_sha256"] or
                witness_hash.lower() != case["witness_sha256"] or
                any(summary.get(k) != scenario[key] for k, key in
                    (("V", "V"), ("M", "M"), ("T", "T_seconds"),
                     ("pickup_time", "pickup_seconds"),
                     ("drop_time", "drop_seconds"), ("lambda", "lambda")))):
            return dict(base, status="invalid_identity_or_scenario_receipt")
    if timed_out:
        return dict(base, status="unknown_whole_case_deadline",
                    reason="native receipts may have unflushed accepted work")
    if returncode != 0:
        return dict(base, status="resource_or_native_fault",
                    reason="native process returned nonzero or was not launched")
    if summary is None or not all(parseable.values()):
        return dict(base, status="invalid_missing_or_malformed_receipt")
    try:
        final = read_json(directory / "native" / "final_witness.json")
        launch = read_json(directory / "command.json").get("command")
        if (not isinstance(launch, list) or len(launch) < 2 or
                launch[-2] != "--whole-run-seconds" or
                not isinstance(launch[-1], str)):
            raise GateError("native whole-run command receipt malformed")
        scenario = case["scenario"]
        if (summary.get("input_sha256", "").lower() != case["input_sha256"] or
                summary.get("witness_sha256", "").lower() != case["witness_sha256"] or
                any(summary.get(k) != scenario[key] for k, key in
                    (("V", "V"), ("M", "M"), ("T", "T_seconds"),
                     ("pickup_time", "pickup_seconds"),
                     ("drop_time", "drop_seconds"), ("lambda", "lambda"))) or
                summary.get("whole_run_seconds", 0) <= 0 or
                summary["whole_run_seconds"] > CASE_SECONDS or
                summary["whole_run_seconds"] != float(launch[-1]) or
                summary.get("wall_seconds_scope") != "sampled_before_summary_write"):
            raise GateError("identity/scenario/whole-run cap mismatch")
        if (summary.get("verification_failed") is not False or
                summary.get("deadline") is not False or
                summary.get("exhausted") is not True):
            raise GateError("driver did not finish valid exhaustive descent")
        result = replay_complete(case, summary, final, ledgers["bands"],
                                 ledgers["intervals"], ledgers["points"],
                                 ledgers["acceptances"])
    except (GateError, OSError, ValueError, TypeError, KeyError,
            AttributeError, SyntaxError) as error:
        return dict(base, status="invalid_domain_or_acceptance_audit",
                    reason=str(error))
    return dict(base, status="diagnostic_completed", **result,
                final_witness_sha256=sha256(directory / "native" / "final_witness.json"))


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
        require_hash(binding["run_lease_path"], binding["run_lease_sha256"],
                     "separate G2 run lease")
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
    try:
        audit = audit_native(directory, case, returncode, timed_out)
    except Exception as error:
        audit = dict(status="resource_or_supervisor_fault",
                     fault="audit failed: " + type(error).__name__ + ": " + str(error))
    final_hashes: dict[str, str | None] = {}
    source_stable = False
    try:
        for label, path in (("input", item["source"]), ("witness", item["witness"]),
                            ("binary", binding["executable"]),
                            ("gate", binding["gate_path"]), ("prereg", PREREG),
                            ("run_lease", binding["run_lease_path"])):
            final_hashes[label] = sha256(path) if path.is_file() else None
        source_stable = all(checked_path(p).is_file() and sha256(checked_path(p)) == h
                            for p, h in binding["source_sha256"].items())
    except Exception as error:
        audit = dict(audit, status="resource_or_supervisor_fault",
                     fault="post-run identity audit failed: " +
                           type(error).__name__ + ": " + str(error))
    if (final_hashes.get("input") != case["input_sha256"] or
            final_hashes.get("witness") != case["witness_sha256"] or
            final_hashes.get("binary") != binding["binary_sha256"] or
            final_hashes.get("gate") != binding["gate_sha256"] or
            final_hashes.get("prereg") != binding["gate"]["preregistration_sha256"] or
            final_hashes.get("run_lease") != binding["run_lease_sha256"] or
            not source_stable):
        audit = dict(audit, status="invalid_identity_drift")
    if fault is not None:
        audit = dict(audit, status="resource_or_supervisor_fault", fault=fault)
    elapsed = time.perf_counter() - case_started
    overall = time.perf_counter() - global_started
    blocking_status = audit["status"].startswith(("invalid_", "resource_or_"))
    if (elapsed >= CASE_SECONDS or overall >= TOTAL_SECONDS) and not blocking_status:
        audit = dict(audit, status="unknown_whole_case_deadline",
                     reason="outer receipt/audit crossed shared deadline")
    receipt = dict(schema="round95-full-block-case-outer-receipt-v1",
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
            and not audit["status"].startswith(("invalid_", "resource_or_"))):
        return dict(receipt, status="unknown_whole_case_deadline_after_receipt",
                    outer_wall_seconds_including_receipt=after_receipt_wall,
                    total_elapsed_seconds_including_receipt=after_receipt_total,
                    evidence=dict(audit, status="unknown_whole_case_deadline_after_receipt"))
    return dict(receipt, status=audit["status"],
                outer_wall_seconds_including_receipt=after_receipt_wall,
                total_elapsed_seconds_including_receipt=after_receipt_total)


def run(gate_path: Path, lease_path: Path, out: Path) -> int:
    started = time.perf_counter()
    plan = preregistration()
    cases = check_cases(plan)
    binding = qualified_gate(gate_path.resolve())
    binding.update(qualified_lease(lease_path.resolve(), binding, out))
    if out.exists():
        raise GateError("batch output path already exists; no overwrite or resume")
    out.mkdir(parents=True, exist_ok=False)
    write_once(out / "batch_start.json", dict(
        schema="round95-full-block-batch-start-v1", case_order=list(ORDER),
        prereg_sha256=sha256(PREREG), gate_path=str(gate_path.resolve()),
        gate_sha256=binding["gate_sha256"],
        run_lease_path=str(binding["run_lease_path"]),
        run_lease_sha256=binding["run_lease_sha256"],
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
    summary = dict(schema="round95-full-block-batch-completion-v1",
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
    ast.parse(Path(__file__).read_text(encoding="utf-8-sig"))
    plan = preregistration()
    cases = check_cases(plan)
    print(json.dumps(dict(schema=plan["schema"], prereg_sha256=sha256(PREREG),
                          cases=[dict(id=i["case"]["id"], input_sha256=i["input_sha256"],
                                      witness_sha256=i["witness_sha256"]) for i in cases],
                          syntax_parsed=True, native_launched=False), indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="read-only prereg/path/hash/witness format check")
    launch = sub.add_parser("run", help="one complete qualified three-case batch")
    launch.add_argument("--qualification-gate", type=Path, required=True)
    launch.add_argument("--run-lease", type=Path, required=True)
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
        return run(args.qualification_gate, args.run_lease,
                   args.out_dir.resolve())
    except (GateError, OSError, ValueError) as error:
        print("round95 full-block harness stopped: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


