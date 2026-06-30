# Moderate Seed 3301 Long Oracle Attempt

`moderate_seed3301` remains the best next V20/M3 target, but it did not certify
in this round.

Main rows:

| row | status | LB | UB | gap | oracle attempted | closed | timed out | open leaves |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `moderate_seed3301_oracle600` | not closed | 0.00921610362464 | 0.0491525526647 | 0.8125 | 14 | 4 | 7 | 2 |
| `moderate_seed3301_oracle_deep` | not closed | 0.00921610362464 | 0.0491525526647 | 0.8125 | 20 | 4 | 12 | 2 |

The deep run enabled low-Gini and penalty-domain oracle tightening, recursive
splitting to depth 3, 600s root-leaf oracle budgets, and 1800s child budgets.
It wrote solver-final JSON with return code 0. No archive, known UB, external
incumbent, or manual gamma interval was used.

The remaining blockers are low-Gini child bands under two root leaves. The
hardest children timed out after 1800s each with best bounds near but below the
incumbent cutoff. Since timeout is not a certificate, both root leaves remain
unresolved. Automatic BPC fallback attempted two leaves but did not close any
leaf with exact pricing.

Detailed traces:

- `results/oracle_closure_round/moderate_seed3301_attempt_summary.csv`
- `results/oracle_closure_round/moderate_seed3301_leaf_oracle_trace.csv`
- `results/oracle_closure_round/leaf_partition_tree.csv`

Conclusion: the all-leaf oracle is now working and budgeted correctly, but the
compact exact interval cutoff MIP remains the blocker on two low-Gini leaves.
