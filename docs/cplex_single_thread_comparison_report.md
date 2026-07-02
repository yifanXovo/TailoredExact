# Single-Thread CPLEX Comparison Report

Single-thread CPLEX benchmark rows were run with `--cplex-threads 1`. V12 M1 closes under plain CPLEX; V12 M2 and all compared V20 rows remain noncertified at 300s.

Compared with single-thread CPLEX, `paper-gf-compact-bc` certifies V12 M2 and tight_T_seed3101 and provides stronger V20 gaps in the bounded 300s rows. These CPLEX rows remain benchmark-only and do not contribute lower-bound evidence to compact-BC certificates.
