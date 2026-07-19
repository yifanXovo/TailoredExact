#!/usr/bin/env python3
"""Independent Round 23 verifier and retained-root witness auditor.

This script deliberately uses only Python's standard library.  It does not
import or execute the production parser, Evaluator, HGA decoder, model writer,
or any retained verification flag.  Its LP audit consumes the retained CPLEX
LP text as an external mathematical object.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
INDEXED = re.compile(r"^([A-Za-z]+(?:_[A-Za-z]+)*)_(\d+(?:_\d+)*)$")


def numbers(text: str) -> list[float]:
    return [float(value) for value in re.findall(NUMBER, text)]


def bracket_vector(text: str, label: str) -> list[float]:
    match = re.search(rf"{re.escape(label)}\s*=\s*\[([\s\S]*?)\]", text)
    if not match:
        raise ValueError(f"missing vector {label}")
    return numbers(match.group(1))


@dataclass(frozen=True)
class Instance:
    V: int
    M: int
    capacities: list[int]
    initial: list[int]
    target: list[int]
    weights: list[float]
    minimum_ratio: list[float]
    vehicle_capacity: list[int]
    points: list[tuple[float, float]]
    distances: list[list[float]]


def parse_instance(path: Path) -> Instance:
    text = path.read_text(encoding="utf-8")
    first = text.splitlines()[0]
    head = numbers(first)
    if len(head) < 2:
        raise ValueError("invalid instance header")
    V, M = round(head[0]), round(head[1])
    capacity_match = re.search(r"\[([^]]+)\]", first)
    if not capacity_match:
        raise ValueError("missing vehicle capacities")
    vehicle_capacity = [round(v) for v in numbers(capacity_match.group(1))]
    point_payload = re.search(r"points\s*=\s*\[([\s\S]*?)\]", text)
    if not point_payload:
        raise ValueError("missing points")
    point_values = numbers(point_payload.group(1))
    points = list(zip(point_values[0::2], point_values[1::2]))
    if len(points) != V + 1:
        raise ValueError(f"expected {V + 1} points, got {len(points)}")
    distances = [[0.0] * (V + 1) for _ in range(V + 1)]
    for i, (xi, yi) in enumerate(points):
        for j, (xj, yj) in enumerate(points):
            if i != j:
                distances[i][j] = math.hypot(xi - xj, yi - yj) / 1.5
    weights = bracket_vector(text, "weights")
    # Match the documented input convention: legacy max-10 data are scaled;
    # this retained input has max weight one, so no scaling is activated.
    if max(weights[1:], default=0.0) == 10.0:
        weights = [weights[0], *[value / 10.0 for value in weights[1:]]]
    instance = Instance(
        V=V,
        M=M,
        capacities=[round(v) for v in bracket_vector(text, "capacities")],
        initial=[round(v) for v in bracket_vector(text, "initial")],
        target=[round(v) for v in bracket_vector(text, "target")],
        weights=weights,
        minimum_ratio=bracket_vector(text, "min_ratio"),
        vehicle_capacity=vehicle_capacity,
        points=points,
        distances=distances,
    )
    expected = V + 1
    for label, vector in (
        ("capacities", instance.capacities),
        ("initial", instance.initial),
        ("target", instance.target),
        ("weights", instance.weights),
        ("minimum_ratio", instance.minimum_ratio),
    ):
        if len(vector) != expected:
            raise ValueError(f"{label} has {len(vector)} entries, expected {expected}")
    if len(vehicle_capacity) != M:
        raise ValueError("vehicle-capacity count mismatch")
    return instance


def independent_verify(
    instance: Instance,
    routes: list[dict],
    *,
    total_time: float,
    pickup_time: float,
    drop_time: float,
    lam: float,
) -> dict:
    errors: list[str] = []
    station_owner: dict[int, int] = {}
    vehicle_owner: set[int] = set()
    final_inventory = list(instance.initial)
    route_audits: list[dict] = []
    for route_index, route in enumerate(routes):
        vehicle = route.get("vehicle")
        nodes = route.get("nodes")
        operations = route.get("operations")
        prefix = f"route[{route_index}]"
        if not isinstance(vehicle, int) or not 0 <= vehicle < instance.M:
            errors.append(f"{prefix}: invalid vehicle index {vehicle!r}")
            continue
        if vehicle in vehicle_owner:
            errors.append(f"{prefix}: duplicate vehicle {vehicle}")
        vehicle_owner.add(vehicle)
        if not isinstance(nodes, list) or len(nodes) < 2:
            errors.append(f"{prefix}: route has fewer than two nodes")
            continue
        if nodes[0] != 0:
            errors.append(f"{prefix}: route does not start at depot")
        if nodes[-1] != 0:
            errors.append(f"{prefix}: route does not end at depot")
        if any(not isinstance(node, int) or not 0 <= node <= instance.V for node in nodes):
            errors.append(f"{prefix}: invalid node index")
            continue
        interior = nodes[1:-1]
        if 0 in interior:
            errors.append(f"{prefix}: depot occurs inside route")
        if len(interior) != len(set(interior)):
            errors.append(f"{prefix}: repeated station")
        for station in interior:
            if station in station_owner:
                errors.append(
                    f"{prefix}: station {station} also assigned to vehicle "
                    f"{station_owner[station]}"
                )
            station_owner[station] = vehicle
        if not isinstance(operations, list):
            errors.append(f"{prefix}: operations are not a list")
            continue
        by_station: dict[int, list[dict]] = {}
        for operation in operations:
            station = operation.get("station")
            by_station.setdefault(station, []).append(operation)
        for station in interior:
            if len(by_station.get(station, [])) != 1:
                errors.append(
                    f"{prefix}: station {station} has "
                    f"{len(by_station.get(station, []))} operations"
                )
        for station in by_station:
            if station not in interior:
                errors.append(f"{prefix}: operation for unvisited station {station}")
        travel = sum(
            instance.distances[a][b] for a, b in zip(nodes[:-1], nodes[1:])
        )
        load = 0
        maximum_load = 0
        pickup_total = 0
        station_drop_total = 0
        load_trace: list[dict] = []
        for station in interior:
            matches = by_station.get(station, [])
            if len(matches) != 1:
                continue
            operation = matches[0]
            pickup = operation.get("pickup")
            drop = operation.get("drop")
            if not isinstance(pickup, int) or not isinstance(drop, int):
                errors.append(f"{prefix}: noninteger operation at station {station}")
                continue
            if pickup < 0 or drop < 0:
                errors.append(f"{prefix}: negative operation at station {station}")
            if pickup > 0 and drop > 0:
                errors.append(f"{prefix}: pickup and drop both positive at station {station}")
            if pickup == 0 and drop == 0:
                errors.append(f"{prefix}: zero operation at visited station {station}")
            load += pickup - drop
            maximum_load = max(maximum_load, load)
            pickup_total += pickup
            station_drop_total += drop
            final_inventory[station] += drop - pickup
            load_trace.append({"station": station, "load_after": load})
            if load < 0 or load > instance.vehicle_capacity[vehicle]:
                errors.append(
                    f"{prefix}: load {load} outside [0,{instance.vehicle_capacity[vehicle]}] "
                    f"after station {station}"
                )
        depot_unload = load
        pickup_handling = pickup_time * pickup_total
        station_drop_handling = drop_time * station_drop_total
        depot_unload_handling = drop_time * depot_unload
        duration = travel + pickup_handling + station_drop_handling + depot_unload_handling
        if duration > total_time + 1e-7:
            errors.append(f"{prefix}: duration {duration:.17g} exceeds {total_time:.17g}")
        route_audits.append(
            {
                "vehicle": vehicle,
                "travel_time": travel,
                "pickup_handling_time": pickup_handling,
                "station_drop_handling_time": station_drop_handling,
                "depot_unload_handling_time": depot_unload_handling,
                "duration": duration,
                "final_load_before_depot_unload": depot_unload,
                "maximum_load": maximum_load,
                "load_trace": load_trace,
            }
        )
    for station in range(1, instance.V + 1):
        if not 0 <= final_inventory[station] <= instance.capacities[station]:
            errors.append(
                f"station {station}: final inventory {final_inventory[station]} "
                f"outside [0,{instance.capacities[station]}]"
            )
    ratios = [0.0] + [
        final_inventory[i] / instance.target[i] for i in range(1, instance.V + 1)
    ]
    deviations = [0.0] + [abs(ratios[i] - 1.0) for i in range(1, instance.V + 1)]
    pairwise = {
        f"{i},{j}": abs(ratios[i] - ratios[j])
        for i in range(1, instance.V + 1)
        for j in range(i + 1, instance.V + 1)
    }
    S = math.fsum(ratios[1:])
    H = math.fsum(pairwise.values())
    G = H / (instance.V * S) if S > 0.0 else 0.0
    P = math.fsum(
        instance.weights[i] * deviations[i] for i in range(1, instance.V + 1)
    )
    objective = G + lam * P
    return {
        "classification": (
            "independently valid original-problem solution"
            if not errors
            else "independently invalid"
        ),
        "valid": not errors,
        "errors": errors,
        "final_inventory": final_inventory,
        "ratios": ratios,
        "deviations": deviations,
        "pairwise_absolute_ratio_differences": pairwise,
        "S": S,
        "H": H,
        "G": G,
        "P": P,
        "lambda": lam,
        "objective": objective,
        "route_audits": route_audits,
    }


def symmetry_canonical_routes(instance: Instance, routes: list[dict]) -> list[dict]:
    """Relabel interchangeable vehicles to satisfy visit-count ordering.

    The retained compact LP contains the valid symmetry breakers
    |visits(k)| >= |visits(k+1)|.  Vehicle identity is immaterial only within
    equal-capacity classes, so this routine never moves a route between
    unequal-capacity vehicles.
    """
    by_vehicle = {route["vehicle"]: route for route in routes}
    relabeled: list[dict] = []
    capacity_groups: dict[int, list[int]] = {}
    for vehicle, capacity in enumerate(instance.vehicle_capacity):
        capacity_groups.setdefault(capacity, []).append(vehicle)
    for _, vehicles in sorted(capacity_groups.items()):
        group_routes = [by_vehicle[vehicle] for vehicle in vehicles]
        group_routes.sort(
            key=lambda route: (
                -len(route["nodes"][1:-1]),
                tuple(route["nodes"]),
                route["vehicle"],
            )
        )
        for target_vehicle, route in zip(sorted(vehicles), group_routes):
            copy = json.loads(json.dumps(route))
            copy["vehicle"] = target_vehicle
            relabeled.append(copy)
    return sorted(relabeled, key=lambda route: route["vehicle"])


def semantic_values(instance: Instance, routes: list[dict], audit: dict) -> dict[str, float]:
    values: dict[str, float] = {}
    used_arc: set[tuple[int, int, int]] = set()
    operations: dict[tuple[int, int], tuple[int, int, int, int]] = {}
    for route in routes:
        vehicle = route["vehicle"]
        nodes = route["nodes"]
        op_by_station = {op["station"]: op for op in route["operations"]}
        load = 0
        for position, (origin, destination) in enumerate(zip(nodes[:-1], nodes[1:]), 1):
            used_arc.add((vehicle, origin, destination))
            if destination != 0:
                operation = op_by_station[destination]
                load += operation["pickup"] - operation["drop"]
                operations[(vehicle, destination)] = (
                    operation["pickup"], operation["drop"], load, position
                )
    for vehicle in range(instance.M):
        for origin in range(instance.V + 1):
            for destination in range(instance.V + 1):
                if origin != destination:
                    values[f"x_{vehicle}_{origin}_{destination}"] = float(
                        (vehicle, origin, destination) in used_arc
                    )
        for station in range(1, instance.V + 1):
            pickup, drop, load, _ = operations.get((vehicle, station), (0, 0, 0, 0))
            values[f"z_{vehicle}_{station}"] = float((vehicle, station) in operations)
            values[f"mode_{vehicle}_{station}"] = float(pickup > 0)
            values[f"p_{vehicle}_{station}"] = float(pickup)
            values[f"d_{vehicle}_{station}"] = float(drop)
            values[f"load_{vehicle}_{station}"] = float(load)
    values["G"] = audit["G"]
    values["W_SP"] = audit["S"] * audit["P"]
    for station in range(1, instance.V + 1):
        values[f"Y_{station}"] = float(audit["final_inventory"][station])
        values[f"r_{station}"] = audit["ratios"][station]
        values[f"e_{station}"] = audit["deviations"][station]
    for key, value in audit["pairwise_absolute_ratio_differences"].items():
        i, j = key.split(",")
        values[f"h_{i}_{j}"] = value
    return values


def complete_values(instance: Instance, routes: list[dict], audit: dict) -> dict[str, float]:
    values = semantic_values(instance, routes, audit)
    route_positions: dict[tuple[int, int], int] = {}
    route_arcs: dict[tuple[int, int, int], float] = {}
    for route in routes:
        vehicle = route["vehicle"]
        nodes = route["nodes"]
        arc_count = len(nodes) - 1
        for position, (origin, destination) in enumerate(zip(nodes[:-1], nodes[1:]), 1):
            route_arcs[(vehicle, origin, destination)] = float(arc_count - position)
            if destination != 0:
                route_positions[(vehicle, destination)] = position
    for vehicle in range(instance.M):
        for origin in range(instance.V + 1):
            for destination in range(instance.V + 1):
                if origin != destination:
                    values[f"conn_{vehicle}_{origin}_{destination}"] = route_arcs.get(
                        (vehicle, origin, destination), 0.0
                    )
        for station in range(1, instance.V + 1):
            values[f"ord_{vehicle}_{station}"] = float(
                route_positions.get((vehicle, station), 0)
            )
    for station in range(1, instance.V + 1):
        inventory = audit["final_inventory"][station]
        bit_count = max(1, math.ceil(math.log2(instance.capacities[station] + 1)))
        for bit in range(bit_count):
            on = float((inventory >> bit) & 1)
            values[f"bit_{station}_{bit}"] = on
            values[f"prod_{station}_{bit}"] = audit["G"] * on
        values[f"zprod_{station}"] = audit["G"] * inventory
    return values


def read_lp(path: Path) -> str:
    if path.suffix == ".gz":
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            return handle.read()
    return path.read_text(encoding="utf-8")


def lp_rows(text: str) -> list[tuple[int, str, str, str, float]]:
    subject = text.split("Subject To", 1)[1].split("Bounds", 1)[0]
    rows = []
    for index, line in enumerate(subject.splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        name, body = stripped.split(":", 1)
        match = re.match(r"([\s\S]*?)\s*(<=|>=|=)\s*(" + NUMBER + r")\s*$", body)
        if not match:
            raise ValueError(f"cannot parse LP row {name}: {body}")
        rows.append((index, name, match.group(1), match.group(2), float(match.group(3))))
    return rows


def expression_terms(expression: str) -> list[tuple[str, float]]:
    term_pattern = re.compile(
        r"(?P<sign>[+-]?)\s*(?:(?P<coef>(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s+)?"
        r"(?P<name>[A-Za-z][A-Za-z0-9_.]*)"
    )
    terms = []
    position = 0
    for match in term_pattern.finditer(expression):
        if expression[position:match.start()].strip():
            raise ValueError(f"unparsed expression fragment: {expression[position:match.start()]!r}")
        coefficient = float(match.group("coef")) if match.group("coef") else 1.0
        if match.group("sign") == "-":
            coefficient = -coefficient
        terms.append((match.group("name"), coefficient))
        position = match.end()
    if expression[position:].strip():
        raise ValueError(f"unparsed expression tail: {expression[position:]!r}")
    return terms


def lp_columns(text: str) -> set[str]:
    columns: set[str] = set()
    objective = text.split("Minimize", 1)[1].split("Subject To", 1)[0]
    objective = objective.split(":", 1)[1]
    columns.update(name for name, _ in expression_terms(objective))
    for _, _, expression, _, _ in lp_rows(text):
        columns.update(name for name, _ in expression_terms(expression))
    return columns


def parse_domains(text: str, columns: set[str]) -> tuple[dict[str, float], dict[str, float], set[str]]:
    lower = {name: 0.0 for name in columns}
    upper = {name: math.inf for name in columns}
    after_bounds = text.split("Bounds", 1)[1]
    section_markers = [
        position
        for marker in ("\nBinaries\n", "\nGenerals\n", "\nGeneral\n")
        if (position := after_bounds.find(marker)) >= 0
    ]
    if not section_markers:
        raise ValueError("LP integer-variable sections not found")
    bounds_body = after_bounds[: min(section_markers)]
    for line in bounds_body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.fullmatch(rf"({NUMBER})\s*<=\s*(\S+)\s*<=\s*({NUMBER})", stripped)
        if match:
            lower[match.group(2)] = float(match.group(1))
            upper[match.group(2)] = float(match.group(3))
            continue
        match = re.fullmatch(rf"(\S+)\s+free", stripped)
        if match:
            lower[match.group(1)] = -math.inf
            upper[match.group(1)] = math.inf
            continue
        raise ValueError(f"unsupported LP bound: {stripped}")
    binary_match = re.search(r"\nBinaries\n([\s\S]*?)(?=\n(?:Generals?|End)\n)", text)
    general_match = re.search(r"\nGenerals?\n([\s\S]*?)(?=\n(?:Binaries|End)\n)", text)
    binaries = set(binary_match.group(1).split()) if binary_match else set()
    generals = set(general_match.group(1).split()) if general_match else set()
    for name in binaries:
        lower[name] = max(lower.get(name, 0.0), 0.0)
        upper[name] = min(upper.get(name, math.inf), 1.0)
    return lower, upper, binaries | generals


def complete_extension_audit(
    lp_text: str, values: dict[str, float]
) -> tuple[list[dict], list[dict], list[str]]:
    columns = lp_columns(lp_text)
    lower, upper, integer = parse_domains(lp_text, columns)
    unsupported = sorted(columns - values.keys())
    column_rows = []
    for name in sorted(columns):
        value = values.get(name)
        mapped = value is not None
        lb = lower.get(name, 0.0)
        ub = upper.get(name, math.inf)
        lb_ok = mapped and value >= lb - 1e-9 * (1.0 + abs(lb))
        ub_ok = mapped and value <= ub + 1e-9 * (1.0 + abs(ub))
        int_ok = mapped and (name not in integer or abs(value - round(value)) <= 1e-9)
        column_rows.append(
            {
                "column": name,
                "mapped": mapped,
                "value": value if mapped else "",
                "lower_bound": lb,
                "upper_bound": ub,
                "integer": name in integer,
                "lower_bound_satisfied": lb_ok,
                "upper_bound_satisfied": ub_ok,
                "integrality_satisfied": int_ok,
            }
        )
    row_rows = []
    if not unsupported:
        for row_index, name, expression, sense, rhs in lp_rows(lp_text):
            terms = expression_terms(expression)
            products = [coefficient * values[column] for column, coefficient in terms]
            activity = math.fsum(products)
            scale = 1.0 + abs(rhs) + math.fsum(abs(product) for product in products)
            if sense == "<=":
                violation = max(0.0, activity - rhs)
            elif sense == ">=":
                violation = max(0.0, rhs - activity)
            else:
                violation = abs(activity - rhs)
            row_rows.append(
                {
                    "row_index": row_index,
                    "row_name": name,
                    "sense": sense,
                    "rhs": rhs,
                    "activity": activity,
                    "absolute_violation": violation,
                    "scaled_violation": violation / scale,
                    "nonzeros": json.dumps(
                        [
                            {"column": column, "coefficient": coefficient, "value": values[column]}
                            for column, coefficient in terms
                        ],
                        separators=(",", ":"),
                    ),
                }
            )
    return column_rows, row_rows, unsupported


def inject_fix_rows(lp_text: str, values: dict[str, float], columns: Iterable[str]) -> str:
    rows = []
    for sequence, name in enumerate(sorted(set(columns)), 1):
        if name not in values:
            raise ValueError(f"semantic fixation column is unmapped: {name}")
        rows.append(f" round23_fix_{sequence}: {name} = {values[name]:.17g}")
    marker = "\nBounds\n"
    if marker not in lp_text:
        raise ValueError("LP Bounds marker not found")
    return lp_text.replace(marker, "\n" + "\n".join(rows) + marker, 1)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError(f"refusing to create empty CSV {path}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", type=Path, required=True)
    parser.add_argument("--hga-json", type=Path, required=True)
    parser.add_argument("--plain-json", type=Path, required=True)
    parser.add_argument("--root-lp", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--partial-lp", type=Path, required=True)
    args = parser.parse_args()

    instance = parse_instance(args.instance)
    hga_retained = json.loads(args.hga_json.read_text(encoding="utf-8"))
    plain_retained = json.loads(args.plain_json.read_text(encoding="utf-8"))
    common = {"total_time": 3600.0, "pickup_time": 60.0, "drop_time": 60.0, "lam": 0.15}
    hga = independent_verify(instance, hga_retained["routes"], **common)
    plain = independent_verify(instance, plain_retained["routes"], **common)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    binding = {
        "instance_path": str(args.instance.resolve()),
        "instance_sha256": sha256(args.instance),
        "V": instance.V,
        "M": instance.M,
        "vehicle_capacities": instance.vehicle_capacity,
        "station_capacities": instance.capacities,
        "initial_inventories": instance.initial,
        "target_inventories": instance.target,
        "weights": instance.weights,
        "minimum_ratios": instance.minimum_ratio,
        "distance_construction": "Euclidean point distance divided by 1.5",
        "pickup_time": common["pickup_time"],
        "drop_time": common["drop_time"],
        "T": common["total_time"],
        "lambda": common["lam"],
    }
    (args.out_dir / "moderate4301_instance_binding.json").write_text(
        json.dumps(binding, indent=2) + "\n", encoding="utf-8"
    )
    for label, audit, retained in (
        ("hga", hga, hga_retained),
        ("plain", plain, plain_retained),
    ):
        payload = {
            "source_json": str((args.hga_json if label == "hga" else args.plain_json).resolve()),
            "retained_fields_for_comparison_only": {
                "objective": retained.get("objective"),
                "G": retained.get("G"),
                "P": retained.get("P"),
                "verification": retained.get("verification"),
            },
            "routes": retained["routes"],
            "independent_verification": audit,
        }
        (args.out_dir / f"moderate4301_{label}_witness.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )
    comparison = {
        "independence_contract": [
            "standard-library parser only",
            "no production Evaluator",
            "no HGA decoder",
            "no production model writer",
            "no retained verification boolean used for classification",
        ],
        "hga": hga,
        "plain": plain,
        "retained_comparison": {
            "hga": {
                key: hga_retained.get(key) for key in ("G", "P", "objective", "upper_bound")
            },
            "plain": {
                key: plain_retained.get(key) for key in ("G", "P", "objective", "upper_bound")
            },
        },
    }
    (args.out_dir / "moderate4301_independent_verification.json").write_text(
        json.dumps(comparison, indent=2) + "\n", encoding="utf-8"
    )

    lp_text = read_lp(args.root_lp)
    original_routes = hga_retained["routes"]
    canonical_routes = symmetry_canonical_routes(instance, original_routes)
    original_semantic = semantic_values(instance, original_routes, hga)
    semantic = semantic_values(instance, canonical_routes, hga)
    complete = complete_values(instance, canonical_routes, hga)
    columns = lp_columns(lp_text)
    partial_columns = [
        name
        for name in columns
        if name in semantic and not name.startswith(("conn_", "ord_", "bit_", "prod_", "zprod_"))
    ]
    args.partial_lp.parent.mkdir(parents=True, exist_ok=True)
    original_label_lp = args.partial_lp.with_name(
        args.partial_lp.stem + "_original_labels" + args.partial_lp.suffix
    )
    original_label_lp.write_text(
        inject_fix_rows(lp_text, original_semantic, partial_columns), encoding="utf-8"
    )
    args.partial_lp.write_text(
        inject_fix_rows(lp_text, semantic, partial_columns), encoding="utf-8"
    )
    partial_rows = []
    for name in sorted(partial_columns):
        partial_rows.append(
            {
                "fixation_case": "retained_labels",
                "column": name,
                "fixed_value": original_semantic[name],
                "fixation_scope": "unambiguous_original_semantics",
            }
        )
        partial_rows.append(
            {
                "fixation_case": "symmetry_canonical_equal_capacity_labels",
                "column": name,
                "fixed_value": semantic[name],
                "fixation_scope": "unambiguous_original_semantics_modulo_valid_vehicle_symmetry",
            }
        )
    write_csv(args.out_dir / "moderate4301_root_partial_fix_audit.csv", partial_rows)
    column_rows, row_rows, unsupported = complete_extension_audit(lp_text, complete)
    write_csv(args.out_dir / "moderate4301_column_mapping_audit.csv", column_rows)
    write_csv(args.out_dir / "moderate4301_root_complete_extension_audit.csv", row_rows)
    summary = {
        "root_lp": str(args.root_lp.resolve()),
        "root_lp_sha256": sha256(args.root_lp),
        "partial_fix_lp": str(args.partial_lp.resolve()),
        "original_label_partial_fix_lp": str(original_label_lp.resolve()),
        "partial_fix_count": len(partial_columns),
        "vehicle_relabeling": [
            {
                "retained_vehicle": original["vehicle"],
                "canonical_vehicle": canonical["vehicle"],
                "retained_nodes": original["nodes"],
                "canonical_nodes": canonical["nodes"],
            }
            for original, canonical in zip(
                sorted(original_routes, key=lambda route: route["vehicle"]),
                canonical_routes,
            )
        ],
        "partial_fix_leaves_free": [
            "connectivity flow",
            "order variables",
            "bit variables",
            "product variables",
            "other auxiliary variables not in the semantic fixation map",
        ],
        "complete_extension_unsupported_columns": unsupported,
        "complete_extension_column_failures": sum(
            not (
                row["mapped"]
                and row["lower_bound_satisfied"]
                and row["upper_bound_satisfied"]
                and row["integrality_satisfied"]
            )
            for row in column_rows
        ),
        "complete_extension_violated_rows_at_1e_9": sum(
            row["scaled_violation"] > 1e-9 for row in row_rows
        ),
        "maximum_scaled_row_violation": max(
            (row["scaled_violation"] for row in row_rows), default=None
        ),
    }
    (args.out_dir / "moderate4301_root_audit_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
