#!/usr/bin/env python3
"""Generate and freeze the deterministic Round 32 multi-M qualification set."""

from __future__ import annotations

import csv
import hashlib
import os
from pathlib import Path

from generate_hard_exact_stress_instances import ROOT, write_instance


STARTING_COMMIT = "919fd688a29a730d897db612213982ba8792a53f"
DERIVATION_TAG = "round32-m-variation"
GENERATOR_VERSION = "round32_multi_m_v1"
OUT_ROOT = ROOT / "reference" / "qualification_round32"
MANIFEST = (
    ROOT / "results" / "gf_c6_long_run_validation_round32"
    / "round32_multi_m_manifest.csv"
)
FAMILIES = (
    ("high_imbalance", 3600.0),
    ("moderate", 3600.0),
    ("tight_T", 2400.0),
)
CASES = tuple(
    (v, m, family, t_limit)
    for v in (20, 50)
    for family, t_limit in FAMILIES
    for m in (2, 4)
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def derive_seed(v: int, m: int, family: str) -> tuple[int, str, str]:
    material = (
        f"{STARTING_COMMIT}|{DERIVATION_TAG}|V{v}|M{m}|{family}"
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    seed = 1 + (int(digest[:16], 16) % 2_147_483_646)
    return seed, digest, material


def validate_generated(path: Path, row: dict[str, str],
                       v: int, m: int) -> None:
    if not path.is_file() or sha256(path) != row["sha256"]:
        raise RuntimeError(f"generated instance hash mismatch: {path}")
    first = path.read_text(encoding="utf-8").splitlines()[0]
    expected = f"{v} {m} [{', '.join('30' for _ in range(m))}]"
    if first != expected:
        raise RuntimeError(
            f"generated instance header mismatch: {path}: {first!r}")
    if (
        int(row["V"]) != v
        or int(row["M"]) != m
        or int(row["Q"]) != 30
        or int(row["surplus_count"]) <= 0
        or int(row["deficit_count"]) <= 0
    ):
        raise RuntimeError(f"generated instance structural audit failed: {path}")


def write_csv_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    fields = list(rows[0])
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def main() -> int:
    rows: list[dict[str, str]] = []
    seeds: set[int] = set()
    for v, m, family, t_limit in CASES:
        seed, derivation_sha, material = derive_seed(v, m, family)
        if seed in seeds:
            raise RuntimeError(f"deterministic seed collision: {seed}")
        seeds.add(seed)
        instance_id = (
            f"round32_multi_m_{family}_V{v}_M{m}_seed{seed}"
        )
        directory = OUT_ROOT / f"V{v}_M{m}"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{instance_id}.txt"
        row = write_instance(
            path, seed, family, t_limit, v=v, m=m, q=30)
        row.update({
            "instance_id": instance_id,
            "derivation_tag": DERIVATION_TAG,
            "starting_commit": STARTING_COMMIT,
            "derivation_material": material,
            "derivation_sha256": derivation_sha,
            "generator_script": "scripts/generate_round32_multi_m.py",
            "base_generator_script":
                "scripts/generate_hard_exact_stress_instances.py",
            "generator_version": GENERATOR_VERSION,
            "structurally_valid": "true",
            "replacement_rule":
                "next_sha256_counter_seed_only_for_general_invalidity",
            "frozen_before_solver_results": "true",
        })
        validate_generated(path, row, v, m)
        rows.append(row)
    write_csv_atomic(MANIFEST, rows)
    print(f"generated and froze {len(rows)} Round 32 multi-M instances")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
