#!/usr/bin/env python3
"""Create the compact final Round 42 decision and narrative artifacts."""

from __future__ import annotations

from typing import Any

import round42_common as common


MAJOR = "round39_small_medium_V12_M3_Q30_slot08_seed1343324363"
STRONG = "round39_small_hard_V12_M3_Q30_slot08_seed1288546114"
NUMERICAL = "round39_small_hard_V12_M3_Q20_slot07_seed621538683"
ARMS = (
    "C6-HGA-FULL-K4",
    "C6-K1-SINGLE",
    "EXTERNAL-K2-FIXED",
    "ST-K2-P-CORE",
    "ST-K4-P-CORE",
    "ST-K4-P-CORE-HIERARCHICAL",
    "PAIRED-K4",
    "PAIRED-K4-FACTORED",
    "C6-SIBLING-CORE",
    "C6-SIBLING-CORE-FACTORED",
)


def truth(value: Any) -> bool:
    return value is True or str(value).strip().lower() in {"1", "true", "yes"}


def number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def fmt(value: Any, digits: int = 3) -> str:
    parsed = number(value)
    return f"{parsed:.{digits}f}"


def main() -> int:
    per_run = common.csv_rows(common.OUT / "per_run_results.csv")
    comparisons = common.csv_rows(common.OUT / "development_comparison.csv")
    ranking = common.csv_rows(common.OUT / "candidate_ranking.csv")
    certificates = common.csv_rows(common.OUT / "certificate_audit.csv")
    root_rows = common.csv_rows(common.OUT / "root_relaxation_comparison.csv")
    equivalence = common.csv_rows(common.OUT / "default_c6_equivalence.csv")

    by_run = {(row["instance_id"], row["arm"]): row for row in per_run}
    by_comparison = {
        (row["instance_id"], row["candidate"]): row
        for row in comparisons
    }

    trajectory_rows: list[dict[str, Any]] = []
    for instance_id in (MAJOR, STRONG, NUMERICAL):
        for arm in ARMS:
            row = by_run[(instance_id, arm)]
            comparison = by_comparison.get((instance_id, arm))
            trajectory_rows.append({
                "instance_id": instance_id,
                "diagnostic_role": row["diagnostic_role"],
                "arm": arm,
                "status": row["status"],
                "strict_certificate": row["strict_certificate"],
                "exact_phase_seconds": row["exact_phase_seconds"],
                "solver_work": row["solver_work"],
                "solver_nodes": row["solver_nodes"],
                "independent_integer_proof_jobs": row[
                    "independent_integer_proof_jobs"],
                "native_optimize_calls": row["native_optimize_calls"],
                "work_ratio_vs_c6": comparison["work_ratio"]
                    if comparison else 1.0,
                "shifted_time_ratio_vs_c6": comparison[
                    "shifted_time_ratio"] if comparison else 1.0,
                "model_nonzeros": row["model_nonzeros"],
                "sibling_pairs_coalesced": row["sibling_pairs_coalesced"],
                "sibling_replaced_leaf_count": row[
                    "sibling_replaced_leaf_count"],
                "sibling_unresolved_union_count": row[
                    "sibling_unresolved_union_count"],
                "coverage_valid": row["coverage_valid"],
                "lifecycle_complete": row["lifecycle_complete"],
            })
    common.write_csv(
        common.OUT / "representative_trajectory_analysis.csv",
        trajectory_rows,
    )

    def witness_table(instance_id: str) -> str:
        lines = [
            "| Arm | Work ratio | Shifted-time ratio | Exact s | Work | Nodes | Proof jobs | Strict |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
        for arm in ARMS:
            row = by_run[(instance_id, arm)]
            comparison = by_comparison.get((instance_id, arm))
            work_ratio = number(comparison["work_ratio"]) if comparison else 1.0
            time_ratio = number(comparison["shifted_time_ratio"]) if comparison else 1.0
            lines.append(
                f"| {arm} | {work_ratio:.3f} | {time_ratio:.3f} | "
                f"{number(row['exact_phase_seconds']):.2f} | "
                f"{number(row['solver_work']):.2f} | "
                f"{number(row['solver_nodes']):.0f} | "
                f"{row['independent_integer_proof_jobs']} | "
                f"{row['strict_certificate']} |"
            )
        return "\n".join(lines)

    trajectory_md = f"""# Representative trajectory analysis

The two prespecified architecture witnesses and the fail-closed numerical
endpoint are recorded in `representative_trajectory_analysis.csv`. Ratios use
the frozen contemporary C6-HGA-FULL-K4 development row.

## Major fragmentation witness

{witness_table(MAJOR)}

The root-LP audit gives the same `0.028210692227...` lower bound for C6 and all
K4 static/paired formulations. Hierarchical ST-K4 reduces the independent
integer jobs from 8 to 1 and cuts Work to 0.426x C6, but the gain is not stable
on the positive control. Terminal sibling coalescing accepts two exact sibling
pairs and replaces four leaves, reducing the counted integer proof jobs from 8
to 4. Its union remains unresolved at the shared process cap, so coverage is
retained and strict certification is correctly refused.

## Strongest K4 positive control

{witness_table(STRONG)}

Every candidate is slower than C6 here. K1 demonstrates the interval-strength
loss most sharply at 5.532x Work. The best Round 42 family ratio on this control
is 1.330x for flat ST-K4, still above the frozen 1.10 limit. Factored sibling
coalescing removes two counted proof jobs but uses 1.422x Work and 1.508x shifted
time.

## Numerical fail-closed endpoint

The CSV retains all ten arms. Baseline C6 and contemporary K1 remain honest
noncertificates. Several static covers certify because their native complete
cover and original-space verifier close the endpoint; none is treated as a
false certificate. The endpoint contributes catastrophic regressions exactly
where both frozen Work and shifted-time ratios exceed 1.25.
"""
    common.write_text(
        common.OUT / "representative_trajectory_analysis.md", trajectory_md)

    not_run_columns = [
        "experiment_group", "status", "reason", "candidate", "baseline",
        "run_count", "gate_eligible", "holdout_remained_sealed",
    ]
    common.write_csv(common.OUT / "validation_comparison.csv", [{
        "experiment_group": "validation",
        "status": "not_run",
        "reason": "no_candidate_passed_frozen_development_gate",
        "candidate": "",
        "baseline": "C6-HGA-FULL-K4",
        "run_count": 0,
        "gate_eligible": False,
        "holdout_remained_sealed": True,
    }], not_run_columns)
    common.write_csv(common.OUT / "holdout_comparison.csv", [{
        "experiment_group": "final_holdout",
        "status": "not_run",
        "reason": "validation_not_reached_no_development_eligible_candidate",
        "candidate": "",
        "baseline": "C6-HGA-FULL-K4",
        "run_count": 0,
        "gate_eligible": False,
        "holdout_remained_sealed": True,
    }], not_run_columns)

    family_a = """# Family A iteration log

## Base: flat ST-K4-P-Core

All 10 development rows completed with one model, one native MIP optimize,
zero false certificates, and no certificate regression. The major witness
ratios were 0.780848 Work and 0.750059 shifted time, but the strongest K4
control regressed to 1.329846 Work and 1.299000 shifted time. Two instances
were catastrophic. The Work geometric mean is infinite because C6 records
zero Work on one easy case while this static arm records positive Work.

Dominant mechanism: the K4 root bound is preserved, but the monolithic integer
search is unstable across regimes; the positive-control regression is not a
model-build or lost-relaxation-strength effect.

## Required refinement: hierarchical selectors

The uniform dyadic hierarchy preserves the same four endpoints and exact
feasible union. It improves the major witness to 0.426242 Work and 0.409840
shifted time, but worsens the strongest control to 1.570105 and 1.570243. It
also has two catastrophic rows. Family A is rejected. No optional second
refinement is justified because the required refinement gives no stable
general signal.
"""
    common.write_text(common.OUT / "family_a_iteration_log.md", family_a)

    family_b = """# Family B iteration log

## Base: paired K4

All 10 adjacent-pair complete covers certified with zero false certificates
and no certificate regression. The major witness uses 4,132.979895 Work and
1,868.013828 exact seconds: ratios 1.060013 and 1.050692 versus C6. The strongest
control ratios are 1.411236 and 1.459460, producing one catastrophic row.

Dominant mechanism: quarter-width root strength is retained, but the two block
trees duplicate search. On the major witness the paired model totals 341,315
nonzeros and is worse than both flat and hierarchical full ST-K4.

## Required refinement: paired K4 factored

Uniform exact factoring removes 604 indicator rows on the major pair but grows
the exported model from 341,315 to 342,713 nonzeros. Major Work/time worsen to
1.133939/1.114984 versus C6. The strongest control improves relative to the
base pair but still fails at 1.342232/1.331534. Family B is rejected. This is
also the top lexicographically ranked exact family, and its required uniform
refinement worsened the primary witness, so no optional second refinement is
supported.
"""
    common.write_text(common.OUT / "family_b_iteration_log.md", family_b)

    family_c = """# Family C iteration log

## Base: C6 sibling Core

All 10 development rows exercised the unchanged C6 scheduler before terminal
closure. Coverage and lifecycle audits pass with zero false certificates. On
the major witness, two sibling pairs are coalesced, four terminal leaves are
replaced, and counted integer proof jobs fall from 8 to 4. One union remains
unresolved at the shared cap; Work is 1.031932x C6 and the candidate correctly
refuses a strict certificate, creating one certificate regression. The
strongest control remains certified but regresses to 1.489296 Work and 1.468462
shifted time.

## Required refinement: C6 sibling Core factored

The same structural trigger with uniform exact factoring reduces major Work to
0.962999x but still reaches the cap (1.000028 shifted time) with the same honest
certificate regression. The strongest control remains certified but uses
1.421817x Work and 1.508178x shifted time. Family C is rejected. The unresolved
union retains a union-only lower bound; no bound is copied to either child and
no coverage is discarded.
"""
    common.write_text(common.OUT / "family_c_iteration_log.md", family_c)

    iteration_log = """# Round 42 research iteration log

The split, gates, materiality rules, candidate definitions, and executable were
frozen before official candidate development runs. All rows use the 1,800-second
process-entry cap, one Gurobi thread, Seed 0, Auto presolve, and zero gaps.

| Order | Family | Iteration | Uniform mechanism | Development outcome |
|---:|---|---|---|---|
| 0 | reference | K1 | contemporary exact C6-K1-SINGLE | completed; witness repaired, positive control catastrophic |
| 0 | causal | fixed K2 | External-K2-Fixed versus ST-K2-P-Core | completed; static/external gmeans 1.026 Work, 1.029 shifted time |
| 1 | A | base | flat ST-K4-P-Core | rejected: 2 catastrophics; positive control 1.330 Work |
| 2 | A | required refinement | dyadic hierarchical K4 selectors | rejected: witness 0.426 Work but positive control 1.570 |
| 3 | B | base | adjacent paired K4 Core blocks | rejected: witness 1.060 Work; 1 catastrophic |
| 4 | B | required refinement | exact common-row factoring in both blocks | rejected: witness worsened to 1.134 Work |
| 5 | C | base | exact terminal sibling Core union | rejected: cap-bound certificate regression; control 1.489 Work |
| 6 | C | required refinement | exact common-row factoring in every sibling union | rejected: certificate regression persists; control 1.422 Work |

The lexicographically best exact family is paired-K4. Its already required
uniform factoring refinement worsens the major witness and aggregate shifted
time, so the optional second-refinement allowance is not used. Engineering
smokes remain separate from official development evidence, and invalidated raw
runs remain preserved locally.
"""
    common.write_text(common.OUT / "research_iteration_log.md", iteration_log)

    factoring_md = """# Common-row factoring audit

The transformation is uniform and exact: coefficient-identical rows present in
every segment are emitted once; shared LHS/sense rows with varying RHS use an
exact selector-weighted RHS; residual rows remain conditional. No row choice
depends on an instance or observed outcome.

- Paired-K4 base/refined comparisons: 10/10 complete.
- Terminal-sibling base/refined comparisons: 10/10 complete.
- Every reported strict result is independently re-audited in
  `certificate_audit.csv`; false certificates are zero.

Factoring does not provide a stable search improvement. On the major paired
case it removes 604 indicator rows but increases nonzeros from 341,315 to
342,713 and worsens Work from 4,132.98 to 4,421.22. In the coalesced major case
it reduces nonzeros from 355,422 to 354,588 and Work from 4,023.49 to 3,754.73,
but both variants reach the process cap and fail closed. On the strongest
control both factored variants reduce Work relative to their bases, yet remain
well above C6. Per-instance row, nonzero, Work, and shifted-time effects are in
`common_row_factoring_audit.csv`.
"""
    common.write_text(common.OUT / "common_row_factoring_audit.md", factoring_md)

    false_certificates = sum(truth(row["false_certificate"])
                             for row in certificates)
    strict_rows = sum(truth(row["strict_certificate"])
                      for row in certificates)
    root_valid = sum(truth(row["diagnostic_valid"]) for row in root_rows)
    development_passes = [row for row in ranking
                          if truth(row["development_gate_passed"])]
    default_equivalent = all(truth(row["default_c6_equivalence_passed"])
                             for row in equivalence)
    decision = {
        "schema": "round42-final-decision-v1",
        "round_id": 42,
        "outcome": "bounded_systematic_negative_result",
        "conclusion": (
            "No stable improvement was found within the tested "
            "static-single-tree, paired-block, and "
            "terminal-sibling-coalescing architecture families."
        ),
        "validated_default": "C6-HGA-FULL K=4 rho=0.01",
        "validated_default_changed": False,
        "candidate_controls_default_off": True,
        "development_candidate_count": len(ranking),
        "development_candidates_passing": len(development_passes),
        "best_ranked_family_candidate": ranking[0]["candidate"],
        "best_candidate_development_gate_passed": False,
        "best_candidate_required_refinement": "PAIRED-K4-FACTORED",
        "optional_second_refinement_run": False,
        "optional_second_refinement_reason": (
            "required factoring worsened the major witness and aggregate "
            "shifted time, so there was no clear general positive signal"
        ),
        "validation": {
            "status": "not_run",
            "eligible": False,
            "reason": "no candidate passed every frozen development gate",
        },
        "final_holdout": {
            "status": "not_run",
            "eligible": False,
            "sealed": True,
            "reason": "validation was not reached",
        },
        "stable_candidate_for_broad_qualification": False,
        "development_evidence_rows": len(per_run),
        "strict_certificate_rows": strict_rows,
        "false_certificates": false_certificates,
        "root_diagnostic_rows": len(root_rows),
        "root_diagnostic_valid_rows": root_valid,
        "default_c6_equivalence_passed": default_equivalent,
        "default_c6_equivalence_sentinels": len(equivalence),
        "completed_families": {
            "A": ["ST-K4-P-CORE", "ST-K4-P-CORE-HIERARCHICAL"],
            "B": ["PAIRED-K4", "PAIRED-K4-FACTORED"],
            "C": ["C6-SIBLING-CORE", "C6-SIBLING-CORE-FACTORED"],
        },
        "contemporary_references": [
            "C6-HGA-FULL-K4", "C6-K1-SINGLE", "EXTERNAL-K2-FIXED",
            "ST-K2-P-CORE",
        ],
        "p_grb_reference_run": False,
        "p_grb_reference_reason": (
            "no candidate passed development or supported a repaired-C6 "
            "claim requiring a new P-GRB adjudication"
        ),
        "candidate_ranking": ranking,
    }
    common.write_json(common.OUT / "final_decision.json", decision)

    major = {arm: by_run[(MAJOR, arm)] for arm in ARMS}
    strong = {arm: by_run[(STRONG, arm)] for arm in ARMS}
    report = f"""# Round 42 decomposition-architecture optimization

## Outcome

**bounded_systematic_negative_result**

No stable improvement was found within the tested static-single-tree,
paired-block, and terminal-sibling-coalescing architecture families. This is a
bounded result about the six frozen Family A/B/C implementations, not a claim
that every future decomposition algorithm is impossible. The validated default
remains **C6-HGA-FULL, K=4, rho=0.01**; every Round 42 mechanism remains
explicit and default-off.

All 6 promotion candidates completed the 10-instance development panel. None
passed every frozen gate. Validation was therefore ineligible and the final
holdout remained sealed. Across 100 development/reference rows there are
{false_certificates} false certificates; {strict_rows} rows are strict. All
three default-off sentinels match Round 41 in all 25 deterministic fields and
trajectory hashes.

## Causal references

At fixed K2 granularity, ST-K2 uses one proof tree instead of External-K2's two.
Its development geometric means are 1.026238 Work and 1.028505 shifted time:
the architecture is dramatically better on the major witness (0.452427 Work,
0.451140 shifted time) but worse on the strongest control (1.331848 and
1.297014). A single tree is therefore not uniformly beneficial even at fixed K.

Contemporary exact K1 reduces the major witness to 0.782874 Work and 0.758360
shifted time, but loses quarter-width interval strength on the strongest K4
control: 5.531719 Work and 5.361040 shifted time. It is a useful reference, not
a stable candidate. P-GRB was not rerun because no Round 42 candidate passed
development or supported a repaired-C6 claim requiring new P-GRB adjudication.

## Family results

Family A proves that ST-K4 is technically feasible: every static K4 row uses
one exact model and one native optimize, with zero false certificates. Flat
ST-K4 meets the major witness threshold (0.780848 Work, 0.750059 time) but fails
the strongest control (1.329846, 1.299000) and has two catastrophics.
Hierarchical selectors greatly improve the witness (0.426242, 0.409840) but
worsen the strongest control to 1.570105/1.570243. The root K4 bound is unchanged,
so remaining regressions are integer-search effects.

Family B's paired cover is exact but does not interpolate favorably. On the
major witness it uses 4,132.98 Work versus C6's 3,898.99 and flat ST-K4's
3,044.52. Factoring grows average paired nonzeros from 166,368 to 167,556 and
worsens the major ratios from 1.060013/1.050692 to 1.133939/1.114984.

Family C exercises real adaptive sibling geometry with atomic coverage. On the
major witness both variants coalesce two pairs and replace four terminal
leaves. Base/factored counted proof jobs fall from {major['C6-HGA-FULL-K4']['independent_integer_proof_jobs']}
to {major['C6-SIBLING-CORE']['independent_integer_proof_jobs']}, but one union
remains unresolved at the shared cap and both correctly refuse certification.
Factoring lowers Work from 4,023.49 to 3,754.73 but does not close the union.
On the strongest control the same mechanism reduces proof jobs from
{strong['C6-HGA-FULL-K4']['independent_integer_proof_jobs']} to
{strong['C6-SIBLING-CORE']['independent_integer_proof_jobs']} while regressing
to 1.489296 Work (base) or 1.421817 (factored).

## Model, relaxation, and lifecycle diagnosis

The root audit contains {root_valid}/{len(root_rows)} valid diagnostic rows.
All 60 standalone static/composite rows are valid. Twelve C6-derived initial
census rows are explicitly unavailable on four instances and are left blank,
not imputed. On the major witness, C6 and every K4 static/paired formulation
share root bound `0.028210692227...`; ST-K2/External-K2 share
`0.024872307367...`. Root solves take seconds, while exact runs take up to the
cap, locating the dominant cost in integer proof search. Binary/integer/
continuous counts and model build/read times are retained for every static and
composite row. C6 union ledgers expose total rows/columns/nonzeros and timings
but not a variable-type split; those cells are explicitly blank.

Coverage is valid and lifecycle-complete in all 100 evidence rows. The sibling
audit records considered/accepted pairs, replaced leaf IDs, atomic events,
fallbacks, and unresolved unions. Incomplete union bounds remain union-only.
Complete external covers certify only when every native component is exact,
the minimum component bound equals the independently verified union objective,
and the original-space verifier passes.

## Frozen selection and confirmation

The best lexicographically ranked exact family is PAIRED-K4, but it fails the
major and strongest-control gates and has one catastrophic regression. Its
required uniform factoring refinement worsens the major witness and aggregate
shifted time, so there is no clear general signal for an optional second
refinement. No candidate may advance to validation. `validation_comparison.csv`
and `holdout_comparison.csv` record this non-run status; no holdout candidate
result was inspected.

## Required questions

1. **Fixed-K2 architecture effect:** one tree gives a huge witness win but
   overall gmeans of 1.026 Work/1.029 shifted time, so it is unstable.
2. **ST-K4 feasibility:** yes—exact, deterministic, one model/one optimize.
3. **K4 strength versus fragmentation:** root strength is preserved and the
   witness improves, but control regressions prevent stability.
4. **Common-row factoring:** mathematically exact, empirically inconsistent;
   it does not produce a stable search improvement.
5. **Hierarchical encoding:** it materially improves flat K4 on the witness but
   materially worsens the strongest control.
6. **Paired-K4:** no; it is worse than C6 and both ST-K4 variants on the major
   witness.
7. **Sibling repair of the witness:** no; it reaches the cap with an unresolved
   union and an honest certificate regression.
8. **Sibling preservation of the positive case:** certification is preserved,
   performance is not (1.489 base, 1.422 factored Work ratios).
9. **Proof jobs removed on the major witness:** A removes 7 of 8, B removes 6,
   and C removes 4; fewer jobs alone does not guarantee less Work.
10. **Remaining causes:** unstable monolithic integer search, duplicated paired
    search, larger selector-weighted factored models, and cap-bound union proof.
11. **Completed work:** every A/B/C base and required refinement completed.
12. **Development pass:** none.
13. **Validation pass:** none; validation was ineligible and not run.
14. **Holdout pass:** none; holdout remained sealed and was not run.
15. **Stable broad-qualification candidate:** no.
16. **Rejected bounded space:** flat/hierarchical static single-tree K4,
    adjacent paired K4 with/without common-row factoring, and structural
    terminal-sibling coalescing with/without common-row factoring.

## Verification

- Frozen executable SHA-256:
  `82178ffbbb8106c06661fcec8fd57ce7fe63b1fb9b6340b9d85bd269fc013fbe`.
- C++ tests at implementation freeze: 20/20 passed.
- Round 42 protocol tests: 7/7 passed before final packaging.
- Default C6 equivalence: 3/3 sentinels, 25/25 deterministic fields each.
- Large raw logs and models remain local; compact hashes, manifests, audits,
  and reproduction scripts are retained here.
"""
    common.write_text(common.OUT / "final_report.md", report)
    evidence_names = (
        "source_of_truth.md", "scientific_problem_statement.md",
        "experiment_split_freeze.json", "development_manifest.csv",
        "validation_manifest.csv", "final_holdout_manifest.csv",
        "implementation_freeze.json", "generalized_segmented_formulation.md",
        "external_k2_vs_static_k2.md", "external_k2_vs_static_k2.csv",
        "st_k4_formulation.md", "paired_k4_formulation.md",
        "sibling_coalescing_formulation.md", "exactness_propositions.md",
        "common_row_factoring_audit.md", "common_row_factoring_audit.csv",
        "model_size_comparison.csv", "root_relaxation_comparison.csv",
        "per_run_results.csv", "development_comparison.csv",
        "validation_comparison.csv", "holdout_comparison.csv",
        "certificate_audit.csv", "coverage_lifecycle_audit.csv",
        "default_c6_equivalence.csv", "representative_trajectory_analysis.md",
        "representative_trajectory_analysis.csv", "family_a_iteration_log.md",
        "family_b_iteration_log.md", "family_c_iteration_log.md",
        "research_iteration_log.md", "candidate_ranking.csv",
        "final_report.md", "final_decision.json",
    )
    common.write_csv(common.OUT / "evidence_package_manifest.csv", [{
        "file": name,
        "bytes": (common.OUT / name).stat().st_size,
        "sha256": common.sha256(common.OUT / name),
        "scope": "compact_round42_evidence",
    } for name in evidence_names])
    print({
        "outcome": decision["outcome"],
        "development_rows": len(per_run),
        "ranked_candidates": len(ranking),
        "development_passes": len(development_passes),
        "false_certificates": false_certificates,
        "root_valid": root_valid,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
