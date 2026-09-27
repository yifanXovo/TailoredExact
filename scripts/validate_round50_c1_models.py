#!/usr/bin/env python3
"""Prove each C1 model is its paired v0 model minus literal duplicates only."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path


def sections(path: Path) -> tuple[str, list[str], str]:
    text = path.read_text(encoding="utf-8")
    before, rest = text.split("Subject To\n", 1)
    rows_text, after = rest.split("Bounds\n", 1)
    rows = []
    for raw in rows_text.splitlines():
        line = raw.strip()
        if line:
            rows.append(re.sub(r"^c\d+:\s*", "", line))
    return before, rows, after


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-root", required=True, type=Path)
    parser.add_argument("--candidate-root", required=True, type=Path)
    parser.add_argument("--states", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    fields = [
        "state_id", "baseline_model_sha256", "candidate_model_sha256",
        "objective_section_identical", "bounds_and_types_identical",
        "baseline_rows", "candidate_rows", "declared_duplicates_omitted",
        "proved_duplicates_omitted", "new_or_strengthened_rows",
        "nonduplicate_rows_removed", "all_omitted_rows_zero_bound_mode_links",
        "feasible_set_and_objective_invariant", "status", "failure_reason",
    ]
    output = []
    for state in [value.strip() for value in args.states.split(",") if value.strip()]:
        base_dir = args.baseline_root / f"{state}__interval-mip-v0"
        candidate_dir = (
            args.candidate_root /
            f"{state}__c1-exact-duplicate-elimination")
        base_model = json.loads(
            (base_dir / "model_fingerprint.json").read_text(encoding="utf-8"))
        candidate_model = json.loads(
            (candidate_dir / "model_fingerprint.json").read_text(encoding="utf-8"))
        base_before, base_rows, base_after = sections(
            base_dir / "canonical_model.lp")
        candidate_before, candidate_rows, candidate_after = sections(
            candidate_dir / "canonical_model.lp")
        base_counter = Counter(base_rows)
        candidate_counter = Counter(candidate_rows)
        removed = base_counter - candidate_counter
        added = candidate_counter - base_counter
        proved_duplicate_count = 0
        nonduplicate_removed = 0
        only_zero_links = True
        for row, count in removed.items():
            surplus = max(0, base_counter[row] - 1)
            proved = min(count, surplus)
            proved_duplicate_count += proved
            nonduplicate_removed += count - proved
            if not re.fullmatch(r"[pd]_\d+_\d+ <= 0", row):
                only_zero_links = False
        declared = int(candidate_model["exact_duplicate_rows_omitted"])
        objective_same = base_before == candidate_before
        domains_same = base_after == candidate_after
        invariant = (
            objective_same and domains_same and not added and
            nonduplicate_removed == 0 and only_zero_links and
            proved_duplicate_count == declared and
            len(base_rows) - len(candidate_rows) == declared)
        output.append({
            "state_id": state,
            "baseline_model_sha256": base_model["sha256"],
            "candidate_model_sha256": candidate_model["sha256"],
            "objective_section_identical": str(objective_same).lower(),
            "bounds_and_types_identical": str(domains_same).lower(),
            "baseline_rows": len(base_rows),
            "candidate_rows": len(candidate_rows),
            "declared_duplicates_omitted": declared,
            "proved_duplicates_omitted": proved_duplicate_count,
            "new_or_strengthened_rows": sum(added.values()),
            "nonduplicate_rows_removed": nonduplicate_removed,
            "all_omitted_rows_zero_bound_mode_links": str(only_zero_links).lower(),
            "feasible_set_and_objective_invariant": str(invariant).lower(),
            "status": "pass" if invariant else "fail",
            "failure_reason": "none" if invariant else "model_delta_not_exact_dedup",
        })

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)
    if any(row["status"] != "pass" for row in output):
        raise RuntimeError("C1 model correctness audit failed")
    print(f"validated {len(output)} C1 model deltas")


if __name__ == "__main__":
    main()
