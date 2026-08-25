# M1 symmetry re-audit protocol

Round 51 does not introduce a new symmetry formulation. It reuses exactly the two Round 50 representatives and compares each independently with the frozen `m1-tight-big-m-v0` baseline:

- `m1-s1-route-start-order` replaces the `M-1` v0 vehicle-cardinality ordering rows with the previously audited depot-start station-index ordering rows.
- `m1-s1r-used-first-route-start-order` makes the same `M-1` replacement with the previously audited used-first rank.

All three policies use the M1 subset-duration coefficients, default Gurobi branching, one thread, seed zero, automatic presolve, zero relative and absolute MIP gaps, identical state intervals, and identical verified cutoffs. There is no instance, size, `V`, panel, time, Work, node, memory, machine, or historical-result dispatch.

Before performance runs, both candidate LPs were parsed against M1-v0 for every D1-D14 and C1-C9 state. Each comparison has an identical objective, domains, row count, and non-symmetry row multiset; removes exactly the intended `M-1` v0 rows; adds exactly the intended `M-1` route-start rows; and preserves an optimal vehicle-label representative. The 46-row compact result is `symmetry_m1_model_correctness.csv`.

D13 (`high_imbalance_seed3201`, `V=20`) is mandatory. Its M1 and historical Round 50 models are byte-identical because the exhaustive subset-duration family is not generated for `V>12`. It is therefore the predeclared Big-M-unaffected negative control for determining whether the Round 50 symmetry regression reproduces. It may not be omitted or routed to another symmetry policy.

The frozen protocol is core screening at 120 seconds, followed only for a passing candidate by complete D1-D14 qualification at 300 seconds and C1-C9 confirmation at 1200 seconds. A lost certificate, false certificate, severe regression (including D13), failed model audit, or aggregate Work regression closes that candidate.

## Outcome

Both candidates passed the 120-second core screen and therefore received the complete 300-second D1-D14 qualification. Both reduced aggregate Work relative to M1-v0: S1 by 9.0% and S1-R1 by 4.5%. S1-R1 additionally certified D3 where M1-v0 capped.

Neither candidate passed the global gate. S1 lost baseline certificates on D12 and D13. S1-R1 retained D12 and gained D3, but lost D13 and had a separate severe capped regression on D14. D13's M1-v0 model is byte-identical to its Round 50 v0 model, M1-v0 certified it, and both route-start policies capped. The Round 50 symmetry regression therefore reproduces without Big-M confounding.

No confirmation panel was opened. The symmetry decision retains v0 cardinality ordering on the M1 experimental baseline; there is no accepted symmetry component and no symmetry+A1 interaction stage may open.
