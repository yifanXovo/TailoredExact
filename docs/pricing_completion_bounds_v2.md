# Pricing Completion Bounds V2

The exact pricer exposes:

- `--pricing-completion-bound none`
- `--pricing-completion-bound basic`
- `--pricing-completion-bound dual-knapsack`
- `--pricing-completion-bound resource`
- `--pricing-completion-bound all`

In the current implementation `all` enables the certificate-safe completion
lower-bound pruning path and records the requested mode in every pricing trace.
It applies both label-level completion checks and a route-skeleton completion
lower bound before the fixed-sequence loading DP is called.  The pruning rule is
used only when the bound is optimistic for minimization:

```text
current_reduced_cost + optimistic_completion_bound >= -epsilon
```

If that condition holds, no completion of the partial label can produce a
negative reduced-cost column under the active bound model.  If the bound cannot
be established safely, the label is kept.

The route-skeleton bound is intentionally conservative.  It assumes the best
possible remaining negative visit, operation, pair, and subset-row dual
contributions across all allowed stations, and uses a safe travel lower bound
for nonnegative travel duals or the maximum route duration for negative travel
duals.

This round tracks:

- labels pruned by reduced-cost completion bounds;
- labels pruned by duration/load/station feasibility;
- best reduced cost by route depth;
- exact pricing closure status with and without completion pruning.

The completion bound is a pricing acceleration only.  It never contributes a
lower-bound certificate unless the final exact pricing closure status is true.
