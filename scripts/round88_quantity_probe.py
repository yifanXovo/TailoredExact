"""Offline Round88 A2 endpoint probe. Historical witnesses never seed ENS-C.

Only supervise is an admitted execution entry. It gives an entire case one
120-second external deadline, including every C++ original-verifier process.
This adapter does not call a MIP solver or change the frozen A2 flow oracle.
"""

from __future__ import annotations

import argparse
import ast
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from fractions import Fraction as F
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
from typing import Any, Callable

import round88_quantity_flow as flow


ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / "build/research/round88-a1/ExactEBRP.exe"
BINARY_SHA = "23d4fd53602d46f599f3f58e33c3ec96c4eec01b972e22ee0d4815cc42a54693"
FLOW_SHA = "fdbe04bdc7b933397aac3ec4fa9d9f0b5adf99c8550c98d14e96ce89db43328d"
WHOLE_CASE_SECONDS = 120.0
APPROVED_SOURCE_OBJECTIVE_TOLERANCE = 1e-7  # existing R88 physical audit gate


@dataclass(frozen=True)
class Case:
    key: str
    input_relative: str
    input_sha256: str
    witness_relative: str
    witness_sha256: str
    route_deadline: int
    pickup_seconds: int = 60
    drop_seconds: int = 60
    penalty_lambda: float = 0.15


CASES: dict[str, Case] = {
    "D6": Case(
        "D6",
        "reference/citibike443-regional-v1/instances/V30/cb443_V30_compact_r1_shortage_M03_Q30.txt",
        "070c2c1413840a09a264d238bdfa320ef76d293a45cab919095851afdea8c01d",
        "results/unified_exact_round88/runner_a1_startup_d6/raw/01_D6_ENS-C/result.json",
        "a8939cae620b6cdf6d20e3d2f957981bbc5144f9157b26dd5dbb5cfc91eb9c3c",
        18000),
    "E8": Case(
        "E8",
        "reference/qualification_round39/small-easy/round39_small_easy_V12_M3_Q30_slot08_seed1167625600.txt",
        "587737b9d000c1712220232a0fe957073f1f03ac649a63a4775abd9166603acd",
        "results/unified_exact_round88/runner_a1_g3/raw/02_E8_ENS-C/external/initial_witness.json",
        "70534fd162bff80ad50210ad94a02a2e0e7f6c6efafd67e58a3dea32ac1faea3",
        3600),
    "S12": Case(
        "S12",
        "reference/citibike443-regional-v1/instances/V12/cb443_V12_regional_r1_surplus_M01_Q30.txt",
        "060ee6366b2277c8427675e1a1484de7db10d2ef82a64d4e2ffa6e4695b7b626",
        "results/unified_exact_round88/runner_a1_g3/raw/05_S12_ENS-C/external/initial_witness.json",
        "af1a591e03c65fd81b96c4fe52b92978f09e34b9a2c2108ff807fc838225fd4b",
        10800),
}


class ProbeError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Parsed:
    problem: flow.Problem
    depot_initial: int
    source_input: Path


@dataclass(frozen=True)
class CppEvidence:
    objective: F
    gini: F
    penalty: F
    route_travel: tuple[F, ...]
    route_duration: tuple[F, ...]
    receipt_path: str = ""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_sha(path: Path, expected: str) -> None:
    if not path.is_file() or sha256(path) != expected:
        raise ProbeError("source_sha256_mismatch:" + str(path))


def _named_literal(text: str, name: str) -> Any:
    match = re.search(r"(?m)^\s*" + re.escape(name) +
                      r"\s*=\s*(\[[^\n]*\])", text)
    if match is None:
        raise ProbeError("missing_instance_vector:" + name)
    return ast.literal_eval(match.group(1))


def parse_instance(text: str, case: Case,
                   source_path: Path) -> Parsed:
    """Mirror selected Parser.cpp paths; stop if the selected format differs."""
    first = text.splitlines()[0]
    header = re.match(r"^\s*(\d+)\s+(\d+)\s+(\[[^\]]*\])", first)
    if header is None:
        raise ProbeError("unsupported_instance_header")
    stations = int(header.group(1))
    vehicles = int(header.group(2))
    capacities = tuple(ast.literal_eval(header.group(3)))
    initial = tuple(_named_literal(text, "initial"))
    capacity = tuple(_named_literal(text, "capacities"))
    target = tuple(_named_literal(text, "target"))
    weights = tuple(float(x) for x in _named_literal(text, "weights"))
    points = tuple(_named_literal(text, "points"))
    if (len(capacities) != vehicles or
            any(len(x) != stations + 1 for x in
                (initial, capacity, target, weights, points))):
        raise ProbeError("instance_dimension_mismatch")
    if abs(max(weights[1:]) - 10.0) <= 1e-6:
        weights = tuple(x / 10.0 for x in weights)
    # Parser.cpp gives points precedence over a serialized distances section.
    distances: list[tuple[F, ...]] = []
    for ax, ay in points:
        row = []
        for bx, by in points:
            dx = float(ax) - float(bx)
            dy = float(ay) - float(by)
            travel = math.sqrt(dx * dx + dy * dy) / 1.5
            row.append(F.from_float(travel))
        distances.append(tuple(row))
    matrix = tuple(distances)
    stock = tuple(flow.Station(
        int(initial[i]), int(capacity[i]), int(target[i]),
        F.from_float(weights[i])) for i in range(1, stations + 1))
    fleet = tuple(flow.Vehicle(
        (), int(capacities[k]), F(case.route_deadline), matrix)
        for k in range(vehicles))
    problem = flow.Problem(stock, fleet, F(case.pickup_seconds),
                           F(case.drop_seconds),
                           F.from_float(case.penalty_lambda))
    flow.validate_problem(problem)
    return Parsed(problem, int(initial[0]), source_path)


def _is_exact_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def canonical_routes(raw: Any, vehicle_count: int,
                     station_count: int) -> tuple[tuple[Any, ...], ...]:
    """Retain visit and operation order; do not normalize a changed witness."""
    if not isinstance(raw, list) or len(raw) != vehicle_count:
        raise ProbeError("route_vehicle_count_mismatch")
    by_vehicle = {}
    seen_stations: set[int] = set()
    for route in raw:
        if not isinstance(route, dict):
            raise ProbeError("route_object_invalid")
        vehicle = route.get("vehicle")
        nodes = route.get("nodes")
        operations = route.get("operations")
        if (not _is_exact_int(vehicle) or not 0 <= vehicle < vehicle_count or
                vehicle in by_vehicle):
            raise ProbeError("route_vehicle_identity")
        if (not isinstance(nodes, list) or len(nodes) < 2 or
                nodes[0] != 0 or nodes[-1] != 0 or
                any(not _is_exact_int(i) or not 0 <= i <= station_count
                    for i in nodes)):
            raise ProbeError("route_nodes_invalid")
        visits = nodes[1:-1]
        if 0 in visits or len(set(visits)) != len(visits):
            raise ProbeError("route_revisit_or_depot_inside")
        if any(i in seen_stations for i in visits):
            raise ProbeError("station_shared_by_vehicles")
        seen_stations.update(visits)
        if not isinstance(operations, list) or len(operations) != len(visits):
            raise ProbeError("route_operations_count")
        ordered_operations = []
        for visit, op in zip(visits, operations):
            if not isinstance(op, dict):
                raise ProbeError("operation_object_invalid")
            station, pickup, drop = (op.get("station"), op.get("pickup"),
                                     op.get("drop"))
            if (not all(_is_exact_int(x) for x in
                        (station, pickup, drop)) or station != visit or
                    pickup < 0 or drop < 0 or (pickup > 0) == (drop > 0)):
                raise ProbeError("operation_identity_or_sign")
            ordered_operations.append((station, pickup, drop))
        by_vehicle[vehicle] = (vehicle, tuple(nodes),
                               tuple(ordered_operations))
    return tuple(by_vehicle[k] for k in range(vehicle_count))


def inventory_from_routes(
        parsed: Parsed, canonical: tuple[tuple[Any, ...], ...]
        ) -> tuple[int, ...]:
    inventory = [s.initial for s in parsed.problem.stations]
    for _vehicle, _nodes, operations in canonical:
        for station, pickup, drop in operations:
            inventory[station - 1] += drop - pickup
    return tuple(inventory)


def attach_fixed_routes(
        parsed: Parsed, canonical: tuple[tuple[Any, ...], ...]) -> Parsed:
    fleet = tuple(flow.Vehicle(
        tuple(i - 1 for i in canonical[k][1][1:-1]),
        vehicle.capacity, vehicle.deadline, vehicle.distances)
        for k, vehicle in enumerate(parsed.problem.vehicles))
    p = parsed.problem
    attached = flow.Problem(p.stations, fleet, p.pickup_time,
                            p.drop_time, p.penalty_weight)
    flow.validate_problem(attached)
    return Parsed(attached, parsed.depot_initial, parsed.source_input)


def routes_from_inventory(parsed: Parsed,
                          inventory: tuple[int, ...]) -> dict[str, Any]:
    routes = []
    for k, vehicle in enumerate(parsed.problem.vehicles):
        nodes = [0]
        operations = []
        for i in vehicle.visits:
            net = parsed.problem.stations[i].initial - inventory[i]
            if net == 0:
                continue
            station = i + 1
            nodes.append(station)
            operations.append(dict(station=station,
                                   pickup=max(net, 0), drop=max(-net, 0)))
        nodes.append(0)
        routes.append(dict(vehicle=k, nodes=nodes, operations=operations))
    candidate = dict(routes=routes)
    canonical_routes(routes, len(routes), len(parsed.problem.stations))
    return candidate


def _finite_fraction(value: Any, label: str) -> F:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProbeError("receipt_non_numeric:" + label)
    number = float(value)
    if not math.isfinite(number):
        raise ProbeError("receipt_nonfinite:" + label)
    return F.from_float(number)


def _same_path(a: str, b: Path) -> bool:
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(
        os.path.abspath(str(b)))


def validate_cpp_receipt(result: dict[str, Any],
                         candidate: dict[str, Any], parsed: Parsed,
                         case: Case, output_path: Path) -> CppEvidence:
    """Import success is mandatory: fallback empty-route verification is not it."""
    p = parsed.problem
    expected = canonical_routes(candidate["routes"], len(p.vehicles),
                                len(p.stations))
    expected_inventory = inventory_from_routes(parsed, expected)
    if result.get("method") != "incumbent-import-test":
        raise ProbeError("receipt_wrong_method")
    if result.get("status") != "diagnostic_complete":
        raise ProbeError("receipt_diagnostic_not_complete")
    if result.get("incumbent_import_verified") is not True:
        raise ProbeError("candidate_not_verified_by_cpp")
    if (result.get("incumbent_import_attempted") is not True or
            result.get("incumbent_source") != "incumbent-json" or
            result.get("incumbent_import_errors") != []):
        raise ProbeError("receipt_import_source_identity")
    if (result.get("instance_name") != parsed.source_input.name or
            not isinstance(result.get("input_path"), str) or
            not _same_path(result["input_path"], parsed.source_input) or
            not isinstance(result.get("result_file"), str) or
            not _same_path(result["result_file"], output_path)):
        raise ProbeError("receipt_source_or_output_identity")
    for name, expected_value in (
            ("route_time_limit_seconds", case.route_deadline),
            ("pickup_time_seconds", case.pickup_seconds),
            ("drop_time_seconds", case.drop_seconds)):
        if _finite_fraction(result.get(name), name) != expected_value:
            raise ProbeError("receipt_scenario_identity:" + name)
    actual = canonical_routes(result.get("routes"),
                              len(p.vehicles), len(p.stations))
    if actual != expected:
        raise ProbeError("receipt_route_or_operation_identity")
    verification = result.get("verification")
    if not isinstance(verification, dict):
        raise ProbeError("receipt_verification_missing")
    for flag in ("feasible", "original_solution_feasible",
                 "original_objective_recomputed", "routes_start_end_depot",
                 "station_disjoint", "load_feasible", "station_feasible",
                 "duration_feasible", "objective_matches"):
        if verification.get(flag) is not True:
            raise ProbeError("receipt_verification_failed:" + flag)
    if verification.get("errors") != []:
        raise ProbeError("receipt_verification_errors")
    full_inventory = [parsed.depot_initial, *expected_inventory]
    if (verification.get("final_inventories") != full_inventory or
            result.get("final_inventories") != full_inventory):
        raise ProbeError("receipt_final_inventory_identity")
    objective = _finite_fraction(verification.get("objective"), "objective")
    gini = _finite_fraction(verification.get("G"), "G")
    penalty = _finite_fraction(verification.get("P"), "P")
    if any(_finite_fraction(result.get(field), field) != expected_value
           for field, expected_value in
           (("objective", objective), ("G", gini), ("P", penalty),
            ("incumbent_import_objective", objective))):
        raise ProbeError("receipt_objective_component_identity")
    if abs(objective - gini - F.from_float(case.penalty_lambda) * penalty) > F(1, 10_000_000):
        raise ProbeError("receipt_lambda_objective_identity")
    raw_travel = verification.get("route_travel_time")
    raw_duration = verification.get("route_duration")
    if (not isinstance(raw_travel, list) or
            not isinstance(raw_duration, list) or
            len(raw_travel) != len(p.vehicles) or
            len(raw_duration) != len(p.vehicles)):
        raise ProbeError("receipt_route_timing_shape")
    travel = tuple(_finite_fraction(x, "route_travel") for x in raw_travel)
    duration = tuple(_finite_fraction(x, "route_duration") for x in raw_duration)
    return CppEvidence(objective, gini, penalty, travel, duration,
                       str(output_path))


def cpp_nominal_budgets(parsed: Parsed,
                        evidence: CppEvidence) -> tuple[int, ...]:
    """Agree on integer floors using exact binary values emitted by C++."""
    p = parsed.problem
    if len(evidence.route_travel) != len(p.vehicles):
        raise ProbeError("cpp_travel_dimension")
    service = p.pickup_time + p.drop_time
    cpp_budgets = []
    for vehicle, travel in zip(p.vehicles, evidence.route_travel):
        if travel > vehicle.deadline:
            raise ProbeError("domain_rejected_cpp_full_template_time")
        stock = sum(p.stations[i].initial for i in vehicle.visits)
        cpp_budgets.append(stock if service == 0 else min(
            stock, int((vehicle.deadline - travel) // service)))
    try:
        python_budgets = flow.nominal_budgets(p)
    except flow.QuantityDomainError as error:
        raise ProbeError("domain_uncertain_parser_vs_cpp:" + error.code)
    if tuple(cpp_budgets) != python_budgets:
        raise ProbeError("domain_uncertain_budget_floor_disagreement")
    return tuple(cpp_budgets)


def _append_jsonl(path: Path, item: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(item, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _write_json(path: Path, item: dict[str, Any]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(item, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def cpp_verify(parsed: Parsed, case: Case, candidate: dict[str, Any],
               directory: Path, call_number: int,
               event: Callable[[dict[str, Any]], None]) -> CppEvidence:
    stem = "candidate_%05d" % call_number
    candidate_path = directory / (stem + ".json")
    result_path = directory / (stem + "_result.json")
    log_path = directory / (stem + ".log")
    stdout_path = directory / (stem + ".stdout.txt")
    stderr_path = directory / (stem + ".stderr.txt")
    with candidate_path.open("x", encoding="utf-8") as stream:
        json.dump(candidate, stream, sort_keys=True, allow_nan=False)
        stream.write("\n")
    command = [str(BINARY), "--input", str(parsed.source_input),
               "--T", str(case.route_deadline),
               "--pickup-time", str(case.pickup_seconds),
               "--drop-time", str(case.drop_seconds),
               "--lambda", repr(case.penalty_lambda),
               "--method", "incumbent-import-test",
               "--incumbent-json", str(candidate_path),
               "--incumbent-format", "route_json",
               "--out", str(result_path), "--log", str(log_path)]
    event(dict(kind="cpp_verify_started", call=call_number,
               candidate_path=str(candidate_path),
               candidate_sha256=sha256(candidate_path), command=command,
               start_wall_time=time.time()))
    started = time.perf_counter()
    completed = subprocess.run(command, capture_output=True, text=True,
                               check=False)
    elapsed = time.perf_counter() - started
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    event(dict(kind="cpp_verify_finished", call=call_number,
               returncode=completed.returncode, wall_seconds=elapsed,
               output_exists=result_path.is_file(),
               result_sha256=sha256(result_path)
               if result_path.is_file() else None))
    if completed.returncode != 0 or not result_path.is_file():
        raise ProbeError("cpp_verifier_process_failed")
    with result_path.open("r", encoding="utf-8") as stream:
        result = json.load(stream)
    if not isinstance(result, dict):
        raise ProbeError("cpp_verifier_result_shape")
    evidence = validate_cpp_receipt(result, candidate, parsed, case,
                                    result_path)
    event(dict(kind="cpp_candidate_accepted_by_verifier", call=call_number,
               objective=str(evidence.objective), G=str(evidence.gini),
               P=str(evidence.penalty)))
    return evidence


def scan_integer_line(
        parsed: Parsed, current: tuple[int, ...], proposal: tuple[int, ...],
        current_evidence: CppEvidence,
        verifier: Callable[[tuple[int, ...]], CppEvidence],
        event: Callable[[dict[str, Any]], None]
        ) -> tuple[tuple[int, ...], CppEvidence, int, int]:
    """Exhaust every primitive integer point, accepting strict original F."""
    line = flow.primitive_segment(current, proposal)
    best, best_evidence = current, current_evidence
    rejected, cpp_calls = 0, 0
    for step, inventory in enumerate(line[1:], 1):
        if not flow.exact_physical_feasible(parsed.problem, inventory):
            rejected += 1
            event(dict(kind="internal_physical_reject", step=step,
                       inventory=inventory))
            continue
        cpp_calls += 1
        evidence = verifier(inventory)
        event(dict(kind="line_cpp_verified", step=step,
                   inventory=inventory, objective=str(evidence.objective),
                   improved=evidence.objective < best_evidence.objective))
        if evidence.objective < best_evidence.objective:
            best, best_evidence = inventory, evidence
    return best, best_evidence, rejected, cpp_calls


def _certificate_json(cert: flow.FlowCertificate) -> dict[str, Any]:
    return dict(integer_cost_scale=cert.integer_cost_scale,
                integer_flow_cost=cert.integer_flow_cost,
                potentials=cert.potentials,
                positive_residual_edges=cert.positive_residual_edges,
                negative_cycle_augmentations=cert.negative_cycle_augmentations,
                arc_flows=cert.arc_flows)


def diagnose(case: Case, directory: Path) -> dict[str, Any]:
    if os.environ.get("ROUND88_A2_PROBE_SUPERVISED") != "1":
        raise ProbeError("diagnose_requires_whole_case_supervisor")
    ready_path = os.environ.get("ROUND88_A2_PROBE_READY_PATH")
    if not ready_path:
        raise ProbeError("diagnose_requires_supervisor_ready_path")
    # The supervisor first places this process in its kill-on-close job. No
    # importer may start before that assignment succeeds.
    while not Path(ready_path).is_file():
        time.sleep(0.01)
    started = time.perf_counter()
    events = directory / "events.jsonl"
    candidates = directory / "candidates"
    candidates.mkdir(exist_ok=False)

    def event(item: dict[str, Any]) -> None:
        item["elapsed_seconds"] = time.perf_counter() - started
        _append_jsonl(events, item)

    source = (ROOT / case.input_relative).resolve()
    witness = (ROOT / case.witness_relative).resolve()
    require_sha(source, case.input_sha256)
    require_sha(witness, case.witness_sha256)
    require_sha(BINARY, BINARY_SHA)
    require_sha(ROOT / "scripts/round88_quantity_flow.py", FLOW_SHA)
    with witness.open("r", encoding="utf-8") as stream:
        historical = json.load(stream)
    if not isinstance(historical, dict):
        raise ProbeError("historical_witness_shape")
    parsed = parse_instance(source.read_text(encoding="utf-8"), case, source)
    canonical = canonical_routes(historical.get("routes"),
                                 len(parsed.problem.vehicles),
                                 len(parsed.problem.stations))
    parsed = attach_fixed_routes(parsed, canonical)
    current = inventory_from_routes(parsed, canonical)
    if canonical_routes(routes_from_inventory(parsed, current)["routes"],
                        len(parsed.problem.vehicles),
                        len(parsed.problem.stations)) != canonical:
        raise ProbeError("historical_route_mapping_not_reversible")
    result: dict[str, Any] = dict(
        status="running", case=case.key,
        input_path=str(source), input_sha256=case.input_sha256,
        witness_path=str(witness), witness_sha256=case.witness_sha256,
        binary_sha256=BINARY_SHA, flow_sha256=FLOW_SHA,
        original_inventory=list(current), original_routes=historical["routes"],
        cpp_calls=0, internal_rejected_points=0, rounds=[],
        start_wall_time=time.time())
    _write_json(directory / "result.json", result)
    event(dict(kind="historical_witness_mapped", inventory=current,
               source_objective=historical.get("objective")))

    def verify(inventory: tuple[int, ...]) -> CppEvidence:
        call_number = result["cpp_calls"]
        result["cpp_calls"] += 1
        _write_json(directory / "result.json", result)
        return cpp_verify(parsed, case, routes_from_inventory(parsed, inventory),
                          candidates, call_number, event)

    evidence = verify(current)
    source_objective = _finite_fraction(historical.get("objective"),
                                        "historical_objective")
    if abs(evidence.objective - source_objective) > F(1, 10_000_000):
        raise ProbeError("historical_objective_cpp_mismatch")
    result["original_cpp_objective"] = str(evidence.objective)
    result["original_cpp_G"] = str(evidence.gini)
    result["original_cpp_P"] = str(evidence.penalty)
    result["original_route_travel"] = [str(x) for x in evidence.route_travel]
    result["original_route_duration"] = [str(x) for x in evidence.route_duration]
    _write_json(directory / "result.json", result)
    seen = {current}
    while True:
        round_started = time.perf_counter()
        try:
            budgets = cpp_nominal_budgets(parsed, evidence)
            flow.validate_current(parsed.problem, current, budgets)
        except flow.QuantityDomainError as error:
            raise ProbeError(error.code)
        if not flow.exact_physical_feasible(parsed.problem, current):
            raise ProbeError("domain_rejected_current_internal_physical")
        weights = flow.gradient(parsed.problem, current)
        if weights is None:
            status = "no_gradient_at_zero"
            event(dict(kind="terminal", reason=status))
            break
        oracle_started = time.perf_counter()
        proposal, certificate = flow._linear_oracle(
            parsed.problem, weights, budgets)
        oracle_seconds = time.perf_counter() - oracle_started
        if not flow.in_nominal_network_domain(parsed.problem, proposal,
                                               budgets):
            raise ProbeError("oracle_projection_outside_nominal_domain")
        line = flow.primitive_segment(current, proposal)
        if any(not flow.in_nominal_network_domain(parsed.problem, point,
                                                   budgets) for point in line):
            raise ProbeError("oracle_line_outside_nominal_domain")
        linear_delta = sum((weight * (new - old)
                            for weight, old, new in
                            zip(weights, current, proposal)), F(0))
        record: dict[str, Any] = dict(
            index=len(result["rounds"]),
            current_inventory=current, current_cpp_objective=str(evidence.objective),
            budgets=budgets, gradient=[str(x) for x in weights],
            proposal_inventory=proposal, linear_delta=str(linear_delta),
            primitive_steps=len(line) - 1,
            certificate=_certificate_json(certificate),
            oracle_seconds=oracle_seconds)
        event(dict(kind="oracle_complete", round=record["index"],
                   proposal=proposal, primitive_steps=len(line) - 1,
                   oracle_seconds=oracle_seconds))
        if len(line) == 1:
            record["status"] = "no_direction"
            record["round_wall_seconds"] = time.perf_counter() - round_started
            result["rounds"].append(record)
            _write_json(directory / "result.json", result)
            status = "no_direction"
            break
        best, best_evidence, rejected, verified = scan_integer_line(
            parsed, current, proposal, evidence, verify, event)
        result["internal_rejected_points"] += rejected
        record.update(internal_rejected_points=rejected,
                      cpp_verified_line_points=verified,
                      accepted_inventory=best if best != current else None,
                      best_cpp_objective=str(best_evidence.objective),
                      round_wall_seconds=time.perf_counter() - round_started)
        if best == current:
            record["status"] = "no_verified_improvement"
            result["rounds"].append(record)
            _write_json(directory / "result.json", result)
            status = "no_verified_improvement"
            break
        if best in seen or not best_evidence.objective < evidence.objective:
            raise ProbeError("strict_descent_or_cycle_failure")
        record["status"] = "improved"
        result["rounds"].append(record)
        event(dict(kind="round_strict_improvement", round=record["index"],
                   objective_before=str(evidence.objective),
                   objective_after=str(best_evidence.objective),
                   inventory=best))
        current, evidence = best, best_evidence
        seen.add(current)
        parsed = attach_fixed_routes(parsed, canonical_routes(
            routes_from_inventory(parsed, current)["routes"],
            len(parsed.problem.vehicles), len(parsed.problem.stations)))
        _write_json(directory / "result.json", result)
    result.update(status="completed_heuristic_endpoint", stop_reason=status,
                  final_inventory=current,
                  final_cpp_objective=str(evidence.objective),
                  final_cpp_G=str(evidence.gini), final_cpp_P=str(evidence.penalty),
                  final_route_travel=[str(x) for x in evidence.route_travel],
                  final_route_duration=[str(x) for x in evidence.route_duration],
                  final_receipt_path=evidence.receipt_path,
                  diagnosis_wall_seconds=time.perf_counter() - started)
    _write_json(directory / "result.json", result)
    return result


class _WindowsJob:
    """A standard Win32 kill-on-close job covering the child and its C++ heirs."""

    def __init__(self) -> None:
        class BasicLimit(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
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
                "ReadOperationCount", "WriteOperationCount",
                "OtherOperationCount", "ReadTransferCount",
                "WriteTransferCount", "OtherTransferCount")]

        class ExtendedLimit(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BasicLimit),
                        ("IoInfo", IoCounters),
                        ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        self.api = ctypes.windll.kernel32
        self.api.CreateJobObjectW.argtypes = (ctypes.c_void_p,
                                               ctypes.c_wchar_p)
        self.api.CreateJobObjectW.restype = ctypes.c_void_p
        self.api.SetInformationJobObject.argtypes = (
            ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint)
        self.api.SetInformationJobObject.restype = wintypes.BOOL
        self.api.AssignProcessToJobObject.argtypes = (
            ctypes.c_void_p, ctypes.c_void_p)
        self.api.AssignProcessToJobObject.restype = wintypes.BOOL
        self.api.CloseHandle.argtypes = (ctypes.c_void_p,)
        self.api.CloseHandle.restype = wintypes.BOOL
        self.handle = self.api.CreateJobObjectW(None, None)
        if not self.handle:
            raise ProbeError("supervisor_job_create_failed")
        info = ExtendedLimit()
        info.BasicLimitInformation.LimitFlags = 0x00002000
        if not self.api.SetInformationJobObject(
                self.handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
            self.close()
            raise ProbeError("supervisor_job_kill_on_close_failed")

    def assign(self, process: subprocess.Popen[str]) -> None:
        if not self.api.AssignProcessToJobObject(
                self.handle, int(process._handle)):
            raise ProbeError("supervisor_job_assignment_failed")

    def close(self) -> None:
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


def _kill_process_tree(process: subprocess.Popen[str],
                       job: _WindowsJob | None) -> None:
    if job is not None:
        job.close()
    if os.name == "nt":
        if process.poll() is None:
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                           capture_output=True, check=False)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def supervise(case: Case, directory: Path, limit: float) -> dict[str, Any]:
    if limit != WHOLE_CASE_SECONDS:
        raise ProbeError("whole_case_limit_must_be_120_seconds")
    started = time.perf_counter()
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    script = Path(__file__).resolve()
    source = (ROOT / case.input_relative).resolve()
    witness = (ROOT / case.witness_relative).resolve()
    preflight: dict[str, Any] = {}
    process: subprocess.Popen[str] | None = None
    job: _WindowsJob | None = None
    output = error_output = ""
    expired = False
    returncode: int | None = None
    try:
        for label, path, expected in (
                ("binary", BINARY, BINARY_SHA),
                ("flow", ROOT / "scripts/round88_quantity_flow.py", FLOW_SHA),
                ("input", source, case.input_sha256),
                ("witness", witness, case.witness_sha256)):
            require_sha(path, expected)
            preflight[label + "_sha256"] = expected
        preflight["adapter_sha256"] = sha256(script)
        command = [sys.executable, str(script), "diagnose", "--case",
                   case.key, "--out-dir", str(directory)]
        if time.perf_counter() - started >= limit:
            expired = True
        else:
            env = os.environ.copy()
            env["ROUND88_A2_PROBE_SUPERVISED"] = "1"
            ready = directory / "supervisor_ready.flag"
            env["ROUND88_A2_PROBE_READY_PATH"] = str(ready)
            if os.name == "nt":
                job = _WindowsJob()
            flags = (subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt"
                     else 0)
            process = subprocess.Popen(
                command, cwd=str(ROOT), env=env, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, creationflags=flags,
                start_new_session=os.name != "nt")
            if job is not None:
                job.assign(process)
            ready.write_text("assigned\n", encoding="ascii")
            remaining = max(0.0, limit - (time.perf_counter() - started))
            if remaining <= 0:
                expired = True
                _kill_process_tree(process, job)
                output, error_output = process.communicate()
            else:
                try:
                    output, error_output = process.communicate(timeout=remaining)
                except subprocess.TimeoutExpired:
                    expired = True
                    _kill_process_tree(process, job)
                    output, error_output = process.communicate()
            if job is not None:
                job.close()
        returncode = process.returncode if process is not None else None
    except Exception as error:
        if process is not None:
            _kill_process_tree(process, job)
        elif job is not None:
            job.close()
        error_output += "\nsupervisor_exception=" + repr(error)
    (directory / "supervisor_stdout.txt").write_text(output, encoding="utf-8")
    (directory / "supervisor_stderr.txt").write_text(error_output,
                                                       encoding="utf-8")
    final_hashes: dict[str, str | None] = {}
    for label, path in (
            ("adapter", script),
            ("binary", BINARY),
            ("flow", ROOT / "scripts/round88_quantity_flow.py"),
            ("input", source), ("witness", witness)):
        final_hashes[label + "_sha256"] = sha256(path) if path.is_file() else None
    elapsed = time.perf_counter() - started
    child_result_path = directory / "result.json"
    child: dict[str, Any] | None = None
    if child_result_path.is_file():
        try:
            with child_result_path.open("r", encoding="utf-8") as stream:
                loaded = json.load(stream)
            if isinstance(loaded, dict):
                child = loaded
        except (OSError, ValueError):
            pass
    stable = all(final_hashes.get(name) == value
                 for name, value in preflight.items()
                 if name.endswith("_sha256"))
    if expired or elapsed > limit:
        status = "unknown_whole_process_deadline"
    elif not stable:
        status = "invalid_source_identity_drift"
    elif (returncode == 0 and child is not None and
          child.get("status") == "completed_heuristic_endpoint"):
        status = "diagnostic_completed"
    elif child is not None and str(child.get("status", "")).startswith(
            ("domain_rejected", "domain_uncertain")):
        status = "diagnostic_inapplicable"
    else:
        status = "diagnostic_invalid"
    summary = dict(status=status, case=case.key,
                   whole_process_limit_seconds=limit,
                   whole_process_wall_seconds=elapsed,
                   wall_clock_boundary="before_supervision_json_write",
                   child_returncode=returncode, child_pid=process.pid
                   if process else None, timed_out=expired or elapsed > limit,
                   preflight=preflight, final_hashes=final_hashes,
                   child_status=child.get("status") if child else None,
                   child_cpp_calls=child.get("cpp_calls") if child else None,
                   command=command if "command" in locals() else None)
    _write_json(directory / "supervision.json", summary)
    after_write = time.perf_counter() - started
    if after_write > limit and status != "unknown_whole_process_deadline":
        summary["status"] = "unknown_whole_process_deadline"
        summary["timed_out"] = True
        summary["after_first_summary_write_wall_seconds"] = after_write
        _write_json(directory / "supervision.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("supervise", "diagnose"))
    parser.add_argument("--case", required=True, choices=tuple(CASES))
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--whole-process-limit-seconds", type=float,
                        default=WHOLE_CASE_SECONDS)
    args = parser.parse_args()
    case = CASES[args.case]
    if args.mode == "supervise":
        result = supervise(case, args.out_dir, args.whole_process_limit_seconds)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] in (
            "diagnostic_completed", "diagnostic_inapplicable") else 2
    directory = args.out_dir.resolve()
    if not directory.is_dir():
        raise ProbeError("diagnose_output_directory_missing")
    try:
        diagnose(case, directory)
        return 0
    except (ProbeError, flow.QuantityDomainError) as error:
        result_path = directory / "result.json"
        result: dict[str, Any] = {}
        if result_path.is_file():
            try:
                with result_path.open("r", encoding="utf-8") as stream:
                    result = json.load(stream)
            except (OSError, ValueError):
                pass
        result.update(status=error.code, error_type=type(error).__name__,
                      error_text=str(error))
        _write_json(result_path, result)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
