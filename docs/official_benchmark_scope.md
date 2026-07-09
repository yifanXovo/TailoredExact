# Official Benchmark Scope

The official benchmark remains the current binary-expansion compact MILP solved by CPLEX.
It is labelled `tolerance_exact` with bit-depth / linearization precision metadata.
Alternative exact-S formulations are audited diagnostics and are not enabled as the official benchmark in this round.
Approximate SOS2, piecewise, Charnes-Cooper, Dinkelbach, and nonconvex MIQCP variants are excluded from official exact benchmarking.
Plain CPLEX benchmark rows are benchmark-only and must never enter the Tailored-BC ledger.
