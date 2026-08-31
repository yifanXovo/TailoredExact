#!/usr/bin/env python3
"""Freeze deterministic Round 52 validation and holdout benchmark inputs.

The identities are derived only from the frozen Round 51 base commit, panel,
size, and a predeclared structural configuration.  The script never invokes a
solver and never filters generated instances using runtime observations.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from generate_hard_exact_stress_instances import write_instance


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_tailored_cut_final_validation_round52"
BASE_COMMIT = "c6d7109bf69f50bd459174e8f05242b478e57d85"
DERIVATION_VERSION = "round52-independent-panels-v1"
PANELS = ("validation", "holdout")
SIZES = (12, 20, 50)
CONFIGURATIONS = (
    ("tight_T_2400", "tight_T", 2400.0),
    ("tight_T_2550", "tight_T", 2550.0),
    ("high_imbalance_3600", "high_imbalance", 3600.0),
    ("moderate_3600", "moderate", 3600.0),
)


def derived_seed(material: str) -> tuple[int, str]:
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    return 10_000 + int(digest[:16], 16) % 1_900_000_000, digest


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    by_panel: dict[str, list[dict[str, object]]] = {panel: [] for panel in PANELS}
    seen_seeds: set[int] = set()

    for panel in PANELS:
        for v in SIZES:
            out_dir = ROOT / "reference" / f"round52_{panel}" / f"V{v}_M3"
            out_dir.mkdir(parents=True, exist_ok=True)
            for ordinal, (config, stress_type, t_limit) in enumerate(
                    CONFIGURATIONS, start=1):
                material = (
                    f"{BASE_COMMIT}|{DERIVATION_VERSION}|{panel}|V{v}|M3|"
                    f"Q30|{ordinal}|{config}"
                )
                seed, digest = derived_seed(material)
                if seed in seen_seeds:
                    raise RuntimeError(f"deterministic seed collision: {seed}")
                seen_seeds.add(seed)
                instance_id = (
                    f"round52_{panel}_{config}_V{v}_M3_seed{seed}"
                )
                path = out_dir / f"{instance_id}.txt"
                generated = write_instance(
                    path, seed, stress_type, t_limit, v=v, m=3, q=30)
                row: dict[str, object] = {
                    "panel": panel,
                    "ordinal": ordinal,
                    "instance_id": instance_id,
                    "input_path": generated["path"],
                    "input_sha256": generated["sha256"],
                    "seed": seed,
                    "seed_derivation_material": material,
                    "seed_derivation_sha256": digest,
                    "base_commit": BASE_COMMIT,
                    "derivation_version": DERIVATION_VERSION,
                    "V": v,
                    "M": 3,
                    "Q": 30,
                    "T": int(t_limit),
                    "difficulty_configuration": config,
                    "generator_stress_type": stress_type,
                    "generator": "scripts/generate_hard_exact_stress_instances.py:write_instance",
                    "selected_before_solver_results": True,
                    "runtime_filtering_forbidden": True,
                    "development_use_forbidden": panel == "holdout",
                }
                by_panel[panel].append(row)

    if set(row["seed"] for rows in by_panel.values() for row in rows) != seen_seeds:
        raise RuntimeError("seed uniqueness audit failed")

    fields = list(by_panel["validation"][0].keys())
    for panel, rows in by_panel.items():
        csv_path = EVIDENCE / f"{panel}_instance_manifest.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        payload = {
            "schema": "round52-independent-instance-manifest-v1",
            "panel": panel,
            "frozen_before_any_round52_solver_result": True,
            "base_commit": BASE_COMMIT,
            "derivation_version": DERIVATION_VERSION,
            "selection_rule": (
                "four predeclared generator configurations for each of V12, "
                "V20, and V50; SHA-256-derived seeds; no runtime filtering"
            ),
            "holdout_opening_rule": (
                "after tau, controller, inner backend, source commit, and "
                "executable SHA-256 are frozen"
                if panel == "holdout" else "after Stage 0 freeze"
            ),
            "row_count": len(rows),
            "rows": rows,
        }
        (EVIDENCE / f"{panel}_instance_manifest.json").write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    freeze = {
        "schema": "round52-final-validation-instance-freeze-v1",
        "frozen_before_any_round52_solver_result": True,
        "validation_count": len(by_panel["validation"]),
        "holdout_count": len(by_panel["holdout"]),
        "counts_by_size_per_panel": {"V12": 4, "V20": 4, "V50": 4},
        "validation_manifest": (
            "results/gf_k1_tailored_cut_final_validation_round52/"
            "validation_instance_manifest.json"
        ),
        "holdout_manifest": (
            "results/gf_k1_tailored_cut_final_validation_round52/"
            "holdout_instance_manifest.json"
        ),
        "independent_panels": True,
        "seed_collision_count": 0,
        "development_use_of_holdout_forbidden": True,
        "algorithm_change_after_validation_opens_forbidden": True,
        "algorithm_change_after_holdout_opens_forbidden": True,
    }
    (EVIDENCE / "final_validation_instance_freeze.json").write_text(
        json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
    print("frozen 12 validation and 12 holdout inputs")


if __name__ == "__main__":
    main()
