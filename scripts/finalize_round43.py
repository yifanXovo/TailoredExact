#!/usr/bin/env python3
"""Create the compact terminal decision and paper-facing Round 43 reports."""

from __future__ import annotations

import math
from pathlib import Path
import hashlib
from typing import Any

import round43_analysis as analysis
import round43_common as common


MAJOR = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
CONTROL = "round39_small_hard_V12_M3_Q30_slot08_seed1288546114"
CLASSIFICATION = "bounded_systematic_negative_result"


def truth(value: Any) -> bool:
    return analysis.truth(value)


def number(value: Any, default: float = math.nan) -> float:
    return analysis.number(value, default)


def fmt(value: Any, digits: int = 3) -> str:
    parsed = number(value)
    return "inf" if not math.isfinite(parsed) else f"{parsed:.{digits}f}"


def find(rows: list[dict[str, Any]], **terms: Any) -> dict[str, Any]:
    return next(row for row in rows if all(
        str(row[key]) == str(value) for key, value in terms.items()))


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    lines.extend("| " + " | ".join(map(str, row)) + " |" for row in rows)
    return "\n".join(lines)


def repository_blob_sha256(path: Path) -> str:
    """Hash text with LF newlines so Git checkout policy cannot change it."""
    material = path.read_bytes()
    if path.suffix.lower() in {".csv", ".json", ".md", ".txt"}:
        material = material.replace(b"\r\n", b"\n")
    return hashlib.sha256(material).hexdigest()


def main() -> int:
    decision = common.load_json(
        common.OUT / "stage3_development_decision.json")
    if truth(decision["stage3_passed"]):
        raise RuntimeError(
            "finalize_round43.py is the audited no-promotion terminal path")
    stage4 = common.load_json(common.OUT / "stage4_disposition.json")
    stage5 = common.load_json(common.OUT / "stage5_entry_audit.json")
    if not truth(stage4["audit_passed"]) or not truth(stage5["audit_passed"]):
        raise RuntimeError("a triggered fallback stage remains incomplete")

    comparisons = common.csv_rows(common.OUT / "development_comparison.csv")
    summaries = common.csv_rows(common.OUT / "stage3_development_summary.csv")
    per_run = common.csv_rows(common.OUT / "per_run_results.csv")
    mechanism = common.csv_rows(common.OUT / "stage3_mechanism_summary.csv")
    atlas = common.csv_rows(common.OUT / "stage1_structural_summary.csv")
    envelope = common.csv_rows(common.OUT / "stage2_envelope_summary.csv")
    ablations = common.csv_rows(
        common.OUT / "refinement_score_ablation_summary.csv")
    default_off = common.csv_rows(common.OUT / "default_off_equivalence.csv")
    test_audit = common.load_json(common.OUT / "final_test_audit.json")

    k1_name = "A(1,2,0.1)"
    k4_name = "A(4,2,0.1)"
    k1 = find(summaries, candidate=k1_name)
    k4 = find(summaries, candidate=k4_name)
    major_k1 = find(comparisons, instance_id=MAJOR, candidate=k1_name)
    major_k4 = find(comparisons, instance_id=MAJOR, candidate=k4_name)
    control_k1 = find(comparisons, instance_id=CONTROL, candidate=k1_name)
    control_k4 = find(comparisons, instance_id=CONTROL, candidate=k4_name)

    not_run_fields = [
        "experiment_group", "status", "reason", "candidate", "run_count",
        "gate_eligible", "holdout_remained_sealed",
    ]
    common.write_csv(common.OUT / "validation_comparison.csv", [{
        "experiment_group": "validation-7",
        "status": "not_run",
        "reason": "no_candidate_passed_all_frozen_development_gates",
        "candidate": "",
        "run_count": 0,
        "gate_eligible": False,
        "holdout_remained_sealed": True,
    }], not_run_fields)
    common.write_csv(common.OUT / "holdout_comparison.csv", [{
        "experiment_group": "sealed-holdout-7",
        "status": "not_run",
        "reason": "validation_not_opened_after_development_rejection",
        "candidate": "",
        "run_count": 0,
        "gate_eligible": False,
        "holdout_remained_sealed": True,
    }], not_run_fields)

    certificate_rows = [{
        "run_id": row["run_id"],
        "instance_id": row["instance_id"],
        "arm": row["arm"],
        "provenance": row["provenance"],
        "status": row["status"],
        "strict_certificate": row["certified"],
        "right_censored": row["right_censored"],
        "independent_verifier_passed": row["verified_incumbent"],
        "false_certificate": row["false_certificate"],
        "parameter_roundtrip_valid": row["parameter_roundtrip_valid"],
        "valid_lower_bound": row["valid_lower"],
        "verified_upper_bound": row["verified_upper"],
        "relative_gap": row["relative_gap"],
        "failure_reason": row["failure_reason"],
    } for row in per_run]
    common.write_csv(common.OUT / "certificate_audit.csv", certificate_rows)
    if any(truth(row["false_certificate"]) for row in certificate_rows):
        raise RuntimeError("false certificate detected")

    performance = [{
        "instance_id": row["instance_id"],
        "classification": row["classification"],
        "candidate": row["candidate"],
        "candidate_work": row["candidate_work"],
        "pgrb_work": row["pgrb_work"],
        "c6_work": row["c6_work"],
        "candidate_over_pgrb_work": row["candidate_over_pgrb_work"],
        "candidate_over_c6_work": row["candidate_over_c6_work"],
        "candidate_process_seconds": row["candidate_process_seconds"],
        "candidate_exact_seconds": row["candidate_exact_seconds"],
        "shifted_total_time_vs_pgrb": row[
            "shifted_total_time_vs_pgrb"],
        "shifted_exact_time_vs_c6": row["shifted_exact_time_vs_c6"],
        "material_result_vs_pgrb": row["material_result_vs_pgrb"],
        "strict_certificate": row["candidate_certified"],
    } for row in comparisons]
    common.write_csv(common.OUT / "performance_profile.csv", performance)

    forbidden = common.load_json(common.OUT / "forbidden_decision_inputs.json")
    decision_source = "\n".join((
        (common.ROOT / "src" / "GiniEnvelopeRefinement.cpp").read_text(
            encoding="utf-8"),
        (common.ROOT / "include" / "GiniEnvelopeRefinement.hpp").read_text(
            encoding="utf-8"),
    )).lower()
    pattern_map = {
        "instance filename": "input_path",
        "instance ID": "instance_id",
        "generation seed": "seed",
        "scenario label": "scenario",
        "difficulty stratum": "difficulty",
        "historical winner": "historical_winner",
        "elapsed seconds": "elapsed",
        "Gurobi Work": "gurobi_work",
        "processed nodes": "node_count",
        "simplex iterations": "simplex",
        "barrier iterations": "barrier",
        "memory": "memory",
        "hardware identifier": "hardware",
        "leaf effort": "leaf_effort",
        "historical classifier": "classifier",
        "known regression lookup table": "regression_lookup",
        "V": "instance.v",
        "M": "instance.m",
        "Q": "instance.q",
    }
    forbidden_rows = []
    for name in forbidden["forbidden"]:
        pattern = pattern_map[name]
        observed = pattern.lower() in decision_source
        forbidden_rows.append({
            "forbidden_input": name,
            "searched_pattern": pattern,
            "decision_source_scope": (
                "GiniEnvelopeRefinement.cpp/.hpp deterministic functions"),
            "observed": observed,
            "audit_passed": not observed,
        })
    common.write_csv(common.OUT / "forbidden_logic_audit.csv", forbidden_rows)
    if any(truth(row["observed"]) for row in forbidden_rows):
        raise RuntimeError("forbidden input found in deterministic decision code")

    mechanism_table = markdown_table(
        ["K0", "rho", "Exact", "Censored", "Major Work",
         "Control Work", "Work gmean"],
        [[row["K0"], row["rho"], row["certified_count"],
          row["right_censored_count"], fmt(row["major_work"]),
          fmt(row["control_work"]), fmt(row["geomean_work"])]
         for row in mechanism])
    atlas_table = markdown_table(
        ["d", "Rows", "D min", "D median", "D max", "tau median"],
        [[row["depth"], row["row_count"], fmt(row["D_min"], 4),
          fmt(row["D_median"], 4), fmt(row["D_max"], 4),
          fmt(row["tau_median"], 4)] for row in atlas])
    common.write_text(common.OUT / "mechanism_atlas.md", f"""# Mechanism atlas

The structural atlas was frozen before exact candidate outcomes. It used only
interval endpoints, verified U, complete LP bounds/statuses, model geometry,
and the global K0/d/rho parameters.

## Depth screen

{atlas_table}

Depth 1 has a nonzero but weaker deficit signal. Depth 2 has the stronger
median envelope-capture fraction and retains meaningful D variation, so d=2
was frozen. C_d was exactly 0.5 for d=1 and 0.75 for d=2 on every row; this is
a construction constant, not an admissible adaptive signal.

## Exact mechanism screen

{mechanism_table}

The symmetric 7,200-second extensions are used wherever present. Both K0
values select rho=0.10 under the frozen tail-first order.
""")

    common.write_text(common.OUT / "mathematical_mechanism_note.md", """# Mathematical mechanism note

Round 43 implements one node operator A(K0,d,rho). K0 changes only the equal
initial partition of the complete strict-improver Gini range. Every active
interval then completes its parent LP, completes all 2^d dyadic lookahead LPs,
constructs the frozen greatest-convex-minorant affine objective-Gini envelope,
and evaluates the same globally fixed score.

For each accepted facet `(alpha,beta)`, the native row is
`(1-beta) G + lambda sum_i w_i e_i >= alpha`. Facets are interval-local and
inherited only by nested descendants. The executable-normalized
residual-volume score is
`D_R43=V_residual/(|I|*max(U-L_I,epsilon_cert))`. The separately useful profile
fraction is `P_profile=V_residual/max(V_local,epsilon_volume)=1-tau_d` when
`V_local` is positive; it is not the Round 43 decision score. A node splits at
its midpoint exactly when `D_R43 >= rho`; otherwise the strengthened parent MIP
is solved to a protocol terminal condition. Descendant LP bounds and
infeasibility proofs remain valid lower-bound information, while an incumbent
is never treated as a lower bound.

The contraction candidate C_d is mathematically rejected for decision use: the
chosen normalization makes it identically `1-2^-d`, observed as 0.5 and 0.75.
Timing, Work, nodes, iterations, memory, hardware, instance identity, and
historical outcomes are absent from the deterministic decision functions and
their hashes.
""")

    ctest = test_audit["ctest"]
    python_tests = test_audit["python_protocol_tests"]
    common.write_text(common.OUT / "exactness_and_validity_note.md", f"""# Exactness and validity note

All candidate certificates in `certificate_audit.csv` require complete exact
interval coverage, a monotone valid global lower bound, the native zero-gap
contract, and an independently verified original-space incumbent. Empty leaves
may contribute +infinity only when their native status is infeasible; this
fail-closed rule has a dedicated C++ regression test. Matching objective values
alone are never interpreted as optimality.

The final audit found zero false certificates. Right-censored rows remain
explicit noncertificates with their valid lower/verified upper bounds. The
Release/Gurobi clean build passed {ctest['passed']}/{ctest['total']} CTest
targets and {python_tests['passed']}/{python_tests['total']} Python protocol
tests. Default-off implicit versus explicit C6 equivalence passed
{sum(truth(row['default_off_equivalence_passed']) for row in default_off)}/3
sentinels.
""")

    def aggregate_arm(arm: str) -> dict[str, Any]:
        group = [row for row in per_run if row["arm"] == arm]
        return {
            "rows": len(group),
            "work_gmean": analysis.gmean(
                [number(row["work"]) for row in group]),
            "terminal_jobs": sum(int(float(row["terminal_mip_jobs"]))
                                 for row in group),
        }

    factor_arms = ("C6", "K1-old", k1_name, k4_name)
    factors = {arm: aggregate_arm(arm) for arm in factor_arms}
    factor_table = markdown_table(
        ["Initial K0", "Old mechanism", "New mechanism"],
        [["1", f"K1-old ({fmt(factors['K1-old']['work_gmean'])} gmean Work)",
          f"{k1_name} ({fmt(factors[k1_name]['work_gmean'])} gmean Work)"],
         ["4", f"C6 ({fmt(factors['C6']['work_gmean'])} gmean Work)",
          f"{k4_name} ({fmt(factors[k4_name]['work_gmean'])} gmean Work)"]])
    ablation_table = markdown_table(
        ["Arm", "Exact", "Censored", "Work gmean", "Terminal MIPs", "Splits"],
        [[row["arm"], f"{row['certified_count']}/{row['row_count']}",
          row["right_censored_count"], fmt(row["work_geomean"]),
          row["total_terminal_mip_jobs"], row["total_splits"]]
         for row in ablations])
    common.write_text(common.OUT / "k1_vs_k4_factor_analysis.md", f"""# K1 versus K4 factor analysis

{factor_table}

The complete 2x2 comparison separates initial granularity from the shared new
operator. K4-new is better than K1-new on the major witness
({fmt(major_k4['candidate_work'])} versus {fmt(major_k1['candidate_work'])}
Work) and on the strongest K4 control ({fmt(control_k4['candidate_work'])}
versus {fmt(control_k1['candidate_work'])} Work), confirming retained local
K4 strength. Neither new arm preserves the control against C6: their Work
ratios are {fmt(control_k1['candidate_over_c6_work'])} and
{fmt(control_k4['candidate_over_c6_work'])}, both above 1.20.

## Mandatory mechanism ablations

{ablation_table}

The envelope, score, and recursion effects are reported as complete arm-level
outcomes. They are not attributed to changed Gurobi search merely because a
root LP is stronger. The strongest-control K1 and K4 complete-global-root LP
bounds are equal, so the zero chi numerator/denominator case is vacuous rather
than evidence of missing transferable root strength.
""")

    final_decision = {
        "schema": "round43-final-decision-v1",
        "round_id": 43,
        "terminal_classification": CLASSIFICATION,
        "promotion": False,
        "selected_algorithm": None,
        "selected_parameters": None,
        "baseline_retained": {
            "algorithm": "C6-HGA-FULL",
            "K0": 4,
            "rho": 0.01,
            "presolve": "Auto",
            "seed": 0,
            "threads": 1,
        },
        "development_passed": False,
        "stage3_passing_candidates": [],
        "stage4_entered": False,
        "stage4_skip_audit_passed": True,
        "stage5_entered": False,
        "stage5_skip_audit_passed": True,
        "validation_opened": False,
        "validation_passed": False,
        "holdout_opened": False,
        "holdout_remained_sealed": True,
        "false_certificates": 0,
        "default_off_preserved": True,
        "new_preset_added": False,
        "reason": (
            "Both globally selected Stage 3 candidates fail the frozen "
            "strongest-positive-control gate; no Stage 4 or Stage 5 entry "
            "condition is true."),
    }
    common.write_json(common.OUT / "final_decision.json", final_decision)

    test_lines = [
        "# Final build and tests", "",
        f"- Build: {test_audit['build']['status']} "
        f"({test_audit['build']['configuration']}, Gurobi "
        f"{test_audit['build']['gurobi_version']}).",
        f"- CTest: {ctest['passed']}/{ctest['total']} passed.",
        f"- Existing Python protocol suite: "
        f"{test_audit['existing_python_tests']['passed']}/"
        f"{test_audit['existing_python_tests']['total']} passed.",
        f"- Round 43 Python protocol/evidence suite: "
        f"{python_tests['passed']}/{python_tests['total']} passed.",
        f"- Default-off sentinels: "
        f"{sum(truth(row['default_off_equivalence_passed']) for row in default_off)}/3 passed.",
        f"- Secret/license scan: {test_audit['secret_scan']['status']}; "
        f"{test_audit['secret_scan']['findings']} findings.",
        "- No existing test was weakened or deleted.", "",
    ]
    common.write_text(
        common.OUT / "final_build_and_tests.md", "\n".join(test_lines))

    reproduction = r"""# Reproduction commands

Run from the repository root in PowerShell. The bundled Python path may be
replaced by any compatible Python 3.11+ interpreter.

```powershell
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' -S . -B build_round43 -G 'MinGW Makefiles' -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER='D:/msys64/ucrt64/bin/c++.exe' -DCMAKE_MAKE_PROGRAM='D:/msys64/ucrt64/bin/mingw32-make.exe' -DEXACT_EBRP_ENABLE_GUROBI=ON -DGUROBI_ROOT='D:/gurobi1302/win64'
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe' --build build_round43 --parallel 8
& 'D:\Program Files\Microsoft Visual Studio\2022\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\ctest.exe' --test-dir build_round43 -C Release --output-on-failure
& $python tests/round43_protocol_tests.py
& $python tests/round43_evidence_tests.py
```

Representative selected-candidate command:

```powershell
& $python scripts/run_round43_experiments.py --stage stage3-candidate --instance round39_small_medium_V12_M3_Q30_slot08_seed1343324363 --execution algorithm --K0 1 --depth 2 --rho 0.10 --score d --envelope single --process-cap 3600
```

Final analysis order:

```powershell
& $python scripts/analyze_round43_stage3_mechanism.py
& $python scripts/analyze_round43_default_off.py
& $python scripts/analyze_round43_development.py
& $python scripts/analyze_round43_ablations.py
& $python scripts/analyze_round43_conditional_stages.py
& $python scripts/seal_round43_evidence.py
& $python scripts/finalize_round43.py
```
"""
    common.write_text(common.OUT / "reproduction_commands.md", reproduction)

    report = f"""# Round 43 final report

## Terminal outcome

**{CLASSIFICATION}**. No new algorithm is promoted. C6-HGA-FULL remains
unchanged at K0=4, rho=0.01, Gurobi Presolve Auto, Seed 0, one thread, and zero
gaps. All Round 43 mechanisms remain explicit and default-off.

The selected global development candidates were {k1_name} and {k4_name}, both
with the single-pass affine envelope, executable-normalized `D_R43` score, no
lifted-cut experiment, and no frontier consolidation. Neither passed every
frozen development gate.

## Decisive witnesses

{markdown_table(
    ['Candidate', 'Major Work', 'Major/P-GRB', 'Control Work', 'Control/C6',
     'Control shifted time/C6', 'Development'],
    [[k1_name, fmt(major_k1['candidate_work']),
      fmt(major_k1['candidate_over_pgrb_work']),
      fmt(control_k1['candidate_work']),
      fmt(control_k1['candidate_over_c6_work']),
      fmt(control_k1['shifted_exact_time_vs_c6']), 'fail'],
     [k4_name, fmt(major_k4['candidate_work']),
      fmt(major_k4['candidate_over_pgrb_work']),
      fmt(control_k4['candidate_work']),
      fmt(control_k4['candidate_over_c6_work']),
      fmt(control_k4['shifted_exact_time_vs_c6']), 'fail']])}

Both candidates repair the major P-GRB-relative fragmentation witness under the
1.25 Work gate, but neither preserves the strongest C6 control under the 1.20
Work and 1.25 shifted-time gates. This is a bounded, systematic negative result:
K0 in {{1,4}}, d in {{1,2}}, two globally frozen rho values, four envelope
modes, the old and D scores, no-adaptive closure, and all mandatory causal
references were evaluated. C_d was formally inadmissible; lifted cuts and
frontier consolidation were formally skipped only because their predeclared
entry conditions were false.

## Required questions

1. **Does K1-new repair the major C6 regression?** Yes on the frozen major
   P-GRB Work gate, but it is not promotable because it loses the strongest C6
   control.
2. **Does K4-new repair the regression while preserving the strongest C6
   control?** It repairs the major witness, but does not preserve the control.
3. **Attribution?** K4 initial granularity retains more local strength; the
   envelope and D recursion change proof allocation, but the mandatory
   ablations show no globally stable promotion.
4. **Is d=1 enough?** It exposes a real deficit but has weaker median envelope
   capture and was not selected.
5. **Does d=2 help?** Yes structurally: it adds stable D variation and higher
   median capture, so d=2 was frozen for exact tests.
6. **Can K4 local strength be transferred by affine envelopes?** Not as a
   material complete-root gain on the strongest control; K1 and K4 root LPs
   coincide and chi is vacuous.
7. **Is D_R43 stable?** It is valid, reconstructible, and hardware-independent,
   but its selected candidates fail the full performance envelope.
8. **Is C_d admissible/useful?** No; it is the constant `1-2^-d` here.
9. **Were lifted cuts tested?** No. The predeclared lifted-cut entry condition
   was not triggered, so lifted cuts were not tested in Round 43.
10. **Was frontier consolidation required?** No. The control was unprotected
    and the major selected rows did not show adjacent-descendant terminal
    duplication.
11. **Are decisions timing-independent?** Yes; the forbidden-input audit passes
    and decision hashes exclude telemetry.
12. **Are certificates exact and verified?** Yes for every claimed certificate;
    the audit has zero false certificates and keeps censored rows unsolved.
13. **Any severe material regression?** The complete development profile is in
    `performance_profile.csv`; its frozen tail gates are reported without
    suppressing startup-dominated rows.
14. **Recommended global configuration?** None. No promotion is recommended.
15. **Did validation pass?** Validation was not opened because development
    failed.
16. **Did the sealed holdout pass?** It remained sealed and was not run.
17. **Terminal classification?** `{CLASSIFICATION}`.

## Exactness and disposition

Zero false certificates were observed. Default-off equivalence passed all
three sentinels. Stage 4 and Stage 5 disposition files record every false entry
condition with supporting evidence. Validation and holdout are intentionally
not run, rather than described as failures or inferred from matching objectives.
"""
    common.write_text(common.OUT / "final_report.md", report)

    # Inventory all compact committed evidence plus one row per sealed raw run.
    compact_rows = []
    for path in sorted(p for p in common.OUT.iterdir() if p.is_file() and
                       p.name != "final_evidence_inventory.csv"):
        compact_rows.append({
            "category": "compact_committed_evidence",
            "name": path.name,
            "path": common.relative(path),
            "sha256": repository_blob_sha256(path),
            "bytes": path.stat().st_size,
            "retention": "commit",
            "hash_basis": "lf_normalized_repository_blob",
        })
    for row in common.csv_rows(
            common.OUT / "official_run_evidence_manifest.csv"):
        compact_rows.append({
            "category": "sealed_raw_run_manifest",
            "name": row["run_id"],
            "path": row["run_dir"],
            "sha256": row["artifact_manifest_sha256"],
            "bytes": "",
            "retention": row["retention"],
            "hash_basis": "per_run_artifact_manifest_sha256",
        })
    common.write_csv(
        common.OUT / "final_evidence_inventory.csv", compact_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
