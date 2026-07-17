#!/usr/bin/env python3
"""No-rerun Round 21 status-101 audit under Round 22 semantics."""

from __future__ import annotations

import csv
import gzip
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "gf_global_gini_tree_strict_flow_round" / "raw"
OUT = ROOT / "results" / "gf_global_gini_tree_unified_validation_round"


def read_json(path: Path) -> dict[str, Any]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def exact_zero_roundtrip(data: dict[str, Any], kind: str, param_id: int) -> bool:
    prefix = f"native_mip_{kind}_gap_"
    return (
        data.get(prefix + "param_id") == param_id
        and data.get(prefix + "requested") == 0
        and data.get(prefix + "set_return_code") == 0
        and data.get(prefix + "get_return_code") == 0
        and data.get(prefix + "effective_available") is True
        and data.get(prefix + "effective") == 0
    )


def first(data: dict[str, Any], *names: str) -> Any:
    for name in names:
        value = data.get(name)
        if value is not None:
            return value
    return ""


def verification(data: dict[str, Any]) -> bool:
    nested = data.get("verification") or {}
    return bool(
        data.get("verified_incumbent_original_problem_feasible") is True
        or (
            nested.get("feasible") is True
            and nested.get("routes_start_end_depot") is True
            and nested.get("station_disjoint") is True
            and nested.get("load_feasible") is True
            and nested.get("station_feasible") is True
            and nested.get("duration_feasible") is True
            and not nested.get("errors")
        )
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = sorted(SOURCE.glob("*.json")) + sorted(SOURCE.glob("*.json.gz"))
    rows: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    for path in paths:
        data = read_json(path)
        status = int(data.get("native_mip_status_code") or 0)
        if status != 101:
            continue
        native_objective = first(data, "native_mip_objective")
        native_bound = first(data, "native_mip_best_bound")
        recomputed = first(
            data, "verified_incumbent_objective",
            "independently_recomputed_original_objective")
        nested = data.get("verification") or {}
        if recomputed == "":
            recomputed = nested.get("objective", "")
        obj_minus_bound = (
            float(native_objective) - float(native_bound)
            if finite(native_objective) and finite(native_bound) else "")
        rec_minus_bound = (
            float(recomputed) - float(native_bound)
            if finite(recomputed) and finite(native_bound) else "")
        rec_minus_obj = (
            float(recomputed) - float(native_objective)
            if finite(recomputed) and finite(native_objective) else "")
        relative_ok = exact_zero_roundtrip(data, "relative", 2009)
        absolute_ok = exact_zero_roundtrip(data, "absolute", 2008)
        lifecycle_ok = data.get("native_mip_lifecycle_valid") is True
        verifier_ok = verification(data)
        # Round 21 did not bind a versioned complete-model audit to executable,
        # source commit, and a frozen production manifest.  Fingerprints are
        # useful evidence but cannot be silently treated as that new gate.
        historical_model_evidence = bool(
            data.get("global_gini_tree_root_model_fingerprint")
            or data.get("compact_bc_model_fingerprint"))
        other_authoritative_gates = (
            relative_ok and absolute_ok and lifecycle_ok and verifier_ok)
        classification = (
            "engineering_exact_candidate_requires_round22_model_gate"
            if other_authoritative_gates
            else "not_engineering_exact_missing_authoritative_gate")
        missing = []
        if not relative_ok:
            missing.append("relative_gap_roundtrip")
        if not absolute_ok:
            missing.append("absolute_gap_roundtrip")
        if not lifecycle_ok:
            missing.append("lifecycle")
        if not verifier_ok:
            missing.append("independent_verifier")
        missing.append("round22_versioned_model_correctness_binding")
        row = {
            "run_id": path.name.removesuffix(".gz").removesuffix(".json"),
            "historical_json": path.relative_to(ROOT).as_posix(),
            "round21_certificate_class": data.get("strict_certificate_class", ""),
            "round21_rejection_reason": data.get("strict_certificate_rejection_reason", ""),
            "native_status_code": status,
            "native_status_text": data.get("native_mip_status_text", ""),
            "relative_gap_parameter_roundtrip_valid": relative_ok,
            "relative_gap_readback": data.get("native_mip_relative_gap_effective", ""),
            "absolute_gap_parameter_roundtrip_valid": absolute_ok,
            "absolute_gap_readback": data.get("native_mip_absolute_gap_effective", ""),
            "lifecycle_valid": lifecycle_ok,
            "independent_verifier_passed": verifier_ok,
            "historical_model_fingerprint_evidence_available": historical_model_evidence,
            "round22_versioned_model_correctness_evidence_available": False,
            "native_objective": native_objective,
            "native_best_bound": native_bound,
            "recomputed_objective": recomputed,
            "native_objective_minus_native_bound": obj_minus_bound,
            "recomputed_objective_minus_native_bound": rec_minus_bound,
            "recomputed_objective_minus_native_objective": rec_minus_obj,
            "native_bound_inversion": finite(obj_minus_bound) and obj_minus_bound < 0,
            "recomputed_bound_inversion": finite(rec_minus_bound) and rec_minus_bound < 0,
            "round22_engineering_exact_classification": classification,
            "missing_authoritative_gates": "|".join(missing),
            "fresh_round22_rerun_required": True,
        }
        rows.append(row)
        diagnostics.append({
            "run_id": row["run_id"],
            "native_objective": native_objective,
            "native_best_bound": native_bound,
            "recomputed_objective": recomputed,
            "native_objective_minus_native_bound": obj_minus_bound,
            "recomputed_objective_minus_native_bound": rec_minus_bound,
            "recomputed_objective_minus_native_objective": rec_minus_obj,
            "round21_mapping_residual_available": data.get(
                "verified_incumbent_objective_residual_available", False),
            "round21_mapping_residual": data.get(
                "verified_incumbent_objective_residual", ""),
            "round22_diagnostic_class": (
                "mapping_residual_unavailable" if not finite(rec_minus_obj)
                else "mapping_residual_nominal" if abs(float(rec_minus_obj)) <=
                    1e-9 * max(1.0, abs(float(recomputed)), abs(float(native_objective)))
                else "mapping_residual_warning"),
            "certificate_gate": False,
        })

    def emit(path: Path, material: list[dict[str, Any]]) -> None:
        fields: list[str] = []
        for row in material:
            for key in row:
                if key not in fields:
                    fields.append(key)
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields or ["status"])
            writer.writeheader()
            writer.writerows(material)

    emit(OUT / "round21_certificate_semantic_migration.csv", rows)
    emit(OUT / "objective_mapping_diagnostics.csv", diagnostics)
    print(f"audited {len(rows)} Round 21 status-101 rows")


if __name__ == "__main__":
    main()
