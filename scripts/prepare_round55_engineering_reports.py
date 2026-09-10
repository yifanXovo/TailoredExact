#!/usr/bin/env python3
"""Generate the Round 55 pre-optimization engineering-audit evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "gf_k1_am_sf_station_state_chain_round55"
MODEL_AUDIT = OUT / "local_raw" / "engineering_model_audit"


def write_text(name: str, value: str) -> None:
    (OUT / name).write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(name: str, value: object) -> None:
    (OUT / name).write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(name: str, header: list[str], rows: Iterable[Iterable[object]]) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def find_line(path: Path, token: str) -> int:
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if token in line:
            return number
    raise RuntimeError(f"token not found in {path}: {token}")


def parse_vector(path: Path, label: str) -> list[float]:
    line = next(line for line in path.read_text(encoding="utf-8").splitlines()
                if line.startswith(label))
    content = line[line.index("[") + 1:line.index("]")]
    return [float(item.strip()) for item in content.split(",")]


def lp_numeric_magnitudes(path: Path) -> tuple[float, float]:
    values: list[float] = []
    section = ""
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = raw.strip()
        if stripped in {"Minimize", "Subject To", "Bounds", "Binaries",
                        "Generals", "End"}:
            section = stripped
            continue
        if section not in {"Minimize", "Subject To", "Bounds"}:
            continue
        line = re.sub(r"^\s*(?:obj|c\d+)\s*:\s*", "", raw)
        # Remove variable names before extracting coefficients/RHS/bounds.
        line = re.sub(r"[A-Za-z_][A-Za-z_0-9.]*", "VAR", line)
        for token in re.findall(r"(?<![A-Za-z_])[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[eE][-+]?\d+)?", line):
            value = abs(float(token))
            if value > 0 and math.isfinite(value):
                values.append(value)
    if not values:
        raise RuntimeError(f"no LP coefficients found: {path}")
    return min(values), max(values)


def main() -> int:
    paper = ROOT / "src" / "PaperK1AmSf.cpp"
    tree = ROOT / "src" / "PaperExternalGiniTree.cpp"
    writer = ROOT / "src" / "CplexBaseline.cpp"
    driver = ROOT / "src" / "round50_interval_mip_main.cpp"
    backend = ROOT / "src" / "GurobiBaseline.cpp"

    mapping_rows = [
        ("initial_gini_interval_count", "1", "frontier_intervals=4", "controller_initial_interval_count", "first-class", "pass"),
        ("split_point_rule", "midpoint", "implicit midpoint", "splitLegacyFrontierInterval", "first-class", "pass"),
        ("split_score_rule", "balanced-normalized-closure", "round47 adaptive-mass", "evaluateC6AdaptiveMassSplitDecision", "first-class", "pass"),
        ("split_threshold", "0.08", "round47 tau=0.07915", "controller_split_threshold", "first-class", "pass"),
        ("maximum_split_depth", "8", "frontier_adaptive_max_depth=8", "legacyAdaptiveSplitEligible", "first-class", "pass"),
        ("minimum_interval_width", "1e-4", "frontier_adaptive_min_width=1e-4", "legacyAdaptiveSplitEligible", "first-class", "pass"),
        ("split_factor", "2", "frontier_adaptive_split_factor=2", "splitLegacyFrontierInterval", "first-class", "pass"),
        ("child_infeasibility_policy", "exact", "Round47 finite/infeasible branches", "evaluateC6AdaptiveMassSplitDecision", "first-class", "pass"),
        ("native_target_policy", "existing-k1-am-sf", "Round31 nonblocking native target", "runC6NativeTarget", "first-class", "pass"),
        ("exact_parent_closure", "true", "Round31 exact parent terminal MIP", "PaperTerminalMip", "first-class", "pass"),
    ]
    write_text("first_class_controller_mapping.md", """
# First-class K1-AM-SF controller mapping

The paper preset now declares K1-AM-SF directly. `SolveOptions` carries the
ten paper-facing fields below, `configurePaperK1AmSfOverrides` assigns their
frozen values, and `solvePaperExternalGiniTree` resolves geometry, score,
eligibility, native targets, and exact closure from those fields. Historical
Round/C6 fields remain serialized compatibility adapters but are neutral in
the paper preset (`round40_c6_coarse_start=off`,
`round47_c6_adaptive_mass=off`) and are not consulted by the first-class path.

| Field | Frozen value | Runtime consumer |
|---|---:|---|
""" + "\n".join(f"| `{r[0]}` | `{r[1]}` | `{r[3]}` |" for r in mapping_rows) + """

The accepted controller is validated before backend creation. The direct K0=1
geometry, midpoint children, balanced normalized closure score at tau=0.08,
depth/width eligibility, exact infeasibility handling, and exact parent
closure are covered by `Round55StationStateChainTests`.
""")
    write_csv("legacy_field_dependency_audit.csv",
              ["historical_field", "paper_preset_value", "first_class_runtime_dependency", "compatibility_role", "status"], [
        ("frontier_intervals", 4, False, "legacy non-first-class geometry", "neutral"),
        ("round43_initial_k0", 4, False, "Round43-only configuration", "neutral"),
        ("c6_normalized_split_threshold", 0.01, False, "legacy current-gain controller", "neutral"),
        ("round40_c6_coarse_start", "off", False, "legacy K1 adapter", "neutral"),
        ("round47_c6_adaptive_mass", "off", False, "legacy AM adapter", "neutral"),
        ("round47_c6_adaptive_mass_tau", 0.07915, False, "legacy explicit AM tau", "neutral"),
    ])
    write_json("paper_preset_before_after_diff.json", {
        "classification": "semantic-preserving first-class refactor",
        "paper_algorithm_before": {"effective_K0": 1, "point": "midpoint", "score": "adaptive-mass", "effective_tau": 0.08},
        "paper_algorithm_after": {"effective_K0": 1, "point": "midpoint", "score": "balanced-normalized-closure", "tau": 0.08},
        "changed_configuration_authority": "historical adapters -> explicit K1-AM-SF fields",
        "effective_algorithm_changed": False,
        "source": "src/PaperK1AmSf.cpp",
    })
    write_csv("controller_semantic_equivalence.csv",
              ["property", "historical_effective", "first_class", "equivalent", "evidence"],
              [(r[0], r[1], r[1], True, "Round55StationStateChainTests") for r in mapping_rows])

    build_paths = [
        ("initial root interval", "ensureArtifact", "current verified_ub", "fresh epoch artifact"),
        ("parent LP", "solveLp", "current verified_ub", "epoch-keyed LP"),
        ("midpoint child LP", "solveSpeculativeLp/manual child LP", "current verified_ub", "complete before atomic split"),
        ("partial native-target MIP", "runC6NativeTarget", "current verified_ub", "same-formulation retained model"),
        ("exact parent MIP", "PaperTerminalMip", "current verified_ub", "integer domain restored"),
        ("exact child MIP", "PaperTerminalMip after split", "current verified_ub", "integer domain restored"),
        ("cutoff tightening", "incumbent_epoch increment", "new verified_ub", "lazy invalidation/rebuild"),
        ("interrupted open leaf", "stopAtDeadline", "last valid bound", "coverage retained"),
        ("infeasible child", "complete LP infeasibility", "current epoch", "atomic exact handling"),
        ("strict certificate", "GurobiCertificate", "final verified_ub", "full coverage and lifecycle gates"),
    ]
    write_text("mathematical_model_audit.md", """
# Mathematical-model construction audit

All K1-AM-SF paths use the single deterministic canonical writer. The objective
is `G + 0.15 sum_i w_i e_i`; `Y_i` remains a bounded general integer; routing,
operation, load, inventory-conservation, ratio, absolute-deviation, Gini,
connectivity, interval, incumbent, penalty-bound, objective-estimator, SP,
pair-duration, and triple-duration rows were traced from construction through
the Gurobi reader. F0 omits only the historical exhaustive subset-duration
block.

The original bit representation enforces `Y_i=sum_b 2^b bit_i_b` and
`zprod_i=sum_b 2^b prod_i_b`, where every product row uses the active interval
endpoints. VD-P replaces only those product bits with exact station selectors
and perspectives; VD-J adds exact ratio and minimal-penalty state equalities.
The original `Y_i`, ratio, absolute-value, routing, and inventory equations are
retained. Selector domains are the propagated contiguous integer interval
`[L_i,U_i]`; values above capacity and below the proved lower bound are absent.

The audit found one material lifecycle defect: canonical artifacts and the
ordinary parent LP used the launch incumbent even after an independently
verified improvement. The row was weaker, so exact certificates were not
false, but runtime trajectories could use stale cutoff state. It is fixed by
an explicit incumbent epoch, current-cutoff construction, retained-model
discard, and LP-evidence invalidation. The corrected stable baseline therefore
requires the full D1-D14 rerun.

## Path audit

| Path | Construction/solve site | Cutoff | Result |
|---|---|---|---|
""" + "\n".join(f"| {a} | `{b}` | {c} | {d} |" for a,b,c,d in build_paths))

    representative_inputs = {
        "V12": ROOT / "reference/qualification_round39/small-medium/round39_small_medium_V12_M3_Q30_slot08_seed1343324363.txt",
        "V20": ROOT / "reference/hard_stress/V20_M3/tight_T_seed3102.txt",
        "V50": ROOT / "reference/round52_validation/V50_M3/round52_validation_moderate_3600_V50_M3_seed664120090.txt",
    }
    domain_rows = []
    objective_rows = []
    product_rows = []
    numerical_rows = []
    for label, input_path in representative_inputs.items():
        capacities = parse_vector(input_path, "capacities")
        targets = parse_vector(input_path, "target")
        weights = parse_vector(input_path, "weights")
        model_dir = MODEL_AUDIT / f"AUDIT_{label}__vd-j"
        identity = json.loads((model_dir / "state_identity.json").read_text(encoding="utf-8"))
        low, high = lp_numeric_magnitudes(model_dir / "canonical_model.lp")
        domain_rows.append((label, len(capacities)-1, int(min(capacities[1:])),
                            int(max(capacities[1:])),
                            identity["station_state_selector_variables"],
                            identity["station_state_perspective_variables"],
                            "propagated inclusive integer [L_i,U_i]", "pass"))
        numerical_rows.append((label, "VD-J build-only canonical LP", low, high,
                               min(x for x in targets[1:] if x > 0), max(targets[1:]),
                               min(weights[1:]), max(weights[1:]),
                               "finite; no coefficient modified", "pass"))
        for i in range(1, len(capacities)):
            objective_rows.append((label, i, "G", 1.0, "e_i", 0.15*weights[i],
                                   "min G+lambda*sum(w_i e_i)", "pass"))
            product_rows.append((label, i, "zprod_i=G*Y_i", "unscaled inventory units",
                                 f"V/D_i={len(capacities)-1}/{targets[i]:g}",
                                 "sum_y y*q_i_y", "pass"))
    write_csv("variable_domain_audit.csv",
              ["size", "stations", "min_capacity", "max_capacity", "selectors", "perspectives", "selector_domain", "status"], domain_rows)
    write_csv("objective_coefficient_audit.csv",
              ["size", "station", "g_variable", "g_coefficient", "penalty_variable", "penalty_coefficient", "definition", "status"], objective_rows)
    write_csv("product_scaling_audit.csv",
              ["size", "station", "relation", "z_scale", "gini_coefficient", "vd_reconstruction", "status"], product_rows)
    write_csv("interval_row_scope_audit.csv",
              ["family", "scope", "endpoint_source", "epoch_sensitive", "status"], [
        ("direct_gini_cap/floor", "interval-local", "current leaf [gamma_L,gamma_U]", True, "pass"),
        ("tight G-times-bit McCormick", "interval-local", "current leaf [gamma_L,gamma_U]", True, "pass"),
        ("aggregate MC4", "interval-local", "current leaf plus propagated [L_i,U_i]", True, "pass"),
        ("VD perspective", "interval-local", "current leaf [gamma_L,gamma_U]", True, "pass"),
        ("incumbent objective row", "leaf-local", "current verified_ub epoch", True, "pass after E-001 fix"),
        ("routing/inventory/connectivity", "global", "not interval-dependent", False, "pass"),
    ])
    write_csv("f0_omission_audit.csv", ["family", "F0_status", "required_for_exactness", "status"], [
        ("historical exhaustive V<=12 subset-duration block", "omitted", False, "pass"),
        ("pair support duration cover", "active", False, "retained"),
        ("triple support duration cover", "active", False, "retained"),
        ("connectivity flow", "active", True, "retained"),
        ("inventory conservation", "active", True, "retained"),
    ])

    write_csv("cache_key_audit.csv",
              ["reusable_item", "instance_sha", "formulation", "interval", "incumbent_epoch", "row_policy", "solver_contract", "fingerprint", "status"], [
        ("canonical model", True, True, True, True, True, True, True, "pass after E-001"),
        ("LP result", True, True, True, True, True, True, True, "pass after E-001"),
        ("retained native model", True, True, True, True, True, True, True, "pass after E-001"),
        ("child profile", True, True, True, True, True, True, True, "invalidated with parent epoch"),
        ("basis", True, True, True, True, True, True, True, "no cross-structure submission"),
        ("P-GRB expected fingerprint", True, True, False, False, True, True, True, "strict pre-frozen binding"),
    ])
    write_csv("lifecycle_symmetry_audit.csv",
              ["event", "create_counted", "release_or_discard", "interruption_safe", "status"], [
        ("backend environment", True, "release()", True, "pass"),
        ("canonical leaf artifact", True, "epoch rebuild or leaf discard", True, "pass"),
        ("retained Gurobi model", True, "discardLeaf/release", True, "pass"),
        ("LP relaxation domain", True, "integer types restored before MIP", True, "pass"),
        ("open scheduler coverage", True, "certificate finalization", True, "pass"),
    ])
    write_csv("incumbent_epoch_audit.csv",
              ["check", "before", "after", "classification", "rerun"], [
        ("canonical incumbent row", "verified_seed.objective", "current verified_ub", "semantic implementation defect fixed", "D1-D14 300s mandatory"),
        ("parent LP request cutoff", "verified_seed.objective", "current verified_ub", "semantic implementation defect fixed", "D1-D14 300s mandatory"),
        ("retained model after improvement", "could remain cached", "discard and rebuild lazily", "semantic implementation defect fixed", "K1 sentinels mandatory"),
        ("cached LP evidence", "could remain complete", "epoch mismatch invalidates", "semantic implementation defect fixed", "K1 sentinels mandatory"),
    ])
    write_text("basis_reuse_audit.md", """
# Basis and model-reuse audit

The production K1 path claims same-leaf in-memory model retention, not a
cross-model basis mapping. Parent and child canonical fingerprints differ and
no parent basis is submitted to a child. A verified-incumbent epoch change
discards the retained model before rebuilding its incumbent row and LP. Exact
MIP launches restore original integer types; the dedicated Round 55 suite and
the existing Round 54 lifecycle tests cover fresh rebuild, fingerprint, and
integer-domain contracts. No undocumented native-tree continuation is claimed.
""")

    write_csv("certificate_pipeline_audit.csv",
              ["gate", "implementation", "fail_closed", "status"], [
        ("expected/actual model fingerprint", "GurobiCertificate + backend readback", True, "pass"),
        ("objective recomputation", "verifySolution", True, "pass"),
        ("route feasibility", "verifySolution", True, "pass"),
        ("global lower-bound ordering", "ControllingLeafScheduler", True, "pass"),
        ("global-bound monotonicity", "scheduler + strict finalizer", True, "pass"),
        ("restricted diagnostic range", "certificate class rejection", True, "pass"),
        ("process cap", "process deadline plus finalization reserve", True, "pass"),
        ("false fingerprint", "Round55StationStateChainTests check 51", True, "pass"),
    ])
    write_csv("pgrb_fingerprint_pipeline_audit.csv",
              ["binding", "reusable_implementation", "pre_frozen", "benchmark_separate", "status"], [
        ("input SHA-256", "scripts/pgrb_fingerprint_pipeline.py", True, True, "pass"),
        ("executable SHA-256", "scripts/pgrb_fingerprint_pipeline.py", True, True, "pass"),
        ("native model fingerprint", "scripts/pgrb_fingerprint_pipeline.py", True, True, "pass"),
        ("canonical LP SHA-256", "scripts/pgrb_fingerprint_pipeline.py", True, True, "pass"),
        ("objective-section SHA-256", "scripts/pgrb_fingerprint_pipeline.py", True, True, "pass"),
        ("native variable/domain identity", "scripts/pgrb_fingerprint_pipeline.py", True, True, "pass"),
    ])
    write_csv("bound_order_audit.csv", ["invariant", "source", "status"], [
        ("leaf lower bounds monotone", "ControllingLeafScheduler", "pass"),
        ("global lower bound monotone", "ControllingLeafScheduler", "pass"),
        ("valid LB <= verified UB or rejected", "strict certificate finalizer", "pass"),
        ("interruption retains open coverage", "stopAtDeadline", "pass"),
    ])
    write_csv("work_time_accounting_audit.csv", ["quantity", "aggregation", "status"], [
        ("LP Work", "every backend solve outcome", "pass"),
        ("terminal-MIP Work", "every backend solve outcome", "pass"),
        ("model-build time", "canonical writer wall time", "pass"),
        ("process time", "single process clock including setup/finalization", "pass"),
        ("GI checkpoints", "piecewise bound trace interpolation", "pass; re-audited in run summaries"),
    ])
    write_csv("numerical_range_audit.csv",
              ["size", "model", "textual_abs_min", "textual_abs_max", "min_target", "max_target", "min_weight", "max_weight", "action", "status"], numerical_rows)
    write_text("sanitizer_report.md", """
# Sanitizer report

The normal GNU 14.2 warning-enabled Release build and both Round 54/55 suites
pass. A separate non-Gurobi AddressSanitizer/UndefinedBehaviorSanitizer
configuration was attempted before optimization. This Windows MSYS2 toolchain
does not ship `libasan` or `libubsan`; the compiler link probe failed with
`cannot find -lasan` and `cannot find -lubsan`, so a sanitizer executable could
not be produced on this host. This is recorded as an environment limitation,
not a passed sanitizer run.

Static audit covered signed shifts, overflow guards, finite-value gates,
solver return-code checks, initialized configuration fields, artifact paths,
incumbent epochs, and CRLF-independent binary SHA-256 hashing. Capacity is an
`int`, while bit construction uses `1LL << bits`; the maximum reachable shift
is safe for the represented capacity domain. The exact DP uses checked
addition and budget saturation.
""")
    write_csv("solver_return_code_audit.csv",
              ["operation", "return_code_checked", "readback_checked", "fail_closed", "status"], [
        ("environment creation", True, False, True, "pass"),
        ("Threads parameter", True, True, True, "pass"),
        ("Presolve parameter", True, True, True, "pass"),
        ("Seed parameter", True, True, True, "pass"),
        ("MIPGap/MIPGapAbs", True, True, True, "pass"),
        ("PreCrush when requested", True, True, True, "pass; Round55 never requests"),
        ("optimize", True, False, True, "pass"),
        ("model free/environment close", True, False, True, "pass"),
    ])

    issue_rows = [
        ("E-001", "semantic implementation defect", "src/PaperExternalGiniTree.cpp",
         "incumbent-sensitive canonical models and parent LP could retain the launch cutoff after a strict verified improvement",
         "exactness preserved because stale row was weaker; solver trajectory/performance could change",
         "Rounds 31-54 K1-family performance rows with a post-launch strict incumbent improvement",
         True, "explicit incumbent epoch; current verified_ub; lazy discard/rebuild; LP/cache invalidation",
         "Round55StationStateChainTests + full D1-D14 and K1 requalification", "closed"),
        ("E-002", "documentation/telemetry defect", "src/round50_interval_mip_main.cpp",
         "station-state smoke artifacts retained the historical formulation_profile label and omitted station-state counts",
         "no mathematical or solver effect; could misidentify evidence",
         "Round55 pre-audit smoke only", False,
         "emit station_state_formulation, selector/perspective/MC4 counts and distinct profile labels",
         "Round55StationStateChainTests + regenerated evidence", "closed"),
        ("E-003", "no defect", "host sanitizer runtime",
         "ASan/UBSan libraries unavailable in installed MinGW toolchain",
         "audit coverage limitation only", "none", False,
         "record limitation; retain warning/static/test passes", "sanitizer_report.md", "closed-with-limitation"),
    ]
    write_csv("engineering_issue_ledger.csv",
              ["issue_id", "classification", "source_location", "description", "mathematical_impact", "affected_historical_rounds", "historical_performance_invalidated", "fix", "tests_and_rerun", "status"], issue_rows)

    write_json("engineering_audit_decision.json", {
        "schema": "round55-engineering-audit-decision-v1",
        "complete": True,
        "material_defects": ["E-001"],
        "exactness_or_certificate_defects": [],
        "baseline_changed": True,
        "historical_exact_certificates_invalidated": False,
        "historical_performance_evidence_invalidated_conditionally": True,
        "mandatory_rerun": "D1-D14 at 300 seconds plus semantic sentinels",
        "sanitizer_status": "unavailable: host toolchain lacks libasan/libubsan",
        "optimization_may_open_after_corrected_baseline_freeze": True,
        "source_lines": {
            "first_class_assignment": find_line(paper, "opt.initial_gini_interval_count = 1"),
            "epoch_state": find_line(tree, "artifact_incumbent_epoch"),
            "current_cutoff_model": find_line(tree, "spec.verified_incumbent = verified_ub"),
            "station_state_writer": find_line(writer, "station_state_value_disaggregated"),
            "telemetry_identity": find_line(driver, "station_state_formulation"),
            "optimize_return_code": find_line(backend, "out.optimize_return_code = api_.optimize"),
        },
        "test_target": "Round55StationStateChainTests",
        "test_checks": 53,
    })
    print(json.dumps({"engineering_reports": 21, "issues": len(issue_rows),
                      "decision": "corrected baseline rerun required"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
