# Dynamic Root Bound Impact V2

`results/gf_compact_bc_lowgini_round/dynamic_root_bound_impact_v2.csv`
reuses the matched moderate low-Gini interval rows to compare variants with the
same root-round configuration. The strongest observed progress in this round
comes from low-Gini denominator/objective rows rather than from additional
dynamic support or transfer rows.

The low_gini_1 combined-safe row improved from LB `0.044612735122` at 60s to
`0.048723364` at 3600s. The leaf did not close, so the remaining blocker is
branch-bound progress under a very tight denominator/cutoff regime, not a false
certificate gap.
