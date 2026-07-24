#!/usr/bin/env python3
"""Round 31 static protocol, serialization, and sealed-set checks."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/gf_nonblocking_gurobi_c6_round31"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def section(text: str, begin: str, end: str) -> str:
    start = text.index(begin)
    finish = text.index(end, start)
    return text[start:finish]


def main() -> int:
    source = (ROOT / "src/PaperExternalGiniTree.cpp").read_text(
        encoding="utf-8")
    header = (ROOT / "include/PaperExternalGiniTree.hpp").read_text(
        encoding="utf-8")
    main_source = (ROOT / "src/main.cpp").read_text(encoding="utf-8")
    result_source = (ROOT / "src/Result.cpp").read_text(encoding="utf-8")
    gurobi_source = (ROOT / "src/GurobiBaseline.cpp").read_text(
        encoding="utf-8")
    decision_code = section(
        source, "C6FrontierDecision evaluateC6FrontierDecision(",
        "PaperTerminalMipDecision evaluatePaperTerminalMipDecision(")

    require(
        "round31-nonblocking-native-bound" in source and
        "round31-open-native-bounded" in source and
        "round31-nonblocking-native-bound" in main_source,
        "C6 selectors are incomplete")
    require(
        "kRound31C6NormalizedSplitThreshold = 0.01" in source,
        "frozen rho is absent")
    require(
        "frontier_milestone_already_reached" in decision_code and
        "next_strict_bound" in decision_code,
        "finite parameter-free frontier transition is absent")
    require(
        "launch_exact_closure" in header and
        "run_child_bound_target" in header,
        "C6 current split states are incomplete")
    require(
        "c6_child_bound_reached_parent_requeued_no_forced_split" in source,
        "no-forced-split transition is absent")
    require(
        "WRITE_EXT_PATH(native_target_ledger_path)" in result_source,
        "native target ledger is not serialized")
    require(
        "round31_p_grb_hga_ablation" in gurobi_source and
        "gurobi_hga_start_submitted" in gurobi_source,
        "P-GRB-HGA incumbent ablation path is incomplete")

    # The pure mathematical predicates must contain no execution-dependent
    # inputs or instance dispatcher. Certificate tolerance is allowed.
    forbidden_predicate_patterns = {
        "elapsed time": r"\belapsed\b",
        "work": r"\bwork\b",
        "node": r"\bnode",
        "attempt": r"\battempt",
        "retry": r"\bretry",
        "family": r"\bfamily\b",
        "instance": r"\binstance\b",
        "seed": r"\bseed\b",
        "path": r"\bpath\b",
    }
    lowered = decision_code.lower()
    for label, pattern in forbidden_predicate_patterns.items():
        require(
            re.search(pattern, lowered) is None,
            f"execution-dependent {label} entered C6 predicates")

    required_docs = (
        "source_of_truth.md",
        "round31_protocol.md",
        "c6_design_decision.md",
        "c6_exactness_argument.md",
        "c6_state_machine.md",
        "c6_native_bound_target_contract.md",
        "c6_split_strategy.md",
        "c6_exact_closure_rule.md",
        "c6_incremental_reoptimization.md",
    )
    for name in required_docs:
        require((OUT / name).is_file(), f"missing protocol artifact: {name}")

    manifest_path = OUT / "round31_sealed_heldout_manifest.csv"
    rows = list(csv.DictReader(manifest_path.open(
        newline="", encoding="utf-8")))
    require(len(rows) == 6, "sealed held-out set must contain six rows")
    require(
        {(row["stress_type"], int(row["V"])) for row in rows} ==
        {(family, size) for family in
         ("high_imbalance", "moderate", "tight_T")
         for size in (20, 50)},
        "sealed family/size cross-product changed")
    for row in rows:
        path = ROOT / row["path"]
        require(path.is_file(), f"sealed instance missing: {path}")
        require(sha256(path) == row["sha256"], "sealed instance hash changed")
        material = (
            "893656f85fa6394dac787fee78baad2a52cdd2d2" +
            "|round31-sealed-heldout|" + row["stress_type"] +
            "|V" + row["V"])
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
        expected_seed = 1 + int(digest[:16], 16) % 2147483646
        require(digest == row["derivation_sha256"],
                "sealed derivation digest changed")
        require(expected_seed == int(row["seed"]),
                "sealed deterministic seed changed")

    # No generated protocol or source may contain common license-secret
    # markers. The license file itself is never accessed here.
    markers = (
        "LicenseID", "WLSAccessID", "WLSSecret", "TokenServer",
        "Computer ID", "HOSTID",
    )
    audited = [
        ROOT / "src/PaperExternalGiniTree.cpp",
        ROOT / "scripts/run_round31_development.py",
        *(OUT / name for name in required_docs),
    ]
    for path in audited:
        text = path.read_text(encoding="utf-8", errors="replace")
        require(
            not any(marker in text for marker in markers),
            f"sensitive marker in {path.relative_to(ROOT)}")

    print(json.dumps({
        "round31_protocol_checks": 21,
        "sealed_instances": len(rows),
        "forbidden_predicate_failures": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
