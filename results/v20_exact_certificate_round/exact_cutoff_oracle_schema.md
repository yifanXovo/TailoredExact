# Exact Cutoff Oracle Result Schema

Each `interval-cutoff-oracle` JSON row includes:

- `interval_exact_cutoff_oracle`
- `interval_exact_cutoff_attempted`
- `interval_exact_cutoff_gamma_L`
- `interval_exact_cutoff_gamma_U`
- `interval_exact_cutoff_UB`
- `interval_exact_cutoff_epsilon`
- `interval_exact_cutoff_solver_status`
- `interval_exact_cutoff_certificate_basis`
- `interval_exact_cutoff_proven_infeasible`
- `interval_exact_cutoff_feasible_improving`
- `interval_exact_cutoff_timeout`
- `interval_exact_cutoff_best_bound`
- `interval_exact_cutoff_objective`
- `interval_exact_cutoff_lp_path`
- `interval_exact_cutoff_solution_path`
- `interval_exact_cutoff_log_path`
- `interval_exact_cutoff_scope`

Only proven infeasibility on an exactly matched full-frontier leaf is mergeable.

