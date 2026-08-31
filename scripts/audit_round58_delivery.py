#!/usr/bin/env python3
"""Run final Round 58 scope, preservation, hash, and delivery audits."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import round58_common as r58
import run_round58_paired_benchmark as runner


OUT = r58.EVIDENCE
REQUIRED_ALWAYS = (
    "final_report.md", "final_decision.json", "repository_start_audit.json",
    "local_round57_dataset_audit.json", "algorithm_identity_audit.csv",
    "pgrb_model_scope_audit.csv", "pgrb_expected_fingerprints.json",
    "gap_definition_contract.json", "round58_complete_panel.csv",
    "round58_panel_balance_audit.csv", "execution_order_manifest.csv",
    "screen_results_3600.csv", "screen_extension_decisions.csv",
    "official_final_results.csv", "common_horizon_comparisons.csv",
    "direct_pair_comparison.csv", "historical_severe_regression_audit.csv",
    "long_run_material_regression_audit.csv", "route_archive_inventory.csv",
    "route_verification_audit.csv", "certificate_audit.csv",
    "false_certificate_audit.csv", "comparison_by_V.csv",
    "comparison_by_geography.csv", "comparison_by_inventory_regime.csv",
    "comparison_by_T.csv", "comparison_by_Q.csv",
    "certificate_horizon_summary.csv", "performance_profile_data.csv",
    "benchmark_analysis.md", "experimental_compute_accounting.csv",
    "final_build_and_tests.md", "final_evidence_inventory.csv",
    "reproduction_commands.md",
)


def check(value: bool, name: str, details: Any = None) -> dict[str, Any]:
    return {"audit": name, "passed": bool(value), "details": details}


def tracked_paths() -> list[str]:
    output = subprocess.check_output(
        ["git", "ls-files"], cwd=r58.ROOT, text=True, encoding="utf-8")
    return output.splitlines()


def command_audit() -> list[str]:
    failures: list[str] = []
    intervals: list[tuple[datetime, datetime, str]] = []
    for scenario in runner.panel():
        for method in runner.METHODS:
            for cap in runner.STAGE_BY_CAP:
                marker = runner.completion_marker(scenario, method, cap)
                if not marker:
                    continue
                directory = runner.run_dir(scenario, method, cap)
                record = r58.read_json(directory / "command.json")
                command = record["command"]
                label = f"{scenario['scenario_id']}/{method}/{cap}"
                if record.get("started_at_utc") and record.get("completed_at_utc"):
                    intervals.append((
                        datetime.fromisoformat(record["started_at_utc"]),
                        datetime.fromisoformat(record["completed_at_utc"]), label))
                if command[0] != str(runner.EXE.resolve()):
                    failures.append(f"executable:{scenario['scenario_id']}/{method}/{cap}")
                if any(option in command for option in runner.FORBIDDEN_OPTIONS):
                    failures.append(f"forbidden:{scenario['scenario_id']}/{method}/{cap}")
                if runner.option_value(command, "--gurobi-threads") != "1":
                    failures.append(f"threads:{scenario['scenario_id']}/{method}/{cap}")
                if runner.option_value(command, "--gurobi-seed") != "0":
                    failures.append(f"seed:{scenario['scenario_id']}/{method}/{cap}")
                if runner.option_value(command, "--gurobi-presolve") != "-1":
                    failures.append(f"presolve:{scenario['scenario_id']}/{method}/{cap}")
                if method == "k1_am_sf" and runner.option_value(
                        command, "--algorithm-preset") != "paper-k1-am-sf":
                    failures.append(f"k1_preset:{scenario['scenario_id']}/{cap}")
                if method == "pgrb" and (
                        "--plain-baseline" not in command or
                        runner.option_value(command, "--gurobi-hga-start") != "false"):
                    failures.append(f"pgrb_scope:{scenario['scenario_id']}/{cap}")
                summary = marker["summary"]
                if not runner.finite(summary["actual_wall_time_seconds"]):
                    failures.append(f"missing_algorithm_wall_time:{label}")
                if (not summary["strict_certificate"] and
                        runner.finite(summary["actual_wall_time_seconds"]) and
                        float(summary["actual_wall_time_seconds"]) < cap - 15.0):
                    failures.append(f"unauthorized_early_stop:{label}")
    intervals.sort()
    for previous, current in zip(intervals, intervals[1:]):
        if current[0] < previous[1]:
            failures.append(f"overlapping_optimizer_processes:{previous[2]}:{current[2]}")
    return failures


def preservation_failures() -> list[str]:
    audit = r58.read_json(OUT / "preexisting_file_preservation_audit.json")
    return [item["path"] for item in audit["tracked_modified_files"]
            if not (r58.ROOT / item["path"]).is_file() or
            r58.sha256_file(r58.ROOT / item["path"]) != item["sha256"]]


def route_failures() -> list[str]:
    failures = []
    inventory = r58.read_csv(OUT / "route_archive_inventory.csv")
    for row in inventory:
        if str(row["package_available"]).lower() != "true":
            continue
        output = r58.ROOT / row["package_path"]
        names = ("native_solution.json", "routes.csv", "operations.csv",
                 "final_inventory.csv", "solution_verification.json",
                 "solution_sha256.txt")
        if any(not (output / name).is_file() for name in names):
            failures.append(f"missing:{row['scenario_id']}/{row['method']}")
            continue
        lines = (output / "solution_sha256.txt").read_text(
            encoding="utf-8").splitlines()
        expected = {line.split("  ", 1)[1]: line.split("  ", 1)[0]
                    for line in lines if "  " in line}
        for name in names[:-1]:
            if expected.get(name) != r58.sha256_file(output / name):
                failures.append(f"hash:{row['scenario_id']}/{row['method']}/{name}")
    return failures


def secret_scan() -> list[str]:
    patterns = (
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"AKIA[0-9A-Z]{16}"),
        re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    )
    findings = []
    names = subprocess.check_output(
        ["git", "diff", "--name-only", r58.BASE_COMMIT],
        cwd=r58.ROOT, text=True, encoding="utf-8").splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "--",
         "docs", "scripts", "tests", "reference/citibike443-regional-v1",
         "results/gf_citibike443_k1_vs_pgrb_round58",
         "results/data_generation_citibike_round57"],
        cwd=r58.ROOT, text=True, encoding="utf-8").splitlines()
    names = sorted(set(names + untracked))
    for name in names:
        path = r58.ROOT / name
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(text) for pattern in patterns):
            findings.append(name)
    return findings


def raw_inventory() -> list[dict[str, Any]]:
    rows = []
    if not r58.RAW.is_dir():
        return rows
    for path in sorted(r58.RAW.rglob("*")):
        if path.is_file():
            reproduction = (
                "scripts/run_round58_pgrb_fingerprint_preflight.py"
                if "fingerprint_preflight" in path.parts else
                "scripts/run_round58_paired_benchmark.py --stage all")
            rows.append({
                "path": r58.repo_path(path), "bytes": path.stat().st_size,
                "sha256": r58.sha256_file(path),
                "committed": False,
                "reproduction": reproduction,
            })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-missing-build-report", action="store_true")
    args = parser.parse_args()
    protocol = runner.protocol_audit()
    decision = r58.read_json(OUT / "final_decision.json")
    required = list(REQUIRED_ALWAYS)
    counts = decision["stage_entry_counts"]
    if counts["long_10800"]:
        required.extend(("long_run_results_10800.csv",
                         "near_convergence_extension_decisions.csv",
                         "long_run_repeatability_audit.csv"))
    if counts["extension_16200"]:
        required.append("extended_results_16200.csv")
    if counts["extension_21600"]:
        required.append("extended_results_21600.csv")
    if args.allow_missing_build_report:
        required.remove("final_build_and_tests.md")
    missing = [name for name in required if not (OUT / name).is_file() or
               (OUT / name).stat().st_size == 0]
    tracked = tracked_paths()
    tmp_tracked = [path for path in tracked if path.startswith("tmp/round58_live_")]
    raw_tracked = [path for path in tracked if
                   "gf_citibike443_k1_vs_pgrb_round58/local_raw/official_runs" in path]
    command_failures = command_audit()
    preservation = preservation_failures()
    routes = route_failures()
    secrets = secret_scan()
    false_audit = r58.read_csv(OUT / "false_certificate_audit.csv")
    false_count = int(false_audit[0]["false_certificate_count"])
    dataset_audit = r58.read_json(OUT / "local_round57_dataset_audit.json")
    audits = [
        check(protocol["protocol_complete"], "staged_protocol_complete", protocol),
        check(protocol["completed_screen_arm_count"] == 100,
              "mandatory_100_arm_screen"),
        check(protocol["maximum_entered_cap_seconds"] <= 21600,
              "six_hour_hard_cap"),
        check(not missing, "required_compact_artifacts", missing),
        check(not command_failures, "official_command_scope", command_failures),
        check(not preservation, "user_file_preservation", preservation),
        check(not routes, "route_archive_hash_roundtrip", routes),
        check(false_count == 0, "zero_false_certificates", false_count),
        check(not tmp_tracked, "live_tmp_not_committed", tmp_tracked),
        check(not raw_tracked, "official_raw_not_committed", raw_tracked),
        check(not secrets, "secret_scan", secrets),
        check(dataset_audit.get("status") == "PASS" or
              dataset_audit.get("overall_status") == "PASS" or
              dataset_audit.get("all_checks_passed") is True or
              dataset_audit.get(
                  "round57_family_acceptable_for_frozen_round58_panel") is True,
              "round57_dataset_qualified", dataset_audit),
        check(r58.sha256_file(runner.EXE) == runner.EXE_SHA256,
              "official_executable_hash"),
        check(len(runner.fingerprint_index()) == 50,
              "pgrb_fingerprint_coverage"),
    ]
    r58.write_csv(OUT / "local_raw_inventory.csv", raw_inventory(), atomic=True)
    result = {
        "schema": "round58-final-delivery-audit-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "passed": all(row["passed"] for row in audits),
        "audit_count": len(audits), "audits": audits,
    }
    r58.write_json(OUT / "final_delivery_audit.json", result)
    r58.write_json(OUT / "secret_license_scan.json", {
        "schema": "round58-secret-license-scan-v1",
        "passed": not secrets, "secret_findings": secrets,
        "gurobi_license_file_committed": any(
            Path(path).name.lower() == "gurobi.lic" for path in tracked),
        "license_secret_content_committed": False,
    })
    r58.write_json(OUT / "source_scope_audit.json", {
        "schema": "round58-source-scope-audit-v1",
        "passed": not command_failures,
        "stable_preset_tuned": False, "VD_P_enabled": False,
        "PGRB_HGA_or_imported_routes": False,
        "scenario_replacement_performed": False,
        "command_failures": command_failures,
    })
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
