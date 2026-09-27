#!/usr/bin/env python3
"""Independent verification and native witness archiving for Round 58."""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

import round58_common as r58


TOL = 1e-6


def object_json(path: Path) -> dict[str, Any]:
    value = r58.read_json(path)
    if isinstance(value, list):
        if len(value) != 1:
            raise RuntimeError(f"expected one result: {path}")
        value = value[0]
    if not isinstance(value, dict):
        raise RuntimeError(f"expected object: {path}")
    return value


def panel_index() -> dict[str, dict[str, str]]:
    return {row["scenario_id"]: row for row in r58.read_csv(
        r58.EVIDENCE / "round58_complete_panel.csv")}


def near(left: float, right: float) -> bool:
    return abs(float(left) - float(right)) <= TOL * max(
        1.0, abs(float(left)), abs(float(right)))


def instance_data(row: dict[str, str]) -> dict[str, Any]:
    landscape_path = r58.ROOT / row["landscape_path"]
    if r58.sha256_file(landscape_path) != row["landscape_file_sha256"]:
        raise RuntimeError("landscape hash mismatch")
    landscape = object_json(landscape_path)
    depot = list(landscape["depot"]["coordinate_utm18n_meters"])
    points = [depot] + [list(point) for point in landscape["points_utm18n_meters"]]
    distances = [[
        math.hypot(float(left[0]) - float(right[0]),
                   float(left[1]) - float(right[1])) / 1.5
        for right in points] for left in points]
    return {
        "V": int(row["V"]), "M": int(row["M"]),
        "Q": [int(row["Q"])] * int(row["M"]),
        "T": float(row["T_seconds"]),
        "pickup_seconds": float(row["pickup_seconds"]),
        "drop_seconds": float(row["drop_seconds"]),
        "lambda": float(row["lambda"]),
        "capacity": [int(landscape["depot"]["capacity_placeholder"])] +
                    [int(value) for value in landscape["capacities"]],
        "initial": [int(landscape["depot"]["initial_placeholder"])] +
                   [int(value) for value in landscape["initial"]],
        "target": [int(landscape["depot"]["target_placeholder"])] +
                  [int(value) for value in landscape["target"]],
        "weights": [0.0] + [float(value) for value in landscape["weights"]],
        "points": points, "distances": distances,
    }


def objective(data: dict[str, Any], inventory: list[int]) -> tuple[float, float, float]:
    ratios = [inventory[i] / data["target"][i]
              for i in range(1, data["V"] + 1)]
    total = sum(ratios)
    dispersion = sum(abs(ratios[i] - ratios[j])
                     for i in range(len(ratios))
                     for j in range(i + 1, len(ratios)))
    gini = dispersion / (data["V"] * total) if total > 0 else 0.0
    penalty = sum(data["weights"][i] * abs(ratios[i - 1] - 1.0)
                  for i in range(1, data["V"] + 1))
    return gini, penalty, gini + data["lambda"] * penalty


def verify_native_result(scenario_id: str, result_path: Path) -> dict[str, Any]:
    started = time.perf_counter()
    row = panel_index()[scenario_id]
    data = instance_data(row)
    result = object_json(result_path)
    failures: list[str] = []
    raw_routes = list(result.get("routes") or [])
    by_vehicle: dict[int, dict[str, Any]] = {}
    for route in raw_routes:
        vehicle = int(route.get("vehicle", -1))
        if vehicle in by_vehicle or not 0 <= vehicle < data["M"]:
            failures.append(f"invalid_or_duplicate_vehicle:{vehicle}")
        else:
            by_vehicle[vehicle] = route
    inventory = list(data["initial"])
    visited_global: set[int] = set()
    detailed_routes: list[dict[str, Any]] = []
    operation_rows: list[dict[str, Any]] = []
    for vehicle in range(data["M"]):
        raw = by_vehicle.get(vehicle, {
            "vehicle": vehicle, "nodes": [0, 0], "operations": []})
        nodes = [int(value) for value in (raw.get("nodes") or [0, 0])]
        operations = list(raw.get("operations") or [])
        if len(nodes) < 2 or nodes[0] != 0 or nodes[-1] != 0:
            failures.append(f"route_not_depot_closed:{vehicle}")
            nodes = [0, 0]
            operations = []
        stations = nodes[1:-1]
        if any(not 1 <= station <= data["V"] for station in stations):
            failures.append(f"station_out_of_range:{vehicle}")
        if len(set(stations)) != len(stations):
            failures.append(f"station_repeated_within_route:{vehicle}")
        if visited_global.intersection(stations):
            failures.append(f"station_repeated_across_routes:{vehicle}")
        visited_global.update(stations)
        op_by_station: dict[int, list[dict[str, Any]]] = {}
        for operation in operations:
            op_by_station.setdefault(int(operation.get("station", -1)), []).append(operation)
        if set(op_by_station) != set(stations) or any(
                len(values) != 1 for values in op_by_station.values()):
            failures.append(f"operation_station_roundtrip_failed:{vehicle}")
        load = 0
        travel = 0.0
        station_operation_time = 0.0
        detailed_operations: list[dict[str, Any]] = []
        for position, station in enumerate(stations, start=1):
            predecessor = nodes[position - 1]
            arc = data["distances"][predecessor][station]
            travel += arc
            choices = op_by_station.get(station, [])
            operation = choices[0] if len(choices) == 1 else {
                "station": station, "pickup": 0, "drop": 0}
            pickup = int(operation.get("pickup", 0))
            drop = int(operation.get("drop", 0))
            if pickup < 0 or drop < 0 or (pickup > 0 and drop > 0):
                failures.append(f"invalid_pickup_drop:{vehicle}:{station}")
            load_before = load
            load += pickup - drop
            if load < 0 or load > data["Q"][vehicle]:
                failures.append(f"vehicle_load_violation:{vehicle}:{station}")
            inventory[station] += drop - pickup
            if not 0 <= inventory[station] <= data["capacity"][station]:
                failures.append(f"station_inventory_violation:{station}")
            op_seconds = (pickup * data["pickup_seconds"] +
                          drop * data["drop_seconds"])
            station_operation_time += op_seconds
            detail = {
                "vehicle": vehicle, "route_sequence_position": position,
                "predecessor": predecessor, "station": station,
                "successor": nodes[position + 1],
                "pickup": pickup, "drop": drop,
                "load_before": load_before, "load_after": load,
                "travel_time_from_predecessor": arc,
                "operation_time": op_seconds,
                "station_inventory_after": inventory[station],
            }
            detailed_operations.append(detail)
            operation_rows.append(detail)
        if len(nodes) >= 2:
            travel += data["distances"][nodes[-2]][0]
        depot_unload = load
        operation_time = station_operation_time + depot_unload * data["drop_seconds"]
        duration = travel + operation_time
        if duration > data["T"] + TOL:
            failures.append(f"route_duration_violation:{vehicle}")
        detailed_routes.append({
            "vehicle": vehicle, "used": bool(stations or operations),
            "nodes": nodes, "vehicle_capacity": data["Q"][vehicle],
            "operations": detailed_operations, "travel_time": travel,
            "operation_time": operation_time, "route_duration": duration,
            "route_time_limit": data["T"],
            "route_utilization": duration / data["T"] if data["T"] > 0 else 0.0,
            "final_depot_unload": depot_unload,
        })
    gini, penalty, recomputed = objective(data, inventory)
    native_verification = result.get("verification") or {}
    if result.get("objective") is not None and not near(recomputed, float(result["objective"])):
        failures.append("result_objective_mismatch")
    if native_verification.get("objective") is not None and not near(
            recomputed, float(native_verification["objective"])):
        failures.append("native_verification_objective_mismatch")
    native_inventory = native_verification.get("final_inventories")
    if native_inventory is not None and [int(x) for x in native_inventory] != inventory:
        failures.append("native_final_inventory_mismatch")
    if result.get("scenario_id") != scenario_id:
        failures.append("scenario_id_mismatch")
    if result.get("mathematical_instance_sha256") != row["scenario_sha256"]:
        failures.append("mathematical_identity_mismatch")
    return {
        "schema": "round58-independent-native-result-verification-v1",
        "scenario_id": scenario_id, "result_path": r58.repo_path(result_path),
        "result_sha256": r58.sha256_file(result_path),
        "passed": not failures, "failures": failures,
        "original_solution_feasible": not failures,
        "routes_start_end_depot": not any("route_not_depot_closed" in x for x in failures),
        "station_disjoint": not any("station_repeated" in x for x in failures),
        "load_and_capacity_verified": not any("load_violation" in x for x in failures),
        "station_inventory_verified": not any("station_inventory" in x for x in failures),
        "route_duration_verified": not any("duration_violation" in x for x in failures),
        "objective_verified": not any("objective_mismatch" in x for x in failures),
        "objective": recomputed, "G": gini, "P": penalty,
        "final_inventory": inventory, "routes": detailed_routes,
        "operations": operation_rows,
        "independent_verification_seconds": time.perf_counter() - started,
        "optimization_or_repair_performed": False,
    }


def archive_native_result(scenario_id: str, method: str,
                          result_path: Path, source_commit: str,
                          executable_sha256: str) -> dict[str, Any]:
    if method not in {"k1_am_sf", "pgrb"}:
        raise RuntimeError(f"unknown Round 58 method: {method}")
    verification = verify_native_result(scenario_id, result_path)
    if not verification["passed"]:
        raise RuntimeError(
            f"native result verification failed: {scenario_id}/{method}: " +
            ";".join(verification["failures"]))
    row = panel_index()[scenario_id]
    result = object_json(result_path)
    output = r58.SOLUTIONS / scenario_id / method
    output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    package = {
        "schema": "round58-native-solution-v1",
        "dataset_family": r58.DATASET_FAMILY,
        "scenario_id": scenario_id, "method": method,
        "mathematical_instance_sha256": row["scenario_sha256"],
        "run_identity_sha256": result.get("run_identity_sha256"),
        "source_commit": source_commit,
        "executable_sha256": executable_sha256,
        "strict_certificate": bool(result.get("strict_certified_original_problem")),
        "certificate_label": "certified" if result.get(
            "strict_certified_original_problem") else "noncertified",
        "native_status": (result.get("gurobi_status_text") if method == "pgrb"
                          else result.get("status")),
        "objective": verification["objective"], "G": verification["G"],
        "P": verification["P"],
        "route_time_limit_seconds": int(row["T_seconds"]),
        "M": int(row["M"]), "Q": int(row["Q"]),
        "routes": verification["routes"],
        "final_inventory": verification["final_inventory"],
        "source_result_path": r58.repo_path(result_path),
        "source_result_sha256": r58.sha256_file(result_path),
        "route_post_optimization_performed": False,
        "native_witness_preserved": True,
    }
    r58.write_json(output / "native_solution.json", package)
    route_rows = []
    for route in verification["routes"]:
        route_rows.append({
            "vehicle": route["vehicle"], "used": route["used"],
            "nodes": r58.canonical_json(route["nodes"]),
            "vehicle_capacity": route["vehicle_capacity"],
            "travel_time": route["travel_time"],
            "operation_time": route["operation_time"],
            "route_duration": route["route_duration"],
            "route_time_limit": route["route_time_limit"],
            "route_utilization": route["route_utilization"],
            "final_depot_unload": route["final_depot_unload"],
        })
    r58.write_csv(output / "routes.csv", route_rows)
    operation_fields = [
        "vehicle", "route_sequence_position", "predecessor", "station",
        "successor", "pickup", "drop", "load_before", "load_after",
        "travel_time_from_predecessor", "operation_time",
        "station_inventory_after",
    ]
    r58.write_csv(output / "operations.csv", verification["operations"],
                  operation_fields)
    data = instance_data(row)
    r58.write_csv(output / "final_inventory.csv", [{
        "station": station, "initial_inventory": data["initial"][station],
        "target_inventory": data["target"][station],
        "final_inventory": verification["final_inventory"][station],
    } for station in range(data["V"] + 1)])
    audit = {key: value for key, value in verification.items()
             if key not in {"routes", "operations", "final_inventory"}}
    audit.update({
        "archive_time_excluded_from_algorithm_time": True,
        "native_witness_preserved": True,
        "archive_materialization_seconds": time.perf_counter() - started,
    })
    r58.write_json(output / "solution_verification.json", audit)
    names = ("native_solution.json", "routes.csv", "operations.csv",
             "final_inventory.csv", "solution_verification.json")
    (output / "solution_sha256.txt").write_text(
        "".join(f"{r58.sha256_file(output / name)}  {name}\n" for name in names),
        encoding="utf-8")
    return {
        "scenario_id": scenario_id, "method": method,
        "package_path": r58.repo_path(output),
        "package_available": True, "verification_passed": True,
        "strict_certificate": package["strict_certificate"],
        "archive_seconds": audit["archive_materialization_seconds"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario-id", required=True)
    parser.add_argument("--method", choices=("k1_am_sf", "pgrb"), required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--executable-sha256", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    if args.verify_only:
        value = verify_native_result(args.scenario_id, args.result.resolve())
    else:
        value = archive_native_result(
            args.scenario_id, args.method, args.result.resolve(),
            args.source_commit, args.executable_sha256)
    print(json.dumps(value, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
