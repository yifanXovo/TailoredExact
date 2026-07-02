# Single-Thread CPLEX Comparison Round 2

Plain compact CPLEX benchmark rows were rerun with `--cplex-threads 1`.

Output:

- `results/gf_compact_bc_strengthening_round2/plain_cplex_single_thread_comparison.csv`
- `results/gf_compact_bc_strengthening_round2/exact_vs_cplex_single_thread_bound_quality.csv`

Benchmark result:

- CPLEX certified V12 M1 at 300s.
- CPLEX did not certify V12 M2 at 300s.
- CPLEX did not certify any V20/M3 row at 300s.
- CPLEX built V50 benchmark rows and one V100 benchmark row; all remained
  noncertified.

These rows are benchmark-only and are not imported into compact-BC certificate
evidence.

