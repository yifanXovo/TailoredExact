# Round 37 exploratory smoke analysis

All run gates passed: **True**; false certificates: **0**; certificate regressions: **0**.

The G1 policy executed on **5/6** pairs. The remaining V50 moderate row exhausted the 180-second cap during the complete four-cell LP census, before any policy decision or split.

| Row | V/M | Exposure | Weakest reproduced | Pilot LP gain | C6 common-UB gap | G1 common-UB gap | Outcome |
|---|---:|---:|---:|---:|---:|---:|---|
| r36_01_V12_M1 | 12/1 | True | True | 0.0157003 | 2.79731e-15 | 2.79731e-15 | tie |
| r36_02_V12_M2 | 12/2 | True | True | 0.00565318 | 5.09912e-15 | 5.09912e-15 | tie |
| r36_04_round32_multi_m_tight_T_V20_M2_seed89001413 | 20/2 | True | True | 0.0171782 | 1.92806e-09 | 1.92806e-09 | tie |
| r36_08_tight_T_seed5102 | 20/3 | True | True | 0.00160882 | 0.201952 | 0.126694 | g1_improves |
| r36_09_round31_sealed_moderate_V50_seed1112848618 | 50/3 | False | False | 0 | 0.75 | 0.75 | tie |
| r36_10_high_imbalance_seed6202 | 50/3 | True | True | 0.0545466 | 0.158063 | 0.187027 | g1_regresses |

## Decision

Advance to a focused medium-cap diagnostic without changing G1. The mechanism is real at the local relaxation level: every exposed pilot strictly raised the selected cell's valid LP bound, and all 5 exposed cells reproduced the independently observed Round 36 weakest-cell index. End-to-end evidence is not uniformly positive: one V20 row improved materially, three pairs tied, one hard V50 row was censored, and the V50 high-imbalance row regressed. This is evidence for a mechanism diagnostic, not candidate promotion.
