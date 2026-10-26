# Existing infeasible-child path audit

The Round 46 C6 path is mathematically exact but is not operationally a
single-child contraction. It constructs and solves both midpoint child LP
models, calls `splitLeafAtomically` with two persistent children, increments
the binary split counter, then marks a strict-infeasible child empty and
discards its retained backend model. The feasible child model is already
available and retained. Therefore AMC requires a new atomic one-child
replacement with explicit infeasible-half certificate metadata; duplicate
no-op code is not appropriate.
