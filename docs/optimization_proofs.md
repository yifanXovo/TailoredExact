# Optimization Proofs

Date: 2026-06-20.

This note documents exactness-preserving optimizations added to the route-load BPC implementation. These optimizations may reduce column pools or strengthen lower-bound preprocessing, but they do not change the original EBRP objective or relax the certificate protocol.

## Closed-Column Projection Dominance

Let `c` and `c'` be feasible route-load columns for the same vehicle. If they have the same station mask `A_c=A_c'` and the same signed operation vector `q_c=q_c'`, then every master row whose coefficient depends only on vehicle identity, station membership, signed inventory change, Ryan-Foster membership rows, subset-row cuts, and station-operation projections has identical coefficients for `c` and `c'`.

The two columns induce the same final inventories in every selected column combination. Therefore they induce the same ratios `r_i`, penalty `P`, Gini numerator `H`, denominator `S`, and Gini value `G`.

If the active master objective has no path-dependent coefficient, replacing one projection-equivalent column by the representative with smaller duration, then smaller travel, then lexicographically smaller path preserves feasibility and objective value. If path-dependent terms exist, only columns dominated in every relevant path-dependent dimension may be removed; otherwise the Pareto frontier over duration, travel, and reduced/objective coefficient is retained.

This is implemented by `ColumnPool` and controlled by `--column-dominance` and `--column-dominance-mode`.

## Inventory-Ratio Interval Projection Lower Bound

For each station, suppose every feasible completion of a BPC node or Gini interval satisfies final inventory

```text
Y_i in [L_i, U_i].
```

Then the ratio lies in

```text
R_i = [L_i / target_i, U_i / target_i].
```

The deviation term satisfies

```text
|r_i - 1| >= dist(1, R_i),
```

so `P >= sum_i w_i dist(1,R_i)`.

Likewise, for each pair,

```text
|r_i - r_j| >= dist(R_i, R_j),
```

so `H >= sum_{i<j} dist(R_i,R_j)`. With `S_UB=sum_i U_i/target_i > 0`, any feasible solution has `S <= S_UB`, therefore

```text
G = H / (V S) >= H_LB / (V S_UB).
```

Thus

```text
G + lambda P >= G_LB + lambda P_LB.
```

If the active interval has floor `gamma_L`, then `G >= gamma_L`, and both `gamma_L` and `gamma_L + lambda P_LB` are valid lower bounds. The implementation takes the maximum of these valid bounds.

This bound is global only when the inventory intervals come from globally valid necessary conditions such as station capacity, final-inventory branching, incumbent-improvement penalty budget, route-mask relaxation, or an exact selected-column prefix. It must not be used as an original-problem certificate when the intervals come only from an incomplete restricted column pool.

## Incumbent Penalty-Budget Domain Tightening

In an interval with floor `gamma_L`, any solution that improves incumbent upper bound `UB` must satisfy

```text
gamma_L + lambda P(Y) <= UB.
```

If `lambda>0`, then

```text
P(Y) <= B = (UB - gamma_L) / lambda.
```

Each term `w_i |Y_i/target_i - 1|` is nonnegative, so for `w_i>0` it must individually satisfy

```text
w_i |Y_i/target_i - 1| <= B.
```

Therefore every incumbent-improving completion has

```text
Y_i / target_i in [1 - B/w_i, 1 + B/w_i].
```

Intersecting the integer final-inventory domain with this range is valid when proving that no solution can improve `UB`. If `B<0`, the interval cannot contain an incumbent-improving solution and may be bound-fathomed at `UB`; it is not reported as unconditionally empty unless infeasibility is proven without the cutoff.

## Filtered Multi-Column Pricing

When exact pricing returns multiple negative route-load columns, filtering those columns through closed-column projection dominance is certificate-neutral. Projection-equivalent dominated columns do not change the restricted master projection, and Pareto filtering preserves all columns that can be better under path-dependent objective terms.

Early negative stopping may be used only to add columns and continue column generation. A BPC node is closed only after exact pricing completes under the current duals and proves that no negative reduced-cost route-load column remains.

## Frontier Column Cache

A frontier cache may reuse independently verified feasible route-load columns across Gini intervals or retry passes when branch restrictions are compatible. Reused columns only enlarge the restricted master. They do not replace exact pricing closure under the current node duals.

The current implementation exposes `--frontier-column-cache` and logs a request, but leaves the cache disabled pending a separate stability pass.

## Imported Incumbents

Imported route solutions, including future HGA/TGBC bridge outputs, are safe only after the independent verifier recomputes route feasibility, load feasibility, station capacity feasibility, route duration, final inventories, `G`, `P`, and `G + lambda P`. A verified incumbent provides only an upper bound and never supplies a lower-bound certificate.

