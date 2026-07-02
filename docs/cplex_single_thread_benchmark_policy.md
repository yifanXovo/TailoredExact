# CPLEX Single-Thread Benchmark Policy

Controlled compact-BC comparisons use one CPLEX thread for both plain compact CPLEX benchmark rows and the compact interval BC subsolver. Plain benchmark rows must pass `--cplex-threads 1`; paper compact-BC rows must pass `--compact-bc-threads 1` (and `--mip-threads 1` for compatibility).

JSON fields used for audit are `cplex_threads`, `mip_threads`, `compact_bc_solver_threads`, `solver_thread_policy`, and `thread_fairness_class`. Rows with `thread_fairness_class != one_thread_fair` are diagnostic only for this round.

Plain CPLEX rows are benchmark-only. Their incumbents and bounds are never imported into `paper-gf-compact-bc` certificate evidence.
