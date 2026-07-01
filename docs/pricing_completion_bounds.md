# Pricing Completion Bounds

`--pricing-completion-bound none|basic|dual-knapsack|resource` is now recorded in result JSON and trace rows. The paper-core preset uses `basic`.

The active safe pruning remains conservative:

- duration/resource infeasibility pruning;
- required closure pruning where already present;
- completion lower-bound pruning where the existing exact-safe bound applies.

The round data shows completion-bound pruning is present but not enough to close BPC leaves. Stronger resource and dual-knapsack lower bounds are the next target, but they must remain optimistic for minimization pricing so no negative column can be pruned incorrectly.

