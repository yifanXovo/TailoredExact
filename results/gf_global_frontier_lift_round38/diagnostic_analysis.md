# Round 38 diagnostic analysis

All run gates passed: **True**; false certificates: **0**; certificate regressions: **0**.

| Row | V/M | Initial bounds | b+ | t | Completes | Split | C6 gap | G2-A gap | Gap change | AUC change | Outcome |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| r36_01_V12_M1 | 12/1 | 0.27726096936095629;0.29424322429778327;0.35403537724225576 | 0.292961 | 0.294243 | False | False | 2.79731e-15 | 2.79731e-15 | 0 | -0.00337619 | tie |
| r36_02_V12_M2 | 12/2 | 0.58956333674838779 | 0 | 0 | False | False | 5.09912e-15 | 5.09912e-15 | 0 | -0.000117017 | tie |
| r36_04_round32_multi_m_tight_T_V20_M2_seed89001413 | 20/2 | 0.15661358654541371;0.23593037105001993;0.32434010332119489 | 0.173792 | 0.23593 | False | False | 1.92806e-09 | 1.92806e-09 | 0 | 0.00020278 | tie |
| r36_06_moderate_seed5301 | 20/3 | 0.057144635390030694;0.083514114925258745;0.11831542250307144;0.15998675644551036 | 0.0661575 | 0.0835141 | False | False | 0.490612 | 0.381546 | 0.109065 | 0.0960632 | g2a_improves |
| r36_07_high_imbalance_seed5203 | 20/3 | 1.9814255024217624;2.1976615213567423;2.258965497085816 | 1.98833 | 2.19766 | False | False | 5.8522e-15 | 5.8522e-15 | 0 | -0.00062132 | tie |
| r36_08_tight_T_seed5102 | 20/3 | 0.20682410371683468;0.28917631309429254 | 0.208433 | 0.289176 | False | False | 0.201952 | 0.101728 | 0.100224 | 0.0800375 | g2a_improves |
| r36_09_round31_sealed_moderate_V50_seed1112848618 | 50/3 | 0.47114477265216009;0.63729271116882058 | 0.471621 | 0.637293 | False | False | 0.147017 | 0.147012 | 5.3125e-06 | -0.0014342 | g2a_improves |
| r36_10_high_imbalance_seed6202 | 50/3 | 7.4070090034849541;7.5557176110501905 | 7.46156 | 7.55572 | False | False | 0.158397 | 0.158397 | 0 | -0.00137203 | tie |
| r36_11_tight_T_seed6102 | 50/3 | 0.48661597140378293;0.62305459378377903 | 0.540854 | 0.623055 | False | False | 0.108775 | 0.118095 | -0.00932019 | -0.0121246 | g2a_regresses |
| r36_12_round32_multi_m_moderate_V50_M4_seed721910669 | 50/4 | 0.26545684397297908;0.36122471902797532 | 0.265457 | 0.361225 | False | False | 0.227694 | 0.226006 | 0.00168846 | -0.00996428 | g2a_improves |
| r36_13_moderate_seed4302 | 20/3 | 0;0.012135714717816735;0.024271429435633471;0.036407144153450206 | 0 | 0.0121357 | False | False | 0.186065 | 0.186065 | 0 | -0.00201159 | tie |
| r36_14_round32_multi_m_high_imbalance_V20_M2_seed1052706459 | 20/2 | 4.2430945553030863;4.3029840799645553 | 4.27329 | 4.30298 | False | False | 0 | 0 | 0 | -0.00242629 | tie |

## Frozen-rule interpretation

Diagnostic admissible: **True**. Stable-witness gate: **True**. Confirmation eligible: **True**. Promotion mechanism gate (at least one accepted next-frontier completion): **False**.
