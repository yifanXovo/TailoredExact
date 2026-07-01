# Exact-Safe Pricing Dominance V2

This round extends the dominance controls to:

- `--pricing-dominance-mode off`
- `--pricing-dominance-mode safe`
- `--pricing-dominance-mode safe-plus`
- `--pricing-dominance-mode diagnostic-aggressive`

Only `safe` and `safe-plus` are certificate-eligible.  The implementation
treats `safe-plus` as an auditable certificate-safe mode: it enables the exact
same conservative dominance checks as `safe` plus the decomposed loading-DP
dominance controls.  `diagnostic-aggressive` is normalized to the historical
`aggressive-diagnostic` value and is never certificate-safe.

Dominance is accepted only when a retained state has no greater consumed
resource, no worse reduced cost, and no weaker branch/domain feasibility than
the discarded state.  If a future feasibility relation is ambiguous, the label
is not dominated.  BPC certificate validity still requires final exact pricing
closure after all dominance pruning.

Validation in this round compares dominance-off and safe/safe-plus variants on
the frozen BPC leaves and records:

- label dominance comparisons;
- labels pruned by dominance;
- operation DP states pruned;
- best reduced cost;
- exact pricing closure status.
