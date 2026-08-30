# Part 1 mechanism definitions

## Frozen K4

Four equal-width intervals cover the complete strict-improver Gini range. The unchanged C6 scheduler uses complete LP bounds, native next-frontier targets, `rho=0.01` child evidence, atomic parent/child replacement, and exact terminal closure.

## K1 single

One interval covers the complete strict-improver range. Its LP is completed and one exact terminal MIP closes it. No midpoint child lookahead or independent interval proof fragmentation occurs.

## K1 adaptive (initial hypothesis)

Start from the same complete root. Reuse the existing complete midpoint-child LP lookahead and `rho=0.01` split logic recursively. A declined refinement closes the coarser parent exactly.

## K1 adaptive decisive (trajectory-motivated revision)

Start from the complete root and solve both child LPs, but refine only when child infeasibility is proved or the child-disjunction lower bound already reaches the verified cutoff. Nondecisive gain closes the coarser parent exactly. This rule is deterministic, parameter-free, hardware-independent, and does not inspect identity, dimensions, seed, elapsed time, nodes, Work, or historical winners.
