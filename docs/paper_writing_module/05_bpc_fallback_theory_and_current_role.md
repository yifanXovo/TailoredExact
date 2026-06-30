# 05 BPC Fallback Theory And Current Role

The BPC fallback is theoretically valid when every node lower bound used for
certification has exact pricing closure.

Current empirical role:

- BPC diagnostics start and pricing is called.
- No nontrivial leaf closed in the realignment round.
- The observed blocker is exact-pricing/column-generation state growth before
  closure.

Therefore BPC should be described as the intended exact fallback, with current
implementation bottlenecks reported honestly.  It should not be described as the
source of the existing V20 exact-portfolio certificates.
# Current Round Update

The `bpc_pricing_optimization_round` keeps BPC in the unified paper-core algorithm only as an exact fallback: an interval may close by BPC only when the branch-price tree has exact pricing closure. The new pricing diagnostics show that BPC starts and can generate/prune very large exact-label state spaces, but no tested nontrivial leaf closed in this round.

Paper wording should therefore be conservative: BPC is a valid exact fallback in the theorem, while the present implementation is bottlenecked by exact pricing state explosion and should not be described as the dominant empirical certificate source.
