# V20-Safe Relaxation Cuts

For V20/M3 hard stress instances, complete all-subset route-mask enumeration is
not used as certifying evidence. This round adds a continuous vehicle-indexed
relaxation layer that does not enumerate station subsets and is therefore safe
for larger instances as a necessary-condition lower-bound relaxation.

## Implemented Families

1. Vehicle-indexed operation variables:
   `y_{k,i}`, `p_{k,i}`, and `d_{k,i}` are continuous relaxation variables
   linked to aggregate station visit and operation variables.

2. Vehicle-indexed load balance:
   for each vehicle, total drop is bounded by total pickup and return load is
   bounded by vehicle capacity. These are necessary for every feasible route.

3. Vehicle operation-budget inequalities:
   total handling time per vehicle is bounded by the route duration limit. For
   each served station, a depot-star duration lower bound is added:
   total handling time plus `depot -> i -> depot` travel must fit in `T`.

4. Vehicle-indexed route-duration cover cuts:
   for station pairs whose best depot-anchored two-station travel plus the
   minimum necessary handling cannot fit in `T`, the same vehicle cannot serve
   both stations. This is a pairwise necessary condition and does not depend on
   sampled routes.

5. Pickup/drop transfer compatibility and transfer-cap cuts:
   vehicle-indexed transfer variables are capped by safe
   `depot -> pickup -> drop -> depot` travel lower bounds, handling budget, bike
   availability, station space, and vehicle capacity. If the safe cap is zero,
   no transfer is allowed. Loose or unknown caps are not tightened.

## Proof Sketch

Every original feasible route induces values for the continuous variables:
`y_{k,i}=1` when vehicle `k` serves station `i`, `p_{k,i}` and `d_{k,i}` equal the
route operation quantities, and transfer variables describe how picked bikes can
support drops or depot unload. Route duration, truck capacity, station mode, and
pickup/drop compatibility constraints are necessary conditions for those induced
values. Relaxing integrality and sequence detail enlarges the feasible set, so
the LP/MIP optimum remains a valid lower bound for a minimization problem.

These cuts do not create route plans or incumbents. They only strengthen the
lower-bound relaxation. If a row remains unresolved, it is noncertified.
