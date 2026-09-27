#!/usr/bin/env python3
"""Combine and classify the frozen Round 53 callback isolation matrix."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_f0_callback_isolation_round53"
ORDER = ("C0", "C1", "C2", "C3", "C4", "C5")
LABELS = {
    "C0": "c0-baseline", "C1": "c1-precrush-only",
    "C2": "c2-status-only", "C3": "c3-status-precrush",
    "C4": "c4-separator-dry-run", "C5": "c5-live"}


def truth(value: object) -> bool:
    return value is True or str(value).lower() in {"1", "true"}


def gm(values: list[float]) -> float:
    return math.exp(sum(math.log(max(1e-300, value)) for value in values) /
                    len(values)) if values else 1.0


def read_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def ratio(right: float, left: float) -> float:
    return (right + 1.0) / (left + 1.0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--c0", type=Path, required=True)
    parser.add_argument("--c1", type=Path, required=True)
    parser.add_argument("--c2", type=Path, required=True)
    parser.add_argument("--c3", type=Path, required=True)
    parser.add_argument("--c4", type=Path, required=True)
    parser.add_argument("--c5", type=Path, required=True)
    parser.add_argument("--cap", type=int, choices=(300, 1200), required=True)
    args = parser.parse_args()
    paths = {mode: getattr(args, mode.lower()) for mode in ORDER}
    rows: list[dict[str, str]] = []
    for mode in ORDER:
        current = read_rows(paths[mode])
        if any(row["round53_callback_mode"] != LABELS[mode]
               for row in current):
            raise RuntimeError(f"callback mode identity mismatch: {mode}")
        for row in current:
            row = dict(row)
            row["callback_isolation_mode"] = mode
            rows.append(row)
    expected = 24 if args.cap == 300 else 12
    if len(rows) != expected:
        raise RuntimeError(f"expected {expected} rows, found {len(rows)}")
    physical = OUT / f"callback_isolation_{args.cap}s.csv"
    fields = ["callback_isolation_mode"] + [
        field for field in rows[0] if field != "callback_isolation_mode"]
    write_csv(physical, fields, rows)
    by_key = {(row["state_id"], row["callback_isolation_mode"]): row
              for row in rows}
    states = sorted({row["state_id"] for row in rows})
    effects = (
        ("C1-C0", "PreCrush only", "C0", "C1"),
        ("C2-C0", "status-only MIPNODE registration", "C0", "C2"),
        ("C3-C2", "PreCrush conditional on status callback", "C2", "C3"),
        ("C3-C1", "status callback conditional on PreCrush", "C1", "C3"),
        ("C4-C3", "relaxation extraction and separator dry run", "C3", "C4"),
        ("C5-C4", "actual user-cut submission", "C4", "C5"))
    pair_rows: list[dict[str, object]] = []
    aggregate: dict[str, dict[str, float]] = {}
    for effect_id, component, left_mode, right_mode in effects:
        work_values, gi_values = [], []
        certificate_changes = 0
        for state in states:
            left, right = by_key[(state, left_mode)], by_key[(state, right_mode)]
            work_ratio = ratio(float(right["work"]), float(left["work"]))
            gi_ratio = ratio(float(right["gi_common_horizon"]),
                             float(left["gi_common_horizon"]))
            work_values.append(work_ratio)
            gi_values.append(gi_ratio)
            certificate_change = int(truth(right["certificate"])) - int(
                truth(left["certificate"]))
            certificate_changes += certificate_change
            pair_rows.append({
                "cap_seconds": args.cap, "state_id": state,
                "effect_id": effect_id, "component": component,
                "left_mode": left_mode, "right_mode": right_mode,
                "left_certificate": truth(left["certificate"]),
                "right_certificate": truth(right["certificate"]),
                "certificate_change": certificate_change,
                "left_work": left["work"], "right_work": right["work"],
                "shifted_work_ratio": work_ratio,
                "left_gi": left["gi_common_horizon"],
                "right_gi": right["gi_common_horizon"],
                "shifted_gi_ratio": gi_ratio})
        aggregate[effect_id] = {
            "work": gm(work_values), "gi": gm(gi_values),
            "cert": certificate_changes}
    pair_path = OUT / "callback_isolation_pairwise_effects.csv"
    prior = [] if args.cap == 300 or not pair_path.is_file() else read_rows(pair_path)
    combined = prior + pair_rows
    write_csv(pair_path, list(pair_rows[0]), combined)

    if args.cap == 300:
        precrush = max(aggregate["C1-C0"]["work"],
                       aggregate["C3-C2"]["work"])
        registration = aggregate["C2-C0"]["work"]
        separator = aggregate["C4-C3"]["work"]
        submission = aggregate["C5-C4"]["work"]
        values = {"precrush": precrush, "registration": registration,
                  "separator": separator, "submission": submission}
        maximum = max(values.values())
        if maximum <= 1.10 and all(value["cert"] == 0
                                   for value in aggregate.values()):
            classification = "callback_path_neutral"
            prose = "no material callback-path effect"
        elif precrush == maximum and precrush > 1.10:
            classification = "precrush_dominant_regression"
            prose = "PreCrush-dominant effect"
        elif registration == maximum and registration > 1.10:
            classification = "mipnode_registration_regression"
            prose = "MIPNODE-registration effect"
        elif separator == maximum and separator > 1.10:
            classification = "separator_overhead_regression"
            prose = "relaxation-extraction/separator overhead"
        elif submission == maximum and submission > 1.10:
            classification = "cut_submission_regression"
            prose = "actual-cut effect"
        else:
            classification = "mixed_callback_regression"
            prose = "mixed or inconclusive"
        certificate_ambiguous = any(
            len({truth(by_key[(state, mode)]["certificate"])
                 for mode in ORDER}) > 1 for state in ("D1", "D13"))
        decision = {
            "schema": "round53-callback-path-decision-v1",
            "classification": classification,
            "paper_classification": prose,
            "physical_rows_300s": len(rows),
            "correctness_failures": sum(
                not truth(row["engineering_gate"]) for row in rows),
            "false_certificates": sum(truth(row["false_certificate"])
                                      for row in rows),
            "c4_cut_submission_calls": sum(
                int(row["cut_submission_calls"]) for row in rows
                if row["callback_isolation_mode"] == "C4"),
            "c5_cut_submission_calls": sum(
                int(row["cut_submission_calls"]) for row in rows
                if row["callback_isolation_mode"] == "C5"),
            "aggregate_shifted_work_effects": {
                key: value["work"] for key, value in aggregate.items()},
            "certificate_classification_differs_on_D1_or_D13":
                certificate_ambiguous,
            "source_ambiguous": classification in {
                "mixed_callback_regression", "callback_source_inconclusive"},
            "extension_1200_required": certificate_ambiguous or
                classification == "mixed_callback_regression"}
        (OUT / "callback_path_decision.json").write_text(
            json.dumps(decision, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")
        (OUT / "callback_path_diagnosis.md").write_text(
            "# Callback-path diagnosis\n\n"
            f"The mandatory 300-second matrix contains {len(rows)} physical "
            f"rows. The frozen causal classification is **{prose}** "
            f"(`{classification}`). C4 made "
            f"{decision['c4_cut_submission_calls']} `GRBcbcut` calls; C5 made "
            f"{decision['c5_cut_submission_calls']}. The pairwise ledger "
            "separates PreCrush, status-only registration, separator dry-run, "
            "and actual submission effects.\n",
            encoding="utf-8")
        if decision["correctness_failures"] or decision["false_certificates"]:
            raise RuntimeError("callback correctness gate failed")
        print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
