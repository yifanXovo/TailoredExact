# 02 Unified Algorithm

The realigned main paper algorithm is `paper-gf-bpc-core`:

1. generate a native HGA-TGBC incumbent and independently verify it;
2. decompose the improving Gini range into frontier intervals;
3. screen intervals with valid non-enumerative relaxation lower bounds;
4. send unresolved intervals to route-load BPC;
5. accept BPC lower-bound evidence only when exact pricing closure is proven;
6. certify only when the full improving Gini range is covered.

The algorithm does not change paradigm by `V`, `M`, or instance name.  Complete
all-subset route-mask enumeration is not a paper-core certificate source.
