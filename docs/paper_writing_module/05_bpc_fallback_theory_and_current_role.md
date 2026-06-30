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
