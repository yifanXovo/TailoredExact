# V20/M3 Mini-Suite Certificate Report

Round directory: `results/v20_replication_round/`.

The five V20/M3 stress instances not named `high_imbalance_seed3202` were run
with the fixed V20 mip-light configuration and native HGA-TGBC incumbents.

| instance | status | LB | UB | gap | runtime | certificate |
|---|---|---:|---:|---:|---:|---|
| high_imbalance_seed3201 | not closed | 1.58377469667 | 2.44340319194 | 0.351816064623 | 6063.134s | none |
| tight_T_seed3101 | optimal | 0.107252734134 | 0.107252734134 | 0 | 148.602s | relaxation-only full frontier |
| tight_T_seed3102 | not closed | 0.31574776659 | 0.600704436685 | 0.474370843117 | 8129.622s | none |
| moderate_seed3301 | not closed | 0.00832009355002 | 0.0491525526647 | 0.830729166667 | 7915.296s | none |
| moderate_seed3302 | not closed | 0.0280208108338 | 0.195636206549 | 0.856770833333 | 5788.069s | none |

`tight_T_seed3101` is a new V20/M3 full original-problem certificate in this
round.  The certificate basis is relaxation-only full frontier: all improving
Gini intervals are bound-fathomed, and the row has zero unresolved intervals,
zero open nodes, and verifier pass.

The noncertified rows are honest lower-bound failures.  Exact interval cutoff
oracles were run on unresolved leaves for `high_imbalance_seed3201`,
`tight_T_seed3102`, and `moderate_seed3301`.  They did not close the first two
within the short per-leaf budget.  For `moderate_seed3301`, the oracle proved
infeasibility for nine final leaves, but one leaf
`[0.0163841842216, 0.0327683684432]` timed out after a longer 600s oracle run.
The merge audit therefore correctly reports `certificate_incomplete`.

Machine-readable evidence:

- `results/v20_replication_round/v20_minisuite_summary.csv`;
- `results/v20_replication_round/v20_minisuite_interval_status.csv`;
- `results/v20_replication_round/v20_minisuite_oracle_results.csv`;
- `results/v20_replication_round/ledger_merge_audit.csv`.
