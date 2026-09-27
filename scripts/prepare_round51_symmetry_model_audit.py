#!/usr/bin/env python3
"""Combine the two all-state M1 symmetry row-delta validations."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_tight_big_m_sparse_branching_round51"


def main() -> None:
    affected = {row["state_id"]: row["big_m_affected"] for row in csv.DictReader(
        (EVIDENCE / "big_m_model_delta_audit.csv").open(
            newline="", encoding="utf-8-sig"))}
    rows: list[dict[str, str]] = []
    for name in ("symmetry_m1_s1_model_raw.csv",
                 "symmetry_m1_s1r_model_raw.csv"):
        for row in csv.DictReader((EVIDENCE / name).open(
                newline="", encoding="utf-8-sig")):
            state = row["state_id"]
            output = dict(row)
            output["big_m_affected"] = affected[state]
            output["baseline_policy"] = "m1-tight-big-m-v0"
            output["d13_mandatory_negative_control"] = str(
                state == "D13").lower()
            rows.append(output)
    if len(rows) != 46 or any(row["status"] != "pass" for row in rows):
        raise RuntimeError("M1 symmetry model audit is incomplete or failed")
    ordered = [
        "baseline_policy", "candidate_policy", "state_id",
        "big_m_affected", "d13_mandatory_negative_control",
    ] + [name for name in rows[0]
         if name not in {"baseline_policy", "candidate_policy", "state_id",
                         "big_m_affected", "d13_mandatory_negative_control"}]
    with (EVIDENCE / "symmetry_m1_model_correctness.csv").open(
            "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ordered,
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print("M1 symmetry all-state model correctness passed (46/46)")


if __name__ == "__main__":
    main()
