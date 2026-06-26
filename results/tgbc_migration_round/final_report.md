# TGBC Migration Round Final Report

## Scope

This round migrated the remaining production-relevant TGBC ideas into the paper primal heuristic path without importing HybridGA debug scaffolding or benchmark loops. The changes affect only the reproducible upper-bound generator. Heuristic incumbents remain verifier-gated upper bounds and do not contribute lower-bound evidence.

## Code Changes

- Added compact TGBC re-decode with inherited operation quantities from the first decoded route plan.
- Added decoded-operation guided education using route windows, supply/demand role classification, same-route relocate, zero-operation tail compaction, and cross-route relocation candidates.
- Increased HGA-style population search caps so `--primal-heuristic-runs` can drive a larger seeded route-set search.
- Added deterministic supply-demand pair route-set construction.
- Added deterministic supply-demand quantity beam construction over verifier-gated route-load transfer fragments. This is the main improvement: it optimizes pickup/drop quantities as complete transfer fragments, rebuilds feasible routes through the existing route decoder, and accepts only independently verified route plans.

## Results

| instance | previous paper UB | new UB | diagnostic/archive UB | verifier |
|---|---:|---:|---:|---|
| V4 smoke | 0 | 0 | n/a | passed |
| V12 M1 regenerated | 0.366799836582 | 0.362059778868 | 0.357200583208 | passed |
| V12 M2 regenerated | 0.745474506024 | 0.721861135274 | 0.719065249476 | passed |

The V12 M2 result now meets the strong UB target (`<= 0.724500`) while remaining paper-reproducible and independent of archive scanning. V12 M1 improves over the previous paper heuristic but remains above the known diagnostic/archive UB.

## Audit

`audit_bpc_certificate.py` audited 12 raw JSON files with zero failures. All heuristic rows are correctly noncertified original-problem rows with `certificate_scope=primal_heuristic_ub_only`.

## Remaining Work

- Use the stronger exported heuristic incumbent in a focused paper-core certification run for V12 M1/M2.
- Further improve V12 M1 by adding deeper multi-transfer education or direct route-window inheritance from the original HybridGA implementation.
- Keep archive incumbents diagnostic only; the new quantity-beam TGBC path is the paper-reproducible UB source for the next exact-certification round.
