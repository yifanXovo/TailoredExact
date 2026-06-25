# Vehicle-Indexed Relaxation Proof

This note documents the certificate-safe relaxation stack now used by
`paper-bpc-core` before expensive branch-price tree work.

## Vehicle-Indexed Operation Rows

For every feasible original route-load solution, define `y_{k,i}=1` when
vehicle `k` visits station `i`, and define `p_{k,i}`, `d_{k,i}` as the total
pickup/drop amounts performed by that vehicle at that station. These values
project any original route plan into the vehicle-indexed relaxation:

- route-mask service linking is valid because a vehicle can serve station `i`
  only if its selected route mask contains `i`;
- station disjointness is valid because the original route plan assigns each
  served station to at most one vehicle;
- aggregate station operations satisfy `p_i=sum_k p_{k,i}` and
  `d_i=sum_k d_{k,i}`;
- operation linking `p_{k,i} <= pickup_ub_i y_{k,i}` and
  `d_{k,i} <= drop_ub_i y_{k,i}` is necessary because an unvisited station
  cannot be operated by that vehicle;
- each truck starts empty, so `sum_i p_{k,i} >= sum_i d_{k,i}`;
- final depot unload equals `sum_i p_{k,i}-sum_i d_{k,i}` and is at most
  truck capacity.

These constraints remove fractional aggregate assignments that cannot be
realized by any single vehicle, while preserving every original feasible
route-load solution. They are valid lower-bound strengthening rows.

## Vehicle-Indexed Transfer Flow

For any original route, every bike dropped by vehicle `k` at station `j` was
previously picked up by the same vehicle from some station `i`, or came from no
station only if initial depot load were allowed. This project uses empty initial
truck load, so a feasible route induces transfer variables `f_{k,i,j}` and
depot-unload variables `h_{k,i}`:

- `p_{k,i}=sum_j f_{k,i,j}+h_{k,i}`;
- `d_{k,j}=sum_i f_{k,i,j}`;
- `f_{k,i,j}` is zero unless a route mask contains both `i` and `j`;
- safe caps use travel lower bounds, handling time, station pickup/drop bounds,
  and truck capacity only.

No heuristic route failure is used as a zero-cap proof. If a cap cannot be
computed safely, the relaxation uses a loose cap rather than cutting a feasible
route.

## Movement-Domain Tightening

Movement-domain tightening bounds station final inventories using only global
necessary conditions: route-duration reachability, handling-time budget,
station capacity, current inventory, target/capacity data, and truck capacity.
It does not use restricted route pools, heuristic incumbents, or sampled route
failures. It is therefore valid lower-bound evidence.

## Incumbent Cutoff

A verified incumbent is an upper bound only. In an interval relaxation, it may
be used as a cutoff to prove that no improving solution exists in that interval.
If the relaxation is infeasible under the incumbent cutoff, every original
solution in that interval is excluded because the original feasible set is a
subset of the relaxation feasible set.

## Complete Route-Mask Enumeration

For V <= 12, `paper-bpc-core` enables complete all-subset route-mask
enumeration (`2^V-1` masks per vehicle before support pruning). These rows are
certifying only when `route_mask_all_subset_enumeration_certifying=true`.
Incomplete route-mask lists are diagnostic only and cannot support an
original-problem certificate.

## Operation-Budget Relaxation Portfolio

Route-mask operation-budget rows are valid strengthening rows, but their MIP can
be harder to solve within the per-interval budget. The current paper-core path
therefore solves the configured operation-budget relaxation first, and when it
does not fathom the interval it also solves the same interval with the
operation-budget rows disabled. Both are relaxations of the original problem.
The solver keeps the stronger valid lower bound. This can improve certificate
progress because a weaker relaxation can sometimes prove cutoff infeasibility
within budget when the stronger MIP only returns a weak time-limited bound.

## Relaxation-Only Frontier Certificates

Exact BPC pricing closure is required only for intervals certified by BPC tree
closure. If every active interval in the full improving Gini range is empty or
bound-fathomed by valid non-pricing lower bounds, no BPC pricing closure is
needed for those intervals. The result must record:

- `frontier_covers_all_improving_gini_values=true`;
- `frontier_range_certificate_scope=original_full_improving_range`;
- `unresolved_intervals=0`;
- `invalid_bound_intervals=0`;
- `open_nodes=0`;
- per-interval `certificate_basis=inventory_route_gini_relaxation_fathomed`
  or another valid non-pricing basis;
- `requires_pricing_closure=false` for those intervals.

