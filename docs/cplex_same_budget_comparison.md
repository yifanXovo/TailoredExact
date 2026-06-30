# Same-Budget Plain CPLEX Comparison

Plain compact CPLEX was run as benchmark evidence only.  Its incumbent and
lower bound are not imported into the sealed exact pipeline.

Summary file:

`results/strengthened_oracle_round/cplex_comparison_summary.csv`

Key observations from 300s plain CPLEX rows:

- V12 M1: CPLEX certifies, but this is a compact benchmark row, not BPC
  evidence.
- V12 M2: CPLEX remains noncertified at 300s while the sealed exact pipeline
  certifies.
- V20 rows: CPLEX remains noncertified on the tested stress rows.  For
  `moderate_seed3301`, CPLEX gap is about `0.41148` at 300s while the sealed
  exact pipeline certifies the row after strengthened interval oracle closure.

The comparison is useful for paper context, but all paper-core lower-bound
evidence still comes from full frontier coverage and valid interval certificates.
