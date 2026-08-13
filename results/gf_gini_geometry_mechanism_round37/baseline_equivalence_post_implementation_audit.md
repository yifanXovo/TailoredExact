# Round 37 contemporaneous C6 equivalence

Gate passed: **True** (18 component comparisons).

The frozen Round 36 Stage C executable and the clean Round 37
executable were run contemporaneously in default C6-HGA-FULL mode.
The V12 case exercises targets, requeue, lookahead, and closure; the
short V20/M2 case additionally exercises actual splits. Clocks and
solver-effort counters are excluded. Numeric ledger comparisons allow
only the precision already lost by the old six-digit CSV writer.

| Instance | Component | Equivalent | Max relative delta |
|---|---|---:|---:|
| V12_M1 | startup | True | 0 |
| V12_M1 | proof_range_and_four_intervals | True | 0 |
| V12_M1 | parent_lp_bounds | True | 3.15e-07 |
| V12_M1 | lp_and_child_lookahead | True | 0 |
| V12_M1 | controlling_leaf_sequence | True | 0 |
| V12_M1 | targets_and_requeues | True | 4.17e-07 |
| V12_M1 | split_decisions | True | 4.17e-07 |
| V12_M1 | closures | True | 4.37e-07 |
| V12_M1 | final_objective_and_certificate | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | startup | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | proof_range_and_four_intervals | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | parent_lp_bounds | True | 1.02e-06 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | lp_and_child_lookahead | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | controlling_leaf_sequence | True | 0 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | targets_and_requeues | True | 1.07e-06 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | split_decisions | True | 9.48e-07 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | closures | True | 1.07e-06 |
| round32_multi_m_high_imbalance_V20_M2_seed1052706459 | final_objective_and_certificate | True | 0 |
