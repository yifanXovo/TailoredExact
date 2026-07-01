# Exact-Safe Pricing Dominance

This round adds `--pricing-dominance-mode off|safe|aggressive-diagnostic`.

Only `safe` is certificate-eligible. It uses exact-state dominance: labels are compared only when the future feasible set is unchanged by the state key, and a label may dominate another only when it is no worse in time, reduced cost, load/resource state, and branch/cut compatibility. If the relation is uncertain, no dominance is applied.

Diagnostic outcome:

- Safe dominance is now visibly active in V12 leaves and prunes hundreds of millions of labels.
- V20 leaves still show limited route-label dominance, so the remaining bottleneck is not a missing switch but the pricing state representation itself.
- `aggressive-diagnostic` is intentionally not part of `paper-gf-bpc-core`.

