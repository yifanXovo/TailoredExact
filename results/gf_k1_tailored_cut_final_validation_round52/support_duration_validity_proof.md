# Validity of the support-duration family

Fix a vehicle `k` and a station support `S`, with `2 <= |S| <= q`. Let `z[k,i]` be the visit indicator, `p[k,i]` the handled pickup quantity, `c` the per-unit handling duration used by the canonical model, `T` the route horizon, and `tau(S)` any valid lower bound on depot-to-depot travel for a route visiting every station in `S`.

The proposed inequality is

`c sum(i in S) p[k,i] <= T - tau(S) + tau(S)(|S| - sum(i in S) z[k,i]).`

If every station in `S` is visited, all its indicators equal one. Any feasible vehicle route serving those stations spends at least `tau(S)` in travel, so its handling time is at most `T - tau(S)`. The inequality is therefore valid.

If at least one station in `S` is not visited, visit/pickup linking gives zero pickup at each unvisited station. The remaining handling appearing on the left is at most the complete route's total handling, hence at most `T`. Meanwhile `|S| - sum z[k,i] >= 1`, so the right side is at least `T`. The inequality is again valid. These cases exhaust all integral solutions. Because every base-model integer feasible point satisfies the row, it is a globally valid user cut and may be added to an LP relaxation through `GRBcbcut`.

For ranks two through four, Round 52 computes `tau(S)` by enumerating every permutation of `S`, adding depot-to-first, consecutive, and last-to-depot distances, and taking the minimum. This is the exact shortest depot tour over the support under the instance distance matrix, and therefore a valid lower bound independent of the order in which the support was supplied.

At an LP point, moving the visit terms to the left yields coefficients `c` on each pickup and `tau(S)` on each visit, with RHS `T - tau(S) + tau(S)|S|`. The implementation evaluates exactly the corresponding raw violation. It sets the scale to the maximum of one, the absolute RHS, and the coefficient-weighted point magnitude. A candidate passes only under the strict frozen test `violation > epsilon_cert * scale`; no empirical threshold is used.
