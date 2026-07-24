#!/usr/bin/env python3
"""Generate the frozen Round 31 sealed held-out qualification instances."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from generate_hard_exact_stress_instances import ROOT, RULE_VERSION, write_instance


STARTING_COMMIT = "893656f85fa6394dac787fee78baad2a52cdd2d2"
DERIVATION_TAG = "round31-sealed-heldout"
OUT_ROOT = ROOT / "reference" / "heldout_round31"
MANIFEST = (
    ROOT
    / "results"
    / "gf_nonblocking_gurobi_c6_round31"
    / "round31_sealed_heldout_manifest.csv"
)

CASES = (
    ("high_imbalance", 20, 3600.0),
    ("high_imbalance", 50, 3600.0),
    ("moderate", 20, 3600.0),
    ("moderate", 50, 3600.0),
    ("tight_T", 20, 2400.0),
    ("tight_T", 50, 2400.0),
)


def derive_seed(family: str, v: int) -> tuple[int, str, str]:
    material = f"{STARTING_COMMIT}|{DERIVATION_TAG}|{family}|V{v}"
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    seed = 1 + (int(digest[:16], 16) % 2_147_483_646)
    return seed, digest, material


def main() -> int:
    rows: list[dict[str, str]] = []
    seen_seeds: set[int] = set()
    for family, v, t_limit in CASES:
        seed, digest, material = derive_seed(family, v)
        if seed in seen_seeds:
            raise RuntimeError(f"held-out seed collision: {seed}")
        seen_seeds.add(seed)
        instance_id = f"round31_sealed_{family}_V{v}_seed{seed}"
        out_dir = OUT_ROOT / f"V{v}_M3"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{instance_id}.txt"
        row = write_instance(path, seed, family, t_limit, v=v)
        row.update(
            {
                "instance_id": instance_id,
                "derivation_tag": DERIVATION_TAG,
                "starting_commit": STARTING_COMMIT,
                "derivation_material": material,
                "derivation_sha256": digest,
                "generator_script": (
                    "scripts/generate_round31_sealed_heldout.py"
                ),
                "base_generator_script": (
                    "scripts/generate_hard_exact_stress_instances.py"
                ),
                "sealed_before_c6_development": "true",
                "development_use_forbidden": "true",
            }
        )
        rows.append(row)

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    fields = (
        "instance_id",
        "path",
        "sha256",
        "seed",
        "V",
        "M",
        "Q",
        "T",
        "lambda",
        "capacity_min",
        "capacity_max",
        "total_initial",
        "total_target",
        "surplus_count",
        "deficit_count",
        "coordinate_pattern",
        "stress_type",
        "generation_rule_version",
        "derivation_tag",
        "starting_commit",
        "derivation_material",
        "derivation_sha256",
        "generator_script",
        "base_generator_script",
        "sealed_before_c6_development",
        "development_use_forbidden",
    )
    with MANIFEST.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    if RULE_VERSION != "hard_v20_m3_v1":
        raise RuntimeError(f"unexpected base generation rule: {RULE_VERSION}")
    print(f"generated {len(rows)} sealed Round 31 instances")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
