# Implementation-Proof Consistency Audit

Date: 2026-06-12.

Scope: `src/Bounds.cpp`, especially `computeGiniIntervalInventoryRelaxationBound`, compared with `docs/route_mask_bound_proof.md`.

## Route-Mask Rows

The implementation matches the proof statement for instances where complete route masks are enabled:

```cpp
route_mask_relaxation =
    integer_inventory_relaxation &&
    instance.V <= route_mask_max_v &&
    instance.M <= 4
```

For certificate-producing runs in this report, `route_mask_max_v=12`, so all `2^V` station masks are enumerated for `V<=12`.

The generated LP rows enforce:

- At most one visit mask per vehicle:
  `sum_A z_{kA} <= 1`.
- Station assignment/disjointness:
  `sum_{k,A contains i} z_{kA} - v_i = 0`.
- Per-station pickup/drop assignment:
  `sum_k p_{ki} = p_i` and `sum_k d_{ki} = d_i`.
- Operation only if the selected mask contains the station:
  `p_{ki} <= pickup_cap_{ki} * sum_{A contains i} z_{kA}` and similarly for drops.
- Route duration/load necessary conditions:
  `sum_i (tau_pick+tau_drop) p_{ki} + sum_A cycle_lb(A) z_{kA} <= T`,
  `sum_i d_{ki} - sum_i p_{ki} <= 0`,
  `sum_i p_{ki} - sum_i d_{ki} <= Q_k`.

The mask set contains all masks whose shortest depot cycle lower bound is no greater than `T`. This cannot exclude a feasible route support because any feasible route visiting support `A` has travel at least `cycle_lb(A)` and duration at most `T`.

Conclusion: the route-mask duration/load relaxation is a valid lower-bound relaxation and is safe for certificate-producing interval bounds.

## Incumbent Cutoff Logic

For interval floor `gamma_L` and incumbent objective `UB`, the code computes:

```text
penalty_budget = (UB - gamma_L) / lambda
```

and adds `P <= penalty_budget` in the relaxation when the cutoff is active. If `penalty_budget < 0`, then the interval floor alone proves no incumbent-improving solution can exist and the interval is bound-fathomed at `UB`.

When the cutoff relaxation is infeasible, the code reports `objective_lb=UB`. This is valid for global minimization because any solution outside the cutoff budget has objective at least `UB`, and any solution inside the budget would have mapped into the relaxation.

## Gini Interval Bounds

The implementation enforces:

- cap: `H <= V * gamma_cap * S`,
- optional floor: `H >= V * gamma_floor * S`,
- objective Gini lower variable: `gbound >= gamma_floor`,
- linear lower estimator: `gbound >= H / (V * S_upper)`.

`S_upper` is an upper bound on the ratio sum for candidate incumbent-improving solutions. Since `H >= 0` and `S <= S_upper`, the row `gbound >= H/(V*S_upper)` is a lower estimator of `H/(V*S)`. Thus it can only weaken the true objective and is valid for lower bounds.

## Station and Inventory Rows

The relaxation keeps exact aggregate station conservation:

```text
p_i - d_i + y_i = initial_i
y_i = target_i * r_i
```

It also includes station capacity bounds, station pickup/drop bounds, no-bike-creation total inventory upper bound, and a depot-return capacity lower bound on total station bikes. These are all necessary conditions for any original solution.

The current implementation also includes the station-operation mode/projection rows:

```text
p_i + d_i <= U_i v_i
p_i + d_i >= v_i
U_i = max(min(initial_i,Qmax), min(capacity_i-initial_i,Qmax)).
```

The upper row matches the original single-mode station operation: a visited station picks up or drops, not both, and the operation is bounded by station inventory/residual capacity and vehicle capacity. The lower row is safe as a projection-strengthening convention because any zero-operation visit can be deleted without changing final inventory or objective and without making the route less feasible.

## Subset Route Cuts for V > 10

The row reported as `route_visit_cuts=singletons+subsets_up_to_K` is separate from the route-mask relaxation. In the current code:

- for `V <= 12`, `K = V`;
- for `V > 12`, `K = 5`.

For a subset `S` of size `m`, the code adds:

```text
sum_{i in S} (tau_pick+tau_drop) p_i
+ L(S) * sum_{i in S} v_i
<= M*T + (m-1)*L(S)
```

where `L(S)` is a lower bound on the minimum total depot-cycle travel needed to cover all stations in `S` with at most `M` vehicles.

Validity proof: let `U` be the stations actually visited inside `S`, with `u=|U|`. Any feasible solution satisfies

```text
operation(U) + travel(U) <= M*T.
```

The cut left side for the realized solution is `operation(U) + L(S)*u`. If `u=m`, then `travel(U)=travel(S) >= L(S)`, so the cut follows. If `u<m`, then

```text
L(S)*u <= (m-1)*L(S)
```

because `u <= m-1`; therefore the extra RHS slack covers the whole travel coefficient term, and the cut follows from `operation(U) <= M*T`.

Thus the subset route cut is valid for any `K`, including the `V=12` full-subset case and the `V>12` capped size-5 case. Capping at 5 for larger instances weakens the relaxation but does not invalidate certificates.

## Timing and Certification Notes

The route-mask relaxation is active only when notes contain `route_mask_duration_load_relaxation=true`. After the current cleanup:

- `wall_time_seconds` is elapsed wall time;
- `bound_time_seconds` is aggregate inventory-bound worker time;
- `route_mask_time_seconds` is aggregate bound time only for bound calls where route-mask rows were active;
- in parallel runs, aggregate worker times may exceed wall time and must not be interpreted as elapsed runtime.

The route-mask threshold is now explicit through `--route-mask-max-v` and defaults to `12`. For `V=12`, the implementation enumerates the full set of `2^12` station masks, so the proof remains the same as for smaller complete-mask runs: every feasible route support maps to one of the enumerated masks. For `V>12`, route-mask rows are disabled by the threshold unless complete enumeration or another proved relaxation is supplied; capped subset route cuts may still be used because they are valid necessary inequalities, but they are not route-mask rows.

## Audit Decision

The implemented rows are consistent with the proof. No certificate-producing bound needs to be disabled.
