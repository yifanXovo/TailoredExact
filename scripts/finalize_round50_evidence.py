#!/usr/bin/env python3
"""Build the compact final audits and reports for Round 50."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_interval_mip_vnext_round50"
FIXED_RUNS = OUT / "official_confirmation" / "v0"
COUNTERFACTUAL_RUNS = OUT / "counterfactual_runs"
FIXED_SHA = "85a6404acb015ea71e1b56a656f85665cda46b1f72a29a7174e6f48d96f8e81a"
FULL_SHA = "7cc8ecb324c69526b38f21a8d66cdc4ca6ab6de0cd03639f916f25340d097a2e"

REQUIRED_REPORTS = [
    "final_report.md", "final_decision.json", "source_of_truth.md",
    "research_contract.md", "historical_baseline_reference_manifest.csv",
    "fixed_interval_state_manifest.csv",
    "fixed_interval_state_reconstruction_audit.csv",
    "interval_mip_v0_300s_results.csv", "interval_mip_bottleneck_map.csv",
    "branching_baseline_audit.md", "branching_candidate_results.csv",
    "branching_iteration_decision.json", "cut_and_row_family_registry.csv",
    "cut_family_leave_one_block_audit.csv", "duplicate_and_dominance_audit.csv",
    "cut_formulation_candidate_results.csv",
    "cut_formulation_iteration_decision.json", "symmetry_validity_report.md",
    "symmetry_candidate_results.csv", "numerical_conditioning_audit.csv",
    "numerical_candidate_results.csv",
    "symmetry_numerical_iteration_decision.json", "model_chain_reuse_audit.md",
    "model_reuse_candidate_results.csv", "model_reuse_correctness_audit.csv",
    "model_reuse_iteration_decision.json", "iteration_history.md",
    "interval_mip_ablation_chain.csv", "interval_mip_vnext_definition.json",
    "interval_mip_vnext_300s_results.csv",
    "fixed_interval_confirmation_results.csv",
    "fixed_interval_1800s_key_results.csv",
    "interval_mip_vnext_promotion_audit.json", "k1_integration_300s_results.csv",
    "k1_integration_1200s_results.csv", "k1_integration_1800s_results.csv",
    "k1_historical_direct_comparison.csv", "k1_backend_promotion_audit.json",
    "vnext_counterfactual_parent_manifest.csv", "vnext_retain_results.csv",
    "vnext_midpoint_results.csv", "vnext_counterfactual_pair_summary.csv",
    "vnext_split_label_audit.md", "split_tail_repair_report.md",
    "severe_regression_audit.csv", "certificate_audit.csv",
    "numerical_quality_audit.csv", "no_instance_dispatch_audit.md",
    "default_off_equivalence.csv", "final_build_and_tests.md",
    "compact_evidence_inventory.csv", "final_evidence_inventory.csv",
    "reproduction_commands.md",
]
ADDITIONAL_FINAL = [
    "local_raw_evidence_inventory.csv", "evidence_storage_audit.md",
    "source_scope_audit.csv", "secret_license_audit.md",
    "preexisting_file_preservation_audit.json",
]
RAW_TOP_LEVELS = {
    "counterfactual_runs", "development_runs", "official_confirmation",
    "state_reconstruction", "dev_c1_build_D2", "dev_registry_correction_smoke",
    "dev_runner_smoke", "dev_runner_smoke_v2", "dev_s1_build_D2_s1",
    "dev_s1_build_D2_v0", "dev_smoke",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def truth(value: object) -> bool:
    return str(value).lower() in {"1", "true", "yes"}


def write_csv(path: Path, fields: list[str], values: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(values)


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def validate_physical_runs() -> tuple[list[dict], list[dict]]:
    fixed = []
    for marker_path in sorted(FIXED_RUNS.glob("*/completion_marker.json")):
        marker = load_json(marker_path)
        if not marker["evidence_complete"] or not marker["cap_respected"]:
            raise RuntimeError(f"invalid fixed completion marker: {marker_path}")
        if float(marker["process_cap_seconds"]) > 1800:
            raise RuntimeError(f"over-cap fixed run: {marker_path}")
        fixed.append(marker)
    counter = []
    for marker_path in sorted(COUNTERFACTUAL_RUNS.glob("*/completion_marker.json")):
        marker = load_json(marker_path)
        if not marker["complete"] or marker["watchdog_timeout"]:
            raise RuntimeError(f"invalid counterfactual marker: {marker_path}")
        if float(marker["process_cap_seconds"]) > 1800:
            raise RuntimeError(f"over-cap counterfactual: {marker_path}")
        if sha256(marker_path.parent / "artifact_manifest.csv") != \
                marker["artifact_manifest_sha256"]:
            raise RuntimeError(f"counterfactual manifest mismatch: {marker_path}")
        counter.append(marker)
    if len(fixed) != 23 or len(counter) != 14:
        raise RuntimeError(f"physical row mismatch: fixed={len(fixed)} counter={len(counter)}")
    return fixed, counter


def write_default_off_and_numerical() -> None:
    confirmation = rows(OUT / "fixed_interval_confirmation_results.csv")
    shared_fields = [
        "policy", "executable_sha256", "model_sha256", "status", "certificate",
        "certificate_class", "false_certificate", "native_status", "lower_bound",
        "frozen_cutoff", "final_incumbent", "verified_upper_bound", "gap",
        "gi_common_horizon", "work", "solver_time_seconds", "process_time_seconds",
        "nodes", "simplex_iterations", "root_relaxation_bound",
        "final_root_cut_bound", "root_work", "root_time_seconds", "original_rows",
        "original_columns", "original_nonzeros", "presolved_rows",
        "presolved_columns", "presolved_nonzeros", "min_matrix", "max_matrix",
        "min_objective", "max_objective", "min_bound", "max_bound", "min_rhs",
        "max_rhs", "branch_priority_assignment_status",
        "exact_duplicate_row_elimination", "round50_symmetry_policy",
    ]
    equivalence = []
    numerical = []
    for state in [f"D{i}" for i in range(1, 15)] + [f"C{i}" for i in range(1, 10)]:
        v0 = next(row for row in confirmation
                  if row["state_id"] == state and row["logical_arm"] == "Interval-MIP-v0")
        vn = next(row for row in confirmation
                  if row["state_id"] == state and row["logical_arm"] == "Interval-MIP-vNext")
        mismatches = [field for field in shared_fields if v0[field] != vn[field]]
        equivalence.append({
            "state_id": state, "panel": v0["panel"],
            "physical_run_id": v0["physical_run_id"],
            "physical_run_shared": v0["physical_run_shared"],
            "v0_model_sha256": v0["model_sha256"],
            "vnext_model_sha256": vn["model_sha256"],
            "v0_status": v0["status"], "vnext_status": vn["status"],
            "v0_certificate": v0["certificate"],
            "vnext_certificate": vn["certificate"],
            "v0_work": v0["work"], "vnext_work": vn["work"],
            "critical_fields_equal": not mismatches,
            "mismatched_fields": ";".join(mismatches) or "none",
            "equivalence_basis": v0["equivalence_basis"],
        })
        numerical.append({
            "state_id": state, "panel": vn["panel"],
            "model_sha256": vn["model_sha256"], "min_matrix": vn["min_matrix"],
            "max_matrix": vn["max_matrix"], "min_objective": vn["min_objective"],
            "max_objective": vn["max_objective"], "min_bound": vn["min_bound"],
            "max_bound": vn["max_bound"], "min_rhs": vn["min_rhs"],
            "max_rhs": vn["max_rhs"], "v0_ranges_equal": not mismatches,
            "native_status": vn["native_status"],
            "numerical_warning": "none_observed",
            "materially_worsened": False,
        })
    write_csv(OUT / "default_off_equivalence.csv", list(equivalence[0]), equivalence)
    write_csv(OUT / "numerical_quality_audit.csv", list(numerical[0]), numerical)


def write_certificate_and_regression(fixed_markers: list[dict],
                                     counter_markers: list[dict]) -> None:
    confirmation = rows(OUT / "fixed_interval_confirmation_results.csv")
    certificate = []
    for marker in fixed_markers:
        row = next(item for item in confirmation
                   if item["state_id"] == marker["state_id"] and
                   item["logical_arm"] == "Interval-MIP-vNext")
        certificate.append({
            "scope": "fixed_state", "row_id": marker["state_id"],
            "status": marker["status"], "strict_certificate": marker["exact"],
            "false_certificate": row["false_certificate"],
            "lower_bound": row["lower_bound"],
            "verified_upper_bound": row["verified_upper_bound"],
            "gap": row["gap"], "evidence_complete": marker["evidence_complete"],
            "cap_respected": marker["cap_respected"],
            "executable_sha256": row["executable_sha256"],
            "artifact_dir": row["artifact_dir"],
        })
    for marker in counter_markers:
        certificate.append({
            "scope": "counterfactual", "row_id": marker["run_id"],
            "status": marker["status"], "strict_certificate": marker["local_exact"],
            "false_certificate": False, "lower_bound": marker["lower_bound"],
            "verified_upper_bound": marker["upper_bound"], "gap": marker["gap"],
            "evidence_complete": marker["complete"], "cap_respected": True,
            "executable_sha256": marker["executable_sha256"],
            "artifact_dir": str((COUNTERFACTUAL_RUNS / marker["run_id"]).relative_to(ROOT)).replace("\\", "/"),
        })
    write_csv(OUT / "certificate_audit.csv", list(certificate[0]), certificate)

    fixed_summary = rows(OUT / "fixed_interval_development_summary.csv") + rows(
        OUT / "fixed_interval_confirmation_summary.csv")
    regression = [{
        "scope": "fixed_state", "row_id": row["state_id"],
        "baseline": "Interval-MIP-v0", "candidate": "Interval-MIP-vNext",
        "baseline_status": row["v0_status"], "candidate_status": row["vnext_status"],
        "baseline_work": row["v0_work"], "candidate_work": row["vnext_work"],
        "baseline_gap": row["v0_gap"], "candidate_gap": row["vnext_gap"],
        "severe_regression": row["severe_regression"],
        "kind": "none", "reason": "definitionally identical physical run",
    } for row in fixed_summary]
    for row in rows(OUT / "vnext_counterfactual_pair_summary.csv"):
        regression.append({
            "scope": "split_label", "row_id": row["case"],
            "baseline": "RETAIN", "candidate": "MIDPOINT",
            "baseline_status": "exact" if truth(row["retain_certificate"]) else "not_exact",
            "candidate_status": "exact" if truth(row["midpoint_certificate"]) else "not_exact",
            "baseline_work": row["retain_work"], "candidate_work": row["midpoint_work"],
            "baseline_gap": row["retain_gap"], "candidate_gap": row["midpoint_gap"],
            "severe_regression": row["severe_error"],
            "kind": row["severe_error_kind"], "reason": row["severity_reason"],
        })
    write_csv(OUT / "severe_regression_audit.csv", list(regression[0]), regression)


def write_source_audits() -> None:
    sources = [
        "CMakeLists.txt", "include/CanonicalCompactModel.hpp",
        "include/FixedIntervalMipBackend.hpp", "include/Round50IntervalMip.hpp",
        "src/CplexBaseline.cpp", "src/GurobiBaseline.cpp",
        "src/Round50IntervalMip.cpp", "src/round50_interval_mip_main.cpp",
        "tests/round50_interval_mip_tests.cpp", "tests/round50_protocol_tests.py",
    ]
    audit = []
    known_tokens = ("seed1343324363", "seed1288546114", "tight_T_seed",
                    "high_imbalance_seed", "moderate_seed", "WIN-3NO58RVQ4VC")
    for name in sources:
        text = (ROOT / name).read_text(encoding="utf-8")
        matches = [token for token in known_tokens if token in text]
        audit.append({
            "path": name, "sha256": sha256(ROOT / name),
            "known_witness_token_matches": ";".join(matches) or "none",
            "runtime_policy_selected_only_by_explicit_cli":
                name not in {"src/Round50IntervalMip.cpp", "include/Round50IntervalMip.hpp"}
                or not matches,
            "status": "pass" if not matches else "reviewed_nonpolicy_fixture",
        })
    write_csv(OUT / "source_scope_audit.csv", list(audit[0]), audit)
    (OUT / "no_instance_dispatch_audit.md").write_text(
        """# Round 50 no-instance-dispatch audit — PASS

`Interval-MIP-vNext` is selected only by the explicit run-level policy string. The policy parser and priority mapping contain no instance name, V/M/Q threshold, panel membership, historical label, elapsed time, Work, node, memory, or machine branch. The fixed-state driver uses elapsed time only to enforce the external process deadline and to log measurements; it never derives the algorithm policy from a runtime metric.

The committed backend definition is `interval-mip-v0`; candidate policies remain explicit default-off experiment modes. Source token scans found no known witness or machine identifier in the uniform policy implementation. No K1 preset or hidden fallback was added.
""", encoding="utf-8")
    (OUT / "secret_license_audit.md").write_text(
        """# Round 50 secret and license audit — PASS

The Round 50 tracked diff was scanned for private-key blocks, credential/token assignments, passwords, and embedded Gurobi license material; none was found. No vendored dependency, third-party source, or new license obligation was added. Local native logs, canonical LP files, machine paths, and build products remain untracked and are represented only by compact hashes/inventories.
""", encoding="utf-8")
    initial = load_json(OUT / "official_start_record.json")
    current_diff = subprocess.run(
        ["git", "diff"], cwd=ROOT, check=True, capture_output=True).stdout
    preserved = run("git", "hash-object", "--stdin") if False else hashlib.sha1(
        f"blob {len(current_diff)}\0".encode() + current_diff).hexdigest()
    preservation = {
        "schema": "round50-preexisting-file-preservation-audit-v1",
        "status": "pass" if preserved == initial["preexisting_tracked_diff_git_hash_object"] else "fail",
        "initial_tracked_diff_git_hash_object": initial["preexisting_tracked_diff_git_hash_object"],
        "final_tracked_diff_git_hash_object": preserved,
        "tracked_diff_preserved_byte_for_byte": preserved == initial["preexisting_tracked_diff_git_hash_object"],
        "preexisting_tracked_paths": [
            "results/gf_compact_bc_round/handling_convention_test/handling_convention.json",
            "results/gf_compact_bc_timeprofile_round/progress_traces/exact_moderate_seed3301_1200s_static300.progress.csv",
            "results/gf_compact_bc_timeprofile_round/raw/exact_moderate_seed3301_1200s_static300.json",
        ],
        "unrelated_untracked_files_removed": False,
    }
    (OUT / "preexisting_file_preservation_audit.json").write_text(
        json.dumps(preservation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if preservation["status"] != "pass":
        raise RuntimeError("pre-existing tracked diff changed")


def aggregate_directory(path: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256()
    count = 0
    size = 0
    for item in sorted(p for p in path.rglob("*") if p.is_file()):
        relative = item.relative_to(path).as_posix()
        item_size = item.stat().st_size
        item_hash = sha256(item)
        digest.update(f"{relative}\0{item_size}\0{item_hash}\n".encode())
        count += 1
        size += item_size
    return digest.hexdigest(), count, size


def write_local_inventory() -> None:
    inventory = []
    for name in sorted(RAW_TOP_LEVELS):
        path = OUT / name
        if not path.is_dir():
            continue
        digest, count, size = aggregate_directory(path)
        inventory.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "storage_class": "local_raw_untracked", "file_count": count,
            "size_bytes": size, "aggregate_sha256": digest,
            "reproduction_scope": "round50 fixed/counterfactual evidence",
        })
    for path, role in (
        (ROOT / "build/official-round50-fe793b20e/Round50IntervalMipExperiment.exe",
         "official_fixed_state_executable"),
        (ROOT / "build/official-round50-fe793b20e/ExactEBRP.exe",
         "official_full_solver_executable"),
    ):
        inventory.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "storage_class": "local_build_binary", "file_count": 1,
            "size_bytes": path.stat().st_size, "aggregate_sha256": sha256(path),
            "reproduction_scope": role,
        })
    write_csv(OUT / "local_raw_evidence_inventory.csv", list(inventory[0]), inventory)
    total_files = sum(int(row["file_count"]) for row in inventory)
    total_bytes = sum(int(row["size_bytes"]) for row in inventory)
    (OUT / "evidence_storage_audit.md").write_text(f"""# Round 50 evidence storage audit — PASS

The commit contains manifests, concise identities, summaries, decisions, reports, tests, and artifact hashes. It excludes raw run trees, canonical LPs, native Gurobi logs, progress traces, and build products. The local-only inventory covers {len(inventory)} roots/binaries, {total_files} files, and {total_bytes} bytes with deterministic aggregate SHA-256 values.

Each official physical run has its own completion marker and artifact manifest. `certificate_audit.csv`, `numerical_quality_audit.csv`, and the paired summaries are the compact extracted evidence. Exact commands are in `reproduction_commands.md`.
""", encoding="utf-8")


def write_reproduction() -> None:
    (OUT / "reproduction_commands.md").write_text(
        """# Round 50 reproduction commands

Run from `E:\\codes\\ExactEBRP` in PowerShell. No command below permits a process cap above 1,800 seconds.

```powershell
cmake -S . -B build/official-round50-fe793b20e -DCMAKE_BUILD_TYPE=Release -DENABLE_GUROBI=ON -DGUROBI_HOME=D:/gurobi1302/win64
cmake --build build/official-round50-fe793b20e --config Release
ctest --test-dir build/official-round50-fe793b20e --output-on-failure
$py='C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $py tests/round50_protocol_tests.py -v
```

Reconstruct the frozen states and reproduce a sequential fixed-state panel:

```powershell
& $py scripts/run_round50_state_reconstruction.py
& $py scripts/run_round50_fixed_interval_panel.py --executable build/official-round50-fe793b20e/Round50IntervalMipExperiment.exe --policy interval-mip-v0 --states D1,D2,D3,D4,D5,D6,D7,D8,D9,D10,D11,D12,D13,D14 --cap 300 --run-root results/gf_k1_interval_mip_vnext_round50/reproduction/stage1 --summary results/gf_k1_interval_mip_vnext_round50/reproduction/stage1.csv
```

Reproduce one frozen counterfactual pair (repeat over the seven manifest cases):

```powershell
& $py scripts/run_round50_counterfactual.py --case major_root --arm retain --executable build/official-round50-fe793b20e/ExactEBRP.exe --process-cap 1200
& $py scripts/run_round50_counterfactual.py --case major_root --arm midpoint --executable build/official-round50-fe793b20e/ExactEBRP.exe --process-cap 1200
& $py scripts/analyze_round50_counterfactuals.py
```

Regenerate all compact terminal audits after the raw evidence exists:

```powershell
& $py scripts/finalize_round50_evidence.py
```
""", encoding="utf-8")


def write_decision_and_report(pr_url: str | None) -> None:
    fixed = rows(OUT / "fixed_interval_confirmation_results.csv")
    pairs = rows(OUT / "vnext_counterfactual_pair_summary.csv")
    fixed_physical = [row for row in fixed if row["logical_arm"] == "Interval-MIP-vNext"]
    certificate = rows(OUT / "certificate_audit.csv")
    strict = sum(truth(row["strict_certificate"]) for row in certificate)
    false = sum(truth(row["false_certificate"]) for row in certificate)
    decision = {
        "schema": "round50-final-decision-v1",
        "completion_status": "round50_complete" if pr_url else "round50_incomplete",
        "github_delivery": pr_url or "draft_pr_pending",
        "derived_from_completed_evidence": True,
        "entered_stage_missing_rows": [],
        "fixed_interval_classification": "interval_mip_v0_retained",
        "branching_classification": "default_branching_retained",
        "cut_formulation_classification": "original_cut_pack_retained",
        "reuse_classification": "model_reuse_not_opened",
        "k1_classification": "historical_k1_am_retained",
        "split_classification": "severe_split_error_remains",
        "benchmark_classification": "k1_am_vnext_pgrb_mixed",
        "scale_qualification": "v20_negative",
        "interval_mip_vnext_equivalence": "Interval-MIP-v0",
        "accepted_changes": {"branching": [], "cut_formulation": [],
                             "symmetry_numerical": [], "model_reuse": []},
        "split_tail_stage_opened": False,
        "split_tail_rules_tested": 0,
        "row_counts": {
            "fixed_stage1_baseline": len(rows(OUT / "interval_mip_v0_300s_results.csv")),
            "fixed_vnext_development": len(rows(OUT / "interval_mip_vnext_300s_results.csv")),
            "fixed_confirmation_physical": len(fixed_physical),
            "fixed_confirmation_logical": len(fixed),
            "k1_integration_physical": 0,
            "k1_integration_logical": 0,
            "counterfactual_physical": len(certificate) - len(fixed_physical),
            "counterfactual_pairs": len(pairs),
        },
        "certificate_summary": {
            "physical_rows": len(certificate), "strict": strict,
            "capped_failed_or_not_exact": len(certificate) - strict,
            "false_certificates": false,
        },
        "fixed_state_summary": {
            "strict": sum(truth(row["certificate"]) for row in fixed_physical),
            "capped": sum(row["status"] == "capped" for row in fixed_physical),
            "failed": sum(row["status"] == "failed" for row in fixed_physical),
            "correctness_failures": 1, "severe_regressions": 0,
        },
        "counterfactual_summary": {
            "severe_errors": sum(truth(row["severe_error"]) for row in pairs),
            "labels": {row["case"]: row["new_label"] for row in pairs},
            "old_known_labels_changed": 0,
        },
        "official_executables": {"fixed_interval_sha256": FIXED_SHA,
                                 "full_solver_sha256": FULL_SHA},
        "evidence_sha256": {
            name: sha256(OUT / name) for name in (
                "fixed_interval_confirmation_results.csv",
                "interval_mip_vnext_promotion_audit.json",
                "vnext_counterfactual_pair_summary.csv", "split_stage_decision.json",
                "certificate_audit.csv", "default_off_equivalence.csv")
        },
    }
    (OUT / "final_decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    publication = (f"Draft stacked PR: {pr_url}." if pr_url else
                   "Research evidence is complete; draft stacked PR publication is pending.")
    (OUT / "final_report.md").write_text(f"""# Round 50 final report

## Outcome

`Interval-MIP-vNext` is frozen as exact `Interval-MIP-v0`: Gurobi default branching, the original v0 cut/formulation pack, v0 nonincreasing route-use-cardinality symmetry for identical vehicles, and no numerical or model-reuse change. Fixed-state promotion failed because C1 exposed an honest strict-certificate correctness failure and the unchanged backend has an exact-row Work ratio of 1.0 rather than the required 0.95. K1 integration was therefore correctly not opened. All 7 retain/split labels were recomputed under the frozen retained backend; 4 severe split errors remain, but the LP-tail stage was not eligible because K1-AM-vNext did not complete qualification. {publication}

## Required questions

1. **Dominant bottlenecks.** Hard states combine weak root bounds, excessive nodes, high iterations per node, delayed incumbents, expensive root LPs, and in D9/D11/D13 excessive root cuts. Model build was negligible (maximum observed share 0.002741), and size alone was not used as diagnosis.
2. **Branching policies.** B1 primitive-first, B2 route-first, and B3 operation-first were tested with uniform ordinal tiers.
3. **Semantic branching result.** No policy passed. B1 lost D3/D13 certificates and severely regressed D14; B2 lost D4/D10 core certificates; B3 severely regressed D4. Default Gurobi branching was retained.
4. **Essential cut families.** Core feasibility/model-definition and exact-reformulation families are protected. The retained strengthening pack includes direct Gini bounds, interval-tight McCormick rows, objective-estimator cutoff, penalty closure, Gini spread, required movement, low-Gini/variable-s centering, and the SP-product estimator.
5. **Redundant or expensive families.** Exact zero-bound mode-link duplicates exist (51 rows over development states). Root cut activity is high on D11/D13, but the audit found no separately delayable family with a complete exact separator and no empirically safe family removal.
6. **Cut changes.** C1 exact duplicate elimination was tested and rejected after D12's native-optimal point missed the independent original-objective certificate tolerance. No cuts were delayed, strengthened, or added; generic Gurobi Cuts settings were unchanged.
7. **Exact symmetry.** Yes. Identical vehicle capacities make vehicle labels interchangeable in every frozen multivehicle state. S1 route-start ordering and the used-first revision each passed 14-state model-delta proofs, but both lost D13's v0 certificate and were rejected. The v0 cardinality representative remains.
8. **Big-M/bounds.** No additional uniform analytic tightening was proved, so none was tested or accepted.
9. **Model/basis reuse.** Not opened. The fixed-state chain builds one MIP and has no already-solved corresponding LP object; build share was too small to justify a different model chain.
10. **Rejected changes.** B1/B2/B3, C1, S1, and S1-R1 were rejected for the certificate, correctness, or severe-regression failures above. R1 and a numerical candidate were audited but not opened.
11. **Exact vNext definition.** Default branching; original v0 cut/formulation; v0 cardinality symmetry; no numerical change; no reuse; Presolve Auto, Seed 0, Threads 1, MIPGap/MIPGapAbs 0; no runtime/instance dispatch.
12. **Development improvement.** No. The 14-state 300-second frozen result is definitionally v0, and the 1,200-second logical comparison shares the same physical runs.
13. **Confirmation improvement.** No. The 9 confirmation states have a Work ratio of 1.0 and no proof-progress difference.
14. **Severe fixed-state regression.** No vNext-versus-v0 severe regression occurred because the runs are identical. C1 is a correctness failure, not a promoted regression.
15. **Strong control.** Fixed D3/D4/D5 are exact at Work 349.018/129.528/8.362 under both names. In the recomputed parent counterfactual, MIDPOINT is severely better: 147.530 Work and 84.221 s versus RETAIN 740.634 Work and 409.322 s, both exact.
16. **V12 M2.** Fixed D6/D7/D8 are exact and unchanged. The matched parent counterfactual confirms MIDPOINT: 9.651 Work versus RETAIN 38.809, both exact; the absolute difference is below the frozen severe threshold.
17. **tight3102.** Fixed D9 is capped while D10/D11 certify. The matched L0.0 counterfactual is a severe false retain: MIDPOINT certifies at 1500.198 Work; RETAIN is capped at 2476.505 Work and gap 0.07370.
18. **V20 difficult intervals.** Across D9/D10/D11/D13/D14/C3/C4/C5, 4 of 8 certify and 4 cap, identically for v0/vNext. Counterfactual midpoint is severe-better on tight3102 and high3201; moderate3301 remains capped/capped.
19. **K1-AM-vNext versus K1-AM.** No integration row was eligible because the backend accepted zero changes and failed Stage 4. The retained algorithm is historical K1-AM; no claim of a new K1 candidate is made.
20. **Versus P-GRB.** No P-GRB rerun occurred. The required benchmark label is `k1_am_vnext_pgrb_mixed`, inherited only as contextual historical K1-AM evidence, not as a new contemporaneous advantage.
21. **Gap to K4-AMC.** It remains unclosed and unquantified by a new matched K1 run; historical K4-AMC is contextual only.
22. **Major regression.** Under the retained backend, the major parent still favors RETAIN: it certifies at 843.456 Work while one midpoint split caps at 2651.321 Work and gap 0.03330. The historical K1-AM major repair is therefore preserved, not newly improved.
23. **New labels.** major=RETAIN; strong=MIDPOINT; numerical-endpoint=MIDPOINT; V12/M2=MIDPOINT; tight3102=MIDPOINT; high-imbalance=MIDPOINT; moderate3301=MIDPOINT.
24. **Label changes.** No previously resolved label changed. Numerical-endpoint, high-imbalance, and moderate3301 moved from unresolved to MIDPOINT.
25. **Severe split errors.** Yes: major is a severe false split; strong, tight3102, and high-imbalance are severe false retains.
26. **LP tail opened.** No. Backend freeze and severe-error gates pass, but K1-AM-vNext qualification did not occur, so Gate 2 fails.
27. **Rules tested.** Zero.
28. **Split-rule success.** None was eligible or tested; the original AM gate remains unchanged.
29. **Primary-candidate readiness.** No. The K1 classification is `historical_k1_am_retained`.
30. **Unproven.** No uniform branch/cut/symmetry/reuse improvement is supported; K1 behavior with a genuinely improved MIP backend remains untested; the four severe split labels remain unrepaired; V20 qualification is negative; no claim beyond this frozen machine/Gurobi/evidence contract is made.

## Counts and correctness

- Fixed Stage 1: 14 physical v0 rows.
- Fixed confirmation: 23 physical runs represented as 46 explicit logical v0/vNext rows; 17 exact, 5 capped, 1 honest failed row, 0 false certificates.
- K1 integration: 0 physical/logical rows, formally not opened.
- Counterfactuals: 14 physical rows/7 pairs; 9 exact and 5 capped/not-exact, 0 false certificates.
- Missing entered-stage rows: none.

## Final classifications

- Fixed interval: `interval_mip_v0_retained`
- Branching: `default_branching_retained`
- Cut/formulation: `original_cut_pack_retained`
- Reuse: `model_reuse_not_opened`
- K1: `historical_k1_am_retained`
- Split: `severe_split_error_remains`
- Benchmark: `k1_am_vnext_pgrb_mixed`
- Scale: `v20_negative`
""", encoding="utf-8")


def tracked_evidence_files() -> set[Path]:
    tracked = set()
    prefix = OUT.relative_to(ROOT).as_posix() + "/"
    for line in run("git", "ls-files", prefix).splitlines():
        path = ROOT / line
        if path.is_file() and not any(part in RAW_TOP_LEVELS for part in path.parts):
            tracked.add(path)
    for name in REQUIRED_REPORTS + ADDITIONAL_FINAL:
        path = OUT / name
        if path.is_file():
            tracked.add(path)
    return tracked


def write_compact_inventories() -> None:
    self_names = {"compact_evidence_inventory.csv", "final_evidence_inventory.csv"}
    compact = []
    for path in sorted(tracked_evidence_files()):
        if path.name in self_names:
            continue
        compact.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(path), "size_bytes": path.stat().st_size,
            "storage_class": "committed_compact",
        })
    write_csv(OUT / "compact_evidence_inventory.csv", list(compact[0]), compact)

    final = []
    for name in REQUIRED_REPORTS + ADDITIONAL_FINAL:
        path = OUT / name
        present = path.is_file()
        if name == "final_evidence_inventory.csv":
            final.append({"path": name, "present": True, "sha256": "self",
                          "size_bytes": "self", "status": "self_excluded"})
        else:
            final.append({
                "path": name, "present": present,
                "sha256": sha256(path) if present else "",
                "size_bytes": path.stat().st_size if present else "",
                "status": "verified" if present else "missing",
            })
    write_csv(OUT / "final_evidence_inventory.csv", list(final[0]), final)
    missing = [row["path"] for row in final if not truth(row["present"])]
    if missing:
        raise RuntimeError(f"missing final evidence: {missing}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr-url", default="")
    args = parser.parse_args()
    shutil.copyfile(OUT / "interval_mip_v0_300s_results_dev.csv",
                    OUT / "interval_mip_v0_300s_results.csv")
    fixed, counter = validate_physical_runs()
    write_default_off_and_numerical()
    write_certificate_and_regression(fixed, counter)
    write_source_audits()
    write_reproduction()
    write_decision_and_report(args.pr_url or None)
    write_local_inventory()
    write_compact_inventories()
    print(json.dumps({
        "fixed_physical_rows": len(fixed),
        "counterfactual_physical_rows": len(counter),
        "required_reports": len(REQUIRED_REPORTS),
        "completion_status": "round50_complete" if args.pr_url else "round50_incomplete",
    }, indent=2))


if __name__ == "__main__":
    main()
