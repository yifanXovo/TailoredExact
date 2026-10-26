#!/usr/bin/env python3
"""Run bounded default-off and tau-equivalence sentinels for Round 52."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
R47 = ROOT / "results" / "gf_c6_adaptive_mass_contraction_round47"
OUT = ROOT / "results" / "gf_k1_tailored_cut_final_validation_round52"
RAW = OUT / "local_raw" / "tau_sentinels"
EXE = ROOT / "build" / "round52" / "ExactEBRP.exe"
CAP = 120

CASES = {
    "major": R47 / "runs" /
        "stage3_300s__round39_small_medium_V12_M3_Q30_slot08_seed1343324363__K1-AM" /
        "command.json",
    "high_imbalance": R47 / "runs" /
        "stage3_300s__high_imbalance_seed3201__K1-AM" / "command.json",
    "moderate": R47 / "runs" /
        "stage3_300s__moderate_seed3301__K1-AM" / "command.json",
}

PATH_FLAGS = {
    "--primal-heuristic-generation-log": "hga_generations.csv",
    "--progress-log": "progress.csv",
    "--process-phase-ledger": "process_phases.csv",
    "--heuristic-candidates-csv": "heuristic_candidates.csv",
    "--external-gini-artifact-dir": "external",
    "--log": "native.log",
    "--out": "result.json",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_value(command: list[str], flag: str, value: str) -> None:
    if flag not in command:
        command.extend([flag, value])
    else:
        command[command.index(flag) + 1] = value


def adapted_command(source: Path, run_dir: Path, tau: float | None) -> list[str]:
    payload = json.loads(source.read_text(encoding="utf-8"))
    command = [str(value) for value in payload["command"]]
    command[0] = str(EXE.resolve())
    for flag, name in PATH_FLAGS.items():
        replace_value(command, flag, str((run_dir / name).resolve()))
    replace_value(command, "--time-limit", str(CAP - 6))
    replace_value(command, "--process-wall-time-limit", str(CAP))
    replace_value(command, "--process-shutdown-margin", "5")
    executable_sha = sha(EXE)
    replace_value(command, "--round24-executable-sha256", executable_sha)
    replace_value(command, "--round24-manifest-executable-sha256", executable_sha)
    if tau is not None:
        replace_value(command, "--round47-c6-adaptive-mass", "adaptive-mass")
        replace_value(command, "--round47-c6-adaptive-mass-tau", format(tau, ".17g"))
        replace_value(command, "--round48-k1-amf", "off")
        replace_value(command, "--round49-k1-am-rc", "off")
    return command


def run_one(run_id: str, source: Path, tau: float | None) -> dict[str, object]:
    run_dir = RAW / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    result_path = run_dir / "result.json"
    ledger = run_dir / "external" / "adaptive_mass_decision_ledger.csv"
    # Completed sentinel evidence is immutable and may be reused after a later
    # unrelated sentinel command-line correction.
    if result_path.exists():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        decisions = []
        if ledger.exists():
            with ledger.open(encoding="utf-8", newline="") as src:
                decisions = list(csv.DictReader(src))
        return {
            "run_id": run_id,
            "tau": "default-off" if tau is None else format(tau, ".17g"),
            "process_cap_seconds": CAP,
            "runner_seconds": result.get("final_process_wall_time_seconds", 0.0),
            "return_code": result.get("process_return_code", 0),
            "watchdog_timeout": False,
            "result": result,
            "decisions": decisions,
            "command_path": (run_dir / "command.json").relative_to(ROOT).as_posix(),
            "result_path": result_path.relative_to(ROOT).as_posix(),
            "decision_ledger_path": ledger.relative_to(ROOT).as_posix(),
        }
    command = adapted_command(source, run_dir, tau)
    (run_dir / "command.json").write_text(
        json.dumps({"command": command, "source_command": source.relative_to(ROOT).as_posix(),
                    "process_cap_seconds": CAP}, indent=2) + "\n", encoding="utf-8")
    started = time.monotonic()
    with (run_dir / "stdout.log").open("w", encoding="utf-8") as stdout, \
         (run_dir / "stderr.log").open("w", encoding="utf-8") as stderr:
        try:
            completed = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr,
                                       timeout=CAP + 30, check=False)
            return_code = completed.returncode
            watchdog_timeout = False
        except subprocess.TimeoutExpired:
            return_code = -999
            watchdog_timeout = True
    runner_seconds = time.monotonic() - started
    result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.exists() else {}
    decisions = []
    if ledger.exists():
        with ledger.open(encoding="utf-8", newline="") as src:
            decisions = list(csv.DictReader(src))
    return {
        "run_id": run_id,
        "tau": "default-off" if tau is None else format(tau, ".17g"),
        "process_cap_seconds": CAP,
        "runner_seconds": runner_seconds,
        "return_code": return_code,
        "watchdog_timeout": watchdog_timeout,
        "result": result,
        "decisions": decisions,
        "command_path": (run_dir / "command.json").relative_to(ROOT).as_posix(),
        "result_path": result_path.relative_to(ROOT).as_posix(),
        "decision_ledger_path": ledger.relative_to(ROOT).as_posix(),
    }


def action_trace(run: dict[str, object]) -> list[tuple[str, str, str, str]]:
    return [(str(row["interval_id"]), str(row["parent_id"]),
             str(row["depth"]), str(row["selected_action"]))
            for row in run["decisions"]]  # type: ignore[index]


def summary_row(case: str, run: dict[str, object], equivalent: bool) -> dict[str, object]:
    result = run["result"]  # type: ignore[assignment]
    decisions = run["decisions"]  # type: ignore[assignment]
    root = next((row for row in decisions if row["interval_id"] == "L0"), None)
    return {
        "sentinel": case,
        "run_id": run["run_id"],
        "tau": run["tau"],
        "process_cap_seconds": run["process_cap_seconds"],
        "cap_respected": (not run["watchdog_timeout"] and
                          float(run["runner_seconds"]) <= CAP + 30),
        "runner_seconds": run["runner_seconds"],
        "return_code": run["return_code"],
        "watchdog_timeout": run["watchdog_timeout"],
        "status": result.get("status", "missing"),
        "strict_certificate": result.get("strict_certified_original_problem", False),
        "certificate_class": result.get("strict_certificate_class", "missing"),
        "lower_bound": result.get("lower_bound", ""),
        "verified_upper_bound": result.get("external_gini_tree_verified_upper_bound",
                                            result.get("upper_bound", "")),
        "gap": result.get("gap", ""),
        "work": result.get("external_gini_tree_work", ""),
        "final_process_seconds": result.get("final_process_wall_time_seconds", ""),
        "decision_count": len(decisions),
        "root_S_AM": "" if root is None else root["S_AM"],
        "root_action": "" if root is None else root["selected_action"],
        "paired_equivalence_pass": equivalent,
        "executable_sha256": sha(EXE),
        "command_path": run["command_path"],
        "result_path": run["result_path"],
        "decision_ledger_path": run["decision_ledger_path"],
    }


def main() -> None:
    if not EXE.exists():
        raise FileNotFoundError(EXE)
    RAW.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    rows: list[dict[str, object]] = []
    failures: list[str] = []

    for case, source in CASES.items():
        ref = run_one(f"{case}__tau_007915", source, 0.07915)
        candidate = run_one(f"{case}__tau_008", source, 0.08)
        equivalent = (action_trace(ref) == action_trace(candidate) and
                      len(action_trace(ref)) > 0)
        if not equivalent:
            failures.append(f"{case}:tau_action_trace")
        rows.extend((summary_row(case, ref, equivalent),
                     summary_row(case, candidate, equivalent)))

    implicit_source = R47 / "default_off_equivalence_runs" / "implicit" / "command.json"
    explicit_source = R47 / "default_off_equivalence_runs" / "explicit" / "command.json"
    implicit = run_one("default_off__implicit", implicit_source, None)
    explicit = run_one("default_off__explicit", explicit_source, None)
    keys = ("status", "strict_certified_original_problem", "strict_certificate_class",
            "external_gini_tree_failure_reason", "external_gini_tree_root_coverage_valid",
            "external_gini_tree_parent_child_coverage_valid",
            "external_gini_tree_initial_leaf_count", "external_gini_tree_final_leaf_count",
            "external_gini_tree_split_count", "external_gini_tree_declined_split_count")
    default_equal = all(implicit["result"].get(key) == explicit["result"].get(key)
                        for key in keys)
    if not default_equal:
        failures.append("default_off_equivalence")
    rows.extend((summary_row("default_off", implicit, default_equal),
                 summary_row("default_off", explicit, default_equal)))

    total_seconds = time.monotonic() - started
    if total_seconds > 1800:
        failures.append("runner_process_cap")
    for row in rows:
        if int(row["return_code"]) != 0 or not row["cap_respected"]:
            failures.append(f"{row['run_id']}:execution")
    with (OUT / "tau_008_runtime_results.csv").open(
            "w", encoding="utf-8", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    audit = {
        "schema": "round52-tau-sentinel-audit-v1",
        "row_count": len(rows),
        "tau_pair_count": len(CASES),
        "default_off_pair_count": 1,
        "all_tau_action_traces_equivalent": not any("tau_action_trace" in f for f in failures),
        "default_off_equivalent": default_equal,
        "process_seconds": total_seconds,
        "process_cap_seconds": 1800,
        "failures": failures,
        "executable_sha256": sha(EXE),
    }
    (OUT / "tau_008_sentinel_audit.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise RuntimeError(f"tau sentinel failures: {failures}")
    print(f"tau/default-off sentinels passed: {len(rows)} rows in {total_seconds:.1f}s")


if __name__ == "__main__":
    main()
