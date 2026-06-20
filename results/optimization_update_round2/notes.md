# Optimization Update Round 2 Notes

Implemented:

- Frontier lower-bound ledger for incomplete `gcap-frontier` runs.
- Duplicate-negative pricing closure safeguard.
- Clarified dominance statistics.
- Movement-reachable final-inventory domain tightening.
- Deterministic best-bound initial frontier scheduling.
- Exact-key interval relaxation cache for sequential frontier passes.
- `dominance-test` diagnostic.

Local input availability:

- Present: `testdata/examples/gcap_smoke_V4_M1.txt`.
- Present: `reference/regen_candidate_V12_M1_average.txt`.
- Present: `reference/regen_candidate_V12_M2_average.txt`.
- Missing locally: V8 M2 average, V10 M2 average, V10 M1 average, V10 M2 low source text files.

Test outcome:

- V4 smoke `gcap-frontier` remained certified with objective/LB/UB `0`.
- V12 M1/M2 average 60s stress rows remained noncertified.
- Incomplete V12 rows now expose valid top-level frontier lower bounds from the interval ledger.
- Plain CPLEX benchmark rows were skipped in this pass. The inventory/route/Gini relaxation did call CPLEX internally where available.

Limitations:

- The relaxation cache is disabled automatically for parallel frontier execution in this pass to avoid shared-state synchronization risk.
- No HGA/TGBC incumbent bridge was implemented.
- No route-support infeasibility cuts were implemented.
- No frontier column cache was enabled.
