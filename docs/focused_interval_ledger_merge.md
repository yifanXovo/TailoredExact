# Focused Interval Ledger Merge

Focused interval evidence can be merged only when it exactly matches a final
unresolved full-frontier leaf, or when a set of focused intervals partitions a
leaf without gaps or overlaps.  The merge script used in this round is:

```powershell
D:\msys64\ucrt64\bin\python.exe scripts\merge_interval_oracle_results.py `
  --ledger <full-frontier intervals.csv> `
  --oracle-results <interval oracle csv> `
  --merged-ledger <merged csv> `
  --audit <merge audit csv>
```

Only `interval_exact_cutoff_mip_infeasible` with a CPLEX solver status proving
infeasibility is merged as `bound_fathomed`. Timeouts, feasible relaxed MIP
solutions, unverified route reconstructions, and narrower focused intervals
without complete sibling coverage remain diagnostic and cannot certify the
original problem.

