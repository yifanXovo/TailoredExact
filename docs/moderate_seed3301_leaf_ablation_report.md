# moderate_seed3301 Leaf Ablation Report

Diagnostic interval-local ablations were run on the two formerly open
`moderate_seed3301` low-Gini bands:

- `[0.0122881381662, 0.0245762763324]`;
- `[0.0245762763324, 0.0368644144986]`.

These ablations are diagnostic only.  They are not full certificates unless the
automatic full-frontier ledger merge covers the complete improving Gini range.

The full strengthened sealed run closes all final leaves.  The diagnostic CSV
`results/strengthened_oracle_round/moderate_seed3301_leaf_ablation.csv` records
per-variant runtime, CPLEX status, best bound, infeasibility status, cut counts,
and tightened domains.

The strongest practical combination was the all-cuts objective-bound oracle:
Gini spread cuts plus penalty-domain tightening plus required movement and
handling rows.  Transfer singleton compatibility did not add cuts on these two
leaves, which is expected because the stations are individually reachable.
