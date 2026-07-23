# C4 split strategy

C4 uses only complete mathematical relaxation information. For parent
interval `I` with complete LP lower bound `b(I)`, an eligible midpoint creates
the exact cover `I0 union I1 = I`. Both child LPs are optimized to a supported
terminal status.

The atomic split predicate is:

`child_infeasible OR min_feasible_child_bound > b(I) + 1e-7`.

If true, the parent is replaced atomically by the two complete children;
infeasible children are immediately marked empty. If false, neither
speculative child enters coverage and the exact unsplit parent MIP is solved.
Thus declining a split never removes a feasible solution.

The decision does not use elapsed time, hardware speed, Gurobi Work, native
nodes, solution count, attempts, retries, instance name, family, seed, `V`,
`M`, path, known objective, or prior benchmark results. The experiment
deadline may interrupt the complete algorithm but cannot change this
predicate.
