# Validity of the M1 row-specific subset-duration Big-M

## Scope

M1 changes only the strengthened exhaustive subset-duration conditional rows generated when `V <= 12`. For every nonempty station subset `S`, the historical constant `100000` is replaced by

`M_S = max(0, tsp[S])`,

where `tsp[S]` is the deterministic subset tour lower bound already computed by the canonical compact-model writer. No instance value, depot sentinel, other Big-M, variable domain, objective coefficient, row sense, or non-target row is changed.

The implemented row is

`c sum_{i in S} p[k,i] <= T - tsp[S] + M_S (|S| - sum_{i in S} z[k,i])`.

Equivalently, in the writer's left-hand-side convention it is

`c sum_{i in S} p[k,i] + M_S sum_{i in S} z[k,i] <= T - tsp[S] + M_S |S|`.

## Assumptions inherited from the frozen formulation

1. Distances and travel duration are nonnegative.
2. Pickup handling time `c` and pickup quantities `p[k,i]` are nonnegative.
3. `z[k,i]` is binary in every integer feasible solution.
4. Existing pickup/visit linking rows force `p[k,i] = 0` when `z[k,i] = 0`.
5. The existing global vehicle-duration row contains all route travel and all pickup handling terms and has upper bound `T`.
6. `tsp[S]` is a valid lower bound on the depot-to-depot travel needed by a vehicle that visits every station in `S`.

The implementation rejects a nonfinite `tsp[S]` and rejects `tsp[S] < -1e-9`. A value in `[-1e-9,0)` is treated as numerical roundoff and mapped to zero, exactly as required by `max(0,tsp[S])`.

## Proof

Fix a vehicle `k`, a nonempty subset `S`, and an integer feasible solution. Define

`r = |S| - sum_{i in S} z[k,i]`.

Because the visit variables are binary, `r` is a nonnegative integer.

If `r = 0`, every station in `S` is visited. The conditional term vanishes and the M1 row becomes

`c sum_{i in S} p[k,i] <= T - tsp[S]`.

This is the intended subset-duration inequality: visiting all of `S` consumes at least `tsp[S]` nonnegative travel duration, leaving at most `T - tsp[S]` for pickup handling.

If `r >= 1`, at least one station of `S` is absent. The global vehicle-duration row and nonnegative travel imply

`c sum_{i in S} p[k,i] <= c sum_i p[k,i] <= T`.

For an accepted nonnegative bound, `M_S = tsp[S]`, and therefore

`T - tsp[S] + M_S r = T - tsp[S] + tsp[S] r >= T`.

Thus the right-hand side of the conditional row is at least `T`, while its pickup-handling left-hand side is at most `T`; the row is valid. If a tolerated roundoff value has `tsp[S] < 0`, then `M_S = 0` and `T - tsp[S] > T`, so the same conclusion holds.

The row is therefore valid in both exhaustive integer cases. M1 changes the LP relaxation but removes no integer-feasible solution and creates no new integer-feasible solution relative to the intended conditional-row logic.

## Code-level correspondence

`round51SubsetDurationRowValues` constructs the visit coefficient and RHS together and checks finiteness and the proved identity. The canonical writer uses both returned values for M1. Historical policies retain the literal `100000.0` path. Tests cover positive, zero, tolerated-negative, rejected-negative, infinite, and NaN bounds; exact coefficient/RHS construction; and both integer proof cases for subset cardinalities 1 through 12.
