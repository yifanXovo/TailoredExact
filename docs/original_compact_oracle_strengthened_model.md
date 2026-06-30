# Strengthened Original Compact Interval Oracle

The strengthened oracle remains an original compact fixed-interval model.  It
adds only necessary conditions for incumbent-improving original solutions:

- fixed Gini interval rows `gamma_L <= G <= gamma_U`;
- optional objective cutoff row for the no-improver subproblem;
- Gini pairwise spread rows;
- penalty-budget final-inventory domain tightening;
- required net movement rows;
- aggregate handling capacity row;
- singleton route-duration compatibility rows;
- service-operation nonzero linking.

The objective-bound mode still minimizes `G + lambda * P`.  When the objective
cutoff row is active, timeout best bounds are merged using the cutoff
disjunction: solutions outside the cutoff row cannot improve the incumbent, so
`min(best_bound, cutoff)` is a valid no-improver lower bound for the full leaf.

Audit-visible fields added this round include:

- `gini_spread_cuts_added`;
- `required_movement_lb`;
- `required_movement_cuts_added`;
- `global_handling_capacity_lb`;
- `global_handling_capacity_cuts_added`;
- `transfer_subset_capacity_cuts_added`;
- `low_gini_ratio_band_domains_tightened`;
- `oracle_strengthening_families_enabled`;
- `oracle_strengthening_lb_improvement`.

The certificate audit accepts timeout-derived bounds only when
`interval_oracle_bound_valid=true`, the scope is `original_fixed_interval`, and
the model type is an accepted original compact interval oracle.
