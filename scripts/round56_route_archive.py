#!/usr/bin/env python3
"""Materialize and independently verify one native Round 56 route witness."""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any

import round56_common as r56


SOURCE_FREEZE = "75e58521158aba8628ebc9444444ec3841415285"
EXECUTABLE_SHA256 = "34e992060e3adffd3a7795c2c783672044996edd7234bf7e9f58a662b1c32fea"
OFFICIAL_RAW = r56.EVIDENCE / "local_raw" / "official"
SOLUTIONS = r56.EVIDENCE / "solutions"
TOL = 1e-7


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        if len(value) != 1:
            raise RuntimeError(f"expected one result: {path}")
        value = value[0]
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def objective(base: dict[str, Any], inventory: list[int]) -> tuple[float, float, float]:
    ratios = [inventory[i] / base["target"][i] for i in range(1, base["V"] + 1)]
    total = sum(ratios)
    dispersion = sum(abs(ratios[i] - ratios[j]) for i in range(len(ratios)) for j in range(i + 1, len(ratios)))
    gini = dispersion / (base["V"] * total) if total > 0 else 0.0
    penalty = sum(base["weights"][i] * abs(ratios[i - 1] - 1.0) for i in range(1, base["V"] + 1))
    return gini, penalty, gini + r56.LAMBDA * penalty


def classify(result: dict[str, Any]) -> str:
    verification = result.get("verification") or {}
    feasible = bool(verification.get("original_solution_feasible") and verification.get("original_objective_recomputed"))
    strict = bool(result.get("strict_certified_original_problem"))
    if strict and feasible and not verification.get("errors"):
        return "certified_optimal_solution"
    if strict and not feasible:
        return "correctness_failure"
    if feasible and result.get("routes"):
        return "verified_incumbent_noncertified"
    return "no_verified_incumbent"


def descriptor_for(scenario_id: str) -> dict[str, Any]:
    return load_json(r56.REFERENCE / "scenario_descriptors" / f"{scenario_id}.json")


def build_package(scenario_id: str) -> dict[str, Any]:
    descriptor = descriptor_for(scenario_id)
    result_path = OFFICIAL_RAW / scenario_id / "result.json"
    result = load_json(result_path)
    solution_class = classify(result)
    if solution_class in {"no_verified_incumbent", "correctness_failure", "execution_failure"}:
        return {"scenario_id": scenario_id, "solution_class": solution_class, "package_available": False}
    base = load_json(r56.ROOT / descriptor["base_landscape_path"])
    output = SOLUTIONS / scenario_id
    output.mkdir(parents=True, exist_ok=True)
    materialize_start = time.perf_counter()
    native_routes = {int(route["vehicle"]): route for route in result["routes"]}
    if len(native_routes) != len(result["routes"]):
        raise RuntimeError(f"duplicate native vehicle index: {scenario_id}")
    inventory = list(base["initial"])
    station_seen: set[int] = set()
    route_rows: list[dict[str, Any]] = []
    operation_rows: list[dict[str, Any]] = []
    package_routes: list[dict[str, Any]] = []
    for vehicle in range(int(descriptor["M"])):
        raw = native_routes.get(vehicle, {"vehicle": vehicle, "nodes": [0, 0], "operations": []})
        nodes = [int(value) for value in raw.get("nodes", [])]
        operations = list(raw.get("operations", []))
        used = len(nodes) > 2 or bool(operations)
        if not used:
            nodes = [0, 0]
            operations = []
        op_by_station: dict[int, list[dict[str, Any]]] = {}
        for operation in operations:
            op_by_station.setdefault(int(operation["station"]), []).append(operation)
        travel = 0.0
        cumulative_travel = 0.0
        cumulative_duration = 0.0
        load = 0
        total_pickup = 0
        total_station_drop = 0
        detailed_operations = []
        for position, station in enumerate(nodes[1:-1], start=1):
            station = int(station)
            predecessor = int(nodes[position - 1])
            successor = int(nodes[position + 1])
            arc = float(base["distances"][predecessor][station])
            travel += arc
            cumulative_travel += arc
            cumulative_duration += arc
            choices = op_by_station.get(station, [])
            if len(choices) != 1:
                raise RuntimeError(f"station {station} does not have exactly one native operation")
            operation = choices[0]
            pickup = int(operation["pickup"])
            drop = int(operation["drop"])
            load_before = load
            load += pickup - drop
            operation_time = descriptor["pickup_time_seconds"] * pickup + descriptor["drop_time_seconds"] * drop
            cumulative_duration += operation_time
            total_pickup += pickup
            total_station_drop += drop
            inventory[station] += drop - pickup
            if station in station_seen:
                raise RuntimeError(f"station {station} occurs in multiple routes")
            station_seen.add(station)
            detail = {
                "native_vehicle_index": vehicle, "route_sequence_position": position,
                "predecessor": predecessor, "station": station, "successor": successor,
                "travel_time_from_predecessor": arc, "cumulative_travel_time": cumulative_travel,
                "pickup": pickup, "drop": drop, "load_before_operation": load_before,
                "load_after_operation": load, "operation_time": operation_time,
                "cumulative_route_duration": cumulative_duration,
                "initial_station_inventory": base["initial"][station],
                "inventory_change": drop - pickup, "final_station_inventory": inventory[station],
            }
            detailed_operations.append(detail)
            operation_rows.append(detail)
        if len(nodes) >= 2:
            return_arc = float(base["distances"][int(nodes[-2])][int(nodes[-1])])
            travel += return_arc
        depot_unload = load
        operation_time_total = (
            descriptor["pickup_time_seconds"] * total_pickup +
            descriptor["drop_time_seconds"] * (total_station_drop + depot_unload)
        )
        duration = travel + operation_time_total
        slack = descriptor["route_time_limit_seconds"] - duration
        route = {
            "native_vehicle_index": vehicle, "used": used, "nodes": nodes,
            "operations": detailed_operations, "vehicle_capacity": descriptor["complete_Q_vector"][vehicle],
            "initial_vehicle_load": 0, "final_depot_unload": depot_unload,
            "total_pickup": total_pickup, "total_station_drop": total_station_drop,
            "travel_time": travel, "operation_time": operation_time_total,
            "route_duration": duration, "route_slack": slack,
            "utilization": duration / descriptor["route_time_limit_seconds"],
            "native_route_present_in_result": vehicle in native_routes,
        }
        package_routes.append(route)
        route_rows.append({key: (r56.canonical_json(value) if isinstance(value, (list, dict)) else value) for key, value in route.items() if key != "operations"})
    gini, penalty, obj = objective(base, inventory)
    materialize_seconds = time.perf_counter() - materialize_start
    package = {
        "schema": "round56-native-solution-v1", "scenario_id": scenario_id,
        "mathematical_instance_sha256": descriptor["mathematical_instance_sha256"],
        "run_identity_sha256": result["run_identity_sha256"],
        "solution_class": solution_class, "certificate_status": bool(result.get("strict_certified_original_problem")),
        "strict_rejection_reason": result.get("strict_certificate_rejection_reason", "none"),
        "objective": obj, "G": gini, "P": penalty,
        "lower_bound": result.get("lower_bound"), "verified_upper_bound": result.get("upper_bound"),
        "final_gap": result.get("gap"), "final_inventory": inventory,
        "V": descriptor["V"], "M": descriptor["M"], "complete_Q_vector": descriptor["complete_Q_vector"],
        "route_time_limit_seconds": descriptor["route_time_limit_seconds"],
        "pickup_time_seconds": descriptor["pickup_time_seconds"], "drop_time_seconds": descriptor["drop_time_seconds"],
        "source_commit": SOURCE_FREEZE, "executable_sha256": EXECUTABLE_SHA256,
        "algorithm_wall_time_seconds": result.get("final_process_wall_time_seconds", result.get("runtime_seconds")),
        "algorithm_work": result.get("external_gini_tree_work", result.get("gurobi_work", 0.0)),
        "mandatory_in_memory_verification_seconds": None,
        "mandatory_in_memory_verification_accounting": "included in frozen algorithm timing; not separately instrumented and not subtracted",
        "route_archive_materialization_seconds": materialize_seconds,
        "routes": package_routes,
        "source_result_path": r56.repo_path(result_path),
        "source_result_sha256": r56.sha256_file(result_path),
        "route_post_optimization_performed": False,
    }
    serialization_start = time.perf_counter()
    native_path = output / "native_solution.json"
    r56.write_json(native_path, package)
    r56.write_csv(output / "routes.csv", route_rows)
    r56.write_csv(output / "operations.csv", operation_rows, fields=(
        "native_vehicle_index", "route_sequence_position", "predecessor", "station", "successor",
        "travel_time_from_predecessor", "cumulative_travel_time", "pickup", "drop",
        "load_before_operation", "load_after_operation", "operation_time", "cumulative_route_duration",
        "initial_station_inventory", "inventory_change", "final_station_inventory",
    ))
    r56.write_csv(output / "final_inventory.csv", [
        {"station": station, "initial_inventory": base["initial"][station], "target_inventory": base["target"][station], "final_inventory": inventory[station]}
        for station in range(base["V"] + 1)
    ])
    serialization_seconds = time.perf_counter() - serialization_start
    verification = verify_package(scenario_id, write=False)
    verification["route_archive_materialization_seconds"] = materialize_seconds
    verification["route_archive_serialization_seconds"] = serialization_seconds
    r56.write_json(output / "solution_verification.json", verification)
    hash_lines = []
    for name in ("native_solution.json", "routes.csv", "operations.csv", "final_inventory.csv", "solution_verification.json"):
        path = output / name
        hash_lines.append(f"{r56.sha256_file(path)}  {name}")
    (output / "solution_sha256.txt").write_text("\n".join(hash_lines) + "\n", encoding="utf-8")
    return {
        "scenario_id": scenario_id, "solution_class": solution_class,
        "package_available": True, "archive_verification_passed": verification["passed"],
        "package_path": r56.repo_path(output), "materialization_seconds": materialize_seconds,
        "serialization_seconds": serialization_seconds,
        "independent_verification_seconds": verification["independent_archive_verification_seconds"],
    }


def near(left: float, right: float) -> bool:
    return abs(float(left) - float(right)) <= TOL * max(1.0, abs(float(left)), abs(float(right)))


def verify_package(scenario_id: str, *, write: bool = True) -> dict[str, Any]:
    started = time.perf_counter()
    descriptor = descriptor_for(scenario_id)
    base_path = r56.ROOT / descriptor["base_landscape_path"]
    if r56.sha256_file(base_path) != descriptor["base_landscape_sha256"]:
        raise RuntimeError("base landscape hash mismatch")
    base = load_json(base_path)
    output = SOLUTIONS / scenario_id
    package = load_json(output / "native_solution.json")
    failures: list[str] = []
    if package.get("scenario_id") != scenario_id: failures.append("scenario_id")
    if package.get("mathematical_instance_sha256") != descriptor["mathematical_instance_sha256"]: failures.append("mathematical_hash")
    if package.get("source_commit") != SOURCE_FREEZE: failures.append("source_commit")
    if package.get("executable_sha256") != EXECUTABLE_SHA256: failures.append("executable_sha256")
    if package.get("route_post_optimization_performed") is not False: failures.append("post_optimization")
    inventory = list(base["initial"])
    seen: set[int] = set()
    if len(package.get("routes", [])) != descriptor["M"]: failures.append("route_count")
    for expected_vehicle, route in enumerate(package.get("routes", [])):
        if route.get("native_vehicle_index") != expected_vehicle: failures.append(f"vehicle_index_{expected_vehicle}")
        nodes = route.get("nodes", [])
        if len(nodes) < 2 or nodes[0] != 0 or nodes[-1] != 0: failures.append(f"depot_{expected_vehicle}")
        load = 0
        travel = sum(base["distances"][int(a)][int(b)] for a, b in zip(nodes, nodes[1:]))
        pickup_total = 0
        drop_total = 0
        operations = route.get("operations", [])
        if len(operations) != max(0, len(nodes) - 2): failures.append(f"operation_count_{expected_vehicle}")
        for position, operation in enumerate(operations, start=1):
            station = int(operation["station"])
            if int(nodes[position]) != station: failures.append(f"node_operation_{expected_vehicle}_{position}")
            if station in seen: failures.append(f"station_unique_{station}")
            seen.add(station)
            pickup, drop = int(operation["pickup"]), int(operation["drop"])
            if pickup < 0 or drop < 0 or (pickup > 0 and drop > 0) or (pickup == 0 and drop == 0): failures.append(f"operation_valid_{station}")
            if int(operation["load_before_operation"]) != load: failures.append(f"load_before_{station}")
            load += pickup - drop
            if load < 0 or load > int(route["vehicle_capacity"]): failures.append(f"load_capacity_{station}")
            if int(operation["load_after_operation"]) != load: failures.append(f"load_after_{station}")
            inventory[station] += drop - pickup
            pickup_total += pickup
            drop_total += drop
        operation_time = descriptor["pickup_time_seconds"] * pickup_total + descriptor["drop_time_seconds"] * (drop_total + load)
        duration = travel + operation_time
        if not near(travel, route["travel_time"]): failures.append(f"travel_{expected_vehicle}")
        if not near(operation_time, route["operation_time"]): failures.append(f"operation_time_{expected_vehicle}")
        if not near(duration, route["route_duration"]): failures.append(f"duration_{expected_vehicle}")
        if duration > descriptor["route_time_limit_seconds"] + TOL: failures.append(f"route_limit_{expected_vehicle}")
        if int(route["final_depot_unload"]) != load: failures.append(f"depot_unload_{expected_vehicle}")
    if inventory != package.get("final_inventory"): failures.append("final_inventory")
    if any(inventory[i] < 0 or inventory[i] > base["capacities"][i] for i in range(1, base["V"] + 1)): failures.append("station_capacity")
    gini, penalty, obj = objective(base, inventory)
    if not near(gini, package["G"]): failures.append("G")
    if not near(penalty, package["P"]): failures.append("P")
    if not near(obj, package["objective"]): failures.append("objective")
    expected_class = "certified_optimal_solution" if package.get("certificate_status") else "verified_incumbent_noncertified"
    if package.get("solution_class") != expected_class: failures.append("solution_class_certificate")
    verification = {
        "schema": "round56-independent-route-verification-v1",
        "scenario_id": scenario_id, "passed": not failures, "failures": failures,
        "scenario_hash_verified": "mathematical_hash" not in failures,
        "source_executable_identity_verified": not ({"source_commit", "executable_sha256"} & set(failures)),
        "route_start_end_depot_verified": not any(value.startswith("depot_") for value in failures),
        "station_uniqueness_verified": not any(value.startswith("station_unique_") for value in failures),
        "load_and_capacity_verified": not any(value.startswith(("load_", "load_capacity_")) for value in failures),
        "route_duration_verified": not any(value.startswith(("travel_", "operation_time_", "duration_", "route_limit_")) for value in failures),
        "final_inventory_verified": "final_inventory" not in failures and "station_capacity" not in failures,
        "objective_verified": not ({"G", "P", "objective"} & set(failures)),
        "certificate_class_verified": "solution_class_certificate" not in failures,
        "optimization_or_repair_performed": False,
        "independent_archive_verification_seconds": time.perf_counter() - started,
    }
    if write:
        r56.write_json(output / "solution_verification.json", verification)
    return verification


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario-id")
    parser.add_argument("--all-completed", action="store_true")
    args = parser.parse_args()
    if bool(args.scenario_id) == bool(args.all_completed):
        raise RuntimeError("select exactly one of --scenario-id or --all-completed")
    ids = [args.scenario_id] if args.scenario_id else [path.parent.name for path in sorted(OFFICIAL_RAW.glob("*/result.json"))]
    rows = [build_package(scenario_id) for scenario_id in ids]
    print(json.dumps({"processed": len(rows), "rows": rows}, indent=2))
    return 0 if all(not row.get("package_available") or row.get("archive_verification_passed") for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
