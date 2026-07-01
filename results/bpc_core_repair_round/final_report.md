# BPC Core Repair Round Final Report

Branch: `codex/longrun-round17-local-results`

Final commit SHA: recorded in the final response after commit/push.

## Scope

This round kept `paper-gf-bpc-core` as the target.  No interval-oracle
certificate, route-mask enumeration certificate, archive incumbent, known UB,
external incumbent, CPLEX benchmark bound, V/M special-casing, or
instance-specific solver logic was used as paper-core evidence.

## Target Leaves

The frozen targets are listed in `target_leaf_manifest.csv`:

- V12 M2 controlling leaf: interval 7,
  `[0.493971548644, 0.538878053066]`.
- V12 M1 controlling leaf: interval 12,
  `[0.223250364505, 0.234412882731]`.
- moderate_seed3301 controlling leaf: interval 2,
  `[0.0245762763324, 0.0368644144986]`.
- high_imbalance_seed3202 controlling leaf: interval 9,
  `[0.5046875, 0.534375]`.
- V12 M2 forced-BPC diagnostic leaf.

`bpc_leaf_data_audit.csv` audited 16 target runs and found no leaf-data
failures.

## BPC Diagnostics

Long-budget diagnostics were mandatory and were run:

| Variant | Leaf | Budget | Pricing calls | Pricing time | Columns | Best reduced cost | Exact pricing |
|---|---:|---:|---:|---:|---:|---:|---|
| V12 M2 all improvements | 7 | 3600s | 4 | 3596.697s | 42252 | -0.00327041731624 | false |
| V12 M1 all improvements | 12 | 3600s | 1 | 3599.406s | 26006 | -0.0088398618421 | false |
| moderate_seed3301 all improvements | 2 | 3600s | 1 | 3579.848s | 166161 | 0.00469307183545 | false |
| high_imbalance_seed3202 all improvements | 9 | 300s | 1 | 291.464s | 94059 | 0.0700591864494 | false |

No BPC leaf closed with exact pricing.

## Optimization Effects

Route-skeleton/loading-DP mode and completion-bound pruning were wired into the
paper-core pricing controls.  In 300s diagnostics they reduced some state
counts but did not produce closure:

| Leaf | Baseline route states | Improved route states | Baseline op states | Improved op states |
|---|---:|---:|---:|---:|
| V12 M1 | 87442803 | 82846349 | 0 | 0 |
| moderate_seed3301 | 173945096 | 169679957 | 107390663 | 103089986 |
| high_imbalance_seed3202 | 225792013 | 224187071 | 0 | 0 |
| V12 M2 forced | 108817682 | 106811911 | 1149989833 | 1125635095 |

V12 M2 did not improve under the same 300s comparison
(`104009341 -> 104692374` route states and
`618664440 -> 626039488` operation states).

Safe-plus dominance remained certificate-safe by construction, but it did not
produce enough pruning in the route-skeleton path.  RMP seeding did not produce
node closure.  BPC cut separation remained ineffective in these runs:
`cuts_added=0` for every target row.

## Large-V Diagnostics

The requested V50/V100 checks exposed finalization defects rather than usable
paper-core progress:

- V50/M3 exceeded the external command timeout without solver final JSON.
- V100/M5 exited with access violation `0xc0000005`.

Wrapper-level noncertified JSONs were written for audit visibility.  They are
not certificates.

## Audit

Audit outputs:

- `certificate_audit.csv`: 18 raw JSON rows audited, 0 failures.
- `no_instance_special_case_audit.txt`: passed.
- `no_v_threshold_audit.txt`: passed.
- `proof_coverage_audit.csv`: written for all round artifacts.
- `certificate-basis-test`: passed.
- `option-consistency-test`: passed.

## Answers

1. Long-budget BPC did reveal more detail than short diagnostics: V12 M2
   advanced through more pricing calls, but negative reduced cost remained.
2. Route-skeleton/loading-DP reduced some state counts modestly, but not enough.
3. Safe dominance v2 remained conservative and did not close a leaf.
4. Completion bounds pruned some states but did not change the closure result.
5. Domain transfer was audited as consistent, but did not make pricing close.
6. RMP seeding did not materially improve convergence.
7. BPC cuts did not improve RMP bounds because no cut rows were added.
8. Branching did not help because root pricing did not close.
9. No BPC leaf closed with exact pricing.
10. `paper-gf-bpc-core` did not certify V12 M1 or V12 M2 in this round.
11. The remaining problem is exact pricing/decomposition: route-skeleton state
    explosion, large operation-DP state counts, inactive cuts, and no finite
    proof of absence of negative reduced-cost columns within the tested budgets.
12. The next algorithmic option is a deeper branch-price-and-cut redesign:
    stronger route-skeleton Pareto dominance, active cut separation before
    pricing dominates, stronger exact completion bounds, and possibly a
    different master/pricing decomposition.  BPC should not be demoted before
    that redesign, but current empirical paper claims must not present it as an
    effective closure engine.

## Paper-Core Decision

The paper-core definition remains clean and unified, but the BPC implementation
is not yet practically meaningful as an exact fallback.  The project should not
claim BPC-core empirical closure beyond rows closed by relaxation.  Another
targeted BPC pricing/master redesign round is required before broad paper
BPC-core benchmarking.
