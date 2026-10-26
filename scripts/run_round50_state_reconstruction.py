#!/usr/bin/env python3
"""Reconstruct and freeze all Round 50 fixed-interval state identities."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
MANIFEST = EVIDENCE / "fixed_interval_state_manifest.csv"
EXE = ROOT / "build" / "dev-gurobi-release" / "Round50IntervalMipExperiment.exe"
RAW = EVIDENCE / "state_reconstruction"
PYTHON_TIMEOUT_SECONDS = 135


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def run(args: list[str], timeout: int = PYTHON_TIMEOUT_SECONDS) -> None:
    completed = subprocess.run(args, cwd=ROOT, timeout=timeout)
    if completed.returncode != 0:
        raise RuntimeError(f"command failed {completed.returncode}: {args}")


def command_flag(path: Path, name: str) -> str | None:
    if not path.exists():
        return None
    command = json.loads(path.read_text(encoding="utf-8")).get("command", [])
    for index, value in enumerate(command[:-1]):
        if value == name:
            return str(command[index + 1])
    return None


def route_time_limit_for(row: dict[str, str]) -> tuple[float, str]:
    source_command = ROOT / row["historical_source_run"] / "command.json"
    historical = command_flag(source_command, "--T")
    if historical is not None:
        return float(historical), source_command.relative_to(ROOT).as_posix()
    input_path = row["input_path"].replace("\\", "/")
    if "/small-hard/" in input_path:
        return 2400.0, "frozen_round39_small_hard_panel_convention"
    if "/small-medium/" in input_path:
        return 2850.0, "frozen_round39_small_medium_panel_convention"
    if "/hard_stress/" in input_path:
        return 3600.0, "frozen_hard_stress_panel_convention"
    raise RuntimeError(f"route horizon is not frozen for {row['state_id']}")


def parse_lp_mapping(path: Path) -> tuple[str, Counter[str], int, int]:
    section = ""
    typed: dict[str, str] = {}
    bounds: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line in {"Bounds", "Generals", "Binaries", "End"}:
            section = line
            continue
        if not line or line.startswith("\\"):
            continue
        if section == "Bounds":
            parts = line.split()
            if len(parts) >= 5 and parts[1] == "<=" and parts[3] == "<=":
                bounds.append(parts[2])
        elif section in {"Generals", "Binaries"}:
            typed[line.split()[0]] = "I" if section == "Generals" else "B"

    def family(name: str) -> str:
        prefixes = (
            ("x_", "routing_arc"), ("z_", "visit_selection"),
            ("mode_", "operation_mode"), ("op_mode_", "operation_mode"),
            ("p_", "pickup_quantity"), ("d_", "drop_quantity"),
            ("load_", "vehicle_load"), ("Y_", "final_inventory"),
            ("y_", "final_inventory"),
        )
        for prefix, label in prefixes:
            if name.startswith(prefix):
                return label
        return "auxiliary"

    counts: Counter[str] = Counter()
    registry = []
    for name in bounds:
        variable_type = typed.get(name, "C")
        label = family(name)
        counts[f"{label}:{variable_type}"] += 1
        registry.append(f"{name}|{variable_type}|{label}")
    digest = hashlib.sha256("\n".join(registry).encode()).hexdigest()
    return digest, counts, len(bounds), len(typed)


def cutoff_for(row: dict[str, str], resolutions: dict[str, float]) -> float:
    value = row["verified_cutoff"]
    if value.startswith("deterministic_hga:"):
        return resolutions[row["instance"]]
    return float(value)


def endpoint(value: str, cutoff: float) -> float:
    if value == "deterministic_hga:0":
        return 0.0
    if value == "deterministic_hga:verified_objective":
        return cutoff
    return float(value)


def main() -> None:
    rows = list(csv.DictReader(MANIFEST.open(newline="", encoding="utf-8-sig")))
    RAW.mkdir(parents=True, exist_ok=True)
    executable_sha = sha256(EXE)

    input_hash_failures = []
    for row in rows:
        actual = sha256(ROOT / row["input_path"])
        if actual != row["input_sha256"]:
            input_hash_failures.append({
                "state_id": row["state_id"], "expected": row["input_sha256"],
                "actual": actual,
            })
    if input_hash_failures:
        raise RuntimeError(f"input hash failures: {input_hash_failures}")

    instance_rows: dict[str, dict[str, str]] = {}
    for row in rows:
        instance_rows.setdefault(row["instance"], row)

    resolutions: dict[str, float] = {}
    resolution_paths: dict[str, Path] = {}
    for instance, representative in sorted(instance_rows.items()):
        route_time_limit, _ = route_time_limit_for(representative)
        cutoff_dir = RAW / (
            f"cutoff_{representative['state_id']}_T{int(route_time_limit)}")
        matched = cutoff_dir / "cutoff_resolution.json"
        expected_text = representative["verified_cutoff"]
        expected = None if expected_text.startswith("deterministic_hga:") else float(expected_text)
        reusable = False
        if matched.exists():
            prior = json.loads(matched.read_text(encoding="utf-8"))
            reusable = (
                prior.get("input_sha256") == representative["input_sha256"]
                and abs(float(prior.get("route_time_limit", -1.0)) - route_time_limit) <= 1e-9
                and prior.get("verified") is True
                and prior.get("expected_cutoff_matches") is True
            )
        if not reusable:
            command = [
                str(EXE), "--mode", "resolve-cutoff", "--state-id",
                representative["state_id"], "--input", representative["input_path"],
                "--artifact-dir", str(cutoff_dir), "--policy", "interval-mip-v0",
                "--process-cap", "120", "--T", format(route_time_limit, ".17g"),
            ]
            if expected is not None:
                command += ["--expected-cutoff", format(expected, ".17g")]
            run(command)
        resolution = json.loads(matched.read_text(encoding="utf-8"))
        if not resolution["verified"]:
            raise RuntimeError(f"unverified cutoff for {instance}")
        resolved = float(resolution["verified_objective"])
        if expected is not None and abs(resolved - expected) > 1e-7 * max(1.0, abs(expected)):
            raise RuntimeError(f"cutoff mismatch {instance}: {resolved} vs {expected}")
        resolutions[instance] = resolved
        resolution_paths[instance] = matched

    audit_fields = [
        "state_id", "panel", "instance", "input_sha256", "interval_id",
        "parent_id", "gamma_lower", "gamma_upper", "split_depth",
        "verified_cutoff", "cutoff_reconstruction_verified", "route_time_limit",
        "route_time_limit_source", "cutoff_resolution_path", "cutoff_resolution_sha256",
        "canonical_model_fingerprint", "row_bound_signature",
        "original_variable_mapping_sha256", "original_rows",
        "original_columns", "original_nonzeros", "mapped_variable_count",
        "typed_variable_count", "semantic_family_counts",
        "objective_sense", "formulation_profile", "selection_rule",
        "reconstruction_status", "experiment_executable_sha256",
        "model_artifact_path", "completion_marker", "failure_reason",
    ]
    audits = []
    for row in rows:
        state_id = row["state_id"]
        route_time_limit, route_time_source = route_time_limit_for(row)
        cutoff = cutoff_for(row, resolutions)
        lower = endpoint(row["gamma_lower"], cutoff)
        upper = endpoint(row["gamma_upper"], cutoff)
        state_dir = RAW / "models" / state_id
        if not (state_dir / "completion_marker.json").exists():
            run([
                str(EXE), "--mode", "build", "--state-id", state_id,
                "--input", row["input_path"], "--artifact-dir", str(state_dir),
                "--policy", "interval-mip-v0", "--gamma-lower",
                format(lower, ".17g"), "--gamma-upper", format(upper, ".17g"),
                "--cutoff", format(cutoff, ".17g"), "--process-cap", "30",
                "--T", format(route_time_limit, ".17g"),
            ], timeout=45)
        completion = json.loads((state_dir / "completion_marker.json").read_text(encoding="utf-8"))
        identity = json.loads((state_dir / "state_identity.json").read_text(encoding="utf-8"))
        model = json.loads((state_dir / "model_fingerprint.json").read_text(encoding="utf-8"))
        mapping_sha, family_counts, mapped_count, typed_count = parse_lp_mapping(
            state_dir / "canonical_model.lp")
        semantic_counts = ";".join(
            f"{name}={count}" for name, count in sorted(family_counts.items()))
        audits.append({
            "state_id": state_id, "panel": row["panel"],
            "instance": row["instance"], "input_sha256": row["input_sha256"],
            "interval_id": row["interval_id"], "parent_id": row["parent_id"],
            "gamma_lower": format(lower, ".17g"),
            "gamma_upper": format(upper, ".17g"),
            "split_depth": row["split_depth"],
            "verified_cutoff": format(cutoff, ".17g"),
            "cutoff_reconstruction_verified": "true",
            "route_time_limit": format(route_time_limit, ".17g"),
            "route_time_limit_source": route_time_source,
            "cutoff_resolution_path": resolution_paths[row["instance"]].relative_to(ROOT).as_posix(),
            "cutoff_resolution_sha256": sha256(resolution_paths[row["instance"]]),
            "canonical_model_fingerprint": model["sha256"],
            "row_bound_signature": model["row_signature"],
            "original_variable_mapping_sha256": mapping_sha,
            "original_rows": model["rows"], "original_columns": model["columns"],
            "original_nonzeros": model["nonzeros"],
            "mapped_variable_count": mapped_count,
            "typed_variable_count": typed_count,
            "semantic_family_counts": semantic_counts,
            "objective_sense": identity["objective_sense"],
            "formulation_profile": identity["formulation_profile"],
            "selection_rule": row["selection_rule"],
            "reconstruction_status": "complete" if completion["evidence_complete"] else "failed",
            "experiment_executable_sha256": executable_sha,
            "model_artifact_path": (state_dir / "canonical_model.lp").relative_to(ROOT).as_posix(),
            "completion_marker": (state_dir / "completion_marker.json").relative_to(ROOT).as_posix(),
            "failure_reason": "none" if completion["evidence_complete"] else completion["status"],
        })

    audit_path = EVIDENCE / "fixed_interval_state_reconstruction_audit.csv"
    with audit_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=audit_fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(audits)
    freeze = {
        "schema": "round50-fixed-state-reconstruction-freeze-v1",
        "state_count": len(audits),
        "complete_count": sum(row["reconstruction_status"] == "complete" for row in audits),
        "cutoff_count": len(resolutions),
        "false_cutoff_count": 0,
        "input_hash_failures": input_hash_failures,
        "experiment_executable_sha256": executable_sha,
        "audit_path": audit_path.relative_to(ROOT).as_posix(),
        "audit_sha256": sha256(audit_path),
        "candidate_result_inspected_before_freeze": False,
        "all_state_identities_frozen_before_stage1": True,
    }
    (EVIDENCE / "fixed_interval_state_reconstruction_freeze.json").write_text(
        json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(freeze, indent=2))


if __name__ == "__main__":
    main()
