# Round 37 exploratory smoke predeclaration

This selection was fixed before any G1 result existed. The smoke stage uses
six contemporaneous C6/G1 pairs, each with a 180-second overall process cap.

| Ordinal | Panel row | V/M | Scenario | Pre-result role |
|---:|---|---:|---|---|
| 1 | r36_01_V12_M1 | 12/1 | v12 | small target/requeue witness |
| 2 | r36_02_V12_M2 | 12/2 | v12 | small multi-vehicle witness |
| 4 | r36_04_round32_multi_m_tight_T_V20_M2_seed89001413 | 20/2 | tight_T | prior candidate-win regime |
| 8 | r36_08_tight_T_seed5102 | 20/3 | tight_T | prior comparator-win regression witness |
| 9 | r36_09_round31_sealed_moderate_V50_seed1112848618 | 50/3 | moderate | hard V50 comparator-win witness |
| 10 | r36_10_high_imbalance_seed6202 | 50/3 | high_imbalance | hard V50 geometry-direction counterweight |

The sample is balanced by size (two V12, two V20, two V50) and includes both
historical geometry directions plus positive and regression regimes. Selection
uses only the frozen panel metadata; smoke outcomes cannot change membership.

Advancement requires zero false certificates, complete root/parent-child
coverage and lifecycle gates, complete four-cell pilot LP evaluation, and
actual midpoint pre-refinement on the open selected cell whenever an improving
cell exists. Aggregate gap wins alone are not sufficient: the post-split child
bound must demonstrate the proposed relaxation mechanism without a concentrated
size/scenario regression.
