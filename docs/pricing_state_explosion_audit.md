# Pricing State Explosion Audit

Round: `results/bpc_pricing_optimization_round`.

The BPC pricing audit targets V12 M1/M2, moderate V20, and high-imbalance V20 leaves from existing frontier ledgers. The key finding is that exact pricing now exposes enough counters to identify the bottleneck, but it still does not close a nontrivial leaf in the tested budgets.

Observed behavior:

- V12 M2 leaf 7: safe dominance pruned about 193M labels in a 30s diagnostic, but exact pricing still returned a negative reduced cost and did not close.
- V12 M1 leaf 12: safe dominance pruned about 222M labels, again without exact closure.
- V20 moderate/high-imbalance leaves: route-label dominance is much weaker or zero; operation-DP pruning is active on some leaves, but enumeration remains the limiting factor.
- BPC cut separation did not change the RMP enough to close a leaf in this round.

Interpretation:

- Pricing is dominated by exact route-label enumeration on V12 and by large V20 route/operation state spaces on V20.
- Negative reduced-cost columns are still found late on some leaves, so the current exact pricer cannot prove closure within the tested budgets.
- The next mathematical step is a deeper route-skeleton/loading-DP decomposition with stronger exact completion bounds, not more frontier scheduling.

