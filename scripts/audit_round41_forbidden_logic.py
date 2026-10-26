#!/usr/bin/env python3
"""Fail-closed source scan for forbidden Round 41 dispatch behavior."""

from __future__ import annotations

import round41_common as common


TOKENS = (
    "instance.name", "instance_id", "scenario", "options.gurobi_seed",
    "hardware",
    "historical_winner", "winner_lookup", "BranchPriority", "GRBcbcut",
    "GRBcblazy", "GRB_CB_MIPNODE", "GRB_CB_MIPSOL",
)


def main() -> int:
    path = common.ROOT / "src" / "PaperExternalGiniTree.cpp"
    text = path.read_text(encoding="utf-8")
    start = text.index("SolveResult solveRound41StaticSegmentedGini(")
    end = text.index("SolveResult solvePaperExternalGiniTree(", start)
    mechanism = text[start:end]
    rows = []
    for token in TOKENS:
        count = mechanism.count(token)
        rows.append({
            "scope": "solveRound41StaticSegmentedGini",
            "forbidden_token": token,
            "occurrences": count,
            "passed": count == 0,
        })
    one_optimize = mechanism.count("backend->solve(request)") == 1
    rows.append({
        "scope": "solveRound41StaticSegmentedGini",
        "forbidden_token": "multiple_backend_solve_calls",
        "occurrences": mechanism.count("backend->solve(request)"),
        "passed": one_optimize,
    })
    common.write_csv(common.OUT / "forbidden_logic_scan.csv", rows)
    if not all(row["passed"] for row in rows):
        raise RuntimeError("Round 41 forbidden-logic scan failed")
    print({"checks": len(rows), "passed": True})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
