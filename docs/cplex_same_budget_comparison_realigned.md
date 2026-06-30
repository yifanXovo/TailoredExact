# CPLEX Same-Budget Comparison, Realigned

CPLEX rows in this round are benchmark-only evidence.  They are not used as
paper-gf-bpc-core lower-bound evidence.

Files:

- `results/paper_core_realignment_round/cplex_summary.csv`
- `results/paper_core_realignment_round/exact_vs_cplex_bound_quality.csv`

The CPLEX summary is copied from the immediately preceding strengthened-oracle
round, where 300s compact benchmark rows were run for V12 and five V20 cases.
The comparison table maps those benchmark rows against the realigned
`paper-gf-bpc-core` rows available in this round.

Interpretation:

- CPLEX can provide useful benchmark LB/UB/gap context.
- CPLEX compact interval oracle evidence is not a core BPC certificate source.
- Exact-portfolio rows and CPLEX rows must not be mixed with paper-core claims.
