#!/usr/bin/env python3
"""Generate the deterministic, unopened Round 53 sealed V12 panel.

This is definition-only.  It calls the repository benchmark generator and
never invokes a solver or reads any Round 53 candidate result.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from generate_hard_exact_stress_instances import write_instance


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"
BASE_COMMIT = "44ed4057cc4d2ce67b86d623b57500e95cad5058"
DERIVATION_VERSION = "round53-sealed-v12-v1"
PANEL = "sealed_v12"
CONFIGURATIONS = (
    ("tight_T_2400", "tight_T", 2400.0),
    ("high_imbalance_3600", "high_imbalance", 3600.0),
    ("moderate_3600", "moderate", 3600.0),
)


def derived_seed(material: str) -> tuple[int, str]:
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return 10_000 + int(digest[:16], 16) % 1_900_000_000, digest


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    seen: set[int] = set()
    for m in (2, 3):
        for q in (20, 30):
            directory = ROOT / "reference" / "round53_sealed_v12" / f"V12_M{m}_Q{q}"
            directory.mkdir(parents=True, exist_ok=True)
            for ordinal, (configuration, stress, route_limit) in enumerate(
                    CONFIGURATIONS, start=1):
                material = (
                    f"{BASE_COMMIT}|{DERIVATION_VERSION}|{PANEL}|"
                    f"M{m}|Q{q}|{configuration}"
                )
                seed, digest = derived_seed(material)
                if seed in seen:
                    raise RuntimeError(f"deterministic seed collision: {seed}")
                seen.add(seed)
                instance_id = (
                    f"round53_sealed_v12_{configuration}_V12_M{m}_Q{q}_seed{seed}"
                )
                generated = write_instance(
                    directory / f"{instance_id}.txt", seed, stress,
                    route_limit, v=12, m=m, q=q)
                rows.append({
                    "panel": PANEL,
                    "ordinal_within_configuration_block": ordinal,
                    "instance_id": instance_id,
                    "input_path": generated["path"],
                    "input_sha256": generated["sha256"],
                    "seed": seed,
                    "seed_derivation_material": material,
                    "seed_derivation_sha256": digest,
                    "base_commit": BASE_COMMIT,
                    "derivation_version": DERIVATION_VERSION,
                    "V": 12,
                    "M": m,
                    "Q": q,
                    "T": int(route_limit),
                    "difficulty_configuration": configuration,
                    "generator_stress_type": stress,
                    "generator": (
                        "scripts/generate_hard_exact_stress_instances.py:write_instance"),
                    "selected_before_round53_candidate_results": True,
                    "runtime_filtering_forbidden": True,
                    "solver_results_sealed": True,
                    "extension_eligible": configuration == "tight_T_2400",
                })
    if len(rows) != 12 or len(seen) != 12:
        raise RuntimeError("sealed panel must contain twelve unique rows")
    fields = list(rows[0])
    with (OUT / "sealed_v12_instance_manifest.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "schema": "round53-sealed-v12-instance-manifest-v1",
        "panel": PANEL,
        "base_commit": BASE_COMMIT,
        "derivation_version": DERIVATION_VERSION,
        "generated_before_any_round53_candidate_performance_result": True,
        "solver_results_opened": False,
        "selection_rule": (
            "Cartesian product M in {2,3}, Q in {20,30}, and the three "
            "predeclared configurations; SHA-256-derived seeds; no filtering"),
        "opening_rule": (
            "only after final backend, K1 integration decision, source commit, "
            "official build, and executable SHA-256 are frozen"),
        "ordinary_process_cap_seconds": 3600,
        "extension_process_cap_seconds": 7200,
        "extension_rule": (
            "for each of the four tight_T_2400 instances, extend all three "
            "methods to 7200 seconds iff none certifies by 3600 seconds"),
        "row_count": len(rows),
        "counts": {"M2_Q20": 3, "M2_Q30": 3, "M3_Q20": 3,
                   "M3_Q30": 3, "tight_T_2400": 4,
                   "high_imbalance_3600": 4, "moderate_3600": 4},
        "seed_collision_count": 0,
        "rows": rows,
    }
    (OUT / "sealed_v12_instance_manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("generated and sealed 12 deterministic Round 53 V12 inputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
