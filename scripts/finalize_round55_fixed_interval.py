#!/usr/bin/env python3
"""Finalize Round 55 fixed-interval gates and freeze one inner candidate."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_am_sf_station_state_chain_round55"


def read_json(name: str) -> dict[str, Any]:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def rows(name: str) -> list[dict[str, str]]:
    with (EVIDENCE / name).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_json(name: str, value: object) -> None:
    path = EVIDENCE / name
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def write_csv(name: str, material: list[dict[str, object]]) -> None:
    path = EVIDENCE / name
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(material[0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(material)
    temporary.replace(path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stage_row(label: str, csv_name: str, summary_name: str,
              decision_name: str) -> dict[str, object]:
    summary = read_json(summary_name)
    decision = read_json(decision_name)
    vd = decision["summaries"]["VD-P"]
    return {
        "stage": label, "evidence_csv": csv_name,
        "physical_rows": summary["row_count"], "pair_count": decision["pair_count"],
        "f0_certificates": summary["certificate_counts"]["F0-CLEAN"],
        "vdp_certificates": summary["certificate_counts"]["VD-P"],
        "certificate_gains": vd["certificate_gain_count"],
        "certificate_losses": vd["certificate_loss_count"],
        "false_certificates": decision["false_certificate_count"],
        "severe_regressions": vd["severe_regression_count"],
        "shifted_work_geometric_mean_ratio": vd["shifted_work_geometric_mean_ratio"],
        "aggregate_gi_ratio": vd["aggregate_gi_ratio"],
        "selected": "VD-P" if "VD-P" in decision["selected_for_next_stage"] else "",
    }


def main() -> int:
    long_stage = read_json("fixed_interval_key_long_3600s.summary.json")
    long_analysis = read_json("fixed_interval_key_long_3600s_decision.json")
    vd = long_analysis["summaries"]["VD-P"]
    physical = rows("fixed_interval_key_long_3600s.csv")
    vdp_memory = max(float(row["peak_memory_gb"] or 0) for row in physical
                     if row["arm"] == "VD-P")
    f0_memory = max(float(row["peak_memory_gb"] or 0) for row in physical
                    if row["arm"] == "F0-CLEAN")
    short_gains_reversed = (
        float(vd["shifted_work_geometric_mean_ratio"]) > 1.05 and
        float(vd["aggregate_gi_ratio"]) > 1.05)
    memory_stable = vdp_memory <= 8.0 and vdp_memory <= max(1.0, 2.0 * f0_memory)
    pass_long = (
        long_analysis["false_certificate_count"] == 0 and
        vd["certificate_loss_count"] == 0 and
        vd["severe_regression_count"] == 0 and
        not short_gains_reversed and memory_stable)
    long_decision = {
        "schema": "round55-fixed-interval-long-decision-v1",
        "physical_rows": long_stage["row_count"],
        "pair_count": long_analysis["pair_count"],
        "certificate_counts": long_stage["certificate_counts"],
        "false_certificates": long_analysis["false_certificate_count"],
        "certificate_gains": vd["certificate_gain_count"],
        "certificate_losses": vd["certificate_loss_count"],
        "severe_regressions": vd["severe_regression_count"],
        "shifted_work_geometric_mean_ratio": vd["shifted_work_geometric_mean_ratio"],
        "aggregate_gi_ratio": vd["aggregate_gi_ratio"],
        "short_horizon_gains_reversed_materially": short_gains_reversed,
        "maximum_f0_memory_gb": f0_memory,
        "maximum_vdp_memory_gb": vdp_memory,
        "memory_stable": memory_stable,
        "gate_pass": pass_long,
        "selected_inner": "VD-P" if pass_long else "F0-CLEAN",
    }
    write_json("fixed_interval_long_decision.json", long_decision)

    summary_rows = [
        stage_row("C1-C9 confirmation", "fixed_interval_confirmation_1200s.csv",
                  "fixed_interval_confirmation_1200s.summary.json",
                  "fixed_interval_confirmation_1200s_decision.json"),
        stage_row("confirmation extension", "fixed_interval_confirmation_1800s.csv",
                  "fixed_interval_confirmation_1800s.summary.json",
                  "fixed_interval_confirmation_1800s_decision.json"),
        {
            "stage": "key long", "evidence_csv": "fixed_interval_key_long_3600s.csv",
            "physical_rows": long_stage["row_count"],
            "pair_count": long_analysis["pair_count"],
            "f0_certificates": long_stage["certificate_counts"]["F0-CLEAN"],
            "vdp_certificates": long_stage["certificate_counts"]["VD-P"],
            "certificate_gains": vd["certificate_gain_count"],
            "certificate_losses": vd["certificate_loss_count"],
            "false_certificates": long_analysis["false_certificate_count"],
            "severe_regressions": vd["severe_regression_count"],
            "shifted_work_geometric_mean_ratio": vd["shifted_work_geometric_mean_ratio"],
            "aggregate_gi_ratio": vd["aggregate_gi_ratio"],
            "selected": long_decision["selected_inner"],
        },
    ]
    write_csv("fixed_interval_confirmation_summary.csv", summary_rows)

    selected = long_decision["selected_inner"]
    definition = {
        "schema": "round55-final-inner-candidate-definition-v1",
        "frozen_after_key_long_results": True,
        "selected_inner": selected,
        "source_commit": "6d0818126cd1d1c00029ea30f346c129d6093bfa",
        "official_fixed_interval_executable_sha256":
            "5151efab9fbd82b91004e2255e60f112707278033d74549a4b0705000b681264",
        "stable_policy": "interval-mip-core-no-exhaustive-subset-duration",
        "candidate_policy": "round55-vd-p" if selected == "VD-P" else
                            "interval-mip-core-no-exhaustive-subset-duration",
        "k1_research_preset": "research-k1-am-sf-vdp" if selected == "VD-P" else
                              "paper-k1-am-sf",
        "formulation": ({
            "selectors": "sum_y s_i_y=1; Y_i=sum_y y*s_i_y",
            "perspectives": "l*s_i_y<=q_i_y<=u*s_i_y",
            "reconstruction": "sum_y q_i_y=G; Z_i=sum_y y*q_i_y",
            "replaces": "product-only binary-expansion block",
        } if selected == "VD-P" else {"formulation": "F0-CLEAN"}),
        "active_static_families": "paperK1AmSfActiveFamilies unchanged",
        "dynamic_user_cut_callback": False,
        "PreCrush_change": False,
        "new_tunable_parameters": [],
        "dispatch": "none",
        "outer_controller_change": "none",
        "gate_evidence": "fixed_interval_long_decision.json",
    }
    write_json("final_inner_candidate_definition.json", definition)
    ablation = [{
        "candidate": "VD-P", "baseline": "F0-CLEAN",
        "root_census_pairs": 27, "pilot_pairs": 16,
        "development_pairs": 14, "confirmation_1200_pairs": 9,
        "confirmation_1800_pairs": 19, "key_long_pairs": long_analysis["pair_count"],
        "key_long_certificate_gains": vd["certificate_gain_count"],
        "key_long_certificate_losses": vd["certificate_loss_count"],
        "key_long_severe_regressions": vd["severe_regression_count"],
        "key_long_shifted_work_gm": vd["shifted_work_geometric_mean_ratio"],
        "key_long_aggregate_gi_ratio": vd["aggregate_gi_ratio"],
        "selected": selected == "VD-P",
    }]
    write_csv("final_inner_candidate_ablation.csv", ablation)
    paths = [
        EVIDENCE / "final_inner_candidate_definition.json",
        EVIDENCE / "fixed_interval_long_decision.json",
        EVIDENCE / "station_state_exactness_proof.md",
        EVIDENCE / "station_state_convex_hull_proof.md",
        ROOT / "src" / "CplexBaseline.cpp",
        ROOT / "include" / "CplexBaseline.hpp",
    ]
    write_json("final_inner_candidate_freeze_manifest.json", {
        "schema": "round55-final-inner-candidate-freeze-manifest-v1",
        "frozen_before_full_k1_integration": True,
        "selected_inner": selected,
        "files": [{"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path)}
                  for path in paths],
    })
    print(json.dumps(long_decision, indent=2, sort_keys=True))
    return 0 if pass_long else 3


if __name__ == "__main__":
    raise SystemExit(main())
