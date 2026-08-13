# Round 38 exploratory smoke analysis

All run gates passed: **True**; false certificates: **0**; certificate regressions: **0**.

| Row | V/M | Children evaluated | Completes frontier | Split | C6 gap | G2-A gap | Gap change | AUC change | Outcome |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| r36_01_V12_M1 | 12/1 | True | False | False | 2.79731e-15 | 2.79731e-15 | 0 | -0.00318992 | tie |
| r36_04_round32_multi_m_tight_T_V20_M2_seed89001413 | 20/2 | True | False | False | 1.92806e-09 | 1.92806e-09 | 0 | 5.19652e-05 | tie |
| r36_08_tight_T_seed5102 | 20/3 | True | False | False | 0.201952 | 0.12204 | 0.0799122 | 0.061046 | g2a_improves |
| r36_09_round31_sealed_moderate_V50_seed1112848618 | 50/3 | False | False | False | 1 | 1 | 0 | 0 | tie |
| r36_10_high_imbalance_seed6202 | 50/3 | True | False | False | 0.165871 | 0.165871 | 0 | -0.0045387 | tie |
| r36_14_round32_multi_m_high_imbalance_V20_M2_seed1052706459 | 20/2 | True | False | False | 0 | 0 | 0 | -0.00212647 | tie |

## Decision

All exactness and artifact gates passed with zero false certificates. No midpoint pair completed the next strict frontier and no G2-A refinement occurred, falsifying immediate frontier completion as the cause of the retained V20 benefit. Nevertheless the stable V20 positive remained positive and the stable V50 regression became a tie, so the frozen rule warrants a medium-cap full-panel test for generality and pilot-overhead effects without any policy change.
