#!/usr/bin/env python3
"""Freeze the predeclared Round 36 causal panel from Round 35 evidence only.

This script deliberately has no knowledge of Round 36 run directories or result
schemas.  Refuse to overwrite the manifest by default so the selection cannot be
changed after a causal arm has been observed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUND35 = ROOT / "results" / "gf_simple_start_qualification_round35"
OUT = ROOT / "results" / "gf_incumbent_decomposition_causal_round36"
CLASSIFICATION = ROUND35 / "startup_pattern_classification.csv"
INSTANCE_MANIFEST = ROUND35 / "round35_instance_manifest.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def number(row: dict[str, str], name: str) -> float:
    return float(row[name])


def unique_choice(rows: list[dict[str, str]], description: str) -> dict[str, str]:
    if len(rows) != 1:
        raise RuntimeError(f"{description}: expected one row, found {len(rows)}")
    return rows[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    csv_path = OUT / "frozen_causal_panel.csv"
    json_path = OUT / "frozen_causal_panel.json"
    if not args.force and (csv_path.exists() or json_path.exists()):
        raise RuntimeError("Round 36 panel is already frozen; refusing to overwrite")

    rows = load_csv(CLASSIFICATION)
    instances = {row["instance_id"]: row for row in load_csv(INSTANCE_MANIFEST)}
    selected: list[tuple[dict[str, str], str]] = []

    # Mandatory regression rows named in the protocol.
    for instance_id in ("V12_M1", "V12_M2"):
        selected.append((unique_choice([
            row for row in rows
            if row["stage"] == "matrix1800" and row["instance_id"] == instance_id
        ], f"mandatory {instance_id}"), "mandatory_v12"))

    # The entire small pre-existing weaker-SIMPLE/slower class is retained.
    for row in sorted((row for row in rows
                       if row["stage"] == "matrix1800" and
                       row["pattern"] == "4_simple_ub_weaker_exact_phase_slower"),
                      key=lambda row: row["instance_id"]):
        selected.append((row, "all_weaker_simple_slower_rows"))

    # For each named scenario, retain the non-V12 weaker-SIMPLE/faster row with
    # the largest Round 35 final common-UB gap improvement.  Ties use ID order.
    for scenario in ("moderate", "high_imbalance", "tight_T"):
        candidates = [
            row for row in rows
            if row["stage"] == "matrix1800" and row["scenario"] == scenario
            and row["pattern"] == "3_simple_ub_weaker_exact_phase_faster"
            and row["instance_id"] not in {"V12_M1", "V12_M2"}
        ]
        candidates.sort(key=lambda row: (
            -(number(row, "full_common_ub_gap") -
              number(row, "simple_common_ub_gap")), row["instance_id"]))
        if not candidates:
            raise RuntimeError(f"no weaker-SIMPLE/faster candidate for {scenario}")
        selected.append((candidates[0],
                         f"largest_round35_gap_improvement_{scenario}"))

    # Long V50 regressions are chosen only from the already observed 3600 s
    # evidence: one largest regression per scenario, then a separate M=4 row.
    v50_regressions = [
        row for row in rows
        if row["stage"] == "v50_3600" and row["V"] == "50"
        and row["pattern"] == "5_simple_certification_or_final_gap_regression"
        and number(row, "simple_common_ub_gap") >
            number(row, "full_common_ub_gap") + 1e-12
    ]
    for scenario in ("moderate", "high_imbalance", "tight_T"):
        candidates = [row for row in v50_regressions
                      if row["scenario"] == scenario]
        candidates.sort(key=lambda row: (
            -(number(row, "simple_common_ub_gap") -
              number(row, "full_common_ub_gap")), row["instance_id"]))
        if not candidates:
            raise RuntimeError(f"no long V50 regression candidate for {scenario}")
        selected.append((candidates[0],
                         f"largest_v50_3600_gap_regression_{scenario}"))
    m4 = [row for row in v50_regressions if row["M"] == "4"]
    m4.sort(key=lambda row: (
        -(number(row, "simple_common_ub_gap") -
          number(row, "full_common_ub_gap")), row["instance_id"]))
    if not m4:
        raise RuntimeError("no long V50 M4 regression candidate")
    selected.append((m4[0], "largest_v50_3600_m4_gap_regression"))

    # Neutral controls: the sole similar-exact-phase row and the lexicographic
    # first exact startup-UB tie from the 1800 s matrix.
    selected.append((unique_choice([
        row for row in rows if row["stage"] == "matrix1800" and
        row["pattern"] == "2_simple_ub_weaker_exact_phase_similar"
    ], "neutral similar row"), "sole_weaker_simple_similar_row"))
    ties = sorted((row for row in rows if row["stage"] == "matrix1800" and
                   row["pattern"] == "1_simple_ub_not_weaker_simple_faster"),
                  key=lambda row: (int(row["V"]), int(row["M"]),
                                   row["instance_id"]))
    if not ties:
        raise RuntimeError("no exact startup-UB tie control")
    selected.append((ties[0], "smallest_v_m_exact_startup_ub_tie"))

    keys = [(row["stage"], row["instance_id"]) for row, _ in selected]
    if len(selected) != 14 or len(set(keys)) != len(keys):
        raise RuntimeError(
            f"predeclared panel must contain 14 unique rows, got {len(selected)}")

    output_rows: list[dict[str, object]] = []
    for ordinal, (row, basis) in enumerate(selected, 1):
        instance = instances[row["instance_id"]]
        input_path = ROOT / instance["path"]
        if sha256(input_path) != instance["instance_sha256"]:
            raise RuntimeError(f"instance hash mismatch: {row['instance_id']}")
        output_rows.append({
            "panel_ordinal": ordinal,
            "panel_row_id": f"r36_{ordinal:02d}_{row['instance_id']}",
            "round35_stage": row["stage"],
            "instance_id": row["instance_id"],
            "path": instance["path"],
            "instance_sha256": instance["instance_sha256"],
            "V": int(row["V"]),
            "M": int(row["M"]),
            "scenario": row["scenario"],
            "process_cap_seconds": 3600 if row["stage"] == "v50_3600" else 1800,
            "round35_pattern": row["pattern"],
            "selection_basis": basis,
            "round35_full_startup_ub": number(row, "full_startup_ub"),
            "round35_simple_startup_ub": number(row, "simple_startup_ub"),
            "round35_full_common_ub_gap": number(row, "full_common_ub_gap"),
            "round35_simple_common_ub_gap": number(row, "simple_common_ub_gap"),
            "frozen_before_round36_causal_results": True,
        })

    fieldnames = list(output_rows[0])
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    payload = {
        "schema": "exactebrp-round36-frozen-causal-panel-v1",
        "selection_observes_round36_results": False,
        "row_count": len(output_rows),
        "arms": ["HH", "SS", "BW-P", "BW-A"],
        "rho": 0.01,
        "initial_interval_count": 4,
        "round35_classification_path": str(CLASSIFICATION.relative_to(ROOT)),
        "round35_classification_sha256": sha256(CLASSIFICATION),
        "round35_instance_manifest_path": str(INSTANCE_MANIFEST.relative_to(ROOT)),
        "round35_instance_manifest_sha256": sha256(INSTANCE_MANIFEST),
        "selection_rule": [
            "mandatory V12_M1 and V12_M2 from matrix1800",
            "all matrix1800 weaker-SIMPLE/slower rows",
            "largest Round-35 final-gap improvement among weaker-SIMPLE/faster rows per moderate/high_imbalance/tight_T scenario",
            "largest 3600-second V50 final-gap regression per moderate/high_imbalance/tight_T scenario",
            "largest 3600-second V50 M4 final-gap regression",
            "sole matrix1800 weaker-SIMPLE/similar row",
            "smallest-(V,M,ID) matrix1800 exact startup-UB tie",
        ],
        "rows": output_rows,
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"froze {len(output_rows)} Round 36 rows in {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
