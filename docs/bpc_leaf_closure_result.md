# BPC Leaf Closure Result

No nontrivial BPC leaf closed in this round.

Evidence:

- `bpc_leaf_validation_after_all.csv` covers V12 M1, V12 M2, moderate_seed3301, high_imbalance_seed3202, and high_imbalance_seed3201 leaves.
- V12 leaves show substantial exact-safe dominance pruning but still retain negative reduced-cost evidence before closure.
- V20 leaves show millions of route-label expansions and weak route-label dominance.

Conclusion:

BPC remains theoretically valid but empirically not yet effective enough to be the main certificate workhorse. The paper-core algorithm can include BPC as a valid fallback, but current empirical claims should emphasize relaxation certificates and identify BPC pricing as the active implementation bottleneck.

