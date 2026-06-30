# Oracle Budget Semantics Audit

This round changes automatic interval-oracle budgets from an ambiguous single
number into explicit per-leaf, total, and child budgets.

New options:

- `--auto-interval-oracle-leaf-budget-policy per-leaf|total|adaptive`
- `--auto-interval-oracle-total-budget <seconds>`
- `--auto-interval-oracle-child-time-limit <seconds>`
- `--auto-interval-oracle-recursive-split true|false`
- `--auto-interval-oracle-min-width <double>`
- `--auto-interval-oracle-max-children-total <N>`

With `per-leaf`, `--auto-interval-oracle-time-limit` is the root-leaf CPLEX
time limit. Split children use `--auto-interval-oracle-child-time-limit` when
provided, otherwise the root-leaf limit. With `total`, the same option is used
as the oracle-phase budget unless `--auto-interval-oracle-total-budget` is set.
`adaptive` currently behaves like per-leaf with an optional total cap; it does
not change certificate logic.

Audit-visible JSON fields now record requested and actual leaf limits, total
budget, policy, budget exhaustion, and the per-leaf limits actually used. The
CSV summary is:

```text
results/oracle_closure_round/oracle_budget_audit.csv
```

Observed behavior:

- `moderate_seed3301_oracle_deep` used 600s root-leaf limits and 1800s child
  limits; it attempted 20 oracle solves, closed 4 root leaves, and left 2 root
  leaves unresolved.
- `tight_T_seed3102_controlled` used 120s root and child limits; it attempted
  9 oracle solves and all timed out.
- `high_imbalance_seed3201_controlled` used 120s root and child limits; it
  attempted 6 oracle solves and all timed out.

Conclusion: the earlier 20s-child behavior was a budget propagation issue. The
new fields make the actual CPLEX oracle budget visible and auditable.
