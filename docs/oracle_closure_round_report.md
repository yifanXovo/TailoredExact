# Oracle Closure Round Report

This round corrected automatic interval-oracle budget semantics, added
recursive leaf partitioning, exposed BPC fallback results after oracle timeout,
and reran the sealed pipeline on V12 stability rows and priority V20/M3 rows.

Certified stability rows:

- V4 smoke;
- V12 M2 regenerated, objective `0.718504070755`;
- V12 M1 regenerated, objective `0.357200583208`;
- `high_imbalance_seed3202`, objective `1.74931345205`;
- `tight_T_seed3101`, objective `0.107252734134`.

Noncertified V20 rows:

- `moderate_seed3301`: 20 oracle solves, 4 root leaves closed, 2 root leaves
  remain open after depth-3 partitioning and 1800s child budgets.
- `tight_T_seed3102`: 9 oracle solves, all timed out; no abnormal exit in the
  controlled row.
- `high_imbalance_seed3201`: 6 oracle solves, all timed out.

Audit:

```text
results/oracle_closure_round/certificate_audit.csv
```

The audit covers certified and noncertified JSONs and reports zero failures.
No broad benchmark is recommended yet because V20/M3 remains at 2/6 certified
stress rows.
