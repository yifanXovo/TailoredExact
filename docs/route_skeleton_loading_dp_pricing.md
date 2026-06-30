# Route Skeleton And Loading-DP Pricing

The current implementation exposes pricing profile controls:

- `--pricing-load-dp-cache`
- `--pricing-route-skeleton-mode standard|pulse`
- `--pricing-operation-dp-dominance`

This round did not complete a full decomposition rewrite. The exact pricer still enumerates route labels and evaluates operation feasibility with the existing DP. Operation-DP dominance is active and logged, while load-DP cache and pulse skeleton mode remain implementation hooks.

Certificate status:

- Returned columns remain original feasible.
- Exact closure still requires the exact pricer to prove no negative reduced-cost column.
- No certificate in this round depends on a heuristic or approximate decomposition.

