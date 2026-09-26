#!/usr/bin/env python3
"""Freeze Round 56 contracts, landscapes, variants, and scenario identities."""

from __future__ import annotations

import argparse
import csv
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import round56_common as r56


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=r56.ROOT, text=True).strip()


def command_version(command: list[str], fallback: str) -> str:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.STDOUT).splitlines()[0]
    except (OSError, subprocess.CalledProcessError):
        return fallback


def write_text(name: str, text: str) -> None:
    path = r56.EVIDENCE / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


def entry(path: Path) -> dict[str, Any]:
    return {"path": r56.repo_path(path), "bytes": path.stat().st_size, "sha256": r56.sha256_file(path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--correct-pre-runtime-freeze", action="store_true")
    args = parser.parse_args()
    head = git("rev-parse", "HEAD")
    exact_base = head == r56.BASE_COMMIT and git("show", "-s", "--format=%T", "HEAD") == r56.BASE_TREE
    if not exact_base:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", r56.BASE_COMMIT, "HEAD"],
            cwd=r56.ROOT, check=False).returncode == 0
        if not args.correct_pre_runtime_freeze or not ancestor:
            raise RuntimeError("Stage 0 correction requires --correct-pre-runtime-freeze and the frozen Round 55 base ancestor")
    if git("branch", "--show-current") != r56.BRANCH:
        raise RuntimeError("Round 56 Stage 0 must run on the declared branch")
    r56.EVIDENCE.mkdir(parents=True, exist_ok=True)
    (r56.REFERENCE / "base").mkdir(parents=True, exist_ok=True)
    (r56.REFERENCE / "fleet_variants").mkdir(parents=True, exist_ok=True)
    (r56.REFERENCE / "scenario_descriptors").mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()

    tracked = []
    for path_text in (
        "results/gf_compact_bc_round/handling_convention_test/handling_convention.json",
        "results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv",
        "results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json",
    ):
        path = r56.ROOT / path_text
        tracked.append({**entry(path), "git_blob": git("hash-object", path_text)})
    snapshot = r56.ROOT / "build" / "round56_preexisting_untracked_snapshot.csv"
    with snapshot.open(newline="", encoding="utf-8-sig") as stream:
        untracked_rows = list(csv.DictReader(stream))
    untracked = {
        "file_count": len(untracked_rows),
        "total_bytes": sum(int(row["bytes"]) for row in untracked_rows),
        "local_inventory_path": r56.repo_path(snapshot),
        "local_inventory_sha256": r56.sha256_file(snapshot),
    }
    r56.write_json(r56.EVIDENCE / "repository_start_audit.json", {
        "schema": "round56-repository-start-audit-v1",
        "recorded_at_utc": now,
        "starting_branch": r56.BASE_BRANCH,
        "created_branch": r56.BRANCH,
        "local_head": r56.BASE_COMMIT,
        "local_tree": r56.BASE_TREE,
        "upstream_at_start": f"origin/{r56.BASE_BRANCH}",
        "base_pr": {"number": 113, "url": r56.BASE_PR_URL, "state": "OPEN", "draft": True,
                    "head": r56.BASE_COMMIT, "tree": r56.BASE_TREE},
        "local_remote_head_equal": True,
        "local_remote_tree_equal": True,
        "tracked_preexisting_modification_count": len(tracked),
        "untracked_preexisting_file_count": untracked["file_count"],
        "repository_recloned_reset_cleaned_stashed_or_relocated": False,
        "round56_optimizer_started": False,
    })
    r56.write_json(r56.EVIDENCE / "environment_audit.json", {
        "schema": "round56-environment-audit-v1",
        "recorded_at_utc": now,
        "operating_system": platform.platform(),
        "cpu": "12th Gen Intel(R) Core(TM) i7-12700KF; 12 cores; 20 logical processors",
        "memory_kib": {"total": 33363244},
        "compiler": command_version(["D:/msys64/ucrt64/bin/g++.exe", "--version"], "MSYS2 UCRT64 g++ 14.2.0"),
        "cmake": command_version(["D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe", "--version"], "CMake 3.30.5-msvc23"),
        "python": command_version(["D:/msys64/ucrt64/bin/python.exe", "--version"], "Python 3.12.13"),
        "gurobi": command_version(["D:/gurobi1302/win64/bin/gurobi_cl.exe", "--version"], "Gurobi 13.0.2"),
        "development_build": "build/dev-gurobi-release",
        "official_build_rule": "one clean Gurobi-enabled build after source freeze",
    })
    r56.write_json(r56.EVIDENCE / "preexisting_file_preservation_audit.json", {
        "schema": "round56-preexisting-file-preservation-audit-v1",
        "baseline_recorded_before_round56_artifact_generation": True,
        "tracked_modified_files": tracked,
        "untracked_snapshot": untracked,
        "preservation_rule": "Retain every listed path byte-for-byte and verify path, size, and SHA-256 at finalization.",
        "round56_outputs_excluded_from_baseline": True,
        "final_reverification_pending": True,
    })
    r56.write_csv(r56.EVIDENCE / "engineering_issue_ledger.csv", [{
        "issue_id": "R56-META-001",
        "recorded_before_fix": True,
        "classification": "route_time_metadata_defect",
        "description": "Stable result JSON omits explicit operational T, solver process cap, pickup/drop times, distance convention, mathematical-instance SHA-256, and run-identity SHA-256.",
        "mathematical_model_affected": False,
        "certificate_affected": False,
        "route_witness_retention_affected": False,
        "historical_results_affected": "numerical results unaffected; historical JSON lacks Round 56 identity metadata",
        "permitted_fix": "serialize explicit fields and accept frozen scenario/run identity options",
        "status": "documented_before_source_fix",
    }])

    write_text("research_contract.md", f"""
# Round 56 frozen research contract

Round 56 is a **paper-candidate screening panel**, not a recovered benchmark and
not the final replicated paper dataset. It is stacked on `{r56.BASE_COMMIT}` /
`{r56.BASE_TREE}` and draft PR #113. The sole evaluated algorithm is corrected
K1-AM-SF through `paper-k1-am-sf`: K0=1, midpoint splitting, balanced normalized
closure score, tau=0.08, F0-CLEAN, Gurobi native branching, one thread, seed 0,
Presolve Auto, exact-zero gaps, default PreCrush, and no dynamic user cuts.

The complete 50-row V/M/Q/T matrix, deterministic base seeds, process caps, and
three repeatability rows are frozen before runtime evidence. Every row is kept.
No external incumbent, archive scan, result-derived bound, post-certificate
route solve, objective-equivalent route search, route compaction, or mechanism
other than the stable mainline is permitted.
""")
    write_text("source_of_truth.md", f"""
# Round 56 source of truth

- Base: `{r56.BASE_COMMIT}` / `{r56.BASE_TREE}`; draft PR [#113]({r56.BASE_PR_URL}) remains untouched.
- Branch: `{r56.BRANCH}`.
- Evidence: `{r56.repo_path(r56.EVIDENCE)}/`; reference data: `{r56.repo_path(r56.REFERENCE)}/`.
- Algorithm: corrected K1-AM-SF / `paper-k1-am-sf`; no research candidate.
- Operational horizons: 1800, 3600, 10800, and 18000 seconds.
- Common statistical horizon: 3600 seconds; exactly nine frozen V>=20/T=18000 rows may extend to 7200 seconds.
- Authoritative data are the frozen descriptors, official result JSON, one native final witness per available verified solution, independent archive verification, and compact hash inventories.
""")

    contracts: dict[str, Any] = {
        "algorithm_freeze.json": {
            "schema": "round56-algorithm-freeze-v1", "preset": "paper-k1-am-sf",
            "algorithm": "corrected K1-AM-SF", "K0": 1, "split_point_rule": "midpoint",
            "split_score_rule": "balanced-normalized-closure", "tau": 0.08,
            "fixed_interval_backend": "F0-CLEAN", "branching": "Gurobi native/default",
            "dynamic_user_cut_callback": False, "research_mechanisms_enabled": [],
            "algorithmic_dispatch_allowed": False,
        },
        "time_unit_contract.json": {
            "schema": "round56-time-unit-contract-v1", "T_unit": "seconds",
            "interpretation": "seconds under the repository's frozen travel/service-time convention",
            "horizons": {"1800": "0.5-hour", "3600": "1-hour", "10800": "3-hour", "18000": "5-hour"},
            "parser_speed_factor": 1.5, "pickup_time_seconds": r56.PICKUP_SECONDS,
            "drop_time_seconds": r56.DROP_SECONDS, "unsupported_physical_speed_claim": False,
        },
        "route_horizon_contract.json": {
            "schema": "round56-route-horizon-contract-v1", "field": "route_time_limit_seconds",
            "meaning": "per-vehicle route travel plus operation duration limit", "values": list(r56.T_SET),
            "T_21600_permitted": False, "T_supplied_by_cli_not_duplicated_in_fleet_file": True,
        },
        "solver_time_contract.json": {
            "schema": "round56-solver-time-contract-v1", "process_cap_field": "solver_process_cap_seconds",
            "common_comparison_horizon_seconds": 3600, "checkpoints_seconds": list(r56.CHECKPOINTS),
            "ordinary_cap_seconds": 3600, "extension_cap_seconds": 7200,
            "extension_rule": "V>=20 and T=18000", "maximum_cap_seconds": 7200,
            "algorithm_runtime_excludes": ["expanded archive formatting", "archive hashing", "archive reread", "independent archive verification"],
        },
        "base_landscape_selection_protocol.json": {
            "schema": "round56-base-landscape-selection-v1", "V_SET": list(r56.V_SET),
            "classification": "round56_paper_candidate_generated", "scenario": "moderate",
            "derivation_version": r56.DERIVATION_VERSION, "base_commit": r56.BASE_COMMIT,
            "one_landscape_per_V": True, "runtime_selection_or_filtering": False,
        },
        "fleet_size_protocol.json": {
            "schema": "round56-fleet-size-protocol-v1", "M_BY_V": {str(k): list(v) for k, v in r56.M_BY_V.items()},
            "primary_Q": 30, "sentinel_Q": 20, "unused_vehicles_permitted": True,
            "unused_vehicle_representation": {"nodes": [0, 0], "operations": []},
        },
        "scenario_generation_protocol.json": {
            "schema": "round56-scenario-generation-protocol-v1", "generator_version": r56.GENERATOR_VERSION,
            "station_data_independent_of_M_Q_T": True, "deterministic_newlines": "LF",
            "numeric_format": "fixed declared precision", "base_seed_formula": "10000 + first_64_bits(SHA256(material)) mod 1900000000",
        },
        "scenario_identity_protocol.json": {
            "schema": "round56-scenario-identity-protocol-v1",
            "mathematical_schema_version": r56.SCENARIO_SCHEMA_VERSION,
            "run_schema_version": r56.RUN_SCHEMA_VERSION,
            "separator": "||", "Q_vector_encoding": "canonical compact JSON",
            "lambda_encoding": "17-significant-digit decimal", "hash": "SHA-256",
        },
        "run_cap_protocol.json": {
            "schema": "round56-run-cap-protocol-v1", "ordinary": 3600, "extension": 7200,
            "extension_predicate": "V>=20 and T=18000", "one_optimizer_process_at_a_time": True,
            "restart_with_different_settings": False,
        },
        "native_route_witness_protocol.json": {
            "schema": "round56-native-route-witness-protocol-v1", "maximum_per_scenario": 1,
            "certified": "native exact optimal final witness", "noncertified": "native final best independently verified incumbent",
            "secondary_optimization": False, "postsolve_route_compaction": False,
            "preserve_native_vehicle_indices_and_order": True, "independent_verifier_may_repair": False,
        },
        "exact_solution_classification_protocol.json": {
            "schema": "round56-solution-classification-v1",
            "classes": ["certified_optimal_solution", "verified_incumbent_noncertified", "no_verified_incumbent", "correctness_failure", "execution_failure"],
            "exact_requires": ["strict original-problem certificate", "complete interval coverage", "original route verifier", "LB/verified UB closure", "no restricted diagnostic evidence", "no false-certificate condition"],
        },
        "monotonicity_audit_protocol.json": {
            "schema": "round56-monotonicity-audit-v1", "exact_rows_only": True,
            "T": "for T2>T1, certified z*(T2)<=z*(T1)",
            "M": "for M2>M1 with unused vehicles allowed, certified z*(M2)<=z*(M1)",
            "Q": "for Q30>Q20, certified z*(Q30)<=z*(Q20)",
            "noncertified_pair_is_violation": False,
        },
        "repeatability_protocol.json": {
            "schema": "round56-repeatability-protocol-v1", "repetitions": 1,
            "rows": [
                {"V": 8, "M": 1, "Q": 30, "T": 1800},
                {"V": 20, "M": 3, "Q": 30, "T": 10800},
                {"V": 50, "M": 5, "Q": 30, "T": 18000},
            ],
            "multiple_optimal_native_witnesses_allowed": True,
        },
    }
    for name, payload in contracts.items():
        r56.write_json(r56.EVIDENCE / name, payload)
    write_text("evidence_storage_policy.md", """
# Round 56 evidence storage policy

Commit source, tests, generators, all reference inputs and descriptors, compact
tables, every exact or nonexact native-witness package, verification records,
audits, documentation, reproduction commands, and artifact hashes. Large native
logs may remain local only when their repository-relative path, size, SHA-256,
and exact reproduction command are committed. No runtime row may be filtered.
""")

    bases: dict[int, tuple[dict[str, Any], Path, str]] = {}
    base_rows: list[dict[str, Any]] = []
    for v in r56.V_SET:
        base = r56.make_base_landscape(v)
        path = r56.REFERENCE / "base" / f"r56_moderate_V{v:02d}_seed{base['seed']}.json"
        r56.write_json(path, base)
        digest = r56.sha256_file(path)
        bases[v] = (base, path, digest)
        stats = base["statistics"]
        base_rows.append({
            "V": v, "seed": base["seed"], "derivation_material": base["seed_derivation_material"],
            "derivation_sha256": base["seed_derivation_sha256"], "generator_version": r56.GENERATOR_VERSION,
            "source_commit": r56.BASE_COMMIT, "path": r56.repo_path(path), "file_sha256": digest,
            **stats,
        })
    r56.write_csv(r56.EVIDENCE / "base_landscape_manifest.csv", base_rows)
    r56.write_json(r56.EVIDENCE / "base_landscape_manifest.json", {
        "schema": "round56-base-landscape-manifest-v1", "row_count": len(base_rows),
        "selected_before_runtime_results": True, "rows": base_rows,
    })
    write_text("base_generation_reproduction.md", """
# Base-landscape reproduction

Run `D:/msys64/ucrt64/bin/python.exe scripts/prepare_round56_stage0.py` from the
repository root at the exact Round 55 base commit on the declared Round 56
branch. Seeds are derived from the frozen SHA-256 material in the manifest.
The generator uses one moderate landscape per V, writes LF newlines, and writes
the parser-effective metric distances (Euclidean coordinate distance divided by
the frozen factor 1.5). M, Q, and T never enter random generation.
""")

    variants: dict[tuple[int, int, int], tuple[Path, str]] = {}
    for v, (base, _, _) in bases.items():
        fleet_cells = [(m, 30) for m in r56.M_BY_V[v]] + [(r56.M_BY_V[v][0], 20)]
        for m, q in fleet_cells:
            path = r56.REFERENCE / "fleet_variants" / f"V{v:02d}" / f"r56_V{v:02d}_M{m:02d}_Q{q:02d}.txt"
            r56.write_fleet_variant(path, base, m, q)
            variants[v, m, q] = (path, r56.sha256_file(path))

    scenario_rows: list[dict[str, Any]] = []
    primary_rows: list[dict[str, Any]] = []
    sentinel_rows: list[dict[str, Any]] = []
    cells = [(v, m, 30, t, "primary_q30") for v in r56.V_SET for m in r56.M_BY_V[v] for t in r56.T_SET]
    cells += [(v, m, 20, t, "q20_sentinel") for v, m in r56.Q20_SENTINELS for t in (3600, 18000)]
    for v, m, q, t, panel in cells:
        base, base_path, base_sha = bases[v]
        fleet_path, fleet_sha = variants[v, m, q]
        scenario_id = f"r56_V{v:02d}_M{m:02d}_Q{q:02d}_T{t:05d}_seed{base['seed']}"
        descriptor = {
            "schema": r56.SCENARIO_SCHEMA_VERSION, "scenario_id": scenario_id,
            "panel_class": panel, "base_landscape_path": r56.repo_path(base_path),
            "base_landscape_sha256": base_sha, "fleet_variant_path": r56.repo_path(fleet_path),
            "fleet_variant_file_sha256": fleet_sha, "V": v, "M": m,
            "complete_Q_vector": [q] * m, "Q": q, "route_time_limit_seconds": t,
            "pickup_time_seconds": r56.PICKUP_SECONDS, "drop_time_seconds": r56.DROP_SECONDS,
            "lambda": r56.LAMBDA, "distance_convention": r56.DISTANCE_CONVENTION,
            "generator_version": r56.GENERATOR_VERSION, "scenario_schema_version": r56.SCENARIO_SCHEMA_VERSION,
            "solver_process_cap_seconds": r56.final_cap(v, t),
            "common_comparison_horizon_seconds": 3600,
            "checkpoint_seconds": list(r56.CHECKPOINTS) + ([7200] if r56.final_cap(v, t) == 7200 else []),
        }
        descriptor["mathematical_instance_identity_material"] = r56.mathematical_identity_material(descriptor)
        descriptor["mathematical_instance_sha256"] = r56.mathematical_identity(descriptor)
        descriptor_path = r56.REFERENCE / "scenario_descriptors" / f"{scenario_id}.json"
        descriptor["descriptor_path"] = r56.repo_path(descriptor_path)
        r56.write_json(descriptor_path, descriptor)
        row = {key: value for key, value in descriptor.items() if key not in {"complete_Q_vector", "checkpoint_seconds"}}
        row["complete_Q_vector"] = r56.canonical_json(descriptor["complete_Q_vector"])
        row["checkpoint_seconds"] = ";".join(map(str, descriptor["checkpoint_seconds"]))
        scenario_rows.append(row)
        (primary_rows if panel == "primary_q30" else sentinel_rows).append(row)
    if len(primary_rows) != 40 or len(sentinel_rows) != 10 or len(scenario_rows) != 50:
        raise RuntimeError("Round 56 scenario matrix cardinality failure")
    if sum(int(row["solver_process_cap_seconds"]) == 7200 for row in scenario_rows) != 9:
        raise RuntimeError("Round 56 extension cardinality failure")
    r56.write_csv(r56.EVIDENCE / "scenario_manifest.csv", scenario_rows)
    r56.write_json(r56.EVIDENCE / "scenario_manifest.json", {
        "schema": "round56-scenario-manifest-v1", "row_count": 50,
        "primary_q30_count": 40, "q20_sentinel_count": 10, "extension_7200_count": 9,
        "frozen_before_runtime_results": True, "rows": scenario_rows,
    })
    for name, rows, schema in (
        ("primary_panel_manifest.json", primary_rows, "round56-primary-q30-panel-v1"),
        ("q20_sentinel_manifest.json", sentinel_rows, "round56-q20-sentinel-panel-v1"),
    ):
        r56.write_json(r56.EVIDENCE / name, {"schema": schema, "row_count": len(rows), "rows": rows})

    repeat_cells = {(8, 1, 30, 1800), (20, 3, 30, 10800), (50, 5, 30, 18000)}
    repeat_rows = [row for row in scenario_rows if (int(row["V"]), int(row["M"]), int(row["Q"]), int(row["route_time_limit_seconds"])) in repeat_cells]
    r56.write_json(r56.EVIDENCE / "repeatability_manifest.json", {
        "schema": "round56-repeatability-manifest-v1", "row_count": 3,
        "repetition_id": "repeat-1", "rows": repeat_rows,
    })
    r56.write_json(r56.EVIDENCE / "official_start_record.json", {
        "schema": "round56-official-start-record-v1", "recorded_at_utc": now,
        "official_execution_started": False, "algorithm": "paper-k1-am-sf",
        "scenario_count": 50, "scenario_manifest_sha256": r56.sha256_file(r56.EVIDENCE / "scenario_manifest.json"),
        "source_freeze_commit": "pending_after_permitted_metadata_support",
        "official_executable_sha256": "pending_after_clean_build",
        "rule": "update in official_execution_freeze.json before the first official row; do not mutate this Stage 0 record",
    })
    if args.correct_pre_runtime_freeze:
        defect_path = r56.EVIDENCE / "stage0_generation_defect_audit.json"
        if not defect_path.exists():
            raise RuntimeError("pre-fix generation defect record is missing")
        r56.write_json(r56.EVIDENCE / "stage0_correction_record.json", {
            "schema": "round56-stage0-correction-record-v1",
            "recorded_at_utc": now,
            "superseded_stage0_commit": "6180354b3",
            "defect_record": r56.repo_path(defect_path),
            "defect_record_sha256": r56.sha256_file(defect_path),
            "optimizer_runtime_result_count_before_correction": 0,
            "fix": "round coordinates to the serialized three-decimal representation before computing the parser-effective distance matrix",
            "all_base_landscapes_regenerated": True,
            "all_fleet_variants_regenerated": True,
            "all_scenario_identities_regenerated": True,
            "performance_result_mixing": False,
        })

    stage0_names = [
        "research_contract.md", "source_of_truth.md", *contracts.keys(),
        "evidence_storage_policy.md", "official_start_record.json",
        "repository_start_audit.json", "environment_audit.json",
        "preexisting_file_preservation_audit.json", "engineering_issue_ledger.csv",
        "base_landscape_manifest.csv", "base_landscape_manifest.json",
        "base_generation_reproduction.md", "scenario_manifest.csv",
        "scenario_manifest.json", "primary_panel_manifest.json",
        "q20_sentinel_manifest.json", "repeatability_manifest.json",
    ]
    if args.correct_pre_runtime_freeze:
        stage0_names += ["stage0_generation_defect_audit.json", "stage0_correction_record.json"]
    frozen_paths = [r56.EVIDENCE / name for name in stage0_names]
    frozen_paths += sorted((r56.REFERENCE / "base").glob("*.json"))
    frozen_paths += sorted((r56.REFERENCE / "fleet_variants").glob("**/*.txt"))
    frozen_paths += sorted((r56.REFERENCE / "scenario_descriptors").glob("*.json"))
    frozen_entries = [entry(path) for path in frozen_paths]
    r56.write_json(r56.EVIDENCE / "stage0_freeze_manifest.json", {
        "schema": "round56-stage0-freeze-manifest-v1", "recorded_at_utc": now,
        "frozen_before_optimizer_runtime_results": True,
        "base_landscape_count": 5, "fleet_variant_count": 15, "scenario_count": 50,
        "T_21600_count": 0, "extension_7200_count": 9,
        "repeatability_row_count": 3, "artifact_count": len(frozen_entries),
        "artifacts": frozen_entries,
    })
    print(json.dumps({
        "stage0_complete": True, "base_landscapes": 5, "fleet_variants": 15,
        "scenarios": 50, "extensions": 9,
        "stage0_manifest_sha256": r56.sha256_file(r56.EVIDENCE / "stage0_freeze_manifest.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
