#!/usr/bin/env python3
"""Static freeze checks for the Round 32 no-C7 validation protocol."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_c6_long_run_validation_round32"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    protocol = (OUT / "round32_protocol.md").read_text(encoding="utf-8")
    source = (
        ROOT / "src" / "PaperExternalGiniTree.cpp"
    ).read_text(encoding="utf-8")
    require("C7" not in source, "Round 32 introduced C7 source")
    require(
        'kRound31C6NormalizedSplitThreshold = 0.01' in source,
        "C6 rho changed")
    for token in (
        "round31-nonblocking-native-bound",
        "round31-open-native-bounded",
        "frontier_intervals",
        "frontier_adaptive_max_depth != 8",
    ):
        require(token in source, f"frozen C6 source token missing: {token}")
    require(
        "does not develop C7" in protocol.replace("\n", " "),
        "no-C7 protocol missing")
    require(
        "experiment-row resume, never native solve-state resume"
        in protocol.replace("\n", " "),
        "resume semantics are not explicit")

    existing = rows(OUT / "round32_existing_instance_manifest.csv")
    multi = rows(OUT / "round32_multi_m_manifest.csv")
    stage3 = rows(OUT / "round32_stage3_freeze.csv")
    matrix = rows(OUT / "round32_official_matrix.csv")
    stage0 = rows(OUT / "round32_stage0_matrix.csv")
    require(len(existing) == 23, "existing instance count changed")
    require(len(multi) == 12, "multi-M instance count changed")
    require(len(stage3) == 12, "Stage 3 V50 count changed")
    require(len(matrix) == 133, "official/reference matrix count changed")
    require(len(stage0) == 12, "Stage 0 matrix count changed")
    require(
        {(int(row["V"]), int(row["M"]), row["stress_type"])
         for row in multi}
        == {(v, m, family)
            for v in (20, 50)
            for m in (2, 4)
            for family in ("high_imbalance", "moderate", "tight_T")},
        "multi-M coverage changed")
    require(
        all(int(row["Q"]) == 30 for row in multi),
        "multi-M Q is not uniformly 30")
    require(
        all(
            digest(ROOT / row["path"]) == row["sha256"]
            and row["frozen_before_solver_results"].lower() == "true"
            for row in multi),
        "multi-M instance freeze failed")
    counts = {}
    for row in matrix:
        counts[row["stage_id"]] = counts.get(row["stage_id"], 0) + 1
        require(row["round_id"] == "32", "matrix round id changed")
        require(
            int(row["emergency_watchdog_seconds"])
            - int(row["actual_process_cap_seconds"]) == 90,
            "watchdog separation changed")
    require(
        counts == {
            "stage1": 46,
            "stage2": 24,
            "stage3": 24,
            "stage4": 16,
            "stage5": 7,
            "repeatability": 16,
        },
        f"official stage counts changed: {counts}")
    require(
        all(int(row["V"]) == 50 for row in stage3),
        "non-V50 row entered Stage 3")
    require(
        all(int(row["V"]) <= 50 for row in existing + multi),
        "V>50 entered Round 32")
    print("Round32ProtocolTests: 25 checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
