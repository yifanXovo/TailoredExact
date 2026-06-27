# V20 Multi-Station Cover Cuts

Date: 2026-06-27

## Purpose

For V20/M3 stress instances, all-subset route-mask enumeration is not a
certifying option. This round adds a certificate-safe route-duration cover cut
family that can be separated from candidate station subsets without enumerating
all masks.

## Cut

For a vehicle `k` and station subset `S`, compute a valid travel lower bound:

```text
travel_lb(S) = MST(S) + min_{i in S} d(depot,i) + min_{i in S} d(i,depot)
```

The MST term is a lower bound on connecting all visited stations, and the two
depot terms are necessary for leaving and returning to the depot. Therefore
`travel_lb(S)` is no larger than the travel time of any feasible route serving
all stations in `S`.

The implementation uses `handling_lb(S)=0`. This is intentionally weaker than
using operation-count assumptions, but it is certificate-safe even when a
relaxation permits a visited station with zero operation.

If:

```text
travel_lb(S) > T_k
```

then no original feasible route for vehicle `k` can serve every station in `S`.
The relaxation can safely add:

```text
sum_{i in S} y[k,i] <= |S| - 1
```

This is a necessary-condition cut; it removes no original feasible route-load
solution.

## Implementation

CLI:

```text
--v20-cover-cuts true|false
--v20-cover-max-size <int>
--v20-cover-max-cuts <int>
--v20-cover-separation-seconds <double>
```

The implementation greedily tests subsets from V20 station lists up to the
configured size and cut budget. It reports:

- candidate subsets tested;
- cuts added;
- max subset size used;
- separation time;
- example subsets.

## Round Result

On the current V20/M3 stress suite, the cut is valid but inactive under the
current `T=3600` convention:

- `tight_T_seed3102_cover6_300s` tested `903735` subsets and added zero cuts.
- All 300s V20 rows in `results/relaxation_closure_round/` report zero cover
  cuts.

This means the present V20 plateau is not caused by missing small infeasible
service-set covers. The more effective strengthening in this round is the
compact-flow relaxation.
