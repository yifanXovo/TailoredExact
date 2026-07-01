# Strengthened Original Compact Interval BC Model

The interval-local compact solver is now used by the `paper-gf-compact-bc`
preset as a compact branch-and-cut/cutoff subsolver.  The legacy
`interval_oracle_*` JSON fields remain for compatibility, but paper-facing
summaries should use the `compact_interval_bc_*` and `compact_bc_*` fields.

The strengthened compact model remains an original fixed-Gini-interval model.
It adds only necessary conditions for incumbent-improving original solutions:

- fixed Gini interval rows `gamma_L <= G <= gamma_U`;
- direct interval Gini rows `H <= V*gamma_U*S` and `H >= V*gamma_L*S`;
- optional objective cutoff row for the no-improver subproblem;
- interval-tight McCormick rows for every product `G*bit`;
- total station-inventory conservation bounds;
- movement-reachability final-inventory domains;
- visit/final-inventory linking rows;
- objective lower-estimator cutoff row;
- penalty lower-bound closure row;
- Gini pairwise spread rows;
- penalty-budget final-inventory domain tightening;
- required net movement rows;
- aggregate handling capacity row, using pickup-only handling under the current
  duration convention;
- singleton route-duration compatibility rows;
- pair/triple route-duration support cuts, subject to the row-count guard;
- pairwise pickup/drop transfer compatibility rows under the empty-start,
  one-mode-per-station convention;
- service-operation nonzero linking.

The verifier and compact model currently use
`travel + (pickup_time + drop_time) * pickup_quantity <= T`.  Under this
convention the aggregate handling row is
`cunit * sum p[k,i] <= M*T`; the old `cunit * sum(p+d)` row is excluded from
paper-core evidence.

The objective-bound mode still minimizes `G + lambda * P`.  When the objective
cutoff row is active, timeout best bounds are merged using the cutoff
disjunction: solutions outside the cutoff row cannot improve the incumbent, so
`min(best_bound, cutoff)` is a valid no-improver lower bound for the full leaf.

Audit-visible fields added this round include:

- `compact_interval_bc_enabled`;
- `compact_interval_bc_model_type`;
- `compact_interval_bc_solver`;
- `compact_interval_bc_threads`;
- `compact_interval_bc_cut_families_enabled`;
- `compact_interval_bc_bound_valid`;
- `compact_interval_bc_bound_scope`;
- `compact_bc_cuts_added_by_family`;
- `compact_bc_domains_tightened_by_family`;
- `gini_spread_cuts_added`;
- `compact_bc_direct_gini_cap_rows_added`;
- `compact_bc_tight_mccormick_rows_added`;
- `compact_bc_inventory_conservation_rows_added`;
- `compact_bc_movement_reachability_domains_tightened`;
- `compact_bc_visit_inventory_linking_rows_added`;
- `compact_bc_objective_estimator_cutoff_rows_added`;
- `compact_bc_penalty_lb`;
- `compact_bc_support_duration_pair_cuts_added`;
- `compact_bc_support_duration_triple_cuts_added`;
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
