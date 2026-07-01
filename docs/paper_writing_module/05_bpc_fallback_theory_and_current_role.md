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

# BPC Core Repair Round

The `bpc_core_repair_round` kept BPC as the mandatory paper-core repair target
and ran long leaf diagnostics before drawing conclusions.  The tested leaves
included the V12 M2 and V12 M1 controlling leaves, a moderate V20 leaf, a
high-imbalance V20 leaf, and a forced-BPC V12 diagnostic leaf.

The strongest 3600s diagnostics still closed zero nontrivial leaves by exact
pricing.  V12 M2 advanced to four pricing calls but retained a negative reduced
cost of `-0.00327041731624`; V12 M1 remained at one pricing call with negative
reduced cost `-0.0088398618421`; moderate_seed3301 had positive best reduced
cost `0.00469307183545` but did not complete exact pricing enumeration.  Cut
separation remained inactive (`cuts_added=0`) across the target leaves.

This supports the theoretical role of BPC but not an empirical claim that the
current implementation is an effective fallback.  The paper should state that
the current bottleneck is exact pricing/decomposition: route-skeleton state
counts reach tens or hundreds of millions, and operation-DP states exceed one
billion on some V12 diagnostics before exact closure.
