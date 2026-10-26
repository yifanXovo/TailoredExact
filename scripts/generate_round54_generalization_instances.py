#!/usr/bin/env python3
"""Generate the deterministic unopened Round 54 V12/V20/V50 panel.

Definition-only: this script invokes the repository instance generator but
never invokes a solver or reads any Round 54 candidate result.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from generate_hard_exact_stress_instances import write_instance


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_am_sf_inventory_route_round54"
BASE_COMMIT = "bbf2044ec710f5eb8bde19d2ed183caa84055dcc"
DERIVATION_VERSION = "round54-generalization-v1"
PANEL = "round54_generalization"

# Every size contains all four M/Q combinations and every structural
# configuration.  The duplicated configuration rotates so the complete panel
# contains four rows of each configuration.
ASSIGNMENTS = {
    12: ((2, 20, "tight_T"), (2, 30, "high_imbalance"),
         (3, 20, "moderate"), (3, 30, "tight_T")),
    20: ((2, 20, "high_imbalance"), (2, 30, "moderate"),
         (3, 20, "tight_T"), (3, 30, "high_imbalance")),
    50: ((2, 20, "moderate"), (2, 30, "tight_T"),
         (3, 20, "high_imbalance"), (3, 30, "moderate")),
}


def derived_seed(material: str) -> tuple[int, str]:
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return 10_000 + int(digest[:16], 16) % 1_900_000_000, digest


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    seen: set[int] = set()
    for size, assignments in ASSIGNMENTS.items():
        for ordinal, (m, q, stress) in enumerate(assignments, start=1):
            route_limit = 2400.0 if stress == "tight_T" else 3600.0
            configuration = f"{stress}_{int(route_limit)}"
            material = (
                f"{BASE_COMMIT}|{DERIVATION_VERSION}|V{size}|M{m}|Q{q}|"
                f"{configuration}|{ordinal}"
            )
            seed, derivation_hash = derived_seed(material)
            if seed in seen:
                raise RuntimeError(f"deterministic seed collision: {seed}")
            seen.add(seed)
            instance_id = (
                f"round54_generalization_{configuration}_V{size}_M{m}_Q{q}_"
                f"seed{seed}"
            )
            directory = (ROOT / "reference" / "round54_generalization" /
                         f"V{size}_M{m}_Q{q}")
            directory.mkdir(parents=True, exist_ok=True)
            generated = write_instance(
                directory / f"{instance_id}.txt", seed, stress,
                route_limit, v=size, m=m, q=q)
            rows.append({
                "panel": PANEL,
                "ordinal_within_size": ordinal,
                "instance_id": instance_id,
                "input_path": generated["path"],
                "input_sha256": generated["sha256"],
                "seed": seed,
                "seed_derivation_material": material,
                "seed_derivation_sha256": derivation_hash,
                "base_commit": BASE_COMMIT,
                "derivation_version": DERIVATION_VERSION,
                "V": size,
                "M": m,
                "Q": q,
                "T": int(route_limit),
                "difficulty_configuration": configuration,
                "generator_stress_type": stress,
                "generator": (
                    "scripts/generate_hard_exact_stress_instances.py:write_instance"),
                "selected_before_any_round54_candidate_runtime_result": True,
                "runtime_filtering_forbidden": True,
                "solver_results_sealed": True,
                "v50_extension_eligible": size == 50,
            })

    if len(rows) != 12 or len(seen) != 12:
        raise RuntimeError("generalization panel must contain 12 unique rows")
    for size in (12, 20, 50):
        size_rows = [row for row in rows if row["V"] == size]
        if ({(row["M"], row["Q"]) for row in size_rows} !=
                {(2, 20), (2, 30), (3, 20), (3, 30)}):
            raise RuntimeError(f"M/Q balance failed for V{size}")
        if {row["generator_stress_type"] for row in size_rows} != {
                "tight_T", "high_imbalance", "moderate"}:
            raise RuntimeError(f"configuration balance failed for V{size}")

    csv_path = OUT / "round54_generalization_manifest.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "schema": "round54-generalization-manifest-v1",
        "panel": PANEL,
        "base_commit": BASE_COMMIT,
        "derivation_version": DERIVATION_VERSION,
        "generated_before_any_round54_candidate_runtime_result": True,
        "solver_results_opened": False,
        "selection_rule": (
            "Four deterministic rows per V in {12,20,50}; every size uses all "
            "M/Q combinations and all three structural configurations; the "
            "duplicated configuration rotates; no runtime filtering."),
        "opening_rule": (
            "only after fixed-interval and K1 integration gates pass and "
            "candidate source plus one official executable are frozen"),
        "ordinary_process_cap_seconds": 3600,
        "v50_extension_process_cap_seconds": 7200,
        "v50_extension_rule": (
            "for a V50 input, extend both frozen methods to 7200 seconds iff "
            "neither method certifies by 3600 seconds"),
        "row_count": len(rows),
        "counts": {"V12": 4, "V20": 4, "V50": 4,
                   "M2_Q20": 3, "M2_Q30": 3,
                   "M3_Q20": 3, "M3_Q30": 3,
                   "tight_T": 4, "high_imbalance": 4, "moderate": 4},
        "seed_collision_count": 0,
        "rows": rows,
    }
    (OUT / "round54_generalization_manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("generated and sealed 12 deterministic Round 54 inputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
