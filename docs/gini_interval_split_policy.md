# Gini Interval Split Policy

The paper-facing Tailored-BC algorithm may split Gini intervals only when the child intervals exactly cover the parent interval.

For a parent interval `[gamma_L, gamma_U]`, a split point `m` is valid only if:

```text
gamma_L <= m <= gamma_U
[gamma_L, gamma_U] = [gamma_L, m] union [m, gamma_U]
```

The full-frontier ledger may close the parent only when every child interval in the coverage is closed by a valid source:

- valid relaxation/frontier lower bound;
- fixed-interval Tailored-BC infeasibility proof;
- fixed-interval Tailored-BC best-bound proof that reaches the cutoff;
- audited empty/out-of-range proof.

Checkpoint best-bound trajectories from callback workers are diagnostic lower-bound progress unless an audited merge rule explicitly accepts their scope. Plain CPLEX benchmark rows, BPC diagnostics, route-mask enumeration, archive scanning, known UB injection, and diagnostic transfer/Benders rows are never Gini interval closure sources.

Current implementation status:

- Callback one-shot Gini branching is diagnostic guidance inside CPLEX node search.
- Outer Gini-frontier interval splitting remains the certificate ledger mechanism.
- Future split heuristics should prefer intervals with the smallest gap to cutoff, low-Gini denominator weakness, or valid checkpoint-bound progress that appears near closure.
