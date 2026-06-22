#!/usr/bin/env python3
"""Convert simple external/HGA incumbent route files to ExactEBRP route_json.

Supported inputs:
  route_json: {"routes":[{"vehicle":0,"nodes":[0,1,0],"operations":[...]}]}
  csv:        vehicle,order,station,pickup,drop
  legacy_text: one stop per line: vehicle station pickup drop

The converter does not validate feasibility. ExactEBRP must verify the output
before using it as an incumbent upper bound.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def normalize_routes(routes):
    normalized = []
    for route in routes:
        vehicle = int(route.get("vehicle", len(normalized)))
        nodes = [int(x) for x in route.get("nodes", [])]
        if not nodes:
            nodes = [0, 0]
        if nodes[0] != 0:
            nodes.insert(0, 0)
        if nodes[-1] != 0:
            nodes.append(0)
        operations = []
        for op in route.get("operations", []):
            station = int(op.get("station", 0))
            pickup = int(op.get("pickup", 0))
            drop = int(op.get("drop", 0))
            if station > 0 and (pickup > 0 or drop > 0):
                operations.append(
                    {"station": station, "pickup": pickup, "drop": drop}
                )
        normalized.append(
            {"vehicle": vehicle, "nodes": nodes, "operations": operations}
        )
    return {"routes": normalized}


def read_route_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return normalize_routes(json.load(handle).get("routes", []))


def read_csv(path: Path):
    by_vehicle = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"vehicle", "order", "station", "pickup", "drop"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing columns: {sorted(missing)}")
        for row in reader:
            vehicle = int(row["vehicle"])
            by_vehicle.setdefault(vehicle, []).append(
                (
                    int(row["order"]),
                    int(row["station"]),
                    int(row["pickup"]),
                    int(row["drop"]),
                )
            )
    routes = []
    for vehicle, stops in sorted(by_vehicle.items()):
        stops.sort()
        nodes = [0]
        operations = []
        for _, station, pickup, drop in stops:
            if station <= 0:
                continue
            nodes.append(station)
            if pickup > 0 or drop > 0:
                operations.append(
                    {"station": station, "pickup": pickup, "drop": drop}
                )
        nodes.append(0)
        routes.append({"vehicle": vehicle, "nodes": nodes, "operations": operations})
    return normalize_routes(routes)


def read_legacy_text(path: Path):
    by_vehicle = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            parts = stripped.replace(",", " ").split()
            if len(parts) < 4:
                continue
            vehicle, station, pickup, drop = map(int, parts[:4])
            by_vehicle.setdefault(vehicle, []).append((station, pickup, drop))
    routes = []
    for vehicle, stops in sorted(by_vehicle.items()):
        nodes = [0]
        operations = []
        for station, pickup, drop in stops:
            if station <= 0:
                continue
            nodes.append(station)
            if pickup > 0 or drop > 0:
                operations.append(
                    {"station": station, "pickup": pickup, "drop": drop}
                )
        nodes.append(0)
        routes.append({"vehicle": vehicle, "nodes": nodes, "operations": operations})
    return normalize_routes(routes)


def infer_format(path: Path, explicit: str):
    if explicit != "auto":
        return explicit
    if path.suffix.lower() == ".csv":
        return "csv"
    if path.suffix.lower() in {".json", ".route_json"}:
        return "route_json"
    return "legacy_text"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--format",
        choices=["auto", "route_json", "csv", "legacy_text"],
        default="auto",
    )
    args = parser.parse_args()
    input_path = Path(args.input)
    fmt = infer_format(input_path, args.format)
    if fmt == "route_json":
        converted = read_route_json(input_path)
    elif fmt == "csv":
        converted = read_csv(input_path)
    else:
        converted = read_legacy_text(input_path)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(converted, handle, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    main()
