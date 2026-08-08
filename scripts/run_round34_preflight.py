#!/usr/bin/env python3
"""Generate fresh fingerprints and qualify strict Round 34 result promotion.

The script contains no license location and never opens, copies, hashes, or
serializes a license file.  It must be launched by the established licensed
child controller, which supplies the authorized environment value only to this
process and its solver children.
"""

from __future__ import annotations

import csv
import json
import math
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import round34_common as common


SENSITIVE_MARKERS = (
    b"GRB_LICENSE_FILE",
    b"gurobi.lic",
    b"LicenseID",
    b"WLSAccessID",
    b"WLSSecret",
)


def scan_sensitive(directory: Path) -> None:
    for path in directory.rglob("*"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        if any(marker.lower() in data.lower() for marker in SENSITIVE_MARKERS):
            raise RuntimeError(
                f"sensitive license marker detected in {path.name}")


def verification_passed(result: dict[str, Any]) -> bool:
    verification = result.get("verification", {})
    return bool(
        verification.get("original_solution_feasible")
        and verification.get("original_objective_recomputed")
        and verification.get("objective_matches")
        and not verification.get("errors")
    )


def exact(arm: str, result: dict[str, Any]) -> bool:
    try:
        lower, upper = common.result_bounds(arm, result)
    except (KeyError, TypeError, ValueError):
        return False
    lifecycle = bool(
        result.get("external_gini_tree_lifecycle_complete")
        if arm.startswith("C6-") else result.get("gurobi_lifecycle_valid"))
    scale = max(1.0, abs(lower), abs(upper))
    return bool(
        math.isfinite(lower) and math.isfinite(upper)
        and lower <= upper + 1e-7 * scale
        and result.get("strict_certified_original_problem") is True
        and result.get("strict_certificate_rejection_reason") == "none"
        and verification_passed(result) and lifecycle
    )


def run_child(label: str, command: list[str], arm: str,
              timeout: int) -> tuple[dict[str, Any], Path]:
    directory = common.STAGE0_RUNS / label
    if directory.exists():
        raise RuntimeError(f"preflight row already exists: {label}")
    directory.mkdir(parents=True)
    record = {
        "schema": "round34-preflight-command-v1",
        "round_id": 34,
        "run_id": label,
        "arm": arm,
        "command": command,
        "executable_sha256": common.sha256(common.EXE),
        "source_commit": common.load_json(
            common.OUT / "stage0_build_and_tests.json")["source_commit"],
        "license_environment":
            "inherited_by_licensed_solver_child_not_serialized",
    }
    common.write_json(directory / "command.json", record)
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
    record.update({
        "return_code": return_code,
        "runner_wall_seconds": time.monotonic() - started,
    })
    common.write_json(directory / "command.json", record)
    scan_sensitive(directory)
    if return_code != 0:
        raise RuntimeError(f"preflight child failed: {label}: rc={return_code}")
    result_path = directory / "result.json"
    if not result_path.is_file():
        raise RuntimeError(f"preflight result missing: {label}")
    return common.load_json(result_path), directory


def trace_audit(run_id: str, arm: str, directory: Path,
                result: dict[str, Any]) -> dict[str, Any]:
    if arm == "P-GRB":
        path = directory / "progress.csv"
        time_fields = ("elapsed_seconds", "runtime_seconds", "time_seconds")
        bound_fields = ("best_bound", "lower_bound", "valid_lower_bound")
    else:
        path = directory / "external" / "global_bound_trace.csv"
        time_fields = ("process_elapsed_seconds",)
        bound_fields = ("valid_global_lower_bound",)
    rows = common.csv_rows(path) if path.is_file() else []
    previous_time = -math.inf
    previous_bound = -math.inf
    monotone_time = True
    monotone_bound = True
    observations = 0
    for row in rows:
        time_value = next((row.get(field, "") for field in time_fields
                           if row.get(field, "") != ""), "")
        bound_value = next((row.get(field, "") for field in bound_fields
                            if row.get(field, "") != ""), "")
        try:
            elapsed = float(time_value)
            bound = float(bound_value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(elapsed) or not math.isfinite(bound):
            continue
        monotone_time &= elapsed + 1e-9 >= previous_time
        monotone_bound &= bound + 1e-7 >= previous_bound
        previous_time = max(previous_time, elapsed)
        previous_bound = max(previous_bound, bound)
        observations += 1
    instantaneous_plain = arm == "P-GRB" and exact(arm, result)
    return {
        "round_id": 34,
        "run_id": run_id,
        "arm": arm,
        "trace_path": common.relative(path),
        "observation_count": observations,
        "elapsed_monotone": monotone_time,
        "valid_lower_bound_monotone": monotone_bound,
        "instantaneous_exact_trace_allowed": instantaneous_plain,
        "passed": monotone_time and monotone_bound and (
            observations > 0 or instantaneous_plain),
    }


def main() -> int:
    if "GRB_LICENSE_FILE" not in os.environ:
        raise SystemExit("licensed child environment is unavailable")
    build = common.load_json(common.OUT / "stage0_build_and_tests.json")
    if not build.get("passed") or not common.EXE.is_file():
        raise RuntimeError("Round 34 build/test gate did not pass")
    if common.sha256(common.EXE) != build["gurobi_executable_sha256"]:
        raise RuntimeError("Round 34 executable changed after stage 0")
    items = common.inventory()
    if len(items) != 22:
        raise RuntimeError(f"expected 22 identities, got {len(items)}")
    common.STAGE0_RUNS.mkdir(parents=True, exist_ok=False)

    entries: dict[str, dict[str, Any]] = {}
    for order, name in enumerate(sorted(items), start=1):
        item = items[name]
        label = f"fingerprint__{name}"
        directory = common.STAGE0_RUNS / label
        command = common.plain_command(
            item, directory, 0, process_cap=5.0,
            solver_seconds=0.001, shutdown_margin=0.0)
        result, directory = run_child(
            label, command, "P-GRB-FINGERPRINT-PROBE", 60)
        fingerprint = int(result.get("gurobi_model_fingerprint", 0))
        model = directory / "canonical.lp"
        if (fingerprint == 0 or not model.is_file() or not result.get(
                "gurobi_native_domain_audit_passed")):
            raise RuntimeError(f"fingerprint audit failed: {name}")
        entries[name] = {
            "serial_order": order,
            "instance_sha256": item["sha256"],
            "canonical_model_path": common.relative(model),
            "canonical_model_sha256": common.sha256(model),
            "gurobi_model_fingerprint": fingerprint,
            "gurobi_native_domain_audit_passed": True,
            "executable_sha256": common.sha256(common.EXE),
            "source_commit": build["source_commit"],
            "solver_version": "13.0.2",
            "frozen_before_official_results": True,
        }
        print(f"fingerprint {order}/22 {name}", flush=True)
    common.write_json(common.FINGERPRINTS, {
        "schema": "round34-gurobi-fingerprints-v1",
        "round_id": 34,
        "source_commit": build["source_commit"],
        "executable_sha256": common.sha256(common.EXE),
        "solver_version": "13.0.2",
        "instance_count": len(entries),
        "created_before_official_results": True,
        "instances": entries,
    })

    smoke_id = "V12_M2"
    item = items[smoke_id]
    fingerprint = entries[smoke_id]["gurobi_model_fingerprint"]
    audits: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    for arm in ("P-GRB", "C6-HGA-FULL"):
        label = f"strict_promotion__{smoke_id}__{arm.lower().replace('-', '_')}"
        directory = common.STAGE0_RUNS / label
        if arm == "P-GRB":
            command = common.plain_command(
                item, directory, fingerprint, process_cap=7200)
        else:
            command = common.c6_command(
                item, arm, directory, fingerprint, process_cap=7200)
        result, directory = run_child(label, command, arm, 7290)
        passed = exact(arm, result)
        startup = result.get(
            "external_gini_tree_startup_variant", "not_applicable")
        row = {
            "round_id": 34,
            "stage": "stage0_strict_promotion",
            "run_id": label,
            "instance_id": smoke_id,
            "instance_sha256": item["sha256"],
            "arm": arm,
            "startup_variant": startup,
            "strict_certificate": bool(
                result.get("strict_certified_original_problem")),
            "strict_certificate_class": result.get(
                "strict_certificate_class", ""),
            "certificate_rejection_reason": result.get(
                "strict_certificate_rejection_reason", ""),
            "verifier_passed": verification_passed(result),
            "lifecycle_valid": bool(result.get(
                "external_gini_tree_lifecycle_complete"
                if arm.startswith("C6-") else "gurobi_lifecycle_valid")),
            "fingerprint_match": int(result.get(
                "gurobi_model_fingerprint", fingerprint)) == fingerprint,
            "process_entry_time_seconds": common.process_entry_time(result),
            "passed": passed,
        }
        audits.append(row)
        traces.append(trace_audit(label, arm, directory, result))
        if not passed:
            raise RuntimeError(f"strict result promotion failed: {arm}")
        print(f"strict promotion {arm} time={row['process_entry_time_seconds']}",
              flush=True)

    common.write_csv(common.OUT / "round34_certificate_preflight.csv", audits)
    common.write_csv(common.OUT / "stage0_exactness.csv", audits)
    common.write_csv(common.OUT / "stage0_trace_audit.csv", traces)
    passed = all(row["passed"] for row in audits + traces)
    common.write_json(common.OUT / "round34_preflight_summary.json", {
        "schema": "round34-preflight-summary-v1",
        "round_id": 34,
        "source_commit": build["source_commit"],
        "executable_sha256": common.sha256(common.EXE),
        "fingerprint_count": len(entries),
        "strict_promotion_rows": len(audits),
        "trace_rows": len(traces),
        "false_certificates": 0,
        "passed": passed,
        "completed_at_unix_seconds": time.time(),
    })
    print(json.dumps({
        "fingerprints": len(entries),
        "strict_promotions": len(audits),
        "false_certificates": 0,
        "passed": passed,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
