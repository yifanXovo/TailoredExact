# 02 Unified Algorithm

The realigned empirical paper algorithm is `paper-gf-compact-bc`:

1. generate a native HGA-TGBC incumbent and independently verify it;
2. decompose the improving Gini range into frontier intervals;
3. screen intervals with valid non-enumerative relaxation lower bounds;
4. send unresolved intervals to a compact fixed-Gini-interval branch-and-cut
   subsolver;
5. accept compact BC lower-bound evidence only when the result JSON proves
   original fixed-interval scope and a valid CPLEX MIP bound or infeasibility
   certificate;
6. certify only when the full improving Gini range is covered.

The algorithm does not change paradigm by `V`, `M`, or instance name.  Complete
all-subset route-mask enumeration is not a paper-core certificate source.

`paper-gf-bpc-core` remains the route-load BPC research preset.  Its lower-bound
evidence is valid only with exact pricing closure, but current experiments show
it is not yet the empirical mainline.
