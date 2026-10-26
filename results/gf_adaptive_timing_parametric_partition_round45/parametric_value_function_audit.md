# Parametric value-function audit

- Live fallback query rows: 32
- Basis-sensitivity breakpoints: 0 (fallback path used)
- Point-certified live rows: 2
- Exact nonmidpoint coverage failures: 0
- Monotonicity failures: 0
- Empirical candidate-pool paths: 0

The query ledger records every bracket, probe, child value, and decision. The
segment ledger is a direct sampled value-function audit for the fallback path;
it is not evidence of a Gurobi basis continuation that did not occur.
