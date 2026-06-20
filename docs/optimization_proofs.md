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

## Frontier Lower-Bound Ledger For Incomplete Runs

For a disjoint Gini-frontier partition, every feasible solution belongs to one relevant interval. If each interval `I` has a valid lower bound `LB_I`, then the global lower bound over the covered range is:

```text
LB_global = min_I LB_I.
```

If an interval is not yet solved, its floor `gamma_L` is still a valid lower bound because every solution in the interval has `G >= gamma_L` and `G + lambda P >= gamma_L`. Bound-fathomed intervals keep their valid relaxation or cutoff lower bound, and skipped intervals with `gamma_L >= incumbent` are irrelevant for improving the incumbent.

This ledger is a progress metric, not an optimality certificate. The original problem is certified only when every relevant interval is closed, empty, or bound-fathomed and the minimum interval lower bound reaches the verified incumbent objective.

## Duplicate Negative Pricing Closure Safety

If exact pricing finds a negative reduced-cost route-load column, the current RMP is not proven closed unless that negative projection is already fully represented and no other missing negative projection exists. A returned negative column that is already present or dominance-filtered cannot by itself certify closure. The implementation therefore leaves the node unresolved when all returned negative columns are duplicate/dominated, unless exact pricing proves no missing negative projection remains.

Early negative stopping may add columns and continue column generation, but node closure requires exact pricing completion with no remaining negative reduced-cost column over the full feasible route-load set.

## Movement-Reachable Inventory-Domain Tightening

For station `i` and vehicle `k`, define:

```text
rt_lb_ki = shortest_path(0,i) + shortest_path(i,0)
move_budget_ki = floor((T - rt_lb_ki) / (tau_pick + tau_drop)).
```

If `T < rt_lb_ki`, then `move_budget_ki=0`. A feasible route that changes station `i` must visit `i`; its travel time is at least `rt_lb_ki`. Moving `p` bikes by pickup or `d` bikes by drop also requires at least `(tau_pick+tau_drop)` handling time per moved bike, since picked bikes are eventually dropped or unloaded and dropped bikes must have been picked earlier. The movement is also bounded by truck capacity, station initial inventory for pickup, and station residual capacity for drop:

```text
pickup_reach_i = max_k min(initial_i, Q_k, move_budget_ki)
drop_reach_i   = max_k min(capacity_i - initial_i, Q_k, move_budget_ki).
```

Therefore every feasible final inventory satisfies:

```text
initial_i - pickup_reach_i <= Y_i <= initial_i + drop_reach_i.
```

Intersecting this interval with station capacity and active branch/domain bounds removes no feasible original solution. The bound uses directed metric-closure distances when available and is global because it uses only necessary route-duration, handling-time, station-capacity, and truck-capacity conditions.

## Best-Bound Scheduling And Relaxation Cache

Best-bound frontier scheduling changes only the order in which independent Gini intervals are processed. It does not remove intervals from the final ledger, so exactness is unchanged.

The relaxation cache is certificate-neutral because a cached bound is reused only under an exact key containing the instance, interval floor/cap, cutoff, lambda, route-mask threshold, and domain-tightening flags. Under the same key, the deterministic relaxation has the same feasible region and lower-bound interpretation. Reused relaxation bounds never replace branch-price exact pricing closure.

## Dominance Statistic Semantics

The reporting fields now separate enumeration, filtering, and insertion:

- `pricing_columns_enumerated`: columns enumerated by pricing or exact route search.
- `dominance_input_columns`: candidate columns passed to a dominance filter.
- `dominance_kept_columns`: candidates retained by that filter.
- `dominance_removed_candidate_projection`: candidates removed by another candidate with the same projection.
- `dominance_removed_existing_projection`: candidates removed because the RMP already contained the projection.
- `rmp_columns_inserted`: filtered candidates actually inserted into the RMP.
- `rmp_columns_active`: active RMP columns after filtering.

The backward-compatible `columns_generated_raw`, `columns_after_dominance`, and `columns_dominated` fields remain, but the more specific counters should be used for paper ablations.

