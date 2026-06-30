# BPC Leaf Domain Transfer

The paper-core JSON now records BPC-domain-transfer related fields and the pricing diagnostics classify whether the BPC leaf is solving the same fixed-Gini interval as the frontier leaf.

Current status:

- Gamma interval and incumbent cutoff are passed through the existing fixed-Gini diagnostic path.
- Inventory-domain and required-movement transfer into pricing are not yet strong enough to prevent state explosion.
- No interval-oracle bound is imported into `paper-gf-bpc-core`.

Next step:

Implement tighter per-leaf final-inventory domains directly inside BPC master and exact pricing, then validate that pricing closure is unchanged on small leaves.

