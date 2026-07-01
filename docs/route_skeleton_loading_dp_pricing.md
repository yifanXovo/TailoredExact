# Route Skeleton + Loading-DP Pricing

The exact BPC pricer now exposes `--pricing-decomposition`:

- `auto`: historical implementation choice.
- `monolithic`: use the monolithic route-load label setting pricer when the
  implementation guard allows it.
- `route-skeleton-load-dp`: enumerate elementary route skeletons, then solve an
  exact loading/operation DP for each fixed station sequence.

The decomposed mode remains an exact pricing method only when the fixed-sequence
loading DP proves the best feasible pickup/drop/loading profile for every
enumerated skeleton.  The route skeleton controls station order, support,
travel time, branch compatibility, and duration prechecks.  The loading DP
handles truck capacity, pickup/drop amounts, station inventory domains, handling
time, depot unloading, and reduced cost.

The paper-core preset `paper-gf-bpc-core` uses
`route-skeleton-load-dp` so V12 and V20 rows use the same non-enumerative BPC
framework rather than a small-V all-route certificate path.

Audit fields:

- `pricing_decomposition`
- `pricing_load_dp_cache_enabled`
- `pricing_route_skeleton_mode`
- `pricing_route_skeleton_cache_enabled`
- `pricing_load_dp_dominance_enabled`
- `operation_dp_profile`
- `pricing_depth_profile`

Cache reuse is conservative: cache settings are logged, but no cached loading
DP result may be reused across incompatible duals, interval bounds, route
domains, vehicle capacity, or handling conventions.
