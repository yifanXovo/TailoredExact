# paper_core_round_next Final Report

## Code Changes

- Added a certificate-safe frontier relaxation portfolio inside
  `paper-bpc-core`: the configured route-mask operation-budget relaxation runs
  first; if it does not fathom the interval, the solver also runs the same
  vehicle-indexed inventory/route/Gini relaxation with operation-budget rows
  disabled and keeps the stronger valid lower bound.
- Added a route-mask certificate guard: route-mask-based certificates are
  rejected when complete all-subset enumeration is not certifying.
- Extended `certificate-basis-test` with C++ guard fixtures that construct
  unsafe `SolveResult` objects and verify `resultToJson` downgrades them.

## Certificate Risks Eliminated

- A valid strengthening MIP can no longer regress the paper-core ledger merely
  because it is harder to solve within the per-interval time budget.
- Relaxation-only frontier certificates are explicitly distinguished from BPC
  tree certificates; exact pricing closure is required only for intervals using
  BPC tree closure.
- Route-mask certificates now have a direct guard against incomplete
  enumeration.

## V12 M2 Status

The custom vehicle-relaxation row was reproduced and then integrated into
`paper-bpc-core`.

| row | status | objective | LB | UB | runtime | certified |
|---|---|---:|---:|---:|---:|---|
| custom repro 1200s | optimal | 0.719065249476 | 0.719065249476 | 0.719065249476 | 716.3878663 | yes |
| paper-core 300s | optimal | 0.719065249476 | 0.719065249476 | 0.719065249476 | 217.7839095 | yes |
| paper-core 1200s | optimal | 0.719065249476 | 0.719065249476 | 0.719065249476 | 215.7528562 | yes |

The certificate basis is all-final-interval bound fathoming by valid
inventory/route/Gini relaxation lower bounds.

## V12 M1 Status

| row | status | objective | LB | UB | runtime | certified |
|---|---|---:|---:|---:|---:|---|
| paper-core 300s | optimal | 0.357200583208 | 0.357200583208 | 0.357200583208 | 265.220702 | yes |
| paper-core 1200s | optimal | 0.357200583208 | 0.357200583208 | 0.357200583208 | 257.5489498 | yes |

The previous V12 M1 pricing plateau is no longer active on the regenerated
engineering benchmark because the relaxation portfolio fathoms the full
frontier before tree pricing starts.

## Benchmark Rows

- V12 M1 plain CPLEX 300s: certified benchmark objective
  `0.357200583208`.
- V12 M2 plain CPLEX 300s: noncertified benchmark row, UB
  `0.72439493548`, LB `0.62335837374`, gap `0.139477178527`.

CPLEX rows are benchmark evidence only and are not BPC lower-bound evidence.

## Audit

`scripts/audit_bpc_certificate.py results/paper_core_round_next/raw
--csv-out results/paper_core_round_next/audit/certificate_audit.csv
--fail-on-error`

Result: `audited_rows=11 failures=0`.

## Remaining Gaps

- These V12 rows are regenerated engineering benchmarks, not confirmed
  historical paper targets.
- Bound time, not pricing time, is now the dominant V12 paper-core component.
  Next optimization should reduce repeated relaxation MIP time, especially by
  caching or early-selecting the no-operation-budget fallback when it proves
  cutoff infeasibility.

