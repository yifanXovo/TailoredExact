# Tight T Seed 3102 Oracle and BPC Attempt

`tight_T_seed3102` previously had abnormal/interrupted behavior. The controlled
sealed run in this round exits normally with return code 0 and solver-final
JSON:

```text
results/oracle_closure_round/raw/tight_T_seed3102_controlled.json
```

Result:

| status | LB | UB | gap | unresolved | oracle attempted | oracle closed | oracle timed out |
|---|---:|---:|---:|---:|---:|---:|---:|
| not closed | 0.450176109171 | 0.600704436685 | 0.250586342169 | 3 | 9 | 0 | 9 |

All three final unresolved leaves were attempted by the oracle and split once.
All root and child oracle solves timed out with `interval_exact_cutoff_mip_timeout`.
BPC fallback attempted two leaves and closed none.

Detailed trace:

```text
results/oracle_closure_round/tight_T_seed3102_attempt_summary.csv
results/oracle_closure_round/tight_T_seed3102_leaf_oracle_trace.csv
```

Conclusion: the abnormal exit is fixed for the controlled row, but the row is
not certified. The exact blocker is oracle timeout on all three tight-T leaves
and no exact BPC pricing closure.
