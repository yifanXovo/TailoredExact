# Interval Oracle Bound Semantics

This round separates interval-local exact oracle evidence into two auditable
classes.

## Cutoff-Feasibility Mode

`--interval-exact-oracle-mode cutoff-feasibility` builds the original compact
fixed-interval BRP MIP with:

- the full compact route/load/inventory/Gini objective model;
- `gamma_L <= G <= gamma_U`;
- `G + lambda * P <= incumbent_UB - epsilon`;
- objective sense `minimize G + lambda * P`.

This is not a pure feasibility model in the implementation: it is an objective
MIP with an incumbent-cutoff row. If CPLEX proves infeasibility, the interval is
closed. If CPLEX times out with a finite best bound `L`, then `L` is mergeable
only when it is recorded as a valid original fixed-interval bound. The cutoff
row does not invalidate `L` when `L <= cutoff`, because any solution excluded by
the cutoff row has objective greater than `cutoff >= L`.

## Objective-Bound Mode

`--interval-exact-oracle-mode objective-bound` builds the same original compact
fixed-interval model but omits the objective cutoff row. The objective is
`min G + lambda * P`. A finite CPLEX dual bound is a valid lower bound for the
original fixed Gini interval, even when the solve times out.

`--interval-exact-oracle-mode both` currently uses the objective-bound model for
automatic bound merging because it gives the cleanest unconditional interval
lower bound. Proven infeasibility, optimal no-improver status, and timeout dual
bounds are all recorded with explicit model metadata.

## Audit Fields

Each oracle JSON now records:

- `interval_oracle_model_type`;
- `interval_oracle_bound_valid`;
- `interval_oracle_bound_scope`;
- `interval_oracle_objective_sense`;
- `interval_oracle_has_objective_cutoff_row`;
- `interval_oracle_has_gamma_interval_rows`;
- `interval_oracle_solver_best_bound`;
- `interval_oracle_solver_incumbent`;
- `interval_oracle_gap_to_cutoff`;
- `interval_oracle_can_merge_bound`.

The Python audit fails if a row marks a timeout bound mergeable without
`interval_oracle_bound_valid=true`, `interval_oracle_bound_scope=original_fixed_interval`,
and `interval_oracle_has_gamma_interval_rows=true`.
