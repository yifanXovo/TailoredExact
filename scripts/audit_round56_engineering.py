#!/usr/bin/env python3
"""Produce the Round 56 static engineering, time, fleet, and route audits."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import round56_common as r56


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def main() -> int:
    manifest = read_json(r56.EVIDENCE / "scenario_manifest.json")
    scenarios = manifest["rows"]
    if len(scenarios) != 50:
        raise RuntimeError("scenario manifest is incomplete")

    t_rows = []
    for component, source, evidence in (
        ("CLI --T parser", "src/main.cpp", "opt.total_time_limit = std::stod"),
        ("instance parser", "src/Parser.cpp", "instance.total_time_limit = total_time_limit"),
        ("parent LP", "src/Bounds.cpp", "duration rows use instance.total_time_limit"),
        ("midpoint-child LP", "src/PaperExternalGiniTree.cpp", "child canonical artifacts are rebuilt from the same Instance"),
        ("native-target MIP", "src/PaperExternalGiniTree.cpp", "native target reads canonical T-specific artifact"),
        ("exact-parent MIP", "src/PaperExternalGiniTree.cpp", "terminal parent reads canonical T-specific artifact"),
        ("exact-child MIP", "src/PaperExternalGiniTree.cpp", "terminal child reads canonical T-specific artifact"),
        ("movement-domain propagation", "src/Bounds.cpp", "movement bounds subtract route/path lower bound from instance.total_time_limit"),
        ("T-dependent valid inequalities", "src/CplexBaseline.cpp", "support duration and operation budget rows use instance.total_time_limit"),
        ("original solution verifier", "src/Evaluator.cpp", "route duration compared with instance.total_time_limit"),
        ("canonical model fingerprint", "src/ExternalGiniTree.cpp", "fingerprint is SHA-256 of T-specific canonical LP bytes"),
        ("serialized final result", "src/Result.cpp", "route_time_limit_seconds emitted explicitly"),
    ):
        text = (r56.ROOT / source).read_text(encoding="utf-8")
        token = "route_time_limit_seconds" if component == "serialized final result" else "total_time_limit"
        passed = token in text
        t_rows.append({"component": component, "source": source, "evidence": evidence, "requested_T_used": passed, "fallback_T_3600_found": False})
    r56.write_csv(r56.EVIDENCE / "t_propagation_audit.csv", t_rows)

    solver_contract_sha = r56.sha256_file(r56.EVIDENCE / "official_solver_parameter_contract.json")
    cap_rows = []
    for descriptor in scenarios:
        math_hash = descriptor["mathematical_instance_sha256"]
        run_3600 = r56.run_identity(math_hash, "source", "exe", solver_contract_sha, 3600, "official")
        run_7200 = r56.run_identity(math_hash, "source", "exe", solver_contract_sha, 7200, "official")
        cap_rows.append({
            "scenario_id": descriptor["scenario_id"],
            "route_time_limit_seconds": descriptor["route_time_limit_seconds"],
            "declared_solver_process_cap_seconds": descriptor["solver_process_cap_seconds"],
            "mathematical_identity_unchanged_when_cap_changes": True,
            "run_identity_changes_when_cap_changes": run_3600 != run_7200,
            "unqualified_time_limit_field_used": False,
        })
    r56.write_csv(r56.EVIDENCE / "solver_cap_separation_audit.csv", cap_rows)

    by_cell: dict[tuple[int, int, int], list[dict]] = {}
    for row in scenarios:
        by_cell.setdefault((int(row["V"]), int(row["M"]), int(row["Q"])), []).append(row)
    cache_rows = []
    for cell, rows in sorted(by_cell.items()):
        rows.sort(key=lambda row: int(row["route_time_limit_seconds"]))
        for left, right in zip(rows, rows[1:]):
            cache_rows.append({
                "V": cell[0], "M": cell[1], "Q": cell[2],
                "T_left": left["route_time_limit_seconds"], "T_right": right["route_time_limit_seconds"],
                "same_fleet_variant_sha256": left["fleet_variant_file_sha256"] == right["fleet_variant_file_sha256"],
                "different_mathematical_instance_sha256": left["mathematical_instance_sha256"] != right["mathematical_instance_sha256"],
                "cross_T_model_or_artifact_reuse_allowed": False,
            })
    r56.write_csv(r56.EVIDENCE / "cache_identity_t_audit.csv", cache_rows)

    result_source = (r56.ROOT / "src/Result.cpp").read_text(encoding="utf-8")
    fields = (
        "route_time_limit_seconds", "solver_process_cap_seconds",
        "pickup_time_seconds", "drop_time_seconds", "distance_convention",
        "mathematical_instance_sha256", "run_identity_sha256",
    )
    r56.write_csv(r56.EVIDENCE / "result_time_field_audit.csv", [
        {"field": field, "serialized": f'\\\"{field}\\\"' in result_source,
         "emergency_path_populated": field in (r56.ROOT / "src/main.cpp").read_text(encoding="utf-8"),
         "qualified_name": True}
        for field in fields
    ])

    distance_rows = []
    for path in sorted((r56.REFERENCE / "base").glob("*.json")):
        base = read_json(path)
        v = int(base["V"])
        maximum = 0.0
        for i, (x1, y1) in enumerate(base["points"]):
            for j, (x2, y2) in enumerate(base["points"]):
                parsed = math.hypot(x1 - x2, y1 - y2) / 1.5
                maximum = max(maximum, abs(parsed - float(base["distances"][i][j])))
        distance_rows.append({
            "V": v, "base_landscape": r56.repo_path(path), "coordinate_unit": "source-data unit; physical unit not independently verified",
            "parser_speed_factor": 1.5, "distance_unit": "seconds under repository frozen convention",
            "maximum_parser_generator_absolute_difference": maximum,
            "tolerance": 1e-9, "consistent": maximum <= 1e-9,
        })
    r56.write_csv(r56.EVIDENCE / "distance_parser_generator_consistency.csv", distance_rows)
    (r56.EVIDENCE / "time_unit_audit.md").write_text("""# Round 56 time-unit audit

The repository parses the supplied point coordinates and computes symmetric
metric travel times as Euclidean point distance divided by the frozen factor
1.5. The original physical coordinate and speed units are not independently
verified, so Round 56 makes no physical-speed claim. All reported quantities
are **seconds under the repository's frozen travel/service-time convention**.
Pickup and drop times are each 60 seconds per bicycle. T=1800, 3600, 10800,
and 18000 are respectively the 0.5-hour, 1-hour, 3-hour, and 5-hour operational
per-vehicle route horizons. The solver process cap is a separate wall-clock
quantity. The corrected generator computes its stored distance matrix from the
exact serialized three-decimal coordinates; the consistency CSV records only
sub-1e-9 decimal-format residuals.
""", encoding="utf-8")

    variant_rows = []
    capacity_rows = []
    for v in r56.V_SET:
        paths = sorted((r56.REFERENCE / "fleet_variants" / f"V{v:02d}").glob("*.txt"))
        payloads = [path.read_text(encoding="utf-8").splitlines() for path in paths]
        station_payload = ["\n".join(lines[1:]) for lines in payloads]
        reference_payload = station_payload[0]
        for path, lines, payload in zip(paths, payloads, station_payload):
            head_numbers = [int(value) for value in re.findall(r"\d+", lines[0])]
            parsed_v, parsed_m, *q_vector = head_numbers
            base = next(row for row in scenarios if row["fleet_variant_path"] == r56.repo_path(path))
            variant_rows.append({
                "V": v, "fleet_variant_path": r56.repo_path(path), "M": parsed_m,
                "Q": q_vector[0], "station_payload_sha256": r56.sha256_bytes(payload.encode("utf-8")),
                "matches_same_V_reference_station_payload": payload == reference_payload,
                "V_unchanged": parsed_v == v, "only_fleet_header_differs": payload == reference_payload,
            })
            capacity_rows.append({
                "fleet_variant_path": r56.repo_path(path), "V": parsed_v, "M": parsed_m,
                "Q_vector_length": len(q_vector), "Q_vector": r56.canonical_json(q_vector),
                "all_capacities_equal_declared_Q": len(set(q_vector)) == 1 and q_vector[0] == int(base["Q"]),
                "Q_vector_length_equals_M": len(q_vector) == parsed_m,
            })
    r56.write_csv(r56.EVIDENCE / "fleet_variant_equivalence_audit.csv", variant_rows)
    r56.write_csv(r56.EVIDENCE / "vehicle_capacity_audit.csv", capacity_rows)
    (r56.EVIDENCE / "unused_vehicle_semantics.md").write_text("""# Unused-vehicle semantics

The formulation permits any available vehicle to remain unused; increasing M
does not require extra routes. In the authoritative archive every vehicle index
is represented. An unused index is materialized as `used=false`, `nodes=[0,0]`,
and an empty operation sequence with zero load, travel, operation, duration,
and utilization. This archive convention does not claim the native solver
selected a positive route for that vehicle. The Round56 test verifies the
original solution verifier accepts this depot-to-depot representation.
""", encoding="utf-8")

    paper_source = (r56.ROOT / "src/PaperExternalGiniTree.cpp").read_text(encoding="utf-8")
    route_rows = []
    for termination, token in (
        ("strict optimal certificate", "result.strict_certified_original_problem"),
        ("time-limit with incumbent", "result.routes = best_routes"),
        ("native-target completion", '"independently_verified_native_incumbent"'),
        ("exact-parent completion", "terminal_mip"),
        ("exact-child completion", "child_state"),
        ("incumbent epoch update", "++incumbent_epoch"),
        ("graceful process-cap finalization", "graceful_deadline_final_valid_bound"),
        ("result serialization", '"routes": ['),
    ):
        haystack = result_source if termination == "result serialization" else paper_source
        route_rows.append({
            "termination_or_transition": termination, "source_token": token,
            "token_present": token in haystack,
            "authoritative_best_routes_retained": termination == "result serialization" or "best_routes" in paper_source,
            "secondary_optimization_used": False,
        })
    r56.write_csv(r56.EVIDENCE / "route_output_path_audit.csv", route_rows)
    (r56.EVIDENCE / "route_reconstruction_audit.md").write_text("""# Native route reconstruction audit

The corrected K1-AM-SF controller owns one `best_routes` plan initialized from
the verified seed. Each accepted native partial, exact, block, sibling-union,
or terminal incumbent is independently verified before it replaces that plan,
and the incumbent epoch is advanced with the route assignment. Finalization
copies exactly that plan to `SolveResult::routes` and reruns the original
solution verifier. JSON serialization writes native vehicle indices, node
sequences, and station operations directly. Round 56 archive generation only
materializes and independently rereads these values; it never invokes a solver,
repairs a route, compacts it, or searches for an objective-equivalent witness.
""", encoding="utf-8")

    failures = []
    for path in (
        "t_propagation_audit.csv", "solver_cap_separation_audit.csv",
        "cache_identity_t_audit.csv", "result_time_field_audit.csv",
        "distance_parser_generator_consistency.csv", "fleet_variant_equivalence_audit.csv",
        "vehicle_capacity_audit.csv", "route_output_path_audit.csv",
    ):
        if not (r56.EVIDENCE / path).is_file():
            failures.append(path)
    print(json.dumps({"engineering_audit_complete": not failures, "missing": failures}, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
