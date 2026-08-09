#!/usr/bin/env python3
"""Prepare and predeclare Round 35 without launching solver experiments."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable

import round35_common as common


R32 = common.ROOT / "results" / "gf_c6_long_run_validation_round32"
R34 = common.ROOT / "results" / "gf_c6_documentation_hga_round34"
STARTING_HEAD = "b1225b9e723516f736df69b5d79f367551ad78ff"
OBSERVED_LIVE_MAIN = "722b9b50cbd2155c43af1b2b511f55d579efb59d"
VALIDATED_SOLVER_SOURCE = "9fef376714dcc25205e677b82e2e473bc4f61398"
REPEAT_IDS = (
    "round32_multi_m_high_imbalance_V20_M2_seed1052706459",
    "tight_T_seed4101",
    "round32_multi_m_high_imbalance_V50_M2_seed910922492",
    "round31_sealed_moderate_V50_seed1112848618",
    "round32_multi_m_tight_T_V50_M4_seed1562257203",
)


def truth(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def option(command: list[Any], name: str) -> str:
    values = [str(value) for value in command]
    index = values.index(name)
    return values[index + 1]


def load_inventory() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in common.csv_rows(R32 / "round32_existing_instance_manifest.csv"):
        rows.append({
            "instance_id": source["instance_id"],
            "path": source["path"],
            "instance_sha256": source["instance_sha256"],
            "family": source["family"],
            "scenario": source["family"],
            "V": int(source["V"]),
            "M": int(source["M"]),
            "Q": int(source["Q"]),
            "T": float(source["T"]),
            "lambda": float(source["lambda"]),
            "origin": source["origin"],
            "historical_source_round": 32,
        })
    for source in common.csv_rows(R32 / "round32_multi_m_manifest.csv"):
        rows.append({
            "instance_id": source["instance_id"],
            "path": source["path"],
            "instance_sha256": source["sha256"],
            "family": source["stress_type"],
            "scenario": source["stress_type"],
            "V": int(source["V"]),
            "M": int(source["M"]),
            "Q": int(source["Q"]),
            "T": float(source["T"]),
            "lambda": float(source["lambda"]),
            "origin": "round32_multi_m",
            "historical_source_round": 32,
        })
    if len(rows) != 35 or len({row["instance_id"] for row in rows}) != 35:
        raise RuntimeError("Round 32 primary inventory is not exactly 35 unique rows")
    for row in rows:
        path = common.ROOT / row["path"]
        if not path.is_file() or common.sha256(path) != row["instance_sha256"]:
            raise RuntimeError(f"instance identity mismatch: {row['instance_id']}")
        row["bytes"] = path.stat().st_size
        row["frozen_before_round35_results"] = True
    common.write_csv(common.INSTANCE_MANIFEST, rows)
    return rows


def write_matrices(rows: list[dict[str, Any]]) -> None:
    by_name = {row["instance_id"]: row for row in rows}
    v50_names = [
        row["instance_id"]
        for row in common.csv_rows(R32 / "round32_stage3_freeze.csv")
    ]
    if len(v50_names) != 12 or any(by_name[name]["V"] != 50 for name in v50_names):
        raise RuntimeError("Round 32 V50 freeze is not exactly 12 V50 rows")
    stage1800 = [{
        "serial_order": index,
        **item,
        "process_cap_seconds": 1800,
        "source_matrix": "round32_stage1_plus_stage2_primary",
        "frozen_before_round35_results": True,
    } for index, item in enumerate(rows, start=1)]
    stage3600 = [{
        "serial_order": index,
        **by_name[name],
        "process_cap_seconds": 3600,
        "source_matrix": "round32_stage3_v50_independent",
        "fresh_independent_run": True,
        "frozen_before_round35_results": True,
    } for index, name in enumerate(v50_names, start=1)]
    repeats = []
    for index, name in enumerate(REPEAT_IDS, start=1):
        item = by_name[name]
        repeats.append({
            "serial_order": index,
            **item,
            "process_cap_seconds": 1800 if item["V"] == 20 else 3600,
            "selection_basis": (
                "predeclared_balance:V20_high,V20_tight,V50_M2,V50_M3,V50_M4"),
            "frozen_before_round35_results": True,
        })
    common.write_csv(common.MATRIX_1800, stage1800)
    common.write_csv(common.MATRIX_3600, stage3600)
    common.write_csv(common.REPEAT_FREEZE, repeats)

    official: list[dict[str, Any]] = []
    def add(stage: str, selected: Iterable[dict[str, Any]], repeat: int) -> None:
        for item in selected:
            cap = int(item["process_cap_seconds"])
            suffix = f"__repeat{repeat}" if repeat else ""
            official.append({
                "round_id": 35,
                "stage": stage,
                "serial_order": len(official) + 1,
                "run_id": (
                    f"{stage}__{item['instance_id']}__c6_simple_start"
                    f"{suffix}__{cap}s"),
                "instance_id": item["instance_id"],
                "arm": common.ARM,
                "startup_variant": "simple-start",
                "repetition": repeat,
                "process_cap_seconds": cap,
                "shutdown_margin_seconds": common.SHUTDOWN_MARGIN,
                "watchdog_seconds": cap + common.WATCHDOG_SEPARATION,
                "fresh_process": True,
                "frozen_before_round35_results": True,
            })
    add("matrix1800", stage1800, 0)
    add("v50_3600", stage3600, 0)
    add("repeat", repeats, 1)
    if len(official) != 52:
        raise RuntimeError(f"expected 52 new solver rows, got {len(official)}")
    common.write_csv(common.OFFICIAL_MATRIX, official)


def historical_run_map() -> tuple[dict[tuple[str, str, int], dict[str, str]],
                                  dict[str, dict[str, str]]]:
    official = common.csv_rows(R32 / "round32_official_matrix.csv")
    selected: dict[tuple[str, str, int], dict[str, str]] = {}
    for row in official:
        if row["stage_id"] not in {"stage1", "stage2", "stage3"}:
            continue
        selected[(row["instance_id"], row["arm"],
                  int(row["nominal_budget_seconds"]))] = row
    summaries = {
        row["run_id"]: row
        for row in common.csv_rows(R32 / "runner_row_summary.csv")
    }
    return selected, summaries


def fingerprints(rows: list[dict[str, Any]]) -> None:
    selected, _ = historical_run_map()
    values: dict[str, Any] = {}
    for item in rows:
        historical = selected[(item["instance_id"], "P-GRB", 1800)]
        result = common.load_json(R32 / "runs" / historical["run_id"] / "result.json")
        value = int(result.get("gurobi_model_fingerprint", 0))
        values[item["instance_id"]] = {
            "gurobi_model_fingerprint": value,
            "fingerprint_check_enabled": value != 0,
            "historical_source_round": 32,
            "historical_run_id": historical["run_id"],
            "instance_sha256": item["instance_sha256"],
        }
    common.write_json(common.FINGERPRINTS, {
        "schema": "round35-historical-fingerprint-freeze-v1",
        "instances": values,
        "no_new_plain_gurobi_run": True,
    })


def historical_compatibility(rows: list[dict[str, Any]]) -> None:
    selected, summaries = historical_run_map()
    output: list[dict[str, Any]] = []
    for budget, subset in (
        (1800, rows),
        (3600, [row for row in rows if row["V"] == 50]),
    ):
        for item in subset:
            for arm in ("C6-FROZEN", "P-GRB"):
                source = selected[(item["instance_id"], arm, budget)]
                run_dir = R32 / "runs" / source["run_id"]
                state = common.load_json(run_dir / "run_state.json")
                result = common.load_json(run_dir / "result.json")
                summary = summaries[source["run_id"]]
                command = [str(value) for value in state["command"]]
                identity = state.get("instance_sha256") == item["instance_sha256"]
                dimensions = (
                    int(state["V"]) == item["V"]
                    and int(state["M"]) == item["M"]
                    and int(state["Q"]) == item["Q"])
                budget_ok = (
                    int(state["nominal_budget_seconds"]) == budget
                    and int(state["actual_process_cap_seconds"]) == budget)
                version_ok = summary.get("solver_version") == "13.0.2"
                one_thread = all(option(command, name) == "1" for name in (
                    "--threads", "--mip-threads", "--cplex-threads",
                    "--compact-bc-threads"))
                timing_ok = "final_process_wall_time_seconds" in result
                certificate_ok = all(key in result for key in (
                    "strict_certified_original_problem",
                    "strict_certificate_class",
                    "strict_certificate_rejection_reason"))
                if arm == "C6-FROZEN":
                    contract_ok = (
                        option(command, "--frontier-intervals") == "4"
                        and option(command, "--external-gini-scheduling")
                        == "round31-nonblocking-native-bound"
                        and option(command, "--external-gini-lifecycle")
                        == "round31-open-native-bounded"
                        and option(command, "--frontier-adaptive-max-depth") == "8"
                        and option(command, "--frontier-adaptive-min-width") == "0.0001"
                        and "current rho split rule" in str(result.get(
                            "external_gini_tree_implementation_boundary", "")))
                    comparator = "C6-HGA-FULL"
                else:
                    contract_ok = (
                        "--plain-baseline" in command
                        and option(command, "--method") == "gurobi"
                        and option(command, "--gurobi-seed") == "0")
                    comparator = "P-GRB"
                checks = (identity, dimensions, budget_ok, version_ok,
                          one_thread, timing_ok, certificate_ok, contract_ok)
                output.append({
                    "round_id": 35,
                    "comparison_stage": "1800s" if budget == 1800 else "3600s_v50",
                    "instance_id": item["instance_id"],
                    "V": item["V"], "M": item["M"], "Q": item["Q"],
                    "scenario": item["scenario"],
                    "historical_comparator": comparator,
                    "historical_source_round": 32,
                    "historical_run_id": source["run_id"],
                    "historical_source_commit": state["source_commit"],
                    "historical_executable_sha256": state["executable_sha256"],
                    "historical_budget_seconds": budget,
                    "instance_sha256_match": identity,
                    "dimension_metadata_match": dimensions,
                    "nominal_and_process_budget_match": budget_ok,
                    "gurobi_13_0_2_match": version_ok,
                    "one_thread_match": one_thread,
                    "process_entry_timing_compatible": timing_ok,
                    "strict_certificate_semantics_compatible": certificate_ok,
                    "exact_or_plain_contract_compatible": contract_ok,
                    "comparison_compatibility": (
                        "compatible" if all(checks) else "unavailable"),
                    "historical_data_read_only": True,
                })
    if len(output) != 94:
        raise RuntimeError(f"expected 94 compatibility rows, got {len(output)}")
    common.write_csv(
        common.OUT / "historical_comparator_compatibility.csv", output)


def function_body(source: str, name: str) -> str:
    start = source.index(name)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise RuntimeError(f"unclosed function: {name}")


def frozen_equivalence() -> None:
    rows = []
    for name in (
        "evaluateC6FrontierDecision",
        "evaluateC6CurrentSplitDecision",
        "evaluatePaperTerminalMipDecision",
    ):
        path = "src/PaperExternalGiniTree.cpp"
        before = subprocess.check_output(
            ("git", "show", f"{VALIDATED_SOLVER_SOURCE}:{path}"),
            cwd=common.ROOT, text=True, encoding="utf-8")
        after = (common.ROOT / path).read_text(encoding="utf-8")
        first = hashlib.sha256(function_body(before, name).encode()).hexdigest()
        second = hashlib.sha256(function_body(after, name).encode()).hexdigest()
        rows.append({
            "component": name,
            "scope": "mathematical_decision_function",
            "validated_sha256": first,
            "round35_sha256": second,
            "identical": first == second,
        })
    for path in (
        "src/ControllingLeafScheduler.cpp",
        "include/ControllingLeafScheduler.hpp",
        "src/IntervalRowFactory.cpp",
        "include/IntervalRowFactory.hpp",
        "src/GurobiBaseline.cpp",
        "src/CplexBaseline.cpp",
        "src/PaperExternalGiniTree.cpp",
    ):
        before = subprocess.check_output(
            ("git", "show", f"{VALIDATED_SOLVER_SOURCE}:{path}"), cwd=common.ROOT)
        first = hashlib.sha256(before).hexdigest()
        second = common.sha256(common.ROOT / path)
        rows.append({
            "component": path,
            "scope": "frozen_exact_source_file",
            "validated_sha256": first,
            "round35_sha256": second,
            "identical": first == second,
        })
    common.write_csv(common.OUT / "frozen_c6_equivalence.csv", rows)


def preservation_manifest() -> None:
    raw = subprocess.check_output(
        ("git", "status", "--porcelain=v1", "-z", "--untracked-files=all"),
        cwd=common.ROOT)
    entries = raw.decode("utf-8", errors="surrogateescape").split("\0")
    excluded_names = {
        "scripts/round35_common.py", "scripts/prepare_round35.py",
        "scripts/freeze_round35.py", "scripts/run_round35_experiments.py",
        "scripts/run_round35_build_and_tests.py", "scripts/analyze_round35.py",
        "scripts/package_round35_evidence.py", "tests/round35_protocol_tests.py",
    }
    output = []
    for entry in entries:
        if len(entry) < 4:
            continue
        status, path_text = entry[:2], entry[3:].replace("\\", "/")
        if (path_text.startswith("results/gf_simple_start_qualification_round35/")
                or path_text.startswith("build_round35/")
                or path_text in excluded_names
                or (path_text.startswith("scripts/__pycache__/")
                    and "round35" in path_text)
                or (path_text.startswith("tests/__pycache__/")
                    and "round35" in path_text)):
            continue
        path = common.ROOT / path_text
        output.append({
            "status": status,
            "path": path_text,
            "exists": path.exists(),
            "bytes": path.stat().st_size if path.is_file() else "",
            "preserve_untouched": True,
        })
    if len(output) != 592:
        raise RuntimeError(
            f"starting worktree manifest changed: expected 592, got {len(output)}")
    common.write_csv(common.OUT / "preexisting_worktree_manifest.csv", output)


def write_documents() -> None:
    common.write_text(common.OUT / ".gitattributes", "* -text\n** -text\n")
    common.write_text(common.OUT / "source_of_truth.md", f"""# Round 35 source of truth

Round 35 starts at `{STARTING_HEAD}` on
`codex/round35-simple-start-full-qualification`. Live remote `main` was
observed as `{OBSERVED_LIVE_MAIN}` before preparation and is not modified.

The current source tree is authoritative for SIMPLE-START and the validated
C6 exact phase. The detailed algorithm basis is the read-only Round 34
`current_exact_algorithm.md`; Round 32 is authoritative for the 35-row
1,800-second and 12-row independent V50 3,600-second comparator matrices.
Round 34 is authoritative for the already qualified V10 SIMPLE evidence.

Historical raw evidence remains read-only. Every comparator enters derived
Round 35 tables only through `historical_comparator_compatibility.csv`.
No P-GRB or C6-HGA-FULL process is launched in Round 35.
""")
    common.write_text(common.OUT / "round35_protocol.md", """# Round 35 frozen protocol

## New solver rows

The only executable arm is `C6-SIMPLE-START`: the existing deterministic
three-mode greedy constructor, independent candidate verification, and the
unchanged C6 exact framework. Stage `matrix1800` contains the 35 Round 32
primary instances at a 1,800-second process cap. Stage `v50_3600` contains 12
fresh independent V50 processes at 3,600 seconds. Stage `repeat` contains two
V20 rows at 1,800 seconds and one V50 row for each of M=2,3,4 at 3,600
seconds. There is no continuation or solver-state resume.

All commands use Gurobi 13.0.2, Seed 0, one thread, a 15-second orderly
shutdown margin, and a watchdog separated from the nominal process cap by 90
seconds. Startup, verification, model construction, exact search, and final
certification are included in process-entry wall time.

## Frozen exact contract

Four initial intervals, all 15 strengthening families, complete LPs,
best-bound scheduling, launch-frozen next-frontier targets, requeue, lazy
child lookahead, `rho=0.01`, midpoint splitting, depth 8, width `1e-4`, atomic
coverage replacement, exact closure, and strict original-problem
certification are unchanged. Round 35 adds no C7 and no algorithm mechanism.

## Historical comparison

The Round 32 C6-FROZEN and P-GRB rows are never rerun. Compatibility requires
instance hash and dimensions, nominal/process budget, Gurobi 13.0.2,
one-thread execution, compatible C6/plain contract, process-entry timing, and
strict-certificate semantics. Incompatible comparisons are reported as
unavailable rather than substituted.

The predeclared repeat set balances V20 high/tight and V50 M2/M3/M4 before
Round 35 performance is observed. Performance does not dispatch startup by
instance. Qualification is decided only after correctness, full-matrix,
long-V50, repeatability, and structural interaction audits.
""")


def main() -> int:
    if subprocess.check_output(
            ("git", "rev-parse", "HEAD"), cwd=common.ROOT,
            text=True).strip() != STARTING_HEAD:
        raise RuntimeError("Round 35 preparation must start at recorded HEAD")
    if subprocess.check_output(
            ("git", "branch", "--show-current"), cwd=common.ROOT,
            text=True).strip() != "codex/round35-simple-start-full-qualification":
        raise RuntimeError("unexpected Round 35 branch")
    common.OUT.mkdir(parents=True, exist_ok=True)
    rows = load_inventory()
    write_matrices(rows)
    fingerprints(rows)
    historical_compatibility(rows)
    frozen_equivalence()
    preservation_manifest()
    write_documents()
    common.write_json(common.OUT / "round35_preparation_summary.json", {
        "round_id": 35,
        "starting_head": STARTING_HEAD,
        "observed_live_main": OBSERVED_LIVE_MAIN,
        "instances": len(rows),
        "matrix_1800_rows": 35,
        "matrix_3600_v50_rows": 12,
        "repeat_rows": len(REPEAT_IDS),
        "new_solver_rows": 52,
        "historical_comparator_rows": 94,
        "preexisting_worktree_rows": 592,
        "historical_comparator_processes_launched": 0,
        "frozen_before_official_results": True,
    })
    print(json.dumps(common.load_json(
        common.OUT / "round35_preparation_summary.json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
