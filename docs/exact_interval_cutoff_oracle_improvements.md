# Exact Interval Cutoff Oracle Improvements

The exact interval cutoff oracle asks whether an original compact MIP has a
feasible route-load solution inside a fixed Gini interval with objective below
the incumbent cutoff.  Proven infeasibility is a valid interval certificate
only after full-ledger coverage is checked.

This round added `--summary-out` to `scripts/run_interval_cutoff_oracles.py`,
so different instance-level oracle batches can write separate machine-readable
CSV files instead of overwriting one default summary.  The script remains
conservative: it never promotes a focused result to a full certificate.

Observed behavior:

- `high_imbalance_seed3201`: all five tested leaves timed out in the short
  30s oracle budget.
- `tight_T_seed3102`: all seven tested leaves timed out in the short 30s
  oracle budget.
- `moderate_seed3301`: nine leaves proved infeasible quickly, but the
  controlling interval `[0.0163841842216, 0.0327683684432]` timed out after
  600s.

The oracle is therefore useful for leaf pruning, but not yet a robust complete
V20 closure engine.  The next implementation target is model-size reduction or
valid warm starts for the remaining low-Gini moderate-case leaf.
