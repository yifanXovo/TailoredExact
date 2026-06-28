# Exact Interval Cutoff MIP Oracle

The interval cutoff oracle is exposed as:

```powershell
build\ExactEBRP.exe --method interval-cutoff-oracle `
  --input <instance> --lambda 0.15 --T 3600 `
  --interval-exact-cutoff-oracle compact-mip `
  --interval-exact-cutoff-gamma-L <L> `
  --interval-exact-cutoff-gamma-U <U> `
  --interval-exact-cutoff-UB <incumbent> `
  --interval-exact-cutoff-time-limit <seconds>
```

It builds the compact original-route MIP with route flow, station disjointness,
integer pickup/drop quantities, truck load propagation, station capacities,
route duration, nonzero served-station operations, depot unload convention, and
the project Gini/penalty objective convention.  The oracle adds the fixed Gini
interval and incumbent cutoff:

- `gamma_L <= G <= gamma_U`
- `G + lambda P <= incumbent_UB - epsilon`

If CPLEX proves this compact cutoff model infeasible, the interval is a valid
no-improver interval for the full-frontier ledger.  If CPLEX finds a feasible
solution, the reconstructed route plan must pass the independent verifier
before it can be accepted as an upper-bound improvement.  If CPLEX times out,
the interval remains unresolved.

The oracle is interval-local evidence. It is never a full original-problem
certificate unless a separate ledger merge proves exact full-frontier coverage.

