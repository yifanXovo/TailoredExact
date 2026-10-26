#!/usr/bin/env python3
"""Run the frozen Round 55 first-class/legacy K1 semantic sentinels."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


EVIDENCE_REL = Path("results/gf_k1_am_sf_station_state_chain_round55")
ROUND53_RUNS = Path("results/gf_k1_f0_callback_isolation_round53/local_raw/k1_panel_runs")
ROUND47_RUNS = Path("results/gf_c6_adaptive_mass_contraction_round47/runs")
SENTINELS = (
    ("major", ROUND53_RUNS / "integration__round39_small_medium_V12_M3_Q30_slot08_seed1343324363__K1-AM-CANDIDATE__300s", 20),
    ("strong_control", ROUND53_RUNS / "integration__round39_small_hard_V12_M3_Q30_slot08_seed1288546114__K1-AM-CANDIDATE__300s", 20),
    ("v10_easy_negative", ROUND53_RUNS / "integration__round39_small_hard_V10_M3_Q20_slot04_seed1145042375__K1-AM-CANDIDATE__300s", 20),
    ("numerical_endpoint", ROUND53_RUNS / "integration__round39_small_hard_V12_M3_Q20_slot07_seed621538683__K1-AM-CANDIDATE__300s", 120),
    ("v12_m2_hard", ROUND53_RUNS / "integration__round39_small_hard_V12_M2_Q20_slot06_seed258908503__K1-AM-CANDIDATE__300s", 20),
    ("startup_easy_v12", ROUND53_RUNS / "integration__round39_small_easy_V12_M3_Q30_slot08_seed1167625600__K1-AM-CANDIDATE__300s", 20),
    ("tight3102", ROUND47_RUNS / "stage5_1800s__tight_T_seed3102__K1-AM", 20),
    ("high_imbalance_3201", ROUND47_RUNS / "stage5_1800s__high_imbalance_seed3201__K1-AM", 20),
    ("moderate3301", ROUND47_RUNS / "stage5_1800s__moderate_seed3301__K1-AM", 20),
    ("v20_sentinel", ROUND53_RUNS / "sentinel__round52_validation_moderate_3600_V20_M3_seed1783533980__K1-AM-CANDIDATE__300s", 20),
    ("v50_sentinel", ROUND53_RUNS / "sentinel__round52_validation_moderate_3600_V50_M3_seed664120090__K1-AM-CANDIDATE__300s", 20),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def set_option(command: list[str], option: str, value: str) -> None:
    if option in command:
        command[command.index(option) + 1] = value


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


def run_arm(root: Path, executable: Path, role: str, template_rel: Path,
            preset: str, arm: str, cap: int) -> tuple[Path, dict]:
    executable_hash = sha256(executable)
    template = json.loads((root / template_rel / "command.json").read_text(encoding="utf-8"))
    command = list(template["command"])
    command[0] = str(executable)
    run_dir = root / EVIDENCE_REL / "local_raw/stable_requalification_sentinels" / role / arm
    result_path = run_dir / "result.json"
    record_path = run_dir / "command.json"
    if result_path.exists() and record_path.exists():
        prior = json.loads(record_path.read_text(encoding="utf-8"))
        if (prior.get("preset") == preset and prior.get("cap_seconds") == cap
                and prior.get("executable_sha256") == executable_hash
                and prior.get("return_code") == 0):
            return run_dir, json.loads(result_path.read_text(encoding="utf-8"))
    run_dir.mkdir(parents=True, exist_ok=True)
    replacements = {
        "--algorithm-preset": preset,
        "--time-limit": str(max(1, cap - 6)),
        "--process-wall-time-limit": str(cap),
        "--process-shutdown-margin": "2",
        "--primal-heuristic-generation-log": str(run_dir / "hga_generations.csv"),
        "--progress-log": str(run_dir / "progress.csv"),
        "--process-phase-ledger": str(run_dir / "process_phases.csv"),
        "--heuristic-candidates-csv": str(run_dir / "heuristic_candidates.csv"),
        "--external-gini-artifact-dir": str(run_dir / "external"),
        "--log": str(run_dir / "native.log"),
        "--out": str(result_path),
        "--round24-executable-sha256": executable_hash,
        "--round24-manifest-executable-sha256": executable_hash,
    }
    for option, value in replacements.items():
        set_option(command, option, value)
    completed = subprocess.run(
        command, cwd=root, text=True, capture_output=True,
        timeout=cap + 60, check=False,
    )
    (run_dir / "stdout.txt").write_text(completed.stdout, encoding="utf-8")
    (run_dir / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
    record_path.write_text(json.dumps({
        "schema": "round55-stable-requalification-command-v1",
        "role": role, "arm": arm, "preset": preset, "cap_seconds": cap,
        "executable_sha256": executable_hash, "command": command,
        "return_code": completed.returncode,
    }, indent=2) + "\n", encoding="utf-8")
    if completed.returncode != 0 or not result_path.exists():
        raise RuntimeError(f"{role}/{arm} failed: {completed.stderr[-800:]}")
    return run_dir, json.loads(result_path.read_text(encoding="utf-8"))


def run_pair(root: Path, executable: Path, role: str, template_rel: Path, cap: int) -> dict:
    canonical_dir, canonical = run_arm(
        root, executable, role, template_rel, "paper-k1-am-sf", "first_class", cap)
    legacy_dir, legacy = run_arm(
        root, executable, role, template_rel, "k1-am-f0", "legacy_alias", cap)
    action_columns = [
        "decision_sequence", "K0", "tau", "interval_id", "parent_id", "depth",
        "gamma_L", "gamma_U", "selected_action", "native_target",
        "deterministic_reason", "coverage_update",
    ]
    split_columns = [
        "parent_id", "eligible", "decision_valid", "split",
        "child_infeasibility_trigger", "strict_bound_trigger", "reason", "b_plus",
        "eta_proof", "eta_anchor", "normalization_source", "normalization_upper_bound",
    ]
    canonical_actions = selected_rows(
        canonical_dir / "external/adaptive_mass_decision_ledger.csv", action_columns)
    legacy_actions = selected_rows(
        legacy_dir / "external/adaptive_mass_decision_ledger.csv", action_columns)
    actions_equal = (
        canonical_actions == legacy_actions
        and selected_rows(canonical_dir / "external/split_decision_ledger.csv", split_columns)
        == selected_rows(legacy_dir / "external/split_decision_ledger.csv", split_columns)
    )
    canonical_models = model_hashes(canonical_dir)
    legacy_models = model_hashes(legacy_dir)
    common_models = set(canonical_models) & set(legacy_models)
    # A wall-capped sentinel can finish constructing one additional leaf in
    # one arm.  The contract requires equal fingerprints where the same model
    # is constructed, not equal work completed after the cap.
    model_equal = all(
        canonical_models[name] == legacy_models[name] for name in common_models)
    config_keys = [
        "round40_c6_coarse_start", "round45_point_rule", "round47_c6_adaptive_mass",
        "round47_c6_adaptive_mass_tau", "external_gini_tree_interval_mip_policy",
        "tailored_bc_callback_cut_profile", "tailored_bc_branching_priority",
        "round48_k1_amf", "round49_k1_am_rc", "gurobi_threads_requested",
        "gurobi_seed_requested", "gurobi_presolve_requested",
        "gurobi_mip_gap_requested", "gurobi_mip_gap_abs_requested",
    ]
    config_equal = all(canonical.get(key) == legacy.get(key) for key in config_keys)
    objective_equal = abs(float(canonical["objective"]) - float(legacy["objective"])) <= 1e-12
    bounds_equal = (
        abs(float(canonical["lower_bound"]) - float(legacy["lower_bound"])) <= 1e-12
        and abs(float(canonical["upper_bound"]) - float(legacy["upper_bound"])) <= 1e-12
    )
    certificate_equal = (
        canonical.get("strict_certificate_class") == legacy.get("strict_certificate_class")
        and canonical.get("certified_original_problem") == legacy.get("certified_original_problem")
    )
    return {
        "role": role,
        "instance": canonical["instance_name"],
        "cap_seconds": cap,
        "first_class_preset": canonical["algorithm_preset"],
        "legacy_alias_canonicalized_to": legacy["algorithm_preset"],
        "K0": canonical_actions[0][1] if canonical_actions else "1",
        "tau": canonical_actions[0][2] if canonical_actions else "0.08",
        "fixed_interval_policy": canonical.get("external_gini_tree_interval_mip_policy", ""),
        "config_equal": config_equal,
        "actions_equal": actions_equal,
        "interval_endpoints_equal": actions_equal,
        "model_fingerprints_equal": model_equal,
        "first_class_model_count": len(canonical_models),
        "legacy_model_count": len(legacy_models),
        "common_model_count": len(common_models),
        "objective_equal": objective_equal,
        "bounds_equal": bounds_equal,
        "certificate_class_equal": certificate_equal,
        "semantic_equivalence": all((config_equal, actions_equal, model_equal,
                                     objective_equal, bounds_equal, certificate_equal)),
        "first_class_result": (canonical_dir / "result.json").relative_to(root).as_posix(),
        "legacy_result": (legacy_dir / "result.json").relative_to(root).as_posix(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    args = parser.parse_args()
    root = args.root.resolve()
    executable = args.executable if args.executable.is_absolute() else root / args.executable
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.jobs, len(SENTINELS)))) as pool:
        futures = {
            pool.submit(run_pair, root, executable, role, template, cap): role
            for role, template, cap in SENTINELS
        }
        for ordinal, future in enumerate(as_completed(futures), start=1):
            role = futures[future]
            rows.append(future.result())
            print(f"[{ordinal}/{len(SENTINELS)}] {role}", flush=True)
    order = {role: index for index, (role, _, _) in enumerate(SENTINELS)}
    rows.sort(key=lambda row: order[row["role"]])
    output = root / EVIDENCE_REL / "stable_requalification_semantic_sentinels.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    decision = {
        "schema": "round55-stable-requalification-sentinels-v1",
        "sentinel_count": len(rows),
        "executable_sha256": sha256(executable),
        "all_semantically_equivalent": all(row["semantic_equivalence"] for row in rows),
        "failed_roles": [row["role"] for row in rows if not row["semantic_equivalence"]],
    }
    (root / EVIDENCE_REL / "stable_requalification_semantic_sentinels.json").write_text(
        json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2))
    return 0 if decision["all_semantically_equivalent"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
