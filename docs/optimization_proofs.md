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

## Third Optimization Pass: Range Coverage, Movement Audit, And Support Pruning

### Original Frontier Gini Range Coverage

For any feasible EBRP solution, `0 <= G <= (V-1)/V`. Given a verified incumbent with objective `UB`, no improving solution can have `G > UB`, because `lambda P >= 0` and the objective is `G + lambda P`. Therefore a full-frontier original certificate must cover at least:

```text
G in [0, min(UB, (V-1)/V)].
```

An explicit `--gini-cap gamma` with `gamma < min(UB, (V-1)/V)` covers only a capped diagnostic range unless the omitted Gini range is separately fathomed by a valid lower bound. The implementation records `gini_max_possible`, `relevant_gini_upper_for_improvement`, `covered_gini_upper_bound`, `frontier_covers_all_improving_gini_values`, and `frontier_range_certificate_scope`. BPC certification requires `frontier_range_certificate_scope=original_full_improving_range`.

### Movement-Bound Audit Selection

When `--movement-bound-audit true`, each audited interval computes one relaxation bound with movement-domain tightening disabled and one with it enabled. Both are valid lower bounds when they are derived from global station/truck/time necessary conditions. Their maximum is therefore also a valid lower bound. The ledger records `relaxation_lb_no_movement`, `relaxation_lb_with_movement`, `relaxation_lb_used`, and improvement/worsening counters.

### Support-Duration Pricing Pruning

For a station subset `S`, let `cycle_lb(S)` be the exact Held-Karp lower bound over metric-closure distances for a depot route visiting every station in `S`. Any feasible route-load column containing `S` has travel time at least `cycle_lb(S)`. A nonempty route-load column also has positive station operation quantity, so its duration is at least:

```text
cycle_lb(S) + pickup_time + drop_time.
```

If this exceeds `T`, no feasible route-load column can contain all stations in `S`. Pricing may therefore prune labels or route masks whose support contains such a subset. This is only an exact-pricing pruning rule; node closure still requires exact pricing completion with no remaining negative reduced-cost feasible column.

### Incumbent Pool Safety

BPC-owned incumbent generation uses priced columns only to propose feasible upper bounds. A candidate route-load column must have a populated operation vector before entering the incumbent route pool. The implementation now skips empty or undersized operation vectors before pool insertion/use. This removes malformed heuristic candidates only; it does not remove any lower-bound column from the RMP or pricing certificate.

### Relaxation Cache Budget Handling

The frontier relaxation cache key omits time budget and includes the instance, lambda, interval floor/cap, incumbent cutoff, route-mask setting, projection/penalty/movement/audit flags, and active restrictions. If a later request has a larger budget, the hit is marked partial and recomputed; the ledger keeps the stronger valid bound. Cache reuse changes runtime only, not the feasible region or certificate meaning.

## Fourth Optimization Pass: Strengthened Support Duration And Incumbents

### Ceil-Half Support-Duration Pruning

Let `S` be a station support subset for a single route-load column and let
`cycle_lb(S)` be a non-overestimating depot-cycle lower bound over metric-closure
distances. Under the certificate-producing model, every visited station in a
route-load column has a nonzero pickup or drop operation. One picked bicycle can
account for at most one pickup station and one drop station. Therefore a route
serving `|S|` nonzero-operation stations must pick up at least:

```text
ceil(|S| / 2)
```

bicycles. Since every picked bicycle is eventually either dropped at a station or
unloaded at the depot, its handling time contributes at least
`pickup_time + drop_time`. Thus every feasible column containing `S` has duration
at least:

```text
cycle_lb(S) + (pickup_time + drop_time) * ceil(|S| / 2).
```

If this lower bound exceeds the vehicle route-duration limit, no feasible
route-load column can contain `S`. Pricing may prune labels or candidate columns
whose support contains such a subset. The rule is exact only when `cycle_lb` is a
valid travel lower bound and zero-operation station visits have been removed or
forbidden by the station-operation cuts. Node closure still requires exact
pricing completion with no missing negative reduced-cost feasible column.

### Route-Mask Support-Duration Relaxation Pruning

The same ceil-half support-duration lower bound can be applied before building a
complete route-mask relaxation. For vehicle `k`, a route-mask variable for mask
`M` is removed if:

```text
cycle_lb(M) + (pickup_time + drop_time) * ceil(|M| / 2) > T_k.
```

Any original route-load column with exactly mask `M` would violate the same
necessary duration lower bound, so removing that mask from the relaxation removes
no feasible original route-load plan. When vehicle capacities or time limits
differ, the filter is vehicle-specific. The filter strengthens only the
inventory/route/Gini lower-bound relaxation; it does not replace the full
branch-price interval certificate.

### Verified Incumbent Seeding

Imported route JSON/CSV solutions, compact-generated seeds, and compact-CPLEX
seeds are used only after the independent verifier recomputes route duration,
load feasibility, station capacity, final inventories, `G`, `P`, and objective.
A verified seed supplies an upper bound and may tighten incumbent cutoffs and
domain bounds. It never contributes lower-bound evidence. A run seeded by compact
or CPLEX output must be labeled as seeded or hybrid; it is not pure BPC
performance even though the lower-bound machinery remains BPC.

### Focused Min-LB Frontier Retry

Focused retry changes only runtime allocation. After an initial frontier pass, it
selects unresolved relevant intervals by increasing valid interval lower bound,
then retries the current global-minimum interval until it closes, is
bound-fathomed, improves above the next unresolved bound, makes no valid
lower-bound progress, or hits the time limit. The final frontier ledger still
contains every relevant interval. Therefore focused retry is certificate-neutral:
it can improve the global lower-bound ledger faster, but cannot certify unless
the usual full-frontier closure conditions hold.

### Exact Support-Feasibility Oracle Status

The `--support-feasibility-oracle` switch is currently present for controlled
experiments, but no heuristic support infeasibility cut is enabled by default.
Future support cuts may be added only when an exact one-vehicle route-load oracle
proves that no route order and integer operation vector can realize the support.
Timeouts or sampled failures are not infeasibility proofs.

## Fifth Optimization Pass: Focused Retry, Route-Pool Incumbents, And Compatibility Flow

### Executed Focused Min-LB Retry

Focused retry is certificate-neutral because it only reallocates remaining time
among already represented frontier intervals. The retry queue is ordered by
valid interval lower bound, then by incumbent gap, open-node count, and interval
id. Retrying an interval can update its branch-price lower bound, open-node
count, incumbent routes, or fathoming status, but it does not remove any other
relevant interval from the final ledger. The global lower bound is still the
minimum valid interval bound over the relevant frontier. A positive-gap run
remains noncertified even if focused retry executes.

### Route-Column Pool Incumbent Master

The frontier route-column pool stores only independently feasible route-load
columns and applies projection dominance by vehicle, station mask, and signed
operation vector before insertion. The true-objective restricted master selects
at most one stored column per vehicle, enforces station-disjointness, recomputes
final inventories, and evaluates `G + lambda P`. For `V <= 16`, the implemented
fallback is an exact DFS over vehicles and station masks for the restricted
pool. Any selected route set is passed through the independent verifier before
it can update the incumbent.

This master is a primal heuristic only. Optimizing over a subset of feasible
columns can produce a valid upper bound, but failure to improve cannot prove a
lower bound. Therefore route-pool results may tighten incumbent cutoffs but do
not close a BPC node or a frontier interval.

### Interval Candidate True-Objective Audit

A branch-price interval may report a surrogate integer metric, such as a
fixed-cap value or an interval lower-bound objective. That metric is not
necessarily the original objective. Every reconstructed route candidate is
therefore independently verified and evaluated under the original
`G + lambda P` objective before acceptance. A feasible candidate that improves
the current verified upper bound is accepted even if its surrogate came from a
different interval metric. Rejections are logged as verifier failure,
non-improving true objective, feasible but outside the interval, duplicate
incumbent, or unknown reason.

### Pickup-Drop Compatibility Flow Relaxation

Let `p_i` be pickup at station `i`, `d_j` be drop at station `j`, `f_ij >= 0`
be continuous transfer from pickup `i` to downstream drop `j`, and `h_i >= 0`
be bikes picked at `i` and unloaded at the depot. Any feasible route-load
solution induces:

```text
p_i = sum_j f_ij + h_i
d_j = sum_i f_ij
```

If station `j` receives a bike picked at `i`, some vehicle route must be able
to visit `i` before `j` within the route-duration limit. The implementation
declares a pair incompatible only when the directed metric-closure lower bound

```text
d(0,i) + d(i,j) + d(j,0) + pickup_time + drop_time > T_k
```

for every vehicle `k`. Pairs that cannot be proven impossible remain compatible.
For compatible pairs, `f_ij` is bounded by station pickup/drop capacity. These
constraints are necessary for every feasible route-load solution and can only
strengthen the inventory/route/Gini relaxation. They are not a certificate by
themselves; full frontier closure and exact pricing are still required.

