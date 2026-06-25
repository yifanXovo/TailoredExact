# Frontier Ledger Monotonicity Audit

The current frontier ledger uses a final active-interval set. Parent intervals
that are adaptively split are marked `replaced_by_children` and are not counted
as final certificate intervals. Children inherit the parent lower bound and may
then receive stronger relaxation lower bounds.

The round-next interval CSVs show the intended monotonic behavior:

- V12 M2 parent interval 2 `[0.359532624738,0.539298937107]` has LB
  `0.577122634894` and is replaced by children.
- Child interval 4 inherits coverage and is strengthened to LB
  `0.719065249476`.
- Parent interval 5 `[0.449415780923,0.539298937107]` has LB
  `0.667005791079` and is replaced by children.
- Child intervals 6 and 7 are both strengthened to LB `0.719065249476`.

The same pattern appears for V12 M1:

- Parent interval 2 `[0.178600291604,0.267900437406]` is replaced.
- Child interval 5 is replaced.
- Final children 6, 8, and 9 are strengthened to the incumbent cutoff.

The operation-budget relaxation portfolio fixes the observed lower-bound
regression mode. A later phase no longer relies only on the time-limited
operation-budget MIP best bound; when that bound is weak, it also tries the
compatible no-operation-budget relaxation and keeps the maximum valid lower
bound for the same interval.

Evidence:

- `results/paper_core_round_next/raw/v12_m2_paper_core_300s_relax_portfolio.intervals.csv`
- `results/paper_core_round_next/raw/v12_m1_paper_core_300s_relax_portfolio.intervals.csv`
- `results/paper_core_round_next/interval_ledger_summary.csv`

