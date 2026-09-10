#!/usr/bin/env python3
"""Freeze Round 50 vNext after the bounded fixed-interval iterations."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
SOURCE = EVIDENCE / "iteration3_revision_v0_300s.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True).strip()


def main() -> None:
    with SOURCE.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if [row["state_id"] for row in rows] != [f"D{i}" for i in range(1, 15)]:
        raise RuntimeError("final post-iteration v0 rerun is incomplete")
    if len({row["executable_sha256"] for row in rows}) != 1:
        raise RuntimeError("final post-iteration rerun used multiple executables")
    if any(row["policy"] != "interval-mip-v0" for row in rows):
        raise RuntimeError("unexpected execution policy in final v0 rerun")

    out_path = EVIDENCE / "interval_mip_vnext_300s_results.csv"
    fields = ["frozen_backend", "execution_equivalence_basis", *rows[0].keys()]
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "frozen_backend": "Interval-MIP-vNext",
                "execution_equivalence_basis":
                    "no accepted factor; vNext is byte-identical to interval-mip-v0",
                **row,
            })

    ablation_path = EVIDENCE / "interval_mip_ablation_chain.csv"
    ablation_fields = [
        "state_id", "baseline_policy", "cumulative_policy",
        "accepted_factor_count", "baseline_certificate",
        "cumulative_certificate", "baseline_work", "cumulative_work",
        "baseline_process_seconds", "cumulative_process_seconds",
        "baseline_gi", "cumulative_gi", "equivalent",
    ]
    with ablation_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ablation_fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "state_id": row["state_id"],
                "baseline_policy": "Interval-MIP-v0",
                "cumulative_policy": "Interval-MIP-vNext",
                "accepted_factor_count": 0,
                "baseline_certificate": row["certificate"],
                "cumulative_certificate": row["certificate"],
                "baseline_work": row["work"],
                "cumulative_work": row["work"],
                "baseline_process_seconds": row["process_time_seconds"],
                "cumulative_process_seconds": row["process_time_seconds"],
                "baseline_gi": row["gi_common_horizon"],
                "cumulative_gi": row["gi_common_horizon"],
                "equivalent": True,
            })

    source_files = [
        "CMakeLists.txt",
        "include/CanonicalCompactModel.hpp",
        "include/FixedIntervalMipBackend.hpp",
        "include/Round50IntervalMip.hpp",
        "scripts/run_round50_fixed_interval_panel.py",
        "src/CplexBaseline.cpp",
        "src/GurobiBaseline.cpp",
        "src/Round50IntervalMip.cpp",
        "src/round50_interval_mip_main.cpp",
        "tests/round50_interval_mip_tests.cpp",
    ]
    runtime_options = {
        "Gurobi.MIPGap": 0,
        "Gurobi.MIPGapAbs": 0,
        "Gurobi.Presolve": "Auto",
        "Gurobi.Seed": 0,
        "Gurobi.Threads": 1,
        "archive_winner_injection": False,
        "evidence_finalization_reserve_seconds": 2,
        "known_optimum_injection": False,
        "lambda": 0.15,
        "process_cap_seconds_development": 300,
    }
    definition = {
        "schema": "round50-interval-mip-vnext-definition-v1",
        "name": "Interval-MIP-vNext",
        "definition_equivalence": "Interval-MIP-v0",
        "accepted_modification_count": 0,
        "branching_policy": "Gurobi default; no branch priorities",
        "strengthening_families": {
            "enabled": [
                "v0 complete compact fixed-interval formulation",
                "round20-current root connectivity flow",
                "round19 interval row factory",
                "safe low-Gini strengthening",
                "tight denominator bounds",
                "adaptive objective estimator",
                "two-round iterative domain propagation",
                "variable-s centering",
                "paper-safe tight sp-product estimator",
            ],
            "disabled": [
                "Round 50 exact duplicate elimination",
                "dynamic cut families",
                "callback cut profile",
                "Gini branching",
                "candidate branch priorities",
            ],
            "delayed": [],
        },
        "new_or_tightened_cuts": [],
        "cut_formulation_policy": "original v0 cut/formulation pack",
        "symmetry_constraints": "v0 nonincreasing route-use cardinality for identical vehicles",
        "numerical_changes": [],
        "model_reuse_policy": "build/read/optimize one fixed-state MIP; no reuse",
        "runtime_dispatch": False,
        "source_files": source_files,
        "runtime_options": runtime_options,
        "development_executable_sha256": rows[0]["executable_sha256"],
        "official_executable_sha256": "pending-clean-official-build",
    }
    definition_path = EVIDENCE / "interval_mip_vnext_definition.json"
    definition_path.write_text(
        json.dumps(definition, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    decisions = {
        "branching": "branching_iteration_decision.json",
        "cut_formulation": "cut_formulation_iteration_decision.json",
        "symmetry_numerical": "symmetry_numerical_iteration_decision.json",
        "model_reuse": "model_reuse_iteration_decision.json",
    }
    manifest = {
        "schema": "round50-interval-mip-vnext-freeze-manifest-v1",
        "status": "frozen_before_confirmation",
        "source_commit": git("rev-parse", "HEAD"),
        "source_tree": git("rev-parse", "HEAD^{tree}"),
        "accepted_modification_count": 0,
        "frozen_backend": "Interval-MIP-vNext",
        "definition_equivalence": "Interval-MIP-v0",
        "development_row_count": len(rows),
        "development_certificate_count": sum(
            row["certificate"].lower() == "true" for row in rows),
        "development_false_certificate_count": sum(
            row["false_certificate"].lower() == "true" for row in rows),
        "development_executable_sha256": rows[0]["executable_sha256"],
        "official_executable_sha256": "pending-clean-official-build",
        "input_hashes": {
            str(SOURCE.relative_to(ROOT)).replace("\\", "/"): sha256(SOURCE),
            str(out_path.relative_to(ROOT)).replace("\\", "/"): sha256(out_path),
            str(ablation_path.relative_to(ROOT)).replace("\\", "/"): sha256(ablation_path),
            str(definition_path.relative_to(ROOT)).replace("\\", "/"): sha256(definition_path),
            **{
                f"results/gf_k1_interval_mip_vnext_round50/{name}":
                    sha256(EVIDENCE / name)
                for name in decisions.values()
            },
        },
        "iteration_decisions": decisions,
        "confirmation_opened": False,
        "post_confirmation_tuning_allowed": False,
        "runtime_dispatch": False,
    }
    manifest_path = EVIDENCE / "interval_mip_vnext_freeze_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    history = """# Round 50 bounded iteration history

| Iteration | Family | Entered candidates | Result | Active policy after iteration |
|---|---|---:|---|---|
| 1 | branching | B1, B2, B3 | rejected; corrected B1 qualification lost D3/D13 certificates and regressed D14 | Gurobi default |
| 2 | cut/formulation | C1 exact duplicate elimination | rejected; D12 failed the independent objective-residual certificate tolerance | original v0 pack |
| 3 | symmetry/numerical | S1 plus one S1-R1 revision | rejected; both lost D13's v0 certificate | v0 cardinality symmetry; no numerical change |
| 4 | model/basis reuse | none after audit | R1 not opened because no corresponding solved LP model exists | one-model rebuild; no reuse |

No candidate passed every frozen acceptance gate, so the cumulative backend contains zero accepted modifications. The final post-iteration D1--D14 v0 rerun is also the exact cumulative vNext rerun; copying its measurements under the frozen-backend label introduces no empirical substitution because the policy and executable path are identical.
"""
    (EVIDENCE / "iteration_history.md").write_text(history, encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
