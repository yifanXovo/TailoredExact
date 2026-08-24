#!/usr/bin/env python3
"""Generate the independent Round 39 small difficulty-gradient benchmark."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import round39_instance_tools as tools


ROOT = tools.ROOT
STARTING_COMMIT = "1459308492a5eceed523dee53b5f9d79141b5242"
DERIVATION_TAG = "round39-small-hard-light-qualification"
GENERATOR_VERSION = "round39_small_gradient_v1"
REFERENCE_ROOT = ROOT / "reference" / "qualification_round39"
RESULT_ROOT = ROOT / "results" / "gf_small_hard_light_round39"
MANIFEST = RESULT_ROOT / "frozen_instance_manifest.csv"
DESCRIPTORS = RESULT_ROOT / "structural_descriptor_table.csv"
REJECTED = RESULT_ROOT / "rejected_generation_manifest.csv"
SEEDS = RESULT_ROOT / "seed_manifest.csv"
CONFIG = RESULT_ROOT / "generator_frozen_config.json"


@dataclass(frozen=True)
class Slot:
    stratum: str
    index: int
    v: int
    m: int
    q: int


SLOTS = tuple(
    Slot(stratum, index, v, m, q)
    for stratum, layout in (
        ("small-easy", (
            (8, 1, 30), (8, 2, 20), (8, 2, 30), (10, 1, 30),
            (10, 2, 30), (10, 3, 20), (12, 2, 30), (12, 3, 30),
        )),
        ("small-medium", (
            (8, 1, 20), (8, 2, 20), (8, 3, 30), (10, 1, 20),
            (10, 2, 20), (10, 3, 30), (12, 1, 30), (12, 3, 30),
        )),
        ("small-hard", (
            (10, 1, 20), (10, 1, 30), (10, 2, 20), (10, 3, 20),
            (12, 1, 20), (12, 2, 20), (12, 3, 20), (12, 3, 30),
        )),
    )
    for index, (v, m, q) in enumerate(layout, start=1)
)


PROFILES: dict[str, dict[str, Any]] = {
    "small-easy": {
        "T": 3600.0, "active_fraction": (0.45, 0.68),
        "imbalance": (3, 6), "radius": (220.0, 420.0),
        "spread": (55.0, 105.0), "clusters": 2,
    },
    "small-medium": {
        "T": 2850.0, "active_fraction": (0.67, 0.84),
        "imbalance": (5, 9), "radius": (430.0, 720.0),
        "spread": (75.0, 135.0), "clusters": 3,
    },
    "small-hard": {
        "T": 2400.0, "active_fraction": (0.84, 1.0),
        "imbalance": (7, 13), "radius": (650.0, 980.0),
        "spread": (70.0, 145.0), "clusters": 3,
    },
}


def derive_seed(slot: Slot, attempt: int) -> tuple[int, str, str]:
    material = (
        f"{STARTING_COMMIT}|{DERIVATION_TAG}|{slot.stratum}|slot{slot.index}"
        f"|V{slot.v}|M{slot.m}|Q{slot.q}|attempt{attempt}"
    )
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return 1 + int(digest[:16], 16) % 2_147_483_646, digest, material


def vectors(rng: random.Random, slot: Slot, profile: dict[str, Any]
            ) -> tuple[list[int], list[int], list[int]]:
    capacities = [100000] + [rng.randint(20, 50) for _ in range(slot.v)]
    target = [0]
    for capacity in capacities[1:]:
        low = max(6, int(math.ceil(0.35 * capacity)))
        high = max(low, int(math.floor(0.65 * capacity)))
        target.append(rng.randint(low, high))
    low_fraction, high_fraction = profile["active_fraction"]
    active_count = max(3, min(slot.v, round(rng.uniform(
        low_fraction, high_fraction) * slot.v)))
    active = list(range(1, slot.v + 1))
    rng.shuffle(active)
    active = active[:active_count]
    rng.shuffle(active)
    surplus_target = max(1, active_count // 2)
    if active_count >= 4:
        surplus_target = max(2, min(active_count - 2, surplus_target))
    signs = {station: (1 if pos < surplus_target else -1)
             for pos, station in enumerate(active)}
    initial = [50000, *target[1:]]
    minimum, maximum = profile["imbalance"]
    for station in active:
        available = (
            capacities[station] - target[station]
            if signs[station] > 0 else target[station]
        )
        magnitude = min(available, rng.randint(minimum, maximum))
        if magnitude < minimum:
            raise ValueError("station capacity cannot realize profile imbalance")
        initial[station] = target[station] + signs[station] * magnitude
    return capacities, initial, target


def points(rng: random.Random, slot: Slot,
           profile: dict[str, Any]) -> list[tuple[float, float]]:
    depot = (584400.0, 4511800.0)
    rotation = rng.uniform(0.0, 2.0 * math.pi)
    count = int(profile["clusters"])
    centers = []
    for index in range(count):
        angle = rotation + 2.0 * math.pi * index / count
        radius = rng.uniform(*profile["radius"])
        centers.append((
            depot[0] + radius * math.cos(angle),
            depot[1] + radius * math.sin(angle),
        ))
    spread = rng.uniform(*profile["spread"])
    output = [depot]
    for index in range(slot.v):
        center = centers[index % count]
        output.append((
            center[0] + rng.gauss(0.0, spread),
            center[1] + rng.gauss(0.0, spread),
        ))
    return output


def weights(initial: list[int], target: list[int]) -> list[float]:
    raw = [
        abs(initial[i] / target[i] - 1.0)
        for i in range(1, len(initial))
    ]
    scale = max(raw) or 1.0
    return [0.0, *(0.15 + 0.85 * value / scale for value in raw)]


def write_instance(path: Path, slot: Slot, seed: int) -> None:
    rng = random.Random(seed)
    profile = PROFILES[slot.stratum]
    capacities, initial, target = vectors(rng, slot, profile)
    station_weights = weights(initial, target)
    min_ratio = [0.0, *(max(0.0, min(initial[i], target[i]) /
                                  target[i] * 0.65)
                               for i in range(1, slot.v + 1))]
    locations = points(rng, slot, profile)
    distances = [[math.hypot(x1 - x2, y1 - y2)
                  for x2, y2 in locations] for x1, y1 in locations]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as out:
        out.write(f"{slot.v} {slot.m} [{', '.join(str(slot.q) for _ in range(slot.m))}]\n")
        out.write(f"capacities = {capacities}\n")
        out.write(f"initial     = {initial}\n")
        out.write(f"target      = {target}\n")
        out.write("weights    = [" + ", ".join(f"{value:.6f}" for value in station_weights) + "]\n")
        out.write("min_ratio  = [" + ", ".join(f"{value:.6f}" for value in min_ratio) + "]\n")
        out.write("points = [" + ", ".join(
            f"({x:.3f}, {y:.3f})" for x, y in locations) + "]\n")
        out.write("distances = [\n")
        for row in distances:
            out.write("{" + ", ".join(f"{value:.4f}" for value in row) + "}\n")
        out.write("]\n")


def rejection_reasons(slot: Slot, desc: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if not desc["structurally_nontrivial"]:
        reasons.extend(str(desc["structural_rejection_reasons"]).split(";"))
    if desc["difficulty_stratum"] != slot.stratum:
        reasons.append(
            f"score_label_{desc['difficulty_stratum']}_not_{slot.stratum}")
    if slot.stratum != "small-easy":
        if desc["surplus_count"] < 2 or desc["deficit_count"] < 2:
            reasons.append("medium_hard_requires_two_surplus_and_two_deficit")
        if desc["active_fraction"] < 0.60:
            reasons.append("medium_hard_active_fraction_below_0.60")
        if desc["initial_objective_lambda_0_15"] < 0.10:
            reasons.append("medium_hard_initial_objective_below_0.10")
        if desc["plausible_ordered_pair_density"] <= 0.10:
            reasons.append("medium_hard_route_choice_density_at_most_0.10")
    if slot.stratum == "small-hard":
        if desc["active_fraction"] < 0.80:
            reasons.append("hard_active_fraction_below_0.80")
        if desc["imbalance_l1"] < 5 * slot.v:
            reasons.append("hard_imbalance_l1_below_5V")
        if desc["support_duration_pressure"] < 0.20:
            reasons.append("hard_support_duration_pressure_below_0.20")
        if desc["full_service_pair_density"] >= 0.95:
            reasons.append("hard_full_service_pair_density_at_least_0.95")
    return sorted(set(reason for reason in reasons if reason))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    fields: list[str] = []
    for row in rows:
        for field in row:
            if field not in fields:
                fields.append(field)
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-attempts", type=int, default=200)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if MANIFEST.exists() and not args.force:
        raise SystemExit("Round 39 benchmark is already frozen; use no regeneration")
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    seed_rows: list[dict[str, Any]] = []
    for slot in SLOTS:
        chosen = False
        for attempt in range(args.max_attempts):
            seed, derivation_sha, material = derive_seed(slot, attempt)
            candidate = RESULT_ROOT / "generator_development" / (
                f"{slot.stratum}__slot{slot.index}__attempt{attempt}.txt")
            try:
                write_instance(candidate, slot, seed)
                desc = tools.descriptors(tools.read_instance(
                    candidate, total_time_limit=PROFILES[slot.stratum]["T"]))
                reasons = rejection_reasons(slot, desc)
            except (ValueError, OSError) as error:
                desc = {}
                reasons = [f"generator_invalid:{error}"]
            base = {
                "stratum_slot": f"{slot.stratum}-{slot.index:02d}",
                "intended_stratum": slot.stratum,
                "attempt": attempt,
                "seed": seed,
                "V": slot.v,
                "M": slot.m,
                "Q": slot.q,
                "derivation_material": material,
                "derivation_sha256": derivation_sha,
                **desc,
            }
            if reasons:
                rejected.append({
                    **base,
                    "candidate_sha256": tools.sha256(candidate)
                        if candidate.is_file() else "",
                    "rejection_reasons": ";".join(reasons),
                    "rejected_before_official_solver_comparison": True,
                })
                candidate.unlink(missing_ok=True)
                continue
            instance_id = (
                f"round39_{slot.stratum.replace('-', '_')}_V{slot.v}_M{slot.m}"
                f"_Q{slot.q}_slot{slot.index:02d}_seed{seed}"
            )
            destination = REFERENCE_ROOT / slot.stratum / f"{instance_id}.txt"
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(candidate, destination)
            record = {
                "round_id": 39,
                "instance_id": instance_id,
                "path": destination.relative_to(ROOT).as_posix(),
                "sha256": tools.sha256(destination),
                "seed": seed,
                "V": slot.v,
                "M": slot.m,
                "Q": slot.q,
                "T": PROFILES[slot.stratum]["T"],
                "lambda": 0.15,
                "difficulty_stratum": slot.stratum,
                "stratum_slot": base["stratum_slot"],
                "accepted_attempt": attempt,
                "derivation_material": material,
                "derivation_sha256": derivation_sha,
                "generator_version": GENERATOR_VERSION,
                "generator_script": "scripts/generate_round39_small_hard.py",
                "descriptor_script": "scripts/round39_instance_tools.py",
                "selection_basis": "frozen_structural_descriptors_only",
                "solver_outcomes_used_for_selection": False,
                "frozen_before_official_comparison": True,
            }
            accepted.append(record)
            seed_rows.append({
                "stratum_slot": base["stratum_slot"],
                "instance_id": instance_id,
                "seed": seed,
                "accepted_attempt": attempt,
                "derivation_material": material,
                "derivation_sha256": derivation_sha,
            })
            chosen = True
            break
        if not chosen:
            raise RuntimeError(f"no structural match for {slot}")
    descriptor_rows = []
    for row in accepted:
        desc = tools.descriptors(tools.read_instance(
            ROOT / row["path"], total_time_limit=float(row["T"])))
        if desc["difficulty_stratum"] != row["difficulty_stratum"]:
            raise RuntimeError(f"descriptor label drift: {row['instance_id']}")
        descriptor_rows.append({
            "round_id": 39,
            "instance_id": row["instance_id"],
            "instance_sha256": row["sha256"],
            "intended_stratum": row["difficulty_stratum"],
            **desc,
        })
    if len(accepted) != 24 or any(
            sum(row["difficulty_stratum"] == name for row in accepted) != 8
            for name in PROFILES):
        raise RuntimeError("Round 39 requires exactly eight instances per stratum")
    write_csv(MANIFEST, accepted)
    write_csv(DESCRIPTORS, descriptor_rows)
    write_csv(REJECTED, rejected or [{"rejection_reasons": "none"}])
    write_csv(SEEDS, seed_rows)
    config = {
        "schema": "round39-generator-config-v1",
        "round_id": 39,
        "starting_commit": STARTING_COMMIT,
        "derivation_tag": DERIVATION_TAG,
        "generator_version": GENERATOR_VERSION,
        "instance_count": len(accepted),
        "stratum_counts": {name: 8 for name in PROFILES},
        "profiles": PROFILES,
        "slots": [slot.__dict__ for slot in SLOTS],
        "score_thresholds": {
            "small-easy": "score < 60",
            "small-medium": "60 <= score < 78",
            "small-hard": "score >= 78",
        },
        "selection_prohibition": (
            "no solver outcome, time, work, node, incumbent, bound, gap, "
            "certificate, or P-GRB/C6 winner field may affect selection"
        ),
        "frozen_before_official_solver_comparison": True,
    }
    CONFIG.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    development = RESULT_ROOT / "generator_development"
    if development.exists() and not any(development.iterdir()):
        development.rmdir()
    print(json.dumps({
        "accepted": len(accepted),
        "rejected": len(rejected),
        "strata": {name: sum(row["difficulty_stratum"] == name
                             for row in accepted) for name in PROFILES},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
