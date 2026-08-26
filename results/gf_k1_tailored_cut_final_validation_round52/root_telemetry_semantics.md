# Root and LP telemetry semantics

The following quantities are distinct and must not be relabeled as each other:

- `plain_continuous_lp_optimum`: optimum after every integer/semi-integer
  variable in the canonical model is changed to continuous, solved as an LP.
- `initial_mip_root_relaxation_bound`: the first valid root-relaxation bound
  observed by the MIP engine before its root cutting loop is complete.
- `post_presolve_root_cut_bound`: the final valid root bound after presolve and
  the root cutting loop, before branching when such an event is available.
- `first_branching_bound`: the first valid best bound after the tree has opened
  beyond the root.
- `mip_best_bound`: general monotone MIP best-bound telemetry at an identified
  event/checkpoint; it is not assumed to be a plain-LP optimum.

Round 51 `root_relaxation_bound` is migrated to
`initial_mip_root_relaxation_bound`; `final_root_cut_bound` is migrated to
`post_presolve_root_cut_bound`. Neither is used as the new plain-LP value. The
paired audit reconstructs the exact hashed Round 51 canonical v0/M1 models,
relaxes all integer variables through the Gurobi model API, and solves with
identical Presolve=Auto, Seed=0, Threads=1, and Method=Auto settings.
