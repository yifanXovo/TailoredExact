# V20 Replication Round Final Report

Branch: `codex/longrun-round17-local-results`

Commit SHA: recorded in the final response after push verification.  The exact
commit hash is self-referential and cannot be embedded in the same commit
without changing that hash.

## Code Changes

- Added `paper-exact-v20-certificate` as a paper-candidate exact portfolio
  preset for V20 stress certification attempts.
- Added `--summary-out` support to `scripts/run_interval_cutoff_oracles.py`.
- Added `scripts/summarize_v20_replication_round.py` to generate the round CSV
  summaries from raw JSON, interval ledgers, oracle outputs, and merge audits.

## high_imbalance_seed3202 Reproducibility

All three clean replicates certified the original problem with identical
objective/LB/UB:

| replicate | objective | runtime | certified |
|---|---:|---:|---|
| rep1 | 1.74931345205 | 301.031s | true |
| rep2 | 1.74931345205 | 405.994s | true |
| rep3 | 1.74931345205 | 344.974s | true |

The final leaf ledger is certificate-equivalent across replicates, although
rep2 splits one bound-fathomed Gini band more finely than rep1/rep3.

## V20/M3 Mini-Suite

Certified V20 rows now include:

- `high_imbalance_seed3202`: certified in all three replications;
- `tight_T_seed3101`: certified with objective `0.107252734134`.

Other rows remain noncertified:

- `high_imbalance_seed3201`: gap `0.351816064623`, five unresolved leaves;
- `tight_T_seed3102`: gap `0.474370843117`, seven unresolved leaves;
- `moderate_seed3301`: gap `0.830729166667`; oracle closed nine leaves but
  one low-Gini leaf remains open;
- `moderate_seed3302`: gap `0.856770833333`; completed noncertified after
  exceeding the requested 1200s budget.

## Oracle and BPC Diagnostics

The exact interval cutoff oracle helped on `moderate_seed3301`: nine final
leaves were proven infeasible and safely merged, but interval
`[0.0163841842216, 0.0327683684432]` timed out after 600s.  The full-ledger
merge audit correctly reports `certificate_incomplete`.

BPC interval fallback on the same remaining leaf did not close the interval and
is still diagnostic, not default certificate evidence.

## V12 Stability

| row | status | objective | runtime |
|---|---|---:|---:|
| V4 smoke 30s | optimal | 0 | 0.879s |
| V12 M2 canonical 300s | optimal | 0.718504070755 | 206.403s |
| V12 M1 diagnostic 300s | not closed | 0.357200583208 | 300.768s |
| V12 M1 600s | optimal | 0.357200583208 | 507.438s |

## Audit

`scripts/audit_bpc_certificate.py --fail-on-error` audited 22 raw JSON rows and
reported zero failures.  C++ `certificate-basis-test` and
`option-consistency-test` also completed successfully.

## Recommendation

The high-imbalance V20 certificate is reproducible and one additional V20/M3
stress row now certifies.  This justifies keeping a paper-candidate V20 exact
portfolio preset for more targeted testing, but it is not yet enough for broad
paper benchmark claims.  The next round should focus on making the exact
interval cutoff oracle stronger on low-Gini moderate-case leaves and on reducing
the very large runtime overshoot in V20 full-frontier runs.
