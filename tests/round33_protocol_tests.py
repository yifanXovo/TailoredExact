#!/usr/bin/env python3
"""Static and deterministic protocol checks for Round 33."""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import generate_round33_v10 as generator  # noqa: E402
import round33_common as common  # noqa: E402


class Checks:
    def __init__(self) -> None:
        self.count = 0

    def require(self, condition: bool, message: str) -> None:
        self.count += 1
        if not condition:
            raise AssertionError(message)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def option(command: list[str], name: str) -> str:
    return command[command.index(name) + 1]


def main() -> int:
    checks = Checks()
    manifest = rows(common.V10_MANIFEST)
    checks.require(len(manifest) == 18, "V10 manifest must contain 18 rows")
    cells = {(int(row["M"]), int(row["Q"]), row["scenario"])
             for row in manifest}
    expected = {(m, q, scenario) for m in (1, 2, 3) for q in (20, 30)
                for scenario in ("high_imbalance", "moderate", "tight_T")}
    checks.require(cells == expected, "V10 M/Q/scenario matrix mismatch")
    checks.require(len({row["seed"] for row in manifest}) == 18,
                   "derived seeds must be unique")
    for row in manifest:
        seed, digest, material = generator.derive_seed(
            int(row["M"]), int(row["Q"]), row["scenario"])
        checks.require(str(seed) == row["seed"], "seed derivation mismatch")
        checks.require(digest == row["derivation_sha256"],
                       "derivation digest mismatch")
        checks.require(material == row["derivation_material"],
                       "derivation material mismatch")
        path = ROOT / row["path"]
        checks.require(path.is_file() and sha256(path) == row["sha256"],
                       "instance hash mismatch")
        checks.require(int(row["V"]) == 10, "Round 33 generated V must be 10")
        checks.require(20 <= int(row["capacity_min"]) <= 50,
                       "capacity minimum outside realistic range")
        checks.require(20 <= int(row["capacity_max"]) <= 50,
                       "capacity maximum outside realistic range")
        checks.require(row["frozen_before_solver_results"] == "true",
                       "instance must be frozen before solver results")
    matrix = rows(common.MATRIX)
    checks.require(len(matrix) == 52, "official matrix must contain 52 rows")
    checks.require(sum(row["stage_id"] == "stage1" for row in matrix) == 36,
                   "Stage 1 must contain 36 rows")
    checks.require(sum(row["stage_id"] == "stage2" for row in matrix) == 4,
                   "Stage 2 must contain four rows")
    checks.require(sum(row["stage_id"] == "stage3" for row in matrix) == 12,
                   "Stage 3 must contain 12 rows")
    checks.require(len({row["run_id"] for row in matrix}) == 52,
                   "run IDs must be unique")
    checks.require(all(row["round_id"] == "33" for row in matrix),
                   "all matrix rows must identify Round 33")
    checks.require(all(row["actual_process_cap_seconds"] == "3600"
                       for row in matrix), "common process cap mismatch")
    repeat = rows(common.OUT / "round33_repeatability_freeze.csv")
    checks.require(len(repeat) == 6, "repeat freeze must contain six instances")
    checks.require(sum(row["Q"] == "20" for row in repeat) == 3,
                   "repeat Q20 balance mismatch")
    checks.require(sum(row["Q"] == "30" for row in repeat) == 3,
                   "repeat Q30 balance mismatch")

    item = common.inventory()[manifest[0]["instance_id"]]
    directory = common.ROOT / "build_round33" / "test_command"
    plain = common.plain_command(
        item, directory, 123456,
        executable_sha256_override="0" * 64)
    checks.require(option(plain, "--method") == "gurobi",
                   "plain arm must use Gurobi baseline")
    checks.require("--plain-baseline" in plain, "plain selector missing")
    checks.require("--gurobi-hga-start" not in plain,
                   "plain arm must not use HGA")
    checks.require(option(plain, "--threads") == "1",
                   "plain arm must use one thread")
    checks.require(option(plain, "--gurobi-seed") == "0",
                   "plain seed must be zero")
    checks.require(option(plain, "--gurobi-presolve") == "-1",
                   "plain presolve must remain automatic")
    checks.require(option(
        plain, "--round24-expected-gurobi-model-fingerprint") == "123456",
        "plain expected fingerprint missing")
    c6 = common.c6_command(item, directory, 123456)
    checks.require(option(c6, "--external-gini-scheduling") ==
                   "round31-nonblocking-native-bound",
                   "C6 scheduler changed")
    checks.require(option(c6, "--external-gini-lifecycle") ==
                   "round31-open-native-bounded", "C6 lifecycle changed")
    checks.require(option(c6, "--frontier-intervals") == "4",
                   "C6 initial intervals changed")
    checks.require(option(c6, "--frontier-adaptive-max-depth") == "8",
                   "C6 adaptive depth changed")
    checks.require(option(c6, "--frontier-adaptive-min-width") == "0.0001",
                   "C6 adaptive width changed")
    checks.require(option(c6, "--threads") == "1",
                   "C6 must use one thread")
    cpp = (ROOT / "src/GurobiBaseline.cpp").read_text(encoding="utf-8")
    checks.require("GRB_DBL_PAR_MIPGAP, 0.0" in cpp,
                   "zero relative MIP gap contract missing")
    checks.require("GRB_DBL_PAR_MIPGAPABS, 0.0" in cpp,
                   "zero absolute MIP gap contract missing")
    protocol = (common.OUT / "round33_protocol.md").read_text(encoding="utf-8")
    checks.require("final_process_wall_time_seconds" in protocol,
                   "process-entry primary timing field missing")
    normalized_protocol = " ".join(protocol.split()).lower()
    checks.require("no interpolation" in normalized_protocol,
                   "observed-only trace policy missing")
    checks.require("round 32" in normalized_protocol and
                   "never mixed" in normalized_protocol,
                   "round separation policy missing")
    for script in (
        "run_round33_preflight.py", "run_round33_experiments.py",
        "analyze_round33.py", "package_round33_evidence.py",
    ):
        text = (SCRIPTS / script).read_text(encoding="utf-8")
        checks.require("E:\\gurobi" not in text,
                       f"license path serialized in {script}")
    print(f"Round33ProtocolTests: {checks.count} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
