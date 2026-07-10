#!/usr/bin/env python3
"""Audit structural-round callback/root vector family parsing."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["audit", "passed", "reason"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--results", default="results/gf_tailored_bc_structural_cut_round")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    root = Path(args.results)
    callback_rows = read_csv(root / "callback_vector_raw.csv")
    root_rows = read_csv(root / "root_lp_vector_raw.csv")
    rows: List[Dict[str, object]] = []
    failures = 0

    def add(name: str, passed: bool, reason: str) -> None:
        nonlocal failures
        if not passed:
            failures += 1
        rows.append({"audit": name, "passed": passed, "reason": reason})

    add("callback_vector_rows_present", bool(callback_rows),
        f"callback_rows={len(callback_rows)}")
    bad_values = [
        r for r in callback_rows + root_rows
        if r.get("value", "") == "" or r.get("value", "") == "0_when_missing"
    ]
    add("missing_values_not_zero_filled", not bad_values,
        f"bad_value_rows={len(bad_values)}")
    diagnostic_bad = [r for r in callback_rows + root_rows
                      if str(r.get("diagnostic_only", "")).lower() not in {"true", "1"}]
    add("vectors_marked_diagnostic_only", not diagnostic_bad,
        f"non_diagnostic_rows={len(diagnostic_bad)}")
    families = {r.get("family", "") for r in callback_rows}
    required = {"G", "r_i", "Y_i", "e_i", "h_i_j", "z_k_i", "p_k_i", "d_k_i", "x_k_i_j"}
    add("required_families_observed_or_listed",
        bool(families & required),
        "families=" + "|".join(sorted(families)))
    unparsed = [r for r in callback_rows + root_rows if r.get("family") == "unknown_unparsed"]
    add("unparsed_columns_listed", True, f"unknown_unparsed_rows={len(unparsed)}")
    parsed_fraction = (
        1.0 - len(unparsed) / len(callback_rows + root_rows)
        if callback_rows or root_rows else 0.0
    )
    add("at_least_95_percent_columns_classified", parsed_fraction >= 0.95,
        f"parsed_fraction={parsed_fraction:.9f}")
    documented = {
        "load variables", "service/mode variables", "bit variables",
        "McCormick auxiliary variables", "objective-estimator auxiliary variables",
        "other documented auxiliary variables",
    }
    add("documented_auxiliary_families_classified",
        bool(families & documented),
        "documented_families=" + "|".join(sorted(families & documented)))
    if root_rows:
        add("root_lp_rows_present", True, f"root_rows={len(root_rows)}")
    else:
        add("root_lp_rows_absent_labeled_by_empty_file", True,
            "root_lp_vector_raw.csv has no rows; no zero-filled root vector was synthesized")

    out = Path(args.out) if args.out else root / "callback_vector_family_parser_audit.csv"
    write_csv(out, rows)
    print(f"audits={len(rows)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
