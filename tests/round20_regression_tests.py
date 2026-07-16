#!/usr/bin/env python3
"""Deterministic Python-side Round 20 exactness and evidence tests."""

from __future__ import annotations

import json
import math
import re
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import run_gf_global_gini_tree_regression_round as round20  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_lp_inventory_parser() -> None:
    model = """Minimize
 obj: G + 0.15 e_1
Subject To
 c1: G + e_1 >= 0.2
 c2: x_0_0_1 + x_0_1_0 = 2
Bounds
 0 <= G <= 1
 0 <= e_1 <= 2
Binaries
 x_0_0_1 x_0_1_0
End
"""
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "toy.lp"
        path.write_text(model, encoding="utf-8")
        audit = round20.lp_inventory(path)
    require(audit["variables"] == 4, "LP inventory variable count is wrong")
    require(audit["rows"] == 2, "LP inventory row count is wrong")
    require(audit["nonzeros"] == 4, "LP inventory nonzero count is wrong")
    require(audit["binary_variables"] == 2, "LP integrality classification is wrong")


def test_objective_serialization() -> None:
    checked = 0
    for path in (ROOT / "results" / round20.ROUND / "raw").glob("*.json"):
        data = round20.read_json(path)
        if not data.get("fresh_run"):
            continue
        objective = round20.number(data.get("objective"))
        gini = round20.number(data.get("gini", data.get("G")))
        penalty = round20.number(data.get("penalty", data.get("P")))
        if not all(math.isfinite(value) for value in (objective, gini, penalty)):
            continue
        require(abs(objective - (gini + 0.15 * penalty)) <=
                1e-7 * max(1.0, abs(objective)),
                f"objective identity failed in {path.name}")
        checked += 1
    require(checked > 0, "no fresh serialized objective was available")


def test_no_benchmark_dispatch() -> None:
    source = (ROOT / "src" / "TailoredBCCplexApi.cpp").read_text(encoding="utf-8")
    forbidden = ("tight_T_seed", "high_imbalance_seed", "moderate_seed",
                 "regen_candidate", "known_objective")
    require(not any(token in source for token in forbidden),
            "production global-tree source contains benchmark dispatch")
    script = (ROOT / "scripts" / "run_gf_global_gini_tree_regression_round.py").read_text(
        encoding="utf-8")
    require("--threads\", \"1" in script and "--cplex-threads\", \"1" in script,
            "experiment runner does not seal one-thread settings")


def test_objective_documents() -> None:
    paths = [ROOT / "README.md"]
    paths.extend((ROOT / "docs").glob("*.md"))
    paths.extend((ROOT / "Manuscript").rglob("*.tex"))
    wrong = re.compile(r"P\s*\+\s*(?:\\lambda|lambda)\s*\*?\s*G", re.IGNORECASE)
    hits = [str(path.relative_to(ROOT)) for path in paths
            if wrong.search(path.read_text(encoding="utf-8", errors="replace"))]
    require(not hits, "documents define P + lambda G: " + "|".join(hits))


def test_trace_estimate_arithmetic() -> None:
    current_hash = round20.sha256(round20.EXE)
    checked = 0
    for result_path in round20.RAW.glob("*.json"):
        data = round20.read_json(result_path)
        if not data.get("global_gini_tree_attempted"):
            continue
        run_id = str(data.get("round20_run_id", result_path.stem))
        command = round20.read_json(round20.paths(run_id)["command"])
        if command.get("executable_sha256") != current_hash:
            continue
        for row in round20.read_csv(round20.paths(run_id)["topology"]):
            parent = round20.number(row.get("parent_relaxation"))
            low = round20.number(row.get("lower_estimate"))
            high = round20.number(row.get("upper_estimate"))
            require(all(math.isfinite(value) for value in (parent, low, high)),
                    f"nonfinite estimate trace in {run_id}")
            require(low + 1e-8 >= parent and high + 1e-8 >= parent,
                    f"child estimate fell below parent in {run_id}")
            if row.get("estimate_mode") == "parent-copy":
                require(abs(low - parent) <= 1e-8 and abs(high - parent) <= 1e-8,
                        f"parent-copy did not copy parent relaxation in {run_id}")
            checked += 1
    require(checked > 0, "no current-executable topology row was available")


def test_no_false_optimality() -> None:
    for path in round20.RAW.glob("*.json"):
        data = round20.read_json(path)
        if data.get("global_gini_tree_optimality_accepted"):
            require(round20.number(data.get("gap"), 1.0) <= 1e-8,
                    f"false positive-gap optimality in {path.name}")
            require(bool(data.get("global_gini_tree_incumbent_verified")),
                    f"unverified optimality in {path.name}")


def main() -> int:
    tests = (
        test_lp_inventory_parser,
        test_objective_serialization,
        test_no_benchmark_dispatch,
        test_objective_documents,
        test_trace_estimate_arithmetic,
        test_no_false_optimality,
    )
    for test in tests:
        test()
    print(f"Round20RegressionTests: {len(tests)} groups passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
