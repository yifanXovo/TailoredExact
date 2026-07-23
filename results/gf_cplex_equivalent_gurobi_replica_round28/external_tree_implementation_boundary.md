# External-tree implementation boundary

C3 reproduces corrected S0 at the level of the complete improving Gini range,
recursive interval decomposition, tailored global/local strengthening,
complete LP lower bounds, pruning, unconditional eligible splits, exact
terminal interval subproblems, best-bound leaf selection, and global
certification.

The implementation boundary is deliberate:

- CPLEX embeds Gini branches inside one native CPLEX tree.
- C3 stores that structural tree in project code and reads a fresh immutable
  canonical model for each complete interval LP or terminal interval MIP.
- Gurobi bases, native cuts, pseudocosts, presolve state, ordinary node queues,
  and terminal B&B trees are not shared between events.
- Native node order, native cut trajectory, incumbent discovery order, and
  wall time are therefore not claimed equivalent.
- Static artifact reuse avoids rewriting an identical interval file between
  that leaf's LP and MIP. It is distinct from optimize-state reuse and cannot
  change a structural decision.

C3 never claims a Gurobi custom branch callback, native tree continuation, or
native event-sequence equivalence. Multiple optimize calls are expected and
are measured as a migration cost, not treated as a correctness defect.
