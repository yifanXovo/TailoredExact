# M1 symmetry re-audit protocol

Round 51 does not introduce a new symmetry formulation. It reuses exactly the two Round 50 representatives and compares each independently with the frozen `m1-tight-big-m-v0` baseline:

- `m1-s1-route-start-order` replaces the `M-1` v0 vehicle-cardinality ordering rows with the previously audited depot-start station-index ordering rows.
- `m1-s1r-used-first-route-start-order` makes the same `M-1` replacement with the previously audited used-first rank.

All three policies use the M1 subset-duration coefficients, default Gurobi branching, one thread, seed zero, automatic presolve, zero relative and absolute MIP gaps, identical state intervals, and identical verified cutoffs. There is no instance, size, `V`, panel, time, Work, node, memory, machine, or historical-result dispatch.

Before performance runs, both candidate LPs were parsed against M1-v0 for every D1-D14 and C1-C9 state. Each comparison has an identical objective, domains, row count, and non-symmetry row multiset; removes exactly the intended `M-1` v0 rows; adds exactly the intended `M-1` route-start rows; and preserves an optimal vehicle-label representative. The 46-row compact result is `symmetry_m1_model_correctness.csv`.

D13 (`high_imbalance_seed3201`, `V=20`) is mandatory. Its M1 and historical Round 50 models are byte-identical because the exhaustive subset-duration family is not generated for `V>12`. It is therefore the predeclared Big-M-unaffected negative control for determining whether the Round 50 symmetry regression reproduces. It may not be omitted or routed to another symmetry policy.

The frozen protocol is core screening at 120 seconds, followed only for a passing candidate by complete D1-D14 qualification at 300 seconds and C1-C9 confirmation at 1200 seconds. A lost certificate, false certificate, severe regression (including D13), failed model audit, or aggregate Work regression closes that candidate.
