# Canonical compact-model schema

`CanonicalCompactModel` is the sole Round 24 model source. It exposes the existing deterministic compact LP writer rather than duplicating the mathematics in a Gurobi-specific builder. P-CPX and P-GRB read the same plain LP artifact. External CPLEX and Gurobi receive the same static fixed-interval artifact generated from the same writer, interval factory, F0 selection, verified cutoff, and interval endpoints.

The model contains route-arc binaries `x`, visit/mode binaries, pickup/drop/load and final-inventory general integers, continuous Gini/deviation/linearization auxiliaries, and the objective `G + lambda * weighted_deviation`. Plain artifacts contain no interval or HGA cutoff. Tailored external artifacts add F0 connectivity-flow columns/rows, the verified improving-objective cutoff, and static interval bounds/rows.

Determinism is bound by SHA-256 over the exact LP bytes. Byte equality therefore audits objective coefficients, names, domains, bounds, row order, senses, RHS values, and coefficients simultaneously. The toy plain artifact has 77 rows, 44 columns, 217 matrix nonzeros, 18 binaries, 8 general integers, and 18 continuous variables. The V12_M1 plain artifact has 992 rows, 489 columns, 3,867 matrix nonzeros, 253 binaries, 48 general integers, and 188 continuous variables. Its F0 static interval artifact has 5,865 rows, 645 columns, 56,154 matrix nonzeros, 253 binaries, 48 general integers, 344 continuous variables, and 156 `conn_*` F0 columns.

The native Gurobi model attribute audit remains unavailable: Gurobi error 10009 occurs while creating the environment, before a model can be read. This is a Stage 0 failure, not an inferred pass.
