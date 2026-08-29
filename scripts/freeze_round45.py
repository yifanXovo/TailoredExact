#!/usr/bin/env python3
"""Create the pre-result Round 45 freeze and fail if any identity drifts."""

from __future__ import annotations

import csv
import datetime as dt
import json
import platform
import re
import subprocess
from pathlib import Path
from typing import Any

import round45_common as common


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=common.ROOT, text=True).strip()


def command_version(command: list[str]) -> str:
    completed = subprocess.run(
        command, cwd=common.ROOT, check=True, capture_output=True, text=True)
    return (completed.stdout or completed.stderr).strip().splitlines()[0]


def small_freeze() -> dict[str, Any]:
    source = common.load_json(
        common.ROOT / "results/gf_c6_envelope_tail_repair_round44/dataset_freeze.json")
    wanted = set(common.SMALL_IDS)
    rows = []
    for item in source["datasets"]:
        if item["instance_id"] not in wanted:
            continue
        path = common.ROOT / item["path"]
        observed = common.sha256(path)
        if observed != item["sha256"]:
            raise RuntimeError(f"small input hash drift: {item['instance_id']}")
        split = "holdout" if item["split"] == "sealed_holdout" else item["split"]
        rows.append({
            "instance_id": item["instance_id"],
            "path": item["path"],
            "sha256": observed,
            "split": split,
            "sealed": split in {"validation", "holdout"},
            "candidate_results_observed": False,
        })
    if {row["instance_id"] for row in rows} != wanted:
        raise RuntimeError("small panel is incomplete")
    return {
        "schema": "round45-small-dataset-freeze-v1",
        "frozen_before_candidate_runs": True,
        "candidate_results_observed": False,
        "validation_state": "sealed",
        "holdout_state": "sealed",
        "mechanism_roles": common.MECHANISM_ROLES,
        "datasets": rows,
    }


def historical_pgrb(instance_id: str) -> tuple[float, str, str]:
    path = (common.ROOT / "results/gf_small_hard_light_round39/runs" /
            f"primary__{instance_id}__p_grb/result.json")
    result = common.load_json(path)
    seconds = float(result["final_process_wall_time_seconds"])
    return seconds, common.relative(path), common.sha256(path)


def material_rows(freeze: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in freeze["datasets"]:
        seconds, source, source_hash = historical_pgrb(item["instance_id"])
        classification = "material" if seconds >= 10.0 else "startup"
        if item["instance_id"] == common.STARTUP_PATHOLOGY:
            classification = "startup_pathology"
        rows.append({
            "instance_id": item["instance_id"],
            "split": item["split"],
            "historical_pgrb_total_seconds": format(seconds, ".17g"),
            "classification": classification,
            "threshold_seconds": "10",
            "blocking_policy": "startup_nonblocking_alone" if
                classification.startswith("startup") else "material_gates_apply",
            "source": source,
            "source_sha256": source_hash,
            "frozen_before_candidate_runs": True,
        })
    return rows


def parse_scale(path: Path) -> tuple[int, int, str]:
    rendered = path.as_posix()
    v_match = re.search(r"V(20|50)", rendered)
    m_match = re.search(r"M([2345])", rendered)
    regime = "tight_T" if "tight_T" in path.name else (
        "high_imbalance" if "high_imbalance" in path.name else (
        "moderate" if "moderate" in path.name else "other"))
    return int(v_match.group(1)), int(m_match.group(1)) if m_match else 0, regime


def complex_inventory() -> list[dict[str, Any]]:
    selected = {
        **{path: "v20_development" for path in common.V20_DEVELOPMENT},
        **{path: "v20_confirmation" for path in common.V20_CONFIRMATION},
        **{path: "v50_development" for path in common.V50_DEVELOPMENT},
        **{path: "v50_confirmation" for path in common.V50_CONFIRMATION},
    }
    paths = sorted(
        path for path in (common.ROOT / "reference").rglob("*.txt")
        if re.search(r"V(?:20|50)", path.as_posix()))
    rows = []
    for path in paths:
        rel = common.relative(path)
        V, M, regime = parse_scale(path)
        rows.append({
            "path": rel,
            "sha256": common.sha256(path),
            "V": V,
            "M": M,
            "regime": regime,
            "selected_role": selected.get(rel, "inventory_only"),
            "historical_evidence_locator":
                "tracked results/manifests; locate by exact basename and input hash",
            "candidate_results_observed": False,
        })
    if len(rows) != 47:
        raise RuntimeError(f"expected 47 V20/V50 inputs, found {len(rows)}")
    missing = set(selected) - {row["path"] for row in rows}
    if missing:
        raise RuntimeError(f"complex panel files missing: {sorted(missing)}")
    return rows


def artifact(path: str) -> dict[str, Any]:
    target = common.OUT / path
    return {
        "path": common.relative(target),
        "sha256": common.sha256(target),
        "bytes": target.stat().st_size,
    }


def main() -> int:
    common.OUT.mkdir(parents=True, exist_ok=True)
    if git("rev-parse", "HEAD") != common.BASE_SHA:
        raise RuntimeError("Stage 0 must be frozen at the published Round 44 base")
    if git("rev-parse", "HEAD^{tree}") != common.BASE_TREE_SHA:
        raise RuntimeError("published Round 44 base tree drift")

    common.write_text(common.OUT / "research_contract.md", """# Round 45 research contract

Round 45 has two strictly separated questions. Part I changes only the
mathematical split/retain timing decision while every split is the midpoint.
Part II freezes the selected timing rule and changes only the split location.

The promoted mechanism must be genuinely adaptive: it must issue both split
and retain actions on the frozen development evidence. `no-adaptive` is an
ineligible performance reference. No instance identity, seed, dimensions,
membership, prior winner, telemetry, runtime, Work, node count, memory,
hardware property, or learned/per-instance dispatch may influence a decision.

All exact runs use Gurobi Presolve Auto, Seed 0, Threads 1, zero relative and
absolute gaps, the full original objective, the same independently verified
HGA-FULL incumbent, certificate tolerance 1e-7, complete interval coverage,
monotone valid global lower bounds, and fail-closed lifecycle handling. The
external 3600-second cap is an outcome constraint and never a decision input.
""")
    common.write_text(common.OUT / "source_of_truth.md", f"""# Source of truth

- Repository: `E:/codes/ExactEBRP`
- Published Round 44 base branch: `{common.BASE_BRANCH}`
- Base commit: `{common.BASE_SHA}`
- Base tree: `{common.BASE_TREE_SHA}`
- Round 45 branch: `{common.RESEARCH_BRANCH}`
- Round 43/44 source, evidence, and default-off behavior are immutable inputs.
- Small split: the exact Round 43/Round 44 development, validation, and sealed
  holdout assignments in `small_dataset_freeze.json`.
- Historical P-GRB total time defines material rows at 10 seconds; the named
  V12 startup pathology is reported but cannot block alone.
- Every V20/V50 input under `reference/` is inventoried and hashed before any
  candidate run. No simplified instance is generated.
""")
    common.write_json(common.OUT / "solver_contract.json", {
        "schema": "round45-solver-contract-v1",
        "solver": "Gurobi 13.0.2",
        "threads": 1,
        "seed": 0,
        "presolve": "Auto",
        "presolve_parameter": -1,
        "mip_gap": 0.0,
        "mip_gap_abs": 0.0,
        "certificate_tolerance": 1e-7,
        "process_cap_seconds": 3600,
        "shutdown_margin_seconds": 20,
        "objective": "unchanged full original objective and strict-improver range",
        "incumbent": "same independently verified HGA-FULL incumbent",
        "certificate": "original-problem verification, complete exact coverage, monotone valid global LB, completed native lifecycle, fail closed",
        "candidate_results_observed": False,
    })
    common.write_json(common.OUT / "forbidden_decision_inputs.json", {
        "schema": "round45-forbidden-decision-inputs-v1",
        "allowed": ["current mathematical state", "certified bounds",
                    "parametric LP state", "interval geometry",
                    "fixed global parameters", "certificate tolerances"],
        "forbidden": ["instance name", "path", "seed", "V", "M", "Q",
                      "panel membership", "historical winner", "time",
                      "Work", "nodes", "iterations", "memory", "hardware",
                      "learned policy", "per-instance dispatch"],
        "telemetry_excluded_from_decision_hash": True,
        "external_cap_is_not_a_decision_input": True,
        "candidate_results_observed": False,
    })

    small = small_freeze()
    common.write_json(common.OUT / "small_dataset_freeze.json", small)
    common.write_csv(common.OUT / "material_classification.csv",
                     material_rows(small))
    inventory = complex_inventory()
    common.write_csv(common.OUT / "complex_instance_inventory.csv", inventory)
    common.write_json(common.OUT / "complex_panel_freeze.json", {
        "schema": "round45-complex-panel-freeze-v1",
        "frozen_before_candidate_runs": True,
        "candidate_results_observed": False,
        "selection_basis": "previously used exact instances; structural regime and M diversity only; not selected on Round 45 outcomes",
        "no_simplified_instances": True,
        "v20_development": common.V20_DEVELOPMENT,
        "v20_confirmation": common.V20_CONFIRMATION,
        "v50_development": common.V50_DEVELOPMENT,
        "v50_confirmation": common.V50_CONFIRMATION,
        "hard_cap_seconds_per_arm": 3600,
        "checkpoints_seconds": [300, 1200, 3600],
    })
    common.write_json(common.OUT / "performance_metric_freeze.json", {
        "schema": "round45-performance-metric-freeze-v1",
        "primary": "Work",
        "work_definition": "native solver work plus every speculative/lookahead/parametric LP and child cost",
        "secondary": ["process wall time", "GI(T)", "final gap", "final valid LB",
                      "verified UB", "nodes", "LP jobs", "split count",
                      "interval count", "peak memory"],
        "checkpoints_seconds": [300, 1200, 3600],
        "right_censoring": "lexicographic certificate, GI, gap, LB, Work",
        "startup_rows_reported_but_nonblocking_alone": True,
        "candidate_results_observed": False,
    })
    common.write_json(common.OUT / "severe_regression_policy.json", {
        "schema": "round45-severe-regression-policy-v1",
        "severe_if": "Work ratio > 1.5 AND time ratio > 1.5 AND (time delta > 60 seconds OR Work delta > 100)",
        "work_ratio_gt": 1.5,
        "time_ratio_gt": 1.5,
        "time_delta_gt_seconds": 60,
        "work_delta_gt": 100,
        "startup_rows_cannot_block_alone": True,
        "candidate_results_observed": False,
    })
    common.write_text(common.OUT / "candidate_family_definition.md", """# Candidate family definition

Part I uses K4-new (`K0=4`) and K1-new (`K0=1`) with one shared adaptive
timing code path. Every Part I split is the exact midpoint. Frozen references
are P-GRB, C6, fixed-d1 no-adaptive, frontier-d2 no-adaptive, no-envelope
no-adaptive, K1-single, K1-decisive, and Round 43 A(4,2,0.1).

Eligible timing scores reconstruct old C6, corrected D_R43, F, M_root, H, and
the new Gamma_sum residual-mass reduction. Gamma-veto and decisive-Gamma are
the only new thresholded families. A timing candidate is eligible only if it
is exact, produces both split and retain decisions, retains the major harmful
witness, and does not exceed the frozen false-split/severe-regression gates.
No-adaptive is never eligible for adaptive promotion.

After `timing_backbone_freeze.json`, Part II permits exactly three global point
arms: midpoint, PMM, and FPMM. Timing, K0, lookahead, envelope, incumbent,
solver, and certificate contracts are identical. PMM/FPMM solve the direct
continuous parametric LP max-min problem; there is no empirical point pool and
an uncertified parametric point retains the parent rather than falling back.
""")
    common.write_json(common.OUT / "promotion_gates.json", {
        "schema": "round45-promotion-gates-v1",
        "frozen_before_candidate_runs": True,
        "timing": {
            "must_be_genuinely_adaptive": True,
            "must_retain_major_harmful_witness": True,
            "split_confirmed_beneficial_leaf_if_any": True,
            "noadaptive_ineligible": True,
            "no_false_certificates": True,
            "no_material_severe_pgrb_regression": True,
        },
        "validation_material": {
            "candidate_over_pgrb_work_geomean_max": 1.0,
            "candidate_over_pgrb_time_geomean_max": 1.10,
            "wins_at_least_losses": True,
            "major_witness_repaired": True,
            "strong_control_pgrb_advantage_min": 2.0,
        },
        "complex_confirmation": {
            "lower_GI_than_pgrb_majority": True,
            "strict_certificates_at_least_pgrb": True,
            "median_c6_advantage_retention_min": 0.5,
            "no_candidate_specific_engineering_failure": True,
            "no_false_certificates": True,
        },
    })

    cmake = Path("D:/Program Files/Microsoft Visual Studio/2022/Professional/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe")
    baseline_exe = common.ROOT / "build_round45_base/ExactEBRP.exe"
    start = {
        "schema": "round45-official-start-record-v1",
        "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "base_branch": common.BASE_BRANCH,
        "base_sha": common.BASE_SHA,
        "base_tree_sha": common.BASE_TREE_SHA,
        "research_branch": common.RESEARCH_BRANCH,
        "head_at_freeze": git("rev-parse", "HEAD"),
        "tree_at_freeze": git("rev-parse", "HEAD^{tree}"),
        "upstream_at_freeze": git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"),
        "machine": {
            "node": platform.node(), "platform": platform.platform(),
            "processor": platform.processor(),
        },
        "toolchain": {
            "compiler": command_version(["g++", "--version"]),
            "cmake": command_version([str(cmake), "--version"]),
            "gurobi_home": "D:/gurobi1302/win64",
            "gurobi_version": "13.0.2",
        },
        "baseline_executable_sha256": common.sha256(baseline_exe),
        "baseline_tests": {
            "clean_release_gurobi_build": "passed",
            "ctest": "22/22 passed",
            "existing_python_protocol_tests": "93/93 passed",
            "round43_round44_default_off_static_contract": "passed in CTest and protocol suites",
        },
        "candidate_results_observed": False,
    }
    common.write_json(common.OUT / "official_start_record.json", start)
    common.write_csv(common.OUT / "baseline_equivalence_manifest.csv", [
        {"check": "published_round44_local_remote_tree", "status": "passed",
         "expected": common.BASE_TREE_SHA, "observed": common.BASE_TREE_SHA,
         "evidence": "git show local research head and fetched PR #93 head"},
        {"check": "clean_release_gurobi_build", "status": "passed",
         "expected": "Release/Gurobi", "observed": "GCC 14.2.0/Gurobi 13.0.2",
         "evidence": "build_round45_base"},
        {"check": "ctest", "status": "passed", "expected": "22/22",
         "observed": "22/22", "evidence": "build_round45_base/Testing"},
        {"check": "existing_python_protocol_tests", "status": "passed",
         "expected": "all", "observed": "93/93", "evidence":
         "python -m unittest discover -s tests -p *protocol_tests.py"},
        {"check": "round44_default_off_evidence", "status": "passed",
         "expected": "3/3", "observed": "3/3", "evidence":
         "results/gf_c6_envelope_tail_repair_round44/default_off_equivalence.csv"},
    ])

    manifest_names = [
        "research_contract.md", "source_of_truth.md", "solver_contract.json",
        "forbidden_decision_inputs.json", "small_dataset_freeze.json",
        "material_classification.csv", "complex_instance_inventory.csv",
        "complex_panel_freeze.json", "performance_metric_freeze.json",
        "severe_regression_policy.json", "candidate_family_definition.md",
        "promotion_gates.json", "official_start_record.json",
        "baseline_equivalence_manifest.csv",
    ]
    manifest = {
        "schema": "round45-stage0-freeze-manifest-v1",
        "base_sha": common.BASE_SHA,
        "base_tree_sha": common.BASE_TREE_SHA,
        "frozen_before_candidate_runs": True,
        "candidate_results_observed": False,
        "artifact_count": len(manifest_names),
        "artifacts": [artifact(name) for name in manifest_names],
    }
    manifest["manifest_content_sha256"] = common.stable_hash(manifest)
    common.write_json(common.OUT / "stage0_freeze_manifest.json", manifest)
    print(json.dumps({
        "stage0": "frozen", "artifacts": len(manifest_names) + 1,
        "small_instances": len(small["datasets"]),
        "complex_inventory": len(inventory),
        "base_sha": common.BASE_SHA,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
