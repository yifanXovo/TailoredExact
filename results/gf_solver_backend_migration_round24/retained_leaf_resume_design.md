# Retained-leaf resume design

`FixedIntervalMipBackend` separates the solver-neutral scheduler from native model state. The external controller reuses the existing `ControllingLeafScheduler`; it owns interval identity, priority, split decisions, inherited bounds, and global aggregation. A backend owns only a fixed-interval model and native calls.

For Gurobi `retained-per-leaf`, the first attempt creates and reads one model. A later selection of the same unchanged leaf calls optimize again on that exact object after changing only `TimeLimit`. It does not rebuild or reset. A continuation claim is accepted only when the model fingerprint still matches and cumulative Runtime, Work, or NodeCount does not decrease. Lifecycle and optimize ledgers distinguish `new_leaf`, `same_leaf_retained`, `fresh_restart`, `child_restart`, `reset_called`, and continuation evidence.

Splitting is categorically different. The parent is replaced atomically, both children receive only the proved parent LB, and each child gets a new native model and tree. No basis, cuts, incumbent pool, pseudocosts, node queue, or presolved parent tree is claimed to transfer. A verified complete MIP start may provide primal information to a new Gurobi child, but is not tree reuse.

CPLEX’s Round 24 external adapter deliberately creates a fresh callable-library environment/problem/read/optimize/free lifecycle for every attempt and makes no continuation claim. `fresh-per-attempt` exists only as a Gurobi diagnostic; official Gurobi cold and warm arms both freeze `retained-per-leaf`.
