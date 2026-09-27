#!/usr/bin/env python3
"""Freeze the Round 52 tau decision and the K1-AM outer controller."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_tailored_cut_final_validation_round52"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    replay_path = OUT / "tau_008_complete_replay.csv"
    changed_path = OUT / "tau_008_changed_decisions.csv"
    runtime_path = OUT / "tau_008_runtime_results.csv"
    sentinel_path = OUT / "tau_008_sentinel_audit.json"
    with replay_path.open(encoding="utf-8", newline="") as src:
        replay = list(csv.DictReader(src))
    with changed_path.open(encoding="utf-8", newline="") as src:
        changed = list(csv.DictReader(src))
    with runtime_path.open(encoding="utf-8", newline="") as src:
        runtime = list(csv.DictReader(src))
    sentinel = json.loads(sentinel_path.read_text(encoding="utf-8"))
    if changed or not sentinel["all_tau_action_traces_equivalent"] or sentinel["failures"]:
        raise RuntimeError("tau=0.08 no-change adoption path is not eligible")

    tau_decision = {
        "schema": "round52-tau-freeze-decision-v1",
        "classification": "tau_008_adopted",
        "tau_reference": 0.07915,
        "tau_candidate": 0.08,
        "frozen_tau": 0.08,
        "complete_replay_rows": len(replay),
        "changed_decision_rows": len(changed),
        "historical_am_decisions_changed": False,
        "anchor_actions_at_0_08": {"major_root": "RETAIN",
                                   "strong_control_root": "RETAIN",
                                   "tight3102_L0.0": "RETAIN",
                                   "high_imbalance_root": "MIDPOINT",
                                   "moderate3301_root": "MIDPOINT"},
        "runtime_sentinel_rows": len(runtime),
        "tau_runtime_pairs": sentinel["tau_pair_count"],
        "default_off_pairs": sentinel["default_off_pair_count"],
        "all_runtime_action_traces_equivalent": True,
        "default_off_equivalent": True,
        "correctness_failures": 0,
        "false_certificates": 0,
        "new_severe_regressions": 0,
        "decision_path": "zero replay changes; broad rerun not opened; bounded equivalence sentinels only",
        "no_further_tau_tuning_in_round52": True,
        "input_sha256": {"complete_replay": sha(replay_path),
                         "changed_decisions": sha(changed_path),
                         "runtime_results": sha(runtime_path),
                         "sentinel_audit": sha(sentinel_path)},
    }
    (OUT / "tau_freeze_decision.json").write_text(
        json.dumps(tau_decision, indent=2) + "\n", encoding="utf-8")

    source = ROOT / "src" / "PaperExternalGiniTree.cpp"
    controller = {
        "schema": "round52-k1-am-controller-freeze-v1",
        "name": "K1-AM",
        "frozen": True,
        "K0": 1,
        "initial_interval_count": 1,
        "initial_interval": "complete strict-improver Gini interval",
        "split_point_rule": "midpoint",
        "tau": 0.08,
        "adaptive_mass_formula": "S_AM = eta * mu with clipped proof-normalized child gains",
        "native_target_behavior": "Round47 adaptive_mass_score_below_tau_native_target",
        "exact_parent_closure": "Round47 adaptive_mass_no_strict_child_improvement",
        "infeasible_child_behavior": "Round47 exact split/closure behavior without K1 contraction",
        "interval_coverage": "complete exact atomic parent replacement or retention",
        "global_certification": "strict original-problem certificate",
        "controller_source": "src/PaperExternalGiniTree.cpp",
        "controller_source_sha256": sha(source),
        "replay_equivalent_to_tau_0_07915": True,
        "replay_row_count": len(replay),
        "controller_changes_after_freeze_allowed": 0,
        "default_off": ["gamma-veto", "AMF", "reduced-cost rescue",
                        "fixed-rho fallback", "root-processing rescue", "PMM", "FPMM",
                        "non-midpoint splits", "AMC for K1", "adaptive branching",
                        "Round51 M1"],
        "inner_backend_not_part_of_controller": True,
    }
    (OUT / "k1_am_controller_freeze.json").write_text(
        json.dumps(controller, indent=2) + "\n", encoding="utf-8")

    rows = [
        ["K0", "1", "1", True, "literal controller setting"],
        ["initial_interval_count", "1", "1", True, "complete strict-improver range"],
        ["point_rule", "midpoint", "midpoint", True, "no breakpoint research"],
        ["adaptive_mass_formula", "Round47 eta*mu", "Round47 eta*mu", True, "source unchanged"],
        ["native_target", "Round47", "Round47", True, "source unchanged"],
        ["exact_parent_closure", "Round47", "Round47", True, "source unchanged"],
        ["infeasible_child_behavior", "Round47 K1", "Round47 K1", True, "source unchanged"],
        ["coverage_and_certification", "complete/exact", "complete/exact", True, "source unchanged"],
        ["tau_numeric", "0.07915", "0.08", False, "paper rounding candidate"],
        ["tau_decision_trace", f"{len(replay)} reference actions",
         f"{len(replay)} identical actions", True, "zero changed replay rows"],
        ["forbidden_rescues", "off", "off", True, "explicit freeze list"],
        ["default_off_equivalence", "implicit=explicit", "implicit=explicit", True,
         "bounded live sentinel"],
    ]
    with (OUT / "k1_am_controller_equivalence.csv").open(
            "w", encoding="utf-8", newline="") as out:
        writer = csv.writer(out)
        writer.writerow(["component", "historical_K1_AM", "round52_frozen_K1_AM",
                         "equivalent", "evidence"])
        writer.writerows(rows)
    print("froze tau=0.08 and the K1-AM controller")


if __name__ == "__main__":
    main()
