# Automatic Interval-Oracle Closure

Automatic interval-oracle closure is enabled by
`--auto-interval-oracle true`. The sealed V20 preset enables it by default.

## Workflow

1. Run the full Gini-frontier relaxation/BPC ledger normally.
2. If the full ledger is already closed, no oracle is called.
3. If final unresolved leaves remain, read the final interval CSV.
4. Select unresolved leaves by the configured generic ordering.
5. For each selected leaf, run the compact original-model fixed-interval
   cutoff oracle using the current run's verified incumbent UB.
6. If the oracle proves infeasibility, mark the exact leaf closed with
   `interval_exact_cutoff_mip_infeasible`.
7. If the oracle finds a verified improving original solution, the current
   ledger is not certified; the frontier must be restarted with the new UB.
8. If the oracle times out or remains unresolved, the full run remains
   noncertified and records the first blocking leaf.

## Merge Rule

A focused oracle result is merged only into the exact final leaf it was created
from. The merge is safe only when every final leaf is closed by an existing
valid lower-bound basis, exact BPC tree closure, or proven interval cutoff MIP
infeasibility. Partial closure is recorded as diagnostic evidence and cannot
produce `certified_original_problem=true`.
