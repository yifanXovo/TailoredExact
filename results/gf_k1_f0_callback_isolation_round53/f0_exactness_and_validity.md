# F0-CLEAN exactness and validity

## Definition

F0-CLEAN is the uniform policy `interval-mip-core-no-exhaustive-subset-duration`.
It omits only the historical exhaustive subset-duration strengthening block
written for `V <= 12`. It does not omit a core feasibility row, add a Round 52
static support-duration row, register a support-duration separator, or set
`PreCrush`. All variables, domains, bounds, interval restrictions, symmetry
rules, cutoff rows, and objective terms are inherited from production v0.

## Validity of a removed row

Fix a vehicle `k` and a nonempty station support `S`. Let `z_ki` be the binary
visit indicator, `p_ki` the nonnegative pickup quantity, `c` the per-unit
handling time, `T` the vehicle-duration limit, and `L(S)` a valid lower bound
on the depot-to-depot travel required to visit every station in `S`. The
historical row has the form

    c sum(i in S) p_ki + B sum(i in S) z_ki
        <= T - L(S) + B |S|,

or equivalently

    c sum(i in S) p_ki
        <= T - L(S) + B sum(i in S) (1 - z_ki).

The core formulation contains pickup/visit linking (`p_ki = 0` when
`z_ki = 0`), nonnegative travel and handling quantities, and the complete
vehicle-duration constraint. Consider an integer-feasible point.

If every station in `S` is visited, the final sum on the right is zero. The
route travel is at least `L(S)`, and the total pickup handling includes the
nonnegative handling on `S`. Subtracting this valid travel lower bound from
the core duration constraint gives

    c sum(i in S) p_ki <= T - L(S).

If at least one station in `S` is not visited, pickup/visit linking removes
its pickup. The core duration row gives `c sum(i in S) p_ki <= T`. The
historical coefficient `B = 100000` therefore makes the displayed row valid
whenever `B >= L(S)`; more generally the tight coefficient `B = L(S)` is
sufficient. Round 53 audits this dominance condition for every removed row
in every frozen state. A dominance failure would classify historical v0 as
unsafe for that state and fail the exactness gate; it is never silently
accepted.

Thus every audited removed row is a redundant inequality for integer-feasible
points. Removing redundant strengthening cannot remove an original feasible
integer point. It also cannot introduce a point infeasible for the original
EBRP, because every core routing, inventory, capacity, duration, interval,
cutoff, and domain constraint remains. The original integer feasible set and
the complete objective are unchanged. Only the continuous relaxation and the
solver's branch-and-bound trajectory can change.

## `V > 12`

Production v0 already skips the historical block when `V > 12`. F0-CLEAN
uses the same core writer with the block uniformly disabled, so the two
canonical LP artifacts must be byte-identical at these sizes. This is a
consequence of the historical writer guard, not an instance-size dispatch in
F0-CLEAN.

## Qualification obligations

The proof is accepted only together with the frozen-state model-delta audit,
the per-row `B >= L(S)` audit, small exact comparisons, and independent
verification of every reused incumbent. Any target mismatch, false
certificate, or incumbent verification failure rejects F0-CLEAN.
