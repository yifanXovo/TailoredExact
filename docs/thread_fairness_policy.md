# Thread Fairness Policy

Controlled compact-BC comparisons use one solver thread unless the row is
explicitly labelled diagnostic.

Required fields:

- `cplex_threads`
- `mip_threads`
- `compact_bc_solver_threads`
- `solver_thread_policy`
- `thread_fairness_class`

For paper-gf-compact-bc controlled rows, `compact_bc_solver_threads=1` and
`thread_fairness_class=one_thread_fair` are required. Plain CPLEX comparison
rows are benchmark-only and must use `cplex_threads=1` for the controlled table.
Multi-thread rows may be kept only as `multithread_diagnostic`.

Round 2 audit output:
`results/gf_compact_bc_strengthening_round2/thread_fairness_audit.csv`.

