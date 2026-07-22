#!/usr/bin/env python3
"""Static contract tests for the distinct Round 28 C3 implementation."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPLICA = (ROOT / "src/ReplicaExternalGiniTree.cpp").read_text(encoding="utf-8")
GEOMETRY = (ROOT / "src/GiniFrontierGeometry.cpp").read_text(encoding="utf-8")
SCHEDULER = (ROOT / "src/ControllingLeafScheduler.cpp").read_text(encoding="utf-8")
MAIN = (ROOT / "src/main.cpp").read_text(encoding="utf-8")
RESULT = (ROOT / "src/Result.cpp").read_text(encoding="utf-8")
RUNNER = (ROOT / "scripts/run_round28_experiments.py").read_text(encoding="utf-8")
PROTOCOL = (ROOT / "results/gf_cplex_equivalent_gurobi_replica_round28/round28_protocol.md").read_text(encoding="utf-8")


checks = 0


def require(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        raise AssertionError(message)


def main() -> int:
    require("solveReplicaExternalGiniTree" in REPLICA, "C3 solver missing")
    require('"cplex-algorithm-replica"' in MAIN, "distinct CLI mode missing")
    require("solveReplicaExternalGiniTree" in MAIN, "C3 dispatch missing")
    require("solvePaperExternalGiniTree" in MAIN, "C2 dispatch was lost")
    require("solveExternalGiniTree" in MAIN, "C0 dispatch was lost")
    require("evaluatePaperLpSplitDecision" not in REPLICA,
            "C2 child-benefit gate leaked into C3")
    require("child_lp_bound_improvement" not in REPLICA.lower(),
            "child improvement gating leaked into C3")
    require("requestedQuantumSeconds" not in REPLICA,
            "time-quantum scheduler leaked into C3")
    require("planLaunch" not in REPLICA, "launch budget scheduler leaked into C3")
    require("externalLeafReadyForAdaptiveSplit" not in REPLICA,
            "attempt-count split rule leaked into C3")
    require("GRB_DBL_PAR_WORKLIMIT" not in REPLICA, "WorkLimit leaked into C3")
    require("GRB_DBL_PAR_NODELIMIT" not in REPLICA, "NodeLimit leaked into C3")
    require("SolutionLimit" not in REPLICA, "SolutionLimit leaked into C3")
    require("time_limit_seconds =" not in REPLICA,
            "per-event local time quantum leaked into C3")
    require("global_deadline_remaining_seconds" in REPLICA,
            "global deadline was not forwarded")
    require("warm_start_enabled = false" in REPLICA,
            "C3 warm start is not explicitly disabled")
    require("selector_variable_count = 0" in REPLICA,
            "zero selector count is not recorded")
    require("interval-selector" not in REPLICA.lower(),
            "selector formulation text leaked into C3 source")
    require("splitLeafAtomically" in REPLICA, "atomic replacement missing")
    require("inherited_complete_parent_lp_bound" in REPLICA,
            "child bound inheritance missing")
    require("selectNextCplexReplica" in REPLICA, "C3 best-bound selector missing")
    require("lhs->lower_bound < rhs->lower_bound" in SCHEDULER,
            "lower bound is not primary selection key")
    require("lhs_width < rhs_width" in SCHEDULER,
            "smaller-width tie key missing")
    require("lhs->split_depth > rhs->split_depth" in SCHEDULER,
            "greater-depth tie key missing")
    require("elapsed" not in SCHEDULER[SCHEDULER.index("selectNextCplexReplica"):SCHEDULER.index("tightenVerifiedCutoff")],
            "elapsed time participates in C3 selection")
    require("work" not in SCHEDULER[SCHEDULER.index("selectNextCplexReplica"):SCHEDULER.index("tightenVerifiedCutoff")].lower(),
            "Work participates in C3 selection")
    require("attempt" not in SCHEDULER[SCHEDULER.index("selectNextCplexReplica"):SCHEDULER.index("tightenVerifiedCutoff")].lower(),
            "attempt state participates in C3 selection")
    require("interior[interior.size() / 2]" in GEOMETRY,
            "accepted median initial breakpoint missing")
    require("legacyAdaptiveSplitEligible" in GEOMETRY,
            "accepted adaptive eligibility helper missing")
    require("split_factor != 2" in GEOMETRY, "binary contract gate missing")
    require("kInitialIntervalCount = 4" in REPLICA, "four-interval contract missing")
    require("kAdaptiveMaximumDepth = 8" in REPLICA, "depth-eight contract missing")
    require("kMinimumWidth = 1e-4" in REPLICA, "minimum-width contract missing")
    require("kCertificateTolerance = 1e-7" in REPLICA,
            "certificate tolerance contract missing")
    require(REPLICA.count('"inventory_conservation"') == 1,
            "global inventory family registry mismatch")
    require(REPLICA.count('"sp_product_estimator"') == 1,
            "SP estimator family registry mismatch")
    require("kGlobalFamilies.size()" in REPLICA,
            "global family count is not recorded")
    require("kIntervalFamilies.size()" in REPLICA,
            "interval family count is not recorded")
    require("buildRound18StaticIntervalRows" in REPLICA,
            "shared row factory is not used")
    require("writeCanonicalCompactModel" in REPLICA,
            "shared canonical model writer is not used")
    require("fileSha256(state.artifact.path)" in REPLICA,
            "immutable artifact identity check missing")
    require("model_count ==" in REPLICA and "model_free_count" in REPLICA,
            "model release symmetry gate missing")
    require("environment_count ==" in REPLICA and
            "environment_free_count" in REPLICA,
            "environment release symmetry gate missing")
    require("terminal_mip_leaf_count ==" in REPLICA,
            "terminal exactly-once lifecycle gate missing")
    require("evaluateExternalGiniTreeCertificate" in REPLICA,
            "global certificate gate missing")
    require("verifySolution(instance, best_routes" in REPLICA,
            "independent final incumbent verification missing")
    require("feasibility_consistency_gate" in REPLICA,
            "infeasibility contradiction gate missing")
    require("C3-REPLICA" in RUNNER, "runner lacks C3 arm")
    require("NO_IMPROVE_GENERATIONS = 2000" in RUNNER,
            "runner HGA stagnation rule mismatch")
    require("20260626" in RUNNER, "runner HGA seed mismatch")
    require("for repetition in (1, 2)" in RUNNER,
            "two fresh repeatability rows per instance missing")
    require("for arm in (\"P-GRB\", \"C3-REPLICA\")" in RUNNER,
            "complete Stage 2 paired arms missing")
    require("for arm in (\"S0-CPLEX\", \"C2-PAPER\", \"C3-REPLICA\")" in RUNNER,
            "Stage 3 anchor arms missing")
    require("OFFICIAL_BUDGET = 300" in RUNNER, "official cap mismatch")
    require("subprocess.run" in RUNNER and "timeout=budget + 15" in RUNNER,
            "runner emergency cap missing")
    require("environment[\"GRB_LICENSE_FILE\"]" in RUNNER,
            "license is not child-environment scoped")
    require("LICENSE.read" not in RUNNER and "sha256(LICENSE" not in RUNNER,
            "runner accesses license contents")
    require("No performance-driven changes" in PROTOCOL,
            "no-tuning freeze is not explicit")
    require("external_gini_tree_algorithm_arm" in RESULT,
            "C3 arm field is not serialized")
    require("external_gini_tree_certificate_tolerance" in RESULT,
            "C3 tolerance field is not serialized")
    require(checks >= 60, "Round 28 static gate must contain at least 60 checks")
    print(f"ROUND28_PROTOCOL_CHECKS={checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
