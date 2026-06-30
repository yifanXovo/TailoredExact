# BPC Leaf Closure After Strengthened Oracle

BPC fallback remains diagnostic in this round.

After the strengthened oracle closes `moderate_seed3301`, no BPC leaf closure is
needed for that row.  For noncertified rows such as `high_imbalance_seed3201`,
automatic BPC fallback still closes zero leaves.  The current sealed
postprocessor records this explicitly:

- `bpc_fallback_auto_called`;
- `bpc_fallback_leaves_attempted`;
- `bpc_fallback_leaves_closed`;
- `bpc_interval_certificate_basis`.

No BPC fallback lower bound is used unless exact pricing closure is available.
Because no fallback leaf closed here, BPC remains off as a paper-default
certificate mechanism and should be revisited only after a targeted exact-pricing
leaf-closure implementation.
