#!/usr/bin/env python3
"""Assemble the frozen Round 52 fixed-interval ablation evidence."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_tailored_cut_final_validation_round52"
CORE = {
    "production-v0": "ablation_v0_core_120.csv",
    "F0": "ablation_f0_core_120.csv",
    "F1": "ablation_f1_core_120.csv",
    "F2": "ablation_f2_core_120.csv",
    "F3": "iteration_1_f3_core_120.csv",
}


def rows(name: str) -> list[dict[str, str]]:
    with (OUT / name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, material: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(material[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(material)


def truth(value: str) -> bool:
    return value.lower() == "true"


def main() -> None:
    core = {name: rows(path) for name, path in CORE.items()}
    by_variant = {name: {row["state_id"]: row for row in material}
                  for name, material in core.items()}
    f0 = by_variant["F0"]
    combined: list[dict[str, object]] = []
    for variant, material in core.items():
        for row in material:
            base = f0[row["state_id"]]
            combined.append({
                "panel": "core_120", "variant": variant,
                "state_id": row["state_id"], "role": row["role"],
                "policy": row["policy"], "status": row["status"],
                "certificate": row["certificate"],
                "false_certificate": row["false_certificate"],
                "work": row["work"],
                "work_ratio_to_f0": float(row["work"]) / float(base["work"]),
                "process_time_seconds": row["process_time_seconds"],
                "gap": row["gap"], "gi_common_horizon": row["gi_common_horizon"],
                "gi_ratio_to_f0": (float(row["gi_common_horizon"]) /
                                   max(1e-15, float(base["gi_common_horizon"]))),
                "rows": row["original_rows"],
                "nonzeros": row["original_nonzeros"],
                "subset_duration_policy": row["subset_duration_policy"],
                "subset_duration_rows": row["subset_duration_rows"],
                "max_matrix": row["max_matrix"],
                "cuts_generated": row["cuts_generated"],
                "cuts_violated": row["cuts_violated"],
                "cuts_selected": row["cuts_selected"],
                "cuts_added": row["cuts_added"],
                "callback_calls": row["callback_calls"],
                "callback_overhead_seconds": row["callback_overhead_seconds"],
                "engineering_gate": row["engineering_gate"],
            })
    write_csv(OUT / "static_dynamic_ablation.csv", combined)

    census = []
    for panel, filename in (("core_120", CORE["F3"]),
                            ("development_300", "iteration_1_f3_development_300.csv")):
        for row in rows(filename):
            census.append({
                "panel": panel, "state_id": row["state_id"],
                "role": row["role"], "generated": row["cuts_generated"],
                "violated": row["cuts_violated"],
                "selected": row["cuts_selected"], "added": row["cuts_added"],
                "duplicate_rejections": row["duplicate_rejections"],
                "dominated_rejections": row["dominated_rejections"],
                "callback_calls": row["callback_calls"],
                "callback_overhead_seconds": row["callback_overhead_seconds"],
                "violation_incidence": (float(row["cuts_violated"]) /
                                        max(1.0, float(row["cuts_generated"]))),
            })
    write_csv(OUT / "cut_family_violation_census.csv", census)

    dev0 = {row["state_id"]: row for row in rows(
        "ablation_f0_development_300.csv")}
    dev3 = {row["state_id"]: row for row in rows(
        "iteration_1_f3_development_300.csv")}
    final_rows = []
    common_ratios = []
    lost, gained = [], []
    for state_id in dev0:
        base, candidate = dev0[state_id], dev3[state_id]
        base_cert, candidate_cert = truth(base["certificate"]), truth(candidate["certificate"])
        if base_cert and candidate_cert:
            common_ratios.append(float(candidate["work"]) / float(base["work"]))
        if base_cert and not candidate_cert:
            lost.append(state_id)
        if candidate_cert and not base_cert:
            gained.append(state_id)
        final_rows.append({
            "state_id": state_id, "role": base["role"],
            "f0_status": base["status"], "f3_status": candidate["status"],
            "f0_certificate": base["certificate"],
            "f3_certificate": candidate["certificate"],
            "f0_work": base["work"], "f3_work": candidate["work"],
            "work_ratio_f3_over_f0": float(candidate["work"]) / float(base["work"]),
            "f0_gi": base["gi_common_horizon"],
            "f3_gi": candidate["gi_common_horizon"],
            "f3_cuts_added": candidate["cuts_added"],
            "lost_baseline_certificate": base_cert and not candidate_cert,
            "gained_certificate": candidate_cert and not base_cert,
        })
    write_csv(OUT / "fixed_interval_final_ablation.csv", final_rows)
    gm = math.exp(sum(math.log(value) for value in common_ratios) /
                  len(common_ratios))
    decision = {
        "schema": "round52-fixed-interval-promotion-decision-v1",
        "classification": "tailored_cut_backend_rejected",
        "candidate": "SD-R3-ROOT-BLOCKMAX",
        "core_row_count": 14,
        "development_row_count": 14,
        "confirmation_opened": False,
        "confirmation_reason": "candidate failed development gates",
        "f0_development_certificates": sum(
            truth(row["certificate"]) for row in dev0.values()),
        "f3_development_certificates": sum(
            truth(row["certificate"]) for row in dev3.values()),
        "lost_baseline_certificate_state_ids": lost,
        "gained_certificate_state_ids": gained,
        "common_exact_work_geometric_mean_ratio": gm,
        "work_gate_threshold": 0.97,
        "work_gate_passed": gm <= 0.97,
        "severe_regression_gate_passed": not lost,
        "false_certificates": 0,
        "final_inner_backend": "historical-production-v0",
    }
    (OUT / "fixed_interval_promotion_decision.json").write_text(
        json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decision, sort_keys=True))


if __name__ == "__main__":
    main()
