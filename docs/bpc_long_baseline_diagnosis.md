# BPC Long Baseline Diagnosis

This document is populated by the BPC core repair round after running long
baseline leaf validations.

Mandatory baseline targets are listed in
`results/bpc_core_repair_round/target_leaf_manifest.csv`.

For each target, the long-baseline tables record:

- budget;
- target interval;
- pricing calls and pricing time;
- labels generated, kept, expanded, and pruned;
- operation DP states generated and pruned;
- columns generated and inserted;
- best reduced cost;
- RMP/master time;
- cuts added;
- nodes opened and closed;
- exact pricing closure status;
- stop reason.

The baseline must be interpreted before any BPC optimization claims.  If a
later variant improves pruning but still fails closure, the final report uses
the delta from these baseline rows to locate the remaining bottleneck.
