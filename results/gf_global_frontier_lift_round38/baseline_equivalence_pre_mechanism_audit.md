# Round 38 pre-mechanism C6 equivalence

Gate passed: **True** (18 comparisons).

The frozen Round 37 executable and a clean executable built from the
Round 38 baseline merge were run in default C6-HGA-FULL mode.
The V12 case exercises targets, requeue, lookahead, and closure; the
V20/M2 case exercises real splits. Clocks and solver-effort counters
are excluded.

| Instance | Component | Equivalent | Max relative delta |
|---|---|---:|---:|
| V12_M1 | startup | True | 0 |
| V12_M1 | proof_range_and_four_intervals | True | 0 |
| V12_M1 | parent_lp_bounds | True | 0 |
| V12_M1 | lp_and_child_lookahead | True | 0 |
| V12_M1 | controlling_leaf_sequence | True | 0 |
| V12_M1 | targets_and_requeues | True | 0 |
| V12_M1 | split_decisions | True | 0 |
| V12_M1 | closures | True | 0 |
| V12_M1 | final_objective_and_certificate | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | startup | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | proof_range_and_four_intervals | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | parent_lp_bounds | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | lp_and_child_lookahead | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | controlling_leaf_sequence | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | targets_and_requeues | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | split_decisions | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | closures | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | final_objective_and_certificate | True | 0 |
