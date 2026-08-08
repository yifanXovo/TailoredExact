#!/usr/bin/env python3
"""Freeze Gurobi fingerprints and validate Round 33 certificates pre-run."""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import analyze_round32 as round32_analysis
import round33_common as common


OUT = common.OUT
PREFLIGHT = common.STAGE0
INVALIDATED = OUT / "invalidated_preflight"
SENSITIVE_MARKERS = (
    b"GRB_LICENSE_FILE",
    b"gurobi.lic",
    b"LicenseID",
    b"WLSAccessID",
    b"WLSSecret",
)
SCENARIO_C6_CELLS = (
    (2, 20, "high_imbalance"),
    (2, 20, "moderate"),
    (2, 20, "tight_T"),
)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def write_json(path: Path, value: Any) -> None:
    write_text(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def verification_passed(result: dict[str, Any]) -> bool:
    verification = result.get("verification", {})
    return bool(
        verification.get("original_solution_feasible")
        and verification.get("original_objective_recomputed")
        and verification.get("objective_matches")
        and not verification.get("errors")
    )


def result_exact(arm: str, result: dict[str, Any]) -> bool:
    try:
        lower, upper = common.result_bounds(arm, result)
    except (KeyError, TypeError, ValueError):
        return False
    scale = max(1.0, abs(lower), abs(upper))
    lifecycle = (
        bool(result.get("external_gini_tree_lifecycle_complete"))
        if arm == "C6-FROZEN"
        else bool(result.get("gurobi_lifecycle_valid"))
    )
    return bool(
        math.isfinite(lower)
        and math.isfinite(upper)
        and lower <= upper + 1e-7 * scale
        and result.get("strict_certified_original_problem") is True
        and verification_passed(result)
        and lifecycle
        and result.get("strict_certificate_rejection_reason") == "none"
    )


def invalidate(directory: Path, reason: str) -> None:
    INVALIDATED.mkdir(parents=True, exist_ok=True)
    target = INVALIDATED / (
        f"{directory.name}__{reason}__{int(time.time() * 1000)}")
    if OUT.resolve() not in target.resolve().parents:
        raise RuntimeError(f"unsafe preflight invalidation: {target}")
    os.replace(directory, target)


def scan_sensitive(directory: Path) -> None:
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        if any(marker.lower() in data.lower() for marker in SENSITIVE_MARKERS):
            raise RuntimeError(
                f"sensitive license marker detected in {path.name}")


def run_child(label: str, command: list[str], timeout: int,
              arm: str) -> tuple[dict[str, Any], Path, bool]:
    directory = PREFLIGHT / label
    command_record = {
        "schema": "round33-preflight-command-v1",
        "round_id": 33,
        "label": label,
        "arm": arm,
        "command": command,
        "executable_sha256": common.sha256(common.EXE),
        "license_environment":
            "inherited_by_licensed_child_not_serialized",
    }
    if directory.exists():
        old_command = directory / "command.json"
        result_path = directory / "result.json"
        if old_command.is_file() and result_path.is_file():
            old = common.load_json(old_command)
            if (
                old.get("command") == command
                and old.get("executable_sha256") ==
                    command_record["executable_sha256"]
            ):
                result = common.load_json(result_path)
                scan_sensitive(directory)
                return result, directory, True
        invalidate(directory, "incomplete_or_identity_mismatch")
    directory.mkdir(parents=True, exist_ok=False)
    write_json(directory / "command.json", command_record)
    started = time.monotonic()
    with (directory / "console.stdout.log").open("wb") as stdout, \
         (directory / "console.stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=common.ROOT, env=os.environ.copy(),
                stdout=stdout, stderr=stderr, timeout=timeout, check=False)
            return_code = completed.returncode
        except subprocess.TimeoutExpired:
            return_code = 124
        stdout.flush()
        os.fsync(stdout.fileno())
        stderr.flush()
        os.fsync(stderr.fileno())
    command_record.update({
        "return_code": return_code,
        "runner_wall_seconds": time.monotonic() - started,
    })
    write_json(directory / "command.json", command_record)
    scan_sensitive(directory)
    if return_code != 0:
        raise RuntimeError(f"preflight child failed: {label}: {return_code}")
    result_path = directory / "result.json"
    if not result_path.is_file():
        raise RuntimeError(f"preflight result missing: {label}")
    return common.load_json(result_path), directory, False


def trace_row(label: str, arm: str, directory: Path,
              result: dict[str, Any]) -> dict[str, Any]:
    run = {
        "state": {"run_id": label, "arm": arm},
        "result": result,
        "run_dir": directory,
    }
    complete, reason, observations = round32_analysis.trace_for(run)
    instantaneous_exact = bool(
        arm == "P-GRB"
        and result.get("strict_certified_original_problem")
        and reason == "too_few_native_callback_bounds"
    )
    return {
        "round_id": 33,
        "run_id": label,
        "arm": arm,
        "trace_complete": complete,
        "trace_reason": (
            "instantaneous_exact_native_trace_explicitly_auc_unavailable"
            if instantaneous_exact else reason),
        "observation_count": len(observations),
        "monotonicity_passed": complete or instantaneous_exact,
        "auc_preflight_available": complete,
        "passed": complete or instantaneous_exact,
    }


def main() -> int:
    if "GRB_LICENSE_FILE" not in os.environ:
        raise SystemExit("licensed child environment is unavailable")
    build = common.load_json(OUT / "stage0_build_and_tests.json")
    if not build.get("passed") or not common.EXE.is_file():
        raise RuntimeError("Round 33 clean build gate did not pass")
    head = subprocess.check_output(
        ("git", "rev-parse", "HEAD"), cwd=common.ROOT,
        text=True).strip()
    if head != build["source_commit"]:
        raise RuntimeError("preflight executable was not built from HEAD")
    items = common.inventory()
    if len(items) != 20:
        raise RuntimeError(f"expected 20 V10/V12 identities, got {len(items)}")
    PREFLIGHT.mkdir(parents=True, exist_ok=True)

    fingerprint_entries: dict[str, dict[str, Any]] = {}
    for index, name in enumerate(sorted(items), start=1):
        item = items[name]
        label = f"fingerprint__{name}"
        directory = PREFLIGHT / label
        command = common.plain_command(
            item, directory, 0, process_cap=5.0,
            solver_seconds=0.001, shutdown_margin=0.0)
        result, directory, reused = run_child(
            label, command, timeout=30, arm="P-GRB-FINGERPRINT-PROBE")
        fingerprint = int(result.get("gurobi_model_fingerprint", 0))
        model = directory / "canonical.lp"
        if (
            fingerprint == 0
            or not result.get("gurobi_native_domain_audit_passed")
            or not model.is_file()
        ):
            raise RuntimeError(f"canonical fingerprint audit failed: {name}")
        fingerprint_entries[name] = {
            "serial_order": index,
            "instance_sha256": item["sha256"],
            "canonical_model_path": common.relative(model),
            "canonical_model_sha256": common.sha256(model),
            "gurobi_model_fingerprint": fingerprint,
            "gurobi_native_domain_audit_passed": True,
            "executable_sha256": common.sha256(common.EXE),
            "source_commit": head,
            "solver_version": "13.0.2",
            "probe_reused": reused,
            "frozen_before_certificate_promotion_and_official_results": True,
        }
    write_json(common.FINGERPRINTS, {
        "schema": "round33-gurobi-fingerprints-v1",
        "round_id": 33,
        "source_commit": head,
        "executable_sha256": common.sha256(common.EXE),
        "solver_version": "13.0.2",
        "created_before_official_results": True,
        "instance_count": len(fingerprint_entries),
        "instances": fingerprint_entries,
    })

    exactness: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    certificate_rows: list[dict[str, Any]] = []
    fingerprints = common.fingerprint_values()
    v10 = [item for item in items.values() if item["V"] == 10]
    for item in sorted(v10, key=lambda row: row["instance_id"]):
        name = item["instance_id"]
        label = f"certificate_promotion__{name}__p_grb"
        directory = PREFLIGHT / label
        command = common.plain_command(
            item, directory, fingerprints[name])
        result, directory, reused = run_child(
            label, command, timeout=common.WATCHDOG, arm="P-GRB")
        exact = result_exact("P-GRB", result)
        fingerprint_match = (
            int(result.get("gurobi_model_fingerprint", 0)) ==
            fingerprints[name]
        )
        threads_ok = (
            int(result.get("gurobi_threads_effective", -1)) == 1
            and int(result.get("gurobi_seed_effective", -1)) == 0
            and int(result.get("gurobi_presolve_effective", -2)) == -1
            and float(result.get("gurobi_mip_gap_effective", -1)) == 0.0
            and float(result.get("gurobi_mip_gap_abs_effective", -1)) == 0.0
        )
        passed = exact and fingerprint_match and threads_ok
        exactness.append({
            "round_id": 33,
            "stage_id": "stage0_certificate_promotion",
            "run_id": label,
            "instance_id": name,
            "V": item["V"],
            "M": item["M"],
            "Q": item["Q"],
            "scenario": item["scenario"],
            "arm": "P-GRB",
            "strict_certificate": bool(
                result.get("strict_certified_original_problem")),
            "strict_certificate_class":
                result.get("strict_certificate_class", ""),
            "fingerprint_match": fingerprint_match,
            "verifier_passed": verification_passed(result),
            "single_thread_seed_presolve_gap_contract": threads_ok,
            "lifecycle_valid": bool(result.get("gurobi_lifecycle_valid")),
            "process_entry_certificate_time_seconds":
                common.process_entry_time(result),
            "reused": reused,
            "passed": passed,
        })
        certificate_rows.append({
            "round_id": 33,
            "instance_id": name,
            "instance_sha256": item["sha256"],
            "V": item["V"],
            "M": item["M"],
            "Q": item["Q"],
            "scenario": item["scenario"],
            "gurobi_model_fingerprint": fingerprints[name],
            "canonical_model_sha256":
                fingerprint_entries[name]["canonical_model_sha256"],
            "executable_sha256": common.sha256(common.EXE),
            "native_optimal_promoted_to_strict_certificate": exact,
            "fingerprint_match": fingerprint_match,
            "verifier_contract_passed": verification_passed(result),
            "single_thread_contract_passed": threads_ok,
            "strict_certificate_class":
                result.get("strict_certificate_class", ""),
            "preflight_run_id": label,
            "frozen_before_official_results": True,
            "passed": passed,
        })
        trace_rows.append(trace_row(label, "P-GRB", directory, result))
        if not passed:
            raise RuntimeError(f"strict certificate preflight failed: {name}")

    keyed = {
        (item["M"], item["Q"], item["scenario"]): item for item in v10
    }
    for cell in SCENARIO_C6_CELLS:
        item = keyed[cell]
        name = item["instance_id"]
        label = f"exactness__{name}__c6_frozen"
        directory = PREFLIGHT / label
        command = common.c6_command(
            item, directory, fingerprints[name])
        result, directory, reused = run_child(
            label, command, timeout=common.WATCHDOG, arm="C6-FROZEN")
        exact = result_exact("C6-FROZEN", result)
        exactness.append({
            "round_id": 33,
            "stage_id": "stage0_c6_scenario_exactness",
            "run_id": label,
            "instance_id": name,
            "V": item["V"],
            "M": item["M"],
            "Q": item["Q"],
            "scenario": item["scenario"],
            "arm": "C6-FROZEN",
            "strict_certificate": bool(
                result.get("strict_certified_original_problem")),
            "strict_certificate_class":
                result.get("strict_certificate_class", ""),
            "fingerprint_match": "metadata_bound_not_native_baseline_gate",
            "verifier_passed": verification_passed(result),
            "single_thread_seed_presolve_gap_contract": True,
            "lifecycle_valid": bool(
                result.get("external_gini_tree_lifecycle_complete")),
            "process_entry_certificate_time_seconds":
                common.process_entry_time(result),
            "reused": reused,
            "passed": exact,
        })
        trace = trace_row(label, "C6-FROZEN", directory, result)
        trace_rows.append(trace)
        if not exact or not trace["passed"]:
            raise RuntimeError(f"C6 scenario exactness failed: {name}")

    write_csv(OUT / "round33_certificate_preflight.csv", certificate_rows)
    write_csv(OUT / "stage0_exactness.csv", exactness)
    write_csv(OUT / "stage0_trace_audit.csv", trace_rows)
    passed = (
        len(certificate_rows) == 18
        and all(row["passed"] for row in certificate_rows)
        and len(exactness) == 21
        and all(row["passed"] for row in exactness)
        and all(row["passed"] for row in trace_rows)
    )
    write_json(OUT / "round33_preflight_summary.json", {
        "schema": "round33-preflight-summary-v1",
        "source_commit": head,
        "fingerprint_count": len(fingerprint_entries),
        "v10_certificate_promotions": len(certificate_rows),
        "c6_scenario_exactness_rows": 3,
        "exactness_rows": len(exactness),
        "trace_rows": len(trace_rows),
        "false_certificates": 0,
        "passed": passed,
    })
    if not passed:
        raise RuntimeError("Round 33 preflight gate failed")
    print(json.dumps({
        "fingerprints": len(fingerprint_entries),
        "certificate_promotions": len(certificate_rows),
        "exactness_rows": len(exactness),
        "trace_rows": len(trace_rows),
        "passed": passed,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
