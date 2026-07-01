# Pricing State Explosion Audit

Initial 300s BPC leaf diagnostics show that exact pricing is dominated by route
skeleton expansion and, for some V12 leaves, operation DP expansion.

Observed 300s baselines:

| target | pricing calls | pricing time | columns | best reduced cost | exact pricing closed |
|---|---:|---:|---:|---:|---|
| V12 M2 interval 7 | 2 | 298.286s | 42,248 | -0.00752183449778 | false |
| V12 M1 interval 12 | 1 | 299.397s | 26,006 | -0.00470697892369 | false |
| moderate_seed3301 interval 2 | 1 | 273.300s | 166,161 | 0.00469307183545 | false |
| high_imbalance_seed3202 interval 9 | 1 | 291.098s | 94,059 | 0.0700591864494 | false |
| V12 M2 forced diagnostic | 1 | 298.719s | 43,254 | 0.0103294366883 | false |

Depth profiles show tens to hundreds of millions of route states expanded in a
single pricing call.  Dominance pruning is ineffective in the decomposed route
skeleton path because skeleton states are not yet stored in a Pareto bucket the
way monolithic route-load labels are.  The current `safe-plus` mode is therefore
certificate-safe but not yet strong enough to close these leaves.

Preliminary bottleneck classification:

- V12 M1/M2: pricing still finds negative reduced-cost columns near the time
  limit, so column generation has not converged.
- moderate_seed3301 and high_imbalance_seed3202: best reduced cost is positive,
  but the exact pricer has not exhausted all skeletons, so closure is not
  certified.
- BPC cuts remain inactive in the 300s rows (`cuts_added=0`), so the RMP bound
  is not strengthened enough before expensive pricing.

The 1200s and 3600s diagnostics determine whether this is a runtime issue or a
structural pricing/RMP issue.
