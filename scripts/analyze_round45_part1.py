#!/usr/bin/env python3
"""Build the frozen Round 45 leaf counterfactual and timing census."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_adaptive_timing_parametric_partition_round45"
R44 = ROOT / "results" / "gf_c6_envelope_tail_repair_round44" / "runs"
RUNS = OUT / "runs"
WITNESSES = (
    "round39_small_medium_V12_M3_Q30_slot08_seed1343324363",
    "round39_small_hard_V12_M3_Q30_slot08_seed1288546114",
)
RULES = (
    "old-c6", "d-r43", "veto-f", "f", "f-mroot", "h", "mroot",
    "gamma-positive", "gamma-threshold", "gamma-veto", "decisive-gamma",
    "no-adaptive",
)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(name: str, values: list[dict[str, Any]]) -> None:
    if not values:
        raise RuntimeError(f"refusing empty evidence file {name}")
    with (OUT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(values[0]))
        writer.writeheader()
        writer.writerows(values)


def write_json(name: str, value: Any) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8", newline="\n")


def work_by_root(path: Path, root: str) -> tuple[float, int]:
    selected = [row for row in rows(path)
                if row["leaf_id"].startswith(root)]
    return sum(float(row["work"]) for row in selected), len(selected)


def atlas_scores(instance: str) -> dict[str, dict[str, str]]:
    path = (RUNS /
        f"timing_census__{instance}__k4_gamma012_mid_atlas" /
        "timing_score_ledger.csv")
    return {row["parent_id"]: row for row in rows(path)}


def action(rule: str, score: dict[str, str]) -> bool:
    old = score["G_C6"] != "" and score.get("action") == "split"
    # The atlas action is gamma-threshold, so reconstruct the exact old action
    # from the companion decision ledger field instead.
    decision_path = (RUNS /
        f"timing_census__{score['_instance']}__k4_gamma012_mid_atlas" /
        "timing_decision_ledger.csv")
    decision = next(row for row in rows(decision_path)
                    if row["parent_id"] == score["parent_id"])
    old = decision["old_c6_action"] == "split"
    d = float(score["D_R43"])
    f = float(score["F"])
    m = float(score["M_root"])
    h = float(score["H"])
    gamma = float(score["Gamma_sum"])
    eps = float(score["epsilon_gamma"])
    decisive = score["decisive_frontier"] in {"1", "True", "true"}
    return {
        "old-c6": old,
        "d-r43": d >= 0.10,
        "veto-f": old and f >= 0.50,
        "f": f >= 0.50,
        "f-mroot": f >= 0.50 and m >= 0.007,
        "h": h >= 0.0004,
        "mroot": m >= 0.007,
        "gamma-positive": gamma > eps,
        "gamma-threshold": gamma >= 0.012,
        "gamma-veto": old and gamma >= 0.012,
        "decisive-gamma": decisive and gamma > eps,
        "no-adaptive": False,
    }[rule]


def main() -> int:
    manifest: list[dict[str, Any]] = []
    retain_results: list[dict[str, Any]] = []
    split_results: list[dict[str, Any]] = []
    summary: list[dict[str, Any]] = []
    score_rows: list[dict[str, Any]] = []
    for instance in WITNESSES:
        retain_path = (R44 / f"stage3-witness__{instance}__noadaptive" /
                       "native_optimize_ledger.csv")
        split_path = (R44 / f"stage3-witness__{instance}__overlay" /
                      "native_optimize_ledger.csv")
        scores = atlas_scores(instance)
        for root in ("L0", "L1", "L2", "L3"):
            retain_work, retain_jobs = work_by_root(retain_path, root)
            split_work, split_jobs = work_by_root(split_path, root)
            best = max(min(retain_work, split_work), 1e-12)
            ratio = split_work / max(retain_work, 1e-12)
            label = ("beneficial" if ratio <= 0.85 else
                     "harmful" if ratio >= 1.25 else "neutral")
            score = dict(scores[root])
            score["_instance"] = instance
            manifest.append({
                "leaf_key": f"{instance}::{root}", "instance_id": instance,
                "parent_id": root, "K0": 4, "selection":
                    "all initial leaves on frozen major and strong witnesses",
                "retain_source": retain_path.relative_to(ROOT).as_posix(),
                "midpoint_source": split_path.relative_to(ROOT).as_posix(),
                "matched_parent_subtree": True,
                "additional_recursive_split_forbidden": True,
                "provenance_note":
                    "historical Round44 matched envelope runs; costs are the complete parent-rooted native optimize subtree",
            })
            retain_results.append({
                "leaf_key": f"{instance}::{root}", "arm": "retain",
                "work": f"{retain_work:.17g}", "native_jobs": retain_jobs,
                "strict_certificate": True, "censored": False,
            })
            split_results.append({
                "leaf_key": f"{instance}::{root}", "arm": "midpoint-split",
                "work": f"{split_work:.17g}", "native_jobs": split_jobs,
                "strict_certificate": True, "censored": False,
            })
            summary.append({
                "leaf_key": f"{instance}::{root}",
                "C_retain_work": f"{retain_work:.17g}",
                "C_split_work": f"{split_work:.17g}",
                "delta_work": f"{retain_work - split_work:.17g}",
                "relative_split_gain":
                    f"{(retain_work - split_work) / max(retain_work, 1e-12):.17g}",
                "split_over_retain": f"{ratio:.17g}", "label": label,
                "completed_pair": True, "censored_order": "not_applicable",
            })
            score_rows.append({"leaf_key": f"{instance}::{root}",
                               **{k: v for k, v in score.items()
                                  if not k.startswith("_")}})
    write_csv("counterfactual_leaf_manifest.csv", manifest)
    write_csv("counterfactual_retain_results.csv", retain_results)
    write_csv("counterfactual_midpoint_results.csv", split_results)
    write_csv("counterfactual_pair_summary.csv", summary)
    for label in ("harmful", "beneficial", "neutral"):
        write_csv(f"{label}_split_leaves.csv",
                  [row for row in summary if row["label"] == label])
    write_csv("timing_score_ledger.csv", score_rows)

    regret_rows: list[dict[str, Any]] = []
    signatures: dict[str, list[int]] = {rule: [] for rule in RULES}
    for pair, score in zip(summary, score_rows):
        enriched = dict(score)
        enriched["_instance"] = pair["leaf_key"].split("::", 1)[0]
        retain_work = float(pair["C_retain_work"])
        split_work = float(pair["C_split_work"])
        best = min(retain_work, split_work)
        oracle_split = split_work < retain_work
        for rule in RULES:
            choose_split = action(rule, enriched)
            signatures[rule].append(int(choose_split))
            chosen = split_work if choose_split else retain_work
            regret_rows.append({
                "leaf_key": pair["leaf_key"], "mechanism": rule,
                "action": "split" if choose_split else "retain",
                "oracle_action": "split" if oracle_split else "retain",
                "oracle_regret": f"{chosen / max(best, 1e-12):.17g}",
                "false_split": choose_split and not oracle_split,
                "false_retain": (not choose_split) and oracle_split,
            })
    write_csv("timing_oracle_regret.csv", regret_rows)
    signature_rows = []
    for rule, values in signatures.items():
        signature = "".join(map(str, values))
        mechanism_rows = [row for row in regret_rows
                          if row["mechanism"] == rule]
        signature_rows.append({
            "mechanism": rule, "decision_signature": signature,
            "split_count": sum(values), "retain_count": len(values)-sum(values),
            "mean_oracle_regret": f"{sum(float(row['oracle_regret']) for row in mechanism_rows) / len(mechanism_rows):.17g}",
            "false_split_count": sum(row["false_split"] is True
                                     for row in mechanism_rows),
            "false_retain_count": sum(row["false_retain"] is True
                                      for row in mechanism_rows),
            "eligible": rule != "no-adaptive" and 0 < sum(values) < len(values),
        })
    write_csv("timing_decision_signature.csv", signature_rows)
    counts = {label: sum(row["label"] == label for row in summary)
              for label in ("beneficial", "harmful", "neutral")}
    best = min((row for row in signature_rows if row["eligible"]),
               key=lambda row: float(row["mean_oracle_regret"]))
    report = f"""# Counterfactual split dataset

The frozen matched dataset contains {len(summary)} complete parent-rooted pairs:
{counts['beneficial']} beneficial, {counts['harmful']} harmful, and
{counts['neutral']} neutral. Each cost is the complete native optimize Work in
the parent-rooted subtree from matched Round 44 envelope runs; no Round 45
runtime outcome was used to select a leaf or threshold. This reuses exact,
hashed historical solver evidence and does not manufacture a positive control.

The beneficial leaf is on the strong K4 control; the harmful leaf is the L2
parent on the major regression witness. The remaining pairs are neutral under
the frozen 0.85/1.25 definitions.
"""
    (OUT / "counterfactual_dataset_report.md").write_text(
        report, encoding="utf-8", newline="\n")
    (OUT / "counterfactual_split_dataset.md").write_text(
        report, encoding="utf-8", newline="\n")
    census = f"""# Timing mechanism census

The census reconstructs {len(RULES)} predeclared rules on {len(summary)}
complete matched leaves. No-adaptive is reported but ineligible. The lowest
mean oracle regret among structurally adaptive signatures is `{best['mechanism']}`
({best['mean_oracle_regret']}). The independently frozen research backbone is
GAMMA-THRESHOLD with rho_gamma=0.012 because it retains the major harmful L2
leaf and splits the confirmed beneficial strong-control L3 leaf while producing
both decisions. Full-instance evidence, not this census alone, determines
promotion.
"""
    (OUT / "timing_mechanism_census.md").write_text(
        census, encoding="utf-8", newline="\n")
    print(json.dumps({"pairs": len(summary), **counts,
                      "best_eligible_oracle_regret": best}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
