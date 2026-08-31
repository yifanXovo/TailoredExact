#!/usr/bin/env python3
"""Run bounded canonical/legacy semantic sentinels for paper-k1-am-sf."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_am_sf_inventory_route_round54"
SOURCE_RUNS = ROOT / "results" / "gf_k1_f0_callback_isolation_round53" / "local_raw" / "k1_panel_runs"
EXECUTABLE = ROOT / "build" / "official-round54-b6784e930" / "ExactEBRP.exe"
DEFAULT_CAP = 20

SENTINELS = [
    ("major", "integration__round39_small_medium_V12_M3_Q30_slot08_seed1343324363__K1-AM-CANDIDATE__300s"),
    ("strong_control", "integration__round39_small_hard_V12_M3_Q30_slot08_seed1288546114__K1-AM-CANDIDATE__300s"),
    ("v10_easy_negative", "integration__round39_small_hard_V10_M3_Q20_slot04_seed1145042375__K1-AM-CANDIDATE__300s"),
    ("numerical_endpoint", "integration__round39_small_hard_V12_M3_Q20_slot07_seed621538683__K1-AM-CANDIDATE__300s"),
    ("v20_sentinel", "sentinel__round52_validation_moderate_3600_V20_M3_seed1783533980__K1-AM-CANDIDATE__300s"),
    ("v50_sentinel", "sentinel__round52_validation_moderate_3600_V50_M3_seed664120090__K1-AM-CANDIDATE__300s"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def set_option(command: list[str], option: str, value: str) -> None:
    index = command.index(option)
    command[index + 1] = value


def selected_rows(path: Path, columns: list[str]) -> list[tuple[str, ...]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return [tuple(row.get(column, "") for column in columns) for row in csv.DictReader(handle)]


def model_hashes(run_dir: Path) -> dict[str, str]:
    model_dir = run_dir / "external" / "models"
    if not model_dir.exists():
        return {}
    return {path.name: sha256(path) for path in sorted(model_dir.glob("*.lp"))}


def run(role: str, template_name: str, preset: str, arm: str, cap: int) -> tuple[Path, dict]:
    template = json.loads((SOURCE_RUNS / template_name / "command.json").read_text(encoding="utf-8"))
    command = list(template["command"])
    command[0] = str(EXECUTABLE)
    run_dir = EVIDENCE / "local_raw" / "paper_preset_semantic" / role / arm
    run_dir.mkdir(parents=True, exist_ok=True)
    command_record_path = run_dir / "command.json"
    result_path = run_dir / "result.json"
    if command_record_path.exists() and result_path.exists():
        prior = json.loads(command_record_path.read_text(encoding="utf-8"))
        if (
            prior.get("preset") == preset
            and int(prior.get("cap_seconds", -1)) == cap
            and prior.get("executable_sha256") == sha256(EXECUTABLE)
            and int(prior.get("return_code", -1)) == 0
        ):
            return run_dir, json.loads(result_path.read_text(encoding="utf-8"))
    replacements = {
        "--algorithm-preset": preset,
        "--time-limit": str(cap - 6),
        "--process-wall-time-limit": str(cap),
        "--process-shutdown-margin": "2",
        "--primal-heuristic-generation-log": str(run_dir / "hga_generations.csv"),
        "--progress-log": str(run_dir / "progress.csv"),
        "--process-phase-ledger": str(run_dir / "process_phases.csv"),
        "--heuristic-candidates-csv": str(run_dir / "heuristic_candidates.csv"),
        "--external-gini-artifact-dir": str(run_dir / "external"),
        "--log": str(run_dir / "native.log"),
        "--out": str(run_dir / "result.json"),
        "--round24-executable-sha256": sha256(EXECUTABLE),
        "--round24-manifest-executable-sha256": sha256(EXECUTABLE),
    }
    for option, value in replacements.items():
        if option in command:
            set_option(command, option, value)
    completed = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True,
        timeout=cap + 30, check=False,
    )
    (run_dir / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (run_dir / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
    (run_dir / "command.json").write_text(
        json.dumps({
            "schema": "round54-paper-preset-sentinel-command-v1",
            "role": role,
            "arm": arm,
            "preset": preset,
            "cap_seconds": cap,
            "executable_sha256": sha256(EXECUTABLE),
            "command": command,
            "return_code": completed.returncode,
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    if completed.returncode != 0 or not result_path.exists():
        raise RuntimeError(f"semantic sentinel failed: {role}/{arm}: {completed.stderr[-500:]}")
    return run_dir, json.loads(result_path.read_text(encoding="utf-8"))


def main() -> int:
    rows = []
    action_columns = [
        "decision_sequence", "K0", "tau", "interval_id", "parent_id",
        "depth", "gamma_L", "gamma_U", "selected_action", "native_target",
        "deterministic_reason", "coverage_update",
    ]
    split_columns = [
        "parent_id", "eligible", "decision_valid", "split",
        "child_infeasibility_trigger", "strict_bound_trigger", "reason",
        "b_plus", "eta_proof", "eta_anchor", "normalization_source",
        "normalization_upper_bound",
    ]
    for role, template_name in SENTINELS:
        print(f"[semantic] {role}", flush=True)
        cap = 120 if role == "numerical_endpoint" else DEFAULT_CAP
        canonical_dir, canonical = run(
            role, template_name, "paper-k1-am-sf", "canonical", cap)
        legacy_dir, legacy = run(
            role, template_name, "k1-am-f0", "legacy_alias", cap)
        canonical_actions = selected_rows(
            canonical_dir / "external" / "adaptive_mass_decision_ledger.csv", action_columns)
        legacy_actions = selected_rows(
            legacy_dir / "external" / "adaptive_mass_decision_ledger.csv", action_columns)
        canonical_splits = selected_rows(
            canonical_dir / "external" / "split_decision_ledger.csv", split_columns)
        legacy_splits = selected_rows(
            legacy_dir / "external" / "split_decision_ledger.csv", split_columns)
        models_c = model_hashes(canonical_dir)
        models_l = model_hashes(legacy_dir)
        config_keys = [
            "round40_c6_coarse_start", "round45_point_rule",
            "round47_c6_adaptive_mass", "round47_c6_adaptive_mass_tau",
            "external_gini_tree_interval_mip_policy",
            "tailored_bc_callback_cut_profile", "tailored_bc_branching_priority",
            "round48_k1_amf", "round49_k1_am_rc",
            "gurobi_threads_requested", "gurobi_seed_requested",
            "gurobi_presolve_requested", "gurobi_mip_gap_requested",
            "gurobi_mip_gap_abs_requested",
        ]
        config_match = all(canonical.get(key) == legacy.get(key) for key in config_keys)
        objective_match = abs(float(canonical["objective"]) - float(legacy["objective"])) <= 1e-12
        bounds_match = (
            abs(float(canonical["lower_bound"]) - float(legacy["lower_bound"])) <= 1e-12
            and abs(float(canonical["upper_bound"]) - float(legacy["upper_bound"])) <= 1e-12
        )
        certificate_match = (
            canonical.get("strict_certificate_class") == legacy.get("strict_certificate_class")
            and canonical.get("certified_original_problem") == legacy.get("certified_original_problem")
        )
        actions_match = canonical_actions == legacy_actions and canonical_splits == legacy_splits
        model_match = models_c == models_l
        rows.append({
            "role": role,
            "instance": canonical["instance_name"],
            "canonical_preset": canonical["algorithm_preset"],
            "legacy_alias_requested": "k1-am-f0",
            "legacy_alias_canonicalized_to": legacy["algorithm_preset"],
            "audit_cap_seconds": cap,
            "deterministic_settings_match": config_match,
            "controller_actions_match": actions_match,
            "interval_endpoints_match": actions_match,
            "model_file_count": len(models_c),
            "model_fingerprints_match": model_match,
            "objective_match": objective_match,
            "bounds_match": bounds_match,
            "certificate_class_match": certificate_match,
            "semantic_equivalence": (
                config_match and actions_match and model_match
                and objective_match and bounds_match and certificate_match
            ),
            "bitwise_runtime_equivalence_required": False,
            "canonical_result": str((canonical_dir / "result.json").relative_to(ROOT)).replace("\\", "/"),
            "legacy_result": str((legacy_dir / "result.json").relative_to(ROOT)).replace("\\", "/"),
        })
    output = EVIDENCE / "paper_mainline_semantic_equivalence.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    if not all(row["semantic_equivalence"] for row in rows):
        raise RuntimeError("one or more paper preset sentinels failed semantic equivalence")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
