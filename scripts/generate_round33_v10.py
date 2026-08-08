#!/usr/bin/env python3
"""Generate and freeze the deterministic Round 33 V=10 benchmark set."""

from __future__ import annotations

import ast
import csv
import hashlib
import os
import statistics
from pathlib import Path

from generate_hard_exact_stress_instances import ROOT, write_instance


STARTING_COMMIT = "2db8fe5b5c33145e1a8cd6dca86f8459885fa2bf"
DERIVATION_TAG = "round33-v10-convergence"
GENERATOR_VERSION = "round33_v10_convergence_v1"
OUT_ROOT = ROOT / "reference" / "qualification_round33"
RESULT_ROOT = ROOT / "results" / "gf_v10_convergence_round33"
MANIFEST = RESULT_ROOT / "round33_v10_instance_manifest.csv"
SCENARIOS = (
    ("high_imbalance", 3600.0),
    ("moderate", 3600.0),
    ("tight_T", 2400.0),
)
CASES = tuple(
    (m, q, scenario, t_limit)
    for m in (1, 2, 3)
    for q in (20, 30)
    for scenario, t_limit in SCENARIOS
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def derive_seed(m: int, q: int, scenario: str,
                replacement_counter: int = 0) -> tuple[int, str, str]:
    material = (
        f"{STARTING_COMMIT}|{DERIVATION_TAG}|M{m}|Q{q}|{scenario}"
        f"|replacement{replacement_counter}"
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    seed = 1 + (int(digest[:16], 16) % 2_147_483_646)
    return seed, digest, material


def station_capacities(path: Path) -> list[int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    prefix = "capacities = "
    line = next((item for item in lines if item.startswith(prefix)), "")
    if not line:
        raise RuntimeError(f"capacity line missing: {path}")
    values = ast.literal_eval(line[len(prefix):])
    if not isinstance(values, list) or len(values) != 11:
        raise RuntimeError(f"capacity vector invalid: {path}")
    return [int(item) for item in values[1:]]


def validate_generated(path: Path, row: dict[str, str],
                       m: int, q: int) -> None:
    if not path.is_file() or sha256(path) != row["sha256"]:
        raise RuntimeError(f"generated instance hash mismatch: {path}")
    first = path.read_text(encoding="utf-8").splitlines()[0]
    expected = f"10 {m} [{', '.join(str(q) for _ in range(m))}]"
    capacities = station_capacities(path)
    if first != expected:
        raise RuntimeError(
            f"generated instance header mismatch: {path}: {first!r}")
    if (
        int(row["V"]) != 10
        or int(row["M"]) != m
        or int(row["Q"]) != q
        or int(row["surplus_count"]) <= 0
        or int(row["deficit_count"]) <= 0
        or min(capacities) < 20
        or max(capacities) > 50
    ):
        raise RuntimeError(f"generated instance structural audit failed: {path}")


def write_csv_atomic(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def main() -> int:
    rows: list[dict[str, str]] = []
    seeds: set[int] = set()
    base_generator = ROOT / "scripts/generate_hard_exact_stress_instances.py"
    for m, q, scenario, t_limit in CASES:
        seed, derivation_sha, material = derive_seed(m, q, scenario)
        if seed in seeds:
            raise RuntimeError(f"deterministic seed collision: {seed}")
        seeds.add(seed)
        instance_id = (
            f"round33_v10_{scenario}_M{m}_Q{q}_seed{seed}"
        )
        directory = OUT_ROOT / f"M{m}_Q{q}"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{instance_id}.txt"
        row = write_instance(
            path, seed, scenario, t_limit, v=10, m=m, q=q)
        capacities = station_capacities(path)
        row.update({
            "instance_id": instance_id,
            "scenario": scenario,
            "family": scenario,
            "derivation_tag": DERIVATION_TAG,
            "starting_commit": STARTING_COMMIT,
            "derivation_material": material,
            "derivation_sha256": derivation_sha,
            "replacement_counter": "0",
            "generator_script": "scripts/generate_round33_v10.py",
            "base_generator_script":
                "scripts/generate_hard_exact_stress_instances.py",
            "base_generator_sha256": sha256(base_generator),
            "generator_version": GENERATOR_VERSION,
            "generation_command":
                "D:/msys64/ucrt64/bin/python.exe "
                "scripts/generate_round33_v10.py",
            "station_capacity_mean": f"{statistics.fmean(capacities):.9f}",
            "station_capacity_median":
                f"{statistics.median(capacities):.9f}",
            "station_capacity_total": str(sum(capacities)),
            "structurally_valid": "true",
            "replacement_rule": (
                "only_after_documented_general_generator_invalidity;"
                "increment_replacement_counter_and_rederive_sha256_seed"
            ),
            "frozen_before_solver_results": "true",
        })
        validate_generated(path, row, m, q)
        rows.append(row)
    if len(rows) != 18:
        raise RuntimeError(f"expected 18 instances, generated {len(rows)}")
    write_csv_atomic(MANIFEST, rows)
    print(f"generated and froze {len(rows)} Round 33 V10 instances")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
