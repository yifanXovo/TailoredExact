#!/usr/bin/env python3
"""Freeze deterministic P-GRB model fingerprints before official rows.

The probes use the established bounded project pattern: a 0.001-second
solver limit inside a five-second total-process cap.  They construct and
export the canonical model but are never classified as benchmark rows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import time
from pathlib import Path

import run_round52_final_panel as final


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_tailored_cut_final_validation_round52"
PROBE_CAP = 5.0
SOLVER_CAP = 0.001
SENSITIVE_MARKERS = (
    b"grb_license_file", b"gurobi.lic", b"licenseid",
    b"wlsaccessid", b"wlssecret",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n",
                         encoding="utf-8")
    temporary.replace(path)


def result_value(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    return value[0] if isinstance(value, list) else value


def scan_sensitive(directory: Path) -> None:
    for path in directory.rglob("*"):
        if path.is_file():
            data = path.read_bytes().lower()
            if any(marker in data for marker in SENSITIVE_MARKERS):
                raise RuntimeError(f"sensitive license marker in {path}")


def invalidate_prior_attempts(executable_hash: str) -> list[dict[str, object]]:
    base = OUT / "local_raw" / "final_panel_runs"
    audits: list[dict[str, object]] = []
    if not base.is_dir():
        return audits
    for directory in sorted(base.glob("validation__*__P-GRB")):
        result_path = directory / "result.json"
        result = result_value(result_path) if result_path.is_file() else {}
        reason = ("model_fingerprint_discovery_without_frozen_expectation"
                  if result else "interrupted_after_plumbing_issue_discovery")
        marker = {
            "schema": "round52-invalidated-preflight-attempt-v1",
            "run_id": directory.name,
            "official_benchmark_row": False,
            "retained_in_local_raw": True,
            "invalidation_reason": reason,
            "result_present": result_path.is_file(),
            "strict_certificate": result.get(
                "strict_certified_original_problem"),
            "certificate_rejection_reason": result.get(
                "strict_certificate_rejection_reason", "no_result"),
            "observed_gurobi_model_fingerprint": result.get(
                "gurobi_model_fingerprint"),
            "executable_sha256": executable_hash,
        }
        write_json(directory / "invalidation_marker.json", marker)
        audits.append({
            **marker,
            "raw_path": directory.relative_to(ROOT).as_posix(),
        })
    return audits


def probe(panel: str, row: dict[str, object], executable: Path,
          executable_hash: str) -> dict[str, object]:
    run_id = f"fingerprint__{panel}__{row['instance_id']}"
    directory = OUT / "local_raw" / "final_model_fingerprint_preflight" / run_id
    result_path = directory / "result.json"
    marker_path = directory / "completion_marker.json"
    if marker_path.is_file() and result_path.is_file():
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        if (marker.get("complete") is True and
                marker.get("executable_sha256") == executable_hash):
            result = result_value(result_path)
            model = directory / "canonical.lp"
            return {
                "instance_sha256": row["input_sha256"],
                "gurobi_model_fingerprint": int(
                    result["gurobi_model_fingerprint"]),
                "canonical_model_sha256": sha256(model),
                "probe_process_cap_seconds": PROBE_CAP,
                "probe_solver_cap_seconds": SOLVER_CAP,
                "gurobi_native_domain_audit_passed": True,
                "raw_probe_path": directory.relative_to(ROOT).as_posix(),
            }
    if directory.exists() and any(directory.iterdir()):
        raise RuntimeError(f"incomplete fingerprint probe retained: {run_id}")
    directory.mkdir(parents=True, exist_ok=True)
    command = final.command_for(
        "P-GRB", row, directory, executable, expected_fingerprint=None)
    final.set_option(command, "--process-wall-time-limit", PROBE_CAP)
    final.set_option(command, "--time-limit", SOLVER_CAP)
    final.set_option(command, "--process-shutdown-margin", 0.0)
    final.set_option(command, "--gurobi-hga-start", False)
    record: dict[str, object] = {
        "schema": "round52-pgrb-fingerprint-probe-command-v1",
        "run_id": run_id, "panel": panel,
        "instance_id": row["instance_id"],
        "input_sha256": row["input_sha256"],
        "official_benchmark_row": False,
        "purpose": "canonical_model_fingerprint_freeze_only",
        "process_cap_seconds": PROBE_CAP,
        "solver_cap_seconds": SOLVER_CAP,
        "executable_sha256": executable_hash,
        "command": command,
    }
    write_json(directory / "command.json", record)
    started = time.monotonic()
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    with (directory / "stdout.log").open("wb") as stdout, \
            (directory / "stderr.log").open("wb") as stderr:
        try:
            completed = subprocess.run(
                command, cwd=ROOT, env=environment, stdout=stdout,
                stderr=stderr, timeout=60, check=False)
            return_code, watchdog = completed.returncode, False
        except subprocess.TimeoutExpired:
            return_code, watchdog = -1, True
    record.update({
        "return_code": return_code, "watchdog_timeout": watchdog,
        "runner_wall_seconds": time.monotonic() - started,
        "result_present": result_path.is_file(),
    })
    write_json(directory / "command.json", record)
    scan_sensitive(directory)
    if return_code != 0 or watchdog or not result_path.is_file():
        raise RuntimeError(f"fingerprint probe failed: {run_id}")
    result = result_value(result_path)
    fingerprint = int(result.get("gurobi_model_fingerprint", 0))
    model = directory / "canonical.lp"
    process_seconds = float(result.get("final_process_wall_time_seconds", 0))
    if (fingerprint == 0 or not model.is_file() or
            result.get("gurobi_native_domain_audit_passed") is not True or
            process_seconds > PROBE_CAP + 1e-6):
        raise RuntimeError(f"fingerprint audit failed: {run_id}")
    entry = {
        "instance_sha256": row["input_sha256"],
        "gurobi_model_fingerprint": fingerprint,
        "canonical_model_sha256": sha256(model),
        "probe_process_cap_seconds": PROBE_CAP,
        "probe_solver_cap_seconds": SOLVER_CAP,
        "gurobi_native_domain_audit_passed": True,
        "raw_probe_path": directory.relative_to(ROOT).as_posix(),
    }
    write_json(marker_path, {
        "schema": "round52-pgrb-fingerprint-probe-completion-v1",
        "complete": True, "official_benchmark_row": False,
        "executable_sha256": executable_hash, **entry,
    })
    print(f"fingerprint {panel} {row['instance_id']} = {fingerprint}",
          flush=True)
    return entry


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, required=True)
    args = parser.parse_args()
    executable = args.executable.resolve()
    if not executable.is_file():
        raise SystemExit("frozen executable missing")
    executable_hash = sha256(executable)
    seal = json.loads((OUT / "holdout_seal_audit.json").read_text(
        encoding="utf-8"))
    if (seal.get("opening_authorized") is not True or
            seal.get("executable_sha256") != executable_hash):
        raise SystemExit("algorithm/holdout seal does not authorize preflight")
    invalidated = invalidate_prior_attempts(executable_hash)
    panels: dict[str, dict[str, object]] = {}
    for panel in ("validation", "holdout"):
        panels[panel] = {}
        for row in final.manifest(panel):
            panels[panel][str(row["instance_id"])] = probe(
                panel, row, executable, executable_hash)
    import subprocess as _subprocess
    source_commit = _subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    output = {
        "schema": "round52-pgrb-model-fingerprints-v1",
        "round_id": 52,
        "created_before_official_bound_rows": True,
        "algorithm_frozen_before_probes": True,
        "algorithm_freeze_commit": seal["algorithm_freeze_commit"],
        "orchestration_commit": source_commit,
        "executable_sha256": executable_hash,
        "solver_version": "13.0.2rc1",
        "probe_process_cap_seconds": PROBE_CAP,
        "probe_solver_cap_seconds": SOLVER_CAP,
        "machine": platform.node(),
        "panels": panels,
    }
    write_json(final.FINGERPRINTS, output)
    write_json(OUT / "final_panel_preflight_invalidation_audit.json", {
        "schema": "round52-final-panel-preflight-invalidation-audit-v1",
        "invalidated_attempt_count": len(invalidated),
        "official_benchmark_rows_counted": 0,
        "all_attempts_retained": True,
        "algorithm_or_executable_changed": False,
        "attempts": invalidated,
    })
    print(json.dumps({
        "validation_fingerprints": len(panels["validation"]),
        "holdout_fingerprints": len(panels["holdout"]),
        "invalidated_prior_attempts": len(invalidated),
        "executable_sha256": executable_hash,
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
