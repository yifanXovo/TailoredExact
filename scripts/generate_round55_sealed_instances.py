#!/usr/bin/env python3
"""Generate the unopened Round 55 primary and strong-expansion panels.

This script is definition-only: it invokes the deterministic repository
instance generator and records hashes, but never invokes an optimizer.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from generate_hard_exact_stress_instances import write_instance


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_am_sf_station_state_chain_round55"
BASE_COMMIT = "324646af2e253618218812717a53e3e9e9cf1d9c"
DERIVATION_VERSION = "round55-station-state-chain-v1"

PRIMARY = {
    12: ((2, 20, "tight_T"), (2, 30, "high_imbalance"),
         (3, 20, "moderate"), (3, 30, "tight_T")),
    20: ((2, 20, "high_imbalance"), (2, 30, "moderate"),
         (3, 20, "tight_T"), (3, 30, "high_imbalance")),
    50: ((2, 20, "moderate"), (2, 30, "tight_T"),
         (3, 20, "high_imbalance"), (3, 30, "moderate")),
}

EXPANSION = {
    20: ((2, 20, "moderate"), (2, 30, "tight_T"),
         (3, 20, "high_imbalance"), (3, 30, "moderate")),
    50: ((2, 20, "tight_T"), (2, 30, "high_imbalance"),
         (3, 20, "moderate"), (3, 30, "tight_T")),
    70: ((2, 20, "high_imbalance"), (3, 30, "moderate")),
}


def seed_for(material: str) -> tuple[int, str]:
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return 10_000 + int(digest[:16], 16) % 1_900_000_000, digest


def generate(panel: str, assignments: dict[int, tuple[tuple[int, int, str], ...]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[int] = set()
    for size, entries in assignments.items():
        for ordinal, (m, q, stress) in enumerate(entries, start=1):
            route_limit = 2400.0 if stress == "tight_T" else 3600.0
            configuration = f"{stress}_{int(route_limit)}"
            material = (
                f"{BASE_COMMIT}|{DERIVATION_VERSION}|{panel}|V{size}|M{m}|"
                f"Q{q}|{configuration}|{ordinal}"
            )
            seed, derivation_hash = seed_for(material)
            if seed in seen:
                raise RuntimeError(f"seed collision in {panel}: {seed}")
            seen.add(seed)
            instance_id = (
                f"round55_{panel}_{configuration}_V{size}_M{m}_Q{q}_seed{seed}"
            )
            directory = ROOT / "reference" / f"round55_{panel}" / f"V{size}_M{m}_Q{q}"
            directory.mkdir(parents=True, exist_ok=True)
            generated = write_instance(
                directory / f"{instance_id}.txt", seed, stress, route_limit,
                v=size, m=m, q=q,
            )
            rows.append({
                "panel": panel,
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
                "generator": "scripts/generate_hard_exact_stress_instances.py:write_instance",
                "selected_before_any_round55_candidate_runtime_result": True,
                "runtime_filtering_forbidden": True,
                "solver_results_sealed": True,
            })
    return rows


def write_manifest(name: str, rows: list[dict[str, object]], opening_rule: str) -> None:
    payload = {
        "schema": f"round55-{name.replace('_', '-')}-manifest-v1",
        "panel": name,
        "base_commit": BASE_COMMIT,
        "derivation_version": DERIVATION_VERSION,
        "generated_before_any_round55_candidate_runtime_result": True,
        "solver_results_opened": False,
        "runtime_filtering_forbidden": True,
        "opening_rule": opening_rule,
        "row_count": len(rows),
        "rows": rows,
    }
    (OUT / f"{name}_manifest.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    primary = generate("sealed_generalization", PRIMARY)
    expansion = generate("expansion_panel", EXPANSION)
    if len(primary) != 12 or len(expansion) != 10:
        raise RuntimeError("Round 55 panel cardinality mismatch")
    write_manifest(
        "sealed_generalization", primary,
        "Open only after source/executable freeze and successful full K1 integration.",
    )
    write_manifest(
        "expansion_panel", expansion,
        "Open only after the frozen strong-result gate passes on the primary sealed panel.",
    )
    print(json.dumps({"sealed_generalization": len(primary), "expansion_panel": len(expansion)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
