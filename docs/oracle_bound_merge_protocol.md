# Oracle Bound Merge Protocol

Automatic oracle merge now handles both closed leaves and valid timeout lower
bounds.

For each final unresolved frontier leaf:

1. Run the interval oracle using the sealed run's verified incumbent UB.
2. If the oracle proves infeasibility, mark the leaf bound-fathomed.
3. If the oracle returns a valid lower bound, set
   `interval_lower_bound = max(existing_LB, oracle_bound)`.
4. If the updated lower bound reaches the incumbent UB within tolerance, mark
   the leaf bound-fathomed.
5. If a leaf is split, merge child evidence only when the children exactly
   partition the parent. The parent lower bound is the minimum child lower
   bound.
6. Recompute the full frontier lower bound from final leaves only, skipping
   `replaced_by_children` rows.

The merged interval ledger records:

- `oracle_bound_merged`;
- `oracle_bound_value`;
- `oracle_bound_status`;
- `oracle_bound_source_json`;
- `oracle_bound_solver_status`;
- `oracle_bound_model_type`;
- `oracle_bound_valid`;
- `lower_bound_before_oracle`;
- `lower_bound_after_oracle`;
- `lower_bound_improvement_by_oracle`;
- `leaf_closed_by_oracle_bound`.

Focused interval or child evidence is never a full certificate by itself. The
frontier is certified only if every final leaf is closed or bound-fathomed and
the usual sealed full-frontier audit passes.
