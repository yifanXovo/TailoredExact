# Route-Mask Duration/Load Bound Proof

## Statement

For small instances where the inventory/Gini interval relaxation enables `route_mask_duration_load_relaxation=true`, each vehicle `k` chooses at most one binary station mask `z_{kA}` from the set of masks `A` whose shortest depot cycle travel lower bound is no more than the route time limit `T`. Station visit indicators, pickup quantities, and drop quantities are assigned to the selected vehicle masks.

For every selected vehicle mask, the relaxation enforces:

- `cycle_lb(A) + (tau_pick + tau_drop) * pickup_k <= T`
- `drop_k <= pickup_k`
- `pickup_k - drop_k <= Q_k`
- pickup/drop at station `i` can be positive for vehicle `k` only if the selected mask contains `i`
- every visited station is assigned to exactly one selected vehicle mask

This is used only inside `computeGiniIntervalInventoryRelaxationBound` in [src/Bounds.cpp](E:/codes/ExactEBRP/src/Bounds.cpp). It is a lower-bound relaxation and, when infeasible under an incumbent cutoff, a valid bound-fathoming test for the corresponding Gini interval. It is not a restricted route/path pool and is not an incumbent heuristic.

## Assumptions

- Vehicles start empty at depot 0.
- Every selected route is elementary with station visits disjoint across vehicles.
- A route may return to the depot with remaining bikes.
- Depot capacity is unlimited.
- Station pickup and drop quantities are integer and respect station capacities.
- Vehicle load is always in `[0,Q_k]`.
- Route duration is travel time plus station pickup/drop operation time plus final depot unloading time.
- Under the project convention, final depot unloading uses `tau_drop`, so route operation time equals `(tau_pick + tau_drop) * total_pickup`.
- `cycle_lb(A)` is a valid lower bound on the travel time of any depot-to-depot route visiting all stations in `A`. The implementation obtains it from the metric closure and a Held-Karp-style shortest cycle bound.

## Validity

Take any feasible EBRP route for vehicle `k` and let `A` be the set of stations visited by that route. The corresponding relaxation can select `z_{kA}=1`, assign those station visit indicators to vehicle `k`, and assign the route's actual pickup and drop quantities to the per-vehicle pickup/drop variables.

The assignment satisfies all route-mask rows:

- The selected mask contains every station with positive pickup/drop by construction.
- Since original routes are station-disjoint, each visited station is assigned to one vehicle mask.
- The actual route starts empty, so cumulative drops cannot exceed total pickups over the full route: `drop_k <= pickup_k`.
- The vehicle returns with load `pickup_k - drop_k`, which must be no larger than `Q_k`.
- The true route travel time is at least `cycle_lb(A)`. The original duration constraint is
  `travel(route) + (tau_pick + tau_drop) * pickup_k <= T`.
  Replacing `travel(route)` by the lower bound `cycle_lb(A)` preserves feasibility of every original route assignment.

Therefore every feasible original solution maps to a feasible point of the route-mask relaxation with the same final inventories and the same `G` and `P` variables. Minimizing a valid lower estimator of `G + lambda P` over this superset cannot produce a value larger than the true interval optimum. If the incumbent-cutoff version is infeasible, then no original feasible solution can satisfy the stricter incumbent-improving conditions in that interval, because every such solution would have mapped into the relaxation.

## Dependence on Parameters

- `tau_pick` and `tau_drop`: used only through the valid operation-time conservation identity `(tau_pick + tau_drop) * pickup_k`.
- `T`: appears in the necessary route duration row.
- `Q_k`: appears in the return-load necessary row and station operation linking caps.
- `M`: controls how many vehicle masks may be selected.
- `lambda`: affects only the relaxation objective and incumbent penalty-budget cutoff; it is not part of route feasibility.
- Triangle inequality / metric closure: the travel lower bound is computed on the metric closure, so it is valid even when raw distances are not perfectly metric.

## Why It Cannot Eliminate an Optimal Solution

The route-mask rows are necessary conditions satisfied by every feasible original route-load column. They do not require a particular station order, do not require selecting a restricted candidate route, and do not forbid any feasible support set whose true route can satisfy the time limit. The relaxation can only remove inventory assignments that no feasible route support/load assignment could realize under these necessary conditions. Thus it cannot eliminate a feasible optimal EBRP solution and is safe for certificate-producing lower bounds.

Implementation scope: current certificate-producing runs use complete mask enumeration through `--route-mask-max-v`, defaulting to `12`. For `V=12`, this means all `2^12` station masks are considered. For larger `V`, the route-mask rows are disabled unless complete enumeration or a separately proved catch-all relaxation is added; an incomplete mask list must not be treated as a complete lower-bound certificate.
