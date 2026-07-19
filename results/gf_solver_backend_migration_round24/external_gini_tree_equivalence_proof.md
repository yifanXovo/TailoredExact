# External global-Gini-tree equivalence proof

Let the improving Gini range be the closed root interval `[L,U]`. The controller creates deterministic initial intervals with exact union `[L,U]`. A split replaces one parent `[a,b]` atomically by `[a,m]` and `[m,b]`, using the shared endpoint convention in `GiniFrontierGeometry`; their union is the parent and neither child exists as authoritative state before both are constructed.

Each leaf model is the complete compact F0 MILP plus the shared static interval/cutoff row pack. Thus its feasible set is exactly the original feasible set restricted to that leaf’s Gini interval and improving cutoff. CPLEX and Gurobi adapters consume the same canonical LP bytes. No solver-specific objective or pruning row is added.

Every child inherits the parent’s valid lower bound because its feasible set is a subset of the parent’s. A native leaf bound replaces that value only when it is finite, lifecycle-valid, model-fingerprint-consistent, and returned under exact-zero gap parameter semantics. Incumbents and MIP starts are never lower bounds. The controller’s global lower bound is the minimum over all relevant frontier leaves; atomic replacement and `max(inherited,native)` leaf updates make both leaf and global sequences monotone.

Global strict optimality requires exact root/child coverage, every relevant leaf closed or validly bound-fathomed, all bounds/lifecycles valid, an independently verified global incumbent, feasibility-consistency, and global LB equal to verified UB under the engineering equality rule. Closing one leaf is insufficient.

The 80-check Round24 backend suite exercises coverage, atomic replacement, inheritance, monotonicity, the one-leaf non-certificate case, exhaustive toy agreement, lifecycle, resume, warm-start, SHA-256, and fail-closed adapters. The CPLEX F0 smoke independently reports valid coverage, bound monotonicity, and lifecycle, while correctly rejecting strict certification because one leaf remains open.
