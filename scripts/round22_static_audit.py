#!/usr/bin/env python3
"""Fail-closed source/manifest audit for the fixed Round 22 production path."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_global_gini_tree_unified_validation_round"


def text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    sources = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for folder in (ROOT / "src", ROOT / "include")
        for path in sorted(folder.rglob("*")) if path.suffix in {".cpp", ".hpp"})
    tailored_source = text("src/TailoredBCCplexApi.cpp")
    global_source = text("src/CplexBaseline.cpp") + tailored_source
    main_source = text("src/main.cpp")
    result_source = text("src/Result.cpp")
    manifests = {
        "S0": OUT / "stable_mainline_manifest.json",
        "S1": OUT / "candidate_mainline_manifest.json",
        "plain": OUT / "plain_cplex_manifest.json",
    }
    loaded = {key: json.loads(path.read_text(encoding="utf-8"))
              for key, path in manifests.items()}
    relaxation_marker = tailored_source.find(
        '"cplex_generic_relaxation_read_only_progress"')
    relaxation_start = tailored_source.rfind(
        "if (contextid == kContextRelaxation", 0, relaxation_marker)
    relaxation_prefix = tailored_source[relaxation_start:relaxation_marker]
    relaxation_snapshot_precedes_mutation = (
        relaxation_marker >= 0 and relaxation_start >= 0 and not any(
            token in relaxation_prefix
            for token in ("callbackaddusercuts(", "callbackmakebranch(",
                          "callbackrejectcandidate(", "callbackabort("))
    )
    checks = [
        ("certificate_policy_version", "round22-engineering-exact-v1" in sources,
         "Round 22 policy is compiled and serialized"),
        ("status101_authoritative_path", "native_engineering_exact_optimal" in sources,
         "status 101 has a dedicated engineering-exact class"),
        ("status102_not_upgraded", "native_tolerance_optimal_only" in sources,
         "status 102 remains tolerance-only"),
        ("model_gate_version", "round22-engineering-model-v1" in sources,
         "versioned model gate is compiled"),
        ("independent_verifier_fields", all(token in sources for token in (
            "original_solution_feasible", "original_objective_recomputed",
            "native_vs_recomputed_objective_residual")),
         "feasibility, recomputation, and mapping residual are distinct"),
        ("dense_read_only_contract", all(token in text("include/DenseProgress.hpp") for token in (
            "may_add_rows = false", "may_branch = false",
            "may_reject_candidate = false", "may_abort = false",
            "may_change_parameters = false", "may_call_auxiliary_optimizer = false")),
         "dense progress mutations are structurally disabled"),
        ("supported_progress_contexts", all(token in global_source for token in (
            "kContextGlobalProgress", "kContextLocalProgress",
            "cplex_generic_relaxation_read_only_progress",
            "callbackgetinfolong", "callbackgetinfodbl")),
         "documented generic progress contexts and info calls are used"),
        ("relaxation_snapshot_precedes_mutation",
         relaxation_snapshot_precedes_mutation,
         "Tailored relaxation progress snapshot occurs before any callback mutation"),
        ("buffered_single_flush", "std::ios::trunc" in text("src/DenseProgress.cpp")
         and "std::vector<DenseProgressEvent> events_" in text("include/DenseProgress.hpp"),
         "events buffer in memory and serialize once"),
        ("no_round22_seed_literal_in_production", not re.search(
            r"(?:310[12]|320[12]|330[12]|410[12]|420[12]|430[12])", sources),
         "no benchmark seed literal occurs in src/include"),
        ("no_round22_instance_label_in_production", not re.search(
            r"(?:moderate_seed|tight_T_seed|high_imbalance_seed)", sources, re.I),
         "no benchmark label occurs in src/include"),
        ("official_dispatch_fixed_by_cli", all(token in main_source for token in (
            'frontier_execution_mode == "global-gini-tree"',
            'opt.method == "cplex"')),
         "official commands select a named fixed path, not an inferred scale tier"),
        ("model_gate_rejects_instance_dispatch", "no_instance_dependent_option_resolution" in sources,
         "model gate explicitly audits dispatch absence"),
        ("native_bound_preserved", "native_CPXgetbestobjval" in sources
         and "strict_serialized_lower_bound_matches_native" in result_source + global_source,
         "serialized lower bound is checked against native evidence"),
        ("S0_fixed_flow", loaded["S0"].get("flow") == "round20-current"
         and loaded["S0"].get("instance_dependent_resolution") is False,
         "S0 always resolves F0"),
        ("S1_fixed_flow", loaded["S1"].get("flow") == "normalized-start-coupled"
         and loaded["S1"].get("instance_dependent_resolution") is False,
         "S1 always resolves F3"),
        ("plain_fixed", loaded["plain"].get("algorithm") == "plain_original_cplex_model"
         and loaded["plain"].get("instance_dependent_resolution") is False,
         "plain arm is fixed"),
        ("same_nonflow_settings", all(
            loaded["S0"].get(key) == loaded["S1"].get(key)
            for key in loaded["S0"] if key not in {"arm", "role", "flow"}),
         "S0 and S1 differ only by identity/role/flow"),
        ("complete_row_inventory", all(token in global_source for token in (
            "row_family_inventory", "callback_row_inventory",
            "selected_flow_rows_complete", "improving_gini_range_complete")),
         "complete static/callback/flow/Gini inventories feed model gate"),
        ("one_model_lifecycle", all(token in global_source for token in (
            "environment_count == 1", "problem_count == 1",
            "model_read_count == 1", "mipopt_count == 1")),
         "one-model lifecycle is checked"),
    ]
    rows = [{"audit_id": name, "status": "PASS" if passed else "FAIL",
             "detail": detail} for name, passed, detail in checks]
    with (OUT / "model_correctness_audit.csv").open(
            "w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["audit_id", "status", "detail"])
        writer.writeheader(); writer.writerows(rows)

    exact = list(rows)
    for arm, path in manifests.items():
        exact.append({"audit_id": f"{arm}_manifest_sha256",
                      "status": "PASS", "detail": sha(path)})
    with (OUT / "exactness_audit.csv").open(
            "w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["audit_id", "status", "detail"])
        writer.writeheader(); writer.writerows(exact)
    failed = [row for row in rows if row["status"] != "PASS"]
    print(f"static audit: {len(rows) - len(failed)} pass, {len(failed)} fail")
    if failed:
        for row in failed:
            print(f"FAIL {row['audit_id']}: {row['detail']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
