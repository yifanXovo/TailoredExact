# Relaxation Bound Optimization: Next Notes

The previous round made the paper-core relaxation portfolio try both
operation-budget and no-operation-budget valid variants and keep the stronger
valid lower bound. That fixed the V12 paper-core regression under strong UBs.

This round keeps relaxation changes secondary to UB quality. The focused V12
paper-core rows with the improved reproducible heuristic remain noncertified
because the UB is weaker than the diagnostic archive incumbent. The V12 M2
diagnostic archive row still certifies, which indicates that the relaxation
certificate path remains healthy.

## Safe Optimization Rules

- Cache only valid lower-bound evidence with exact option and interval scope.
- Reuse parent/child relaxation evidence only when the gamma interval, cutoff,
  route-mask mode, movement-domain flags, vehicle-indexed flags, and
  operation-budget/compatibility settings are compatible.
- Never report a cached restricted-pool or diagnostic result as a global lower
  bound.
- Keep the best valid lower bound for every final active interval
  monotonically.

## Variant Logging Required

Every relaxation variant should report:

- variant name;
- solve status;
- objective or lower bound;
- cutoff-fathomed flag;
- runtime;
- whether selected for the final ledger;
- skipped reason.

The current round writes a summary to
`results/primal_ub_improvement_round/relaxation_variant_summary.csv`. Rows
missing detailed per-variant ledgers are marked `not_available_in_raw` rather
than inferred.

## Current Priority

Do not continue optimizing broad frontier scheduling until the paper
reproducible UB improves. Under the archive UB, V12 M2 still closes; under the
new heuristic UB, it does not.
