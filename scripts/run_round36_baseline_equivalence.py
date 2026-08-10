#!/usr/bin/env python3
"""Run and audit the Round 36 frozen-C6 baseline-equivalence gate."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import round35_common as r35
import run_round25_experiments as licensed
import run_round31_experiments as r31


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_incumbent_decomposition_causal_round36"
RUNS = OUT / "baseline_equivalence_runs"
OLD_EXE = ROOT / "build_round35" / "official" / "gurobi" / "ExactEBRP.exe"
NEW_EXE = ROOT / "build_round36" / "official" / "gurobi" / "ExactEBRP.exe"
INSTANCE_ID = "V12_M1"
INSTANCE = ROOT / "reference" / "regen_candidate_V12_M1_average.txt"
PROCESS_CAP = 300


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def command(exe: Path, run_dir: Path, arm: str) -> list[str]:
    args = [str(exe), "--input", str(INSTANCE)]
    args.extend(r31.tailored_options(run_dir, PROCESS_CAP))
    for name, value in (
        ("--round34-c6-startup-variant", "hga-full"),
        ("--heuristic-candidates-csv", run_dir / "heuristic_candidates.csv"),
        ("--frontier-execution-mode", "external-gini-tree"),
        ("--external-gini-scheduling", "round31-nonblocking-native-bound"),
        ("--external-gini-artifact-dir", run_dir / "external"),
        ("--external-gini-backend", "gurobi"),
        ("--external-gini-lifecycle", "round31-open-native-bounded"),
        ("--external-gini-warm-start", False),
        ("--gurobi-home", "D:/gurobi1302/win64"),
        ("--gurobi-seed", 0),
        ("--gurobi-presolve", -1),
        ("--round24-executable-sha256", sha256(exe)),
        ("--round24-manifest-executable-sha256", sha256(exe)),
        ("--round24-expected-gurobi-model-fingerprint",
         r35.fingerprint_values()[INSTANCE_ID]),
        ("--log", run_dir / "native.log"),
        ("--out", run_dir / "result.json"),
    ):
        r35.add(args, name, value)
    if arm == "hh":
        r35.add(args, "--round36-c6-causal-arm", "hh")
        r35.add(args, "--round36-c6-split-normalization", "proof")
    return [str(value) for value in args]


def run_one(name: str, exe: Path, arm: str) -> None:
    run_dir = RUNS / name
    result_path = run_dir / "result.json"
    if result_path.is_file():
        return
    run_dir.mkdir(parents=True, exist_ok=False)
    args = command(exe, run_dir, arm)
    write_json(run_dir / "command.json", {
        "schema": "round36-baseline-equivalence-command-v1",
        "run_id": name,
        "executable_sha256": sha256(exe),
        "instance_sha256": sha256(INSTANCE),
        "process_cap_seconds": PROCESS_CAP,
        "command": args,
        "license_environment": "child_only_not_serialized",
    })
    environment = os.environ.copy()
    environment["GRB_LICENSE_FILE"] = str(licensed.LICENSE)
    with (run_dir / "console.stdout.log").open("wb") as stdout, \
         (run_dir / "console.stderr.log").open("wb") as stderr:
        completed = subprocess.run(
            args, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr,
            timeout=PROCESS_CAP + 60, check=False)
    if completed.returncode != 0 or not result_path.is_file():
        raise RuntimeError(f"baseline-equivalence run failed: {name} "
                           f"rc={completed.returncode}")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    return value[0] if isinstance(value, list) else value


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def select(source: list[dict[str, str]], fields: tuple[str, ...]) -> list[list[str]]:
    return [[row.get(field, "") for field in fields] for row in source]


def signature(run_dir: Path) -> dict[str, Any]:
    external = run_dir / "external"
    leaf = rows(external / "paper_leaf_ledger.csv")
    lp = rows(external / "lp_status_ledger.csv")
    events = rows(external / "paper_tree_events.csv")
    targets = rows(external / "native_target_ledger.csv")
    splits = rows(external / "split_decision_ledger.csv")
    result = load_json(run_dir / "result.json")

    initial = select(
        [row for row in leaf if not row.get("parent_id")],
        ("leaf_id", "depth", "gamma_L", "gamma_U", "base_lower_bound",
         "lower_bound", "status", "closure_source"))
    lp_decisions = select(
        lp, ("leaf_id", "parent_id", "depth", "gamma_L", "gamma_U",
             "terminal_valid", "optimal", "infeasible", "bound_available",
             "lower_bound", "native_status"))
    controlling = select(
        [row for row in events if row.get("event") in {
            "lp_complete", "parent_lp_requeue", "native_bound_target_reached",
            "atomic_split", "terminal_mip_complete", "lp_bound_prune"}],
        ("event", "leaf_id", "gamma_L", "gamma_U", "status", "global_lb",
         "verified_ub", "detail"))
    target_decisions = select(
        targets, ("phase_index", "leaf_id", "target_kind", "current_bound",
                  "target_bound", "other_open_min_bound", "verified_cutoff",
                  "status", "native_status", "native_bound", "target_reached",
                  "exact_closure", "requeued", "event_source"))
    split_decisions = select(
        splits, ("parent_id", "eligible", "decision_valid", "split",
                 "child_infeasibility_trigger", "strict_bound_trigger",
                 "normalized_disjunction_gain", "parent_native_bound_target",
                 "target_phase_required", "reason"))
    closures = select(
        [row for row in events if row.get("event") in {
            "terminal_mip_complete", "lp_bound_prune", "atomic_split"}],
        ("event", "leaf_id", "gamma_L", "gamma_U", "status", "detail"))
    final = {
        name: result.get(name) for name in (
            "status", "objective", "external_gini_tree_global_lower_bound",
            "external_gini_tree_verified_upper_bound",
            "strict_certified_original_problem", "strict_certificate_class",
            "strict_certificate_rejection_reason",
            "external_gini_tree_initial_leaf_count",
            "external_gini_tree_split_count",
            "external_gini_tree_terminal_mip_optimize_count",
            "external_gini_tree_root_coverage_valid",
            "external_gini_tree_parent_child_coverage_valid")
    }
    components = {
        "initial_intervals": initial,
        "lp_bounds": lp_decisions,
        "controlling_leaf_sequence": controlling,
        "native_target_sequence": target_decisions,
        "split_sequence": split_decisions,
        "closure_sequence": closures,
        "final_objective_certificate": final,
    }
    return {
        "component_hashes": {name: digest(value)
                             for name, value in components.items()},
        "components": components,
    }


def main() -> int:
    if not OLD_EXE.is_file() or not NEW_EXE.is_file():
        raise SystemExit("Round 35 and Round 36 executables are required")
    RUNS.mkdir(parents=True, exist_ok=True)
    runs = (
        ("frozen_round35_c6", OLD_EXE, "off"),
        ("round36_default_off", NEW_EXE, "off"),
        ("round36_hh", NEW_EXE, "hh"),
    )
    for name, exe, arm in runs:
        run_one(name, exe, arm)
    signatures = {name: signature(RUNS / name) for name, _, _ in runs}
    baseline_hashes = signatures["frozen_round35_c6"]["component_hashes"]
    audit_rows = []
    for component, baseline_hash in baseline_hashes.items():
        for candidate in ("round36_default_off", "round36_hh"):
            candidate_hash = signatures[candidate]["component_hashes"][component]
            audit_rows.append({
                "component": component,
                "candidate": candidate,
                "baseline_sha256": baseline_hash,
                "candidate_sha256": candidate_hash,
                "identical": baseline_hash == candidate_hash,
            })
    passed = all(row["identical"] for row in audit_rows)
    with (OUT / "baseline_equivalence_audit.csv").open(
            "w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(audit_rows[0]))
        writer.writeheader()
        writer.writerows(audit_rows)
    write_json(OUT / "baseline_equivalence_audit.json", {
        "schema": "round36-baseline-equivalence-v1",
        "passed": passed,
        "instance_id": INSTANCE_ID,
        "process_cap_seconds": PROCESS_CAP,
        "runs": {
            name: {
                "executable_sha256": sha256(exe),
                "result_sha256": sha256(RUNS / name / "result.json"),
                **signatures[name],
            } for name, exe, _ in runs
        },
        "comparisons": audit_rows,
    })
    report = [
        "# Round 36 baseline-equivalence audit", "",
        f"Gate passed: **{passed}**.", "",
        "A contemporaneous frozen Round 35 C6 executable, the new executable "
        "with every Round 36 control off, and explicit HH were run on V12_M1. "
        "Hashes exclude wall time and solver effort but include every "
        "mathematical decision field listed below.", "",
        "| component | default off | HH |", "|---|---|---|",
    ]
    for component in baseline_hashes:
        values = {row["candidate"]: row["identical"] for row in audit_rows
                  if row["component"] == component}
        report.append(
            f"| {component} | {values['round36_default_off']} | "
            f"{values['round36_hh']} |")
    report.extend(("", "A false result is a blocking Stage A error."))
    (OUT / "baseline_equivalence_audit.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"passed": passed, "comparisons": len(audit_rows)},
                     indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
