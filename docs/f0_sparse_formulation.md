# F0-CLEAN sparse fixed-interval formulation

F0-CLEAN is the fixed-interval backend used by K1-AM-SF. It enforces the
original route, operation, inventory, duration, ratio, Gini, penalty, and
objective relations for a closed interval `[gamma_L,gamma_U]`, then adds only
the audited static families listed in `active_formulation_families.md`.

The defining sparsification is narrow: the historical exhaustive station-
subset duration block is off, including for V<=12. Pair and triple
support-duration covers remain active. No other F0 row-removal is implied by
the name.

Important interval-specific elements are the direct cap/floor rows, the exact
binary McCormick hull for G times each inventory-expansion bit, penalty and
reachability domains, incumbent/objective estimators, the W_SP McCormick
estimator, connectivity-flow extended variables, two deterministic propagation
rounds, and tight denominator bounds. These preserve every original feasible
solution in the interval.

The model is solved by Gurobi's native branch-and-cut. The stable policy adds
no root closure outside the solver and registers no dynamic user-cut callback.
The Round 54 inventory--route experiment builds a fresh model after exact
external root closure, but that experiment failed promotion and is not F0-CLEAN.
